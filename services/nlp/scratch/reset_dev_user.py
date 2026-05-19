import sys
import os
import sqlite3
import uuid

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth_utils import hash_password

DB_PATH = "docppt.db"

def reset():
    print(f"Connecting directly to SQLite: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Delete existing developer user
    print("Deleting existing user with email 'local_user@example.com'...")
    cursor.execute("DELETE FROM user_settings WHERE user_id IN (SELECT id FROM users WHERE email = 'local_user@example.com')")
    cursor.execute("DELETE FROM user_sessions WHERE user_id IN (SELECT id FROM users WHERE email = 'local_user@example.com')")
    cursor.execute("DELETE FROM users WHERE email = 'local_user@example.com'")
    
    # 2. Insert clean developer user
    dev_id = uuid.uuid4().hex
    pw_hash = hash_password("password")
    print(f"Inserting new developer user. ID: {dev_id}")
    cursor.execute(
        "INSERT INTO users (id, email, full_name, auth_provider, hashed_password, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
        (dev_id, "local_user@example.com", "Local Developer", "email", pw_hash, "developer")
    )
    
    # 3. Insert default settings
    settings_id = uuid.uuid4().hex
    print(f"Inserting settings for developer user. ID: {settings_id}")
    cursor.execute(
        "INSERT INTO user_settings (id, user_id, theme, model_mode, ppt_sensitivity, retain_source_files) VALUES (?, ?, ?, ?, ?, ?)",
        (settings_id, dev_id, "dark", "local_cpu", "balanced", 1)
    )
    
    conn.commit()
    conn.close()
    print("Database seeding completed successfully via raw SQL!")

if __name__ == "__main__":
    reset()
