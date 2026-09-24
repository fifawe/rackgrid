"""Collector Agent - a small FastAPI wrapper around `ansible-playbook`.

This is what makes the `collector` container independently triggerable:
the `scheduler` service (see backend/app/infrastructure/scheduling)
POSTs here to kick off a discovery run, and this process supervises the
`ansible-playbook` subprocess and reports back pass/fail plus a return
code, without either service needing shell/SSH access into the other's
container.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("collector-agent")

COLLECTOR_DIR = os.environ.get("COLLECTOR_DIR", "/collector")
INVENTORY_PATH = os.environ.get("COLLECTOR_INVENTORY", f"{COLLECTOR_DIR}/inventory/hosts.ini")
PLAYBOOK_PATH = os.environ.get("COLLECTOR_PLAYBOOK", f"{COLLECTOR_DIR}/playbook.yml")

app = FastAPI(title="RackGrid Collector Agent")

# A simple lock prevents two overlapping ansible-playbook runs from
# racing against the same inventory/managed hosts.
_run_lock = asyncio.Lock()


class RunRequest(BaseModel):
    collector_run_id: Optional[int] = None
    backend_base_url: str = "http://backend:8000"


class RunResponse(BaseModel):
    return_code: int
    output_tail: str


@app.post("/run", response_model=RunResponse)
async def run(request: RunRequest):
    if _run_lock.locked():
        logger.warning("collector_run_rejected_busy", extra={"run_id": request.collector_run_id})
        return RunResponse(return_code=1, output_tail="A collection run is already in progress")

    async with _run_lock:
        cmd = [
            "ansible-playbook",
            "-i",
            INVENTORY_PATH,
            PLAYBOOK_PATH,
            "-e",
            f"backend_base_url={request.backend_base_url}",
        ]
        if request.collector_run_id is not None:
            cmd += ["-e", f"collector_run_id={request.collector_run_id}"]

        logger.info("collector_run_started run_id=%s cmd=%s", request.collector_run_id, " ".join(cmd))

        if not os.path.exists(PLAYBOOK_PATH):
            return RunResponse(return_code=1, output_tail=f"Playbook not found at {PLAYBOOK_PATH}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=COLLECTOR_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        output = (stdout or b"").decode(errors="replace")
        logger.info(
            "collector_run_finished run_id=%s return_code=%s",
            request.collector_run_id,
            process.returncode,
        )
        return RunResponse(return_code=process.returncode or 0, output_tail=output[-4000:])


@app.get("/health")
async def health():
    return {"status": "ok"}
