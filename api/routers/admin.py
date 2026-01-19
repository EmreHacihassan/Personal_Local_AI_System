"""
Admin Router
=============

Sistem yönetimi, istatistikler, analitik ve ayarlar.
Export/Import, autostart ve kaynak izleme endpoint'leri.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
import logging
import shutil
import os

from core.config import settings
from core.vector_store import vector_store
from core.analytics import analytics
from core.export import export_manager, import_manager
from core.rate_limiter import rate_limiter
from rag.document_loader import document_loader
from rag.chunker import document_chunker


router = APIRouter(prefix="/api", tags=["Admin"])
logger = logging.getLogger(__name__)

# In-memory sessions reference (will be set from main.py)
sessions: Dict[str, List[Dict[str, Any]]] = {}


# ============ PYDANTIC MODELS ============

class AutostartRequest(BaseModel):
    """Autostart toggle isteği."""
    enabled: bool = Field(..., description="Autostart etkin mi?")


# ============ ADMIN ENDPOINTS ============

@router.get("/admin/stats")
async def get_stats():
    """Sistem istatistikleri."""
    import psutil
    
    # Vector store stats
    try:
        vs_stats = vector_store.get_stats() if hasattr(vector_store, 'get_stats') else {}
    except Exception:
        vs_stats = {}
    
    # Upload folder stats
    upload_dir = settings.DATA_DIR / "uploads"
    doc_count = 0
    total_size = 0
    
    if upload_dir.exists():
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                doc_count += 1
                total_size += file_path.stat().st_size
    
    # System resources
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        system_resources = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_gb": memory.used / (1024 ** 3),
            "memory_total_gb": memory.total / (1024 ** 3),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024 ** 3),
            "disk_total_gb": disk.total / (1024 ** 3),
        }
    except Exception:
        system_resources = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
        }
    
    return {
        "documents": {
            "total": doc_count,
            "chunks": vs_stats.get("total_documents", vector_store.count()) if vs_stats else vector_store.count(),
            "total_size_mb": total_size / (1024 * 1024)
        },
        "sessions": len(sessions),
        "total_messages": sum(len(s) for s in sessions.values()),
        "vector_store": vs_stats,
        "vector_count": vs_stats.get("total_documents", vector_store.count()) if vs_stats else vector_store.count(),
        "system_resources": system_resources
    }


@router.post("/admin/reindex")
async def reindex_documents():
    """Tüm dökümanları yeniden indexle."""
    try:
        upload_dir = settings.DATA_DIR / "uploads"
        
        if not upload_dir.exists():
            return {"message": "Yüklenmiş döküman yok", "indexed": 0}
        
        # Clear existing index
        vector_store.clear()
        
        # Reindex all documents
        total_chunks = 0
        for file_path in upload_dir.iterdir():
            if file_path.is_file():
                try:
                    documents = document_loader.load_file(str(file_path))
                    chunks = document_chunker.chunk_documents(documents)
                    
                    chunk_texts = [c.content for c in chunks]
                    chunk_metadatas = [c.metadata for c in chunks]
                    
                    vector_store.add_documents(
                        documents=chunk_texts,
                        metadatas=chunk_metadatas,
                    )
                    
                    total_chunks += len(chunks)
                except Exception as e:
                    logger.error(f"Reindex hatası: {file_path} - {e}")
        
        return {
            "message": "Yeniden indexleme tamamlandı",
            "indexed_chunks": total_chunks,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ ANALYTICS ENDPOINTS ============

@router.get("/analytics/stats")
async def get_analytics_stats(days: int = 7):
    """
    Kullanım istatistikleri.
    
    Args:
        days: Kaç günlük veri (varsayılan 7)
    """
    try:
        return analytics.get_stats(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/activity")
async def get_hourly_activity(days: int = 7):
    """Saatlik aktivite dağılımı."""
    try:
        return {"hourly_activity": analytics.get_hourly_activity(days)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/agents")
async def get_agent_usage(days: int = 30):
    """Agent kullanım istatistikleri."""
    try:
        return {"agent_usage": analytics.get_agent_usage(days)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ RATE LIMITING ENDPOINTS ============

@router.get("/ratelimit/status")
async def get_rate_limit_status(request: Request):
    """Mevcut rate limit durumu."""
    client_ip = request.client.host if request.client else "unknown"
    return rate_limiter.get_client_stats(client_ip)


@router.get("/ratelimit/global")
async def get_global_rate_limit_status():
    """Global rate limit istatistikleri."""
    return rate_limiter.get_global_stats()


# ============ EXPORT ENDPOINTS ============

@router.get("/export/sessions")
async def export_sessions(format: str = "json"):
    """
    Session'ları dışa aktar.
    
    Args:
        format: json veya csv
    """
    try:
        if format == "csv":
            file_path = export_manager.export_sessions_csv()
            media_type = "text/csv"
        else:
            file_path = export_manager.export_sessions_json()
            media_type = "application/json"
        
        def iterfile():
            with open(file_path, "rb") as f:
                yield from f
        
        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/analytics")
async def export_analytics(days: int = 30):
    """Analytics verilerini dışa aktar."""
    try:
        file_path = export_manager.export_analytics(days)
        
        def iterfile():
            with open(file_path, "rb") as f:
                yield from f
        
        return StreamingResponse(
            iterfile(),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/backup")
async def export_full_backup():
    """Tam sistem yedeği indir."""
    try:
        file_path = export_manager.export_full_backup()
        
        def iterfile():
            with open(file_path, "rb") as f:
                yield from f
        
        return StreamingResponse(
            iterfile(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={file_path.name}"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ IMPORT ENDPOINTS ============

@router.post("/import/sessions")
async def import_sessions(file: UploadFile = File(...)):
    """JSON dosyasından session'ları içe aktar."""
    try:
        # Save uploaded file temporarily
        temp_path = settings.DATA_DIR / "temp" / file.filename
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(temp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Import
        result = import_manager.import_sessions_json(temp_path)
        
        # Cleanup
        temp_path.unlink()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ AUTOSTART SETTINGS ============

@router.get("/settings/autostart")
async def get_autostart_status():
    """Windows başlangıç durumunu kontrol et."""
    try:
        startup_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EnterpriseAI.lnk")
        enabled = os.path.exists(startup_path)
        return {
            "success": True,
            "enabled": enabled,
            "startup_path": startup_path
        }
    except Exception as e:
        logger.error(f"Autostart status check error: {e}")
        return {
            "success": False,
            "enabled": False,
            "error": str(e)
        }


@router.post("/settings/autostart")
async def toggle_autostart(request: AutostartRequest):
    """Windows başlangıcına ekle/çıkar."""
    try:
        import subprocess
        
        startup_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\EnterpriseAI.lnk")
        project_path = Path(__file__).parent.parent.parent
        vbs_path = project_path / "startup.vbs"
        
        if request.enabled:
            # Startup kısayolu oluştur
            ps_command = f'''
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{startup_path}")
            $Shortcut.TargetPath = "{vbs_path}"
            $Shortcut.WorkingDirectory = "{project_path}"
            $Shortcut.Description = "Enterprise AI Assistant"
            $Shortcut.WindowStyle = 7
            $Shortcut.Save()
            '''
            result = subprocess.run(
                ["powershell", "-Command", ps_command], 
                capture_output=True, 
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            if result.returncode != 0:
                raise Exception(f"PowerShell error: {result.stderr}")
            
            return {
                "success": True,
                "enabled": True,
                "message": "Otomatik başlatma etkinleştirildi"
            }
        else:
            # Startup kısayolunu sil
            if os.path.exists(startup_path):
                os.remove(startup_path)
            
            return {
                "success": True,
                "enabled": False,
                "message": "Otomatik başlatma devre dışı bırakıldı"
            }
    except Exception as e:
        logger.error(f"Autostart toggle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
