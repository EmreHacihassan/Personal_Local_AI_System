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
