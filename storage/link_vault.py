import sqlite3
from typing import List, Optional
from heartbeat.config import get_config
from pydantic import BaseModel
import datetime

class LinkMetadata(BaseModel):
    """Pydantic model for stored links."""
    url: str
    cell_id: str
    user_id: str
    title: Optional[str] = None
    topic_id: Optional[str] = None
    discovered_at: str = datetime.datetime.now().isoformat()

class LinkVault:
    """Manages persistent structured storage for discovered links."""
    def __init__(self):
        config = get_config()
        self.db_path = config.sqlite_db_path
        self._create_link_table()

    def _create_link_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS link_vault (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT,
                topic_id TEXT,
                discovered_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_link(self, link: LinkMetadata):
        """Saves or updates a purified link in the vault."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO link_vault (url, cell_id, user_id, title, topic_id, discovered_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (link.url, link.cell_id, link.user_id, link.title, link.topic_id, link.discovered_at))
        conn.commit()
        conn.close()

    def get_user_links(self, user_id: str) -> List[LinkMetadata]:
        """Retrieves all links ever discovered for a specific user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, cell_id, user_id, title, topic_id, discovered_at FROM link_vault WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [LinkMetadata(url=r[0], cell_id=r[1], user_id=r[2], title=r[3], topic_id=r[4], discovered_at=r[5]) for r in rows]

# Singleton helper
_link_vault_instance = None
def get_link_vault():
    global _link_vault_instance
    if _link_vault_instance is None:
        _link_vault_instance = LinkVault()
    return _link_vault_instance
