"""
RealTimeStreaming - Gerçek Zamanlı İçerik Akışı
==============================================

Paragraf paragraf streaming, canlı önizleme ve ETA hesaplama.

Özellikler:
- Paragraf bazlı streaming
- Kelime sayısı takibi
- ETA (tahmini bitiş süresi) hesaplama
- Live markdown render desteği
- Progress tracking
- Checkpoint entegrasyonu
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import re

from core.logger import get_logger

logger = get_logger("realtime_streaming")


class StreamingEventType(str, Enum):
    """Streaming event tipleri."""
    STREAM_START = "stream_start"
    PARAGRAPH_CHUNK = "paragraph_chunk"
    PARAGRAPH_COMPLETE = "paragraph_complete"
    SECTION_PROGRESS = "section_progress"
    WORD_COUNT_UPDATE = "word_count_update"
    ETA_UPDATE = "eta_update"
    PREVIEW_UPDATE = "preview_update"
    STREAM_COMPLETE = "stream_complete"
    STREAM_ERROR = "stream_error"


@dataclass
class StreamingEvent:
    """Streaming eventi."""
    type: StreamingEventType
    timestamp: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "timestamp": self.timestamp,
            **self.data
        }


@dataclass
class ParagraphChunk:
    """Paragraf parçası."""
    paragraph_index: int
    chunk_index: int
    text: str
    is_complete: bool
    word_count: int
    
    def to_dict(self) -> Dict:
        return {
            "paragraph_index": self.paragraph_index,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "is_complete": self.is_complete,
            "word_count": self.word_count
        }


@dataclass
class StreamingMetrics:
    """Streaming metrikleri."""
    start_time: float
    current_time: float
    total_words: int
    target_words: int
    words_per_minute: float
    estimated_remaining_minutes: float
    progress_percentage: float
    sections_completed: int
    sections_total: int
    
    def to_dict(self) -> Dict:
        return {
            "elapsed_seconds": int(self.current_time - self.start_time),
            "total_words": self.total_words,
            "target_words": self.target_words,
            "words_per_minute": round(self.words_per_minute, 1),
            "eta_minutes": round(self.estimated_remaining_minutes, 1),
            "progress": round(self.progress_percentage, 1),
            "sections_completed": self.sections_completed,
            "sections_total": self.sections_total
        }


class ETACalculator:
    """Tahmini bitiş süresi hesaplayıcı."""
    
    def __init__(self, target_words: int, target_sections: int):
        self.target_words = target_words
        self.target_sections = target_sections
        
        self.start_time = time.time()
        self.word_history: List[tuple] = []  # (timestamp, cumulative_words)
        self.section_times: List[float] = []  # Her bölüm için geçen süre
        
        self.last_update_time = self.start_time
        self.smoothing_window = 5  # Son N ölçümü kullan
    
    def update(self, current_words: int, sections_completed: int) -> Dict[str, Any]:
        """
        İlerlemeyi güncelle ve ETA hesapla.
        
        Args:
            current_words: Mevcut kelime sayısı
            sections_completed: Tamamlanan bölüm sayısı
        
        Returns:
            ETA bilgileri
        """
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Word history güncelle
        self.word_history.append((current_time, current_words))
        
        # Sadece son N kayıtı tut
        if len(self.word_history) > self.smoothing_window * 2:
            self.word_history = self.word_history[-self.smoothing_window * 2:]
        
        # Kelime hızı hesapla (son window üzerinden)
        if len(self.word_history) >= 2:
            recent_history = self.word_history[-self.smoothing_window:]
            time_diff = recent_history[-1][0] - recent_history[0][0]
            word_diff = recent_history[-1][1] - recent_history[0][1]
            
            if time_diff > 0:
                words_per_second = word_diff / time_diff
                words_per_minute = words_per_second * 60
            else:
                words_per_minute = 0
        else:
            words_per_minute = current_words / max(elapsed / 60, 0.1)
        
        # Kalan kelime ve süre
        remaining_words = max(0, self.target_words - current_words)
        
        if words_per_minute > 0:
            estimated_remaining_minutes = remaining_words / words_per_minute
        else:
            # Fallback: ortalama hesapla
            if elapsed > 0 and current_words > 0:
                avg_wpm = (current_words / elapsed) * 60
                estimated_remaining_minutes = remaining_words / max(avg_wpm, 1)
            else:
                estimated_remaining_minutes = 999  # Bilinmiyor
        
        # Progress yüzdesi
        if self.target_words > 0:
            word_progress = (current_words / self.target_words) * 100
        else:
            word_progress = 0
        
        if self.target_sections > 0:
            section_progress = (sections_completed / self.target_sections) * 100
        else:
            section_progress = 0
        
        # Ağırlıklı progress (kelime %70, bölüm %30)
        overall_progress = word_progress * 0.7 + section_progress * 0.3
        
        self.last_update_time = current_time
        
        return {
            "elapsed_seconds": int(elapsed),
            "elapsed_formatted": self._format_time(elapsed),
            "words_per_minute": round(words_per_minute, 1),
            "eta_minutes": round(estimated_remaining_minutes, 1),
            "eta_formatted": self._format_time(estimated_remaining_minutes * 60),
            "progress": round(overall_progress, 1),
            "word_progress": round(word_progress, 1),
            "section_progress": round(section_progress, 1),
            "remaining_words": remaining_words,
            "current_words": current_words,
            "target_words": self.target_words
        }
    
    def _format_time(self, seconds: float) -> str:
        """Süreyi formatla."""
        if seconds < 0 or seconds > 36000:  # 10 saatten fazla
            return "∞"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}s {minutes}dk"
        elif minutes > 0:
            return f"{minutes}dk {secs}sn"
        else:
            return f"{secs}sn"


class RealTimeStreamingManager:
    """
    Gerçek Zamanlı Streaming Yöneticisi
    
    İçeriği paragraf paragraf stream eder, 
    kelime sayısını ve ETA'yı takip eder.
    """
    
    def __init__(
        self,
        target_pages: int,
        target_sections: int,
        words_per_page: int = 300,
        event_callback: Optional[Callable] = None
    ):
        self.target_pages = target_pages
        self.target_sections = target_sections
        self.words_per_page = words_per_page
        self.target_words = target_pages * words_per_page
        self.event_callback = event_callback
        
        # Metrics
        self.eta_calculator = ETACalculator(self.target_words, target_sections)
        
        # State
        self.current_section = 0
        self.current_paragraph = 0
        self.total_words = 0
        self.sections_completed = 0
        
        # Content buffer
        self.content_buffer: List[str] = []
        self.section_contents: Dict[int, str] = {}
        
        # Stream state
        self.is_streaming = False
        self.last_event_time = time.time()
    
    async def _emit_event(self, event_type: StreamingEventType, data: Dict):
        """Event gönder."""
        event = StreamingEvent(
            type=event_type,
            timestamp=datetime.now().isoformat(),
            data=data
        )
        
        if self.event_callback:
            await self.event_callback(event.to_dict())
        
        self.last_event_time = time.time()
    
    async def start_streaming(self, section_id: int, section_title: str):
        """Streaming başlat."""
        self.is_streaming = True
        self.current_section = section_id
        self.current_paragraph = 0
        
        await self._emit_event(StreamingEventType.STREAM_START, {
            "section_id": section_id,
            "section_title": section_title,
            "target_words": self.target_words,
            "message": f"📄 Bölüm {section_id + 1} yazılıyor: {section_title}"
        })
    
    async def stream_paragraph(
        self,
        content: str,
        section_id: int,
        is_final: bool = False
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Paragrafı chunk'lar halinde stream et.
        
        Args:
            content: Paragraf içeriği
            section_id: Bölüm ID
            is_final: Son paragraf mı
        
        Yields:
            StreamingEvent'ler
        """
        # Paragrafı cümlelere böl
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        chunk_text = ""
        chunk_index = 0
        
        for i, sentence in enumerate(sentences):
            chunk_text += sentence + " "
            
            # Her 2-3 cümlede bir chunk gönder
            if (i + 1) % 2 == 0 or i == len(sentences) - 1:
                word_count = len(chunk_text.split())
                self.total_words += word_count
                
                chunk = ParagraphChunk(
                    paragraph_index=self.current_paragraph,
                    chunk_index=chunk_index,
                    text=chunk_text.strip(),
                    is_complete=(i == len(sentences) - 1),
                    word_count=word_count
                )
                
                # Chunk event
                event = StreamingEvent(
                    type=StreamingEventType.PARAGRAPH_CHUNK,
                    timestamp=datetime.now().isoformat(),
                    data={
                        "section_id": section_id,
                        "chunk": chunk.to_dict(),
                        "total_words": self.total_words
                    }
                )
                yield event
                
                # ETA güncelle
                eta_info = self.eta_calculator.update(self.total_words, self.sections_completed)
                
                eta_event = StreamingEvent(
                    type=StreamingEventType.ETA_UPDATE,
                    timestamp=datetime.now().isoformat(),
                    data=eta_info
                )
                yield eta_event
                
                chunk_text = ""
                chunk_index += 1
                
                # Küçük gecikme (streaming efekti)
                await asyncio.sleep(0.05)
        
        # Paragraf tamamlandı
        self.current_paragraph += 1
        self.content_buffer.append(content)
        
        complete_event = StreamingEvent(
            type=StreamingEventType.PARAGRAPH_COMPLETE,
            timestamp=datetime.now().isoformat(),
            data={
                "section_id": section_id,
                "paragraph_index": self.current_paragraph - 1,
                "is_final": is_final
            }
        )
        yield complete_event
    
    async def complete_section(
        self,
        section_id: int,
        section_title: str,
        full_content: str
    ):
        """Bölümü tamamla."""
        self.sections_completed += 1
        self.section_contents[section_id] = full_content
        
        # Word count güncelle
        section_words = len(full_content.split())
        
        await self._emit_event(StreamingEventType.SECTION_PROGRESS, {
            "section_id": section_id,
            "section_title": section_title,
            "section_words": section_words,
            "total_words": self.total_words,
            "sections_completed": self.sections_completed,
            "sections_total": self.target_sections,
            "message": f"✅ Bölüm tamamlandı: {section_title} ({section_words} kelime)"
        })
        
        # Preview güncelle
        preview_content = self._generate_preview()
        
        await self._emit_event(StreamingEventType.PREVIEW_UPDATE, {
            "preview": preview_content,
            "word_count": self.total_words,
            "sections_completed": self.sections_completed
        })
    
    def _generate_preview(self) -> str:
        """Önizleme içeriği oluştur."""
        preview_parts = []
        
        for section_id, content in sorted(self.section_contents.items()):
            # İlk 500 karakteri al
            preview = content[:500]
            if len(content) > 500:
                preview += "..."
            preview_parts.append(preview)
        
        return "\n\n---\n\n".join(preview_parts)
    
    async def complete_streaming(self, final_document: Dict):
        """Streaming tamamla."""
        self.is_streaming = False
        
        final_eta = self.eta_calculator.update(self.total_words, self.sections_completed)
        
        await self._emit_event(StreamingEventType.STREAM_COMPLETE, {
            "total_words": self.total_words,
            "target_words": self.target_words,
            "sections_completed": self.sections_completed,
            "elapsed": final_eta["elapsed_formatted"],
            "final_document": final_document,
            "message": f"🎉 Döküman tamamlandı: {self.total_words} kelime"
        })
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Mevcut metrikleri al."""
        eta_info = self.eta_calculator.update(self.total_words, self.sections_completed)
        
        return {
            "total_words": self.total_words,
            "target_words": self.target_words,
            "sections_completed": self.sections_completed,
            "sections_total": self.target_sections,
            "is_streaming": self.is_streaming,
            **eta_info
        }
    
    def to_event(self) -> Dict[str, Any]:
        """WebSocket event formatına dönüştür."""
        metrics = self.get_current_metrics()
        
        return {
            "type": "streaming_metrics",
            "timestamp": datetime.now().isoformat(),
            **metrics
        }
