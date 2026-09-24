"""Dashboard summary endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.dashboard import DashboardSummaryOut
from app.application.services.dashboard_service import DashboardService
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryOut)
async def dashboard_summary(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    _user=Depends(require_role(UserRole.VIEWER)),
):
    service = DashboardService(uow)
    data = await service.summary()
    return DashboardSummaryOut(**data)
