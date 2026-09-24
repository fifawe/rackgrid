"""Design-document attachment endpoints for a specific asset - upload,
list, download, delete. An asset can hold any number of attachments
(diagrams, spec sheets, vendor quotes, etc.); file type is restricted to
common design-doc formats and each upload is capped in size (see
Settings.max_attachment_size_bytes)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.attachment import AttachmentOut
from app.domain.entities.asset_attachment import AssetAttachment
from app.domain.value_objects.enums import UserRole
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.storage import local_file_storage

router = APIRouter(prefix="/assets", tags=["attachments"])

# Documents & images only - matches what the Asset Details page's
# Attachments tab advertises as accepted.
_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"}


async def _require_asset(asset_id: int, uow: SqlAlchemyUnitOfWork):
    asset = await uow.assets.get_by_id(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/{asset_id}/attachments", response_model=List[AttachmentOut])
async def list_attachments(
    asset_id: int,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    await _require_asset(asset_id, uow)
    items = await uow.attachments.list_for_asset(asset_id)
    return [AttachmentOut.model_validate(a, from_attributes=True) for a in items]


@router.post("/{asset_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    asset_id: int,
    file: UploadFile,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    user=Depends(require_role(UserRole.EDITOR)),
):
    await _require_asset(asset_id, uow)

    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    extension = Path(file.filename).suffix.lower()
    if extension not in _ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(_ALLOWED_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"File type not allowed - accepted types: {allowed}")

    content = await file.read()
    max_size = get_settings().max_attachment_size_bytes
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File is too large - max {max_size // (1024 * 1024)} MB",
        )

    stored_filename = local_file_storage.save_file(
        local_file_storage.ATTACHMENTS_SUBDIR, file.filename, content
    )
    saved = await uow.attachments.create(
        AssetAttachment(
            asset_id=asset_id,
            original_filename=file.filename,
            stored_filename=stored_filename,
            content_type=file.content_type,
            file_size=len(content),
            uploaded_by=user.username,
            uploaded_at=datetime.now(timezone.utc),
        )
    )
    await uow.commit()
    return AttachmentOut.model_validate(saved, from_attributes=True)


@router.get("/{asset_id}/attachments/{attachment_id}/download")
async def download_attachment(
    asset_id: int,
    attachment_id: int,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    attachment = await uow.attachments.get_by_id(attachment_id)
    if attachment is None or attachment.asset_id != asset_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    try:
        content = local_file_storage.read_file(
            local_file_storage.ATTACHMENTS_SUBDIR, attachment.stored_filename
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Attachment file is missing from storage")
    return Response(
        content=content,
        media_type=attachment.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment.original_filename}"'},
    )


@router.delete("/{asset_id}/attachments/{attachment_id}", status_code=204)
async def delete_attachment(
    asset_id: int,
    attachment_id: int,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    attachment = await uow.attachments.get_by_id(attachment_id)
    if attachment is None or attachment.asset_id != asset_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    await uow.attachments.delete(attachment_id)
    await uow.commit()
    local_file_storage.delete_file(local_file_storage.ATTACHMENTS_SUBDIR, attachment.stored_filename)
