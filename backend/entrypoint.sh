#!/bin/sh
set -e

echo "Waiting for the database..."
python3 -m scripts.wait_for_db

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Applying Alembic migrations..."
    alembic upgrade head
fi

exec "$@"
