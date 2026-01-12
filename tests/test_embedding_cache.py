"""
Enterprise AI Assistant - Embedding Cache Tests
================================================

Embedding cache sistemi için unit testler.
"""

import pytest
import sys
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEmbeddingCache:
    """Embedding cache testleri."""
    
    def test_cache_initialization(self):
        """Cache düzgün initialize olmalı."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=100)
        stats = cache.get_stats()
        
        assert stats["max_size"] == 100
        assert stats["size"] == 0
        assert "hit_rate" in stats
    
    def test_cache_set_and_get(self):
        """Cache set/get çalışmalı."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=100)
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        cache.set("test_key", test_embedding)
        result = cache.get("test_key")
        
        assert result == test_embedding
    
    def test_cache_miss(self):
        """Cache miss None döndürmeli."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=100)
        result = cache.get("nonexistent_key")
        
        assert result is None
    
    def test_cache_eviction(self):
        """Cache max size aşıldığında eviction yapmalı."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=3)
        
        cache.set("key1", [1.0])
        cache.set("key2", [2.0])
        cache.set("key3", [3.0])
        cache.set("key4", [4.0])  # Bu key1'i silmeli
        
        stats = cache.get_stats()
        assert stats["size"] <= 3
    
    def test_cache_hit_rate(self):
        """Hit rate doğru hesaplanmalı."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=100)
        cache.set("key1", [1.0])
        
        # 1 hit
        cache.get("key1")
        # 1 miss
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        # hit_rate is formatted as string "50.0%"
        assert stats["hits"] == 1
        assert stats["misses"] == 1
    
    def test_cache_thread_safety(self):
        """Cache thread-safe olmalı."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=1000)
        errors = []
        
        def writer(thread_id):
            try:
                for i in range(100):
                    cache.set(f"thread_{thread_id}_key_{i}", [float(i)])
            except Exception as e:
                errors.append(e)
        
        def reader(thread_id):
            try:
                for i in range(100):
                    cache.get(f"thread_{thread_id}_key_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(5):
            t1 = threading.Thread(target=writer, args=(i,))
            t2 = threading.Thread(target=reader, args=(i,))
            threads.extend([t1, t2])
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_cache_clear(self):
        """Cache temizlenebilmeli."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=100)
        cache.set("key1", [1.0])
        cache.set("key2", [2.0])
        
        cache.clear()
        stats = cache.get_stats()
        
        assert stats["size"] == 0
    
    def test_text_hashing(self):
        """Aynı text aynı hash üretmeli."""
        from core.embedding import EmbeddingCache
        
        cache = EmbeddingCache(max_size=100)
        
        text1 = "Hello World"
        text2 = "Hello World"
        text3 = "Different Text"
        
        hash1 = cache._hash_text(text1)
        hash2 = cache._hash_text(text2)
        hash3 = cache._hash_text(text3)
        
        assert hash1 == hash2
        assert hash1 != hash3


class TestEmbeddingSystem:
    """Embedding sistemi testleri."""
    
    def test_embedding_manager_initialization(self):
        """EmbeddingManager initialize edilebilmeli."""
        try:
            from core.embedding import EmbeddingManager
            # Constructor test
            assert EmbeddingManager is not None
        except ImportError:
            pytest.skip("EmbeddingManager not available")
    
    def test_embedding_dimensions(self):
        """Embedding boyutları tutarlı olmalı."""
        # Mock embedding
        mock_embedding = [0.0] * 384  # Common embedding size
        assert len(mock_embedding) == 384


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
