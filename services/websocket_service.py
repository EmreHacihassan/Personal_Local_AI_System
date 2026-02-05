"""
Enterprise AI Assistant - WebSocket Service
=============================================

Merkezi WebSocket yardımcı servisi.
Mesaj formatları, faz yönetimi ve yardımcı fonksiyonlar.

Features:
- Standardized message types
- Pipeline phase management
- Message builders
- Connection utilities
- Error formatters

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class WSMessageType(str, Enum):
    """WebSocket mesaj tipleri."""
    # Connection
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PING = "ping"
    PONG = "pong"
    
    # Streaming
    START = "start"
    TOKEN = "token"
    CHUNK = "chunk"
    THINKING = "thinking"
    END = "end"
    STOPPED = "stopped"
    
    # Pipeline phases
    STATUS = "status"
    ROUTING = "routing"
    SOURCES = "sources"
    
    # Errors
    ERROR = "error"
    WARNING = "warning"
    
    # Model routing
    FEEDBACK_RECEIVED = "feedback_received"
    FEEDBACK_CONFIRMED = "feedback_confirmed"
    COMPARE_START = "compare_start"
    COMPARE_CHUNK = "compare_chunk"
    COMPARE_END = "compare_end"
    
    # Resume
    RESUME_DATA = "resume_data"


class WSPhase(str, Enum):
    """Pipeline fazları."""
    ROUTING = "routing"
    SEARCH = "search"
    ANALYZE = "analyze"
    CONTEXT = "context"
    GENERATE = "generate"
    COMPLETE = "complete"


class WSErrorCode(str, Enum):
    """Hata kodları."""
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    RATE_LIMIT = "rate_limit"
    INVALID_MESSAGE = "invalid_message"
    PROCESSING_ERROR = "processing_error"
    MODEL_ERROR = "model_error"
    RAG_ERROR = "rag_error"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class WSMessage:
    """WebSocket mesajı."""
    type: WSMessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            **self.data,
            "timestamp": self.timestamp,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class WSError:
    """WebSocket hatası."""
    code: WSErrorCode
    message: str
    details: Optional[str] = None
    recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "error",
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


@dataclass
class WSStatus:
    """Pipeline durum mesajı."""
    phase: WSPhase
    message: str
    progress: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": "status",
            "phase": self.phase.value,
            "message": self.message,
        }
        if self.progress is not None:
            result["progress"] = self.progress
        if self.metadata:
            result.update(self.metadata)
        return result


# =============================================================================
# MESSAGE BUILDERS
# =============================================================================

class MessageBuilder:
    """WebSocket mesaj oluşturucu."""
    
    @staticmethod
    def connected(
        client_id: str,
        features: List[str],
        models: List[Dict[str, Any]],
        version: str = "2.0",
    ) -> Dict[str, Any]:
        """Connection established mesajı."""
        return {
            "type": WSMessageType.CONNECTED.value,
            "version": version,
            "client_id": client_id,
            "features": features,
            "models": models,
            "ping_interval": settings.WS_PING_INTERVAL,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def start(
        stream_id: str,
        response_id: str,
        model_name: str,
    ) -> Dict[str, Any]:
        """Stream start mesajı."""
        return {
            "type": WSMessageType.START.value,
            "stream_id": stream_id,
            "response_id": response_id,
            "model": model_name,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def routing(
        model_name: str,
        model_size: str,
        confidence: float,
        decision_source: str,
        reasoning: str,
        response_id: str,
        model_icon: str = "🔵",
        model_display_name: str = "",
    ) -> Dict[str, Any]:
        """Model routing decision mesajı."""
        return {
            "type": WSMessageType.ROUTING.value,
            "model": model_name,
            "model_size": model_size,
            "model_icon": model_icon,
            "model_display_name": model_display_name or model_name,
            "confidence": confidence,
            "decision_source": decision_source,
            "reasoning": reasoning,
            "response_id": response_id,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def status(
        phase: WSPhase,
        message: str,
        progress: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Pipeline status mesajı."""
        result = {
            "type": WSMessageType.STATUS.value,
            "phase": phase.value,
            "message": message,
        }
        if progress is not None:
            result["progress"] = progress
        return result
    
    @staticmethod
    def sources(sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sources mesajı."""
        return {
            "type": WSMessageType.SOURCES.value,
            "sources": sources,
            "count": len(sources),
            "timestamp": time.time(),
        }
    
    @staticmethod
    def token(
        content: str,
        token_index: int,
        stream_id: str,
    ) -> Dict[str, Any]:
        """Token/chunk mesajı."""
        return {
            "type": WSMessageType.TOKEN.value,
            "content": content,
            "token_index": token_index,
            "stream_id": stream_id,
        }
    
    @staticmethod
    def thinking(content: str) -> Dict[str, Any]:
        """AI thinking mesajı."""
        return {
            "type": WSMessageType.THINKING.value,
            "content": content,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def end(
        stream_id: str,
        total_tokens: int,
        total_time_ms: float,
        model_name: str,
        response_id: str,
        finish_reason: str = "stop",
    ) -> Dict[str, Any]:
        """Stream end mesajı."""
        return {
            "type": WSMessageType.END.value,
            "stream_id": stream_id,
            "total_tokens": total_tokens,
            "tokens_per_second": round(total_tokens / (total_time_ms / 1000), 1) if total_time_ms > 0 else 0,
            "total_time_ms": round(total_time_ms, 1),
            "model": model_name,
            "response_id": response_id,
            "finish_reason": finish_reason,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def error(
        code: WSErrorCode,
        message: str,
        details: Optional[str] = None,
        recoverable: bool = True,
    ) -> Dict[str, Any]:
        """Error mesajı."""
        return {
            "type": WSMessageType.ERROR.value,
            "error_code": code.value,
            "message": message,
            "details": details,
            "recoverable": recoverable,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def pong() -> Dict[str, Any]:
        """Pong mesajı."""
        return {
            "type": WSMessageType.PONG.value,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def stopped(stream_id: str, reason: str = "user_request") -> Dict[str, Any]:
        """Stream stopped mesajı."""
        return {
            "type": WSMessageType.STOPPED.value,
            "stream_id": stream_id,
            "reason": reason,
            "timestamp": time.time(),
        }
    
    @staticmethod
    def feedback_received(
        feedback_id: str,
        feedback_type: str,
        response_id: str,
    ) -> Dict[str, Any]:
        """Feedback received mesajı."""
        return {
            "type": WSMessageType.FEEDBACK_RECEIVED.value,
            "feedback_id": feedback_id,
            "feedback_type": feedback_type,
            "response_id": response_id,
            "timestamp": time.time(),
        }


# =============================================================================
# WEBSOCKET SERVICE
# =============================================================================

class WebSocketService:
    """
    Merkezi WebSocket servisi.
    
    Mesaj oluşturma, faz yönetimi ve yardımcı fonksiyonlar.
    """
    
    def __init__(self):
        """Initialize WebSocket service."""
        self.message_builder = MessageBuilder()
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors_sent": 0,
        }
    
    def get_ws_url(self, path: str) -> str:
        """Get WebSocket URL for a path."""
        return settings.get_ws_url(path)
    
    def get_features_list(self) -> List[str]:
        """Get available features list."""
        return [
            "streaming",
            "model_routing",
            "sources",
            "feedback",
            "comparison",
            "resume",
            "thinking_mode",
            "web_search",
        ]
    
    def get_models_list(self) -> List[Dict[str, Any]]:
        """Get available models list."""
        config = settings.get_model_routing_config()
        return [
            {
                "name": info["name"],
                "display_name": info["display_name"],
                "icon": info["icon"],
                "description": info["description"],
                "size": size.value,
            }
            for size, info in config.items()
        ]
    
    def build_connected_message(self, client_id: str) -> Dict[str, Any]:
        """Build connected message."""
        self._stats["messages_sent"] += 1
        return self.message_builder.connected(
            client_id=client_id,
            features=self.get_features_list(),
            models=self.get_models_list(),
        )
    
    def build_status_message(
        self,
        phase: WSPhase,
        message: str,
        progress: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Build status message."""
        self._stats["messages_sent"] += 1
        return self.message_builder.status(phase, message, progress)
    
    def build_error_message(
        self,
        code: WSErrorCode,
        message: str,
        details: Optional[str] = None,
        recoverable: bool = True,
    ) -> Dict[str, Any]:
        """Build error message."""
        self._stats["errors_sent"] += 1
        return self.message_builder.error(code, message, details, recoverable)
    
    def parse_client_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """Parse client message."""
        try:
            self._stats["messages_received"] += 1
            data = json.loads(raw_message)
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON message: {e}")
            return None
    
    def get_phase_order(self) -> List[WSPhase]:
        """Get pipeline phase order."""
        return [
            WSPhase.ROUTING,
            WSPhase.SEARCH,
            WSPhase.ANALYZE,
            WSPhase.CONTEXT,
            WSPhase.GENERATE,
            WSPhase.COMPLETE,
        ]
    
    def get_stats(self) -> Dict[str, int]:
        """Get service statistics."""
        return self._stats.copy()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

ws_service = WebSocketService()
