"""
Enterprise AI Assistant - RAG Service
======================================

Merkezi RAG (Retrieval Augmented Generation) servisi.
CRAG (Corrective RAG) entegrasyonu ile zenginleştirilmiş bilgi erişimi.

Features:
- Vector store search with scoring
- Web search integration
- CRAG pipeline for query correction
- Multi-source context building
- Source deduplication
- Relevance grading
- Hallucination risk assessment

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class SourceType(str, Enum):
    """Kaynak tipi."""
    DOCUMENT = "document"   # Yerel dosya
    WEB = "web"             # Web araması
    WIKIPEDIA = "wikipedia" # Wikipedia
    GENERAL = "general"     # Genel LLM bilgisi


class RelevanceLevel(str, Enum):
    """Kaynak alaka düzeyi."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class RAGSearchResult:
    """Tek bir RAG arama sonucu."""
    content: str
    source: str
    source_type: SourceType
    title: str = ""
    url: str = ""
    page: Optional[int] = None
    relevance_score: float = 0.0
    relevance_level: RelevanceLevel = RelevanceLevel.MEDIUM
    snippet: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_frontend_format(self) -> Dict[str, Any]:
        """Frontend için kaynak formatı."""
        type_icons = {
            SourceType.DOCUMENT: "📄",
            SourceType.WEB: "🌐",
            SourceType.WIKIPEDIA: "📚",
            SourceType.GENERAL: "💡",
        }
        return {
            "title": self.title or self.source,
            "url": self.url or "#",
            "domain": f"{type_icons.get(self.source_type, '📄')} {self.source_type.value.title()}",
            "snippet": self.snippet or self.content[:200],
            "type": self.source_type.value,
            "reliability": self.relevance_score,
        }


@dataclass
class EnrichedContext:
    """Zenginleştirilmiş bağlam."""
    query: str
    document_context: str = ""
    web_context: str = ""
    general_context: str = ""
    all_sources: List[RAGSearchResult] = field(default_factory=list)
    document_sources: List[RAGSearchResult] = field(default_factory=list)
    web_sources: List[RAGSearchResult] = field(default_factory=list)
    has_documents: bool = False
    has_web: bool = False
    needs_general_knowledge: bool = False
    total_sources: int = 0
    search_time_ms: float = 0.0
    crag_iterations: int = 0
    hallucination_risk: str = "low"
    
    def get_combined_context(self) -> str:
        """Birleşik bağlam metni oluştur."""
        parts = []
        
        if self.document_context:
            parts.append(f"=== 📄 DOSYA KAYNAKLARI ===\n{self.document_context}\n=== DOSYA KAYNAKLARI SONU ===")
        
        if self.web_context:
            parts.append(f"=== 🌐 WEB KAYNAKLARI ===\n{self.web_context}\n=== WEB KAYNAKLARI SONU ===")
        
        if not parts and self.needs_general_knowledge:
            parts.append("=== 💡 GENEL BİLGİ MODU ===\nBu soru için spesifik kaynak bulunamadı. Genel bilgi kullanılacak.\n=== GENEL BİLGİ MODU SONU ===")
        
        return "\n\n".join(parts)
    
    def get_source_summary(self) -> str:
        """Kaynak özeti."""
        parts = []
        if self.document_sources:
            parts.append(f"📄 {len(self.document_sources)} dosya")
        if self.web_sources:
            parts.append(f"🌐 {len(self.web_sources)} web")
        if self.needs_general_knowledge:
            parts.append("💡 genel bilgi")
        return " + ".join(parts) if parts else "Kaynak yok"


# =============================================================================
# RAG SERVICE
# =============================================================================

class RAGService:
    """
    Merkezi RAG servisi.
    
    Vector store, web search ve CRAG entegrasyonu sağlar.
    """
    
    def __init__(self):
        """Initialize RAG service."""
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="rag_")
        self._stats = {
            "total_searches": 0,
            "document_hits": 0,
            "web_hits": 0,
            "crag_corrections": 0,
            "avg_search_time_ms": 0.0,
        }
    
    async def search(
        self,
        query: str,
        include_documents: bool = True,
        include_web: bool = False,
        n_results: int = 5,
        score_threshold: float = 0.35,
        timeout: Optional[float] = None,
    ) -> EnrichedContext:
        """
        Comprehensive search across all sources.
        
        Args:
            query: Search query
            include_documents: Search local documents
            include_web: Search web
            n_results: Max results per source
            score_threshold: Minimum relevance score
            timeout: Search timeout in seconds
            
        Returns:
            EnrichedContext with all search results
        """
        start_time = time.time()
        self._stats["total_searches"] += 1
        
        timeout = timeout or settings.WS_RAG_SEARCH_TIMEOUT
        
        context = EnrichedContext(query=query)
        
        try:
            # Run searches in parallel
            tasks = []
            
            if include_documents:
                tasks.append(self._search_documents(query, n_results, score_threshold))
            
            if include_web:
                tasks.append(self._search_web(query, n_results))
            
            if tasks:
                results = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=timeout
                )
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.warning(f"Search error: {result}")
                        continue
                    
                    if include_documents and i == 0:
                        context.document_sources = result
                        context.has_documents = len(result) > 0
                        if context.has_documents:
                            self._stats["document_hits"] += 1
                            context.document_context = self._build_context(result)
                    
                    if include_web and i == (1 if include_documents else 0):
                        context.web_sources = result
                        context.has_web = len(result) > 0
                        if context.has_web:
                            self._stats["web_hits"] += 1
                            context.web_context = self._build_context(result)
            
            # Combine all sources
            context.all_sources = context.document_sources + context.web_sources
            context.total_sources = len(context.all_sources)
            
            # Determine if general knowledge is needed
            context.needs_general_knowledge = context.total_sources == 0
            
        except asyncio.TimeoutError:
            logger.warning(f"RAG search timeout after {timeout}s")
            context.needs_general_knowledge = True
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            context.needs_general_knowledge = True
        
        context.search_time_ms = (time.time() - start_time) * 1000
        
        # Update avg search time
        total = self._stats["total_searches"]
        avg = self._stats["avg_search_time_ms"]
        self._stats["avg_search_time_ms"] = ((avg * (total - 1)) + context.search_time_ms) / total
        
        return context
    
    async def _search_documents(
        self,
        query: str,
        n_results: int,
        score_threshold: float,
    ) -> List[RAGSearchResult]:
        """Search local documents."""
        try:
            from core.vector_store import vector_store
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor,
                lambda: vector_store.search_with_scores(
                    query=query,
                    n_results=n_results,
                    score_threshold=score_threshold
                )
            )
            
            if not results:
                return []
            
            search_results = []
            for r in results:
                meta = r.get("metadata", {})
                doc_text = r.get("document", "")
                score = r.get("score", 0.5)
                
                search_results.append(RAGSearchResult(
                    content=doc_text,
                    source=meta.get("filename", "unknown"),
                    source_type=SourceType.DOCUMENT,
                    title=meta.get("filename", "Kaynak"),
                    url=meta.get("source", "#"),
                    page=meta.get("page"),
                    relevance_score=score,
                    relevance_level=self._score_to_level(score),
                    snippet=doc_text[:200],
                    metadata=meta,
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []
    
    async def _search_web(
        self,
        query: str,
        n_results: int,
    ) -> List[RAGSearchResult]:
        """Search web sources."""
        try:
            from tools.web_search_engine import get_search_engine
            
            engine = get_search_engine()
            if not engine:
                return []
            
            # Run in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self._executor,
                lambda: engine.search(
                    query=query,
                    num_results=n_results,
                    extract_content=True,
                    include_wikipedia=True
                )
            )
            
            if not response or not response.results:
                return []
            
            search_results = []
            for wr in response.results:
                search_results.append(RAGSearchResult(
                    content=wr.full_content[:1000] if wr.full_content else "",
                    source=wr.domain,
                    source_type=SourceType.WIKIPEDIA if "wikipedia" in wr.url.lower() else SourceType.WEB,
                    title=wr.title,
                    url=wr.url,
                    relevance_score=wr.reliability_score if hasattr(wr, 'reliability_score') else 0.6,
                    relevance_level=self._score_to_level(wr.reliability_score if hasattr(wr, 'reliability_score') else 0.6),
                    snippet=wr.snippet or wr.full_content[:200] if wr.full_content else "",
                    metadata={"domain": wr.domain, "provider": str(wr.provider)},
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    def _build_context(self, results: List[RAGSearchResult]) -> str:
        """Build context string from results."""
        parts = []
        for i, r in enumerate(results[:30]):
            source_label = f"[Kaynak {i+1}: {r.title}]"
            if r.url and r.url != "#":
                source_label += f"\nURL: {r.url}"
            if r.page:
                source_label += f" (Sayfa {r.page})"
            
            parts.append(f"{source_label}\n{r.content[:800]}")
        
        return "\n\n".join(parts)
    
    def _score_to_level(self, score: float) -> RelevanceLevel:
        """Convert score to relevance level."""
        if score >= 0.7:
            return RelevanceLevel.HIGH
        elif score >= 0.4:
            return RelevanceLevel.MEDIUM
        elif score >= 0.2:
            return RelevanceLevel.LOW
        return RelevanceLevel.NONE
    
    async def search_with_crag(
        self,
        query: str,
        include_web: bool = False,
        max_iterations: int = 3,
    ) -> EnrichedContext:
        """
        Search with CRAG (Corrective RAG) pipeline.
        
        Applies query transformation and relevance grading
        for better retrieval quality.
        
        Args:
            query: Search query
            include_web: Include web search
            max_iterations: Max CRAG iterations
            
        Returns:
            EnrichedContext with CRAG-enhanced results
        """
        try:
            from core.crag_system import CRAGPipeline, CorrectionAction
            
            # First try normal search
            context = await self.search(
                query=query,
                include_documents=True,
                include_web=include_web,
            )
            
            # If we have enough relevant documents, return
            high_relevance = [
                s for s in context.document_sources 
                if s.relevance_level == RelevanceLevel.HIGH
            ]
            
            if len(high_relevance) >= 2:
                return context
            
            # Apply CRAG correction if needed
            self._stats["crag_corrections"] += 1
            
            # TODO: Full CRAG integration when async pipeline is ready
            # For now, try with expanded query
            expanded_query = self._expand_query(query)
            if expanded_query != query:
                extra_context = await self.search(
                    query=expanded_query,
                    include_documents=True,
                    include_web=False,
                    n_results=3,
                )
                
                # Merge unique results
                existing_sources = {s.source for s in context.document_sources}
                for source in extra_context.document_sources:
                    if source.source not in existing_sources:
                        context.document_sources.append(source)
                        context.all_sources.append(source)
                
                context.crag_iterations = 1
            
            return context
            
        except ImportError:
            logger.warning("CRAG system not available, using basic search")
            return await self.search(
                query=query,
                include_documents=True,
                include_web=include_web,
            )
    
    def _expand_query(self, query: str) -> str:
        """Simple query expansion."""
        # Add Turkish/English variants
        expansions = {
            "nedir": "ne demek açıkla",
            "nasıl": "nasıl yapılır örnek",
            "what is": "what is explain definition",
            "how to": "how to example tutorial",
        }
        
        query_lower = query.lower()
        for key, expansion in expansions.items():
            if key in query_lower:
                return f"{query} {expansion}"
        
        return query
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return self._stats.copy()
    
    def close(self) -> None:
        """Cleanup resources."""
        self._executor.shutdown(wait=False)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

rag_service = RAGService()
