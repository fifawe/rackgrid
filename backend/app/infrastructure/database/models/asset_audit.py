"""ORM model for asset_audit - change-only history. No snapshots."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class AssetAuditModel(Base):
    __tablename__ = "asset_audit"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"), index=True
    )
    collector_run_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("collector_runs.run_id", ondelete="SET NULL"), nullable=True, index=True
    )

    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    change_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="discovery")
