"""
Document Reranker
=================

Endüstri standartlarında döküman reranking sistemi.
Cross-encoder ve diğer reranking stratejileri.

Features:
- GPU-Accelerated Cross-encoder reranking
- BM25 reranking
- Reciprocal Rank Fusion (RRF)
- Cohere-style reranking
- Custom scoring functions

GPU OPTIMIZATION (RTX 4070 8GB):
- CUDA acceleration for CrossEncoder
- Batch processing for efficiency
- FP16 inference for speed
- Config-driven settings
"""

import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.logger import get_logger
from core.config import settings

logger = get_logger("reranker")

# GPU Detection
try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
    GPU_DEVICE = "cuda" if CUDA_AVAILABLE else "cpu"
except ImportError:
    CUDA_AVAILABLE = False
    GPU_DEVICE = "cpu"

# CrossEncoder for GPU reranking
try:
    from sentence_transformers import CrossEncoder
    CROSSENCODER_AVAILABLE = True
except ImportError:
    CROSSENCODER_AVAILABLE = False

# Config-driven settings
RERANKER_BATCH_SIZE = getattr(settings, 'GPU_RERANKER_BATCH_SIZE', 32)
RERANKER_MODEL = getattr(settings, 'GPU_RERANKER_MODEL', 'multilingual')


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
    GPU-Accelerated Cross-Encoder tabanlı reranking
    
    Query ve document'ı birlikte encode ederek similarity hesaplar.
    Daha doğru ama daha yavaş - GPU ile hızlandırılmış.
    
    GPU OPTIMIZATION:
    - CUDA acceleration
    - FP16 inference
    - Batch processing
    - Config-driven settings
    """
    
    # GPU-optimized CrossEncoder models - Quality Rankings
    CROSSENCODER_MODELS = {
        "default": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # Fast, good quality
        "multilingual": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",  # Multi-language, BEST for Turkish
        "large": "cross-encoder/ms-marco-MiniLM-L-12-v2",  # Better quality, slower
    }
    
    def __init__(
        self,
        model_fn: Optional[Callable[[str, str], float]] = None,
        batch_size: int = None,  # None = use config
        use_embeddings: bool = True,
        use_gpu: bool = True,
        crossencoder_model: str = None  # None = use config (RERANKER_MODEL)
    ):
        """
        Args:
            model_fn: (query, document) -> similarity score döndüren fonksiyon
            batch_size: Batch processing için boyut (None = config'den al)
            use_embeddings: Gerçek embedding similarity kullan (varsayılan: True)
            use_gpu: GPU kullan (varsayılan: True)
            crossencoder_model: CrossEncoder model ismi (None = config'den al)
        """
        self.model_fn = model_fn
        self.batch_size = batch_size or RERANKER_BATCH_SIZE  # Config'den al
        self.use_embeddings = use_embeddings
        self._embedding_manager = None
        
        # GPU CrossEncoder - Use config model if not specified
        crossencoder_model = crossencoder_model or RERANKER_MODEL
        self._use_gpu = use_gpu and CUDA_AVAILABLE and CROSSENCODER_AVAILABLE
        self._crossencoder_model_name = self.CROSSENCODER_MODELS.get(
            crossencoder_model, crossencoder_model
        )
        self._crossencoder = None
        
        if self._use_gpu:
            self._init_crossencoder()
    
    def _init_crossencoder(self):
        """Initialize GPU CrossEncoder model"""
        if not CROSSENCODER_AVAILABLE:
            logger.warning("CrossEncoder not available, falling back to embedding similarity")
            return
        
        try:
            logger.info(f"🚀 CrossEncoder GPU yükleniyor: {self._crossencoder_model_name}")
            
            # Offline modda çalış - HuggingFace Hub'a bağlanma
            import os
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # Önce local_files_only ile dene
            try:
                self._crossencoder = CrossEncoder(
                    self._crossencoder_model_name,
                    device=GPU_DEVICE,
                    trust_remote_code=False,
                    local_files_only=True
                )
            except OSError as cache_error:
                # Model cache'de yok, internet varsa indir
                logger.warning(f"Model cache'de yok, indiriliyor: {cache_error}")
                os.environ.pop('HF_HUB_OFFLINE', None)
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
                
                self._crossencoder = CrossEncoder(
                    self._crossencoder_model_name,
                    device=GPU_DEVICE,
                    trust_remote_code=False
                )
                
                # Başarılı indirmeden sonra tekrar offline mode
                os.environ['HF_HUB_OFFLINE'] = '1'
                os.environ['TRANSFORMERS_OFFLINE'] = '1'
            
            # FP16 for faster inference
            if CUDA_AVAILABLE:
                self._crossencoder.model.half()
            
            logger.info(f"✅ CrossEncoder GPU hazır! Device: {GPU_DEVICE}")
            
        except Exception as e:
            logger.warning(f"CrossEncoder yüklenemedi: {e}")
            self._crossencoder = None
            self._use_gpu = False
    
    def _get_embedding_manager(self):
        """Lazy loading for embedding manager"""
        if self._embedding_manager is None:
            try:
                from core.embedding_manager import embedding_manager
                self._embedding_manager = embedding_manager
            except ImportError:
                self._embedding_manager = False  # Mark as unavailable
        return self._embedding_manager if self._embedding_manager else None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Cosine similarity hesapla"""
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _embedding_similarity(self, query: str, document: str) -> float:
        """
        Gerçek embedding-based similarity
        Embedding manager kullanarak cosine similarity hesaplar
        """
        emb_manager = self._get_embedding_manager()
        if not emb_manager:
            return self._keyword_similarity(query, document)
        
        try:
            # Embed both texts
            embeddings = emb_manager.embed_texts([query, document])
            query_emb = embeddings[0]
            doc_emb = embeddings[1]
            
            # Cosine similarity
            return self._cosine_similarity(query_emb, doc_emb)
        except Exception as e:
            logger.warning(f"Embedding similarity failed, falling back to keyword: {e}")
            return self._keyword_similarity(query, document)
    
    def _keyword_similarity(self, query: str, document: str) -> float:
        """
        Fallback similarity - keyword overlap with TF-IDF weighting
        """
        import math
        
        query_words = query.lower().split()
        doc_words = document.lower().split()
        
        if not query_words or not doc_words:
            return 0.0
        
        query_set = set(query_words)
        doc_set = set(doc_words)
        
        # Jaccard similarity (better than simple overlap)
        intersection = len(query_set & doc_set)
        union = len(query_set | doc_set)
        
        if union == 0:
            return 0.0
        
        jaccard = intersection / union
        
        # Boost for exact phrase matches
        query_str = query.lower()
        doc_str = document.lower()
        
        phrase_boost = 0.0
        for i in range(len(query_words) - 1):
            phrase = f"{query_words[i]} {query_words[i+1]}"
            if phrase in doc_str:
                phrase_boost += 0.1
        
        return min(jaccard + phrase_boost, 1.0)
    
    def _default_similarity(self, query: str, document: str) -> float:
        """
        Default similarity function
        Uses embeddings if available, otherwise falls back to keyword matching
        """
        if self.use_embeddings:
            return self._embedding_similarity(query, document)
        return self._keyword_similarity(query, document)
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[RankedDocument]:
        if not documents:
            return []
        
        # Helper: Extract content from document (handles both dict and string)
        def get_content(doc):
            if isinstance(doc, str):
                return doc
            return doc.get("content", doc.get("text", ""))
        
        # GPU CrossEncoder reranking (fastest, most accurate)
        if self._use_gpu and self._crossencoder is not None:
            try:
                # Prepare query-document pairs for batch scoring
                contents = [get_content(doc) for doc in documents]
                pairs = [[query, content] for content in contents]
                
                # GPU batch scoring
                with torch.no_grad():
                    scores = self._crossencoder.predict(
                        pairs,
                        batch_size=self.batch_size,
                        show_progress_bar=False
                    )
                
                # Pair documents with scores
                scored_docs = list(zip(documents, scores.tolist() if hasattr(scores, 'tolist') else list(scores)))
                
            except Exception as e:
                logger.warning(f"GPU reranking failed, falling back: {e}")
                scorer = self.model_fn or self._default_similarity
                scored_docs = [(doc, scorer(query, get_content(doc))) for doc in documents]
        else:
            # Fallback to embedding/keyword similarity
            scorer = self.model_fn or self._default_similarity
            scored_docs = [(doc, scorer(query, get_content(doc))) for doc in documents]
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Helper: Get dict field safely
        def get_field(doc, field, default=None):
            if isinstance(doc, str):
                return default
            return doc.get(field, default)
        
        # Create ranked documents
        results = []
        for rank, (doc, score) in enumerate(scored_docs[:top_k], 1):
            results.append(RankedDocument(
                content=get_content(doc),
                original_score=get_field(doc, "score", 0.0),
                reranked_score=float(score),
                rank=rank,
                metadata=get_field(doc, "metadata", {}),
                doc_id=get_field(doc, "id"),
                source=get_field(doc, "source")
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
    
    def get_status(self) -> Dict[str, Any]:
        """Reranker durumu"""
        return {
            "strategy": self.strategy.__class__.__name__,
            "gpu_available": CUDA_AVAILABLE,
            "crossencoder_available": CROSSENCODER_AVAILABLE,
            "device": GPU_DEVICE,
            "batch_size": RERANKER_BATCH_SIZE,
            "model": RERANKER_MODEL
        }


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
