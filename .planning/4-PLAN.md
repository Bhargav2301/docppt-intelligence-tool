# Phase 4 Plan: Doc Extraction

## Goal
Extract text from docx, URLs, pasted text.

## Steps

### 1. Requirements
- **Action**: Add `python-docx`, `google-api-python-client`, `google-auth-oauthlib`, `ftfy`, `python-multipart` to `services/nlp/requirements.txt`.

### 2. Extraction Services
- **Action**: Create `services/nlp/extraction` module.
- **Action**: Add `docx_parser.py` with `extract_from_docx(file_bytes)`.
- **Action**: Add `google_docs.py` with `extract_from_google_doc(url)`. It should raise a custom exception if credentials are not configured.
- **Action**: Add `text_normalizer.py` with `normalize_text(text)` using `ftfy.fix_text`.

### 3. API Router
- **Action**: Create `services/nlp/routers/doc.py`.
- **Content**: 
  - `POST /api/doc/extract`
  - Accepts `UploadFile` (for `.docx`), `url` (form field), or `text` (form field).
  - Normalizes the output.
  - Returns `{"extracted_text": "...", "source_type": "...", "word_count": ...}`.

### 4. Integration
- **Action**: Include `doc.router` in `services/nlp/main.py`.

## Verification
- Code builds without errors.
- `/api/doc/extract` exists in the OpenAPI schema.
