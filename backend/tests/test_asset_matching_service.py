"""Unit tests for AssetMatchingService - priority order is
Serial Number > Primary IP > Hostname, per PROJECT_SPEC.md."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.dto.discovery_payload import DiscoveryPayloadDTO
from app.application.services.asset_matching_service import AssetMatchingService
from app.domain.entities.asset import Asset


def _payload(**kwargs) -> DiscoveryPayloadDTO:
    return DiscoveryPayloadDTO(hostname=kwargs.pop("hostname", "server01"), **kwargs)


@pytest.mark.asyncio
async def test_matches_by_serial_number_first():
    repo = AsyncMock()
    repo.get_by_serial_number.return_value = Asset(hostname="server01", asset_id=1)
    service = AssetMatchingService(repo)

    payload = _payload(serial_number="ABC123", primary_ip="10.0.0.1")
    match = await service.find_match(payload)

    assert match.asset_id == 1
    repo.get_by_serial_number.assert_awaited_once_with("ABC123")
    repo.get_by_primary_ip.assert_not_called()
    repo.get_by_hostname.assert_not_called()


@pytest.mark.asyncio
async def test_falls_back_to_primary_ip_when_serial_has_no_match():
    repo = AsyncMock()
    repo.get_by_serial_number.return_value = None
    repo.get_by_primary_ip.return_value = Asset(hostname="server01", asset_id=2)
    service = AssetMatchingService(repo)

    payload = _payload(serial_number="ABC123", primary_ip="10.0.0.1")
    match = await service.find_match(payload)

    assert match.asset_id == 2
    repo.get_by_hostname.assert_not_called()


@pytest.mark.asyncio
async def test_falls_back_to_hostname_when_no_identifiers_match():
    repo = AsyncMock()
    repo.get_by_serial_number.return_value = None
    repo.get_by_primary_ip.return_value = None
    repo.get_by_hostname.return_value = Asset(hostname="server01", asset_id=3)
    service = AssetMatchingService(repo)

    payload = _payload(serial_number="ABC123", primary_ip="10.0.0.1")
    match = await service.find_match(payload)

    assert match.asset_id == 3


@pytest.mark.asyncio
async def test_returns_none_when_nothing_matches_anywhere():
    repo = AsyncMock()
    repo.get_by_serial_number.return_value = None
    repo.get_by_hostname.return_value = None
    service = AssetMatchingService(repo)

    payload = _payload(serial_number="ABC123")
    match = await service.find_match(payload)
    assert match is None


@pytest.mark.parametrize(
    "placeholder",
    ["Not Specified", "not specified", "  Not Specified  ", "NA", "N/A", "None", "Unknown", ""],
)
@pytest.mark.asyncio
async def test_ignores_bios_placeholder_serial_numbers(placeholder):
    """Regression test: unconfigured KVM/QEMU/Proxmox VMs commonly all
    report the SAME literal placeholder serial (most often "Not
    Specified") identically. Matching on that would merge every such VM
    into a single asset record - "only the last host collected"."""
    repo = AsyncMock()
    repo.get_by_primary_ip.return_value = Asset(hostname="server01", asset_id=2)
    service = AssetMatchingService(repo)

    payload = _payload(serial_number=placeholder, primary_ip="10.0.0.1")
    match = await service.find_match(payload)

    repo.get_by_serial_number.assert_not_called()
    assert match.asset_id == 2


@pytest.mark.asyncio
async def test_two_hosts_with_same_placeholder_serial_do_not_collide():
    """Even more direct version of the above: two different hosts that
    both report "Not Specified" must resolve to two different assets,
    keyed off their (different) primary IPs instead."""
    repo = AsyncMock()
    repo.get_by_primary_ip.side_effect = lambda ip: {
        "10.0.0.1": Asset(hostname="host-a", asset_id=1),
        "10.0.0.2": Asset(hostname="host-b", asset_id=2),
    }.get(ip)
    service = AssetMatchingService(repo)

    match_a = await service.find_match(_payload(hostname="host-a", serial_number="Not Specified", primary_ip="10.0.0.1"))
    match_b = await service.find_match(_payload(hostname="host-b", serial_number="Not Specified", primary_ip="10.0.0.2"))

    assert match_a.asset_id != match_b.asset_id
    repo.get_by_serial_number.assert_not_called()
