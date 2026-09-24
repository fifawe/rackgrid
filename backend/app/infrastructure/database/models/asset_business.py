"""ORM model for asset_business - manually managed metadata.

Never written to by the discovery/collector pipeline.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class AssetBusinessModel(Base):
    __tablename__ = "asset_business"

    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"), primary_key=True
    )

    asset_owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    support_team: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    application_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    business_service: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    environment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    site: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rack_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    technology: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    hw_support_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    os_support_expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Active")

    asset: Mapped["InventoryAssetModel"] = relationship(back_populates="business")
