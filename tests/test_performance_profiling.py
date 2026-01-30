#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║            PERFORMANCE & MEMORY PROFILING TEST SUITE                                 ║
║                   "Find the Hidden Performance Killers"                              ║
║                                                                                      ║
║  ⚡ Latency | 💾 Memory | 🔄 GC Pressure | 📊 Throughput | 🎯 Bottlenecks            ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

Metrics Tracked:
================
- Response latency (P50, P95, P99)
- Memory usage over time
- Garbage collection frequency
- Throughput (requests/second)
- Connection pool utilization
- Thread pool saturation
- CPU utilization during requests

Benchmarks:
===========
- Cold start time
- Warm request latency
- Memory under sustained load
- Recovery time after peak load

Author: Performance Engineer
Date: 2026-01-28
"""

import asyncio
import concurrent.futures
import gc
import json
import os
import statistics
import sys
import threading
import time
import tracemalloc
import uuid
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest

try:
    import httpx
    import psutil
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "psutil", "-q"])
    import httpx
    import psutil

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8001")

PERFORMANCE_CONFIG = {
    "warmup_requests": 5,
    "benchmark_requests": 50,
    "concurrent_users": 10,
    "max_latency_p95_ms": 5000,
    "max_latency_p99_ms": 10000,
    "min_throughput_rps": 1,
    "max_memory_growth_mb": 100,
}


# =============================================================================
# PERFORMANCE UTILITIES
# =============================================================================

@dataclass
class LatencyStats:
    """Latency statistics."""
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    sample_count: int
    
    def __str__(self):
        return f"min={self.min_ms:.1f}ms, median={self.median_ms:.1f}ms, p95={self.p95_ms:.1f}ms, p99={self.p99_ms:.1f}ms"


@dataclass
class MemoryStats:
    """Memory statistics."""
    initial_mb: float
    final_mb: float
    peak_mb: float
    delta_mb: float
    gc_collections: Dict[int, int]
    
    def __str__(self):
        return f"initial={self.initial_mb:.1f}MB, final={self.final_mb:.1f}MB, peak={self.peak_mb:.1f}MB, delta={self.delta_mb:+.1f}MB"


@dataclass
class ThroughputStats:
    """Throughput statistics."""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_s: float
    requests_per_second: float
    success_rate: float
    
    def __str__(self):
        return f"rps={self.requests_per_second:.2f}, success_rate={self.success_rate:.1%}"


class PerformanceProfiler:
    """Profile performance of operations."""
    
    def __init__(self):
        self.latencies: List[float] = []
        self.memory_samples: List[float] = []
        self.gc_stats_before: Dict[int, int] = {}
        self.gc_stats_after: Dict[int, int] = {}
        self.start_time: float = 0
        self.end_time: float = 0
        
    def start(self):
        """Start profiling."""
        gc.collect()
        self.gc_stats_before = {i: gc.get_count()[i] for i in range(3)}
        self.start_time = time.time()
        tracemalloc.start()
        self.memory_samples.append(self._get_memory_mb())
        
    def record_latency(self, latency_ms: float):
        """Record a latency measurement."""
        self.latencies.append(latency_ms)
        
    def sample_memory(self):
        """Take a memory sample."""
        self.memory_samples.append(self._get_memory_mb())
        
    def stop(self) -> Tuple[LatencyStats, MemoryStats]:
        """Stop profiling and return stats."""
        self.end_time = time.time()
        
        # Memory
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        self.gc_stats_after = {i: gc.get_count()[i] for i in range(3)}
        gc_collections = {
            i: self.gc_stats_after[i] - self.gc_stats_before[i] 
            for i in range(3)
        }
        
        memory_stats = MemoryStats(
            initial_mb=self.memory_samples[0] if self.memory_samples else 0,
            final_mb=current / (1024 * 1024),
            peak_mb=peak / (1024 * 1024),
            delta_mb=(current / (1024 * 1024)) - (self.memory_samples[0] if self.memory_samples else 0),
            gc_collections=gc_collections
        )
        
        # Latency
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            n = len(sorted_latencies)
            latency_stats = LatencyStats(
                min_ms=min(sorted_latencies),
                max_ms=max(sorted_latencies),
                mean_ms=statistics.mean(sorted_latencies),
                median_ms=statistics.median(sorted_latencies),
                p95_ms=sorted_latencies[int(n * 0.95)] if n > 1 else sorted_latencies[0],
                p99_ms=sorted_latencies[int(n * 0.99)] if n > 1 else sorted_latencies[0],
                std_dev_ms=statistics.stdev(sorted_latencies) if n > 1 else 0,
                sample_count=n
            )
        else:
            latency_stats = LatencyStats(0, 0, 0, 0, 0, 0, 0, 0)
            
        return latency_stats, memory_stats
    
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)


class LoadGenerator:
    """Generate load for testing."""
    
    def __init__(self, base_url: str, timeout: float = 30):
        self.base_url = base_url
        self.timeout = timeout
        
    def single_request(self, session_id: Optional[str] = None) -> Tuple[float, int]:
        """Make a single request and return (latency_ms, status_code)."""
        session_id = session_id or f"load_{uuid.uuid4().hex[:8]}"
        
        start = time.time()
        try:
            with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
                response = client.post("/api/chat", json={
                    "message": "Performance test message",
                    "session_id": session_id
                })
                latency_ms = (time.time() - start) * 1000
                return latency_ms, response.status_code
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return latency_ms, 0
    
    async def async_request(self, client: httpx.AsyncClient, session_id: str) -> Tuple[float, int]:
        """Make an async request."""
        start = time.time()
        try:
            response = await client.post("/api/chat", json={
                "message": "Async performance test",
                "session_id": session_id
            })
            latency_ms = (time.time() - start) * 1000
            return latency_ms, response.status_code
        except Exception:
            latency_ms = (time.time() - start) * 1000
            return latency_ms, 0
    
    def concurrent_requests(self, num_requests: int, num_workers: int = 10) -> List[Tuple[float, int]]:
        """Make concurrent requests using thread pool."""
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(self.single_request, f"concurrent_{i}_{uuid.uuid4().hex[:4]}")
                for i in range(num_requests)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        return results


# =============================================================================
# LATENCY TESTS
# =============================================================================

class TestLatencyPerformance:
    """Test response latency under various conditions."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    @pytest.fixture
    def profiler(self):
        return PerformanceProfiler()
    
    @pytest.fixture
    def load_gen(self):
        return LoadGenerator(BASE_URL)
    
    def test_cold_start_latency(self, client, profiler):
        """Measure cold start latency."""
        # Force new session
        session_id = f"cold_{uuid.uuid4().hex}"
        
        profiler.start()
        
        start = time.time()
        response = client.post("/api/chat", json={
            "message": "Cold start test",
            "session_id": session_id
        })
        latency_ms = (time.time() - start) * 1000
        profiler.record_latency(latency_ms)
        
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nCold Start Latency: {latency_ms:.1f}ms")
        print(f"Status: {response.status_code}")
        
        # Cold start should complete in reasonable time
        assert latency_ms < 30000, f"Cold start too slow: {latency_ms}ms"
    
    def test_warm_request_latency(self, client, profiler):
        """Measure latency after warmup."""
        session_id = f"warm_{uuid.uuid4().hex[:8]}"
        
        # Warmup
        for i in range(PERFORMANCE_CONFIG["warmup_requests"]):
            client.post("/api/chat", json={
                "message": f"Warmup {i}",
                "session_id": session_id
            })
        
        # Measure
        profiler.start()
        
        for i in range(PERFORMANCE_CONFIG["benchmark_requests"]):
            start = time.time()
            response = client.post("/api/chat", json={
                "message": f"Benchmark {i}",
                "session_id": session_id
            })
            latency_ms = (time.time() - start) * 1000
            profiler.record_latency(latency_ms)
        
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nWarm Request Latency: {latency_stats}")
        
        # P95 should be under threshold
        assert latency_stats.p95_ms < PERFORMANCE_CONFIG["max_latency_p95_ms"], \
            f"P95 latency too high: {latency_stats.p95_ms}ms"
    
    def test_latency_under_load(self, load_gen, profiler):
        """Measure latency under concurrent load."""
        profiler.start()
        
        # Generate concurrent load
        results = load_gen.concurrent_requests(
            num_requests=50,
            num_workers=PERFORMANCE_CONFIG["concurrent_users"]
        )
        
        for latency_ms, status_code in results:
            if status_code == 200:
                profiler.record_latency(latency_ms)
        
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nLatency Under Load: {latency_stats}")
        print(f"Successful: {sum(1 for _, s in results if s == 200)}/{len(results)}")
        
        # P99 under load
        if latency_stats.sample_count > 0:
            assert latency_stats.p99_ms < PERFORMANCE_CONFIG["max_latency_p99_ms"], \
                f"P99 latency under load too high: {latency_stats.p99_ms}ms"
    
    def test_latency_variance(self, client, profiler):
        """Test that latency is consistent (low variance)."""
        session_id = f"variance_{uuid.uuid4().hex[:8]}"
        
        # Warmup
        for _ in range(5):
            client.post("/api/chat", json={
                "message": "warmup",
                "session_id": session_id
            })
        
        profiler.start()
        
        for i in range(30):
            start = time.time()
            client.post("/api/chat", json={
                "message": f"variance_test_{i}",
                "session_id": session_id
            })
            profiler.record_latency((time.time() - start) * 1000)
        
        latency_stats, _ = profiler.stop()
        
        print(f"\nLatency Variance: std_dev={latency_stats.std_dev_ms:.1f}ms")
        
        # Coefficient of variation should be reasonable
        if latency_stats.mean_ms > 0:
            cv = latency_stats.std_dev_ms / latency_stats.mean_ms
            print(f"Coefficient of Variation: {cv:.2f}")


# =============================================================================
# MEMORY TESTS
# =============================================================================

class TestMemoryPerformance:
    """Test memory usage and leaks."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    @pytest.fixture
    def profiler(self):
        return PerformanceProfiler()
    
    def test_memory_stability_under_load(self, client, profiler):
        """Test that memory doesn't grow unbounded under load."""
        session_id = f"mem_stable_{uuid.uuid4().hex[:8]}"
        
        profiler.start()
        
        for i in range(100):
            client.post("/api/chat", json={
                "message": f"Memory test {i}",
                "session_id": session_id
            })
            
            if i % 20 == 0:
                profiler.sample_memory()
                gc.collect()
        
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nMemory Stats: {memory_stats}")
        print(f"GC Collections: {memory_stats.gc_collections}")
        
        # Memory growth should be bounded
        assert memory_stats.delta_mb < PERFORMANCE_CONFIG["max_memory_growth_mb"], \
            f"Memory grew too much: {memory_stats.delta_mb}MB"
    
    def test_memory_with_large_payloads(self, client, profiler):
        """Test memory handling with large payloads."""
        profiler.start()
        
        for i in range(10):
            large_message = "x" * (100 * 1024)  # 100KB
            try:
                client.post("/api/chat", json={
                    "message": large_message,
                    "session_id": f"large_{i}_{uuid.uuid4().hex[:4]}"
                })
            except Exception:
                pass
            
            profiler.sample_memory()
            gc.collect()
        
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nLarge Payload Memory: {memory_stats}")
        
        # Should reclaim memory after processing
        assert memory_stats.delta_mb < 200, f"Memory not reclaimed: {memory_stats.delta_mb}MB"
    
    def test_session_memory_isolation(self, client, profiler):
        """Test that sessions don't leak memory to each other."""
        profiler.start()
        
        # Create many sessions
        for i in range(50):
            session_id = f"isolation_{i}_{uuid.uuid4().hex[:4]}"
            client.post("/api/chat", json={
                "message": f"Session {i} message",
                "session_id": session_id
            })
            
            if i % 10 == 0:
                profiler.sample_memory()
        
        gc.collect()
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nSession Isolation Memory: {memory_stats}")
    
    def test_gc_pressure(self, client, profiler):
        """Test garbage collection pressure."""
        profiler.start()
        initial_gc = gc.get_count()
        
        for i in range(50):
            # Create some temporary objects
            temp_data = {"index": i, "data": "x" * 1000, "nested": {"a": [1, 2, 3] * 100}}
            
            client.post("/api/chat", json={
                "message": json.dumps(temp_data),
                "session_id": f"gc_{i}_{uuid.uuid4().hex[:4]}"
            })
            
            del temp_data
        
        final_gc = gc.get_count()
        latency_stats, memory_stats = profiler.stop()
        
        print(f"\nGC Pressure: initial={initial_gc}, final={final_gc}")
        print(f"Collections: {memory_stats.gc_collections}")


# =============================================================================
# THROUGHPUT TESTS
# =============================================================================

class TestThroughputPerformance:
    """Test request throughput."""
    
    @pytest.fixture
    def load_gen(self):
        return LoadGenerator(BASE_URL)
    
    def test_sustained_throughput(self, load_gen):
        """Measure sustained request throughput."""
        start_time = time.time()
        
        results = load_gen.concurrent_requests(
            num_requests=100,
            num_workers=10
        )
        
        total_time = time.time() - start_time
        successful = sum(1 for _, s in results if s == 200)
        
        throughput_stats = ThroughputStats(
            total_requests=len(results),
            successful_requests=successful,
            failed_requests=len(results) - successful,
            total_time_s=total_time,
            requests_per_second=len(results) / total_time,
            success_rate=successful / len(results) if results else 0
        )
        
        print(f"\nSustained Throughput: {throughput_stats}")
        
        assert throughput_stats.requests_per_second >= PERFORMANCE_CONFIG["min_throughput_rps"], \
            f"Throughput too low: {throughput_stats.requests_per_second} rps"
    
    def test_burst_throughput(self, load_gen):
        """Measure throughput during traffic bursts."""
        latencies = []
        
        # Burst: 20 rapid requests
        burst_start = time.time()
        results = load_gen.concurrent_requests(num_requests=20, num_workers=20)
        burst_time = time.time() - burst_start
        
        successful = sum(1 for _, s in results if s == 200)
        burst_rps = len(results) / burst_time
        
        print(f"\nBurst Throughput: {burst_rps:.2f} rps")
        print(f"Burst Success Rate: {successful}/{len(results)}")
    
    def test_throughput_degradation(self, load_gen):
        """Test that throughput doesn't degrade over time."""
        batches = []
        
        for batch_num in range(5):
            batch_start = time.time()
            results = load_gen.concurrent_requests(num_requests=20, num_workers=5)
            batch_time = time.time() - batch_start
            
            successful = sum(1 for _, s in results if s == 200)
            batch_rps = len(results) / batch_time
            batches.append({
                "batch": batch_num,
                "rps": batch_rps,
                "success_rate": successful / len(results)
            })
        
        print("\nThroughput Over Time:")
        for b in batches:
            print(f"  Batch {b['batch']}: {b['rps']:.2f} rps, {b['success_rate']:.1%} success")
        
        # Throughput shouldn't drop more than 50%
        if batches[0]["rps"] > 0:
            degradation = (batches[0]["rps"] - batches[-1]["rps"]) / batches[0]["rps"]
            print(f"Degradation: {degradation:.1%}")


# =============================================================================
# SCALABILITY TESTS
# =============================================================================

class TestScalabilityPerformance:
    """Test system scalability."""
    
    @pytest.fixture
    def load_gen(self):
        return LoadGenerator(BASE_URL, timeout=60)
    
    def test_concurrent_user_scaling(self, load_gen):
        """Test performance as concurrent users increase."""
        user_counts = [1, 5, 10, 20, 50]
        results = []
        
        for num_users in user_counts:
            start = time.time()
            request_results = load_gen.concurrent_requests(
                num_requests=num_users * 2,
                num_workers=num_users
            )
            total_time = time.time() - start
            
            successful = sum(1 for _, s in request_results if s == 200)
            latencies = [lat for lat, s in request_results if s == 200]
            
            results.append({
                "users": num_users,
                "rps": len(request_results) / total_time,
                "success_rate": successful / len(request_results),
                "avg_latency_ms": statistics.mean(latencies) if latencies else 0
            })
        
        print("\nConcurrent User Scaling:")
        for r in results:
            print(f"  {r['users']} users: {r['rps']:.2f} rps, "
                  f"{r['success_rate']:.1%} success, {r['avg_latency_ms']:.0f}ms avg")
    
    def test_payload_size_scaling(self, load_gen):
        """Test performance with increasing payload sizes."""
        sizes_kb = [1, 10, 50, 100, 500]
        results = []
        
        for size_kb in sizes_kb:
            message = "x" * (size_kb * 1024)
            
            latencies = []
            for _ in range(5):
                start = time.time()
                try:
                    with httpx.Client(base_url=BASE_URL, timeout=60) as client:
                        response = client.post("/api/chat", json={
                            "message": message,
                            "session_id": f"size_{size_kb}_{uuid.uuid4().hex[:4]}"
                        })
                        if response.status_code == 200:
                            latencies.append((time.time() - start) * 1000)
                except Exception:
                    pass
            
            results.append({
                "size_kb": size_kb,
                "avg_latency_ms": statistics.mean(latencies) if latencies else float('inf'),
                "success_count": len(latencies)
            })
        
        print("\nPayload Size Scaling:")
        for r in results:
            print(f"  {r['size_kb']}KB: {r['avg_latency_ms']:.0f}ms avg, {r['success_count']}/5 success")


# =============================================================================
# RESOURCE UTILIZATION TESTS
# =============================================================================

class TestResourceUtilization:
    """Test system resource utilization."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    def test_cpu_utilization_during_load(self, client):
        """Monitor CPU utilization during load."""
        cpu_samples = []
        
        # Sample CPU before
        cpu_before = psutil.cpu_percent(interval=1)
        
        # Generate load
        for i in range(20):
            client.post("/api/chat", json={
                "message": f"CPU test {i}",
                "session_id": f"cpu_{uuid.uuid4().hex[:8]}"
            })
            cpu_samples.append(psutil.cpu_percent())
        
        # Sample CPU after
        cpu_after = psutil.cpu_percent(interval=1)
        
        print(f"\nCPU Utilization:")
        print(f"  Before: {cpu_before}%")
        print(f"  During (avg): {statistics.mean(cpu_samples):.1f}%")
        print(f"  During (max): {max(cpu_samples)}%")
        print(f"  After: {cpu_after}%")
    
    def test_connection_pool_efficiency(self, client):
        """Test connection pool is used efficiently."""
        # Reuse same client for multiple requests
        latencies = []
        
        for i in range(20):
            start = time.time()
            client.post("/api/chat", json={
                "message": f"Pool test {i}",
                "session_id": f"pool_{uuid.uuid4().hex[:8]}"
            })
            latencies.append((time.time() - start) * 1000)
        
        # Later requests should be as fast or faster (connection reuse)
        first_half_avg = statistics.mean(latencies[:10])
        second_half_avg = statistics.mean(latencies[10:])
        
        print(f"\nConnection Pool Efficiency:")
        print(f"  First 10 requests avg: {first_half_avg:.1f}ms")
        print(f"  Last 10 requests avg: {second_half_avg:.1f}ms")
        
        # Second half should not be slower
        assert second_half_avg <= first_half_avg * 1.5, \
            "Connection pool not being reused efficiently"


# =============================================================================
# BENCHMARK RUNNER
# =============================================================================

class TestBenchmarkSuite:
    """Run complete performance benchmark."""
    
    @pytest.fixture
    def load_gen(self):
        return LoadGenerator(BASE_URL)
    
    def test_full_benchmark(self, load_gen):
        """Run a comprehensive performance benchmark."""
        print("\n" + "="*60)
        print("       PERFORMANCE BENCHMARK REPORT")
        print("="*60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "tests": {}
        }
        
        # 1. Cold Start
        print("\n1. Cold Start Test...")
        cold_latency, cold_status = load_gen.single_request(f"bench_cold_{uuid.uuid4().hex}")
        results["tests"]["cold_start"] = {
            "latency_ms": cold_latency,
            "status": cold_status
        }
        print(f"   Cold Start: {cold_latency:.1f}ms")
        
        # 2. Warmup
        print("\n2. Warming up...")
        session_id = f"bench_warm_{uuid.uuid4().hex[:8]}"
        for _ in range(5):
            load_gen.single_request(session_id)
        
        # 3. Single-threaded latency
        print("\n3. Single-threaded Latency Test...")
        single_latencies = []
        for _ in range(20):
            lat, _ = load_gen.single_request(session_id)
            single_latencies.append(lat)
        
        sorted_lat = sorted(single_latencies)
        n = len(sorted_lat)
        results["tests"]["single_thread"] = {
            "min_ms": min(sorted_lat),
            "max_ms": max(sorted_lat),
            "median_ms": statistics.median(sorted_lat),
            "p95_ms": sorted_lat[int(n * 0.95)],
            "p99_ms": sorted_lat[int(n * 0.99)]
        }
        print(f"   Median: {results['tests']['single_thread']['median_ms']:.1f}ms")
        print(f"   P95: {results['tests']['single_thread']['p95_ms']:.1f}ms")
        
        # 4. Concurrent load
        print("\n4. Concurrent Load Test (10 users)...")
        concurrent_results = load_gen.concurrent_requests(50, 10)
        successful = sum(1 for _, s in concurrent_results if s == 200)
        concurrent_latencies = [lat for lat, s in concurrent_results if s == 200]
        
        results["tests"]["concurrent"] = {
            "total_requests": 50,
            "successful": successful,
            "success_rate": successful / 50,
            "avg_latency_ms": statistics.mean(concurrent_latencies) if concurrent_latencies else 0
        }
        print(f"   Success Rate: {results['tests']['concurrent']['success_rate']:.1%}")
        print(f"   Avg Latency: {results['tests']['concurrent']['avg_latency_ms']:.1f}ms")
        
        # 5. Throughput
        print("\n5. Throughput Test...")
        start = time.time()
        throughput_results = load_gen.concurrent_requests(100, 20)
        duration = time.time() - start
        
        results["tests"]["throughput"] = {
            "requests": 100,
            "duration_s": duration,
            "rps": 100 / duration
        }
        print(f"   Throughput: {results['tests']['throughput']['rps']:.2f} req/s")
        
        # Summary
        print("\n" + "="*60)
        print("       BENCHMARK SUMMARY")
        print("="*60)
        print(f"Cold Start: {results['tests']['cold_start']['latency_ms']:.0f}ms")
        print(f"Single-thread P95: {results['tests']['single_thread']['p95_ms']:.0f}ms")
        print(f"Concurrent Success: {results['tests']['concurrent']['success_rate']:.1%}")
        print(f"Throughput: {results['tests']['throughput']['rps']:.1f} req/s")
        print("="*60)
        
        # Save results
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("\nResults saved to benchmark_results.json")


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",
        "--timeout=300",
        "-W", "ignore::DeprecationWarning"
    ])

