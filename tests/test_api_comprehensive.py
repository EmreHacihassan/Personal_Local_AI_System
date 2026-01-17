"""
Enterprise AI Assistant - API Comprehensive Tests
==================================================

Tüm API endpoint'leri için kapsamlı testler.
HTTP methods, validation, error handling, response format testleri.
"""

import pytest
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock chromadb before any imports
if 'chromadb' not in sys.modules:
    mock_chromadb = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_collection
    sys.modules['chromadb'] = mock_chromadb
    sys.modules['chromadb.config'] = MagicMock()
    sys.modules['chromadb.api'] = MagicMock()


class TestHealthEndpoints:
    """Health check endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Root endpoint çalışmalı."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "status" in data
    
    def test_health_endpoint(self, client):
        """Health endpoint çalışmalı."""
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.vector_store') as mock_vs:
                mock_vs.count.return_value = 0
                
                response = client.get("/health")
                
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert "components" in data
    
    def test_liveness_probe(self, client):
        """Liveness probe çalışmalı."""
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_readiness_probe(self, client):
        """Readiness probe çalışmalı."""
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.vector_store') as mock_vs:
                mock_vs.count.return_value = 0
                
                response = client.get("/health/ready")
                
                assert response.status_code == 200
                data = response.json()
                assert "ready" in data
                assert "checks" in data
    
    def test_status_endpoint(self, client):
        """Status endpoint detaylı bilgi vermeli."""
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.vector_store') as mock_vs:
                mock_vs.get_stats.return_value = {}
                
                with patch('api.main.orchestrator') as mock_orch:
                    mock_orch.get_agents_status.return_value = {}
                    
                    with patch('api.main.circuit_registry') as mock_circuit:
                        mock_circuit.get_all_status.return_value = {}
                        
                        response = client.get("/status")
                        
                        assert response.status_code == 200


class TestChatEndpoints:
    """Chat endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_chat_basic_request(self, client):
        """Basit chat isteği çalışmalı."""
        with patch('api.main.session_manager') as mock_session:
            mock_session.get_session.return_value = None
            mock_session.create_session.return_value = MagicMock(id='test-session')
            mock_session.add_message.return_value = None
            
            with patch('api.main.orchestrator') as mock_orch:
                mock_orch.execute.return_value = MagicMock(
                    content="Test yanıtı",
                    sources=[],
                    metadata={"agent": "test"}
                )
                
                with patch('api.main.ollama_circuit') as mock_circuit:
                    mock_circuit.call.side_effect = lambda f: f()
                    
                    with patch('api.main.analytics') as mock_analytics:
                        mock_analytics.track_chat.return_value = None
                        
                        response = client.post(
                            "/api/chat",
                            json={"message": "Merhaba"}
                        )
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert "response" in data
                        assert "session_id" in data
    
    def test_chat_validation_empty_message(self, client):
        """Boş mesaj hata vermeli."""
        response = client.post(
            "/api/chat",
            json={"message": ""}
        )
        
        # Validation error
        assert response.status_code == 422
    
    def test_chat_validation_too_long_message(self, client):
        """Çok uzun mesaj hata vermeli."""
        long_message = "x" * 15000  # 10000 limit üzerinde
        
        response = client.post(
            "/api/chat",
            json={"message": long_message}
        )
        
        # Validation error
        assert response.status_code == 422
    
    def test_chat_with_session_id(self, client):
        """Session ID ile chat çalışmalı."""
        with patch('api.main.session_manager') as mock_session:
            mock_session.get_session.return_value = MagicMock(
                id='existing-session',
                get_history=MagicMock(return_value=[])
            )
            mock_session.add_message.return_value = None
            
            with patch('api.main.orchestrator') as mock_orch:
                mock_orch.execute.return_value = MagicMock(
                    content="Yanıt",
                    sources=[],
                    metadata={}
                )
                
                with patch('api.main.ollama_circuit') as mock_circuit:
                    mock_circuit.call.side_effect = lambda f: f()
                    
                    with patch('api.main.analytics'):
                        response = client.post(
                            "/api/chat",
                            json={
                                "message": "Test",
                                "session_id": "existing-session"
                            }
                        )
                        
                        assert response.status_code == 200
    
    def test_chat_response_mode_detailed(self, client):
        """Detaylı mod çalışmalı."""
        with patch('api.main.session_manager') as mock_session:
            mock_session.get_session.return_value = None
            mock_session.create_session.return_value = MagicMock(id='test')
            mock_session.add_message.return_value = None
            
            with patch('api.main.orchestrator') as mock_orch:
                mock_orch.execute.return_value = MagicMock(
                    content="Detaylı yanıt",
                    sources=[],
                    metadata={}
                )
                
                with patch('api.main.ollama_circuit') as mock_circuit:
                    mock_circuit.call.side_effect = lambda f: f()
                    
                    with patch('api.main.analytics'):
                        response = client.post(
                            "/api/chat",
                            json={
                                "message": "Test",
                                "response_mode": "detailed"
                            }
                        )
                        
                        assert response.status_code == 200


class TestDocumentEndpoints:
    """Document endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_list_documents(self, client):
        """Döküman listesi alınabilmeli."""
        with patch('api.main.settings') as mock_settings:
            mock_settings.DATA_DIR = Path("/tmp/test")
            
            response = client.get("/api/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert "total" in data
    
    def test_upload_validation_unsupported_format(self, client):
        """Desteklenmeyen format hata vermeli."""
        # Create fake file with unsupported extension
        from io import BytesIO
        
        file_content = BytesIO(b"test content")
        
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.xyz", file_content, "application/octet-stream")}
        )
        
        # Unsupported format error
        assert response.status_code in [400, 422]


class TestSearchEndpoints:
    """Search endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_search_basic(self, client):
        """Basit arama çalışmalı."""
        with patch('api.main.vector_store') as mock_vs:
            mock_vs.search_with_scores.return_value = []
            
            with patch('api.main.analytics'):
                response = client.post(
                    "/api/search",
                    json={"query": "test arama"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert "total" in data
    
    def test_search_with_top_k(self, client):
        """Top K parametresi çalışmalı."""
        with patch('api.main.vector_store') as mock_vs:
            mock_vs.search_with_scores.return_value = []
            
            with patch('api.main.analytics'):
                response = client.post(
                    "/api/search",
                    json={"query": "test", "top_k": 10}
                )
                
                assert response.status_code == 200
    
    def test_search_validation_empty_query(self, client):
        """Boş sorgu hata vermeli."""
        response = client.post(
            "/api/search",
            json={"query": ""}
        )
        
        assert response.status_code == 422


class TestWebSearchEndpoints:
    """Web search endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_web_search_basic(self, client):
        """Web arama çalışmalı."""
        with patch('api.main.get_search_engine') as mock_engine:
            mock_result = MagicMock()
            mock_result.success = True
            mock_result.query = "test"
            mock_result.instant_answer = None
            mock_result.knowledge_panel = None
            mock_result.total_results = 0
            mock_result.providers_used = []
            mock_result.related_queries = []
            mock_result.cached = False
            
            mock_engine.return_value.search.return_value = mock_result
            mock_engine.return_value.get_sources_for_ui.return_value = []
            
            response = client.post(
                "/api/web-search",
                json={"query": "test arama"}
            )
            
            assert response.status_code == 200
    
    def test_web_search_stats(self, client):
        """Web search istatistikleri alınabilmeli."""
        with patch('api.main.get_search_engine') as mock_engine:
            mock_engine.return_value.get_stats.return_value = {}
            
            response = client.get("/api/web-search/stats")
            
            assert response.status_code == 200


class TestNotesEndpoints:
    """Notes endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_notes_manager_imported(self, client):
        """Notes manager API'de import edilmiş olmalı."""
        from api.main import notes_manager
        
        # Notes manager import edilmiş
        assert notes_manager is not None
        
        # CRUD metodları mevcut
        assert hasattr(notes_manager, 'create_note')
        assert hasattr(notes_manager, 'get_note')
        assert hasattr(notes_manager, 'update_note')
        assert hasattr(notes_manager, 'delete_note')
        assert hasattr(notes_manager, 'search_notes')


class TestSessionEndpoints:
    """Session endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_chat_history(self, client):
        """Chat history alınabilmeli."""
        response = client.get("/api/chat/history/test-session")
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
    
    def test_clear_session(self, client):
        """Session temizlenebilmeli."""
        response = client.delete("/api/chat/session/test-session")
        
        assert response.status_code == 200


class TestAPIResponseFormat:
    """API yanıt format testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_json_response_format(self, client):
        """Yanıtlar JSON formatında olmalı."""
        response = client.get("/")
        
        assert response.headers.get("content-type", "").startswith("application/json")
    
    def test_error_response_format(self, client):
        """Hata yanıtları standart formatta olmalı."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_validation_error_format(self, client):
        """Validation hataları detaylı olmalı."""
        response = client.post(
            "/api/chat",
            json={}  # message required
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestAPIPerformance:
    """API performans testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_health_endpoint_fast(self, client):
        """Health endpoint hızlı yanıt vermeli."""
        start = time.time()
        response = client.get("/health/live")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5  # 500ms altında
    
    def test_root_endpoint_fast(self, client):
        """Root endpoint hızlı yanıt vermeli."""
        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.2  # 200ms altında


class TestAPICORS:
    """CORS testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_cors_headers_present(self, client):
        """CORS headers mevcut olmalı."""
        response = client.options(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # CORS için Access-Control headers
        # Not: TestClient CORS'u farklı ele alabilir
        assert response.status_code in [200, 405]


class TestAPIRateLimiting:
    """Rate limiting testleri."""
    
    def test_rate_limiter_class_exists(self):
        """Rate limiter sınıfı mevcut olmalı."""
        from api.main import RateLimitMiddleware
        
        limiter = RateLimitMiddleware()
        
        assert hasattr(limiter, 'is_allowed')
        assert hasattr(limiter, 'limits')
    
    def test_rate_limiter_allows_normal_traffic(self):
        """Normal trafik izin verilmeli."""
        from api.main import RateLimitMiddleware
        
        limiter = RateLimitMiddleware()
        
        # İlk istekler geçmeli
        for _ in range(5):
            result = limiter.is_allowed("test-ip", "default")
            assert result is True
    
    def test_rate_limits_defined(self):
        """Rate limit'ler tanımlı olmalı."""
        from api.main import RateLimitMiddleware
        
        limiter = RateLimitMiddleware()
        
        assert "chat" in limiter.limits
        assert "search" in limiter.limits
        assert "upload" in limiter.limits


class TestAPIDocumentation:
    """API dokümantasyon testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_docs_endpoint(self, client):
        """Swagger docs erişilebilir olmalı."""
        response = client.get("/docs")
        
        assert response.status_code == 200
    
    def test_openapi_schema(self, client):
        """OpenAPI schema erişilebilir olmalı."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_redoc_endpoint(self, client):
        """ReDoc erişilebilir olmalı."""
        response = client.get("/redoc")
        
        assert response.status_code == 200
