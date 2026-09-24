"""Inventory Import - CSV round trip.

Import reuses the same column names the CSV export writes (see
routes/assets.py's `_CSV_COLUMNS` and routes/data.py's export bundle), so
a user can export the current inventory, edit it in a spreadsheet, and
re-import it.

Design decisions (explicitly confirmed with the user rather than the
safer defaults that were offered - see CHANGELOG v1.9.0):

  - A row whose identifiers don't match any existing asset creates a
    NEW asset record, exactly like an unmatched discovery payload
    would. Matching uses the same priority as the collector
    (AssetMatchingService: Serial Number, then Primary IP, then
    Hostname).
  - A matched row may overwrite collector-owned hardware/OS fields as
    well as business metadata - NOT restricted to business fields
    only.
  - To keep a sparse/partially-filled CSV from silently wiping out
    real data, a BLANK cell on an UPDATE means "leave the existing
    value unchanged" (mirroring the Bulk Edit page's existing
    convention: only populated fields are applied). A blank cell on a
    newly CREATED asset simply means "no value provided" - there's
    nothing to preserve.
  - storage/network device rows are never touched by Import - the
    export format doesn't carry that granular per-device data.
  - Collector-owned field changes ARE audited (source="import"), the
    same way discovery audits them. Business metadata changes are
    never audited anywhere in this app (AuditService.diff_fields only
    ever considers COLLECTOR_OWNED_FIELDS) and Import doesn't change
    that existing behavior.
  - Import does not refresh last_seen/last_collection - those reflect
    when the collector actually last saw the host, and a bulk CSV
    edit isn't that.
  - A row that fails to parse (e.g. non-numeric CPU Count, an
    unrecognized Status value) is rejected in full and reported as an
    error; nothing on that row is written. Each row is committed
    independently, so one bad row never rolls back rows already
    applied earlier in the same file.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime
from typing import List, Optional

from app.application.dto.discovery_payload import DiscoveryPayloadDTO
from app.application.interfaces.unit_of_work import UnitOfWork
from app.application.services.asset_business_service import AssetBusinessService
from app.application.services.asset_matching_service import AssetMatchingService
from app.application.services.audit_service import AuditService
from app.domain.entities.asset import Asset
from app.domain.entities.hardware import HardwareInfo, OperatingSystemInfo
from app.domain.value_objects.enums import AssetStatus

REQUIRED_COLUMN = "Hostname"


@dataclass
class ImportRowError:
    row: int
    message: str


@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    errors: List[ImportRowError] = dc_field(default_factory=list)


def _clean(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _parse_int(raw: Optional[str], label: str) -> Optional[int]:
    value = _clean(raw)
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError as exc:
        raise ValueError(f"{label} must be a whole number") from exc


def _parse_float(raw: Optional[str], label: str) -> Optional[float]:
    value = _clean(raw)
    if value is None:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a number") from exc


def _parse_date(raw: Optional[str], label: str) -> Optional[date]:
    value = _clean(raw)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a date in YYYY-MM-DD format") from exc


def _parse_status(raw: Optional[str]) -> Optional[AssetStatus]:
    value = _clean(raw)
    if value is None:
        return None
    for status in AssetStatus:
        if status.value.lower() == value.lower():
            return status
    valid = ", ".join(s.value for s in AssetStatus)
    raise ValueError(f"Status must be one of: {valid}")


class InventoryImportService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow
        self._matching = AssetMatchingService(uow.assets)
        self._audit = AuditService()
        self._business = AssetBusinessService(uow)

    async def import_csv(self, raw_bytes: bytes) -> ImportResult:
        text = raw_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        result = ImportResult()

        if not reader.fieldnames or REQUIRED_COLUMN not in reader.fieldnames:
            result.errors.append(
                ImportRowError(row=1, message=f'CSV must include a "{REQUIRED_COLUMN}" column header')
            )
            return result

        for line_number, row in enumerate(reader, start=2):
            try:
                parsed = self._parse_row(row)
            except ValueError as exc:
                result.errors.append(ImportRowError(row=line_number, message=str(exc)))
                continue

            try:
                created = await self._apply_row(parsed)
                await self._uow.commit()
            except Exception as exc:  # noqa: BLE001 - isolate this row, keep importing
                await self._uow.rollback()
                result.errors.append(ImportRowError(row=line_number, message=f"Save failed: {exc}"))
                continue

            if created:
                result.created += 1
            else:
                result.updated += 1

        return result

    def _parse_row(self, row: dict) -> dict:
        hostname = _clean(row.get("Hostname"))
        if not hostname:
            raise ValueError("Hostname is required")

        return {
            "hostname": hostname,
            "serial_number": _clean(row.get("Serial Number")),
            "primary_ip": _clean(row.get("Primary IP")),
            "status": _parse_status(row.get("Status")),
            "virtual_physical": _clean(row.get("Virtual/Physical")),
            "hypervisor": _clean(row.get("Hypervisor")),
            "manufacturer": _clean(row.get("Manufacturer")),
            "model": _clean(row.get("Model")),
            "cpu_model": _clean(row.get("CPU Model")),
            "cpu_count": _parse_int(row.get("CPU Count"), "CPU Count"),
            "cpu_cores": _parse_int(row.get("CPU Cores"), "CPU Cores"),
            "cpu_threads": _parse_int(row.get("CPU Threads"), "CPU Threads"),
            "ram_gb": _parse_float(row.get("RAM (GB)"), "RAM (GB)"),
            "os_distribution": _clean(row.get("OS Distribution")),
            "os_version": _clean(row.get("OS Version")),
            "kernel_version": _clean(row.get("Kernel Version")),
            "architecture": _clean(row.get("Architecture")),
            "uptime_seconds": _parse_int(row.get("Uptime (s)"), "Uptime (s)"),
            "support_team": _clean(row.get("Support Team")),
            "asset_owner": _clean(row.get("Asset Owner")),
            "application_name": _clean(row.get("Application Name")),
            "business_service": _clean(row.get("Business Service")),
            "environment": _clean(row.get("Environment")),
            "site": _clean(row.get("Site")),
            "rack_number": _clean(row.get("Rack Number")),
            "technology": _clean(row.get("Technology")),
            "hw_support_expiry": _parse_date(row.get("HW Support Expiry"), "HW Support Expiry"),
            "os_support_expiry": _parse_date(row.get("OS Support Expiry"), "OS Support Expiry"),
        }

    async def _apply_row(self, row: dict) -> bool:
        """Applies one already-parsed row. Returns True if a new asset
        was created, False if an existing one was updated."""
        match_payload = DiscoveryPayloadDTO(
            hostname=row["hostname"],
            serial_number=row["serial_number"],
            primary_ip=row["primary_ip"],
        )
        existing = await self._matching.find_match(match_payload)
        now = datetime.utcnow()

        collector_fields = {
            "hostname": row["hostname"],
            "serial_number": row["serial_number"],
            "primary_ip": row["primary_ip"],
            "manufacturer": row["manufacturer"],
            "model": row["model"],
            "cpu_model": row["cpu_model"],
            "cpu_count": row["cpu_count"],
            "cpu_cores": row["cpu_cores"],
            "cpu_threads": row["cpu_threads"],
            "ram_gb": row["ram_gb"],
            "os_distribution": row["os_distribution"],
            "os_version": row["os_version"],
            "kernel_version": row["kernel_version"],
            "architecture": row["architecture"],
            "uptime_seconds": row["uptime_seconds"],
            "virtual_physical": row["virtual_physical"],
            "hypervisor": row["hypervisor"],
        }
        business_fields = {
            "support_team": row["support_team"],
            "asset_owner": row["asset_owner"],
            "application_name": row["application_name"],
            "business_service": row["business_service"],
            "environment": row["environment"],
            "site": row["site"],
            "rack_number": row["rack_number"],
            "technology": row["technology"],
            "hw_support_expiry": row["hw_support_expiry"],
            "os_support_expiry": row["os_support_expiry"],
        }
        if row["status"] is not None:
            business_fields["status"] = row["status"]

        if existing is None:
            return await self._create(row, collector_fields, business_fields, now)
        return await self._update(existing, row, collector_fields, business_fields, now)

    async def _create(self, row: dict, collector_fields: dict, business_fields: dict, now: datetime) -> bool:
        asset = Asset(
            hostname=row["hostname"],
            serial_number=row["serial_number"],
            primary_ip=row["primary_ip"],
            hardware=HardwareInfo(
                manufacturer=row["manufacturer"],
                model=row["model"],
                cpu_model=row["cpu_model"],
                cpu_count=row["cpu_count"],
                cpu_cores=row["cpu_cores"],
                cpu_threads=row["cpu_threads"],
                ram_gb=row["ram_gb"],
            ),
            os=OperatingSystemInfo(
                distribution=row["os_distribution"],
                version=row["os_version"],
                kernel=row["kernel_version"],
                architecture=row["architecture"],
                uptime_seconds=row["uptime_seconds"],
            ),
            virtual_physical=row["virtual_physical"] or "Unknown",
            hypervisor=row["hypervisor"],
            first_seen=now,
            last_seen=now,
            last_collection=now,
        )
        asset = await self._uow.assets.create(asset)

        audit_records = self._audit.diff_fields(
            asset_id=asset.asset_id,
            collector_run_id=None,
            old_values={k: None for k in collector_fields},
            new_values=collector_fields,
            source="import",
            now=now,
        )
        if audit_records:
            await self._uow.audit.add_many(audit_records)

        business_updates = {k: v for k, v in business_fields.items() if v is not None}
        if business_updates:
            await self._business.upsert(asset.asset_id, business_updates)

        return True

    async def _update(
        self, existing: Asset, row: dict, collector_fields: dict, business_fields: dict, now: datetime
    ) -> bool:
        old_collector_values = {
            "hostname": existing.hostname,
            "serial_number": existing.serial_number,
            "primary_ip": existing.primary_ip,
            "manufacturer": existing.hardware.manufacturer,
            "model": existing.hardware.model,
            "cpu_model": existing.hardware.cpu_model,
            "cpu_count": existing.hardware.cpu_count,
            "cpu_cores": existing.hardware.cpu_cores,
            "cpu_threads": existing.hardware.cpu_threads,
            "ram_gb": existing.hardware.ram_gb,
            "os_distribution": existing.os.distribution,
            "os_version": existing.os.version,
            "kernel_version": existing.os.kernel,
            "architecture": existing.os.architecture,
            "uptime_seconds": existing.os.uptime_seconds,
            "virtual_physical": existing.virtual_physical,
            "hypervisor": existing.hypervisor,
        }
        # Blank cell (None here) means "leave unchanged" on an update -
        # Hostname is always non-blank already (validated in _parse_row).
        new_collector_values = {
            k: (collector_fields[k] if collector_fields[k] is not None else old_collector_values[k])
            for k in old_collector_values
        }
        new_collector_values["hostname"] = row["hostname"]

        audit_records = self._audit.diff_fields(
            asset_id=existing.asset_id,
            collector_run_id=None,
            old_values=old_collector_values,
            new_values=new_collector_values,
            source="import",
            now=now,
        )

        existing.hostname = new_collector_values["hostname"]
        existing.serial_number = new_collector_values["serial_number"]
        existing.primary_ip = new_collector_values["primary_ip"]
        existing.hardware = HardwareInfo(
            manufacturer=new_collector_values["manufacturer"],
            model=new_collector_values["model"],
            cpu_model=new_collector_values["cpu_model"],
            cpu_count=new_collector_values["cpu_count"],
            cpu_cores=new_collector_values["cpu_cores"],
            cpu_threads=new_collector_values["cpu_threads"],
            ram_gb=new_collector_values["ram_gb"],
        )
        existing.os = OperatingSystemInfo(
            distribution=new_collector_values["os_distribution"],
            version=new_collector_values["os_version"],
            kernel=new_collector_values["kernel_version"],
            architecture=new_collector_values["architecture"],
            uptime_seconds=new_collector_values["uptime_seconds"],
        )
        existing.virtual_physical = new_collector_values["virtual_physical"]
        existing.hypervisor = new_collector_values["hypervisor"]
        await self._uow.assets.update(existing)

        if audit_records:
            await self._uow.audit.add_many(audit_records)

        business_updates = {k: v for k, v in business_fields.items() if v is not None}
        if business_updates:
            await self._business.upsert(existing.asset_id, business_updates)

        return False
