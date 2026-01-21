"""
Enterprise AI Assistant - WebSocket Module
Real-time streaming chat desteği

Endüstri standardı WebSocket implementasyonu.
Gerçek token-by-token streaming ile.

V2 Features:
- Intelligent Model Routing (4B/8B)
- Human-in-the-Loop Feedback
- A/B Model Comparison
- Real-time Model Badges
"""

import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from core.config import settings
from core.llm_manager import llm_manager
from core.logger import get_logger
from core.model_router import (
    get_model_router,
    ModelSize,
    FeedbackType,
    FeedbackStatus,
    MODEL_CONFIG,
)
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
    """
    Mesajın basit sohbet mi yoksa kompleks görev mi olduğunu belirle.
    
    NOTE: Bu fonksiyon backward compatibility için korunuyor.
    Yeni kod ModelRouter kullanmalı.
    """
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


async def route_and_generate(
    client_id: str,
    message: str,
    use_routing: bool = True,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Model router ile routing yapıp yanıt üret.
    
    Args:
        client_id: Client ID
        message: Kullanıcı mesajı  
        use_routing: Model routing kullanılsın mı
        
    Yields:
        Streaming mesajları (routing_info, chunk, end, etc.)
    """
    try:
        model_router = get_model_router()
        
        # 1. ROUTING - Hangi model kullanılacak?
        routing_result = await model_router.route_async(message)
        
        # Routing bilgisini gönder
        yield {
            "type": "routing",
            "routing": routing_result.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # 2. MODEL SEÇİMİ
        model_name = routing_result.model_name
        model_config = MODEL_CONFIG[routing_result.model_size]
        
        logger.info(
            f"Routing decision: {model_config['display_name']} "
            f"(confidence: {routing_result.confidence:.2f}, "
            f"source: {routing_result.decision_source.value})"
        )
        
        # 3. LLM'DEN STREAMING YANIT
        default_system = """Sen yardımcı bir AI asistanısın. Türkçe yanıt ver.
Kullanıcıya nazik ve bilgilendirici yanıtlar sun."""
        
        async for chunk in llm_manager.generate_stream_async(
            prompt=message,
            system_prompt=default_system,
            temperature=0.7,
            model=model_name,  # Seçilen modeli kullan
        ):
            # İptal kontrolü
            if manager.is_cancelled(client_id):
                logger.info(f"Streaming cancelled for {client_id}")
                yield {
                    "type": "cancelled",
                    "timestamp": datetime.now().isoformat()
                }
                return
            
            yield {
                "type": "chunk",
                "content": chunk,
                "timestamp": datetime.now().isoformat()
            }
        
        # 4. BİTİŞ - Feedback için gerekli bilgilerle
        yield {
            "type": "end",
            "response_id": routing_result.response_id,
            "model_size": routing_result.model_size.value,
            "model_name": model_name,
            "model_icon": model_config["icon"],
            "model_display_name": model_config["display_name"],
            "confidence": routing_result.confidence,
            "decision_source": routing_result.decision_source.value,
            "attempt_number": routing_result.attempt_number,
            "streaming_type": "real",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Route and generate error: {e}")
        yield {
            "type": "error",
            "content": f"Bir hata oluştu: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


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
    use_routing: bool = True,
    force_model: Optional[str] = None,
) -> None:
    """
    Chat mesajını işle ve streaming yanıt gönder.
    
    Args:
        websocket: WebSocket bağlantısı
        client_id: Client ID
        message: Kullanıcı mesajı
        session_id: Session ID (opsiyonel)
        use_streaming: Gerçek streaming mi kullanılsın
        use_routing: Model routing kullanılsın mı
        force_model: Zorla belirli model kullan (comparison için)
    """
    try:
        # İptal bayrağını sıfırla
        manager.reset_cancellation(client_id)
        
        # Başlangıç mesajı
        await manager.send_message(client_id, {
            "type": "start",
            "timestamp": datetime.now().isoformat()
        })
        
        # FORCED MODEL - Karşılaştırma modu
        if force_model:
            logger.info(f"Forced model mode: {force_model}")
            
            # Direkt belirtilen modeli kullan
            default_system = """Sen yardımcı bir AI asistanısın. Türkçe yanıt ver.
Kullanıcıya nazik ve bilgilendirici yanıtlar sun."""
            
            async for chunk in llm_manager.generate_stream_async(
                prompt=message,
                system_prompt=default_system,
                temperature=0.7,
                model=force_model,
            ):
                if manager.is_cancelled(client_id):
                    break
                    
                await manager.send_message(client_id, {
                    "type": "chunk",
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })
            
            await manager.send_message(client_id, {
                "type": "end",
                "model_name": force_model,
                "streaming_type": "forced",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # MODEL ROUTING MODE
        if use_routing:
            logger.info(f"Using model routing for: {message[:50]}...")
            
            async for event in route_and_generate(client_id, message):
                if event["type"] == "cancelled":
                    await manager.send_message(client_id, event)
                    return
                await manager.send_message(client_id, event)
            
            return
        
        # LEGACY MODE - Basit sorgu kontrolü
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
    
    Desteklenen mesaj tipleri:
    - chat: Normal chat mesajı (model routing ile)
    - chat_legacy: Eski mod (routing olmadan)
    - compare: Model karşılaştırma
    - feedback: Kullanıcı feedback'i
    - confirm: Feedback onayı
    - cancel: Streaming iptal
    - ping: Heartbeat
    
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
                "model_routing": True,
                "feedback": True,
                "comparison": True,
            },
            "models": {
                k.value: {
                    "name": v["name"],
                    "display_name": v["display_name"],
                    "icon": v["icon"],
                }
                for k, v in MODEL_CONFIG.items()
            },
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Mesaj bekle
            data = await websocket.receive_json()
            
            message_type = data.get("type", "chat")
            
            # =====================
            # CHAT - Model Routing ile
            # =====================
            if message_type == "chat":
                message = data.get("message", "")
                session_id = data.get("session_id")
                use_streaming = data.get("streaming", True)
                use_routing = data.get("routing", True)  # Default: routing açık
                
                if message.strip():
                    await handle_chat_message(
                        websocket,
                        client_id,
                        message,
                        session_id,
                        use_streaming,
                        use_routing=use_routing,
                    )
            
            # =====================
            # CHAT LEGACY - Eski mod
            # =====================
            elif message_type == "chat_legacy":
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
                        use_routing=False,
                    )
            
            # =====================
            # COMPARE - Model karşılaştırma
            # =====================
            elif message_type == "compare":
                feedback_id = data.get("feedback_id")
                
                if not feedback_id:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "content": "feedback_id gerekli",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                try:
                    model_router = get_model_router()
                    query, comparison_result = model_router.request_comparison(feedback_id)
                    
                    # Karşılaştırma başlangıcı
                    await manager.send_message(client_id, {
                        "type": "compare_start",
                        "feedback_id": feedback_id,
                        "comparison_routing": comparison_result.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Alternatif model ile yanıt üret
                    await handle_chat_message(
                        websocket,
                        client_id,
                        query,
                        force_model=comparison_result.model_name,
                    )
                    
                except ValueError as e:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "content": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # =====================
            # FEEDBACK - Kullanıcı geri bildirimi
            # =====================
            elif message_type == "feedback":
                response_id = data.get("response_id")
                feedback_type = data.get("feedback_type")  # correct, downgrade, upgrade
                
                if not response_id or not feedback_type:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "content": "response_id ve feedback_type gerekli",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                try:
                    # FeedbackType'a çevir
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
                        message = "✅ Teşekkürler! Tercih kaydedildi."
                    elif fb_type == FeedbackType.DOWNGRADE:
                        message = "🔄 Küçük modeli denemek için 'Dene' butonunu kullanın."
                    else:
                        message = "🔄 Büyük modeli denemek için 'Dene' butonunu kullanın."
                    
                    await manager.send_message(client_id, {
                        "type": "feedback_received",
                        "feedback": feedback.to_dict(),
                        "message": message,
                        "requires_comparison": requires_comparison,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except ValueError as e:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "content": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # =====================
            # CONFIRM - Feedback onayı
            # =====================
            elif message_type == "confirm":
                feedback_id = data.get("feedback_id")
                confirmed = data.get("confirmed", False)
                
                if not feedback_id:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "content": "feedback_id gerekli",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                try:
                    model_router = get_model_router()
                    feedback = model_router.confirm_feedback(
                        feedback_id=feedback_id,
                        confirmed=confirmed,
                    )
                    
                    if confirmed:
                        model_config = MODEL_CONFIG.get(feedback.final_decision, {})
                        model_name = model_config.get("display_name", "Model")
                        message = f"✅ Tercih kaydedildi! Benzer sorgular için {model_name} kullanılacak."
                        learning_applied = True
                    else:
                        message = "↩️ İlk tercih korundu. Teşekkürler!"
                        learning_applied = False
                    
                    await manager.send_message(client_id, {
                        "type": "feedback_confirmed",
                        "feedback": feedback.to_dict(),
                        "message": message,
                        "learning_applied": learning_applied,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                except ValueError as e:
                    await manager.send_message(client_id, {
                        "type": "error",
                        "content": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # =====================
            # CANCEL - Streaming iptal
            # =====================
            elif message_type == "cancel":
                manager.cancel_stream(client_id)
                await manager.send_message(client_id, {
                    "type": "cancel_acknowledged",
                    "timestamp": datetime.now().isoformat()
                })
            
            # =====================
            # PING - Heartbeat
            # =====================
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
