"""
🎓 Learning Journey V2 API Endpoints
Gelişmiş Öğrenme Yolculuğu API'leri

Endpoints:
- POST /api/journey/v2/create - Yeni yolculuk oluştur (WebSocket destekli)
- GET /api/journey/v2/{journey_id}/map - Stage haritası
- GET /api/journey/v2/{journey_id}/progress - İlerleme durumu
- POST /api/journey/v2/{journey_id}/packages/{package_id}/start - Paket başlat
- POST /api/journey/v2/{journey_id}/packages/{package_id}/complete - Paket tamamla
- POST /api/journey/v2/{journey_id}/exams/{exam_id}/submit - Sınav gönder
- POST /api/journey/v2/{journey_id}/complete - Yolculuğu tamamla
- GET /api/certificates/verify/{code} - Sertifika doğrula
- WS /ws/journey/v2/{journey_id} - Real-time updates
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.learning_journey_v2 import (
    LearningGoal, CurriculumPlan, Stage, Package, UserProgress,
    ContentType, ExamType, ExerciseType, DifficultyLevel,
    get_learning_orchestrator, get_exam_system, get_certificate_generator,
    get_certificate_analytics, OrchestrationEvent, EventType
)


# ==================== ROUTER ====================

router = APIRouter(prefix="/journey/v2", tags=["Learning Journey V2"])


# ==================== PYDANTIC MODELS ====================

class LearningGoalCreate(BaseModel):
    """Öğrenme hedefi oluşturma"""
    title: str = Field(..., description="Hedef başlığı", example="AYT Matematik Çalışma Planı")
    subject: str = Field(..., description="Konu alanı", example="Matematik")
    target_outcome: str = Field(..., description="Hedef sonuç", example="AYT'de 35+ net yapmak")
    motivation: str = Field(default="", description="Motivasyon")
    
    prior_knowledge: Optional[str] = Field(default=None, description="Ön bilgi seviyesi")
    weak_areas: List[str] = Field(default_factory=list, description="Zayıf alanlar")
    focus_areas: List[str] = Field(default_factory=list, description="Odaklanılacak alanlar")
    
    daily_hours: float = Field(default=2.0, ge=0.5, le=8.0, description="Günlük çalışma saati")
    deadline: Optional[str] = Field(default=None, description="Hedef tarih (ISO format)")
    
    content_preferences: List[str] = Field(
        default=["text", "video"],
        description="İçerik tercihleri: text, video, interactive, audio"
    )
    exam_preferences: List[str] = Field(
        default=["multiple_choice", "feynman"],
        description="Sınav tercihleri"
    )
    
    topics_to_include: Optional[List[str]] = Field(default=None, description="Dahil edilecek konular")
    topics_to_exclude: Optional[List[str]] = Field(default=None, description="Hariç tutulacak konular")


class ExamSubmission(BaseModel):
    """Sınav gönderimi"""
    exam_type: str = Field(..., description="Sınav türü")
    
    # Multiple choice
    answers: Optional[Dict[str, str]] = Field(default=None, description="Çoktan seçmeli cevaplar")
    
    # Feynman / Teach-back
    explanation: Optional[str] = Field(default=None, description="Açıklama metni")
    audio_transcript: Optional[str] = Field(default=None, description="Ses transkripsiyonu")
    
    # Problem solving
    solutions: Optional[Dict[str, str]] = Field(default=None, description="Problem çözümleri")
    
    # Concept map
    concept_map: Optional[Dict[str, Any]] = Field(default=None, description="Kavram haritası")
    
    # Q&A history for teach-back
    qa_history: Optional[List[Dict[str, str]]] = Field(default=None)
    
    time_taken_seconds: int = Field(default=0, ge=0)


class JourneyCompleteRequest(BaseModel):
    """Yolculuk tamamlama isteği"""
    user_name: str = Field(..., description="Kullanıcı adı (sertifika için)")


# ==================== ENDPOINTS ====================

@router.post("/create", response_model=Dict[str, Any])
async def create_journey(goal_data: LearningGoalCreate, user_id: str = "default_user"):
    """
    Yeni öğrenme yolculuğu oluştur
    
    Bu endpoint senkron olarak plan oluşturur.
    Real-time AI thinking için WebSocket endpoint'i kullanın.
    """
    try:
        # LearningGoal oluştur
        content_prefs = []
        for pref in goal_data.content_preferences:
            try:
                content_prefs.append(ContentType(pref))
            except:
                pass
        
        exam_prefs = []
        for pref in goal_data.exam_preferences:
            try:
                exam_prefs.append(ExamType(pref))
            except:
                pass
        
        goal = LearningGoal(
            title=goal_data.title,
            subject=goal_data.subject,
            target_outcome=goal_data.target_outcome,
            motivation=goal_data.motivation,
            prior_knowledge=goal_data.prior_knowledge or "",
            weak_areas=goal_data.weak_areas,
            focus_areas=goal_data.focus_areas,
            daily_hours=goal_data.daily_hours,
            deadline=goal_data.deadline,
            content_preferences=content_prefs,
            exam_preferences=exam_prefs,
            topics_to_include=goal_data.topics_to_include,
            topics_to_exclude=goal_data.topics_to_exclude
        )
        
        # Orchestrator ile plan oluştur
        orchestrator = get_learning_orchestrator()
        
        events = []
        plan = None
        
        async for event in orchestrator.create_journey(goal, user_id):
            events.append(event.to_dict())
            if event.type == EventType.PLANNING_COMPLETED:
                pass
            if event.type == EventType.JOURNEY_STARTED:
                plan = event.data.get("plan")
        
        return {
            "success": True,
            "journey_id": plan.get("id") if plan else None,
            "plan": plan,
            "thinking_steps": [e for e in events if e["type"] == "planning_step"],
            "total_events": len(events)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{journey_id}/map")
async def get_journey_map(journey_id: str):
    """Stage haritasını getir"""
    
    orchestrator = get_learning_orchestrator()
    stage_map = orchestrator.get_stage_map(journey_id)
    
    if not stage_map:
        raise HTTPException(status_code=404, detail="Journey bulunamadı")
    
    return stage_map


@router.get("/{journey_id}/progress")
async def get_journey_progress(journey_id: str):
    """İlerleme durumunu getir"""
    
    orchestrator = get_learning_orchestrator()
    state = orchestrator.get_journey_state(journey_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Journey bulunamadı")
    
    return state


@router.get("/{journey_id}/stages/{stage_id}")
async def get_stage_details(journey_id: str, stage_id: str):
    """Stage detaylarını getir"""
    
    orchestrator = get_learning_orchestrator()
    state = orchestrator.active_journeys.get(journey_id)
    
    if not state or not state.plan:
        raise HTTPException(status_code=404, detail="Journey bulunamadı")
    
    for stage in state.plan.stages:
        if stage.id == stage_id:
            return stage.to_dict()
    
    raise HTTPException(status_code=404, detail="Stage bulunamadı")


@router.get("/{journey_id}/packages/{package_id}")
async def get_package_details(journey_id: str, package_id: str):
    """Paket detaylarını getir"""
    
    orchestrator = get_learning_orchestrator()
    state = orchestrator.active_journeys.get(journey_id)
    
    if not state or not state.plan:
        raise HTTPException(status_code=404, detail="Journey bulunamadı")
    
    for stage in state.plan.stages:
        for package in stage.packages:
            if package.id == package_id:
                return {
                    "package": package.to_dict(),
                    "stage": {
                        "id": stage.id,
                        "title": stage.title
                    }
                }
    
    raise HTTPException(status_code=404, detail="Package bulunamadı")


@router.post("/{journey_id}/packages/{package_id}/start")
async def start_package(journey_id: str, package_id: str, user_id: str = "default_user"):
    """Paketi başlat ve içerik üret"""
    
    orchestrator = get_learning_orchestrator()
    
    events = []
    async for event in orchestrator.start_package(journey_id, package_id, user_id):
        events.append(event.to_dict())
    
    # En son package durumunu getir
    state = orchestrator.active_journeys.get(journey_id)
    if state and state.plan:
        for stage in state.plan.stages:
            for package in stage.packages:
                if package.id == package_id:
                    return {
                        "success": True,
                        "package": package.to_dict(),
                        "events": events
                    }
    
    return {
        "success": True,
        "events": events
    }


@router.post("/{journey_id}/packages/{package_id}/complete")
async def complete_package(journey_id: str, package_id: str, user_id: str = "default_user"):
    """Paketi tamamla"""
    
    orchestrator = get_learning_orchestrator()
    
    events = []
    async for event in orchestrator.complete_package(journey_id, package_id, user_id):
        events.append(event.to_dict())
    
    return {
        "success": True,
        "events": events
    }


@router.post("/{journey_id}/exams/{exam_id}/submit")
async def submit_exam(
    journey_id: str, 
    exam_id: str, 
    submission: ExamSubmission,
    user_id: str = "default_user"
):
    """Sınav gönder ve değerlendir"""
    
    orchestrator = get_learning_orchestrator()
    
    try:
        result = await orchestrator.submit_exam(
            journey_id=journey_id,
            exam_id=exam_id,
            submission=submission.dict(),
            user_id=user_id
        )
        
        return {
            "success": True,
            "result": result.to_dict()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{journey_id}/complete")
async def complete_journey(
    journey_id: str,
    request: JourneyCompleteRequest,
    user_id: str = "default_user"
):
    """Yolculuğu tamamla ve sertifika al"""
    
    orchestrator = get_learning_orchestrator()
    
    events = []
    certificate = None
    
    async for event in orchestrator.complete_journey(journey_id, user_id, request.user_name):
        events.append(event.to_dict())
        if event.type == EventType.CERTIFICATE_GENERATED:
            certificate = event.data
    
    if certificate:
        return {
            "success": True,
            "certificate": certificate,
            "events": events
        }
    else:
        raise HTTPException(status_code=400, detail="Yolculuk tamamlanamadı")


# ==================== CERTIFICATE ENDPOINTS ====================

certificate_router = APIRouter(prefix="/certificates", tags=["Certificates"])


@certificate_router.get("/verify/{verification_code}")
async def verify_certificate(verification_code: str):
    """Sertifika doğrula"""
    
    generator = get_certificate_generator()
    result = generator.verify_certificate(verification_code)
    
    return result


@certificate_router.get("/user/{user_id}/stats")
async def get_user_certificate_stats(user_id: str):
    """Kullanıcının sertifika istatistikleri"""
    
    analytics = get_certificate_analytics()
    stats = analytics.get_user_stats(user_id)
    
    return stats.to_dict()


@certificate_router.get("/leaderboard")
async def get_certificate_leaderboard(subject: Optional[str] = None, limit: int = 10):
    """Sertifika liderlik tablosu"""
    
    analytics = get_certificate_analytics()
    leaderboard = analytics.get_leaderboard(subject, limit)
    
    return {
        "subject": subject or "Tüm Konular",
        "leaderboard": leaderboard
    }


# ==================== WEBSOCKET ENDPOINT ====================

@router.websocket("/ws/{journey_id}")
async def journey_websocket(websocket: WebSocket, journey_id: str):
    """
    Real-time journey updates WebSocket
    
    Message types:
    - create_journey: Yeni yolculuk oluştur
    - start_package: Paket başlat
    - complete_package: Paket tamamla
    - submit_exam: Sınav gönder
    - complete_journey: Yolculuğu tamamla
    - get_map: Stage haritası
    - get_progress: İlerleme durumu
    - update_time: Zaman güncelle
    """
    
    await websocket.accept()
    
    orchestrator = get_learning_orchestrator()
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            payload = data.get("payload", {})
            
            if message_type == "create_journey":
                # Goal oluştur
                goal_data = payload.get("goal", {})
                user_id = payload.get("user_id", "default_user")
                
                content_prefs = [ContentType(p) for p in goal_data.get("content_preferences", ["text"]) if p in ContentType.__members__]
                exam_prefs = [ExamType(p) for p in goal_data.get("exam_preferences", ["multiple_choice"]) if p in ExamType.__members__]
                
                goal = LearningGoal(
                    title=goal_data.get("title", "Öğrenme Hedefi"),
                    subject=goal_data.get("subject", "Genel"),
                    target_outcome=goal_data.get("target_outcome", "Konuyu öğrenmek"),
                    motivation=goal_data.get("motivation", ""),
                    prior_knowledge=goal_data.get("prior_knowledge", ""),
                    weak_areas=goal_data.get("weak_areas", []),
                    focus_areas=goal_data.get("focus_areas", []),
                    daily_hours=goal_data.get("daily_hours", 2.0),
                    deadline=goal_data.get("deadline"),
                    content_preferences=content_prefs,
                    exam_preferences=exam_prefs,
                    topics_to_include=goal_data.get("topics_to_include"),
                    topics_to_exclude=goal_data.get("topics_to_exclude")
                )
                
                # Stream events
                async for event in orchestrator.create_journey(goal, user_id):
                    await websocket.send_json({
                        "type": "event",
                        "event": event.to_dict()
                    })
            
            elif message_type == "start_package":
                package_id = payload.get("package_id")
                user_id = payload.get("user_id", "default_user")
                
                async for event in orchestrator.start_package(journey_id, package_id, user_id):
                    await websocket.send_json({
                        "type": "event",
                        "event": event.to_dict()
                    })
            
            elif message_type == "complete_package":
                package_id = payload.get("package_id")
                user_id = payload.get("user_id", "default_user")
                
                async for event in orchestrator.complete_package(journey_id, package_id, user_id):
                    await websocket.send_json({
                        "type": "event",
                        "event": event.to_dict()
                    })
            
            elif message_type == "submit_exam":
                exam_id = payload.get("exam_id")
                submission = payload.get("submission", {})
                user_id = payload.get("user_id", "default_user")
                
                try:
                    result = await orchestrator.submit_exam(journey_id, exam_id, submission, user_id)
                    await websocket.send_json({
                        "type": "exam_result",
                        "result": result.to_dict()
                    })
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
            
            elif message_type == "complete_journey":
                user_name = payload.get("user_name", "Öğrenci")
                user_id = payload.get("user_id", "default_user")
                
                async for event in orchestrator.complete_journey(journey_id, user_id, user_name):
                    await websocket.send_json({
                        "type": "event",
                        "event": event.to_dict()
                    })
            
            elif message_type == "get_map":
                stage_map = orchestrator.get_stage_map(journey_id)
                await websocket.send_json({
                    "type": "map",
                    "data": stage_map
                })
            
            elif message_type == "get_progress":
                state = orchestrator.get_journey_state(journey_id)
                await websocket.send_json({
                    "type": "progress",
                    "data": state
                })
            
            elif message_type == "update_time":
                seconds = payload.get("seconds", 0)
                orchestrator.update_time_spent(journey_id, seconds)
                await websocket.send_json({
                    "type": "time_updated",
                    "seconds": seconds
                })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Bilinmeyen mesaj tipi: {message_type}"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


# ==================== INCLUDE ROUTERS ====================

def include_journey_v2_routes(app):
    """API'ye journey v2 route'larını ekle"""
    app.include_router(router, prefix="/api")
    app.include_router(certificate_router, prefix="/api")
