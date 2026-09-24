"""SQLAlchemy implementation of AssetRepository."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional, Sequence

from sqlalchemy import asc, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import AssetRepository
from app.domain.entities.asset import Asset
from app.domain.value_objects.enums import UNDEFINED_FILTER_VALUE
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.models.asset_business import AssetBusinessModel
from app.infrastructure.database.models.inventory_asset import InventoryAssetModel
from app.infrastructure.database.models.inventory_network import InventoryNetworkModel
from app.infrastructure.database.models.inventory_storage import InventoryStorageModel
from app.infrastructure.database.repositories.mappers import asset_to_domain

SORTABLE_COLUMNS = {
    "hostname": InventoryAssetModel.hostname,
    "primary_ip": InventoryAssetModel.primary_ip,
    "last_seen": InventoryAssetModel.last_seen,
    "first_seen": InventoryAssetModel.first_seen,
}


class SqlAlchemyAssetRepository(AssetRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, asset_id: int) -> Optional[Asset]:
        model = await self._session.get(InventoryAssetModel, asset_id)
        return asset_to_domain(model) if model else None

    async def get_by_serial_number(self, serial_number: str) -> Optional[Asset]:
        stmt = select(InventoryAssetModel).where(InventoryAssetModel.serial_number == serial_number)
        model = (await self._session.execute(stmt)).scalars().first()
        return asset_to_domain(model) if model else None

    async def get_by_primary_ip(self, primary_ip: str) -> Optional[Asset]:
        stmt = select(InventoryAssetModel).where(InventoryAssetModel.primary_ip == primary_ip)
        model = (await self._session.execute(stmt)).scalars().first()
        return asset_to_domain(model) if model else None

    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        stmt = select(InventoryAssetModel).where(InventoryAssetModel.hostname == hostname)
        model = (await self._session.execute(stmt)).scalars().first()
        return asset_to_domain(model) if model else None

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
        stmt = select(InventoryAssetModel).outerjoin(
            AssetBusinessModel, AssetBusinessModel.asset_id == InventoryAssetModel.asset_id
        )
        count_stmt = select(func.count(func.distinct(InventoryAssetModel.asset_id))).outerjoin(
            AssetBusinessModel, AssetBusinessModel.asset_id == InventoryAssetModel.asset_id
        )

        if search:
            like = f"%{search}%"
            cond = (InventoryAssetModel.hostname.ilike(like)) | (InventoryAssetModel.primary_ip.ilike(like))
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        if technology:
            stmt = stmt.where(AssetBusinessModel.technology == technology)
            count_stmt = count_stmt.where(AssetBusinessModel.technology == technology)
        if environment:
            stmt = stmt.where(AssetBusinessModel.environment == environment)
            count_stmt = count_stmt.where(AssetBusinessModel.environment == environment)
        if status:
            stmt = stmt.where(AssetBusinessModel.status == status)
            count_stmt = count_stmt.where(AssetBusinessModel.status == status)
        if site:
            stmt = stmt.where(AssetBusinessModel.site == site)
            count_stmt = count_stmt.where(AssetBusinessModel.site == site)
        if os_distribution:
            if os_distribution == UNDEFINED_FILTER_VALUE:
                cond = (InventoryAssetModel.os_distribution.is_(None)) | (
                    InventoryAssetModel.os_distribution == ""
                )
            else:
                cond = InventoryAssetModel.os_distribution == os_distribution
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        if manufacturer:
            cond = self._undefined_or_equals(InventoryAssetModel.manufacturer, manufacturer)
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)
        if model:
            cond = self._undefined_or_equals(InventoryAssetModel.model, model)
            stmt = stmt.where(cond)
            count_stmt = count_stmt.where(cond)

        column = SORTABLE_COLUMNS.get(sort_by, InventoryAssetModel.hostname)
        order = desc(column) if sort_dir.lower() == "desc" else asc(column)
        stmt = stmt.order_by(order).offset(offset).limit(limit)

        total = (await self._session.execute(count_stmt)).scalar_one()
        models = (await self._session.execute(stmt)).scalars().unique().all()
        return [asset_to_domain(m) for m in models], total

    def _undefined_or_equals(self, column, value: str):
        if value == UNDEFINED_FILTER_VALUE:
            return (column.is_(None)) | (column == "")
        return column == value

    async def distinct_hardware_values(self) -> dict:
        manufacturer_stmt = (
            select(InventoryAssetModel.manufacturer)
            .where(InventoryAssetModel.manufacturer.is_not(None))
            .where(InventoryAssetModel.manufacturer != "")
            .distinct()
        )
        model_stmt = (
            select(InventoryAssetModel.model)
            .where(InventoryAssetModel.model.is_not(None))
            .where(InventoryAssetModel.model != "")
            .distinct()
        )
        manufacturers = sorted(
            row[0] for row in (await self._session.execute(manufacturer_stmt)).all()
        )
        models = sorted(row[0] for row in (await self._session.execute(model_stmt)).all())
        return {"manufacturer": manufacturers, "model": models}

    async def create(self, asset: Asset) -> Asset:
        model = InventoryAssetModel(
            hostname=asset.hostname,
            serial_number=asset.serial_number,
            primary_ip=asset.primary_ip,
            manufacturer=asset.hardware.manufacturer,
            model=asset.hardware.model,
            cpu_model=asset.hardware.cpu_model,
            cpu_count=asset.hardware.cpu_count,
            cpu_cores=asset.hardware.cpu_cores,
            cpu_threads=asset.hardware.cpu_threads,
            ram_gb=asset.hardware.ram_gb,
            os_distribution=asset.os.distribution,
            os_version=asset.os.version,
            kernel_version=asset.os.kernel,
            architecture=asset.os.architecture,
            uptime_seconds=asset.os.uptime_seconds,
            virtual_physical=asset.virtual_physical,
            hypervisor=asset.hypervisor,
            first_seen=asset.first_seen,
            last_seen=asset.last_seen,
            last_collection=asset.last_collection,
        )
        # Explicitly mark these collections as loaded (empty) - without
        # this, accessing them via asset_to_domain() after flush() below
        # triggers a lazy load, which fails outside an async greenlet
        # context since this object was never queried from the DB.
        model.storage = []
        model.network = []
        self._session.add(model)
        await self._session.flush()
        # New assets default to Active business status so they show up
        # correctly on the dashboard immediately.
        self._session.add(AssetBusinessModel(asset_id=model.asset_id, status="Active"))
        await self._session.flush()
        return asset_to_domain(model)

    async def update(self, asset: Asset) -> Asset:
        model = await self._session.get(InventoryAssetModel, asset.asset_id)
        if model is None:
            raise ValueError(f"Asset {asset.asset_id} does not exist")

        model.hostname = asset.hostname
        model.serial_number = asset.serial_number
        model.primary_ip = asset.primary_ip
        model.manufacturer = asset.hardware.manufacturer
        model.model = asset.hardware.model
        model.cpu_model = asset.hardware.cpu_model
        model.cpu_count = asset.hardware.cpu_count
        model.cpu_cores = asset.hardware.cpu_cores
        model.cpu_threads = asset.hardware.cpu_threads
        model.ram_gb = asset.hardware.ram_gb
        model.os_distribution = asset.os.distribution
        model.os_version = asset.os.version
        model.kernel_version = asset.os.kernel
        model.architecture = asset.os.architecture
        model.uptime_seconds = asset.os.uptime_seconds
        model.virtual_physical = asset.virtual_physical
        model.hypervisor = asset.hypervisor
        model.last_seen = asset.last_seen
        model.last_collection = asset.last_collection

        await self._session.flush()
        return asset_to_domain(model)

    async def replace_storage(self, asset_id: int, storage: List) -> None:
        await self._session.execute(
            delete(InventoryStorageModel).where(InventoryStorageModel.asset_id == asset_id)
        )
        for item in storage:
            self._session.add(
                InventoryStorageModel(
                    asset_id=asset_id,
                    device_name=item.device_name,
                    filesystem_type=item.filesystem_type,
                    mount_point=item.mount_point,
                    capacity_gb=item.capacity_gb,
                )
            )
        await self._session.flush()

    async def replace_network(self, asset_id: int, network: List) -> None:
        await self._session.execute(
            delete(InventoryNetworkModel).where(InventoryNetworkModel.asset_id == asset_id)
        )
        for item in network:
            self._session.add(
                InventoryNetworkModel(
                    asset_id=asset_id,
                    interface_name=item.interface_name,
                    ip_address=item.ip_address,
                    mac_address=item.mac_address,
                )
            )
        await self._session.flush()

    async def dashboard_summary(self) -> dict:
        settings = get_settings()
        now = datetime.utcnow()
        active_cutoff = now - timedelta(days=settings.active_threshold_days)
        offline_cutoff = now - timedelta(days=settings.offline_threshold_days)

        total = (await self._session.execute(select(func.count(InventoryAssetModel.asset_id)))).scalar_one()

        status_counts_stmt = select(AssetBusinessModel.status, func.count()).group_by(AssetBusinessModel.status)
        status_rows = (await self._session.execute(status_counts_stmt)).all()
        by_status = {row[0]: row[1] for row in status_rows}

        vp_stmt = select(InventoryAssetModel.virtual_physical, func.count()).group_by(
            InventoryAssetModel.virtual_physical
        )
        vp_rows = (await self._session.execute(vp_stmt)).all()
        by_virtual_physical = {(row[0] or "Unknown"): row[1] for row in vp_rows}

        tech_stmt = (
            select(AssetBusinessModel.technology, func.count())
            .where(AssetBusinessModel.technology.is_not(None))
            .group_by(AssetBusinessModel.technology)
        )
        by_technology = {row[0]: row[1] for row in (await self._session.execute(tech_stmt)).all()}

        # Unlike technology/OS, a host with no Site or Environment assigned
        # is still counted here - as an "Un Defined" bucket - rather than
        # silently dropped, so the chart reflects every host in the fleet
        # and makes it obvious how many still need that field filled in.
        site_stmt = select(AssetBusinessModel.site, func.count()).group_by(AssetBusinessModel.site)
        by_site = self._bucket_undefined((await self._session.execute(site_stmt)).all())

        env_stmt = select(AssetBusinessModel.environment, func.count()).group_by(AssetBusinessModel.environment)
        by_environment = self._bucket_undefined((await self._session.execute(env_stmt)).all())

        os_stmt = select(InventoryAssetModel.os_distribution, func.count()).group_by(
            InventoryAssetModel.os_distribution
        )
        os_rows = (await self._session.execute(os_stmt)).all()
        by_os_family = {(row[0] or "Unknown"): row[1] for row in os_rows}

        man_stmt = select(InventoryAssetModel.manufacturer, func.count()).group_by(
            InventoryAssetModel.manufacturer
        )
        man_rows = (await self._session.execute(man_stmt)).all()
        by_manufacturer = {(row[0] or "Unknown"): row[1] for row in man_rows}

        model_stmt = select(InventoryAssetModel.model, func.count()).group_by(InventoryAssetModel.model)
        model_rows = (await self._session.execute(model_stmt)).all()
        by_model = self._top_n_with_other(model_rows, top_n=9)

        expiring_support = await self._expiring_support(settings.support_expiry_alert_days)

        return {
            "total_assets": total,
            "active_assets": by_status.get("Active", 0),
            "offline_assets": by_status.get("Offline", 0),
            "retired_assets": by_status.get("Retired", 0),
            "physical_assets": by_virtual_physical.get("Physical", 0),
            "virtual_assets": by_virtual_physical.get("Virtual", 0),
            "by_technology": by_technology,
            "by_site": by_site,
            "by_environment": by_environment,
            "by_os_family": by_os_family,
            "by_manufacturer": by_manufacturer,
            "by_model": by_model,
            "expiring_support_count": len(expiring_support),
            "expiring_support": expiring_support[:25],
        }

    def _bucket_undefined(self, rows) -> dict[str, int]:
        """Merges NULL and empty-string group keys into a single
        "Un Defined" bucket. A host whose Site/Environment was never set
        (NULL) and one where it was cleared via the edit form (saved as
        "") both mean "not filled in yet" and should count as one bucket,
        rather than one being silently dropped by a NULL filter and the
        other showing up as a blank/unlabeled bar in the chart."""
        result: dict[str, int] = {}
        for value, count in rows:
            key = value if value else "Un Defined"
            result[key] = result.get(key, 0) + count
        return result

    def _top_n_with_other(self, rows, top_n: int) -> dict[str, int]:
        """Merges NULL/empty model values into "Unknown", keeps the top
        `top_n` most common remaining values, and collapses everything
        else into a single "Other" bucket - Model can have far higher
        cardinality than the other dashboard dimensions, so without this
        the chart would be unreadable. "Other" is intentionally not a
        single real value, so unlike the rest of the dashboard's pies it
        isn't meant to be clickable through to a filtered list."""
        merged: dict[str, int] = {}
        for value, count in rows:
            key = value if value else "Unknown"
            merged[key] = merged.get(key, 0) + count

        unknown_count = merged.pop("Unknown", 0)
        ranked = sorted(merged.items(), key=lambda kv: kv[1], reverse=True)
        top = ranked[:top_n]
        rest = ranked[top_n:]

        result: dict[str, int] = {name: count for name, count in top}
        if unknown_count:
            result["Unknown"] = unknown_count
        other_count = sum(count for _, count in rest)
        if other_count:
            result["Other"] = other_count
        return result

    async def _expiring_support(self, within_days: int) -> list[dict]:
        """Assets whose HW or OS support expiry is `within_days` away or
        sooner (already-expired counts too - it's trivially "sooner").
        Returns one entry per (asset, expiring field) pair, soonest first,
        so an asset with both HW and OS expiring soon shows up twice with
        its own countdown for each."""
        today = date.today()
        cutoff = today + timedelta(days=within_days)

        stmt = (
            select(
                InventoryAssetModel.asset_id,
                InventoryAssetModel.hostname,
                AssetBusinessModel.hw_support_expiry,
                AssetBusinessModel.os_support_expiry,
            )
            .join(AssetBusinessModel, AssetBusinessModel.asset_id == InventoryAssetModel.asset_id)
            .where(
                (AssetBusinessModel.hw_support_expiry <= cutoff)
                | (AssetBusinessModel.os_support_expiry <= cutoff)
            )
        )
        rows = (await self._session.execute(stmt)).all()

        items: list[dict] = []
        for asset_id, hostname, hw_expiry, os_expiry in rows:
            if hw_expiry is not None and hw_expiry <= cutoff:
                items.append(
                    {
                        "asset_id": asset_id,
                        "hostname": hostname,
                        "support_type": "Hardware",
                        "expiry_date": hw_expiry,
                        "days_remaining": (hw_expiry - today).days,
                    }
                )
            if os_expiry is not None and os_expiry <= cutoff:
                items.append(
                    {
                        "asset_id": asset_id,
                        "hostname": hostname,
                        "support_type": "OS",
                        "expiry_date": os_expiry,
                        "days_remaining": (os_expiry - today).days,
                    }
                )
        items.sort(key=lambda i: i["days_remaining"])
        return items
