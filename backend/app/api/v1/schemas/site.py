"""Pydantic schemas for the Site reference-data endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SiteOut(BaseModel):
    site_id: int
    name: str
    code: Optional[str] = None
    city: Optional[str] = None

    model_config = {"from_attributes": True}


class SiteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=255)


class SiteUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=255)
