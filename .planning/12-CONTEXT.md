# Phase 12 Context: DB Sessions & Doc UI

## Goal
Integrate the Doc Pipeline UI with a backend that creates and tracks database sessions.

## Key Decisions
1. **DB-Backed Sessions:** As per user request, we are moving away from purely stateless API calls. Every document processing run will now generate a `Session` record, along with `DocOutput` records, tracking status from `created` -> `validating` -> `extracting` -> `analyzing` -> `completed`.
2. **Synchronous UX / Async DB Flow:** While the UI will await the API synchronously for the MVP, the backend will still execute the steps and update the DB as if it were a background job. This ensures session history is immediately populated.
3. **Recent Sessions Dashboard:** A new endpoint `/api/sessions/recent` will supply the frontend dashboard with session history.
