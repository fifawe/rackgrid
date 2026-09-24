"""Pydantic schemas for the Support Team directory endpoints."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SupportTeamOut(BaseModel):
    support_team_id: int
    name: str
    contact_number: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class SupportTeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class SupportTeamUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    contact_number: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=255)
    location: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None
