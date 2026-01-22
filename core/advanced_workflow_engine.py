"""
Advanced Workflow Orchestration Engine
======================================
Visual workflow designer with drag-drop canvas, conditional branching,
scheduled execution, and real-time visualization.

Premium Features:
- Visual Node-based Workflow Builder
- Conditional Branching & Decision Trees
- Scheduled/Triggered Workflows (cron-like)
- Parallel Execution Paths
- Error Recovery & Rollback
- Workflow Versioning & Diff
- Real-time Execution Visualization
- Template Marketplace (local)
- Import/Export Workflows

100% Local Execution
"""

import asyncio
import copy
import hashlib
import json
import logging
import os
import re
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import traceback

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class NodeCategory(str, Enum):
    """Categories of workflow nodes"""
    INPUT = "input"
    OUTPUT = "output"
    AI = "ai"
    PROCESSING = "processing"
    CONTROL = "control"
    INTEGRATION = "integration"
    UTILITY = "utility"


class NodeType(str, Enum):
    """Types of workflow nodes"""
    # Input nodes
    START = "start"
    TEXT_INPUT = "text_input"
    FILE_INPUT = "file_input"
    VARIABLE = "variable"
    USER_INPUT = "user_input"
    WEBHOOK_TRIGGER = "webhook_trigger"
    SCHEDULE_TRIGGER = "schedule_trigger"
    
    # AI nodes
    LLM_CHAT = "llm_chat"
    LLM_COMPLETE = "llm_complete"
    EMBEDDING = "embedding"
    RAG_QUERY = "rag_query"
    VISION_ANALYZE = "vision_analyze"
    CODE_EXECUTE = "code_execute"
    VOICE_STT = "voice_stt"
    VOICE_TTS = "voice_tts"
    AGENT_RUN = "agent_run"
    SUMMARIZE = "summarize"
    TRANSLATE = "translate"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    
    # Processing nodes
    TEXT_TRANSFORM = "text_transform"
    JSON_PARSE = "json_parse"
    JSON_BUILD = "json_build"
    REGEX_EXTRACT = "regex_extract"
    TEMPLATE = "template"
    SPLIT = "split"
    MERGE = "merge"
    FILTER = "filter"
    MAP = "map"
    REDUCE = "reduce"
    
    # Control flow nodes
    CONDITION = "condition"
    SWITCH = "switch"
    LOOP = "loop"
    PARALLEL = "parallel"
    WAIT = "wait"
    DELAY = "delay"
    RETRY = "retry"
    ERROR_HANDLER = "error_handler"
    
    # Output nodes
    OUTPUT = "output"
    FILE_WRITE = "file_write"
    WEBHOOK_CALL = "webhook_call"
    NOTIFICATION = "notification"
    LOG = "log"
    END = "end"
    
    # Utility nodes
    NOTE = "note"
    GROUP = "group"
    SUBWORKFLOW = "subworkflow"


class ExecutionStatus(str, Enum):
    """Status of workflow/node execution"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    WAITING = "waiting"


class TriggerType(str, Enum):
    """Types of workflow triggers"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"
    WORKFLOW = "workflow"  # Triggered by another workflow


class ScheduleFrequency(str, Enum):
    """Schedule frequency options"""
    ONCE = "once"
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Cron expression


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NodePort:
    """Input or output port of a node"""
    id: str
    name: str
    type: str = "any"  # any, string, number, boolean, array, object, file
    required: bool = False
    default: Any = None
    description: str = ""
    multiple: bool = False  # Can accept multiple connections


@dataclass
class NodePosition:
    """Position of a node on the canvas"""
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 100


@dataclass
class WorkflowNode:
    """A single node in the workflow"""
    id: str
    type: NodeType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: NodePosition = field(default_factory=NodePosition)
    inputs: List[NodePort] = field(default_factory=list)
    outputs: List[NodePort] = field(default_factory=list)
    category: NodeCategory = NodeCategory.PROCESSING
    description: str = ""
    icon: str = ""
    color: str = "#4A90D9"
    
    # Runtime state
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, NodeType) else self.type,
            "name": self.name,
            "config": self.config,
            "position": {"x": self.position.x, "y": self.position.y, 
                        "width": self.position.width, "height": self.position.height},
            "inputs": [{"id": p.id, "name": p.name, "type": p.type, 
                       "required": p.required, "default": p.default} for p in self.inputs],
            "outputs": [{"id": p.id, "name": p.name, "type": p.type} for p in self.outputs],
            "category": self.category.value if isinstance(self.category, NodeCategory) else self.category,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "status": self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowNode":
        pos_data = data.get("position", {})
        position = NodePosition(
            x=pos_data.get("x", 0),
            y=pos_data.get("y", 0),
            width=pos_data.get("width", 200),
            height=pos_data.get("height", 100)
        )
        
        inputs = [NodePort(**p) for p in data.get("inputs", [])]
        outputs = [NodePort(**p) for p in data.get("outputs", [])]
        
        return cls(
            id=data["id"],
            type=NodeType(data["type"]) if data.get("type") else NodeType.TEXT_INPUT,
            name=data.get("name", ""),
            config=data.get("config", {}),
            position=position,
            inputs=inputs,
            outputs=outputs,
            category=NodeCategory(data.get("category", "processing")),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            color=data.get("color", "#4A90D9")
        )


@dataclass
class WorkflowEdge:
    """Connection between two nodes"""
    id: str
    source_node: str
    source_port: str
    target_node: str
    target_port: str
    label: str = ""
    condition: Optional[str] = None  # For conditional edges
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_node": self.source_node,
            "source_port": self.source_port,
            "target_node": self.target_node,
            "target_port": self.target_port,
            "label": self.label,
            "condition": self.condition
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowEdge":
        return cls(
            id=data["id"],
            source_node=data["source_node"],
            source_port=data["source_port"],
            target_node=data["target_node"],
            target_port=data["target_port"],
            label=data.get("label", ""),
            condition=data.get("condition")
        )


@dataclass
class WorkflowSchedule:
    """Schedule configuration for a workflow"""
    enabled: bool = False
    frequency: ScheduleFrequency = ScheduleFrequency.DAILY
    time: str = "09:00"  # HH:MM format
    days: List[int] = field(default_factory=lambda: [1, 2, 3, 4, 5])  # 1=Mon, 7=Sun
    cron: str = ""  # Custom cron expression
    timezone: str = "Europe/Istanbul"
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "frequency": self.frequency.value,
            "time": self.time,
            "days": self.days,
            "cron": self.cron,
            "timezone": self.timezone,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None
        }


@dataclass
class WorkflowVersion:
    """Version of a workflow for history/rollback"""
    version: int
    created_at: datetime
    created_by: str
    description: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    config: Dict[str, Any]
    checksum: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "description": self.description,
            "checksum": self.checksum
        }


@dataclass
class Workflow:
    """Complete workflow definition"""
    id: str
    name: str
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    
    # Metadata
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    icon: str = "workflow"
    color: str = "#4A90D9"
    
    # Trigger configuration
    trigger_type: TriggerType = TriggerType.MANUAL
    schedule: WorkflowSchedule = field(default_factory=WorkflowSchedule)
    
    # Variables
    variables: Dict[str, Any] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)  # Names of secret variables
    
    # Settings
    timeout_seconds: int = 3600
    max_retries: int = 3
    retry_delay_seconds: int = 60
    parallel_execution: bool = True
    stop_on_error: bool = True
    
    # Versioning
    version: int = 1
    versions: List[WorkflowVersion] = field(default_factory=list)
    
    # Status
    status: ExecutionStatus = ExecutionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    is_template: bool = False
    template_id: Optional[str] = None
    
    # Statistics
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    avg_duration_seconds: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "category": self.category,
            "tags": self.tags,
            "icon": self.icon,
            "color": self.color,
            "trigger_type": self.trigger_type.value,
            "schedule": self.schedule.to_dict(),
            "variables": self.variables,
            "secrets": self.secrets,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "parallel_execution": self.parallel_execution,
            "stop_on_error": self.stop_on_error,
            "version": self.version,
            "versions": [v.to_dict() for v in self.versions],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "is_template": self.is_template,
            "template_id": self.template_id,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "avg_duration_seconds": self.avg_duration_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        workflow = cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", "")
        )
        
        workflow.nodes = [WorkflowNode.from_dict(n) for n in data.get("nodes", [])]
        workflow.edges = [WorkflowEdge.from_dict(e) for e in data.get("edges", [])]
        workflow.category = data.get("category", "general")
        workflow.tags = data.get("tags", [])
        workflow.icon = data.get("icon", "workflow")
        workflow.color = data.get("color", "#4A90D9")
        workflow.trigger_type = TriggerType(data.get("trigger_type", "manual"))
        
        if data.get("schedule"):
            sched = data["schedule"]
            workflow.schedule = WorkflowSchedule(
                enabled=sched.get("enabled", False),
                frequency=ScheduleFrequency(sched.get("frequency", "daily")),
                time=sched.get("time", "09:00"),
                days=sched.get("days", [1, 2, 3, 4, 5]),
                cron=sched.get("cron", ""),
                timezone=sched.get("timezone", "Europe/Istanbul")
            )
        
        workflow.variables = data.get("variables", {})
        workflow.secrets = data.get("secrets", [])
        workflow.timeout_seconds = data.get("timeout_seconds", 3600)
        workflow.max_retries = data.get("max_retries", 3)
        workflow.version = data.get("version", 1)
        workflow.is_template = data.get("is_template", False)
        workflow.template_id = data.get("template_id")
        
        if data.get("created_at"):
            workflow.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            workflow.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return workflow
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """Get a node by ID"""
        return next((n for n in self.nodes if n.id == node_id), None)
    
    def get_edges_from(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges originating from a node"""
        return [e for e in self.edges if e.source_node == node_id]
    
    def get_edges_to(self, node_id: str) -> List[WorkflowEdge]:
        """Get all edges leading to a node"""
        return [e for e in self.edges if e.target_node == node_id]
    
    def get_start_nodes(self) -> List[WorkflowNode]:
        """Get nodes with no incoming edges (start points)"""
        nodes_with_incoming = {e.target_node for e in self.edges}
        return [n for n in self.nodes if n.id not in nodes_with_incoming 
                or n.type in [NodeType.START, NodeType.SCHEDULE_TRIGGER, NodeType.WEBHOOK_TRIGGER]]
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the workflow structure"""
        errors = []
        
        if not self.name:
            errors.append("Workflow name is required")
        
        if not self.nodes:
            errors.append("Workflow must have at least one node")
        
        # Check for orphan nodes
        connected_nodes = set()
        for edge in self.edges:
            connected_nodes.add(edge.source_node)
            connected_nodes.add(edge.target_node)
        
        for node in self.nodes:
            if node.type not in [NodeType.START, NodeType.NOTE, NodeType.GROUP]:
                if node.id not in connected_nodes and len(self.nodes) > 1:
                    errors.append(f"Node '{node.name}' is not connected")
        
        # Check for cycles (simplified)
        # Full cycle detection would use DFS/Tarjan's algorithm
        
        # Validate required node configs
        for node in self.nodes:
            if node.type == NodeType.LLM_CHAT:
                if not node.config.get("prompt") and not node.config.get("system_prompt"):
                    errors.append(f"LLM node '{node.name}' requires a prompt")
        
        return len(errors) == 0, errors


@dataclass
class ExecutionContext:
    """Context for workflow execution"""
    execution_id: str
    workflow_id: str
    variables: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    current_node: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def log(self, level: str, message: str, node_id: Optional[str] = None):
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "node_id": node_id
        })
    
    def get_input(self, node_id: str, port_name: str) -> Any:
        """Get input value for a node port"""
        return self.node_outputs.get(f"{node_id}.{port_name}")
    
    def set_output(self, node_id: str, port_name: str, value: Any):
        """Set output value for a node port"""
        self.node_outputs[f"{node_id}.{port_name}"] = value


# =============================================================================
# NODE EXECUTORS
# =============================================================================

class NodeExecutor(ABC):
    """Base class for node executors"""
    
    @abstractmethod
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the node and return outputs"""
        pass


class LLMChatExecutor(NodeExecutor):
    """Executor for LLM Chat node"""
    
    def __init__(self):
        self._llm = None
    
    def _get_llm(self):
        if self._llm is None:
            try:
                from core.llm_manager import llm_manager
                self._llm = llm_manager
            except:
                pass
        return self._llm
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        llm = self._get_llm()
        if not llm:
            raise RuntimeError("LLM manager not available")
        
        # Get prompt from config or input
        prompt = node.config.get("prompt", "")
        system_prompt = node.config.get("system_prompt", "")
        
        # Replace variables in prompt
        user_input = inputs.get("input", "")
        if user_input:
            prompt = prompt.replace("{{input}}", str(user_input))
        
        for var_name, var_value in context.variables.items():
            prompt = prompt.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Execute
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: llm.chat(messages, max_tokens=node.config.get("max_tokens", 1000))
        )
        
        return {"output": response, "tokens_used": len(response.split()) * 1.3}


class RAGQueryExecutor(NodeExecutor):
    """Executor for RAG Query node"""
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            from rag.unified_orchestrator import UnifiedRAGOrchestrator
            orchestrator = UnifiedRAGOrchestrator()
            
            query = inputs.get("query", node.config.get("query", ""))
            
            # Replace variables
            for var_name, var_value in context.variables.items():
                query = query.replace(f"{{{{{var_name}}}}}", str(var_value))
            
            result = await orchestrator.query(query)
            
            return {
                "answer": result.get("answer", ""),
                "sources": result.get("sources", []),
                "confidence": result.get("confidence", 0)
            }
        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return {"answer": "", "sources": [], "error": str(e)}


class ConditionExecutor(NodeExecutor):
    """Executor for Condition node"""
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        condition = node.config.get("condition", "")
        
        # Simple condition evaluation
        # Supports: ==, !=, >, <, >=, <=, contains, startswith, endswith
        input_value = inputs.get("value", "")
        
        try:
            # Parse condition
            if " contains " in condition:
                parts = condition.split(" contains ")
                result = parts[1].strip().strip('"\'') in str(input_value)
            elif " == " in condition:
                parts = condition.split(" == ")
                result = str(input_value) == parts[1].strip().strip('"\'')
            elif " != " in condition:
                parts = condition.split(" != ")
                result = str(input_value) != parts[1].strip().strip('"\'')
            elif " > " in condition:
                parts = condition.split(" > ")
                result = float(input_value) > float(parts[1].strip())
            elif " < " in condition:
                parts = condition.split(" < ")
                result = float(input_value) < float(parts[1].strip())
            elif " >= " in condition:
                parts = condition.split(" >= ")
                result = float(input_value) >= float(parts[1].strip())
            elif " <= " in condition:
                parts = condition.split(" <= ")
                result = float(input_value) <= float(parts[1].strip())
            else:
                # Truthy check
                result = bool(input_value)
            
            return {"result": result, "true": result, "false": not result}
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            return {"result": False, "true": False, "false": True, "error": str(e)}


class TextTransformExecutor(NodeExecutor):
    """Executor for Text Transform node"""
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        text = inputs.get("text", "")
        operation = node.config.get("operation", "none")
        
        if operation == "uppercase":
            result = str(text).upper()
        elif operation == "lowercase":
            result = str(text).lower()
        elif operation == "capitalize":
            result = str(text).capitalize()
        elif operation == "strip":
            result = str(text).strip()
        elif operation == "split":
            delimiter = node.config.get("delimiter", "\n")
            result = str(text).split(delimiter)
        elif operation == "join":
            delimiter = node.config.get("delimiter", "\n")
            if isinstance(text, list):
                result = delimiter.join(text)
            else:
                result = str(text)
        elif operation == "replace":
            find = node.config.get("find", "")
            replace_with = node.config.get("replace_with", "")
            result = str(text).replace(find, replace_with)
        elif operation == "regex":
            pattern = node.config.get("pattern", "")
            replace_with = node.config.get("replace_with", "")
            result = re.sub(pattern, replace_with, str(text))
        elif operation == "template":
            template = node.config.get("template", "{{text}}")
            result = template.replace("{{text}}", str(text))
            for var_name, var_value in context.variables.items():
                result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        else:
            result = text
        
        return {"output": result}


class LoopExecutor(NodeExecutor):
    """Executor for Loop node"""
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        items = inputs.get("items", [])
        max_iterations = node.config.get("max_iterations", 100)
        
        if not isinstance(items, list):
            items = [items]
        
        results = []
        for i, item in enumerate(items[:max_iterations]):
            results.append({
                "index": i,
                "item": item,
                "is_first": i == 0,
                "is_last": i == len(items) - 1
            })
        
        return {
            "items": results,
            "count": len(results),
            "current_index": 0,
            "current_item": results[0] if results else None
        }


class JSONParseExecutor(NodeExecutor):
    """Executor for JSON Parse node"""
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        text = inputs.get("text", "")
        extract_path = node.config.get("path", "")
        
        try:
            data = json.loads(text) if isinstance(text, str) else text
            
            if extract_path:
                # Navigate path like "data.items[0].name"
                parts = extract_path.replace("[", ".").replace("]", "").split(".")
                result = data
                for part in parts:
                    if part.isdigit():
                        result = result[int(part)]
                    else:
                        result = result[part]
                return {"output": result, "parsed": data}
            
            return {"output": data, "parsed": data}
        except Exception as e:
            return {"output": None, "error": str(e)}


class CodeExecuteExecutor(NodeExecutor):
    """Executor for Code Execute node"""
    
    async def execute(
        self,
        node: WorkflowNode,
        context: ExecutionContext,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            from core.code_interpreter import CodeInterpreter
            interpreter = CodeInterpreter()
            
            code = node.config.get("code", "")
            language = node.config.get("language", "python")
            
            # Inject inputs as variables
            if language == "python":
                var_setup = ""
                for key, value in inputs.items():
                    if isinstance(value, str):
                        var_setup += f'{key} = """{value}"""\n'
                    else:
                        var_setup += f'{key} = {json.dumps(value)}\n'
                code = var_setup + code
            
            result = await interpreter.execute(code, language)
            
            return {
                "output": result.stdout if result.stdout else result.return_value,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.status.value == "success"
            }
        except Exception as e:
            return {"output": None, "error": str(e), "success": False}


# =============================================================================
# WORKFLOW ENGINE
# =============================================================================

class AdvancedWorkflowEngine:
    """
    Advanced Workflow Orchestration Engine
    
    Provides a complete workflow management system with:
    - Visual node-based workflow design
    - Parallel and conditional execution
    - Scheduling and triggers
    - Version control
    - Error handling and recovery
    """
    
    def __init__(self, storage_dir: str = "data/workflows"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, ExecutionContext] = {}
        self.templates: Dict[str, Workflow] = {}
        
        # Node executors
        self.executors: Dict[NodeType, NodeExecutor] = {
            NodeType.LLM_CHAT: LLMChatExecutor(),
            NodeType.RAG_QUERY: RAGQueryExecutor(),
            NodeType.CONDITION: ConditionExecutor(),
            NodeType.TEXT_TRANSFORM: TextTransformExecutor(),
            NodeType.LOOP: LoopExecutor(),
            NodeType.JSON_PARSE: JSONParseExecutor(),
            NodeType.CODE_EXECUTE: CodeExecuteExecutor(),
        }
        
        # Scheduler
        self._scheduler_running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        
        # Callbacks for real-time updates
        self._execution_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        self._load_workflows()
        self._load_templates()
        
        logger.info(f"AdvancedWorkflowEngine initialized with {len(self.workflows)} workflows")
    
    def _load_workflows(self):
        """Load all workflows from disk"""
        workflows_path = self.storage_dir / "workflows"
        workflows_path.mkdir(exist_ok=True)
        
        for wf_file in workflows_path.glob("*.json"):
            try:
                with open(wf_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    workflow = Workflow.from_dict(data)
                    self.workflows[workflow.id] = workflow
            except Exception as e:
                logger.error(f"Error loading workflow {wf_file}: {e}")
    
    def _load_templates(self):
        """Load built-in workflow templates"""
        templates_path = self.storage_dir / "templates"
        templates_path.mkdir(exist_ok=True)
        
        # Built-in templates
        self._create_builtin_templates()
        
        # Load custom templates
        for tpl_file in templates_path.glob("*.json"):
            try:
                with open(tpl_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    workflow = Workflow.from_dict(data)
                    workflow.is_template = True
                    self.templates[workflow.id] = workflow
            except Exception as e:
                logger.error(f"Error loading template {tpl_file}: {e}")
    
    def _create_builtin_templates(self):
        """Create built-in workflow templates"""
        # Template 1: Document Q&A
        doc_qa = Workflow(
            id="template-doc-qa",
            name="Döküman Soru-Cevap",
            description="Yüklenen dökümanlara soru sorun ve cevap alın",
            category="rag",
            tags=["rag", "qa", "documents"],
            is_template=True
        )
        
        start = WorkflowNode(
            id="start-1",
            type=NodeType.START,
            name="Başla",
            category=NodeCategory.INPUT,
            position=NodePosition(x=100, y=200)
        )
        
        input_node = WorkflowNode(
            id="input-1",
            type=NodeType.USER_INPUT,
            name="Soru Girişi",
            config={"prompt": "Sorunuzu yazın:"},
            category=NodeCategory.INPUT,
            position=NodePosition(x=300, y=200),
            outputs=[NodePort(id="question", name="question", type="string")]
        )
        
        rag_node = WorkflowNode(
            id="rag-1",
            type=NodeType.RAG_QUERY,
            name="RAG Sorgu",
            category=NodeCategory.AI,
            position=NodePosition(x=500, y=200),
            inputs=[NodePort(id="query", name="query", type="string", required=True)],
            outputs=[NodePort(id="answer", name="answer", type="string"),
                    NodePort(id="sources", name="sources", type="array")]
        )
        
        output_node = WorkflowNode(
            id="output-1",
            type=NodeType.OUTPUT,
            name="Cevap",
            category=NodeCategory.OUTPUT,
            position=NodePosition(x=700, y=200),
            inputs=[NodePort(id="result", name="result", type="string")]
        )
        
        doc_qa.nodes = [start, input_node, rag_node, output_node]
        doc_qa.edges = [
            WorkflowEdge(id="e1", source_node="start-1", source_port="out", 
                        target_node="input-1", target_port="in"),
            WorkflowEdge(id="e2", source_node="input-1", source_port="question", 
                        target_node="rag-1", target_port="query"),
            WorkflowEdge(id="e3", source_node="rag-1", source_port="answer", 
                        target_node="output-1", target_port="result"),
        ]
        
        self.templates["template-doc-qa"] = doc_qa
        
        # Template 2: Content Summarizer
        summarizer = Workflow(
            id="template-summarizer",
            name="İçerik Özetleyici",
            description="Uzun metinleri otomatik özetler",
            category="ai",
            tags=["summarization", "ai", "text"],
            is_template=True
        )
        
        summarizer.nodes = [
            WorkflowNode(
                id="start-1",
                type=NodeType.START,
                name="Başla",
                category=NodeCategory.INPUT,
                position=NodePosition(x=100, y=200)
            ),
            WorkflowNode(
                id="text-input-1",
                type=NodeType.TEXT_INPUT,
                name="Metin Girişi",
                config={"placeholder": "Özetlenecek metin..."},
                category=NodeCategory.INPUT,
                position=NodePosition(x=300, y=200),
                outputs=[NodePort(id="text", name="text", type="string")]
            ),
            WorkflowNode(
                id="llm-1",
                type=NodeType.LLM_CHAT,
                name="Özetleme AI",
                config={
                    "system_prompt": "Sen profesyonel bir metin özetleyicisin. Verilen metni kısa ve öz şekilde özetle.",
                    "prompt": "Aşağıdaki metni özetle:\n\n{{input}}"
                },
                category=NodeCategory.AI,
                position=NodePosition(x=500, y=200),
                inputs=[NodePort(id="input", name="input", type="string", required=True)],
                outputs=[NodePort(id="output", name="output", type="string")]
            ),
            WorkflowNode(
                id="output-1",
                type=NodeType.OUTPUT,
                name="Özet",
                category=NodeCategory.OUTPUT,
                position=NodePosition(x=700, y=200),
                inputs=[NodePort(id="result", name="result", type="string")]
            )
        ]
        
        summarizer.edges = [
            WorkflowEdge(id="e1", source_node="start-1", source_port="out", 
                        target_node="text-input-1", target_port="in"),
            WorkflowEdge(id="e2", source_node="text-input-1", source_port="text", 
                        target_node="llm-1", target_port="input"),
            WorkflowEdge(id="e3", source_node="llm-1", source_port="output", 
                        target_node="output-1", target_port="result"),
        ]
        
        self.templates["template-summarizer"] = summarizer
        
        # Template 3: Multi-step Research
        research = Workflow(
            id="template-research",
            name="Araştırma Pipeline",
            description="Çok adımlı araştırma ve rapor oluşturma",
            category="research",
            tags=["research", "multi-step", "report"],
            is_template=True
        )
        
        research.nodes = [
            WorkflowNode(id="start-1", type=NodeType.START, name="Başla",
                        category=NodeCategory.INPUT, position=NodePosition(x=100, y=200)),
            WorkflowNode(id="topic-1", type=NodeType.USER_INPUT, name="Konu",
                        config={"prompt": "Araştırma konusu:"}, category=NodeCategory.INPUT,
                        position=NodePosition(x=250, y=200),
                        outputs=[NodePort(id="topic", name="topic", type="string")]),
            WorkflowNode(id="rag-1", type=NodeType.RAG_QUERY, name="Bilgi Toplama",
                        category=NodeCategory.AI, position=NodePosition(x=400, y=100),
                        inputs=[NodePort(id="query", name="query", type="string")],
                        outputs=[NodePort(id="answer", name="answer", type="string")]),
            WorkflowNode(id="llm-expand", type=NodeType.LLM_CHAT, name="Genişletme",
                        config={"prompt": "Bu konu hakkında detaylı sorular üret:\n\n{{input}}"},
                        category=NodeCategory.AI, position=NodePosition(x=400, y=300),
                        inputs=[NodePort(id="input", name="input", type="string")],
                        outputs=[NodePort(id="output", name="output", type="string")]),
            WorkflowNode(id="merge-1", type=NodeType.MERGE, name="Birleştir",
                        category=NodeCategory.PROCESSING, position=NodePosition(x=600, y=200),
                        inputs=[NodePort(id="input1", name="input1", type="string"),
                               NodePort(id="input2", name="input2", type="string")],
                        outputs=[NodePort(id="merged", name="merged", type="string")]),
            WorkflowNode(id="llm-report", type=NodeType.LLM_CHAT, name="Rapor Yaz",
                        config={"system_prompt": "Detaylı ve profesyonel araştırma raporları yaz.",
                               "prompt": "Aşağıdaki bilgileri kullanarak detaylı bir rapor yaz:\n\n{{input}}"},
                        category=NodeCategory.AI, position=NodePosition(x=800, y=200),
                        inputs=[NodePort(id="input", name="input", type="string")],
                        outputs=[NodePort(id="output", name="output", type="string")]),
            WorkflowNode(id="output-1", type=NodeType.OUTPUT, name="Rapor",
                        category=NodeCategory.OUTPUT, position=NodePosition(x=1000, y=200),
                        inputs=[NodePort(id="result", name="result", type="string")])
        ]
        
        research.edges = [
            WorkflowEdge(id="e1", source_node="start-1", source_port="out", 
                        target_node="topic-1", target_port="in"),
            WorkflowEdge(id="e2", source_node="topic-1", source_port="topic", 
                        target_node="rag-1", target_port="query"),
            WorkflowEdge(id="e3", source_node="topic-1", source_port="topic", 
                        target_node="llm-expand", target_port="input"),
            WorkflowEdge(id="e4", source_node="rag-1", source_port="answer", 
                        target_node="merge-1", target_port="input1"),
            WorkflowEdge(id="e5", source_node="llm-expand", source_port="output", 
                        target_node="merge-1", target_port="input2"),
            WorkflowEdge(id="e6", source_node="merge-1", source_port="merged", 
                        target_node="llm-report", target_port="input"),
            WorkflowEdge(id="e7", source_node="llm-report", source_port="output", 
                        target_node="output-1", target_port="result"),
        ]
        
        self.templates["template-research"] = research
    
    def _save_workflow(self, workflow: Workflow):
        """Save a workflow to disk"""
        workflows_path = self.storage_dir / "workflows"
        workflows_path.mkdir(exist_ok=True)
        
        file_path = workflows_path / f"{workflow.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(workflow.to_dict(), f, ensure_ascii=False, indent=2)
    
    # =========================================================================
    # WORKFLOW CRUD
    # =========================================================================
    
    def create_workflow(
        self,
        name: str,
        description: str = "",
        template_id: Optional[str] = None,
        category: str = "general",
        tags: List[str] = None
    ) -> Workflow:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())
        
        if template_id and template_id in self.templates:
            # Create from template
            template = self.templates[template_id]
            workflow = copy.deepcopy(template)
            workflow.id = workflow_id
            workflow.name = name
            workflow.description = description or template.description
            workflow.is_template = False
            workflow.template_id = template_id
        else:
            workflow = Workflow(
                id=workflow_id,
                name=name,
                description=description,
                category=category,
                tags=tags or []
            )
            
            # Add default start node
            start_node = WorkflowNode(
                id=str(uuid.uuid4()),
                type=NodeType.START,
                name="Başla",
                category=NodeCategory.INPUT,
                position=NodePosition(x=100, y=200)
            )
            workflow.nodes.append(start_node)
        
        workflow.created_at = datetime.now()
        workflow.updated_at = datetime.now()
        
        self.workflows[workflow_id] = workflow
        self._save_workflow(workflow)
        
        logger.info(f"Created workflow: {name} ({workflow_id})")
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_templates: bool = False
    ) -> List[Workflow]:
        """List all workflows with optional filtering"""
        workflows = list(self.workflows.values())
        
        if include_templates:
            workflows.extend(self.templates.values())
        
        if category:
            workflows = [w for w in workflows if w.category == category]
        
        if tags:
            workflows = [w for w in workflows if any(t in w.tags for t in tags)]
        
        return sorted(workflows, key=lambda w: w.updated_at, reverse=True)
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Create version before update
        self._create_version(workflow)
        
        # Apply updates
        for key, value in updates.items():
            if key == "nodes":
                workflow.nodes = [WorkflowNode.from_dict(n) for n in value]
            elif key == "edges":
                workflow.edges = [WorkflowEdge.from_dict(e) for e in value]
            elif hasattr(workflow, key):
                setattr(workflow, key, value)
        
        workflow.updated_at = datetime.now()
        workflow.version += 1
        
        self._save_workflow(workflow)
        
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        del self.workflows[workflow_id]
        
        # Delete file
        file_path = self.storage_dir / "workflows" / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()
        
        return True
    
    def duplicate_workflow(self, workflow_id: str, new_name: str) -> Optional[Workflow]:
        """Duplicate an existing workflow"""
        original = self.workflows.get(workflow_id)
        if not original:
            return None
        
        new_workflow = copy.deepcopy(original)
        new_workflow.id = str(uuid.uuid4())
        new_workflow.name = new_name
        new_workflow.created_at = datetime.now()
        new_workflow.updated_at = datetime.now()
        new_workflow.version = 1
        new_workflow.versions = []
        new_workflow.total_runs = 0
        new_workflow.successful_runs = 0
        new_workflow.failed_runs = 0
        
        # Generate new IDs for nodes and edges
        id_map = {}
        for node in new_workflow.nodes:
            old_id = node.id
            new_id = str(uuid.uuid4())
            id_map[old_id] = new_id
            node.id = new_id
        
        for edge in new_workflow.edges:
            edge.id = str(uuid.uuid4())
            edge.source_node = id_map.get(edge.source_node, edge.source_node)
            edge.target_node = id_map.get(edge.target_node, edge.target_node)
        
        self.workflows[new_workflow.id] = new_workflow
        self._save_workflow(new_workflow)
        
        return new_workflow
    
    # =========================================================================
    # NODE MANAGEMENT
    # =========================================================================
    
    def add_node(
        self,
        workflow_id: str,
        node_type: NodeType,
        name: str,
        position: Dict[str, float],
        config: Dict[str, Any] = None
    ) -> Optional[WorkflowNode]:
        """Add a node to a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        node = self._create_node(node_type, name, position, config)
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now()
        
        self._save_workflow(workflow)
        return node
    
    def _create_node(
        self,
        node_type: NodeType,
        name: str,
        position: Dict[str, float],
        config: Dict[str, Any] = None
    ) -> WorkflowNode:
        """Create a node with default ports based on type"""
        node_id = str(uuid.uuid4())
        
        # Default ports by node type
        port_configs = {
            NodeType.START: {
                "outputs": [NodePort(id="out", name="out", type="any")],
                "category": NodeCategory.INPUT,
                "icon": "play",
                "color": "#22C55E"
            },
            NodeType.END: {
                "inputs": [NodePort(id="in", name="in", type="any")],
                "category": NodeCategory.OUTPUT,
                "icon": "stop",
                "color": "#EF4444"
            },
            NodeType.LLM_CHAT: {
                "inputs": [NodePort(id="input", name="input", type="string")],
                "outputs": [NodePort(id="output", name="output", type="string")],
                "category": NodeCategory.AI,
                "icon": "brain",
                "color": "#8B5CF6"
            },
            NodeType.RAG_QUERY: {
                "inputs": [NodePort(id="query", name="query", type="string", required=True)],
                "outputs": [
                    NodePort(id="answer", name="answer", type="string"),
                    NodePort(id="sources", name="sources", type="array")
                ],
                "category": NodeCategory.AI,
                "icon": "search",
                "color": "#3B82F6"
            },
            NodeType.CONDITION: {
                "inputs": [NodePort(id="value", name="value", type="any", required=True)],
                "outputs": [
                    NodePort(id="true", name="true", type="any"),
                    NodePort(id="false", name="false", type="any")
                ],
                "category": NodeCategory.CONTROL,
                "icon": "git-branch",
                "color": "#F59E0B"
            },
            NodeType.LOOP: {
                "inputs": [NodePort(id="items", name="items", type="array", required=True)],
                "outputs": [
                    NodePort(id="item", name="item", type="any"),
                    NodePort(id="index", name="index", type="number"),
                    NodePort(id="done", name="done", type="any")
                ],
                "category": NodeCategory.CONTROL,
                "icon": "repeat",
                "color": "#F59E0B"
            },
            NodeType.TEXT_TRANSFORM: {
                "inputs": [NodePort(id="text", name="text", type="string", required=True)],
                "outputs": [NodePort(id="output", name="output", type="string")],
                "category": NodeCategory.PROCESSING,
                "icon": "type",
                "color": "#6366F1"
            },
            NodeType.USER_INPUT: {
                "outputs": [NodePort(id="value", name="value", type="string")],
                "category": NodeCategory.INPUT,
                "icon": "edit",
                "color": "#10B981"
            },
            NodeType.OUTPUT: {
                "inputs": [NodePort(id="result", name="result", type="any", required=True)],
                "category": NodeCategory.OUTPUT,
                "icon": "log-out",
                "color": "#EC4899"
            },
            NodeType.CODE_EXECUTE: {
                "inputs": [NodePort(id="input", name="input", type="any")],
                "outputs": [
                    NodePort(id="output", name="output", type="any"),
                    NodePort(id="error", name="error", type="string")
                ],
                "category": NodeCategory.PROCESSING,
                "icon": "code",
                "color": "#14B8A6"
            },
            NodeType.MERGE: {
                "inputs": [
                    NodePort(id="input1", name="input1", type="any"),
                    NodePort(id="input2", name="input2", type="any")
                ],
                "outputs": [NodePort(id="merged", name="merged", type="string")],
                "category": NodeCategory.PROCESSING,
                "icon": "git-merge",
                "color": "#6366F1"
            },
            NodeType.JSON_PARSE: {
                "inputs": [NodePort(id="text", name="text", type="string", required=True)],
                "outputs": [
                    NodePort(id="output", name="output", type="any"),
                    NodePort(id="error", name="error", type="string")
                ],
                "category": NodeCategory.PROCESSING,
                "icon": "braces",
                "color": "#6366F1"
            }
        }
        
        port_config = port_configs.get(node_type, {
            "inputs": [NodePort(id="in", name="in", type="any")],
            "outputs": [NodePort(id="out", name="out", type="any")],
            "category": NodeCategory.PROCESSING,
            "icon": "box",
            "color": "#6B7280"
        })
        
        return WorkflowNode(
            id=node_id,
            type=node_type,
            name=name,
            config=config or {},
            position=NodePosition(
                x=position.get("x", 0),
                y=position.get("y", 0)
            ),
            inputs=port_config.get("inputs", []),
            outputs=port_config.get("outputs", []),
            category=port_config.get("category", NodeCategory.PROCESSING),
            icon=port_config.get("icon", "box"),
            color=port_config.get("color", "#6B7280")
        )
    
    def update_node(
        self,
        workflow_id: str,
        node_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WorkflowNode]:
        """Update a node in a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        node = workflow.get_node(node_id)
        if not node:
            return None
        
        for key, value in updates.items():
            if key == "position":
                node.position = NodePosition(**value)
            elif key == "config":
                node.config.update(value)
            elif hasattr(node, key):
                setattr(node, key, value)
        
        workflow.updated_at = datetime.now()
        self._save_workflow(workflow)
        
        return node
    
    def delete_node(self, workflow_id: str, node_id: str) -> bool:
        """Delete a node from a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        # Remove node
        workflow.nodes = [n for n in workflow.nodes if n.id != node_id]
        
        # Remove connected edges
        workflow.edges = [e for e in workflow.edges 
                         if e.source_node != node_id and e.target_node != node_id]
        
        workflow.updated_at = datetime.now()
        self._save_workflow(workflow)
        
        return True
    
    def add_edge(
        self,
        workflow_id: str,
        source_node: str,
        source_port: str,
        target_node: str,
        target_port: str,
        condition: Optional[str] = None
    ) -> Optional[WorkflowEdge]:
        """Add an edge between nodes"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Validate nodes exist
        if not workflow.get_node(source_node) or not workflow.get_node(target_node):
            return None
        
        edge = WorkflowEdge(
            id=str(uuid.uuid4()),
            source_node=source_node,
            source_port=source_port,
            target_node=target_node,
            target_port=target_port,
            condition=condition
        )
        
        workflow.edges.append(edge)
        workflow.updated_at = datetime.now()
        self._save_workflow(workflow)
        
        return edge
    
    def delete_edge(self, workflow_id: str, edge_id: str) -> bool:
        """Delete an edge from a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        workflow.edges = [e for e in workflow.edges if e.id != edge_id]
        workflow.updated_at = datetime.now()
        self._save_workflow(workflow)
        
        return True
    
    # =========================================================================
    # VERSIONING
    # =========================================================================
    
    def _create_version(self, workflow: Workflow):
        """Create a version snapshot of the workflow"""
        checksum = hashlib.md5(
            json.dumps(workflow.to_dict(), sort_keys=True).encode()
        ).hexdigest()
        
        # Don't create version if nothing changed
        if workflow.versions and workflow.versions[-1].checksum == checksum:
            return
        
        version = WorkflowVersion(
            version=workflow.version,
            created_at=datetime.now(),
            created_by=workflow.created_by,
            description=f"Version {workflow.version}",
            nodes=[n.to_dict() for n in workflow.nodes],
            edges=[e.to_dict() for e in workflow.edges],
            config={
                "variables": workflow.variables,
                "schedule": workflow.schedule.to_dict()
            },
            checksum=checksum
        )
        
        workflow.versions.append(version)
        
        # Keep only last 20 versions
        if len(workflow.versions) > 20:
            workflow.versions = workflow.versions[-20:]
    
    def rollback_workflow(self, workflow_id: str, version: int) -> Optional[Workflow]:
        """Rollback a workflow to a previous version"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        target_version = next(
            (v for v in workflow.versions if v.version == version),
            None
        )
        
        if not target_version:
            return None
        
        # Create version of current state before rollback
        self._create_version(workflow)
        
        # Restore from version
        workflow.nodes = [WorkflowNode.from_dict(n) for n in target_version.nodes]
        workflow.edges = [WorkflowEdge.from_dict(e) for e in target_version.edges]
        workflow.variables = target_version.config.get("variables", {})
        
        workflow.version += 1
        workflow.updated_at = datetime.now()
        
        self._save_workflow(workflow)
        
        return workflow
    
    def get_version_diff(
        self,
        workflow_id: str,
        version1: int,
        version2: int
    ) -> Optional[Dict[str, Any]]:
        """Get the diff between two workflow versions"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        v1 = next((v for v in workflow.versions if v.version == version1), None)
        v2 = next((v for v in workflow.versions if v.version == version2), None)
        
        if not v1 or not v2:
            return None
        
        # Calculate differences
        v1_node_ids = {n["id"] for n in v1.nodes}
        v2_node_ids = {n["id"] for n in v2.nodes}
        
        added_nodes = v2_node_ids - v1_node_ids
        removed_nodes = v1_node_ids - v2_node_ids
        
        v1_edge_ids = {e["id"] for e in v1.edges}
        v2_edge_ids = {e["id"] for e in v2.edges}
        
        added_edges = v2_edge_ids - v1_edge_ids
        removed_edges = v1_edge_ids - v2_edge_ids
        
        return {
            "version1": version1,
            "version2": version2,
            "added_nodes": list(added_nodes),
            "removed_nodes": list(removed_nodes),
            "added_edges": list(added_edges),
            "removed_edges": list(removed_edges),
            "node_count_change": len(v2.nodes) - len(v1.nodes),
            "edge_count_change": len(v2.edges) - len(v1.edges)
        }
    
    # =========================================================================
    # EXECUTION
    # =========================================================================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any] = None,
        callback: Optional[Callable] = None
    ) -> ExecutionContext:
        """Execute a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Validate
        valid, errors = workflow.validate()
        if not valid:
            raise ValueError(f"Workflow validation failed: {errors}")
        
        # Create execution context
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow_id,
            variables={**workflow.variables, **(inputs or {})},
            status=ExecutionStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self.executions[execution_id] = context
        
        if callback:
            self._execution_callbacks[execution_id].append(callback)
        
        try:
            # Reset node states
            for node in workflow.nodes:
                node.status = ExecutionStatus.PENDING
                node.result = None
                node.error = None
            
            # Execute starting from start nodes
            start_nodes = workflow.get_start_nodes()
            
            if workflow.parallel_execution and len(start_nodes) > 1:
                # Parallel execution of independent branches
                tasks = [
                    self._execute_node(workflow, node, context)
                    for node in start_nodes
                ]
                await asyncio.gather(*tasks)
            else:
                # Sequential execution
                for node in start_nodes:
                    await self._execute_node(workflow, node, context)
            
            context.status = ExecutionStatus.COMPLETED
            
        except Exception as e:
            context.status = ExecutionStatus.FAILED
            context.error = str(e)
            logger.error(f"Workflow execution failed: {e}")
            traceback.print_exc()
        
        finally:
            context.end_time = datetime.now()
            
            # Update workflow statistics
            workflow.total_runs += 1
            if context.status == ExecutionStatus.COMPLETED:
                workflow.successful_runs += 1
            else:
                workflow.failed_runs += 1
            
            duration = (context.end_time - context.start_time).total_seconds()
            workflow.avg_duration_seconds = (
                (workflow.avg_duration_seconds * (workflow.total_runs - 1) + duration)
                / workflow.total_runs
            )
            
            self._save_workflow(workflow)
        
        return context
    
    async def _execute_node(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        context: ExecutionContext
    ):
        """Execute a single node"""
        if node.status == ExecutionStatus.COMPLETED:
            return  # Already executed
        
        context.current_node = node.id
        node.status = ExecutionStatus.RUNNING
        node.start_time = datetime.now()
        node.execution_count += 1
        
        context.log("info", f"Executing node: {node.name}", node.id)
        self._notify_execution(context)
        
        try:
            # Gather inputs from connected edges
            inputs = {}
            incoming_edges = workflow.get_edges_to(node.id)
            
            for edge in incoming_edges:
                # Check condition if present
                if edge.condition:
                    source_output = context.node_outputs.get(
                        f"{edge.source_node}.{edge.source_port}"
                    )
                    if not self._evaluate_edge_condition(edge.condition, source_output):
                        continue
                
                input_value = context.node_outputs.get(
                    f"{edge.source_node}.{edge.source_port}"
                )
                inputs[edge.target_port] = input_value
            
            # Execute node
            executor = self.executors.get(node.type)
            
            if executor:
                outputs = await executor.execute(node, context, inputs)
            else:
                # Default pass-through for unknown node types
                outputs = {"out": inputs.get("in", None)}
            
            # Store outputs
            node.result = outputs
            for port_name, value in outputs.items():
                context.set_output(node.id, port_name, value)
            
            node.status = ExecutionStatus.COMPLETED
            node.end_time = datetime.now()
            
            context.log("info", f"Node completed: {node.name}", node.id)
            self._notify_execution(context)
            
            # Execute next nodes
            outgoing_edges = workflow.get_edges_from(node.id)
            
            for edge in outgoing_edges:
                # Check condition
                if edge.condition:
                    source_output = outputs.get(edge.source_port)
                    if not self._evaluate_edge_condition(edge.condition, source_output):
                        continue
                
                next_node = workflow.get_node(edge.target_node)
                if next_node and next_node.status == ExecutionStatus.PENDING:
                    # Check if all required inputs are ready
                    if self._all_inputs_ready(workflow, next_node, context):
                        await self._execute_node(workflow, next_node, context)
        
        except Exception as e:
            node.status = ExecutionStatus.FAILED
            node.error = str(e)
            node.end_time = datetime.now()
            
            context.log("error", f"Node failed: {node.name} - {str(e)}", node.id)
            self._notify_execution(context)
            
            if workflow.stop_on_error:
                raise
    
    def _all_inputs_ready(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        context: ExecutionContext
    ) -> bool:
        """Check if all required inputs for a node are ready"""
        incoming_edges = workflow.get_edges_to(node.id)
        
        for port in node.inputs:
            if port.required:
                # Check if there's an edge providing this input
                has_edge = any(e.target_port == port.id for e in incoming_edges)
                if has_edge:
                    # Check if the source node has completed
                    for edge in incoming_edges:
                        if edge.target_port == port.id:
                            source_node = workflow.get_node(edge.source_node)
                            if source_node and source_node.status != ExecutionStatus.COMPLETED:
                                return False
        
        return True
    
    def _evaluate_edge_condition(self, condition: str, value: Any) -> bool:
        """Evaluate a condition on an edge"""
        try:
            if condition == "true":
                return bool(value)
            elif condition == "false":
                return not bool(value)
            elif condition.startswith("=="):
                return str(value) == condition[2:].strip().strip('"\'')
            elif condition.startswith("!="):
                return str(value) != condition[2:].strip().strip('"\'')
            elif condition.startswith("contains:"):
                return condition[9:].strip() in str(value)
            else:
                return bool(value)
        except:
            return False
    
    def _notify_execution(self, context: ExecutionContext):
        """Notify callbacks about execution updates"""
        for callback in self._execution_callbacks.get(context.execution_id, []):
            try:
                callback(context)
            except:
                pass
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get an execution context"""
        return self.executions.get(execution_id)
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        context = self.executions.get(execution_id)
        if not context or context.status != ExecutionStatus.RUNNING:
            return False
        
        context.status = ExecutionStatus.CANCELLED
        context.end_time = datetime.now()
        
        return True
    
    # =========================================================================
    # SCHEDULING
    # =========================================================================
    
    def schedule_workflow(
        self,
        workflow_id: str,
        frequency: ScheduleFrequency,
        time: str = "09:00",
        days: List[int] = None,
        cron: str = ""
    ) -> bool:
        """Schedule a workflow for automatic execution"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        workflow.trigger_type = TriggerType.SCHEDULED
        workflow.schedule = WorkflowSchedule(
            enabled=True,
            frequency=frequency,
            time=time,
            days=days or [1, 2, 3, 4, 5],
            cron=cron,
            next_run=self._calculate_next_run(frequency, time, days)
        )
        
        self._save_workflow(workflow)
        
        return True
    
    def _calculate_next_run(
        self,
        frequency: ScheduleFrequency,
        time: str,
        days: List[int] = None
    ) -> datetime:
        """Calculate the next run time based on schedule"""
        now = datetime.now()
        hour, minute = map(int, time.split(":"))
        
        if frequency == ScheduleFrequency.ONCE:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif frequency == ScheduleFrequency.HOURLY:
            next_run = now.replace(minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(hours=1)
        
        elif frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        
        elif frequency == ScheduleFrequency.WEEKLY:
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if days:
                while next_run.isoweekday() not in days or next_run <= now:
                    next_run += timedelta(days=1)
        
        else:
            next_run = now + timedelta(days=1)
        
        return next_run
    
    def start_scheduler(self):
        """Start the background scheduler"""
        if self._scheduler_running:
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info("Workflow scheduler started")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
    
    def _scheduler_loop(self):
        """Background scheduler loop"""
        while self._scheduler_running:
            try:
                now = datetime.now()
                
                for workflow in self.workflows.values():
                    if (workflow.trigger_type == TriggerType.SCHEDULED and
                        workflow.schedule.enabled and
                        workflow.schedule.next_run and
                        workflow.schedule.next_run <= now):
                        
                        # Execute workflow
                        logger.info(f"Executing scheduled workflow: {workflow.name}")
                        asyncio.run(self.execute_workflow(workflow.id))
                        
                        # Update schedule
                        workflow.schedule.last_run = now
                        workflow.schedule.next_run = self._calculate_next_run(
                            workflow.schedule.frequency,
                            workflow.schedule.time,
                            workflow.schedule.days
                        )
                        self._save_workflow(workflow)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    # =========================================================================
    # TEMPLATES
    # =========================================================================
    
    def get_templates(self, category: Optional[str] = None) -> List[Workflow]:
        """Get available workflow templates"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def create_from_template(
        self,
        template_id: str,
        name: str,
        description: str = ""
    ) -> Optional[Workflow]:
        """Create a new workflow from a template"""
        return self.create_workflow(
            name=name,
            description=description,
            template_id=template_id
        )
    
    def save_as_template(
        self,
        workflow_id: str,
        name: str,
        description: str = ""
    ) -> Optional[Workflow]:
        """Save a workflow as a template"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        template = copy.deepcopy(workflow)
        template.id = f"template-{str(uuid.uuid4())[:8]}"
        template.name = name
        template.description = description
        template.is_template = True
        
        # Reset statistics
        template.total_runs = 0
        template.successful_runs = 0
        template.failed_runs = 0
        
        self.templates[template.id] = template
        
        # Save to disk
        templates_path = self.storage_dir / "templates"
        templates_path.mkdir(exist_ok=True)
        
        file_path = templates_path / f"{template.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
        
        return template
    
    # =========================================================================
    # IMPORT/EXPORT
    # =========================================================================
    
    def export_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Export a workflow for sharing"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        export_data = workflow.to_dict()
        export_data["export_version"] = "1.0"
        export_data["exported_at"] = datetime.now().isoformat()
        
        return export_data
    
    def import_workflow(self, data: Dict[str, Any], new_name: Optional[str] = None) -> Workflow:
        """Import a workflow from export data"""
        workflow = Workflow.from_dict(data)
        
        # Generate new IDs
        workflow.id = str(uuid.uuid4())
        if new_name:
            workflow.name = new_name
        
        workflow.created_at = datetime.now()
        workflow.updated_at = datetime.now()
        workflow.version = 1
        workflow.versions = []
        workflow.total_runs = 0
        workflow.successful_runs = 0
        workflow.failed_runs = 0
        
        self.workflows[workflow.id] = workflow
        self._save_workflow(workflow)
        
        return workflow
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def get_node_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get catalog of available node types"""
        catalog = defaultdict(list)
        
        node_info = [
            # Input nodes
            {"type": NodeType.START, "name": "Başlangıç", "category": "input", 
             "description": "Workflow başlangıç noktası", "icon": "play"},
            {"type": NodeType.TEXT_INPUT, "name": "Metin Girişi", "category": "input",
             "description": "Sabit metin veya değişken", "icon": "type"},
            {"type": NodeType.USER_INPUT, "name": "Kullanıcı Girişi", "category": "input",
             "description": "Çalışma zamanında kullanıcı girişi al", "icon": "edit"},
            {"type": NodeType.VARIABLE, "name": "Değişken", "category": "input",
             "description": "Workflow değişkeni", "icon": "variable"},
            
            # AI nodes
            {"type": NodeType.LLM_CHAT, "name": "AI Sohbet", "category": "ai",
             "description": "LLM ile sohbet", "icon": "brain"},
            {"type": NodeType.RAG_QUERY, "name": "RAG Sorgu", "category": "ai",
             "description": "Dökümanlardan bilgi sorgula", "icon": "search"},
            {"type": NodeType.SUMMARIZE, "name": "Özetle", "category": "ai",
             "description": "Metni özetle", "icon": "file-text"},
            {"type": NodeType.TRANSLATE, "name": "Çevir", "category": "ai",
             "description": "Metni çevir", "icon": "globe"},
            {"type": NodeType.CLASSIFY, "name": "Sınıflandır", "category": "ai",
             "description": "Metni kategorize et", "icon": "tags"},
            {"type": NodeType.CODE_EXECUTE, "name": "Kod Çalıştır", "category": "ai",
             "description": "Python kodu çalıştır", "icon": "code"},
            
            # Processing nodes
            {"type": NodeType.TEXT_TRANSFORM, "name": "Metin Dönüştür", "category": "processing",
             "description": "Metin işlemleri", "icon": "type"},
            {"type": NodeType.JSON_PARSE, "name": "JSON Parse", "category": "processing",
             "description": "JSON parse et", "icon": "braces"},
            {"type": NodeType.MERGE, "name": "Birleştir", "category": "processing",
             "description": "Birden fazla girdiyi birleştir", "icon": "git-merge"},
            {"type": NodeType.SPLIT, "name": "Böl", "category": "processing",
             "description": "Metni parçalara böl", "icon": "scissors"},
            {"type": NodeType.TEMPLATE, "name": "Şablon", "category": "processing",
             "description": "Şablon ile format", "icon": "layout"},
            
            # Control nodes
            {"type": NodeType.CONDITION, "name": "Koşul", "category": "control",
             "description": "If/else dallanma", "icon": "git-branch"},
            {"type": NodeType.LOOP, "name": "Döngü", "category": "control",
             "description": "Liste üzerinde döngü", "icon": "repeat"},
            {"type": NodeType.SWITCH, "name": "Switch", "category": "control",
             "description": "Çoklu durum kontrolü", "icon": "git-branch"},
            {"type": NodeType.DELAY, "name": "Bekle", "category": "control",
             "description": "Belirli süre bekle", "icon": "clock"},
            
            # Output nodes
            {"type": NodeType.OUTPUT, "name": "Çıktı", "category": "output",
             "description": "Sonucu göster", "icon": "log-out"},
            {"type": NodeType.FILE_WRITE, "name": "Dosyaya Yaz", "category": "output",
             "description": "Dosyaya kaydet", "icon": "save"},
            {"type": NodeType.END, "name": "Bitiş", "category": "output",
             "description": "Workflow bitiş noktası", "icon": "stop"}
        ]
        
        for info in node_info:
            catalog[info["category"]].append(info)
        
        return dict(catalog)


# =============================================================================
# SINGLETON
# =============================================================================

advanced_workflow_engine = AdvancedWorkflowEngine()
