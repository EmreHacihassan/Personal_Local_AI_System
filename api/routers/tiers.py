"""
Premium Tiers API Router
========================

Kullanıcı tier yönetimi ve kota endpoint'leri.

Features:
- Tier bilgisi sorgulama
- Kota kontrolü
- Özellik listesi
- Kullanım istatistikleri
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from core.premium_tiers import (
    PremiumTier,
    PremiumFeature,
    TierLimits,
    TIER_LIMITS,
    FEATURE_TIERS,
    get_tier_manager,
    get_all_features_for_tier,
    get_feature_tier
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tiers", tags=["Premium Tiers"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TierInfoResponse(BaseModel):
    """Tier bilgi yanıtı."""
    tier: str
    tier_display: str
    priority: int
    limits: Dict[str, Any]
    features: Dict[str, bool]


class UsageResponse(BaseModel):
    """Kullanım yanıtı."""
    tier: str
    usage: Dict[str, int]
    limits: Dict[str, int]
    quota_status: Dict[str, Any]


class SetTierRequest(BaseModel):
    """Tier değiştirme isteği."""
    user_id: str = Field(..., description="Kullanıcı ID")
    tier: str = Field(..., description="Yeni tier: free, pro, enterprise")


class FeatureCheckResponse(BaseModel):
    """Özellik kontrolü yanıtı."""
    feature: str
    available: bool
    minimum_tier: str
    current_tier: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", summary="Tüm tier'ları listele")
async def list_tiers():
    """
    Mevcut tüm tier'ları ve özelliklerini listele.
    
    Returns:
        Tier listesi ve detayları
    """
    tiers = []
    for tier in PremiumTier:
        limits = TIER_LIMITS.get(tier, TierLimits())
        features = get_all_features_for_tier(tier)
        
        tiers.append({
            "id": tier.value,
            "name": tier.display_name,
            "priority": tier.priority,
            "limits": {
                "requests_per_day": limits.requests_per_day,
                "tokens_per_day": limits.max_tokens_per_day,
                "max_sessions": limits.max_sessions,
                "max_documents": limits.max_documents,
                "max_file_size_mb": limits.max_file_size_mb,
                "max_document_pages": limits.max_document_pages
            },
            "features": features,
            "feature_count": len(features)
        })
    
    return {
        "success": True,
        "tiers": tiers,
        "total": len(tiers),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/features", summary="Tüm özellikleri listele")
async def list_features():
    """
    Mevcut tüm premium özellikleri listele.
    
    Returns:
        Özellik listesi ve tier gereksinimleri
    """
    features = []
    for feature in PremiumFeature:
        min_tier = get_feature_tier(feature)
        allowed_tiers = FEATURE_TIERS.get(feature, set())
        
        features.append({
            "id": feature.value,
            "name": feature.value.replace("_", " ").title(),
            "minimum_tier": min_tier,
            "available_in": [t.value for t in allowed_tiers]
        })
    
    return {
        "success": True,
        "features": features,
        "total": len(features),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/user/{user_id}", summary="Kullanıcı tier bilgisi")
async def get_user_tier(user_id: str):
    """
    Kullanıcının tier bilgilerini al.
    
    Args:
        user_id: Kullanıcı kimliği
        
    Returns:
        Tier bilgisi, limitler ve özellikler
    """
    manager = get_tier_manager()
    usage = manager.get_usage(user_id)
    tier = manager.get_tier(user_id)
    
    return {
        "success": True,
        "user_id": user_id,
        "tier": usage,
        "is_premium": tier != PremiumTier.FREE,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/user/{user_id}/usage", summary="Kullanım istatistikleri")
async def get_user_usage(user_id: str):
    """
    Kullanıcının kullanım istatistiklerini al.
    
    Args:
        user_id: Kullanıcı kimliği
        
    Returns:
        Detaylı kullanım istatistikleri
    """
    manager = get_tier_manager()
    usage = manager.get_usage(user_id)
    
    # Calculate percentages
    limits = usage.get("limits", {})
    current = usage.get("usage", {})
    
    percentages = {}
    for key in ["requests_per_day", "tokens_per_day"]:
        limit = limits.get(key, 1)
        usage_key = key.replace("_per_day", "_today")
        current_val = current.get(usage_key, 0)
        percentages[key] = round((current_val / limit) * 100, 1) if limit > 0 else 0
    
    return {
        "success": True,
        "user_id": user_id,
        "usage": current,
        "limits": limits,
        "percentages": percentages,
        "features": usage.get("features", {}),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/user/{user_id}/check-feature/{feature}", summary="Özellik kontrolü")
async def check_feature_access(user_id: str, feature: str):
    """
    Kullanıcının belirli bir özelliğe erişimi var mı?
    
    Args:
        user_id: Kullanıcı kimliği
        feature: Özellik adı
        
    Returns:
        Erişim durumu ve gereksinimler
    """
    manager = get_tier_manager()
    
    # Find feature enum
    try:
        feature_enum = PremiumFeature(feature)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown feature: {feature}. Available: {[f.value for f in PremiumFeature]}"
        )
    
    has_access = manager.has_feature(user_id, feature_enum)
    current_tier = manager.get_tier(user_id)
    min_tier = get_feature_tier(feature_enum)
    
    return {
        "success": True,
        "user_id": user_id,
        "feature": feature,
        "has_access": has_access,
        "current_tier": current_tier.value,
        "minimum_tier": min_tier,
        "upgrade_required": not has_access,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/user/{user_id}/set-tier", summary="Tier ayarla (Admin)")
async def set_user_tier(user_id: str, request: SetTierRequest):
    """
    Kullanıcının tier'ını ayarla.
    
    NOT: Bu endpoint admin yetkisi gerektirir.
    
    Args:
        user_id: Kullanıcı kimliği
        request: Yeni tier bilgisi
    """
    # Validate tier
    try:
        new_tier = PremiumTier(request.tier)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {request.tier}. Available: {[t.value for t in PremiumTier]}"
        )
    
    manager = get_tier_manager()
    old_tier = manager.get_tier(user_id)
    manager.set_tier(user_id, new_tier)
    
    logger.info(f"User {user_id} tier changed: {old_tier.value} -> {new_tier.value}")
    
    return {
        "success": True,
        "user_id": user_id,
        "old_tier": old_tier.value,
        "new_tier": new_tier.value,
        "message": f"Tier updated to {new_tier.display_name}",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/compare", summary="Tier karşılaştırması")
async def compare_tiers(
    tier1: str = Query(..., description="İlk tier"),
    tier2: str = Query(..., description="İkinci tier")
):
    """
    İki tier'ı karşılaştır.
    
    Args:
        tier1: İlk tier
        tier2: İkinci tier
        
    Returns:
        Karşılaştırma detayları
    """
    try:
        t1 = PremiumTier(tier1)
        t2 = PremiumTier(tier2)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    limits1 = TIER_LIMITS.get(t1, TierLimits())
    limits2 = TIER_LIMITS.get(t2, TierLimits())
    
    features1 = set(get_all_features_for_tier(t1))
    features2 = set(get_all_features_for_tier(t2))
    
    comparison = {
        "limits": {},
        "features": {
            "only_in_tier1": list(features1 - features2),
            "only_in_tier2": list(features2 - features1),
            "shared": list(features1 & features2)
        }
    }
    
    # Compare limits
    for attr in ["requests_per_day", "max_tokens_per_day", "max_sessions", "max_documents"]:
        val1 = getattr(limits1, attr if "tokens" not in attr else "max_tokens_per_day", 0)
        val2 = getattr(limits2, attr if "tokens" not in attr else "max_tokens_per_day", 0)
        comparison["limits"][attr] = {
            tier1: val1,
            tier2: val2,
            "difference": val2 - val1
        }
    
    return {
        "success": True,
        "tier1": {"id": t1.value, "name": t1.display_name},
        "tier2": {"id": t2.value, "name": t2.display_name},
        "comparison": comparison,
        "recommendation": t2.value if t2.priority > t1.priority else t1.value,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/pricing", summary="Fiyatlandırma bilgisi")
async def get_pricing():
    """
    Tier fiyatlandırma bilgisi.
    
    NOT: Bu örnek fiyatlar, gerçek fiyatlandırma için konfigüre edilmeli.
    """
    pricing = {
        "free": {
            "name": "Free",
            "price_monthly": 0,
            "price_yearly": 0,
            "currency": "USD",
            "highlights": [
                "Temel sohbet özellikleri",
                "5 session limiti",
                "50 döküman limiti",
                "Günlük 1000 istek"
            ]
        },
        "pro": {
            "name": "Pro",
            "price_monthly": 19.99,
            "price_yearly": 199.99,
            "currency": "USD",
            "highlights": [
                "Web arama",
                "Ses girdi/çıktı",
                "Görsel analiz",
                "Knowledge Graph",
                "DeepScholar (30 sayfa)",
                "Günlük 10000 istek"
            ]
        },
        "enterprise": {
            "name": "Enterprise",
            "price_monthly": 99.99,
            "price_yearly": 999.99,
            "currency": "USD",
            "highlights": [
                "Tüm Pro özellikler",
                "Computer Use Agent",
                "Özel model desteği",
                "Öncelikli kuyruk",
                "DeepScholar (100 sayfa)",
                "Günlük 100000 istek",
                "Premium destek"
            ]
        }
    }
    
    return {
        "success": True,
        "pricing": pricing,
        "currency": "USD",
        "note": "Yıllık ödemede 2 ay ücretsiz",
        "timestamp": datetime.now().isoformat()
    }
