"""
Enterprise AI Assistant - Configuration Module
Endüstri Standartlarında Kurumsal AI Çözümü

Merkezi konfigürasyon yönetimi - tüm sistem ayarları burada tanımlanır.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Ana konfigürasyon sınıfı - Endüstri standartlarına uygun."""
    
    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "data")
    LOGS_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent / "logs")
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_PRIMARY_MODEL: str = "qwen3-vl:8b"
    OLLAMA_BACKUP_MODEL: str = "qwen3-vl:8b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 120
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001  # Unified port - matches run.py and frontend config
    API_DEBUG: bool = True
    API_KEY: Optional[str] = None
    ALLOWED_ORIGINS: str = "http://localhost:8501,http://localhost:3000,http://localhost:8001"
    
    # Frontend settings
    STREAMLIT_PORT: int = 8501
    
    # ChromaDB settings
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "enterprise_knowledge"
    
    # SQLite settings
    SQLITE_DB_PATH: str = "./data/enterprise.db"
    
    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    EMBEDDING_DIMENSION: int = 384  # GPU model (multilingual) uses 384
    
    # GPU Settings - RTX 4070 (8GB) Optimized
    USE_GPU_EMBEDDING: bool = True
    GPU_EMBEDDING_MODEL: str = "multilingual"  # Best quality for Turkish/English
    GPU_BATCH_SIZE: int = 64  # Optimal for 8GB GPU
    GPU_RERANKER_MODEL: str = "multilingual"  # CrossEncoder with Turkish support
    GPU_RERANKER_BATCH_SIZE: int = 32  # CrossEncoder batch size
    CUDA_VISIBLE_DEVICES: str = "0"
    
    # Ollama GPU Settings
    OLLAMA_NUM_GPU: int = 99  # All layers on GPU (max quality)
    OLLAMA_NUM_CTX: int = 4096  # Context window
    OLLAMA_NUM_BATCH: int = 512  # Batch size for prompt processing
    
    # Agent settings
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def ensure_directories(self) -> None:
        """Gerekli klasörleri oluştur."""
        directories = [
            self.DATA_DIR,
            self.DATA_DIR / "chroma_db",
            self.DATA_DIR / "uploads",
            self.DATA_DIR / "sessions",
            self.DATA_DIR / "cache",
            self.LOGS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """CORS için izin verilen origin listesi."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


# Singleton settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
