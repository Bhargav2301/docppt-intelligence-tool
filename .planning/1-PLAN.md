# Phase 1 Plan: Project Setup

## Goal
Create monorepo with frontend, backend, local model environment, and storage configuration.

## Steps

### 1. Initialize Next.js Frontend
- **Action**: Run `npx create-next-app@latest apps/web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"` in non-interactive mode.
- **Why**: Sets up the React/Next.js foundation for the UI with the modern App Router and Tailwind CSS pre-configured.

### 2. Initialize FastAPI Backend
- **Action**: Create the python virtual environment and directory structure in `services/nlp/`.
- **Files**:
  - `services/nlp/requirements.txt`: Include `fastapi`, `uvicorn`, `pydantic`.
  - `services/nlp/main.py`: Basic FastAPI app with a `/health` endpoint returning `200 OK`.
- **Why**: Establishes the backend service that will later run the NLP pipelines.

### 3. Setup Docker Compose
- **Action**: Update `infra/docker-compose.yml`.
- **Content**:
  - `web` service: build from `apps/web/Dockerfile`, port `3000`.
  - `nlp` service: build from `services/nlp/Dockerfile`, port `8000`.
  - `db` service: standard `postgres:15-alpine`, port `5432`.
  - Create volumes for `postgres_data` and a local `model_cache`.
- **Why**: Allows one-command local startup of the entire stack.

### 4. Setup Dockerfiles
- **Action**: Create Dockerfiles for the two services.
- **Files**:
  - `apps/web/Dockerfile`: Standard Node.js Next.js builder and runner.
  - `services/nlp/Dockerfile`: Standard Python 3.11+ runner.

### 5. Validate Health
- **Action**: Run the FastAPI server and Next.js dev server locally to ensure they start correctly.
- **Why**: Ensures the scaffolding is sound before moving on to database integrations in Phase 2.

## Verification
- Run `npm run dev` in `apps/web` -> succeeds.
- Run `uvicorn main:app --reload` in `services/nlp` -> succeeds.
- Hitting `http://localhost:8000/health` returns `200`.
