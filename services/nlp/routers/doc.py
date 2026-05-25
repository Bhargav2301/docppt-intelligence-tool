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
    file: Optional[UploadFile] = None,
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
from models import Session, User, DocOutput, File
from routers.auth import get_current_user
from datetime import datetime
import os
from analysis.doc_summarizer import generate_structured_summary, extract_product_description
from analysis.req_extractor import extract_requirements
from routers.sessions import SessionResponse
import uuid
import json
from typing import List

class ProcessResponse(BaseModel):
    session: dict
    output: dict

async def process_single_doc_internal(
    db: DBSession,
    user_id: int,
    file_bytes: Optional[bytes] = None,
    filename: Optional[str] = None,
    url: Optional[str] = None,
    text: Optional[str] = None,
    label: Optional[str] = None
) -> dict:
    input_type = "pasted_text"
    input_label = label or "Pasted Text"
    if file_bytes:
        input_type = "docx"
        input_label = filename or "Uploaded Word Document"
    elif url:
        input_type = "google_doc"
        input_label = url
    elif text and label:
        input_type = "pasted_text"
        input_label = label

    db_session = Session(
        user_id=user_id,
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
        if file_bytes:
            # Create doc upload dir and save source file
            doc_upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "doc")
            os.makedirs(doc_upload_dir, exist_ok=True)
            docx_path = os.path.join(doc_upload_dir, f"{db_session.id}.docx")
            with open(docx_path, "wb") as f:
                f.write(file_bytes)
            
            extracted = extract_from_docx(file_bytes)
        elif url:
            extracted = extract_from_google_doc(url)
        elif text:
            extracted = text

        if not extracted or not extracted.strip():
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

        # Log source file if uploaded as a file
        if file_bytes:
            db_file = File(
                session_id=db_session.id,
                user_id=user_id,
                file_role="source",
                file_type="docx",
                storage_path=docx_path,
                original_filename=filename or "document.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                size_bytes=len(file_bytes)
            )
            db.add(db_file)
            db.commit()

        return {
            "session_id": str(db_session.id),
            "input_label": input_label,
            "status": "completed",
            "word_count": word_count,
            "output": {
                "structured_summary": summary,
                "product_description": product_desc,
                "implementation_requirements": requirements,
                "word_count": word_count
            }
        }

    except Exception as e:
        db_session.status = "failed_final"
        db_session.error_message = str(e)
        db_session.completed_at = datetime.utcnow()
        db.commit()
        return {
            "session_id": str(db_session.id),
            "input_label": input_label,
            "status": "failed_final",
            "error_message": str(e)
        }

@router.post("/process", response_model=ProcessResponse)
async def process_document(
    file: Optional[UploadFile] = None,
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Synchronous full processing: Creates a DB session, extracts text,
    runs analysis, persists results to DB, and returns the whole payload.
    """
    file_bytes = None
    filename = None
    if file:
        if not file.filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="Only .docx supported.")
        file_bytes = await file.read()
        filename = file.filename

    res = await process_single_doc_internal(
        db=db,
        user_id=current_user.id,
        file_bytes=file_bytes,
        filename=filename,
        url=url,
        text=text
    )

    if res["status"] == "failed_final":
        raise HTTPException(status_code=400, detail=res.get("error_message", "Processing failed"))

    # Construct the SessionResponse-compatible structure for /process
    # Retrieve the DB session details
    db_session = db.query(Session).filter(Session.id == uuid.UUID(res["session_id"])).first()
    return ProcessResponse(
        session={
            "id": str(db_session.id),
            "session_type": db_session.session_type,
            "input_type": db_session.input_type,
            "input_label": db_session.input_label,
            "status": db_session.status,
            "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
            "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None
        },
        output=res["output"]
    )

class BatchDocItemResponse(BaseModel):
    session_id: str
    input_label: str
    status: str
    error_message: Optional[str] = None
    word_count: Optional[int] = None

@router.post("/batch-process", response_model=List[BatchDocItemResponse])
async def batch_process_document(
    files: Optional[List[UploadFile]] = None,
    urls: Optional[str] = Form(None),   # JSON-serialized list of URLs or objects {"url": "...", "label": "..."}
    texts: Optional[str] = Form(None),  # JSON-serialized list of objects {"text": "...", "label": "..."}
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Processes multiple documents in a single user action.
    Returns an array of session statuses.
    """
    results = []

    # 1. Process files
    if files:
        for file in files:
            if not file.filename.endswith(".docx"):
                results.append(BatchDocItemResponse(
                    session_id="",
                    input_label=file.filename,
                    status="failed_final",
                    error_message="Only .docx files are supported."
                ))
                continue
            try:
                file_bytes = await file.read()
                res = await process_single_doc_internal(
                    db=db,
                    user_id=current_user.id,
                    file_bytes=file_bytes,
                    filename=file.filename
                )
                results.append(BatchDocItemResponse(
                    session_id=res["session_id"],
                    input_label=res["input_label"],
                    status=res["status"],
                    error_message=res.get("error_message"),
                    word_count=res.get("word_count")
                ))
            except Exception as e:
                results.append(BatchDocItemResponse(
                    session_id="",
                    input_label=file.filename,
                    status="failed_final",
                    error_message=str(e)
                ))

    # 2. Process URLs
    if urls:
        try:
            url_entries = json.loads(urls)
            if not isinstance(url_entries, list):
                url_entries = [url_entries]
        except Exception:
            url_entries = [urls]

        for entry in url_entries:
            url_str = ""
            label_str = None
            if isinstance(entry, dict):
                url_str = entry.get("url", "")
                label_str = entry.get("label")
            else:
                url_str = str(entry)

            if not url_str.strip():
                continue

            try:
                res = await process_single_doc_internal(
                    db=db,
                    user_id=current_user.id,
                    url=url_str,
                    label=label_str
                )
                results.append(BatchDocItemResponse(
                    session_id=res["session_id"],
                    input_label=res["input_label"],
                    status=res["status"],
                    error_message=res.get("error_message"),
                    word_count=res.get("word_count")
                ))
            except Exception as e:
                results.append(BatchDocItemResponse(
                    session_id="",
                    input_label=url_str,
                    status="failed_final",
                    error_message=str(e)
                ))

    # 3. Process Texts
    if texts:
        try:
            text_entries = json.loads(texts)
            if not isinstance(text_entries, list):
                text_entries = [text_entries]
        except Exception:
            text_entries = []

        for entry in text_entries:
            text_str = ""
            label_str = "Pasted Text"
            if isinstance(entry, dict):
                text_str = entry.get("text", "")
                label_str = entry.get("label", "Pasted Text")
            else:
                text_str = str(entry)

            if not text_str.strip():
                continue

            try:
                res = await process_single_doc_internal(
                    db=db,
                    user_id=current_user.id,
                    text=text_str,
                    label=label_str
                )
                results.append(BatchDocItemResponse(
                    session_id=res["session_id"],
                    input_label=res["input_label"],
                    status=res["status"],
                    error_message=res.get("error_message"),
                    word_count=res.get("word_count")
                ))
            except Exception as e:
                results.append(BatchDocItemResponse(
                    session_id="",
                    input_label=label_str,
                    status="failed_final",
                    error_message=str(e)
                ))

    return results

