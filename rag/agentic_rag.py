"""
Agentic RAG System
==================

Akıllı, otonom strateji seçimi yapan gelişmiş RAG sistemi.

Features:
- Query Complexity Analysis
- Dynamic Strategy Selection
- Multi-Step Planning
- Adaptive Retrieval
- Tool-Augmented Reasoning
- Self-Correction Loop
- Trace & Explainability

Enterprise-grade implementation with full observability.

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    Union,
)

from core.logger import get_logger

logger = get_logger("rag.agentic")


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class QueryComplexity(Enum):
    """Sorgu karmaşıklık seviyeleri."""
    SIMPLE = "simple"           # Tek hop, doğrudan cevap
    MODERATE = "moderate"       # 2-3 hop, basit reasoning
    COMPLEX = "complex"         # Multi-hop, karşılaştırma
    ANALYTICAL = "analytical"   # Analiz, synthesis gerektiren
    EXPERT = "expert"           # Domain expertise gerektiren


class StrategyType(Enum):
    """RAG strateji türleri."""
    DIRECT = "direct"                   # Doğrudan semantic search
    HYDE = "hyde"                       # Hypothetical Document Embeddings
    MULTI_QUERY = "multi_query"         # Query expansion
    STEP_BACK = "step_back"             # Abstract reasoning
    DECOMPOSE = "decompose"             # Question decomposition
    ITERATIVE = "iterative"             # Iterative refinement
    COMPARATIVE = "comparative"         # Karşılaştırmalı analiz
    TEMPORAL = "temporal"               # Zaman bazlı sıralama
    HIERARCHICAL = "hierarchical"       # Parent-child traversal
    GRAPH = "graph"                     # Knowledge graph traversal


class ActionType(Enum):
    """Agent action türleri."""
    RETRIEVE = "retrieve"               # Bilgi getir
    REASON = "reason"                   # Mantık yürüt
    SYNTHESIZE = "synthesize"           # Bilgileri birleştir
    VALIDATE = "validate"               # Doğrula
    REFINE = "refine"                   # İyileştir
    DECOMPOSE = "decompose"             # Parçalara ayır
    COMPARE = "compare"                 # Karşılaştır
    SUMMARIZE = "summarize"             # Özetle
    FINISH = "finish"                   # Tamamla


class AgentState(Enum):
    """Agent durumları."""
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    REFINING = "refining"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QueryAnalysis:
    """Sorgu analiz sonucu."""
    original_query: str
    complexity: QueryComplexity
    query_type: str
    intent: str
    entities: List[str]
    keywords: List[str]
    required_hops: int
    needs_comparison: bool
    needs_temporal: bool
    needs_aggregation: bool
    confidence: float
    recommended_strategies: List[StrategyType]
    sub_questions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "original_query": self.original_query,
            "complexity": self.complexity.value,
            "query_type": self.query_type,
            "intent": self.intent,
            "entities": self.entities,
            "keywords": self.keywords,
            "required_hops": self.required_hops,
            "needs_comparison": self.needs_comparison,
            "needs_temporal": self.needs_temporal,
            "needs_aggregation": self.needs_aggregation,
            "confidence": self.confidence,
            "recommended_strategies": [s.value for s in self.recommended_strategies],
            "sub_questions": self.sub_questions,
        }


@dataclass
class AgentAction:
    """Tek bir agent aksiyonu."""
    action_id: str
    action_type: ActionType
    description: str
    input_data: Dict[str, Any]
    strategy: Optional[StrategyType] = None
    expected_output: str = ""
    dependencies: List[str] = field(default_factory=list)
    
    # Execution results
    status: str = "pending"
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "description": self.description,
            "strategy": self.strategy.value if self.strategy else None,
            "status": self.status,
            "execution_time_ms": self.execution_time_ms,
            "has_output": self.output is not None,
            "error": self.error,
        }


@dataclass
class AgentPlan:
    """Agent execution planı."""
    plan_id: str
    query: str
    analysis: QueryAnalysis
    actions: List[AgentAction]
    created_at: datetime = field(default_factory=datetime.now)
    
    # Execution tracking
    current_action_idx: int = 0
    state: AgentState = AgentState.PLANNING
    iterations: int = 0
    max_iterations: int = 5
    
    def get_current_action(self) -> Optional[AgentAction]:
        if self.current_action_idx < len(self.actions):
            return self.actions[self.current_action_idx]
        return None
    
    def advance(self):
        self.current_action_idx += 1
        if self.current_action_idx >= len(self.actions):
            self.state = AgentState.COMPLETED
    
    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "query": self.query,
            "analysis": self.analysis.to_dict(),
            "actions": [a.to_dict() for a in self.actions],
            "state": self.state.value,
            "current_action": self.current_action_idx,
            "iterations": self.iterations,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgenticResult:
    """Agentic RAG sonucu."""
    query: str
    response: str
    confidence: float
    plan: AgentPlan
    chunks: List[Any]
    citations: List[Dict]
    
    # Execution metadata
    total_time_ms: int = 0
    strategies_used: List[str] = field(default_factory=list)
    iterations: int = 0
    trace_id: str = ""
    
    # Quality metrics
    relevance_score: Optional[float] = None
    coherence_score: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "response": self.response,
            "confidence": self.confidence,
            "plan": self.plan.to_dict(),
            "chunks_count": len(self.chunks),
            "citations": self.citations,
            "total_time_ms": self.total_time_ms,
            "strategies_used": self.strategies_used,
            "iterations": self.iterations,
            "trace_id": self.trace_id,
            "relevance_score": self.relevance_score,
            "coherence_score": self.coherence_score,
        }


# =============================================================================
# PROTOCOLS
# =============================================================================

class LLMProtocol(Protocol):
    """LLM arayüz protokolü."""
    
    def generate(self, prompt: str, **kwargs) -> str:
        ...
    
    async def generate_async(self, prompt: str, **kwargs) -> str:
        ...


class RetrieverProtocol(Protocol):
    """Retriever arayüz protokolü."""
    
    def search(self, query: str, top_k: int = 5, **kwargs) -> List[Any]:
        ...
    
    async def search_async(self, query: str, top_k: int = 5, **kwargs) -> List[Any]:
        ...


# =============================================================================
# QUERY ANALYZER
# =============================================================================

class AgenticQueryAnalyzer:
    """
    Gelişmiş sorgu analizi.
    
    - Complexity detection
    - Intent classification  
    - Entity extraction
    - Strategy recommendation
    - Sub-question generation
    """
    
    # Complexity indicators
    COMPLEX_INDICATORS = {
        "compare": ["karşılaştır", "fark", "vs", "versus", "arasındaki", "compare", "difference"],
        "temporal": ["önce", "sonra", "sırasında", "when", "before", "after", "during", "tarih"],
        "aggregation": ["toplam", "ortalama", "en çok", "en az", "total", "average", "most", "least"],
        "multi_hop": ["neden", "nasıl", "açıkla", "why", "how", "explain", "ilişki", "bağlantı"],
        "analytical": ["analiz", "değerlendir", "analyze", "evaluate", "incele", "yorumla"],
    }
    
    # Intent patterns
    INTENT_PATTERNS = {
        "definition": ["nedir", "ne demek", "tanımı", "what is", "define"],
        "explanation": ["nasıl", "neden", "açıkla", "how", "why", "explain"],
        "comparison": ["karşılaştır", "fark", "compare", "vs", "versus"],
        "listing": ["listele", "say", "sırala", "list", "enumerate"],
        "summarization": ["özetle", "özet", "summarize", "brief"],
        "fact_check": ["doğru mu", "gerçek mi", "is it true", "verify"],
    }
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def analyze(self, query: str) -> QueryAnalysis:
        """Sorguyu kapsamlı analiz et."""
        query_lower = query.lower()
        
        # 1. Complexity detection
        complexity = self._detect_complexity(query_lower)
        
        # 2. Intent classification
        intent = self._classify_intent(query_lower)
        
        # 3. Feature detection
        needs_comparison = any(
            ind in query_lower 
            for ind in self.COMPLEX_INDICATORS["compare"]
        )
        needs_temporal = any(
            ind in query_lower 
            for ind in self.COMPLEX_INDICATORS["temporal"]
        )
        needs_aggregation = any(
            ind in query_lower 
            for ind in self.COMPLEX_INDICATORS["aggregation"]
        )
        
        # 4. Entity extraction (basit)
        entities = self._extract_entities(query)
        
        # 5. Keyword extraction
        keywords = self._extract_keywords(query)
        
        # 6. Required hops estimation
        required_hops = self._estimate_hops(complexity, needs_comparison, needs_aggregation)
        
        # 7. Strategy recommendation
        strategies = self._recommend_strategies(
            complexity, intent, needs_comparison, needs_temporal
        )
        
        # 8. Query type
        query_type = self._determine_query_type(intent, complexity)
        
        # 9. Sub-questions (for complex queries)
        sub_questions = []
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.ANALYTICAL, QueryComplexity.EXPERT]:
            sub_questions = self._generate_sub_questions(query)
        
        return QueryAnalysis(
            original_query=query,
            complexity=complexity,
            query_type=query_type,
            intent=intent,
            entities=entities,
            keywords=keywords,
            required_hops=required_hops,
            needs_comparison=needs_comparison,
            needs_temporal=needs_temporal,
            needs_aggregation=needs_aggregation,
            confidence=0.8,
            recommended_strategies=strategies,
            sub_questions=sub_questions,
        )
    
    def _detect_complexity(self, query: str) -> QueryComplexity:
        """Sorgu karmaşıklığını tespit et."""
        score = 0
        
        # Indicator-based scoring
        for category, indicators in self.COMPLEX_INDICATORS.items():
            if any(ind in query for ind in indicators):
                score += 1
        
        # Length-based adjustment
        word_count = len(query.split())
        if word_count > 20:
            score += 1
        if word_count > 40:
            score += 1
        
        # Question count
        question_marks = query.count("?")
        if question_marks > 1:
            score += question_marks - 1
        
        # Map score to complexity
        if score <= 0:
            return QueryComplexity.SIMPLE
        elif score <= 1:
            return QueryComplexity.MODERATE
        elif score <= 2:
            return QueryComplexity.COMPLEX
        elif score <= 3:
            return QueryComplexity.ANALYTICAL
        else:
            return QueryComplexity.EXPERT
    
    def _classify_intent(self, query: str) -> str:
        """Intent sınıflandırması."""
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                return intent
        return "information_seeking"
    
    def _extract_entities(self, query: str) -> List[str]:
        """Basit entity extraction."""
        # Büyük harfle başlayan kelimeleri al (proper nouns)
        words = query.split()
        entities = []
        
        for i, word in enumerate(words):
            # İlk kelime değilse ve büyük harfle başlıyorsa
            if i > 0 and word[0].isupper():
                clean_word = word.strip(".,?!:;\"'")
                if len(clean_word) > 2:
                    entities.append(clean_word)
        
        return list(set(entities))
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Keyword extraction."""
        stopwords = {
            "bir", "bu", "şu", "ve", "ile", "için", "ne", "nasıl", "neden",
            "kim", "hangi", "kaç", "the", "a", "an", "is", "are", "was",
            "were", "what", "how", "why", "when", "where", "mi", "mu", "mı"
        }
        
        words = query.lower().split()
        keywords = [
            w.strip(".,?!:;\"'") 
            for w in words 
            if len(w) > 2 and w.strip(".,?!:;\"'") not in stopwords
        ]
        
        return keywords[:10]  # Top 10
    
    def _estimate_hops(
        self,
        complexity: QueryComplexity,
        needs_comparison: bool,
        needs_aggregation: bool
    ) -> int:
        """Gereken hop sayısını tahmin et."""
        base_hops = {
            QueryComplexity.SIMPLE: 1,
            QueryComplexity.MODERATE: 2,
            QueryComplexity.COMPLEX: 3,
            QueryComplexity.ANALYTICAL: 4,
            QueryComplexity.EXPERT: 5,
        }
        
        hops = base_hops.get(complexity, 1)
        
        if needs_comparison:
            hops += 1
        if needs_aggregation:
            hops += 1
        
        return min(hops, 5)
    
    def _recommend_strategies(
        self,
        complexity: QueryComplexity,
        intent: str,
        needs_comparison: bool,
        needs_temporal: bool
    ) -> List[StrategyType]:
        """Strateji önerisi."""
        strategies = []
        
        # Complexity-based
        if complexity == QueryComplexity.SIMPLE:
            strategies.append(StrategyType.DIRECT)
        elif complexity == QueryComplexity.MODERATE:
            strategies.extend([StrategyType.HYDE, StrategyType.MULTI_QUERY])
        elif complexity == QueryComplexity.COMPLEX:
            strategies.extend([StrategyType.DECOMPOSE, StrategyType.ITERATIVE])
        elif complexity == QueryComplexity.ANALYTICAL:
            strategies.extend([StrategyType.STEP_BACK, StrategyType.DECOMPOSE])
        else:
            strategies.extend([StrategyType.DECOMPOSE, StrategyType.GRAPH, StrategyType.ITERATIVE])
        
        # Feature-based additions
        if needs_comparison:
            strategies.append(StrategyType.COMPARATIVE)
        if needs_temporal:
            strategies.append(StrategyType.TEMPORAL)
        
        # Intent-based
        if intent == "explanation":
            strategies.append(StrategyType.STEP_BACK)
        
        return list(set(strategies))[:4]  # Max 4 strategies
    
    def _determine_query_type(self, intent: str, complexity: QueryComplexity) -> str:
        """Query type belirle."""
        if complexity in [QueryComplexity.ANALYTICAL, QueryComplexity.EXPERT]:
            return "analytical"
        if intent in ["comparison"]:
            return "comparative"
        if intent in ["summarization"]:
            return "summarization"
        return "factual"
    
    def _generate_sub_questions(self, query: str) -> List[str]:
        """Karmaşık sorguları alt sorulara böl."""
        self._lazy_load()
        
        try:
            prompt = f"""Aşağıdaki karmaşık soruyu, cevaplamak için gereken alt sorulara böl.
Her alt soru bağımsız olarak cevaplanabilir olmalı.
Maksimum 4 alt soru üret.
Sadece soruları listele, açıklama yapma.

Soru: {query}

Alt Sorular:"""
            
            response = self._llm.generate(prompt, max_tokens=200)
            
            sub_questions = []
            for line in response.strip().split("\n"):
                line = line.strip().lstrip("0123456789.-) ")
                if line and "?" in line:
                    sub_questions.append(line)
            
            return sub_questions[:4]
        
        except Exception as e:
            logger.warning(f"Sub-question generation failed: {e}")
            return []


# =============================================================================
# PLANNER
# =============================================================================

class AgenticPlanner:
    """
    Agentic execution planner.
    
    Sorgu analizine göre execution planı oluşturur.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def create_plan(self, analysis: QueryAnalysis) -> AgentPlan:
        """Execution planı oluştur."""
        plan_id = str(uuid.uuid4())[:8]
        actions = []
        
        # 1. Her sub-question için retrieve action
        if analysis.sub_questions:
            for i, sub_q in enumerate(analysis.sub_questions):
                actions.append(AgentAction(
                    action_id=f"retrieve_{i+1}",
                    action_type=ActionType.RETRIEVE,
                    description=f"Retrieve for: {sub_q[:50]}...",
                    input_data={"query": sub_q},
                    strategy=analysis.recommended_strategies[0] if analysis.recommended_strategies else StrategyType.DIRECT,
                ))
            
            # Synthesize action
            actions.append(AgentAction(
                action_id="synthesize_1",
                action_type=ActionType.SYNTHESIZE,
                description="Synthesize sub-question results",
                input_data={"combine_results": True},
                dependencies=[f"retrieve_{i+1}" for i in range(len(analysis.sub_questions))],
            ))
        else:
            # Simple query - single retrieve
            primary_strategy = analysis.recommended_strategies[0] if analysis.recommended_strategies else StrategyType.DIRECT
            
            actions.append(AgentAction(
                action_id="retrieve_1",
                action_type=ActionType.RETRIEVE,
                description=f"Primary retrieval with {primary_strategy.value}",
                input_data={"query": analysis.original_query},
                strategy=primary_strategy,
            ))
        
        # 2. Comparison için ekstra action
        if analysis.needs_comparison:
            actions.append(AgentAction(
                action_id="compare_1",
                action_type=ActionType.COMPARE,
                description="Compare retrieved information",
                input_data={"compare_mode": True},
                dependencies=["retrieve_1"],
            ))
        
        # 3. Validation action (complex queries için)
        if analysis.complexity in [QueryComplexity.COMPLEX, QueryComplexity.ANALYTICAL, QueryComplexity.EXPERT]:
            actions.append(AgentAction(
                action_id="validate_1",
                action_type=ActionType.VALIDATE,
                description="Validate response quality",
                input_data={"quality_check": True},
            ))
        
        # 4. Final action
        actions.append(AgentAction(
            action_id="finish",
            action_type=ActionType.FINISH,
            description="Generate final response",
            input_data={"finalize": True},
        ))
        
        return AgentPlan(
            plan_id=plan_id,
            query=analysis.original_query,
            analysis=analysis,
            actions=actions,
            max_iterations=min(analysis.required_hops + 2, 7),
        )


# =============================================================================
# EXECUTOR
# =============================================================================

class AgenticExecutor:
    """
    Agentic plan executor.
    
    Planı adım adım execute eder.
    """
    
    def __init__(
        self,
        retriever: Optional[RetrieverProtocol] = None,
        llm: Optional[LLMProtocol] = None,
    ):
        self._retriever = retriever
        self._llm = llm
        
        # Execution context
        self._context: Dict[str, Any] = {}
        self._all_chunks: List[Any] = []
    
    def _lazy_load(self):
        if self._retriever is None:
            from rag.pipeline import rag_pipeline
            self._retriever = rag_pipeline
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def execute(self, plan: AgentPlan) -> AgenticResult:
        """Planı execute et."""
        self._lazy_load()
        
        start_time = time.time()
        trace_id = str(uuid.uuid4())[:12]
        
        self._context = {}
        self._all_chunks = []
        strategies_used = set()
        
        plan.state = AgentState.EXECUTING
        
        try:
            while plan.state == AgentState.EXECUTING:
                action = plan.get_current_action()
                
                if action is None:
                    plan.state = AgentState.COMPLETED
                    break
                
                # Check dependencies
                if action.dependencies:
                    deps_met = all(
                        self._context.get(f"{dep}_status") == "completed"
                        for dep in action.dependencies
                    )
                    if not deps_met:
                        action.error = "Dependencies not met"
                        action.status = "skipped"
                        plan.advance()
                        continue
                
                # Execute action
                action_start = time.time()
                
                try:
                    result = self._execute_action(action, plan)
                    action.output = result
                    action.status = "completed"
                    self._context[f"{action.action_id}_status"] = "completed"
                    self._context[f"{action.action_id}_result"] = result
                    
                    if action.strategy:
                        strategies_used.add(action.strategy.value)
                    
                except Exception as e:
                    action.error = str(e)
                    action.status = "failed"
                    logger.error(f"Action {action.action_id} failed: {e}")
                
                action.execution_time_ms = int((time.time() - action_start) * 1000)
                
                plan.advance()
                plan.iterations += 1
                
                # Iteration limit
                if plan.iterations >= plan.max_iterations:
                    plan.state = AgentState.COMPLETED
                    break
            
            # Generate final response
            final_response = self._generate_final_response(plan)
            confidence = self._calculate_confidence(plan)
            
            total_time = int((time.time() - start_time) * 1000)
            
            return AgenticResult(
                query=plan.query,
                response=final_response,
                confidence=confidence,
                plan=plan,
                chunks=self._all_chunks,
                citations=self._extract_citations(),
                total_time_ms=total_time,
                strategies_used=list(strategies_used),
                iterations=plan.iterations,
                trace_id=trace_id,
            )
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            plan.state = AgentState.FAILED
            
            return AgenticResult(
                query=plan.query,
                response=f"Execution failed: {str(e)}",
                confidence=0.0,
                plan=plan,
                chunks=[],
                citations=[],
                total_time_ms=int((time.time() - start_time) * 1000),
                trace_id=trace_id,
            )
    
    def _execute_action(self, action: AgentAction, plan: AgentPlan) -> Any:
        """Tek bir action'ı execute et."""
        if action.action_type == ActionType.RETRIEVE:
            return self._execute_retrieve(action)
        
        elif action.action_type == ActionType.REASON:
            return self._execute_reason(action)
        
        elif action.action_type == ActionType.SYNTHESIZE:
            return self._execute_synthesize(action, plan)
        
        elif action.action_type == ActionType.VALIDATE:
            return self._execute_validate(action, plan)
        
        elif action.action_type == ActionType.COMPARE:
            return self._execute_compare(action)
        
        elif action.action_type == ActionType.FINISH:
            return self._execute_finish(action, plan)
        
        else:
            return {"status": "unknown_action"}
    
    def _execute_retrieve(self, action: AgentAction) -> Dict:
        """Retrieve action."""
        query = action.input_data.get("query", "")
        top_k = action.input_data.get("top_k", 5)
        
        # Get strategy
        strategy = action.strategy or StrategyType.DIRECT
        
        # Map to retrieval strategy
        from rag.pipeline import RetrievalStrategy
        
        strategy_map = {
            StrategyType.DIRECT: RetrievalStrategy.SEMANTIC,
            StrategyType.HYDE: RetrievalStrategy.HYDE,
            StrategyType.MULTI_QUERY: RetrievalStrategy.MULTI_QUERY,
            StrategyType.DECOMPOSE: RetrievalStrategy.FUSION,
            StrategyType.ITERATIVE: RetrievalStrategy.FUSION,
            StrategyType.COMPARATIVE: RetrievalStrategy.HYBRID,
            StrategyType.HIERARCHICAL: RetrievalStrategy.PARENT_CHILD,
        }
        
        retrieval_strategy = strategy_map.get(strategy, RetrievalStrategy.SEMANTIC)
        
        # Execute retrieval
        context = self._retriever.retrieve(
            query=query,
            strategy=retrieval_strategy,
            top_k=top_k,
        )
        
        # Store chunks
        self._all_chunks.extend(context.chunks)
        
        return {
            "chunks_count": len(context.chunks),
            "strategy": retrieval_strategy.value,
            "context": context,
        }
    
    def _execute_reason(self, action: AgentAction) -> Dict:
        """Reasoning action."""
        context_text = action.input_data.get("context", "")
        question = action.input_data.get("question", "")
        
        prompt = f"""Based on the following context, reason about the answer:

Context: {context_text[:2000]}

Question: {question}

Reasoning:"""
        
        response = self._llm.generate(prompt, max_tokens=500)
        
        return {"reasoning": response}
    
    def _execute_synthesize(self, action: AgentAction, plan: AgentPlan) -> Dict:
        """Synthesize multiple results."""
        # Gather all retrieve results
        retrieve_results = []
        for a in plan.actions:
            if a.action_type == ActionType.RETRIEVE and a.output:
                retrieve_results.append(a.output)
        
        # Combine chunks
        all_chunks = []
        for result in retrieve_results:
            if "context" in result:
                all_chunks.extend(result["context"].chunks)
        
        # Deduplicate
        seen = set()
        unique_chunks = []
        for chunk in all_chunks:
            chunk_hash = hashlib.md5(chunk.content[:100].encode()).hexdigest()
            if chunk_hash not in seen:
                seen.add(chunk_hash)
                unique_chunks.append(chunk)
        
        return {
            "combined_chunks": len(unique_chunks),
            "chunks": unique_chunks[:10],  # Top 10
        }
    
    def _execute_validate(self, action: AgentAction, plan: AgentPlan) -> Dict:
        """Validate response quality."""
        # Check if we have enough context
        has_context = len(self._all_chunks) > 0
        
        # Check action success rate
        successful_actions = sum(1 for a in plan.actions if a.status == "completed")
        total_actions = len([a for a in plan.actions if a.status != "pending"])
        success_rate = successful_actions / max(total_actions, 1)
        
        return {
            "has_context": has_context,
            "success_rate": success_rate,
            "is_valid": has_context and success_rate > 0.5,
        }
    
    def _execute_compare(self, action: AgentAction) -> Dict:
        """Compare action."""
        # Get chunks for comparison
        chunks_to_compare = self._all_chunks[:6]
        
        if len(chunks_to_compare) < 2:
            return {"comparison": "Not enough data for comparison"}
        
        # Build comparison context
        context_parts = []
        for i, chunk in enumerate(chunks_to_compare):
            context_parts.append(f"Source {i+1}: {chunk.content[:500]}")
        
        prompt = f"""Compare the following sources and identify key similarities and differences:

{chr(10).join(context_parts)}

Comparison Analysis:"""
        
        response = self._llm.generate(prompt, max_tokens=400)
        
        return {"comparison": response}
    
    def _execute_finish(self, action: AgentAction, plan: AgentPlan) -> Dict:
        """Finish and prepare final response."""
        return {"finalized": True}
    
    def _generate_final_response(self, plan: AgentPlan) -> str:
        """Final response oluştur."""
        # Build context from all chunks
        if not self._all_chunks:
            return "İlgili bilgi bulunamadı."
        
        context_parts = []
        for i, chunk in enumerate(self._all_chunks[:5], 1):
            source = chunk.source or "Kaynak"
            context_parts.append(f"[{i}. {source}]: {chunk.content[:600]}")
        
        context_text = "\n\n".join(context_parts)
        
        # Generate answer
        prompt = f"""Aşağıdaki kaynaklara dayanarak soruyu cevapla.
Her önemli bilgi için kaynak numarası belirt.

KAYNAKLAR:
{context_text}

SORU: {plan.query}

CEVAP:"""
        
        response = self._llm.generate(prompt, max_tokens=800)
        
        return response
    
    def _calculate_confidence(self, plan: AgentPlan) -> float:
        """Confidence score hesapla."""
        # Factors
        has_chunks = len(self._all_chunks) > 0
        chunk_count_score = min(len(self._all_chunks) / 5, 1.0)
        
        successful_actions = sum(1 for a in plan.actions if a.status == "completed")
        success_rate = successful_actions / max(len(plan.actions), 1)
        
        # Weighted score
        confidence = (
            0.3 * (1.0 if has_chunks else 0.0) +
            0.3 * chunk_count_score +
            0.4 * success_rate
        )
        
        return round(confidence, 3)
    
    def _extract_citations(self) -> List[Dict]:
        """Citation'ları çıkar."""
        citations = []
        
        for chunk in self._all_chunks[:10]:
            citations.append({
                "source": chunk.source or "Unknown",
                "page": chunk.page_number,
                "snippet": chunk.content[:150] + "...",
                "score": round(chunk.score, 3),
            })
        
        return citations


# =============================================================================
# AGENTIC RAG - MAIN CLASS
# =============================================================================

class AgenticRAG:
    """
    Agentic RAG - Ana sınıf.
    
    Tüm bileşenleri koordine eder:
    - Query Analysis
    - Planning
    - Execution
    - Reflection
    
    Example:
        agentic = AgenticRAG()
        result = agentic.query("Compare the benefits of X and Y")
    """
    
    def __init__(
        self,
        retriever: Optional[RetrieverProtocol] = None,
        llm: Optional[LLMProtocol] = None,
        max_iterations: int = 5,
        quality_threshold: float = 0.6,
    ):
        """
        AgenticRAG başlat.
        
        Args:
            retriever: Retriever instance
            llm: LLM instance
            max_iterations: Maksimum iteration sayısı
            quality_threshold: Minimum kalite eşiği
        """
        self.analyzer = AgenticQueryAnalyzer(llm)
        self.planner = AgenticPlanner(llm)
        self.executor = AgenticExecutor(retriever, llm)
        
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        
        # Statistics
        self._query_count = 0
        self._total_time_ms = 0
        self._avg_confidence = 0.0
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        enable_reflection: bool = True,
    ) -> AgenticResult:
        """
        Agentic RAG sorgusu.
        
        Args:
            query: Kullanıcı sorgusu
            top_k: Döndürülecek chunk sayısı
            enable_reflection: Self-reflection aktif mi
            
        Returns:
            AgenticResult
        """
        logger.info(f"Agentic query: {query[:50]}...")
        
        # 1. Analyze query
        analysis = self.analyzer.analyze(query)
        logger.debug(f"Analysis: complexity={analysis.complexity.value}, strategies={[s.value for s in analysis.recommended_strategies]}")
        
        # 2. Create plan
        plan = self.planner.create_plan(analysis)
        logger.debug(f"Plan created: {len(plan.actions)} actions")
        
        # 3. Execute plan
        result = self.executor.execute(plan)
        
        # 4. Optional reflection & refinement
        if enable_reflection and result.confidence < self.quality_threshold:
            logger.info(f"Low confidence ({result.confidence}), attempting refinement...")
            result = self._refine_result(result)
        
        # 5. Update stats
        self._update_stats(result)
        
        logger.info(f"Agentic query completed: confidence={result.confidence}, time={result.total_time_ms}ms")
        
        return result
    
    async def query_async(
        self,
        query: str,
        top_k: int = 5,
        enable_reflection: bool = True,
    ) -> AgenticResult:
        """Asenkron agentic query."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(query, top_k, enable_reflection)
        )
    
    def _refine_result(self, result: AgenticResult) -> AgenticResult:
        """Düşük kaliteli sonucu iyileştir."""
        # Re-execute with different strategy
        analysis = result.plan.analysis
        
        # Try next strategy
        if len(analysis.recommended_strategies) > 1:
            new_strategies = analysis.recommended_strategies[1:]
            analysis.recommended_strategies = new_strategies
            
            new_plan = self.planner.create_plan(analysis)
            new_result = self.executor.execute(new_plan)
            
            # Return better result
            if new_result.confidence > result.confidence:
                return new_result
        
        return result
    
    def _update_stats(self, result: AgenticResult):
        """İstatistikleri güncelle."""
        self._query_count += 1
        self._total_time_ms += result.total_time_ms
        
        # Running average
        n = self._query_count
        self._avg_confidence = (
            (self._avg_confidence * (n - 1) + result.confidence) / n
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        return {
            "query_count": self._query_count,
            "total_time_ms": self._total_time_ms,
            "avg_time_ms": self._total_time_ms / max(self._query_count, 1),
            "avg_confidence": round(self._avg_confidence, 3),
        }


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_agentic_rag: Optional[AgenticRAG] = None


def get_agentic_rag() -> AgenticRAG:
    """Singleton AgenticRAG instance."""
    global _agentic_rag
    
    if _agentic_rag is None:
        _agentic_rag = AgenticRAG()
    
    return _agentic_rag


# Convenience singleton
agentic_rag = AgenticRAG()


__all__ = [
    "AgenticRAG",
    "AgenticQueryAnalyzer",
    "AgenticPlanner",
    "AgenticExecutor",
    "QueryComplexity",
    "StrategyType",
    "ActionType",
    "AgentState",
    "QueryAnalysis",
    "AgentAction",
    "AgentPlan",
    "AgenticResult",
    "agentic_rag",
    "get_agentic_rag",
]
