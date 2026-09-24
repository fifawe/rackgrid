"""ORM model for inventory_storage - mounted storage devices per asset."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class InventoryStorageModel(Base):
    __tablename__ = "inventory_storage"

    storage_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"), index=True
    )

    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    filesystem_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mount_point: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    capacity_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    asset: Mapped["InventoryAssetModel"] = relationship(back_populates="storage")
