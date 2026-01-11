"""
Enterprise AI Assistant - WebSocket Module
Real-time streaming chat desteği

Endüstri standardı WebSocket implementasyonu.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect
from core.config import settings
from core.llm_manager import llm_manager
from agents.orchestrator import orchestrator


class ConnectionManager:
    """WebSocket bağlantı yöneticisi."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Yeni bağlantı kabul et."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str) -> None:
        """Bağlantıyı kapat."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_message(self, client_id: str, message: dict) -> None:
        """Belirli bir client'a mesaj gönder."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: dict) -> None:
        """Tüm bağlı client'lara mesaj gönder."""
        for connection in self.active_connections.values():
            await connection.send_json(message)


# Global connection manager
manager = ConnectionManager()


async def handle_chat_message(
    websocket: WebSocket,
    client_id: str,
    message: str,
    session_id: Optional[str] = None
) -> None:
    """
    Chat mesajını işle ve streaming yanıt gönder.
    
    Args:
        websocket: WebSocket bağlantısı
        client_id: Client ID
        message: Kullanıcı mesajı
        session_id: Session ID (opsiyonel)
    """
    try:
        # Başlangıç mesajı
        await manager.send_message(client_id, {
            "type": "start",
            "timestamp": datetime.now().isoformat()
        })
        
        # Orchestrator ile görevi işle
        response = await orchestrator.process(message)
        
        # Streaming simulation (Ollama native streaming için)
        if response.success:
            # Token token gönder (simülasyon)
            content = response.content
            chunk_size = 10  # Her seferde 10 karakter
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                await manager.send_message(client_id, {
                    "type": "chunk",
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })
                await asyncio.sleep(0.02)  # Doğal görünmesi için küçük gecikme
            
            # Kaynakları gönder
            if response.sources:
                await manager.send_message(client_id, {
                    "type": "sources",
                    "sources": response.sources,
                    "timestamp": datetime.now().isoformat()
                })
        else:
            await manager.send_message(client_id, {
                "type": "error",
                "content": response.content,
                "timestamp": datetime.now().isoformat()
            })
        
        # Bitiş mesajı
        await manager.send_message(client_id, {
            "type": "end",
            "agent": response.agent,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        await manager.send_message(client_id, {
            "type": "error",
            "content": f"Bir hata oluştu: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """
    Ana WebSocket endpoint'i.
    
    Args:
        websocket: WebSocket bağlantısı
        client_id: Client ID
    """
    await manager.connect(websocket, client_id)
    
    try:
        # Bağlantı onayı
        await manager.send_message(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Mesaj bekle
            data = await websocket.receive_json()
            
            message_type = data.get("type", "chat")
            
            if message_type == "chat":
                message = data.get("message", "")
                session_id = data.get("session_id")
                
                if message.strip():
                    await handle_chat_message(
                        websocket,
                        client_id,
                        message,
                        session_id
                    )
            
            elif message_type == "ping":
                await manager.send_message(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        manager.disconnect(client_id)
        raise e
