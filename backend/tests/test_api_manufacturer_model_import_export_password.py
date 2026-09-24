"""API-level tests for the v1.9 features: Manufacturer/Model dashboard
buckets + inventory filters + hardware-options, the Import/Export bundle
(including the create-on-no-match / overwrite-hardware-fields /
blank-means-unchanged semantics confirmed with the user), and
self-service change-password."""
from __future__ import annotations

import csv
import io
import zipfile

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


# --------------------------------------------------------- manufacturer/model --


async def test_hardware_options_and_dashboard_by_manufacturer_and_model(authed_client):
    await _discover(authed_client, "hw-host-1", hardware={"manufacturer": "Dell", "model": "PowerEdge R750"})
    await _discover(authed_client, "hw-host-2", hardware={"manufacturer": "Dell", "model": "PowerEdge R750"})
    await _discover(authed_client, "hw-host-3", hardware={"manufacturer": "HPE", "model": "ProLiant DL380"})
    await _discover(authed_client, "hw-host-4")  # no hardware info at all -> Unknown bucket

    options = await authed_client.get("/api/v1/assets/hardware-options")
    assert options.status_code == 200
    body = options.json()
    assert "Dell" in body["manufacturer"]
    assert "HPE" in body["manufacturer"]
    assert "PowerEdge R750" in body["model"]
    assert "ProLiant DL380" in body["model"]

    summary = await authed_client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    data = summary.json()
    assert data["by_manufacturer"]["Dell"] == 2
    assert data["by_manufacturer"]["HPE"] == 1
    assert data["by_manufacturer"]["Unknown"] == 1
    assert data["by_model"]["PowerEdge R750"] == 2
    assert data["by_model"]["ProLiant DL380"] == 1
    assert data["by_model"]["Unknown"] == 1


async def test_dashboard_model_bucket_collapses_long_tail_into_other(authed_client):
    # 9 distinct single-count models plus a 10th and 11th push past top_n=9.
    for i in range(11):
        await _discover(authed_client, f"model-host-{i}", hardware={"manufacturer": "Acme", "model": f"Model-{i}"})

    summary = await authed_client.get("/api/v1/dashboard/summary")
    by_model = summary.json()["by_model"]
    assert "Other" in by_model
    assert sum(by_model.values()) == 11
    assert len(by_model) <= 10  # top 9 + "Other" (no Unknown here)


async def test_inventory_list_filters_by_manufacturer_and_model(authed_client):
    await _discover(authed_client, "filter-host-1", hardware={"manufacturer": "Cisco", "model": "UCS C220"})
    await _discover(authed_client, "filter-host-2", hardware={"manufacturer": "Lenovo", "model": "SR650"})

    by_manufacturer = await authed_client.get("/api/v1/assets", params={"manufacturer": "Cisco"})
    assert by_manufacturer.status_code == 200
    items = by_manufacturer.json()["items"]
    assert len(items) == 1
    assert items[0]["hostname"] == "filter-host-1"

    by_model = await authed_client.get("/api/v1/assets", params={"model": "SR650"})
    items = by_model.json()["items"]
    assert len(items) == 1
    assert items[0]["hostname"] == "filter-host-2"


# ------------------------------------------------------------ import/export --


async def test_export_bundle_contains_inventory_and_audit_log_csv(authed_client):
    await _discover(authed_client, "export-host-1", hardware={"manufacturer": "Dell", "model": "R750"})

    resp = await authed_client.get("/api/v1/data/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    archive = zipfile.ZipFile(io.BytesIO(resp.content))
    names = archive.namelist()
    assert "inventory.csv" in names
    assert "audit_log.csv" in names

    inventory_rows = list(csv.reader(io.StringIO(archive.read("inventory.csv").decode())))
    assert inventory_rows[0][0] == "Hostname"
    assert any(row[0] == "export-host-1" for row in inventory_rows[1:])

    audit_rows = list(csv.reader(io.StringIO(archive.read("audit_log.csv").decode())))
    assert audit_rows[0] == ["Timestamp", "Hostname", "Field", "Old Value", "New Value", "Source"]
    assert any(row[1] == "export-host-1" and row[5] == "discovery" for row in audit_rows[1:])


_IMPORT_HEADER = [
    "Hostname", "Serial Number", "Primary IP", "Status", "Virtual/Physical", "Hypervisor",
    "Manufacturer", "Model", "CPU Model", "CPU Count", "CPU Cores", "CPU Threads", "RAM (GB)",
    "OS Distribution", "OS Version", "Kernel Version", "Architecture", "Uptime (s)",
    "Support Team", "Asset Owner", "Application Name", "Business Service", "Environment",
    "Site", "Rack Number", "Technology", "HW Support Expiry", "OS Support Expiry",
    "First Seen", "Last Seen", "Last Collection",
]


def _csv_bytes(header: list, rows: list) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode()


def _import_row(hostname, **overrides) -> list:
    row = {col: "" for col in _IMPORT_HEADER}
    row["Hostname"] = hostname
    row.update(overrides)
    return [row[col] for col in _IMPORT_HEADER]


async def test_import_creates_new_asset_when_no_match(authed_client):
    csv_bytes = _csv_bytes(_IMPORT_HEADER, [
        _import_row("import-new-host", Manufacturer="Dell", Model="R750", Technology="Database"),
    ])

    resp = await authed_client.post(
        "/api/v1/data/import", files={"file": ("inventory.csv", csv_bytes, "text/csv")}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] == 1
    assert body["updated"] == 0
    assert body["errors"] == []

    listed = await authed_client.get("/api/v1/assets", params={"search": "import-new-host"})
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["technology"] == "Database"


async def test_import_updates_matched_asset_and_leaves_blank_fields_unchanged(authed_client):
    asset_id = await _discover(
        authed_client, "import-existing-host",
        hardware={"manufacturer": "Dell", "model": "R750", "ram_gb": 64},
    )
    await authed_client.put(f"/api/v1/assets/{asset_id}/business", json={"asset_owner": "Jane Doe"})

    csv_bytes = _csv_bytes(_IMPORT_HEADER, [
        _import_row("import-existing-host", Model="R760"),  # only Model provided
    ])
    resp = await authed_client.post(
        "/api/v1/data/import", files={"file": ("inventory.csv", csv_bytes, "text/csv")}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["updated"] == 1
    assert body["created"] == 0

    detail = await authed_client.get(f"/api/v1/assets/{asset_id}")
    data = detail.json()
    assert data["model"] == "R760"           # overwritten by the non-blank cell
    assert data["manufacturer"] == "Dell"    # left unchanged (blank cell)
    assert data["ram_gb"] == 64              # left unchanged (blank cell)
    assert data["business"]["asset_owner"] == "Jane Doe"  # left unchanged

    audit = await authed_client.get(f"/api/v1/audit/{asset_id}", params={"field_name": "model"})
    audit_items = audit.json()["items"]
    assert any(a["new_value"] == "R760" and a["source"] == "import" for a in audit_items)


async def test_import_reports_row_errors_without_aborting_other_rows(authed_client):
    csv_bytes = _csv_bytes(_IMPORT_HEADER, [
        _import_row("import-good-host"),
        _import_row("import-bad-host", **{"CPU Count": "not-a-number"}),
        _import_row("", **{"Serial Number": "should-fail-no-hostname"}),
    ])
    resp = await authed_client.post(
        "/api/v1/data/import", files={"file": ("inventory.csv", csv_bytes, "text/csv")}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["created"] == 1
    assert len(body["errors"]) == 2
    messages = " ".join(e["message"] for e in body["errors"])
    assert "CPU Count" in messages
    assert "Hostname" in messages


async def test_import_requires_editor_role(app_client, session):
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="viewer-only",
            hashed_password=BcryptPasswordHasher().hash("pw12345"),
            role="Viewer",
            is_active=True,
        )
    )
    await session.commit()
    login = await app_client.post("/api/v1/auth/login", json={"username": "viewer-only", "password": "pw12345"})
    assert login.status_code == 200
    app_client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    csv_bytes = _csv_bytes(_IMPORT_HEADER, [_import_row("blocked-host")])
    resp = await app_client.post(
        "/api/v1/data/import", files={"file": ("inventory.csv", csv_bytes, "text/csv")}
    )
    assert resp.status_code == 403


# --------------------------------------------------------------- password --


async def test_change_password_success_and_relogin(authed_client):
    resp = await authed_client.put(
        "/api/v1/auth/change-password",
        json={"current_password": "ChangeMe123!", "new_password": "NewPassword456!"},
    )
    assert resp.status_code == 204

    del authed_client.headers["Authorization"]
    old_login = await authed_client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "ChangeMe123!"}
    )
    assert old_login.status_code == 401

    new_login = await authed_client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "NewPassword456!"}
    )
    assert new_login.status_code == 200


async def test_change_password_rejects_wrong_current_password(authed_client):
    resp = await authed_client.put(
        "/api/v1/auth/change-password",
        json={"current_password": "totally-wrong", "new_password": "NewPassword456!"},
    )
    assert resp.status_code == 400


async def test_change_password_rejects_too_short_new_password(authed_client):
    resp = await authed_client.put(
        "/api/v1/auth/change-password",
        json={"current_password": "ChangeMe123!", "new_password": "short"},
    )
    assert resp.status_code == 422
