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
from .retriever import Retriever
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

__all__ = [
    # Basic RAG
    "DocumentLoader",
    "DocumentChunker", 
    "Retriever",
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
]
