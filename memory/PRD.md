# PRD

## Original Problem Statement
Please Create a .env file for:

APP_PASSWORD: Set this to AtlasMaster2026

Run tests

Follow-up requests:
- add persistent storage and versioning so current users do not need to hard refresh
- make the preview/staging environment work correctly here in Emergent
- add sync status

## User Choices
- Database: MongoDB
- Persist: variants + login sessions + audit/mission logs
- Update behavior: auto-update dashboard data in place, but prompt on full app changes
- Existing data: migrate existing in-memory data if possible during this update
- Sync status: show last sync time + syncing state + error state if refresh fails
- Sync status placement: all major pages

## Architecture Decisions
- Kept the core app as a single FastAPI + Jinja server-rendered application.
- Added MongoDB-backed persistence for variants and sessions.
- Added app-version detection and dashboard snapshot polling for live updates.
- Added a staging-compatible `/app/backend` wrapper and `/app/frontend` proxy so the hosted preview works in Emergent’s expected split layout.
- Added a reusable sync-status panel in the base template so authenticated pages can report syncing, success, and failure states consistently.
- Added a variant snapshot endpoint so detail pages can refresh without a hard reload.

## What's Implemented
- Root `.env` includes `APP_PASSWORD`, `MONGO_URL`, and `DB_NAME`.
- `app/state.py` persists variants, sessions, and mission logs in MongoDB.
- Added `/api/app-meta`, `/api/dashboard-snapshot`, and `/api/variants/{id}/snapshot` for update/version and live sync behavior.
- Added a global update banner and dashboard auto-sync.
- Added reusable sync status UI across authenticated major pages:
  - Dashboard: live fleet data sync state
  - Variant detail: live variant snapshot sync state
  - New/edit pages: app freshness monitoring state
- Added staging wrappers so preview/staging now loads correctly.
- Added missing `data-testid` attributes to login, detail, and form controls used in user flows.
- Improved login footer contrast.
- Verified live preview loads and the dashboard sync panel shows `Synced` in the hosted preview.
- Full backend suite passes: 39 tests.

## Prioritized Backlog
### P0
- None currently blocking the product or preview.

### P1
- Extend live sync from variant detail to more fields if collaborative editing becomes important.
- Add session expiry / cleanup for old session records.

### P2
- Add a fuller operator system-status view with database health and sync history.
- Add explicit legacy import tooling if old runtime-only data ever needs manual migration.

## Next Tasks
- Optionally surface sync history or failure counts in the dashboard.
- Add richer end-to-end automation around create/edit/deploy flows using the stable test IDs.
- Optionally add a user-facing status legend explaining syncing vs version updates.
