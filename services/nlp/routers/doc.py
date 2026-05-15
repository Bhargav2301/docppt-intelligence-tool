from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from extraction.docx_parser import extract_from_docx
from extraction.google_docs import extract_from_google_doc
from extraction.text_normalizer import normalize_text

router = APIRouter(prefix="/api/doc", tags=["doc"])

class ExtractionResponse(BaseModel):
    extracted_text: str
    source_type: str
    word_count: int

@router.post("/extract", response_model=ExtractionResponse)
async def extract_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None)
):
    """
    Extracts and normalizes text from an uploaded .docx file, a Google Docs URL, or raw pasted text.
    """
    extracted = ""
    source_type = "unknown"

    if file:
        if not file.filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="Only .docx files are supported for file upload.")
        file_bytes = await file.read()
        extracted = extract_from_docx(file_bytes)
        source_type = "docx"
    elif url:
        try:
            extracted = extract_from_google_doc(url)
            source_type = "google_doc"
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except NotImplementedError as e:
            raise HTTPException(status_code=501, detail=str(e))
    elif text:
        extracted = text
        source_type = "pasted_text"
    else:
        raise HTTPException(status_code=400, detail="Must provide either file, url, or text.")

    if not extracted.strip():
        raise HTTPException(status_code=400, detail="No readable text could be extracted from the input.")

    normalized = normalize_text(extracted)
    word_count = len(normalized.split())

    return ExtractionResponse(
        extracted_text=normalized,
        source_type=source_type,
        word_count=word_count
    )
