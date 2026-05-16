# Phase 8 Plan: Extractive Evaluation

## Goal
Measure text fidelity (similarity) and readability (perplexity) of AI outputs.

## Steps

### 1. Update Configuration
- **Action**: Add `HALLUCINATION_SIMILARITY_THRESHOLD = float(os.getenv("HALLUCINATION_SIMILARITY_THRESHOLD", "0.75"))` to `services/nlp/runtime/config.py`.

### 2. Evaluator Service
- **Action**: Create `services/nlp/analysis/evaluator.py`.
- **Content**: 
  - `calculate_similarity(source, generated)`: Get embeddings from `registry.get_embedding_model()`, compute `cosine_similarity` via `sklearn.metrics.pairwise`.
  - `calculate_perplexity(text)`: Use `registry.get_perplexity_model()` and PyTorch's `CrossEntropyLoss` via the `@safe_perplexity` decorator.

### 3. API Router
- **Action**: Create `services/nlp/routers/eval.py`.
- **Content**: 
  - `POST /api/eval/score`
  - Accepts `source_text` and `generated_text`.
  - Computes metrics.
  - If similarity < 0.75, populates a `hallucination_flag` object in the response.

### 4. Integration
- **Action**: Include `eval.router` in `services/nlp/main.py`.

## Verification
- Code builds without errors.
- `/api/eval/score` responds correctly.
