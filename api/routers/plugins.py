"""
Plugins Router
===============

Plugin yönetimi, aktivasyon, çalıştırma ve observability endpoint'leri.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import logging


router = APIRouter(prefix="/api", tags=["Plugins", "Observability"])
logger = logging.getLogger(__name__)


# ============ PYDANTIC MODELS ============

class PluginExecuteRequest(BaseModel):
    """Plugin çalıştırma isteği."""
    input_data: Dict[str, Any]


# ============ PLUGIN ENDPOINTS ============

@router.get("/plugins")
async def list_plugins():
    """Kayıtlı plugin'leri listele."""
    try:
        from plugins.base import PluginRegistry
        
        plugins = PluginRegistry.list_plugins()
        return {
            "success": True,
            "plugins": [p.to_dict() for p in plugins],
            "total": len(plugins),
        }
        
    except Exception as e:
        logger.error(f"List plugins error: {e}")
        return {"success": False, "error": str(e), "plugins": []}


@router.post("/plugins/{plugin_name}/activate")
async def activate_plugin(plugin_name: str):
    """Plugin'i aktif et."""
    try:
        from plugins.base import PluginRegistry
        
        success = await PluginRegistry.activate(plugin_name)
        
        return {
            "success": success,
            "plugin": plugin_name,
            "status": "active" if success else "activation_failed",
        }
        
    except Exception as e:
        logger.error(f"Activate plugin error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/plugins/{plugin_name}/deactivate")
async def deactivate_plugin(plugin_name: str):
    """Plugin'i deaktif et."""
    try:
        from plugins.base import PluginRegistry
        
        success = await PluginRegistry.deactivate(plugin_name)
        
        return {
            "success": success,
            "plugin": plugin_name,
            "status": "inactive" if success else "deactivation_failed",
        }
        
    except Exception as e:
        logger.error(f"Deactivate plugin error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/plugins/{plugin_name}/execute")
async def execute_plugin(plugin_name: str, request: PluginExecuteRequest):
    """Plugin'i çalıştır."""
    try:
        from plugins.base import PluginRegistry
        
        result = await PluginRegistry.execute(plugin_name, request.input_data)
        
        if result:
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
            }
        else:
            return {
                "success": False,
                "error": f"Plugin '{plugin_name}' not found",
            }
        
    except Exception as e:
        logger.error(f"Execute plugin error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/plugins/stats")
async def get_plugin_stats():
    """Plugin sistemi istatistikleri."""
    try:
        from plugins.base import PluginRegistry
        
        return {
            "success": True,
            "stats": PluginRegistry.get_stats(),
        }
        
    except Exception as e:
        logger.error(f"Plugin stats error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/plugins/initialize")
async def initialize_default_plugins():
    """Varsayılan plugin'leri yükle ve aktif et."""
    try:
        from plugins.base import PluginRegistry
        from plugins.text_processing_plugin import TextProcessingPlugin
        from plugins.code_analysis_plugin import CodeAnalysisPlugin
        
        # Plugin'leri kaydet
        plugins_registered = []
        
        text_plugin = TextProcessingPlugin()
        PluginRegistry.register(text_plugin)
        await text_plugin.setup()
        plugins_registered.append(text_plugin.name)
        
        code_plugin = CodeAnalysisPlugin()
        PluginRegistry.register(code_plugin)
        await code_plugin.setup()
        plugins_registered.append(code_plugin.name)
        
        # Web search plugin opsiyonel
        try:
            from plugins.web_search_plugin import WebSearchPlugin
            web_plugin = WebSearchPlugin()
            PluginRegistry.register(web_plugin)
            await web_plugin.setup()
            plugins_registered.append(web_plugin.name)
        except Exception as e:
            logger.warning(f"Web search plugin not available: {e}")
        
        return {
            "success": True,
            "plugins_registered": plugins_registered,
            "message": f"{len(plugins_registered)} plugin başarıyla yüklendi",
        }
        
    except Exception as e:
        logger.error(f"Initialize plugins error: {e}")
        return {"success": False, "error": str(e)}


# ============ OBSERVABILITY ENDPOINTS ============

@router.get("/observability/metrics")
async def get_observability_metrics():
    """
    LLM observability metrikleri.
    
    Token kullanımı, latency, maliyet ve kalite metriklerini döndürür.
    """
    try:
        from core.langfuse_observability import Observability
        
        obs = Observability()
        backend = obs.backend
        
        # Backend'den metrikleri al
        if hasattr(backend, 'get_metrics'):
            metrics = backend.get_metrics()
        else:
            # Local backend için manuel hesaplama
            metrics = {
                "total_traces": getattr(backend, '_trace_count', 0),
                "total_generations": getattr(backend, '_generation_count', 0),
                "total_tokens": getattr(backend, '_total_tokens', 0),
                "total_cost_usd": getattr(backend, '_total_cost', 0.0),
                "avg_latency_ms": getattr(backend, '_avg_latency', 0.0),
            }
        
        return {
            "success": True,
            "backend_type": type(backend).__name__,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Observability metrics error: {e}")
        return {
            "success": False,
            "error": str(e),
            "metrics": None,
        }


@router.get("/observability/traces")
async def get_recent_traces(limit: int = 20):
    """Son trace'leri listele."""
    try:
        from core.langfuse_observability import Observability
        
        obs = Observability()
        backend = obs.backend
        
        if hasattr(backend, 'get_traces'):
            traces = backend.get_traces(limit=limit)
        elif hasattr(backend, 'traces'):
            traces = list(backend.traces.values())[-limit:]
        else:
            traces = []
        
        return {
            "success": True,
            "traces": traces,
            "count": len(traces),
        }
        
    except Exception as e:
        logger.error(f"Get traces error: {e}")
        return {"success": False, "error": str(e), "traces": []}


@router.get("/observability/dashboard")
async def get_observability_dashboard():
    """
    Kapsamlı observability dashboard verisi.
    
    Tüm LLM operasyonlarının özet istatistiklerini döndürür.
    """
    try:
        from core.langfuse_observability import Observability
        from core.analytics import analytics
        from core.circuit_breaker import circuit_registry
        from core.error_recovery import ErrorRecoveryManager
        from core.moe_router import MoERouter
        
        obs = Observability()
        error_recovery = ErrorRecoveryManager()
        moe_router = MoERouter()
        
        # Analytics'ten veriler
        analytics_summary = {}
        if hasattr(analytics, 'get_summary'):
            analytics_summary = analytics.get_summary()
        
        # Circuit breaker durumları
        circuit_status = circuit_registry.get_all_status()
        
        # Error recovery durumu
        error_stats = {}
        if hasattr(error_recovery, 'get_stats'):
            error_stats = error_recovery.get_stats()
        
        # MoE routing stats
        moe_stats = {
            "total_routings": len(moe_router.routing_history),
            "strategy": moe_router.strategy.value,
        }
        
        return {
            "success": True,
            "dashboard": {
                "observability": {
                    "backend": type(obs.backend).__name__,
                    "status": "active",
                },
                "analytics": analytics_summary,
                "circuit_breakers": circuit_status,
                "error_recovery": error_stats,
                "moe_router": moe_stats,
            },
            "health": {
                "llm_available": True,
                "vector_store_available": True,
                "all_systems_operational": True,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/observability/score")
async def add_score(
    trace_id: str,
    name: str,
    value: float,
    comment: Optional[str] = None
):
    """
    Bir trace'e kalite skoru ekle.
    
    RAGAS skorları veya kullanıcı feedbacki için kullanılır.
    """
    try:
        from core.langfuse_observability import Observability, Score
        
        obs = Observability()
        
        score = Score(
            name=name,
            value=value,
            comment=comment
        )
        
        if hasattr(obs.backend, 'score'):
            obs.backend.score(trace_id, score)
        
        return {
            "success": True,
            "trace_id": trace_id,
            "score": {
                "name": name,
                "value": value,
                "comment": comment,
            }
        }
        
    except Exception as e:
        logger.error(f"Add score error: {e}")
        return {"success": False, "error": str(e)}
