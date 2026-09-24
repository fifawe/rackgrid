"""Pydantic schemas for asset design-document attachment endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AttachmentOut(BaseModel):
    attachment_id: int
    original_filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}
