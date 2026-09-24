"""The Asset aggregate root.

Discovery-owned fields (hardware/os/network identity) are set by the
collector pipeline. Business metadata lives in a separate entity and is
never touched by discovery. Status is derived from last_seen unless the
asset has been manually Retired.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from app.domain.entities.hardware import HardwareInfo, OperatingSystemInfo
from app.domain.entities.network_interface import NetworkInterface
from app.domain.entities.storage_device import StorageDevice
from app.domain.value_objects.enums import AssetStatus


@dataclass
class Asset:
    hostname: str
    serial_number: Optional[str] = None
    primary_ip: Optional[str] = None

    hardware: HardwareInfo = field(default_factory=HardwareInfo)
    os: OperatingSystemInfo = field(default_factory=OperatingSystemInfo)
    virtual_physical: str = "Unknown"
    hypervisor: Optional[str] = None

    storage: List[StorageDevice] = field(default_factory=list)
    network: List[NetworkInterface] = field(default_factory=list)

    asset_id: Optional[int] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    last_collection: Optional[datetime] = None

    def compute_status(
        self,
        manual_status: Optional[AssetStatus],
        active_threshold_days: int = 7,
        offline_threshold_days: int = 30,
        now: Optional[datetime] = None,
    ) -> AssetStatus:
        """Derive effective status.

        Retired is a manual-only terminal state and always wins. Otherwise
        status is computed from last_seen against the configured
        thresholds, per the Asset Lifecycle rules in the project charter.
        """
        if manual_status == AssetStatus.RETIRED:
            return AssetStatus.RETIRED

        now = now or datetime.utcnow()
        if self.last_seen is None:
            return AssetStatus.OFFLINE

        # last_seen may be naive (an Asset just built in this request, e.g.
        # during discovery, before ever round-tripping through the DB) or
        # tz-aware (one just loaded back via the repository mapper, which
        # attaches UTC tzinfo - see mappers._utc - so API responses carry
        # a proper offset instead of a bare timestamp browsers misread as
        # local time). Both sides are always UTC wall-clock either way, so
        # normalize both to naive here rather than requiring every caller
        # to agree on a convention.
        last_seen = self.last_seen.replace(tzinfo=None) if self.last_seen.tzinfo else self.last_seen
        if now.tzinfo:
            now = now.replace(tzinfo=None)

        age = now - last_seen
        if age <= timedelta(days=active_threshold_days):
            return AssetStatus.ACTIVE
        if age > timedelta(days=offline_threshold_days):
            return AssetStatus.OFFLINE
        # Between the two thresholds: not fresh enough to be Active, not
        # stale enough to be forced Offline - keep prior manual status if
        # set, otherwise default to Active (still within grace window).
        return manual_status or AssetStatus.ACTIVE
