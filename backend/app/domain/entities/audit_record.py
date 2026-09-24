"""A single field-level change recorded by the audit engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AuditRecord:
    asset_id: int
    collector_run_id: Optional[int]
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    source: str
    change_timestamp: datetime
    audit_id: Optional[int] = None
