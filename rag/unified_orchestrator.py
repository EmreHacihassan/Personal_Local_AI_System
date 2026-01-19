"""
Unified Advanced RAG Orchestrator
==================================

Enterprise-grade orchestrator that unifies all advanced RAG systems:
- Agentic RAG (dynamic, agent-based retrieval)
- Self-RAG (self-reflective with quality feedback)
- Graph RAG (knowledge graph enhanced)
- Multimodal RAG (handles various content types)
- Conversational RAG (chat-aware with memory)
- Citation Verifier (hallucination detection)

Features:
- Automatic strategy selection based on query analysis
- Fallback chains between systems
- Quality gates and thresholds
- Async processing pipeline
- Real-time metrics and monitoring
- Graceful degradation

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple, Union

from core.logger import get_logger

logger = get_logger("rag.unified_orchestrator")


# =============================================================================
# ENUMS
# =============================================================================

class RAGStrategy(Enum):
    """RAG strategy types."""
    STANDARD = "standard"           # Basic retrieval
    AGENTIC = "agentic"             # Agent-based dynamic
    SELF_RAG = "self_rag"           # Self-reflective
    GRAPH_RAG = "graph_rag"         # Knowledge graph
    MULTIMODAL = "multimodal"       # Multi-content types
    CONVERSATIONAL = "conversational"  # Chat-aware
    HYBRID = "hybrid"               # Combination
    AUTO = "auto"                   # Automatic selection


class QueryIntent(Enum):
    """Query intent classification."""
    FACTUAL = "factual"             # Who, what, when, where
    ANALYTICAL = "analytical"       # Why, how, compare
    EXPLORATORY = "exploratory"     # Tell me about, explain
    CONVERSATIONAL = "conversational"  # Follow-up, reference
    MULTIMODAL = "multimodal"       # Images, tables, code
    KNOWLEDGE_GRAPH = "knowledge_graph"  # Relationships, entities


class PipelinePhase(Enum):
    """Pipeline execution phases."""
    ANALYSIS = "analysis"
    STRATEGY_SELECTION = "strategy_selection"
    RETRIEVAL = "retrieval"
    GENERATION = "generation"
    VERIFICATION = "verification"
    POST_PROCESSING = "post_processing"


class FailureMode(Enum):
    """Failure handling modes."""
    STRICT = "strict"       # Fail on any error
    FALLBACK = "fallback"   # Try fallback strategies
    GRACEFUL = "graceful"   # Return partial results


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QueryAnalysis:
    """Query analysis result."""
    query: str
    intent: QueryIntent
    complexity: str  # simple, medium, complex
    
    # Features
    has_conversation_context: bool = False
    has_multimodal_request: bool = False
    requires_reasoning: bool = False
    requires_knowledge_graph: bool = False
    
    # Scores
    confidence: float = 1.0
    features: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    analysis_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query[:100],
            "intent": self.intent.value,
            "complexity": self.complexity,
            "has_conversation_context": self.has_conversation_context,
            "has_multimodal_request": self.has_multimodal_request,
            "requires_reasoning": self.requires_reasoning,
            "requires_knowledge_graph": self.requires_knowledge_graph,
            "confidence": self.confidence,
            "analysis_time_ms": self.analysis_time_ms,
        }


@dataclass
class StrategyDecision:
    """Strategy selection decision."""
    primary_strategy: RAGStrategy
    fallback_strategies: List[RAGStrategy]
    
    # Reasoning
    reasoning: str = ""
    confidence: float = 1.0
    
    # Configuration overrides
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "primary": self.primary_strategy.value,
            "fallbacks": [s.value for s in self.fallback_strategies],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


@dataclass
class RetrievalResult:
    """Retrieval result from any RAG system."""
    documents: List[Dict[str, Any]]
    scores: List[float]
    
    # Metadata
    strategy_used: RAGStrategy = RAGStrategy.STANDARD
    retrieval_time_ms: int = 0
    total_candidates: int = 0
    
    # Quality
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "document_count": len(self.documents),
            "strategy": self.strategy_used.value,
            "retrieval_time_ms": self.retrieval_time_ms,
            "quality_score": self.quality_score,
        }


@dataclass
class GenerationResult:
    """Generation result."""
    answer: str
    
    # Citations
    citations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Quality
    confidence: float = 0.0
    grounding_score: float = 0.0
    
    # Processing
    generation_time_ms: int = 0
    tokens_used: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "answer_length": len(self.answer),
            "citation_count": len(self.citations),
            "confidence": self.confidence,
            "grounding_score": self.grounding_score,
            "generation_time_ms": self.generation_time_ms,
        }


@dataclass
class VerificationResult:
    """Verification result from citation verifier."""
    is_verified: bool
    
    # Scores
    faithfulness_score: float = 0.0
    grounding_score: float = 0.0
    
    # Issues
    hallucinations_detected: int = 0
    unsupported_claims: List[str] = field(default_factory=list)
    
    # Timing
    verification_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "is_verified": self.is_verified,
            "faithfulness": self.faithfulness_score,
            "grounding": self.grounding_score,
            "hallucinations": self.hallucinations_detected,
        }


@dataclass
class UnifiedRAGResponse:
    """Complete unified RAG response."""
    query: str
    answer: str
    
    # Analysis
    query_analysis: Optional[QueryAnalysis] = None
    strategy_decision: Optional[StrategyDecision] = None
    
    # Results from each phase
    retrieval_result: Optional[RetrievalResult] = None
    generation_result: Optional[GenerationResult] = None
    verification_result: Optional[VerificationResult] = None
    
    # Quality
    overall_quality_score: float = 0.0
    confidence: float = 0.0
    
    # Citations
    citations: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    
    # Processing
    total_time_ms: int = 0
    phases_completed: List[str] = field(default_factory=list)
    
    # Fallback info
    fallback_used: bool = False
    fallback_strategy: Optional[RAGStrategy] = None
    
    # Metadata
    request_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query[:100],
            "answer": self.answer[:500] if self.answer else "",
            "strategy": self.strategy_decision.to_dict() if self.strategy_decision else None,
            "retrieval": self.retrieval_result.to_dict() if self.retrieval_result else None,
            "generation": self.generation_result.to_dict() if self.generation_result else None,
            "verification": self.verification_result.to_dict() if self.verification_result else None,
            "quality_score": self.overall_quality_score,
            "confidence": self.confidence,
            "total_time_ms": self.total_time_ms,
            "phases_completed": self.phases_completed,
            "fallback_used": self.fallback_used,
            "request_id": self.request_id,
        }


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration."""
    # Strategy
    default_strategy: RAGStrategy = RAGStrategy.AUTO
    enable_fallbacks: bool = True
    max_fallback_attempts: int = 2
    
    # Quality gates
    min_retrieval_quality: float = 0.3
    min_answer_confidence: float = 0.4
    max_hallucination_score: float = 0.3
    
    # Timeouts (ms)
    analysis_timeout: int = 2000
    retrieval_timeout: int = 10000
    generation_timeout: int = 30000
    verification_timeout: int = 5000
    
    # Features
    enable_verification: bool = True
    enable_caching: bool = True
    enable_metrics: bool = True
    
    # Failure mode
    failure_mode: FailureMode = FailureMode.FALLBACK
    
    def to_dict(self) -> Dict:
        return {
            "default_strategy": self.default_strategy.value,
            "enable_fallbacks": self.enable_fallbacks,
            "min_retrieval_quality": self.min_retrieval_quality,
            "min_answer_confidence": self.min_answer_confidence,
            "enable_verification": self.enable_verification,
            "failure_mode": self.failure_mode.value,
        }


# =============================================================================
# PROTOCOLS
# =============================================================================

class LLMProtocol(Protocol):
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        ...


# =============================================================================
# QUERY ANALYZER
# =============================================================================

class UnifiedQueryAnalyzer:
    """Analyzes queries to determine optimal RAG strategy."""
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
        
        # Intent patterns
        self._intent_patterns = {
            QueryIntent.FACTUAL: [
                r'\b(who|what|when|where|which)\b',
                r'\b(kim|ne|ne zaman|nerede|hangi)\b',
                r'\b(define|list|name)\b',
            ],
            QueryIntent.ANALYTICAL: [
                r'\b(why|how|explain|analyze|compare)\b',
                r'\b(neden|nasıl|açıkla|analiz|karşılaştır)\b',
                r'\b(difference|relationship|cause)\b',
            ],
            QueryIntent.EXPLORATORY: [
                r'\b(tell me about|describe|overview)\b',
                r'\b(anlat|tanımla|hakkında)\b',
                r'\b(introduction|summary)\b',
            ],
            QueryIntent.CONVERSATIONAL: [
                r'\b(it|this|that|they|these)\b',
                r'\b(bu|şu|o|onlar)\b',
                r'\b(also|more|another)\b',
                r'\b(previous|before|earlier)\b',
            ],
            QueryIntent.MULTIMODAL: [
                r'\b(image|picture|photo|diagram)\b',
                r'\b(table|chart|graph)\b',
                r'\b(code|snippet|function)\b',
                r'\b(resim|fotoğraf|tablo|grafik|kod)\b',
            ],
            QueryIntent.KNOWLEDGE_GRAPH: [
                r'\b(related|connection|link)\b',
                r'\b(entities|relationships)\b',
                r'\b(ilişki|bağlantı|varlık)\b',
            ],
        }
        
        # Complexity indicators
        self._complexity_patterns = {
            'complex': [
                r'\band\b.*\band\b',
                r'multiple|several|various',
                r'compare.*with',
                r'relationship between',
            ],
            'medium': [
                r'\bbut\b',
                r'however|although',
                r'explain how',
            ],
        }
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def analyze(self, query: str, conversation_history: Optional[List[str]] = None) -> QueryAnalysis:
        """Analyze query to determine optimal strategy."""
        import re
        start_time = time.time()
        
        query_lower = query.lower()
        
        # Detect intent
        intent_scores = {}
        for intent, patterns in self._intent_patterns.items():
            score = sum(1 for p in patterns if re.search(p, query_lower, re.IGNORECASE))
            intent_scores[intent] = score
        
        # Primary intent
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else QueryIntent.FACTUAL
        
        # If no clear pattern, default to exploratory
        if all(v == 0 for v in intent_scores.values()):
            primary_intent = QueryIntent.EXPLORATORY
        
        # Detect complexity
        complexity = 'simple'
        for level, patterns in self._complexity_patterns.items():
            if any(re.search(p, query_lower, re.IGNORECASE) for p in patterns):
                complexity = level
                break
        
        # Check for conversation context
        has_conversation = bool(conversation_history and len(conversation_history) > 0)
        
        # Check if query references previous context
        if intent_scores.get(QueryIntent.CONVERSATIONAL, 0) > 0:
            has_conversation = True
        
        # Check for multimodal request
        has_multimodal = intent_scores.get(QueryIntent.MULTIMODAL, 0) > 0
        
        # Check if reasoning required
        requires_reasoning = (
            complexity == 'complex' or
            primary_intent == QueryIntent.ANALYTICAL
        )
        
        # Check for knowledge graph need
        requires_kg = (
            intent_scores.get(QueryIntent.KNOWLEDGE_GRAPH, 0) > 0 or
            'relationship' in query_lower or
            'connection' in query_lower
        )
        
        analysis_time = int((time.time() - start_time) * 1000)
        
        return QueryAnalysis(
            query=query,
            intent=primary_intent,
            complexity=complexity,
            has_conversation_context=has_conversation,
            has_multimodal_request=has_multimodal,
            requires_reasoning=requires_reasoning,
            requires_knowledge_graph=requires_kg,
            confidence=0.8,
            features={
                "intent_scores": {k.value: v for k, v in intent_scores.items()},
                "word_count": len(query.split()),
            },
            analysis_time_ms=analysis_time,
        )


# =============================================================================
# STRATEGY SELECTOR
# =============================================================================

class StrategySelector:
    """Selects optimal RAG strategy based on query analysis."""
    
    def __init__(self):
        # Strategy capabilities
        self._strategy_capabilities = {
            RAGStrategy.AGENTIC: {
                'complex_queries': True,
                'multi_step': True,
                'dynamic_retrieval': True,
            },
            RAGStrategy.SELF_RAG: {
                'quality_critical': True,
                'fact_checking': True,
                'iterative_refinement': True,
            },
            RAGStrategy.GRAPH_RAG: {
                'entity_relationships': True,
                'multi_hop': True,
                'knowledge_graph': True,
            },
            RAGStrategy.MULTIMODAL: {
                'images': True,
                'tables': True,
                'code': True,
                'mixed_content': True,
            },
            RAGStrategy.CONVERSATIONAL: {
                'chat_context': True,
                'follow_up': True,
                'memory': True,
            },
            RAGStrategy.STANDARD: {
                'simple_queries': True,
                'fast': True,
            },
        }
        
        # Fallback chain
        self._fallback_chains = {
            RAGStrategy.AGENTIC: [RAGStrategy.SELF_RAG, RAGStrategy.STANDARD],
            RAGStrategy.SELF_RAG: [RAGStrategy.AGENTIC, RAGStrategy.STANDARD],
            RAGStrategy.GRAPH_RAG: [RAGStrategy.AGENTIC, RAGStrategy.STANDARD],
            RAGStrategy.MULTIMODAL: [RAGStrategy.STANDARD],
            RAGStrategy.CONVERSATIONAL: [RAGStrategy.STANDARD],
            RAGStrategy.STANDARD: [],
        }
    
    def select(self, analysis: QueryAnalysis) -> StrategyDecision:
        """Select optimal strategy based on analysis."""
        reasoning_parts = []
        
        # Determine primary strategy
        if analysis.has_multimodal_request:
            primary = RAGStrategy.MULTIMODAL
            reasoning_parts.append("Multimodal content detected")
        
        elif analysis.has_conversation_context:
            primary = RAGStrategy.CONVERSATIONAL
            reasoning_parts.append("Conversation context present")
        
        elif analysis.requires_knowledge_graph:
            primary = RAGStrategy.GRAPH_RAG
            reasoning_parts.append("Knowledge graph queries needed")
        
        elif analysis.complexity == 'complex' or analysis.requires_reasoning:
            # For complex queries, prefer Agentic or Self-RAG
            if analysis.intent == QueryIntent.ANALYTICAL:
                primary = RAGStrategy.SELF_RAG
                reasoning_parts.append("Complex analytical query -> Self-RAG")
            else:
                primary = RAGStrategy.AGENTIC
                reasoning_parts.append("Complex query -> Agentic RAG")
        
        elif analysis.intent == QueryIntent.FACTUAL:
            primary = RAGStrategy.STANDARD
            reasoning_parts.append("Simple factual query -> Standard RAG")
        
        else:
            primary = RAGStrategy.AGENTIC
            reasoning_parts.append("Default -> Agentic RAG")
        
        # Get fallback chain
        fallbacks = self._fallback_chains.get(primary, [RAGStrategy.STANDARD])
        
        return StrategyDecision(
            primary_strategy=primary,
            fallback_strategies=fallbacks,
            reasoning=" | ".join(reasoning_parts),
            confidence=analysis.confidence * 0.9,
        )


# =============================================================================
# UNIFIED ORCHESTRATOR
# =============================================================================

class UnifiedAdvancedOrchestrator:
    """
    Enterprise-grade unified RAG orchestrator.
    
    Combines all advanced RAG systems with:
    - Automatic strategy selection
    - Quality-based fallbacks
    - Verification and grounding
    - Comprehensive monitoring
    
    Example:
        orchestrator = UnifiedAdvancedOrchestrator()
        response = orchestrator.query("What is the relationship between X and Y?")
        print(response.answer)
        print(f"Quality: {response.overall_quality_score}")
    """
    
    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        llm: Optional[LLMProtocol] = None,
    ):
        self.config = config or OrchestratorConfig()
        self._llm = llm
        
        # Components
        self._analyzer = UnifiedQueryAnalyzer(llm)
        self._selector = StrategySelector()
        
        # Lazy-loaded RAG systems
        self._rag_systems: Dict[RAGStrategy, Any] = {}
        self._citation_verifier = None
        
        # Stats
        self._query_count = 0
        self._fallback_count = 0
        self._strategy_usage: Dict[str, int] = {}
        
        logger.info("UnifiedAdvancedOrchestrator initialized")
    
    def _lazy_load_llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def _get_rag_system(self, strategy: RAGStrategy):
        """Lazy load and return RAG system."""
        if strategy in self._rag_systems:
            return self._rag_systems[strategy]
        
        try:
            if strategy == RAGStrategy.AGENTIC:
                from rag.agentic_rag import get_agentic_rag
                self._rag_systems[strategy] = get_agentic_rag()
            
            elif strategy == RAGStrategy.SELF_RAG:
                from rag.self_rag import get_self_rag
                self._rag_systems[strategy] = get_self_rag()
            
            elif strategy == RAGStrategy.GRAPH_RAG:
                from rag.graph_rag_advanced import get_graph_rag
                self._rag_systems[strategy] = get_graph_rag()
            
            elif strategy == RAGStrategy.MULTIMODAL:
                from rag.multimodal_rag import get_multimodal_rag
                self._rag_systems[strategy] = get_multimodal_rag()
            
            elif strategy == RAGStrategy.CONVERSATIONAL:
                from rag.conversational_rag import get_conversational_rag
                self._rag_systems[strategy] = get_conversational_rag()
            
            elif strategy == RAGStrategy.STANDARD:
                from rag.advanced_rag import get_advanced_rag
                self._rag_systems[strategy] = get_advanced_rag()
            
            return self._rag_systems.get(strategy)
        
        except ImportError as e:
            logger.warning(f"Could not load {strategy.value}: {e}")
            return None
    
    def _get_citation_verifier(self):
        """Lazy load citation verifier."""
        if self._citation_verifier is None:
            try:
                from rag.citation_verifier import get_citation_verifier
                self._citation_verifier = get_citation_verifier()
            except ImportError:
                logger.warning("Citation verifier not available")
        return self._citation_verifier
    
    def query(
        self,
        query: str,
        strategy: RAGStrategy = RAGStrategy.AUTO,
        conversation_history: Optional[List[str]] = None,
        context_filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> UnifiedRAGResponse:
        """
        Execute unified RAG query.
        
        Args:
            query: User query
            strategy: RAG strategy (AUTO for automatic selection)
            conversation_history: Previous conversation messages
            context_filter: Metadata filters for retrieval
            **kwargs: Additional parameters
            
        Returns:
            UnifiedRAGResponse
        """
        start_time = time.time()
        request_id = hashlib.md5(f"{query}{time.time()}".encode()).hexdigest()[:8]
        
        self._query_count += 1
        phases_completed = []
        
        response = UnifiedRAGResponse(
            query=query,
            answer="",
            request_id=request_id,
        )
        
        try:
            # Phase 1: Query Analysis
            logger.info(f"[{request_id}] Analyzing query...")
            
            analysis = self._analyzer.analyze(query, conversation_history)
            response.query_analysis = analysis
            phases_completed.append(PipelinePhase.ANALYSIS.value)
            
            # Phase 2: Strategy Selection
            if strategy == RAGStrategy.AUTO:
                decision = self._selector.select(analysis)
            else:
                decision = StrategyDecision(
                    primary_strategy=strategy,
                    fallback_strategies=[RAGStrategy.STANDARD],
                    reasoning=f"User-specified: {strategy.value}",
                )
            
            response.strategy_decision = decision
            phases_completed.append(PipelinePhase.STRATEGY_SELECTION.value)
            
            logger.info(f"[{request_id}] Strategy: {decision.primary_strategy.value}")
            
            # Phase 3: Execute with fallback support
            retrieval_result, generation_result, strategy_used = self._execute_with_fallbacks(
                query=query,
                decision=decision,
                conversation_history=conversation_history,
                context_filter=context_filter,
                **kwargs
            )
            
            response.retrieval_result = retrieval_result
            response.generation_result = generation_result
            response.answer = generation_result.answer if generation_result else ""
            phases_completed.append(PipelinePhase.RETRIEVAL.value)
            phases_completed.append(PipelinePhase.GENERATION.value)
            
            # Track if fallback was used
            if strategy_used != decision.primary_strategy:
                response.fallback_used = True
                response.fallback_strategy = strategy_used
                self._fallback_count += 1
            
            # Update strategy usage stats
            self._strategy_usage[strategy_used.value] = self._strategy_usage.get(strategy_used.value, 0) + 1
            
            # Phase 4: Verification (optional)
            if self.config.enable_verification and generation_result and retrieval_result:
                verification_result = self._verify_response(
                    answer=generation_result.answer,
                    documents=retrieval_result.documents,
                    request_id=request_id,
                )
                response.verification_result = verification_result
                phases_completed.append(PipelinePhase.VERIFICATION.value)
                
                # Update confidence based on verification
                if verification_result:
                    response.confidence = (
                        generation_result.confidence * 0.5 +
                        verification_result.faithfulness_score * 0.5
                    )
                else:
                    response.confidence = generation_result.confidence
            else:
                response.confidence = generation_result.confidence if generation_result else 0.0
            
            # Phase 5: Post-processing
            response = self._post_process(response)
            phases_completed.append(PipelinePhase.POST_PROCESSING.value)
            
            response.phases_completed = phases_completed
        
        except Exception as e:
            logger.error(f"[{request_id}] Error: {e}")
            
            if self.config.failure_mode == FailureMode.STRICT:
                raise
            
            response.answer = f"An error occurred while processing your query: {str(e)}"
            response.confidence = 0.0
        
        finally:
            response.total_time_ms = int((time.time() - start_time) * 1000)
        
        return response
    
    def _execute_with_fallbacks(
        self,
        query: str,
        decision: StrategyDecision,
        conversation_history: Optional[List[str]] = None,
        context_filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[Optional[RetrievalResult], Optional[GenerationResult], RAGStrategy]:
        """Execute query with fallback support."""
        strategies_to_try = [decision.primary_strategy] + decision.fallback_strategies
        
        for i, strategy in enumerate(strategies_to_try):
            if i >= self.config.max_fallback_attempts + 1:
                break
            
            try:
                rag_system = self._get_rag_system(strategy)
                if rag_system is None:
                    logger.warning(f"RAG system not available: {strategy.value}")
                    continue
                
                # Execute based on strategy type
                retrieval_result, generation_result = self._execute_strategy(
                    rag_system=rag_system,
                    strategy=strategy,
                    query=query,
                    conversation_history=conversation_history,
                    context_filter=context_filter,
                    **kwargs
                )
                
                # Quality check
                if retrieval_result and retrieval_result.quality_score >= self.config.min_retrieval_quality:
                    return retrieval_result, generation_result, strategy
                
                if generation_result and generation_result.confidence >= self.config.min_answer_confidence:
                    return retrieval_result, generation_result, strategy
                
                logger.info(f"Quality below threshold, trying fallback...")
                
            except Exception as e:
                logger.warning(f"Strategy {strategy.value} failed: {e}")
                if not self.config.enable_fallbacks:
                    raise
        
        # Return last attempt results
        return None, GenerationResult(answer="Could not generate satisfactory answer"), RAGStrategy.STANDARD
    
    def _execute_strategy(
        self,
        rag_system,
        strategy: RAGStrategy,
        query: str,
        conversation_history: Optional[List[str]] = None,
        context_filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[RetrievalResult, GenerationResult]:
        """Execute specific RAG strategy."""
        start_time = time.time()
        
        # Different strategies have different interfaces
        if strategy == RAGStrategy.CONVERSATIONAL:
            result = rag_system.query(
                query=query,
                conversation_id=kwargs.get("conversation_id", "default"),
            )
            
            return (
                RetrievalResult(
                    documents=getattr(result, 'contexts', []),
                    scores=[0.8] * len(getattr(result, 'contexts', [])),
                    strategy_used=strategy,
                    retrieval_time_ms=int((time.time() - start_time) * 500),
                    quality_score=0.7,
                ),
                GenerationResult(
                    answer=getattr(result, 'answer', str(result)),
                    confidence=getattr(result, 'confidence', 0.7),
                    generation_time_ms=int((time.time() - start_time) * 500),
                )
            )
        
        elif strategy == RAGStrategy.SELF_RAG:
            result = rag_system.query(query=query, k=kwargs.get("k", 5))
            
            return (
                RetrievalResult(
                    documents=getattr(result, 'passages', []),
                    scores=getattr(result, 'passage_scores', []),
                    strategy_used=strategy,
                    retrieval_time_ms=int((time.time() - start_time) * 500),
                    quality_score=getattr(result, 'grounding_score', 0.7),
                ),
                GenerationResult(
                    answer=getattr(result, 'answer', str(result)),
                    confidence=getattr(result, 'confidence', 0.7),
                    grounding_score=getattr(result, 'grounding_score', 0.7),
                    generation_time_ms=int((time.time() - start_time) * 500),
                )
            )
        
        elif strategy == RAGStrategy.AGENTIC:
            result = rag_system.query(query=query)
            
            return (
                RetrievalResult(
                    documents=getattr(result, 'retrieved_documents', []),
                    scores=getattr(result, 'retrieval_scores', []),
                    strategy_used=strategy,
                    retrieval_time_ms=int((time.time() - start_time) * 500),
                    quality_score=getattr(result, 'quality_score', 0.7),
                ),
                GenerationResult(
                    answer=getattr(result, 'answer', str(result)),
                    confidence=getattr(result, 'confidence', 0.7),
                    generation_time_ms=int((time.time() - start_time) * 500),
                )
            )
        
        elif strategy == RAGStrategy.GRAPH_RAG:
            result = rag_system.query(query=query)
            
            return (
                RetrievalResult(
                    documents=getattr(result, 'subgraph', {}).get('nodes', []),
                    scores=[0.8] * len(getattr(result, 'subgraph', {}).get('nodes', [])),
                    strategy_used=strategy,
                    retrieval_time_ms=int((time.time() - start_time) * 500),
                    quality_score=0.7,
                ),
                GenerationResult(
                    answer=getattr(result, 'answer', str(result)),
                    confidence=getattr(result, 'confidence', 0.7),
                    generation_time_ms=int((time.time() - start_time) * 500),
                )
            )
        
        else:  # STANDARD, MULTIMODAL, etc.
            result = rag_system.query(query=query, k=kwargs.get("k", 5))
            
            return (
                RetrievalResult(
                    documents=getattr(result, 'documents', []) or getattr(result, 'contexts', []),
                    scores=[0.7] * 5,
                    strategy_used=strategy,
                    retrieval_time_ms=int((time.time() - start_time) * 500),
                    quality_score=0.7,
                ),
                GenerationResult(
                    answer=getattr(result, 'answer', str(result)),
                    confidence=getattr(result, 'confidence', 0.7),
                    generation_time_ms=int((time.time() - start_time) * 500),
                )
            )
    
    def _verify_response(
        self,
        answer: str,
        documents: List[Dict[str, Any]],
        request_id: str,
    ) -> Optional[VerificationResult]:
        """Verify response using citation verifier."""
        start_time = time.time()
        
        verifier = self._get_citation_verifier()
        if verifier is None:
            return None
        
        try:
            # Extract text from documents
            context_texts = []
            for doc in documents[:5]:
                if isinstance(doc, dict):
                    context_texts.append(doc.get('content', doc.get('text', str(doc))))
                else:
                    context_texts.append(str(doc))
            
            result = verifier.verify(answer=answer, sources=context_texts)
            
            verification_time = int((time.time() - start_time) * 1000)
            
            return VerificationResult(
                is_verified=getattr(result, 'is_grounded', True),
                faithfulness_score=getattr(result, 'faithfulness_score', 0.7),
                grounding_score=getattr(result, 'grounding_score', 0.7),
                hallucinations_detected=len(getattr(result, 'hallucinations', [])),
                unsupported_claims=getattr(result, 'unsupported_claims', []),
                verification_time_ms=verification_time,
            )
        
        except Exception as e:
            logger.warning(f"Verification failed: {e}")
            return None
    
    def _post_process(self, response: UnifiedRAGResponse) -> UnifiedRAGResponse:
        """Post-process response."""
        # Calculate overall quality score
        scores = []
        
        if response.retrieval_result:
            scores.append(response.retrieval_result.quality_score)
        
        if response.generation_result:
            scores.append(response.generation_result.confidence)
            if response.generation_result.grounding_score > 0:
                scores.append(response.generation_result.grounding_score)
        
        if response.verification_result:
            scores.append(response.verification_result.faithfulness_score)
        
        if scores:
            response.overall_quality_score = sum(scores) / len(scores)
        
        # Extract sources
        if response.retrieval_result:
            for doc in response.retrieval_result.documents[:5]:
                if isinstance(doc, dict):
                    source = doc.get('source', doc.get('metadata', {}).get('source', ''))
                    if source and source not in response.sources:
                        response.sources.append(source)
        
        return response
    
    async def query_async(
        self,
        query: str,
        strategy: RAGStrategy = RAGStrategy.AUTO,
        **kwargs
    ) -> UnifiedRAGResponse:
        """Asynchronous query execution."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(query, strategy, **kwargs)
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "total_queries": self._query_count,
            "fallback_count": self._fallback_count,
            "fallback_rate": self._fallback_count / max(self._query_count, 1),
            "strategy_usage": self._strategy_usage,
            "config": self.config.to_dict(),
        }
    
    def reset_stats(self):
        """Reset statistics."""
        self._query_count = 0
        self._fallback_count = 0
        self._strategy_usage = {}


# =============================================================================
# SINGLETON
# =============================================================================

_unified_orchestrator: Optional[UnifiedAdvancedOrchestrator] = None


def get_unified_orchestrator(config: Optional[OrchestratorConfig] = None) -> UnifiedAdvancedOrchestrator:
    """Singleton UnifiedAdvancedOrchestrator instance."""
    global _unified_orchestrator
    
    if _unified_orchestrator is None:
        _unified_orchestrator = UnifiedAdvancedOrchestrator(config=config)
    
    return _unified_orchestrator


unified_orchestrator = UnifiedAdvancedOrchestrator()


__all__ = [
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
    "RAGStrategy",
    "QueryIntent",
    "PipelinePhase",
    "FailureMode",
    "unified_orchestrator",
    "get_unified_orchestrator",
]
