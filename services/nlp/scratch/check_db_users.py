import os
import sys

# Add backend root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
import models

db = SessionLocal()
try:
    print("=== Listing all Users in DB ===")
    users = db.query(models.User).all()
    for u in users:
        print(f"ID: {u.id} | Email: {u.email} | Name: {u.full_name} | Role: {u.role} | PwdHash: {u.hashed_password[:15] if u.hashed_password else None}")
    
    print("\n=== Listing all UserSession in DB ===")
    sessions = db.query(models.UserSession).all()
    for s in sessions:
        print(f"ID: {s.id} | UserID: {s.user_id} | Token: {s.token[:15]}... | Expires: {s.expires_at}")
        
except Exception as e:
    print(f"Error querying DB: {e}")
finally:
    db.close()
