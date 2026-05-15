# Phase 5 Plan: Doc Summary

## Goal
Generate structured summary, product description, and requirements.

## Steps

### 1. Update Registry
- **Action**: Modify `services/nlp/runtime/registry.py` to add `get_instruction_model()`, loading `INSTRUCTION_MODEL` (e.g., `google/flan-t5-small`) using `pipeline("text2text-generation")`.

### 2. Analysis Services
- **Action**: Create `services/nlp/analysis` module.
- **Action**: Add `doc_summarizer.py` implementing `generate_structured_summary()`. It uses the summarization model from the registry, wrapped with `@with_summarization_fallback`.
- **Action**: Add `req_extractor.py` implementing `extract_requirements()`. It will:
  1. Chunk text into sentences using `spaCy`.
  2. Use the instruction model to prompt: `"Is this a product requirement? Answer yes or no: {sentence}"`
  3. If yes, prompt: `"Classify priority as P0, P1, or P2: {sentence}"`
  4. Provide a hardcoded fallback if `MODEL_MODE == "extractive_only"`.

### 3. API Router
- **Action**: Create `services/nlp/routers/analysis.py`.
- **Content**: `POST /api/doc/analyze`. Takes text, calls summarizer and req extractor, returns JSON structure mapping to schema.

### 4. Integration
- **Action**: Wire `analysis` router into `services/nlp/main.py`.

## Verification
- Code builds without errors.
- `/api/doc/analyze` exists in the OpenAPI schema.
