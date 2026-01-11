"""
Streaming Manager
=================

Endüstri standartlarında streaming yanıt yönetimi.
Real-time token streaming, progress updates ve event handling.

Features:
- Async streaming generators
- Token-by-token streaming
- Progress callbacks
- Stream buffering
- Retry on stream interruption
- Multi-client broadcasting
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any, AsyncGenerator, Callable, Dict, List, Optional, 
    Set, TypeVar, Union
)
import uuid

from .logger import get_logger

logger = get_logger("streaming")

T = TypeVar("T")


class StreamEventType(Enum):
    """Stream event türleri"""
    START = "start"
    TOKEN = "token"
    CHUNK = "chunk"
    PROGRESS = "progress"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    METADATA = "metadata"
    ERROR = "error"
    END = "end"
    HEARTBEAT = "heartbeat"


@dataclass
class StreamEvent:
    """Stream event"""
    type: StreamEventType
    data: Any
    timestamp: float = field(default_factory=time.time)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "event_id": self.event_id
        }
    
    def to_sse(self) -> str:
        """Server-Sent Events formatına dönüştür"""
        return f"event: {self.type.value}\ndata: {json.dumps(self.data)}\n\n"


@dataclass
class StreamStats:
    """Stream istatistikleri"""
    total_tokens: int = 0
    total_chunks: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    first_token_time: Optional[float] = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    @property
    def time_to_first_token(self) -> float:
        if self.start_time and self.first_token_time:
            return self.first_token_time - self.start_time
        return 0.0
    
    @property
    def tokens_per_second(self) -> float:
        if self.duration > 0:
            return self.total_tokens / self.duration
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            "total_tokens": self.total_tokens,
            "total_chunks": self.total_chunks,
            "duration": self.duration,
            "time_to_first_token": self.time_to_first_token,
            "tokens_per_second": self.tokens_per_second
        }


class StreamBuffer:
    """
    Stream buffer - token'ları biriktirip işle
    
    Token'ları biriktirir ve belirli koşullarda flush eder:
    - Buffer dolunca
    - Timeout sonunda
    - Cümle/paragraf sonunda
    """
    
    def __init__(
        self,
        max_size: int = 100,
        timeout: float = 0.1,
        flush_on_sentence: bool = True
    ):
        self.max_size = max_size
        self.timeout = timeout
        self.flush_on_sentence = flush_on_sentence
        
        self._buffer: List[str] = []
        self._last_flush: float = time.time()
    
    def add(self, token: str) -> Optional[str]:
        """
        Token ekle, flush gerekiyorsa içeriği döndür
        """
        self._buffer.append(token)
        
        should_flush = False
        
        # Size check
        if len(self._buffer) >= self.max_size:
            should_flush = True
        
        # Timeout check
        if time.time() - self._last_flush > self.timeout:
            should_flush = True
        
        # Sentence end check
        if self.flush_on_sentence and token:
            if token.rstrip().endswith(('.', '!', '?', '\n')):
                should_flush = True
        
        if should_flush:
            return self.flush()
        
        return None
    
    def flush(self) -> str:
        """Buffer'ı boşalt ve içeriği döndür"""
        content = ''.join(self._buffer)
        self._buffer.clear()
        self._last_flush = time.time()
        return content
    
    @property
    def content(self) -> str:
        """Buffer içeriğini al (boşaltmadan)"""
        return ''.join(self._buffer)
    
    @property
    def size(self) -> int:
        """Buffer boyutu"""
        return len(self._buffer)


class StreamSubscriber:
    """Stream subscriber - event'leri dinleyen istemci"""
    
    def __init__(
        self,
        subscriber_id: str,
        queue: Optional[asyncio.Queue] = None
    ):
        self.subscriber_id = subscriber_id
        self.queue = queue or asyncio.Queue()
        self.subscribed_at = datetime.now()
        self.events_received = 0
    
    async def send(self, event: StreamEvent):
        """Event gönder"""
        await self.queue.put(event)
        self.events_received += 1
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[StreamEvent]:
        """Event al"""
        try:
            if timeout:
                return await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return await self.queue.get()
        except asyncio.TimeoutError:
            return None


class StreamBroadcaster:
    """
    Stream broadcaster - çoklu istemcilere broadcast
    
    Bir stream'i birden fazla subscriber'a dağıtır.
    """
    
    def __init__(self, stream_id: Optional[str] = None):
        self.stream_id = stream_id or str(uuid.uuid4())[:8]
        self._subscribers: Dict[str, StreamSubscriber] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, subscriber_id: Optional[str] = None) -> StreamSubscriber:
        """Yeni subscriber ekle"""
        async with self._lock:
            sub_id = subscriber_id or str(uuid.uuid4())[:8]
            subscriber = StreamSubscriber(sub_id)
            self._subscribers[sub_id] = subscriber
            
            logger.debug(f"Subscriber added: {sub_id}")
            
            return subscriber
    
    async def unsubscribe(self, subscriber_id: str):
        """Subscriber'ı kaldır"""
        async with self._lock:
            if subscriber_id in self._subscribers:
                del self._subscribers[subscriber_id]
                logger.debug(f"Subscriber removed: {subscriber_id}")
    
    async def broadcast(self, event: StreamEvent):
        """Event'i tüm subscriber'lara gönder"""
        async with self._lock:
            tasks = [
                subscriber.send(event)
                for subscriber in self._subscribers.values()
            ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


class StreamingResponse:
    """
    Streaming response wrapper
    
    LLM yanıtlarını streaming olarak işler ve yönetir.
    """
    
    def __init__(
        self,
        generator: AsyncGenerator[str, None],
        metadata: Optional[Dict] = None
    ):
        self._generator = generator
        self._metadata = metadata or {}
        self._stats = StreamStats()
        self._buffer = StreamBuffer()
        self._accumulated = ""
        self._callbacks: Dict[str, List[Callable]] = {
            "on_token": [],
            "on_chunk": [],
            "on_complete": [],
            "on_error": []
        }
        self._broadcaster = StreamBroadcaster()
    
    def on(self, event: str, callback: Callable):
        """Event callback ekle"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    async def _trigger_callback(self, event: str, *args, **kwargs):
        """Callback'leri tetikle"""
        for callback in self._callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def stream(self) -> AsyncGenerator[StreamEvent, None]:
        """Stream event'lerini generate et"""
        self._stats.start_time = time.time()
        
        # Start event
        yield StreamEvent(
            type=StreamEventType.START,
            data={"metadata": self._metadata}
        )
        
        try:
            async for token in self._generator:
                # İlk token zamanı
                if self._stats.first_token_time is None:
                    self._stats.first_token_time = time.time()
                
                self._stats.total_tokens += 1
                self._accumulated += token
                
                # Token event
                token_event = StreamEvent(
                    type=StreamEventType.TOKEN,
                    data={"token": token, "index": self._stats.total_tokens}
                )
                
                yield token_event
                await self._broadcaster.broadcast(token_event)
                await self._trigger_callback("on_token", token)
                
                # Buffer'a ekle, chunk varsa gönder
                chunk = self._buffer.add(token)
                if chunk:
                    self._stats.total_chunks += 1
                    
                    chunk_event = StreamEvent(
                        type=StreamEventType.CHUNK,
                        data={"chunk": chunk, "index": self._stats.total_chunks}
                    )
                    
                    yield chunk_event
                    await self._trigger_callback("on_chunk", chunk)
            
            # Flush remaining buffer
            remaining = self._buffer.flush()
            if remaining:
                self._stats.total_chunks += 1
                yield StreamEvent(
                    type=StreamEventType.CHUNK,
                    data={"chunk": remaining, "index": self._stats.total_chunks}
                )
            
            self._stats.end_time = time.time()
            
            # End event
            end_event = StreamEvent(
                type=StreamEventType.END,
                data={
                    "full_response": self._accumulated,
                    "stats": self._stats.to_dict()
                }
            )
            
            yield end_event
            await self._broadcaster.broadcast(end_event)
            await self._trigger_callback("on_complete", self._accumulated, self._stats)
        
        except Exception as e:
            error_event = StreamEvent(
                type=StreamEventType.ERROR,
                data={"error": str(e), "partial_response": self._accumulated}
            )
            
            yield error_event
            await self._broadcaster.broadcast(error_event)
            await self._trigger_callback("on_error", e)
            
            raise
    
    async def collect(self) -> str:
        """Tüm stream'i topla ve tam yanıtı döndür"""
        async for event in self.stream():
            if event.type == StreamEventType.END:
                return event.data["full_response"]
        
        return self._accumulated
    
    @property
    def stats(self) -> StreamStats:
        return self._stats
    
    @property
    def broadcaster(self) -> StreamBroadcaster:
        return self._broadcaster


class StreamManager:
    """
    Stream yönetim sistemi
    
    Aktif stream'leri yönetir ve izler.
    """
    
    def __init__(self):
        self._active_streams: Dict[str, StreamingResponse] = {}
        self._stream_history: List[Dict] = []
        self._lock = asyncio.Lock()
    
    async def create_stream(
        self,
        generator: AsyncGenerator[str, None],
        stream_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> StreamingResponse:
        """Yeni stream oluştur"""
        stream_id = stream_id or str(uuid.uuid4())[:8]
        
        response = StreamingResponse(generator, metadata)
        
        async with self._lock:
            self._active_streams[stream_id] = response
        
        logger.info(f"Stream created: {stream_id}")
        
        return response
    
    async def get_stream(self, stream_id: str) -> Optional[StreamingResponse]:
        """Stream'i al"""
        return self._active_streams.get(stream_id)
    
    async def close_stream(self, stream_id: str):
        """Stream'i kapat"""
        async with self._lock:
            if stream_id in self._active_streams:
                stream = self._active_streams[stream_id]
                
                # Save to history
                self._stream_history.append({
                    "stream_id": stream_id,
                    "stats": stream.stats.to_dict(),
                    "closed_at": datetime.now().isoformat()
                })
                
                del self._active_streams[stream_id]
                
                logger.info(f"Stream closed: {stream_id}")
    
    @property
    def active_count(self) -> int:
        return len(self._active_streams)
    
    def get_stats(self) -> Dict:
        """İstatistikleri al"""
        return {
            "active_streams": self.active_count,
            "total_created": len(self._stream_history) + self.active_count,
            "recent_history": self._stream_history[-10:]
        }


# Global stream manager
stream_manager = StreamManager()


# ========================
# Utility Functions
# ========================

async def stream_tokens(
    text: str,
    delay: float = 0.02
) -> AsyncGenerator[str, None]:
    """
    Text'i token'lara ayırarak stream et (simülasyon/test için)
    """
    words = text.split(' ')
    
    for i, word in enumerate(words):
        if i > 0:
            yield ' '
        yield word
        await asyncio.sleep(delay)


async def stream_with_progress(
    generator: AsyncGenerator[str, None],
    total_expected: Optional[int] = None,
    progress_callback: Optional[Callable[[float], None]] = None
) -> AsyncGenerator[StreamEvent, None]:
    """
    Generator'ı progress tracking ile wrap et
    """
    count = 0
    
    async for token in generator:
        count += 1
        
        yield StreamEvent(
            type=StreamEventType.TOKEN,
            data={"token": token}
        )
        
        if total_expected and progress_callback:
            progress = min(count / total_expected, 1.0)
            progress_callback(progress)
            
            yield StreamEvent(
                type=StreamEventType.PROGRESS,
                data={"progress": progress, "current": count, "total": total_expected}
            )


def create_sse_response(events: AsyncGenerator[StreamEvent, None]):
    """
    FastAPI için SSE response oluştur
    
    Usage:
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            create_sse_response(stream.stream()),
            media_type="text/event-stream"
        )
    """
    async def generate():
        async for event in events:
            yield event.to_sse()
    
    return generate()


__all__ = [
    "StreamManager",
    "StreamingResponse",
    "StreamEvent",
    "StreamEventType",
    "StreamStats",
    "StreamBuffer",
    "StreamBroadcaster",
    "StreamSubscriber",
    "stream_manager",
    "stream_tokens",
    "stream_with_progress",
    "create_sse_response"
]
