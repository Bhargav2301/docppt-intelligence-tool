from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from analysis.rewriter import generate_rewrite
from analysis.evaluator import calculate_similarity, calculate_perplexity
from runtime.config import REWRITE_MAX_EXPANSION, HALLUCINATION_SIMILARITY_THRESHOLD

router = APIRouter(prefix="/api/ppt", tags=["rewrite"])

class RewriteRequest(BaseModel):
    original_text: str
    tone: str = "professional"

class EvalScores(BaseModel):
    similarity_score: float
    perplexity_score: Optional[float]
    hallucination_flag: Optional[Dict[str, Any]]

class RewriteResponse(BaseModel):
    final_text: str
    flags: List[Dict[str, Any]] = []
    eval_scores: Optional[EvalScores] = None

@router.post("/rewrite", response_model=RewriteResponse)
def rewrite_segment(req: RewriteRequest):
    """
    Generates an AI rewrite of the provided text.
    Enforces strict length constraints (discarding rewrites that overflow).
    Evaluates the final result against the original for hallucinations.
    """
    flags = []
    
    # 1. Generate the rewrite
    rewritten_text = generate_rewrite(req.original_text, tone=req.tone)
    
    if not rewritten_text:
        # Fallback if generation fails or is disabled
        return RewriteResponse(final_text=req.original_text, flags=[])
        
    # 2. Enforce length constraint
    len_original = len(req.original_text)
    len_rewrite = len(rewritten_text)
    
    if len_original > 0 and len_rewrite > (REWRITE_MAX_EXPANSION * len_original):
        # Discard rewrite
        final_text = req.original_text
        flags.append({
            "type": "length_overflow",
            "severity": "low",
            "explanation": f"Proposed rewrite was {(len_rewrite/len_original - 1)*100:.1f}% longer than the original (exceeding the {REWRITE_MAX_EXPANSION*100 - 100}% limit) and was discarded to avoid overflowing the slide."
        })
        return RewriteResponse(final_text=final_text, flags=flags)
        
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
        hallucination_flag=hallucination_flag
    )
    
    return RewriteResponse(
        final_text=final_text,
        flags=flags,
        eval_scores=eval_scores
    )
