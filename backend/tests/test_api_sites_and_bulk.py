"""API-level tests for the v1.5 dashboard-enhancement features: Sites
reference data CRUD, the dropdown-with-add-new field-options endpoint,
rack_number end-to-end, bulk business-metadata edit, and the expanded
CSV export."""
from __future__ import annotations

import csv
import io

import pytest

from app.infrastructure.config.settings import get_settings

pytestmark = pytest.mark.asyncio


def _auth_headers():
    return {"X-Collector-Api-Key": get_settings().collector_api_key}


async def _discover(client, hostname: str, **extra) -> int:
    payload = {"hostname": hostname, **extra}
    resp = await client.post("/api/v1/discovery", json=payload, headers=_auth_headers())
    assert resp.status_code == 200, resp.text
    return resp.json()["asset_id"]


# ---------------------------------------------------------------- Sites --


async def test_site_crud_lifecycle(authed_client):
    create = await authed_client.post("/api/v1/sites", json={"name": "HQ", "code": "HQ1", "city": "Cairo"})
    assert create.status_code == 201, create.text
    site = create.json()
    assert site["name"] == "HQ"
    assert site["city"] == "Cairo"
    site_id = site["site_id"]

    listed = await authed_client.get("/api/v1/sites")
    assert listed.status_code == 200
    assert any(s["site_id"] == site_id for s in listed.json())

    updated = await authed_client.put(
        f"/api/v1/sites/{site_id}", json={"name": "HQ", "code": "HQ1", "city": "Giza"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["city"] == "Giza"

    deleted = await authed_client.delete(f"/api/v1/sites/{site_id}")
    assert deleted.status_code == 204

    listed_after = await authed_client.get("/api/v1/sites")
    assert all(s["site_id"] != site_id for s in listed_after.json())


async def test_site_name_must_be_unique(authed_client):
    first = await authed_client.post("/api/v1/sites", json={"name": "Dallas DC"})
    assert first.status_code == 201

    dup = await authed_client.post("/api/v1/sites", json={"name": "Dallas DC"})
    assert dup.status_code == 400


async def test_site_write_requires_editor_or_above(app_client, session):
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="viewer2",
            hashed_password=BcryptPasswordHasher().hash("password123"),
            role="Viewer",
            is_active=True,
        )
    )
    await session.commit()

    login = await app_client.post("/api/v1/auth/login", json={"username": "viewer2", "password": "password123"})
    app_client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    resp = await app_client.post("/api/v1/sites", json={"name": "Blocked Site"})
    assert resp.status_code == 403


# --------------------------------------------------------- field-options --


async def test_field_options_reflects_saved_values_and_includes_technology_defaults(authed_client):
    asset_id = await _discover(authed_client, "opt-host-1")
    resp = await authed_client.put(
        f"/api/v1/assets/{asset_id}/business",
        json={"support_team": "Platform Eng", "asset_owner": "carol", "site": "Dallas DC", "environment": "Staging"},
    )
    assert resp.status_code == 200, resp.text

    options = await authed_client.get("/api/v1/assets/field-options")
    assert options.status_code == 200
    body = options.json()
    assert "Platform Eng" in body["support_team"]
    assert "carol" in body["asset_owner"]
    assert "Dallas DC" in body["site"]
    assert "Staging" in body["environment"]
    # built-in Technology enum values are always offered as suggestions
    assert "Database" in body["technology"]


async def test_field_options_supports_a_brand_new_technology_value(authed_client):
    asset_id = await _discover(authed_client, "opt-host-2")
    resp = await authed_client.put(
        f"/api/v1/assets/{asset_id}/business",
        json={"technology": "Quantum Widget Farm"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["technology"] == "Quantum Widget Farm"

    options = await authed_client.get("/api/v1/assets/field-options")
    assert "Quantum Widget Farm" in options.json()["technology"]


# ------------------------------------------------------------ rack_number --


async def test_rack_number_round_trips_through_business_metadata(authed_client):
    asset_id = await _discover(authed_client, "rack-host-1")
    resp = await authed_client.put(
        f"/api/v1/assets/{asset_id}/business",
        json={"rack_number": "R-42-U18"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["rack_number"] == "R-42-U18"

    detail = await authed_client.get(f"/api/v1/assets/{asset_id}")
    assert detail.json()["business"]["rack_number"] == "R-42-U18"


# ------------------------------------------------------------------ bulk --


async def test_bulk_update_applies_fields_to_every_listed_asset(authed_client):
    ids = [await _discover(authed_client, f"bulk-host-{i}") for i in range(3)]

    resp = await authed_client.put(
        "/api/v1/assets/bulk-business",
        json={"asset_ids": ids, "support_team": "NOC", "environment": "Production"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["updated"] == 3
    assert set(body["asset_ids"]) == set(ids)

    for asset_id in ids:
        detail = await authed_client.get(f"/api/v1/assets/{asset_id}")
        business = detail.json()["business"]
        assert business["support_team"] == "NOC"
        assert business["environment"] == "Production"


async def test_bulk_update_rejects_empty_asset_id_list(authed_client):
    resp = await authed_client.put(
        "/api/v1/assets/bulk-business", json={"asset_ids": [], "support_team": "NOC"}
    )
    assert resp.status_code == 400


async def test_bulk_update_404s_on_unknown_asset_and_rolls_back(authed_client):
    ids = [await _discover(authed_client, "bulk-host-known")]
    resp = await authed_client.put(
        "/api/v1/assets/bulk-business",
        json={"asset_ids": ids + [999999], "support_team": "Should Not Stick"},
    )
    assert resp.status_code == 404

    detail = await authed_client.get(f"/api/v1/assets/{ids[0]}")
    business = detail.json().get("business")
    # the whole batch rolled back, so the first (valid) asset must not have
    # been partially updated either
    assert business is None or business.get("support_team") != "Should Not Stick"


async def test_bulk_update_requires_editor_or_above(app_client, session):
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="viewer3",
            hashed_password=BcryptPasswordHasher().hash("password123"),
            role="Viewer",
            is_active=True,
        )
    )
    await session.commit()

    login = await app_client.post("/api/v1/auth/login", json={"username": "viewer3", "password": "password123"})
    app_client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    resp = await app_client.put("/api/v1/assets/bulk-business", json={"asset_ids": [1], "support_team": "NOC"})
    assert resp.status_code == 403


# ------------------------------------------------------------- CSV export --


async def test_csv_export_includes_full_inventory_detail(authed_client):
    asset_id = await _discover(
        authed_client,
        "csv-host-1",
        serial_number="SN-CSV-1",
        primary_ip="10.9.9.9",
        hardware={"manufacturer": "Dell", "model": "R740", "ram_gb": 64},
        os={"distribution": "Ubuntu", "version": "22.04"},
    )
    await authed_client.put(
        f"/api/v1/assets/{asset_id}/business",
        json={
            "support_team": "Platform Eng",
            "asset_owner": "dave",
            "site": "Dallas DC",
            "rack_number": "R-12",
            "technology": "Database",
            "environment": "Production",
        },
    )

    resp = await authed_client.get("/api/v1/assets/export.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    rows = list(csv.reader(io.StringIO(resp.text)))
    header, data_rows = rows[0], rows[1:]

    for column in [
        "Hostname",
        "Serial Number",
        "Manufacturer",
        "Model",
        "RAM (GB)",
        "OS Distribution",
        "Support Team",
        "Asset Owner",
        "Site",
        "Rack Number",
        "Technology",
        "Environment",
    ]:
        assert column in header, f"missing column: {column}"

    by_hostname = {row[header.index("Hostname")]: row for row in data_rows}
    row = by_hostname["csv-host-1"]
    assert row[header.index("Serial Number")] == "SN-CSV-1"
    assert row[header.index("Manufacturer")] == "Dell"
    assert row[header.index("RAM (GB)")] == "64.0" or row[header.index("RAM (GB)")] == "64"
    assert row[header.index("Support Team")] == "Platform Eng"
    assert row[header.index("Rack Number")] == "R-12"
    assert row[header.index("Technology")] == "Database"
