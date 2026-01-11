"""
Enterprise AI Assistant - ReAct Agent Framework
===============================================

ReAct (Reasoning + Acting) Pattern Implementation
Endüstri Standartlarında Kurumsal AI Çözümü

ReAct Döngüsü:
    Thought → Action → Observation → Thought → ... → Final Answer

Bu modül, agent'ların düşünce süreçlerini şeffaf ve yapılandırılmış
şekilde göstermesini sağlar. Chain-of-Thought (CoT) reasoning ile
tool kullanımını birleştirir.

Referanslar:
- ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)
- Chain-of-Thought Prompting (Wei et al., 2022)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import json
import re
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

import sys
sys.path.append('..')

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("react_agent")


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ThoughtType(str, Enum):
    """Düşünce türleri."""
    REASONING = "reasoning"           # Mantıksal çıkarım
    PLANNING = "planning"             # Planlama
    REFLECTION = "reflection"         # Yansıtma
    OBSERVATION = "observation"       # Gözlem
    QUESTION = "question"             # Soru
    HYPOTHESIS = "hypothesis"         # Hipotez
    CONCLUSION = "conclusion"         # Sonuç
    UNCERTAINTY = "uncertainty"       # Belirsizlik
    CORRECTION = "correction"         # Düzeltme


class ActionType(str, Enum):
    """Aksiyon türleri."""
    TOOL_CALL = "tool_call"           # Araç çağrısı
    SEARCH = "search"                 # Arama
    RETRIEVE = "retrieve"             # Bilgi getirme
    COMPUTE = "compute"               # Hesaplama
    DELEGATE = "delegate"             # Başka agent'a delege
    ASK_USER = "ask_user"             # Kullanıcıya sor
    WAIT = "wait"                     # Bekle
    FINISH = "finish"                 # Bitir


class ReActStepType(str, Enum):
    """ReAct adım türleri."""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"


@dataclass
class Thought:
    """Düşünce yapısı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    thought_type: ThoughtType = ThoughtType.REASONING
    confidence: float = 0.8  # 0.0 - 1.0
    reasoning_chain: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Önceki thought ID'leri
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.thought_type.value,
            "confidence": self.confidence,
            "reasoning_chain": self.reasoning_chain,
            "dependencies": self.dependencies,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    def __str__(self) -> str:
        return f"💭 [{self.thought_type.value}] {self.content}"


@dataclass
class Action:
    """Aksiyon yapısı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: ActionType = ActionType.TOOL_CALL
    tool_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""  # Neden bu aksiyon?
    expected_outcome: str = ""
    fallback_action: Optional["Action"] = None
    timeout_seconds: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "reason": self.reason,
            "expected_outcome": self.expected_outcome,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        if self.tool_name:
            return f"🔧 [{self.action_type.value}] {self.tool_name}({json.dumps(self.arguments, ensure_ascii=False)})"
        return f"🔧 [{self.action_type.value}] {self.reason}"


@dataclass
class Observation:
    """Gözlem yapısı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: Any = None
    source: str = ""  # Gözlem kaynağı (tool adı, search, etc.)
    action_id: str = ""  # İlgili action ID
    success: bool = True
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    confidence: float = 1.0  # Sonucun güvenilirliği
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": str(self.content)[:1000] if self.content else None,
            "source": self.source,
            "action_id": self.action_id,
            "success": self.success,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        content_preview = str(self.content)[:200] if self.content else "No content"
        return f"👁️ {status} [{self.source}] {content_preview}"


@dataclass
class ReActStep:
    """ReAct adımı."""
    step_number: int
    step_type: ReActStepType
    thought: Optional[Thought] = None
    action: Optional[Action] = None
    observation: Optional[Observation] = None
    final_answer: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "thought": self.thought.to_dict() if self.thought else None,
            "action": self.action.to_dict() if self.action else None,
            "observation": self.observation.to_dict() if self.observation else None,
            "final_answer": self.final_answer,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ReActTrace:
    """ReAct izleme kaydı - tüm düşünce/aksiyon/gözlem zinciri."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    steps: List[ReActStep] = field(default_factory=list)
    final_answer: str = ""
    success: bool = True
    total_tokens_used: int = 0
    total_time_ms: float = 0.0
    tool_calls_count: int = 0
    thoughts_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: ReActStep):
        """Adım ekle."""
        self.steps.append(step)
        if step.thought:
            self.thoughts_count += 1
        if step.action and step.action.action_type == ActionType.TOOL_CALL:
            self.tool_calls_count += 1
    
    def get_thought_chain(self) -> List[str]:
        """Düşünce zincirini döndür."""
        return [
            step.thought.content 
            for step in self.steps 
            if step.thought
        ]
    
    def get_action_history(self) -> List[Dict]:
        """Aksiyon geçmişini döndür."""
        return [
            step.action.to_dict() 
            for step in self.steps 
            if step.action
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "success": self.success,
            "total_tokens_used": self.total_tokens_used,
            "total_time_ms": self.total_time_ms,
            "tool_calls_count": self.tool_calls_count,
            "thoughts_count": self.thoughts_count,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def format_trace(self) -> str:
        """İnsan okunabilir trace formatı."""
        lines = [
            f"═══════════════════════════════════════════════════",
            f"🔍 Query: {self.query}",
            f"═══════════════════════════════════════════════════",
            "",
        ]
        
        for step in self.steps:
            lines.append(f"📍 Step {step.step_number}")
            
            if step.thought:
                lines.append(f"   {step.thought}")
            
            if step.action:
                lines.append(f"   {step.action}")
            
            if step.observation:
                lines.append(f"   {step.observation}")
            
            if step.final_answer:
                lines.append(f"   ✨ Final Answer: {step.final_answer[:200]}...")
            
            lines.append("")
        
        lines.extend([
            f"═══════════════════════════════════════════════════",
            f"📊 Stats: {self.thoughts_count} thoughts, {self.tool_calls_count} tool calls, {self.total_time_ms:.0f}ms",
            f"═══════════════════════════════════════════════════",
        ])
        
        return "\n".join(lines)


# ============================================================================
# TOOL INTERFACE
# ============================================================================

@dataclass
class ToolDefinition:
    """Araç tanımı."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_params: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    category: str = "general"
    
    def to_prompt_format(self) -> str:
        """Prompt için formatla."""
        params_str = ", ".join([
            f"{name}: {info.get('type', 'any')}" 
            for name, info in self.parameters.items()
        ])
        return f"- {self.name}({params_str}): {self.description}"


class ToolExecutor:
    """Araç çalıştırıcı."""
    
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any],
        required_params: List[str] = None,
        examples: List[Dict] = None,
        category: str = "general",
    ):
        """Araç kaydet."""
        self._tools[name] = func
        self._definitions[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required_params or [],
            examples=examples or [],
            category=category,
        )
    
    def get_definitions(self) -> List[ToolDefinition]:
        """Tüm araç tanımlarını döndür."""
        return list(self._definitions.values())
    
    def get_tools_prompt(self) -> str:
        """Araçları prompt formatında döndür."""
        lines = ["Kullanılabilir Araçlar:"]
        for defn in self._definitions.values():
            lines.append(defn.to_prompt_format())
        return "\n".join(lines)
    
    async def execute(self, action: Action) -> Observation:
        """Aracı çalıştır."""
        import time
        start_time = time.time()
        
        tool_name = action.tool_name
        
        if tool_name not in self._tools:
            return Observation(
                action_id=action.id,
                source=tool_name,
                success=False,
                error=f"Tool not found: {tool_name}",
            )
        
        try:
            func = self._tools[tool_name]
            
            # Execute (async veya sync)
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(**action.arguments),
                    timeout=action.timeout_seconds,
                )
            else:
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self._executor,
                        lambda: func(**action.arguments)
                    ),
                    timeout=action.timeout_seconds,
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            return Observation(
                action_id=action.id,
                content=result,
                source=tool_name,
                success=True,
                execution_time_ms=execution_time,
            )
            
        except asyncio.TimeoutError:
            return Observation(
                action_id=action.id,
                source=tool_name,
                success=False,
                error=f"Tool execution timed out after {action.timeout_seconds}s",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return Observation(
                action_id=action.id,
                source=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )


# ============================================================================
# REACT AGENT
# ============================================================================

class ReActAgent:
    """
    ReAct Agent - Reasoning + Acting Pattern.
    
    Bu agent, düşünce süreçlerini şeffaf hale getirir ve her adımı
    açıkça gösterir. Tool kullanımı ile reasoning'i birleştirir.
    
    Özellikler:
    - Structured thought process (Thought → Action → Observation)
    - Chain-of-Thought reasoning
    - Tool use with verification
    - Self-correction capability
    - Trace logging for debugging
    - Configurable max iterations
    """
    
    REACT_SYSTEM_PROMPT = """Sen bir ReAct (Reasoning + Acting) agent'ısın. Karmaşık görevleri çözmek için düşünce ve aksiyon döngüsü kullanırsın.

HER ADIMDA şu formatı KESINLIKLE kullan:

Thought: [Mevcut durumu analiz et, ne yapman gerektiğini düşün]
Action: [tool_name(param1="value1", param2="value2")] veya [finish(answer="...")]
Observation: [Aksiyon sonucunu bekle - bu kısım sana verilecek]

KURALLAR:
1. Her zaman önce DÜŞÜN (Thought)
2. Düşündükten sonra AKSIYON al (Action)
3. Gözlemi değerlendir ve tekrar düşün
4. Yeterli bilgi topladığında finish() ile bitir
5. Emin olmadığın durumlarda hipotez belirt
6. Hata aldığında alternatif strateji düşün

KULLANILABİLİR ARAÇLAR:
{tools_prompt}

ÖRNEK:
Thought: Kullanıcı şirket politikasını soruyor. Önce bilgi tabanında aramalıyım.
Action: search(query="şirket izin politikası")
Observation: [Arama sonuçları burada görünecek]
Thought: Arama sonuçlarında izin politikası buldum. Şimdi özetleyebilirim.
Action: finish(answer="Şirket izin politikasına göre...")

ÖNEMLİ: 
- Thought her zaman türkçe ve açıklayıcı olmalı
- Action formatı kesinlikle: tool_name(param="value") şeklinde
- Birden fazla düşünce zinciri kullanabilirsin
- Belirsizlik varsa açıkça belirt"""

    def __init__(
        self,
        name: str = "ReActAgent",
        tool_executor: Optional[ToolExecutor] = None,
        max_iterations: int = 10,
        temperature: float = 0.7,
        verbose: bool = True,
    ):
        """
        ReAct Agent başlat.
        
        Args:
            name: Agent adı
            tool_executor: Araç çalıştırıcı
            max_iterations: Maksimum iterasyon sayısı
            temperature: LLM temperature
            verbose: Detaylı log
        """
        self.name = name
        self.tool_executor = tool_executor or ToolExecutor()
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.verbose = verbose
        
        # Trace history
        self._traces: List[ReActTrace] = []
        self._current_trace: Optional[ReActTrace] = None
        
        # Register default tools
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Varsayılan araçları kaydet."""
        # Search tool
        def search(query: str) -> Dict[str, Any]:
            """Bilgi tabanında arama yap."""
            from rag.retriever import retriever
            results = retriever.retrieve(query=query, top_k=5)
            return {
                "results": [
                    {"content": r.content[:500], "source": r.source, "score": r.score}
                    for r in results
                ],
                "total": len(results),
            }
        
        self.tool_executor.register(
            name="search",
            func=search,
            description="Bilgi tabanında arama yapar",
            parameters={
                "query": {"type": "string", "description": "Arama sorgusu"},
            },
            required_params=["query"],
            category="retrieval",
        )
        
        # Calculator tool
        def calculate(expression: str) -> Dict[str, Any]:
            """Matematiksel hesaplama yap."""
            try:
                # Safe eval
                allowed = set("0123456789+-*/.() ")
                if not all(c in allowed for c in expression):
                    return {"error": "Invalid expression"}
                result = eval(expression)
                return {"result": result, "expression": expression}
            except Exception as e:
                return {"error": str(e)}
        
        self.tool_executor.register(
            name="calculate",
            func=calculate,
            description="Matematiksel ifadeyi hesaplar",
            parameters={
                "expression": {"type": "string", "description": "Hesaplanacak ifade"},
            },
            required_params=["expression"],
            category="computation",
        )
        
        # Get time tool
        def get_time() -> Dict[str, Any]:
            """Mevcut tarih ve saati döndür."""
            now = datetime.now()
            return {
                "datetime": now.isoformat(),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
            }
        
        self.tool_executor.register(
            name="get_time",
            func=get_time,
            description="Mevcut tarih ve saati döndürür",
            parameters={},
            category="utility",
        )
    
    def register_tool(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any],
        required_params: List[str] = None,
    ):
        """Yeni araç kaydet."""
        self.tool_executor.register(
            name=name,
            func=func,
            description=description,
            parameters=parameters,
            required_params=required_params,
        )
    
    def _build_system_prompt(self) -> str:
        """System prompt oluştur."""
        tools_prompt = self.tool_executor.get_tools_prompt()
        return self.REACT_SYSTEM_PROMPT.format(tools_prompt=tools_prompt)
    
    def _parse_llm_response(self, response: str) -> Tuple[Optional[Thought], Optional[Action]]:
        """
        LLM yanıtından thought ve action parse et.
        
        Returns:
            (Thought, Action) tuple'ı
        """
        thought = None
        action = None
        
        # Parse Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=Action:|$)", response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought_content = thought_match.group(1).strip()
            
            # Thought type'ı belirle
            thought_type = ThoughtType.REASONING
            if any(w in thought_content.lower() for w in ["plan", "adım", "sıra"]):
                thought_type = ThoughtType.PLANNING
            elif any(w in thought_content.lower() for w in ["emin değil", "belirsiz", "olabilir"]):
                thought_type = ThoughtType.UNCERTAINTY
            elif any(w in thought_content.lower() for w in ["düzelt", "hata", "yanlış"]):
                thought_type = ThoughtType.CORRECTION
            elif any(w in thought_content.lower() for w in ["gözlem", "sonuç", "görüyorum"]):
                thought_type = ThoughtType.OBSERVATION
            
            thought = Thought(
                content=thought_content,
                thought_type=thought_type,
            )
        
        # Parse Action
        action_match = re.search(
            r"Action:\s*\[?\s*(\w+)\s*\((.*)?\)\s*\]?",
            response,
            re.DOTALL | re.IGNORECASE,
        )
        
        if action_match:
            tool_name = action_match.group(1).strip()
            args_str = action_match.group(2).strip() if action_match.group(2) else ""
            
            # Parse arguments
            arguments = {}
            if args_str:
                # Pattern: param="value" veya param='value'
                arg_pattern = r'(\w+)\s*=\s*["\']([^"\']*)["\']'
                for match in re.finditer(arg_pattern, args_str):
                    arguments[match.group(1)] = match.group(2)
            
            action_type = ActionType.FINISH if tool_name.lower() == "finish" else ActionType.TOOL_CALL
            
            action = Action(
                action_type=action_type,
                tool_name=tool_name,
                arguments=arguments,
                reason=thought.content if thought else "",
            )
        
        return thought, action
    
    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReActTrace:
        """
        ReAct döngüsünü çalıştır.
        
        Args:
            query: Kullanıcı sorgusu
            context: Ek bağlam
            
        Returns:
            ReActTrace - tüm düşünce/aksiyon/gözlem zinciri
        """
        import time
        start_time = time.time()
        
        # Initialize trace
        trace = ReActTrace(query=query)
        self._current_trace = trace
        
        # Build initial prompt
        system_prompt = self._build_system_prompt()
        messages = []
        
        # Add context if provided
        if context:
            context_str = f"\n\nEk Bağlam:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
            messages.append(f"Soru: {query}{context_str}")
        else:
            messages.append(f"Soru: {query}")
        
        step_number = 0
        
        while step_number < self.max_iterations:
            step_number += 1
            
            if self.verbose:
                logger.info(f"ReAct Step {step_number}")
            
            # Build conversation history for LLM
            conversation = "\n\n".join(messages)
            
            # Get LLM response
            llm_response = llm_manager.generate(
                prompt=conversation,
                system_prompt=system_prompt,
                temperature=self.temperature,
            )
            
            # Parse response
            thought, action = self._parse_llm_response(llm_response)
            
            if self.verbose and thought:
                logger.info(f"  {thought}")
            
            # Create step
            step = ReActStep(
                step_number=step_number,
                step_type=ReActStepType.THOUGHT if thought else ReActStepType.ACTION,
                thought=thought,
                action=action,
            )
            
            # Check if finished
            if action and action.action_type == ActionType.FINISH:
                final_answer = action.arguments.get("answer", "")
                step.step_type = ReActStepType.FINAL_ANSWER
                step.final_answer = final_answer
                trace.add_step(step)
                trace.final_answer = final_answer
                break
            
            # Execute action if present
            if action and action.tool_name:
                if self.verbose:
                    logger.info(f"  {action}")
                
                # Execute tool
                observation = await self.tool_executor.execute(action)
                step.observation = observation
                
                if self.verbose:
                    logger.info(f"  {observation}")
                
                # Add to messages for next iteration
                messages.append(llm_response)
                messages.append(f"Observation: {json.dumps(observation.content, ensure_ascii=False)}")
            
            trace.add_step(step)
            
            # Safety check - no action parsed
            if not action:
                messages.append(llm_response)
                messages.append("Observation: Action parse edilemedi. Lütfen doğru formatta devam et.")
        
        # Finalize trace
        trace.completed_at = datetime.now()
        trace.total_time_ms = (time.time() - start_time) * 1000
        
        # If no final answer after max iterations
        if not trace.final_answer:
            trace.final_answer = "Maksimum iterasyona ulaşıldı. Kesin bir cevap verilemedi."
            trace.success = False
        
        self._traces.append(trace)
        
        if self.verbose:
            logger.info(trace.format_trace())
        
        return trace
    
    def run_sync(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReActTrace:
        """Senkron çalıştır."""
        return asyncio.run(self.run(query, context))
    
    def get_traces(self, limit: int = 10) -> List[ReActTrace]:
        """Son trace'leri döndür."""
        return self._traces[-limit:]
    
    def get_last_trace(self) -> Optional[ReActTrace]:
        """Son trace'i döndür."""
        return self._traces[-1] if self._traces else None


# ============================================================================
# REACT WITH MEMORY
# ============================================================================

class ReActAgentWithMemory(ReActAgent):
    """
    Memory destekli ReAct Agent.
    
    Önceki konuşmaları ve öğrenilen bilgileri hatırlar.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        from core.memory import memory_manager
        self.memory_manager = memory_manager
        
        self._session_id: Optional[str] = None
    
    def set_session(self, session_id: str):
        """Session ID ayarla."""
        self._session_id = session_id
    
    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ReActTrace:
        """Memory-aware ReAct çalıştır."""
        # Enrich context with memory
        if self._session_id:
            memory_context = self.memory_manager.get_context_for_query(
                self._session_id,
                query,
            )
            
            context = context or {}
            context["memory"] = memory_context
        
        # Run normal ReAct
        trace = await super().run(query, context)
        
        # Store interaction in memory
        if self._session_id and trace.success:
            self.memory_manager.add_interaction(
                self._session_id,
                query,
                trace.final_answer,
            )
            
            # Learn important facts
            if trace.thoughts_count > 3:
                # Complex reasoning - worth remembering
                self.memory_manager.learn_from_conversation(
                    content=f"Q: {query} A: {trace.final_answer[:500]}",
                    importance=0.7,
                    source="react_agent",
                )
        
        return trace


# ============================================================================
# STREAMING REACT
# ============================================================================

class StreamingReActAgent(ReActAgent):
    """
    Streaming destekli ReAct Agent.
    
    Her adımı anlık olarak stream eder.
    """
    
    async def run_streaming(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """
        Streaming ReAct çalıştır.
        
        Yields:
            Dict with step information
        """
        import time
        start_time = time.time()
        
        trace = ReActTrace(query=query)
        self._current_trace = trace
        
        yield {"type": "start", "query": query}
        
        system_prompt = self._build_system_prompt()
        messages = [f"Soru: {query}"]
        
        if context:
            messages[0] += f"\n\nEk Bağlam:\n{json.dumps(context, ensure_ascii=False)}"
        
        step_number = 0
        
        while step_number < self.max_iterations:
            step_number += 1
            
            yield {"type": "step_start", "step": step_number}
            
            conversation = "\n\n".join(messages)
            
            llm_response = llm_manager.generate(
                prompt=conversation,
                system_prompt=system_prompt,
                temperature=self.temperature,
            )
            
            thought, action = self._parse_llm_response(llm_response)
            
            if thought:
                yield {
                    "type": "thought",
                    "step": step_number,
                    "content": thought.content,
                    "thought_type": thought.thought_type.value,
                }
            
            step = ReActStep(
                step_number=step_number,
                step_type=ReActStepType.THOUGHT,
                thought=thought,
                action=action,
            )
            
            if action and action.action_type == ActionType.FINISH:
                final_answer = action.arguments.get("answer", "")
                step.final_answer = final_answer
                trace.add_step(step)
                trace.final_answer = final_answer
                
                yield {
                    "type": "final_answer",
                    "step": step_number,
                    "answer": final_answer,
                }
                break
            
            if action and action.tool_name:
                yield {
                    "type": "action",
                    "step": step_number,
                    "tool": action.tool_name,
                    "arguments": action.arguments,
                }
                
                observation = await self.tool_executor.execute(action)
                step.observation = observation
                
                yield {
                    "type": "observation",
                    "step": step_number,
                    "content": observation.content,
                    "success": observation.success,
                }
                
                messages.append(llm_response)
                messages.append(f"Observation: {json.dumps(observation.content, ensure_ascii=False)}")
            
            trace.add_step(step)
        
        trace.completed_at = datetime.now()
        trace.total_time_ms = (time.time() - start_time) * 1000
        
        if not trace.final_answer:
            trace.final_answer = "Maksimum iterasyona ulaşıldı."
            trace.success = False
        
        self._traces.append(trace)
        
        yield {
            "type": "complete",
            "success": trace.success,
            "total_steps": len(trace.steps),
            "total_time_ms": trace.total_time_ms,
        }


# ============================================================================
# FACTORY & SINGLETON
# ============================================================================

def create_react_agent(
    name: str = "ReActAgent",
    with_memory: bool = False,
    streaming: bool = False,
    **kwargs,
) -> ReActAgent:
    """
    ReAct Agent factory.
    
    Args:
        name: Agent adı
        with_memory: Memory desteği
        streaming: Streaming desteği
        **kwargs: Ek parametreler
        
    Returns:
        ReActAgent instance
    """
    if streaming:
        return StreamingReActAgent(name=name, **kwargs)
    elif with_memory:
        return ReActAgentWithMemory(name=name, **kwargs)
    else:
        return ReActAgent(name=name, **kwargs)


# Default instance
react_agent = create_react_agent(name="DefaultReActAgent", verbose=True)
streaming_react_agent = create_react_agent(name="StreamingReActAgent", streaming=True)
