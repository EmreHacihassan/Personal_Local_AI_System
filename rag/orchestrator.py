"""
RAG Orchestrator
================

Gelişmiş RAG iş akışı yönetimi.

Features:
- Multi-stage retrieval pipeline
- Adaptive strategy selection
- Real-time streaming support
- Caching and optimization
- A/B testing support
- Comprehensive metrics
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)

from core.config import settings
from core.logger import get_logger

logger = get_logger("rag.orchestrator")


# =============================================================================
# CACHE SYSTEM
# =============================================================================

class RAGCache:
    """
    RAG sonuç cache sistemi.
    
    - Query embedding cache
    - Retrieval result cache
    - TTL support
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 3600,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._hit_count = 0
        self._miss_count = 0
    
    def _generate_key(self, query: str, strategy: str = "", filters: Dict = None) -> str:
        """Cache key oluştur."""
        key_parts = [query.lower().strip(), strategy]
        if filters:
            key_parts.append(json.dumps(filters, sort_keys=True))
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    def get(self, query: str, strategy: str = "", filters: Dict = None) -> Optional[Any]:
        """Cache'den al."""
        key = self._generate_key(query, strategy, filters)
        
        if key in self._cache:
            entry = self._cache[key]
            
            # TTL kontrolü
            if time.time() - entry["timestamp"] > entry["ttl"]:
                del self._cache[key]
                self._miss_count += 1
                return None
            
            self._access_times[key] = time.time()
            self._hit_count += 1
            return entry["data"]
        
        self._miss_count += 1
        return None
    
    def set(
        self,
        query: str,
        data: Any,
        strategy: str = "",
        filters: Dict = None,
        ttl: int = None,
    ):
        """Cache'e yaz."""
        key = self._generate_key(query, strategy, filters)
        
        # Boyut kontrolü (LRU eviction)
        if len(self._cache) >= self.max_size:
            self._evict_lru()
        
        self._cache[key] = {
            "data": data,
            "timestamp": time.time(),
            "ttl": ttl or self.default_ttl,
        }
        self._access_times[key] = time.time()
    
    def _evict_lru(self):
        """En az kullanılanı çıkar."""
        if not self._access_times:
            return
        
        oldest_key = min(self._access_times, key=self._access_times.get)
        del self._cache[oldest_key]
        del self._access_times[oldest_key]
    
    def invalidate(self, query: str = None):
        """Cache'i geçersiz kıl."""
        if query:
            key = self._generate_key(query)
            if key in self._cache:
                del self._cache[key]
        else:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        total = self._hit_count + self._miss_count
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hit_count,
            "misses": self._miss_count,
            "hit_rate": self._hit_count / total if total > 0 else 0,
        }


# =============================================================================
# METRICS COLLECTOR
# =============================================================================

@dataclass
class RAGMetrics:
    """RAG metrik toplama."""
    
    # Timing
    total_requests: int = 0
    total_latency_ms: int = 0
    retrieval_latency_ms: int = 0
    generation_latency_ms: int = 0
    
    # Quality
    avg_relevance_score: float = 0.0
    avg_chunks_returned: float = 0.0
    
    # Strategy usage
    strategy_usage: Dict[str, int] = field(default_factory=dict)
    
    # Errors
    error_count: int = 0
    
    def record_request(
        self,
        latency_ms: int,
        retrieval_ms: int,
        generation_ms: int,
        chunks_count: int,
        strategy: str,
        relevance_score: float = 0.0,
    ):
        """İstek kaydet."""
        self.total_requests += 1
        self.total_latency_ms += latency_ms
        self.retrieval_latency_ms += retrieval_ms
        self.generation_latency_ms += generation_ms
        
        # Rolling average
        n = self.total_requests
        self.avg_chunks_returned = (
            (self.avg_chunks_returned * (n - 1) + chunks_count) / n
        )
        self.avg_relevance_score = (
            (self.avg_relevance_score * (n - 1) + relevance_score) / n
        )
        
        # Strategy tracking
        if strategy not in self.strategy_usage:
            self.strategy_usage[strategy] = 0
        self.strategy_usage[strategy] += 1
    
    def record_error(self):
        """Hata kaydet."""
        self.error_count += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Özet istatistikler."""
        return {
            "total_requests": self.total_requests,
            "error_rate": self.error_count / max(self.total_requests, 1),
            "avg_latency_ms": self.total_latency_ms / max(self.total_requests, 1),
            "avg_retrieval_ms": self.retrieval_latency_ms / max(self.total_requests, 1),
            "avg_generation_ms": self.generation_latency_ms / max(self.total_requests, 1),
            "avg_chunks": round(self.avg_chunks_returned, 2),
            "avg_relevance": round(self.avg_relevance_score, 3),
            "strategy_usage": self.strategy_usage,
        }


# =============================================================================
# RAG ORCHESTRATOR
# =============================================================================

class RAGOrchestrator:
    """
    RAG Orchestrator - Merkezi kontrol ve koordinasyon.
    
    Features:
    - Intelligent strategy selection
    - Multi-stage retrieval
    - Streaming support
    - Caching
    - Metrics collection
    - Fallback handling
    """
    
    def __init__(
        self,
        pipeline=None,
        llm_manager=None,
        enable_cache: bool = True,
        enable_metrics: bool = True,
    ):
        """
        Orchestrator başlat.
        
        Args:
            pipeline: RAG Pipeline instance
            llm_manager: LLM manager
            enable_cache: Cache aktif mi
            enable_metrics: Metrik toplama aktif mi
        """
        self._pipeline = pipeline
        self._llm_manager = llm_manager
        
        # Bileşenler
        self.cache = RAGCache() if enable_cache else None
        self.metrics = RAGMetrics() if enable_metrics else None
        
        # Callbacks
        self._on_retrieval_start: Optional[Callable] = None
        self._on_retrieval_complete: Optional[Callable] = None
        self._on_generation_start: Optional[Callable] = None
        self._on_token: Optional[Callable] = None
    
    def _lazy_load(self):
        """Lazy loading."""
        if self._pipeline is None:
            from rag.pipeline import rag_pipeline
            self._pipeline = rag_pipeline
        
        if self._llm_manager is None:
            from core.llm_manager import llm_manager
            self._llm_manager = llm_manager
    
    def set_callbacks(
        self,
        on_retrieval_start: Callable = None,
        on_retrieval_complete: Callable = None,
        on_generation_start: Callable = None,
        on_token: Callable = None,
    ):
        """Callback'leri ayarla."""
        self._on_retrieval_start = on_retrieval_start
        self._on_retrieval_complete = on_retrieval_complete
        self._on_generation_start = on_generation_start
        self._on_token = on_token
    
    def query(
        self,
        query: str,
        strategy: str = None,
        top_k: int = 5,
        filter_metadata: Dict = None,
        use_cache: bool = True,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """
        Senkron RAG sorgusu.
        
        Args:
            query: Kullanıcı sorgusu
            strategy: Retrieval stratejisi
            top_k: Döndürülecek chunk sayısı
            filter_metadata: Metadata filtresi
            use_cache: Cache kullan
            include_sources: Kaynak bilgilerini dahil et
            
        Returns:
            RAG yanıt dictionary
        """
        self._lazy_load()
        
        start_time = time.time()
        
        try:
            # Callback
            if self._on_retrieval_start:
                self._on_retrieval_start(query)
            
            # 1. Cache kontrolü
            if use_cache and self.cache:
                cached = self.cache.get(query, strategy or "auto", filter_metadata)
                if cached:
                    logger.debug(f"Cache hit for query: {query[:50]}...")
                    return cached
            
            # 2. Retrieval
            retrieval_start = time.time()
            
            from rag.pipeline import RetrievalStrategy
            strat = RetrievalStrategy(strategy) if strategy else None
            
            context = self._pipeline.retrieve(
                query=query,
                strategy=strat,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )
            
            retrieval_ms = int((time.time() - retrieval_start) * 1000)
            
            # Callback
            if self._on_retrieval_complete:
                self._on_retrieval_complete(context)
            
            # 3. Generation
            if self._on_generation_start:
                self._on_generation_start()
            
            generation_start = time.time()
            response = self._pipeline.generate_answer(query, context)
            generation_ms = int((time.time() - generation_start) * 1000)
            
            # 4. Result oluştur
            total_ms = int((time.time() - start_time) * 1000)
            
            result = {
                "answer": response.answer,
                "query": query,
                "strategy_used": context.strategy_used.value,
                "chunks_count": len(context.chunks),
                "timing": {
                    "total_ms": total_ms,
                    "retrieval_ms": retrieval_ms,
                    "generation_ms": generation_ms,
                },
            }
            
            if include_sources:
                result["citations"] = [c.to_dict() for c in response.citations]
                result["sources"] = list(set(c.source for c in response.citations))
            
            # 5. Cache'e yaz
            if use_cache and self.cache:
                self.cache.set(query, result, strategy or "auto", filter_metadata)
            
            # 6. Metrics
            if self.metrics:
                avg_score = sum(c.score for c in context.chunks) / max(len(context.chunks), 1)
                self.metrics.record_request(
                    latency_ms=total_ms,
                    retrieval_ms=retrieval_ms,
                    generation_ms=generation_ms,
                    chunks_count=len(context.chunks),
                    strategy=context.strategy_used.value,
                    relevance_score=avg_score,
                )
            
            return result
            
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            if self.metrics:
                self.metrics.record_error()
            
            return {
                "error": str(e),
                "query": query,
                "answer": "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.",
            }
    
    async def query_async(
        self,
        query: str,
        strategy: str = None,
        top_k: int = 5,
        filter_metadata: Dict = None,
        use_cache: bool = True,
        include_sources: bool = True,
    ) -> Dict[str, Any]:
        """Asenkron RAG sorgusu."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(
                query, strategy, top_k, filter_metadata, use_cache, include_sources
            )
        )
    
    async def stream_response(
        self,
        query: str,
        strategy: str = None,
        top_k: int = 5,
        filter_metadata: Dict = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming RAG yanıtı.
        
        Yields:
            {"type": "retrieval", "data": {...}}
            {"type": "context", "data": {...}}
            {"type": "token", "data": "..."}
            {"type": "done", "data": {...}}
        """
        self._lazy_load()
        
        start_time = time.time()
        
        try:
            # 1. Retrieval başladı
            yield {
                "type": "retrieval_start",
                "data": {"query": query, "strategy": strategy},
            }
            
            # 2. Retrieval yap
            from rag.pipeline import RetrievalStrategy
            strat = RetrievalStrategy(strategy) if strategy else None
            
            context = await self._pipeline.retrieve_async(
                query=query,
                strategy=strat,
                top_k=top_k,
                filter_metadata=filter_metadata,
            )
            
            # 3. Context bilgisi
            yield {
                "type": "context",
                "data": {
                    "chunks_count": len(context.chunks),
                    "strategy": context.strategy_used.value,
                    "search_time_ms": context.search_time_ms,
                    "citations": [c.to_dict() for c in context.get_citations()],
                },
            }
            
            # 4. Generation başladı
            yield {"type": "generation_start", "data": {}}
            
            # 5. Streaming generation
            prompt = self._pipeline._build_rag_prompt(context)
            full_prompt = f"{prompt}\n\nKullanıcı Sorusu: {query}\n\nCevap:"
            
            # Token token stream
            full_answer = ""
            
            if hasattr(self._llm_manager, 'stream'):
                async for token in self._llm_manager.stream(full_prompt):
                    full_answer += token
                    yield {"type": "token", "data": token}
                    
                    if self._on_token:
                        await self._on_token(token)
            else:
                # Fallback: sync generation
                answer = self._llm_manager.generate(full_prompt, max_tokens=1000)
                full_answer = answer
                
                # Simulate streaming
                for i in range(0, len(answer), 20):
                    chunk = answer[i:i+20]
                    yield {"type": "token", "data": chunk}
                    await asyncio.sleep(0.01)
            
            # 6. Tamamlandı
            total_ms = int((time.time() - start_time) * 1000)
            
            yield {
                "type": "done",
                "data": {
                    "answer": full_answer,
                    "total_ms": total_ms,
                    "chunks_count": len(context.chunks),
                    "citations": [c.to_dict() for c in context.get_citations()],
                },
            }
            
            # Metrics
            if self.metrics:
                avg_score = sum(c.score for c in context.chunks) / max(len(context.chunks), 1)
                self.metrics.record_request(
                    latency_ms=total_ms,
                    retrieval_ms=context.search_time_ms,
                    generation_ms=total_ms - context.search_time_ms,
                    chunks_count=len(context.chunks),
                    strategy=context.strategy_used.value,
                    relevance_score=avg_score,
                )
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            if self.metrics:
                self.metrics.record_error()
            
            yield {
                "type": "error",
                "data": {"error": str(e)},
            }
    
    def multi_query(
        self,
        queries: List[str],
        strategy: str = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Birden fazla sorguyu paralel işle.
        
        Args:
            queries: Sorgu listesi
            strategy: Retrieval stratejisi
            top_k: Her sorgu için chunk sayısı
            
        Returns:
            Birleştirilmiş sonuçlar
        """
        results = []
        all_chunks = []
        all_citations = []
        
        for query in queries:
            result = self.query(query, strategy, top_k, use_cache=True)
            results.append(result)
            
            if "citations" in result:
                all_citations.extend(result["citations"])
        
        # Deduplicate citations
        seen = set()
        unique_citations = []
        for c in all_citations:
            key = f"{c.get('source', '')}_{c.get('page', '')}"
            if key not in seen:
                seen.add(key)
                unique_citations.append(c)
        
        return {
            "queries": queries,
            "results": results,
            "merged_citations": unique_citations,
            "total_chunks": sum(r.get("chunks_count", 0) for r in results),
        }
    
    def search_only(
        self,
        query: str,
        strategy: str = None,
        top_k: int = 10,
        filter_metadata: Dict = None,
    ) -> List[Dict[str, Any]]:
        """
        Sadece retrieval yap, generation yapma.
        
        Args:
            query: Arama sorgusu
            strategy: Retrieval stratejisi
            top_k: Döndürülecek sonuç sayısı
            filter_metadata: Metadata filtresi
            
        Returns:
            Chunk listesi
        """
        self._lazy_load()
        
        from rag.pipeline import RetrievalStrategy
        strat = RetrievalStrategy(strategy) if strategy else None
        
        context = self._pipeline.retrieve(
            query=query,
            strategy=strat,
            top_k=top_k,
            filter_metadata=filter_metadata,
        )
        
        return [chunk.to_dict() for chunk in context.chunks]
    
    def get_page_content(
        self,
        page_numbers: List[int],
        source: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Belirli sayfaların içeriğini getir.
        
        Args:
            page_numbers: Sayfa numaraları
            source: Kaynak dosya adı
            
        Returns:
            Sayfa içerikleri
        """
        self._lazy_load()
        
        from core.vector_store import vector_store
        
        return vector_store.get_by_page_numbers(page_numbers, source)
    
    def get_stats(self) -> Dict[str, Any]:
        """Orchestrator istatistikleri."""
        stats = {
            "pipeline": self._pipeline.get_stats() if self._pipeline else {},
        }
        
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        if self.metrics:
            stats["metrics"] = self.metrics.get_summary()
        
        return stats
    
    def clear_cache(self):
        """Cache'i temizle."""
        if self.cache:
            self.cache.invalidate()
            logger.info("RAG cache cleared")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

rag_orchestrator = RAGOrchestrator()


__all__ = [
    "RAGOrchestrator",
    "RAGCache",
    "RAGMetrics",
    "rag_orchestrator",
]
