"""ORM model for collector_runs - one row per discovery execution."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class CollectorRunModel(Base):
    __tablename__ = "collector_runs"

    run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RUNNING")

    assets_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    trigger_source: Mapped[str] = mapped_column(String(30), nullable=False)
