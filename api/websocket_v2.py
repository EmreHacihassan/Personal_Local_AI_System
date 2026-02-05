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

# Python 3.10 ve altı için async_timeout uyumluluğu - GERÇEK TIMEOUT İMPLEMENTASYONU
if sys.version_info < (3, 11):
    try:
        from async_timeout import timeout as asyncio_timeout
    except ImportError:
        # async_timeout yoksa, GERÇEK timeout implementasyonu - BU KRİTİK!
        @asynccontextmanager
        async def asyncio_timeout(seconds: float):
            """
            Gerçek timeout wrapper - Python 3.10 uyumlu.
            
            Bu implementasyon GERÇEKTEN timeout uygular!
            Eski versiyon sadece 'yield' yapıyordu ve timeout ÇALIŞMIYORDU.
            """
            loop = asyncio.get_running_loop()
            task = asyncio.current_task()
            timed_out = False
            
            def timeout_handler():
                nonlocal timed_out
                timed_out = True
                if task and not task.done():
                    task.cancel()
            
            # Timeout timer'ı başlat
            handle = loop.call_later(seconds, timeout_handler)
            try:
                yield
            except asyncio.CancelledError:
                if timed_out:
                    raise asyncio.TimeoutError(f"Operation timed out after {seconds} seconds")
                raise
            finally:
                handle.cancel()
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

# Intent classifier import
try:
    from core.intent_classifier import intent_classifier, QueryIntent, ResponseStrategy
except ImportError:
    intent_classifier = None
    QueryIntent = None
    ResponseStrategy = None

# Web search import
try:
    from tools.web_search_engine import get_search_engine
    web_search_engine = get_search_engine()
except ImportError:
    web_search_engine = None

# Premium modules import
try:
    from core.response_length_manager import ResponseLengthManager
    response_length_manager = ResponseLengthManager()
except ImportError:
    response_length_manager = None

try:
    from core.source_quality_scorer import SourceQualityScorer
    source_quality_scorer = SourceQualityScorer()
except ImportError:
    source_quality_scorer = None

try:
    from core.semantic_query_expander import SemanticQueryExpander
    semantic_query_expander = SemanticQueryExpander()
except ImportError:
    semantic_query_expander = None

try:
    from core.smart_title_generator import SmartTitleGenerator
    smart_title_generator = SmartTitleGenerator()
except ImportError:
    smart_title_generator = None

# === PREMIUM FULL QUALITY MODULES ===

# CRAG - Corrective RAG System
try:
    from core.crag_system import (
        CRAGPipeline, RelevanceGrader, QueryTransformer, HallucinationDetector,
        RelevanceGrade, CorrectionAction, HallucinationRisk, GradedDocument, CRAGResult
    )
    # Lazy initialization - CRAGPipeline requires retriever/generator
    crag_pipeline = None  # Will be initialized when needed
    relevance_grader = RelevanceGrader()
    query_transformer = QueryTransformer()
    hallucination_detector = HallucinationDetector()
    CRAG_AVAILABLE = True
    logging.info("✅ CRAG System loaded")
except ImportError as e:
    crag_pipeline = None
    relevance_grader = None
    query_transformer = None
    hallucination_detector = None
    CRAG_AVAILABLE = False
    logging.warning(f"⚠️ CRAG System not available: {e}")

# MoE Router - Mixture of Experts
try:
    from core.moe_router import (
        MoERouter, AdaptiveMoERouter, QueryAnalyzer as MoEQueryAnalyzer,
        ExpertType, QueryComplexity as MoEComplexity, RoutingStrategy,
        RoutingDecision, RoutingResult
    )
    moe_router = AdaptiveMoERouter(strategy=RoutingStrategy.BALANCED)
    moe_query_analyzer = MoEQueryAnalyzer()
    MOE_AVAILABLE = True
    logging.info("✅ MoE Router loaded")
except ImportError as e:
    moe_router = None
    moe_query_analyzer = None
    MOE_AVAILABLE = False
    logging.warning(f"⚠️ MoE Router not available: {e}")

# Multi-Agent Debate System
try:
    from core.multi_agent_debate import (
        DebateOrchestrator, DebateAgent,
        AgentRole, DebatePhase, VoteType, Argument, DebateResult,
        multi_agent_debate
    )
    # Lazy initialization - DebateOrchestrator requires llm_factory
    debate_orchestrator = None  # Will be initialized when needed
    DEBATE_AVAILABLE = True
    logging.info("✅ Multi-Agent Debate loaded")
except ImportError as e:
    debate_orchestrator = None
    DEBATE_AVAILABLE = False
    logging.warning(f"⚠️ Multi-Agent Debate not available: {e}")

# MemGPT-Style Tiered Memory
try:
    from core.memgpt_memory import (
        TieredMemoryManager, CoreMemory, MemoryBlock,
        MemoryType, MemoryPriority
    )
    # Lazy initialization - TieredMemoryManager requires storage
    memory_manager = None  # Will be initialized when needed
    MEMGPT_AVAILABLE = True
    logging.info("✅ MemGPT Memory loaded")
except ImportError as e:
    memory_manager = None
    MEMGPT_AVAILABLE = False
    logging.warning(f"⚠️ MemGPT Memory not available: {e}")

# RAGAS Evaluation System
try:
    from core.ragas_evaluation import (
        RAGASEvaluator, quick_evaluate,
        MetricType, EvaluationSample, EvaluationResult
    )
    ragas_evaluator = RAGASEvaluator()
    RAGAS_AVAILABLE = True
    logging.info("✅ RAGAS Evaluation loaded")
except ImportError as e:
    ragas_evaluator = None
    RAGAS_AVAILABLE = False
    logging.warning(f"⚠️ RAGAS Evaluation not available: {e}")

# Feature Flags System
try:
    from core.config import FeatureFlags, feature_enabled
    FEATURE_FLAGS_AVAILABLE = True
except ImportError:
    FEATURE_FLAGS_AVAILABLE = False
    def feature_enabled(flag): return True

# Services import
try:
    from services.query_analyzer import query_analyzer, QueryComplexity, QueryType
    from services.rag_service import rag_service, EnrichedContext
    from services.websocket_service import ws_service, WSPhase, WSMessageType, WSErrorCode, MessageBuilder
    from services.routing_service import routing_service
    SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Services not available: {e}")
    query_analyzer = None
    rag_service = None
    ws_service = None
    routing_service = None
    SERVICES_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION (from settings)
# =============================================================================

PING_INTERVAL: int = settings.WS_PING_INTERVAL      # Keepalive ping aralığı (saniye)
STREAM_TIMEOUT: int = settings.WS_STREAM_TIMEOUT    # Maksimum yanıt süresi (saniye)
RAG_SEARCH_TIMEOUT: int = settings.WS_RAG_SEARCH_TIMEOUT  # RAG search timeout
WEB_SEARCH_TIMEOUT: int = settings.WS_WEB_SEARCH_TIMEOUT  # Web search timeout
MODEL_ROUTING_TIMEOUT: int = settings.WS_MODEL_ROUTING_TIMEOUT  # Model routing timeout
RATE_LIMIT_WINDOW: int = 5       # Rate limit penceresi (saniye)
RATE_LIMIT_MAX: int = 10         # Pencere içinde maksimum istek
MAX_MESSAGE_SIZE: int = settings.WS_MAX_MESSAGE_SIZE  # Maksimum mesaj boyutu
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
    active_agents: Dict[str, Any] = field(default_factory=dict)  # Aktif agent'lar
    
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
                except Exception:
                    pass  # Ignore errors when closing old connection
            
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
        
        # 🔍 DEBUG: Log incoming chat request
        logger.info(f"📨 [CHAT DEBUG] Received chat request:")
        logger.info(f"   - session_id from frontend: {data.get('session_id')}")
        logger.info(f"   - effective session_id: {session_id}")
        logger.info(f"   - message preview: {message[:50]}...")
        logger.info(f"   - use_routing: {data.get('use_routing')}")
        
        # Model routing modu - frontend'den gelen use_routing parametresini kontrol et
        use_routing = data.get("use_routing", False)
        force_model = data.get("force_model")
        
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
        
        # use_routing=true ise model routing kullan, yoksa normal stream
        if use_routing:
            self._stream_task = asyncio.create_task(
                self._stream_routed_response(
                    message, session_id, use_routing, force_model,
                    web_search, complexity_level, response_mode
                )
            )
        else:
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
        
        # Yeni parametreler
        web_search = data.get("web_search", False)
        complexity_level = data.get("complexity_level", "auto")
        response_mode = data.get("response_mode", "normal")
        
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
            self._stream_routed_response(
                message, session_id, use_routing, force_model,
                web_search, complexity_level, response_mode
            )
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
        web_search: bool = False,
        complexity_level: str = "auto",
        response_mode: str = "normal",
    ) -> None:
        """
        Model routing ile streaming yanıt üret.
        
        Args:
            message: Kullanıcı mesajı
            session_id: Session ID
            use_routing: Model routing kullanılsın mı
            force_model: Zorla belirli model kullan
            web_search: Web araması yapılsın mı
            complexity_level: simple/normal/comprehensive/research
            response_mode: normal/analytical/creative/technical
        """
        stats = StreamStats(start_time=time.time())
        
        # Stream buffer'da yeni stream oluştur
        stream = stream_buffer.create_stream(session_id, message)
        stream_id = stream.stream_id
        self.conn.current_stream_id = stream_id
        
        try:
            model_router = get_model_router()
            
            # Başlangıç mesajı
            await self._send({
                "type": "start",
                "ts": int(time.time() * 1000),
                "session_id": session_id,
                "stream_id": stream_id,
            })
            
            # ⚡ Basit sorgu tespiti - ROUTING'DEN ÖNCE kontrol et (query_analyzer service)
            is_simple_query = query_analyzer.is_simple_query(message)
            
            # Complexity override - simple mode forced
            if complexity_level == "simple":
                is_simple_query = True
            elif complexity_level in ["comprehensive", "research"]:
                is_simple_query = False
            
            # === PHASE 1: ROUTING ===
            await self._send({
                "type": "status",
                "message": "⚡ Hızlı yanıt..." if is_simple_query else "Model seçiliyor...",
                "phase": "routing"
            })
            
            if force_model:
                # Zorla belirtilen model - 'small' veya 'large' string olarak gelebilir
                if force_model == "small":
                    actual_model = MODEL_CONFIG[ModelSize.SMALL]["name"]
                    model_size = "small"
                elif force_model == "large":
                    actual_model = MODEL_CONFIG[ModelSize.LARGE]["name"]
                    model_size = "large"
                else:
                    actual_model = force_model
                    model_size = "unknown"
                    
                routing_info = {
                    "model_name": actual_model,
                    "model_size": model_size,
                    "model_icon": MODEL_CONFIG.get(ModelSize.SMALL if model_size == "small" else ModelSize.LARGE, {}).get("icon", "🤖"),
                    "model_display_name": MODEL_CONFIG.get(ModelSize.SMALL if model_size == "small" else ModelSize.LARGE, {}).get("display_name", actual_model),
                    "decision_source": "forced",
                    "confidence": 1.0,
                    "response_id": str(uuid.uuid4()),
                }
            elif is_simple_query:
                # ⚡ Basit sorgular için routing atla, direkt small model
                routing_info = {
                    "model_name": MODEL_CONFIG[ModelSize.SMALL]["name"],
                    "model_size": "small",
                    "model_icon": MODEL_CONFIG[ModelSize.SMALL]["icon"],
                    "model_display_name": MODEL_CONFIG[ModelSize.SMALL]["display_name"],
                    "decision_source": "simple_query_bypass",
                    "confidence": 1.0,
                    "response_id": str(uuid.uuid4()),
                    "reasoning": "Basit sorgu - hızlı yanıt modu"
                }
            elif use_routing:
                # Model router kullan
                routing_result = await model_router.route_async(message)
                routing_info = routing_result.to_dict()
            else:
                # Default small model
                routing_info = {
                    "model_name": MODEL_CONFIG[ModelSize.SMALL]["name"],
                    "model_size": "small",
                    "decision_source": "default",
                    "confidence": 1.0,
                    "response_id": str(uuid.uuid4()),
                }
            
            # Routing bilgisini gönder
            await self._send({
                "type": "routing",
                "routing_info": routing_info,
                "timestamp": datetime.now().isoformat()
            })
            
            model_name = routing_info["model_name"]
            response_id = routing_info.get("response_id", str(uuid.uuid4()))
            
            # === RAG ARAŞI (Karmaşık sorgular için) ===
            knowledge_context = ""
            sources = []
            web_context = ""
            web_sources = []
            
            # === PREMIUM: MoE Router - Sorgu Analizi ===
            moe_analysis = None
            selected_expert = None
            if MOE_AVAILABLE and moe_query_analyzer and not is_simple_query and feature_enabled('moe_router'):
                try:
                    moe_analysis = moe_query_analyzer.analyze(message)
                    routing_decision = moe_router.route(message)
                    selected_expert = routing_decision.selected_expert
                    
                    # MoE bilgisini gönder
                    await self._send({
                        "type": "moe_routing",
                        "complexity": moe_analysis.complexity.value if moe_analysis else "unknown",
                        "expert": selected_expert.value if selected_expert else "default",
                        "confidence": routing_decision.confidence if routing_decision else 0.5,
                        "reasoning": routing_decision.reasoning if routing_decision else ""
                    })
                    logger.info(f"🔀 MoE: {moe_analysis.complexity.value if moe_analysis else 'N/A'} -> {selected_expert}")
                except Exception as e:
                    logger.warning(f"MoE analysis error: {e}")
            
            # === PREMIUM: MemGPT Memory - Konuşma Geçmişi ===
            memory_context = ""
            if MEMGPT_AVAILABLE and memory_manager and session_id and feature_enabled('memgpt_memory'):
                try:
                    # Session için bellek getir
                    relevant_memories = memory_manager.recall(
                        query=message,
                        session_id=session_id,
                        limit=5
                    )
                    if relevant_memories:
                        memory_parts = []
                        for mem in relevant_memories:
                            memory_parts.append(f"[Önceki Konuşma]: {mem.content[:300]}")
                        memory_context = "\n".join(memory_parts)
                        logger.info(f"🧠 MemGPT: {len(relevant_memories)} ilgili bellek bulundu")
                except Exception as e:
                    logger.warning(f"MemGPT recall error: {e}")
            
            if is_simple_query:
                # === PHASE 2: SEARCH (skipped) ===
                await self._send({
                    "type": "status",
                    "message": "⚡ Atlandı",
                    "phase": "search"
                })
                # === PHASE 3: ANALYZE (skipped) ===
                await self._send({
                    "type": "status",
                    "message": "⚡ Atlandı",
                    "phase": "analyze"
                })
            else:
                # === PHASE 2: SEARCH ===
                await self._send({
                    "type": "status",
                    "message": "Bilgi tabanı aranıyor...",
                    "phase": "search"
                })
                
                # === PREMIUM CRAG: Query Transformation ===
                search_message = message
                query_variations = [message]
                crag_metadata = {}
                
                if CRAG_AVAILABLE and query_transformer and complexity_level in ["comprehensive", "research"] and feature_enabled('crag_full'):
                    try:
                        # Sorguyu analiz et ve dönüştür
                        transformed = query_transformer.transform(message)
                        if transformed and transformed.reformulated != message:
                            search_message = transformed.reformulated
                            query_variations = [message, transformed.reformulated]
                            if transformed.sub_queries:
                                query_variations.extend(transformed.sub_queries[:3])
                            
                            crag_metadata["original_query"] = message
                            crag_metadata["transformed_query"] = transformed.reformulated
                            crag_metadata["sub_queries"] = transformed.sub_queries[:3] if transformed.sub_queries else []
                            
                            await self._send({
                                "type": "crag_transform",
                                "original": message,
                                "transformed": transformed.reformulated,
                                "sub_queries": transformed.sub_queries[:3] if transformed.sub_queries else []
                            })
                            logger.info(f"🔄 CRAG: Query transformed -> {len(query_variations)} variations")
                    except Exception as e:
                        logger.warning(f"CRAG transform error: {e}")
                
                # RAG Search - rag_service ile CRAG entegrasyonu
                try:
                    # Arama sonuç sayısını complexity'ye göre ayarla - PREMIUM: Daha fazla sonuç
                    n_results = 5 if complexity_level == "normal" else 10 if complexity_level == "comprehensive" else 15
                    score_threshold = 0.2 if complexity_level in ["comprehensive", "research"] else 0.3
                    
                    # Use rag_service if available (with CRAG), fallback to direct vector_store
                    if rag_service and SERVICES_AVAILABLE:
                        # Use CRAG for comprehensive/research queries
                        if complexity_level in ["comprehensive", "research"]:
                            enriched_context = await rag_service.search_with_crag(
                                query=search_message,
                                include_web=web_search,
                            )
                        else:
                            enriched_context = await rag_service.search(
                                query=search_message,
                                include_documents=True,
                                include_web=False,
                                n_results=n_results,
                                score_threshold=score_threshold,
                            )
                        
                        # Extract results from enriched context
                        if enriched_context.document_context:
                            knowledge_context = enriched_context.document_context
                        
                        # Convert to frontend sources format
                        for src in enriched_context.document_sources:
                            sources.append(src.to_frontend_format())
                        
                        # Web sources (if CRAG included them)
                        for src in enriched_context.web_sources:
                            web_sources.append(src.to_frontend_format())
                        
                        if enriched_context.web_context:
                            web_context = enriched_context.web_context
                        
                        # === PREMIUM CRAG: Relevance Grading ===
                        if CRAG_AVAILABLE and relevance_grader and sources and feature_enabled('crag_full'):
                            try:
                                graded_sources = []
                                high_relevance_count = 0
                                
                                for src in sources:
                                    grade = relevance_grader.grade(
                                        query=message,
                                        document=src.get("snippet", ""),
                                        metadata=src
                                    )
                                    src["relevance_grade"] = grade.grade.value
                                    src["relevance_score"] = grade.score
                                    graded_sources.append(src)
                                    
                                    if grade.grade in [RelevanceGrade.HIGHLY_RELEVANT, RelevanceGrade.RELEVANT]:
                                        high_relevance_count += 1
                                
                                sources = sorted(graded_sources, key=lambda x: x.get("relevance_score", 0), reverse=True)
                                crag_metadata["graded_sources"] = len(graded_sources)
                                crag_metadata["high_relevance"] = high_relevance_count
                                
                                logger.info(f"⭐ CRAG Grading: {high_relevance_count}/{len(sources)} highly relevant")
                            except Exception as e:
                                logger.warning(f"CRAG grading error: {e}")
                    else:
                        # Fallback: use direct vector_store with multiple queries
                        all_results = []
                        seen_docs = set()
                        
                        for q_var in query_variations[:3]:
                            results = vector_store.search_with_scores(
                                query=q_var, 
                                n_results=n_results, 
                                score_threshold=score_threshold
                            )
                            if results:
                                for r in results:
                                    doc_id = hash(r.get('document', '')[:100])
                                    if doc_id not in seen_docs:
                                        seen_docs.add(doc_id)
                                        all_results.append(r)
                        
                        if all_results:
                            # En iyi 30 sonucu al
                            all_results = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)[:30]
                            
                            knowledge_context = "\n\n".join([
                                f"[Kaynak: {r.get('metadata', {}).get('filename', 'unknown')}]\n{r.get('document', '')}"
                                for r in all_results
                            ])
                            
                            # Frontend için sources formatı
                            for r in all_results:
                                meta = r.get('metadata', {})
                                doc_text = r.get('document', '')[:200]
                                sources.append({
                                    "title": meta.get('filename', 'Kaynak'),
                                    "url": meta.get('source', '#'),
                                    "domain": "📄 Yerel Dosya",
                                    "snippet": doc_text,
                                    "type": "document",
                                    "reliability": r.get('score', 0.5),
                                })
                except Exception as e:
                    logger.warning(f"RAG search error: {e}")
                
                # === WEB SEARCH (if enabled) ===
                if web_search and web_search_engine:
                    await self._send({
                        "type": "status",
                        "message": "🌐 Web'de aranıyor...",
                        "phase": "search"
                    })
                    
                    try:
                        import asyncio
                        
                        # === PREMIUM: Semantic Query Expansion ===
                        search_queries = [message]  # Ana sorgu
                        if semantic_query_expander and feature_enabled('semantic_expansion'):
                            try:
                                expansion_result = await semantic_query_expander.expand_query(message, max_variations=5)
                                if expansion_result and expansion_result.expanded_queries:
                                    search_queries = [eq.query for eq in expansion_result.expanded_queries[:5]]
                                    if message not in search_queries:
                                        search_queries.insert(0, message)
                                    logger.info(f"🔄 Query expanded to {len(search_queries)} variations")
                            except Exception as e:
                                logger.warning(f"Query expansion error: {e}")
                        
                        # Tüm sorgular için paralel search
                        all_web_results = []
                        seen_urls = set()
                        
                        for query in search_queries:
                            loop = asyncio.get_event_loop()
                            web_response = await loop.run_in_executor(
                                None, 
                                lambda q=query: web_search_engine.search(
                                    query=q,
                                    num_results=15 if len(search_queries) > 1 else 30,
                                    extract_content=True,
                                    include_wikipedia=True
                                )
                            )
                            
                            if web_response and web_response.results:
                                for wr in web_response.results:
                                    if wr.url not in seen_urls:
                                        seen_urls.add(wr.url)
                                        all_web_results.append(wr)
                        
                        if all_web_results:
                            # Web context oluştur - Premium: 30 kaynak
                            web_parts = []
                            for i, wr in enumerate(all_web_results[:30]):
                                # Her kaynak için daha fazla content
                                content_preview = wr.full_content[:1500] if wr.full_content else wr.snippet or ''
                                web_parts.append(f"[Web Kaynak {i+1}: {wr.title}]\nURL: {wr.url}\n{content_preview}")
                                
                                # Frontend için web source formatı
                                web_sources.append({
                                    "title": wr.title,
                                    "url": wr.url,
                                    "domain": f"🌐 {wr.domain}",
                                    "snippet": wr.snippet or wr.full_content[:200] if wr.full_content else "",
                                    "type": "web",
                                    "reliability": wr.reliability_score if hasattr(wr, 'reliability_score') else 0.6,
                                })
                            
                            web_context = "\n\n".join(web_parts)
                            logger.info(f"🌐 Web search: {len(all_web_results)} sonuç bulundu ({len(search_queries)} sorgu)")
                            
                            # === PREMIUM: Smart Title Generator ===
                            if smart_title_generator and web_sources and feature_enabled('smart_titles'):
                                try:
                                    improved_sources = []
                                    for src in web_sources:
                                        result = smart_title_generator.generate_title_sync(
                                            url=src["url"],
                                            raw_title=src["title"],
                                            query=message,
                                            content_snippet=src.get("snippet", "")
                                        )
                                        src["title"] = result.smart_title
                                        improved_sources.append(src)
                                    web_sources = improved_sources
                                    logger.info(f"📝 Titles improved for {len(web_sources)} sources")
                                except Exception as e:
                                    logger.warning(f"Smart title generator error: {e}")
                            
                            # === PREMIUM: Source Quality Scorer ===
                            if source_quality_scorer and web_sources and feature_enabled('source_scoring'):
                                try:
                                    scored_sources = source_quality_scorer.rank_sources(
                                        sources=web_sources,
                                        query=message,
                                        top_k=50
                                    )
                                    web_sources = scored_sources
                                    logger.info(f"⭐ Sources ranked by quality")
                                except Exception as e:
                                    logger.warning(f"Source quality scorer error: {e}")
                    except Exception as e:
                        logger.warning(f"Web search error: {e}")
                
                # Tüm kaynakları birleştir
                all_sources = sources + web_sources
                
                # === PHASE 3: ANALYZE ===
                if all_sources:
                    doc_count = len(sources)
                    web_count = len(web_sources)
                    status_msg = []
                    if doc_count > 0:
                        status_msg.append(f"📄 {doc_count} dosya")
                    if web_count > 0:
                        status_msg.append(f"🌐 {web_count} web")
                    
                    await self._send({
                        "type": "status",
                        "message": f"{' + '.join(status_msg)} bulundu, analiz ediliyor...",
                        "phase": "analyze"
                    })
                    
                    # Kaynakları buffer'a ve frontend'e gönder
                    stream_buffer.set_sources(stream_id, all_sources[:50])
                    await self._send({
                        "type": "sources",
                        "sources": all_sources[:50]
                    })
                else:
                    await self._send({
                        "type": "status",
                        "message": "Genel bilgi kullanılacak",
                        "phase": "analyze"
                    })
            
            # === PHASE 4: CONTEXT ===
            await self._send({
                "type": "status",
                "message": "⚡ Hazır" if is_simple_query else "Bağlam hazırlanıyor...",
                "phase": "context"
            })
            
            # === PHASE 5: GENERATE ===
            await self._send({
                "type": "status",
                "message": "⚡ Hızlı yanıt..." if is_simple_query else "Yanıt üretiliyor...",
                "phase": "generate"
            })
            
            # LLM'DEN STREAMING YANIT
            from core.system_knowledge import SELF_KNOWLEDGE_PROMPT
            
            # Sistem hakkında mı soruyor kontrolü (query_analyzer service)
            is_about_system = query_analyzer.analyze(message).is_system_query
            
            # System prompt oluştur - PREMIUM EDUCATOR MODE
            if is_simple_query and not is_about_system:
                system_prompt = """Sen yardımcı ve öğretici bir AI asistanısın. Kısa ama bilgilendirici yanıtlar ver."""
            elif is_about_system:
                system_prompt = SELF_KNOWLEDGE_PROMPT
            else:
                # Karmaşık sorgular için PREMIUM EDUCATOR PROMPT
                system_prompt = """Sen dünya standartlarında bir AI Eğitmenisin. Görevin kullanıcıya konuyu GERÇEKTEN ÖĞRETMEK.

## TEMEL PRENSİPLER:
1. **Derinlemesine Açıklama**: Her kavramı "neden" ve "nasıl" boyutlarıyla açıkla
2. **Pratik Örnekler**: Soyut kavramları somut örneklerle destekle
3. **Kod Öğretimi**: Sadece kod gösterme - her satırı açıkla, alternatiflerini sun
4. **Kritik Noktalar**: Yaygın hatalar, best practice'ler ve edge case'leri vurgula
5. **Bağlam**: Konunun büyük resimde nereye oturduğunu açıkla

## YANITLAMA FORMATI:
### 📚 Konu Başlığı
- Konunun tanımı ve önemi
- Neden öğrenilmeli?

### 🎯 Temel Kavramlar
- Her kavram detaylı açıklama ile
- Gerçek dünya analojileri

### 💻 Kod Örnekleri (varsa)
```language
# Her satır için yorum
code_line  # Bu ne yapıyor ve NEDEN
```
**Kod Açıklaması:**
- Satır satır ne yaptığını açıkla
- Alternatif yaklaşımları belirt
- Yaygın hataları ve çözümlerini göster

### ⚠️ Dikkat Edilmesi Gerekenler
- Yaygın hatalar ve nasıl kaçınılır
- Best practice'ler
- Edge case'ler

### 🔗 İlişkili Konular
- Bu konuyla bağlantılı kavramlar
- Sonraki öğrenme adımları

### 📝 Özet
- Kilit noktaların listesi
"""
                
                # Response mode'a göre ek talimatlar
                if response_mode == "analytical":
                    system_prompt += "\n\n## EXTRA: ANALİTİK MOD\n- Karşılaştırmalı analiz yap\n- Avantaj/dezavantaj tabloları kullan\n- Metrikler ve ölçütlerle destekle"
                elif response_mode == "creative":
                    system_prompt += "\n\n## EXTRA: YARATICI MOD\n- Farklı perspektifler sun\n- İlham verici örnekler kullan\n- Benzersiz çözümler öner"
                elif response_mode == "technical":
                    system_prompt += "\n\n## EXTRA: TEKNİK MOD\n- Low-level detaylar ver\n- Performans optimizasyonlarını açıkla\n- Mimari kararları tartış"
                elif response_mode == "debate":
                    system_prompt += "\n\n## EXTRA: TARTIŞMA MOD\n- Farklı bakış açılarını sun\n- Her görüşün güçlü/zayıf yanlarını analiz et\n- Sonunda dengeli bir sonuç çıkar"
            
            # === PREMIUM: Multi-Agent Debate (Research Mode) ===
            debate_result = None
            if DEBATE_AVAILABLE and debate_orchestrator and complexity_level == "research" and response_mode in ["debate", "analytical"] and feature_enabled('multi_agent_debate'):
                try:
                    await self._send({
                        "type": "status",
                        "message": "🤖 Multi-agent tartışma başlıyor...",
                        "phase": "debate"
                    })
                    
                    # LLM factory for debate agents
                    def create_debate_llm():
                        def llm_fn(prompt):
                            import asyncio
                            loop = asyncio.get_event_loop()
                            result = loop.run_until_complete(
                                llm_manager.generate_async(prompt, system_prompt="You are a debate participant.", temperature=0.7)
                            )
                            return result
                        return llm_fn
                    
                    # Run multi-agent debate
                    from core.multi_agent_debate import multi_agent_debate
                    debate_result = await multi_agent_debate(
                        question=message,
                        llm=create_debate_llm(),
                        context=knowledge_context + "\n\n" + web_context if (knowledge_context or web_context) else "",
                        num_agents=3,
                        max_rounds=2
                    )
                    
                    if debate_result:
                        # Debate sonuçlarını system prompt'a ekle
                        system_prompt += f"""

## 🤖 MULTI-AGENT DEBATE SONUÇLARI
**Konsensüs Seviyesi:** {debate_result.consensus_level:.0%}
**Kazanan Pozisyon:** {debate_result.winning_position}
**Güven:** {debate_result.confidence:.0%}

Bu debate sonuçlarını kullanarak kapsamlı ve dengeli bir yanıt oluştur.
Farklı perspektifleri de yansıt."""
                        
                        await self._send({
                            "type": "debate_result",
                            "consensus": debate_result.consensus_level,
                            "winning_position": debate_result.winning_position,
                            "confidence": debate_result.confidence,
                            "dissenting_views": debate_result.dissenting_views if hasattr(debate_result, 'dissenting_views') else []
                        })
                        logger.info(f"🤖 Debate completed: consensus={debate_result.consensus_level:.0%}")
                except Exception as e:
                    logger.warning(f"Multi-agent debate error: {e}")
            
            # === PREMIUM: Response Length Manager ===
            if response_length_manager and not is_simple_query and feature_enabled('response_length'):
                try:
                    # Sorgu için uygun yanıt modunu belirle
                    source_count = len(sources) + len(web_sources) if 'sources' in dir() else 0
                    suggested_mode = response_length_manager.suggest_mode_for_query(message, source_count)
                    
                    # System prompt'a uzunluk talimatları ekle
                    length_enhancement = response_length_manager.get_system_prompt_enhancement(suggested_mode, source_count)
                    system_prompt += f"\n\n{length_enhancement}"
                    logger.info(f"📏 Response mode: {suggested_mode}, sources: {source_count}")
                except Exception as e:
                    logger.warning(f"Response length manager error: {e}")
            
            # RAG context ve web context'i prompt'a ekle
            final_prompt = message
            has_doc_sources = bool(knowledge_context)
            has_web_sources = bool(web_context)
            
            if has_doc_sources or has_web_sources:
                context_parts = []
                
                if has_doc_sources:
                    context_parts.append(f"""=== 📄 DOSYA KAYNAKLARI ===
{knowledge_context}
=== DOSYA KAYNAKLARI SONU ===""")
                
                if has_web_sources:
                    context_parts.append(f"""=== 🌐 WEB KAYNAKLARI ===
{web_context}
=== WEB KAYNAKLARI SONU ===""")
                
                combined_context = "\n\n".join(context_parts)
                
                final_prompt = f"""## 📚 ARAŞTIRMA KAYNAKLARI
{combined_context}

## ❓ KULLANICI SORUSU
{message}

## 📝 YANITLAMA TALİMATLARI

### Kaynak Kullanımı:
- Yukarıdaki kaynaklardan BİLGİ SENTEZİ yap - sadece kopyalama değil
- Her kaynaktan aldığın bilgiyi kendi cümlelerinle açıkla
- Farklı kaynaklardan gelen bilgileri birleştirerek kapsamlı yanıt oluştur

### Format Gereksinimleri:
1. **Giriş**: Konunun ne olduğunu ve neden önemli olduğunu açıkla
2. **Ana İçerik**: Konuyu sistematik ve detaylı işle
   - Her kavramı derinlemesine açıkla (sadece tanım değil, NEDEN ve NASIL)
   - Kod varsa: Her satırı açıkla, alternatiflerini göster, yaygın hataları belirt
   - Pratik örnekler ve analojiler kullan
3. **Kritik Noktalar**: Dikkat edilmesi gerekenler, yaygın hatalar, best practice'ler
4. **Özet**: Kilit noktaları listele

### Uzunluk:
- KAPSAMLI ve DETAYLI yanıt ver - kısa kesme
- Her önemli kavramı tam olarak açıkla, yüzeysel geçme
- Minimum 1500 kelime hedefle (karmaşık konularda daha fazla)

### Kaynak Gösterimi:
- Yanıtın sonunda kullanılan web kaynaklarını listele:
  🔗 **Kaynaklar:**
  - [Kaynak Adı](URL)"""
            elif not is_simple_query:
                # Kaynak yok ama karmaşık sorgu - genel bilgi kullan
                final_prompt = f"""{message}

NOT: Bu soru için bilgi tabanında veya web'de spesifik kaynak bulunamadı. 
Lütfen genel bilginle kapsamlı yanıt ver ve yanıtının başına "💡 Genel Bilgi:" ekle."""
            
            full_response = ""
            token_index = 0
            
            # DEBUG: LLM streaming başlıyor
            logger.info(f"🚀 LLM STREAMING BAŞLIYOR: model={model_name}, prompt_len={len(final_prompt)}")
            
            thinking_content = ""  # AI düşünce sürecini biriktir
            
            async with asyncio_timeout(STREAM_TIMEOUT):
                async for chunk_data in llm_manager.generate_stream_async(
                    prompt=final_prompt,
                    system_prompt=system_prompt,
                    temperature=0.7 if response_mode != "analytical" else 0.4,
                    model=model_name,
                ):
                    # DEBUG: Her chunk'ta log
                    if token_index == 0:
                        logger.info(f"✅ İLK CHUNK GELDİ: {type(chunk_data)}")
                    
                    # Stop kontrolü
                    if self.conn.stop_flag or stream_buffer.is_stop_requested(stream_id):
                        stats.was_stopped = True
                        stream_buffer.stop_stream(stream_id)
                        break
                    
                    if chunk_data:
                        # Dict format: {"type": "content"|"thinking", "content": "..."}
                        if isinstance(chunk_data, dict):
                            chunk_type = chunk_data.get("type", "content")
                            chunk_content = chunk_data.get("content", "")
                            
                            if chunk_type == "thinking":
                                # Thinking content - ayrı mesaj olarak gönder
                                thinking_content += chunk_content
                                await self._send({
                                    "type": "thinking",
                                    "content": chunk_content,
                                    "index": token_index
                                })
                                token_index += 1
                            else:
                                # Normal content
                                stats.token_count += 1
                                stats.char_count += len(chunk_content)
                                full_response += chunk_content
                                
                                # Token'ı buffer'a kaydet
                                token = stream_buffer.add_token(stream_id, chunk_content)
                                
                                # ANLIK gönder
                                await self._send({
                                    "type": "chunk",
                                    "content": chunk_content,
                                    "index": token.index if token else token_index
                                })
                                token_index += 1
                        else:
                            # Backward compatibility - string
                            chunk = str(chunk_data)
                            stats.token_count += 1
                            stats.char_count += len(chunk)
                            full_response += chunk
                            
                            token = stream_buffer.add_token(stream_id, chunk)
                            await self._send({
                                "type": "chunk",
                                "content": chunk,
                                "index": token.index if token else token_index
                            })
                            token_index += 1
            
            stats.end_time = time.time()
            self.conn.total_tokens += stats.token_count
            
            # === PREMIUM: Hallucination Detection ===
            hallucination_risk = "low"
            if CRAG_AVAILABLE and hallucination_detector and full_response and (sources or web_sources) and feature_enabled('crag_full'):
                try:
                    all_contexts = []
                    for src in sources[:10]:
                        all_contexts.append(src.get("snippet", ""))
                    for src in web_sources[:10]:
                        all_contexts.append(src.get("snippet", ""))
                    
                    if all_contexts:
                        risk = hallucination_detector.detect(
                            answer=full_response,
                            contexts=all_contexts,
                            query=message
                        )
                        hallucination_risk = risk.risk_level.value if risk else "unknown"
                        
                        if risk and risk.risk_level in [HallucinationRisk.HIGH, HallucinationRisk.CRITICAL]:
                            await self._send({
                                "type": "hallucination_warning",
                                "risk": hallucination_risk,
                                "confidence": risk.confidence if risk else 0,
                                "message": "⚠️ Yanıt kaynaklarla tam uyumlu olmayabilir"
                            })
                        logger.info(f"🔍 Hallucination check: {hallucination_risk}")
                except Exception as e:
                    logger.warning(f"Hallucination detection error: {e}")
            
            # === PREMIUM: RAGAS Evaluation ===
            ragas_score = None
            if RAGAS_AVAILABLE and ragas_evaluator and full_response and not is_simple_query and feature_enabled('ragas_evaluation'):
                try:
                    contexts = [src.get("snippet", "") for src in (sources + web_sources)[:15]]
                    if contexts:
                        eval_result = await ragas_evaluator.evaluate_async(
                            question=message,
                            answer=full_response,
                            contexts=contexts
                        )
                        if eval_result:
                            ragas_score = eval_result.overall_score
                            await self._send({
                                "type": "quality_score",
                                "overall": ragas_score,
                                "faithfulness": eval_result.metrics.get(MetricType.FAITHFULNESS, {}).score if hasattr(eval_result, 'metrics') else None,
                                "relevancy": eval_result.metrics.get(MetricType.ANSWER_RELEVANCY, {}).score if hasattr(eval_result, 'metrics') else None
                            })
                            logger.info(f"📊 RAGAS score: {ragas_score:.2f}")
                except Exception as e:
                    logger.warning(f"RAGAS evaluation error: {e}")
            
            # === PREMIUM: MemGPT Memory - Konuşmayı Kaydet ===
            if MEMGPT_AVAILABLE and memory_manager and session_id and full_response and feature_enabled('memgpt_memory'):
                try:
                    # Konuşmayı working memory'ye kaydet
                    memory_manager.store(
                        content=f"User: {message}\nAssistant: {full_response[:500]}",
                        session_id=session_id,
                        memory_type=MemoryType.WORKING,
                        priority=MemoryPriority.MEDIUM
                    )
                    
                    # Önemli bilgileri archival memory'ye taşı (uzun yanıtlar için)
                    if len(full_response) > 1000 and not is_simple_query:
                        memory_manager.consolidate(session_id=session_id)
                    
                    logger.info(f"🧠 MemGPT: Conversation stored")
                except Exception as e:
                    logger.warning(f"MemGPT store error: {e}")
            
            # === PHASE 6: COMPLETE ===
            await self._send({
                "type": "status",
                "message": "Tamamlandı",
                "phase": "complete"
            })
            
            # BİTİŞ
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
                    "response_id": response_id,
                    "model_info": routing_info,
                    "stats": stats.to_dict(),
                    "ts": int(time.time() * 1000),
                    "stream_id": stream_id,
                })
            
            # Session'a kaydet
            logger.info(f"🔍 [SESSION DEBUG] About to save session:")
            logger.info(f"   - session_id: {session_id}")
            logger.info(f"   - full_response length: {len(full_response) if full_response else 0}")
            logger.info(f"   - message preview: {message[:50]}...")
            
            if full_response:
                try:
                    # Session yoksa oluştur - create_session_with_id kullan
                    logger.info(f"   - Checking if session exists...")
                    session = session_manager.get_session(session_id)
                    logger.info(f"   - Session found: {session is not None}")
                    
                    if not session:
                        # Yeni session oluştur - belirli ID ile
                        title = message[:50] if len(message) > 50 else message
                        session = session_manager.create_session_with_id(session_id, title=title)
                        logger.info(f"📝 Created new session with ID: {session_id}")
                    
                    logger.info(f"   - Adding user message...")
                    session_manager.add_message(session_id, "user", message)
                    saved_response = full_response
                    if stats.was_stopped:
                        saved_response += "\n\n*[Yanıt durduruldu]*"
                    logger.info(f"   - Adding assistant message...")
                    session_manager.add_message(session_id, "assistant", saved_response)
                    
                    # Verify save
                    updated_session = session_manager.get_session(session_id)
                    logger.info(f"✅ Session saved: {session_id}, messages: {len(updated_session.messages) if updated_session else 'N/A'}")
                    
                    # Check file exists
                    from core.config import settings
                    file_path = settings.DATA_DIR / "sessions" / f"{session_id}.json"
                    logger.info(f"   - File exists: {file_path.exists()}")
                    
                except Exception as e:
                    logger.error(f"❌ Session save error: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"⚠️ No full_response to save!")
            
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
            # === PHASE 1: ROUTING ===
            await self._send({
                "type": "status",
                "message": "Sorgu analiz ediliyor...",
                "phase": "routing"
            })
            
            # Basit sorgu tespiti (query_analyzer service kullanıyor)
            is_simple_greeting = query_analyzer.is_simple_query(message)
            is_short_query = len(message) < 25
            
            # Auto modda basit sorgular için otomatik simple mod kullan
            if complexity_level == "auto" and (is_simple_greeting or is_short_query):
                complexity_level = "simple"
            
            # ⚡ SIMPLE MOD: Ultra hızlı - RAG araması yapma, direkt LLM
            skip_rag = complexity_level == "simple"
            
            async with asyncio_timeout(STREAM_TIMEOUT):
                knowledge_context = ""
                sources = []
                
                # Simple modda RAG'ı atla - maksimum hız
                if not skip_rag:
                    # === PHASE 2: SEARCH ===
                    await self._send({
                        "type": "status",
                        "message": "Bilgi tabanı aranıyor...",
                        "phase": "search"
                    })
                    
                    # RAG search - use rag_service if available
                    try:
                        if rag_service and SERVICES_AVAILABLE:
                            enriched_context = await rag_service.search(
                                query=message,
                                include_documents=True,
                                include_web=False,
                                n_results=5,
                                score_threshold=0.3,
                            )
                            
                            if enriched_context.document_context:
                                knowledge_context = enriched_context.document_context
                            
                            for src in enriched_context.document_sources:
                                sources.append(src.to_frontend_format())
                        else:
                            # Fallback to direct vector_store
                            results = vector_store.search_with_scores(query=message, n_results=5, score_threshold=0.3)
                            if results:
                                knowledge_context = "\n\n".join([
                                    f"[Kaynak: {r.get('metadata', {}).get('filename', 'unknown')}]\n{r.get('document', '')}"
                                    for r in results[:3]
                                ])
                                for r in results:
                                    meta = r.get('metadata', {})
                                    doc_text = r.get('document', '')[:200]
                                    sources.append({
                                        "title": meta.get('filename', 'Kaynak'),
                                        "url": meta.get('source', '#'),
                                        "domain": "📄 Yerel Dosya",
                                        "snippet": doc_text,
                                        "type": "document",
                                        "reliability": r.get('score', 0.5),
                                    })
                    except Exception as e:
                        logger.warning(f"RAG search error: {e}")
                    
                # Kaynakları buffer'a kaydet
                if sources:
                    # === PHASE 3: ANALYZE ===
                    await self._send({
                        "type": "status",
                        "message": "Kaynaklar analiz ediliyor...",
                        "phase": "analyze"
                    })
                    
                    stream_buffer.set_sources(stream_id, sources[:30])
                    await self._send({
                        "type": "sources",
                        "sources": sources[:30]
                    })
                
                # === PHASE 4: CONTEXT ===
                await self._send({
                    "type": "status",
                    "message": "Bağlam hazırlanıyor...",
                    "phase": "context"
                })
                
                # === PHASE 5: GENERATE ===
                await self._send({
                    "type": "status",
                    "message": "Yanıt oluşturuluyor..." if not skip_rag else "⚡ Hızlı yanıt...",
                    "phase": "generate"
                })
                
                # System prompt oluştur
                from core.system_knowledge import SELF_KNOWLEDGE_PROMPT
                
                # Sistem hakkında mı soruyor kontrolü (query_analyzer service)
                is_about_system = query_analyzer.analyze(message).is_system_query
                
                if skip_rag and not is_about_system:
                    # Basit sorular için minimal sistem prompt
                    system_prompt = "Sen yardımcı bir AI asistanısın. Samimi ve kısa yanıt ver."
                elif is_about_system:
                    system_prompt = SELF_KNOWLEDGE_PROMPT
                else:
                    system_prompt = "Sen Enterprise AI Asistan'sın. Kullanıcının sorusuna odaklan ve yardımcı ol."
                
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
                
                # ⚡ Simple modda küçük model kullan - ultra hızlı
                selected_model = None
                if skip_rag:
                    # Basit sorgular için küçük model (qwen3:4b veya benzeri)
                    selected_model = MODEL_CONFIG[ModelSize.SMALL]["name"]
                
                # Streaming response - token'lar buffer'a kaydedilir
                full_response = ""
                token_index = 0
                async for chunk in llm_manager.generate_stream_async(
                    prompt=message,
                    system_prompt=system_prompt,
                    model=selected_model,  # Simple modda küçük model
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
                
                # === PHASE 6: COMPLETE ===
                await self._send({
                    "type": "status",
                    "message": "Tamamlandı",
                    "phase": "complete"
                })
                
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
                        # Session yoksa oluştur
                        if not session_manager.get_session(session_id):
                            title = message[:50] if len(message) > 50 else message
                            session_manager.create_session_with_id(session_id, title=title)
                            logger.info(f"📝 Created new session: {session_id}")
                        
                        session_manager.add_message(session_id, "user", message)
                        # Durdurulduysa yanıta işaret ekle
                        saved_response = full_response
                        if stats.was_stopped:
                            saved_response += "\n\n*[Yanıt durduruldu]*"
                        session_manager.add_message(session_id, "assistant", saved_response)
                        logger.info(f"✅ Session saved: {session_id}")
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
