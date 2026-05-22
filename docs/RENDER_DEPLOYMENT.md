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

## 4. Render Blueprint Deployment (Automated Flow)

We recommend using Render's **Blueprint (YAML) flow** to deploy the entire stack at once:

1. Push this repository to your GitHub account.
2. Log in to the [Render Dashboard](https://dashboard.render.com).
3. Click **New** (top right) and select **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically parse the `render.yaml` file in the root and configure three services:
   - **`docppt-db`**: A managed PostgreSQL database.
   - **`docppt-backend`**: FastAPI web service using the Dockerfile under `services/nlp`.
   - **`docppt-frontend`**: Next.js web service using the Dockerfile under `apps/web`.
6. Click **Apply** to deploy the services.

---

## 5. Production Database Seeding

Once the services are deployed, you must seed a secure developer account to monitor telemetry and error events:

1. Go to your Render Dashboard and open the **`docppt-backend`** Web Service.
2. Select the **Shell** tab on the left-side navigation to open a terminal context inside the container.
3. Run the following seed script command:
   ```bash
   python infra/scripts/prod_seed.py \
     --email your-developer-email@example.com \
     --password YourSecurePassword123 \
     --role developer
   ```
4. This command will hash the password and securely insert the user into the production Postgres database. Default credentials like `local_user@example.com` are blocked and will NOT be seeded in production.

---

## 6. Making the Site Usable by Other Users

To share the application with external team members or users:

1. **Keep Public Visibility Enabled**:
   - The frontend service `docppt-frontend` must remain a **Public Web Service** so users can access it at `https://docppt-frontend.onrender.com`.
2. **User Sign-up & Isolation**:
   - Authentication is fully enabled. Other users can register themselves at `/auth/signup` and log in.
   - Standard users are assigned `role = "user"`. They will only see their own sessions and will be blocked from accessing developer telemetry dashboards.
3. **Hosted LLM Enablement (Zero Local Installs)**:
   - In production, users should not be expected to run a local Ollama endpoint.
   - As a developer, configure the `MANAGED_LLM_ENDPOINT` and `MANAGED_LLM_API_KEY` (e.g. OpenAI, Anthropic, or a self-hosted cloud Llama model) in the backend's environment variables.
   - In Settings, select **Managed Hosted LLM** and save. The app will now process summaries and rewrites using the cloud endpoint for all users without requiring any local setups.

---

## 7. Post-Deployment Smoke Test Checklist

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

