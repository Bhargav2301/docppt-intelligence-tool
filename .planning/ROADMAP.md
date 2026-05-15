# Roadmap

**13 phases** | **13 requirements mapped** | All v1 requirements covered ✓

| Phase | Goal | Requirements | Criteria |
|-------|------|--------------|----------|
| **1: Project Setup** | Create monorepo, Next.js, FastAPI, Docker | None | 4 |
| **2: DB and Storage** | Set up Postgres, schema, and session API | None | 4 |
| **3: Model Runtime** | NLP fallback layer and model registry | None | 3 |
| **4: Doc Extraction** | Extract text from docx, URLs, pasted text | DOC-01, DOC-02 | 4 |
| **5: Doc Summary** | Generate summary, spec, and requirements | DOC-03, DOC-04, DOC-05 | 4 |
| **6: PPT Extraction** | Extract PPT slide and shape text | PPT-01 | 3 |
| **7: PPT Artifacts** | Detect AI/Markdown artifacts in slides | PPT-02 | 3 |
| **8: PPT Scoring** | Local AI-likeness style scoring | PPT-03 | 3 |
| **9: PPT Rewrite** | Local model / rules for text rewrite | PPT-04 | 3 |
| **10: PPT Review UI** | Edit, review, and export cleaned PPTX | PPT-05, PPT-06 | 4 |
| **11: Dashboard** | Session history and downloads | SYS-01, SYS-02 | 3 |
| **12: Testing** | QA edge cases and fallbacks | None | 5 |
| **13: Deployment** | Docker-compose for local deploy | None | 3 |

---

## Phase 1: Project Setup
**Goal:** Create monorepo with frontend, backend, local model environment, and storage configuration.
**Requirements:** None
**Success criteria:**
- Web app starts locally
- FastAPI service starts locally
- Health check returns 200
- Docker Compose boots full stack

## Phase 2: DB and Storage
**Goal:** Create schema, storage paths, and session lifecycle.
**Requirements:** None
**Success criteria:**
- Migrations run cleanly
- Test session can be created/updated
- Files stored and retrieved
- Cascading delete works for sessions

## Phase 3: Model Runtime
**Goal:** Set up NLP runtime that avoids paid LLM API dependency.
**Requirements:** None
**Success criteria:**
- Service loads configured models or enters fallback
- Extractive-only mode works without transformer model
- Model failures produce warnings, not crashes

## Phase 4: Doc Extraction
**Goal:** Extract clean text from Google Docs, `.docx`, and pasted text.
**Requirements:** DOC-01, DOC-02
**Success criteria:**
- Valid URL/docx extracts text
- Pasted text is accepted
- Normalization maintains headers/structure
- Empty inputs show clear errors

## Phase 5: Doc Summary
**Goal:** Generate structured summary, product description, and requirements.
**Requirements:** DOC-03, DOC-04, DOC-05
**Success criteria:**
- Source doc produces all 3 outputs
- No paid API-generated text
- Requirements are grouped and prioritized
- Guesses marked as assumptions

## Phase 6: PPT Extraction
**Goal:** Extract PPT text with metadata.
**Requirements:** PPT-01
**Success criteria:**
- Text extracted from typical decks
- Slide and shape references preserved
- Image-only decks clearly state "no extractable text"

## Phase 7: PPT Artifacts
**Goal:** Detect visible artifacts in slide text.
**Requirements:** PPT-02
**Success criteria:**
- Known citation/delimiter artifacts flagged
- Exact matched text and recommended fix shown
- Runs without local model dependency

## Phase 8: PPT Scoring
**Goal:** Quality scoring based on signals.
**Requirements:** PPT-03
**Success criteria:**
- Explainable signals per text segment
- Stable scores across repeated runs
- UI displays reasons, not just numbers

## Phase 9: PPT Rewrite
**Goal:** Generate natural rewrites for flagged text.
**Requirements:** PPT-04
**Success criteria:**
- Artifact-only fixes run without generative model
- Rewrites are concise and ready
- Risky rewrites flagged for review

## Phase 10: PPT Review UI
**Goal:** Inspect, edit, accept, reject, export changes.
**Requirements:** PPT-05, PPT-06
**Success criteria:**
- Review every proposed change
- Only accepted/edited changes applied
- Cleaned PPT downloads successfully
- Original deck unchanged

## Phase 11: Dashboard
**Goal:** Revisit outputs and manage data.
**Requirements:** SYS-01, SYS-02
**Success criteria:**
- Sessions visible after processing
- Outputs can be reopened
- Session delete cleans DB and files

## Phase 12: Testing
**Goal:** Validate across realistic documents and fallbacks.
**Requirements:** None
**Success criteria:**
- No unhandled exceptions in core flows
- Fallback mode returns usable output
- PPT export preserves non-text objects
- Destructive actions require confirmation
- Accessibility checks pass

## Phase 13: Deployment
**Goal:** Deploy preserving low-cost strategy.
**Requirements:** None
**Success criteria:**
- Runs from README instructions
- No paid API key required
- Sample doc and PPT process end-to-end
