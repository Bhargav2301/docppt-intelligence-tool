# Implementation Plan: DocPPT Intelligence Tool

This implementation plan sequences the build from local-first infrastructure through Google Doc analysis, PPT humanization, review UI, testing, and deployment. The plan assumes the MVP should avoid paid Claude/OpenAI-style API usage and rely on free/local models, extractive summarization, classical NLP, and optional LSTM/classifier components.

## Phase 1: Project Setup

### Goal

Create a working monorepo with frontend, backend, local model environment, and storage/database configuration.

### Tasks

- Create monorepo:
  - `/apps/web` for Next.js.
  - `/services/nlp` for FastAPI.
  - `/packages/shared` for shared types if needed.
  - `/infra` for Docker Compose and database migrations.
- Initialize Next.js with TypeScript and Tailwind CSS.
- Initialize FastAPI with Python 3.11+.
- Add Docker Compose for:
  - Web app.
  - NLP service.
  - Postgres.
  - Optional local object storage such as MinIO.
- Add `.env.example`.
- Add local model cache directory.
- Add health check endpoints.
- Configure linting and formatting:
  - ESLint.
  - Prettier.
  - Ruff or Black for Python.

### Done Criteria

- Web app starts locally.
- FastAPI service starts locally.
- Health check returns `200`.
- Docker Compose can boot the full stack.
- `.env.example` documents all required variables.

## Phase 2: Database and Storage

### Goal

Create the schema, storage paths, and session lifecycle foundation.

### Tasks

- Write SQL migrations for all tables:
  - `users`.
  - `user_settings`.
  - `sessions`.
  - `files`.
  - `doc_outputs`.
  - `ppt_outputs`.
  - `ppt_slide_results`.
  - `ppt_text_segments`.
  - `model_runs`.
- Add indexes.
- Add RLS policies if using Supabase hosted mode.
- Add local-only default user seed.
- Create storage buckets or local file paths:
  - `docppt-inputs`.
  - `docppt-outputs`.
- Implement session repository functions:
  - Create session.
  - Update status.
  - Save files.
  - Save outputs.
  - Delete session.

### Done Criteria

- Migrations run cleanly.
- Test session can be created and updated.
- Files can be stored and retrieved.
- Deleting a session removes related records.

## Phase 3: Model Runtime and Fallback Layer

### Goal

Set up the low/no-cost NLP runtime that avoids paid LLM API dependency.

### Tasks

- Install NLP dependencies:
  - `transformers`.
  - `torch`.
  - `sentence-transformers`.
  - `sumy`.
  - `spacy`.
  - `nltk`.
  - `scikit-learn`.
  - `textstat`.
- Implement model registry:
  - Summarization model.
  - Instruction model.
  - Perplexity model.
  - Embedding model.
  - Optional LSTM classifier path.
- Implement model loading with caching.
- Implement `MODEL_MODE`:
  - `local_cpu`.
  - `local_gpu`.
  - `extractive_only`.
  - `user_hosted_endpoint`.
- Add fallback behavior:
  - If summarization model fails, use TextRank or LexRank.
  - If perplexity model fails, use statistical features only.
  - If embedding model fails, require manual review for rewrites.
- Log every model run to `model_runs`.

### Done Criteria

- Service can load configured models or enter fallback mode.
- Extractive-only mode works with no transformer model.
- Model failures produce useful warnings, not app crashes.

## Phase 4: Google Doc and DOCX Extraction

### Goal

Extract clean text from Google Docs, `.docx`, and pasted text.

### Tasks

- Implement Google Doc ID parser from URL.
- Implement Google Docs API fetch using OAuth token.
- Implement public/shared doc handling where possible.
- Implement `.docx` extraction.
- Implement pasted text ingestion.
- Normalize:
  - Unicode.
  - Whitespace.
  - Bullets.
  - Numbered lists.
  - Headings.
  - Tables where possible.
- Preserve structural metadata:
  - Headings.
  - Paragraph index.
  - Section title.
  - Source offsets.

### Done Criteria

- Valid Google Doc URL extracts text.
- Valid `.docx` extracts text.
- Pasted text is accepted.
- Empty or inaccessible documents show clear errors.

## Phase 5: Document Summarization and Requirements Generation

### Goal

Generate a structured summary, product description, and implementation requirements from source documents.

### Tasks

- Implement heading-aware chunking.
- Implement extractive summarization:
  - Sentence scoring.
  - Section-level summary.
  - Global summary merge.
- Implement optional local abstractive summarization:
  - Chunk compression with `distilbart` or `flan-t5-small`.
  - Final synthesis from chunk summaries.
- Implement product description generator using structured templates:
  - Product overview.
  - Target users.
  - Problem.
  - Solution.
  - Core workflows.
  - Benefits.
  - Assumptions.
- Implement implementation requirement extractor:
  - Rule-based modal verb detection.
  - Keyword patterns for integrations, auth, data, UI, security, performance.
  - Optional small model classifier for requirement type.
- Implement source-grounding checks:
  - Sentence embedding similarity.
  - Remove unsupported claims.
  - Mark assumptions separately.
- Save outputs to `doc_outputs`.
- Add Markdown and JSON export.

### Done Criteria

- A source document produces all three required outputs.
- Outputs contain no paid API-generated text.
- Requirements are grouped and prioritized.
- Unsupported guesses are marked as assumptions or open questions.

## Phase 6: PPT Text Extraction

### Goal

Extract PPT text with enough metadata to safely replace accepted text later.

### Tasks

- Validate `.pptx` file.
- Reject `.ppt` and macro-enabled formats in MVP.
- Parse file with `python-pptx`.
- Extract:
  - Slide number.
  - Shape ID.
  - Shape type.
  - Paragraph index.
  - Run index where possible.
  - Text content.
- Detect text from:
  - Text boxes.
  - Titles.
  - Tables where possible.
  - Speaker notes if enabled later.
- Save extracted structure to `ppt_slide_results` and `ppt_text_segments`.

### Done Criteria

- Text is extracted from typical PPT decks.
- Slide and shape references are preserved.
- Image-only decks show a clear “no extractable text” state.

## Phase 7: PPT Artifact Detection

### Goal

Detect visible artifacts that make slide text look AI-generated, machine-exported, or unreviewed.

### Tasks

- Implement regex detectors for:
  - Bracketed numeric citations: `[1]`, `[2]`.
  - Named citation placeholders: `[Source]`, `[Citation needed]`.
  - Dagger markers: `†`, `‡`.
  - Markdown bold/italic remnants: `**`, `***`, `_`.
  - Markdown tables or pipes: `|`.
  - Delimiter lines: `---`, `***`.
  - Unbalanced brackets or parentheses.
  - Smart quote inconsistency.
  - Escaped characters.
- Implement punctuation and special-character normalization suggestions.
- Implement bullet nesting checks.
- Store flags with type, severity, location, and recommendation.

### Done Criteria

- Known citation and delimiter artifacts are flagged.
- User can see exact matched text and recommended fix.
- Detection runs without local model dependency.

## Phase 8: PPT AI-Likeness Quality Scoring

### Goal

Implement robust and explainable style scoring based on statistical and ML-inspired signals.

### Tasks

- Implement preprocessing:
  - Normalize text for analysis.
  - Tokenize into sentences.
  - Tokenize into words or subwords.
- Implement feature extraction:
  - Sentence length mean and variance.
  - Burstiness score.
  - Type-token ratio.
  - N-gram repetition.
  - Repeated sentence starts.
  - Punctuation density.
  - Generic AI phrase matches.
  - Optional POS pattern features.
- Implement perplexity:
  - Use `distilgpt2` or another local causal LM.
  - Compute average token negative log likelihood.
  - Compute sentence-level perplexity when feasible.
- Implement quality score:
  - Weighted rule-based score for MVP.
  - Optional logistic regression or gradient boosting classifier.
  - Optional bidirectional LSTM classifier in v1.1.
- Calibrate labels:
  - `clean`.
  - `minor_review`.
  - `review_recommended`.
  - `rewrite_recommended`.
- Add warning copy:
  - “This is a quality signal, not proof of AI generation.”

### Done Criteria

- Each text segment receives explainable quality signals.
- Scores are stable across repeated runs.
- The UI displays reasons rather than only a number.

## Phase 9: PPT Rewrite Generation

### Goal

Generate safer, more natural rewrite candidates for flagged PPT text while preserving meaning.

### Tasks

- Implement deterministic rewrite rules:
  - Remove citation artifacts.
  - Replace em-dash-heavy constructions with commas, periods, or shorter sentences.
  - Remove generic openers.
  - Simplify overloaded phrases.
  - Break long uniform sentences.
  - Vary repeated sentence starts.
- Implement optional local SLM rewrite:
  - Use `flan-t5-small`, `t5-small`, or another small instruction model.
  - Keep prompts short and constrained.
  - Require output length limits.
- Add rewrite guardrails:
  - Do not add new facts.
  - Preserve numbers, names, dates, product terms, and technical nouns.
  - Avoid changing claims.
  - Keep slide text concise.
- Implement semantic similarity check:
  - Compare original and rewrite with `all-MiniLM-L6-v2`.
  - If similarity is below threshold, mark `semantic_risk`.
- Save suggestions as pending review.

### Done Criteria

- Artifact-only fixes can run without a generative model.
- Rewrite suggestions are concise and presentation-ready.
- Risky rewrites are flagged for manual review.

## Phase 10: Review UI and Export

### Goal

Let users inspect, edit, accept, reject, and export PPT changes.

### Tasks

- Build slide review UI.
- Show flag badges and explanations.
- Show original vs suggested text.
- Add accept, reject, edit, and revert controls.
- Persist user decisions.
- Implement PPT export:
  - Clone original deck.
  - Apply accepted changes only.
  - Preserve slide count, images, charts, shapes, and layout.
  - Save cleaned `.pptx`.
- Add download button.
- Add analysis report export as JSON.

### Done Criteria

- User can review every proposed change.
- Only accepted or edited changes are applied.
- Cleaned PPT downloads successfully.
- Original deck remains unchanged.

## Phase 11: Dashboard and Session History

### Goal

Allow users to revisit outputs and manage data.

### Tasks

- Build dashboard session list.
- Add filters:
  - Doc sessions.
  - PPT sessions.
  - Completed.
  - Failed.
- Build session detail pages.
- Add delete session flow.
- Add retry failed session flow.
- Add download previous exports.

### Done Criteria

- Sessions are visible after processing.
- Outputs can be reopened.
- Deleting session removes DB records and files.

## Phase 12: Testing and QA

### Goal

Validate the application across realistic documents, decks, edge cases, and fallback conditions.

### Test Cases

- Google Doc:
  - Short clear brief.
  - Long unstructured brief.
  - Technical project brief.
  - Vague client notes.
  - Empty or inaccessible doc.
- PPT:
  - Clean deck.
  - Deck with citation artifacts.
  - Deck with markdown residue.
  - Deck with uniform AI-style text.
  - Image-only deck.
  - Large deck.
- Model behavior:
  - Local model available.
  - Local model missing.
  - Extractive-only mode.
  - Embedding check failure.
- Export:
  - PPT with images.
  - PPT with tables.
  - PPT with charts.
  - PPT with mixed fonts.

### Done Criteria

- No unhandled exceptions in core flows.
- Fallback mode returns usable output.
- PPT export preserves slide count and non-text objects.
- All destructive actions require confirmation.
- Accessibility checks pass for key screens.

## Phase 13: Deployment

### Goal

Deploy in a way that preserves the low-cost model strategy.

### Recommended MVP Deployment

- Docker Compose local deployment for full control and no API charges.
- Optional hosted frontend with self-hosted NLP container.
- Optional Supabase free-tier database and storage.

### Tasks

- Write Dockerfiles for web and NLP service.
- Add production environment documentation.
- Configure storage.
- Configure database migrations.
- Add model download/setup script.
- Add monitoring logs.
- Add backup and deletion instructions.

### Done Criteria

- A new developer can run the app from README instructions.
- No paid API key is required.
- Sample doc and PPT can be processed end-to-end.

## Build Dependency Order

```text
Project setup
  -> Database and storage
    -> Model runtime and fallback layer
      -> Doc extraction
        -> Doc summarization and requirements
      -> PPT extraction
        -> Artifact detection
          -> AI-likeness scoring
            -> Rewrite generation
              -> Review UI and export
                -> Dashboard/session history
                  -> Testing
                    -> Deployment
```

## MVP Completion Definition

The MVP is complete when:

- A user can process a Google Doc, `.docx`, or pasted text.
- The app generates a summary, product description, and implementation requirements.
- A user can upload a PPTX.
- The app flags citations, delimiters, special characters, and style quality issues.
- The app suggests humanized rewrites without paid LLM APIs.
- The user can review and export a cleaned PPTX.
- The tool has fallback behavior when local models are unavailable.
- All outputs are downloadable.
- The documentation clearly states that AI-likeness scores are probabilistic quality signals, not proof.

