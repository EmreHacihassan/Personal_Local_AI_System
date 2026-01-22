"""
Agent Marketplace API Endpoints
Premium agent builder, templates, teams, and marketplace

Features:
- Custom agent builder
- Agent templates
- Multi-agent teams
- Performance analytics
- Import/export agents
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import json

router = APIRouter(prefix="/api/agents", tags=["Agent Marketplace"])


# =============================================================================
# MODELS
# =============================================================================

class AgentBehaviorConfig(BaseModel):
    personality: str = Field(default="professional", description="Agent personality type")
    creativity: float = Field(default=0.5, ge=0, le=1)
    verbosity: float = Field(default=0.5, ge=0, le=1)
    risk_tolerance: float = Field(default=0.3, ge=0, le=1)
    autonomy_level: float = Field(default=0.5, ge=0, le=1)
    use_markdown: bool = True
    include_reasoning: bool = True
    include_sources: bool = True
    primary_language: str = "auto"
    response_length: str = "adaptive"
    custom_instructions: str = ""
    avoid_topics: List[str] = Field(default_factory=list)


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    role: str = Field(..., description="Agent role: researcher, coder, writer, analyst, etc.")
    icon: str = Field(default="🤖")
    color: str = Field(default="#3B82F6")
    template_id: Optional[str] = None
    
    # Configuration
    behavior: Optional[AgentBehaviorConfig] = None
    capabilities: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    
    # LLM settings
    preferred_model: str = "auto"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, ge=100, le=32000)
    
    # System prompt
    system_prompt_base: str = ""
    system_prompt_additions: List[str] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    category: str = "custom"


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    behavior: Optional[AgentBehaviorConfig] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    preferred_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt_base: Optional[str] = None
    system_prompt_additions: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    status: Optional[str] = None


class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    agent_ids: List[str] = Field(..., min_items=1)
    strategy: str = Field(default="sequential", description="Execution strategy")
    manager_agent_id: Optional[str] = None
    max_rounds: int = Field(default=5, ge=1, le=20)
    consensus_threshold: float = Field(default=0.7, ge=0.5, le=1)
    parallel_limit: int = Field(default=3, ge=1, le=10)
    timeout_per_agent: int = Field(default=60, ge=10, le=300)
    aggregate_outputs: bool = True


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    agent_ids: Optional[List[str]] = None
    strategy: Optional[str] = None
    manager_agent_id: Optional[str] = None
    max_rounds: Optional[int] = None
    consensus_threshold: Optional[float] = None
    parallel_limit: Optional[int] = None
    timeout_per_agent: Optional[int] = None
    aggregate_outputs: Optional[bool] = None


class AgentRunRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Task to perform")
    context: Dict[str, Any] = Field(default_factory=dict)
    stream: bool = False


class TeamRunRequest(BaseModel):
    task: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# AGENT CRUD
# =============================================================================

@router.post("", summary="Create agent")
async def create_agent(agent: AgentCreate):
    """Create a new custom agent"""
    try:
        from core.agent_marketplace import agent_marketplace, AgentRole
        
        behavior_dict = agent.behavior.dict() if agent.behavior else {}
        
        result = await agent_marketplace.create_agent(
            name=agent.name,
            description=agent.description,
            role=AgentRole(agent.role),
            template_id=agent.template_id,
            icon=agent.icon,
            color=agent.color,
            behavior=behavior_dict,
            capabilities=agent.capabilities,
            tools=agent.tools,
            preferred_model=agent.preferred_model,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt_base=agent.system_prompt_base,
            system_prompt_additions=agent.system_prompt_additions,
            tags=agent.tags,
            category=agent.category
        )
        
        return {
            "success": True,
            "agent": result.to_dict(),
            "message": "Agent created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", summary="List agents")
async def list_agents(
    role: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List agents with optional filters"""
    try:
        from core.agent_marketplace import agent_marketplace, AgentRole, AgentStatus
        
        role_enum = AgentRole(role) if role else None
        status_enum = AgentStatus(status) if status else None
        tag_list = tags.split(",") if tags else None
        
        agents = agent_marketplace.list_agents(
            role=role_enum,
            category=category,
            status=status_enum,
            tags=tag_list
        )
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            agents = [a for a in agents if search_lower in a.name.lower() or search_lower in a.description.lower()]
        
        # Apply pagination
        agents = agents[offset:offset + limit]
        
        return {
            "success": True,
            "count": len(agents),
            "agents": [a.to_dict() for a in agents]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", summary="Get agent")
async def get_agent(agent_id: str):
    """Get agent by ID"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        agent = agent_marketplace.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "agent": agent.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{agent_id}", summary="Update agent")
async def update_agent(agent_id: str, updates: AgentUpdate):
    """Update agent"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        update_dict = updates.dict(exclude_none=True)
        if "behavior" in update_dict and update_dict["behavior"]:
            update_dict["behavior"] = update_dict["behavior"]
        
        result = await agent_marketplace.update_agent(agent_id, update_dict)
        
        if not result:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "agent": result.to_dict(),
            "message": "Agent updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}", summary="Delete agent")
async def delete_agent(agent_id: str):
    """Delete agent"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        success = await agent_marketplace.delete_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "message": "Agent deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/duplicate", summary="Duplicate agent")
async def duplicate_agent(agent_id: str, new_name: Optional[str] = None):
    """Duplicate an existing agent"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        original = agent_marketplace.get_agent(agent_id)
        if not original:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Create new agent with same config
        config = original.to_dict()
        config.pop("id")
        config["name"] = new_name or f"{original.name} (Copy)"
        
        result = await agent_marketplace.create_agent(
            name=config["name"],
            description=config["description"],
            role=config["role"],
            **config
        )
        
        return {
            "success": True,
            "agent": result.to_dict(),
            "message": "Agent duplicated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AGENT EXECUTION
# =============================================================================

@router.post("/{agent_id}/run", summary="Run agent")
async def run_agent(agent_id: str, request: AgentRunRequest):
    """Execute a task with an agent"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        agent = agent_marketplace.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        result = await agent_marketplace._run_agent(
            agent=agent,
            task=request.task,
            context=request.context
        )
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/system-prompt", summary="Get system prompt")
async def get_system_prompt(agent_id: str):
    """Get the generated system prompt for an agent"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        agent = agent_marketplace.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        system_prompt = agent.generate_system_prompt()
        
        return {
            "success": True,
            "agent_id": agent_id,
            "system_prompt": system_prompt
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/rate", summary="Rate agent")
async def rate_agent(agent_id: str, rating: float = Query(..., ge=1, le=5)):
    """Rate an agent (1-5 stars)"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        success = await agent_marketplace.rate_agent(agent_id, rating)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "message": f"Rated {rating} stars"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TEMPLATES
# =============================================================================

@router.get("/templates", summary="List templates")
async def list_templates(
    category: Optional[str] = None,
    role: Optional[str] = None
):
    """List available agent templates"""
    try:
        from core.agent_marketplace import agent_marketplace, AgentRole
        
        role_enum = AgentRole(role) if role else None
        
        templates = agent_marketplace.list_templates(
            category=category,
            role=role_enum
        )
        
        return {
            "success": True,
            "count": len(templates),
            "templates": [t.to_dict() for t in templates]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}", summary="Get template")
async def get_template(template_id: str):
    """Get template details"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        template = agent_marketplace.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "template": template.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/templates/{template_id}/create", summary="Create from template")
async def create_from_template(
    template_id: str,
    name: str = Query(..., min_length=1),
    customizations: Optional[Dict[str, Any]] = None
):
    """Create an agent from a template"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        result = await agent_marketplace.create_from_template(
            template_id=template_id,
            name=name,
            customizations=customizations
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "success": True,
            "agent": result.to_dict(),
            "message": "Agent created from template"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# TEAMS
# =============================================================================

@router.post("/teams", summary="Create team")
async def create_team(team: TeamCreate):
    """Create a multi-agent team"""
    try:
        from core.agent_marketplace import agent_marketplace, TeamStrategy
        
        result = await agent_marketplace.create_team(
            name=team.name,
            description=team.description,
            agent_ids=team.agent_ids,
            strategy=TeamStrategy(team.strategy),
            manager_agent_id=team.manager_agent_id,
            max_rounds=team.max_rounds,
            consensus_threshold=team.consensus_threshold,
            parallel_limit=team.parallel_limit,
            timeout_per_agent=team.timeout_per_agent,
            aggregate_outputs=team.aggregate_outputs
        )
        
        return {
            "success": True,
            "team": result.to_dict(),
            "message": "Team created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams", summary="List teams")
async def list_teams():
    """List all teams"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        teams = agent_marketplace.list_teams()
        
        return {
            "success": True,
            "count": len(teams),
            "teams": [t.to_dict() for t in teams]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}", summary="Get team")
async def get_team(team_id: str):
    """Get team details"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        team = agent_marketplace.get_team(team_id)
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Include agent details
        agents = []
        for aid in team.agents:
            agent = agent_marketplace.get_agent(aid)
            if agent:
                agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "role": agent.role.value,
                    "icon": agent.icon
                })
        
        team_dict = team.to_dict()
        team_dict["agent_details"] = agents
        
        return {
            "success": True,
            "team": team_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/run", summary="Run team")
async def run_team(team_id: str, request: TeamRunRequest):
    """Execute a task with a team of agents"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        result = await agent_marketplace.execute_team(
            team_id=team_id,
            task=request.task,
            context=request.context
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "result": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/{team_id}", summary="Delete team")
async def delete_team(team_id: str):
    """Delete a team"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        team = agent_marketplace.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Remove from storage
        del agent_marketplace.teams[team_id]
        
        return {
            "success": True,
            "message": "Team deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# IMPORT/EXPORT
# =============================================================================

@router.get("/{agent_id}/export", summary="Export agent")
async def export_agent(agent_id: str):
    """Export agent as .agent file"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        file_path = await agent_marketplace.export_agent(agent_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.split("/")[-1].split("\\")[-1],
            media_type="application/zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", summary="Import agent")
async def import_agent(file: UploadFile = File(...)):
    """Import agent from .agent file"""
    try:
        from core.agent_marketplace import agent_marketplace
        import tempfile
        
        # Save uploaded file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".agent") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        result = await agent_marketplace.import_agent(tmp_path)
        
        # Clean up
        import os
        os.unlink(tmp_path)
        
        if not result:
            raise HTTPException(status_code=400, detail="Invalid agent file")
        
        return {
            "success": True,
            "agent": result.to_dict(),
            "message": "Agent imported"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team_id}/export", summary="Export team")
async def export_team(team_id: str):
    """Export team with all agents"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        file_path = await agent_marketplace.export_team(team_id)
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Team not found")
        
        return FileResponse(
            path=file_path,
            filename=file_path.split("/")[-1].split("\\")[-1],
            media_type="application/zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ANALYTICS
# =============================================================================

@router.get("/{agent_id}/analytics", summary="Get agent analytics")
async def get_agent_analytics(agent_id: str):
    """Get detailed analytics for an agent"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        analytics = agent_marketplace.get_agent_analytics(agent_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "analytics": analytics
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marketplace/stats", summary="Get marketplace statistics")
async def get_marketplace_stats():
    """Get overall marketplace statistics"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        stats = agent_marketplace.get_marketplace_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CONFIGURATION
# =============================================================================

@router.get("/config/tools", summary="Get available tools")
async def get_available_tools():
    """Get list of available tools for agents"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        tools = agent_marketplace.get_available_tools()
        
        return {
            "success": True,
            "tools": tools
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/capabilities", summary="Get available capabilities")
async def get_available_capabilities():
    """Get list of available capabilities for agents"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        capabilities = agent_marketplace.get_available_capabilities()
        
        return {
            "success": True,
            "capabilities": capabilities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/roles", summary="Get role descriptions")
async def get_role_descriptions():
    """Get descriptions for all agent roles"""
    try:
        from core.agent_marketplace import agent_marketplace
        
        roles = agent_marketplace.get_role_descriptions()
        
        return {
            "success": True,
            "roles": roles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/personalities", summary="Get personality types")
async def get_personality_types():
    """Get available personality types"""
    from core.agent_marketplace import AgentPersonality
    
    return {
        "success": True,
        "personalities": [
            {"value": p.value, "label": p.value.title()}
            for p in AgentPersonality
        ]
    }


@router.get("/config/strategies", summary="Get team strategies")
async def get_team_strategies():
    """Get available team execution strategies"""
    from core.agent_marketplace import TeamStrategy
    
    descriptions = {
        "sequential": "Agents execute one after another, each seeing previous results",
        "parallel": "All agents execute simultaneously",
        "hierarchical": "Manager agent delegates tasks to worker agents",
        "consensus": "Agents vote and reach consensus on answers",
        "debate": "Agents debate and critique each other's responses",
        "pipeline": "Each agent transforms the output of the previous"
    }
    
    return {
        "success": True,
        "strategies": [
            {"value": s.value, "label": s.value.title(), "description": descriptions.get(s.value, "")}
            for s in TeamStrategy
        ]
    }
