"""
Enterprise AI Assistant - FastAPI Main
Endüstri Standartlarında Kurumsal AI Çözümü

Ana API uygulaması - RESTful endpoints ve WebSocket.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
from agents.orchestrator import orchestrator
from rag.document_loader import document_loader
from rag.chunker import document_chunker
from api.websocket import websocket_endpoint, manager


# ============ PYDANTIC MODELS ============

class ChatRequest(BaseModel):
    """Chat isteği modeli."""
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


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


# ============ FASTAPI APP ============

app = FastAPI(
    title="Enterprise AI Assistant API",
    description="Endüstri Standartlarında Kurumsal AI Çözümü - REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage (in-memory for simplicity)
sessions: Dict[str, List[Dict[str, Any]]] = {}


# ============ HEALTH & STATUS ============

@app.get("/", tags=["Status"])
async def root():
    """API ana sayfası."""
    return {
        "name": "Enterprise AI Assistant",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Status"])
async def health_check():
    """Sistem sağlık kontrolü."""
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


@app.get("/status", tags=["Status"])
async def get_status():
    """Detaylı sistem durumu."""
    return {
        "llm": llm_manager.get_status(),
        "vector_store": vector_store.get_stats(),
        "agents": orchestrator.get_agents_status(),
        "config": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "top_k": settings.TOP_K_RESULTS,
        },
    }


# ============ CHAT ENDPOINTS ============

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Ana chat endpoint'i.
    
    Kullanıcı mesajını işler ve AI yanıtı döndürür.
    """
    try:
        # Get or create session from file-based storage
        session_id = request.session_id or str(uuid.uuid4())
        
        session = session_manager.get_session(session_id)
        if session is None:
            session = session_manager.create_session()
            session_id = session.session_id
        
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
        
        # Prepare context with chat history
        context = request.context or {}
        context["chat_history"] = recent_history
        context["history_text"] = history_text
        
        # Execute through orchestrator
        response = orchestrator.execute(request.message, context)
        
        # Add assistant response to history (both in-memory and file)
        assistant_msg = {
            "role": "assistant",
            "content": response.content,
            "timestamp": datetime.now().isoformat(),
        }
        sessions[session_id].append(assistant_msg)
        session_manager.add_message(session_id, "assistant", response.content)
        
        # Track analytics
        analytics.track_chat(
            query=request.message[:100],
            response_length=len(response.content),
            duration_ms=0,  # TODO: Calculate actual duration
            agent=response.metadata.get("agent", "unknown"),
            session_id=session_id,
        )
        
        return ChatResponse(
            response=response.content,
            session_id=session_id,
            sources=response.sources,
            metadata=response.metadata,
            timestamp=datetime.now().isoformat(),
        )
        
    except Exception as e:
        # Track error
        analytics.track_error("chat", str(e))
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
                session_id = session.session_id
            
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
            
            # Build chat history context for LLM
            recent_history = sessions[session_id][-10:]
            history_text = ""
            if len(recent_history) > 1:  # More than just current message
                history_text = "\n\nÖnceki konuşma geçmişi:\n"
                for msg in recent_history[:-1]:  # Exclude current message
                    role_name = "Kullanıcı" if msg["role"] == "user" else "Asistan"
                    history_text += f"{role_name}: {msg['content']}\n"
            
            # Prepare context
            context = request.context or {}
            context["chat_history"] = recent_history
            
            # Stream tokens from LLM
            full_response = ""
            
            # Get system prompt with history context
            system_prompt = f"""Sen yardımcı bir AI asistanısın. Türkçe yanıt ver.
{history_text}
Yukarıdaki konuşma geçmişini dikkate alarak kullanıcının mevcut sorusuna cevap ver."""
            
            for token in llm_manager.generate_stream(request.message, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
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
            
            # Send end event
            yield f"data: {json.dumps({'type': 'end', 'session_id': session_id})}\n\n"
            
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
    Döküman yükle ve indexle.
    
    Desteklenen formatlar: PDF, DOCX, TXT, MD, CSV, JSON, HTML
    """
    try:
        # Validate file extension
        filename = file.filename or "unknown"
        extension = Path(filename).suffix.lower()
        
        if extension not in document_loader.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Desteklenmeyen dosya formatı: {extension}",
            )
        
        # Save file
        upload_dir = settings.DATA_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        document_id = str(uuid.uuid4())
        file_path = upload_dir / f"{document_id}_{filename}"
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Load and process document
        documents = document_loader.load_file(str(file_path))
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="Döküman içeriği okunamadı",
            )
        
        # Chunk documents
        chunks = document_chunker.chunk_documents(documents)
        
        # Add to vector store
        chunk_texts = [c.content for c in chunks]
        chunk_metadatas = [
            {**c.metadata, "document_id": document_id, "original_filename": filename}
            for c in chunks
        ]
        
        vector_store.add_documents(
            documents=chunk_texts,
            metadatas=chunk_metadatas,
        )
        
        # Track analytics
        analytics.track_document_upload(
            filename=filename,
            file_size=file_path.stat().st_size,
            chunks_created=len(chunks),
        )
        
        return DocumentUploadResponse(
            success=True,
            document_id=document_id,
            filename=filename,
            chunks_created=len(chunks),
            message=f"{filename} başarıyla yüklendi ve indexlendi",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        analytics.track_error("upload", str(e))
        raise HTTPException(status_code=500, detail=str(e))


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
    
    # TODO: Also delete from vector store by document_id metadata
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    return {"message": "Döküman silindi", "document_id": document_id}


# ============ SEARCH ENDPOINTS ============

@app.post("/api/search", response_model=SearchResponse, tags=["Search"])
async def search_documents(request: SearchRequest):
    """
    Bilgi tabanında semantic arama.
    """
    try:
        results = vector_store.search_with_scores(
            query=request.query,
            n_results=request.top_k,
            where=request.filter_metadata,
        )
        
        # Track analytics
        analytics.track_search(
            query=request.query,
            results_count=len(results),
            duration_ms=0,  # TODO: Calculate actual duration
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


# ============ ADMIN ENDPOINTS ============

@app.get("/api/admin/stats", tags=["Admin"])
async def get_stats():
    """Sistem istatistikleri."""
    return {
        "documents": vector_store.count(),
        "sessions": len(sessions),
        "total_messages": sum(len(s) for s in sessions.values()),
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

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """
    Real-time streaming chat için WebSocket endpoint.
    
    Bağlantı sonrası JSON formatında mesaj gönderin:
    {"type": "chat", "message": "Merhaba", "session_id": "optional-session-id"}
    """
    await websocket_endpoint(websocket, client_id)


@app.get("/api/ws/clients", tags=["WebSocket"])
async def get_connected_clients():
    """Bağlı WebSocket client'larını listele."""
    return {
        "connected_clients": list(manager.active_connections.keys()),
        "total": len(manager.active_connections),
    }


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


# ============ RUN SERVER ============

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
    )
