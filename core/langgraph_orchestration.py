"""
🔄 LangGraph Agent Orchestration
================================

LangGraph-inspired agent orchestration sistemi.
State machine tabanlı, kontrol edilebilir agent akışları.

Features:
- State graph tanımlaması
- Conditional routing
- Parallel execution
- Human-in-the-loop
- Checkpoint/resume
- Streaming support
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any, Callable, Dict, Generic, List, Literal, Optional,
    Set, Tuple, Type, TypeVar, Union
)
from pydantic import BaseModel, Field
import copy

logger = logging.getLogger(__name__)


# ============ STATE TYPES ============

class NodeType(str, Enum):
    """Node types in the graph"""
    START = "start"
    END = "end"
    AGENT = "agent"
    TOOL = "tool"
    ROUTER = "router"
    HUMAN = "human"
    PARALLEL = "parallel"
    CHECKPOINT = "checkpoint"


class ExecutionStatus(str, Enum):
    """Execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    WAITING_HUMAN = "waiting_human"
    CANCELLED = "cancelled"


# ============ STATE CLASSES ============

class AgentState(BaseModel):
    """
    Base agent state - mutable state passed through the graph.
    Extend this for your specific use case.
    """
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    current_step: int = 0
    total_steps: int = 0
    error: Optional[str] = None
    
    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to state"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    def get_last_message(self) -> Optional[Dict]:
        """Get last message"""
        return self.messages[-1] if self.messages else None
    
    def get_messages_as_string(self) -> str:
        """Get messages formatted as string"""
        lines = []
        for msg in self.messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
    
    def model_copy(self, deep: bool = True) -> "AgentState":
        """Create a copy of state"""
        return super().model_copy(deep=deep)


class ConversationState(AgentState):
    """Conversation-specific state"""
    user_input: str = ""
    assistant_response: str = ""
    intent: Optional[str] = None
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    rag_results: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    requires_human: bool = False
    session_id: Optional[str] = None


class RAGState(AgentState):
    """RAG pipeline state"""
    query: str = ""
    reformulated_query: Optional[str] = None
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    filtered_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    answer: str = ""
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    needs_correction: bool = False
    correction_reason: Optional[str] = None
    retrieval_scores: List[float] = Field(default_factory=list)


class TaskState(AgentState):
    """Task execution state"""
    task_description: str = ""
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    current_subtask: int = 0
    results: List[Any] = Field(default_factory=list)
    tools_available: List[str] = Field(default_factory=list)
    plan: Optional[str] = None


S = TypeVar('S', bound=AgentState)


# ============ NODE DEFINITIONS ============

@dataclass
class GraphNode:
    """Graph node definition"""
    name: str
    node_type: NodeType
    handler: Optional[Callable[[Any], Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class GraphEdge:
    """Graph edge definition"""
    source: str
    target: str
    condition: Optional[Callable[[Any], bool]] = None
    label: Optional[str] = None
    priority: int = 0


@dataclass
class ExecutionResult:
    """Result of node execution"""
    node_name: str
    status: ExecutionStatus
    state: Any
    next_nodes: List[str]
    duration_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============ STATE GRAPH ============

class StateGraph(Generic[S]):
    """
    LangGraph-style state graph for agent orchestration.
    
    Usage:
        graph = StateGraph(ConversationState)
        
        # Add nodes
        graph.add_node("classify", classify_intent)
        graph.add_node("rag_search", rag_search)
        graph.add_node("generate", generate_response)
        
        # Add edges
        graph.add_edge("classify", "rag_search", condition=needs_rag)
        graph.add_edge("classify", "generate", condition=lambda s: not needs_rag(s))
        graph.add_edge("rag_search", "generate")
        
        # Compile and run
        app = graph.compile()
        result = await app.invoke(initial_state)
    """
    
    def __init__(self, state_class: Type[S]):
        self.state_class = state_class
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.entry_point: Optional[str] = None
        self.end_nodes: Set[str] = set()
        
        # Add implicit START and END nodes
        self.add_node("__start__", NodeType.START)
        self.add_node("__end__", NodeType.END)
    
    def add_node(
        self,
        name: str,
        handler: Optional[Callable[[S], S]] = None,
        node_type: NodeType = NodeType.AGENT,
        **metadata
    ) -> "StateGraph[S]":
        """Add a node to the graph"""
        if handler is None and node_type not in [NodeType.START, NodeType.END]:
            raise ValueError(f"Handler required for node type: {node_type}")
        
        self.nodes[name] = GraphNode(
            name=name,
            node_type=node_type,
            handler=handler,
            metadata=metadata
        )
        
        if node_type == NodeType.END:
            self.end_nodes.add(name)
        
        return self
    
    def add_edge(
        self,
        source: str,
        target: str,
        condition: Optional[Callable[[S], bool]] = None,
        label: Optional[str] = None,
        priority: int = 0
    ) -> "StateGraph[S]":
        """Add an edge between nodes"""
        if source not in self.nodes and source != "__start__":
            raise ValueError(f"Source node not found: {source}")
        if target not in self.nodes and target != "__end__":
            raise ValueError(f"Target node not found: {target}")
        
        self.edges.append(GraphEdge(
            source=source,
            target=target,
            condition=condition,
            label=label,
            priority=priority
        ))
        
        return self
    
    def add_conditional_edges(
        self,
        source: str,
        condition_map: Dict[str, str],
        condition_fn: Callable[[S], str]
    ) -> "StateGraph[S]":
        """
        Add conditional edges from a node.
        
        Args:
            source: Source node name
            condition_map: Dict mapping condition results to target nodes
            condition_fn: Function that returns a key from condition_map
        """
        for key, target in condition_map.items():
            self.add_edge(
                source=source,
                target=target,
                condition=lambda s, k=key, fn=condition_fn: fn(s) == k,
                label=key
            )
        
        return self
    
    def set_entry_point(self, node_name: str) -> "StateGraph[S]":
        """Set the entry point for the graph"""
        if node_name not in self.nodes:
            raise ValueError(f"Node not found: {node_name}")
        self.entry_point = node_name
        self.add_edge("__start__", node_name)
        return self
    
    def set_finish(self, node_name: str) -> "StateGraph[S]":
        """Set a node as finish point (connects to END)"""
        if node_name not in self.nodes:
            raise ValueError(f"Node not found: {node_name}")
        self.add_edge(node_name, "__end__")
        return self
    
    def compile(self) -> "CompiledGraph[S]":
        """Compile the graph for execution"""
        if not self.entry_point:
            raise ValueError("Entry point not set. Use set_entry_point()")
        
        return CompiledGraph(self)
    
    def get_mermaid(self) -> str:
        """Generate Mermaid diagram of the graph"""
        lines = ["graph TD"]
        
        for edge in self.edges:
            source = edge.source.replace("__", "")
            target = edge.target.replace("__", "")
            if edge.label:
                lines.append(f"    {source}-->|{edge.label}|{target}")
            else:
                lines.append(f"    {source}-->{target}")
        
        return "\n".join(lines)


# ============ COMPILED GRAPH ============

class CompiledGraph(Generic[S]):
    """Compiled graph ready for execution"""
    
    def __init__(self, graph: StateGraph[S]):
        self.graph = graph
        self.state_class = graph.state_class
        self.checkpoints: Dict[str, Any] = {}
        self._validate()
    
    def _validate(self):
        """Validate graph structure"""
        # Check all nodes are reachable
        reachable = set()
        to_visit = ["__start__"]
        
        while to_visit:
            current = to_visit.pop()
            if current in reachable:
                continue
            reachable.add(current)
            
            for edge in self.graph.edges:
                if edge.source == current and edge.target not in reachable:
                    to_visit.append(edge.target)
        
        unreachable = set(self.graph.nodes.keys()) - reachable
        if unreachable:
            logger.warning(f"Unreachable nodes: {unreachable}")
        
        # Check END is reachable
        if "__end__" not in reachable:
            logger.warning("END node is not reachable - graph may run indefinitely")
    
    async def invoke(
        self,
        state: S,
        config: Optional[Dict[str, Any]] = None,
        max_steps: int = 100,
        timeout: float = 300.0
    ) -> S:
        """
        Execute the graph from start to end.
        
        Args:
            state: Initial state
            config: Execution configuration
            max_steps: Maximum execution steps
            timeout: Timeout in seconds
            
        Returns:
            Final state after graph execution
        """
        config = config or {}
        execution_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        current_node = self.graph.entry_point
        step = 0
        
        logger.info(f"[{execution_id}] Starting graph execution from: {current_node}")
        
        while current_node and current_node != "__end__" and step < max_steps:
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Graph execution timed out after {timeout}s")
            
            step += 1
            state.current_step = step
            
            # Get node
            node = self.graph.nodes.get(current_node)
            if not node:
                raise ValueError(f"Node not found: {current_node}")
            
            logger.debug(f"[{execution_id}] Step {step}: Executing node '{current_node}'")
            
            # Execute node
            result = await self._execute_node(node, state, config)
            
            if result.status == ExecutionStatus.FAILED:
                state.error = result.error
                logger.error(f"[{execution_id}] Node '{current_node}' failed: {result.error}")
                break
            
            state = result.state
            
            # Save checkpoint if enabled
            if config.get("checkpoints", False):
                self.checkpoints[f"{execution_id}_{step}"] = state.model_copy(deep=True)
            
            # Get next node
            next_node = self._get_next_node(current_node, state)
            current_node = next_node
        
        if step >= max_steps:
            logger.warning(f"[{execution_id}] Reached max steps ({max_steps})")
        
        state.total_steps = step
        logger.info(f"[{execution_id}] Graph execution completed in {step} steps")
        
        return state
    
    async def stream(
        self,
        state: S,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Stream execution results as generator.
        
        Yields:
            Tuple of (node_name, state) after each node execution
        """
        config = config or {}
        current_node = self.graph.entry_point
        step = 0
        
        while current_node and current_node != "__end__" and step < 100:
            step += 1
            node = self.graph.nodes.get(current_node)
            if not node:
                break
            
            result = await self._execute_node(node, state, config)
            state = result.state
            
            yield (current_node, state.model_copy())
            
            if result.status == ExecutionStatus.FAILED:
                break
            
            current_node = self._get_next_node(current_node, state)
    
    async def _execute_node(
        self,
        node: GraphNode,
        state: S,
        config: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single node"""
        start_time = time.time()
        
        try:
            if node.node_type in [NodeType.START, NodeType.END]:
                return ExecutionResult(
                    node_name=node.name,
                    status=ExecutionStatus.COMPLETED,
                    state=state,
                    next_nodes=[],
                    duration_ms=0
                )
            
            # Execute handler
            if asyncio.iscoroutinefunction(node.handler):
                new_state = await node.handler(state)
            else:
                new_state = node.handler(state)
            
            # Ensure state type
            if not isinstance(new_state, self.state_class):
                if isinstance(new_state, dict):
                    new_state = self.state_class(**new_state)
                else:
                    new_state = state  # Use original if handler didn't return state
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                node_name=node.name,
                status=ExecutionStatus.COMPLETED,
                state=new_state,
                next_nodes=self._get_all_next_nodes(node.name, new_state),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"Node execution failed: {node.name}")
            
            return ExecutionResult(
                node_name=node.name,
                status=ExecutionStatus.FAILED,
                state=state,
                next_nodes=[],
                duration_ms=duration_ms,
                error=str(e)
            )
    
    def _get_next_node(self, current: str, state: S) -> Optional[str]:
        """Get the next node to execute"""
        # Get all edges from current node, sorted by priority
        edges = sorted(
            [e for e in self.graph.edges if e.source == current],
            key=lambda e: -e.priority
        )
        
        for edge in edges:
            # Check condition if present
            if edge.condition is None or edge.condition(state):
                return edge.target
        
        return None
    
    def _get_all_next_nodes(self, current: str, state: S) -> List[str]:
        """Get all possible next nodes (for parallel execution)"""
        next_nodes = []
        
        for edge in self.graph.edges:
            if edge.source == current:
                if edge.condition is None or edge.condition(state):
                    next_nodes.append(edge.target)
        
        return next_nodes


# ============ PRE-BUILT GRAPHS ============

def create_rag_graph() -> StateGraph[RAGState]:
    """
    Create a pre-built RAG pipeline graph with CRAG-style correction.
    
    Flow:
    1. Query Reformulation
    2. Retrieval
    3. Relevance Check
    4. Generate or Correct
    """
    graph = StateGraph(RAGState)
    
    # Define node handlers
    async def reformulate_query(state: RAGState) -> RAGState:
        """Optionally reformulate query for better retrieval"""
        # In production, use LLM to reformulate
        state.reformulated_query = state.query
        state.add_message("system", f"Query reformulated: {state.reformulated_query}")
        return state
    
    async def retrieve_chunks(state: RAGState) -> RAGState:
        """Retrieve relevant chunks"""
        # In production, call vector store
        state.add_message("system", f"Retrieved {len(state.retrieved_chunks)} chunks")
        return state
    
    async def check_relevance(state: RAGState) -> RAGState:
        """Check if retrieved chunks are relevant"""
        # In production, use LLM to grade relevance
        if not state.retrieved_chunks:
            state.needs_correction = True
            state.correction_reason = "No chunks retrieved"
        else:
            state.needs_correction = False
            state.filtered_chunks = state.retrieved_chunks
        return state
    
    async def generate_answer(state: RAGState) -> RAGState:
        """Generate answer from chunks"""
        # In production, use LLM to generate
        state.answer = "Generated answer based on context"
        return state
    
    async def correct_query(state: RAGState) -> RAGState:
        """Correct/expand query and retry"""
        state.reformulated_query = f"expanded: {state.query}"
        state.needs_correction = False
        return state
    
    # Add nodes
    graph.add_node("reformulate", reformulate_query)
    graph.add_node("retrieve", retrieve_chunks)
    graph.add_node("check_relevance", check_relevance, node_type=NodeType.ROUTER)
    graph.add_node("generate", generate_answer)
    graph.add_node("correct", correct_query)
    
    # Define routing
    graph.set_entry_point("reformulate")
    graph.add_edge("reformulate", "retrieve")
    graph.add_edge("retrieve", "check_relevance")
    
    # Conditional routing based on relevance
    graph.add_conditional_edges(
        "check_relevance",
        {
            "generate": "generate",
            "correct": "correct"
        },
        lambda s: "correct" if s.needs_correction else "generate"
    )
    
    graph.add_edge("correct", "retrieve")  # Retry after correction
    graph.set_finish("generate")
    
    return graph


def create_conversation_graph() -> StateGraph[ConversationState]:
    """
    Create a conversation handling graph.
    
    Flow:
    1. Intent Classification
    2. Route to appropriate handler (RAG, Tool, Direct)
    3. Generate Response
    4. Check if human needed
    """
    graph = StateGraph(ConversationState)
    
    async def classify_intent(state: ConversationState) -> ConversationState:
        """Classify user intent"""
        # In production, use LLM for classification
        user_input = state.user_input.lower()
        
        if any(w in user_input for w in ["search", "find", "what is", "explain"]):
            state.intent = "rag"
        elif any(w in user_input for w in ["calculate", "convert", "time"]):
            state.intent = "tool"
        else:
            state.intent = "chat"
        
        state.add_message("system", f"Classified intent: {state.intent}")
        return state
    
    async def rag_search(state: ConversationState) -> ConversationState:
        """Perform RAG search"""
        # In production, call RAG pipeline
        state.rag_results = [{"content": "RAG result", "score": 0.9}]
        state.tools_used.append("rag_search")
        return state
    
    async def execute_tool(state: ConversationState) -> ConversationState:
        """Execute requested tool"""
        # In production, call tool system
        state.tools_used.append("calculator")
        state.context["tool_result"] = "Tool executed"
        return state
    
    async def generate_response(state: ConversationState) -> ConversationState:
        """Generate final response"""
        # In production, use LLM
        if state.intent == "rag":
            state.assistant_response = f"Based on my knowledge: {state.rag_results}"
        elif state.intent == "tool":
            state.assistant_response = f"Tool result: {state.context.get('tool_result')}"
        else:
            state.assistant_response = f"Chat response to: {state.user_input}"
        
        state.add_message("assistant", state.assistant_response)
        return state
    
    async def check_confidence(state: ConversationState) -> ConversationState:
        """Check if human review needed"""
        state.requires_human = state.confidence < 0.5
        return state
    
    # Add nodes
    graph.add_node("classify", classify_intent)
    graph.add_node("rag", rag_search)
    graph.add_node("tool", execute_tool)
    graph.add_node("generate", generate_response)
    graph.add_node("check_human", check_confidence, node_type=NodeType.ROUTER)
    graph.add_node("human_review", lambda s: s, node_type=NodeType.HUMAN)
    
    # Set entry and routing
    graph.set_entry_point("classify")
    
    graph.add_conditional_edges(
        "classify",
        {
            "rag": "rag",
            "tool": "tool",
            "chat": "generate"
        },
        lambda s: s.intent or "chat"
    )
    
    graph.add_edge("rag", "generate")
    graph.add_edge("tool", "generate")
    graph.add_edge("generate", "check_human")
    
    graph.add_conditional_edges(
        "check_human",
        {
            "human": "human_review",
            "done": "__end__"
        },
        lambda s: "human" if s.requires_human else "done"
    )
    
    graph.set_finish("human_review")
    
    return graph


# ============ EXPORTS ============

__all__ = [
    # Core types
    "NodeType",
    "ExecutionStatus",
    # State classes
    "AgentState",
    "ConversationState",
    "RAGState",
    "TaskState",
    # Graph classes
    "StateGraph",
    "CompiledGraph",
    "GraphNode",
    "GraphEdge",
    "ExecutionResult",
    # Pre-built graphs
    "create_rag_graph",
    "create_conversation_graph",
]
