import pytest
import threading
import concurrent.futures
from fastapi.testclient import TestClient

def send_message_task(client: TestClient, user_id: str, i: int):
    """Sends a message request with a unique chat_id."""
    response = client.post(
        f"/api/message?user_id={user_id}",
        json={
            "user_id": user_id,
            "chat_id": f"stress_chat_{i}",
            "session_id": "stress_sess",
            "content": f"Stress test message {i}"
        }
    )
    return response.status_code

def test_concurrency_stress(client: TestClient, test_user):
    """Test Phase 6.4: Fire 50 concurrent requests to verify WAL/Singleton."""
    num_requests = 50
    status_codes = []
    
    # Use ThreadPoolExecutor to simulate concurrent users
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_message_task, client, test_user, i) for i in range(num_requests)]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                status_codes.append(future.result())
            except Exception as e:
                pytest.fail(f"Concurrent request failed with error: {e}")

    # Verify all requests succeeded (200 OK)
    assert len(status_codes) == num_requests
    assert all(code == 200 for code in status_codes)
    
    # Verify chats were created
    response = client.get(f"/api/chats/{test_user}")
    chats = response.json()["chats"]
    # We expect 50+ chats (some already created in other tests)
    assert len(chats) >= num_requests
