"""
Enterprise AI Assistant - Performance Optimization Module
Endüstri Standartlarında Performans Optimizasyonu

ENTERPRISE FEATURES:
- Connection pooling for all HTTP clients
- Request deduplication
- Batch operation queuing
- Performance monitoring & metrics
- Automatic resource cleanup
- Circuit breaker pattern
- Rate limiting
"""

import time
import threading
import hashlib
from typing import Dict, Any, Optional, Callable, List, Tuple
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import queue
import weakref


@dataclass
class CircuitState:
    """Circuit breaker durumu."""
    failures: int = 0
    last_failure_time: Optional[float] = None
    state: str = "closed"  # closed, open, half_open
    

class CircuitBreaker:
    """
    Circuit Breaker Pattern implementasyonu.
    
    Hatalı servislere tekrar tekrar istek göndermekten kaçınır.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_requests: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        self._states: Dict[str, CircuitState] = defaultdict(CircuitState)
        self._lock = threading.Lock()
    
    def is_allowed(self, service_name: str) -> bool:
        """Servise istek gönderilebilir mi?"""
        with self._lock:
            state = self._states[service_name]
            
            if state.state == "closed":
                return True
            
            if state.state == "open":
                # Recovery timeout geçti mi?
                if state.last_failure_time and \
                   time.time() - state.last_failure_time > self.recovery_timeout:
                    state.state = "half_open"
                    state.failures = 0
                    return True
                return False
            
            # half_open
            return state.failures < self.half_open_requests
    
    def record_success(self, service_name: str):
        """Başarılı istek kaydet."""
        with self._lock:
            state = self._states[service_name]
            if state.state == "half_open":
                state.state = "closed"
            state.failures = 0
    
    def record_failure(self, service_name: str):
        """Başarısız istek kaydet."""
        with self._lock:
            state = self._states[service_name]
            state.failures += 1
            state.last_failure_time = time.time()
            
            if state.failures >= self.failure_threshold:
                state.state = "open"
    
    def get_status(self) -> Dict[str, Any]:
        """Tüm servislerin durumunu al."""
        with self._lock:
            return {
                name: {
                    "state": state.state,
                    "failures": state.failures,
                }
                for name, state in self._states.items()
            }


class RequestDeduplicator:
    """
    Aynı anda yapılan duplicate istekleri birleştirir.
    
    Örneğin, aynı sorgu için birden fazla istek gelirse,
    sadece bir kez işlenir ve sonuç paylaşılır.
    """
    
    def __init__(self, ttl_seconds: float = 5.0):
        self.ttl_seconds = ttl_seconds
        self._pending: Dict[str, Tuple[threading.Event, Any, Optional[Exception]]] = {}
        self._lock = threading.Lock()
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Request key oluştur."""
        data = f"{args}|{sorted(kwargs.items())}"
        return hashlib.sha256(data.encode()).hexdigest()[:24]
    
    def deduplicate(self, key: str, fn: Callable, *args, **kwargs) -> Any:
        """
        İsteği deduplicate et.
        
        Eğer aynı key için bekleyen bir istek varsa, sonucunu bekle.
        Yoksa, isteği yap ve sonucu paylaş.
        """
        with self._lock:
            if key in self._pending:
                # Bekleyen istek var, sonucunu bekle
                event, _, _ = self._pending[key]
                wait = True
            else:
                # Yeni istek
                event = threading.Event()
                self._pending[key] = (event, None, None)
                wait = False
        
        if wait:
            # Sonucu bekle
            event.wait(timeout=60.0)
            with self._lock:
                if key in self._pending:
                    _, result, error = self._pending[key]
                    if error:
                        raise error
                    return result
                return None
        
        # İsteği yap
        try:
            result = fn(*args, **kwargs)
            with self._lock:
                event_ref, _, _ = self._pending[key]
                self._pending[key] = (event_ref, result, None)
                event_ref.set()
            return result
        except Exception as e:
            with self._lock:
                event_ref, _, _ = self._pending[key]
                self._pending[key] = (event_ref, None, e)
                event_ref.set()
            raise
        finally:
            # Cleanup after TTL
            def cleanup():
                time.sleep(self.ttl_seconds)
                with self._lock:
                    if key in self._pending:
                        del self._pending[key]
            
            cleanup_thread = threading.Thread(target=cleanup, daemon=True)
            cleanup_thread.start()


class PerformanceMetrics:
    """
    Performans metrikleri toplama ve raporlama.
    """
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
        self._start_time = time.time()
    
    def record_timing(self, name: str, duration_ms: float):
        """Süre metriği kaydet."""
        with self._lock:
            self._metrics[name].append(duration_ms)
            # Son 1000 kaydı tut
            if len(self._metrics[name]) > 1000:
                self._metrics[name] = self._metrics[name][-1000:]
    
    def increment_counter(self, name: str, value: int = 1):
        """Sayaç artır."""
        with self._lock:
            self._counters[name] += value
    
    def get_summary(self) -> Dict[str, Any]:
        """Özet rapor al."""
        with self._lock:
            uptime = time.time() - self._start_time
            
            timing_summary = {}
            for name, values in self._metrics.items():
                if values:
                    timing_summary[name] = {
                        "count": len(values),
                        "avg_ms": sum(values) / len(values),
                        "min_ms": min(values),
                        "max_ms": max(values),
                        "p95_ms": sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max(values),
                    }
            
            return {
                "uptime_seconds": uptime,
                "counters": dict(self._counters),
                "timings": timing_summary,
            }
    
    def reset(self):
        """Metrikleri sıfırla."""
        with self._lock:
            self._metrics.clear()
            self._counters.clear()
            self._start_time = time.time()


class RateLimiter:
    """
    Token bucket rate limiter.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: float = 60.0,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str = "default") -> bool:
        """İstek izni kontrol et."""
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            # Eski istekleri temizle
            self._requests[key] = [
                t for t in self._requests[key] if t > window_start
            ]
            
            if len(self._requests[key]) >= self.max_requests:
                return False
            
            self._requests[key].append(now)
            return True
    
    def get_remaining(self, key: str = "default") -> int:
        """Kalan istek sayısını al."""
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            current = len([t for t in self._requests[key] if t > window_start])
            return max(0, self.max_requests - current)


class BatchProcessor:
    """
    Batch işleme queue'su.
    
    Küçük istekleri birleştirip toplu işler.
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        max_wait_ms: float = 100.0,
        processor_fn: Optional[Callable] = None,
    ):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.processor_fn = processor_fn
        self._queue: queue.Queue = queue.Queue()
        self._results: Dict[str, Any] = {}
        self._events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Worker thread başlat."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
    
    def stop(self):
        """Worker thread durdur."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
    
    def submit(self, item: Any, item_id: str) -> Any:
        """İş parçasını submit et ve sonucu bekle."""
        event = threading.Event()
        
        with self._lock:
            self._events[item_id] = event
        
        self._queue.put((item_id, item))
        
        # Sonucu bekle
        event.wait(timeout=30.0)
        
        with self._lock:
            result = self._results.pop(item_id, None)
            self._events.pop(item_id, None)
        
        return result
    
    def _worker(self):
        """Batch processing worker."""
        while self._running:
            batch = []
            batch_ids = []
            
            # Batch topla
            start_time = time.time()
            while len(batch) < self.batch_size:
                remaining_ms = self.max_wait_ms - (time.time() - start_time) * 1000
                if remaining_ms <= 0:
                    break
                
                try:
                    item_id, item = self._queue.get(timeout=remaining_ms / 1000)
                    batch.append(item)
                    batch_ids.append(item_id)
                except queue.Empty:
                    break
            
            if not batch:
                continue
            
            # Batch işle
            if self.processor_fn:
                try:
                    results = self.processor_fn(batch)
                except Exception as e:
                    results = [e] * len(batch)
            else:
                results = batch
            
            # Sonuçları dağıt
            with self._lock:
                for item_id, result in zip(batch_ids, results):
                    self._results[item_id] = result
                    if item_id in self._events:
                        self._events[item_id].set()


def timed(metrics: PerformanceMetrics, name: str):
    """Decorator: Fonksiyon süresini ölç."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                return fn(*args, **kwargs)
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics.record_timing(name, duration_ms)
        return wrapper
    return decorator


def rate_limited(limiter: RateLimiter, key: str = "default"):
    """Decorator: Rate limiting uygula."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not limiter.is_allowed(key):
                raise Exception(f"Rate limit exceeded for {key}")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def circuit_protected(breaker: CircuitBreaker, service_name: str):
    """Decorator: Circuit breaker uygula."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not breaker.is_allowed(service_name):
                raise Exception(f"Circuit breaker open for {service_name}")
            try:
                result = fn(*args, **kwargs)
                breaker.record_success(service_name)
                return result
            except Exception as e:
                breaker.record_failure(service_name)
                raise
        return wrapper
    return decorator


# Global instances
circuit_breaker = CircuitBreaker()
rate_limiter = RateLimiter()
performance_metrics = PerformanceMetrics()
request_deduplicator = RequestDeduplicator()


__all__ = [
    "CircuitBreaker",
    "RateLimiter",
    "PerformanceMetrics",
    "RequestDeduplicator",
    "BatchProcessor",
    "timed",
    "rate_limited",
    "circuit_protected",
    "circuit_breaker",
    "rate_limiter",
    "performance_metrics",
    "request_deduplicator",
]
