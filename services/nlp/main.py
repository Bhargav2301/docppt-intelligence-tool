import os
from fastapi import FastAPI
from routers import sessions, models as models_router, ppt, ppt_analysis, eval, rewrite, settings, auth, telemetry
from database import engine
import models

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

models.Base.metadata.create_all(bind=engine)

def run_migrations():
    inspector = inspect(engine)
    if "user_settings" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("user_settings")]
        with engine.begin() as conn:
            if "advanced_instruction_model" not in columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN advanced_instruction_model VARCHAR DEFAULT 'llama3'"))
            if "advanced_model_endpoint" not in columns:
                conn.execute(text("ALTER TABLE user_settings ADD COLUMN advanced_model_endpoint VARCHAR DEFAULT 'http://localhost:11434/v1'"))

    if "users" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("users")]
        with engine.begin() as conn:
            if "hashed_password" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR"))
            if "role" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
            if "email_hash" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_hash VARCHAR"))

def run_crypto_migration():
    """
    Migration to symmetrically encrypt legacy plaintext users in the database
    and populate their email_hash fields.
    """
    from database import SessionLocal
    from models import User
    from runtime.crypto import hash_email
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        migrated = False
        for user in users:
            # If email_hash is not set, this is a legacy user that needs encryption
            if not user.email_hash and user.email:
                plain_email = user.email
                plain_name = user.full_name
                print(f"Migrating legacy user: {plain_email}")
                
                # Re-assigning triggers EncryptedString process_bind_param
                user.email = plain_email
                user.email_hash = hash_email(plain_email)
                if plain_name:
                    user.full_name = plain_name
                migrated = True
        if migrated:
            db.commit()
            print("Legacy user accounts migrated and encrypted successfully.")
    except Exception as e:
        print(f"Warning: database encryption migration failed: {e}")
    finally:
        db.close()

def seed_default_user():
    # Only seed default developer user when ENV is development or local_dev. Never in production.
    env = os.getenv("ENV", "development")
    if env not in ("local_dev", "development"):
        print(f"ENV={env}: Skipping default developer user seeding.")
        return
        
    from database import SessionLocal
    from auth_utils import hash_password
    from runtime.crypto import hash_email
    db = SessionLocal()
    try:
        email = "local_user@example.com"
        email_h = hash_email(email)
        user = db.query(models.User).filter(models.User.email_hash == email_h).first()
        if user:
            print("Developer user already exists. Updating credentials/role if necessary...")
            user.full_name = "Local Developer"
            user.role = "developer"
            user.hashed_password = hash_password("password")
            user.auth_provider = "email"
            db.commit()
        else:
            print("Seeding fresh default developer user in development...")
            new_user = models.User(
                email=email,
                email_hash=email_h,
                full_name="Local Developer",
                auth_provider="email",
                role="developer",
                hashed_password=hash_password("password")
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Seed default settings
            settings = models.UserSettings(user_id=new_user.id)
            db.add(settings)
            db.commit()
            print("Default developer user and settings seeded successfully.")
    except Exception as e:
        print(f"Warning: Failed to seed default user: {e}")
    finally:
        db.close()

try:
    run_migrations()
    run_crypto_migration()
    seed_default_user()
except Exception as e:
    print(f"Startup warning: {e}")

app = FastAPI(title="DocPPT PPTX AI-Likeness Detector & Humanizer", version="1.0.0")

# Setup CORS origins dynamically from FRONTEND_URL or default to localhost:3000
origins = ["http://localhost:3000", "http://localhost:5173"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "X-Gemini-API-Key"],
)

app.include_router(auth.router)
app.include_router(telemetry.router)
app.include_router(sessions.router)
app.include_router(models_router.router)
app.include_router(ppt.router)
app.include_router(ppt_analysis.router)
app.include_router(eval.router)
app.include_router(rewrite.router)
app.include_router(settings.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
