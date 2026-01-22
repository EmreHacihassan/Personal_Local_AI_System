"""
🖥️👁️ Vision API Endpoints
===========================

Real-time ekran paylaşımı ve AI görüntü analizi API'si.
Tamamen LOCAL çalışır - hiçbir veri dışarı gönderilmez.

Endpoints:
- POST /api/vision/analyze - Tek seferlik ekran analizi
- POST /api/vision/ask - Ekrana soru sor
- POST /api/vision/session - Oturum oluştur
- DELETE /api/vision/session/{id} - Oturum sonlandır
- GET /api/vision/capture - Ekran görüntüsü al
- GET /api/vision/status - Sistem durumu
- WebSocket /api/vision/ws/stream - Gerçek zamanlı streaming

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.logger import get_logger
from core.realtime_vision import (
    RealtimeVisionSystem,
    VisionConfig,
    VisionMode,
    StreamQuality,
    ScreenAnalysis,
    get_realtime_vision,
)

logger = get_logger("vision_api")

router = APIRouter(prefix="/api/vision", tags=["Vision AI"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AnalyzeRequest(BaseModel):
    """Ekran analiz isteği."""
    mode: str = Field(default="describe", description="Analiz modu: describe, ui_analysis, text_extract, code_review, error_detect, tutorial, custom")
    custom_prompt: Optional[str] = Field(default=None, description="Özel prompt (mode=custom için)")
    session_id: Optional[str] = Field(default=None, description="Oturum ID (context için)")


class AskRequest(BaseModel):
    """Ekrana soru sorma isteği."""
    question: str = Field(..., description="Ekran hakkında soru")
    session_id: Optional[str] = Field(default=None, description="Oturum ID (konuşma context'i için)")


class TutorialRequest(BaseModel):
    """Tutorial isteği."""
    task: str = Field(..., description="Yapılmak istenen görev")


class SessionResponse(BaseModel):
    """Oturum yanıtı."""
    session_id: str
    created_at: str
    message: str


class AnalysisResponse(BaseModel):
    """Analiz yanıtı."""
    success: bool
    frame_id: str
    timestamp: str
    duration_ms: float
    description: str
    ai_response: str
    detected_text: Optional[str] = None
    detected_errors: List[str] = []
    suggestions: List[str] = []
    mode: str
    model: str
    error: Optional[str] = None


class CaptureResponse(BaseModel):
    """Ekran yakalama yanıtı."""
    success: bool
    frame_id: str
    timestamp: str
    width: int
    height: int
    size_bytes: int
    image_base64: str
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Sistem durumu yanıtı."""
    streaming: bool
    frame_count: int
    subscribers: int
    active_sessions: int
    vision_available: bool
    model: str
    quality: str
    dependencies: Dict[str, bool]


class StreamConfigRequest(BaseModel):
    """Streaming konfigürasyonu."""
    quality: str = Field(default="medium", description="low, medium, high, ultra")
    analyze_interval: float = Field(default=2.0, description="Analiz aralığı (saniye)")
    auto_analyze: bool = Field(default=False, description="Otomatik analiz")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_vision_mode(mode_str: str) -> VisionMode:
    """String'den VisionMode enum'a dönüştür."""
    mode_map = {
        "describe": VisionMode.DESCRIBE,
        "ui_analysis": VisionMode.UI_ANALYSIS,
        "text_extract": VisionMode.TEXT_EXTRACT,
        "code_review": VisionMode.CODE_REVIEW,
        "error_detect": VisionMode.ERROR_DETECT,
        "tutorial": VisionMode.TUTORIAL,
        "compare": VisionMode.COMPARE,
        "custom": VisionMode.CUSTOM,
    }
    return mode_map.get(mode_str.lower(), VisionMode.DESCRIBE)


def _analysis_to_response(analysis: ScreenAnalysis) -> AnalysisResponse:
    """ScreenAnalysis'i response modeline dönüştür."""
    return AnalysisResponse(
        success=analysis.success,
        frame_id=analysis.frame_id,
        timestamp=analysis.timestamp.isoformat(),
        duration_ms=analysis.duration_ms,
        description=analysis.description,
        ai_response=analysis.ai_response,
        detected_text=analysis.detected_text if analysis.detected_text else None,
        detected_errors=analysis.detected_errors,
        suggestions=analysis.suggestions,
        mode=analysis.mode.value,
        model=analysis.model,
        error=analysis.error,
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status", response_model=StatusResponse, summary="Sistem durumu")
async def get_status():
    """
    Vision sisteminin durumunu al.
    
    Döner:
    - Streaming durumu
    - Frame sayısı
    - Aktif oturumlar
    - Vision model durumu
    """
    vision = get_realtime_vision()
    status = vision.get_status()
    
    # Check vision availability
    vision_check = await vision.check_vision_available()
    
    return StatusResponse(
        streaming=status["streaming"],
        frame_count=status["frame_count"],
        subscribers=status["subscribers"],
        active_sessions=status["active_sessions"],
        vision_available=vision_check.get("available", False),
        model=status["config"]["model"],
        quality=status["config"]["quality"],
        dependencies=status["dependencies"],
    )


@router.get("/health", summary="Vision sağlık kontrolü")
async def health_check():
    """Vision sisteminin sağlık durumunu kontrol et."""
    vision = get_realtime_vision()
    vision_check = await vision.check_vision_available()
    
    return {
        "status": "healthy" if vision_check.get("available") else "degraded",
        "vision": vision_check,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/session", response_model=SessionResponse, summary="Oturum oluştur")
async def create_session():
    """
    Yeni bir görüşme oturumu oluştur.
    
    Oturumlar konuşma bağlamını korur, böylece önceki sorular
    ve ekran görüntüleri hatırlanır.
    """
    vision = get_realtime_vision()
    session_id = vision.create_session()
    
    return SessionResponse(
        session_id=session_id,
        created_at=datetime.now().isoformat(),
        message="Oturum başarıyla oluşturuldu. Artık ekran hakkında sorular sorabilirsiniz.",
    )


@router.delete("/session/{session_id}", summary="Oturumu sonlandır")
async def end_session(session_id: str):
    """Bir görüşme oturumunu sonlandır."""
    vision = get_realtime_vision()
    
    if vision.end_session(session_id):
        return {"success": True, "message": "Oturum sonlandırıldı"}
    
    raise HTTPException(status_code=404, detail="Oturum bulunamadı")


@router.get("/session/{session_id}", summary="Oturum bilgisi")
async def get_session_info(session_id: str):
    """Oturum bilgilerini al."""
    vision = get_realtime_vision()
    context = vision.get_session(session_id)
    
    if context is None:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı")
    
    return {
        "session_id": context.session_id,
        "created_at": context.created_at.isoformat(),
        "last_activity": context.last_activity.isoformat(),
        "message_count": len(context.messages),
        "frame_count": len(context.frames),
        "analysis_count": len(context.analysis_history),
    }


@router.get("/capture", response_model=CaptureResponse, summary="Ekran yakala")
async def capture_screen():
    """
    Anlık ekran görüntüsü yakala.
    
    Base64 formatında görüntü döner.
    """
    vision = get_realtime_vision()
    frame = vision._stream_manager.capture_single()
    
    if frame is None:
        raise HTTPException(status_code=500, detail="Ekran yakalama başarısız")
    
    return CaptureResponse(
        success=True,
        frame_id=frame.id,
        timestamp=frame.timestamp.isoformat(),
        width=frame.width,
        height=frame.height,
        size_bytes=frame.size_bytes,
        image_base64=frame.image_base64,
    )


@router.post("/analyze", response_model=AnalysisResponse, summary="Ekran analizi")
async def analyze_screen(request: AnalyzeRequest):
    """
    Ekranı analiz et.
    
    Modlar:
    - describe: Genel açıklama
    - ui_analysis: UI element analizi
    - text_extract: Metin çıkarma
    - code_review: Kod inceleme
    - error_detect: Hata tespiti
    - tutorial: Rehber/eğitim
    - custom: Özel prompt
    """
    vision = get_realtime_vision()
    mode = _get_vision_mode(request.mode)
    
    analysis = await vision.capture_and_analyze(
        mode=mode,
        custom_prompt=request.custom_prompt,
    )
    
    return _analysis_to_response(analysis)


@router.post("/ask", response_model=AnalysisResponse, summary="Ekrana soru sor")
async def ask_screen(request: AskRequest):
    """
    Ekran görüntüsü hakkında soru sor.
    
    Örnek sorular:
    - "Ekranda hangi program açık?"
    - "Bu butona nasıl tıklarım?"
    - "Hata mesajı ne diyor?"
    - "Kodda hata var mı?"
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Soru boş olamaz")
    
    vision = get_realtime_vision()
    
    analysis = await vision.analyze_screen(
        question=request.question,
        session_id=request.session_id,
    )
    
    return _analysis_to_response(analysis)


@router.post("/tutorial", response_model=AnalysisResponse, summary="Görev rehberi")
async def get_tutorial(request: TutorialRequest):
    """
    Belirli bir görev için ekran bazlı rehber al.
    
    Örnek:
    - task: "Dosyayı kaydetmek istiyorum"
    - task: "Bu programı kapatmak istiyorum"
    """
    vision = get_realtime_vision()
    
    analysis = await vision.get_tutorial(request.task)
    
    return _analysis_to_response(analysis)


@router.post("/detect-errors", response_model=AnalysisResponse, summary="Hata tespiti")
async def detect_errors():
    """Ekranda hata ve uyarıları tespit et."""
    vision = get_realtime_vision()
    analysis = await vision.detect_errors()
    return _analysis_to_response(analysis)


@router.post("/extract-text", response_model=AnalysisResponse, summary="Metin çıkarma")
async def extract_text():
    """Ekrandaki metinleri çıkar."""
    vision = get_realtime_vision()
    analysis = await vision.extract_text()
    return _analysis_to_response(analysis)


@router.post("/analyze-ui", response_model=AnalysisResponse, summary="UI analizi")
async def analyze_ui():
    """UI elementlerini analiz et."""
    vision = get_realtime_vision()
    analysis = await vision.analyze_ui()
    return _analysis_to_response(analysis)


@router.post("/review-code", response_model=AnalysisResponse, summary="Kod inceleme")
async def review_code():
    """Ekrandaki kodu incele ve analiz et."""
    vision = get_realtime_vision()
    analysis = await vision.review_code()
    return _analysis_to_response(analysis)


@router.post("/streaming/start", summary="Streaming başlat")
async def start_streaming():
    """Ekran streaming'i başlat."""
    vision = get_realtime_vision()
    vision.start_streaming()
    
    return {
        "success": True,
        "message": "Streaming başlatıldı",
        "websocket_url": "/api/vision/ws/stream",
    }


@router.post("/streaming/stop", summary="Streaming durdur")
async def stop_streaming():
    """Ekran streaming'i durdur."""
    vision = get_realtime_vision()
    vision.stop_streaming()
    
    return {
        "success": True,
        "message": "Streaming durduruldu",
    }


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket ile gerçek zamanlı ekran streaming.
    
    Mesaj formatları:
    
    Client -> Server:
    - {"type": "start"} - Streaming başlat
    - {"type": "stop"} - Streaming durdur
    - {"type": "analyze", "question": "..."} - Anlık analiz
    - {"type": "config", "quality": "low/medium/high"} - Kalite ayarı
    
    Server -> Client:
    - {"type": "frame", "data": {...}} - Frame verisi
    - {"type": "analysis", "data": {...}} - Analiz sonucu
    - {"type": "status", "data": {...}} - Durum bilgisi
    - {"type": "error", "message": "..."} - Hata mesajı
    """
    await websocket.accept()
    
    vision = get_realtime_vision()
    streaming_task = None
    session_id = vision.create_session()
    
    logger.info(f"Vision WebSocket connected: {session_id}")
    
    try:
        while True:
            # Receive message
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "ping"})
                continue
            
            msg_type = data.get("type", "")
            
            if msg_type == "start":
                # Start streaming
                if not vision._stream_manager.is_running:
                    vision.start_streaming()
                
                await websocket.send_json({
                    "type": "status",
                    "data": {"streaming": True, "message": "Streaming başladı"}
                })
                
                # Start frame sending task
                if streaming_task is None or streaming_task.done():
                    streaming_task = asyncio.create_task(
                        _send_frames(websocket, vision)
                    )
            
            elif msg_type == "stop":
                # Stop streaming task
                if streaming_task and not streaming_task.done():
                    streaming_task.cancel()
                    try:
                        await streaming_task
                    except asyncio.CancelledError:
                        pass
                
                await websocket.send_json({
                    "type": "status",
                    "data": {"streaming": False, "message": "Streaming durduruldu"}
                })
            
            elif msg_type == "analyze":
                # Analyze current screen
                question = data.get("question", "Ekranda ne var?")
                
                await websocket.send_json({
                    "type": "status",
                    "data": {"analyzing": True}
                })
                
                analysis = await vision.analyze_screen(question, session_id)
                
                await websocket.send_json({
                    "type": "analysis",
                    "data": analysis.to_dict()
                })
            
            elif msg_type == "capture":
                # Single capture
                frame = vision._stream_manager.capture_single()
                
                if frame:
                    await websocket.send_json({
                        "type": "frame",
                        "data": {
                            "id": frame.id,
                            "timestamp": frame.timestamp.isoformat(),
                            "width": frame.width,
                            "height": frame.height,
                            "image": frame.image_base64,
                        }
                    })
            
            elif msg_type == "config":
                # Update config
                quality = data.get("quality", "medium")
                quality_map = {
                    "low": StreamQuality.LOW,
                    "medium": StreamQuality.MEDIUM,
                    "high": StreamQuality.HIGH,
                    "ultra": StreamQuality.ULTRA,
                }
                vision.config.quality = quality_map.get(quality, StreamQuality.MEDIUM)
                
                await websocket.send_json({
                    "type": "status",
                    "data": {"config_updated": True, "quality": quality}
                })
            
            elif msg_type == "pong":
                # Keepalive response
                pass
            
    except WebSocketDisconnect:
        logger.info(f"Vision WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Vision WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except Exception:
            pass
    finally:
        # Cleanup
        if streaming_task and not streaming_task.done():
            streaming_task.cancel()
        vision.end_session(session_id)


async def _send_frames(websocket: WebSocket, vision: RealtimeVisionSystem):
    """Frame'leri WebSocket'e gönder."""
    frame_interval = 1.0 / vision.config.quality_settings["fps"]
    
    try:
        while True:
            frame = vision._stream_manager.capture_single()
            
            if frame:
                await websocket.send_json({
                    "type": "frame",
                    "data": {
                        "id": frame.id,
                        "timestamp": frame.timestamp.isoformat(),
                        "width": frame.width,
                        "height": frame.height,
                        "size": frame.size_bytes,
                        "image": frame.image_base64,
                    }
                })
            
            await asyncio.sleep(frame_interval)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Frame sending error: {e}")


@router.websocket("/ws/interactive")
async def websocket_interactive(websocket: WebSocket):
    """
    Etkileşimli vision oturumu.
    
    Sürekli ekran izleme ve soru-cevap modunda çalışır.
    """
    await websocket.accept()
    
    vision = get_realtime_vision()
    session_id = vision.create_session()
    
    logger.info(f"Interactive vision session started: {session_id}")
    
    # Welcome message
    await websocket.send_json({
        "type": "welcome",
        "session_id": session_id,
        "message": "Merhaba! Ekranınız hakkında sorular sorabilirsiniz.",
        "commands": [
            "Ekranda ne var?",
            "Bu butona nasıl tıklarım?",
            "Hata var mı?",
            "Kodu incele",
            "Metin çıkar",
        ]
    })
    
    try:
        while True:
            # Receive question
            data = await websocket.receive_json()
            
            question = data.get("question", data.get("message", ""))
            
            if not question:
                await websocket.send_json({
                    "type": "error",
                    "message": "Lütfen bir soru sorun"
                })
                continue
            
            # Thinking indicator
            await websocket.send_json({
                "type": "thinking",
                "message": "Ekranınızı analiz ediyorum..."
            })
            
            # Analyze
            analysis = await vision.analyze_screen(question, session_id)
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "success": analysis.success,
                "message": analysis.ai_response,
                "suggestions": analysis.suggestions,
                "errors": analysis.detected_errors,
                "duration_ms": analysis.duration_ms,
            })
            
    except WebSocketDisconnect:
        logger.info(f"Interactive session ended: {session_id}")
    except Exception as e:
        logger.error(f"Interactive session error: {e}")
    finally:
        vision.end_session(session_id)


# =============================================================================
# BATCH OPERATIONS
# =============================================================================

@router.post("/batch/analyze", summary="Toplu analiz")
async def batch_analyze(
    modes: List[str] = ["describe", "error_detect"],
    session_id: Optional[str] = None,
):
    """
    Tek ekran görüntüsünü birden fazla modda analiz et.
    """
    vision = get_realtime_vision()
    
    # Single capture
    frame = vision._stream_manager.capture_single()
    
    if frame is None:
        raise HTTPException(status_code=500, detail="Ekran yakalama başarısız")
    
    results = {}
    
    for mode_str in modes:
        mode = _get_vision_mode(mode_str)
        analysis = await vision._analyzer.analyze(frame, mode)
        results[mode_str] = analysis.to_dict()
    
    return {
        "success": True,
        "frame_id": frame.id,
        "timestamp": frame.timestamp.isoformat(),
        "analyses": results,
    }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["router"]
