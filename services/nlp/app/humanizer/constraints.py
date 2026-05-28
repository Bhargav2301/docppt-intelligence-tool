"""Export Safety Agent.

Enforces character limits, line break limits, and other layout safety rules
to prevent presentation slide overflows.
"""

from typing import Dict, Any

def estimate_char_limit(slide_role: str, original_length: int) -> int:
    """Estimates the character limit safety boundary for a slide run."""
    if original_length <= 0:
        return 0
        
    if slide_role == "title":
        return min(80, max(40, int(original_length * 1.1)))
    elif slide_role == "bullet":
        return min(120, max(60, int(original_length * 1.3)))
    elif slide_role == "body":
        return max(100, int(original_length * 1.3))
    else:  # speaker_note or fallback
        return int(original_length * 1.5)

def check_export_safety(
    original_text: str,
    rewritten_text: str,
    slide_role: str,
    char_limit: int = 0
) -> Dict[str, Any]:
    """
    Checks if the rewritten text is safe for slide export.
    
    Returns:
        Dict detailing safety band, character delta, and overflow risks.
    """
    limit = char_limit if char_limit > 0 else estimate_char_limit(slide_role, len(original_text))
    
    char_delta = len(rewritten_text) - len(original_text)
    
    # Check for layout overflow
    overflow_risk = False
    if limit > 0 and len(rewritten_text) > limit:
        overflow_risk = True
        
    # Check for line break expansions (adding multiple paragraphs/lines)
    orig_newlines = original_text.count("\n")
    rew_newlines = rewritten_text.count("\n")
    line_break_risk = False
    if rew_newlines > orig_newlines + 1:
        line_break_risk = True
        
    # Determine overall safety classification
    if overflow_risk:
        safety = "needs_shorter_option"
    elif line_break_risk:
        safety = "manual_review"
    else:
        safety = "safe_replace"
        
    return {
        "safety": safety,
        "char_delta": char_delta,
        "line_break_risk": line_break_risk,
        "overflow_risk": overflow_risk
    }
