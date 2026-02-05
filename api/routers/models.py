"""
Enterprise AI Assistant - Models Router
========================================

Model yönetimi ve routing endpoints.

Features:
- Model listing
- Model routing info
- Routing metrics
- Feedback metrics

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


# =============================================================================
# MODELS
# =============================================================================

class ModelInfo(BaseModel):
    """Model bilgisi."""
    name: str
    display_name: str
    icon: str
    description: str
    size: str
    tokens_per_second: int


class RoutingMetricsResponse(BaseModel):
    """Routing metrikleri yanıtı."""
    total_requests: int = 0
    rule_based_routes: int = 0
    ai_routes: int = 0
    learned_routes: int = 0
    similarity_routes: int = 0
    default_routes: int = 0
    total_feedbacks: int = 0
    confirmed_feedbacks: int = 0
    cancelled_feedbacks: int = 0
    accuracy_score: float = 0.0


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/available", response_model=List[ModelInfo])
async def get_available_models():
    """Get list of available models."""
    try:
        from core.model_router import MODEL_CONFIG, ModelSize
        
        models = []
        for size, config in MODEL_CONFIG.items():
            models.append(ModelInfo(
                name=config["name"],
                display_name=config["display_name"],
                icon=config["icon"],
                description=config["description"],
                size=size.value,
                tokens_per_second=config["avg_tokens_per_second"],
            ))
        
        return models
        
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/config")
async def get_routing_config():
    """Get model routing configuration."""
    return {
        "small_model": {
            "name": settings.ROUTING_SMALL_MODEL,
            "display_name": settings.ROUTING_SMALL_MODEL_DISPLAY,
            "icon": settings.ROUTING_SMALL_MODEL_ICON,
        },
        "large_model": {
            "name": settings.ROUTING_LARGE_MODEL,
            "display_name": settings.ROUTING_LARGE_MODEL_DISPLAY,
            "icon": settings.ROUTING_LARGE_MODEL_ICON,
        },
        "thresholds": {
            "confidence_high": settings.ROUTING_CONFIDENCE_HIGH,
            "confidence_medium": settings.ROUTING_CONFIDENCE_MEDIUM,
            "confidence_low": settings.ROUTING_CONFIDENCE_LOW,
            "similarity": settings.ROUTING_SIMILARITY_THRESHOLD,
        },
        "learning": {
            "min_feedbacks": settings.ROUTING_MIN_FEEDBACKS_TO_LEARN,
        },
    }


@router.get("/routing/metrics", response_model=RoutingMetricsResponse)
async def get_routing_metrics():
    """Get model routing metrics."""
    try:
        from core.model_router import get_model_router
        
        router = get_model_router()
        metrics = router.get_metrics()
        
        return RoutingMetricsResponse(
            total_requests=metrics.total_requests,
            rule_based_routes=metrics.rule_based_routes,
            ai_routes=metrics.ai_routes,
            learned_routes=metrics.learned_routes,
            similarity_routes=metrics.similarity_routes,
            default_routes=metrics.default_routes,
            total_feedbacks=metrics.total_feedbacks,
            confirmed_feedbacks=metrics.confirmed_feedbacks,
            cancelled_feedbacks=metrics.cancelled_feedbacks,
            accuracy_score=metrics.accuracy_score,
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/learned-patterns")
async def get_learned_patterns():
    """Get learned routing patterns."""
    try:
        from core.model_router import get_model_router
        
        router = get_model_router()
        patterns = router.get_learned_patterns()
        
        return {
            "patterns": [p.to_dict() for p in patterns],
            "count": len(patterns),
        }
        
    except Exception as e:
        logger.error(f"Error getting patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/routing/clear-cache")
async def clear_routing_cache():
    """Clear routing cache."""
    try:
        from services.routing_service import routing_service
        
        cleared = routing_service.clear_cache()
        return {
            "success": True,
            "cleared_entries": cleared,
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/routing/stats")
async def get_routing_service_stats():
    """Get routing service statistics."""
    try:
        from services.routing_service import routing_service
        
        return routing_service.get_stats()
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/status")
async def get_ollama_status():
    """Get Ollama connection status."""
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return {
                    "status": "connected",
                    "base_url": settings.OLLAMA_BASE_URL,
                    "models_count": len(models),
                    "models": [m.get("name") for m in models[:10]],
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {response.status_code}",
                }
                
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e),
        }
