"""
Configuration settings for FastAPI backend
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # MongoDB Atlas
    MONGODB_URI: str = "mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority"
    MONGODB_DATABASE: str = "pdf_insight"
    MONGODB_CHUNKS_COLLECTION: str = "chunks"
    MONGODB_DOCUMENTS_COLLECTION: str = "documents"
    MONGODB_SESSIONS_COLLECTION: str = "sessions"
    MONGODB_CHAT_HISTORY_COLLECTION: str = "chat_history"
    
    # Gemini API
    GEMINI_API_KEY: str = "test-key"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    GEMINI_CHAT_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_OCR_MODEL: str = "gemini-3.1-flash-lite"
    
    # LangChain Configuration
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 300
    TOP_K_RETRIEVAL: int = 10
    SIMILARITY_THRESHOLD: float = 0.3
    
    # Vector Search Configuration
    EMBEDDING_DIMENSION: int = 3072  # gemini-embedding-001 produces 3072-dim vectors
    VECTOR_SEARCH_SIMILARITY: str = "cosine"
    
    # Session Configuration
    SESSION_EXPIRY_HOURS: int = 24
    DOCUMENT_CLEANUP_ENABLED: bool = True
    
    # PDF Processing
    MAX_PDF_SIZE_MB: int = 100
    SUPPORTED_FORMATS: str = "pdf,docx,txt"
    OCR_ENABLED: bool = True
    OCR_MIN_TEXT_CHARS: int = 25
    OCR_RENDER_DPI: int = 200
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()


settings = get_settings()
