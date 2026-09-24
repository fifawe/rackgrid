"""SQLAlchemy implementation of BusinessMetadataRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import BusinessMetadataRepository
from app.domain.entities.business_metadata import BusinessMetadata
from app.infrastructure.database.models.asset_business import AssetBusinessModel
from app.infrastructure.database.repositories.mappers import business_to_domain

# Columns offered by the dashboard's "dropdown with option to add new"
# fields (Support Team, Asset Owner, Site, Technology, Environment).
_FIELD_OPTION_COLUMNS = {
    "support_team": AssetBusinessModel.support_team,
    "asset_owner": AssetBusinessModel.asset_owner,
    "site": AssetBusinessModel.site,
    "technology": AssetBusinessModel.technology,
    "environment": AssetBusinessModel.environment,
}


class SqlAlchemyBusinessMetadataRepository(BusinessMetadataRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_asset_id(self, asset_id: int) -> Optional[BusinessMetadata]:
        model = await self._session.get(AssetBusinessModel, asset_id)
        return business_to_domain(model) if model else None

    async def field_options(self) -> dict:
        result: dict[str, list[str]] = {}
        for field_name, column in _FIELD_OPTION_COLUMNS.items():
            stmt = select(column).distinct().where(column.is_not(None), column != "").order_by(column.asc())
            values = (await self._session.execute(stmt)).scalars().all()
            result[field_name] = list(values)
        return result

    async def upsert(self, metadata: BusinessMetadata) -> BusinessMetadata:
        model = await self._session.get(AssetBusinessModel, metadata.asset_id)
        if model is None:
            model = AssetBusinessModel(asset_id=metadata.asset_id)
            self._session.add(model)

        model.asset_owner = metadata.asset_owner
        model.support_team = metadata.support_team
        model.application_name = metadata.application_name
        model.business_service = metadata.business_service
        model.environment = metadata.environment
        model.site = metadata.site
        model.rack_number = metadata.rack_number
        model.technology = metadata.technology
        model.hw_support_expiry = metadata.hw_support_expiry
        model.os_support_expiry = metadata.os_support_expiry
        model.status = metadata.status.value if metadata.status else "Active"

        await self._session.flush()
        return business_to_domain(model)
