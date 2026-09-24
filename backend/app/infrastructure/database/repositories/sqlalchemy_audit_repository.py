"""SQLAlchemy implementation of AuditRepository."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import AuditRepository
from app.domain.entities.audit_record import AuditRecord
from app.infrastructure.database.models.asset_audit import AssetAuditModel
from app.infrastructure.database.repositories.mappers import audit_to_domain


class SqlAlchemyAuditRepository(AuditRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_many(self, records: List[AuditRecord]) -> None:
        for record in records:
            self._session.add(
                AssetAuditModel(
                    asset_id=record.asset_id,
                    collector_run_id=record.collector_run_id,
                    field_name=record.field_name,
                    old_value=record.old_value,
                    new_value=record.new_value,
                    change_timestamp=record.change_timestamp,
                    source=record.source,
                )
            )
        await self._session.flush()

    async def list(
        self,
        *,
        asset_id: Optional[int] = None,
        field_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[AuditRecord], int]:
        stmt = select(AssetAuditModel)
        count_stmt = select(func.count(AssetAuditModel.audit_id))

        if asset_id is not None:
            stmt = stmt.where(AssetAuditModel.asset_id == asset_id)
            count_stmt = count_stmt.where(AssetAuditModel.asset_id == asset_id)
        if field_name:
            stmt = stmt.where(AssetAuditModel.field_name == field_name)
            count_stmt = count_stmt.where(AssetAuditModel.field_name == field_name)
        if date_from:
            stmt = stmt.where(AssetAuditModel.change_timestamp >= date_from)
            count_stmt = count_stmt.where(AssetAuditModel.change_timestamp >= date_from)
        if date_to:
            stmt = stmt.where(AssetAuditModel.change_timestamp <= date_to)
            count_stmt = count_stmt.where(AssetAuditModel.change_timestamp <= date_to)

        stmt = stmt.order_by(desc(AssetAuditModel.change_timestamp)).offset(offset).limit(limit)

        total = (await self._session.execute(count_stmt)).scalar_one()
        models = (await self._session.execute(stmt)).scalars().all()
        return [audit_to_domain(m) for m in models], total
