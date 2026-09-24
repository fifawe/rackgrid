"""Discovery ingestion endpoint - the single entry point the Ansible
collector posts to (see collector/roles/submit_payload)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_uow, verify_collector_api_key
from app.api.v1.schemas.discovery import DiscoveryPayloadSchema, DiscoveryResponseSchema
from app.application.dto.discovery_payload import (
    DiscoveryPayloadDTO,
    HardwareDTO,
    NetworkDTO,
    OsDTO,
    StorageDTO,
    VirtualizationDTO,
)
from app.application.services.discovery_service import DiscoveryService
from app.domain.exceptions.errors import DomainError
from app.infrastructure.config.logging import get_logger
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

logger = get_logger(__name__)

router = APIRouter(prefix="/discovery", tags=["discovery"], dependencies=[Depends(verify_collector_api_key)])


def _to_dto(payload: DiscoveryPayloadSchema) -> DiscoveryPayloadDTO:
    return DiscoveryPayloadDTO(
        hostname=payload.hostname,
        serial_number=payload.serial_number,
        primary_ip=payload.primary_ip,
        hardware=HardwareDTO(**payload.hardware.model_dump()),
        os=OsDTO(**payload.os.model_dump()),
        virtualization=VirtualizationDTO(**payload.virtualization.model_dump()),
        storage=[StorageDTO(**s.model_dump()) for s in payload.storage],
        network=[NetworkDTO(**n.model_dump()) for n in payload.network],
        collector_run_id=payload.collector_run_id,
    )


async def _record_run_outcome(uow: SqlAlchemyUnitOfWork, collector_run_id: int, *, success: bool) -> None:
    """Bookkeeping only - records the per-host outcome against the shared
    collector_run row via an atomic increment (see CollectorRunRepository.
    increment_success/increment_failure), in its own transaction so a
    failure here never masks the real ingestion result already returned
    to the caller."""
    try:
        if success:
            await uow.collector_runs.increment_success(collector_run_id)
        else:
            await uow.collector_runs.increment_failure(collector_run_id)
        await uow.commit()
    except Exception:  # pragma: no cover - best-effort bookkeeping only
        logger.error(
            "collector_run_bookkeeping_failed",
            collector_run_id=collector_run_id,
            success=success,
            exc_info=True,
        )
        await uow.rollback()


@router.post("", response_model=DiscoveryResponseSchema)
async def submit_discovery(
    payload: DiscoveryPayloadSchema,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
):
    dto = _to_dto(payload)
    service = DiscoveryService(uow)

    try:
        asset = await service.ingest(dto, collector_run_id=dto.collector_run_id)
        await uow.commit()
    except DomainError as exc:
        await uow.rollback()
        if dto.collector_run_id:
            await _record_run_outcome(uow, dto.collector_run_id, success=False)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception:
        # Anything other than a DomainError is a bug, not a validation
        # problem - the old code here only caught DomainError, so any
        # other exception (a DB error, a race on the collector_run row,
        # etc.) propagated as a bare, unlogged 500 AND skipped the
        # rollback below, leaving the session's failed transaction state
        # to surprise whatever ran next. Log the full traceback (visible
        # via `docker compose logs backend`) and always roll back.
        await uow.rollback()
        logger.error(
            "discovery_ingest_failed",
            hostname=payload.hostname,
            collector_run_id=dto.collector_run_id,
            exc_info=True,
        )
        if dto.collector_run_id:
            await _record_run_outcome(uow, dto.collector_run_id, success=False)
        raise HTTPException(
            status_code=500,
            detail="Discovery ingestion failed unexpectedly - see backend logs for details.",
        )

    if dto.collector_run_id:
        await _record_run_outcome(uow, dto.collector_run_id, success=True)

    created = asset.first_seen == asset.last_seen
    return DiscoveryResponseSchema(asset_id=asset.asset_id, hostname=asset.hostname, created=created)
