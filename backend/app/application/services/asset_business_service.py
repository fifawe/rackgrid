"""Business metadata management (manual, dashboard-driven).

This is the ONLY service permitted to write asset_business fields. It
never touches collector-owned fields on the Asset entity.
"""
from __future__ import annotations

from typing import Optional

from app.application.interfaces.unit_of_work import UnitOfWork
from app.domain.entities.business_metadata import BusinessMetadata
from app.domain.exceptions.errors import AssetNotFoundError


class AssetBusinessService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def get(self, asset_id: int) -> Optional[BusinessMetadata]:
        return await self._uow.business_metadata.get_by_asset_id(asset_id)

    async def upsert(self, asset_id: int, updates: dict) -> BusinessMetadata:
        asset = await self._uow.assets.get_by_id(asset_id)
        if asset is None:
            raise AssetNotFoundError(asset_id)

        current = await self._uow.business_metadata.get_by_asset_id(asset_id)
        if current is None:
            current = BusinessMetadata(asset_id=asset_id)

        for field_name, value in updates.items():
            if hasattr(current, field_name) and field_name != "asset_id":
                setattr(current, field_name, value)

        saved = await self._uow.business_metadata.upsert(current)
        return saved
