"""
Enterprise AI Assistant - RAG Tool
Endüstri Standartlarında Kurumsal AI Çözümü

RAG arama tool'u - bilgi tabanında semantic search.
"""

from typing import Dict, Any, Optional, List

from .base_tool import BaseTool, ToolResult

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.retriever import retriever
from core.vector_store import vector_store


class RAGTool(BaseTool):
    """
    RAG Arama Tool'u - Endüstri standartlarına uygun.
    
    Yetenekler:
    - Semantic search
    - Metadata filtering
    - Multi-query search
    """
    
    def __init__(self):
        super().__init__(
            name="rag_search",
            description="Şirket bilgi tabanında semantic arama yapar. Dökümanlardan ilgili bilgileri bulur.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Arama sorgusu",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Döndürülecek sonuç sayısı",
                        "default": 5,
                    },
                    "filter_metadata": {
                        "type": "object",
                        "description": "Metadata filtresi",
                    },
                },
                "required": ["query"],
            },
        )
    
    def execute(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> ToolResult:
        """
        RAG araması yap.
        
        Args:
            query: Arama sorgusu
            top_k: Sonuç sayısı
            filter_metadata: Metadata filtresi
            
        Returns:
            ToolResult
        """
        try:
            results = retriever.retrieve(
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )
            
            if not results:
                return ToolResult(
                    success=True,
                    data=[],
                    metadata={"message": "Sonuç bulunamadı", "query": query},
                )
            
            formatted_results = [
                {
                    "content": r.content,
                    "source": r.source,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in results
            ]
            
            return ToolResult(
                success=True,
                data=formatted_results,
                metadata={
                    "query": query,
                    "result_count": len(results),
                    "top_score": results[0].score if results else 0,
                },
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"query": query},
            )
    
    def search_with_context(
        self,
        query: str,
        max_context_length: int = 4000,
    ) -> str:
        """Context string olarak arama sonuçları döndür."""
        return retriever.retrieve_with_context(
            query=query,
            max_context_length=max_context_length,
        )
    
    def get_sources(self, query: str) -> List[str]:
        """Sadece kaynak listesi döndür."""
        return retriever.get_sources(query)


# Singleton instance
rag_tool = RAGTool()
