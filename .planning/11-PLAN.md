# Phase 11 Plan: Frontend UI Foundation and Routing

## Goal
Build the Next.js UI shell and API client.

## Steps

### 1. Dependencies
- **Action**: Run `npm install lucide-react` in `apps/web`.

### 2. Styling Foundation
- **Action**: Modify `apps/web/src/app/globals.css`.
- **Content**: Define CSS variables matching the design brief (Dark Mode defaults).

### 3. Layout & Navigation
- **Action**: Modify `apps/web/src/app/layout.tsx`.
- **Content**: Include `Inter` font. Build a simple `TopNav` component wrapping the `children`.

### 4. API Client
- **Action**: Create `apps/web/src/lib/api.ts`.
- **Content**: Implement a native `fetch` wrapper using `process.env.NEXT_PUBLIC_API_BASE_URL` with a fallback to `http://localhost:8000`. Include generic return types and error handling.

### 5. Page Scaffolding
- **Action**: Create default exports for `/`, `/dashboard`, `/process/doc`, `/process/ppt`, and `/review/ppt/[id]`.

## Verification
- Code builds without errors.
- Pages render without 404s.
