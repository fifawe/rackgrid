"""Shared FastAPI dependencies: DB session/UoW wiring and JWT auth."""
from __future__ import annotations

from typing import AsyncIterator, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.value_objects.enums import UserRole
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_session
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.scheduling.scheduler_client import HttpSchedulerAdapter
from app.infrastructure.security.jwt_handler import JwtTokenIssuer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_ROLE_RANK = {
    UserRole.VIEWER.value: 0,
    UserRole.EDITOR.value: 1,
    UserRole.ADMIN.value: 2,
}


async def get_uow(session: AsyncSession = Depends(get_session)) -> AsyncIterator[SqlAlchemyUnitOfWork]:
    yield SqlAlchemyUnitOfWork(session)


def get_scheduler_client() -> HttpSchedulerAdapter:
    return HttpSchedulerAdapter()


class CurrentUser:
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> CurrentUser:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = JwtTokenIssuer().decode(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    username = payload.get("sub")
    role = payload.get("role", UserRole.VIEWER.value)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return CurrentUser(username=username, role=role)


def require_role(minimum_role: UserRole):
    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if _ROLE_RANK.get(user.role, -1) < _ROLE_RANK[minimum_role.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {minimum_role.value}",
            )
        return user

    return _checker


async def verify_collector_api_key(x_collector_api_key: Optional[str] = Header(default=None)) -> None:
    """Machine-to-machine auth for the discovery ingestion endpoint - the
    Ansible submit_payload role presents this shared secret rather than a
    user JWT."""
    settings = get_settings()
    if not x_collector_api_key or x_collector_api_key != settings.collector_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid collector API key")
