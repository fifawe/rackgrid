"""add sites table and asset_business.rack_number

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("site_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=True),
        sa.Column("city", sa.String(255), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_sites_name", "sites", ["name"], unique=True)

    op.add_column("asset_business", sa.Column("rack_number", sa.String(50), nullable=True))

    # Backfill: any site name already in use on an asset (free-text,
    # pre-existing this table) becomes a real site row too, so it shows
    # up on the new Sites page and in the dropdown immediately rather
    # than only after someone re-types it.
    conn = op.get_bind()
    existing_site_names = conn.execute(
        sa.text("SELECT DISTINCT site FROM asset_business WHERE site IS NOT NULL AND site != ''")
    ).scalars().all()
    if existing_site_names:
        sites_table = sa.table("sites", sa.column("name", sa.String))
        op.bulk_insert(sites_table, [{"name": name} for name in existing_site_names])


def downgrade() -> None:
    op.drop_column("asset_business", "rack_number")
    op.drop_index("ix_sites_name", table_name="sites")
    op.drop_table("sites")
