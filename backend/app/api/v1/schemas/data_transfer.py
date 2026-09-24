"""Pydantic schemas for the Import/Export (data transfer) endpoints."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ImportRowErrorOut(BaseModel):
    row: int
    message: str


class ImportResultOut(BaseModel):
    created: int
    updated: int
    errors: List[ImportRowErrorOut]
