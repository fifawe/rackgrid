"""add support_teams directory and asset_attachments table

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-23

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "support_teams",
        sa.Column("support_team_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("contact_number", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_support_teams_name", "support_teams", ["name"], unique=True)

    # Backfill: any support_team name already in use on an asset
    # (free-text, pre-existing this table) becomes a real directory row
    # too, so it shows up on the new Support Team page and in the asset
    # dropdown immediately rather than being silently unselectable until
    # someone re-creates it by hand - same rationale as the 0003 Site
    # backfill.
    conn = op.get_bind()
    existing_team_names = (
        conn.execute(
            sa.text("SELECT DISTINCT support_team FROM asset_business WHERE support_team IS NOT NULL AND support_team != ''")
        )
        .scalars()
        .all()
    )
    if existing_team_names:
        support_teams_table = sa.table("support_teams", sa.column("name", sa.String))
        op.bulk_insert(support_teams_table, [{"name": name} for name in existing_team_names])

    op.create_table(
        "asset_attachments",
        sa.Column("attachment_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        # Randomized on-disk filename - never the user-supplied one, to
        # avoid path-traversal and collisions. See
        # infrastructure/storage/local_file_storage.py.
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.String(100), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_asset_attachments_asset_id", "asset_attachments", ["asset_id"])


def downgrade() -> None:
    op.drop_index("ix_asset_attachments_asset_id", table_name="asset_attachments")
    op.drop_table("asset_attachments")
    op.drop_index("ix_support_teams_name", table_name="support_teams")
    op.drop_table("support_teams")
