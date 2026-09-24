"""Pydantic schemas for platform branding settings (title + logo)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PublicSettingsOut(BaseModel):
    platform_title: str
    logo_url: Optional[str] = None
    version: str


class PlatformTitleUpdate(BaseModel):
    platform_title: str = Field(min_length=1, max_length=255)
