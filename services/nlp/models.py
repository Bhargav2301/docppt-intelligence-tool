import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, BigInteger, Numeric, ForeignKey, text, Uuid, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True)
    full_name = Column(String)
    avatar_url = Column(String)
    auth_provider = Column(String, default="email")
    google_linked = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete")
    sessions = relationship("Session", back_populates="user", cascade="all, delete")

class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    theme = Column(String, default="dark")
    model_mode = Column(String, default="local_cpu")
    summarization_model = Column(String)
    instruction_model = Column(String)
    perplexity_model = Column(String)
    embedding_model = Column(String)
    advanced_instruction_model = Column(String, default="llama3")
    advanced_model_endpoint = Column(String, default="http://localhost:11434/v1")
    ppt_sensitivity = Column(String, default="balanced")
    retain_source_files = Column(Boolean, default=True)
    auto_delete_days = Column(Integer)
    google_tokens_encrypted = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="settings")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    session_type = Column(String, nullable=False)
    input_type = Column(String, nullable=False)
    input_label = Column(String)
    input_url = Column(String)
    status = Column(String, default="created")
    error_code = Column(String)
    error_message = Column(String)
    processing_started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
    files = relationship("File", back_populates="session", cascade="all, delete")
    model_runs = relationship("ModelRun", back_populates="session", cascade="all, delete")

class File(Base):
    __tablename__ = "files"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    file_role = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    original_filename = Column(String)
    mime_type = Column(String)
    size_bytes = Column(BigInteger)
    checksum_sha256 = Column(String)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("Session", back_populates="files")

class DocOutput(Base):
    __tablename__ = "doc_outputs"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="CASCADE"), unique=True)
    structured_summary = Column(String)
    product_description = Column(String)
    implementation_requirements = Column(JSON)
    open_questions = Column(JSON)
    assumptions = Column(JSON)
    word_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("Session")

class PptOutput(Base):
    __tablename__ = "ppt_outputs"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="CASCADE"), unique=True)
    total_slides = Column(Integer)
    total_flags = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("Session")
    segments = relationship("PptSegment", back_populates="ppt_output", cascade="all, delete")

class PptSegment(Base):
    __tablename__ = "ppt_segments"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    ppt_output_id = Column(Uuid, ForeignKey("ppt_outputs.id", ondelete="CASCADE"))
    slide_index = Column(Integer, nullable=False)
    shape_id = Column(String, nullable=False)
    paragraph_index = Column(Integer, nullable=False)
    run_index = Column(Integer, nullable=False)
    original_text = Column(String, nullable=False)
    normalized_text = Column(String)
    flags = Column(JSON)
    eval_scores = Column(JSON)
    final_text = Column(String)
    decision = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ppt_output = relationship("PptOutput", back_populates="segments")


class ModelRun(Base):
    __tablename__ = "model_runs"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="CASCADE"))
    run_type = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    model_mode = Column(String, nullable=False)
    input_tokens_estimate = Column(Integer)
    output_tokens_estimate = Column(Integer)
    duration_ms = Column(Integer)
    status = Column(String, nullable=False)
    error_code = Column(String)
    error_message = Column(String)
    run_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("Session", back_populates="model_runs")


class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User")


class ErrorEvent(Base):
    __tablename__ = "error_events"
    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    user_id = Column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(Uuid, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    route = Column(String, nullable=False)
    error_type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    stack_summary = Column(String, nullable=True)
    consent_flag = Column(Boolean, default=False)

    user = relationship("User")
    session = relationship("Session")
