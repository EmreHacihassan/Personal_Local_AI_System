"""
🔀 Mixture of Experts Query Router
=================================

Akıllı query routing sistemi ile en uygun model/pipeline seçimi.

Features:
- Multi-model routing (local/cloud)
- Complexity-based selection
- Cost optimization
- Latency optimization
- Quality prediction
- Automatic fallback
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class ExpertType(str, Enum):
    """Types of expert models/pipelines"""
    LOCAL_SMALL = "local_small"  # Fast, simple queries
    LOCAL_LARGE = "local_large"  # Complex local queries
    CLOUD_FAST = "cloud_fast"  # GPT-3.5, Claude Haiku
    CLOUD_SMART = "cloud_smart"  # GPT-4, Claude Sonnet
    CLOUD_BEST = "cloud_best"  # GPT-4o, Claude Opus
    RAG_SIMPLE = "rag_simple"  # Basic RAG
    RAG_ADVANCED = "rag_advanced"  # CRAG
    CODE_EXPERT = "code_expert"  # Code-specialized
    MATH_EXPERT = "math_expert"  # Math-specialized
    CREATIVE = "creative"  # Creative writing


class QueryComplexity(str, Enum):
    """Query complexity levels"""
    TRIVIAL = "trivial"  # Yes/no, simple facts
    SIMPLE = "simple"  # Straightforward questions
    MODERATE = "moderate"  # Multi-step reasoning
    COMPLEX = "complex"  # Deep analysis
    EXPERT = "expert"  # Requires specialized knowledge


class RoutingStrategy(str, Enum):
    """Routing optimization strategies"""
    QUALITY = "quality"  # Best quality
    SPEED = "speed"  # Fastest response
    COST = "cost"  # Cheapest option
    BALANCED = "balanced"  # Balance all factors


# ============ DATA MODELS ============

class ExpertConfig(BaseModel):
    """Configuration for an expert"""
    expert_type: ExpertType
    name: str
    model: str
    handler: Optional[str] = None  # Function name to call
    capabilities: List[str] = Field(default_factory=list)
    avg_latency_ms: float = 1000
    cost_per_1k_tokens: float = 0.0
    quality_score: float = 0.7
    max_tokens: int = 4000
    supports_streaming: bool = True
    is_available: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryFeatures(BaseModel):
    """Extracted features from a query"""
    text: str
    length: int
    word_count: int
    complexity: QueryComplexity
    query_type: str  # question, command, creative, etc.
    domain: str  # general, code, math, etc.
    requires_reasoning: bool = False
    requires_knowledge: bool = False
    requires_creativity: bool = False
    requires_code: bool = False
    requires_math: bool = False
    language: str = "en"
    estimated_tokens: int = 0
    keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)


class RoutingDecision(BaseModel):
    """Routing decision with explanation"""
    selected_expert: ExpertType
    expert_config: Optional[ExpertConfig] = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    reasoning: str = ""
    alternatives: List[Tuple[ExpertType, float]] = Field(default_factory=list)
    query_features: Optional[QueryFeatures] = None
    estimated_latency_ms: float = 0
    estimated_cost: float = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoutingResult(BaseModel):
    """Result of routing and execution"""
    decision: RoutingDecision
    response: str
    actual_latency_ms: float
    actual_tokens: int = 0
    success: bool = True
    error: Optional[str] = None
    fallback_used: bool = False
    fallback_expert: Optional[ExpertType] = None


# ============ QUERY ANALYZER ============

class QueryAnalyzer:
    """
    Analyze queries to extract routing features.
    """
    
    def __init__(self):
        # Pattern definitions
        self.code_patterns = [
            r'\b(code|function|class|def|import|variable|bug|error|exception)\b',
            r'```',
            r'\b(python|javascript|java|c\+\+|rust|go|sql)\b',
        ]
        
        self.math_patterns = [
            r'\b(calculate|compute|solve|equation|formula|integral|derivative)\b',
            r'[\d+\-*/^=()]+',
            r'\b(sum|average|mean|median|probability|statistics)\b',
        ]
        
        self.creative_patterns = [
            r'\b(write|story|poem|creative|imagine|describe|generate)\b',
            r'\b(blog|article|essay|narrative)\b',
        ]
        
        self.reasoning_patterns = [
            r'\b(why|how|explain|analyze|compare|evaluate|reason)\b',
            r'\b(because|therefore|however|although)\b',
        ]
        
        self.knowledge_patterns = [
            r'\b(what is|who is|when did|where is|define|describe)\b',
            r'\b(history|science|geography|politics)\b',
        ]
    
    def analyze(self, query: str) -> QueryFeatures:
        """Extract features from query"""
        query_lower = query.lower()
        words = query.split()
        
        # Basic features
        length = len(query)
        word_count = len(words)
        
        # Detect query type
        if query.endswith("?"):
            query_type = "question"
        elif any(w in query_lower for w in ["write", "create", "generate"]):
            query_type = "creative"
        elif any(w in query_lower for w in ["do", "make", "execute"]):
            query_type = "command"
        else:
            query_type = "statement"
        
        # Detect domain requirements
        requires_code = any(
            re.search(p, query_lower) for p in self.code_patterns
        )
        requires_math = any(
            re.search(p, query_lower) for p in self.math_patterns
        )
        requires_creativity = any(
            re.search(p, query_lower) for p in self.creative_patterns
        )
        requires_reasoning = any(
            re.search(p, query_lower) for p in self.reasoning_patterns
        )
        requires_knowledge = any(
            re.search(p, query_lower) for p in self.knowledge_patterns
        )
        
        # Determine domain
        if requires_code:
            domain = "code"
        elif requires_math:
            domain = "math"
        elif requires_creativity:
            domain = "creative"
        else:
            domain = "general"
        
        # Estimate complexity
        complexity = self._estimate_complexity(
            word_count=word_count,
            requires_reasoning=requires_reasoning,
            requires_code=requires_code,
            requires_math=requires_math
        )
        
        # Extract keywords (simple approach)
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why"}
        keywords = [w.lower() for w in words if len(w) > 3 and w.lower() not in stop_words][:10]
        
        return QueryFeatures(
            text=query,
            length=length,
            word_count=word_count,
            complexity=complexity,
            query_type=query_type,
            domain=domain,
            requires_reasoning=requires_reasoning,
            requires_knowledge=requires_knowledge,
            requires_creativity=requires_creativity,
            requires_code=requires_code,
            requires_math=requires_math,
            estimated_tokens=word_count * 2,  # Rough estimate
            keywords=keywords
        )
    
    def _estimate_complexity(
        self,
        word_count: int,
        requires_reasoning: bool,
        requires_code: bool,
        requires_math: bool
    ) -> QueryComplexity:
        """Estimate query complexity"""
        score = 0
        
        # Length factor
        if word_count < 10:
            score += 1
        elif word_count < 30:
            score += 2
        elif word_count < 100:
            score += 3
        else:
            score += 4
        
        # Requirement factors
        if requires_reasoning:
            score += 2
        if requires_code:
            score += 1
        if requires_math:
            score += 1
        
        # Map to complexity level
        if score <= 2:
            return QueryComplexity.TRIVIAL
        elif score <= 4:
            return QueryComplexity.SIMPLE
        elif score <= 6:
            return QueryComplexity.MODERATE
        elif score <= 8:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.EXPERT


# ============ MOE ROUTER ============

class MoERouter:
    """
    Mixture of Experts Router.
    
    Routes queries to the most appropriate expert based on:
    - Query complexity
    - Domain requirements
    - Cost constraints
    - Latency requirements
    - Quality requirements
    """
    
    def __init__(
        self,
        experts: Optional[List[ExpertConfig]] = None,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        default_expert: ExpertType = ExpertType.LOCAL_LARGE
    ):
        self.strategy = strategy
        self.default_expert = default_expert
        self.analyzer = QueryAnalyzer()
        
        # Initialize experts
        self.experts: Dict[ExpertType, ExpertConfig] = {}
        if experts:
            for expert in experts:
                self.experts[expert.expert_type] = expert
        else:
            self._init_default_experts()
        
        # Expert handlers
        self.handlers: Dict[ExpertType, Callable] = {}
        
        # Routing history for learning
        self.routing_history: List[Dict] = []
    
    def _init_default_experts(self):
        """Initialize default expert configurations"""
        defaults = [
            ExpertConfig(
                expert_type=ExpertType.LOCAL_SMALL,
                name="Llama 3.2 3B",
                model="llama3.2:3b",
                capabilities=["simple_qa", "classification", "summarization"],
                avg_latency_ms=200,
                cost_per_1k_tokens=0.0,
                quality_score=0.6,
                max_tokens=2000
            ),
            ExpertConfig(
                expert_type=ExpertType.LOCAL_LARGE,
                name="Llama 3.2",
                model="llama3.2",
                capabilities=["reasoning", "analysis", "creative", "code"],
                avg_latency_ms=500,
                cost_per_1k_tokens=0.0,
                quality_score=0.75,
                max_tokens=4000
            ),
            ExpertConfig(
                expert_type=ExpertType.CLOUD_FAST,
                name="GPT-3.5 Turbo",
                model="gpt-3.5-turbo",
                capabilities=["general", "code", "fast_response"],
                avg_latency_ms=800,
                cost_per_1k_tokens=0.002,
                quality_score=0.8,
                max_tokens=4000
            ),
            ExpertConfig(
                expert_type=ExpertType.CLOUD_SMART,
                name="GPT-4",
                model="gpt-4",
                capabilities=["complex_reasoning", "analysis", "code", "math"],
                avg_latency_ms=2000,
                cost_per_1k_tokens=0.06,
                quality_score=0.95,
                max_tokens=8000
            ),
            ExpertConfig(
                expert_type=ExpertType.RAG_SIMPLE,
                name="Basic RAG",
                model="llama3.2",
                capabilities=["knowledge_retrieval", "qa"],
                avg_latency_ms=1000,
                cost_per_1k_tokens=0.0,
                quality_score=0.7,
                max_tokens=4000
            ),
            ExpertConfig(
                expert_type=ExpertType.RAG_ADVANCED,
                name="CRAG Pipeline",
                model="llama3.2",
                capabilities=["knowledge_retrieval", "qa", "correction"],
                avg_latency_ms=2000,
                cost_per_1k_tokens=0.0,
                quality_score=0.85,
                max_tokens=4000
            ),
            ExpertConfig(
                expert_type=ExpertType.CODE_EXPERT,
                name="Code Llama",
                model="codellama",
                capabilities=["code_generation", "code_review", "debugging"],
                avg_latency_ms=600,
                cost_per_1k_tokens=0.0,
                quality_score=0.8,
                max_tokens=4000
            ),
        ]
        
        for expert in defaults:
            self.experts[expert.expert_type] = expert
    
    def register_handler(
        self,
        expert_type: ExpertType,
        handler: Callable[[str], str]
    ):
        """Register a handler for an expert type"""
        self.handlers[expert_type] = handler
    
    def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a query to the best expert.
        
        Args:
            query: User query
            context: Additional context (history, user preferences)
            constraints: Constraints (max_latency, max_cost)
            
        Returns:
            RoutingDecision
        """
        context = context or {}
        constraints = constraints or {}
        
        # Analyze query
        features = self.analyzer.analyze(query)
        
        # Score each expert
        expert_scores: List[Tuple[ExpertType, float]] = []
        
        for expert_type, expert in self.experts.items():
            if not expert.is_available:
                continue
            
            score = self._score_expert(expert, features, constraints)
            expert_scores.append((expert_type, score))
        
        # Sort by score
        expert_scores.sort(key=lambda x: -x[1])
        
        if not expert_scores:
            # Fallback to default
            return RoutingDecision(
                selected_expert=self.default_expert,
                confidence=0.3,
                reasoning="No suitable expert found, using default",
                query_features=features
            )
        
        # Select best expert
        best_expert, best_score = expert_scores[0]
        expert_config = self.experts[best_expert]
        
        # Build reasoning
        reasoning = self._build_reasoning(features, best_expert, best_score)
        
        return RoutingDecision(
            selected_expert=best_expert,
            expert_config=expert_config,
            confidence=min(1.0, best_score),
            reasoning=reasoning,
            alternatives=expert_scores[1:4],
            query_features=features,
            estimated_latency_ms=expert_config.avg_latency_ms,
            estimated_cost=self._estimate_cost(expert_config, features)
        )
    
    def _score_expert(
        self,
        expert: ExpertConfig,
        features: QueryFeatures,
        constraints: Dict[str, Any]
    ) -> float:
        """Score an expert for the given query"""
        score = 0.0
        
        # 1. Capability match (40%)
        capability_score = self._score_capabilities(expert, features)
        score += capability_score * 0.4
        
        # 2. Quality vs complexity match (30%)
        quality_score = self._score_quality(expert, features)
        score += quality_score * 0.3
        
        # 3. Strategy-based scoring (30%)
        strategy_score = self._score_strategy(expert, features, constraints)
        score += strategy_score * 0.3
        
        return score
    
    def _score_capabilities(
        self,
        expert: ExpertConfig,
        features: QueryFeatures
    ) -> float:
        """Score expert capabilities for query requirements"""
        required = []
        
        if features.requires_code:
            required.append("code")
        if features.requires_math:
            required.append("math")
        if features.requires_creativity:
            required.append("creative")
        if features.requires_reasoning:
            required.append("reasoning")
        if features.requires_knowledge:
            required.append("knowledge_retrieval")
        
        if not required:
            required = ["general"]
        
        # Check how many requirements are met
        capabilities_lower = [c.lower() for c in expert.capabilities]
        matches = sum(
            1 for r in required 
            if any(r in c for c in capabilities_lower)
        )
        
        return matches / len(required) if required else 0.5
    
    def _score_quality(
        self,
        expert: ExpertConfig,
        features: QueryFeatures
    ) -> float:
        """Score expert quality vs required complexity"""
        complexity_requirements = {
            QueryComplexity.TRIVIAL: 0.4,
            QueryComplexity.SIMPLE: 0.5,
            QueryComplexity.MODERATE: 0.7,
            QueryComplexity.COMPLEX: 0.85,
            QueryComplexity.EXPERT: 0.95
        }
        
        required_quality = complexity_requirements[features.complexity]
        
        # Expert quality should be >= required
        if expert.quality_score >= required_quality:
            # But not too much overkill for simple queries
            overkill = expert.quality_score - required_quality
            return 1.0 - (overkill * 0.3)  # Slight penalty for overkill
        else:
            # Under-qualified
            deficit = required_quality - expert.quality_score
            return max(0.0, 1.0 - deficit * 2)
    
    def _score_strategy(
        self,
        expert: ExpertConfig,
        features: QueryFeatures,
        constraints: Dict[str, Any]
    ) -> float:
        """Score based on routing strategy"""
        if self.strategy == RoutingStrategy.QUALITY:
            return expert.quality_score
        
        elif self.strategy == RoutingStrategy.SPEED:
            # Lower latency = higher score
            max_latency = 3000
            return 1.0 - (expert.avg_latency_ms / max_latency)
        
        elif self.strategy == RoutingStrategy.COST:
            # Lower cost = higher score
            if expert.cost_per_1k_tokens == 0:
                return 1.0
            max_cost = 0.1
            return 1.0 - (expert.cost_per_1k_tokens / max_cost)
        
        else:  # BALANCED
            quality_factor = expert.quality_score * 0.4
            speed_factor = (1.0 - expert.avg_latency_ms / 3000) * 0.3
            cost_factor = (1.0 - min(1.0, expert.cost_per_1k_tokens / 0.1)) * 0.3
            return quality_factor + speed_factor + cost_factor
    
    def _build_reasoning(
        self,
        features: QueryFeatures,
        selected: ExpertType,
        score: float
    ) -> str:
        """Build human-readable reasoning for selection"""
        parts = []
        
        parts.append(f"Query complexity: {features.complexity.value}")
        parts.append(f"Domain: {features.domain}")
        
        if features.requires_code:
            parts.append("Requires code expertise")
        if features.requires_math:
            parts.append("Requires math expertise")
        if features.requires_reasoning:
            parts.append("Requires reasoning")
        
        parts.append(f"Selected {selected.value} with confidence {score:.0%}")
        
        return "; ".join(parts)
    
    def _estimate_cost(
        self,
        expert: ExpertConfig,
        features: QueryFeatures
    ) -> float:
        """Estimate cost for this query"""
        estimated_tokens = features.estimated_tokens + 500  # Output tokens
        return (estimated_tokens / 1000) * expert.cost_per_1k_tokens
    
    async def route_and_execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> RoutingResult:
        """
        Route query and execute with selected expert.
        
        Includes automatic fallback on failure.
        """
        decision = self.route(query, context, constraints)
        
        start_time = time.time()
        
        # Try selected expert
        handler = self.handlers.get(decision.selected_expert)
        
        if handler:
            try:
                response = handler(query)
                latency = (time.time() - start_time) * 1000
                
                return RoutingResult(
                    decision=decision,
                    response=response,
                    actual_latency_ms=latency,
                    success=True
                )
                
            except Exception as e:
                logger.warning(f"Expert {decision.selected_expert} failed: {e}")
                
                # Try fallback
                for alt_expert, _ in decision.alternatives:
                    alt_handler = self.handlers.get(alt_expert)
                    if alt_handler:
                        try:
                            response = alt_handler(query)
                            latency = (time.time() - start_time) * 1000
                            
                            return RoutingResult(
                                decision=decision,
                                response=response,
                                actual_latency_ms=latency,
                                success=True,
                                fallback_used=True,
                                fallback_expert=alt_expert
                            )
                        except Exception:
                            continue
        
        # All failed
        return RoutingResult(
            decision=decision,
            response="",
            actual_latency_ms=(time.time() - start_time) * 1000,
            success=False,
            error="No available handler could process the query"
        )


# ============ ADAPTIVE ROUTER ============

class AdaptiveMoERouter(MoERouter):
    """
    Adaptive router that learns from feedback.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feedback_history: List[Dict] = []
        self.expert_performance: Dict[ExpertType, Dict] = {}
    
    def record_feedback(
        self,
        decision: RoutingDecision,
        user_rating: float,  # 0-1
        actual_quality: float,  # 0-1
        actual_latency: float
    ):
        """Record feedback to improve routing"""
        feedback = {
            "expert": decision.selected_expert,
            "query_features": decision.query_features.model_dump() if decision.query_features else {},
            "user_rating": user_rating,
            "actual_quality": actual_quality,
            "actual_latency": actual_latency,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_history.append(feedback)
        
        # Update expert performance stats
        expert = decision.selected_expert
        if expert not in self.expert_performance:
            self.expert_performance[expert] = {
                "total_queries": 0,
                "avg_rating": 0.5,
                "avg_quality": 0.5,
                "avg_latency": 1000
            }
        
        stats = self.expert_performance[expert]
        n = stats["total_queries"]
        
        # Running average update
        stats["avg_rating"] = (stats["avg_rating"] * n + user_rating) / (n + 1)
        stats["avg_quality"] = (stats["avg_quality"] * n + actual_quality) / (n + 1)
        stats["avg_latency"] = (stats["avg_latency"] * n + actual_latency) / (n + 1)
        stats["total_queries"] = n + 1
        
        # Update expert config based on feedback
        if expert in self.experts:
            config = self.experts[expert]
            # Adjust quality score slowly
            config.quality_score = config.quality_score * 0.9 + stats["avg_quality"] * 0.1
            config.avg_latency_ms = config.avg_latency_ms * 0.9 + stats["avg_latency"] * 0.1


# ============ EXPORTS ============

__all__ = [
    # Types
    "ExpertType",
    "QueryComplexity",
    "RoutingStrategy",
    # Models
    "ExpertConfig",
    "QueryFeatures",
    "RoutingDecision",
    "RoutingResult",
    # Classes
    "QueryAnalyzer",
    "MoERouter",
    "AdaptiveMoERouter",
]
