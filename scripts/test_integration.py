import httpx
import asyncio
import uuid

BASE_URL = "http://127.0.0.1:8000"
USER_ID = f"U_TEST_{uuid.uuid4().hex[:6]}"
CHAT_ID = f"C_TEST_{uuid.uuid4().hex[:6]}"

async def run_tests():
    print(f"STARTING HEARTBEAT INTEGRATION AUDIT (Increased Timeout)")
    score = 0
    client = httpx.AsyncClient(timeout=60.0) # Increased to 60s

    try:
        # 1. Ping
        r = await client.get(f"{BASE_URL}/api/ping")
        if r.status_code == 200:
            print("Test 1 (Ping): PASS")
            score += 1

        # 2. Message
        cell_id = None
        payload = {"user_id": USER_ID, "chat_id": CHAT_ID, "session_id": "test", "content": "I like writing code in Python."}
        r = await client.post(f"{BASE_URL}/api/message", json=payload)
        if r.status_code == 200:
            print("Test 2 (Message): PASS")
            score += 1
            cell_id = r.json().get("cell_id")
        else: print(f"Test 2 (Message): FAIL {r.status_code}")

        # 3. Cells
        r = await client.get(f"{BASE_URL}/api/cells/{USER_ID}")
        if r.status_code == 200 and len(r.json().get("cells", [])) > 0:
            print("Test 3 (Cells): PASS")
            score += 1

        # 4. History
        r = await client.get(f"{BASE_URL}/api/history/{CHAT_ID}")
        if r.status_code == 200:
            print("Test 4 (History): PASS")
            score += 1

        # 5. Chats
        r = await client.get(f"{BASE_URL}/api/chats/{USER_ID}")
        if r.status_code == 200 and len(r.json().get("chats", [])) > 0:
            print("Test 5 (Chats): PASS")
            score += 1

        # 6. Stats
        r = await client.get(f"{BASE_URL}/api/stats/{USER_ID}")
        if r.status_code == 200:
            print("Test 6 (Stats): PASS")
            score += 1

        # 7. Pipeline
        payload = {"user_id": USER_ID, "chat_id": "tp", "session_id": "s", "content": "Pipeline test"}
        r = await client.post(f"{BASE_URL}/api/test/pipeline", json=payload)
        if r.status_code == 200:
            print("Test 7 (Pipeline): PASS")
            score += 1

        # 8. Answer
        if cell_id:
            payload = {"user_id": USER_ID, "cell_id": cell_id, "depth_level": 1}
            r = await client.post(f"{BASE_URL}/api/answer", json=payload)
            if r.status_code == 200:
                print("Test 8 (Answer): PASS")
                score += 1
            else: print(f"Test 8 (Answer): FAIL {r.status_code} {r.text}")
        else: print("Test 8 (Answer): SKIP")

    finally: await client.aclose()
    print(f"FINAL INTEGRATION SCORE: {score}/8")

if __name__ == "__main__":
    asyncio.run(run_tests())
