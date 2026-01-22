"""
Screen Recording API Endpoints
Record screen and analyze with AI
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screen-recording", tags=["Screen Recording"])

_recorder = None

def get_recorder():
    global _recorder
    if _recorder is None:
        from core.screen_recorder import get_screen_recorder
        _recorder = get_screen_recorder()
    return _recorder


class StartRecordingRequest(BaseModel):
    name: str = "Recording"
    fps: int = 2
    monitor: int = 0
    max_duration: int = 300


class AnalyzeRequest(BaseModel):
    sample_interval: int = 5


class TutorialRequest(BaseModel):
    title: str = "Tutorial"


@router.get("/status")
async def get_status():
    """Get screen recording status"""
    try:
        recorder = get_recorder()
        return {
            "status": "available",
            "current_recording": recorder.current_recording,
            "recording_count": len(recorder.recordings)
        }
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


@router.post("/capture")
async def capture_screen(monitor: int = 0):
    """Capture current screen"""
    recorder = get_recorder()
    image_base64 = recorder.capture_screen_base64(monitor)
    
    if not image_base64:
        raise HTTPException(status_code=500, detail="Screen capture failed")
    
    return {
        "image": image_base64,
        "format": "jpeg"
    }


@router.get("/capture/image")
async def capture_screen_image(monitor: int = 0):
    """Get screen capture as image file"""
    recorder = get_recorder()
    image_data = recorder.capture_screen(monitor)
    
    if not image_data:
        raise HTTPException(status_code=500, detail="Screen capture failed")
    
    return StreamingResponse(
        io.BytesIO(image_data),
        media_type="image/jpeg"
    )


@router.post("/start")
async def start_recording(request: StartRecordingRequest):
    """Start a new screen recording"""
    try:
        recorder = get_recorder()
        recording_id = recorder.start_recording(
            name=request.name,
            fps=request.fps,
            monitor=request.monitor,
            max_duration=request.max_duration
        )
        
        return {
            "recording_id": recording_id,
            "status": "recording",
            "fps": request.fps,
            "max_duration": request.max_duration
        }
        
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_recording():
    """Stop current recording"""
    recorder = get_recorder()
    recording = recorder.stop_recording()
    
    if not recording:
        raise HTTPException(status_code=400, detail="No recording in progress")
    
    return {
        "recording_id": recording.id,
        "status": recording.status.value,
        "frame_count": len(recording.frames),
        "duration": recording.duration
    }


@router.get("/recordings")
async def list_recordings():
    """List all recordings"""
    recorder = get_recorder()
    return {"recordings": recorder.list_recordings()}


@router.get("/recordings/{recording_id}")
async def get_recording(recording_id: str):
    """Get recording details"""
    recorder = get_recorder()
    recording = recorder.get_recording(recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return {
        "id": recording.id,
        "name": recording.name,
        "status": recording.status.value,
        "frame_count": len(recording.frames),
        "duration": recording.duration,
        "fps": recording.fps,
        "start_time": recording.start_time.isoformat() if recording.start_time else None,
        "end_time": recording.end_time.isoformat() if recording.end_time else None,
        "analysis_summary": recording.analysis_summary,
        "tutorial_steps": recording.tutorial_steps,
        "error": recording.error
    }


@router.delete("/recordings/{recording_id}")
async def delete_recording(recording_id: str):
    """Delete a recording"""
    recorder = get_recorder()
    if recorder.delete_recording(recording_id):
        return {"status": "deleted", "recording_id": recording_id}
    raise HTTPException(status_code=404, detail="Recording not found")


@router.get("/recordings/{recording_id}/frames/{frame_index}")
async def get_frame(recording_id: str, frame_index: int):
    """Get a specific frame image"""
    recorder = get_recorder()
    image_data = recorder.get_frame_image(recording_id, frame_index)
    
    if not image_data:
        raise HTTPException(status_code=404, detail="Frame not found")
    
    return StreamingResponse(
        io.BytesIO(image_data),
        media_type="image/jpeg"
    )


@router.post("/recordings/{recording_id}/analyze")
async def analyze_recording(recording_id: str, request: AnalyzeRequest):
    """Analyze recording with AI"""
    try:
        recorder = get_recorder()
        result = await recorder.analyze_recording(
            recording_id,
            sample_interval=request.sample_interval
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recordings/{recording_id}/tutorial")
async def generate_tutorial(recording_id: str, request: TutorialRequest):
    """Generate tutorial from recording"""
    try:
        recorder = get_recorder()
        result = await recorder.generate_tutorial(
            recording_id,
            title=request.title
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Tutorial generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recordings/{recording_id}/export")
async def export_recording(recording_id: str):
    """Export recording metadata"""
    recorder = get_recorder()
    data = recorder.export_recording(recording_id)
    
    if not data:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return data
