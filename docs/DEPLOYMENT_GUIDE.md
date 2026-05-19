# Deployment Guide

## Overview
The DocPPT Intelligence Tool is designed for local or private server deployment.

## Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

## Quick Start (Docker)
1. Clone the repository.
2. Run `./scripts/download_models.sh` (downloads T5, GPT2, etc. to local cache).
3. Run `docker-compose up --build`.
4. Access the web UI at `http://localhost:3000`.

## Environment Variables
See `.env.example` for full list.
- `DATABASE_URL`: Postgres connection string.
- `MODEL_CACHE_DIR`: Path to store downloaded models.
- `NEXT_PUBLIC_API_BASE_URL`: Backend API endpoint.

## Local Development
### Backend
```bash
cd services/nlp
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd apps/web
npm install
npm run dev
```

## Model Management
- Default models are downloaded to `./models_cache`.
- Advanced models (Llama/Mistral) should be hosted separately via Ollama or similar.
