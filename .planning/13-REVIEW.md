---
status: review_recommended
files_reviewed: 29
findings:
  critical: 2
  warning: 2
  info: 1
  total: 5
---

# Code Review Report: Phase 13 (Deployment & V2 Updates)

This review covers the source changes since Phase 11, including Phase 12 (DB sessions & Doc pipeline), Phase 13 (PPT Review UI & export), and V2 features (User Auth, Settings, Telemetry).

## Summary of Findings

* **Critical**: 2
* **Warning**: 2
* **Info**: 1
* **Total**: 5

---

## Findings Details

### ### CR-01: Missing Authentication & Ownership Checks on PPT Compilation
* **Component**: FastAPI Backend (`services/nlp/routers/ppt.py`)
* **File Reference**: [ppt.py](file:///c:/Projects/Samtool/docppt-intelligence-tool/services/nlp/routers/ppt.py#L81-L111)
* **Severity**: High
* **Description**: The `/api/ppt/compile_session/{session_id}` endpoint retrieves and compiles a PowerPoint file based on a path mapped directly to `session_id`. However, it does not declare `current_user: User = Depends(get_current_user)` and does not verify if the requesting user owns the session in the database.
* **Risk**: An attacker who guesses or obtains another user's `session_id` can fetch and compile their presentation slides.
* **Recommendation**: Add the `get_current_user` dependency and verify session ownership in the database before proceeding with compilation.

### ### CR-02: Missing Authorization Header in Frontend PPT Session Compile Call
* **Component**: Next.js Frontend (`apps/web/src/lib/api.ts`)
* **File Reference**: [api.ts](file:///c:/Projects/Samtool/docppt-intelligence-tool/apps/web/src/lib/api.ts#L263-L282)
* **Severity**: High
* **Description**: `PptAPI.compileSession` uses raw `fetch` directly rather than the custom `apiFetch` wrapper. As a result, it does not propagate the `Authorization: Bearer <token>` header.
* **Risk**: When `CR-01` is patched to require authentication, all export actions on the frontend review UI will fail with a `401 Unauthorized` error.
* **Recommendation**: Refactor `compileSession` to use the `apiFetch` wrapper, which handles authorization propagation and returns the binary Blob appropriately.

### ### WR-01: Environment Mode Inconsistency (`local_dev` vs `development`)
* **Component**: FastAPI Backend Configuration (`services/nlp/database.py`, `routers/auth.py`, `runtime/registry.py`)
* **File Reference**: [database.py](file:///c:/Projects/Samtool/docppt-intelligence-tool/services/nlp/database.py#L11-L13) and [auth.py](file:///c:/Projects/Samtool/docppt-intelligence-tool/services/nlp/routers/auth.py#L62-L70)
* **Severity**: Medium
* **Description**: The codebase uses both `"local_dev"` and `"development"` to signify development mode, but handles fallback behaviors inconsistently. `database.py` and `registry.py` only load SQLite configurations and setting overrides if `ENV == "local_dev"`. However, `main.py` defaults the environment to `"development"`.
* **Risk**: A developer starting the backend locally without explicitly overriding `ENV=local_dev` will see the application try (and fail) to connect to a production/Docker Postgres instance, leading to immediate crash on startup.
* **Recommendation**: Standardize environment detection by checking if `ENV` is in `("local_dev", "development")` or by setting the default environment variable consistently.

### ### WR-02: Client-Side-Only Access Control for Observability Dashboard
* **Component**: Next.js Frontend (`apps/web/src/app/dev/dashboard/page.tsx`)
* **File Reference**: [page.tsx](file:///c:/Projects/Samtool/docppt-intelligence-tool/apps/web/src/app/dev/dashboard/page.tsx#L23-L40)
* **Severity**: Medium
* **Description**: Dev access checking relies purely on reading the parsed JSON in `localStorage.getItem("docppt_user")`.
* **Risk**: While the backend telemetry endpoint is secure (verifies role on JWT), a user can bypass client-side routing guards and inspect the page layout/structure by modifying their local storage role to `"developer"`.
* **Recommendation**: Fetch the profile from the `/api/auth/me` endpoint on mount to verify the user role against the database session before rendering any portion of the page.

### ### IF-01: Hashing Salt String Encoding Redundancy
* **Component**: FastAPI Backend Utilities (`services/nlp/auth_utils.py`)
* **File Reference**: [auth_utils.py](file:///c:/Projects/Samtool/docppt-intelligence-tool/services/nlp/auth_utils.py#L9-L15)
* **Severity**: Low
* **Description**: `hash_password` generates a salt via `secrets.token_hex(16)` (producing a hex string), then encodes the hex string as UTF-8 bytes to pass into `hashlib.pbkdf2_hmac`.
* **Risk**: Hex strings represent only 4 bits of entropy per byte of storage, reducing the potential space of the salt.
* **Recommendation**: Generate raw bytes using `secrets.token_bytes(16)` directly, which keeps the full 8 bits of entropy per byte, and encode the final output cleanly.
