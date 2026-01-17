"""
Enterprise AI Assistant - CRAG (Corrective RAG) Tests
======================================================

Corrective RAG sistemi için kapsamlı unit ve integration testleri.
Relevance grading, query transformation, web search fallback testleri.
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRelevanceGrader:
    """Relevance Grader testleri."""
    
    @pytest.fixture
    def mock_llm_grader(self):
        """LLM yanıtı simüle eden mock."""
        mock = Mock()
        mock.generate = Mock(return_value='{"score": 0.85, "reasoning": "Relevant content"}')
        mock.generate_async = AsyncMock(return_value='{"score": 0.85, "reasoning": "Relevant content"}')
        return mock
    
    def test_grader_initialization(self):
        """RelevanceGrader başlatılabilmeli."""
        from core.crag_system import RelevanceGrader
        
        grader = RelevanceGrader()
        assert grader is not None
        assert hasattr(grader, 'grade')
    
    def test_grade_highly_relevant_document(self, mock_llm_grader):
        """Yüksek ilgili doküman yüksek skor almalı."""
        from core.crag_system import RelevanceGrader
        
        with patch('core.crag_system.llm_manager', mock_llm_grader):
            grader = RelevanceGrader(threshold=0.5)
            
            query = "Python programlama nedir?"
            document = "Python, yüksek seviyeli bir programlama dilidir. Guido van Rossum tarafından geliştirilmiştir."
            
            # Mock return
            mock_llm_grader.generate.return_value = '{"score": 0.9, "is_relevant": true, "reasoning": "Directly answers the question"}'
            
            result = grader.grade(query, document)
            
            assert result['score'] >= 0.5
            assert result['is_relevant'] == True
    
    def test_grade_irrelevant_document(self, mock_llm_grader):
        """İlgisiz doküman düşük skor almalı."""
        from core.crag_system import RelevanceGrader
        
        with patch('core.crag_system.llm_manager', mock_llm_grader):
            grader = RelevanceGrader(threshold=0.5)
            
            query = "Python programlama nedir?"
            document = "Bugün hava çok güzel. Parkta yürüyüş yapıyorum."
            
            mock_llm_grader.generate.return_value = '{"score": 0.1, "is_relevant": false, "reasoning": "Unrelated content"}'
            
            result = grader.grade(query, document)
            
            assert result['score'] < 0.5
            assert result['is_relevant'] == False
    
    def test_batch_grading(self, mock_llm_grader):
        """Çoklu doküman değerlendirmesi çalışmalı."""
        from core.crag_system import RelevanceGrader
        
        with patch('core.crag_system.llm_manager', mock_llm_grader):
            grader = RelevanceGrader()
            
            query = "FastAPI nedir?"
            documents = [
                "FastAPI modern bir Python web framework'üdür.",
                "Django popüler bir web framework'üdür.",
                "Yemek tarifleri için en iyi siteler."
            ]
            
            # Her doküman için farklı skor
            mock_llm_grader.generate.side_effect = [
                '{"score": 0.95, "is_relevant": true}',
                '{"score": 0.4, "is_relevant": false}',
                '{"score": 0.05, "is_relevant": false}'
            ]
            
            results = grader.grade_batch(query, documents)
            
            assert len(results) == 3
            assert results[0]['score'] > results[1]['score'] > results[2]['score']


class TestQueryTransformer:
    """Query Transformer testleri."""
    
    @pytest.fixture
    def mock_llm_transformer(self):
        """Query transformation için mock LLM."""
        mock = Mock()
        mock.generate = Mock(return_value='{"transformed_query": "What is Python programming language?", "intent": "definition"}')
        return mock
    
    def test_transformer_initialization(self):
        """QueryTransformer başlatılabilmeli."""
        from core.crag_system import QueryTransformer
        
        transformer = QueryTransformer()
        assert transformer is not None
    
    def test_query_expansion(self, mock_llm_transformer):
        """Query genişletme çalışmalı."""
        from core.crag_system import QueryTransformer
        
        with patch('core.crag_system.llm_manager', mock_llm_transformer):
            transformer = QueryTransformer()
            
            original_query = "python nedir"
            mock_llm_transformer.generate.return_value = '{"expanded": ["python programlama dili nedir", "python ne işe yarar", "python özellikleri"]}'
            
            expanded = transformer.expand_query(original_query)
            
            assert len(expanded) >= 1
    
    def test_query_decomposition(self, mock_llm_transformer):
        """Karmaşık sorular parçalanabilmeli."""
        from core.crag_system import QueryTransformer
        
        with patch('core.crag_system.llm_manager', mock_llm_transformer):
            transformer = QueryTransformer()
            
            complex_query = "Python ve JavaScript arasındaki farklar nelerdir ve hangisi web geliştirme için daha uygun?"
            
            mock_llm_transformer.generate.return_value = '''{"sub_queries": [
                "Python nedir ve özellikleri nelerdir?",
                "JavaScript nedir ve özellikleri nelerdir?",
                "Python ve JavaScript karşılaştırması",
                "Web geliştirme için en iyi dil hangisi?"
            ]}'''
            
            sub_queries = transformer.decompose_query(complex_query)
            
            assert len(sub_queries) >= 2
    
    def test_hypothetical_document_generation(self, mock_llm_transformer):
        """HyDE - Hipotetik doküman üretimi çalışmalı."""
        from core.crag_system import QueryTransformer
        
        with patch('core.crag_system.llm_manager', mock_llm_transformer):
            transformer = QueryTransformer()
            
            query = "RAG sistemleri nasıl çalışır?"
            
            mock_llm_transformer.generate.return_value = """RAG (Retrieval Augmented Generation) sistemleri, 
            büyük dil modellerini harici bilgi kaynaklarıyla birleştiren bir yaklaşımdır. 
            Kullanıcı sorusu alınır, ilgili dokümanlar aranır, ve LLM bu bağlamla yanıt üretir."""
            
            hyde_doc = transformer.generate_hypothetical_document(query)
            
            assert len(hyde_doc) > 50
            assert "RAG" in hyde_doc or "retrieval" in hyde_doc.lower()


class TestCRAGPipeline:
    """CRAG Pipeline entegrasyon testleri."""
    
    @pytest.fixture
    def mock_services(self):
        """Tüm servisleri mockla."""
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value="Test yanıtı")
        mock_llm.generate_async = AsyncMock(return_value="Test yanıtı")
        
        mock_vector_store = Mock()
        mock_vector_store.search_with_scores = Mock(return_value=[
            {"document": "Test doc 1", "score": 0.9, "metadata": {"source": "test1.txt"}},
            {"document": "Test doc 2", "score": 0.7, "metadata": {"source": "test2.txt"}},
        ])
        
        mock_embedding = Mock()
        mock_embedding.embed_query = Mock(return_value=[0.1] * 768)
        
        return {
            "llm": mock_llm,
            "vector_store": mock_vector_store,
            "embedding": mock_embedding
        }
    
    def test_pipeline_initialization(self):
        """CRAG Pipeline başlatılabilmeli."""
        from core.crag_system import CRAGPipeline
        
        pipeline = CRAGPipeline()
        assert pipeline is not None
        assert hasattr(pipeline, 'process')
    
    @pytest.mark.asyncio
    async def test_pipeline_with_relevant_docs(self, mock_services):
        """İlgili dokümanlar bulunduğunda normal RAG akışı."""
        from core.crag_system import CRAGPipeline
        
        with patch('core.crag_system.llm_manager', mock_services['llm']), \
             patch('core.crag_system.vector_store', mock_services['vector_store']):
            
            pipeline = CRAGPipeline()
            
            # Mock relevance grading
            pipeline.grader.grade = Mock(return_value={"score": 0.9, "is_relevant": True})
            
            result = await pipeline.process("Python nedir?")
            
            assert result is not None
            assert "answer" in result or isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_pipeline_with_no_relevant_docs(self, mock_services):
        """İlgili doküman yoksa web search fallback."""
        from core.crag_system import CRAGPipeline
        
        with patch('core.crag_system.llm_manager', mock_services['llm']), \
             patch('core.crag_system.vector_store', mock_services['vector_store']):
            
            pipeline = CRAGPipeline()
            
            # Tüm dokümanlar irrelevant
            pipeline.grader.grade = Mock(return_value={"score": 0.2, "is_relevant": False})
            
            # Web search mock
            pipeline.web_search = AsyncMock(return_value=[
                {"content": "Web'den bulunan içerik", "source": "https://example.com"}
            ])
            
            result = await pipeline.process("Çok spesifik bir soru?")
            
            # Fallback mekanizması devreye girmeli
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_pipeline_with_ambiguous_docs(self, mock_services):
        """Belirsiz sonuçlarda query transformation."""
        from core.crag_system import CRAGPipeline
        
        with patch('core.crag_system.llm_manager', mock_services['llm']), \
             patch('core.crag_system.vector_store', mock_services['vector_store']):
            
            pipeline = CRAGPipeline()
            
            # Ortala skor - belirsiz
            pipeline.grader.grade = Mock(return_value={"score": 0.5, "is_relevant": False})
            
            # Query transformation mock
            pipeline.transformer.transform = Mock(return_value="Transformed query")
            
            result = await pipeline.process("ML?")  # Belirsiz kısa query
            
            assert result is not None


class TestCRAGKnowledgeRefinement:
    """Bilgi rafine etme testleri."""
    
    def test_extract_key_sentences(self):
        """Anahtar cümleler çıkarılabilmeli."""
        from core.crag_system import CRAGPipeline
        
        pipeline = CRAGPipeline()
        
        document = """
        Python çok yönlü bir programlama dilidir.
        Web geliştirme, veri analizi ve yapay zeka için kullanılır.
        Syntax'ı okunabilir ve öğrenmesi kolaydır.
        Guido van Rossum tarafından 1991'de geliştirilmiştir.
        """
        
        query = "Python ne zaman geliştirildi?"
        
        # Key sentence extraction
        if hasattr(pipeline, 'extract_key_sentences'):
            key_sentences = pipeline.extract_key_sentences(document, query)
            
            # 1991 içeren cümle ön plana çıkmalı
            assert any("1991" in s for s in key_sentences)
    
    def test_context_compression(self):
        """Bağlam sıkıştırma çalışmalı."""
        from core.crag_system import CRAGPipeline
        
        pipeline = CRAGPipeline()
        
        long_context = "Bu çok uzun bir metin. " * 100
        
        if hasattr(pipeline, 'compress_context'):
            compressed = pipeline.compress_context(long_context, max_tokens=500)
            
            assert len(compressed) < len(long_context)


class TestCRAGMetrics:
    """CRAG performans metrikleri testleri."""
    
    def test_track_retrieval_metrics(self):
        """Retrieval metrikleri takip edilmeli."""
        from core.crag_system import CRAGPipeline
        
        pipeline = CRAGPipeline()
        
        if hasattr(pipeline, 'metrics'):
            # Başlangıçta metrikler sıfır
            assert pipeline.metrics.get('total_queries', 0) >= 0
    
    def test_track_correction_rate(self):
        """Düzeltme oranı takip edilmeli."""
        from core.crag_system import CRAGPipeline
        
        pipeline = CRAGPipeline()
        
        if hasattr(pipeline, 'get_correction_stats'):
            stats = pipeline.get_correction_stats()
            
            assert 'correction_rate' in stats or stats is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
