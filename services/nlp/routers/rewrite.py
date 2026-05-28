from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from database import get_db
from analysis.rewriter import generate_rewrite
from analysis.evaluator import calculate_similarity, calculate_perplexity
from runtime.config import REWRITE_MAX_EXPANSION, HALLUCINATION_SIMILARITY_THRESHOLD
from runtime.crypto import decrypt_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ppt", tags=["rewrite"])

class RewriteRequest(BaseModel):
    original_text: str
    tone: str = "professional"

from app.humanizer.editorial_rules import apply_all_editorial_rules
from app.humanizer.constraints import check_export_safety

class EvalScores(BaseModel):
    similarity_score: float
    perplexity_score: Optional[float]
    hallucination_flag: Optional[Dict[str, Any]]
    safety: Optional[str] = None

class RewriteResponse(BaseModel):
    final_text: str
    flags: List[Dict[str, Any]] = []
    eval_scores: Optional[EvalScores] = None
    safety: Optional[str] = "safe_replace"
    change_notes: List[str] = []

@router.post("/rewrite", response_model=RewriteResponse)
def rewrite_segment(
    req: RewriteRequest,
    db: DBSession = Depends(get_db),
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Generates an AI rewrite of the provided text.
    Enforces strict length constraints (discarding rewrites that overflow).
    Evaluates the final result against the original for hallucinations.
    """
    flags = []
    
    # Decrypt API key if present
    gemini_api_key = None
    if x_gemini_api_key:
        try:
            gemini_api_key = decrypt_api_key(x_gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to decrypt X-Gemini-API-Key: {e}")
    
    # 1. Generate the rewrite
    rewritten_text = generate_rewrite(
        req.original_text,
        tone=req.tone,
        db=db,
        gemini_api_key=gemini_api_key
    )
    
    if not rewritten_text:
        # Fallback if generation fails or is disabled
        return RewriteResponse(final_text=req.original_text, flags=[], safety="safe_replace", change_notes=["No change."])
        
    # Apply editorial rules before any evaluation
    rewritten_text = apply_all_editorial_rules(rewritten_text)
    
    # 2. Enforce length constraint / check safety
    safety_res = check_export_safety(req.original_text, rewritten_text, "body")
    safety = safety_res.get("safety", "safe_replace")
    
    if safety == "needs_shorter_option":
        flags.append({
            "type": "length_overflow",
            "severity": "low",
            "explanation": "Proposed rewrite exceeded character limit and was discarded to avoid overflowing the slide."
        })
        return RewriteResponse(final_text=req.original_text, flags=flags, safety=safety, change_notes=["Discarded due to layout constraints."])
        
    if safety == "manual_review":
        flags.append({
            "type": "layout_overflow_risk",
            "severity": "medium",
            "explanation": "Rewrite introduces potential line break or layout overflow risk."
        })
        
    # Valid rewrite
    final_text = rewritten_text
    
    # 3. Evaluate the rewrite for semantic drift and perplexity
    similarity = calculate_similarity(req.original_text, final_text)
    perplexity_data = calculate_perplexity(final_text)
    
    hallucination_flag = None
    if similarity > 0.0 and similarity < HALLUCINATION_SIMILARITY_THRESHOLD:
        hallucination_flag = {
            "type": "hallucination_risk",
            "severity": "high",
            "explanation": f"The generated text has a semantic similarity of {similarity:.2f}, which is below the threshold of {HALLUCINATION_SIMILARITY_THRESHOLD}. It may have drifted from the original meaning.",
            "recommendation": "Review the rewrite carefully for missing or altered facts."
        }
        # Add to main flags array for UI convenience
        flags.append(hallucination_flag)
        
    eval_scores = EvalScores(
        similarity_score=similarity,
        perplexity_score=perplexity_data.get("perplexity"),
        hallucination_flag=hallucination_flag,
        safety=safety
    )
    
    return RewriteResponse(
        final_text=final_text,
        flags=flags,
        eval_scores=eval_scores,
        safety=safety,
        change_notes=["Rewritten for clarity"]
    )
