"""Support Team reference-data endpoints (Name / Contact Number / Email /
Location / Notes). Used by the Support Team management page and to
populate the Support Team dropdown on the Asset Details business-metadata
form and the Inventory bulk-edit dialog."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.support_team import SupportTeamCreate, SupportTeamOut, SupportTeamUpdate
from app.domain.entities.support_team import SupportTeam
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/support-teams", tags=["support-teams"])


@router.get("", response_model=List[SupportTeamOut])
async def list_support_teams(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    teams = await uow.support_teams.list()
    return [SupportTeamOut.model_validate(t, from_attributes=True) for t in teams]


@router.post("", response_model=SupportTeamOut, status_code=201)
async def create_support_team(
    payload: SupportTeamCreate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    try:
        saved = await uow.support_teams.create(
            SupportTeam(
                name=payload.name,
                contact_number=payload.contact_number,
                email=payload.email,
                location=payload.location,
                notes=payload.notes,
            )
        )
        await uow.commit()
    except IntegrityError:
        await uow.rollback()
        raise HTTPException(status_code=400, detail=f"Support team '{payload.name}' already exists")
    return SupportTeamOut.model_validate(saved, from_attributes=True)


@router.put("/{support_team_id}", response_model=SupportTeamOut)
async def update_support_team(
    support_team_id: int,
    payload: SupportTeamUpdate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    existing = await uow.support_teams.get_by_id(support_team_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Support team not found")
    try:
        saved = await uow.support_teams.update(
            SupportTeam(
                support_team_id=support_team_id,
                name=payload.name,
                contact_number=payload.contact_number,
                email=payload.email,
                location=payload.location,
                notes=payload.notes,
            )
        )
        await uow.commit()
    except IntegrityError:
        await uow.rollback()
        raise HTTPException(status_code=400, detail=f"Support team '{payload.name}' already exists")
    return SupportTeamOut.model_validate(saved, from_attributes=True)


@router.delete("/{support_team_id}", status_code=204)
async def delete_support_team(
    support_team_id: int,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.ADMIN)),
):
    existing = await uow.support_teams.get_by_id(support_team_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Support team not found")
    await uow.support_teams.delete(support_team_id)
    await uow.commit()
