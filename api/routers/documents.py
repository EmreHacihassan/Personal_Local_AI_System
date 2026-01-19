"""
Documents Router
=================

Döküman yükleme, listeleme, indirme ve silme endpoint'leri.
PDF, DOCX, PPTX, XLSX, TXT ve daha fazlasını destekler.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import logging
import uuid

from core.config import settings
from core.vector_store import vector_store
from core.analytics import analytics
from rag.document_loader import document_loader, Document
from rag.chunker import document_chunker, Chunk
from rag.async_processor import robust_loader


router = APIRouter(prefix="/api/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


# ============ PYDANTIC MODELS ============

class DocumentUploadResponse(BaseModel):
    """Döküman yükleme yanıtı."""
    success: bool
    document_id: str
    filename: str
    chunks_created: int
    message: str


# ============ DOCUMENT ENDPOINTS ============

@router.post("/upload", response_model=DocumentUploadResponse)
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
        doc_objects = [
            Document(content=d["content"], metadata=d["metadata"])
            for d in documents
        ]
        
        chunks = document_chunker.chunk_documents(doc_objects)
        
        if not chunks:
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


@router.get("")
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


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """Dökümanı indir."""
    upload_dir = settings.DATA_DIR / "uploads"
    
    # Find file
    for file_path in upload_dir.iterdir():
        if file_path.name.startswith(document_id):
            return FileResponse(
                path=str(file_path),
                filename=file_path.name.split("_", 1)[-1] if "_" in file_path.name else file_path.name,
                media_type="application/octet-stream"
            )
    
    raise HTTPException(status_code=404, detail="Döküman bulunamadı")


@router.get("/{document_id}/preview")
async def preview_document(document_id: str):
    """Döküman içeriğini önizle (text tabanlı dosyalar için)."""
    upload_dir = settings.DATA_DIR / "uploads"
    
    # Find file
    for file_path in upload_dir.iterdir():
        if file_path.name.startswith(document_id):
            # Get file extension
            ext = file_path.suffix.lower()
            
            # Text-based files
            if ext in ['.txt', '.md', '.json', '.csv', '.log', '.py', '.js', '.html', '.xml']:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    return {
                        "success": True,
                        "content": content[:50000],  # Limit to 50KB
                        "truncated": len(content) > 50000,
                        "filename": file_path.name,
                        "type": "text"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Dosya okunamadı: {str(e)}",
                        "type": "error"
                    }
            
            # PDF files - extract text if possible
            elif ext == '.pdf':
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(file_path))
                    text = ""
                    for page in reader.pages[:10]:  # First 10 pages
                        text += page.extract_text() + "\n---\n"
                    return {
                        "success": True,
                        "content": text[:50000],
                        "truncated": len(text) > 50000 or len(reader.pages) > 10,
                        "filename": file_path.name,
                        "type": "pdf",
                        "page_count": len(reader.pages)
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"PDF okunamadı: {str(e)}",
                        "type": "error"
                    }
            
            # Binary files - not previewable
            else:
                return {
                    "success": False,
                    "error": "Bu dosya türü önizlenemez",
                    "type": "binary",
                    "filename": file_path.name
                }
    
    raise HTTPException(status_code=404, detail="Döküman bulunamadı")


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Dökümanı sil."""
    upload_dir = settings.DATA_DIR / "uploads"
    
    # Find and delete file
    deleted = False
    deleted_filename = None
    for file_path in upload_dir.iterdir():
        if file_path.name.startswith(document_id):
            deleted_filename = file_path.name
            file_path.unlink()
            deleted = True
            break
    
    # Delete from vector store by document_id metadata
    try:
        # Get all vectors and filter by document_id
        all_data = vector_store.collection.get(include=['metadatas'])
        ids_to_delete = []
        
        for i, meta in enumerate(all_data.get('metadatas', [])):
            if meta and meta.get('document_id') == document_id:
                ids_to_delete.append(all_data['ids'][i])
        
        if ids_to_delete:
            vector_store.collection.delete(ids=ids_to_delete)
    except Exception as e:
        logger.error(f"Vector store delete error: {e}")
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    return {
        "message": "Döküman silindi",
        "document_id": document_id,
        "filename": deleted_filename,
    }


@router.post("/batch-upload")
async def batch_upload_documents(files: List[UploadFile] = File(...)):
    """Birden fazla dökümanı toplu yükle."""
    results = []
    
    for file in files:
        try:
            result = await upload_document(file)
            results.append({
                "filename": file.filename,
                "success": True,
                "document_id": result.document_id,
                "chunks_created": result.chunks_created,
            })
        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e.detail),
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e),
            })
    
    successful = sum(1 for r in results if r.get("success"))
    
    return {
        "results": results,
        "total": len(files),
        "successful": successful,
        "failed": len(files) - successful,
    }


@router.get("/{document_id}/chunks")
async def get_document_chunks(document_id: str, limit: int = 100):
    """Dökümanın chunk'larını getir."""
    try:
        all_data = vector_store.collection.get(include=['metadatas', 'documents'])
        chunks = []
        
        for i, meta in enumerate(all_data.get('metadatas', [])):
            if meta and meta.get('document_id') == document_id:
                chunks.append({
                    "id": all_data['ids'][i],
                    "content": all_data['documents'][i][:500] + "..." if len(all_data['documents'][i]) > 500 else all_data['documents'][i],
                    "metadata": meta,
                })
        
        return {
            "document_id": document_id,
            "chunks": chunks[:limit],
            "total": len(chunks),
            "truncated": len(chunks) > limit,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
