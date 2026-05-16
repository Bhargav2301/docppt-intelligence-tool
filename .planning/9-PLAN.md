# Phase 9 Plan: AI Rewrite Engine

## Goal
Generate rewrites with safety bounds (length & evaluation).

## Steps

### 1. Configuration Update
- **Action**: Add `REWRITE_MAX_EXPANSION = 1.30` to `services/nlp/runtime/config.py`.

### 2. Rewriter Service
- **Action**: Create `services/nlp/analysis/rewriter.py`.
- **Content**: 
  - `generate_rewrite(text: str, tone: str) -> str`.
  - Uses `registry.get_instruction_model()`. If mode is `extractive_only` or generation fails, returns original text.

### 3. API Router
- **Action**: Create `services/nlp/routers/rewrite.py`.
- **Content**: 
  - `POST /api/ppt/rewrite`.
  - Accepts a single segment: `{ "original_text": "...", "tone": "professional" }`.
  - Calls `generate_rewrite`.
  - Enforces length constraint: if `len(rewrite) > 1.3 * len(original)`, revert to original and add a `length_overflow` flag.
  - Computes similarity and perplexity via `calculate_similarity` and `calculate_perplexity`.
  - Appends `hallucination_risk` flag if similarity < threshold.
  - Returns the `final_text`, `flags`, and `eval_scores`.

### 4. Integration
- **Action**: Include `rewrite.router` in `services/nlp/main.py`.

## Verification
- Code builds without errors.
- `/api/ppt/rewrite` rejects massive length expansions and adds the `length_overflow` flag.
