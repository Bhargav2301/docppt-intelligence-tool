# DocPPT Intelligence Tool

## Core Value
Convert client docs into product specs and clean AI-looking slide text into presentation-ready language without paying for LLM APIs.

## Target Users
- Product development consultants
- Technical content architects
- Indie hackers or solo founders

## Background
Product consultants and founders often receive messy Google Docs and AI-assisted PowerPoint decks. Manually converting docs into specs and cleaning up AI artifacts from PPTs is slow and expensive via paid LLMs. They need a fast, local-first tool that handles these tasks automatically.

## Requirements

### Validated
(None yet — ship to validate)

### Active
- [ ] Parse Google Docs, `.docx`, and pasted text
- [ ] Extract structured product descriptions and requirements
- [ ] Summarize docs locally
- [ ] Parse `.pptx` files and extract text cleanly
- [ ] Detect AI artifacts (citations, delimiters, etc.)
- [ ] Score PPT AI-likeness locally
- [ ] Provide humanized rewrite suggestions
- [ ] Clean PPT export with preserved layout
- [ ] Review UI for approving changes

### Out of Scope
- Perfect AI detection (scores are probabilistic)
- Full design automation/slide generation
- Enterprise document governance

## Constraints
- Must not require paid LLM APIs (Claude, OpenAI)
- Must run locally with free/small models
- Must preserve PPT layout and non-text elements
- Typical Google Doc processing under 3 minutes

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Local/Free Model Default | Avoid recurring API costs and improve privacy | — Pending |
| FastAPI Backend | Best suited for Python NLP ecosystem | — Pending |
| Next.js Frontend | Fast iteration and familiar stack | — Pending |

---
*Last updated: 2026-05-16 after initialization*
