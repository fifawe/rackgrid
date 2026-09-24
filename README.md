# Linux Asset Inventory Platform

A containerized platform that discovers Linux servers via Ansible,
tracks their current state, records change-only audit history, and
lets you manage business metadata (owner, environment, support dates,
etc.) through a React dashboard.

Built per `PROJECT_SPEC.md` / `05_CLAUDE_CODE_IMPLEMENTATION_PROMPT.md`
in the project's planning docs, following Clean Architecture
(Domain / Application / Infrastructure / API) on the backend.

## Repository Layout

```
asset-inventory/
  backend/      FastAPI + SQLAlchemy (async) + Alembic, Clean Architecture
  frontend/     React + TypeScript + Material UI
  collector/    Ansible roles/playbook + a small HTTP trigger agent
  database/     Seed data notes (seed data itself ships as an Alembic migration)
  deployment/   docker-compose.yml + .env.example
  docs/         Architecture and API notes
```

## Quick Start

```bash
cp deployment/.env.example deployment/.env
# edit deployment/.env: set DB_PASSWORD, DB_ROOT_PASSWORD, SECRET_KEY,
# COLLECTOR_API_KEY to real random values

cd deployment
docker compose up --build
```

- Frontend: http://localhost (nginx, serves the React SPA and proxies `/api`)
- Backend API docs: http://localhost:8000/docs
- Default login: `admin` / `ChangeMe123!` (seeded by the first Alembic
  migration - **change this immediately**, see `database/seed/README.md`)

Database schema is created automatically on backend startup
(`entrypoint.sh` runs `alembic upgrade head` before starting uvicorn).

## Running Discovery

Edit `collector/inventory/hosts.ini` to list your real Linux servers,
then either:

- Click **Run Now** on the Job Management page (requires Editor role or
  above), or
- `POST http://localhost:9000/internal/run` directly, or
- Run the playbook standalone: see `collector/README.md`.

The scheduler container also runs discovery automatically on the cron
schedule in `DEFAULT_COLLECTOR_CRON` (default: daily at 02:00).

## Architecture

See `docs/ARCHITECTURE.md` for the full request flow, the five
containers, and how the discovery/audit pipeline enforces the
"collector owns technical fields, humans own business fields" rule from
the project charter.

## Tests

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

25 tests cover the asset matching engine, the change-only audit engine,
full discovery-to-audit integration (against an in-memory SQLite DB),
and the API layer (auth, RBAC, discovery ingestion, business metadata
protection).

## Verification Performed

This MVP was built and verified in a sandboxed environment without a
Docker daemon available, so the full `docker compose up` stack itself
could not be exercised end-to-end here. What *was* verified directly:

- Backend: full `pip install`, `python -m app.main` / `scheduler_main`
  import cleanly, all 25 pytest tests pass, `py_compile` across the
  whole backend succeeds.
- Frontend: `npm install` + `npm run build` (TypeScript strict mode +
  Vite production build) succeeds with zero errors.
- Collector: all Ansible YAML parses, `ansible-playbook --syntax-check`
  passes, the FastAPI trigger agent imports and its routes resolve.
- `docker compose config` validates the full compose file (env
  interpolation, `depends_on`, healthchecks, networks, volumes).

Before a real deployment, run `docker compose up --build` once against
a real (or test) set of Linux hosts to confirm the images build and the
five containers reach a healthy state together.
