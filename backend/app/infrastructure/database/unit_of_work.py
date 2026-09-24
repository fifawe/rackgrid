"""SQLAlchemy-backed UnitOfWork - binds all repositories to a single
AsyncSession so a discovery/business-update operation commits atomically."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.unit_of_work import UnitOfWork
from app.infrastructure.database.repositories.sqlalchemy_asset_repository import (
    SqlAlchemyAssetRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_attachment_repository import (
    SqlAlchemyAttachmentRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_audit_repository import (
    SqlAlchemyAuditRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_business_repository import (
    SqlAlchemyBusinessMetadataRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_collector_run_repository import (
    SqlAlchemyCollectorRunRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_settings_repository import (
    SqlAlchemySystemSettingsRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_site_repository import (
    SqlAlchemySiteRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_support_team_repository import (
    SqlAlchemySupportTeamRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession):
        self._session = session
        self.assets = SqlAlchemyAssetRepository(session)
        self.business_metadata = SqlAlchemyBusinessMetadataRepository(session)
        self.audit = SqlAlchemyAuditRepository(session)
        self.collector_runs = SqlAlchemyCollectorRunRepository(session)
        self.settings = SqlAlchemySystemSettingsRepository(session)
        self.users = SqlAlchemyUserRepository(session)
        self.sites = SqlAlchemySiteRepository(session)
        self.support_teams = SqlAlchemySupportTeamRepository(session)
        self.attachments = SqlAlchemyAttachmentRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
