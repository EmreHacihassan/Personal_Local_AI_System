"""
Enterprise AI Assistant - Screen Capture API Router
====================================================

Ekran görüntüsü yakalama ve analiz API endpoint'leri.
Tamamen local çalışır.

Endpoints:
- POST /api/screen/capture - Ekran yakala
- POST /api/screen/analyze - Görüntü analiz et
- POST /api/screen/capture-and-analyze - Yakala ve analiz et
- GET /api/screen/status - Sistem durumu
- GET /api/screen/monitors - Monitör listesi
- GET /api/screen/screenshots - Cache'deki screenshot'lar
- GET /api/screen/screenshots/{id} - Belirli screenshot
- DELETE /api/screen/screenshots/{id} - Screenshot sil
- GET /api/screen/last - Son screenshot (base64)
"""

import io
import base64
from typing import Optional, List, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

# Screen capture system
try:
    from core.screen_capture import (
        get_screen_capture_system,
        ScreenCaptureConfig,
        CaptureMode,
    )
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError as e:
    SCREEN_CAPTURE_AVAILABLE = False
    get_screen_capture_system = None

from core.logger import get_logger

logger = get_logger("screen_router")

router = APIRouter(prefix="/api/screen", tags=["Screen Capture"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CaptureRequest(BaseModel):
    """Ekran yakalama isteği."""
    mode: str = Field(
        default="primary",
        description="Yakalama modu: primary, full_screen, all_monitors, region"
    )
    monitor_index: Optional[int] = Field(
        default=None,
        description="Monitör indeksi (çoklu monitör için)"
    )
    region: Optional[List[int]] = Field(
        default=None,
        description="Bölge koordinatları [x, y, width, height]"
    )
    save_to_cache: bool = Field(
        default=True,
        description="Cache'e kaydet"
    )


class AnalyzeRequest(BaseModel):
    """Görüntü analiz isteği."""
    prompt: str = Field(
        default="Bu ekran görüntüsünde ne görüyorsun? Detaylı açıkla.",
        description="Analiz sorusu"
    )
    screenshot_id: Optional[str] = Field(
        default=None,
        description="Analiz edilecek screenshot ID (opsiyonel, yoksa son yakalanan)"
    )
    image_base64: Optional[str] = Field(
        default=None,
        description="Base64 encoded görüntü (opsiyonel)"
    )


class CaptureAndAnalyzeRequest(BaseModel):
    """Yakala ve analiz et isteği."""
    prompt: str = Field(
        default="Bu ekran görüntüsünde ne görüyorsun?",
        description="Analiz sorusu"
    )
    mode: str = Field(
        default="primary",
        description="Yakalama modu"
    )
    monitor_index: Optional[int] = Field(
        default=None,
        description="Monitör indeksi"
    )
    region: Optional[List[int]] = Field(
        default=None,
        description="Bölge koordinatları [x, y, width, height]"
    )


class ScreenshotResponse(BaseModel):
    """Screenshot yanıtı."""
    success: bool
    screenshot_id: Optional[str] = None
    timestamp: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    image_base64: Optional[str] = None
    error: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Analiz yanıtı."""
    success: bool
    response: Optional[str] = None
    model: Optional[str] = None
    duration_ms: Optional[float] = None
    screenshot_id: Optional[str] = None
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Sistem durumu yanıtı."""
    available: bool
    vision_available: bool
    vision_model: str
    monitors: List[dict]
    cache: dict
    last_screenshot: Optional[dict] = None
    capture_backend: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_capture_mode(mode_str: str) -> CaptureMode:
    """String'den CaptureMode'a dönüştür."""
    mode_map = {
        "primary": CaptureMode.PRIMARY_MONITOR,
        "full_screen": CaptureMode.FULL_SCREEN,
        "all_monitors": CaptureMode.ALL_MONITORS,
        "region": CaptureMode.REGION,
        "window": CaptureMode.WINDOW,
    }
    return mode_map.get(mode_str.lower(), CaptureMode.PRIMARY_MONITOR)


def _check_available():
    """Screen capture mevcut mu kontrol et."""
    if not SCREEN_CAPTURE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Screen capture not available. Install: pip install mss Pillow"
        )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status", response_model=StatusResponse)
async def get_screen_status():
    """
    Screen capture sistem durumunu al.
    """
    if not SCREEN_CAPTURE_AVAILABLE:
        return StatusResponse(
            available=False,
            vision_available=False,
            vision_model="",
            monitors=[],
            cache={},
            capture_backend="none",
        )
    
    try:
        system = get_screen_capture_system()
        status = system.get_status()
        
        return StatusResponse(
            available=True,
            vision_available=status.get("vision_available", False),
            vision_model=status.get("vision_model", ""),
            monitors=status.get("monitors", []),
            cache=status.get("cache", {}),
            last_screenshot=status.get("last_screenshot"),
            capture_backend=status.get("capture_backend", "unknown"),
        )
    except Exception as e:
        logger.error(f"Status error: {e}")
        return StatusResponse(
            available=False,
            vision_available=False,
            vision_model="",
            monitors=[],
            cache={},
            capture_backend="error",
        )


@router.get("/monitors")
async def get_monitors():
    """
    Mevcut monitörleri listele.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        monitors = system.get_monitors()
        
        return {
            "success": True,
            "monitors": monitors,
            "count": len(monitors),
        }
    except Exception as e:
        logger.error(f"Get monitors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capture", response_model=ScreenshotResponse)
async def capture_screen(request: CaptureRequest):
    """
    Ekran görüntüsü yakala.
    
    Modes:
    - primary: Ana monitör
    - full_screen: Tam ekran
    - all_monitors: Tüm monitörler
    - region: Belirli bölge (region parametresi gerekli)
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        
        mode = _get_capture_mode(request.mode)
        region = tuple(request.region) if request.region and len(request.region) == 4 else None
        
        image, metadata = system.capture(
            mode=mode,
            monitor_index=request.monitor_index,
            region=region,
            save_to_cache=request.save_to_cache,
        )
        
        if image is None or metadata is None:
            return ScreenshotResponse(
                success=False,
                error="Screen capture failed",
            )
        
        # Convert to base64
        import io
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return ScreenshotResponse(
            success=True,
            screenshot_id=metadata.id,
            timestamp=metadata.timestamp.isoformat(),
            width=metadata.width,
            height=metadata.height,
            size_bytes=metadata.size_bytes,
            image_base64=image_b64,
        )
        
    except Exception as e:
        logger.error(f"Capture error: {e}")
        return ScreenshotResponse(
            success=False,
            error=str(e),
        )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(request: AnalyzeRequest):
    """
    Görüntüyü analiz et.
    
    Üç modda çalışır:
    1. screenshot_id verilirse: Cache'deki görüntüyü analiz et
    2. image_base64 verilirse: Verilen görüntüyü analiz et
    3. Hiçbiri verilmezse: Son yakalanan görüntüyü analiz et
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        
        # Check if vision is available
        if not system.is_vision_available():
            return AnalysisResponse(
                success=False,
                error="Vision model not available. Make sure Ollama is running with llava model.",
            )
        
        # Determine which image to analyze
        if request.screenshot_id:
            # From cache
            result = system.analyze_from_cache(request.screenshot_id, request.prompt)
        elif request.image_base64:
            # From provided base64
            from PIL import Image
            import io
            
            image_bytes = base64.b64decode(request.image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            result = system._analyzer.analyze(image, request.prompt, "provided")
        else:
            # Last captured
            result = system.analyze(request.prompt)
        
        return AnalysisResponse(
            success=result.success,
            response=result.response if result.success else None,
            model=result.model,
            duration_ms=result.duration_ms,
            screenshot_id=result.screenshot_id,
            error=result.error if not result.success else None,
        )
        
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        return AnalysisResponse(
            success=False,
            error=str(e),
        )


@router.post("/capture-and-analyze", response_model=AnalysisResponse)
async def capture_and_analyze(request: CaptureAndAnalyzeRequest):
    """
    Ekran yakala ve hemen analiz et.
    
    Tek adımda capture + analyze.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        
        # Check if vision is available
        if not system.is_vision_available():
            return AnalysisResponse(
                success=False,
                error="Vision model not available. Make sure Ollama is running with llava model.",
            )
        
        mode = _get_capture_mode(request.mode)
        region = tuple(request.region) if request.region and len(request.region) == 4 else None
        
        result = system.capture_and_analyze(
            prompt=request.prompt,
            mode=mode,
            monitor_index=request.monitor_index,
            region=region,
        )
        
        return AnalysisResponse(
            success=result.success,
            response=result.response if result.success else None,
            model=result.model,
            duration_ms=result.duration_ms,
            screenshot_id=result.screenshot_id,
            error=result.error if not result.success else None,
        )
        
    except Exception as e:
        logger.error(f"Capture and analyze error: {e}")
        return AnalysisResponse(
            success=False,
            error=str(e),
        )


@router.get("/screenshots")
async def list_screenshots(
    limit: int = Query(default=10, ge=1, le=100),
):
    """
    Cache'deki screenshot'ları listele.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        screenshots = system.list_screenshots(limit)
        
        return {
            "success": True,
            "screenshots": screenshots,
            "count": len(screenshots),
        }
    except Exception as e:
        logger.error(f"List screenshots error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screenshots/{screenshot_id}")
async def get_screenshot(screenshot_id: str):
    """
    Belirli bir screenshot'ı al.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        result = system.get_screenshot(screenshot_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="Screenshot not found")
        
        image, metadata = result
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "success": True,
            "screenshot": {
                **metadata.to_dict(),
                "image_base64": image_b64,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get screenshot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/screenshots/{screenshot_id}")
async def delete_screenshot(screenshot_id: str):
    """
    Screenshot'ı sil.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        deleted = system.delete_screenshot(screenshot_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Screenshot not found")
        
        return {
            "success": True,
            "message": f"Screenshot {screenshot_id} deleted",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete screenshot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_cache():
    """
    Screenshot cache'ini temizle.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        count = system.clear_cache()
        
        return {
            "success": True,
            "message": f"Cleared {count} screenshots from cache",
            "deleted_count": count,
        }
        
    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last")
async def get_last_screenshot():
    """
    Son yakalanan screenshot'ı al.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        image_b64 = system.get_last_screenshot_base64()
        
        if image_b64 is None:
            raise HTTPException(
                status_code=404,
                detail="No screenshot captured yet. Call /capture first."
            )
        
        metadata = system._last_metadata
        
        return {
            "success": True,
            "screenshot": {
                **(metadata.to_dict() if metadata else {}),
                "image_base64": image_b64,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get last screenshot error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/last/image")
async def get_last_screenshot_image():
    """
    Son yakalanan screenshot'ı JPEG olarak döndür.
    """
    _check_available()
    
    try:
        system = get_screen_capture_system()
        
        if system._last_screenshot is None:
            raise HTTPException(
                status_code=404,
                detail="No screenshot captured yet. Call /capture first."
            )
        
        buffer = io.BytesIO()
        system._last_screenshot.save(buffer, format="JPEG", quality=85)
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get last screenshot image error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
