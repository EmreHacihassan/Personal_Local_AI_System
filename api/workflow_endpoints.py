"""
Workflow Builder API Endpoints
Create and execute AI workflows visually
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["Workflow Builder"])

# Lazy import
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        from core.workflow_engine import get_workflow_engine
        _engine = get_workflow_engine()
    return _engine


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    nodes: Optional[List[Dict]] = None
    edges: Optional[List[Dict]] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[Dict]] = None
    edges: Optional[List[Dict]] = None
    variables: Optional[Dict[str, Any]] = None


class WorkflowExecute(BaseModel):
    inputs: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    node_count: int
    created_at: str
    updated_at: str


class ExecutionResponse(BaseModel):
    execution_id: str
    workflow_id: str
    status: str
    outputs: Dict[str, Any]
    logs: List[Dict]
    error: Optional[str]
    duration: Optional[float]


@router.get("/node-types")
async def get_node_types():
    """Get all available node types for workflow builder"""
    engine = get_engine()
    return {"types": engine.get_node_types()}


@router.post("", response_model=WorkflowResponse)
async def create_workflow(request: WorkflowCreate):
    """Create a new workflow"""
    try:
        engine = get_engine()
        workflow = engine.create_workflow(
            name=request.name,
            description=request.description,
            nodes=request.nodes,
            edges=request.edges
        )
        
        return WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status.value,
            node_count=len(workflow.nodes),
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def list_workflows():
    """List all workflows"""
    engine = get_engine()
    return {"workflows": engine.list_workflows()}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow details"""
    engine = get_engine()
    workflow = engine.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
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
        "version": workflow.version,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at
    }


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, request: WorkflowUpdate):
    """Update workflow"""
    engine = get_engine()
    workflow = engine.update_workflow(
        workflow_id=workflow_id,
        name=request.name,
        description=request.description,
        nodes=request.nodes,
        edges=request.edges,
        variables=request.variables
    )
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        status=workflow.status.value,
        node_count=len(workflow.nodes),
        created_at=workflow.created_at,
        updated_at=workflow.updated_at
    )


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete workflow"""
    engine = get_engine()
    if engine.delete_workflow(workflow_id):
        return {"status": "deleted", "workflow_id": workflow_id}
    raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
async def execute_workflow(workflow_id: str, request: WorkflowExecute):
    """Execute a workflow"""
    try:
        engine = get_engine()
        
        ctx = await engine.execute_workflow(
            workflow_id=workflow_id,
            inputs=request.inputs,
            variables=request.variables
        )
        
        duration = None
        if ctx.start_time and ctx.end_time:
            duration = (ctx.end_time - ctx.start_time).total_seconds()
        
        return ExecutionResponse(
            execution_id=ctx.execution_id,
            workflow_id=ctx.workflow_id,
            status=ctx.status.value,
            outputs=ctx.node_outputs,
            logs=ctx.logs,
            error=ctx.error,
            duration=duration
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Workflow execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions/{execution_id}")
async def get_execution(workflow_id: str, execution_id: str):
    """Get execution details"""
    engine = get_engine()
    ctx = engine.get_execution(execution_id)
    
    if not ctx or ctx.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    duration = None
    if ctx.start_time and ctx.end_time:
        duration = (ctx.end_time - ctx.start_time).total_seconds()
    
    return {
        "execution_id": ctx.execution_id,
        "workflow_id": ctx.workflow_id,
        "status": ctx.status.value,
        "outputs": ctx.node_outputs,
        "variables": ctx.variables,
        "logs": ctx.logs,
        "current_node": ctx.current_node,
        "error": ctx.error,
        "duration": duration,
        "start_time": ctx.start_time.isoformat() if ctx.start_time else None,
        "end_time": ctx.end_time.isoformat() if ctx.end_time else None
    }


@router.post("/{workflow_id}/duplicate")
async def duplicate_workflow(workflow_id: str, new_name: Optional[str] = None):
    """Duplicate a workflow"""
    engine = get_engine()
    original = engine.get_workflow(workflow_id)
    
    if not original:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    name = new_name or f"{original.name} (Copy)"
    
    new_workflow = engine.create_workflow(
        name=name,
        description=original.description,
        nodes=[
            {
                "id": n.id,
                "type": n.type.value,
                "name": n.name,
                "config": n.config,
                "position": n.position,
                "inputs": n.inputs,
                "outputs": n.outputs
            }
            for n in original.nodes
        ],
        edges=[
            {
                "source_node": e.source_node,
                "source_port": e.source_port,
                "target_node": e.target_node,
                "target_port": e.target_port
            }
            for e in original.edges
        ]
    )
    new_workflow.variables = original.variables.copy()
    engine._save_workflow(new_workflow)
    
    return {
        "id": new_workflow.id,
        "name": new_workflow.name,
        "original_id": workflow_id
    }


# Workflow templates
WORKFLOW_TEMPLATES = [
    {
        "id": "chat_with_rag",
        "name": "Chat with RAG",
        "description": "Query documents and generate response",
        "nodes": [
            {"id": "start", "type": "start", "name": "Start", "position": {"x": 100, "y": 200}},
            {"id": "rag", "type": "rag_query", "name": "RAG Query", "position": {"x": 300, "y": 200}, "config": {"top_k": 5}},
            {"id": "llm", "type": "llm_chat", "name": "Generate Response", "position": {"x": 500, "y": 200}, "config": {"prompt": "Based on the following context, answer the question:\n\n{{context}}\n\nQuestion: {{query}}"}},
            {"id": "end", "type": "end", "name": "End", "position": {"x": 700, "y": 200}}
        ],
        "edges": [
            {"source_node": "start", "source_port": "output", "target_node": "rag", "target_port": "input"},
            {"source_node": "rag", "source_port": "output", "target_node": "llm", "target_port": "input"},
            {"source_node": "llm", "source_port": "output", "target_node": "end", "target_port": "input"}
        ]
    },
    {
        "id": "code_analysis",
        "name": "Code Analysis",
        "description": "Analyze code and generate report",
        "nodes": [
            {"id": "start", "type": "start", "name": "Start", "position": {"x": 100, "y": 200}},
            {"id": "analyze", "type": "llm_chat", "name": "Analyze Code", "position": {"x": 300, "y": 200}, "config": {"system": "You are a code reviewer. Analyze the code and list issues.", "prompt": "{{code}}"}},
            {"id": "format", "type": "template", "name": "Format Report", "position": {"x": 500, "y": 200}, "config": {"template": "# Code Analysis Report\n\n{{input}}"}},
            {"id": "end", "type": "end", "name": "End", "position": {"x": 700, "y": 200}}
        ],
        "edges": [
            {"source_node": "start", "source_port": "output", "target_node": "analyze", "target_port": "input"},
            {"source_node": "analyze", "source_port": "output", "target_node": "format", "target_port": "input"},
            {"source_node": "format", "source_port": "output", "target_node": "end", "target_port": "input"}
        ]
    },
    {
        "id": "summarize_chain",
        "name": "Summarize Chain",
        "description": "Multi-step summarization",
        "nodes": [
            {"id": "start", "type": "start", "name": "Start", "position": {"x": 100, "y": 200}},
            {"id": "summary1", "type": "llm_chat", "name": "Initial Summary", "position": {"x": 300, "y": 200}, "config": {"prompt": "Summarize this text in 3 paragraphs:\n\n{{input}}"}},
            {"id": "summary2", "type": "llm_chat", "name": "Refine Summary", "position": {"x": 500, "y": 200}, "config": {"prompt": "Make this summary more concise, keeping only key points:\n\n{{input}}"}},
            {"id": "end", "type": "end", "name": "End", "position": {"x": 700, "y": 200}}
        ],
        "edges": [
            {"source_node": "start", "source_port": "output", "target_node": "summary1", "target_port": "input"},
            {"source_node": "summary1", "source_port": "output", "target_node": "summary2", "target_port": "input"},
            {"source_node": "summary2", "source_port": "output", "target_node": "end", "target_port": "input"}
        ]
    }
]


@router.get("/templates/list")
async def list_templates():
    """Get workflow templates"""
    return {"templates": [
        {"id": t["id"], "name": t["name"], "description": t["description"]}
        for t in WORKFLOW_TEMPLATES
    ]}


@router.post("/templates/{template_id}/create")
async def create_from_template(template_id: str, name: Optional[str] = None):
    """Create workflow from template"""
    template = next((t for t in WORKFLOW_TEMPLATES if t["id"] == template_id), None)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    engine = get_engine()
    workflow = engine.create_workflow(
        name=name or template["name"],
        description=template["description"],
        nodes=template["nodes"],
        edges=template["edges"]
    )
    
    return {
        "id": workflow.id,
        "name": workflow.name,
        "template_id": template_id
    }


@router.websocket("/ws/{workflow_id}/execute")
async def execute_workflow_ws(websocket: WebSocket, workflow_id: str):
    """
    Execute workflow with real-time updates via WebSocket
    """
    await websocket.accept()
    
    try:
        engine = get_engine()
        workflow = engine.get_workflow(workflow_id)
        
        if not workflow:
            await websocket.send_json({"type": "error", "message": "Workflow not found"})
            await websocket.close()
            return
        
        # Receive execution parameters
        data = await websocket.receive_json()
        inputs = data.get("inputs", {})
        variables = data.get("variables", {})
        
        await websocket.send_json({"type": "started", "workflow_id": workflow_id})
        
        # Execute and stream updates
        ctx = await engine.execute_workflow(workflow_id, inputs, variables)
        
        # Send logs
        for log in ctx.logs:
            await websocket.send_json({"type": "log", "data": log})
        
        # Send final result
        duration = None
        if ctx.start_time and ctx.end_time:
            duration = (ctx.end_time - ctx.start_time).total_seconds()
        
        await websocket.send_json({
            "type": "completed",
            "status": ctx.status.value,
            "outputs": ctx.node_outputs,
            "error": ctx.error,
            "duration": duration
        })
        
    except WebSocketDisconnect:
        logger.info("Workflow WebSocket disconnected")
    except Exception as e:
        logger.error(f"Workflow WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
