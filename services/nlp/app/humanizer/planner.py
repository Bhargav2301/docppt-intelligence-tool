"""Humanization Strategy Agent.

Plans the rewrite approach based on AI-likeness assessment, detected
artifacts, slide role, and tone preset.
"""

from typing import Any, Dict, List

def plan_rewrite_strategy(
    text: str,
    ai_likeness_band: str,  # 'low', 'moderate', 'high'
    ai_likeness_reasons: List[str],
    artifact_flags: List[Dict[str, Any]],
    tone_preset: str,
    slide_role: str,  # 'title', 'bullet', 'body', 'speaker_note'
    char_limit: int = 0,
    intensity: str = "balanced"
) -> Dict[str, Any]:
    """
    Generates a rewrite plan based on slide role and AI-likeness diagnosis.
    
    Returns:
        Dict detailing action, strategy list, and constraint variables.
    """
    word_count = len(text.split())
    has_artifacts = len(artifact_flags) > 0
    
    # 1. Determine action level based on intensity and likeness
    if intensity == "strong":
        # In strong mode, even moderate likeness gets a full rewrite, and low gets a light edit if there are flags/AI patterns
        if ai_likeness_band == "low":
            action = "light_edit" if (has_artifacts or any(k in text.lower() for k in ["not just", "scale", "outgrown", "platform", "+", "vs"])) else "pass_through"
        elif ai_likeness_band == "moderate":
            action = "full_rewrite"
        else:  # High
            action = "full_rewrite"
    elif intensity == "minimal":
        # In minimal mode, only high likeness gets a light edit, moderate and low pass through
        if ai_likeness_band == "high":
            action = "light_edit"
        else:
            action = "pass_through"
    else:  # balanced
        if ai_likeness_band == "low":
            action = "pass_through"
        elif ai_likeness_band == "moderate":
            action = "light_edit"
        else:
            action = "full_rewrite"
        
    # Titles/Headings: restrict to light_edit max to avoid breaking layout/context, unless strong intensity is requested
    if slide_role == "title":
        if intensity == "strong" and ai_likeness_band != "low":
            action = "full_rewrite"
        else:
            action = "light_edit" if ai_likeness_band != "low" else "pass_through"

    # NEW: If the segment is flagged with any artifact, never fully pass_through in strong mode.
    if intensity == "strong" and action == "pass_through" and has_artifacts:
        action = "light_edit"

    # NEW: For slide roles that are NOT title/bullet (body copy, callouts), in strong mode,
    # a moderate band should always trigger full_rewrite, not light_edit
    if intensity == "strong" and slide_role in ("body", "callout") and ai_likeness_band == "moderate":
        action = "full_rewrite"

    # NEW: Protect internal/notes slides from rewrites entirely.
    if slide_role == "internal_note":
        action = "pass_through"

    # 2. Build strategies
    strategies = []
    if slide_role == "internal_note":
        strategies = []
    else:
        if has_artifacts:
            strategies.append("remove_mechanical_artifacts")
        
    if action == "light_edit":
        strategies.append("apply_editorial_normalization")
        if any("generic" in r.lower() for r in ai_likeness_reasons):
            strategies.append("replace_buzzwords")
    elif action == "full_rewrite":
        strategies.append("apply_editorial_normalization")
        strategies.append("restructure_sentences_for_flow")
        if slide_role == "bullet":
            strategies.append("compress_and_make_punchy")
        else:
            strategies.append("improve_readability_rhythm")

    # 3. Formulate constraints
    if char_limit <= 0:
        # Estimate safety boundary based on role
        if slide_role == "title":
            max_chars = max(80, int(len(text) * 1.1))
        elif slide_role == "bullet":
            max_chars = max(120, int(len(text) * 1.2))
        else:
            max_chars = int(len(text) * 1.3)
    else:
        max_chars = char_limit

    return {
        "action": action,
        "strategy": strategies,
        "constraints": {
            "max_chars": max_chars,
            "preserve_named_entities": True,
            "slide_role": slide_role,
            "tone_preset": tone_preset,
            "intensity": intensity
        }
    }
