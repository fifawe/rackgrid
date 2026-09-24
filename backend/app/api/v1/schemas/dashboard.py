"""Pydantic schema for the dashboard summary endpoint."""
from __future__ import annotations

from datetime import date
from typing import Dict, List

from pydantic import BaseModel


class ExpiringSupportItemOut(BaseModel):
    asset_id: int
    hostname: str
    support_type: str  # "Hardware" | "OS"
    expiry_date: date
    days_remaining: int


class DashboardSummaryOut(BaseModel):
    total_assets: int
    active_assets: int
    offline_assets: int
    retired_assets: int
    physical_assets: int
    virtual_assets: int
    by_technology: Dict[str, int]
    by_site: Dict[str, int]
    by_environment: Dict[str, int]
    by_os_family: Dict[str, int]
    by_manufacturer: Dict[str, int]
    by_model: Dict[str, int]
    expiring_support_count: int
    expiring_support: List[ExpiringSupportItemOut]
