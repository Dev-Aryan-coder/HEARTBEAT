import asyncio
import sys
import os
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.getcwd())
load_dotenv()

from cells.cell_model import CellFactory, BloodCell, CellType, CellStatus
from answers.answer_router import route_answer
from storage.database import init_database, save_message, save_cell

async def test_phase7():
    print("--- Phase 7 Verification: 3-Level Answer System ---")
    init_database()
    
    # 1. Setup Mock State
    user_id = "user_answer_test"
    chat_id = "chat_depth_test"
    
    # Save a raw message to SQLite for Level 3 to find
    save_message("msg_raw_1", chat_id, user_id, "user", "Remember the recipe for Chocolate Cake: 2 cups flour, 1 cup sugar, 2 eggs.")
    
    # Create the Blood Cell (Purified version)
    cake_cell = CellFactory.from_text(user_id, chat_id, "msg_raw_1", "sess_1", "Chocolate Cake Recipe")
    cake_cell.cell_type = CellType.purified
    cake_cell.status = CellStatus.active
    cake_cell.summary = "User provided ingredients for a Chocolate Cake recipe."
    
    # 2. Test Level 1: Quick (Default)
    print("\n[TEST] Level 1: Quick (Default Trigger)...")
    ans1 = await route_answer("Tell me what you know.", cake_cell)
    print(f"Result: {ans1}")
    if "Quick" in ans1 and "ingredients" in ans1:
        print("✅ Level 1 Success")

    # 3. Test Level 2: Detailed
    print("\n[TEST] Level 2: Detailed (Trigger: 'more detail')...")
    ans2 = await route_answer("Give me more detail.", cake_cell)
    print(f"Result: {ans2}")
    if "Detailed" in ans2:
        print("✅ Level 2 Success")

    # 4. Test Level 3: Full Original (Groq-power)
    print("\n[TEST] Level 3: Full Original (Trigger: 'original source')...")
    ans3 = await route_answer("Show me the original source please.", cake_cell)
    print(f"Result: {ans3}")
    if "Full Original" in ans3:
        print("✅ Level 3 Success (Groq Reconstruction OK)")

    print("\n--- Phase 7 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(test_phase7())
