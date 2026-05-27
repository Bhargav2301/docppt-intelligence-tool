import sqlite3
import os

db_path = "services/nlp/docppt.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT id, input_label, status, error_message FROM sessions WHERE session_type='ppt'")
for row in cursor.fetchall():
    print(row)
conn.close()
