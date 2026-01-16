from abc import ABC, abstractmethod
from typing import List
from sentence_transformers import SentenceTransformer
from loguru import logger
from app.core.config import EmbeddingConfig
from app.core.exceptions import RetrievalError

class EmbeddingClient(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass
        
    @abstractmethod
    def check_health(self) -> bool:
        pass

class HuggingFaceEmbeddings(EmbeddingClient):
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading embedding model: {self.config.model}")
            try:
                self._model = SentenceTransformer(self.config.model)
                dimension = self._model.get_sentence_embedding_dimension()
                if dimension != self.config.dimension:
                    logger.error(f"Model dimension {dimension} != config {self.config.dimension}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise RetrievalError(f"Embedding model load failed: {str(e)}")
        return self._model

    def embed_text(self, text: str) -> List[float]:
        try:
            return self.model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise RetrievalError(f"Embedding failed: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.model.encode(texts).tolist()
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise RetrievalError(f"Batch embedding failed: {e}")

    def check_health(self) -> bool:
        try:
            # Trigger load
            m = self.model
            m.encode("test")
            return True
        except Exception:
            return False
