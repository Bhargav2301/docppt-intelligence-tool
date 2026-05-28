"""Weighted scoring and band assignment for AI-likeness detection.

Implements the v2 instruction-spec additive model with per-feature weights,
short-text dampening, and three-band classification (low / moderate / high).
"""

from __future__ import annotations

from .explanations import generate_reasons
from .features import (
    compute_burstiness_score,
    compute_discourse_template_score,
    compute_generic_phrase_score,
    compute_readability_score,
    compute_repetition_score,
    compute_specificity_score,
    compute_surface_features,
    compute_syntactic_uniformity_score,
)
from .schemas import AILikenessResult, FeatureValues


def compute_ai_likeness(text: str) -> AILikenessResult:
    """Compute the AI-likeness score for *text*.

    Steps:
        1. Compute all individual feature scores.
        2. Combine via weighted additive model (v2 spec weights).
        3. Apply short-text dampening.
        4. Assign qualitative band.
        5. Generate human-readable reasons.

    Args:
        text: The input text to evaluate.

    Returns:
        An :class:`AILikenessResult` containing score, band, reasons,
        and the raw feature values.
    """
    # ------------------------------------------------------------------
    # 1. Compute individual feature scores
    # ------------------------------------------------------------------
    surface = compute_surface_features(text)
    burstiness = compute_burstiness_score(text)
    repetition = compute_repetition_score(text)
    generic = compute_generic_phrase_score(text)
    specificity = compute_specificity_score(text)
    readability = compute_readability_score(text)
    syntactic = compute_syntactic_uniformity_score(text)
    discourse = compute_discourse_template_score(text)
    perplexity_signal = 0.0  # No local model for MVP

    # ------------------------------------------------------------------
    # 2. Weighted additive scoring (v2 spec)
    # ------------------------------------------------------------------
    raw_score = (
        0.18 * burstiness
        + 0.17 * repetition
        + 0.15 * generic
        + 0.12 * specificity
        + 0.10 * readability
        + 0.10 * syntactic
        + 0.10 * discourse
        + 0.08 * perplexity_signal
    )

    # Clamp to [0, 1]
    score = max(0.0, min(1.0, raw_score))

    # ------------------------------------------------------------------
    # 3. Short-text dampening
    # ------------------------------------------------------------------
    word_count = len(text.split())
    if word_count < 8:
        # Short titles / headings: never classify as "high"
        score = min(score, 0.33)
    elif word_count < 20:
        # Brief text: reduce score to avoid false positives
        score = score * 0.7

    # ------------------------------------------------------------------
    # 4. Band assignment
    # ------------------------------------------------------------------
    if score <= 0.33:
        band = "low"
    elif score <= 0.66:
        band = "moderate"
    else:
        band = "high"

    # ------------------------------------------------------------------
    # 5. Reasons
    # ------------------------------------------------------------------
    reasons = generate_reasons(
        burstiness=burstiness,
        repetition=repetition,
        generic=generic,
        specificity=specificity,
        readability=readability,
        syntactic=syntactic,
        discourse=discourse,
        surface_features=surface,
        text=text,
    )

    # ------------------------------------------------------------------
    # 6. Pack feature values
    # ------------------------------------------------------------------
    feature_values = FeatureValues(
        sentence_count=int(surface["sentence_count"]),
        avg_sentence_length=surface["avg_sentence_length"],
        sentence_length_std=surface["sentence_length_std"],
        type_token_ratio=surface["type_token_ratio"],
        flesch_kincaid=round(readability * 20, 2),  # approximate re-scaling
        trigram_repeat_rate=repetition,
        generic_phrase_density=generic,
        passive_voice_ratio=0.0,  # placeholder for MVP
        vague_modifier_ratio=specificity,
        repeated_opener_ratio=syntactic,
    )

    return AILikenessResult(
        score=round(score, 2),
        band=band,
        reasons=reasons,
        feature_values=feature_values,
    )
