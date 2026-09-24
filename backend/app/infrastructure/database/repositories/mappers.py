"""Conversion functions between SQLAlchemy ORM models and domain
entities. Keeping this in one place is what lets the domain/application
layers stay persistence-agnostic (Clean Architecture)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.domain.entities.asset import Asset
from app.domain.entities.asset_attachment import AssetAttachment
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.business_metadata import BusinessMetadata
from app.domain.entities.collector_run import CollectorRun
from app.domain.entities.hardware import HardwareInfo, OperatingSystemInfo
from app.domain.entities.network_interface import NetworkInterface
from app.domain.entities.site import Site
from app.domain.entities.support_team import SupportTeam
from app.domain.entities.storage_device import StorageDevice
from app.domain.value_objects.enums import AssetStatus, CollectorRunStatus, TriggerSource
from app.infrastructure.database.models.asset_attachment import AssetAttachmentModel
from app.infrastructure.database.models.asset_audit import AssetAuditModel
from app.infrastructure.database.models.asset_business import AssetBusinessModel
from app.infrastructure.database.models.collector_run import CollectorRunModel
from app.infrastructure.database.models.inventory_asset import InventoryAssetModel
from app.infrastructure.database.models.inventory_network import InventoryNetworkModel
from app.infrastructure.database.models.inventory_storage import InventoryStorageModel
from app.infrastructure.database.models.site import SiteModel
from app.infrastructure.database.models.support_team import SupportTeamModel


def _utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Attaches UTC tzinfo to a naive datetime read back from the DB.

    Every timestamp is written with `datetime.utcnow()` (naive, but
    always UTC wall-clock), and MySQL's DATETIME columns don't store
    timezone info, so it comes back naive too. Left naive, Pydantic
    serializes it over the API with no UTC offset - which browsers then
    parse as already being in the viewer's own local timezone, silently
    displaying UTC values mislabeled as local (Job Management run
    history, asset first/last seen, audit history all showed this).
    Attaching tzinfo here, once, fixes every one of those call sites: the
    browser's `new Date(...)` then correctly converts to local time for
    display.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt
    return dt.replace(tzinfo=timezone.utc)


def storage_to_domain(m: InventoryStorageModel) -> StorageDevice:
    return StorageDevice(
        storage_id=m.storage_id,
        asset_id=m.asset_id,
        device_name=m.device_name,
        filesystem_type=m.filesystem_type,
        mount_point=m.mount_point,
        capacity_gb=m.capacity_gb,
    )


def network_to_domain(m: InventoryNetworkModel) -> NetworkInterface:
    return NetworkInterface(
        network_id=m.network_id,
        asset_id=m.asset_id,
        interface_name=m.interface_name,
        ip_address=m.ip_address,
        mac_address=m.mac_address,
    )


def asset_to_domain(m: InventoryAssetModel) -> Asset:
    return Asset(
        asset_id=m.asset_id,
        hostname=m.hostname,
        serial_number=m.serial_number,
        primary_ip=m.primary_ip,
        hardware=HardwareInfo(
            manufacturer=m.manufacturer,
            model=m.model,
            cpu_model=m.cpu_model,
            cpu_count=m.cpu_count,
            cpu_cores=m.cpu_cores,
            cpu_threads=m.cpu_threads,
            ram_gb=m.ram_gb,
        ),
        os=OperatingSystemInfo(
            distribution=m.os_distribution,
            version=m.os_version,
            kernel=m.kernel_version,
            architecture=m.architecture,
            uptime_seconds=m.uptime_seconds,
        ),
        virtual_physical=m.virtual_physical or "Unknown",
        hypervisor=m.hypervisor,
        storage=[storage_to_domain(s) for s in m.storage],
        network=[network_to_domain(n) for n in m.network],
        first_seen=_utc(m.first_seen),
        last_seen=_utc(m.last_seen),
        last_collection=_utc(m.last_collection),
    )


def business_to_domain(m: AssetBusinessModel) -> BusinessMetadata:
    return BusinessMetadata(
        asset_id=m.asset_id,
        asset_owner=m.asset_owner,
        support_team=m.support_team,
        application_name=m.application_name,
        business_service=m.business_service,
        environment=m.environment,
        site=m.site,
        rack_number=m.rack_number,
        technology=m.technology,
        hw_support_expiry=m.hw_support_expiry,
        os_support_expiry=m.os_support_expiry,
        status=AssetStatus(m.status) if m.status else AssetStatus.ACTIVE,
    )


def site_to_domain(m: SiteModel) -> Site:
    return Site(
        site_id=m.site_id,
        name=m.name,
        code=m.code,
        city=m.city,
    )


def support_team_to_domain(m: SupportTeamModel) -> SupportTeam:
    return SupportTeam(
        support_team_id=m.support_team_id,
        name=m.name,
        contact_number=m.contact_number,
        email=m.email,
        location=m.location,
        notes=m.notes,
    )


def attachment_to_domain(m: AssetAttachmentModel) -> AssetAttachment:
    return AssetAttachment(
        attachment_id=m.attachment_id,
        asset_id=m.asset_id,
        original_filename=m.original_filename,
        stored_filename=m.stored_filename,
        content_type=m.content_type,
        file_size=m.file_size,
        uploaded_by=m.uploaded_by,
        uploaded_at=_utc(m.uploaded_at),
    )


def audit_to_domain(m: AssetAuditModel) -> AuditRecord:
    return AuditRecord(
        audit_id=m.audit_id,
        asset_id=m.asset_id,
        collector_run_id=m.collector_run_id,
        field_name=m.field_name,
        old_value=m.old_value,
        new_value=m.new_value,
        source=m.source,
        change_timestamp=_utc(m.change_timestamp),
    )


def run_to_domain(m: CollectorRunModel) -> CollectorRun:
    return CollectorRun(
        run_id=m.run_id,
        trigger_source=TriggerSource(m.trigger_source),
        start_time=_utc(m.start_time),
        end_time=_utc(m.end_time),
        status=CollectorRunStatus(m.status),
        assets_processed=m.assets_processed,
        success_count=m.success_count,
        failure_count=m.failure_count,
    )
