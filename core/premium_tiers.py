"""
Enterprise AI Assistant - Premium Tiers System
===============================================

Kurumsal seviye abonelik ve özellik yönetimi.

Tier Levels:
- FREE: Temel özellikler, sınırlı kullanım
- PRO: Gelişmiş özellikler, yüksek limitler
- ENTERPRISE: Tüm özellikler, sınırsız kullanım

Features:
- Rate limiting per tier
- Feature gating
- Usage tracking
- Quota management
- Session-based tier detection
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from functools import wraps
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# TIER DEFINITIONS
# =============================================================================

class PremiumTier(str, Enum):
    """Abonelik seviyeleri."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    
    @property
    def display_name(self) -> str:
        """Görüntüleme adı."""
        names = {
            "free": "Free",
            "pro": "Pro",
            "enterprise": "Enterprise"
        }
        return names.get(self.value, self.value.title())
    
    @property
    def priority(self) -> int:
        """Öncelik sırası (yüksek = daha iyi)."""
        priorities = {"free": 0, "pro": 1, "enterprise": 2}
        return priorities.get(self.value, 0)


@dataclass
class TierLimits:
    """Tier bazlı limitler."""
    # API Limits
    requests_per_minute: int = 20
    requests_per_hour: int = 200
    requests_per_day: int = 1000
    
    # Token Limits
    max_tokens_per_request: int = 4096
    max_tokens_per_day: int = 100000
    
    # Feature Limits
    max_sessions: int = 10
    max_documents: int = 100
    max_file_size_mb: int = 10
    
    # Search Limits
    max_search_results: int = 10
    max_rag_sources: int = 5
    
    # DeepScholar Limits
    max_document_pages: int = 10
    max_research_depth: int = 2
    
    # Advanced Features
    web_search_enabled: bool = False
    voice_enabled: bool = False
    vision_enabled: bool = False
    knowledge_graph_enabled: bool = False
    custom_models_enabled: bool = False
    priority_queue: bool = False


# =============================================================================
# TIER CONFIGURATIONS
# =============================================================================

TIER_LIMITS: Dict[PremiumTier, TierLimits] = {
    PremiumTier.FREE: TierLimits(
        requests_per_minute=20,
        requests_per_hour=200,
        requests_per_day=1000,
        max_tokens_per_request=4096,
        max_tokens_per_day=50000,
        max_sessions=5,
        max_documents=50,
        max_file_size_mb=5,
        max_search_results=5,
        max_rag_sources=3,
        max_document_pages=5,
        max_research_depth=1,
        web_search_enabled=False,
        voice_enabled=False,
        vision_enabled=False,
        knowledge_graph_enabled=False,
        custom_models_enabled=False,
        priority_queue=False
    ),
    PremiumTier.PRO: TierLimits(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000,
        max_tokens_per_request=16384,
        max_tokens_per_day=500000,
        max_sessions=50,
        max_documents=500,
        max_file_size_mb=50,
        max_search_results=20,
        max_rag_sources=10,
        max_document_pages=30,
        max_research_depth=3,
        web_search_enabled=True,
        voice_enabled=True,
        vision_enabled=True,
        knowledge_graph_enabled=True,
        custom_models_enabled=False,
        priority_queue=False
    ),
    PremiumTier.ENTERPRISE: TierLimits(
        requests_per_minute=300,
        requests_per_hour=10000,
        requests_per_day=100000,
        max_tokens_per_request=65536,
        max_tokens_per_day=10000000,
        max_sessions=1000,
        max_documents=10000,
        max_file_size_mb=500,
        max_search_results=100,
        max_rag_sources=50,
        max_document_pages=100,
        max_research_depth=5,
        web_search_enabled=True,
        voice_enabled=True,
        vision_enabled=True,
        knowledge_graph_enabled=True,
        custom_models_enabled=True,
        priority_queue=True
    )
}


# =============================================================================
# FEATURE FLAGS
# =============================================================================

class PremiumFeature(str, Enum):
    """Premium özellikler."""
    WEB_SEARCH = "web_search"
    VOICE_INPUT = "voice_input"
    VOICE_OUTPUT = "voice_output"
    VISION = "vision"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    DEEP_SCHOLAR = "deep_scholar"
    CUSTOM_MODELS = "custom_models"
    PRIORITY_QUEUE = "priority_queue"
    ANALYTICS = "analytics"
    EXPORT_PDF = "export_pdf"
    MULTI_LANGUAGE = "multi_language"
    AUTO_TAGGING = "auto_tagging"
    SEMANTIC_RERANK = "semantic_rerank"
    COMPUTER_USE = "computer_use"
    MCP_TOOLS = "mcp_tools"


FEATURE_TIERS: Dict[PremiumFeature, Set[PremiumTier]] = {
    PremiumFeature.WEB_SEARCH: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.VOICE_INPUT: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.VOICE_OUTPUT: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.VISION: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.KNOWLEDGE_GRAPH: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.DEEP_SCHOLAR: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.CUSTOM_MODELS: {PremiumTier.ENTERPRISE},
    PremiumFeature.PRIORITY_QUEUE: {PremiumTier.ENTERPRISE},
    PremiumFeature.ANALYTICS: {PremiumTier.FREE, PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.EXPORT_PDF: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.MULTI_LANGUAGE: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.AUTO_TAGGING: {PremiumTier.FREE, PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.SEMANTIC_RERANK: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
    PremiumFeature.COMPUTER_USE: {PremiumTier.ENTERPRISE},
    PremiumFeature.MCP_TOOLS: {PremiumTier.PRO, PremiumTier.ENTERPRISE},
}


# =============================================================================
# USAGE TRACKING
# =============================================================================

@dataclass
class UsageStats:
    """Kullanım istatistikleri."""
    tier: PremiumTier = PremiumTier.FREE
    
    # Request counts
    requests_today: int = 0
    requests_this_hour: int = 0
    requests_this_minute: int = 0
    
    # Token usage
    tokens_today: int = 0
    tokens_this_session: int = 0
    
    # Resource usage
    sessions_count: int = 0
    documents_count: int = 0
    storage_used_mb: float = 0.0
    
    # Timestamps
    last_request: Optional[datetime] = None
    quota_reset_at: Optional[datetime] = None
    
    # Feature usage counts
    feature_usage: Dict[str, int] = field(default_factory=dict)


class UsageTracker:
    """
    Kullanım takibi ve kota yönetimi.
    
    Thread-safe kullanım istatistikleri.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self._users: Dict[str, UsageStats] = {}
        self._data_dir = data_dir or Path("data/usage")
        self._data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self, user_id: str) -> UsageStats:
        """Kullanıcı istatistiklerini al."""
        if user_id not in self._users:
            self._users[user_id] = self._load_stats(user_id)
        return self._users[user_id]
    
    def _load_stats(self, user_id: str) -> UsageStats:
        """Disk'ten istatistik yükle."""
        filepath = self._data_dir / f"{user_id}.json"
        if filepath.exists():
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    return UsageStats(**data)
            except Exception as e:
                logger.warning(f"Failed to load usage stats: {e}")
        return UsageStats()
    
    def _save_stats(self, user_id: str, stats: UsageStats):
        """İstatistikleri disk'e kaydet."""
        try:
            filepath = self._data_dir / f"{user_id}.json"
            with open(filepath, 'w') as f:
                data = {
                    "tier": stats.tier.value,
                    "requests_today": stats.requests_today,
                    "tokens_today": stats.tokens_today,
                    "sessions_count": stats.sessions_count,
                    "documents_count": stats.documents_count,
                    "feature_usage": stats.feature_usage
                }
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save usage stats: {e}")
    
    def record_request(self, user_id: str, tokens_used: int = 0):
        """İstek kaydet."""
        stats = self.get_stats(user_id)
        now = datetime.now()
        
        # Reset counters if needed
        if stats.quota_reset_at and now > stats.quota_reset_at:
            stats.requests_today = 0
            stats.tokens_today = 0
            stats.quota_reset_at = now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        
        stats.requests_today += 1
        stats.requests_this_hour += 1
        stats.requests_this_minute += 1
        stats.tokens_today += tokens_used
        stats.last_request = now
        
        self._save_stats(user_id, stats)
    
    def record_feature_use(self, user_id: str, feature: PremiumFeature):
        """Özellik kullanımı kaydet."""
        stats = self.get_stats(user_id)
        feature_name = feature.value
        stats.feature_usage[feature_name] = stats.feature_usage.get(feature_name, 0) + 1
        self._save_stats(user_id, stats)
    
    def check_quota(self, user_id: str) -> Dict[str, Any]:
        """Kota kontrolü yap."""
        stats = self.get_stats(user_id)
        limits = TIER_LIMITS.get(stats.tier, TIER_LIMITS[PremiumTier.FREE])
        
        return {
            "within_limits": stats.requests_today < limits.requests_per_day,
            "requests_remaining": max(0, limits.requests_per_day - stats.requests_today),
            "tokens_remaining": max(0, limits.max_tokens_per_day - stats.tokens_today),
            "tier": stats.tier.value,
            "limits": {
                "requests_per_day": limits.requests_per_day,
                "tokens_per_day": limits.max_tokens_per_day
            }
        }


# =============================================================================
# TIER MANAGER
# =============================================================================

class PremiumTierManager:
    """
    Premium tier ve özellik yönetimi.
    
    Singleton pattern ile tek instance.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._user_tiers: Dict[str, PremiumTier] = {}
        self._usage_tracker = UsageTracker()
        self._initialized = True
        logger.info("PremiumTierManager initialized")
    
    def get_tier(self, user_id: str) -> PremiumTier:
        """Kullanıcının tier'ını al."""
        return self._user_tiers.get(user_id, PremiumTier.FREE)
    
    def set_tier(self, user_id: str, tier: PremiumTier):
        """Kullanıcının tier'ını ayarla."""
        self._user_tiers[user_id] = tier
        stats = self._usage_tracker.get_stats(user_id)
        stats.tier = tier
        logger.info(f"User {user_id} tier set to {tier.value}")
    
    def get_limits(self, user_id: str) -> TierLimits:
        """Kullanıcının limitlerini al."""
        tier = self.get_tier(user_id)
        return TIER_LIMITS.get(tier, TIER_LIMITS[PremiumTier.FREE])
    
    def has_feature(self, user_id: str, feature: PremiumFeature) -> bool:
        """Kullanıcının özelliğe erişimi var mı?"""
        tier = self.get_tier(user_id)
        allowed_tiers = FEATURE_TIERS.get(feature, set())
        return tier in allowed_tiers
    
    def check_limit(self, user_id: str, limit_name: str, current_value: int) -> bool:
        """Limit aşılmış mı kontrol et."""
        limits = self.get_limits(user_id)
        max_value = getattr(limits, limit_name, None)
        if max_value is None:
            return True  # Limit tanımlı değilse izin ver
        return current_value < max_value
    
    def get_usage(self, user_id: str) -> Dict[str, Any]:
        """Kullanım istatistiklerini al."""
        stats = self._usage_tracker.get_stats(user_id)
        limits = self.get_limits(user_id)
        
        return {
            "tier": stats.tier.value,
            "tier_display": stats.tier.display_name if hasattr(stats.tier, 'display_name') else stats.tier.value.title(),
            "usage": {
                "requests_today": stats.requests_today,
                "tokens_today": stats.tokens_today,
                "sessions": stats.sessions_count,
                "documents": stats.documents_count
            },
            "limits": {
                "requests_per_day": limits.requests_per_day,
                "tokens_per_day": limits.max_tokens_per_day,
                "max_sessions": limits.max_sessions,
                "max_documents": limits.max_documents
            },
            "features": {
                feature.value: self.has_feature(user_id, feature)
                for feature in PremiumFeature
            }
        }
    
    def record_usage(self, user_id: str, tokens: int = 0, feature: Optional[PremiumFeature] = None):
        """Kullanım kaydet."""
        self._usage_tracker.record_request(user_id, tokens)
        if feature:
            self._usage_tracker.record_feature_use(user_id, feature)


# =============================================================================
# DECORATORS
# =============================================================================

def require_tier(min_tier: PremiumTier):
    """
    Minimum tier gerektiren endpoint decorator.
    
    Usage:
        @require_tier(PremiumTier.PRO)
        async def pro_only_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user_id from request context
            user_id = kwargs.get('user_id', 'anonymous')
            manager = get_tier_manager()
            user_tier = manager.get_tier(user_id)
            
            if user_tier.priority < min_tier.priority:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "tier_required",
                        "message": f"This feature requires {min_tier.display_name} tier",
                        "current_tier": user_tier.value,
                        "required_tier": min_tier.value
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_feature(feature: PremiumFeature):
    """
    Özellik gerektiren endpoint decorator.
    
    Usage:
        @require_feature(PremiumFeature.WEB_SEARCH)
        async def web_search_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id', 'anonymous')
            manager = get_tier_manager()
            
            if not manager.has_feature(user_id, feature):
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_not_available",
                        "message": f"Feature '{feature.value}' is not available in your plan",
                        "feature": feature.value,
                        "upgrade_to": "pro"  # Suggest upgrade
                    }
                )
            
            # Record feature usage
            manager.record_usage(user_id, feature=feature)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# SINGLETON ACCESS
# =============================================================================

_tier_manager: Optional[PremiumTierManager] = None


def get_tier_manager() -> PremiumTierManager:
    """Tier manager singleton'ını al."""
    global _tier_manager
    if _tier_manager is None:
        _tier_manager = PremiumTierManager()
    return _tier_manager


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_premium_user(user_id: str) -> bool:
    """Kullanıcı premium mu?"""
    manager = get_tier_manager()
    return manager.get_tier(user_id) != PremiumTier.FREE


def get_feature_tier(feature: PremiumFeature) -> str:
    """Özelliğin minimum tier'ını al."""
    tiers = FEATURE_TIERS.get(feature, set())
    if not tiers:
        return "enterprise"
    
    for tier in [PremiumTier.FREE, PremiumTier.PRO, PremiumTier.ENTERPRISE]:
        if tier in tiers:
            return tier.value
    return "enterprise"


def get_all_features_for_tier(tier: PremiumTier) -> List[str]:
    """Tier için tüm özellikleri listele."""
    return [
        feature.value
        for feature, allowed_tiers in FEATURE_TIERS.items()
        if tier in allowed_tiers
    ]
