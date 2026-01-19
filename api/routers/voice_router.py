"""
🎤🔊🖼️ Voice & Multimodal API Router
=====================================

Fully LOCAL voice and vision endpoints.
All processing happens on your machine - no data leaves your computer.

Features:
- Speech-to-Text (STT) via local Whisper
- Text-to-Speech (TTS) via Pyttsx3
- Vision/Image analysis via LLaVA (Ollama)
"""

import asyncio
import base64
import io
import logging
import tempfile
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice & Multimodal"])


# ============ PYDANTIC MODELS ============

class TTSRequest(BaseModel):
    """Text-to-Speech isteği."""
    text: str = Field(..., min_length=1, max_length=5000, description="Seslendirilecek metin")
    voice: Optional[str] = Field(default=None, description="Ses seçimi (opsiyonel)")
    rate: int = Field(default=150, ge=50, le=300, description="Konuşma hızı")
    volume: float = Field(default=1.0, ge=0.0, le=1.0, description="Ses seviyesi")
    language: str = Field(default="tr", description="Dil kodu")


class TTSResponse(BaseModel):
    """Text-to-Speech yanıtı."""
    success: bool
    audio_base64: Optional[str] = None
    format: str = "wav"
    duration_ms: Optional[float] = None
    message: Optional[str] = None


class STTResponse(BaseModel):
    """Speech-to-Text yanıtı."""
    success: bool
    text: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration_ms: Optional[float] = None
    message: Optional[str] = None


class VisionRequest(BaseModel):
    """Vision analiz isteği."""
    prompt: str = Field(default="Bu görseli detaylı açıkla.", description="Görsel için soru/prompt")
    image_base64: str = Field(..., description="Base64 encoded görsel")
    model: str = Field(default="llava", description="Vision model (llava, bakllava, etc.)")


class VisionResponse(BaseModel):
    """Vision analiz yanıtı."""
    success: bool
    description: Optional[str] = None
    objects_detected: List[str] = []
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    message: Optional[str] = None


class MultimodalChatRequest(BaseModel):
    """Multimodal chat isteği."""
    text: Optional[str] = Field(default=None, description="Metin mesajı")
    audio_base64: Optional[str] = Field(default=None, description="Base64 encoded ses")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded görsel")
    generate_audio_response: bool = Field(default=False, description="Sesli yanıt üret")


class MultimodalChatResponse(BaseModel):
    """Multimodal chat yanıtı."""
    success: bool
    text_response: Optional[str] = None
    audio_response_base64: Optional[str] = None
    transcription: Optional[str] = None
    image_description: Optional[str] = None
    message: Optional[str] = None


# ============ TTS ENDPOINT ============

@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    🔊 Text-to-Speech (Metin → Ses)
    
    Metni sese dönüştürür. Tamamen yerel işlenir, veri dışarı gitmez.
    
    - **text**: Seslendirilecek metin
    - **rate**: Konuşma hızı (50-300)
    - **volume**: Ses seviyesi (0.0-1.0)
    - **language**: Dil kodu (tr, en, etc.)
    """
    try:
        from core.voice_multimodal import Pyttsx3TTS, AudioFormat
        
        # TTS engine oluştur
        tts = Pyttsx3TTS(rate=request.rate, volume=request.volume)
        
        # Sesi sentezle
        result = await tts.synthesize(request.text, request.voice)
        
        # Base64'e çevir
        audio_base64 = base64.b64encode(result.audio_data).decode('utf-8')
        
        return TTSResponse(
            success=True,
            audio_base64=audio_base64,
            format=result.format.value,
            duration_ms=result.duration_ms
        )
        
    except ImportError as e:
        logger.error(f"TTS import error: {e}")
        return TTSResponse(
            success=False,
            message="pyttsx3 paketi yüklü değil. pip install pyttsx3"
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return TTSResponse(
            success=False,
            message=str(e)
        )


@router.post("/tts/stream")
async def text_to_speech_stream(request: TTSRequest):
    """
    🔊 Text-to-Speech Streaming
    
    Metni sese dönüştürür ve streaming olarak döndürür.
    """
    try:
        from core.voice_multimodal import Pyttsx3TTS
        
        tts = Pyttsx3TTS(rate=request.rate, volume=request.volume)
        result = await tts.synthesize(request.text, request.voice)
        
        return Response(
            content=result.audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ STT ENDPOINT ============

@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(..., description="Ses dosyası (wav, mp3, etc.)"),
    model_size: str = Form(default="base", description="Whisper model boyutu: tiny, base, small, medium, large")
):
    """
    🎤 Speech-to-Text (Ses → Metin)
    
    Ses dosyasını metne dönüştürür. Tamamen yerel işlenir.
    
    - **audio**: Ses dosyası (wav, mp3, ogg, flac)
    - **model_size**: Whisper model boyutu (tiny, base, small, medium, large)
    """
    try:
        from core.voice_multimodal import WhisperLocalSTT, AudioSegment, AudioFormat
        
        # Dosya içeriğini oku
        audio_data = await audio.read()
        
        # Format tespit
        filename = audio.filename or "audio.wav"
        ext = Path(filename).suffix.lower().strip(".")
        
        format_map = {
            "wav": AudioFormat.WAV,
            "mp3": AudioFormat.MP3,
            "ogg": AudioFormat.OGG,
            "flac": AudioFormat.FLAC,
            "webm": AudioFormat.WEBM,
        }
        audio_format = format_map.get(ext, AudioFormat.WAV)
        
        # Audio segment oluştur
        segment = AudioSegment(
            data=audio_data,
            format=audio_format
        )
        
        # STT engine oluştur ve transcribe et
        stt = WhisperLocalSTT(model_size=model_size)
        result = await stt.transcribe(segment)
        
        return STTResponse(
            success=True,
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration_ms=result.duration_ms
        )
        
    except ImportError as e:
        logger.error(f"STT import error: {e}")
        return STTResponse(
            success=False,
            message="Whisper paketi yüklü değil. pip install faster-whisper veya pip install openai-whisper"
        )
    except Exception as e:
        logger.error(f"STT error: {e}")
        return STTResponse(
            success=False,
            message=str(e)
        )


@router.post("/stt/base64", response_model=STTResponse)
async def speech_to_text_base64(
    audio_base64: str = Form(..., description="Base64 encoded ses"),
    format: str = Form(default="wav", description="Ses formatı"),
    model_size: str = Form(default="base", description="Whisper model boyutu")
):
    """
    🎤 Speech-to-Text (Base64)
    
    Base64 encoded ses verisini metne dönüştürür.
    """
    try:
        from core.voice_multimodal import WhisperLocalSTT, AudioSegment, AudioFormat
        
        # Base64'ü decode et
        audio_data = base64.b64decode(audio_base64)
        
        format_map = {
            "wav": AudioFormat.WAV,
            "mp3": AudioFormat.MP3,
            "ogg": AudioFormat.OGG,
            "flac": AudioFormat.FLAC,
            "webm": AudioFormat.WEBM,
        }
        audio_format = format_map.get(format.lower(), AudioFormat.WAV)
        
        segment = AudioSegment(data=audio_data, format=audio_format)
        
        stt = WhisperLocalSTT(model_size=model_size)
        result = await stt.transcribe(segment)
        
        return STTResponse(
            success=True,
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration_ms=result.duration_ms
        )
        
    except Exception as e:
        logger.error(f"STT base64 error: {e}")
        return STTResponse(
            success=False,
            message=str(e)
        )


# ============ VISION ENDPOINT ============

@router.post("/vision", response_model=VisionResponse)
async def analyze_image(request: VisionRequest):
    """
    🖼️ Vision Analysis (Görsel Analizi)
    
    Görseli analiz eder ve açıklama üretir. LLaVA via Ollama kullanır.
    Tamamen yerel işlenir, veri dışarı gitmez.
    
    - **image_base64**: Base64 encoded görsel
    - **prompt**: Görsel için soru (örn: "Bu görselde ne var?")
    - **model**: Vision model (llava, bakllava)
    """
    try:
        from core.voice_multimodal import LLaVAVision, ImageInput, ImageFormat
        
        # Vision analyzer oluştur
        vision = LLaVAVision(model=request.model)
        
        # Image input oluştur
        image = ImageInput(base64_data=request.image_base64)
        
        # Analiz et
        result = await vision.analyze(image, request.prompt)
        
        return VisionResponse(
            success=True,
            description=result.description,
            objects_detected=result.objects_detected,
            confidence=result.confidence,
            model_used=request.model
        )
        
    except Exception as e:
        logger.error(f"Vision error: {e}")
        return VisionResponse(
            success=False,
            message=str(e)
        )


@router.post("/vision/upload", response_model=VisionResponse)
async def analyze_uploaded_image(
    image: UploadFile = File(..., description="Görsel dosyası"),
    prompt: str = Form(default="Bu görseli detaylı açıkla.", description="Soru/prompt"),
    model: str = Form(default="llava", description="Vision model")
):
    """
    🖼️ Vision Analysis (Dosya Upload)
    
    Yüklenen görseli analiz eder.
    """
    try:
        from core.voice_multimodal import LLaVAVision, ImageInput, ImageFormat
        
        # Dosyayı oku ve base64'e çevir
        image_data = await image.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Vision analyzer
        vision = LLaVAVision(model=model)
        image_input = ImageInput(base64_data=image_base64)
        
        result = await vision.analyze(image_input, prompt)
        
        return VisionResponse(
            success=True,
            description=result.description,
            objects_detected=result.objects_detected,
            confidence=result.confidence,
            model_used=model
        )
        
    except Exception as e:
        logger.error(f"Vision upload error: {e}")
        return VisionResponse(
            success=False,
            message=str(e)
        )


# ============ MULTIMODAL CHAT ============

@router.post("/multimodal-chat", response_model=MultimodalChatResponse)
async def multimodal_chat(request: MultimodalChatRequest):
    """
    🎤🖼️💬 Multimodal Chat
    
    Ses, görsel ve metin kombinasyonu ile sohbet.
    Tüm işlemler yerel yapılır.
    
    - **text**: Metin mesajı
    - **audio_base64**: Base64 encoded ses (opsiyonel)
    - **image_base64**: Base64 encoded görsel (opsiyonel)
    - **generate_audio_response**: Sesli yanıt üret
    """
    try:
        from core.voice_multimodal import (
            create_multimodal_pipeline,
            MultimodalInput,
            AudioSegment,
            AudioFormat,
            ImageInput
        )
        from core.llm_manager import llm_manager
        
        # Pipeline oluştur
        pipeline = create_multimodal_pipeline(llm_client=llm_manager)
        
        # Input hazırla
        audio_segment = None
        if request.audio_base64:
            audio_data = base64.b64decode(request.audio_base64)
            audio_segment = AudioSegment(data=audio_data, format=AudioFormat.WAV)
        
        images = []
        if request.image_base64:
            images.append(ImageInput(base64_data=request.image_base64))
        
        multimodal_input = MultimodalInput(
            text=request.text,
            audio=audio_segment,
            images=images
        )
        
        # İşle
        result = await pipeline.process(
            multimodal_input,
            generate_audio_response=request.generate_audio_response
        )
        
        # Yanıt hazırla
        audio_response_base64 = None
        if result.audio_response:
            audio_response_base64 = base64.b64encode(result.audio_response.audio_data).decode('utf-8')
        
        transcription = None
        if result.transcription:
            transcription = result.transcription.text
        
        image_description = None
        if result.image_descriptions:
            image_description = result.image_descriptions[0].description
        
        return MultimodalChatResponse(
            success=True,
            text_response=result.text_response,
            audio_response_base64=audio_response_base64,
            transcription=transcription,
            image_description=image_description
        )
        
    except Exception as e:
        logger.error(f"Multimodal chat error: {e}")
        return MultimodalChatResponse(
            success=False,
            message=str(e)
        )


# ============ STATUS & CAPABILITIES ============

@router.get("/status")
async def get_voice_status():
    """
    📊 Voice & Multimodal durumu
    
    Mevcut ses ve görsel yeteneklerinin durumunu döndürür.
    """
    status = {
        "tts": {
            "provider": "Pyttsx3 (LOCAL)",
            "available": False,
            "data_privacy": "100% LOCAL - No data leaves your computer"
        },
        "stt": {
            "provider": "Whisper Local (faster-whisper)",
            "available": False,
            "models": ["tiny", "base", "small", "medium", "large"],
            "data_privacy": "100% LOCAL - No data leaves your computer"
        },
        "vision": {
            "provider": "LLaVA (Ollama)",
            "available": False,
            "models": ["llava", "bakllava", "llava-llama3"],
            "data_privacy": "100% LOCAL - No data leaves your computer"
        }
    }
    
    # TTS kontrolü
    try:
        import pyttsx3
        status["tts"]["available"] = True
        status["tts"]["message"] = "Pyttsx3 TTS hazır"
    except ImportError:
        status["tts"]["message"] = "pyttsx3 yüklü değil: pip install pyttsx3"
    
    # STT kontrolü
    try:
        from faster_whisper import WhisperModel
        status["stt"]["available"] = True
        status["stt"]["message"] = "Faster-Whisper STT hazır"
    except ImportError:
        try:
            import whisper
            status["stt"]["available"] = True
            status["stt"]["message"] = "OpenAI-Whisper STT hazır"
        except ImportError:
            status["stt"]["message"] = "Whisper yüklü değil: pip install faster-whisper"
    
    # Vision kontrolü
    try:
        import aiohttp
        # Ollama kontrolü
        import httpx
        try:
            response = httpx.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                vision_models = [m["name"] for m in models if "llava" in m["name"].lower()]
                if vision_models:
                    status["vision"]["available"] = True
                    status["vision"]["installed_models"] = vision_models
                    status["vision"]["message"] = f"LLaVA modelleri mevcut: {vision_models}"
                else:
                    status["vision"]["message"] = "LLaVA modeli yüklü değil: ollama pull llava"
            else:
                status["vision"]["message"] = "Ollama bağlantı hatası"
        except Exception:
            status["vision"]["message"] = "Ollama çalışmıyor"
    except ImportError:
        status["vision"]["message"] = "aiohttp yüklü değil"
    
    return {
        "success": True,
        "capabilities": status,
        "privacy_note": "🔒 Tüm işlemler bilgisayarınızda yapılır. Hiçbir veri dışarı gönderilmez."
    }


@router.get("/voices")
async def list_available_voices():
    """
    🔊 Mevcut TTS seslerini listele
    """
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        voice_list = []
        for voice in voices:
            voice_list.append({
                "id": voice.id,
                "name": voice.name,
                "languages": voice.languages,
                "gender": getattr(voice, 'gender', 'unknown')
            })
        
        engine.stop()
        
        return {
            "success": True,
            "voices": voice_list,
            "count": len(voice_list)
        }
        
    except ImportError:
        return {
            "success": False,
            "message": "pyttsx3 yüklü değil",
            "voices": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "voices": []
        }


# Export router
voice_router = router
