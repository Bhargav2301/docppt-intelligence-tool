from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any

from analysis.evaluator import calculate_similarity, calculate_perplexity
from runtime.config import HALLUCINATION_SIMILARITY_THRESHOLD

router = APIRouter(prefix="/api/eval", tags=["eval"])

class EvalRequest(BaseModel):
    source_text: str
    generated_text: str

class EvalResponse(BaseModel):
    similarity_score: float
    perplexity_score: Optional[float]
    hallucination_flag: Optional[Dict[str, Any]]

@router.post("/score", response_model=EvalResponse)
def score_generation(req: EvalRequest):
    """
    Evaluates the quality and fidelity of generated text against the original source.
    Flags hallucination risks if semantic similarity drops below a configured threshold.
    """
    similarity = calculate_similarity(req.source_text, req.generated_text)
    perplexity_data = calculate_perplexity(req.generated_text)
    
    hallucination_flag = None
    
    # Only flag if we actually ran the embedding model and got a score
    # (If similarity == 0.0 because the model is off, we don't want to falsely flag everything)
    if similarity > 0.0 and similarity < HALLUCINATION_SIMILARITY_THRESHOLD:
        hallucination_flag = {
            "type": "hallucination_risk",
            "severity": "high",
            "explanation": f"The generated text has a semantic similarity of {similarity:.2f}, which is below the threshold of {HALLUCINATION_SIMILARITY_THRESHOLD}. It may have drifted from the original meaning.",
            "recommendation": "Review the rewrite carefully for missing or altered facts."
        }
        
    return EvalResponse(
        similarity_score=similarity,
        perplexity_score=perplexity_data.get("perplexity"),
        hallucination_flag=hallucination_flag
    )
