import sqlite3
import os

db_path = "heartbeat.db"
if not os.path.exists(db_path):
    print("DB not found at heartbeat.db, checking config...")
    # fallback to current dir if main.py is in the same place
    
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print("TABLES:")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in cursor.fetchall():
    print(f"- {row['name']}")
    
print("\nCHATS:")
cursor.execute("SELECT * FROM chats")
for row in cursor.fetchall():
    print(dict(row))

print("\nMESSAGES (Last 5):")
cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5")
for row in cursor.fetchall():
    print(dict(row))

conn.close()
