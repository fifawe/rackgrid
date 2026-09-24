"""SQLAlchemy implementation of SystemSettingsRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import SystemSettingsRepository
from app.infrastructure.database.models.system_setting import SystemSettingModel


class SqlAlchemySystemSettingsRepository(SystemSettingsRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        model = await self._session.get(SystemSettingModel, name)
        return model.setting_value if model else default

    async def set(self, name: str, value: str) -> None:
        model = await self._session.get(SystemSettingModel, name)
        if model is None:
            model = SystemSettingModel(setting_name=name, setting_value=value)
            self._session.add(model)
        else:
            model.setting_value = value
        await self._session.flush()

    async def all(self) -> dict:
        stmt = select(SystemSettingModel)
        rows = (await self._session.execute(stmt)).scalars().all()
        return {r.setting_name: r.setting_value for r in rows}
