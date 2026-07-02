"""
Production configuration for RAG Healthcare API
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application
    APP_NAME: str = "Healthcare RAG API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # API Keys (loaded from environment)
    OPENAI_API_KEY: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"

    # Model Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    OPENAI_MODEL: str = "gpt-4o-mini"
    MAX_QUERY_LENGTH: int = 500
    MAX_RESULTS: int = 10
    DEFAULT_RESULTS: int = 2
    GENERATE_ANSWER: bool = True  # Enable LLM answer generation

    # Corpus / Ingestion Configuration
    DATA_DIR: str = "seed_corpus"  # Directory scanned for source documents (.txt, .md, .pdf)
    CHUNK_SIZE: int = 512  # Target chunk size in characters
    CHUNK_OVERLAP: int = 64  # Character overlap between consecutive chunks
    REINDEX_ON_CORPUS_CHANGE: bool = True  # Rebuild the index when the corpus fingerprint changes

    # Vector Store Configuration
    USE_CHROMADB: bool = True  # Set to False to use FAISS fallback

    # ChromaDB Configuration
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_NAME: str = "healthcare_documents"
    CHROMA_DISTANCE_METRIC: str = "cosine"  # Options: cosine, l2, ip

    # Rate Limiting (requests per minute)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Timeouts (seconds)
    REQUEST_TIMEOUT: int = 30
    STARTUP_TIMEOUT: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()