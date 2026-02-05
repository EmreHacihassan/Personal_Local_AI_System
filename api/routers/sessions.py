"""
Sessions API Router
====================

Session management endpoints - CRUD operations for chat sessions.

Features:
- List all sessions with pagination
- Get/Update/Delete individual sessions
- Session search with filters
- Tags and categories management
- Session title generation
- Old session cleanup
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.session_manager import session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Sessions"])


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SessionResponse(BaseModel):
    """Session response modeli."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    is_pinned: bool = False
    tags: List[str] = []
    category: Optional[str] = None


class SessionMessagesResponse(BaseModel):
    """Session mesajları response modeli."""
    session: SessionResponse
    messages: List[Dict[str, Any]]


class SessionUpdateRequest(BaseModel):
    """Session güncelleme isteği"""
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class GenerateTitleRequest(BaseModel):
    """AI ile başlık oluşturma isteği"""
    first_message: str


# =============================================================================
# SESSION ENDPOINTS
# =============================================================================

@router.get("/sessions", tags=["Sessions"])
@router.get("/chat/sessions", tags=["Sessions"])
async def get_sessions(limit: int = 500):
    """
    Tüm oturumları listele.
    Dosya tabanlı session_manager kullanır - kalıcı depolama.
    
    Args:
        limit: Maksimum döndürülecek session sayısı (default: 500)
    """
    try:
        session_list = session_manager.list_sessions(limit=limit)
        return {"sessions": session_list, "total": len(session_list)}
    except Exception as e:
        logger.error(f"Sessions list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/tags", tags=["Sessions"])
async def get_all_tags():
    """
    Tüm session'larda kullanılan etiketleri getir.
    """
    try:
        tags = session_manager.get_all_tags()
        return {"tags": tags, "total": len(tags)}
    except Exception as e:
        logger.error(f"Tags fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/categories", tags=["Sessions"])
async def get_all_categories():
    """
    Tüm session'larda kullanılan kategorileri getir.
    """
    try:
        categories = session_manager.get_all_categories()
        return {"categories": categories, "total": len(categories)}
    except Exception as e:
        logger.error(f"Categories fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/search", tags=["Sessions"])
async def advanced_session_search(
    query: str = "",
    date_from: str = None,
    date_to: str = None,
    tags: List[str] = Query(None),
    category: str = None,
    pinned_only: bool = False,
    favorites_only: bool = False,
    limit: int = 100
):
    """
    Gelişmiş session ve mesaj araması.
    
    Args:
        query: Arama metni
        date_from: Başlangıç tarihi (YYYY-MM-DD)
        date_to: Bitiş tarihi (YYYY-MM-DD)
        tags: Etiket filtresi
        category: Kategori filtresi
        pinned_only: Sadece sabitlenmiş
        favorites_only: Sadece favoriler
        limit: Maksimum sonuç sayısı
    """
    try:
        results = session_manager.advanced_search(
            query=query,
            date_from=date_from or "",
            date_to=date_to or "",
            tags=tags,
            category=category or "",
            pinned_only=pinned_only,
            favorites_only=favorites_only,
            limit=limit
        )
        
        # Her sonuç için eşleşen mesajları da getir
        enriched_results = []
        for result in results:
            session_data = session_manager.get_session(result["id"])
            matched_messages = []
            
            if session_data and query:
                query_lower = query.lower()
                for i, msg in enumerate(session_data.messages):
                    msg_content = msg.content if hasattr(msg, 'content') else msg.get("content", "")
                    if query_lower in msg_content.lower():
                        matched_messages.append({
                            "index": i,
                            "role": msg.role if hasattr(msg, 'role') else msg.get("role"),
                            "snippet": msg_content[:200] + "..." if len(msg_content) > 200 else msg_content
                        })
            
            enriched_results.append({
                **result,
                "matched_messages": matched_messages[:5]  # Max 5 eşleşme
            })
        
        return {
            "results": enriched_results,
            "total": len(enriched_results),
            "query": query
        }
    except Exception as e:
        logger.error(f"Session search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", tags=["Sessions"])
async def get_session(session_id: str):
    """
    Belirli bir oturumu ve mesajlarını getir.
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        session_dict = session.to_dict()
        
        session_info = {
            "id": session_dict["id"],
            "title": session_dict["title"],
            "created_at": session_dict["created_at"],
            "updated_at": session_dict["updated_at"],
            "message_count": len(session_dict["messages"]),
            "is_pinned": session_dict.get("is_pinned", False),
            "tags": session_dict.get("tags", []),
            "category": session_dict.get("category", ""),
        }
        
        return {
            "session": session_info,
            "messages": session_dict["messages"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """
    Bir oturumu sil.
    """
    try:
        deleted = session_manager.delete_session(session_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        return {"message": "Oturum silindi", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/sessions/{session_id}", tags=["Sessions"])
async def update_session(session_id: str, request: SessionUpdateRequest):
    """
    Oturum bilgilerini güncelle (title, pin status, tags, category).
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        # Güncellenecek alanları uygula
        if request.title is not None:
            session_manager.update_session_title(session_id, request.title)
        
        if request.is_pinned is not None:
            if request.is_pinned != session.is_pinned:
                session_manager.toggle_pin(session_id)
        
        if request.tags is not None:
            for tag in list(session.tags):
                session_manager.remove_tag(session_id, tag)
            for tag in request.tags:
                session_manager.add_tag(session_id, tag)
        
        if request.category is not None:
            session_manager.set_category(session_id, request.category)
        
        # Güncellenmiş session'ı al
        updated_session = session_manager.get_session(session_id)
        
        return {
            "success": True,
            "session": updated_session.to_dict() if updated_session else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/generate-title", tags=["Sessions"])
async def generate_session_title(session_id: str, request: GenerateTitleRequest):
    """
    AI kullanarak session başlığı oluştur.
    """
    try:
        from core.llm_manager import llm_manager
        
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        # AI ile başlık oluştur
        prompt = f"""Aşağıdaki mesaj için kısa (2-5 kelime) ve açıklayıcı bir başlık oluştur.
        Sadece başlığı yaz, başka bir şey yazma.
        
        Mesaj: {request.first_message[:500]}
        
        Başlık:"""
        
        title = llm_manager.generate(
            prompt=prompt,
            system_prompt="Sen bir başlık oluşturma asistanısın. Kısa ve öz başlıklar üret.",
            temperature=0.3,
            max_tokens=30
        ).strip()
        
        # Başlığı temizle
        title = title.strip('"\'').replace('\n', ' ').strip()
        if len(title) > 50:
            title = title[:47] + "..."
        
        # Başlığı kaydet
        session_manager.update_session_title(session_id, title)
        
        return {
            "success": True,
            "title": title,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Title generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/cleanup/old", tags=["Sessions"])
async def cleanup_old_sessions(days: int = 7):
    """
    Eski oturumları temizle.
    
    Args:
        days: Kaç günden eski oturumlar silinsin (varsayılan: 7)
        
    Returns:
        Temizleme raporu (silinen sayı, korunan pinned sayısı)
    
    Sabitlenmiş (pinned) oturumlar korunur.
    """
    try:
        result = session_manager.cleanup_old_sessions(days=days, keep_pinned=True)
        return {
            "success": True,
            "message": f"{result['deleted_count']} eski oturum silindi",
            **result
        }
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
