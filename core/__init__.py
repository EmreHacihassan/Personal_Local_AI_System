# Enterprise AI Assistant - Core Module v2.0
# Endüstri Standartlarında Kurumsal AI Çözümü
# 12 İleri Düzey Teknoloji Entegrasyonu

from .config import settings
from .llm_manager import LLMManager
from .embedding import EmbeddingManager
from .vector_store import VectorStore
from .session_manager import SessionManager, session_manager
from .logger import get_logger, logger, log_info, log_error, log_warning
from .utils import (
    sanitize_filename,
    generate_hash,
    truncate_text,
    format_bytes,
    clean_text,
    timestamp_now,
)
from .analytics import AnalyticsManager, analytics
from .cache import CacheManager, cache_manager, cached
from .prompts import PromptManager, prompt_manager, PromptCategory
from .export import ExportManager, ImportManager, export_manager, import_manager
from .rate_limiter import RateLimiter, rate_limiter, rate_limit
from .health import HealthChecker, health_checker, get_health_report
from .document_processor import DocumentProcessor, document_processor
from .memory import MemoryManager, memory_manager, LongTermMemory
from .workflow import Workflow, WorkflowBuilder, WorkflowState, rag_workflow, agent_workflow
from .guardrails import Guardrails, guardrails, InputGuard, OutputGuard, GuardLevel
from .task_queue import TaskQueue, task_queue, Task, TaskStatus, TaskPriority, task_registry
from .plugins import PluginManager, plugin_manager, PluginInterface, HookManager, HookPriority
from .streaming import StreamManager, stream_manager, StreamingResponse, StreamEvent, StreamEventType
from .tracing import (
    Tracer, global_tracer, Span, SpanKind, SpanStatus,
    MetricsRegistry, metrics_registry, Counter, Gauge, Histogram,
    trace, timed, request_counter, request_duration, llm_tokens
)

# Conversation Chain
from .conversation import (
    Message,
    MessageRole,
    ConversationTurn,
    Conversation,
    ConversationStore,
    ConversationChain,
    conversation_store,
)

# Semantic Router
from .router import (
    Route,
    RouteMatch,
    RouteType,
    RouterStrategy,
    KeywordRouter,
    SemanticRouter,
    HybridRouter,
    SemanticRouterManager,
    semantic_router,
)

# ============ NEW ENTERPRISE MODULES v2.0 ============

# 1. MCP Protocol (Model Context Protocol)
try:
    from .mcp_server import MCPServer, MCPResource, MCPTool, MCPPrompt
    from .mcp_providers import CoreToolProvider, RAGToolProvider, SystemPromptProvider
except ImportError:
    MCPServer = None

# 2. Langfuse Observability
try:
    from .langfuse_observability import ObservabilityManager, traced, spanned
except ImportError:
    ObservabilityManager = None
    traced = lambda *a, **kw: lambda f: f
    spanned = traced

# 3. Instructor Structured Output
try:
    from .instructor_structured import (
        StructuredLLM, ConversationIntent, RAGResponse, 
        Summary, ChainOfThought
    )
except ImportError:
    StructuredLLM = None

# 4. LangGraph Agent Orchestration
try:
    from .langgraph_orchestration import (
        StateGraph, CompiledGraph, AgentState,
        create_rag_graph, create_conversation_graph
    )
except ImportError:
    StateGraph = None

# 5. CRAG Self-Correcting RAG
try:
    from .crag_system import CRAGPipeline, RelevanceGrader, QueryTransformer
except ImportError:
    CRAGPipeline = None

# 6. MemGPT Tiered Memory
try:
    from .memgpt_memory import (
        TieredMemoryManager, MemoryEnabledAgent,
        CoreMemory, WorkingMemory, ArchivalMemory
    )
except ImportError:
    TieredMemoryManager = None

# 7. Multi-Agent Debate
try:
    from .multi_agent_debate import (
        DebateOrchestrator, DebateAgent, JudgeAgent,
        multi_agent_debate, AgentRole, DebatePhase
    )
except ImportError:
    DebateOrchestrator = None

# 8. MoE Query Router
try:
    from .moe_router import (
        MoERouter, AdaptiveMoERouter, QueryAnalyzer,
        ExpertType, RoutingStrategy
    )
except ImportError:
    MoERouter = None

# 9. Graph RAG
try:
    from .graph_rag import (
        GraphRAGPipeline, create_graph_rag,
        Entity, Relationship, EntityType, RelationType
    )
except ImportError:
    GraphRAGPipeline = None

# 10. RAGAS Evaluation
try:
    from .ragas_evaluation import (
        RAGASEvaluator, quick_evaluate,
        MetricType, EvaluationSample, EvaluationResult
    )
except ImportError:
    RAGASEvaluator = None

# 11. Advanced Guardrails
try:
    from .advanced_guardrails import (
        GuardrailOrchestrator, create_default_guardrails,
        PIIDetectionGuardrail, JailbreakDetectionGuardrail,
        safe_generate
    )
except ImportError:
    GuardrailOrchestrator = None

# 12. Voice/Multimodal
try:
    from .voice_multimodal import (
        MultimodalPipeline, create_multimodal_pipeline,
        WhisperLocalSTT, EdgeTTS, LLaVAVision
    )
except ImportError:
    MultimodalPipeline = None

# Enterprise Orchestrator
try:
    from .orchestrator import (
        EnterpriseAIOrchestrator, create_orchestrator,
        SystemConfig, ProcessingResult
    )
except ImportError:
    EnterpriseAIOrchestrator = None

__all__ = [
    # Config
    "settings",
    # Managers
    "LLMManager",
    "EmbeddingManager", 
    "VectorStore",
    "SessionManager",
    "session_manager",
    # Logging
    "get_logger",
    "logger",
    "log_info",
    "log_error",
    "log_warning",
    # Utils
    "sanitize_filename",
    "generate_hash",
    "truncate_text",
    "format_bytes",
    "clean_text",
    "timestamp_now",
    # Analytics
    "AnalyticsManager",
    "analytics",
    # Cache
    "CacheManager",
    "cache_manager",
    "cached",
    # Prompts
    "PromptManager",
    "prompt_manager",
    "PromptCategory",
    # Export/Import
    "ExportManager",
    "ImportManager",
    "export_manager",
    "import_manager",
    # Rate Limiting
    "RateLimiter",
    "rate_limiter",
    "rate_limit",
    # Health
    "HealthChecker",
    "health_checker",
    "get_health_report",
    # Document Processing
    "DocumentProcessor",
    "document_processor",
    # Memory
    "MemoryManager",
    "memory_manager",
    "LongTermMemory",
    # Workflow
    "Workflow",
    "WorkflowBuilder",
    "WorkflowState",
    "rag_workflow",
    "agent_workflow",
    # Guardrails
    "Guardrails",
    "guardrails",
    "InputGuard",
    "OutputGuard",
    "GuardLevel",
    # Task Queue
    "TaskQueue",
    "task_queue",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "task_registry",
    # Plugins
    "PluginManager",
    "plugin_manager",
    "PluginInterface",
    "HookManager",
    "HookPriority",
    # Streaming
    "StreamManager",
    "stream_manager",
    "StreamingResponse",
    "StreamEvent",
    "StreamEventType",
    # Tracing & Observability
    "Tracer",
    "global_tracer",
    "Span",
    "SpanKind",
    "SpanStatus",
    "MetricsRegistry",
    "metrics_registry",
    "Counter",
    "Gauge",
    "Histogram",
    "trace",
    "timed",
    "request_counter",
    "request_duration",
    "llm_tokens",
    # Conversation Chain
    "Message",
    "MessageRole",
    "ConversationTurn",
    "Conversation",
    "ConversationStore",
    "ConversationChain",
    "conversation_store",
    # Semantic Router
    "Route",
    "RouteMatch",
    "RouteType",
    "RouterStrategy",
    "KeywordRouter",
    "SemanticRouter",
    "HybridRouter",
    "SemanticRouterManager",
    "semantic_router",
    
    # ============ NEW v2.0 EXPORTS ============
    
    # 1. MCP Protocol
    "MCPServer",
    "MCPResource",
    "MCPTool",
    "MCPPrompt",
    "CoreToolProvider",
    "RAGToolProvider",
    "SystemPromptProvider",
    
    # 2. Langfuse Observability
    "ObservabilityManager",
    "traced",
    "spanned",
    
    # 3. Instructor Structured Output
    "StructuredLLM",
    "ConversationIntent",
    "RAGResponse",
    "Summary",
    "ChainOfThought",
    
    # 4. LangGraph Orchestration
    "StateGraph",
    "CompiledGraph",
    "AgentState",
    "create_rag_graph",
    "create_conversation_graph",
    
    # 5. CRAG
    "CRAGPipeline",
    "RelevanceGrader",
    "QueryTransformer",
    
    # 6. MemGPT Memory
    "TieredMemoryManager",
    "MemoryEnabledAgent",
    "CoreMemory",
    "WorkingMemory",
    "ArchivalMemory",
    
    # 7. Multi-Agent Debate
    "DebateOrchestrator",
    "DebateAgent",
    "JudgeAgent",
    "multi_agent_debate",
    "AgentRole",
    "DebatePhase",
    
    # 8. MoE Router
    "MoERouter",
    "AdaptiveMoERouter",
    "QueryAnalyzer",
    "ExpertType",
    "RoutingStrategy",
    
    # 9. Graph RAG
    "GraphRAGPipeline",
    "create_graph_rag",
    "Entity",
    "Relationship",
    "EntityType",
    "RelationType",
    
    # 10. RAGAS Evaluation
    "RAGASEvaluator",
    "quick_evaluate",
    "MetricType",
    "EvaluationSample",
    "EvaluationResult",
    
    # 11. Advanced Guardrails
    "GuardrailOrchestrator",
    "create_default_guardrails",
    "PIIDetectionGuardrail",
    "JailbreakDetectionGuardrail",
    "safe_generate",
    
    # 12. Voice/Multimodal
    "MultimodalPipeline",
    "create_multimodal_pipeline",
    "WhisperLocalSTT",
    "EdgeTTS",
    "LLaVAVision",
    
    # Enterprise Orchestrator
    "EnterpriseAIOrchestrator",
    "create_orchestrator",
    "SystemConfig",
    "ProcessingResult",
]
