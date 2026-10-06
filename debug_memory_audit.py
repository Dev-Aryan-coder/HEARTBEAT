import sqlite3
import os

def audit_memory():
    db_path = "data/heartbeat.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("--- 🕵️ Audit: Memory Cells for MASTER_USER ---")
    cursor.execute("SELECT cell_id, summary, ai_response_full, topic_id FROM blood_cells WHERE user_id = 'MASTER_USER' COLLATE NOCASE")
    cells = cursor.fetchall()
    for c in cells:
        content_preview = (c['ai_response_full'][:100] + "...") if c['ai_response_full'] else "EMPTY CONTENT"
        print(f"CellID: {c['cell_id']} | Topic: {c['topic_id']} | Summary: {c['summary']}")
        print(f"Content Preview: {content_preview}\n")

    print("\n--- 📝 Audit: All Messages related to Guevara ---")
    cursor.execute("SELECT role, content FROM messages WHERE user_id = 'MASTER_USER' COLLATE NOCASE AND content LIKE '%Guevara%'")
    msgs = cursor.fetchall()
    for m in msgs:
        print(f"Role: {m['role']} | Length: {len(m['content'])}")
        if len(m['content']) > 500:
            print(f"FOUND LONG CONTENT: {m['content'][:100]}...")

    conn.close()

if __name__ == "__main__":
    audit_memory()
