"""Storage device entity (mounted filesystem on an asset)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageDevice:
    device_name: str
    filesystem_type: Optional[str]
    mount_point: Optional[str]
    capacity_gb: Optional[float]
    storage_id: Optional[int] = None
    asset_id: Optional[int] = None

    def identity_key(self) -> tuple:
        return (self.device_name, self.mount_point)
