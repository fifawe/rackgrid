"""Manually-managed business metadata for an asset.

The collector must NEVER write to any field on this entity - see
value_objects.enums.BUSINESS_OWNED_FIELDS.

`technology` is a free-form string rather than the Technology enum: the
dashboard's "dropdown with option to add new" UX lets users type a value
outside the built-in suggestion list, and the DB column has always been a
plain VARCHAR, so nothing downstream depends on it being enum-constrained.
The Technology enum still exists as the seed list of suggested options.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.domain.value_objects.enums import AssetStatus


@dataclass
class BusinessMetadata:
    asset_id: int
    asset_owner: Optional[str] = None
    support_team: Optional[str] = None
    application_name: Optional[str] = None
    business_service: Optional[str] = None
    environment: Optional[str] = None
    site: Optional[str] = None
    rack_number: Optional[str] = None
    technology: Optional[str] = None
    hw_support_expiry: Optional[date] = None
    os_support_expiry: Optional[date] = None
    status: AssetStatus = AssetStatus.ACTIVE
