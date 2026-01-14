import os
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    
    # Authentication
    API_KEY: str = Field(..., description="Bearer token for API access")
    
    # Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    LLM_MODEL: str = "meta-llama/llama-3.2-3b-instruct"
    
    # OpenRouter
    OPENROUTER_API_KEY: str = Field(..., description="OpenRouter API Key")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Limits & Thresholds
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_TAGS: str = "HR,Legal,Finance"  # Comma-separated string in .env
    SIMILARITY_THRESHOLD: float = 0.6
    DEFAULT_TOP_K: int = 5
    MAX_CONTEXT_TOKENS: int = 6000
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 300
    
    # Langchain
    PGVECTOR_COLLECTION_NAME: str = "corporate_documents"
    PGVECTOR_DISTANCE_STRATEGY: str = "cosine"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    @computed_field
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @computed_field
    @property
    def ALLOWED_TAGS_LIST(self) -> List[str]:
        return [tag.strip() for tag in self.ALLOWED_TAGS.split(",") if tag.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
