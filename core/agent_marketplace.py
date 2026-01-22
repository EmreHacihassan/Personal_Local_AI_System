"""
Agent Marketplace & Custom Agent Builder
=========================================

Premium no-code agent builder, agent templates, multi-agent teams,
performance analytics, and agent import/export.

100% Local Execution - All agents run locally with full privacy.

Features:
- No-code visual agent builder
- Agent templates library
- Multi-agent team composition
- Agent performance analytics
- Custom tool integration
- Agent import/export (.agent files)
- Role-based agent behaviors
- Agent versioning and rollback
- Agent marketplace (local sharing)
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import time
import uuid
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import base64

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class AgentRole(str, Enum):
    """Predefined agent roles with specialized behaviors"""
    GENERAL = "general"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    CODER = "coder"
    PLANNER = "planner"
    CRITIC = "critic"
    SUMMARIZER = "summarizer"
    TRANSLATOR = "translator"
    TEACHER = "teacher"
    DEBUGGER = "debugger"
    ARCHITECT = "architect"
    REVIEWER = "reviewer"
    CREATIVE = "creative"
    CUSTOM = "custom"


class AgentPersonality(str, Enum):
    """Agent personality traits affecting response style"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CONCISE = "concise"
    DETAILED = "detailed"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CAUTIOUS = "cautious"
    BOLD = "bold"
    HUMOROUS = "humorous"
    FORMAL = "formal"


class SkillLevel(str, Enum):
    """Agent skill level"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AgentStatus(str, Enum):
    """Agent status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class TeamStrategy(str, Enum):
    """Multi-agent team execution strategy"""
    SEQUENTIAL = "sequential"      # One after another
    PARALLEL = "parallel"          # All at once
    HIERARCHICAL = "hierarchical"  # Manager delegates
    CONSENSUS = "consensus"        # Vote on decisions
    DEBATE = "debate"              # Adversarial discussion
    PIPELINE = "pipeline"          # Each agent transforms output


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AgentCapability:
    """A capability/skill that an agent has"""
    id: str
    name: str
    description: str
    category: str  # reasoning, coding, research, writing, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_tools: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class AgentTool:
    """A tool that an agent can use"""
    id: str
    name: str
    description: str
    category: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    is_async: bool = False
    requires_approval: bool = False
    enabled: bool = True


@dataclass
class AgentMemoryConfig:
    """Memory configuration for an agent"""
    enable_short_term: bool = True
    enable_long_term: bool = True
    enable_episodic: bool = True
    short_term_capacity: int = 50
    long_term_capacity: int = 1000
    memory_decay_rate: float = 0.1
    consolidation_threshold: float = 0.7


@dataclass
class AgentBehavior:
    """Behavioral configuration for an agent"""
    personality: AgentPersonality = AgentPersonality.PROFESSIONAL
    creativity: float = 0.5  # 0.0 - 1.0
    verbosity: float = 0.5   # 0.0 - 1.0 (concise to detailed)
    risk_tolerance: float = 0.3  # 0.0 - 1.0
    autonomy_level: float = 0.5  # 0.0 - 1.0 (asks permission vs acts)
    
    # Response style
    use_markdown: bool = True
    include_reasoning: bool = True
    include_sources: bool = True
    
    # Language settings
    primary_language: str = "auto"
    response_length: str = "adaptive"  # short, medium, long, adaptive
    
    # Custom instructions
    custom_instructions: str = ""
    
    # Constraints
    avoid_topics: List[str] = field(default_factory=list)
    required_disclaimers: List[str] = field(default_factory=list)


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for an agent"""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    average_response_time: float = 0.0
    average_token_usage: int = 0
    user_ratings: List[float] = field(default_factory=list)
    average_rating: float = 0.0
    last_used: Optional[str] = None
    total_tokens_used: int = 0
    error_rate: float = 0.0
    
    # Detailed metrics
    capability_usage: Dict[str, int] = field(default_factory=dict)
    tool_usage: Dict[str, int] = field(default_factory=dict)
    response_times: List[float] = field(default_factory=list)


@dataclass
class AgentVersion:
    """Version information for an agent"""
    version: str
    created_at: str
    changelog: str
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    is_current: bool = False


@dataclass
class CustomAgent:
    """A custom agent definition"""
    id: str
    name: str
    description: str
    role: AgentRole
    icon: str = "🤖"
    color: str = "#3B82F6"
    
    # Configuration
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[AgentTool] = field(default_factory=list)
    behavior: AgentBehavior = field(default_factory=AgentBehavior)
    memory_config: AgentMemoryConfig = field(default_factory=AgentMemoryConfig)
    
    # System prompt components
    system_prompt_base: str = ""
    system_prompt_additions: List[str] = field(default_factory=list)
    example_conversations: List[Dict] = field(default_factory=list)
    
    # LLM settings
    preferred_model: str = "auto"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    
    # Metadata
    author: str = "local"
    status: AgentStatus = AgentStatus.ACTIVE
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    
    # Version control
    version: str = "1.0.0"
    versions: List[AgentVersion] = field(default_factory=list)
    
    # Performance tracking
    metrics: AgentPerformanceMetrics = field(default_factory=AgentPerformanceMetrics)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role": self.role.value if isinstance(self.role, AgentRole) else self.role,
            "icon": self.icon,
            "color": self.color,
            "capabilities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "category": c.category,
                    "parameters": c.parameters,
                    "required_tools": c.required_tools,
                    "examples": c.examples
                } for c in self.capabilities
            ],
            "tools": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "input_schema": t.input_schema,
                    "output_schema": t.output_schema,
                    "is_async": t.is_async,
                    "requires_approval": t.requires_approval,
                    "enabled": t.enabled
                } for t in self.tools
            ],
            "behavior": {
                "personality": self.behavior.personality.value if isinstance(self.behavior.personality, AgentPersonality) else self.behavior.personality,
                "creativity": self.behavior.creativity,
                "verbosity": self.behavior.verbosity,
                "risk_tolerance": self.behavior.risk_tolerance,
                "autonomy_level": self.behavior.autonomy_level,
                "use_markdown": self.behavior.use_markdown,
                "include_reasoning": self.behavior.include_reasoning,
                "include_sources": self.behavior.include_sources,
                "primary_language": self.behavior.primary_language,
                "response_length": self.behavior.response_length,
                "custom_instructions": self.behavior.custom_instructions,
                "avoid_topics": self.behavior.avoid_topics,
                "required_disclaimers": self.behavior.required_disclaimers
            },
            "memory_config": {
                "enable_short_term": self.memory_config.enable_short_term,
                "enable_long_term": self.memory_config.enable_long_term,
                "enable_episodic": self.memory_config.enable_episodic,
                "short_term_capacity": self.memory_config.short_term_capacity,
                "long_term_capacity": self.memory_config.long_term_capacity,
                "memory_decay_rate": self.memory_config.memory_decay_rate,
                "consolidation_threshold": self.memory_config.consolidation_threshold
            },
            "system_prompt_base": self.system_prompt_base,
            "system_prompt_additions": self.system_prompt_additions,
            "example_conversations": self.example_conversations,
            "preferred_model": self.preferred_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "author": self.author,
            "status": self.status.value if isinstance(self.status, AgentStatus) else self.status,
            "tags": self.tags,
            "category": self.category,
            "version": self.version,
            "metrics": {
                "total_runs": self.metrics.total_runs,
                "successful_runs": self.metrics.successful_runs,
                "failed_runs": self.metrics.failed_runs,
                "average_response_time": self.metrics.average_response_time,
                "average_token_usage": self.metrics.average_token_usage,
                "average_rating": self.metrics.average_rating,
                "last_used": self.metrics.last_used,
                "total_tokens_used": self.metrics.total_tokens_used,
                "error_rate": self.metrics.error_rate
            },
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomAgent':
        """Create from dictionary"""
        # Parse capabilities
        capabilities = []
        for c in data.get("capabilities", []):
            capabilities.append(AgentCapability(
                id=c.get("id", str(uuid.uuid4())[:8]),
                name=c.get("name", ""),
                description=c.get("description", ""),
                category=c.get("category", "general"),
                parameters=c.get("parameters", {}),
                required_tools=c.get("required_tools", []),
                examples=c.get("examples", [])
            ))
        
        # Parse tools
        tools = []
        for t in data.get("tools", []):
            tools.append(AgentTool(
                id=t.get("id", str(uuid.uuid4())[:8]),
                name=t.get("name", ""),
                description=t.get("description", ""),
                category=t.get("category", "general"),
                input_schema=t.get("input_schema", {}),
                output_schema=t.get("output_schema", {}),
                is_async=t.get("is_async", False),
                requires_approval=t.get("requires_approval", False),
                enabled=t.get("enabled", True)
            ))
        
        # Parse behavior
        behavior_data = data.get("behavior", {})
        behavior = AgentBehavior(
            personality=AgentPersonality(behavior_data.get("personality", "professional")),
            creativity=behavior_data.get("creativity", 0.5),
            verbosity=behavior_data.get("verbosity", 0.5),
            risk_tolerance=behavior_data.get("risk_tolerance", 0.3),
            autonomy_level=behavior_data.get("autonomy_level", 0.5),
            use_markdown=behavior_data.get("use_markdown", True),
            include_reasoning=behavior_data.get("include_reasoning", True),
            include_sources=behavior_data.get("include_sources", True),
            primary_language=behavior_data.get("primary_language", "auto"),
            response_length=behavior_data.get("response_length", "adaptive"),
            custom_instructions=behavior_data.get("custom_instructions", ""),
            avoid_topics=behavior_data.get("avoid_topics", []),
            required_disclaimers=behavior_data.get("required_disclaimers", [])
        )
        
        # Parse memory config
        memory_data = data.get("memory_config", {})
        memory_config = AgentMemoryConfig(
            enable_short_term=memory_data.get("enable_short_term", True),
            enable_long_term=memory_data.get("enable_long_term", True),
            enable_episodic=memory_data.get("enable_episodic", True),
            short_term_capacity=memory_data.get("short_term_capacity", 50),
            long_term_capacity=memory_data.get("long_term_capacity", 1000),
            memory_decay_rate=memory_data.get("memory_decay_rate", 0.1),
            consolidation_threshold=memory_data.get("consolidation_threshold", 0.7)
        )
        
        # Parse metrics
        metrics_data = data.get("metrics", {})
        metrics = AgentPerformanceMetrics(
            total_runs=metrics_data.get("total_runs", 0),
            successful_runs=metrics_data.get("successful_runs", 0),
            failed_runs=metrics_data.get("failed_runs", 0),
            average_response_time=metrics_data.get("average_response_time", 0.0),
            average_token_usage=metrics_data.get("average_token_usage", 0),
            average_rating=metrics_data.get("average_rating", 0.0),
            last_used=metrics_data.get("last_used"),
            total_tokens_used=metrics_data.get("total_tokens_used", 0),
            error_rate=metrics_data.get("error_rate", 0.0)
        )
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Unnamed Agent"),
            description=data.get("description", ""),
            role=AgentRole(data.get("role", "general")),
            icon=data.get("icon", "🤖"),
            color=data.get("color", "#3B82F6"),
            capabilities=capabilities,
            tools=tools,
            behavior=behavior,
            memory_config=memory_config,
            system_prompt_base=data.get("system_prompt_base", ""),
            system_prompt_additions=data.get("system_prompt_additions", []),
            example_conversations=data.get("example_conversations", []),
            preferred_model=data.get("preferred_model", "auto"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            top_p=data.get("top_p", 0.9),
            author=data.get("author", "local"),
            status=AgentStatus(data.get("status", "active")),
            tags=data.get("tags", []),
            category=data.get("category", "general"),
            version=data.get("version", "1.0.0"),
            metrics=metrics,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )
    
    def generate_system_prompt(self) -> str:
        """Generate the full system prompt for this agent"""
        parts = []
        
        # Role and identity
        parts.append(f"You are {self.name}, a {self.role.value} AI assistant.")
        parts.append(f"Description: {self.description}")
        
        # Personality
        personality_desc = {
            AgentPersonality.PROFESSIONAL: "You communicate in a professional and business-like manner.",
            AgentPersonality.FRIENDLY: "You are warm, approachable, and conversational.",
            AgentPersonality.CONCISE: "You provide brief, to-the-point responses.",
            AgentPersonality.DETAILED: "You provide comprehensive, thorough explanations.",
            AgentPersonality.CREATIVE: "You think outside the box and offer innovative solutions.",
            AgentPersonality.ANALYTICAL: "You approach problems methodically with data-driven insights.",
            AgentPersonality.CAUTIOUS: "You carefully consider risks and potential issues.",
            AgentPersonality.BOLD: "You are confident and not afraid to take calculated risks.",
            AgentPersonality.HUMOROUS: "You incorporate appropriate humor to engage users.",
            AgentPersonality.FORMAL: "You maintain formal, respectful communication."
        }
        parts.append(personality_desc.get(self.behavior.personality, ""))
        
        # Base prompt
        if self.system_prompt_base:
            parts.append(self.system_prompt_base)
        
        # Additional instructions
        for addition in self.system_prompt_additions:
            parts.append(addition)
        
        # Capabilities
        if self.capabilities:
            caps = ", ".join([c.name for c in self.capabilities])
            parts.append(f"Your capabilities include: {caps}")
        
        # Tools
        if self.tools:
            enabled_tools = [t.name for t in self.tools if t.enabled]
            if enabled_tools:
                parts.append(f"You have access to these tools: {', '.join(enabled_tools)}")
        
        # Behavior settings
        if self.behavior.creativity > 0.7:
            parts.append("Be creative and innovative in your responses.")
        elif self.behavior.creativity < 0.3:
            parts.append("Stick to established methods and proven approaches.")
        
        if self.behavior.verbosity > 0.7:
            parts.append("Provide detailed explanations and examples.")
        elif self.behavior.verbosity < 0.3:
            parts.append("Keep responses concise and focused.")
        
        if self.behavior.include_reasoning:
            parts.append("Show your reasoning process when solving problems.")
        
        if self.behavior.include_sources:
            parts.append("Cite sources and references when applicable.")
        
        # Custom instructions
        if self.behavior.custom_instructions:
            parts.append(f"Special instructions: {self.behavior.custom_instructions}")
        
        # Constraints
        if self.behavior.avoid_topics:
            parts.append(f"Avoid discussing: {', '.join(self.behavior.avoid_topics)}")
        
        if self.behavior.required_disclaimers:
            parts.append("Include appropriate disclaimers when relevant.")
        
        # Language
        if self.behavior.primary_language != "auto":
            parts.append(f"Respond primarily in {self.behavior.primary_language}.")
        
        return "\n\n".join(parts)


@dataclass
class AgentTeam:
    """A team of agents working together"""
    id: str
    name: str
    description: str
    agents: List[str] = field(default_factory=list)  # Agent IDs
    strategy: TeamStrategy = TeamStrategy.SEQUENTIAL
    
    # Team configuration
    manager_agent_id: Optional[str] = None  # For hierarchical strategy
    max_rounds: int = 5  # For debate/consensus
    consensus_threshold: float = 0.7  # Agreement threshold
    
    # Execution settings
    parallel_limit: int = 3
    timeout_per_agent: int = 60
    aggregate_outputs: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agents": self.agents,
            "strategy": self.strategy.value,
            "manager_agent_id": self.manager_agent_id,
            "max_rounds": self.max_rounds,
            "consensus_threshold": self.consensus_threshold,
            "parallel_limit": self.parallel_limit,
            "timeout_per_agent": self.timeout_per_agent,
            "aggregate_outputs": self.aggregate_outputs,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class AgentTemplate:
    """A template for creating agents"""
    id: str
    name: str
    description: str
    role: AgentRole
    icon: str
    category: str
    
    # Template configuration
    default_config: Dict[str, Any] = field(default_factory=dict)
    suggested_tools: List[str] = field(default_factory=list)
    suggested_capabilities: List[str] = field(default_factory=list)
    example_prompts: List[str] = field(default_factory=list)
    
    # Metadata
    author: str = "system"
    downloads: int = 0
    rating: float = 0.0
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role": self.role.value,
            "icon": self.icon,
            "category": self.category,
            "default_config": self.default_config,
            "suggested_tools": self.suggested_tools,
            "suggested_capabilities": self.suggested_capabilities,
            "example_prompts": self.example_prompts,
            "author": self.author,
            "downloads": self.downloads,
            "rating": self.rating,
            "tags": self.tags
        }


# =============================================================================
# AGENT MARKETPLACE
# =============================================================================

class AgentMarketplace:
    """
    Agent Marketplace & Custom Agent Builder
    
    Features:
    - Create custom agents with no-code builder
    - Browse and use agent templates
    - Manage multi-agent teams
    - Track agent performance
    - Import/export agents
    """
    
    def __init__(self, storage_dir: str = "data/agent_marketplace"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.agents_dir = self.storage_dir / "agents"
        self.teams_dir = self.storage_dir / "teams"
        self.templates_dir = self.storage_dir / "templates"
        self.exports_dir = self.storage_dir / "exports"
        
        for d in [self.agents_dir, self.teams_dir, self.templates_dir, self.exports_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self.agents: Dict[str, CustomAgent] = {}
        self.teams: Dict[str, AgentTeam] = {}
        self.templates: Dict[str, AgentTemplate] = {}
        
        # Available tools registry
        self.available_tools: Dict[str, AgentTool] = {}
        self.available_capabilities: Dict[str, AgentCapability] = {}
        
        # Initialize
        self._load_data()
        self._init_builtin_templates()
        self._init_available_tools()
        self._init_available_capabilities()
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
    def _load_data(self):
        """Load all data from storage"""
        # Load agents
        for f in self.agents_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.agents[data["id"]] = CustomAgent.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load agent {f}: {e}")
        
        # Load teams
        for f in self.teams_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.teams[data["id"]] = AgentTeam(**data)
            except Exception as e:
                logger.error(f"Failed to load team {f}: {e}")
        
        # Load custom templates
        for f in self.templates_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    data["role"] = AgentRole(data.get("role", "general"))
                    self.templates[data["id"]] = AgentTemplate(**data)
            except Exception as e:
                logger.error(f"Failed to load template {f}: {e}")
        
        logger.info(f"Loaded {len(self.agents)} agents, {len(self.teams)} teams, {len(self.templates)} templates")
    
    def _init_builtin_templates(self):
        """Initialize built-in agent templates"""
        builtin = [
            AgentTemplate(
                id="tpl_researcher",
                name="Research Assistant",
                description="Expert at finding, analyzing, and synthesizing information from multiple sources",
                role=AgentRole.RESEARCHER,
                icon="🔍",
                category="research",
                default_config={
                    "temperature": 0.6,
                    "behavior": {
                        "personality": "analytical",
                        "verbosity": 0.7,
                        "include_sources": True
                    }
                },
                suggested_tools=["web_search", "rag_query", "document_reader"],
                suggested_capabilities=["research", "summarization", "fact_checking"],
                example_prompts=[
                    "Research the latest developments in quantum computing",
                    "Find and compare the top 5 project management tools",
                    "Summarize recent studies on renewable energy"
                ],
                tags=["research", "analysis", "information"]
            ),
            AgentTemplate(
                id="tpl_coder",
                name="Code Developer",
                description="Expert programmer who writes, reviews, and debugs code across multiple languages",
                role=AgentRole.CODER,
                icon="💻",
                category="development",
                default_config={
                    "temperature": 0.4,
                    "behavior": {
                        "personality": "professional",
                        "verbosity": 0.5,
                        "include_reasoning": True
                    }
                },
                suggested_tools=["code_executor", "file_operations", "web_search"],
                suggested_capabilities=["coding", "debugging", "code_review", "testing"],
                example_prompts=[
                    "Write a Python function to parse CSV files",
                    "Debug this JavaScript code that isn't working",
                    "Review my code for security vulnerabilities"
                ],
                tags=["coding", "programming", "development"]
            ),
            AgentTemplate(
                id="tpl_writer",
                name="Content Writer",
                description="Creative writer for articles, documentation, and marketing content",
                role=AgentRole.WRITER,
                icon="✍️",
                category="content",
                default_config={
                    "temperature": 0.8,
                    "behavior": {
                        "personality": "creative",
                        "verbosity": 0.6,
                        "creativity": 0.8
                    }
                },
                suggested_tools=["web_search", "grammar_check"],
                suggested_capabilities=["writing", "editing", "brainstorming"],
                example_prompts=[
                    "Write a blog post about AI in healthcare",
                    "Create documentation for this API",
                    "Draft a marketing email for our new product"
                ],
                tags=["writing", "content", "creative"]
            ),
            AgentTemplate(
                id="tpl_analyst",
                name="Data Analyst",
                description="Analyzes data, creates visualizations, and provides insights",
                role=AgentRole.ANALYST,
                icon="📊",
                category="analytics",
                default_config={
                    "temperature": 0.3,
                    "behavior": {
                        "personality": "analytical",
                        "verbosity": 0.6,
                        "include_reasoning": True
                    }
                },
                suggested_tools=["code_executor", "file_operations", "calculator"],
                suggested_capabilities=["data_analysis", "visualization", "statistics"],
                example_prompts=[
                    "Analyze this sales data and find trends",
                    "Create a visualization of user growth",
                    "Calculate the correlation between these variables"
                ],
                tags=["analytics", "data", "visualization"]
            ),
            AgentTemplate(
                id="tpl_planner",
                name="Project Planner",
                description="Helps plan projects, break down tasks, and manage timelines",
                role=AgentRole.PLANNER,
                icon="📋",
                category="productivity",
                default_config={
                    "temperature": 0.5,
                    "behavior": {
                        "personality": "professional",
                        "verbosity": 0.5,
                        "risk_tolerance": 0.3
                    }
                },
                suggested_tools=["calendar", "task_manager"],
                suggested_capabilities=["planning", "organization", "estimation"],
                example_prompts=[
                    "Create a project plan for building a mobile app",
                    "Break down this feature into smaller tasks",
                    "Estimate the timeline for this project"
                ],
                tags=["planning", "productivity", "management"]
            ),
            AgentTemplate(
                id="tpl_teacher",
                name="AI Tutor",
                description="Patient teacher who explains concepts and helps with learning",
                role=AgentRole.TEACHER,
                icon="👨‍🏫",
                category="education",
                default_config={
                    "temperature": 0.6,
                    "behavior": {
                        "personality": "friendly",
                        "verbosity": 0.7,
                        "include_reasoning": True
                    }
                },
                suggested_tools=["web_search", "code_executor"],
                suggested_capabilities=["teaching", "explanation", "examples"],
                example_prompts=[
                    "Explain how neural networks work",
                    "Teach me Python basics step by step",
                    "Help me understand calculus derivatives"
                ],
                tags=["education", "teaching", "learning"]
            ),
            AgentTemplate(
                id="tpl_critic",
                name="Code Reviewer",
                description="Critical reviewer who identifies issues and suggests improvements",
                role=AgentRole.CRITIC,
                icon="🔎",
                category="quality",
                default_config={
                    "temperature": 0.4,
                    "behavior": {
                        "personality": "analytical",
                        "verbosity": 0.6,
                        "risk_tolerance": 0.2
                    }
                },
                suggested_tools=["code_executor", "security_scanner"],
                suggested_capabilities=["review", "critique", "improvement"],
                example_prompts=[
                    "Review this code for best practices",
                    "Find potential bugs in this function",
                    "Suggest improvements for this architecture"
                ],
                tags=["review", "quality", "critique"]
            ),
            AgentTemplate(
                id="tpl_architect",
                name="System Architect",
                description="Designs system architectures and makes technical decisions",
                role=AgentRole.ARCHITECT,
                icon="🏗️",
                category="architecture",
                default_config={
                    "temperature": 0.5,
                    "behavior": {
                        "personality": "professional",
                        "verbosity": 0.7,
                        "include_reasoning": True
                    }
                },
                suggested_tools=["web_search", "diagram_generator"],
                suggested_capabilities=["architecture", "design", "scalability"],
                example_prompts=[
                    "Design a microservices architecture for an e-commerce platform",
                    "Compare SQL vs NoSQL for our use case",
                    "Recommend a tech stack for a real-time chat application"
                ],
                tags=["architecture", "design", "systems"]
            )
        ]
        
        for template in builtin:
            if template.id not in self.templates:
                self.templates[template.id] = template
    
    def _init_available_tools(self):
        """Initialize available tools that agents can use"""
        tools = [
            AgentTool(
                id="tool_web_search",
                name="web_search",
                description="Search the web for information",
                category="research",
                input_schema={"query": "string", "num_results": "integer"},
                output_schema={"results": "array"}
            ),
            AgentTool(
                id="tool_rag_query",
                name="rag_query",
                description="Query the local knowledge base",
                category="research",
                input_schema={"query": "string", "top_k": "integer"},
                output_schema={"documents": "array", "answer": "string"}
            ),
            AgentTool(
                id="tool_code_executor",
                name="code_executor",
                description="Execute Python or JavaScript code",
                category="development",
                input_schema={"code": "string", "language": "string"},
                output_schema={"output": "string", "error": "string"},
                requires_approval=True
            ),
            AgentTool(
                id="tool_file_operations",
                name="file_operations",
                description="Read, write, and manage files",
                category="utility",
                input_schema={"operation": "string", "path": "string", "content": "string"},
                output_schema={"success": "boolean", "data": "any"}
            ),
            AgentTool(
                id="tool_calculator",
                name="calculator",
                description="Perform mathematical calculations",
                category="utility",
                input_schema={"expression": "string"},
                output_schema={"result": "number"}
            ),
            AgentTool(
                id="tool_vision_analyze",
                name="vision_analyze",
                description="Analyze images using AI vision",
                category="ai",
                input_schema={"image": "string", "prompt": "string"},
                output_schema={"description": "string", "objects": "array"}
            ),
            AgentTool(
                id="tool_voice_stt",
                name="voice_stt",
                description="Convert speech to text",
                category="ai",
                input_schema={"audio": "string", "language": "string"},
                output_schema={"text": "string", "confidence": "number"},
                is_async=True
            ),
            AgentTool(
                id="tool_voice_tts",
                name="voice_tts",
                description="Convert text to speech",
                category="ai",
                input_schema={"text": "string", "voice": "string"},
                output_schema={"audio": "string"},
                is_async=True
            ),
            AgentTool(
                id="tool_security_scan",
                name="security_scan",
                description="Scan code for security vulnerabilities",
                category="security",
                input_schema={"code": "string", "language": "string"},
                output_schema={"vulnerabilities": "array"}
            )
        ]
        
        for tool in tools:
            self.available_tools[tool.id] = tool
    
    def _init_available_capabilities(self):
        """Initialize available capabilities"""
        capabilities = [
            AgentCapability(
                id="cap_research",
                name="research",
                description="Find and analyze information",
                category="research",
                required_tools=["web_search", "rag_query"]
            ),
            AgentCapability(
                id="cap_summarization",
                name="summarization",
                description="Summarize long documents",
                category="research"
            ),
            AgentCapability(
                id="cap_coding",
                name="coding",
                description="Write and understand code",
                category="development",
                required_tools=["code_executor"]
            ),
            AgentCapability(
                id="cap_debugging",
                name="debugging",
                description="Find and fix bugs in code",
                category="development",
                required_tools=["code_executor"]
            ),
            AgentCapability(
                id="cap_writing",
                name="writing",
                description="Create written content",
                category="content"
            ),
            AgentCapability(
                id="cap_data_analysis",
                name="data_analysis",
                description="Analyze and interpret data",
                category="analytics",
                required_tools=["code_executor", "calculator"]
            ),
            AgentCapability(
                id="cap_planning",
                name="planning",
                description="Create plans and break down tasks",
                category="productivity"
            ),
            AgentCapability(
                id="cap_teaching",
                name="teaching",
                description="Explain concepts clearly",
                category="education"
            ),
            AgentCapability(
                id="cap_review",
                name="review",
                description="Review and critique work",
                category="quality"
            )
        ]
        
        for cap in capabilities:
            self.available_capabilities[cap.id] = cap
    
    # =========================================================================
    # AGENT CRUD
    # =========================================================================
    
    async def create_agent(
        self,
        name: str,
        description: str,
        role: AgentRole,
        template_id: Optional[str] = None,
        **kwargs
    ) -> CustomAgent:
        """Create a new custom agent"""
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        
        # Start from template if provided
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            config = template.default_config.copy()
            config.update(kwargs)
            kwargs = config
            
            # Add suggested tools
            tools = []
            for tool_name in template.suggested_tools:
                for tid, tool in self.available_tools.items():
                    if tool.name == tool_name:
                        tools.append(tool)
                        break
            
            # Add suggested capabilities
            capabilities = []
            for cap_name in template.suggested_capabilities:
                for cid, cap in self.available_capabilities.items():
                    if cap.name == cap_name:
                        capabilities.append(cap)
                        break
            
            kwargs["tools"] = tools
            kwargs["capabilities"] = capabilities
        
        # Create behavior
        behavior_data = kwargs.pop("behavior", {})
        behavior = AgentBehavior(
            personality=AgentPersonality(behavior_data.get("personality", "professional")),
            creativity=behavior_data.get("creativity", 0.5),
            verbosity=behavior_data.get("verbosity", 0.5),
            risk_tolerance=behavior_data.get("risk_tolerance", 0.3),
            autonomy_level=behavior_data.get("autonomy_level", 0.5),
            use_markdown=behavior_data.get("use_markdown", True),
            include_reasoning=behavior_data.get("include_reasoning", True),
            include_sources=behavior_data.get("include_sources", True),
            primary_language=behavior_data.get("primary_language", "auto"),
            response_length=behavior_data.get("response_length", "adaptive"),
            custom_instructions=behavior_data.get("custom_instructions", ""),
            avoid_topics=behavior_data.get("avoid_topics", []),
            required_disclaimers=behavior_data.get("required_disclaimers", [])
        )
        
        agent = CustomAgent(
            id=agent_id,
            name=name,
            description=description,
            role=role,
            icon=kwargs.get("icon", "🤖"),
            color=kwargs.get("color", "#3B82F6"),
            capabilities=kwargs.get("capabilities", []),
            tools=kwargs.get("tools", []),
            behavior=behavior,
            system_prompt_base=kwargs.get("system_prompt_base", ""),
            system_prompt_additions=kwargs.get("system_prompt_additions", []),
            preferred_model=kwargs.get("preferred_model", "auto"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
            tags=kwargs.get("tags", []),
            category=kwargs.get("category", "custom")
        )
        
        # Save
        self.agents[agent_id] = agent
        await self._save_agent(agent)
        
        logger.info(f"Created agent: {name} ({agent_id})")
        return agent
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[CustomAgent]:
        """Update an existing agent"""
        if agent_id not in self.agents:
            return None
        
        agent = self.agents[agent_id]
        
        # Create version snapshot before update
        version = AgentVersion(
            version=agent.version,
            created_at=agent.updated_at,
            changelog=f"Updated: {list(updates.keys())}",
            config_snapshot=agent.to_dict(),
            is_current=False
        )
        agent.versions.append(version)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(agent, key):
                if key == "behavior" and isinstance(value, dict):
                    for bkey, bvalue in value.items():
                        if hasattr(agent.behavior, bkey):
                            setattr(agent.behavior, bkey, bvalue)
                elif key == "memory_config" and isinstance(value, dict):
                    for mkey, mvalue in value.items():
                        if hasattr(agent.memory_config, mkey):
                            setattr(agent.memory_config, mkey, mvalue)
                else:
                    setattr(agent, key, value)
        
        # Update metadata
        agent.updated_at = datetime.now().isoformat()
        
        # Increment version
        parts = agent.version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        agent.version = ".".join(parts)
        
        await self._save_agent(agent)
        logger.info(f"Updated agent: {agent.name} to v{agent.version}")
        
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents.pop(agent_id)
        
        # Remove from disk
        agent_file = self.agents_dir / f"{agent_id}.json"
        if agent_file.exists():
            agent_file.unlink()
        
        # Remove from teams
        for team in self.teams.values():
            if agent_id in team.agents:
                team.agents.remove(agent_id)
        
        logger.info(f"Deleted agent: {agent.name}")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[CustomAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(
        self,
        role: Optional[AgentRole] = None,
        category: Optional[str] = None,
        status: Optional[AgentStatus] = None,
        tags: Optional[List[str]] = None
    ) -> List[CustomAgent]:
        """List agents with optional filters"""
        agents = list(self.agents.values())
        
        if role:
            agents = [a for a in agents if a.role == role]
        
        if category:
            agents = [a for a in agents if a.category == category]
        
        if status:
            agents = [a for a in agents if a.status == status]
        
        if tags:
            agents = [a for a in agents if any(t in a.tags for t in tags)]
        
        return sorted(agents, key=lambda x: x.name)
    
    async def _save_agent(self, agent: CustomAgent):
        """Save agent to disk"""
        agent_file = self.agents_dir / f"{agent.id}.json"
        with open(agent_file, 'w', encoding='utf-8') as f:
            json.dump(agent.to_dict(), f, indent=2, ensure_ascii=False)
    
    # =========================================================================
    # AGENT TEAMS
    # =========================================================================
    
    async def create_team(
        self,
        name: str,
        description: str,
        agent_ids: List[str],
        strategy: TeamStrategy = TeamStrategy.SEQUENTIAL,
        **kwargs
    ) -> AgentTeam:
        """Create a multi-agent team"""
        team_id = f"team_{uuid.uuid4().hex[:12]}"
        
        # Validate agents exist
        valid_agents = [aid for aid in agent_ids if aid in self.agents]
        
        team = AgentTeam(
            id=team_id,
            name=name,
            description=description,
            agents=valid_agents,
            strategy=strategy,
            manager_agent_id=kwargs.get("manager_agent_id"),
            max_rounds=kwargs.get("max_rounds", 5),
            consensus_threshold=kwargs.get("consensus_threshold", 0.7),
            parallel_limit=kwargs.get("parallel_limit", 3),
            timeout_per_agent=kwargs.get("timeout_per_agent", 60),
            aggregate_outputs=kwargs.get("aggregate_outputs", True)
        )
        
        self.teams[team_id] = team
        await self._save_team(team)
        
        logger.info(f"Created team: {name} with {len(valid_agents)} agents")
        return team
    
    async def execute_team(
        self,
        team_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a task using a team of agents"""
        if team_id not in self.teams:
            return {"error": "Team not found"}
        
        team = self.teams[team_id]
        results = []
        
        if team.strategy == TeamStrategy.SEQUENTIAL:
            results = await self._execute_sequential(team, task, context)
        elif team.strategy == TeamStrategy.PARALLEL:
            results = await self._execute_parallel(team, task, context)
        elif team.strategy == TeamStrategy.HIERARCHICAL:
            results = await self._execute_hierarchical(team, task, context)
        elif team.strategy == TeamStrategy.CONSENSUS:
            results = await self._execute_consensus(team, task, context)
        elif team.strategy == TeamStrategy.DEBATE:
            results = await self._execute_debate(team, task, context)
        elif team.strategy == TeamStrategy.PIPELINE:
            results = await self._execute_pipeline(team, task, context)
        
        # Aggregate if needed
        if team.aggregate_outputs and len(results) > 1:
            aggregated = await self._aggregate_results(results, task)
            return {
                "team_id": team_id,
                "strategy": team.strategy.value,
                "individual_results": results,
                "aggregated_result": aggregated
            }
        
        return {
            "team_id": team_id,
            "strategy": team.strategy.value,
            "results": results
        }
    
    async def _execute_sequential(
        self,
        team: AgentTeam,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """Execute agents one after another"""
        results = []
        current_context = context or {}
        
        for agent_id in team.agents:
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            
            # Add previous results to context
            if results:
                current_context["previous_results"] = results
            
            result = await self._run_agent(agent, task, current_context)
            results.append({
                "agent_id": agent_id,
                "agent_name": agent.name,
                "result": result
            })
        
        return results
    
    async def _execute_parallel(
        self,
        team: AgentTeam,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """Execute agents in parallel"""
        tasks = []
        
        for agent_id in team.agents[:team.parallel_limit]:
            agent = self.agents.get(agent_id)
            if agent:
                tasks.append(self._run_agent(agent, task, context))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            {
                "agent_id": team.agents[i],
                "agent_name": self.agents[team.agents[i]].name,
                "result": r if not isinstance(r, Exception) else str(r)
            }
            for i, r in enumerate(results)
        ]
    
    async def _execute_hierarchical(
        self,
        team: AgentTeam,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """Manager agent delegates to worker agents"""
        if not team.manager_agent_id or team.manager_agent_id not in self.agents:
            return await self._execute_sequential(team, task, context)
        
        manager = self.agents[team.manager_agent_id]
        workers = [self.agents[aid] for aid in team.agents if aid != team.manager_agent_id and aid in self.agents]
        
        # Manager creates delegation plan
        delegation_prompt = f"""As a manager, analyze this task and delegate to your team members:
Task: {task}

Available team members:
{json.dumps([{"name": w.name, "role": w.role.value, "capabilities": [c.name for c in w.capabilities]} for w in workers], indent=2)}

Create a delegation plan with subtasks for each team member."""
        
        plan_result = await self._run_agent(manager, delegation_prompt, context)
        
        results = [{"agent_id": team.manager_agent_id, "agent_name": manager.name, "result": plan_result, "role": "manager"}]
        
        # Workers execute (simplified - in real implementation parse the plan)
        for worker in workers:
            result = await self._run_agent(worker, f"Manager's task for you: {task}", context)
            results.append({"agent_id": worker.id, "agent_name": worker.name, "result": result, "role": "worker"})
        
        return results
    
    async def _execute_consensus(
        self,
        team: AgentTeam,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """Agents vote and reach consensus"""
        # First round: all agents give their answers
        initial_results = await self._execute_parallel(team, task, context)
        
        # Voting rounds
        for round_num in range(team.max_rounds):
            # Each agent sees others' answers and votes
            voting_context = {
                **(context or {}),
                "previous_answers": initial_results,
                "instruction": "Review all answers and vote for the best one or synthesize a consensus."
            }
            
            vote_results = await self._execute_parallel(team, 
                f"Based on the team's answers, what is the consensus for: {task}", 
                voting_context)
            
            # Check consensus (simplified)
            # In real implementation, parse votes and check threshold
            break
        
        return initial_results + [{"round": "consensus", "votes": vote_results}]
    
    async def _execute_debate(
        self,
        team: AgentTeam,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """Agents debate and critique each other"""
        if len(team.agents) < 2:
            return await self._execute_sequential(team, task, context)
        
        results = []
        
        # Initial positions
        for agent_id in team.agents[:2]:
            agent = self.agents.get(agent_id)
            if agent:
                result = await self._run_agent(agent, task, context)
                results.append({"agent_id": agent_id, "agent_name": agent.name, "result": result, "round": 0})
        
        # Debate rounds
        for round_num in range(1, team.max_rounds):
            for i, agent_id in enumerate(team.agents[:2]):
                agent = self.agents.get(agent_id)
                if not agent:
                    continue
                
                opponent_idx = 1 - i
                opponent_result = results[-(2 - i)]["result"] if len(results) >= 2 else ""
                
                debate_context = {
                    **(context or {}),
                    "opponent_argument": opponent_result,
                    "instruction": "Critique the opponent's argument and strengthen your position."
                }
                
                result = await self._run_agent(agent, 
                    f"Debate round {round_num}: {task}", 
                    debate_context)
                results.append({"agent_id": agent_id, "agent_name": agent.name, "result": result, "round": round_num})
        
        return results
    
    async def _execute_pipeline(
        self,
        team: AgentTeam,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict]:
        """Each agent transforms the output of the previous"""
        results = []
        current_input = task
        current_context = context or {}
        
        for agent_id in team.agents:
            agent = self.agents.get(agent_id)
            if not agent:
                continue
            
            pipeline_context = {
                **current_context,
                "pipeline_input": current_input,
                "instruction": f"Transform this input according to your role ({agent.role.value})."
            }
            
            result = await self._run_agent(agent, current_input, pipeline_context)
            results.append({
                "agent_id": agent_id,
                "agent_name": agent.name,
                "input": current_input,
                "output": result
            })
            
            current_input = result
        
        return results
    
    async def _run_agent(
        self,
        agent: CustomAgent,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Run a single agent on a task"""
        try:
            # Import LLM manager
            from core.llm_manager import llm_manager
            
            # Build messages
            system_prompt = agent.generate_system_prompt()
            if context:
                system_prompt += f"\n\nContext: {json.dumps(context, indent=2)}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ]
            
            # Get model
            model = agent.preferred_model if agent.preferred_model != "auto" else None
            
            # Generate
            start_time = time.time()
            response = await llm_manager.generate_async(
                messages=messages,
                model=model,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens
            )
            elapsed = time.time() - start_time
            
            # Update metrics
            agent.metrics.total_runs += 1
            agent.metrics.successful_runs += 1
            agent.metrics.response_times.append(elapsed)
            agent.metrics.average_response_time = sum(agent.metrics.response_times) / len(agent.metrics.response_times)
            agent.metrics.last_used = datetime.now().isoformat()
            
            await self._save_agent(agent)
            
            return response
        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {e}")
            agent.metrics.total_runs += 1
            agent.metrics.failed_runs += 1
            agent.metrics.error_rate = agent.metrics.failed_runs / agent.metrics.total_runs
            return f"Error: {str(e)}"
    
    async def _aggregate_results(self, results: List[Dict], task: str) -> str:
        """Aggregate multiple agent results into one"""
        try:
            from core.llm_manager import llm_manager
            
            results_text = "\n\n".join([
                f"**{r.get('agent_name', 'Agent')}**:\n{r.get('result', r.get('output', ''))}"
                for r in results
            ])
            
            prompt = f"""Synthesize these team member responses into a comprehensive answer:

Task: {task}

Team Responses:
{results_text}

Provide a unified, well-organized response that incorporates the best insights from all team members."""
            
            response = await llm_manager.generate_async(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            return response
        except Exception as e:
            return f"Aggregation failed: {e}"
    
    async def _save_team(self, team: AgentTeam):
        """Save team to disk"""
        team_file = self.teams_dir / f"{team.id}.json"
        with open(team_file, 'w', encoding='utf-8') as f:
            json.dump(team.to_dict(), f, indent=2, ensure_ascii=False)
    
    def list_teams(self) -> List[AgentTeam]:
        """List all teams"""
        return list(self.teams.values())
    
    def get_team(self, team_id: str) -> Optional[AgentTeam]:
        """Get a team by ID"""
        return self.teams.get(team_id)
    
    # =========================================================================
    # TEMPLATES
    # =========================================================================
    
    def list_templates(
        self,
        category: Optional[str] = None,
        role: Optional[AgentRole] = None
    ) -> List[AgentTemplate]:
        """List available templates"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if role:
            templates = [t for t in templates if t.role == role]
        
        return sorted(templates, key=lambda x: (-x.downloads, x.name))
    
    def get_template(self, template_id: str) -> Optional[AgentTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)
    
    async def create_from_template(
        self,
        template_id: str,
        name: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Optional[CustomAgent]:
        """Create an agent from a template"""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        # Increment download count
        template.downloads += 1
        
        # Merge customizations with template defaults
        config = template.default_config.copy()
        if customizations:
            config.update(customizations)
        
        return await self.create_agent(
            name=name,
            description=f"Based on {template.name} template",
            role=template.role,
            template_id=template_id,
            icon=template.icon,
            category=template.category,
            tags=template.tags,
            **config
        )
    
    # =========================================================================
    # IMPORT/EXPORT
    # =========================================================================
    
    async def export_agent(self, agent_id: str) -> Optional[str]:
        """Export an agent to a .agent file"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        # Create export package
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "agent": agent.to_dict()
        }
        
        # Create zip file
        export_filename = f"{agent.name.replace(' ', '_')}_{agent.version}.agent"
        export_path = self.exports_dir / export_filename
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("agent.json", json.dumps(export_data, indent=2, ensure_ascii=False))
            
            # Include icon if custom
            if agent.icon and len(agent.icon) > 2:  # Not an emoji
                zf.writestr("icon.txt", agent.icon)
        
        logger.info(f"Exported agent {agent.name} to {export_path}")
        return str(export_path)
    
    async def import_agent(self, file_path: str) -> Optional[CustomAgent]:
        """Import an agent from a .agent file"""
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                agent_json = zf.read("agent.json").decode('utf-8')
                export_data = json.loads(agent_json)
                
                agent_data = export_data.get("agent", {})
                
                # Generate new ID to avoid conflicts
                agent_data["id"] = f"agent_{uuid.uuid4().hex[:12]}"
                agent_data["created_at"] = datetime.now().isoformat()
                agent_data["updated_at"] = datetime.now().isoformat()
                
                # Reset metrics
                agent_data["metrics"] = {}
                
                agent = CustomAgent.from_dict(agent_data)
                self.agents[agent.id] = agent
                await self._save_agent(agent)
                
                logger.info(f"Imported agent: {agent.name}")
                return agent
        except Exception as e:
            logger.error(f"Failed to import agent: {e}")
            return None
    
    async def export_team(self, team_id: str) -> Optional[str]:
        """Export a team with all its agents"""
        team = self.teams.get(team_id)
        if not team:
            return None
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "team": team.to_dict(),
            "agents": [self.agents[aid].to_dict() for aid in team.agents if aid in self.agents]
        }
        
        export_filename = f"{team.name.replace(' ', '_')}.team"
        export_path = self.exports_dir / export_filename
        
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("team.json", json.dumps(export_data, indent=2, ensure_ascii=False))
        
        return str(export_path)
    
    # =========================================================================
    # ANALYTICS
    # =========================================================================
    
    def get_agent_analytics(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed analytics for an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        metrics = agent.metrics
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "total_runs": metrics.total_runs,
            "successful_runs": metrics.successful_runs,
            "failed_runs": metrics.failed_runs,
            "success_rate": (metrics.successful_runs / metrics.total_runs * 100) if metrics.total_runs > 0 else 0,
            "average_response_time": metrics.average_response_time,
            "average_rating": metrics.average_rating,
            "total_tokens_used": metrics.total_tokens_used,
            "last_used": metrics.last_used,
            "capability_usage": metrics.capability_usage,
            "tool_usage": metrics.tool_usage
        }
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get overall marketplace statistics"""
        total_agents = len(self.agents)
        total_teams = len(self.teams)
        total_templates = len(self.templates)
        
        # Role distribution
        role_counts = {}
        for agent in self.agents.values():
            role = agent.role.value
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Category distribution
        category_counts = {}
        for agent in self.agents.values():
            cat = agent.category
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Most used agents
        agents_by_usage = sorted(
            self.agents.values(),
            key=lambda x: x.metrics.total_runs,
            reverse=True
        )[:5]
        
        # Top rated agents
        agents_by_rating = sorted(
            [a for a in self.agents.values() if a.metrics.average_rating > 0],
            key=lambda x: x.metrics.average_rating,
            reverse=True
        )[:5]
        
        return {
            "total_agents": total_agents,
            "total_teams": total_teams,
            "total_templates": total_templates,
            "role_distribution": role_counts,
            "category_distribution": category_counts,
            "most_used_agents": [
                {"id": a.id, "name": a.name, "runs": a.metrics.total_runs}
                for a in agents_by_usage
            ],
            "top_rated_agents": [
                {"id": a.id, "name": a.name, "rating": a.metrics.average_rating}
                for a in agents_by_rating
            ]
        }
    
    async def rate_agent(self, agent_id: str, rating: float) -> bool:
        """Rate an agent (1-5 stars)"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        rating = max(1.0, min(5.0, rating))
        
        agent.metrics.user_ratings.append(rating)
        agent.metrics.average_rating = sum(agent.metrics.user_ratings) / len(agent.metrics.user_ratings)
        
        await self._save_agent(agent)
        return True
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "requires_approval": t.requires_approval
            }
            for t in self.available_tools.values()
        ]
    
    def get_available_capabilities(self) -> List[Dict[str, Any]]:
        """Get list of available capabilities"""
        return [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "category": c.category,
                "required_tools": c.required_tools
            }
            for c in self.available_capabilities.values()
        ]
    
    def get_role_descriptions(self) -> Dict[str, str]:
        """Get descriptions for all agent roles"""
        return {
            AgentRole.GENERAL.value: "General purpose assistant",
            AgentRole.RESEARCHER.value: "Expert at finding and analyzing information",
            AgentRole.ANALYST.value: "Analyzes data and provides insights",
            AgentRole.WRITER.value: "Creates written content and documentation",
            AgentRole.CODER.value: "Writes, reviews, and debugs code",
            AgentRole.PLANNER.value: "Plans projects and breaks down tasks",
            AgentRole.CRITIC.value: "Reviews and critiques work",
            AgentRole.SUMMARIZER.value: "Summarizes long content",
            AgentRole.TRANSLATOR.value: "Translates between languages",
            AgentRole.TEACHER.value: "Explains concepts and teaches",
            AgentRole.DEBUGGER.value: "Finds and fixes bugs",
            AgentRole.ARCHITECT.value: "Designs system architectures",
            AgentRole.REVIEWER.value: "Reviews code and documents",
            AgentRole.CREATIVE.value: "Creative and artistic tasks",
            AgentRole.CUSTOM.value: "Custom role with specific behaviors"
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

agent_marketplace = AgentMarketplace()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def create_agent(name: str, role: str, **kwargs) -> CustomAgent:
    """Quick function to create an agent"""
    return await agent_marketplace.create_agent(
        name=name,
        description=kwargs.get("description", ""),
        role=AgentRole(role),
        **kwargs
    )


async def run_agent(agent_id: str, task: str, context: Optional[Dict] = None) -> str:
    """Quick function to run an agent"""
    agent = agent_marketplace.get_agent(agent_id)
    if not agent:
        return "Agent not found"
    return await agent_marketplace._run_agent(agent, task, context)


async def run_team(team_id: str, task: str, context: Optional[Dict] = None) -> Dict:
    """Quick function to run a team"""
    return await agent_marketplace.execute_team(team_id, task, context)
