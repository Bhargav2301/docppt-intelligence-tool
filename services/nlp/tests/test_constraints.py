import pytest
from app.humanizer.constraints import estimate_char_limit, check_export_safety

def test_estimate_char_limit():
    assert estimate_char_limit("title", 50) == 55 # 1.1x bounded between 40 and 80
    assert estimate_char_limit("bullet", 50) == 65 # 1.3x bounded between 60 and 120
    assert estimate_char_limit("body", 50) == 100 # max(100, 50*1.3)

def test_check_export_safety_safe():
    orig = "This is some original slide text."
    rew = "Original slide text is here."
    res = check_export_safety(orig, rew, "bullet")
    assert res["safety"] == "safe_replace"
    assert res["overflow_risk"] is False
    assert res["line_break_risk"] is False

def test_check_export_safety_overflow():
    orig = "Original text." # length 14
    # Estimate limit for bullet is min(120, max(60, 14*1.3)) = 60
    rew = "A very long rewrite that exceeds sixty characters of text to test layout overflow constraint."
    res = check_export_safety(orig, rew, "bullet")
    assert res["safety"] == "needs_shorter_option"
    assert res["overflow_risk"] is True

def test_check_export_safety_line_break():
    orig = "Hello world."
    rew = "Hello\nworld\nnew line."
    res = check_export_safety(orig, rew, "bullet")
    assert res["safety"] == "manual_review"
    assert res["line_break_risk"] is True
