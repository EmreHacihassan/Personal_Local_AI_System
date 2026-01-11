"""
Hybrid Search Module
====================

Dense + Sparse retrieval kombinasyonu.

Stratejiler:
- Dense Search: Embedding-based semantic search
- Sparse Search: BM25 keyword-based search
- Hybrid: RRF ile kombinasyon
"""

import asyncio
import math
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar

import numpy as np


T = TypeVar("T")


class SearchStrategy(Enum):
    """Arama stratejileri"""
    DENSE = "dense"
    SPARSE = "sparse"
    HYBRID = "hybrid"


@dataclass
class SearchResult:
    """Arama sonucu"""
    id: str
    content: str
    score: float
    source: SearchStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)
    dense_score: Optional[float] = None
    sparse_score: Optional[float] = None
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, SearchResult):
            return self.id == other.id
        return False


@dataclass
class Document:
    """Doküman veri yapısı"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None


class BM25Index:
    """
    BM25 sparse arama indeksi
    
    Okapi BM25 algoritması kullanır.
    """
    
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25
    ):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        
        # Index verileri
        self.documents: Dict[str, Document] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0.0
        self.term_doc_freqs: Dict[str, Set[str]] = defaultdict(set)
        self.doc_term_freqs: Dict[str, Dict[str, int]] = {}
        self.idf_cache: Dict[str, float] = {}
        
        self._indexed = False
    
    def _tokenize(self, text: str) -> List[str]:
        """Metni tokenize et"""
        # Basit tokenization: küçük harf + kelime ayırma
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def _compute_idf(self, term: str) -> float:
        """IDF değerini hesapla"""
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        n = len(self.documents)
        df = len(self.term_doc_freqs.get(term, set()))
        
        if df == 0:
            idf = 0.0
        else:
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
        
        self.idf_cache[term] = idf
        return idf
    
    def add_document(self, doc: Document):
        """Doküman ekle"""
        tokens = self._tokenize(doc.content)
        
        self.documents[doc.id] = doc
        self.doc_lengths[doc.id] = len(tokens)
        
        # Term frekansları
        term_freqs: Dict[str, int] = defaultdict(int)
        for token in tokens:
            term_freqs[token] += 1
            self.term_doc_freqs[token].add(doc.id)
        
        self.doc_term_freqs[doc.id] = dict(term_freqs)
        self._indexed = False
    
    def add_documents(self, docs: List[Document]):
        """Birden fazla doküman ekle"""
        for doc in docs:
            self.add_document(doc)
    
    def build_index(self):
        """İndeksi oluştur"""
        if len(self.documents) == 0:
            self.avg_doc_length = 0.0
        else:
            self.avg_doc_length = sum(self.doc_lengths.values()) / len(self.documents)
        
        # IDF cache'i temizle
        self.idf_cache.clear()
        
        self._indexed = True
    
    def _score_document(
        self,
        doc_id: str,
        query_terms: List[str]
    ) -> float:
        """Doküman skorunu hesapla"""
        if not self._indexed:
            self.build_index()
        
        score = 0.0
        doc_len = self.doc_lengths.get(doc_id, 0)
        term_freqs = self.doc_term_freqs.get(doc_id, {})
        
        for term in query_terms:
            if term not in term_freqs:
                continue
            
            tf = term_freqs[term]
            idf = self._compute_idf(term)
            
            # BM25 skoru
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * doc_len / max(self.avg_doc_length, 1)
            )
            
            score += idf * (numerator / denominator)
        
        return score
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        BM25 ile arama yap
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            (doc_id, score) tuple listesi
        """
        if not self._indexed:
            self.build_index()
        
        query_terms = self._tokenize(query)
        
        # İlgili dokümanları bul
        candidate_docs: Set[str] = set()
        for term in query_terms:
            candidate_docs.update(self.term_doc_freqs.get(term, set()))
        
        # Skorları hesapla
        scores = []
        for doc_id in candidate_docs:
            score = self._score_document(doc_id, query_terms)
            if score > 0:
                scores.append((doc_id, score))
        
        # Sırala ve döndür
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class DenseSearcher:
    """
    Dense (embedding-based) arama
    
    Cosine similarity kullanır.
    """
    
    def __init__(
        self,
        embedding_func: Optional[Callable] = None,
        normalize: bool = True
    ):
        self.embedding_func = embedding_func
        self.normalize = normalize
        
        self.documents: Dict[str, Document] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
    
    async def add_document(self, doc: Document):
        """Doküman ekle"""
        self.documents[doc.id] = doc
        
        if doc.embedding is not None:
            embedding = doc.embedding
        elif self.embedding_func:
            embedding = await self.embedding_func(doc.content)
            if isinstance(embedding, list):
                embedding = np.array(embedding)
        else:
            raise ValueError("Embedding gerekli: embedding_func veya doc.embedding")
        
        if self.normalize:
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
        
        self.embeddings[doc.id] = embedding
    
    async def add_documents(self, docs: List[Document]):
        """Birden fazla doküman ekle"""
        for doc in docs:
            await self.add_document(doc)
    
    def _cosine_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embedding: np.ndarray
    ) -> float:
        """Cosine similarity hesapla"""
        if self.normalize:
            # Normalize edilmişse dot product = cosine similarity
            return float(np.dot(query_embedding, doc_embedding))
        else:
            norm_q = np.linalg.norm(query_embedding)
            norm_d = np.linalg.norm(doc_embedding)
            if norm_q == 0 or norm_d == 0:
                return 0.0
            return float(np.dot(query_embedding, doc_embedding) / (norm_q * norm_d))
    
    async def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Dense arama yap
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            
        Returns:
            (doc_id, score) tuple listesi
        """
        if not self.embedding_func:
            raise ValueError("embedding_func gerekli")
        
        # Query embedding
        query_embedding = await self.embedding_func(query)
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)
        
        if self.normalize:
            norm = np.linalg.norm(query_embedding)
            if norm > 0:
                query_embedding = query_embedding / norm
        
        # Tüm dokümanlarla similarity hesapla
        scores = []
        for doc_id, doc_embedding in self.embeddings.items():
            score = self._cosine_similarity(query_embedding, doc_embedding)
            scores.append((doc_id, score))
        
        # Sırala ve döndür
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HybridSearcher:
    """
    Hybrid Search: Dense + Sparse kombinasyonu
    
    Reciprocal Rank Fusion (RRF) ile skorları birleştirir.
    """
    
    def __init__(
        self,
        embedding_func: Optional[Callable] = None,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
        rrf_k: int = 60
    ):
        self.embedding_func = embedding_func
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k
        
        # Alt arama motorları
        self.bm25_index = BM25Index()
        self.dense_searcher = DenseSearcher(embedding_func)
        
        self.documents: Dict[str, Document] = {}
    
    async def add_document(self, doc: Document):
        """Doküman ekle"""
        self.documents[doc.id] = doc
        self.bm25_index.add_document(doc)
        
        if self.embedding_func:
            await self.dense_searcher.add_document(doc)
    
    async def add_documents(self, docs: List[Document]):
        """Birden fazla doküman ekle"""
        for doc in docs:
            await self.add_document(doc)
        
        # BM25 indeksini oluştur
        self.bm25_index.build_index()
    
    def _rrf_score(
        self,
        rankings: List[List[Tuple[str, float]]],
        weights: List[float]
    ) -> Dict[str, float]:
        """
        RRF ile skorları birleştir
        
        Args:
            rankings: Her kaynaktan sıralı sonuçlar
            weights: Her kaynak için ağırlık
            
        Returns:
            doc_id -> final_score mapping
        """
        final_scores: Dict[str, float] = defaultdict(float)
        
        for ranking, weight in zip(rankings, weights):
            for rank, (doc_id, _) in enumerate(ranking, 1):
                final_scores[doc_id] += weight / (self.rrf_k + rank)
        
        return dict(final_scores)
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        strategy: SearchStrategy = SearchStrategy.HYBRID
    ) -> List[SearchResult]:
        """
        Hybrid arama yap
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            strategy: Arama stratejisi
            
        Returns:
            SearchResult listesi
        """
        results = []
        
        if strategy == SearchStrategy.SPARSE:
            # Sadece BM25
            sparse_results = self.bm25_index.search(query, top_k)
            for doc_id, score in sparse_results:
                doc = self.documents.get(doc_id)
                if doc:
                    results.append(SearchResult(
                        id=doc_id,
                        content=doc.content,
                        score=score,
                        source=SearchStrategy.SPARSE,
                        metadata=doc.metadata,
                        sparse_score=score
                    ))
        
        elif strategy == SearchStrategy.DENSE:
            # Sadece dense
            if not self.embedding_func:
                raise ValueError("Dense search için embedding_func gerekli")
            
            dense_results = await self.dense_searcher.search(query, top_k)
            for doc_id, score in dense_results:
                doc = self.documents.get(doc_id)
                if doc:
                    results.append(SearchResult(
                        id=doc_id,
                        content=doc.content,
                        score=score,
                        source=SearchStrategy.DENSE,
                        metadata=doc.metadata,
                        dense_score=score
                    ))
        
        else:  # HYBRID
            # Her iki kaynaktan sonuç al
            sparse_results = self.bm25_index.search(query, top_k * 2)
            
            dense_results = []
            if self.embedding_func:
                dense_results = await self.dense_searcher.search(query, top_k * 2)
            
            # Orijinal skorları sakla
            sparse_scores = {doc_id: score for doc_id, score in sparse_results}
            dense_scores = {doc_id: score for doc_id, score in dense_results}
            
            # RRF ile birleştir
            rankings = [sparse_results]
            weights = [self.sparse_weight]
            
            if dense_results:
                rankings.append(dense_results)
                weights.append(self.dense_weight)
            
            final_scores = self._rrf_score(rankings, weights)
            
            # Sonuçları oluştur
            sorted_docs = sorted(
                final_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:top_k]
            
            for doc_id, score in sorted_docs:
                doc = self.documents.get(doc_id)
                if doc:
                    results.append(SearchResult(
                        id=doc_id,
                        content=doc.content,
                        score=score,
                        source=SearchStrategy.HYBRID,
                        metadata=doc.metadata,
                        dense_score=dense_scores.get(doc_id),
                        sparse_score=sparse_scores.get(doc_id)
                    ))
        
        return results
    
    async def search_with_filter(
        self,
        query: str,
        filter_func: Callable[[Document], bool],
        top_k: int = 10,
        strategy: SearchStrategy = SearchStrategy.HYBRID
    ) -> List[SearchResult]:
        """
        Filtreli arama
        
        Args:
            query: Arama sorgusu
            filter_func: Doküman filtre fonksiyonu
            top_k: Döndürülecek sonuç sayısı
            strategy: Arama stratejisi
            
        Returns:
            Filtrelenmiş SearchResult listesi
        """
        # Daha fazla sonuç al ve filtrele
        all_results = await self.search(query, top_k * 3, strategy)
        
        filtered = []
        for result in all_results:
            doc = self.documents.get(result.id)
            if doc and filter_func(doc):
                filtered.append(result)
                if len(filtered) >= top_k:
                    break
        
        return filtered


class HybridSearchManager:
    """
    Hybrid Search yöneticisi
    
    Birden fazla koleksiyon/namespace desteği.
    """
    
    def __init__(
        self,
        embedding_func: Optional[Callable] = None,
        default_config: Optional[Dict[str, Any]] = None
    ):
        self.embedding_func = embedding_func
        self.default_config = default_config or {
            "dense_weight": 0.5,
            "sparse_weight": 0.5,
            "rrf_k": 60
        }
        
        self._searchers: Dict[str, HybridSearcher] = {}
    
    def get_searcher(self, namespace: str = "default") -> HybridSearcher:
        """Namespace için searcher al veya oluştur"""
        if namespace not in self._searchers:
            self._searchers[namespace] = HybridSearcher(
                embedding_func=self.embedding_func,
                **self.default_config
            )
        return self._searchers[namespace]
    
    async def add_document(
        self,
        doc: Document,
        namespace: str = "default"
    ):
        """Doküman ekle"""
        searcher = self.get_searcher(namespace)
        await searcher.add_document(doc)
    
    async def add_documents(
        self,
        docs: List[Document],
        namespace: str = "default"
    ):
        """Birden fazla doküman ekle"""
        searcher = self.get_searcher(namespace)
        await searcher.add_documents(docs)
    
    async def search(
        self,
        query: str,
        namespace: str = "default",
        top_k: int = 10,
        strategy: SearchStrategy = SearchStrategy.HYBRID
    ) -> List[SearchResult]:
        """Arama yap"""
        searcher = self.get_searcher(namespace)
        return await searcher.search(query, top_k, strategy)
    
    async def search_all(
        self,
        query: str,
        top_k: int = 10,
        strategy: SearchStrategy = SearchStrategy.HYBRID
    ) -> Dict[str, List[SearchResult]]:
        """Tüm namespace'lerde ara"""
        results = {}
        for namespace, searcher in self._searchers.items():
            results[namespace] = await searcher.search(query, top_k, strategy)
        return results
    
    def list_namespaces(self) -> List[str]:
        """Namespace listesi"""
        return list(self._searchers.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler"""
        stats = {
            "namespaces": len(self._searchers),
            "by_namespace": {}
        }
        
        for namespace, searcher in self._searchers.items():
            stats["by_namespace"][namespace] = {
                "document_count": len(searcher.documents),
                "has_dense": searcher.embedding_func is not None
            }
        
        return stats


# Singleton instance
hybrid_search_manager = HybridSearchManager()
