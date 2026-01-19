"""
Enterprise AI Assistant - Orchestrator
Endüstri Standartlarında Kurumsal AI Çözümü

Merkez yönetici - görev analizi, agent routing, sonuç birleştirme.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .base_agent import BaseAgent, AgentRole, AgentResponse, AgentMessage
from .research_agent import ResearchAgent
from .writer_agent import WriterAgent
from .analyzer_agent import AnalyzerAgent
from .assistant_agent import AssistantAgent

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_manager import llm_manager


class TaskType(Enum):
    """Görev tipleri."""
    QUESTION = "question"           # Soru-cevap
    RESEARCH = "research"           # Araştırma
    WRITE = "write"                 # Yazma
    ANALYZE = "analyze"             # Analiz
    MULTI_STEP = "multi_step"       # Çok adımlı
    CHAT = "chat"                   # Genel sohbet


@dataclass
class TaskPlan:
    """Görev planı."""
    task_type: TaskType
    steps: List[Dict[str, Any]]
    estimated_agents: List[str]


class Orchestrator(BaseAgent):
    """
    Orchestrator - Merkez yönetici agent.
    
    Sorumluluklar:
    - Gelen görevi analiz etme
    - Uygun agent'a yönlendirme
    - Çoklu agent koordinasyonu
    - Sonuçları birleştirme
    """
    
    SYSTEM_PROMPT = """Sen AI asistan sisteminin merkez yöneticisisin. Görevin kullanıcı taleplerini analiz etmek ve doğru uzmanlara yönlendirmek.

AGENT'LAR:
1. Research Agent: Bilgi arama, kaynak bulma
2. Writer Agent: İçerik yazma, email, rapor
3. Analyzer Agent: Veri analizi, karşılaştırma, özet
4. Assistant Agent: Genel sorular, yardım

GÖREV ANALİZİ:
- Basit sorular → Assistant Agent
- Bilgi araması → Research Agent
- Yazma işleri → Writer Agent (Research sonrası)
- Analiz işleri → Analyzer Agent (Research sonrası)
- Karmaşık görevler → Çoklu agent koordinasyonu"""
    
    def __init__(self):
        super().__init__(
            name="Orchestrator",
            role=AgentRole.ORCHESTRATOR,
            description="Görevleri analiz eder ve uygun agent'lara yönlendirir",
            system_prompt=self.SYSTEM_PROMPT,
        )
        
        # Initialize agents
        self.research_agent = ResearchAgent()
        self.writer_agent = WriterAgent()
        self.analyzer_agent = AnalyzerAgent()
        self.assistant_agent = AssistantAgent()
        
        self.agents = {
            "research": self.research_agent,
            "writer": self.writer_agent,
            "analyzer": self.analyzer_agent,
            "assistant": self.assistant_agent,
        }
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Ana çalıştırma metodu.
        
        Args:
            task: Kullanıcı görevi/sorusu
            context: Ek bağlam
            
        Returns:
            AgentResponse
        """
        try:
            # Analyze task
            task_plan = self._analyze_task(task)
            
            # Execute based on task type
            if task_plan.task_type == TaskType.CHAT:
                return self.assistant_agent.execute(task, context)
            
            elif task_plan.task_type == TaskType.QUESTION:
                return self._handle_question(task, context)
            
            elif task_plan.task_type == TaskType.RESEARCH:
                return self.research_agent.execute(task, context)
            
            elif task_plan.task_type == TaskType.WRITE:
                return self._handle_writing(task, context)
            
            elif task_plan.task_type == TaskType.ANALYZE:
                return self._handle_analysis(task, context)
            
            elif task_plan.task_type == TaskType.MULTI_STEP:
                return self._handle_multi_step(task, task_plan, context)
            
            else:
                return self.assistant_agent.execute(task, context)
                
        except Exception as e:
            return AgentResponse(
                content=f"Görev işlenirken bir hata oluştu: {str(e)}",
                agent_name=self.name,
                agent_role=self.role.value,
                success=False,
                error=str(e),
            )
    
    def _analyze_task(self, task: str) -> TaskPlan:
        """Görevi analiz et ve plan oluştur."""
        task_lower = task.lower()
        
        # Writing indicators
        write_keywords = [
            "yaz", "hazırla", "oluştur", "taslak", "email", "mail",
            "rapor", "döküman", "metin", "write", "draft", "create",
            "prepare", "compose",
        ]
        
        # Analysis indicators
        analyze_keywords = [
            "analiz", "karşılaştır", "özetle", "incele", "değerlendir",
            "analyze", "compare", "summarize", "evaluate", "assess",
            "trend", "risk",
        ]
        
        # Research indicators
        research_keywords = [
            "ara", "bul", "getir", "listele", "hangi", "kaç",
            "search", "find", "list", "what", "which", "how many",
        ]
        
        # Multi-step indicators
        multi_step_keywords = [
            " ve ", " sonra ", " ardından ", " önce ",
            " and ", " then ", " after ", " before ",
        ]
        
        # Chat/greeting indicators
        chat_keywords = [
            "merhaba", "selam", "nasılsın", "teşekkür",
            "hello", "hi", "thanks", "bye",
        ]
        
        # Determine task type
        if any(kw in task_lower for kw in chat_keywords) and len(task.split()) <= 5:
            return TaskPlan(TaskType.CHAT, [], ["assistant"])
        
        # Check for multi-step
        is_multi_step = any(kw in task_lower for kw in multi_step_keywords)
        has_write = any(kw in task_lower for kw in write_keywords)
        has_analyze = any(kw in task_lower for kw in analyze_keywords)
        has_research = any(kw in task_lower for kw in research_keywords)
        
        if is_multi_step or (has_write and (has_analyze or has_research)):
            return self._create_multi_step_plan(task, has_research, has_analyze, has_write)
        
        if has_write:
            return TaskPlan(TaskType.WRITE, [], ["writer"])
        
        if has_analyze:
            return TaskPlan(TaskType.ANALYZE, [], ["analyzer"])
        
        if has_research:
            return TaskPlan(TaskType.RESEARCH, [], ["research"])
        
        # Default to question
        return TaskPlan(TaskType.QUESTION, [], ["assistant", "research"])
    
    def _create_multi_step_plan(
        self,
        task: str,
        needs_research: bool,
        needs_analysis: bool,
        needs_writing: bool,
    ) -> TaskPlan:
        """Çok adımlı görev planı oluştur."""
        steps = []
        agents = []
        
        if needs_research:
            steps.append({"agent": "research", "task": "Gerekli bilgileri topla"})
            agents.append("research")
        
        if needs_analysis:
            steps.append({"agent": "analyzer", "task": "Bilgileri analiz et"})
            agents.append("analyzer")
        
        if needs_writing:
            steps.append({"agent": "writer", "task": "İçerik oluştur"})
            agents.append("writer")
        
        return TaskPlan(TaskType.MULTI_STEP, steps, agents)
    
    def _handle_question(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Soru-cevap işle."""
        # First try assistant (with RAG)
        response = self.assistant_agent.execute(task, context)
        
        # If no good answer, try research
        if not response.sources:
            research_response = self.research_agent.execute(task, context)
            if research_response.sources:
                return research_response
        
        return response
    
    def _handle_writing(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Yazma görevi işle."""
        # Check if we need research first
        if self._needs_research_for_writing(task):
            # Get relevant information
            research_response = self.research_agent.execute(task, context)
            
            # Pass to writer with context
            write_context = context or {}
            write_context["previous_results"] = research_response.content
            write_context["sources"] = research_response.sources
            
            writer_response = self.writer_agent.execute(task, write_context)
            writer_response.sources = research_response.sources
            return writer_response
        
        return self.writer_agent.execute(task, context)
    
    def _handle_analysis(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Analiz görevi işle."""
        # Check if we need to fetch documents first
        if self._needs_research_for_analysis(task):
            research_response = self.research_agent.execute(task, context)
            
            analyze_context = context or {}
            analyze_context["documents"] = research_response.content
            analyze_context["sources"] = research_response.sources
            
            analyzer_response = self.analyzer_agent.execute(task, analyze_context)
            analyzer_response.sources = research_response.sources
            return analyzer_response
        
        return self.analyzer_agent.execute(task, context)
    
    def _handle_multi_step(
        self,
        task: str,
        plan: TaskPlan,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentResponse:
        """Çok adımlı görevi işle."""
        results = []
        sources = []
        current_context = context or {}
        
        for step in plan.steps:
            agent_name = step["agent"]
            agent = self.agents.get(agent_name)
            
            if not agent:
                continue
            
            # Execute step
            response = agent.execute(task, current_context)
            results.append({
                "agent": agent_name,
                "response": response.content,
            })
            
            # Update context for next step
            current_context["previous_results"] = response.content
            sources.extend(response.sources)
        
        # Return final result (last agent's output)
        final_content = results[-1]["response"] if results else "Görev tamamlanamadı."
        
        return AgentResponse(
            content=final_content,
            agent_name=self.name,
            agent_role=self.role.value,
            sources=list(set(sources)),
            metadata={
                "task_type": "multi_step",
                "steps_completed": len(results),
                "agents_used": [r["agent"] for r in results],
            },
        )
    
    def _needs_research_for_writing(self, task: str) -> bool:
        """Yazma için araştırma gerekip gerekmediğini belirle."""
        keywords = ["hakkında", "ile ilgili", "about", "regarding", "based on"]
        return any(kw in task.lower() for kw in keywords)
    
    def _needs_research_for_analysis(self, task: str) -> bool:
        """Analiz için araştırma gerekip gerekmediğini belirle."""
        # If specific document mentioned, need to fetch it
        keywords = ["rapor", "döküman", "dosya", "report", "document", "file"]
        return any(kw in task.lower() for kw in keywords)
    
    def get_agents_status(self) -> Dict[str, Any]:
        """Tüm agent'ların durumunu döndür."""
        return {
            name: agent.get_status()
            for name, agent in self.agents.items()
        }


# Singleton instance
orchestrator = Orchestrator()
