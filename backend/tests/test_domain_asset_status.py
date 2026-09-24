"""Unit tests for Asset.compute_status - the Active/Offline/Retired
lifecycle rules from PROJECT_SPEC.md > Status Rules."""
from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.entities.asset import Asset
from app.domain.value_objects.enums import AssetStatus


def _asset(last_seen):
    return Asset(hostname="host1", last_seen=last_seen)


def test_active_when_seen_recently():
    now = datetime(2026, 1, 10, 12, 0, 0)
    asset = _asset(now - timedelta(days=3))
    assert asset.compute_status(None, now=now) == AssetStatus.ACTIVE


def test_offline_when_not_seen_for_over_30_days():
    now = datetime(2026, 1, 10, 12, 0, 0)
    asset = _asset(now - timedelta(days=45))
    assert asset.compute_status(None, now=now) == AssetStatus.OFFLINE


def test_offline_when_never_seen():
    asset = Asset(hostname="host1", last_seen=None)
    assert asset.compute_status(None) == AssetStatus.OFFLINE


def test_retired_is_manual_only_and_always_wins():
    now = datetime(2026, 1, 10, 12, 0, 0)
    # Even a freshly-seen asset stays Retired once manually set.
    asset = _asset(now - timedelta(hours=1))
    assert asset.compute_status(AssetStatus.RETIRED, now=now) == AssetStatus.RETIRED


def test_collector_cannot_force_retired_status_via_compute():
    # compute_status only ever returns RETIRED when the manual status
    # passed in is already RETIRED - discovery never supplies that.
    now = datetime(2026, 1, 10, 12, 0, 0)
    asset = _asset(now - timedelta(days=45))
    assert asset.compute_status(AssetStatus.ACTIVE, now=now) in (AssetStatus.ACTIVE, AssetStatus.OFFLINE)
    assert asset.compute_status(AssetStatus.ACTIVE, now=now) != AssetStatus.RETIRED
