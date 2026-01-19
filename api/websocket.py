"""
Enterprise AI Assistant - WebSocket Module
Real-time streaming chat desteği

Endüstri standardı WebSocket implementasyonu.
Gerçek token-by-token streaming ile.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator
from fastapi import WebSocket, WebSocketDisconnect
from core.config import settings
from core.llm_manager import llm_manager
from core.logger import get_logger
from agents.orchestrator import orchestrator

logger = get_logger("websocket")


class ConnectionManager:
    """WebSocket bağlantı yöneticisi."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.cancellation_flags: dict[str, bool] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Yeni bağlantı kabul et."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.cancellation_flags[client_id] = False
    
    def disconnect(self, client_id: str) -> None:
        """Bağlantıyı kapat."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.cancellation_flags:
            del self.cancellation_flags[client_id]
    
    def cancel_stream(self, client_id: str) -> None:
        """Streaming'i iptal et."""
        self.cancellation_flags[client_id] = True
    
    def is_cancelled(self, client_id: str) -> bool:
        """Streaming iptal edildi mi kontrol et."""
        return self.cancellation_flags.get(client_id, False)
    
    def reset_cancellation(self, client_id: str) -> None:
        """İptal bayrağını sıfırla."""
        self.cancellation_flags[client_id] = False
    
    async def send_message(self, client_id: str, message: dict) -> None:
        """Belirli bir client'a mesaj gönder."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
    
    async def broadcast(self, message: dict) -> None:
        """Tüm bağlı client'lara mesaj gönder."""
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception:
                pass


# Global connection manager
manager = ConnectionManager()


def is_simple_chat_query(message: str) -> bool:
    """Mesajın basit sohbet mi yoksa kompleks görev mi olduğunu belirle."""
    message_lower = message.lower().strip()
    
    # Basit sohbet kalıpları
    simple_patterns = [
        "merhaba", "selam", "nasılsın", "teşekkür", "sağol", 
        "hello", "hi", "thanks", "bye", "hey",
        "günaydın", "iyi geceler", "iyi akşamlar",
        "naber", "ne haber", "hoşçakal",
    ]
    
    # Kompleks görev kalıpları (RAG/Agent gerektiren)
    complex_patterns = [
        "ara", "bul", "getir", "listele", "analiz", "yaz", "hazırla",
        "döküman", "dosya", "upload", "belge", "rapor",
        "search", "find", "analyze", "write", "document",
    ]
    
    # Basit sohbet mi?
    if any(pattern in message_lower for pattern in simple_patterns) and len(message.split()) <= 10:
        return True
    
    # Kompleks görev mi?
    if any(pattern in message_lower for pattern in complex_patterns):
        return False
    
    # Soru mu? (kısa sorular direkt streaming ile yanıtlanabilir)
    if len(message.split()) <= 20 and message.endswith("?"):
        return True
    
    # Default: kompleks
    return False


async def stream_llm_response(
    client_id: str,
    message: str,
    system_prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    LLM'den gerçek streaming yanıt al.
    Token-by-token streaming sağlar.
    """
    default_system = """Sen yardımcı bir AI asistanısın. Türkçe yanıt ver.
Kullanıcıya nazik ve bilgilendirici yanıtlar sun."""
    
    async for chunk in llm_manager.generate_stream_async(
        prompt=message,
        system_prompt=system_prompt or default_system,
        temperature=0.7,
    ):
        # İptal kontrolü
        if manager.is_cancelled(client_id):
            logger.info(f"Streaming cancelled for {client_id}")
            break
        yield chunk


async def handle_chat_message(
    websocket: WebSocket,
    client_id: str,
    message: str,
    session_id: Optional[str] = None,
    use_streaming: bool = True,
) -> None:
    """
    Chat mesajını işle ve streaming yanıt gönder.
    
    Args:
        websocket: WebSocket bağlantısı
        client_id: Client ID
        message: Kullanıcı mesajı
        session_id: Session ID (opsiyonel)
        use_streaming: Gerçek streaming mi kullanılsın
    """
    try:
        # İptal bayrağını sıfırla
        manager.reset_cancellation(client_id)
        
        # Başlangıç mesajı
        await manager.send_message(client_id, {
            "type": "start",
            "timestamp": datetime.now().isoformat()
        })
        
        # Basit sorgu mu kontrol et
        is_simple = is_simple_chat_query(message)
        
        if is_simple and use_streaming:
            # GERÇEK STREAMING - Token by token
            logger.info(f"Using real streaming for: {message[:50]}...")
            
            full_content = []
            async for chunk in stream_llm_response(client_id, message):
                if manager.is_cancelled(client_id):
                    break
                    
                full_content.append(chunk)
                await manager.send_message(client_id, {
                    "type": "chunk",
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Bitiş mesajı
            await manager.send_message(client_id, {
                "type": "end",
                "agent": "assistant",
                "streaming_type": "real",
                "timestamp": datetime.now().isoformat()
            })
            
        else:
            # ORCHESTRATOR MODU - Kompleks görevler için
            logger.info(f"Using orchestrator for: {message[:50]}...")
            
            # Orchestrator işlem bilgisi
            await manager.send_message(client_id, {
                "type": "processing",
                "message": "Görev analiz ediliyor...",
                "timestamp": datetime.now().isoformat()
            })
            
            # Orchestrator ile görevi işle
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: orchestrator.process(message)
            )
            
            if manager.is_cancelled(client_id):
                await manager.send_message(client_id, {
                    "type": "cancelled",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            if response.success:
                content = response.content
                
                # Yanıtı streaming olarak gönder (ama gerçek token değil, chunk)
                chunk_size = 15  # Daha doğal görünüm için
                
                for i in range(0, len(content), chunk_size):
                    if manager.is_cancelled(client_id):
                        break
                        
                    chunk = content[i:i + chunk_size]
                    await manager.send_message(client_id, {
                        "type": "chunk",
                        "content": chunk,
                        "timestamp": datetime.now().isoformat()
                    })
                    await asyncio.sleep(0.015)  # Küçük gecikme
                
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
                "agent": response.agent if hasattr(response, 'agent') else "orchestrator",
                "streaming_type": "simulated",
                "timestamp": datetime.now().isoformat()
            })
        
    except asyncio.CancelledError:
        await manager.send_message(client_id, {
            "type": "cancelled",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Chat message error: {e}")
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
            "features": {
                "real_streaming": True,
                "cancellation": True,
                "sources": True,
            },
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Mesaj bekle
            data = await websocket.receive_json()
            
            message_type = data.get("type", "chat")
            
            if message_type == "chat":
                message = data.get("message", "")
                session_id = data.get("session_id")
                use_streaming = data.get("streaming", True)
                
                if message.strip():
                    await handle_chat_message(
                        websocket,
                        client_id,
                        message,
                        session_id,
                        use_streaming,
                    )
            
            elif message_type == "cancel":
                # Mevcut streaming'i iptal et
                manager.cancel_stream(client_id)
                await manager.send_message(client_id, {
                    "type": "cancel_acknowledged",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "ping":
                await manager.send_message(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        manager.disconnect(client_id)
        logger.error(f"WebSocket error for {client_id}: {e}")
        raise e
