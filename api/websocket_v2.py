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
        {"type": "ping"}  - Manuel ping
    
    Server -> Client:
        {"type": "connected", "client_id": "...", "ts": ...}
        {"type": "start", "ts": ...}  - Yanıt başladı
        {"type": "token", "content": "..."}  - Her token anında
        {"type": "status", "message": "...", "phase": "..."}  - Durum güncellemesi
        {"type": "sources", "sources": [...]}  - Kaynaklar
        {"type": "end", "stats": {...}}  - Tamamlandı
        {"type": "error", "message": "..."}  - Hata
        {"type": "stopped", "elapsed_ms": ...}  - Durduruldu
        {"type": "pong", "ts": ...}  - Ping yanıtı
"""

import json
import asyncio
import time
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from core.config import settings
from core.llm_manager import llm_manager
from core.vector_store import vector_store
from core.session_manager import session_manager
from agents.orchestrator import orchestrator

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

PING_INTERVAL: int = 25          # Keepalive ping aralığı (saniye)
STREAM_TIMEOUT: int = 180        # Maksimum yanıt süresi (saniye)
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
        
        elif msg_type == "chat":
            await self._handle_chat(data)
        
        # Bilinmeyen mesaj tipleri sessizce yoksayılır (hata gönderme!)
    
    async def _handle_stop(self) -> None:
        """Stop komutunu işle."""
        self.conn.stop_flag = True
        
        if self._stream_task and not self._stream_task.done():
            self._stream_task.cancel()
        
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
        
        Her token anında client'a iletilir - buffering YOK.
        
        Args:
            complexity_level: "auto", "simple", "moderate", "advanced", "comprehensive"
        """
        stats = StreamStats(start_time=time.time())
        
        # Başlangıç mesajı
        await self._send({
            "type": "start",
            "ts": int(time.time() * 1000),
            "session_id": session_id,
        })
        
        try:
            # ⚡ SIMPLE MOD: Ultra hızlı - RAG araması yapma, direkt LLM
            skip_rag = complexity_level == "simple"
            
            async with asyncio.timeout(STREAM_TIMEOUT):
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
                    
                    # Kaynakları gönder
                    if sources:
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
                
                # Streaming response
                full_response = ""
                async for chunk in llm_manager.generate_stream_async(
                    prompt=message,
                    system_prompt=system_prompt,
                ):
                    # Stop kontrolü
                    if self.conn.stop_flag:
                        stats.was_stopped = True
                        break
                    
                    if chunk:
                        stats.token_count += 1
                        stats.char_count += len(chunk)
                        full_response += chunk
                        
                        # ANLIK gönder
                        await self._send({
                            "type": "token",
                            "content": chunk
                        })
                
                stats.end_time = time.time()
                self.conn.total_tokens += stats.token_count
                
                # Bitiş mesajı
                if stats.was_stopped:
                    await self._send({
                        "type": "stopped",
                        "elapsed_ms": stats.duration_ms,
                        "tokens": stats.token_count,
                    })
                else:
                    await self._send({
                        "type": "end",
                        "stats": stats.to_dict(),
                        "ts": int(time.time() * 1000),
                    })
                
                # Session'a kaydet
                if full_response and not stats.was_stopped:
                    try:
                        session_manager.add_message(session_id, "user", message)
                        session_manager.add_message(session_id, "assistant", full_response)
                    except Exception as e:
                        logger.warning(f"Session save error: {e}")
                
        except asyncio.TimeoutError:
            stats.error = "timeout"
            await self._send({
                "type": "error",
                "code": "timeout",
                "message": f"Yanıt {STREAM_TIMEOUT} saniye içinde tamamlanamadı",
                "elapsed_ms": stats.duration_ms,
            })
        
        except asyncio.CancelledError:
            stats.was_stopped = True
            logger.debug(f"Stream cancelled: {self.conn.client_id}")
        
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
