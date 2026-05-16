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

from sqlalchemy.orm import Session as DBSession
from fastapi import Depends
from database import get_db
from models import Session, User, DocOutput
from datetime import datetime
from analysis.doc_summarizer import generate_structured_summary, extract_product_description
from analysis.req_extractor import extract_requirements
from routers.sessions import SessionResponse
import uuid

class ProcessResponse(BaseModel):
    session: dict
    output: dict

@router.post("/process", response_model=ProcessResponse)
async def process_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    db: DBSession = Depends(get_db)
):
    """
    Synchronous full processing: Creates a DB session, extracts text,
    runs analysis, persists results to DB, and returns the whole payload.
    """
    # 1. Initialize Session
    user = db.query(User).filter(User.email == "local_user@example.com").first()
    if not user:
        raise HTTPException(status_code=500, detail="Default local user not found.")

    input_type = "pasted_text"
    input_label = "Pasted Text"
    if file:
        input_type = "docx"
        input_label = file.filename
    elif url:
        input_type = "google_doc"
        input_label = url

    db_session = Session(
        user_id=user.id,
        session_type="doc",
        input_type=input_type,
        input_label=input_label,
        status="validating",
        processing_started_at=datetime.utcnow()
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    try:
        # 2. Extract
        db_session.status = "extracting"
        db.commit()
        
        extracted = ""
        if file:
            if not file.filename.endswith(".docx"):
                raise ValueError("Only .docx supported.")
            file_bytes = await file.read()
            extracted = extract_from_docx(file_bytes)
        elif url:
            extracted = extract_from_google_doc(url)
        elif text:
            extracted = text

        if not extracted.strip():
            raise ValueError("No readable text could be extracted.")

        normalized = normalize_text(extracted)
        word_count = len(normalized.split())

        # 3. Analyze
        db_session.status = "analyzing"
        db.commit()

        summary = generate_structured_summary(normalized)
        product_desc = extract_product_description(normalized)
        requirements = extract_requirements(normalized)

        # 4. Save Output
        db_session.status = "completed"
        db_session.completed_at = datetime.utcnow()

        doc_output = DocOutput(
            session_id=db_session.id,
            structured_summary=summary,
            product_description=product_desc,
            implementation_requirements=requirements,
            word_count=word_count
        )
        db.add(doc_output)
        db.commit()

        return ProcessResponse(
            session={
                "id": str(db_session.id),
                "session_type": db_session.session_type,
                "input_type": db_session.input_type,
                "input_label": db_session.input_label,
                "status": db_session.status,
                "created_at": db_session.created_at.isoformat(),
                "completed_at": db_session.completed_at.isoformat()
            },
            output={
                "structured_summary": summary,
                "product_description": product_desc,
                "implementation_requirements": requirements,
                "word_count": word_count
            }
        )

    except Exception as e:
        db_session.status = "failed_final"
        db_session.error_message = str(e)
        db_session.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
