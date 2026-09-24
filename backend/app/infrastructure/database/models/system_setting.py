"""ORM model for system_settings - simple key/value config store."""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SystemSettingModel(Base):
    __tablename__ = "system_settings"

    setting_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    setting_value: Mapped[str] = mapped_column(String(255), nullable=False)
