import os
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import User, UserSettings, UserSession
from auth_utils import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str = ""
    role: str = "user"

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


def _user_to_response(user: "User") -> UserResponse:
    """Coerce an ORM User into a UserResponse, tolerating NULL columns from legacy rows."""
    return UserResponse(
        id=user.id,
        email=user.email or "",
        full_name=user.full_name or (user.email.split("@")[0] if user.email else "User"),
        role=user.role or "user",
    )

def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    """Treat naive datetimes as UTC to compare safely with aware values."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def clean_expired_tokens(db: DBSession):
    """Periodic cleanup of expired tokens."""
    try:
        now = _utcnow()
        expired = db.query(UserSession).filter(UserSession.expires_at < now).all()
        for tok in expired:
            db.delete(tok)
        db.commit()
    except Exception as e:
        print(f"Error cleaning expired tokens: {e}")

def get_current_user(
    authorization: Optional[str] = Header(None),
    x_auth_token: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_auth_token:
        # Fallback for internal microservice calls
        token = x_auth_token

    env = os.getenv("ENV", "production")

    if not token:
        # Dev-only fallback: only when ENV is explicitly local_dev. Never in production or default.
        if env == "local_dev":
            local_user = db.query(User).filter(User.email == "local_user@example.com").first()
            if local_user:
                return local_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate token
    db_session = db.query(UserSession).filter(UserSession.token == token).first()
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if _ensure_aware(db_session.expires_at) < _utcnow():
        db.delete(db_session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == db_session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Defensive backfill: legacy rows in production may have NULL role/full_name,
    # which causes ResponseValidationError downstream. Patch in-memory only.
    if user.role is None:
        user.role = "user"
    if user.full_name is None:
        user.full_name = (user.email.split("@")[0] if user.email else "User")
    return user

@router.post("/signup", response_model=TokenResponse)
def signup(req: SignupRequest, db: DBSession = Depends(get_db)):
    # 1. Enforce password policy
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    # 2. Check if user already exists
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    # 3. Create user
    new_user = User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Create default user settings
    settings = UserSettings(user_id=new_user.id)
    db.add(settings)
    db.commit()

    # 5. Create active token
    clean_expired_tokens(db)
    token_str = secrets.token_urlsafe(32)
    new_session = UserSession(
        user_id=new_user.id,
        token=token_str,
        expires_at=_utcnow() + timedelta(days=7)
    )
    db.add(new_session)
    db.commit()

    return TokenResponse(
        access_token=token_str,
        user=_user_to_response(new_user)
    )

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    clean_expired_tokens(db)
    
    # 1. Fetch user
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # 2. Verify password
    if not verify_password(user.hashed_password, req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # 3. Generate token
    token_str = secrets.token_urlsafe(32)
    new_session = UserSession(
        user_id=user.id,
        token=token_str,
        expires_at=_utcnow() + timedelta(days=7)
    )
    db.add(new_session)
    db.commit()

    return TokenResponse(
        access_token=token_str,
        user=_user_to_response(user)
    )

@router.post("/logout")
def logout(authorization: Optional[str] = Header(None), db: DBSession = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        db_session = db.query(UserSession).filter(UserSession.token == token).first()
        if db_session:
            db.delete(db_session)
            db.commit()
    return {"detail": "Successfully logged out."}

@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return _user_to_response(user)
