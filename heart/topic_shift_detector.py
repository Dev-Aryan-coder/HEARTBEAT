import os
import logging
from typing import List, Optional
from heart.embeddings import get_embedding_model

def get_embedding(text: str) -> List[float]:
    """Returns a 384-dimension embedding vector for the text using the shared singleton."""
    model = get_embedding_model()
    return model.encode(text)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Computes cosine similarity between two vectors using the shared singleton."""
    model = get_embedding_model()
    return model.similarity(a, b)

def detect_shift(current_text: str, previous_embedding: Optional[List[float]]) -> dict:
    """Detects if the current text represents a shift in topic."""
    current_embedding = get_embedding(current_text)
    
    if previous_embedding is None:
        return {"is_shift": False, "similarity": 1.0, "embedding": current_embedding}
    
    similarity = cosine_similarity(current_embedding, previous_embedding)
    # Topic shift if similarity dropped significantly
    is_shift = similarity < 0.35
    
    return {
        "is_shift": is_shift,
        "similarity": similarity,
        "embedding": current_embedding
    }

def load_embedding_model():
    """ISSUE 5.1 & Pre-warm: Just trigger the singleton loading."""
    get_embedding_model()
