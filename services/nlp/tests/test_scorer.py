import pytest
from app.detector.scorer import compute_ai_likeness

def test_scorer_bands():
    # Very short text (< 8 words) should never be high likeness (clamped to <= 0.33)
    short_title = "Streamline workflows and enhance synergy"
    res = compute_ai_likeness(short_title)
    assert res.band in ("low", "moderate")
    assert res.score <= 0.33
    
    # Generic business text (long enough to trigger higher score)
    generic_text = (
        "We enables seamless integration to streamline workflows and maximize efficiency. "
        "This holistic approach drives digital transformation across the enterprise, "
        "ensuring strategic alignment, competitive advantage, and stakeholder engagement. "
        "Additionally, it fosters innovation to optimize operations and minimize risk."
    )
    res_generic = compute_ai_likeness(generic_text)
    # Generic business fluff should have a higher likelihood score
    assert res_generic.score > 0.4
    assert len(res_generic.reasons) >= 1
    # Check that generic reasons list exists
    assert any("generic" in r.lower() for r in res_generic.reasons) or any("modifiers" in r.lower() for r in res_generic.reasons)

def test_scorer_intensity():
    # Very short text under strong intensity should not be clamped to 0.33 limit, and should get moderate band
    short_title = "Built to scale your manufacturing - not just run it."
    res_strong = compute_ai_likeness(short_title, intensity="strong")
    assert res_strong.band == "moderate"
    assert res_strong.score > 0.15

    # Short title under minimal intensity should have very low score
    res_minimal = compute_ai_likeness(short_title, intensity="minimal")
    assert res_minimal.band == "low"
    assert res_minimal.score < 0.25
