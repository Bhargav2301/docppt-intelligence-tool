from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
import uuid
import urllib.request
import urllib.error
import json

from database import get_db
from models import User, UserSettings
from routers.auth import get_current_user
from runtime.crypto import decrypt_api_key

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    theme: str = None
    model_mode: str = None
    ppt_sensitivity: str = None
    advanced_instruction_model: str = None
    advanced_model_endpoint: str = None
    default_tone_preset: str = None
    default_intensity: str = None
    local_model_endpoint: str = None

@router.get("/")
def get_settings(db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        # Create default settings if not exists
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

@router.put("/")
def update_settings(update: SettingsUpdate, db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
    
    if update.theme is not None:
        settings.theme = update.theme
    if update.model_mode is not None:
        settings.model_mode = update.model_mode
    if update.ppt_sensitivity is not None:
        settings.ppt_sensitivity = update.ppt_sensitivity
    if update.advanced_instruction_model is not None:
        settings.advanced_instruction_model = update.advanced_instruction_model
    if update.advanced_model_endpoint is not None:
        settings.advanced_model_endpoint = update.advanced_model_endpoint
    if update.default_tone_preset is not None:
        settings.default_tone_preset = update.default_tone_preset
    if update.default_intensity is not None:
        settings.default_intensity = update.default_intensity
    if update.local_model_endpoint is not None:
        settings.local_model_endpoint = update.local_model_endpoint
    
    db.commit()
    db.refresh(settings)
    return settings

@router.get("/test-gemini")
def test_gemini(request: Request):
    encrypted_key = request.headers.get("X-Gemini-API-Key")
    if not encrypted_key:
        raise HTTPException(status_code=400, detail="Gemini API Key header missing.")
    
    try:
        api_key = decrypt_api_key(encrypted_key)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decrypt Gemini API Key: {str(e)}")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{
            "parts": [{"text": "Hello, respond with exact word 'Connected'."}]
        }]
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("error"):
                error_msg = res_data["error"].get("message", "Unknown Gemini API error")
                raise HTTPException(status_code=400, detail=f"Gemini API error: {error_msg}")
            return {"status": "success", "message": "Gemini connection successful."}
    except urllib.error.HTTPError as he:
        try:
            err_body = he.read().decode("utf-8")
            err_json = json.loads(err_body)
            if "error" in err_json:
                error_msg = err_json["error"].get("message", err_body)
            else:
                error_msg = err_body
        except Exception:
            error_msg = str(he)
        raise HTTPException(status_code=he.code, detail=f"Gemini connection failed: {error_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini connection failed: {str(e)}")

@router.get("/test-local-model")
def test_local_model(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="Local endpoint URL query parameter is missing.")
    
    try:
        endpoint = url.rstrip("/")
        test_endpoints = [f"{endpoint}/v1/models", f"{endpoint}/api/tags", endpoint]
        last_error = None
        for test_url in test_endpoints:
            try:
                req = urllib.request.Request(test_url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status in (200, 201, 204, 401):
                        return {"status": "success", "message": f"Successfully connected to local model server at {test_url}"}
            except Exception as conn_err:
                last_error = conn_err
        
        # Check if the last error represents a connection refused (Errno 111 / 61)
        err_str = str(last_error).lower()
        is_conn_refused = False
        if isinstance(last_error, ConnectionRefusedError):
            is_conn_refused = True
        elif isinstance(last_error, urllib.error.URLError):
            reason = last_error.reason
            if isinstance(reason, OSError):
                if reason.errno in (111, 61) or isinstance(reason, ConnectionRefusedError):
                    is_conn_refused = True
        elif isinstance(last_error, OSError) and getattr(last_error, 'errno', None) in (111, 61):
            is_conn_refused = True
        
        if not is_conn_refused and ("errno 111" in err_str or "errno 61" in err_str or "connection refused" in err_str):
            is_conn_refused = True

        if is_conn_refused:
            return {
                "status": "not_running",
                "message": "No model server found at this address. Start Ollama or LM Studio locally and try again."
            }

        raise HTTPException(status_code=500, detail=f"Could not connect to model server. Error: {str(last_error)}")
    except Exception as e:
        err_str = str(e).lower()
        is_conn_refused = False
        if isinstance(e, ConnectionRefusedError):
            is_conn_refused = True
        elif isinstance(e, urllib.error.URLError):
            reason = e.reason
            if isinstance(reason, OSError):
                if reason.errno in (111, 61) or isinstance(reason, ConnectionRefusedError):
                    is_conn_refused = True
        elif isinstance(e, OSError) and getattr(e, 'errno', None) in (111, 61):
            is_conn_refused = True

        if not is_conn_refused and ("errno 111" in err_str or "errno 61" in err_str or "connection refused" in err_str):
            is_conn_refused = True

        if is_conn_refused:
            return {
                "status": "not_running",
                "message": "No model server found at this address. Start Ollama or LM Studio locally and try again."
            }
        raise HTTPException(status_code=500, detail=f"Local model connection failed: {str(e)}")


