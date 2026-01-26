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
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.learning_journey_v2 import (
    LearningGoal, CurriculumPlan, Stage, Package, UserProgress,
    ContentType, ExamType, ExerciseType, DifficultyLevel,
    get_learning_orchestrator, get_exam_system, get_certificate_generator,
    get_certificate_analytics, OrchestrationEvent, EventType
)

# Premium V2 imports
try:
    from core.learning_journey_v2.curriculum_studio.orchestrator import (
        CurriculumStudioOrchestrator,
        create_curriculum_with_studio
    )
    from core.learning_journey_v2.curriculum_studio.agents.base_agent import (
        AgentThought,
        ThinkingPhase
    )
    CURRICULUM_STUDIO_AVAILABLE = True
except ImportError:
    CURRICULUM_STUDIO_AVAILABLE = False

try:
    from core.learning_journey_v2.spaced_repetition import (
        SM2Algorithm,
        MasteryTracker,
        mastery_tracker,
        sm2
    )
    SPACED_REPETITION_AVAILABLE = True
except ImportError:
    SPACED_REPETITION_AVAILABLE = False

try:
    from core.learning_journey_v2.weakness_detection import (
        WeaknessDetector,
        weakness_detector
    )
    WEAKNESS_DETECTION_AVAILABLE = True
except ImportError:
    WEAKNESS_DETECTION_AVAILABLE = False


# ==================== ROUTER ====================

router = APIRouter(prefix="/api/journey/v2", tags=["Learning Journey V2"])


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

@router.get("/list")
async def list_journeys(user_id: str = "default_user"):
    """
    Kullanıcının tüm öğrenme yolculuklarını listele
    """
    try:
        orchestrator = get_learning_orchestrator()
        journeys = orchestrator.list_journeys(user_id)
        return {"journeys": journeys}
    except Exception as e:
        return {"journeys": [], "error": str(e)}


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
        journey_id = None
        
        async for event in orchestrator.create_journey(goal, user_id):
            events.append(event.to_dict())
            if event.type == EventType.PLANNING_COMPLETED:
                pass
            if event.type == EventType.JOURNEY_STARTED:
                plan = event.data.get("plan")
                journey_id = plan.get("id") if plan else None
        
        # Frontend uyumlu curriculum formatı oluştur
        curriculum = None
        if plan:
            curriculum = {
                "journey_id": plan.get("id"),
                "title": plan.get("title"),
                "subject": plan.get("subject"),
                "target_outcome": plan.get("target_outcome"),
                "total_stages": plan.get("total_stages", len(plan.get("stages", []))),
                "total_packages": plan.get("total_packages", 0),
                "total_exams": plan.get("total_exams", 0),
                "total_exercises": plan.get("total_exercises", 0),
                "estimated_total_hours": plan.get("estimated_total_hours", 0),  # Doğrudan plan'dan al
                "total_xp_possible": plan.get("total_xp_possible", 0),
                "created_at": plan.get("created_at")
            }
        
        # Backend thinking_steps'i frontend formatına dönüştür
        frontend_thinking_steps = []
        step_mapping = {
            "Goal Analyzer": "goal_analysis",
            "Curriculum Selector": "curriculum_selection",
            "Topic Mapper": "topic_mapping",
            "Stage Planner": "stage_planning",
            "Package Creator": "package_design",
            "Exam Strategist": "exam_generation",
            "Timeline Optimizer": "exercise_creation",
            "Plan Finalizer": "content_structuring"
        }
        
        for event in events:
            if event["type"] == "planning_step":
                agent_name = event.get("agent_name", "")
                step_id = step_mapping.get(agent_name, "goal_analysis")
                frontend_thinking_steps.append({
                    "step": step_id,
                    "status": "completed",
                    "message": event.get("data", {}).get("action", "İşlem tamamlandı"),
                    "details": {
                        "agent": agent_name,
                        "reasoning": event.get("data", {}).get("reasoning", ""),
                        "output": event.get("data", {}).get("output", {})
                    }
                })
        
        # UTF-8 encoding ile JSONResponse döndür
        response_data = {
            "success": True,
            "journey_id": journey_id,
            "curriculum": curriculum,
            "plan": plan,
            "thinking_steps": frontend_thinking_steps,
            "total_events": len(events)
        }
        return JSONResponse(
            content=response_data,
            media_type="application/json; charset=utf-8"
        )
    
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
    """Paketi başlat ve içerik üret - LLM ile zenginleştirilmiş"""
    
    orchestrator = get_learning_orchestrator()
    
    # Önce journey ve package'ın var olduğunu kontrol et
    state = orchestrator.active_journeys.get(journey_id)
    if not state or not state.plan:
        raise HTTPException(status_code=404, detail="Journey bulunamadı")
    
    target_package = None
    target_stage = None
    for stage in state.plan.stages:
        for package in stage.packages:
            if package.id == package_id:
                target_package = package
                target_stage = stage
                break
        if target_package:
            break
    
    if not target_package:
        raise HTTPException(status_code=404, detail="Package bulunamadı")
    
    # LLM ile içerik zenginleştir (eğer henüz yapılmamışsa)
    if not getattr(target_package, 'llm_content_ready', False):
        try:
            planner = orchestrator.curriculum_planner
            if hasattr(planner, 'enhance_package_content_with_llm'):
                goal = state.plan.goal
                await planner.enhance_package_content_with_llm(target_package, target_stage, goal)
        except Exception as e:
            print(f"[API] LLM enhancement skipped: {e}")
    
    events = []
    async for event in orchestrator.start_package(journey_id, package_id, user_id):
        events.append(event.to_dict())
    
    # En son package durumunu getir
    return {
        "success": True,
        "package": target_package.to_dict(),
        "llm_enhanced": getattr(target_package, 'llm_content_ready', False),
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
        
        # Frontend uyumlu format - criteria_scores'dan feedback oluştur
        feedback = {
            "accuracy": 0,
            "depth": 0,
            "clarity": 0,
            "examples": 0,
            "completeness": 0,
            "overall_feedback": result.detailed_feedback
        }
        
        # Criteria scores'u feedback'e map et
        criteria_mapping = {
            "accuracy": "accuracy",
            "depth": "depth", 
            "clarity": "clarity",
            "examples": "examples",
            "completeness": "completeness",
            "doğruluk": "accuracy",
            "derinlik": "depth",
            "açıklık": "clarity",
            "örnekler": "examples",
            "bütünlük": "completeness"
        }
        
        for cs in result.criteria_scores:
            key = cs.criteria_name.lower()
            if key in criteria_mapping:
                feedback_key = criteria_mapping[key]
                feedback[feedback_key] = int((cs.score / cs.max_score) * 100) if cs.max_score > 0 else 0
        
        return {
            "success": True,
            "score": int(result.percentage),
            "passed": result.passed,
            "feedback": feedback,
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
    app.include_router(premium_v2_router, prefix="/api")


# ==================== PREMIUM V2 ROUTER ====================

premium_v2_router = APIRouter(prefix="/api/journey/v2/premium", tags=["Learning Journey V2 Premium"])


class RecordAttemptRequest(BaseModel):
    """Deneme kaydı isteği"""
    topic_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    duration_minutes: int = Field(default=5, ge=1)
    question_results: List[Dict[str, Any]] = Field(default=[])


class ReviewCardRequest(BaseModel):
    """Kart değerlendirme isteği (SM-2)"""
    quality: int = Field(..., ge=0, le=5)


class CurriculumStudioRequest(BaseModel):
    """Multi-Agent Curriculum Studio isteği"""
    topic: str = Field(..., min_length=1, max_length=500)
    target_level: str = Field(default="intermediate")
    daily_hours: float = Field(default=2.0, ge=0.5, le=8.0)
    duration_weeks: int = Field(default=4, ge=1, le=52)
    learning_style: str = Field(default="multimodal")
    custom_instructions: str = Field(default="", max_length=2000)


@premium_v2_router.get("/status")
async def get_premium_v2_status():
    """Premium V2 modüllerinin durumunu getir"""
    return {
        "version": "2.0.0-premium",
        "modules": {
            "curriculum_studio": {
                "available": CURRICULUM_STUDIO_AVAILABLE,
                "description": "Multi-Agent Curriculum Generation (5 uzman agent)"
            },
            "spaced_repetition": {
                "available": SPACED_REPETITION_AVAILABLE,
                "description": "SM-2 Algorithm + Mastery Tracking"
            },
            "weakness_detection": {
                "available": WEAKNESS_DETECTION_AVAILABLE,
                "description": "Automatic Weakness Detection & Adaptive Content"
            }
        },
        "features": [
            "30-120 saniye derin düşünme",
            "Görünür agent reasoning",
            "SM-2 aralıklı tekrar",
            "Otomatik zayıflık tespiti",
            "Dinamik stage closure",
            "Skor bazlı unlocking",
            "XP ve seviye sistemi"
        ]
    }


@premium_v2_router.post("/curriculum/generate")
async def generate_curriculum_with_studio(request: CurriculumStudioRequest):
    """
    🎭 Multi-Agent Curriculum Studio ile streaming müfredat oluşturma
    
    5 uzman agent sırayla çalışır:
    1. 📚 Pedagogy Agent - Bloom taksonomisi, öğrenme stilleri
    2. 🔍 Research Agent - RAG araştırması
    3. 🎨 Content Agent - Multimedya planlama
    4. 📋 Exam Agent - Sınav stratejisi, aralıklı tekrar
    5. 🔬 Review Agent - Kalite kontrol
    """
    from fastapi.responses import StreamingResponse
    
    if not CURRICULUM_STUDIO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Curriculum Studio modülü yüklenmedi")
    
    class Goal:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    goal = Goal(
        topic=request.topic,
        target_level=request.target_level,
        daily_hours=request.daily_hours,
        duration_weeks=request.duration_weeks,
        learning_style=request.learning_style,
        custom_instructions=request.custom_instructions
    )
    
    async def generate():
        try:
            llm_service = None
            try:
                from core.llm_manager import llm_manager
                llm_service = llm_manager
            except:
                pass
            
            async for event in create_curriculum_with_studio(goal=goal, llm_service=llm_service):
                if event["type"] == "thought":
                    thought = event["thought"]
                    thought_data = {
                        "type": "thought",
                        "agent": thought.agent_name,
                        "icon": thought.agent_icon,
                        "step": thought.step,
                        "phase": thought.phase.value if hasattr(thought.phase, "value") else str(thought.phase),
                        "thinking": thought.thinking,
                        "reasoning": thought.reasoning,
                        "evidence": thought.evidence,
                        "conclusion": thought.conclusion,
                        "confidence": thought.confidence,
                        "is_complete": thought.is_complete,
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(thought_data, ensure_ascii=False)}\n\n"
                elif event["type"] == "result":
                    result_data = {"type": "result", **event["result"]}
                    yield f"data: {json.dumps(result_data, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )


@premium_v2_router.get("/mastery/summary")
async def get_mastery_summary():
    """Genel hakimiyet özeti"""
    if not SPACED_REPETITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Spaced Repetition modülü yüklenmedi")
    
    return {"success": True, "summary": mastery_tracker.get_progress_summary()}


@premium_v2_router.get("/mastery/topics/{topic_id}")
async def get_topic_mastery(topic_id: str):
    """Konu hakimiyet detayı"""
    if not SPACED_REPETITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Spaced Repetition modülü yüklenmedi")
    
    topic = mastery_tracker.topic_masteries.get(topic_id)
    if not topic:
        return {"success": True, "topic_id": topic_id, "mastery": None}
    
    review_items = [mastery_tracker.review_items[rid] for rid in topic.review_items if rid in mastery_tracker.review_items]
    retention = sum(sm2.calculate_retention_rate(item) for item in review_items) / len(review_items) if review_items else 0.0
    
    return {
        "success": True,
        "topic_id": topic_id,
        "mastery": {
            "score": topic.mastery_score,
            "level": topic.mastery_level.value,
            "confidence": topic.confidence,
            "total_attempts": topic.total_attempts,
            "correct_attempts": topic.correct_attempts,
            "average_score": topic.average_score,
            "xp_earned": topic.xp_earned,
            "retention_rate": retention
        }
    }


@premium_v2_router.post("/mastery/record-attempt")
async def record_topic_attempt(request: RecordAttemptRequest):
    """Konu denemesi kaydet ve mastery güncelle"""
    if not SPACED_REPETITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Spaced Repetition modülü yüklenmedi")
    
    topic, xp = mastery_tracker.record_topic_attempt(
        topic_id=request.topic_id,
        score=request.score,
        duration_minutes=request.duration_minutes,
        question_results=request.question_results
    )
    
    # Weakness detection
    weakness_signals = []
    if WEAKNESS_DETECTION_AVAILABLE:
        signals = weakness_detector.analyze_attempt(
            topic_id=request.topic_id,
            score=request.score,
            question_results=request.question_results
        )
        weakness_signals = [{"type": s.weakness_type.value, "severity": s.severity} for s in signals]
    
    return {
        "success": True,
        "mastery": {"score": topic.mastery_score, "level": topic.mastery_level.value, "xp_earned": xp},
        "user": {"total_xp": mastery_tracker.total_xp, "level": mastery_tracker.current_level},
        "weakness_signals": weakness_signals
    }


@premium_v2_router.get("/reviews/due")
async def get_due_reviews(max_items: int = 20):
    """Bugün tekrar edilecek öğeleri getir (SM-2)"""
    if not SPACED_REPETITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Spaced Repetition modülü yüklenmedi")
    
    due_items = mastery_tracker.get_due_reviews(max_items=max_items)
    
    return {
        "success": True,
        "due_count": len(due_items),
        "items": [
            {"id": item.item_id, "topic_id": item.topic_id, "type": item.item_type,
             "retention": sm2.calculate_retention_rate(item), "interval": item.interval}
            for item in due_items
        ]
    }


@premium_v2_router.post("/reviews/{item_id}/complete")
async def complete_review(item_id: str, request: ReviewCardRequest):
    """Tekrar tamamla (SM-2 quality: 0-5)"""
    if not SPACED_REPETITION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Spaced Repetition modülü yüklenmedi")
    
    if item_id not in mastery_tracker.review_items:
        raise HTTPException(status_code=404, detail="Öğe bulunamadı")
    
    item = mastery_tracker.review_items[item_id]
    updated = sm2.calculate_next_review(item, request.quality)
    level_name, level_score = sm2.get_mastery_level(updated)
    
    return {
        "success": True,
        "item": {
            "id": updated.item_id,
            "new_interval": updated.interval,
            "new_ease_factor": updated.ease_factor,
            "next_review": updated.next_review.isoformat() if updated.next_review else None,
            "mastery_level": level_name,
            "mastery_score": level_score
        }
    }


@premium_v2_router.get("/weakness/summary")
async def get_weakness_summary():
    """Zayıflık özeti"""
    if not WEAKNESS_DETECTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Weakness Detection modülü yüklenmedi")
    
    return {"success": True, "summary": weakness_detector.get_weakness_summary()}


@premium_v2_router.get("/weakness/topics/{topic_id}/content")
async def get_adaptive_content(topic_id: str, max_recommendations: int = 5):
    """Konu için adaptif içerik önerileri"""
    if not WEAKNESS_DETECTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Weakness Detection modülü yüklenmedi")
    
    content = weakness_detector.recommend_adaptive_content(topic_id=topic_id, max_recommendations=max_recommendations)
    
    return {
        "success": True,
        "topic_id": topic_id,
        "recommendations": [
            {"id": c.content_id, "type": c.content_type, "title": c.title,
             "description": c.description, "minutes": c.estimated_minutes, "priority": c.priority}
            for c in content
        ]
    }


@premium_v2_router.get("/weakness/stages/{stage_id}/closure-adjustments")
async def get_stage_closure_adjustments(stage_id: str):
    """Aşama kapanış sınavı için zayıflık bazlı ek sorular (%40 extra)"""
    if not WEAKNESS_DETECTION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Weakness Detection modülü yüklenmedi")
    
    base_questions = [{"id": f"q{i}"} for i in range(10)]
    adjustments = weakness_detector.get_stage_closure_adjustments(stage_id=stage_id, base_questions=base_questions)
    
    return {
        "success": True,
        "stage_id": stage_id,
        "base_question_count": len(base_questions),
        "extra_questions": adjustments,
        "total_questions": len(base_questions) + len(adjustments)
    }


@premium_v2_router.post("/track-progress")
async def track_learning_progress(request: RecordAttemptRequest):
    """
    Tek endpoint ile tam ilerleme takibi:
    1. Mastery kaydı + XP
    2. Zayıflık analizi
    3. SM-2 review scheduling
    """
    result = {"success": True, "topic_id": request.topic_id, "score": request.score}
    
    if SPACED_REPETITION_AVAILABLE:
        topic, xp = mastery_tracker.record_topic_attempt(
            topic_id=request.topic_id, score=request.score,
            duration_minutes=request.duration_minutes, question_results=request.question_results
        )
        result["mastery"] = {"score": topic.mastery_score, "level": topic.mastery_level.value, "xp_earned": xp,
                            "total_xp": mastery_tracker.total_xp, "user_level": mastery_tracker.current_level}
    
    if WEAKNESS_DETECTION_AVAILABLE:
        signals = weakness_detector.analyze_attempt(topic_id=request.topic_id, score=request.score,
                                                   question_results=request.question_results)
        result["weakness"] = {"signals_detected": len(signals),
                             "types": list(set(s.weakness_type.value for s in signals)),
                             "max_severity": max((s.severity for s in signals), default=0.0)}
    
    if SPACED_REPETITION_AVAILABLE:
        due = mastery_tracker.get_due_reviews(max_items=5)
        result["reviews"] = {"due_count": len(due), "next_review_ids": [item.item_id for item in due[:3]]}
    
    return result
