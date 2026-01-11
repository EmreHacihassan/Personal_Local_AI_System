"""
Enterprise AI Assistant - Retriever
Endüstri Standartlarında Kurumsal AI Çözümü

Akıllı bilgi getirme - semantic search, hybrid search, reranking.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import sys
sys.path.append('..')

from core.config import settings
from core.vector_store import vector_store
from core.llm_manager import llm_manager


@dataclass
class RetrievalResult:
    """Retrieval sonuç yapısı."""
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source": self.source,
        }


class Retriever:
    """
    Bilgi getirme sınıfı - Endüstri standartlarına uygun.
    
    Stratejiler:
    - Semantic: Vector similarity search
    - Keyword: BM25 tabanlı arama
    - Hybrid: Semantic + Keyword birleşimi
    - Multi-Query: Query expansion ile arama
    """
    
    def __init__(
        self,
        top_k: Optional[int] = None,
        score_threshold: float = 0.3,
    ):
        self.top_k = top_k or settings.TOP_K_RESULTS
        self.score_threshold = score_threshold
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        strategy: str = "semantic",
    ) -> List[RetrievalResult]:
        """
        Sorguya göre ilgili dökümanları getir.
        
        Args:
            query: Arama sorgusu
            top_k: Döndürülecek sonuç sayısı
            filter_metadata: Metadata filtresi
            strategy: Arama stratejisi (semantic, hybrid, multi_query)
            
        Returns:
            RetrievalResult listesi
        """
        k = top_k or self.top_k
        
        if strategy == "semantic":
            return self._semantic_search(query, k, filter_metadata)
        elif strategy == "hybrid":
            return self._hybrid_search(query, k, filter_metadata)
        elif strategy == "multi_query":
            return self._multi_query_search(query, k, filter_metadata)
        else:
            return self._semantic_search(query, k, filter_metadata)
    
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


# Singleton instance
retriever = Retriever()
