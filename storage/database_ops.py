from .database import get_connection, save_cell, get_cell_by_id
from .chroma_client import get_chroma_manager
from .link_vault import get_link_vault, LinkMetadata
from .temporal_graph import TemporalGraph
from .synaptic_network import SynapticNetwork
from cells.cell_model import BloodCell
import datetime
import logging

logger = logging.getLogger("HEARTBEAT_STORAGE_OPS")

async def persist_purified_cell(cell: BloodCell):
    """Unified entry point to save a purified cell into all storage layers."""
    # 1. Save to SQLite (Relational)
    save_cell(cell)
    
    # 2. Save to ChromaDB (Semantic Vector)
    chroma = get_chroma_manager()
    chroma.upsert_cell(cell)
    
    # 3. Upgrade 1: Extract and index Temporal Knowledge Graph Triples
    try:
        content = cell.summary or cell.user_content or cell.user_raw_content or ""
        TemporalGraph.extract_and_store_triples_from_cell(
            cell_id=cell.cell_id,
            content=content,
            user_id=cell.user_id
        )
    except Exception as e:
        logger.debug(f"[STORAGE_OPS] Temporal graph extraction note: {e}")

    # 4. Save to Link Vault (if any URLs discovered)
    if cell.purified_data and cell.purified_data.metadata.get("urls"):
        vault = get_link_vault()
        urls = cell.purified_data.metadata.get("urls")
        for url_data in urls:
            link = LinkMetadata(
                url=str(url_data),
                cell_id=cell.cell_id,
                user_id=cell.user_id,
                title=cell.purified_data.metadata.get("topic_id", "Unknown"),
                topic_id=cell.purified_data.metadata.get("topic_id")
            )
            vault.save_link(link)

def get_semantic_memory(user_id: str, query: str, limit: int = 5):
    """
    Retrieves long-term semantic context for the LLM.
    Enforces State Supremacy and triggers:
    1. Hebbian Synaptic Reinforcement on co-retrieved cells
    2. Associative Priming to pull wired neighbors
    """
    chroma = get_chroma_manager()
    res = chroma.search_related(query, n_results=limit * 2, user_id=user_id)
    if not res:
        return []
    
    # State Supremacy Filter: Cross-reference SQLite so expired/superseded cells never leak
    active_res = []
    try:
        conn = get_connection()
        cursor = conn.cursor()
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
    except Exception:
        active_res = res[:limit]

    # Upgrade 3: Hebbian Synaptic Reinforcement & Associative Priming
    if active_res:
        retrieved_ids = [hit.get("id") for hit in active_res if hit.get("id")]
        try:
            # 1. Fire together -> Wire together (+0.2 boost)
            SynapticNetwork.reinforce_co_occurrence(retrieved_ids, boost=0.2)
            
            # 2. Associative Priming: find strongly wired neighbors not in the original result set
            associated = SynapticNetwork.get_associated_cells(retrieved_ids, top_k=2)
            conn = get_connection()
            cursor = conn.cursor()
            for assoc in associated:
                assoc_id = assoc["cell_id"]
                cursor.execute("SELECT cell_id, summary, user_content, status FROM blood_cells WHERE cell_id = ?", (assoc_id,))
                assoc_row = cursor.fetchone()
                if assoc_row and assoc_row["status"] == "active":
                    text = assoc_row["summary"] or assoc_row["user_content"] or ""
                    active_res.append({
                        "id": assoc_id,
                        "metadata": {"associative_primed": True, "synaptic_weight": assoc["synaptic_weight"]},
                        "score": 0.99,
                        "document": text
                    })
        except Exception as e:
            logger.debug(f"[STORAGE_OPS] Synaptic reinforcement note: {e}")

    return active_res

def list_user_data_inventory(user_id: str):
    """Returns a full inventory summary for the user."""
    pass

