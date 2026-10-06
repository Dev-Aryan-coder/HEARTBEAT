import sqlite3
import os
import json
from typing import List, Optional
from datetime import datetime
import logging
from heartbeat.config import get_config

# Configure logging
logger = logging.getLogger("HEARTBEAT_DB")
from cells.cell_model import BloodCell, CellType, CellStatus, ContentType
from storage.migrations import run_migrations, create_indexes

_db_connection = None

def get_connection() -> sqlite3.Connection:
    """
    Returns a managed SQLite connection with WAL mode and Foreign Keys enabled.
    ISSUE 36 FIX: Detects and recreates closed connections automatically.
    """
    global _db_connection
    config = get_config()
    db_path = getattr(config, 'sqlite_db_path', None)

    if not db_path:
        # Fallback to default if config is missing path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, "data", "heartbeat.db")

    # Ensure data folder exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # ISSUE 36 FIX: Check if connection is closed or never created
    if _db_connection is None:
        _db_connection = _create_connection(db_path)
    else:
        # Detect if connection was closed externally
        try:
            _db_connection.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            logger.warning("SQLite connection was closed. Recreating...")
            _db_connection = _create_connection(db_path)

    return _db_connection

def _create_connection(db_path: str) -> sqlite3.Connection:
    """Creates and configures a new SQLite connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # CRITICAL: Enable WAL mode for high-concurrency (Metabolism + API)
    conn.execute("PRAGMA journal_mode=WAL")
    # CRITICAL: Enable Foreign Keys (not enabled by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_database() -> None:
    conn = get_connection()
    try:
        create_all_tables(conn)
        create_indexes(conn)
    finally:
        pass # Keep singleton connection open

def create_all_tables(conn: sqlite3.Connection) -> None:
    run_migrations(conn)

def _normalize_user_id(user_id: str) -> str:
    """Unified user_id normalization — ISSUE 1.4 FIX
    Maps MASTER_USER, USER, or empty string to MASTER_USER."""
    if not user_id:
        return "MASTER_USER"
    uid = user_id.strip()
    if uid.upper() in ("MASTER_USER", "USER"):
        return "MASTER_USER"
    return uid

def ensure_user(user_id: str) -> None:
    """ENSURE USER EXISTS: satisfying Foreign Key constraints for chats/messages."""
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, created_at)
        VALUES (?, ?)
    """, (uid, now))
    conn.commit()

def save_message(msg_id: str, chat_id: str, user_id: str, role: str, content: str, image_url: Optional[str] = None) -> None:
    """Saves a message — Note: Caller should handle transaction if calling multiple DB functions."""
    conn = get_connection()
    timestamp = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO messages (msg_id, chat_id, user_id, role, content, timestamp, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (msg_id, chat_id, user_id, role, content, timestamp, image_url))
    conn.commit()

def save_cell(cell: BloodCell) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Serialize cell
    cell_dict = cell.model_dump()
    cell_dict['keywords'] = json.dumps(cell_dict.get('keywords', []))
    
    # Handle datetimes
    time_keys = ['expires_at', 'last_activated_at', 'created_at', 'entered_artery_at', 'ai_responded_at', 'purified_at', 'entered_vein_at']
    for key in time_keys:
        if cell_dict.get(key) and isinstance(cell_dict[key], datetime):
            cell_dict[key] = cell_dict[key].isoformat()
        elif cell_dict.get(key) is None:
            cell_dict[key] = None

    # Booleans
    bool_keys = ['is_ambiguous', 'is_head', 'is_chain']
    for key in bool_keys:
        if cell_dict.get(key) is not None:
            cell_dict[key] = 1 if cell_dict[key] else 0

    cursor.execute("""
        INSERT OR REPLACE INTO blood_cells (
            cell_id, user_id, chat_id, message_id, session_id,
            status, cell_type, user_raw_content, user_content,
            ai_response_summary, ai_response_full, ai_response_link_id,
            is_head, is_chain, chain_id, next_cell_id, link_id,
            importance_score, keywords, topic_id, summary, 
            is_ambiguous, clarification_question, 
            expires_at, last_activated_at, activation_count, 
            created_at, purified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cell_dict['cell_id'], cell_dict['user_id'], cell_dict['chat_id'], cell_dict['message_id'], cell_dict.get('session_id', 'unknown'),
        cell_dict['status'], cell_dict['cell_type'], cell_dict['user_raw_content'], cell_dict['user_content'],
        cell_dict['ai_response_summary'], cell_dict['ai_response_full'], cell_dict['ai_response_link_id'],
        cell_dict['is_head'], cell_dict['is_chain'], cell_dict['chain_id'], cell_dict['next_cell_id'], cell_dict['link_id'],
        cell_dict['importance_score'], cell_dict['keywords'], cell_dict['topic_id'], cell_dict['summary'],
        cell_dict['is_ambiguous'], cell_dict['clarification_question'], 
        cell_dict['expires_at'], cell_dict['last_activated_at'], cell_dict['activation_count'],
        cell_dict['created_at'], cell_dict['purified_at']
    ))
    conn.commit()

def get_messages_by_chat(chat_id: str) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY timestamp ASC", (chat_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_cell_by_id(cell_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM blood_cells WHERE cell_id = ?", (cell_id,))
    row = cursor.fetchone()
    if not row: return None
    cell = dict(row)
    if cell.get('keywords'):
        try: cell['keywords'] = json.loads(cell['keywords'])
        except: cell['keywords'] = []
    # FIX: Ensure session_id exists for Pydantic
    if 'session_id' not in cell or not cell['session_id']:
        cell['session_id'] = 'unknown'
    return cell

def get_cells_by_user(user_id: str, status: str = None) -> List[dict]:
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM blood_cells WHERE user_id = ? COLLATE NOCASE AND status = ? ORDER BY created_at DESC", (uid, status))
    else:
        cursor.execute("SELECT * FROM blood_cells WHERE user_id = ? COLLATE NOCASE ORDER BY created_at DESC", (uid,))
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    for cell in result:
        if cell.get('keywords'):
            try: cell['keywords'] = json.loads(cell['keywords'])
            except: cell['keywords'] = []
    return result

def update_cell_status(cell_id: str, status: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE blood_cells SET status = ? WHERE cell_id = ?", (status, cell_id))
    conn.commit()

def create_chat(chat_id: str, user_id: str, title: str) -> None:
    # ISSUE 6.2 FIX: Ensure user exists first (Foreign Key)
    ensure_user(user_id)
    
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO chats (chat_id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            updated_at = excluded.updated_at,
            title = CASE WHEN length(title) < 5 THEN excluded.title ELSE title END
    """, (chat_id, user_id, title, now, now))
    conn.commit()

def get_chats_by_user(user_id: str) -> List[dict]:
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chats WHERE user_id = ? COLLATE NOCASE ORDER BY updated_at DESC", (uid,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def save_link_vault_entry(link_id: str, cell_id: str, content_type: str, full_content: str, part_num: int, total_parts: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("""
        INSERT OR REPLACE INTO link_vault (link_id, cell_id, content_type, full_content, part_number, total_parts, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (link_id, cell_id, content_type, full_content, part_num, total_parts, now))
    conn.commit()

def get_global_user_history(user_id: str, limit: int = 30) -> List[dict]:
    uid = _normalize_user_id(user_id)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE user_id = ? COLLATE NOCASE ORDER BY timestamp DESC LIMIT ?", (uid, limit))
    rows = cursor.fetchall()
    return [dict(row) for row in reversed(list(rows))]
