from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

from database import get_db
from models import Session, User, DocOutput, PptOutput

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
    input_label: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class RecentSessionItem(SessionResponse):
    metrics: dict = {}

@router.get("/recent", response_model=List[RecentSessionItem])
def get_recent_sessions(limit: int = 20, db: DBSession = Depends(get_db)):
    db_sessions = db.query(Session).order_by(Session.created_at.desc()).limit(limit).all()
    
    results = []
    for s in db_sessions:
        metrics = {}
        if s.session_type == "doc":
            out = db.query(DocOutput).filter(DocOutput.session_id == s.id).first()
            if out:
                metrics["word_count"] = out.word_count
                metrics["summary_ready"] = bool(out.structured_summary)
        elif s.session_type == "ppt":
            out = db.query(PptOutput).filter(PptOutput.session_id == s.id).first()
            if out:
                metrics["total_slides"] = out.total_slides
                metrics["total_flags"] = out.total_flags
                
        results.append(RecentSessionItem(
            id=s.id,
            session_type=s.session_type,
            input_type=s.input_type,
            input_label=s.input_label or (f"Untitled {s.session_type.upper()}"),
            status=s.status,
            created_at=s.created_at,
            completed_at=s.completed_at,
            metrics=metrics
        ))
        
    return results

@router.post("/", response_model=SessionResponse)
def create_session(session: SessionCreate, db: DBSession = Depends(get_db)):
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

@router.get("/{session_id}/detail")
def get_session_detail(session_id: uuid.UUID, db: DBSession = Depends(get_db)):
    """Return session metadata plus its associated output (doc or ppt)."""
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    result: dict = {
        "session": {
            "id": str(db_session.id),
            "session_type": db_session.session_type,
            "input_type": db_session.input_type,
            "input_label": db_session.input_label,
            "status": db_session.status,
            "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
            "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None,
            "error_message": db_session.error_message,
        },
        "output": None,
    }

    if db_session.session_type == "doc":
        doc_out = db.query(DocOutput).filter(DocOutput.session_id == db_session.id).first()
        if doc_out:
            result["output"] = {
                "structured_summary": doc_out.structured_summary,
                "product_description": doc_out.product_description,
                "implementation_requirements": doc_out.implementation_requirements,
                "word_count": doc_out.word_count,
            }

    return result

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
