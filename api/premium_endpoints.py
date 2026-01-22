"""
Premium Integration API Endpoints
=================================

Kullanılmayan modülleri API'ye açan endpoint'ler.
Bu router main.py'ye eklenir.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.logger import get_logger
from core.premium_integrations import premium_manager

logger = get_logger("premium_endpoints")

router = APIRouter(prefix="/api/premium", tags=["Premium Features"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TaskSubmitRequest(BaseModel):
    """Task gönderme isteği."""
    task_name: str = Field(..., description="Task adı: deep_scholar_generate, batch_rag_index, analytics_report, rag_quality_check")
    args: List[Any] = Field(default=[], description="Pozisyonel argümanlar")
    kwargs: Dict[str, Any] = Field(default={}, description="Keyword argümanlar")
    priority: str = Field(default="normal", pattern="^(low|normal|high|critical)$")


class TaskStatusResponse(BaseModel):
    """Task durumu yanıtı."""
    task_id: str
    name: str
    status: str
    progress: float
    created_at: str
    result: Optional[Dict] = None


class QueryExpansionRequest(BaseModel):
    """Sorgu genişletme isteği."""
    query: str = Field(..., min_length=1)
    strategies: Optional[List[str]] = Field(default=None, description="synonym, keyword, multi_query, hyde")
    context: Optional[Dict[str, Any]] = None


class GuardrailCheckRequest(BaseModel):
    """Guardrail kontrol isteği."""
    text: str = Field(..., min_length=1)
    level: str = Field(default="medium", pattern="^(low|medium|high|strict)$")
    check_type: str = Field(default="input", pattern="^(input|output)$")
    context: Optional[str] = None


class RAGEvaluationRequest(BaseModel):
    """RAG değerlendirme isteği."""
    query: str
    contexts: List[str]
    answer: str
    ground_truth: Optional[str] = None


class WorkflowRunRequest(BaseModel):
    """Workflow çalıştırma isteği."""
    workflow_type: str = Field(..., pattern="^(rag|agent|custom)$")
    query: str
    custom_workflow_name: Optional[str] = None
    additional_params: Dict[str, Any] = Field(default={})


# ============================================================================
# TASK QUEUE ENDPOINTS
# ============================================================================

@router.post("/tasks/submit", response_model=Dict[str, Any])
async def submit_task(request: TaskSubmitRequest):
    """
    Background task gönder.
    
    Mevcut task'lar:
    - deep_scholar_generate: DeepScholar döküman oluştur
    - batch_rag_index: Toplu RAG indexleme
    - analytics_report: Analytics raporu oluştur
    - rag_quality_check: RAG kalite kontrolü
    """
    try:
        task_id = await premium_manager.tasks.submit_task(
            request.task_name,
            *request.args,
            priority=request.priority,
            **request.kwargs
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "task_name": request.task_name,
            "priority": request.priority,
            "message": "Task kuyruğa eklendi",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Task submit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Task durumunu al."""
    try:
        status = await premium_manager.tasks.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Task bulunamadı")
        
        return {
            "success": True,
            **status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Task status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/wait")
async def wait_for_task(
    task_id: str,
    timeout: float = Query(default=60.0, description="Timeout in seconds")
):
    """Task'ın tamamlanmasını bekle."""
    try:
        result = await premium_manager.tasks.wait_for_task(task_id, timeout=timeout)
        
        if not result:
            return {
                "success": False,
                "message": "Task tamamlanmadı veya bulunamadı",
                "timeout": True
            }
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Task wait error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/stats")
async def get_task_queue_stats():
    """Task kuyruğu istatistikleri."""
    try:
        stats = premium_manager.tasks.get_queue_stats()
        return {
            "success": True,
            **stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Task stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUERY EXPANSION ENDPOINTS
# ============================================================================

@router.post("/query/expand")
async def expand_query(request: QueryExpansionRequest):
    """
    Sorguyu genişlet.
    
    Stratejiler:
    - synonym: Eş anlamlı kelimelerle genişlet
    - keyword: Anahtar kelime çıkar
    - multi_query: LLM ile farklı versiyonlar oluştur
    - hyde: Hipotetik döküman oluştur
    """
    try:
        result = await premium_manager.query_expander.expand_query(
            query=request.query,
            strategies=request.strategies,
            context=request.context
        )
        
        return {
            "success": True,
            **result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Query expansion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GUARDRAILS ENDPOINTS
# ============================================================================

@router.post("/guardrails/check")
async def check_guardrails(request: GuardrailCheckRequest):
    """
    Input veya output güvenlik kontrolü.
    
    Seviyeler:
    - low: Minimal kontrol
    - medium: Standart kontrol
    - high: Sıkı kontrol
    - strict: En katı kontrol + filtreleme
    """
    try:
        if request.check_type == "input":
            result = premium_manager.guardrails.check_input(
                text=request.text,
                level=request.level
            )
        else:
            result = premium_manager.guardrails.check_output(
                output=request.text,
                context=request.context,
                level=request.level
            )
        
        return {
            "success": True,
            "check_type": request.check_type,
            "level": request.level,
            **result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Guardrails check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RAG EVALUATION ENDPOINTS
# ============================================================================

@router.post("/rag/evaluate")
async def evaluate_rag(request: RAGEvaluationRequest):
    """
    RAG kalitesi değerlendir.
    
    Metrikler:
    - context_relevance: Context'lerin sorguyla ilgisi
    - faithfulness: Cevabın kaynaklara sadakati
    - answer_relevance: Cevabın soruyla ilgisi
    - lexical_overlap: Kelime örtüşmesi
    - answer_correctness: Doğruluk (ground truth varsa)
    """
    try:
        result = premium_manager.evaluator.evaluate_full(
            query=request.query,
            contexts=request.contexts,
            answer=request.answer,
            ground_truth=request.ground_truth
        )
        
        return {
            "success": True,
            **result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"RAG evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/evaluate/batch/add")
async def add_evaluation_sample(request: RAGEvaluationRequest):
    """Batch evaluation'a örnek ekle."""
    try:
        premium_manager.evaluator.add_evaluation_sample(
            query=request.query,
            contexts=request.contexts,
            answer=request.answer,
            ground_truth=request.ground_truth
        )
        
        return {
            "success": True,
            "message": "Örnek eklendi",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/evaluate/batch/summary")
async def get_batch_evaluation_summary():
    """Batch evaluation özeti."""
    try:
        summary = premium_manager.evaluator.get_batch_summary()
        
        return {
            "success": True,
            **summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Batch summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/workflow/run")
async def run_workflow(request: WorkflowRunRequest):
    """
    Workflow çalıştır.
    
    Tipler:
    - rag: RAG workflow (retrieve -> generate)
    - agent: Agent routing workflow (classify -> route -> execute)
    - custom: Özel workflow (isim belirt)
    """
    try:
        if request.workflow_type == "rag":
            result = await premium_manager.workflows.run_rag_workflow(
                query=request.query,
                **request.additional_params
            )
        elif request.workflow_type == "agent":
            result = await premium_manager.workflows.run_agent_workflow(
                query=request.query,
                **request.additional_params
            )
        elif request.workflow_type == "custom":
            if not request.custom_workflow_name:
                raise HTTPException(status_code=400, detail="custom_workflow_name gerekli")
            result = await premium_manager.workflows.run_custom_workflow(
                name=request.custom_workflow_name,
                initial_state={"query": request.query, **request.additional_params}
            )
        else:
            raise HTTPException(status_code=400, detail="Geçersiz workflow tipi")
        
        return {
            "success": True,
            "workflow_type": request.workflow_type,
            **result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow run error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@router.get("/status")
async def get_premium_status():
    """Tüm premium modüllerin durumu."""
    try:
        status = premium_manager.get_status()
        
        return {
            "success": True,
            "modules": status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/initialize")
async def initialize_all_modules(background_tasks: BackgroundTasks):
    """Tüm premium modülleri önceden yükle."""
    try:
        background_tasks.add_task(premium_manager.initialize_all)
        
        return {
            "success": True,
            "message": "Modüller arka planda yükleniyor",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Initialize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
