from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
import uuid

from database import get_db
from models import User, UserSettings

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    theme: str = None
    model_mode: str = None
    ppt_sensitivity: str = None
    advanced_instruction_model: str = None
    advanced_model_endpoint: str = None

@router.get("/")
def get_settings(db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == "local_user@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        # Create default settings if not exists
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

@router.put("/")
def update_settings(update: SettingsUpdate, db: DBSession = Depends(get_db)):
    user = db.query(User).filter(User.email == "local_user@example.com").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
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
    
    db.commit()
    db.refresh(settings)
    return settings
