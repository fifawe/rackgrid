"""Scheduler / job management endpoints (Job Management page)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_scheduler_client, get_uow, require_role
from app.api.v1.schemas.jobs import (
    JobsResponse,
    RunHistoryResponse,
    ScheduledJobOut,
    ScheduleRequest,
    CollectorRunOut,
)
from app.application.services.job_service import JobService
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.scheduling.scheduler_client import HttpSchedulerAdapter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobsResponse)
async def list_jobs(
    scheduler: HttpSchedulerAdapter = Depends(get_scheduler_client),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    jobs = scheduler.list_jobs()
    return JobsResponse(jobs=[ScheduledJobOut(**j) for j in jobs])


@router.post("/run", status_code=202)
async def run_now(
    scheduler: HttpSchedulerAdapter = Depends(get_scheduler_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    job_service = JobService(uow.collector_runs, scheduler)
    await job_service.run_now()
    return {"status": "triggered"}


@router.post("/schedule", status_code=200)
async def set_schedule(
    body: ScheduleRequest,
    scheduler: HttpSchedulerAdapter = Depends(get_scheduler_client),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.ADMIN)),
):
    job_service = JobService(uow.collector_runs, scheduler)
    await job_service.schedule(body.cron_expression)
    return {"status": "scheduled", "cron_expression": body.cron_expression}


@router.get("/history", response_model=RunHistoryResponse)
async def run_history(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    job_service = JobService(uow.collector_runs)
    runs, total = await job_service.history(offset=offset, limit=limit)
    items = [
        CollectorRunOut(
            run_id=r.run_id,
            start_time=r.start_time,
            end_time=r.end_time,
            status=r.status.value,
            assets_processed=r.assets_processed,
            success_count=r.success_count,
            failure_count=r.failure_count,
            trigger_source=r.trigger_source.value,
        )
        for r in runs
    ]
    return RunHistoryResponse(items=items, total=total, offset=offset, limit=limit)
