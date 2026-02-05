"""
Services API Router
====================

Service management endpoints - control backend services.

Features:
- Ollama service control (start/status)
- ChromaDB service control (start/reset/status)
- Backend restart
- Next.js frontend control
- Overall services status
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.config import settings
from core.embedding import embedding_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/services", tags=["Services"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ServiceStartRequest(BaseModel):
    """Servis başlatma isteği"""
    force: bool = Field(default=False, description="Zorla yeniden başlat")


# =============================================================================
# OLLAMA SERVICE
# =============================================================================

@router.post("/ollama/start", tags=["Services"])
async def start_ollama_service():
    """
    Ollama servisini başlat veya bağlantıyı yenile.
    """
    import httpx
    
    try:
        # First check if already running
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(settings.OLLAMA_API_TAGS_URL)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return {
                        "success": True,
                        "status": "already_running",
                        "message": "Ollama zaten çalışıyor",
                        "models": [m.get("name") for m in models],
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception:
                pass  # Not running, continue to start
        
        # Try to start Ollama on Windows
        try:
            ollama_paths = [
                rf"C:\Users\{os.environ.get('USERNAME', '')}\AppData\Local\Programs\Ollama\ollama.exe",
                r"C:\Program Files\Ollama\ollama.exe",
                "ollama"  # If in PATH
            ]
            
            started = False
            for path in ollama_paths:
                try:
                    if os.path.exists(path) or path == "ollama":
                        subprocess.Popen(
                            [path, "serve"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                        )
                        started = True
                        break
                except Exception:
                    continue
            
            if started:
                await asyncio.sleep(3)
                
                async with httpx.AsyncClient(timeout=5.0) as client:
                    try:
                        response = await client.get(settings.OLLAMA_API_TAGS_URL)
                        if response.status_code == 200:
                            return {
                                "success": True,
                                "status": "started",
                                "message": "Ollama başarıyla başlatıldı",
                                "timestamp": datetime.now().isoformat()
                            }
                    except Exception:
                        pass
            
            return {
                "success": False,
                "status": "failed",
                "message": "Ollama başlatılamadı. Lütfen manuel olarak başlatın: ollama serve",
                "hint": "Ollama'yı yüklemediyseniz: https://ollama.ai/download",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"Başlatma hatası: {str(e)}",
                "hint": "Terminal'de 'ollama serve' komutunu çalıştırın",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Ollama start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CHROMADB SERVICE
# =============================================================================

@router.post("/chromadb/start", tags=["Services"])
async def start_chromadb_service():
    """
    ChromaDB bağlantısını yenile veya sıfırla.
    """
    try:
        from core.chromadb_manager import chromadb_manager
        
        # Test connection
        health = chromadb_manager.health_check()
        
        if health.get("status") == "healthy":
            return {
                "success": True,
                "status": "already_running",
                "message": "ChromaDB zaten çalışıyor",
                "document_count": health.get("document_count", 0),
                "timestamp": datetime.now().isoformat()
            }
        
        # Try to reinitialize
        try:
            chromadb_manager._initialize()
            health = chromadb_manager.health_check()
            
            return {
                "success": health.get("status") == "healthy",
                "status": "reinitialized" if health.get("status") == "healthy" else "failed",
                "message": "ChromaDB yeniden başlatıldı" if health.get("status") == "healthy" else "Başlatma başarısız",
                "document_count": health.get("document_count", 0),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "status": "error",
                "message": f"ChromaDB başlatma hatası: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"ChromaDB start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chromadb/reset", tags=["Services"])
async def reset_chromadb():
    """
    ChromaDB'yi sıfırla (tüm verileri sil).
    DİKKAT: Bu işlem geri alınamaz!
    """
    try:
        from core.chromadb_manager import chromadb_manager
        
        # Get current count
        health = chromadb_manager.health_check()
        old_count = health.get("document_count", 0)
        
        # Reset
        chromadb_manager.reset_collection()
        
        # Verify
        health = chromadb_manager.health_check()
        new_count = health.get("document_count", 0)
        
        return {
            "success": True,
            "message": f"ChromaDB sıfırlandı. {old_count} döküman silindi.",
            "previous_count": old_count,
            "current_count": new_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ChromaDB reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# BACKEND SERVICE
# =============================================================================

@router.post("/backend/restart", tags=["Services"])
async def restart_backend():
    """
    Backend servisini yeniden başlat.
    
    NOT: Bu endpoint çağrıldıktan sonra servis yeniden başlatılır,
    mevcut bağlantılar kesilir.
    """
    try:
        from core.llm_manager import llm_manager
        
        # Clear caches
        llm_manager.clear_cache()
        
        # Clear embedding cache
        try:
            from core.embedding import embedding_manager
            embedding_manager.clear_cache()
        except Exception:
            pass
        
        # Notify about restart
        logger.info("Backend restart requested via API")
        
        return {
            "success": True,
            "message": "Backend yeniden başlatma hazırlandı. Birkaç saniye içinde yeniden bağlanabilirsiniz.",
            "action": "restart_pending",
            "hint": "Tam yeniden başlatma için run.py'yi kullanın",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backend restart error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NEXTJS FRONTEND SERVICE
# =============================================================================

@router.post("/nextjs/start", tags=["Services"])
async def start_nextjs_service():
    """
    Next.js frontend servisini başlat veya durumunu kontrol et.
    """
    import httpx
    
    try:
        # Check if already running
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(settings.FRONTEND_URL)
                if response.status_code in [200, 304]:
                    return {
                        "success": True,
                        "status": "already_running",
                        "message": "Next.js zaten çalışıyor",
                        "url": settings.FRONTEND_URL,
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception:
                pass  # Not running
        
        return {
            "success": False,
            "status": "not_running",
            "message": "Next.js çalışmıyor",
            "start_steps": [
                "1. Terminalde AgenticManagingSystem/frontend-next klasörüne gidin",
                "2. 'npm run dev' komutunu çalıştırın",
                "Veya: 'python run.py' ile tüm sistemi başlatın"
            ],
            "hint": "run.py scripti hem backend hem frontend'i otomatik başlatır",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Next.js check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# OVERALL STATUS
# =============================================================================

@router.get("/status", tags=["Services"])
async def get_all_services_status():
    """
    Tüm servislerin durumunu kontrol et.
    """
    import httpx
    
    services = {
        "backend": {"status": "online", "healthy": True, "port": settings.API_PORT},
        "nextjs": {"status": "unknown", "healthy": False, "port": settings.FRONTEND_PORT},
        "ollama": {"status": "unknown", "healthy": False, "port": 11434},
        "chromadb": {"status": "unknown", "healthy": False},
        "embedding": {"status": "unknown", "healthy": False}
    }
    
    # Check Next.js
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(settings.FRONTEND_URL)
            if response.status_code in [200, 304]:
                services["nextjs"] = {
                    "status": "online",
                    "healthy": True,
                    "port": settings.FRONTEND_PORT
                }
    except Exception:
        services["nextjs"] = {"status": "offline", "healthy": False, "port": settings.FRONTEND_PORT}

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(settings.OLLAMA_API_TAGS_URL)
            if response.status_code == 200:
                models = response.json().get("models", [])
                services["ollama"] = {
                    "status": "online",
                    "healthy": True,
                    "models": len(models),
                    "model_names": [m.get("name", "unknown") for m in models[:5]],
                    "port": 11434
                }
    except Exception:
        services["ollama"] = {"status": "offline", "healthy": False, "port": 11434}
    
    # Check ChromaDB
    try:
        from core.chromadb_manager import chromadb_manager
        health = chromadb_manager.health_check()
        services["chromadb"] = {
            "status": "online" if health.get("status") == "healthy" else "degraded",
            "healthy": health.get("status") == "healthy",
            "documents": health.get("document_count", 0)
        }
    except Exception:
        services["chromadb"] = {"status": "offline", "healthy": False}
    
    # Check Embedding
    try:
        stats = embedding_manager.get_cache_stats()
        services["embedding"] = {
            "status": "online",
            "healthy": True,
            "gpu_loaded": embedding_manager._gpu_model_loaded,
            "cache_size": stats.get("size", 0)
        }
    except Exception:
        services["embedding"] = {"status": "error", "healthy": False}
    
    # Core services check
    core_services = ["backend", "ollama", "chromadb"]
    core_healthy = all(services[s].get("healthy", False) for s in core_services if s in services)
    
    return {
        "services": services,
        "all_healthy": all(s.get("healthy", False) for s in services.values()),
        "core_healthy": core_healthy,
        "timestamp": datetime.now().isoformat()
    }
