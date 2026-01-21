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

from core.deep_scholar import (
    DeepScholarOrchestrator,
    DeepScholarConfig,
    DocumentLanguage,
    CitationStyle,
    EventType,
    PDFExporter
)
from core.learning_workspace import learning_workspace_manager, DocumentStatus


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


# ==================== ACTIVE GENERATIONS ====================

# Aktif üretim süreçlerini takip et
_active_deep_generations: Dict[str, Dict] = {}


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
    
    # Config oluştur
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
    
    # Döküman oluştur
    document = learning_workspace_manager.create_document(
        workspace_id=workspace_id,
        title=request.title,
        topic=request.topic,
        page_count=request.page_count,
        style=request.style
    )
    
    document_id = document.id
    
    # Generation state
    _active_deep_generations[document_id] = {
        "config": config,
        "status": "starting",
        "progress": 0,
        "events": [],
        "started_at": datetime.now().isoformat(),
        "orchestrator": None
    }
    
    return {
        "success": True,
        "document_id": document_id,
        "message": "DeepScholar üretimi başlatıldı. WebSocket ile takip edin.",
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
    """
    await websocket.accept()
    
    try:
        # Generation state kontrolü
        gen_state = _active_deep_generations.get(document_id)
        
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
            if document.status == DocumentStatus.READY:
                await websocket.send_json({
                    "type": "complete",
                    "message": "Döküman zaten hazır",
                    "document": document.to_dict()
                })
                return
        
        # Orchestrator oluştur ve başlat
        orchestrator = DeepScholarOrchestrator()
        
        if gen_state:
            config = gen_state["config"]
            gen_state["orchestrator"] = orchestrator
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Generation config bulunamadı"
            })
            return
        
        # Event callback
        async def send_event(event: Dict):
            try:
                await websocket.send_json(event)
                gen_state["events"].append(event)
                gen_state["progress"] = event.get("progress", gen_state["progress"])
            except:
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
                document.status = DocumentStatus.READY
                document.word_count = final_document.get("word_count", 0)
                document.generation_log.append(f"[{datetime.now().isoformat()}] ✅ DeepScholar üretimi tamamlandı")
                document.generation_log.append(f"Toplam kaynak: {final_document.get('citations_count', 0)}")
                learning_workspace_manager.update_document(document)
        
        # Temizlik
        _active_deep_generations.pop(document_id, None)
        
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected: {document_id}")
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
        _active_deep_generations.pop(document_id, None)


@router.get("/status/{document_id}")
async def get_generation_status(document_id: str):
    """Üretim durumunu getir (polling alternatifi)."""
    gen_state = _active_deep_generations.get(document_id)
    
    if gen_state:
        return {
            "active": True,
            "status": gen_state.get("status", "unknown"),
            "progress": gen_state.get("progress", 0),
            "events_count": len(gen_state.get("events", [])),
            "last_events": gen_state.get("events", [])[-5:],  # Son 5 event
            "started_at": gen_state.get("started_at")
        }
    
    # Dökümanı kontrol et
    document = learning_workspace_manager.get_document(document_id)
    if document:
        return {
            "active": False,
            "status": document.status.value if hasattr(document.status, 'value') else str(document.status),
            "progress": 100 if document.status == DocumentStatus.READY else 0,
            "document": document.to_dict()
        }
    
    raise HTTPException(status_code=404, detail="Döküman bulunamadı")


@router.post("/cancel/{document_id}")
async def cancel_generation(document_id: str):
    """Üretimi iptal et."""
    gen_state = _active_deep_generations.get(document_id)
    
    if gen_state:
        gen_state["status"] = "cancelled"
        _active_deep_generations.pop(document_id, None)
        
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
