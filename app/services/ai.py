from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the multilingual model on the first embedding request."""
    return SentenceTransformer("BAAI/bge-m3")


class AIService:
    @staticmethod
    def get_embedding_for_text(text: str) -> List[float]:
        """
        Generates an embedding vector for a given text query.
        """
        # The model.encode returns a numpy array, we convert it to a list of floats.
        embedding: np.ndarray = get_embedding_model().encode(text)
        return embedding.tolist()
