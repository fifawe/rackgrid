"""Repository ports (interfaces) the application layer depends on.

Concrete implementations live in the infrastructure layer. Defining these
as ABCs keeps the application/domain layers persistence-agnostic, per the
Clean Architecture separation required by the project spec.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Sequence

from app.domain.entities.asset import Asset
from app.domain.entities.asset_attachment import AssetAttachment
from app.domain.entities.audit_record import AuditRecord
from app.domain.entities.business_metadata import BusinessMetadata
from app.domain.entities.collector_run import CollectorRun
from app.domain.entities.site import Site
from app.domain.entities.support_team import SupportTeam


class AssetRepository(ABC):
    @abstractmethod
    async def get_by_id(self, asset_id: int) -> Optional[Asset]:
        ...

    @abstractmethod
    async def get_by_serial_number(self, serial_number: str) -> Optional[Asset]:
        ...

    @abstractmethod
    async def get_by_primary_ip(self, primary_ip: str) -> Optional[Asset]:
        ...

    @abstractmethod
    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        ...

    @abstractmethod
    async def list(
        self,
        *,
        search: Optional[str] = None,
        technology: Optional[str] = None,
        environment: Optional[str] = None,
        status: Optional[str] = None,
        site: Optional[str] = None,
        os_distribution: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        sort_by: str = "hostname",
        sort_dir: str = "asc",
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[Asset], int]:
        """Returns (page of assets, total matching count).

        `os_distribution` is the literal value of `os_distribution` to
        match, or the sentinel `"__none__"` to match assets that have no
        OS distribution recorded at all (the "Unknown" bucket on the
        dashboard's By OS Family chart) - used when the dashboard's pie
        charts are clicked through to a filtered Inventory list.

        `manufacturer` and `model` are exact-match filters on the
        collector-reported hardware fields; either also accepts the
        `"__none__"` sentinel to match assets with no value recorded, for
        the same click-through-to-filtered-list reason as `os_distribution`.
        """
        ...

    @abstractmethod
    async def distinct_hardware_values(self) -> dict:
        """Distinct, non-empty existing `manufacturer` and `model` values
        currently in the inventory, sorted alphabetically - used to
        populate the Inventory page's Manufacturer/Model filter dropdowns."""
        ...

    @abstractmethod
    async def create(self, asset: Asset) -> Asset:
        ...

    @abstractmethod
    async def update(self, asset: Asset) -> Asset:
        ...

    @abstractmethod
    async def replace_storage(self, asset_id: int, storage: list) -> None:
        ...

    @abstractmethod
    async def replace_network(self, asset_id: int, network: list) -> None:
        ...

    @abstractmethod
    async def dashboard_summary(self) -> dict:
        """Aggregate counts used by the Dashboard page: totals by status,
        by virtual/physical, by technology, by site, by environment, by
        manufacturer (Unknown bucket for missing values), and by model
        (Unknown bucket for missing values, plus an "Other" bucket
        collapsing everything past the top N most common models so the
        chart stays readable)."""
        ...


class BusinessMetadataRepository(ABC):
    @abstractmethod
    async def get_by_asset_id(self, asset_id: int) -> Optional[BusinessMetadata]:
        ...

    @abstractmethod
    async def upsert(self, metadata: BusinessMetadata) -> BusinessMetadata:
        ...

    @abstractmethod
    async def field_options(self) -> dict:
        """Distinct, non-empty existing values already used for the
        'dropdown with option to add new' fields: support_team,
        asset_owner, site, technology, environment."""
        ...


class AuditRepository(ABC):
    @abstractmethod
    async def add_many(self, records: List[AuditRecord]) -> None:
        ...

    @abstractmethod
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
        ...


class CollectorRunRepository(ABC):
    @abstractmethod
    async def create(self, run: CollectorRun) -> CollectorRun:
        ...

    @abstractmethod
    async def update(self, run: CollectorRun) -> CollectorRun:
        ...

    @abstractmethod
    async def increment_success(self, run_id: int) -> None:
        """Atomically bumps success_count/assets_processed by 1.

        Used from the per-host discovery endpoint, where many hosts from
        the same collection run submit concurrently (Ansible's `linear`
        strategy fires every host's submit_payload task within the same
        handful of seconds). A load-mutate-save `update()` there is a
        classic read-modify-write race - concurrent requests overwrite
        each other's counts, and under real lock contention can throw and
        take the whole per-host transaction down with it. A single atomic
        UPDATE has neither problem.
        """
        ...

    @abstractmethod
    async def increment_failure(self, run_id: int) -> None:
        """See increment_success - the failure-count equivalent."""
        ...

    @abstractmethod
    async def list(self, *, offset: int = 0, limit: int = 50) -> tuple[Sequence[CollectorRun], int]:
        ...

    @abstractmethod
    async def get_by_id(self, run_id: int) -> Optional[CollectorRun]:
        ...


class SystemSettingsRepository(ABC):
    @abstractmethod
    async def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        ...

    @abstractmethod
    async def set(self, name: str, value: str) -> None:
        ...

    @abstractmethod
    async def all(self) -> dict:
        ...


class UserRepository(ABC):
    @abstractmethod
    async def get_by_username(self, username: str):
        ...

    @abstractmethod
    async def update_password(self, username: str, hashed_password: str) -> None:
        ...


class SiteRepository(ABC):
    @abstractmethod
    async def list(self) -> Sequence[Site]:
        ...

    @abstractmethod
    async def get_by_id(self, site_id: int) -> Optional[Site]:
        ...

    @abstractmethod
    async def create(self, site: Site) -> Site:
        ...

    @abstractmethod
    async def update(self, site: Site) -> Site:
        ...

    @abstractmethod
    async def delete(self, site_id: int) -> None:
        ...


class SupportTeamRepository(ABC):
    @abstractmethod
    async def list(self) -> Sequence[SupportTeam]:
        ...

    @abstractmethod
    async def get_by_id(self, support_team_id: int) -> Optional[SupportTeam]:
        ...

    @abstractmethod
    async def create(self, team: SupportTeam) -> SupportTeam:
        ...

    @abstractmethod
    async def update(self, team: SupportTeam) -> SupportTeam:
        ...

    @abstractmethod
    async def delete(self, support_team_id: int) -> None:
        ...


class AttachmentRepository(ABC):
    """Design documents (and other reference files) uploaded against a
    specific asset. The repository only manages the DB-side metadata
    row; the actual file bytes go through
    infrastructure/storage/local_file_storage.py, invoked from the route
    handler alongside this."""

    @abstractmethod
    async def list_for_asset(self, asset_id: int) -> Sequence[AssetAttachment]:
        ...

    @abstractmethod
    async def get_by_id(self, attachment_id: int) -> Optional[AssetAttachment]:
        ...

    @abstractmethod
    async def create(self, attachment: AssetAttachment) -> AssetAttachment:
        ...

    @abstractmethod
    async def delete(self, attachment_id: int) -> None:
        ...
