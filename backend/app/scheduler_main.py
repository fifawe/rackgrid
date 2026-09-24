"""Standalone scheduler process.

Runs as its own container (service: `scheduler` in docker-compose),
built from the same backend image but launched with:

    uvicorn app.scheduler_main:app --host 0.0.0.0 --port 9000

It owns an APScheduler instance that periodically triggers a collector
(Ansible) run, and exposes a tiny internal HTTP API that the main backend
process calls to support "Run Now" and "Update Schedule" from the
dashboard's Job Management page.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from pydantic import BaseModel

from app.application.services.job_service import JobService
from app.domain.value_objects.enums import TriggerSource
from app.infrastructure.config.logging import configure_logging, get_logger
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import AsyncSessionFactory
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.scheduling.collector_runner import run_playbook

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://backend:8000")


def _resolve_timezone(tz_name: str) -> ZoneInfo:
    """Resolves the configured TZ to a ZoneInfo, falling back to UTC with
    a loud warning rather than crashing on a typo'd/unavailable zone -
    a broken timezone shouldn't take the whole scheduler down."""
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        logger.warning("unknown_timezone_falling_back_to_utc", requested_tz=tz_name)
        return ZoneInfo("UTC")


# Without this, APScheduler falls back to the OS default (UTC in an
# unconfigured container), so "0 2 * * *" silently means 2am UTC instead
# of 2am in the deployer's timezone. Set TZ (see deployment/.env.example)
# to fix that.
scheduler = AsyncIOScheduler(timezone=_resolve_timezone(settings.tz))
JOB_ID = "collector_run"


async def execute_collector_run(trigger_source: TriggerSource = TriggerSource.INTERNAL_SCHEDULER) -> None:
    async with AsyncSessionFactory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        job_service = JobService(uow.collector_runs)
        run = await job_service.start_run(trigger_source)
        await uow.commit()
        run_id = run.run_id

    return_code = await run_playbook(run_id, BACKEND_BASE_URL)

    async with AsyncSessionFactory() as session:
        uow = SqlAlchemyUnitOfWork(session)
        run = await uow.collector_runs.get_by_id(run_id)
        if run is not None:
            if return_code != 0 and run.success_count == 0:
                run.failure_count = max(run.failure_count, 1)
            run.finish()
            await uow.collector_runs.update(run)
            await uow.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.scheduler_enabled:
        scheduler.add_job(
            execute_collector_run,
            CronTrigger.from_crontab(settings.default_collector_cron),
            id=JOB_ID,
            replace_existing=True,
            kwargs={"trigger_source": TriggerSource.INTERNAL_SCHEDULER},
        )
        scheduler.start()
        logger.info("scheduler_started", cron=settings.default_collector_cron, timezone=settings.tz)
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Asset Inventory Scheduler", lifespan=lifespan)


class ScheduleRequest(BaseModel):
    cron_expression: str


@app.post("/internal/run")
async def run_now():
    scheduler.add_job(
        execute_collector_run,
        id=f"{JOB_ID}_manual_{os.urandom(4).hex()}",
        kwargs={"trigger_source": TriggerSource.MANUAL},
    )
    return {"status": "triggered"}


@app.post("/internal/schedule")
async def reschedule(payload: ScheduleRequest):
    scheduler.add_job(
        execute_collector_run,
        CronTrigger.from_crontab(payload.cron_expression),
        id=JOB_ID,
        replace_existing=True,
        kwargs={"trigger_source": TriggerSource.INTERNAL_SCHEDULER},
    )
    return {"status": "scheduled", "cron_expression": payload.cron_expression}


@app.get("/internal/jobs")
async def list_jobs():
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            }
        )
    return {"jobs": jobs}


@app.get("/internal/health")
async def health():
    return {"status": "ok"}
