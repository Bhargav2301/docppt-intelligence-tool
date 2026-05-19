import os
from fastapi import FastAPI
from routers import sessions, models as models_router, doc, analysis, ppt, ppt_analysis, eval, rewrite, settings, export, auth, telemetry
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

def seed_default_user():
    # Only seed default user in non-production environments
    env = os.getenv("ENV", "development")
    if env == "production":
        print("Production environment detected. Skipping default developer user seeding.")
        return
        
    from database import SessionLocal
    from auth_utils import hash_password
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == "local_user@example.com").first()
        if user:
            print("Deleting existing developer user for clean seed...")
            db.delete(user)
            db.commit()
            
        print("Seeding fresh default developer user in development...")
        new_user = models.User(
            email="local_user@example.com",
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
    seed_default_user()
except Exception as e:
    print(f"Startup warning: {e}")

app = FastAPI(title="DocPPT NLP Service", version="1.0.0")

# Setup CORS origins dynamically from FRONTEND_URL or default to localhost:3000
origins = ["http://localhost:3000"]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(telemetry.router)
app.include_router(sessions.router)
app.include_router(models_router.router)
app.include_router(doc.router)
app.include_router(analysis.router)
app.include_router(ppt.router)
app.include_router(ppt_analysis.router)
app.include_router(eval.router)
app.include_router(rewrite.router)
app.include_router(settings.router)
app.include_router(export.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
