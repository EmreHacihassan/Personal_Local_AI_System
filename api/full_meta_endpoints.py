"""
Full Meta Learning API Endpoints
Nöro-Adaptif Mastery Sistemi için REST API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import json

from core.full_meta_learning import (
    get_full_meta_engine,
    PackageStatus,
    LayerType,
    DifficultyLevel,
    FeynmanSubmission
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/full-meta", tags=["Full Meta Learning"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateWorkspaceRequest(BaseModel):
    """Workspace oluşturma isteği"""
    user_id: str = Field(default="default_user")
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="")
    target_goal: str = Field(..., description="Öğrenme hedefi")
    sources: List[Dict[str, str]] = Field(default_factory=list)


class AddStageRequest(BaseModel):
    """Aşama ekleme isteği"""
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="")


class AddPackageRequest(BaseModel):
    """Paket ekleme isteği"""
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(default="")
    concepts: List[Dict[str, Any]] = Field(default_factory=list)


class ConceptInput(BaseModel):
    """Kavram girişi"""
    name: str
    description: str = ""
    keywords: List[str] = []
    difficulty: str = "medium"
    estimated_minutes: int = 30


class CompleteLayerRequest(BaseModel):
    """Katman tamamlama isteği"""
    score: float = Field(..., ge=0, le=100)
    time_spent_minutes: int = Field(default=0)
    answers: Optional[Dict[str, Any]] = None


class FeynmanSubmitRequest(BaseModel):
    """Feynman anlatım gönderimi"""
    user_id: str = Field(default="default_user")
    target_audience: str = Field(..., pattern="^(child|student|expert)$")
    format: str = Field(..., pattern="^(audio|text|diagram)$")
    content: str = Field(..., min_length=50)


class ReviewRecordRequest(BaseModel):
    """Tekrar kaydı isteği"""
    user_id: str = Field(default="default_user")
    concept_id: str
    quality: int = Field(..., ge=0, le=5, description="0=blackout, 5=perfect")
    workspace_id: str = ""


class PlanSessionRequest(BaseModel):
    """Oturum planlama isteği"""
    user_id: str = Field(default="default_user")
    available_minutes: int = Field(default=45, ge=10, le=180)


class WorkspaceResponse(BaseModel):
    """Workspace yanıtı"""
    id: str
    name: str
    description: str
    target_goal: str
    stages_count: int
    total_packages: int
    overall_progress: float
    total_xp: int
    level: int
    streak_days: int
    created_at: str


class StageResponse(BaseModel):
    """Aşama yanıtı"""
    id: str
    name: str
    description: str
    order: int
    packages_count: int
    status: str
    mastery_score: float


class PackageResponse(BaseModel):
    """Paket yanıtı"""
    id: str
    name: str
    description: str
    order: int
    concepts_count: int
    layers_count: int
    current_layer_index: int
    status: str
    overall_score: float
    xp_earned: int


class LayerResponse(BaseModel):
    """Katman yanıtı"""
    id: str
    layer_type: str
    title: str
    description: str
    estimated_minutes: int
    content: Dict[str, Any]
    questions: List[Dict[str, Any]]
    completed: bool
    score: Optional[float]


class SessionPlanResponse(BaseModel):
    """Oturum planı yanıtı"""
    id: str
    date: str
    planned_minutes: int
    refresh_items: List[Dict[str, Any]]
    new_content: List[Dict[str, Any]]
    challenges: List[Dict[str, Any]]


class ProgressStatsResponse(BaseModel):
    """İlerleme istatistikleri yanıtı"""
    workspace_id: str
    name: str
    total_stages: int
    total_packages: int
    completed_packages: int
    total_layers: int
    completed_layers: int
    overall_progress: float
    total_xp: int
    level: int
    streak_days: int
    estimated_hours_remaining: float


# ============================================================================
# WORKSPACE ENDPOINTS
# ============================================================================

@router.post("/workspaces", response_model=Dict[str, Any])
async def create_workspace(request: CreateWorkspaceRequest):
    """
    Yeni öğrenme workspace'i oluştur
    
    Bir workspace, tam bir öğrenme yolculuğunu temsil eder.
    Aşamalar ve paketler içerir.
    """
    try:
        engine = get_full_meta_engine()
        workspace = await engine.create_workspace(
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            target_goal=request.target_goal,
            sources=request.sources
        )
        
        return {
            "success": True,
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "target_goal": workspace.target_goal,
                "stages_count": len(workspace.stages),
                "created_at": workspace.created_at
            }
        }
    except Exception as e:
        logger.error(f"Create workspace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces", response_model=Dict[str, Any])
async def list_workspaces(user_id: str = "default_user"):
    """Kullanıcının tüm workspace'lerini listele"""
    try:
        engine = get_full_meta_engine()
        workspaces = engine.get_user_workspaces(user_id)
        
        return {
            "success": True,
            "count": len(workspaces),
            "workspaces": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "target_goal": w.target_goal,
                    "stages_count": len(w.stages),
                    "total_packages": sum(len(s.packages) for s in w.stages),
                    "overall_progress": w.overall_progress,
                    "total_xp": w.total_xp,
                    "level": w.level,
                    "streak_days": w.streak_days,
                    "created_at": w.created_at,
                    "last_activity": w.last_activity
                }
                for w in workspaces
            ]
        }
    except Exception as e:
        logger.error(f"List workspaces error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}", response_model=Dict[str, Any])
async def get_workspace(workspace_id: str):
    """Workspace detaylarını getir"""
    try:
        engine = get_full_meta_engine()
        workspace = engine.get_workspace(workspace_id)
        
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        stages_data = []
        for stage in workspace.stages:
            packages_data = []
            for pkg in stage.packages:
                packages_data.append({
                    "id": pkg.id,
                    "name": pkg.name,
                    "description": pkg.description,
                    "order": pkg.order,
                    "concepts_count": len(pkg.concepts),
                    "layers_count": len(pkg.layers),
                    "current_layer_index": pkg.current_layer_index,
                    "status": pkg.status.value,
                    "overall_score": pkg.overall_score,
                    "xp_earned": pkg.xp_earned
                })
            
            stages_data.append({
                "id": stage.id,
                "name": stage.name,
                "description": stage.description,
                "order": stage.order,
                "packages": packages_data,
                "status": stage.status.value,
                "mastery_score": stage.mastery_score
            })
        
        return {
            "success": True,
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "description": workspace.description,
                "target_goal": workspace.target_goal,
                "stages": stages_data,
                "overall_progress": workspace.overall_progress,
                "total_xp": workspace.total_xp,
                "level": workspace.level,
                "streak_days": workspace.streak_days,
                "estimated_total_hours": workspace.estimated_total_hours,
                "actual_total_hours": workspace.actual_total_hours,
                "created_at": workspace.created_at,
                "last_activity": workspace.last_activity
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workspace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/stats", response_model=ProgressStatsResponse)
async def get_workspace_stats(workspace_id: str):
    """Workspace istatistiklerini getir"""
    try:
        engine = get_full_meta_engine()
        stats = engine.get_workspace_stats(workspace_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        return ProgressStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workspace stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STAGE ENDPOINTS
# ============================================================================

@router.post("/workspaces/{workspace_id}/stages", response_model=Dict[str, Any])
async def add_stage(workspace_id: str, request: AddStageRequest):
    """Workspace'e yeni aşama ekle"""
    try:
        engine = get_full_meta_engine()
        stage = engine.add_stage(workspace_id, request.name, request.description)
        
        if not stage:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        return {
            "success": True,
            "stage": {
                "id": stage.id,
                "name": stage.name,
                "description": stage.description,
                "order": stage.order,
                "status": stage.status.value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add stage error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PACKAGE ENDPOINTS
# ============================================================================

@router.post("/stages/{stage_id}/packages", response_model=Dict[str, Any])
async def add_package(stage_id: str, request: AddPackageRequest):
    """Aşamaya yeni paket ekle"""
    try:
        engine = get_full_meta_engine()
        package = engine.add_package(
            stage_id, 
            request.name, 
            request.description, 
            request.concepts
        )
        
        if not package:
            raise HTTPException(status_code=404, detail="Stage not found")
        
        return {
            "success": True,
            "package": {
                "id": package.id,
                "name": package.name,
                "description": package.description,
                "order": package.order,
                "concepts_count": len(package.concepts),
                "layers_count": len(package.layers),
                "status": package.status.value
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add package error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/packages/{package_id}/start", response_model=Dict[str, Any])
async def start_package(package_id: str):
    """Paketi başlat"""
    try:
        engine = get_full_meta_engine()
        package = engine.start_package(package_id)
        
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        
        # İlk katmanı döndür
        first_layer = package.layers[0] if package.layers else None
        
        return {
            "success": True,
            "package": {
                "id": package.id,
                "name": package.name,
                "status": package.status.value,
                "started_at": package.started_at
            },
            "current_layer": {
                "id": first_layer.id,
                "layer_type": first_layer.layer_type.value,
                "title": first_layer.title,
                "description": first_layer.description,
                "estimated_minutes": first_layer.estimated_minutes,
                "content": first_layer.content,
                "questions": [
                    {
                        "id": q.id,
                        "question_type": q.question_type.value,
                        "difficulty": q.difficulty.value,
                        "question_text": q.question_text,
                        "options": q.options,
                        "points": q.points,
                        "time_limit_seconds": q.time_limit_seconds
                    }
                    for q in first_layer.questions
                ]
            } if first_layer else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Start package error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packages/{package_id}/current-layer", response_model=Dict[str, Any])
async def get_current_layer(package_id: str):
    """Mevcut katmanı getir"""
    try:
        engine = get_full_meta_engine()
        result = engine.get_current_layer(package_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Package not found")
        
        package, layer = result
        
        if not layer:
            return {
                "success": True,
                "package_completed": True,
                "package": {
                    "id": package.id,
                    "name": package.name,
                    "status": package.status.value,
                    "overall_score": package.overall_score
                }
            }
        
        return {
            "success": True,
            "package": {
                "id": package.id,
                "name": package.name,
                "current_layer_index": package.current_layer_index,
                "total_layers": len(package.layers)
            },
            "layer": {
                "id": layer.id,
                "index": package.current_layer_index,
                "layer_type": layer.layer_type.value,
                "title": layer.title,
                "description": layer.description,
                "estimated_minutes": layer.estimated_minutes,
                "content": layer.content,
                "questions": [
                    {
                        "id": q.id,
                        "question_type": q.question_type.value,
                        "difficulty": q.difficulty.value,
                        "question_text": q.question_text,
                        "options": q.options,
                        "hints": q.hints,
                        "points": q.points,
                        "time_limit_seconds": q.time_limit_seconds
                    }
                    for q in layer.questions
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current layer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packages/{package_id}/layers", response_model=Dict[str, Any])
async def get_all_layers(package_id: str):
    """Paketin tüm katmanlarını getir (overview)"""
    try:
        engine = get_full_meta_engine()
        result = engine.get_current_layer(package_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Package not found")
        
        package, _ = result
        
        layers_overview = []
        for i, layer in enumerate(package.layers):
            layers_overview.append({
                "index": i,
                "id": layer.id,
                "layer_type": layer.layer_type.value,
                "title": layer.title,
                "estimated_minutes": layer.estimated_minutes,
                "completed": layer.completed,
                "score": layer.score,
                "is_current": i == package.current_layer_index,
                "is_locked": i > package.current_layer_index
            })
        
        return {
            "success": True,
            "package": {
                "id": package.id,
                "name": package.name,
                "status": package.status.value
            },
            "layers": layers_overview,
            "progress": {
                "completed": sum(1 for l in package.layers if l.completed),
                "total": len(package.layers),
                "percent": round(sum(1 for l in package.layers if l.completed) / len(package.layers) * 100, 1)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get all layers error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/packages/{package_id}/complete-layer", response_model=Dict[str, Any])
async def complete_layer(package_id: str, request: CompleteLayerRequest):
    """Mevcut katmanı tamamla"""
    try:
        engine = get_full_meta_engine()
        result = engine.complete_layer(package_id, request.score)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Complete layer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FEYNMAN ENDPOINTS
# ============================================================================

@router.post("/packages/{package_id}/feynman", response_model=Dict[str, Any])
async def submit_feynman(package_id: str, request: FeynmanSubmitRequest):
    """Feynman anlatımı gönder"""
    try:
        engine = get_full_meta_engine()
        
        submission = engine.submit_feynman(
            user_id=request.user_id,
            package_id=package_id,
            target_audience=request.target_audience,
            format=request.format,
            content=request.content
        )
        
        # Değerlendir
        analysis = await engine.evaluate_feynman(submission, package_id)
        
        return {
            "success": True,
            "submission": {
                "id": submission.id,
                "target_audience": submission.target_audience,
                "format": submission.format,
                "submitted_at": submission.submitted_at
            },
            "analysis": analysis
        }
    except Exception as e:
        logger.error(f"Submit feynman error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEMORY & SPACED REPETITION ENDPOINTS
# ============================================================================

@router.post("/memory/record-review", response_model=Dict[str, Any])
async def record_review(request: ReviewRecordRequest):
    """Tekrar kaydı oluştur (Spaced Repetition)"""
    try:
        engine = get_full_meta_engine()
        record = engine.record_review(
            user_id=request.user_id,
            concept_id=request.concept_id,
            quality=request.quality,
            workspace_id=request.workspace_id
        )
        
        return {
            "success": True,
            "record": {
                "concept_id": record.concept_id,
                "memory_strength": round(record.memory_strength, 2),
                "review_count": record.review_count,
                "correct_count": record.correct_count,
                "incorrect_count": record.incorrect_count,
                "next_review": record.next_review,
                "interval_days": round(record.interval_days, 1),
                "ease_factor": round(record.ease_factor, 2)
            }
        }
    except Exception as e:
        logger.error(f"Record review error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory/needs-review", response_model=Dict[str, Any])
async def get_needs_review(user_id: str = "default_user", workspace_id: str = None):
    """Tekrar edilmesi gereken konuları getir"""
    try:
        engine = get_full_meta_engine()
        concepts = engine.get_review_needed(user_id, workspace_id)
        
        return {
            "success": True,
            "count": len(concepts),
            "concepts": concepts
        }
    except Exception as e:
        logger.error(f"Get needs review error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION PLANNING ENDPOINTS
# ============================================================================

@router.post("/workspaces/{workspace_id}/plan-session", response_model=Dict[str, Any])
async def plan_session(workspace_id: str, request: PlanSessionRequest):
    """Günlük öğrenme oturumu planla"""
    try:
        engine = get_full_meta_engine()
        session = engine.plan_session(
            user_id=request.user_id,
            workspace_id=workspace_id,
            available_minutes=request.available_minutes
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        return {
            "success": True,
            "session": {
                "id": session.id,
                "date": session.date,
                "planned_minutes": session.planned_minutes,
                "refresh_items": session.refresh_items,
                "new_content": session.new_content,
                "challenges": session.challenges
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LAYER TYPE INFO ENDPOINT
# ============================================================================

@router.get("/layer-types", response_model=Dict[str, Any])
async def get_layer_types():
    """Tüm katman türlerini ve açıklamalarını getir"""
    return {
        "success": True,
        "layer_types": [
            {
                "type": "warmup",
                "title": "🔥 Warm-Up",
                "description": "Hafıza Aktivasyonu - Önceki öğrenmeleri hatırla",
                "scientific_basis": "Retrieval Practice (Roediger), Priming",
                "estimated_minutes": 10
            },
            {
                "type": "prime",
                "title": "💡 Prime",
                "description": "Merak Uyandırma - Bu pakette neler öğreneceksin",
                "scientific_basis": "Curiosity Gap, Advance Organizer",
                "estimated_minutes": 5
            },
            {
                "type": "acquire",
                "title": "📚 Acquire",
                "description": "Ana İçerik - Kavramları birden fazla formatta öğren",
                "scientific_basis": "Dual Coding (Paivio), Multimedia Learning",
                "estimated_minutes": 30
            },
            {
                "type": "interrogate",
                "title": "🔍 Interrogate",
                "description": "Derinleştirme - Neden ve nasıl sorularıyla derinleş",
                "scientific_basis": "Elaborative Interrogation",
                "estimated_minutes": 10
            },
            {
                "type": "practice",
                "title": "💪 Practice",
                "description": "Kademeli Problem Çözme - Kolaydan zora",
                "scientific_basis": "Deliberate Practice (Ericsson), Scaffolding",
                "estimated_minutes": 45
            },
            {
                "type": "connect",
                "title": "🔗 Connect",
                "description": "Bağlantılar & Analojiler - Mevcut bilgilerle ilişkilendir",
                "scientific_basis": "Schema Theory, Analogical Reasoning",
                "estimated_minutes": 10
            },
            {
                "type": "challenge",
                "title": "⚔️ Challenge",
                "description": "Boss Battle - Sınırlarını zorla, edge case'leri keşfet",
                "scientific_basis": "Desirable Difficulties (Bjork)",
                "estimated_minutes": 15
            },
            {
                "type": "error_lab",
                "title": "⚠️ Error Lab",
                "description": "Yaygın Hatalar - Hataları tanı, tuzaklardan kaçın",
                "scientific_basis": "Misconception Correction",
                "estimated_minutes": 10
            },
            {
                "type": "feynman",
                "title": "🎤 Feynman",
                "description": "Anlat & Öğret - Öğrendiklerini kendi kelimelerinle açıkla",
                "scientific_basis": "Teaching Effect, Generation Effect",
                "estimated_minutes": 20
            },
            {
                "type": "transfer",
                "title": "🌍 Transfer",
                "description": "Farklı Bağlamda Uygula - Yeni durumlara transfer et",
                "scientific_basis": "Far Transfer, Situated Learning",
                "estimated_minutes": 15
            },
            {
                "type": "meta_reflection",
                "title": "🪞 Meta-Reflection",
                "description": "Öz Değerlendirme - Öğrenme sürecini analiz et",
                "scientific_basis": "Metacognition (Flavell), Self-Regulation",
                "estimated_minutes": 5
            },
            {
                "type": "consolidate",
                "title": "📦 Consolidate",
                "description": "Özet & İleri Bağlantı - Öğrenilenleri paketle",
                "scientific_basis": "Spaced Repetition (Ebbinghaus), Summary",
                "estimated_minutes": 5
            }
        ]
    }


# ============================================================================
# QUICK CREATE DEMO WORKSPACE
# ============================================================================

@router.post("/demo/create-sample", response_model=Dict[str, Any])
async def create_sample_workspace(user_id: str = "default_user"):
    """Demo amaçlı örnek bir workspace oluştur"""
    try:
        engine = get_full_meta_engine()
        
        # Workspace oluştur
        workspace = await engine.create_workspace(
            user_id=user_id,
            name="Deep Learning Temelleri",
            description="Derin öğrenme temellerini sıfırdan öğren",
            target_goal="TensorFlow ile kendi modelini eğitebilir hale gel"
        )
        
        # Stage 1: Matematik Temelleri
        stage1 = engine.add_stage(
            workspace.id,
            "Matematik Temelleri",
            "Derin öğrenme için gerekli matematik altyapısı"
        )
        
        # Paket 1.1: Lineer Cebir
        engine.add_package(
            stage1.id,
            "Lineer Cebir Temelleri",
            "Matrisler, vektörler ve temel işlemler",
            [
                {"name": "Vektörler", "description": "Vektör nedir ve temel işlemleri", "difficulty": "easy"},
                {"name": "Matrisler", "description": "Matris işlemleri ve özellikleri", "difficulty": "medium"},
                {"name": "Matris Çarpımı", "description": "Matris çarpımı ve uygulamaları", "difficulty": "medium"}
            ]
        )
        
        # Paket 1.2: Kalkülüs
        engine.add_package(
            stage1.id,
            "Türev ve Gradyan",
            "Optimizasyon için gerekli kalkülüs temelleri",
            [
                {"name": "Türev Temelleri", "description": "Türev kavramı ve kuralları", "difficulty": "medium"},
                {"name": "Gradyan", "description": "Çok değişkenli fonksiyonlarda gradyan", "difficulty": "hard"},
                {"name": "Zincir Kuralı", "description": "Backpropagation için temel", "difficulty": "hard"}
            ]
        )
        
        # Stage 2: Neural Networks
        stage2 = engine.add_stage(
            workspace.id,
            "Yapay Sinir Ağları",
            "Temel neural network kavramları"
        )
        
        engine.add_package(
            stage2.id,
            "Perceptron",
            "En basit yapay nöron modeli",
            [
                {"name": "Yapay Nöron", "description": "Biyolojik esinlenme", "difficulty": "easy"},
                {"name": "Aktivasyon Fonksiyonları", "description": "Sigmoid, ReLU, Tanh", "difficulty": "medium"},
                {"name": "Öğrenme Kuralı", "description": "Ağırlık güncelleme", "difficulty": "medium"}
            ]
        )
        
        return {
            "success": True,
            "message": "Demo workspace oluşturuldu",
            "workspace": {
                "id": workspace.id,
                "name": workspace.name,
                "stages_count": len(workspace.stages),
                "total_packages": sum(len(s.packages) for s in workspace.stages)
            }
        }
    except Exception as e:
        logger.error(f"Create sample workspace error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
