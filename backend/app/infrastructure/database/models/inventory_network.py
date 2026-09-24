"""ORM model for inventory_network - network interfaces per asset."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class InventoryNetworkModel(Base):
    __tablename__ = "inventory_network"

    network_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"), index=True
    )

    interface_name: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    asset: Mapped["InventoryAssetModel"] = relationship(back_populates="network")
