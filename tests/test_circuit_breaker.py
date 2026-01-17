"""
Enterprise AI Assistant - Circuit Breaker Tests
================================================

Circuit breaker pattern, error recovery, ve resilience testleri.
"""

import pytest
import sys
import time
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCircuitBreaker:
    """Circuit Breaker testleri."""
    
    def test_circuit_breaker_initialization(self):
        """CircuitBreaker başlatılabilmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        # Actual API uses: name (required), failure_threshold, success_threshold, timeout_seconds
        cb = CircuitBreaker(
            name="test_breaker",
            failure_threshold=5,
            success_threshold=2,
            timeout_seconds=30
        )
        
        assert cb is not None
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_closed_allows_calls(self):
        """CLOSED durumda çağrılar geçmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(name="test", failure_threshold=5)
        
        @cb
        def successful_func():
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_failures(self):
        """Ardışık hatalardan sonra devre açılmalı."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(name="test", failure_threshold=3)
        
        @cb
        def failing_func():
            raise Exception("Simulated failure")
        
        # 3 kez başarısız ol
        for _ in range(3):
            try:
                failing_func()
            except:
                pass
        
        assert cb.state == CircuitState.OPEN
    
    def test_circuit_open_rejects_calls(self):
        """OPEN durumda çağrılar reddedilmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        from core.exceptions import CircuitBreakerOpenError
        
        cb = CircuitBreaker(name="test", failure_threshold=1)
        
        @cb
        def func():
            raise Exception("Fail")
        
        # Devre aç
        try:
            func()
        except CircuitBreakerOpenError:
            pass
        except:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        # Şimdi çağrı reddedilmeli
        with pytest.raises(CircuitBreakerOpenError):
            func()
    
    def test_circuit_half_open_after_timeout(self):
        """Timeout sonrası HALF_OPEN duruma geçmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(name="test", failure_threshold=1, timeout_seconds=1)
        
        @cb
        def func():
            raise Exception("Fail")
        
        # Devre aç
        try:
            func()
        except:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        # Timeout bekle
        time.sleep(1.5)
        
        # State property check triggers HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_circuit_closes_after_success_in_half_open(self):
        """HALF_OPEN'da başarılı çağrı deveyi kapatmalı."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(
            name="test",
            failure_threshold=1, 
            timeout_seconds=1,  # Use timeout_seconds instead of recovery_timeout
            success_threshold=1  # Use success_threshold instead of half_open_max_calls
        )
        
        call_count = [0]
        
        @cb
        def func():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("First call fails")
            return "success"
        
        # İlk çağrı - başarısız, devre açılır
        try:
            func()
        except:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        # Timeout bekle
        time.sleep(1.1)
        
        # HALF_OPEN'a geç ve başarılı çağrı yap
        result = func()
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_stats_tracking(self):
        """Circuit breaker istatistikleri tutmalı."""
        from core.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker(name="test", failure_threshold=10)
        
        @cb
        def func(fail=False):
            if fail:
                raise Exception("Fail")
            return "success"
        
        # 3 başarılı
        for _ in range(3):
            func()
        
        # 2 başarısız
        for _ in range(2):
            try:
                func(fail=True)
            except:
                pass
        
        assert cb.stats.successful_calls == 3
        assert cb.stats.failed_calls == 2
        assert cb.stats.total_calls == 5


class TestCircuitBreakerDecorator:
    """Circuit Breaker decorator testleri."""
    
    def test_circuit_breaker_as_decorator(self):
        """CircuitBreaker decorator olarak çalışmalı."""
        from core.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker(name="decorator_test")
        
        @cb
        def my_func():
            return "works"
        
        result = my_func()
        assert result == "works"
    
    def test_circuit_breaker_with_custom_params(self):
        """CircuitBreaker özel parametrelerle decorator olarak çalışmalı."""
        from core.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker(name="custom_test", failure_threshold=10, timeout_seconds=60)
        
        @cb
        def my_func():
            return "works"
        
        result = my_func()
        assert result == "works"
    
    def test_circuit_breaker_on_async_function(self):
        """CircuitBreaker async fonksiyonlarda çalışmalı."""
        from core.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker(name="async_test")
        
        @cb
        async def async_func():
            return "async works"
        
        result = asyncio.run(async_func())
        assert result == "async works"
    
    def test_circuit_breaker_preserves_function_metadata(self):
        """CircuitBreaker fonksiyon metadata'sını korumalı."""
        from core.circuit_breaker import CircuitBreaker
        
        cb = CircuitBreaker(name="metadata_test")
        
        @cb
        def documented_func():
            """Bu fonksiyon dökümante edilmiş."""
            return "works"
        
        assert "dökümante" in documented_func.__doc__


class TestErrorRecovery:
    """Error Recovery testleri."""
    
    def test_error_recovery_initialization(self):
        """ErrorRecoveryManager başlatılabilmeli."""
        from core.error_recovery import ErrorRecoveryManager, ErrorSeverity
        
        manager = ErrorRecoveryManager()
        
        assert manager is not None
    
    def test_error_categorization(self):
        """Hatalar kategorilere ayrılabilmeli."""
        from core.error_recovery import ErrorCategory, ErrorClassifier
        
        # Network error - using ErrorClassifier.classify() instead of categorize_error()
        network_error = ConnectionError("Connection refused")
        category, severity = ErrorClassifier.classify(network_error)
        assert category == ErrorCategory.NETWORK
        
        # Timeout error
        timeout_error = TimeoutError("Request timed out")
        category, severity = ErrorClassifier.classify(timeout_error)
        assert category == ErrorCategory.TIMEOUT
    
    def test_retry_with_backoff(self):
        """Exponential backoff ile retry çalışmalı."""
        from core.error_recovery import retry_with_backoff
        
        attempts = [0]
        
        @retry_with_backoff(max_retries=3, initial_delay=0.1)
        def flaky_func():
            attempts[0] += 1
            if attempts[0] < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = flaky_func()
        
        assert result == "success"
        assert attempts[0] == 3
    
    def test_fallback_decorator(self):
        """Fallback decorator çalışmalı - fallback değer döner."""
        from core.error_recovery import with_fallback
        
        @with_fallback(fallback_value="fallback result")
        def failing_func():
            raise Exception("Primary failed")
        
        # Decorator returns a wrapper that returns fallback_value on error
        result = failing_func()
        
        assert result == "fallback result"
    
    def test_error_context_creation(self):
        """Error context oluşturulabilmeli."""
        from core.error_recovery import ErrorContext, ErrorCategory, ErrorSeverity
        
        context = ErrorContext(
            error=ValueError("Invalid input"),
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            component="InputValidator",
            operation="validate_user_input"
        )
        
        assert context.category == ErrorCategory.VALIDATION
        assert context.severity == ErrorSeverity.MEDIUM
        assert context.component == "InputValidator"
    
    def test_error_severity_levels(self):
        """Tüm severity seviyeleri tanımlı olmalı."""
        from core.error_recovery import ErrorSeverity
        
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_graceful_degradation_decorator(self):
        """Graceful degradation decorator çalışmalı."""
        from core.error_recovery import graceful_degradation
        
        @graceful_degradation(default_response="degraded", critical=False)
        def failing_func():
            raise Exception("Service unavailable")
        
        # Should return default_response instead of raising
        result = failing_func()
        assert result == "degraded"


class TestCircuitBreakerRegistry:
    """Circuit Breaker Registry testleri."""
    
    def test_registry_tracking(self):
        """Registry tüm circuit breaker'ları takip etmeli."""
        from core.circuit_breaker import CircuitBreaker, circuit_registry
        
        # Create circuit breakers - they auto-register
        cb1 = CircuitBreaker(name="test_service_a", failure_threshold=5)
        cb2 = CircuitBreaker(name="test_service_b", failure_threshold=5)
        
        # Use the circuit_registry singleton
        status = circuit_registry.get_all_status()
        assert status is not None
    
    def test_registry_reset(self):
        """Circuit breaker sıfırlanabilmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(name="reset_test", failure_threshold=1)
        
        @cb
        def func():
            raise Exception("Fail")
        
        try:
            func()
        except:
            pass
        
        # Reset the circuit breaker
        cb.reset()
        assert cb.state == CircuitState.CLOSED


class TestRateLimiter:
    """Rate Limiter testleri - skip if module doesn't exist."""
    
    @pytest.fixture
    def rate_limiter_available(self):
        """Check if rate_limiter module exists."""
        try:
            from core import rate_limiter
            return True
        except ImportError:
            return False
    
    def test_rate_limiter_initialization(self, rate_limiter_available):
        """RateLimiter başlatılabilmeli."""
        if not rate_limiter_available:
            pytest.skip("rate_limiter module not available")
        
        from core.rate_limiter import RateLimiter, RateLimitConfig
        
        # Actual API: RateLimiter(config: RateLimitConfig = None)
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=5
        )
        limiter = RateLimiter(config=config)
        assert limiter is not None
        assert limiter.config.requests_per_minute == 10
    
    def test_rate_limit_allows_within_limit(self, rate_limiter_available):
        """Limit dahilinde istekler geçmeli."""
        if not rate_limiter_available:
            pytest.skip("rate_limiter module not available")
        
        from core.rate_limiter import RateLimiter, RateLimitConfig
        
        # Actual API: check_limit(client_id) returns (is_allowed, reason)
        config = RateLimitConfig(requests_per_minute=60, burst_limit=10)
        limiter = RateLimiter(config=config)
        
        for i in range(5):
            is_allowed, reason = limiter.check_limit("test_user")
            assert is_allowed, f"Request {i+1} should be allowed, got: {reason}"


class TestHealthIntegration:
    """Health check entegrasyon testleri."""
    
    def test_circuit_breaker_in_health_check(self):
        """Circuit breaker durumu health check'te görünmeli."""
        try:
            from core.health import HealthChecker
            
            checker = HealthChecker()
            
            if hasattr(checker, 'check_circuit_breakers'):
                status = asyncio.run(checker.check_circuit_breakers())
                assert status is not None
        except ImportError:
            pytest.skip("HealthChecker not available")
    
    def test_error_rate_monitoring(self):
        """Error rate izlenebilmeli."""
        from core.error_recovery import ErrorRecoveryManager
        
        manager = ErrorRecoveryManager()
        
        # Hataları kaydet - use record_error method
        for _ in range(5):
            manager.record_error(Exception("Test error"))
        
        # Check metrics
        metrics = manager.get_metrics()
        assert metrics["total_errors"] >= 5


class TestResiliencePatterns:
    """Resilience pattern testleri."""
    
    def test_bulkhead_pattern(self):
        """Bulkhead pattern - izole kaynak havuzları."""
        # Farklı servisler için farklı circuit breaker
        from core.circuit_breaker import CircuitBreaker
        
        llm_breaker = CircuitBreaker(name="llm_service_bulkhead", failure_threshold=5)
        db_breaker = CircuitBreaker(name="db_service_bulkhead", failure_threshold=3)
        
        # Birinin açılması diğerini etkilememeli
        @llm_breaker
        def call_llm():
            raise Exception("LLM down")
        
        @db_breaker
        def call_db():
            return "DB works"
        
        # LLM'i düşür
        for _ in range(5):
            try:
                call_llm()
            except:
                pass
        
        # DB hala çalışmalı
        result = call_db()
        assert result == "DB works"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
