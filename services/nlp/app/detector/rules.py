"""Artifact detection rules — ported and extended from the legacy module.

Detects mechanical artifacts (citation residue, markdown leakage, delimiter
noise, bare URLs, placeholder text) **and** generation-framing leftovers
(e.g. ``"Certainly,"``, ``"Here's a refined version:"``).

Outputs use the new :class:`ArtifactFlag` / :class:`ArtifactResult` Pydantic
schemas defined in ``schemas.py``.
"""

from __future__ import annotations

import re
from typing import List

from .schemas import ArtifactFlag, ArtifactResult

# ---------------------------------------------------------------------------
# Pattern groups
# ---------------------------------------------------------------------------

_CITATION_PATTERNS: List[str] = [
    r'\[\d+\]',
    r'\[Artifact:\s*.*?\]',
    r'\[Draft\s+.*?\]',
    r'\(Ref:\s*.*?\)',
    r'Source:',
    r'Citation needed',
    r'\u2020',   # †  Dagger
    r'\u2021',   # ‡  Double dagger
]

_MARKDOWN_PATTERNS: List[str] = [
    r'\*\*.*?\*\*',   # Bold
    r'\_.*?\_',       # Italic (underscores)
    r'`.*?`',         # Inline code
]

_NOISE_PATTERNS: List[str] = [
    r'={4,}',
    r'-{4,}',
    r'\*{3,}',
    r'<{2,}|>{2,}',
]

_PLACEHOLDER_PATTERNS: List[str] = [
    r'\[\s*insert\s*.*?\]',
    r'\{\s*insert\s*.*?\}',
    r'<\s*insert\s*.*?>',
    r'\bTODO\b',
    r'\bTBD\b',
    r'\bplaceholder\b',
    r'\blorem\s+ipsum\b',
    r'\breplace\s+(?:this|these|with)\b',
    r'\byour\s+company\s+here\b',
]

# Case-sensitive bracketed placeholders (e.g. [City], [X%], [N])
_BRACKET_CS_PATTERN = r'\[\s*[A-Z][A-Za-z0-9\s/%_&,\-\u2014\u2013]*\s*\]'

# Case-insensitive bracketed keywords
_BRACKET_CI_PATTERN = (
    r'\[\s*(?:city|region|country|company|client|prospect|date|value|percent|'
    r'amount|n|x|y|a|b|insert|replace|todo|tbd)\b[^\]]*\]'
)

# NEW: Generation-framing leftovers
_GENERATION_FRAMING_PATTERNS: List[str] = [
    r"(?i)^Certainly[,.]",
    r"(?i)^Sure[,.]",
    r"(?i)^Of course[,.]",
    r"(?i)Here(?:'s| is) a (?:refined|revised|updated|improved|rewritten) version[:\.]?",
    r"(?i)^In conclusion[,]",
    r"(?i)^Overall[,]",
    r"(?i)^It is worth noting that\b",
    r"(?i)^To summarize[,]",
    r"(?i)^As an AI\b",
    r"(?i)^I'd be happy to\b",
    r"(?i)^Let me\b",
]

# URL pattern
_URL_PATTERN = r'(https?://[^\s]+|www\.[^\s]+)'

# Anchor words for bare-URL whitelisting
_URL_ANCHORS: List[str] = [
    "see", "reference", "for more details", "url:", "link:",
    "resource:", "attached here", "specified on this slide",
    "visit", "contact", "website", "sales", "email",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_artifacts(text: str, paragraph_context: str = "") -> ArtifactResult:
    """Detect mechanical and generation-framing artifacts in *text*.

    Args:
        text: The text passage to scan.
        paragraph_context: Optional broader paragraph for contextual
            whitelisting (e.g. bare-URL anchor words).

    Returns:
        An :class:`ArtifactResult` with all detected flags and a
        cleaned text candidate.
    """
    flags: List[ArtifactFlag] = []
    if not text:
        return ArtifactResult(artifact_flags=flags, clean_text_candidate=text or "")

    # 1. Citation artifacts ---------------------------------------------------
    for pattern in _CITATION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            matched_text = match.group(0)
            # Whitelist "Source: ABSOLIN"
            if matched_text.lower() == "source:" and re.search(
                r'source:\s*ABSOLIN', text, re.IGNORECASE
            ):
                continue
            flags.append(
                ArtifactFlag(type="citation_artifact", span=matched_text, severity="high")
            )

    # 2. Markdown residue -----------------------------------------------------
    for pattern in _MARKDOWN_PATTERNS:
        for match in re.finditer(pattern, text):
            matched = match.group(0)
            if len(matched) > 2:
                flags.append(
                    ArtifactFlag(type="markdown_residue", span=matched, severity="medium")
                )

    # 3. Delimiter / noise characters -----------------------------------------
    for pattern in _NOISE_PATTERNS:
        for match in re.finditer(pattern, text):
            flags.append(
                ArtifactFlag(type="delimiter_artifact", span=match.group(0), severity="low")
            )

    # 4. Bare URLs ------------------------------------------------------------
    for match in re.finditer(_URL_PATTERN, text):
        url_text = match.group(0)
        context = paragraph_context if paragraph_context else text
        context_lower = context.lower()

        # Simple domain-only URLs are branding, not artifacts
        url_no_scheme = url_text.replace("https://", "").replace("http://", "")
        parts = url_no_scheme.split("/")
        is_simple_domain = len(parts) <= 1 or (len(parts) == 2 and parts[1] == "")

        has_anchor = any(a in context_lower for a in _URL_ANCHORS)

        if not has_anchor and not is_simple_domain:
            flags.append(
                ArtifactFlag(type="url_artifact", span=url_text, severity="medium")
            )

    # 5. Placeholder / instruction text ---------------------------------------
    for pattern in _PLACEHOLDER_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            flags.append(
                ArtifactFlag(type="placeholder_text", span=match.group(0), severity="high")
            )

    # Case-sensitive bracketed placeholders
    for match in re.finditer(_BRACKET_CS_PATTERN, text):
        flags.append(
            ArtifactFlag(type="placeholder_text", span=match.group(0), severity="high")
        )

    # Case-insensitive bracketed keywords (deduplicate)
    flagged_spans = {f.span for f in flags}
    for match in re.finditer(_BRACKET_CI_PATTERN, text, re.IGNORECASE):
        matched_text = match.group(0)
        if matched_text not in flagged_spans:
            flags.append(
                ArtifactFlag(type="placeholder_text", span=matched_text, severity="high")
            )

    # 6. Generation-framing leftovers (NEW) -----------------------------------
    for pattern in _GENERATION_FRAMING_PATTERNS:
        for match in re.finditer(pattern, text):
            flags.append(
                ArtifactFlag(type="generation_framing", span=match.group(0), severity="medium")
            )

    # Build the clean text candidate
    clean = clean_text_by_rules(text, flags)

    return ArtifactResult(artifact_flags=flags, clean_text_candidate=clean)


def clean_text_by_rules(text: str, flags: List[ArtifactFlag]) -> str:
    """Strip detected artifacts from *text* using rule-based cleaning.

    Longer matches are replaced first to avoid partial-match artefacts.

    Args:
        text: Original text.
        flags: Detected :class:`ArtifactFlag` objects.

    Returns:
        Cleaned text with collapsed whitespace.
    """
    if not text or not flags:
        return text

    cleaned = text

    # Replace longer spans first to avoid substring collisions
    sorted_flags = sorted(flags, key=lambda f: len(f.span), reverse=True)

    for flag in sorted_flags:
        matched = flag.span
        if not matched:
            continue

        if flag.type in ("citation_artifact", "delimiter_artifact", "url_artifact", "generation_framing"):
            cleaned = cleaned.replace(matched, "")
        elif flag.type == "markdown_residue":
            inner = matched
            if inner.startswith("**") and inner.endswith("**"):
                inner = inner[2:-2]
            elif inner.startswith("_") and inner.endswith("_"):
                inner = inner[1:-1]
            elif inner.startswith("`") and inner.endswith("`"):
                inner = inner[1:-1]
            cleaned = cleaned.replace(matched, inner)
        # placeholder_text is intentionally left in place — the user must
        # replace it with real content; auto-removal would lose context.

    # Collapse runs of whitespace and trim
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned
