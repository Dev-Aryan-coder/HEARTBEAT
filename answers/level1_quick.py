from cells.cell_model import BloodCell

def get_quick_answer(cell: BloodCell) -> str:
    """Instant Level 1 Answer: Returns the summary only (Zero LLM)."""
    if not cell.summary:
        return "No summary available for this intelligence unit."
    
    return f"💓 [Level 1: Quick] {cell.summary}"
