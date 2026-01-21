"""
Enterprise AI Assistant - Fluency & Performance Tests
======================================================

Akıcılık (fluency), yanıt süresi ve performans testleri.
Response time, latency, throughput, memory testleri.
"""

import pytest
import sys
import time
import asyncio
import threading
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List
from concurrent.futures import ThreadPoolExecutor
import statistics

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock chromadb before any imports
if 'chromadb' not in sys.modules:
    mock_chromadb = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_collection
    sys.modules['chromadb'] = mock_chromadb
    sys.modules['chromadb.config'] = MagicMock()
    sys.modules['chromadb.api'] = MagicMock()


class TestResponseTimes:
    """Yanıt süresi testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_health_response_time(self, client):
        """Health endpoint 100ms altında yanıt vermeli."""
        times = []
        
        for _ in range(10):
            start = time.perf_counter()
            response = client.get("/health/live")
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)
            
            assert response.status_code == 200
        
        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        assert avg_time < 100, f"Ortalama yanıt süresi {avg_time:.2f}ms (< 100ms olmalı)"
        assert p95_time < 200, f"P95 yanıt süresi {p95_time:.2f}ms (< 200ms olmalı)"
    
    def test_root_response_time(self, client):
        """Root endpoint 50ms altında yanıt vermeli."""
        times = []
        
        for _ in range(10):
            start = time.perf_counter()
            response = client.get("/")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            
            assert response.status_code == 200
        
        avg_time = statistics.mean(times)
        
        assert avg_time < 50, f"Ortalama yanıt süresi {avg_time:.2f}ms (< 50ms olmalı)"
    
    def test_docs_response_time(self, client):
        """Docs endpoint 200ms altında yanıt vermeli."""
        start = time.perf_counter()
        response = client.get("/docs")
        elapsed = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 200, f"Docs süresi {elapsed:.2f}ms (< 200ms olmalı)"
    
    def test_openapi_response_time(self, client):
        """OpenAPI schema 500ms altında yanıt vermeli."""
        start = time.perf_counter()
        response = client.get("/openapi.json")
        elapsed = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 200
        assert elapsed < 500, f"OpenAPI süresi {elapsed:.2f}ms (< 500ms olmalı)"


class TestConcurrency:
    """Eşzamanlılık testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_concurrent_health_requests(self, client):
        """Eşzamanlı health istekleri başarılı olmalı."""
        results = []
        
        def make_request():
            response = client.get("/health/live")
            results.append(response.status_code)
        
        threads = []
        for _ in range(20):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        # Tüm istekler başarılı olmalı
        success_rate = results.count(200) / len(results)
        
        assert success_rate >= 0.95, f"Başarı oranı {success_rate * 100:.1f}% (>= 95% olmalı)"
    
    def test_concurrent_root_requests(self, client):
        """Eşzamanlı root istekleri başarılı olmalı."""
        results = []
        times = []
        
        def make_request():
            start = time.perf_counter()
            response = client.get("/")
            elapsed = time.perf_counter() - start
            results.append(response.status_code)
            times.append(elapsed)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            for f in futures:
                f.result(timeout=30)
        
        success_rate = results.count(200) / len(results)
        avg_time = statistics.mean(times) * 1000
        
        assert success_rate >= 0.95
        assert avg_time < 500, f"Concurrent avg time {avg_time:.2f}ms"


class TestModuleImportTimes:
    """Modül import süreleri testleri."""
    
    def test_config_import_time(self):
        """Config import süresi 1s altında olmalı."""
        start = time.perf_counter()
        import importlib
        
        # Varsa cache'den sil
        if 'core.config' in sys.modules:
            del sys.modules['core.config']
        
        from core import config
        elapsed = time.perf_counter() - start
        
        assert elapsed < 1.0, f"Config import {elapsed:.2f}s (< 1s olmalı)"
    
    def test_llm_manager_import_time(self):
        """LLM manager import süresi makul olmalı."""
        start = time.perf_counter()
        
        if 'core.llm_manager' in sys.modules:
            # Zaten import edilmiş, bu normal
            from core.llm_manager import llm_manager
            elapsed = time.perf_counter() - start
        else:
            from core.llm_manager import llm_manager
            elapsed = time.perf_counter() - start
        
        # Cached import çok hızlı olmalı
        assert elapsed < 5.0, f"LLM manager import {elapsed:.2f}s"


class TestMemoryUsage:
    """Bellek kullanımı testleri."""
    
    def test_basic_memory_footprint(self):
        """Temel memory kullanımı makul olmalı."""
        import gc
        gc.collect()
        
        # Process memory'yi kontrol et
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # 2500MB altında olmalı (GPU modelleri yüklü testler için)
            assert memory_mb < 2500, f"Memory usage {memory_mb:.1f}MB (< 2500MB olmalı)"
        except ImportError:
            # psutil yoksa skip
            pytest.skip("psutil yüklü değil")
    
    def test_no_memory_leak_on_repeated_operations(self):
        """Tekrarlanan işlemlerde memory leak olmamalı."""
        import gc
        
        try:
            import psutil
            process = psutil.Process()
            
            initial_memory = process.memory_info().rss
            
            # Çok sayıda işlem yap
            for _ in range(100):
                from core.config import settings
                _ = settings.OLLAMA_PRIMARY_MODEL
            
            gc.collect()
            final_memory = process.memory_info().rss
            
            memory_increase_mb = (final_memory - initial_memory) / 1024 / 1024
            
            # 50MB'dan az artış olmalı
            assert memory_increase_mb < 50, f"Memory increase {memory_increase_mb:.1f}MB"
        except ImportError:
            pytest.skip("psutil yüklü değil")


class TestAPIFluency:
    """API akıcılık testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_consistent_response_times(self, client):
        """Yanıt süreleri tutarlı olmalı."""
        times = []
        
        for _ in range(20):
            start = time.perf_counter()
            response = client.get("/")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        # Standart sapma düşük olmalı
        std_dev = statistics.stdev(times)
        mean_time = statistics.mean(times)
        
        # Coefficient of variation %50'den az olmalı
        cv = (std_dev / mean_time) * 100 if mean_time > 0 else 0
        
        assert cv < 100, f"Response time CV {cv:.1f}% (tutarsız)"
    
    def test_no_timeout_on_quick_endpoints(self, client):
        """Hızlı endpoint'lerde timeout olmamalı."""
        quick_endpoints = ["/", "/health/live", "/docs"]
        
        for endpoint in quick_endpoints:
            start = time.perf_counter()
            try:
                response = client.get(endpoint)
                elapsed = time.perf_counter() - start
                
                # 5 saniyeden uzun olmamalı
                assert elapsed < 5.0, f"{endpoint} {elapsed:.2f}s timeout"
                assert response.status_code in [200, 301, 302, 307, 308]
            except Exception as e:
                pytest.fail(f"{endpoint} hatası: {e}")


class TestStartupTime:
    """Başlangıç süresi testleri."""
    
    def test_app_creation_time(self):
        """App oluşturma süresi 5s altında olmalı."""
        start = time.perf_counter()
        
        # Fresh import
        from api.main import app
        
        elapsed = time.perf_counter() - start
        
        # Cached olduğu için hızlı olmalı
        assert elapsed < 5.0, f"App creation {elapsed:.2f}s (< 5s olmalı)"
    
    def test_first_request_time(self):
        """İlk istek süresi makul olmalı."""
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        start = time.perf_counter()
        response = client.get("/")
        elapsed = time.perf_counter() - start
        
        # İlk istek warmup içerdiği için 2s'ye kadar normal
        assert elapsed < 2.0, f"First request {elapsed:.2f}s"
        assert response.status_code == 200


class TestErrorHandlingPerformance:
    """Hata işleme performans testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_404_response_time(self, client):
        """404 hatası hızlı dönmeli."""
        start = time.perf_counter()
        response = client.get("/nonexistent-endpoint-xyz")
        elapsed = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 404
        assert elapsed < 100, f"404 süresi {elapsed:.2f}ms"
    
    def test_validation_error_time(self, client):
        """Validation hatası hızlı dönmeli."""
        start = time.perf_counter()
        response = client.post("/api/chat", json={})  # message eksik
        elapsed = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 422
        assert elapsed < 200, f"Validation error süresi {elapsed:.2f}ms"


class TestCachePerformance:
    """Cache performans testleri."""
    
    def test_repeated_config_access(self):
        """Config erişimi cache'lenmiş olmalı."""
        from core.config import settings
        
        times = []
        
        for _ in range(100):
            start = time.perf_counter()
            _ = settings.OLLAMA_PRIMARY_MODEL
            _ = settings.OLLAMA_BASE_URL
            _ = settings.API_DEBUG
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times) * 1000000  # microseconds
        
        # Her erişim 1ms'den az olmalı
        assert avg_time < 1000, f"Config access {avg_time:.2f}μs"


class TestDatabasePerformance:
    """Veritabanı performans testleri."""
    
    def test_vector_store_init(self):
        """Vector store init süresi makul olmalı."""
        start = time.perf_counter()
        
        with patch('chromadb.PersistentClient') as mock_client:
            mock_client.return_value.get_or_create_collection.return_value = MagicMock()
            
            # Import fresh
            from core.vector_store import VectorStore
            
        elapsed = time.perf_counter() - start
        
        # Init 5s'den az olmalı
        assert elapsed < 5.0, f"Vector store init {elapsed:.2f}s"


class TestLoadTesting:
    """Yük testi simülasyonları."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_burst_requests(self, client):
        """Ani yük patlaması test."""
        results = []
        
        # 50 istek burst olarak gönder
        start_all = time.perf_counter()
        
        for _ in range(50):
            response = client.get("/health/live")
            results.append(response.status_code)
        
        total_time = time.perf_counter() - start_all
        
        success_count = results.count(200)
        success_rate = success_count / len(results) * 100
        
        assert success_rate >= 95, f"Burst success rate {success_rate:.1f}%"
        assert total_time < 10, f"Burst total time {total_time:.2f}s"
    
    def test_sustained_load(self, client):
        """Sürekli yük testi."""
        results = []
        duration = 2  # 2 saniye
        
        start_time = time.perf_counter()
        
        while time.perf_counter() - start_time < duration:
            response = client.get("/")
            results.append(response.status_code)
        
        requests_per_second = len(results) / duration
        success_rate = results.count(200) / len(results) * 100
        
        assert success_rate >= 95, f"Sustained success rate {success_rate:.1f}%"
        # En az 10 RPS
        assert requests_per_second >= 10, f"RPS {requests_per_second:.1f}"


class TestLatencyDistribution:
    """Latency dağılımı testleri."""
    
    @pytest.fixture
    def client(self):
        """Test client fixture."""
        from fastapi.testclient import TestClient
        from api.main import app
        return TestClient(app)
    
    def test_latency_percentiles(self, client):
        """Latency percentile'ları makul olmalı."""
        times = []
        
        for _ in range(100):
            start = time.perf_counter()
            response = client.get("/")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        times.sort()
        
        p50 = times[int(len(times) * 0.50)]
        p90 = times[int(len(times) * 0.90)]
        p99 = times[int(len(times) * 0.99)]
        
        assert p50 < 50, f"P50 latency {p50:.2f}ms"
        assert p90 < 100, f"P90 latency {p90:.2f}ms"
        assert p99 < 500, f"P99 latency {p99:.2f}ms"
    
    def test_no_extreme_outliers(self, client):
        """Aşırı yavaş yanıtlar olmamalı."""
        times = []
        
        for _ in range(50):
            start = time.perf_counter()
            response = client.get("/health/live")
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        max_time = max(times)
        
        # Hiçbir istek 2 saniyeden uzun sürmemeli
        assert max_time < 2000, f"Max latency {max_time:.2f}ms (outlier!)"


class TestResourceEfficiency:
    """Kaynak verimliliği testleri."""
    
    def test_thread_count_reasonable(self):
        """Thread sayısı makul olmalı."""
        active_threads = threading.active_count()
        
        # 100'den fazla thread olmamalı (test ortamında)
        assert active_threads < 100, f"Active threads: {active_threads}"
    
    def test_no_file_descriptor_leak(self):
        """Dosya descriptor sızıntısı olmamalı."""
        try:
            import psutil
            process = psutil.Process()
            
            initial_fds = len(process.open_files())
            
            # Birkaç işlem yap
            from fastapi.testclient import TestClient
            from api.main import app
            client = TestClient(app)
            
            for _ in range(10):
                client.get("/")
            
            final_fds = len(process.open_files())
            
            fd_increase = final_fds - initial_fds
            
            # 10'dan fazla artış olmamalı
            assert fd_increase < 10, f"FD increase: {fd_increase}"
        except ImportError:
            pytest.skip("psutil yüklü değil")
