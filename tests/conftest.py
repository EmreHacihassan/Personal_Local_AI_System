"""
Enterprise AI Assistant - Test Configuration
=============================================

pytest fixtures ve mock factories.
LLM/Ollama bağımlılığı olmadan test çalıştırma.
"""

import pytest
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# CHROMADB MOCK - Module level to prevent import errors
# =============================================================================

def _setup_chromadb_mock():
    """Setup ChromaDB mock before any imports."""
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient = MagicMock(return_value=MagicMock())
    mock_chromadb.Client = MagicMock(return_value=MagicMock())
    
    # Mock the collection
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
        "ids": [[]]
    }
    mock_collection.add.return_value = None
    mock_collection.delete.return_value = None
    mock_collection.get.return_value = {"documents": [], "metadatas": [], "ids": []}
    
    mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_collection
    mock_chromadb.PersistentClient.return_value.list_collections.return_value = []
    mock_chromadb.Client.return_value.get_or_create_collection.return_value = mock_collection
    
    # Pre-mock chromadb before imports try to use it
    if 'chromadb' not in sys.modules:
        sys.modules['chromadb'] = mock_chromadb
        sys.modules['chromadb.config'] = MagicMock()
        sys.modules['chromadb.api'] = MagicMock()
        sys.modules['chromadb.api.client'] = MagicMock()
    
    return mock_chromadb


# Initialize mock immediately
_mock_chromadb = _setup_chromadb_mock()


# =============================================================================
# MOCK FACTORIES
# =============================================================================

class MockLLMResponse:
    """Mock LLM yanıtı."""
    
    def __init__(self, content: str = "Mock LLM yanıtı"):
        self.content = content
    
    def __getitem__(self, key):
        if key == "message":
            return {"content": self.content}
        return None


class MockLLMManager:
    """
    LLM Manager mock - gerçek Ollama bağlantısı gerektirmez.
    """
    
    def __init__(self, default_response: str = "Bu bir mock yanıttır."):
        self.default_response = default_response
        self.primary_model = "mock-model"
        self.backup_model = "mock-backup"
        self.base_url = "http://localhost:11434"
        self._current_model = self.primary_model
        self._call_count = 0
        self._last_prompt = None
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        self._call_count += 1
        self._last_prompt = prompt
        return self.default_response
    
    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        return self.generate(prompt, system_prompt, temperature, max_tokens)
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        for word in self.default_response.split():
            yield word + " "
    
    def chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        self._call_count += 1
        return self.default_response
    
    def check_model_available(self, model_name: str = None) -> bool:
        return True
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "primary_model": self.primary_model,
            "backup_model": self.backup_model,
            "current_model": self._current_model,
            "base_url": self.base_url,
            "primary_available": True,
            "backup_available": True,
        }
    
    @property
    def call_count(self) -> int:
        return self._call_count
    
    @property
    def last_prompt(self) -> Optional[str]:
        return self._last_prompt


class MockEmbeddingManager:
    """Embedding Manager mock."""
    
    def __init__(self, dimension: int = 768):
        self._dimension = dimension
        self._call_count = 0
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def embed_text(self, text: str) -> List[float]:
        self._call_count += 1
        # Deterministic mock embedding based on text hash
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(hash_val % (i + 1)) / 1000.0 for i in range(self._dimension)]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
    
    def embed_query(self, query: str) -> List[float]:
        return self.embed_text(query)
    
    def embed_document(self, document: str) -> List[float]:
        return self.embed_text(document)
    
    def check_model_available(self) -> bool:
        return True
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "model_name": "mock-embed-model",
            "dimension": self._dimension,
            "available": True,
        }


class MockVectorStore:
    """Vector Store mock - in-memory storage."""
    
    def __init__(self):
        self._documents: Dict[str, Dict] = {}
        self._embeddings: Dict[str, List[float]] = {}
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        import uuid
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        for i, doc_id in enumerate(ids):
            self._documents[doc_id] = {
                "document": documents[i],
                "metadata": metadatas[i],
            }
        
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        # Simple mock: return all documents
        docs = list(self._documents.values())[:n_results]
        return {
            "documents": [d["document"] for d in docs],
            "metadatas": [d["metadata"] for d in docs],
            "distances": [0.1 * i for i in range(len(docs))],
            "ids": list(self._documents.keys())[:n_results],
        }
    
    def search_with_scores(
        self,
        query: str,
        n_results: int = 5,
        score_threshold: float = 0.0,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        results = self.search(query, n_results, where)
        scored = []
        for i, doc in enumerate(results["documents"]):
            score = 1.0 - results["distances"][i]
            if score >= score_threshold:
                scored.append({
                    "document": doc,
                    "metadata": results["metadatas"][i],
                    "score": score,
                    "id": results["ids"][i],
                })
        return scored
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        return self._documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False
    
    def count(self) -> int:
        return len(self._documents)
    
    def clear(self) -> bool:
        self._documents.clear()
        return True


class MockHealthChecker:
    """Health Checker mock."""
    
    def __init__(self, healthy: bool = True):
        self._healthy = healthy
    
    async def check_all(self) -> Dict[str, Any]:
        status = "healthy" if self._healthy else "unhealthy"
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": 3600,
            "components": {
                "ollama": {"status": status, "message": "Mock"},
                "chromadb": {"status": status, "message": "Mock"},
                "disk": {"status": "healthy", "message": "Mock"},
                "memory": {"status": "healthy", "message": "Mock"},
            },
        }
    
    def get_quick_status(self) -> Dict[str, str]:
        return {
            "ollama": "healthy" if self._healthy else "unhealthy",
            "chromadb": "healthy",
            "disk": "healthy",
            "memory": "healthy",
        }


# =============================================================================
# PYTEST FIXTURES
# =============================================================================

@pytest.fixture
def mock_llm():
    """Mock LLM manager fixture."""
    return MockLLMManager()


@pytest.fixture
def mock_llm_custom_response():
    """Özelleştirilebilir yanıtlı mock LLM."""
    def _create(response: str):
        return MockLLMManager(default_response=response)
    return _create


@pytest.fixture
def mock_embedding():
    """Mock embedding manager fixture."""
    return MockEmbeddingManager()


@pytest.fixture
def mock_vector_store():
    """Mock vector store fixture."""
    return MockVectorStore()


@pytest.fixture
def mock_health_checker():
    """Mock health checker fixture."""
    return MockHealthChecker()


@pytest.fixture
def sample_documents():
    """Test dökümanları."""
    return [
        {
            "content": "Bu bir test dökümanıdır. Python programlama dili hakkında bilgi içerir.",
            "metadata": {"source": "test1.txt", "page_number": 1},
        },
        {
            "content": "FastAPI ile REST API geliştirme rehberi. Modern Python web framework.",
            "metadata": {"source": "test2.txt", "page_number": 1},
        },
        {
            "content": "Machine Learning ve yapay zeka temelleri. Derin öğrenme algoritmaları.",
            "metadata": {"source": "test3.txt", "page_number": 1},
        },
    ]


@pytest.fixture
def sample_messages():
    """Test mesajları."""
    return [
        {"role": "user", "content": "Merhaba, nasılsın?"},
        {"role": "assistant", "content": "İyiyim, teşekkür ederim! Size nasıl yardımcı olabilirim?"},
        {"role": "user", "content": "Python hakkında bilgi ver."},
    ]


@pytest.fixture
def temp_data_dir(tmp_path):
    """Geçici veri klasörü."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "chroma_db").mkdir()
    (data_dir / "uploads").mkdir()
    (data_dir / "sessions").mkdir()
    (data_dir / "cache").mkdir()
    return data_dir


@pytest.fixture
def mock_settings(temp_data_dir):
    """Mock settings."""
    class MockSettings:
        BASE_DIR = temp_data_dir.parent
        DATA_DIR = temp_data_dir
        LOGS_DIR = temp_data_dir.parent / "logs"
        CHROMA_PERSIST_DIR = str(temp_data_dir / "chroma_db")
        CHROMA_COLLECTION_NAME = "test_collection"
        CHUNK_SIZE = 500
        CHUNK_OVERLAP = 50
        TOP_K_RESULTS = 5
        EMBEDDING_DIMENSION = 768
        OLLAMA_BASE_URL = "http://localhost:11434"
        OLLAMA_PRIMARY_MODEL = "mock-model"
        OLLAMA_BACKUP_MODEL = "mock-backup"
        OLLAMA_EMBEDDING_MODEL = "mock-embed"
        API_HOST = "0.0.0.0"
        API_PORT = 8000
        
        def ensure_directories(self):
            self.LOGS_DIR.mkdir(exist_ok=True)
    
    return MockSettings()


# =============================================================================
# ASYNC FIXTURES
# =============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# PATCH HELPERS
# =============================================================================

@pytest.fixture
def patch_llm_manager(mock_llm):
    """LLM manager'ı mock ile değiştir."""
    with patch("core.llm_manager.llm_manager", mock_llm):
        yield mock_llm


@pytest.fixture
def patch_embedding_manager(mock_embedding):
    """Embedding manager'ı mock ile değiştir."""
    with patch("core.embedding.embedding_manager", mock_embedding):
        yield mock_embedding


@pytest.fixture
def patch_vector_store(mock_vector_store):
    """Vector store'u mock ile değiştir."""
    with patch("core.vector_store.vector_store", mock_vector_store):
        yield mock_vector_store


@pytest.fixture
def patch_all_services(mock_llm, mock_embedding, mock_vector_store):
    """Tüm servisleri mock ile değiştir."""
    with patch("core.llm_manager.llm_manager", mock_llm), \
         patch("core.embedding.embedding_manager", mock_embedding), \
         patch("core.vector_store.vector_store", mock_vector_store):
        yield {
            "llm": mock_llm,
            "embedding": mock_embedding,
            "vector_store": mock_vector_store,
        }


# =============================================================================
# TEST CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)


@pytest.fixture
def async_api_client():
    """Async FastAPI test client."""
    from httpx import AsyncClient
    from api.main import app
    
    async def _get_client():
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    return _get_client


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
    """Pytest markers kaydet."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "rag: RAG tests")
    config.addinivalue_line("markers", "agent: Agent tests")
    config.addinivalue_line("markers", "requires_ollama: Requires Ollama")
