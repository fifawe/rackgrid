"""Authentication service - verifies local account credentials and mints
JWTs. Password hashing / JWT encode-decode are infrastructure concerns
injected via small ports to keep this layer testable."""
from __future__ import annotations

from typing import Optional, Protocol

from app.application.interfaces.repositories import UserRepository
from app.domain.exceptions.errors import AuthenticationError


class PasswordHasher(Protocol):
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        ...


class TokenIssuer(Protocol):
    def issue(self, subject: str, role: str) -> str:
        ...


class AuthService:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenIssuer):
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    async def authenticate(self, username: str, password: str) -> str:
        user = await self._users.get_by_username(username)
        if user is None or not self._hasher.verify(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        return self._tokens.issue(subject=user.username, role=user.role)
