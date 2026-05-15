# Technical Requirements Document: DocPPT Intelligence Tool

This TRD defines the technical architecture, stack, model strategy, processing pipelines, APIs, constraints, and deployment approach for a low/no-cost document intelligence tool. The MVP must not depend on Claude, OpenAI, or other paid LLM APIs. It should use deterministic NLP, free small language models, local inference, and optional LSTM/classical ML components.

## Architecture Summary

| Layer | Recommended Technology | Purpose |
| :--- | :--- | :--- |
| Frontend | Next.js 14, TypeScript, Tailwind CSS | Web UI, uploads, review screens, downloads |
| Backend API | FastAPI, Python 3.11+ | NLP processing, PPT parsing, doc analysis |
| Database | PostgreSQL via Supabase or local Postgres | Sessions, outputs, flags, audit metadata |
| File Storage | Supabase Storage, S3-compatible storage, or local volume | Input docs, input PPTs, cleaned PPTs, exports |
| Auth | Supabase Auth or local-only mode | User accounts and session ownership |
| NLP Runtime | Hugging Face Transformers, spaCy, scikit-learn, sentence-transformers, NLTK/Sumy | Summarization, feature extraction, scoring, semantic checks |
| PPT Processing | `python-pptx` | Extract and replace PPT text while preserving deck structure |
| Google Docs Integration | Google Docs API with OAuth 2.0 | Read authorized Google Docs |
| Deployment | Docker Compose for local-first MVP; optional Vercel plus container service later | Reduce cost and simplify reproducibility |

## Cost-Control Requirements

- No paid LLM API calls in the MVP.
- All summarization, requirements extraction, analysis, and humanization must run through:
  - Rule-based NLP.
  - Classical ML.
  - Local small language models.
  - Optional LSTM classifier or sequence model.
  - Optional user-hosted Hugging Face model endpoints only if the user provides them.
- The app must expose a configuration flag named `MODEL_MODE` with allowed values:
  - `local_cpu`
  - `local_gpu`
  - `extractive_only`
  - `user_hosted_endpoint`
- Default mode must be `local_cpu` or `extractive_only`.

## Recommended Model Strategy

### Google Docs Summarization

Use a hybrid pipeline to avoid hallucination and reduce compute cost.

| Stage | Technique | Candidate Libraries or Models |
| :--- | :--- | :--- |
| Cleaning | Regex, Unicode normalization, heading detection | Python `re`, `ftfy`, `unidecode` |
| Segmentation | Heading-aware chunking, paragraph grouping | Custom Python |
| Extractive summary | TextRank, LexRank, centroid ranking | `sumy`, `networkx`, `scikit-learn` |
| Abstractive summary | Small local summarization model | `sshleifer/distilbart-cnn-12-6`, `google/flan-t5-small`, `t5-small` |
| Requirement extraction | Pattern-based extraction plus small model classification | `spaCy`, `scikit-learn`, optional `flan-t5-small` |
| Similarity validation | Ensure generated output remains source-grounded | `sentence-transformers/all-MiniLM-L6-v2` |

### PPT Humanization Analysis

AI text detectors usually combine preprocessing, statistical features, machine-learning scoring, and calibrated labels. The tool should adapt that structure for quality guidance, not certainty, using the user-provided detector concepts such as perplexity, burstiness, n-gram repetition, lexical diversity, and segment-level labeling. References for the underlying conceptual detector pipeline include Grammarly, Compilatio, Coursera, GPTZero, Scribbr, Originality.ai, Adobe, and related AI-detection research resources:

- https://www.grammarly.com/blog/ai/how-do-ai-detectors-work/
- https://www.compilatio.net/en/blog/how-do-ai-detectors-work
- https://www.coursera.org/articles/how-do-ai-detectors-work
- https://gptzero.me/news/how-ai-detectors-work/
- https://www.scribbr.com/ai-tools/how-do-ai-detectors-work/
- https://originality.ai/blog/ai-content-detection-algorithms
- https://www.adobe.com/acrobat/resources/how-do-ai-detectors-work.html
- https://arxiv.org/abs/2405.16422

The MVP should calculate quality signals locally:

| Signal | Purpose | Implementation |
| :--- | :--- | :--- |
| Perplexity | Estimate predictability of text | Use `distilgpt2`, `gpt2`, or another small local causal LM to compute token log probabilities. |
| Burstiness | Measure sentence-level variation | Compute variance of sentence length, punctuation density, and optional per-sentence perplexity. |
| Lexical diversity | Detect repetitive vocabulary | Type-token ratio, moving average TTR, rare word ratio. |
| N-gram repetition | Detect repeated AI-like phrasing | Count repeated bigrams/trigrams and repeated sentence openings. |
| Punctuation density | Detect overuse or unnatural punctuation | Count punctuation per token and compare to baseline thresholds. |
| Citation artifacts | Detect leftover AI citations | Regex for `[1]`, `[2]`, `[Source]`, `†`, `(Source:)`, malformed URLs. |
| Delimiter artifacts | Detect markdown or export residue | Regex for `**`, `***`, `---`, `|`, unbalanced brackets, escaped characters. |
| Style phrases | Detect generic LLM wording | Phrase dictionary for “it is worth noting,” “delve into,” “in today’s fast-paced,” “seamlessly,” “robust,” and similar patterns. |
| Semantic preservation | Prevent harmful rewrites | Compare original and rewrite embeddings using `all-MiniLM-L6-v2`; require similarity above threshold. |

### Optional Classifier

The system can support two local classifier tracks:

- **Classical ML track**: Logistic regression, SVM, random forest, or gradient boosting over handcrafted features.
- **LSTM track**: Lightweight bidirectional LSTM over token embeddings for sentence-level AI-likeness scoring.

The classifier must output probability-like quality scores, but UI copy must describe them as “AI-like style signal,” “low variation,” or “artifact risk,” not as proof of AI generation.

## System Components

### Web App

- Landing page.
- Auth pages if hosted multi-user mode is enabled.
- Dashboard with sessions.
- Google Doc processor.
- PPT processor.
- Review and diff UI.
- Settings for model mode, cleanup sensitivity, and export preferences.

### FastAPI NLP Service

Responsible for:

- File validation.
- Google Doc extraction.
- `.docx` parsing.
- Text preprocessing.
- Summarization.
- Requirement extraction.
- PPT parsing.
- PPT artifact detection.
- AI-likeness feature computation.
- Rewrite recommendation generation.
- PPT reconstruction.

### Database

Stores:

- Users.
- Sessions.
- Source document metadata.
- Generated summaries.
- Product descriptions.
- Implementation requirements.
- PPT flags.
- PPT rewrite candidates.
- Export paths.
- Model run metadata.

### Storage

Stores:

- Original uploaded PPT files.
- Cleaned PPT exports.
- Markdown exports.
- JSON exports.
- Optional source snapshots.

## Data Processing Pipelines

### Google Docs Pipeline

1. Validate input type.
2. Fetch Google Doc content through Google Docs API or parse uploaded `.docx`.
3. Normalize text and structure.
4. Segment into heading-aware chunks.
5. Run extractive summarization per chunk.
6. Optionally run local SLM abstractive compression per chunk.
7. Merge chunk summaries into final summary.
8. Extract product description fields.
9. Extract implementation requirements using patterns plus small-model classification.
10. Validate source grounding and remove unsupported claims.
11. Save session and outputs.
12. Return Markdown, JSON, and UI-renderable response.

### PPT Pipeline

1. Validate `.pptx` file extension, MIME type, and size.
2. Parse deck with `python-pptx`.
3. Extract text by slide, shape, paragraph, and run.
4. Normalize text for analysis without modifying original deck.
5. Run artifact detection.
6. Tokenize into sentences.
7. Compute statistical and linguistic features.
8. Score each segment using rule-based thresholds and optional local classifier.
9. Generate rewrite candidates for flagged segments through deterministic templates and optional local SLM.
10. Check semantic similarity between original and rewrite.
11. Return review data to UI.
12. Apply accepted rewrites to a copy of the original PPT.
13. Export cleaned `.pptx`.

## Key Libraries

### Frontend

- `next`
- `react`
- `typescript`
- `tailwindcss`
- `@tanstack/react-query`
- `zustand`
- `react-dropzone`
- `lucide-react`
- `react-markdown`

### Backend

- `fastapi`
- `uvicorn`
- `pydantic`
- `python-pptx`
- `python-docx`
- `google-api-python-client`
- `google-auth-oauthlib`
- `transformers`
- `torch`
- `sentence-transformers`
- `spacy`
- `nltk`
- `sumy`
- `scikit-learn`
- `numpy`
- `pandas`
- `textstat`
- `ftfy`

## API Endpoints

### Public or Authenticated App API

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/api/doc/analyze` | Start Google Doc or `.docx` analysis. |
| `POST` | `/api/ppt/analyze` | Upload and analyze PPT. |
| `POST` | `/api/ppt/apply-rewrites` | Apply accepted PPT rewrites and generate export. |
| `GET` | `/api/sessions` | List user sessions. |
| `GET` | `/api/sessions/{session_id}` | Retrieve full session results. |
| `GET` | `/api/download/{session_id}/{artifact_type}` | Return downloadable file or signed URL. |
| `DELETE` | `/api/sessions/{session_id}` | Delete session and related files. |

### Internal FastAPI Endpoints

| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check. |
| `POST` | `/nlp/doc/extract` | Extract content from Google Doc or `.docx`. |
| `POST` | `/nlp/doc/summarize` | Run hybrid summarization. |
| `POST` | `/nlp/doc/requirements` | Extract product and implementation requirements. |
| `POST` | `/nlp/ppt/extract` | Extract slide text. |
| `POST` | `/nlp/ppt/analyze` | Run artifact and AI-likeness analysis. |
| `POST` | `/nlp/ppt/rewrite` | Generate local rewrite candidates. |
| `POST` | `/nlp/ppt/export` | Apply accepted rewrites and export PPTX. |

## Environment Variables

```text
APP_ENV=
NEXT_PUBLIC_APP_URL=

DATABASE_URL=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

STORAGE_BUCKET_INPUTS=
STORAGE_BUCKET_OUTPUTS=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

FASTAPI_SERVICE_URL=
FASTAPI_INTERNAL_SECRET=

MODEL_MODE=local_cpu
LOCAL_MODEL_CACHE_DIR=
SUMMARIZATION_MODEL=sshleifer/distilbart-cnn-12-6
INSTRUCTION_MODEL=google/flan-t5-small
PERPLEXITY_MODEL=distilgpt2
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ENABLE_LSTM_CLASSIFIER=false
LSTM_CLASSIFIER_PATH=
```

## Security Requirements

- Never expose OAuth tokens, service role keys, or model service secrets to the browser.
- Store Google OAuth refresh tokens encrypted at rest.
- Restrict file downloads to session owners.
- Validate all uploaded files by extension, MIME type, and parse success.
- Strip active macros and reject legacy `.ppt` files in MVP.
- Enforce per-user storage boundaries.
- Add rate limits for expensive processing routes.
- Delete source files when the user deletes a session.

## Performance Requirements

| Area | Requirement |
| :--- | :--- |
| PPT parsing | Start within 10 seconds for decks under 50 MB. |
| Google Doc extraction | Complete within 30 seconds for typical docs where API access is available. |
| Summarization | Process chunked documents incrementally with visible progress. |
| PPT analysis | Analyze slide text within three minutes for typical decks under 40 slides. |
| Export | Generate cleaned PPTX within 30 seconds after user accepts rewrites. |
| Fallback | If local model inference fails, return extractive/rule-based output instead of failing the whole session. |

## Technical Constraints

- MVP supports English text.
- MVP supports `.pptx`, not `.ppt`.
- MVP may support `.docx` upload as a practical fallback to Google Docs API.
- Local CPU mode may be slower; UI must show progress and allow background session refresh.
- Small local models may produce weaker prose than paid frontier models; outputs must be editable.
- AI-likeness detection is not definitive and must be presented as a quality review aid.

