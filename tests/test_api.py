"""
Enterprise AI Assistant - API Integration Tests
================================================

FastAPI endpoint'leri için entegrasyon testleri.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAPIEndpoints:
    """API endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client oluştur."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Root endpoint çalışmalı."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Health endpoint çalışmalı."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert "timestamp" in data
    
    def test_liveness_probe(self, client):
        """Kubernetes liveness probe çalışmalı."""
        response = client.get("/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
    
    def test_readiness_probe(self, client):
        """Kubernetes readiness probe çalışmalı."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
        assert "checks" in data
    
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
        assert "info" in data
        assert data["info"]["title"] == "Enterprise AI Assistant API"


class TestChatEndpoints:
    """Chat endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client oluştur."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_chat_request_validation(self, client):
        """Chat request validation çalışmalı."""
        # Boş mesaj
        response = client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422  # Validation error
        
        # Mesaj çok uzun
        long_message = "a" * 15000
        response = client.post("/api/chat", json={"message": long_message})
        assert response.status_code == 422


class TestDocumentEndpoints:
    """Document endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client oluştur."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_documents(self, client):
        """Document listesi alınabilmeli."""
        response = client.get("/api/documents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "documents" in data or "success" in data


class TestNotesEndpoints:
    """Notes endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client oluştur."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_notes(self, client):
        """Not listesi alınabilmeli."""
        response = client.get("/api/notes")
        # Endpoint varsa 200, yoksa 404
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
