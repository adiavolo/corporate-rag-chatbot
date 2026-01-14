from sentence_transformers import SentenceTransformer
from app.config import settings
from loguru import logger
from typing import List

class EmbeddingService:
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            # Verify dimension
            dimension = self.model.get_sentence_embedding_dimension()
            if dimension != settings.EMBEDDING_DIMENSION:
                logger.error(f"Model dimension {dimension} does not match settings {settings.EMBEDDING_DIMENSION}")
                raise ValueError("Embedding dimension mismatch")
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise e

    def embed_text(self, text: str) -> List[float]:
        """
        Embeds a single string into a vector.
        """
        return self.model.encode(text).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of strings.
        """
        return self.model.encode(texts).tolist()

# Singleton instance
# We load this lazily or at startup in main.py to avoid import time overhead/errors if model missing
embedding_service = None

def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        embedding_service = EmbeddingService()
    return embedding_service
