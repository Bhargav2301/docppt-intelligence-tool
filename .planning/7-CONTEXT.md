# Phase 7 Context: PPT Artifact Detection

## Goal
Detect and flag artifact noise in extracted PowerPoint text without altering the text.

## Key Decisions
1. **Rule-Based Strategy:** This phase is completely deterministic. We are using regex heuristics to flag anomalies (citations, markdown noise, delimiters) without generating any new text or dropping any original text.
2. **Bare URLs:** Per user request, we detect bare URLs (`http`, `www`) and flag them as `url_artifact` *unless* they are anchored by contextual words like "see", "reference", or "link". This specifically targets sloppy copy-pastes.
3. **Data Immutability:** The `normalized_text` remains untouched. The API only populates the `flags` array within the segment objects, passing the decision of whether to "accept" the cleanup to the frontend UI.
