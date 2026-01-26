"""
🎓 Curriculum Studio - Multi-Agent AI Curriculum Planning System

Deep Scholar 2.0 tarzı multi-model multi-agent sistem.
5 uzman agent paralel çalışarak kişiselleştirilmiş müfredat oluşturur.

Agents:
- PedagogyAgent: Eğitim bilimi uzmanı
- ResearchAgent: RAG + Web araştırmacı  
- ContentAgent: İçerik tasarımcısı
- ExamAgent: Sınav oluşturucu
- ReviewAgent: Kalite kontrol

Usage:
    from core.learning_journey_v2.curriculum_studio import CurriculumStudioOrchestrator
    
    orchestrator = CurriculumStudioOrchestrator()
    async for thought in orchestrator.create_curriculum(goal):
        print(f"{thought.agent_name}: {thought.thinking}")
"""

from .orchestrator import CurriculumStudioOrchestrator, get_curriculum_studio
from .agents import (
    BaseCurriculumAgent,
    PedagogyAgent,
    ResearchAgent,
    ContentAgent,
    ExamAgent,
    ReviewAgent,
    AgentThought,
    AgentOutput
)

__all__ = [
    "CurriculumStudioOrchestrator",
    "get_curriculum_studio",
    "BaseCurriculumAgent",
    "PedagogyAgent", 
    "ResearchAgent",
    "ContentAgent",
    "ExamAgent",
    "ReviewAgent",
    "AgentThought",
    "AgentOutput"
]
