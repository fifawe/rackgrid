"""HTTP adapter that lets the backend API control the standalone scheduler
container (app/scheduler_main.py) over the internal Docker network.
Implements application.services.job_service.SchedulerPort."""
from __future__ import annotations

import httpx

from app.application.services.job_service import SchedulerPort
from app.infrastructure.config.logging import get_logger

logger = get_logger(__name__)


class HttpSchedulerAdapter(SchedulerPort):
    def __init__(self, base_url: str = "http://scheduler:9000"):
        self._base_url = base_url.rstrip("/")

    async def trigger_run_now(self) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(f"{self._base_url}/internal/run")
            except httpx.HTTPError as exc:
                logger.warning("scheduler_trigger_failed", error=str(exc))

    async def set_schedule(self, cron_expression: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                await client.post(
                    f"{self._base_url}/internal/schedule",
                    json={"cron_expression": cron_expression},
                )
            except httpx.HTTPError as exc:
                logger.warning("scheduler_reschedule_failed", error=str(exc))

    def list_jobs(self) -> list:
        try:
            resp = httpx.get(f"{self._base_url}/internal/jobs", timeout=5)
            resp.raise_for_status()
            return resp.json().get("jobs", [])
        except httpx.HTTPError as exc:
            logger.warning("scheduler_list_jobs_failed", error=str(exc))
            return []
