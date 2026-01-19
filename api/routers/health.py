"""
Health Check Router
====================

Kubernetes-ready liveness ve readiness probes.
Sistem sağlık kontrolü endpoint'leri.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime
import shutil

from core.config import settings
from core.llm_manager import llm_manager
from core.vector_store import vector_store
from agents.orchestrator import orchestrator
from core.circuit_breaker import circuit_registry
from core.health import get_health_report


router = APIRouter(prefix="", tags=["health"])


# ============ PYDANTIC MODELS ============

class HealthResponse(BaseModel):
    """Sağlık kontrolü yanıtı."""
    status: str
    timestamp: str
    components: Dict[str, Any]


class LivenessResponse(BaseModel):
    """Kubernetes liveness probe yanıtı."""
    status: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe yanıtı."""
    status: str
    ready: bool
    checks: Dict[str, bool]


# ============ ENDPOINTS ============

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Sistem sağlık kontrolü.
    
    Tüm bileşenlerin durumunu kontrol eder ve genel sağlık durumunu döndürür.
    """
    components = {
        "api": "healthy",
        "llm": "unknown",
        "vector_store": "unknown",
    }
    
    # Check LLM
    try:
        status = llm_manager.get_status()
        components["llm"] = "healthy" if status.get("primary_available") else "degraded"
    except Exception:
        components["llm"] = "unhealthy"
    
    # Check Vector Store
    try:
        count = vector_store.count()
        components["vector_store"] = "healthy"
        components["document_count"] = count
    except Exception:
        components["vector_store"] = "unhealthy"
    
    overall = "healthy" if all(
        v in ["healthy", "unknown"] for k, v in components.items() 
        if isinstance(v, str)
    ) else "degraded"
    
    return HealthResponse(
        status=overall,
        timestamp=datetime.now().isoformat(),
        components=components,
    )


@router.get("/health/live", response_model=LivenessResponse)
async def liveness_probe():
    """
    Kubernetes Liveness Probe.
    
    Uygulamanın çalışıp çalışmadığını kontrol eder.
    Bu endpoint her zaman 200 döndürür (uygulama ayaktaysa).
    
    Kullanım:
    ```yaml
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8001
      initialDelaySeconds: 10
      periodSeconds: 30
    ```
    """
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now().isoformat()
    )


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_probe():
    """
    Kubernetes Readiness Probe.
    
    Uygulamanın trafiğe hazır olup olmadığını kontrol eder.
    Tüm kritik bağımlılıklar kontrol edilir.
    
    Kullanım:
    ```yaml
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8001
      initialDelaySeconds: 5
      periodSeconds: 10
    ```
    """
    checks = {
        "llm_available": False,
        "vector_store_ready": False,
        "disk_space_ok": False,
    }
    
    # LLM kontrolü
    try:
        status = llm_manager.get_status()
        checks["llm_available"] = status.get("primary_available", False)
    except Exception:
        pass
    
    # Vector store kontrolü
    try:
        _ = vector_store.count()
        checks["vector_store_ready"] = True
    except Exception:
        pass
    
    # Disk alanı kontrolü
    try:
        total, used, free = shutil.disk_usage(settings.DATA_DIR)
        # En az 100MB boş alan olmalı
        checks["disk_space_ok"] = free > 100 * 1024 * 1024
    except Exception:
        checks["disk_space_ok"] = True  # Kontrol edilemezse geç
    
    # Tüm kritik kontroller geçmeli
    is_ready = checks["llm_available"] and checks["vector_store_ready"]
    
    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        ready=is_ready,
        checks=checks
    )


@router.get("/status")
async def get_status():
    """Detaylı sistem durumu."""
    return {
        "llm": llm_manager.get_status(),
        "vector_store": vector_store.get_stats(),
        "agents": orchestrator.get_agents_status(),
        "circuit_breakers": circuit_registry.get_all_status(),
        "config": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "top_k": settings.TOP_K_RESULTS,
        },
    }


@router.get("/status/circuits")
async def get_circuit_breaker_status():
    """
    Circuit breaker durumları.
    
    Tüm circuit breaker'ların anlık durumunu döndürür.
    """
    return {
        "circuits": circuit_registry.get_all_status(),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/status/circuits/reset")
async def reset_circuit_breakers():
    """
    Tüm circuit breaker'ları sıfırla.
    
    Dikkatli kullanın - tüm devre durumlarını CLOSED'a çevirir.
    """
    circuit_registry.reset_all()
    return {
        "message": "All circuit breakers reset to CLOSED state",
        "circuits": circuit_registry.get_all_status(),
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/api/health/detailed")
async def detailed_health_check():
    """Detaylı sistem sağlık raporu."""
    try:
        report = await get_health_report()
        return report
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        }
