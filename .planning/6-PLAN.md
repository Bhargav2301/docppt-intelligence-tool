# Phase 6 Plan: PPT Extraction

## Goal
Extract text from `.pptx` files with full metadata referencing.

## Steps

### 1. Requirements
- **Action**: Add `python-pptx` to `services/nlp/requirements.txt`.

### 2. Parser Logic
- **Action**: Create `services/nlp/extraction/ppt_parser.py`.
- **Content**: 
  - `extract_ppt_text(file_bytes)`
  - Iterates `slides -> shapes -> paragraphs -> runs`.
  - Maps to structure: `{"slide_index", "shape_id", "paragraph_index", "run_index", "original_text", "normalized_text"}` (where normalized = original initially).

### 3. API Router
- **Action**: Create `services/nlp/routers/ppt.py`.
- **Content**: 
  - `POST /api/ppt/extract`
  - Accepts `UploadFile` (only `.pptx`).
  - Calls parser and returns the JSON payload.
  
### 4. Integration
- **Action**: Include `ppt.router` in `services/nlp/main.py`.

## Verification
- Code builds without errors.
- `/api/ppt/extract` exists in the OpenAPI schema.
