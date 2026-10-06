import asyncio
import logging
import os
import sqlite3
import concurrent.futures
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from cells.cell_model import BloodCell, CellStatus, CellType
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HEARTBEAT_STABILITY_TEST")

def setup_test_env():
    test_db = "data/manual_test.db"
    if not os.path.exists("data"): os.makedirs("data")
    if os.path.exists(test_db):
        try: os.remove(test_db)
        except: pass
    
    from storage.database import init_database
    import storage.database
    storage.database._db_connection = sqlite3.connect(test_db, check_same_thread=False)
    storage.database._db_connection.row_factory = sqlite3.Row
    storage.database._db_connection.execute("PRAGMA journal_mode=WAL")
    storage.database._db_connection.execute("PRAGMA foreign_keys = ON")
    init_database()
    return test_db

async def test_api_loop(client: TestClient):
    logger.info("--- Testing API Loop ---")
    
    # Mocking run_pipeline to avoid ANY LLM calls or complex logic
    with patch("api.routes.run_pipeline", new_callable=AsyncMock) as mock_pipe, \
         patch("api.routes.call_brain", new_callable=AsyncMock) as mock_brain:
        
        mock_brain.return_value = "AI Response"
        # Return a dummy list of cells
        mock_pipe.return_value = [
            BloodCell(
                cell_id="test_1", user_id="TEST_USER", chat_id="chat_1",
                message_id="m1", session_id="s1", status=CellStatus.active,
                cell_type=CellType.purified, user_raw_content="hi",
                user_content="hi", topic_id="general", summary="hi",
                created_at=datetime.utcnow()
            )
        ]
        
        response = client.post("/api/message?user_id=TEST_USER", json={
            "user_id": "TEST_USER", "chat_id": "chat_1", "session_id": "s1", "content": "Hello."
        })
        
        if response.status_code != 200:
            logger.error(f"❌ API Failure: {response.status_code} - {response.text}")
            return False
            
        logger.info("✅ API Message Loop OK")
        return True

async def test_concurrency(client: TestClient):
    logger.info("--- Testing Database Concurrency ---")
    
    def send_req(i):
        return client.post("/api/message?user_id=STRESS_USER", json={
            "user_id": "STRESS_USER", "chat_id": f"c_{i}", "session_id": "s1", "content": "stress"
        }).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        with patch("api.routes.run_pipeline", new_callable=AsyncMock) as mock_pipe, \
             patch("api.routes.call_brain", new_callable=AsyncMock) as mock_brain:
            
            mock_brain.return_value = "stress ok"
            mock_pipe.return_value = []
            
            futures = [executor.submit(send_req, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
    if not all(r == 200 for r in results):
        logger.error(f"❌ Concurrency Failures: {results}")
        return False
    logger.info("✅ Database WAL Concurrency OK")
    return True

async def run_all():
    db_path = setup_test_env()
    client = TestClient(app)
    
    passed = True
    passed &= await test_api_loop(client)
    passed &= await test_concurrency(client)
    
    if passed:
        print("\n" + "="*50)
        print("🏆 HEARTBEAT HARDENING VERIFIED STABLE")
        print("="*50)
    else:
        print("\n" + "!"*50)
        print("❌ STABILITY VERIFICATION FAILED")
        print("!"*50)
        exit(1)

if __name__ == "__main__":
    asyncio.run(run_all())
