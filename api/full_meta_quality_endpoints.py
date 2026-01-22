"""
Full Meta Learning - Quality Enhancements API
2026 öğrenci deneyimi için kalite iyileştirme endpoint'leri

Bu endpoint'ler mevcut öğrenme sisteminin VERİMLİLİĞİNİ kritik derecede artırır.
"""

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/full-meta/quality", tags=["Full Meta Quality"])


# ==================== PYDANTIC MODELS ====================

class StartSessionRequest(BaseModel):
    user_id: str
    content_difficulty: float = Field(0.5, ge=0, le=1)


class AttentionSignalRequest(BaseModel):
    session_id: str
    signal_type: str  # active, idle, distraction, return, progress
    signal_data: Optional[Dict[str, Any]] = None


class LearningMomentRequest(BaseModel):
    user_id: str
    moment_type: str = "break"  # waiting, commute, break
    available_seconds: int = 60
    location: str = "unknown"
    device: str = "phone"


class FeedbackRequest(BaseModel):
    user_id: str
    event_type: str  # correct, incorrect, streak, level_up, flow
    difficulty: str = "medium"
    xp: int = 10
    consecutive_errors: int = 0


class ContentLoadRequest(BaseModel):
    content: Dict[str, Any]
    user_id: Optional[str] = None
    session_duration_minutes: int = 0


class ActivityRequest(BaseModel):
    user_id: str
    activity_type: str  # session_complete, item_complete, xp_earned, daily_login
    value: int = 1


class MicroContentRequest(BaseModel):
    content: str
    topic: str
    target_duration: int = 30


# ==================== LAZY IMPORTS ====================

def get_quality_engines():
    """Kalite iyileştirme engine'lerini lazy load"""
    from core.full_meta_quality_enhancements import (
        attention_flow_manager,
        micro_learning_optimizer,
        realtime_feedback_engine,
        cognitive_load_balancer,
        learning_momentum_engine
    )
    return {
        "attention": attention_flow_manager,
        "micro": micro_learning_optimizer,
        "feedback": realtime_feedback_engine,
        "cognitive": cognitive_load_balancer,
        "momentum": learning_momentum_engine
    }


# ==================== ATTENTION FLOW ENDPOINTS ====================

@router.post("/attention/start-session")
async def start_attention_session(request: StartSessionRequest):
    """
    Dikkat oturumu başlat.
    Flow state tracking ve dikkat yönetimi başlatır.
    """
    engines = get_quality_engines()
    session = engines["attention"].start_session(
        request.user_id,
        request.content_difficulty
    )
    
    return {
        "session_id": session.id,
        "optimal_session_length": session.optimal_session_length,
        "next_micro_break": session.next_micro_break.isoformat() if session.next_micro_break else None,
        "distraction_risk_score": session.distraction_risk_score
    }


@router.post("/attention/signal")
async def record_attention_signal(request: AttentionSignalRequest):
    """
    Dikkat sinyali kaydet.
    
    Sinyal tipleri:
    - active: Aktif çalışma (scrolling, typing, clicking)
    - idle: Pasif (hareketsizlik)
    - distraction: Dikkat dağılması (tab switch, notification)
    - return: Dönüş (dikkat yeniden kazanıldı)
    - progress: İlerleme (soru cevaplama, içerik tamamlama)
    """
    engines = get_quality_engines()
    result = engines["attention"].record_attention_signal(
        request.session_id,
        request.signal_type,
        request.signal_data
    )
    
    return result


@router.get("/attention/optimal-config/{user_id}")
async def get_optimal_session_config(
    user_id: str,
    content_type: str = Query("learning")
):
    """
    Kullanıcı için optimal oturum konfigürasyonu al.
    Saate ve kullanıcı profiline göre kişiselleştirilmiş ayarlar.
    """
    engines = get_quality_engines()
    config = engines["attention"].get_optimal_session_config(user_id, content_type)
    
    return config


@router.get("/attention/flow-tips/{user_id}")
async def get_flow_tips(user_id: str):
    """Flow state'e girme ipuçları"""
    engines = get_quality_engines()
    profile = engines["attention"]._get_or_create_profile(user_id)
    
    tips = []
    
    # Zaman bazlı ipuçları
    current_hour = datetime.now().hour
    if current_hour in profile.peak_performance_hours:
        tips.append({
            "type": "peak_hour",
            "icon": "🔥",
            "message": "Şu an en verimli saatlerinden birinde olduğun zamandasın!"
        })
    elif current_hour in profile.distraction_prone_hours:
        tips.append({
            "type": "caution",
            "icon": "⚠️",
            "message": "Bu saatlerde dikkat dağılması riski yüksek. Focus mode'u aç."
        })
    
    # Flow trigger patterns
    if profile.flow_trigger_patterns:
        tips.append({
            "type": "trigger",
            "icon": "🎯",
            "message": f"Flow'a girmek için dene: {profile.flow_trigger_patterns[0]}"
        })
    
    # Ortalama süre bilgisi
    tips.append({
        "type": "info",
        "icon": "⏱️",
        "message": f"Ortalama {profile.avg_time_to_flow:.0f} dakikada flow'a giriyorsun. Sabırlı ol!"
    })
    
    return {
        "tips": tips,
        "avg_focus_duration": profile.avg_focus_duration,
        "preferred_session_length": profile.preferred_session_length,
        "total_flow_minutes": profile.total_flow_minutes,
        "best_flow_streak": profile.best_flow_streak
    }


# ==================== MICRO-LEARNING ENDPOINTS ====================

@router.post("/micro/chunk-content")
async def chunk_content_to_micro(request: MicroContentRequest):
    """
    İçeriği mikro parçalara böl.
    TikTok tarzı swipe edilebilir içerikler oluşturur.
    """
    engines = get_quality_engines()
    units = engines["micro"].chunk_content_to_micro(
        request.content,
        request.topic,
        request.target_duration
    )
    
    return {
        "units": [
            {
                "id": u.id,
                "type": u.content_type.value,
                "title": u.title,
                "content": u.content,
                "visual": u.visual_aid,
                "duration": u.duration_seconds,
                "interaction": u.interaction_type
            }
            for u in units
        ],
        "total_duration_seconds": sum(u.duration_seconds for u in units)
    }


@router.post("/micro/detect-moment")
async def detect_learning_moment(request: LearningMomentRequest):
    """
    Öğrenme anı tespit et.
    Dead time'ları öğrenme fırsatına çevirir.
    """
    engines = get_quality_engines()
    moment = engines["micro"].detect_learning_moment(
        request.user_id,
        {
            "moment_type": request.moment_type,
            "available_seconds": request.available_seconds,
            "location": request.location,
            "device": request.device
        }
    )
    
    if not moment:
        return {"detected": False, "reason": "Duration too short"}
    
    return {
        "detected": True,
        "moment_id": moment.id,
        "moment_type": moment.moment_type,
        "available_seconds": moment.available_seconds,
        "suggested_unit_ids": moment.suggested_units
    }


@router.get("/micro/feed/{user_id}")
async def get_micro_feed(user_id: str, count: int = Query(5, le=10)):
    """
    TikTok/Instagram tarzı mikro içerik akışı.
    Swipe ile geçilebilir hızlı öğrenme içerikleri.
    """
    engines = get_quality_engines()
    feed = engines["micro"].get_micro_feed(user_id, count)
    
    return {
        "feed": feed,
        "swipe_enabled": True,
        "interaction_mode": "card"
    }


# ==================== REAL-TIME FEEDBACK ENDPOINTS ====================

@router.post("/feedback/generate")
async def generate_feedback(request: FeedbackRequest):
    """
    Anında geri bildirim oluştur.
    Dopamin odaklı mikro ödüller ve görsel feedback.
    """
    engines = get_quality_engines()
    feedback = engines["feedback"].generate_feedback(
        request.user_id,
        request.event_type,
        {
            "difficulty": request.difficulty,
            "xp": request.xp,
            "consecutive_errors": request.consecutive_errors
        }
    )
    
    return {
        "event_type": feedback.event_type,
        "intensity": feedback.intensity.value,
        "timing": feedback.timing.value,
        "animation": feedback.animation,
        "color": feedback.color,
        "icon": feedback.icon,
        "message": feedback.message,
        "sound": feedback.sound,
        "haptic": feedback.haptic,
        "stat_update": feedback.stat_update
    }


@router.get("/feedback/progress/{user_id}")
async def get_progress_animation(user_id: str, target: str = Query("daily")):
    """
    İlerleme animasyonu verisi.
    Gamification progress bar/ring için.
    """
    engines = get_quality_engines()
    animation_data = engines["feedback"].get_progress_animation(user_id, target)
    
    return animation_data


@router.get("/feedback/stats/{user_id}")
async def get_user_feedback_stats(user_id: str):
    """Kullanıcı feedback istatistikleri"""
    engines = get_quality_engines()
    stats = engines["feedback"].user_stats.get(user_id, {
        "total_correct": 0,
        "total_incorrect": 0,
        "current_streak": 0,
        "best_streak": 0,
        "xp": 0,
        "level": 1
    })
    
    return {
        "total_correct": stats.get("total_correct", 0),
        "total_incorrect": stats.get("total_incorrect", 0),
        "accuracy_rate": stats["total_correct"] / max(1, stats["total_correct"] + stats["total_incorrect"]) * 100,
        "current_streak": stats.get("current_streak", 0),
        "best_streak": stats.get("best_streak", 0),
        "xp": stats.get("xp", 0),
        "level": stats.get("level", 1)
    }


# ==================== COGNITIVE LOAD ENDPOINTS ====================

@router.post("/cognitive/analyze-content")
async def analyze_content_load(request: ContentLoadRequest):
    """
    İçeriğin bilişsel yükünü analiz et.
    Sweller's Cognitive Load Theory bazlı.
    """
    engines = get_quality_engines()
    loads = engines["cognitive"].analyze_content_load(request.content)
    
    # Yük seviyesi belirleme
    total = loads["total"]
    if total < 40:
        level = "minimal"
        warning = "İçerik çok basit, sıkılma riski"
    elif total < 70:
        level = "optimal"
        warning = None
    elif total < 85:
        level = "high"
        warning = "Yük yüksek, içerik basitleştirilebilir"
    else:
        level = "overload"
        warning = "Aşırı yük! İçerik bölünmeli"
    
    return {
        "intrinsic_load": loads["intrinsic"],
        "extraneous_load": loads["extraneous"],
        "germane_load": loads["germane"],
        "total_load": loads["total"],
        "load_level": level,
        "warning": warning
    }


@router.post("/cognitive/adjust-content")
async def adjust_content_for_load(request: ContentLoadRequest):
    """
    İçeriği kullanıcının kapasitesine göre ayarla.
    Otomatik basitleştirme ve zorluk ayarlama.
    """
    engines = get_quality_engines()
    
    # Kullanıcı durumunu al
    user_state = engines["cognitive"].get_user_cognitive_state(
        request.user_id or "default",
        request.session_duration_minutes
    )
    
    # İçeriği ayarla
    adjusted = engines["cognitive"].adjust_content_for_load(
        request.content,
        user_state
    )
    
    return {
        "original_content": request.content,
        "adjusted_content": adjusted,
        "user_capacity": user_state.available_capacity,
        "fatigue_factor": user_state.fatigue_factor,
        "adjustments_made": adjusted.get("_adjustments", [])
    }


@router.get("/cognitive/pacing/{user_id}")
async def get_pacing_recommendation(user_id: str):
    """
    Tempo önerisi - ne kadar hızlı/yavaş ilerlemeli.
    Kullanıcının mevcut bilişsel yüküne göre.
    """
    engines = get_quality_engines()
    recommendation = engines["cognitive"].get_pacing_recommendation(user_id)
    
    return recommendation


# ==================== MOMENTUM ENDPOINTS ====================

@router.post("/momentum/record-activity")
async def record_activity(request: ActivityRequest):
    """
    Aktivite kaydet ve momentum güncelle.
    
    Aktivite tipleri:
    - session_complete: Oturum tamamlandı
    - item_complete: Öğe tamamlandı
    - xp_earned: XP kazanıldı
    - daily_login: Günlük giriş
    """
    engines = get_quality_engines()
    momentum = engines["momentum"].record_activity(
        request.user_id,
        request.activity_type,
        request.value
    )
    
    return {
        "momentum_score": momentum.momentum_score,
        "state": momentum.state.value,
        "daily_streak": momentum.daily_streak,
        "session_streak": momentum.session_streak,
        "xp_today": momentum.xp_today,
        "risk_factors": momentum.risk_factors,
        "boost_opportunities": momentum.boost_opportunities
    }


@router.get("/momentum/{user_id}")
async def get_momentum_status(user_id: str):
    """Kullanıcının momentum durumunu al"""
    engines = get_quality_engines()
    momentum = engines["momentum"]._get_or_create_momentum(user_id)
    
    return {
        "momentum_score": momentum.momentum_score,
        "state": momentum.state.value,
        "daily_streak": momentum.daily_streak,
        "weekly_streak": momentum.weekly_streak,
        "sessions_today": momentum.sessions_today,
        "items_today": momentum.items_today,
        "xp_today": momentum.xp_today,
        "trend_direction": momentum.trend_direction,
        "velocity": momentum.velocity,
        "risk_factors": momentum.risk_factors,
        "boost_opportunities": momentum.boost_opportunities
    }


@router.get("/momentum/comeback/{user_id}")
async def get_comeback_path(user_id: str):
    """
    Momentum kaybeden kullanıcı için geri dönüş yolu.
    Gentle re-onboarding.
    """
    engines = get_quality_engines()
    path = engines["momentum"].get_comeback_path(user_id)
    
    return path


@router.get("/momentum/notification/{user_id}")
async def get_momentum_notification(user_id: str):
    """
    Momentum boost için proaktif bildirim.
    Streak kurtarma, hedef yaklaşma vb.
    """
    engines = get_quality_engines()
    notification = engines["momentum"].get_momentum_boost_notification(user_id)
    
    if not notification:
        return {"has_notification": False}
    
    return {
        "has_notification": True,
        **notification
    }


# ==================== COMBINED QUALITY DASHBOARD ====================

@router.get("/dashboard/{user_id}")
async def get_quality_dashboard(user_id: str):
    """
    Tüm kalite metriklerini birleştiren dashboard.
    2026 öğrenci deneyimi için tek bakışta durum.
    """
    engines = get_quality_engines()
    
    # Attention
    attention_profile = engines["attention"]._get_or_create_profile(user_id)
    
    # Feedback stats
    feedback_stats = engines["feedback"].user_stats.get(user_id, {})
    
    # Momentum
    momentum = engines["momentum"]._get_or_create_momentum(user_id)
    
    # Cognitive state
    cognitive_state = engines["cognitive"].get_user_cognitive_state(user_id)
    
    return {
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        
        "attention": {
            "avg_focus_duration_minutes": attention_profile.avg_focus_duration,
            "peak_hours": attention_profile.peak_performance_hours,
            "total_flow_minutes": attention_profile.total_flow_minutes,
            "best_flow_streak_minutes": attention_profile.best_flow_streak
        },
        
        "performance": {
            "accuracy_rate": feedback_stats.get("total_correct", 0) / max(1, feedback_stats.get("total_correct", 0) + feedback_stats.get("total_incorrect", 0)) * 100,
            "current_streak": feedback_stats.get("current_streak", 0),
            "best_streak": feedback_stats.get("best_streak", 0),
            "level": feedback_stats.get("level", 1),
            "total_xp": feedback_stats.get("xp", 0)
        },
        
        "momentum": {
            "score": momentum.momentum_score,
            "state": momentum.state.value,
            "daily_streak": momentum.daily_streak,
            "risk_factors": momentum.risk_factors
        },
        
        "cognitive": {
            "available_capacity": cognitive_state.available_capacity,
            "fatigue_factor": cognitive_state.fatigue_factor,
            "recommended_pace": engines["cognitive"].get_pacing_recommendation(user_id)
        },
        
        "recommendations": _generate_quality_recommendations(
            attention_profile, feedback_stats, momentum, cognitive_state
        )
    }


def _generate_quality_recommendations(
    attention_profile,
    feedback_stats,
    momentum,
    cognitive_state
) -> List[Dict]:
    """Dashboard için öneriler oluştur"""
    recommendations = []
    
    # Momentum düşükse
    if momentum.momentum_score < 30:
        recommendations.append({
            "priority": "high",
            "icon": "🔋",
            "title": "Momentum Düşük",
            "message": "Kısa bir mikro-ders ile momentumunu yeniden kazan!",
            "action": "start_micro_lesson"
        })
    
    # Streak riski
    if "streak_at_risk" in momentum.risk_factors:
        recommendations.append({
            "priority": "urgent",
            "icon": "🔥",
            "title": "Streak Tehlikede!",
            "message": f"{momentum.daily_streak} günlük serini kaybetme!",
            "action": "quick_save_streak"
        })
    
    # Yorgunluk yüksekse
    if cognitive_state.fatigue_factor > 1.5:
        recommendations.append({
            "priority": "medium",
            "icon": "😴",
            "title": "Mola Zamanı",
            "message": "Uzun süredir çalışıyorsun. 10 dakika mola verimliliği artırır.",
            "action": "take_break"
        })
    
    # Accuracy düşükse
    accuracy = feedback_stats.get("total_correct", 0) / max(1, feedback_stats.get("total_correct", 0) + feedback_stats.get("total_incorrect", 0))
    if accuracy < 0.6 and feedback_stats.get("total_correct", 0) + feedback_stats.get("total_incorrect", 0) > 10:
        recommendations.append({
            "priority": "medium",
            "icon": "🎯",
            "title": "Doğruluk Geliştirilebilir",
            "message": "Yavaşlayarak ve ipuçlarını kullanarak doğruluğunu artırabilirsin.",
            "action": "slow_practice"
        })
    
    # Flow teşviki
    if attention_profile.total_flow_minutes > 0:
        recommendations.append({
            "priority": "low",
            "icon": "🌊",
            "title": "Flow Master",
            "message": f"Toplam {attention_profile.total_flow_minutes} dk flow! En iyi: {attention_profile.best_flow_streak} dk",
            "action": None
        })
    
    return recommendations[:4]  # Max 4 öneri
