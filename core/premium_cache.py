"""
💾 Premium Cache Layer
======================

Endüstri-seviyesi önbellekleme sistemi.
Search sonuçları, embedding'ler ve session'lar için.

Özellikler:
- DiskCache: Disk tabanlı persistent cache
- MemoryCache: Hızlı memory cache 
- TTL Support: Zaman bazlı invalidation
- LRU Eviction: En az kullanılanı sil
- Compression: Büyük veriler için sıkıştırma
"""

import asyncio
import hashlib
import json
import logging
import os
import pickle
import shutil
import threading
import time
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Generic, Callable
from collections import OrderedDict
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============ CACHE ENTRY ============

@dataclass
class CacheEntry(Generic[T]):
    """Cache girişi"""
    key: str
    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    compressed: bool = False
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self):
        """Erişim zamanını güncelle"""
        self.access_count += 1
        self.last_accessed = time.time()


# ============ MEMORY CACHE ============

class MemoryCache:
    """
    Thread-safe LRU Memory Cache.
    
    Hızlı erişim için memory tabanlı cache.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        default_ttl_seconds: int = 3600,
    ):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl = default_ttl_seconds
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._current_memory = 0
        
        # Stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den değer al"""
        with self._lock:
            if key not in self._cache:
                self.stats["misses"] += 1
                return None
            
            entry = self._cache[key]
            
            # Expired check
            if entry.is_expired:
                self._remove(key)
                self.stats["misses"] += 1
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            entry.touch()
            
            self.stats["hits"] += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Cache'e değer yaz"""
        with self._lock:
            # Eski değeri temizle
            if key in self._cache:
                self._remove(key)
            
            # TTL hesapla
            ttl = ttl_seconds or self.default_ttl
            expires_at = time.time() + ttl if ttl > 0 else None
            
            # Boyut hesapla
            try:
                size = len(pickle.dumps(value))
            except Exception:
                size = 1000  # Fallback
            
            # Entry oluştur
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at,
                size_bytes=size
            )
            
            # Yer aç
            self._evict_if_needed(size)
            
            # Ekle
            self._cache[key] = entry
            self._current_memory += size
            
            return True
    
    def delete(self, key: str) -> bool:
        """Cache'den sil"""
        with self._lock:
            return self._remove(key)
    
    def clear(self):
        """Tüm cache'i temizle"""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    def _remove(self, key: str) -> bool:
        """Internal remove"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_memory -= entry.size_bytes
            return True
        return False
    
    def _evict_if_needed(self, needed_bytes: int):
        """LRU eviction"""
        # Size limit check
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
            self.stats["evictions"] += 1
        
        # Memory limit check
        while self._current_memory + needed_bytes > self.max_memory_bytes and self._cache:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
            self.stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri al"""
        with self._lock:
            total = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / max(1, total)
            
            return {
                **self.stats,
                "size": len(self._cache),
                "memory_mb": self._current_memory / (1024 * 1024),
                "hit_rate": round(hit_rate, 3),
            }


# ============ DISK CACHE ============

class DiskCache:
    """
    Persistent Disk Cache.
    
    Kalıcı depolama için disk tabanlı cache.
    """
    
    def __init__(
        self,
        cache_dir: str = ".cache/premium",
        max_size_mb: int = 500,
        default_ttl_seconds: int = 86400,  # 24 saat
        enable_compression: bool = True,
    ):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl_seconds
        self.enable_compression = enable_compression
        
        # Index dosyası
        self.index_file = self.cache_dir / "index.json"
        self._index: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        
        # Initialize
        self._ensure_dir()
        self._load_index()
        
        # Stats
        self.stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0,
        }
    
    def _ensure_dir(self):
        """Cache dizinini oluştur"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """Index'i yükle"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
                    
                # Expired olanları temizle
                self._cleanup_expired()
        except Exception as e:
            logger.warning(f"Index load failed: {e}")
            self._index = {}
    
    def _save_index(self):
        """Index'i kaydet"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, indent=2)
        except Exception as e:
            logger.error(f"Index save failed: {e}")
    
    def _cleanup_expired(self):
        """Expired girişleri temizle"""
        now = time.time()
        expired_keys = [
            key for key, meta in self._index.items()
            if meta.get("expires_at") and meta["expires_at"] < now
        ]
        
        for key in expired_keys:
            self._remove_file(key)
            del self._index[key]
        
        if expired_keys:
            self._save_index()
            logger.info(f"Cleaned {len(expired_keys)} expired cache entries")
    
    def _get_file_path(self, key: str) -> Path:
        """Key için dosya yolu"""
        hashed = hashlib.md5(key.encode()).hexdigest()
        subdir = self.cache_dir / hashed[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{hashed}.cache"
    
    def _remove_file(self, key: str):
        """Dosyayı sil"""
        try:
            path = self._get_file_path(key)
            if path.exists():
                path.unlink()
        except Exception:
            pass
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den oku"""
        with self._lock:
            if key not in self._index:
                self.stats["misses"] += 1
                return None
            
            meta = self._index[key]
            
            # Expired check
            if meta.get("expires_at") and meta["expires_at"] < time.time():
                self._remove_file(key)
                del self._index[key]
                self._save_index()
                self.stats["misses"] += 1
                return None
            
            # Dosyadan oku
            try:
                path = self._get_file_path(key)
                if not path.exists():
                    del self._index[key]
                    self._save_index()
                    self.stats["misses"] += 1
                    return None
                
                with open(path, 'rb') as f:
                    data = f.read()
                
                # Decompress if needed
                if meta.get("compressed"):
                    data = zlib.decompress(data)
                
                value = pickle.loads(data)
                
                # Update access time
                self._index[key]["access_count"] = meta.get("access_count", 0) + 1
                self._index[key]["last_accessed"] = time.time()
                
                self.stats["hits"] += 1
                return value
                
            except Exception as e:
                logger.warning(f"Cache read failed for {key}: {e}")
                self.stats["misses"] += 1
                return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Cache'e yaz"""
        with self._lock:
            try:
                # Serialize
                data = pickle.dumps(value)
                original_size = len(data)
                
                # Compress if enabled and worthwhile
                compressed = False
                if self.enable_compression and original_size > 1000:
                    compressed_data = zlib.compress(data, level=6)
                    if len(compressed_data) < original_size * 0.9:
                        data = compressed_data
                        compressed = True
                
                # Dosyaya yaz
                path = self._get_file_path(key)
                with open(path, 'wb') as f:
                    f.write(data)
                
                # TTL
                ttl = ttl_seconds or self.default_ttl
                expires_at = time.time() + ttl if ttl > 0 else None
                
                # Index güncelle
                self._index[key] = {
                    "created_at": time.time(),
                    "expires_at": expires_at,
                    "size_bytes": len(data),
                    "original_size": original_size,
                    "compressed": compressed,
                    "access_count": 0,
                    "last_accessed": time.time(),
                }
                
                self._save_index()
                self.stats["writes"] += 1
                
                # Size cleanup
                self._cleanup_if_needed()
                
                return True
                
            except Exception as e:
                logger.error(f"Cache write failed for {key}: {e}")
                return False
    
    def delete(self, key: str) -> bool:
        """Cache'den sil"""
        with self._lock:
            if key in self._index:
                self._remove_file(key)
                del self._index[key]
                self._save_index()
                return True
            return False
    
    def clear(self):
        """Tüm cache'i temizle"""
        with self._lock:
            try:
                shutil.rmtree(self.cache_dir)
                self._ensure_dir()
                self._index = {}
                self._save_index()
            except Exception as e:
                logger.error(f"Cache clear failed: {e}")
    
    def _cleanup_if_needed(self):
        """Size limit aşılırsa temizle"""
        total_size = sum(m.get("size_bytes", 0) for m in self._index.values())
        
        if total_size > self.max_size_bytes:
            # Sort by last accessed (LRU)
            sorted_keys = sorted(
                self._index.keys(),
                key=lambda k: self._index[k].get("last_accessed", 0)
            )
            
            # En eski %20'yi sil
            to_remove = sorted_keys[:len(sorted_keys) // 5 + 1]
            
            for key in to_remove:
                self._remove_file(key)
                del self._index[key]
            
            self._save_index()
            logger.info(f"Removed {len(to_remove)} old cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri al"""
        with self._lock:
            total_size = sum(m.get("size_bytes", 0) for m in self._index.values())
            total = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / max(1, total)
            
            return {
                **self.stats,
                "entries": len(self._index),
                "size_mb": round(total_size / (1024 * 1024), 2),
                "hit_rate": round(hit_rate, 3),
            }


# ============ UNIFIED PREMIUM CACHE ============

class PremiumCache:
    """
    Unified Premium Cache.
    
    Memory + Disk kombinasyonu.
    Hot data memory'de, cold data disk'te.
    """
    
    def __init__(
        self,
        cache_dir: str = ".cache/premium",
        memory_max_size: int = 500,
        memory_max_mb: int = 50,
        disk_max_mb: int = 500,
        default_ttl: int = 3600,
    ):
        self.memory = MemoryCache(
            max_size=memory_max_size,
            max_memory_mb=memory_max_mb,
            default_ttl_seconds=default_ttl,
        )
        
        self.disk = DiskCache(
            cache_dir=cache_dir,
            max_size_mb=disk_max_mb,
            default_ttl_seconds=default_ttl * 24,  # Disk'te daha uzun sakla
        )
        
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Önce memory, sonra disk'ten oku.
        Disk'te bulursa memory'ye de yaz (cache warming).
        """
        # Memory check
        value = self.memory.get(key)
        if value is not None:
            return value
        
        # Disk check
        value = self.disk.get(key)
        if value is not None:
            # Warm memory cache
            self.memory.set(key, value)
            return value
        
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        persist: bool = True,
    ) -> bool:
        """
        Hem memory hem disk'e yaz.
        
        Args:
            key: Cache key
            value: Değer
            ttl_seconds: TTL
            persist: Disk'e de yaz
        """
        ttl = ttl_seconds or self.default_ttl
        
        # Memory'ye yaz
        self.memory.set(key, value, ttl)
        
        # Disk'e yaz (opsiyonel)
        if persist:
            self.disk.set(key, value, ttl * 24)  # Disk'te daha uzun
        
        return True
    
    def delete(self, key: str) -> bool:
        """Her iki cache'den sil"""
        m = self.memory.delete(key)
        d = self.disk.delete(key)
        return m or d
    
    def clear(self):
        """Tüm cache'leri temizle"""
        self.memory.clear()
        self.disk.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Birleşik istatistikler"""
        return {
            "memory": self.memory.get_stats(),
            "disk": self.disk.get_stats(),
        }


# ============ CACHE DECORATORS ============

def cached(
    cache: Optional[PremiumCache] = None,
    ttl_seconds: int = 3600,
    key_prefix: str = "",
):
    """
    Cache decorator for sync functions.
    
    Example:
        @cached(ttl_seconds=300)
        def expensive_function(x, y):
            ...
    """
    def decorator(func: Callable) -> Callable:
        _cache = cache or _get_global_cache()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate key
            key = f"{key_prefix}:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Check cache
            result = _cache.get(key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            _cache.set(key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


def async_cached(
    cache: Optional[PremiumCache] = None,
    ttl_seconds: int = 3600,
    key_prefix: str = "",
):
    """
    Cache decorator for async functions.
    
    Example:
        @async_cached(ttl_seconds=300)
        async def expensive_async_function(x, y):
            ...
    """
    def decorator(func: Callable) -> Callable:
        _cache = cache or _get_global_cache()
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate key
            key = f"{key_prefix}:{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Check cache
            result = _cache.get(key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            _cache.set(key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


# ============ SEARCH CACHE ============

class SearchCache:
    """
    Search-specific cache.
    
    Multi-Provider Search sonuçları için optimize edilmiş cache.
    """
    
    def __init__(self, base_cache: Optional[PremiumCache] = None):
        self.cache = base_cache or _get_global_cache()
        self.prefix = "search"
    
    def _make_key(self, query: str, providers: Optional[List[str]] = None) -> str:
        """Sorgu için unique key"""
        provider_str = ",".join(sorted(providers or ["all"]))
        raw = f"{query.lower().strip()}:{provider_str}"
        return f"{self.prefix}:{hashlib.md5(raw.encode()).hexdigest()}"
    
    def get_results(
        self,
        query: str,
        providers: Optional[List[str]] = None
    ) -> Optional[Any]:
        """Arama sonuçlarını al"""
        key = self._make_key(query, providers)
        return self.cache.get(key)
    
    def set_results(
        self,
        query: str,
        results: Any,
        providers: Optional[List[str]] = None,
        ttl_seconds: int = 1800,  # 30 dakika
    ):
        """Arama sonuçlarını kaydet"""
        key = self._make_key(query, providers)
        self.cache.set(key, results, ttl_seconds)
    
    def invalidate(self, query: str, providers: Optional[List[str]] = None):
        """Belirli sorguyu invalidate et"""
        key = self._make_key(query, providers)
        self.cache.delete(key)


# ============ SESSION CACHE ============

class SessionCache:
    """
    Session-specific cache.
    
    Chat session'ları için persistent storage.
    """
    
    def __init__(self, base_cache: Optional[PremiumCache] = None):
        self.cache = base_cache or _get_global_cache()
        self.prefix = "session"
    
    def _make_key(self, session_id: str) -> str:
        return f"{self.prefix}:{session_id}"
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Session verilerini al"""
        key = self._make_key(session_id)
        return self.cache.get(key)
    
    def save_session(
        self,
        session_id: str,
        data: Dict,
        ttl_seconds: int = 86400 * 7,  # 7 gün
    ):
        """Session verilerini kaydet"""
        key = self._make_key(session_id)
        self.cache.set(key, data, ttl_seconds, persist=True)
    
    def delete_session(self, session_id: str):
        """Session'ı sil"""
        key = self._make_key(session_id)
        self.cache.delete(key)
    
    def update_session(self, session_id: str, updates: Dict):
        """Session'ı güncelle"""
        data = self.get_session(session_id) or {}
        data.update(updates)
        data["updated_at"] = datetime.now().isoformat()
        self.save_session(session_id, data)


# ============ EMBEDDING CACHE ============

class EmbeddingCache:
    """
    Embedding-specific cache.
    
    HyDE ve diğer embedding'ler için optimize edilmiş cache.
    """
    
    def __init__(self, base_cache: Optional[PremiumCache] = None):
        self.cache = base_cache or _get_global_cache()
        self.prefix = "embedding"
    
    def _make_key(self, text: str, model: str = "default") -> str:
        """Text için unique key"""
        raw = f"{text}:{model}"
        return f"{self.prefix}:{hashlib.md5(raw.encode()).hexdigest()}"
    
    def get_embedding(
        self,
        text: str,
        model: str = "default"
    ) -> Optional[List[float]]:
        """Embedding'i al"""
        key = self._make_key(text, model)
        return self.cache.get(key)
    
    def set_embedding(
        self,
        text: str,
        embedding: List[float],
        model: str = "default",
        ttl_seconds: int = 86400 * 30,  # 30 gün (embedding'ler değişmez)
    ):
        """Embedding'i kaydet"""
        key = self._make_key(text, model)
        self.cache.set(key, embedding, ttl_seconds, persist=True)


# ============ GLOBAL CACHE INSTANCE ============

_global_cache: Optional[PremiumCache] = None
_cache_lock = threading.Lock()


def _get_global_cache() -> PremiumCache:
    """Global cache instance'ı al"""
    global _global_cache
    
    with _cache_lock:
        if _global_cache is None:
            _global_cache = PremiumCache()
        return _global_cache


def get_premium_cache() -> PremiumCache:
    """Public API for global cache"""
    return _get_global_cache()


def get_search_cache() -> SearchCache:
    """Search cache instance"""
    return SearchCache(_get_global_cache())


def get_session_cache() -> SessionCache:
    """Session cache instance"""
    return SessionCache(_get_global_cache())


def get_embedding_cache() -> EmbeddingCache:
    """Embedding cache instance"""
    return EmbeddingCache(_get_global_cache())


# ============ INITIALIZATION ============

def init_premium_cache(
    cache_dir: str = ".cache/premium",
    memory_max_mb: int = 50,
    disk_max_mb: int = 500,
) -> PremiumCache:
    """
    Premium cache'i başlat.
    
    Uygulama başlangıcında bir kere çağrılmalı.
    """
    global _global_cache
    
    with _cache_lock:
        _global_cache = PremiumCache(
            cache_dir=cache_dir,
            memory_max_mb=memory_max_mb,
            disk_max_mb=disk_max_mb,
        )
        logger.info(f"Premium cache initialized at {cache_dir}")
        return _global_cache
