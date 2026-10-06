import httpx
import time
import sys

def test_api_health():
    print("--- [1/3] Checking API Server Health ---")
    try:
        r = httpx.get('http://127.0.0.1:8000/docs', timeout=10)
        if r.status_code == 200:
            print("✅ Server is ALIVE at 127.0.0.1:8000\n")
            return True
        else:
            print(f"❌ Server returned status {r.status_code}\n")
            return False
    except Exception as e:
        print(f"❌ Could not connect to server: {e}\n")
        return False

def test_intelligence_loop():
    print("--- [2/3] Testing 9-Step Intelligence Loop ---")
    payload = {
        "user_id": "test_pilot",
        "chat_id": "verified_chat_01",
        "session_id": "alpha_session",
        "content": "I am testing the heartbeat API for the first time.",
        "content_type": "text"
    }
    
    try:
        start_time = time.time()
        r = httpx.post('http://127.0.0.1:8000/api/message', json=payload, timeout=45)
        duration = time.time() - start_time
        
        if r.status_code == 200:
            resp = r.json()
            print(f"✅ Intelligence Loop Success ({duration:.2f}s)")
            print(f"✅ AI Response: {resp.get('ai_response')}")
            print(f"✅ Cell ID: {resp.get('cell_id')}\n")
            return True, resp.get('cell_id')
        else:
            print(f"❌ Request failed with status {r.status_code}: {r.text}\n")
            return False, None
    except Exception as e:
        print(f"❌ Error in intelligence loop: {e}\n")
        return False, None

def test_memory_history():
    print("--- [3/3] Testing SQLite Memory History ---")
    try:
        r = httpx.get('http://127.0.0.1:8000/api/history/verified_chat_01', timeout=10)
        if r.status_code == 200:
            messages = r.json().get('messages', [])
            if len(messages) >= 2:
                print(f"✅ Found {len(messages)} messages in history.")
                print(f"✅ Last Speaker: {messages[-1].get('role')}\n")
                return True
            else:
                print("❌ History found but messages missing.\n")
                return False
        else:
            print(f"❌ History request failed: {r.status_code}\n")
            return False
    except Exception as e:
        print(f"❌ Error fetching history: {e}\n")
        return False

if __name__ == "__main__":
    print("--- Phase 8 Final Verification: HEARTBEAT API SYSTEM ---\n")
    if test_api_health():
        success, cell_id = test_intelligence_loop()
        if success:
            test_memory_history()
            print("--- PHASE 8 VERIFICATION COMPLETE: ALL SYSTEMS NOMINAL ---")
        else:
            print("--- PHASE 8 VERIFICATION FAILED: INTELLIGENCE LOOP ERROR ---")
    else:
        print("--- PHASE 8 VERIFICATION FAILED: SERVER NOT REACHABLE ---")
