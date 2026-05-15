# App Flow: DocPPT Intelligence Tool

This document maps the pages, navigation, user journeys, processing states, edge cases, and redirects for the web application. The app has two primary workflows: Google Docs-to-product-spec generation and PPT text humanization with reviewable cleanup.

## Navigation Model

### Desktop Navigation

- Top navigation bar with:
  - Product logo.
  - Dashboard.
  - Analyze Doc.
  - Humanize PPT.
  - Sessions.
  - Settings.
  - Profile/logout.

### Mobile Navigation

- Bottom tab navigation with:
  - Home.
  - Doc.
  - PPT.
  - History.
  - Profile.

### Local-Only Mode

If the product is deployed as a local Docker app, authentication can be disabled. In this mode:

- The dashboard opens directly.
- Sessions are stored locally.
- Google OAuth is optional.
- `.docx` upload and pasted text remain available without Google account linking.

## Pages and Screens

| Route | Page | Description |
| :--- | :--- | :--- |
| `/` | Landing Page | Explains the two product workflows and low/no-cost local model strategy. |
| `/dashboard` | Dashboard | Shows recent sessions, processing status, and quick-start actions. |
| `/process/doc` | Google Doc Processor | Accepts Google Doc URL, `.docx`, or pasted text and generates summary/product/requirements. |
| `/process/ppt` | PPT Humanizer | Accepts `.pptx`, analyzes text quality, flags artifacts, and prepares rewrite candidates. |
| `/session/[id]` | Session Detail | Displays saved outputs, flags, downloads, and metadata for a past session. |
| `/review/ppt/[id]` | PPT Review | Shows slide-by-slide original text, flags, rewrite candidates, and accept/reject controls. |
| `/settings` | Settings | Model mode, cleanup sensitivity, storage, Google connection, and privacy controls. |
| `/login` | Login | Optional for hosted multi-user mode. |
| `/signup` | Sign Up | Optional for hosted multi-user mode. |
| `/auth/callback` | Auth Callback | Handles Supabase and Google OAuth redirects. |

## Entry Points

### New Visitor

1. Lands on `/`.
2. Sees two primary CTAs:
   - Analyze a Google Doc.
   - Humanize a PPT.
3. If hosted mode requires auth, user signs up or logs in.
4. If local-only mode is enabled, user proceeds directly to processor page.

### Returning User

1. Opens `/dashboard`.
2. Sees recent sessions grouped by document type.
3. Starts a new doc or PPT run.
4. Reopens old outputs if needed.

## Core User Journey: Google Doc to Product Spec

### Happy Path

1. User opens `/process/doc`.
2. User selects input method:
   - Google Doc URL.
   - `.docx` upload.
   - Paste raw text.
3. User clicks `Analyze Document`.
4. System creates a session with status `pending`.
5. UI shows progress:
   - Validating input.
   - Extracting text.
   - Cleaning structure.
   - Segmenting content.
   - Summarizing.
   - Generating product description.
   - Extracting implementation requirements.
   - Validating output.
6. Results appear in three panels:
   - Structured Summary.
   - Product Description.
   - Implementation Requirements.
7. User edits output inline if needed.
8. User downloads:
   - Markdown.
   - JSON.
   - Optional DOCX in later version.
9. Session status changes to `completed`.

### Output Panel Behavior

- Summary panel shows:
  - Executive summary.
  - Client goals.
  - User needs.
  - Constraints.
  - Assumptions.
- Product description panel shows:
  - Product overview.
  - Target users.
  - Value proposition.
  - Key workflows.
  - Differentiators.
- Implementation requirements panel shows:
  - Functional requirements.
  - Non-functional requirements.
  - Technical requirements.
  - Data requirements.
  - Integration requirements.
  - Open questions.

### Error Paths

| Error | User Experience | Recovery |
| :--- | :--- | :--- |
| Google Doc inaccessible | Show message explaining document is private or invalid. | Connect Google account, change sharing settings, upload `.docx`, or paste text. |
| Empty document | Show empty-state message. | Ask user to provide a document with readable text. |
| Model unavailable | Show fallback notice. | Run extractive-only summary and rule-based extraction. |
| Long document | Show chunked progress. | Process in sections and merge outputs. |
| Network failure | Keep session in `pending` or `failed_retryable`. | Let user retry from same session. |

## Core User Journey: PPT Humanization

### Happy Path

1. User opens `/process/ppt`.
2. User uploads a `.pptx` file.
3. System validates:
   - File extension.
   - MIME type.
   - Size.
   - Parseability.
4. User selects cleanup sensitivity:
   - Conservative: only obvious artifacts and broken text.
   - Balanced: artifacts plus moderate AI-like style patterns.
   - Aggressive: artifacts, repetitive style, and broad rewrite suggestions.
5. User clicks `Analyze & Humanize`.
6. System creates a PPT session.
7. UI shows progress:
   - Parsing slides.
   - Extracting text.
   - Detecting citations and delimiters.
   - Computing style metrics.
   - Flagging risky segments.
   - Generating rewrite suggestions.
   - Checking semantic similarity.
8. User lands on `/review/ppt/[id]`.
9. Review page displays slide-by-slide results:
   - Slide thumbnail or slide number.
   - Original text.
   - Flags.
   - Quality signal scores.
   - Suggested rewrite.
   - Accept, reject, edit controls.
10. User accepts or edits changes.
11. User clicks `Export Clean PPT`.
12. System applies accepted rewrites to a copy of the original deck.
13. User downloads cleaned `.pptx`.

## PPT Review Screen

### Layout

- Left panel:
  - Slide list.
  - Status badges for each slide.
  - Counts of accepted, rejected, and pending changes.
- Center panel:
  - Original text grouped by slide and shape.
  - Highlighted flagged segments.
- Right panel:
  - Suggested rewrite.
  - Explanation of detected issues.
  - Semantic preservation indicator.
  - Accept/reject/edit actions.

### Flag Types

- `citation_artifact`
- `delimiter_artifact`
- `special_character`
- `markdown_residue`
- `low_burstiness`
- `high_repetition`
- `low_lexical_diversity`
- `generic_ai_phrase`
- `punctuation_density`
- `semantic_risk`

### Score Presentation

The UI must avoid saying “this is AI-generated.” It should use language like:

- “This sentence has low variation.”
- “This phrase looks templated.”
- “Citation artifact detected.”
- “Rewrite recommended for presentation polish.”
- “Semantic risk: review before accepting.”

## Settings Flow

User opens `/settings` and can configure:

- Model mode:
  - Local CPU.
  - Local GPU.
  - Extractive only.
  - User-hosted endpoint.
- Summarization model.
- Perplexity reference model.
- Embedding model.
- PPT cleanup sensitivity.
- Whether to store original source files.
- Auto-delete sessions after selected number of days.
- Google account connection.

## Session Lifecycle

| Status | Meaning |
| :--- | :--- |
| `created` | Session initialized. |
| `validating` | Input validation in progress. |
| `extracting` | Document or PPT text extraction in progress. |
| `analyzing` | NLP analysis in progress. |
| `rewriting` | Rewrite or summary generation in progress. |
| `review_required` | PPT suggestions ready for user review. |
| `exporting` | Clean output being generated. |
| `completed` | Output ready. |
| `failed_retryable` | Error occurred but user can retry. |
| `failed_final` | Error cannot be recovered without new input. |
| `deleted` | Session and files removed. |

## Empty States

- **No sessions**: “No documents processed yet. Start with a Google Doc or PPT.”
- **No flags in PPT**: “No major artifacts or style issues detected. You can still review the extracted text.”
- **No Google connection**: “Connect Google to import private Docs, or upload `.docx` instead.”
- **No model available**: “Local model not found. Run extractive-only mode or configure model path.”

## Redirect Logic

| Trigger | Destination |
| :--- | :--- |
| Unauthenticated user in hosted mode opens protected route | `/login?redirect=current_path` |
| Login success | Original redirect target or `/dashboard` |
| Google OAuth success | `/settings?connected=google` or return to doc processor |
| Doc processing complete | Stay on `/process/doc` and render results |
| PPT analysis complete | `/review/ppt/[id]` |
| PPT export complete | Stay on review page and show download button |
| Session deleted | `/dashboard` |

## Loading and Progress States

Processing can be slow because local small models may run on CPU. The UI must show clear progress and avoid appearing frozen.

- Use step-based progress labels.
- Show approximate stage, not fake exact percentages.
- Allow user to leave and reopen the session.
- Save intermediate status after each pipeline stage.
- Show fallback mode notice if the system switched from SLM to extractive-only.

## User Control Requirements

- User can cancel a queued or running session where technically possible.
- User can retry failed sessions.
- User can edit generated document outputs before download.
- User can accept or reject every PPT rewrite.
- User can delete session data and source files.

