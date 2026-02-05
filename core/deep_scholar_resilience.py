"""
DeepScholar v2.0 - Premium Resilience Module
=============================================

Kurumsal seviye esneklik ve dayanıklılık özellikleri.

Özellikler:
1. Auto-Save: Her bölüm otomatik kaydedilir
2. Browser Tab Protection: Sayfa kapatılırken uyarı
3. Partial Export: Yarım kalan dökümanı PDF olarak indir
4. Error Recovery: Hata sonrası otomatik devam
5. Connection Resilience: WebSocket yeniden bağlanma
6. Generation Queue: Çoklu döküman kuyruğu
7. Offline Mode: Bağlantı kesintisinde veri koruma

Premium Feature: Enterprise-grade reliability
"""

import asyncio
import json
import logging
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import aiofiles
import traceback

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ResilienceEventType(str, Enum):
    """Resilience event tipleri."""
    AUTO_SAVED = "auto_saved"
    CHECKPOINT_CREATED = "checkpoint_created"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_COMPLETED = "recovery_completed"
    CONNECTION_LOST = "connection_lost"
    CONNECTION_RESTORED = "connection_restored"
    QUEUE_UPDATED = "queue_updated"
    PARTIAL_EXPORT_READY = "partial_export_ready"
    ERROR_RECOVERED = "error_recovered"
    OFFLINE_DATA_SAVED = "offline_data_saved"


class GenerationState(str, Enum):
    """Üretim durumu."""
    QUEUED = "queued"
    STARTING = "starting"
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING = "writing"
    FACT_CHECKING = "fact_checking"
    FINALIZING = "finalizing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


class RecoveryStrategy(str, Enum):
    """Kurtarma stratejisi."""
    RETRY_SECTION = "retry_section"           # Sadece başarısız bölümü tekrarla
    CONTINUE_FROM_CHECKPOINT = "continue"      # Checkpoint'ten devam et
    RESTART_PHASE = "restart_phase"           # Mevcut fazı tekrarla
    FULL_RESTART = "full_restart"             # Baştan başla


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AutoSaveEntry:
    """Otomatik kayıt girişi."""
    document_id: str
    section_id: str
    section_title: str
    content: str
    word_count: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = hashlib.md5(self.content.encode()).hexdigest()[:16]


@dataclass 
class ResilienceCheckpoint:
    """Kapsamlı checkpoint - tüm state bilgisi."""
    document_id: str
    workspace_id: str
    config: Dict[str, Any]
    
    # İlerleme bilgisi
    state: str
    progress: int
    current_phase: str
    current_section_index: int
    
    # Tamamlanan içerik
    completed_sections: List[Dict[str, Any]] = field(default_factory=list)
    section_contents: Dict[str, str] = field(default_factory=dict)
    
    # Araştırma verileri
    research_data: Dict[str, List[Dict]] = field(default_factory=dict)
    citations: List[Dict] = field(default_factory=list)
    
    # Görsel ve ek veriler
    visuals: List[Dict] = field(default_factory=list)
    agent_thoughts: List[Dict] = field(default_factory=list)
    
    # Hata ve retry bilgisi
    error_log: List[Dict] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    # Zaman damgaları
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_successful_save: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ResilienceCheckpoint':
        return cls(**data)
    
    def get_partial_content(self) -> str:
        """Mevcut içeriği markdown olarak döndür."""
        content_parts = []
        
        # Başlık
        title = self.config.get('title', 'Döküman')
        content_parts.append(f"# {title}\n\n")
        content_parts.append(f"*Bu döküman üretim sırasında kaydedilmiştir. "
                           f"İlerleme: {self.progress}%*\n\n")
        content_parts.append("---\n\n")
        
        # Bölümler
        for section in self.completed_sections:
            section_id = section.get('id', '')
            section_title = section.get('title', '')
            level = section.get('level', 1)
            
            # Başlık seviyesi
            header = '#' * (level + 1)
            content_parts.append(f"{header} {section_title}\n\n")
            
            # İçerik
            content = self.section_contents.get(section_id, '')
            if content:
                content_parts.append(f"{content}\n\n")
        
        # Kaynakça
        if self.citations:
            content_parts.append("\n---\n## Kaynakça\n\n")
            for i, citation in enumerate(self.citations, 1):
                title = citation.get('title', 'Kaynak')
                url = citation.get('url', '')
                if url:
                    content_parts.append(f"{i}. [{title}]({url})\n")
                else:
                    content_parts.append(f"{i}. {title}\n")
        
        return ''.join(content_parts)


@dataclass
class QueuedGeneration:
    """Kuyrukta bekleyen üretim."""
    id: str
    workspace_id: str
    config: Dict[str, Any]
    priority: int = 1  # 1 = normal, 2 = high, 3 = urgent
    status: str = "queued"
    position: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    estimated_completion: Optional[str] = None


@dataclass
class OfflineData:
    """Çevrimdışı mod için kaydedilen veri."""
    document_id: str
    last_known_state: Dict[str, Any]
    pending_events: List[Dict] = field(default_factory=list)
    saved_at: str = field(default_factory=lambda: datetime.now().isoformat())
    sync_required: bool = True


# ============================================================================
# AUTO-SAVE MANAGER
# ============================================================================

class AutoSaveManager:
    """
    Otomatik Kayıt Yöneticisi
    
    Her bölüm tamamlandığında otomatik kayıt yapar.
    Disk ve memory'de cache tutar.
    """
    
    def __init__(self, cache_dir: str = "data/autosave"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._cache: Dict[str, List[AutoSaveEntry]] = {}
        self._save_interval = 30  # saniye
        self._last_save_time: Dict[str, datetime] = {}
        
    async def save_section(
        self, 
        document_id: str,
        section_id: str,
        section_title: str,
        content: str
    ) -> AutoSaveEntry:
        """Bölümü otomatik kaydet."""
        word_count = len(content.split())
        
        entry = AutoSaveEntry(
            document_id=document_id,
            section_id=section_id,
            section_title=section_title,
            content=content,
            word_count=word_count
        )
        
        # Memory cache'e ekle
        if document_id not in self._cache:
            self._cache[document_id] = []
        self._cache[document_id].append(entry)
        
        # Disk'e kaydet
        await self._save_to_disk(document_id)
        
        return entry
    
    async def _save_to_disk(self, document_id: str):
        """Disk'e kaydet."""
        filepath = self.cache_dir / f"{document_id}.autosave.json"
        
        data = {
            "document_id": document_id,
            "entries": [asdict(e) for e in self._cache.get(document_id, [])],
            "saved_at": datetime.now().isoformat()
        }
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        
        self._last_save_time[document_id] = datetime.now()
    
    async def load_from_disk(self, document_id: str) -> List[AutoSaveEntry]:
        """Disk'ten yükle."""
        filepath = self.cache_dir / f"{document_id}.autosave.json"
        
        if not filepath.exists():
            return []
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
            
            entries = [AutoSaveEntry(**e) for e in data.get("entries", [])]
            self._cache[document_id] = entries
            return entries
        except Exception as e:
            logger.warning(f"AutoSave yükleme hatası: {e}")
            return []
    
    def get_cached_content(self, document_id: str) -> str:
        """Önbelleğe alınmış içeriği al."""
        entries = self._cache.get(document_id, [])
        if not entries:
            return ""
        
        return "\n\n".join([e.content for e in entries])
    
    def get_word_count(self, document_id: str) -> int:
        """Toplam kelime sayısını al."""
        entries = self._cache.get(document_id, [])
        return sum(e.word_count for e in entries)
    
    async def clear_cache(self, document_id: str):
        """Cache'i temizle."""
        self._cache.pop(document_id, None)
        
        filepath = self.cache_dir / f"{document_id}.autosave.json"
        if filepath.exists():
            filepath.unlink()


# ============================================================================
# CHECKPOINT MANAGER
# ============================================================================

class CheckpointManager:
    """
    Checkpoint Yöneticisi
    
    Kapsamlı state yönetimi ve recovery.
    """
    
    def __init__(self, checkpoint_dir: str = "data/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory checkpoints
        self._checkpoints: Dict[str, ResilienceCheckpoint] = {}
        
    async def create_checkpoint(
        self,
        document_id: str,
        workspace_id: str,
        config: Dict[str, Any],
        state: GenerationState,
        progress: int,
        current_phase: str,
        current_section_index: int,
        completed_sections: List[Dict],
        section_contents: Dict[str, str],
        research_data: Dict[str, List[Dict]] = None,
        citations: List[Dict] = None,
        visuals: List[Dict] = None,
        agent_thoughts: List[Dict] = None
    ) -> ResilienceCheckpoint:
        """Yeni checkpoint oluştur."""
        
        checkpoint = ResilienceCheckpoint(
            document_id=document_id,
            workspace_id=workspace_id,
            config=config,
            state=state.value,
            progress=progress,
            current_phase=current_phase,
            current_section_index=current_section_index,
            completed_sections=completed_sections or [],
            section_contents=section_contents or {},
            research_data=research_data or {},
            citations=citations or [],
            visuals=visuals or [],
            agent_thoughts=agent_thoughts or [],
            updated_at=datetime.now().isoformat(),
            last_successful_save=datetime.now().isoformat()
        )
        
        # Memory'e kaydet
        self._checkpoints[document_id] = checkpoint
        
        # Disk'e kaydet
        await self._save_checkpoint(checkpoint)
        
        return checkpoint
    
    async def update_checkpoint(
        self,
        document_id: str,
        **updates
    ) -> Optional[ResilienceCheckpoint]:
        """Mevcut checkpoint'i güncelle."""
        checkpoint = self._checkpoints.get(document_id)
        
        if not checkpoint:
            checkpoint = await self.load_checkpoint(document_id)
        
        if not checkpoint:
            return None
        
        # Güncelle
        for key, value in updates.items():
            if hasattr(checkpoint, key):
                setattr(checkpoint, key, value)
        
        checkpoint.updated_at = datetime.now().isoformat()
        
        # Kaydet
        await self._save_checkpoint(checkpoint)
        
        return checkpoint
    
    async def _save_checkpoint(self, checkpoint: ResilienceCheckpoint):
        """Checkpoint'i disk'e kaydet."""
        filepath = self.checkpoint_dir / f"{checkpoint.document_id}.checkpoint.json"
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(checkpoint.to_dict(), ensure_ascii=False, indent=2))
    
    async def load_checkpoint(self, document_id: str) -> Optional[ResilienceCheckpoint]:
        """Checkpoint'i disk'ten yükle."""
        filepath = self.checkpoint_dir / f"{document_id}.checkpoint.json"
        
        if not filepath.exists():
            return None
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
            
            checkpoint = ResilienceCheckpoint.from_dict(data)
            self._checkpoints[document_id] = checkpoint
            return checkpoint
        except Exception as e:
            logger.warning(f"Checkpoint yükleme hatası: {e}")
            return None
    
    def get_checkpoint(self, document_id: str) -> Optional[ResilienceCheckpoint]:
        """Memory'den checkpoint al."""
        return self._checkpoints.get(document_id)
    
    async def delete_checkpoint(self, document_id: str):
        """Checkpoint'i sil."""
        self._checkpoints.pop(document_id, None)
        
        filepath = self.checkpoint_dir / f"{document_id}.checkpoint.json"
        if filepath.exists():
            filepath.unlink()
    
    def list_checkpoints(self) -> List[str]:
        """Tüm checkpoint'leri listele."""
        checkpoints = []
        for f in self.checkpoint_dir.glob("*.checkpoint.json"):
            checkpoints.append(f.stem.replace(".checkpoint", ""))
        return checkpoints


# ============================================================================
# ERROR RECOVERY MANAGER
# ============================================================================

class ErrorRecoveryManager:
    """
    Hata Kurtarma Yöneticisi
    
    Otomatik hata kurtarma ve retry logic.
    """
    
    def __init__(self):
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, List[Dict]] = {}
        self._recovery_callbacks: Dict[str, Callable] = {}
        
        # Retry ayarları
        self.max_retries = 3
        self.retry_delays = [5, 15, 30]  # saniye
        self.recoverable_errors = [
            "timeout",
            "connection_error",
            "rate_limit",
            "api_error",
            "llm_error"
        ]
    
    async def handle_error(
        self,
        document_id: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> RecoveryStrategy:
        """Hatayı işle ve kurtarma stratejisi belirle."""
        
        error_type = self._classify_error(error)
        
        # Hata sayısını artır
        if document_id not in self._error_counts:
            self._error_counts[document_id] = 0
        self._error_counts[document_id] += 1
        
        # Log ekle
        if document_id not in self._last_errors:
            self._last_errors[document_id] = []
        self._last_errors[document_id].append({
            "type": error_type,
            "message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        })
        
        # Kurtarma stratejisi belirle
        retry_count = self._error_counts[document_id]
        
        if error_type in self.recoverable_errors:
            if retry_count <= 1:
                return RecoveryStrategy.RETRY_SECTION
            elif retry_count <= 2:
                return RecoveryStrategy.CONTINUE_FROM_CHECKPOINT
            elif retry_count <= 3:
                return RecoveryStrategy.RESTART_PHASE
            else:
                return RecoveryStrategy.FULL_RESTART
        else:
            # Kurtarılamaz hata
            return RecoveryStrategy.FULL_RESTART
    
    def _classify_error(self, error: Exception) -> str:
        """Hatayı sınıflandır."""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return "timeout"
        elif "connection" in error_str or "network" in error_str:
            return "connection_error"
        elif "rate" in error_str or "429" in error_str:
            return "rate_limit"
        elif "api" in error_str:
            return "api_error"
        elif "llm" in error_str or "openai" in error_str or "anthropic" in error_str:
            return "llm_error"
        else:
            return "unknown"
    
    async def execute_recovery(
        self,
        document_id: str,
        strategy: RecoveryStrategy,
        checkpoint_manager: CheckpointManager
    ) -> bool:
        """Kurtarma işlemini gerçekleştir."""
        
        checkpoint = checkpoint_manager.get_checkpoint(document_id)
        if not checkpoint:
            return False
        
        retry_count = self._error_counts.get(document_id, 0)
        delay = self.retry_delays[min(retry_count - 1, len(self.retry_delays) - 1)]
        
        # Bekle
        await asyncio.sleep(delay)
        
        # Strateji uygula
        if strategy == RecoveryStrategy.RETRY_SECTION:
            # Sadece mevcut bölümü tekrarla
            return True
        elif strategy == RecoveryStrategy.CONTINUE_FROM_CHECKPOINT:
            # Checkpoint'ten devam et
            return True
        elif strategy == RecoveryStrategy.RESTART_PHASE:
            # Mevcut fazı baştan başlat
            checkpoint.current_section_index = 0
            await checkpoint_manager.update_checkpoint(
                document_id,
                current_section_index=0
            )
            return True
        else:
            # Tam yeniden başlatma
            return False
    
    def reset_error_count(self, document_id: str):
        """Hata sayacını sıfırla."""
        self._error_counts.pop(document_id, None)
        self._last_errors.pop(document_id, None)
    
    def get_error_info(self, document_id: str) -> Dict:
        """Hata bilgisini al."""
        return {
            "error_count": self._error_counts.get(document_id, 0),
            "last_errors": self._last_errors.get(document_id, [])[-5:]
        }


# ============================================================================
# GENERATION QUEUE MANAGER
# ============================================================================

class GenerationQueueManager:
    """
    Üretim Kuyruğu Yöneticisi
    
    Çoklu döküman üretimini sıralar ve yönetir.
    """
    
    def __init__(self, max_concurrent: int = 1):
        self._queue: List[QueuedGeneration] = []
        self._active: Dict[str, QueuedGeneration] = {}
        self._completed: List[QueuedGeneration] = []
        self._max_concurrent = max_concurrent
        self._queue_callbacks: List[Callable] = []
    
    def add_to_queue(
        self,
        generation_id: str,
        workspace_id: str,
        config: Dict[str, Any],
        priority: int = 1
    ) -> QueuedGeneration:
        """Kuyruğa ekle."""
        
        queued = QueuedGeneration(
            id=generation_id,
            workspace_id=workspace_id,
            config=config,
            priority=priority,
            position=len(self._queue) + 1
        )
        
        # Priority'ye göre sırala
        self._queue.append(queued)
        self._queue.sort(key=lambda x: (-x.priority, x.created_at))
        
        # Pozisyonları güncelle
        for i, item in enumerate(self._queue):
            item.position = i + 1
        
        return queued
    
    def get_next(self) -> Optional[QueuedGeneration]:
        """Sıradaki üretimi al."""
        if len(self._active) >= self._max_concurrent:
            return None
        
        if not self._queue:
            return None
        
        next_item = self._queue.pop(0)
        next_item.status = "starting"
        next_item.started_at = datetime.now().isoformat()
        self._active[next_item.id] = next_item
        
        # Pozisyonları güncelle
        for i, item in enumerate(self._queue):
            item.position = i + 1
        
        return next_item
    
    def mark_completed(self, generation_id: str, success: bool = True):
        """Tamamlandı olarak işaretle."""
        if generation_id in self._active:
            item = self._active.pop(generation_id)
            item.status = "completed" if success else "failed"
            self._completed.append(item)
    
    def get_queue_status(self) -> Dict:
        """Kuyruk durumunu al."""
        return {
            "queue_length": len(self._queue),
            "active_count": len(self._active),
            "completed_count": len(self._completed),
            "queue": [
                {
                    "id": q.id,
                    "title": q.config.get("title", ""),
                    "priority": q.priority,
                    "position": q.position,
                    "created_at": q.created_at
                }
                for q in self._queue
            ],
            "active": [
                {
                    "id": a.id,
                    "title": a.config.get("title", ""),
                    "started_at": a.started_at
                }
                for a in self._active.values()
            ]
        }
    
    def remove_from_queue(self, generation_id: str) -> bool:
        """Kuyruktan çıkar."""
        for i, item in enumerate(self._queue):
            if item.id == generation_id:
                self._queue.pop(i)
                # Pozisyonları güncelle
                for j, remaining in enumerate(self._queue):
                    remaining.position = j + 1
                return True
        return False
    
    def update_priority(self, generation_id: str, new_priority: int):
        """Önceliği güncelle."""
        for item in self._queue:
            if item.id == generation_id:
                item.priority = new_priority
                break
        
        # Yeniden sırala
        self._queue.sort(key=lambda x: (-x.priority, x.created_at))
        for i, item in enumerate(self._queue):
            item.position = i + 1


# ============================================================================
# OFFLINE MODE MANAGER
# ============================================================================

class OfflineModeManager:
    """
    Çevrimdışı Mod Yöneticisi
    
    Bağlantı kesintisinde verileri korur ve sync yapar.
    """
    
    def __init__(self, offline_dir: str = "data/offline"):
        self.offline_dir = Path(offline_dir)
        self.offline_dir.mkdir(parents=True, exist_ok=True)
        
        self._offline_data: Dict[str, OfflineData] = {}
        self._pending_sync: List[str] = []
    
    async def save_offline_state(
        self,
        document_id: str,
        state: Dict[str, Any],
        events: List[Dict] = None
    ) -> OfflineData:
        """Çevrimdışı durum kaydet."""
        
        offline = OfflineData(
            document_id=document_id,
            last_known_state=state,
            pending_events=events or [],
            sync_required=True
        )
        
        self._offline_data[document_id] = offline
        self._pending_sync.append(document_id)
        
        # Disk'e kaydet
        filepath = self.offline_dir / f"{document_id}.offline.json"
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(asdict(offline), ensure_ascii=False, indent=2))
        
        return offline
    
    async def load_offline_state(self, document_id: str) -> Optional[OfflineData]:
        """Çevrimdışı durumu yükle."""
        filepath = self.offline_dir / f"{document_id}.offline.json"
        
        if not filepath.exists():
            return None
        
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                data = json.loads(await f.read())
            
            offline = OfflineData(**data)
            self._offline_data[document_id] = offline
            return offline
        except Exception as e:
            logger.warning(f"Çevrimdışı veri yükleme hatası: {e}")
            return None
    
    def get_pending_sync(self) -> List[str]:
        """Sync bekleyen dökümanları al."""
        return self._pending_sync.copy()
    
    async def mark_synced(self, document_id: str):
        """Sync edildi olarak işaretle."""
        if document_id in self._pending_sync:
            self._pending_sync.remove(document_id)
        
        if document_id in self._offline_data:
            self._offline_data[document_id].sync_required = False
        
        # Dosyayı sil
        filepath = self.offline_dir / f"{document_id}.offline.json"
        if filepath.exists():
            filepath.unlink()


# ============================================================================
# PARTIAL EXPORT MANAGER
# ============================================================================

class PartialExportManager:
    """
    Kısmi Export Yöneticisi
    
    Tamamlanmamış dökümanları PDF olarak export eder.
    """
    
    def __init__(self, export_dir: str = "data/exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_partial_export(
        self,
        checkpoint: ResilienceCheckpoint
    ) -> str:
        """Kısmi export oluştur."""
        
        # Markdown içeriği al
        content = checkpoint.get_partial_content()
        
        # Export bilgisi ekle
        export_info = f"""
---
## Export Bilgisi

- **Üretim Durumu:** {checkpoint.state}
- **İlerleme:** {checkpoint.progress}%
- **Tamamlanan Bölümler:** {len(checkpoint.completed_sections)}
- **Son Kayıt:** {checkpoint.updated_at}

*Bu döküman otomatik olarak kaydedilmiştir. Üretim devam etmektedir veya durdurulmuştur.*
"""
        
        full_content = content + export_info
        
        # Dosya kaydet
        safe_title = "".join(c for c in checkpoint.config.get('title', 'partial') 
                           if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_{checkpoint.document_id[:8]}_partial.md"
        filepath = self.export_dir / filename
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(full_content)
        
        return str(filepath)
    
    async def export_to_html(self, checkpoint: ResilienceCheckpoint) -> str:
        """HTML olarak export et."""
        import markdown
        
        content = checkpoint.get_partial_content()
        
        html_template = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{checkpoint.config.get('title', 'Döküman')} - Kısmi Export</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3 {{ color: #1a1a1a; }}
        .progress-banner {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .progress-bar {{
            background: rgba(255,255,255,0.3);
            border-radius: 10px;
            height: 10px;
            margin-top: 10px;
        }}
        .progress-fill {{
            background: white;
            height: 100%;
            border-radius: 10px;
            width: {checkpoint.progress}%;
        }}
        blockquote {{
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin-left: 0;
            color: #666;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        pre {{
            background: #1a1a1a;
            color: #f4f4f4;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="progress-banner">
        <strong>⚡ Kısmi Export</strong> - İlerleme: {checkpoint.progress}%
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
    </div>
    {markdown.markdown(content, extensions=['tables', 'fenced_code'])}
</body>
</html>
"""
        
        safe_title = "".join(c for c in checkpoint.config.get('title', 'partial') 
                           if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}_{checkpoint.document_id[:8]}_partial.html"
        filepath = self.export_dir / filename
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(html_template)
        
        return str(filepath)


# ============================================================================
# CONNECTION RESILIENCE MANAGER
# ============================================================================

class ConnectionResilienceManager:
    """
    Bağlantı Dayanıklılık Yöneticisi
    
    WebSocket ve HTTP bağlantılarını yönetir.
    Otomatik yeniden bağlanma sağlar.
    """
    
    def __init__(self):
        self._connection_states: Dict[str, Dict] = {}
        self._reconnect_attempts: Dict[str, int] = {}
        self._max_reconnect_attempts = 5
        self._reconnect_delays = [1, 2, 5, 10, 30]  # saniye
        
    def on_disconnect(self, document_id: str) -> Dict:
        """Bağlantı kesildiğinde."""
        
        if document_id not in self._reconnect_attempts:
            self._reconnect_attempts[document_id] = 0
        
        self._reconnect_attempts[document_id] += 1
        attempt = self._reconnect_attempts[document_id]
        
        can_reconnect = attempt <= self._max_reconnect_attempts
        delay = self._reconnect_delays[min(attempt - 1, len(self._reconnect_delays) - 1)]
        
        self._connection_states[document_id] = {
            "connected": False,
            "attempt": attempt,
            "can_reconnect": can_reconnect,
            "next_retry_delay": delay if can_reconnect else None,
            "disconnected_at": datetime.now().isoformat()
        }
        
        return self._connection_states[document_id]
    
    def on_connect(self, document_id: str):
        """Bağlantı kurulduğunda."""
        self._reconnect_attempts[document_id] = 0
        self._connection_states[document_id] = {
            "connected": True,
            "attempt": 0,
            "connected_at": datetime.now().isoformat()
        }
    
    def get_reconnect_delay(self, document_id: str) -> int:
        """Yeniden bağlanma gecikmesini al."""
        attempt = self._reconnect_attempts.get(document_id, 0)
        if attempt >= self._max_reconnect_attempts:
            return -1  # Artık deneme
        return self._reconnect_delays[min(attempt, len(self._reconnect_delays) - 1)]
    
    def reset(self, document_id: str):
        """Durumu sıfırla."""
        self._reconnect_attempts.pop(document_id, None)
        self._connection_states.pop(document_id, None)


# ============================================================================
# DEEP SCHOLAR RESILIENCE SERVICE
# ============================================================================

class DeepScholarResilienceService:
    """
    Ana Dayanıklılık Servisi
    
    Tüm resilience özelliklerini koordine eder.
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
        
        self.auto_save = AutoSaveManager()
        self.checkpoint = CheckpointManager()
        self.error_recovery = ErrorRecoveryManager()
        self.queue = GenerationQueueManager()
        self.offline = OfflineModeManager()
        self.partial_export = PartialExportManager()
        self.connection = ConnectionResilienceManager()
        
        # Event callbacks
        self._event_callbacks: List[Callable] = []
        
        self._initialized = True
    
    def add_event_callback(self, callback: Callable):
        """Event callback ekle."""
        self._event_callbacks.append(callback)
    
    async def emit_event(self, event_type: ResilienceEventType, data: Dict):
        """Event yayınla."""
        event = {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(f"Resilience callback hatası: {e}")
    
    async def on_section_complete(
        self,
        document_id: str,
        workspace_id: str,
        config: Dict[str, Any],
        section_id: str,
        section_title: str,
        content: str,
        progress: int,
        current_phase: str,
        section_index: int,
        completed_sections: List[Dict],
        section_contents: Dict[str, str],
        research_data: Dict = None,
        citations: List[Dict] = None,
        visuals: List[Dict] = None
    ):
        """Bölüm tamamlandığında çağrılır."""
        
        # Auto-save
        await self.auto_save.save_section(
            document_id=document_id,
            section_id=section_id,
            section_title=section_title,
            content=content
        )
        
        # Checkpoint güncelle
        await self.checkpoint.create_checkpoint(
            document_id=document_id,
            workspace_id=workspace_id,
            config=config,
            state=GenerationState.WRITING,
            progress=progress,
            current_phase=current_phase,
            current_section_index=section_index,
            completed_sections=completed_sections,
            section_contents=section_contents,
            research_data=research_data,
            citations=citations,
            visuals=visuals
        )
        
        # Event yayınla
        await self.emit_event(ResilienceEventType.AUTO_SAVED, {
            "document_id": document_id,
            "section_id": section_id,
            "section_title": section_title,
            "progress": progress,
            "word_count": self.auto_save.get_word_count(document_id)
        })
    
    async def on_error(
        self,
        document_id: str,
        error: Exception,
        context: Dict[str, Any]
    ) -> RecoveryStrategy:
        """Hata oluştuğunda çağrılır."""
        
        strategy = await self.error_recovery.handle_error(
            document_id=document_id,
            error=error,
            context=context
        )
        
        await self.emit_event(ResilienceEventType.ERROR_RECOVERED, {
            "document_id": document_id,
            "error": str(error),
            "strategy": strategy.value,
            "retry_count": self.error_recovery._error_counts.get(document_id, 0)
        })
        
        return strategy
    
    async def on_disconnect(self, document_id: str, state: Dict[str, Any]):
        """Bağlantı kesildiğinde çağrılır."""
        
        # Connection durumunu güncelle
        conn_state = self.connection.on_disconnect(document_id)
        
        # Offline veri kaydet
        await self.offline.save_offline_state(document_id, state)
        
        await self.emit_event(ResilienceEventType.CONNECTION_LOST, {
            "document_id": document_id,
            "can_reconnect": conn_state["can_reconnect"],
            "retry_delay": conn_state.get("next_retry_delay")
        })
        
        return conn_state
    
    async def on_reconnect(self, document_id: str):
        """Yeniden bağlandığında çağrılır."""
        
        self.connection.on_connect(document_id)
        
        # Offline sync
        await self.offline.mark_synced(document_id)
        
        await self.emit_event(ResilienceEventType.CONNECTION_RESTORED, {
            "document_id": document_id
        })
    
    async def get_partial_export(self, document_id: str) -> Optional[str]:
        """Kısmi export al."""
        checkpoint = await self.checkpoint.load_checkpoint(document_id)
        
        if not checkpoint:
            return None
        
        filepath = await self.partial_export.create_partial_export(checkpoint)
        
        await self.emit_event(ResilienceEventType.PARTIAL_EXPORT_READY, {
            "document_id": document_id,
            "filepath": filepath,
            "progress": checkpoint.progress
        })
        
        return filepath
    
    async def cleanup(self, document_id: str):
        """Temizlik yap."""
        await self.auto_save.clear_cache(document_id)
        await self.checkpoint.delete_checkpoint(document_id)
        self.error_recovery.reset_error_count(document_id)
        self.connection.reset(document_id)


# Singleton instance
resilience_service = DeepScholarResilienceService()
