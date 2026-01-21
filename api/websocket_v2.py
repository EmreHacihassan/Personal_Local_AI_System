"""
🚀 Enterprise WebSocket v2 - Real-time Streaming
=================================================

MyChatbot'tan ilham alan ama onu aşan enterprise-grade WebSocket.

Özellikler:
- ANLIK streaming (buffering yok)
- Keepalive ping/pong (25 saniye)
- Rate limiting (10 istek/5 saniye)
- Graceful shutdown
- Stop komutu desteği
- Detaylı istatistikler
- Bağlantı durumu takibi
- Otomatik reconnection desteği

Protocol:
    Client -> Server:
        {"type": "chat", "message": "...", "session_id": "..."}
        {"type": "stop"}  - Streaming'i durdur
        {"type": "resume", "stream_id": "...", "from_index": N}  - Kaldığı yerden devam et
        {"type": "ping"}  - Manuel ping
    
    Server -> Client:
        {"type": "connected", "client_id": "...", "ts": ...}
        {"type": "start", "ts": ..., "stream_id": "..."}  - Yanıt başladı (stream_id ile)
        {"type": "token", "content": "...", "index": N}  - Her token anında (index ile)
        {"type": "status", "message": "...", "phase": "..."}  - Durum güncellemesi
        {"type": "sources", "sources": [...]}  - Kaynaklar
        {"type": "end", "stats": {...}}  - Tamamlandı
        {"type": "error", "message": "..."}  - Hata
        {"type": "stopped", "elapsed_ms": ...}  - Durduruldu
        {"type": "pong", "ts": ...}  - Ping yanıtı
        {"type": "resume_data", ...}  - Resume verisi

Mimari Prensip:
    WebSocket hiçbir zaman state taşımaz. WebSocket sadece iletir.
    Token'lar StreamBuffer'da saklanır.
    Client reconnect edince kaldığı yerden devam eder.
"""

import json
import asyncio
import time
import logging
import uuid
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

# Python 3.10 ve altı için async_timeout uyumluluğu
if sys.version_info < (3, 11):
    try:
        from async_timeout import timeout as asyncio_timeout
    except ImportError:
        # async_timeout yoksa, basit bir wrapper kullan
        @asynccontextmanager
        async def asyncio_timeout(seconds):
            """Basit timeout wrapper - Python 3.10 uyumlu."""
            yield
else:
    asyncio_timeout = asyncio.timeout

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from core.config import settings
from core.llm_manager import llm_manager
from core.vector_store import vector_store
from core.session_manager import session_manager
from core.stream_buffer import stream_buffer
from agents.orchestrator import orchestrator
from core.model_router import (
    get_model_router,
    ModelSize,
    FeedbackType,
    FeedbackStatus,
    MODEL_CONFIG,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

PING_INTERVAL: int = 25          # Keepalive ping aralığı (saniye)
STREAM_TIMEOUT: int = 800        # Maksimum yanıt süresi (saniye)
RATE_LIMIT_WINDOW: int = 5       # Rate limit penceresi (saniye)
RATE_LIMIT_MAX: int = 10         # Pencere içinde maksimum istek
MAX_MESSAGE_SIZE: int = 100000   # 100KB maksimum mesaj boyutu
MAX_CONNECTIONS: int = 100       # Maksimum eşzamanlı bağlantı


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ClientConnection:
    """WebSocket client bağlantı bilgisi."""
    client_id: str
    websocket: WebSocket
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    request_times: List[float] = field(default_factory=list)
    total_requests: int = 0
    total_tokens: int = 0
    is_streaming: bool = False
    stop_flag: bool = False
    session_id: Optional[str] = None
    current_stream_id: Optional[str] = None  # Aktif stream ID
    
    @property
    def connection_duration(self) -> float:
        return time.time() - self.connected_at


@dataclass
class StreamStats:
    """Streaming istatistikleri."""
    start_time: float
    end_time: Optional[float] = None
    token_count: int = 0
    char_count: int = 0
    error: Optional[str] = None
    was_stopped: bool = False
    
    @property
    def duration_ms(self) -> int:
        end = self.end_time or time.time()
        return int((end - self.start_time) * 1000)
    
    @property
    def tokens_per_second(self) -> float:
        duration = (self.end_time or time.time()) - self.start_time
        return round(self.token_count / duration, 1) if duration > 0 else 0
    
    def to_dict(self) -> dict:
        return {
            "duration_ms": self.duration_ms,
            "tokens": self.token_count,
            "chars": self.char_count,
            "tokens_per_second": self.tokens_per_second,
            "was_stopped": self.was_stopped,
        }


# =============================================================================
# CONNECTION MANAGER v2
# =============================================================================

class WebSocketManagerV2:
    """
    Enterprise WebSocket Connection Manager.
    
    MyChatbot'tan daha gelişmiş:
    - Connection pooling
    - Detaylı metriks
    - Broadcast desteği
    - Room/group desteği
    """
    
    def __init__(self):
        self._connections: Dict[str, ClientConnection] = {}
        self._rooms: Dict[str, Set[str]] = {}  # room_id -> client_ids
        self._lock = asyncio.Lock()
        self._stats = {
            "total_connections": 0,
            "total_messages": 0,
            "total_errors": 0,
        }
    
    @property
    def active_count(self) -> int:
        return len(self._connections)
    
    async def connect(self, websocket: WebSocket, client_id: str) -> ClientConnection:
        """Yeni bağlantı kabul et."""
        async with self._lock:
            # Maksimum bağlantı kontrolü
            if len(self._connections) >= MAX_CONNECTIONS:
                await websocket.close(code=1013, reason="Server overloaded")
                raise ConnectionError("Maximum connections reached")
            
            # Mevcut bağlantı varsa kapat
            if client_id in self._connections:
                old_conn = self._connections[client_id]
                try:
                    await old_conn.websocket.close(code=1000, reason="New connection")
                except:
                    pass
            
            # Bağlantıyı kabul et
            await websocket.accept()
            
            # Client connection oluştur
            conn = ClientConnection(
                client_id=client_id,
                websocket=websocket
            )
            self._connections[client_id] = conn
            self._stats["total_connections"] += 1
            
            logger.info(f"WebSocket connected: {client_id}, total: {self.active_count}")
            return conn
    
    async def disconnect(self, client_id: str) -> Optional[ClientConnection]:
        """Bağlantıyı kapat ve temizle."""
        async with self._lock:
            if client_id in self._connections:
                conn = self._connections.pop(client_id)
                
                # Room'lardan çıkar
                for room_clients in self._rooms.values():
                    room_clients.discard(client_id)
                
                logger.info(
                    f"WebSocket disconnected: {client_id}, "
                    f"duration: {conn.connection_duration:.1f}s, "
                    f"requests: {conn.total_requests}"
                )
                return conn
            return None
    
    def get_connection(self, client_id: str) -> Optional[ClientConnection]:
        """Client bağlantısını al."""
        return self._connections.get(client_id)
    
    async def send(self, client_id: str, data: dict) -> bool:
        """Belirli bir client'a mesaj gönder."""
        conn = self._connections.get(client_id)
        if not conn or conn.websocket.client_state != WebSocketState.CONNECTED:
            return False
        
        try:
            await conn.websocket.send_json(data)
            conn.last_activity = time.time()
            self._stats["total_messages"] += 1
            return True
        except Exception as e:
            logger.debug(f"Send error to {client_id}: {e}")
            self._stats["total_errors"] += 1
            return False
    
    async def broadcast(self, data: dict, exclude: Optional[Set[str]] = None) -> int:
        """Tüm bağlı client'lara mesaj gönder."""
        exclude = exclude or set()
        sent = 0
        for client_id in list(self._connections.keys()):
            if client_id not in exclude:
                if await self.send(client_id, data):
                    sent += 1
        return sent
    
    async def send_to_room(self, room_id: str, data: dict) -> int:
        """Room'daki tüm client'lara mesaj gönder."""
        if room_id not in self._rooms:
            return 0
        sent = 0
        for client_id in self._rooms[room_id]:
            if await self.send(client_id, data):
                sent += 1
        return sent
    
    def join_room(self, client_id: str, room_id: str) -> None:
        """Client'ı room'a ekle."""
        if room_id not in self._rooms:
            self._rooms[room_id] = set()
        self._rooms[room_id].add(client_id)
    
    def leave_room(self, client_id: str, room_id: str) -> None:
        """Client'ı room'dan çıkar."""
        if room_id in self._rooms:
            self._rooms[room_id].discard(client_id)
    
    def check_rate_limit(self, client_id: str) -> bool:
        """Rate limiting kontrolü."""
        conn = self._connections.get(client_id)
        if not conn:
            return False
        
        now = time.time()
        # Eski istekleri temizle
        conn.request_times = [t for t in conn.request_times if now - t < RATE_LIMIT_WINDOW]
        
        if len(conn.request_times) >= RATE_LIMIT_MAX:
            return False
        
        conn.request_times.append(now)
        return True
    
    def get_stats(self) -> dict:
        """Manager istatistiklerini al."""
        return {
            "active_connections": self.active_count,
            "total_connections": self._stats["total_connections"],
            "total_messages": self._stats["total_messages"],
            "total_errors": self._stats["total_errors"],
            "rooms": len(self._rooms),
        }
    
    def get_clients_info(self) -> List[dict]:
        """Tüm client'ların bilgisini al."""
        return [
            {
                "client_id": conn.client_id,
                "connected_at": datetime.fromtimestamp(conn.connected_at).isoformat(),
                "duration_seconds": int(conn.connection_duration),
                "total_requests": conn.total_requests,
                "is_streaming": conn.is_streaming,
                "session_id": conn.session_id,
            }
            for conn in self._connections.values()
        ]


# Global manager instance
ws_manager = WebSocketManagerV2()


# =============================================================================
# WEBSOCKET HANDLER v2
# =============================================================================

class WebSocketHandlerV2:
    """
    WebSocket mesaj işleyici.
    
    Her bağlantı için ayrı bir handler instance'ı.
    """
    
    def __init__(self, conn: ClientConnection, manager: WebSocketManagerV2):
        self.conn = conn
        self.manager = manager
        self._ping_task: Optional[asyncio.Task] = None
        self._stream_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Handler'ı başlat."""
        # Hoş geldin mesajı
        await self._send({
            "type": "connected",
            "client_id": self.conn.client_id,
            "ts": int(time.time() * 1000),
            "server_time": datetime.now().isoformat(),
        })
        
        # Keepalive başlat
        self._ping_task = asyncio.create_task(self._keepalive_loop())
    
    async def stop(self) -> None:
        """Handler'ı durdur."""
        self.conn.stop_flag = True
        
        # Task'ları iptal et
        for task in [self._stream_task, self._ping_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def handle_message(self, data: dict) -> None:
        """Gelen mesajı işle."""
        msg_type = data.get("type", "chat")
        
        if msg_type == "ping":
            await self._send({
                "type": "pong",
                "ts": int(time.time() * 1000)
            })
        
        elif msg_type == "pong":
            # Client'tan gelen pong - keepalive onayı, sessizce yoksay
            self.conn.last_activity = time.time()
        
        elif msg_type == "stop":
            await self._handle_stop()
        
        elif msg_type == "resume":
            await self._handle_resume(data)
        
        elif msg_type == "chat":
            await self._handle_chat(data)
        
        elif msg_type == "message":
            # Routing destekli mesaj (frontend'den gelen format)
            await self._handle_routed_message(data)
        
        elif msg_type == "agent":
            # Autonomous Agent modu
            await self._handle_agent_task(data)
        
        elif msg_type == "feedback":
            await self._handle_feedback(data)
        
        elif msg_type == "compare":
            await self._handle_compare(data)
        
        elif msg_type == "confirm":
            await self._handle_confirm(data)
        
        # Bilinmeyen mesaj tipleri sessizce yoksayılır (hata gönderme!)
    
    async def _handle_resume(self, data: dict) -> None:
        """
        Resume komutunu işle - kaldığı yerden devam et.
        
        Client reconnect ettikten sonra eksik token'ları alır.
        """
        stream_id = data.get("stream_id")
        from_index = data.get("from_index", 0)
        
        if not stream_id:
            # Session'ın aktif stream'ini bul
            session_id = data.get("session_id") or self.conn.session_id
            if session_id:
                stream = stream_buffer.get_active_stream(session_id)
                if stream:
                    stream_id = stream.stream_id
        
        if not stream_id:
            await self._send({
                "type": "error",
                "code": "no_stream",
                "message": "Devam edilecek stream bulunamadı"
            })
            return
        
        # Resume verisini al
        resume_data = stream_buffer.get_resume_data(stream_id, from_index)
        
        if "error" in resume_data:
            await self._send({
                "type": "error",
                "code": "stream_not_found",
                "message": "Stream bulunamadı"
            })
            return
        
        # Resume verisini gönder
        await self._send({
            "type": "resume_data",
            **resume_data
        })
        
        # Eğer stream hala aktifse, yeni token'ları canlı olarak göndermeye devam et
        stream = stream_buffer.get_stream(stream_id)
        if stream and stream.is_active:
            self.conn.current_stream_id = stream_id
            # Stream'i takip et
            asyncio.create_task(self._follow_stream(stream_id, stream.token_count))
    
    async def _follow_stream(self, stream_id: str, last_sent_index: int) -> None:
        """
        Aktif bir stream'i takip et ve yeni token'ları gönder.
        
        Resume sonrası veya reconnect durumunda kullanılır.
        """
        while True:
            stream = stream_buffer.get_stream(stream_id)
            if not stream:
                break
            
            # Yeni token'lar var mı?
            if stream.token_count > last_sent_index:
                new_tokens = stream.get_tokens_from(last_sent_index)
                for token in new_tokens:
                    await self._send({
                        "type": "token",
                        "content": token.content,
                        "index": token.index
                    })
                last_sent_index = stream.token_count
            
            # Stream tamamlandı mı?
            if not stream.is_active:
                if stream.status == "completed":
                    await self._send({
                        "type": "end",
                        "stats": {
                            "duration_ms": stream.duration_ms,
                            "tokens": stream.token_count,
                        }
                    })
                elif stream.status == "stopped":
                    await self._send({
                        "type": "stopped",
                        "elapsed_ms": stream.duration_ms,
                        "tokens": stream.token_count,
                    })
                elif stream.status == "error":
                    await self._send({
                        "type": "error",
                        "message": stream.error or "Stream hatası"
                    })
                break
            
            # Kısa bekle
            await asyncio.sleep(0.05)
    
    async def _handle_stop(self) -> None:
        """Stop komutunu işle - o ana kadar yazılanları koru."""
        self.conn.stop_flag = True
        
        # Stream buffer'a stop isteği gönder
        if self.conn.session_id:
            stream_buffer.request_stop(self.conn.session_id)
        
        # Task'ı cancel etmiyoruz - streaming loop stop_flag'i kontrol edecek
        # ve graceful olarak duracak, böylece o ana kadar yazılanlar korunur
        # Stream task kendi "stopped" mesajını gönderecek
        
        # Sadece stream aktif değilse burada "stopped" gönder
        if not self._stream_task or self._stream_task.done():
            await self._send({"type": "stopped", "ts": int(time.time() * 1000)})
    
    async def _handle_chat(self, data: dict) -> None:
        """Chat mesajını işle."""
        # Rate limiting
        if not self.manager.check_rate_limit(self.conn.client_id):
            await self._send({
                "type": "error",
                "code": "rate_limited",
                "message": f"Çok fazla istek. {RATE_LIMIT_WINDOW} saniye bekleyin.",
                "retry_after": RATE_LIMIT_WINDOW
            })
            return
        
        message = data.get("message", "").strip()
        if not message:
            await self._send({
                "type": "error",
                "code": "empty_message",
                "message": "Mesaj boş olamaz"
            })
            return
        
        session_id = data.get("session_id") or str(uuid.uuid4())
        self.conn.session_id = session_id
        
        # Web search modu
        web_search = data.get("web_search", False)
        response_mode = data.get("response_mode", "normal")
        complexity_level = data.get("complexity_level", "auto")  # auto, simple, moderate, advanced, comprehensive
        
        # Önceki stream'i iptal et
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        
        # Yeni stream başlat
        self.conn.stop_flag = False
        self.conn.is_streaming = True
        self.conn.total_requests += 1
        
        self._stream_task = asyncio.create_task(
            self._stream_response(message, session_id, web_search, response_mode, complexity_level)
        )
    
    async def _handle_routed_message(self, data: dict) -> None:
        """
        Model routing destekli mesaj işleyici.
        
        Frontend'den gelen format:
        {
            "type": "message",
            "content": "...",
            "use_routing": true,
            "session_id": "..."
        }
        """
        # Rate limiting
        if not self.manager.check_rate_limit(self.conn.client_id):
            await self._send({
                "type": "error",
                "code": "rate_limited",
                "message": f"Çok fazla istek. {RATE_LIMIT_WINDOW} saniye bekleyin.",
                "retry_after": RATE_LIMIT_WINDOW
            })
            return
        
        message = data.get("content", "").strip()
        if not message:
            await self._send({
                "type": "error",
                "code": "empty_message",
                "message": "Mesaj boş olamaz"
            })
            return
        
        session_id = data.get("session_id") or str(uuid.uuid4())
        self.conn.session_id = session_id
        use_routing = data.get("use_routing", True)
        force_model = data.get("force_model")
        
        # Önceki stream'i iptal et
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        
        # Yeni stream başlat
        self.conn.stop_flag = False
        self.conn.is_streaming = True
        self.conn.total_requests += 1
        
        self._stream_task = asyncio.create_task(
            self._stream_routed_response(message, session_id, use_routing, force_model)
        )
    
    async def _handle_feedback(self, data: dict) -> None:
        """
        Kullanıcı feedback'ini işle.
        
        {
            "type": "feedback",
            "response_id": "...",
            "feedback_type": "correct" | "downgrade" | "upgrade"
        }
        """
        response_id = data.get("response_id")
        feedback_type = data.get("feedback_type")
        
        if not response_id or not feedback_type:
            await self._send({
                "type": "error",
                "code": "missing_fields",
                "message": "response_id ve feedback_type gerekli"
            })
            return
        
        try:
            fb_type = FeedbackType(feedback_type)
            
            # Suggested model
            suggested_model = None
            if fb_type == FeedbackType.DOWNGRADE:
                suggested_model = ModelSize.SMALL
            elif fb_type == FeedbackType.UPGRADE:
                suggested_model = ModelSize.LARGE
            
            model_router = get_model_router()
            feedback = model_router.submit_feedback(
                response_id=response_id,
                feedback_type=fb_type,
                suggested_model=suggested_model,
            )
            
            # Yanıt
            requires_comparison = fb_type != FeedbackType.CORRECT
            
            if fb_type == FeedbackType.CORRECT:
                message_text = "✅ Teşekkürler! Tercih kaydedildi."
            elif fb_type == FeedbackType.DOWNGRADE:
                message_text = "🔄 Küçük modeli denemek için 'Dene' butonunu kullanın."
            else:
                message_text = "🔄 Büyük modeli denemek için 'Dene' butonunu kullanın."
            
            await self._send({
                "type": "feedback_received",
                "feedback": feedback.to_dict(),
                "message": message_text,
                "requires_comparison": requires_comparison,
                "status": feedback.status.value,
                "timestamp": datetime.now().isoformat()
            })
            
        except ValueError as e:
            await self._send({
                "type": "error",
                "code": "invalid_feedback",
                "message": str(e)
            })
    
    async def _handle_compare(self, data: dict) -> None:
        """
        Model karşılaştırma isteğini işle.
        
        {
            "type": "compare",
            "response_id": "...",
            "query": "..."
        }
        """
        response_id = data.get("response_id")
        query = data.get("query", "")
        
        if not response_id:
            await self._send({
                "type": "error",
                "code": "missing_fields",
                "message": "response_id gerekli"
            })
            return
        
        try:
            model_router = get_model_router()
            
            # Response'dan original model bilgisini al
            response = model_router.storage.get_response(response_id)
            if not response:
                await self._send({
                    "type": "error",
                    "code": "response_not_found",
                    "message": "Response bulunamadı"
                })
                return
            
            original_model_size = ModelSize(response["model_size"])
            
            # Alternatif modeli belirle
            if original_model_size == ModelSize.LARGE:
                comparison_model = MODEL_CONFIG[ModelSize.SMALL]["name"]
                comparison_display = MODEL_CONFIG[ModelSize.SMALL]["display_name"]
                comparison_icon = MODEL_CONFIG[ModelSize.SMALL]["icon"]
            else:
                comparison_model = MODEL_CONFIG[ModelSize.LARGE]["name"]
                comparison_display = MODEL_CONFIG[ModelSize.LARGE]["display_name"]
                comparison_icon = MODEL_CONFIG[ModelSize.LARGE]["icon"]
            
            # Karşılaştırma başlangıcı
            await self._send({
                "type": "compare_start",
                "response_id": response_id,
                "model": comparison_model,
                "model_display_name": comparison_display,
                "model_icon": comparison_icon,
                "timestamp": datetime.now().isoformat()
            })
            
            # Query'yi al
            if not query:
                query = response.get("query", "Merhaba")
            
            # Alternatif modelden yanıt üret
            from core.system_knowledge import SELF_KNOWLEDGE_PROMPT
            system_prompt = SELF_KNOWLEDGE_PROMPT
            
            async for chunk in llm_manager.generate_stream_async(
                prompt=query,
                system_prompt=system_prompt,
                temperature=0.7,
                model=comparison_model,
            ):
                if self.conn.stop_flag:
                    break
                
                await self._send({
                    "type": "compare_chunk",
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })
            
            await self._send({
                "type": "compare_end",
                "response_id": response_id,
                "model": comparison_model,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Compare error: {e}")
            await self._send({
                "type": "error",
                "code": "compare_failed",
                "message": str(e)[:200]
            })
    
    async def _handle_confirm(self, data: dict) -> None:
        """
        Feedback onayını işle.
        
        {
            "type": "confirm",
            "feedback_id": "...",
            "confirmed": true/false,
            "selected_model": "small"/"large"
        }
        """
        feedback_id = data.get("feedback_id")
        confirmed = data.get("confirmed", False)
        selected_model = data.get("selected_model")
        
        if not feedback_id:
            await self._send({
                "type": "error",
                "code": "missing_fields",
                "message": "feedback_id gerekli"
            })
            return
        
        try:
            model_router = get_model_router()
            
            # Final decision'ı belirle
            final_decision = None
            if selected_model:
                final_decision = ModelSize.SMALL if selected_model == "small" else ModelSize.LARGE
            
            feedback = model_router.confirm_feedback(
                feedback_id=feedback_id,
                confirmed=confirmed,
                final_decision=final_decision,
            )
            
            if confirmed:
                model_config = MODEL_CONFIG.get(feedback.final_decision, {})
                model_name = model_config.get("display_name", "Model")
                message_text = f"✅ Tercih kaydedildi! Benzer sorgular için {model_name} kullanılacak."
                learning_applied = True
            else:
                message_text = "↩️ İlk tercih korundu. Teşekkürler!"
                learning_applied = False
            
            await self._send({
                "type": "feedback_confirmed",
                "feedback": feedback.to_dict(),
                "message": message_text,
                "learning_applied": learning_applied,
                "timestamp": datetime.now().isoformat()
            })
            
        except ValueError as e:
            await self._send({
                "type": "error",
                "code": "confirm_failed",
                "message": str(e)
            })
    
    async def _handle_agent_task(self, data: dict) -> None:
        """
        Autonomous Agent görevini WebSocket üzerinden işle.
        
        Mesaj formatı:
        {
            "type": "agent",
            "action": "create" | "start" | "respond" | "cancel",
            "task_id": str (optional),
            "goal": str (create için),
            "context": dict (optional),
            "response": str (respond için),
            "intervention_type": str (respond için)
        }
        """
        from agents.autonomous_agent import (
            StreamingAutonomousAgent, AgentTask, HumanIntervention, InterventionType
        )
        
        action = data.get("action", "create")
        task_id = data.get("task_id")
        
        try:
            if action == "create":
                # Yeni görev oluştur
                goal = data.get("goal", "")
                context = data.get("context", {})
                
                if not goal:
                    await self._send({
                        "type": "agent_error",
                        "code": "missing_goal",
                        "message": "Görev hedefi belirtilmedi"
                    })
                    return
                
                # Streaming agent oluştur
                agent = StreamingAutonomousAgent(max_steps=10, max_retries=3)
                
                # Görev oluştur
                task = await agent.create_task(goal, context)
                
                # Agent'ı sakla (session bazlı)
                if not hasattr(self.conn, 'active_agents'):
                    self.conn.active_agents = {}
                self.conn.active_agents[task.id] = agent
                
                # Görev oluşturuldu bilgisi
                await self._send({
                    "type": "agent_task_created",
                    "task": {
                        "task_id": task.id,
                        "goal": task.user_request,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat()
                    },
                    "message": f"🎯 Görev oluşturuldu: {task.user_request[:100]}..."
                })
                
                # Otomatik olarak görevi başlat ve planla
                await self._send({
                    "type": "agent_planning",
                    "task_id": task.id,
                    "message": "📋 Görev planlanıyor..."
                })
                
                # Görevi planla
                plan = await agent.plan_task(task)
                
                # Plan bilgisini gönder
                await self._send({
                    "type": "agent_plan_ready",
                    "task_id": task.id,
                    "plan": {
                        "total_steps": plan.total_steps,
                        "steps": [
                            {
                                "step_number": step.step_number,
                                "description": step.description,
                                "tool_name": step.tool_name
                            }
                            for step in plan.steps
                        ]
                    },
                    "message": f"✅ Plan hazır: {plan.total_steps} adım"
                })
                
                # Görevi stream olarak çalıştır
                await self._execute_agent_task_streaming(agent, task)
                
            elif action == "start":
                # Bekleyen görevi başlat
                if not task_id or task_id not in getattr(self.conn, 'active_agents', {}):
                    await self._send({
                        "type": "agent_error",
                        "code": "task_not_found",
                        "message": "Görev bulunamadı"
                    })
                    return
                
                agent = self.conn.active_agents[task_id]
                task = agent._tasks.get(task_id)
                
                if task:
                    await self._execute_agent_task_streaming(agent, task)
                    
            elif action == "respond":
                # İnsan müdahalesine yanıt
                if not task_id or task_id not in getattr(self.conn, 'active_agents', {}):
                    await self._send({
                        "type": "agent_error",
                        "code": "task_not_found",
                        "message": "Görev bulunamadı"
                    })
                    return
                
                agent = self.conn.active_agents[task_id]
                response = data.get("response", "")
                
                # Yanıtı işle
                if hasattr(agent, 'pending_intervention') and agent.pending_intervention:
                    intervention = agent.pending_intervention
                    intervention.response = response
                    intervention.responded = True
                    agent.pending_intervention = None
                    
                    await self._send({
                        "type": "agent_intervention_response",
                        "task_id": task_id,
                        "response": response,
                        "message": "✅ Yanıt alındı, devam ediliyor..."
                    })
                    
            elif action == "cancel":
                # Görevi iptal et
                if task_id and task_id in getattr(self.conn, 'active_agents', {}):
                    agent = self.conn.active_agents[task_id]
                    task = agent._tasks.get(task_id)
                    if task:
                        from agents.autonomous_agent import TaskStatus
                        task.status = TaskStatus.CANCELLED
                        
                    del self.conn.active_agents[task_id]
                    
                    await self._send({
                        "type": "agent_task_cancelled",
                        "task_id": task_id,
                        "message": "❌ Görev iptal edildi"
                    })
                    
        except Exception as e:
            logger.error(f"Agent task error: {e}")
            await self._send({
                "type": "agent_error",
                "code": "agent_failed",
                "message": str(e)
            })
    
    async def _execute_agent_task_streaming(self, agent, task) -> None:
        """Agent görevini streaming olarak çalıştır."""
        from agents.autonomous_agent import TaskStatus, StepStatus
        
        task_id = task.id
        
        try:
            # Plan kontrolü
            if not task.plan or not task.plan.steps:
                await self._send({
                    "type": "agent_error",
                    "task_id": task_id,
                    "code": "no_plan",
                    "message": "❌ Görev planı bulunamadı"
                })
                return
            
            # Görevi başlat
            await self._send({
                "type": "agent_executing",
                "task_id": task_id,
                "message": "🚀 Görev çalıştırılıyor..."
            })
            
            # Her adımı çalıştır
            for step in task.plan.steps:
                if task.status == TaskStatus.CANCELLED:
                    break
                    
                # Adım başladı
                await self._send({
                    "type": "agent_step_start",
                    "task_id": task_id,
                    "step": {
                        "step_number": step.step_number,
                        "description": step.description,
                        "tool_name": step.tool_name
                    },
                    "message": f"⚙️ Adım {step.step_number}/{task.plan.total_steps}: {step.description}"
                })
                
                # Adımı çalıştır
                try:
                    success, result = await agent.execute_step(task, step)
                    
                    # Adım tamamlandı
                    await self._send({
                        "type": "agent_step_complete",
                        "task_id": task_id,
                        "step": {
                            "step_number": step.step_number,
                            "status": step.status.value,
                            "success": success,
                            "result": str(result)[:500] if result else None
                        },
                        "message": f"✅ Adım {step.step_number} tamamlandı"
                    })
                    
                except Exception as step_error:
                    # Adım başarısız
                    await self._send({
                        "type": "agent_step_failed",
                        "task_id": task_id,
                        "step": {
                            "step_number": step.step_number,
                            "error": str(step_error)
                        },
                        "message": f"❌ Adım {step.step_number} başarısız: {step_error}"
                    })
                    
                    # Self-correction dene
                    if step.attempts < step.max_attempts:
                        await self._send({
                            "type": "agent_self_correction",
                            "task_id": task_id,
                            "retry": step.attempts,
                            "message": f"🔄 Düzeltme deneniyor ({step.attempts}/{step.max_attempts})..."
                        })
                
                # Küçük gecikme
                await asyncio.sleep(0.1)
            
            # Görev tamamlandı
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            # Sonucu oluştur
            await agent._generate_summary(task)
            final_result = task.final_result or "Görev tamamlandı"
            
            progress = task.plan.get_progress() if task.plan else {"completed": 0}
            await self._send({
                "type": "agent_task_complete",
                "task_id": task_id,
                "result": final_result,
                "stats": {
                    "total_steps": task.plan.total_steps if task.plan else 0,
                    "completed_steps": progress.get("completed", 0),
                    "duration": (task.completed_at - task.created_at).total_seconds() if task.completed_at else 0
                },
                "message": "🎉 Görev başarıyla tamamlandı!"
            })
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            await self._send({
                "type": "agent_task_failed",
                "task_id": task_id,
                "error": str(e),
                "message": f"💥 Görev başarısız: {e}"
            })
    
    async def _stream_routed_response(
        self,
        message: str,
        session_id: str,
        use_routing: bool = True,
        force_model: Optional[str] = None,
    ) -> None:
        """
        Model routing ile streaming yanıt üret.
        
        Args:
            message: Kullanıcı mesajı
            session_id: Session ID
            use_routing: Model routing kullanılsın mı
            force_model: Zorla belirli model kullan
        """
        stats = StreamStats(start_time=time.time())
        
        # Stream buffer'da yeni stream oluştur
        stream = stream_buffer.create_stream(session_id, message)
        stream_id = stream.stream_id
        self.conn.current_stream_id = stream_id
        
        try:
            model_router = get_model_router()
            
            # 1. ROUTING
            if force_model:
                # Zorla belirtilen model
                routing_info = {
                    "model_name": force_model,
                    "model_size": "unknown",
                    "decision_source": "forced",
                    "confidence": 1.0,
                    "response_id": str(uuid.uuid4()),
                }
            elif use_routing:
                # Model router kullan
                routing_result = await model_router.route_async(message)
                routing_info = routing_result.to_dict()
                
                # Routing bilgisini gönder
                await self._send({
                    "type": "routing",
                    "routing_info": routing_info,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                # Default small model
                routing_info = {
                    "model_name": MODEL_CONFIG[ModelSize.SMALL]["name"],
                    "model_size": "small",
                    "decision_source": "default",
                    "confidence": 1.0,
                    "response_id": str(uuid.uuid4()),
                }
            
            model_name = routing_info["model_name"]
            response_id = routing_info.get("response_id", str(uuid.uuid4()))
            
            # Başlangıç mesajı
            await self._send({
                "type": "start",
                "ts": int(time.time() * 1000),
                "session_id": session_id,
                "stream_id": stream_id,
            })
            
            # 2. LLM'DEN STREAMING YANIT
            from core.system_knowledge import SELF_KNOWLEDGE_PROMPT
            system_prompt = SELF_KNOWLEDGE_PROMPT
            
            full_response = ""
            token_index = 0
            
            async with asyncio_timeout(STREAM_TIMEOUT):
                async for chunk in llm_manager.generate_stream_async(
                    prompt=message,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    model=model_name,
                ):
                    # Stop kontrolü
                    if self.conn.stop_flag or stream_buffer.is_stop_requested(stream_id):
                        stats.was_stopped = True
                        stream_buffer.stop_stream(stream_id)
                        break
                    
                    if chunk:
                        stats.token_count += 1
                        stats.char_count += len(chunk)
                        full_response += chunk
                        
                        # Token'ı buffer'a kaydet
                        token = stream_buffer.add_token(stream_id, chunk)
                        
                        # ANLIK gönder
                        await self._send({
                            "type": "chunk",
                            "content": chunk,
                            "index": token.index if token else token_index
                        })
                        token_index += 1
            
            stats.end_time = time.time()
            self.conn.total_tokens += stats.token_count
            
            # 3. BİTİŞ
            if stats.was_stopped:
                stream_buffer.stop_stream(stream_id)
                await self._send({
                    "type": "stopped",
                    "elapsed_ms": stats.duration_ms,
                    "tokens": stats.token_count,
                    "stream_id": stream_id,
                })
            else:
                stream_buffer.complete_stream(stream_id)
                await self._send({
                    "type": "complete",
                    "response_id": response_id,
                    "model_info": routing_info,
                    "stats": stats.to_dict(),
                    "ts": int(time.time() * 1000),
                    "stream_id": stream_id,
                })
            
            # Session'a kaydet
            if full_response:
                try:
                    session_manager.add_message(session_id, "user", message)
                    saved_response = full_response
                    if stats.was_stopped:
                        saved_response += "\n\n*[Yanıt durduruldu]*"
                    session_manager.add_message(session_id, "assistant", saved_response)
                except Exception as e:
                    logger.warning(f"Session save error: {e}")
            
        except asyncio.TimeoutError:
            stats.error = "timeout"
            stream_buffer.error_stream(stream_id, "timeout")
            await self._send({
                "type": "error",
                "code": "timeout",
                "message": f"Yanıt {STREAM_TIMEOUT} saniye içinde tamamlanamadı",
                "elapsed_ms": stats.duration_ms,
                "stream_id": stream_id,
            })
        
        except asyncio.CancelledError:
            stats.was_stopped = True
            stats.end_time = time.time()
            stream_buffer.stop_stream(stream_id)
            logger.debug(f"Stream cancelled: {self.conn.client_id}")
            try:
                await self._send({
                    "type": "stopped",
                    "elapsed_ms": stats.duration_ms,
                    "tokens": stats.token_count,
                    "stream_id": stream_id,
                })
            except Exception:
                pass
        
        except Exception as e:
            stats.error = str(e)
            logger.exception(f"Routed stream error: {self.conn.client_id}")
            await self._send({
                "type": "error",
                "code": "stream_failed",
                "message": str(e)[:300],
                "elapsed_ms": stats.duration_ms,
            })
        
        finally:
            self.conn.is_streaming = False

    async def _stream_response(
        self, 
        message: str, 
        session_id: str,
        web_search: bool = False,
        response_mode: str = "normal",
        complexity_level: str = "auto"
    ) -> None:
        """
        Streaming yanıt üret ve gönder.
        
        Token'lar StreamBuffer'da saklanır - WebSocket kopsa bile kaybolmaz.
        Client reconnect edince kaldığı yerden devam edebilir.
        
        Args:
            complexity_level: "auto", "simple", "moderate", "advanced", "comprehensive"
        """
        stats = StreamStats(start_time=time.time())
        
        # Stream buffer'da yeni stream oluştur
        stream = stream_buffer.create_stream(session_id, message)
        stream_id = stream.stream_id
        self.conn.current_stream_id = stream_id
        
        # Başlangıç mesajı - stream_id ile
        await self._send({
            "type": "start",
            "ts": int(time.time() * 1000),
            "session_id": session_id,
            "stream_id": stream_id,  # Client bu ID ile resume yapabilir
        })
        
        try:
            # ⚡ SIMPLE MOD: Ultra hızlı - RAG araması yapma, direkt LLM
            skip_rag = complexity_level == "simple"
            
            async with asyncio_timeout(STREAM_TIMEOUT):
                knowledge_context = ""
                sources = []
                
                # Simple modda RAG'ı atla - maksimum hız
                if not skip_rag:
                    # Knowledge base'den context al
                    await self._send({
                        "type": "status",
                        "message": "Bilgi tabanı aranıyor...",
                        "phase": "search"
                    })
                    
                    # RAG search
                    try:
                        results = vector_store.search_with_scores(query=message, n_results=5, score_threshold=0.3)
                        if results:
                            knowledge_context = "\n\n".join([
                                f"[Kaynak: {r.get('metadata', {}).get('filename', 'unknown')}]\n{r.get('document', '')}"
                                for r in results[:3]
                            ])
                            # Frontend'in beklediği dict formatında sources oluştur
                            for r in results:
                                meta = r.get('metadata', {})
                                doc_text = r.get('document', '')[:200]  # snippet
                                sources.append({
                                    "title": meta.get('filename', 'Kaynak'),
                                    "url": meta.get('source', '#'),
                                    "domain": "📄 Yerel Dosya",
                                    "snippet": doc_text,
                                    "type": "unknown",
                                    "reliability": r.get('score', 0.5),
                                })
                    except Exception as e:
                        logger.warning(f"RAG search error: {e}")
                    
                # Kaynakları buffer'a kaydet
                if sources:
                    stream_buffer.set_sources(stream_id, sources[:5])
                    await self._send({
                        "type": "sources",
                        "sources": sources[:5]
                    })
                
                # LLM'e gönder
                await self._send({
                    "type": "status",
                    "message": "Yanıt oluşturuluyor..." if not skip_rag else "⚡ Hızlı yanıt...",
                    "phase": "generate"
                })
                
                # System prompt oluştur
                from core.system_knowledge import SELF_KNOWLEDGE_PROMPT
                system_prompt = SELF_KNOWLEDGE_PROMPT
                
                if knowledge_context:
                    system_prompt += f"\n\n📚 İlgili Bilgiler:\n{knowledge_context}"
                
                # Complexity level'a göre prompt ayarla
                complexity_instructions = {
                    "simple": "\n\n⚡ YANITLAMA STİLİ: ÇOK KISA yanıt ver. Sadece 1-2 cümle. Gereksiz detay VERME.",
                    "moderate": "\n\n📝 YANITLAMA STİLİ: Orta uzunlukta, dengeli yanıt ver. Ana noktaları açıkla.",
                    "advanced": "\n\n📊 YANITLAMA STİLİ: Detaylı analiz yap. Örnekler ve açıklamalar ekle.",
                    "comprehensive": "\n\n📚 YANITLAMA STİLİ: Kapsamlı ve derinlemesine yanıt ver. Tüm yönleri ele al, kaynaklar ve örneklerle destekle.",
                }
                if complexity_level in complexity_instructions:
                    system_prompt += complexity_instructions[complexity_level]
                
                # Streaming response - token'lar buffer'a kaydedilir
                full_response = ""
                token_index = 0
                async for chunk in llm_manager.generate_stream_async(
                    prompt=message,
                    system_prompt=system_prompt,
                ):
                    # Stop kontrolü - hem local flag hem buffer'dan
                    if self.conn.stop_flag or stream_buffer.is_stop_requested(stream_id):
                        stats.was_stopped = True
                        stream_buffer.stop_stream(stream_id)
                        break
                    
                    if chunk:
                        stats.token_count += 1
                        stats.char_count += len(chunk)
                        full_response += chunk
                        
                        # Token'ı buffer'a kaydet
                        token = stream_buffer.add_token(stream_id, chunk)
                        
                        # ANLIK gönder - index ile (resume için gerekli)
                        await self._send({
                            "type": "token",
                            "content": chunk,
                            "index": token.index if token else token_index
                        })
                        token_index += 1
                
                stats.end_time = time.time()
                self.conn.total_tokens += stats.token_count
                
                # Bitiş mesajı ve buffer güncelle
                if stats.was_stopped:
                    stream_buffer.stop_stream(stream_id)
                    await self._send({
                        "type": "stopped",
                        "elapsed_ms": stats.duration_ms,
                        "tokens": stats.token_count,
                        "stream_id": stream_id,
                    })
                else:
                    stream_buffer.complete_stream(stream_id)
                    await self._send({
                        "type": "end",
                        "stats": stats.to_dict(),
                        "ts": int(time.time() * 1000),
                        "stream_id": stream_id,
                    })
                
                # Session'a kaydet (durdurulsa bile kısmi yanıtı kaydet)
                if full_response:
                    try:
                        session_manager.add_message(session_id, "user", message)
                        # Durdurulduysa yanıta işaret ekle
                        saved_response = full_response
                        if stats.was_stopped:
                            saved_response += "\n\n*[Yanıt durduruldu]*"
                        session_manager.add_message(session_id, "assistant", saved_response)
                    except Exception as e:
                        logger.warning(f"Session save error: {e}")
                
        except asyncio.TimeoutError:
            stats.error = "timeout"
            stream_buffer.error_stream(stream_id, "timeout")
            await self._send({
                "type": "error",
                "code": "timeout",
                "message": f"Yanıt {STREAM_TIMEOUT} saniye içinde tamamlanamadı",
                "elapsed_ms": stats.duration_ms,
                "stream_id": stream_id,
            })
        
        except asyncio.CancelledError:
            # Kullanıcı durduğunda, o ana kadar yazılanları koru
            stats.was_stopped = True
            stats.end_time = time.time()
            stream_buffer.stop_stream(stream_id)
            logger.debug(f"Stream cancelled: {self.conn.client_id}, tokens: {stats.token_count}")
            # Frontend'e "stopped" mesajı gönder - o ana kadar yazılanlar korunacak
            try:
                await self._send({
                    "type": "stopped",
                    "elapsed_ms": stats.duration_ms,
                    "tokens": stats.token_count,
                    "partial": True,
                    "stream_id": stream_id,
                })
            except Exception:
                pass  # Bağlantı kapanmış olabilir
        
        except Exception as e:
            stats.error = str(e)
            logger.exception(f"Stream error: {self.conn.client_id}")
            await self._send({
                "type": "error",
                "code": "stream_failed",
                "message": str(e)[:300],
                "elapsed_ms": stats.duration_ms,
            })
        
        finally:
            self.conn.is_streaming = False
    
    async def _keepalive_loop(self) -> None:
        """Keepalive ping gönder."""
        try:
            while True:
                await asyncio.sleep(PING_INTERVAL)
                await self._send({
                    "type": "ping",
                    "ts": int(time.time() * 1000)
                })
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"Keepalive error: {e}")
    
    async def _send(self, data: dict) -> bool:
        """Mesaj gönder."""
        return await self.manager.send(self.conn.client_id, data)


# =============================================================================
# FASTAPI WEBSOCKET ENDPOINT
# =============================================================================

async def websocket_endpoint_v2(websocket: WebSocket, client_id: str) -> None:
    """
    Enterprise WebSocket endpoint v2.
    
    Args:
        websocket: WebSocket bağlantısı
        client_id: Client ID
    """
    handler: Optional[WebSocketHandlerV2] = None
    
    try:
        # Bağlantıyı kabul et
        conn = await ws_manager.connect(websocket, client_id)
        
        # Handler oluştur ve başlat
        handler = WebSocketHandlerV2(conn, ws_manager)
        await handler.start()
        
        # Mesaj döngüsü
        while True:
            try:
                # Mesaj bekle
                data = await websocket.receive_json()
                
                # Mesaj boyutu kontrolü
                if len(json.dumps(data)) > MAX_MESSAGE_SIZE:
                    await ws_manager.send(client_id, {
                        "type": "error",
                        "code": "message_too_large",
                        "message": f"Maksimum mesaj boyutu: {MAX_MESSAGE_SIZE} byte"
                    })
                    continue
                
                # Mesajı işle
                await handler.handle_message(data)
                
            except json.JSONDecodeError:
                await ws_manager.send(client_id, {
                    "type": "error",
                    "code": "invalid_json",
                    "message": "Geçersiz JSON formatı"
                })
    
    except WebSocketDisconnect:
        logger.debug(f"WebSocket disconnect: {client_id}")
    
    except ConnectionError as e:
        logger.warning(f"Connection error: {client_id}, {e}")
    
    except Exception as e:
        logger.exception(f"WebSocket error: {client_id}")
    
    finally:
        # Temizlik
        if handler:
            await handler.stop()
        await ws_manager.disconnect(client_id)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ws_manager',
    'websocket_endpoint_v2',
    'WebSocketManagerV2',
    'WebSocketHandlerV2',
    'ClientConnection',
    'StreamStats',
]
