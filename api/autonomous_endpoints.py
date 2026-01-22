"""
Autonomous Agent API Endpoints
Goal-driven AI agent that plans and executes tasks
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/autonomous", tags=["Autonomous Agent"])

_agent = None

def get_agent():
    global _agent
    if _agent is None:
        from core.autonomous_agent import get_autonomous_agent
        _agent = get_autonomous_agent()
    return _agent


class CreateSessionRequest(BaseModel):
    goal: str
    context: Optional[Dict[str, Any]] = None
    max_iterations: int = 20


class SessionResponse(BaseModel):
    id: str
    goal: str
    status: str
    iterations: int
    plan: Optional[Dict] = None
    final_result: Optional[str] = None
    error: Optional[str] = None


@router.get("/status")
async def get_status():
    """Get autonomous agent status"""
    agent = get_agent()
    return {
        "status": "available",
        "active_session": agent.active_session,
        "total_sessions": len(agent.sessions)
    }


@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new autonomous agent session"""
    try:
        agent = get_agent()
        session = await agent.create_session(
            goal=request.goal,
            context=request.context,
            max_iterations=request.max_iterations
        )
        
        return SessionResponse(
            id=session.id,
            goal=session.goal,
            status=session.status.value,
            iterations=session.iterations,
            plan=None,
            final_result=None,
            error=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/run")
async def run_session(session_id: str):
    """Run an autonomous agent session"""
    try:
        agent = get_agent()
        
        # Run in background
        session = await agent.run_session(session_id)
        
        return {
            "id": session.id,
            "status": session.status.value,
            "iterations": session.iterations,
            "plan": agent._serialize_plan(session.plan) if session.plan else None,
            "final_result": session.final_result,
            "error": session.error,
            "duration": (session.end_time - session.start_time).total_seconds() if session.start_time and session.end_time else None
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Session run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """List all sessions"""
    agent = get_agent()
    return {"sessions": agent.list_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    agent = get_agent()
    session = agent.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.id,
        "goal": session.goal,
        "status": session.status.value,
        "iterations": session.iterations,
        "max_iterations": session.max_iterations,
        "plan": agent._serialize_plan(session.plan) if session.plan else None,
        "memory": {
            "short_term_count": len(session.memory.short_term),
            "long_term": session.memory.long_term,
            "working": session.memory.working
        },
        "history": session.history[-10:],  # Last 10 reflections
        "final_result": session.final_result,
        "error": session.error,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None
    }


@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    """Stop a running session"""
    agent = get_agent()
    agent.stop_session(session_id)
    
    session = agent.get_session(session_id)
    if session:
        return {"status": session.status.value, "message": "Stop requested"}
    
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/sessions/{session_id}/actions")
async def get_session_actions(session_id: str):
    """Get all actions from a session"""
    agent = get_agent()
    session = agent.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.plan:
        return {"actions": []}
    
    return {
        "actions": [agent._serialize_action(a) for a in session.plan.actions],
        "current_step": session.plan.current_step
    }


@router.get("/sessions/{session_id}/memory")
async def get_session_memory(session_id: str):
    """Get session memory"""
    agent = get_agent()
    session = agent.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "short_term": session.memory.short_term,
        "long_term": session.memory.long_term,
        "working": session.memory.working
    }


@router.websocket("/ws/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket for real-time session updates
    
    Creates and runs a session with live updates
    """
    await websocket.accept()
    
    try:
        agent = get_agent()
        
        # Receive initial goal
        data = await websocket.receive_json()
        goal = data.get("goal", "")
        context = data.get("context", {})
        max_iterations = data.get("max_iterations", 20)
        
        # Create session
        session = await agent.create_session(goal, context, max_iterations)
        
        await websocket.send_json({
            "type": "session_created",
            "session_id": session.id,
            "goal": goal
        })
        
        # Run with updates
        async def on_update(update: Dict):
            try:
                await websocket.send_json({
                    "type": "update",
                    **update
                })
            except:
                pass
        
        session = await agent.run_session(session.id, on_update=on_update)
        
        # Send final result
        await websocket.send_json({
            "type": "completed",
            "session_id": session.id,
            "status": session.status.value,
            "iterations": session.iterations,
            "final_result": session.final_result,
            "error": session.error
        })
        
    except WebSocketDisconnect:
        logger.info("Autonomous agent WebSocket disconnected")
        agent = get_agent()
        if agent.active_session:
            agent.stop_session(agent.active_session)
    except Exception as e:
        logger.error(f"Autonomous agent WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# Quick run endpoint
@router.post("/run")
async def quick_run(goal: str, context: Optional[Dict] = None, max_iterations: int = 10):
    """
    Quick run: Create and execute a session in one call
    """
    try:
        agent = get_agent()
        
        session = await agent.create_session(goal, context, max_iterations)
        session = await agent.run_session(session.id)
        
        return {
            "session_id": session.id,
            "status": session.status.value,
            "iterations": session.iterations,
            "result": session.final_result,
            "error": session.error,
            "actions": [
                {"type": a.type.value, "status": a.status, "result": a.result[:200] if a.result else None}
                for a in (session.plan.actions if session.plan else [])
            ]
        }
        
    except Exception as e:
        logger.error(f"Quick run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
