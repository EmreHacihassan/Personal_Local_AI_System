"""
Enterprise AI Assistant - Enhanced Agent
========================================

ReAct + Planning + Self-Reflection Entegrasyonu
Endüstri Standartlarında Kurumsal AI Çözümü

Bu modül, tüm gelişmiş agent özelliklerini birleştiren
üst düzey agent implementasyonunu içerir.

Entegre Özellikler:
- ReAct Pattern (Reasoning + Acting)
- Planning Agent (Task Decomposition)
- Self-Reflection & Critique
- Iterative Refinement
- Constitutional AI Layer
- Memory Integration
- Tool Orchestration

Kullanım:
    from agents.enhanced_agent import enhanced_agent
    
    result = enhanced_agent.execute(
        query="Karmaşık bir görev açıklaması",
        mode="auto"  # auto, react, plan, simple
    )
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import json
import asyncio
import uuid

import sys
sys.path.append('..')

from core.llm_manager import llm_manager
from core.logger import get_logger
from core.memory import memory_manager

from .react_agent import (
    ReActAgent, ReActAgentWithMemory, StreamingReActAgent,
    ReActTrace, Thought, Action, Observation,
    ThoughtType, ActionType, ToolExecutor,
)
from .planning_agent import (
    PlanningAgent, ExecutionPlan, TaskNode, TaskDecomposer,
    TreeOfThoughts, ThoughtBranch,
    PlanningStrategy, TaskStatus, TaskComplexity,
)
from .self_reflection import (
    SelfCritiqueSystem, CriticAgent, IterativeRefiner,
    SelfReflector, ConstitutionalChecker,
    CritiqueResult, ReflectionResult, RefinementResult,
    QualityLevel, RefinementAction,
)

logger = get_logger("enhanced_agent")


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ExecutionMode(str, Enum):
    """Çalıştırma modları."""
    AUTO = "auto"               # Otomatik mod seçimi
    REACT = "react"             # ReAct pattern
    PLAN = "plan"               # Planning + Execute
    SIMPLE = "simple"           # Basit LLM çağrısı
    HYBRID = "hybrid"           # ReAct + Planning


class QueryComplexity(str, Enum):
    """Sorgu karmaşıklığı."""
    TRIVIAL = "trivial"         # Basit selam, teşekkür
    SIMPLE = "simple"           # Tek adımlık sorular
    MODERATE = "moderate"       # 2-3 adımlık görevler
    COMPLEX = "complex"         # Çok adımlı, araç gerektiren
    VERY_COMPLEX = "very_complex"  # Planlama gerektiren


@dataclass
class QueryAnalysis:
    """Sorgu analizi."""
    query: str
    complexity: QueryComplexity
    recommended_mode: ExecutionMode
    needs_tools: bool = False
    needs_search: bool = False
    needs_planning: bool = False
    estimated_steps: int = 1
    detected_intent: str = ""
    key_entities: List[str] = field(default_factory=list)
    confidence: float = 0.8
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query[:100],
            "complexity": self.complexity.value,
            "recommended_mode": self.recommended_mode.value,
            "needs_tools": self.needs_tools,
            "needs_search": self.needs_search,
            "needs_planning": self.needs_planning,
            "estimated_steps": self.estimated_steps,
            "detected_intent": self.detected_intent,
            "key_entities": self.key_entities,
            "confidence": self.confidence,
        }


@dataclass
class EnhancedResponse:
    """Gelişmiş yanıt yapısı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    response: str = ""
    
    # Execution details
    mode_used: ExecutionMode = ExecutionMode.SIMPLE
    execution_trace: Optional[Dict[str, Any]] = None
    
    # Quality
    quality_score: float = 0.0
    quality_level: QualityLevel = QualityLevel.ACCEPTABLE
    was_refined: bool = False
    refinement_iterations: int = 0
    
    # Planning (if used)
    plan: Optional[ExecutionPlan] = None
    tasks_completed: int = 0
    tasks_total: int = 0
    
    # ReAct (if used)
    react_trace: Optional[ReActTrace] = None
    thoughts_count: int = 0
    actions_count: int = 0
    
    # Reflection
    reflection: Optional[ReflectionResult] = None
    critique: Optional[CritiqueResult] = None
    
    # Sources & Citations
    sources: List[str] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Meta
    success: bool = True
    error: Optional[str] = None
    total_time_ms: float = 0.0
    tokens_used: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "response": self.response,
            "mode_used": self.mode_used.value,
            "quality_score": self.quality_score,
            "quality_level": self.quality_level.value,
            "was_refined": self.was_refined,
            "sources": self.sources,
            "success": self.success,
            "error": self.error,
            "total_time_ms": self.total_time_ms,
            "created_at": self.created_at.isoformat(),
            "thoughts_count": self.thoughts_count,
            "actions_count": self.actions_count,
            "tasks_completed": self.tasks_completed,
            "tasks_total": self.tasks_total,
        }
    
    def format_detailed(self) -> str:
        """Detaylı format."""
        lines = [
            "═" * 70,
            f"🤖 Enhanced Agent Response",
            "═" * 70,
            f"Query: {self.query[:80]}...",
            f"Mode: {self.mode_used.value}",
            f"Quality: {self.quality_score:.2f} ({self.quality_level.value})",
            "─" * 70,
            "",
            self.response,
            "",
            "─" * 70,
            f"⏱️  Time: {self.total_time_ms:.0f}ms",
            f"💭 Thoughts: {self.thoughts_count}",
            f"🔧 Actions: {self.actions_count}",
        ]
        
        if self.sources:
            lines.append(f"📚 Sources: {len(self.sources)}")
        
        if self.was_refined:
            lines.append(f"✨ Refined: {self.refinement_iterations} iterations")
        
        lines.append("═" * 70)
        
        return "\n".join(lines)


# ============================================================================
# QUERY ANALYZER
# ============================================================================

class QueryAnalyzer:
    """
    Sorgu Analiz Edici.
    
    Gelen sorguyu analiz ederek en uygun çalıştırma modunu belirler.
    """
    
    # Keyword patterns for complexity detection
    TRIVIAL_PATTERNS = [
        "merhaba", "selam", "günaydın", "iyi günler", "nasılsın",
        "teşekkür", "sağol", "eyvallah", "görüşürüz", "hoşçakal",
        "hello", "hi", "hey", "thanks", "bye",
    ]
    
    SIMPLE_PATTERNS = [
        "nedir", "ne", "kim", "kaç", "kac", "hangi", "nasıl", "nasil",
        "what", "who", "how many", "which", "how",
        "eder", "yapar", "olur", "var mı", "mi", "mı",
    ]
    
    COMPLEX_PATTERNS = [
        " ve ", " sonra ", " ardından ", " önce ",
        "karşılaştır", "analiz", "özetle", "değerlendir",
        "compare", "analyze", "summarize", "evaluate",
        "tüm", "hepsi", "liste", "detaylı",
    ]
    
    PLANNING_PATTERNS = [
        "plan", "strateji", "adım", "aşama", "süreç",
        "proje", "yol haritası", "nasıl yapılır",
        "step by step", "roadmap", "process",
    ]
    
    TOOL_PATTERNS = [
        "ara", "bul", "hesapla", "dönüştür", "çevir",
        "search", "find", "calculate", "convert",
        "dosya", "file", "web", "api",
    ]
    
    def __init__(self):
        self._analysis_cache: Dict[str, QueryAnalysis] = {}
    
    def analyze(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """
        Sorguyu analiz et.
        
        Args:
            query: Analiz edilecek sorgu
            context: Ek bağlam
            
        Returns:
            QueryAnalysis
        """
        # Check cache
        cache_key = query.lower()[:100]
        if cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]
        
        query_lower = query.lower()
        
        # Detect complexity
        complexity = self._detect_complexity(query_lower)
        
        # Detect needs
        needs_tools = any(p in query_lower for p in self.TOOL_PATTERNS)
        needs_search = any(p in query_lower for p in ["ara", "bul", "bilgi", "search", "find", "document"])
        needs_planning = any(p in query_lower for p in self.PLANNING_PATTERNS)
        
        # Estimate steps
        estimated_steps = self._estimate_steps(query_lower, complexity)
        
        # Determine recommended mode
        recommended_mode = self._recommend_mode(
            complexity, needs_tools, needs_search, needs_planning
        )
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query)
        
        analysis = QueryAnalysis(
            query=query,
            complexity=complexity,
            recommended_mode=recommended_mode,
            needs_tools=needs_tools,
            needs_search=needs_search,
            needs_planning=needs_planning,
            estimated_steps=estimated_steps,
            detected_intent=intent,
            key_entities=entities,
        )
        
        # Cache
        self._analysis_cache[cache_key] = analysis
        
        return analysis
    
    def _detect_complexity(self, query_lower: str) -> QueryComplexity:
        """Karmaşıklığı tespit et. OPTIMIZED for faster responses."""
        word_count = len(query_lower.split())
        
        # Trivial check - greetings and very short
        if any(p in query_lower for p in self.TRIVIAL_PATTERNS):
            if word_count <= 5:
                return QueryComplexity.TRIVIAL
        
        # SHORT queries (< 8 words) without complex patterns -> SIMPLE
        if word_count < 8:
            if not any(p in query_lower for p in self.COMPLEX_PATTERNS):
                return QueryComplexity.SIMPLE
        
        # Planning check (highest complexity)
        if any(p in query_lower for p in self.PLANNING_PATTERNS):
            return QueryComplexity.VERY_COMPLEX
        
        # Complex check
        complex_count = sum(1 for p in self.COMPLEX_PATTERNS if p in query_lower)
        if complex_count >= 2:
            return QueryComplexity.COMPLEX
        
        # Simple check
        if any(p in query_lower for p in self.SIMPLE_PATTERNS):
            if word_count <= 10:
                return QueryComplexity.SIMPLE
        
        # Default to SIMPLE for better performance (was MODERATE)
        return QueryComplexity.SIMPLE
    
    def _estimate_steps(self, query_lower: str, complexity: QueryComplexity) -> int:
        """Tahmini adım sayısı."""
        base_steps = {
            QueryComplexity.TRIVIAL: 1,
            QueryComplexity.SIMPLE: 1,
            QueryComplexity.MODERATE: 2,
            QueryComplexity.COMPLEX: 4,
            QueryComplexity.VERY_COMPLEX: 6,
        }
        
        steps = base_steps.get(complexity, 2)
        
        # Adjust based on keywords
        if " ve " in query_lower or " and " in query_lower:
            steps += 1
        if "karşılaştır" in query_lower or "compare" in query_lower:
            steps += 2
        
        return min(steps, 10)
    
    def _recommend_mode(
        self,
        complexity: QueryComplexity,
        needs_tools: bool,
        needs_search: bool,
        needs_planning: bool,
    ) -> ExecutionMode:
        """Çalıştırma modu öner. OPTIMIZED for local models."""
        if complexity == QueryComplexity.TRIVIAL:
            return ExecutionMode.SIMPLE
        
        if needs_planning or complexity == QueryComplexity.VERY_COMPLEX:
            return ExecutionMode.PLAN
        
        # OPTIMIZATION: Only use ReAct when really needed (tools/search)
        if needs_tools or needs_search:
            return ExecutionMode.REACT
        
        # For COMPLEX without tools, still use SIMPLE (faster)
        if complexity == QueryComplexity.COMPLEX:
            return ExecutionMode.SIMPLE
        
        # MODERATE -> SIMPLE (was REACT, too slow for local models)
        if complexity == QueryComplexity.MODERATE:
            return ExecutionMode.SIMPLE
        
        return ExecutionMode.SIMPLE
    
    def _detect_intent(self, query_lower: str) -> str:
        """Niyet tespit et."""
        intents = {
            "question": ["nedir", "ne", "kim", "kaç", "what", "who", "how"],
            "search": ["ara", "bul", "search", "find"],
            "analysis": ["analiz", "değerlendir", "analyze", "evaluate"],
            "comparison": ["karşılaştır", "fark", "compare", "difference"],
            "summary": ["özetle", "özet", "summarize", "summary"],
            "creation": ["yaz", "oluştur", "create", "write", "hazırla"],
            "planning": ["planla", "plan", "strategy", "roadmap"],
            "greeting": ["merhaba", "selam", "hello", "hi"],
        }
        
        for intent, keywords in intents.items():
            if any(k in query_lower for k in keywords):
                return intent
        
        return "general"
    
    def _extract_entities(self, query: str) -> List[str]:
        """Önemli varlıkları çıkar."""
        # Simple extraction - words that start with uppercase
        words = query.split()
        entities = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip(".,;:!?\"'")
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                entities.append(clean_word)
        
        return list(set(entities))[:5]


# ============================================================================
# ENHANCED AGENT
# ============================================================================

class EnhancedAgent:
    """
    Enhanced Agent - Tüm gelişmiş özelliklerin birleşimi.
    
    Özellikler:
    - Automatic mode selection
    - ReAct reasoning
    - Task planning
    - Self-critique & refinement
    - Constitutional AI safety
    - Memory integration
    - Streaming support
    """
    
    def __init__(
        self,
        name: str = "EnhancedAgent",
        enable_react: bool = True,
        enable_planning: bool = True,
        enable_critique: bool = True,
        enable_refinement: bool = True,
        enable_constitutional: bool = True,
        enable_memory: bool = True,
        auto_mode: bool = True,
        verbose: bool = True,
        quality_threshold: float = 0.5,
        max_refinement_iterations: int = 1,
    ):
        """
        Enhanced Agent başlat.
        
        Args:
            name: Agent adı
            enable_react: ReAct aktif
            enable_planning: Planning aktif
            enable_critique: Critique aktif
            enable_refinement: Refinement aktif
            enable_constitutional: Constitutional AI aktif
            enable_memory: Memory aktif
            auto_mode: Otomatik mod seçimi
            verbose: Detaylı log
            quality_threshold: Kalite eşiği
            max_refinement_iterations: Max refinement iterasyonu
        """
        self.name = name
        self.enable_react = enable_react
        self.enable_planning = enable_planning
        self.enable_critique = enable_critique
        self.enable_refinement = enable_refinement
        self.enable_constitutional = enable_constitutional
        self.enable_memory = enable_memory
        self.auto_mode = auto_mode
        self.verbose = verbose
        self.quality_threshold = quality_threshold
        self.max_refinement_iterations = max_refinement_iterations
        
        # Components
        self.query_analyzer = QueryAnalyzer()
        
        # ReAct
        self.react_agent = ReActAgentWithMemory(
            name=f"{name}_ReAct",
            verbose=verbose,
        ) if enable_react else None
        
        # Planning
        self.planning_agent = PlanningAgent(
            name=f"{name}_Planner",
            enable_tot=True,
            verbose=verbose,
        ) if enable_planning else None
        
        # Critique
        self.critic = CriticAgent(strict_mode=True) if enable_critique else None
        
        # Refinement
        self.refiner = IterativeRefiner(
            critic=self.critic,
            max_iterations=max_refinement_iterations,
            target_score=0.85,
        ) if enable_refinement else None
        
        # Constitutional
        self.constitutional = ConstitutionalChecker(strict_mode=True) if enable_constitutional else None
        
        # Memory
        self.memory = memory_manager if enable_memory else None
        
        # Session
        self._session_id: Optional[str] = None
        
        # Stats
        self._total_queries = 0
        self._mode_usage: Dict[str, int] = {}
        self._average_quality = 0.0
        self._response_history: List[EnhancedResponse] = []
    
    def set_session(self, session_id: str):
        """Session ayarla."""
        self._session_id = session_id
        if self.react_agent:
            self.react_agent.set_session(session_id)
    
    async def execute(
        self,
        query: str,
        mode: Optional[ExecutionMode] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EnhancedResponse:
        """
        Sorguyu çalıştır.
        
        Args:
            query: Kullanıcı sorgusu
            mode: Çalıştırma modu (None = auto)
            context: Ek bağlam
            
        Returns:
            EnhancedResponse
        """
        import time
        start_time = time.time()
        
        self._total_queries += 1
        
        response = EnhancedResponse(query=query)
        
        try:
            # Analyze query
            analysis = self.query_analyzer.analyze(query, context)
            
            if self.verbose:
                logger.info(f"Query analysis: {analysis.to_dict()}")
            
            # Determine mode
            if mode is None and self.auto_mode:
                mode = analysis.recommended_mode
            elif mode is None:
                mode = ExecutionMode.SIMPLE
            
            response.mode_used = mode
            response.metadata["analysis"] = analysis.to_dict()
            
            # Track mode usage
            self._mode_usage[mode.value] = self._mode_usage.get(mode.value, 0) + 1
            
            # Get memory context
            memory_context = {}
            if self.memory and self._session_id:
                memory_context = self.memory.get_context_for_query(
                    self._session_id,
                    query,
                )
            
            # Merge contexts
            full_context = {**(context or {}), **memory_context}
            
            # Execute based on mode
            if mode == ExecutionMode.SIMPLE:
                response = await self._execute_simple(query, full_context, response)
            elif mode == ExecutionMode.REACT:
                response = await self._execute_react(query, full_context, response)
            elif mode == ExecutionMode.PLAN:
                response = await self._execute_plan(query, full_context, response)
            elif mode == ExecutionMode.HYBRID:
                response = await self._execute_hybrid(query, full_context, response)
            else:
                response = await self._execute_simple(query, full_context, response)
            
            # OPTIMIZATION: Skip heavy checks for simple/trivial queries
            skip_heavy_checks = analysis.complexity in [QueryComplexity.TRIVIAL, QueryComplexity.SIMPLE]
            
            # Constitutional check (skip for simple queries)
            if self.constitutional and response.response and not skip_heavy_checks:
                const_result = self.constitutional.check(response.response)
                
                if not const_result.get("is_safe", True):
                    logger.warning("Response failed constitutional check, regenerating...")
                    response.response = await self._regenerate_safe_response(
                        query,
                        const_result.get("revision_suggestions", []),
                    )
                    response.metadata["constitutional_revised"] = True
            
            # Quality critique (skip for simple queries)
            if self.critic and response.response and not skip_heavy_checks:
                critique = self.critic.critique(
                    response.response,
                    original_question=query,
                )
                response.critique = critique
                response.quality_score = critique.overall_score
                response.quality_level = critique.overall_level
                
                # Auto-refine if needed
                if (self.refiner and 
                    critique.overall_score < self.quality_threshold and
                    critique.needs_refinement()):
                    
                    if self.verbose:
                        logger.info(f"Quality below threshold ({critique.overall_score:.2f}), refining...")
                    
                    trace = self.refiner.refine(
                        response.response,
                        original_question=query,
                    )
                    
                    response.response = trace.final_content
                    response.was_refined = True
                    response.refinement_iterations = trace.total_iterations
                    response.quality_score = trace.final_score
                    
                    # Update quality level
                    if trace.final_score >= 0.9:
                        response.quality_level = QualityLevel.EXCELLENT
                    elif trace.final_score >= 0.7:
                        response.quality_level = QualityLevel.GOOD
            
            # Store in memory
            if self.memory and self._session_id and response.success:
                self.memory.add_interaction(
                    self._session_id,
                    query,
                    response.response,
                )
            
            # Update stats
            self._average_quality = (
                self._average_quality * (len(self._response_history)) + response.quality_score
            ) / (len(self._response_history) + 1)
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            response.success = False
            response.error = str(e)
            response.response = f"Bir hata oluştu: {str(e)}"
        
        # Finalize
        response.total_time_ms = (time.time() - start_time) * 1000
        self._response_history.append(response)
        
        if self.verbose:
            logger.info(f"\n{response.format_detailed()}")
        
        return response
    
    async def _execute_simple(
        self,
        query: str,
        context: Dict[str, Any],
        response: EnhancedResponse,
    ) -> EnhancedResponse:
        """Basit LLM çağrısı."""
        # Build prompt with context
        prompt = query
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            prompt = f"Bağlam:\n{context_str}\n\nSoru: {query}"
        
        result = llm_manager.generate(prompt=prompt, temperature=0.7)
        
        response.response = result
        response.thoughts_count = 0
        response.actions_count = 0
        
        return response
    
    async def _execute_react(
        self,
        query: str,
        context: Dict[str, Any],
        response: EnhancedResponse,
    ) -> EnhancedResponse:
        """ReAct pattern ile çalıştır."""
        if not self.react_agent:
            return await self._execute_simple(query, context, response)
        
        trace = await self.react_agent.run(query, context)
        
        response.response = trace.final_answer
        response.react_trace = trace
        response.thoughts_count = trace.thoughts_count
        response.actions_count = trace.tool_calls_count
        response.execution_trace = trace.to_dict()
        
        # Extract sources from observations
        for step in trace.steps:
            if step.observation and step.observation.content:
                if isinstance(step.observation.content, dict):
                    results = step.observation.content.get("results", [])
                    for r in results:
                        if isinstance(r, dict) and "source" in r:
                            response.sources.append(r["source"])
        
        response.sources = list(set(response.sources))
        
        return response
    
    async def _execute_plan(
        self,
        query: str,
        context: Dict[str, Any],
        response: EnhancedResponse,
    ) -> EnhancedResponse:
        """Planning ile çalıştır."""
        if not self.planning_agent:
            return await self._execute_react(query, context, response)
        
        # Create plan
        plan = self.planning_agent.create_plan(query, context=context)
        
        response.plan = plan
        response.tasks_total = plan.total_tasks
        
        if self.verbose:
            logger.info(f"\n{plan.visualize()}")
        
        # Execute plan
        plan = await self.planning_agent.execute_plan(plan)
        
        response.tasks_completed = plan.completed_tasks
        
        # Collect results
        results = []
        for task_id in plan.execution_order:
            task = plan.tasks.get(task_id)
            if task and task.result:
                results.append(str(task.result))
        
        # Generate final response from results
        if results:
            summary_prompt = f"""Aşağıdaki alt görev sonuçlarını kullanarak "{query}" sorusuna kapsamlı bir yanıt oluştur:

GÖREV SONUÇLARI:
{chr(10).join(f'{i+1}. {r[:500]}' for i, r in enumerate(results))}

Sonuçları sentezleyerek tek bir tutarlı yanıt oluştur:"""
            
            response.response = llm_manager.generate(
                prompt=summary_prompt,
                temperature=0.5,
            )
        else:
            response.response = "Plan tamamlandı ancak sonuç alınamadı."
        
        response.execution_trace = plan.to_dict()
        
        return response
    
    async def _execute_hybrid(
        self,
        query: str,
        context: Dict[str, Any],
        response: EnhancedResponse,
    ) -> EnhancedResponse:
        """Hybrid: Planning + ReAct."""
        if not self.planning_agent:
            return await self._execute_react(query, context, response)
        
        # Create high-level plan
        plan = self.planning_agent.create_plan(
            query,
            strategy=PlanningStrategy.LINEAR,
            context=context,
        )
        
        response.plan = plan
        response.tasks_total = plan.total_tasks
        
        # Execute each task with ReAct
        results = []
        
        for task_id in plan.execution_order:
            task = plan.tasks.get(task_id)
            if not task:
                continue
            
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            if self.react_agent:
                # Use ReAct for task execution
                trace = await self.react_agent.run(
                    task.description,
                    {"parent_goal": query, "task_name": task.name},
                )
                task.result = trace.final_answer
                
                response.thoughts_count += trace.thoughts_count
                response.actions_count += trace.tool_calls_count
            else:
                # Fallback to simple
                task.result = llm_manager.generate(task.description)
            
            plan.mark_completed(task_id, task.result)
            results.append(task.result)
        
        response.tasks_completed = plan.completed_tasks
        
        # Synthesize results
        if results:
            synthesis_prompt = f""""{query}" için gerçekleştirilen görevlerin sonuçları:

{chr(10).join(f'- {r[:300]}' for r in results)}

Bu sonuçları birleştirerek kapsamlı bir yanıt oluştur:"""
            
            response.response = llm_manager.generate(
                prompt=synthesis_prompt,
                temperature=0.5,
            )
        
        return response
    
    async def _regenerate_safe_response(
        self,
        query: str,
        suggestions: List[str],
    ) -> str:
        """Güvenli yanıt yeniden oluştur."""
        prompt = f"""Aşağıdaki soruya yanıt ver. Yanıtın güvenli ve etik olmalı.

SORU: {query}

DİKKAT EDİLMESİ GEREKENLER:
{chr(10).join(f'- {s}' for s in suggestions)}

Güvenli ve yararlı yanıt:"""
        
        return llm_manager.generate(prompt=prompt, temperature=0.5)
    
    def execute_sync(
        self,
        query: str,
        mode: Optional[ExecutionMode] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EnhancedResponse:
        """Senkron çalıştırma."""
        return asyncio.run(self.execute(query, mode, context))
    
    async def stream_execute(
        self,
        query: str,
        mode: Optional[ExecutionMode] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Streaming çalıştırma.
        
        Yields:
            Dict with progress information
        """
        # Analyze
        analysis = self.query_analyzer.analyze(query, context)
        
        yield {
            "type": "analysis",
            "data": analysis.to_dict(),
        }
        
        # Determine mode
        if mode is None and self.auto_mode:
            mode = analysis.recommended_mode
        
        yield {
            "type": "mode_selected",
            "mode": mode.value,
        }
        
        # Execute with progress
        if mode == ExecutionMode.REACT and self.react_agent:
            # Use streaming react
            streaming_agent = StreamingReActAgent(
                name=f"{self.name}_StreamingReAct",
                verbose=self.verbose,
            )
            
            async for event in streaming_agent.run_streaming(query, context):
                yield {
                    "type": "react_event",
                    "data": event,
                }
        else:
            # Non-streaming fallback
            response = await self.execute(query, mode, context)
            
            yield {
                "type": "complete",
                "data": response.to_dict(),
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler."""
        return {
            "total_queries": self._total_queries,
            "mode_usage": self._mode_usage,
            "average_quality": self._average_quality,
            "response_count": len(self._response_history),
            "components": {
                "react_enabled": self.enable_react,
                "planning_enabled": self.enable_planning,
                "critique_enabled": self.enable_critique,
                "refinement_enabled": self.enable_refinement,
                "constitutional_enabled": self.enable_constitutional,
                "memory_enabled": self.enable_memory,
            },
        }
    
    def get_history(self, limit: int = 10) -> List[EnhancedResponse]:
        """Yanıt geçmişi."""
        return self._response_history[-limit:]
    
    def clear_history(self):
        """Geçmişi temizle."""
        self._response_history.clear()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_enhanced_agent(
    enable_all: bool = True,
    **kwargs,
) -> EnhancedAgent:
    """Enhanced Agent factory."""
    return EnhancedAgent(
        enable_react=enable_all,
        enable_planning=enable_all,
        enable_critique=enable_all,
        enable_refinement=enable_all,
        enable_constitutional=enable_all,
        enable_memory=enable_all,
        **kwargs,
    )


async def quick_execute(
    query: str,
    mode: Optional[ExecutionMode] = None,
) -> str:
    """Hızlı çalıştırma - sadece yanıt döndürür."""
    agent = enhanced_agent
    response = await agent.execute(query, mode)
    return response.response


def quick_execute_sync(
    query: str,
    mode: Optional[ExecutionMode] = None,
) -> str:
    """Senkron hızlı çalıştırma."""
    return asyncio.run(quick_execute(query, mode))


# ============================================================================
# SINGLETON
# ============================================================================

# Default instance with all features
enhanced_agent = create_enhanced_agent(
    name="EnterpriseEnhancedAgent",
    verbose=True,
    quality_threshold=0.5,
    max_refinement_iterations=1,
)
