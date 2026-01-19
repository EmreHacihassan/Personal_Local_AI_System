"""
Enterprise AI Assistant - Screen Capture & Analysis System
===========================================================

Local ekran görüntüsü yakalama ve LLM ile analiz sistemi.
Tamamen local çalışır - hiçbir veri dışarı gönderilmez.

Features:
- Ekran görüntüsü yakalama (tam ekran, pencere, alan seçimi)
- Local LLM ile görüntü analizi (LLaVA via Ollama)
- Screenshot history ve caching
- Görüntü optimizasyonu
- Privacy-first tasarım

Dependencies:
- mss: Cross-platform screen capture
- Pillow: Image processing
- ollama: Local LLM inference

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import os
import io
import base64
import time
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json

# Image processing
try:
    from PIL import Image, ImageGrab, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

# Screen capture
try:
    import mss
    import mss.tools
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    mss = None

# Local LLM
try:
    import ollama
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False
    ollama = None

from .config import settings
from .logger import get_logger

logger = get_logger("screen_capture")


# =============================================================================
# CONFIGURATION
# =============================================================================

class CaptureMode(Enum):
    """Ekran yakalama modları."""
    FULL_SCREEN = "full_screen"
    PRIMARY_MONITOR = "primary"
    ALL_MONITORS = "all_monitors"
    REGION = "region"
    WINDOW = "window"


@dataclass
class ScreenCaptureConfig:
    """Ekran yakalama konfigürasyonu."""
    # Capture settings
    default_mode: CaptureMode = CaptureMode.PRIMARY_MONITOR
    max_width: int = 1920
    max_height: int = 1080
    jpeg_quality: int = 85
    
    # Cache settings
    cache_enabled: bool = True
    cache_dir: str = ""
    max_cache_size_mb: int = 100
    cache_ttl_hours: int = 24
    
    # LLM settings
    vision_model: str = "llava"
    ollama_host: str = "http://localhost:11434"
    analysis_timeout: int = 120
    
    # Privacy
    blur_sensitive_areas: bool = False
    auto_cleanup: bool = True
    
    def __post_init__(self):
        if not self.cache_dir:
            self.cache_dir = str(settings.DATA_DIR / "screen_cache")


@dataclass
class ScreenshotMetadata:
    """Screenshot metadata."""
    id: str
    timestamp: datetime
    mode: CaptureMode
    width: int
    height: int
    size_bytes: int
    monitor_index: Optional[int] = None
    region: Optional[Tuple[int, int, int, int]] = None
    hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "mode": self.mode.value,
            "width": self.width,
            "height": self.height,
            "size_bytes": self.size_bytes,
            "monitor_index": self.monitor_index,
            "region": self.region,
            "hash": self.hash,
        }


@dataclass
class AnalysisResult:
    """Görüntü analiz sonucu."""
    success: bool
    response: str
    model: str
    timestamp: datetime
    duration_ms: float
    screenshot_id: str
    prompt: str
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "response": self.response,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "screenshot_id": self.screenshot_id,
            "prompt": self.prompt,
            "error": self.error,
        }


# =============================================================================
# SCREEN CAPTURE ENGINE
# =============================================================================

class ScreenCaptureEngine:
    """
    Ekran yakalama motoru.
    
    Cross-platform screen capture with optimization.
    """
    
    def __init__(self, config: Optional[ScreenCaptureConfig] = None):
        self.config = config or ScreenCaptureConfig()
        
        if not HAS_MSS:
            logger.warning("mss not installed, using PIL fallback")
        if not HAS_PIL:
            raise ImportError("Pillow is required for screen capture")
    
    def capture(
        self,
        mode: Optional[CaptureMode] = None,
        monitor_index: Optional[int] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Tuple[Optional[Image.Image], Optional[ScreenshotMetadata]]:
        """
        Ekran görüntüsü yakala.
        
        Args:
            mode: Yakalama modu
            monitor_index: Monitor indeksi (çoklu monitör için)
            region: Bölge (x, y, width, height)
            
        Returns:
            (PIL Image, Metadata) veya (None, None) hata durumunda
        """
        mode = mode or self.config.default_mode
        
        try:
            if HAS_MSS:
                return self._capture_with_mss(mode, monitor_index, region)
            else:
                return self._capture_with_pil(mode, region)
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None, None
    
    def _capture_with_mss(
        self,
        mode: CaptureMode,
        monitor_index: Optional[int],
        region: Optional[Tuple[int, int, int, int]],
    ) -> Tuple[Optional[Image.Image], Optional[ScreenshotMetadata]]:
        """MSS ile ekran yakala."""
        with mss.mss() as sct:
            if mode == CaptureMode.REGION and region:
                # Belirli bölge
                monitor = {
                    "left": region[0],
                    "top": region[1],
                    "width": region[2],
                    "height": region[3],
                }
            elif mode == CaptureMode.ALL_MONITORS:
                # Tüm monitörler
                monitor = sct.monitors[0]
            elif mode == CaptureMode.PRIMARY_MONITOR or monitor_index is None:
                # Ana monitör
                monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            else:
                # Belirli monitör
                idx = min(monitor_index + 1, len(sct.monitors) - 1)
                monitor = sct.monitors[idx]
            
            # Capture
            screenshot = sct.grab(monitor)
            
            # Convert to PIL
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Optimize
            img = self._optimize_image(img)
            
            # Metadata
            img_bytes = self._image_to_bytes(img)
            metadata = ScreenshotMetadata(
                id=self._generate_id(),
                timestamp=datetime.now(),
                mode=mode,
                width=img.width,
                height=img.height,
                size_bytes=len(img_bytes),
                monitor_index=monitor_index,
                region=region,
                hash=hashlib.md5(img_bytes).hexdigest(),
            )
            
            return img, metadata
    
    def _capture_with_pil(
        self,
        mode: CaptureMode,
        region: Optional[Tuple[int, int, int, int]],
    ) -> Tuple[Optional[Image.Image], Optional[ScreenshotMetadata]]:
        """PIL ile ekran yakala (Windows fallback)."""
        try:
            if mode == CaptureMode.REGION and region:
                # Bölge: (left, top, right, bottom)
                bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
                img = ImageGrab.grab(bbox=bbox)
            else:
                # Tam ekran
                img = ImageGrab.grab(all_screens=(mode == CaptureMode.ALL_MONITORS))
            
            # Optimize
            img = self._optimize_image(img)
            
            # Metadata
            img_bytes = self._image_to_bytes(img)
            metadata = ScreenshotMetadata(
                id=self._generate_id(),
                timestamp=datetime.now(),
                mode=mode,
                width=img.width,
                height=img.height,
                size_bytes=len(img_bytes),
                region=region,
                hash=hashlib.md5(img_bytes).hexdigest(),
            )
            
            return img, metadata
            
        except Exception as e:
            logger.error(f"PIL capture failed: {e}")
            return None, None
    
    def _optimize_image(self, img: Image.Image) -> Image.Image:
        """Görüntüyü optimize et."""
        # Boyut kontrolü
        if img.width > self.config.max_width or img.height > self.config.max_height:
            ratio = min(
                self.config.max_width / img.width,
                self.config.max_height / img.height
            )
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # RGB'ye dönüştür
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        return img
    
    def _image_to_bytes(self, img: Image.Image, format: str = "JPEG") -> bytes:
        """Görüntüyü byte'a dönüştür."""
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=self.config.jpeg_quality)
        return buffer.getvalue()
    
    def _generate_id(self) -> str:
        """Unique ID oluştur."""
        return f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    
    def get_monitors_info(self) -> List[Dict[str, Any]]:
        """Monitör bilgilerini al."""
        monitors = []
        
        try:
            if HAS_MSS:
                with mss.mss() as sct:
                    for i, mon in enumerate(sct.monitors[1:], 1):  # Skip "all monitors"
                        monitors.append({
                            "index": i - 1,
                            "left": mon["left"],
                            "top": mon["top"],
                            "width": mon["width"],
                            "height": mon["height"],
                            "is_primary": i == 1,
                        })
        except Exception as e:
            logger.error(f"Get monitors failed: {e}")
        
        return monitors


# =============================================================================
# VISION ANALYZER
# =============================================================================

class LocalVisionAnalyzer:
    """
    Local LLM ile görüntü analizi.
    
    Ollama üzerinden LLaVA kullanır.
    """
    
    def __init__(self, config: Optional[ScreenCaptureConfig] = None):
        self.config = config or ScreenCaptureConfig()
        self._client = None
        self._model_available = False
        self._lock = threading.Lock()
    
    def _ensure_client(self, auto_pull: bool = False) -> bool:
        """
        Ollama client'ı hazırla.
        
        Args:
            auto_pull: True ise eksik modeli otomatik indir (uzun sürer)
        """
        if not HAS_OLLAMA:
            logger.error("ollama package not installed")
            return False
        
        try:
            # Test connection with timeout
            response = ollama.list()
            
            # Check if vision model is available
            models = [m.get("name", "").split(":")[0] for m in response.get("models", [])]
            self._model_available = self.config.vision_model in models
            
            if not self._model_available and auto_pull:
                logger.warning(f"Vision model '{self.config.vision_model}' not found. Available: {models}")
                # Try to pull (only if explicitly requested)
                logger.info(f"Pulling {self.config.vision_model}...")
                ollama.pull(self.config.vision_model)
                self._model_available = True
            elif not self._model_available:
                logger.debug(f"Vision model '{self.config.vision_model}' not available (auto_pull=False)")
            
            return True
            
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False
    
    def analyze(
        self,
        image: Union[Image.Image, bytes, str],
        prompt: str = "Bu ekran görüntüsünde ne görüyorsun? Detaylı açıkla.",
        screenshot_id: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Görüntüyü analiz et.
        
        Args:
            image: PIL Image, bytes veya base64 string
            prompt: Analiz sorusu
            screenshot_id: Screenshot ID (opsiyonel)
            
        Returns:
            AnalysisResult
        """
        start_time = time.time()
        
        # Convert image to base64
        try:
            if isinstance(image, Image.Image):
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=85)
                image_bytes = buffer.getvalue()
                image_b64 = base64.b64encode(image_bytes).decode()
            elif isinstance(image, bytes):
                image_b64 = base64.b64encode(image).decode()
            else:
                image_b64 = image  # Assume already base64
        except Exception as e:
            return AnalysisResult(
                success=False,
                response="",
                model=self.config.vision_model,
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                screenshot_id=screenshot_id or "unknown",
                prompt=prompt,
                error=f"Image conversion failed: {e}",
            )
        
        # Ensure client (with auto_pull for actual analysis)
        with self._lock:
            if not self._ensure_client(auto_pull=True):
                return AnalysisResult(
                    success=False,
                    response="",
                    model=self.config.vision_model,
                    timestamp=datetime.now(),
                    duration_ms=(time.time() - start_time) * 1000,
                    screenshot_id=screenshot_id or "unknown",
                    prompt=prompt,
                    error="Ollama connection failed",
                )
        
        # Analyze
        try:
            response = ollama.chat(
                model=self.config.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_b64],
                    }
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 1024,
                },
            )
            
            result_text = response.get("message", {}).get("content", "")
            
            return AnalysisResult(
                success=True,
                response=result_text,
                model=self.config.vision_model,
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                screenshot_id=screenshot_id or "unknown",
                prompt=prompt,
            )
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return AnalysisResult(
                success=False,
                response="",
                model=self.config.vision_model,
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                screenshot_id=screenshot_id or "unknown",
                prompt=prompt,
                error=str(e),
            )
    
    def is_available(self) -> bool:
        """Vision modeli mevcut mu? (Hızlı kontrol, pull yapmaz)"""
        with self._lock:
            return self._ensure_client(auto_pull=False) and self._model_available


# =============================================================================
# SCREENSHOT CACHE
# =============================================================================

class ScreenshotCache:
    """Screenshot cache yönetimi."""
    
    def __init__(self, config: Optional[ScreenCaptureConfig] = None):
        self.config = config or ScreenCaptureConfig()
        self.cache_dir = Path(self.config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._metadata_file = self.cache_dir / "cache_metadata.json"
        self._metadata: Dict[str, Dict] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """Metadata'yı yükle."""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file) as f:
                    self._metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Cache metadata load failed: {e}")
            self._metadata = {}
    
    def _save_metadata(self):
        """Metadata'yı kaydet."""
        try:
            with open(self._metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Cache metadata save failed: {e}")
    
    def save(
        self,
        image: Image.Image,
        metadata: ScreenshotMetadata,
    ) -> bool:
        """Screenshot'ı cache'e kaydet."""
        if not self.config.cache_enabled:
            return False
        
        try:
            # Save image
            image_path = self.cache_dir / f"{metadata.id}.jpg"
            image.save(image_path, "JPEG", quality=self.config.jpeg_quality)
            
            # Update metadata
            self._metadata[metadata.id] = {
                **metadata.to_dict(),
                "path": str(image_path),
            }
            self._save_metadata()
            
            # Cleanup if needed
            self._cleanup_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache save failed: {e}")
            return False
    
    def get(self, screenshot_id: str) -> Optional[Tuple[Image.Image, ScreenshotMetadata]]:
        """Cache'den screenshot al."""
        if screenshot_id not in self._metadata:
            return None
        
        try:
            meta = self._metadata[screenshot_id]
            image_path = Path(meta["path"])
            
            if not image_path.exists():
                del self._metadata[screenshot_id]
                self._save_metadata()
                return None
            
            image = Image.open(image_path)
            
            return image, ScreenshotMetadata(
                id=meta["id"],
                timestamp=datetime.fromisoformat(meta["timestamp"]),
                mode=CaptureMode(meta["mode"]),
                width=meta["width"],
                height=meta["height"],
                size_bytes=meta["size_bytes"],
                monitor_index=meta.get("monitor_index"),
                region=tuple(meta["region"]) if meta.get("region") else None,
                hash=meta.get("hash"),
            )
            
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def get_latest(self) -> Optional[Tuple[Image.Image, ScreenshotMetadata]]:
        """En son screenshot'ı al."""
        if not self._metadata:
            return None
        
        # Sort by timestamp
        sorted_ids = sorted(
            self._metadata.keys(),
            key=lambda x: self._metadata[x].get("timestamp", ""),
            reverse=True
        )
        
        if sorted_ids:
            return self.get(sorted_ids[0])
        return None
    
    def list_screenshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Screenshot listesi."""
        sorted_items = sorted(
            self._metadata.values(),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        return sorted_items[:limit]
    
    def delete(self, screenshot_id: str) -> bool:
        """Screenshot'ı sil."""
        if screenshot_id not in self._metadata:
            return False
        
        try:
            meta = self._metadata[screenshot_id]
            image_path = Path(meta["path"])
            
            if image_path.exists():
                image_path.unlink()
            
            del self._metadata[screenshot_id]
            self._save_metadata()
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed: {e}")
            return False
    
    def clear(self) -> int:
        """Tüm cache'i temizle."""
        count = 0
        for screenshot_id in list(self._metadata.keys()):
            if self.delete(screenshot_id):
                count += 1
        return count
    
    def _cleanup_if_needed(self):
        """Cache boyutunu kontrol et ve gerekirse temizle."""
        try:
            # Calculate total size
            total_size = sum(
                Path(m["path"]).stat().st_size
                for m in self._metadata.values()
                if Path(m["path"]).exists()
            )
            
            max_size = self.config.max_cache_size_mb * 1024 * 1024
            
            if total_size > max_size:
                # Delete oldest
                sorted_ids = sorted(
                    self._metadata.keys(),
                    key=lambda x: self._metadata[x].get("timestamp", "")
                )
                
                while total_size > max_size * 0.8 and sorted_ids:
                    oldest_id = sorted_ids.pop(0)
                    if oldest_id in self._metadata:
                        path = Path(self._metadata[oldest_id]["path"])
                        if path.exists():
                            size = path.stat().st_size
                            self.delete(oldest_id)
                            total_size -= size
            
            # Delete expired
            cutoff = datetime.now() - timedelta(hours=self.config.cache_ttl_hours)
            for sid, meta in list(self._metadata.items()):
                try:
                    ts = datetime.fromisoformat(meta["timestamp"])
                    if ts < cutoff:
                        self.delete(sid)
                except Exception:
                    pass
                    
        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        total_size = 0
        for m in self._metadata.values():
            try:
                total_size += Path(m["path"]).stat().st_size
            except Exception:
                pass
        
        return {
            "count": len(self._metadata),
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.config.max_cache_size_mb,
            "cache_dir": str(self.cache_dir),
        }


# =============================================================================
# MAIN SCREEN CAPTURE SYSTEM
# =============================================================================

class ScreenCaptureSystem:
    """
    Ana ekran yakalama ve analiz sistemi.
    
    Kullanım:
        system = ScreenCaptureSystem()
        
        # Ekran yakala
        image, metadata = system.capture()
        
        # Analiz et
        result = system.analyze("Bu ekranda ne var?")
        
        # Tek adımda
        result = system.capture_and_analyze("Ekranda ne görüyorsun?")
    """
    
    def __init__(self, config: Optional[ScreenCaptureConfig] = None):
        self.config = config or ScreenCaptureConfig()
        
        self._capture_engine = ScreenCaptureEngine(self.config)
        self._analyzer = LocalVisionAnalyzer(self.config)
        self._cache = ScreenshotCache(self.config)
        
        self._last_screenshot: Optional[Image.Image] = None
        self._last_metadata: Optional[ScreenshotMetadata] = None
        
        logger.info("ScreenCaptureSystem initialized")
    
    def capture(
        self,
        mode: Optional[CaptureMode] = None,
        monitor_index: Optional[int] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
        save_to_cache: bool = True,
    ) -> Tuple[Optional[Image.Image], Optional[ScreenshotMetadata]]:
        """
        Ekran görüntüsü yakala.
        
        Returns:
            (PIL Image, Metadata)
        """
        image, metadata = self._capture_engine.capture(mode, monitor_index, region)
        
        if image and metadata:
            self._last_screenshot = image
            self._last_metadata = metadata
            
            if save_to_cache:
                self._cache.save(image, metadata)
        
        return image, metadata
    
    def analyze(
        self,
        prompt: str = "Bu ekran görüntüsünde ne görüyorsun? Detaylı açıkla.",
        image: Optional[Image.Image] = None,
    ) -> AnalysisResult:
        """
        Son yakalanan veya verilen görüntüyü analiz et.
        
        Args:
            prompt: Analiz sorusu
            image: Analiz edilecek görüntü (opsiyonel, yoksa son yakalanan)
        """
        target_image = image or self._last_screenshot
        screenshot_id = self._last_metadata.id if self._last_metadata else "unknown"
        
        if target_image is None:
            return AnalysisResult(
                success=False,
                response="",
                model=self.config.vision_model,
                timestamp=datetime.now(),
                duration_ms=0,
                screenshot_id=screenshot_id,
                prompt=prompt,
                error="No screenshot available. Call capture() first.",
            )
        
        return self._analyzer.analyze(target_image, prompt, screenshot_id)
    
    def capture_and_analyze(
        self,
        prompt: str = "Bu ekran görüntüsünde ne görüyorsun?",
        mode: Optional[CaptureMode] = None,
        monitor_index: Optional[int] = None,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> AnalysisResult:
        """
        Tek adımda yakala ve analiz et.
        
        Args:
            prompt: Analiz sorusu
            mode: Yakalama modu
            monitor_index: Monitör indeksi
            region: Bölge koordinatları
            
        Returns:
            AnalysisResult
        """
        image, metadata = self.capture(mode, monitor_index, region)
        
        if image is None:
            return AnalysisResult(
                success=False,
                response="",
                model=self.config.vision_model,
                timestamp=datetime.now(),
                duration_ms=0,
                screenshot_id="unknown",
                prompt=prompt,
                error="Screen capture failed",
            )
        
        return self._analyzer.analyze(image, prompt, metadata.id)
    
    def analyze_from_cache(
        self,
        screenshot_id: str,
        prompt: str = "Bu ekran görüntüsünde ne görüyorsun?",
    ) -> AnalysisResult:
        """Cache'deki bir screenshot'ı analiz et."""
        cached = self._cache.get(screenshot_id)
        
        if cached is None:
            return AnalysisResult(
                success=False,
                response="",
                model=self.config.vision_model,
                timestamp=datetime.now(),
                duration_ms=0,
                screenshot_id=screenshot_id,
                prompt=prompt,
                error=f"Screenshot not found in cache: {screenshot_id}",
            )
        
        image, metadata = cached
        return self._analyzer.analyze(image, prompt, metadata.id)
    
    def get_monitors(self) -> List[Dict[str, Any]]:
        """Mevcut monitörleri listele."""
        return self._capture_engine.get_monitors_info()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri."""
        return self._cache.get_stats()
    
    def list_screenshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Son screenshot'ları listele."""
        return self._cache.list_screenshots(limit)
    
    def get_screenshot(self, screenshot_id: str) -> Optional[Tuple[Image.Image, ScreenshotMetadata]]:
        """ID ile screenshot al."""
        return self._cache.get(screenshot_id)
    
    def delete_screenshot(self, screenshot_id: str) -> bool:
        """Screenshot'ı sil."""
        return self._cache.delete(screenshot_id)
    
    def clear_cache(self) -> int:
        """Cache'i temizle."""
        return self._cache.clear()
    
    def is_vision_available(self) -> bool:
        """Vision modeli mevcut mu?"""
        return self._analyzer.is_available()
    
    def get_last_screenshot_base64(self) -> Optional[str]:
        """Son screenshot'ı base64 olarak al."""
        if self._last_screenshot is None:
            return None
        
        buffer = io.BytesIO()
        self._last_screenshot.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode()
    
    def get_status(self) -> Dict[str, Any]:
        """Sistem durumu."""
        return {
            "vision_available": self.is_vision_available(),
            "vision_model": self.config.vision_model,
            "monitors": self.get_monitors(),
            "cache": self.get_cache_stats(),
            "last_screenshot": self._last_metadata.to_dict() if self._last_metadata else None,
            "capture_backend": "mss" if HAS_MSS else "PIL",
        }


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_screen_system: Optional[ScreenCaptureSystem] = None


def get_screen_capture_system(config: Optional[ScreenCaptureConfig] = None) -> ScreenCaptureSystem:
    """Screen capture system instance al."""
    global _screen_system
    
    if _screen_system is None:
        _screen_system = ScreenCaptureSystem(config)
    
    return _screen_system


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ScreenCaptureSystem",
    "ScreenCaptureConfig",
    "ScreenCaptureEngine",
    "LocalVisionAnalyzer",
    "ScreenshotCache",
    "CaptureMode",
    "ScreenshotMetadata",
    "AnalysisResult",
    "get_screen_capture_system",
]
