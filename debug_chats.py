import sqlite3
import os
from typing import List

def get_connection():
    db_path = "data/heartbeat.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_chats_by_user(user_id: str) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    # Using the same query as the actual code
    cursor.execute("SELECT * FROM chats WHERE user_id = ? COLLATE NOCASE ORDER BY updated_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

result = get_chats_by_user("MASTER_USER")
print(f"Chats found for MASTER_USER: {len(result)}")
for r in result:
    print(r)
