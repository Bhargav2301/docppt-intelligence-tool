# Phase 12 Plan: DB Sessions & Doc UI

## Goal
Build the DB session tracker, Dashboard API, and integrate the frontend Doc Pipeline.

## Steps

### 1. Backend Models Update
- **Action**: Modify `services/nlp/models.py`. Add `DocOutput`, `PptOutput`, and `PptSegment` models mapped to `sessions.id`.

### 2. Alembic Migration
- **Action**: Run `alembic revision --autogenerate` and `alembic upgrade head` to generate tables.

### 3. Sessions API
- **Action**: Modify `services/nlp/routers/sessions.py`.
- **Content**: Add `GET /api/sessions/recent` that joins `Session` with outputs and returns a combined dashboard payload.

### 4. Doc Processing API
- **Action**: Modify `services/nlp/routers/doc.py`.
- **Content**: Add `POST /api/doc/process`. Create session, extract text, run analysis, save `DocOutput`, return combined metadata and results.

### 5. Frontend API Types
- **Action**: Modify `apps/web/src/lib/api.ts`.
- **Content**: Add `fetchRecentSessions()` and `processDocument()` functions.

### 6. Frontend UI Integration
- **Action**: Modify `dashboard/page.tsx` to call `fetchRecentSessions()`.
- **Action**: Modify `process/doc/page.tsx` to call `processDocument()`.
- **Action**: Create `session/[id]/page.tsx` to view completed Doc sessions.

## Verification
- Can process a doc and see results immediately.
- Session appears in Dashboard.
