from pydantic import BaseModel
from typing import Optional
from answers.answer_router import route_answer
from storage.database import get_cell_by_id
from cells.cell_model import BloodCell

class AnswerRequest(BaseModel):
    user_id: str
    cell_id: str
    message: Optional[str] = "Tell me more"
    depth_level: Optional[int] = 1

async def process_answer_request(req: AnswerRequest):
    """Integrates Phase 7 Answer Router into the API."""
    # 1. Load the cell from storage
    cell_data = get_cell_by_id(req.cell_id)
    if not cell_data:
        return {"error": "Cell not found."}
    
    # 2. Reconstruct cell model
    try:
        cell = BloodCell.model_validate(cell_data)
    except Exception as e:
        # Fallback if validation fails slightly
        print(f"Validation error: {e}")
        from cells.cell_model import CellStatus
        cell = BloodCell(**cell_data)

    # 3. Route to the correct intelligence level
    # Map depth_level to keywords for the router
    effective_msg = req.message or ""
    if req.depth_level == 3: effective_msg += " raw source original"
    elif req.depth_level == 2: effective_msg += " detailed expanded more"
    elif req.depth_level == 1: effective_msg += " quick summary"
    
    response = await route_answer(effective_msg, cell)
    return {"response": response}
