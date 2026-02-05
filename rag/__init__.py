# Enterprise AI Assistant - RAG Module
# Endüstri Standartlarında Kurumsal AI Çözümü
#
# Features:
# - Multi-strategy retrieval (Semantic, BM25, Hybrid, HyDE, Fusion)
# - Page-based search support
# - Parent-child chunk hierarchy
# - Semantic chunking with boundaries
# - Citation tracking with source attribution
# - Context window optimization
# - Query understanding & classification
# - Comprehensive evaluation metrics
# - Caching and metrics collection
# - Real-time streaming support

from .document_loader import DocumentLoader
from .chunker import DocumentChunker
from .retriever import Retriever, retriever  # Export both class and singleton
from .advanced_rag import AdvancedRAG, advanced_rag, RAGStrategy, RAGConfig
from .knowledge_graph import KnowledgeGraph, knowledge_graph, Entity, Relation
from .evaluation import RAGEvaluator, rag_evaluator, RAGEvaluationReport

# Enterprise RAG Pipeline (NEW)
from .pipeline import (
    RAGPipeline,
    RAGContext,
    RAGResponse,
    RetrievedChunk,
    Citation,
    RetrievalStrategy,
    QueryType,
    ChunkType,
    QueryAnalyzer,
    SemanticChunker,
    ContextWindowOptimizer,
    rag_pipeline,
)

# RAG Orchestrator (NEW)
from .orchestrator import (
    RAGOrchestrator,
    RAGCache,
    RAGMetrics,
    rag_orchestrator,
)

# Reranker
from .reranker import (
    RankedDocument,
    RerankerStrategy,
    BM25Reranker,
    CrossEncoderReranker,
    RRFReranker,
    LLMReranker,
    EnsembleReranker,
    Reranker,
    reranker,
)

# Adaptive Threshold (NEW - Premium)
from .adaptive_threshold import (
    AdaptiveThresholdEngine,
    AdaptiveRetriever,
    ThresholdConfig,
    ThresholdResult,
    QueryDifficulty,
    adaptive_threshold,
    adaptive_retriever,
)

# Context Optimizer (NEW - Premium)
from .context_optimizer import (
    ContextOptimizer,
    ContextBuilder,
    OptimizedContext,
    OptimizerConfig,
    CompressionStrategy,
    context_optimizer,
    context_builder,
)

# Query Expansion
from .query_expansion import (
    ExpansionStrategy,
    ExpandedQuery,
    QueryExpander,
    SynonymExpander,
    HyDEExpander,
    MultiQueryExpander,
    StepBackExpander,
    KeywordExpander,
    QueryExpansionManager,
    query_expansion_manager,
)

# Hybrid Search
from .hybrid_search import (
    SearchStrategy,
    SearchResult,
    Document,
    BM25Index,
    DenseSearcher,
    HybridSearcher,
    HybridSearchManager,
    hybrid_search_manager,
)

# ============================================================================
# ADVANCED RAG MODULES (Enterprise Features)
# ============================================================================

# Agentic RAG - Agent-based dynamic retrieval
from .agentic_rag import (
    AgenticRAG,
    AgenticQueryAnalyzer,
    AgenticPlanner,
    AgenticExecutor,
    AgenticResult,
    QueryComplexity,
    StrategyType,
    AgentState,
    agentic_rag,
    get_agentic_rag,
)

# Self-RAG - Self-reflective RAG with quality feedback
from .self_rag import (
    SelfRAG,
    SelfRAGResponse,
    RetrievalDecision,
    SupportLevel,
    RelevanceLevel,
    UsefulnessLevel,
    QualityDimension,
    RetrievalPredictor,
    PassageEvaluator,
    SelfCritic,
    ResponseRefiner,
    self_rag,
    get_self_rag,
)

# Graph RAG - Knowledge Graph enhanced retrieval
from .graph_rag_advanced import (
    GraphRAG,
    GraphRAGResult,  # Was incorrectly named GraphRAGResponse
    EntityType,
    RelationType,
    TraversalStrategy,
    Entity as GraphEntity,
    Relationship,
    GraphPath,
    KnowledgeGraph as AdvancedKnowledgeGraph,
    EntityExtractor,
    RelationshipExtractor,
    graph_rag,
    get_graph_rag,
)

# Multimodal RAG - Multi-content type processing
from .multimodal_rag import (
    MultiModalRAG,
    MultiModalResult,  # Was incorrectly named MultiModalResponse
    ContentModality,
    ExtractionMethod,
    ProcessingStatus,
    ExtractedContent,
    MultiModalProcessor,
    TextExtractor,
    ImageExtractor,
    PDFExtractor,
    multimodal_rag,
    get_multimodal_rag,
)

# Conversational RAG - Chat-aware with memory
from .conversational_rag import (
    ConversationalRAG,
    ConversationalResult,  # Was incorrectly named ConversationalResponse
    MessageRole,
    ConversationState,
    QueryType as ConvQueryType,
    TopicState,
    Message,
    Topic,
    ConversationContext,
    ConversationMemory,
    QueryReformulator,
    TopicTracker,
    conversational_rag,
    get_conversational_rag,
)

# Citation Verifier - Hallucination detection
from .citation_verifier import (
    CitationVerifier,
    CitationAnalysis,
    ClaimType,
    VerificationStatus,
    HallucinationType,
    GroundingLevel,
    Claim,
    SourceCitation,
    ClaimExtractor,
    SourceVerifier,
    HallucinationDetector,
    GroundingScorer,
    citation_verifier,
    get_citation_verifier,
)

# RAGAS Metrics - Comprehensive evaluation
from .ragas_metrics import (
    RAGASEvaluator,
    RAGASInput,
    RAGASResult,
    MetricResult,
    BatchEvaluationResult,
    MetricType,
    EvaluationLevel,
    QualityTier,
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    ContextPrecisionMetric,
    ContextRecallMetric,
    ContextRelevancyMetric,
    CoherenceMetric,
    HarmfulnessMetric,
    ragas_evaluator,
    get_ragas_evaluator,
)

# Unified Orchestrator - Advanced RAG coordination
from .unified_orchestrator import (
    UnifiedAdvancedOrchestrator,
    UnifiedQueryAnalyzer,
    StrategySelector,
    UnifiedRAGResponse,
    QueryAnalysis,
    StrategyDecision,
    RetrievalResult,
    GenerationResult,
    VerificationResult,
    OrchestratorConfig,
    RAGStrategy as UnifiedRAGStrategy,
    QueryIntent,
    PipelinePhase,
    FailureMode,
    unified_orchestrator,
    get_unified_orchestrator,
)

__all__ = [
    # Basic RAG
    "DocumentLoader",
    "DocumentChunker", 
    "Retriever",
    "retriever",  # Singleton instance
    # Advanced RAG
    "AdvancedRAG",
    "advanced_rag",
    "RAGStrategy",
    "RAGConfig",
    # Enterprise Pipeline (NEW)
    "RAGPipeline",
    "RAGContext",
    "RAGResponse",
    "RetrievedChunk",
    "Citation",
    "RetrievalStrategy",
    "QueryType",
    "ChunkType",
    "QueryAnalyzer",
    "SemanticChunker",
    "ContextWindowOptimizer",
    "rag_pipeline",
    # RAG Orchestrator (NEW)
    "RAGOrchestrator",
    "RAGCache",
    "RAGMetrics",
    "rag_orchestrator",
    # Knowledge Graph
    "KnowledgeGraph",
    "knowledge_graph",
    "Entity",
    "Relation",
    # Evaluation
    "RAGEvaluator",
    "rag_evaluator",
    "RAGEvaluationReport",
    # Reranker
    "RankedDocument",
    "RerankerStrategy",
    "BM25Reranker",
    "CrossEncoderReranker",
    "RRFReranker",
    "LLMReranker",
    "EnsembleReranker",
    "Reranker",
    "reranker",
    # Adaptive Threshold (Premium)
    "AdaptiveThresholdEngine",
    "AdaptiveRetriever",
    "ThresholdConfig",
    "ThresholdResult",
    "QueryDifficulty",
    "adaptive_threshold",
    "adaptive_retriever",
    # Context Optimizer (Premium)
    "ContextOptimizer",
    "ContextBuilder",
    "OptimizedContext",
    "OptimizerConfig",
    "CompressionStrategy",
    "context_optimizer",
    "context_builder",
    # Query Expansion
    "ExpansionStrategy",
    "ExpandedQuery",
    "QueryExpander",
    "SynonymExpander",
    "HyDEExpander",
    "MultiQueryExpander",
    "StepBackExpander",
    "KeywordExpander",
    "QueryExpansionManager",
    "query_expansion_manager",
    # Hybrid Search
    "SearchStrategy",
    "SearchResult",
    "Document",
    "BM25Index",
    "DenseSearcher",
    "HybridSearcher",
    "HybridSearchManager",
    "hybrid_search_manager",
    # ========================================
    # ADVANCED RAG MODULES
    # ========================================
    # Agentic RAG
    "AgenticRAG",
    "AgenticQueryAnalyzer",
    "AgenticPlanner",
    "AgenticExecutor",
    "AgenticResult",
    "QueryComplexity",
    "StrategyType",
    "AgentState",
    "agentic_rag",
    "get_agentic_rag",
    # Self-RAG
    "SelfRAG",
    "SelfRAGResponse",
    "RetrievalDecision",
    "SupportLevel",
    "RelevanceLevel",
    "UsefulnessLevel",
    "QualityDimension",
    "RetrievalPredictor",
    "PassageEvaluator",
    "SelfCritic",
    "ResponseRefiner",
    "self_rag",
    "get_self_rag",
    # Graph RAG
    "GraphRAG",
    "GraphRAGResponse",
    "EntityType",
    "RelationType",
    "TraversalStrategy",
    "GraphEntity",
    "Relationship",
    "GraphPath",
    "AdvancedKnowledgeGraph",
    "EntityExtractor",
    "RelationshipExtractor",
    "graph_rag",
    "get_graph_rag",
    # Multimodal RAG
    "MultiModalRAG",
    "MultiModalResponse",
    "ContentModality",
    "ExtractionMethod",
    "ProcessingStatus",
    "ExtractedContent",
    "MultiModalProcessor",
    "TextExtractor",
    "ImageExtractor",
    "PDFExtractor",
    "multimodal_rag",
    "get_multimodal_rag",
    # Conversational RAG
    "ConversationalRAG",
    "ConversationalResponse",
    "MessageRole",
    "ConversationState",
    "ConvQueryType",
    "TopicState",
    "Message",
    "Topic",
    "ConversationContext",
    "ConversationMemory",
    "QueryReformulator",
    "TopicTracker",
    "conversational_rag",
    "get_conversational_rag",
    # Citation Verifier
    "CitationVerifier",
    "CitationAnalysis",
    "ClaimType",
    "VerificationStatus",
    "HallucinationType",
    "GroundingLevel",
    "Claim",
    "SourceCitation",
    "ClaimExtractor",
    "SourceVerifier",
    "HallucinationDetector",
    "GroundingScorer",
    "citation_verifier",
    "get_citation_verifier",
    # RAGAS Metrics
    "RAGASEvaluator",
    "RAGASInput",
    "RAGASResult",
    "MetricResult",
    "BatchEvaluationResult",
    "MetricType",
    "EvaluationLevel",
    "QualityTier",
    "AnswerRelevancyMetric",
    "FaithfulnessMetric",
    "ContextPrecisionMetric",
    "ContextRecallMetric",
    "ContextRelevancyMetric",
    "CoherenceMetric",
    "HarmfulnessMetric",
    "ragas_evaluator",
    "get_ragas_evaluator",
    # Unified Orchestrator
    "UnifiedAdvancedOrchestrator",
    "UnifiedQueryAnalyzer",
    "StrategySelector",
    "UnifiedRAGResponse",
    "QueryAnalysis",
    "StrategyDecision",
    "RetrievalResult",
    "GenerationResult",
    "VerificationResult",
    "OrchestratorConfig",
    "UnifiedRAGStrategy",
    "QueryIntent",
    "PipelinePhase",
    "FailureMode",
    "unified_orchestrator",
    "get_unified_orchestrator",
]
