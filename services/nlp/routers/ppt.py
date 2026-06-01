from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)
import json
import io
import os
import uuid as uuid_mod
from datetime import datetime

from extraction.ppt_parser import extract_ppt_text
from extraction.ppt_compiler import compile_ppt
from analysis.template_similarity import check_template_similarity
from analysis.rewriter import generate_rewrite
from analysis.evaluator import calculate_similarity
from runtime.config import REWRITE_MAX_EXPANSION, HALLUCINATION_SIMILARITY_THRESHOLD
from runtime.upload_guard import validate_upload
from database import get_db
from models import Session, User, PptOutput, PptSegment, File as DbFile
from routers.auth import get_current_user
from runtime.crypto import decrypt_api_key
from app.detector.rules import detect_artifacts as detect_rule_artifacts, clean_text_by_rules
from app.detector.scorer import compute_ai_likeness
from app.humanizer.editorial_rules import apply_all_editorial_rules
from app.humanizer.constraints import check_export_safety

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
    try:
        file_bytes = await file.read()
        validate_upload(file, file_bytes, "pptx")
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
    try:
        mods_list = json.loads(modifications)
        if not isinstance(mods_list, list):
            raise ValueError("Modifications must be a JSON array.")

        # Apply editorial rules to every modification final text to ensure cleanliness
        for mod in mods_list:
            if "new_text" in mod:
                mod["new_text"] = apply_all_editorial_rules(mod["new_text"])

        file_bytes = await file.read()
        validate_upload(file, file_bytes, "pptx")
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
async def compile_session(
    session_id: str,
    modifications: str = Form(...),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compile using the stored .pptx file for a given session.
    """
    import uuid
    try:
        uuid_obj = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    db_session = db.query(Session).filter(Session.id == uuid_obj, Session.user_id == current_user.id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found or access denied.")

    pptx_path = os.path.join(PPT_UPLOAD_DIR, f"{session_id}.pptx")
    if not os.path.exists(pptx_path):
        raise HTTPException(status_code=404, detail="Original .pptx file not found for this session.")
    
    try:
        mods_list = json.loads(modifications)
        if not isinstance(mods_list, list):
            raise ValueError("Modifications must be a JSON array.")
        
        # Apply editorial rules to every modification text before compiling
        for mod in mods_list:
            if "new_text" in mod:
                mod["new_text"] = apply_all_editorial_rules(mod["new_text"])
        
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
    file_path: str,
    filename: str,
    sensitivity: str,
    db: DBSession,
    current_user: User,
    intensity: str = "balanced",
    tone_preset: str = "presentation_concise",
    gemini_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Internal helper that executes the E2E presentation humanization pipeline.
    """
    db_session = Session(
        user_id=current_user.id,
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
        import shutil
        shutil.copy2(file_path, pptx_path)
        
        extracted_data = extract_ppt_text(pptx_path)
        
        # 3. Detect artifacts & AI Likeness
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
                
                # Rule-based artifacts
                art_res = detect_rule_artifacts(norm, paragraph_context=context)
                
                # AI Likeness
                ai_res = compute_ai_likeness(norm, intensity=intensity)
                
                # Assign slide/shape role if possible
                role = seg.get("role", "body")
                
                seg_flags = []
                
                # Add mechanical flags
                for flag in art_res.artifact_flags:
                    seg_flags.append({
                        "type": flag.type,
                        "severity": flag.severity,
                        "span": flag.span,
                        "explanation": f"Mechanical artifact detected: '{flag.span}'",
                        "recommendation": f"Strip this {flag.type} before publishing."
                    })
                    
                # Add AI likeness warning flag
                if ai_res.band in ("moderate", "high"):
                    import re
                    from app.detector.features import find_generic_phrases_present, VAGUE_MODIFIERS, find_discourse_markers_present
                    
                    found_any_specific = False
                    
                    # Highlight generic phrases
                    found_generics = find_generic_phrases_present(norm)
                    for gp in found_generics:
                        orig_match = re.search(rf'\b{re.escape(gp)}\b', norm, re.IGNORECASE)
                        span_val = orig_match.group(0) if orig_match else gp
                        seg_flags.append({
                            "type": "generic_business_phrase",
                            "severity": "medium" if ai_res.band == "moderate" else "high",
                            "span": span_val,
                            "explanation": f"Generic business phrase detected: '{span_val}'",
                            "recommendation": "Replace with a concrete capability statement or specific business metric."
                        })
                        found_any_specific = True
                        
                    # Highlight vague modifiers
                    found_vague = [w for w in re.findall(r'\b[a-zA-Z]+\b', norm.lower()) if w in VAGUE_MODIFIERS]
                    seen_vague = set()
                    for vm in found_vague:
                        if vm not in seen_vague:
                            seen_vague.add(vm)
                            orig_match = re.search(rf'\b{re.escape(vm)}\b', norm, re.IGNORECASE)
                            span_val = orig_match.group(0) if orig_match else vm
                            seg_flags.append({
                                "type": "vague_modifier",
                                "severity": "medium",
                                "span": span_val,
                                "explanation": f"Vague modifier detected: '{span_val}'",
                                "recommendation": "Replace with a specific, quantitative metric."
                            })
                            found_any_specific = True
                            
                    # Highlight discourse markers
                    found_discourse = find_discourse_markers_present(norm)
                    for dm in found_discourse:
                        orig_match = re.search(rf'\b{re.escape(dm)}\b', norm, re.IGNORECASE)
                        span_val = orig_match.group(0) if orig_match else dm
                        seg_flags.append({
                            "type": "robotic_transition",
                            "severity": "medium",
                            "span": span_val,
                            "explanation": f"Robotic transition/discourse marker detected: '{span_val}'",
                            "recommendation": "Remove or simplify this transition."
                        })
                        found_any_specific = True
                        
                    # Fallback general flag if no specific pattern was extracted but score is high
                    if not found_any_specific:
                        seg_flags.append({
                            "type": "ai_likeness_risk",
                            "severity": "medium" if ai_res.band == "moderate" else "high",
                            "span": norm,
                            "explanation": f"AI-likeness band is {ai_res.band} (score: {ai_res.score}). Reasons: {', '.join(ai_res.reasons)}",
                            "recommendation": "Rewrite to sound more natural and conversational."
                        })
                
                if seg_flags:
                    seg.setdefault("flags", []).extend(seg_flags)
                    total_flags += len(seg_flags)

        # Cross-session template/slide similarity checks
        try:
            similarity_matches = check_template_similarity(
                db, 
                current_user.id, 
                extracted_data.get("slides", []),
                current_filename=filename
            )
            
            for slide in extracted_data.get("slides", []):
                slide_idx = slide.get("slide_index", 0)
                if slide_idx in similarity_matches:
                    match = similarity_matches[slide_idx]
                    for seg in slide.get("segments", []):
                        if seg.get("original_text", "").strip():
                            sim_flag = {
                                "type": "template_similarity_risk",
                                "severity": "medium",
                                "matched_text": seg.get("original_text", ""),
                                "explanation": f"This slide matches a template previously used in '{match['matched_filename']}' (Slide {match['matched_slide_idx'] + 1}).",
                                "recommendation": "Customize this slide's content specifically to avoid generic template fatigue."
                            }
                            seg.setdefault("flags", []).append(sim_flag)
                            total_flags += 1
                            break
        except Exception as sim_err:
            logger.error(f"Error executing template similarity check: {str(sim_err)}")
        
        # 4. Rewrite flagged segments
        db_session.status = "rewriting"
        db.commit()
        
        for slide in extracted_data.get("slides", []):
            for seg in slide.get("segments", []):
                flags = seg.get("flags", [])
                original = seg.get("original_text", "")
                
                if not flags or not original.strip():
                    seg["final_text"] = apply_all_editorial_rules(original)
                    seg["decision"] = "no_change"
                    continue
                
                # Conservative: only strip artifacts & enforce editorial rules
                if sensitivity == "conservative" and intensity != "strong":
                    art_flags = detect_rule_artifacts(original).artifact_flags
                    cleaned = clean_text_by_rules(original, art_flags)
                    seg["final_text"] = apply_all_editorial_rules(cleaned)
                    seg["decision"] = "pending"
                    continue
                
                # Balanced / Aggressive: attempt generative rewrite
                try:
                    rewritten = generate_rewrite(
                        original,
                        tone=tone_preset,
                        db=db,
                        session_id=db_session.id,
                        gemini_api_key=gemini_api_key,
                        intensity=intensity
                    )
                    
                    if not rewritten:
                        seg["final_text"] = apply_all_editorial_rules(original)
                        seg["decision"] = "pending"
                        continue
                    
                    role = seg.get("role", "body")
                    safety_res = check_export_safety(original, rewritten, role)
                    safety = safety_res.get("safety", "safe_replace")
                    
                    if safety == "needs_shorter_option":
                        seg["final_text"] = apply_all_editorial_rules(original)
                        seg.setdefault("flags", []).append({
                            "type": "length_overflow",
                            "severity": "low",
                            "explanation": f"Proposed rewrite was too long for slide {role} layout and was discarded.",
                            "safety": "needs_shorter_option"
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
                        
                    if safety == "manual_review":
                        seg.setdefault("flags", []).append({
                            "type": "layout_overflow_risk",
                            "severity": "medium",
                            "explanation": "Rewrite introduces potential line break or layout overflow risk."
                        })
                    
                    seg["final_text"] = apply_all_editorial_rules(rewritten)
                    seg["eval_scores"] = {"similarity": similarity, "safety": safety}
                    seg["decision"] = "pending"
                    
                except Exception as rew_err:
                    logger.error(f"Error during segment rewrite: {rew_err}")
                    seg["final_text"] = apply_all_editorial_rules(original)
                    seg["decision"] = "pending"
        
        # 5. Persist
        db_session.status = "completed"
        db_session.completed_at = datetime.utcnow()
        
        # Post-process segment decisions
        cleaned_total_flags = 0
        for slide in extracted_data.get("slides", []):
            for seg in slide.get("segments", []):
                original = seg.get("original_text", "")
                final = seg.get("final_text", original)
                flags = seg.get("flags", [])
                if final == original and not flags:
                    seg["flags"] = []
                    seg["decision"] = "no_change"
                    seg["final_text"] = apply_all_editorial_rules(original)
                else:
                    if flags:
                        seg["decision"] = "pending"
                    cleaned_total_flags += len(flags)
        total_flags = cleaned_total_flags

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
        db_file = DbFile(
            session_id=db_session.id,
            user_id=current_user.id,
            file_role="source",
            file_type="pptx",
            storage_path=pptx_path,
            original_filename=filename,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            size_bytes=os.path.getsize(pptx_path)
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

import tempfile

async def save_upload_file_tmp(upload_file: UploadFile) -> str:
    from runtime.upload_guard import MAX_UPLOAD_BYTES, _OOXML_MAGIC, _ALLOWED
    spec = _ALLOWED.get("pptx")
    if spec is None:
        raise HTTPException(status_code=500, detail="Unknown upload kind: pptx")

    filename = (upload_file.filename or "").lower()
    if not filename.endswith(spec["extensions"]):
        raise HTTPException(
            status_code=400,
            detail=f"Only {', '.join(spec['extensions'])} files are supported.",
        )

    try:
        suffix = os.path.splitext(upload_file.filename)[1]
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        total_size = 0
        is_first_chunk = True

        with os.fdopen(fd, "wb") as tmp_file:
            while True:
                chunk = await upload_file.read(65536)
                if not chunk:
                    break

                if is_first_chunk:
                    is_first_chunk = False
                    if not chunk.startswith(_OOXML_MAGIC):
                        raise HTTPException(
                            status_code=400,
                            detail="File does not look like a valid OOXML (.docx/.pptx) archive.",
                        )

                total_size += len(chunk)
                if total_size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large: {total_size} bytes exceeds {MAX_UPLOAD_BYTES} bytes.",
                    )
                tmp_file.write(chunk)

        if total_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        return tmp_path
    except HTTPException:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to process uploaded file: {str(e)}")
    finally:
        await upload_file.close()

@router.post("/process")
async def process_presentation(
    file: UploadFile = File(...),
    sensitivity: Optional[str] = Form(None),
    intensity: Optional[str] = Form(None),
    tone_preset: Optional[str] = Form(None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Pipeline for a single presentation.
    """
    gemini_api_key = None
    if x_gemini_api_key:
        try:
            gemini_api_key = decrypt_api_key(x_gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to decrypt X-Gemini-API-Key: {e}")

    # Load defaults from user settings if not specified
    from models import UserSettings
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not intensity:
        intensity = user_settings.default_intensity if user_settings else "balanced"
    if not tone_preset:
        tone_preset = user_settings.default_tone_preset if user_settings else "presentation_concise"
    if not sensitivity:
        sensitivity = user_settings.ppt_sensitivity if user_settings else "balanced"

    tmp_path = await save_upload_file_tmp(file)
    try:
        return await process_single_ppt_internal(
            file_path=tmp_path,
            filename=file.filename,
            sensitivity=sensitivity,
            db=db,
            current_user=current_user,
            intensity=intensity,
            tone_preset=tone_preset,
            gemini_api_key=gemini_api_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

@router.post("/batch-process", response_model=List[BatchPptItemResponse])
async def batch_process_presentation(
    files: List[UploadFile] = File(...),
    sensitivity: Optional[str] = Form(None),
    intensity: Optional[str] = Form(None),
    tone_preset: Optional[str] = Form(None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Pipeline for processing multiple presentations in a batch.
    """
    gemini_api_key = None
    if x_gemini_api_key:
        try:
            gemini_api_key = decrypt_api_key(x_gemini_api_key)
        except Exception as e:
            logger.error(f"Failed to decrypt X-Gemini-API-Key: {e}")

    # Load defaults from user settings if not specified
    from models import UserSettings
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not intensity:
        intensity = user_settings.default_intensity if user_settings else "balanced"
    if not tone_preset:
        tone_preset = user_settings.default_tone_preset if user_settings else "presentation_concise"
    if not sensitivity:
        sensitivity = user_settings.ppt_sensitivity if user_settings else "balanced"

    results = []
    
    for file in files:
        try:
            tmp_path = await save_upload_file_tmp(file)
        except Exception as e:
            logger.error(f"Failed validation/saving for batch item {file.filename}: {str(e)}")
            results.append(BatchPptItemResponse(
                session_id="",
                filename=file.filename,
                status="failed",
                error=str(e)
            ))
            continue

        try:
            res = await process_single_ppt_internal(
                file_path=tmp_path,
                filename=file.filename,
                sensitivity=sensitivity,
                db=db,
                current_user=current_user,
                intensity=intensity,
                tone_preset=tone_preset,
                gemini_api_key=gemini_api_key
            )
            session_id = res["session"]["id"]
            results.append(BatchPptItemResponse(
                session_id=session_id,
                filename=file.filename,
                status="completed",
                total_slides=res["data"].get("total_slides", 0),
                total_flags=0
            ))
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
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            
    return results
