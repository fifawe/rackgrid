"""Integration tests for DiscoveryService against a real (in-memory
SQLite) UnitOfWork - covers asset creation, duplicate prevention via
matching, change-only audit recording, and business-field protection."""
from __future__ import annotations

import pytest

from app.application.dto.discovery_payload import DiscoveryPayloadDTO, HardwareDTO, OsDTO
from app.application.services.discovery_service import DiscoveryService


def _payload(hostname="server01", serial="SN-001", ip="10.0.0.1", ram=16, os_version="8.8"):
    return DiscoveryPayloadDTO(
        hostname=hostname,
        serial_number=serial,
        primary_ip=ip,
        hardware=HardwareDTO(ram_gb=ram),
        os=OsDTO(distribution="RHEL", version=os_version),
    )


@pytest.mark.asyncio
async def test_first_discovery_creates_a_new_asset(uow):
    service = DiscoveryService(uow)
    asset = await service.ingest(_payload())
    await uow.commit()

    assert asset.asset_id is not None
    assert asset.hostname == "server01"

    all_assets, total = await uow.assets.list()
    assert total == 1


@pytest.mark.asyncio
async def test_second_discovery_with_same_serial_updates_not_duplicates(uow):
    service = DiscoveryService(uow)
    first = await service.ingest(_payload(ram=16))
    await uow.commit()

    second = await service.ingest(_payload(hostname="server01-renamed", ram=32))
    await uow.commit()

    assert second.asset_id == first.asset_id

    _, total = await uow.assets.list()
    assert total == 1, "duplicate assets must be prevented via serial-number matching"


@pytest.mark.asyncio
async def test_ram_change_is_recorded_as_a_single_audit_entry(uow):
    service = DiscoveryService(uow)
    await service.ingest(_payload(ram=16))
    await uow.commit()

    await service.ingest(_payload(ram=32))
    await uow.commit()

    records, total = await uow.audit.list()
    ram_changes = [r for r in records if r.field_name == "ram_gb"]
    # One entry from asset creation (None -> 16) and one from the actual
    # 16 -> 32 update - never a full snapshot, always change-only.
    assert len(ram_changes) == 2
    update_entry = next(r for r in ram_changes if r.old_value == "16")
    assert update_entry.new_value == "32"


@pytest.mark.asyncio
async def test_no_audit_entries_when_nothing_changes(uow):
    service = DiscoveryService(uow)
    await service.ingest(_payload())
    await uow.commit()

    first_run_records, _ = await uow.audit.list()

    await service.ingest(_payload())
    await uow.commit()

    second_run_records, total = await uow.audit.list()
    assert total == len(first_run_records), "re-submitting identical data must not add new audit rows"


@pytest.mark.asyncio
async def test_matches_by_hostname_when_no_serial_or_ip(uow):
    service = DiscoveryService(uow)
    no_id_payload = DiscoveryPayloadDTO(hostname="edge-device-01")
    first = await service.ingest(no_id_payload)
    await uow.commit()

    second = await service.ingest(DiscoveryPayloadDTO(hostname="edge-device-01", os=OsDTO(version="2.0")))
    await uow.commit()

    assert second.asset_id == first.asset_id
    _, total = await uow.assets.list()
    assert total == 1


@pytest.mark.asyncio
async def test_bogus_collector_run_id_does_not_crash_ingestion(uow):
    """Regression test: citing a collector_run_id that doesn't exist (a
    stale id, or the literal `42` from playbook.yml's own usage-comment
    example, copy-pasted for a manual test) used to crash the whole
    request with an unhandled FK IntegrityError on the asset_audit
    insert. It must degrade gracefully instead."""
    service = DiscoveryService(uow)

    asset = await service.ingest(_payload(), collector_run_id=999999)
    await uow.commit()

    assert asset.asset_id is not None

    records, _ = await uow.audit.list()
    assert all(r.collector_run_id is None for r in records)


@pytest.mark.asyncio
async def test_discovery_never_touches_business_metadata(uow):
    from app.application.services.asset_business_service import AssetBusinessService

    service = DiscoveryService(uow)
    asset = await service.ingest(_payload())
    await uow.commit()

    biz_service = AssetBusinessService(uow)
    await biz_service.upsert(asset.asset_id, {"asset_owner": "alice", "environment": "Production"})
    await uow.commit()

    # A subsequent discovery run with all-new hardware values must not
    # alter the manually-set business metadata.
    await service.ingest(_payload(ram=999))
    await uow.commit()

    business = await uow.business_metadata.get_by_asset_id(asset.asset_id)
    assert business.asset_owner == "alice"
    assert business.environment == "Production"
