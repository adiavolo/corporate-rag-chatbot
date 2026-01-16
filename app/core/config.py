import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
from typing import List

class DatabaseConfig(BaseSettings):
    url: str = Field(..., alias="DATABASE_URL", description="PostgreSQL connection string")
    pgvector_collection_name: str = Field("corporate_documents", alias="PGVECTOR_COLLECTION_NAME")
    pgvector_distance_strategy: str = Field("cosine", alias="PGVECTOR_DISTANCE_STRATEGY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True
    )

class LLMConfig(BaseSettings):
    api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")
    model: str = Field("meta-llama/llama-3.2-3b-instruct", alias="LLM_MODEL")
    temperature: float = Field(0.3, alias="LLM_TEMPERATURE")
    max_tokens: int = Field(300, alias="LLM_MAX_TOKENS")
    timeout: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True
    )

class EmbeddingConfig(BaseSettings):
    model: str = Field("sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    dimension: int = Field(384, alias="EMBEDDING_DIMENSION")
    batch_size: int = 32

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True
    )

class RetrievalConfig(BaseSettings):
    similarity_threshold: float = Field(0.6, alias="SIMILARITY_THRESHOLD")
    top_k: int = Field(5, alias="DEFAULT_TOP_K")
    max_context_tokens: int = Field(6000, alias="MAX_CONTEXT_TOKENS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True
    )

class IngestionConfig(BaseSettings):
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = Field(10, alias="MAX_FILE_SIZE_MB")
    allowed_tags: str = Field("HR,Legal,Finance", alias="ALLOWED_TAGS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True
    )

    @computed_field
    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @computed_field
    @property
    def allowed_tags_list(self) -> List[str]:
        return [tag.strip() for tag in self.allowed_tags.split(",") if tag.strip()]

class AppConfig(BaseSettings):
    api_key: str = Field(..., alias="API_KEY")
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True
    )

settings = AppConfig()
