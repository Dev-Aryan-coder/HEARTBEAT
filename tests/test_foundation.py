import pytest
import os
from heartbeat.config import get_config
from cells.cell_model import CellFactory, BloodCell, CellType
from storage.database import init_database, save_message, get_messages_by_chat

def test_config_loading():
    """Confirms .env and dataclass config is active."""
    config = get_config()
    assert config.max_active_cells > 0
    assert "gsk_" in config.brain_key or config.brain_key == "" # Accept empty for CI

def test_cell_identity():
    """Confirms CellFactory generates valid UUIDs and types."""
    cell = CellFactory.from_text("user_1", "chat_1", "msg_1", "sess_1", "Hello Heart")
    assert cell.cell_type == CellType.raw
    assert len(cell.cell_id) > 20
    assert cell.user_raw_content == "Hello Heart"

def test_sqlite_persistence():
    """Confirms SQLite messages are saved and retrieved."""
    init_database()
    test_chat = "test_chat_99"
    save_message("m1", test_chat, "u1", "user", "Secret Recipe")
    
    messages = get_messages_by_chat(test_chat)
    assert len(messages) >= 1
    assert messages[0]['content'] == "Secret Recipe"
