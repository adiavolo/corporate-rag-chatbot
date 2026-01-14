from typing import List, Dict, Any
from langchain_postgres.vectorstores import PGVector
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from sqlalchemy.orm import Session
from app.config import settings
from app.embeddings import get_embedding_service
from loguru import logger

# Adapter to accept our EmbeddingService into Langchain's Embeddings interface
class SentEmdeddingsAdapter(Embeddings):
    def __init__(self):
        self.service = get_embedding_service()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.service.embed_batch(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.service.embed_text(text)

class VectorStoreService:
    def __init__(self):
        self.connection_string = settings.DATABASE_URL
        self.collection_name = settings.PGVECTOR_COLLECTION_NAME
        self.embeddings = SentEmdeddingsAdapter()
        
        # Initialize PGVector
        # Note: langchain-postgres uses psycopg3 style connection string usually,
        # but standard postgresql:// works with the underlying driver if installed correctly.
        # We need to ensure the tables exist.
        self.vectorstore = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.connection_string,
            use_jsonb=True,
        )

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> List[str]:
        """
        Adds texts + metadata to the vector store.
        """
        try:
            logger.info(f"Adding {len(texts)} chunks to vector store")
            return self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise e

    def similarity_search(self, query: str, k: int = 5, filter: Dict[str, Any] = None) -> List[Document]:
        """
        Performs semantic search.
        """
        try:
            logger.info(f"Searching for: '{query}' with filter: {filter}")
            results = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            return results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise e
    
    def similarity_search_with_score(self, query: str, k: int = 5, filter: Dict[str, Any] = None):
         try:
            logger.info(f"Searching (with score) for: '{query}' with filter: {filter}")
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter
            )
            return results
         except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise e

# Global instance
vector_store = None

def get_vector_store():
    global vector_store
    if vector_store is None:
        vector_store = VectorStoreService()
    return vector_store
