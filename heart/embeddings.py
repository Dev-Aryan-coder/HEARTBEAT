import os
import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer, util

# Configure logging
logger = logging.getLogger("HEARTBEAT_EMBEDDINGS")

class EmbeddingModel:
    """ISSUE 5.1 FIX: Centralized Embedding Singleton to save RAM."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            # Silence noisy logs during load
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            os.environ["TQDM_DISABLE"] = "1"
            
            logger.info("Initializing Shared SentenceTransformer ('all-MiniLM-L6-v2')...")
            # Create the instance
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
            cls._instance.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            logger.info("Shared Embedding Model Ready.")
        return cls._instance

    def encode(self, text: str) -> List[float]:
        """Encodes text into a normalized embedding vector."""
        return self.model.encode(text).tolist()

    def similarity(self, a_emb: List[float], b_emb: List[float]) -> float:
        """Calculates cosine similarity between two vectors."""
        return float(util.cos_sim(a_emb, b_emb).item())

def get_embedding_model() -> EmbeddingModel:
    """Returns the shared singleton instance."""
    return EmbeddingModel()
