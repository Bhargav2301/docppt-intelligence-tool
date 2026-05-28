import pytest
from app.humanizer.judge import judge_candidates, _get_entities, _has_british_spelling

def test_has_british_spelling():
    assert _has_british_spelling("We should optimise the colour.") is True
    assert _has_british_spelling("We should optimize the color.") is False

def test_get_entities():
    # Capitalized words that are not the first word of a sentence
    text = "The company is based in London and Paris."
    entities = _get_entities(text)
    assert "london" in entities
    assert "paris" in entities
    assert "the" not in entities  # First word of sentence

def test_judge_rejects_emojis():
    original = "Simplify the project workflow."
    candidates = [
        {"text": "Simplify the project workflow 🎨", "notes": "Emoji added", "estimated_ai_likeness_delta": -0.3},
        {"text": "Streamline the workflow.", "notes": "Clean rewrite", "estimated_ai_likeness_delta": -0.1}
    ]
    res = judge_candidates(candidates, original, {"max_chars": 80, "slide_role": "body"})
    # The emoji one must be rejected, and the clean one accepted
    assert "🎨" not in res["selected_text"]
    assert res["selected_text"] == "Streamline the workflow."
    assert res["decision"] == "accepted"

def test_judge_rejects_british_spelling():
    original = "Optimize this setup."
    candidates = [
        {"text": "Optimise this setup.", "notes": "British spelling", "estimated_ai_likeness_delta": -0.4},
        {"text": "Streamline this setup.", "notes": "American spelling", "estimated_ai_likeness_delta": -0.2}
    ]
    res = judge_candidates(candidates, original, {"max_chars": 80, "slide_role": "body"})
    # The British one must be rejected, and the American one accepted
    assert res["selected_text"] == "Streamline this setup."

def test_judge_rejects_number_modifications():
    original = "Increase sales by 15% in Q3."
    candidates = [
        {"text": "Increase sales by 20% in Q3.", "notes": "Number changed", "estimated_ai_likeness_delta": -0.5},
        {"text": "Grow sales by 15% during Q3.", "notes": "Correct numbers", "estimated_ai_likeness_delta": -0.2}
    ]
    res = judge_candidates(candidates, original, {"max_chars": 80, "slide_role": "body"})
    assert res["selected_text"] == "Grow sales by 15% during Q3."

def test_judge_rejects_new_entities():
    original = "The platform works with AWS."
    candidates = [
        {"text": "The platform works with Azure.", "notes": "Entity changed", "estimated_ai_likeness_delta": -0.5},
        {"text": "It integrates with AWS.", "notes": "Entity preserved", "estimated_ai_likeness_delta": -0.2}
    ]
    res = judge_candidates(candidates, original, {"max_chars": 80, "slide_role": "body"})
    assert res["selected_text"] == "It integrates with AWS."
