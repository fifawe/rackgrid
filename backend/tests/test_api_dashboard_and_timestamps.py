"""API-level tests for the post-1.5.0 fixes: timestamps must serialize
with an explicit UTC offset (not naive, which browsers misread as local
time), the Sites directory must feed the Site dropdown's suggestions
even before any asset uses a new site, and the dashboard summary must
include the OS family breakdown and the support-expiry alert."""
from __future__ import annotations

import re
from datetime import date, timedelta

import pytest

from app.infrastructure.config.settings import get_settings

pytestmark = pytest.mark.asyncio

# Matches a trailing UTC offset on an ISO8601 datetime string: "+00:00",
# "Z", or any other explicit "+HH:MM"/"-HH:MM" offset - anything that
# tells the browser this is NOT already local time.
_HAS_TZ_OFFSET = re.compile(r"(Z|[+-]\d{2}:\d{2})$")


def _auth_headers():
    return {"X-Collector-Api-Key": get_settings().collector_api_key}


async def _discover(client, hostname: str, **extra) -> int:
    payload = {"hostname": hostname, **extra}
    resp = await client.post("/api/v1/discovery", json=payload, headers=_auth_headers())
    assert resp.status_code == 200, resp.text
    return resp.json()["asset_id"]


# --------------------------------------------------------------- tz bug --


async def test_asset_timestamps_carry_explicit_utc_offset(authed_client):
    asset_id = await _discover(authed_client, "tz-host-1")
    detail = await authed_client.get(f"/api/v1/assets/{asset_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert _HAS_TZ_OFFSET.search(body["last_seen"]), (
        f"last_seen {body['last_seen']!r} has no UTC offset - a browser will misread it as local time"
    )
    assert _HAS_TZ_OFFSET.search(body["first_seen"])


async def test_run_history_timestamps_carry_explicit_utc_offset(authed_client, uow):
    from datetime import datetime

    from app.domain.entities.collector_run import CollectorRun
    from app.domain.value_objects.enums import TriggerSource

    run = await uow.collector_runs.create(
        CollectorRun(trigger_source=TriggerSource.MANUAL, start_time=datetime.utcnow())
    )
    await uow.commit()

    resp = await authed_client.get("/api/v1/jobs/history")
    assert resp.status_code == 200
    items = resp.json()["items"]
    match = next(i for i in items if i["run_id"] == run.run_id)
    assert _HAS_TZ_OFFSET.search(match["start_time"]), (
        f"start_time {match['start_time']!r} has no UTC offset - Job Management would show it as local"
    )


async def test_audit_history_timestamps_carry_explicit_utc_offset(authed_client):
    asset_id = await _discover(authed_client, "tz-host-2")
    await authed_client.put(f"/api/v1/assets/{asset_id}/business", json={"asset_owner": "erin"})

    resp = await authed_client.get(f"/api/v1/audit/{asset_id}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    assert _HAS_TZ_OFFSET.search(items[0]["change_timestamp"])


# ----------------------------------------------------- site directory ---


async def test_field_options_site_list_includes_unused_site_from_directory(authed_client):
    """A site added on the Sites page must appear as a dropdown suggestion
    immediately - before any asset has ever been assigned to it. Before
    the fix, field-options only looked at asset_business.site values
    actually in use, so a brand-new site was invisible until someone
    manually typed its exact name on an asset first."""
    create = await authed_client.post(
        "/api/v1/sites", json={"name": "Unused Site Alpha", "code": "USA-1", "city": "Nowhere"}
    )
    assert create.status_code == 201, create.text

    options = await authed_client.get("/api/v1/assets/field-options")
    assert options.status_code == 200
    assert "Unused Site Alpha" in options.json()["site"]


# ------------------------------------------------------------- dashboard --


async def test_dashboard_summary_includes_os_family_breakdown(authed_client):
    await _discover(authed_client, "os-host-1", os={"distribution": "Ubuntu", "version": "22.04"})
    await _discover(authed_client, "os-host-2", os={"distribution": "Ubuntu", "version": "24.04"})
    await _discover(authed_client, "os-host-3", os={"distribution": "RHEL", "version": "9.4"})

    resp = await authed_client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    by_os_family = resp.json()["by_os_family"]
    assert by_os_family.get("Ubuntu") == 2
    assert by_os_family.get("RHEL") == 1


async def test_dashboard_summary_flags_support_expiring_within_60_days(authed_client):
    soon = (date.today() + timedelta(days=10)).isoformat()
    far = (date.today() + timedelta(days=400)).isoformat()
    expired = (date.today() - timedelta(days=5)).isoformat()

    expiring_asset = await _discover(authed_client, "expiry-host-soon")
    await authed_client.put(
        f"/api/v1/assets/{expiring_asset}/business", json={"hw_support_expiry": soon}
    )

    expired_asset = await _discover(authed_client, "expiry-host-expired")
    await authed_client.put(
        f"/api/v1/assets/{expired_asset}/business", json={"os_support_expiry": expired}
    )

    safe_asset = await _discover(authed_client, "expiry-host-safe")
    await authed_client.put(f"/api/v1/assets/{safe_asset}/business", json={"hw_support_expiry": far})

    resp = await authed_client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()

    hostnames_flagged = {item["hostname"] for item in body["expiring_support"]}
    assert "expiry-host-soon" in hostnames_flagged
    assert "expiry-host-expired" in hostnames_flagged
    assert "expiry-host-safe" not in hostnames_flagged
    assert body["expiring_support_count"] >= 2

    # soonest-expiring (or already-expired) items sort first
    days = [item["days_remaining"] for item in body["expiring_support"]]
    assert days == sorted(days)
    expired_item = next(i for i in body["expiring_support"] if i["hostname"] == "expiry-host-expired")
    assert expired_item["days_remaining"] < 0


async def test_dashboard_summary_buckets_missing_site_and_environment_as_undefined(authed_client):
    """A host that's never had its Site/Environment set (NULL) and one
    where the field was explicitly cleared via the edit form (saved as
    "") must both land in a single, clearly-labeled "Un Defined" bucket
    on the By Site / By Environment charts - not be silently dropped
    (the old `.is_not(None)` filter) and not show up as a separate,
    unlabeled blank-key bar (the "" case the old filter let through)."""
    never_set = await _discover(authed_client, "undefined-host-never-set")

    cleared_id = await _discover(authed_client, "undefined-host-cleared")
    put = await authed_client.put(
        f"/api/v1/assets/{cleared_id}/business",
        json={"site": "Some Site", "environment": "Production"},
    )
    assert put.status_code == 200, put.text
    put = await authed_client.put(
        f"/api/v1/assets/{cleared_id}/business", json={"site": "", "environment": ""}
    )
    assert put.status_code == 200, put.text

    assigned_id = await _discover(authed_client, "undefined-host-assigned")
    put = await authed_client.put(
        f"/api/v1/assets/{assigned_id}/business",
        json={"site": "HQ", "environment": "Staging"},
    )
    assert put.status_code == 200, put.text

    resp = await authed_client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()

    assert body["by_site"].get("Un Defined", 0) >= 2
    assert body["by_environment"].get("Un Defined", 0) >= 2
    assert body["by_site"].get("HQ") == 1
    assert body["by_environment"].get("Staging") == 1
    # Neither the null-key nor the empty-string-key form should survive
    # separately - both must have been folded into "Un Defined".
    assert None not in body["by_site"]
    assert "" not in body["by_site"]
    assert None not in body["by_environment"]
    assert "" not in body["by_environment"]

    # sanity: the fixture ids above aren't unused
    assert never_set > 0


# --------------------------------------------------- os_distribution filter --


async def test_assets_list_filters_by_os_distribution(authed_client):
    await _discover(authed_client, "osfilter-ubuntu", os={"distribution": "Ubuntu", "version": "22.04"})
    await _discover(authed_client, "osfilter-rhel", os={"distribution": "RHEL", "version": "9.4"})
    await _discover(authed_client, "osfilter-no-os")

    resp = await authed_client.get("/api/v1/assets", params={"os_distribution": "Ubuntu"})
    assert resp.status_code == 200
    hostnames = {item["hostname"] for item in resp.json()["items"]}
    assert hostnames == {"osfilter-ubuntu"}


async def test_assets_list_filters_by_os_distribution_undefined_sentinel(authed_client):
    """The dashboard's OS Family "Unknown" slice links through to
    ?os_distribution=__none__ rather than a literal string, since there's
    no real DB value meaning "no OS recorded". The endpoint must translate
    that sentinel into an IS NULL / empty-string match."""
    await _discover(authed_client, "osfilter-sentinel-ubuntu", os={"distribution": "Ubuntu", "version": "22.04"})
    await _discover(authed_client, "osfilter-sentinel-none")

    resp = await authed_client.get("/api/v1/assets", params={"os_distribution": "__none__"})
    assert resp.status_code == 200
    hostnames = {item["hostname"] for item in resp.json()["items"]}
    assert "osfilter-sentinel-none" in hostnames
    assert "osfilter-sentinel-ubuntu" not in hostnames
