from .level1_quick import get_quick_answer
from .level2_detailed import get_detailed_answer
from .level3_original import get_full_original_answer
from cells.cell_model import BloodCell
import re

async def route_answer(user_message: str, current_cell: BloodCell) -> str:
    """Intelligently detects depth trigger and routes the answer."""
    message_lc = user_message.lower()
    
    # 1. Detect Level 3: Full Original (Highest Priority)
    l3_patterns = ["full", "original", "source", "raw", "exact"]
    if any(p in message_lc for p in l3_patterns):
        return await get_full_original_answer(current_cell)
        
    # 2. Detect Level 2: Detailed
    l2_patterns = ["detail", "more", "everything", "chained", "expanded", "depth"]
    if any(p in message_lc for p in l2_patterns):
        return get_detailed_answer(current_cell)
        
    # 3. Default: Level 1 Quick
    return get_quick_answer(current_cell)
