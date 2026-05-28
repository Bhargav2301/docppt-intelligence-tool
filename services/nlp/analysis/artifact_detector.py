from typing import List, Dict, Any
from app.detector.rules import detect_artifacts as detect_rule_artifacts, clean_text_by_rules as clean_rule_text
from app.detector.schemas import ArtifactFlag

def detect_artifacts(text: str, paragraph_context: str = "") -> List[Dict[str, Any]]:
    """
    Thin wrapper delegating to app.detector.rules.
    """
    res = detect_rule_artifacts(text, paragraph_context)
    return [
        {
            "type": f.type,
            "severity": f.severity,
            "matched_text": f.span,
            "explanation": f"Mechanical artifact detected: '{f.span}'",
            "recommendation": f"Remove the leftover {f.type} pattern."
        }
        for f in res.artifact_flags
    ]

def clean_text_by_rules(text: str, flags: List[Dict[str, Any]]) -> str:
    """
    Thin wrapper delegating to app.detector.rules.
    """
    f_list = [
        ArtifactFlag(
            type=f["type"],
            span=f.get("matched_text", f.get("span", "")),
            severity=f["severity"]
        )
        for f in flags
    ]
    return clean_rule_text(text, f_list)
