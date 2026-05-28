"""Pydantic models for the AI-likeness detection pipeline.

Defines the data contracts for artifact detection and AI-likeness scoring,
used across the detector subpackage and exposed to API consumers.
"""

from typing import List, Literal

from pydantic import BaseModel


class ArtifactFlag(BaseModel):
    """A single mechanical artifact detected in the text.

    Attributes:
        type: Category of the artifact (e.g. ``citation_artifact``,
              ``markdown_residue``, ``generation_framing``).
        span: The matched text span that triggered the flag.
        severity: Impact level — ``low``, ``medium``, or ``high``.
    """

    type: str
    span: str
    severity: Literal["low", "medium", "high"]


class ArtifactResult(BaseModel):
    """Aggregated result of artifact detection for a text passage.

    Attributes:
        artifact_flags: All detected artifact flags.
        clean_text_candidate: The text with detected artifacts stripped.
    """

    artifact_flags: List[ArtifactFlag]
    clean_text_candidate: str


class FeatureValues(BaseModel):
    """Raw feature values computed during AI-likeness scoring.

    Exposed so that downstream consumers (UI, API, debug tools) can
    inspect *why* a particular score was assigned.

    Attributes:
        sentence_length_std: Standard deviation of sentence lengths (in words).
        trigram_repeat_rate: 0-1 ratio of repeated tri-grams.
        type_token_ratio: Lexical diversity (unique words / total words).
        flesch_kincaid: Approximate Flesch-Kincaid grade level.
        generic_phrase_density: 0-1 density of generic business phrases.
        passive_voice_ratio: 0-1 passive-voice ratio (placeholder for MVP).
        vague_modifier_ratio: 0-1 ratio of vague modifiers to total words.
        sentence_count: Total number of sentences detected.
        avg_sentence_length: Average sentence length in words.
        repeated_opener_ratio: 0-1 ratio of sentences sharing an opener.
    """

    sentence_length_std: float
    trigram_repeat_rate: float
    type_token_ratio: float
    flesch_kincaid: float
    generic_phrase_density: float
    passive_voice_ratio: float
    vague_modifier_ratio: float
    sentence_count: int
    avg_sentence_length: float
    repeated_opener_ratio: float


class AILikenessResult(BaseModel):
    """Final AI-likeness assessment for a text passage.

    Attributes:
        score: 0-1 AI-likeness score (higher = more AI-like).
        band: Qualitative band — ``low``, ``moderate``, or ``high``.
        reasons: 1-5 human-readable explanations for the score.
        feature_values: The underlying feature values.
    """

    score: float
    band: Literal["low", "moderate", "high"]
    reasons: List[str]
    feature_values: FeatureValues


class DetectionResult(BaseModel):
    """Combined output of both artifact detection and AI-likeness scoring.

    This is the top-level return type for the full detection pipeline.

    Attributes:
        artifact_result: Mechanical artifact analysis.
        ai_likeness: AI-likeness score, band, and explanations.
    """

    artifact_result: ArtifactResult
    ai_likeness: AILikenessResult
