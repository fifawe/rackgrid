"""A single execution of the discovery/collection process."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.domain.value_objects.enums import CollectorRunStatus, TriggerSource


@dataclass
class CollectorRun:
    trigger_source: TriggerSource
    start_time: datetime
    run_id: Optional[int] = None
    end_time: Optional[datetime] = None
    status: CollectorRunStatus = CollectorRunStatus.RUNNING
    assets_processed: int = 0
    success_count: int = 0
    failure_count: int = 0

    def record_success(self) -> None:
        self.assets_processed += 1
        self.success_count += 1

    def record_failure(self) -> None:
        self.assets_processed += 1
        self.failure_count += 1

    def finish(self) -> None:
        self.end_time = datetime.utcnow()
        if self.failure_count == 0:
            self.status = CollectorRunStatus.SUCCESS
        elif self.success_count == 0:
            self.status = CollectorRunStatus.FAILED
        else:
            self.status = CollectorRunStatus.PARTIAL
