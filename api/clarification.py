from pydantic import BaseModel
from storage.database import update_cell_status, get_connection, get_cell_by_id
import logging

logger = logging.getLogger("HEARTBEAT_CLARIFY")

class ClarifyRequest(BaseModel):
    # ISSUE 30 FIX: Match frontend payload — frontend sends 'user_answer', not 'answer'
    cell_id: str
    user_answer: str

def resolve_ambiguity(req: ClarifyRequest):
    """Updates the cell in SQLite with the user's clarification.
    ISSUE 21 FIX: Verify cell exists before updating; check rowcount."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Verify the cell exists first
    cell = get_cell_by_id(req.cell_id)
    if not cell:
        logger.warning(f"Clarification rejected for non-existent cell: {req.cell_id}")
        conn.close()
        return {"status": "error", "message": f"Cell {req.cell_id} not found"}

    # 2. Update the cell in blood_cells
    cursor.execute("""
        UPDATE blood_cells
        SET status = 'active',
            clarification_answer = ?,
            is_ambiguous = 0
        WHERE cell_id = ?
    """, (req.user_answer, req.cell_id))

    if cursor.rowcount == 0:
        conn.close()
        return {"status": "error", "message": "No rows updated"}

    conn.commit()
    conn.close()

    logger.info(f"Clarification resolved for cell: {req.cell_id}")
    return {"status": "resolved", "cell_id": req.cell_id, "message": "Memory ambiguity resolved. Cell reactivated."}
