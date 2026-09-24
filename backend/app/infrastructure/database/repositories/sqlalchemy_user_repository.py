"""SQLAlchemy implementation of UserRepository."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repositories import UserRepository
from app.infrastructure.database.models.user import UserModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        return await self._session.get(UserModel, username)

    async def update_password(self, username: str, hashed_password: str) -> None:
        user = await self._session.get(UserModel, username)
        if user is None:
            raise ValueError(f"User {username!r} does not exist")
        user.hashed_password = hashed_password
        await self._session.flush()
