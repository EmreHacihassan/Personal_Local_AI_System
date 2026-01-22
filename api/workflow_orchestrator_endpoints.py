"""
Advanced Workflow Orchestration API Endpoints
Premium visual workflow designer with node-based execution

Features:
- Visual workflow builder API
- Node management
- Real-time execution
- Workflow templates
- Version control
- Scheduling
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import asyncio
import json

router = APIRouter(prefix="/api/workflows", tags=["Advanced Workflow Orchestration"])


# =============================================================================
# MODELS
# =============================================================================

class NodePosition(BaseModel):
    x: float = 0
    y: float = 0


class NodeConfig(BaseModel):
    node_type: str = Field(..., description="Type of node")
    name: str = Field(..., description="Node display name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration")
    position: NodePosition = Field(default_factory=NodePosition)


class EdgeConfig(BaseModel):
    source_node: str = Field(..., description="Source node ID")
    source_port: str = Field(default="output", description="Source port name")
    target_node: str = Field(..., description="Target node ID")
    target_port: str = Field(default="input", description="Target port name")
    condition: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    nodes: List[NodeConfig] = Field(default_factory=list)
    edges: List[EdgeConfig] = Field(default_factory=list)
    category: str = Field(default="general")
    tags: List[str] = Field(default_factory=list)
    is_template: bool = False


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[NodeConfig]] = None
    edges: Optional[List[EdgeConfig]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class NodeCreate(BaseModel):
    workflow_id: str
    node_type: str
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    position: NodePosition = Field(default_factory=NodePosition)


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    position: Optional[NodePosition] = None


class ExecutionRequest(BaseModel):
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Initial input values")
    options: Dict[str, Any] = Field(default_factory=dict, description="Execution options")


class ScheduleConfig(BaseModel):
    schedule_type: str = Field(..., description="Type: once, interval, cron")
    value: str = Field(..., description="Schedule value (ISO datetime, seconds, or cron expression)")
    enabled: bool = True
    max_runs: Optional[int] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)


class TriggerConfig(BaseModel):
    trigger_type: str = Field(..., description="Type: webhook, file_change, event")
    config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


# =============================================================================
# WORKFLOW CRUD ENDPOINTS
# =============================================================================

@router.post("", summary="Create workflow")
async def create_workflow(workflow: WorkflowCreate):
    """Create a new workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.create_workflow(
            name=workflow.name,
            description=workflow.description,
            nodes=workflow.nodes,
            edges=workflow.edges,
            category=workflow.category,
            tags=workflow.tags,
            is_template=workflow.is_template
        )
        
        return {
            "success": True,
            "workflow": result.to_dict(),
            "message": "Workflow created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", summary="List workflows")
async def list_workflows(
    category: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    is_template: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List workflows with optional filters"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        tag_list = tags.split(",") if tags else None
        
        workflows = workflow_orchestrator.list_workflows(
            category=category,
            status=status,
            tags=tag_list,
            search=search,
            is_template=is_template,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "count": len(workflows),
            "workflows": [w.to_dict() for w in workflows]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates", summary="List workflow templates")
async def list_templates(category: Optional[str] = None):
    """List available workflow templates"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        templates = workflow_orchestrator.get_templates(category)
        
        return {
            "success": True,
            "count": len(templates),
            "templates": templates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}", summary="Get workflow")
async def get_workflow(workflow_id: str):
    """Get workflow by ID"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        workflow = workflow_orchestrator.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow": workflow.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{workflow_id}", summary="Update workflow")
async def update_workflow(workflow_id: str, updates: WorkflowUpdate):
    """Update workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.update_workflow(
            workflow_id=workflow_id,
            updates=updates.dict(exclude_none=True)
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow": result.to_dict(),
            "message": "Workflow updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}", summary="Delete workflow")
async def delete_workflow(workflow_id: str):
    """Delete workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        success = await workflow_orchestrator.delete_workflow(workflow_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "message": "Workflow deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/duplicate", summary="Duplicate workflow")
async def duplicate_workflow(workflow_id: str, new_name: Optional[str] = None):
    """Duplicate an existing workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.duplicate_workflow(workflow_id, new_name)
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "workflow": result.to_dict(),
            "message": "Workflow duplicated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-template/{template_id}", summary="Create from template")
async def create_from_template(template_id: str, name: str, customizations: Optional[Dict[str, Any]] = None):
    """Create a workflow from a template"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.create_from_template(
            template_id=template_id,
            name=name,
            customizations=customizations or {}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "workflow": result.to_dict(),
            "message": "Workflow created from template"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NODE MANAGEMENT
# =============================================================================

@router.get("/nodes/types", summary="Get available node types")
async def get_node_types():
    """Get all available node types with their schemas"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        node_types = workflow_orchestrator.get_node_types()
        
        return {
            "success": True,
            "node_types": node_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/nodes", summary="Add node to workflow")
async def add_node(workflow_id: str, node: NodeCreate):
    """Add a node to a workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.add_node(
            workflow_id=workflow_id,
            node_type=node.node_type,
            name=node.name,
            config=node.config,
            position={"x": node.position.x, "y": node.position.y}
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "node": result,
            "message": "Node added"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{workflow_id}/nodes/{node_id}", summary="Update node")
async def update_node(workflow_id: str, node_id: str, updates: NodeUpdate):
    """Update a node in a workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        update_dict = updates.dict(exclude_none=True)
        if "position" in update_dict:
            update_dict["position"] = {"x": updates.position.x, "y": updates.position.y}
        
        result = await workflow_orchestrator.update_node(
            workflow_id=workflow_id,
            node_id=node_id,
            updates=update_dict
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow or node not found")
        
        return {
            "success": True,
            "node": result,
            "message": "Node updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}/nodes/{node_id}", summary="Delete node")
async def delete_node(workflow_id: str, node_id: str):
    """Delete a node from a workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        success = await workflow_orchestrator.delete_node(workflow_id, node_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow or node not found")
        
        return {
            "success": True,
            "message": "Node deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/edges", summary="Add edge")
async def add_edge(workflow_id: str, edge: EdgeConfig):
    """Add an edge between nodes"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.add_edge(
            workflow_id=workflow_id,
            source_node=edge.source_node,
            source_port=edge.source_port,
            target_node=edge.target_node,
            target_port=edge.target_port,
            condition=edge.condition
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow or nodes not found")
        
        return {
            "success": True,
            "edge": result,
            "message": "Edge added"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}/edges/{edge_id}", summary="Delete edge")
async def delete_edge(workflow_id: str, edge_id: str):
    """Delete an edge from a workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        success = await workflow_orchestrator.delete_edge(workflow_id, edge_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow or edge not found")
        
        return {
            "success": True,
            "message": "Edge deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXECUTION
# =============================================================================

@router.post("/{workflow_id}/execute", summary="Execute workflow")
async def execute_workflow(
    workflow_id: str,
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    async_execution: bool = Query(False)
):
    """Execute a workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        if async_execution:
            execution_id = await workflow_orchestrator.start_async_execution(
                workflow_id=workflow_id,
                inputs=request.inputs,
                options=request.options
            )
            
            return {
                "success": True,
                "execution_id": execution_id,
                "status": "started",
                "message": "Workflow execution started"
            }
        
        result = await workflow_orchestrator.execute_workflow(
            workflow_id=workflow_id,
            inputs=request.inputs,
            options=request.options
        )
        
        return {
            "success": True,
            "execution": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions", summary="List executions")
async def list_executions(
    workflow_id: str,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """List workflow executions"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        executions = workflow_orchestrator.list_executions(
            workflow_id=workflow_id,
            status=status,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(executions),
            "executions": executions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executions/{execution_id}", summary="Get execution status")
async def get_execution(execution_id: str):
    """Get execution status and results"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        execution = workflow_orchestrator.get_execution(execution_id)
        
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "success": True,
            "execution": execution
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/cancel", summary="Cancel execution")
async def cancel_execution(execution_id: str):
    """Cancel a running execution"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        success = await workflow_orchestrator.cancel_execution(execution_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Execution not found or already completed")
        
        return {
            "success": True,
            "message": "Execution cancelled"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executions/{execution_id}/retry", summary="Retry failed execution")
async def retry_execution(execution_id: str, from_failed_node: bool = True):
    """Retry a failed execution"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.retry_execution(
            execution_id=execution_id,
            from_failed_node=from_failed_node
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return {
            "success": True,
            "new_execution_id": result["execution_id"],
            "message": "Execution retried"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SCHEDULING & TRIGGERS
# =============================================================================

@router.post("/{workflow_id}/schedule", summary="Schedule workflow")
async def schedule_workflow(workflow_id: str, schedule: ScheduleConfig):
    """Schedule a workflow for automatic execution"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.schedule_workflow(
            workflow_id=workflow_id,
            schedule_type=schedule.schedule_type,
            value=schedule.value,
            enabled=schedule.enabled,
            max_runs=schedule.max_runs,
            inputs=schedule.inputs
        )
        
        return {
            "success": True,
            "schedule": result,
            "message": "Workflow scheduled"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/schedules", summary="List schedules")
async def list_schedules(workflow_id: str):
    """List workflow schedules"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        schedules = workflow_orchestrator.list_schedules(workflow_id)
        
        return {
            "success": True,
            "schedules": schedules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}/schedules/{schedule_id}", summary="Delete schedule")
async def delete_schedule(workflow_id: str, schedule_id: str):
    """Delete a workflow schedule"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        success = await workflow_orchestrator.delete_schedule(workflow_id, schedule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        return {
            "success": True,
            "message": "Schedule deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/triggers", summary="Add trigger")
async def add_trigger(workflow_id: str, trigger: TriggerConfig):
    """Add a trigger to a workflow"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.add_trigger(
            workflow_id=workflow_id,
            trigger_type=trigger.trigger_type,
            config=trigger.config,
            enabled=trigger.enabled
        )
        
        return {
            "success": True,
            "trigger": result,
            "message": "Trigger added"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VERSION CONTROL
# =============================================================================

@router.get("/{workflow_id}/versions", summary="List versions")
async def list_versions(workflow_id: str):
    """List workflow versions"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        versions = workflow_orchestrator.list_versions(workflow_id)
        
        return {
            "success": True,
            "versions": versions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/versions", summary="Create version snapshot")
async def create_version(workflow_id: str, changelog: str = ""):
    """Create a version snapshot"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.create_version(workflow_id, changelog)
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "version": result,
            "message": "Version created"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/rollback/{version}", summary="Rollback to version")
async def rollback_version(workflow_id: str, version: str):
    """Rollback workflow to a specific version"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.rollback_to_version(workflow_id, version)
        
        if not result:
            raise HTTPException(status_code=404, detail="Workflow or version not found")
        
        return {
            "success": True,
            "workflow": result.to_dict(),
            "message": f"Rolled back to version {version}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/diff/{version1}/{version2}", summary="Diff versions")
async def diff_versions(workflow_id: str, version1: str, version2: str):
    """Get diff between two versions"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        diff = workflow_orchestrator.diff_versions(workflow_id, version1, version2)
        
        if not diff:
            raise HTTPException(status_code=404, detail="Workflow or versions not found")
        
        return {
            "success": True,
            "diff": diff
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# IMPORT/EXPORT
# =============================================================================

@router.get("/{workflow_id}/export", summary="Export workflow")
async def export_workflow(workflow_id: str, include_history: bool = False):
    """Export workflow as JSON"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        export_data = await workflow_orchestrator.export_workflow(
            workflow_id=workflow_id,
            include_history=include_history
        )
        
        if not export_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return export_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", summary="Import workflow")
async def import_workflow(workflow_data: Dict[str, Any]):
    """Import a workflow from JSON"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.import_workflow(workflow_data)
        
        return {
            "success": True,
            "workflow": result.to_dict(),
            "message": "Workflow imported"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ANALYTICS
# =============================================================================

@router.get("/{workflow_id}/analytics", summary="Get workflow analytics")
async def get_analytics(
    workflow_id: str,
    period: str = Query("week", pattern="^(day|week|month|all)$")
):
    """Get workflow analytics and performance metrics"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        analytics = workflow_orchestrator.get_analytics(workflow_id, period)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "success": True,
            "analytics": analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get overall workflow statistics")
async def get_stats():
    """Get overall workflow system statistics"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        stats = workflow_orchestrator.get_system_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VALIDATION
# =============================================================================

@router.post("/{workflow_id}/validate", summary="Validate workflow")
async def validate_workflow(workflow_id: str):
    """Validate workflow configuration"""
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        result = await workflow_orchestrator.validate_workflow(workflow_id)
        
        return {
            "success": True,
            "is_valid": result["is_valid"],
            "errors": result.get("errors", []),
            "warnings": result.get("warnings", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WEBSOCKET FOR REAL-TIME EXECUTION
# =============================================================================

@router.websocket("/ws/execute/{workflow_id}")
async def websocket_execute(websocket: WebSocket, workflow_id: str):
    """WebSocket for real-time workflow execution updates"""
    await websocket.accept()
    
    try:
        from core.workflow_orchestrator import workflow_orchestrator
        
        # Receive initial inputs
        data = await websocket.receive_json()
        inputs = data.get("inputs", {})
        options = data.get("options", {})
        
        # Start execution with progress callback
        async def progress_callback(update):
            try:
                await websocket.send_json(update)
            except:
                pass
        
        execution_id = await workflow_orchestrator.execute_with_streaming(
            workflow_id=workflow_id,
            inputs=inputs,
            options=options,
            progress_callback=progress_callback
        )
        
        # Wait for completion or cancellation
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                if msg.get("action") == "cancel":
                    await workflow_orchestrator.cancel_execution(execution_id)
                    await websocket.send_json({"type": "cancelled", "execution_id": execution_id})
                    break
            except asyncio.TimeoutError:
                # Check if execution is complete
                execution = workflow_orchestrator.get_execution(execution_id)
                if execution and execution["status"] in ["completed", "failed", "cancelled"]:
                    await websocket.send_json({
                        "type": "completed",
                        "execution": execution
                    })
                    break
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
