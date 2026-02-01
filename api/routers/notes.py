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
    locked: Optional[bool] = None  # Kilitleme durumu
    encrypted: Optional[bool] = None  # Şifreleme durumu


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
    locked: Optional[bool] = None  # Kilitleme durumu


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
            locked=folder.locked,  # Kilit durumu güncelleme
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
    Klasörü sil. Kilitli klasörler silinemez. recursive=True ise içindeki notları ve alt klasörleri de siler.
    """
    try:
        # Kilit kontrolü
        folder = notes_manager.get_folder(folder_id)
        if folder and getattr(folder, 'locked', False):
            raise HTTPException(status_code=403, detail="Kilitli klasör silinemez. Önce kilidi kaldırın.")
        
        success = notes_manager.delete_folder(folder_id, recursive=recursive)
        if not success:
            raise HTTPException(status_code=404, detail="Klasör bulunamadı veya boş değil")
        
        return {"message": "Klasör silindi", "folder_id": folder_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Folder delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ AI ENDPOINTS ============

@router.post("/notes/{note_id}/summarize")
async def summarize_note(note_id: str, max_length: int = 200):
    """
    AI ile notu özetle.
    """
    try:
        from core.notes_ai import get_notes_ai
        notes_ai = get_notes_ai(notes_manager=notes_manager)
        result = await notes_ai.summarize_note(note_id, max_length)
        return result
    except Exception as e:
        logger.error(f"Note summarize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/suggest-tags")
async def suggest_note_tags(note_id: str, max_tags: int = 5):
    """
    Not için AI etiket önerisi al.
    """
    try:
        from core.notes_ai import get_notes_ai
        notes_ai = get_notes_ai(notes_manager=notes_manager)
        tags = await notes_ai.suggest_tags(note_id=note_id, max_tags=max_tags)
        return {"tags": tags}
    except Exception as e:
        logger.error(f"Tag suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/related")
async def get_related_notes(note_id: str, max_results: int = 5):
    """
    Bir nota semantik olarak benzer notları getir.
    """
    try:
        from core.notes_ai import get_notes_ai
        notes_ai = get_notes_ai(notes_manager=notes_manager)
        related = await notes_ai.find_related_notes(note_id, max_results)
        return {"related_notes": related}
    except Exception as e:
        logger.error(f"Related notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/enrich")
async def enrich_note(note_id: str):
    """
    AI ile notu zenginleştir - eksik bilgileri ekle.
    """
    try:
        from core.notes_ai import get_notes_ai
        notes_ai = get_notes_ai(notes_manager=notes_manager)
        result = await notes_ai.enrich_note(note_id)
        return result
    except Exception as e:
        logger.error(f"Note enrich error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/flashcards")
async def generate_flashcards(note_id: str, count: int = 5):
    """
    Nottan flashcard (çalışma kartı) üret.
    """
    try:
        from core.notes_ai import get_notes_ai
        notes_ai = get_notes_ai(notes_manager=notes_manager)
        flashcards = await notes_ai.generate_flashcards(note_id, count)
        return {"flashcards": [fc.to_dict() for fc in flashcards]}
    except Exception as e:
        logger.error(f"Flashcard generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AskNotesRequest(BaseModel):
    """Notlara soru sorma modeli."""
    question: str
    note_ids: Optional[List[str]] = None
    include_all: bool = False


@router.post("/notes/ask")
async def ask_notes(request: AskNotesRequest):
    """
    Notlara soru sor - RAG tabanlı soru-cevap.
    """
    try:
        from core.notes_ai import get_notes_ai
        notes_ai = get_notes_ai(notes_manager=notes_manager)
        result = await notes_ai.ask_notes(
            question=request.question,
            note_ids=request.note_ids,
            include_all=request.include_all
        )
        return result
    except Exception as e:
        logger.error(f"Ask notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ GRAPH / MIND ENDPOINTS ============

@router.get("/notes/graph")
async def get_notes_graph(
    include_orphans: bool = True,
    include_similarity: bool = True,
    similarity_threshold: float = 0.2,
    include_tags: bool = True,
    folder_filter: Optional[str] = None
):
    """
    Mind graf verisi - React Flow için nodes ve edges.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        graph = note_graph.build_graph(
            include_orphans=include_orphans,
            include_similarity=include_similarity,
            similarity_threshold=similarity_threshold,
            include_tags=include_tags,
            folder_filter=folder_filter
        )
        return graph
    except Exception as e:
        logger.error(f"Graph build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/links")
async def get_note_links(note_id: str):
    """
    Not bağlantılarını getir (wiki-style [[linkler]]).
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        links = note_graph.get_note_links(note_id)
        return {"links": links}
    except Exception as e:
        logger.error(f"Note links error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/backlinks")
async def get_note_backlinks(note_id: str):
    """
    Bu nota bağlanan notları getir (backlinks).
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        backlinks = note_graph.get_backlinks(note_id)
        return {"backlinks": backlinks}
    except Exception as e:
        logger.error(f"Note backlinks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/graph/stats")
async def get_graph_stats():
    """
    Graf istatistiklerini getir.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        stats = note_graph.get_graph_stats()
        return stats
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/graph/central")
async def get_central_notes(limit: int = 5):
    """
    En çok bağlantılı (merkezi) notları getir.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        central = note_graph.get_central_notes(limit)
        return {"central_notes": central}
    except Exception as e:
        logger.error(f"Central notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/graph/orphans")
async def get_orphan_notes():
    """
    Hiçbir bağlantısı olmayan notları getir.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        orphans = note_graph.get_orphan_notes()
        return {"orphan_notes": [n.to_dict() for n in orphans]}
    except Exception as e:
        logger.error(f"Orphan notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/suggestions")
async def get_connection_suggestions(note_id: str, limit: int = 3):
    """
    Not için önerilen bağlantıları getir.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        suggestions = note_graph.suggest_connections(note_id, limit)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Connection suggestions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ PREMIUM MIND MAP ENDPOINTS ============

@router.get("/notes/graph/path")
async def find_graph_path(source_id: str, target_id: str):
    """
    🔗 İki not arasındaki en kısa yolu bul.
    Path finding with BFS algorithm.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        path_result = note_graph.find_path(source_id, target_id)
        return path_result
    except Exception as e:
        logger.error(f"Path finding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/graph/clusters")
async def get_note_clusters():
    """
    🎨 Notları konu bazlı kümele.
    AI-powered topic clustering.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        clusters = note_graph.cluster_notes_by_similarity()
        return clusters
    except Exception as e:
        logger.error(f"Clustering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/graph/connections")
async def get_connection_counts():
    """
    🔥 Her node'un bağlantı sayısı (Heat Map için).
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        counts = note_graph.get_connection_counts()
        return {"connections": counts}
    except Exception as e:
        logger.error(f"Connection counts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/details")
async def get_note_details(note_id: str):
    """
    📋 Not detayları (Sidebar preview için).
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        details = note_graph.get_node_details(note_id)
        if not details:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/ai-summary")
async def get_note_ai_summary(note_id: str):
    """
    🤖 AI ile not özeti oluştur.
    """
    try:
        from core.note_graph import get_note_graph
        note_graph = get_note_graph(notes_manager=notes_manager)
        summary = await note_graph.generate_ai_summary(note_id)
        return {"summary": summary}
    except Exception as e:
        logger.error(f"AI summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ NOTES STATS ============

@router.get("/notes/stats")
async def get_notes_stats():
    """
    Not istatistiklerini getir.
    """
    try:
        stats = notes_manager.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Notes stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ TEMPLATES ============

NOTE_TEMPLATES = [
    {
        "id": "meeting",
        "name": "Toplantı Notu",
        "icon": "📋",
        "content": """# Toplantı Notu

**Tarih:** {tarih}
**Katılımcılar:** 

## Gündem
- 

## Notlar


## Aksiyonlar
- [ ] 

## Sonraki Toplantı
"""
    },
    {
        "id": "lecture",
        "name": "Ders Notu",
        "icon": "📚",
        "content": """# {konu}

## Özet


## Ana Kavramlar
1. 
2. 
3. 

## Detaylar


## Önemli Noktalar
> 

## Sorular
- 
"""
    },
    {
        "id": "daily",
        "name": "Günlük",
        "icon": "📔",
        "content": """# {tarih} Günlüğü

## Bugün Neler Oldu?


## Öğrendiklerim


## Yarın İçin


## Notlar
"""
    },
    {
        "id": "research",
        "name": "Araştırma",
        "icon": "🔬",
        "content": """# Araştırma: {konu}

## Amaç


## Kaynaklar
- 

## Bulgular


## Sonuç


## Referanslar
1. 
"""
    },
    {
        "id": "project",
        "name": "Proje Planı",
        "icon": "🎯",
        "content": """# Proje: {proje_adı}

## Hedef


## Kapsam
- 

## Takvim
| Aşama | Tarih | Durum |
|-------|-------|-------|
|       |       | ⏳    |

## Kaynaklar


## Riskler
- 

## Notlar
"""
    },
    {
        "id": "idea",
        "name": "Fikir",
        "icon": "💡",
        "content": """# Fikir: {başlık}

## Açıklama


## Neden Önemli?


## Nasıl Uygulanır?


## İlgili Konular
- [[]]
"""
    }
]


@router.get("/notes/templates")
async def get_note_templates():
    """
    Mevcut not şablonlarını getir.
    """
    return {"templates": NOTE_TEMPLATES}


# ============ TRASH ENDPOINTS (MUST BE BEFORE {note_id} ROUTES) ============

@router.get("/notes/trash")
async def get_trash():
    """
    Çöp kutusundaki notları getir.
    Silinen notlar burada saklanır ve geri yüklenebilir.
    """
    try:
        trash = notes_manager.get_trash()
        return {
            "trash": [t.to_dict() for t in trash],
            "count": len(trash),
        }
    except Exception as e:
        logger.error(f"Get trash error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/trash/count")
async def get_trash_count():
    """
    Çöp kutusundaki not sayısını getir.
    """
    try:
        count = notes_manager.get_trash_count()
        return {"count": count}
    except Exception as e:
        logger.error(f"Get trash count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/trash/{trash_id}")
async def get_trash_note(trash_id: str):
    """
    Çöp kutusundan belirli bir notu getir.
    """
    try:
        trash_note = notes_manager.get_trash_note(trash_id)
        if not trash_note:
            raise HTTPException(status_code=404, detail="Not çöp kutusunda bulunamadı")
        return trash_note.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get trash note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/trash/{trash_id}/restore")
async def restore_from_trash(trash_id: str):
    """
    Notu çöp kutusundan geri yükle.
    Not orijinal klasörüne geri döner ve versiyonları da geri yüklenir.
    """
    try:
        restored_note = notes_manager.restore_from_trash(trash_id)
        if not restored_note:
            raise HTTPException(status_code=404, detail="Not çöp kutusunda bulunamadı")
        
        return {
            "message": "Not başarıyla geri yüklendi",
            "note": restored_note.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore from trash error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/trash/{trash_id}")
async def permanent_delete(trash_id: str):
    """
    Notu kalıcı olarak sil (geri alınamaz!).
    """
    try:
        success = notes_manager.permanent_delete(trash_id)
        if not success:
            raise HTTPException(status_code=404, detail="Not çöp kutusunda bulunamadı")
        
        return {"message": "Not kalıcı olarak silindi", "trash_id": trash_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permanent delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/trash")
async def empty_trash():
    """
    Çöp kutusunu tamamen boşalt (tüm notlar kalıcı olarak silinir!).
    """
    try:
        deleted_count = notes_manager.empty_trash()
        return {
            "message": f"Çöp kutusu boşaltıldı, {deleted_count} not kalıcı olarak silindi",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error(f"Empty trash error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ NOTE CRUD OPERATIONS (MOVED) ============

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
            locked=note.locked,
            encrypted=note.encrypted,
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
    Bir notu sil. Kilitli notlar silinemez.
    """
    try:
        # Kilit kontrolü
        note = notes_manager.get_note(note_id)
        if note and getattr(note, 'locked', False):
            raise HTTPException(status_code=403, detail="Kilitli not silinemez. Önce kilidi kaldırın.")
        
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


# ============ VERSİYON ENDPOINTS ============

@router.get("/notes/{note_id}/versions")
async def get_note_versions(note_id: str):
    """
    Notun tüm versiyonlarını getir (en yeniden eskiye).
    Her not için maksimum 10 versiyon saklanır.
    """
    try:
        # Önce notun var olduğunu kontrol et
        note = notes_manager.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        
        versions = notes_manager.get_note_versions(note_id)
        return {
            "note_id": note_id,
            "versions": [v.to_dict() for v in versions],
            "count": len(versions),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get versions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/versions/{version_id}")
async def get_version(note_id: str, version_id: str):
    """
    Belirli bir versiyonu getir.
    """
    try:
        version = notes_manager.get_version(version_id)
        if not version or version.note_id != note_id:
            raise HTTPException(status_code=404, detail="Versiyon bulunamadı")
        return version.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get version error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/{note_id}/restore/{version_id}")
async def restore_version(note_id: str, version_id: str):
    """
    Notu belirli bir versiyona geri döndür.
    Mevcut durum otomatik olarak yeni bir versiyon olarak kaydedilir.
    """
    try:
        restored_note = notes_manager.restore_version(note_id, version_id)
        if not restored_note:
            raise HTTPException(status_code=404, detail="Not veya versiyon bulunamadı")
        
        return {
            "message": "Versiyon başarıyla geri yüklendi",
            "note": restored_note.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore version error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/{note_id}/diff/{version_id_1}/{version_id_2}")
async def get_version_diff(note_id: str, version_id_1: str, version_id_2: str):
    """
    İki versiyon arasındaki farkları getir.
    Side-by-side diff görünümü için kullanılır.
    """
    try:
        diff = notes_manager.get_version_diff(note_id, version_id_1, version_id_2)
        if "error" in diff:
            raise HTTPException(status_code=404, detail=diff["error"])
        return diff
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}/versions/{version_id}")
async def delete_version(note_id: str, version_id: str):
    """
    Belirli bir versiyonu sil.
    """
    try:
        version = notes_manager.get_version(version_id)
        if not version or version.note_id != note_id:
            raise HTTPException(status_code=404, detail="Versiyon bulunamadı")
        
        success = notes_manager.delete_version(version_id)
        if not success:
            raise HTTPException(status_code=500, detail="Versiyon silinemedi")
        
        return {"message": "Versiyon silindi", "version_id": version_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete version error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notes/{note_id}/versions")
async def clear_note_versions(note_id: str):
    """
    Notun tüm versiyonlarını sil.
    """
    try:
        note = notes_manager.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        
        deleted_count = notes_manager.clear_note_versions(note_id)
        return {
            "message": f"{deleted_count} versiyon silindi",
            "note_id": note_id,
            "deleted_count": deleted_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear versions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ OCR / VİZYON ENDPOINTS ============

class OCRRequest(BaseModel):
    """OCR istek modeli."""
    image_path: str
    extract_formulas: bool = False


@router.post("/notes/ocr")
async def extract_text_from_image(request: OCRRequest):
    """
    Görseldan metin çıkar (OCR).
    LLaVA Vision modeli kullanılır.
    """
    try:
        from core.notes_vision import get_notes_vision
        notes_vision = get_notes_vision()
        
        if request.extract_formulas:
            result = await notes_vision.extract_latex_formula(request.image_path)
        else:
            result = await notes_vision.extract_text_from_image(request.image_path)
        
        return result
    except Exception as e:
        logger.error(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ImageDescriptionRequest(BaseModel):
    """Görsel açıklama istek modeli."""
    image_path: str
    language: str = "tr"


@router.post("/notes/describe-image")
async def describe_image(request: ImageDescriptionRequest):
    """
    Görsel için AI açıklama oluştur.
    """
    try:
        from core.notes_vision import get_notes_vision
        notes_vision = get_notes_vision()
        result = await notes_vision.generate_image_description(
            request.image_path,
            language=request.language
        )
        return result
    except Exception as e:
        logger.error(f"Image description error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ PREMIUM FEATURES ============

@router.get("/notes/premium/insights/{note_id}")
async def get_note_insights(note_id: str):
    """
    🧠 Smart Insights - Not analizi (kelime sayısı, okunabilirlik, sentiment, öneriler).
    """
    try:
        from core.notes_premium import get_premium_manager
        
        note = notes_manager.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Not bulunamadı")
        
        pm = get_premium_manager()
        insights = pm.analyze_note(note.content, note_id)
        
        return {
            "success": True,
            "note_id": note_id,
            "title": note.title,
            "insights": {
                "word_count": insights.word_count,
                "character_count": insights.character_count,
                "sentence_count": insights.sentence_count,
                "paragraph_count": insights.paragraph_count,
                "reading_time_minutes": insights.reading_time_minutes,
                "readability_score": insights.readability_score,
                "sentiment": insights.sentiment,
                "suggestions": insights.suggestions,
                "has_links": insights.has_links,
                "has_images": insights.has_images,
                "has_code": insights.has_code,
                "has_latex": insights.has_latex,
                "markdown_elements": insights.markdown_elements,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Note insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/premium/stats")
async def get_user_stats():
    """
    🏆 Gamification Stats - Kullanıcı istatistikleri, rozetler, level.
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        return {
            "success": True,
            **pm.get_user_stats()
        }
    except Exception as e:
        logger.error(f"User stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/premium/streak")
async def get_writing_streak():
    """
    🔥 Writing Streak - Yazma serisi bilgisi.
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        return {
            "success": True,
            **pm.get_streak_info()
        }
    except Exception as e:
        logger.error(f"Streak error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notes/premium/activity")
async def record_activity(activity_type: str = "note_edit"):
    """
    📊 Activity Recording - Aktivite kaydet (streak için).
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        streak = pm.record_activity(activity_type)
        return {
            "success": True,
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
        }
    except Exception as e:
        logger.error(f"Activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FocusSessionRequest(BaseModel):
    """Focus session istek modeli."""
    duration_minutes: int = 25
    break_minutes: int = 5
    note_id: Optional[str] = None


@router.post("/notes/premium/focus/start")
async def start_focus_session(request: FocusSessionRequest):
    """
    ⏱️ Pomodoro Focus - Odaklanma oturumu başlat.
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        session = pm.start_focus_session(
            duration_minutes=request.duration_minutes,
            break_minutes=request.break_minutes,
            note_id=request.note_id
        )
        return {
            "success": True,
            "session_id": session.session_id,
            "duration_minutes": session.duration_minutes,
            "break_minutes": session.break_minutes,
            "start_time": session.start_time,
        }
    except Exception as e:
        logger.error(f"Focus start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/premium/focus/active")
async def get_active_focus_session():
    """
    Aktif focus oturumunu getir.
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        session = pm.get_active_session()
        return {
            "success": True,
            "active": session is not None,
            "session": session,
        }
    except Exception as e:
        logger.error(f"Active session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FocusCompleteRequest(BaseModel):
    """Focus tamamlama modeli."""
    session_id: str
    words_written: int = 0


@router.post("/notes/premium/focus/complete")
async def complete_focus_session(request: FocusCompleteRequest):
    """
    ✅ Focus oturumu tamamla.
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        result = pm.complete_focus_session(request.session_id, request.words_written)
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Focus complete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notes/premium/digest")
async def get_daily_digest():
    """
    📊 Daily Digest - Günlük özet ve öneriler.
    """
    try:
        from core.notes_premium import get_premium_manager
        pm = get_premium_manager()
        return {
            "success": True,
            **pm.get_daily_digest()
        }
    except Exception as e:
        logger.error(f"Daily digest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

