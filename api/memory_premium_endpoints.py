"""
🧠 Premium Memory API Endpoints
================================

Enterprise-grade memory management endpoints.

Features:
- Long-term memory storage and retrieval
- MemGPT-style tiered memory
- User preference learning
- Fact/knowledge graph storage
- Memory decay and maintenance
- Session-based conversation memory
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["Memory"])


# ============================================================================
# MODELS
# ============================================================================

class StoreMemoryRequest(BaseModel):
    """Store memory request"""
    content: str = Field(..., description="Content to store")
    memory_type: str = Field("context", description="fact, preference, context, interaction")
    importance: float = Field(0.5, ge=0.0, le=1.0, description="Importance score")
    source: str = Field("api", description="Source of the memory")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RecallMemoryRequest(BaseModel):
    """Recall memory request"""
    query: Optional[str] = Field(None, description="Search query")
    memory_type: Optional[str] = Field(None, description="Filter by type")
    min_importance: float = Field(0.0, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=100)


class StorePreferenceRequest(BaseModel):
    """Store user preference request"""
    user_id: str
    key: str
    value: Any


class StoreFactRequest(BaseModel):
    """Store fact (triple) request"""
    subject: str
    predicate: str
    object: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source: Optional[str] = None


class QueryFactsRequest(BaseModel):
    """Query facts request"""
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None


class AddInteractionRequest(BaseModel):
    """Add conversation interaction request"""
    session_id: str
    user_message: str
    assistant_response: str
    auto_learn: bool = Field(True, description="Auto-learn from this interaction")


class GetContextRequest(BaseModel):
    """Get context for query request"""
    session_id: str
    query: str


class CoreMemoryUpdateRequest(BaseModel):
    """Update core memory request"""
    section: str = Field(..., description="persona, human, or custom section name")
    content: str


class SetLLMFunctionRequest(BaseModel):
    """Set LLM summarization function"""
    endpoint: str = Field(..., description="LLM API endpoint")
    model: str = Field("qwen2.5:7b", description="Model name")


# ============================================================================
# MEMORY INSTANCES
# ============================================================================

_memory_manager = None
_long_term_memory = None
_memgpt_system = None


def get_memory_manager():
    """Get or create memory manager"""
    global _memory_manager
    if _memory_manager is None:
        try:
            from core.memory import MemoryManager, start_memory_maintenance
            _memory_manager = MemoryManager()
            start_memory_maintenance(interval_hours=6)
            logger.info("🧠 Memory manager initialized with maintenance")
        except Exception as e:
            logger.warning(f"Failed to initialize memory manager: {e}")
    return _memory_manager


def get_long_term_memory():
    """Get or create long-term memory"""
    global _long_term_memory
    if _long_term_memory is None:
        try:
            from core.memory import LongTermMemory
            from core.config import settings
            _long_term_memory = LongTermMemory(db_path=settings.DATA_DIR / "memory.db")
            logger.info("💾 Long-term memory initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize long-term memory: {e}")
    return _long_term_memory


def get_memgpt_system():
    """Get or create MemGPT-style memory system"""
    global _memgpt_system
    if _memgpt_system is None:
        try:
            from core.memgpt_memory import CoreMemory
            _memgpt_system = {
                "core": CoreMemory(
                    persona="I am Enterprise AI Assistant, a helpful and knowledgeable AI.",
                    human="The user is interacting with an enterprise assistant."
                )
            }
            logger.info("🤖 MemGPT-style memory initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize MemGPT system: {e}")
    return _memgpt_system


# ============================================================================
# LONG-TERM MEMORY ENDPOINTS
# ============================================================================

@router.get("/status")
async def get_memory_status():
    """Get memory system status"""
    mm = get_memory_manager()
    ltm = get_long_term_memory()
    memgpt = get_memgpt_system()
    
    status = {
        "memory_manager": mm is not None,
        "long_term_memory": ltm is not None,
        "memgpt_system": memgpt is not None,
        "timestamp": datetime.now().isoformat()
    }
    
    if mm:
        status["active_sessions"] = len(mm.short_term)
        status["llm_enabled"] = mm._llm_fn is not None
    
    if ltm:
        try:
            stats = ltm.get_stats()
            status["long_term_stats"] = stats
        except:
            pass
    
    return status


@router.post("/store")
async def store_memory(request: StoreMemoryRequest):
    """
    Store information in long-term memory.
    
    Memory types:
    - fact: Factual information
    - preference: User preferences
    - context: Contextual information
    - interaction: Conversation memories
    """
    try:
        ltm = get_long_term_memory()
        if not ltm:
            raise HTTPException(status_code=503, detail="Long-term memory not available")
        
        memory_id = ltm.store(
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            source=request.source,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "type": request.memory_type,
            "importance": request.importance,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Store memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall")
async def recall_memories(request: RecallMemoryRequest):
    """
    Recall memories from long-term storage.
    
    Searches by query, type, and importance threshold.
    """
    try:
        ltm = get_long_term_memory()
        if not ltm:
            raise HTTPException(status_code=503, detail="Long-term memory not available")
        
        memories = ltm.recall(
            query=request.query,
            memory_type=request.memory_type,
            limit=request.limit,
            min_importance=request.min_importance
        )
        
        return {
            "success": True,
            "count": len(memories),
            "memories": [m.to_dict() for m in memories],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Recall memories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preference/store")
async def store_preference(request: StorePreferenceRequest):
    """Store user preference"""
    try:
        ltm = get_long_term_memory()
        if not ltm:
            raise HTTPException(status_code=503, detail="Long-term memory not available")
        
        ltm.store_preference(
            user_id=request.user_id,
            key=request.key,
            value=request.value
        )
        
        return {
            "success": True,
            "user_id": request.user_id,
            "key": request.key,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Store preference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preference/{user_id}/{key}")
async def get_preference(user_id: str, key: str, default: Optional[str] = None):
    """Get user preference"""
    try:
        ltm = get_long_term_memory()
        if not ltm:
            raise HTTPException(status_code=503, detail="Long-term memory not available")
        
        value = ltm.get_preference(user_id, key, default)
        
        return {
            "success": True,
            "user_id": user_id,
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get preference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fact/store")
async def store_fact(request: StoreFactRequest):
    """
    Store a fact as a triple (subject-predicate-object).
    
    Example: ("Python", "is", "programming language")
    """
    try:
        ltm = get_long_term_memory()
        if not ltm:
            raise HTTPException(status_code=503, detail="Long-term memory not available")
        
        fact_id = ltm.store_fact(
            subject=request.subject,
            predicate=request.predicate,
            obj=request.object,
            confidence=request.confidence,
            source=request.source
        )
        
        return {
            "success": True,
            "fact_id": fact_id,
            "triple": f"({request.subject}, {request.predicate}, {request.object})",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Store fact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fact/query")
async def query_facts(request: QueryFactsRequest):
    """Query stored facts"""
    try:
        ltm = get_long_term_memory()
        if not ltm:
            raise HTTPException(status_code=503, detail="Long-term memory not available")
        
        facts = ltm.query_facts(
            subject=request.subject,
            predicate=request.predicate,
            obj=request.object
        )
        
        return {
            "success": True,
            "count": len(facts),
            "facts": facts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Query facts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_memory_stats():
    """Get memory usage statistics"""
    try:
        ltm = get_long_term_memory()
        mm = get_memory_manager()
        
        stats = {}
        
        if ltm:
            stats["long_term"] = ltm.get_stats()
        
        if mm:
            stats["manager"] = mm.get_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance")
async def run_maintenance():
    """Run memory maintenance (decay, cleanup)"""
    try:
        mm = get_memory_manager()
        ltm = get_long_term_memory()
        
        results = {}
        
        if mm:
            results["manager"] = mm.run_maintenance()
        
        if ltm:
            ltm.decay_memories(days_threshold=30)
            results["decay_applied"] = True
        
        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Maintenance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SESSION MEMORY ENDPOINTS
# ============================================================================

@router.post("/session/interaction")
async def add_interaction(request: AddInteractionRequest):
    """Add conversation interaction to session memory"""
    try:
        mm = get_memory_manager()
        if not mm:
            raise HTTPException(status_code=503, detail="Memory manager not available")
        
        mm.add_interaction(
            session_id=request.session_id,
            user_message=request.user_message,
            assistant_response=request.assistant_response,
            auto_learn=request.auto_learn
        )
        
        return {
            "success": True,
            "session_id": request.session_id,
            "auto_learn": request.auto_learn,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Add interaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/context")
async def get_context_for_query(request: GetContextRequest):
    """Get relevant context for a query from session and long-term memory"""
    try:
        mm = get_memory_manager()
        if not mm:
            raise HTTPException(status_code=503, detail="Memory manager not available")
        
        context = mm.get_context_for_query(
            session_id=request.session_id,
            query=request.query
        )
        
        return {
            "success": True,
            "session_id": request.session_id,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up session memory"""
    try:
        mm = get_memory_manager()
        if not mm:
            raise HTTPException(status_code=503, detail="Memory manager not available")
        
        mm.cleanup_session(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Session cleaned up",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cleanup session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MEMGPT-STYLE MEMORY ENDPOINTS
# ============================================================================

@router.get("/core")
async def get_core_memory():
    """Get MemGPT-style core memory"""
    try:
        memgpt = get_memgpt_system()
        if not memgpt:
            raise HTTPException(status_code=503, detail="MemGPT system not available")
        
        core = memgpt.get("core")
        
        return {
            "success": True,
            "core_memory": {
                "persona": core.persona,
                "human": core.human,
                "system_facts": core.system_facts,
                "user_facts": core.user_facts,
                "custom_sections": core.custom_sections
            },
            "prompt_preview": core.to_prompt()[:500] + "...",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get core memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/core/update")
async def update_core_memory(request: CoreMemoryUpdateRequest):
    """Update MemGPT-style core memory section"""
    try:
        memgpt = get_memgpt_system()
        if not memgpt:
            raise HTTPException(status_code=503, detail="MemGPT system not available")
        
        core = memgpt.get("core")
        core.update_section(request.section, request.content)
        
        return {
            "success": True,
            "section": request.section,
            "updated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Update core memory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/core/fact")
async def add_core_fact(fact: str, fact_type: str = "system"):
    """Add fact to core memory"""
    try:
        memgpt = get_memgpt_system()
        if not memgpt:
            raise HTTPException(status_code=503, detail="MemGPT system not available")
        
        core = memgpt.get("core")
        
        if fact_type == "system":
            core.system_facts.append(fact)
        elif fact_type == "user":
            core.user_facts.append(fact)
        else:
            raise HTTPException(status_code=400, detail="fact_type must be 'system' or 'user'")
        
        return {
            "success": True,
            "fact": fact,
            "type": fact_type,
            "total_facts": len(core.system_facts) + len(core.user_facts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Add core fact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/set")
async def set_llm_function(request: SetLLMFunctionRequest):
    """Set LLM function for memory summarization"""
    try:
        mm = get_memory_manager()
        if not mm:
            raise HTTPException(status_code=503, detail="Memory manager not available")
        
        # Create LLM function
        async def llm_fn(prompt: str) -> str:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{request.endpoint}/api/generate",
                    json={"model": request.model, "prompt": prompt, "stream": False},
                    timeout=60.0
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
                return ""
        
        # We need sync function, so wrap it
        import asyncio
        def sync_llm_fn(prompt: str) -> str:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        return pool.submit(asyncio.run, llm_fn(prompt)).result()
                return asyncio.run(llm_fn(prompt))
            except:
                return ""
        
        mm.set_llm_function(sync_llm_fn)
        
        return {
            "success": True,
            "endpoint": request.endpoint,
            "model": request.model,
            "message": "LLM function set for memory summarization",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Set LLM function error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
