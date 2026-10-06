import asyncio
import sys
import os
import redis
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.getcwd())
load_dotenv()

from heartbeat.config import get_config
from cells.cell_model import CellFactory
from circulation.artery_queue import push_cell, pop_cell
from circulation.vein_pubsub import publish_purified

async def test_phase4():
    print("--- Phase 4 Verification: Circulation Layer ---")
    
    config = get_config()
    r = redis.Redis(host=config.redis_host, port=config.redis_port, decode_responses=True)
    
    # 1. Test Redis Connection
    try:
        r.ping()
        print("✅ Redis Connection OK")
    except Exception as e:
        print(f"❌ Redis Connection Failed: {e}. Please ensure Redis is running on localhost:6379.")
        return

    # 2. Test Artery (Push/Pop)
    print("\nTesting Artery Queue (Redis Hash)...")
    sample_cell = CellFactory.from_text(
        user_id="user_circ",
        chat_id="chat_circ",
        message_id="msg_circ",
        session_id="sess_circ",
        content="Testing artery logic."
    )
    
    try:
        pushed = push_cell(sample_cell)
        if not pushed:
             print("❌ push_cell returned False (check internal logs)")
        assert pushed is True
        print(f"Pushed cell {sample_cell.cell_id} to artery.")
    except Exception as e:
        print(f"❌ Artery Push Failed: {e}")
        return
    
    popped = pop_cell(sample_cell.cell_id)
    assert popped is not None
    assert popped.cell_id == sample_cell.cell_id
    assert popped.user_raw_content == "Testing artery logic."
    print("✅ Artery Push/Pop OK")

    # 3. Test Vein (Publish)
    print("\nTesting Vein Pub/Sub (Redis Publish)...")
    # We'll just test if publish doesn't throw
    try:
        publish_purified(sample_cell)
        print("✅ Vein Publish OK")
    except Exception as e:
        print(f"❌ Vein Publish Failed: {e}")

    print("\n--- Phase 4 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_phase4())
