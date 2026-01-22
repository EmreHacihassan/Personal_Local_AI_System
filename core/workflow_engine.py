"""
AI Workflow Builder - Visual workflow designer for AI pipelines
Create, save, and execute complex AI workflows
100% Local execution
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import traceback

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    # Input nodes
    TEXT_INPUT = "text_input"
    FILE_INPUT = "file_input"
    VARIABLE = "variable"
    
    # AI nodes
    LLM_CHAT = "llm_chat"
    LLM_COMPLETE = "llm_complete"
    EMBEDDING = "embedding"
    RAG_QUERY = "rag_query"
    VISION_ANALYZE = "vision_analyze"
    CODE_EXECUTE = "code_execute"
    VOICE_STT = "voice_stt"
    VOICE_TTS = "voice_tts"
    
    # Processing nodes
    TEXT_TRANSFORM = "text_transform"
    JSON_PARSE = "json_parse"
    JSON_EXTRACT = "json_extract"
    REGEX_EXTRACT = "regex_extract"
    TEMPLATE = "template"
    SPLIT = "split"
    MERGE = "merge"
    
    # Control flow
    CONDITION = "condition"
    LOOP = "loop"
    SWITCH = "switch"
    DELAY = "delay"
    
    # Output nodes
    OUTPUT = "output"
    FILE_WRITE = "file_write"
    WEBHOOK = "webhook"
    
    # Special
    START = "start"
    END = "end"
    NOTE = "note"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowNode:
    """A single node in the workflow"""
    id: str
    type: NodeType
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    inputs: List[str] = field(default_factory=list)  # Input port IDs
    outputs: List[str] = field(default_factory=list)  # Output port IDs


@dataclass
class WorkflowEdge:
    """Connection between nodes"""
    id: str
    source_node: str
    source_port: str
    target_node: str
    target_port: str


@dataclass
class Workflow:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    variables: Dict[str, Any] = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1


@dataclass
class ExecutionContext:
    """Context for workflow execution"""
    workflow_id: str
    execution_id: str
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict] = field(default_factory=list)
    current_node: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.RUNNING
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class WorkflowEngine:
    """
    Execute AI workflows
    """
    
    def __init__(self, storage_dir: str = "data/workflows"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, ExecutionContext] = {}
        self._load_workflows()
        
        # Node executors
        self.executors: Dict[NodeType, Callable] = {
            NodeType.START: self._exec_start,
            NodeType.END: self._exec_end,
            NodeType.TEXT_INPUT: self._exec_text_input,
            NodeType.VARIABLE: self._exec_variable,
            NodeType.LLM_CHAT: self._exec_llm_chat,
            NodeType.LLM_COMPLETE: self._exec_llm_complete,
            NodeType.RAG_QUERY: self._exec_rag_query,
            NodeType.CODE_EXECUTE: self._exec_code,
            NodeType.TEXT_TRANSFORM: self._exec_text_transform,
            NodeType.JSON_PARSE: self._exec_json_parse,
            NodeType.JSON_EXTRACT: self._exec_json_extract,
            NodeType.TEMPLATE: self._exec_template,
            NodeType.CONDITION: self._exec_condition,
            NodeType.LOOP: self._exec_loop,
            NodeType.MERGE: self._exec_merge,
            NodeType.OUTPUT: self._exec_output,
            NodeType.DELAY: self._exec_delay,
        }
    
    def _load_workflows(self):
        """Load saved workflows from disk"""
        for f in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                workflow = self._dict_to_workflow(data)
                self.workflows[workflow.id] = workflow
            except Exception as e:
                logger.error(f"Failed to load workflow {f}: {e}")
    
    def _save_workflow(self, workflow: Workflow):
        """Save workflow to disk"""
        path = self.storage_dir / f"{workflow.id}.json"
        data = self._workflow_to_dict(workflow)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def _workflow_to_dict(self, workflow: Workflow) -> Dict:
        """Convert workflow to dictionary"""
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type.value,
                    "name": n.name,
                    "config": n.config,
                    "position": n.position,
                    "inputs": n.inputs,
                    "outputs": n.outputs
                }
                for n in workflow.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_node": e.source_node,
                    "source_port": e.source_port,
                    "target_node": e.target_node,
                    "target_port": e.target_port
                }
                for e in workflow.edges
            ],
            "variables": workflow.variables,
            "status": workflow.status.value,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
            "version": workflow.version
        }
    
    def _dict_to_workflow(self, data: Dict) -> Workflow:
        """Convert dictionary to workflow"""
        return Workflow(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            nodes=[
                WorkflowNode(
                    id=n["id"],
                    type=NodeType(n["type"]),
                    name=n["name"],
                    config=n.get("config", {}),
                    position=n.get("position", {"x": 0, "y": 0}),
                    inputs=n.get("inputs", []),
                    outputs=n.get("outputs", [])
                )
                for n in data["nodes"]
            ],
            edges=[
                WorkflowEdge(
                    id=e["id"],
                    source_node=e["source_node"],
                    source_port=e["source_port"],
                    target_node=e["target_node"],
                    target_port=e["target_port"]
                )
                for e in data["edges"]
            ],
            variables=data.get("variables", {}),
            status=WorkflowStatus(data.get("status", "draft")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            version=data.get("version", 1)
        )
    
    # CRUD Operations
    
    def create_workflow(
        self,
        name: str,
        description: str = "",
        nodes: Optional[List[Dict]] = None,
        edges: Optional[List[Dict]] = None
    ) -> Workflow:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())[:8]
        
        # Default nodes if none provided
        if nodes is None:
            nodes = [
                {"id": "start", "type": "start", "name": "Start", "position": {"x": 100, "y": 200}},
                {"id": "end", "type": "end", "name": "End", "position": {"x": 500, "y": 200}}
            ]
        
        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            nodes=[
                WorkflowNode(
                    id=n["id"],
                    type=NodeType(n["type"]),
                    name=n["name"],
                    config=n.get("config", {}),
                    position=n.get("position", {"x": 0, "y": 0}),
                    inputs=n.get("inputs", []),
                    outputs=n.get("outputs", [])
                )
                for n in nodes
            ],
            edges=[
                WorkflowEdge(
                    id=e.get("id", str(uuid.uuid4())[:8]),
                    source_node=e["source_node"],
                    source_port=e.get("source_port", "output"),
                    target_node=e["target_node"],
                    target_port=e.get("target_port", "input")
                )
                for e in (edges or [])
            ]
        )
        
        self.workflows[workflow_id] = workflow
        self._save_workflow(workflow)
        
        logger.info(f"Created workflow: {workflow_id} - {name}")
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[Dict]:
        """List all workflows"""
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "status": w.status.value,
                "node_count": len(w.nodes),
                "updated_at": w.updated_at
            }
            for w in self.workflows.values()
        ]
    
    def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[List[Dict]] = None,
        edges: Optional[List[Dict]] = None,
        variables: Optional[Dict] = None
    ) -> Optional[Workflow]:
        """Update workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        if name:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if variables is not None:
            workflow.variables = variables
        if nodes is not None:
            workflow.nodes = [
                WorkflowNode(
                    id=n["id"],
                    type=NodeType(n["type"]),
                    name=n["name"],
                    config=n.get("config", {}),
                    position=n.get("position", {"x": 0, "y": 0}),
                    inputs=n.get("inputs", []),
                    outputs=n.get("outputs", [])
                )
                for n in nodes
            ]
        if edges is not None:
            workflow.edges = [
                WorkflowEdge(
                    id=e.get("id", str(uuid.uuid4())[:8]),
                    source_node=e["source_node"],
                    source_port=e.get("source_port", "output"),
                    target_node=e["target_node"],
                    target_port=e.get("target_port", "input")
                )
                for e in edges
            ]
        
        workflow.updated_at = datetime.now().isoformat()
        workflow.version += 1
        self._save_workflow(workflow)
        
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            path = self.storage_dir / f"{workflow_id}.json"
            if path.exists():
                path.unlink()
            return True
        return False
    
    # Execution
    
    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """Execute a workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        execution_id = str(uuid.uuid4())[:8]
        
        # Create execution context
        ctx = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=execution_id,
            variables={**(workflow.variables or {}), **(variables or {}), **(inputs or {})},
            start_time=datetime.now()
        )
        self.executions[execution_id] = ctx
        
        try:
            # Find start node
            start_node = next((n for n in workflow.nodes if n.type == NodeType.START), None)
            if not start_node:
                raise ValueError("Workflow has no start node")
            
            # Execute from start
            await self._execute_node(workflow, start_node, ctx)
            
            ctx.status = WorkflowStatus.COMPLETED
            ctx.end_time = datetime.now()
            
        except Exception as e:
            ctx.status = WorkflowStatus.FAILED
            ctx.error = str(e)
            ctx.end_time = datetime.now()
            logger.error(f"Workflow execution failed: {e}")
            logger.error(traceback.format_exc())
        
        return ctx
    
    async def _execute_node(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        ctx: ExecutionContext
    ) -> Any:
        """Execute a single node"""
        ctx.current_node = node.id
        
        # Log execution
        ctx.logs.append({
            "node_id": node.id,
            "node_name": node.name,
            "type": node.type.value,
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        })
        
        try:
            # Get inputs from connected nodes
            inputs = self._get_node_inputs(workflow, node, ctx)
            
            # Execute node
            executor = self.executors.get(node.type)
            if executor:
                result = await executor(node, inputs, ctx)
            else:
                result = inputs  # Pass through
            
            # Store output
            ctx.node_outputs[node.id] = result
            
            # Log success
            ctx.logs.append({
                "node_id": node.id,
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "output_preview": str(result)[:100] if result else None
            })
            
            # Execute connected nodes
            if node.type != NodeType.END:
                next_nodes = self._get_next_nodes(workflow, node)
                for next_node in next_nodes:
                    await self._execute_node(workflow, next_node, ctx)
            
            return result
            
        except Exception as e:
            ctx.logs.append({
                "node_id": node.id,
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })
            raise
    
    def _get_node_inputs(
        self,
        workflow: Workflow,
        node: WorkflowNode,
        ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Get inputs for a node from connected nodes"""
        inputs = {}
        
        for edge in workflow.edges:
            if edge.target_node == node.id:
                source_output = ctx.node_outputs.get(edge.source_node)
                inputs[edge.target_port] = source_output
        
        return inputs
    
    def _get_next_nodes(
        self,
        workflow: Workflow,
        node: WorkflowNode
    ) -> List[WorkflowNode]:
        """Get nodes connected to this node's output"""
        next_ids = set()
        for edge in workflow.edges:
            if edge.source_node == node.id:
                next_ids.add(edge.target_node)
        
        return [n for n in workflow.nodes if n.id in next_ids]
    
    # Node Executors
    
    async def _exec_start(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Start node - pass through variables"""
        return ctx.variables
    
    async def _exec_end(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """End node - collect final output"""
        return inputs.get("input", inputs)
    
    async def _exec_text_input(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> str:
        """Text input node"""
        return node.config.get("text", "")
    
    async def _exec_variable(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Get variable value"""
        var_name = node.config.get("variable_name", "")
        return ctx.variables.get(var_name, node.config.get("default", ""))
    
    async def _exec_llm_chat(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> str:
        """Execute LLM chat"""
        try:
            from core.llm_client import get_llm_client
            
            llm = await get_llm_client()
            prompt = node.config.get("prompt", "")
            system = node.config.get("system", "")
            
            # Replace variables in prompt
            for key, value in {**ctx.variables, **inputs}.items():
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
                system = system.replace(f"{{{{{key}}}}}", str(value))
            
            # Also use input as prompt if provided
            if inputs.get("input"):
                prompt = str(inputs["input"]) if not prompt else f"{prompt}\n\n{inputs['input']}"
            
            response = await llm.chat(prompt, system_prompt=system)
            return response
            
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return f"Error: {e}"
    
    async def _exec_llm_complete(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> str:
        """Execute LLM completion"""
        return await self._exec_llm_chat(node, inputs, ctx)
    
    async def _exec_rag_query(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Dict:
        """Query RAG system"""
        try:
            from rag.rag_engine import get_rag_engine
            
            engine = await get_rag_engine()
            query = inputs.get("input", node.config.get("query", ""))
            top_k = node.config.get("top_k", 5)
            
            results = await engine.query(query, top_k=top_k)
            return {
                "answer": results.get("answer", ""),
                "sources": results.get("sources", [])
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def _exec_code(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Execute code"""
        try:
            from core.code_interpreter import get_code_interpreter
            
            interpreter = get_code_interpreter()
            code = node.config.get("code", "")
            language = node.config.get("language", "python")
            
            # Inject inputs as variables
            if language == "python":
                inject = "\n".join([f"{k} = {repr(v)}" for k, v in inputs.items()])
                code = f"{inject}\n{code}"
            
            from core.code_interpreter import ExecutionLanguage
            lang = ExecutionLanguage.PYTHON if language == "python" else ExecutionLanguage.JAVASCRIPT
            
            result = await interpreter.execute(code, lang)
            return result.return_value or result.stdout
            
        except Exception as e:
            return f"Error: {e}"
    
    async def _exec_text_transform(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> str:
        """Transform text"""
        text = str(inputs.get("input", ""))
        operation = node.config.get("operation", "none")
        
        if operation == "uppercase":
            return text.upper()
        elif operation == "lowercase":
            return text.lower()
        elif operation == "strip":
            return text.strip()
        elif operation == "split_lines":
            return text.split("\n")
        elif operation == "join_lines":
            if isinstance(text, list):
                return "\n".join(text)
            return text
        
        return text
    
    async def _exec_json_parse(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Parse JSON"""
        text = str(inputs.get("input", "{}"))
        try:
            return json.loads(text)
        except:
            return {"error": "Invalid JSON", "raw": text}
    
    async def _exec_json_extract(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Extract value from JSON using path"""
        data = inputs.get("input", {})
        path = node.config.get("path", "")
        
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return None
        
        # Simple path navigation (e.g., "user.name" or "items[0].id")
        current = data
        for part in path.replace("]", "").replace("[", ".").split("."):
            if not part:
                continue
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except:
                    return None
            else:
                return None
        
        return current
    
    async def _exec_template(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> str:
        """Render template with variables"""
        template = node.config.get("template", "")
        
        # Replace variables
        for key, value in {**ctx.variables, **inputs}.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        
        return template
    
    async def _exec_condition(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> bool:
        """Evaluate condition"""
        condition = node.config.get("condition", "true")
        input_val = inputs.get("input")
        
        # Simple conditions
        if condition == "true":
            return True
        elif condition == "false":
            return False
        elif condition == "empty":
            return not bool(input_val)
        elif condition == "not_empty":
            return bool(input_val)
        
        # Eval condition (be careful!)
        try:
            return bool(eval(condition, {"input": input_val, "inputs": inputs, "vars": ctx.variables}))
        except:
            return False
    
    async def _exec_loop(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> List:
        """Loop over items"""
        items = inputs.get("input", [])
        if not isinstance(items, list):
            items = [items]
        
        # Note: Full loop implementation would need special handling
        return items
    
    async def _exec_merge(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Dict:
        """Merge multiple inputs"""
        return dict(inputs)
    
    async def _exec_output(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Output node - store named output"""
        output_name = node.config.get("name", "output")
        ctx.variables[f"output_{output_name}"] = inputs.get("input")
        return inputs.get("input")
    
    async def _exec_delay(self, node: WorkflowNode, inputs: Dict, ctx: ExecutionContext) -> Any:
        """Delay execution"""
        seconds = node.config.get("seconds", 1)
        await asyncio.sleep(min(seconds, 30))  # Max 30 seconds
        return inputs.get("input")
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get execution context"""
        return self.executions.get(execution_id)
    
    def get_node_types(self) -> List[Dict]:
        """Get all available node types with metadata"""
        return [
            {"type": "start", "name": "Start", "category": "control", "inputs": [], "outputs": ["output"]},
            {"type": "end", "name": "End", "category": "control", "inputs": ["input"], "outputs": []},
            {"type": "text_input", "name": "Text Input", "category": "input", "inputs": [], "outputs": ["output"]},
            {"type": "variable", "name": "Variable", "category": "input", "inputs": [], "outputs": ["output"]},
            {"type": "llm_chat", "name": "LLM Chat", "category": "ai", "inputs": ["input"], "outputs": ["output"]},
            {"type": "rag_query", "name": "RAG Query", "category": "ai", "inputs": ["input"], "outputs": ["output"]},
            {"type": "code_execute", "name": "Code Execute", "category": "processing", "inputs": ["input"], "outputs": ["output"]},
            {"type": "text_transform", "name": "Text Transform", "category": "processing", "inputs": ["input"], "outputs": ["output"]},
            {"type": "json_parse", "name": "JSON Parse", "category": "processing", "inputs": ["input"], "outputs": ["output"]},
            {"type": "json_extract", "name": "JSON Extract", "category": "processing", "inputs": ["input"], "outputs": ["output"]},
            {"type": "template", "name": "Template", "category": "processing", "inputs": ["input"], "outputs": ["output"]},
            {"type": "condition", "name": "Condition", "category": "control", "inputs": ["input"], "outputs": ["true", "false"]},
            {"type": "loop", "name": "Loop", "category": "control", "inputs": ["input"], "outputs": ["item", "done"]},
            {"type": "merge", "name": "Merge", "category": "control", "inputs": ["input1", "input2"], "outputs": ["output"]},
            {"type": "output", "name": "Output", "category": "output", "inputs": ["input"], "outputs": []},
            {"type": "delay", "name": "Delay", "category": "control", "inputs": ["input"], "outputs": ["output"]},
        ]


# Global instance
workflow_engine = WorkflowEngine()


def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance"""
    return workflow_engine
