from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from app.detector.rules import detect_artifacts as detect_rule_artifacts
from app.detector.scorer import compute_ai_likeness

router = APIRouter(prefix="/api/ppt", tags=["ppt_analysis"])

class Segment(BaseModel):
    shape_id: str
    paragraph_index: int
    run_index: int
    original_text: str
    normalized_text: str
    flags: List[Dict[str, Any]] = []

class Slide(BaseModel):
    slide_index: int
    slide_number: int
    segments: List[Segment]

class DetectArtifactsRequest(BaseModel):
    total_slides: int
    total_segments: int
    slides: List[Slide]

@router.post("/detect_artifacts")
def detect_ppt_artifacts(req: DetectArtifactsRequest):
    """
    Takes the structured PPT data and applies rule-based detection for
    mechanical artifacts and qualitative AI-likeness bands.
    """
    for slide in req.slides:
        paragraph_texts = {}
        for seg in slide.segments:
            para_idx = seg.paragraph_index
            if para_idx not in paragraph_texts:
                paragraph_texts[para_idx] = ""
            paragraph_texts[para_idx] += seg.original_text + " "

        for seg in slide.segments:
            norm = seg.normalized_text.strip()
            if not norm:
                continue
            
            context_text = paragraph_texts.get(seg.paragraph_index, seg.original_text)
            
            # Rule-based artifacts
            art_res = detect_rule_artifacts(norm, paragraph_context=context_text)
            
            # AI likeness
            ai_res = compute_ai_likeness(norm)
            
            seg_flags = []
            
            # Add mechanical flags
            for flag in art_res.artifact_flags:
                seg_flags.append({
                    "type": flag.type,
                    "severity": flag.severity,
                    "span": flag.span,
                    "explanation": f"Mechanical artifact detected: '{flag.span}'",
                    "recommendation": f"Strip this {flag.type} before publishing."
                })
                
            # Add AI likeness flag
            if ai_res.band in ("moderate", "high"):
                seg_flags.append({
                    "type": "ai_likeness_risk",
                    "severity": "medium" if ai_res.band == "moderate" else "high",
                    "span": norm,
                    "explanation": f"AI-likeness band is {ai_res.band} (score: {ai_res.score}). Reasons: {', '.join(ai_res.reasons)}",
                    "recommendation": "Rewrite to sound more natural and conversational."
                })
            
            if seg_flags:
                seg.flags.extend(seg_flags)

    return req
