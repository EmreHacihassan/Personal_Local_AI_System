"""
🎭 Curriculum Studio Orchestrator

Multi-Agent Müfredat Üretim Sistemi
5 uzman agent ile kapsamlı, aşamalı düşünme süreciyle
yüksek kaliteli öğrenme yolculuğu oluşturur.

Agents:
1. 📚 Pedagogy Agent - Bloom taksonomisi, öğrenme stilleri
2. 🔍 Research Agent - RAG, kaynak araştırması
3. 🎨 Content Agent - Multimedya, AI video planlama
4. 📋 Exam Agent - Sınav stratejisi, aralıklı tekrar
5. 🔬 Review Agent - Kalite kontrol, onay

Özellikler:
- Gerçek zamanlı streaming thoughts
- 30-120 saniye derin düşünme
- Multi-model fallback
- Görünür reasoning süreci
"""

import asyncio
from typing import Dict, Any, AsyncGenerator, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from .agents.base_agent import AgentThought, ThinkingPhase
from .agents.pedagogy_agent import PedagogyAgent
from .agents.research_agent import ResearchAgent
from .agents.content_agent import ContentAgent
from .agents.exam_agent import ExamAgent
from .agents.review_agent import ReviewAgent


@dataclass
class OrchestrationProgress:
    """Orkestrasyon ilerleme durumu"""
    total_agents: int = 5
    completed_agents: int = 0
    current_agent: str = ""
    current_step: str = ""
    elapsed_seconds: float = 0.0
    estimated_remaining: float = 0.0
    thoughts: List[AgentThought] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CurriculumResult:
    """Final müfredat sonucu"""
    success: bool
    curriculum_plan: Optional[Dict[str, Any]]
    quality_score: float
    total_thinking_time: float
    agent_contributions: Dict[str, Any]
    recommendations: List[str]
    all_thoughts: List[AgentThought]


class CurriculumStudioOrchestrator:
    """
    Multi-Agent Curriculum Studio Orchestrator
    
    5 uzman agent'ı koordine eder ve gerçek zamanlı
    streaming thoughts ile yüksek kaliteli müfredat üretir.
    """
    
    def __init__(self, llm_service=None, rag_engine=None):
        """
        Args:
            llm_service: LLM service instance
            rag_engine: RAG engine instance
        """
        self.llm_service = llm_service
        self.rag_engine = rag_engine
        
        # Agent'ları oluştur
        self.pedagogy_agent = PedagogyAgent()
        self.research_agent = ResearchAgent()
        self.content_agent = ContentAgent()
        self.exam_agent = ExamAgent()
        self.review_agent = ReviewAgent()
        
        self.agents = [
            self.pedagogy_agent,
            self.research_agent,
            self.content_agent,
            self.exam_agent,
            self.review_agent
        ]
        
        # LLM service ve RAG engine'i agent'lara bağla
        for agent in self.agents:
            agent.llm_service = llm_service
            if isinstance(agent, ResearchAgent) and self.rag_engine:
                agent.rag_engine = rag_engine
        
        self.start_time: Optional[datetime] = None
    
    async def generate_curriculum(
        self,
        goal: Any,
        user_id: str = "",
        stream_thoughts: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Multi-agent müfredat üretimi
        
        Yields:
            Dict with either:
            - {"type": "thought", "thought": AgentThought}
            - {"type": "progress", "progress": OrchestrationProgress}
            - {"type": "result", "result": CurriculumResult}
        """
        self.start_time = datetime.now()
        
        # Shared context
        context: Dict[str, Any] = {
            "goal": goal,
            "user_id": user_id,
            "start_time": self.start_time.isoformat()
        }
        
        all_thoughts: List[AgentThought] = []
        agent_contributions: Dict[str, Any] = {}
        
        # Opening message
        yield {
            "type": "thought",
            "thought": AgentThought(
                agent_name="Curriculum Studio",
                agent_icon="🎭",
                step="baslangic",
                phase=ThinkingPhase.ANALYZING,
                thinking="🎭 Multi-Agent Curriculum Studio başlatılıyor...",
                reasoning=f"'{goal.topic if hasattr(goal, 'topic') else goal}' için kapsamlı müfredat oluşturuluyor.",
                is_streaming=True
            )
        }
        
        await asyncio.sleep(0.5)
        
        yield {
            "type": "thought",
            "thought": AgentThought(
                agent_name="Curriculum Studio",
                agent_icon="🎭",
                step="agent_tanitim",
                phase=ThinkingPhase.ANALYZING,
                thinking="5 uzman agent sırayla çalışacak:",
                evidence=[
                    "📚 Pedagogy Agent - Eğitim stratejisi",
                    "🔍 Research Agent - Kaynak araştırması", 
                    "🎨 Content Agent - İçerik planlaması",
                    "📋 Exam Agent - Sınav sistemi",
                    "🔬 Review Agent - Kalite kontrol"
                ],
                is_streaming=True
            )
        }
        
        await asyncio.sleep(1.0)
        
        # Her agent'ı sırayla çalıştır
        for i, agent in enumerate(self.agents):
            agent_name = agent.name
            agent_icon = getattr(agent, 'icon', '🤖')
            
            # Agent başlangıç
            yield {
                "type": "progress",
                "progress": {
                    "total_agents": len(self.agents),
                    "completed_agents": i,
                    "current_agent": agent_name,
                    "current_step": "baslangic",
                    "elapsed_seconds": (datetime.now() - self.start_time).total_seconds()
                }
            }
            
            # Agent'ı çalıştır
            agent_thoughts = []
            async for thought in agent.execute(context):
                all_thoughts.append(thought)
                agent_thoughts.append(thought)
                
                if stream_thoughts:
                    yield {
                        "type": "thought",
                        "thought": thought
                    }
            
            # Agent sonuçlarını kaydet
            agent_contributions[agent_name] = {
                "thought_count": len(agent_thoughts),
                "final_confidence": agent_thoughts[-1].confidence if agent_thoughts else 0.8,
                "steps_completed": list(set(t.step for t in agent_thoughts))
            }
        
        # Toplam süre
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        # Quality score
        quality_review = context.get("quality_review", {})
        quality_score = quality_review.get("final_score", 0.85)
        
        # Final curriculum plan oluştur
        curriculum_plan = self._build_curriculum_plan(context, goal)
        
        # Final result
        result = CurriculumResult(
            success=quality_score >= 0.75,
            curriculum_plan=curriculum_plan,
            quality_score=quality_score,
            total_thinking_time=total_time,
            agent_contributions=agent_contributions,
            recommendations=quality_review.get("recommendations", []),
            all_thoughts=all_thoughts
        )
        
        # Final thought
        yield {
            "type": "thought",
            "thought": AgentThought(
                agent_name="Curriculum Studio",
                agent_icon="🎭",
                step="tamamlandi",
                phase=ThinkingPhase.CONCLUDING,
                thinking=f"✅ Müfredat üretimi tamamlandı!",
                reasoning=f"Toplam {total_time:.1f} saniye sürdü.",
                conclusion=f"Kalite skoru: %{int(quality_score * 100)}",
                evidence=[
                    f"✓ {len(self.agents)} agent çalıştı",
                    f"✓ {len(all_thoughts)} düşünce adımı",
                    f"✓ {curriculum_plan.get('stage_count', 0)} aşama oluşturuldu"
                ],
                confidence=quality_score,
                is_complete=True
            )
        }
        
        yield {
            "type": "result",
            "result": {
                "success": result.success,
                "curriculum_plan": result.curriculum_plan,
                "quality_score": result.quality_score,
                "total_thinking_time": result.total_thinking_time,
                "agent_contributions": result.agent_contributions,
                "recommendations": result.recommendations
            }
        }
    
    def _build_curriculum_plan(
        self, 
        context: Dict[str, Any], 
        goal: Any
    ) -> Dict[str, Any]:
        """Context'ten curriculum plan oluştur"""
        
        # Goal bilgileri
        topic = goal.topic if hasattr(goal, 'topic') else str(goal)
        target_level = goal.target_level if hasattr(goal, 'target_level') else "intermediate"
        daily_hours = goal.daily_hours if hasattr(goal, 'daily_hours') else 2
        
        # Agent sonuçlarından veri topla
        pedagogy = context.get("pedagogy_result", {})
        research = context.get("research_result", {})
        content_plan = context.get("content_plan", {})
        exam_plan = context.get("exam_plan", {})
        quality = context.get("quality_review", {})
        
        # Aşama sayısı hesapla
        bloom_level = pedagogy.get("bloom_level", "applying")
        stage_count = self._calculate_stage_count(bloom_level, target_level)
        
        # Package sayısı
        packages_per_stage = content_plan.get("packages_per_stage", 3)
        total_packages = stage_count * packages_per_stage
        
        return {
            "topic": topic,
            "target_level": target_level,
            "bloom_level": bloom_level,
            "stage_count": stage_count,
            "packages_per_stage": packages_per_stage,
            "total_packages": total_packages,
            "daily_hours": daily_hours,
            
            # Pedagogy
            "learning_style": pedagogy.get("learning_style", "multimodal"),
            "prerequisites": pedagogy.get("prerequisites", []),
            "topic_sequence": pedagogy.get("topic_sequence", []),
            
            # Content
            "content_types": content_plan.get("content_types", ["text", "video"]),
            "ai_video_planned": content_plan.get("ai_video_planned", False),
            "interactive_count": content_plan.get("interactive_count", 0),
            
            # Exam
            "exam_strategy": exam_plan.get("strategy", "progressive"),
            "spaced_repetition": exam_plan.get("spaced_repetition", {}),
            "stage_closure": exam_plan.get("stage_closure", {}),
            "question_types": exam_plan.get("question_types", []),
            
            # Quality
            "quality_score": quality.get("final_score", 0.85),
            "recommendations": quality.get("recommendations", []),
            
            # Research
            "sources": research.get("sources", []),
            "video_resources": research.get("video_resources", [])
        }
    
    def _calculate_stage_count(
        self, 
        bloom_level: str, 
        target_level: str
    ) -> int:
        """Bloom ve hedef seviyeye göre aşama sayısı hesapla"""
        
        bloom_stages = {
            "remembering": 2,
            "understanding": 3,
            "applying": 4,
            "analyzing": 5,
            "evaluating": 5,
            "creating": 6
        }
        
        level_multiplier = {
            "beginner": 0.8,
            "intermediate": 1.0,
            "advanced": 1.2,
            "expert": 1.4
        }
        
        base = bloom_stages.get(bloom_level, 4)
        mult = level_multiplier.get(target_level, 1.0)
        
        return max(2, min(8, int(base * mult)))


# ==================== CONVENIENCE FUNCTIONS ====================

_curriculum_studio_instance: Optional["CurriculumStudioOrchestrator"] = None


def get_curriculum_studio(llm_service=None, rag_engine=None) -> "CurriculumStudioOrchestrator":
    """Get or create singleton curriculum studio instance"""
    global _curriculum_studio_instance
    if _curriculum_studio_instance is None:
        _curriculum_studio_instance = CurriculumStudioOrchestrator(
            llm_service=llm_service,
            rag_engine=rag_engine
        )
    return _curriculum_studio_instance


async def create_curriculum_with_studio(
    goal: Any,
    llm_service=None,
    rag_engine=None,
    user_id: str = ""
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Convenience function to create curriculum with studio
    
    Usage:
        async for event in create_curriculum_with_studio(goal, llm_service):
            if event["type"] == "thought":
                # Stream thought to frontend
                pass
            elif event["type"] == "result":
                # Handle final result
                pass
    """
    orchestrator = CurriculumStudioOrchestrator(
        llm_service=llm_service,
        rag_engine=rag_engine
    )
    
    async for event in orchestrator.generate_curriculum(goal, user_id):
        yield event
