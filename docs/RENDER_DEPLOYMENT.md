# Render Cloud Deployment Guide - RENDER_DEPLOYMENT.md

This document outlines the cloud deployment architecture, environment configurations, database migration patterns, and post-deployment validation checklists for the **DocPPT Intelligence Tool** deployed on Render.

---

## 1. Deployment Architecture

The application is deployed as two decoupled Web Services and a Managed Postgres database on Render:

```mermaid
graph LR
    User([End User]) --> NextJS[Render Web Service: Next.js Frontend]
    NextJS --> FastAPI[Render Web Service: FastAPI Backend]
    FastAPI --> Postgres[(Render Managed Postgres DB)]
```

1. **Frontend Service (`web`):** Next.js single-page application deployed as a **Node Web Service**.
2. **Backend Service (`nlp`):** FastAPI Python service deployed as a **Python Web Service**.
3. **Database Service (`db`):** **Managed PostgreSQL** instance provided by Render (Production).

---

## 2. Environment Variables & Portability Configuration

All configuration is driven purely by environment variables. No Render URLs are hardcoded in the codebase, ensuring that the same Docker files and code paths run seamlessly in both local Docker environments and Render.

### 2.1 Backend Environment Variables (`nlp` Service)

| Environment Variable | Production Value (Render Example) | Default Local/Dev Value | Description |
|----------------------|-----------------------------------|--------------------------|-------------|
| `ENV` | `production` | `development` (or `local_dev`) | Disables default dev user seeding when set to `production`. |
| `DATABASE_URL` | `postgresql://user:pass@host/db` | *Unset* (triggers SQLite fallback) | Postgres connection URI for production data persistence. |
| `FRONTEND_URL` | `https://docppt-intel.onrender.com` | `http://localhost:3000` | Target URL of the Next.js frontend, loaded dynamically into CORS. |
| `MODEL_MODE` | `managed_endpoint` | `extractive_only` | Initial runtime execution mode default. |
| `MANAGED_LLM_ENDPOINT` | `https://api.your-free-endpoint.com/v1` | *Unset* | Base API URL of your self-hosted Llama/Mistral server. |
| `MANAGED_LLM_MODEL_NAME` | `llama3-70b` | *Unset* | Model ID for the developer self-hosted LLM endpoint. |

### 2.2 Frontend Environment Variables (`web` Service)

| Environment Variable | Production Value (Render Example) | Default Local/Dev Value | Description |
|----------------------|-----------------------------------|--------------------------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://docppt-nlp.onrender.com` | `http://localhost:8000` | Points the browser API clients directly to the FastAPI service URL. |

---

## 3. Database Strategy: SQLite (Dev) vs. Postgres (Prod)

To maintain a zero-friction local developer workflow while supporting standard enterprise data durability in cloud production:
- **Production Mode:** When `DATABASE_URL` is set, the backend dynamically connects to the PostgreSQL driver.
- **Local Fallback:** If `DATABASE_URL` is empty, the database initializer falls back to the local SQLite database (`docppt.db`).
- **Safe Dynamic Migrations:** Dynamic database initialization (`Base.metadata.create_all`) and dynamic inspection-based column alterations run transparently, adapting safely to both SQLite and Postgres.

---

## 4. Render Build & Run Commands

### 4.1 Backend Service (`nlp`) Setup
- **Service Type:** Web Service (Python)
- **Build Command:**
  ```bash
  pip install -r services/nlp/requirements.txt
  ```
- **Start Command:**
  ```bash
  uvicorn services.nlp.main:app --host 0.0.0.0 --port 8000
  ```

### 4.2 Frontend Service (`web`) Setup
- **Service Type:** Web Service (Node)
- **Build Command:**
  ```bash
  cd apps/web && npm install && npm run build
  ```
- **Start Command:**
  ```bash
  cd apps/web && npm run start
  ```

---

## 5. Post-Deployment Smoke Test Checklist

Execute these 6 verification checks immediately after successfully deploying to Render to ensure integrity:

- `[ ]` **1. Service Discovery & Health Validation**
  - Navigate to backend health endpoint `https://<your-nlp-url>.onrender.com/health`.
  - **Success Criteria:** Returns `{"status": "ok"}` with HTTP 200.
  
- `[ ]` **2. User Registration & Auth Pipeline**
  - Navigate to the frontend login page, click **Sign Up**, and create a fresh test account.
  - **Success Criteria:** User account registers successfully in the production Postgres instance, generates a valid token, and redirects seamlessly to the dashboard.
  
- `[ ]` **3. Security Sandbox Verification (Developer Isolation)**
  - Attempt to navigate directly to `https://<your-web-url>.onrender.com/dev/dashboard` using your fresh test account.
  - **Success Criteria:** Access is blocked; user receives a `403 Forbidden` response or a clean UI block redirecting them to `/dashboard`.

- `[ ]` **4. Doc Extraction & NLP Pipeline**
  - Click **Analyze Doc**, paste a sample specifications text, and execute.
  - **Success Criteria:** Text normalizes, summary successfully populates, requirements prioritized properly, and no C-extension or memory crashes occur on Render container.

- `[ ]` **5. PPT Shape Replacement & Compilation**
  - Navigate to **Humanize PPT**, upload a small test deck, set sensitivity to balanced/conservative, verify reviewed text block replacements, and click **Export Presentation**.
  - **Success Criteria:** Replaces target slide shape paragraphs at the run level, compiles successfully in production memory, and downloads a layout-perfect `.pptx` file.

- `[ ]` **6. Crash Telemetry Consent Compliance**
  - Toggle off telemetry in Settings. Trigger an error, check the console; verify no network calls were made to `/api/telemetry/crash`.
  - Toggle it back on. Trigger an error; verify that a clean, scrubbed telemetry payload containing *no document content* is sent and stored in the database.
