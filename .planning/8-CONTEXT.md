# Phase 8 Context: Extractive Evaluation

## Goal
Score how true generated text is to original text to detect semantic drift and hallucinations.

## Key Decisions
1. **Semantic Similarity Threshold:** We have set the default hallucination threshold to `0.75` based on cosine similarity computed by `sentence-transformers/all-MiniLM-L6-v2`. If the score drops below this, we flag it as `hallucination_risk` with `high` severity. This threshold is exposed as an environment variable to allow future tuning.
2. **Perplexity for Fluency:** `distilgpt2` is used to calculate perplexity, which serves purely as a readability/fluency signal, not as a gate for hallucination detection.
3. **Execution Fallbacks:** The `@safe_perplexity` fallback ensures that the API will gracefully return nulls for these metrics if the system is running in `extractive_only` mode or if models fail to load.
