"""SQLAlchemy implementation of AttachmentRepository. Manages only the
DB-side metadata row - the route handler is responsible for writing/
deleting the actual file bytes via infrastructure/storage/
local_file_storage.py alongside calls to this repository."""
from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import AttachmentRepository
from app.domain.entities.asset_attachment import AssetAttachment
from app.infrastructure.database.models.asset_attachment import AssetAttachmentModel
from app.infrastructure.database.repositories.mappers import attachment_to_domain


class SqlAlchemyAttachmentRepository(AttachmentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_asset(self, asset_id: int) -> Sequence[AssetAttachment]:
        stmt = (
            select(AssetAttachmentModel)
            .where(AssetAttachmentModel.asset_id == asset_id)
            .order_by(AssetAttachmentModel.uploaded_at.desc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [attachment_to_domain(m) for m in rows]

    async def get_by_id(self, attachment_id: int) -> Optional[AssetAttachment]:
        model = await self._session.get(AssetAttachmentModel, attachment_id)
        return attachment_to_domain(model) if model else None

    async def create(self, attachment: AssetAttachment) -> AssetAttachment:
        model = AssetAttachmentModel(
            asset_id=attachment.asset_id,
            original_filename=attachment.original_filename,
            stored_filename=attachment.stored_filename,
            content_type=attachment.content_type,
            file_size=attachment.file_size,
            uploaded_by=attachment.uploaded_by,
            uploaded_at=attachment.uploaded_at,
        )
        self._session.add(model)
        await self._session.flush()
        return attachment_to_domain(model)

    async def delete(self, attachment_id: int) -> None:
        model = await self._session.get(AssetAttachmentModel, attachment_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
