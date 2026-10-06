import asyncio
import sys
import os
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load .env for real test
load_dotenv(os.path.join(os.getcwd(), '.env'))
sys.path.append(os.getcwd())

from llm.client import call_llm, call_heart_l2
from llm.key_manager import get_fallback_model

async def test_phase3():
    print("--- Phase 3 Verification: LLM Client & Rotation ---")
    
    # 1. Test Prompt Building
    print("\nTesting Prompt Logic...")
    from llm.prompts import build_heart_l3_prompt
    prompt = build_heart_l3_prompt("I love Python", "Python is great")
    assert "USER SAID: I love Python" in prompt
    assert "AI RESPONDED: Python is great" in prompt
    print("✅ Prompts OK")

    # 2. Test Key Rotation (Mocking 429)
    print("\nTesting 429 Key Rotation (Mocked)...")
    
    # Mock httpx response for 429
    mock_429_resp = MagicMock()
    mock_429_resp.status_code = 429
    
    # Mock successful retry response
    mock_success_resp = MagicMock()
    mock_success_resp.status_code = 200
    mock_success_resp.json.return_value = {
        "choices": [{"message": {"content": '{"intent_type": "permanent_fact", "is_permanent": true}'}}]
    }
    
    # We mock the post method to return 429 then success
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = [mock_429_resp, mock_success_resp]
        
        # This call should trigger a retry
        result = await call_heart_l2("Test message")
        print(f"Result after 429 retry: {result}")
        
        # Verify post was called twice
        assert mock_post.call_count == 2
        print("✅ 429 Key Rotation OK")

    # 3. Test Real Call (Optional Integration)
    print("\nAttempting Real LLM Call (optional)...")
    try:
        # Simple classification check
        result = await call_heart_l2("Hi Heartbeat!")
        print(f"Real L2 Call Result: {result}")
        print("✅ Real LLM Call OK")
    except Exception as e:
        print(f"⚠️ Real LLM Call failed (likely keys): {e}")

    print("\n--- Phase 3 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_phase3())
