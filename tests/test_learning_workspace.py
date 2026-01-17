"""
Enterprise AI Assistant - Learning Workspace Tests
====================================================

AI ile Öğren özelliği için kapsamlı testler.
Workspaces, documents, sources, tests, chat testleri.
"""

import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

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


class TestLearningWorkspaceAPI:
    """Learning API endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_list_workspaces_endpoint(self, client):
        """Workspaces listesi endpoint'i çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.list_workspaces.return_value = []
            
            response = client.get("/api/learning/workspaces")
            
            assert response.status_code == 200
            data = response.json()
            assert "workspaces" in data
            assert "total" in data
    
    def test_create_workspace_endpoint(self, client):
        """Workspace oluşturma endpoint'i çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_workspace.to_dict.return_value = {
                "id": "test-id",
                "name": "Test Workspace",
                "description": "",
                "topic": "Python",
                "status": "active",
                "active_sources": [],
                "inactive_sources": [],
                "documents": [],
                "tests": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_manager.create_workspace.return_value = mock_workspace
            
            response = client.post(
                "/api/learning/workspaces",
                json={
                    "name": "Test Workspace",
                    "topic": "Python"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "workspace" in data
    
    def test_create_workspace_validation(self, client):
        """Workspace oluşturma validasyonu çalışmalı."""
        # Boş isim
        response = client.post(
            "/api/learning/workspaces",
            json={"name": ""}
        )
        
        assert response.status_code == 422
    
    def test_get_workspace_endpoint(self, client):
        """Workspace detay endpoint'i çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_workspace.to_dict.return_value = {
                "id": "test-id",
                "name": "Test",
                "description": "",
                "topic": "",
                "status": "active",
                "active_sources": [],
                "inactive_sources": [],
                "documents": [],
                "tests": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_manager.get_workspace.return_value = mock_workspace
            mock_manager.get_workspace_stats.return_value = {}
            mock_manager.list_documents.return_value = []
            mock_manager.list_tests.return_value = []
            
            response = client.get("/api/learning/workspaces/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert "workspace" in data
            assert "stats" in data
    
    def test_get_nonexistent_workspace(self, client):
        """Olmayan workspace 404 dönmeli."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.get_workspace.return_value = None
            
            response = client.get("/api/learning/workspaces/nonexistent")
            
            assert response.status_code == 404
    
    def test_delete_workspace_endpoint(self, client):
        """Workspace silme endpoint'i çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_manager.get_workspace.return_value = mock_workspace
            mock_manager.delete_workspace.return_value = True
            
            response = client.delete("/api/learning/workspaces/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestLearningDocumentsAPI:
    """Document API endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_document_styles(self, client):
        """Document stilleri alınabilmeli."""
        with patch('api.learning_endpoints.study_document_generator') as mock_gen:
            mock_gen.get_available_styles.return_value = {
                "styles": [
                    {"id": "detailed", "name": "Detaylı"},
                    {"id": "concise", "name": "Özet"}
                ]
            }
            
            response = client.get("/api/learning/documents/styles")
            
            assert response.status_code == 200
    
    def test_create_document_endpoint(self, client):
        """Document oluşturma çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_manager.get_workspace.return_value = mock_workspace
            
            mock_document = MagicMock()
            mock_document.to_dict.return_value = {
                "id": "doc-id",
                "title": "Python Temelleri",
                "topic": "Python programlama",
                "content": "",
                "page_count": 5,
                "style": "detailed",
                "status": "draft",
                "references": [],
                "generation_log": [],
                "workspace_id": "ws-id",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_manager.create_document.return_value = mock_document
            
            response = client.post(
                "/api/learning/workspaces/ws-id/documents",
                json={
                    "title": "Python Temelleri",
                    "topic": "Python programlama",
                    "page_count": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "document" in data
    
    def test_create_document_validation(self, client):
        """Document oluşturma validasyonu çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.get_workspace.return_value = MagicMock()
            
            # page_count 0 veya negatif olamaz
            response = client.post(
                "/api/learning/workspaces/ws-id/documents",
                json={
                    "title": "Test",
                    "topic": "Konu",
                    "page_count": 0
                }
            )
            
            assert response.status_code == 422
    
    def test_get_document_endpoint(self, client):
        """Document detay endpoint'i çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_document = MagicMock()
            mock_document.to_dict.return_value = {
                "id": "doc-id",
                "title": "Test Doc",
                "topic": "Topic",
                "content": "İçerik",
                "page_count": 5,
                "style": "detailed",
                "status": "completed",
                "references": [],
                "generation_log": [],
                "workspace_id": "ws-id",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_manager.get_document.return_value = mock_document
            
            response = client.get("/api/learning/documents/doc-id")
            
            assert response.status_code == 200
            data = response.json()
            assert "document" in data
    
    def test_list_documents_endpoint(self, client):
        """Document listesi çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.list_documents.return_value = []
            
            response = client.get("/api/learning/workspaces/ws-id/documents")
            
            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert "total" in data


class TestLearningTestsAPI:
    """Test (quiz) API endpoint testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_test_types(self, client):
        """Test türleri alınabilmeli."""
        with patch('api.learning_endpoints.test_generator') as mock_gen:
            mock_gen.get_available_types.return_value = {
                "types": [
                    {"id": "multiple_choice", "name": "Çoktan Seçmeli"},
                    {"id": "true_false", "name": "Doğru/Yanlış"}
                ]
            }
            
            response = client.get("/api/learning/tests/types")
            
            assert response.status_code == 200
    
    def test_get_difficulty_levels(self, client):
        """Zorluk seviyeleri alınabilmeli."""
        with patch('api.learning_endpoints.test_generator') as mock_gen:
            mock_gen.get_difficulty_levels.return_value = {
                "levels": ["easy", "medium", "hard", "mixed"]
            }
            
            response = client.get("/api/learning/tests/difficulties")
            
            assert response.status_code == 200
    
    def test_create_test_endpoint(self, client):
        """Test oluşturma çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_manager.get_workspace.return_value = mock_workspace
            
            mock_test = MagicMock()
            mock_test.to_dict.return_value = {
                "id": "test-id",
                "title": "Python Quiz",
                "description": "",
                "test_type": "multiple_choice",
                "question_count": 10,
                "difficulty": "mixed",
                "questions": [],
                "answers": {},
                "score": None,
                "status": "draft",
                "workspace_id": "ws-id",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_manager.create_test.return_value = mock_test
            
            response = client.post(
                "/api/learning/workspaces/ws-id/tests",
                json={
                    "title": "Python Quiz",
                    "question_count": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "test" in data
    
    def test_create_test_validation(self, client):
        """Test oluşturma validasyonu çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.get_workspace.return_value = MagicMock()
            
            # question_count 0 olamaz
            response = client.post(
                "/api/learning/workspaces/ws-id/tests",
                json={
                    "title": "Test",
                    "question_count": 0
                }
            )
            
            assert response.status_code == 422
    
    def test_get_test_endpoint(self, client):
        """Test detay endpoint'i çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.to_dict.return_value = {
                "id": "test-id",
                "title": "Quiz",
                "description": "",
                "test_type": "multiple_choice",
                "question_count": 5,
                "difficulty": "easy",
                "questions": [],
                "answers": {},
                "score": None,
                "status": "ready",
                "workspace_id": "ws-id",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            mock_manager.get_test.return_value = mock_test
            
            response = client.get("/api/learning/tests/test-id")
            
            assert response.status_code == 200
            data = response.json()
            assert "test" in data
    
    def test_list_tests_endpoint(self, client):
        """Test listesi çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.list_tests.return_value = []
            
            response = client.get("/api/learning/workspaces/ws-id/tests")
            
            assert response.status_code == 200
            data = response.json()
            assert "tests" in data
            assert "total" in data


class TestLearningSourcesAPI:
    """Source management API testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_workspace_sources(self, client):
        """Workspace kaynakları alınabilmeli."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_workspace.active_sources = []
            mock_workspace.inactive_sources = []
            mock_manager.get_workspace.return_value = mock_workspace
            
            with patch('api.learning_endpoints.vector_store') as mock_vs:
                mock_vs.get_unique_sources.return_value = []
                mock_vs.get_document_stats.return_value = {"sources": {}}
                
                with patch('api.learning_endpoints.settings') as mock_settings:
                    mock_settings.DATA_DIR = Path(tempfile.gettempdir())
                    
                    response = client.get("/api/learning/workspaces/ws-id/sources")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "sources" in data
                    assert "active_count" in data
                    assert "total" in data
    
    def test_toggle_source(self, client):
        """Source aktif/deaktif çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.toggle_source.return_value = True
            
            response = client.post(
                "/api/learning/workspaces/ws-id/sources/toggle",
                json={
                    "source_id": "source-123",
                    "active": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["active"] is True
    
    def test_bulk_toggle_sources(self, client):
        """Toplu source aktif/deaktif çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_workspace.active_sources = ["source-1", "source-2"]
            mock_workspace.inactive_sources = []
            mock_manager.get_workspace.return_value = mock_workspace
            mock_manager.toggle_source.return_value = True
            
            response = client.post(
                "/api/learning/workspaces/ws-id/sources/bulk-toggle",
                json={"active": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestLearningChatAPI:
    """Learning chat API testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_chat_history(self, client):
        """Chat geçmişi alınabilmeli."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.get_chat_history.return_value = [
                {"role": "user", "content": "Merhaba"},
                {"role": "assistant", "content": "Merhaba! Nasıl yardımcı olabilirim?"}
            ]
            
            response = client.get("/api/learning/workspaces/ws-id/chat")
            
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert "total" in data
    
    def test_send_chat_message(self, client):
        """Chat mesajı gönderilebilmeli."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_workspace = MagicMock()
            mock_workspace.name = "Test Workspace"
            mock_workspace.topic = "Python"
            mock_workspace.active_sources = []
            mock_manager.get_workspace.return_value = mock_workspace
            mock_manager.add_chat_message.return_value = None
            
            with patch('api.learning_endpoints.vector_store') as mock_vs:
                mock_vs.search_with_scores.return_value = []
                
                with patch('core.llm_manager.llm_manager') as mock_llm:
                    mock_llm.generate.return_value = "Bu bir test yanıtıdır."
                    
                    response = client.post(
                        "/api/learning/workspaces/ws-id/chat",
                        json={"message": "Python nedir?"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert "response" in data


class TestLearningStatsAPI:
    """Learning stats API testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_get_learning_stats(self, client):
        """Öğrenme istatistikleri alınabilmeli."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.list_workspaces.return_value = []
            
            response = client.get("/api/learning/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "workspaces_count" in data
            assert "documents_count" in data
            assert "tests_count" in data
            assert "completed_tests" in data
            assert "average_score" in data


class TestLearningWorkspaceManager:
    """LearningWorkspaceManager unit testleri."""
    
    def test_workspace_manager_import(self):
        """LearningWorkspaceManager import edilebilmeli."""
        from core.learning_workspace import learning_workspace_manager
        
        assert learning_workspace_manager is not None
    
    def test_workspace_model_exists(self):
        """LearningWorkspace modeli mevcut olmalı."""
        from core.learning_workspace import LearningWorkspace
        
        assert LearningWorkspace is not None
    
    def test_document_model_exists(self):
        """StudyDocument modeli mevcut olmalı."""
        from core.learning_workspace import StudyDocument
        
        assert StudyDocument is not None
    
    def test_test_model_exists(self):
        """Test modeli mevcut olmalı."""
        from core.learning_workspace import Test
        
        assert Test is not None
    
    def test_status_enums_exist(self):
        """Status enumları mevcut olmalı."""
        from core.learning_workspace import TestType, TestStatus, DocumentStatus, WorkspaceStatus
        
        assert TestType is not None
        assert TestStatus is not None
        assert DocumentStatus is not None
        assert WorkspaceStatus is not None


class TestStudyDocumentGenerator:
    """StudyDocumentGenerator testleri."""
    
    def test_generator_import(self):
        """StudyDocumentGenerator import edilebilmeli."""
        from core.study_document_generator import study_document_generator
        
        assert study_document_generator is not None
    
    def test_get_available_styles(self):
        """Stiller alınabilmeli."""
        from core.study_document_generator import study_document_generator
        
        styles = study_document_generator.get_available_styles()
        
        assert styles is not None
        # styles dict veya styles key içeren dict olabilir
        assert isinstance(styles, dict)
        assert len(styles) > 0


class TestTestGenerator:
    """TestGenerator testleri."""
    
    def test_generator_import(self):
        """TestGenerator import edilebilmeli."""
        from core.test_generator import test_generator
        
        assert test_generator is not None
    
    def test_get_available_types(self):
        """Test türleri alınabilmeli."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert types is not None
    
    def test_get_difficulty_levels(self):
        """Zorluk seviyeleri alınabilmeli."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        assert levels is not None


class TestLearningDataModels:
    """Learning data modelleri testleri."""
    
    def test_test_type_enum(self):
        """TestType enum değerleri doğru olmalı."""
        from core.learning_workspace import TestType
        
        assert hasattr(TestType, 'MULTIPLE_CHOICE')
        assert hasattr(TestType, 'TRUE_FALSE')
    
    def test_document_status_enum(self):
        """DocumentStatus enum değerleri doğru olmalı."""
        from core.learning_workspace import DocumentStatus
        
        assert hasattr(DocumentStatus, 'DRAFT')
        assert hasattr(DocumentStatus, 'GENERATING')
        assert hasattr(DocumentStatus, 'COMPLETED')
        assert hasattr(DocumentStatus, 'FAILED')
    
    def test_test_status_enum(self):
        """TestStatus enum değerleri doğru olmalı."""
        from core.learning_workspace import TestStatus
        
        assert hasattr(TestStatus, 'NOT_STARTED')
        assert hasattr(TestStatus, 'IN_PROGRESS')
        assert hasattr(TestStatus, 'COMPLETED')
    
    def test_workspace_status_enum(self):
        """WorkspaceStatus enum değerleri doğru olmalı."""
        from core.learning_workspace import WorkspaceStatus
        
        assert hasattr(WorkspaceStatus, 'ACTIVE')
        assert hasattr(WorkspaceStatus, 'ARCHIVED')


class TestLearningRequestModels:
    """Request model testleri."""
    
    def test_create_workspace_request(self):
        """CreateWorkspaceRequest çalışmalı."""
        from api.learning_endpoints import CreateWorkspaceRequest
        
        request = CreateWorkspaceRequest(
            name="Test Workspace",
            description="Açıklama",
            topic="Python"
        )
        
        assert request.name == "Test Workspace"
        assert request.topic == "Python"
    
    def test_create_document_request(self):
        """CreateDocumentRequest çalışmalı."""
        from api.learning_endpoints import CreateDocumentRequest
        
        request = CreateDocumentRequest(
            title="Python Temelleri",
            topic="Python programlama dili",
            page_count=10,
            style="detailed"
        )
        
        assert request.title == "Python Temelleri"
        assert request.page_count == 10
    
    def test_create_test_request(self):
        """CreateTestRequest çalışmalı."""
        from api.learning_endpoints import CreateTestRequest
        
        request = CreateTestRequest(
            title="Python Quiz",
            question_count=20,
            difficulty="medium"
        )
        
        assert request.title == "Python Quiz"
        assert request.question_count == 20
    
    def test_submit_answer_request(self):
        """SubmitAnswerRequest çalışmalı."""
        from api.learning_endpoints import SubmitAnswerRequest
        
        request = SubmitAnswerRequest(
            question_id="q-123",
            answer="A"
        )
        
        assert request.question_id == "q-123"
        assert request.answer == "A"
    
    def test_chat_message_request(self):
        """ChatMessageRequest çalışmalı."""
        from api.learning_endpoints import ChatMessageRequest
        
        request = ChatMessageRequest(message="Merhaba")
        
        assert request.message == "Merhaba"


class TestLearningDocumentGeneration:
    """Document generation testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_generate_document_endpoint(self, client):
        """Document üretim başlatma çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_document = MagicMock()
            mock_document.status = "draft"
            mock_document.workspace_id = "ws-id"
            mock_document.generation_log = []
            mock_manager.get_document.return_value = mock_document
            mock_manager.update_document.return_value = None
            
            mock_workspace = MagicMock()
            mock_workspace.active_sources = []
            mock_manager.get_workspace.return_value = mock_workspace
            
            with patch('api.learning_endpoints.study_document_generator') as mock_gen:
                mock_gen.generate_document_sync.return_value = {"success": True}
                
                response = client.post("/api/learning/documents/doc-id/generate")
                
                assert response.status_code == 200
    
    def test_cancel_document_generation(self, client):
        """Document üretimi iptal edilebilmeli."""
        from core.learning_workspace import DocumentStatus
        
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_document = MagicMock()
            mock_document.status = DocumentStatus.GENERATING
            mock_document.generation_log = []
            mock_manager.get_document.return_value = mock_document
            mock_manager.update_document.return_value = None
            
            response = client.post("/api/learning/documents/doc-id/cancel")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestLearningTestGeneration:
    """Test (quiz) generation testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_submit_answer_endpoint(self, client):
        """Cevap gönderme çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.submit_test_answer.return_value = True
            
            with patch('api.learning_endpoints.test_generator') as mock_gen:
                # Use MagicMock for sync-compatible mock
                mock_gen.grade_answer = MagicMock(return_value={
                    "correct": True, 
                    "explanation": "Doğru!"
                })
                
                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop.return_value.run_until_complete.return_value = {
                        "correct": True,
                        "explanation": "Doğru!"
                    }
                    
                    response = client.post(
                        "/api/learning/tests/test-id/answer",
                        json={
                            "question_id": "q-1",
                            "answer": "A"
                        }
                    )
                    
                    assert response.status_code == 200
    
    def test_complete_test_endpoint(self, client):
        """Test tamamlama çalışmalı."""
        with patch('api.learning_endpoints.learning_workspace_manager') as mock_manager:
            mock_manager.complete_test.return_value = {
                "score": 80,
                "correct_count": 8,
                "total_questions": 10,
                "passed": True
            }
            
            response = client.post("/api/learning/tests/test-id/complete")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "result" in data
