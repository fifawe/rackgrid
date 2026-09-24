"""A support team contact record - the structured directory an asset's
`asset_business.support_team` field selects from. Mirrors Site: kept as
a free-text column on asset_business (see infrastructure/database/models
/asset_business.py) rather than a hard foreign key, but unlike Site the
asset-side field is a strict dropdown (no free typing) so every value on
an asset should correspond to a row here."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SupportTeam:
    name: str
    support_team_id: Optional[int] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
