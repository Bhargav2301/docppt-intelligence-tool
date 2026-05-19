import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The default docker-compose connection string for the NLP container
# DB connects using postgres user
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@db:5432/docppt"
)

# For testing outside docker, use SQLite for local_dev to avoid Postgres auth issues
if os.getenv("ENV") == "local_dev":
    SQLALCHEMY_DATABASE_URL = "sqlite:///./docppt.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
