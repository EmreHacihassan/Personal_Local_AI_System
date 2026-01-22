"""
Screen Recording with AI Analysis
Record screen, analyze with Vision AI, create tutorials
100% Local processing
"""

import asyncio
import base64
import json
import logging
import os
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import io

logger = logging.getLogger(__name__)

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False
    logger.warning("mss not installed. Install with: pip install mss")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class RecordingStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Frame:
    """A single frame from recording"""
    index: int
    timestamp: float
    image_data: bytes
    width: int
    height: int
    analysis: Optional[str] = None
    events: List[Dict] = field(default_factory=list)  # Mouse/keyboard events


@dataclass
class Recording:
    """A screen recording session"""
    id: str
    name: str
    frames: List[Frame] = field(default_factory=list)
    status: RecordingStatus = RecordingStatus.IDLE
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    fps: int = 2  # Frames per second (low for AI analysis)
    duration: float = 0
    analysis_summary: Optional[str] = None
    tutorial_steps: List[Dict] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class ScreenAnalysis:
    """Analysis result for a screen/frame"""
    description: str
    detected_elements: List[Dict]  # buttons, text fields, windows
    actions_detected: List[str]  # what user might be doing
    suggestions: List[str]  # improvement suggestions


class ScreenRecorder:
    """
    Screen recorder with AI analysis capabilities
    """
    
    def __init__(self, storage_dir: str = "data/recordings"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.recordings: Dict[str, Recording] = {}
        self.current_recording: Optional[str] = None
        self._recording_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        if HAS_MSS:
            self.sct = mss.mss()
        else:
            self.sct = None
    
    def capture_screen(
        self,
        monitor: int = 0,
        quality: int = 70
    ) -> Optional[bytes]:
        """Capture current screen as JPEG bytes"""
        if not HAS_MSS or not self.sct:
            return None
        
        try:
            # Get monitor (0 = all monitors, 1+ = specific monitor)
            mon = self.sct.monitors[monitor]
            
            # Capture
            screenshot = self.sct.grab(mon)
            
            if HAS_PIL:
                # Convert to PIL and compress
                img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                
                # Resize for efficiency
                max_size = 1920
                if img.width > max_size:
                    ratio = max_size / img.width
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to JPEG
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality)
                return buffer.getvalue()
            else:
                # Return raw PNG
                return mss.tools.to_png(screenshot.rgb, screenshot.size)
                
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return None
    
    def capture_screen_base64(self, monitor: int = 0) -> Optional[str]:
        """Capture screen and return as base64"""
        data = self.capture_screen(monitor)
        if data:
            return base64.b64encode(data).decode('utf-8')
        return None
    
    def start_recording(
        self,
        name: str = "Recording",
        fps: int = 2,
        monitor: int = 0,
        max_duration: int = 300  # 5 minutes max
    ) -> str:
        """Start a new recording session"""
        if self.current_recording:
            raise RuntimeError("Recording already in progress")
        
        recording_id = str(uuid.uuid4())[:8]
        
        recording = Recording(
            id=recording_id,
            name=name,
            status=RecordingStatus.RECORDING,
            start_time=datetime.now(),
            fps=fps
        )
        
        self.recordings[recording_id] = recording
        self.current_recording = recording_id
        
        # Start recording thread
        self._stop_event.clear()
        self._recording_thread = threading.Thread(
            target=self._record_loop,
            args=(recording_id, monitor, fps, max_duration)
        )
        self._recording_thread.start()
        
        logger.info(f"Started recording: {recording_id}")
        return recording_id
    
    def _record_loop(
        self,
        recording_id: str,
        monitor: int,
        fps: int,
        max_duration: int
    ):
        """Background recording loop"""
        recording = self.recordings.get(recording_id)
        if not recording:
            return
        
        frame_interval = 1.0 / fps
        start_time = time.time()
        frame_index = 0
        
        try:
            while not self._stop_event.is_set():
                # Check duration limit
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    break
                
                # Capture frame
                frame_start = time.time()
                image_data = self.capture_screen(monitor)
                
                if image_data:
                    frame = Frame(
                        index=frame_index,
                        timestamp=elapsed,
                        image_data=image_data,
                        width=1920,  # TODO: Get actual size
                        height=1080
                    )
                    recording.frames.append(frame)
                    frame_index += 1
                
                # Wait for next frame
                elapsed_frame = time.time() - frame_start
                sleep_time = max(0, frame_interval - elapsed_frame)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            recording.duration = time.time() - start_time
            recording.status = RecordingStatus.COMPLETED
            recording.end_time = datetime.now()
            
        except Exception as e:
            recording.status = RecordingStatus.ERROR
            recording.error = str(e)
            logger.error(f"Recording error: {e}")
        
        self.current_recording = None
        logger.info(f"Recording stopped: {recording_id}, {len(recording.frames)} frames")
    
    def stop_recording(self) -> Optional[Recording]:
        """Stop current recording"""
        if not self.current_recording:
            return None
        
        recording_id = self.current_recording
        self._stop_event.set()
        
        if self._recording_thread:
            self._recording_thread.join(timeout=5)
        
        return self.recordings.get(recording_id)
    
    def pause_recording(self):
        """Pause current recording"""
        if self.current_recording:
            recording = self.recordings[self.current_recording]
            recording.status = RecordingStatus.PAUSED
            self._stop_event.set()
    
    def get_recording(self, recording_id: str) -> Optional[Recording]:
        """Get recording by ID"""
        return self.recordings.get(recording_id)
    
    def list_recordings(self) -> List[Dict]:
        """List all recordings"""
        return [
            {
                "id": r.id,
                "name": r.name,
                "status": r.status.value,
                "frame_count": len(r.frames),
                "duration": r.duration,
                "start_time": r.start_time.isoformat() if r.start_time else None
            }
            for r in self.recordings.values()
        ]
    
    def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording"""
        if recording_id in self.recordings:
            del self.recordings[recording_id]
            return True
        return False
    
    async def analyze_frame(
        self,
        frame: Frame,
        question: Optional[str] = None
    ) -> ScreenAnalysis:
        """Analyze a single frame with Vision AI"""
        try:
            from core.vision_ai import get_vision_ai
            
            vision = await get_vision_ai()
            
            prompt = question or "Describe what you see on this screen. What application is open? What is the user doing? What UI elements are visible?"
            
            analysis = await vision.analyze_image(
                frame.image_data,
                prompt=prompt
            )
            
            frame.analysis = analysis.description
            
            return ScreenAnalysis(
                description=analysis.description,
                detected_elements=analysis.detected_objects,
                actions_detected=[],
                suggestions=[]
            )
            
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return ScreenAnalysis(
                description=f"Analysis failed: {e}",
                detected_elements=[],
                actions_detected=[],
                suggestions=[]
            )
    
    async def analyze_recording(
        self,
        recording_id: str,
        sample_interval: int = 5  # Analyze every Nth frame
    ) -> Dict:
        """Analyze entire recording and generate summary"""
        recording = self.recordings.get(recording_id)
        if not recording:
            raise ValueError("Recording not found")
        
        recording.status = RecordingStatus.PROCESSING
        
        try:
            # Sample frames for analysis
            frames_to_analyze = recording.frames[::sample_interval]
            analyses = []
            
            for frame in frames_to_analyze:
                analysis = await self.analyze_frame(frame)
                analyses.append({
                    "timestamp": frame.timestamp,
                    "description": analysis.description
                })
            
            # Generate summary with LLM
            from core.llm_client import get_llm_client
            llm = await get_llm_client()
            
            analysis_text = "\n".join([
                f"[{a['timestamp']:.1f}s] {a['description'][:200]}"
                for a in analyses
            ])
            
            summary_prompt = f"""Based on the following screen recording analysis, provide:
1. A summary of what the user was doing
2. Key steps performed
3. Any issues or suggestions for improvement

Recording Analysis:
{analysis_text}

Summary:"""
            
            summary = await llm.chat(summary_prompt)
            recording.analysis_summary = summary
            
            # Generate tutorial steps
            steps_prompt = f"""Based on this recording analysis, create step-by-step tutorial instructions:

{analysis_text}

Format as numbered steps:"""
            
            steps_response = await llm.chat(steps_prompt)
            
            # Parse steps (simple line-based)
            steps = []
            for line in steps_response.split('\n'):
                line = line.strip()
                if line and line[0].isdigit():
                    steps.append({"step": len(steps) + 1, "instruction": line})
            
            recording.tutorial_steps = steps
            recording.status = RecordingStatus.COMPLETED
            
            return {
                "recording_id": recording_id,
                "summary": summary,
                "steps": steps,
                "frames_analyzed": len(analyses)
            }
            
        except Exception as e:
            recording.status = RecordingStatus.ERROR
            recording.error = str(e)
            raise
    
    async def generate_tutorial(
        self,
        recording_id: str,
        title: str = "Tutorial"
    ) -> Dict:
        """Generate a tutorial from recording"""
        recording = self.recordings.get(recording_id)
        if not recording:
            raise ValueError("Recording not found")
        
        # Ensure recording is analyzed
        if not recording.analysis_summary:
            await self.analyze_recording(recording_id)
        
        # Generate markdown tutorial
        tutorial_md = f"# {title}\n\n"
        tutorial_md += f"**Duration:** {recording.duration:.1f} seconds\n\n"
        tutorial_md += "## Overview\n\n"
        tutorial_md += recording.analysis_summary or "No summary available.\n"
        tutorial_md += "\n\n## Steps\n\n"
        
        for step in recording.tutorial_steps:
            tutorial_md += f"{step['step']}. {step['instruction']}\n"
        
        # Add key frames
        tutorial_md += "\n\n## Screenshots\n\n"
        
        key_frames = recording.frames[::max(1, len(recording.frames) // 5)]  # 5 key frames
        for i, frame in enumerate(key_frames[:5]):
            if frame.analysis:
                tutorial_md += f"### Step {i+1}\n"
                tutorial_md += f"*{frame.analysis[:200]}...*\n\n"
        
        return {
            "recording_id": recording_id,
            "title": title,
            "tutorial_markdown": tutorial_md,
            "steps": recording.tutorial_steps,
            "key_frame_count": len(key_frames)
        }
    
    def get_frame_image(
        self,
        recording_id: str,
        frame_index: int
    ) -> Optional[bytes]:
        """Get image data for a specific frame"""
        recording = self.recordings.get(recording_id)
        if not recording:
            return None
        
        if frame_index < 0 or frame_index >= len(recording.frames):
            return None
        
        return recording.frames[frame_index].image_data
    
    def export_recording(
        self,
        recording_id: str,
        format: str = "json"
    ) -> Optional[Dict]:
        """Export recording metadata"""
        recording = self.recordings.get(recording_id)
        if not recording:
            return None
        
        return {
            "id": recording.id,
            "name": recording.name,
            "status": recording.status.value,
            "duration": recording.duration,
            "fps": recording.fps,
            "frame_count": len(recording.frames),
            "start_time": recording.start_time.isoformat() if recording.start_time else None,
            "end_time": recording.end_time.isoformat() if recording.end_time else None,
            "analysis_summary": recording.analysis_summary,
            "tutorial_steps": recording.tutorial_steps,
            "frames": [
                {
                    "index": f.index,
                    "timestamp": f.timestamp,
                    "analysis": f.analysis
                }
                for f in recording.frames
            ]
        }


# Global instance
screen_recorder = ScreenRecorder()


def get_screen_recorder() -> ScreenRecorder:
    """Get screen recorder instance"""
    return screen_recorder
