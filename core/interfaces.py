"""
Enterprise AI Assistant - Abstract Base Classes
================================================

Endüstri standartlarında interface tanımları.
Dependency Injection ve loose coupling için.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# LLM INTERFACE
# =============================================================================

@dataclass
class LLMResponse:
    """LLM yanıt objesi."""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMProviderBase(ABC):
    """
    LLM provider abstract base class.
    
    Tüm LLM implementasyonları bu interface'i kullanmalı.
    Ollama, OpenAI, Anthropic vb. için ortak arayüz.
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Senkron metin üretimi."""
        pass
    
    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Asenkron metin üretimi."""
        pass
    
    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ):
        """Streaming metin üretimi."""
        pass
    
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Multi-turn chat."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Provider durumu."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Provider erişilebilir mi?"""
        pass


# =============================================================================
# EMBEDDING INTERFACE
# =============================================================================

class EmbeddingProviderBase(ABC):
    """
    Embedding provider abstract base class.
    
    Tüm embedding modelleri için ortak arayüz.
    """
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding boyutu."""
        pass
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Tek metin için embedding."""
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Çoklu metin için embedding."""
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Sorgu için optimize edilmiş embedding."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Provider erişilebilir mi?"""
        pass


# =============================================================================
# VECTOR STORE INTERFACE
# =============================================================================

@dataclass
class SearchResult:
    """Arama sonucu objesi."""
    id: str
    content: str
    score: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorStoreBase(ABC):
    """
    Vector store abstract base class.
    
    ChromaDB, Pinecone, Weaviate vb. için ortak arayüz.
    """
    
    @abstractmethod
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Dökümanları ekle."""
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Semantic arama."""
        pass
    
    @abstractmethod
    def search_by_embedding(
        self,
        embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Embedding ile arama."""
        pass
    
    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """ID ile döküman getir."""
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str) -> bool:
        """Döküman sil."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Toplam döküman sayısı."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Tüm dökümanları sil."""
        pass


# =============================================================================
# DOCUMENT LOADER INTERFACE
# =============================================================================

@dataclass
class LoadedDocument:
    """Yüklenen döküman objesi."""
    content: str
    metadata: Dict[str, Any]
    source: str
    page_count: int = 1
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DocumentLoaderBase(ABC):
    """
    Document loader abstract base class.
    
    PDF, DOCX, TXT vb. loader'lar için ortak arayüz.
    """
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Desteklenen dosya uzantıları."""
        pass
    
    @abstractmethod
    def load(self, file_path: str) -> List[LoadedDocument]:
        """Dosyayı yükle."""
        pass
    
    @abstractmethod
    def load_from_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> List[LoadedDocument]:
        """Byte içerikten yükle."""
        pass
    
    def can_load(self, file_path: str) -> bool:
        """Bu loader dosyayı yükleyebilir mi?"""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_extensions


# =============================================================================
# CHUNKER INTERFACE
# =============================================================================

@dataclass
class Chunk:
    """Chunk objesi."""
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    start_char: int = 0
    end_char: int = 0
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ChunkerBase(ABC):
    """
    Text chunker abstract base class.
    
    Farklı chunking stratejileri için ortak arayüz.
    """
    
    @abstractmethod
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        """Metni parçala."""
        pass
    
    @abstractmethod
    def chunk_documents(
        self,
        documents: List[LoadedDocument],
    ) -> List[Chunk]:
        """Dökümanları parçala."""
        pass


# =============================================================================
# AGENT INTERFACE
# =============================================================================

class AgentRole(str, Enum):
    """Agent rolleri."""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    WRITER = "writer"
    ANALYZER = "analyzer"
    ASSISTANT = "assistant"
    PLANNER = "planner"
    EXECUTOR = "executor"


@dataclass
class AgentResponse:
    """Agent yanıt objesi."""
    content: str
    agent_name: str
    agent_role: str
    success: bool = True
    sources: List[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}


class AgentBase(ABC):
    """
    Agent abstract base class.
    
    Tüm agent'lar bu interface'i implement etmeli.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent adı."""
        pass
    
    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """Agent rolü."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent açıklaması."""
        pass
    
    @abstractmethod
    def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Görevi yürüt."""
        pass
    
    @abstractmethod
    async def execute_async(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Asenkron görev yürütme."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Agent durumu."""
        pass


# =============================================================================
# TOOL INTERFACE
# =============================================================================

@dataclass
class ToolResult:
    """Tool sonuç objesi."""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolBase(ABC):
    """
    Tool abstract base class.
    
    Tüm agent araçları için ortak arayüz.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool adı."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool açıklaması."""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """OpenAI function calling uyumlu şema."""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Tool'u çalıştır."""
        pass
    
    @abstractmethod
    async def execute_async(self, **kwargs) -> ToolResult:
        """Asenkron çalıştırma."""
        pass


# =============================================================================
# CACHE INTERFACE
# =============================================================================

class CacheBase(ABC):
    """
    Cache abstract base class.
    
    Memory, Redis, Disk cache vb. için ortak arayüz.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Değer al."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Değer kaydet."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Değer sil."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Anahtar var mı?"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Tüm cache'i temizle."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        pass


# =============================================================================
# MEMORY INTERFACE
# =============================================================================

@dataclass
class MemoryItem:
    """Memory objesi."""
    id: str
    content: str
    memory_type: str
    importance: float
    created_at: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MemoryBase(ABC):
    """
    Memory abstract base class.
    
    Short-term, long-term, episodic memory vb. için ortak arayüz.
    """
    
    @abstractmethod
    def store(
        self,
        content: str,
        memory_type: str,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Hafızaya kaydet."""
        pass
    
    @abstractmethod
    def recall(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """Hafızadan çağır."""
        pass
    
    @abstractmethod
    def forget(self, memory_id: str) -> bool:
        """Hafızadan sil."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Hafıza istatistikleri."""
        pass


# =============================================================================
# SESSION INTERFACE
# =============================================================================

class SessionManagerBase(ABC):
    """
    Session manager abstract base class.
    
    Kullanıcı oturumları için ortak arayüz.
    """
    
    @abstractmethod
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Yeni session oluştur."""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Session bilgilerini al."""
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Session güncelle."""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Session sil."""
        pass
    
    @abstractmethod
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> bool:
        """Session'a mesaj ekle."""
        pass
    
    @abstractmethod
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Session mesajlarını al."""
        pass


__all__ = [
    # LLM
    "LLMResponse",
    "LLMProviderBase",
    
    # Embedding
    "EmbeddingProviderBase",
    
    # Vector Store
    "SearchResult",
    "VectorStoreBase",
    
    # Document
    "LoadedDocument",
    "DocumentLoaderBase",
    
    # Chunker
    "Chunk",
    "ChunkerBase",
    
    # Agent
    "AgentRole",
    "AgentResponse",
    "AgentBase",
    
    # Tool
    "ToolResult",
    "ToolBase",
    
    # Cache
    "CacheBase",
    
    # Memory
    "MemoryItem",
    "MemoryBase",
    
    # Session
    "SessionManagerBase",
]
