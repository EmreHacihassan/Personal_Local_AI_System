"""
Document Reranker
=================

Endüstri standartlarında döküman reranking sistemi.
Cross-encoder ve diğer reranking stratejileri.

Features:
- Cross-encoder reranking
- BM25 reranking
- Reciprocal Rank Fusion (RRF)
- Cohere-style reranking
- Custom scoring functions
"""

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .logger import get_logger

logger = get_logger("reranker")


@dataclass
class RankedDocument:
    """Rerank edilmiş döküman"""
    content: str
    original_score: float
    reranked_score: float
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # İsteğe bağlı alanlar
    doc_id: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "original_score": self.original_score,
            "reranked_score": self.reranked_score,
            "rank": self.rank,
            "metadata": self.metadata,
            "doc_id": self.doc_id,
            "source": self.source
        }


class RerankerStrategy(ABC):
    """Reranking stratejisi base class"""
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        pass


class BM25Reranker(RerankerStrategy):
    """
    BM25 algoritması ile reranking
    
    Lexical (keyword-based) reranking için kullanılır.
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
    
    def _tokenize(self, text: str) -> List[str]:
        """Basit tokenization"""
        # Lowercase ve kelime ayırma
        text = text.lower()
        words = re.findall(r'\b\w+\b', text)
        return words
    
    def _compute_idf(
        self,
        word: str,
        doc_freqs: Dict[str, int],
        num_docs: int
    ) -> float:
        """Inverse Document Frequency hesapla"""
        df = doc_freqs.get(word, 0)
        return math.log((num_docs - df + 0.5) / (df + 0.5) + 1)
    
    def _compute_bm25(
        self,
        query_tokens: List[str],
        doc_tokens: List[str],
        doc_freqs: Dict[str, int],
        num_docs: int,
        avg_doc_len: float
    ) -> float:
        """BM25 skoru hesapla"""
        score = 0.0
        doc_len = len(doc_tokens)
        doc_term_freqs = Counter(doc_tokens)
        
        for term in query_tokens:
            if term not in doc_term_freqs:
                continue
            
            tf = doc_term_freqs[term]
            idf = self._compute_idf(term, doc_freqs, num_docs)
            
            # BM25 formülü
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avg_doc_len)
            
            score += idf * (numerator / denominator)
        
        return score
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        if not documents:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        # Tokenize all documents
        doc_tokens_list = []
        for doc in documents:
            content = doc.get("content", doc.get("text", ""))
            doc_tokens_list.append(self._tokenize(content))
        
        # Document frequencies
        doc_freqs: Dict[str, int] = {}
        for tokens in doc_tokens_list:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freqs[token] = doc_freqs.get(token, 0) + 1
        
        # Average document length
        total_tokens = sum(len(tokens) for tokens in doc_tokens_list)
        avg_doc_len = total_tokens / len(documents) if documents else 1
        
        # Compute BM25 scores
        scored_docs = []
        for i, (doc, tokens) in enumerate(zip(documents, doc_tokens_list)):
            bm25_score = self._compute_bm25(
                query_tokens, tokens, doc_freqs,
                len(documents), avg_doc_len
            )
            
            scored_docs.append((doc, bm25_score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Create ranked documents
        results = []
        for rank, (doc, score) in enumerate(scored_docs[:top_k], 1):
            results.append(RankedDocument(
                content=doc.get("content", doc.get("text", "")),
                original_score=doc.get("score", 0.0),
                reranked_score=score,
                rank=rank,
                metadata=doc.get("metadata", {}),
                doc_id=doc.get("id"),
                source=doc.get("source")
            ))
        
        return results


class CrossEncoderReranker(RerankerStrategy):
    """
    Cross-Encoder tabanlı reranking
    
    Query ve document'ı birlikte encode ederek similarity hesaplar.
    Daha doğru ama daha yavaş.
    """
    
    def __init__(
        self,
        model_fn: Optional[Callable[[str, str], float]] = None,
        batch_size: int = 32
    ):
        """
        Args:
            model_fn: (query, document) -> similarity score döndüren fonksiyon
            batch_size: Batch processing için boyut
        """
        self.model_fn = model_fn
        self.batch_size = batch_size
    
    def _default_similarity(self, query: str, document: str) -> float:
        """
        Fallback similarity - keyword overlap
        Gerçek uygulamada bir cross-encoder model kullanılmalı
        """
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        
        if not query_words or not doc_words:
            return 0.0
        
        overlap = len(query_words & doc_words)
        return overlap / max(len(query_words), 1)
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        if not documents:
            return []
        
        scorer = self.model_fn or self._default_similarity
        
        # Score all documents
        scored_docs = []
        for doc in documents:
            content = doc.get("content", doc.get("text", ""))
            score = scorer(query, content)
            scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Create ranked documents
        results = []
        for rank, (doc, score) in enumerate(scored_docs[:top_k], 1):
            results.append(RankedDocument(
                content=doc.get("content", doc.get("text", "")),
                original_score=doc.get("score", 0.0),
                reranked_score=score,
                rank=rank,
                metadata=doc.get("metadata", {}),
                doc_id=doc.get("id"),
                source=doc.get("source")
            ))
        
        return results


class RRFReranker(RerankerStrategy):
    """
    Reciprocal Rank Fusion
    
    Birden fazla ranking listesini birleştirmek için kullanılır.
    """
    
    def __init__(self, k: int = 60):
        """
        Args:
            k: RRF constant (default 60)
        """
        self.k = k
    
    def _rrf_score(self, rank: int) -> float:
        """RRF skoru hesapla"""
        return 1 / (self.k + rank)
    
    def fuse(
        self,
        ranking_lists: List[List[Dict[str, Any]]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        """
        Birden fazla ranking listesini birleştir
        
        Args:
            ranking_lists: Her biri ranked document listesi olan listeler
            top_k: Döndürülecek sonuç sayısı
        """
        # Document ID -> aggregated score
        fused_scores: Dict[str, Tuple[float, Dict]] = {}
        
        for ranking in ranking_lists:
            for rank, doc in enumerate(ranking, 1):
                # Document identifier oluştur
                doc_id = doc.get("id") or hash(doc.get("content", doc.get("text", "")))
                doc_id = str(doc_id)
                
                rrf = self._rrf_score(rank)
                
                if doc_id in fused_scores:
                    current_score, current_doc = fused_scores[doc_id]
                    fused_scores[doc_id] = (current_score + rrf, current_doc)
                else:
                    fused_scores[doc_id] = (rrf, doc)
        
        # Sort by fused score
        sorted_docs = sorted(
            fused_scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )
        
        # Create ranked documents
        results = []
        for rank, (doc_id, (score, doc)) in enumerate(sorted_docs[:top_k], 1):
            results.append(RankedDocument(
                content=doc.get("content", doc.get("text", "")),
                original_score=doc.get("score", 0.0),
                reranked_score=score,
                rank=rank,
                metadata=doc.get("metadata", {}),
                doc_id=doc_id,
                source=doc.get("source")
            ))
        
        return results
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        """Tek liste için passthrough"""
        return self.fuse([documents], top_k)


class LLMReranker(RerankerStrategy):
    """
    LLM tabanlı reranking
    
    LLM'e query ve document'ları verip relevance puanı alır.
    """
    
    def __init__(
        self,
        llm_fn: Optional[Callable[[str], str]] = None,
        prompt_template: Optional[str] = None
    ):
        self.llm_fn = llm_fn
        self.prompt_template = prompt_template or """
Given the following query and document, rate the relevance on a scale of 0-10.
Only respond with a single number.

Query: {query}

Document: {document}

Relevance score (0-10):"""
    
    def _parse_score(self, response: str) -> float:
        """LLM yanıtından skor çıkar"""
        try:
            # İlk sayıyı bul
            numbers = re.findall(r'\d+(?:\.\d+)?', response)
            if numbers:
                score = float(numbers[0])
                return min(max(score / 10, 0), 1)  # Normalize to 0-1
        except:
            pass
        return 0.5  # Default
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        if not self.llm_fn or not documents:
            # Fallback: original order
            return [
                RankedDocument(
                    content=doc.get("content", doc.get("text", "")),
                    original_score=doc.get("score", 0.0),
                    reranked_score=doc.get("score", 0.0),
                    rank=i + 1,
                    metadata=doc.get("metadata", {}),
                    doc_id=doc.get("id"),
                    source=doc.get("source")
                )
                for i, doc in enumerate(documents[:top_k])
            ]
        
        # Score each document with LLM
        scored_docs = []
        for doc in documents:
            content = doc.get("content", doc.get("text", ""))
            
            # Truncate if too long
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            prompt = self.prompt_template.format(
                query=query,
                document=content
            )
            
            try:
                response = self.llm_fn(prompt)
                score = self._parse_score(response)
            except Exception as e:
                logger.error(f"LLM reranking error: {e}")
                score = doc.get("score", 0.5)
            
            scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Create ranked documents
        results = []
        for rank, (doc, score) in enumerate(scored_docs[:top_k], 1):
            results.append(RankedDocument(
                content=doc.get("content", doc.get("text", "")),
                original_score=doc.get("score", 0.0),
                reranked_score=score,
                rank=rank,
                metadata=doc.get("metadata", {}),
                doc_id=doc.get("id"),
                source=doc.get("source")
            ))
        
        return results


class EnsembleReranker(RerankerStrategy):
    """
    Ensemble reranking
    
    Birden fazla reranker'ı birleştirir.
    """
    
    def __init__(
        self,
        rerankers: List[Tuple[RerankerStrategy, float]],
        fusion_method: str = "weighted_sum"  # "weighted_sum" or "rrf"
    ):
        """
        Args:
            rerankers: (reranker, weight) tuple listesi
            fusion_method: Birleştirme yöntemi
        """
        self.rerankers = rerankers
        self.fusion_method = fusion_method
        self.rrf_reranker = RRFReranker()
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        if not documents:
            return []
        
        if self.fusion_method == "rrf":
            # Her reranker'dan sonuç al ve RRF ile birleştir
            all_rankings = []
            for reranker, _ in self.rerankers:
                ranked = reranker.rerank(query, documents, top_k=len(documents))
                # Convert back to dict format for RRF
                ranking = [
                    {
                        "content": r.content,
                        "score": r.reranked_score,
                        "id": r.doc_id,
                        "metadata": r.metadata,
                        "source": r.source
                    }
                    for r in ranked
                ]
                all_rankings.append(ranking)
            
            return self.rrf_reranker.fuse(all_rankings, top_k)
        
        else:  # weighted_sum
            # Document ID -> aggregated score
            doc_scores: Dict[str, Tuple[float, Dict]] = {}
            
            for reranker, weight in self.rerankers:
                ranked = reranker.rerank(query, documents, top_k=len(documents))
                
                for r in ranked:
                    doc_id = r.doc_id or hash(r.content)
                    doc_id = str(doc_id)
                    
                    weighted_score = r.reranked_score * weight
                    
                    if doc_id in doc_scores:
                        current_score, doc_data = doc_scores[doc_id]
                        doc_scores[doc_id] = (current_score + weighted_score, doc_data)
                    else:
                        doc_scores[doc_id] = (weighted_score, {
                            "content": r.content,
                            "metadata": r.metadata,
                            "source": r.source,
                            "original_score": r.original_score
                        })
            
            # Sort by aggregated score
            sorted_docs = sorted(
                doc_scores.items(),
                key=lambda x: x[1][0],
                reverse=True
            )
            
            # Create ranked documents
            results = []
            for rank, (doc_id, (score, data)) in enumerate(sorted_docs[:top_k], 1):
                results.append(RankedDocument(
                    content=data["content"],
                    original_score=data.get("original_score", 0.0),
                    reranked_score=score,
                    rank=rank,
                    metadata=data.get("metadata", {}),
                    doc_id=doc_id,
                    source=data.get("source")
                ))
            
            return results


class Reranker:
    """
    Main Reranker class
    
    Farklı stratejileri yönetir.
    """
    
    def __init__(
        self,
        strategy: Optional[RerankerStrategy] = None
    ):
        self.strategy = strategy or BM25Reranker()
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        """Dökümanları rerank et"""
        return self.strategy.rerank(query, documents, top_k)
    
    def set_strategy(self, strategy: RerankerStrategy):
        """Strateji değiştir"""
        self.strategy = strategy


# Global instance
reranker = Reranker()


__all__ = [
    "Reranker",
    "RerankerStrategy",
    "BM25Reranker",
    "CrossEncoderReranker",
    "RRFReranker",
    "LLMReranker",
    "EnsembleReranker",
    "RankedDocument",
    "reranker"
]
