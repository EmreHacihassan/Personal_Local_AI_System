"""
Enterprise AI Assistant - Cache Module
LLM yanıt cache sistemi

Endüstri standardı caching implementasyonu.
"""

import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from core.config import settings


@dataclass
class CacheEntry:
    """Cache girişi."""
    key: str
    value: Any
    created_at: str
    expires_at: Optional[str]
    hit_count: int = 0


class CacheManager:
    """Cache yönetim sınıfı."""
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        default_ttl: int = 3600  # 1 saat
    ):
        """
        Cache manager başlat.
        
        Args:
            db_path: SQLite veritabanı yolu
            default_ttl: Varsayılan TTL (saniye)
        """
        self.db_path = db_path or settings.DATA_DIR / "cache" / "cache.db"
        self.default_ttl = default_ttl
        self._init_db()
    
    def _init_db(self) -> None:
        """Veritabanını başlat."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)
            """)
            conn.commit()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Cache anahtarı oluştur."""
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Cache'den değer al.
        
        Args:
            key: Cache anahtarı
            
        Returns:
            Cache değeri veya None
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                SELECT value, expires_at FROM cache WHERE key = ?
                """,
                (key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            value, expires_at = row
            
            # Check expiration
            if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
                self.delete(key)
                return None
            
            # Update hit count
            conn.execute(
                "UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?",
                (key,)
            )
            conn.commit()
            
            return json.loads(value)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache'e değer kaydet.
        
        Args:
            key: Cache anahtarı
            value: Kaydedilecek değer
            ttl: TTL (saniye), None ise varsayılan
        """
        ttl = ttl if ttl is not None else self.default_ttl
        now = datetime.now()
        expires_at = (now + timedelta(seconds=ttl)).isoformat() if ttl > 0 else None
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, created_at, expires_at, hit_count)
                VALUES (?, ?, ?, ?, 0)
                """,
                (
                    key,
                    json.dumps(value, ensure_ascii=False),
                    now.isoformat(),
                    expires_at,
                )
            )
            conn.commit()
    
    def delete(self, key: str) -> bool:
        """Cache'den sil."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0
    
    def clear(self) -> int:
        """Tüm cache'i temizle."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("DELETE FROM cache")
            conn.commit()
            return cursor.rowcount
    
    def cleanup_expired(self) -> int:
        """Süresi dolmuş cache girişlerini temizle."""
        now = datetime.now().isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (now,)
            )
            conn.commit()
            return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(hit_count) FROM cache")
            total, total_hits = cursor.fetchone()
            
            cursor = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (datetime.now().isoformat(),)
            )
            expired = cursor.fetchone()[0]
        
        return {
            "total_entries": total or 0,
            "total_hits": total_hits or 0,
            "expired_entries": expired,
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
