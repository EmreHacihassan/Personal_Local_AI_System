"""
Enterprise AI Assistant - Circuit Breaker
==========================================

Servis dayanıklılığı için Circuit Breaker pattern.
Başarısız servis çağrılarını yönetir ve cascade failure'ı önler.
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime

from .logger import get_logger
from .exceptions import CircuitBreakerOpenError

logger = get_logger("circuit_breaker")


class CircuitState(str, Enum):
    """Circuit breaker durumları."""
    CLOSED = "closed"      # Normal çalışma
    OPEN = "open"          # Servis devre dışı
    HALF_OPEN = "half_open"  # Test aşaması


@dataclass
class CircuitStats:
    """Circuit breaker istatistikleri."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    def reset(self):
        """İstatistikleri sıfırla."""
        self.consecutive_failures = 0
        self.consecutive_successes = 0
    
    def record_success(self):
        """Başarılı çağrı kaydet."""
        self.total_calls += 1
        self.successful_calls += 1
        self.consecutive_successes += 1
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()
    
    def record_failure(self):
        """Başarısız çağrı kaydet."""
        self.total_calls += 1
        self.failed_calls += 1
        self.consecutive_failures += 1
        self.consecutive_successes = 0
        self.last_failure_time = datetime.now()
    
    def record_rejection(self):
        """Reddedilen çağrı kaydet."""
        self.total_calls += 1
        self.rejected_calls += 1
    
    @property
    def failure_rate(self) -> float:
        """Hata oranı."""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    @property
    def success_rate(self) -> float:
        """Başarı oranı."""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "failure_rate": round(self.failure_rate, 4),
            "success_rate": round(self.success_rate, 4),
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
        }


class CircuitBreaker:
    """
    Circuit Breaker implementation.
    
    Üç durum:
    - CLOSED: Normal çalışma, hatalar sayılır
    - OPEN: Çağrılar engellenir, belirli süre beklenir
    - HALF_OPEN: Test çağrısı yapılır, başarılı olursa CLOSED'a geçer
    
    Kullanım:
        breaker = CircuitBreaker(name="ollama", failure_threshold=5)
        
        @breaker
        def call_ollama():
            ...
        
        # veya
        result = breaker.call(call_ollama)
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 30,
        excluded_exceptions: tuple = (),
    ):
        """
        Circuit Breaker oluştur.
        
        Args:
            name: Breaker adı (loglama için)
            failure_threshold: OPEN durumuna geçmek için gereken ardışık hata sayısı
            success_threshold: HALF_OPEN'dan CLOSED'a geçmek için gereken başarı sayısı
            timeout_seconds: OPEN durumunda bekleme süresi
            excluded_exceptions: Circuit'i etkilemeyen exception türleri
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.excluded_exceptions = excluded_exceptions
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._opened_at: Optional[float] = None
        self._lock = threading.RLock()
    
    @property
    def state(self) -> CircuitState:
        """Mevcut durum."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Timeout kontrolü
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"[{self.name}] Circuit HALF_OPEN - test aşaması")
            return self._state
    
    @property
    def stats(self) -> CircuitStats:
        """İstatistikler."""
        return self._stats
    
    def _should_attempt_reset(self) -> bool:
        """OPEN timeout'u doldu mu?"""
        if self._opened_at is None:
            return False
        return time.time() - self._opened_at >= self.timeout_seconds
    
    def _open_circuit(self):
        """Circuit'i aç."""
        self._state = CircuitState.OPEN
        self._opened_at = time.time()
        logger.warning(
            f"[{self.name}] Circuit OPEN - {self.failure_threshold} ardışık hata. "
            f"{self.timeout_seconds}s sonra yeniden denenecek."
        )
    
    def _close_circuit(self):
        """Circuit'i kapat (normal çalışma)."""
        self._state = CircuitState.CLOSED
        self._opened_at = None
        self._stats.reset()
        logger.info(f"[{self.name}] Circuit CLOSED - normal çalışma")
    
    def _handle_success(self):
        """Başarılı çağrı işle."""
        with self._lock:
            self._stats.record_success()
            
            if self._state == CircuitState.HALF_OPEN:
                if self._stats.consecutive_successes >= self.success_threshold:
                    self._close_circuit()
    
    def _handle_failure(self, exception: Exception):
        """Başarısız çağrı işle."""
        with self._lock:
            # Excluded exception kontrolü
            if isinstance(exception, self.excluded_exceptions):
                return
            
            self._stats.record_failure()
            
            if self._state == CircuitState.HALF_OPEN:
                self._open_circuit()
            elif self._state == CircuitState.CLOSED:
                if self._stats.consecutive_failures >= self.failure_threshold:
                    self._open_circuit()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Korumalı fonksiyon çağrısı.
        
        Args:
            func: Çağrılacak fonksiyon
            *args, **kwargs: Fonksiyon argümanları
            
        Returns:
            Fonksiyon sonucu
            
        Raises:
            CircuitBreakerOpenError: Circuit açıksa
        """
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            self._stats.record_rejection()
            raise CircuitBreakerOpenError(
                service_name=self.name,
                retry_after_seconds=self.timeout_seconds,
            )
        
        try:
            result = func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure(e)
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Asenkron korumalı fonksiyon çağrısı."""
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            self._stats.record_rejection()
            raise CircuitBreakerOpenError(
                service_name=self.name,
                retry_after_seconds=self.timeout_seconds,
            )
        
        try:
            result = await func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure(e)
            raise
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator olarak kullanım."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self.call_async(func, *args, **kwargs)
        
        # Async kontrolü
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    
    def reset(self):
        """Circuit'i sıfırla."""
        with self._lock:
            self._close_circuit()
            self._stats = CircuitStats()
    
    def force_open(self):
        """Circuit'i zorla aç."""
        with self._lock:
            self._open_circuit()
    
    def get_status(self) -> Dict[str, Any]:
        """Durum raporu."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout_seconds": self.timeout_seconds,
            "stats": self._stats.to_dict(),
        }


# =============================================================================
# CIRCUIT BREAKER REGISTRY
# =============================================================================

class CircuitBreakerRegistry:
    """
    Circuit Breaker kayıt defteri.
    
    Tüm circuit breaker'ları merkezi yönetim.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._breakers = {}  # Dict[str, CircuitBreaker]
        return cls._instance
    
    def register(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 30,
        excluded_exceptions: tuple = (),
    ) -> CircuitBreaker:
        """
        Yeni circuit breaker kaydet veya mevcut olanı döndür.
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
                excluded_exceptions=excluded_exceptions,
            )
        return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Circuit breaker al."""
        return self._breakers.get(name)
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Tüm circuit breaker durumları."""
        return {
            name: breaker.get_status()
            for name, breaker in self._breakers.items()
        }
    
    def reset_all(self):
        """Tüm circuit breaker'ları sıfırla."""
        for breaker in self._breakers.values():
            breaker.reset()


# Singleton instance
circuit_registry = CircuitBreakerRegistry()


# =============================================================================
# PRE-CONFIGURED CIRCUIT BREAKERS
# =============================================================================

# Ollama servisi için
ollama_circuit = circuit_registry.register(
    name="ollama",
    failure_threshold=3,
    success_threshold=2,
    timeout_seconds=30,
)

# ChromaDB için
chromadb_circuit = circuit_registry.register(
    name="chromadb",
    failure_threshold=5,
    success_threshold=1,
    timeout_seconds=15,
)

# External API'ler için
external_api_circuit = circuit_registry.register(
    name="external_api",
    failure_threshold=5,
    success_threshold=2,
    timeout_seconds=60,
)


__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "CircuitStats",
    "CircuitBreakerRegistry",
    "circuit_registry",
    "ollama_circuit",
    "chromadb_circuit",
    "external_api_circuit",
]
