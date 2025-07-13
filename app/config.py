from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # API Configuration
    api_key: str = os.getenv("API_KEY")
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # MongoDB Configuration
    mongodb_uri: str = "mongodb://localhost:27017/resume_screener"
    mongodb_database: str = "resume_screener"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    openai_model: str = "text-embedding-ada-002"
    openai_parsing_model: str = "gpt-4o-2024-08-06"
    openai_chunk_size: int = 1000
    openai_chunk_overlap: int = 200
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME")
    pinecone_dimension: int = 1536
    
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = ["pdf"]
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    
    # Security Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    rate_limit_per_minute: int = 60
    
    model_config = {
        "env_file": None,
        "case_sensitive": False,
        "extra": "ignore"
    }


# Create global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True) 