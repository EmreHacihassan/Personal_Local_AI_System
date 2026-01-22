"""
DeepScholar v2.0 - API Endpoints
=================================

Premium döküman üretim sistemi için API.

Özellikler:
- Fraktal araştırma mimarisi
- Multi-agent koordinasyonu
- Akademik kaynak entegrasyonu
- Canlı WebSocket ilerleme takibi
- PDF export
- Çoklu dil desteği
- Premium Resilience (Auto-Save, Checkpoint, Error Recovery)
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import asyncio
import os
import tempfile
import traceback

from core.deep_scholar import (
    DeepScholarOrchestrator,
    DeepScholarConfig,
    DocumentLanguage,
    CitationStyle,
    EventType,
    PDFExporter
)
from core.learning_workspace import learning_workspace_manager, DocumentStatus

# Premium Resilience Integration
try:
    from core.deep_scholar_resilience import (
        resilience_service,
        ResilienceEventType,
        GenerationState
    )
    RESILIENCE_ENABLED = True
except ImportError:
    RESILIENCE_ENABLED = False
    print("[DeepScholar] Resilience module not available")


router = APIRouter(prefix="/api/deep-scholar", tags=["DeepScholar"])


# ==================== PYDANTIC MODELS ====================

class CreateDeepDocumentRequest(BaseModel):
    """DeepScholar döküman oluşturma isteği."""
    title: str = Field(..., min_length=1, max_length=300)
    topic: str = Field(..., min_length=1, max_length=1000)
    page_count: int = Field(..., ge=1, le=60)  # Maksimum 60 sayfa
    
    # Dil ve stil
    language: str = Field(default="tr")  # tr, en, de
    style: str = Field(default="academic")  # academic, casual, detailed, summary, exam_prep
    citation_style: str = Field(default="apa")  # apa, ieee, chicago, harvard
    
    # Araştırma ayarları
    web_search: str = Field(default="auto")  # off, auto, on
    academic_search: bool = Field(default=True)
    max_sources_per_section: int = Field(default=10, ge=1, le=20)
    
    # Kalite ayarları
    enable_fact_checking: bool = Field(default=True)
    enable_user_proxy: bool = Field(default=True)
    enable_conflict_detection: bool = Field(default=True)
    
    # Kullanıcı talimatları
    custom_instructions: str = Field(default="", max_length=5000)
    user_persona: str = Field(default="", max_length=500)
    
    # Gelişmiş
    parallel_research: bool = Field(default=True)
    max_research_depth: int = Field(default=3, ge=1, le=5)


class ExportPDFRequest(BaseModel):
    """PDF export isteği."""
    document_id: str
    language: str = Field(default="tr")


# ==================== ACTIVE GENERATIONS & QUEUE ====================

# Aktif üretim süreçlerini takip et
_active_deep_generations: Dict[str, Dict] = {}

# Queue işlemci durumu
_queue_processor_running = False
_queue_processor_task = None


async def _process_queue_item(document_id: str, workspace_id: str, config: 'DeepScholarConfig'):
    """
    Kuyruktan alınan dökümanı işle.
    WebSocket bağlantısı beklemeden arka planda çalışır.
    """
    from core.deep_scholar import DeepScholarOrchestrator, EventType
    
    try:
        # Orchestrator oluştur
        orchestrator = DeepScholarOrchestrator()
        
        gen_state = _active_deep_generations.get(document_id)
        if gen_state:
            gen_state["orchestrator"] = orchestrator
            gen_state["status"] = "generating"
        
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.status = DocumentStatus.GENERATING
            document.generation_log.append(f"[{datetime.now().isoformat()}] 🚀 DeepScholar v2.0 başlatıldı (Queue)")
            learning_workspace_manager.update_document(document)
        
        # Event callback - state güncelle
        async def update_state(event: Dict):
            if not gen_state:
                return
            
            event_type = event.get("type", "")
            gen_state["events"].append(event)
            gen_state["progress"] = event.get("progress", gen_state["progress"])
            gen_state["current_phase"] = event.get("phase", gen_state.get("current_phase", ""))
            gen_state["current_agent"] = event.get("agent", gen_state.get("current_agent", ""))
            
            # Bölüm tamamlandıysa
            if event_type in ["section_written", "section_complete"]:
                section_data = {
                    "id": event.get("section_id", ""),
                    "title": event.get("section_title", ""),
                    "content": event.get("content", ""),
                    "wordCount": event.get("word_count", 0),
                    "level": event.get("level", 1)
                }
                gen_state["completed_sections"].append(section_data)
                
                # Resilience: Auto-save
                if RESILIENCE_ENABLED:
                    try:
                        config_dict = {k: str(v) if hasattr(v, 'value') else v 
                                     for k, v in config.__dict__.items()}
                        section_contents = {s.get("id", ""): s.get("content", "") 
                                          for s in gen_state["completed_sections"]}
                        
                        await resilience_service.on_section_complete(
                            document_id=document_id,
                            workspace_id=workspace_id,
                            config=config_dict,
                            section_id=section_data["id"],
                            section_title=section_data["title"],
                            content=section_data["content"],
                            progress=gen_state["progress"],
                            current_phase=gen_state["current_phase"],
                            section_index=len(gen_state["completed_sections"]),
                            completed_sections=gen_state["completed_sections"],
                            section_contents=section_contents,
                            visuals=gen_state.get("generated_visuals", [])
                        )
                    except Exception as e:
                        print(f"[Queue Resilience Error] {e}")
            
            # Agent düşüncesi
            if event_type == "agent_thinking":
                gen_state["agent_thoughts"].append({
                    "agent": event.get("agent", ""),
                    "thought": event.get("thought", ""),
                    "timestamp": datetime.now().isoformat()
                })
            
            # Görsel
            if event_type == "visual_generated":
                gen_state["generated_visuals"].append({
                    "type": event.get("visual_type", ""),
                    "title": event.get("visual_title", ""),
                    "code": event.get("visual", {}).get("code", ""),
                    "render_type": event.get("visual", {}).get("render_type", "")
                })
        
        orchestrator.set_event_callback(update_state)
        
        # Üretimi başlat
        final_document = None
        async for event in orchestrator.generate_document(config):
            await update_state(event)
            
            if event.get("type") == EventType.COMPLETE.value:
                final_document = event.get("document", {})
                gen_state["status"] = "completed"
            elif event.get("type") == EventType.ERROR.value:
                gen_state["status"] = "failed"
        
        # Dökümanı güncelle
        if final_document:
            document = learning_workspace_manager.get_document(document_id)
            if document:
                document.content = final_document.get("content", "")
                document.status = DocumentStatus.COMPLETED
                document.word_count = final_document.get("word_count", 0)
                document.generation_log.append(f"[{datetime.now().isoformat()}] ✅ Tamamlandı")
                learning_workspace_manager.update_document(document)
        
        # Queue'da tamamlandı işaretle
        if RESILIENCE_ENABLED:
            resilience_service.queue.mark_completed(document_id, success=gen_state.get("status") == "completed")
        
        return True
        
    except Exception as e:
        print(f"[Queue Process Error] {document_id}: {e}")
        traceback.print_exc()
        
        if RESILIENCE_ENABLED:
            resilience_service.queue.mark_completed(document_id, success=False)
        
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.status = DocumentStatus.ERROR
            document.generation_log.append(f"[{datetime.now().isoformat()}] ❌ Hata: {str(e)}")
            learning_workspace_manager.update_document(document)
        
        return False
    finally:
        # State'i temizle (tamamlandıysa)
        gen_state = _active_deep_generations.get(document_id)
        if gen_state and gen_state.get("status") in ["completed", "failed"]:
            # 5 dakika sonra temizle (reconnect için)
            await asyncio.sleep(300)
            _active_deep_generations.pop(document_id, None)


async def _queue_processor():
    """
    Arka plan kuyruk işlemcisi.
    Sıradaki dökümanları sırayla işler.
    """
    global _queue_processor_running
    
    print("[Queue] Processor started")
    
    while _queue_processor_running:
        try:
            if RESILIENCE_ENABLED:
                # Sıradaki öğeyi al
                next_item = resilience_service.queue.get_next()
                
                if next_item:
                    print(f"[Queue] Processing: {next_item.id} - {next_item.config.get('title', 'Untitled')}")
                    
                    # Config'i DeepScholarConfig'e dönüştür
                    from core.deep_scholar import DeepScholarConfig, DocumentLanguage, CitationStyle
                    
                    config_dict = next_item.config
                    
                    # Enum dönüşümleri
                    try:
                        language = DocumentLanguage(config_dict.get("language", "tr"))
                    except:
                        language = DocumentLanguage.TURKISH
                    
                    try:
                        citation_style = CitationStyle(config_dict.get("citation_style", "apa"))
                    except:
                        citation_style = CitationStyle.APA
                    
                    config = DeepScholarConfig(
                        title=config_dict.get("title", ""),
                        topic=config_dict.get("topic", ""),
                        page_count=config_dict.get("page_count", 10),
                        language=language,
                        citation_style=citation_style,
                        style=config_dict.get("style", "academic"),
                        web_search=config_dict.get("web_search", "auto"),
                        academic_search=config_dict.get("academic_search", True),
                        max_sources_per_section=config_dict.get("max_sources_per_section", 10),
                        enable_fact_checking=config_dict.get("enable_fact_checking", True),
                        enable_user_proxy=config_dict.get("enable_user_proxy", True),
                        enable_conflict_detection=config_dict.get("enable_conflict_detection", True),
                        custom_instructions=config_dict.get("custom_instructions", ""),
                        user_persona=config_dict.get("user_persona", ""),
                        parallel_research=config_dict.get("parallel_research", True),
                        max_research_depth=config_dict.get("max_research_depth", 3)
                    )
                    
                    # Generation state oluştur
                    _active_deep_generations[next_item.id] = {
                        "config": config,
                        "status": "starting",
                        "progress": 0,
                        "current_phase": "",
                        "current_agent": "",
                        "events": [],
                        "completed_sections": [],
                        "agent_thoughts": [],
                        "generated_visuals": [],
                        "started_at": datetime.now().isoformat(),
                        "orchestrator": None,
                        "websocket_connected": False,
                        "queued": True
                    }
                    
                    # İşle
                    await _process_queue_item(next_item.id, next_item.workspace_id, config)
                    
                    print(f"[Queue] Completed: {next_item.id}")
                else:
                    # Kuyruk boş, bekle
                    await asyncio.sleep(2)
            else:
                await asyncio.sleep(5)
                
        except Exception as e:
            print(f"[Queue Processor Error] {e}")
            traceback.print_exc()
            await asyncio.sleep(5)
    
    print("[Queue] Processor stopped")


def _ensure_queue_processor():
    """Queue processor'ın çalıştığından emin ol."""
    global _queue_processor_running, _queue_processor_task
    
    if not _queue_processor_running:
        _queue_processor_running = True
        _queue_processor_task = asyncio.create_task(_queue_processor())
        print("[Queue] Processor task created")


# ==================== ENDPOINTS ====================

@router.get("/info")
async def get_deep_scholar_info():
    """DeepScholar v2.0 hakkında bilgi."""
    return {
        "version": "2.0",
        "name": "DeepScholar",
        "description": "Premium akademik döküman üretim sistemi",
        "features": [
            "Fraktal Araştırma (Fractal Expansion)",
            "Multi-Agent Mimari (Planner, Researcher, Writer, Fact-Checker, User Proxy, Synthesizer)",
            "Akademik Kaynak Entegrasyonu (Semantic Scholar, arXiv, CrossRef)",
            "Information Gain Algoritması",
            "Cross-Pollination Sentez Motoru",
            "Self-Correction Loop",
            "Canlı WebSocket İlerleme Takibi",
            "PDF Export",
            "Çoklu Dil Desteği (TR, EN, DE)",
            "Akademik Kaynakça (APA, IEEE, Chicago, Harvard)"
        ],
        "max_pages": 60,
        "supported_languages": ["tr", "en", "de"],
        "citation_styles": ["apa", "ieee", "chicago", "harvard"],
        "document_styles": ["academic", "casual", "detailed", "summary", "exam_prep"]
    }


@router.get("/config-options")
async def get_config_options():
    """Mevcut yapılandırma seçeneklerini getir."""
    return {
        "languages": [
            {"value": "tr", "label": "Türkçe", "flag": "🇹🇷"},
            {"value": "en", "label": "English", "flag": "🇬🇧"},
            {"value": "de", "label": "Deutsch", "flag": "🇩🇪"}
        ],
        "citation_styles": [
            {"value": "apa", "label": "APA Style", "description": "American Psychological Association"},
            {"value": "ieee", "label": "IEEE", "description": "Institute of Electrical and Electronics Engineers"},
            {"value": "chicago", "label": "Chicago", "description": "Chicago Manual of Style"},
            {"value": "harvard", "label": "Harvard", "description": "Harvard Referencing"}
        ],
        "document_styles": [
            {"value": "academic", "label": "Akademik", "description": "Formal, detaylı, teknik dil"},
            {"value": "casual", "label": "Samimi", "description": "Anlaşılır, akıcı, günlük dil"},
            {"value": "detailed", "label": "Detaylı", "description": "Her detayı açıklayan, kapsamlı"},
            {"value": "summary", "label": "Özet", "description": "Ana noktaları vurgulayan, kısa"},
            {"value": "exam_prep", "label": "Sınav Hazırlık", "description": "Önemli noktalar, test odaklı"}
        ],
        "page_limits": {
            "min": 1,
            "max": 60,
            "default": 10,
            "research_depth_thresholds": {
                "shallow": "1-5 sayfa",
                "moderate": "6-15 sayfa",
                "deep": "16-30 sayfa",
                "exhaustive": "31-60 sayfa"
            }
        },
        "web_search_options": [
            {"value": "off", "label": "Kapalı", "description": "Web araması yapma"},
            {"value": "auto", "label": "Otomatik", "description": "Gerektiğinde ara"},
            {"value": "on", "label": "Açık", "description": "Her bölüm için ara"}
        ]
    }


@router.post("/generate")
async def start_deep_generation(
    workspace_id: str,
    request: CreateDeepDocumentRequest
):
    """
    DeepScholar döküman üretimini başlat.
    
    Kuyruğa ekler, sıra gelince otomatik başlar.
    Döküman ID'si döndürür, ilerleme WebSocket üzerinden takip edilir.
    """
    import uuid
    
    # Workspace kontrolü
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    # Dil enum'a çevir
    try:
        language = DocumentLanguage(request.language)
    except ValueError:
        language = DocumentLanguage.TURKISH
    
    try:
        citation_style = CitationStyle(request.citation_style)
    except ValueError:
        citation_style = CitationStyle.APA
    
    # Config dict olarak sakla (queue için)
    config_dict = {
        "title": request.title,
        "topic": request.topic,
        "page_count": request.page_count,
        "language": request.language,
        "citation_style": request.citation_style,
        "style": request.style,
        "web_search": request.web_search,
        "academic_search": request.academic_search,
        "max_sources_per_section": request.max_sources_per_section,
        "enable_fact_checking": request.enable_fact_checking,
        "enable_user_proxy": request.enable_user_proxy,
        "enable_conflict_detection": request.enable_conflict_detection,
        "custom_instructions": request.custom_instructions,
        "user_persona": request.user_persona,
        "parallel_research": request.parallel_research,
        "max_research_depth": request.max_research_depth
    }
    
    # Döküman oluştur
    document = learning_workspace_manager.create_document(
        workspace_id=workspace_id,
        title=request.title,
        topic=request.topic,
        page_count=request.page_count,
        style=request.style
    )
    
    document_id = document.id
    
    # Kuyruğa ekle
    queue_position = 1
    is_immediate = True
    
    if RESILIENCE_ENABLED:
        # Queue processor'ı başlat
        _ensure_queue_processor()
        
        # Mevcut aktif üretim var mı kontrol et
        active_count = len([g for g in _active_deep_generations.values() 
                           if g.get("status") in ["starting", "generating"]])
        
        # Kuyruğa ekle
        queued = resilience_service.queue.add_to_queue(
            generation_id=document_id,
            workspace_id=workspace_id,
            config=config_dict,
            priority=1
        )
        queue_position = queued.position
        is_immediate = active_count == 0 and queue_position == 1
        
        # Döküman durumunu güncelle
        document.generation_log.append(
            f"[{datetime.now().isoformat()}] 📋 Kuyruğa eklendi (Sıra: {queue_position})"
        )
        if not is_immediate:
            document.status = DocumentStatus.DRAFT  # Beklemede
        learning_workspace_manager.update_document(document)
    else:
        # Resilience yoksa eski davranış - hemen başlat
        config = DeepScholarConfig(
            title=request.title,
            topic=request.topic,
            page_count=request.page_count,
            language=language,
            citation_style=citation_style,
            style=request.style,
            web_search=request.web_search,
            academic_search=request.academic_search,
            max_sources_per_section=request.max_sources_per_section,
            enable_fact_checking=request.enable_fact_checking,
            enable_user_proxy=request.enable_user_proxy,
            enable_conflict_detection=request.enable_conflict_detection,
            custom_instructions=request.custom_instructions,
            user_persona=request.user_persona,
            parallel_research=request.parallel_research,
            max_research_depth=request.max_research_depth
        )
        
        _active_deep_generations[document_id] = {
            "config": config,
            "status": "starting",
            "progress": 0,
            "current_phase": "",
            "current_agent": "",
            "events": [],
            "completed_sections": [],
            "agent_thoughts": [],
            "generated_visuals": [],
            "started_at": datetime.now().isoformat(),
            "orchestrator": None,
            "websocket_connected": False
        }
    
    return {
        "success": True,
        "document_id": document_id,
        "message": "Kuyruğa eklendi" if not is_immediate else "DeepScholar üretimi başlatıldı",
        "queue_position": queue_position,
        "is_immediate": is_immediate,
        "websocket_url": f"/api/deep-scholar/ws/{document_id}"
    }


@router.websocket("/ws/{document_id}")
async def deep_scholar_websocket(websocket: WebSocket, document_id: str):
    """
    DeepScholar ilerleme WebSocket.
    
    Gerçek zamanlı olarak:
    - Agent mesajları
    - Araştırma sonuçları
    - Bölüm ilerlemesi
    - Conflict tespitleri
    - Fact-check sonuçları
    - User Proxy feedback
    
    Reconnect desteği: Eğer üretim devam ediyorsa mevcut state gönderilir.
    """
    await websocket.accept()
    
    try:
        # Generation state kontrolü
        gen_state = _active_deep_generations.get(document_id)
        
        # RECONNECT DURUMU: Üretim devam ediyorsa mevcut state'i gönder
        if gen_state and gen_state.get("status") in ["generating", "starting", "paused"]:
            print(f"[WebSocket] Reconnecting to active generation: {document_id}")
            
            # WebSocket bağlantısını işaretle
            gen_state["websocket_connected"] = True
            
            # Mevcut durumu gönder - RECONNECT event
            await websocket.send_json({
                "type": "reconnected",
                "message": "Üretim devam ediyor, mevcut durum yükleniyor...",
                "progress": gen_state.get("progress", 0),
                "current_phase": gen_state.get("current_phase", ""),
                "current_agent": gen_state.get("current_agent", ""),
                "is_paused": gen_state.get("status") == "paused"
            })
            
            # Tamamlanan bölümleri gönder
            for section in gen_state.get("completed_sections", []):
                await websocket.send_json({
                    "type": "section_written",
                    "section_id": section.get("id"),
                    "section_title": section.get("title"),
                    "content": section.get("content"),
                    "word_count": section.get("wordCount"),
                    "level": section.get("level"),
                    "progress": gen_state.get("progress", 0)
                })
            
            # Agent düşüncelerini gönder
            for thought in gen_state.get("agent_thoughts", []):
                await websocket.send_json({
                    "type": "agent_thinking",
                    "agent": thought.get("agent"),
                    "thought": thought.get("thought")
                })
            
            # Görselleri gönder
            for visual in gen_state.get("generated_visuals", []):
                await websocket.send_json({
                    "type": "visual_generated",
                    "visual_type": visual.get("type"),
                    "visual_title": visual.get("title"),
                    "visual": {
                        "code": visual.get("code"),
                        "render_type": visual.get("render_type")
                    }
                })
            
            # Bekle - üretim arka planda devam ediyor
            # Sadece bağlantı açık kalsın, yeni eventler gelecek
            while True:
                try:
                    # Client'tan mesaj bekle (ping/pong veya cancel)
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    msg = json.loads(data)
                    if msg.get("action") == "cancel":
                        DeepScholarOrchestrator.pause_generation(document_id)
                        break
                except asyncio.TimeoutError:
                    # Ping gönder
                    await websocket.send_json({"type": "ping"})
                except WebSocketDisconnect:
                    gen_state["websocket_connected"] = False
                    return
            return
        
        if not gen_state:
            # Dökümanı al ve streaming başlat
            document = learning_workspace_manager.get_document(document_id)
            if not document:
                await websocket.send_json({
                    "type": "error",
                    "message": "Döküman bulunamadı"
                })
                return
            
            # Eğer zaten tamamlandıysa
            if document.status == DocumentStatus.COMPLETED:
                await websocket.send_json({
                    "type": "complete",
                    "message": "Döküman zaten hazır",
                    "document": document.to_dict()
                })
                return
        
        # Yeni üretim başlatma
        # Orchestrator oluştur ve başlat
        orchestrator = DeepScholarOrchestrator()
        
        if gen_state:
            config = gen_state["config"]
            gen_state["orchestrator"] = orchestrator
            gen_state["websocket_connected"] = True
            gen_state["status"] = "generating"
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Generation config bulunamadı"
            })
            return
        
        # Event callback - state'i güncelle ve WebSocket'e gönder
        async def send_event(event: Dict):
            try:
                # State'i güncelle
                event_type = event.get("type", "")
                gen_state["events"].append(event)
                gen_state["progress"] = event.get("progress", gen_state["progress"])
                gen_state["current_phase"] = event.get("phase", gen_state.get("current_phase", ""))
                gen_state["current_agent"] = event.get("agent", gen_state.get("current_agent", ""))
                
                # Bölüm tamamlandıysa ekle
                if event_type == "section_written" or event_type == "section_complete":
                    section_data = {
                        "id": event.get("section_id", ""),
                        "title": event.get("section_title", ""),
                        "content": event.get("content", ""),
                        "wordCount": event.get("word_count", 0),
                        "level": event.get("level", 1)
                    }
                    gen_state["completed_sections"].append(section_data)
                    
                    # 🛡️ RESILIENCE: Auto-save ve checkpoint
                    if RESILIENCE_ENABLED:
                        try:
                            # Config'i dict olarak al
                            config_dict = {}
                            if hasattr(config, '__dict__'):
                                config_dict = {k: str(v) if hasattr(v, 'value') else v 
                                             for k, v in config.__dict__.items()}
                            
                            # Section contents dict oluştur
                            section_contents = {
                                s.get("id", ""): s.get("content", "") 
                                for s in gen_state["completed_sections"]
                            }
                            
                            await resilience_service.on_section_complete(
                                document_id=document_id,
                                workspace_id=workspace_id,
                                config=config_dict,
                                section_id=section_data["id"],
                                section_title=section_data["title"],
                                content=section_data["content"],
                                progress=gen_state["progress"],
                                current_phase=gen_state["current_phase"],
                                section_index=len(gen_state["completed_sections"]),
                                completed_sections=gen_state["completed_sections"],
                                section_contents=section_contents,
                                visuals=gen_state.get("generated_visuals", [])
                            )
                            
                            # Auto-save event gönder
                            await websocket.send_json({
                                "type": "auto_saved",
                                "section_id": section_data["id"],
                                "progress": gen_state["progress"],
                                "total_words": sum(s.get("wordCount", 0) for s in gen_state["completed_sections"]),
                                "timestamp": datetime.now().isoformat()
                            })
                        except Exception as e:
                            print(f"[Resilience Auto-Save Error] {e}")
                
                # Agent düşüncesi ekle
                if event_type == "agent_thinking":
                    thought_data = {
                        "agent": event.get("agent", ""),
                        "thought": event.get("thought", ""),
                        "timestamp": datetime.now().isoformat()
                    }
                    gen_state["agent_thoughts"].append(thought_data)
                
                # Görsel üretildiyse ekle
                if event_type == "visual_generated":
                    visual_data = {
                        "type": event.get("visual_type", ""),
                        "title": event.get("visual_title", ""),
                        "code": event.get("visual", {}).get("code", ""),
                        "render_type": event.get("visual", {}).get("render_type", "")
                    }
                    gen_state["generated_visuals"].append(visual_data)
                
                # WebSocket'e gönder (bağlıysa)
                if gen_state.get("websocket_connected"):
                    await websocket.send_json(event)
            except Exception as e:
                print(f"[Event Error] {e}")
                pass
        
        orchestrator.set_event_callback(send_event)
        
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.status = DocumentStatus.GENERATING
            document.generation_log.append(f"[{datetime.now().isoformat()}] 🚀 DeepScholar v2.0 başlatıldı")
            learning_workspace_manager.update_document(document)
        
        # Üretimi başlat
        final_document = None
        async for event in orchestrator.generate_document(config):
            await send_event(event)
            
            if event.get("type") == EventType.COMPLETE.value:
                final_document = event.get("document", {})
                gen_state["status"] = "completed"
            elif event.get("type") == EventType.ERROR.value:
                gen_state["status"] = "failed"
        
        # Dökümanı güncelle
        if final_document:
            document = learning_workspace_manager.get_document(document_id)
            if document:
                document.content = final_document.get("content", "")
                document.status = DocumentStatus.COMPLETED
                document.word_count = final_document.get("word_count", 0)
                document.generation_log.append(f"[{datetime.now().isoformat()}] ✅ DeepScholar üretimi tamamlandı")
                document.generation_log.append(f"Toplam kaynak: {final_document.get('citations_count', 0)}")
                learning_workspace_manager.update_document(document)
        
        # Temizlik
        _active_deep_generations.pop(document_id, None)
        
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected: {document_id}")
        # State'i silme, sadece websocket bağlantısını kapat
        if gen_state:
            gen_state["websocket_connected"] = False
    except Exception as e:
        import traceback
        print(f"[WebSocket Error] {e}")
        traceback.print_exc()
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        # Sadece tamamlandıysa veya hata aldıysa temizle
        if gen_state and gen_state.get("status") in ["completed", "failed"]:
            _active_deep_generations.pop(document_id, None)


@router.get("/status/{document_id}")
async def get_generation_status(document_id: str):
    """
    Üretim durumunu getir.
    
    Reconnect için kullanılır - aktif üretim varsa tüm state döndürülür.
    """
    gen_state = _active_deep_generations.get(document_id)
    
    if gen_state:
        return {
            "active": True,
            "can_reconnect": gen_state.get("status") in ["generating", "starting", "paused"],
            "status": gen_state.get("status", "unknown"),
            "progress": gen_state.get("progress", 0),
            "current_phase": gen_state.get("current_phase", ""),
            "current_agent": gen_state.get("current_agent", ""),
            "events_count": len(gen_state.get("events", [])),
            "completed_sections_count": len(gen_state.get("completed_sections", [])),
            "agent_thoughts_count": len(gen_state.get("agent_thoughts", [])),
            "visuals_count": len(gen_state.get("generated_visuals", [])),
            "started_at": gen_state.get("started_at"),
            "websocket_url": f"/api/deep-scholar/ws/{document_id}"
        }
    
    # Dökümanı kontrol et
    document = learning_workspace_manager.get_document(document_id)
    if document:
        doc_status = document.status.value if hasattr(document.status, 'value') else str(document.status)
        
        # Eğer döküman "generating" ama backend'de aktif değilse, "stale" durumu
        is_stale = doc_status == "generating"
        
        # Stale generating dökümanı otomatik olarak cancelled yap
        if is_stale:
            document.status = DocumentStatus.CANCELLED
            document.generation_log.append(f"[{datetime.now().isoformat()}] ⚠️ Üretim yarıda kaldı (bağlantı koptu)")
            learning_workspace_manager.update_document(document)
            doc_status = "cancelled"
        
        return {
            "active": False,
            "can_reconnect": False,
            "status": doc_status,
            "was_stale": is_stale,
            "progress": 100 if document.status == DocumentStatus.COMPLETED else 0,
            "document": document.to_dict()
        }
    
    raise HTTPException(status_code=404, detail="Döküman bulunamadı")


@router.post("/pause/{document_id}")
async def pause_generation(document_id: str):
    """
    Üretimi duraklat.
    
    Duraklatılan üretim checkpoint olarak kaydedilir ve 
    daha sonra kaldığı yerden devam edilebilir.
    """
    gen_state = _active_deep_generations.get(document_id)
    
    if gen_state:
        # Orchestrator'a duraklatma sinyali gönder
        DeepScholarOrchestrator.pause_generation(document_id)
        gen_state["status"] = "paused"
        
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.generation_log.append(f"[{datetime.now().isoformat()}] ⏸️ DeepScholar üretimi duraklatıldı")
            learning_workspace_manager.update_document(document)
        
        return {
            "success": True,
            "message": "Üretim duraklatıldı. Kaldığınız yerden devam edebilirsiniz.",
            "document_id": document_id,
            "progress": gen_state.get("progress", 0)
        }
    
    raise HTTPException(status_code=404, detail="Aktif üretim bulunamadı")


@router.post("/resume/{document_id}")
async def resume_generation(document_id: str):
    """
    Duraklatılmış üretimi devam ettir.
    
    Checkpoint'ten kaldığı yerden devam eder.
    """
    gen_state = _active_deep_generations.get(document_id)
    
    if gen_state and gen_state.get("status") == "paused":
        # Orchestrator'a devam sinyali gönder
        DeepScholarOrchestrator.resume_generation(document_id)
        gen_state["status"] = "generating"
        
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.generation_log.append(f"[{datetime.now().isoformat()}] ▶️ DeepScholar üretimi devam ediyor")
            learning_workspace_manager.update_document(document)
        
        return {
            "success": True,
            "message": "Üretim devam ediyor...",
            "document_id": document_id,
            "progress": gen_state.get("progress", 0)
        }
    
    # Checkpoint kontrolü
    checkpoint = DeepScholarOrchestrator.get_checkpoint(document_id)
    if checkpoint:
        return {
            "success": True,
            "message": "Checkpoint bulundu. WebSocket ile bağlanarak devam edebilirsiniz.",
            "document_id": document_id,
            "checkpoint": {
                "progress": checkpoint.progress,
                "current_phase": checkpoint.current_phase,
                "completed_sections": len(checkpoint.completed_sections),
                "pending_sections": len(checkpoint.pending_sections)
            }
        }
    
    raise HTTPException(status_code=404, detail="Duraklatılmış üretim bulunamadı")


@router.get("/checkpoint/{document_id}")
async def get_checkpoint(document_id: str):
    """Checkpoint bilgisini getir."""
    checkpoint = DeepScholarOrchestrator.get_checkpoint(document_id)
    
    if checkpoint:
        return {
            "exists": True,
            "document_id": document_id,
            "progress": checkpoint.progress,
            "current_phase": checkpoint.current_phase,
            "completed_sections": len(checkpoint.completed_sections),
            "pending_sections": len(checkpoint.pending_sections),
            "created_at": checkpoint.created_at
        }
    
    return {
        "exists": False,
        "document_id": document_id
    }


@router.post("/cancel/{document_id}")
async def cancel_generation(document_id: str):
    """Üretimi iptal et."""
    gen_state = _active_deep_generations.get(document_id)
    
    if gen_state:
        gen_state["status"] = "cancelled"
        _active_deep_generations.pop(document_id, None)
        
        # Checkpoint'i de sil
        DeepScholarOrchestrator.delete_checkpoint(document_id)
        
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.status = DocumentStatus.CANCELLED
            document.generation_log.append(f"[{datetime.now().isoformat()}] ❌ DeepScholar üretimi iptal edildi")
            learning_workspace_manager.update_document(document)
        
        return {
            "success": True,
            "message": "Üretim iptal edildi"
        }
    
    raise HTTPException(status_code=404, detail="Aktif üretim bulunamadı")


@router.post("/export/pdf/{document_id}")
async def export_to_pdf(document_id: str, request: Optional[ExportPDFRequest] = None):
    """Dökümanı PDF olarak export et."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    if not document.content:
        raise HTTPException(status_code=400, detail="Döküman içeriği boş")
    
    try:
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            output_path = tmp.name
        
        # PDF export
        success = await PDFExporter.export_to_pdf(
            content=document.content,
            title=document.title,
            output_path=output_path
        )
        
        if success and os.path.exists(output_path):
            return FileResponse(
                path=output_path,
                filename=f"{document.title.replace(' ', '_')}.pdf",
                media_type="application/pdf"
            )
        else:
            # PDF başarısız, HTML olarak dön
            html_path = output_path.replace('.pdf', '.html')
            if os.path.exists(html_path):
                return FileResponse(
                    path=html_path,
                    filename=f"{document.title.replace(' ', '_')}.html",
                    media_type="text/html"
                )
            raise HTTPException(status_code=500, detail="PDF export başarısız")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export hatası: {str(e)}")


@router.get("/export/markdown/{document_id}")
async def export_to_markdown(document_id: str):
    """Dökümanı Markdown olarak export et."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    if not document.content:
        raise HTTPException(status_code=400, detail="Döküman içeriği boş")
    
    # Markdown döndür
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=document.content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{document.title.replace(" ", "_")}.md"'
        }
    )


# ==================== ACADEMIC SEARCH ENDPOINTS ====================

@router.get("/search/academic")
async def search_academic_sources(
    query: str,
    limit: int = 10
):
    """Akademik kaynak araması (test amaçlı)."""
    from core.deep_scholar import AcademicSearchEngine
    
    engine = AcademicSearchEngine()
    results = await engine.search_all(query, limit_per_source=limit // 3)
    
    return {
        "query": query,
        "results": [
            {
                "id": r.id,
                "title": r.source_title,
                "type": r.source_type,
                "authors": r.authors,
                "year": r.year,
                "url": r.source_url,
                "abstract": r.abstract[:300] + "..." if r.abstract and len(r.abstract) > 300 else r.abstract,
                "relevance": r.relevance_score,
                "reliability": r.reliability_score
            }
            for r in results[:limit]
        ],
        "total": len(results)
    }


@router.get("/search/semantic-scholar")
async def search_semantic_scholar(
    query: str,
    limit: int = 10
):
    """Semantic Scholar araması."""
    from core.deep_scholar import AcademicSearchEngine
    
    engine = AcademicSearchEngine()
    results = await engine.search_semantic_scholar(query, limit)
    
    return {
        "source": "semantic_scholar",
        "query": query,
        "results": [
            {
                "id": r.id,
                "title": r.source_title,
                "authors": r.authors,
                "year": r.year,
                "url": r.source_url,
                "abstract": r.abstract,
                "relevance": r.relevance_score
            }
            for r in results
        ],
        "total": len(results)
    }


@router.get("/search/arxiv")
async def search_arxiv(
    query: str,
    limit: int = 10
):
    """arXiv araması."""
    from core.deep_scholar import AcademicSearchEngine
    
    engine = AcademicSearchEngine()
    results = await engine.search_arxiv(query, limit)
    
    return {
        "source": "arxiv",
        "query": query,
        "results": [
            {
                "id": r.id,
                "title": r.source_title,
                "authors": r.authors,
                "year": r.year,
                "url": r.source_url,
                "abstract": r.abstract,
                "relevance": r.relevance_score
            }
            for r in results
        ],
        "total": len(results)
    }


# ==================== AGENT STATUS ENDPOINTS ====================

@router.get("/agents")
async def get_agent_info():
    """Agent bilgilerini getir."""
    return {
        "agents": [
            {
                "role": "orchestrator",
                "name": "Orkestratör",
                "icon": "🎯",
                "description": "Tüm ajanları koordine eder ve süreç akışını yönetir"
            },
            {
                "role": "planner",
                "name": "Planlayıcı",
                "icon": "📋",
                "description": "Döküman iskeletini oluşturur, sayfa dağılımını hesaplar"
            },
            {
                "role": "researcher",
                "name": "Araştırmacı",
                "icon": "🔍",
                "description": "Web ve akademik kaynaklarda araştırma yapar"
            },
            {
                "role": "writer",
                "name": "Yazar",
                "icon": "✍️",
                "description": "İçerik yazar, kaynakları entegre eder"
            },
            {
                "role": "fact_checker",
                "name": "Doğrulayıcı",
                "icon": "✅",
                "description": "Halüsinasyon kontrolü, referans doğrulama yapar"
            },
            {
                "role": "user_proxy",
                "name": "Okuyucu",
                "icon": "👤",
                "description": "Kullanıcı perspektifinden içerik değerlendirir"
            },
            {
                "role": "synthesizer",
                "name": "Sentezci",
                "icon": "🔗",
                "description": "Çelişen kaynakları sentezler"
            }
        ]
    }


# ==================== QUEUE ENDPOINTS ====================

@router.get("/queue")
async def get_queue_status():
    """
    Döküman üretim kuyruğu durumunu getir.
    
    Bekleyen, aktif ve tamamlanan dökümanları gösterir.
    """
    if not RESILIENCE_ENABLED:
        return {
            "enabled": False,
            "message": "Queue sistemi aktif değil"
        }
    
    queue_status = resilience_service.queue.get_queue_status()
    
    # Aktif üretimleri detaylı ekle
    active_details = []
    for gen_id, gen_state in _active_deep_generations.items():
        if gen_state.get("status") in ["starting", "generating"]:
            active_details.append({
                "id": gen_id,
                "title": gen_state.get("config", {}).title if hasattr(gen_state.get("config", {}), 'title') else gen_state.get("config", {}).get("title", ""),
                "status": gen_state.get("status"),
                "progress": gen_state.get("progress", 0),
                "current_phase": gen_state.get("current_phase", ""),
                "current_agent": gen_state.get("current_agent", ""),
                "started_at": gen_state.get("started_at"),
                "sections_completed": len(gen_state.get("completed_sections", []))
            })
    
    return {
        "enabled": True,
        "queue": queue_status.get("queue", []),
        "queue_length": queue_status.get("queue_length", 0),
        "active": active_details,
        "active_count": len(active_details),
        "completed_count": queue_status.get("completed_count", 0),
        "max_concurrent": 1
    }


@router.delete("/queue/{document_id}")
async def remove_from_queue(document_id: str):
    """Dökümanı kuyruktan çıkar (henüz başlamamışsa)."""
    if not RESILIENCE_ENABLED:
        raise HTTPException(status_code=400, detail="Queue sistemi aktif değil")
    
    # Aktif mi kontrol et
    gen_state = _active_deep_generations.get(document_id)
    if gen_state and gen_state.get("status") in ["starting", "generating"]:
        raise HTTPException(
            status_code=400, 
            detail="Üretim devam ediyor. Önce iptal edin."
        )
    
    # Kuyruktan çıkar
    removed = resilience_service.queue.remove_from_queue(document_id)
    
    if removed:
        # Döküman durumunu güncelle
        document = learning_workspace_manager.get_document(document_id)
        if document:
            document.status = DocumentStatus.CANCELLED
            document.generation_log.append(f"[{datetime.now().isoformat()}] 🗑️ Kuyruktan çıkarıldı")
            learning_workspace_manager.update_document(document)
        
        return {
            "success": True,
            "message": "Kuyruktan çıkarıldı",
            "document_id": document_id
        }
    
    raise HTTPException(status_code=404, detail="Döküman kuyrukta bulunamadı")


@router.post("/queue/{document_id}/priority")
async def update_queue_priority(document_id: str, priority: int = 1):
    """Kuyruk önceliğini güncelle (1-10, yüksek = öncelikli)."""
    if not RESILIENCE_ENABLED:
        raise HTTPException(status_code=400, detail="Queue sistemi aktif değil")
    
    if priority < 1 or priority > 10:
        raise HTTPException(status_code=400, detail="Öncelik 1-10 arasında olmalı")
    
    resilience_service.queue.update_priority(document_id, priority)
    
    return {
        "success": True,
        "message": f"Öncelik güncellendi: {priority}",
        "document_id": document_id,
        "new_priority": priority
    }


@router.get("/queue/active")
async def get_active_generations():
    """Şu an aktif olan tüm üretimleri getir."""
    active = []
    
    for gen_id, gen_state in _active_deep_generations.items():
        if gen_state.get("status") in ["starting", "generating", "paused"]:
            config = gen_state.get("config", {})
            title = config.title if hasattr(config, 'title') else config.get("title", "Untitled")
            
            active.append({
                "id": gen_id,
                "title": title,
                "status": gen_state.get("status"),
                "progress": gen_state.get("progress", 0),
                "current_phase": gen_state.get("current_phase", ""),
                "current_agent": gen_state.get("current_agent", ""),
                "started_at": gen_state.get("started_at"),
                "sections_completed": len(gen_state.get("completed_sections", [])),
                "websocket_connected": gen_state.get("websocket_connected", False)
            })
    
    return {
        "count": len(active),
        "generations": active
    }
