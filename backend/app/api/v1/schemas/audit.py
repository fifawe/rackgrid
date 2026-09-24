"""Pydantic schemas for audit history endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AuditRecordOut(BaseModel):
    audit_id: Optional[int] = None
    asset_id: int
    collector_run_id: Optional[int] = None
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_timestamp: datetime
    source: str


class AuditListResponse(BaseModel):
    items: List[AuditRecordOut]
    total: int
    offset: int
    limit: int
