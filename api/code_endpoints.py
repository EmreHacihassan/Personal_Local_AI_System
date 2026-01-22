"""
Code Interpreter API Endpoints
Execute Python/JS code safely with visualization support
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Any
import base64
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/code", tags=["Code Interpreter"])

# Lazy import
_interpreter = None

def get_interpreter():
    global _interpreter
    if _interpreter is None:
        from core.code_interpreter import get_code_interpreter
        _interpreter = get_code_interpreter()
    return _interpreter


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"  # python, javascript
    session_id: Optional[str] = None
    timeout: Optional[int] = 30


class ExecuteResponse(BaseModel):
    execution_id: str
    session_id: Optional[str]
    status: str
    stdout: str
    stderr: str
    return_value: Any
    execution_time: float
    plots: List[str]  # Base64 encoded images
    created_files: List[str]
    error: Optional[str]


class SessionInfo(BaseModel):
    id: str
    created_at: str
    files: List[str]
    history_count: int


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(request: ExecuteRequest):
    """
    Execute code in sandbox
    
    Supported languages: python, javascript
    Returns stdout, stderr, plots (base64), and created files
    """
    try:
        interpreter = get_interpreter()
        
        # Map language string
        from core.code_interpreter import ExecutionLanguage
        lang_map = {
            "python": ExecutionLanguage.PYTHON,
            "javascript": ExecutionLanguage.JAVASCRIPT,
            "js": ExecutionLanguage.JAVASCRIPT,
        }
        language = lang_map.get(request.language.lower(), ExecutionLanguage.PYTHON)
        
        # Execute
        result = await interpreter.execute(
            code=request.code,
            language=language,
            session_id=request.session_id,
            timeout=request.timeout
        )
        
        # Get session ID if created
        session_id = request.session_id
        if not session_id:
            # Find latest session
            if interpreter.sessions:
                session_id = list(interpreter.sessions.keys())[-1]
        
        return ExecuteResponse(
            execution_id=result.execution_id,
            session_id=session_id,
            status=result.status.value,
            stdout=result.stdout,
            stderr=result.stderr,
            return_value=result.return_value,
            execution_time=result.execution_time,
            plots=result.plots,
            created_files=result.created_files,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session", response_model=SessionInfo)
async def create_session():
    """Create a new code execution session"""
    try:
        interpreter = get_interpreter()
        session_id = interpreter.create_session()
        session = interpreter.get_session(session_id)
        
        return SessionInfo(
            id=session["id"],
            created_at=session["created_at"],
            files=[],
            history_count=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session info"""
    interpreter = get_interpreter()
    session = interpreter.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionInfo(
        id=session["id"],
        created_at=session["created_at"],
        files=session.get("files", []),
        history_count=len(session.get("history", []))
    )


@router.delete("/session/{session_id}")
async def close_session(session_id: str):
    """Close and cleanup session"""
    interpreter = get_interpreter()
    if interpreter.close_session(session_id):
        return {"status": "closed", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/session/{session_id}/files")
async def list_session_files(session_id: str):
    """List files in session"""
    interpreter = get_interpreter()
    files = interpreter.get_session_files(session_id)
    return {"session_id": session_id, "files": files}


@router.get("/session/{session_id}/files/{filename}")
async def download_session_file(session_id: str, filename: str):
    """Download file from session"""
    interpreter = get_interpreter()
    content = interpreter.read_session_file(session_id, filename)
    
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type
    content_type = "application/octet-stream"
    if filename.endswith('.png'):
        content_type = "image/png"
    elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
        content_type = "image/jpeg"
    elif filename.endswith('.csv'):
        content_type = "text/csv"
    elif filename.endswith('.json'):
        content_type = "application/json"
    elif filename.endswith('.txt'):
        content_type = "text/plain"
    
    return StreamingResponse(
        io.BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/session/{session_id}/upload")
async def upload_to_session(session_id: str, file: UploadFile = File(...)):
    """Upload file to session for processing"""
    interpreter = get_interpreter()
    session = interpreter.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    from pathlib import Path
    work_dir = Path(session["work_dir"])
    file_path = work_dir / file.filename
    
    content = await file.read()
    file_path.write_bytes(content)
    
    return {
        "status": "uploaded",
        "filename": file.filename,
        "size": len(content)
    }


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get execution history for session"""
    interpreter = get_interpreter()
    session = interpreter.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "history": session.get("history", [])
    }


# Quick execute without session management
@router.post("/run")
async def quick_run(code: str, language: str = "python"):
    """
    Quick code execution (no persistent session)
    
    Good for one-off calculations
    """
    try:
        interpreter = get_interpreter()
        
        from core.code_interpreter import ExecutionLanguage
        lang_map = {
            "python": ExecutionLanguage.PYTHON,
            "javascript": ExecutionLanguage.JAVASCRIPT,
        }
        lang = lang_map.get(language.lower(), ExecutionLanguage.PYTHON)
        
        result = await interpreter.execute(code=code, language=lang, timeout=10)
        
        return {
            "status": result.status.value,
            "output": result.stdout or result.stderr,
            "result": result.return_value,
            "plots": result.plots,
            "error": result.error,
            "time": result.execution_time
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
