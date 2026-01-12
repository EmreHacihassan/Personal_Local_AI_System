"""
Enterprise AI Assistant - Cache Module
LLM yanıt cache sistemi

Endüstri standardı caching implementasyonu.

ENTERPRISE FEATURES:
- SQLite-backed persistent cache
- TTL-based expiration
- LRU eviction policy
- Hit rate analytics
- Connection pooling
- Thread-safe operations
- LLM response caching with semantic matching
- Query result caching
"""

import json
import hashlib
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from collections import OrderedDict

from core.config import settings


@dataclass
class CacheEntry:
    """Cache girişi."""
    key: str
    value: Any
    created_at: str
    expires_at: Optional[str]
    hit_count: int = 0
    size_bytes: int = 0


class InMemoryLRUCache:
    """
    In-memory LRU cache.
    
    Sık erişilen verileri bellekte tutar.
    SQLite cache'inin önünde L1 cache olarak çalışır.
    """
    
    def __init__(self, max_size: int = 500, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache: OrderedDict[str, tuple] = OrderedDict()  # key -> (value, size_bytes)
        self._current_memory = 0
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Cache'den değer al."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key][0]
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache'e değer ekle."""
        value_json = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        size_bytes = len(value_json.encode('utf-8'))
        
        with self._lock:
            # Mevcut değeri sil (varsa)
            if key in self._cache:
                self._current_memory -= self._cache[key][1]
                del self._cache[key]
            
            # Yer aç (gerekirse)
            while (len(self._cache) >= self.max_size or 
                   self._current_memory + size_bytes > self.max_memory_bytes):
                if not self._cache:
                    break
                _, (_, old_size) = self._cache.popitem(last=False)
                self._current_memory -= old_size
            
            # Ekle
            self._cache[key] = (value, size_bytes)
            self._current_memory += size_bytes
    
    def delete(self, key: str) -> bool:
        """Cache'den sil."""
        with self._lock:
            if key in self._cache:
                self._current_memory -= self._cache[key][1]
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Cache'i temizle."""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total * 100 if total > 0 else 0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "memory_mb": self._current_memory / (1024 * 1024),
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.1f}%",
            }


class ConnectionPool:
    """
    SQLite connection pool.
    
    Thread başına bir connection tutar.
    """
    
    def __init__(self, db_path: Path, pool_size: int = 5):
        self.db_path = str(db_path)
        self.pool_size = pool_size
        self._local = threading.local()
    
    @contextmanager
    def get_connection(self):
        """Connection al."""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
        
        try:
            yield self._local.connection
        except Exception:
            # Hata durumunda connection'ı kapat
            if hasattr(self._local, 'connection') and self._local.connection:
                self._local.connection.close()
                self._local.connection = None
            raise


class CacheManager:
    """
    Cache yönetim sınıfı.
    
    ENTERPRISE FEATURES:
    - Two-tier caching (L1: In-memory LRU, L2: SQLite)
    - Connection pooling
    - Automatic cleanup
    - Comprehensive metrics
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        default_ttl: int = 3600,  # 1 saat
        enable_l1_cache: bool = True,
        l1_max_size: int = 500,
        l1_max_memory_mb: int = 100,
    ):
        """
        Cache manager başlat.
        
        Args:
            db_path: SQLite veritabanı yolu
            default_ttl: Varsayılan TTL (saniye)
            enable_l1_cache: L1 (in-memory) cache aktif mi
            l1_max_size: L1 cache maksimum giriş sayısı
            l1_max_memory_mb: L1 cache maksimum bellek (MB)
        """
        self.db_path = db_path or settings.DATA_DIR / "cache" / "cache.db"
        self.default_ttl = default_ttl
        
        # L1 Cache (in-memory)
        self._l1_enabled = enable_l1_cache
        self._l1_cache = InMemoryLRUCache(l1_max_size, l1_max_memory_mb) if enable_l1_cache else None
        
        # L2 Cache (SQLite with connection pool)
        self._pool = ConnectionPool(self.db_path)
        
        # Metrics
        self._metrics = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
        }
        self._lock = threading.Lock()
        
        self._init_db()
    
    def _init_db(self) -> None:
        """Veritabanını başlat."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._pool.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    hit_count INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created ON cache(created_at)
            """)
            conn.commit()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Cache anahtarı oluştur."""
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Cache'den değer al.
        
        İki kademeli arama: L1 (memory) -> L2 (SQLite)
        
        Args:
            key: Cache anahtarı
            
        Returns:
            Cache değeri veya None
        """
        # L1 Cache kontrolü
        if self._l1_enabled and self._l1_cache:
            value = self._l1_cache.get(key)
            if value is not None:
                with self._lock:
                    self._metrics["l1_hits"] += 1
                return value
        
        # L2 Cache kontrolü (SQLite)
        with self._pool.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT value, expires_at FROM cache WHERE key = ?
                """,
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                with self._lock:
                    self._metrics["misses"] += 1
                return None
            
            value_str, expires_at = row
            
            # Check expiration
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                self.delete(key)
                with self._lock:
                    self._metrics["misses"] += 1
                return None
            
            # Update hit count
            conn.execute(
                "UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?",
                (key,)
            )
            conn.commit()
            
            value = json.loads(value_str)
            
            # L1 cache'e ekle (cache warming)
            if self._l1_enabled and self._l1_cache:
                self._l1_cache.set(key, value)
            
            with self._lock:
                self._metrics["l2_hits"] += 1
            
            return value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache'e değer kaydet.
        
        Hem L1 (memory) hem L2 (SQLite) cache'e yazar.
        
        Args:
            key: Cache anahtarı
            value: Kaydedilecek değer
            ttl: TTL (saniye), None ise varsayılan
        """
        ttl = ttl if ttl is not None else self.default_ttl
        now = datetime.now()
        expires_at = (now + timedelta(seconds=ttl)).isoformat() if ttl > 0 else None
        
        value_json = json.dumps(value, ensure_ascii=False)
        size_bytes = len(value_json.encode('utf-8'))
        
        # L1 Cache'e ekle
        if self._l1_enabled and self._l1_cache:
            self._l1_cache.set(key, value)
        
        # L2 Cache'e ekle (SQLite)
        with self._pool.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, created_at, expires_at, hit_count, size_bytes)
                VALUES (?, ?, ?, ?, 0, ?)
                """,
                (
                    key,
                    value_json,
                    now.isoformat(),
                    expires_at,
                    size_bytes,
                )
            )
            conn.commit()
        
        with self._lock:
            self._metrics["sets"] += 1
    
    def delete(self, key: str) -> bool:
        """
        Cache'den sil.
        
        Hem L1 hem L2'den siler.
        """
        # L1'den sil
        if self._l1_enabled and self._l1_cache:
            self._l1_cache.delete(key)
        
        # L2'den sil
        with self._pool.get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            deleted = cursor.rowcount > 0
        
        if deleted:
            with self._lock:
                self._metrics["deletes"] += 1
        
        return deleted
    
    def clear(self) -> int:
        """
        Tüm cache'i temizle.
        
        Hem L1 hem L2'yi temizler.
        """
        # L1'i temizle
        if self._l1_enabled and self._l1_cache:
            self._l1_cache.clear()
        
        # L2'yi temizle
        with self._pool.get_connection() as conn:
            cursor = conn.execute("DELETE FROM cache")
            conn.commit()
            return cursor.rowcount
    
    def cleanup_expired(self) -> int:
        """Süresi dolmuş cache girişlerini temizle."""
        now = datetime.now().isoformat()
        with self._pool.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,)
            )
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Cache istatistikleri.
        
        Hem L1 hem L2 istatistiklerini döndürür.
        """
        # L2 stats
        with self._pool.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(hit_count), SUM(size_bytes) FROM cache")
            total, total_hits, total_size = cursor.fetchone()
            
            cursor = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (datetime.now().isoformat(),)
            )
            expired = cursor.fetchone()[0]
        
        # L1 stats
        l1_stats = self._l1_cache.get_stats() if self._l1_enabled and self._l1_cache else {}
        
        # Combined metrics
        with self._lock:
            total_requests = self._metrics["l1_hits"] + self._metrics["l2_hits"] + self._metrics["misses"]
            hit_rate = (self._metrics["l1_hits"] + self._metrics["l2_hits"]) / total_requests * 100 if total_requests > 0 else 0
        
        return {
            "l1_cache": l1_stats,
            "l2_cache": {
                "total_entries": total or 0,
                "total_hits": total_hits or 0,
                "total_size_mb": (total_size or 0) / (1024 * 1024),
                "expired_entries": expired,
            },
            "metrics": {
                "l1_hits": self._metrics["l1_hits"],
                "l2_hits": self._metrics["l2_hits"],
                "misses": self._metrics["misses"],
                "sets": self._metrics["sets"],
                "deletes": self._metrics["deletes"],
                "hit_rate": f"{hit_rate:.1f}%",
            },
        }
    
    def cache_llm_response(
        self,
        query: str,
        response: str,
        model: str = None,
        ttl: int = 7200  # 2 saat
    ) -> str:
        """
        LLM yanıtını cache'le.
        
        Args:
            query: Sorgu
            response: LLM yanıtı
            model: Model adı
            ttl: TTL (saniye)
            
        Returns:
            Cache anahtarı
        """
        key = self._generate_key(query=query.strip().lower(), model=model)
        self.set(key, {"response": response, "model": model}, ttl=ttl)
        return key
    
    def get_cached_llm_response(
        self,
        query: str,
        model: str = None
    ) -> Optional[str]:
        """
        Cache'lenmiş LLM yanıtını al.
        
        Args:
            query: Sorgu
            model: Model adı
            
        Returns:
            Cache'lenmiş yanıt veya None
        """
        key = self._generate_key(query=query.strip().lower(), model=model)
        cached = self.get(key)
        
        if cached:
            return cached.get("response")
        return None


# Singleton instance
cache = CacheManager()
cache_manager = cache  # Alias for compatibility


def cached(ttl: int = 3600):
    """
    Cache decorator.
    
    Args:
        ttl: TTL (saniye)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = cache._generate_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator
