"""Import/Export endpoints for the current inventory.

Export bundles the full inventory CSV (same schema as
`GET /assets/export.csv`) together with the complete audit log into a
single ZIP, so a downloaded snapshot is self-contained. Import re-loads
inventory data from a CSV built to that same schema - see
InventoryImportService for the full set of design decisions around
create-vs-update matching, which fields may be overwritten, and the
blank-cell-means-unchanged convention.
"""
from __future__ import annotations

import csv
import io
import zipfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.data_transfer import ImportResultOut
from app.api.v1.routes.assets import _CSV_COLUMNS, _effective_status, _full_export_row
from app.application.services.inventory_import_service import InventoryImportService
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/data", tags=["import-export"])

_AUDIT_LOG_COLUMNS = ["Timestamp", "Hostname", "Field", "Old Value", "New Value", "Source"]


@router.get("/export")
async def export_inventory_bundle(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    """A ZIP containing inventory.csv (full inventory detail, every
    asset) and audit_log.csv (the complete field-change history)."""
    assets, _ = await uow.assets.list(offset=0, limit=100000)

    inventory_buffer = io.StringIO()
    writer = csv.writer(inventory_buffer)
    writer.writerow(_CSV_COLUMNS)
    hostname_by_id: dict[int, str] = {}
    for asset in assets:
        business = await uow.business_metadata.get_by_asset_id(asset.asset_id)
        writer.writerow(_full_export_row(asset, business))
        hostname_by_id[asset.asset_id] = asset.hostname

    audit_records, _ = await uow.audit.list(offset=0, limit=1_000_000)
    audit_buffer = io.StringIO()
    audit_writer = csv.writer(audit_buffer)
    audit_writer.writerow(_AUDIT_LOG_COLUMNS)
    for record in audit_records:
        audit_writer.writerow(
            [
                record.change_timestamp,
                hostname_by_id.get(record.asset_id, f"asset #{record.asset_id}"),
                record.field_name,
                record.old_value,
                record.new_value,
                record.source,
            ]
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("inventory.csv", inventory_buffer.getvalue())
        archive.writestr("audit_log.csv", audit_buffer.getvalue())
    zip_buffer.seek(0)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"asset_inventory_export_{timestamp}.zip"
    return StreamingResponse(
        iter([zip_buffer.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", response_model=ImportResultOut)
async def import_inventory(
    file: UploadFile,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    """Create-or-update the inventory from a CSV built to the same
    column schema `GET /assets/export.csv` writes. See
    InventoryImportService for the full behavior."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A .csv file is required")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    service = InventoryImportService(uow)
    result = await service.import_csv(content)
    return ImportResultOut(
        created=result.created,
        updated=result.updated,
        errors=[{"row": e.row, "message": e.message} for e in result.errors],
    )
