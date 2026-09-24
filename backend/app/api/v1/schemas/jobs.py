"""Pydantic schemas for scheduler / job management endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CollectorRunOut(BaseModel):
    run_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    assets_processed: int
    success_count: int
    failure_count: int
    trigger_source: str


class RunHistoryResponse(BaseModel):
    items: List[CollectorRunOut]
    total: int
    offset: int
    limit: int


class ScheduleRequest(BaseModel):
    cron_expression: str


class ScheduledJobOut(BaseModel):
    id: str
    next_run_time: Optional[str] = None


class JobsResponse(BaseModel):
    jobs: List[ScheduledJobOut]
