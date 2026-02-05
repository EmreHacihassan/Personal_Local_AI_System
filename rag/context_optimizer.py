"""
🎯 RAG Context Optimizer
========================

Context window optimizasyonu ve doküman sıkıştırma.
Token limitleri içinde maksimum bilgi yoğunluğu sağlar.

Features:
- Intelligent context compression
- Relevance-based selection
- Redundancy elimination
- Hierarchical summarization
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """Sıkıştırma stratejisi."""
    TRUNCATE = "truncate"  # Basit kesme
    EXTRACTIVE = "extractive"  # Önemli cümleleri çıkar
    HIERARCHICAL = "hierarchical"  # Hiyerarşik özet
    SEMANTIC = "semantic"  # Semantic deduplication


@dataclass
class OptimizedContext:
    """Optimize edilmiş context."""
    content: str
    original_token_count: int
    optimized_token_count: int
    compression_ratio: float
    sources_used: int
    sources_total: int
    strategy_used: CompressionStrategy
    quality_score: float


@dataclass
class OptimizerConfig:
    """Optimizer konfigürasyonu."""
    max_context_tokens: int = 4096
    min_chunk_tokens: int = 100
    overlap_threshold: float = 0.7
    sentence_importance_threshold: float = 0.3
    preserve_structure: bool = True


class ContextOptimizer:
    """
    RAG context optimizer.
    
    Token limitleri içinde maksimum bilgi sağlar.
    """
    
    def __init__(self, config: Optional[OptimizerConfig] = None):
        self.config = config or OptimizerConfig()
        
        # Basit token tahmini (tiktoken unavailable ise)
        self._avg_chars_per_token = 4
        
        # Önemli kelimeler (Türkçe + İngilizce)
        self.importance_markers = {
            "important", "key", "critical", "main", "primary",
            "önemli", "ana", "temel", "kritik", "asıl",
            "conclusion", "summary", "result", "finding",
            "sonuç", "özet", "bulgu", "therefore", "thus",
            "dolayısıyla", "bu nedenle", "sonuç olarak"
        }
        
        # Stop words for deduplication
        self.stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may",
            "might", "must", "shall", "can", "need", "dare",
            "ve", "ile", "için", "bu", "bir", "da", "de",
            "olan", "olarak", "gibi", "kadar", "daha"
        }
    
    def optimize(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_tokens: Optional[int] = None,
        strategy: CompressionStrategy = CompressionStrategy.EXTRACTIVE
    ) -> OptimizedContext:
        """
        Dokümanları optimize et.
        
        Args:
            documents: RAG dokümanları
            query: Kullanıcı sorgusu
            max_tokens: Maksimum token limiti
            strategy: Sıkıştırma stratejisi
            
        Returns:
            Optimize edilmiş context
        """
        max_tokens = max_tokens or self.config.max_context_tokens
        
        if not documents:
            return OptimizedContext(
                content="",
                original_token_count=0,
                optimized_token_count=0,
                compression_ratio=1.0,
                sources_used=0,
                sources_total=0,
                strategy_used=strategy,
                quality_score=0.0
            )
        
        # 1. Original token count
        original_content = "\n\n".join(
            d.get("content", "") for d in documents
        )
        original_tokens = self._estimate_tokens(original_content)
        
        # 2. Seçilen stratejiye göre optimize et
        if strategy == CompressionStrategy.TRUNCATE:
            optimized, sources_used = self._optimize_truncate(
                documents, query, max_tokens
            )
        elif strategy == CompressionStrategy.EXTRACTIVE:
            optimized, sources_used = self._optimize_extractive(
                documents, query, max_tokens
            )
        elif strategy == CompressionStrategy.HIERARCHICAL:
            optimized, sources_used = self._optimize_hierarchical(
                documents, query, max_tokens
            )
        elif strategy == CompressionStrategy.SEMANTIC:
            optimized, sources_used = self._optimize_semantic(
                documents, query, max_tokens
            )
        else:
            optimized, sources_used = self._optimize_extractive(
                documents, query, max_tokens
            )
        
        # 3. Metrics
        optimized_tokens = self._estimate_tokens(optimized)
        compression_ratio = optimized_tokens / original_tokens if original_tokens > 0 else 1.0
        
        # 4. Quality score
        quality_score = self._calculate_quality(
            optimized, query, original_content
        )
        
        return OptimizedContext(
            content=optimized,
            original_token_count=original_tokens,
            optimized_token_count=optimized_tokens,
            compression_ratio=round(compression_ratio, 3),
            sources_used=sources_used,
            sources_total=len(documents),
            strategy_used=strategy,
            quality_score=round(quality_score, 3)
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Token sayısını tahmin et."""
        if not text:
            return 0
        return len(text) // self._avg_chars_per_token
    
    def _optimize_truncate(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Basit truncation stratejisi."""
        result_parts = []
        total_tokens = 0
        sources_used = 0
        
        for doc in documents:
            content = doc.get("content", "")
            content_tokens = self._estimate_tokens(content)
            
            if total_tokens + content_tokens <= max_tokens:
                result_parts.append(content)
                total_tokens += content_tokens
                sources_used += 1
            else:
                # Partial fit
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > self.config.min_chunk_tokens:
                    truncated = content[:remaining_tokens * self._avg_chars_per_token]
                    # Cümle sonunda kes
                    last_period = truncated.rfind(".")
                    if last_period > len(truncated) // 2:
                        truncated = truncated[:last_period + 1]
                    result_parts.append(truncated + "...")
                    sources_used += 1
                break
        
        return "\n\n".join(result_parts), sources_used
    
    def _optimize_extractive(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Extractive summarization stratejisi."""
        query_words = set(query.lower().split())
        
        # Tüm cümleleri topla ve skorla
        all_sentences = []
        for doc_idx, doc in enumerate(documents):
            content = doc.get("content", "")
            sentences = self._split_sentences(content)
            
            for sent_idx, sentence in enumerate(sentences):
                score = self._score_sentence(sentence, query_words, sent_idx)
                all_sentences.append({
                    "text": sentence,
                    "score": score,
                    "doc_idx": doc_idx,
                    "sent_idx": sent_idx
                })
        
        # Skora göre sırala
        all_sentences.sort(key=lambda x: x["score"], reverse=True)
        
        # Token limitine kadar ekle
        result_parts = []
        total_tokens = 0
        used_docs = set()
        
        for sent in all_sentences:
            sent_tokens = self._estimate_tokens(sent["text"])
            if total_tokens + sent_tokens > max_tokens:
                continue
            
            result_parts.append(sent)
            total_tokens += sent_tokens
            used_docs.add(sent["doc_idx"])
        
        # Original sıraya göre düzenle
        result_parts.sort(key=lambda x: (x["doc_idx"], x["sent_idx"]))
        
        # Group by document
        if self.config.preserve_structure:
            grouped = {}
            for sent in result_parts:
                doc_idx = sent["doc_idx"]
                if doc_idx not in grouped:
                    grouped[doc_idx] = []
                grouped[doc_idx].append(sent["text"])
            
            final_parts = [
                "\n".join(sents)
                for doc_idx, sents in sorted(grouped.items())
            ]
            return "\n\n".join(final_parts), len(grouped)
        
        return "\n".join(s["text"] for s in result_parts), len(used_docs)
    
    def _optimize_hierarchical(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Hierarchical summarization stratejisi."""
        # Her dokümanı özle
        summaries = []
        for doc in documents:
            content = doc.get("content", "")
            summary = self._extract_key_sentences(content, query, max_sentences=3)
            summaries.append(summary)
        
        # Token limiti kontrolü
        combined = "\n\n".join(summaries)
        if self._estimate_tokens(combined) <= max_tokens:
            return combined, len(documents)
        
        # Hala fazlaysa, en relevan olanları seç
        query_words = set(query.lower().split())
        scored = []
        for i, summary in enumerate(summaries):
            score = self._score_sentence(summary, query_words, 0)
            scored.append((i, summary, score))
        
        scored.sort(key=lambda x: x[2], reverse=True)
        
        result_parts = []
        total_tokens = 0
        used_count = 0
        
        for idx, summary, score in scored:
            summary_tokens = self._estimate_tokens(summary)
            if total_tokens + summary_tokens > max_tokens:
                break
            result_parts.append((idx, summary))
            total_tokens += summary_tokens
            used_count += 1
        
        # Original sıraya göre düzenle
        result_parts.sort(key=lambda x: x[0])
        return "\n\n".join(s for _, s in result_parts), used_count
    
    def _optimize_semantic(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_tokens: int
    ) -> Tuple[str, int]:
        """Semantic deduplication stratejisi."""
        # Cümleleri çıkar
        all_sentences = []
        for doc_idx, doc in enumerate(documents):
            content = doc.get("content", "")
            sentences = self._split_sentences(content)
            for sent in sentences:
                all_sentences.append({
                    "text": sent,
                    "doc_idx": doc_idx,
                    "words": set(sent.lower().split()) - self.stop_words
                })
        
        # Duplicate/similar cümleleri filtrele
        unique_sentences = []
        for sent in all_sentences:
            is_duplicate = False
            for existing in unique_sentences:
                similarity = self._jaccard_similarity(
                    sent["words"], existing["words"]
                )
                if similarity > self.config.overlap_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_sentences.append(sent)
        
        # Relevance skorla
        query_words = set(query.lower().split()) - self.stop_words
        for sent in unique_sentences:
            relevance = self._jaccard_similarity(sent["words"], query_words)
            sent["score"] = relevance
        
        # Skora göre sırala
        unique_sentences.sort(key=lambda x: x["score"], reverse=True)
        
        # Token limitine kadar ekle
        result_parts = []
        total_tokens = 0
        used_docs = set()
        
        for sent in unique_sentences:
            sent_tokens = self._estimate_tokens(sent["text"])
            if total_tokens + sent_tokens > max_tokens:
                continue
            
            result_parts.append(sent)
            total_tokens += sent_tokens
            used_docs.add(sent["doc_idx"])
        
        return "\n".join(s["text"] for s in result_parts), len(used_docs)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Metni cümlelere ayır."""
        # Basit cümle ayırıcı
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _score_sentence(
        self,
        sentence: str,
        query_words: set,
        position: int
    ) -> float:
        """Cümle önem skoru hesapla."""
        sent_lower = sentence.lower()
        sent_words = set(sent_lower.split())
        
        # 1. Query overlap
        overlap = len(query_words & sent_words) / max(len(query_words), 1)
        
        # 2. Importance markers
        importance_bonus = sum(
            0.1 for marker in self.importance_markers
            if marker in sent_lower
        )
        
        # 3. Position penalty (başlangıç ve son cümleler önemli)
        position_score = 1.0 if position < 3 else 0.8
        
        # 4. Length factor (çok kısa/uzun cümleler daha az değerli)
        word_count = len(sent_words)
        if word_count < 5:
            length_factor = 0.5
        elif word_count > 50:
            length_factor = 0.7
        else:
            length_factor = 1.0
        
        return (overlap * 0.5 + importance_bonus + 
                position_score * 0.2 + length_factor * 0.1)
    
    def _extract_key_sentences(
        self,
        text: str,
        query: str,
        max_sentences: int = 3
    ) -> str:
        """Key cümleleri çıkar."""
        sentences = self._split_sentences(text)
        if len(sentences) <= max_sentences:
            return text
        
        query_words = set(query.lower().split())
        scored = []
        for i, sent in enumerate(sentences):
            score = self._score_sentence(sent, query_words, i)
            scored.append((i, sent, score))
        
        # Top sentences
        scored.sort(key=lambda x: x[2], reverse=True)
        top = scored[:max_sentences]
        
        # Original order
        top.sort(key=lambda x: x[0])
        return " ".join(s for _, s, _ in top)
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """Jaccard similarity hesapla."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
    
    def _calculate_quality(
        self,
        optimized: str,
        query: str,
        original: str
    ) -> float:
        """Optimizasyon kalite skoru."""
        if not optimized:
            return 0.0
        
        opt_words = set(optimized.lower().split()) - self.stop_words
        query_words = set(query.lower().split()) - self.stop_words
        orig_words = set(original.lower().split()) - self.stop_words
        
        # Query coverage
        query_coverage = len(query_words & opt_words) / max(len(query_words), 1)
        
        # Information retention
        retention = len(orig_words & opt_words) / max(len(orig_words), 1)
        
        # Balance
        return (query_coverage * 0.6 + retention * 0.4)


class ContextBuilder:
    """
    LLM için context oluşturucu.
    """
    
    def __init__(
        self,
        optimizer: Optional[ContextOptimizer] = None
    ):
        self.optimizer = optimizer or ContextOptimizer()
        
    def build_context(
        self,
        documents: List[Dict[str, Any]],
        query: str,
        max_tokens: int = 4096,
        include_metadata: bool = True,
        format_style: str = "numbered"  # "numbered", "bullet", "plain"
    ) -> str:
        """
        LLM için formatlanmış context oluştur.
        
        Args:
            documents: RAG dokümanları
            query: Kullanıcı sorgusu
            max_tokens: Token limiti
            include_metadata: Metadata ekle
            format_style: Format stili
            
        Returns:
            Formatlanmış context
        """
        # Önce optimize et
        optimized = self.optimizer.optimize(
            documents, query, max_tokens,
            strategy=CompressionStrategy.EXTRACTIVE
        )
        
        # Format
        if format_style == "numbered":
            return self._format_numbered(documents, optimized)
        elif format_style == "bullet":
            return self._format_bullet(documents, optimized)
        else:
            return optimized.content
    
    def _format_numbered(
        self,
        documents: List[Dict[str, Any]],
        optimized: OptimizedContext
    ) -> str:
        """Numaralı format."""
        parts = ["Related Information:"]
        
        # Split by document markers
        sections = optimized.content.split("\n\n")
        
        for i, section in enumerate(sections, 1):
            if section.strip():
                parts.append(f"\n[{i}] {section.strip()}")
        
        return "\n".join(parts)
    
    def _format_bullet(
        self,
        documents: List[Dict[str, Any]],
        optimized: OptimizedContext
    ) -> str:
        """Bullet format."""
        parts = ["Related Information:"]
        
        sentences = optimized.content.split("\n")
        for sent in sentences:
            if sent.strip():
                parts.append(f"• {sent.strip()}")
        
        return "\n".join(parts)


# Singleton instances
context_optimizer = ContextOptimizer()
context_builder = ContextBuilder(context_optimizer)
