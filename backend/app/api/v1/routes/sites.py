"""Site reference-data endpoints (Site name / code / city). Used by the
Sites management page and to populate the Site dropdown on the Asset
Details business-metadata form."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.site import SiteCreate, SiteOut, SiteUpdate
from app.domain.entities.site import Site
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=List[SiteOut])
async def list_sites(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    sites = await uow.sites.list()
    return [SiteOut.model_validate(s, from_attributes=True) for s in sites]


@router.post("", response_model=SiteOut, status_code=201)
async def create_site(
    payload: SiteCreate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    try:
        saved = await uow.sites.create(Site(name=payload.name, code=payload.code, city=payload.city))
        await uow.commit()
    except IntegrityError:
        await uow.rollback()
        raise HTTPException(status_code=400, detail=f"Site '{payload.name}' already exists")
    return SiteOut.model_validate(saved, from_attributes=True)


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: int,
    payload: SiteUpdate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    existing = await uow.sites.get_by_id(site_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Site not found")
    try:
        saved = await uow.sites.update(Site(site_id=site_id, name=payload.name, code=payload.code, city=payload.city))
        await uow.commit()
    except IntegrityError:
        await uow.rollback()
        raise HTTPException(status_code=400, detail=f"Site '{payload.name}' already exists")
    return SiteOut.model_validate(saved, from_attributes=True)


@router.delete("/{site_id}", status_code=204)
async def delete_site(
    site_id: int,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.ADMIN)),
):
    existing = await uow.sites.get_by_id(site_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Site not found")
    await uow.sites.delete(site_id)
    await uow.commit()
