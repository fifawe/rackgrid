"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inventory_assets",
        sa.Column("asset_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("serial_number", sa.String(255), nullable=True),
        sa.Column("primary_ip", sa.String(45), nullable=True),
        sa.Column("manufacturer", sa.String(255), nullable=True),
        sa.Column("model", sa.String(255), nullable=True),
        sa.Column("cpu_model", sa.String(255), nullable=True),
        sa.Column("cpu_count", sa.Integer(), nullable=True),
        sa.Column("cpu_cores", sa.Integer(), nullable=True),
        sa.Column("cpu_threads", sa.Integer(), nullable=True),
        sa.Column("ram_gb", sa.Float(), nullable=True),
        sa.Column("os_distribution", sa.String(255), nullable=True),
        sa.Column("os_version", sa.String(100), nullable=True),
        sa.Column("kernel_version", sa.String(100), nullable=True),
        sa.Column("architecture", sa.String(50), nullable=True),
        sa.Column("uptime_seconds", sa.Integer(), nullable=True),
        sa.Column("virtual_physical", sa.String(20), nullable=True),
        sa.Column("hypervisor", sa.String(100), nullable=True),
        sa.Column("first_seen", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("last_collection", sa.DateTime(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_inventory_assets_hostname", "inventory_assets", ["hostname"])
    op.create_index("ix_inventory_assets_serial_number", "inventory_assets", ["serial_number"])
    op.create_index("ix_inventory_assets_primary_ip", "inventory_assets", ["primary_ip"])

    op.create_table(
        "inventory_storage",
        sa.Column("storage_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_name", sa.String(255), nullable=False),
        sa.Column("filesystem_type", sa.String(50), nullable=True),
        sa.Column("mount_point", sa.String(255), nullable=True),
        sa.Column("capacity_gb", sa.Float(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_inventory_storage_asset_id", "inventory_storage", ["asset_id"])

    op.create_table(
        "inventory_network",
        sa.Column("network_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("interface_name", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_inventory_network_asset_id", "inventory_network", ["asset_id"])

    op.create_table(
        "asset_business",
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("asset_owner", sa.String(255), nullable=True),
        sa.Column("support_team", sa.String(255), nullable=True),
        sa.Column("application_name", sa.String(255), nullable=True),
        sa.Column("business_service", sa.String(255), nullable=True),
        sa.Column("environment", sa.String(50), nullable=True),
        sa.Column("site", sa.String(100), nullable=True),
        sa.Column("technology", sa.String(50), nullable=True),
        sa.Column("hw_support_expiry", sa.Date(), nullable=True),
        sa.Column("os_support_expiry", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Active"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "asset_tags",
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("tag", sa.String(100), primary_key=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "collector_runs",
        sa.Column("run_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="RUNNING"),
        sa.Column("assets_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger_source", sa.String(30), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "asset_audit",
        sa.Column("audit_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "asset_id",
            sa.Integer(),
            sa.ForeignKey("inventory_assets.asset_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "collector_run_id",
            sa.Integer(),
            sa.ForeignKey("collector_runs.run_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("change_timestamp", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="discovery"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_asset_audit_asset_id", "asset_audit", ["asset_id"])
    op.create_index("ix_asset_audit_collector_run_id", "asset_audit", ["collector_run_id"])
    op.create_index("ix_asset_audit_field_name", "asset_audit", ["field_name"])
    op.create_index("ix_asset_audit_change_timestamp", "asset_audit", ["change_timestamp"])

    op.create_table(
        "system_settings",
        sa.Column("setting_name", sa.String(100), primary_key=True),
        sa.Column("setting_value", sa.String(255), nullable=False),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "users",
        sa.Column("username", sa.String(100), primary_key=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="Viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("system_settings")
    op.drop_index("ix_asset_audit_change_timestamp", table_name="asset_audit")
    op.drop_index("ix_asset_audit_field_name", table_name="asset_audit")
    op.drop_index("ix_asset_audit_collector_run_id", table_name="asset_audit")
    op.drop_index("ix_asset_audit_asset_id", table_name="asset_audit")
    op.drop_table("asset_audit")
    op.drop_table("collector_runs")
    op.drop_table("asset_tags")
    op.drop_table("asset_business")
    op.drop_index("ix_inventory_network_asset_id", table_name="inventory_network")
    op.drop_table("inventory_network")
    op.drop_index("ix_inventory_storage_asset_id", table_name="inventory_storage")
    op.drop_table("inventory_storage")
    op.drop_index("ix_inventory_assets_primary_ip", table_name="inventory_assets")
    op.drop_index("ix_inventory_assets_serial_number", table_name="inventory_assets")
    op.drop_index("ix_inventory_assets_hostname", table_name="inventory_assets")
    op.drop_table("inventory_assets")
