import logging
import time
import uuid
import os
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from runtime.registry import registry
from runtime.config import MODEL_MODE, ADVANCED_INSTRUCTION_MODEL, ADVANCED_MODEL_ENDPOINT, MANAGED_LLM_ENDPOINT, MANAGED_LLM_MODEL_NAME
from models import User, UserSettings, ModelRun, Session as DbSessionModel

logger = logging.getLogger(__name__)

def generate_rewrite(
    text: str, 
    tone: str = "professional", 
    db: Optional[DBSession] = None, 
    session_id: Optional[uuid.UUID] = None,
    gemini_api_key: Optional[str] = None,
    intensity: str = "balanced"
) -> Optional[str]:
    """
    Rewrites the input text using the configured instruction model.
    Routes all model modes through the unified multi-agent humanizer pipeline.
    """
    if not text.strip():
        return None
        
    mode = "gemini_byok"
    adv_model = ADVANCED_INSTRUCTION_MODEL
    adv_endpoint = ADVANCED_MODEL_ENDPOINT
    managed_model = MANAGED_LLM_MODEL_NAME
    managed_endpoint = MANAGED_LLM_ENDPOINT

    # Query DB settings if a database session is provided
    if db is not None:
        try:
            user = None
            if session_id:
                sess_record = db.query(DbSessionModel).filter(DbSessionModel.id == session_id).first()
                if sess_record:
                    user = db.query(User).filter(User.id == sess_record.user_id).first()
            
            # Dev-only fallback
            if not user and os.getenv("ENV") == "local_dev":
                from runtime.crypto import hash_email
                dev_hash = hash_email("local_user@example.com")
                user = db.query(User).filter(User.email_hash == dev_hash).first()
                
            if user:
                settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
                if settings:
                    # Enforce gemini_byok
                    mode = "gemini_byok"
                    adv_model = settings.advanced_instruction_model or adv_model
                    adv_endpoint = settings.advanced_model_endpoint or adv_endpoint
        except Exception as e:
            logger.error(f"Error reading DB settings: {str(e)}")

    if mode == "extractive_only":
        logger.info("Using rule-based fallback clean because MODEL_MODE is extractive_only.")
        from app.detector.rules import detect_artifacts, clean_text_by_rules
        from app.humanizer.editorial_rules import apply_all_editorial_rules
        flags = detect_artifacts(text).artifact_flags
        cleaned = clean_text_by_rules(text, flags)
        return apply_all_editorial_rules(cleaned)

    # Unified pipeline for all generative/LLM modes (gemini_byok, managed_endpoint, user_hosted_endpoint, local_cpu, local_gpu)
    try:
        from app.humanizer.planner import plan_rewrite_strategy
        from app.humanizer.rewriter import generate_candidates
        from app.humanizer.judge import judge_candidates
        from app.detector.scorer import compute_ai_likeness
        from app.detector.rules import detect_artifacts
        from app.humanizer.editorial_rules import apply_all_editorial_rules
        
        # Map tone label to preset
        tone_map = {
            "professional": "consulting_professional",
            "concise": "presentation_concise",
            "founder": "founder_clear",
            "polished": "executive_polished",
            "direct": "product_manager_direct",
            "consulting_professional": "consulting_professional",
            "presentation_concise": "presentation_concise",
            "founder_clear": "founder_clear",
            "executive_polished": "executive_polished",
            "product_manager_direct": "product_manager_direct"
        }
        mapped_tone = tone_map.get(tone.lower(), "consulting_professional")
        
        ai_res = compute_ai_likeness(text, intensity=intensity)
        art_res = detect_artifacts(text)
        
        plan = plan_rewrite_strategy(
            text=text,
            ai_likeness_band=ai_res.band,
            ai_likeness_reasons=ai_res.reasons,
            artifact_flags=[f.dict() for f in art_res.artifact_flags],
            tone_preset=mapped_tone,
            slide_role="body",
            intensity=intensity
        )
        
        # Route specific model settings depending on mode
        actual_name = adv_model if mode == "user_hosted_endpoint" else managed_model if mode == "managed_endpoint" else None
        actual_endpoint = adv_endpoint if mode == "user_hosted_endpoint" else managed_endpoint if mode == "managed_endpoint" else None
        
        candidates = generate_candidates(
            text=text,
            rewrite_plan=plan,
            tone_preset=mapped_tone,
            gemini_api_key=gemini_api_key,
            model_mode=mode,
            model_name=actual_name,
            endpoint=actual_endpoint,
            intensity=intensity
        )
        
        decision_dict = judge_candidates(
            candidates=candidates,
            original_text=text,
            constraints=plan.get("constraints", {})
        )
        
        # Log to db as ModelRun if database session is provided
        if db is not None:
            try:
                from models import ModelRun
                model_used = actual_name or "gemini" if mode == "gemini_byok" or gemini_api_key else "local_model"
                run_log = ModelRun(
                    session_id=session_id,
                    run_type="rewrite",
                    model_name=model_used,
                    model_mode=mode,
                    input_tokens_estimate=len(text.split()),
                    output_tokens_estimate=len(decision_dict.get("selected_text", "").split()),
                    duration_ms=100,
                    status="success",
                    run_metadata={"text_length": len(text)}
                )
                db.add(run_log)
                db.commit()
            except Exception as log_err:
                logger.error(f"Failed to log ModelRun to DB in unified pipeline: {str(log_err)}")
                
        return decision_dict.get("selected_text", text)
        
    except Exception as e:
        logger.error(f"Unified rewrite pipeline failed, falling back to rules: {e}")
        from app.detector.rules import detect_artifacts, clean_text_by_rules
        from app.humanizer.editorial_rules import apply_all_editorial_rules
        flags = detect_artifacts(text).artifact_flags
        cleaned = clean_text_by_rules(text, flags)
        return apply_all_editorial_rules(cleaned)
