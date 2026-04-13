# PRD

## Original Problem Statement
Please Create a .env file for:

APP_PASSWORD: Set this to AtlasMaster2026

Run tests

Follow-up request: add persistent storage and versioning so current users do not need to hard refresh.

## User Choices
- Database: MongoDB
- Persist: variants + login sessions + audit/mission logs
- Update behavior: auto-update dashboard data in place, but prompt on full app changes
- Existing data: migrate existing in-memory data if possible during this update

## Architecture Decisions
- Kept the existing FastAPI + Jinja server-rendered architecture.
- Switched app state from in-memory dictionaries/sets to MongoDB collections using `MONGO_URL` and `DB_NAME`.
- Kept a compatibility layer so existing tests and state access patterns continue to work.
- Added a lightweight app-version check endpoint and client-side polling banner for release detection.
- Added dashboard polling against a snapshot endpoint so live data refreshes without a hard reload.
- API auth failures now return JSON 401 for `/api/*` paths while browser pages still redirect to login.

## What's Implemented
- Root `.env` now includes `APP_PASSWORD`, `MONGO_URL`, and `DB_NAME`.
- `app/state.py` now persists variants, sessions, and mission logs in MongoDB.
- Sessions remain valid across fresh state instances because they are stored in MongoDB.
- Added `/api/app-meta` for version detection and `/api/dashboard-snapshot` for live dashboard refresh.
- Added a global update banner in the base template and auto-sync on the dashboard.
- Added/updated backend regression tests for persistence and versioning.
- Full backend suite passes: 37 tests.

## Prioritized Backlog
### P0
- Align runtime/deployment process configuration with this single FastAPI app structure.

### P1
- If a live in-memory export is ever available before restart, add a one-time import utility for legacy runtime state.
- Add optional session expiry / cleanup policy for old sessions.

### P2
- Add live refresh for variant detail pages as well, not just the dashboard.
- Add small admin diagnostics page for env/version/database health.

## Next Tasks
- Fix the process/startup wiring so the hosted app starts from the correct app entrypoint.
- Optionally add a one-click manual “refresh data now” action for operators.
- Optionally add persistent audit timestamps and user attribution if multi-user access is introduced.
