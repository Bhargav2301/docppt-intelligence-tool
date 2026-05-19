from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from typing import Dict, Any, List
import json
import io
import os
import uuid as uuid_mod
from datetime import datetime

from extraction.ppt_parser import extract_ppt_text
from extraction.ppt_compiler import compile_ppt
from analysis.artifact_detector import detect_artifacts
from analysis.rewriter import generate_rewrite
from analysis.evaluator import calculate_similarity, calculate_perplexity
from runtime.config import REWRITE_MAX_EXPANSION, HALLUCINATION_SIMILARITY_THRESHOLD
from database import get_db
from models import Session, User, PptOutput, PptSegment

router = APIRouter(prefix="/api/ppt", tags=["ppt"])

# Directory for temporarily persisting uploaded .pptx files so compile can re-read them
PPT_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "ppt")
os.makedirs(PPT_UPLOAD_DIR, exist_ok=True)

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

@router.post("/compile_session/{session_id}")
async def compile_session(session_id: str, modifications: str = Form(...), db: DBSession = Depends(get_db)):
    """
    Compile using the stored .pptx file for a given session.
    The frontend sends the accepted modifications JSON, and this endpoint
    reads the saved .pptx from disk, applies changes, and streams the result.
    """
    pptx_path = os.path.join(PPT_UPLOAD_DIR, f"{session_id}.pptx")
    if not os.path.exists(pptx_path):
        raise HTTPException(status_code=404, detail="Original .pptx file not found for this session.")
    
    try:
        mods_list = json.loads(modifications)
        if not isinstance(mods_list, list):
            raise ValueError("Modifications must be a JSON array.")
        
        with open(pptx_path, "rb") as f:
            file_bytes = f.read()
        
        compiled_bytes = compile_ppt(file_bytes, mods_list)
        
        return StreamingResponse(
            io.BytesIO(compiled_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={"Content-Disposition": f"attachment; filename=cleaned_{session_id[:8]}.pptx"}
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in modifications field.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import Optional

class BatchPptItemResponse(BaseModel):
    session_id: str
    filename: str
    status: str
    total_slides: Optional[int] = 0
    total_flags: Optional[int] = 0
    error: Optional[str] = None

async def process_single_ppt_internal(
    file_bytes: bytes,
    filename: str,
    sensitivity: str,
    db: DBSession
) -> Dict[str, Any]:
    """
    Internal helper that executes the E2E presentation humanization pipeline.
    """
    user = db.query(User).filter(User.email == "local_user@example.com").first()
    if not user:
        raise ValueError("Default local user not found.")
    
    db_session = Session(
        user_id=user.id,
        session_type="ppt",
        input_type="pptx",
        input_label=filename,
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
        
        # Save original .pptx to disk for later compilation
        pptx_path = os.path.join(PPT_UPLOAD_DIR, f"{db_session.id}.pptx")
        with open(pptx_path, "wb") as f:
            f.write(file_bytes)
        
        extracted_data = extract_ppt_text(file_bytes)
        
        # 3. Detect artifacts
        db_session.status = "analyzing"
        db.commit()
        
        total_flags = 0
        
        for slide in extracted_data.get("slides", []):
            # Build paragraph context map
            paragraph_texts = {}
            for seg in slide.get("segments", []):
                pi = seg.get("paragraph_index", 0)
                if pi not in paragraph_texts:
                    paragraph_texts[pi] = ""
                paragraph_texts[pi] += seg.get("original_text", "") + " "
            
            for seg in slide.get("segments", []):
                norm = seg.get("normalized_text", "").strip()
                if not norm:
                    continue
                
                context = paragraph_texts.get(seg.get("paragraph_index", 0), norm)
                new_flags = detect_artifacts(norm, paragraph_context=context)
                if new_flags:
                    seg.setdefault("flags", []).extend(new_flags)
                    total_flags += len(new_flags)
        
        # 4. Rewrite flagged segments
        db_session.status = "rewriting"
        db.commit()
        
        for slide in extracted_data.get("slides", []):
            for seg in slide.get("segments", []):
                flags = seg.get("flags", [])
                original = seg.get("original_text", "")
                
                if not flags or not original.strip():
                    seg["final_text"] = original
                    seg["decision"] = "no_change"
                    continue
                
                # Conservative: only strip artifacts, no generative rewrite
                if sensitivity == "conservative":
                    seg["final_text"] = original
                    seg["decision"] = "pending"
                    continue
                
                # Balanced / Aggressive: attempt generative rewrite
                try:
                    rewritten = generate_rewrite(original, tone="professional", db=db, session_id=db_session.id)
                    if not rewritten:
                        seg["final_text"] = original
                        seg["decision"] = "pending"
                        continue
                    
                    # Length constraint
                    if len(original) > 0 and len(rewritten) > (REWRITE_MAX_EXPANSION * len(original)):
                        seg["final_text"] = original
                        seg.setdefault("flags", []).append({
                            "type": "length_overflow",
                            "severity": "low",
                            "explanation": "Rewrite exceeded length limit and was discarded."
                        })
                        seg["decision"] = "pending"
                        continue
                    
                    # Semantic evaluation
                    similarity = calculate_similarity(original, rewritten)
                    if similarity > 0.0 and similarity < HALLUCINATION_SIMILARITY_THRESHOLD:
                        seg.setdefault("flags", []).append({
                            "type": "hallucination_risk",
                            "severity": "high",
                            "explanation": f"Similarity {similarity:.2f} is below threshold."
                        })
                    
                    seg["final_text"] = rewritten
                    seg["eval_scores"] = {"similarity": similarity}
                    seg["decision"] = "pending"
                    
                except Exception:
                    seg["final_text"] = original
                    seg["decision"] = "pending"
        
        # 5. Persist
        db_session.status = "completed"
        db_session.completed_at = datetime.utcnow()
        
        ppt_output = PptOutput(
            session_id=db_session.id,
            total_slides=extracted_data.get("total_slides", 0),
            total_flags=total_flags
        )
        db.add(ppt_output)
        db.flush()
        
        for slide in extracted_data.get("slides", []):
            for seg in slide.get("segments", []):
                db_seg = PptSegment(
                    ppt_output_id=ppt_output.id,
                    slide_index=slide.get("slide_index", 0),
                    shape_id=str(seg.get("shape_id", "")),
                    paragraph_index=seg.get("paragraph_index", 0),
                    run_index=seg.get("run_index", 0),
                    original_text=seg.get("original_text", ""),
                    normalized_text=seg.get("normalized_text", ""),
                    flags=seg.get("flags"),
                    eval_scores=seg.get("eval_scores"),
                    final_text=seg.get("final_text", seg.get("original_text", "")),
                    decision=seg.get("decision", "no_change"),
                )
                db.add(db_seg)
        
        db.commit()

        # Build File table logging for source .pptx
        db_file = File(
            session_id=db_session.id,
            user_id=user.id,
            file_role="source",
            file_type="pptx",
            storage_path=pptx_path,
            original_filename=filename,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            size_bytes=len(file_bytes)
        )
        db.add(db_file)
        db.commit()
        
        return {
            "session": {
                "id": str(db_session.id),
                "session_type": "ppt",
                "input_label": db_session.input_label,
                "status": "completed",
                "created_at": db_session.created_at.isoformat(),
                "completed_at": db_session.completed_at.isoformat(),
            },
            "data": extracted_data,
        }
    
    except Exception as e:
        db_session.status = "failed_final"
        db_session.error_message = str(e)
        db_session.completed_at = datetime.utcnow()
        db.commit()
        raise e

@router.post("/process")
async def process_presentation(
    file: UploadFile = File(...),
    sensitivity: str = Form("conservative"),
    db: DBSession = Depends(get_db)
):
    """
    Pipeline for a single presentation.
    """
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Only .pptx files are supported.")
    
    try:
        file_bytes = await file.read()
        return await process_single_ppt_internal(
            file_bytes=file_bytes,
            filename=file.filename,
            sensitivity=sensitivity,
            db=db
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-process", response_model=List[BatchPptItemResponse])
async def batch_process_presentation(
    files: List[UploadFile] = File(...),
    sensitivity: str = Form("conservative"),
    db: DBSession = Depends(get_db)
):
    """
    Pipeline for processing multiple presentations in a batch.
    Gracefully handles partial failures.
    """
    results = []
    
    for file in files:
        if not file.filename.endswith(".pptx"):
            results.append(BatchPptItemResponse(
                session_id="",
                filename=file.filename,
                status="failed",
                error="Only .pptx files are supported."
            ))
            continue
            
        try:
            file_bytes = await file.read()
            res = await process_single_ppt_internal(
                file_bytes=file_bytes,
                filename=file.filename,
                sensitivity=sensitivity,
                db=db
            )
            session_id = res["session"]["id"]
            results.append(BatchPptItemResponse(
                session_id=session_id,
                filename=file.filename,
                status="completed",
                total_slides=res["data"].get("total_slides", 0),
                total_flags=res["session"].get("total_flags", 0) # fallbacks to 0 if not set, or we can fetch total flags from the output
            ))
            # Let's dynamically fix total_flags by computing from res
            results[-1].total_flags = sum(
                len(seg.get("flags", [])) 
                for slide in res["data"].get("slides", []) 
                for seg in slide.get("segments", [])
            )
        except Exception as e:
            logger.error(f"Failed processing batch item {file.filename}: {str(e)}")
            results.append(BatchPptItemResponse(
                session_id="",
                filename=file.filename,
                status="failed",
                error=str(e)
            ))
            
    return results

