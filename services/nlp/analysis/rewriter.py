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
    session_id: Optional[uuid.UUID] = None
) -> Optional[str]:
    """
    Rewrites the input text using the configured instruction model.
    Supports local_cpu, local_gpu, user_hosted_endpoint, and managed_endpoint.
    Falls back to local flan-t5-small if remote endpoints fail or time out.
    Logs execution metrics to the model_runs table if db is provided.
    """
    if not text.strip():
        return None
        
    mode = MODEL_MODE
    adv_model = ADVANCED_INSTRUCTION_MODEL
    adv_endpoint = ADVANCED_MODEL_ENDPOINT
    managed_model = MANAGED_LLM_MODEL_NAME
    managed_endpoint = MANAGED_LLM_ENDPOINT

    # Query DB settings if a database session is provided
    if db is not None:
        try:
            # First attempt to find the user linked to this session
            user = None
            if session_id:
                sess_record = db.query(DbSessionModel).filter(DbSessionModel.id == session_id).first()
                if sess_record:
                    user = db.query(User).filter(User.id == sess_record.user_id).first()
            
            # Dev-only fallback: only when ENV is explicitly local_dev. Never in production.
            if not user and os.getenv("ENV") == "local_dev":
                user = db.query(User).filter(User.email == "local_user@example.com").first()
                
            if user:
                settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
                if settings:
                    mode = settings.model_mode or mode
                    adv_model = settings.advanced_instruction_model or adv_model
                    adv_endpoint = settings.advanced_model_endpoint or adv_endpoint
        except Exception as e:
            logger.error(f"Error reading DB settings: {str(e)}")

    if mode == "extractive_only":
        logger.info("Using rule-based fallback clean because MODEL_MODE is extractive_only.")
        from .artifact_detector import detect_artifacts, clean_text_by_rules
        flags = detect_artifacts(text)
        return clean_text_by_rules(text, flags)


    start_time = time.time()
    status = "success"
    err_code = None
    err_msg = None
    
    if mode == "user_hosted_endpoint":
        model_used = adv_model
    elif mode == "managed_endpoint":
        model_used = managed_model
    else:
        model_used = "flan-t5-small"
        
    rewritten = None

    # 1. Attempt remote endpoint calls if selected
    if mode == "managed_endpoint":
        try:
            # If endpoint is not configured (or set to placeholder in production), trigger fallback immediately
            if not managed_endpoint or "api.managed-llm.com" in managed_endpoint:
                raise ValueError("Managed LLM endpoint not configured in production.")
                
            rewritten = registry.call_user_hosted_endpoint(
                endpoint=managed_endpoint,
                model_name=managed_model,
                prompt=f"Rewrite the following text to be more {tone} and clear, but keep the original meaning: {text}"
            )
        except Exception as e:
            status = "fallback"
            err_code = "MANAGED_ENDPOINT_ERROR"
            err_msg = str(e)
            logger.warning(f"Managed hosted LLM failed, falling back to local instruction model: {str(e)}")

    elif mode == "user_hosted_endpoint":
        try:
            rewritten = registry.call_user_hosted_endpoint(
                endpoint=adv_endpoint,
                model_name=adv_model,
                prompt=f"Rewrite the following text to be more {tone} and clear, but keep the original meaning: {text}"
            )
        except Exception as e:
            status = "fallback"
            err_code = "USER_ENDPOINT_ERROR"
            err_msg = str(e)
            logger.warning(f"User-hosted model failed, falling back to local instruction model: {str(e)}")

    # 2. Fall back to local model if selected, or if remote calls fell back
    if rewritten is None:
        try:
            instruction_model = registry.get_instruction_model()
            if not instruction_model:
                logger.warning("Instruction model not available for rewrite.")
                if status == "success" or status == "fallback":
                    if mode in ("user_hosted_endpoint", "managed_endpoint"):
                        status = "fallback"
                    else:
                        status = "failed"
                    err_code = "MODEL_UNAVAILABLE"
                    err_msg = "Local instruction model not available"
            else:
                try:
                    # Construct prompt for flan-t5-small
                    prompt = f"Rewrite the following text to be more {tone} and clear, but keep the original meaning: {text}"
                    input_words = len(text.split())
                    max_tokens = max(50, int(input_words * 2))
                    
                    result = instruction_model(prompt, max_new_tokens=max_tokens, do_sample=True, temperature=0.7)
                    rewritten = result[0]['generated_text'].strip()
                except Exception as e:
                    if mode in ("user_hosted_endpoint", "managed_endpoint"):
                        status = "fallback"
                    else:
                        status = "failed"
                    err_code = "LOCAL_MODEL_ERROR"
                    err_msg = str(e)
                    logger.error(f"Failed to generate rewrite: {str(e)}")
        except Exception as load_err:
            if mode in ("user_hosted_endpoint", "managed_endpoint"):
                status = "fallback"
            else:
                status = "failed"
            err_code = "LOCAL_MODEL_LOAD_ERROR"
            err_msg = str(load_err)
    if rewritten is None:
        from .artifact_detector import detect_artifacts, clean_text_by_rules
        flags = detect_artifacts(text)
        rewritten = clean_text_by_rules(text, flags)

    duration_ms = int((time.time() - start_time) * 1000)

    # 3. Log model run to database
    if db is not None:
        try:
            run_log = ModelRun(
                session_id=session_id,
                run_type="rewrite",
                model_name=model_used,
                model_mode=mode,
                input_tokens_estimate=len(text.split()),
                output_tokens_estimate=len(rewritten.split()) if rewritten else 0,
                duration_ms=duration_ms,
                status=status,
                error_code=err_code,
                error_message=err_msg,
                run_metadata={"text_length": len(text)}
            )
            db.add(run_log)
            db.commit()
        except Exception as log_err:
            logger.error(f"Failed to log ModelRun to DB: {str(log_err)}")

    return rewritten

