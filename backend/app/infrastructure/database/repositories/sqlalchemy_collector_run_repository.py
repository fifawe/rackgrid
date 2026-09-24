"""SQLAlchemy implementation of CollectorRunRepository."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import CollectorRunRepository
from app.domain.entities.collector_run import CollectorRun
from app.infrastructure.database.models.collector_run import CollectorRunModel
from app.infrastructure.database.repositories.mappers import run_to_domain


class SqlAlchemyCollectorRunRepository(CollectorRunRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, run: CollectorRun) -> CollectorRun:
        model = CollectorRunModel(
            start_time=run.start_time,
            end_time=run.end_time,
            status=run.status.value,
            assets_processed=run.assets_processed,
            success_count=run.success_count,
            failure_count=run.failure_count,
            trigger_source=run.trigger_source.value,
        )
        self._session.add(model)
        await self._session.flush()
        return run_to_domain(model)

    async def update(self, run: CollectorRun) -> CollectorRun:
        model = await self._session.get(CollectorRunModel, run.run_id)
        if model is None:
            raise ValueError(f"CollectorRun {run.run_id} does not exist")
        model.end_time = run.end_time
        model.status = run.status.value
        model.assets_processed = run.assets_processed
        model.success_count = run.success_count
        model.failure_count = run.failure_count
        await self._session.flush()
        return run_to_domain(model)

    async def increment_success(self, run_id: int) -> None:
        # A single atomic UPDATE ... SET x = x + 1, instead of
        # get()-then-mutate-then-flush(), so concurrent hosts from the
        # same run (see the interface docstring) can't clobber each
        # other's counts or deadlock the row.
        stmt = (
            update(CollectorRunModel)
            .where(CollectorRunModel.run_id == run_id)
            .values(
                success_count=CollectorRunModel.success_count + 1,
                assets_processed=CollectorRunModel.assets_processed + 1,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def increment_failure(self, run_id: int) -> None:
        stmt = (
            update(CollectorRunModel)
            .where(CollectorRunModel.run_id == run_id)
            .values(
                failure_count=CollectorRunModel.failure_count + 1,
                assets_processed=CollectorRunModel.assets_processed + 1,
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def list(self, *, offset: int = 0, limit: int = 50) -> tuple[Sequence[CollectorRun], int]:
        stmt = select(CollectorRunModel).order_by(desc(CollectorRunModel.start_time)).offset(offset).limit(limit)
        total = (await self._session.execute(select(func.count(CollectorRunModel.run_id)))).scalar_one()
        models = (await self._session.execute(stmt)).scalars().all()
        return [run_to_domain(m) for m in models], total

    async def get_by_id(self, run_id: int) -> Optional[CollectorRun]:
        model = await self._session.get(CollectorRunModel, run_id)
        return run_to_domain(model) if model else None
