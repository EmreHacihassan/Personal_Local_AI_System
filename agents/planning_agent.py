"""
Enterprise AI Assistant - Planning Agent
========================================

Task Decomposition & Planning System
Endüstri Standartlarında Kurumsal AI Çözümü

Bu modül, karmaşık görevleri alt görevlere ayıran ve plan oluşturan
akıllı planlama sistemini içerir.

Desteklenen Planlama Stratejileri:
- Linear Planning: Sıralı adımlar
- Tree of Thoughts (ToT): Ağaç yapısında düşünce dalları
- Plan-and-Execute: Önce plan, sonra uygula
- Hierarchical Planning: Hiyerarşik alt görevler
- Adaptive Planning: Dinamik plan güncelleme

Referanslar:
- Tree of Thoughts (Yao et al., 2023)
- Plan-and-Solve Prompting (Wang et al., 2023)
- Least-to-Most Prompting (Zhou et al., 2022)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import json
import re
import uuid
import asyncio
from collections import defaultdict
import heapq

import sys
sys.path.append('..')

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("planning_agent")


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class PlanningStrategy(str, Enum):
    """Planlama stratejileri."""
    LINEAR = "linear"                   # Sıralı adımlar
    TREE_OF_THOUGHTS = "tree_of_thoughts"  # ToT
    PLAN_AND_EXECUTE = "plan_and_execute"  # Plan → Execute
    HIERARCHICAL = "hierarchical"       # Hiyerarşik
    ADAPTIVE = "adaptive"               # Dinamik
    LEAST_TO_MOST = "least_to_most"    # Basit → Karmaşık


class TaskStatus(str, Enum):
    """Görev durumları."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Görev öncelikleri."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskComplexity(str, Enum):
    """Görev karmaşıklığı."""
    TRIVIAL = "trivial"        # Tek adımda çözülebilir
    SIMPLE = "simple"          # 2-3 adım
    MODERATE = "moderate"      # 4-6 adım
    COMPLEX = "complex"        # 7+ adım
    VERY_COMPLEX = "very_complex"  # Alt planlara ayrılmalı


@dataclass
class TaskNode:
    """Görev düğümü - ağaç yapısı için."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    complexity: TaskComplexity = TaskComplexity.SIMPLE
    
    # Ağaç yapısı
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # Bağımlılıklar
    dependencies: List[str] = field(default_factory=list)  # Önce tamamlanması gereken görevler
    blocked_by: List[str] = field(default_factory=list)    # Bekleyen görevler
    
    # Uygulama detayları
    assigned_agent: Optional[str] = None
    required_tools: List[str] = field(default_factory=list)
    estimated_duration_minutes: float = 5.0
    actual_duration_minutes: Optional[float] = None
    
    # Sonuç
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other: "TaskNode") -> bool:
        """Priority queue için karşılaştırma."""
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        return priority_order[self.priority] < priority_order[other.priority]
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Görev hazır mı (bağımlılıklar tamamlandı mı)?"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "complexity": self.complexity.value,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "dependencies": self.dependencies,
            "assigned_agent": self.assigned_agent,
            "required_tools": self.required_tools,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "actual_duration_minutes": self.actual_duration_minutes,
            "result": str(self.result)[:500] if self.result else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __str__(self) -> str:
        status_emoji = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⏭️",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.CANCELLED: "🚫",
        }
        return f"{status_emoji.get(self.status, '?')} [{self.id}] {self.name}"


@dataclass
class ThoughtBranch:
    """Tree of Thoughts için düşünce dalı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    thought: str = ""
    score: float = 0.0  # Değerlendirme skoru (0-1)
    depth: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    is_terminal: bool = False
    selected: bool = False
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "thought": self.thought,
            "score": self.score,
            "depth": self.depth,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "is_terminal": self.is_terminal,
            "selected": self.selected,
            "reasoning": self.reasoning,
        }


@dataclass
class ExecutionPlan:
    """Uygulama planı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    original_goal: str = ""
    strategy: PlanningStrategy = PlanningStrategy.LINEAR
    
    # Görevler
    tasks: Dict[str, TaskNode] = field(default_factory=dict)
    root_task_ids: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    
    # Tree of Thoughts
    thought_branches: Dict[str, ThoughtBranch] = field(default_factory=dict)
    selected_path: List[str] = field(default_factory=list)
    
    # Durum
    status: TaskStatus = TaskStatus.PENDING
    current_task_id: Optional[str] = None
    completed_task_ids: Set[str] = field(default_factory=set)
    failed_task_ids: Set[str] = field(default_factory=set)
    
    # İstatistikler
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    estimated_total_duration_minutes: float = 0.0
    actual_total_duration_minutes: float = 0.0
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_task(self, task: TaskNode, parent_id: Optional[str] = None):
        """Plana görev ekle."""
        self.tasks[task.id] = task
        self.total_tasks += 1
        self.estimated_total_duration_minutes += task.estimated_duration_minutes
        
        if parent_id and parent_id in self.tasks:
            task.parent_id = parent_id
            self.tasks[parent_id].children_ids.append(task.id)
        else:
            self.root_task_ids.append(task.id)
    
    def get_next_tasks(self) -> List[TaskNode]:
        """Çalıştırılabilir sonraki görevleri döndür."""
        ready_tasks = []
        
        for task_id, task in self.tasks.items():
            if task.status == TaskStatus.PENDING and task.is_ready(self.completed_task_ids):
                ready_tasks.append(task)
        
        # Önceliğe göre sırala
        ready_tasks.sort()
        return ready_tasks
    
    def mark_completed(self, task_id: str, result: Any = None):
        """Görevi tamamlandı olarak işaretle."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            if task.started_at:
                task.actual_duration_minutes = (
                    task.completed_at - task.started_at
                ).total_seconds() / 60
            
            self.completed_task_ids.add(task_id)
            self.completed_tasks += 1
    
    def mark_failed(self, task_id: str, error: str):
        """Görevi başarısız olarak işaretle."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.now()
            
            self.failed_task_ids.add(task_id)
            self.failed_tasks += 1
    
    def get_progress(self) -> Dict[str, Any]:
        """İlerleme durumu."""
        return {
            "total": self.total_tasks,
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "pending": self.total_tasks - self.completed_tasks - self.failed_tasks,
            "percentage": (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "original_goal": self.original_goal,
            "strategy": self.strategy.value,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "root_task_ids": self.root_task_ids,
            "execution_order": self.execution_order,
            "status": self.status.value,
            "progress": self.get_progress(),
            "created_at": self.created_at.isoformat(),
        }
    
    def visualize(self) -> str:
        """Plan görselleştirmesi."""
        lines = [
            f"╔══════════════════════════════════════════════════════════════╗",
            f"║ 📋 Plan: {self.name[:50]:<50} ║",
            f"║ Strategy: {self.strategy.value:<49} ║",
            f"╠══════════════════════════════════════════════════════════════╣",
        ]
        
        def add_task_tree(task_id: str, indent: int = 0):
            task = self.tasks.get(task_id)
            if not task:
                return
            
            prefix = "│   " * indent
            lines.append(f"║ {prefix}{task} ")
            
            for child_id in task.children_ids:
                add_task_tree(child_id, indent + 1)
        
        for root_id in self.root_task_ids:
            add_task_tree(root_id)
        
        progress = self.get_progress()
        lines.extend([
            f"╠══════════════════════════════════════════════════════════════╣",
            f"║ Progress: {progress['completed']}/{progress['total']} ({progress['percentage']:.1f}%) ",
            f"╚══════════════════════════════════════════════════════════════╝",
        ])
        
        return "\n".join(lines)


# ============================================================================
# TASK DECOMPOSER
# ============================================================================

class TaskDecomposer:
    """
    Görev Ayrıştırıcı.
    
    Karmaşık görevleri alt görevlere ayırır.
    """
    
    DECOMPOSITION_PROMPT = """Sen bir görev planlama uzmanısın. Verilen hedefi alt görevlere ayır.

HEDEF: {goal}

KURALLAR:
1. Her alt görev açık ve uygulanabilir olmalı
2. Alt görevler mantıksal sırada olmalı
3. Bağımlılıkları belirle (hangi görev hangisine bağlı)
4. Her görev için tahmini süre ver
5. Gerekli araçları/kaynakları belirt

ÇIKTI FORMATI (JSON):
{{
    "analysis": "Hedefin kısa analizi",
    "complexity": "trivial|simple|moderate|complex|very_complex",
    "tasks": [
        {{
            "name": "Görev adı",
            "description": "Detaylı açıklama",
            "dependencies": ["bağımlı görev adları"],
            "estimated_minutes": 5,
            "required_tools": ["tool1", "tool2"],
            "priority": "critical|high|medium|low"
        }}
    ],
    "success_criteria": "Başarı kriterleri",
    "risks": ["Olası riskler"]
}}

Yanıtı SADECE JSON olarak ver, başka açıklama ekleme."""

    def __init__(self, temperature: float = 0.3):
        self.temperature = temperature
    
    def decompose(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[TaskNode], Dict[str, Any]]:
        """
        Hedefi alt görevlere ayır.
        
        Args:
            goal: Ana hedef
            context: Ek bağlam
            
        Returns:
            (TaskNode listesi, analiz metadata)
        """
        prompt = self.DECOMPOSITION_PROMPT.format(goal=goal)
        
        if context:
            prompt += f"\n\nEk Bağlam:\n{json.dumps(context, ensure_ascii=False)}"
        
        response = llm_manager.generate(
            prompt=prompt,
            temperature=self.temperature,
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            tasks = []
            task_name_to_id = {}
            
            for i, task_data in enumerate(data.get("tasks", [])):
                task = TaskNode(
                    name=task_data.get("name", f"Task {i+1}"),
                    description=task_data.get("description", ""),
                    priority=TaskPriority(task_data.get("priority", "medium")),
                    estimated_duration_minutes=task_data.get("estimated_minutes", 5),
                    required_tools=task_data.get("required_tools", []),
                )
                
                task_name_to_id[task.name] = task.id
                tasks.append(task)
            
            # Resolve dependencies
            for i, task_data in enumerate(data.get("tasks", [])):
                task = tasks[i]
                for dep_name in task_data.get("dependencies", []):
                    if dep_name in task_name_to_id:
                        task.dependencies.append(task_name_to_id[dep_name])
            
            # Set complexity
            complexity = TaskComplexity(data.get("complexity", "moderate"))
            for task in tasks:
                task.complexity = complexity
            
            metadata = {
                "analysis": data.get("analysis", ""),
                "complexity": complexity.value,
                "success_criteria": data.get("success_criteria", ""),
                "risks": data.get("risks", []),
            }
            
            return tasks, metadata
            
        except Exception as e:
            logger.error(f"Failed to decompose task: {e}")
            # Return single task as fallback
            return [
                TaskNode(
                    name=goal[:50],
                    description=goal,
                    complexity=TaskComplexity.SIMPLE,
                )
            ], {"error": str(e)}
    
    def estimate_complexity(self, goal: str) -> TaskComplexity:
        """Hedefin karmaşıklığını tahmin et."""
        prompt = f"""Aşağıdaki görevin karmaşıklığını değerlendir:

GÖREV: {goal}

Karmaşıklık seviyeleri:
- trivial: Tek adımda, araç gerektirmeden çözülebilir
- simple: 2-3 basit adım
- moderate: 4-6 adım, bazı araçlar gerekebilir
- complex: 7+ adım, multiple araç ve kaynak gerektirir
- very_complex: Alt planlara ayrılması gereken çok karmaşık görev

Sadece karmaşıklık seviyesini yaz (trivial/simple/moderate/complex/very_complex):"""

        response = llm_manager.generate(prompt=prompt, temperature=0.1)
        
        for level in TaskComplexity:
            if level.value in response.lower():
                return level
        
        return TaskComplexity.MODERATE


# ============================================================================
# TREE OF THOUGHTS
# ============================================================================

class TreeOfThoughts:
    """
    Tree of Thoughts (ToT) implementasyonu.
    
    Farklı düşünce dallarını explore eder ve en iyi yolu seçer.
    """
    
    GENERATION_PROMPT = """Aşağıdaki problem için {num_thoughts} farklı düşünce/yaklaşım üret.

PROBLEM: {problem}

{parent_context}

Her düşünce farklı bir perspektif veya strateji olmalı.
Her düşünceyi ayrı satırda, numaralı olarak yaz:

1. [Düşünce 1]
2. [Düşünce 2]
..."""

    EVALUATION_PROMPT = """Aşağıdaki düşünceyi değerlendir.

PROBLEM: {problem}
DÜŞÜNCE: {thought}

Değerlendirme kriterleri:
1. Uygulanabilirlik (0-1)
2. Tamamlılık (0-1)
3. Verimlilik (0-1)
4. Risk seviyesi (0-1, düşük risk = yüksek skor)

Değerlendirmeyi şu formatta yap:
{{
    "score": 0.0-1.0,
    "reasoning": "Değerlendirme gerekçesi",
    "pros": ["Avantajlar"],
    "cons": ["Dezavantajlar"],
    "is_terminal": true/false
}}"""

    def __init__(
        self,
        max_depth: int = 2,
        branching_factor: int = 2,
        beam_width: int = 1,
        temperature: float = 0.7,
    ):
        """
        ToT başlat.
        
        Args:
            max_depth: Maksimum derinlik
            branching_factor: Her seviyede üretilecek düşünce sayısı
            beam_width: Her seviyede tutulacak en iyi düşünce sayısı
            temperature: LLM temperature
        """
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.beam_width = beam_width
        self.temperature = temperature
        
        self.branches: Dict[str, ThoughtBranch] = {}
        self.root_ids: List[str] = []
    
    def generate_thoughts(
        self,
        problem: str,
        parent_branch: Optional[ThoughtBranch] = None,
    ) -> List[ThoughtBranch]:
        """Yeni düşünce dalları üret."""
        parent_context = ""
        if parent_branch:
            parent_context = f"ÖNCEKİ DÜŞÜNCE: {parent_branch.thought}\n"
        
        prompt = self.GENERATION_PROMPT.format(
            problem=problem,
            num_thoughts=self.branching_factor,
            parent_context=parent_context,
        )
        
        response = llm_manager.generate(
            prompt=prompt,
            temperature=self.temperature,
        )
        
        branches = []
        depth = parent_branch.depth + 1 if parent_branch else 0
        
        # Parse numbered thoughts
        lines = response.strip().split("\n")
        for line in lines:
            match = re.match(r'\d+\.\s*(.+)', line.strip())
            if match:
                thought_text = match.group(1).strip()
                if thought_text:
                    branch = ThoughtBranch(
                        thought=thought_text,
                        depth=depth,
                        parent_id=parent_branch.id if parent_branch else None,
                    )
                    branches.append(branch)
                    self.branches[branch.id] = branch
        
        # Update parent's children
        if parent_branch:
            parent_branch.children_ids = [b.id for b in branches]
        else:
            self.root_ids = [b.id for b in branches]
        
        return branches
    
    def evaluate_thought(self, problem: str, branch: ThoughtBranch) -> float:
        """Düşünceyi değerlendir."""
        prompt = self.EVALUATION_PROMPT.format(
            problem=problem,
            thought=branch.thought,
        )
        
        response = llm_manager.generate(
            prompt=prompt,
            temperature=0.1,
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                branch.score = float(data.get("score", 0.5))
                branch.reasoning = data.get("reasoning", "")
                branch.is_terminal = data.get("is_terminal", False)
                branch.metadata["pros"] = data.get("pros", [])
                branch.metadata["cons"] = data.get("cons", [])
                return branch.score
        except Exception as e:
            logger.warning(f"Failed to parse evaluation: {e}")
            branch.score = 0.5
        
        return branch.score
    
    def search(self, problem: str) -> List[ThoughtBranch]:
        """
        Beam search ile en iyi düşünce yolunu bul.
        
        Args:
            problem: Çözülecek problem
            
        Returns:
            En iyi düşünce yolu
        """
        self.branches.clear()
        self.root_ids.clear()
        
        # Generate root thoughts
        current_level = self.generate_thoughts(problem)
        
        # Evaluate root thoughts
        for branch in current_level:
            self.evaluate_thought(problem, branch)
        
        # Sort by score and keep beam_width best
        current_level.sort(key=lambda x: x.score, reverse=True)
        current_level = current_level[:self.beam_width]
        
        # Mark selected
        for branch in current_level:
            branch.selected = True
        
        # Iterate through depths
        for depth in range(1, self.max_depth):
            next_level = []
            
            for parent in current_level:
                if parent.is_terminal:
                    next_level.append(parent)
                    continue
                
                # Generate children
                children = self.generate_thoughts(problem, parent)
                
                # Evaluate children
                for child in children:
                    self.evaluate_thought(problem, child)
                
                next_level.extend(children)
            
            if not next_level:
                break
            
            # Keep best
            next_level.sort(key=lambda x: x.score, reverse=True)
            current_level = next_level[:self.beam_width]
            
            for branch in current_level:
                branch.selected = True
        
        # Return best path
        if current_level:
            best = max(current_level, key=lambda x: x.score)
            return self._get_path(best)
        
        return []
    
    def _get_path(self, branch: ThoughtBranch) -> List[ThoughtBranch]:
        """Kökten verilen dala kadar yolu döndür."""
        path = []
        current = branch
        
        while current:
            path.append(current)
            if current.parent_id:
                current = self.branches.get(current.parent_id)
            else:
                break
        
        path.reverse()
        return path
    
    def get_best_thought(self) -> Optional[ThoughtBranch]:
        """En iyi düşünceyi döndür."""
        if not self.branches:
            return None
        
        return max(self.branches.values(), key=lambda x: x.score)
    
    def visualize(self) -> str:
        """Ağacı görselleştir."""
        lines = ["🌳 Tree of Thoughts", ""]
        
        def add_branch(branch_id: str, indent: int = 0):
            branch = self.branches.get(branch_id)
            if not branch:
                return
            
            prefix = "  " * indent
            selected = "🌟" if branch.selected else "  "
            score = f"({branch.score:.2f})"
            lines.append(f"{prefix}{selected} {branch.thought[:60]}... {score}")
            
            for child_id in branch.children_ids:
                add_branch(child_id, indent + 1)
        
        for root_id in self.root_ids:
            add_branch(root_id)
        
        return "\n".join(lines)


# ============================================================================
# PLANNING AGENT
# ============================================================================

class PlanningAgent:
    """
    Planning Agent - Karmaşık görevleri planlayan akıllı agent.
    
    Özellikler:
    - Task decomposition
    - Multiple planning strategies
    - Tree of Thoughts reasoning
    - Adaptive replanning
    - Progress tracking
    - Rollback capability
    """
    
    def __init__(
        self,
        name: str = "PlanningAgent",
        default_strategy: PlanningStrategy = PlanningStrategy.PLAN_AND_EXECUTE,
        enable_tot: bool = True,
        verbose: bool = True,
    ):
        """
        Planning Agent başlat.
        
        Args:
            name: Agent adı
            default_strategy: Varsayılan planlama stratejisi
            enable_tot: Tree of Thoughts kullan
            verbose: Detaylı log
        """
        self.name = name
        self.default_strategy = default_strategy
        self.enable_tot = enable_tot
        self.verbose = verbose
        
        self.decomposer = TaskDecomposer()
        self.tot = TreeOfThoughts() if enable_tot else None
        
        self._plans: Dict[str, ExecutionPlan] = {}
        self._current_plan: Optional[ExecutionPlan] = None
        
        # Task executors (registered by type)
        self._executors: Dict[str, Callable] = {}
    
    def register_executor(
        self,
        task_type: str,
        executor: Callable[[TaskNode], Any],
    ):
        """Görev türü için executor kaydet."""
        self._executors[task_type] = executor
    
    def _select_strategy(self, goal: str, complexity: TaskComplexity) -> PlanningStrategy:
        """Hedefe uygun strateji seç. OPTIMIZED: ToT disabled for performance."""
        if complexity == TaskComplexity.TRIVIAL:
            return PlanningStrategy.LINEAR
        elif complexity == TaskComplexity.SIMPLE:
            return PlanningStrategy.LINEAR
        elif complexity == TaskComplexity.MODERATE:
            return PlanningStrategy.LINEAR  # Changed from PLAN_AND_EXECUTE for speed
        elif complexity == TaskComplexity.COMPLEX:
            # OPTIMIZATION: ToT is too slow for local models, use LINEAR instead
            return PlanningStrategy.LINEAR
        else:  # VERY_COMPLEX
            return PlanningStrategy.HIERARCHICAL
    
    def create_plan(
        self,
        goal: str,
        strategy: Optional[PlanningStrategy] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """
        Hedef için plan oluştur.
        
        Args:
            goal: Ana hedef
            strategy: Planlama stratejisi (None = otomatik)
            context: Ek bağlam
            
        Returns:
            ExecutionPlan
        """
        # Estimate complexity
        complexity = self.decomposer.estimate_complexity(goal)
        
        if self.verbose:
            logger.info(f"Goal complexity: {complexity.value}")
        
        # Select strategy
        if strategy is None:
            strategy = self._select_strategy(goal, complexity)
        
        if self.verbose:
            logger.info(f"Selected strategy: {strategy.value}")
        
        # Create plan based on strategy
        if strategy == PlanningStrategy.LINEAR:
            plan = self._create_linear_plan(goal, context)
        elif strategy == PlanningStrategy.TREE_OF_THOUGHTS:
            plan = self._create_tot_plan(goal, context)
        elif strategy == PlanningStrategy.HIERARCHICAL:
            plan = self._create_hierarchical_plan(goal, context)
        elif strategy == PlanningStrategy.LEAST_TO_MOST:
            plan = self._create_least_to_most_plan(goal, context)
        else:
            plan = self._create_plan_and_execute(goal, context)
        
        plan.strategy = strategy
        plan.original_goal = goal
        
        # Determine execution order
        plan.execution_order = self._topological_sort(plan)
        
        self._plans[plan.id] = plan
        self._current_plan = plan
        
        if self.verbose:
            logger.info(f"\n{plan.visualize()}")
        
        return plan
    
    def _create_linear_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Sıralı plan oluştur."""
        plan = ExecutionPlan(name=f"Linear: {goal[:30]}")
        
        tasks, metadata = self.decomposer.decompose(goal, context)
        plan.metadata = metadata
        
        prev_task_id = None
        for task in tasks:
            if prev_task_id:
                task.dependencies.append(prev_task_id)
            plan.add_task(task)
            prev_task_id = task.id
        
        return plan
    
    def _create_tot_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Tree of Thoughts ile plan oluştur."""
        plan = ExecutionPlan(name=f"ToT: {goal[:30]}")
        
        if not self.tot:
            return self._create_linear_plan(goal, context)
        
        # Run ToT search
        best_path = self.tot.search(goal)
        
        if self.verbose:
            logger.info(f"\n{self.tot.visualize()}")
        
        # Store thought branches
        plan.thought_branches = self.tot.branches.copy()
        plan.selected_path = [b.id for b in best_path]
        
        # Convert best path to tasks
        for i, branch in enumerate(best_path):
            task = TaskNode(
                name=f"Step {i+1}",
                description=branch.thought,
                metadata={"thought_id": branch.id, "score": branch.score},
            )
            
            if i > 0:
                prev_task = list(plan.tasks.values())[i-1]
                task.dependencies.append(prev_task.id)
            
            plan.add_task(task)
        
        return plan
    
    def _create_hierarchical_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Hiyerarşik plan oluştur."""
        plan = ExecutionPlan(name=f"Hierarchical: {goal[:30]}")
        
        # Decompose main goal
        main_tasks, metadata = self.decomposer.decompose(goal, context)
        plan.metadata = metadata
        
        for task in main_tasks:
            plan.add_task(task)
            
            # Check if task is complex enough to decompose further
            if task.complexity in [TaskComplexity.COMPLEX, TaskComplexity.VERY_COMPLEX]:
                sub_tasks, _ = self.decomposer.decompose(
                    task.description,
                    {"parent_task": task.name},
                )
                
                for sub_task in sub_tasks:
                    plan.add_task(sub_task, parent_id=task.id)
        
        return plan
    
    def _create_plan_and_execute(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Plan-and-Execute stratejisi."""
        return self._create_linear_plan(goal, context)
    
    def _create_least_to_most_plan(
        self,
        goal: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """Least-to-Most: Basit → Karmaşık sıralama."""
        plan = ExecutionPlan(name=f"LeastToMost: {goal[:30]}")
        
        tasks, metadata = self.decomposer.decompose(goal, context)
        plan.metadata = metadata
        
        # Sort by complexity (trivial first)
        complexity_order = {
            TaskComplexity.TRIVIAL: 0,
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 2,
            TaskComplexity.COMPLEX: 3,
            TaskComplexity.VERY_COMPLEX: 4,
        }
        
        tasks.sort(key=lambda t: complexity_order.get(t.complexity, 2))
        
        prev_task_id = None
        for task in tasks:
            if prev_task_id:
                task.dependencies.append(prev_task_id)
            plan.add_task(task)
            prev_task_id = task.id
        
        return plan
    
    def _topological_sort(self, plan: ExecutionPlan) -> List[str]:
        """Görevleri bağımlılıklara göre sırala."""
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for task_id, task in plan.tasks.items():
            for dep_id in task.dependencies:
                graph[dep_id].append(task_id)
                in_degree[task_id] += 1
        
        # Start with tasks that have no dependencies
        queue = [
            task_id for task_id in plan.tasks
            if in_degree[task_id] == 0
        ]
        
        result = []
        while queue:
            # Sort by priority
            queue.sort(key=lambda x: plan.tasks[x])
            task_id = queue.pop(0)
            result.append(task_id)
            
            for next_id in graph[task_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)
        
        return result
    
    async def execute_plan(
        self,
        plan: Optional[ExecutionPlan] = None,
        on_task_start: Optional[Callable] = None,
        on_task_complete: Optional[Callable] = None,
        on_task_fail: Optional[Callable] = None,
    ) -> ExecutionPlan:
        """
        Planı çalıştır.
        
        Args:
            plan: Çalıştırılacak plan (None = current)
            on_task_start: Task başladığında callback
            on_task_complete: Task tamamlandığında callback
            on_task_fail: Task başarısız olduğunda callback
            
        Returns:
            Güncellenmiş plan
        """
        plan = plan or self._current_plan
        if not plan:
            raise ValueError("No plan to execute")
        
        import time
        
        plan.status = TaskStatus.IN_PROGRESS
        plan.started_at = datetime.now()
        
        # Execute in order
        for task_id in plan.execution_order:
            task = plan.tasks.get(task_id)
            if not task:
                continue
            
            # Wait for dependencies
            while not task.is_ready(plan.completed_task_ids):
                await asyncio.sleep(0.1)
            
            # Start task
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            plan.current_task_id = task_id
            
            if on_task_start:
                on_task_start(task)
            
            if self.verbose:
                logger.info(f"Executing: {task}")
            
            # Execute
            try:
                result = await self._execute_task(task)
                plan.mark_completed(task_id, result)
                
                if on_task_complete:
                    on_task_complete(task)
                    
            except Exception as e:
                task.retry_count += 1
                
                if task.retry_count < task.max_retries:
                    # Retry
                    task.status = TaskStatus.PENDING
                    plan.execution_order.append(task_id)
                    logger.warning(f"Task failed, will retry: {task.name}")
                else:
                    plan.mark_failed(task_id, str(e))
                    
                    if on_task_fail:
                        on_task_fail(task)
                    
                    logger.error(f"Task failed permanently: {task.name} - {e}")
        
        # Finalize
        plan.completed_at = datetime.now()
        plan.actual_total_duration_minutes = (
            plan.completed_at - plan.started_at
        ).total_seconds() / 60
        
        if plan.failed_tasks == 0:
            plan.status = TaskStatus.COMPLETED
        else:
            plan.status = TaskStatus.FAILED
        
        return plan
    
    async def _execute_task(self, task: TaskNode) -> Any:
        """Tek bir görevi çalıştır."""
        # Check for registered executor
        for tool in task.required_tools:
            if tool in self._executors:
                return await self._executors[tool](task)
        
        # Default: Use LLM to execute
        prompt = f"""Aşağıdaki görevi gerçekleştir:

GÖREV: {task.name}
AÇIKLAMA: {task.description}

Görevi tamamla ve sonucu açıkla."""

        result = llm_manager.generate(prompt=prompt, temperature=0.5)
        return result
    
    def execute_plan_sync(
        self,
        plan: Optional[ExecutionPlan] = None,
    ) -> ExecutionPlan:
        """Senkron plan çalıştırma."""
        return asyncio.run(self.execute_plan(plan))
    
    def replan(
        self,
        plan: ExecutionPlan,
        reason: str,
        failed_task_id: Optional[str] = None,
    ) -> ExecutionPlan:
        """
        Planı yeniden oluştur.
        
        Args:
            plan: Mevcut plan
            reason: Yeniden planlama nedeni
            failed_task_id: Başarısız olan görev ID
            
        Returns:
            Yeni plan
        """
        if self.verbose:
            logger.info(f"Replanning due to: {reason}")
        
        # Get remaining tasks
        remaining_goals = []
        for task_id, task in plan.tasks.items():
            if task.status == TaskStatus.PENDING:
                remaining_goals.append(task.description)
        
        if not remaining_goals:
            return plan
        
        # Create new plan for remaining tasks
        combined_goal = f"Kalan görevler: {'; '.join(remaining_goals)}"
        
        new_plan = self.create_plan(
            combined_goal,
            context={"original_plan_id": plan.id, "replan_reason": reason},
        )
        
        # Copy completed tasks
        new_plan.completed_task_ids = plan.completed_task_ids.copy()
        new_plan.completed_tasks = plan.completed_tasks
        
        return new_plan
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Plan al."""
        return self._plans.get(plan_id)
    
    def get_current_plan(self) -> Optional[ExecutionPlan]:
        """Mevcut planı döndür."""
        return self._current_plan
    
    def get_all_plans(self) -> List[ExecutionPlan]:
        """Tüm planları döndür."""
        return list(self._plans.values())


# ============================================================================
# SINGLETON & FACTORY
# ============================================================================

def create_planning_agent(
    name: str = "PlanningAgent",
    strategy: PlanningStrategy = PlanningStrategy.PLAN_AND_EXECUTE,
    enable_tot: bool = True,
    **kwargs,
) -> PlanningAgent:
    """Planning Agent factory."""
    return PlanningAgent(
        name=name,
        default_strategy=strategy,
        enable_tot=enable_tot,
        **kwargs,
    )


# Default instance
planning_agent = create_planning_agent(verbose=True)
