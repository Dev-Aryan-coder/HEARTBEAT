from storage.database import get_cells_by_user
from cells.cell_model import BloodCell
from typing import List

def get_detailed_answer(head_cell: BloodCell) -> str:
    """Detailed Level 2 Answer: Aggregates summaries from any related cells in the chain."""
    if not head_cell.chain_id:
        return f"💓 [Level 2: Detailed] {head_cell.summary}"
    
    # Fetch all cells with the same chain_id
    related_cells = get_cells_by_user(head_cell.user_id)
    chain_cells = [c for c in related_cells if c.get('chain_id') == head_cell.chain_id]
    
    # Sort by part number if available
    chain_cells.sort(key=lambda x: x.get('part_number', 0))
    
    summaries = [c.get('summary', '') for c in chain_cells if c.get('summary')]
    
    if not summaries:
        return f"💓 [Level 2: Detailed] {head_cell.summary}"
    
    combined = "\n- ".join(summaries)
    return f"💓 [Level 2: Detailed Chain]\nSummary Chain:\n- {combined}"
