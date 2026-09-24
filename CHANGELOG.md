# Changelog

## Unreleased

**Project renamed to RackGrid.** The platform's default title (shown in the
sidebar and on the login page until an admin customizes it in Settings), the
API/scheduler/collector service titles, and the frontend package name all
changed from "Asset Inventory Platform" to "RackGrid" ahead of the public
GitHub release. No functional or API changes - `platform_title` remains
admin-editable via the same `/settings/title` endpoint for anyone who wants
a different name.

## 1.9.0 - 2026-09-23

New reporting, data-migration, and account-management features requested
after using 1.8.0:

**New: Manufacturer/Model dashboard charts + Inventory filters.** The
Dashboard gains two new charts - **By Manufacturer** (clickable pie,
same pattern as By Technology) and **By Model** (clickable bar chart).
Model can have far higher cardinality than the dashboard's other
dimensions, so the backend collapses everything past the 9 most common
models into a non-clickable "Other" bucket
(`SqlAlchemyAssetRepository._top_n_with_other()`) - clicking a real
model bar still navigates to a pre-filtered Inventory list, same as
every other dashboard chart. The Inventory page gets matching
Manufacturer/Model filter dropdowns, sourced from a new
`GET /assets/hardware-options` endpoint (distinct values currently in
the inventory), and `GET /assets`/`GET /assets/export.csv` both accept
new `manufacturer`/`model` query params (including the `__none__`
sentinel, same convention as `os_distribution`).

**New: Import/Export.** A new **Import / Export** page (`/data`) lets
you download a ZIP bundle of the full inventory
(`GET /api/v1/data/export`: `inventory.csv` + the complete
`audit_log.csv`) and bulk create/update assets by uploading a CSV built
to that same column schema (`POST /api/v1/data/import`, Editor role).
Two import-behavior questions were decided explicitly rather than
defaulted to the safer option:

- A row whose identifiers don't match any existing asset **creates a
  new asset** (matched using the same Serial Number -> Primary IP ->
  Hostname priority the collector uses), rather than being rejected as
  an error.
- A matched row **may overwrite that asset's hardware/OS fields**
  (Manufacturer, Model, CPU, RAM, OS, etc.), not just business
  metadata.

To keep a sparse or partially-filled CSV from silently wiping out real
data, a **blank cell on a matched row leaves the existing value
unchanged** rather than clearing it (mirroring the existing Bulk Edit
convention) - only cells you actually fill in are written. Hardware/OS
field changes made via Import are recorded in the audit log with
`source="import"`, the same as a real collector run; storage/network
device rows are never touched by Import. Every row is validated and
committed independently, so one bad row (reported with its line number
and reason) never blocks the rest of the file. See
`backend/app/application/services/inventory_import_service.py` and
`docs/API.md` for the full details.

**New: self-service change password.** Any logged-in user (any role)
can change their own password from the new **My Account** section of
the Settings page (`PUT /api/v1/auth/change-password`, requiring the
correct current password and an 8+ character new password).

**New: dark mode.** A theme toggle in the Settings page's new
**Appearance** section switches the whole app between light and dark
palettes, remembered per-device via `localStorage` (it's a personal UI
preference, not shared state, so it isn't synced through the backend).

**Changed: Settings is no longer Admin-only.** The Settings page is now
reachable by every role and is split into **My Account** (change
password), **Appearance** (dark mode) - both available to everyone -
and **Platform Branding** (title/logo), which stays Admin-only and is
simply hidden from that page for non-Admins rather than gating the
whole page.

## 1.8.0 - 2026-09-23

New administration and asset-documentation features requested after using 1.7.0:

**New: running version number on the Dashboard.** A small "vX.Y.Z" caption now
sits next to the Dashboard's page title, sourced from the same new
`GET /api/v1/settings/public` endpoint that drives the platform title/logo
below - no more needing to check the zip filename to know what's deployed.

**New: platform title and logo customization.** A new Admin-only **Settings**
page (`/settings`, linked from the sidebar only for Admins) lets you rename
the platform from the default "Asset Inventory Platform" and upload a logo
(PNG/JPG/SVG, up to 5 MB) - both are shown immediately in the sidebar header
and on the login page, site-wide, not just for the admin who set them.
Backed by the existing `system_settings` key/value store plus a new local
file-storage helper (`infrastructure/storage/local_file_storage.py`) that
writes uploads under a configurable `UPLOAD_DIR` (mounted as a Docker volume
so they survive a container recreate); `GET /settings/public` and
`GET /settings/logo` intentionally require no auth, since the login page
needs the branding before anyone is signed in and neither is sensitive.

**New: design-document attachments on assets.** Every asset's detail page
has a new **Attachments** tab for uploading reference files against it -
diagrams, spec sheets, vendor quotes - with no limit on how many an asset
can hold. Accepted types are PDF, DOCX, XLSX, PNG and JPG (validated by
extension server-side, not just in the file picker), capped at 25 MB per
file. Files are listed with size/uploader/timestamp, and can be downloaded
or deleted. New `asset_attachments` table and
`GET/POST /assets/{id}/attachments`,
`GET /assets/{id}/attachments/{id}/download`,
`DELETE /assets/{id}/attachments/{id}` endpoints; the actual bytes live on
local disk via the same storage helper the logo uses.

**New: Support Team directory + strict dropdown.** A new **Support Team**
page (`/support-teams`, mirroring the existing Sites page) manages a real
directory of support teams - Name, Contact Number, Email, Location, Notes -
instead of the free-typed text that previously lived directly on each
asset. The asset edit page's and Bulk Edit dialog's Support Team field is
now a fixed dropdown sourced from this directory (no more typos creating a
new "team" by accident), matching the same fixed-dropdown treatment
Environment got in 1.7.0. New `support_teams` table, backfilled from every
distinct `support_team` value already in use (same approach as the 1.5.0
Sites backfill), and `/api/v1/support-teams` CRUD endpoints.

**Asset Details page: visual refresh.** Each tab (Hardware, Operating
System, Storage, Network, Business Metadata, the new Attachments tab, Audit
History) now has its own icon in the tab bar and a consistent icon+title
header atop its content, matching the header style already used on the
Sites page - previously the tabs were bare labels with no visual anchor
once you were inside one.

New Alembic migration `0004` adds `support_teams` and `asset_attachments`.
10 new backend tests (67 total, all passing) cover Support Team CRUD and
uniqueness, assigning a directory team to an asset, attachment
upload/list/download/delete, multiple attachments per asset, rejecting a
disallowed file type and an oversized upload, and the settings
public/title/logo endpoints including logo replacement. Frontend
type-checks and builds clean.

**Deployment note:** this release adds a `backend_uploads` Docker volume
(`deployment/docker-compose.yml`) so attachment and logo files survive a
`docker compose up` recreate - run `docker compose up -d` after pulling to
pick it up. Run `alembic upgrade head` (or let the backend's normal startup
migration step handle it) before starting on an existing database.

## 1.7.0 - 2026-09-23

Follow-up fixes and dashboard interactivity reported after using 1.6.0:

**Collector image now includes `vim` and `less`.** The collector
container's Dockerfile only had `curl` for anything resembling an
in-container text/file tool, which made ad-hoc troubleshooting on the
collector host awkward. Added `vim` and `less` to the `apt-get install`
list alongside the existing packages.

**Environment field on the asset edit page is a fixed dropdown again
(fixed).** 1.5.0 moved every "dropdown with option to add new" field,
Environment included, onto `FieldAutocomplete` (MUI's `freeSolo`
Autocomplete), so Environment could accidentally be saved as an
arbitrary typo'd value instead of one of the five real environments.
The Asset Details page's Business Metadata tab and the Inventory page's
Bulk Edit dialog both now use a plain `Select` constrained to
`ENVIRONMENT_OPTIONS` (`Production` / `Staging` / `Development` / `DR`
/ `Test` - a new shared export in `frontend/src/types/index.ts`,
mirroring the existing `TECHNOLOGY_OPTIONS` pattern), matching the
Inventory page's filter bar, which was already a fixed dropdown and is
now sourced from the same constant instead of its own local copy.

**Dashboard's By Site / By Environment charts showed a blank,
unlabeled bar for hosts with no value set (fixed).** Root cause: these
charts excluded `NULL` site/environment values with a SQL
`.is_not(None)` filter, but *clearing* the field via the edit form
saves an empty string `""`, not `NULL` - `BusinessMetadataUpdate`
only ever drops `None` fields from an update, so `""` reaches the
database and survives the `.is_not(None)` filter, showing up as an
extra bar with no visible label. Both cases (never set at all, or
cleared back to blank) now merge into a single, clearly-labeled "Un
Defined" bucket via a new `_bucket_undefined()` helper in
`SqlAlchemyAssetRepository`, so every host is represented on the chart
and it's obvious at a glance how many still need Site/Environment
filled in. (Technology and OS Family are unaffected - Technology still
excludes untagged hosts since there's a large pre-existing "not yet
tagged" population there by design, and OS Family already had its own
"Unknown" bucket for hosts with no OS recorded.)

**Dashboard's By Technology and By OS Family pie charts are now
clickable.** Clicking a slice navigates to the Inventory page
pre-filtered to that category, e.g. clicking "Database" on the
Technology chart opens Inventory filtered to `technology=Database`.
The OS Family chart's "Unknown" slice (hosts with no OS recorded)
filters via a new `__none__` sentinel value
(`os_distribution=__none__`) rather than the literal string "Unknown",
since there's no real database value meaning "no OS" - the backend
translates that sentinel into an `IS NULL OR = ''` condition. This
required adding `os_distribution` as a new, previously-unsupported
filter on `GET /api/v1/assets` and `GET /api/v1/assets/export.csv`
(threaded through the `AssetRepository.list()` interface and its
SQLAlchemy implementation), and the Inventory page now reads its
initial Technology/OS filter from the URL's query string
(`useSearchParams`) so a link from the dashboard lands pre-filtered;
since there's no permanent OS-filter dropdown control on that page (
unlike Technology, which already has one), an active OS filter now
shows as a small removable chip above the results table.

3 new backend tests (57 total, all passing) cover the "Un Defined"
bucketing (both the never-set and cleared-to-empty-string cases, for
both Site and Environment) and the new `os_distribution` filter
(a literal value, and the `__none__` sentinel). Frontend type-checks
and builds clean.

No database migration in this release.

## 1.6.0 - 2026-09-23

Follow-up fixes and dashboard additions reported after using 1.5.0:

**Timestamps shown in UTC instead of local time (fixed).** Every
timestamp the API returned (Job Management's run history, an asset's
first/last seen, audit history) was a naive datetime with no timezone
marker in its JSON - e.g. `"2026-09-23T02:15:30"` with no `Z` or
offset. Browsers treat a timezone-less ISO datetime string as already
being in the *viewer's own* local time, so the raw UTC wall-clock value
was displayed unconverted and mislabeled as local. Root cause:
`datetime.utcnow()` throughout the backend produces naive datetimes,
and MySQL `DATETIME` columns don't store timezone info either, so
values came back from the DB naive and stayed that way all the way to
the JSON response. Fixed at the single point where every DB-read
datetime becomes a domain object -
`backend/app/infrastructure/database/repositories/mappers.py` now has a
`_utc()` helper that attaches UTC tzinfo before constructing
`Asset`/`AuditRecord`/`CollectorRun` entities, so Pydantic's default
JSON encoding includes an explicit `+00:00` offset and the browser's
`Date`/`toLocaleString()` (already used everywhere in the frontend)
converts to the viewer's actual local time correctly. Also fixed a
resulting `Asset.compute_status()` crash (`can't subtract
offset-naive and offset-aware datetimes`) by normalizing both sides of
that comparison regardless of which one happens to carry tzinfo.

**Site dropdown didn't see newly-added sites (fixed).** `GET
/api/v1/assets/field-options` built its Site suggestion list purely
from `SELECT DISTINCT site FROM asset_business` - i.e. only sites some
asset had already been assigned. A site added on the new Sites page
was invisible in the Asset Details dropdown until an asset happened to
use its exact name. The endpoint now also merges in every name from
the Sites directory (`uow.sites.list()`), so a new site shows up as a
suggestion immediately.

**New: By OS Family chart.** A fourth dashboard chart (grouped by
`os_distribution`, same aggregation style as the existing Technology/
Site/Environment charts) shows the OS mix across the fleet.

**New: support-expiry alert.** The dashboard now flags any asset whose
hardware or OS support expiry is 60 days away or sooner (including
already-expired) with a warning banner listing each affected host,
which field is expiring, and a countdown - click a chip to jump to
that asset. The 60-day window is configurable via
`support_expiry_alert_days` in backend settings. Backed by a new
`_expiring_support()` query in `SqlAlchemyAssetRepository` and two new
fields on `GET /api/v1/dashboard/summary`
(`expiring_support_count`, `expiring_support`).

6 new backend tests (54 total, all passing) cover the UTC-offset fix
across asset/run-history/audit timestamps, the Sites-directory merge
into field-options, the OS family breakdown, and the expiry alert
(soon-expiring, already-expired, and out-of-window cases, plus
soonest-first sort order). Frontend type-checks and builds clean.

No database migration in this release.

## 1.5.0 - 2026-09-23

Dashboard enhancement release, built on top of the working 1.4.0
collection/dashboard baseline. No bug fixes in this release - all new
features, requested as a batch:

**Modern dashboard styling.** New MUI theme (`frontend/src/main.tsx`):
indigo/teal palette, Inter font, rounded cards, softer shadows, styled
table headers/rows. `Layout.tsx` got a cleaner white app bar with an
avatar + role chip and a pill-style active nav item. `DashboardPage.tsx`
stat cards now carry an icon and accent color per metric, and the three
charts sit in a shared `ChartCard` with subtitles and a grid backdrop.

**Dropdown-with-add-new fields.** Support Team, Asset Owner, Site,
Technology, and Environment on the Asset Details "Business Metadata" tab
are now a `FieldAutocomplete` (MUI `Autocomplete` in `freeSolo` mode)
instead of a plain text box or a fixed `Select`: existing values are
offered as suggestions, but typing something new and saving it makes
that value available as a suggestion for everyone else immediately
after. Backed by a new `GET /api/v1/assets/field-options` endpoint
(distinct existing values per field, technology's built-in suggestion
list merged in). Technology's backend type changed from a strict enum to
a free-form string end-to-end (domain entity, schema, mapper, repository)
to allow values outside the original fixed list - the DB column was
already a plain VARCHAR, so this is a typing-layer change only, no data
migration needed for it.

**Rack number.** New `rack_number` field on asset business metadata,
plumbed through the full stack (migration `0003`, domain entity, ORM
model, schemas, mapper, repository upsert) and surfaced in its own
"Server Location" section on the Asset Details business tab, alongside
Site.

**Sites management page.** New `sites` table (migration `0003`, backfilled
from any site names already in use on existing assets) with full CRUD -
`SiteRepository`/`SqlAlchemySiteRepository`, `GET/POST/PUT/DELETE
/api/v1/sites` (write requires Editor, delete requires Admin), and a new
`/sites` page (name/code/city) reachable from the nav. `asset_business.site`
stays free text rather than a foreign key to avoid a migration risk
against pre-existing free-text values - the Site dropdown just offers
values from both sources.

**Full inventory CSV export.** `GET /api/v1/assets/export.csv` (already
existed for the 7-column Inventory table view) now exports every field -
hardware, OS, business metadata including rack number - instead of just
the summary columns, so "export all servers" actually gets the full
record per server.

**Bulk edit.** New `PUT /api/v1/assets/bulk-business` applies the same
set of business-metadata field changes to many assets in one transaction
(all-or-nothing - an unknown asset ID rolls the whole batch back). The
Inventory page grew row checkboxes, a "Select all on page" header
checkbox, and a "Bulk Edit (N)" button that opens a dialog pre-wired to
the same field-options suggestions; fields left blank in the dialog are
left untouched on every selected asset.

11 new backend tests (48 total, all passing) cover Sites CRUD and its
uniqueness constraint, field-options round-tripping (including saving a
brand-new Technology value), rack_number persistence, bulk edit
(success, empty-list rejection, rollback-on-unknown-asset, role
enforcement), and the expanded CSV columns. Frontend type-checks and
builds clean (`tsc -b && vite build`).

**Migration:** run `alembic upgrade head` (new revision `0003`) before
deploying the new backend image - it adds the `sites` table and
`asset_business.rack_number`, and backfills `sites` from any distinct
`site` values already present on existing assets.

## 1.4.0 - 2026-09-22

The 1.3.0 fix below made failures visible (proper rollback + logged
tracebacks) but the underlying "only last host collected" bug was still
there, now surfacing as a *different* 500. The real backend logs (thank
you for pulling them) pinned down the actual cause - two separate bugs,
both now fixed:

**Bug 1 - the real root cause of "only last host collected".** The
logs showed multiple *completely different* hosts (`k8s-master-2`,
`k8s-worker-3`, `docker1`, `cs7`, ...) each overwriting the *same* asset
row's hostname, one after another. `AssetMatchingService` matches on
`serial_number` first whenever it's non-empty - and unconfigured
KVM/QEMU/Proxmox VMs commonly all report the *identical* BIOS placeholder
serial number "Not Specified". The collector's `gather_hardware` role
only filtered that placeholder out of `ansible_facts.product_serial`, not
out of its own `dmidecode` fallback - so it went straight to the backend
as if it were a real, unique serial, and every VM reporting it collided
into one asset record, each discovery overwriting the last.

Fixed in two places (belt and suspenders):
- `collector/roles/gather_hardware/tasks/main.yml` +
  `collector/group_vars/all.yml` - the placeholder-exclusion list
  (`collector_invalid_serial_values`, now covering more known junk
  values, not just "Not Specified") is applied consistently to *both*
  `product_serial` and the `dmidecode` fallback. A host with no real
  serial now correctly reports an empty one, which falls through to
  primary IP / hostname matching as designed.
- `backend/app/domain/value_objects/enums.py` (new
  `is_usable_identifier()`) + `backend/app/application/services/
  asset_matching_service.py` - the backend now also refuses to match on
  a known placeholder serial, regardless of what any collector version,
  manual API call, or other data source sends it.

**Bug 2 - a bogus `collector_run_id` crashed ingestion entirely.** The
logs also showed `collector_run_id=42` failing a foreign-key check on
`asset_audit` for every host - `42` is the literal example value in
`playbook.yml`'s own usage comment, understandably copied for a manual
test run, and no such row existed. `DiscoveryService.ingest()` now
checks the run exists before citing it on audit records; if it doesn't,
it logs a warning and records the audit without it instead of taking the
whole request down with an unhandled `IntegrityError`.

Both were reproduced directly (unit tests plus an end-to-end run against
the real FastAPI app replicating the exact reported scenario: 5 hosts
sharing the "Not Specified" serial, submitted concurrently, citing
`collector_run_id=42`) and confirmed fixed - all 5 hosts now get their
own asset and every request returns 200. 11 new regression tests added
(37 total, all passing).

**Note on existing data:** any asset row that already absorbed multiple
hosts' data before this fix (repeatedly renamed as different hosts wrote
over it) will keep the last writer's hostname/IP and a mixed audit trail.
It won't get worse, and on the *next* discovery run every affected host
will correctly get its own new asset (since its serial now resolves to
empty and it no longer matches anything by IP or hostname either) - but
consider finding and deleting that one polluted row so its history isn't
misleading. To find it: look for an asset whose audit history shows
several different `hostname` values in a short window.

## 1.3.0 - 2026-09-22

Fixes a production bug reported after the previous release: a cron-triggered
collection run against a multi-host inventory ended up with only the last
host's asset in the database, and a manual `ansible-playbook` run showed
`Status code was 500 ... /api/v1/discovery` for one of the hosts
(`k8s-worker-2`).

**Root cause:** `POST /api/v1/discovery` updated the shared `collector_runs`
row with a read-modify-write (SELECT the row, mutate its counters in
Python, `UPDATE` the whole row back). Ansible's default `linear` strategy
fires every inventory host's `submit_payload` task within the same few
seconds, so several hosts POST against the *same* `collector_run_id`
concurrently, all racing on that one row. This both lost counter updates
(reproduced directly: 20 concurrent increments against the same row left
`success_count` at 1 instead of 20) and, because the route only caught
`DomainError`, let any other exception from that contention surface as an
unhandled, unlogged 500 with **no rollback** - silently dropping the
asset that request had just discovered along with it.

**Fixed:**
- `backend/app/infrastructure/database/repositories/sqlalchemy_collector_run_repository.py`
  and `backend/app/application/interfaces/repositories.py` - added
  `increment_success()` / `increment_failure()`, a single atomic
  `UPDATE ... SET success_count = success_count + 1` in place of the
  racy select-then-save.
- `backend/app/api/v1/routes/discovery.py` - now uses the atomic
  increments, catches *any* exception (not just `DomainError`), always
  rolls back the session, and logs the full traceback via structlog so a
  future failure is visible in `docker compose logs backend` instead of
  a bare 500.
- Added a regression test submitting several hosts against one
  `collector_run_id` and asserting every host gets its own asset with
  correct run counters. Verified end-to-end against 15 genuinely
  concurrent, separately-connected discovery submissions.

No database migration is required - this release is backend application
code only. Rebuild and restart `backend` and `scheduler` (they share the
same image) to pick it up.

## 1.2.0

Fixed two additional Ansible collector crashes found via real (not just
syntax-check) end-to-end playbook execution while verifying the 1.1 fix:
an infinite recursion in `playbook.yml`'s self-referential `vars:` block
when no `-e collector_run_id=...` extra-var was supplied, and a
`collector_primary_ip` crash on hosts with no detected default route.

## 1.1.0

Fixed two production issues reported after the initial 1.0 release:

- The collector container failed with "plugin 'yaml' was not installed"
  - root-caused to the `community.general.yaml` stdout callback plugin
    being removed in `community.general` 12.0.0. Replaced with the
    ansible-core-native `stdout_callback = default` +
    `callback_result_format = yaml`, which needs no collection at all.
- All containers ran on UTC regardless of the deployer's actual
  timezone. Added a `TZ` environment variable (see
  `deployment/.env.example`), wired into every container plus the
  scheduler's `AsyncIOScheduler` so cron expressions are interpreted in
  the configured timezone rather than always UTC.

## 1.0.0

Initial MVP: Clean Architecture FastAPI backend, React/TypeScript/MUI
frontend, Ansible-based collector, 5-service Docker Compose deployment,
asset matching (Serial Number -> Primary IP -> Hostname), change-only
audit engine, and JWT + collector API-key authentication.
