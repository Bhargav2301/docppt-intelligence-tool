from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
import uuid
import urllib.request
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
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
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
            return {"status": "success", "message": "Gemini connection successful."}
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
        raise HTTPException(status_code=500, detail=f"Could not connect to model server. Error: {str(last_error)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local model connection failed: {str(e)}")

