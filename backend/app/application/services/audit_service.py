"""Audit Engine.

Compares the current persisted state of an asset against a freshly
discovered payload and produces AuditRecord entries for changed fields
only. Snapshots are never stored - see PROJECT_SPEC.md > Audit Engine.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.domain.entities.audit_record import AuditRecord
from app.domain.value_objects.enums import COLLECTOR_OWNED_FIELDS


def _stringify(value) -> Optional[str]:
    """Normalize a value to a comparable/storable string.

    Numeric values are normalized so that e.g. the int 16 (as parsed from
    a JSON payload) and the float 16.0 (as round-tripped through a
    Float DB column) compare equal and never produce a spurious audit
    entry for a value that didn't actually change.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        as_float = float(value)
        if as_float.is_integer():
            return str(int(as_float))
        return str(as_float)
    return str(value)


class AuditService:
    def diff_fields(
        self,
        *,
        asset_id: int,
        collector_run_id: Optional[int],
        old_values: Dict[str, object],
        new_values: Dict[str, object],
        source: str = "discovery",
        now: Optional[datetime] = None,
    ) -> List[AuditRecord]:
        """Compare old vs new collector-owned field values and return only
        the fields that actually changed, as AuditRecord instances.

        Fields outside COLLECTOR_OWNED_FIELDS are ignored defensively -
        discovery must never be able to audit/overwrite business metadata.
        """
        now = now or datetime.utcnow()
        records: List[AuditRecord] = []

        for field_name, new_value in new_values.items():
            if field_name not in COLLECTOR_OWNED_FIELDS:
                continue
            old_value = old_values.get(field_name)
            if _stringify(old_value) == _stringify(new_value):
                continue
            if old_value is None and new_value is None:
                continue
            records.append(
                AuditRecord(
                    asset_id=asset_id,
                    collector_run_id=collector_run_id,
                    field_name=field_name,
                    old_value=_stringify(old_value),
                    new_value=_stringify(new_value),
                    source=source,
                    change_timestamp=now,
                )
            )
        return records
