# Phase 2 Plan: Database and Storage

## Goal
Create schema, storage paths, and session lifecycle.

## Steps

### 1. Database Migrations
- **Action**: Create `infra/migrations/001_initial_schema.sql`.
- **Content**: 
  - `pgcrypto` extension for UUIDs.
  - Tables: `users`, `user_settings`, `sessions`, `files`, `doc_outputs`, `ppt_outputs`, `ppt_slide_results`, `ppt_text_segments`, `model_runs`.
  - Add indexes and a seed user.

### 2. Local Storage Directories
- **Action**: Create `infra/storage/docppt-inputs` and `infra/storage/docppt-outputs`.
- **Action**: Update `docker-compose.yml` to mount these directories.

### 3. FastAPI ORM Setup
- **Action**: Update `services/nlp/requirements.txt` with `sqlalchemy` and `psycopg2-binary`.
- **Action**: Create `services/nlp/database.py` to establish the connection pool.
- **Action**: Create `services/nlp/models.py` mapping to the SQL schema.

### 4. FastAPI Session API
- **Action**: Create `services/nlp/routers/sessions.py` for CRUD.
- **Action**: Include the router in `main.py`.

## Verification
- Start PostgreSQL via docker-compose and run the `.sql` migration against it.
- Start FastAPI and make a test `POST /api/sessions` call.
