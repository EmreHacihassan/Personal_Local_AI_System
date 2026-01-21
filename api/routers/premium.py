"""
Enterprise AI Assistant - Premium Features API Endpoints
========================================================

Premium özellikler için RESTful API.

Endpoints:
- POST /premium/tag - Döküman etiketle
- GET /premium/dashboard - Analytics dashboard
- GET /premium/metrics - Live metrics
- POST /premium/rerank - Sonuçları yeniden sırala
- GET /premium/graph - Knowledge graph
- POST /premium/graph/build - Knowledge graph oluştur
- GET /premium/graph/related/{doc_id} - İlişkili dökümanlar
- GET /premium/graph/path - İki döküman arası yol
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from core.premium_features import (
    get_premium_features,
    SmartAutoTagger,
    RealTimeAnalytics,
    SemanticReranker,
    KnowledgeGraph,
    TaggingConfig,
    RerankerConfig
)
from core.vector_store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/premium", tags=["Premium Features"])


# =============================================================================
# STATUS ENDPOINT
# =============================================================================

@router.get("/status")
async def premium_status():
    """
    🔍 Premium özellikler durumu.
    
    Returns:
        Premium modüllerinin durumu ve aktiflik bilgisi
    """
    try:
        premium = get_premium_features()
        return {
            "success": True,
            "status": "operational",
            "message": "Premium features are active",
            "modules": {
                "auto_tagger": premium.auto_tagger is not None,
                "analytics": premium.analytics is not None,
                "reranker": premium.reranker is not None,
                "knowledge_graph": premium.knowledge_graph is not None
            },
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Premium status error: {e}")
        return {
            "success": True,
            "status": "degraded",
            "message": str(e),
            "modules": {},
            "version": "2.0.0"
        }


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class TagRequest(BaseModel):
    """Auto-tagging isteği."""
    content: str = Field(..., min_length=1, max_length=100000)
    metadata: Optional[Dict[str, Any]] = None


class TagResponse(BaseModel):
    """Auto-tagging yanıtı."""
    tags: List[str]
    categories: List[Dict[str, Any]]
    entities: Dict[str, List[str]]
    keywords: List[Dict[str, Any]]
    language: Dict[str, Any]
    confidence: float


class ReranRequest(BaseModel):
    """Reranking isteği."""
    query: str = Field(..., min_length=1, max_length=1000)
    documents: List[Dict[str, Any]]
    original_scores: Optional[List[float]] = None
    top_k: int = Field(default=5, ge=1, le=20)


class BuildGraphRequest(BaseModel):
    """Knowledge graph oluşturma isteği."""
    rebuild: bool = Field(default=False, description="Mevcut graph'ı sıfırla")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class PathRequest(BaseModel):
    """Path bulma isteği."""
    source_id: str
    target_id: str


# =============================================================================
# AUTO-TAGGING ENDPOINTS
# =============================================================================

@router.post("/tag", response_model=TagResponse)
async def tag_document(request: TagRequest):
    """
    🏷️ Dökümanı otomatik etiketle.
    
    AI-powered auto-tagging:
    - Keyword extraction
    - Topic classification
    - Entity recognition
    - Language detection
    """
    try:
        premium = get_premium_features()
        
        # Track event
        premium.track_event("tag_document", {"content_length": len(request.content)})
        
        # Generate tags
        result = premium.tag_document(request.content, request.metadata)
        
        return TagResponse(
            tags=result.get("tags", []),
            categories=[{"name": c, "confidence": s} for c, s in result.get("categories", [])],
            entities=result.get("entities", {}),
            keywords=[{"word": w, "score": s} for w, s in result.get("keywords", [])],
            language={"code": result.get("language", ("unknown", 0.0))[0], 
                     "confidence": result.get("language", ("unknown", 0.0))[1]},
            confidence=result.get("confidence", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Tagging error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tag/batch")
async def tag_documents_batch(documents: List[TagRequest]):
    """
    🏷️ Birden fazla dökümanı toplu etiketle.
    """
    try:
        premium = get_premium_features()
        
        results = []
        for doc in documents:
            result = premium.tag_document(doc.content, doc.metadata)
            results.append({
                "tags": result.get("tags", []),
                "categories": result.get("categories", []),
                "confidence": result.get("confidence", 0.0)
            })
        
        premium.track_event("tag_batch", {"count": len(documents)})
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch tagging error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ANALYTICS DASHBOARD ENDPOINTS
# =============================================================================

@router.get("/dashboard")
async def get_dashboard():
    """
    📊 Real-time analytics dashboard verisi.
    
    İçerir:
    - Uptime ve health score
    - Response time istatistikleri
    - Error rates
    - Event counters
    - Time series data
    """
    try:
        premium = get_premium_features()
        dashboard = premium.get_dashboard()
        
        return {
            "success": True,
            "data": dashboard
        }
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_live_metrics():
    """
    📈 Anlık metrikler (WebSocket polling için).
    """
    try:
        premium = get_premium_features()
        metrics = premium.analytics.get_live_metrics()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/metrics/record")
async def record_metric(
    name: str = Body(...),
    value: float = Body(...),
    metric_type: str = Body(default="gauge")
):
    """
    📊 Custom metrik kaydet.
    """
    try:
        premium = get_premium_features()
        
        if metric_type == "gauge":
            premium.analytics.set_gauge(name, value)
        elif metric_type == "counter":
            premium.analytics.increment_counter(name, int(value))
        else:
            premium.analytics.record_metric(name, value)
        
        return {"success": True, "name": name, "value": value}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/event")
async def track_event(
    event_type: str = Body(...),
    data: Optional[Dict[str, Any]] = Body(default=None)
):
    """
    📊 Analytics event kaydet.
    """
    try:
        premium = get_premium_features()
        premium.track_event(event_type, data)
        
        return {"success": True, "event_type": event_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SEMANTIC RERANKING ENDPOINTS
# =============================================================================

@router.post("/rerank")
async def rerank_results(request: ReranRequest):
    """
    🔄 Arama sonuçlarını semantic reranking ile yeniden sırala.
    
    Özellikler:
    - Query-document relevance scoring
    - Keyword matching boost
    - Recency boost
    - Diversity optimization
    """
    try:
        premium = get_premium_features()
        
        # Track event
        premium.track_event("rerank", {
            "query_length": len(request.query),
            "doc_count": len(request.documents)
        })
        
        # Rerank
        reranked = premium.rerank_results(
            request.query,
            request.documents,
            request.original_scores
        )
        
        return {
            "success": True,
            "query": request.query,
            "original_count": len(request.documents),
            "reranked_count": len(reranked),
            "results": reranked
        }
        
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/enhanced")
async def enhanced_search(
    query: str = Body(...),
    top_k: int = Body(default=10),
    rerank: bool = Body(default=True)
):
    """
    🔍 Enhanced search with automatic reranking.
    
    Vector store araması + semantic reranking.
    """
    try:
        premium = get_premium_features()
        
        # Perform vector search
        search_results = vector_store.search(query, top_k=top_k * 2 if rerank else top_k)
        
        if not search_results:
            return {
                "success": True,
                "query": query,
                "results": [],
                "reranked": False
            }
        
        # Convert to document format
        documents = []
        original_scores = []
        
        for result in search_results:
            if isinstance(result, dict):
                documents.append(result)
                original_scores.append(result.get("score", result.get("similarity", 0.5)))
            else:
                documents.append({
                    "content": result[0] if isinstance(result, tuple) else str(result),
                    "metadata": result[1] if isinstance(result, tuple) and len(result) > 1 else {},
                    "score": result[2] if isinstance(result, tuple) and len(result) > 2 else 0.5
                })
                original_scores.append(documents[-1]["score"])
        
        # Rerank if enabled
        if rerank and documents:
            results = premium.rerank_results(query, documents, original_scores)
        else:
            results = documents[:top_k]
        
        # Track event
        premium.track_event("enhanced_search", {
            "query": query[:100],
            "result_count": len(results),
            "reranked": rerank
        })
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "reranked": rerank,
            "original_count": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# =============================================================================

@router.get("/graph")
async def get_knowledge_graph():
    """
    🕸️ Knowledge graph'ı döndür (visualization için).
    
    D3.js / vis.js uyumlu format.
    """
    try:
        premium = get_premium_features()
        graph_data = premium.export_graph()
        
        return {
            "success": True,
            "data": graph_data
        }
        
    except Exception as e:
        logger.error(f"Graph export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph/build")
async def build_knowledge_graph(request: BuildGraphRequest):
    """
    🕸️ Knowledge graph oluştur/yenile.
    
    Vector store'daki tüm dökümanlardan graph oluşturur.
    """
    try:
        premium = get_premium_features()
        
        # Reset graph if requested
        if request.rebuild:
            premium.knowledge_graph = KnowledgeGraph()
        
        # Get all documents from vector store
        try:
            stats = vector_store.get_stats()
            doc_count = stats.get("document_count", stats.get("total_documents", 0))
        except:
            doc_count = 50  # Default
        
        # Retrieve documents
        documents = []
        
        try:
            # Try to get documents through search
            sample_queries = ["", "a", "e", "i", "proje", "sistem", "bilgi"]
            seen_ids = set()
            
            for query in sample_queries:
                try:
                    results = vector_store.search(query, top_k=20)
                    for result in results:
                        if isinstance(result, dict):
                            doc_id = result.get("id", hash(result.get("content", "")[:100]))
                            if doc_id not in seen_ids:
                                seen_ids.add(doc_id)
                                documents.append(result)
                        elif isinstance(result, tuple):
                            content = result[0] if result else ""
                            doc_id = hash(content[:100])
                            if doc_id not in seen_ids:
                                seen_ids.add(doc_id)
                                documents.append({
                                    "id": str(doc_id),
                                    "content": content,
                                    "metadata": result[1] if len(result) > 1 else {}
                                })
                except:
                    continue
        except Exception as e:
            logger.warning(f"Document retrieval error: {e}")
        
        if not documents:
            return {
                "success": False,
                "message": "No documents found in vector store",
                "stats": {}
            }
        
        # Build graph
        premium.build_knowledge_graph(documents)
        
        # Track event
        premium.track_event("graph_build", {"doc_count": len(documents)})
        
        # Get stats
        graph_stats = premium.knowledge_graph.get_stats()
        
        return {
            "success": True,
            "message": f"Knowledge graph built from {len(documents)} documents",
            "stats": graph_stats
        }
        
    except Exception as e:
        logger.error(f"Graph build error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/related/{doc_id}")
async def get_related_documents(
    doc_id: str,
    max_depth: int = Query(default=2, ge=1, le=5),
    max_results: int = Query(default=10, ge=1, le=50)
):
    """
    🕸️ Belirli bir dökümanla ilişkili dökümanları bul.
    """
    try:
        premium = get_premium_features()
        
        # Ensure doc_id has correct prefix
        if not doc_id.startswith("doc_"):
            doc_id = f"doc_{doc_id}"
        
        related = premium.get_related_documents(doc_id)
        
        return {
            "success": True,
            "doc_id": doc_id,
            "related_count": len(related),
            "related": related[:max_results]
        }
        
    except Exception as e:
        logger.error(f"Related docs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/graph/path")
async def find_path(request: PathRequest):
    """
    🕸️ İki döküman arasındaki en kısa yolu bul.
    """
    try:
        premium = get_premium_features()
        
        # Ensure prefixes
        source = request.source_id if request.source_id.startswith("doc_") else f"doc_{request.source_id}"
        target = request.target_id if request.target_id.startswith("doc_") else f"doc_{request.target_id}"
        
        path = premium.knowledge_graph.find_path(source, target)
        
        if path:
            return {
                "success": True,
                "source": source,
                "target": target,
                "path": path,
                "length": len(path)
            }
        else:
            return {
                "success": False,
                "message": "No path found between documents",
                "source": source,
                "target": target
            }
        
    except Exception as e:
        logger.error(f"Path finding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats")
async def get_graph_stats():
    """
    🕸️ Knowledge graph istatistikleri.
    """
    try:
        premium = get_premium_features()
        stats = premium.knowledge_graph.get_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/central")
async def get_central_nodes(top_n: int = Query(default=10, ge=1, le=50)):
    """
    🕸️ En merkezi (en çok bağlantılı) node'ları döndür.
    """
    try:
        premium = get_premium_features()
        central = premium.knowledge_graph.get_central_nodes(top_n)
        
        return {
            "success": True,
            "central_nodes": central
        }
        
    except Exception as e:
        logger.error(f"Central nodes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/communities")
async def get_communities():
    """
    🕸️ Graph community'lerini (gruplarını) döndür.
    """
    try:
        premium = get_premium_features()
        communities = premium.knowledge_graph.get_communities()
        
        return {
            "success": True,
            "community_count": len(communities),
            "communities": [
                {
                    "id": i,
                    "size": len(c),
                    "members": c[:10]  # First 10 members
                }
                for i, c in enumerate(communities[:20])  # Top 20 communities
            ]
        }
        
    except Exception as e:
        logger.error(f"Communities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SUMMARY ENDPOINT
# =============================================================================

@router.get("/features")
async def list_features():
    """
    📋 Tüm premium özellikleri listele.
    """
    return {
        "success": True,
        "features": [
            {
                "id": "auto_tagging",
                "name": "🏷️ Smart Auto-Tagging",
                "description": "AI-powered otomatik etiketleme ve kategorizasyon",
                "endpoints": ["/premium/tag", "/premium/tag/batch"]
            },
            {
                "id": "analytics",
                "name": "📊 Real-time Analytics",
                "description": "Canlı metrikler ve dashboard",
                "endpoints": ["/premium/dashboard", "/premium/metrics", "/premium/event"]
            },
            {
                "id": "reranking",
                "name": "🔄 Semantic Reranking",
                "description": "Arama sonuçlarını akıllıca yeniden sıralama",
                "endpoints": ["/premium/rerank", "/premium/search/enhanced"]
            },
            {
                "id": "knowledge_graph",
                "name": "🕸️ Knowledge Graph",
                "description": "Dökümanlar arası ilişki haritası",
                "endpoints": [
                    "/premium/graph",
                    "/premium/graph/build",
                    "/premium/graph/related/{doc_id}",
                    "/premium/graph/path",
                    "/premium/graph/stats",
                    "/premium/graph/central",
                    "/premium/graph/communities"
                ]
            },
            {
                "id": "summarization",
                "name": "🧠 AI Summarization",
                "description": "Otomatik metin özetleme ve key point extraction",
                "endpoints": ["/premium/summarize", "/premium/summarize/multi", "/premium/headline"]
            },
            {
                "id": "fuzzy_search",
                "name": "🔍 Fuzzy Search",
                "description": "Bulanık arama ve yazım düzeltme",
                "endpoints": ["/premium/fuzzy/search", "/premium/fuzzy/correct", "/premium/fuzzy/didyoumean"]
            },
            {
                "id": "trend_analysis",
                "name": "📈 Trend Analysis",
                "description": "Trend analizi ve içgörüler",
                "endpoints": ["/premium/trends/analyze", "/premium/trends/insights", "/premium/trends/compare"]
            },
            {
                "id": "query_suggestions",
                "name": "🎯 Query Suggestions",
                "description": "Akıllı sorgu önerileri ve autocomplete",
                "endpoints": ["/premium/suggest", "/premium/suggest/popular", "/premium/suggest/record"]
            }
        ],
        "version": "2.0.0"
    }


# =============================================================================
# 5. AI SUMMARIZATION ENDPOINTS
# =============================================================================

class SummarizeRequest(BaseModel):
    """Özetleme isteği."""
    text: str = Field(..., min_length=50, max_length=100000)
    format: str = Field(default="paragraph", pattern="^(paragraph|bullets|tldr)$")
    max_sentences: int = Field(default=5, ge=1, le=20)


class MultiSummarizeRequest(BaseModel):
    """Çoklu özetleme isteği."""
    texts: List[str] = Field(..., min_length=1, max_length=10)
    max_sentences: int = Field(default=10, ge=1, le=30)


@router.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    """
    🧠 Metni özetle.
    
    Formats:
    - paragraph: Paragraf formatında özet
    - bullets: Madde işaretli liste
    - tldr: Çok kısa özet
    """
    try:
        premium = get_premium_features()
        
        result = premium.summarizer.summarize(
            request.text,
            max_sentences=request.max_sentences,
            format=request.format
        )
        
        premium.track_event("summarize", {
            "format": request.format,
            "original_length": len(request.text),
            "compression_ratio": result.get("compression_ratio")
        })
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize/multi")
async def summarize_multiple(request: MultiSummarizeRequest):
    """
    🧠 Birden fazla metni özetle (multi-document summarization).
    """
    try:
        premium = get_premium_features()
        
        result = premium.summarizer.summarize_multiple(
            request.texts,
            max_sentences=request.max_sentences
        )
        
        premium.track_event("summarize_multi", {"doc_count": len(request.texts)})
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Multi-summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/headline")
async def generate_headline(
    text: str = Body(..., min_length=50),
    max_length: int = Body(default=80, ge=20, le=200)
):
    """
    🧠 Metinden başlık oluştur.
    """
    try:
        premium = get_premium_features()
        headline = premium.summarizer.generate_headline(text, max_length)
        
        return {
            "success": True,
            "headline": headline,
            "original_length": len(text)
        }
        
    except Exception as e:
        logger.error(f"Headline generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 6. FUZZY SEARCH ENDPOINTS
# =============================================================================

class FuzzySearchRequest(BaseModel):
    """Fuzzy search isteği."""
    query: str = Field(..., min_length=1, max_length=500)
    candidates: Optional[List[str]] = None
    top_n: int = Field(default=5, ge=1, le=20)


class SpellCheckRequest(BaseModel):
    """Yazım kontrolü isteği."""
    text: str = Field(..., min_length=1, max_length=5000)


@router.post("/fuzzy/search")
async def fuzzy_search(request: FuzzySearchRequest):
    """
    🔍 Fuzzy search - benzer kelimeleri bul.
    """
    try:
        premium = get_premium_features()
        
        results = premium.fuzzy_search.find_similar(
            request.query,
            request.candidates,
            request.top_n
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": [
                {"word": word, "similarity": round(score, 3)}
                for word, score in results
            ]
        }
        
    except Exception as e:
        logger.error(f"Fuzzy search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fuzzy/correct")
async def correct_spelling(request: SpellCheckRequest):
    """
    🔍 Yazım düzeltme.
    """
    try:
        premium = get_premium_features()
        result = premium.correct_spelling(request.text)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Spell check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fuzzy/didyoumean")
async def did_you_mean(query: str = Query(..., min_length=2)):
    """
    🔍 'Bunu mu demek istediniz?' önerisi.
    """
    try:
        premium = get_premium_features()
        suggestion = premium.did_you_mean(query)
        
        return {
            "success": True,
            "original": query,
            "suggestion": suggestion,
            "has_suggestion": suggestion is not None
        }
        
    except Exception as e:
        logger.error(f"Did you mean error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fuzzy/vocabulary")
async def add_to_vocabulary(words: List[str] = Body(...)):
    """
    🔍 Kelime haznesine kelime ekle.
    """
    try:
        premium = get_premium_features()
        premium.fuzzy_search.add_words(words)
        
        return {
            "success": True,
            "added_count": len(words)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 7. TREND ANALYSIS ENDPOINTS
# =============================================================================

class TrendMetricRequest(BaseModel):
    """Trend metrik kaydı."""
    metric_name: str = Field(..., min_length=1, max_length=100)
    value: float


@router.post("/trends/record")
async def record_trend_metric(request: TrendMetricRequest):
    """
    📈 Trend için metrik kaydet.
    """
    try:
        premium = get_premium_features()
        premium.record_trend_metric(request.metric_name, request.value)
        
        return {
            "success": True,
            "metric": request.metric_name,
            "value": request.value
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/analyze/{metric_name}")
async def analyze_trend(metric_name: str):
    """
    📈 Belirli bir metriğin trend analizini yap.
    """
    try:
        premium = get_premium_features()
        result = premium.analyze_trend(metric_name)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Trend analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/insights")
async def get_trend_insights():
    """
    📈 Tüm trend içgörülerini al.
    """
    try:
        premium = get_premium_features()
        insights = premium.get_trend_insights()
        
        return {
            "success": True,
            **insights
        }
        
    except Exception as e:
        logger.error(f"Trend insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/compare/{metric_name}")
async def compare_trends(
    metric_name: str,
    period1_days: int = Query(default=7, ge=1, le=30),
    period2_days: int = Query(default=7, ge=1, le=30)
):
    """
    📈 İki dönemi karşılaştır.
    """
    try:
        premium = get_premium_features()
        result = premium.trend_analyzer.compare_periods(
            metric_name, period1_days, period2_days
        )
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Trend comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 8. QUERY SUGGESTIONS ENDPOINTS
# =============================================================================

class RecordQueryRequest(BaseModel):
    """Sorgu kayıt isteği."""
    query: str = Field(..., min_length=1, max_length=500)
    success: bool = Field(default=True)
    related_queries: Optional[List[str]] = None


@router.get("/suggest")
async def get_suggestions(
    q: str = Query(..., min_length=1, max_length=500, alias="q")
):
    """
    🎯 Sorgu önerileri al.
    
    Autocomplete, trending ve ilişkili sorgular.
    """
    try:
        premium = get_premium_features()
        suggestions = premium.suggest_queries(q)
        
        return {
            "success": True,
            "query": q,
            **suggestions
        }
        
    except Exception as e:
        logger.error(f"Suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest/record")
async def record_query(request: RecordQueryRequest):
    """
    🎯 Sorgu kaydet (öneri sistemi için).
    """
    try:
        premium = get_premium_features()
        premium.query_suggester.record_query(
            request.query,
            request.success,
            request.related_queries
        )
        
        return {
            "success": True,
            "query": request.query,
            "recorded": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest/popular")
async def get_popular_queries(limit: int = Query(default=10, ge=1, le=50)):
    """
    🎯 En popüler sorguları getir.
    """
    try:
        premium = get_premium_features()
        popular = premium.get_popular_queries(limit)
        
        return {
            "success": True,
            "popular_queries": popular
        }
        
    except Exception as e:
        logger.error(f"Popular queries error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest/stats")
async def get_suggestion_stats():
    """
    🎯 Sorgu öneri istatistikleri.
    """
    try:
        premium = get_premium_features()
        stats = premium.query_suggester.get_stats()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 9. DOCUMENT COMPARISON & DIFF ENDPOINTS
# =============================================================================

class DiffRequest(BaseModel):
    """Diff isteği."""
    text1: str = Field(..., min_length=1, max_length=500000)
    text2: str = Field(..., min_length=1, max_length=500000)
    label1: str = Field(default="Original")
    label2: str = Field(default="Modified")


class VersionDiffRequest(BaseModel):
    """Version diff isteği."""
    versions: List[Dict[str, Any]] = Field(
        ..., 
        min_length=2,
        description="List of {'version': str, 'content': str, 'timestamp': str}"
    )


@router.post("/compare/lines")
async def compare_lines(request: DiffRequest):
    """
    📝 Satır bazlı diff.
    
    İki döküman arasındaki satır farklarını tespit eder.
    """
    try:
        premium = get_premium_features()
        premium.track_event("document_compare", {"type": "lines"})
        
        result = premium.document_comparator.line_diff(
            request.text1,
            request.text2,
            request.label1,
            request.label2
        )
        
        return {
            "success": True,
            "type": "line_diff",
            **result
        }
        
    except Exception as e:
        logger.error(f"Line diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/words")
async def compare_words(request: DiffRequest):
    """
    📝 Kelime bazlı diff.
    
    Daha granüler karşılaştırma.
    """
    try:
        premium = get_premium_features()
        premium.track_event("document_compare", {"type": "words"})
        
        result = premium.document_comparator.word_diff(
            request.text1,
            request.text2
        )
        
        return {
            "success": True,
            "type": "word_diff",
            **result
        }
        
    except Exception as e:
        logger.error(f"Word diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/semantic")
async def compare_semantic(request: DiffRequest):
    """
    📝 Anlam bazlı diff.
    
    Cümle seviyesinde semantik karşılaştırma.
    """
    try:
        premium = get_premium_features()
        premium.track_event("document_compare", {"type": "semantic"})
        
        result = premium.document_comparator.semantic_diff(
            request.text1,
            request.text2
        )
        
        return {
            "success": True,
            "type": "semantic_diff",
            **result
        }
        
    except Exception as e:
        logger.error(f"Semantic diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/versions")
async def compare_versions(request: VersionDiffRequest):
    """
    📝 Birden fazla versiyon karşılaştırma.
    
    Versiyon zinciri üzerinde diff analizi.
    """
    try:
        premium = get_premium_features()
        premium.track_event("document_compare", {"type": "versions", "count": len(request.versions)})
        
        result = premium.document_comparator.version_diff(request.versions)
        
        return {
            "success": True,
            "type": "version_diff",
            **result
        }
        
    except Exception as e:
        logger.error(f"Version diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/side-by-side")
async def compare_side_by_side(request: DiffRequest):
    """
    📝 Yan yana görselleştirme.
    
    HTML ve JSON formatında side-by-side diff.
    """
    try:
        premium = get_premium_features()
        premium.track_event("document_compare", {"type": "side_by_side"})
        
        result = premium.document_comparator.side_by_side(
            request.text1,
            request.text2,
            request.label1,
            request.label2
        )
        
        return {
            "success": True,
            "type": "side_by_side",
            **result
        }
        
    except Exception as e:
        logger.error(f"Side-by-side diff error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/similarity")
async def compare_similarity(request: DiffRequest):
    """
    📝 Benzerlik skoru hesapla.
    
    Çoklu benzerlik metrikleri.
    """
    try:
        premium = get_premium_features()
        premium.track_event("document_compare", {"type": "similarity"})
        
        result = premium.document_comparator.similarity_score(
            request.text1,
            request.text2
        )
        
        return {
            "success": True,
            "type": "similarity",
            **result
        }
        
    except Exception as e:
        logger.error(f"Similarity score error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 10. CONTENT ENHANCEMENT ENDPOINTS
# =============================================================================

class EnhanceRequest(BaseModel):
    """İçerik zenginleştirme isteği."""
    content: str = Field(..., min_length=1, max_length=500000)


class CodeDetectRequest(BaseModel):
    """Kod dili tespit isteği."""
    code: str = Field(..., min_length=1, max_length=100000)


@router.post("/enhance")
async def enhance_content(request: EnhanceRequest):
    """
    🎨 İçerik zenginleştirme.
    
    Tüm enhancement özelliklerini uygular:
    - Markdown düzeltme
    - Kod tespiti
    - Tablo çıkarma
    - Link zenginleştirme
    - Image metadata
    """
    try:
        premium = get_premium_features()
        premium.track_event("content_enhance", {"content_length": len(request.content)})
        
        result = premium.content_enhancer.enhance_content(request.content)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Content enhancement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/markdown")
async def fix_markdown(request: EnhanceRequest):
    """
    🎨 Markdown format düzeltme.
    """
    try:
        premium = get_premium_features()
        
        result = premium.content_enhancer.fix_markdown(request.content)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Markdown fix error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/detect-code")
async def detect_code_language(request: CodeDetectRequest):
    """
    🎨 Kod dili tespit et.
    
    Python, JavaScript, TypeScript, HTML, CSS, SQL, vb.
    """
    try:
        premium = get_premium_features()
        
        result = premium.content_enhancer.detect_code_language(request.code)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Code detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/tables")
async def extract_tables(request: EnhanceRequest):
    """
    🎨 Metinden tablo çıkar.
    
    Markdown, ASCII ve TSV tabloları destekler.
    """
    try:
        premium = get_premium_features()
        
        result = premium.content_enhancer.extract_tables(request.content)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Table extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/links")
async def extract_links(request: EnhanceRequest):
    """
    🎨 Link'leri çıkar ve zenginleştir.
    
    URL, email, domain bilgileri.
    """
    try:
        premium = get_premium_features()
        
        result = premium.content_enhancer.extract_links(request.content)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Link extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/images")
async def extract_images(request: EnhanceRequest):
    """
    🎨 Image URL'lerini tespit et.
    
    Format, domain ve metadata bilgileri.
    """
    try:
        premium = get_premium_features()
        
        result = premium.content_enhancer.extract_images(request.content)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Image extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/format")
async def auto_format(request: EnhanceRequest):
    """
    🎨 Otomatik format düzeltme.
    
    Line endings, whitespace, blank lines.
    """
    try:
        premium = get_premium_features()
        
        result = premium.content_enhancer.auto_format(request.content)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        logger.error(f"Auto format error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
