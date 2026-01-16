from functools import lru_cache
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.config import AppConfig, settings
from app.data.database import get_db, Document, Chunk
from app.data.repositories import DocumentRepository, ChunkRepository
from app.clients.llm_client import LLMClient, OpenRouterClient
from app.clients.embedding_client import EmbeddingClient, HuggingFaceEmbeddings
from app.clients.vector_client import VectorStore, PGVectorStore
from app.services.ingestion_service import IngestionService
from app.services.retrieval_service import RetrievalService
from app.services.health_service import HealthService
from app.services.rag_service import RAGService

# --- Config ---
def get_config() -> AppConfig:
    return settings

# --- Database ---
def get_database_session() -> Generator[Session, None, None]:
    # Use the generator from database.py that handles closing
    yield from get_db()

# --- Repositories ---
def get_document_repository(session: Session = Depends(get_database_session)) -> DocumentRepository:
    return DocumentRepository(session)

def get_chunk_repository(session: Session = Depends(get_database_session)) -> ChunkRepository:
    return ChunkRepository(session)

# --- Clients (Singletons) ---
@lru_cache()
def get_embedding_client(config: AppConfig = Depends(get_config)) -> EmbeddingClient:
    return HuggingFaceEmbeddings(config.embedding)

@lru_cache()
def get_vector_store(config: AppConfig = Depends(get_config)) -> VectorStore:
    # VectorStore needs DatabaseConfig and embedding dimension
    return PGVectorStore(config.database, embedding_dimension=config.embedding.dimension)

@lru_cache()
def get_llm_client(config: AppConfig = Depends(get_config)) -> LLMClient:
    return OpenRouterClient(config.llm)

# --- Services (Per Request) ---
def get_ingestion_service(
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    vector_store: VectorStore = Depends(get_vector_store),
    document_repo: DocumentRepository = Depends(get_document_repository),
    chunk_repo: ChunkRepository = Depends(get_chunk_repository),
    config: AppConfig = Depends(get_config)
) -> IngestionService:
    return IngestionService(
        embedding_client=embedding_client,
        vector_store=vector_store,
        document_repo=document_repo,
        chunk_repo=chunk_repo,
        config=config.ingestion
    )

def get_retrieval_service(
    vector_store: VectorStore = Depends(get_vector_store),
    embedding_client: EmbeddingClient = Depends(get_embedding_client),
    chunk_repo: ChunkRepository = Depends(get_chunk_repository),
    document_repo: DocumentRepository = Depends(get_document_repository),
    config: AppConfig = Depends(get_config)
) -> RetrievalService:
    return RetrievalService(
        vector_store=vector_store,
        embedding_client=embedding_client,
        chunk_repo=chunk_repo,
        document_repo=document_repo,
        config=config.retrieval
    )

def get_health_service(
    vector_store: VectorStore = Depends(get_vector_store),
    llm_client: LLMClient = Depends(get_llm_client),
    document_repo: DocumentRepository = Depends(get_document_repository),
    config: AppConfig = Depends(get_config)
) -> HealthService:
    return HealthService(
        vector_store=vector_store,
        llm_client=llm_client,
        document_repo=document_repo,
        config=config
    )

def get_rag_service(
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    health_service: HealthService = Depends(get_health_service),
    llm_client: LLMClient = Depends(get_llm_client),
    config: AppConfig = Depends(get_config)
) -> RAGService:
    return RAGService(
        retrieval_service=retrieval_service,
        ingestion_service=ingestion_service,
        health_service=health_service,
        llm_client=llm_client,
        config=config
    )
