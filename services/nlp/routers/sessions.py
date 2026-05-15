from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
import uuid

from database import get_db
from models import Session, User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class SessionCreate(BaseModel):
    session_type: str
    input_type: str
    input_label: str = None
    input_url: str = None

class SessionResponse(BaseModel):
    id: uuid.UUID
    session_type: str
    input_type: str
    status: str
    
    class Config:
        from_attributes = True

@router.post("/", response_model=SessionResponse)
def create_session(session: SessionCreate, db: DBSession = Depends(get_db)):
    # Retrieve the default local user
    user = db.query(User).filter(User.email == "local_user@example.com").first()
    if not user:
        raise HTTPException(status_code=500, detail="Default local user not found in DB.")

    db_session = Session(
        user_id=user.id,
        session_type=session.session_type,
        input_type=session.input_type,
        input_label=session.input_label,
        input_url=session.input_url,
        status="created"
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: uuid.UUID, db: DBSession = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.delete("/{session_id}")
def delete_session(session_id: uuid.UUID, db: DBSession = Depends(get_db)):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(db_session)
    db.commit()
    return {"detail": "Session deleted"}
