"""
Enterprise AI Assistant - Configuration Module
Endüstri Standartlarında Kurumsal AI Çözümü

Merkezi konfigürasyon yönetimi - tüm sistem ayarları burada tanımlanır.
Multi-environment desteği ve feature flags entegrasyonu.
"""

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


# =============================================================================
# ENVIRONMENT MANAGEMENT
# =============================================================================

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


def is_production() -> bool:
    """Production ortamında mıyız?"""
    return get_environment() == Environment.PRODUCTION


def is_development() -> bool:
    """Development ortamında mıyız?"""
    return get_environment() == Environment.DEVELOPMENT


def is_testing() -> bool:
    """Test ortamında mıyız?"""
    return get_environment() == Environment.TESTING


# =============================================================================
# FEATURE FLAGS
# =============================================================================

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
        "crag_enabled": True,
        "model_routing": True,
        # === PREMIUM FULL QUALITY FLAGS ===
        "crag_full": True,          # Full CRAG: Query Transform + Relevance Grading + Hallucination Detection
        "moe_router": True,         # Mixture of Experts Query Routing
        "multi_agent_debate": True, # Multi-Agent Debate for complex questions
        "memgpt_memory": True,      # MemGPT-style Tiered Memory
        "ragas_evaluation": True,   # RAGAS Quality Evaluation
        "semantic_expansion": True, # Semantic Query Expansion
        "smart_titles": True,       # Smart Title Generation
        "source_scoring": True,     # Source Quality Scoring
        "response_length": True,    # Response Length Management
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


def feature_enabled(flag_name: str) -> bool:
    """Feature flag aktif mi? Shortcut function."""
    return FeatureFlags.is_enabled(flag_name)


# =============================================================================
# SETTINGS CLASS
# =============================================================================


class Settings(BaseSettings):
    """Ana konfigürasyon sınıfı - Endüstri standartlarına uygun."""
    
    # Project paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    # Data isolation: User data stored outside project workspace for privacy
    # External AI coding assistants cannot access this path
    DATA_DIR: Path = Field(default_factory=lambda: Path(os.environ.get("AGENTIC_DATA_DIR", "C:/Users/LENOVO/AgenticData")))
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
    
    # ChromaDB settings - relative to DATA_DIR
    CHROMA_PERSIST_DIR: str = Field(default_factory=lambda: str(Path(os.environ.get("AGENTIC_DATA_DIR", "C:/Users/LENOVO/AgenticData")) / "chroma_db"))
    CHROMA_COLLECTION_NAME: str = "enterprise_knowledge"
    
    # SQLite settings - relative to DATA_DIR
    SQLITE_DB_PATH: str = Field(default_factory=lambda: str(Path(os.environ.get("AGENTIC_DATA_DIR", "C:/Users/LENOVO/AgenticData")) / "enterprise.db"))
    
    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 30
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
    
    # ==================== MODEL ROUTING CONFIGURATION ====================
    # Small model - fast responses, simple queries
    ROUTING_SMALL_MODEL: str = "qwen3:4b"
    ROUTING_SMALL_MODEL_DISPLAY: str = "Qwen 4B"
    ROUTING_SMALL_MODEL_ICON: str = "🟢"
    ROUTING_SMALL_MODEL_TOKENS_PER_SEC: int = 80
    
    # Large model - comprehensive responses, complex queries
    ROUTING_LARGE_MODEL: str = "qwen3-vl:8b"
    ROUTING_LARGE_MODEL_DISPLAY: str = "Qwen 8B"
    ROUTING_LARGE_MODEL_ICON: str = "🔵"
    ROUTING_LARGE_MODEL_TOKENS_PER_SEC: int = 40
    
    # Routing thresholds
    ROUTING_CONFIDENCE_HIGH: float = 0.85
    ROUTING_CONFIDENCE_MEDIUM: float = 0.60
    ROUTING_CONFIDENCE_LOW: float = 0.40
    ROUTING_SIMILARITY_THRESHOLD: float = 0.85
    ROUTING_MIN_FEEDBACKS_TO_LEARN: int = 2
    
    # ==================== RAG & CRAG CONFIGURATION ====================
    # RAG thresholds
    RAG_RELEVANCE_THRESHOLD: float = 0.35
    RAG_HIGH_RELEVANCE_THRESHOLD: float = 0.25
    RAG_SIMILARITY_THRESHOLD: float = 0.85
    
    # CRAG settings
    CRAG_MAX_ITERATIONS: int = 3
    CRAG_MIN_RELEVANT_DOCS: int = 1
    CRAG_HALLUCINATION_CHECK: bool = True
    
    # ==================== WEBSOCKET CONFIGURATION ====================
    # WebSocket URLs and settings
    WS_PING_INTERVAL: int = 25  # seconds
    WS_PING_TIMEOUT: int = 10  # seconds
    WS_RECONNECT_ATTEMPTS: int = 5
    WS_RECONNECT_DELAY: int = 1000  # milliseconds
    WS_MAX_MESSAGE_SIZE: int = 1048576  # 1MB
    
    # Timeouts
    WS_STREAM_TIMEOUT: int = 180  # seconds
    WS_RAG_SEARCH_TIMEOUT: int = 30  # seconds
    WS_WEB_SEARCH_TIMEOUT: int = 45  # seconds
    WS_MODEL_ROUTING_TIMEOUT: int = 10  # seconds
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Pydantic V2 model config
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # ==================== URL PROPERTIES ====================
    # Frontend URL
    FRONTEND_PORT: int = 3000
    
    @property
    def FRONTEND_URL(self) -> str:
        """Frontend URL."""
        return f"http://localhost:{self.FRONTEND_PORT}"
    
    @property
    def OLLAMA_API_TAGS_URL(self) -> str:
        """Ollama API tags endpoint."""
        return f"{self.OLLAMA_BASE_URL}/api/tags"
    
    @property
    def OLLAMA_API_GENERATE_URL(self) -> str:
        """Ollama API generate endpoint."""
        return f"{self.OLLAMA_BASE_URL}/api/generate"
    
    @property
    def WS_BASE_URL(self) -> str:
        """WebSocket base URL for backend."""
        return f"ws://localhost:{self.API_PORT}"
    
    @property
    def API_BASE_URL(self) -> str:
        """HTTP API base URL."""
        return f"http://localhost:{self.API_PORT}"
    
    def get_ws_url(self, path: str) -> str:
        """Get full WebSocket URL for a path."""
        path = path.lstrip("/")
        return f"{self.WS_BASE_URL}/{path}"
    
    def get_model_routing_config(self) -> dict:
        """Get model routing configuration as a dictionary."""
        from enum import Enum
        
        class ModelSize(str, Enum):
            SMALL = "small"
            LARGE = "large"
        
        return {
            ModelSize.SMALL: {
                "name": self.ROUTING_SMALL_MODEL,
                "display_name": self.ROUTING_SMALL_MODEL_DISPLAY,
                "icon": self.ROUTING_SMALL_MODEL_ICON,
                "description": "Hızlı yanıtlar, basit sorgular",
                "avg_tokens_per_second": self.ROUTING_SMALL_MODEL_TOKENS_PER_SEC,
            },
            ModelSize.LARGE: {
                "name": self.ROUTING_LARGE_MODEL,
                "display_name": self.ROUTING_LARGE_MODEL_DISPLAY,
                "icon": self.ROUTING_LARGE_MODEL_ICON,
                "description": "Kapsamlı yanıtlar, karmaşık sorgular",
                "avg_tokens_per_second": self.ROUTING_LARGE_MODEL_TOKENS_PER_SEC,
            },
        }
    
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


# =============================================================================
# ENVIRONMENT-AWARE SETTINGS FACTORY
# =============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Environment'a göre ayarlanmış settings döndür.
    Production'da daha sıkı ayarlar kullanılır.
    """
    base_settings = Settings()
    env = get_environment()
    
    # Production overrides
    if env == Environment.PRODUCTION:
        base_settings.API_DEBUG = False
        base_settings.LOG_LEVEL = "WARNING"
    elif env == Environment.TESTING:
        base_settings.LOG_LEVEL = "DEBUG"
    
    base_settings.ensure_directories()
    return base_settings


# Singleton settings instance (backward compatible)
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Settings
    "Settings",
    "settings",
    "get_settings",
    # Environment
    "Environment",
    "get_environment",
    "is_production",
    "is_development",
    "is_testing",
    # Feature Flags
    "FeatureFlags",
    "feature_enabled",
]
