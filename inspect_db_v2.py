import sqlite3
import os

db_path = "data/heartbeat.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- CHATS ---")
cursor.execute("SELECT * FROM chats")
chats = cursor.fetchall()
if not chats:
    print("No chats found.")
else:
    for c in chats:
        print(f"ChatID: {c['chat_id']} | UserID: {c['user_id']} | Title: {c['title']}")

print("\n--- MESSAGES ---")
cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10")
msgs = cursor.fetchall()
if not msgs:
    print("No messages found.")
else:
    for m in msgs:
        print(f"ChatID: {m['chat_id']} | Role: {m['role']} | Content: {m['content'][:50]}...")

conn.close()
