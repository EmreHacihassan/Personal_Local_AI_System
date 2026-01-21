"""
Agent API Endpoints
===================

Autonomous Agent için REST ve WebSocket API'leri.

Endpoints:
    POST /api/agent/tasks              - Yeni görev oluştur
    GET  /api/agent/tasks              - Tüm görevleri listele
    GET  /api/agent/tasks/{task_id}    - Görev detayı
    POST /api/agent/tasks/{task_id}/start      - Görevi başlat
    POST /api/agent/tasks/{task_id}/cancel     - Görevi iptal et
    POST /api/agent/tasks/{task_id}/respond    - Intervention yanıtla
    GET  /api/agent/tools              - Mevcut araçları listele
    WS   /ws/agent/{task_id}           - Streaming task execution

Author: Enterprise AI Assistant
Date: 2026-01-20
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.autonomous_agent import (
    AutonomousAgent,
    StreamingAutonomousAgent,
    AgentTask,
    TaskStatus,
    InterventionType,
    get_autonomous_agent,
    get_streaming_agent,
)
from tools.tool_manager import tool_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Agent"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateTaskRequest(BaseModel):
    """Görev oluşturma isteği."""
    request: str = Field(..., min_length=3, max_length=5000, description="Kullanıcı isteği")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Ek bağlam")
    auto_start: bool = Field(default=False, description="Otomatik başlat")
    
    class Config:
        json_schema_extra = {
            "example": {
                "request": "Python'da web scraping projesi oluştur",
                "context": {"language": "python", "framework": "beautifulsoup"},
                "auto_start": True
            }
        }


class TaskResponse(BaseModel):
    """Görev yanıtı."""
    success: bool = True
    task: Dict[str, Any]
    message: Optional[str] = None


class TaskListResponse(BaseModel):
    """Görev listesi yanıtı."""
    success: bool = True
    tasks: List[Dict[str, Any]]
    total: int


class InterventionResponse(BaseModel):
    """Intervention yanıt isteği."""
    response: str = Field(..., min_length=1, description="Kullanıcı yanıtı")


class ToolListResponse(BaseModel):
    """Araç listesi yanıtı."""
    success: bool = True
    tools: List[Dict[str, str]]
    total: int


# =============================================================================
# REST ENDPOINTS
# =============================================================================

@router.post("/tasks", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest) -> TaskResponse:
    """
    Yeni otonom görev oluştur.
    
    Görev oluşturulur ve isteğe bağlı olarak otomatik başlatılır.
    """
    try:
        agent = get_autonomous_agent()
        
        # Create task
        task = await agent.create_task(
            user_request=request.request,
            context=request.context,
        )
        
        # Auto-start if requested
        if request.auto_start:
            # Start in background
            asyncio.create_task(agent.run_task(task))
            message = "Görev oluşturuldu ve başlatıldı"
        else:
            message = "Görev oluşturuldu"
        
        return TaskResponse(
            success=True,
            task=task.to_dict(),
            message=message,
        )
        
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
) -> TaskListResponse:
    """
    Tüm görevleri listele.
    
    İsteğe bağlı olarak durum filtrelemesi yapılabilir.
    """
    try:
        agent = get_autonomous_agent()
        tasks = agent.get_all_tasks()
        
        # Filter by status if provided
        if status:
            try:
                status_enum = TaskStatus(status)
                tasks = [t for t in tasks if t.status == status_enum]
            except ValueError:
                pass
        
        # Limit
        tasks = tasks[-limit:]
        
        return TaskListResponse(
            success=True,
            tasks=[t.to_dict() for t in tasks],
            total=len(tasks),
        )
        
    except Exception as e:
        logger.error(f"Task list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """
    Görev detaylarını al.
    
    Plan, adımlar, ilerleme ve sonuçlar dahil.
    """
    try:
        agent = get_autonomous_agent()
        task = agent.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        return TaskResponse(
            success=True,
            task=task.to_dict(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/start", response_model=TaskResponse)
async def start_task(task_id: str) -> TaskResponse:
    """
    Görevi başlat veya devam ettir.
    
    Pending veya paused durumundaki görevler için.
    """
    try:
        agent = get_autonomous_agent()
        task = agent.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        if task.status not in [TaskStatus.PENDING, TaskStatus.PAUSED, TaskStatus.WAITING_HUMAN]:
            raise HTTPException(
                status_code=400, 
                detail=f"Görev başlatılamaz: {task.status.value}"
            )
        
        # Start in background
        asyncio.create_task(agent.run_task(task))
        
        return TaskResponse(
            success=True,
            task=task.to_dict(),
            message="Görev başlatıldı",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: str) -> TaskResponse:
    """
    Görevi iptal et.
    
    Devam eden görevleri durdurur.
    """
    try:
        agent = get_autonomous_agent()
        
        success = agent.cancel_task(task_id)
        
        if not success:
            task = agent.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Görev bulunamadı")
            raise HTTPException(
                status_code=400, 
                detail=f"Görev iptal edilemez: {task.status.value}"
            )
        
        task = agent.get_task(task_id)
        
        return TaskResponse(
            success=True,
            task=task.to_dict(),
            message="Görev iptal edildi",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/respond", response_model=TaskResponse)
async def respond_to_intervention(
    task_id: str,
    request: InterventionResponse,
) -> TaskResponse:
    """
    Human intervention'a yanıt ver.
    
    Kullanıcı onayı veya girdisi gerektiren görevler için.
    """
    try:
        agent = get_autonomous_agent()
        
        task = await agent.respond_to_intervention(task_id, request.response)
        
        return TaskResponse(
            success=True,
            task=task.to_dict(),
            message="Yanıt alındı",
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Respond error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: str) -> Dict[str, Any]:
    """
    Görev ilerleme durumunu al.
    
    Adım bazında detaylı ilerleme bilgisi.
    """
    try:
        agent = get_autonomous_agent()
        task = agent.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Görev bulunamadı")
        
        progress = {
            "task_id": task.id,
            "status": task.status.value,
            "plan": None,
            "progress": None,
            "current_step": None,
            "pending_intervention": None,
        }
        
        if task.plan:
            progress["plan"] = {
                "goal": task.plan.goal,
                "total_steps": task.plan.total_steps,
            }
            progress["progress"] = task.plan.get_progress()
            progress["current_step"] = task.plan.current_step
        
        if task.pending_intervention:
            progress["pending_intervention"] = task.pending_intervention.to_dict()
        
        return progress
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Progress error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", response_model=ToolListResponse)
async def list_tools() -> ToolListResponse:
    """
    Mevcut agent araçlarını listele.
    
    Agent'ın kullanabileceği tüm araçlar.
    """
    try:
        tools = tool_manager.list_tools()
        
        return ToolListResponse(
            success=True,
            tools=tools,
            total=len(tools),
        )
        
    except Exception as e:
        logger.error(f"List tools error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STREAMING ENDPOINT
# =============================================================================

@router.post("/tasks/{task_id}/stream")
async def stream_task_execution(task_id: str):
    """
    Görev yürütmesini SSE olarak stream et.
    
    Gerçek zamanlı progress güncellemeleri.
    """
    agent = get_streaming_agent()
    task = agent.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    
    async def generate():
        try:
            async for event in agent.run_task_streaming(task):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =============================================================================
# WEBSOCKET ENDPOINT
# =============================================================================

@router.websocket("/ws/{task_id}")
async def websocket_task_execution(websocket: WebSocket, task_id: str):
    """
    WebSocket üzerinden görev yürütme.
    
    Bidirectional communication:
    - Server → Client: Progress updates
    - Client → Server: Intervention responses
    """
    await websocket.accept()
    
    agent = get_streaming_agent()
    
    try:
        # Create or get task
        task = agent.get_task(task_id)
        
        if not task:
            await websocket.send_json({
                "type": "error",
                "message": "Görev bulunamadı",
            })
            await websocket.close()
            return
        
        # Start streaming execution
        async for event in agent.run_task_streaming(task):
            await websocket.send_json(event)
            
            # Check for intervention
            if event.get("type") == "intervention_required":
                # Wait for response
                try:
                    response_data = await asyncio.wait_for(
                        websocket.receive_json(),
                        timeout=300.0,  # 5 minutes
                    )
                    
                    if response_data.get("type") == "intervention_response":
                        await agent.respond_to_intervention(
                            task_id,
                            response_data.get("response", ""),
                        )
                        
                        # Continue execution
                        async for event in agent.run_task_streaming(task):
                            await websocket.send_json(event)
                            
                except asyncio.TimeoutError:
                    await websocket.send_json({
                        "type": "timeout",
                        "message": "Intervention yanıt süresi doldu",
                    })
                    break
        
        await websocket.send_json({
            "type": "connection_closed",
            "task_id": task_id,
            "final_status": task.status.value,
        })
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# =============================================================================
# QUICK AGENT ENDPOINT
# =============================================================================

@router.post("/quick")
async def quick_agent_task(request: CreateTaskRequest):
    """
    Hızlı agent görevi - tek seferde planla ve çalıştır.
    
    Streaming response ile sonucu döndürür.
    """
    agent = get_streaming_agent()
    
    # Create task
    task = await agent.create_task(
        user_request=request.request,
        context=request.context,
    )
    
    async def generate():
        try:
            async for event in agent.run_task_streaming(task):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                
                # If intervention required, skip (quick mode)
                if event.get("type") == "intervention_required":
                    yield f"data: {json.dumps({'type': 'skipped', 'reason': 'Quick mode - intervention skipped'})}\n\n"
                    break
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# =============================================================================
# STATS ENDPOINT
# =============================================================================

@router.get("/stats")
async def get_agent_stats() -> Dict[str, Any]:
    """
    Agent istatistiklerini al.
    
    Görev sayıları, başarı oranları, araç kullanımı vb.
    """
    try:
        agent = get_autonomous_agent()
        tasks = agent.get_all_tasks()
        
        # Calculate stats
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        waiting = sum(1 for t in tasks if t.status == TaskStatus.WAITING_HUMAN)
        
        avg_duration = 0
        if completed > 0:
            durations = [t.total_duration_ms for t in tasks if t.status == TaskStatus.COMPLETED]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Tool stats
        tool_stats = tool_manager.get_stats()
        
        return {
            "success": True,
            "tasks": {
                "total": total_tasks,
                "completed": completed,
                "failed": failed,
                "in_progress": in_progress,
                "waiting_human": waiting,
                "success_rate": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            },
            "performance": {
                "avg_duration_ms": avg_duration,
            },
            "tools": tool_stats,
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

def get_router() -> APIRouter:
    """Router instance'ını döndür."""
    return router
