"""
Enterprise AI Assistant - Advanced RAG Module
Gelişmiş RAG teknikleri

HyDE, Multi-Query, Reranking, Fusion RAG.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import defaultdict

from core.config import settings


class RAGStrategy(str, Enum):
    """RAG stratejileri."""
    NAIVE = "naive"  # Basit semantic search
    HYDE = "hyde"  # Hypothetical Document Embeddings
    MULTI_QUERY = "multi_query"  # Çoklu sorgu genişletme
    FUSION = "fusion"  # Reciprocal Rank Fusion
    RERANK = "rerank"  # İki aşamalı reranking
    CONTEXTUAL = "contextual"  # Bağlamsal sıkıştırma


@dataclass
class RetrievalResult:
    """Retrieval sonucu."""
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    chunk_id: str = ""
    relevance_explanation: str = ""


@dataclass
class RAGConfig:
    """RAG konfigürasyonu."""
    strategy: RAGStrategy = RAGStrategy.FUSION
    top_k: int = 5
    rerank_top_k: int = 20
    min_score: float = 0.3
    enable_hyde: bool = True
    num_queries: int = 3
    fusion_k: int = 60  # RRF parameter


class HyDERetriever:
    """
    Hypothetical Document Embeddings (HyDE).
    
    Sorguyu hipotetik bir cevaba dönüştürüp,
    o cevabın embedding'i ile arama yapar.
    """
    
    def __init__(self, llm_manager=None, embedding_manager=None):
        """HyDE retriever başlat."""
        self._llm = llm_manager
        self._embedding = embedding_manager
    
    def _lazy_load(self):
        """Lazy loading for managers."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
        if self._embedding is None:
            from core.embedding import embedding_manager
            self._embedding = embedding_manager
    
    def generate_hypothetical_document(self, query: str) -> str:
        """
        Sorgu için hipotetik döküman üret.
        
        Args:
            query: Kullanıcı sorgusu
            
        Returns:
            Hipotetik cevap dökümanı
        """
        self._lazy_load()
        
        prompt = f"""Aşağıdaki soruya verilecek ideal bir cevap dökümanı yaz.
Bu döküman, sorunun cevabını içeren gerçek bir kurumsal döküman gibi olmalı.
Kısa ve öz ol (maksimum 150 kelime).

Soru: {query}

Hipotetik Döküman:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=200)
            return response
        except Exception:
            return query
    
    def get_hyde_embedding(self, query: str) -> List[float]:
        """HyDE embedding al."""
        self._lazy_load()
        
        hypothetical_doc = self.generate_hypothetical_document(query)
        return self._embedding.embed_text(hypothetical_doc)


class MultiQueryRetriever:
    """
    Multi-Query Retrieval.
    
    Tek bir sorguyu birden fazla perspektiften yeniden yazar
    ve tüm sonuçları birleştirir.
    """
    
    def __init__(self, llm_manager=None, num_queries: int = 3):
        """Multi-query retriever başlat."""
        self._llm = llm_manager
        self.num_queries = num_queries
    
    def _lazy_load(self):
        """Lazy loading."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def generate_queries(self, original_query: str) -> List[str]:
        """
        Orijinal sorgudan alternatif sorgular üret.
        
        Args:
            original_query: Orijinal kullanıcı sorgusu
            
        Returns:
            Alternatif sorgular listesi
        """
        self._lazy_load()
        
        prompt = f"""Aşağıdaki soruyu {self.num_queries} farklı şekilde yeniden yaz.
Her versiyon farklı kelimeler ve perspektif kullanmalı ama aynı anlama gelmeli.
Her sorguyu yeni satırda yaz, numarasız.

Orijinal Soru: {original_query}

Alternatif Sorgular:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=200)
            queries = [q.strip() for q in response.strip().split("\n") if q.strip()]
            queries = [original_query] + queries[:self.num_queries]
            return queries
        except Exception:
            return [original_query]


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF).
    
    Birden fazla retrieval sonucunu birleştirir.
    """
    
    def __init__(self, k: int = 60):
        """RRF başlat."""
        self.k = k
    
    def fuse(
        self,
        result_lists: List[List[RetrievalResult]],
    ) -> List[RetrievalResult]:
        """
        Sonuç listelerini birleştir.
        
        Args:
            result_lists: Birleştirilecek sonuç listeleri
            
        Returns:
            Birleştirilmiş ve sıralanmış sonuçlar
        """
        # Calculate RRF scores
        rrf_scores: Dict[str, float] = defaultdict(float)
        content_map: Dict[str, RetrievalResult] = {}
        
        for results in result_lists:
            for rank, result in enumerate(results, 1):
                # Use content hash as key
                key = hash(result.content)
                rrf_scores[key] += 1.0 / (self.k + rank)
                
                # Keep the result with highest original score
                if key not in content_map or result.score > content_map[key].score:
                    content_map[key] = result
        
        # Sort by RRF score
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        
        # Build final results
        fused_results = []
        for key in sorted_keys:
            result = content_map[key]
            result.score = rrf_scores[key]  # Replace with RRF score
            fused_results.append(result)
        
        return fused_results


class Reranker:
    """
    Cross-Encoder Reranking.
    
    İlk retrieval sonuçlarını LLM ile yeniden sıralar.
    """
    
    def __init__(self, llm_manager=None):
        """Reranker başlat."""
        self._llm = llm_manager
    
    def _lazy_load(self):
        """Lazy loading."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        Sonuçları yeniden sırala.
        
        Args:
            query: Sorgu
            results: İlk sonuçlar
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            Yeniden sıralanmış sonuçlar
        """
        self._lazy_load()
        
        if not results:
            return []
        
        # Score each result
        scored_results = []
        
        for result in results[:20]:  # Limit for efficiency
            score = self._score_relevance(query, result.content)
            result.score = score
            scored_results.append(result)
        
        # Sort by new scores
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        return scored_results[:top_k]
    
    def _score_relevance(self, query: str, document: str) -> float:
        """
        Sorgu-döküman ilişkisini skorla.
        
        Args:
            query: Sorgu
            document: Döküman içeriği
            
        Returns:
            Relevance skoru (0-1)
        """
        prompt = f"""Aşağıdaki sorgu ve döküman arasındaki ilişkiyi 0-10 arası puanla.
Sadece sayı yaz.

Sorgu: {query}

Döküman: {document[:500]}

Puan (0-10):"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=10)
            score = float(re.search(r'\d+', response).group()) / 10.0
            return min(max(score, 0.0), 1.0)
        except Exception:
            return 0.5


class ContextualCompressor:
    """
    Contextual Compression.
    
    Retrieval sonuçlarını sorguya göre sıkıştırır,
    sadece ilgili kısımları tutar.
    """
    
    def __init__(self, llm_manager=None):
        """Compressor başlat."""
        self._llm = llm_manager
    
    def _lazy_load(self):
        """Lazy loading."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def compress(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """
        Sonuçları sıkıştır.
        
        Args:
            query: Sorgu
            results: Retrieval sonuçları
            
        Returns:
            Sıkıştırılmış sonuçlar
        """
        self._lazy_load()
        
        compressed = []
        
        for result in results:
            compressed_content = self._extract_relevant(query, result.content)
            
            if compressed_content:
                new_result = RetrievalResult(
                    content=compressed_content,
                    score=result.score,
                    metadata=result.metadata,
                    source=result.source,
                    chunk_id=result.chunk_id,
                )
                compressed.append(new_result)
        
        return compressed
    
    def _extract_relevant(self, query: str, document: str) -> str:
        """İlgili kısımları çıkar."""
        if len(document) < 500:
            return document
        
        prompt = f"""Aşağıdaki dökümanın sadece soruyla ilgili kısımlarını çıkar.
İlgisiz kısımları at. Kısa ve öz tut.

Soru: {query}

Döküman:
{document[:1500]}

İlgili Kısımlar:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=300)
            return response.strip()
        except Exception:
            return document[:500]


class AdvancedRAG:
    """
    Gelişmiş RAG sistemi.
    
    Tüm RAG stratejilerini birleştiren ana sınıf.
    """
    
    def __init__(self, config: RAGConfig = None):
        """Advanced RAG başlat."""
        self.config = config or RAGConfig()
        self.hyde = HyDERetriever()
        self.multi_query = MultiQueryRetriever()
        self.rrf = ReciprocalRankFusion(k=self.config.fusion_k)
        self.reranker = Reranker()
        self.compressor = ContextualCompressor()
        self._vector_store = None
    
    def _lazy_load_vector_store(self):
        """Lazy load vector store."""
        if self._vector_store is None:
            from core.vector_store import vector_store
            self._vector_store = vector_store
    
    def retrieve(
        self,
        query: str,
        strategy: RAGStrategy = None,
        top_k: int = None,
    ) -> List[RetrievalResult]:
        """
        Gelişmiş retrieval yap.
        
        Args:
            query: Kullanıcı sorgusu
            strategy: RAG stratejisi
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            Retrieval sonuçları
        """
        self._lazy_load_vector_store()
        
        strategy = strategy or self.config.strategy
        top_k = top_k or self.config.top_k
        
        if strategy == RAGStrategy.NAIVE:
            return self._naive_retrieve(query, top_k)
        
        elif strategy == RAGStrategy.HYDE:
            return self._hyde_retrieve(query, top_k)
        
        elif strategy == RAGStrategy.MULTI_QUERY:
            return self._multi_query_retrieve(query, top_k)
        
        elif strategy == RAGStrategy.FUSION:
            return self._fusion_retrieve(query, top_k)
        
        elif strategy == RAGStrategy.RERANK:
            return self._rerank_retrieve(query, top_k)
        
        elif strategy == RAGStrategy.CONTEXTUAL:
            return self._contextual_retrieve(query, top_k)
        
        else:
            return self._naive_retrieve(query, top_k)
    
    def _naive_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """Basit semantic search."""
        raw_results = self._vector_store.search_with_scores(
            query=query,
            n_results=top_k,
        )
        
        return [
            RetrievalResult(
                content=r.get("content", r.get("document", "")),
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {}),
                source=r.get("metadata", {}).get("source", ""),
            )
            for r in raw_results
        ]
    
    def _hyde_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """HyDE tabanlı retrieval."""
        hyde_embedding = self.hyde.get_hyde_embedding(query)
        
        # Search with HyDE embedding
        raw_results = self._vector_store.search_by_embedding(
            embedding=hyde_embedding,
            n_results=top_k,
        )
        
        return [
            RetrievalResult(
                content=r.get("content", r.get("document", "")),
                score=r.get("score", 0.0),
                metadata=r.get("metadata", {}),
                source=r.get("metadata", {}).get("source", ""),
            )
            for r in raw_results
        ]
    
    def _multi_query_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """Multi-query retrieval."""
        queries = self.multi_query.generate_queries(query)
        
        all_results = []
        for q in queries:
            results = self._naive_retrieve(q, top_k * 2)
            all_results.append(results)
        
        # Fuse results
        fused = self.rrf.fuse(all_results)
        return fused[:top_k]
    
    def _fusion_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """Fusion RAG - tüm yöntemleri birleştir."""
        result_lists = []
        
        # Naive results
        naive_results = self._naive_retrieve(query, top_k * 2)
        result_lists.append(naive_results)
        
        # Multi-query results
        try:
            mq_results = self._multi_query_retrieve(query, top_k * 2)
            result_lists.append(mq_results)
        except Exception:
            pass
        
        # HyDE results (if enabled)
        if self.config.enable_hyde:
            try:
                hyde_results = self._hyde_retrieve(query, top_k * 2)
                result_lists.append(hyde_results)
            except Exception:
                pass
        
        # Fuse all results
        fused = self.rrf.fuse(result_lists)
        return fused[:top_k]
    
    def _rerank_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """İki aşamalı reranking retrieval."""
        # First stage: get more results
        initial_results = self._naive_retrieve(query, self.config.rerank_top_k)
        
        # Second stage: rerank
        reranked = self.reranker.rerank(query, initial_results, top_k)
        return reranked
    
    def _contextual_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> List[RetrievalResult]:
        """Bağlamsal sıkıştırma ile retrieval."""
        # Get initial results
        results = self._fusion_retrieve(query, top_k * 2)
        
        # Compress
        compressed = self.compressor.compress(query, results)
        return compressed[:top_k]
    
    def get_context_for_llm(
        self,
        query: str,
        strategy: RAGStrategy = None,
    ) -> str:
        """
        LLM için formatlanmış bağlam al.
        
        Args:
            query: Sorgu
            strategy: Strateji
            
        Returns:
            Formatlanmış bağlam string'i
        """
        results = self.retrieve(query, strategy)
        
        if not results:
            return "İlgili bilgi bulunamadı."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            source = result.source or "Bilinmeyen Kaynak"
            context_parts.append(f"[Kaynak {i}: {source}]\n{result.content}")
        
        return "\n\n---\n\n".join(context_parts)


# Singleton instance
advanced_rag = AdvancedRAG()
