"""
Enterprise AI Assistant - Embedding Manager
Endüstri Standartlarında Kurumsal AI Çözümü

Ollama tabanlı embedding üretimi - döküman ve sorgu vektörizasyonu.
"""

import hashlib
import threading
from typing import List, Optional, Dict, Tuple
from collections import OrderedDict
import ollama
import numpy as np

from .config import settings


class EmbeddingCache:
    """
    Thread-safe LRU embedding cache.
    
    Embedding hesaplaması pahalı bir işlem olduğundan,
    sık kullanılan sorgu/dokümanlar için cache tutulur.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, List[float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def _hash_text(self, text: str) -> str:
        """Metin için unique hash oluştur."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:32]
    
    def get(self, text: str) -> Optional[List[float]]:
        """Cache'den embedding al."""
        key = self._hash_text(text)
        with self._lock:
            if key in self._cache:
                # LRU: Move to end
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            self._misses += 1
            return None
    
    def set(self, text: str, embedding: List[float]) -> None:
        """Embedding'i cache'e ekle."""
        key = self._hash_text(text)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    # Remove oldest
                    self._cache.popitem(last=False)
                self._cache[key] = embedding
    
    def clear(self) -> None:
        """Cache'i temizle."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, any]:
        """Cache istatistiklerini döndür."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }


class EmbeddingManager:
    """
    Embedding yönetim sınıfı - Endüstri standartlarına uygun.
    
    Özellikler:
    - Ollama embedding modeli desteği
    - Batch processing
    - Normalization
    - LRU Caching (performans için)
    """
    
    # Cache sabitleri
    CACHE_MAX_SIZE = 2000  # Maksimum cache girişi
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        enable_cache: bool = True,
    ):
        self.model_name = model_name or settings.OLLAMA_EMBEDDING_MODEL
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.client = ollama.Client(host=self.base_url)
        self.dimension = settings.EMBEDDING_DIMENSION
        
        # Cache
        self._cache_enabled = enable_cache
        self._cache = EmbeddingCache(max_size=self.CACHE_MAX_SIZE) if enable_cache else None
    
    def check_model_available(self) -> bool:
        """Embedding model'in mevcut olup olmadığını kontrol et."""
        try:
            result = self.client.list()
            # Handle both old (dict) and new (object) API formats
            if hasattr(result, 'models'):
                # New API: result.models is a list of Model objects
                available_models = [m.model for m in result.models]
            elif isinstance(result, dict):
                # Old API: result is a dict with 'models' key
                available_models = [m["name"] for m in result.get("models", [])]
            else:
                available_models = []
            
            return any(
                self.model_name in m or m.startswith(self.model_name.split(":")[0])
                for m in available_models
            )
        except Exception:
            return False
    
    def pull_model(self) -> bool:
        """Embedding model'ini indir."""
        try:
            print(f"📥 Embedding model indiriliyor: {self.model_name}")
            self.client.pull(self.model_name)
            print(f"✅ Embedding model indirildi: {self.model_name}")
            return True
        except Exception as e:
            print(f"❌ Embedding model indirilemedi: {e}")
            return False
    
    def ensure_model(self) -> bool:
        """Model'in mevcut olduğundan emin ol."""
        if not self.check_model_available():
            return self.pull_model()
        return True
    
    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Tek bir metin için embedding üret.
        
        Args:
            text: Embedding yapılacak metin
            use_cache: Cache kullanılsın mı
            
        Returns:
            Embedding vektörü (float listesi)
        """
        # Cache kontrolü
        if use_cache and self._cache_enabled and self._cache:
            cached = self._cache.get(text)
            if cached is not None:
                return cached
        
        try:
            response = self.client.embeddings(
                model=self.model_name,
                prompt=text,
            )
            embedding = response["embedding"]
            
            # Cache'e ekle
            if use_cache and self._cache_enabled and self._cache:
                self._cache.set(text, embedding)
            
            return embedding
        except Exception as e:
            print(f"❌ Embedding hatası: {e}")
            raise
    
    def embed_texts(self, texts: List[str], batch_size: int = 32, use_cache: bool = True) -> List[List[float]]:
        """
        Birden fazla metin için embedding üret.
        
        Args:
            texts: Embedding yapılacak metinler
            batch_size: Batch boyutu
            use_cache: Cache kullanılsın mı
            
        Returns:
            Embedding vektörleri listesi
        """
        embeddings = []
        cache_hits = 0
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                # Cache kontrolü
                if use_cache and self._cache_enabled and self._cache:
                    cached = self._cache.get(text)
                    if cached is not None:
                        embeddings.append(cached)
                        cache_hits += 1
                        continue
                
                embedding = self.embed_text(text, use_cache=use_cache)
                embeddings.append(embedding)
            
            # Progress indicator
            progress = min(i + batch_size, len(texts))
            cache_info = f" (cache hits: {cache_hits})" if cache_hits > 0 else ""
            print(f"📊 Embedding progress: {progress}/{len(texts)}{cache_info}")
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        Sorgu için embedding üret (arama optimizasyonu).
        Cache'lenir çünkü aynı sorgular tekrarlanabilir.
        
        Args:
            query: Arama sorgusu
            
        Returns:
            Query embedding vektörü
        """
        return self.embed_text(query, use_cache=True)
    
    def embed_document(self, document: str, use_cache: bool = False) -> List[float]:
        """
        Döküman için embedding üret (indexing optimizasyonu).
        Default olarak cache'lenmez çünkü dokümanlar genelde tek sefer işlenir.
        
        Args:
            document: Döküman içeriği
            use_cache: Cache kullanılsın mı
            
        Returns:
            Document embedding vektörü
        """
        return self.embed_text(document, use_cache=use_cache)
    
    @staticmethod
    def normalize(embedding: List[float]) -> List[float]:
        """Embedding vektörünü normalize et (L2 normalization)."""
        arr = np.array(embedding)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """İki vektör arasındaki cosine similarity hesapla."""
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get_status(self) -> dict:
        """Embedding manager durumunu döndür."""
        status = {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "dimension": self.dimension,
            "model_available": self.check_model_available(),
            "cache_enabled": self._cache_enabled,
        }
        
        if self._cache_enabled and self._cache:
            status["cache_stats"] = self._cache.get_stats()
        
        return status
    
    def clear_cache(self) -> None:
        """Embedding cache'ini temizle."""
        if self._cache:
            self._cache.clear()
    
    def get_cache_stats(self) -> Optional[Dict]:
        """Cache istatistiklerini döndür."""
        if self._cache:
            return self._cache.get_stats()
        return None


# Singleton instance
embedding_manager = EmbeddingManager()
