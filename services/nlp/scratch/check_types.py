import sqlite3

conn = sqlite3.connect("docppt.db")
cursor = conn.cursor()
cursor.execute("SELECT id, typeof(id), email, typeof(email) FROM users")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Type: {row[1]} | Email: {row[2]} | Type: {row[3]}")
conn.close()
