import sqlite3

db_path = "heartbeat.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- ORPHANED MESSAGES ---")
# Messages that have a chat_id but that chat_id is NOT in the chats table
cursor.execute("""
    SELECT DISTINCT m.chat_id, m.user_id 
    FROM messages m 
    LEFT JOIN chats c ON m.chat_id = c.chat_id 
    WHERE c.chat_id IS NULL
""")
orphans = cursor.fetchall()
if not orphans:
    print("No orphaned messages.")
else:
    for o in orphans:
        print(f"ChatID: {o['chat_id']} | UserID: {o['user_id']}")

print("\n--- CHATS BY USER ---")
cursor.execute("SELECT user_id, COUNT(*) as count FROM chats GROUP BY user_id")
for row in cursor.fetchall():
    print(f"User: {row['user_id']} | Chat Count: {row['count']}")

conn.close()
