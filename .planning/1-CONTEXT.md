# Phase 1 Context: Project Setup

## Goal
Create monorepo with frontend, backend, local model environment, and storage configuration.

## Key Decisions
1. **Monorepo Structure:** 
   - `apps/web`: Next.js 14+ app router, TypeScript, TailwindCSS for the frontend.
   - `services/nlp`: FastAPI, Python 3.11+ for the backend.
   - `packages/shared`: (Optional) Shared types or data contracts.
   - `infra/`: Docker Compose configuration.
2. **Backend Framework:** FastAPI is selected due to the native fit with the Python NLP ecosystem (Transformers, Torch, spaCy).
3. **Frontend Framework:** Next.js is selected to quickly iterate on the web UI and build out the dashboard/review views later.
4. **Local Deployment Default:** The infrastructure defaults to local deployment via Docker Compose. The `docker-compose.yml` will run the Next.js app, the FastAPI service, Postgres, and setup a local cache volume for NLP models.
5. **No External LLM API:** The MVP and Docker setup will not require any paid external API keys.

## Open Questions for Later Phases
- Will we use Supabase for Postgres+Storage, or self-hosted Postgres and MinIO? (Phase 2 decision)
- Which specific small models will we use for summarization and scoring? (Phase 3 decision)
