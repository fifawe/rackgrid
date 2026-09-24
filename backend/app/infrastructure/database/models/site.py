"""ORM model for sites - the structured, canonical list of physical
locations an asset's `asset_business.site` free-text field can refer to.

`asset_business.site` intentionally stays a free-text column rather than
a foreign key here: it already held whatever text users had typed before
this table existed, and turning it into a hard FK would risk breaking on
values that don't match any row here. The Sites page is the place to
give a site real structure (code, city); the dropdown on an asset just
offers known site names (plus "add new") without enforcing referential
integrity against them.
"""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class SiteModel(Base):
    __tablename__ = "sites"

    site_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
