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
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Add user message to history
        sessions[session_id].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Prepare context with chat history
        context = request.context or {}
        context["chat_history"] = sessions[session_id][-10:]  # Last 10 messages
        
        # Execute through orchestrator
        response = orchestrator.execute(request.message, context)
        
        # Add assistant response to history
        sessions[session_id].append({
            "role": "assistant",
            "content": response.content,
            "timestamp": datetime.now().isoformat(),
        })
        
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
            
            if session_id not in sessions:
                sessions[session_id] = []
            
            # Add user message to history
            sessions[session_id].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat(),
            })
            
            # Send session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # Prepare context
            context = request.context or {}
            context["chat_history"] = sessions[session_id][-10:]
            
            # Stream tokens from LLM
            full_response = ""
            
            # Get system prompt from orchestrator
            system_prompt = """Sen yardımcı bir AI asistanısın. Türkçe yanıt ver."""
            
            for token in llm_manager.generate_stream(request.message, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Add assistant response to history
            sessions[session_id].append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now().isoformat(),
            })
            
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
        analytics.track_upload(
            filename=filename,
            file_size=file_path.stat().st_size,
            chunks_count=len(chunks),
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
        )
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
        )
        
    except Exception as e:
        analytics.track_error("search", str(e))
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
