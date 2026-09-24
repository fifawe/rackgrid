"""seed default admin user and system settings

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# bcrypt hash of "ChangeMe123!" - change this password immediately after
# first login in a real deployment.
_DEFAULT_ADMIN_HASH = "$2b$12$ZyLTJQCaM86bDXizNGvZAOU/2RjErO0HWlKQzVYAFbmqY4q0DgJG6"

_SETTINGS = [
    ("active_threshold_days", "7"),
    ("offline_threshold_days", "30"),
    ("collector_version", "1.0.0"),
    ("default_collector_cron", "0 2 * * *"),
]

users_table = sa.table(
    "users",
    sa.column("username", sa.String),
    sa.column("hashed_password", sa.String),
    sa.column("role", sa.String),
    sa.column("is_active", sa.Boolean),
)

settings_table = sa.table(
    "system_settings",
    sa.column("setting_name", sa.String),
    sa.column("setting_value", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        users_table,
        [
            {
                "username": "admin",
                "hashed_password": _DEFAULT_ADMIN_HASH,
                "role": "Admin",
                "is_active": True,
            }
        ],
    )
    op.bulk_insert(
        settings_table,
        [{"setting_name": name, "setting_value": value} for name, value in _SETTINGS],
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE username = 'admin'"))
    conn.execute(
        sa.text(
            "DELETE FROM system_settings WHERE setting_name IN "
            "('active_threshold_days','offline_threshold_days','collector_version','default_collector_cron')"
        )
    )
