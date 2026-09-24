"""Asset Matching Engine.

Implements the matching priority mandated by the project spec:

    1. Serial Number
    2. Primary IP
    3. Hostname

The first strategy that yields a non-empty identifier AND a matching
existing asset wins. If no existing asset matches by any available
identifier, the caller should create a new asset.
"""
from __future__ import annotations

from typing import Optional

from app.application.dto.discovery_payload import DiscoveryPayloadDTO
from app.application.interfaces.repositories import AssetRepository
from app.domain.entities.asset import Asset
from app.domain.value_objects.enums import is_usable_identifier


class AssetMatchingService:
    def __init__(self, asset_repository: AssetRepository):
        self._assets = asset_repository

    async def find_match(self, payload: DiscoveryPayloadDTO) -> Optional[Asset]:
        # A non-empty serial_number is normally authoritative, but a
        # known BIOS/hypervisor placeholder (e.g. "Not Specified", which
        # unconfigured KVM/QEMU/Proxmox VMs commonly all report
        # identically) is NOT a real identifier - matching on it would
        # merge every host that reports it into one asset. Treat those
        # the same as "no serial available" and fall through.
        if is_usable_identifier(payload.serial_number):
            match = await self._assets.get_by_serial_number(payload.serial_number)
            if match:
                return match

        if payload.primary_ip:
            match = await self._assets.get_by_primary_ip(payload.primary_ip)
            if match:
                return match

        if payload.hostname:
            match = await self._assets.get_by_hostname(payload.hostname)
            if match:
                return match

        return None
