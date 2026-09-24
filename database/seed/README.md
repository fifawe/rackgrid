# Seed Data

Seed data is applied as part of the Alembic migration chain
(`backend/alembic/versions/0002_seed_data.py`), so it runs automatically
with `alembic upgrade head` / on container startup - no separate step is
required.

It creates:

- A default `system_settings` row set (lifecycle thresholds, collector
  version, default cron schedule).
- A default local admin account:
  - username: `admin`
  - password: `ChangeMe123!`

**Change this password immediately after first login** - it is committed
to source control for MVP convenience only and must not be used in a
real deployment.
