"""
Enterprise AI Assistant - Environment Configuration
====================================================

Multi-environment konfigürasyon yönetimi.
Development, Staging, Production ayrımı.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings
from pydantic import Field


class Environment(str, Enum):
    """Çalışma ortamları."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


def get_environment() -> Environment:
    """Mevcut environment'ı al."""
    env_str = os.getenv("ENVIRONMENT", "development").lower()
    
    try:
        return Environment(env_str)
    except ValueError:
        return Environment.DEVELOPMENT


class BaseConfig(BaseSettings):
    """
    Temel konfigürasyon - tüm environment'lar için ortak ayarlar.
    """
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # Project paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    
    @property
    def DATA_DIR(self) -> Path:
        return self.BASE_DIR / "data"
    
    @property
    def LOGS_DIR(self) -> Path:
        return self.BASE_DIR / "logs"
    
    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_PRIMARY_MODEL: str = "qwen2.5:7b"
    OLLAMA_BACKUP_MODEL: str = "qwen2.5:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 120
    
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    API_KEY: Optional[str] = None
    ALLOWED_ORIGINS: str = "http://localhost:8501,http://localhost:3000"
    
    # Frontend settings
    STREAMLIT_PORT: int = 8501
    
    # ChromaDB settings
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "enterprise_knowledge"
    
    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    EMBEDDING_DIMENSION: int = 768
    
    # Agent settings
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json veya text
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_SIZE: int = 1000
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Circuit breaker
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 30
    
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
            self.DATA_DIR / "exports",
            self.DATA_DIR / "notes",
            self.LOGS_DIR,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """CORS için izin verilen origin listesi."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def CHROMA_DB_PATH(self) -> Path:
        """ChromaDB path as Path object."""
        return Path(self.CHROMA_PERSIST_DIR)


class DevelopmentConfig(BaseConfig):
    """Development ortamı konfigürasyonu."""
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "text"  # Geliştirmede okunabilir format
    
    # Daha düşük rate limit
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    
    # Cache kısa TTL
    CACHE_TTL_SECONDS: int = 300
    
    # Circuit breaker daha toleranslı
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 10
    CIRCUIT_BREAKER_TIMEOUT: int = 15
    
    # Smaller models for faster iteration
    OLLAMA_PRIMARY_MODEL: str = "qwen2.5:7b"


class StagingConfig(BaseConfig):
    """Staging ortamı konfigürasyonu."""
    
    ENVIRONMENT: str = "staging"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Orta seviye rate limit
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    
    # Orta TTL
    CACHE_TTL_SECONDS: int = 1800
    
    # Circuit breaker production-like
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 30


class ProductionConfig(BaseConfig):
    """Production ortamı konfigürasyonu."""
    
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    API_DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    LOG_FORMAT: str = "json"
    
    # Sıkı rate limit
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    
    # Uzun cache TTL
    CACHE_TTL_SECONDS: int = 7200
    CACHE_MAX_SIZE: int = 5000
    
    # Circuit breaker sıkı
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    
    # Larger models for better quality
    OLLAMA_PRIMARY_MODEL: str = "qwen2.5:14b"
    
    # Daha büyük chunk için daha iyi context
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 300


class TestingConfig(BaseConfig):
    """Test ortamı konfigürasyonu."""
    
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "text"
    
    # Test için hızlı ayarlar
    CACHE_ENABLED: bool = False
    RATE_LIMIT_ENABLED: bool = False
    CIRCUIT_BREAKER_ENABLED: bool = False
    
    # Küçük model
    OLLAMA_PRIMARY_MODEL: str = "qwen2.5:3b"
    
    # Küçük chunk
    CHUNK_SIZE: int = 200
    CHUNK_OVERLAP: int = 50
    
    # In-memory test DB
    CHROMA_PERSIST_DIR: str = ":memory:"


# Config mapping
CONFIG_MAP: Dict[Environment, type] = {
    Environment.DEVELOPMENT: DevelopmentConfig,
    Environment.STAGING: StagingConfig,
    Environment.PRODUCTION: ProductionConfig,
    Environment.TESTING: TestingConfig,
}


@lru_cache()
def get_settings() -> BaseConfig:
    """
    Environment'a göre doğru konfigürasyonu döndür.
    
    Singleton pattern ile cached.
    """
    env = get_environment()
    config_class = CONFIG_MAP.get(env, DevelopmentConfig)
    config = config_class()
    config.ensure_directories()
    return config


# Feature flags
class FeatureFlags:
    """
    Feature flag yönetimi.
    
    Özellikleri runtime'da açıp kapatmak için.
    """
    
    _flags: Dict[str, bool] = {}
    
    # Default flags
    DEFAULTS = {
        "web_search": True,
        "voice_input": False,
        "voice_output": False,
        "graph_rag": True,
        "hyde_retrieval": True,
        "multi_query_retrieval": True,
        "guardrails": True,
        "analytics": True,
        "advanced_caching": True,
        "streaming_response": True,
        "document_ocr": False,
        "multi_language": True,
        "export_feature": True,
        "notes_feature": True,
        "mcp_integration": True,
    }
    
    @classmethod
    def is_enabled(cls, flag_name: str) -> bool:
        """Flag aktif mi?"""
        # Önce environment variable kontrol
        env_key = f"FEATURE_{flag_name.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")
        
        # Sonra runtime flags
        if flag_name in cls._flags:
            return cls._flags[flag_name]
        
        # Son olarak default
        return cls.DEFAULTS.get(flag_name, False)
    
    @classmethod
    def enable(cls, flag_name: str):
        """Flag'i aktifleştir."""
        cls._flags[flag_name] = True
    
    @classmethod
    def disable(cls, flag_name: str):
        """Flag'i deaktifleştir."""
        cls._flags[flag_name] = False
    
    @classmethod
    def set(cls, flag_name: str, enabled: bool):
        """Flag değerini ayarla."""
        cls._flags[flag_name] = enabled
    
    @classmethod
    def get_all(cls) -> Dict[str, bool]:
        """Tüm flag'leri döndür."""
        result = cls.DEFAULTS.copy()
        result.update(cls._flags)
        
        # Environment variables'ı da ekle
        for flag_name in cls.DEFAULTS.keys():
            env_key = f"FEATURE_{flag_name.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                result[flag_name] = env_value.lower() in ("true", "1", "yes", "on")
        
        return result
    
    @classmethod
    def reset(cls):
        """Runtime flags'leri sıfırla."""
        cls._flags.clear()


# Shortcuts
def is_production() -> bool:
    """Production ortamında mıyız?"""
    return get_environment() == Environment.PRODUCTION


def is_development() -> bool:
    """Development ortamında mıyız?"""
    return get_environment() == Environment.DEVELOPMENT


def is_testing() -> bool:
    """Test ortamında mıyız?"""
    return get_environment() == Environment.TESTING


def feature_enabled(flag_name: str) -> bool:
    """Feature flag aktif mi?"""
    return FeatureFlags.is_enabled(flag_name)


# Backward compatibility - mevcut settings kullanımı için
settings = get_settings()


__all__ = [
    "Environment",
    "get_environment",
    "BaseConfig",
    "DevelopmentConfig",
    "StagingConfig",
    "ProductionConfig",
    "TestingConfig",
    "get_settings",
    "settings",
    "FeatureFlags",
    "feature_enabled",
    "is_production",
    "is_development",
    "is_testing",
]
