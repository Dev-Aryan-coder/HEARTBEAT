import sqlite3

db_path = "heartbeat.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- RECENT CELLS ---")
cursor.execute("SELECT cell_id, user_id, chat_id, summary FROM blood_cells ORDER BY created_at DESC LIMIT 10")
cells = cursor.fetchall()
for c in cells:
    print(f"CellID: {c['cell_id']} | UserID: {c['user_id']} | ChatID: {c['chat_id']} | Summary: {c['summary'][:30]}...")

print("\n--- CHATS FOR THESE USERS ---")
# Get unique user_ids from recent cells
user_ids = list(set([c['user_id'] for c in cells]))
for uid in user_ids:
    cursor.execute("SELECT chat_id, title FROM chats WHERE user_id = ?", (uid,))
    chats = cursor.fetchall()
    print(f"User: {uid} | Chat Count: {len(chats)}")
    for chat in chats:
        print(f"  - ChatID: {chat['chat_id']} | Title: {chat['title']}")

print("\n--- BACKFILLING MISSING CHATS ---")
# If a cell has a chat_id but it's not in the chats table, create it.
cursor.execute("""
    SELECT DISTINCT bc.chat_id, bc.user_id, bc.summary, bc.created_at 
    FROM blood_cells bc
    LEFT JOIN chats c ON bc.chat_id = c.chat_id
    WHERE c.chat_id IS NULL AND bc.chat_id IS NOT NULL AND bc.chat_id != ''
""")
orphans = cursor.fetchall()
print(f"Found {len(orphans)} orphaned chats in history.")
for o in orphans:
    title = (o['summary'][:50] if o['summary'] else "Recovered Chat")
    print(f"Backfilling ChatID: {o['chat_id']} for User: {o['user_id']}")
    # Use REPLACE to be safe
    cursor.execute("""
        INSERT OR REPLACE INTO chats (chat_id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """, (o['chat_id'], o['user_id'], title, o['created_at'], o['created_at']))

conn.commit()
print("Backfill complete.")
conn.close()
