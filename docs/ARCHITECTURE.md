# Architecture

## Containers

| Service     | Image                  | Purpose                                                   |
|-------------|-------------------------|------------------------------------------------------------|
| `mariadb`   | `mariadb:11.4`           | Persistent storage for all 9 tables                         |
| `backend`   | built from `backend/`    | FastAPI REST API; runs Alembic migrations on startup         |
| `scheduler` | built from `backend/` (same image, `scheduler_main:app`) | APScheduler cron + Run Now/schedule HTTP control |
| `collector` | built from `collector/`  | Ansible control node + `/run` trigger agent (FastAPI)         |
| `frontend`  | built from `frontend/`   | React SPA served by nginx, proxies `/api` to `backend`        |

`backend` and `scheduler` share one Docker image (same codebase, Clean
Architecture layers are fully reused) but run different entrypoints -
this keeps the "5 services" from the spec without duplicating code.

## Request Flow (Discovery)

```
Cron (scheduler) or "Run Now" click (dashboard -> backend -> scheduler)
  -> scheduler creates a collector_runs row (status=RUNNING)
  -> scheduler POSTs /run to the collector agent
  -> collector agent runs `ansible-playbook` against inventory/hosts.ini
       for each host:
         gather_hardware / gather_os / gather_network / gather_storage
         -> build_payload assembles the JSON payload
         -> submit_payload POSTs it to backend's /api/v1/discovery
              (X-Collector-Api-Key header, not a user JWT)
  -> backend's DiscoveryService, per host:
       1. AssetMatchingService finds the existing asset
          (Serial Number -> Primary IP -> Hostname priority)
       2. AuditService diffs old vs new collector-owned field values
       3. Only changed fields are written to asset_audit (no snapshots)
       4. inventory_assets / inventory_storage / inventory_network are
          upserted; last_seen and last_collection are stamped
       5. asset_business is left completely untouched
  -> scheduler marks the collector_runs row finished (status/counts)
```

## Clean Architecture (backend)

```
app/
  domain/          Entities, value objects, exceptions - no framework
                    imports, no SQLAlchemy, no FastAPI.
  application/      Services (AssetMatchingService, AuditService,
                    DiscoveryService, DashboardService, JobService,
                    AuthService) + repository/UnitOfWork interfaces
                    (ABCs) the domain/application layers depend on.
  infrastructure/    SQLAlchemy models + repositories implementing
                    those interfaces, Alembic, JWT/bcrypt, APScheduler,
                    structured logging, Settings.
  api/              FastAPI routers + Pydantic schemas + auth deps.
                    Translates HTTP <-> DTOs <-> domain calls only.
```

Dependencies point inward: `api` depends on `application` and
`infrastructure`; `application` depends only on `domain` and its own
interfaces; `domain` depends on nothing. Swapping MariaDB for another
database means rewriting `infrastructure/database/repositories/*`
without touching `domain` or `application`.

## Business-field protection

`value_objects/enums.py` defines two disjoint sets,
`COLLECTOR_OWNED_FIELDS` and `BUSINESS_OWNED_FIELDS`. `AuditService`
only ever diffs/records fields in the collector-owned set, and
`AssetBusinessService` is the *only* code path that writes
`asset_business` - `DiscoveryService` never touches it. This is also
covered by
`backend/tests/test_discovery_service_integration.py::test_discovery_never_touches_business_metadata`.

## Asset status lifecycle

`Asset.compute_status()` in the domain layer implements:

- **Retired**: manual-only, always wins once set (collector can never
  set it - discovery never passes a status at all).
- **Active**: `last_seen` within `ACTIVE_THRESHOLD_DAYS` (default 7).
- **Offline**: `last_seen` older than `OFFLINE_THRESHOLD_DAYS` (default
  30), or never seen.

## Security (Phase 1)

Local accounts + JWT (`python-jose`), passwords hashed with `bcrypt`
directly (not `passlib`, which doesn't work with modern bcrypt - see
comment in `password_hasher.py`). Three roles, enforced via FastAPI
dependency (`require_role`): Viewer (read-only), Editor (can update
business metadata, trigger runs), Admin (also can change the
schedule). The discovery ingestion endpoint uses a separate shared-secret
header (`X-Collector-Api-Key`) instead of a user JWT, since it's a
machine-to-machine call from the collector, not a logged-in user.
