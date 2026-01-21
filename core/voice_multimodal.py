"""
🎤🖼️ Voice & Multimodal Pipeline
=================================

Speech and vision capabilities for the agentic system.

Features:
- Speech-to-Text (STT) with Whisper
- Text-to-Speech (TTS) with multiple backends
- Vision/Image understanding
- Audio processing
- Multimodal fusion
- Real-time streaming support
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import tempfile
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, BinaryIO, Callable, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class MediaType(str, Enum):
    """Types of media"""
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"


class AudioFormat(str, Enum):
    """Audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    WEBM = "webm"


class ImageFormat(str, Enum):
    """Image formats"""
    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"
    GIF = "gif"


class STTProvider(str, Enum):
    """Speech-to-text providers"""
    WHISPER_LOCAL = "whisper_local"
    WHISPER_API = "whisper_api"
    AZURE = "azure"
    GOOGLE = "google"
    DEEPGRAM = "deepgram"


class TTSProvider(str, Enum):
    """Text-to-speech providers"""
    PYTTSX3 = "pyttsx3"
    EDGE_TTS = "edge_tts"
    OPENAI_TTS = "openai_tts"
    ELEVENLABS = "elevenlabs"
    AZURE = "azure"


class VisionProvider(str, Enum):
    """Vision/image understanding providers"""
    LLAVA = "llava"
    GPT4_VISION = "gpt4_vision"
    CLAUDE_VISION = "claude_vision"
    BLIP = "blip"


# ============ DATA MODELS ============

class AudioSegment(BaseModel):
    """An audio segment"""
    data: bytes
    format: AudioFormat
    sample_rate: int = 16000
    channels: int = 1
    duration_ms: float = 0


class TranscriptionResult(BaseModel):
    """Result from speech-to-text"""
    text: str
    language: str = "en"
    confidence: float = 1.0
    segments: List[Dict[str, Any]] = Field(default_factory=list)
    duration_ms: float = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TTSResult(BaseModel):
    """Result from text-to-speech"""
    audio_data: bytes
    format: AudioFormat = AudioFormat.MP3
    sample_rate: int = 22050
    duration_ms: float = 0


class ImageInput(BaseModel):
    """Image input for vision"""
    data: Optional[bytes] = None
    url: Optional[str] = None
    base64_data: Optional[str] = None
    format: ImageFormat = ImageFormat.PNG
    
    def get_base64(self) -> str:
        """Get base64 representation"""
        if self.base64_data:
            return self.base64_data
        if self.data:
            return base64.b64encode(self.data).decode("utf-8")
        return ""


class VisionResult(BaseModel):
    """Result from vision analysis"""
    description: str
    objects_detected: List[str] = Field(default_factory=list)
    text_detected: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultimodalInput(BaseModel):
    """Combined multimodal input"""
    text: Optional[str] = None
    audio: Optional[AudioSegment] = None
    images: List[ImageInput] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultimodalResult(BaseModel):
    """Combined multimodal result"""
    text_response: str
    audio_response: Optional[TTSResult] = None
    image_descriptions: List[VisionResult] = Field(default_factory=list)
    transcription: Optional[TranscriptionResult] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============ SPEECH-TO-TEXT ============

class SpeechToText(ABC):
    """Base class for STT providers"""
    
    @property
    @abstractmethod
    def provider(self) -> STTProvider:
        pass
    
    @abstractmethod
    async def transcribe(self, audio: AudioSegment) -> TranscriptionResult:
        pass


class WhisperLocalSTT(SpeechToText):
    """
    Local Whisper STT using faster-whisper or openai-whisper.
    
    GPU OPTIMIZATION:
    - CUDA acceleration for 10x faster transcription
    - FP16 for memory efficiency
    - Batch processing support
    """
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",  # "auto", "cuda", "cpu"
        compute_type: str = "auto"  # "auto", "float16", "int8", "float32"
    ):
        self.model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model = None
        
        # Auto-detect GPU
        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device
        
        # Auto-select compute type based on device
        if compute_type == "auto":
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        else:
            self.compute_type = compute_type
    
    @property
    def provider(self) -> STTProvider:
        return STTProvider.WHISPER_LOCAL
    
    def _load_model(self):
        """Lazy load whisper model with GPU support"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                
                print(f"🎤 Whisper model yükleniyor: {self.model_size}")
                print(f"   Device: {self.device}, Compute: {self.compute_type}")
                
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                
                gpu_info = " (GPU)" if self.device == "cuda" else " (CPU)"
                print(f"✅ Whisper hazır{gpu_info}")
                
            except ImportError:
                try:
                    import whisper
                    print(f"🎤 OpenAI Whisper yükleniyor: {self.model_size}")
                    self._model = whisper.load_model(self.model_size, device=self.device)
                    print(f"✅ OpenAI Whisper hazır")
                except ImportError:
                    raise RuntimeError("Neither faster-whisper nor openai-whisper installed")
    
    async def transcribe(self, audio: AudioSegment) -> TranscriptionResult:
        self._load_model()
        
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix=f".{audio.format.value}", delete=False) as f:
            f.write(audio.data)
            temp_path = f.name
        
        try:
            # Check which backend we're using
            if hasattr(self._model, "transcribe"):
                # faster-whisper
                segments, info = self._model.transcribe(temp_path)
                
                text_parts = []
                segment_data = []
                
                for segment in segments:
                    text_parts.append(segment.text)
                    segment_data.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text
                    })
                
                return TranscriptionResult(
                    text=" ".join(text_parts).strip(),
                    language=info.language,
                    confidence=info.language_probability,
                    segments=segment_data,
                    duration_ms=audio.duration_ms
                )
            else:
                # openai-whisper
                result = self._model.transcribe(temp_path)
                
                return TranscriptionResult(
                    text=result["text"].strip(),
                    language=result.get("language", "en"),
                    segments=result.get("segments", []),
                    duration_ms=audio.duration_ms
                )
        finally:
            os.unlink(temp_path)


# WhisperAPISTT REMOVED - Privacy: Data would be sent to OpenAI servers
# Use WhisperLocalSTT instead for fully offline speech-to-text


# ============ TEXT-TO-SPEECH ============

class TextToSpeech(ABC):
    """Base class for TTS providers"""
    
    @property
    @abstractmethod
    def provider(self) -> TTSProvider:
        pass
    
    @abstractmethod
    async def synthesize(self, text: str, voice: Optional[str] = None) -> TTSResult:
        pass


class Pyttsx3TTS(TextToSpeech):
    """
    Local TTS using pyttsx3.
    """
    
    def __init__(self, rate: int = 150, volume: float = 1.0):
        self.rate = rate
        self.volume = volume
        self._engine = None
    
    @property
    def provider(self) -> TTSProvider:
        return TTSProvider.PYTTSX3
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> TTSResult:
        try:
            import pyttsx3
            
            if self._engine is None:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", self.rate)
                self._engine.setProperty("volume", self.volume)
            
            if voice:
                self._engine.setProperty("voice", voice)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            try:
                self._engine.save_to_file(text, temp_path)
                self._engine.runAndWait()
                
                with open(temp_path, "rb") as f:
                    audio_data = f.read()
                
                return TTSResult(
                    audio_data=audio_data,
                    format=AudioFormat.WAV,
                    sample_rate=22050
                )
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except ImportError:
            raise RuntimeError("pyttsx3 package not installed")


# EdgeTTS REMOVED - Privacy: Data is sent to Microsoft servers
# Use Pyttsx3TTS instead for fully offline text-to-speech


# OpenAITTS REMOVED - Privacy: Data is sent to OpenAI servers
# Use Pyttsx3TTS instead for fully offline text-to-speech


# ============ VISION ============

class VisionAnalyzer(ABC):
    """Base class for vision analysis"""
    
    @property
    @abstractmethod
    def provider(self) -> VisionProvider:
        pass
    
    @abstractmethod
    async def analyze(
        self,
        image: ImageInput,
        prompt: Optional[str] = None
    ) -> VisionResult:
        pass


class LLaVAVision(VisionAnalyzer):
    """
    Local LLaVA vision model via Ollama.
    """
    
    def __init__(
        self,
        model: str = "llava",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url
    
    @property
    def provider(self) -> VisionProvider:
        return VisionProvider.LLAVA
    
    async def analyze(
        self,
        image: ImageInput,
        prompt: Optional[str] = None
    ) -> VisionResult:
        import aiohttp
        
        prompt = prompt or "Describe this image in detail."
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [image.get_base64()],
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return VisionResult(
                        description=data.get("response", ""),
                        confidence=0.8
                    )
                else:
                    raise RuntimeError(f"LLaVA request failed: {response.status}")


# GPT4Vision REMOVED - Privacy: Data is sent to OpenAI servers
# Use LLaVAVision instead for fully offline image analysis via Ollama


# ============ MULTIMODAL PIPELINE ============

class MultimodalPipeline:
    """
    Complete multimodal processing pipeline.
    
    Handles:
    - Audio -> Text (STT)
    - Text -> Audio (TTS)
    - Image -> Text (Vision)
    - Combined multimodal inputs
    """
    
    def __init__(
        self,
        stt: Optional[SpeechToText] = None,
        tts: Optional[TextToSpeech] = None,
        vision: Optional[VisionAnalyzer] = None,
        llm_client: Optional[Any] = None
    ):
        self.stt = stt
        self.tts = tts
        self.vision = vision
        self.llm_client = llm_client
    
    async def process(
        self,
        input: MultimodalInput,
        generate_audio_response: bool = False
    ) -> MultimodalResult:
        """
        Process multimodal input and generate response.
        """
        # 1. Process audio input (if any)
        transcription = None
        text_parts = []
        
        if input.audio and self.stt:
            transcription = await self.stt.transcribe(input.audio)
            text_parts.append(f"User said: {transcription.text}")
        
        # 2. Process images (if any)
        image_descriptions = []
        if input.images and self.vision:
            for image in input.images:
                result = await self.vision.analyze(image)
                image_descriptions.append(result)
                text_parts.append(f"Image shows: {result.description}")
        
        # 3. Add text input
        if input.text:
            text_parts.append(input.text)
        
        # 4. Generate response
        combined_input = "\n".join(text_parts)
        
        if self.llm_client:
            text_response = await self._generate_response(combined_input)
        else:
            text_response = f"Processed input: {combined_input}"
        
        # 5. Generate audio response (if requested)
        audio_response = None
        if generate_audio_response and self.tts:
            audio_response = await self.tts.synthesize(text_response)
        
        return MultimodalResult(
            text_response=text_response,
            audio_response=audio_response,
            image_descriptions=image_descriptions,
            transcription=transcription
        )
    
    async def _generate_response(self, input: str) -> str:
        """Generate LLM response"""
        if hasattr(self.llm_client, "generate"):
            return await self.llm_client.generate(input)
        elif hasattr(self.llm_client, "chat"):
            return await self.llm_client.chat(input)
        else:
            return f"Processed: {input}"
    
    async def transcribe_audio(self, audio_data: bytes, format: AudioFormat = AudioFormat.WAV) -> str:
        """Convenience method for audio transcription"""
        if not self.stt:
            raise RuntimeError("No STT provider configured")
        
        segment = AudioSegment(data=audio_data, format=format)
        result = await self.stt.transcribe(segment)
        return result.text
    
    async def synthesize_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """Convenience method for speech synthesis"""
        if not self.tts:
            raise RuntimeError("No TTS provider configured")
        
        result = await self.tts.synthesize(text, voice)
        return result.audio_data
    
    async def describe_image(self, image_data: bytes, format: ImageFormat = ImageFormat.PNG) -> str:
        """Convenience method for image description"""
        if not self.vision:
            raise RuntimeError("No vision provider configured")
        
        image = ImageInput(data=image_data, format=format)
        result = await self.vision.analyze(image)
        return result.description


# ============ STREAMING SUPPORT ============

class StreamingSTT:
    """
    Real-time streaming speech-to-text.
    """
    
    def __init__(
        self,
        stt: SpeechToText,
        chunk_duration_ms: int = 500
    ):
        self.stt = stt
        self.chunk_duration_ms = chunk_duration_ms
        self.buffer = b""
    
    async def process_chunk(self, audio_chunk: bytes) -> Optional[str]:
        """Process an audio chunk, return transcription if ready"""
        self.buffer += audio_chunk
        
        # Check if we have enough data
        # This is simplified - production would check actual duration
        if len(self.buffer) > 8000:  # ~500ms at 16kHz mono
            segment = AudioSegment(
                data=self.buffer,
                format=AudioFormat.WAV
            )
            
            result = await self.stt.transcribe(segment)
            self.buffer = b""
            
            return result.text
        
        return None


class StreamingTTS:
    """
    Real-time streaming text-to-speech.
    """
    
    def __init__(self, tts: TextToSpeech):
        self.tts = tts
    
    async def stream(self, text: str) -> AsyncIterator[bytes]:
        """Stream audio chunks"""
        # Simple implementation - full result then yield
        # Production would use actual streaming TTS
        result = await self.tts.synthesize(text)
        
        # Yield in chunks
        chunk_size = 4096
        data = result.audio_data
        
        for i in range(0, len(data), chunk_size):
            yield data[i:i + chunk_size]
            await asyncio.sleep(0.01)  # Small delay for streaming effect


# ============ CONVENIENCE FUNCTIONS ============

def create_multimodal_pipeline(
    llm_client: Optional[Any] = None
) -> MultimodalPipeline:
    """
    Create a multimodal pipeline with LOCAL-ONLY providers.
    
    All processing happens on your machine - no data leaves your computer.
    
    Args:
        llm_client: Optional LLM client for response generation
        
    Returns:
        Configured MultimodalPipeline with local providers
    """
    # All providers are LOCAL - data never leaves your computer
    stt = WhisperLocalSTT(model_size="tiny")  # tiny for faster startup
    tts = Pyttsx3TTS()
    vision = LLaVAVision()
    
    return MultimodalPipeline(
        stt=stt,
        tts=tts,
        vision=vision,
        llm_client=llm_client
    )


async def quick_transcribe(audio_path: str) -> str:
    """Quick transcription from file"""
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    
    # Detect format from extension
    ext = Path(audio_path).suffix.lower().strip(".")
    format = AudioFormat(ext) if ext in [e.value for e in AudioFormat] else AudioFormat.WAV
    
    stt = WhisperLocalSTT()
    segment = AudioSegment(data=audio_data, format=format)
    result = await stt.transcribe(segment)
    
    return result.text


async def quick_speak(text: str, output_path: str):
    """Quick text-to-speech to file (LOCAL - no data leaves your computer)"""
    tts = Pyttsx3TTS()  # Fully offline TTS
    result = await tts.synthesize(text)
    
    with open(output_path, "wb") as f:
        f.write(result.audio_data)


# ============ HEALTH CHECK ============

class VoiceSystemHealth:
    """Voice system health checker."""
    
    @staticmethod
    def check_tts() -> Dict[str, Any]:
        """Check TTS availability."""
        result = {
            "available": False,
            "provider": "pyttsx3",
            "error": None,
        }
        
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.stop()
            
            result["available"] = True
            result["voices_count"] = len(voices) if voices else 0
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def check_stt() -> Dict[str, Any]:
        """Check STT availability."""
        result = {
            "available": False,
            "provider": None,
            "error": None,
        }
        
        # Try faster-whisper first
        try:
            from faster_whisper import WhisperModel
            result["available"] = True
            result["provider"] = "faster-whisper"
            return result
        except ImportError:
            pass
        
        # Try openai-whisper
        try:
            import whisper
            result["available"] = True
            result["provider"] = "openai-whisper"
            return result
        except ImportError:
            result["error"] = "Neither faster-whisper nor openai-whisper installed"
        
        return result
    
    @staticmethod
    def check_vision() -> Dict[str, Any]:
        """Check vision availability."""
        result = {
            "available": False,
            "provider": "llava",
            "ollama_running": False,
            "model_available": False,
            "error": None,
        }
        
        try:
            import requests
            
            # Check Ollama
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    result["ollama_running"] = True
                    
                    # Check for vision model
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "").split(":")[0] for m in models]
                    
                    if "llava" in model_names:
                        result["model_available"] = True
                        result["available"] = True
                    else:
                        result["error"] = f"llava model not found. Available: {model_names}"
            except requests.exceptions.ConnectionError:
                result["error"] = "Ollama not running on localhost:11434"
                
        except ImportError:
            result["error"] = "requests package not installed"
        
        return result
    
    @staticmethod
    def full_check() -> Dict[str, Any]:
        """Full system health check."""
        return {
            "tts": VoiceSystemHealth.check_tts(),
            "stt": VoiceSystemHealth.check_stt(),
            "vision": VoiceSystemHealth.check_vision(),
            "timestamp": datetime.now().isoformat(),
        }


# ============ SINGLETON INSTANCES ============

_tts_instance: Optional[Pyttsx3TTS] = None
_stt_instance: Optional[WhisperLocalSTT] = None
_vision_instance: Optional[LLaVAVision] = None
_pipeline_instance: Optional[MultimodalPipeline] = None


def get_tts() -> Pyttsx3TTS:
    """Get singleton TTS instance."""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = Pyttsx3TTS()
    return _tts_instance


def get_stt(model_size: str = "tiny") -> WhisperLocalSTT:
    """Get singleton STT instance."""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = WhisperLocalSTT(model_size=model_size)
    return _stt_instance


def get_vision() -> LLaVAVision:
    """Get singleton vision instance."""
    global _vision_instance
    if _vision_instance is None:
        _vision_instance = LLaVAVision()
    return _vision_instance


def get_pipeline(llm_client: Optional[Any] = None) -> MultimodalPipeline:
    """Get singleton pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = create_multimodal_pipeline(llm_client)
    return _pipeline_instance


# ============ EXPORTS ============

__all__ = [
    # Types
    "MediaType",
    "AudioFormat",
    "ImageFormat",
    "STTProvider",
    "TTSProvider",
    "VisionProvider",
    # Models
    "AudioSegment",
    "TranscriptionResult",
    "TTSResult",
    "ImageInput",
    "VisionResult",
    "MultimodalInput",
    "MultimodalResult",
    # STT (LOCAL ONLY)
    "SpeechToText",
    "WhisperLocalSTT",
    # TTS (LOCAL ONLY)
    "TextToSpeech",
    "Pyttsx3TTS",
    # Vision (LOCAL ONLY)
    "VisionAnalyzer",
    "LLaVAVision",
    # Pipeline
    "MultimodalPipeline",
    "StreamingSTT",
    "StreamingTTS",
    # Factory
    "create_multimodal_pipeline",
    "quick_transcribe",
    "quick_speak",
    # Singletons
    "get_tts",
    "get_stt",
    "get_vision",
    "get_pipeline",
    # Health
    "VoiceSystemHealth",
]
