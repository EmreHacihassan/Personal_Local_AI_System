"""
Voice AI Assistant - Local Speech-to-Text and Text-to-Speech
Uses Whisper for STT and edge-tts/pyttsx3 for TTS
100% Local processing capability
"""

import asyncio
import base64
import io
import json
import logging
import os
import tempfile
import wave
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
import threading
import queue

logger = logging.getLogger(__name__)

class VoiceLanguage(str, Enum):
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"
    FRENCH = "fr"
    SPANISH = "es"
    ITALIAN = "it"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    RUSSIAN = "ru"
    ARABIC = "ar"
    PORTUGUESE = "pt"

@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[Dict[str, Any]]

@dataclass
class TTSResult:
    audio_data: bytes
    format: str
    sample_rate: int
    duration: float

class VoiceAI:
    """
    Premium Voice AI Assistant with local STT/TTS
    """
    
    def __init__(self):
        self.whisper_model = None
        self.whisper_model_name = "base"  # tiny, base, small, medium, large
        self.tts_engine = None
        self.is_initialized = False
        self._lock = threading.Lock()
        self._audio_queue = queue.Queue()
        
        # TTS voices mapping
        self.tts_voices = {
            "tr": "tr-TR-AhmetNeural",
            "en": "en-US-GuyNeural",
            "de": "de-DE-ConradNeural",
            "fr": "fr-FR-HenriNeural",
            "es": "es-ES-AlvaroNeural",
            "it": "it-IT-DiegoNeural",
            "ja": "ja-JP-KeitaNeural",
            "zh": "zh-CN-YunxiNeural",
            "ko": "ko-KR-InJoonNeural",
            "ru": "ru-RU-DmitryNeural",
            "ar": "ar-SA-HamedNeural",
            "pt": "pt-BR-AntonioNeural"
        }
        
        # Female voice alternatives
        self.tts_voices_female = {
            "tr": "tr-TR-EmelNeural",
            "en": "en-US-JennyNeural",
            "de": "de-DE-KatjaNeural",
            "fr": "fr-FR-DeniseNeural",
            "es": "es-ES-ElviraNeural",
            "it": "it-IT-ElsaNeural",
            "ja": "ja-JP-NanamiNeural",
            "zh": "zh-CN-XiaoxiaoNeural",
            "ko": "ko-KR-SunHiNeural",
            "ru": "ru-RU-SvetlanaNeural",
            "ar": "ar-SA-ZariyahNeural",
            "pt": "pt-BR-FranciscaNeural"
        }
    
    async def initialize(self, whisper_model: str = "base") -> bool:
        """Initialize Voice AI components"""
        try:
            self.whisper_model_name = whisper_model
            
            # Try to load Whisper
            try:
                import whisper
                logger.info(f"Loading Whisper model: {whisper_model}")
                self.whisper_model = whisper.load_model(whisper_model)
                logger.info("Whisper model loaded successfully")
            except ImportError:
                logger.warning("Whisper not installed. Install with: pip install openai-whisper")
                # Try faster-whisper as alternative
                try:
                    from faster_whisper import WhisperModel
                    logger.info(f"Loading faster-whisper model: {whisper_model}")
                    self.whisper_model = WhisperModel(whisper_model, device="cpu", compute_type="int8")
                    logger.info("faster-whisper model loaded successfully")
                except ImportError:
                    logger.warning("faster-whisper not installed either")
            
            # Initialize TTS
            try:
                import edge_tts
                self.tts_engine = "edge_tts"
                logger.info("edge-tts initialized")
            except ImportError:
                try:
                    import pyttsx3
                    self.tts_engine = pyttsx3.init()
                    logger.info("pyttsx3 initialized")
                except ImportError:
                    logger.warning("No TTS engine available. Install edge-tts or pyttsx3")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Voice AI: {e}")
            return False
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        task: str = "transcribe"  # or "translate" to English
    ) -> TranscriptionResult:
        """
        Transcribe audio to text using Whisper
        
        Args:
            audio_data: Raw audio bytes (WAV, MP3, etc.)
            language: Optional language code (auto-detect if None)
            task: "transcribe" or "translate"
        
        Returns:
            TranscriptionResult with text and metadata
        """
        if not self.whisper_model:
            raise RuntimeError("Whisper model not loaded. Call initialize() first.")
        
        try:
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            try:
                # Check if using faster-whisper or original whisper
                if hasattr(self.whisper_model, 'transcribe'):
                    # Original Whisper
                    import whisper
                    result = self.whisper_model.transcribe(
                        temp_path,
                        language=language,
                        task=task,
                        fp16=False
                    )
                    
                    return TranscriptionResult(
                        text=result["text"].strip(),
                        language=result.get("language", language or "unknown"),
                        confidence=1.0,
                        duration=result.get("duration", 0),
                        segments=[{
                            "start": s["start"],
                            "end": s["end"],
                            "text": s["text"]
                        } for s in result.get("segments", [])]
                    )
                else:
                    # faster-whisper
                    segments, info = self.whisper_model.transcribe(
                        temp_path,
                        language=language,
                        task=task
                    )
                    
                    segments_list = list(segments)
                    full_text = " ".join([s.text for s in segments_list])
                    
                    return TranscriptionResult(
                        text=full_text.strip(),
                        language=info.language,
                        confidence=info.language_probability,
                        duration=info.duration,
                        segments=[{
                            "start": s.start,
                            "end": s.end,
                            "text": s.text
                        } for s in segments_list]
                    )
                    
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    async def transcribe_base64(
        self,
        audio_base64: str,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribe base64 encoded audio"""
        audio_data = base64.b64decode(audio_base64)
        return await self.transcribe(audio_data, language)
    
    async def text_to_speech(
        self,
        text: str,
        language: str = "tr",
        voice_gender: str = "male",  # "male" or "female"
        rate: str = "+0%",  # Speed adjustment
        pitch: str = "+0Hz",  # Pitch adjustment
        volume: str = "+0%"  # Volume adjustment
    ) -> TTSResult:
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            language: Language code
            voice_gender: "male" or "female"
            rate: Speed adjustment (e.g., "+20%", "-10%")
            pitch: Pitch adjustment (e.g., "+5Hz", "-5Hz")
            volume: Volume adjustment
        
        Returns:
            TTSResult with audio data
        """
        if self.tts_engine == "edge_tts":
            return await self._edge_tts(text, language, voice_gender, rate, pitch, volume)
        elif self.tts_engine:
            return await self._pyttsx3_tts(text, language, rate)
        else:
            raise RuntimeError("No TTS engine available")
    
    async def _edge_tts(
        self,
        text: str,
        language: str,
        voice_gender: str,
        rate: str,
        pitch: str,
        volume: str
    ) -> TTSResult:
        """Use edge-tts for high-quality neural TTS"""
        import edge_tts
        
        # Select voice
        voices = self.tts_voices_female if voice_gender == "female" else self.tts_voices
        voice = voices.get(language, voices["en"])
        
        # Create communicate object
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )
        
        # Generate audio
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        
        return TTSResult(
            audio_data=audio_data,
            format="mp3",
            sample_rate=24000,
            duration=len(audio_data) / 24000  # Approximate
        )
    
    async def _pyttsx3_tts(
        self,
        text: str,
        language: str,
        rate: str
    ) -> TTSResult:
        """Use pyttsx3 for offline TTS"""
        import pyttsx3
        
        # Create temp file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            engine = pyttsx3.init()
            
            # Set rate
            current_rate = engine.getProperty('rate')
            rate_adjust = int(rate.replace('%', '').replace('+', ''))
            engine.setProperty('rate', current_rate + rate_adjust)
            
            # Save to file
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # Read audio data
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            return TTSResult(
                audio_data=audio_data,
                format="wav",
                sample_rate=22050,
                duration=len(audio_data) / 44100
            )
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def text_to_speech_base64(
        self,
        text: str,
        language: str = "tr",
        voice_gender: str = "male"
    ) -> str:
        """Convert text to speech and return base64 encoded audio"""
        result = await self.text_to_speech(text, language, voice_gender)
        return base64.b64encode(result.audio_data).decode('utf-8')
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        return [
            {"code": "tr", "name": "Türkçe", "name_en": "Turkish"},
            {"code": "en", "name": "English", "name_en": "English"},
            {"code": "de", "name": "Deutsch", "name_en": "German"},
            {"code": "fr", "name": "Français", "name_en": "French"},
            {"code": "es", "name": "Español", "name_en": "Spanish"},
            {"code": "it", "name": "Italiano", "name_en": "Italian"},
            {"code": "ja", "name": "日本語", "name_en": "Japanese"},
            {"code": "zh", "name": "中文", "name_en": "Chinese"},
            {"code": "ko", "name": "한국어", "name_en": "Korean"},
            {"code": "ru", "name": "Русский", "name_en": "Russian"},
            {"code": "ar", "name": "العربية", "name_en": "Arabic"},
            {"code": "pt", "name": "Português", "name_en": "Portuguese"},
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """Get Voice AI status"""
        return {
            "initialized": self.is_initialized,
            "stt_available": self.whisper_model is not None,
            "stt_model": self.whisper_model_name if self.whisper_model else None,
            "tts_available": self.tts_engine is not None,
            "tts_engine": "edge_tts" if self.tts_engine == "edge_tts" else "pyttsx3" if self.tts_engine else None,
            "supported_languages": len(self.tts_voices)
        }


# Global instance
voice_ai = VoiceAI()


async def get_voice_ai() -> VoiceAI:
    """Get or initialize Voice AI instance"""
    if not voice_ai.is_initialized:
        await voice_ai.initialize()
    return voice_ai
