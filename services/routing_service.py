"""
Enterprise AI Assistant - Routing Service
===========================================

Merkezi model yönlendirme servisi.
Model router'ı sararak async wrapper ve cache sağlar.

Features:
- Async routing wrapper
- Timeout management
- Caching
- Metrics collection
- Error handling

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

from core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ROUTING SERVICE
# =============================================================================

class RoutingService:
    """
    Merkezi model yönlendirme servisi.
    
    Model router'ı sararak async operations sağlar.
    """
    
    def __init__(self):
        """Initialize routing service."""
        self._executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="routing_"
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._stats = {
            "total_routes": 0,
            "cache_hits": 0,
            "timeouts": 0,
            "errors": 0,
            "avg_route_time_ms": 0.0,
        }
    
    async def route_async(
        self,
        query: str,
        timeout: Optional[float] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Route query to appropriate model asynchronously.
        
        Args:
            query: User query
            timeout: Routing timeout in seconds
            use_cache: Whether to use caching
            
        Returns:
            RoutingResult dictionary
        """
        start_time = time.time()
        self._stats["total_routes"] += 1
        
        timeout = timeout or settings.WS_MODEL_ROUTING_TIMEOUT
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(query)
            cached = self._get_cached(cache_key)
            if cached:
                self._stats["cache_hits"] += 1
                return cached
        
        try:
            from core.model_router import get_model_router
            
            router = get_model_router()
            
            # Run in executor with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    lambda: router.route(query)
                ),
                timeout=timeout
            )
            
            # Convert to dict
            result_dict = result.to_dict()
            
            # Cache result
            if use_cache:
                self._set_cached(cache_key, result_dict)
            
            # Update stats
            route_time = (time.time() - start_time) * 1000
            total = self._stats["total_routes"]
            avg = self._stats["avg_route_time_ms"]
            self._stats["avg_route_time_ms"] = ((avg * (total - 1)) + route_time) / total
            
            return result_dict
            
        except asyncio.TimeoutError:
            logger.warning(f"Routing timeout after {timeout}s, using default model")
            self._stats["timeouts"] += 1
            return self._get_default_routing(query, "timeout")
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            self._stats["errors"] += 1
            return self._get_default_routing(query, f"error: {e}")
    
    def route_sync(self, query: str) -> Dict[str, Any]:
        """
        Route query synchronously.
        
        Args:
            query: User query
            
        Returns:
            RoutingResult dictionary
        """
        try:
            from core.model_router import get_model_router
            
            router = get_model_router()
            result = router.route(query)
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Sync routing error: {e}")
            return self._get_default_routing(query, f"error: {e}")
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        import hashlib
        normalized = query.lower().strip()[:200]
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached routing result."""
        if key in self._cache:
            cached = self._cache[key]
            if time.time() - cached["cached_at"] < self._cache_ttl:
                return cached["result"]
            else:
                del self._cache[key]
        return None
    
    def _set_cached(self, key: str, result: Dict[str, Any]) -> None:
        """Cache routing result."""
        # Limit cache size
        if len(self._cache) > 1000:
            # Remove oldest entries
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]["cached_at"]
            )
            for old_key in sorted_keys[:100]:
                del self._cache[old_key]
        
        self._cache[key] = {
            "result": result,
            "cached_at": time.time(),
        }
    
    def _get_default_routing(self, query: str, reason: str) -> Dict[str, Any]:
        """Get default routing result."""
        from core.model_router import ModelSize, RoutingDecision, MODEL_CONFIG
        
        model_size = ModelSize.LARGE
        model_config = MODEL_CONFIG[model_size]
        
        import uuid
        import hashlib
        
        return {
            "model_size": model_size.value,
            "model_name": model_config["name"],
            "model_icon": model_config["icon"],
            "model_display_name": model_config["display_name"],
            "confidence": 0.5,
            "decision_source": RoutingDecision.DEFAULT.value,
            "reasoning": f"Default model used: {reason}",
            "response_id": str(uuid.uuid4()),
            "attempt_number": 1,
        }
    
    async def submit_feedback_async(
        self,
        response_id: str,
        feedback_type: str,
        query: str,
    ) -> Dict[str, Any]:
        """
        Submit feedback asynchronously.
        
        Args:
            response_id: Response ID to give feedback for
            feedback_type: Type of feedback (correct/downgrade/upgrade)
            query: Original query
            
        Returns:
            Feedback result
        """
        try:
            from core.model_router import get_model_router, FeedbackType
            
            router = get_model_router()
            
            # Map feedback type
            feedback_type_enum = FeedbackType(feedback_type)
            
            # Run in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                lambda: router.submit_feedback(
                    response_id=response_id,
                    feedback_type=feedback_type_enum,
                    query=query,
                )
            )
            
            return {
                "success": True,
                "feedback_id": result.id if hasattr(result, 'id') else response_id,
                "feedback_type": feedback_type,
            }
            
        except Exception as e:
            logger.error(f"Feedback submission error: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics."""
        try:
            from core.model_router import get_model_router
            router = get_model_router()
            router_metrics = router.get_metrics()
            return {
                **self._stats,
                "router_metrics": router_metrics.to_dict() if hasattr(router_metrics, 'to_dict') else {},
            }
        except Exception as e:
            return {
                **self._stats,
                "router_metrics_error": str(e),
            }
    
    def clear_cache(self) -> int:
        """Clear routing cache."""
        count = len(self._cache)
        self._cache.clear()
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "cache_size": len(self._cache),
        }
    
    def close(self) -> None:
        """Cleanup resources."""
        self._executor.shutdown(wait=False)


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

routing_service = RoutingService()
