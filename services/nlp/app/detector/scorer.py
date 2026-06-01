"""Weighted scoring and band assignment for AI-likeness detection.

Implements the v2 instruction-spec additive model with per-feature weights,
short-text dampening, and three-band classification (low / moderate / high).
"""

from __future__ import annotations

import re

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

def is_url(text: str) -> bool:
    clean = text.strip()
    if " " in clean:
        return False
    if "@" in clean:
        return True
    if clean.lower().startswith(("www.", "http://", "https://")):
        return True
    if re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,6}(?:/.*)?$', clean):
        return True
    return False

def is_metric_or_stat(text: str) -> bool:
    clean = text.strip()
    if not any(c.isdigit() for c in clean):
        return False
    
    stripped = re.sub(r'[\d%\$\+\-\/><=\.,:;!#\(\)]', '', clean)
    stripped_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]+\b', stripped)]
    
    if not stripped_words:
        return True
        
    COMMON_STAT_LABELS = {
        "businesses", "regions", "days", "minutes", "mins", "hours", "hrs",
        "weeks", "months", "years", "slide", "slides", "pages", "page",
        "percent", "percentage", "sec", "seconds", "secs", "people", "clients",
        "users", "customers", "countries", "regions", "offices", "sites", "sources", "buyers",
        "quotations", "quoted"
    }
    
    if len(stripped_words) <= 2 and all(w in COMMON_STAT_LABELS for w in stripped_words):
        return True
        
    return False

def is_short_label(text: str) -> bool:
    words = text.strip().split()
    if len(words) <= 3:
        lower_words = [w.lower() for w in words]
        common_verbs = {"is", "are", "was", "were", "has", "have", "do", "does", "been", "go", "went"}
        if not any(v in lower_words for v in common_verbs):
            return True
    return False

def compute_ai_likeness(text: str, intensity: str = "balanced") -> AILikenessResult:
    """Compute the AI-likeness score for *text*.

    Steps:
        1. Compute all individual feature scores.
        2. Combine via weighted additive model (v2 spec weights).
        3. Apply short-text dampening.
        4. Assign qualitative band.
        5. Generate human-readable reasons.

    Args:
        text: The input text to evaluate.
        intensity: The rewrite intensity context (minimal / balanced / strong).

    Returns:
        An :class:`AILikenessResult` containing score, band, reasons,
        and the raw feature values.
    """
    # ------------------------------------------------------------------
    # 0. Pre-classification bypass checks
    # ------------------------------------------------------------------
    if is_url(text) or is_metric_or_stat(text) or is_short_label(text):
        return AILikenessResult(
            score=0.0,
            band="low",
            reasons=[],
            feature_values=FeatureValues(
                sentence_count=1,
                avg_sentence_length=len(text.split()),
                sentence_length_std=0.0,
                type_token_ratio=1.0,
                flesch_kincaid=0.0,
                trigram_repeat_rate=0.0,
                generic_phrase_density=0.0,
                passive_voice_ratio=0.0,
                vague_modifier_ratio=0.0,
                repeated_opener_ratio=0.0,
            )
        )

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

    # Scale down score for concrete, factual narrative prose (no generic phrases and low vague modifiers ratio)
    is_narrative = (generic == 0.0 and specificity <= 0.05)
    if is_narrative:
        score = score * 0.2

    # ------------------------------------------------------------------
    # 3. Short-text dampening
    # ------------------------------------------------------------------
    word_count = len(text.split())
    if intensity == "strong":
        # Under strong intensity, we want to flag AI promotional copy even in headings/bullet points
        if word_count < 5:
            score = min(score, 0.5)
        # No other dampening or much higher limits!
    elif intensity == "minimal":
        if word_count < 12:
            score = min(score, 0.2)
        elif word_count < 25:
            score = score * 0.5
    else:  # balanced
        if word_count < 8:
            # Short titles / headings: never classify as "high"
            score = min(score, 0.33)
        elif word_count < 20:
            # Brief text: reduce score to avoid false positives
            score = score * 0.7

    # ------------------------------------------------------------------
    # 4. Band assignment
    # ------------------------------------------------------------------
    if is_narrative:
        band = "low"
    elif intensity == "strong":
        # Lower thresholds so more things get flagged under "strong"
        if score <= 0.15:
            band = "low"
        elif score <= 0.40:
            band = "moderate"
        else:
            band = "high"
    elif intensity == "minimal":
        # Higher thresholds so fewer things get flagged under "minimal"
        if score <= 0.45:
            band = "low"
        elif score <= 0.75:
            band = "moderate"
        else:
            band = "high"
    else:  # balanced / default
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
