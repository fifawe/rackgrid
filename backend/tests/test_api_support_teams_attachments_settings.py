"""API-level tests for the v1.8 features: the Support Team directory
(CRUD, mirroring Sites) and its use as a strict asset dropdown, asset
design-document attachments (upload/list/download/delete, including
file-type and size rejection), and platform branding settings
(title/logo)."""
from __future__ import annotations

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


# --------------------------------------------------------- support teams --


async def test_support_team_crud_lifecycle(authed_client):
    create = await authed_client.post(
        "/api/v1/support-teams",
        json={
            "name": "Network Ops",
            "contact_number": "+20-100-555-1212",
            "email": "netops@example.com",
            "location": "Cairo DC",
            "notes": "Escalate P1s via PagerDuty",
        },
    )
    assert create.status_code == 201, create.text
    team = create.json()
    assert team["name"] == "Network Ops"
    assert team["email"] == "netops@example.com"
    team_id = team["support_team_id"]

    listed = await authed_client.get("/api/v1/support-teams")
    assert listed.status_code == 200
    assert any(t["support_team_id"] == team_id for t in listed.json())

    updated = await authed_client.put(
        f"/api/v1/support-teams/{team_id}",
        json={"name": "Network Ops", "contact_number": None, "email": "netops@example.com",
              "location": "Riyadh DC", "notes": None},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["location"] == "Riyadh DC"

    deleted = await authed_client.delete(f"/api/v1/support-teams/{team_id}")
    assert deleted.status_code == 204

    listed_after = await authed_client.get("/api/v1/support-teams")
    assert not any(t["support_team_id"] == team_id for t in listed_after.json())


async def test_support_team_name_must_be_unique(authed_client):
    first = await authed_client.post("/api/v1/support-teams", json={"name": "Storage Team"})
    assert first.status_code == 201

    dupe = await authed_client.post("/api/v1/support-teams", json={"name": "Storage Team"})
    assert dupe.status_code == 400


async def test_asset_can_be_assigned_a_support_team_from_the_directory(authed_client):
    await authed_client.post("/api/v1/support-teams", json={"name": "DBA Team"})
    asset_id = await _discover(authed_client, "supportteam-host-1")

    updated = await authed_client.put(
        f"/api/v1/assets/{asset_id}/business", json={"support_team": "DBA Team"}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["support_team"] == "DBA Team"


# ------------------------------------------------------------ attachments --


async def test_attachment_upload_list_download_delete_lifecycle(authed_client):
    asset_id = await _discover(authed_client, "attachment-host-1")

    upload = await authed_client.post(
        f"/api/v1/assets/{asset_id}/attachments",
        files={"file": ("rack-diagram.pdf", b"%PDF-1.4 fake pdf bytes", "application/pdf")},
    )
    assert upload.status_code == 201, upload.text
    attachment = upload.json()
    assert attachment["original_filename"] == "rack-diagram.pdf"
    assert attachment["file_size"] == len(b"%PDF-1.4 fake pdf bytes")
    attachment_id = attachment["attachment_id"]

    listed = await authed_client.get(f"/api/v1/assets/{asset_id}/attachments")
    assert listed.status_code == 200
    assert any(a["attachment_id"] == attachment_id for a in listed.json())

    download = await authed_client.get(f"/api/v1/assets/{asset_id}/attachments/{attachment_id}/download")
    assert download.status_code == 200
    assert download.content == b"%PDF-1.4 fake pdf bytes"
    assert "rack-diagram.pdf" in download.headers["content-disposition"]

    deleted = await authed_client.delete(f"/api/v1/assets/{asset_id}/attachments/{attachment_id}")
    assert deleted.status_code == 204

    listed_after = await authed_client.get(f"/api/v1/assets/{asset_id}/attachments")
    assert not any(a["attachment_id"] == attachment_id for a in listed_after.json())


async def test_attachment_upload_supports_multiple_files_per_asset(authed_client):
    asset_id = await _discover(authed_client, "attachment-host-multi")

    first = await authed_client.post(
        f"/api/v1/assets/{asset_id}/attachments",
        files={"file": ("spec.xlsx", b"fake xlsx bytes", "application/vnd.ms-excel")},
    )
    second = await authed_client.post(
        f"/api/v1/assets/{asset_id}/attachments",
        files={"file": ("photo.png", b"fake png bytes", "image/png")},
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listed = await authed_client.get(f"/api/v1/assets/{asset_id}/attachments")
    assert len(listed.json()) == 2


async def test_attachment_upload_rejects_disallowed_file_type(authed_client):
    asset_id = await _discover(authed_client, "attachment-host-badtype")

    upload = await authed_client.post(
        f"/api/v1/assets/{asset_id}/attachments",
        files={"file": ("script.exe", b"MZ fake exe bytes", "application/octet-stream")},
    )
    assert upload.status_code == 400

    listed = await authed_client.get(f"/api/v1/assets/{asset_id}/attachments")
    assert listed.json() == []


async def test_attachment_upload_rejects_oversized_file(authed_client, monkeypatch):
    from app.infrastructure.config import settings as settings_module

    asset_id = await _discover(authed_client, "attachment-host-oversize")

    settings_module.get_settings.cache_clear()
    monkeypatch.setenv("MAX_ATTACHMENT_SIZE_BYTES", "10")
    settings_module.get_settings.cache_clear()
    try:
        upload = await authed_client.post(
            f"/api/v1/assets/{asset_id}/attachments",
            files={"file": ("bigger-than-limit.pdf", b"0123456789ABCDEF", "application/pdf")},
        )
        assert upload.status_code == 400
    finally:
        settings_module.get_settings.cache_clear()


# ---------------------------------------------------------------- settings --


async def test_public_settings_default_title_and_no_logo(app_client):
    resp = await app_client.get("/api/v1/settings/public")
    assert resp.status_code == 200
    body = resp.json()
    assert body["platform_title"] == "Asset Inventory Platform"
    assert body["logo_url"] is None
    assert body["version"]


async def test_admin_can_update_platform_title(authed_client):
    updated = await authed_client.put("/api/v1/settings/title", json={"platform_title": "Acme Assets"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["platform_title"] == "Acme Assets"

    public = await authed_client.get("/api/v1/settings/public")
    assert public.json()["platform_title"] == "Acme Assets"


async def test_admin_can_upload_and_replace_logo(authed_client):
    upload = await authed_client.post(
        "/api/v1/settings/logo",
        files={"file": ("logo.png", b"fake png bytes", "image/png")},
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["logo_url"] == "/api/v1/settings/logo"

    fetched = await authed_client.get("/api/v1/settings/logo")
    assert fetched.status_code == 200
    assert fetched.content == b"fake png bytes"

    # Uploading a second logo replaces the first rather than stacking.
    replace = await authed_client.post(
        "/api/v1/settings/logo",
        files={"file": ("logo2.png", b"a different png", "image/png")},
    )
    assert replace.status_code == 200
    fetched_again = await authed_client.get("/api/v1/settings/logo")
    assert fetched_again.content == b"a different png"
