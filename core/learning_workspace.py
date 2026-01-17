"""
AI ile Öğren - Çalışma Ortamı Yönetimi
Enterprise Learning Workspace Manager

Çalışma ortamları, kaynaklar, testler ve dökümanları yönetir.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import shutil

from core.config import settings


class WorkspaceStatus(str, Enum):
    """Çalışma ortamı durumu."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentStatus(str, Enum):
    """Çalışma dökümanı durumu."""
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TestStatus(str, Enum):
    """Test durumu."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TestType(str, Enum):
    """Test türleri."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    MIXED = "mixed"


@dataclass
class SourceReference:
    """Kaynak referansı - satır bazlı."""
    source_id: str
    source_name: str
    source_type: str  # file, url
    line_start: int
    line_end: int
    content_preview: str = ""


@dataclass 
class StudyDocument:
    """Çalışma dökümanı."""
    id: str
    workspace_id: str
    title: str
    topic: str
    page_count: int
    style: str  # academic, casual, detailed, summary
    content: str = ""
    status: DocumentStatus = DocumentStatus.DRAFT
    references: List[Dict] = field(default_factory=list)  # Satır bazlı kaynakça
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    generation_log: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value if isinstance(self.status, DocumentStatus) else self.status
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StudyDocument':
        if isinstance(data.get('status'), str):
            data['status'] = DocumentStatus(data['status'])
        return cls(**data)


@dataclass
class TestQuestion:
    """Test sorusu."""
    id: str
    question: str
    question_type: TestType
    options: List[str] = field(default_factory=list)  # Çoktan seçmeli için
    correct_answer: str = ""
    explanation: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    source_ref: str = ""  # Hangi kaynaktan
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['question_type'] = self.question_type.value if isinstance(self.question_type, TestType) else self.question_type
        return data


@dataclass
class Test:
    """Test."""
    id: str
    workspace_id: str
    title: str
    description: str
    test_type: TestType
    question_count: int
    difficulty: str = "mixed"  # easy, medium, hard, mixed
    questions: List[Dict] = field(default_factory=list)
    user_answers: Dict[str, str] = field(default_factory=dict)
    score: Optional[float] = None
    status: TestStatus = TestStatus.NOT_STARTED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    feedback: str = ""
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['test_type'] = self.test_type.value if isinstance(self.test_type, TestType) else self.test_type
        data['status'] = self.status.value if isinstance(self.status, TestStatus) else self.status
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Test':
        if isinstance(data.get('test_type'), str):
            data['test_type'] = TestType(data['test_type'])
        if isinstance(data.get('status'), str):
            data['status'] = TestStatus(data['status'])
        return cls(**data)


@dataclass
class LearningWorkspace:
    """Öğrenme çalışma ortamı."""
    id: str
    name: str
    description: str = ""
    topic: str = ""
    active_sources: List[str] = field(default_factory=list)  # Aktif kaynak ID'leri
    inactive_sources: List[str] = field(default_factory=list)  # Deaktif kaynak ID'leri
    documents: List[str] = field(default_factory=list)  # Döküman ID'leri
    tests: List[str] = field(default_factory=list)  # Test ID'leri
    chat_history: List[Dict] = field(default_factory=list)
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value if isinstance(self.status, WorkspaceStatus) else self.status
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LearningWorkspace':
        if isinstance(data.get('status'), str):
            data['status'] = WorkspaceStatus(data['status'])
        return cls(**data)


class LearningWorkspaceManager:
    """Öğrenme çalışma ortamları yöneticisi."""
    
    def __init__(self):
        self.base_dir = settings.DATA_DIR / "learning_workspaces"
        self.workspaces_dir = self.base_dir / "workspaces"
        self.documents_dir = self.base_dir / "documents"
        self.tests_dir = self.base_dir / "tests"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Gerekli klasörleri oluştur."""
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== WORKSPACE OPERATIONS ====================
    
    def create_workspace(
        self,
        name: str,
        description: str = "",
        topic: str = "",
        initial_sources: List[str] = None
    ) -> LearningWorkspace:
        """Yeni çalışma ortamı oluştur."""
        workspace = LearningWorkspace(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            topic=topic,
            active_sources=initial_sources or [],
        )
        
        self._save_workspace(workspace)
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[LearningWorkspace]:
        """Çalışma ortamını getir."""
        file_path = self.workspaces_dir / f"{workspace_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return LearningWorkspace.from_dict(data)
        except Exception as e:
            print(f"Workspace yükleme hatası: {e}")
            return None
    
    def list_workspaces(self, include_archived: bool = False) -> List[LearningWorkspace]:
        """Tüm çalışma ortamlarını listele."""
        workspaces = []
        
        for file_path in self.workspaces_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                workspace = LearningWorkspace.from_dict(data)
                
                if workspace.status == WorkspaceStatus.DELETED:
                    continue
                if not include_archived and workspace.status == WorkspaceStatus.ARCHIVED:
                    continue
                
                workspaces.append(workspace)
            except Exception as e:
                print(f"Workspace okuma hatası {file_path}: {e}")
        
        # En son güncellenen en üstte
        workspaces.sort(key=lambda x: x.updated_at, reverse=True)
        return workspaces
    
    def update_workspace(self, workspace: LearningWorkspace) -> LearningWorkspace:
        """Çalışma ortamını güncelle."""
        workspace.updated_at = datetime.now().isoformat()
        self._save_workspace(workspace)
        return workspace
    
    def delete_workspace(self, workspace_id: str, permanent: bool = False):
        """Çalışma ortamını sil."""
        if permanent:
            file_path = self.workspaces_dir / f"{workspace_id}.json"
            if file_path.exists():
                file_path.unlink()
        else:
            workspace = self.get_workspace(workspace_id)
            if workspace:
                workspace.status = WorkspaceStatus.DELETED
                self._save_workspace(workspace)
    
    def archive_workspace(self, workspace_id: str):
        """Çalışma ortamını arşivle."""
        workspace = self.get_workspace(workspace_id)
        if workspace:
            workspace.status = WorkspaceStatus.ARCHIVED
            self._save_workspace(workspace)
    
    def _save_workspace(self, workspace: LearningWorkspace):
        """Çalışma ortamını kaydet."""
        file_path = self.workspaces_dir / f"{workspace.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(workspace.to_dict(), f, ensure_ascii=False, indent=2)
    
    # ==================== SOURCE MANAGEMENT ====================
    
    def toggle_source(self, workspace_id: str, source_id: str, active: bool) -> bool:
        """Kaynağı aktif/deaktif et."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        if active:
            if source_id not in workspace.active_sources:
                workspace.active_sources.append(source_id)
            if source_id in workspace.inactive_sources:
                workspace.inactive_sources.remove(source_id)
        else:
            if source_id not in workspace.inactive_sources:
                workspace.inactive_sources.append(source_id)
            if source_id in workspace.active_sources:
                workspace.active_sources.remove(source_id)
        
        self.update_workspace(workspace)
        return True
    
    def get_active_sources(self, workspace_id: str) -> List[str]:
        """Aktif kaynakları getir."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return []
        return workspace.active_sources
    
    # ==================== DOCUMENT OPERATIONS ====================
    
    def create_document(
        self,
        workspace_id: str,
        title: str,
        topic: str,
        page_count: int,
        style: str = "detailed"
    ) -> StudyDocument:
        """Yeni çalışma dökümanı oluştur."""
        doc = StudyDocument(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=title,
            topic=topic,
            page_count=min(page_count, 40),  # Max 40 sayfa
            style=style,
        )
        
        self._save_document(doc)
        
        # Workspace'e ekle
        workspace = self.get_workspace(workspace_id)
        if workspace:
            workspace.documents.append(doc.id)
            self.update_workspace(workspace)
        
        return doc
    
    def get_document(self, document_id: str) -> Optional[StudyDocument]:
        """Dökümanı getir."""
        file_path = self.documents_dir / f"{document_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return StudyDocument.from_dict(data)
        except Exception as e:
            print(f"Document yükleme hatası: {e}")
            return None
    
    def list_documents(self, workspace_id: str) -> List[StudyDocument]:
        """Çalışma ortamındaki dökümanları listele."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return []
        
        documents = []
        for doc_id in workspace.documents:
            doc = self.get_document(doc_id)
            if doc:
                documents.append(doc)
        
        documents.sort(key=lambda x: x.created_at, reverse=True)
        return documents
    
    def update_document(self, document: StudyDocument) -> StudyDocument:
        """Dökümanı güncelle."""
        self._save_document(document)
        return document
    
    def _save_document(self, document: StudyDocument):
        """Dökümanı kaydet."""
        file_path = self.documents_dir / f"{document.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(document.to_dict(), f, ensure_ascii=False, indent=2)
    
    # ==================== TEST OPERATIONS ====================
    
    def create_test(
        self,
        workspace_id: str,
        title: str,
        description: str,
        test_type: TestType,
        question_count: int,
        difficulty: str = "mixed"
    ) -> Test:
        """Yeni test oluştur."""
        test = Test(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=title,
            description=description,
            test_type=test_type,
            question_count=question_count,
            difficulty=difficulty,
        )
        
        self._save_test(test)
        
        # Workspace'e ekle
        workspace = self.get_workspace(workspace_id)
        if workspace:
            workspace.tests.append(test.id)
            self.update_workspace(workspace)
        
        return test
    
    def get_test(self, test_id: str) -> Optional[Test]:
        """Testi getir."""
        file_path = self.tests_dir / f"{test_id}.json"
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Test.from_dict(data)
        except Exception as e:
            print(f"Test yükleme hatası: {e}")
            return None
    
    def list_tests(self, workspace_id: str) -> List[Test]:
        """Çalışma ortamındaki testleri listele."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return []
        
        tests = []
        for test_id in workspace.tests:
            test = self.get_test(test_id)
            if test:
                tests.append(test)
        
        tests.sort(key=lambda x: x.created_at, reverse=True)
        return tests
    
    def update_test(self, test: Test) -> Test:
        """Testi güncelle."""
        self._save_test(test)
        return test
    
    def submit_test_answer(self, test_id: str, question_id: str, answer: str) -> bool:
        """Test cevabını kaydet."""
        test = self.get_test(test_id)
        if not test:
            return False
        
        test.user_answers[question_id] = answer
        
        if test.status == TestStatus.NOT_STARTED:
            test.status = TestStatus.IN_PROGRESS
            test.started_at = datetime.now().isoformat()
        
        self.update_test(test)
        return True
    
    def complete_test(self, test_id: str) -> Optional[Dict]:
        """Testi tamamla ve sonuçları hesapla."""
        test = self.get_test(test_id)
        if not test:
            return None
        
        # Puanlama
        correct = 0
        total = len(test.questions)
        
        for question in test.questions:
            q_id = question.get('id')
            user_answer = test.user_answers.get(q_id, '')
            correct_answer = question.get('correct_answer', '')
            
            if user_answer.strip().lower() == correct_answer.strip().lower():
                correct += 1
        
        test.score = (correct / total * 100) if total > 0 else 0
        test.status = TestStatus.COMPLETED
        test.completed_at = datetime.now().isoformat()
        
        self.update_test(test)
        
        return {
            "score": test.score,
            "correct": correct,
            "total": total,
            "feedback": test.feedback
        }
    
    def _save_test(self, test: Test):
        """Testi kaydet."""
        file_path = self.tests_dir / f"{test.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test.to_dict(), f, ensure_ascii=False, indent=2)
    
    # ==================== CHAT OPERATIONS ====================
    
    def add_chat_message(
        self,
        workspace_id: str,
        role: str,
        content: str,
        sources: List[str] = None
    ):
        """Çalışma ortamına chat mesajı ekle."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return
        
        message = {
            "role": role,
            "content": content,
            "sources": sources or [],
            "timestamp": datetime.now().isoformat()
        }
        
        workspace.chat_history.append(message)
        
        # Son 100 mesajı tut
        if len(workspace.chat_history) > 100:
            workspace.chat_history = workspace.chat_history[-100:]
        
        self.update_workspace(workspace)
    
    def get_chat_history(self, workspace_id: str, limit: int = 50) -> List[Dict]:
        """Chat geçmişini getir."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return []
        
        return workspace.chat_history[-limit:]
    
    # ==================== STATS ====================
    
    def get_workspace_stats(self, workspace_id: str) -> Dict:
        """Çalışma ortamı istatistikleri."""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return {}
        
        documents = self.list_documents(workspace_id)
        tests = self.list_tests(workspace_id)
        
        completed_tests = [t for t in tests if t.status == TestStatus.COMPLETED]
        avg_score = sum(t.score or 0 for t in completed_tests) / len(completed_tests) if completed_tests else 0
        
        return {
            "workspace_id": workspace_id,
            "name": workspace.name,
            "active_sources_count": len(workspace.active_sources),
            "documents_count": len(documents),
            "tests_count": len(tests),
            "completed_tests": len(completed_tests),
            "average_score": round(avg_score, 1),
            "chat_messages": len(workspace.chat_history),
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at,
        }


# Singleton instance
learning_workspace_manager = LearningWorkspaceManager()
