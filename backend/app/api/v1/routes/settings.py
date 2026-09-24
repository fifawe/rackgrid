"""Platform branding settings - a custom title and logo shown in the
sidebar and on the login page, plus the running app version. Backed by
the existing system_settings key/value store (see
infrastructure/database/repositories/sqlalchemy_settings_repository.py);
the logo file itself lives on local disk (see
infrastructure/storage/local_file_storage.py) with only its stored
filename/content-type kept in system_settings.

GET /public and GET /logo deliberately require no auth: the login page
needs the title/logo before anyone is signed in, and neither is
sensitive information."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.settings import PlatformTitleUpdate, PublicSettingsOut
from app.domain.value_objects.enums import UserRole
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.storage import local_file_storage

router = APIRouter(prefix="/settings", tags=["settings"])

_DEFAULT_TITLE = "Asset Inventory Platform"
_TITLE_KEY = "platform_title"
_LOGO_FILENAME_KEY = "logo_stored_filename"
_LOGO_CONTENT_TYPE_KEY = "logo_content_type"

_ALLOWED_LOGO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}
_MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024


@router.get("/public", response_model=PublicSettingsOut)
async def get_public_settings(uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    title = await uow.settings.get(_TITLE_KEY, _DEFAULT_TITLE)
    logo_filename = await uow.settings.get(_LOGO_FILENAME_KEY)
    return PublicSettingsOut(
        platform_title=title,
        logo_url="/api/v1/settings/logo" if logo_filename else None,
        version=get_settings().app_version,
    )


@router.get("/logo")
async def get_logo(uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    logo_filename = await uow.settings.get(_LOGO_FILENAME_KEY)
    if not logo_filename:
        raise HTTPException(status_code=404, detail="No logo has been uploaded")
    content_type = await uow.settings.get(_LOGO_CONTENT_TYPE_KEY, "application/octet-stream")
    try:
        content = local_file_storage.read_file(local_file_storage.BRANDING_SUBDIR, logo_filename)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Logo file is missing from storage")
    return Response(content=content, media_type=content_type)


@router.put("/title", response_model=PublicSettingsOut)
async def update_platform_title(
    payload: PlatformTitleUpdate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.ADMIN)),
):
    await uow.settings.set(_TITLE_KEY, payload.platform_title.strip())
    await uow.commit()
    return await get_public_settings(uow)


@router.post("/logo", response_model=PublicSettingsOut)
async def upload_logo(
    file: UploadFile,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.ADMIN)),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required")
    extension = Path(file.filename).suffix.lower()
    if extension not in _ALLOWED_LOGO_EXTENSIONS:
        allowed = ", ".join(sorted(_ALLOWED_LOGO_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"File type not allowed - accepted types: {allowed}")

    content = await file.read()
    if len(content) > _MAX_LOGO_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Logo is too large - max {_MAX_LOGO_SIZE_BYTES // (1024 * 1024)} MB",
        )

    # Replace: remove the previous logo file (if any) so uploads don't
    # accumulate orphaned files on disk.
    old_filename = await uow.settings.get(_LOGO_FILENAME_KEY)
    if old_filename:
        local_file_storage.delete_file(local_file_storage.BRANDING_SUBDIR, old_filename)

    stored_filename = local_file_storage.save_file(
        local_file_storage.BRANDING_SUBDIR, file.filename, content
    )
    await uow.settings.set(_LOGO_FILENAME_KEY, stored_filename)
    await uow.settings.set(_LOGO_CONTENT_TYPE_KEY, file.content_type or "application/octet-stream")
    await uow.commit()
    return await get_public_settings(uow)


@router.delete("/logo", response_model=PublicSettingsOut)
async def delete_logo(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.ADMIN)),
):
    old_filename = await uow.settings.get(_LOGO_FILENAME_KEY)
    if old_filename:
        local_file_storage.delete_file(local_file_storage.BRANDING_SUBDIR, old_filename)
        await uow.settings.set(_LOGO_FILENAME_KEY, "")
        await uow.commit()
    return await get_public_settings(uow)
