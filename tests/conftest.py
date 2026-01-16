import pytest
from unittest.mock import MagicMock
from app.core.config import AppConfig, SettingsConfigDict
from app.clients.llm_client import LLMClient
from app.clients.embedding_client import EmbeddingClient
from app.clients.vector_client import VectorStore
from app.data.repositories import DocumentRepository, ChunkRepository
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService
from app.services.health_service import HealthService
from app.services.rag_service import RAGService

@pytest.fixture
def mock_config():
    # Use defaults or dummy values
    return AppConfig(
        API_KEY="test-key",
        OPENROUTER_API_KEY="test-key",
        DATABASE_URL="postgresql://user:pass@localhost:5432/db"
    )

@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=LLMClient)
    client.generate.return_value = "This is a mock answer."
    client.check_health.return_value = True
    return client

@pytest.fixture
def mock_embedding_client():
    client = MagicMock(spec=EmbeddingClient)
    client.embed_text.return_value = [0.1] * 384
    client.embed_batch.return_value = [[0.1] * 384]
    client.check_health.return_value = True
    return client

@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=VectorStore)
    store.similarity_search.return_value = []
    store.check_health.return_value = True
    # Default to returning empty list for search
    return store

@pytest.fixture
def mock_document_repo():
    repo = MagicMock() # Relaxed mock
    repo.get_by_hash.return_value = None # No duplicate by default
    repo.create.return_value = MagicMock(id=1, filename="test.pdf")
    # Mock session for health check
    repo.session.execute.return_value = MagicMock()
    return repo

@pytest.fixture
def mock_chunk_repo():
    repo = MagicMock() # Relaxed mock
    repo.create_batch.return_value = [MagicMock(id=1)]
    repo.search_by_text.return_value = []
    repo.session = MagicMock()
    return repo

@pytest.fixture
def ingestion_service(mock_embedding_client, mock_vector_store, mock_document_repo, mock_chunk_repo, mock_config):
    return IngestionService(
        embedding_client=mock_embedding_client,
        vector_store=mock_vector_store,
        document_repo=mock_document_repo,
        chunk_repo=mock_chunk_repo,
        config=mock_config.ingestion
    )

@pytest.fixture
def retrieval_service(mock_vector_store, mock_embedding_client, mock_chunk_repo, mock_document_repo, mock_config):
    return RetrievalService(
        vector_store=mock_vector_store,
        embedding_client=mock_embedding_client,
        chunk_repo=mock_chunk_repo,
        document_repo=mock_document_repo,
        config=mock_config.retrieval
    )

@pytest.fixture
def health_service(mock_vector_store, mock_llm_client, mock_document_repo, mock_config):
    return HealthService(
        vector_store=mock_vector_store,
        llm_client=mock_llm_client,
        document_repo=mock_document_repo,
        config=mock_config
    )

@pytest.fixture
def rag_service(retrieval_service, ingestion_service, health_service, mock_llm_client, mock_config):
    return RAGService(
        retrieval_service=retrieval_service,
        ingestion_service=ingestion_service,
        health_service=health_service,
        llm_client=mock_llm_client,
        config=mock_config
    )
