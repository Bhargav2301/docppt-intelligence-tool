import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, BigInteger, Numeric, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    email = Column(String, unique=True)
    full_name = Column(String)
    avatar_url = Column(String)
    auth_provider = Column(String, default="email")
    google_linked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete")
    sessions = relationship("Session", back_populates="user", cascade="all, delete")

class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    theme = Column(String, default="dark")
    model_mode = Column(String, default="local_cpu")
    summarization_model = Column(String)
    instruction_model = Column(String)
    perplexity_model = Column(String)
    embedding_model = Column(String)
    ppt_sensitivity = Column(String, default="balanced")
    retain_source_files = Column(Boolean, default=True)
    auto_delete_days = Column(Integer)
    google_tokens_encrypted = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))

    user = relationship("User", back_populates="settings")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    session_type = Column(String, nullable=False)
    input_type = Column(String, nullable=False)
    input_label = Column(String)
    input_url = Column(String)
    status = Column(String, default="created")
    error_code = Column(String)
    error_message = Column(String)
    processing_started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))

    user = relationship("User", back_populates="sessions")
    files = relationship("File", back_populates="session", cascade="all, delete")

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    file_role = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    original_filename = Column(String)
    mime_type = Column(String)
    size_bytes = Column(BigInteger)
    checksum_sha256 = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=text("now()"))

    session = relationship("Session", back_populates="files")
