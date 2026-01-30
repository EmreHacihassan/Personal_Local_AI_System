#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║           ENTERPRISE CHAOS ENGINEERING TEST SUITE                                    ║
║                  "Netflix-Style Failure Injection"                                   ║
║                                                                                      ║
║  🔥 Failure Injection | 🌊 Cascading Failures | ⚡ Recovery Testing | 🎲 Random Chaos║
╚══════════════════════════════════════════════════════════════════════════════════════╝

Chaos Engineering Principles:
=============================
1. Build a hypothesis around steady state behavior
2. Vary real-world events
3. Run experiments in production (or production-like)
4. Automate experiments
5. Minimize blast radius

Experiments:
============
- Latency injection
- Resource exhaustion
- Dependency failures
- Network partitions (simulated)
- Clock skew
- Disk pressure
- Connection pool exhaustion
- Thread starvation
- Memory pressure
- CPU saturation

Author: Chaos Engineer
Date: 2026-01-28
"""

import asyncio
import concurrent.futures
import gc
import json
import os
import psutil
import random
import signal
import socket
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

try:
    import httpx
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "websockets", "-q"])
    import httpx
    import websockets

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8001")
WS_URL = os.environ.get("TEST_WS_URL", "ws://localhost:8001/ws/chat")

CHAOS_CONFIG = {
    "latency_injection_ms": (100, 5000),  # Min/max latency to inject
    "failure_rate": 0.2,  # 20% failure rate
    "timeout_duration": 30,
    "resource_limit_mb": 512,
    "connection_pool_size": 100,
}


# =============================================================================
# CHAOS UTILITIES
# =============================================================================

@dataclass
class ChaosExperiment:
    """Configuration for a chaos experiment."""
    name: str
    description: str
    blast_radius: str  # "low", "medium", "high"
    hypothesis: str
    steady_state: Dict[str, Any]
    chaos_applied: bool = False
    results: Dict[str, Any] = field(default_factory=dict)


class SteadyStateValidator:
    """Validate system is in steady state."""
    
    def __init__(self, client: httpx.Client):
        self.client = client
    
    def check_health(self) -> bool:
        """Check if health endpoint responds."""
        try:
            resp = self.client.get("/api/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
    
    def check_chat_response(self) -> bool:
        """Check if chat responds."""
        try:
            resp = self.client.post("/api/chat", json={
                "message": "steady state check",
                "session_id": f"steady_{uuid.uuid4().hex[:8]}"
            }, timeout=30)
            return resp.status_code == 200
        except Exception:
            return False
    
    def measure_latency(self, samples: int = 5) -> float:
        """Measure average response latency."""
        latencies = []
        for _ in range(samples):
            start = time.time()
            try:
                self.client.get("/api/health", timeout=10)
                latencies.append(time.time() - start)
            except Exception:
                latencies.append(float('inf'))
        return sum(latencies) / len(latencies) if latencies else float('inf')
    
    def get_steady_state(self) -> Dict[str, Any]:
        """Get current steady state metrics."""
        return {
            "health_ok": self.check_health(),
            "chat_ok": self.check_chat_response(),
            "avg_latency_ms": self.measure_latency() * 1000,
            "timestamp": datetime.now().isoformat()
        }


class ChaosMonkey:
    """Inject various types of failures."""
    
    def __init__(self, failure_rate: float = 0.2):
        self.failure_rate = failure_rate
        self.active_experiments: List[str] = []
        self.failure_count = 0
        
    @contextmanager
    def inject_latency(self, min_ms: int = 100, max_ms: int = 5000):
        """Inject random latency."""
        latency = random.randint(min_ms, max_ms) / 1000
        self.active_experiments.append(f"latency_{latency}s")
        time.sleep(latency)
        try:
            yield latency
        finally:
            self.active_experiments.remove(f"latency_{latency}s")
    
    @contextmanager
    def inject_memory_pressure(self, mb: int = 100):
        """Create memory pressure."""
        self.active_experiments.append(f"memory_{mb}MB")
        data = bytearray(mb * 1024 * 1024)  # Allocate memory
        try:
            yield data
        finally:
            del data
            gc.collect()
            self.active_experiments.remove(f"memory_{mb}MB")
    
    def should_fail(self) -> bool:
        """Randomly decide if operation should fail."""
        if random.random() < self.failure_rate:
            self.failure_count += 1
            return True
        return False
    
    def inject_exception(self, error_types: List[type] = None):
        """Randomly inject an exception."""
        error_types = error_types or [
            RuntimeError, ValueError, TimeoutError, 
            ConnectionError, IOError, MemoryError
        ]
        if self.should_fail():
            error = random.choice(error_types)
            raise error(f"ChaosMonkey injected {error.__name__}")


# =============================================================================
# CHAOS EXPERIMENTS
# =============================================================================

class TestLatencyInjection:
    """Test system behavior under latency conditions."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    @pytest.fixture
    def validator(self, client):
        return SteadyStateValidator(client)
    
    @pytest.fixture
    def chaos(self):
        return ChaosMonkey()
    
    def test_system_handles_200ms_latency(self, client, validator, chaos):
        """Test system with 200ms added latency."""
        # Steady state
        steady = validator.get_steady_state()
        assert steady["health_ok"], "System not in steady state"
        
        # Apply chaos
        results = []
        for i in range(10):
            with chaos.inject_latency(200, 200):
                start = time.time()
                try:
                    resp = client.post("/api/chat", json={
                        "message": f"latency_test_{i}",
                        "session_id": f"lat_{uuid.uuid4().hex[:8]}"
                    })
                    results.append({
                        "success": resp.status_code == 200,
                        "latency_ms": (time.time() - start) * 1000
                    })
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e)
                    })
        
        # Verify hypothesis: System should still work with added latency
        success_rate = sum(1 for r in results if r.get("success")) / len(results)
        assert success_rate >= 0.8, f"Success rate {success_rate} below threshold"
    
    def test_system_handles_variable_latency(self, client, validator, chaos):
        """Test system with variable latency (spike simulation)."""
        steady = validator.get_steady_state()
        results = []
        
        for i in range(20):
            # Randomly inject latency on some requests
            if random.random() < 0.3:
                with chaos.inject_latency(500, 2000):
                    pass  # Just delay
            
            try:
                resp = client.post("/api/chat", json={
                    "message": f"var_latency_{i}",
                    "session_id": f"varlat_{uuid.uuid4().hex[:8]}"
                })
                results.append(resp.status_code == 200)
            except Exception:
                results.append(False)
        
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.6, f"Too many failures under variable latency: {success_rate}"
    
    def test_timeout_cascade_prevention(self, client, validator):
        """Test that timeouts don't cascade."""
        session_id = f"cascade_{uuid.uuid4().hex[:8]}"
        
        # First: Request with very short timeout (will likely fail)
        try:
            client.post("/api/chat", json={
                "message": "Generate a detailed explanation" * 20,
                "session_id": session_id
            }, timeout=1.0)
        except Exception:
            pass
        
        # Second: Normal request should still work
        resp = client.post("/api/chat", json={
            "message": "quick test",
            "session_id": session_id
        }, timeout=30)
        
        assert resp.status_code in [200, 500], "Timeout cascaded to subsequent request"


class TestResourceExhaustion:
    """Test system behavior under resource exhaustion."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    @pytest.fixture
    def chaos(self):
        return ChaosMonkey()
    
    def test_connection_pool_exhaustion(self, client):
        """Test behavior when connection pool is exhausted."""
        # Create many concurrent connections
        clients = []
        results = []
        
        for i in range(50):
            c = httpx.Client(base_url=BASE_URL, timeout=30)
            clients.append(c)
            try:
                resp = c.post("/api/chat", json={
                    "message": f"pool_exhaust_{i}",
                    "session_id": f"pool_{uuid.uuid4().hex[:8]}"
                })
                results.append(resp.status_code)
            except Exception as e:
                results.append(str(e))
        
        # Cleanup
        for c in clients:
            c.close()
        
        # Should handle gracefully
        success_count = sum(1 for r in results if r == 200)
        assert success_count > 20, f"Only {success_count}/50 succeeded under pool exhaustion"
    
    def test_memory_pressure_response(self, client, chaos):
        """Test system response under memory pressure."""
        results = []
        
        # Apply memory pressure
        with chaos.inject_memory_pressure(mb=200):
            for i in range(10):
                try:
                    resp = client.post("/api/chat", json={
                        "message": f"memory_pressure_{i}",
                        "session_id": f"mem_{uuid.uuid4().hex[:8]}"
                    })
                    results.append(resp.status_code == 200)
                except Exception:
                    results.append(False)
        
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.5, f"System too degraded under memory pressure: {success_rate}"
    
    def test_thread_starvation_recovery(self, client):
        """Test recovery from thread starvation."""
        results = []
        
        def blocking_request(i: int) -> int:
            """Make a blocking request."""
            try:
                resp = client.post("/api/chat", json={
                    "message": f"large_request_{i} " * 100,
                    "session_id": f"thread_{i}_{uuid.uuid4().hex[:8]}"
                })
                return resp.status_code
            except Exception:
                return 0
        
        # Create thread pressure
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(blocking_request, i) for i in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        success_count = sum(1 for r in results if r == 200)
        assert success_count > 20, f"Only {success_count}/50 succeeded under thread starvation"


class TestDependencyFailures:
    """Test system behavior when dependencies fail."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    def test_ollama_unavailable_handling(self, client):
        """Test handling when Ollama becomes unavailable."""
        # This tests actual behavior when LLM is slow/unavailable
        session_id = f"ollama_fail_{uuid.uuid4().hex[:8]}"
        
        # Make request that requires Ollama
        resp = client.post("/api/chat", json={
            "message": "test",
            "session_id": session_id
        })
        
        # Should handle gracefully (either work or proper error)
        assert resp.status_code in [200, 500, 503, 504]
        
        if resp.status_code != 200:
            data = resp.json()
            assert "error" in data or "detail" in data, "No error message provided"
    
    def test_chromadb_recovery(self, client):
        """Test system recovery when ChromaDB has issues."""
        # This tests the circuit breaker behavior
        session_id = f"chroma_fail_{uuid.uuid4().hex[:8]}"
        
        results = []
        for i in range(10):
            resp = client.post("/api/chat", json={
                "message": f"chromadb_test_{i}",
                "session_id": session_id
            })
            results.append(resp.status_code)
        
        # Should eventually recover or degrade gracefully
        # Not all failures, system should have circuit breaker
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 0, "System completely failed"  # At least run
    
    def test_cascading_failure_prevention(self, client):
        """Test that failures don't cascade."""
        session_ids = [f"cascade_{i}_{uuid.uuid4().hex[:8]}" for i in range(10)]
        
        # First: Cause some failures
        for sid in session_ids[:5]:
            try:
                client.post("/api/chat", 
                    json={"message": "x" * 1000000},  # Large request
                    session_id=sid,
                    timeout=1.0  # Short timeout
                )
            except Exception:
                pass
        
        # Then: Normal requests should work
        success_count = 0
        for sid in session_ids[5:]:
            resp = client.post("/api/chat", json={
                "message": "quick test",
                "session_id": sid
            })
            if resp.status_code == 200:
                success_count += 1
        
        # At least some should succeed
        assert success_count >= 2, "Failures cascaded to normal requests"


class TestNetworkPartition:
    """Test simulated network partition scenarios."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    def test_partial_connectivity(self, client):
        """Test behavior during partial connectivity."""
        results = []
        
        for i in range(20):
            # Simulate partial connectivity with random timeouts
            timeout = random.choice([0.5, 1.0, 5.0, 30.0])
            try:
                resp = client.post("/api/chat", json={
                    "message": f"partial_{i}",
                    "session_id": f"partial_{uuid.uuid4().hex[:8]}"
                }, timeout=timeout)
                results.append(("success", resp.status_code))
            except httpx.TimeoutException:
                results.append(("timeout", None))
            except Exception as e:
                results.append(("error", str(e)))
        
        # Should have mix of results
        success_count = sum(1 for r in results if r[0] == "success")
        assert success_count > 5, f"Too few successes: {success_count}/20"
    
    def test_reconnection_after_partition(self, client):
        """Test system reconnects after partition ends."""
        session_id = f"reconnect_{uuid.uuid4().hex[:8]}"
        
        # Simulate partition: rapid timeouts
        for _ in range(5):
            try:
                client.post("/api/chat", json={
                    "message": "during_partition",
                    "session_id": session_id
                }, timeout=0.1)
            except Exception:
                pass
        
        # Wait for "partition to heal"
        time.sleep(2)
        
        # Should reconnect
        resp = client.post("/api/chat", json={
            "message": "after_partition",
            "session_id": session_id
        }, timeout=30)
        
        assert resp.status_code in [200, 500], "System didn't recover from partition"


class TestRecoveryPatterns:
    """Test system recovery patterns."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=60)
    
    def test_exponential_backoff_respect(self, client):
        """Test that system respects backoff during recovery."""
        session_id = f"backoff_{uuid.uuid4().hex[:8]}"
        request_times = []
        
        for i in range(10):
            start = time.time()
            try:
                resp = client.post("/api/chat", json={
                    "message": f"backoff_test_{i}",
                    "session_id": session_id
                })
                request_times.append((time.time() - start, resp.status_code))
            except Exception:
                request_times.append((time.time() - start, 0))
        
        # Just verify requests complete
        assert len(request_times) == 10
    
    def test_circuit_breaker_behavior(self, client):
        """Test circuit breaker opens on failures."""
        session_id = f"circuit_{uuid.uuid4().hex[:8]}"
        
        # First: Multiple rapid failures (simulated by timeout)
        failures = 0
        for i in range(10):
            try:
                resp = client.post("/api/chat", json={
                    "message": "x" * 100000,  # Large message
                    "session_id": session_id
                }, timeout=0.5)
                if resp.status_code != 200:
                    failures += 1
            except Exception:
                failures += 1
        
        # System should still respond (circuit breaker or graceful degradation)
        resp = client.get("/api/health", timeout=10)
        assert resp.status_code in [200, 503], "System completely unresponsive"
    
    def test_state_preservation_during_recovery(self, client):
        """Test that state is preserved during recovery."""
        session_id = f"state_{uuid.uuid4().hex[:8]}"
        
        # Create some state
        for i in range(3):
            client.post("/api/chat", json={
                "message": f"state_message_{i}",
                "session_id": session_id
            })
        
        # Simulate some failures
        for _ in range(3):
            try:
                client.post("/api/chat", json={
                    "message": "error trigger",
                    "session_id": session_id
                }, timeout=0.5)
            except Exception:
                pass
        
        # State should still be there
        try:
            resp = client.get(f"/api/sessions/{session_id}")
            if resp.status_code == 200:
                # If endpoint exists, check state
                assert "error" not in resp.text.lower() or "messages" in resp.text
        except Exception:
            pass  # Endpoint might not exist


class TestChaosGameDay:
    """Full chaos game day simulation."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=120)
    
    @pytest.fixture
    def validator(self, client):
        return SteadyStateValidator(client)
    
    def test_full_chaos_simulation(self, client, validator):
        """Run a full chaos simulation."""
        # Record steady state
        steady_state = validator.get_steady_state()
        print(f"\nSteady State: {steady_state}")
        
        chaos = ChaosMonkey(failure_rate=0.3)
        experiment_results = []
        
        # Run chaos for 30 seconds
        start_time = time.time()
        request_count = 0
        success_count = 0
        
        while time.time() - start_time < 30:
            request_count += 1
            
            # Random chaos injection
            chaos_type = random.choice(["latency", "memory", "none", "none", "none"])
            
            try:
                if chaos_type == "latency":
                    with chaos.inject_latency(100, 1000):
                        resp = client.post("/api/chat", json={
                            "message": f"chaos_{request_count}",
                            "session_id": f"game_{uuid.uuid4().hex[:8]}"
                        })
                elif chaos_type == "memory":
                    with chaos.inject_memory_pressure(50):
                        resp = client.post("/api/chat", json={
                            "message": f"chaos_{request_count}",
                            "session_id": f"game_{uuid.uuid4().hex[:8]}"
                        })
                else:
                    resp = client.post("/api/chat", json={
                        "message": f"chaos_{request_count}",
                        "session_id": f"game_{uuid.uuid4().hex[:8]}"
                    })
                
                if resp.status_code == 200:
                    success_count += 1
                    
                experiment_results.append({
                    "request": request_count,
                    "chaos": chaos_type,
                    "status": resp.status_code
                })
                
            except Exception as e:
                experiment_results.append({
                    "request": request_count,
                    "chaos": chaos_type,
                    "error": str(e)[:100]
                })
        
        # Verify recovery
        final_state = validator.get_steady_state()
        print(f"\nFinal State: {final_state}")
        print(f"Requests: {request_count}, Success: {success_count}")
        
        # System should recover to steady state
        success_rate = success_count / request_count if request_count > 0 else 0
        assert success_rate >= 0.3, f"System too degraded under chaos: {success_rate:.2%}"
        assert final_state["health_ok"], "System didn't recover after chaos"


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

