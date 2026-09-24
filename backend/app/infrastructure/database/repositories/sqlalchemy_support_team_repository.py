"""SQLAlchemy implementation of SupportTeamRepository."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import SupportTeamRepository
from app.domain.entities.support_team import SupportTeam
from app.infrastructure.database.models.support_team import SupportTeamModel
from app.infrastructure.database.repositories.mappers import support_team_to_domain


class SqlAlchemySupportTeamRepository(SupportTeamRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list(self) -> Sequence[SupportTeam]:
        stmt = select(SupportTeamModel).order_by(SupportTeamModel.name.asc())
        rows = (await self._session.execute(stmt)).scalars().all()
        return [support_team_to_domain(m) for m in rows]

    async def get_by_id(self, support_team_id: int) -> Optional[SupportTeam]:
        model = await self._session.get(SupportTeamModel, support_team_id)
        return support_team_to_domain(model) if model else None

    async def create(self, team: SupportTeam) -> SupportTeam:
        model = SupportTeamModel(
            name=team.name,
            contact_number=team.contact_number,
            email=team.email,
            location=team.location,
            notes=team.notes,
        )
        self._session.add(model)
        await self._session.flush()
        return support_team_to_domain(model)

    async def update(self, team: SupportTeam) -> SupportTeam:
        model = await self._session.get(SupportTeamModel, team.support_team_id)
        if model is None:
            raise ValueError(f"Support team {team.support_team_id} not found")
        model.name = team.name
        model.contact_number = team.contact_number
        model.email = team.email
        model.location = team.location
        model.notes = team.notes
        await self._session.flush()
        return support_team_to_domain(model)

    async def delete(self, support_team_id: int) -> None:
        model = await self._session.get(SupportTeamModel, support_team_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
