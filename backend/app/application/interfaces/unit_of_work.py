"""Unit of Work abstraction.

Wraps a set of repositories that must be committed atomically. The
infrastructure layer provides a SQLAlchemy-backed implementation bound to
a single AsyncSession per request/job.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.application.interfaces.repositories import (
    AssetRepository,
    AttachmentRepository,
    AuditRepository,
    BusinessMetadataRepository,
    CollectorRunRepository,
    SiteRepository,
    SupportTeamRepository,
    SystemSettingsRepository,
    UserRepository,
)


class UnitOfWork(ABC):
    assets: AssetRepository
    business_metadata: BusinessMetadataRepository
    audit: AuditRepository
    collector_runs: CollectorRunRepository
    settings: SystemSettingsRepository
    users: UserRepository
    sites: SiteRepository
    support_teams: SupportTeamRepository
    attachments: AttachmentRepository

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...
