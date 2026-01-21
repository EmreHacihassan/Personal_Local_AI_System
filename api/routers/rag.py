"""
RAG Router
===========

Enterprise RAG sistemi endpoint'leri.
Semantic, Hybrid, Fusion arama stratejileri ve RAGAS evaluation.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import json

from core.vector_store import vector_store
from core.analytics import analytics


router = APIRouter(prefix="/api/rag", tags=["RAG"])
logger = logging.getLogger(__name__)


# ============ PYDANTIC MODELS ============

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
    page_numbers: List[int] = Field(..., min_length=1, max_length=50)
    source: Optional[str] = None


class RAGEvaluationRequest(BaseModel):
    """RAGAS evaluation isteği."""
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None


class BatchEvaluationRequest(BaseModel):
    """Toplu RAGAS evaluation isteği."""
    evaluations: List[RAGEvaluationRequest]


# ============ HELPER FUNCTIONS ============

def _interpret_ragas_score(score: float) -> str:
    """RAGAS skorunu yorumla."""
    if score >= 0.9:
        return "Mükemmel - Yanıt yüksek kaliteli ve güvenilir"
    elif score >= 0.75:
        return "İyi - Yanıt güvenilir, küçük iyileştirmeler yapılabilir"
    elif score >= 0.6:
        return "Orta - Yanıt kabul edilebilir ama dikkatli olunmalı"
    elif score >= 0.4:
        return "Zayıf - Yanıt güvenilirlik açısından sorunlu"
    else:
        return "Kritik - Yanıt güvenilir değil, yeniden oluşturulmalı"


# ============ RAG QUERY ENDPOINTS ============

@router.post("/query")
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


@router.post("/stream")
async def rag_stream(request: RAGStreamRequest):
    """
    Streaming RAG yanıtı (SSE).
    
    Real-time token streaming ile RAG yanıtı.
    """
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


@router.post("/search")
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


@router.post("/pages")
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


@router.get("/analyze")
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


@router.get("/stats")
async def get_rag_stats():
    """RAG sistem istatistikleri."""
    try:
        from rag.orchestrator import rag_orchestrator
        
        return rag_orchestrator.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_rag_status():
    """RAG sistem durumu - sağlık kontrolü."""
    try:
        # Vector store durumunu kontrol et
        doc_count = vector_store.count()
        unique_sources = vector_store.get_unique_sources()
        
        return {
            "success": True,
            "status": "healthy",
            "document_count": doc_count,
            "source_count": len(unique_sources),
            "vector_store": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/cache/clear")
async def clear_rag_cache():
    """RAG cache'ini temizle."""
    try:
        from rag.orchestrator import rag_orchestrator
        
        rag_orchestrator.clear_cache()
        
        return {"message": "RAG cache temizlendi", "success": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
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


# ============ RAGAS EVALUATION ENDPOINTS ============

@router.post("/evaluate")
async def evaluate_rag_response(request: RAGEvaluationRequest):
    """
    RAG yanıtını RAGAS metrikleriyle değerlendir.
    
    Faithfulness, Answer Relevancy ve Context Precision skorlarını döndürür.
    """
    try:
        from core.ragas_evaluation import RAGASEvaluator
        
        evaluator = RAGASEvaluator()
        
        # Metrikleri hesapla
        faithfulness = await evaluator.evaluate_faithfulness(
            question=request.question,
            answer=request.answer,
            contexts=request.contexts
        )
        
        relevancy = await evaluator.evaluate_answer_relevancy(
            question=request.question,
            answer=request.answer
        )
        
        context_precision = await evaluator.evaluate_context_precision(
            question=request.question,
            contexts=request.contexts,
            ground_truth=request.ground_truth
        )
        
        # Genel skor hesapla (ağırlıklı ortalama)
        overall_score = (
            faithfulness.get("score", 0) * 0.4 +
            relevancy.get("score", 0) * 0.35 +
            context_precision.get("score", 0) * 0.25
        )
        
        return {
            "success": True,
            "metrics": {
                "faithfulness": faithfulness,
                "answer_relevancy": relevancy,
                "context_precision": context_precision,
            },
            "overall_score": round(overall_score, 4),
            "interpretation": _interpret_ragas_score(overall_score),
        }
        
    except Exception as e:
        logger.error(f"RAGAS evaluation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "metrics": None,
        }


@router.post("/evaluate/batch")
async def batch_evaluate_rag(request: BatchEvaluationRequest):
    """
    Birden fazla RAG yanıtını toplu değerlendir.
    
    Her evaluation için ayrı skorlar ve genel istatistikler döndürür.
    """
    try:
        from core.ragas_evaluation import RAGASEvaluator
        
        evaluator = RAGASEvaluator()
        results = []
        
        for i, eval_request in enumerate(request.evaluations):
            try:
                # Metrikleri hesapla
                faithfulness = await evaluator.evaluate_faithfulness(
                    question=eval_request.question,
                    answer=eval_request.answer,
                    contexts=eval_request.contexts
                )
                
                relevancy = await evaluator.evaluate_answer_relevancy(
                    question=eval_request.question,
                    answer=eval_request.answer
                )
                
                # Genel skor
                overall_score = (
                    faithfulness.get("score", 0) * 0.6 +
                    relevancy.get("score", 0) * 0.4
                )
                
                results.append({
                    "index": i,
                    "question": eval_request.question[:100] + "...",
                    "overall_score": round(overall_score, 4),
                    "faithfulness": faithfulness.get("score", 0),
                    "relevancy": relevancy.get("score", 0),
                    "success": True,
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "error": str(e),
                    "success": False,
                })
        
        # İstatistikler
        successful = [r for r in results if r.get("success")]
        avg_score = sum(r.get("overall_score", 0) for r in successful) / len(successful) if successful else 0
        
        return {
            "success": True,
            "results": results,
            "statistics": {
                "total": len(results),
                "successful": len(successful),
                "failed": len(results) - len(successful),
                "average_score": round(avg_score, 4),
            }
        }
        
    except Exception as e:
        logger.error(f"Batch RAGAS evaluation error: {e}")
        return {"success": False, "error": str(e)}
