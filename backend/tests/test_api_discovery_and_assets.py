"""API-level tests exercising the discovery ingestion endpoint and the
assets/dashboard/audit read endpoints together, through the FastAPI app
(auth, schemas, routing all included)."""
from __future__ import annotations

import pytest

from app.infrastructure.config.settings import get_settings

pytestmark = pytest.mark.asyncio


def _auth_headers():
    return {"X-Collector-Api-Key": get_settings().collector_api_key}


@pytest.fixture
async def authed_client(app_client, session):
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="admin",
            hashed_password=BcryptPasswordHasher().hash("ChangeMe123!"),
            role="Admin",
            is_active=True,
        )
    )
    await session.commit()

    resp = await app_client.post("/api/v1/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    app_client.headers["Authorization"] = f"Bearer {token}"
    return app_client


async def test_login_rejects_bad_password(app_client, session):
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="admin",
            hashed_password=BcryptPasswordHasher().hash("correct-password"),
            role="Admin",
            is_active=True,
        )
    )
    await session.commit()

    resp = await app_client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


async def test_discovery_requires_collector_api_key(app_client):
    resp = await app_client.post("/api/v1/discovery", json={"hostname": "server01"})
    assert resp.status_code == 401


async def test_discovery_then_list_assets(authed_client):
    payload = {
        "hostname": "server01",
        "serial_number": "SN-001",
        "primary_ip": "10.0.0.5",
        "hardware": {"ram_gb": 16, "cpu_cores": 8},
        "os": {"distribution": "RHEL", "version": "9.4"},
        "storage": [{"device_name": "/dev/sda1", "filesystem_type": "xfs", "mount_point": "/", "capacity_gb": 100}],
        "network": [{"interface_name": "eth0", "ip_address": "10.0.0.5", "mac_address": "00:11:22:33:44:55"}],
    }
    resp = await authed_client.post("/api/v1/discovery", json=payload, headers=_auth_headers())
    assert resp.status_code == 200, resp.text
    asset_id = resp.json()["asset_id"]

    listed = await authed_client.get("/api/v1/assets")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["hostname"] == "server01"

    detail = await authed_client.get(f"/api/v1/assets/{asset_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["storage"][0]["mount_point"] == "/"
    assert body["network"][0]["mac_address"] == "00:11:22:33:44:55"


async def test_business_metadata_update_requires_editor_or_above(authed_client):
    discover = await authed_client.post(
        "/api/v1/discovery", json={"hostname": "server02"}, headers=_auth_headers()
    )
    asset_id = discover.json()["asset_id"]

    resp = await authed_client.put(
        f"/api/v1/assets/{asset_id}/business",
        json={"asset_owner": "alice", "environment": "Production", "technology": "Database"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["asset_owner"] == "alice"
    assert resp.json()["technology"] == "Database"


async def test_dashboard_summary_reflects_discovered_assets(authed_client):
    await authed_client.post("/api/v1/discovery", json={"hostname": "server03"}, headers=_auth_headers())
    resp = await authed_client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_assets"] == 1
    assert body["active_assets"] == 1


async def test_discovery_multiple_hosts_same_run_each_create_own_asset(authed_client, uow, session):
    """Regression test for the "only the last host survives a cron run"
    bug: every host submitted against the same collector_run_id must end
    up as its own asset, and the run's success_count must reflect every
    host, not just whichever one wrote last (see CollectorRunRepository.
    increment_success/increment_failure - the old code loaded, mutated,
    and saved the whole run row per host, which raced when hosts in the
    same run submit close together)."""
    from datetime import datetime

    from app.domain.entities.collector_run import CollectorRun
    from app.domain.value_objects.enums import TriggerSource

    run = await uow.collector_runs.create(
        CollectorRun(trigger_source=TriggerSource.INTERNAL_SCHEDULER, start_time=datetime.utcnow())
    )
    await uow.commit()

    hostnames = ["k8s-worker-1", "k8s-worker-2", "k8s-worker-3"]
    for hostname in hostnames:
        resp = await authed_client.post(
            "/api/v1/discovery",
            json={"hostname": hostname, "collector_run_id": run.run_id},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200, resp.text

    listed = await authed_client.get("/api/v1/assets")
    assert listed.status_code == 200
    assert listed.json()["total"] == len(hostnames)
    assert {item["hostname"] for item in listed.json()["items"]} == set(hostnames)

    refreshed_run = await uow.collector_runs.get_by_id(run.run_id)
    assert refreshed_run.success_count == len(hostnames)
    assert refreshed_run.failure_count == 0
    assert refreshed_run.assets_processed == len(hostnames)


async def test_discovery_hosts_sharing_placeholder_serial_stay_separate_assets(authed_client):
    """Regression test for the real-world root cause of "only the last
    host collected": unconfigured KVM/QEMU/Proxmox VMs commonly all
    report the identical BIOS placeholder serial "Not Specified". Before
    the fix, AssetMatchingService treated that as a real, authoritative
    serial number, so every host reporting it collided into one asset
    record that each subsequent host's discovery silently overwrote."""
    hostnames = ["k8s-master-2", "k8s-worker-1", "k8s-worker-3", "docker1", "cs7"]
    for i, hostname in enumerate(hostnames):
        resp = await authed_client.post(
            "/api/v1/discovery",
            json={
                "hostname": hostname,
                "serial_number": "Not Specified",
                "primary_ip": f"192.168.100.{i}",
            },
            headers=_auth_headers(),
        )
        assert resp.status_code == 200, resp.text

    listed = await authed_client.get("/api/v1/assets")
    assert listed.status_code == 200
    assert listed.json()["total"] == len(hostnames), (
        "every host must get its own asset even though they share a placeholder serial number"
    )
    assert {item["hostname"] for item in listed.json()["items"]} == set(hostnames)


async def test_viewer_cannot_write_business_metadata(app_client, session):
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="viewer1",
            hashed_password=BcryptPasswordHasher().hash("password123"),
            role="Viewer",
            is_active=True,
        )
    )
    await session.commit()

    login = await app_client.post("/api/v1/auth/login", json={"username": "viewer1", "password": "password123"})
    app_client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"

    discover = await app_client.post(
        "/api/v1/discovery", json={"hostname": "server04"}, headers=_auth_headers()
    )
    asset_id = discover.json()["asset_id"]

    resp = await app_client.put(f"/api/v1/assets/{asset_id}/business", json={"asset_owner": "bob"})
    assert resp.status_code == 403
