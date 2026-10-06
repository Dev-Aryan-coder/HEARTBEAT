import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_ping(client: TestClient):
    """Test the refined health check endpoint."""
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()

@patch("api.routes.call_brain", new_callable=AsyncMock)
def test_create_and_list_chats(mock_brain, client: TestClient, test_user):
    """Test chat persistence and listing."""
    mock_brain.return_value = "Test AI Response"
    chat_id = "pytest_chat_1"
    
    # 1. Create a message which creates the chat
    response = client.post(
        f"/api/message?user_id={test_user}",
        json={
            "user_id": test_user,
            "chat_id": chat_id,
            "session_id": "sess_1",
            "content": "Hello, this is a test chat creation."
        }
    )
    assert response.status_code == 200
    
    # 2. List chats for the user
    response = client.get(f"/api/chats/{test_user}")
    assert response.status_code == 200
    chats = response.json()["chats"]
    assert any(c["chat_id"] == chat_id for c in chats)

def test_validation_limits(client: TestClient, test_user):
    """Test Pydantic validation (Phase 2.2)."""
    # Test min_length
    response = client.post(
        f"/api/message?user_id={test_user}",
        json={
            "user_id": test_user,
            "chat_id": "c1",
            "session_id": "s1",
            "content": "" # Invalid: min_length=1
        }
    )
    assert response.status_code == 422

@patch("api.routes.call_brain", new_callable=AsyncMock)
def test_cascade_delete(mock_brain, client: TestClient, test_user):
    """Test Chat deletion cascading (Phase 2.4)."""
    mock_brain.return_value = "Delete me response"
    chat_id = "delete_me_123"
    client.post(
        f"/api/message?user_id={test_user}",
        json={
            "user_id": test_user, "chat_id": chat_id, "session_id": "s1", "content": "Evidence for deletion."
        }
    )
    
    # Verify messages exist
    hist = client.get(f"/api/history/{chat_id}")
    assert len(hist.json()["messages"]) > 0
    
    # DELETE
    response = client.delete(f"/api/chats/{chat_id}")
    assert response.status_code == 200
    
    # Verify messages are GONE
    hist = client.get(f"/api/history/{chat_id}")
    assert len(hist.json()["messages"]) == 0
