"""A physical site/location. Deliberately not referenced by a foreign
key from asset_business.site - see infrastructure/database/models/site.py
for why."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Site:
    name: str
    site_id: Optional[int] = None
    code: Optional[str] = None
    city: Optional[str] = None
