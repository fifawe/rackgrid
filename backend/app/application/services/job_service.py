"""Job / scheduler management service.

Wraps the SchedulerPort (implemented with APScheduler in the
infrastructure layer) and the CollectorRunRepository so the API layer has
a single place to trigger and inspect collection runs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from app.application.interfaces.repositories import CollectorRunRepository
from app.domain.entities.collector_run import CollectorRun
from app.domain.value_objects.enums import TriggerSource


class SchedulerPort:
    """Abstract scheduler the application layer depends on."""

    async def trigger_run_now(self) -> None:
        raise NotImplementedError

    async def set_schedule(self, cron_expression: str) -> None:
        raise NotImplementedError

    def list_jobs(self) -> list:
        raise NotImplementedError


class JobService:
    def __init__(self, run_repository: CollectorRunRepository, scheduler: Optional[SchedulerPort] = None):
        self._runs = run_repository
        self._scheduler = scheduler

    async def start_run(self, trigger_source: TriggerSource) -> CollectorRun:
        run = CollectorRun(trigger_source=trigger_source, start_time=datetime.utcnow())
        return await self._runs.create(run)

    async def finish_run(self, run: CollectorRun) -> CollectorRun:
        run.finish()
        return await self._runs.update(run)

    async def history(self, offset: int = 0, limit: int = 50) -> tuple[Sequence[CollectorRun], int]:
        return await self._runs.list(offset=offset, limit=limit)

    async def run_now(self) -> None:
        if self._scheduler is not None:
            await self._scheduler.trigger_run_now()

    async def schedule(self, cron_expression: str) -> None:
        if self._scheduler is not None:
            await self._scheduler.set_schedule(cron_expression)

    def list_jobs(self) -> list:
        if self._scheduler is not None:
            return self._scheduler.list_jobs()
        return []
