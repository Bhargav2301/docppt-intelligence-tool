# Phase 5 Context: Doc Summary

## Goal
Generate structured summary, product description, and requirements.

## Key Decisions
1. **Generative Requirement Extraction:** Per user request, requirements are classified and prioritized using a local generative SLM (`google/flan-t5-small`) instead of purely relying on `spaCy` keyword heuristics. `spaCy` is still used to chunk sentences, but the model determines if a sentence is a requirement and what its priority is.
2. **Fallback Layer:** If the `google/flan-t5-small` model fails or `MODEL_MODE` is `extractive_only`, the requirement extractor will fall back to basic regex/keyword heuristics.
3. **Pipeline Flow:** The `POST /api/doc/analyze` endpoint chains the summarizer and requirement extractor together.
