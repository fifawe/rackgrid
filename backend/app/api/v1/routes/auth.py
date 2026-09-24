"""Local-account JWT authentication (Phase 1 security model)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_uow, require_role
from app.api.v1.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.application.services.auth_service import AuthService
from app.domain.exceptions.errors import AuthenticationError
from app.domain.value_objects.enums import UserRole
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.security.jwt_handler import JwtTokenIssuer
from app.infrastructure.security.password_hasher import BcryptPasswordHasher

router = APIRouter(prefix="/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, uow: SqlAlchemyUnitOfWork = Depends(get_uow)):
    service = AuthService(uow.users, BcryptPasswordHasher(), JwtTokenIssuer())
    try:
        token = await service.authenticate(body.username, body.password)
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return TokenResponse(access_token=token)


@router.put("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
    user=Depends(require_role(UserRole.VIEWER)),
):
    """Lets the currently-logged-in user (any role) change their own
    password. Requires the correct current password."""
    hasher = BcryptPasswordHasher()
    account = await uow.users.get_by_username(user.username)
    if account is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not hasher.verify(body.current_password, account.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(body.new_password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"New password must be at least {MIN_PASSWORD_LENGTH} characters",
        )
    await uow.users.update_password(user.username, hasher.hash(body.new_password))
    await uow.commit()
