"""
Enterprise AI Assistant - Base Agent
Endüstri Standartlarında Kurumsal AI Çözümü

Tüm agent'ların temel sınıfı - ortak özellikler ve interface.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

import sys
sys.path.append('..')

from core.llm_manager import llm_manager


class AgentRole(Enum):
    """Agent rolleri."""
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    WRITER = "writer"
    ANALYZER = "analyzer"
    ASSISTANT = "assistant"


@dataclass
class AgentResponse:
    """Agent yanıt yapısı."""
    content: str
    agent_name: str
    agent_role: str
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "sources": self.sources,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class AgentMessage:
    """Agent'lar arası mesaj yapısı."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    message_type: str = "request"  # request, response, status, error
    content: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """
    Temel Agent sınıfı - Endüstri standartlarına uygun.
    
    Tüm agent'lar bu sınıftan türer ve ortak özellikleri paylaşır.
    """
    
    def __init__(
        self,
        name: str,
        role: AgentRole,
        description: str,
        system_prompt: str,
        tools: Optional[List[Any]] = None,
    ):
        self.name = name
        self.role = role
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.memory: List[Dict[str, Any]] = []
        self.max_memory = 10
    
    @abstractmethod
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Görevi çalıştır.
        
        Args:
            task: Yapılacak görev/soru
            context: Ek bağlam bilgisi
            
        Returns:
            AgentResponse
        """
        pass
    
    def think(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        LLM ile düşün ve yanıt üret.
        
        Args:
            task: Görev/soru
            context: Bağlam
            
        Returns:
            LLM yanıtı
        """
        # Build prompt
        prompt = self._build_prompt(task, context)
        
        # Generate response
        response = llm_manager.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.7,
        )
        
        # Add to memory
        self._add_to_memory(task, response)
        
        return response
    
    def _build_prompt(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Prompt oluştur."""
        parts = []
        
        # Add context if provided
        if context:
            if "documents" in context:
                parts.append("=== İLGİLİ DÖKÜMANLAR ===")
                parts.append(context["documents"])
                parts.append("")
            
            if "previous_results" in context:
                parts.append("=== ÖNCEKİ SONUÇLAR ===")
                parts.append(str(context["previous_results"]))
                parts.append("")
        
        # Add memory context
        if self.memory:
            parts.append("=== SON KONUŞMALAR ===")
            for mem in self.memory[-3:]:  # Last 3 interactions
                parts.append(f"Görev: {mem['task']}")
                parts.append(f"Yanıt: {mem['response'][:200]}...")
            parts.append("")
        
        # Add task
        parts.append("=== GÖREV ===")
        parts.append(task)
        
        return "\n".join(parts)
    
    def _add_to_memory(self, task: str, response: str) -> None:
        """Belleğe ekle."""
        self.memory.append({
            "task": task,
            "response": response,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Limit memory size
        if len(self.memory) > self.max_memory:
            self.memory = self.memory[-self.max_memory:]
    
    def clear_memory(self) -> None:
        """Belleği temizle."""
        self.memory = []
    
    def get_available_tools(self) -> List[str]:
        """Kullanılabilir tool listesi."""
        return [tool.name for tool in self.tools]
    
    def use_tool(self, tool_name: str, **kwargs) -> Any:
        """Tool kullan."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.execute(**kwargs)
        raise ValueError(f"Tool bulunamadı: {tool_name}")
    
    def receive_message(self, message: AgentMessage) -> AgentMessage:
        """
        Başka agent'tan mesaj al ve yanıtla.
        
        Args:
            message: Gelen mesaj
            
        Returns:
            Yanıt mesajı
        """
        if message.message_type == "request":
            task = message.content.get("task", "")
            context = message.content.get("context")
            
            response = self.execute(task, context)
            
            return AgentMessage(
                sender=self.name,
                recipient=message.sender,
                message_type="response",
                content={
                    "response": response.to_dict(),
                    "original_message_id": message.message_id,
                },
            )
        
        return AgentMessage(
            sender=self.name,
            recipient=message.sender,
            message_type="error",
            content={"error": f"Desteklenmeyen mesaj tipi: {message.message_type}"},
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Agent durumu."""
        return {
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "tools": self.get_available_tools(),
            "memory_size": len(self.memory),
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, role={self.role.value})"
