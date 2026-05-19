# DocPPT Intelligence Tool - TEST_PLAN_V1.md

This document serves as the comprehensive E2E test suite for validating all core and V2 functionality, edge cases, fallback routes, security policies, and privacy protocols.

---

## 1. Document Extraction & Processing Pipeline

### 1.1 Single Doc Processing (Pasted Text)
- **Precondition:** User is logged in.
- **Steps:**
  1. Navigate to `/process/doc`.
  2. Paste a standard text (e.g. *"Our product is a mobile app named Tasky. It must support user registration and allow creating tasks with high/low priority. A task must have a title, description, and due date."*) in the Paste text area.
  3. Click **Analyze**.
- **Expected Result:**
  - Page redirects or updates to show structured product description, summaries, and categorized prioritized requirements (e.g., Task management: High Priority).
  - Open developer console or check recent sessions; a new session entry is generated.

### 1.2 Single Doc Processing (Word File Upload)
- **Precondition:** A valid `.docx` file is prepared locally.
- **Steps:**
  1. Navigate to `/process/doc`.
  2. Upload the `.docx` file using the file drag-and-drop input.
  3. Click **Analyze**.
- **Expected Result:**
  - File successfully uploads and parses.
  - The structured summary, product description, and requirements grids populate with parsed text.

### 1.3 Batch Doc Processing
- **Precondition:** Multiple valid `.docx` files are prepared.
- **Steps:**
  1. Navigate to `/process/doc` and select the **Batch Upload** tab.
  2. Drag and drop 3 distinct `.docx` files.
  3. Click **Analyze Batch**.
- **Expected Result:**
  - A Batch Results Grid renders immediately displaying each document with status badges (`validating`, `extracting`, `analyzing`, `completed`).
  - Upon completion, each row has a "View Analysis" shortcut navigating to the respective detailed session page.

---

## 2. PowerPoint Analysis & Humanization Pipeline

### 2.1 Single PPT Analysis (Conservative Sensitivity)
- **Precondition:** A valid `.pptx` file is prepared.
- **Steps:**
  1. Navigate to `/process/ppt`.
  2. Upload `.pptx` file.
  3. Set sensitivity slider/selector to **Conservative**.
  4. Click **Humanize Presentation**.
- **Expected Result:**
  - PPT successfully parses.
  - Review panel loads displaying slide-by-slide text boxes.
  - Only exact citation or delimiter artifacts (like markdown delimiters or raw `[1]` tags) are flagged. No generative rewrites are suggested by default.
  - Exporting "Clean PPT" downloads the modified deck with layout preserved.

### 2.2 Single PPT Analysis (Balanced / Generative Rewrite)
- **Precondition:** A valid `.pptx` file is prepared.
- **Steps:**
  1. Navigate to `/process/ppt`.
  2. Upload `.pptx` file.
  3. Set sensitivity to **Balanced** or **Aggressive**.
  4. Click **Humanize Presentation**.
- **Expected Result:**
  - System attempts to call local or hosted LLM to generate professional rewrites for identified slide components.
  - Review screen displays proposed rewrites with options: Accept, Reject, Edit.
  - Modifying a text block manually and clicking "Accept" persists changes.
  - Clicking "Export Presentation" triggers `/api/ppt/compile_session/{id}` and downloads a valid `.pptx` reflecting exactly the accepted and manually edited replacements.

---

## 3. Session Management & Dashboard

### 3.1 Dashboard Validation
- **Precondition:** At least 2 doc sessions and 2 ppt sessions exist in history.
- **Steps:**
  1. Navigate to `/dashboard`.
  2. Verify that **Recent Sessions** list loads showing both Doc and PPT processing runs with correct filenames/labels.
  3. Click the filter tags: **Docs**, **PPT**, **Completed**, **Failed**.
- **Expected Result:**
  - Table dynamically filters and displays corresponding items correctly.

### 3.2 Session Action Verification
- **Steps:**
  1. On `/dashboard`, find a completed PPT session, click **View Review**.
  2. Verify that it opens the correct review path (`/review/{id}`).
  3. Return to `/dashboard`, click **Delete** on a session. Confirm the action.
- **Expected Result:**
  - DB record is wiped, associated files are cleared from uploads folders on the disk.
  - Row is dynamically removed from dashboard table list.

---

## 4. User Settings & Multi-Mode LLM Configurations

### 4.1 Granular Validation of the 5 LLM Modes
- **Steps:**
  1. Navigate to `/settings`.
  2. **Test Mode 1: Local CPU.** Select Local CPU and save settings. Execute a rewrite; verify that local Flan-T5 model loads in CPU memory and logs the status.
  3. **Test Mode 2: Local GPU.** Select Local GPU and save settings. Verify CUDA is loaded.
  4. **Test Mode 3: Extractive-Only.** Select Extractive Only and save settings. Execute a PPT analysis; verify no models are loaded and processing completes instantly using regular expression rule scripts.
  5. **Test Mode 4: Managed Hosted LLM.** Select Managed Hosted LLM, save settings. Verify endpoint inputs are hidden. Perform a rewrite; verify that the backend directs the request to the configured `MANAGED_LLM_ENDPOINT`.
  6. **Test Mode 5: Custom LLM Endpoint.** Select Custom LLM Endpoint, verify URL input appears. Set custom URL (e.g. `http://localhost:11434/v1`) and Model ID (e.g. `mistral`), save settings. Execute a rewrite; check backend logs to verify it posts to this specific custom endpoint.
- **Verification:**
  - In each mode, check that subsequent runs populate a new `ModelRun` row in the database matching the exact `model_mode` selected.

---

## 5. Security & Authentication Controls

### 5.1 Sign Up Password Validation
- **Steps:**
  1. Navigate to `/auth/signup`.
  2. Enter a weak password (e.g. `12345`). Click Sign Up.
- **Expected Result:**
  - Frontend blocks form submission and highlights validation error ("Password must be at least 8 characters").
  - Attempting to force-post via API returns a clear `400 Bad Request` explaining that the password fails the length requirement.

### 5.2 Sign Up & Redirect
- **Steps:**
  1. Navigate to `/auth/signup`.
  2. Enter valid Email, full name, and an 8-character password. Click Sign Up.
- **Expected Result:**
  - User record and associated `UserSettings` are created in DB.
  - Backend returns a valid auth token.
  - Page redirects directly to `/dashboard` with logged-in user profile displayed in header.

### 5.3 Dev-Only Dashboard Protection
- **Steps:**
  1. Create or log into a regular user account (role = `user`).
  2. Manually navigate URL to `/dev/dashboard`.
- **Expected Result:**
  - Access is blocked. UI redirects user to standard `/dashboard` with a warning message, or renders a "403 Forbidden - Access Denied" card.
  - Log in as the seeded developer user (`local_user@example.com` / `password` in dev mode), navigate to `/dev/dashboard`, and verify page loads cleanly.

---

## 6. Telemetry & Privacy Controls

### 6.1 Telemetry Consent Settings Toggle
- **Steps:**
  1. Navigate to `/settings`.
  2. Toggle off the *"Allow crash telemetry"* option and save settings.
  3. Trigger an API or client-side crash intentionally.
  4. Inspect Network tab.
- **Expected Result:**
  - No network request is dispatched to `/api/telemetry/crash`.
  - Toggle on the *"Allow crash telemetry"* option and save settings.
  - Trigger a crash; verify payload is sent with consent flag = `True`.

### 6.2 Global Crash Consent Modal
- **Precondition:** Cleared local storage and fresh user.
- **Steps:**
  1. Cause an intentional app error.
  2. Verify that `CrashConsentModal` dialog displays with rich aesthetics.
  3. Click **"No, Keep Private"**.
- **Expected Result:**
  - Browser saves `docppt_crash_consent = denied` in `localStorage`. No telemetry is transmitted.
  - Trigger another error; verify that the user is not prompted again.
