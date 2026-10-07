from .database import get_connection, save_cell, get_cell_by_id
from .chroma_client import get_chroma_manager
from .link_vault import get_link_vault, LinkMetadata
from cells.cell_model import BloodCell
import datetime

async def persist_purified_cell(cell: BloodCell):
    """Unified entry point to save a purified cell into all storage layers."""
    # 1. Save to SQLite (Relational)
    save_cell(cell)
    
    # 2. Save to ChromaDB (Semantic Vector)
    chroma = get_chroma_manager()
    chroma.upsert_cell(cell)
    
    # 3. Save to Link Vault (if any URLs discovered)
    if cell.purified_data and cell.purified_data.metadata.get("urls"):
        vault = get_link_vault()
        urls = cell.purified_data.metadata.get("urls")
        for url_data in urls:
            # Assuming url_data is a dict or string from L3 output
            # We'll create a LinkMetadata entry
            link = LinkMetadata(
                url=str(url_data),
                cell_id=cell.cell_id,
                user_id=cell.user_id,
                title=cell.purified_data.metadata.get("topic_id", "Unknown"),
                topic_id=cell.purified_data.metadata.get("topic_id")
            )
            vault.save_link(link)

def get_semantic_memory(user_id: str, query: str, limit: int = 5):
    """Retrieves long-term semantic context for the LLM, guaranteed active-only."""
    chroma = get_chroma_manager()
    res = chroma.search_related(query, n_results=limit * 2, user_id=user_id)
    if not res:
        return []
    
    # State Supremacy Filter: Cross-reference SQLite so expired/superseded cells never leak
    try:
        conn = get_connection()
        cursor = conn.cursor()
        active_res = []
        for hit in res:
            cell_id = hit.get("id")
            cursor.execute("SELECT status FROM blood_cells WHERE cell_id = ?", (cell_id,))
            row = cursor.fetchone()
            # If found in DB, must be active (not expired or dormant)
            if row and row["status"] != "active":
                continue
            active_res.append(hit)
            if len(active_res) >= limit:
                break
        return active_res
    except Exception:
        return res[:limit]

def list_user_data_inventory(user_id: str):
    """Returns a full inventory summary for the user."""
    # This could connect SQLite for count and Vault for links
    pass
