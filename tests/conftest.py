import pytest
import os
import sqlite3
from fastapi.testclient import TestClient
from main import app
from storage.database import get_connection, _db_connection

# Use a separate test database
TEST_DB_PATH = "data/test_heartbeat.db"

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Sets up a temporary database for the entire test session."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
    
    # Override the connection for tests in storage.database
    import storage.database
    conn = sqlite3.connect(TEST_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    storage.database._db_connection = conn
    
    from storage.database import init_database
    init_database()
    
    yield
    
    # Cleanup after session
    try:
        if storage.database._db_connection:
            storage.database._db_connection.close()
    except Exception:
        pass
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
        except PermissionError:
            pass # Windows might lock it

@pytest.fixture
def client():
    """Returns a FastAPI TestClient."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user():
    return "PYTEST_BOT"

@pytest.fixture
def test_chat(client, test_user):
    chat_id = "test_chat_123"
    # Endpoints use user_id from query params or body
    return chat_id
