# Phase 9 Context: AI Rewrite Engine

## Goal
Generate improved slide text while enforcing structural boundaries and safety constraints.

## Key Decisions
1. **Length Constraints**: To prevent breaking PowerPoint bounding boxes, we enforce a strict 30% expansion limit (`REWRITE_MAX_EXPANSION = 1.30`). If a rewrite exceeds this length relative to the original, we completely discard it, return the original text, and attach a `length_overflow` flag.
2. **Evaluation Integration**: Every accepted rewrite is automatically scored against the Phase 8 evaluator. If the semantic drift is too high (`similarity < 0.75`), a `hallucination_risk` flag is added.
3. **Optional Execution**: The rewrite engine is explicitly a secondary phase that acts upon the text *after* artifact detection.
