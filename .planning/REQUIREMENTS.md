# v1 Requirements

## Google Docs Processing
- [ ] **DOC-01**: Accept Google Doc URL, `.docx` upload, or pasted text.
- [ ] **DOC-02**: Normalize whitespace, headings, bullets, Unicode characters, and section boundaries.
- [ ] **DOC-03**: Generate a structured summary using extractive methods and small local models.
- [ ] **DOC-04**: Generate a polished product description from the client brief.
- [ ] **DOC-05**: Extract functional, technical, data, integration, and non-functional requirements.

## PPT Humanization
- [ ] **PPT-01**: Accept `.pptx`, parse slides, preserve slide IDs, shape IDs, and original text.
- [ ] **PPT-02**: Detect `[1]`, `[Source]`, `†`, markdown markers, broken citations, bracket residues, excessive delimiters, unusual symbols, and smart-character inconsistencies.
- [ ] **PPT-03**: Compute style signals such as sentence length variance, burstiness, lexical diversity, repetition, punctuation density, and perplexity using local models.
- [ ] **PPT-04**: Rewrite only flagged text segments to sound natural, presentation-ready, and human-edited while preserving meaning.
- [ ] **PPT-05**: Show original vs cleaned text, flags, and rewrite rationale in a review screen.
- [ ] **PPT-06**: Export `.pptx` with text replacements while preserving non-text elements (slide count, layout, images, charts, shapes).

## Dashboard & Sessions
- [ ] **SYS-01**: Store recent doc and PPT processing sessions per user.
- [ ] **SYS-02**: Allow markdown export of doc outputs and JSON export of structured requirements.

## Traceability

*(To be filled by roadmap phase mappings)*
