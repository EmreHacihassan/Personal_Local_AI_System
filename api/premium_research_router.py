"""
🚀 Premium Research & Chat API Router
=====================================

Endüstri-seviyesi premium araştırma ve sohbet API'si.
Deep Research 3.0, Multi-Provider Search, Reasoning Engine entegrasyonu.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3", tags=["Premium Research"])


# ============ PYDANTIC MODELS ============

class DeepResearchRequest(BaseModel):
    """Deep Research 3.0 isteği"""
    query: str = Field(..., min_length=5, max_length=2000, description="Araştırma sorusu")
    depth: str = Field(default="standard", description="quick, standard, comprehensive, exhaustive")
    session_id: Optional[str] = None


class DeepResearchResponse(BaseModel):
    """Deep Research sonucu"""
    query: str
    executive_summary: str
    findings: List[Dict[str, Any]]
    overall_confidence: float
    overall_grade: str
    total_sources: int
    key_insights: List[str]
    limitations: List[str]
    iterations: int
    total_time_seconds: float


class MultiSearchRequest(BaseModel):
    """Multi-Provider Search isteği"""
    query: str = Field(..., min_length=2, max_length=500)
    providers: Optional[List[str]] = Field(default=None, description="ddg, brave, wiki, semantic_scholar, jina")
    num_results: int = Field(default=10, ge=1, le=30)
    include_content: bool = Field(default=True)


class MultiSearchResponse(BaseModel):
    """Multi-Provider Search sonucu"""
    query: str
    results: List[Dict[str, Any]]
    providers_used: List[str]
    total_results: int
    search_time_ms: int


class ReasoningRequest(BaseModel):
    """Reasoning Engine isteği"""
    question: str = Field(..., min_length=5, max_length=2000)
    mode: str = Field(default="auto", description="auto, cot, debate, comprehensive")
    depth: str = Field(default="standard", description="quick, standard, deep")
    context: Optional[str] = None


class ReasoningResponse(BaseModel):
    """Reasoning sonucu"""
    question: str
    answer: str
    confidence: float
    confidence_level: str
    reasoning_type: str
    chain_of_thought: Optional[Dict[str, Any]] = None
    debate: Optional[Dict[str, Any]] = None
    total_time_ms: int


class PremiumChatRequest(BaseModel):
    """Premium Chat isteği"""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    enable_follow_ups: bool = Field(default=True)
    enable_source_cards: bool = Field(default=True)
    enable_reasoning: bool = Field(default=False)


class PremiumChatResponse(BaseModel):
    """Premium Chat sonucu"""
    response: str
    session_id: str
    follow_up_questions: Optional[List[Dict[str, str]]] = None
    source_cards: Optional[List[Dict[str, Any]]] = None
    reasoning_steps: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any]
    timestamp: str


# ============ ENDPOINTS ============

@router.post("/research", response_model=DeepResearchResponse)
async def deep_research(request: DeepResearchRequest):
    """
    🔬 Deep Research 3.0 API
    
    Endüstri-seviyesi derinlemesine araştırma.
    Perplexity Pro, ChatGPT Deep Research kalitesinde.
    
    Features:
    - Iterative Research Loop (3-5 iterations)
    - Evidence Grading (A-F)
    - Multi-Source Synthesis
    - Confidence Scoring
    """
    import time
    start_time = time.time()
    
    try:
        from core.deep_research_engine import get_deep_research_engine, ResearchReport
        
        engine = get_deep_research_engine()
        
        # Run research
        final_report = None
        async for result in engine.research(request.query, depth=request.depth):
            if isinstance(result, ResearchReport):
                final_report = result
        
        if not final_report:
            raise HTTPException(status_code=500, detail="Araştırma tamamlanamadı")
        
        return DeepResearchResponse(
            query=final_report.query,
            executive_summary=final_report.executive_summary,
            findings=[f.to_dict() for f in final_report.findings],
            overall_confidence=final_report.overall_confidence,
            overall_grade=final_report.overall_grade.value,
            total_sources=final_report.total_sources,
            key_insights=final_report.key_insights,
            limitations=final_report.limitations,
            iterations=final_report.iterations,
            total_time_seconds=final_report.total_time_seconds,
        )
        
    except ImportError as e:
        logger.warning(f"Deep Research module not available: {e}")
        raise HTTPException(status_code=501, detail="Deep Research modülü yüklenmemiş")
    except Exception as e:
        logger.error(f"Deep Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/stream")
async def deep_research_stream(request: DeepResearchRequest):
    """
    🔬 Deep Research 3.0 Streaming API
    
    Araştırma ilerlemesini gerçek zamanlı stream eder.
    SSE (Server-Sent Events) formatında.
    """
    async def generate():
        try:
            from core.deep_research_engine import get_deep_research_engine, ResearchProgress, ResearchReport
            
            engine = get_deep_research_engine()
            
            async for result in engine.research(request.query, depth=request.depth):
                if isinstance(result, ResearchProgress):
                    yield f"data: {json.dumps({'type': 'progress', **result.to_dict()})}\n\n"
                elif isinstance(result, ResearchReport):
                    yield f"data: {json.dumps({'type': 'report', **result.to_dict()})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/search", response_model=MultiSearchResponse)
async def multi_provider_search(request: MultiSearchRequest):
    """
    🔍 Multi-Provider Search API
    
    Birden fazla arama motorundan sonuç toplar ve birleştirir.
    
    Desteklenen Providerlar (Ücretsiz):
    - DuckDuckGo (ddg) - Sınırsız
    - Brave Search (brave) - 2000/ay ücretsiz
    - Wikipedia (wiki) - Sınırsız
    - Semantic Scholar (semantic_scholar) - Akademik
    - Jina Reader (jina) - İçerik çıkarma
    """
    import time
    start_time = time.time()
    
    try:
        from tools.multi_provider_search import get_multi_search_engine
        
        engine = get_multi_search_engine()
        
        # Search
        response = await engine.search(
            query=request.query,
            num_results=request.num_results,
            providers=request.providers,
        )
        
        # Extract content if requested
        results = []
        for r in response.results:
            result_dict = {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "provider": r.provider,
                "score": r.score,
            }
            if request.include_content and hasattr(r, 'content'):
                result_dict["content"] = r.content[:1000] if r.content else None
            results.append(result_dict)
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return MultiSearchResponse(
            query=request.query,
            results=results,
            providers_used=response.providers_used,
            total_results=len(results),
            search_time_ms=search_time_ms,
        )
        
    except ImportError as e:
        logger.warning(f"Multi-Provider Search module not available: {e}")
        raise HTTPException(status_code=501, detail="Multi-Provider Search modülü yüklenmemiş")
    except Exception as e:
        logger.error(f"Multi-Provider Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reason", response_model=ReasoningResponse)
async def reasoning(request: ReasoningRequest):
    """
    🧠 Premium Reasoning Engine API
    
    Gelişmiş reasoning ve düşünme yetenekleri.
    
    Modlar:
    - auto: Otomatik mod seçimi
    - cot: Chain of Thought (adım adım düşünme)
    - debate: Multi-Agent Debate (çoklu perspektif)
    - comprehensive: Tüm yeteneklerin kombinasyonu
    """
    try:
        from core.reasoning_engine import get_reasoning_engine
        
        engine = get_reasoning_engine()
        
        result = await engine.reason(
            question=request.question,
            mode=request.mode,
            depth=request.depth,
            context=request.context or "",
        )
        
        return ReasoningResponse(
            question=result.question,
            answer=result.answer,
            confidence=result.confidence,
            confidence_level=result.confidence_level.value,
            reasoning_type=result.reasoning_type,
            chain_of_thought=result.chain_of_thought.to_dict() if result.chain_of_thought else None,
            debate=result.debate.to_dict() if result.debate else None,
            total_time_ms=result.total_time_ms,
        )
        
    except ImportError as e:
        logger.warning(f"Reasoning Engine module not available: {e}")
        raise HTTPException(status_code=501, detail="Reasoning Engine modülü yüklenmemiş")
    except Exception as e:
        logger.error(f"Reasoning error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reason/stream")
async def reasoning_stream(request: ReasoningRequest):
    """
    🧠 Premium Reasoning Engine Streaming API
    
    Düşünme adımlarını gerçek zamanlı stream eder.
    """
    async def generate():
        try:
            from core.reasoning_engine import get_reasoning_engine
            
            engine = get_reasoning_engine()
            
            async for step in engine.stream_reasoning(
                question=request.question,
                mode=request.mode,
                depth=request.depth,
            ):
                yield f"data: {json.dumps(step)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.post("/chat/premium", response_model=PremiumChatResponse)
async def premium_chat(request: PremiumChatRequest):
    """
    💎 Premium Chat API
    
    Endüstri-seviyesi chat deneyimi.
    
    Features:
    - Auto Follow-up Questions
    - Source Cards
    - Reasoning Steps (optional)
    - Conversation Context
    """
    import time
    start_time = time.time()
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get base response from orchestrator
        from agents.orchestrator import orchestrator
        
        base_response = orchestrator.execute(request.message, {})
        
        # Generate follow-up questions
        follow_ups = None
        if request.enable_follow_ups:
            try:
                from core.premium_chat_engine import get_premium_chat_engine
                chat_engine = get_premium_chat_engine()
                follow_ups_result = await chat_engine.follow_up_generator.generate(
                    question=request.message,
                    answer=base_response.content,
                )
                follow_ups = [{"text": q.text, "category": q.category} for q in follow_ups_result]
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Follow-up generation error: {e}")
        
        # Generate source cards
        source_cards = None
        if request.enable_source_cards and base_response.sources:
            # sources is List[str] (URLs), convert to card format
            source_cards = [
                {
                    "title": url.split("/")[-1] if "/" in url else url,
                    "url": url,
                    "snippet": "",
                    "source_type": "web",
                }
                for url in base_response.sources[:5]
                if isinstance(url, str)
            ]
        
        # Add reasoning if requested
        reasoning_steps = None
        if request.enable_reasoning:
            try:
                from core.reasoning_engine import get_reasoning_engine
                engine = get_reasoning_engine()
                result = await engine.reason(request.message, mode="cot", depth="quick")
                if result.chain_of_thought:
                    reasoning_steps = [s.to_dict() for s in result.chain_of_thought.steps]
            except Exception as e:
                logger.warning(f"Reasoning error: {e}")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return PremiumChatResponse(
            response=base_response.content,
            session_id=session_id,
            follow_up_questions=follow_ups,
            source_cards=source_cards,
            reasoning_steps=reasoning_steps,
            metadata={
                "agent": base_response.metadata.get("agent", "unknown"),
                "duration_ms": duration_ms,
                "premium_features": {
                    "follow_ups": follow_ups is not None,
                    "source_cards": source_cards is not None,
                    "reasoning": reasoning_steps is not None,
                },
            },
            timestamp=datetime.now().isoformat(),
        )
        
    except Exception as e:
        logger.error(f"Premium Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def premium_status():
    """
    Premium modüllerin durumu
    """
    status = {
        "deep_research": False,
        "multi_provider_search": False,
        "reasoning_engine": False,
        "premium_chat": False,
        "hyde_transformer": False,
    }
    
    try:
        from core.deep_research_engine import get_deep_research_engine
        get_deep_research_engine()
        status["deep_research"] = True
    except Exception:
        pass
    
    try:
        from tools.multi_provider_search import get_multi_search_engine
        get_multi_search_engine()
        status["multi_provider_search"] = True
    except Exception:
        pass
    
    try:
        from core.reasoning_engine import get_reasoning_engine
        get_reasoning_engine()
        status["reasoning_engine"] = True
    except Exception:
        pass
    
    try:
        from core.premium_chat_engine import get_premium_chat_engine
        get_premium_chat_engine()
        status["premium_chat"] = True
    except Exception:
        pass
    
    try:
        from rag.hyde_transformer import get_hyde_generator
        get_hyde_generator()
        status["hyde_transformer"] = True
    except Exception:
        pass
    
    all_enabled = all(status.values())
    
    return {
        "premium_enabled": all_enabled,
        "modules": status,
        "timestamp": datetime.now().isoformat(),
    }
