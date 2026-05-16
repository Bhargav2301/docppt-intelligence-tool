import re
from typing import List, Dict, Any

def detect_artifacts(text: str, paragraph_context: str = "") -> List[Dict[str, Any]]:
    """
    Detects mechanical artifacts (citations, markdown, noise, bare URLs) in text.
    Returns a list of flag objects.
    `paragraph_context` is the full paragraph text to check surrounding context (e.g., for bare URLs).
    """
    flags = []
    if not text:
        return flags

    # 1. Citation Artifacts
    # Match [1], [12], Source:, †, ‡
    citation_patterns = [
        r'\[\d+\]',
        r'Source:',
        r'Citation needed',
        r'\u2020', # Dagger
        r'\u2021'  # Double dagger
    ]
    for pattern in citation_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            flags.append({
                "type": "citation_artifact",
                "severity": "high",
                "matched_text": match.group(0),
                "explanation": "Citation marker or placeholder appears to be leftover copied text.",
                "recommendation": "Remove the marker or replace it with a real citation."
            })

    # 2. Markdown Residue
    markdown_patterns = [
        r'\*\*.*?\*\*', # Bold
        r'\_.*?\_',     # Italic (underscores)
        r'`.*?`',       # Inline code
    ]
    for pattern in markdown_patterns:
        for match in re.finditer(pattern, text):
            # To avoid flagging legit math or punctuation, ensure it actually matched markdown-like boundaries
            matched = match.group(0)
            if len(matched) > 2:
                flags.append({
                    "type": "markdown_residue",
                    "severity": "medium",
                    "matched_text": matched,
                    "explanation": "Markdown formatting characters detected.",
                    "recommendation": "Remove markdown notation and apply native PowerPoint formatting if needed."
                })

    # 3. Delimiter and Noise Characters
    noise_patterns = [
        r'={4,}',
        r'-{4,}',
        r'\*{3,}',
        r'<+|>+'
    ]
    for pattern in noise_patterns:
        for match in re.finditer(pattern, text):
            flags.append({
                "type": "delimiter_artifact",
                "severity": "low",
                "matched_text": match.group(0),
                "explanation": "Unusual delimiter or repeated punctuation sequence detected.",
                "recommendation": "Remove noise characters to clean up the slide."
            })

    # 4. Bare URLs
    url_pattern = r'(https?://[^\s]+|www\.[^\s]+)'
    for match in re.finditer(url_pattern, text):
        url_text = match.group(0)
        # Check surrounding context for anchoring words
        context_to_search = paragraph_context if paragraph_context else text
        context_lower = context_to_search.lower()
        
        anchors = ["see", "reference", "for more details", "url:", "link:", "resource:", "attached here", "specified on this slide"]
        
        has_anchor = any(anchor in context_lower for anchor in anchors)
        
        if not has_anchor:
            flags.append({
                "type": "url_artifact",
                "severity": "medium",
                "matched_text": url_text,
                "explanation": "Raw/bare URL likely pasted from an AI tool or browser without context.",
                "recommendation": "Remove this raw URL or replace it with a shorter descriptor or a proper reference note."
            })

    return flags
