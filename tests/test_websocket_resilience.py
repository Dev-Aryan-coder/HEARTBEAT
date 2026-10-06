import pytest
from fastapi.testclient import TestClient

def test_websocket_connection(client: TestClient, test_user):
    """Test Phase 6.3: WebSocket connecting and welcome message."""
    with client.websocket_connect(f"/ws/connect/{test_user}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "WELCOME"
        assert data["user_id"] == test_user

def test_websocket_bad_user_id(client: TestClient):
    """Test that empty user_id is handled (though currently the route might allow it)."""
    # This is more of a safety check
    with client.websocket_connect("/ws/connect/ ") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "WELCOME"
