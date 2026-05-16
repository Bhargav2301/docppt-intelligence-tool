# Phase 10 Plan: PPT Compilation

## Goal
Build the `.pptx` compiler to apply text updates preserving layout.

## Steps

### 1. Compiler Service
- **Action**: Create `services/nlp/extraction/ppt_compiler.py`.
- **Content**: 
  - `compile_ppt(original_file_bytes: bytes, modifications: List[Dict]) -> bytes`.
  - Parse `modifications`, iterating and looking up the `run` using the precise indices.
  - Wrap the lookup in a `try/except` block to catch index drifts (e.g., deleted slides or shapes). Log these skips using `logger.warning`.
  - Overwrite `run.text = new_text`.
  - Save to an in-memory `io.BytesIO()` buffer and return `buffer.getvalue()`.

### 2. API Router
- **Action**: Update `services/nlp/routers/ppt.py`.
- **Content**: 
  - Add `POST /api/ppt/compile`.
  - Accepts `file: UploadFile` and `modifications: str = Form(...)`.
  - Parses the `modifications` JSON string.
  - Calls `compile_ppt`.
  - Returns the bytes via `StreamingResponse` with the proper `.pptx` MIME type and `Content-Disposition` header.

## Verification
- Code builds without errors.
- `/api/ppt/compile` gracefully handles invalid indices without crashing.
