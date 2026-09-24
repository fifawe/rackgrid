"""Asset inventory endpoints: list/search/filter/paginate, detail view,
and manual business-metadata updates."""
from __future__ import annotations

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.asset import (
    AssetDetailOut,
    AssetListResponse,
    AssetSummaryOut,
    BulkBusinessMetadataUpdate,
    BulkUpdateResult,
    BusinessMetadataOut,
    BusinessMetadataUpdate,
    FieldOptionsOut,
    HardwareOptionsOut,
    NetworkOut,
    StorageOut,
)
from app.application.services.asset_business_service import AssetBusinessService
from app.domain.exceptions.errors import AssetNotFoundError
from app.domain.value_objects.enums import Technology, UserRole
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/assets", tags=["assets"])


def _effective_status(asset, business) -> str:
    manual_status = business.status if business else None
    settings = get_settings()
    return asset.compute_status(
        manual_status,
        active_threshold_days=settings.active_threshold_days,
        offline_threshold_days=settings.offline_threshold_days,
    ).value


async def _summary_row(uow: SqlAlchemyUnitOfWork, asset) -> AssetSummaryOut:
    business = await uow.business_metadata.get_by_asset_id(asset.asset_id)
    return AssetSummaryOut(
        asset_id=asset.asset_id,
        hostname=asset.hostname,
        primary_ip=asset.primary_ip,
        technology=business.technology if business else None,
        environment=business.environment if business else None,
        asset_owner=business.asset_owner if business else None,
        status=_effective_status(asset, business),
        last_seen=asset.last_seen,
    )


@router.get("", response_model=AssetListResponse)
async def list_assets(
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
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    assets, total = await uow.assets.list(
        search=search,
        technology=technology,
        environment=environment,
        status=status,
        site=site,
        os_distribution=os_distribution,
        manufacturer=manufacturer,
        model=model,
        sort_by=sort_by,
        sort_dir=sort_dir,
        offset=offset,
        limit=limit,
    )
    items = [await _summary_row(uow, a) for a in assets]
    return AssetListResponse(items=items, total=total, offset=offset, limit=limit)


_CSV_COLUMNS = [
    "Hostname",
    "Serial Number",
    "Primary IP",
    "Status",
    "Virtual/Physical",
    "Hypervisor",
    "Manufacturer",
    "Model",
    "CPU Model",
    "CPU Count",
    "CPU Cores",
    "CPU Threads",
    "RAM (GB)",
    "OS Distribution",
    "OS Version",
    "Kernel Version",
    "Architecture",
    "Uptime (s)",
    "Support Team",
    "Asset Owner",
    "Application Name",
    "Business Service",
    "Environment",
    "Site",
    "Rack Number",
    "Technology",
    "HW Support Expiry",
    "OS Support Expiry",
    "First Seen",
    "Last Seen",
    "Last Collection",
]


def _full_export_row(asset, business) -> list:
    return [
        asset.hostname,
        asset.serial_number,
        asset.primary_ip,
        _effective_status(asset, business),
        asset.virtual_physical,
        asset.hypervisor,
        asset.hardware.manufacturer,
        asset.hardware.model,
        asset.hardware.cpu_model,
        asset.hardware.cpu_count,
        asset.hardware.cpu_cores,
        asset.hardware.cpu_threads,
        asset.hardware.ram_gb,
        asset.os.distribution,
        asset.os.version,
        asset.os.kernel,
        asset.os.architecture,
        asset.os.uptime_seconds,
        business.support_team if business else None,
        business.asset_owner if business else None,
        business.application_name if business else None,
        business.business_service if business else None,
        business.environment if business else None,
        business.site if business else None,
        business.rack_number if business else None,
        business.technology if business else None,
        business.hw_support_expiry if business else None,
        business.os_support_expiry if business else None,
        asset.first_seen,
        asset.last_seen,
        asset.last_collection,
    ]


@router.get("/export.csv")
async def export_assets_csv(
    search: Optional[str] = None,
    technology: Optional[str] = None,
    environment: Optional[str] = None,
    status: Optional[str] = None,
    site: Optional[str] = None,
    os_distribution: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    """Full inventory detail for every matching server - hardware, OS,
    and business metadata in one row per asset - not just the summary
    columns shown in the Inventory table."""
    assets, _ = await uow.assets.list(
        search=search,
        technology=technology,
        environment=environment,
        status=status,
        site=site,
        os_distribution=os_distribution,
        manufacturer=manufacturer,
        model=model,
        offset=0,
        limit=100000,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_CSV_COLUMNS)
    for asset in assets:
        business = await uow.business_metadata.get_by_asset_id(asset.asset_id)
        writer.writerow(_full_export_row(asset, business))
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=asset_inventory.csv"},
    )


@router.get("/field-options", response_model=FieldOptionsOut)
async def get_field_options(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    """Existing values for the dropdown-with-add-new fields (Support Team,
    Asset Owner, Site, Technology, Environment), so the frontend can offer
    them as suggestions while still allowing a brand-new value to be typed
    and saved. Technology's built-in suggestion list is merged in so the
    dropdown isn't empty before anyone has picked a custom value.

    Site is merged with the Sites directory (uow.sites) as well as the
    distinct values already in use on assets: `field_options()` alone only
    sees values some asset has actually been assigned, so a site added on
    the Sites page wouldn't show up here - and therefore not in this
    dropdown - until an asset used it once."""
    options = await uow.business_metadata.field_options()
    sites = await uow.sites.list()
    merged_technology = sorted(set(options.get("technology", [])) | {t.value for t in Technology})
    merged_sites = sorted(set(options.get("site", [])) | {s.name for s in sites})
    return FieldOptionsOut(
        support_team=options.get("support_team", []),
        asset_owner=options.get("asset_owner", []),
        site=merged_sites,
        technology=merged_technology,
        environment=options.get("environment", []),
    )


@router.get("/hardware-options", response_model=HardwareOptionsOut)
async def get_hardware_options(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    """Distinct Manufacturer/Model values currently in the inventory, for
    the Inventory page's filter dropdowns."""
    options = await uow.assets.distinct_hardware_values()
    return HardwareOptionsOut(
        manufacturer=options.get("manufacturer", []),
        model=options.get("model", []),
    )


@router.put("/bulk-business", response_model=BulkUpdateResult)
async def bulk_update_business_metadata(
    updates: BulkBusinessMetadataUpdate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    """Applies the same set of business-metadata field changes to many
    assets at once (Inventory page bulk edit). Fields left unset on the
    payload are left untouched on every asset; only asset_ids is required."""
    if not updates.asset_ids:
        raise HTTPException(status_code=400, detail="asset_ids must not be empty")

    field_updates = updates.to_update_dict()
    service = AssetBusinessService(uow)
    updated_ids: list[int] = []
    try:
        for asset_id in updates.asset_ids:
            await service.upsert(asset_id, field_updates)
            updated_ids.append(asset_id)
        await uow.commit()
    except AssetNotFoundError as exc:
        await uow.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return BulkUpdateResult(updated=len(updated_ids), asset_ids=updated_ids)


@router.get("/{asset_id}", response_model=AssetDetailOut)
async def get_asset(
    asset_id: int,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    asset = await uow.assets.get_by_id(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    business = await uow.business_metadata.get_by_asset_id(asset_id)

    return AssetDetailOut(
        asset_id=asset.asset_id,
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
        storage=[StorageOut.model_validate(s, from_attributes=True) for s in asset.storage],
        network=[NetworkOut.model_validate(n, from_attributes=True) for n in asset.network],
        business=(
            BusinessMetadataOut(
                asset_owner=business.asset_owner,
                support_team=business.support_team,
                application_name=business.application_name,
                business_service=business.business_service,
                environment=business.environment,
                site=business.site,
                rack_number=business.rack_number,
                technology=business.technology,
                hw_support_expiry=business.hw_support_expiry,
                os_support_expiry=business.os_support_expiry,
                status=_effective_status(asset, business),
            )
            if business
            else None
        ),
    )


@router.put("/{asset_id}/business", response_model=BusinessMetadataOut)
async def update_business_metadata(
    asset_id: int,
    updates: BusinessMetadataUpdate,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.EDITOR)),
):
    service = AssetBusinessService(uow)
    try:
        saved = await service.upsert(asset_id, updates.to_update_dict())
        await uow.commit()
    except AssetNotFoundError as exc:
        await uow.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return BusinessMetadataOut(
        asset_owner=saved.asset_owner,
        support_team=saved.support_team,
        application_name=saved.application_name,
        business_service=saved.business_service,
        environment=saved.environment,
        site=saved.site,
        rack_number=saved.rack_number,
        technology=saved.technology,
        hw_support_expiry=saved.hw_support_expiry,
        os_support_expiry=saved.os_support_expiry,
        status=saved.status,
    )
