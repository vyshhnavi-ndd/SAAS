from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "RAG SaaS API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ragdb"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: Optional[str] = None

    # Storage
    STORAGE_PATH: str = "/tmp/rag-storage"  # Local storage for MVP

    # Sentence-Transformers
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2:7b"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    # Admin
    ADMIN_EMAIL: str = "admin@ragSaas.com"
    ADMIN_PASSWORD: str = "changeme123"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
