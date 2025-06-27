from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

# This model is chosen for its multilingual capabilities, including Turkish.
# In a production environment, you might want to manage the model loading
# more carefully (e.g., as a singleton during application startup).
# model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
model = SentenceTransformer('BAAI/bge-m3')


class AIService:
    @staticmethod
    def get_embedding_for_text(text: str) -> List[float]:
        """
        Generates an embedding vector for a given text query.
        """
        # The model.encode returns a numpy array, we convert it to a list of floats.
        embedding: np.ndarray = model.encode(text)
        return embedding.tolist() 