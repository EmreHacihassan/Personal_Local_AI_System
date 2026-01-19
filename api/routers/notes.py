"""
Notes & Folders Router
=======================

File-based kalıcı Notes ve Folders API.
NotesManager kullanarak JSON persistence sağlar.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from core.notes_manager import notes_manager


router = APIRouter(prefix="/api", tags=["Notes", "Folders"])
logger = logging.getLogger(__name__)


# ============ PYDANTIC MODELS ============

class NoteCreate(BaseModel):
    """Not oluşturma modeli."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")
    folder_id: Optional[str] = None
    color: Optional[str] = "yellow"
    pinned: Optional[bool] = False
    tags: Optional[List[str]] = []


class NoteUpdate(BaseModel):
    """Not güncelleme modeli."""
    title: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None
    color: Optional[str] = None
    pinned: Optional[bool] = None
    tags: Optional[List[str]] = None


class FolderCreate(BaseModel):
    """Klasör oluşturma modeli."""
    name: str = Field(..., min_length=1, max_length=100)
    parent_id: Optional[str] = None
    color: Optional[str] = "blue"
    icon: Optional[str] = "📁"


class FolderUpdate(BaseModel):
    """Klasör güncelleme modeli."""
    name: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


# ============ NOTES ENDPOINTS ============

@router.get("/notes")
async def get_notes(
    folder_id: Optional[str] = None,
    include_subfolders: bool = False,
    search_query: Optional[str] = None,
    pinned_only: bool = False,
):
    """
    Tüm notları listele. Opsiyonel olarak klasöre veya arama sorgusuna göre filtrele.
    """
    try:
        notes = notes_manager.list_notes(
            folder_id=folder_id,
            include_subfolders=include_subfolders,
            search_query=search_query,
            pinned_only=pinned_only,
        )
        # Convert to dicts
        notes_list = [n.to_dict() for n in notes]
        return {"notes": notes_list, "count": len(notes_list)}
        
    except Exception as e:
        logger.error(f"Notes list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes")
async def create_note(note: NoteCreate):
    """
    Yeni not oluştur. File-based kalıcı depolama kullanır.
    """
    try:
        created_note = notes_manager.create_note(
            title=note.title,
            content=note.content,
            folder_id=note.folder_id,
            color=note.color or "yellow",
            tags=note.tags or [],
            pinned=note.pinned or False,
        )
        return created_note.to_dict()
        
    except Exception as e:
        logger.error(f"Note create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}")
async def get_note(note_id: str):
    """
    Belirli bir notu getir.
    """
    try:
        note = notes_manager.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        return note.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notes/{note_id}")
async def update_note(note_id: str, note: NoteUpdate):
    """
    Bir notu güncelle.
    """
    try:
        updated_note = notes_manager.update_note(
            note_id=note_id,
            title=note.title,
            content=note.content,
            folder_id=note.folder_id,
            color=note.color,
            tags=note.tags,
            pinned=note.pinned,
        )
        
        if not updated_note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        
        return updated_note.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}")
async def delete_note(note_id: str):
    """
    Bir notu sil.
    """
    try:
        success = notes_manager.delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        
        return {"message": "Not silindi", "note_id": note_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/pin")
async def toggle_note_pin(note_id: str):
    """
    Notu sabitle/kaldır.
    """
    try:
        note = notes_manager.toggle_pin(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        return note.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note pin toggle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/move")
async def move_note(note_id: str, folder_id: Optional[str] = None):
    """
    Notu başka klasöre taşı.
    """
    try:
        note = notes_manager.move_note(note_id, folder_id)
        if not note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        return note.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note move error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ FOLDERS ENDPOINTS ============

@router.get("/folders")
async def get_folders(parent_id: Optional[str] = None):
    """
    Klasörleri listele. parent_id=None ise root klasörleri döndürür.
    """
    try:
        folders = notes_manager.list_folders(parent_id=parent_id)
        return {"folders": [f.to_dict() for f in folders], "count": len(folders)}
        
    except Exception as e:
        logger.error(f"Folders list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/all")
async def get_all_folders():
    """
    Tüm klasörleri getir (ağaç yapısı için).
    """
    try:
        folders = notes_manager.get_all_folders()
        return {"folders": [f.to_dict() for f in folders], "count": len(folders)}
        
    except Exception as e:
        logger.error(f"All folders list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/folders")
async def create_folder(folder: FolderCreate):
    """
    Yeni klasör oluştur.
    """
    try:
        created_folder = notes_manager.create_folder(
            name=folder.name,
            parent_id=folder.parent_id,
            color=folder.color or "blue",
            icon=folder.icon or "📁",
        )
        return created_folder.to_dict()
        
    except Exception as e:
        logger.error(f"Folder create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/{folder_id}")
async def get_folder(folder_id: str):
    """
    Belirli bir klasörü getir.
    """
    try:
        folder = notes_manager.get_folder(folder_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Klasör bulunamadı")
        return folder.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/{folder_id}/path")
async def get_folder_path(folder_id: str):
    """
    Klasörün breadcrumb path'ini getir.
    """
    try:
        path = notes_manager.get_folder_path(folder_id)
        return {"path": [f.to_dict() for f in path]}
        
    except Exception as e:
        logger.error(f"Folder path error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/folders/{folder_id}")
async def update_folder(folder_id: str, folder: FolderUpdate):
    """
    Klasörü güncelle.
    """
    try:
        updated_folder = notes_manager.update_folder(
            folder_id=folder_id,
            name=folder.name,
            color=folder.color,
            icon=folder.icon,
            parent_id=folder.parent_id,
        )
        
        if not updated_folder:
            raise HTTPException(status_code=404, detail="Klasör bulunamadı")
        
        return updated_folder.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, recursive: bool = True):
    """
    Klasörü sil. recursive=True ise içindeki notları ve alt klasörleri de siler.
    """
    try:
        success = notes_manager.delete_folder(folder_id, recursive=recursive)
        if not success:
            raise HTTPException(status_code=404, detail="Klasör bulunamadı veya boş değil")
        
        return {"message": "Klasör silindi", "folder_id": folder_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
