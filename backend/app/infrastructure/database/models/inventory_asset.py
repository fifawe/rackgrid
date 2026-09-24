"""ORM model for inventory_assets - current discovered state of assets."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class InventoryAssetModel(Base):
    __tablename__ = "inventory_assets"

    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    primary_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)

    manufacturer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    cpu_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cpu_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_cores: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_threads: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    ram_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    os_distribution: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    kernel_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    architecture: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    uptime_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    virtual_physical: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hypervisor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    first_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_collection: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    storage: Mapped[List["InventoryStorageModel"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )
    network: Mapped[List["InventoryNetworkModel"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )
    business: Mapped[Optional["AssetBusinessModel"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    tags: Mapped[List["AssetTagModel"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )
