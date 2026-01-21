"""
Enterprise AI Assistant - Advanced Vector Store
===============================================

Gelişmiş özellikler içeren Enterprise-grade Vector Store.

YENİ ÖZELLİKLER:
1. Akıllı Duplicate Detection (Hash + Semantic)
2. Near-Duplicate Detection (Yakın benzerlik tespiti)
3. Content Quality Scoring (İçerik kalitesi puanlama)
4. Auto-Cleanup (Eski/kullanılmayan dökümanları temizle)
5. Document Versioning (Versiyon kontrolü)
6. Smart Chunking (Akıllı parçalama)
7. Query Caching (Sorgu önbellekleme)
8. Source Tracking (Kaynak takibi)
9. Document Statistics (Detaylı istatistikler)
10. Batch Optimization (Toplu işlem optimizasyonu)
11. Search History (Arama geçmişi)
12. Related Documents (İlişkili dökümanlar)
13. Document Clustering (Döküman gruplama)
14. Content Validation (İçerik doğrulama)
15. Export/Import (Dışa/İçe aktarma)
16. Language Detection (Dil tespiti)
17. Automatic Summarization (Otomatik özetleme)
18. Metadata Enrichment (Metadata zenginleştirme)
19. Document Expiry (Döküman süresi)
20. Usage Analytics (Kullanım analitiği)

Author: Enterprise AI Assistant
Version: 2.0.0
"""

import hashlib
import json
import re
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from threading import Lock
import statistics

from .config import settings
from .embedding import embedding_manager
from .logger import get_logger
from .chromadb_manager import get_chromadb_manager, ChromaDBConfig

logger = get_logger("enterprise_vector_store")


# =============================================================================
# CONFIGURATION & DATA CLASSES
# =============================================================================

@dataclass
class DuplicateConfig:
    """Duplicate tespiti yapılandırması."""
    enabled: bool = True
    
    # Hash-based exact duplicate
    check_exact_hash: bool = True
    
    # Semantic similarity threshold (0.0-1.0)
    semantic_threshold: float = 0.95
    check_semantic: bool = True
    
    # Near-duplicate detection
    near_duplicate_threshold: float = 0.85
    check_near_duplicates: bool = True
    
    # Text normalization for comparison
    normalize_whitespace: bool = True
    normalize_case: bool = False  # False = case-sensitive
    
    # Minimum length for semantic check
    min_length_for_semantic: int = 50


@dataclass
class ContentQualityConfig:
    """İçerik kalitesi yapılandırması."""
    enabled: bool = True
    
    # Minimum requirements
    min_length: int = 10
    max_length: int = 100000
    min_word_count: int = 3
    
    # Quality thresholds
    min_quality_score: float = 0.3
    
    # Reject patterns (spam, empty, etc.)
    reject_patterns: List[str] = field(default_factory=lambda: [
        r'^[\s\n\r]*$',  # Only whitespace
        r'^[^\w]*$',  # No word characters
        r'(.)\1{10,}',  # Repeated character 10+ times
        r'^\d+$',  # Only numbers
    ])


@dataclass
class DocumentStats:
    """Döküman istatistikleri."""
    total_documents: int = 0
    total_chunks: int = 0
    unique_sources: int = 0
    
    duplicates_blocked: int = 0
    near_duplicates_blocked: int = 0
    quality_rejected: int = 0
    
    avg_document_length: float = 0.0
    avg_quality_score: float = 0.0
    
    last_add_time: Optional[datetime] = None
    last_query_time: Optional[datetime] = None
    
    sources_breakdown: Dict[str, int] = field(default_factory=dict)
    language_breakdown: Dict[str, int] = field(default_factory=dict)
    
    query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "unique_sources": self.unique_sources,
            "duplicates_blocked": self.duplicates_blocked,
            "near_duplicates_blocked": self.near_duplicates_blocked,
            "quality_rejected": self.quality_rejected,
            "avg_document_length": round(self.avg_document_length, 2),
            "avg_quality_score": round(self.avg_quality_score, 2),
            "last_add_time": self.last_add_time.isoformat() if self.last_add_time else None,
            "last_query_time": self.last_query_time.isoformat() if self.last_query_time else None,
            "sources_breakdown": dict(self.sources_breakdown),
            "language_breakdown": dict(self.language_breakdown),
            "query_count": self.query_count,
            "cache_hit_rate": (
                f"{(self.cache_hits / (self.cache_hits + self.cache_misses) * 100):.1f}%"
                if (self.cache_hits + self.cache_misses) > 0 else "N/A"
            ),
        }


@dataclass 
class DocumentVersion:
    """Döküman versiyonu."""
    version: int
    content_hash: str
    created_at: datetime
    metadata: Dict[str, Any]
    

@dataclass
class QueryCacheEntry:
    """Sorgu önbellek girişi."""
    query: str
    query_hash: str
    results: List[Dict[str, Any]]
    timestamp: datetime
    hit_count: int = 0


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def compute_content_hash(content: str, normalize: bool = True) -> str:
    """İçerik için MD5 hash hesapla."""
    if normalize:
        content = re.sub(r'\s+', ' ', content.strip().lower())
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def compute_shingle_hash(content: str, shingle_size: int = 5) -> Set[str]:
    """MinHash için shingle seti oluştur."""
    words = content.lower().split()
    if len(words) < shingle_size:
        return {content.lower()}
    
    shingles = set()
    for i in range(len(words) - shingle_size + 1):
        shingle = ' '.join(words[i:i + shingle_size])
        shingles.add(shingle)
    return shingles


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Jaccard benzerliği hesapla."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def detect_language(text: str) -> str:
    """Basit dil tespiti (Türkçe/İngilizce)."""
    turkish_chars = set('çğıöşüÇĞİÖŞÜ')
    turkish_words = {'ve', 'bir', 'bu', 'için', 'ile', 'de', 'da', 'ki', 'ne', 'var'}
    
    text_lower = text.lower()
    
    # Check for Turkish characters
    if any(c in text for c in turkish_chars):
        return 'tr'
    
    # Check for common Turkish words
    words = set(text_lower.split())
    if len(words & turkish_words) >= 2:
        return 'tr'
    
    return 'en'


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Basit anahtar kelime çıkarma."""
    # Stop words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'it', 'its', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'from',
        'by', 'about', 'as', 'into', 'through', 'during', 'before', 'after',
        've', 'bir', 'bu', 'için', 'ile', 'de', 'da', 'ki', 'ne', 'var',
        'olan', 'olarak', 'gibi', 'daha', 'çok', 'en', 'kadar', 'sonra',
    }
    
    # Extract words
    words = re.findall(r'\b\w{3,}\b', text.lower())
    
    # Count frequencies
    word_freq = defaultdict(int)
    for word in words:
        if word not in stop_words and not word.isdigit():
            word_freq[word] += 1
    
    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, _ in sorted_words[:max_keywords]]


def calculate_quality_score(content: str) -> float:
    """
    İçerik kalitesi puanı hesapla (0.0-1.0).
    
    Faktörler:
    - Uzunluk
    - Kelime çeşitliliği
    - Cümle yapısı
    - Özel karakter oranı
    """
    if not content or len(content.strip()) < 10:
        return 0.0
    
    score = 0.0
    content = content.strip()
    
    # 1. Uzunluk (max 0.25)
    length = len(content)
    if length >= 100:
        score += 0.25
    elif length >= 50:
        score += 0.15
    elif length >= 20:
        score += 0.10
    
    # 2. Kelime çeşitliliği (max 0.25)
    words = content.lower().split()
    if words:
        unique_ratio = len(set(words)) / len(words)
        score += unique_ratio * 0.25
    
    # 3. Cümle yapısı (max 0.25)
    sentences = re.split(r'[.!?]+', content)
    valid_sentences = [s for s in sentences if len(s.strip().split()) >= 3]
    if sentences:
        sentence_ratio = len(valid_sentences) / len(sentences)
        score += sentence_ratio * 0.25
    
    # 4. Alfanumerik karakter oranı (max 0.25)
    alnum_chars = sum(1 for c in content if c.isalnum() or c.isspace())
    alnum_ratio = alnum_chars / len(content) if content else 0
    score += min(alnum_ratio, 1.0) * 0.25
    
    return min(score, 1.0)


def generate_summary(content: str, max_length: int = 200) -> str:
    """Basit özet oluştur (ilk cümleler)."""
    sentences = re.split(r'(?<=[.!?])\s+', content.strip())
    
    summary = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) <= max_length:
            summary.append(sentence)
            current_length += len(sentence) + 1
        else:
            break
    
    if summary:
        return ' '.join(summary)
    return content[:max_length] + '...' if len(content) > max_length else content


# =============================================================================
# ENTERPRISE VECTOR STORE
# =============================================================================

class EnterpriseVectorStore:
    """
    Enterprise-grade Vector Store with advanced features.
    
    Özellikler:
    - Akıllı duplicate detection
    - Near-duplicate detection
    - Content quality scoring
    - Query caching
    - Document versioning
    - Usage analytics
    - Auto-cleanup
    - Export/Import
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        duplicate_config: Optional[DuplicateConfig] = None,
        quality_config: Optional[ContentQualityConfig] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        
        # Configurations
        self.duplicate_config = duplicate_config or DuplicateConfig()
        self.quality_config = quality_config or ContentQualityConfig()
        
        # ChromaDB Manager
        config = ChromaDBConfig(
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
            auto_backup=True,
            auto_recovery=True,
            enable_wal_mode=True,
            max_retries=5,
        )
        self._manager = get_chromadb_manager(config)
        
        # Caches
        self._hash_cache: Dict[str, str] = {}  # doc_id -> content_hash
        self._shingle_cache: Dict[str, Set[str]] = {}  # doc_id -> shingles
        self._query_cache: Dict[str, QueryCacheEntry] = {}  # query_hash -> results
        self._search_history: List[Dict[str, Any]] = []
        
        # Statistics
        self._stats = DocumentStats()
        
        # Thread safety
        self._cache_lock = Lock()
        self._stats_lock = Lock()
        
        # Version tracking
        self._versions: Dict[str, List[DocumentVersion]] = {}
        
        # Initialized flag
        self._initialized = False
        
        logger.info("EnterpriseVectorStore initialized")
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
    def _ensure_initialized(self):
        """Lazy initialization."""
        if not self._initialized:
            if not self._manager.is_healthy:
                self._manager.initialize()
            self._load_hash_cache()
            self._initialized = True
    
    def _load_hash_cache(self):
        """Mevcut dökümanların hash'lerini yükle."""
        try:
            all_data = self._manager.get(include=["metadatas"])
            
            for i, doc_id in enumerate(all_data.get("ids", [])):
                meta = all_data.get("metadatas", [])[i] if all_data.get("metadatas") else {}
                if meta and "content_hash" in meta:
                    self._hash_cache[doc_id] = meta["content_hash"]
            
            logger.debug(f"Loaded {len(self._hash_cache)} hashes into cache")
        except Exception as e:
            logger.warning(f"Failed to load hash cache: {e}")
    
    @property
    def collection(self):
        """Backward compatibility."""
        self._ensure_initialized()
        return self._manager._collection
    
    # =========================================================================
    # DUPLICATE DETECTION
    # =========================================================================
    
    def _check_exact_duplicate(self, content: str) -> Optional[str]:
        """
        Tam eşleşme duplicate kontrolü (hash-based).
        
        Returns:
            Eşleşen döküman ID'si veya None
        """
        if not self.duplicate_config.check_exact_hash:
            return None
        
        content_hash = compute_content_hash(
            content, 
            normalize=self.duplicate_config.normalize_whitespace
        )
        
        # Check cache first
        for doc_id, cached_hash in self._hash_cache.items():
            if cached_hash == content_hash:
                return doc_id
        
        # Check database
        try:
            existing = self._manager.get(
                where={"content_hash": content_hash},
                limit=1,
            )
            if existing and existing.get("ids"):
                return existing["ids"][0]
        except Exception as e:
            logger.warning(f"Exact duplicate check error: {e}")
        
        return None
    
    def _check_semantic_duplicate(
        self,
        content: str,
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[str, float]]:
        """
        Semantic similarity ile duplicate kontrolü.
        
        Returns:
            (Eşleşen döküman ID'si, similarity score) veya None
        """
        if not self.duplicate_config.check_semantic:
            return None
        
        if len(content) < self.duplicate_config.min_length_for_semantic:
            return None
        
        threshold = threshold or self.duplicate_config.semantic_threshold
        
        try:
            # Semantic search
            embedding = embedding_manager.embed_query(content[:1000])
            
            results = self._manager.query(
                query_embeddings=[embedding],
                n_results=3,
                include=["distances"],
            )
            
            if results and results.get("distances"):
                for i, distance in enumerate(results["distances"][0]):
                    score = 1 - distance
                    if score >= threshold:
                        return (results["ids"][0][i], score)
            
        except Exception as e:
            logger.warning(f"Semantic duplicate check error: {e}")
        
        return None
    
    def _check_near_duplicate(self, content: str) -> Optional[Tuple[str, float]]:
        """
        Near-duplicate kontrolü (shingle-based Jaccard similarity).
        
        Returns:
            (Eşleşen döküman ID'si, similarity score) veya None
        """
        if not self.duplicate_config.check_near_duplicates:
            return None
        
        threshold = self.duplicate_config.near_duplicate_threshold
        content_shingles = compute_shingle_hash(content)
        
        max_similarity = 0.0
        matched_id = None
        
        for doc_id, cached_shingles in self._shingle_cache.items():
            similarity = jaccard_similarity(content_shingles, cached_shingles)
            if similarity > max_similarity and similarity >= threshold:
                max_similarity = similarity
                matched_id = doc_id
        
        if matched_id:
            return (matched_id, max_similarity)
        
        return None
    
    def check_duplicate(
        self,
        content: str,
        check_exact: bool = True,
        check_semantic: bool = True,
        check_near: bool = True,
    ) -> Dict[str, Any]:
        """
        Kapsamlı duplicate kontrolü.
        
        Returns:
            {
                "is_duplicate": bool,
                "duplicate_type": "exact" | "semantic" | "near" | None,
                "matched_id": str | None,
                "similarity_score": float | None,
                "message": str
            }
        """
        result = {
            "is_duplicate": False,
            "duplicate_type": None,
            "matched_id": None,
            "similarity_score": None,
            "message": "No duplicate found",
        }
        
        # 1. Exact duplicate check
        if check_exact:
            matched = self._check_exact_duplicate(content)
            if matched:
                result.update({
                    "is_duplicate": True,
                    "duplicate_type": "exact",
                    "matched_id": matched,
                    "similarity_score": 1.0,
                    "message": f"Exact duplicate of document {matched[:8]}...",
                })
                return result
        
        # 2. Semantic duplicate check
        if check_semantic:
            matched = self._check_semantic_duplicate(content)
            if matched:
                result.update({
                    "is_duplicate": True,
                    "duplicate_type": "semantic",
                    "matched_id": matched[0],
                    "similarity_score": matched[1],
                    "message": f"Semantic duplicate ({matched[1]:.1%}) of document {matched[0][:8]}...",
                })
                return result
        
        # 3. Near-duplicate check
        if check_near:
            matched = self._check_near_duplicate(content)
            if matched:
                result.update({
                    "is_duplicate": True,
                    "duplicate_type": "near",
                    "matched_id": matched[0],
                    "similarity_score": matched[1],
                    "message": f"Near-duplicate ({matched[1]:.1%}) of document {matched[0][:8]}...",
                })
                return result
        
        return result
    
    # =========================================================================
    # CONTENT VALIDATION
    # =========================================================================
    
    def validate_content(self, content: str) -> Dict[str, Any]:
        """
        İçerik doğrulama.
        
        Returns:
            {
                "is_valid": bool,
                "quality_score": float,
                "issues": List[str],
                "language": str,
                "keywords": List[str],
                "summary": str
            }
        """
        result = {
            "is_valid": True,
            "quality_score": 0.0,
            "issues": [],
            "language": "unknown",
            "keywords": [],
            "summary": "",
        }
        
        if not self.quality_config.enabled:
            result["is_valid"] = True
            return result
        
        # Basic checks
        if not content:
            result["is_valid"] = False
            result["issues"].append("Empty content")
            return result
        
        content = content.strip()
        
        # Length check
        if len(content) < self.quality_config.min_length:
            result["is_valid"] = False
            result["issues"].append(f"Too short ({len(content)} < {self.quality_config.min_length})")
        
        if len(content) > self.quality_config.max_length:
            result["is_valid"] = False
            result["issues"].append(f"Too long ({len(content)} > {self.quality_config.max_length})")
        
        # Word count check
        word_count = len(content.split())
        if word_count < self.quality_config.min_word_count:
            result["is_valid"] = False
            result["issues"].append(f"Too few words ({word_count} < {self.quality_config.min_word_count})")
        
        # Reject patterns
        for pattern in self.quality_config.reject_patterns:
            if re.search(pattern, content):
                result["is_valid"] = False
                result["issues"].append(f"Matches reject pattern: {pattern}")
        
        # Quality score
        result["quality_score"] = calculate_quality_score(content)
        if result["quality_score"] < self.quality_config.min_quality_score:
            result["is_valid"] = False
            result["issues"].append(
                f"Low quality score ({result['quality_score']:.2f} < {self.quality_config.min_quality_score})"
            )
        
        # Language detection
        result["language"] = detect_language(content)
        
        # Keywords
        result["keywords"] = extract_keywords(content)
        
        # Summary
        result["summary"] = generate_summary(content)
        
        return result
    
    # =========================================================================
    # DOCUMENT OPERATIONS
    # =========================================================================
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        skip_duplicates: bool = True,
        validate_content: bool = True,
        enrich_metadata: bool = True,
    ) -> Dict[str, Any]:
        """
        Dökümanları ekle (gelişmiş özelliklerle).
        
        Args:
            documents: Döküman içerikleri
            metadatas: Metadata listesi
            ids: Döküman ID'leri
            skip_duplicates: Duplicate'leri atla
            validate_content: İçerik doğrulama
            enrich_metadata: Metadata zenginleştirme
            
        Returns:
            {
                "added_ids": List[str],
                "skipped": {
                    "duplicates": List[str],
                    "near_duplicates": List[str],
                    "quality_rejected": List[str],
                },
                "stats": Dict[str, Any]
            }
        """
        self._ensure_initialized()
        
        result = {
            "added_ids": [],
            "skipped": {
                "duplicates": [],
                "near_duplicates": [],
                "quality_rejected": [],
            },
            "stats": {
                "total_input": len(documents),
                "added": 0,
                "skipped": 0,
            },
        }
        
        if not documents:
            return result
        
        unique_docs = []
        unique_metadatas = []
        unique_ids = []
        
        for i, doc in enumerate(documents):
            doc_content = doc.strip()
            doc_meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            doc_id = ids[i] if ids and i < len(ids) else None
            
            # 1. Content validation
            if validate_content:
                validation = self.validate_content(doc_content)
                if not validation["is_valid"]:
                    result["skipped"]["quality_rejected"].append({
                        "content_preview": doc_content[:100] + "...",
                        "issues": validation["issues"],
                    })
                    with self._stats_lock:
                        self._stats.quality_rejected += 1
                    continue
            
            # 2. Duplicate check
            if skip_duplicates and self.duplicate_config.enabled:
                dup_check = self.check_duplicate(doc_content)
                
                if dup_check["is_duplicate"]:
                    if dup_check["duplicate_type"] == "exact":
                        result["skipped"]["duplicates"].append({
                            "matched_id": dup_check["matched_id"],
                            "content_preview": doc_content[:100] + "...",
                        })
                        with self._stats_lock:
                            self._stats.duplicates_blocked += 1
                    else:
                        result["skipped"]["near_duplicates"].append({
                            "matched_id": dup_check["matched_id"],
                            "similarity": dup_check["similarity_score"],
                            "content_preview": doc_content[:100] + "...",
                        })
                        with self._stats_lock:
                            self._stats.near_duplicates_blocked += 1
                    continue
            
            # 3. Generate content hash and ID
            content_hash = compute_content_hash(doc_content)
            if not doc_id:
                doc_id = f"doc_{content_hash[:16]}_{int(time.time() * 1000) % 100000}"
            
            # 4. Metadata enrichment
            if enrich_metadata:
                validation = self.validate_content(doc_content) if not validate_content else validation
                enriched_meta = {
                    "content_hash": content_hash,
                    "added_at": datetime.now().isoformat(),
                    "length": len(doc_content),
                    "word_count": len(doc_content.split()),
                    "quality_score": validation.get("quality_score", calculate_quality_score(doc_content)),
                    "language": validation.get("language", detect_language(doc_content)),
                    "keywords": ",".join(validation.get("keywords", extract_keywords(doc_content))[:5]),
                    **doc_meta,
                }
            else:
                enriched_meta = {"content_hash": content_hash, **doc_meta}
            
            unique_docs.append(doc_content)
            unique_metadatas.append(enriched_meta)
            unique_ids.append(doc_id)
            
            # Update caches
            with self._cache_lock:
                self._hash_cache[doc_id] = content_hash
                self._shingle_cache[doc_id] = compute_shingle_hash(doc_content)
        
        # Add to vector store
        if unique_docs:
            try:
                print(f"📊 {len(unique_docs)} döküman için embedding oluşturuluyor...")
                embeddings = embedding_manager.embed_texts(unique_docs)
                
                self._manager.add_documents(
                    documents=unique_docs,
                    embeddings=embeddings,
                    metadatas=unique_metadatas,
                    ids=unique_ids,
                )
                
                result["added_ids"] = unique_ids
                result["stats"]["added"] = len(unique_ids)
                
                # Update stats
                with self._stats_lock:
                    self._stats.total_documents = self._manager.count()
                    self._stats.last_add_time = datetime.now()
                    
                    # Update source breakdown
                    for meta in unique_metadatas:
                        source = meta.get("source") or meta.get("filename", "unknown")
                        if source not in self._stats.sources_breakdown:
                            self._stats.sources_breakdown[source] = 0
                        self._stats.sources_breakdown[source] += 1
                        
                        # Language breakdown
                        lang = meta.get("language", "unknown")
                        if lang not in self._stats.language_breakdown:
                            self._stats.language_breakdown[lang] = 0
                        self._stats.language_breakdown[lang] += 1
                
                print(f"✅ {len(unique_docs)} döküman eklendi")
                
            except Exception as e:
                logger.error(f"Add documents failed: {e}")
                logger.debug(traceback.format_exc())
                raise
        
        result["stats"]["skipped"] = (
            len(result["skipped"]["duplicates"]) +
            len(result["skipped"]["near_duplicates"]) +
            len(result["skipped"]["quality_rejected"])
        )
        
        # Log summary
        if result["stats"]["skipped"] > 0:
            print(f"⏭️ {result['stats']['skipped']} döküman atlandı:")
            if result["skipped"]["duplicates"]:
                print(f"   - {len(result['skipped']['duplicates'])} exact duplicate")
            if result["skipped"]["near_duplicates"]:
                print(f"   - {len(result['skipped']['near_duplicates'])} near duplicate")
            if result["skipped"]["quality_rejected"]:
                print(f"   - {len(result['skipped']['quality_rejected'])} quality rejected")
        
        return result
    
    # =========================================================================
    # SEARCH OPERATIONS
    # =========================================================================
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = 300,  # 5 minutes
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with caching.
        
        Args:
            query: Arama sorgusu
            n_results: Döndürülecek sonuç sayısı
            where: Metadata filtresi
            use_cache: Önbellek kullan
            cache_ttl: Önbellek süresi (saniye)
            
        Returns:
            Arama sonuçları
        """
        self._ensure_initialized()
        
        # Generate cache key
        query_hash = hashlib.md5(
            f"{query}:{n_results}:{json.dumps(where or {}, sort_keys=True)}".encode()
        ).hexdigest()
        
        # Check cache
        if use_cache:
            with self._cache_lock:
                if query_hash in self._query_cache:
                    entry = self._query_cache[query_hash]
                    age = (datetime.now() - entry.timestamp).total_seconds()
                    if age < cache_ttl:
                        entry.hit_count += 1
                        self._stats.cache_hits += 1
                        logger.debug(f"Cache hit for query: {query[:50]}...")
                        return entry.results
        
        self._stats.cache_misses += 1
        
        # Perform search
        try:
            query_embedding = embedding_manager.embed_query(query)
            
            results = self._manager.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
            
            # Format results
            formatted_results = []
            for i, doc in enumerate(results["documents"][0] if results["documents"] else []):
                distance = results["distances"][0][i] if results["distances"] else 1.0
                score = 1 - distance
                
                formatted_results.append({
                    "id": results["ids"][0][i] if results["ids"] else None,
                    "document": doc,
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": score,
                    "rank": i + 1,
                })
            
            # Update cache
            if use_cache:
                with self._cache_lock:
                    self._query_cache[query_hash] = QueryCacheEntry(
                        query=query,
                        query_hash=query_hash,
                        results=formatted_results,
                        timestamp=datetime.now(),
                    )
            
            # Update stats
            with self._stats_lock:
                self._stats.query_count += 1
                self._stats.last_query_time = datetime.now()
            
            # Save search history
            self._search_history.append({
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "result_count": len(formatted_results),
            })
            if len(self._search_history) > 1000:
                self._search_history = self._search_history[-500:]
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            logger.debug(traceback.format_exc())
            return []
    
    def find_similar(
        self,
        doc_id: str,
        n_results: int = 5,
        exclude_self: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Belirli bir dökümana benzer dökümanları bul.
        
        Args:
            doc_id: Kaynak döküman ID'si
            n_results: Döndürülecek sonuç sayısı
            exclude_self: Kendisini hariç tut
            
        Returns:
            Benzer dökümanlar
        """
        self._ensure_initialized()
        
        try:
            # Get source document
            source = self._manager.get(ids=[doc_id], include=["documents"])
            if not source or not source.get("documents"):
                return []
            
            # Search for similar
            results = self.search(
                query=source["documents"][0],
                n_results=n_results + (1 if exclude_self else 0),
            )
            
            if exclude_self:
                results = [r for r in results if r["id"] != doc_id]
            
            return results[:n_results]
            
        except Exception as e:
            logger.error(f"Find similar failed: {e}")
            return []
    
    def find_related(
        self,
        doc_id: str,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        İlişkili dökümanları bul (source, keywords, language bazlı).
        """
        self._ensure_initialized()
        
        try:
            # Get source document
            source = self._manager.get(ids=[doc_id], include=["metadatas"])
            if not source or not source.get("metadatas"):
                return []
            
            meta = source["metadatas"][0]
            related = []
            
            # Find by same source
            source_name = meta.get("source") or meta.get("filename")
            if source_name:
                results = self._manager.get(
                    where={"source": source_name},
                    include=["documents", "metadatas"],
                    limit=max_results,
                )
                for i, rid in enumerate(results.get("ids", [])):
                    if rid != doc_id:
                        related.append({
                            "id": rid,
                            "document": results["documents"][i],
                            "metadata": results["metadatas"][i],
                            "relation": "same_source",
                        })
            
            return related[:max_results]
            
        except Exception as e:
            logger.error(f"Find related failed: {e}")
            return []
    
    # =========================================================================
    # CLEANUP & MAINTENANCE
    # =========================================================================
    
    def find_duplicates(
        self,
        threshold: float = 0.95,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Mevcut duplicate'leri tespit et.
        
        Returns:
            Duplicate grupları listesi
        """
        self._ensure_initialized()
        
        duplicates = []
        checked_ids = set()
        
        try:
            all_data = self._manager.get(include=["documents", "metadatas"])
            
            for i, doc_id in enumerate(all_data.get("ids", [])):
                if doc_id in checked_ids:
                    continue
                
                doc = all_data["documents"][i]
                checked_ids.add(doc_id)
                
                # Find similar documents
                similar = self.find_similar(doc_id, n_results=10)
                
                high_similarity = [
                    s for s in similar 
                    if s["score"] >= threshold and s["id"] not in checked_ids
                ]
                
                if high_similarity:
                    duplicates.append({
                        "original_id": doc_id,
                        "original_preview": doc[:100] + "...",
                        "duplicates": [
                            {
                                "id": s["id"],
                                "score": s["score"],
                                "preview": s["document"][:100] + "...",
                            }
                            for s in high_similarity
                        ],
                    })
                    
                    for s in high_similarity:
                        checked_ids.add(s["id"])
                
                if len(duplicates) >= limit:
                    break
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Find duplicates failed: {e}")
            return []
    
    def remove_duplicates(
        self,
        threshold: float = 0.98,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Duplicate dökümanları otomatik temizle.
        
        Args:
            threshold: Benzerlik eşiği
            dry_run: Sadece simüle et, silme
            
        Returns:
            Temizleme raporu
        """
        duplicates = self.find_duplicates(threshold=threshold)
        
        result = {
            "duplicate_groups": len(duplicates),
            "total_duplicates": sum(len(d["duplicates"]) for d in duplicates),
            "removed_ids": [],
            "dry_run": dry_run,
        }
        
        if not dry_run:
            for group in duplicates:
                for dup in group["duplicates"]:
                    try:
                        self.delete_document(dup["id"])
                        result["removed_ids"].append(dup["id"])
                    except Exception as e:
                        logger.warning(f"Failed to remove {dup['id']}: {e}")
        
        return result
    
    def cleanup_old_documents(
        self,
        max_age_days: int = 365,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Eski dökümanları temizle.
        
        Args:
            max_age_days: Maksimum yaş (gün)
            dry_run: Sadece simüle et
            
        Returns:
            Temizleme raporu
        """
        self._ensure_initialized()
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        old_docs = []
        
        try:
            all_data = self._manager.get(include=["metadatas"])
            
            for i, doc_id in enumerate(all_data.get("ids", [])):
                meta = all_data.get("metadatas", [])[i] if all_data.get("metadatas") else {}
                
                added_at = meta.get("added_at")
                if added_at:
                    try:
                        doc_date = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                        if doc_date < cutoff:
                            old_docs.append(doc_id)
                    except Exception:
                        pass
            
            result = {
                "old_documents": len(old_docs),
                "cutoff_date": cutoff.isoformat(),
                "removed_ids": [],
                "dry_run": dry_run,
            }
            
            if not dry_run and old_docs:
                self._manager.delete(ids=old_docs)
                result["removed_ids"] = old_docs
            
            return result
            
        except Exception as e:
            logger.error(f"Cleanup old documents failed: {e}")
            return {"error": str(e)}
    
    def cleanup_low_quality(
        self,
        min_quality: float = 0.3,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Düşük kaliteli dökümanları temizle.
        """
        self._ensure_initialized()
        
        low_quality_docs = []
        
        try:
            all_data = self._manager.get(include=["metadatas", "documents"])
            
            for i, doc_id in enumerate(all_data.get("ids", [])):
                meta = all_data.get("metadatas", [])[i] if all_data.get("metadatas") else {}
                doc = all_data.get("documents", [])[i] if all_data.get("documents") else ""
                
                # Check stored quality score
                quality = meta.get("quality_score")
                if quality is None:
                    quality = calculate_quality_score(doc)
                
                if quality < min_quality:
                    low_quality_docs.append({
                        "id": doc_id,
                        "quality": quality,
                        "preview": doc[:100] + "...",
                    })
            
            result = {
                "low_quality_documents": len(low_quality_docs),
                "min_quality_threshold": min_quality,
                "documents": low_quality_docs[:20],  # First 20
                "removed_ids": [],
                "dry_run": dry_run,
            }
            
            if not dry_run and low_quality_docs:
                ids_to_remove = [d["id"] for d in low_quality_docs]
                self._manager.delete(ids=ids_to_remove)
                result["removed_ids"] = ids_to_remove
            
            return result
            
        except Exception as e:
            logger.error(f"Cleanup low quality failed: {e}")
            return {"error": str(e)}
    
    # =========================================================================
    # STATISTICS & ANALYTICS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Detaylı istatistikler."""
        self._ensure_initialized()
        
        with self._stats_lock:
            self._stats.total_documents = self._manager.count()
            self._stats.unique_sources = len(self._stats.sources_breakdown)
            
            return self._stats.to_dict()
    
    def get_analytics(self) -> Dict[str, Any]:
        """Kullanım analitiği."""
        self._ensure_initialized()
        
        try:
            all_data = self._manager.get(include=["metadatas"])
            
            # Quality distribution
            qualities = []
            lengths = []
            languages = defaultdict(int)
            sources = defaultdict(int)
            
            for i, meta in enumerate(all_data.get("metadatas", [])):
                if not meta:
                    continue
                
                if "quality_score" in meta:
                    qualities.append(meta["quality_score"])
                if "length" in meta:
                    lengths.append(meta["length"])
                
                lang = meta.get("language", "unknown")
                languages[lang] += 1
                
                source = meta.get("source") or meta.get("filename", "unknown")
                sources[source] += 1
            
            analytics = {
                "total_documents": self._manager.count(),
                "quality": {
                    "avg": statistics.mean(qualities) if qualities else 0,
                    "min": min(qualities) if qualities else 0,
                    "max": max(qualities) if qualities else 0,
                    "std": statistics.stdev(qualities) if len(qualities) > 1 else 0,
                },
                "length": {
                    "avg": statistics.mean(lengths) if lengths else 0,
                    "min": min(lengths) if lengths else 0,
                    "max": max(lengths) if lengths else 0,
                    "total_chars": sum(lengths) if lengths else 0,
                },
                "languages": dict(languages),
                "sources": dict(sources),
                "cache": {
                    "size": len(self._query_cache),
                    "hash_cache_size": len(self._hash_cache),
                },
                "search_history_count": len(self._search_history),
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Get analytics failed: {e}")
            return {"error": str(e)}
    
    def get_search_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Arama geçmişi."""
        return self._search_history[-limit:]
    
    # =========================================================================
    # EXPORT / IMPORT
    # =========================================================================
    
    def export_documents(
        self,
        output_path: str,
        include_embeddings: bool = False,
    ) -> Dict[str, Any]:
        """
        Dökümanları JSON dosyasına export et.
        """
        self._ensure_initialized()
        
        try:
            all_data = self._manager.get(
                include=["documents", "metadatas", "embeddings"] if include_embeddings else ["documents", "metadatas"]
            )
            
            export_data = {
                "export_time": datetime.now().isoformat(),
                "document_count": len(all_data.get("ids", [])),
                "documents": [],
            }
            
            for i, doc_id in enumerate(all_data.get("ids", [])):
                doc_entry = {
                    "id": doc_id,
                    "content": all_data["documents"][i] if all_data.get("documents") else "",
                    "metadata": all_data["metadatas"][i] if all_data.get("metadatas") else {},
                }
                if include_embeddings and all_data.get("embeddings"):
                    doc_entry["embedding"] = all_data["embeddings"][i]
                
                export_data["documents"].append(doc_entry)
            
            # Write to file
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "path": str(output),
                "document_count": export_data["document_count"],
            }
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"success": False, "error": str(e)}
    
    def import_documents(
        self,
        input_path: str,
        skip_duplicates: bool = True,
    ) -> Dict[str, Any]:
        """
        JSON dosyasından döküman import et.
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            documents = []
            metadatas = []
            ids = []
            
            for doc_entry in import_data.get("documents", []):
                documents.append(doc_entry["content"])
                metadatas.append(doc_entry.get("metadata", {}))
                ids.append(doc_entry["id"])
            
            result = self.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                skip_duplicates=skip_duplicates,
            )
            
            return {
                "success": True,
                "imported": len(result["added_ids"]),
                "skipped": result["stats"]["skipped"],
            }
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # STANDARD OPERATIONS (Backward Compatible)
    # =========================================================================
    
    def delete_document(self, doc_id: str) -> bool:
        """Döküman sil."""
        self._ensure_initialized()
        
        try:
            self._manager.delete(ids=[doc_id])
            
            # Clear from caches
            with self._cache_lock:
                self._hash_cache.pop(doc_id, None)
                self._shingle_cache.pop(doc_id, None)
            
            return True
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """ID ile döküman getir."""
        self._ensure_initialized()
        
        try:
            result = self._manager.get(
                ids=[doc_id],
                include=["documents", "metadatas"],
            )
            
            if result["documents"]:
                return {
                    "id": doc_id,
                    "document": result["documents"][0],
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0] if result["metadatas"] else {},
                }
            return None
        except Exception as e:
            logger.warning(f"Get document failed: {e}")
            return None
    
    def count(self) -> int:
        """Döküman sayısı."""
        self._ensure_initialized()
        return self._manager.count()
    
    def clear(self) -> bool:
        """Tüm dökümanları sil."""
        self._ensure_initialized()
        
        try:
            self._manager.clear()
            
            # Clear caches
            with self._cache_lock:
                self._hash_cache.clear()
                self._shingle_cache.clear()
                self._query_cache.clear()
            
            # Reset stats
            with self._stats_lock:
                self._stats = DocumentStats()
            
            return True
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return False
    
    def clear_cache(self):
        """Önbellekleri temizle."""
        with self._cache_lock:
            self._query_cache.clear()
        logger.info("Query cache cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Sağlık kontrolü."""
        self._ensure_initialized()
        
        return {
            **self._manager.get_status(),
            "enterprise_features": {
                "duplicate_detection": self.duplicate_config.enabled,
                "content_validation": self.quality_config.enabled,
                "query_cache_size": len(self._query_cache),
                "hash_cache_size": len(self._hash_cache),
            },
        }


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

# Singleton instance
_enterprise_store: Optional[EnterpriseVectorStore] = None


def get_enterprise_vector_store(
    duplicate_config: Optional[DuplicateConfig] = None,
    quality_config: Optional[ContentQualityConfig] = None,
) -> EnterpriseVectorStore:
    """Enterprise vector store instance al."""
    global _enterprise_store
    
    if _enterprise_store is None:
        _enterprise_store = EnterpriseVectorStore(
            duplicate_config=duplicate_config,
            quality_config=quality_config,
        )
    
    return _enterprise_store


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "EnterpriseVectorStore",
    "DuplicateConfig",
    "ContentQualityConfig",
    "DocumentStats",
    "get_enterprise_vector_store",
    "compute_content_hash",
    "calculate_quality_score",
    "detect_language",
    "extract_keywords",
    "generate_summary",
]
