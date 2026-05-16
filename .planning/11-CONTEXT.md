# Phase 11 Context: Frontend UI Foundation and Routing

## Goal
Establish the Next.js shell, dark-mode aesthetic, global routing, and API communication layer to interface with the FastAPI backend.

## Key Decisions
1. **Design System:** We are implementing the dark-mode first design specified in the UI/UX brief. CSS variables (`--bg-base`, `--accent`, etc.) are injected into `globals.css` and the `Inter` font is used globally.
2. **Icons:** `lucide-react` is used for clean, minimal iconography.
3. **API Client:** A native `fetch` utility layer (`src/lib/api.ts`) is created to centralize requests to the FastAPI backend (`http://localhost:8000`). This supports environment variable configuration, centralized JSON parsing, error handling, and TypeScript generics for response payloads.
4. **Backend Integration:** By building the frontend pages now, we are simultaneously transitioning into the testing phase, wrapping the backend endpoints in real-world usage scenarios to catch discrepancies early.
