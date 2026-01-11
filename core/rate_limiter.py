"""
Enterprise AI Assistant - Rate Limiter Module
API isteklerini sınırlandırma

DDoS koruması ve adil kullanım.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from functools import wraps


@dataclass
class RateLimitConfig:
    """Rate limit konfigürasyonu."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10  # Anlık burst
    cooldown_seconds: int = 60  # Aşım sonrası bekleme


@dataclass
class ClientState:
    """İstemci durumu."""
    minute_requests: list = field(default_factory=list)
    hour_requests: list = field(default_factory=list)
    day_requests: list = field(default_factory=list)
    is_blocked: bool = False
    blocked_until: Optional[datetime] = None
    total_requests: int = 0
    total_blocked: int = 0


class RateLimiter:
    """Rate limiting yöneticisi."""
    
    def __init__(self, config: RateLimitConfig = None):
        """
        Rate limiter başlat.
        
        Args:
            config: Rate limit ayarları
        """
        self.config = config or RateLimitConfig()
        self._clients: Dict[str, ClientState] = defaultdict(ClientState)
        self._lock = threading.Lock()
        self._global_requests: list = []
    
    def _clean_old_requests(self, state: ClientState, now: datetime):
        """Eski istekleri temizle."""
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        state.minute_requests = [
            t for t in state.minute_requests if t > minute_ago
        ]
        state.hour_requests = [
            t for t in state.hour_requests if t > hour_ago
        ]
        state.day_requests = [
            t for t in state.day_requests if t > day_ago
        ]
    
    def check_limit(self, client_id: str) -> tuple[bool, Optional[str]]:
        """
        Rate limit kontrolü yap.
        
        Args:
            client_id: İstemci tanımlayıcısı (IP, user_id, vb.)
            
        Returns:
            (izin_var_mı, hata_mesajı)
        """
        with self._lock:
            now = datetime.now()
            state = self._clients[client_id]
            
            # Check if blocked
            if state.is_blocked:
                if state.blocked_until and now < state.blocked_until:
                    remaining = (state.blocked_until - now).seconds
                    return False, f"Rate limit aşıldı. {remaining} saniye bekleyin."
                else:
                    state.is_blocked = False
                    state.blocked_until = None
            
            # Clean old requests
            self._clean_old_requests(state, now)
            
            # Check limits
            if len(state.minute_requests) >= self.config.requests_per_minute:
                state.is_blocked = True
                state.blocked_until = now + timedelta(seconds=self.config.cooldown_seconds)
                state.total_blocked += 1
                return False, "Dakikalık limit aşıldı."
            
            if len(state.hour_requests) >= self.config.requests_per_hour:
                state.is_blocked = True
                state.blocked_until = now + timedelta(seconds=self.config.cooldown_seconds * 5)
                state.total_blocked += 1
                return False, "Saatlik limit aşıldı."
            
            if len(state.day_requests) >= self.config.requests_per_day:
                state.is_blocked = True
                state.blocked_until = now + timedelta(hours=1)
                state.total_blocked += 1
                return False, "Günlük limit aşıldı."
            
            # Check burst
            recent = [t for t in state.minute_requests if t > now - timedelta(seconds=5)]
            if len(recent) >= self.config.burst_limit:
                return False, "Çok hızlı istek gönderiyorsunuz. Lütfen yavaşlayın."
            
            return True, None
    
    def record_request(self, client_id: str):
        """
        İsteği kaydet.
        
        Args:
            client_id: İstemci tanımlayıcısı
        """
        with self._lock:
            now = datetime.now()
            state = self._clients[client_id]
            
            state.minute_requests.append(now)
            state.hour_requests.append(now)
            state.day_requests.append(now)
            state.total_requests += 1
            
            self._global_requests.append(now)
    
    def get_client_stats(self, client_id: str) -> Dict:
        """
        İstemci istatistiklerini al.
        
        Args:
            client_id: İstemci tanımlayıcısı
            
        Returns:
            İstatistikler
        """
        with self._lock:
            now = datetime.now()
            state = self._clients[client_id]
            self._clean_old_requests(state, now)
            
            return {
                "client_id": client_id,
                "minute_requests": len(state.minute_requests),
                "hour_requests": len(state.hour_requests),
                "day_requests": len(state.day_requests),
                "total_requests": state.total_requests,
                "total_blocked": state.total_blocked,
                "is_blocked": state.is_blocked,
                "blocked_until": state.blocked_until.isoformat() if state.blocked_until else None,
                "limits": {
                    "per_minute": self.config.requests_per_minute,
                    "per_hour": self.config.requests_per_hour,
                    "per_day": self.config.requests_per_day,
                },
            }
    
    def get_global_stats(self) -> Dict:
        """
        Global istatistikleri al.
        
        Returns:
            Global istatistikler
        """
        with self._lock:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            hour_ago = now - timedelta(hours=1)
            
            # Clean old global requests
            self._global_requests = [
                t for t in self._global_requests if t > hour_ago
            ]
            
            recent_minute = [t for t in self._global_requests if t > minute_ago]
            
            return {
                "total_clients": len(self._clients),
                "requests_last_minute": len(recent_minute),
                "requests_last_hour": len(self._global_requests),
                "blocked_clients": sum(
                    1 for s in self._clients.values() if s.is_blocked
                ),
            }
    
    def reset_client(self, client_id: str):
        """
        İstemci durumunu sıfırla.
        
        Args:
            client_id: İstemci tanımlayıcısı
        """
        with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
    
    def whitelist_client(self, client_id: str):
        """İstemciyi beyaz listeye al (limit yok)."""
        # Implementation would store whitelisted clients
        pass


def rate_limit(limiter: RateLimiter, get_client_id: Callable = None):
    """
    Rate limit decorator for async functions.
    
    Args:
        limiter: RateLimiter instance
        get_client_id: Function to extract client ID from request
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get client_id from various sources
            client_id = "default"
            
            if get_client_id:
                client_id = get_client_id(*args, **kwargs)
            elif "request" in kwargs:
                request = kwargs["request"]
                client_id = getattr(request.client, "host", "default")
            
            # Check rate limit
            allowed, error_msg = limiter.check_limit(client_id)
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(status_code=429, detail=error_msg)
            
            # Record request
            limiter.record_request(client_id)
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_sync(limiter: RateLimiter, get_client_id: Callable = None):
    """
    Rate limit decorator for sync functions.
    
    Args:
        limiter: RateLimiter instance
        get_client_id: Function to extract client ID
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = "default"
            
            if get_client_id:
                client_id = get_client_id(*args, **kwargs)
            
            allowed, error_msg = limiter.check_limit(client_id)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded: {error_msg}")
            
            limiter.record_request(client_id)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Farklı limitler için hazır konfigürasyonlar
STRICT_LIMIT = RateLimitConfig(
    requests_per_minute=20,
    requests_per_hour=200,
    requests_per_day=1000,
    burst_limit=5,
)

STANDARD_LIMIT = RateLimitConfig(
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=10000,
    burst_limit=10,
)

RELAXED_LIMIT = RateLimitConfig(
    requests_per_minute=120,
    requests_per_hour=3000,
    requests_per_day=50000,
    burst_limit=20,
)

# Default limiter
rate_limiter = RateLimiter(STANDARD_LIMIT)
