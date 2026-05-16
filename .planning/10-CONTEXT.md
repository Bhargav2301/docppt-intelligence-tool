# Phase 10 Context: PPT Compilation

## Goal
Rebuild the PPT presentation with updated text while perfectly preserving the original styling and layout.

## Key Decisions
1. **Surgical Run-Level Replacement**: We will iterate through a given array of modifications, targeting the exact `slide_index`, `shape_id`, `paragraph_index`, and `run_index`. Setting `run.text = new_text` ensures `python-pptx` maintains the underlying XML styling (fonts, colors, size).
2. **Graceful Failures**: If the presentation was modified between extraction and compilation (causing index drifts where a shape or run no longer exists), the compiler will safely catch the `IndexError` or `KeyError`, log a warning, and skip that specific modification without crashing the entire export.
3. **In-Memory Processing**: The file is ingested, modified, and exported entirely within memory (`io.BytesIO`) to avoid any disk write vulnerabilities.
