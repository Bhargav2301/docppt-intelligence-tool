from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any

from analysis.doc_summarizer import generate_structured_summary, extract_product_description
from analysis.req_extractor import extract_requirements

router = APIRouter(prefix="/api/doc", tags=["analysis"])

class AnalyzeRequest(BaseModel):
    text: str
    source_title: str = "Untitled Document"

class AnalyzeResponse(BaseModel):
    source_title: str
    source_word_count: int
    structured_summary: str
    product_description: str
    implementation_requirements: Dict[str, List[Dict[str, Any]]]
    open_questions: List[str] = []
    assumptions: List[str] = []
    
    class Config:
        from_attributes = True

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_document(req: AnalyzeRequest):
    """
    Takes clean, extracted text and generates a structured summary, 
    a product description, and classifies implementation requirements.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Cannot analyze empty text.")
        
    word_count = len(req.text.split())
    
    summary = generate_structured_summary(req.text)
    product_desc = extract_product_description(req.text)
    requirements = extract_requirements(req.text)
    
    return AnalyzeResponse(
        source_title=req.source_title,
        source_word_count=word_count,
        structured_summary=summary,
        product_description=product_desc,
        implementation_requirements=requirements,
        open_questions=[],
        assumptions=["Generated via heuristic/SLM extraction and may miss implied requirements."]
    )
