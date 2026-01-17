"""
Enterprise AI Assistant - Test Generator Tests
===============================================

Test sorusu oluşturma sistemi için kapsamlı testler.
Question generation, grading, explanation testleri.
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


class TestTestGeneratorBasics:
    """TestGenerator temel testleri."""
    
    def test_import(self):
        """TestGenerator import edilebilmeli."""
        from core.test_generator import test_generator
        
        assert test_generator is not None
    
    def test_singleton(self):
        """TestGenerator singleton olmalı."""
        from core.test_generator import test_generator as tg1
        from core.test_generator import test_generator as tg2
        
        assert tg1 is tg2
    
    def test_has_question_templates(self):
        """Question templates tanımlı olmalı."""
        from core.test_generator import TestGenerator
        
        assert hasattr(TestGenerator, 'QUESTION_TEMPLATES')
        assert len(TestGenerator.QUESTION_TEMPLATES) > 0
    
    def test_has_difficulty_levels(self):
        """Difficulty levels tanımlı olmalı."""
        from core.test_generator import TestGenerator
        
        assert hasattr(TestGenerator, 'DIFFICULTY_LEVELS')
        assert len(TestGenerator.DIFFICULTY_LEVELS) > 0


class TestAvailableTypes:
    """Test türleri testleri."""
    
    def test_get_available_types(self):
        """Test türleri alınabilmeli."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert types is not None
        assert len(types) > 0
    
    def test_multiple_choice_type(self):
        """Multiple choice tipi mevcut olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert "multiple_choice" in types
    
    def test_true_false_type(self):
        """True/false tipi mevcut olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert "true_false" in types
    
    def test_fill_blank_type(self):
        """Fill blank tipi mevcut olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert "fill_blank" in types
    
    def test_short_answer_type(self):
        """Short answer tipi mevcut olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert "short_answer" in types
    
    def test_mixed_type(self):
        """Mixed tipi mevcut olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        assert "mixed" in types
    
    def test_type_has_name(self):
        """Her tipin adı olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        for type_key, type_info in types.items():
            assert "name" in type_info, f"{type_key} tipi name içermeli"
    
    def test_type_has_description(self):
        """Her tipin açıklaması olmalı."""
        from core.test_generator import test_generator
        
        types = test_generator.get_available_types()
        
        for type_key, type_info in types.items():
            assert "description" in type_info, f"{type_key} tipi description içermeli"


class TestDifficultyLevels:
    """Zorluk seviyeleri testleri."""
    
    def test_get_difficulty_levels(self):
        """Zorluk seviyeleri alınabilmeli."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        assert levels is not None
        assert len(levels) > 0
    
    def test_easy_level(self):
        """Easy seviyesi mevcut olmalı."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        assert "easy" in levels
    
    def test_medium_level(self):
        """Medium seviyesi mevcut olmalı."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        assert "medium" in levels
    
    def test_hard_level(self):
        """Hard seviyesi mevcut olmalı."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        assert "hard" in levels
    
    def test_mixed_level(self):
        """Mixed seviyesi mevcut olmalı."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        assert "mixed" in levels
    
    def test_level_has_name(self):
        """Her seviyenin adı olmalı."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        for level_key, level_info in levels.items():
            assert "name" in level_info, f"{level_key} seviyesi name içermeli"
    
    def test_level_has_complexity(self):
        """Her seviyenin complexity açıklaması olmalı."""
        from core.test_generator import test_generator
        
        levels = test_generator.get_difficulty_levels()
        
        for level_key, level_info in levels.items():
            assert "complexity" in level_info, f"{level_key} seviyesi complexity içermeli"


class TestTestQuestion:
    """TestQuestion model testleri."""
    
    def test_test_question_model(self):
        """TestQuestion model mevcut olmalı."""
        from core.learning_workspace import TestQuestion
        
        assert TestQuestion is not None
    
    def test_create_test_question(self):
        """TestQuestion oluşturulabilmeli."""
        from core.learning_workspace import TestQuestion, TestType
        
        question = TestQuestion(
            id="q-1",
            question="Python nedir?",
            question_type=TestType.MULTIPLE_CHOICE,
            options=["A) Yılan", "B) Programlama dili", "C) Oyun", "D) Renk"],
            correct_answer="B",
            explanation="Python bir programlama dilidir.",
            difficulty="easy"
        )
        
        assert question.id == "q-1"
        assert question.question == "Python nedir?"
        assert question.correct_answer == "B"
    
    def test_test_question_to_dict(self):
        """TestQuestion dict'e dönüştürülebilmeli."""
        from core.learning_workspace import TestQuestion, TestType
        
        question = TestQuestion(
            id="q-1",
            question="Test",
            question_type=TestType.TRUE_FALSE,
            options=["Doğru", "Yanlış"],
            correct_answer="Doğru",
            explanation="Açıklama",
            difficulty="medium"
        )
        
        d = question.to_dict()
        
        assert d["id"] == "q-1"
        assert d["question"] == "Test"
        assert d["correct_answer"] == "Doğru"


class TestAnswerGrading:
    """Cevap değerlendirme testleri."""
    
    @pytest.mark.asyncio
    async def test_grade_multiple_choice_correct(self):
        """Doğru çoktan seçmeli cevap doğru değerlendirilmeli."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = [
                {
                    "id": "q-1",
                    "question": "Test soru?",
                    "question_type": TestType.MULTIPLE_CHOICE.value,
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "B",
                    "explanation": "Açıklama"
                }
            ]
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.grade_answer("test-id", "q-1", "B")
            
            assert result["is_correct"] is True
            assert result["score"] == 100
    
    @pytest.mark.asyncio
    async def test_grade_multiple_choice_wrong(self):
        """Yanlış çoktan seçmeli cevap yanlış değerlendirilmeli."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = [
                {
                    "id": "q-1",
                    "question": "Test soru?",
                    "question_type": TestType.MULTIPLE_CHOICE.value,
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "B",
                    "explanation": "Açıklama"
                }
            ]
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.grade_answer("test-id", "q-1", "A")
            
            assert result["is_correct"] is False
            assert result["score"] == 0
    
    @pytest.mark.asyncio
    async def test_grade_true_false_correct(self):
        """Doğru D/Y cevabı doğru değerlendirilmeli."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = [
                {
                    "id": "q-1",
                    "question": "Python bir dildir.",
                    "question_type": TestType.TRUE_FALSE.value,
                    "options": ["Doğru", "Yanlış"],
                    "correct_answer": "DOĞRU",
                    "explanation": "Açıklama"
                }
            ]
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.grade_answer("test-id", "q-1", "doğru")
            
            assert result["is_correct"] is True
    
    @pytest.mark.asyncio
    async def test_grade_fill_blank_correct(self):
        """Doğru boşluk doldurma doğru değerlendirilmeli."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = [
                {
                    "id": "q-1",
                    "question": "Python bir ___ dilidir.",
                    "question_type": TestType.FILL_BLANK.value,
                    "options": [],
                    "correct_answer": "programlama",
                    "explanation": "Açıklama"
                }
            ]
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.grade_answer("test-id", "q-1", "programlama")
            
            assert result["is_correct"] is True
    
    @pytest.mark.asyncio
    async def test_grade_case_insensitive(self):
        """Değerlendirme büyük/küçük harf duyarsız olmalı."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = [
                {
                    "id": "q-1",
                    "question": "Test?",
                    "question_type": TestType.MULTIPLE_CHOICE.value,
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "B",
                    "explanation": "Açıklama"
                }
            ]
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.grade_answer("test-id", "q-1", "b")
            
            assert result["is_correct"] is True
    
    @pytest.mark.asyncio
    async def test_grade_nonexistent_test(self):
        """Olmayan test için hata dönmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_manager.get_test.return_value = None
            
            result = await test_generator.grade_answer("nonexistent", "q-1", "A")
            
            assert result["is_correct"] is False
            assert "bulunamadı" in result["feedback"]
    
    @pytest.mark.asyncio
    async def test_grade_nonexistent_question(self):
        """Olmayan soru için hata dönmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = []
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.grade_answer("test-id", "nonexistent", "A")
            
            assert result["is_correct"] is False


class TestQuestionExplanation:
    """Soru açıklama testleri."""
    
    @pytest.mark.asyncio
    async def test_explain_question(self):
        """Soru açıklaması alınabilmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = [
                {
                    "id": "q-1",
                    "question": "Python nedir?",
                    "options": ["A) Yılan", "B) Dil", "C) Oyun", "D) Renk"],
                    "correct_answer": "B",
                    "explanation": "Python bir programlama dilidir."
                }
            ]
            mock_manager.get_test.return_value = mock_test
            
            with patch('core.test_generator.llm_manager') as mock_llm:
                mock_llm.generate.return_value = "Python, Guido van Rossum tarafından geliştirilmiş bir dildir."
                
                result = await test_generator.explain_question(
                    "test-id", 
                    "q-1", 
                    "Neden B doğru?"
                )
                
                assert result is not None
                assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_explain_nonexistent_test(self):
        """Olmayan test için açıklama hata dönmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_manager.get_test.return_value = None
            
            result = await test_generator.explain_question("nonexistent", "q-1", "Soru?")
            
            assert "bulunamadı" in result
    
    @pytest.mark.asyncio
    async def test_explain_nonexistent_question(self):
        """Olmayan soru için açıklama hata dönmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.questions = []
            mock_manager.get_test.return_value = mock_test
            
            result = await test_generator.explain_question("test-id", "nonexistent", "Soru?")
            
            assert "bulunamadı" in result


class TestTestSummary:
    """Test özeti testleri."""
    
    def test_get_test_summary(self):
        """Test özeti alınabilmeli."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType, TestStatus
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.id = "test-123"
            mock_test.title = "Python Quiz"
            mock_test.description = "Temel Python testi"
            mock_test.test_type = TestType.MULTIPLE_CHOICE
            mock_test.questions = [{"id": "q1"}, {"id": "q2"}]
            mock_test.difficulty = "medium"
            mock_test.status = TestStatus.COMPLETED
            mock_test.score = 80
            mock_test.created_at = "2024-01-01"
            mock_test.completed_at = "2024-01-02"
            mock_manager.get_test.return_value = mock_test
            
            summary = test_generator.get_test_summary("test-123")
            
            assert summary["id"] == "test-123"
            assert summary["title"] == "Python Quiz"
            assert summary["question_count"] == 2
            assert summary["score"] == 80
    
    def test_get_test_summary_nonexistent(self):
        """Olmayan test için boş özet dönmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_manager.get_test.return_value = None
            
            summary = test_generator.get_test_summary("nonexistent")
            
            assert summary == {}


class TestTestGeneration:
    """Test üretimi testleri."""
    
    @pytest.mark.asyncio
    async def test_generate_test_nonexistent(self):
        """Olmayan test için hata event'i dönmeli."""
        from core.test_generator import test_generator
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_manager.get_test.return_value = None
            
            events = []
            async for event in test_generator.generate_test("nonexistent"):
                events.append(event)
            
            assert len(events) > 0
            assert events[0]["type"] == "error"
    
    @pytest.mark.asyncio
    async def test_generate_test_yields_status(self):
        """Test üretimi status event'leri yield etmeli."""
        from core.test_generator import test_generator
        from core.learning_workspace import TestType, TestStatus
        
        with patch.object(test_generator, 'manager') as mock_manager:
            mock_test = MagicMock()
            mock_test.id = "test-123"
            mock_test.workspace_id = "ws-123"
            mock_test.test_type = TestType.MULTIPLE_CHOICE
            mock_test.question_count = 2
            mock_test.difficulty = "easy"
            mock_test.questions = []
            mock_manager.get_test.return_value = mock_test
            
            mock_workspace = MagicMock()
            mock_workspace.topic = "Python"
            mock_manager.get_workspace.return_value = mock_workspace
            
            with patch('core.test_generator.vector_store') as mock_vs:
                mock_vs.search_with_scores.return_value = []
                
                with patch('core.test_generator.llm_manager') as mock_llm:
                    mock_llm.generate.return_value = json.dumps([
                        {
                            "question": "Soru 1?",
                            "question_type": "multiple_choice",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "A",
                            "explanation": "Açıklama",
                            "difficulty": "easy"
                        },
                        {
                            "question": "Soru 2?",
                            "question_type": "multiple_choice",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": "B",
                            "explanation": "Açıklama",
                            "difficulty": "easy"
                        }
                    ])
                    
                    events = []
                    async for event in test_generator.generate_test("test-123"):
                        events.append(event)
                    
                    # En az status ve complete event'leri olmalı
                    event_types = [e["type"] for e in events]
                    
                    assert "status" in event_types


class TestQuestionTemplates:
    """Question template testleri."""
    
    def test_multiple_choice_template(self):
        """Multiple choice template doğru olmalı."""
        from core.test_generator import TestGenerator
        from core.learning_workspace import TestType
        
        template = TestGenerator.QUESTION_TEMPLATES[TestType.MULTIPLE_CHOICE]
        
        assert template["option_count"] == 4
        assert "Çoktan" in template["name"]
    
    def test_true_false_template(self):
        """True/false template doğru olmalı."""
        from core.test_generator import TestGenerator
        from core.learning_workspace import TestType
        
        template = TestGenerator.QUESTION_TEMPLATES[TestType.TRUE_FALSE]
        
        assert template["option_count"] == 2
    
    def test_fill_blank_template(self):
        """Fill blank template doğru olmalı."""
        from core.test_generator import TestGenerator
        from core.learning_workspace import TestType
        
        template = TestGenerator.QUESTION_TEMPLATES[TestType.FILL_BLANK]
        
        assert template["option_count"] == 0
    
    def test_short_answer_template(self):
        """Short answer template doğru olmalı."""
        from core.test_generator import TestGenerator
        from core.learning_workspace import TestType
        
        template = TestGenerator.QUESTION_TEMPLATES[TestType.SHORT_ANSWER]
        
        assert template["option_count"] == 0


class TestSourceGathering:
    """Kaynak toplama testleri."""
    
    @pytest.mark.asyncio
    async def test_gather_sources(self):
        """Kaynaklar toplanabilmeli."""
        from core.test_generator import test_generator
        
        with patch('core.test_generator.vector_store') as mock_vs:
            mock_vs.search_with_scores.return_value = [
                {
                    "document": "Python içerik",
                    "metadata": {
                        "document_id": "doc-1",
                        "filename": "python.pdf"
                    }
                }
            ]
            
            sources = await test_generator._gather_sources("Python", [])
            
            assert len(sources) > 0
            assert "content" in sources[0]
    
    @pytest.mark.asyncio
    async def test_gather_sources_empty(self):
        """Kaynak yoksa boş liste dönmeli."""
        from core.test_generator import test_generator
        
        with patch('core.test_generator.vector_store') as mock_vs:
            mock_vs.search_with_scores.return_value = []
            
            sources = await test_generator._gather_sources("Bilinmeyen", [])
            
            assert sources == []
    
    @pytest.mark.asyncio
    async def test_gather_sources_filters_by_active(self):
        """Sadece aktif kaynaklar alınmalı."""
        from core.test_generator import test_generator
        
        with patch('core.test_generator.vector_store') as mock_vs:
            mock_vs.search_with_scores.return_value = [
                {
                    "document": "Aktif kaynak",
                    "metadata": {
                        "document_id": "active-doc",
                        "filename": "active.pdf"
                    }
                },
                {
                    "document": "Pasif kaynak",
                    "metadata": {
                        "document_id": "passive-doc",
                        "filename": "passive.pdf"
                    }
                }
            ]
            
            sources = await test_generator._gather_sources("Test", ["active-doc"])
            
            # Sadece aktif kaynak gelmeli
            assert len(sources) == 1
            assert sources[0]["source_id"] == "active-doc"
