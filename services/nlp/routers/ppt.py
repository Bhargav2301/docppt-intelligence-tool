from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List
import json
import io
from extraction.ppt_parser import extract_ppt_text
from extraction.ppt_compiler import compile_ppt

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

@router.post("/compile")
async def compile_presentation(
    file: UploadFile = File(...),
    modifications: str = Form(...)
):
    """
    Takes an original .pptx file and a JSON string of modifications,
    applies the text replacements at the precise run level, and returns
    the modified .pptx file as a binary stream.
    """
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported.")
        
    try:
        mods_list = json.loads(modifications)
        if not isinstance(mods_list, list):
            raise ValueError("Modifications must be a JSON array.")
            
        file_bytes = await file.read()
        compiled_bytes = compile_ppt(file_bytes, mods_list)
        
        return StreamingResponse(
            io.BytesIO(compiled_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename=compiled_{file.filename}"}
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in modifications field.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during PPT compilation: {str(e)}")
