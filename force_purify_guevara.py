import sqlite3
import os
from uuid import uuid4
from datetime import datetime

def force_purify_biography():
    db_path = "data/heartbeat.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find the longest assistant response mentioning Guevara (The Biography)
    print("🔍 Searching for original biography in messages...")
    cursor.execute("""
        SELECT content, chat_id 
        FROM messages 
        WHERE user_id = 'MASTER_USER' COLLATE NOCASE 
        AND role = 'assistant' 
        AND content LIKE '%Guevara%' 
        ORDER BY length(content) DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()

    if not row:
        print("❌ Error: No long biography found in messages table.")
        return

    full_bio = row['content']
    chat_id = row['chat_id']
    print(f"✅ Found biography (Length: {len(full_bio)}) in Chat: {chat_id}")

    # Create a new High-Fidelity Cell in blood_cells
    cell_id = "FORCE-PURIFIED-" + str(uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    print(f"🧬 Force-Purifying into Cell: {cell_id}...")
    
    cursor.execute("""
        INSERT INTO blood_cells (
            cell_id, user_id, chat_id, message_id, 
            topic_id, summary, ai_response_full, 
            importance_score, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cell_id, 'MASTER_USER', chat_id, 'SYSTEM-FORCE',
        'CHE_GUEVARA_BIOGRAPHY', 'Complete high-fidelity biography of Ernesto Che Guevara',
        full_bio, 10, 'active', now
    ))

    # Commit and close
    conn.commit()
    conn.close()
    print("✨ SUCCESS: The biography is now a permanent, high-fidelity Memory Cell.")

if __name__ == "__main__":
    force_purify_biography()
