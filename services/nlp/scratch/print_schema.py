import sqlite3

conn = sqlite3.connect("docppt.db")
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(f"Table: {row[0]}")
    print(row[1])
    print("-" * 50)
conn.close()
