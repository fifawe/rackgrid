# REST API Reference

Full interactive docs are always available at `/docs` (Swagger UI) and
`/redoc` on the running backend. This is a quick reference matching
PROJECT_SPEC.md > REST API.

All endpoints are prefixed with `/api/v1`. Except `/health`,
`/auth/login` and `/discovery` (which uses `X-Collector-Api-Key`
instead), every endpoint requires `Authorization: Bearer <JWT>`.

| Method | Path                        | Role required | Notes                                   |
|--------|------------------------------|----------------|-------------------------------------------|
| GET    | `/health`                    | none           | Liveness check                            |
| POST   | `/auth/login`                 | none           | `{username, password}` -> JWT             |
| POST   | `/discovery`                  | collector key  | Ingest a discovery payload                |
| GET    | `/assets`                     | Viewer         | Search/filter/sort/paginate (incl. `os_distribution`/`manufacturer`/`model`, `__none__` sentinel) |
| GET    | `/assets/export.csv`           | Viewer         | Same filters, CSV download                |
| GET    | `/assets/{id}`                 | Viewer         | Full detail incl. storage/network/business |
| PUT    | `/assets/{id}/business`        | Editor         | Update business metadata only             |
| PUT    | `/assets/bulk-business`        | Editor         | Apply the same field changes to many assets |
| GET    | `/assets/field-options`        | Viewer         | Existing values for the "add new" dropdown fields |
| GET    | `/assets/hardware-options`     | Viewer         | Distinct Manufacturer/Model values, for the Inventory filters |
| GET    | `/assets/{id}/attachments`     | Viewer         | List design-document attachments           |
| POST   | `/assets/{id}/attachments`     | Editor         | Upload a design document (multipart)       |
| GET    | `/assets/{id}/attachments/{attachment_id}/download` | Viewer | Download an attachment            |
| DELETE | `/assets/{id}/attachments/{attachment_id}`          | Editor | Delete an attachment              |
| GET    | `/audit`                       | Viewer         | Filter by asset/field/date range           |
| GET    | `/audit/{asset_id}`            | Viewer         | Audit history for one asset                |
| GET    | `/dashboard/summary`           | Viewer         | Counts + by-technology/site/environment/os/manufacturer/model |
| GET    | `/jobs`                        | Viewer         | Scheduled jobs + next run time             |
| POST   | `/jobs/run`                     | Editor         | Trigger a collection run now               |
| POST   | `/jobs/schedule`                | Admin          | Update the cron schedule                   |
| GET    | `/jobs/history`                 | Viewer         | Past collector runs                        |
| GET/POST/PUT/DELETE | `/sites`         | Viewer/Editor/Admin | Site directory CRUD                  |
| GET/POST/PUT/DELETE | `/support-teams` | Viewer/Editor/Admin | Support Team directory CRUD          |
| GET    | `/settings/public`             | none           | Platform title, logo URL, version          |
| GET    | `/settings/logo`               | none           | Streams the uploaded logo image            |
| PUT    | `/settings/title`               | Admin          | Update the platform title                  |
| POST   | `/settings/logo`                | Admin          | Upload/replace the platform logo           |
| DELETE | `/settings/logo`                | Admin          | Remove the platform logo                   |
| PUT    | `/auth/change-password`         | Viewer         | Change your own password (any role)        |
| GET    | `/data/export`                  | Viewer         | ZIP bundle: full inventory.csv + audit_log.csv |
| POST   | `/data/import`                  | Editor         | Create/update assets from a CSV (see below) |

## Discovery payload

See `PROJECT_SPEC.md` for the full JSON shape (also mirrored exactly by
`backend/app/api/v1/schemas/discovery.py` and
`collector/roles/build_payload`).

## Inventory Import (`POST /data/import`)

Accepts a multipart CSV upload built to the same column schema
`GET /assets/export.csv` (and the export bundle's `inventory.csv`)
write, so export -> edit in a spreadsheet -> re-import works without any
reformatting. See `backend/app/application/services/inventory_import_service.py`
for the full behavior; in short:

- A row is matched to an existing asset using the same priority the
  collector uses (Serial Number, then Primary IP, then Hostname). No
  match creates a **new** asset from the row.
- A matched row may overwrite that asset's hardware/OS fields as well
  as its business metadata - not restricted to business fields.
- A **blank cell on a matched row leaves the existing value
  unchanged** rather than clearing it; on a newly created asset a
  blank cell is simply not set. Neither `storage` nor `network` device
  data is touched by Import.
- Hardware/OS field changes are audited (`source="import"`); business
  metadata changes are never audited anywhere in this app, and Import
  doesn't change that.
- Each row is validated and committed independently, so one invalid
  row (reported in the response's `errors` list, 1-indexed against the
  file including the header row) never rolls back rows already
  applied from the same file.
