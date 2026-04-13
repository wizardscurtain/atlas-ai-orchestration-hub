# PRD

## Original Problem Statement
Please Create a .env file for:

APP_PASSWORD: Set this to AtlasMaster2026

Run tests

Follow-up requests:
- add persistent storage and versioning so current users do not need to hard refresh
- make the preview/staging environment work correctly here in Emergent
- add sync status
- analyze native deployment issues and fix code-level blockers for production deployment

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
- Hardened deployment env handling so the app works with backend-managed secrets and Atlas-style MongoDB timing.

## What's Implemented
- Root `.env` includes `APP_PASSWORD`, `MONGO_URL`, and `DB_NAME` for sandbox use.
- Added `/app/backend/.env` so deployment-aligned backend secret loading works as expected.
- `app/main.py` now loads backend `.env` first, then root `.env`, while still letting real environment variables win.
- `app/state.py` now loads env files safely on standalone import and initializes MongoDB lazily instead of connecting at module import time.
- MongoDB startup retries are longer and more production-tolerant.
- `frontend/server.js` now uses `BACKEND_PROXY_TARGET` instead of `REACT_APP_BACKEND_URL`, avoiding production proxy loops when frontend secrets are injected.
- Added `/api/app-meta`, `/api/dashboard-snapshot`, and `/api/variants/{id}/snapshot` for update/version and live sync behavior.
- Added reusable sync status UI across authenticated major pages.
- Added staging wrappers so preview/staging now loads correctly.
- Added/expanded regression tests for env loading, persistence, versioning, sync status, and deployment hardening.
- Verified live preview loads and the full backend suite passes: 40 tests.

## Prioritized Backlog
### P0
- None currently blocking the product, preview, or deployment hardening path.

### P1
- Extend live sync from variant detail to more fields if collaborative editing becomes important.
- Add session expiry / cleanup for old session records.

### P2
- Add a fuller operator system-status view with database health and sync history.
- Add explicit legacy import tooling if old runtime-only data ever needs manual migration.

## Next Tasks
- If needed, review the actual production deployment logs once they include concrete stack traces to confirm the hardened fixes match the exact failing stage.
- Add richer end-to-end automation around create/edit/deploy flows using the stable test IDs.
- Optionally add a user-facing status legend explaining syncing vs version updates.
