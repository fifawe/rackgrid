"""Dashboard summary aggregation service."""
from __future__ import annotations

from app.application.interfaces.unit_of_work import UnitOfWork


class DashboardService:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def summary(self) -> dict:
        # Delegated to the repository, which can express this efficiently
        # as SQL aggregate queries rather than loading every asset.
        return await self._uow.assets.dashboard_summary()
