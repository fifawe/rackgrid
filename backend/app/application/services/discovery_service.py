"""Discovery Service - orchestrates the full ingestion workflow described
in PROJECT_SPEC.md > Audit Engine:

    1. Receive payload
    2. Locate asset (AssetMatchingService)
    3. Compare existing values (AuditService)
    4. Insert audit records for changed fields only
    5. Update current asset state
    6. Update last_seen
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.application.dto.discovery_payload import DiscoveryPayloadDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.asset_matching_service import AssetMatchingService
from app.application.services.audit_service import AuditService
from app.domain.entities.asset import Asset
from app.domain.entities.hardware import HardwareInfo, OperatingSystemInfo
from app.domain.entities.network_interface import NetworkInterface
from app.domain.entities.storage_device import StorageDevice

# Plain stdlib logging, not app.infrastructure.config.logging's structlog
# wrapper - the application layer must not depend on infrastructure (see
# Clean Architecture layering in PROJECT_SPEC.md). structlog is itself
# configured on top of stdlib logging (see configure_logging()), so this
# still gets the same JSON output/handlers once the app has started.
import logging

logger = logging.getLogger(__name__)


def _collector_owned_values(asset: Asset) -> dict:
    return {
        "hostname": asset.hostname,
        "serial_number": asset.serial_number,
        "primary_ip": asset.primary_ip,
        "manufacturer": asset.hardware.manufacturer,
        "model": asset.hardware.model,
        "cpu_model": asset.hardware.cpu_model,
        "cpu_count": asset.hardware.cpu_count,
        "cpu_cores": asset.hardware.cpu_cores,
        "cpu_threads": asset.hardware.cpu_threads,
        "ram_gb": asset.hardware.ram_gb,
        "os_distribution": asset.os.distribution,
        "os_version": asset.os.version,
        "kernel_version": asset.os.kernel,
        "architecture": asset.os.architecture,
        "uptime_seconds": asset.os.uptime_seconds,
        "virtual_physical": asset.virtual_physical,
        "hypervisor": asset.hypervisor,
    }


def _payload_values(payload: DiscoveryPayloadDTO, virtual_physical: str) -> dict:
    hw, os_ = payload.hardware, payload.os
    return {
        "hostname": payload.hostname,
        "serial_number": payload.serial_number,
        "primary_ip": payload.primary_ip,
        "manufacturer": hw.manufacturer,
        "model": hw.model,
        "cpu_model": hw.cpu_model,
        "cpu_count": hw.cpu_count,
        "cpu_cores": hw.cpu_cores,
        "cpu_threads": hw.cpu_threads,
        "ram_gb": hw.ram_gb,
        "os_distribution": os_.distribution,
        "os_version": os_.version,
        "kernel_version": os_.kernel,
        "architecture": os_.architecture,
        "uptime_seconds": os_.uptime_seconds,
        "virtual_physical": virtual_physical,
        "hypervisor": payload.virtualization.hypervisor,
    }


class DiscoveryService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._matching = AssetMatchingService(uow.assets)
        self._audit = AuditService()

    async def ingest(
        self,
        payload: DiscoveryPayloadDTO,
        *,
        collector_run_id: Optional[int] = None,
    ) -> Asset:
        now = datetime.utcnow()

        # A caller-supplied collector_run_id that doesn't correspond to a
        # real row (a stale id, a manual test using the playbook's own
        # usage-comment example value, a run that was since pruned, ...)
        # must not take down discovery for a real host: asset_audit's
        # collector_run_id column is an FK to collector_runs, so citing a
        # nonexistent run_id previously crashed the whole request with an
        # unhandled IntegrityError. Degrade to "no run" instead.
        if collector_run_id is not None:
            run = await self._uow.collector_runs.get_by_id(collector_run_id)
            if run is None:
                logger.warning(
                    "collector_run_id=%s not found (hostname=%s); recording audit without it",
                    collector_run_id,
                    payload.hostname,
                )
                collector_run_id = None

        existing = await self._matching.find_match(payload)

        virtualization = payload.virtualization
        role = (virtualization.role or "").lower()
        if role == "guest":
            virtual_physical = "Virtual"
        elif role in ("host", "physical"):
            virtual_physical = "Physical"
        else:
            virtual_physical = "Unknown"

        new_values = _payload_values(payload, virtual_physical)

        if existing is None:
            asset = Asset(
                hostname=payload.hostname,
                serial_number=payload.serial_number,
                primary_ip=payload.primary_ip,
                hardware=HardwareInfo(**{
                    k: v for k, v in {
                        "manufacturer": payload.hardware.manufacturer,
                        "model": payload.hardware.model,
                        "cpu_model": payload.hardware.cpu_model,
                        "cpu_count": payload.hardware.cpu_count,
                        "cpu_cores": payload.hardware.cpu_cores,
                        "cpu_threads": payload.hardware.cpu_threads,
                        "ram_gb": payload.hardware.ram_gb,
                    }.items()
                }),
                os=OperatingSystemInfo(
                    distribution=payload.os.distribution,
                    version=payload.os.version,
                    kernel=payload.os.kernel,
                    architecture=payload.os.architecture,
                    uptime_seconds=payload.os.uptime_seconds,
                ),
                virtual_physical=virtual_physical,
                hypervisor=payload.virtualization.hypervisor,
                first_seen=now,
                last_seen=now,
                last_collection=now,
            )
            asset = await self._uow.assets.create(asset)
            # Every field on a brand new asset is a "change" from nothing.
            audit_records = self._audit.diff_fields(
                asset_id=asset.asset_id,
                collector_run_id=collector_run_id,
                old_values={k: None for k in new_values},
                new_values=new_values,
            )
        else:
            old_values = _collector_owned_values(existing)
            audit_records = self._audit.diff_fields(
                asset_id=existing.asset_id,
                collector_run_id=collector_run_id,
                old_values=old_values,
                new_values=new_values,
            )

            existing.hostname = payload.hostname
            existing.serial_number = payload.serial_number or existing.serial_number
            existing.primary_ip = payload.primary_ip or existing.primary_ip
            existing.hardware = HardwareInfo(
                manufacturer=payload.hardware.manufacturer,
                model=payload.hardware.model,
                cpu_model=payload.hardware.cpu_model,
                cpu_count=payload.hardware.cpu_count,
                cpu_cores=payload.hardware.cpu_cores,
                cpu_threads=payload.hardware.cpu_threads,
                ram_gb=payload.hardware.ram_gb,
            )
            existing.os = OperatingSystemInfo(
                distribution=payload.os.distribution,
                version=payload.os.version,
                kernel=payload.os.kernel,
                architecture=payload.os.architecture,
                uptime_seconds=payload.os.uptime_seconds,
            )
            existing.virtual_physical = virtual_physical
            existing.hypervisor = payload.virtualization.hypervisor
            existing.last_seen = now
            existing.last_collection = now
            asset = await self._uow.assets.update(existing)

        storage = [
            StorageDevice(
                device_name=s.device_name,
                filesystem_type=s.filesystem_type,
                mount_point=s.mount_point,
                capacity_gb=s.capacity_gb,
                asset_id=asset.asset_id,
            )
            for s in payload.storage
        ]
        network = [
            NetworkInterface(
                interface_name=n.interface_name,
                ip_address=n.ip_address,
                mac_address=n.mac_address,
                asset_id=asset.asset_id,
            )
            for n in payload.network
        ]
        await self._uow.assets.replace_storage(asset.asset_id, storage)
        await self._uow.assets.replace_network(asset.asset_id, network)

        if audit_records:
            await self._uow.audit.add_many(audit_records)

        return asset
