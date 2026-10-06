import asyncio
import os
import httpx
from dotenv import load_dotenv

# Test configurations
TEST_CONFIGS = [
    ("HEARTBEAT_HEART_L3_KEY", "llama-3.3-70b-versatile", "L3 Purifier"),
    ("HEARTBEAT_HEART_L2_KEY", "llama-3.1-8b-instant", "L2 Valve"),
    ("HEARTBEAT_BRAIN_KEY", "llama-3.1-8b-instant", "Brain"),
    ("HEARTBEAT_NERVOUS_KEY", "llama-3.3-70b-versatile", "Nervous System"),
    ("HEARTBEAT_FALLBACK_KEY", "llama-3.1-8b-instant", "Fallback")
]

async def check_key(env_name, model, label):
    key = os.getenv(env_name)
    if not key or "your-groq-key" in key:
        print(f"[FAIL] {label} ({env_name}): Missing or placeholder key.")
        return False
    
    # Auto-detect Groq vs OpenRouter
    is_groq = key.startswith("gsk_")
    base_url = "https://api.groq.com/openai/v1" if is_groq else "https://openrouter.ai/api/v1"
    
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 10
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            if r.status_code == 200:
                resp = r.json()
                content = resp["choices"][0]["message"]["content"]
                print(f"[OK]   {label} ({env_name}): Groq={is_groq} | Response: {content.strip()}")
                return True
            else:
                print(f"[FAIL] {label} ({env_name}): Failed with status {r.status_code} ({base_url})")
                return False
        except Exception as e:
            print(f"[FAIL] {label} ({env_name}): Error - {str(e)}")
            return False

async def main():
    print("--- Verifying Finalized Heartbeat Intelligence Stack ---")
    load_dotenv(override=True)
    tasks = [check_key(env_name, model, label) for env_name, model, label in TEST_CONFIGS]
    results = await asyncio.gather(*tasks)
    
    print("\n--- Final Status Summary ---")
    successful = sum(1 for r in results if r)
    print(f"Total Components: {len(TEST_CONFIGS)}")
    print(f"Verified & Active: {successful}")
    print(f"Failed/Inactive: {len(TEST_CONFIGS) - successful}")

if __name__ == "__main__":
    asyncio.run(main())
