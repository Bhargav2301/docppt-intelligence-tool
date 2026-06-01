import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from models import User, Session, UserSettings
import uuid

client = TestClient(app)

def test_create_and_delete_session():
    # 1. Sign up user
    email = "delete_test_user@example.com"
    password = "password123"
    full_name = "Delete Test User"
    
    signup_payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    
    signup_res = client.post("/api/auth/signup", json=signup_payload)
    if signup_res.status_code == 400:
        # Already exists, just login
        login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    else:
        login_res = signup_res
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create session
    session_payload = {
        "session_type": "ppt",
        "input_type": "pptx",
        "input_label": "Test Presentation Deletion"
    }
    create_res = client.post("/api/sessions/", json=session_payload, headers=headers)
    assert create_res.status_code == 200
    session_id = create_res.json()["id"]
    
    # Verify it exists in recent
    recent_res = client.get("/api/sessions/recent", headers=headers)
    assert any(s["id"] == session_id for s in recent_res.json())
    
    # 3. Delete session
    delete_res = client.delete(f"/api/sessions/{session_id}", headers=headers)
    assert delete_res.status_code == 200
    assert delete_res.json() == {"detail": "Session deleted"}
    
    # Verify it no longer exists in recent
    recent_res2 = client.get("/api/sessions/recent", headers=headers)
    assert not any(s["id"] == session_id for s in recent_res2.json())

def test_delete_all_sessions():
    # 1. Sign up user
    email = "delete_all_test_user@example.com"
    password = "password123"
    full_name = "Delete All Test User"
    
    signup_payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    
    signup_res = client.post("/api/auth/signup", json=signup_payload)
    if signup_res.status_code == 400:
        login_res = client.post("/api/auth/login", json={"email": email, "password": password})
    else:
        login_res = signup_res
        
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create multiple sessions
    for i in range(3):
        client.post("/api/sessions/", json={
            "session_type": "ppt",
            "input_type": "pptx",
            "input_label": f"Test Session {i}"
        }, headers=headers)
        
    # Verify we have 3 recent sessions
    recent_res = client.get("/api/sessions/recent", headers=headers)
    assert len(recent_res.json()) >= 3
    
    # 3. Delete all sessions
    delete_all_res = client.delete("/api/sessions/delete-all", headers=headers)
    assert delete_all_res.status_code == 200
    assert delete_all_res.json() == {"detail": "All sessions deleted"}
    
    # Verify no sessions remain
    recent_res2 = client.get("/api/sessions/recent", headers=headers)
    assert len(recent_res2.json()) == 0
