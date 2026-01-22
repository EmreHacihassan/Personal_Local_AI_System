"""
DeepScholar v2.0 - Resilience API Endpoints
============================================

Premium esneklik özellikleri için API.
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import asyncio
import os

from core.deep_scholar_resilience import (
    resilience_service,
    ResilienceEventType,
    GenerationState,
    RecoveryStrategy
)


router = APIRouter(prefix="/api/deep-scholar/resilience", tags=["DeepScholar Resilience"])


# ==================== PYDANTIC MODELS ====================

class QueueRequest(BaseModel):
    """Kuyruğa ekleme isteği."""
    workspace_id: str
    config: Dict[str, Any]
    priority: int = Field(default=1, ge=1, le=3)


class PriorityUpdateRequest(BaseModel):
    """Öncelik güncelleme isteği."""
    priority: int = Field(..., ge=1, le=3)


# ==================== AUTO-SAVE ENDPOINTS ====================

@router.get("/autosave/{document_id}")
async def get_autosave_status(document_id: str):
    """
    Auto-save durumunu getir.
    
    Kaydedilmiş bölümleri ve toplam kelime sayısını döndürür.
    """
    entries = await resilience_service.auto_save.load_from_disk(document_id)
    
    return {
        "document_id": document_id,
        "saved_sections": len(entries),
        "total_words": sum(e.word_count for e in entries),
        "sections": [
            {
                "section_id": e.section_id,
                "section_title": e.section_title,
                "word_count": e.word_count,
                "timestamp": e.timestamp,
                "checksum": e.checksum
            }
            for e in entries
        ],
        "last_save": entries[-1].timestamp if entries else None
    }


@router.get("/autosave/{document_id}/content")
async def get_autosaved_content(document_id: str):
    """
    Auto-save edilmiş içeriği getir.
    
    Markdown formatında tüm kaydedilmiş içeriği döndürür.
    """
    await resilience_service.auto_save.load_from_disk(document_id)
    content = resilience_service.auto_save.get_cached_content(document_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="Kaydedilmiş içerik bulunamadı")
    
    return {
        "document_id": document_id,
        "content": content,
        "word_count": resilience_service.auto_save.get_word_count(document_id)
    }


@router.delete("/autosave/{document_id}")
async def clear_autosave(document_id: str):
    """Auto-save cache'ini temizle."""
    await resilience_service.auto_save.clear_cache(document_id)
    return {"success": True, "message": "Auto-save temizlendi"}


# ==================== CHECKPOINT ENDPOINTS ====================

@router.get("/checkpoint/{document_id}")
async def get_checkpoint(document_id: str):
    """
    Checkpoint bilgisini getir.
    
    Kapsamlı durum bilgisi döndürür.
    """
    checkpoint = await resilience_service.checkpoint.load_checkpoint(document_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint bulunamadı")
    
    return {
        "document_id": document_id,
        "workspace_id": checkpoint.workspace_id,
        "state": checkpoint.state,
        "progress": checkpoint.progress,
        "current_phase": checkpoint.current_phase,
        "current_section_index": checkpoint.current_section_index,
        "completed_sections_count": len(checkpoint.completed_sections),
        "total_words": sum(len(c.split()) for c in checkpoint.section_contents.values()),
        "citations_count": len(checkpoint.citations),
        "visuals_count": len(checkpoint.visuals),
        "retry_count": checkpoint.retry_count,
        "created_at": checkpoint.created_at,
        "updated_at": checkpoint.updated_at,
        "can_resume": checkpoint.state not in ["completed", "cancelled"]
    }


@router.get("/checkpoint/{document_id}/sections")
async def get_checkpoint_sections(document_id: str):
    """Checkpoint'teki tamamlanan bölümleri getir."""
    checkpoint = await resilience_service.checkpoint.load_checkpoint(document_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint bulunamadı")
    
    sections = []
    for section in checkpoint.completed_sections:
        section_id = section.get('id', '')
        content = checkpoint.section_contents.get(section_id, '')
        sections.append({
            "id": section_id,
            "title": section.get('title', ''),
            "level": section.get('level', 1),
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "word_count": len(content.split())
        })
    
    return {
        "document_id": document_id,
        "sections": sections,
        "total_sections": len(sections)
    }


@router.post("/checkpoint/{document_id}/resume")
async def resume_from_checkpoint(document_id: str):
    """
    Checkpoint'ten devam et.
    
    WebSocket bağlantısı ile üretimi kaldığı yerden devam ettirir.
    """
    checkpoint = await resilience_service.checkpoint.load_checkpoint(document_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint bulunamadı")
    
    if checkpoint.state in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Bu döküman tamamlanmış veya iptal edilmiş")
    
    return {
        "success": True,
        "document_id": document_id,
        "message": "Checkpoint hazır. WebSocket ile bağlanarak devam edebilirsiniz.",
        "websocket_url": f"/api/deep-scholar/ws/{document_id}",
        "resume_info": {
            "progress": checkpoint.progress,
            "current_phase": checkpoint.current_phase,
            "completed_sections": len(checkpoint.completed_sections),
            "pending_sections": checkpoint.current_section_index
        }
    }


@router.delete("/checkpoint/{document_id}")
async def delete_checkpoint(document_id: str):
    """Checkpoint'i sil."""
    await resilience_service.checkpoint.delete_checkpoint(document_id)
    return {"success": True, "message": "Checkpoint silindi"}


@router.get("/checkpoints")
async def list_all_checkpoints():
    """Tüm checkpoint'leri listele."""
    checkpoint_ids = resilience_service.checkpoint.list_checkpoints()
    
    checkpoints = []
    for doc_id in checkpoint_ids:
        cp = await resilience_service.checkpoint.load_checkpoint(doc_id)
        if cp:
            checkpoints.append({
                "document_id": doc_id,
                "title": cp.config.get("title", ""),
                "progress": cp.progress,
                "state": cp.state,
                "updated_at": cp.updated_at
            })
    
    return {
        "total": len(checkpoints),
        "checkpoints": checkpoints
    }


# ==================== PARTIAL EXPORT ENDPOINTS ====================

@router.post("/export/partial/{document_id}")
async def create_partial_export(document_id: str, format: str = "markdown"):
    """
    Kısmi export oluştur.
    
    Tamamlanmamış dökümanı belirtilen formatta export eder.
    
    Args:
        format: 'markdown' veya 'html'
    """
    checkpoint = await resilience_service.checkpoint.load_checkpoint(document_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint bulunamadı")
    
    if format == "html":
        filepath = await resilience_service.partial_export.export_to_html(checkpoint)
        media_type = "text/html"
    else:
        filepath = await resilience_service.partial_export.create_partial_export(checkpoint)
        media_type = "text/markdown"
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail="Export oluşturulamadı")
    
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type=media_type
    )


@router.get("/export/partial/{document_id}/preview")
async def preview_partial_export(document_id: str):
    """Kısmi export önizlemesi."""
    checkpoint = await resilience_service.checkpoint.load_checkpoint(document_id)
    
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint bulunamadı")
    
    content = checkpoint.get_partial_content()
    
    return {
        "document_id": document_id,
        "title": checkpoint.config.get("title", "Döküman"),
        "progress": checkpoint.progress,
        "content_preview": content[:2000] + "..." if len(content) > 2000 else content,
        "total_length": len(content),
        "sections_count": len(checkpoint.completed_sections),
        "can_export": len(content) > 0
    }


# ==================== GENERATION QUEUE ENDPOINTS ====================

@router.post("/queue")
async def add_to_queue(request: QueueRequest):
    """
    Kuyruğa yeni üretim ekle.
    
    Priority:
    - 1: Normal
    - 2: Yüksek
    - 3: Acil
    """
    import uuid
    
    generation_id = str(uuid.uuid4())
    
    queued = resilience_service.queue.add_to_queue(
        generation_id=generation_id,
        workspace_id=request.workspace_id,
        config=request.config,
        priority=request.priority
    )
    
    return {
        "success": True,
        "generation_id": queued.id,
        "position": queued.position,
        "priority": queued.priority,
        "queue_length": len(resilience_service.queue._queue)
    }


@router.get("/queue")
async def get_queue_status():
    """Kuyruk durumunu getir."""
    status = resilience_service.queue.get_queue_status()
    return status


@router.get("/queue/{generation_id}")
async def get_queue_item(generation_id: str):
    """Kuyruktaki öğenin durumunu getir."""
    status = resilience_service.queue.get_queue_status()
    
    # Kuyrukta ara
    for item in status["queue"]:
        if item["id"] == generation_id:
            return {
                "found": True,
                "status": "queued",
                **item
            }
    
    # Aktif'te ara
    for item in status["active"]:
        if item["id"] == generation_id:
            return {
                "found": True,
                "status": "active",
                **item
            }
    
    raise HTTPException(status_code=404, detail="Kuyrukta bulunamadı")


@router.delete("/queue/{generation_id}")
async def remove_from_queue(generation_id: str):
    """Kuyruktan çıkar."""
    success = resilience_service.queue.remove_from_queue(generation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Kuyrukta bulunamadı")
    
    return {"success": True, "message": "Kuyruktan çıkarıldı"}


@router.patch("/queue/{generation_id}/priority")
async def update_queue_priority(generation_id: str, request: PriorityUpdateRequest):
    """Önceliği güncelle."""
    resilience_service.queue.update_priority(generation_id, request.priority)
    
    return {
        "success": True,
        "generation_id": generation_id,
        "new_priority": request.priority
    }


@router.post("/queue/process-next")
async def process_next_in_queue():
    """Sıradaki üretimi başlat."""
    next_item = resilience_service.queue.get_next()
    
    if not next_item:
        return {
            "success": False,
            "message": "Kuyrukta bekleyen yok veya maksimum eşzamanlı üretim sayısına ulaşıldı"
        }
    
    return {
        "success": True,
        "generation_id": next_item.id,
        "config": next_item.config,
        "message": "Üretim başlatılıyor..."
    }


# ==================== ERROR RECOVERY ENDPOINTS ====================

@router.get("/errors/{document_id}")
async def get_error_info(document_id: str):
    """Hata bilgisini getir."""
    info = resilience_service.error_recovery.get_error_info(document_id)
    return {
        "document_id": document_id,
        **info
    }


@router.post("/errors/{document_id}/reset")
async def reset_error_count(document_id: str):
    """Hata sayacını sıfırla."""
    resilience_service.error_recovery.reset_error_count(document_id)
    return {"success": True, "message": "Hata sayacı sıfırlandı"}


@router.post("/errors/{document_id}/recover")
async def trigger_recovery(document_id: str, strategy: str = "continue"):
    """Manuel kurtarma tetikle."""
    try:
        recovery_strategy = RecoveryStrategy(strategy)
    except ValueError:
        recovery_strategy = RecoveryStrategy.CONTINUE_FROM_CHECKPOINT
    
    success = await resilience_service.error_recovery.execute_recovery(
        document_id=document_id,
        strategy=recovery_strategy,
        checkpoint_manager=resilience_service.checkpoint
    )
    
    return {
        "success": success,
        "strategy": recovery_strategy.value,
        "message": "Kurtarma işlemi başlatıldı" if success else "Kurtarma başarısız"
    }


# ==================== OFFLINE MODE ENDPOINTS ====================

@router.get("/offline/pending")
async def get_pending_sync():
    """Sync bekleyen dökümanları listele."""
    pending = resilience_service.offline.get_pending_sync()
    
    items = []
    for doc_id in pending:
        offline = await resilience_service.offline.load_offline_state(doc_id)
        if offline:
            items.append({
                "document_id": doc_id,
                "saved_at": offline.saved_at,
                "pending_events": len(offline.pending_events)
            })
    
    return {
        "pending_count": len(items),
        "items": items
    }


@router.post("/offline/{document_id}/sync")
async def sync_offline_data(document_id: str):
    """Çevrimdışı veriyi sync et."""
    offline = await resilience_service.offline.load_offline_state(document_id)
    
    if not offline:
        raise HTTPException(status_code=404, detail="Çevrimdışı veri bulunamadı")
    
    # Sync işlemi
    await resilience_service.offline.mark_synced(document_id)
    
    return {
        "success": True,
        "document_id": document_id,
        "message": "Sync tamamlandı"
    }


# ==================== CONNECTION RESILIENCE ENDPOINTS ====================

@router.get("/connection/{document_id}")
async def get_connection_status(document_id: str):
    """Bağlantı durumunu getir."""
    state = resilience_service.connection._connection_states.get(document_id, {})
    
    return {
        "document_id": document_id,
        "connected": state.get("connected", False),
        "reconnect_attempts": state.get("attempt", 0),
        "can_reconnect": state.get("can_reconnect", True),
        "next_retry_delay": resilience_service.connection.get_reconnect_delay(document_id)
    }


@router.post("/connection/{document_id}/reset")
async def reset_connection_state(document_id: str):
    """Bağlantı durumunu sıfırla."""
    resilience_service.connection.reset(document_id)
    return {"success": True, "message": "Bağlantı durumu sıfırlandı"}


# ==================== CLEANUP ENDPOINTS ====================

@router.post("/cleanup/{document_id}")
async def cleanup_document_data(document_id: str):
    """Döküman için tüm resilience verilerini temizle."""
    await resilience_service.cleanup(document_id)
    return {
        "success": True,
        "document_id": document_id,
        "message": "Tüm resilience verileri temizlendi"
    }


# ==================== STATUS & INFO ENDPOINTS ====================

@router.get("/status")
async def get_resilience_status():
    """Genel resilience durumu."""
    checkpoints = resilience_service.checkpoint.list_checkpoints()
    pending_sync = resilience_service.offline.get_pending_sync()
    queue_status = resilience_service.queue.get_queue_status()
    
    return {
        "active_checkpoints": len(checkpoints),
        "pending_offline_sync": len(pending_sync),
        "queue_length": queue_status["queue_length"],
        "active_generations": queue_status["active_count"],
        "features": {
            "auto_save": True,
            "checkpoint": True,
            "error_recovery": True,
            "queue": True,
            "offline_mode": True,
            "partial_export": True,
            "connection_resilience": True
        }
    }


@router.get("/info")
async def get_resilience_info():
    """Resilience özellikleri hakkında bilgi."""
    return {
        "version": "2.0",
        "name": "DeepScholar Resilience Module",
        "description": "Kurumsal seviye esneklik ve dayanıklılık özellikleri",
        "features": [
            {
                "name": "Auto-Save",
                "description": "Her bölüm tamamlandığında otomatik kayıt",
                "icon": "💾"
            },
            {
                "name": "Checkpoint System",
                "description": "Kapsamlı durum yönetimi ve recovery",
                "icon": "🔖"
            },
            {
                "name": "Error Recovery",
                "description": "Otomatik hata kurtarma ve retry logic",
                "icon": "🔄"
            },
            {
                "name": "Generation Queue",
                "description": "Çoklu döküman üretim kuyruğu",
                "icon": "📋"
            },
            {
                "name": "Offline Mode",
                "description": "Bağlantı kesintisinde veri koruma",
                "icon": "📴"
            },
            {
                "name": "Partial Export",
                "description": "Tamamlanmamış dökümanları export etme",
                "icon": "📤"
            },
            {
                "name": "Connection Resilience",
                "description": "Otomatik yeniden bağlanma",
                "icon": "🔌"
            }
        ],
        "premium": True
    }
