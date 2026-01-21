"""
Model Routing API Endpoints
============================

Human-in-the-Loop Model Routing ve Feedback API'leri.

Endpoints:
    POST /api/routing/route       - Sorgu için model routing
    POST /api/routing/feedback    - Feedback gönder
    POST /api/routing/compare     - Karşılaştırma iste  
    POST /api/routing/confirm     - Feedback'i onayla/iptal et
    GET  /api/routing/stats       - Router istatistikleri
    GET  /api/routing/patterns    - Öğrenilmiş pattern'lar
    GET  /api/routing/history     - Routing geçmişi
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.model_router import (
    ModelRouter,
    ModelSize,
    RoutingResult,
    FeedbackType,
    FeedbackStatus,
    Feedback,
    MODEL_CONFIG,
    get_model_router,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["Model Routing"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RouteRequest(BaseModel):
    """Routing isteği."""
    query: str = Field(..., min_length=1, max_length=5000, description="Kullanıcı sorgusu")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Python'da decorator nasıl çalışır?"
            }
        }


class RouteResponse(BaseModel):
    """Routing yanıtı."""
    success: bool = True
    routing: Dict[str, Any] = Field(..., description="Routing bilgisi")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "routing": {
                    "model_size": "large",
                    "model_name": "qwen3-vl:8b",
                    "model_icon": "🔵",
                    "model_display_name": "Qwen 8B",
                    "confidence": 0.85,
                    "decision_source": "ai_router",
                    "reasoning": "Educational content requiring detailed explanation",
                    "response_id": "abc123",
                    "attempt_number": 1
                }
            }
        }


class FeedbackRequest(BaseModel):
    """Feedback isteği."""
    response_id: str = Field(..., description="Yanıt ID'si")
    feedback_type: str = Field(
        ..., 
        description="Feedback tipi: 'correct', 'downgrade', 'upgrade'"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response_id": "abc123",
                "feedback_type": "downgrade"  # "Küçük model yeterliydi"
            }
        }


class FeedbackResponse(BaseModel):
    """Feedback yanıtı."""
    success: bool = True
    feedback: Dict[str, Any] = Field(..., description="Feedback bilgisi")
    message: str = Field(..., description="Durum mesajı")
    requires_comparison: bool = Field(False, description="Karşılaştırma gerekiyor mu?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "feedback": {
                    "id": "feedback123",
                    "response_id": "abc123",
                    "feedback_type": "downgrade",
                    "status": "pending"
                },
                "message": "Feedback alındı. Karşılaştırma için 'Dene' butonunu kullanabilirsiniz.",
                "requires_comparison": True
            }
        }


class CompareRequest(BaseModel):
    """Karşılaştırma isteği."""
    feedback_id: str = Field(..., description="Feedback ID'si")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback_id": "feedback123"
            }
        }


class CompareResponse(BaseModel):
    """Karşılaştırma yanıtı."""
    success: bool = True
    query: str = Field(..., description="Sorgu")
    comparison_routing: Dict[str, Any] = Field(..., description="Karşılaştırma için routing")
    message: str = Field(..., description="Durum mesajı")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "query": "Python'da decorator nasıl çalışır?",
                "comparison_routing": {
                    "model_size": "small",
                    "model_name": "qwen3:4b",
                    "response_id": "compare123",
                    "attempt_number": 2
                },
                "message": "Küçük model ile yanıt hazırlanıyor..."
            }
        }


class ConfirmRequest(BaseModel):
    """Onay isteği."""
    feedback_id: str = Field(..., description="Feedback ID'si")
    confirmed: bool = Field(
        ..., 
        description="True = Feedback doğruydu, False = İlk model doğruydu"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback_id": "feedback123",
                "confirmed": True  # "Evet, küçük model yeterliymiş"
            }
        }


class ConfirmResponse(BaseModel):
    """Onay yanıtı."""
    success: bool = True
    feedback: Dict[str, Any] = Field(..., description="Güncel feedback bilgisi")
    message: str = Field(..., description="Durum mesajı")
    learning_applied: bool = Field(False, description="Öğrenme uygulandı mı?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "feedback": {
                    "id": "feedback123",
                    "status": "confirmed",
                    "final_decision": "small"
                },
                "message": "Tercih kaydedildi! Benzer sorgular için küçük model kullanılacak.",
                "learning_applied": True
            }
        }


class StatsResponse(BaseModel):
    """İstatistik yanıtı."""
    success: bool = True
    stats: Dict[str, Any] = Field(..., description="Router istatistikleri")


class PatternsResponse(BaseModel):
    """Pattern listesi yanıtı."""
    success: bool = True
    patterns: List[Dict[str, Any]] = Field(..., description="Öğrenilmiş pattern'lar")
    count: int = Field(..., description="Toplam pattern sayısı")


class HistoryResponse(BaseModel):
    """Geçmiş yanıtı."""
    success: bool = True
    history: List[Dict[str, Any]] = Field(..., description="Routing geçmişi")
    count: int = Field(..., description="Toplam kayıt sayısı")


class ModelsResponse(BaseModel):
    """Model listesi yanıtı."""
    success: bool = True
    models: Dict[str, Any] = Field(..., description="Mevcut modeller")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/route", response_model=RouteResponse)
async def route_query(request: RouteRequest) -> RouteResponse:
    """
    Sorgu için en uygun modeli belirle.
    
    Bu endpoint:
    1. Rule-based pattern matching yapar
    2. Öğrenilmiş pattern'lara bakar
    3. Gerekirse AI router (4B model) kullanır
    4. Routing kararını ve bilgilerini döner
    """
    try:
        model_router = get_model_router()
        result = await model_router.route_async(request.query)
        
        return RouteResponse(
            success=True,
            routing=result.to_dict()
        )
    except Exception as e:
        logger.error(f"Routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Kullanıcı feedback'i gönder.
    
    Feedback tipleri:
    - correct: Model seçimi doğruydu
    - downgrade: Büyük model kullanıldı ama küçük yeterliydi
    - upgrade: Küçük model kullanıldı ama büyük lazımdı
    
    Correct feedback doğrudan kaydedilir.
    Downgrade/upgrade için karşılaştırma önerilir.
    """
    try:
        # Validate feedback type
        try:
            feedback_type = FeedbackType(request.feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid feedback type. Use: {[t.value for t in FeedbackType]}"
            )
        
        # Determine suggested model
        suggested_model = None
        if feedback_type == FeedbackType.DOWNGRADE:
            suggested_model = ModelSize.SMALL
        elif feedback_type == FeedbackType.UPGRADE:
            suggested_model = ModelSize.LARGE
        
        model_router = get_model_router()
        feedback = model_router.submit_feedback(
            response_id=request.response_id,
            feedback_type=feedback_type,
            suggested_model=suggested_model,
        )
        
        # Determine message
        if feedback_type == FeedbackType.CORRECT:
            message = "Teşekkürler! Tercih kaydedildi."
            requires_comparison = False
        elif feedback_type == FeedbackType.DOWNGRADE:
            message = "Küçük modeli denemek ister misiniz? 'Dene' butonunu kullanın."
            requires_comparison = True
        else:
            message = "Büyük modeli denemek ister misiniz? 'Dene' butonunu kullanın."
            requires_comparison = True
        
        return FeedbackResponse(
            success=True,
            feedback=feedback.to_dict(),
            message=message,
            requires_comparison=requires_comparison,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare", response_model=CompareResponse)
async def request_comparison(request: CompareRequest) -> CompareResponse:
    """
    Karşılaştırma için diğer modeli dene.
    
    Bu endpoint:
    1. Pending feedback'i bulur
    2. Alternatif model için routing oluşturur
    3. Sorguyu ve yeni routing'i döner
    
    Frontend bu bilgiyle alternatif modelden yanıt alabilir.
    """
    try:
        model_router = get_model_router()
        query, comparison_result = model_router.request_comparison(request.feedback_id)
        
        model_name = MODEL_CONFIG[comparison_result.model_size]["display_name"]
        message = f"{model_name} ile yanıt hazırlanıyor..."
        
        return CompareResponse(
            success=True,
            query=query,
            comparison_routing=comparison_result.to_dict(),
            message=message,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_feedback(request: ConfirmRequest) -> ConfirmResponse:
    """
    Karşılaştırma sonrası feedback'i onayla veya iptal et.
    
    Args:
        confirmed: True = Feedback doğruydu (yeni model tercih edildi)
                   False = İlk model doğruydu (feedback iptal)
    
    Onaylanan feedback'ler öğrenme için kullanılır.
    """
    try:
        model_router = get_model_router()
        feedback = model_router.confirm_feedback(
            feedback_id=request.feedback_id,
            confirmed=request.confirmed,
        )
        
        if request.confirmed:
            model_name = MODEL_CONFIG[feedback.final_decision]["display_name"]
            message = f"Tercih kaydedildi! Benzer sorgular için {model_name} kullanılacak."
            learning_applied = True
        else:
            message = "İlk tercih korundu. Teşekkürler!"
            learning_applied = False
        
        return ConfirmResponse(
            success=True,
            feedback=feedback.to_dict(),
            message=message,
            learning_applied=learning_applied,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """
    Router istatistiklerini al.
    
    Dönen bilgiler:
    - Toplam istek sayısı
    - Routing kaynağı dağılımı
    - Feedback istatistikleri
    - Öğrenilmiş pattern sayısı
    - Ortalama routing süresi
    - Doğruluk skoru
    """
    try:
        model_router = get_model_router()
        stats = model_router.get_stats()
        
        return StatsResponse(
            success=True,
            stats=stats
        )
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns(
    target_model: Optional[str] = Query(None, description="Filter by model: 'small' or 'large'")
) -> PatternsResponse:
    """
    Öğrenilmiş pattern'ları listele.
    
    Bu pattern'lar kullanıcı feedback'lerinden öğrenilmiştir.
    """
    try:
        model_router = get_model_router()
        patterns = model_router.storage.get_all_patterns()
        
        # Filter if specified
        if target_model:
            try:
                model_size = ModelSize(target_model)
                patterns = [p for p in patterns if p.target_model == model_size]
            except ValueError:
                pass
        
        return PatternsResponse(
            success=True,
            patterns=[p.to_dict() for p in patterns],
            count=len(patterns),
        )
        
    except Exception as e:
        logger.error(f"Patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_routing_history(
    limit: int = Query(50, ge=1, le=200, description="Maksimum kayıt sayısı"),
    offset: int = Query(0, ge=0, description="Başlangıç offset'i"),
) -> HistoryResponse:
    """
    Routing geçmişini al.
    
    Son routing kararlarını ve feedback'leri gösterir.
    """
    try:
        model_router = get_model_router()
        
        # Get recent feedbacks
        feedbacks = model_router.storage.get_confirmed_feedbacks(limit=limit)
        
        history = [
            {
                **f.to_dict(),
                "model_icon": MODEL_CONFIG.get(f.final_decision, {}).get("icon", "❓") if f.final_decision else "❓",
            }
            for f in feedbacks
        ]
        
        return HistoryResponse(
            success=True,
            history=history,
            count=len(history),
        )
        
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=ModelsResponse)
async def get_models() -> ModelsResponse:
    """
    Mevcut modelleri listele.
    
    Her model için ad, ikon, açıklama ve hız bilgisi döner.
    """
    try:
        model_router = get_model_router()
        
        models = {}
        for size, config in MODEL_CONFIG.items():
            models[size.value] = {
                **config,
                "available": True,  # Could check actual availability
            }
        
        # Check AI router availability
        ai_router_available = model_router.ai_router.is_available() if model_router.ai_router else False
        
        return ModelsResponse(
            success=True,
            models={
                "available_models": models,
                "router_model": {
                    "name": "qwen3:4b",
                    "available": ai_router_available,
                    "description": "Routing kararları için kullanılan 4B model"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-patterns")
async def refresh_patterns() -> Dict[str, Any]:
    """
    Pattern cache'ini yenile.
    
    Yeni öğrenilen pattern'ları aktif hale getirir.
    """
    try:
        model_router = get_model_router()
        model_router.refresh_patterns()
        
        return {
            "success": True,
            "message": "Pattern cache yenilendi"
        }
        
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ROUTER REGISTRATION
# =============================================================================

def get_router() -> APIRouter:
    """Router instance'ını döndür."""
    return router
