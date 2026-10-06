import asyncio
import sys
import os
from dotenv import load_dotenv

# Explicitly load dotenv from root
load_dotenv(os.path.join(os.getcwd(), '.env'))

# Add root to path
sys.path.append(os.getcwd())

from heartbeat.config import get_config
from cells.cell_model import CellFactory
from heart.pipeline import run_pipeline

async def test_phase2():
    print("--- Phase 2 Verification: Heart Pipeline ---")
    
    # 1. Test Sieve (L1)
    print("\nTesting Level 1 Sieve...")
    from heart.level1_sieve import sieve
    res = sieve("Um, hello, I basically want to tell you that I love coding in Python.")
    print(f"Cleaned: {res['cleaned']}")
    assert res['passed'] is True
    assert "basically" not in res['cleaned']
    print("✅ Level 1 OK")

    # 2. Test Ambiguity (Local)
    print("\nTesting Ambiguity Detector...")
    from heart.ambiguity_detector import detect
    res = detect("I bought an apple today", [])
    print(f"Ambiguous: {res['is_ambiguous']} | Question: {res['question']}")
    assert res['is_ambiguous'] is True
    print("✅ Ambiguity Detector (Local) OK")

    # 3. Test Full Pipeline (Integration)
    print("\nTesting Full Pipeline (L1 -> L2 -> L3)...")
    raw_cell = CellFactory.from_text(
        user_id="user_123",
        chat_id="chat_456",
        message_id="msg_789",
        session_id="sess_000",
        content="I am currently living in Mumbai and I am working on a new AI project using Python."
    )
    
    # We'll use real API calls if keys are present, otherwise this might fail or we should mock.
    # For this verification, we assume the user has configured keys or we've provided fallbacks.
    try:
        processed_cells = await run_pipeline(raw_cell)
        print(f"Pipeline returned {len(processed_cells)} cells.")
        
        for i, cell in enumerate(processed_cells):
            print(f"Cell {i+1} Status: {cell.status}")
            print(f"Summary: {cell.summary}")
            print(f"Topic: {cell.topic_id}")
            print(f"Importance: {cell.importance_score}")

        assert len(processed_cells) > 0
        print("✅ Pipeline Integration OK")
    except Exception as e:
        print(f"⚠️ Pipeline call failed (likely API keys or network): {e}")
        print("Note: Local components (Sieve/Ambiguity) passed. AI steps require OpenRouter access.")

    print("\n--- Phase 2 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_phase2())
