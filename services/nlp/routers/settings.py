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
        settings = UserSettings(user_id=current_user.id, model_mode="gemini_byok")
        db.add(settings)
        db.commit()
        db.refresh(settings)
    elif settings.model_mode != "gemini_byok":
        settings.model_mode = "gemini_byok"
        db.commit()
        db.refresh(settings)
    
    return settings

@router.put("/")
def update_settings(update: SettingsUpdate, db: DBSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id, model_mode="gemini_byok")
        db.add(settings)
    
    if update.theme is not None:
        settings.theme = update.theme
    # Force model_mode to be gemini_byok
    settings.model_mode = "gemini_byok"
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
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
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
    raise HTTPException(status_code=400, detail="Local model mode is disabled. Only Gemini BYOK is supported.")
