"""
Enterprise AI Assistant - Workflow Orchestrator Module
Visual workflow designer with node-based execution

Provides:
- Workflow creation and management
- Node-based execution engine
- Template management
- Scheduling support
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class WorkflowStatus(str, Enum):
    """Workflow status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeType(str, Enum):
    """Available node types."""
    INPUT = "input"
    OUTPUT = "output"
    LLM = "llm"
    RAG = "rag"
    CONDITION = "condition"
    LOOP = "loop"
    TRANSFORM = "transform"
    API_CALL = "api_call"
    CODE = "code"
    DELAY = "delay"
    PARALLEL = "parallel"
    MERGE = "merge"
    AGENT = "agent"
    MEMORY = "memory"


@dataclass
class NodePosition:
    """Node position in visual editor."""
    x: float = 0
    y: float = 0


@dataclass
class WorkflowNode:
    """A node in the workflow."""
    id: str
    node_type: str
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: NodePosition = field(default_factory=NodePosition)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "node_type": self.node_type,
            "name": self.name,
            "config": self.config,
            "position": {"x": self.position.x, "y": self.position.y},
            "inputs": self.inputs,
            "outputs": self.outputs
        }


@dataclass
class WorkflowEdge:
    """An edge connecting two nodes."""
    id: str
    source_node: str
    source_port: str
    target_node: str
    target_port: str
    condition: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source_node": self.source_node,
            "source_port": self.source_port,
            "target_node": self.target_node,
            "target_port": self.target_port,
            "condition": self.condition
        }


@dataclass
class Workflow:
    """A complete workflow definition."""
    id: str
    name: str
    description: str = ""
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    is_template: bool = False
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "category": self.category,
            "tags": self.tags,
            "status": self.status.value,
            "is_template": self.is_template,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class ExecutionResult:
    """Result of a workflow execution."""
    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    outputs: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "outputs": self.outputs,
            "node_results": self.node_results,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class WorkflowOrchestrator:
    """
    Manages workflow creation, storage, and execution.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/workflows")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, ExecutionResult] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}
        self.schedules: Dict[str, Dict] = {}
        self.triggers: Dict[str, Dict] = {}
        self.templates: Dict[str, Workflow] = {}
        
        # Node executors
        self.node_executors: Dict[str, Callable] = {
            NodeType.INPUT.value: self._execute_input_node,
            NodeType.OUTPUT.value: self._execute_output_node,
            NodeType.LLM.value: self._execute_llm_node,
            NodeType.RAG.value: self._execute_rag_node,
            NodeType.CONDITION.value: self._execute_condition_node,
            NodeType.TRANSFORM.value: self._execute_transform_node,
            NodeType.DELAY.value: self._execute_delay_node,
            NodeType.CODE.value: self._execute_code_node,
        }
        
        self._load_workflows()
    
    def _generate_id(self, prefix: str = "wf") -> str:
        """Generate a unique ID."""
        timestamp = datetime.now().isoformat()
        hash_val = hashlib.md5(timestamp.encode()).hexdigest()[:8]
        return f"{prefix}_{hash_val}"
    
    def _load_workflows(self):
        """Load workflows from storage."""
        workflows_file = self.storage_path / "workflows.json"
        if workflows_file.exists():
            try:
                with open(workflows_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for wf_data in data.get("workflows", []):
                        workflow = self._dict_to_workflow(wf_data)
                        self.workflows[workflow.id] = workflow
                        if workflow.is_template:
                            self.templates[workflow.id] = workflow
            except Exception:
                pass
    
    def _save_workflows(self):
        """Save workflows to storage."""
        workflows_file = self.storage_path / "workflows.json"
        data = {
            "workflows": [wf.to_dict() for wf in self.workflows.values()]
        }
        with open(workflows_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    
    def _dict_to_workflow(self, data: Dict) -> Workflow:
        """Convert dict to Workflow object."""
        nodes = []
        for n in data.get("nodes", []):
            pos_data = n.get("position", {})
            nodes.append(WorkflowNode(
                id=n.get("id", self._generate_id("node")),
                node_type=n.get("node_type", "input"),
                name=n.get("name", "Node"),
                config=n.get("config", {}),
                position=NodePosition(x=pos_data.get("x", 0), y=pos_data.get("y", 0))
            ))
        
        edges = []
        for e in data.get("edges", []):
            edges.append(WorkflowEdge(
                id=e.get("id", self._generate_id("edge")),
                source_node=e.get("source_node", ""),
                source_port=e.get("source_port", "output"),
                target_node=e.get("target_node", ""),
                target_port=e.get("target_port", "input"),
                condition=e.get("condition")
            ))
        
        return Workflow(
            id=data.get("id", self._generate_id()),
            name=data.get("name", "Untitled"),
            description=data.get("description", ""),
            nodes=nodes,
            edges=edges,
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            status=WorkflowStatus(data.get("status", "draft")),
            is_template=data.get("is_template", False),
            version=data.get("version", 1)
        )
    
    # ==================== WORKFLOW CRUD ====================
    
    async def create_workflow(
        self,
        name: str,
        description: str = "",
        nodes: List = None,
        edges: List = None,
        category: str = "general",
        tags: List[str] = None,
        is_template: bool = False
    ) -> Workflow:
        """Create a new workflow."""
        workflow_id = self._generate_id()
        
        # Convert nodes
        wf_nodes = []
        if nodes:
            for i, n in enumerate(nodes):
                if hasattr(n, 'dict'):
                    n = n.dict()
                elif hasattr(n, 'model_dump'):
                    n = n.model_dump()
                pos = n.get("position", {})
                wf_nodes.append(WorkflowNode(
                    id=self._generate_id("node"),
                    node_type=n.get("node_type", "input"),
                    name=n.get("name", f"Node {i+1}"),
                    config=n.get("config", {}),
                    position=NodePosition(x=pos.get("x", i*200), y=pos.get("y", 100))
                ))
        
        # Convert edges
        wf_edges = []
        if edges:
            for e in edges:
                if hasattr(e, 'dict'):
                    e = e.dict()
                elif hasattr(e, 'model_dump'):
                    e = e.model_dump()
                wf_edges.append(WorkflowEdge(
                    id=self._generate_id("edge"),
                    source_node=e.get("source_node", ""),
                    source_port=e.get("source_port", "output"),
                    target_node=e.get("target_node", ""),
                    target_port=e.get("target_port", "input"),
                    condition=e.get("condition")
                ))
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            nodes=wf_nodes,
            edges=wf_edges,
            category=category,
            tags=tags or [],
            is_template=is_template
        )
        
        self.workflows[workflow_id] = workflow
        if is_template:
            self.templates[workflow_id] = workflow
        
        self._save_workflows()
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def list_workflows(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        is_template: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Workflow]:
        """List workflows with filters."""
        results = []
        
        for wf in self.workflows.values():
            # Apply filters
            if is_template and not wf.is_template:
                continue
            if category and wf.category != category:
                continue
            if status and wf.status.value != status:
                continue
            if tags and not any(t in wf.tags for t in tags):
                continue
            if search and search.lower() not in wf.name.lower():
                continue
            
            results.append(wf)
        
        # Sort by updated_at
        results.sort(key=lambda w: w.updated_at, reverse=True)
        
        return results[offset:offset + limit]
    
    async def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Workflow]:
        """Update a workflow."""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        if "name" in updates and updates["name"]:
            workflow.name = updates["name"]
        if "description" in updates and updates["description"] is not None:
            workflow.description = updates["description"]
        if "category" in updates and updates["category"]:
            workflow.category = updates["category"]
        if "tags" in updates and updates["tags"] is not None:
            workflow.tags = updates["tags"]
        if "status" in updates and updates["status"]:
            workflow.status = WorkflowStatus(updates["status"])
        
        workflow.updated_at = datetime.now()
        workflow.version += 1
        
        self._save_workflows()
        return workflow
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id not in self.workflows:
            return False
        
        del self.workflows[workflow_id]
        self.templates.pop(workflow_id, None)
        self._save_workflows()
        return True
    
    # ==================== NODE OPERATIONS ====================
    
    async def add_node(
        self,
        workflow_id: str,
        node_type: str,
        name: str,
        config: Dict = None,
        position: Dict = None
    ) -> Optional[WorkflowNode]:
        """Add a node to workflow."""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        pos = position or {}
        
        node = WorkflowNode(
            id=self._generate_id("node"),
            node_type=node_type,
            name=name,
            config=config or {},
            position=NodePosition(x=pos.get("x", 0), y=pos.get("y", 0))
        )
        
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now()
        self._save_workflows()
        
        return node
    
    async def update_node(
        self,
        workflow_id: str,
        node_id: str,
        updates: Dict[str, Any]
    ) -> Optional[WorkflowNode]:
        """Update a node."""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        for node in workflow.nodes:
            if node.id == node_id:
                if "name" in updates and updates["name"]:
                    node.name = updates["name"]
                if "config" in updates and updates["config"]:
                    node.config.update(updates["config"])
                if "position" in updates and updates["position"]:
                    pos = updates["position"]
                    if hasattr(pos, 'dict'):
                        pos = pos.dict()
                    elif hasattr(pos, 'model_dump'):
                        pos = pos.model_dump()
                    node.position = NodePosition(x=pos.get("x", 0), y=pos.get("y", 0))
                
                workflow.updated_at = datetime.now()
                self._save_workflows()
                return node
        
        return None
    
    async def delete_node(self, workflow_id: str, node_id: str) -> bool:
        """Delete a node."""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        original_len = len(workflow.nodes)
        workflow.nodes = [n for n in workflow.nodes if n.id != node_id]
        
        # Remove connected edges
        workflow.edges = [e for e in workflow.edges 
                        if e.source_node != node_id and e.target_node != node_id]
        
        if len(workflow.nodes) < original_len:
            workflow.updated_at = datetime.now()
            self._save_workflows()
            return True
        
        return False
    
    async def add_edge(
        self,
        workflow_id: str,
        source_node: str,
        target_node: str,
        source_port: str = "output",
        target_port: str = "input",
        condition: Optional[str] = None
    ) -> Optional[WorkflowEdge]:
        """Add an edge between nodes."""
        if workflow_id not in self.workflows:
            return None
        
        workflow = self.workflows[workflow_id]
        
        edge = WorkflowEdge(
            id=self._generate_id("edge"),
            source_node=source_node,
            source_port=source_port,
            target_node=target_node,
            target_port=target_port,
            condition=condition
        )
        
        workflow.edges.append(edge)
        workflow.updated_at = datetime.now()
        self._save_workflows()
        
        return edge
    
    async def delete_edge(self, workflow_id: str, edge_id: str) -> bool:
        """Delete an edge."""
        if workflow_id not in self.workflows:
            return False
        
        workflow = self.workflows[workflow_id]
        original_len = len(workflow.edges)
        workflow.edges = [e for e in workflow.edges if e.id != edge_id]
        
        if len(workflow.edges) < original_len:
            workflow.updated_at = datetime.now()
            self._save_workflows()
            return True
        
        return False
    
    # ==================== EXECUTION ====================
    
    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any] = None,
        options: Dict[str, Any] = None
    ) -> ExecutionResult:
        """Execute a workflow."""
        if workflow_id not in self.workflows:
            return ExecutionResult(
                execution_id=self._generate_id("exec"),
                workflow_id=workflow_id,
                status=ExecutionStatus.FAILED,
                error="Workflow not found"
            )
        
        workflow = self.workflows[workflow_id]
        execution_id = self._generate_id("exec")
        
        result = ExecutionResult(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = result
        
        try:
            # Build execution graph
            node_map = {n.id: n for n in workflow.nodes}
            outputs = inputs or {}
            
            # Find input nodes (no incoming edges)
            target_nodes = {e.target_node for e in workflow.edges}
            input_nodes = [n for n in workflow.nodes if n.id not in target_nodes]
            
            # Execute nodes in order
            executed = set()
            to_execute = list(input_nodes)
            
            while to_execute:
                node = to_execute.pop(0)
                
                if node.id in executed:
                    continue
                
                # Execute node
                try:
                    node_output = await self._execute_node(node, outputs)
                    outputs[node.id] = node_output
                    result.node_results[node.id] = {
                        "status": "completed",
                        "output": node_output
                    }
                except Exception as e:
                    result.node_results[node.id] = {
                        "status": "failed",
                        "error": str(e)
                    }
                
                executed.add(node.id)
                
                # Add successor nodes
                for edge in workflow.edges:
                    if edge.source_node == node.id:
                        target = node_map.get(edge.target_node)
                        if target and target.id not in executed:
                            to_execute.append(target)
            
            result.status = ExecutionStatus.COMPLETED
            result.outputs = outputs
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.now()
        
        return result
    
    async def _execute_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute a single node."""
        executor = self.node_executors.get(node.node_type, self._execute_default_node)
        return await executor(node, context)
    
    async def _execute_input_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute input node."""
        return node.config.get("value", context.get("input", ""))
    
    async def _execute_output_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute output node."""
        # Get input from connected node
        return context.get(node.config.get("source_node", ""), "")
    
    async def _execute_llm_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute LLM node."""
        try:
            from core.llm_manager import llm_manager
            prompt = node.config.get("prompt", "")
            # Replace variables
            for key, value in context.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))
            
            response = await llm_manager.generate(prompt)
            return response
        except Exception as e:
            return f"LLM Error: {e}"
    
    async def _execute_rag_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute RAG node."""
        try:
            from rag.unified_orchestrator import advanced_orchestrator
            query = node.config.get("query", "")
            for key, value in context.items():
                query = query.replace(f"{{{key}}}", str(value))
            
            result = await advanced_orchestrator.query(query)
            return result.get("answer", "")
        except Exception as e:
            return f"RAG Error: {e}"
    
    async def _execute_condition_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute condition node."""
        condition = node.config.get("condition", "true")
        try:
            result = eval(condition, {"context": context})
            return {"branch": "true" if result else "false", "result": result}
        except Exception:
            return {"branch": "false", "result": False}
    
    async def _execute_transform_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute transform node."""
        transform_type = node.config.get("transform", "passthrough")
        input_key = node.config.get("input", "")
        value = context.get(input_key, "")
        
        if transform_type == "uppercase":
            return str(value).upper()
        elif transform_type == "lowercase":
            return str(value).lower()
        elif transform_type == "json_parse":
            return json.loads(str(value))
        elif transform_type == "json_stringify":
            return json.dumps(value)
        else:
            return value
    
    async def _execute_delay_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute delay node."""
        delay_seconds = node.config.get("seconds", 1)
        await asyncio.sleep(delay_seconds)
        return {"delayed": delay_seconds}
    
    async def _execute_code_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Execute code node (sandboxed)."""
        code = node.config.get("code", "return None")
        try:
            # Simple eval for now (should be sandboxed in production)
            local_context = {"context": context}
            exec(f"__result__ = {code}", local_context)
            return local_context.get("__result__")
        except Exception as e:
            return f"Code Error: {e}"
    
    async def _execute_default_node(self, node: WorkflowNode, context: Dict) -> Any:
        """Default node executor."""
        return node.config
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get execution result."""
        return self.executions.get(execution_id)
    
    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[ExecutionResult]:
        """List executions."""
        results = list(self.executions.values())
        
        if workflow_id:
            results = [r for r in results if r.workflow_id == workflow_id]
        if status:
            results = [r for r in results if r.status.value == status]
        
        results.sort(key=lambda r: r.started_at or datetime.min, reverse=True)
        return results[:limit]
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an execution."""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            del self.active_executions[execution_id]
            
            if execution_id in self.executions:
                self.executions[execution_id].status = ExecutionStatus.CANCELLED
                self.executions[execution_id].completed_at = datetime.now()
            
            return True
        return False
    
    # ==================== TEMPLATES ====================
    
    def get_templates(self, category: Optional[str] = None) -> List[Workflow]:
        """Get workflow templates."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    async def create_from_template(
        self,
        template_id: str,
        name: str,
        customizations: Dict[str, Any] = None
    ) -> Optional[Workflow]:
        """Create workflow from template."""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id]
        
        # Create new workflow based on template
        workflow = await self.create_workflow(
            name=name,
            description=template.description,
            nodes=[{"node_type": n.node_type, "name": n.name, "config": n.config, 
                   "position": {"x": n.position.x, "y": n.position.y}} 
                  for n in template.nodes],
            edges=[{"source_node": e.source_node, "source_port": e.source_port,
                   "target_node": e.target_node, "target_port": e.target_port,
                   "condition": e.condition}
                  for e in template.edges],
            category=template.category,
            tags=template.tags.copy(),
            is_template=False
        )
        
        return workflow
    
    # ==================== SCHEDULING ====================
    
    def get_schedules(self, workflow_id: str) -> List[Dict]:
        """Get schedules for workflow."""
        return [s for s in self.schedules.values() if s.get("workflow_id") == workflow_id]
    
    async def add_schedule(
        self,
        workflow_id: str,
        schedule_type: str,
        value: str,
        inputs: Dict = None
    ) -> Dict:
        """Add a schedule."""
        schedule_id = self._generate_id("sched")
        schedule = {
            "id": schedule_id,
            "workflow_id": workflow_id,
            "schedule_type": schedule_type,
            "value": value,
            "inputs": inputs or {},
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
        self.schedules[schedule_id] = schedule
        return schedule
    
    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            return True
        return False
    
    # ==================== TRIGGERS ====================
    
    def get_triggers(self, workflow_id: str) -> List[Dict]:
        """Get triggers for workflow."""
        return [t for t in self.triggers.values() if t.get("workflow_id") == workflow_id]
    
    async def add_trigger(
        self,
        workflow_id: str,
        trigger_type: str,
        config: Dict = None
    ) -> Dict:
        """Add a trigger."""
        trigger_id = self._generate_id("trig")
        trigger = {
            "id": trigger_id,
            "workflow_id": workflow_id,
            "trigger_type": trigger_type,
            "config": config or {},
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
        self.triggers[trigger_id] = trigger
        return trigger
    
    async def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a trigger."""
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]
            return True
        return False
    
    # ==================== STATS ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "total_workflows": len(self.workflows),
            "active_workflows": len([w for w in self.workflows.values() 
                                    if w.status == WorkflowStatus.ACTIVE]),
            "total_templates": len(self.templates),
            "total_executions": len(self.executions),
            "active_executions": len(self.active_executions),
            "schedules": len(self.schedules),
            "triggers": len(self.triggers)
        }
    
    def get_node_types(self) -> List[Dict]:
        """Get available node types."""
        return [
            {"type": NodeType.INPUT.value, "name": "Input", "category": "io", 
             "description": "Workflow input point"},
            {"type": NodeType.OUTPUT.value, "name": "Output", "category": "io",
             "description": "Workflow output point"},
            {"type": NodeType.LLM.value, "name": "LLM", "category": "ai",
             "description": "Language model processing"},
            {"type": NodeType.RAG.value, "name": "RAG", "category": "ai",
             "description": "Retrieval augmented generation"},
            {"type": NodeType.CONDITION.value, "name": "Condition", "category": "logic",
             "description": "Conditional branching"},
            {"type": NodeType.LOOP.value, "name": "Loop", "category": "logic",
             "description": "Iteration control"},
            {"type": NodeType.TRANSFORM.value, "name": "Transform", "category": "data",
             "description": "Data transformation"},
            {"type": NodeType.API_CALL.value, "name": "API Call", "category": "integration",
             "description": "External API integration"},
            {"type": NodeType.CODE.value, "name": "Code", "category": "advanced",
             "description": "Custom code execution"},
            {"type": NodeType.DELAY.value, "name": "Delay", "category": "control",
             "description": "Time delay"},
            {"type": NodeType.PARALLEL.value, "name": "Parallel", "category": "control",
             "description": "Parallel execution"},
            {"type": NodeType.MERGE.value, "name": "Merge", "category": "control",
             "description": "Merge parallel branches"},
            {"type": NodeType.AGENT.value, "name": "Agent", "category": "ai",
             "description": "AI agent execution"},
            {"type": NodeType.MEMORY.value, "name": "Memory", "category": "ai",
             "description": "Memory operations"},
        ]
    
    def get_categories(self) -> List[str]:
        """Get workflow categories."""
        categories = set(w.category for w in self.workflows.values())
        return sorted(list(categories)) or ["general", "automation", "ai", "data"]


# Singleton instance
workflow_orchestrator = WorkflowOrchestrator()


__all__ = [
    "WorkflowOrchestrator",
    "workflow_orchestrator",
    "Workflow",
    "WorkflowNode",
    "WorkflowEdge",
    "ExecutionResult",
    "WorkflowStatus",
    "ExecutionStatus",
    "NodeType"
]
