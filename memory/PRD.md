# PRD

## Original Problem Statement
Please Create a .env file for:

APP_PASSWORD: Set this to AtlasMaster2026

Run tests

Follow-up requests:
- add persistent storage and versioning so current users do not need to hard refresh
- make the preview/staging environment work correctly here in Emergent

## User Choices
- Database: MongoDB
- Persist: variants + login sessions + audit/mission logs
- Update behavior: auto-update dashboard data in place, but prompt on full app changes
- Existing data: migrate existing in-memory data if possible during this update

## Architecture Decisions
- Kept the core app as a single FastAPI + Jinja server-rendered application.
- Added MongoDB-backed persistence for variants and sessions.
- Added app-version detection and dashboard snapshot polling for live updates.
- To match Emergent staging expectations, added a lightweight `/app/backend/server.py` wrapper and a `/app/frontend` proxy app so supervisor can run the project in the expected split layout without rewriting the product.
- Frontend proxy now requires explicit env values and forwards browser traffic to the FastAPI app.

## What's Implemented
- Root `.env` includes `APP_PASSWORD`, `MONGO_URL`, and `DB_NAME`.
- `app/state.py` persists variants, sessions, and mission logs in MongoDB.
- Added `/api/app-meta` and `/api/dashboard-snapshot` for version checks and live dashboard refresh.
- Added a global update banner and dashboard auto-sync.
- Created `/app/backend/server.py` so supervisor’s backend command can start the existing FastAPI app.
- Created `/app/frontend` with a small proxy server and env config so preview/staging routes load correctly on port 3000.
- Added/expanded regression tests for env loading, persistence, versioning, and staging wrappers.
- Added missing `data-testid` attributes to login controls and improved login footer contrast.
- Verified live preview loads successfully and login UI is visible.
- Full backend suite passes: 37 tests.

## Prioritized Backlog
### P0
- None currently blocking the preview environment.

### P1
- Add live auto-refresh on variant detail pages, not just the dashboard.
- Add session expiry / cleanup for old session records.

### P2
- Add a small operator system-status panel for database health, app version, and sync state.
- Add a one-time import tool if legacy runtime-only data ever needs explicit migration.

## Next Tasks
- If desired, extend live sync behavior to detail/edit screens.
- Add richer e2e coverage for the authenticated dashboard flows using the new stable test IDs.
- Optionally improve the login experience with clearer help text or secret rotation controls.
