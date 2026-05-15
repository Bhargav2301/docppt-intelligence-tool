# Phase 3 Plan: Model Runtime and Fallback Layer

## Goal
Setup NLP fallback layer and model registry.

## Steps

### 1. NLP Dependencies
- **Action**: Append `transformers`, `torch`, `sentence-transformers`, `spacy`, `nltk`, `sumy`, `scikit-learn`, `networkx` to `services/nlp/requirements.txt`.

### 2. Runtime Configuration
- **Action**: Create `services/nlp/runtime/config.py`.
- **Content**: Load env variables for `MODEL_MODE`, `SUMMARIZATION_MODEL`, etc. Define fallback constants.

### 3. Model Registry
- **Action**: Create `services/nlp/runtime/registry.py`.
- **Content**: A class with `get_summarization_model()`, `get_embedding_model()`, etc. that dynamically imports `transformers` and loads weights via HuggingFace hub only upon first call.

### 4. Fallback Decorator
- **Action**: Create `services/nlp/runtime/fallback.py`.
- **Content**: A `with_fallback` function/decorator that intercepts ML calls. If `MODEL_MODE` is `extractive_only` or an Exception is caught, it returns a hardcoded fallback or calls `sumy`.

### 5. Models API Endpoint
- **Action**: Create `services/nlp/routers/models.py`.
- **Content**: A route to return current model cache status.
- **Action**: Add it to `main.py`.

## Verification
- Run `uvicorn main:app` locally (if python environment permits) or build the docker image to ensure there are no syntax errors.
- Confirm `/api/models/status` returns `200 OK`.
