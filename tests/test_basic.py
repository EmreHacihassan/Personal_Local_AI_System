"""
Enterprise AI Assistant - Test Suite
Endüstri Standartlarında Kurumsal AI Çözümü

Temel testler - Core, RAG, Agents.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestConfig:
    """Config testleri."""
    
    def test_settings_load(self):
        """Settings yüklenmeli."""
        from core.config import settings
        
        assert settings is not None
        assert settings.CHUNK_SIZE > 0
        assert settings.CHUNK_OVERLAP >= 0
    
    def test_directories_exist(self):
        """Gerekli klasörler oluşturulmalı."""
        from core.config import settings
        
        settings.ensure_directories()
        
        assert settings.DATA_DIR.exists()
        assert settings.LOGS_DIR.exists()


class TestDocumentLoader:
    """Document loader testleri."""
    
    def test_supported_extensions(self):
        """Desteklenen uzantılar tanımlı olmalı."""
        from rag.document_loader import DocumentLoader
        
        loader = DocumentLoader()
        
        assert ".pdf" in loader.SUPPORTED_EXTENSIONS
        assert ".docx" in loader.SUPPORTED_EXTENSIONS
        assert ".txt" in loader.SUPPORTED_EXTENSIONS
    
    def test_load_text_file(self, tmp_path):
        """Text dosyası yüklenebilmeli."""
        from rag.document_loader import DocumentLoader
        
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Bu bir test dökümanıdır.")
        
        loader = DocumentLoader()
        docs = loader.load_file(str(test_file))
        
        assert len(docs) > 0
        assert "test dökümanı" in docs[0].content


class TestChunker:
    """Chunker testleri."""
    
    def test_chunk_text(self):
        """Metin parçalanabilmeli."""
        from rag.chunker import DocumentChunker
        
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        text = "Bu bir test metnidir. " * 50
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.content) <= 150  # Some tolerance
    
    def test_chunk_with_metadata(self):
        """Metadata korunmalı."""
        from rag.chunker import DocumentChunker
        
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        text = "Kısa bir test metni."
        metadata = {"source": "test.txt", "author": "test"}
        
        chunks = chunker.chunk_text(text, metadata)
        
        assert len(chunks) > 0
        assert chunks[0].metadata.get("source") == "test.txt"


class TestAgents:
    """Agent testleri."""
    
    def test_orchestrator_init(self):
        """Orchestrator başlatılabilmeli."""
        from agents.orchestrator import Orchestrator
        
        orch = Orchestrator()
        
        assert orch.name == "Orchestrator"
        assert len(orch.agents) == 4
    
    def test_agent_roles(self):
        """Agent rolleri doğru tanımlanmalı."""
        from agents.base_agent import AgentRole
        
        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.RESEARCH.value == "research"
        assert AgentRole.WRITER.value == "writer"
        assert AgentRole.ANALYZER.value == "analyzer"
        assert AgentRole.ASSISTANT.value == "assistant"


class TestTools:
    """Tool testleri."""
    
    def test_rag_tool_schema(self):
        """RAG tool şeması doğru olmalı."""
        from tools.rag_tool import RAGTool
        
        tool = RAGTool()
        schema = tool.get_schema()
        
        assert schema["name"] == "rag_search"
        assert "query" in schema["parameters"]["properties"]
    
    def test_file_tool_operations(self):
        """File tool operasyonları tanımlı olmalı."""
        from tools.file_tool import FileTool
        
        tool = FileTool()
        schema = tool.get_schema()
        
        operations = schema["parameters"]["properties"]["operation"]["enum"]
        
        assert "read" in operations
        assert "write" in operations
        assert "list" in operations
        assert "search" in operations


# ============ INTEGRATION TESTS ============

class TestIntegration:
    """Entegrasyon testleri (Ollama gerektirir)."""
    
    @pytest.mark.skipif(
        not pytest.importorskip("ollama", reason="Ollama not installed"),
        reason="Ollama not available"
    )
    def test_llm_connection(self):
        """LLM bağlantısı test edilmeli."""
        from core.llm_manager import LLMManager
        
        llm = LLMManager()
        status = llm.get_status()
        
        # At least check structure
        assert "primary_model" in status
        assert "base_url" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
