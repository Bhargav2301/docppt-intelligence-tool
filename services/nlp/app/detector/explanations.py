"""Human-readable reason generation for AI-likeness scores.

Produces 1-5 concise explanation strings that tell the user *why* a given
text received its score.  Only features whose individual score exceeds the
**0.3 threshold** are surfaced.
"""

from __future__ import annotations

from typing import Dict, List

from .features import (
    find_discourse_markers_present,
    find_generic_phrases_present,
    find_openers_present,
)


def generate_reasons(
    burstiness: float,
    repetition: float,
    generic: float,
    specificity: float,
    readability: float,
    syntactic: float,
    discourse: float,
    surface_features: Dict[str, float],
    text: str = "",
) -> List[str]:
    """Build a list of 1-5 human-readable reason strings.

    Each reason maps to a single feature group whose score exceeded 0.3.
    When the original *text* is supplied the reasons include concrete
    examples (e.g. the actual generic phrases that were found).

    Args:
        burstiness: Burstiness score (0-1).
        repetition: Repetition score (0-1).
        generic: Generic-phrase score (0-1).
        specificity: Specificity / vague-modifier score (0-1).
        readability: Readability regularisation score (0-1).
        syntactic: Syntactic-uniformity score (0-1).
        discourse: Discourse-template score (0-1).
        surface_features: Dict returned by ``compute_surface_features``.
        text: Original text (optional).  Needed to list specific phrases.

    Returns:
        A list of 1-5 explanation strings, ordered by score descending.
        If no feature exceeds 0.3 the list contains a single neutral
        reason: ``"No strong AI-likeness signals detected."``.
    """
    threshold = 0.3
    candidates: List[tuple[float, str]] = []

    # --- Burstiness ----------------------------------------------------------
    if burstiness > threshold:
        sent_count = int(surface_features.get("sentence_count", 0))
        candidates.append(
            (burstiness, f"Low sentence-length variance across {sent_count} sentences")
        )

    # --- Repetition ----------------------------------------------------------
    if repetition > threshold:
        candidates.append(
            (repetition, "Repeated bi-gram/tri-gram patterns detected")
        )

    # --- Generic phrases -----------------------------------------------------
    if generic > threshold:
        if text:
            found = find_generic_phrases_present(text)
            examples = ", ".join(f"'{p}'" for p in found[:3])
            candidates.append(
                (generic, f"Generic business phrases: {examples}")
            )
        else:
            candidates.append(
                (generic, "High density of generic business phrases")
            )

    # --- Specificity ---------------------------------------------------------
    if specificity > threshold:
        candidates.append(
            (specificity, "High ratio of vague modifiers; low concrete detail")
        )

    # --- Readability ---------------------------------------------------------
    if readability > threshold:
        candidates.append(
            (readability, "Overly uniform readability grade")
        )

    # --- Syntactic uniformity ------------------------------------------------
    if syntactic > threshold:
        if text:
            found = find_openers_present(text)
            examples = ", ".join(f"'{o}'" for o in found[:3])
            candidates.append(
                (syntactic, f"Repeated sentence openers: {examples}")
            )
        else:
            candidates.append(
                (syntactic, "Repeated sentence-opening patterns detected")
            )

    # --- Discourse templates -------------------------------------------------
    if discourse > threshold:
        if text:
            found = find_discourse_markers_present(text)
            examples = ", ".join(f"'{m}'" for m in found[:3])
            candidates.append(
                (discourse, f"Discourse template markers present: {examples}")
            )
        else:
            candidates.append(
                (discourse, "Discourse template / transition markers present")
            )

    # --- Fallback ------------------------------------------------------------
    if not candidates:
        return ["No strong AI-likeness signals detected."]

    # Sort descending by score, take top 5.
    candidates.sort(key=lambda t: t[0], reverse=True)
    return [reason for _, reason in candidates[:5]]
