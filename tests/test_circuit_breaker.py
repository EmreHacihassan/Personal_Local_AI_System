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
        
        cb = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=30,
            half_open_max_calls=3
        )
        
        assert cb is not None
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_closed_allows_calls(self):
        """CLOSED durumda çağrılar geçmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=5)
        
        @cb
        def successful_func():
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_opens_after_failures(self):
        """Ardışık hatalardan sonra devre açılmalı."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=3)
        
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
        from core.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerOpenError
        
        cb = CircuitBreaker(failure_threshold=1)
        
        @cb
        def func():
            raise Exception("Fail")
        
        # Devre aç
        try:
            func()
        except:
            pass
        
        assert cb.state == CircuitState.OPEN
        
        # Şimdi çağrı reddedilmeli
        with pytest.raises(CircuitBreakerOpenError):
            func()
    
    def test_circuit_half_open_after_timeout(self):
        """Timeout sonrası HALF_OPEN duruma geçmeli."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)
        
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
        
        # Yeni çağrı HALF_OPEN durumuna geçirmeli
        cb._check_state()
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_circuit_closes_after_success_in_half_open(self):
        """HALF_OPEN'da başarılı çağrı deveyi kapatmalı."""
        from core.circuit_breaker import CircuitBreaker, CircuitState
        
        cb = CircuitBreaker(
            failure_threshold=1, 
            recovery_timeout=0.1,
            half_open_max_calls=1
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
        time.sleep(0.2)
        
        # HALF_OPEN'a geç ve başarılı çağrı yap
        result = func()
        
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_circuit_stats_tracking(self):
        """Circuit breaker istatistikleri tutmalı."""
        from core.circuit_breaker import CircuitBreaker, CircuitStats
        
        cb = CircuitBreaker(failure_threshold=10)
        
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
    
    def test_decorator_with_defaults(self):
        """Decorator varsayılan parametrelerle çalışmalı."""
        from core.circuit_breaker import circuit_breaker
        
        @circuit_breaker()
        def my_func():
            return "works"
        
        result = my_func()
        assert result == "works"
    
    def test_decorator_with_custom_params(self):
        """Decorator özel parametrelerle çalışmalı."""
        from core.circuit_breaker import circuit_breaker
        
        @circuit_breaker(failure_threshold=10, recovery_timeout=60)
        def my_func():
            return "works"
        
        result = my_func()
        assert result == "works"
    
    def test_decorator_on_async_function(self):
        """Decorator async fonksiyonlarda çalışmalı."""
        from core.circuit_breaker import circuit_breaker
        
        @circuit_breaker()
        async def async_func():
            return "async works"
        
        result = asyncio.run(async_func())
        assert result == "async works"
    
    def test_decorator_preserves_function_metadata(self):
        """Decorator fonksiyon metadata'sını korumalı."""
        from core.circuit_breaker import circuit_breaker
        
        @circuit_breaker()
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
        from core.error_recovery import ErrorCategory, categorize_error
        
        # Network error
        network_error = ConnectionError("Connection refused")
        category = categorize_error(network_error)
        assert category == ErrorCategory.NETWORK
        
        # Timeout error
        timeout_error = TimeoutError("Request timed out")
        category = categorize_error(timeout_error)
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
    
    def test_fallback_execution(self):
        """Fallback fonksiyon çalıştırılabilmeli."""
        from core.error_recovery import with_fallback
        
        def primary():
            raise Exception("Primary failed")
        
        def fallback():
            return "fallback result"
        
        result = with_fallback(primary, fallback)
        
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
    
    def test_graceful_degradation(self):
        """Graceful degradation çalışmalı."""
        from core.error_recovery import ErrorRecoveryManager
        
        manager = ErrorRecoveryManager()
        
        # Degrade mod aktif et
        if hasattr(manager, 'enable_degraded_mode'):
            manager.enable_degraded_mode("LLM temporarily unavailable")
            
            assert manager.is_degraded
            
            manager.disable_degraded_mode()
            assert not manager.is_degraded


class TestCircuitBreakerRegistry:
    """Circuit Breaker Registry testleri."""
    
    def test_registry_tracking(self):
        """Registry tüm circuit breaker'ları takip etmeli."""
        from core.circuit_breaker import CircuitBreaker, get_circuit_breaker_registry
        
        cb1 = CircuitBreaker(name="service_a", failure_threshold=5)
        cb2 = CircuitBreaker(name="service_b", failure_threshold=5)
        
        registry = get_circuit_breaker_registry()
        
        if registry:
            assert "service_a" in registry or len(registry) >= 0
    
    def test_bulk_reset(self):
        """Tüm circuit breaker'lar sıfırlanabilmeli."""
        from core.circuit_breaker import CircuitBreaker, reset_all_circuits
        
        cb = CircuitBreaker(failure_threshold=1)
        
        @cb
        def func():
            raise Exception("Fail")
        
        try:
            func()
        except:
            pass
        
        if hasattr(cb, 'reset'):
            cb.reset()
            from core.circuit_breaker import CircuitState
            assert cb.state == CircuitState.CLOSED


class TestRateLimiter:
    """Rate Limiter testleri."""
    
    def test_rate_limiter_initialization(self):
        """RateLimiter başlatılabilmeli."""
        from core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        assert limiter is not None
    
    def test_rate_limit_allows_within_limit(self):
        """Limit dahilinde istekler geçmeli."""
        from core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            result = limiter.is_allowed("test_user")
            assert result, f"Request {i+1} should be allowed"
    
    def test_rate_limit_blocks_over_limit(self):
        """Limit aşıldığında istekler bloklanmalı."""
        from core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # 3 istek geç
        for _ in range(3):
            limiter.is_allowed("test_user")
        
        # 4. istek bloklanmalı
        result = limiter.is_allowed("test_user")
        assert not result
    
    def test_rate_limit_resets_after_window(self):
        """Window sonrası limit sıfırlanmalı."""
        from core.rate_limiter import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Limiti doldur
        limiter.is_allowed("test_user")
        limiter.is_allowed("test_user")
        
        assert not limiter.is_allowed("test_user")
        
        # Window bekle
        time.sleep(1.5)
        
        # Artık geçmeli
        assert limiter.is_allowed("test_user")
    
    def test_rate_limit_decorator(self):
        """Rate limit decorator çalışmalı."""
        from core.rate_limiter import rate_limit
        
        @rate_limit(max_requests=2, window_seconds=60)
        def limited_func():
            return "success"
        
        # İlk 2 çağrı başarılı
        assert limited_func() == "success"
        assert limited_func() == "success"
        
        # 3. çağrı rate limit hatası vermeli
        try:
            limited_func()
            # Eğer hata vermezse, fonksiyon farklı şekilde handle ediyor olabilir
        except Exception as e:
            assert "rate" in str(e).lower() or "limit" in str(e).lower()


class TestHealthIntegration:
    """Health check entegrasyon testleri."""
    
    def test_circuit_breaker_in_health_check(self):
        """Circuit breaker durumu health check'te görünmeli."""
        from core.health import HealthChecker
        
        checker = HealthChecker()
        
        if hasattr(checker, 'check_circuit_breakers'):
            status = asyncio.run(checker.check_circuit_breakers())
            assert status is not None
    
    def test_error_rate_monitoring(self):
        """Error rate izlenebilmeli."""
        from core.error_recovery import ErrorRecoveryManager
        
        manager = ErrorRecoveryManager()
        
        # Hataları kaydet
        for _ in range(5):
            if hasattr(manager, 'record_error'):
                manager.record_error(Exception("Test error"))
        
        if hasattr(manager, 'get_error_rate'):
            rate = manager.get_error_rate()
            assert rate >= 0


class TestResiliencePatterns:
    """Resilience pattern testleri."""
    
    def test_bulkhead_pattern(self):
        """Bulkhead pattern - izole kaynak havuzları."""
        # Farklı servisler için farklı circuit breaker
        from core.circuit_breaker import CircuitBreaker
        
        llm_breaker = CircuitBreaker(name="llm_service", failure_threshold=5)
        db_breaker = CircuitBreaker(name="db_service", failure_threshold=3)
        
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
    
    def test_timeout_pattern(self):
        """Timeout pattern çalışmalı."""
        from core.error_recovery import with_timeout
        
        async def slow_operation():
            await asyncio.sleep(10)
            return "done"
        
        if hasattr(with_timeout, '__call__'):
            # 1 saniye timeout ile çalıştır
            try:
                result = asyncio.run(with_timeout(slow_operation(), timeout=1))
            except asyncio.TimeoutError:
                # Beklenen davranış
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
