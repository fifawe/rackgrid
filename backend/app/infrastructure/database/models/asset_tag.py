"""ORM model for asset_tags - future extensibility, composite PK."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class AssetTagModel(Base):
    __tablename__ = "asset_tags"

    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(100), primary_key=True)

    asset: Mapped["InventoryAssetModel"] = relationship(back_populates="tags")
