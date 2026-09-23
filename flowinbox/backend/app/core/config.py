import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FlowInbox AI"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://flowinbox_user:flowinbox_password@localhost:5432/flowinbox_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Vector Store
    QDRANT_URL: str = "http://localhost:6333"
    VECTOR_STORE: str = "qdrant"  # "qdrant" or "chroma"
    
    # LLM Providers
    LLM_PROVIDER: str = "groq"
    LLM_FALLBACK_PROVIDER: str = "gemini"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Embeddings
    EMBEDDING_PROVIDER: str = "fastembed"
    
    # Background Sync Configuration
    ENABLE_GMAIL_SYNC: bool = True

    # Observability (Optional)
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "flowinbox-ai"
    
    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Security
    FRONTEND_URL: str = "http://localhost:8080"
    FRONTEND_ORIGINS: list[str] = ["http://localhost:8080", "http://localhost:5173", "http://localhost:3000"]

    JWT_SECRET: str = "super_secret_jwt_key_for_dev_mode_only"

    OAUTH_TOKEN_ENCRYPTION_KEY: str = "secret_key_32_bytes_long_for_fernet!!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
