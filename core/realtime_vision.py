"""
🖥️👁️ Real-Time Vision System
==============================

Gerçek zamanlı ekran paylaşımı ve AI görüntü analizi.
Tamamen LOCAL çalışır - hiçbir veri dışarı gönderilmez.

Features:
- 🎥 Real-time screen streaming
- 🧠 Multi-modal reasoning (görüntü + metin)
- 🔄 Continuous screen monitoring
- 🎯 UI element detection
- 📝 Screen annotation
- 💬 Conversational screen Q&A
- 🖱️ Mouse/keyboard interaction tracking
- 🔍 OCR text extraction
- 📊 Screen change detection

Tech Stack:
- mss/PIL: Screen capture
- Ollama + LLaVA: Local vision AI
- asyncio: Async processing
- WebSocket: Real-time streaming

Author: Enterprise AI Assistant
Version: 2.0.0
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import queue
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any, AsyncGenerator, Callable, Dict, List, 
    Optional, Tuple, Union, Set
)
from concurrent.futures import ThreadPoolExecutor

# Image processing
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

# Screen capture
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

# OCR (optional)
try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Async HTTP
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from .config import settings
from .logger import get_logger
from .screen_capture import (
    ScreenCaptureSystem, 
    ScreenCaptureConfig, 
    CaptureMode,
    AnalysisResult,
    ScreenshotMetadata,
    get_screen_capture_system
)

logger = get_logger("realtime_vision")


# =============================================================================
# CONFIGURATION
# =============================================================================

class StreamQuality(str, Enum):
    """Streaming kalitesi."""
    LOW = "low"          # 480p, 5 FPS
    MEDIUM = "medium"    # 720p, 10 FPS
    HIGH = "high"        # 1080p, 15 FPS
    ULTRA = "ultra"      # Native, 30 FPS


class VisionMode(str, Enum):
    """Vision modları."""
    DESCRIBE = "describe"           # Genel açıklama
    UI_ANALYSIS = "ui_analysis"     # UI element analizi
    TEXT_EXTRACT = "text_extract"   # OCR / metin çıkarma
    CODE_REVIEW = "code_review"     # Kod analizi
    ERROR_DETECT = "error_detect"   # Hata/uyarı tespiti
    TUTORIAL = "tutorial"           # Eğitim/rehber modu
    COMPARE = "compare"             # İki frame karşılaştırma
    CUSTOM = "custom"               # Özel prompt


@dataclass
class VisionConfig:
    """Real-time vision konfigürasyonu."""
    # Model settings
    model: str = "llava"
    ollama_host: str = "http://localhost:11434"
    timeout: int = 120
    
    # Stream settings
    quality: StreamQuality = StreamQuality.MEDIUM
    target_fps: float = 10.0
    max_queue_size: int = 10
    
    # Analysis settings
    auto_analyze_interval: float = 2.0  # saniye
    change_detection_threshold: float = 0.05  # %5 değişim
    min_analysis_interval: float = 0.5
    
    # Memory
    context_history_size: int = 5
    max_image_dimension: int = 1920
    jpeg_quality: int = 80
    
    # Features
    ocr_enabled: bool = True
    change_detection_enabled: bool = True
    ui_detection_enabled: bool = True
    
    @property
    def quality_settings(self) -> Dict[str, Any]:
        """Kalite ayarları."""
        settings_map = {
            StreamQuality.LOW: {"width": 854, "height": 480, "fps": 5},
            StreamQuality.MEDIUM: {"width": 1280, "height": 720, "fps": 10},
            StreamQuality.HIGH: {"width": 1920, "height": 1080, "fps": 15},
            StreamQuality.ULTRA: {"width": 2560, "height": 1440, "fps": 30},
        }
        return settings_map.get(self.quality, settings_map[StreamQuality.MEDIUM])


@dataclass
class FrameData:
    """Tek frame verisi."""
    id: str
    timestamp: datetime
    image: Image.Image
    image_base64: str
    width: int
    height: int
    hash: str
    size_bytes: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "width": self.width,
            "height": self.height,
            "hash": self.hash,
            "size_bytes": self.size_bytes,
            "metadata": self.metadata,
        }


@dataclass
class VisionContext:
    """Görüşme bağlamı."""
    session_id: str
    frames: deque = field(default_factory=lambda: deque(maxlen=10))
    messages: List[Dict[str, str]] = field(default_factory=list)
    analysis_history: List[AnalysisResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_frame(self, frame: FrameData):
        """Frame ekle."""
        self.frames.append(frame)
        self.last_activity = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Mesaj ekle."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now()
    
    def get_conversation_context(self, max_messages: int = 10) -> str:
        """Konuşma bağlamı."""
        recent = self.messages[-max_messages:]
        return "\n".join([
            f"{m['role']}: {m['content']}" 
            for m in recent
        ])


@dataclass
class UIElement:
    """Tespit edilen UI elementi."""
    element_type: str  # button, input, text, icon, menu, etc.
    text: Optional[str]
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class ScreenAnalysis:
    """Detaylı ekran analizi sonucu."""
    success: bool
    frame_id: str
    timestamp: datetime
    duration_ms: float
    
    # Analiz sonuçları
    description: str = ""
    ui_elements: List[UIElement] = field(default_factory=list)
    detected_text: str = ""
    detected_errors: List[str] = field(default_factory=list)
    detected_apps: List[str] = field(default_factory=list)
    
    # AI yanıtı
    ai_response: str = ""
    suggestions: List[str] = field(default_factory=list)
    
    # Meta
    model: str = ""
    mode: VisionMode = VisionMode.DESCRIBE
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "description": self.description,
            "ui_elements": [
                {
                    "type": e.element_type,
                    "text": e.text,
                    "bounds": e.bounds,
                    "confidence": e.confidence,
                }
                for e in self.ui_elements
            ],
            "detected_text": self.detected_text,
            "detected_errors": self.detected_errors,
            "detected_apps": self.detected_apps,
            "ai_response": self.ai_response,
            "suggestions": self.suggestions,
            "model": self.model,
            "mode": self.mode.value,
            "error": self.error,
        }


# =============================================================================
# VISION PROMPTS
# =============================================================================

class VisionPrompts:
    """Vision modları için optimize edilmiş promptlar."""
    
    DESCRIBE = """Bu ekran görüntüsünü analiz et ve detaylı açıkla:
1. Hangi uygulama/pencere açık?
2. Ekranda ne görünüyor?
3. Kullanıcı ne yapıyor olabilir?
4. Önemli UI elementleri neler?

Türkçe ve detaylı yanıt ver."""

    UI_ANALYSIS = """Bu ekran görüntüsündeki UI elementlerini analiz et:
1. Tüm butonları, menüleri, input alanlarını listele
2. Her elementin konumunu ve işlevini açıkla
3. Tıklanabilir alanları belirt
4. UI hiyerarşisini açıkla

JSON formatında yanıt ver:
{
    "application": "uygulama adı",
    "elements": [
        {"type": "button/input/menu/text", "label": "...", "location": "üst/sol/sağ/alt", "action": "..."}
    ],
    "layout": "açıklama"
}"""

    TEXT_EXTRACT = """Bu ekran görüntüsündeki TÜM metinleri oku ve listele:
1. Başlıklar
2. Menü öğeleri
3. Buton yazıları
4. Giriş alanlarındaki metinler
5. Hata/uyarı mesajları
6. Durum çubuğu bilgileri

Okunabilir sırayla, gruplandırarak listele."""

    CODE_REVIEW = """Bu ekran görüntüsünde kod görüyorum. Analiz et:
1. Hangi programlama dili?
2. Kodun ne yaptığını açıkla
3. Görünen hataları veya sorunları belirt
4. İyileştirme önerileri sun
5. Eğer hata mesajı varsa çözümünü öner

Detaylı ve teknik yanıt ver."""

    ERROR_DETECT = """Bu ekran görüntüsünde hata, uyarı veya sorun var mı?
1. Kırmızı/sarı uyarı işaretleri
2. Error/Exception mesajları
3. Dialog boxes
4. Başarısız işlem göstergeleri
5. Sistem hataları

Bulunan HER hatayı detaylıca açıkla ve çözüm öner."""

    TUTORIAL = """Bu ekran görüntüsünü kullanarak kullanıcıya rehberlik et:
1. Ekranda ne görünüyor?
2. Kullanıcı ne yapmalı? (adım adım)
3. Dikkat edilmesi gerekenler
4. Olası hatalardan kaçınma
5. Sonraki adımlar

Basit ve anlaşılır dille Türkçe açıkla."""

    COMPARE = """Bu iki ekran görüntüsünü karşılaştır:
1. Ne değişti?
2. Hangi elementler eklendi/silindi?
3. Pozisyon değişiklikleri
4. İçerik farklılıkları
5. Durum değişiklikleri

Değişiklikleri detaylıca listele."""

    @classmethod
    def get_prompt(cls, mode: VisionMode, custom_prompt: Optional[str] = None) -> str:
        """Mode'a göre prompt al."""
        if mode == VisionMode.CUSTOM and custom_prompt:
            return custom_prompt
        
        prompts = {
            VisionMode.DESCRIBE: cls.DESCRIBE,
            VisionMode.UI_ANALYSIS: cls.UI_ANALYSIS,
            VisionMode.TEXT_EXTRACT: cls.TEXT_EXTRACT,
            VisionMode.CODE_REVIEW: cls.CODE_REVIEW,
            VisionMode.ERROR_DETECT: cls.ERROR_DETECT,
            VisionMode.TUTORIAL: cls.TUTORIAL,
            VisionMode.COMPARE: cls.COMPARE,
        }
        return prompts.get(mode, cls.DESCRIBE)


# =============================================================================
# SCREEN STREAM MANAGER
# =============================================================================

class ScreenStreamManager:
    """
    Ekran streaming yöneticisi.
    
    Gerçek zamanlı ekran yakalama ve frame queue yönetimi.
    """
    
    def __init__(self, config: VisionConfig):
        self.config = config
        self._running = False
        self._frame_queue: queue.Queue = queue.Queue(maxsize=config.max_queue_size)
        self._capture_thread: Optional[threading.Thread] = None
        self._last_frame_hash: Optional[str] = None
        self._frame_count = 0
        self._capture_system = get_screen_capture_system()
        self._subscribers: Set[asyncio.Queue] = set()
        self._lock = threading.Lock()
        
        logger.info("ScreenStreamManager initialized")
    
    def start(self):
        """Streaming başlat."""
        if self._running:
            return
        
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()
        logger.info("Screen streaming started")
    
    def stop(self):
        """Streaming durdur."""
        self._running = False
        if self._capture_thread:
            self._capture_thread.join(timeout=2)
        logger.info("Screen streaming stopped")
    
    def _capture_loop(self):
        """Ana capture döngüsü."""
        quality = self.config.quality_settings
        target_interval = 1.0 / quality["fps"]
        
        while self._running:
            start_time = time.time()
            
            try:
                # Capture
                frame = self._capture_frame()
                
                if frame:
                    # Change detection
                    if self.config.change_detection_enabled:
                        if self._last_frame_hash and frame.hash == self._last_frame_hash:
                            # Değişiklik yok, atla
                            elapsed = time.time() - start_time
                            sleep_time = max(0, target_interval - elapsed)
                            time.sleep(sleep_time)
                            continue
                    
                    self._last_frame_hash = frame.hash
                    
                    # Queue'ya ekle
                    try:
                        self._frame_queue.put_nowait(frame)
                    except queue.Full:
                        # Eski frame'i çıkar
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait(frame)
                        except queue.Empty:
                            pass
                    
                    # Subscriber'lara bildir
                    self._notify_subscribers(frame)
                    
                    self._frame_count += 1
                    
            except Exception as e:
                logger.error(f"Capture error: {e}")
            
            # FPS kontrolü
            elapsed = time.time() - start_time
            sleep_time = max(0, target_interval - elapsed)
            time.sleep(sleep_time)
    
    def _capture_frame(self) -> Optional[FrameData]:
        """Tek frame yakala."""
        try:
            image, metadata = self._capture_system.capture(
                mode=CaptureMode.PRIMARY_MONITOR,
                save_to_cache=False
            )
            
            if image is None:
                return None
            
            # Resize if needed
            quality = self.config.quality_settings
            if image.width > quality["width"] or image.height > quality["height"]:
                ratio = min(quality["width"] / image.width, quality["height"] / image.height)
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.config.jpeg_quality)
            image_bytes = buffer.getvalue()
            image_b64 = base64.b64encode(image_bytes).decode()
            
            # Hash for change detection
            frame_hash = hashlib.md5(image_bytes).hexdigest()[:16]
            
            return FrameData(
                id=f"frame_{datetime.now().strftime('%H%M%S')}_{self._frame_count}",
                timestamp=datetime.now(),
                image=image,
                image_base64=image_b64,
                width=image.width,
                height=image.height,
                hash=frame_hash,
                size_bytes=len(image_bytes),
            )
            
        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            return None
    
    def _notify_subscribers(self, frame: FrameData):
        """Subscriber'lara frame bildir."""
        with self._lock:
            for sub_queue in list(self._subscribers):
                try:
                    sub_queue.put_nowait(frame)
                except asyncio.QueueFull:
                    pass
                except Exception:
                    self._subscribers.discard(sub_queue)
    
    def subscribe(self) -> asyncio.Queue:
        """Frame stream'e abone ol."""
        sub_queue = asyncio.Queue(maxsize=5)
        with self._lock:
            self._subscribers.add(sub_queue)
        return sub_queue
    
    def unsubscribe(self, sub_queue: asyncio.Queue):
        """Abonelikten çık."""
        with self._lock:
            self._subscribers.discard(sub_queue)
    
    def get_latest_frame(self) -> Optional[FrameData]:
        """Son frame'i al."""
        try:
            return self._frame_queue.get_nowait()
        except queue.Empty:
            return None
    
    def capture_single(self) -> Optional[FrameData]:
        """Tek frame yakala (streaming olmadan)."""
        return self._capture_frame()
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def frame_count(self) -> int:
        return self._frame_count
    
    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


# =============================================================================
# VISION ANALYZER ENGINE
# =============================================================================

class VisionAnalyzerEngine:
    """
    Görüntü analiz motoru.
    
    Ollama + LLaVA ile local vision AI.
    """
    
    def __init__(self, config: VisionConfig):
        self.config = config
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._analysis_lock = asyncio.Lock()
        self._last_analysis_time: float = 0
        
        logger.info(f"VisionAnalyzerEngine initialized with model: {config.model}")
    
    async def analyze(
        self,
        frame: FrameData,
        mode: VisionMode = VisionMode.DESCRIBE,
        custom_prompt: Optional[str] = None,
        context: Optional[VisionContext] = None,
    ) -> ScreenAnalysis:
        """
        Frame analizi yap.
        
        Args:
            frame: Analiz edilecek frame
            mode: Analiz modu
            custom_prompt: Özel prompt (mode=CUSTOM için)
            context: Konuşma bağlamı
            
        Returns:
            ScreenAnalysis
        """
        start_time = time.time()
        
        # Rate limiting
        async with self._analysis_lock:
            elapsed_since_last = time.time() - self._last_analysis_time
            if elapsed_since_last < self.config.min_analysis_interval:
                await asyncio.sleep(self.config.min_analysis_interval - elapsed_since_last)
        
        # Build prompt
        base_prompt = VisionPrompts.get_prompt(mode, custom_prompt)
        
        # Add context if available
        if context and context.messages:
            conversation = context.get_conversation_context(max_messages=5)
            prompt = f"""Önceki konuşma:
{conversation}

Şimdi bu ekran görüntüsünü analiz et:
{base_prompt}"""
        else:
            prompt = base_prompt
        
        # OCR ön işleme (opsiyonel)
        detected_text = ""
        if self.config.ocr_enabled and HAS_OCR and mode in [VisionMode.TEXT_EXTRACT, VisionMode.ERROR_DETECT]:
            detected_text = await self._extract_text_ocr(frame)
            if detected_text:
                prompt += f"\n\nOCR ile tespit edilen metin:\n{detected_text}"
        
        try:
            # Ollama API call
            response = await self._call_ollama(frame.image_base64, prompt)
            
            self._last_analysis_time = time.time()
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse response
            analysis = self._parse_response(
                response=response,
                frame=frame,
                mode=mode,
                duration_ms=duration_ms,
                detected_text=detected_text,
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return ScreenAnalysis(
                success=False,
                frame_id=frame.id,
                timestamp=datetime.now(),
                duration_ms=(time.time() - start_time) * 1000,
                model=self.config.model,
                mode=mode,
                error=str(e),
            )
    
    async def _call_ollama(self, image_base64: str, prompt: str) -> str:
        """Ollama API çağrısı."""
        if not HAS_AIOHTTP:
            # Sync fallback
            return await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._call_ollama_sync,
                image_base64,
                prompt
            )
        
        url = f"{self.config.ollama_host}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_base64]
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048,
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("message", {}).get("content", "")
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Ollama error {response.status}: {error_text}")
    
    def _call_ollama_sync(self, image_base64: str, prompt: str) -> str:
        """Sync Ollama çağrısı (fallback)."""
        try:
            import ollama
            
            response = ollama.chat(
                model=self.config.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [image_base64]
                    }
                ],
                options={
                    "temperature": 0.7,
                    "num_predict": 2048,
                }
            )
            
            return response.get("message", {}).get("content", "")
            
        except Exception as e:
            raise RuntimeError(f"Ollama sync call failed: {e}")
    
    async def _extract_text_ocr(self, frame: FrameData) -> str:
        """OCR ile metin çıkar."""
        if not HAS_OCR:
            return ""
        
        try:
            # Run in executor
            text = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: pytesseract.image_to_string(frame.image, lang="tur+eng")
            )
            return text.strip()
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""
    
    def _parse_response(
        self,
        response: str,
        frame: FrameData,
        mode: VisionMode,
        duration_ms: float,
        detected_text: str,
    ) -> ScreenAnalysis:
        """Yanıtı parse et."""
        analysis = ScreenAnalysis(
            success=True,
            frame_id=frame.id,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            model=self.config.model,
            mode=mode,
            ai_response=response,
            detected_text=detected_text,
        )
        
        # Mode-specific parsing
        if mode == VisionMode.UI_ANALYSIS:
            # Try to parse JSON
            try:
                if "{" in response and "}" in response:
                    json_str = response[response.index("{"):response.rindex("}") + 1]
                    data = json.loads(json_str)
                    
                    for elem in data.get("elements", []):
                        analysis.ui_elements.append(UIElement(
                            element_type=elem.get("type", "unknown"),
                            text=elem.get("label"),
                            bounds=(0, 0, 0, 0),  # Would need actual detection
                            confidence=0.8,
                        ))
                    
                    if "application" in data:
                        analysis.detected_apps.append(data["application"])
            except json.JSONDecodeError:
                pass
        
        elif mode == VisionMode.ERROR_DETECT:
            # Extract error lines
            lines = response.split("\n")
            for line in lines:
                lower = line.lower()
                if any(kw in lower for kw in ["error", "hata", "uyarı", "warning", "exception", "failed"]):
                    analysis.detected_errors.append(line.strip())
        
        # Extract suggestions (look for numbered lists or bullet points)
        lines = response.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("-", "•", "*")) or (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in ".):"):
                suggestion = stripped.lstrip("-•*0123456789.):").strip()
                if len(suggestion) > 10:
                    analysis.suggestions.append(suggestion)
        
        # Set description
        analysis.description = response[:500] if response else ""
        
        return analysis
    
    async def analyze_with_question(
        self,
        frame: FrameData,
        question: str,
        context: Optional[VisionContext] = None,
    ) -> ScreenAnalysis:
        """
        Ekran görüntüsüne soru sor.
        
        Args:
            frame: Frame
            question: Kullanıcı sorusu
            context: Konuşma bağlamı
            
        Returns:
            ScreenAnalysis
        """
        prompt = f"""Kullanıcı bu ekran görüntüsü hakkında soru soruyor:

SORU: {question}

Bu ekran görüntüsünü dikkatlice incele ve soruyu yanıtla.
Türkçe ve detaylı yanıt ver. Eğer soruda bahsedilen şey ekranda görünmüyorsa bunu belirt."""

        return await self.analyze(
            frame=frame,
            mode=VisionMode.CUSTOM,
            custom_prompt=prompt,
            context=context,
        )
    
    async def compare_frames(
        self,
        frame1: FrameData,
        frame2: FrameData,
    ) -> ScreenAnalysis:
        """İki frame'i karşılaştır."""
        # Combine images side by side
        combined = Image.new('RGB', (frame1.width + frame2.width, max(frame1.height, frame2.height)))
        combined.paste(frame1.image, (0, 0))
        combined.paste(frame2.image, (frame1.width, 0))
        
        # Convert to base64
        buffer = io.BytesIO()
        combined.save(buffer, format="JPEG", quality=self.config.jpeg_quality)
        combined_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Create combined frame
        combined_frame = FrameData(
            id=f"compare_{frame1.id}_{frame2.id}",
            timestamp=datetime.now(),
            image=combined,
            image_base64=combined_b64,
            width=combined.width,
            height=combined.height,
            hash="",
            size_bytes=len(buffer.getvalue()),
        )
        
        return await self.analyze(
            frame=combined_frame,
            mode=VisionMode.COMPARE,
        )


# =============================================================================
# REALTIME VISION SYSTEM
# =============================================================================

class RealtimeVisionSystem:
    """
    Ana real-time vision sistemi.
    
    Kullanım:
        system = RealtimeVisionSystem()
        
        # Tek seferlik analiz
        result = await system.analyze_screen("Ekranda ne var?")
        
        # Streaming başlat
        system.start_streaming()
        async for analysis in system.continuous_analysis():
            print(analysis.description)
        
        # Konuşma modu
        session = system.create_session()
        result = await system.ask(session, "Bu butona nasıl tıklarım?")
    """
    
    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig()
        
        self._stream_manager = ScreenStreamManager(self.config)
        self._analyzer = VisionAnalyzerEngine(self.config)
        self._sessions: Dict[str, VisionContext] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info("RealtimeVisionSystem initialized")
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Yeni görüşme oturumu oluştur."""
        if session_id is None:
            session_id = f"vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        self._sessions[session_id] = VisionContext(session_id=session_id)
        logger.info(f"Created vision session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[VisionContext]:
        """Oturum al."""
        return self._sessions.get(session_id)
    
    def end_session(self, session_id: str) -> bool:
        """Oturumu sonlandır."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Ended vision session: {session_id}")
            return True
        return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 1):
        """Eski oturumları temizle."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_delete = [
            sid for sid, ctx in self._sessions.items()
            if ctx.last_activity < cutoff
        ]
        for sid in to_delete:
            del self._sessions[sid]
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old sessions")
    
    # =========================================================================
    # SINGLE ANALYSIS
    # =========================================================================
    
    async def capture_and_analyze(
        self,
        mode: VisionMode = VisionMode.DESCRIBE,
        custom_prompt: Optional[str] = None,
    ) -> ScreenAnalysis:
        """
        Ekran yakala ve analiz et.
        
        Args:
            mode: Analiz modu
            custom_prompt: Özel prompt
            
        Returns:
            ScreenAnalysis
        """
        # Capture frame
        frame = self._stream_manager.capture_single()
        
        if frame is None:
            return ScreenAnalysis(
                success=False,
                frame_id="",
                timestamp=datetime.now(),
                duration_ms=0,
                error="Screen capture failed",
            )
        
        # Analyze
        return await self._analyzer.analyze(
            frame=frame,
            mode=mode,
            custom_prompt=custom_prompt,
        )
    
    async def analyze_screen(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> ScreenAnalysis:
        """
        Ekrana soru sor.
        
        Args:
            question: Soru
            session_id: Oturum ID (opsiyonel, context için)
            
        Returns:
            ScreenAnalysis
        """
        # Capture frame
        frame = self._stream_manager.capture_single()
        
        if frame is None:
            return ScreenAnalysis(
                success=False,
                frame_id="",
                timestamp=datetime.now(),
                duration_ms=0,
                error="Screen capture failed",
            )
        
        # Get context
        context = None
        if session_id:
            context = self.get_session(session_id)
            if context:
                context.add_frame(frame)
                context.add_message("user", question)
        
        # Analyze
        result = await self._analyzer.analyze_with_question(
            frame=frame,
            question=question,
            context=context,
        )
        
        # Update context
        if context and result.success:
            context.add_message("assistant", result.ai_response)
            context.analysis_history.append(result)
        
        return result
    
    async def ask(
        self,
        session_id: str,
        question: str,
    ) -> ScreenAnalysis:
        """
        Oturum içinde soru sor (context korunur).
        
        Args:
            session_id: Oturum ID
            question: Soru
            
        Returns:
            ScreenAnalysis
        """
        return await self.analyze_screen(question, session_id)
    
    # =========================================================================
    # STREAMING
    # =========================================================================
    
    def start_streaming(self):
        """Ekran streaming'i başlat."""
        self._stream_manager.start()
    
    def stop_streaming(self):
        """Ekran streaming'i durdur."""
        self._stream_manager.stop()
    
    async def get_frame_stream(self) -> AsyncGenerator[FrameData, None]:
        """
        Frame stream'i al (async generator).
        
        Usage:
            async for frame in system.get_frame_stream():
                # Process frame
                pass
        """
        sub_queue = self._stream_manager.subscribe()
        
        try:
            while self._stream_manager.is_running:
                try:
                    frame = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None, sub_queue.get
                        ),
                        timeout=1.0
                    )
                    yield frame
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break
        finally:
            self._stream_manager.unsubscribe(sub_queue)
    
    async def continuous_analysis(
        self,
        mode: VisionMode = VisionMode.DESCRIBE,
        analyze_every_n_frames: int = 10,
    ) -> AsyncGenerator[ScreenAnalysis, None]:
        """
        Sürekli analiz stream'i.
        
        Args:
            mode: Analiz modu
            analyze_every_n_frames: Her N frame'de bir analiz yap
            
        Yields:
            ScreenAnalysis
        """
        frame_count = 0
        
        async for frame in self.get_frame_stream():
            frame_count += 1
            
            if frame_count % analyze_every_n_frames == 0:
                analysis = await self._analyzer.analyze(frame, mode)
                yield analysis
    
    # =========================================================================
    # SPECIALIZED ANALYSIS
    # =========================================================================
    
    async def detect_errors(self) -> ScreenAnalysis:
        """Ekranda hata/uyarı tespit et."""
        return await self.capture_and_analyze(mode=VisionMode.ERROR_DETECT)
    
    async def extract_text(self) -> ScreenAnalysis:
        """Ekrandaki metinleri çıkar."""
        return await self.capture_and_analyze(mode=VisionMode.TEXT_EXTRACT)
    
    async def analyze_ui(self) -> ScreenAnalysis:
        """UI elementlerini analiz et."""
        return await self.capture_and_analyze(mode=VisionMode.UI_ANALYSIS)
    
    async def review_code(self) -> ScreenAnalysis:
        """Ekrandaki kodu incele."""
        return await self.capture_and_analyze(mode=VisionMode.CODE_REVIEW)
    
    async def get_tutorial(self, task: str) -> ScreenAnalysis:
        """Belirli bir görev için rehber al."""
        prompt = f"""Kullanıcı şunu yapmak istiyor: {task}

Bu ekran görüntüsüne bakarak:
1. Kullanıcının şu an nerede olduğunu açıkla
2. Hedefe ulaşmak için adım adım talimatlar ver
3. Dikkat edilmesi gereken noktaları belirt
4. Olası hataları ve çözümlerini açıkla

Türkçe ve anlaşılır şekilde yanıtla."""
        
        return await self.capture_and_analyze(
            mode=VisionMode.CUSTOM,
            custom_prompt=prompt,
        )
    
    async def compare_with_previous(self) -> Optional[ScreenAnalysis]:
        """Son frame ile önceki frame'i karşılaştır."""
        # Get two frames
        frame1 = self._stream_manager.capture_single()
        await asyncio.sleep(0.5)
        frame2 = self._stream_manager.capture_single()
        
        if frame1 and frame2:
            return await self._analyzer.compare_frames(frame1, frame2)
        return None
    
    # =========================================================================
    # STATUS & INFO
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Sistem durumu."""
        return {
            "streaming": self._stream_manager.is_running,
            "frame_count": self._stream_manager.frame_count,
            "subscribers": self._stream_manager.subscriber_count,
            "active_sessions": len(self._sessions),
            "config": {
                "model": self.config.model,
                "quality": self.config.quality.value,
                "ocr_enabled": self.config.ocr_enabled,
            },
            "dependencies": {
                "PIL": HAS_PIL,
                "mss": HAS_MSS,
                "aiohttp": HAS_AIOHTTP,
                "OCR": HAS_OCR,
            }
        }
    
    def get_latest_frame_base64(self) -> Optional[str]:
        """Son frame'i base64 olarak al."""
        frame = self._stream_manager.capture_single()
        if frame:
            return frame.image_base64
        return None
    
    async def check_vision_available(self) -> Dict[str, Any]:
        """Vision modeli kontrolü."""
        result = {
            "available": False,
            "model": self.config.model,
            "ollama_running": False,
            "error": None,
        }
        
        try:
            if HAS_AIOHTTP:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.config.ollama_host}/api/tags",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            result["ollama_running"] = True
                            data = await response.json()
                            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                            result["available_models"] = models
                            result["available"] = self.config.model in models
                            if not result["available"]:
                                result["error"] = f"Model '{self.config.model}' not found. Available: {models}"
            else:
                import requests
                response = requests.get(f"{self.config.ollama_host}/api/tags", timeout=5)
                if response.status_code == 200:
                    result["ollama_running"] = True
                    models = [m.get("name", "").split(":")[0] for m in response.json().get("models", [])]
                    result["available"] = self.config.model in models
                    
        except Exception as e:
            result["error"] = str(e)
        
        return result


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_realtime_vision: Optional[RealtimeVisionSystem] = None


def get_realtime_vision(config: Optional[VisionConfig] = None) -> RealtimeVisionSystem:
    """Singleton instance al."""
    global _realtime_vision
    
    if _realtime_vision is None:
        _realtime_vision = RealtimeVisionSystem(config)
    
    return _realtime_vision


async def quick_screen_analyze(question: str) -> str:
    """
    Hızlı ekran analizi.
    
    Usage:
        answer = await quick_screen_analyze("Ekranda hangi program açık?")
    """
    system = get_realtime_vision()
    result = await system.analyze_screen(question)
    return result.ai_response if result.success else f"Hata: {result.error}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "VisionConfig",
    "StreamQuality",
    "VisionMode",
    # Data classes
    "FrameData",
    "VisionContext",
    "UIElement",
    "ScreenAnalysis",
    # Managers
    "ScreenStreamManager",
    "VisionAnalyzerEngine",
    # Main system
    "RealtimeVisionSystem",
    # Factory
    "get_realtime_vision",
    "quick_screen_analyze",
    # Prompts
    "VisionPrompts",
]
