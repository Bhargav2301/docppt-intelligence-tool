# Phase 3 Context: Model Runtime and Fallback Layer

## Goal
Setup NLP fallback layer and model registry.

## Key Decisions
1. **Lazy Loading:** ML models are extremely memory intensive. The `ModelRegistry` ensures models are loaded into memory *only* when requested, instead of during the FastAPI startup event.
2. **Fallback-First Design:** The application defaults to expecting the worst (e.g. out of memory, no GPU, missing model weights). The `@with_fallback` decorator guarantees that if a `transformers` call fails, execution drops to a safe, deterministic NLP backup (like `sumy` or basic extraction) without failing the HTTP request.
3. **Environment Modes:** `MODEL_MODE` controls behavior. If set to `extractive_only`, the registry will immediately route requests to the fallback layer, completely skipping heavy ML inferences.
