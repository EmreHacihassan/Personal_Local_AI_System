"""
Enterprise AI Assistant - Autonomous Agent System
==================================================

Gelişmiş otonom agent sistemi. Karmaşık görevleri bağımsız olarak
planlar, yürütür ve doğrular.

Özellikler:
- Multi-step task decomposition
- Automatic tool selection & execution
- Self-correction & retry mechanisms  
- Progress tracking & checkpoints
- Human-in-the-loop intervention points
- Memory & learning from past executions

Author: Enterprise AI Assistant
Date: 2026-01-20
"""

import asyncio
import json
import re
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_manager import llm_manager
from core.logger import get_logger
from tools.tool_manager import tool_manager, ToolCategory

logger = get_logger("autonomous_agent")


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class TaskStatus(str, Enum):
    """Görev durumları."""
    PENDING = "pending"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    WAITING_HUMAN = "waiting_human"  # Human intervention needed
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Adım durumları."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class InterventionType(str, Enum):
    """Human intervention türleri."""
    APPROVAL = "approval"        # Devam etmek için onay
    CLARIFICATION = "clarification"  # Açıklama gerekli
    CHOICE = "choice"           # Seçenek seçimi
    INPUT = "input"             # Kullanıcı girdisi
    REVIEW = "review"           # Sonuç inceleme


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TaskStep:
    """Görev adımı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    step_number: int = 0
    description: str = ""
    action_type: str = "tool_call"  # tool_call, llm_call, human_input
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""
    dependencies: List[str] = field(default_factory=list)  # Previous step IDs
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "step_number": self.step_number,
            "description": self.description,
            "action_type": self.action_type,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "expected_output": self.expected_output,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": str(self.result)[:500] if self.result else None,
            "error": self.error,
            "attempts": self.attempts,
            "duration_ms": self.duration_ms,
        }


@dataclass
class TaskPlan:
    """Görev planı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_description: str = ""
    goal: str = ""
    steps: List[TaskStep] = field(default_factory=list)
    current_step: int = 0
    total_steps: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_description": self.task_description,
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "created_at": self.created_at.isoformat(),
        }
    
    def get_next_step(self) -> Optional[TaskStep]:
        """Sıradaki bekleyen adımı döndür."""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check dependencies
                deps_met = all(
                    any(s.id == dep and s.status == StepStatus.COMPLETED 
                        for s in self.steps)
                    for dep in step.dependencies
                )
                if deps_met or not step.dependencies:
                    return step
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """İlerleme durumu."""
        completed = sum(1 for s in self.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == StepStatus.FAILED)
        pending = sum(1 for s in self.steps if s.status == StepStatus.PENDING)
        
        return {
            "total": len(self.steps),
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress_percent": (completed / len(self.steps) * 100) if self.steps else 0,
        }


@dataclass
class HumanIntervention:
    """Human intervention isteği."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    intervention_type: InterventionType = InterventionType.APPROVAL
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    options: List[str] = field(default_factory=list)  # For choice type
    default_option: Optional[str] = None
    required: bool = True
    timeout_seconds: Optional[float] = None
    response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.intervention_type.value,
            "message": self.message,
            "context": self.context,
            "options": self.options,
            "default_option": self.default_option,
            "required": self.required,
            "timeout_seconds": self.timeout_seconds,
            "response": self.response,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentTask:
    """Agent görevi."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_request: str = ""
    interpreted_goal: str = ""
    plan: Optional[TaskPlan] = None
    status: TaskStatus = TaskStatus.PENDING
    pending_intervention: Optional[HumanIntervention] = None
    final_result: Optional[str] = None
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_request": self.user_request,
            "interpreted_goal": self.interpreted_goal,
            "plan": self.plan.to_dict() if self.plan else None,
            "status": self.status.value,
            "pending_intervention": self.pending_intervention.to_dict() if self.pending_intervention else None,
            "final_result": self.final_result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": self.total_duration_ms,
        }
    
    def log(self, event: str, details: Optional[Dict] = None):
        """Execution log'a kaydet."""
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details or {},
        })


# =============================================================================
# AUTONOMOUS AGENT
# =============================================================================

class AutonomousAgent:
    """
    Otonom Agent - Karmaşık görevleri bağımsız olarak yürütür.
    
    Capabilities:
    - Task understanding & goal extraction
    - Automatic planning & step decomposition
    - Tool selection & execution
    - Self-correction on failures
    - Progress tracking with checkpoints
    - Human-in-the-loop when needed
    """
    
    PLANNING_PROMPT = """Sen bir otonom AI agent'ısın. Kullanıcının isteğini analiz edip adım adım plan oluştur.

KULLANICI İSTEĞİ:
{user_request}

MEVCUT BAĞLAM:
{context}

KULLANILABILIR ARAÇLAR:
{available_tools}

GÖREV: Bu isteği yerine getirmek için detaylı bir plan oluştur.

PLAN FORMATI (JSON):
{{
    "goal": "Ana hedefin kısa açıklaması",
    "steps": [
        {{
            "step_number": 1,
            "description": "Adım açıklaması",
            "action_type": "tool_call | llm_call | human_input",
            "tool_name": "araç adı (tool_call için)",
            "tool_args": {{"arg1": "value1"}},
            "expected_output": "Beklenen çıktı açıklaması",
            "dependencies": []
        }}
    ],
    "estimated_duration": "tahmini süre",
    "risks": ["olası riskler"],
    "requires_human_approval": true/false
}}

ÖNEMLİ KURALLAR:
1. Adımlar atomik ve net olmalı
2. Her adım bağımsız doğrulanabilir olmalı
3. Riskli işlemler için human_input adımı ekle
4. Bağımlılıkları doğru belirt
5. Gereksiz adım ekleme, minimal plan yap

JSON PLAN:"""

    EXECUTION_PROMPT = """Bir görevi yürütüyorsun.

ADIM BİLGİSİ:
- Açıklama: {step_description}
- Araç: {tool_name}
- Beklenen: {expected_output}

ÖNCEKİ SONUÇLAR:
{previous_results}

GÖREV: Bu adımı yürütmek için araç çağrısını hazırla.

ARAÇ ÇAĞRISI FORMATI:
{{
    "tool_name": "{tool_name}",
    "arguments": {{...}}
}}

ARAÇ ÇAĞRISI:"""

    REFLECTION_PROMPT = """Yürütülen adımın sonucunu değerlendir.

ADIM:
{step_description}

BEKLENEN:
{expected_output}

GERÇEKLEŞEN:
{actual_result}

HATA (varsa):
{error}

GÖREV: Sonucu değerlendir ve ne yapılması gerektiğini belirt.

DEĞERLENDIRME FORMATI:
{{
    "success": true/false,
    "assessment": "Değerlendirme açıklaması",
    "should_retry": true/false,
    "retry_strategy": "Yeniden deneme stratejisi (retry ise)",
    "should_continue": true/false,
    "next_action": "Sonraki aksiyon önerisi"
}}

DEĞERLENDIRME:"""

    SUMMARY_PROMPT = """Tamamlanan görevin sonucunu özetle.

KULLANICI İSTEĞİ:
{user_request}

HEDEF:
{goal}

TAMAMLANAN ADIMLAR:
{completed_steps}

SONUÇLAR:
{results}

GÖREV: Kullanıcı için anlaşılır bir özet oluştur.

ÖZET:"""

    def __init__(
        self,
        name: str = "AutonomousAgent",
        max_steps: int = 10,
        max_retries: int = 3,
        auto_approve_safe: bool = True,  # Güvenli işlemleri otomatik onayla
        verbose: bool = True,
    ):
        """
        Otonom Agent başlat.
        
        Args:
            name: Agent adı
            max_steps: Maksimum adım sayısı
            max_retries: Adım başına maksimum deneme
            auto_approve_safe: Güvenli işlemleri otomatik onayla
            verbose: Detaylı log
        """
        self.name = name
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.auto_approve_safe = auto_approve_safe
        self.verbose = verbose
        
        # Active tasks
        self._tasks: Dict[str, AgentTask] = {}
        self._intervention_callbacks: Dict[str, Callable] = {}
        
        # Executor for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def _get_available_tools(self) -> str:
        """Mevcut araçları formatla."""
        tools = tool_manager.list_tools()
        if not tools:
            return "Mevcut araç yok."
        
        lines = []
        for tool in tools:
            lines.append(f"- {tool['name']}: {tool['description']}")
        return "\n".join(lines)
    
    async def create_task(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentTask:
        """
        Yeni görev oluştur.
        
        Args:
            user_request: Kullanıcı isteği
            context: Ek bağlam
            
        Returns:
            AgentTask
        """
        task = AgentTask(
            user_request=user_request,
            context=context or {},
        )
        task.log("task_created", {"user_request": user_request})
        
        self._tasks[task.id] = task
        
        if self.verbose:
            logger.info(f"Task created: {task.id[:8]} - {user_request[:50]}...")
        
        return task
    
    async def plan_task(self, task: AgentTask) -> TaskPlan:
        """
        Görev için plan oluştur.
        
        Args:
            task: Görev
            
        Returns:
            TaskPlan
        """
        task.status = TaskStatus.PLANNING
        task.log("planning_started")
        
        # Build planning prompt
        prompt = self.PLANNING_PROMPT.format(
            user_request=task.user_request,
            context=json.dumps(task.context, ensure_ascii=False, indent=2) if task.context else "Yok",
            available_tools=self._get_available_tools(),
        )
        
        # Generate plan
        response = llm_manager.generate(
            prompt=prompt,
            system_prompt="Sen görev planlama uzmanı bir AI agent'sın. JSON formatında plan üret.",
            temperature=0.3,
        )
        
        # Parse plan
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                raise ValueError("JSON plan bulunamadı")
            
            # Create plan
            plan = TaskPlan(
                task_description=task.user_request,
                goal=plan_data.get("goal", task.user_request),
            )
            
            # Create steps
            for i, step_data in enumerate(plan_data.get("steps", [])[:self.max_steps]):
                step = TaskStep(
                    step_number=i + 1,
                    description=step_data.get("description", ""),
                    action_type=step_data.get("action_type", "tool_call"),
                    tool_name=step_data.get("tool_name"),
                    tool_args=step_data.get("tool_args", {}),
                    expected_output=step_data.get("expected_output", ""),
                    dependencies=step_data.get("dependencies", []),
                )
                plan.steps.append(step)
            
            plan.total_steps = len(plan.steps)
            task.plan = plan
            task.interpreted_goal = plan.goal
            
            # Check if human approval needed
            if plan_data.get("requires_human_approval", False):
                task.pending_intervention = HumanIntervention(
                    intervention_type=InterventionType.APPROVAL,
                    message=f"Bu görev için {len(plan.steps)} adımlık bir plan hazırlandı. Devam edilsin mi?",
                    context={"plan_summary": plan.to_dict()},
                    options=["Evet, devam et", "Hayır, iptal et", "Planı düzenle"],
                )
                task.status = TaskStatus.WAITING_HUMAN
            
            task.log("planning_completed", {"steps_count": len(plan.steps)})
            
            if self.verbose:
                logger.info(f"Plan created: {len(plan.steps)} steps")
            
            return plan
            
        except Exception as e:
            task.log("planning_failed", {"error": str(e)})
            task.error = f"Plan oluşturulamadı: {e}"
            task.status = TaskStatus.FAILED
            raise
    
    async def execute_step(
        self,
        task: AgentTask,
        step: TaskStep,
    ) -> Tuple[bool, Any]:
        """
        Tek bir adımı yürüt.
        
        Args:
            task: Görev
            step: Adım
            
        Returns:
            (success, result) tuple
        """
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        step.attempts += 1
        
        task.log("step_started", {
            "step_id": step.id,
            "step_number": step.step_number,
            "attempt": step.attempts,
        })
        
        if self.verbose:
            logger.info(f"  Step {step.step_number}: {step.description[:50]}...")
        
        try:
            if step.action_type == "tool_call" and step.tool_name:
                # Execute tool
                result = await tool_manager.execute_tool(
                    step.tool_name,
                    step.tool_args,
                )
                
                if result.get("success"):
                    step.result = result.get("data")
                    step.status = StepStatus.COMPLETED
                    success = True
                else:
                    step.error = result.get("error", "Unknown error")
                    success = False
                    
            elif step.action_type == "llm_call":
                # LLM call
                previous_results = self._get_previous_results(task)
                
                prompt = self.EXECUTION_PROMPT.format(
                    step_description=step.description,
                    tool_name=step.tool_name or "N/A",
                    expected_output=step.expected_output,
                    previous_results=json.dumps(previous_results, ensure_ascii=False),
                )
                
                response = llm_manager.generate(prompt)
                step.result = response
                step.status = StepStatus.COMPLETED
                success = True
                
            elif step.action_type == "human_input":
                # Request human input
                task.pending_intervention = HumanIntervention(
                    intervention_type=InterventionType.INPUT,
                    message=step.description,
                    context={"step": step.to_dict()},
                )
                task.status = TaskStatus.WAITING_HUMAN
                return False, None
                
            else:
                step.error = f"Bilinmeyen action type: {step.action_type}"
                success = False
            
        except Exception as e:
            step.error = str(e)
            success = False
        
        # Calculate duration
        step.completed_at = datetime.now()
        step.duration_ms = (step.completed_at - step.started_at).total_seconds() * 1000
        
        # Handle failure
        if not success:
            if step.attempts < step.max_attempts:
                step.status = StepStatus.RETRYING
                task.log("step_retrying", {
                    "step_id": step.id,
                    "attempt": step.attempts,
                    "error": step.error,
                })
                
                # Self-correction: analyze failure and adjust
                await self._self_correct(task, step)
                
                # Retry
                return await self.execute_step(task, step)
            else:
                step.status = StepStatus.FAILED
                task.log("step_failed", {
                    "step_id": step.id,
                    "error": step.error,
                })
        else:
            task.log("step_completed", {
                "step_id": step.id,
                "duration_ms": step.duration_ms,
            })
        
        return success, step.result
    
    async def _self_correct(self, task: AgentTask, step: TaskStep):
        """
        Başarısız adım için düzeltme stratejisi uygula.
        
        Args:
            task: Görev
            step: Başarısız adım
        """
        task.log("self_correction", {"step_id": step.id, "error": step.error})
        
        # Analyze failure
        prompt = self.REFLECTION_PROMPT.format(
            step_description=step.description,
            expected_output=step.expected_output,
            actual_result=step.result,
            error=step.error,
        )
        
        response = llm_manager.generate(
            prompt=prompt,
            system_prompt="Sen hata analizi uzmanı bir AI'sın. JSON formatında analiz yap.",
            temperature=0.3,
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Apply correction strategy
                if analysis.get("retry_strategy"):
                    strategy = analysis["retry_strategy"]
                    
                    # Modify tool args based on strategy
                    if "farklı parametre" in strategy.lower():
                        # LLM'den yeni parametreler iste
                        pass
                    
                    task.log("correction_applied", {"strategy": strategy})
                    
        except Exception as e:
            logger.warning(f"Self-correction failed: {e}")
    
    def _get_previous_results(self, task: AgentTask) -> Dict[str, Any]:
        """Önceki adım sonuçlarını al."""
        if not task.plan:
            return {}
        
        results = {}
        for step in task.plan.steps:
            if step.status == StepStatus.COMPLETED and step.result:
                results[f"step_{step.step_number}"] = {
                    "description": step.description,
                    "result": str(step.result)[:500],
                }
        return results
    
    async def run_task(
        self,
        task: AgentTask,
        intervention_callback: Optional[Callable] = None,
    ) -> AgentTask:
        """
        Görevi baştan sona yürüt.
        
        Args:
            task: Görev
            intervention_callback: Human intervention callback
            
        Returns:
            Tamamlanmış görev
        """
        start_time = time.time()
        task.started_at = datetime.now()
        task.status = TaskStatus.IN_PROGRESS
        task.log("execution_started")
        
        if intervention_callback:
            self._intervention_callbacks[task.id] = intervention_callback
        
        try:
            # Create plan if not exists
            if not task.plan:
                await self.plan_task(task)
            
            # Check for pending intervention
            if task.status == TaskStatus.WAITING_HUMAN:
                if intervention_callback and task.pending_intervention:
                    response = await intervention_callback(task.pending_intervention)
                    task.pending_intervention.response = response
                    task.pending_intervention.responded_at = datetime.now()
                    task.pending_intervention = None
                    task.status = TaskStatus.IN_PROGRESS
                else:
                    return task  # Wait for intervention
            
            # Execute steps
            while True:
                next_step = task.plan.get_next_step()
                
                if not next_step:
                    # All steps completed or no more executable steps
                    break
                
                task.plan.current_step = next_step.step_number
                success, result = await self.execute_step(task, next_step)
                
                # Check for intervention
                if task.status == TaskStatus.WAITING_HUMAN:
                    if intervention_callback and task.pending_intervention:
                        response = await intervention_callback(task.pending_intervention)
                        next_step.result = response
                        next_step.status = StepStatus.COMPLETED
                        task.pending_intervention = None
                        task.status = TaskStatus.IN_PROGRESS
                    else:
                        return task
                
                # Check for failure
                if not success and next_step.status == StepStatus.FAILED:
                    # Check if task should fail
                    progress = task.plan.get_progress()
                    if progress["failed"] >= 2:  # Too many failures
                        task.status = TaskStatus.FAILED
                        task.error = f"Çok fazla adım başarısız oldu"
                        break
            
            # Generate final result
            if task.status != TaskStatus.FAILED:
                await self._generate_summary(task)
                task.status = TaskStatus.COMPLETED
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.log("execution_failed", {"error": str(e)})
        
        task.completed_at = datetime.now()
        task.total_duration_ms = (time.time() - start_time) * 1000
        task.log("execution_completed", {
            "status": task.status.value,
            "duration_ms": task.total_duration_ms,
        })
        
        if self.verbose:
            logger.info(f"Task {task.id[:8]} completed: {task.status.value}")
        
        return task
    
    async def _generate_summary(self, task: AgentTask):
        """Görev özeti oluştur."""
        if not task.plan:
            return
        
        completed_steps = [
            f"{s.step_number}. {s.description}: {'✅' if s.status == StepStatus.COMPLETED else '❌'}"
            for s in task.plan.steps
        ]
        
        results = self._get_previous_results(task)
        
        prompt = self.SUMMARY_PROMPT.format(
            user_request=task.user_request,
            goal=task.interpreted_goal,
            completed_steps="\n".join(completed_steps),
            results=json.dumps(results, ensure_ascii=False, indent=2),
        )
        
        summary = llm_manager.generate(
            prompt=prompt,
            system_prompt="Sen görev özetleme uzmanı bir AI'sın. Net ve anlaşılır özetler yaz.",
            temperature=0.5,
        )
        
        task.final_result = summary
    
    async def respond_to_intervention(
        self,
        task_id: str,
        response: str,
    ) -> AgentTask:
        """
        Human intervention'a yanıt ver.
        
        Args:
            task_id: Görev ID
            response: Kullanıcı yanıtı
            
        Returns:
            Güncel görev
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Görev bulunamadı: {task_id}")
        
        if not task.pending_intervention:
            raise ValueError("Bekleyen intervention yok")
        
        task.pending_intervention.response = response
        task.pending_intervention.responded_at = datetime.now()
        
        # Handle based on intervention type
        if task.pending_intervention.intervention_type == InterventionType.APPROVAL:
            if "evet" in response.lower() or "devam" in response.lower():
                task.pending_intervention = None
                task.status = TaskStatus.IN_PROGRESS
                return await self.run_task(task)
            else:
                task.status = TaskStatus.CANCELLED
                task.pending_intervention = None
                return task
        
        elif task.pending_intervention.intervention_type == InterventionType.INPUT:
            # Store response as step result
            if task.plan:
                for step in task.plan.steps:
                    if step.action_type == "human_input" and step.status == StepStatus.RUNNING:
                        step.result = response
                        step.status = StepStatus.COMPLETED
                        break
            
            task.pending_intervention = None
            task.status = TaskStatus.IN_PROGRESS
            return await self.run_task(task)
        
        task.pending_intervention = None
        return task
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Görevi al."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> List[AgentTask]:
        """Tüm görevleri al."""
        return list(self._tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """Görevi iptal et."""
        task = self._tasks.get(task_id)
        if task and task.status in [TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.IN_PROGRESS, TaskStatus.WAITING_HUMAN]:
            task.status = TaskStatus.CANCELLED
            task.log("task_cancelled")
            return True
        return False


# =============================================================================
# STREAMING AUTONOMOUS AGENT
# =============================================================================

class StreamingAutonomousAgent(AutonomousAgent):
    """
    Streaming destekli otonom agent.
    
    Her adımı anlık olarak stream eder.
    """
    
    async def run_task_streaming(
        self,
        task: AgentTask,
    ):
        """
        Görevi streaming ile yürüt.
        
        Yields:
            Progress updates
        """
        task.started_at = datetime.now()
        task.status = TaskStatus.IN_PROGRESS
        
        yield {
            "type": "task_started",
            "task_id": task.id,
            "request": task.user_request,
        }
        
        # Planning
        yield {"type": "planning_started"}
        
        try:
            await self.plan_task(task)
            
            yield {
                "type": "plan_created",
                "goal": task.interpreted_goal,
                "steps": [s.to_dict() for s in task.plan.steps],
            }
            
            # Check intervention
            if task.pending_intervention:
                yield {
                    "type": "intervention_required",
                    "intervention": task.pending_intervention.to_dict(),
                }
                return
            
            # Execute steps
            for step in task.plan.steps:
                if step.status != StepStatus.PENDING:
                    continue
                
                yield {
                    "type": "step_started",
                    "step": step.to_dict(),
                }
                
                success, result = await self.execute_step(task, step)
                
                if task.pending_intervention:
                    yield {
                        "type": "intervention_required",
                        "intervention": task.pending_intervention.to_dict(),
                    }
                    return
                
                yield {
                    "type": "step_completed",
                    "step": step.to_dict(),
                    "success": success,
                }
            
            # Summary
            await self._generate_summary(task)
            task.status = TaskStatus.COMPLETED
            
            yield {
                "type": "task_completed",
                "task_id": task.id,
                "result": task.final_result,
                "progress": task.plan.get_progress(),
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            yield {
                "type": "task_failed",
                "task_id": task.id,
                "error": str(e),
            }


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

# Shared task store (tüm agent'lar aynı task'ları paylaşır)
_shared_tasks: Dict[str, AgentTask] = {}

# Global instances
autonomous_agent = AutonomousAgent(name="MainAgent", verbose=True)
streaming_autonomous_agent = StreamingAutonomousAgent(name="StreamingAgent", verbose=True)

# Task store'u paylaştır
autonomous_agent._tasks = _shared_tasks
streaming_autonomous_agent._tasks = _shared_tasks


def get_autonomous_agent() -> AutonomousAgent:
    """Global otonom agent'ı döndür."""
    return autonomous_agent


def get_streaming_agent() -> StreamingAutonomousAgent:
    """Global streaming agent'ı döndür."""
    return streaming_autonomous_agent
