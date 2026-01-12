# Enterprise AI Assistant - Core Module v2.0
# Endüstri Standartlarında Kurumsal AI Çözümü
# 12 İleri Düzey Teknoloji Entegrasyonu
#
# LAZY LOADING: Modüller sadece ihtiyaç duyulduğunda yüklenir
# Bu, frontend başlatma süresini önemli ölçüde azaltır

from .config import settings
from .logger import get_logger, logger, log_info, log_error, log_warning
from .utils import (
    sanitize_filename,
    generate_hash,
    truncate_text,
    format_bytes,
    clean_text,
    timestamp_now,
)

# Lazy imports - sadece erişildiğinde yüklenir
def __getattr__(name):
    """Lazy loading for heavy modules."""
    
    # LLM Manager
    if name == "LLMManager":
        from .llm_manager import LLMManager
        return LLMManager
    if name == "llm_manager":
        from .llm_manager import llm_manager
        return llm_manager
    
    # Embedding Manager
    if name == "EmbeddingManager":
        from .embedding import EmbeddingManager
        return EmbeddingManager
    if name == "embedding_manager":
        from .embedding import embedding_manager
        return embedding_manager
    
    # Vector Store
    if name == "VectorStore":
        from .vector_store import VectorStore
        return VectorStore
    if name == "vector_store":
        from .vector_store import vector_store
        return vector_store
    
    # Session Manager
    if name in ("SessionManager", "session_manager"):
        from .session_manager import SessionManager, session_manager
        return session_manager if name == "session_manager" else SessionManager
    
    # Analytics
    if name in ("AnalyticsManager", "analytics"):
        from .analytics import AnalyticsManager, analytics
        return analytics if name == "analytics" else AnalyticsManager
    
    # Cache
    if name in ("CacheManager", "cache_manager", "cached"):
        from .cache import CacheManager, cache_manager, cached
        if name == "CacheManager":
            return CacheManager
        elif name == "cache_manager":
            return cache_manager
        return cached
    
    # Prompts
    if name in ("PromptManager", "prompt_manager", "PromptCategory"):
        from .prompts import PromptManager, prompt_manager, PromptCategory
        if name == "PromptManager":
            return PromptManager
        elif name == "prompt_manager":
            return prompt_manager
        return PromptCategory
    
    # Export/Import
    if name in ("ExportManager", "ImportManager", "export_manager", "import_manager"):
        from .export import ExportManager, ImportManager, export_manager, import_manager
        mapping = {
            "ExportManager": ExportManager,
            "ImportManager": ImportManager,
            "export_manager": export_manager,
            "import_manager": import_manager,
        }
        return mapping[name]
    
    # Rate Limiter
    if name in ("RateLimiter", "rate_limiter", "rate_limit"):
        from .rate_limiter import RateLimiter, rate_limiter, rate_limit
        mapping = {"RateLimiter": RateLimiter, "rate_limiter": rate_limiter, "rate_limit": rate_limit}
        return mapping[name]
    
    # Health
    if name in ("HealthChecker", "health_checker", "get_health_report"):
        from .health import HealthChecker, health_checker, get_health_report
        mapping = {"HealthChecker": HealthChecker, "health_checker": health_checker, "get_health_report": get_health_report}
        return mapping[name]
    
    # Document Processor
    if name in ("DocumentProcessor", "document_processor"):
        from .document_processor import DocumentProcessor, document_processor
        return document_processor if name == "document_processor" else DocumentProcessor
    
    # Memory
    if name in ("MemoryManager", "memory_manager", "LongTermMemory"):
        from .memory import MemoryManager, memory_manager, LongTermMemory
        mapping = {"MemoryManager": MemoryManager, "memory_manager": memory_manager, "LongTermMemory": LongTermMemory}
        return mapping[name]
    
    # Workflow
    if name in ("Workflow", "WorkflowBuilder", "WorkflowState", "rag_workflow", "agent_workflow"):
        from .workflow import Workflow, WorkflowBuilder, WorkflowState, rag_workflow, agent_workflow
        mapping = {
            "Workflow": Workflow, "WorkflowBuilder": WorkflowBuilder, 
            "WorkflowState": WorkflowState, "rag_workflow": rag_workflow, "agent_workflow": agent_workflow
        }
        return mapping[name]
    
    # Guardrails
    if name in ("Guardrails", "guardrails", "InputGuard", "OutputGuard", "GuardLevel"):
        from .guardrails import Guardrails, guardrails, InputGuard, OutputGuard, GuardLevel
        mapping = {
            "Guardrails": Guardrails, "guardrails": guardrails, 
            "InputGuard": InputGuard, "OutputGuard": OutputGuard, "GuardLevel": GuardLevel
        }
        return mapping[name]
    
    # Task Queue
    if name in ("TaskQueue", "task_queue", "Task", "TaskStatus", "TaskPriority", "task_registry"):
        from .task_queue import TaskQueue, task_queue, Task, TaskStatus, TaskPriority, task_registry
        mapping = {
            "TaskQueue": TaskQueue, "task_queue": task_queue, "Task": Task,
            "TaskStatus": TaskStatus, "TaskPriority": TaskPriority, "task_registry": task_registry
        }
        return mapping[name]
    
    # Plugins
    if name in ("PluginManager", "plugin_manager", "PluginInterface", "HookManager", "HookPriority"):
        from .plugins import PluginManager, plugin_manager, PluginInterface, HookManager, HookPriority
        mapping = {
            "PluginManager": PluginManager, "plugin_manager": plugin_manager,
            "PluginInterface": PluginInterface, "HookManager": HookManager, "HookPriority": HookPriority
        }
        return mapping[name]
    
    # Streaming
    if name in ("StreamManager", "stream_manager", "StreamingResponse", "StreamEvent", "StreamEventType"):
        from .streaming import StreamManager, stream_manager, StreamingResponse, StreamEvent, StreamEventType
        mapping = {
            "StreamManager": StreamManager, "stream_manager": stream_manager,
            "StreamingResponse": StreamingResponse, "StreamEvent": StreamEvent, "StreamEventType": StreamEventType
        }
        return mapping[name]
    
    # Tracing
    if name in ("Tracer", "global_tracer", "Span", "SpanKind", "SpanStatus", 
                "MetricsRegistry", "metrics_registry", "Counter", "Gauge", "Histogram",
                "trace", "timed", "request_counter", "request_duration", "llm_tokens"):
        from .tracing import (
            Tracer, global_tracer, Span, SpanKind, SpanStatus,
            MetricsRegistry, metrics_registry, Counter, Gauge, Histogram,
            trace, timed, request_counter, request_duration, llm_tokens
        )
        mapping = {
            "Tracer": Tracer, "global_tracer": global_tracer, "Span": Span,
            "SpanKind": SpanKind, "SpanStatus": SpanStatus,
            "MetricsRegistry": MetricsRegistry, "metrics_registry": metrics_registry,
            "Counter": Counter, "Gauge": Gauge, "Histogram": Histogram,
            "trace": trace, "timed": timed, "request_counter": request_counter,
            "request_duration": request_duration, "llm_tokens": llm_tokens
        }
        return mapping[name]
    
    # Conversation Chain
    if name in ("Message", "MessageRole", "ConversationTurn", "Conversation", 
                "ConversationStore", "ConversationChain", "conversation_store"):
        from .conversation import (
            Message, MessageRole, ConversationTurn, Conversation,
            ConversationStore, ConversationChain, conversation_store
        )
        mapping = {
            "Message": Message, "MessageRole": MessageRole, "ConversationTurn": ConversationTurn,
            "Conversation": Conversation, "ConversationStore": ConversationStore,
            "ConversationChain": ConversationChain, "conversation_store": conversation_store
        }
        return mapping[name]
    
    # Semantic Router
    if name in ("Route", "RouteMatch", "RouteType", "RouterStrategy",
                "KeywordRouter", "SemanticRouter", "HybridRouter",
                "SemanticRouterManager", "semantic_router"):
        from .router import (
            Route, RouteMatch, RouteType, RouterStrategy,
            KeywordRouter, SemanticRouter, HybridRouter,
            SemanticRouterManager, semantic_router
        )
        mapping = {
            "Route": Route, "RouteMatch": RouteMatch, "RouteType": RouteType,
            "RouterStrategy": RouterStrategy, "KeywordRouter": KeywordRouter,
            "SemanticRouter": SemanticRouter, "HybridRouter": HybridRouter,
            "SemanticRouterManager": SemanticRouterManager, "semantic_router": semantic_router
        }
        return mapping[name]
    
    # ============ NEW ENTERPRISE MODULES v2.0 (Lazy) ============
    
    # 1. MCP Protocol
    if name in ("MCPServer", "MCPResource", "MCPTool", "MCPPrompt", 
                "CoreToolProvider", "RAGToolProvider", "SystemPromptProvider"):
        try:
            from .mcp_server import MCPServer, MCPResource, MCPTool, MCPPrompt
            from .mcp_providers import CoreToolProvider, RAGToolProvider, SystemPromptProvider
            mapping = {
                "MCPServer": MCPServer, "MCPResource": MCPResource,
                "MCPTool": MCPTool, "MCPPrompt": MCPPrompt,
                "CoreToolProvider": CoreToolProvider, "RAGToolProvider": RAGToolProvider,
                "SystemPromptProvider": SystemPromptProvider
            }
            return mapping.get(name)
        except ImportError:
            return None
    
    # 2. Langfuse Observability
    if name in ("ObservabilityManager", "traced", "spanned"):
        try:
            from .langfuse_observability import ObservabilityManager, traced, spanned
            mapping = {"ObservabilityManager": ObservabilityManager, "traced": traced, "spanned": spanned}
            return mapping[name]
        except ImportError:
            if name in ("traced", "spanned"):
                return lambda *a, **kw: lambda f: f
            return None
    
    # 3. Instructor Structured Output
    if name in ("StructuredLLM", "ConversationIntent", "RAGResponse", "Summary", "ChainOfThought"):
        try:
            from .instructor_structured import StructuredLLM, ConversationIntent, RAGResponse, Summary, ChainOfThought
            mapping = {
                "StructuredLLM": StructuredLLM, "ConversationIntent": ConversationIntent,
                "RAGResponse": RAGResponse, "Summary": Summary, "ChainOfThought": ChainOfThought
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 4. LangGraph Orchestration
    if name in ("StateGraph", "CompiledGraph", "AgentState", "create_rag_graph", "create_conversation_graph"):
        try:
            from .langgraph_orchestration import StateGraph, CompiledGraph, AgentState, create_rag_graph, create_conversation_graph
            mapping = {
                "StateGraph": StateGraph, "CompiledGraph": CompiledGraph, "AgentState": AgentState,
                "create_rag_graph": create_rag_graph, "create_conversation_graph": create_conversation_graph
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 5. CRAG
    if name in ("CRAGPipeline", "RelevanceGrader", "QueryTransformer"):
        try:
            from .crag_system import CRAGPipeline, RelevanceGrader, QueryTransformer
            mapping = {"CRAGPipeline": CRAGPipeline, "RelevanceGrader": RelevanceGrader, "QueryTransformer": QueryTransformer}
            return mapping[name]
        except ImportError:
            return None
    
    # 6. MemGPT Memory
    if name in ("TieredMemoryManager", "MemoryEnabledAgent", "CoreMemory", "WorkingMemory", "ArchivalMemory"):
        try:
            from .memgpt_memory import TieredMemoryManager, MemoryEnabledAgent, CoreMemory, WorkingMemory, ArchivalMemory
            mapping = {
                "TieredMemoryManager": TieredMemoryManager, "MemoryEnabledAgent": MemoryEnabledAgent,
                "CoreMemory": CoreMemory, "WorkingMemory": WorkingMemory, "ArchivalMemory": ArchivalMemory
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 7. Multi-Agent Debate
    if name in ("DebateOrchestrator", "DebateAgent", "JudgeAgent", "multi_agent_debate", "AgentRole", "DebatePhase"):
        try:
            from .multi_agent_debate import DebateOrchestrator, DebateAgent, JudgeAgent, multi_agent_debate, AgentRole, DebatePhase
            mapping = {
                "DebateOrchestrator": DebateOrchestrator, "DebateAgent": DebateAgent,
                "JudgeAgent": JudgeAgent, "multi_agent_debate": multi_agent_debate,
                "AgentRole": AgentRole, "DebatePhase": DebatePhase
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 8. MoE Router
    if name in ("MoERouter", "AdaptiveMoERouter", "QueryAnalyzer", "ExpertType", "RoutingStrategy"):
        try:
            from .moe_router import MoERouter, AdaptiveMoERouter, QueryAnalyzer, ExpertType, RoutingStrategy
            mapping = {
                "MoERouter": MoERouter, "AdaptiveMoERouter": AdaptiveMoERouter,
                "QueryAnalyzer": QueryAnalyzer, "ExpertType": ExpertType, "RoutingStrategy": RoutingStrategy
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 9. Graph RAG
    if name in ("GraphRAGPipeline", "create_graph_rag", "Entity", "Relationship", "EntityType", "RelationType"):
        try:
            from .graph_rag import GraphRAGPipeline, create_graph_rag, Entity, Relationship, EntityType, RelationType
            mapping = {
                "GraphRAGPipeline": GraphRAGPipeline, "create_graph_rag": create_graph_rag,
                "Entity": Entity, "Relationship": Relationship, "EntityType": EntityType, "RelationType": RelationType
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 10. RAGAS Evaluation
    if name in ("RAGASEvaluator", "quick_evaluate", "MetricType", "EvaluationSample", "EvaluationResult"):
        try:
            from .ragas_evaluation import RAGASEvaluator, quick_evaluate, MetricType, EvaluationSample, EvaluationResult
            mapping = {
                "RAGASEvaluator": RAGASEvaluator, "quick_evaluate": quick_evaluate,
                "MetricType": MetricType, "EvaluationSample": EvaluationSample, "EvaluationResult": EvaluationResult
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 11. Advanced Guardrails
    if name in ("GuardrailOrchestrator", "create_default_guardrails", "PIIDetectionGuardrail", 
                "JailbreakDetectionGuardrail", "safe_generate"):
        try:
            from .advanced_guardrails import (
                GuardrailOrchestrator, create_default_guardrails,
                PIIDetectionGuardrail, JailbreakDetectionGuardrail, safe_generate
            )
            mapping = {
                "GuardrailOrchestrator": GuardrailOrchestrator,
                "create_default_guardrails": create_default_guardrails,
                "PIIDetectionGuardrail": PIIDetectionGuardrail,
                "JailbreakDetectionGuardrail": JailbreakDetectionGuardrail,
                "safe_generate": safe_generate
            }
            return mapping[name]
        except ImportError:
            return None
    
    # 12. Voice/Multimodal
    if name in ("MultimodalPipeline", "create_multimodal_pipeline", "WhisperLocalSTT", "EdgeTTS", "LLaVAVision"):
        try:
            from .voice_multimodal import MultimodalPipeline, create_multimodal_pipeline, WhisperLocalSTT, EdgeTTS, LLaVAVision
            mapping = {
                "MultimodalPipeline": MultimodalPipeline, "create_multimodal_pipeline": create_multimodal_pipeline,
                "WhisperLocalSTT": WhisperLocalSTT, "EdgeTTS": EdgeTTS, "LLaVAVision": LLaVAVision
            }
            return mapping[name]
        except ImportError:
            return None
    
    # Enterprise Orchestrator
    if name in ("EnterpriseAIOrchestrator", "create_orchestrator", "SystemConfig", "ProcessingResult"):
        try:
            from .orchestrator import EnterpriseAIOrchestrator, create_orchestrator, SystemConfig, ProcessingResult
            mapping = {
                "EnterpriseAIOrchestrator": EnterpriseAIOrchestrator, "create_orchestrator": create_orchestrator,
                "SystemConfig": SystemConfig, "ProcessingResult": ProcessingResult
            }
            return mapping[name]
        except ImportError:
            return None
    
    # System Self-Knowledge
    if name in ("SYSTEM_KNOWLEDGE", "SELF_KNOWLEDGE_PROMPT", "get_capability_info", 
                "get_all_capabilities", "get_feature_summary", "system_knowledge",
                "SYSTEM_VERSION", "SYSTEM_NAME"):
        try:
            from .system_knowledge import (
                SYSTEM_KNOWLEDGE, SELF_KNOWLEDGE_PROMPT, get_capability_info,
                get_all_capabilities, get_feature_summary, system_knowledge,
                SYSTEM_VERSION, SYSTEM_NAME
            )
            mapping = {
                "SYSTEM_KNOWLEDGE": SYSTEM_KNOWLEDGE,
                "SELF_KNOWLEDGE_PROMPT": SELF_KNOWLEDGE_PROMPT,
                "get_capability_info": get_capability_info,
                "get_all_capabilities": get_all_capabilities,
                "get_feature_summary": get_feature_summary,
                "system_knowledge": system_knowledge,
                "SYSTEM_VERSION": SYSTEM_VERSION,
                "SYSTEM_NAME": SYSTEM_NAME,
            }
            return mapping[name]
        except ImportError:
            return None
    
    raise AttributeError(f"module 'core' has no attribute '{name}'")


__all__ = [
    # Config (always loaded)
    "settings",
    # Logging (always loaded)
    "get_logger",
    "logger",
    "log_info",
    "log_error",
    "log_warning",
    # Utils (always loaded)
    "sanitize_filename",
    "generate_hash",
    "truncate_text",
    "format_bytes",
    "clean_text",
    "timestamp_now",
    # Heavy modules (lazy loaded)
    "LLMManager",
    "llm_manager",
    "EmbeddingManager", 
    "embedding_manager",
    "VectorStore",
    "vector_store",
    "SessionManager",
    "session_manager",
    "AnalyticsManager",
    "analytics",
    "CacheManager",
    "cache_manager",
    "cached",
    "PromptManager",
    "prompt_manager",
    "PromptCategory",
    "ExportManager",
    "ImportManager",
    "export_manager",
    "import_manager",
    "RateLimiter",
    "rate_limiter",
    "rate_limit",
    "HealthChecker",
    "health_checker",
    "get_health_report",
    "DocumentProcessor",
    "document_processor",
    "MemoryManager",
    "memory_manager",
    "LongTermMemory",
    "Workflow",
    "WorkflowBuilder",
    "WorkflowState",
    "rag_workflow",
    "agent_workflow",
    "Guardrails",
    "guardrails",
    "InputGuard",
    "OutputGuard",
    "GuardLevel",
    "TaskQueue",
    "task_queue",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "task_registry",
    "PluginManager",
    "plugin_manager",
    "PluginInterface",
    "HookManager",
    "HookPriority",
    "StreamManager",
    "stream_manager",
    "StreamingResponse",
    "StreamEvent",
    "StreamEventType",
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
    "Message",
    "MessageRole",
    "ConversationTurn",
    "Conversation",
    "ConversationStore",
    "ConversationChain",
    "conversation_store",
    "Route",
    "RouteMatch",
    "RouteType",
    "RouterStrategy",
    "KeywordRouter",
    "SemanticRouter",
    "HybridRouter",
    "SemanticRouterManager",
    "semantic_router",
    # Enterprise v2.0 (lazy loaded)
    "MCPServer",
    "MCPResource",
    "MCPTool",
    "MCPPrompt",
    "CoreToolProvider",
    "RAGToolProvider",
    "SystemPromptProvider",
    "ObservabilityManager",
    "traced",
    "spanned",
    "StructuredLLM",
    "ConversationIntent",
    "RAGResponse",
    "Summary",
    "ChainOfThought",
    "StateGraph",
    "CompiledGraph",
    "AgentState",
    "create_rag_graph",
    "create_conversation_graph",
    "CRAGPipeline",
    "RelevanceGrader",
    "QueryTransformer",
    "TieredMemoryManager",
    "MemoryEnabledAgent",
    "CoreMemory",
    "WorkingMemory",
    "ArchivalMemory",
    "DebateOrchestrator",
    "DebateAgent",
    "JudgeAgent",
    "multi_agent_debate",
    "AgentRole",
    "DebatePhase",
    "MoERouter",
    "AdaptiveMoERouter",
    "QueryAnalyzer",
    "ExpertType",
    "RoutingStrategy",
    "GraphRAGPipeline",
    "create_graph_rag",
    "Entity",
    "Relationship",
    "EntityType",
    "RelationType",
    "RAGASEvaluator",
    "quick_evaluate",
    "MetricType",
    "EvaluationSample",
    "EvaluationResult",
    "GuardrailOrchestrator",
    "create_default_guardrails",
    "PIIDetectionGuardrail",
    "JailbreakDetectionGuardrail",
    "safe_generate",
    "MultimodalPipeline",
    "create_multimodal_pipeline",
    "WhisperLocalSTT",
    "EdgeTTS",
    "LLaVAVision",
    "EnterpriseAIOrchestrator",
    "create_orchestrator",
    "SystemConfig",
    "ProcessingResult",
    # System Self-Knowledge
    "SYSTEM_KNOWLEDGE",
    "SELF_KNOWLEDGE_PROMPT",
    "get_capability_info",
    "get_all_capabilities",
    "get_feature_summary",
    "system_knowledge",
    "SYSTEM_VERSION",
    "SYSTEM_NAME",
]
