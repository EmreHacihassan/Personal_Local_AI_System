"""
🚀 AgenticManagingSystem - Enterprise AI Platform
=================================================

Tüm ileri düzey teknolojileri birleştiren ana orkestrasyon katmanı.

Integrated Technologies:
1. MCP Server - Model Context Protocol
2. Langfuse - LLM Observability
3. Instructor - Structured Output
4. LangGraph - Agent Orchestration
5. CRAG - Self-Correcting RAG
6. MemGPT - Tiered Memory
7. Multi-Agent Debate - Consensus
8. MoE Router - Query Routing
9. Graph RAG - Knowledge Graph
10. RAGAS - Evaluation
11. Guardrails - Safety
12. Multimodal - Voice/Vision
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)


# ============ IMPORTS ============

# Core modules
try:
    from core.mcp_server import MCPServer
    from core.mcp_providers import CoreToolProvider, RAGToolProvider, SystemPromptProvider
except ImportError:
    MCPServer = None
    logger.warning("MCP modules not available")

try:
    from core.langfuse_observability import ObservabilityManager, traced
except ImportError:
    ObservabilityManager = None
    traced = lambda *a, **kw: lambda f: f
    logger.warning("Langfuse module not available")

try:
    from core.instructor_structured import StructuredLLM, ConversationIntent, RAGResponse
except ImportError:
    StructuredLLM = None
    logger.warning("Instructor module not available")

try:
    from core.langgraph_orchestration import StateGraph, AgentState, create_rag_graph
except ImportError:
    StateGraph = None
    create_rag_graph = None
    logger.warning("LangGraph module not available")

try:
    from core.crag_system import CRAGPipeline
except ImportError:
    CRAGPipeline = None
    logger.warning("CRAG module not available")

try:
    from core.memgpt_memory import TieredMemoryManager, MemoryEnabledAgent
except ImportError:
    TieredMemoryManager = None
    logger.warning("MemGPT module not available")

try:
    from core.multi_agent_debate import DebateOrchestrator, multi_agent_debate
except ImportError:
    DebateOrchestrator = None
    logger.warning("Multi-Agent Debate module not available")

try:
    from core.moe_router import MoERouter, AdaptiveMoERouter, RoutingStrategy
except ImportError:
    MoERouter = None
    logger.warning("MoE Router module not available")

try:
    from core.graph_rag import GraphRAGPipeline, create_graph_rag
except ImportError:
    GraphRAGPipeline = None
    create_graph_rag = None
    logger.warning("Graph RAG module not available")

try:
    from core.ragas_evaluation import RAGASEvaluator, quick_evaluate
except ImportError:
    RAGASEvaluator = None
    logger.warning("RAGAS module not available")

try:
    from core.advanced_guardrails import GuardrailOrchestrator, create_default_guardrails, safe_generate
except ImportError:
    GuardrailOrchestrator = None
    create_default_guardrails = None
    logger.warning("Guardrails module not available")

try:
    from core.voice_multimodal import MultimodalPipeline, create_multimodal_pipeline
except ImportError:
    MultimodalPipeline = None
    logger.warning("Multimodal module not available")


# ============ DATA MODELS ============

class SystemConfig(BaseModel):
    """System-wide configuration"""
    # LLM Settings
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    llm_base_url: str = "http://localhost:11434"
    
    # RAG Settings
    vector_store_path: str = "./data/chroma_db"
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # MCP Settings
    mcp_enabled: bool = True
    mcp_host: str = "localhost"
    mcp_port: int = 8000
    
    # Observability
    langfuse_enabled: bool = True
    langfuse_host: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    
    # Memory
    memory_enabled: bool = True
    memory_db_path: str = "./data/memory.db"
    
    # Guardrails
    guardrails_enabled: bool = True
    
    # Multimodal
    multimodal_enabled: bool = False
    use_local_models: bool = True
    
    # Graph RAG
    graph_rag_enabled: bool = False
    neo4j_uri: Optional[str] = None
    neo4j_user: str = "neo4j"
    neo4j_password: Optional[str] = None


class ProcessingResult(BaseModel):
    """Result from processing a request"""
    response: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float = 0
    guardrail_results: List[Dict] = Field(default_factory=list)
    routing_info: Optional[Dict] = None
    evaluation_score: Optional[float] = None


# ============ ENTERPRISE ORCHESTRATOR ============

class EnterpriseAIOrchestrator:
    """
    Enterprise-grade AI orchestrator combining all technologies.
    
    This is the main entry point for the system.
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        
        # Initialize components
        self._init_observability()
        self._init_guardrails()
        self._init_memory()
        self._init_router()
        self._init_rag()
        self._init_multimodal()
        self._init_mcp()
        
        logger.info("EnterpriseAIOrchestrator initialized")
    
    def _init_observability(self):
        """Initialize observability"""
        if self.config.langfuse_enabled and ObservabilityManager:
            try:
                self.observability = ObservabilityManager(
                    host=self.config.langfuse_host,
                    public_key=self.config.langfuse_public_key,
                    secret_key=self.config.langfuse_secret_key
                )
            except Exception as e:
                logger.warning(f"Observability init failed: {e}")
                self.observability = None
        else:
            self.observability = None
    
    def _init_guardrails(self):
        """Initialize guardrails"""
        if self.config.guardrails_enabled and create_default_guardrails:
            self.guardrails = create_default_guardrails()
        else:
            self.guardrails = None
    
    def _init_memory(self):
        """Initialize memory system"""
        if self.config.memory_enabled and TieredMemoryManager:
            try:
                self.memory = TieredMemoryManager(
                    db_path=self.config.memory_db_path
                )
            except Exception as e:
                logger.warning(f"Memory init failed: {e}")
                self.memory = None
        else:
            self.memory = None
    
    def _init_router(self):
        """Initialize query router"""
        if MoERouter:
            self.router = AdaptiveMoERouter(
                strategy=RoutingStrategy.BALANCED
            )
        else:
            self.router = None
    
    def _init_rag(self):
        """Initialize RAG systems"""
        # Standard CRAG
        if CRAGPipeline:
            try:
                self.crag = CRAGPipeline()
            except Exception as e:
                logger.warning(f"CRAG init failed: {e}")
                self.crag = None
        else:
            self.crag = None
        
        # Graph RAG
        if self.config.graph_rag_enabled and create_graph_rag:
            try:
                self.graph_rag = create_graph_rag(
                    use_neo4j=bool(self.config.neo4j_uri),
                    neo4j_uri=self.config.neo4j_uri or "",
                    neo4j_user=self.config.neo4j_user,
                    neo4j_password=self.config.neo4j_password or ""
                )
            except Exception as e:
                logger.warning(f"Graph RAG init failed: {e}")
                self.graph_rag = None
        else:
            self.graph_rag = None
    
    def _init_multimodal(self):
        """Initialize multimodal pipeline"""
        if self.config.multimodal_enabled and create_multimodal_pipeline:
            try:
                self.multimodal = create_multimodal_pipeline(
                    use_local=self.config.use_local_models
                )
            except Exception as e:
                logger.warning(f"Multimodal init failed: {e}")
                self.multimodal = None
        else:
            self.multimodal = None
    
    def _init_mcp(self):
        """Initialize MCP server"""
        if self.config.mcp_enabled and MCPServer:
            try:
                self.mcp_server = MCPServer(
                    name="AgenticManagingSystem",
                    version="2.0.0"
                )
            except Exception as e:
                logger.warning(f"MCP init failed: {e}")
                self.mcp_server = None
        else:
            self.mcp_server = None
    
    @traced(name="process_request")
    async def process(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        include_sources: bool = True,
        use_debate: bool = False,
        evaluate: bool = False
    ) -> ProcessingResult:
        """
        Process a user request through the full pipeline.
        
        Pipeline:
        1. Input guardrails
        2. Query routing
        3. Memory retrieval
        4. RAG retrieval
        5. Response generation
        6. Output guardrails
        7. Evaluation (optional)
        """
        import time
        start_time = time.time()
        
        metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        guardrail_results = []
        
        # 1. Input Guardrails
        safe_query = query
        if self.guardrails:
            allowed, results, safe_query = await self.guardrails.check_input(
                query, user_id=user_id, session_id=session_id
            )
            guardrail_results.extend([r.model_dump() for r in results])
            
            if not allowed:
                return ProcessingResult(
                    response="I cannot process that request.",
                    guardrail_results=guardrail_results,
                    processing_time_ms=(time.time() - start_time) * 1000
                )
        
        # 2. Query Routing
        routing_info = None
        if self.router:
            decision = self.router.route(safe_query)
            routing_info = {
                "expert": decision.selected_expert.value,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning
            }
            metadata["routing"] = routing_info
        
        # 3. Memory Retrieval
        memory_context = ""
        if self.memory and user_id:
            try:
                memories = await self.memory.search(safe_query, limit=3)
                if memories:
                    memory_context = "\n".join([
                        f"[Memory] {m.content}" for m in memories
                    ])
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")
        
        # 4. RAG Retrieval
        sources = []
        rag_context = ""
        
        if self.crag:
            try:
                crag_result = await self.crag.process(safe_query)
                rag_context = crag_result.final_context
                sources = [{"source": "crag", "chunks": len(crag_result.retrieved_documents)}]
            except Exception as e:
                logger.warning(f"CRAG retrieval failed: {e}")
        
        if self.graph_rag:
            try:
                graph_result = await self.graph_rag.retrieve(safe_query)
                rag_context += f"\n\n{graph_result.graph_context}"
                sources.append({
                    "source": "graph_rag",
                    "entities": graph_result.entities_found,
                    "relationships": graph_result.relationships_found
                })
            except Exception as e:
                logger.warning(f"Graph RAG retrieval failed: {e}")
        
        # 5. Response Generation
        combined_context = f"{memory_context}\n\n{rag_context}".strip()
        
        if use_debate and DebateOrchestrator:
            # Multi-agent debate for complex queries
            try:
                debate_result = await multi_agent_debate(
                    topic=safe_query,
                    context=combined_context
                )
                response = debate_result.final_answer
            except Exception as e:
                logger.warning(f"Debate failed: {e}")
                response = await self._generate_simple_response(safe_query, combined_context)
        else:
            response = await self._generate_simple_response(safe_query, combined_context)
        
        # 6. Output Guardrails
        if self.guardrails:
            allowed, results, response = await self.guardrails.check_output(
                safe_query, response, user_id=user_id
            )
            guardrail_results.extend([r.model_dump() for r in results])
            
            if not allowed:
                response = "I cannot provide that response."
        
        # 7. Evaluation (optional)
        eval_score = None
        if evaluate and quick_evaluate:
            try:
                eval_result = await quick_evaluate(
                    question=safe_query,
                    answer=response,
                    contexts=[rag_context] if rag_context else []
                )
                eval_score = eval_result.overall_score
                metadata["evaluation"] = eval_result.model_dump()
            except Exception as e:
                logger.warning(f"Evaluation failed: {e}")
        
        # Store in memory
        if self.memory and user_id:
            try:
                await self.memory.store(
                    content=f"Q: {safe_query}\nA: {response}",
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Memory store failed: {e}")
        
        processing_time = (time.time() - start_time) * 1000
        
        return ProcessingResult(
            response=response,
            sources=sources if include_sources else [],
            metadata=metadata,
            processing_time_ms=processing_time,
            guardrail_results=guardrail_results,
            routing_info=routing_info,
            evaluation_score=eval_score
        )
    
    async def _generate_simple_response(self, query: str, context: str) -> str:
        """Generate a simple LLM response"""
        from .llm_manager import llm_manager
        
        prompt = f"""Context:
{context}

Question: {query}

Provide a helpful, accurate answer based on the context."""
        
        try:
            # Use actual LLM client
            response = await llm_manager.generate_async(
                prompt=prompt,
                system_prompt="You are a helpful AI assistant that provides accurate answers based on the given context.",
                temperature=0.7,
                max_tokens=2048
            )
            return response
        except Exception as e:
            # Fallback if LLM fails
            from .logger import get_logger
            logger = get_logger("orchestrator")
            logger.warning(f"LLM generation failed, using fallback: {e}")
            return f"Based on the provided context, here is my response to: {query}"
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio to text"""
        if self.multimodal:
            return await self.multimodal.transcribe_audio(audio_data)
        raise RuntimeError("Multimodal pipeline not enabled")
    
    async def synthesize_speech(self, text: str) -> bytes:
        """Convert text to speech"""
        if self.multimodal:
            return await self.multimodal.synthesize_speech(text)
        raise RuntimeError("Multimodal pipeline not enabled")
    
    async def describe_image(self, image_data: bytes) -> str:
        """Describe an image"""
        if self.multimodal:
            return await self.multimodal.describe_image(image_data)
        raise RuntimeError("Multimodal pipeline not enabled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "components": {
                "observability": self.observability is not None,
                "guardrails": self.guardrails is not None,
                "memory": self.memory is not None,
                "router": self.router is not None,
                "crag": self.crag is not None,
                "graph_rag": self.graph_rag is not None,
                "multimodal": self.multimodal is not None,
                "mcp_server": self.mcp_server is not None
            },
            "config": self.config.model_dump()
        }


# ============ FACTORY FUNCTIONS ============

def create_orchestrator(
    enable_all: bool = False,
    **kwargs
) -> EnterpriseAIOrchestrator:
    """
    Create an orchestrator with custom configuration.
    
    Args:
        enable_all: Enable all features
        **kwargs: Additional config overrides
        
    Returns:
        Configured EnterpriseAIOrchestrator
    """
    config_dict = {}
    
    if enable_all:
        config_dict.update({
            "mcp_enabled": True,
            "langfuse_enabled": True,
            "memory_enabled": True,
            "guardrails_enabled": True,
            "multimodal_enabled": True,
            "graph_rag_enabled": True
        })
    
    config_dict.update(kwargs)
    config = SystemConfig(**config_dict)
    
    return EnterpriseAIOrchestrator(config)


# ============ EXPORTS ============

__all__ = [
    # Config
    "SystemConfig",
    # Result
    "ProcessingResult",
    # Main
    "EnterpriseAIOrchestrator",
    # Factory
    "create_orchestrator"
]
