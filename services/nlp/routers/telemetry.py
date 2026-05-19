import re
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import List, Optional

from database import get_db
from models import User, ErrorEvent
from routers.auth import get_current_user

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

class CrashReportRequest(BaseModel):
    route: str
    error_type: str
    message: str
    stack_summary: Optional[str] = None
    consent_flag: bool
    session_id: Optional[str] = None

class ErrorEventResponse(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    user_id: Optional[uuid.UUID]
    session_id: Optional[uuid.UUID]
    route: str
    error_type: str
    message: str
    stack_summary: Optional[str]
    consent_flag: bool

    class Config:
        from_attributes = True

class PaginatedEventsResponse(BaseModel):
    total: int
    page: int
    limit: int
    events: List[ErrorEventResponse]

def scrub_sensitive_info(text: str) -> str:
    """Scrubs Windows and Linux system folder paths to protect PII."""
    if not text:
        return ""
    # Scrub Windows path names like C:\Users\bharg\...
    text = re.sub(r'[cC]:\\Users\\[^\\]+', r'C:\\Users\\<user>', text)
    # Scrub Linux path names like /home/username/...
    text = re.sub(r'/home/[^/]+', r'/home/<user>', text)
    # Truncate to maximum 1024 characters
    if len(text) > 1024:
        text = text[:1021] + "..."
    return text

def get_optional_user(
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """Gracefully handles optional users for crash reports."""
    try:
        from routers.auth import get_current_user
        return get_current_user(authorization=authorization, x_auth_token=x_auth_token, db=db)
    except Exception:
        return None

@router.post("/crash")
def record_crash(req: CrashReportRequest, db: DBSession = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    """
    Accepts crash reports from clients. 
    Only persists if the consent_flag is set to True.
    """
    if not req.consent_flag:
        return {"detail": "Telemetry declined by user. Wiped."}

    parsed_session_id = None
    if req.session_id:
        try:
            parsed_session_id = uuid.UUID(req.session_id)
        except ValueError:
            pass

    # Scrub message and stack traces of raw slide contents or system paths
    scrubbed_message = scrub_sensitive_info(req.message)
    scrubbed_stack = scrub_sensitive_info(req.stack_summary) if req.stack_summary else None

    error_log = ErrorEvent(
        route=req.route,
        error_type=req.error_type,
        message=scrubbed_message,
        stack_summary=scrubbed_stack,
        consent_flag=True,
        user_id=current_user.id if current_user else None,
        session_id=parsed_session_id
    )
    db.add(error_log)
    db.commit()
    return {"detail": "Crash telemetry stored successfully."}

@router.get("/events", response_model=PaginatedEventsResponse)
def get_telemetry_events(
    page: int = 1,
    limit: int = 20,
    route: Optional[str] = None,
    error_type: Optional[str] = None,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns telemetry logs for developers.
    """
    # 1. Access Control: Developer role only
    if current_user.role != "developer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Developer privileges required."
        )

    # Enforce safe bounds for pagination
    if limit > 100:
        limit = 100
    if page < 1:
        page = 1

    query = db.query(ErrorEvent)

    if route:
        query = query.filter(ErrorEvent.route.contains(route))
    if error_type:
        query = query.filter(ErrorEvent.error_type == error_type)

    total = query.count()
    events = query.order_by(ErrorEvent.timestamp.desc()).offset((page - 1) * limit).limit(limit).all()

    return PaginatedEventsResponse(
        total=total,
        page=page,
        limit=limit,
        events=events
    )
