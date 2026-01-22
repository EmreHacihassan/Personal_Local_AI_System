"""
Voice AI API Endpoints
Premium voice assistant with STT/TTS capabilities
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import base64
import io
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["Voice AI"])

# Lazy import to avoid startup issues
voice_ai_instance = None

async def get_voice_ai():
    global voice_ai_instance
    if voice_ai_instance is None:
        try:
            from core.voice_ai import get_voice_ai as _get_voice_ai
            voice_ai_instance = await _get_voice_ai()
        except Exception as e:
            logger.error(f"Failed to initialize Voice AI: {e}")
            raise HTTPException(status_code=503, detail=f"Voice AI not available: {str(e)}")
    return voice_ai_instance


class TTSRequest(BaseModel):
    text: str
    language: str = "tr"
    voice_gender: str = "male"
    rate: str = "+0%"
    pitch: str = "+0Hz"
    format: str = "mp3"  # mp3 or wav


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float
    duration: float
    segments: List[dict]


class TTSResponse(BaseModel):
    audio_base64: str
    format: str
    duration: float


class VoiceStatus(BaseModel):
    initialized: bool
    stt_available: bool
    stt_model: Optional[str]
    tts_available: bool
    tts_engine: Optional[str]
    supported_languages: int


@router.get("/status", response_model=VoiceStatus)
async def get_status():
    """Get Voice AI status"""
    try:
        voice = await get_voice_ai()
        return voice.get_status()
    except Exception as e:
        return VoiceStatus(
            initialized=False,
            stt_available=False,
            stt_model=None,
            tts_available=False,
            tts_engine=None,
            supported_languages=0
        )


@router.get("/languages")
async def get_languages():
    """Get supported languages"""
    try:
        voice = await get_voice_ai()
        return {"languages": voice.get_supported_languages()}
    except Exception as e:
        # Return default languages even if voice AI not initialized
        return {"languages": [
            {"code": "tr", "name": "Türkçe", "name_en": "Turkish"},
            {"code": "en", "name": "English", "name_en": "English"},
            {"code": "de", "name": "Deutsch", "name_en": "German"},
        ]}


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None)
):
    """
    Transcribe audio file to text
    
    Supports: WAV, MP3, FLAC, OGG, M4A
    """
    try:
        voice = await get_voice_ai()
        
        # Read audio data
        audio_data = await audio.read()
        
        # Transcribe
        result = await voice.transcribe(audio_data, language)
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration=result.duration,
            segments=result.segments
        )
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transcribe/base64", response_model=TranscriptionResponse)
async def transcribe_base64(
    audio_base64: str,
    language: Optional[str] = None
):
    """Transcribe base64 encoded audio"""
    try:
        voice = await get_voice_ai()
        result = await voice.transcribe_base64(audio_base64, language)
        
        return TranscriptionResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
            duration=result.duration,
            segments=result.segments
        )
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech
    
    Returns base64 encoded audio
    """
    try:
        voice = await get_voice_ai()
        
        result = await voice.text_to_speech(
            text=request.text,
            language=request.language,
            voice_gender=request.voice_gender,
            rate=request.rate,
            pitch=request.pitch
        )
        
        return TTSResponse(
            audio_base64=base64.b64encode(result.audio_data).decode('utf-8'),
            format=result.format,
            duration=result.duration
        )
        
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts/stream")
async def text_to_speech_stream(request: TTSRequest):
    """
    Stream TTS audio directly
    
    Returns audio file stream
    """
    try:
        voice = await get_voice_ai()
        
        result = await voice.text_to_speech(
            text=request.text,
            language=request.language,
            voice_gender=request.voice_gender,
            rate=request.rate,
            pitch=request.pitch
        )
        
        # Determine content type
        content_type = "audio/mpeg" if result.format == "mp3" else "audio/wav"
        
        return StreamingResponse(
            io.BytesIO(result.audio_data),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{result.format}"
            }
        )
        
    except Exception as e:
        logger.error(f"TTS stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/conversation")
async def voice_conversation_ws(websocket: WebSocket):
    """
    Real-time voice conversation WebSocket
    
    Protocol:
    - Client sends: {"type": "audio", "data": "<base64 audio>", "language": "tr"}
    - Server responds: {"type": "transcription", "text": "...", "language": "..."}
    - Client sends: {"type": "chat", "text": "...", "language": "tr"}
    - Server responds: {"type": "response", "text": "...", "audio": "<base64>"}
    """
    await websocket.accept()
    
    try:
        voice = await get_voice_ai()
        
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "audio":
                # Transcribe audio
                audio_base64 = data.get("data", "")
                language = data.get("language")
                
                try:
                    result = await voice.transcribe_base64(audio_base64, language)
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result.text,
                        "language": result.language,
                        "confidence": result.confidence
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })
            
            elif msg_type == "tts":
                # Text to speech
                text = data.get("text", "")
                language = data.get("language", "tr")
                voice_gender = data.get("voice_gender", "male")
                
                try:
                    audio_base64 = await voice.text_to_speech_base64(
                        text, language, voice_gender
                    )
                    await websocket.send_json({
                        "type": "audio",
                        "data": audio_base64,
                        "format": "mp3"
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"TTS failed: {str(e)}"
                    })
            
            elif msg_type == "chat":
                # Full conversation: transcribe -> chat -> TTS
                text = data.get("text", "")
                language = data.get("language", "tr")
                
                # Here you would integrate with your chat system
                # For now, echo back
                response_text = f"Mesajınızı aldım: {text}"
                
                try:
                    audio_base64 = await voice.text_to_speech_base64(
                        response_text, language
                    )
                    await websocket.send_json({
                        "type": "response",
                        "text": response_text,
                        "audio": audio_base64
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "response",
                        "text": response_text,
                        "audio": None,
                        "error": str(e)
                    })
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info("Voice conversation WebSocket disconnected")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
