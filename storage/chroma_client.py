import chromadb
from chromadb.config import Settings
from heartbeat.config import get_config
from cells.cell_model import BloodCell
from heart.embeddings import get_embedding_model
from typing import List
import logging

# Configure logging
logger = logging.getLogger("HEARTBEAT_CHROMA")

class ChromaManager:
    """ISSUE 5.1 & 5.4 FIX: Manages the vector database for long-term memory."""
    def __init__(self):
        config = get_config()
        # Initialize client with persistent storage
        self.client = chromadb.PersistentClient(path=config.chroma_db_path)
        self.collection = self.client.get_or_create_collection(
            name="heartbeat_cells",
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB initialized at {config.chroma_db_path}")

    def upsert_cell(self, cell: BloodCell):
        """Encodes and stores/updates a cell in the vector database."""
        text_to_embed = cell.summary or cell.user_content or cell.user_raw_content
        if not text_to_embed:
            logger.warning(f"Skipping cell {cell.cell_id} — no text to embed")
            return
            
        # Use shared singleton embedding model
        model = get_embedding_model()
        embedding = model.encode(text_to_embed)
        
        self.collection.upsert(
            ids=[cell.cell_id],
            embeddings=[embedding],
            metadatas=[{
                "user_id": cell.user_id,
                "session_id": cell.session_id or "unknown",
                "topic_id": cell.topic_id or "",
                "timestamp": str(cell.created_at),
                "summary": text_to_embed[:500] # Cap metadata summary length
            }],
            documents=[text_to_embed]
        )

    def search_related(self, query: str, n_results: int = 5, user_id: str = None) -> List[dict]:
        """Searches for semantically related cells using the shared singleton."""
        model = get_embedding_model()
        query_embedding = model.encode(query)
        
        where_filter = {}
        if user_id:
            where_filter["user_id"] = user_id

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )
        
        # Format results for consumption
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted.append({
                    "id": results['ids'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": results['distances'][0][i]
                })
        return formatted

# Singleton instance for high-performance access
_chroma_instance = None
def get_chroma_manager():
    global _chroma_instance
    if _chroma_instance is None:
        _chroma_instance = ChromaManager()
    return _chroma_instance
