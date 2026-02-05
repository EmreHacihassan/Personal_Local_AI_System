"""
Enterprise AI Assistant - Notifications Router
===============================================

Real-time bildirim sistemi.
WebSocket ve HTTP endpoints ile bildirim yönetimi.

Features:
- WebSocket notifications endpoint
- Notification broadcasting
- Notification history
- Read/unread status
- Priority levels

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketState

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# =============================================================================
# ENUMS & MODELS
# =============================================================================

class NotificationPriority(str, Enum):
    """Bildirim öncelik seviyesi."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Bildirim tipi."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    TASK = "task"
    DOCUMENT = "document"
    AGENT = "agent"


@dataclass
class Notification:
    """Bildirim veri yapısı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.INFO
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    read: bool = False
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "read": self.read,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


class NotificationCreate(BaseModel):
    """Bildirim oluşturma modeli."""
    type: str = Field(default="info")
    priority: str = Field(default="normal")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    data: Dict[str, Any] = Field(default_factory=dict)
    expires_in_seconds: Optional[int] = Field(default=None, ge=1)


class NotificationResponse(BaseModel):
    """Bildirim yanıt modeli."""
    success: bool
    notification_id: Optional[str] = None
    message: str = ""


# =============================================================================
# NOTIFICATION MANAGER
# =============================================================================

class NotificationManager:
    """
    Merkezi bildirim yöneticisi.
    
    WebSocket bağlantılarını ve bildirim geçmişini yönetir.
    """
    
    def __init__(self):
        """Initialize notification manager."""
        self._connections: Dict[str, WebSocket] = {}
        self._notifications: List[Notification] = []
        self._max_history = 100
        self._lock = asyncio.Lock()
        self._stats = {
            "total_sent": 0,
            "total_broadcasts": 0,
            "active_connections": 0,
        }
    
    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """Register new WebSocket connection."""
        await websocket.accept()
        
        async with self._lock:
            self._connections[client_id] = websocket
            self._stats["active_connections"] = len(self._connections)
        
        logger.info(f"Notification client connected: {client_id}")
        
        # Send connection confirmation
        await self._send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": time.time(),
        })
        
        # Send unread notifications
        unread = [n.to_dict() for n in self._notifications if not n.read]
        if unread:
            await self._send_to_client(client_id, {
                "type": "history",
                "notifications": unread[:20],
                "unread_count": len(unread),
            })
    
    async def disconnect(self, client_id: str) -> None:
        """Remove WebSocket connection."""
        async with self._lock:
            if client_id in self._connections:
                del self._connections[client_id]
                self._stats["active_connections"] = len(self._connections)
        
        logger.info(f"Notification client disconnected: {client_id}")
    
    async def broadcast(self, notification: Notification) -> int:
        """Broadcast notification to all connected clients."""
        self._stats["total_broadcasts"] += 1
        
        # Store in history
        self._notifications.append(notification)
        if len(self._notifications) > self._max_history:
            self._notifications = self._notifications[-self._max_history:]
        
        # Broadcast
        sent_count = 0
        disconnected = []
        
        async with self._lock:
            for client_id, ws in self._connections.items():
                try:
                    if ws.client_state == WebSocketState.CONNECTED:
                        await ws.send_json({
                            "type": "notification",
                            "notification": notification.to_dict(),
                        })
                        sent_count += 1
                        self._stats["total_sent"] += 1
                except Exception as e:
                    logger.warning(f"Failed to send to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Cleanup disconnected
        for client_id in disconnected:
            await self.disconnect(client_id)
        
        return sent_count
    
    async def send_to_client(self, client_id: str, notification: Notification) -> bool:
        """Send notification to specific client."""
        return await self._send_to_client(client_id, {
            "type": "notification",
            "notification": notification.to_dict(),
        })
    
    async def _send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """Send data to specific client."""
        async with self._lock:
            ws = self._connections.get(client_id)
            if not ws:
                return False
            
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(data)
                    return True
            except Exception as e:
                logger.warning(f"Failed to send to {client_id}: {e}")
        
        return False
    
    def create_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None,
        expires_in_seconds: Optional[int] = None,
    ) -> Notification:
        """Create a new notification."""
        expires_at = None
        if expires_in_seconds:
            expires_at = time.time() + expires_in_seconds
        
        return Notification(
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            expires_at=expires_at,
        )
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        for n in self._notifications:
            if n.id == notification_id:
                n.read = True
                return True
        return False
    
    def get_unread_count(self) -> int:
        """Get unread notification count."""
        now = time.time()
        return sum(
            1 for n in self._notifications 
            if not n.read and (n.expires_at is None or n.expires_at > now)
        )
    
    def get_history(self, limit: int = 50, include_read: bool = True) -> List[Dict[str, Any]]:
        """Get notification history."""
        now = time.time()
        notifications = [
            n for n in self._notifications
            if (include_read or not n.read) and (n.expires_at is None or n.expires_at > now)
        ]
        return [n.to_dict() for n in notifications[-limit:]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            **self._stats,
            "history_size": len(self._notifications),
            "unread_count": self.get_unread_count(),
        }


# Singleton instance
notification_manager = NotificationManager()


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@router.websocket("/ws/{client_id}")
async def notifications_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time notifications.
    
    Protocol:
    - Server sends: connected, notification, history
    - Client sends: ping, mark_read, mark_all_read
    """
    await notification_manager.connect(client_id, websocket)
    
    try:
        while True:
            try:
                # Receive message
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=settings.WS_PING_INTERVAL + 5
                )
                
                msg_type = data.get("type", "")
                
                if msg_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": time.time(),
                    })
                
                elif msg_type == "mark_read":
                    notification_id = data.get("notification_id")
                    if notification_id:
                        success = notification_manager.mark_as_read(notification_id)
                        await websocket.send_json({
                            "type": "mark_read_result",
                            "notification_id": notification_id,
                            "success": success,
                        })
                
                elif msg_type == "mark_all_read":
                    for n in notification_manager._notifications:
                        n.read = True
                    await websocket.send_json({
                        "type": "mark_all_read_result",
                        "success": True,
                    })
                
                elif msg_type == "get_history":
                    limit = data.get("limit", 50)
                    include_read = data.get("include_read", True)
                    history = notification_manager.get_history(limit, include_read)
                    await websocket.send_json({
                        "type": "history",
                        "notifications": history,
                        "unread_count": notification_manager.get_unread_count(),
                    })
                    
            except asyncio.TimeoutError:
                # Send ping to keep alive
                try:
                    await websocket.send_json({
                        "type": "ping",
                        "timestamp": time.time(),
                    })
                except Exception as ping_err:
                    logger.debug(f"Ping failed, closing connection: {ping_err}")
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"Notification client {client_id} disconnected normally")
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
    finally:
        await notification_manager.disconnect(client_id)


# =============================================================================
# HTTP ENDPOINTS
# =============================================================================

@router.post("/send", response_model=NotificationResponse)
async def send_notification(notification: NotificationCreate):
    """Send a notification to all connected clients."""
    try:
        notification_type = NotificationType(notification.type)
    except ValueError:
        notification_type = NotificationType.INFO
    
    try:
        priority = NotificationPriority(notification.priority)
    except ValueError:
        priority = NotificationPriority.NORMAL
    
    notif = notification_manager.create_notification(
        title=notification.title,
        message=notification.message,
        notification_type=notification_type,
        priority=priority,
        data=notification.data,
        expires_in_seconds=notification.expires_in_seconds,
    )
    
    sent_count = await notification_manager.broadcast(notif)
    
    return NotificationResponse(
        success=True,
        notification_id=notif.id,
        message=f"Sent to {sent_count} clients",
    )


@router.get("/history")
async def get_notification_history(
    limit: int = 50,
    include_read: bool = True,
):
    """Get notification history."""
    history = notification_manager.get_history(limit, include_read)
    return {
        "notifications": history,
        "count": len(history),
        "unread_count": notification_manager.get_unread_count(),
    }


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read."""
    success = notification_manager.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/mark-all-read")
async def mark_all_notifications_read():
    """Mark all notifications as read."""
    for n in notification_manager._notifications:
        n.read = True
    return {"success": True}


@router.get("/stats")
async def get_notification_stats():
    """Get notification system statistics."""
    return notification_manager.get_stats()


@router.get("/unread-count")
async def get_unread_count():
    """Get unread notification count."""
    return {
        "unread_count": notification_manager.get_unread_count(),
    }
