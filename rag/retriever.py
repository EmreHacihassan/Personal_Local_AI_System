"""
Enterprise AI Assistant - Retriever
Endüstri Standartlarında Kurumsal AI Çözümü

Akıllı bilgi getirme - semantic search, hybrid search, reranking.

ENTERPRISE FEATURES:
- Multiple retrieval strategies (semantic, hybrid, multi-query)
- INTEGRATED RERANKING (BM25, CrossEncoder, Ensemble)
- Query result caching
- Performance metrics
- Context-aware truncation
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache
import hashlib

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from core.vector_store import vector_store
from core.llm_manager import llm_manager

# Import reranker
try:
    from rag.reranker import (
        Reranker, BM25Reranker, CrossEncoderReranker, 
        RRFReranker, EnsembleReranker, RankedDocument
    )
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("⚠️ Reranker module not available, using basic retrieval")


@dataclass
class RetrievalResult:
    """Retrieval sonuç yapısı."""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str
    reranked: bool = False  # Reranking uygulandı mı
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source": self.source,
            "reranked": self.reranked,
        }


class QueryResultCache:
    """
    Sorgu sonucu cache'i.
    
    Aynı sorgular için retrieval sonuçlarını cache'ler.
    """
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (results, timestamp)
    
    def _generate_key(self, query: str, top_k: int, strategy: str) -> str:
        """Cache key oluştur."""
        data = f"{query.lower().strip()}|{top_k}|{strategy}"
        return hashlib.sha256(data.encode()).hexdigest()[:24]
    
    def get(self, query: str, top_k: int, strategy: str) -> Optional[List]:
        """Cache'den sonuç al."""
        key = self._generate_key(query, top_k, strategy)
        if key in self._cache:
            results, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return results
            else:
                del self._cache[key]
        return None
    
    def set(self, query: str, top_k: int, strategy: str, results: List) -> None:
        """Sonucu cache'le."""
        if len(self._cache) >= self.max_size:
            # En eski girişi sil
            oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        key = self._generate_key(query, top_k, strategy)
        self._cache[key] = (results, time.time())
    
    def clear(self) -> None:
        """Cache'i temizle."""
        self._cache.clear()


class Retriever:
    """
    Bilgi getirme sınıfı - Endüstri standartlarına uygun.
    
    ENTERPRISE FEATURES:
    - Semantic: Vector similarity search
    - Keyword: BM25 tabanlı arama
    - Hybrid: Semantic + Keyword birleşimi
    - Multi-Query: Query expansion ile arama
    - INTEGRATED RERANKING: BM25 + Ensemble reranking
    - Query result caching
    - Performance metrics
    """
    
    def __init__(
        self,
        top_k: Optional[int] = None,
        score_threshold: float = 0.3,
        enable_reranking: bool = True,
        enable_cache: bool = True,
    ):
        self.top_k = top_k or settings.TOP_K_RESULTS
        self.score_threshold = score_threshold
        self.enable_reranking = enable_reranking and RERANKER_AVAILABLE
        
        # Initialize rerankers
        if self.enable_reranking:
            self._bm25_reranker = BM25Reranker()
            self._ensemble_reranker = EnsembleReranker(
                rerankers=[
                    (BM25Reranker(), 0.4),
                    (CrossEncoderReranker(), 0.6),
                ],
                fusion_method="weighted_sum"
            )
        
        # Query cache
        self.enable_cache = enable_cache
        self._cache = QueryResultCache() if enable_cache else None
        
        # Performance metrics
        self._metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "reranking_applied": 0,
            "total_latency_ms": 0,
        }
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        strategy: str = "semantic",
        rerank: bool = None,  # None = use default setting
    ) -> List[RetrievalResult]:
        """
        Sorguya göre ilgili dökümanları getir.
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            filter_metadata: Metadata filtresi
            strategy: Arama stratejisi (semantic, hybrid, multi_query, rerank)
            rerank: Reranking uygulansın mı (None = default ayarı kullan)
            
        Returns:
            RetrievalResult listesi
        """
        start_time = time.time()
        k = top_k or self.top_k
        should_rerank = rerank if rerank is not None else (self.enable_reranking and strategy != "hybrid")
        
        self._metrics["total_queries"] += 1
        
        # Cache kontrolü
        cache_key_strategy = f"{strategy}_rerank" if should_rerank else strategy
        if self.enable_cache and self._cache:
            cached = self._cache.get(query, k, cache_key_strategy)
            if cached:
                self._metrics["cache_hits"] += 1
                return cached
        
        self._metrics["cache_misses"] += 1
        
        # Retrieval strategy
        if strategy == "semantic":
            results = self._semantic_search(query, k * 2 if should_rerank else k, filter_metadata)
        elif strategy == "hybrid":
            results = self._hybrid_search(query, k, filter_metadata)
        elif strategy == "multi_query":
            results = self._multi_query_search(query, k * 2 if should_rerank else k, filter_metadata)
        elif strategy == "rerank":
            # Semantic + Reranking
            results = self._semantic_search(query, k * 3, filter_metadata)
            should_rerank = True
        else:
            results = self._semantic_search(query, k, filter_metadata)
        
        # RERANKING
        if should_rerank and results and self.enable_reranking:
            results = self._apply_reranking(query, results, k)
            self._metrics["reranking_applied"] += 1
        else:
            results = results[:k]
        
        # Cache sonucu
        if self.enable_cache and self._cache:
            self._cache.set(query, k, cache_key_strategy, results)
        
        # Metrics güncelle
        self._metrics["total_latency_ms"] += (time.time() - start_time) * 1000
        
        return results
    
    def _apply_reranking(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int
    ) -> List[RetrievalResult]:
        """
        Sonuçlara reranking uygula.
        
        BM25 + CrossEncoder ensemble reranking.
        """
        if not results or not self.enable_reranking:
            return results[:top_k]
        
        # Convert to dict format for reranker
        docs_for_rerank = [
            {
                "content": r.content,
                "score": r.score,
                "metadata": r.metadata,
                "source": r.source,
            }
            for r in results
        ]
        
        try:
            # Apply ensemble reranking
            reranked = self._ensemble_reranker.rerank(query, docs_for_rerank, top_k)
            
            # Convert back to RetrievalResult
            reranked_results = [
                RetrievalResult(
                    content=r.content,
                    metadata=r.metadata,
                    score=r.reranked_score,
                    source=r.source or r.metadata.get("source", "unknown"),
                    reranked=True,
                )
                for r in reranked
            ]
            
            return reranked_results
        except Exception as e:
            print(f"⚠️ Reranking failed, returning original results: {e}")
            return results[:top_k]
    
    def _semantic_search(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Semantic (vector) search.
        """
        results = vector_store.search_with_scores(
            query=query,
            n_results=top_k,
            score_threshold=self.score_threshold,
            where=filter_metadata,
        )
        
        return [
            RetrievalResult(
                content=r["document"],
                metadata=r["metadata"],
                score=r["score"],
                source=r["metadata"].get("source", "unknown"),
            )
            for r in results
        ]
    
    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None,
        alpha: float = 0.7,
    ) -> List[RetrievalResult]:
        """
        Hybrid search (semantic + keyword).
        
        Alpha: Semantic ağırlığı (0-1). 1 = sadece semantic, 0 = sadece keyword.
        """
        # Get semantic results
        semantic_results = self._semantic_search(query, top_k * 2, filter_metadata)
        
        # Keyword search (simple implementation - contains query terms)
        query_terms = query.lower().split()
        
        # Re-score with hybrid approach
        for result in semantic_results:
            content_lower = result.content.lower()
            
            # Calculate keyword score (term frequency based)
            keyword_matches = sum(1 for term in query_terms if term in content_lower)
            keyword_score = keyword_matches / len(query_terms) if query_terms else 0
            
            # Combine scores
            result.score = (alpha * result.score) + ((1 - alpha) * keyword_score)
        
        # Sort by combined score
        semantic_results.sort(key=lambda x: x.score, reverse=True)
        
        return semantic_results[:top_k]
    
    def _multi_query_search(
        self,
        query: str,
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Multi-query retrieval - sorgunun farklı varyasyonlarını kullan.
        """
        # Generate query variations using LLM
        expansion_prompt = f"""Aşağıdaki arama sorgusunun 3 farklı varyasyonunu oluştur.
Her varyasyon aynı bilgiyi farklı kelimelerle aramalı.
Sadece varyasyonları listele, açıklama yapma.

Orijinal sorgu: {query}

Varyasyonlar:"""
        
        try:
            variations_text = llm_manager.generate(
                prompt=expansion_prompt,
                temperature=0.7,
                max_tokens=200,
            )
            
            # Parse variations
            variations = [query]  # Original query
            for line in variations_text.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove numbering
                    line = line.lstrip('0123456789.-) ')
                    if line:
                        variations.append(line)
            
            variations = variations[:4]  # Max 4 queries
            
        except Exception:
            variations = [query]
        
        # Search with all variations
        all_results = {}
        
        for variation in variations:
            results = self._semantic_search(variation, top_k, filter_metadata)
            for result in results:
                # Use content hash as key for deduplication
                key = hash(result.content[:100])
                if key not in all_results or result.score > all_results[key].score:
                    all_results[key] = result
        
        # Sort and return
        final_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return final_results[:top_k]
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        max_context_length: int = 4000,
    ) -> str:
        """
        Sorgu için context string oluştur.
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            filter_metadata: Metadata filtresi
            max_context_length: Maksimum context uzunluğu
            
        Returns:
            Formatlanmış context string
        """
        results = self.retrieve(query, top_k, filter_metadata)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            source = result.source
            content = result.content
            score = result.score
            
            # Format result
            result_text = f"""[Kaynak {i}] {source}
Skor: {score:.2f}
---
{content}
---
"""
            
            # Check length
            if current_length + len(result_text) > max_context_length:
                # Truncate if needed
                remaining = max_context_length - current_length - 50
                if remaining > 200:
                    truncated = content[:remaining] + "..."
                    result_text = f"""[Kaynak {i}] {source}
Skor: {score:.2f}
---
{truncated}
---
"""
                    context_parts.append(result_text)
                break
            
            context_parts.append(result_text)
            current_length += len(result_text)
        
        return "\n".join(context_parts)
    
    def get_sources(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[str]:
        """Sadece kaynak listesi döndür."""
        results = self.retrieve(query, top_k)
        return list(set(r.source for r in results))
    
    def get_metrics(self) -> Dict[str, Any]:
        """Performance metrics döndür."""
        total = self._metrics["cache_hits"] + self._metrics["cache_misses"]
        cache_hit_rate = (
            self._metrics["cache_hits"] / total * 100 if total > 0 else 0
        )
        avg_latency = (
            self._metrics["total_latency_ms"] / self._metrics["total_queries"]
            if self._metrics["total_queries"] > 0 else 0
        )
        
        return {
            "total_queries": self._metrics["total_queries"],
            "cache_hits": self._metrics["cache_hits"],
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "reranking_applied": self._metrics["reranking_applied"],
            "avg_latency_ms": f"{avg_latency:.1f}",
            "reranking_enabled": self.enable_reranking,
            "cache_enabled": self.enable_cache,
        }
    
    def clear_cache(self) -> None:
        """Query cache'i temizle."""
        if self._cache:
            self._cache.clear()
    
    def reset_metrics(self) -> None:
        """Metrics'i sıfırla."""
        for key in self._metrics:
            self._metrics[key] = 0


# Singleton instance
retriever = Retriever()
