import sqlite3

db_path = "heartbeat.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Search for these specific cells to find out who owns them
# Summaries: USER_BIOGRAPHY_INQUIRY, USER_QUERY_AIR_POLLUTION
print("--- SEARCHING FOR RELEVANT CELLS ---")
cursor.execute("SELECT user_id, chat_id, last_activated_at, summary FROM blood_cells WHERE summary LIKE '%USER_BIOGRAPHY_INQUIRY%' OR summary LIKE '%AIR_POLLUTION%' LIMIT 10")
cells = cursor.fetchall()
for c in cells:
    print(f"Cell Owner: {c['user_id']} | ChatID: {c['chat_id']} | Summary: {c['summary'][:40]}...")

# 2. Check if a chat exists in the 'chats' table for these users
owners = list(set([c['user_id'] for c in cells]))
print(f"\n--- CHECKING CHATS TABLE FOR OWNERS: {owners} ---")
for uid in owners:
    cursor.execute("SELECT * FROM chats WHERE user_id = ?", (uid,))
    chats = cursor.fetchall()
    print(f"User: {uid} | Chat Count: {len(chats)}")
    for chat in chats:
        print(f"  [Chat List Item] ID: {chat['chat_id']} | Title: {chat['title']}")

# 3. Create missing chats with better defaults if they are missing
for c in cells:
    uid = c['user_id']
    cid = c['chat_id']
    cursor.execute("SELECT count(*) FROM chats WHERE chat_id = ?", (cid,))
    if cursor.fetchone()[0] == 0:
        print(f"Repairing Chat: {cid} for {uid}")
        title = c['summary'][:50]
        now = c['last_activated_at'] or "2026-03-29T10:00:00"
        cursor.execute("""
            INSERT INTO chats (chat_id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (cid, uid, title, now, now))

conn.commit()
conn.close()
