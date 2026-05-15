from fastapi import APIRouter, File, UploadFile, HTTPException
from typing import Dict, Any, List
from extraction.ppt_parser import extract_ppt_text

router = APIRouter(prefix="/api/ppt", tags=["ppt"])

@router.post("/extract")
async def extract_presentation(file: UploadFile = File(...)):
    """
    Extracts text from a .pptx file, preserving precise location metadata 
    (slide, shape, paragraph, and run indices) for future reconstruction.
    """
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported.")
        
    try:
        file_bytes = await file.read()
        extracted_data = extract_ppt_text(file_bytes)
        return extracted_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during PPT extraction: {str(e)}")
