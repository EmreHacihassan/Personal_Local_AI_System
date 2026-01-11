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
    """
    
    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
    
    @property
    def provider(self) -> STTProvider:
        return STTProvider.WHISPER_LOCAL
    
    def _load_model(self):
        """Lazy load whisper model"""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except ImportError:
                try:
                    import whisper
                    self._model = whisper.load_model(self.model_size)
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


class WhisperAPISTT(SpeechToText):
    """
    OpenAI Whisper API STT.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    @property
    def provider(self) -> STTProvider:
        return STTProvider.WHISPER_API
    
    async def transcribe(self, audio: AudioSegment) -> TranscriptionResult:
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            
            # Create file-like object
            audio_file = io.BytesIO(audio.data)
            audio_file.name = f"audio.{audio.format.value}"
            
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
            
            return TranscriptionResult(
                text=response.text,
                language=response.language,
                segments=[s.model_dump() for s in response.segments] if hasattr(response, 'segments') else [],
                duration_ms=response.duration * 1000 if hasattr(response, 'duration') else 0
            )
            
        except ImportError:
            raise RuntimeError("openai package not installed")


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


class EdgeTTS(TextToSpeech):
    """
    Microsoft Edge TTS (free, high quality).
    """
    
    def __init__(self, default_voice: str = "en-US-AriaNeural"):
        self.default_voice = default_voice
    
    @property
    def provider(self) -> TTSProvider:
        return TTSProvider.EDGE_TTS
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> TTSResult:
        try:
            import edge_tts
            
            voice = voice or self.default_voice
            
            # Generate speech
            communicate = edge_tts.Communicate(text, voice)
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            return TTSResult(
                audio_data=audio_data,
                format=AudioFormat.MP3,
                sample_rate=24000
            )
            
        except ImportError:
            raise RuntimeError("edge-tts package not installed")
    
    async def list_voices(self) -> List[Dict[str, str]]:
        """List available voices"""
        try:
            import edge_tts
            voices = await edge_tts.list_voices()
            return voices
        except ImportError:
            return []


class OpenAITTS(TextToSpeech):
    """
    OpenAI TTS API.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "tts-1",
        default_voice: str = "alloy"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.default_voice = default_voice
    
    @property
    def provider(self) -> TTSProvider:
        return TTSProvider.OPENAI_TTS
    
    async def synthesize(self, text: str, voice: Optional[str] = None) -> TTSResult:
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            voice = voice or self.default_voice
            
            response = client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text
            )
            
            return TTSResult(
                audio_data=response.content,
                format=AudioFormat.MP3,
                sample_rate=24000
            )
            
        except ImportError:
            raise RuntimeError("openai package not installed")


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


class GPT4Vision(VisionAnalyzer):
    """
    OpenAI GPT-4 Vision.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
    
    @property
    def provider(self) -> VisionProvider:
        return VisionProvider.GPT4_VISION
    
    async def analyze(
        self,
        image: ImageInput,
        prompt: Optional[str] = None
    ) -> VisionResult:
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            prompt = prompt or "Describe this image in detail."
            
            # Build image content
            if image.url:
                image_content = {"type": "image_url", "image_url": {"url": image.url}}
            else:
                base64_data = image.get_base64()
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image.format.value};base64,{base64_data}"
                    }
                }
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            image_content
                        ]
                    }
                ],
                max_tokens=500
            )
            
            return VisionResult(
                description=response.choices[0].message.content,
                confidence=0.95
            )
            
        except ImportError:
            raise RuntimeError("openai package not installed")


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
    use_local: bool = True,
    openai_api_key: Optional[str] = None,
    llm_client: Optional[Any] = None
) -> MultimodalPipeline:
    """
    Create a multimodal pipeline with default providers.
    
    Args:
        use_local: Whether to use local models
        openai_api_key: OpenAI API key for cloud providers
        llm_client: Optional LLM client for response generation
        
    Returns:
        Configured MultimodalPipeline
    """
    if use_local:
        stt = WhisperLocalSTT(model_size="base")
        tts = Pyttsx3TTS()
        vision = LLaVAVision()
    else:
        stt = WhisperAPISTT(api_key=openai_api_key)
        tts = OpenAITTS(api_key=openai_api_key)
        vision = GPT4Vision(api_key=openai_api_key)
    
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
    """Quick text-to-speech to file"""
    tts = EdgeTTS()
    result = await tts.synthesize(text)
    
    with open(output_path, "wb") as f:
        f.write(result.audio_data)


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
    # STT
    "SpeechToText",
    "WhisperLocalSTT",
    "WhisperAPISTT",
    # TTS
    "TextToSpeech",
    "Pyttsx3TTS",
    "EdgeTTS",
    "OpenAITTS",
    # Vision
    "VisionAnalyzer",
    "LLaVAVision",
    "GPT4Vision",
    # Pipeline
    "MultimodalPipeline",
    "StreamingSTT",
    "StreamingTTS",
    # Factory
    "create_multimodal_pipeline",
    "quick_transcribe",
    "quick_speak",
]
