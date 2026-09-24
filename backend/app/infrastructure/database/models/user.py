"""ORM model for local user accounts (Phase 1 auth - see PROJECT_SPEC.md
> Security)."""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), primary_key=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="Viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
