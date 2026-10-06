import sqlite3
import logging

logger = logging.getLogger("HEARTBEAT_MIGRATIONS")

def run_migrations(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    
    # TABLE: users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            plan_type TEXT DEFAULT 'free',
            encryption_key TEXT,
            created_at TEXT
        )
    """)
    
    # TABLE: chats
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            chat_id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT DEFAULT 'New Chat',
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Safe ALTER for chats
    try:
        cursor.execute("ALTER TABLE chats ADD COLUMN updated_at TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # TABLE: messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            msg_id TEXT PRIMARY KEY,
            chat_id TEXT,
            user_id TEXT,
            role TEXT CHECK(role IN ('user', 'assistant')),
            content TEXT,
            timestamp TEXT,
            image_url TEXT,
            FOREIGN KEY (chat_id) REFERENCES chats (chat_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Safe ALTER for messages image_url
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN image_url TEXT")
    except sqlite3.OperationalError:
        pass
    
    # TABLE: blood_cells (Comprehensive Fix)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blood_cells (
            cell_id TEXT PRIMARY KEY,
            user_id TEXT,
            chat_id TEXT,
            message_id TEXT,
            session_id TEXT,
            status TEXT,
            cell_type TEXT,
            user_raw_content TEXT,
            user_content TEXT,
            ai_response_summary TEXT,
            ai_response_full TEXT,
            ai_response_link_id TEXT,
            is_head INTEGER,
            is_chain INTEGER,
            chain_id TEXT,
            next_cell_id TEXT,
            link_id TEXT,
            importance_score INTEGER,
            keywords TEXT,
            topic_id TEXT,
            summary TEXT,
            is_ambiguous INTEGER,
            clarification_question TEXT,
            expires_at TEXT,
            last_activated_at TEXT,
            activation_count INTEGER DEFAULT 0,
            created_at TEXT,
            purified_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # Safe ALTERs for missing columns in blood_cells
    cols = [
        ("session_id", "TEXT"),
        ("ai_raw_response", "TEXT"),
        ("user_content_type", "TEXT"),
        ("analysis_status", "TEXT"),
        ("clarification_answer", "TEXT")
    ]
    for col, ctype in cols:
        try:
            cursor.execute(f"ALTER TABLE blood_cells ADD COLUMN {col} {ctype}")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # TABLE: link_vault
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS link_vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id TEXT UNIQUE,
            cell_id TEXT NOT NULL,
            content_type TEXT,
            full_content TEXT,
            part_number INTEGER,
            total_parts INTEGER,
            created_at TEXT,
            FOREIGN KEY (cell_id) REFERENCES blood_cells (cell_id)
        )
    """)
    
    conn.commit()

def create_indexes(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cells_user_id ON blood_cells(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cells_status ON blood_cells(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)")
    conn.commit()
