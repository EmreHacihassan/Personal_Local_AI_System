"""
AI ile Öğren - API Endpoints
Learning Workspace API Routes

Çalışma ortamları, dökümanlar ve testler için API.
"""

import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from core.learning_workspace import (
    learning_workspace_manager,
    LearningWorkspace,
    StudyDocument,
    Test,
    TestType,
    TestStatus,
    DocumentStatus,
    WorkspaceStatus
)
from core.study_document_generator import study_document_generator
from core.test_generator import test_generator
from core.vector_store import vector_store
from core.config import settings


router = APIRouter(prefix="/api/learning", tags=["Learning"])


# ==================== PYDANTIC MODELS ====================

class CreateWorkspaceRequest(BaseModel):
    """Çalışma ortamı oluşturma isteği."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    topic: str = Field(default="", max_length=200)
    initial_sources: List[str] = Field(default=[])


class UpdateWorkspaceRequest(BaseModel):
    """Çalışma ortamı güncelleme isteği."""
    name: Optional[str] = None
    description: Optional[str] = None
    topic: Optional[str] = None


class ToggleSourceRequest(BaseModel):
    """Kaynak aktif/deaktif isteği."""
    source_id: str
    active: bool


class BulkToggleSourceRequest(BaseModel):
    """Toplu kaynak aktif/deaktif isteği."""
    active: bool


class CreateDocumentRequest(BaseModel):
    """Çalışma dökümanı oluşturma isteği."""
    title: str = Field(..., min_length=1, max_length=200)
    topic: str = Field(..., min_length=1, max_length=500)
    page_count: int = Field(..., ge=1, le=40)
    style: str = Field(default="detailed")
    custom_instructions: str = Field(default="", max_length=2000)


class UpdateDocumentRequest(BaseModel):
    """Döküman güncelleme isteği."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    topic: Optional[str] = Field(None, min_length=1, max_length=500)
    page_count: Optional[int] = Field(None, ge=1, le=40)
    style: Optional[str] = None


class CreateTestRequest(BaseModel):
    """Test oluşturma isteği."""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    test_type: str = Field(default="multiple_choice")
    question_count: int = Field(..., ge=1, le=50)
    difficulty: str = Field(default="mixed")
    custom_instructions: str = Field(default="", max_length=2000)


class SubmitAnswerRequest(BaseModel):
    """Cevap gönderme isteği."""
    question_id: str
    answer: str


class ExplainQuestionRequest(BaseModel):
    """Soru açıklama isteği."""
    question_id: str
    user_question: str


class ChatMessageRequest(BaseModel):
    """Chat mesajı isteği."""
    message: str = Field(..., min_length=1, max_length=5000)


# ==================== WORKSPACE ENDPOINTS ====================

@router.get("/workspaces")
async def list_workspaces(include_archived: bool = False):
    """Tüm çalışma ortamlarını listele."""
    workspaces = learning_workspace_manager.list_workspaces(include_archived)
    
    return {
        "workspaces": [w.to_dict() for w in workspaces],
        "total": len(workspaces)
    }


@router.post("/workspaces")
async def create_workspace(request: CreateWorkspaceRequest):
    """Yeni çalışma ortamı oluştur."""
    workspace = learning_workspace_manager.create_workspace(
        name=request.name,
        description=request.description,
        topic=request.topic,
        initial_sources=request.initial_sources
    )
    
    return {
        "success": True,
        "workspace": workspace.to_dict(),
        "message": f"'{request.name}' çalışma ortamı oluşturuldu"
    }


@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Çalışma ortamı detayları."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    # İstatistikler
    stats = learning_workspace_manager.get_workspace_stats(workspace_id)
    
    # Dökümanlar ve testler
    documents = learning_workspace_manager.list_documents(workspace_id)
    tests = learning_workspace_manager.list_tests(workspace_id)
    
    return {
        "workspace": workspace.to_dict(),
        "stats": stats,
        "documents": [d.to_dict() for d in documents],
        "tests": [t.to_dict() for t in tests]
    }


@router.put("/workspaces/{workspace_id}")
async def update_workspace(workspace_id: str, request: UpdateWorkspaceRequest):
    """Çalışma ortamını güncelle."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    if request.name:
        workspace.name = request.name
    if request.description is not None:
        workspace.description = request.description
    if request.topic is not None:
        workspace.topic = request.topic
    
    learning_workspace_manager.update_workspace(workspace)
    
    return {
        "success": True,
        "workspace": workspace.to_dict()
    }


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str, permanent: bool = False):
    """Çalışma ortamını sil."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    learning_workspace_manager.delete_workspace(workspace_id, permanent)
    
    return {
        "success": True,
        "message": "Çalışma ortamı silindi"
    }


@router.post("/workspaces/{workspace_id}/archive")
async def archive_workspace(workspace_id: str):
    """Çalışma ortamını arşivle."""
    learning_workspace_manager.archive_workspace(workspace_id)
    
    return {
        "success": True,
        "message": "Çalışma ortamı arşivlendi"
    }


@router.get("/workspaces/{workspace_id}/stats")
async def get_workspace_stats(workspace_id: str):
    """Çalışma ortamı istatistikleri."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    stats = learning_workspace_manager.get_workspace_stats(workspace_id)
    
    return {
        "success": True,
        "stats": stats
    }


# ==================== SOURCE MANAGEMENT ====================

@router.get("/workspaces/{workspace_id}/sources")
async def get_workspace_sources(workspace_id: str):
    """Çalışma ortamı kaynakları - RAG sistemindeki tüm dökümanları listeler."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    all_sources = []
    
    try:
        # 1. Vector store'dan unique kaynakları al
        unique_sources = vector_store.get_unique_sources()
        doc_stats = vector_store.get_document_stats()
        sources_info = doc_stats.get("sources", {})
        
        # 2. Upload klasöründeki dosyaları kontrol et
        upload_dir = settings.DATA_DIR / "uploads"
        uploaded_files = {}
        
        if upload_dir.exists():
            for file_path in upload_dir.iterdir():
                if file_path.is_file():
                    # Dosya adından ID ve orijinal adı çıkar
                    parts = file_path.name.split("_", 1)
                    if len(parts) > 1:
                        doc_id = parts[0]
                        original_name = parts[1]
                    else:
                        doc_id = file_path.stem
                        original_name = file_path.name
                    
                    uploaded_files[original_name] = {
                        "id": doc_id,
                        "path": file_path,
                        "size": file_path.stat().st_size,
                        "mtime": file_path.stat().st_mtime
                    }
        
        # 3. Kaynakları birleştir
        seen_sources = set()
        
        # Upload klasöründeki dosyalar
        for filename, file_info in uploaded_files.items():
            if filename in seen_sources:
                continue
            seen_sources.add(filename)
            
            # Vector store'da chunk sayısını bul
            chunk_count = sources_info.get(filename, 0)
            
            # Dosya uzantısını al
            suffix = file_info["path"].suffix[1:].upper() if file_info["path"].suffix else "FILE"
            
            # Aktiflik durumu
            is_active = (
                file_info["id"] in workspace.active_sources or
                filename in workspace.active_sources or
                file_info["path"].stem in workspace.active_sources
            )
            
            all_sources.append({
                "id": file_info["id"],
                "name": filename,
                "type": suffix,
                "size": file_info["size"],
                "chunk_count": chunk_count,
                "active": is_active,
                "in_vector_store": chunk_count > 0,
                "uploaded_at": datetime.fromtimestamp(file_info["mtime"]).isoformat()
            })
        
        # Vector store'daki ama upload klasöründe olmayan kaynaklar
        for source_name in unique_sources:
            if source_name in seen_sources:
                continue
            seen_sources.add(source_name)
            
            chunk_count = sources_info.get(source_name, 0)
            
            # Tam yol ise sadece dosya adını al
            from pathlib import Path
            if "\\" in source_name or "/" in source_name:
                display_name = Path(source_name).name
                # ID_filename formatındaysa, sadece filename'i al
                if "_" in display_name:
                    parts = display_name.split("_", 1)
                    if len(parts) > 1 and len(parts[0]) > 30:  # UUID formatı
                        display_name = parts[1]
            else:
                display_name = source_name
            
            # Dosya uzantısını tahmin et
            if "." in display_name:
                suffix = display_name.rsplit(".", 1)[-1].upper()
            else:
                suffix = "FILE"
            
            is_active = source_name in workspace.active_sources or display_name in workspace.active_sources
            
            all_sources.append({
                "id": source_name,
                "name": display_name,
                "type": suffix,
                "size": 0,
                "chunk_count": chunk_count,
                "active": is_active,
                "in_vector_store": True,
                "uploaded_at": None
            })
        
        # Sırala: önce aktifler, sonra isme göre
        all_sources.sort(key=lambda x: (not x["active"], x["name"].lower()))
        
    except Exception as e:
        print(f"Source listing error: {e}")
        import traceback
        traceback.print_exc()
    
    active_count = sum(1 for s in all_sources if s.get("active", False))
    
    return {
        "sources": all_sources,
        "active_count": active_count,
        "total": len(all_sources)
    }


@router.post("/workspaces/{workspace_id}/sources/toggle")
async def toggle_source(workspace_id: str, request: ToggleSourceRequest):
    """Kaynağı aktif/deaktif et."""
    success = learning_workspace_manager.toggle_source(
        workspace_id,
        request.source_id,
        request.active
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    return {
        "success": True,
        "source_id": request.source_id,
        "active": request.active
    }


@router.post("/workspaces/{workspace_id}/sources/bulk-toggle")
async def bulk_toggle_sources(workspace_id: str, request: BulkToggleSourceRequest):
    """Tüm kaynakları toplu olarak aktif/deaktif et."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    # Tüm kaynakları topla
    all_sources = list(workspace.active_sources) + list(workspace.inactive_sources)
    unique_sources = list(set(all_sources))
    
    toggled_count = 0
    for source_id in unique_sources:
        success = learning_workspace_manager.toggle_source(
            workspace_id,
            source_id,
            request.active
        )
        if success:
            toggled_count += 1
    
    return {
        "success": True,
        "active": request.active,
        "toggled_count": toggled_count
    }


# ==================== DOCUMENT ENDPOINTS ====================

@router.get("/documents/styles")
async def get_document_styles():
    """Kullanılabilir döküman stillerini getir."""
    return study_document_generator.get_available_styles()


@router.post("/workspaces/{workspace_id}/documents")
async def create_document(workspace_id: str, request: CreateDocumentRequest):
    """Çalışma dökümanı oluştur (meta veri)."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    document = learning_workspace_manager.create_document(
        workspace_id=workspace_id,
        title=request.title,
        topic=request.topic,
        page_count=request.page_count,
        style=request.style
    )
    
    return {
        "success": True,
        "document": document.to_dict(),
        "message": "Döküman oluşturuldu, içerik üretimi başlatılabilir"
    }


@router.post("/documents/{document_id}/generate")
async def generate_document(
    document_id: str,
    request: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = None
):
    """Döküman içeriği oluştur (background task + polling)."""
    import threading
    
    # Request body'den parametreleri al
    custom_instructions = ""
    web_search = "auto"  # off, auto, on
    
    if request:
        custom_instructions = request.get("custom_instructions", "")
        web_search = request.get("web_search", "auto")
    
    document = learning_workspace_manager.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    # Zaten üretiliyorsa engelle (enum veya string olarak kontrol)
    if document.status == DocumentStatus.GENERATING or document.status == "generating":
        return {
            "success": False,
            "message": "Bu döküman zaten üretiliyor"
        }
    
    workspace = learning_workspace_manager.get_workspace(document.workspace_id)
    active_sources = workspace.active_sources if workspace else []
    
    # Cancellation flag'i ayarla
    _active_generations[document_id] = True
    
    # Önce durumu "generating" yap
    document.status = DocumentStatus.GENERATING
    document.generation_log.append(f"[{datetime.now().isoformat()}] 🚀 Üretim isteği alındı")
    learning_workspace_manager.update_document(document)
    
    def cancel_check():
        return not _active_generations.get(document_id, True)
    
    def run_generation():
        """Thread içinde synchronous çalıştır."""
        try:
            print(f"[Generate Thread] Starting for document: {document_id}")
            
            result = study_document_generator.generate_document_sync(
                document_id=document_id,
                active_source_ids=active_sources,
                custom_instructions=custom_instructions,
                web_search=web_search,
                cancel_check=cancel_check
            )
            
            print(f"[Generate Thread] Completed: {result.get('success')}")
            
        except Exception as e:
            import traceback
            print(f"[Generate Thread] Exception: {e}")
            print(traceback.format_exc())
            
            # Hata durumunda dökümanı güncelle
            doc = learning_workspace_manager.get_document(document_id)
            if doc:
                doc.status = DocumentStatus.FAILED
                doc.generation_log.append(f"[{datetime.now().isoformat()}] ❌ Thread HATA: {str(e)}")
                learning_workspace_manager.update_document(doc)
        finally:
            _active_generations.pop(document_id, None)
    
    # Thread başlat
    thread = threading.Thread(target=run_generation, daemon=True, name=f"DocGen-{document_id[:8]}")
    thread.start()
    
    # Hemen yanıt dön
    return {
        "success": True,
        "message": "Döküman üretimi başlatıldı",
        "document_id": document_id,
        "status": "generating"
    }


# Aktif generation thread'lerini takip et
_active_generations: Dict[str, bool] = {}


@router.post("/documents/{document_id}/cancel")
async def cancel_document_generation(document_id: str):
    """Döküman üretimini iptal et."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    if document.status != DocumentStatus.GENERATING and document.status != "generating":
        return {
            "success": False,
            "message": f"Döküman zaten '{document.status}' durumunda"
        }
    
    # Cancellation flag'i ayarla
    _active_generations[document_id] = False
    
    # Döküman durumunu güncelle
    document.status = DocumentStatus.CANCELLED
    document.generation_log.append(f"[{datetime.now().isoformat()}] ❌ Kullanıcı tarafından iptal edildi")
    learning_workspace_manager.update_document(document)
    
    return {
        "success": True,
        "message": "Döküman üretimi iptal edildi"
    }


@router.post("/documents/{document_id}/restart")
async def restart_document_generation(document_id: str, request: Optional[Dict[str, Any]] = None):
    """Döküman üretimini yeniden başlat."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    if document.status == DocumentStatus.GENERATING or document.status == "generating":
        return {
            "success": False,
            "message": "Döküman zaten üretiliyor"
        }
    
    # Önceki içeriği temizle
    document.content = ""
    document.references = []
    document.generation_log = [f"[{datetime.now().isoformat()}] 🔄 Yeniden başlatıldı"]
    document.status = DocumentStatus.DRAFT
    learning_workspace_manager.update_document(document)
    
    # Yeniden üretimi başlat - generate_document fonksiyonunu çağır
    return await generate_document(document_id, request)


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Döküman detayları."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    return {
        "document": document.to_dict()
    }


@router.put("/documents/{document_id}")
async def update_document(document_id: str, request: UpdateDocumentRequest):
    """Döküman bilgilerini güncelle (başlık, konu, sayfa sayısı, stil)."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    # Üretim devam ediyorsa güncelleme yapma
    if document.status == DocumentStatus.GENERATING or document.status == "generating":
        raise HTTPException(
            status_code=400, 
            detail="Döküman üretimi devam ediyor. Önce iptal edin veya tamamlanmasını bekleyin."
        )
    
    # Değişen alanları güncelle
    changes = []
    if request.title is not None and request.title != document.title:
        document.title = request.title
        changes.append(f"başlık: {request.title}")
    
    if request.topic is not None and request.topic != document.topic:
        document.topic = request.topic
        changes.append(f"konu: {request.topic}")
    
    if request.page_count is not None and request.page_count != document.page_count:
        document.page_count = min(request.page_count, 40)
        changes.append(f"sayfa: {document.page_count}")
    
    if request.style is not None and request.style != document.style:
        document.style = request.style
        changes.append(f"stil: {request.style}")
    
    if changes:
        # Değişiklik logu ekle
        document.generation_log.append(
            f"[{datetime.now().isoformat()}] ✏️ Düzenlendi: {', '.join(changes)}"
        )
        learning_workspace_manager.update_document(document)
    
    return {
        "success": True,
        "message": f"Döküman güncellendi: {', '.join(changes)}" if changes else "Değişiklik yapılmadı",
        "document": document.to_dict(),
        "changes": changes
    }


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Dökümanı sil."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    # Üretim devam ediyorsa önce iptal et
    if document.status == DocumentStatus.GENERATING or document.status == "generating":
        _active_generations[document_id] = False
    
    # Workspace'den çıkar
    workspace = learning_workspace_manager.get_workspace(document.workspace_id)
    if workspace and document_id in workspace.documents:
        workspace.documents.remove(document_id)
        learning_workspace_manager.update_workspace(workspace)
    
    # Dosyayı sil
    doc_path = learning_workspace_manager.documents_dir / f"{document_id}.json"
    if doc_path.exists():
        doc_path.unlink()
    
    return {
        "success": True,
        "message": f"'{document.title}' dökümanı silindi"
    }


@router.post("/documents/{document_id}/edit-and-restart")
async def edit_and_restart_document(
    document_id: str, 
    request: UpdateDocumentRequest
):
    """Dökümanı düzenle ve yeniden üretimi başlat."""
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    # Üretim devam ediyorsa önce iptal et
    if document.status == DocumentStatus.GENERATING or document.status == "generating":
        _active_generations[document_id] = False
        await asyncio.sleep(0.5)  # İptal işleminin tamamlanması için bekle
    
    # Değişen alanları güncelle
    changes = []
    if request.title is not None:
        document.title = request.title
        changes.append(f"başlık: {request.title}")
    
    if request.topic is not None:
        document.topic = request.topic
        changes.append(f"konu: {request.topic}")
    
    if request.page_count is not None:
        document.page_count = min(request.page_count, 40)
        changes.append(f"sayfa: {document.page_count}")
    
    if request.style is not None:
        document.style = request.style
        changes.append(f"stil: {request.style}")
    
    # İçeriği temizle ve durumu sıfırla
    document.content = ""
    document.references = []
    document.generation_log = [
        f"[{datetime.now().isoformat()}] ✏️ Düzenleme: {', '.join(changes)}" if changes else f"[{datetime.now().isoformat()}] 🔄 Yeniden başlatıldı"
    ]
    document.status = DocumentStatus.DRAFT
    learning_workspace_manager.update_document(document)
    
    # Üretimi başlat
    return await generate_document(document_id, None)


@router.get("/workspaces/{workspace_id}/documents")
async def list_documents(workspace_id: str):
    """Çalışma ortamındaki dökümanları listele."""
    documents = learning_workspace_manager.list_documents(workspace_id)
    
    return {
        "documents": [d.to_dict() for d in documents],
        "total": len(documents)
    }


# ==================== TEST ENDPOINTS ====================

@router.get("/tests/types")
async def get_test_types():
    """Kullanılabilir test türlerini getir."""
    return test_generator.get_available_types()


@router.get("/tests/difficulties")
async def get_difficulty_levels():
    """Zorluk seviyelerini getir."""
    return test_generator.get_difficulty_levels()


@router.post("/workspaces/{workspace_id}/tests")
async def create_test(workspace_id: str, request: CreateTestRequest):
    """Test oluştur (meta veri)."""
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    try:
        test_type = TestType(request.test_type)
    except ValueError:
        test_type = TestType.MULTIPLE_CHOICE
    
    test = learning_workspace_manager.create_test(
        workspace_id=workspace_id,
        title=request.title,
        description=request.description,
        test_type=test_type,
        question_count=request.question_count,
        difficulty=request.difficulty
    )
    
    return {
        "success": True,
        "test": test.to_dict(),
        "message": "Test oluşturuldu, soru üretimi başlatılabilir"
    }


@router.post("/tests/{test_id}/generate")
async def generate_test(
    test_id: str,
    custom_instructions: str = ""
):
    """Test sorularını oluştur (streaming)."""
    
    test = learning_workspace_manager.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test bulunamadı")
    
    workspace = learning_workspace_manager.get_workspace(test.workspace_id)
    active_sources = workspace.active_sources if workspace else []
    
    async def generate():
        try:
            async for event in test_generator.generate_test(
                test_id=test_id,
                active_source_ids=active_sources,
                custom_instructions=custom_instructions
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/tests/{test_id}")
async def get_test(test_id: str):
    """Test detayları."""
    test = learning_workspace_manager.get_test(test_id)
    
    if not test:
        raise HTTPException(status_code=404, detail="Test bulunamadı")
    
    return {
        "test": test.to_dict()
    }


@router.get("/workspaces/{workspace_id}/tests")
async def list_tests(workspace_id: str):
    """Çalışma ortamındaki testleri listele."""
    tests = learning_workspace_manager.list_tests(workspace_id)
    
    return {
        "tests": [t.to_dict() for t in tests],
        "total": len(tests)
    }


@router.post("/tests/{test_id}/answer")
async def submit_answer(test_id: str, request: SubmitAnswerRequest):
    """Cevap gönder."""
    success = learning_workspace_manager.submit_test_answer(
        test_id,
        request.question_id,
        request.answer
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Test bulunamadı")
    
    # Cevabı değerlendir
    import asyncio
    result = asyncio.get_event_loop().run_until_complete(
        test_generator.grade_answer(test_id, request.question_id, request.answer)
    )
    
    return {
        "success": True,
        "grading": result
    }


@router.post("/tests/{test_id}/complete")
async def complete_test(test_id: str):
    """Testi tamamla ve sonuçları al."""
    result = learning_workspace_manager.complete_test(test_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Test bulunamadı")
    
    return {
        "success": True,
        "result": result
    }


@router.post("/tests/{test_id}/explain")
async def explain_question(test_id: str, request: ExplainQuestionRequest):
    """Soru hakkında açıklama al (anlamadığını sor)."""
    import asyncio
    
    explanation = asyncio.get_event_loop().run_until_complete(
        test_generator.explain_question(
            test_id,
            request.question_id,
            request.user_question
        )
    )
    
    return {
        "success": True,
        "explanation": explanation
    }


# ==================== CHAT ENDPOINTS ====================

@router.get("/workspaces/{workspace_id}/chat")
async def get_chat_history(workspace_id: str, limit: int = 50):
    """Chat geçmişini getir."""
    history = learning_workspace_manager.get_chat_history(workspace_id, limit)
    
    return {
        "messages": history,
        "total": len(history)
    }


@router.post("/workspaces/{workspace_id}/chat")
async def send_chat_message(workspace_id: str, request: ChatMessageRequest):
    """Chat mesajı gönder (workspace context'inde)."""
    from core.llm_manager import llm_manager
    
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    # Mesajı kaydet
    learning_workspace_manager.add_chat_message(
        workspace_id,
        "user",
        request.message
    )
    
    # Aktif kaynaklarla RAG araması
    context = ""
    sources_used = []
    
    if workspace.active_sources:
        try:
            results = vector_store.search_with_scores(
                query=request.message,
                n_results=5,
                score_threshold=0.3
            )
            
            for r in results:
                metadata = r.get("metadata", {})
                source_id = metadata.get("document_id", "")
                filename = metadata.get("original_filename", metadata.get("filename", ""))
                
                # Aktif kaynak kontrolü
                if source_id in workspace.active_sources or filename in workspace.active_sources:
                    context += f"\n[{filename}]:\n{r.get('document', '')[:500]}\n"
                    if filename not in sources_used:
                        sources_used.append(filename)
        except Exception as e:
            print(f"RAG search error: {e}")
    
    # LLM yanıtı
    system_prompt = f"""Sen bir öğrenme asistanısın. Kullanıcı "{workspace.name}" çalışma ortamında çalışıyor.
Konu: {workspace.topic}

{f'Kaynaklar:{context}' if context else 'Kaynaklarda bilgi bulunamadı, genel bilginle cevap ver.'}

Öğretici ve yardımcı ol. Türkçe yanıt ver."""

    response = llm_manager.generate(request.message, system_prompt)
    
    # Yanıtı kaydet
    learning_workspace_manager.add_chat_message(
        workspace_id,
        "assistant",
        response,
        sources_used
    )
    
    return {
        "success": True,
        "response": response,
        "sources": sources_used
    }


@router.post("/workspaces/{workspace_id}/chat/stream")
async def chat_stream(workspace_id: str, request: ChatMessageRequest):
    """Streaming chat."""
    from core.llm_manager import llm_manager
    
    workspace = learning_workspace_manager.get_workspace(workspace_id)
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Çalışma ortamı bulunamadı")
    
    # Mesajı kaydet
    learning_workspace_manager.add_chat_message(
        workspace_id,
        "user",
        request.message
    )
    
    # Aktif kaynaklarla RAG araması
    context = ""
    sources_used = []
    
    if workspace.active_sources:
        try:
            results = vector_store.search_with_scores(
                query=request.message,
                n_results=5,
                score_threshold=0.3
            )
            
            for r in results:
                metadata = r.get("metadata", {})
                source_id = metadata.get("document_id", "")
                filename = metadata.get("original_filename", metadata.get("filename", ""))
                
                if source_id in workspace.active_sources or filename in workspace.active_sources:
                    context += f"\n[{filename}]:\n{r.get('document', '')[:500]}\n"
                    if filename not in sources_used:
                        sources_used.append(filename)
        except:
            pass
    
    system_prompt = f"""Sen bir öğrenme asistanısın. Kullanıcı "{workspace.name}" çalışma ortamında çalışıyor.
Konu: {workspace.topic}

{f'Kaynaklar:{context}' if context else 'Kaynaklarda bilgi bulunamadı, genel bilginle cevap ver.'}

Öğretici ve yardımcı ol. Türkçe yanıt ver."""

    async def generate():
        full_response = ""
        try:
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources_used})}\n\n"
            
            for token in llm_manager.generate_stream(request.message, system_prompt):
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            
            # Yanıtı kaydet
            learning_workspace_manager.add_chat_message(
                workspace_id,
                "assistant",
                full_response,
                sources_used
            )
            
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ==================== STATS ====================

@router.get("/stats")
async def get_learning_stats():
    """Genel öğrenme istatistikleri."""
    workspaces = learning_workspace_manager.list_workspaces(include_archived=True)
    
    total_documents = 0
    total_tests = 0
    completed_tests = 0
    total_score = 0
    
    for ws in workspaces:
        docs = learning_workspace_manager.list_documents(ws.id)
        tests = learning_workspace_manager.list_tests(ws.id)
        
        total_documents += len(docs)
        total_tests += len(tests)
        
        for test in tests:
            if test.status == TestStatus.COMPLETED:
                completed_tests += 1
                total_score += test.score or 0
    
    avg_score = total_score / completed_tests if completed_tests > 0 else 0
    
    return {
        "workspaces_count": len(workspaces),
        "documents_count": total_documents,
        "tests_count": total_tests,
        "completed_tests": completed_tests,
        "average_score": round(avg_score, 1)
    }


# ==================== ADVANCED FEATURES ====================
# 14. Visual Learning Tools
# 15. Multimedia Content Generation
# 16. Smart Content Linking

from core.learning_advanced_features import get_learning_advanced_features


class VisualContentRequest(BaseModel):
    """Görsel içerik oluşturma isteği."""
    topic: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=100000)


class MultimediaRequest(BaseModel):
    """Multimedya içerik isteği."""
    topic: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=100000)
    duration_minutes: int = Field(default=10, ge=1, le=60)
    style: str = Field(default="educational")


class SlideRequest(BaseModel):
    """Slide deck isteği."""
    topic: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=100000)
    slide_count: int = Field(default=10, ge=3, le=30)
    include_notes: bool = Field(default=True)


class PodcastRequest(BaseModel):
    """Podcast script isteği."""
    topic: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=100000)
    duration_minutes: int = Field(default=15, ge=5, le=60)
    host_count: int = Field(default=1, ge=1, le=2)
    style: str = Field(default="conversational")


class LearningPathRequest(BaseModel):
    """Öğrenme yolu isteği."""
    target_topic: str = Field(..., min_length=1, max_length=200)
    current_knowledge: List[str] = Field(default=[])
    max_steps: int = Field(default=10, ge=1, le=20)


class NextTopicsRequest(BaseModel):
    """Sonraki konu önerisi isteği."""
    completed_topics: List[str] = Field(..., min_length=1)
    interests: List[str] = Field(default=[])


# ==================== VISUAL LEARNING TOOLS ====================

@router.post("/visual/mindmap")
async def create_mind_map(request: VisualContentRequest):
    """
    🎨 Mind-map oluştur.
    
    İçerikten otomatik mind-map çıkarır.
    Mermaid ve HTML formatında export.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_mind_map(request.topic, request.content)
        
        return {
            "success": True,
            "type": "mindmap",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/conceptmap")
async def create_concept_map(request: VisualContentRequest):
    """
    🎨 Kavram haritası oluştur.
    
    Kavramlar arası ilişkileri gösterir.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_concept_map(request.topic, request.content)
        
        return {
            "success": True,
            "type": "conceptmap",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/timeline")
async def create_timeline(request: VisualContentRequest):
    """
    🎨 Zaman çizelgesi oluştur.
    
    Sıralı adımlar ve olaylar için.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_timeline(request.topic, request.content)
        
        return {
            "success": True,
            "type": "timeline",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/flowchart")
async def create_flowchart(request: VisualContentRequest):
    """
    🎨 Akış şeması oluştur.
    
    Süreç, algoritma ve karar ağaçları için.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_flowchart(request.topic, request.content)
        
        return {
            "success": True,
            "type": "flowchart",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visual/infographic")
async def create_infographic(request: VisualContentRequest):
    """
    🎨 İnfografik yapısı oluştur.
    
    Bölümler, istatistikler, önemli noktalar.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_infographic(request.topic, request.content)
        
        return {
            "success": True,
            "type": "infographic",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MULTIMEDIA CONTENT ====================

@router.post("/multimedia/video-script")
async def create_video_script(request: MultimediaRequest):
    """
    📹 Video script oluştur.
    
    Segment'ler, görsel cue'lar ve tam script.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_video_script(
            request.topic, 
            request.content,
            duration_minutes=request.duration_minutes,
            style=request.style
        )
        
        return {
            "success": True,
            "type": "video_script",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimedia/slides")
async def create_slide_deck(request: SlideRequest):
    """
    📹 Slide deck oluştur.
    
    PowerPoint/Google Slides için yapı.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_slide_deck(
            request.topic,
            request.content,
            slide_count=request.slide_count,
            include_notes=request.include_notes
        )
        
        return {
            "success": True,
            "type": "slide_deck",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimedia/podcast")
async def create_podcast_script(request: PodcastRequest):
    """
    📹 Podcast script oluştur.
    
    Monolog veya dialog formatında.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_podcast_script(
            request.topic,
            request.content,
            duration_minutes=request.duration_minutes,
            host_count=request.host_count,
            style=request.style
        )
        
        return {
            "success": True,
            "type": "podcast_script",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimedia/audio-summary")
async def create_audio_summary(request: VisualContentRequest):
    """
    📹 Audio özet scripti oluştur.
    
    1 dakikalık TL;DR.
    """
    try:
        features = get_learning_advanced_features()
        result = features.create_audio_summary(request.topic, request.content)
        
        return {
            "success": True,
            "type": "audio_summary",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SMART CONTENT LINKING ====================

@router.post("/linking/prerequisites")
async def get_prerequisites(request: VisualContentRequest):
    """
    🔗 Ön koşulları tespit et.
    
    "Bu konuyu anlamak için önce ne öğrenmeli?"
    """
    try:
        features = get_learning_advanced_features()
        result = features.get_prerequisites(request.topic, request.content)
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/linking/related")
async def get_related_content(request: VisualContentRequest):
    """
    🔗 İlişkili içerikleri bul.
    
    Benzer konular, devam konuları, örnekler.
    """
    try:
        features = get_learning_advanced_features()
        result = features.get_related_content(request.topic, request.content)
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/linking/learning-path")
async def get_learning_path(request: LearningPathRequest):
    """
    🔗 Öğrenme yolu oluştur.
    
    Hedefe ulaşmak için adım adım yol haritası.
    """
    try:
        features = get_learning_advanced_features()
        result = features.get_learning_path(
            request.target_topic,
            current_knowledge=request.current_knowledge,
            max_steps=request.max_steps
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/linking/next-topics")
async def get_next_topics(request: NextTopicsRequest):
    """
    🔗 Sonraki konuları öner.
    
    Tamamlanan konulara göre ne öğrenilmeli?
    """
    try:
        features = get_learning_advanced_features()
        result = features.get_next_topics(
            request.completed_topics,
            interests=request.interests
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DOCUMENT VISUAL GENERATION ====================

@router.post("/documents/{document_id}/visualize")
async def generate_document_visuals(
    document_id: str,
    visual_types: List[str] = ["mindmap", "timeline"]
):
    """
    Döküman için görsel içerikler oluştur.
    
    Mind-map, timeline, flowchart vb.
    """
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    if not document.content:
        raise HTTPException(status_code=400, detail="Döküman içeriği boş")
    
    features = get_learning_advanced_features()
    results = {}
    
    try:
        if "mindmap" in visual_types:
            results["mindmap"] = features.create_mind_map(document.title, document.content)
        
        if "conceptmap" in visual_types:
            results["conceptmap"] = features.create_concept_map(document.title, document.content)
        
        if "timeline" in visual_types:
            results["timeline"] = features.create_timeline(document.title, document.content)
        
        if "flowchart" in visual_types:
            results["flowchart"] = features.create_flowchart(document.title, document.content)
        
        if "infographic" in visual_types:
            results["infographic"] = features.create_infographic(document.title, document.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "success": True,
        "document_id": document_id,
        "document_title": document.title,
        "visuals": results
    }


@router.post("/documents/{document_id}/multimedia")
async def generate_document_multimedia(
    document_id: str,
    content_type: str = "slides"  # slides, video, podcast, audio
):
    """
    Döküman için multimedya içerik oluştur.
    """
    document = learning_workspace_manager.get_document(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Döküman bulunamadı")
    
    if not document.content:
        raise HTTPException(status_code=400, detail="Döküman içeriği boş")
    
    features = get_learning_advanced_features()
    
    try:
        if content_type == "slides":
            result = features.create_slide_deck(document.title, document.content)
        elif content_type == "video":
            result = features.create_video_script(document.title, document.content)
        elif content_type == "podcast":
            result = features.create_podcast_script(document.title, document.content)
        elif content_type == "audio":
            result = features.create_audio_summary(document.title, document.content)
        else:
            raise HTTPException(status_code=400, detail="Geçersiz içerik tipi")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "success": True,
        "document_id": document_id,
        "document_title": document.title,
        "content_type": content_type,
        **result
    }


# ==================== PREMIUM: LEARNING ANALYTICS ====================

from core.learning_premium_features import get_premium_features, ScenarioType, ScenarioDifficulty, ReviewRating, TutorMode


class LogEventRequest(BaseModel):
    """Öğrenme olayı kaydı."""
    event_type: str
    duration_minutes: int = 0
    score: Optional[float] = None
    topic: str = ""
    metadata: Dict[str, Any] = {}


@router.get("/analytics/status")
async def get_premium_status():
    """Premium özelliklerin durumunu getir."""
    try:
        features = get_premium_features()
        return {
            "success": True,
            "features": features.get_feature_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/analytics/log")
async def log_learning_event(workspace_id: str, request: LogEventRequest):
    """Öğrenme olayı kaydet."""
    try:
        features = get_premium_features()
        event = features.analytics.log_event(
            workspace_id=workspace_id,
            event_type=request.event_type,
            duration_minutes=request.duration_minutes,
            score=request.score,
            topic=request.topic,
            metadata=request.metadata
        )
        return {"success": True, "event": event.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/analytics/stats")
async def get_workspace_analytics(workspace_id: str):
    """Çalışma alanı istatistiklerini getir."""
    try:
        features = get_premium_features()
        stats = features.analytics.get_workspace_stats(workspace_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/analytics/weekly")
async def get_weekly_activity(workspace_id: str):
    """Haftalık aktivite verilerini getir."""
    try:
        features = get_premium_features()
        weekly = features.analytics.get_weekly_activity(workspace_id)
        return {"success": True, "weekly_activity": weekly}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/analytics/insights")
async def get_learning_insights(workspace_id: str):
    """AI destekli öğrenme içgörüleri."""
    try:
        features = get_premium_features()
        insights = features.analytics.generate_insights(workspace_id)
        return {"success": True, "insights": [i.to_dict() for i in insights]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/analytics/report")
async def get_learning_report(workspace_id: str):
    """Kapsamlı öğrenme raporu."""
    try:
        features = get_premium_features()
        report = features.analytics.get_learning_report(workspace_id)
        return {"success": True, **report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/analytics/weak-areas")
async def get_weak_areas(workspace_id: str, limit: int = 5):
    """Zayıf alanları tespit et."""
    try:
        features = get_premium_features()
        weak = features.analytics.get_weak_areas(workspace_id, limit)
        return {"success": True, "weak_areas": weak}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PREMIUM: AI SIMULATIONS ====================

class CreateScenarioRequest(BaseModel):
    """Senaryo oluşturma isteği."""
    scenario_type: str
    topic: str
    difficulty: str = "medium"
    custom_context: str = ""


class ScenarioInteractRequest(BaseModel):
    """Senaryo etkileşim isteği."""
    message: str


@router.get("/simulations/types")
async def get_scenario_types():
    """Mevcut senaryo türlerini getir."""
    try:
        features = get_premium_features()
        types = features.simulations.get_scenario_types()
        return {"success": True, "scenario_types": types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/simulations")
async def create_simulation(workspace_id: str, request: CreateScenarioRequest):
    """Yeni simülasyon senaryosu oluştur."""
    try:
        features = get_premium_features()
        
        # Enum'a çevir
        scenario_type = ScenarioType(request.scenario_type)
        difficulty = ScenarioDifficulty(request.difficulty)
        
        scenario = features.simulations.create_scenario(
            workspace_id=workspace_id,
            scenario_type=scenario_type,
            topic=request.topic,
            difficulty=difficulty,
            custom_context=request.custom_context
        )
        
        return {
            "success": True,
            "scenario": scenario.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/simulations")
async def list_simulations(workspace_id: str, status: Optional[str] = None):
    """Simülasyonları listele."""
    try:
        features = get_premium_features()
        scenarios = features.simulations.list_scenarios(workspace_id, status)
        return {
            "success": True,
            "scenarios": [s.to_dict() for s in scenarios]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulations/{scenario_id}")
async def get_simulation(scenario_id: str):
    """Simülasyon detaylarını getir."""
    try:
        features = get_premium_features()
        scenario = features.simulations.get_scenario(scenario_id)
        
        if not scenario:
            raise HTTPException(status_code=404, detail="Senaryo bulunamadı")
        
        return {"success": True, "scenario": scenario.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulations/{scenario_id}/interact")
async def interact_with_simulation(scenario_id: str, request: ScenarioInteractRequest):
    """Simülasyonla etkileşim."""
    try:
        features = get_premium_features()
        result = features.simulations.interact(scenario_id, request.message)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulations/{scenario_id}/abandon")
async def abandon_simulation(scenario_id: str):
    """Simülasyonu terk et."""
    try:
        features = get_premium_features()
        success = features.simulations.abandon_scenario(scenario_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Senaryo bulunamadı")
        
        return {"success": True, "message": "Senaryo terk edildi"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PREMIUM: AI TUTOR ====================

class StartTutorSessionRequest(BaseModel):
    """Tutor oturumu başlatma isteği."""
    topic: str
    mode: str = "adaptive"
    student_id: Optional[str] = None


class TutorMessageRequest(BaseModel):
    """Tutor mesaj isteği."""
    message: str
    context: Optional[str] = None


@router.post("/workspaces/{workspace_id}/tutor/session")
async def start_tutor_session(workspace_id: str, request: StartTutorSessionRequest):
    """Yeni AI Tutor oturumu başlat."""
    try:
        features = get_premium_features()
        
        mode = TutorMode(request.mode)
        session = features.ai_tutor.start_session(
            workspace_id=workspace_id,
            topic=request.topic,
            mode=mode,
            student_id=request.student_id
        )
        
        return {"success": True, "session": session.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor/{session_id}/message")
async def send_tutor_message(session_id: str, request: TutorMessageRequest):
    """Tutor'a mesaj gönder."""
    try:
        features = get_premium_features()
        result = features.ai_tutor.process_message(
            session_id=session_id,
            user_message=request.message,
            context=request.context
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"success": True, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tutor/{session_id}")
async def get_tutor_session(session_id: str):
    """Tutor oturumunu getir."""
    try:
        features = get_premium_features()
        session = features.ai_tutor.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        return {"success": True, "session": session.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tutor/{session_id}/end")
async def end_tutor_session(session_id: str):
    """Tutor oturumunu sonlandır."""
    try:
        features = get_premium_features()
        result = features.ai_tutor.end_session(session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Oturum bulunamadı")
        
        return {"success": True, "session": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PREMIUM: SPACED REPETITION ====================

class CreateFlashcardRequest(BaseModel):
    """Flashcard oluşturma isteği."""
    front: str
    back: str
    deck: str = "default"
    tags: List[str] = []


class CreateCardsFromContentRequest(BaseModel):
    """İçerikten kart oluşturma isteği."""
    content: str
    deck: str = "default"
    card_type: str = "qa"  # qa, cloze, reverse


class ReviewCardRequest(BaseModel):
    """Kart değerlendirme isteği."""
    rating: int  # 0-3


@router.post("/workspaces/{workspace_id}/flashcards")
async def create_flashcard(workspace_id: str, request: CreateFlashcardRequest):
    """Yeni flashcard oluştur."""
    try:
        features = get_premium_features()
        card = features.srs.create_card(
            workspace_id=workspace_id,
            front=request.front,
            back=request.back,
            deck=request.deck,
            tags=request.tags
        )
        return {"success": True, "card": card.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/flashcards/generate")
async def generate_flashcards(workspace_id: str, request: CreateCardsFromContentRequest):
    """İçerikten otomatik flashcard oluştur."""
    try:
        features = get_premium_features()
        cards = features.srs.create_cards_from_content(
            workspace_id=workspace_id,
            content=request.content,
            deck=request.deck,
            card_type=request.card_type
        )
        return {
            "success": True,
            "cards": [c.to_dict() for c in cards],
            "count": len(cards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/flashcards")
async def get_flashcards(workspace_id: str, deck: Optional[str] = None):
    """Flashcard'ları getir."""
    try:
        features = get_premium_features()
        cards = features.srs.get_cards_by_workspace(workspace_id, deck)
        return {
            "success": True,
            "cards": [c.to_dict() for c in cards],
            "count": len(cards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/flashcards/due")
async def get_due_flashcards(workspace_id: str, deck: Optional[str] = None, limit: int = 20):
    """Tekrar edilmesi gereken kartları getir."""
    try:
        features = get_premium_features()
        cards = features.srs.get_due_cards(workspace_id, deck, limit)
        return {
            "success": True,
            "cards": [c.to_dict() for c in cards],
            "count": len(cards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/flashcards/stats")
async def get_flashcard_stats(workspace_id: str, deck: Optional[str] = None):
    """Flashcard istatistiklerini getir."""
    try:
        features = get_premium_features()
        stats = features.srs.get_deck_stats(workspace_id, deck)
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flashcards/{card_id}/review")
async def review_flashcard(card_id: str, request: ReviewCardRequest):
    """Flashcard'ı değerlendir."""
    try:
        features = get_premium_features()
        
        # Rating enum'a çevir
        rating = ReviewRating(request.rating)
        result = features.srs.review_card(card_id, rating)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Geçersiz rating: 0-3 arası olmalı")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flashcards/{card_id}")
async def delete_flashcard(card_id: str):
    """Flashcard sil."""
    try:
        features = get_premium_features()
        success = features.srs.delete_card(card_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Kart bulunamadı")
        
        return {"success": True, "message": "Kart silindi"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PREMIUM: KNOWLEDGE GRAPH ====================

class CreateKnowledgeNodeRequest(BaseModel):
    """Bilgi düğümü oluşturma isteği."""
    label: str
    node_type: str = "concept"
    description: str = ""
    tags: List[str] = []


class CreateKnowledgeEdgeRequest(BaseModel):
    """Bilgi bağlantısı oluşturma isteği."""
    source_id: str
    target_id: str
    edge_type: str = "related"
    label: str = ""
    bidirectional: bool = False


class BuildGraphRequest(BaseModel):
    """İçerikten graph oluşturma isteği."""
    content: str
    source_doc_id: Optional[str] = None


@router.post("/workspaces/{workspace_id}/knowledge-graph/nodes")
async def create_knowledge_node(workspace_id: str, request: CreateKnowledgeNodeRequest):
    """Bilgi düğümü oluştur."""
    try:
        from core.learning_premium_features import NodeType
        features = get_premium_features()
        
        node_type = NodeType(request.node_type)
        node = features.knowledge_graph.create_node(
            workspace_id=workspace_id,
            label=request.label,
            node_type=node_type,
            description=request.description,
            tags=request.tags
        )
        return {"success": True, "node": node.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/knowledge-graph/edges")
async def create_knowledge_edge(workspace_id: str, request: CreateKnowledgeEdgeRequest):
    """Bilgi bağlantısı oluştur."""
    try:
        from core.learning_premium_features import EdgeType
        features = get_premium_features()
        
        edge_type = EdgeType(request.edge_type)
        edge = features.knowledge_graph.create_edge(
            source_id=request.source_id,
            target_id=request.target_id,
            edge_type=edge_type,
            label=request.label,
            bidirectional=request.bidirectional
        )
        
        if not edge:
            raise HTTPException(status_code=400, detail="Düğümler bulunamadı")
        
        return {"success": True, "edge": edge.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/knowledge-graph/build")
async def build_knowledge_graph(workspace_id: str, request: BuildGraphRequest):
    """İçerikten otomatik bilgi grafiği oluştur."""
    try:
        features = get_premium_features()
        result = features.knowledge_graph.build_from_content(
            workspace_id=workspace_id,
            content=request.content,
            source_doc_id=request.source_doc_id
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/knowledge-graph")
async def get_knowledge_graph(workspace_id: str):
    """Bilgi grafiğini getir."""
    try:
        features = get_premium_features()
        nodes = features.knowledge_graph.get_nodes_by_workspace(workspace_id)
        edges = features.knowledge_graph.get_edges_by_workspace(workspace_id)
        stats = features.knowledge_graph.get_graph_stats(workspace_id)
        
        return {
            "success": True,
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/knowledge-graph/clusters")
async def get_knowledge_clusters(workspace_id: str):
    """Bilgi kümelerini getir."""
    try:
        features = get_premium_features()
        clusters = features.knowledge_graph.get_clusters(workspace_id)
        return {"success": True, "clusters": clusters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/knowledge-graph/export/{format}")
async def export_knowledge_graph(workspace_id: str, format: str):
    """Bilgi grafiğini export et."""
    try:
        features = get_premium_features()
        
        if format == "mermaid":
            result = features.knowledge_graph.export_mermaid(workspace_id)
            return {"success": True, "format": "mermaid", "content": result}
        elif format == "cytoscape":
            result = features.knowledge_graph.export_cytoscape(workspace_id)
            return {"success": True, "format": "cytoscape", "elements": result}
        else:
            raise HTTPException(status_code=400, detail="Desteklenmeyen format. mermaid veya cytoscape kullanın.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/nodes/{node_id}/suggestions")
async def get_node_suggestions(node_id: str, limit: int = 5):
    """Düğüm için bağlantı önerileri."""
    try:
        features = get_premium_features()
        node = features.knowledge_graph.get_node(node_id)
        
        if not node:
            raise HTTPException(status_code=404, detail="Düğüm bulunamadı")
        
        suggestions = features.knowledge_graph.suggest_connections(
            node.workspace_id, node_id, limit
        )
        return {"success": True, "suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PREMIUM: CODE PLAYGROUND ====================

class CreateSnippetRequest(BaseModel):
    """Kod parçası oluşturma isteği."""
    title: str
    language: str = "python"
    code: str
    explanation: str = ""
    tags: List[str] = []


class RunCodeRequest(BaseModel):
    """Kod çalıştırma isteği."""
    code: str
    language: str = "python"


@router.post("/workspaces/{workspace_id}/code/snippets")
async def create_code_snippet(workspace_id: str, request: CreateSnippetRequest):
    """Kod parçası oluştur."""
    try:
        from core.learning_premium_features import CodeLanguage
        features = get_premium_features()
        
        language = CodeLanguage(request.language)
        snippet = features.code_playground.create_snippet(
            workspace_id=workspace_id,
            title=request.title,
            language=language,
            code=request.code,
            explanation=request.explanation,
            tags=request.tags
        )
        return {"success": True, "snippet": snippet.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/code/snippets")
async def get_code_snippets(workspace_id: str):
    """Kod parçalarını getir."""
    try:
        features = get_premium_features()
        snippets = features.code_playground.get_snippets_by_workspace(workspace_id)
        return {
            "success": True,
            "snippets": [s.to_dict() for s in snippets]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/snippets/{snippet_id}/run")
async def run_code_snippet(snippet_id: str):
    """Kod parçasını çalıştır."""
    try:
        features = get_premium_features()
        result = features.code_playground.run_snippet(snippet_id)
        
        if "error" in result and "Snippet bulunamadı" in str(result.get("error", "")):
            raise HTTPException(status_code=404, detail="Snippet bulunamadı")
        
        return {"success": result.get("success", False), **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/run")
async def run_code(request: RunCodeRequest):
    """Anlık kod çalıştır."""
    try:
        features = get_premium_features()
        
        if request.language != "python":
            raise HTTPException(status_code=400, detail="Şu an sadece Python destekleniyor")
        
        result = features.code_playground.run_python_code(request.code)
        return {"success": result.get("success", False), **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/analyze")
async def analyze_code(request: RunCodeRequest):
    """Kod analizi yap."""
    try:
        from core.learning_premium_features import CodeLanguage
        features = get_premium_features()
        
        language = CodeLanguage(request.language)
        analysis = features.code_playground.analyze_code(request.code, language)
        return {"success": True, "analysis": analysis}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
