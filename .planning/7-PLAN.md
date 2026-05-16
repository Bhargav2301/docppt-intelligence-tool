# Phase 7 Plan: PPT Artifact Detection

## Goal
Detect and flag artifact noise in extracted PowerPoint text.

## Steps

### 1. Artifact Detector Service
- **Action**: Create `services/nlp/analysis/artifact_detector.py`.
- **Content**: 
  - `detect_artifacts(text: str, context: str = "") -> List[Dict]`
  - Regex rules for:
    - **Citations**: `r'\[\d+\]|Source:|\u2020|\u2021'`
    - **Markdown Residue**: `r'\*\*.*?\*\*|_.*?_|`.*?`'`
    - **Delimiters**: `r'={4,}|-{4,}|\*{3,}'`
    - **Bare URLs**: `r'(https?://\S+|www\.\S+)'`. Check surrounding context (the full segment or slide context) for words like `see`, `reference`, `url:`, `link:`. If none are found, flag as `url_artifact`.

### 2. API Router
- **Action**: Create `services/nlp/routers/ppt_analysis.py`.
- **Content**: 
  - `POST /api/ppt/detect_artifacts`
  - Accepts a JSON payload containing the structured PPT data (from Phase 6).
  - Iterates through `slides` -> `segments`, passing `original_text` to `detect_artifacts`.
  - Appends the returned flags to the segment's `flags` array.
  - Returns the updated JSON structure.

### 3. Integration
- **Action**: Wire `ppt_analysis.router` into `services/nlp/main.py`.

## Verification
- Code builds without errors.
- `/api/ppt/detect_artifacts` exists in the OpenAPI schema and successfully adds flags to a sample payload without changing the `normalized_text`.
