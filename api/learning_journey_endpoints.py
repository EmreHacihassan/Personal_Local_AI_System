"""
🎮 Learning Journey API Endpoints
Candy Crush tarzı stage map için API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.learning_journey_system import (
    get_stage_map_generator,
    get_content_generator,
    MATH_CURRICULUM,
    StageStatus,
    ContentType,
    DifficultyLevel,
    PackageTheme
)

router = APIRouter(prefix="/api/learning-journey", tags=["Learning Journey"])


# ==================== REQUEST/RESPONSE MODELS ====================

class CreatePathRequest(BaseModel):
    user_id: str
    subject: str = "Matematik"
    goal: str = "AYT sınavında başarılı olmak"


class UpdateProgressRequest(BaseModel):
    user_id: str
    stage_id: str
    content_id: str
    score: float = Field(ge=0, le=100)
    completed: bool = True


class ContentCompletionRequest(BaseModel):
    user_id: str
    stage_id: str
    content_id: str
    time_spent_seconds: int
    answers: Optional[Dict[str, Any]] = None


class StageStartRequest(BaseModel):
    user_id: str
    stage_id: str


# ==================== PATH ENDPOINTS ====================

@router.post("/path/create")
async def create_learning_path(request: CreatePathRequest):
    """
    Kullanıcı için yeni öğrenme yolu oluştur.
    Tüm paketler ve stage'ler otomatik oluşturulur.
    """
    generator = get_stage_map_generator()
    
    # Mevcut yolu kontrol et
    existing_path = generator.get_user_path(request.user_id)
    if existing_path and existing_path.subject == request.subject:
        return {
            "message": "Path already exists",
            "path": existing_path.to_dict()
        }
    
    # Yeni yol oluştur
    path = await generator.generate_learning_path(
        user_id=request.user_id,
        subject=request.subject,
        goal=request.goal
    )
    
    return {
        "message": "Learning path created successfully",
        "path": path.to_dict(),
        "stats": {
            "total_packages": len(path.packages),
            "total_stages": sum(len(p.stages) for p in path.packages),
            "total_xp": sum(p.total_xp for p in path.packages),
            "estimated_days": path.estimated_completion_days
        }
    }


@router.get("/path/{user_id}")
async def get_learning_path(user_id: str):
    """Kullanıcının öğrenme yolunu getir"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    return {
        "path": path.to_dict(),
        "progress": {
            "total_xp": path.total_xp,
            "total_stars": path.total_stars,
            "streak_days": path.streak_days,
            "current_package": path.current_package_id,
            "current_stage": path.current_stage_id
        }
    }


@router.get("/path/{user_id}/summary")
async def get_path_summary(user_id: str):
    """Öğrenme yolu özeti (hafif veri)"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    packages_summary = []
    for pkg in path.packages:
        completed_stages = sum(1 for s in pkg.stages if s.status == StageStatus.COMPLETED)
        packages_summary.append({
            "id": pkg.id,
            "name": pkg.name,
            "theme": pkg.theme.value if isinstance(pkg.theme, PackageTheme) else pkg.theme,
            "is_unlocked": pkg.is_unlocked,
            "total_stages": len(pkg.stages),
            "completed_stages": completed_stages,
            "completion_percentage": pkg.completion_percentage,
            "total_xp": pkg.total_xp,
            "earned_xp": pkg.earned_xp
        })
    
    return {
        "user_id": user_id,
        "subject": path.subject,
        "goal": path.goal,
        "packages": packages_summary,
        "stats": {
            "total_xp": path.total_xp,
            "total_stars": path.total_stars,
            "streak_days": path.streak_days
        }
    }


# ==================== PACKAGE ENDPOINTS ====================

@router.get("/packages/{user_id}")
async def get_user_packages(user_id: str):
    """Kullanıcının tüm paketlerini getir"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    return {
        "packages": [pkg.to_dict() for pkg in path.packages],
        "current_package_id": path.current_package_id
    }


@router.get("/package/{user_id}/{package_id}")
async def get_package_detail(user_id: str, package_id: str):
    """Tek bir paketin detaylarını getir"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    for pkg in path.packages:
        if pkg.id == package_id:
            return {
                "package": pkg.to_dict(),
                "is_current": pkg.id == path.current_package_id
            }
    
    raise HTTPException(status_code=404, detail="Package not found")


@router.get("/package/{user_id}/{package_id}/map")
async def get_package_map(user_id: str, package_id: str):
    """
    Candy Crush tarzı stage haritası verisi.
    Stage pozisyonları, durumları ve bağlantıları.
    """
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    for pkg in path.packages:
        if pkg.id == package_id:
            # Stage bağlantıları oluştur
            connections = []
            for i, stage in enumerate(pkg.stages[:-1]):
                connections.append({
                    "from": stage.id,
                    "to": pkg.stages[i + 1].id,
                    "is_unlocked": pkg.stages[i + 1].status != StageStatus.LOCKED
                })
            
            stages_map = []
            for stage in pkg.stages:
                stages_map.append({
                    "id": stage.id,
                    "number": stage.number,
                    "title": stage.title,
                    "status": stage.status.value if isinstance(stage.status, StageStatus) else stage.status,
                    "stars": stage.stars,
                    "position": stage.position,
                    "is_boss": stage.id == pkg.boss_stage_id,
                    "has_special_reward": stage.special_reward is not None,
                    "xp_total": stage.xp_total,
                    "xp_earned": stage.xp_earned
                })
            
            return {
                "package_id": package_id,
                "package_name": pkg.name,
                "theme": pkg.theme.value if isinstance(pkg.theme, PackageTheme) else pkg.theme,
                "color_scheme": pkg.color_scheme,
                "stages": stages_map,
                "connections": connections,
                "current_stage_id": path.current_stage_id if path.current_package_id == package_id else None
            }
    
    raise HTTPException(status_code=404, detail="Package not found")


# ==================== STAGE ENDPOINTS ====================

@router.get("/stage/{user_id}/{stage_id}")
async def get_stage_detail(user_id: str, stage_id: str):
    """Stage detayları ve içerikleri"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    for pkg in path.packages:
        for stage in pkg.stages:
            if stage.id == stage_id:
                return {
                    "stage": stage.to_dict(),
                    "package": {
                        "id": pkg.id,
                        "name": pkg.name,
                        "theme": pkg.theme.value if isinstance(pkg.theme, PackageTheme) else pkg.theme
                    },
                    "is_current": stage.id == path.current_stage_id
                }
    
    raise HTTPException(status_code=404, detail="Stage not found")


@router.post("/stage/start")
async def start_stage(request: StageStartRequest):
    """Stage'e başla"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(request.user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    for pkg in path.packages:
        for stage in pkg.stages:
            if stage.id == request.stage_id:
                if stage.status == StageStatus.LOCKED:
                    raise HTTPException(status_code=403, detail="Stage is locked")
                
                if stage.status == StageStatus.AVAILABLE:
                    stage.status = StageStatus.IN_PROGRESS
                
                path.current_stage_id = stage.id
                path.current_package_id = pkg.id
                path.last_activity = datetime.now().isoformat()
                
                return {
                    "message": "Stage started",
                    "stage": stage.to_dict(),
                    "first_content": stage.contents[0].to_dict() if stage.contents else None
                }
    
    raise HTTPException(status_code=404, detail="Stage not found")


@router.post("/stage/complete-content")
async def complete_stage_content(request: ContentCompletionRequest):
    """Stage içeriğini tamamla"""
    generator = get_stage_map_generator()
    
    result = generator.update_stage_progress(
        user_id=request.user_id,
        stage_id=request.stage_id,
        content_id=request.content_id,
        score=100.0,  # İçerik tamamlama varsayılan 100
        completed=True
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/progress/update")
async def update_progress(request: UpdateProgressRequest):
    """İlerleme güncelle (quiz/practice sonuçları)"""
    generator = get_stage_map_generator()
    
    result = generator.update_stage_progress(
        user_id=request.user_id,
        stage_id=request.stage_id,
        content_id=request.content_id,
        score=request.score,
        completed=request.completed
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


# ==================== CONTENT ENDPOINTS ====================

@router.get("/content/{user_id}/{stage_id}/{content_id}")
async def get_content_detail(user_id: str, stage_id: str, content_id: str):
    """İçerik detayını getir"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    for pkg in path.packages:
        for stage in pkg.stages:
            if stage.id == stage_id:
                for content in stage.contents:
                    if content.id == content_id:
                        return {
                            "content": content.to_dict(),
                            "stage_title": stage.title,
                            "package_name": pkg.name
                        }
    
    raise HTTPException(status_code=404, detail="Content not found")


@router.get("/content/{user_id}/{stage_id}/next")
async def get_next_content(user_id: str, stage_id: str):
    """Tamamlanmamış sonraki içeriği getir"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    for pkg in path.packages:
        for stage in pkg.stages:
            if stage.id == stage_id:
                for content in stage.contents:
                    if not content.is_completed:
                        return {
                            "content": content.to_dict(),
                            "stage_title": stage.title,
                            "remaining": sum(1 for c in stage.contents if not c.is_completed)
                        }
                
                return {
                    "message": "All content completed",
                    "stage_completed": True
                }
    
    raise HTTPException(status_code=404, detail="Stage not found")


# ==================== STATS ENDPOINTS ====================

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """Kullanıcı istatistikleri"""
    generator = get_stage_map_generator()
    path = generator.get_user_path(user_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    
    total_stages = sum(len(p.stages) for p in path.packages)
    completed_stages = sum(
        sum(1 for s in p.stages if s.status == StageStatus.COMPLETED)
        for p in path.packages
    )
    
    total_contents = sum(
        sum(len(s.contents) for s in p.stages)
        for p in path.packages
    )
    completed_contents = sum(
        sum(sum(1 for c in s.contents if c.is_completed) for s in p.stages)
        for p in path.packages
    )
    
    max_possible_xp = sum(p.total_xp for p in path.packages)
    max_possible_stars = total_stages * 3
    
    return {
        "user_id": user_id,
        "subject": path.subject,
        "xp": {
            "earned": path.total_xp,
            "total": max_possible_xp,
            "percentage": (path.total_xp / max_possible_xp * 100) if max_possible_xp > 0 else 0
        },
        "stars": {
            "earned": path.total_stars,
            "total": max_possible_stars,
            "percentage": (path.total_stars / max_possible_stars * 100) if max_possible_stars > 0 else 0
        },
        "stages": {
            "completed": completed_stages,
            "total": total_stages,
            "percentage": (completed_stages / total_stages * 100) if total_stages > 0 else 0
        },
        "contents": {
            "completed": completed_contents,
            "total": total_contents,
            "percentage": (completed_contents / total_contents * 100) if total_contents > 0 else 0
        },
        "streak_days": path.streak_days,
        "estimated_completion_days": path.estimated_completion_days,
        "last_activity": path.last_activity
    }


# ==================== CURRICULUM ENDPOINTS ====================

@router.get("/curriculum/available")
async def get_available_curricula():
    """Mevcut müfredat seçenekleri"""
    return {
        "curricula": [
            {
                "id": "math_ayt",
                "name": "Matematik (AYT)",
                "packages": list(MATH_CURRICULUM.keys()),
                "total_topics": sum(len(v["topics"]) for v in MATH_CURRICULUM.values()),
                "estimated_hours": sum(v["estimated_hours"] for v in MATH_CURRICULUM.values())
            }
        ]
    }


@router.get("/curriculum/math")
async def get_math_curriculum():
    """Matematik müfredatı detayları"""
    curriculum_data = []
    for pkg_name, pkg_info in MATH_CURRICULUM.items():
        curriculum_data.append({
            "package_name": pkg_name,
            "topics": pkg_info["topics"],
            "difficulty": pkg_info["difficulty"].value,
            "theme": pkg_info["theme"].value,
            "estimated_hours": pkg_info["estimated_hours"]
        })
    
    return {
        "subject": "Matematik",
        "packages": curriculum_data,
        "total_packages": len(curriculum_data),
        "total_topics": sum(len(p["topics"]) for p in curriculum_data),
        "total_hours": sum(p["estimated_hours"] for p in curriculum_data)
    }
