# Phase 4 Context: Doc Extraction

## Goal
Extract text from docx, URLs, pasted text.

## Key Decisions
1. **Google Docs Auth:** The backend will attempt to use Google Docs API. If the `GOOGLE_CLIENT_ID` isn't found or auth fails, it will return a clean 501/400 error rather than crashing.
2. **Text Normalization:** `ftfy` (Fix Text For You) is used to resolve common encoding bugs ("mojibake") that happen when users copy-paste from PDFs or Word docs into the raw text input.
3. **DOCX Parsing:** `python-docx` is utilized to extract text paragraph by paragraph. We insert basic newlines to retain structural boundaries for downstream summarization chunks.
4. **API Structure:** We expose a unified `POST /api/doc/extract` endpoint that can handle multi-part file uploads (`.docx`), raw text payloads, or URLs.
