"""Triggers a collection run on the `collector` container (an Ansible
control node with a small HTTP trigger wrapper - see collector/agent.py)
over the internal Docker network, and waits for it to finish.

Keeping the actual `ansible-playbook` invocation inside the collector
container (rather than shelling out from here) matches the five-service
architecture in PROJECT_SPEC.md - scheduler owns *when*, collector owns
*how*.
"""
from __future__ import annotations

import os

import httpx

from app.infrastructure.config.logging import get_logger

logger = get_logger(__name__)

COLLECTOR_BASE_URL = os.environ.get("COLLECTOR_BASE_URL", "http://collector:9100")

# Ansible runs against a whole inventory of servers, which can take a
# while - give it a generous timeout rather than the default few seconds.
_RUN_TIMEOUT_SECONDS = float(os.environ.get("COLLECTOR_RUN_TIMEOUT_SECONDS", "1800"))


async def run_playbook(collector_run_id: int, backend_base_url: str) -> int:
    """Calls the collector agent's /run endpoint and returns an exit-code
    style int (0 = success) for the caller to interpret."""
    logger.info("collector_run_started", run_id=collector_run_id, collector_base_url=COLLECTOR_BASE_URL)

    try:
        async with httpx.AsyncClient(timeout=_RUN_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{COLLECTOR_BASE_URL}/run",
                json={"collector_run_id": collector_run_id, "backend_base_url": backend_base_url},
            )
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPError as exc:
        logger.error("collector_run_failed", run_id=collector_run_id, error=str(exc))
        return 1

    return_code = body.get("return_code", 1)
    logger.info("collector_run_finished", run_id=collector_run_id, return_code=return_code)
    return return_code
