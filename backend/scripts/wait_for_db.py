"""Blocks until MariaDB is accepting TCP connections, then exits 0.

Used by the container entrypoint before running Alembic migrations, so
the backend/scheduler containers don't crash-loop racing the database's
startup time.
"""
from __future__ import annotations

import socket
import sys
import time

from app.infrastructure.config.settings import get_settings

MAX_WAIT_SECONDS = 60


def main() -> int:
    settings = get_settings()
    deadline = time.monotonic() + MAX_WAIT_SECONDS

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((settings.db_host, settings.db_port), timeout=3):
                print(f"Database at {settings.db_host}:{settings.db_port} is accepting connections.")
                return 0
        except OSError:
            print(f"Waiting for database at {settings.db_host}:{settings.db_port} ...")
            time.sleep(2)

    print("Timed out waiting for the database.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
