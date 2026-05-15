# Backend Schema: DocPPT Intelligence Tool

This document defines the database schema, relationships, file storage layout, JSON structures, indexes, row-level security approach, and API-facing data contracts for the DocPPT Intelligence Tool.

## Schema Principles

- Every processing run is a session.
- A session belongs to one user in hosted mode.
- Local-only mode can use a default local user or omit authentication.
- Source files and exported files are tracked separately.
- Doc outputs and PPT outputs use separate tables because their data structures differ.
- PPT analysis must preserve slide, shape, paragraph, and run identifiers where possible.
- Model metadata must be stored to support reproducibility and debugging.
- AI-likeness scores are stored as quality signals, not ground-truth labels.

## Entity Relationship Overview

```text
users 1 ── * sessions
sessions 1 ── 0..1 doc_outputs
sessions 1 ── 0..1 ppt_outputs
sessions 1 ── * files
ppt_outputs 1 ── * ppt_slide_results
ppt_slide_results 1 ── * ppt_text_segments
sessions 1 ── * model_runs
users 1 ── 1 user_settings
```

## Tables

### `users`

Stores user identity in hosted mode.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK, default `gen_random_uuid()` | User ID. |
| `email` | TEXT | Unique, nullable in local mode | User email. |
| `full_name` | TEXT | Nullable | Display name. |
| `avatar_url` | TEXT | Nullable | Profile image. |
| `auth_provider` | TEXT | Default `email` | `email`, `google`, `local`. |
| `google_linked` | BOOLEAN | Default `false` | Whether Docs API access is connected. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |
| `updated_at` | TIMESTAMPTZ | Default `now()` | Updated timestamp. |

### `user_settings`

Stores user preferences and processing configuration.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Setting row ID. |
| `user_id` | UUID | FK `users.id`, unique, cascade delete | Owner. |
| `theme` | TEXT | Default `dark` | `dark` or `light`. |
| `model_mode` | TEXT | Default `local_cpu` | `local_cpu`, `local_gpu`, `extractive_only`, `user_hosted_endpoint`. |
| `summarization_model` | TEXT | Nullable | Example: `sshleifer/distilbart-cnn-12-6`. |
| `instruction_model` | TEXT | Nullable | Example: `google/flan-t5-small`. |
| `perplexity_model` | TEXT | Nullable | Example: `distilgpt2`. |
| `embedding_model` | TEXT | Nullable | Example: `sentence-transformers/all-MiniLM-L6-v2`. |
| `ppt_sensitivity` | TEXT | Default `balanced` | `conservative`, `balanced`, `aggressive`. |
| `retain_source_files` | BOOLEAN | Default `true` | Controls file retention. |
| `auto_delete_days` | INTEGER | Nullable | Optional retention period. |
| `google_tokens_encrypted` | JSONB | Nullable | Encrypted OAuth token payload. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |
| `updated_at` | TIMESTAMPTZ | Default `now()` | Updated timestamp. |

### `sessions`

Represents every processing run.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Session ID. |
| `user_id` | UUID | FK `users.id`, cascade delete | Owner. |
| `session_type` | TEXT | Not null | `doc` or `ppt`. |
| `input_type` | TEXT | Not null | `google_doc_url`, `docx_upload`, `pasted_text`, `pptx_upload`. |
| `input_label` | TEXT | Nullable | Filename or doc title. |
| `input_url` | TEXT | Nullable | Google Doc URL if used. |
| `status` | TEXT | Default `created` | Session lifecycle status. |
| `error_code` | TEXT | Nullable | Machine-readable error. |
| `error_message` | TEXT | Nullable | User-safe error. |
| `processing_started_at` | TIMESTAMPTZ | Nullable | Start time. |
| `completed_at` | TIMESTAMPTZ | Nullable | Completion time. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |
| `updated_at` | TIMESTAMPTZ | Default `now()` | Updated timestamp. |

### `files`

Tracks input and output artifacts.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | File row ID. |
| `session_id` | UUID | FK `sessions.id`, cascade delete | Related session. |
| `user_id` | UUID | FK `users.id`, cascade delete | Owner for faster RLS. |
| `file_role` | TEXT | Not null | `input`, `output`, `intermediate`. |
| `file_type` | TEXT | Not null | `pptx`, `docx`, `md`, `json`, `txt`. |
| `storage_path` | TEXT | Not null | Private storage path. |
| `original_filename` | TEXT | Nullable | Original upload filename. |
| `mime_type` | TEXT | Nullable | Detected MIME type. |
| `size_bytes` | BIGINT | Nullable | File size. |
| `checksum_sha256` | TEXT | Nullable | Optional integrity check. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |

### `doc_outputs`

Stores Google Doc and `.docx` analysis outputs.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Output ID. |
| `session_id` | UUID | FK `sessions.id`, unique, cascade delete | Related session. |
| `source_title` | TEXT | Nullable | Extracted document title. |
| `source_word_count` | INTEGER | Nullable | Word count after cleaning. |
| `structured_summary` | TEXT | Not null | Final summary. |
| `product_description` | TEXT | Not null | Generated product description. |
| `implementation_requirements` | JSONB | Not null | Grouped requirements. |
| `open_questions` | JSONB | Nullable | Unclear or missing details. |
| `assumptions` | JSONB | Nullable | Inferred assumptions. |
| `source_traceability` | JSONB | Nullable | Requirement-to-source mapping. |
| `quality_report` | JSONB | Nullable | Grounding, confidence, warnings. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |

### `ppt_outputs`

Stores deck-level PPT analysis output.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | PPT output ID. |
| `session_id` | UUID | FK `sessions.id`, unique, cascade delete | Related session. |
| `total_slides` | INTEGER | Not null | Slide count. |
| `total_text_segments` | INTEGER | Default `0` | Count of extracted text segments. |
| `total_flags` | INTEGER | Default `0` | Count of all flags. |
| `artifact_counts` | JSONB | Not null | Counts by flag type. |
| `accepted_rewrite_count` | INTEGER | Default `0` | User-accepted rewrite count. |
| `rejected_rewrite_count` | INTEGER | Default `0` | User-rejected rewrite count. |
| `export_file_id` | UUID | FK `files.id`, nullable | Clean PPTX file. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |

### `ppt_slide_results`

Stores slide-level results.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Slide result ID. |
| `ppt_output_id` | UUID | FK `ppt_outputs.id`, cascade delete | Parent PPT output. |
| `session_id` | UUID | FK `sessions.id`, cascade delete | Related session. |
| `slide_index` | INTEGER | Not null | Zero-based index. |
| `slide_number` | INTEGER | Not null | Human-readable number. |
| `slide_title` | TEXT | Nullable | Inferred title. |
| `flag_count` | INTEGER | Default `0` | Flags on this slide. |
| `status` | TEXT | Default `pending_review` | `pending_review`, `accepted`, `partially_accepted`, `rejected`. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |

### `ppt_text_segments`

Stores sentence or shape-level analysis results.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Segment ID. |
| `ppt_slide_result_id` | UUID | FK `ppt_slide_results.id`, cascade delete | Parent slide. |
| `shape_id` | TEXT | Nullable | PowerPoint shape identifier if available. |
| `paragraph_index` | INTEGER | Nullable | Paragraph index. |
| `run_index` | INTEGER | Nullable | Text run index. |
| `segment_index` | INTEGER | Not null | Segment order. |
| `original_text` | TEXT | Not null | Original extracted text. |
| `normalized_text` | TEXT | Nullable | Text used for analysis. |
| `suggested_text` | TEXT | Nullable | Rewrite candidate. |
| `final_text` | TEXT | Nullable | User-approved or edited text. |
| `flags` | JSONB | Not null | Array of issue objects. |
| `quality_scores` | JSONB | Nullable | Perplexity, burstiness, lexical metrics. |
| `semantic_similarity` | NUMERIC | Nullable | Similarity between original and rewrite. |
| `decision` | TEXT | Default `pending` | `pending`, `accepted`, `rejected`, `edited`. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |
| `updated_at` | TIMESTAMPTZ | Default `now()` | Updated timestamp. |

### `model_runs`

Stores model and algorithm execution metadata.

| Column | Type | Constraints | Notes |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Model run ID. |
| `session_id` | UUID | FK `sessions.id`, cascade delete | Related session. |
| `run_type` | TEXT | Not null | `summarization`, `requirements`, `ppt_scoring`, `ppt_rewrite`, `embedding_check`. |
| `model_name` | TEXT | Nullable | Model or algorithm used. |
| `model_mode` | TEXT | Not null | `local_cpu`, `local_gpu`, `extractive_only`, `user_hosted_endpoint`. |
| `input_tokens_estimate` | INTEGER | Nullable | Estimated token count. |
| `output_tokens_estimate` | INTEGER | Nullable | Estimated output count. |
| `duration_ms` | INTEGER | Nullable | Runtime. |
| `status` | TEXT | Not null | `success`, `fallback`, `failed`. |
| `metadata` | JSONB | Nullable | Warnings, fallback reason, thresholds. |
| `created_at` | TIMESTAMPTZ | Default `now()` | Created timestamp. |

## JSON Structures

### `implementation_requirements`

```json
{
  "functional": [
    {
      "id": "FR-001",
      "requirement": "The system shall accept Google Doc URLs as input.",
      "priority": "P0",
      "source_reference": "Paragraph 3",
      "confidence": 0.86
    }
  ],
  "technical": [],
  "integrations": [],
  "data": [],
  "ui_ux": [],
  "security_privacy": [],
  "non_functional": []
}
```

### `flags`

```json
[
  {
    "type": "citation_artifact",
    "severity": "high",
    "matched_text": "[1]",
    "explanation": "Bracketed citation marker appears to be leftover generated-text residue.",
    "recommendation": "Remove marker or replace with a real citation if needed."
  },
  {
    "type": "low_burstiness",
    "severity": "medium",
    "matched_text": "Full sentence text",
    "explanation": "Sentence rhythm is highly uniform compared with nearby slide text.",
    "recommendation": "Vary structure and shorten the phrase."
  }
]
```

### `quality_scores`

```json
{
  "perplexity": 18.4,
  "burstiness_score": 0.21,
  "sentence_length_zscore": -1.2,
  "type_token_ratio": 0.43,
  "ngram_repetition_rate": 0.18,
  "punctuation_density": 0.09,
  "style_risk_score": 0.74,
  "label": "review_recommended"
}
```

## Indexes

```sql
CREATE INDEX idx_sessions_user_id_created_at ON sessions(user_id, created_at DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_files_session_id ON files(session_id);
CREATE INDEX idx_doc_outputs_session_id ON doc_outputs(session_id);
CREATE INDEX idx_ppt_outputs_session_id ON ppt_outputs(session_id);
CREATE INDEX idx_ppt_slide_results_output_id ON ppt_slide_results(ppt_output_id);
CREATE INDEX idx_ppt_text_segments_slide_id ON ppt_text_segments(ppt_slide_result_id);
CREATE INDEX idx_model_runs_session_id ON model_runs(session_id);
```

## Row-Level Security

### Policy Requirements

- Users can only read, create, update, and delete their own sessions.
- Users can only access files tied to their own sessions.
- Users can only access doc outputs and PPT outputs through owned sessions.
- Admin access should be restricted to service role or explicit internal accounts.
- Local-only mode may disable RLS if no multi-user hosting exists, but the schema should still support hosted RLS later.

### Example Policy Concept

```sql
-- sessions
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid())

-- files
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid())
```

## Storage Layout

```text
docppt-inputs/
  {user_id}/
    {session_id}/
      original.docx
      original.pptx
      source_snapshot.txt

docppt-outputs/
  {user_id}/
    {session_id}/
      summary.md
      requirements.json
      cleaned.pptx
      analysis_report.json
```

## Deletion Rules

- Deleting a session deletes:
  - `doc_outputs`.
  - `ppt_outputs`.
  - `ppt_slide_results`.
  - `ppt_text_segments`.
  - `model_runs`.
  - Related `files` records.
  - Storage files.
- Deleting a user deletes all sessions and files.
- If `retain_source_files` is false, original inputs are deleted after output generation.

## Migration Order

1. Enable required extensions, including `pgcrypto`.
2. Create `users`.
3. Create `user_settings`.
4. Create `sessions`.
5. Create `files`.
6. Create `doc_outputs`.
7. Create `ppt_outputs`.
8. Create `ppt_slide_results`.
9. Create `ppt_text_segments`.
10. Create `model_runs`.
11. Add indexes.
12. Enable RLS.
13. Add policies.
14. Seed local/default user if local-only mode is enabled.

