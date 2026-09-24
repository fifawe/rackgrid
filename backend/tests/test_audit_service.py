"""Unit tests for AuditService - change-only diffing, per PROJECT_SPEC.md
> Audit Engine (only changed fields are recorded, never full snapshots)."""
from __future__ import annotations

from app.application.services.audit_service import AuditService


def test_no_records_when_nothing_changed():
    service = AuditService()
    old = {"ram_gb": 16, "os_version": "8.8"}
    new = {"ram_gb": 16, "os_version": "8.8"}
    records = service.diff_fields(asset_id=1, collector_run_id=1, old_values=old, new_values=new)
    assert records == []


def test_only_changed_fields_are_recorded():
    service = AuditService()
    old = {"ram_gb": 16, "os_version": "8.8", "hostname": "server01"}
    new = {"ram_gb": 32, "os_version": "8.10", "hostname": "server01"}
    records = service.diff_fields(asset_id=1, collector_run_id=1, old_values=old, new_values=new)

    changed_fields = {r.field_name for r in records}
    assert changed_fields == {"ram_gb", "os_version"}
    assert "hostname" not in changed_fields


def test_ignores_fields_outside_collector_owned_set():
    service = AuditService()
    # asset_owner is business-owned; even if it somehow ended up in the
    # diff inputs, the audit engine must never touch it.
    old = {"ram_gb": 16, "asset_owner": "alice"}
    new = {"ram_gb": 16, "asset_owner": "bob"}
    records = service.diff_fields(asset_id=1, collector_run_id=1, old_values=old, new_values=new)
    assert records == []


def test_new_asset_records_every_populated_field_as_a_change():
    service = AuditService()
    old = {"ram_gb": None, "hostname": None}
    new = {"ram_gb": 64, "hostname": "server02"}
    records = service.diff_fields(asset_id=2, collector_run_id=1, old_values=old, new_values=new)
    assert len(records) == 2
    assert all(r.old_value is None for r in records)
