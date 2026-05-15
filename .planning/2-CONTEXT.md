# Phase 2 Context: Database and Storage

## Goal
Create schema, storage paths, and session lifecycle.

## Key Decisions
1. **Raw SQL Migrations:** Instead of using an ORM to generate schema, we will manage raw SQL migrations in `infra/migrations`. This keeps the schema framework-agnostic.
2. **SQLAlchemy ORM:** FastAPI will use SQLAlchemy to interact with the database. We will define Python models that map to the raw SQL schema.
3. **Local Storage:** For the MVP, we will use local directories (`infra/storage/docppt-inputs` and `infra/storage/docppt-outputs`) mounted into the containers via Docker Compose.
4. **Session API:** The core lifecycle API for managing sessions, updating status, and associating files will be housed in FastAPI under `/api/sessions`.
