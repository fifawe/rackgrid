"""SQLAlchemy implementation of SiteRepository."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import SiteRepository
from app.domain.entities.site import Site
from app.infrastructure.database.models.site import SiteModel
from app.infrastructure.database.repositories.mappers import site_to_domain


class SqlAlchemySiteRepository(SiteRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list(self) -> Sequence[Site]:
        stmt = select(SiteModel).order_by(SiteModel.name.asc())
        rows = (await self._session.execute(stmt)).scalars().all()
        return [site_to_domain(m) for m in rows]

    async def get_by_id(self, site_id: int) -> Optional[Site]:
        model = await self._session.get(SiteModel, site_id)
        return site_to_domain(model) if model else None

    async def create(self, site: Site) -> Site:
        model = SiteModel(name=site.name, code=site.code, city=site.city)
        self._session.add(model)
        await self._session.flush()
        return site_to_domain(model)

    async def update(self, site: Site) -> Site:
        model = await self._session.get(SiteModel, site.site_id)
        if model is None:
            raise ValueError(f"Site {site.site_id} not found")
        model.name = site.name
        model.code = site.code
        model.city = site.city
        await self._session.flush()
        return site_to_domain(model)

    async def delete(self, site_id: int) -> None:
        model = await self._session.get(SiteModel, site_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
