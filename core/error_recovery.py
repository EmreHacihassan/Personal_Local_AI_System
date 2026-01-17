"""
Enterprise AI Assistant - Advanced Error Recovery
Endüstri Standartlarında Hata Kurtarma Sistemi

ENTERPRISE FEATURES:
- Graceful degradation
- Automatic retry with backoff
- Error categorization
- Fallback strategies
- Self-healing mechanisms
- Comprehensive error logging
- Recovery metrics
"""

import time
import traceback
import threading
from typing import Dict, Any, Optional, Callable, List, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import logging


class ErrorSeverity(Enum):
    """Hata şiddeti seviyeleri."""
    LOW = "low"           # Uyarı, işlem devam eder
    MEDIUM = "medium"     # Hata, fallback kullanılır
    HIGH = "high"         # Kritik, işlem durur
    CRITICAL = "critical" # Sistem seviyesi, acil müdahale


class ErrorCategory(Enum):
    """Hata kategorileri."""
    NETWORK = "network"           # Ağ hataları
    TIMEOUT = "timeout"           # Zaman aşımı
    RESOURCE = "resource"         # Kaynak yetersizliği
    VALIDATION = "validation"     # Doğrulama hataları
    EXTERNAL_SERVICE = "external" # Dış servis hataları
    INTERNAL = "internal"         # İç hatalar
    CONFIGURATION = "config"      # Yapılandırma hataları
    UNKNOWN = "unknown"           # Bilinmeyen hatalar


@dataclass
class ErrorContext:
    """Hata bağlamı."""
    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    component: str = ""
    operation: str = ""
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": str(self.error),
            "error_type": type(self.error).__name__,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


class ErrorClassifier:
    """
    Hataları kategorize eder.
    """
    
    # Hata pattern'leri
    PATTERNS = {
        ErrorCategory.NETWORK: [
            "ConnectionError", "ConnectionRefused", "ConnectionReset",
            "socket.error", "NetworkError", "BrokenPipe"
        ],
        ErrorCategory.TIMEOUT: [
            "TimeoutError", "Timeout", "deadline exceeded", "timed out"
        ],
        ErrorCategory.RESOURCE: [
            "MemoryError", "OutOfMemory", "ResourceExhausted",
            "No space left", "disk full"
        ],
        ErrorCategory.VALIDATION: [
            "ValidationError", "ValueError", "TypeError", "KeyError",
            "invalid", "malformed"
        ],
        ErrorCategory.EXTERNAL_SERVICE: [
            "503", "502", "504", "ServiceUnavailable",
            "rate limit", "quota exceeded"
        ],
        ErrorCategory.CONFIGURATION: [
            "ConfigError", "SettingsError", "not configured",
            "missing required"
        ],
    }
    
    @classmethod
    def classify(cls, error: Exception) -> tuple:
        """
        Hatayı kategorize et ve şiddetini belirle.
        
        Returns:
            (ErrorCategory, ErrorSeverity)
        """
        error_str = f"{type(error).__name__}: {str(error)}"
        
        for category, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in error_str.lower():
                    severity = cls._get_severity(category)
                    return category, severity
        
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM
    
    @classmethod
    def _get_severity(cls, category: ErrorCategory) -> ErrorSeverity:
        """Kategoriye göre varsayılan şiddet."""
        severity_map = {
            ErrorCategory.NETWORK: ErrorSeverity.MEDIUM,
            ErrorCategory.TIMEOUT: ErrorSeverity.MEDIUM,
            ErrorCategory.RESOURCE: ErrorSeverity.HIGH,
            ErrorCategory.VALIDATION: ErrorSeverity.LOW,
            ErrorCategory.EXTERNAL_SERVICE: ErrorSeverity.MEDIUM,
            ErrorCategory.CONFIGURATION: ErrorSeverity.HIGH,
            ErrorCategory.INTERNAL: ErrorSeverity.HIGH,
            ErrorCategory.UNKNOWN: ErrorSeverity.MEDIUM,
        }
        return severity_map.get(category, ErrorSeverity.MEDIUM)


T = TypeVar("T")


class FallbackChain(Generic[T]):
    """
    Fallback zinciri.
    
    Ana işlem başarısız olursa, sırayla fallback'leri dener.
    """
    
    def __init__(self):
        self._handlers: List[tuple] = []  # [(name, handler, condition)]
    
    def add(
        self,
        name: str,
        handler: Callable[..., T],
        condition: Optional[Callable[[ErrorContext], bool]] = None,
    ) -> "FallbackChain[T]":
        """Fallback handler ekle."""
        self._handlers.append((name, handler, condition))
        return self
    
    def execute(
        self,
        primary: Callable[..., T],
        *args,
        component: str = "",
        operation: str = "",
        **kwargs
    ) -> tuple:
        """
        Ana işlemi çalıştır, başarısız olursa fallback'leri dene.
        
        Returns:
            (result, handler_name, error_context)
        """
        last_error = None
        
        # Ana işlemi dene
        try:
            result = primary(*args, **kwargs)
            return result, "primary", None
        except Exception as e:
            category, severity = ErrorClassifier.classify(e)
            last_error = ErrorContext(
                error=e,
                category=category,
                severity=severity,
                component=component,
                operation=operation,
                stack_trace=traceback.format_exc(),
            )
        
        # Fallback'leri dene
        for name, handler, condition in self._handlers:
            # Koşul varsa kontrol et
            if condition and not condition(last_error):
                continue
            
            try:
                result = handler(*args, **kwargs)
                return result, name, last_error
            except Exception as e:
                category, severity = ErrorClassifier.classify(e)
                last_error = ErrorContext(
                    error=e,
                    category=category,
                    severity=severity,
                    component=component,
                    operation=f"{operation}_fallback_{name}",
                    stack_trace=traceback.format_exc(),
                )
        
        # Tüm fallback'ler başarısız
        raise last_error.error


class RetryStrategy:
    """
    Yeniden deneme stratejileri.
    """
    
    @staticmethod
    def constant(delay: float = 1.0):
        """Sabit bekleme."""
        def strategy(attempt: int) -> float:
            return delay
        return strategy
    
    @staticmethod
    def linear(base: float = 1.0, increment: float = 1.0):
        """Doğrusal artış."""
        def strategy(attempt: int) -> float:
            return base + (attempt * increment)
        return strategy
    
    @staticmethod
    def exponential(base: float = 1.0, multiplier: float = 2.0, max_delay: float = 60.0):
        """Üstel artış."""
        def strategy(attempt: int) -> float:
            delay = base * (multiplier ** attempt)
            return min(delay, max_delay)
        return strategy
    
    @staticmethod
    def fibonacci():
        """Fibonacci artış."""
        def strategy(attempt: int) -> float:
            a, b = 1, 1
            for _ in range(attempt):
                a, b = b, a + b
            return float(a)
        return strategy


class ErrorRecoveryManager:
    """
    Merkezi hata kurtarma yöneticisi.
    """
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self._error_log: List[ErrorContext] = []
        self._recovery_actions: Dict[ErrorCategory, Callable] = {}
        self._metrics = {
            "total_errors": 0,
            "recovered": 0,
            "failed": 0,
            "by_category": {},
            "by_severity": {},
        }
        self._lock = threading.Lock()
    
    def register_recovery_action(
        self,
        category: ErrorCategory,
        action: Callable[[ErrorContext], bool],
    ):
        """Kategori için kurtarma aksiyonu kaydet."""
        self._recovery_actions[category] = action
    
    def handle_error(self, context: ErrorContext) -> bool:
        """
        Hatayı işle ve kurtarmayı dene.
        
        Returns:
            Kurtarma başarılı mı
        """
        with self._lock:
            # Log
            self._error_log.append(context)
            if len(self._error_log) > self.max_errors:
                self._error_log = self._error_log[-self.max_errors:]
            
            # Metrics güncelle
            self._metrics["total_errors"] += 1
            self._metrics["by_category"][context.category.value] = \
                self._metrics["by_category"].get(context.category.value, 0) + 1
            self._metrics["by_severity"][context.severity.value] = \
                self._metrics["by_severity"].get(context.severity.value, 0) + 1
        
        # Kurtarma aksiyonu var mı?
        recovery_action = self._recovery_actions.get(context.category)
        if recovery_action:
            try:
                success = recovery_action(context)
                with self._lock:
                    if success:
                        self._metrics["recovered"] += 1
                    else:
                        self._metrics["failed"] += 1
                return success
            except Exception:
                with self._lock:
                    self._metrics["failed"] += 1
                return False
        
        with self._lock:
            self._metrics["failed"] += 1
        return False
    
    def get_recent_errors(
        self,
        limit: int = 10,
        category: Optional[ErrorCategory] = None,
    ) -> List[Dict[str, Any]]:
        """Son hataları al."""
        with self._lock:
            errors = self._error_log.copy()
        
        if category:
            errors = [e for e in errors if e.category == category]
        
        return [e.to_dict() for e in errors[-limit:]]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Metrics al."""
        with self._lock:
            total = self._metrics["total_errors"]
            recovery_rate = (
                self._metrics["recovered"] / total * 100 if total > 0 else 0
            )
            return {
                **self._metrics,
                "recovery_rate": f"{recovery_rate:.1f}%",
            }
    
    def reset_metrics(self):
        """Metrics sıfırla."""
        with self._lock:
            for key in self._metrics:
                if isinstance(self._metrics[key], int):
                    self._metrics[key] = 0
                elif isinstance(self._metrics[key], dict):
                    self._metrics[key] = {}

    def record_error(
        self,
        error: Exception,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        component: str = "",
        operation: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Hatayı kaydet ve metriklere ekle.
        
        Daha basit API - sadece kayıt, kurtarma denemez.
        """
        if category is None or severity is None:
            auto_category, auto_severity = ErrorClassifier.classify(error)
            category = category or auto_category
            severity = severity or auto_severity
        
        context = ErrorContext(
            error=error,
            category=category,
            severity=severity,
            component=component,
            operation=operation,
            metadata=metadata or {},
            stack_trace=traceback.format_exc(),
        )
        
        with self._lock:
            self._error_log.append(context)
            if len(self._error_log) > self.max_errors:
                self._error_log = self._error_log[-self.max_errors:]
            
            self._metrics["total_errors"] += 1
            self._metrics["by_category"][category.value] = \
                self._metrics["by_category"].get(category.value, 0) + 1
            self._metrics["by_severity"][severity.value] = \
                self._metrics["by_severity"].get(severity.value, 0) + 1


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    """
    Decorator: Exponential backoff ile retry.
    
    Args:
        max_retries: Maksimum deneme sayısı
        initial_delay: İlk bekleme süresi (saniye)
        max_delay: Maksimum bekleme süresi
        exponential_base: Üstel çarpan
        retryable_exceptions: Yeniden denenecek exception türleri
    
    Usage:
        @retry_with_backoff(max_retries=3, initial_delay=0.5)
        def flaky_operation():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        delay = min(
                            initial_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        logging.warning(
                            f"Retry {attempt + 1}/{max_retries} for {fn.__name__} "
                            f"after {delay:.2f}s: {e}"
                        )
                        time.sleep(delay)
            
            raise last_exception
        
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await fn(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        delay = min(
                            initial_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        logging.warning(
                            f"Retry {attempt + 1}/{max_retries} for {fn.__name__} "
                            f"after {delay:.2f}s: {e}"
                        )
                        await asyncio.sleep(delay)
            
            raise last_exception
        
        import asyncio
        if asyncio.iscoroutinefunction(fn):
            return async_wrapper
        return wrapper
    return decorator


def with_fallback(fallback_value: Any = None, fallback_fn: Callable = None):
    """
    Decorator: Hata durumunda fallback değer döndür.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if fallback_fn:
                    return fallback_fn(e, *args, **kwargs)
                return fallback_value
        return wrapper
    return decorator


def graceful_degradation(
    critical: bool = False,
    default_response: Any = None,
    log_errors: bool = True,
):
    """
    Decorator: Graceful degradation.
    
    Kritik olmayan hatalar için default yanıt döner.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if critical:
                    raise
                
                if log_errors:
                    logging.warning(
                        f"Graceful degradation for {fn.__name__}: {e}"
                    )
                
                return default_response
        return wrapper
    return decorator


# Global instance
error_recovery_manager = ErrorRecoveryManager()


# Default recovery actions
def _network_recovery(ctx: ErrorContext) -> bool:
    """Ağ hatası kurtarma."""
    # Kısa bekleme sonrası tekrar denenebilir
    time.sleep(1)
    return True  # Retry'a izin ver


def _resource_recovery(ctx: ErrorContext) -> bool:
    """Kaynak hatası kurtarma."""
    # Garbage collection tetikle
    import gc
    gc.collect()
    return True


# Varsayılan recovery action'ları kaydet
error_recovery_manager.register_recovery_action(
    ErrorCategory.NETWORK, _network_recovery
)
error_recovery_manager.register_recovery_action(
    ErrorCategory.RESOURCE, _resource_recovery
)


__all__ = [
    "ErrorSeverity",
    "ErrorCategory",
    "ErrorContext",
    "ErrorClassifier",
    "FallbackChain",
    "RetryStrategy",
    "ErrorRecoveryManager",
    "with_retry",
    "with_fallback",
    "retry_with_backoff",
    "graceful_degradation",
    "error_recovery_manager",
]
