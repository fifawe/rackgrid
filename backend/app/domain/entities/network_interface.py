"""Network interface entity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class NetworkInterface:
    interface_name: str
    ip_address: Optional[str]
    mac_address: Optional[str]
    network_id: Optional[int] = None
    asset_id: Optional[int] = None

    def identity_key(self) -> tuple:
        return (self.interface_name, self.ip_address)
