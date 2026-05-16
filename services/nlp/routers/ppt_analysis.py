from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
from analysis.artifact_detector import detect_artifacts

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
    citations, markdown residue, delimiters, and bare URLs.
    Populates the 'flags' array for each segment without modifying the text.
    """
    for slide in req.slides:
        # Reconstruct paragraph text for better context scanning (e.g. for bare URLs)
        paragraph_texts = {}
        for seg in slide.segments:
            para_idx = seg.paragraph_index
            if para_idx not in paragraph_texts:
                paragraph_texts[para_idx] = ""
            paragraph_texts[para_idx] += seg.original_text + " "

        for seg in slide.segments:
            if not seg.normalized_text.strip():
                continue
            
            context_text = paragraph_texts.get(seg.paragraph_index, seg.normalized_text)
            new_flags = detect_artifacts(seg.normalized_text, paragraph_context=context_text)
            
            if new_flags:
                seg.flags.extend(new_flags)

    return req
