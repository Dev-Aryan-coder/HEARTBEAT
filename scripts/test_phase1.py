import sys
import os
from dotenv import load_dotenv

# Explicitly load dotenv from root
load_dotenv(os.path.join(os.getcwd(), '.env'))

# Add root to path
sys.path.append(os.getcwd())

from heartbeat.config import get_config
from cells.cell_model import CellFactory, BloodCell
from storage.database import init_database, save_cell, get_cell_by_id, create_user, create_chat

def test_phase1():
    print("--- Phase 1 Verification ---")
    
    # 1. Test Config
    print("Testing Config...")
    config = get_config()
    print(f"Config loaded: {config.sqlite_db_path}")
    assert config.heart_l3_key == "test_l3"
    print("✅ Config OK")

    # 2. Test Cell Model & Factory
    print("\nTesting Cell Model & Factory...")
    cell = CellFactory.from_text(
        user_id="user_123",
        chat_id="chat_456",
        message_id="msg_789",
        session_id="sess_000",
        content="Hello Heartbeat!"
    )
    print(f"Cell created: {cell.cell_id} | Status: {cell.status}")
    assert cell.user_raw_content == "Hello Heartbeat!"
    print("✅ Cell Model OK")

    # 3. Test Database
    print("\nTesting Database...")
    if os.path.exists("test_heartbeat.db"):
        os.remove("test_heartbeat.db")
    
    init_database()
    print("Database initialized (Tables created)")
    
    # Create required relations
    create_user("user_123", "Test User", "test@example.com")
    create_chat("chat_456", "user_123", "Test Chat")
    
    # Save the cell
    save_cell(cell)
    print(f"Cell {cell.cell_id} saved to database.")
    
    # Retrieve the cell
    retrieved = get_cell_by_id(cell.cell_id)
    print(f"Retrieved cell status: {retrieved['status']}")
    assert retrieved['user_raw_content'] == "Hello Heartbeat!"
    print("✅ Database OK")

    print("\n--- Phase 1 ALL PASS ---")

if __name__ == "__main__":
    try:
        test_phase1()
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
