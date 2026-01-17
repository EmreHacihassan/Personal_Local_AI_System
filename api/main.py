"""
Enterprise AI Assistant - FastAPI Main
Endüstri Standartlarında Kurumsal AI Çözümü

Ana API uygulaması - RESTful endpoints ve WebSocket.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Logger setup
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, WebSocket, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import shutil

from core.config import settings
from core.llm_manager import llm_manager
from core.vector_store import vector_store
from core.analytics import analytics
from core.rate_limiter import rate_limiter
from core.health import get_health_report
from core.export import export_manager, import_manager
from core.session_manager import session_manager
from core.notes_manager import notes_manager
from core.system_knowledge import SELF_KNOWLEDGE_PROMPT, SYSTEM_VERSION, SYSTEM_NAME
from core.circuit_breaker import (
    ollama_circuit, 
    chromadb_circuit, 
    external_api_circuit,
    circuit_registry,
)
from core.error_recovery import (
    ErrorRecoveryManager,
    ErrorCategory,
    ErrorSeverity,
    retry_with_backoff,
    with_fallback
)
from core.exceptions import CircuitBreakerOpenError
from core.moe_router import MoERouter, ExpertType, RoutingStrategy, QueryComplexity
from agents.orchestrator import orchestrator
from rag.document_loader import document_loader
from rag.chunker import document_chunker
from rag.async_processor import robust_loader, batch_processor
from api.websocket import websocket_endpoint, manager
from tools.web_search_engine import PremiumWebSearchEngine, get_search_engine, WebSearchTool
from tools.research_synthesizer import get_synthesizer, ResearchSynthesizer

# Learning module router
from api.learning_endpoints import router as learning_router


# ============ PYDANTIC MODELS ============

class ChatRequest(BaseModel):
    """Chat isteği modeli."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    web_search: bool = Field(default=False, description="Web araması yapılsın mı?")
    response_mode: str = Field(default="normal", pattern="^(normal|detailed)$", description="Yanıt modu: normal veya detailed")


class WebSearchRequest(BaseModel):
    """Web arama isteği modeli."""
    query: str = Field(..., min_length=1, max_length=1000)
    num_results: int = Field(default=8, ge=1, le=15)
    search_type: str = Field(default="general", pattern="^(general|news|academic)$")
    extract_content: bool = Field(default=True, description="İçerik çıkarsın mı")
    include_wikipedia: bool = Field(default=True, description="Wikipedia dahil edilsin mi")


class ChatResponse(BaseModel):
    """Chat yanıtı modeli."""
    response: str
    session_id: str
    sources: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: str


class DocumentUploadResponse(BaseModel):
    """Döküman yükleme yanıtı."""
    success: bool
    document_id: str
    filename: str
    chunks_created: int
    message: str


class SearchRequest(BaseModel):
    """Arama isteği modeli."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    filter_metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Arama yanıtı modeli."""
    results: List[Dict[str, Any]]
    total: int
    query: str


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


# ============ API VERSION & CONSTANTS ============

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


# ============ FASTAPI APP ============

app = FastAPI(
    title="Enterprise AI Assistant API",
    description="""
# Enterprise AI Assistant API

Endüstri Standartlarında Kurumsal AI Çözümü - REST API

## Özellikler
- 🤖 LLM Chat with streaming
- 🌐 Web Search integration
- 📁 Document RAG (Retrieval Augmented Generation)
- 📝 Notes management
- 📊 Analytics & Dashboard

## API Versioning
Current version: **v1**

Tüm endpoint'ler `/api/v1/` prefix'i ile erişilebilir.
Geriye uyumluluk için eski endpoint'ler de desteklenmektedir.

## Rate Limiting
- Chat endpoints: 60 requests/minute
- Search endpoints: 100 requests/minute
- Upload endpoints: 10 requests/minute
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Health check endpoints"},
        {"name": "chat", "description": "Chat and conversation endpoints"},
        {"name": "documents", "description": "Document management endpoints"},
        {"name": "search", "description": "Search endpoints"},
        {"name": "notes", "description": "Notes management endpoints"},
        {"name": "admin", "description": "Admin and analytics endpoints"},
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ RATE LIMITING MIDDLEWARE ============

from collections import defaultdict
import time as time_module

class RateLimitMiddleware:
    """Simple in-memory rate limiting."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.limits = {
            "chat": {"requests": 60, "window": 60},      # 60 req/min
            "search": {"requests": 100, "window": 60},   # 100 req/min
            "upload": {"requests": 10, "window": 60},    # 10 req/min
            "default": {"requests": 200, "window": 60},  # 200 req/min
        }
    
    def is_allowed(self, client_ip: str, endpoint_type: str = "default") -> bool:
        """Check if request is allowed."""
        now = time_module.time()
        limit_config = self.limits.get(endpoint_type, self.limits["default"])
        
        key = f"{client_ip}:{endpoint_type}"
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < limit_config["window"]
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit_config["requests"]:
            return False
        
        # Record request
        self.requests[key].append(now)
        return True

rate_limiter_middleware = RateLimitMiddleware()


# Session storage (in-memory for simplicity)
sessions: Dict[str, List[Dict[str, Any]]] = {}


# ============ HELPER FUNCTIONS ============

def get_uploaded_documents_info() -> str:
    """Yüklenen dökümanların bilgisini döndür."""
    upload_dir = settings.DATA_DIR / "uploads"
    
    if not upload_dir.exists():
        return ""
    
    documents = []
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            # Extract original filename from stored name
            parts = file_path.name.split("_", 1)
            original_name = parts[1] if len(parts) > 1 else file_path.name
            size_kb = file_path.stat().st_size / 1024
            documents.append(f"• {original_name} ({size_kb:.1f} KB)")
    
    if not documents:
        return ""
    
    docs_text = "\n\n### 📁 Yüklenen Dökümanlar:\n"
    docs_text += "Kullanıcı aşağıdaki dökümanları bilgi tabanına yüklemiş. Bu dosyalardaki bilgileri kullanarak yanıt verebilirsin:\n"
    docs_text += "\n".join(documents)
    docs_text += f"\n\n**Toplam:** {len(documents)} döküman"
    
    return docs_text


def generate_source_ref_id(filename: str, page_num: any, source_index: int, source_map: dict) -> tuple:
    """
    Wikipedia tarzı referans ID'si oluştur.
    
    Mantık:
    - Her döküman bir harf alır: A, B, C, D...
    - Sayfa numarası varsa: A.1, A.2, B.3 gibi
    - Sayfa yoksa: A, B, C gibi tek harf
    
    Örnek: [A.2] = A dökümanının 2. sayfası
    
    Returns:
        (ref_id, is_new_source)
    """
    import re
    
    # Dosya adını normalize et - sadece orijinal dosya adını kullan
    if '\\' in filename or '/' in filename:
        filename = filename.replace('\\', '/').split('/')[-1]
    
    # UUID prefix'i varsa kaldır (örn: a3e58d19-bcb8-4766-b461-2f7b87fc747c_excel4.pdf -> excel4.pdf)
    if '_' in filename and len(filename.split('_')[0]) == 36:
        parts = filename.split('_', 1)
        if len(parts) > 1:
            filename = parts[1]
    
    base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    base_name = re.sub(r'[^a-zA-Z0-9ğüşıöçĞÜŞİÖÇ\s_-]', '', base_name)
    base_name = base_name[:40]  # İlk 40 karakter
    
    # Bu dosya için harf ata (A, B, C...)
    is_new_source = False
    if base_name not in source_map:
        letter_index = len(source_map)
        if letter_index < 26:
            letter = chr(65 + letter_index)  # A=65
        else:
            first = chr(65 + (letter_index // 26) - 1)
            second = chr(65 + (letter_index % 26))
            letter = first + second
        source_map[base_name] = {"letter": letter, "filename": filename, "pages": set()}
        is_new_source = True
    
    letter = source_map[base_name]["letter"]
    
    # Sayfa numarası varsa ekle
    if page_num:
        try:
            page = int(page_num)
            source_map[base_name]["pages"].add(page)
            ref_id = f"{letter}.{page}"
        except (ValueError, TypeError):
            ref_id = letter
    else:
        ref_id = letter
    
    return ref_id, is_new_source


def format_reference_list(source_map: dict) -> str:
    """
    Wikipedia tarzı referans listesi oluştur.
    """
    if not source_map:
        return ""
    
    ref_list = "\n\n---\n📚 **KAYNAKLAR**\n"
    
    for base_name, info in source_map.items():
        letter = info["letter"]
        filename = info["filename"]
        pages = sorted(info["pages"]) if info["pages"] else []
        
        if pages:
            page_str = ", ".join(str(p) for p in pages)
            ref_list += f"**[{letter}]** {filename} (s. {page_str})\n"
        else:
            ref_list += f"**[{letter}]** {filename}\n"
    
    return ref_list


def deduplicate_results(results: list, content_key: str = "document") -> list:
    """
    Sonuçlardan duplicate içerikleri kaldır.
    İlk 200 karaktere göre karşılaştır.
    """
    seen_content = set()
    unique_results = []
    
    for r in results:
        content = r.get(content_key, "") if isinstance(r, dict) else getattr(r, 'content', '')
        content_hash = hash(content[:200].strip().lower())
        
        if content_hash not in seen_content:
            seen_content.add(content_hash)
            unique_results.append(r)
    
    return unique_results


def get_uploaded_document_list() -> list:
    """
    Yüklenen dökümanların listesini döndür.
    """
    upload_dir = settings.DATA_DIR / "uploads"
    
    if not upload_dir.exists():
        return []
    
    documents = []
    seen_names = set()
    
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            # UUID prefix'i kaldır
            parts = file_path.name.split("_", 1)
            original_name = parts[1] if len(parts) > 1 else file_path.name
            
            # Duplicate dosya adlarını atla
            if original_name in seen_names:
                continue
            seen_names.add(original_name)
            
            size_kb = file_path.stat().st_size / 1024
            doc_type = file_path.suffix.upper()[1:] if file_path.suffix else "FILE"
            documents.append({
                "name": original_name,
                "type": doc_type,
                "size_kb": size_kb
            })
    
    return documents


def search_knowledge_base(query: str, top_k: int = 5, strategy: str = "fusion") -> tuple:
    """
    Gelişmiş RAG ile bilgi tabanında arama yap ve Wikipedia tarzı referanslarla döndür.
    
    ENTERPRISE GRADE RAG:
    - Filename-based priority (dosya adı eşleşmesi en yüksek öncelik)
    - Keyword matching (içerikte kelime eşleşmesi)  
    - Semantic search (embedding benzerliği)
    - Duplicate filtering
    - Source attribution with refs
    
    Args:
        query: Arama sorgusu
        top_k: Döndürülecek sonuç sayısı
        strategy: RAG stratejisi (kullanılmıyor, future use)
        
    Returns:
        tuple: (knowledge_text, reference_list, source_map)
    """
    source_map = {}
    
    # Önce yüklenmiş döküman var mı kontrol et
    doc_count = vector_store.count()
    if doc_count == 0:
        return "", "", {}
    
    try:
        # === SORGU ANALİZİ ===
        query_lower = query.lower()
        query_words = [w.strip() for w in query_lower.split() if len(w.strip()) > 2]
        
        # Özel anahtar kelimeler ve dosya türleri
        doc_type_keywords = {
            'powerpoint': ['pptx', 'ppt', 'slayt', 'sunum', 'slide'],
            'excel': ['xlsx', 'xls', 'tablo', 'hücre', 'formül', 'sheet'],
            'pdf': ['pdf', 'kitap', 'döküman', 'belge'],
            'word': ['docx', 'doc', 'metin', 'yazı'],
        }
        
        # Kullanıcı hangi dosya türünü arıyor?
        target_doc_types = set()
        for doc_type, keywords in doc_type_keywords.items():
            if any(kw in query_lower for kw in keywords):
                target_doc_types.add(doc_type)
        
        # === TÜM DÖKÜMANLARI AL ===
        all_data = vector_store.collection.get(include=['documents', 'metadatas', 'embeddings'])
        
        if not all_data.get('documents'):
            return "", "", {}
        
        # === SKORLAMA SİSTEMİ ===
        scored_results = []
        seen_content_hashes = set()  # Duplicate tespiti için
        
        for i, doc in enumerate(all_data['documents']):
            if not doc:
                continue
                
            doc_lower = doc.lower()
            meta = all_data['metadatas'][i] if all_data['metadatas'] else {}
            
            # Dosya adını al ve normalize et
            filename = meta.get('original_filename') or meta.get('filename', 'unknown')
            if '_' in filename and len(filename.split('_')[0]) == 36:
                filename = filename.split('_', 1)[1]
            filename_lower = filename.lower()
            
            # Dosya uzantısını al
            file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            
            # === SKOR HESAPLA ===
            score = 0.0
            match_reasons = []
            
            # 1. DOSYA ADI EŞLEŞMESİ (En yüksek öncelik)
            filename_base = filename_lower.rsplit('.', 1)[0] if '.' in filename_lower else filename_lower
            filename_words_match = sum(1 for w in query_words if w in filename_base)
            if filename_words_match > 0:
                score += 0.5 + (filename_words_match * 0.15)  # 0.5 - 0.95 arası
                match_reasons.append(f"filename({filename_words_match})")
            
            # 2. DOSYA TÜRÜ EŞLEŞMESİ
            if target_doc_types:
                type_match = False
                if 'powerpoint' in target_doc_types and file_ext in ['pptx', 'ppt']:
                    score += 0.4
                    type_match = True
                elif 'excel' in target_doc_types and file_ext in ['xlsx', 'xls']:
                    score += 0.4
                    type_match = True
                elif 'pdf' in target_doc_types and file_ext == 'pdf':
                    score += 0.3
                    type_match = True
                elif 'word' in target_doc_types and file_ext in ['docx', 'doc']:
                    score += 0.4
                    type_match = True
                if type_match:
                    match_reasons.append(f"filetype({file_ext})")
            
            # 3. İÇERİK KEYWORD EŞLEŞMESİ
            content_matches = sum(1 for w in query_words if w in doc_lower)
            if content_matches > 0:
                score += 0.1 + (content_matches * 0.08)  # 0.1 - 0.5 arası
                match_reasons.append(f"content({content_matches})")
            
            # 4. Minimum skor kontrolü
            if score < 0.15:  # Çok düşük skorları atla
                continue
            
            # === DUPLICATE KONTROLÜ ===
            content_hash = hash(doc[:200].strip().lower())
            if content_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(content_hash)
            
            # Skoru 0-1 arasına normalize et
            score = min(score, 1.0)
            
            scored_results.append({
                'document': doc,
                'metadata': meta,
                'score': score,
                'filename': filename,
                'match_reasons': match_reasons,
                'id': all_data['ids'][i] if all_data.get('ids') else None,
            })
        
        # === SIRALAMA VE FİLTRELEME ===
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Eğer hiç sonuç yoksa, semantic search'e fallback yap
        if not scored_results:
            semantic_results = vector_store.search_with_scores(
                query=query,
                n_results=top_k,
                score_threshold=0.3,
            )
            for r in semantic_results:
                meta = r.get('metadata', {})
                filename = meta.get('original_filename') or meta.get('filename', 'Bilinmeyen')
                if '_' in filename and len(filename.split('_')[0]) == 36:
                    filename = filename.split('_', 1)[1]
                scored_results.append({
                    'document': r.get('document', ''),
                    'metadata': meta,
                    'score': r.get('score', 0),
                    'filename': filename,
                    'match_reasons': ['semantic'],
                })
        
        # En iyi sonuçları al
        top_results = scored_results[:top_k]
        
        if not top_results:
            return "", "", {}
        
        # === FORMAT RESULTS ===
        knowledge_text = "\n\n### 📚 BİLGİ TABANI İÇERİKLERİ (Referanslı):\n"
        knowledge_text += "Aşağıdaki bilgiler yüklenen dökümanlardan alınmıştır. Her içeriğin yanında [REF] referans kodu vardır.\n"
        knowledge_text += "Yanıtında bu bilgileri kullanırken ilgili referansı [X] veya [X.Y] formatında ekle.\n\n"
        
        for i, result in enumerate(top_results, 1):
            doc_content = result.get("document", "")
            metadata = result.get("metadata", {})
            score = result.get("score", 0)
            filename = result.get("filename", "Bilinmeyen")
            match_reasons = result.get("match_reasons", [])
            
            page_num = metadata.get("page") or metadata.get("page_number")
            chunk_idx = metadata.get("chunk_index")
            
            # Referans ID oluştur
            ref_id, _ = generate_source_ref_id(filename, page_num, i, source_map)
            
            # İçeriği optimize et
            if len(doc_content) > 2000:
                doc_content = doc_content[:2000] + "..."
            
            # Kaynak bilgisi satırı
            match_str = ", ".join(match_reasons) if match_reasons else "general"
            knowledge_text += f"**[{ref_id}]** 📄 _{filename}"
            if page_num:
                knowledge_text += f" | Sayfa {page_num}"
            if chunk_idx is not None:
                knowledge_text += f" | Bölüm {chunk_idx}"
            knowledge_text += f"_ | Alaka: {score:.2f} ({match_str})\n"
            knowledge_text += f"```\n{doc_content}\n```\n\n"
        
        reference_list = format_reference_list(source_map)
        return knowledge_text, reference_list, source_map
        
    except Exception as e:
        print(f"RAG search error: {e}")
        import traceback
        traceback.print_exc()
        return "", "", {}


# ============ HEALTH & STATUS ============

@app.get("/", tags=["Status"])
async def root():
    """API ana sayfası."""
    return {
        "name": "Enterprise AI Assistant",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_version": API_VERSION,
    }


# ============ KUBERNETES-READY HEALTH ENDPOINTS ============

@app.get("/health", response_model=HealthResponse, tags=["health"])
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


@app.get("/health/live", response_model=LivenessResponse, tags=["health"])
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
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 30
    ```
    """
    return LivenessResponse(
        status="alive",
        timestamp=datetime.now().isoformat()
    )


@app.get("/health/ready", response_model=ReadinessResponse, tags=["health"])
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
        port: 8000
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
        import shutil
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


@app.get("/status", tags=["health"])
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


@app.get("/status/circuits", tags=["health"])
async def get_circuit_breaker_status():
    """
    Circuit breaker durumları.
    
    Tüm circuit breaker'ların anlık durumunu döndürür.
    """
    return {
        "circuits": circuit_registry.get_all_status(),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/status/circuits/reset", tags=["health"])
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


# ============ CHAT ENDPOINTS ============

# Error recovery manager instance
error_recovery = ErrorRecoveryManager()

# MoE Router instance (Mixture of Experts query routing)
moe_router = MoERouter(strategy=RoutingStrategy.BALANCED)


def _get_fallback_response(message: str, error: str) -> str:
    """Circuit breaker açıkken veya hata durumunda fallback yanıt."""
    return (
        f"⚠️ Şu anda AI servislerine erişimde geçici bir sorun yaşıyorum. "
        f"Lütfen birkaç saniye sonra tekrar deneyin.\n\n"
        f"Sorununuz: '{message[:50]}...'\n"
        f"Teknik detay: {error}"
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Ana chat endpoint'i.
    
    Kullanıcı mesajını işler ve AI yanıtı döndürür.
    Circuit breaker korumalı - ardışık hatalar servisi geçici olarak devre dışı bırakır.
    """
    import time
    start_time = time.time()
    
    try:
        # Get or create session from file-based storage
        session_id = request.session_id or str(uuid.uuid4())
        
        session = session_manager.get_session(session_id)
        if session is None:
            session = session_manager.create_session()
            session_id = session.id
        
        # Sync with in-memory cache
        if session_id not in sessions:
            sessions[session_id] = session.get_history(limit=50)
        
        # Add user message to history (both in-memory and file)
        user_msg = {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat(),
        }
        sessions[session_id].append(user_msg)
        session_manager.add_message(session_id, "user", request.message)
        
        # Build chat history text for context
        recent_history = sessions[session_id][-10:]
        history_text = ""
        if len(recent_history) > 1:
            history_text = "\n\nÖnceki konuşma geçmişi:\n"
            for msg in recent_history[:-1]:
                role_name = "Kullanıcı" if msg["role"] == "user" else "Asistan"
                history_text += f"{role_name}: {msg['content']}\n"
        
        # Build notes context - search relevant notes
        notes_text = ""
        try:
            relevant_notes = notes_manager.search_notes(request.message)
            if relevant_notes:
                notes_text = "\n\nKullanıcının Notlarından İlgili Bilgiler:\n"
                for note in relevant_notes[:5]:  # Max 5 relevant note
                    notes_text += f"- [{note.category}] {note.title}: {note.content[:200]}...\n"
        except Exception as e:
            pass  # Notes not critical, continue without them
        
        # Prepare context with chat history and notes
        context = request.context or {}
        context["chat_history"] = recent_history
        context["history_text"] = history_text
        context["notes_text"] = notes_text
        
        # Execute through orchestrator with circuit breaker protection
        try:
            response = ollama_circuit.call(
                lambda: orchestrator.execute(request.message, context)
            )
        except CircuitBreakerOpenError as cb_error:
            # Circuit açık - fallback yanıt ver
            error_recovery.record_error(cb_error, ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH)
            fallback_content = _get_fallback_response(request.message, str(cb_error))
            
            return ChatResponse(
                response=fallback_content,
                session_id=session_id,
                sources=[],
                metadata={"circuit_breaker": "open", "service": "ollama"},
                timestamp=datetime.now().isoformat(),
            )
        
        # Add assistant response to history (both in-memory and file)
        assistant_msg = {
            "role": "assistant",
            "content": response.content,
            "timestamp": datetime.now().isoformat(),
        }
        sessions[session_id].append(assistant_msg)
        session_manager.add_message(session_id, "assistant", response.content)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Track analytics with actual duration
        analytics.track_chat(
            query=request.message[:100],
            response_length=len(response.content),
            duration_ms=duration_ms,
            agent=response.metadata.get("agent", "unknown"),
            session_id=session_id,
        )
        
        return ChatResponse(
            response=response.content,
            session_id=session_id,
            sources=response.sources,
            metadata={**response.metadata, "duration_ms": duration_ms},
            timestamp=datetime.now().isoformat(),
        )
        
    except CircuitBreakerOpenError as cb_error:
        # Circuit breaker açık
        analytics.track_error("chat", f"circuit_breaker_open: {cb_error}")
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "Service temporarily unavailable",
                "retry_after": cb_error.retry_after_seconds,
                "message": str(cb_error)
            }
        )
    except Exception as e:
        # Track error and record for recovery
        analytics.track_error("chat", str(e))
        error_recovery.record_error(e, ErrorCategory.INTERNAL, ErrorSeverity.MEDIUM)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint - SSE (Server-Sent Events) kullanır.
    
    Token token yanıt gönderir.
    """
    import json
    
    async def generate():
        try:
            # Get or create session
            session_id = request.session_id or str(uuid.uuid4())
            
            # Load session from file-based storage
            session = session_manager.get_session(session_id)
            if session is None:
                session = session_manager.create_session()
                session_id = session.id
            
            # Also sync with in-memory cache
            if session_id not in sessions:
                sessions[session_id] = session.get_history(limit=50)
            
            # Add user message to history (both in-memory and file)
            user_msg = {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat(),
            }
            sessions[session_id].append(user_msg)
            session_manager.add_message(session_id, "user", request.message)
            
            # Send session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # ========== GELİŞMİŞ CHAT HISTORY CONTEXT ==========
            # Son 20 mesajı al (daha fazla bağlam için)
            recent_history = sessions[session_id][-20:]
            
            # History text oluştur - mesaj içeriklerini TAM olarak dahil et
            history_text = ""
            if len(recent_history) > 1:  # More than just current message
                history_text = "\n\n### 💬 ÖNCEKİ KONUŞMA GEÇMİŞİ:\n"
                history_text += "Aşağıdaki mesajlar bu oturumdaki önceki konuşmadır. Son yanıtın yarım kaldıysa devam et.\n\n"
                
                for i, msg in enumerate(recent_history[:-1]):  # Exclude current message
                    role_name = "👤 Kullanıcı" if msg["role"] == "user" else "🤖 Asistan"
                    content = msg.get('content', '')
                    
                    # Mesaj içeriğini TAM olarak dahil et (kısaltma yok!)
                    history_text += f"**{role_name}:** {content}\n\n"
                    
                    # Son asistan mesajı yarım kaldıysa özel işaretle
                    if msg["role"] == "assistant" and i == len(recent_history) - 2:
                        # Son mesajın yarım kalıp kalmadığını kontrol et
                        if not content.strip().endswith(('.', '!', '?', ':', '"', "'", ')', ']', '}')):
                            history_text += "⚠️ **[ÖNCEKİ YANITIM YARIM KALDI - DEVAM EDECEĞİM]**\n\n"
            
            # "Devam et" tarzı komutları algıla
            continue_commands = [
                "devam et", "devam", "bitir", "tamamla", "son yanıtını bitir",
                "kaldığın yerden devam", "yarım kalan", "continue", "finish",
                "go on", "keep going", "son cevabını bitir", "yarım bıraktın"
            ]
            is_continue_request = any(cmd in request.message.lower() for cmd in continue_commands)
            
            # Build notes context - search relevant notes
            notes_text = ""
            try:
                relevant_notes = notes_manager.search_notes(request.message)
                if relevant_notes:
                    notes_text = "\n\n### 📒 Kullanıcının Notları:\n"
                    for note in relevant_notes[:5]:
                        notes_text += f"- [{note.category}] {note.title}: {note.content[:300]}\n"
            except:
                pass
            
            # Prepare context
            context = request.context or {}
            context["chat_history"] = recent_history
            
            # Stream tokens from LLM
            full_response = ""
            
            # Yüklenen dökümanların listesini al
            documents_text = get_uploaded_documents_info()
            
            # === BASİT MESAJ TESPİTİ ===
            # Selamlaşma, teşekkür, basit sohbet mesajlarında RAG araması yapma
            simple_greetings = [
                "merhaba", "selam", "hey", "hi", "hello", "günaydın", "iyi günler", 
                "iyi akşamlar", "iyi geceler", "nasılsın", "naber", "ne haber",
                "teşekkür", "sağol", "eyvallah", "thanks", "thank you", "bye",
                "görüşürüz", "hoşça kal", "bb", "ok", "tamam", "anladım", "peki",
                "evet", "hayır", "yes", "no", "hmm", "hm", "aha"
            ]
            query_lower = request.message.lower().strip()
            query_words = query_lower.split()
            
            # Kısa mesaj (3 kelime veya daha az) ve basit selamlaşma kontrolü
            is_simple_message = (
                len(query_words) <= 3 and 
                any(greet in query_lower for greet in simple_greetings)
            ) or (
                len(query_lower) <= 15 and 
                any(query_lower.startswith(greet) or query_lower == greet for greet in simple_greetings)
            )
            
            # RAG: Bilgi tabanında ilgili içerikleri ara (fusion strateji ile) - Wikipedia tarzı referanslarla
            # Basit mesajlarda RAG atlansın
            if is_simple_message:
                knowledge_text, reference_list, source_map = "", "", {}
            else:
                knowledge_text, reference_list, source_map = search_knowledge_base(request.message, top_k=8, strategy="fusion")
            
            # Response mode'a göre sistem promptu ayarla
            if request.response_mode == "detailed":
                mode_instruction = """
📝 **DETAYLI YANIT MODU AKTİF**
Yanıtın şu özelliklere sahip olmalı:
- Kapsamlı ve derinlemesine açıklama
- Konuyu birden fazla açıdan ele al
- Örnekler, karşılaştırmalar ve detaylı açıklamalar ekle
- Adım adım açıklamalar yap (varsa)
- Avantaj/dezavantaj, dikkat edilmesi gerekenler gibi ek bilgiler ver
- En az 400-600 kelime uzunluğunda yanıt ver
- Markdown formatında düzenli ve okunabilir yaz
"""
            else:
                mode_instruction = """
💬 **NORMAL YANIT MODU**
Yanıtın şu özelliklere sahip olmalı:
- Net ve öz açıklama
- Doğrudan konuya odaklan
- Gerekli bilgiyi kısa ve anlaşılır şekilde ver
"""
            
            # Get system prompt with history, notes, documents and RAG knowledge
            # "Devam et" komutu için özel talimat
            continue_instruction = ""
            if is_continue_request:
                continue_instruction = """
🔄 **DEVAM ET KOMUTU ALGILANDI**
Kullanıcı önceki yarım kalan yanıtının devamını istiyor.
- Yukarıdaki konuşma geçmişindeki son asistan mesajını kontrol et
- Eğer yarım kaldıysa, KALDĞIN YERDEN AYNEN DEVAM ET
- Yeni bir yanıt başlatma, önceki yanıtı tamamla
- Önceki yanıtın bağlamını ve formatını koru
"""
            
            # Wikipedia tarzı referans talimatı
            reference_instruction = ""
            if source_map:
                ref_examples = ", ".join([f"[{info['letter']}]" for info in list(source_map.values())[:3]])
                reference_instruction = f"""
📚 **WİKİPEDİA TARZI REFERANS SİSTEMİ**
Yanıtında dökümanlardan aldığın bilgilere referans ver. Format:
- Tek kaynak: [A] veya [B.2] (B dökümanının 2. sayfası)
- Birden fazla kaynak: [A][B] veya [A.1][C.3]
- Mevcut referanslar: {ref_examples}

Örnek kullanım:
"PowerPoint'te yeni slayt eklemek için Ctrl+M kullanılır [A.1]. Animasyon eklemek için ise Animasyonlar sekmesi tercih edilir [A.3][B]."

ÖNEMLİ: Her bilgi için uygun referansı cümle sonuna ekle. Referans yoksa ekleme.
"""
            
            system_prompt = f"""Sen "{SYSTEM_NAME}" adlı kurumsal bir AI asistanısın (v{SYSTEM_VERSION}). Türkçe yanıt ver.

{SELF_KNOWLEDGE_PROMPT}

{mode_instruction}
{continue_instruction}
{reference_instruction}
{history_text}
{notes_text}
{documents_text}
{knowledge_text}

**KRİTİK KURALLAR:**
1. Eğer yukarıda "BİLGİ TABANI İÇERİKLERİ" bölümü varsa, öncelikle bu bilgileri kullanarak yanıt ver.
2. Her bilgi için ilgili referansı [X] veya [X.Y] formatında ekle (X=döküman harfi, Y=sayfa no).
3. Konuşma geçmişini DİKKATLİCE oku ve bağlamı koru.
4. Eğer önceki yanıtın yarım kaldıysa (ÖNCEKİ YANITIM YARIM KALDI işareti varsa), önce onu tamamla.
5. Kullanıcı "devam et", "bitir" gibi komutlar verdiyse, önceki yarım kalan yanıtı TAM OLARAK tamamla.
6. Yanıtını ASLA yarım bırakma, her zaman mantıksal bir sonuçla bitir.
7. Yanıtın sonunda "{reference_list}" bölümünü EKLEMENİ İSTEMİYORUM, sadece metin içinde referans kullan.
8. Kullanıcı kendi mimarini, yeteneklerini veya nasıl çalıştığını sorarsa yukarıdaki "Senin Hakkında" bölümündeki bilgileri kullan.

Yukarıdaki konuşma geçmişini, kullanıcının notlarını ve bilgi tabanı içeriklerini dikkate alarak mevcut soruya cevap ver."""
            
            for token in llm_manager.generate_stream(request.message, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Yanıt sonuna referans listesi ekle (eğer kaynaklar varsa)
            if source_map and reference_list:
                # Referans listesini stream et
                yield f"data: {json.dumps({'type': 'token', 'content': reference_list})}\n\n"
                full_response += reference_list
            
            # Add assistant response to history (both in-memory and file)
            assistant_msg = {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat(),
            }
            sessions[session_id].append(assistant_msg)
            session_manager.add_message(session_id, "assistant", full_response)
            
            # Track analytics
            analytics.track_chat(
                query=request.message[:100],
                response_length=len(full_response),
                duration_ms=0,
                agent="streaming",
                session_id=session_id,
            )
            
            # Send end event with sources info
            end_data = {'type': 'end', 'session_id': session_id}
            if source_map:
                end_data['sources'] = [
                    {'ref': info['letter'], 'filename': info['filename'], 'pages': list(info['pages'])}
                    for info in source_map.values()
                ]
            yield f"data: {json.dumps(end_data)}\n\n"
            
        except Exception as e:
            analytics.track_error("chat_stream", str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ============ WEB SEARCH ENDPOINTS ============

@app.post("/api/web-search", tags=["Web Search"])
async def web_search(request: WebSearchRequest):
    """
    Premium Web Search - İçerik çıkarmalı kapsamlı arama.
    
    Perplexity AI kalitesinde web araması yapar:
    - Multi-source arama (DuckDuckGo + Wikipedia)
    - Gerçek içerik çıkarma (sadece link değil)
    - Kaynak güvenilirlik skorlaması
    - Akıllı cache sistemi
    """
    try:
        import time
        start_time = time.time()
        
        # Premium search engine kullan
        engine = get_search_engine()
        
        result = engine.search(
            query=request.query,
            num_results=request.num_results,
            extract_content=request.extract_content,
            include_wikipedia=request.include_wikipedia
        )
        
        search_time = int((time.time() - start_time) * 1000)
        
        if result.success:
            # UI için kaynakları formatla
            sources = engine.get_sources_for_ui(result)
            
            return {
                "success": True,
                "query": result.query,
                "instant_answer": result.instant_answer,
                "knowledge_panel": result.knowledge_panel,
                "results": sources,
                "total": result.total_results,
                "providers": result.providers_used,
                "related_queries": result.related_queries,
                "search_time_ms": search_time,
                "cached": result.cached,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "query": request.query,
                "error": result.error_message or "Arama başarısız",
                "results": [],
                "total": 0
            }
    except Exception as e:
        analytics.track_error("web_search", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/web-search/stats", tags=["Web Search"])
async def get_web_search_stats():
    """Web arama istatistikleri"""
    engine = get_search_engine()
    return engine.get_stats()


@app.post("/api/web-search/clear-cache", tags=["Web Search"])
async def clear_web_search_cache():
    """Web arama cache'ini temizle"""
    engine = get_search_engine()
    engine.clear_cache()
    return {"success": True, "message": "Cache temizlendi"}


@app.post("/api/chat/web-stream", tags=["Chat"])
async def chat_web_stream(request: ChatRequest):
    """
    🌐 Premium Web Search Chat - Perplexity AI Kalitesinde
    
    Özellikler:
    - Multi-source arama (DuckDuckGo + Wikipedia)
    - Gerçek içerik çıkarma ve analizi
    - AI-powered sentez ve özet
    - Kaynak güvenilirlik skorlaması
    - Akıllı prompt oluşturma
    - Streaming yanıt
    """
    import json
    import time
    
    async def generate():
        try:
            search_start = time.time()
            
            # Get or create session
            session_id = request.session_id or str(uuid.uuid4())
            
            # Load session from file-based storage
            session = session_manager.get_session(session_id)
            if session is None:
                session = session_manager.create_session()
                session_id = session.id
            
            # Also sync with in-memory cache
            if session_id not in sessions:
                sessions[session_id] = session.get_history(limit=50)
            
            # Add user message to history
            user_msg = {
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat(),
            }
            sessions[session_id].append(user_msg)
            session_manager.add_message(session_id, "user", request.message)
            
            # Send session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # ===== PHASE 1: WEB SEARCH =====
            status_search = {"type": "status", "phase": "search", "message": "🔍 Web'de aranıyor..."}
            yield f"data: {json.dumps(status_search)}\n\n"
            
            web_sources = []
            search_response = None
            research_context = None
            
            try:
                # Premium search engine kullan
                engine = get_search_engine()
                synthesizer = get_synthesizer()
                
                # Arama yap
                search_response = engine.search(
                    query=request.message,
                    num_results=8,
                    extract_content=True,
                    include_wikipedia=True
                )
                
                search_time = int((time.time() - search_start) * 1000)
                
                if search_response.success:
                    # UI için kaynakları formatla
                    web_sources = engine.get_sources_for_ui(search_response)
                    
                    # İlerleme bildir
                    analyze_msg = f"📊 {len(web_sources)} kaynak analiz ediliyor..."
                    status_analyze = {"type": "status", "phase": "analyze", "message": analyze_msg}
                    yield f"data: {json.dumps(status_analyze)}\n\n"
                    
                    # Kaynakları hemen gönder (UI için)
                    sources_data = {
                        "type": "sources",
                        "sources": web_sources,
                        "instant_answer": search_response.instant_answer,
                        "knowledge_panel": search_response.knowledge_panel,
                        "related_queries": search_response.related_queries,
                        "providers": search_response.providers_used,
                        "search_time_ms": search_time,
                        "cached": search_response.cached
                    }
                    yield f"data: {json.dumps(sources_data)}\n\n"
                    
                    # Araştırma bağlamı oluştur
                    raw_response = {
                        "query": search_response.query,
                        "instant_answer": search_response.instant_answer,
                        "knowledge_panel": search_response.knowledge_panel,
                        "results": [
                            {
                                "title": r.title,
                                "url": r.url,
                                "snippet": r.snippet,
                                "content": r.full_content,
                                "domain": r.domain,
                                "type": r.source_type.value,
                                "reliability": r.reliability_score
                            }
                            for r in search_response.results
                        ]
                    }
                    
                    research_context = synthesizer.prepare_context(raw_response)
                    
            except Exception as search_error:
                warning_msg = f"⚠️ Web araması sırasında hata: {str(search_error)}"
                warning_data = {"type": "warning", "message": warning_msg}
                yield f"data: {json.dumps(warning_data)}\n\n"
            
            # ===== PHASE 2: BUILD CONTEXT =====
            status_context = {"type": "status", "phase": "context", "message": "📝 Bağlam hazırlanıyor..."}
            yield f"data: {json.dumps(status_context)}\n\n"
            
            # ========== GELİŞMİŞ CHAT HISTORY CONTEXT ==========
            # Son 20 mesajı al (daha fazla bağlam için)
            recent_history = sessions[session_id][-20:]
            
            # History text oluştur - mesaj içeriklerini TAM olarak dahil et
            history_text = ""
            if len(recent_history) > 1:
                history_text = "\n\n### 💬 ÖNCEKİ KONUŞMA GEÇMİŞİ:\n"
                history_text += "Aşağıdaki mesajlar bu oturumdaki önceki konuşmadır. Son yanıtın yarım kaldıysa devam et.\n\n"
                
                for i, msg in enumerate(recent_history[:-1]):
                    role_name = "👤 Kullanıcı" if msg["role"] == "user" else "🤖 Asistan"
                    content = msg.get('content', '')
                    
                    # Mesaj içeriğini TAM olarak dahil et (kısaltma yok!)
                    history_text += f"**{role_name}:** {content}\n\n"
                    
                    # Son asistan mesajı yarım kaldıysa özel işaretle
                    if msg["role"] == "assistant" and i == len(recent_history) - 2:
                        if not content.strip().endswith(('.', '!', '?', ':', '"', "'", ')', ']', '}')):
                            history_text += "⚠️ **[ÖNCEKİ YANITIM YARIM KALDI - DEVAM EDECEĞİM]**\n\n"
            
            # "Devam et" tarzı komutları algıla
            continue_commands = [
                "devam et", "devam", "bitir", "tamamla", "son yanıtını bitir",
                "kaldığın yerden devam", "yarım kalan", "continue", "finish",
                "go on", "keep going", "son cevabını bitir", "yarım bıraktın"
            ]
            is_continue_request = any(cmd in request.message.lower() for cmd in continue_commands)
            
            # Notes context
            notes_text = ""
            try:
                relevant_notes = notes_manager.search_notes(request.message)
                if relevant_notes:
                    notes_text = "\n\n### 📒 İlgili Notlar:\n"
                    for note in relevant_notes[:3]:
                        notes_text += f"- **{note.title}**: {note.content[:300]}...\n"
            except:
                pass
            
            # Documents context - yüklenen dökümanların bilgisi
            documents_text = get_uploaded_documents_info()
            
            # === BASİT MESAJ TESPİTİ (Web Search için de) ===
            simple_greetings = [
                "merhaba", "selam", "hey", "hi", "hello", "günaydın", "iyi günler", 
                "iyi akşamlar", "iyi geceler", "nasılsın", "naber", "ne haber",
                "teşekkür", "sağol", "eyvallah", "thanks", "thank you", "bye",
                "görüşürüz", "hoşça kal", "bb", "ok", "tamam", "anladım", "peki",
                "evet", "hayır", "yes", "no", "hmm", "hm", "aha"
            ]
            query_lower = request.message.lower().strip()
            query_words = query_lower.split()
            
            is_simple_message = (
                len(query_words) <= 3 and 
                any(greet in query_lower for greet in simple_greetings)
            ) or (
                len(query_lower) <= 15 and 
                any(query_lower.startswith(greet) or query_lower == greet for greet in simple_greetings)
            )
            
            # RAG: Bilgi tabanında ilgili içerikleri ara (rerank strateji ile daha iyi sonuçlar) - Wikipedia tarzı referanslarla
            # Basit mesajlarda RAG atlansın
            if is_simple_message:
                knowledge_text, reference_list, source_map = "", "", {}
            else:
                knowledge_text, reference_list, source_map = search_knowledge_base(request.message, top_k=8, strategy="rerank")
            
            # ===== PHASE 3: BUILD PROMPTS =====
            # Response mode'a göre ek talimatlar
            if request.response_mode == "detailed":
                mode_instruction = """
## 📝 DETAYLI YANIT MODU
Yanıtın şu özelliklere sahip OLMALI:
- Kapsamlı ve derinlemesine açıklama yap
- Konuyu birden fazla açıdan ele al
- Somut örnekler, karşılaştırmalar ve detaylı açıklamalar ekle
- Adım adım açıklamalar yap
- Avantaj/dezavantaj, dikkat edilmesi gerekenler gibi ek bilgiler ver
- En az 500-800 kelime uzunluğunda yanıt ver
- Markdown formatında düzenli ve okunabilir yaz
- Her ana konuyu ayrı başlık altında ele al
"""
            else:
                mode_instruction = ""
            
            # Wikipedia tarzı referans talimatı
            reference_instruction = ""
            if source_map:
                ref_examples = ", ".join([f"[{info['letter']}]" for info in list(source_map.values())[:3]])
                reference_instruction = f"""
📚 **WİKİPEDİA TARZI REFERANS SİSTEMİ**
Yanıtında dökümanlardan aldığın bilgilere referans ver. Format:
- Tek kaynak: [A] veya [B.2] (B dökümanının 2. sayfası)
- Birden fazla kaynak: [A][B] veya [A.1][C.3]
- Mevcut referanslar: {ref_examples}

Örnek: "Bu işlem için Ctrl+M kısayolu kullanılır [A.1]."
ÖNEMLİ: Her bilgi için uygun referansı ekle. Referans yoksa ekleme.
"""
            
            if research_context:
                # Synthesizer'dan promptları al
                system_prompt, user_prompt = synthesizer.build_prompts(research_context)
                
                # Mode instruction ve reference instruction ekle
                if mode_instruction:
                    system_prompt = mode_instruction + "\n" + system_prompt
                if reference_instruction:
                    system_prompt = reference_instruction + "\n" + system_prompt
                
                # History, notes, documents ve knowledge ekle
                knowledge_section = knowledge_text if knowledge_text else ""
                system_prompt = system_prompt.replace(
                    "## 📋 GÖREV",
                    f"{history_text}{notes_text}{documents_text}{knowledge_section}\n\n## 📋 GÖREV"
                )
                
                # Metadata ekle
                intent = research_context.intent.value
                style = research_context.style.value
                source_count = len(research_context.sources)
                
                metadata_data = {"type": "metadata", "intent": intent, "style": style, "source_count": source_count}
                yield f"data: {json.dumps(metadata_data)}\n\n"
                
            else:
                # Fallback prompt (arama başarısız olursa)
                # "Devam et" komutu için özel talimat
                continue_instruction = ""
                if is_continue_request:
                    continue_instruction = """
🔄 **DEVAM ET KOMUTU ALGILANDI**
Kullanıcı önceki yarım kalan yanıtının devamını istiyor.
- Yukarıdaki konuşma geçmişindeki son asistan mesajını kontrol et
- Eğer yarım kaldıysa, KALDIĞIN YERDEN AYNEN DEVAM ET
- Yeni bir yanıt başlatma, önceki yanıtı tamamla
- Önceki yanıtın bağlamını ve formatını koru
"""
                
                system_prompt = f"""Sen "{SYSTEM_NAME}" adlı kurumsal bir AI asistanısın (v{SYSTEM_VERSION}). Türkçe yanıt ver.

{SELF_KNOWLEDGE_PROMPT}

{continue_instruction}
{reference_instruction}
{history_text}
{notes_text}
{documents_text}
{knowledge_text}

**KRİTİK KURALLAR:**
1. Eğer yukarıda "BİLGİ TABANI İÇERİKLERİ" bölümü varsa, öncelikle bu bilgileri kullanarak yanıt ver.
2. Her bilgi için ilgili referansı [X] veya [X.Y] formatında ekle.
3. Konuşma geçmişini DİKKATLİCE oku ve bağlamı koru.
4. Eğer önceki yanıtın yarım kaldıysa, önce onu tamamla.
5. Yanıtını ASLA yarım bırakma.
6. Kullanıcı kendi mimarini, yeteneklerini veya nasıl çalıştığını sorarsa yukarıdaki "Senin Hakkında" bölümündeki bilgileri kullan.

⚠️ Web araması yapılamadı. Bilgi tabanındaki dökümanları ve genel bilginle yanıt ver.
"""
                user_prompt = request.message
            
            # ===== PHASE 4: GENERATE RESPONSE =====
            status_generate = {"type": "status", "phase": "generate", "message": "✨ Yanıt oluşturuluyor..."}
            yield f"data: {json.dumps(status_generate)}\n\n"
            
            full_response = ""
            generation_start = time.time()
            
            for token in llm_manager.generate_stream(user_prompt, system_prompt):
                full_response += token
                token_data = {"type": "token", "content": token}
                yield f"data: {json.dumps(token_data)}\n\n"
            
            # Yanıt sonuna döküman referans listesi ekle (eğer kaynaklar varsa)
            if source_map and reference_list:
                yield f"data: {json.dumps({'type': 'token', 'content': reference_list})}\n\n"
                full_response += reference_list
            
            generation_time = int((time.time() - generation_start) * 1000)
            total_time = int((time.time() - search_start) * 1000)
            
            # ===== PHASE 5: POST-PROCESS =====
            # Follow-up sorular
            follow_ups = []
            if research_context:
                formatted = synthesizer.format_response(full_response, research_context)
                follow_ups = formatted.follow_up_questions
                confidence = formatted.confidence_score
            else:
                confidence = 0.5
            
            # Add assistant response to history
            assistant_msg = {
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat(),
                "sources": [s["url"] for s in web_sources],
            }
            sessions[session_id].append(assistant_msg)
            session_manager.add_message(
                session_id, 
                "assistant", 
                full_response,
                sources=[s["url"] for s in web_sources]
            )
            
            # Track analytics
            analytics.track_chat(
                query=request.message[:100],
                response_length=len(full_response),
                duration_ms=total_time,
                agent="premium_web_search",
                session_id=session_id,
            )
            
            # ===== FINAL: SEND COMPLETION =====
            completion_data = {
                "type": "end",
                "session_id": session_id,
                "sources": web_sources,
                "follow_up_questions": follow_ups[:4],
                "confidence_score": confidence,
                "timing": {
                    "total_ms": total_time,
                    "generation_ms": generation_time,
                    "search_ms": search_time if search_response else 0
                },
                "word_count": len(full_response.split()),
                "sources_used": len(web_sources)
            }
            # Döküman kaynakları da ekle
            if source_map:
                completion_data["document_sources"] = [
                    {'ref': info['letter'], 'filename': info['filename'], 'pages': list(info['pages'])}
                    for info in source_map.values()
                ]
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            analytics.track_error("chat_web_stream", str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/chat/vision", tags=["Chat"])
async def chat_with_vision(
    message: str = Form(...),
    image: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    """
    Görsel analizi ile chat endpoint'i (VLM desteği).
    
    Görsel yükleyerek AI'dan analiz alın.
    """
    import json
    
    async def generate():
        try:
            # Get or create session
            sid = session_id or str(uuid.uuid4())
            
            if sid not in sessions:
                sessions[sid] = []
            
            # Save uploaded image
            upload_dir = settings.DATA_DIR / "uploads" / "images"
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            image_id = str(uuid.uuid4())
            image_ext = Path(image.filename or "image.jpg").suffix or ".jpg"
            image_path = upload_dir / f"{image_id}{image_ext}"
            
            with open(image_path, "wb") as f:
                content = await image.read()
                f.write(content)
            
            # Add user message to history
            sessions[sid].append({
                "role": "user",
                "content": message,
                "image": str(image_path),
                "timestamp": datetime.now().isoformat(),
            })
            
            # Send session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
            
            # Stream response with image
            full_response = ""
            system_prompt = """Sen görsel analizi yapabilen yardımcı bir AI asistanısın. 
Görseli detaylı analiz et ve Türkçe yanıt ver."""
            
            for token in llm_manager.generate_stream_with_image(
                message, 
                str(image_path),
                system_prompt
            ):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Add assistant response to history
            sessions[sid].append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat(),
            })
            
            # Track analytics
            analytics.track_chat(
                query=f"[IMAGE] {message[:80]}",
                response_length=len(full_response),
                duration_ms=0,
                agent="vision",
                session_id=sid,
            )
            
            # Send end event
            yield f"data: {json.dumps({'type': 'end', 'session_id': sid})}\n\n"
            
        except Exception as e:
            analytics.track_error("chat_vision", str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/chat/history/{session_id}", tags=["Chat"])
async def get_chat_history(session_id: str):
    """Session için chat geçmişi."""
    if session_id not in sessions:
        return {"messages": [], "session_id": session_id}
    
    return {
        "messages": sessions[session_id],
        "session_id": session_id,
        "message_count": len(sessions[session_id]),
    }


@app.delete("/api/chat/session/{session_id}", tags=["Chat"])
async def clear_session(session_id: str):
    """Session'ı temizle."""
    if session_id in sessions:
        del sessions[session_id]
    
    return {"message": "Session cleared", "session_id": session_id}


# ============ DOCUMENT ENDPOINTS ============

@app.post("/api/documents/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Döküman yükle ve indexle - ROBUST VERSION.
    
    Desteklenen formatlar: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV, JSON, HTML
    
    Özellikler:
    - Timeout korumalı işleme
    - Çoklu fallback mekanizması
    - Büyük dosya desteği
    - Duplicate kontrolü
    """
    import time
    import warnings
    import asyncio
    import concurrent.futures
    
    start_time = time.time()
    warnings.filterwarnings("ignore")
    
    try:
        # Validate file extension
        filename = file.filename or "unknown"
        extension = Path(filename).suffix.lower()
        
        if extension not in robust_loader.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Desteklenmeyen dosya formatı: {extension}. Desteklenen: {', '.join(robust_loader.SUPPORTED_EXTENSIONS.keys())}",
            )
        
        # DUPLICATE KONTROLÜ
        upload_dir = settings.DATA_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        existing_file = None
        was_updated = False
        
        for f in upload_dir.iterdir():
            if f.is_file():
                parts = f.name.split("_", 1)
                if len(parts) > 1 and parts[1] == filename:
                    existing_file = f
                    break
        
        if existing_file:
            was_updated = True
            old_doc_id = existing_file.name.split("_")[0]
            
            # Vector store'dan eski chunk'ları sil
            try:
                all_data = vector_store.collection.get(include=['metadatas'])
                ids_to_delete = []
                for i, meta in enumerate(all_data.get('metadatas', [])):
                    if meta:
                        orig = meta.get('original_filename', '')
                        if '_' in orig and len(orig.split('_')[0]) == 36:
                            orig = orig.split('_', 1)[1]
                        if orig == filename:
                            ids_to_delete.append(all_data['ids'][i])
                
                if ids_to_delete:
                    vector_store.collection.delete(ids=ids_to_delete)
            except Exception:
                pass
            
            # Eski dosyayı sil
            try:
                existing_file.unlink()
            except Exception:
                pass
        
        # Dosyayı kaydet
        document_id = str(uuid.uuid4())
        file_path = upload_dir / f"{document_id}_{filename}"
        
        # Async file write
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        # ROBUST LOADER ile yükle (timeout korumalı)
        timeout = robust_loader.get_timeout(
            robust_loader.SUPPORTED_EXTENSIONS.get(extension, "default"),
            file_size_mb
        )
        
        # Thread pool'da işle (blocking I/O)
        loop = asyncio.get_event_loop()
        documents, error = await loop.run_in_executor(
            None,
            lambda: robust_loader.load_with_timeout(str(file_path), timeout=timeout)
        )
        
        if error:
            # Hata durumunda bile minimal içerik oluştur
            documents = [{
                "content": f"[Dosya işlenemedi: {filename}]\n\nHata: {error}",
                "metadata": {
                    "source": str(file_path),
                    "filename": filename,
                    "file_type": extension,
                    "error": error[:100]
                }
            }]
        
        if not documents:
            documents = [{
                "content": f"[Boş dosya: {filename}]",
                "metadata": {
                    "source": str(file_path),
                    "filename": filename,
                    "file_type": extension
                }
            }]
        
        # Chunk documents - rag.document_loader.Document formatına çevir
        from rag.document_loader import Document
        doc_objects = [
            Document(content=d["content"], metadata=d["metadata"])
            for d in documents
        ]
        
        chunks = document_chunker.chunk_documents(doc_objects)
        
        if not chunks:
            from rag.chunker import Chunk
            chunks = [Chunk(content=d.content, metadata=d.metadata) for d in doc_objects]
        
        # Vector store'a ekle
        chunk_texts = [c.content for c in chunks]
        chunk_metadatas = [
            {**c.metadata, "document_id": document_id, "original_filename": filename}
            for c in chunks
        ]
        
        vector_store.add_documents(
            documents=chunk_texts,
            metadatas=chunk_metadatas,
        )
        
        # Analytics
        processing_time = time.time() - start_time
        analytics.track_document_upload(
            filename=filename,
            file_size=file_size,
            chunks_created=len(chunks),
        )
        
        status_msg = f"{filename} başarıyla yüklendi ({len(chunks)} parça, {processing_time:.1f}s)"
        if was_updated:
            status_msg += " [güncellendi]"
        
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=filename,
            chunks_created=len(chunks),
            message=status_msg,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        analytics.track_error("upload", str(e))
        raise HTTPException(status_code=500, detail=f"Yükleme hatası: {str(e)[:200]}")


@app.get("/api/documents", tags=["Documents"])
async def list_documents():
    """Yüklenen dökümanları listele."""
    upload_dir = settings.DATA_DIR / "uploads"
    
    if not upload_dir.exists():
        return {"documents": [], "total": 0}
    
    documents = []
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            # Extract original filename from stored name
            parts = file_path.name.split("_", 1)
            doc_id = parts[0] if len(parts) > 1 else None
            original_name = parts[1] if len(parts) > 1 else file_path.name
            
            documents.append({
                "document_id": doc_id,
                "filename": original_name,
                "size": file_path.stat().st_size,
                "uploaded_at": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
            })
    
    return {"documents": documents, "total": len(documents)}


@app.delete("/api/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Dökümanı sil."""
    upload_dir = settings.DATA_DIR / "uploads"
    
    # Find and delete file
    deleted = False
    for file_path in upload_dir.iterdir():
        if file_path.name.startswith(document_id):
            file_path.unlink()
            deleted = True
            break
    
    # Delete from vector store by document_id metadata
    try:
        vector_store.delete_by_metadata({"document_id": document_id})
    except Exception as e:
        # Log but don't fail - file is already deleted
        import logging
        logging.warning(f"Could not delete from vector store: {e}")
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    return {"message": "Döküman silindi", "document_id": document_id}


# ============ SEARCH ENDPOINTS ============

@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_documents(request: SearchRequest):
    """
    Bilgi tabanında semantic arama.
    """
    import time
    start_time = time.time()
    
    try:
        results = vector_store.search_with_scores(
            query=request.query,
            n_results=request.top_k,
            where=request.filter_metadata,
        )
        
        # Calculate actual duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Track analytics with actual duration
        analytics.track_search(
            query=request.query,
            results_count=len(results),
            duration_ms=duration_ms,
        )
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
        )
        
    except Exception as e:
        analytics.track_error("search", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============ ENTERPRISE RAG ENDPOINTS ============

class RAGQueryRequest(BaseModel):
    """Enterprise RAG sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    strategy: Optional[str] = None  # semantic, hybrid, fusion, page_based, multi_query
    top_k: int = Field(default=5, ge=1, le=20)
    filter_metadata: Optional[Dict[str, Any]] = None
    include_sources: bool = True


class RAGStreamRequest(BaseModel):
    """RAG streaming isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    strategy: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class PageSearchRequest(BaseModel):
    """Sayfa bazlı arama isteği."""
    page_numbers: List[int] = Field(..., min_items=1, max_items=50)
    source: Optional[str] = None


@app.post("/api/rag/query", tags=["RAG"])
async def rag_query(request: RAGQueryRequest):
    """
    Enterprise RAG sorgusu.
    
    Gelişmiş retrieval stratejileri ile bilgi tabanından yanıt üret.
    
    Stratejiler:
    - semantic: Vector similarity search
    - hybrid: Semantic + BM25 kombinasyonu
    - fusion: Tüm stratejilerin RRF birleşimi
    - page_based: Sayfa numarasına göre arama
    - multi_query: Query expansion ile arama
    """
    try:
        from rag.orchestrator import rag_orchestrator
        
        result = rag_orchestrator.query(
            query=request.query,
            strategy=request.strategy,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata,
            include_sources=request.include_sources,
        )
        
        return result
        
    except Exception as e:
        analytics.track_error("rag_query", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/stream", tags=["RAG"])
async def rag_stream(request: RAGStreamRequest):
    """
    Streaming RAG yanıtı (SSE).
    
    Real-time token streaming ile RAG yanıtı.
    """
    import json
    
    async def generate():
        try:
            from rag.orchestrator import rag_orchestrator
            
            async for event in rag_orchestrator.stream_response(
                query=request.query,
                strategy=request.strategy,
                top_k=request.top_k,
            ):
                yield f"data: {json.dumps(event)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/rag/search", tags=["RAG"])
async def rag_search_only(request: RAGQueryRequest):
    """
    Sadece RAG retrieval (generation yok).
    
    Dökümanları arar ve ilgili chunk'ları döndürür.
    """
    try:
        from rag.orchestrator import rag_orchestrator
        
        chunks = rag_orchestrator.search_only(
            query=request.query,
            strategy=request.strategy,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata,
        )
        
        return {
            "query": request.query,
            "strategy": request.strategy or "auto",
            "chunks": chunks,
            "total": len(chunks),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/pages", tags=["RAG"])
async def get_pages(request: PageSearchRequest):
    """
    Sayfa numarasına göre içerik getir.
    
    Belirli sayfa numaralarındaki içeriği doğrudan getirir.
    """
    try:
        from rag.orchestrator import rag_orchestrator
        
        pages = rag_orchestrator.get_page_content(
            page_numbers=request.page_numbers,
            source=request.source,
        )
        
        return {
            "requested_pages": request.page_numbers,
            "source": request.source,
            "chunks": pages,
            "total": len(pages),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/analyze", tags=["RAG"])
async def analyze_query(query: str):
    """
    Sorgu analizi yap.
    
    Sorgunun türünü, sayfa numaralarını ve önerilen stratejiyi döndürür.
    """
    try:
        from rag.pipeline import QueryAnalyzer
        
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(query)
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/stats", tags=["RAG"])
async def get_rag_stats():
    """RAG sistem istatistikleri."""
    try:
        from rag.orchestrator import rag_orchestrator
        
        return rag_orchestrator.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/rag/cache/clear", tags=["RAG"])
async def clear_rag_cache():
    """RAG cache'ini temizle."""
    try:
        from rag.orchestrator import rag_orchestrator
        
        rag_orchestrator.clear_cache()
        
        return {"message": "RAG cache temizlendi", "success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/sources", tags=["RAG"])
async def get_document_sources():
    """Yüklenmiş döküman kaynaklarını listele."""
    try:
        sources = vector_store.get_unique_sources()
        stats = vector_store.get_document_stats()
        
        return {
            "sources": sources,
            "total_sources": len(sources),
            "stats": stats,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ RAGAS EVALUATION ENDPOINTS ============

class RAGEvaluationRequest(BaseModel):
    """RAGAS evaluation isteği."""
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None


class BatchEvaluationRequest(BaseModel):
    """Toplu RAGAS evaluation isteği."""
    evaluations: List[RAGEvaluationRequest]


@app.post("/api/rag/evaluate", tags=["RAG", "Evaluation"])
async def evaluate_rag_response(request: RAGEvaluationRequest):
    """
    RAG yanıtını RAGAS metrikleriyle değerlendir.
    
    Faithfulness, Answer Relevancy ve Context Precision skorlarını döndürür.
    """
    try:
        from core.ragas_evaluation import RAGASEvaluator
        
        evaluator = RAGASEvaluator()
        
        # Metrikleri hesapla
        faithfulness = await evaluator.evaluate_faithfulness(
            question=request.question,
            answer=request.answer,
            contexts=request.contexts
        )
        
        relevancy = await evaluator.evaluate_answer_relevancy(
            question=request.question,
            answer=request.answer
        )
        
        context_precision = await evaluator.evaluate_context_precision(
            question=request.question,
            contexts=request.contexts,
            ground_truth=request.ground_truth
        )
        
        # Genel skor hesapla (ağırlıklı ortalama)
        overall_score = (
            faithfulness.get("score", 0) * 0.4 +
            relevancy.get("score", 0) * 0.35 +
            context_precision.get("score", 0) * 0.25
        )
        
        return {
            "success": True,
            "metrics": {
                "faithfulness": faithfulness,
                "answer_relevancy": relevancy,
                "context_precision": context_precision,
            },
            "overall_score": round(overall_score, 4),
            "interpretation": _interpret_ragas_score(overall_score),
        }
        
    except Exception as e:
        logger.error(f"RAGAS evaluation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "metrics": None,
        }


@app.post("/api/rag/evaluate/batch", tags=["RAG", "Evaluation"])
async def batch_evaluate_rag(request: BatchEvaluationRequest):
    """
    Birden fazla RAG yanıtını toplu değerlendir.
    
    Her evaluation için ayrı skorlar ve genel istatistikler döndürür.
    """
    try:
        from core.ragas_evaluation import RAGASEvaluator
        
        evaluator = RAGASEvaluator()
        results = []
        
        for i, eval_request in enumerate(request.evaluations):
            try:
                faithfulness = await evaluator.evaluate_faithfulness(
                    question=eval_request.question,
                    answer=eval_request.answer,
                    contexts=eval_request.contexts
                )
                
                relevancy = await evaluator.evaluate_answer_relevancy(
                    question=eval_request.question,
                    answer=eval_request.answer
                )
                
                context_precision = await evaluator.evaluate_context_precision(
                    question=eval_request.question,
                    contexts=eval_request.contexts,
                    ground_truth=eval_request.ground_truth
                )
                
                overall = (
                    faithfulness.get("score", 0) * 0.4 +
                    relevancy.get("score", 0) * 0.35 +
                    context_precision.get("score", 0) * 0.25
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "faithfulness": faithfulness.get("score", 0),
                    "relevancy": relevancy.get("score", 0),
                    "context_precision": context_precision.get("score", 0),
                    "overall_score": round(overall, 4),
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                })
        
        # Genel istatistikler
        successful = [r for r in results if r.get("success")]
        if successful:
            avg_faithfulness = sum(r["faithfulness"] for r in successful) / len(successful)
            avg_relevancy = sum(r["relevancy"] for r in successful) / len(successful)
            avg_precision = sum(r["context_precision"] for r in successful) / len(successful)
            avg_overall = sum(r["overall_score"] for r in successful) / len(successful)
        else:
            avg_faithfulness = avg_relevancy = avg_precision = avg_overall = 0
        
        return {
            "success": True,
            "total": len(request.evaluations),
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "results": results,
            "aggregate": {
                "avg_faithfulness": round(avg_faithfulness, 4),
                "avg_relevancy": round(avg_relevancy, 4),
                "avg_context_precision": round(avg_precision, 4),
                "avg_overall": round(avg_overall, 4),
            },
            "interpretation": _interpret_ragas_score(avg_overall),
        }
        
    except Exception as e:
        logger.error(f"Batch RAGAS evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rag/evaluate/metrics", tags=["RAG", "Evaluation"])
async def get_evaluation_metrics_info():
    """Kullanılabilir RAGAS metrikleri hakkında bilgi."""
    return {
        "metrics": [
            {
                "name": "faithfulness",
                "description": "Yanıtın bağlamlara ne kadar sadık olduğunu ölçer",
                "range": "0-1",
                "weight": 0.4,
            },
            {
                "name": "answer_relevancy",
                "description": "Yanıtın soruyla ne kadar ilgili olduğunu ölçer",
                "range": "0-1",
                "weight": 0.35,
            },
            {
                "name": "context_precision",
                "description": "Bağlamların ne kadar hassas/ilgili olduğunu ölçer",
                "range": "0-1",
                "weight": 0.25,
            },
        ],
        "interpretation": {
            "excellent": "0.8-1.0: Mükemmel RAG performansı",
            "good": "0.6-0.8: İyi performans, iyileştirme potansiyeli var",
            "fair": "0.4-0.6: Orta, önemli iyileştirme gerekiyor",
            "poor": "0.0-0.4: Zayıf, ciddi iyileştirme gerekiyor",
        },
    }


def _interpret_ragas_score(score: float) -> str:
    """RAGAS skorunu yorumla."""
    if score >= 0.8:
        return "Mükemmel - RAG sistemi yüksek kalitede yanıt üretiyor"
    elif score >= 0.6:
        return "İyi - Performans yeterli, iyileştirme potansiyeli var"
    elif score >= 0.4:
        return "Orta - Önemli iyileştirmeler gerekiyor"
    else:
        return "Zayıf - Ciddi iyileştirme ve hata ayıklama gerekiyor"


# ============ MOE ROUTER ENDPOINTS ============

class MoEQueryRequest(BaseModel):
    """MoE Router sorgu isteği."""
    query: str
    strategy: Optional[str] = "balanced"  # quality, speed, cost, balanced


class MoERouteResponse(BaseModel):
    """MoE routing sonucu."""
    query: str
    complexity: str
    selected_expert: str
    expert_name: str
    confidence: float
    routing_reason: str
    alternatives: List[Dict[str, Any]] = []


@app.post("/api/moe/analyze", response_model=MoERouteResponse, tags=["MoE Router"])
async def analyze_query_routing(request: MoEQueryRequest):
    """
    Sorguyu analiz et ve en uygun expert'i belirle.
    
    Query complexity'yi, domain'i ve gereksinimleri analiz ederek
    optimal model/pipeline seçimi önerir.
    """
    try:
        # Query'i analiz et
        features = moe_router.analyzer.analyze(request.query)
        
        # Stratejiyi ayarla
        if request.strategy == "quality":
            moe_router.strategy = RoutingStrategy.QUALITY
        elif request.strategy == "speed":
            moe_router.strategy = RoutingStrategy.SPEED
        elif request.strategy == "cost":
            moe_router.strategy = RoutingStrategy.COST
        else:
            moe_router.strategy = RoutingStrategy.BALANCED
        
        # Routing yap (sync method)
        route_result = moe_router.route(request.query)
        
        # Alternatifleri hesapla
        alternatives = []
        for expert_type, expert_config in moe_router.experts.items():
            if expert_type != route_result.selected_expert:
                alternatives.append({
                    "expert_type": expert_type.value,
                    "name": expert_config.name,
                    "quality_score": expert_config.quality_score,
                    "avg_latency_ms": expert_config.avg_latency_ms,
                    "cost_per_1k_tokens": expert_config.cost_per_1k_tokens,
                })
        
        return MoERouteResponse(
            query=request.query,
            complexity=features.complexity.value,
            selected_expert=route_result.selected_expert.value,
            expert_name=moe_router.experts[route_result.selected_expert].name,
            confidence=route_result.confidence,
            routing_reason=route_result.reasoning,
            alternatives=sorted(alternatives, key=lambda x: -x["quality_score"])[:3],
        )
        
    except Exception as e:
        logger.error(f"MoE routing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/moe/experts", tags=["MoE Router"])
async def get_available_experts():
    """Kullanılabilir expert'leri listele."""
    experts = []
    for expert_type, config in moe_router.experts.items():
        experts.append({
            "type": expert_type.value,
            "name": config.name,
            "model": config.model,
            "capabilities": config.capabilities,
            "quality_score": config.quality_score,
            "avg_latency_ms": config.avg_latency_ms,
            "cost_per_1k_tokens": config.cost_per_1k_tokens,
            "max_tokens": config.max_tokens,
            "is_available": config.is_available,
            "supports_streaming": config.supports_streaming,
        })
    
    return {
        "experts": experts,
        "total": len(experts),
        "current_strategy": moe_router.strategy.value,
    }


@app.get("/api/moe/complexity-levels", tags=["MoE Router"])
async def get_complexity_levels():
    """Query complexity seviyeleri hakkında bilgi."""
    return {
        "levels": [
            {
                "level": QueryComplexity.TRIVIAL.value,
                "description": "Basit evet/hayır soruları, tanımlar",
                "example": "Python nedir?",
                "recommended_expert": ExpertType.LOCAL_SMALL.value,
            },
            {
                "level": QueryComplexity.SIMPLE.value,
                "description": "Tek adımlı sorular",
                "example": "Python'da liste nasıl oluşturulur?",
                "recommended_expert": ExpertType.LOCAL_LARGE.value,
            },
            {
                "level": QueryComplexity.MODERATE.value,
                "description": "Çok adımlı akıl yürütme gerektiren",
                "example": "REST API tasarımı için best practice'ler nelerdir?",
                "recommended_expert": ExpertType.RAG_SIMPLE.value,
            },
            {
                "level": QueryComplexity.COMPLEX.value,
                "description": "Derin analiz ve sentez gerektiren",
                "example": "Microservices vs Monolith - hangisi ne zaman tercih edilmeli?",
                "recommended_expert": ExpertType.RAG_ADVANCED.value,
            },
            {
                "level": QueryComplexity.EXPERT.value,
                "description": "Uzmanlık gerektiren, çok boyutlu",
                "example": "Dağıtık sistemlerde eventual consistency nasıl sağlanır?",
                "recommended_expert": ExpertType.CLOUD_SMART.value,
            },
        ]
    }


@app.post("/api/moe/strategy", tags=["MoE Router"])
async def set_routing_strategy(strategy: str):
    """
    Routing stratejisini değiştir.
    
    Strategies:
    - quality: En yüksek kalite
    - speed: En hızlı yanıt
    - cost: En düşük maliyet
    - balanced: Dengeli seçim
    """
    valid_strategies = ["quality", "speed", "cost", "balanced"]
    if strategy not in valid_strategies:
        raise HTTPException(
            status_code=400, 
            detail=f"Geçersiz strateji. Geçerli değerler: {valid_strategies}"
        )
    
    strategy_map = {
        "quality": RoutingStrategy.QUALITY,
        "speed": RoutingStrategy.SPEED,
        "cost": RoutingStrategy.COST,
        "balanced": RoutingStrategy.BALANCED,
    }
    
    moe_router.strategy = strategy_map[strategy]
    
    return {
        "message": f"Routing stratejisi '{strategy}' olarak ayarlandı",
        "current_strategy": moe_router.strategy.value,
    }


@app.get("/api/moe/stats", tags=["MoE Router"])
async def get_moe_stats():
    """MoE Router istatistikleri."""
    # Routing history analizi
    history = moe_router.routing_history[-100:]  # Son 100 routing
    
    if not history:
        return {
            "total_routings": 0,
            "expert_usage": {},
            "avg_confidence": 0,
            "complexity_distribution": {},
        }
    
    expert_usage = {}
    complexity_dist = {}
    total_confidence = 0
    
    for entry in history:
        expert = entry.get("expert", "unknown")
        expert_usage[expert] = expert_usage.get(expert, 0) + 1
        
        complexity = entry.get("complexity", "unknown")
        complexity_dist[complexity] = complexity_dist.get(complexity, 0) + 1
        
        total_confidence += entry.get("confidence", 0)
    
    return {
        "total_routings": len(moe_router.routing_history),
        "recent_routings": len(history),
        "expert_usage": expert_usage,
        "avg_confidence": round(total_confidence / len(history), 4) if history else 0,
        "complexity_distribution": complexity_dist,
        "current_strategy": moe_router.strategy.value,
    }


# ============ PLUGIN ENDPOINTS ============

@app.get("/api/plugins", tags=["Plugins"])
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


@app.post("/api/plugins/{plugin_name}/activate", tags=["Plugins"])
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


@app.post("/api/plugins/{plugin_name}/deactivate", tags=["Plugins"])
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


class PluginExecuteRequest(BaseModel):
    """Plugin çalıştırma isteği."""
    input_data: Dict[str, Any]


@app.post("/api/plugins/{plugin_name}/execute", tags=["Plugins"])
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


@app.get("/api/plugins/stats", tags=["Plugins"])
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


@app.post("/api/plugins/initialize", tags=["Plugins"])
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

@app.get("/api/observability/metrics", tags=["Observability"])
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


@app.get("/api/observability/traces", tags=["Observability"])
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


@app.get("/api/observability/dashboard", tags=["Observability"])
async def get_observability_dashboard():
    """
    Kapsamlı observability dashboard verisi.
    
    Tüm LLM operasyonlarının özet istatistiklerini döndürür.
    """
    try:
        from core.langfuse_observability import Observability
        from core.analytics import analytics
        
        obs = Observability()
        
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


@app.post("/api/observability/score", tags=["Observability"])
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


# ============ ADMIN ENDPOINTS ============

@app.get("/api/admin/stats", tags=["Admin"])
async def get_stats():
    """Sistem istatistikleri."""
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
    
    return {
        "documents": {
            "total": doc_count,
            "chunks": vs_stats.get("total_documents", vector_store.count()) if vs_stats else vector_store.count(),
            "total_size_mb": total_size / (1024 * 1024)
        },
        "sessions": len(sessions),
        "total_messages": sum(len(s) for s in sessions.values()),
        "vector_store": vs_stats
    }


@app.post("/api/admin/reindex", tags=["Admin"])
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
                    print(f"Reindex hatası: {file_path} - {e}")
        
        return {
            "message": "Yeniden indexleme tamamlandı",
            "indexed_chunks": total_chunks,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ WEBSOCKET ENDPOINTS ============

# Import WebSocket v2
from api.websocket_v2 import ws_manager, websocket_endpoint_v2

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """
    Real-time streaming chat için WebSocket endpoint.
    
    Bağlantı sonrası JSON formatında mesaj gönderin:
    {"type": "chat", "message": "Merhaba", "session_id": "optional-session-id"}
    {"type": "stop"} - Streaming'i durdur
    {"type": "ping"} - Keepalive ping
    """
    await websocket_endpoint_v2(websocket, client_id)


@app.websocket("/ws/v2/{client_id}")
async def websocket_chat_v2(websocket: WebSocket, client_id: str):
    """
    WebSocket v2 - Enterprise-grade streaming.
    
    Özellikler:
    - ANLIK streaming (buffering yok)
    - Keepalive ping/pong (25 saniye)
    - Rate limiting (10 istek/5 saniye)
    - Stop komutu desteği
    - Detaylı istatistikler
    """
    await websocket_endpoint_v2(websocket, client_id)


@app.get("/api/ws/clients", tags=["WebSocket"])
async def get_connected_clients():
    """Bağlı WebSocket client'larını listele."""
    return {
        "connected_clients": ws_manager.get_clients_info(),
        "total": ws_manager.active_count,
        "stats": ws_manager.get_stats(),
    }


@app.get("/api/ws/stats", tags=["WebSocket"])
async def get_websocket_stats():
    """WebSocket istatistiklerini al."""
    return ws_manager.get_stats()


# ============ HEALTH & MONITORING ENDPOINTS ============

@app.get("/api/health/detailed", tags=["Health"])
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


@app.get("/api/analytics/stats", tags=["Analytics"])
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


@app.get("/api/analytics/activity", tags=["Analytics"])
async def get_hourly_activity(days: int = 7):
    """Saatlik aktivite dağılımı."""
    try:
        return {"hourly_activity": analytics.get_hourly_activity(days)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/agents", tags=["Analytics"])
async def get_agent_usage(days: int = 30):
    """Agent kullanım istatistikleri."""
    try:
        return {"agent_usage": analytics.get_agent_usage(days)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ RATE LIMITING INFO ============

@app.get("/api/ratelimit/status", tags=["Rate Limit"])
async def get_rate_limit_status(request: Request):
    """Mevcut rate limit durumu."""
    client_ip = request.client.host if request.client else "unknown"
    return rate_limiter.get_client_stats(client_ip)


@app.get("/api/ratelimit/global", tags=["Rate Limit"])
async def get_global_rate_limit_status():
    """Global rate limit istatistikleri."""
    return rate_limiter.get_global_stats()


# ============ EXPORT/IMPORT ENDPOINTS ============

@app.get("/api/export/sessions", tags=["Export"])
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


@app.get("/api/export/analytics", tags=["Export"])
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


@app.get("/api/export/backup", tags=["Export"])
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


# ============ ENHANCED AGENT ENDPOINTS ============

class EnhancedAgentRequest(BaseModel):
    """Enhanced Agent isteği."""
    query: str = Field(..., min_length=1, max_length=10000)
    mode: Optional[str] = None  # auto, react, plan, simple, hybrid
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ReActRequest(BaseModel):
    """ReAct Agent isteği."""
    query: str = Field(..., min_length=1, max_length=10000)
    context: Optional[Dict[str, Any]] = None
    max_iterations: int = Field(default=10, ge=1, le=20)


class PlanningRequest(BaseModel):
    """Planning Agent isteği."""
    goal: str = Field(..., min_length=1, max_length=10000)
    strategy: Optional[str] = None  # linear, tree_of_thoughts, hierarchical, adaptive
    context: Optional[Dict[str, Any]] = None


class CritiqueRequest(BaseModel):
    """Critique isteği."""
    content: str = Field(..., min_length=1, max_length=50000)
    original_question: Optional[str] = None
    context: Optional[str] = None


class RefineRequest(BaseModel):
    """Refinement isteği."""
    content: str = Field(..., min_length=1, max_length=50000)
    original_question: Optional[str] = None
    max_iterations: int = Field(default=3, ge=1, le=10)


@app.post("/api/agent/execute", tags=["Enhanced Agent"])
async def execute_enhanced_agent(request: EnhancedAgentRequest):
    """
    Enhanced Agent ile sorgu çalıştır.
    
    Otomatik mod seçimi, ReAct reasoning, Planning, Self-Critique
    ve Iterative Refinement özelliklerini içerir.
    
    Modlar:
    - auto: Sorguya göre otomatik mod seçimi
    - react: ReAct (Reasoning + Acting) pattern
    - plan: Task decomposition ve planning
    - simple: Basit LLM çağrısı
    - hybrid: ReAct + Planning kombinasyonu
    """
    try:
        from agents.enhanced_agent import enhanced_agent, ExecutionMode
        
        # Set session if provided
        if request.session_id:
            enhanced_agent.set_session(request.session_id)
        
        # Determine mode
        mode = None
        if request.mode:
            mode_map = {
                "auto": ExecutionMode.AUTO,
                "react": ExecutionMode.REACT,
                "plan": ExecutionMode.PLAN,
                "simple": ExecutionMode.SIMPLE,
                "hybrid": ExecutionMode.HYBRID,
            }
            mode = mode_map.get(request.mode.lower())
        
        # Execute
        response = await enhanced_agent.execute(
            query=request.query,
            mode=mode,
            context=request.context,
        )
        
        return response.to_dict()
        
    except Exception as e:
        analytics.track_error("enhanced_agent", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/execute/stream", tags=["Enhanced Agent"])
async def execute_enhanced_agent_stream(request: EnhancedAgentRequest):
    """
    Enhanced Agent streaming çalıştırma (SSE).
    
    Real-time progress updates ile agent çalışmasını izleyin.
    """
    import json
    
    async def generate():
        try:
            from agents.enhanced_agent import enhanced_agent, ExecutionMode
            
            if request.session_id:
                enhanced_agent.set_session(request.session_id)
            
            mode = None
            if request.mode:
                mode_map = {
                    "auto": ExecutionMode.AUTO,
                    "react": ExecutionMode.REACT,
                    "plan": ExecutionMode.PLAN,
                    "simple": ExecutionMode.SIMPLE,
                    "hybrid": ExecutionMode.HYBRID,
                }
                mode = mode_map.get(request.mode.lower())
            
            async for event in enhanced_agent.stream_execute(
                query=request.query,
                mode=mode,
                context=request.context,
            ):
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': {'error': str(e)}})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/agent/react", tags=["Enhanced Agent"])
async def run_react_agent(request: ReActRequest):
    """
    ReAct Agent ile sorgu çalıştır.
    
    Thought → Action → Observation döngüsü ile şeffaf reasoning.
    Tool kullanımı ve düşünce zinciri görüntülenir.
    """
    try:
        from agents.react_agent import react_agent
        
        trace = await react_agent.run(
            query=request.query,
            context=request.context,
        )
        
        return {
            "final_answer": trace.final_answer,
            "trace": trace.to_dict(),
            "formatted_trace": trace.format_trace(),
            "success": trace.success,
            "thoughts_count": trace.thoughts_count,
            "tool_calls_count": trace.tool_calls_count,
            "total_time_ms": trace.total_time_ms,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/react/stream", tags=["Enhanced Agent"])
async def run_react_agent_stream(request: ReActRequest):
    """
    Streaming ReAct Agent (SSE).
    
    Her thought, action ve observation adımını real-time olarak izleyin.
    """
    import json
    
    async def generate():
        try:
            from agents.react_agent import streaming_react_agent
            
            async for event in streaming_react_agent.run_streaming(
                query=request.query,
                context=request.context,
            ):
                yield f"data: {json.dumps(event)}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.post("/api/agent/plan", tags=["Enhanced Agent"])
async def create_and_execute_plan(request: PlanningRequest):
    """
    Planning Agent ile hedef için plan oluştur ve çalıştır.
    
    Karmaşık görevleri alt görevlere ayırır ve sırayla çalıştırır.
    
    Stratejiler:
    - linear: Sıralı adımlar
    - tree_of_thoughts: ToT ile farklı yaklaşımları keşfet
    - hierarchical: Hiyerarşik alt görevler
    - adaptive: Dinamik strateji seçimi
    """
    try:
        from agents.planning_agent import planning_agent, PlanningStrategy
        
        # Determine strategy
        strategy = None
        if request.strategy:
            strategy_map = {
                "linear": PlanningStrategy.LINEAR,
                "tree_of_thoughts": PlanningStrategy.TREE_OF_THOUGHTS,
                "hierarchical": PlanningStrategy.HIERARCHICAL,
                "adaptive": PlanningStrategy.ADAPTIVE,
                "least_to_most": PlanningStrategy.LEAST_TO_MOST,
            }
            strategy = strategy_map.get(request.strategy.lower())
        
        # Create plan
        plan = planning_agent.create_plan(
            goal=request.goal,
            strategy=strategy,
            context=request.context,
        )
        
        # Execute plan
        executed_plan = await planning_agent.execute_plan(plan)
        
        return {
            "plan": executed_plan.to_dict(),
            "visualization": executed_plan.visualize(),
            "progress": executed_plan.get_progress(),
            "success": executed_plan.status.value == "completed",
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/plan/create", tags=["Enhanced Agent"])
async def create_plan_only(request: PlanningRequest):
    """
    Sadece plan oluştur (çalıştırma yok).
    
    Planı önizle ve gerekirse düzenle.
    """
    try:
        from agents.planning_agent import planning_agent, PlanningStrategy
        
        strategy = None
        if request.strategy:
            strategy_map = {
                "linear": PlanningStrategy.LINEAR,
                "tree_of_thoughts": PlanningStrategy.TREE_OF_THOUGHTS,
                "hierarchical": PlanningStrategy.HIERARCHICAL,
                "adaptive": PlanningStrategy.ADAPTIVE,
            }
            strategy = strategy_map.get(request.strategy.lower())
        
        plan = planning_agent.create_plan(
            goal=request.goal,
            strategy=strategy,
            context=request.context,
        )
        
        return {
            "plan": plan.to_dict(),
            "visualization": plan.visualize(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/critique", tags=["Enhanced Agent"])
async def critique_content(request: CritiqueRequest):
    """
    İçeriği kalite açısından değerlendir.
    
    Faktüel doğruluk, mantıksal tutarlılık, tamlık,
    ilgililik, açıklık ve hallucination kontrolü yapar.
    """
    try:
        from agents.self_reflection import critic_agent
        
        result = critic_agent.critique(
            content=request.content,
            original_question=request.original_question,
            context=request.context,
        )
        
        return {
            "critique": result.to_dict(),
            "report": result.format_report(),
            "needs_refinement": result.needs_refinement(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/refine", tags=["Enhanced Agent"])
async def refine_content(request: RefineRequest):
    """
    İçeriği iteratif olarak iyileştir.
    
    Kalite eşiğine ulaşana kadar critique ve refinement döngüsü çalışır.
    """
    try:
        from agents.self_reflection import iterative_refiner
        
        trace = iterative_refiner.refine(
            content=request.content,
            original_question=request.original_question,
        )
        
        return {
            "original_content": trace.original_content,
            "refined_content": trace.final_content,
            "initial_score": trace.initial_score,
            "final_score": trace.final_score,
            "improvement": trace.total_improvement,
            "iterations": trace.total_iterations,
            "converged": trace.converged,
            "convergence_reason": trace.convergence_reason,
            "trace": trace.to_dict(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/reflect", tags=["Enhanced Agent"])
async def self_reflect(content: str = Form(...), context: Optional[str] = Form(None)):
    """
    İçerik üzerinde self-reflection yap.
    
    Düşünce sürecini değerlendir, hataları tespit et ve iyileştirme öner.
    """
    try:
        from agents.self_reflection import self_reflector
        
        result = self_reflector.reflect(
            thought=content,
            context=context,
        )
        
        return result.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/constitutional-check", tags=["Enhanced Agent"])
async def constitutional_check(content: str = Form(...)):
    """
    Constitutional AI kontrolü.
    
    İçeriğin etik kurallara uygunluğunu kontrol eder.
    """
    try:
        from agents.self_reflection import constitutional_checker
        
        result = constitutional_checker.check(content)
        
        return {
            "is_safe": result.get("is_safe", False),
            "ethical_score": result.get("overall_ethical_score", 0),
            "principle_scores": result.get("principle_scores", {}),
            "violations": result.get("violations", []),
            "concerns": result.get("concerns", []),
            "revision_needed": result.get("revision_needed", False),
            "revision_suggestions": result.get("revision_suggestions", []),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/analyze-query", tags=["Enhanced Agent"])
async def analyze_query(query: str):
    """
    Sorguyu analiz et.
    
    Karmaşıklık, önerilen mod, gereken araçlar vb. bilgileri döndürür.
    """
    try:
        from agents.enhanced_agent import QueryAnalyzer
        
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(query)
        
        return analysis.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/stats", tags=["Enhanced Agent"])
async def get_enhanced_agent_stats():
    """Enhanced Agent istatistikleri."""
    try:
        from agents.enhanced_agent import enhanced_agent
        
        return enhanced_agent.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agent/history", tags=["Enhanced Agent"])
async def get_agent_history(limit: int = 10):
    """Son agent yanıtlarının geçmişi."""
    try:
        from agents.enhanced_agent import enhanced_agent
        
        history = enhanced_agent.get_history(limit)
        
        return {
            "history": [h.to_dict() for h in history],
            "total": len(history),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/agent/history", tags=["Enhanced Agent"])
async def clear_agent_history():
    """Agent geçmişini temizle."""
    try:
        from agents.enhanced_agent import enhanced_agent
        
        enhanced_agent.clear_history()
        
        return {"message": "Agent history cleared", "success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/import/sessions", tags=["Import"])
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


# ============ INCLUDE ROUTERS ============

app.include_router(learning_router)


# ============ RUN SERVER ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
    )
