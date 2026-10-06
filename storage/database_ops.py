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
    """Retrieves long-term semantic context for the LLM."""
    chroma = get_chroma_manager()
    res = chroma.search_related(query, n_results=limit, user_id=user_id)
    return res

def list_user_data_inventory(user_id: str):
    """Returns a full inventory summary for the user."""
    # This could connect SQLite for count and Vault for links
    pass
