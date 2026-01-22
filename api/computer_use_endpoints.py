"""
🖥️🤖 Computer Use API Endpoints
================================

AI kontrollü masaüstü otomasyon API'si.
%100 LOCAL çalışır - hiçbir veri dışarı gönderilmez.

⚠️ GÜVENLİK: Her işlemde kullanıcı onayı istenir!

Endpoints:
- POST /api/computer/task - Yeni görev oluştur
- GET /api/computer/task/{id} - Görev detayı
- POST /api/computer/task/{id}/execute - Görevi çalıştır
- POST /api/computer/task/{id}/cancel - Görevi iptal et
- GET /api/computer/approvals - Bekleyen onaylar
- POST /api/computer/approve/{id} - Onayla
- POST /api/computer/reject/{id} - Reddet
- GET /api/computer/status - Agent durumu
- WebSocket /api/computer/ws/execute - Gerçek zamanlı çalıştırma

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.logger import get_logger
from core.computer_use_agent import (
    ComputerUseAgent,
    ComputerUseConfig,
    AgentMode,
    ActionType,
    RiskLevel,
    ApprovalStatus,
    Action,
    ActionPlan,
    ApprovalRequest,
    get_computer_use_agent,
)

logger = get_logger("computer_use_api")

router = APIRouter(prefix="/api/computer", tags=["Computer Use Agent"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class TaskRequest(BaseModel):
    """Görev oluşturma isteği."""
    task: str = Field(..., description="Görev açıklaması (ör: 'Notepad aç ve Merhaba yaz')")
    mode: Optional[str] = Field(default="confirm_all", description="Mod: preview, confirm_all, confirm_risky")


class ActionResponse(BaseModel):
    """İşlem yanıtı."""
    id: str
    action_type: str
    description: str
    risk_level: str
    approval_status: str
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    keys: Optional[List[str]] = None


class PlanResponse(BaseModel):
    """Plan yanıtı."""
    id: str
    task: str
    actions: List[ActionResponse]
    current_step: int
    total_steps: int
    success: bool
    cancelled: bool
    error: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Onay yanıtı."""
    id: str
    action: ActionResponse
    plan_id: str
    status: str
    created_at: str
    expires_at: str
    is_expired: bool
    has_screenshot: bool


class StatusResponse(BaseModel):
    """Durum yanıtı."""
    mode: str
    running: bool
    active_plan: Optional[str]
    emergency_stop: bool
    pending_approvals: int
    total_plans: int
    mouse_position: List[int]
    screen_size: List[int]
    dependencies: Dict[str, bool]


class ApproveRejectRequest(BaseModel):
    """Onay/Ret isteği."""
    reason: Optional[str] = Field(default=None, description="Onay/ret nedeni")


class QuickActionRequest(BaseModel):
    """Hızlı işlem isteği."""
    action_type: str = Field(..., description="click, type, hotkey, scroll")
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    keys: Optional[List[str]] = None
    amount: Optional[int] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _action_to_response(action: Action) -> ActionResponse:
    """Action'ı response'a dönüştür."""
    return ActionResponse(
        id=action.id,
        action_type=action.action_type.value,
        description=action.description,
        risk_level=action.risk_level.value,
        approval_status=action.approval_status.value,
        x=action.x,
        y=action.y,
        text=action.text[:50] + "..." if action.text and len(action.text) > 50 else action.text,
        keys=action.keys,
    )


def _plan_to_response(plan: ActionPlan) -> PlanResponse:
    """Plan'ı response'a dönüştür."""
    return PlanResponse(
        id=plan.id,
        task=plan.task,
        actions=[_action_to_response(a) for a in plan.actions],
        current_step=plan.current_step,
        total_steps=plan.total_steps,
        success=plan.success,
        cancelled=plan.cancelled,
        error=plan.error,
    )


def _approval_to_response(req: ApprovalRequest) -> ApprovalResponse:
    """ApprovalRequest'i response'a dönüştür."""
    return ApprovalResponse(
        id=req.id,
        action=_action_to_response(req.action) if req.action else None,
        plan_id=req.plan_id,
        status=req.status.value,
        created_at=req.created_at.isoformat(),
        expires_at=req.expires_at.isoformat(),
        is_expired=req.is_expired(),
        has_screenshot=req.screenshot_base64 is not None,
    )


def _get_agent_mode(mode_str: str) -> AgentMode:
    """String'den AgentMode'a dönüştür."""
    mode_map = {
        "preview": AgentMode.PREVIEW,
        "confirm_all": AgentMode.CONFIRM_ALL,
        "confirm_risky": AgentMode.CONFIRM_RISKY,
        "autonomous": AgentMode.AUTONOMOUS,
    }
    return mode_map.get(mode_str.lower(), AgentMode.CONFIRM_ALL)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status", response_model=StatusResponse, summary="Agent durumu")
async def get_status():
    """
    Computer Use Agent'ın durumunu al.
    
    Döner:
    - Çalışma modu
    - Aktif plan
    - Bekleyen onaylar
    - Mouse/ekran bilgisi
    """
    agent = get_computer_use_agent()
    status = agent.get_status()
    
    return StatusResponse(
        mode=status["mode"],
        running=status["running"],
        active_plan=status["active_plan"],
        emergency_stop=status["emergency_stop"],
        pending_approvals=status["pending_approvals"],
        total_plans=status["total_plans"],
        mouse_position=list(status["mouse_position"]),
        screen_size=list(status["screen_size"]),
        dependencies=status["dependencies"],
    )


@router.get("/health", summary="Sağlık kontrolü")
async def health_check():
    """Agent sağlık durumu."""
    agent = get_computer_use_agent()
    status = agent.get_status()
    
    healthy = (
        status["dependencies"]["pyautogui"] and
        not status["emergency_stop"]
    )
    
    return {
        "status": "healthy" if healthy else "degraded",
        "pyautogui_available": status["dependencies"]["pyautogui"],
        "emergency_stop": status["emergency_stop"],
        "mode": status["mode"],
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/task", summary="Görev oluştur")
async def create_task(request: TaskRequest):
    """
    Yeni görev oluştur.
    
    Örnek görevler:
    - "Notepad'i aç"
    - "Chrome'da yeni sekme aç"
    - "Masaüstündeki dosyayı aç"
    
    ⚠️ Görev oluşturulduktan sonra /execute ile çalıştırılmalı.
    """
    if not request.task.strip():
        raise HTTPException(status_code=400, detail="Görev boş olamaz")
    
    agent = get_computer_use_agent()
    
    # Update mode if specified
    agent.config.mode = _get_agent_mode(request.mode)
    
    # Create plan
    plan = await agent.create_task(request.task)
    
    if plan.error:
        raise HTTPException(status_code=500, detail=plan.error)
    
    return {
        "success": True,
        "plan": _plan_to_response(plan).dict(),
        "message": f"✅ Plan oluşturuldu: {len(plan.actions)} adım",
        "next_step": f"POST /api/computer/task/{plan.id}/execute ile çalıştırın",
    }


@router.get("/task/{plan_id}", summary="Görev detayı")
async def get_task(plan_id: str):
    """Görev detaylarını al."""
    agent = get_computer_use_agent()
    plan = agent.get_plan(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    
    return {
        "plan": _plan_to_response(plan).dict(),
        "before_screenshot": plan.before_screenshot is not None,
        "after_screenshot": plan.after_screenshot is not None,
    }


@router.get("/task/{plan_id}/screenshot/{which}", summary="Plan screenshot")
async def get_task_screenshot(plan_id: str, which: str = "before"):
    """Plan öncesi/sonrası screenshot."""
    agent = get_computer_use_agent()
    plan = agent.get_plan(plan_id)
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    
    screenshot = plan.before_screenshot if which == "before" else plan.after_screenshot
    
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot bulunamadı")
    
    return {
        "plan_id": plan_id,
        "type": which,
        "image_base64": screenshot,
    }


@router.post("/task/{plan_id}/cancel", summary="Görevi iptal et")
async def cancel_task(plan_id: str):
    """Çalışan görevi iptal et."""
    agent = get_computer_use_agent()
    
    success = await agent.cancel_plan(plan_id)
    
    if success:
        return {"success": True, "message": "Görev iptal edildi"}
    
    raise HTTPException(status_code=404, detail="Plan bulunamadı veya zaten tamamlandı")


@router.get("/tasks", summary="Görevleri listele")
async def list_tasks(limit: int = Query(default=10, le=50)):
    """Tüm görevleri listele."""
    agent = get_computer_use_agent()
    plans = agent.list_plans(limit)
    
    return {
        "plans": plans,
        "total": len(plans),
    }


@router.get("/approvals", summary="Bekleyen onaylar")
async def get_pending_approvals():
    """
    Bekleyen onay isteklerini listele.
    
    Her işlem için onay gerekir (confirm_all modunda).
    """
    agent = get_computer_use_agent()
    pending = agent.approvals.get_pending_approvals()
    
    return {
        "pending": [_approval_to_response(r).dict() for r in pending],
        "count": len(pending),
    }


@router.get("/approval/{request_id}", summary="Onay detayı")
async def get_approval(request_id: str):
    """Onay isteği detayı."""
    agent = get_computer_use_agent()
    req = agent.approvals.get_approval(request_id)
    
    if not req:
        raise HTTPException(status_code=404, detail="Onay isteği bulunamadı")
    
    response = _approval_to_response(req).dict()
    
    # Include screenshot if available
    if req.screenshot_base64:
        response["screenshot_base64"] = req.screenshot_base64
    
    return response


@router.post("/approve/{request_id}", summary="Onayla")
async def approve_action(request_id: str, request: ApproveRejectRequest = None):
    """
    İşlemi onayla.
    
    ✅ Onaylanan işlem hemen çalıştırılır.
    """
    agent = get_computer_use_agent()
    
    reason = request.reason if request else None
    success = await agent.approvals.approve(request_id, reason)
    
    if success:
        return {
            "success": True,
            "message": "✅ İşlem onaylandı ve çalıştırılacak",
        }
    
    raise HTTPException(status_code=404, detail="Onay isteği bulunamadı veya süresi doldu")


@router.post("/reject/{request_id}", summary="Reddet")
async def reject_action(request_id: str, request: ApproveRejectRequest = None):
    """
    İşlemi reddet.
    
    ❌ Reddedilen işlem atlanır.
    """
    agent = get_computer_use_agent()
    
    reason = request.reason if request else None
    success = await agent.approvals.reject(request_id, reason)
    
    if success:
        return {
            "success": True,
            "message": "❌ İşlem reddedildi",
        }
    
    raise HTTPException(status_code=404, detail="Onay isteği bulunamadı")


@router.post("/emergency-stop", summary="Acil durdur")
async def emergency_stop():
    """
    🛑 TÜM işlemleri acil durdur.
    
    Aktif plan iptal edilir.
    """
    agent = get_computer_use_agent()
    agent.safety._emergency_stop = True
    
    return {
        "success": True,
        "message": "🛑 EMERGENCY STOP! Tüm işlemler durduruldu.",
    }


@router.post("/reset-emergency", summary="Emergency reset")
async def reset_emergency():
    """Emergency stop'u sıfırla."""
    agent = get_computer_use_agent()
    agent.reset_emergency_stop()
    
    return {
        "success": True,
        "message": "✅ Emergency stop sıfırlandı",
    }


@router.get("/history", summary="İşlem geçmişi")
async def get_history(limit: int = Query(default=50, le=100)):
    """Çalıştırılan işlemlerin geçmişi."""
    agent = get_computer_use_agent()
    history = agent.get_action_history(limit)
    
    return {
        "history": history,
        "count": len(history),
    }


@router.post("/mode", summary="Mod değiştir")
async def set_mode(mode: str):
    """
    Agent modunu değiştir.
    
    Modlar:
    - preview: Sadece göster, çalıştırma
    - confirm_all: Her işlemde onay iste (ÖNERİLEN)
    - confirm_risky: Sadece riskli işlemlerde onay
    - autonomous: Onaysız çalış (TEHLİKELİ!)
    """
    agent = get_computer_use_agent()
    
    new_mode = _get_agent_mode(mode)
    agent.config.mode = new_mode
    
    warning = ""
    if new_mode == AgentMode.AUTONOMOUS:
        warning = "⚠️ UYARI: Autonomous mod tehlikelidir! İşlemler onaysız çalışır."
    
    return {
        "success": True,
        "mode": new_mode.value,
        "warning": warning,
    }


# =============================================================================
# WEBSOCKET ENDPOINTS
# =============================================================================

@router.websocket("/ws/execute/{plan_id}")
async def websocket_execute(websocket: WebSocket, plan_id: str):
    """
    WebSocket ile plan çalıştırma.
    
    Gerçek zamanlı olarak:
    - Adım durumları
    - Onay istekleri
    - Tamamlanma bildirimleri
    
    gönderir.
    
    Client -> Server:
    - {"type": "approve", "request_id": "..."} - Onayla
    - {"type": "reject", "request_id": "..."} - Reddet
    - {"type": "cancel"} - İptal et
    
    Server -> Client:
    - {"type": "started", ...}
    - {"type": "approval_needed", ...}
    - {"type": "step_completed", ...}
    - {"type": "completed", ...}
    """
    await websocket.accept()
    
    agent = get_computer_use_agent()
    plan = agent.get_plan(plan_id)
    
    if not plan:
        await websocket.send_json({
            "type": "error",
            "message": "Plan bulunamadı"
        })
        await websocket.close()
        return
    
    logger.info(f"WebSocket execute started for plan: {plan_id}")
    
    # Task for receiving client messages
    async def receive_client_messages():
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type", "")
                
                if msg_type == "approve":
                    request_id = data.get("request_id")
                    if request_id:
                        await agent.approvals.approve(request_id)
                        await websocket.send_json({
                            "type": "approval_received",
                            "request_id": request_id,
                            "status": "approved"
                        })
                
                elif msg_type == "reject":
                    request_id = data.get("request_id")
                    if request_id:
                        await agent.approvals.reject(request_id)
                        await websocket.send_json({
                            "type": "approval_received",
                            "request_id": request_id,
                            "status": "rejected"
                        })
                
                elif msg_type == "cancel":
                    await agent.cancel_plan(plan_id)
                    await websocket.send_json({
                        "type": "cancelled",
                        "message": "Plan iptal edildi"
                    })
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"Client message error: {e}")
    
    # Start client message receiver
    receive_task = asyncio.create_task(receive_client_messages())
    
    try:
        # Execute plan and stream status
        async for status in agent.execute_plan(plan_id):
            await websocket.send_json(status)
            
            # If approval needed, wait a bit for client response
            if status.get("type") == "approval_needed":
                await asyncio.sleep(0.1)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for plan: {plan_id}")
        await agent.cancel_plan(plan_id)
    except Exception as e:
        logger.error(f"WebSocket execute error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        receive_task.cancel()
        try:
            await websocket.close()
        except Exception:
            pass


@router.websocket("/ws/interactive")
async def websocket_interactive(websocket: WebSocket):
    """
    Etkileşimli Computer Use oturumu.
    
    Kullanıcı doğal dilde komut verir, AI planlar ve onay ister.
    
    Client -> Server:
    - {"type": "task", "text": "Notepad aç"} - Yeni görev
    - {"type": "approve", "request_id": "..."} - Onayla
    - {"type": "reject", "request_id": "..."} - Reddet
    - {"type": "stop"} - Durdur
    
    Server -> Client:
    - {"type": "thinking", ...}
    - {"type": "plan_created", ...}
    - {"type": "approval_needed", ...}
    - {"type": "step_completed", ...}
    """
    await websocket.accept()
    
    agent = get_computer_use_agent()
    current_plan_id = None
    
    logger.info("Interactive Computer Use session started")
    
    # Welcome message
    await websocket.send_json({
        "type": "welcome",
        "message": "🤖 Computer Use Agent hazır! Bir görev yazın.",
        "mode": agent.config.mode.value,
        "examples": [
            "Notepad'i aç",
            "Chrome'da yeni sekme aç",
            "Ekranın ortasına tıkla",
        ],
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            
            if msg_type == "task":
                task_text = data.get("text", "")
                
                if not task_text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Görev metni boş"
                    })
                    continue
                
                # Thinking indicator
                await websocket.send_json({
                    "type": "thinking",
                    "message": "🤔 Planlanıyor..."
                })
                
                # Create plan
                plan = await agent.create_task(task_text)
                current_plan_id = plan.id
                
                if plan.error:
                    await websocket.send_json({
                        "type": "error",
                        "message": plan.error
                    })
                    continue
                
                await websocket.send_json({
                    "type": "plan_created",
                    "plan": _plan_to_response(plan).dict(),
                    "message": f"📋 Plan hazır: {len(plan.actions)} adım"
                })
                
                # Execute plan
                async for status in agent.execute_plan(plan.id):
                    await websocket.send_json(status)
                    
                    if status.get("type") == "approval_needed":
                        await asyncio.sleep(0.1)
            
            elif msg_type == "approve":
                request_id = data.get("request_id")
                if request_id:
                    await agent.approvals.approve(request_id)
            
            elif msg_type == "reject":
                request_id = data.get("request_id")
                if request_id:
                    await agent.approvals.reject(request_id)
            
            elif msg_type == "stop":
                if current_plan_id:
                    await agent.cancel_plan(current_plan_id)
                    await websocket.send_json({
                        "type": "stopped",
                        "message": "🛑 Durduruldu"
                    })
            
            elif msg_type == "status":
                status = agent.get_status()
                await websocket.send_json({
                    "type": "status",
                    "data": status
                })
                
    except WebSocketDisconnect:
        logger.info("Interactive session disconnected")
        if current_plan_id:
            await agent.cancel_plan(current_plan_id)
    except Exception as e:
        logger.error(f"Interactive session error: {e}")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ["router"]
