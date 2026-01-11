"""
Enterprise AI Assistant - LangGraph Workflow Engine
Durum makinesi tabanlı akış yönetimi

LangGraph benzeri state machine workflow.
"""

from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod


class NodeType(str, Enum):
    """Düğüm türleri."""
    START = "start"
    END = "end"
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    PARALLEL = "parallel"
    HUMAN_IN_LOOP = "human_in_loop"


@dataclass
class WorkflowState:
    """Workflow durumu."""
    current_node: str
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_complete: bool = False
    is_paused: bool = False
    pause_reason: str = ""
    
    def update(self, key: str, value: Any):
        """State güncelle."""
        self.data[key] = value
        self.updated_at = datetime.now()
    
    def get(self, key: str, default: Any = None) -> Any:
        """State değeri al."""
        return self.data.get(key, default)
    
    def add_to_history(self, node: str, result: Any):
        """Geçmişe ekle."""
        self.history.append({
            "node": node,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })


@dataclass
class Node:
    """Workflow düğümü."""
    name: str
    node_type: NodeType
    handler: Optional[Callable] = None
    next_nodes: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None  # For conditional routing
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowBuilder:
    """Workflow oluşturucu."""
    
    def __init__(self, name: str):
        """Builder başlat."""
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[str]] = {}
        self.conditional_edges: Dict[str, Callable] = {}
        
        # Add start and end nodes
        self.add_node("__start__", NodeType.START)
        self.add_node("__end__", NodeType.END)
    
    def add_node(
        self,
        name: str,
        node_type: NodeType = NodeType.AGENT,
        handler: Callable = None,
    ) -> "WorkflowBuilder":
        """Düğüm ekle."""
        self.nodes[name] = Node(
            name=name,
            node_type=node_type,
            handler=handler,
        )
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> "WorkflowBuilder":
        """Kenar ekle."""
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        return self
    
    def add_conditional_edge(
        self,
        from_node: str,
        condition: Callable[[WorkflowState], str],
    ) -> "WorkflowBuilder":
        """
        Koşullu kenar ekle.
        
        condition fonksiyonu state alır ve hedef node adını döndürür.
        """
        self.conditional_edges[from_node] = condition
        return self
    
    def set_entry_point(self, node: str) -> "WorkflowBuilder":
        """Giriş noktası belirle."""
        self.add_edge("__start__", node)
        return self
    
    def set_finish_point(self, node: str) -> "WorkflowBuilder":
        """Bitiş noktası belirle."""
        self.add_edge(node, "__end__")
        return self
    
    def build(self) -> "Workflow":
        """Workflow oluştur."""
        return Workflow(
            name=self.name,
            nodes=self.nodes,
            edges=self.edges,
            conditional_edges=self.conditional_edges,
        )


class Workflow:
    """Çalıştırılabilir workflow."""
    
    def __init__(
        self,
        name: str,
        nodes: Dict[str, Node],
        edges: Dict[str, List[str]],
        conditional_edges: Dict[str, Callable],
    ):
        """Workflow başlat."""
        self.name = name
        self.nodes = nodes
        self.edges = edges
        self.conditional_edges = conditional_edges
    
    async def run(
        self,
        initial_state: Dict[str, Any] = None,
        max_iterations: int = 100,
    ) -> WorkflowState:
        """
        Workflow çalıştır.
        
        Args:
            initial_state: Başlangıç durumu
            max_iterations: Maksimum iterasyon
            
        Returns:
            Son durum
        """
        state = WorkflowState(
            current_node="__start__",
            data=initial_state or {},
        )
        
        iterations = 0
        
        while not state.is_complete and iterations < max_iterations:
            iterations += 1
            
            # Get current node
            current = self.nodes.get(state.current_node)
            if not current:
                state.errors.append(f"Node not found: {state.current_node}")
                break
            
            # Check for pause
            if state.is_paused:
                break
            
            # Execute node
            if current.handler:
                try:
                    if asyncio.iscoroutinefunction(current.handler):
                        result = await current.handler(state)
                    else:
                        result = current.handler(state)
                    
                    state.add_to_history(current.name, result)
                except Exception as e:
                    state.errors.append(f"Error in {current.name}: {str(e)}")
                    break
            
            # Determine next node
            next_node = self._get_next_node(state)
            
            if next_node == "__end__":
                state.is_complete = True
            elif next_node:
                state.current_node = next_node
            else:
                state.errors.append(f"No next node from {state.current_node}")
                break
        
        return state
    
    def _get_next_node(self, state: WorkflowState) -> Optional[str]:
        """Sonraki düğümü belirle."""
        current = state.current_node
        
        # Check conditional edges first
        if current in self.conditional_edges:
            condition = self.conditional_edges[current]
            return condition(state)
        
        # Check regular edges
        if current in self.edges and self.edges[current]:
            return self.edges[current][0]
        
        return None
    
    def run_sync(
        self,
        initial_state: Dict[str, Any] = None,
        max_iterations: int = 100,
    ) -> WorkflowState:
        """Senkron çalıştır."""
        return asyncio.run(self.run(initial_state, max_iterations))


# ============ PRESET WORKFLOWS ============

def create_rag_workflow() -> Workflow:
    """RAG workflow oluştur."""
    
    def retrieve_handler(state: WorkflowState) -> Dict:
        """Retrieval adımı."""
        from rag.advanced_rag import advanced_rag
        
        query = state.get("query", "")
        results = advanced_rag.retrieve(query)
        state.update("retrieved_docs", results)
        return {"retrieved": len(results)}
    
    def generate_handler(state: WorkflowState) -> Dict:
        """Generation adımı."""
        from core.llm_manager import llm_manager
        
        query = state.get("query", "")
        docs = state.get("retrieved_docs", [])
        
        context = "\n\n".join([d.content for d in docs[:5]])
        
        prompt = f"""Bağlam:
{context}

Soru: {query}

Cevap:"""
        
        response = llm_manager.generate(prompt)
        state.update("response", response)
        return {"response_length": len(response)}
    
    def route_by_docs(state: WorkflowState) -> str:
        """Döküman sayısına göre yönlendir."""
        docs = state.get("retrieved_docs", [])
        if len(docs) == 0:
            return "fallback"
        return "generate"
    
    def fallback_handler(state: WorkflowState) -> Dict:
        """Döküman bulunamadığında."""
        state.update("response", "İlgili bilgi bulunamadı.")
        return {"fallback": True}
    
    builder = WorkflowBuilder("rag_workflow")
    
    builder.add_node("retrieve", NodeType.TOOL, retrieve_handler)
    builder.add_node("generate", NodeType.AGENT, generate_handler)
    builder.add_node("fallback", NodeType.AGENT, fallback_handler)
    
    builder.set_entry_point("retrieve")
    builder.add_conditional_edge("retrieve", route_by_docs)
    builder.set_finish_point("generate")
    builder.set_finish_point("fallback")
    
    return builder.build()


def create_agent_workflow() -> Workflow:
    """Multi-agent workflow oluştur."""
    
    def classify_handler(state: WorkflowState) -> Dict:
        """Görevi sınıflandır."""
        query = state.get("query", "").lower()
        
        if any(w in query for w in ["yaz", "oluştur", "hazırla", "email"]):
            state.update("agent_type", "writer")
        elif any(w in query for w in ["analiz", "karşılaştır", "özetle"]):
            state.update("agent_type", "analyzer")
        elif any(w in query for w in ["ara", "bul", "bilgi"]):
            state.update("agent_type", "research")
        else:
            state.update("agent_type", "assistant")
        
        return {"agent": state.get("agent_type")}
    
    def route_to_agent(state: WorkflowState) -> str:
        """Agent'a yönlendir."""
        return state.get("agent_type", "assistant")
    
    def writer_handler(state: WorkflowState) -> Dict:
        """Writer agent."""
        from agents.writer_agent import writer_agent
        result = writer_agent.execute(state.get("query", ""))
        state.update("response", result.content)
        return {"agent": "writer"}
    
    def analyzer_handler(state: WorkflowState) -> Dict:
        """Analyzer agent."""
        from agents.analyzer_agent import analyzer_agent
        result = analyzer_agent.execute(state.get("query", ""))
        state.update("response", result.content)
        return {"agent": "analyzer"}
    
    def research_handler(state: WorkflowState) -> Dict:
        """Research agent."""
        from agents.research_agent import research_agent
        result = research_agent.execute(state.get("query", ""))
        state.update("response", result.content)
        return {"agent": "research"}
    
    def assistant_handler(state: WorkflowState) -> Dict:
        """Assistant agent."""
        from agents.assistant_agent import assistant_agent
        result = assistant_agent.execute(state.get("query", ""))
        state.update("response", result.content)
        return {"agent": "assistant"}
    
    builder = WorkflowBuilder("agent_workflow")
    
    builder.add_node("classify", NodeType.CONDITION, classify_handler)
    builder.add_node("writer", NodeType.AGENT, writer_handler)
    builder.add_node("analyzer", NodeType.AGENT, analyzer_handler)
    builder.add_node("research", NodeType.AGENT, research_handler)
    builder.add_node("assistant", NodeType.AGENT, assistant_handler)
    
    builder.set_entry_point("classify")
    builder.add_conditional_edge("classify", route_to_agent)
    
    for agent in ["writer", "analyzer", "research", "assistant"]:
        builder.set_finish_point(agent)
    
    return builder.build()


# Preset workflows
rag_workflow = create_rag_workflow()
agent_workflow = create_agent_workflow()
