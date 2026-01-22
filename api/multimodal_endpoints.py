"""
Multi-Modal RAG API Endpoints
PDF, Image, Audio, Video indexing and retrieval
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/multimodal", tags=["Multi-Modal RAG"])

_rag = None

def get_rag():
    global _rag
    if _rag is None:
        from core.multimodal_rag import get_multimodal_rag
        _rag = get_multimodal_rag()
    return _rag


class SearchRequest(BaseModel):
    query: str
    media_types: Optional[List[str]] = None
    top_k: int = 10


class AskRequest(BaseModel):
    question: str
    media_types: Optional[List[str]] = None


@router.get("/status")
async def get_status():
    """Get Multi-Modal RAG status"""
    rag = get_rag()
    stats = rag.get_stats()
    return {
        "status": "available",
        **stats
    }


@router.post("/index/file")
async def index_file(filepath: str = Form(...)):
    """Index a file from the filesystem"""
    try:
        rag = get_rag()
        doc = await rag.index_file(filepath)
        
        return {
            "success": True,
            "document_id": doc.id,
            "filename": doc.filename,
            "media_type": doc.media_type.value,
            "chunks": len(doc.chunks),
            "images": len(doc.image_descriptions),
            "has_audio": doc.audio_transcript is not None,
            "keyframes": len(doc.video_keyframes)
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/upload")
async def index_upload(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    """Upload and index a file"""
    try:
        rag = get_rag()
        
        content = await file.read()
        
        metadata = {}
        if title:
            metadata["title"] = title
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = [t.strip() for t in tags.split(",")]
        
        doc = await rag.index_content(
            content=content,
            filename=file.filename,
            metadata=metadata
        )
        
        return {
            "success": True,
            "document_id": doc.id,
            "filename": doc.filename,
            "media_type": doc.media_type.value,
            "chunks": len(doc.chunks),
            "images": len(doc.image_descriptions),
            "has_audio": doc.audio_transcript is not None,
            "keyframes": len(doc.video_keyframes)
        }
        
    except Exception as e:
        logger.error(f"Upload indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(request: SearchRequest):
    """Search across all indexed content"""
    try:
        rag = get_rag()
        
        from core.multimodal_rag import MediaType
        
        media_types = None
        if request.media_types:
            media_types = [MediaType(t) for t in request.media_types]
        
        results = await rag.search(
            query=request.query,
            media_types=media_types,
            top_k=request.top_k
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_question(request: AskRequest):
    """Ask a question and get AI-generated answer with sources"""
    try:
        rag = get_rag()
        
        from core.multimodal_rag import MediaType
        
        media_types = None
        if request.media_types:
            media_types = [MediaType(t) for t in request.media_types]
        
        result = await rag.ask(
            question=request.question,
            media_types=media_types
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Ask failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(
    media_type: Optional[str] = Query(None, description="Filter by media type")
):
    """List all indexed documents"""
    rag = get_rag()
    
    from core.multimodal_rag import MediaType
    
    mt = None
    if media_type:
        mt = MediaType(media_type)
    
    return {
        "documents": rag.list_documents(mt)
    }


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document details"""
    rag = get_rag()
    doc = rag.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    rag = get_rag()
    success = rag.delete_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"success": True, "message": f"Document {doc_id} deleted"}


@router.get("/stats")
async def get_stats():
    """Get indexing statistics"""
    rag = get_rag()
    return rag.get_stats()


# Batch operations
@router.post("/index/batch")
async def batch_index(filepaths: List[str]):
    """Index multiple files"""
    rag = get_rag()
    
    results = []
    for filepath in filepaths:
        try:
            doc = await rag.index_file(filepath)
            results.append({
                "filepath": filepath,
                "success": True,
                "document_id": doc.id,
                "media_type": doc.media_type.value
            })
        except Exception as e:
            results.append({
                "filepath": filepath,
                "success": False,
                "error": str(e)
            })
    
    return {
        "results": results,
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"])
    }
