import asyncio
import os
import sys
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.getcwd())

from llm.client import call_nervous
from llm.prompts import build_trigger_prompt

async def test_nervous():
    print("--- Testing Nervous System Key ---")
    load_dotenv()
    
    user_msg = "Tell me about my favorite coding language."
    summaries = [
        "User loves Python for its simplicity.",
        "User is currently living in Mumbai.",
        "User is working on a new AI project."
    ]
    
    prompt = build_trigger_prompt(user_msg, summaries)
    print(f"Prompt built. Calling {os.getenv('HEARTBEAT_NERVOUS_KEY')[:10]}...")
    
    try:
        response = await call_nervous(prompt)
        print(f"Response: {response}")
        print("✅ Nervous System Key Test Complete")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_nervous())
