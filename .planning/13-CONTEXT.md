# Phase 13 Context: PPT Pipeline Frontend Integration

## Goal
Wire the PPT humanization frontend to the backend pipeline. Create a unified `POST /api/ppt/process` that orchestrates extract → artifact detection → AI rewrite → DB persist, then build the slide-by-slide review UI with accept/reject/edit controls and the compile-export download.

## Architecture
1. **`POST /api/ppt/process`** — New orchestrator that:
   - Creates a session (`session_type=ppt`)
   - Extracts runs via `ppt_parser`
   - Detects artifacts via `artifact_detector`
   - Generates rewrites for flagged segments via `rewriter`
   - Persists `PptOutput` + `PptSegment` rows
   - Returns session ID + full slide data for the review page

2. **`/process/ppt`** — Upload form calls `/api/ppt/process`, then redirects to `/review/ppt/{session_id}`

3. **`/review/ppt/[id]`** — Loads segments from `GET /api/sessions/{id}/detail` (extended for PPT), renders slide sidebar + segment diff cards with accept/reject/edit controls, and exports via `POST /api/ppt/compile`
