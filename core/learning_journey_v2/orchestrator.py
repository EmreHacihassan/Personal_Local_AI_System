"""
🎭 Learning Journey Orchestrator
Multi-Agent Orchestration Sistemi

Bu modül Research 2.0'daki gibi çalışır:
1. Kullanıcı hedefini alır
2. Curriculum Planner ile plan oluşturur
3. Content Generator ile içerik üretir
4. Exam System ile sınavları hazırlar
5. Certificate System ile sertifika verir

Tüm süreç AI Thinking olarak görselleştirilir.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from dataclasses import dataclass, field
from enum import Enum

from .models import (
    LearningGoal, CurriculumPlan, Stage, Package, 
    UserProgress, Certificate, ContentType, ExamType,
    DifficultyLevel, StageStatus, PackageStatus
)
from .curriculum_planner import CurriculumPlannerAgent, AgentThought, get_curriculum_planner
from .content_generator import ContentGeneratorAgent, get_content_generator
from .exam_system import ExamSystem, ExamResult, get_exam_system
from .certificate_system import CertificateGenerator, get_certificate_generator


# ==================== ORCHESTRATION EVENTS ====================

class EventType(str, Enum):
    """Olay türleri"""
    PLANNING_STARTED = "planning_started"
    PLANNING_STEP = "planning_step"
    PLANNING_COMPLETED = "planning_completed"
    
    CONTENT_GENERATION_STARTED = "content_generation_started"
    CONTENT_BLOCK_CREATED = "content_block_created"
    CONTENT_GENERATION_COMPLETED = "content_generation_completed"
    
    EXAM_STARTED = "exam_started"
    EXAM_SUBMITTED = "exam_submitted"
    EXAM_GRADED = "exam_graded"
    EXAM_COMPLETED = "exam_completed"
    
    PACKAGE_STARTED = "package_started"
    PACKAGE_COMPLETED = "package_completed"
    
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    
    JOURNEY_STARTED = "journey_started"
    JOURNEY_COMPLETED = "journey_completed"
    
    CERTIFICATE_GENERATED = "certificate_generated"
    
    ERROR = "error"
    PROGRESS_UPDATE = "progress_update"


@dataclass
class OrchestrationEvent:
    """Orchestration olayı"""
    type: EventType
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    agent_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "agent_name": self.agent_name
        }


# ==================== JOURNEY STATE ====================

@dataclass
class JourneyState:
    """Yolculuk durumu"""
    plan: Optional[CurriculumPlan] = None
    current_stage_index: int = 0
    current_package_index: int = 0
    progress: Optional[UserProgress] = None
    is_active: bool = False
    started_at: Optional[str] = None
    events: List[OrchestrationEvent] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan.id if self.plan else None,
            "current_stage_index": self.current_stage_index,
            "current_package_index": self.current_package_index,
            "progress": self.progress.to_dict() if self.progress else None,
            "is_active": self.is_active,
            "started_at": self.started_at,
            "events_count": len(self.events)
        }


# ==================== LEARNING JOURNEY ORCHESTRATOR ====================

class LearningJourneyOrchestrator:
    """
    Öğrenme Yolculuğu Orkestratörü
    
    Research 2.0'daki WebSocket streaming gibi:
    - Real-time AI thinking updates
    - Progress tracking
    - Multi-agent coordination
    """
    
    def __init__(
        self,
        curriculum_planner: Optional[CurriculumPlannerAgent] = None,
        content_generator: Optional[ContentGeneratorAgent] = None,
        exam_system: Optional[ExamSystem] = None,
        certificate_generator: Optional[CertificateGenerator] = None
    ):
        self.curriculum_planner = curriculum_planner or get_curriculum_planner()
        self.content_generator = content_generator or get_content_generator()
        self.exam_system = exam_system or get_exam_system()
        self.certificate_generator = certificate_generator or get_certificate_generator()
        
        # Active journeys
        self.active_journeys: Dict[str, JourneyState] = {}
        
        # Event listeners
        self.event_listeners: List[Callable[[OrchestrationEvent], None]] = []
    
    def add_event_listener(self, listener: Callable[[OrchestrationEvent], None]):
        """Event listener ekle"""
        self.event_listeners.append(listener)
    
    def _emit_event(self, event: OrchestrationEvent):
        """Event gönder"""
        for listener in self.event_listeners:
            try:
                listener(event)
            except:
                pass
    
    # ==================== JOURNEY CREATION ====================
    
    async def create_journey(
        self,
        goal: LearningGoal,
        user_id: str
    ) -> AsyncGenerator[OrchestrationEvent, None]:
        """
        Yeni öğrenme yolculuğu oluştur
        
        Yields:
            OrchestrationEvent - Her adımda olay
        """
        
        # Planning başladı
        yield OrchestrationEvent(
            type=EventType.PLANNING_STARTED,
            data={
                "goal_id": goal.id,
                "title": goal.title,
                "subject": goal.subject,
                "message": "🎯 Hedefin analiz ediliyor..."
            },
            agent_name="Orchestrator"
        )
        
        # Müfredat planla - MASTER TIMEOUT ile (60 saniye)
        try:
            plan, thoughts = await asyncio.wait_for(
                self.curriculum_planner.plan_curriculum(goal),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            # Timeout olursa basit plan döndür
            print("[Orchestrator] Curriculum planning timeout - using fast mode")
            # Planner'ı LLM olmadan yeniden çalıştır
            from core.learning_journey_v2.curriculum_planner import CurriculumPlanner
            fast_planner = CurriculumPlanner(use_llm=False)
            plan, thoughts = await fast_planner.plan_curriculum(goal)
        
        # Her düşünce adımını yayınla
        for thought in thoughts:
            yield OrchestrationEvent(
                type=EventType.PLANNING_STEP,
                data={
                    "step": thought.step,
                    "action": thought.action,
                    "reasoning": thought.reasoning,
                    "output": thought.output if not hasattr(thought.output, 'to_dict') else thought.output
                },
                agent_name=thought.agent_name
            )
            await asyncio.sleep(0.05)  # Animasyon için kısa bekleme (hızlandırıldı)
        
        # Plan tamamlandı
        yield OrchestrationEvent(
            type=EventType.PLANNING_COMPLETED,
            data={
                "plan_id": plan.id,
                "total_stages": len(plan.stages),
                "total_packages": plan.total_packages,
                "total_exams": plan.total_exams,
                "estimated_days": plan.estimated_completion_days,
                "total_xp": plan.total_xp_possible
            },
            agent_name="Plan Finalizer"
        )
        
        # Journey state oluştur
        progress = UserProgress(
            user_id=user_id,
            journey_id=plan.id
        )
        
        state = JourneyState(
            plan=plan,
            progress=progress,
            is_active=True,
            started_at=datetime.now().isoformat()
        )
        
        self.active_journeys[plan.id] = state
        
        # Journey başladı
        yield OrchestrationEvent(
            type=EventType.JOURNEY_STARTED,
            data={
                "journey_id": plan.id,
                "user_id": user_id,
                "plan": plan.to_dict()
            },
            agent_name="Orchestrator"
        )
    
    # ==================== PACKAGE OPERATIONS ====================
    
    async def start_package(
        self,
        journey_id: str,
        package_id: str,
        user_id: str
    ) -> AsyncGenerator[OrchestrationEvent, None]:
        """Paket başlat ve içerik üret"""
        
        state = self.active_journeys.get(journey_id)
        if not state or not state.plan:
            yield OrchestrationEvent(
                type=EventType.ERROR,
                data={"message": "Journey bulunamadı"}
            )
            return
        
        # Package bul
        package = None
        stage = None
        for s in state.plan.stages:
            for p in s.packages:
                if p.id == package_id:
                    package = p
                    stage = s
                    break
            if package:
                break
        
        if not package:
            yield OrchestrationEvent(
                type=EventType.ERROR,
                data={"message": "Package bulunamadı"}
            )
            return
        
        # Package başladı
        yield OrchestrationEvent(
            type=EventType.PACKAGE_STARTED,
            data={
                "package_id": package.id,
                "title": package.title,
                "type": package.type.value
            },
            agent_name="Orchestrator"
        )
        
        # İçerik üret
        yield OrchestrationEvent(
            type=EventType.CONTENT_GENERATION_STARTED,
            data={
                "package_id": package.id,
                "topics": package.topics
            },
            agent_name="Content Generator"
        )
        
        # İçerik üretimi
        content_blocks = await self.content_generator.generate_package_content(
            package, stage, package.difficulty
        )
        
        for block in content_blocks:
            yield OrchestrationEvent(
                type=EventType.CONTENT_BLOCK_CREATED,
                data={
                    "block_id": block.id,
                    "type": block.type.value if hasattr(block.type, 'value') else str(block.type),
                    "title": block.title
                },
                agent_name="Content Generator"
            )
            await asyncio.sleep(0.05)
        
        # Content blocks'u package'a ata
        package.content_blocks = content_blocks
        package.status = PackageStatus.IN_PROGRESS
        
        yield OrchestrationEvent(
            type=EventType.CONTENT_GENERATION_COMPLETED,
            data={
                "package_id": package.id,
                "blocks_count": len(content_blocks),
                "content_blocks": [cb.to_dict() for cb in content_blocks]
            },
            agent_name="Content Generator"
        )
    
    async def complete_package(
        self,
        journey_id: str,
        package_id: str,
        user_id: str
    ) -> AsyncGenerator[OrchestrationEvent, None]:
        """Paketi tamamla"""
        
        state = self.active_journeys.get(journey_id)
        if not state or not state.plan:
            yield OrchestrationEvent(
                type=EventType.ERROR,
                data={"message": "Journey bulunamadı"}
            )
            return
        
        # Package bul ve tamamla
        for stage in state.plan.stages:
            for package in stage.packages:
                if package.id == package_id:
                    package.status = PackageStatus.PASSED
                    
                    # XP ekle ve level hesapla
                    xp_result = state.progress.add_xp(package.xp_reward)
                    state.progress.completed_packages += 1
                    
                    # Streak güncelle
                    state.progress.update_streak()
                    
                    # Sonraki paketi aç
                    pkg_index = stage.packages.index(package)
                    if pkg_index + 1 < len(stage.packages):
                        stage.packages[pkg_index + 1].status = PackageStatus.AVAILABLE
                    
                    yield OrchestrationEvent(
                        type=EventType.PACKAGE_COMPLETED,
                        data={
                            "package_id": package.id,
                            "xp_earned": package.xp_reward,
                            "total_xp": state.progress.xp_earned,
                            "level": state.progress.level,
                            "leveled_up": xp_result.get("leveled_up", False),
                            "streak_days": state.progress.streak_days
                        },
                        agent_name="Orchestrator"
                    )
                    
                    # Tüm paketler tamamlandı mı?
                    if all(p.status == PackageStatus.PASSED for p in stage.packages):
                        stage.status = StageStatus.COMPLETED
                        state.progress.completed_stages += 1
                        
                        yield OrchestrationEvent(
                            type=EventType.STAGE_COMPLETED,
                            data={
                                "stage_id": stage.id,
                                "stage_title": stage.title
                            },
                            agent_name="Orchestrator"
                        )
                        
                        # Sonraki stage'i aç
                        stage_index = state.plan.stages.index(stage)
                        if stage_index + 1 < len(state.plan.stages):
                            state.plan.stages[stage_index + 1].status = StageStatus.AVAILABLE
                            state.plan.stages[stage_index + 1].packages[0].status = PackageStatus.AVAILABLE
                    
                    return
    
    # ==================== EXAM OPERATIONS ====================
    
    async def submit_exam(
        self,
        journey_id: str,
        exam_id: str,
        submission: Dict[str, Any],
        user_id: str
    ) -> ExamResult:
        """Sınav gönder ve değerlendir"""
        
        state = self.active_journeys.get(journey_id)
        if not state or not state.plan:
            raise ValueError("Journey bulunamadı")
        
        # Exam bul
        exam = None
        for stage in state.plan.stages:
            for package in stage.packages:
                for e in package.exams:
                    if e.id == exam_id:
                        exam = e
                        break
        
        if not exam:
            raise ValueError("Exam bulunamadı")
        
        # Değerlendir
        result = await self.exam_system.evaluate_exam(
            exam=exam,
            submission=submission,
            user_id=user_id,
            attempt_number=exam.attempts + 1
        )
        
        exam.attempts += 1
        
        return result
    
    # ==================== JOURNEY COMPLETION ====================
    
    async def complete_journey(
        self,
        journey_id: str,
        user_id: str,
        user_name: str
    ) -> AsyncGenerator[OrchestrationEvent, None]:
        """Yolculuğu tamamla ve sertifika ver"""
        
        state = self.active_journeys.get(journey_id)
        if not state or not state.plan:
            yield OrchestrationEvent(
                type=EventType.ERROR,
                data={"message": "Journey bulunamadı"}
            )
            return
        
        # Tüm stage'ler tamamlandı mı kontrol et
        if not all(s.status == StageStatus.COMPLETED for s in state.plan.stages):
            yield OrchestrationEvent(
                type=EventType.ERROR,
                data={"message": "Tüm aşamalar tamamlanmadan yolculuk bitirilemez"}
            )
            return
        
        # Sertifika oluştur
        certificate = await self.certificate_generator.create_certificate(
            plan=state.plan,
            user_progress=state.progress,
            user_name=user_name,
            user_id=user_id
        )
        
        yield OrchestrationEvent(
            type=EventType.CERTIFICATE_GENERATED,
            data={
                "certificate_id": certificate.id,
                "verification_code": certificate.verification_code,
                "badge_level": certificate.badge_level
            },
            agent_name="Certificate Generator"
        )
        
        # Journey tamamlandı
        state.is_active = False
        
        yield OrchestrationEvent(
            type=EventType.JOURNEY_COMPLETED,
            data={
                "journey_id": journey_id,
                "total_xp": state.progress.xp_earned,
                "total_time_hours": state.progress.total_time_spent / 3600,
                "certificate": certificate.to_dict()
            },
            agent_name="Orchestrator"
        )
    
    # ==================== PROGRESS TRACKING ====================
    
    def get_journey_state(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Journey durumunu getir"""
        
        state = self.active_journeys.get(journey_id)
        if not state:
            return None
        
        return state.to_dict()
    
    def get_stage_map(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Stage haritasını getir - Frontend uyumlu format"""
        
        state = self.active_journeys.get(journey_id)
        if not state or not state.plan:
            return None
        
        stages = []
        for stage in state.plan.stages:
            # Packages'ı frontend formatına çevir
            packages = []
            for pkg in stage.packages:
                pkg_type = pkg.type.value if hasattr(pkg.type, 'value') else str(pkg.type)
                pkg_status = pkg.status.value if hasattr(pkg.status, 'value') else str(pkg.status)
                
                packages.append({
                    # Primary fields (new format)
                    "id": pkg.id,
                    "title": pkg.title,
                    "type": pkg_type,
                    "number": pkg.number,
                    "status": pkg_status,
                    # Alias fields (old format for compatibility)
                    "package_id": pkg.id,
                    "name": pkg.title,
                    "package_type": pkg_type,
                    "order": pkg.number,
                    # Common fields
                    "description": pkg.description,
                    "progress_percentage": 100.0 if pkg.status == PackageStatus.PASSED else 0.0,
                    "xp_earned": pkg.xp_reward if pkg.status == PackageStatus.PASSED else 0,
                    "xp_total": pkg.xp_reward,
                    "xp_reward": pkg.xp_reward,
                    "content_blocks": [
                        {
                            "id": cb.id,
                            "type": cb.type.value if hasattr(cb.type, 'value') else str(cb.type),
                            "block_type": cb.type.value if hasattr(cb.type, 'value') else str(cb.type),
                            "title": cb.title,
                            "content": cb.content.get("markdown", "") if isinstance(cb.content, dict) else str(cb.content),
                            "media_url": cb.media_url,
                            "completed": False
                        } for cb in (pkg.content_blocks or [])
                    ],
                    "exercises": [
                        {
                            "id": ex.id,
                            "type": ex.type.value if hasattr(ex.type, 'value') else str(ex.type),
                            "exercise_type": ex.type.value if hasattr(ex.type, 'value') else str(ex.type),
                            "title": ex.title,
                            "description": ex.instructions,
                            "instructions": ex.instructions,
                            "completed": False,
                            "score": None
                        } for ex in (pkg.exercises or [])
                    ],
                    "exams": [
                        {
                            "id": exam.id,
                            "type": exam.type.value if hasattr(exam.type, 'value') else str(exam.type),
                            "exam_type": exam.type.value if hasattr(exam.type, 'value') else str(exam.type),
                            "title": exam.title,
                            "description": exam.description,
                            "topic": exam.questions[0].topic if exam.questions else pkg.topics[0] if pkg.topics else "",
                            "time_limit_minutes": exam.time_limit_minutes or 30,
                            "passing_score": exam.passing_score,
                            "status": "pending",
                            "score": None,
                            "questions": [q.to_dict() for q in (exam.questions or [])]
                        } for exam in (pkg.exams or [])
                    ]
                })
            
            stage_status = stage.status.value if hasattr(stage.status, 'value') else str(stage.status)
            
            stages.append({
                # Primary fields (new format)
                "id": stage.id,
                "title": stage.title,
                "number": stage.number,
                "status": stage_status,
                # Alias fields (old format for compatibility)
                "stage_id": stage.id,
                "name": stage.title,
                "order": stage.number,
                # Common fields
                "description": stage.description,
                "packages": packages,
                "progress_percentage": stage.progress_percentage,
                "xp_earned": stage.xp_earned,
                "xp_total": stage.xp_total
            })
        
        return {
            "journey_id": journey_id,
            "title": state.plan.title,
            "subject": state.plan.subject,
            "target_outcome": state.plan.target_outcome,
            "total_stages": len(state.plan.stages),
            "total_packages": state.plan.total_packages,
            "total_exams": state.plan.total_exams,
            "total_exercises": state.plan.total_exercises,
            "estimated_total_hours": state.plan.estimated_completion_days * 2,  # Günde 2 saat varsayımı
            "total_xp_possible": state.plan.total_xp_possible,
            "stages": stages,
            "progress": {
                "completed_packages": state.progress.completed_packages if state.progress else 0,
                "total_packages": state.plan.total_packages,
                "completed_exams": state.progress.completed_exams if state.progress else 0,
                "total_exams": state.plan.total_exams,
                "xp_earned": state.progress.xp_earned if state.progress else 0,
                "xp_total": state.plan.total_xp_possible,
                "streak_days": state.progress.streak_days if state.progress else 0,
                "level": state.progress.level if state.progress else 1
            } if state.progress else None
        }
    
    def list_journeys(self, user_id: str = "default_user") -> List[Dict[str, Any]]:
        """Kullanıcının tüm yolculuklarını listele"""
        
        journeys = []
        for journey_id, state in self.active_journeys.items():
            if not state.plan:
                continue
            
            # User ID kontrolü (progress'ten)
            if state.progress and state.progress.user_id != user_id:
                continue
            
            journeys.append({
                "journey_id": journey_id,
                "title": state.plan.title,
                "subject": state.plan.subject,
                "target_outcome": state.plan.target_outcome,
                "total_stages": len(state.plan.stages),
                "total_packages": state.plan.total_packages,
                "total_exams": state.plan.total_exams,
                "total_exercises": state.plan.total_exercises,
                "estimated_total_hours": state.plan.estimated_total_hours,
                "total_xp_possible": state.plan.total_xp_possible,
                "created_at": state.started_at,
                "is_active": state.is_active,
                "progress": {
                    "completed_packages": state.progress.completed_packages if state.progress else 0,
                    "total_packages": state.plan.total_packages,
                    "completed_exams": state.progress.completed_exams if state.progress else 0,
                    "total_exams": state.plan.total_exams,
                    "xp_earned": state.progress.xp_earned if state.progress else 0,
                    "xp_total": state.plan.total_xp_possible,
                    "streak_days": state.progress.streak_days if state.progress else 0,
                    "level": state.progress.level if state.progress else 1
                } if state.progress else None
            })
        
        return journeys
    
    def update_time_spent(self, journey_id: str, seconds: int):
        """Harcanan zamanı güncelle"""
        
        state = self.active_journeys.get(journey_id)
        if state and state.progress:
            state.progress.total_time_spent += seconds


# ==================== WEBSOCKET HELPER ====================

async def stream_journey_creation(
    orchestrator: LearningJourneyOrchestrator,
    goal: LearningGoal,
    user_id: str,
    send_func: Callable[[Dict[str, Any]], None]
):
    """WebSocket üzerinden journey oluşturma stream'i"""
    
    async for event in orchestrator.create_journey(goal, user_id):
        await send_func(event.to_dict())


# ==================== SINGLETON ====================

_orchestrator: Optional[LearningJourneyOrchestrator] = None

def get_learning_orchestrator() -> LearningJourneyOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LearningJourneyOrchestrator()
    return _orchestrator
