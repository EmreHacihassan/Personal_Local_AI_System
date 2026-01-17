"""
🚀 Stream Buffer - Token State Management
==========================================

WebSocket'ten bağımsız token state yönetimi.

Prensipler:
- WebSocket hiçbir zaman state taşımaz. WebSocket sadece iletir.
- Token'lar dışarıda saklanır, WebSocket canlı olsun ya da olmasın token üretimi devam eder
- Client reconnect edince kaldığı yerden devam eder

Bu modül token'ları saklar ve resume desteği sağlar.
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from threading import Lock
from collections import OrderedDict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class StreamToken:
    """Tek bir stream token'ı."""
    index: int
    content: str
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "content": self.content,
            "ts": int(self.timestamp * 1000)
        }


@dataclass 
class StreamState:
    """Bir stream session'ın durumu."""
    stream_id: str
    session_id: str
    message: str
    tokens: List[StreamToken] = field(default_factory=list)
    sources: List[dict] = field(default_factory=list)
    status: str = "pending"  # pending, generating, completed, stopped, error
    error: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    stop_requested: bool = False
    
    @property
    def token_count(self) -> int:
        return len(self.tokens)
    
    @property
    def full_response(self) -> str:
        return "".join(t.content for t in self.tokens)
    
    @property
    def is_active(self) -> bool:
        return self.status in ("pending", "generating")
    
    @property
    def duration_ms(self) -> int:
        end = self.ended_at or time.time()
        return int((end - self.started_at) * 1000)
    
    def add_token(self, content: str) -> StreamToken:
        """Yeni token ekle."""
        token = StreamToken(
            index=len(self.tokens),
            content=content
        )
        self.tokens.append(token)
        return token
    
    def get_tokens_from(self, from_index: int) -> List[StreamToken]:
        """Belirli bir index'ten sonraki token'ları al."""
        if from_index < 0 or from_index >= len(self.tokens):
            return []
        return self.tokens[from_index:]
    
    def to_dict(self) -> dict:
        return {
            "stream_id": self.stream_id,
            "session_id": self.session_id,
            "status": self.status,
            "token_count": self.token_count,
            "duration_ms": self.duration_ms,
            "has_sources": len(self.sources) > 0,
        }


class StreamBuffer:
    """
    In-memory stream buffer.
    
    Token'ları saklar ve reconnect sonrası resume sağlar.
    Eski stream'ler otomatik temizlenir.
    
    Thread-safe: Lock kullanır.
    """
    
    MAX_STREAMS = 1000  # Maksimum aktif stream
    STREAM_TTL = 3600   # 1 saat (saniye)
    CLEANUP_INTERVAL = 300  # 5 dakikada bir temizlik
    
    def __init__(self):
        self._streams: OrderedDict[str, StreamState] = OrderedDict()
        self._session_streams: Dict[str, str] = {}  # session_id -> active stream_id
        self._lock = Lock()
        self._last_cleanup = time.time()
    
    def create_stream(self, session_id: str, message: str) -> StreamState:
        """Yeni stream oluştur."""
        with self._lock:
            # Cleanup kontrolü
            self._maybe_cleanup()
            
            # Eski aktif stream'i durdur
            if session_id in self._session_streams:
                old_stream_id = self._session_streams[session_id]
                if old_stream_id in self._streams:
                    old_stream = self._streams[old_stream_id]
                    if old_stream.is_active:
                        old_stream.status = "stopped"
                        old_stream.ended_at = time.time()
            
            # Yeni stream oluştur
            stream_id = str(uuid.uuid4())
            stream = StreamState(
                stream_id=stream_id,
                session_id=session_id,
                message=message,
                status="pending"
            )
            
            self._streams[stream_id] = stream
            self._session_streams[session_id] = stream_id
            
            logger.debug(f"Stream created: {stream_id} for session {session_id}")
            return stream
    
    def get_stream(self, stream_id: str) -> Optional[StreamState]:
        """Stream'i al."""
        with self._lock:
            return self._streams.get(stream_id)
    
    def get_active_stream(self, session_id: str) -> Optional[StreamState]:
        """Session'ın aktif stream'ini al."""
        with self._lock:
            stream_id = self._session_streams.get(session_id)
            if stream_id:
                return self._streams.get(stream_id)
            return None
    
    def add_token(self, stream_id: str, content: str) -> Optional[StreamToken]:
        """Stream'e token ekle."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream and stream.is_active:
                stream.status = "generating"
                return stream.add_token(content)
            return None
    
    def set_sources(self, stream_id: str, sources: List[dict]) -> None:
        """Stream'e kaynakları ekle."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                stream.sources = sources
    
    def complete_stream(self, stream_id: str) -> None:
        """Stream'i tamamla."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                stream.status = "completed"
                stream.ended_at = time.time()
                logger.debug(f"Stream completed: {stream_id}, tokens: {stream.token_count}")
    
    def stop_stream(self, stream_id: str) -> None:
        """Stream'i durdur."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                stream.stop_requested = True
                if stream.is_active:
                    stream.status = "stopped"
                    stream.ended_at = time.time()
                logger.debug(f"Stream stopped: {stream_id}, tokens: {stream.token_count}")
    
    def error_stream(self, stream_id: str, error: str) -> None:
        """Stream'i hata ile sonlandır."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                stream.status = "error"
                stream.error = error
                stream.ended_at = time.time()
    
    def request_stop(self, session_id: str) -> bool:
        """Session'ın aktif stream'ini durdurmak için istek gönder."""
        with self._lock:
            stream_id = self._session_streams.get(session_id)
            if stream_id:
                stream = self._streams.get(stream_id)
                if stream and stream.is_active:
                    stream.stop_requested = True
                    return True
            return False
    
    def is_stop_requested(self, stream_id: str) -> bool:
        """Stop isteği var mı?"""
        with self._lock:
            stream = self._streams.get(stream_id)
            return stream.stop_requested if stream else False
    
    def get_tokens_from(self, stream_id: str, from_index: int) -> List[StreamToken]:
        """Belirli index'ten sonraki token'ları al (resume için)."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if stream:
                return stream.get_tokens_from(from_index)
            return []
    
    def get_resume_data(self, stream_id: str, from_index: int = 0) -> dict:
        """Resume için gerekli tüm veriyi al."""
        with self._lock:
            stream = self._streams.get(stream_id)
            if not stream:
                return {"error": "stream_not_found"}
            
            tokens = stream.get_tokens_from(from_index)
            return {
                "stream_id": stream.stream_id,
                "status": stream.status,
                "token_count": stream.token_count,
                "from_index": from_index,
                "tokens": [t.to_dict() for t in tokens],
                "sources": stream.sources if from_index == 0 else [],
                "is_complete": not stream.is_active,
            }
    
    def get_stats(self) -> dict:
        """Buffer istatistikleri."""
        with self._lock:
            active = sum(1 for s in self._streams.values() if s.is_active)
            return {
                "total_streams": len(self._streams),
                "active_streams": active,
                "sessions": len(self._session_streams),
            }
    
    def _maybe_cleanup(self) -> None:
        """Eski stream'leri temizle."""
        now = time.time()
        if now - self._last_cleanup < self.CLEANUP_INTERVAL:
            return
        
        self._last_cleanup = now
        cutoff = now - self.STREAM_TTL
        
        # Eski stream'leri bul
        to_delete = []
        for stream_id, stream in self._streams.items():
            if stream.started_at < cutoff and not stream.is_active:
                to_delete.append(stream_id)
        
        # Sil
        for stream_id in to_delete:
            stream = self._streams.pop(stream_id, None)
            if stream:
                # Session mapping'den de sil
                if self._session_streams.get(stream.session_id) == stream_id:
                    del self._session_streams[stream.session_id]
        
        # Maksimum stream kontrolü
        while len(self._streams) > self.MAX_STREAMS:
            # En eski stream'i sil
            oldest_id, oldest = next(iter(self._streams.items()))
            if not oldest.is_active:
                self._streams.pop(oldest_id)
                if self._session_streams.get(oldest.session_id) == oldest_id:
                    del self._session_streams[oldest.session_id]
            else:
                break
        
        if to_delete:
            logger.debug(f"Cleaned up {len(to_delete)} old streams")


# Global singleton
stream_buffer = StreamBuffer()

__all__ = ['stream_buffer', 'StreamBuffer', 'StreamState', 'StreamToken']
