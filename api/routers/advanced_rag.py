"""
Advanced RAG Router
====================

Enterprise-grade Advanced RAG sistemleri için REST API endpoints.

Endpoints:
- /advanced/unified    - Unified Orchestrator (automatic strategy selection)
- /advanced/agentic    - Agentic RAG (agent-based dynamic retrieval)
- /advanced/self       - Self-RAG (self-reflective with quality feedback)
- /advanced/graph      - Graph RAG (knowledge graph enhanced)
- /advanced/multimodal - Multimodal RAG (text, images, tables, code)
- /advanced/conversational - Conversational RAG (chat-aware with memory)
- /advanced/verify     - Citation verification and hallucination detection
- /advanced/evaluate   - RAGAS metrics evaluation

Author: AI Assistant
Version: 1.0.0
"""

import logging
import json
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.logger import get_logger

router = APIRouter(prefix="/api/advanced", tags=["Advanced RAG"])
logger = get_logger("api.advanced_rag")


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class UnifiedQueryRequest(BaseModel):
    """Unified Orchestrator sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    strategy: Optional[str] = Field(
        default="auto",
        description="Strategy: auto, agentic, self_rag, graph_rag, multimodal, conversational, standard"
    )
    conversation_history: Optional[List[str]] = None
    context_filter: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=5, ge=1, le=20)


class UnifiedQueryResponse(BaseModel):
    """Unified Orchestrator yanıt modeli."""
    query: str
    answer: str
    strategy_used: str
    quality_score: float
    confidence: float
    phases_completed: List[str]
    fallback_used: bool
    total_time_ms: int
    sources: List[str]
    request_id: str


class AgenticQueryRequest(BaseModel):
    """Agentic RAG sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    max_iterations: int = Field(default=3, ge=1, le=10)
    top_k: int = Field(default=5, ge=1, le=20)


class SelfRAGQueryRequest(BaseModel):
    """Self-RAG sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    max_iterations: int = Field(default=3, ge=1, le=5)
    min_quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    top_k: int = Field(default=5, ge=1, le=20)


class GraphRAGQueryRequest(BaseModel):
    """Graph RAG sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    max_hops: int = Field(default=2, ge=1, le=5)
    include_graph: bool = Field(default=False)
    top_k: int = Field(default=5, ge=1, le=20)


class ConversationalQueryRequest(BaseModel):
    """Conversational RAG sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str = Field(default="default")
    max_history: int = Field(default=10, ge=1, le=50)
    top_k: int = Field(default=5, ge=1, le=20)


class MultimodalQueryRequest(BaseModel):
    """Multimodal RAG sorgu isteği."""
    query: str = Field(..., min_length=1, max_length=5000)
    include_images: bool = Field(default=True)
    include_tables: bool = Field(default=True)
    include_code: bool = Field(default=True)
    top_k: int = Field(default=5, ge=1, le=20)


class VerificationRequest(BaseModel):
    """Citation verification isteği."""
    answer: str = Field(..., min_length=1, max_length=10000)
    sources: List[str] = Field(..., min_length=1)
    strict_mode: bool = Field(default=False)


class VerificationResponse(BaseModel):
    """Citation verification yanıtı."""
    is_grounded: bool
    faithfulness_score: float
    grounding_score: float
    hallucinations_detected: int
    unsupported_claims: List[str]
    verification_time_ms: int


class RAGASEvaluationRequest(BaseModel):
    """RAGAS evaluation isteği."""
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    contexts: List[str] = Field(..., min_length=1)
    ground_truth: Optional[str] = None
    evaluation_level: str = Field(
        default="standard",
        description="Level: basic, standard, comprehensive"
    )


class RAGASEvaluationResponse(BaseModel):
    """RAGAS evaluation yanıtı."""
    overall_score: float
    quality_tier: str
    metrics: Dict[str, Any]
    issues_detected: List[str]
    recommendations: List[str]
    processing_time_ms: int


class BatchEvaluationRequest(BaseModel):
    """Toplu RAGAS evaluation isteği."""
    samples: List[Dict[str, Any]] = Field(..., min_length=1, max_length=100)
    evaluation_level: str = Field(default="standard")


# ============================================================================
# UNIFIED ORCHESTRATOR ENDPOINTS
# ============================================================================

@router.post("/unified/query", response_model=UnifiedQueryResponse)
async def unified_query(request: UnifiedQueryRequest):
    """
    Unified Advanced RAG Query.
    
    Automatic strategy selection ile en optimal RAG pipeline'ını kullanır.
    
    Strategies:
    - auto: Sorgu analizine göre otomatik seçim
    - agentic: Karmaşık, çok adımlı sorgular için
    - self_rag: Kalite kritik sorgular için
    - graph_rag: İlişki ve entity sorguları için
    - multimodal: Görsel içerik sorguları için
    - conversational: Sohbet bağlamlı sorgular için
    - standard: Basit factual sorgular için
    """
    try:
        from rag.unified_orchestrator import get_unified_orchestrator, RAGStrategy
        
        orchestrator = get_unified_orchestrator()
        
        # Map string strategy to enum
        strategy_map = {
            "auto": RAGStrategy.AUTO,
            "agentic": RAGStrategy.AGENTIC,
            "self_rag": RAGStrategy.SELF_RAG,
            "graph_rag": RAGStrategy.GRAPH_RAG,
            "multimodal": RAGStrategy.MULTIMODAL,
            "conversational": RAGStrategy.CONVERSATIONAL,
            "standard": RAGStrategy.STANDARD,
        }
        strategy = strategy_map.get(request.strategy, RAGStrategy.AUTO)
        
        result = orchestrator.query(
            query=request.query,
            strategy=strategy,
            conversation_history=request.conversation_history,
            context_filter=request.context_filter,
            k=request.top_k,
        )
        
        return UnifiedQueryResponse(
            query=result.query,
            answer=result.answer,
            strategy_used=result.strategy_decision.primary_strategy.value if result.strategy_decision else "unknown",
            quality_score=result.overall_quality_score,
            confidence=result.confidence,
            phases_completed=result.phases_completed,
            fallback_used=result.fallback_used,
            total_time_ms=result.total_time_ms,
            sources=result.sources,
            request_id=result.request_id,
        )
        
    except Exception as e:
        logger.error(f"Unified query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unified/stats")
async def get_unified_stats():
    """Unified orchestrator istatistikleri."""
    try:
        from rag.unified_orchestrator import get_unified_orchestrator
        
        orchestrator = get_unified_orchestrator()
        return orchestrator.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENTIC RAG ENDPOINTS
# ============================================================================

@router.post("/agentic/query")
async def agentic_query(request: AgenticQueryRequest):
    """
    Agentic RAG Query.
    
    Agent-based dynamic retrieval ile karmaşık sorguları çözer.
    - Sorgu analizi ve planlama
    - Dinamik strateji seçimi
    - İteratif iyileştirme
    """
    try:
        from rag.agentic_rag import get_agentic_rag
        
        agentic_rag = get_agentic_rag()
        
        result = agentic_rag.query(
            query=request.query,
            max_iterations=request.max_iterations,
            k=request.top_k,
        )
        
        return result.to_dict() if hasattr(result, 'to_dict') else {
            "answer": str(result),
            "strategy": "agentic",
        }
        
    except Exception as e:
        logger.error(f"Agentic query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agentic/stats")
async def get_agentic_stats():
    """Agentic RAG istatistikleri."""
    try:
        from rag.agentic_rag import get_agentic_rag
        
        agentic_rag = get_agentic_rag()
        return agentic_rag.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SELF-RAG ENDPOINTS
# ============================================================================

@router.post("/self/query")
async def self_rag_query(request: SelfRAGQueryRequest):
    """
    Self-RAG Query.
    
    Self-reflective RAG ile yüksek kaliteli yanıtlar üretir.
    - Retrieval kararı (gerekli mi?)
    - Passage değerlendirme
    - Yanıt kritik ve düzeltme
    - Hallucination tespiti
    """
    try:
        from rag.self_rag import get_self_rag
        
        self_rag = get_self_rag()
        
        result = self_rag.query(
            query=request.query,
            max_iterations=request.max_iterations,
            min_quality=request.min_quality_threshold,
            k=request.top_k,
        )
        
        return result.to_dict() if hasattr(result, 'to_dict') else {
            "answer": str(result),
            "strategy": "self_rag",
        }
        
    except Exception as e:
        logger.error(f"Self-RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/self/stats")
async def get_self_rag_stats():
    """Self-RAG istatistikleri."""
    try:
        from rag.self_rag import get_self_rag
        
        self_rag = get_self_rag()
        return self_rag.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GRAPH RAG ENDPOINTS
# ============================================================================

@router.post("/graph/query")
async def graph_rag_query(request: GraphRAGQueryRequest):
    """
    Graph RAG Query.
    
    Knowledge Graph ile zenginleştirilmiş retrieval.
    - Entity extraction
    - Relationship discovery
    - Multi-hop reasoning
    - Subgraph retrieval
    """
    try:
        from rag.graph_rag_advanced import get_graph_rag
        
        graph_rag = get_graph_rag()
        
        result = graph_rag.query(
            query=request.query,
            max_hops=request.max_hops,
            include_graph=request.include_graph,
            k=request.top_k,
        )
        
        return result.to_dict() if hasattr(result, 'to_dict') else {
            "answer": str(result),
            "strategy": "graph_rag",
        }
        
    except Exception as e:
        logger.error(f"Graph RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/entities")
async def get_graph_entities(limit: int = Query(default=100, ge=1, le=1000)):
    """Knowledge graph entity'lerini listele."""
    try:
        from rag.graph_rag_advanced import get_graph_rag
        
        graph_rag = get_graph_rag()
        entities = graph_rag.get_entities(limit=limit)
        
        return {
            "entities": entities,
            "total": len(entities),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/relationships")
async def get_graph_relationships(
    entity_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000)
):
    """Knowledge graph ilişkilerini listele."""
    try:
        from rag.graph_rag_advanced import get_graph_rag
        
        graph_rag = get_graph_rag()
        relationships = graph_rag.get_relationships(entity_id=entity_id, limit=limit)
        
        return {
            "relationships": relationships,
            "total": len(relationships),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats")
async def get_graph_stats():
    """Graph RAG istatistikleri."""
    try:
        from rag.graph_rag_advanced import get_graph_rag
        
        graph_rag = get_graph_rag()
        return graph_rag.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONVERSATIONAL RAG ENDPOINTS
# ============================================================================

@router.post("/conversational/query")
async def conversational_query(request: ConversationalQueryRequest):
    """
    Conversational RAG Query.
    
    Chat-aware RAG ile sohbet bağlamlı yanıtlar.
    - Conversation memory
    - Query reformulation
    - Anaphora resolution
    - Topic tracking
    """
    try:
        from rag.conversational_rag import get_conversational_rag
        
        conv_rag = get_conversational_rag()
        
        result = conv_rag.query(
            query=request.query,
            conversation_id=request.conversation_id,
            max_history=request.max_history,
            k=request.top_k,
        )
        
        return result.to_dict() if hasattr(result, 'to_dict') else {
            "answer": str(result),
            "conversation_id": request.conversation_id,
            "strategy": "conversational",
        }
        
    except Exception as e:
        logger.error(f"Conversational query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversational/history/{conversation_id}")
async def get_conversation_history(conversation_id: str, limit: int = Query(default=20, ge=1, le=100)):
    """Conversation geçmişini getir."""
    try:
        from rag.conversational_rag import get_conversational_rag
        
        conv_rag = get_conversational_rag()
        history = conv_rag.get_history(conversation_id=conversation_id, limit=limit)
        
        return {
            "conversation_id": conversation_id,
            "messages": history,
            "total": len(history),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversational/history/{conversation_id}")
async def clear_conversation_history(conversation_id: str):
    """Conversation geçmişini temizle."""
    try:
        from rag.conversational_rag import get_conversational_rag
        
        conv_rag = get_conversational_rag()
        conv_rag.clear_history(conversation_id=conversation_id)
        
        return {
            "message": f"Conversation {conversation_id} cleared",
            "success": True,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversational/stats")
async def get_conversational_stats():
    """Conversational RAG istatistikleri."""
    try:
        from rag.conversational_rag import get_conversational_rag
        
        conv_rag = get_conversational_rag()
        return conv_rag.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MULTIMODAL RAG ENDPOINTS
# ============================================================================

@router.post("/multimodal/query")
async def multimodal_query(request: MultimodalQueryRequest):
    """
    Multimodal RAG Query.
    
    Çoklu içerik tiplerini destekleyen RAG.
    - Text processing
    - Image OCR & analysis
    - Table extraction
    - Code understanding
    """
    try:
        from rag.multimodal_rag import get_multimodal_rag
        
        mm_rag = get_multimodal_rag()
        
        result = mm_rag.query(
            query=request.query,
            include_images=request.include_images,
            include_tables=request.include_tables,
            include_code=request.include_code,
            k=request.top_k,
        )
        
        return result.to_dict() if hasattr(result, 'to_dict') else {
            "answer": str(result),
            "strategy": "multimodal",
        }
        
    except Exception as e:
        logger.error(f"Multimodal query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multimodal/process")
async def process_multimodal_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Multimodal dosya işle.
    
    Desteklenen formatlar: PDF, DOCX, PNG, JPG, CSV, JSON
    """
    try:
        from rag.multimodal_rag import get_multimodal_rag
        
        mm_rag = get_multimodal_rag()
        
        # Read file content
        content = await file.read()
        
        # Process file
        result = mm_rag.process_file(
            content=content,
            filename=file.filename,
            content_type=file.content_type,
        )
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "processed": True,
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Multimodal file processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multimodal/stats")
async def get_multimodal_stats():
    """Multimodal RAG istatistikleri."""
    try:
        from rag.multimodal_rag import get_multimodal_rag
        
        mm_rag = get_multimodal_rag()
        return mm_rag.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CITATION VERIFICATION ENDPOINTS
# ============================================================================

@router.post("/verify", response_model=VerificationResponse)
async def verify_citation(request: VerificationRequest):
    """
    Citation Verification.
    
    Yanıtın kaynaklara dayandığını doğrula.
    - Claim extraction
    - Source verification
    - Hallucination detection
    - Grounding scoring
    """
    try:
        from rag.citation_verifier import get_citation_verifier
        
        verifier = get_citation_verifier()
        
        result = verifier.verify(
            answer=request.answer,
            sources=request.sources,
            strict_mode=request.strict_mode,
        )
        
        return VerificationResponse(
            is_grounded=result.is_grounded,
            faithfulness_score=result.faithfulness_score,
            grounding_score=result.grounding_score,
            hallucinations_detected=len(result.hallucinations) if hasattr(result, 'hallucinations') else 0,
            unsupported_claims=result.unsupported_claims[:10] if hasattr(result, 'unsupported_claims') else [],
            verification_time_ms=result.verification_time_ms if hasattr(result, 'verification_time_ms') else 0,
        )
        
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/stats")
async def get_verification_stats():
    """Citation verifier istatistikleri."""
    try:
        from rag.citation_verifier import get_citation_verifier
        
        verifier = get_citation_verifier()
        return verifier.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RAGAS EVALUATION ENDPOINTS
# ============================================================================

@router.post("/evaluate", response_model=RAGASEvaluationResponse)
async def ragas_evaluate(request: RAGASEvaluationRequest):
    """
    RAGAS Evaluation.
    
    RAG yanıtını kapsamlı metriklerle değerlendir.
    
    Metrics:
    - Answer Relevancy
    - Faithfulness
    - Context Precision
    - Context Recall
    - Context Relevancy
    - Coherence
    - Harmfulness
    """
    try:
        from rag.ragas_metrics import get_ragas_evaluator, EvaluationLevel
        
        level_map = {
            "basic": EvaluationLevel.BASIC,
            "standard": EvaluationLevel.STANDARD,
            "comprehensive": EvaluationLevel.COMPREHENSIVE,
        }
        level = level_map.get(request.evaluation_level, EvaluationLevel.STANDARD)
        
        evaluator = get_ragas_evaluator(level=level)
        
        result = evaluator.evaluate(
            question=request.question,
            answer=request.answer,
            contexts=request.contexts,
            ground_truth=request.ground_truth,
        )
        
        return RAGASEvaluationResponse(
            overall_score=result.overall_score,
            quality_tier=result.quality_tier.value,
            metrics={k.value: v.to_dict() for k, v in result.metrics.items()},
            issues_detected=result.issues_detected,
            recommendations=result.recommendations,
            processing_time_ms=result.total_processing_time_ms,
        )
        
    except Exception as e:
        logger.error(f"RAGAS evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/batch")
async def ragas_batch_evaluate(request: BatchEvaluationRequest):
    """
    Batch RAGAS Evaluation.
    
    Birden fazla RAG yanıtını toplu değerlendir.
    """
    try:
        from rag.ragas_metrics import get_ragas_evaluator, EvaluationLevel
        
        level_map = {
            "basic": EvaluationLevel.BASIC,
            "standard": EvaluationLevel.STANDARD,
            "comprehensive": EvaluationLevel.COMPREHENSIVE,
        }
        level = level_map.get(request.evaluation_level, EvaluationLevel.STANDARD)
        
        evaluator = get_ragas_evaluator(level=level)
        
        batch_result = evaluator.evaluate_batch(samples=request.samples)
        
        return {
            "total_samples": batch_result.total_samples,
            "successful_samples": batch_result.successful_samples,
            "failed_samples": batch_result.failed_samples,
            "mean_scores": batch_result.mean_scores,
            "quality_distribution": batch_result.quality_distribution,
            "total_processing_time_ms": batch_result.total_processing_time_ms,
        }
        
    except Exception as e:
        logger.error(f"Batch RAGAS evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evaluate/stats")
async def get_evaluation_stats():
    """RAGAS evaluator istatistikleri."""
    try:
        from rag.ragas_metrics import get_ragas_evaluator
        
        evaluator = get_ragas_evaluator()
        return evaluator.get_stats()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@router.get("/health")
async def advanced_rag_health():
    """Advanced RAG sistemlerinin sağlık kontrolü."""
    systems = {}
    
    # Check each system
    try:
        from rag.unified_orchestrator import get_unified_orchestrator
        get_unified_orchestrator()
        systems["unified_orchestrator"] = "healthy"
    except Exception as e:
        systems["unified_orchestrator"] = f"error: {str(e)}"
    
    try:
        from rag.agentic_rag import get_agentic_rag
        get_agentic_rag()
        systems["agentic_rag"] = "healthy"
    except Exception as e:
        systems["agentic_rag"] = f"error: {str(e)}"
    
    try:
        from rag.self_rag import get_self_rag
        get_self_rag()
        systems["self_rag"] = "healthy"
    except Exception as e:
        systems["self_rag"] = f"error: {str(e)}"
    
    try:
        from rag.graph_rag_advanced import get_graph_rag
        get_graph_rag()
        systems["graph_rag"] = "healthy"
    except Exception as e:
        systems["graph_rag"] = f"error: {str(e)}"
    
    try:
        from rag.conversational_rag import get_conversational_rag
        get_conversational_rag()
        systems["conversational_rag"] = "healthy"
    except Exception as e:
        systems["conversational_rag"] = f"error: {str(e)}"
    
    try:
        from rag.multimodal_rag import get_multimodal_rag
        get_multimodal_rag()
        systems["multimodal_rag"] = "healthy"
    except Exception as e:
        systems["multimodal_rag"] = f"error: {str(e)}"
    
    try:
        from rag.citation_verifier import get_citation_verifier
        get_citation_verifier()
        systems["citation_verifier"] = "healthy"
    except Exception as e:
        systems["citation_verifier"] = f"error: {str(e)}"
    
    try:
        from rag.ragas_metrics import get_ragas_evaluator
        get_ragas_evaluator()
        systems["ragas_evaluator"] = "healthy"
    except Exception as e:
        systems["ragas_evaluator"] = f"error: {str(e)}"
    
    # Determine overall health
    healthy_count = sum(1 for v in systems.values() if v == "healthy")
    total_count = len(systems)
    
    overall = "healthy" if healthy_count == total_count else (
        "degraded" if healthy_count > total_count // 2 else "unhealthy"
    )
    
    return {
        "status": overall,
        "systems": systems,
        "healthy_count": healthy_count,
        "total_count": total_count,
    }


@router.get("/capabilities")
async def get_capabilities():
    """Advanced RAG yeteneklerini listele."""
    return {
        "unified_orchestrator": {
            "description": "Automatic strategy selection with fallback support",
            "strategies": ["auto", "agentic", "self_rag", "graph_rag", "multimodal", "conversational", "standard"],
            "features": ["quality_gates", "fallbacks", "verification", "metrics"],
        },
        "agentic_rag": {
            "description": "Agent-based dynamic retrieval for complex queries",
            "features": ["query_analysis", "planning", "multi_step", "dynamic_strategy"],
        },
        "self_rag": {
            "description": "Self-reflective RAG with quality feedback loop",
            "features": ["retrieval_decision", "passage_evaluation", "self_critique", "refinement"],
        },
        "graph_rag": {
            "description": "Knowledge Graph enhanced retrieval",
            "features": ["entity_extraction", "relationship_discovery", "multi_hop_reasoning", "subgraph_retrieval"],
        },
        "conversational_rag": {
            "description": "Chat-aware RAG with conversation memory",
            "features": ["memory", "query_reformulation", "anaphora_resolution", "topic_tracking"],
        },
        "multimodal_rag": {
            "description": "Multi-content type processing",
            "formats": ["text", "pdf", "docx", "images", "tables", "code"],
            "features": ["ocr", "table_extraction", "code_understanding"],
        },
        "citation_verifier": {
            "description": "Citation verification and hallucination detection",
            "features": ["claim_extraction", "source_verification", "hallucination_detection", "grounding_score"],
        },
        "ragas_evaluator": {
            "description": "Comprehensive RAG quality metrics",
            "metrics": [
                "answer_relevancy", "faithfulness", "context_precision", 
                "context_recall", "context_relevancy", "coherence", "harmfulness"
            ],
            "levels": ["basic", "standard", "comprehensive"],
        },
    }
