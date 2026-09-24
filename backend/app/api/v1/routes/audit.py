"""Audit history endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.audit import AuditListResponse, AuditRecordOut
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditListResponse)
async def list_audit(
    asset_id: Optional[int] = None,
    field_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    records, total = await uow.audit.list(
        asset_id=asset_id,
        field_name=field_name,
        date_from=date_from,
        date_to=date_to,
        offset=offset,
        limit=limit,
    )
    return AuditListResponse(
        items=[AuditRecordOut(**r.__dict__) for r in records], total=total, offset=offset, limit=limit
    )


@router.get("/{asset_id}", response_model=AuditListResponse)
async def list_audit_for_asset(
    asset_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    records, total = await uow.audit.list(asset_id=asset_id, offset=offset, limit=limit)
    return AuditListResponse(
        items=[AuditRecordOut(**r.__dict__) for r in records], total=total, offset=offset, limit=limit
    )
