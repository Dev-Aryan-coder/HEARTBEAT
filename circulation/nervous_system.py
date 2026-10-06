import asyncio
from typing import List
from llm.client import call_nervous
from llm.prompts import build_trigger_prompt
from cells.cell_model import BloodCell

async def detect_dormant_triggers(user_message: str, dormant_cells: List[BloodCell]) -> List[BloodCell]:
    """Uses Qwen (Nervous Key) to detect if any dormant memory cells are relevant."""
    if not dormant_cells:
        return []
    
    # Extract summaries for the LLM
    summaries = [cell.summary for cell in dormant_cells if cell.summary]
    if not summaries:
        return []
    
    prompt = build_trigger_prompt(user_message, summaries)
    
    try:
        # Call Qwen
        response_json = await call_nervous(prompt)
        # Parse indices (e.g. [0, 2])
        import json
        indices = json.loads(response_json)
        
        triggered = []
        for idx in indices:
            if 0 <= idx < len(dormant_cells):
                triggered.append(dormant_cells[idx])
        return triggered
        
    except Exception as e:
        print(f"Nervous system trigger error: {e}")
        return []

async def handle_websocket_loop():
    """Placeholder for the nervous system's WebSocket loop logic."""
    # This will be fully implemented in Phase 5/6 with FastAPI
    pass
