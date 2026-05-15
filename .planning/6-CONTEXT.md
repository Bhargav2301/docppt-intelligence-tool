# Phase 6 Context: PPT Extraction

## Goal
Extract PPT text with precise metadata mapping down to the `run` level.

## Key Decisions
1. **Run-level indexing:** To allow safe reconstruction of slides later, we are extracting text exactly as-is down to the `run` level (the smallest unit of text with uniform formatting in python-pptx).
2. **Phase 7 Preparation:** Extraction here only grabs the text and prepares the schema (`originaltext` = `normalizedtext`). It will NOT perform semantic rewrites or restructuring. Phase 7 will later apply deterministic rule-based artifact detection over these runs.
3. **Validation:** The parser detects if a `.pptx` file has zero text runs (e.g., image-only slides) and throws an explicit error indicating no extractable text.
