"""
MultiAgentDebate - Çok Ajanlı Tartışma Sistemi
==============================================

Farklı perspektiflerden konuyu inceleyen ajanlar arası tartışma.

Ajanlar:
- ProAgent: Konunun olumlu yönlerini savunur
- ConAgent: Konunun olumsuz/riskli yönlerini belirtir
- DevilsAdvocate: Karşıt görüşleri test eder
- ConsensusBuilder: Tartışmayı sentezler

Özellikler:
- Perspektif çeşitliliği
- Balanced synthesis
- Conflict resolution
- Evidence-based argumentation
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from datetime import datetime
from enum import Enum
import json
import re

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("multi_agent_debate")


class DebateRole(str, Enum):
    """Tartışma rolleri."""
    PRO = "pro"
    CON = "con"
    DEVILS_ADVOCATE = "devils_advocate"
    CONSENSUS_BUILDER = "consensus_builder"
    MODERATOR = "moderator"
    FACT_CHECKER = "fact_checker"


class ArgumentStrength(str, Enum):
    """Argüman gücü."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    OVERWHELMING = "overwhelming"


@dataclass
class Argument:
    """Tartışma argümanı."""
    id: str
    role: DebateRole
    claim: str
    evidence: List[str]
    strength: ArgumentStrength
    counter_to: Optional[str] = None  # Karşı olduğu argüman ID
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "claim": self.claim,
            "evidence": self.evidence,
            "strength": self.strength.value,
            "counter_to": self.counter_to,
            "timestamp": self.timestamp
        }


@dataclass
class DebateRound:
    """Tartışma turu."""
    round_number: int
    topic_focus: str
    arguments: List[Argument]
    consensus_reached: bool = False
    consensus_statement: Optional[str] = None


@dataclass
class DebateSynthesis:
    """Tartışma sentezi."""
    main_conclusion: str
    pro_points: List[str]
    con_points: List[str]
    balanced_view: str
    recommendations: List[str]
    confidence_score: float
    evidence_quality: str


class DebateAgent:
    """
    Tartışma Ajanı - Belirli bir perspektiften argüman üretir.
    """
    
    ROLE_PROMPTS = {
        DebateRole.PRO: """Sen bir "Pro" ajanısın. Verilen konunun OLUMLU yönlerini, 
faydalarını ve avantajlarını savunursun. Kanıt odaklı, ikna edici argümanlar üret.
Her zaman yapıcı ve destekleyici ol.""",
        
        DebateRole.CON: """Sen bir "Con" ajanısın. Verilen konunun OLUMSUZ yönlerini, 
risklerini ve dezavantajlarını belirt. Eleştirel düşün ama adil ol.
Gerçek endişeleri ve potansiyel sorunları vurgula.""",
        
        DebateRole.DEVILS_ADVOCATE: """Sen bir "Şeytan'ın Avukatı" ajanısın. 
Hakim görüşleri sorgula, varsayımları test et, alternatif senaryoları sun.
Provokatif ama yapıcı ol. Düşünce deneylerini kullan.""",
        
        DebateRole.FACT_CHECKER: """Sen bir "Fact Checker" ajanısın.
İddiaları doğrula, kanıtları değerlendir, yanlış bilgileri düzelt.
Tarafsız ve kanıt odaklı ol.""",
        
        DebateRole.MODERATOR: """Sen bir "Moderatör" ajanısın.
Tartışmayı yönet, dengeyi koru, önemli noktaları özetle.
Her görüşe adil davran."""
    }
    
    def __init__(self, role: DebateRole, persona: Optional[str] = None):
        self.role = role
        self.persona = persona or self.ROLE_PROMPTS.get(role, "")
        self.arguments_made: List[Argument] = []
        self.argument_counter = 0
    
    async def generate_argument(
        self,
        topic: str,
        context: str,
        previous_arguments: List[Argument],
        focus_area: Optional[str] = None
    ) -> Argument:
        """
        Argüman üret.
        
        Args:
            topic: Tartışma konusu
            context: Bağlam bilgisi
            previous_arguments: Önceki argümanlar
            focus_area: Odak alanı
        
        Returns:
            Argument objesi
        """
        prev_args_text = "\n".join([
            f"[{a.role.value}] {a.claim}" 
            for a in previous_arguments[-5:]
        ]) if previous_arguments else "Henüz argüman yok."
        
        prompt = f"""{self.persona}

Konu: {topic}

Bağlam:
{context[:1000]}

Önceki Argümanlar:
{prev_args_text}

{f"Odak Alanı: {focus_area}" if focus_area else ""}

Görev: Bu konu hakkında {self.role.value} perspektifinden tek bir güçlü argüman üret.

JSON formatında yanıt ver:
{{
    "claim": "Ana iddia (1-2 cümle)",
    "evidence": ["kanıt1", "kanıt2", "kanıt3"],
    "strength": "weak|moderate|strong|overwhelming",
    "counter_to_previous": true/false
}}
"""
        
        try:
            response = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # JSON çıkar
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                self.argument_counter += 1
                arg_id = f"{self.role.value}_{self.argument_counter}"
                
                strength = ArgumentStrength.MODERATE
                strength_str = result.get("strength", "moderate").lower()
                if "strong" in strength_str:
                    strength = ArgumentStrength.STRONG
                elif "weak" in strength_str:
                    strength = ArgumentStrength.WEAK
                elif "overwhelming" in strength_str:
                    strength = ArgumentStrength.OVERWHELMING
                
                argument = Argument(
                    id=arg_id,
                    role=self.role,
                    claim=result.get("claim", ""),
                    evidence=result.get("evidence", []),
                    strength=strength,
                    counter_to=previous_arguments[-1].id if (
                        result.get("counter_to_previous") and previous_arguments
                    ) else None
                )
                
                self.arguments_made.append(argument)
                return argument
                
        except Exception as e:
            logger.error(f"Argument generation error: {e}")
        
        # Fallback
        self.argument_counter += 1
        return Argument(
            id=f"{self.role.value}_{self.argument_counter}",
            role=self.role,
            claim=f"[{self.role.value}] Bu konu hakkında görüş",
            evidence=[],
            strength=ArgumentStrength.WEAK
        )


class ConsensusBuilder:
    """
    Konsensüs Oluşturucu - Tartışmayı sentezler ve dengeli sonuç üretir.
    """
    
    def __init__(self):
        self.synthesis_history: List[DebateSynthesis] = []
    
    async def build_consensus(
        self,
        topic: str,
        arguments: List[Argument],
        context: str
    ) -> DebateSynthesis:
        """
        Argümanlardan konsensüs oluştur.
        
        Args:
            topic: Tartışma konusu
            arguments: Tüm argümanlar
            context: Bağlam
        
        Returns:
            DebateSynthesis
        """
        pro_args = [a for a in arguments if a.role == DebateRole.PRO]
        con_args = [a for a in arguments if a.role == DebateRole.CON]
        devils_args = [a for a in arguments if a.role == DebateRole.DEVILS_ADVOCATE]
        
        prompt = f"""Aşağıdaki tartışmayı sentezle ve dengeli bir sonuç üret.

Konu: {topic}

PRO (Olumlu) Argümanlar:
{chr(10).join([f"- {a.claim}" for a in pro_args])}

CON (Olumsuz) Argümanlar:
{chr(10).join([f"- {a.claim}" for a in con_args])}

Şeytan'ın Avukatı:
{chr(10).join([f"- {a.claim}" for a in devils_args])}

Görev: Dengeli bir sentez oluştur.

JSON formatında yanıt ver:
{{
    "main_conclusion": "Ana sonuç (2-3 cümle)",
    "pro_points": ["olumlu nokta 1", "olumlu nokta 2"],
    "con_points": ["olumsuz nokta 1", "olumsuz nokta 2"],
    "balanced_view": "Dengeli değerlendirme (3-4 cümle)",
    "recommendations": ["öneri 1", "öneri 2", "öneri 3"],
    "confidence_score": 0.0-1.0,
    "evidence_quality": "low|medium|high"
}}
"""
        
        try:
            response = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.4,
                max_tokens=800
            )
            
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                synthesis = DebateSynthesis(
                    main_conclusion=result.get("main_conclusion", ""),
                    pro_points=result.get("pro_points", []),
                    con_points=result.get("con_points", []),
                    balanced_view=result.get("balanced_view", ""),
                    recommendations=result.get("recommendations", []),
                    confidence_score=float(result.get("confidence_score", 0.7)),
                    evidence_quality=result.get("evidence_quality", "medium")
                )
                
                self.synthesis_history.append(synthesis)
                return synthesis
                
        except Exception as e:
            logger.error(f"Consensus building error: {e}")
        
        # Fallback
        return DebateSynthesis(
            main_conclusion="Konsensüs oluşturulamadı",
            pro_points=[a.claim for a in pro_args[:2]],
            con_points=[a.claim for a in con_args[:2]],
            balanced_view="Tartışma devam ediyor",
            recommendations=[],
            confidence_score=0.5,
            evidence_quality="low"
        )


class MultiAgentDebate:
    """
    Çok Ajanlı Tartışma Orkestratörü
    
    Pro/Con/Devil's Advocate ajanlarını koordine eder
    ve dengeli sentez üretir.
    """
    
    def __init__(
        self,
        max_rounds: int = 3,
        agents_per_round: int = 3,
        event_callback: Optional[Callable] = None
    ):
        self.max_rounds = max_rounds
        self.agents_per_round = agents_per_round
        self.event_callback = event_callback
        
        # Ajanları oluştur
        self.pro_agent = DebateAgent(DebateRole.PRO)
        self.con_agent = DebateAgent(DebateRole.CON)
        self.devils_advocate = DebateAgent(DebateRole.DEVILS_ADVOCATE)
        self.fact_checker = DebateAgent(DebateRole.FACT_CHECKER)
        self.consensus_builder = ConsensusBuilder()
        
        # Tartışma durumu
        self.rounds: List[DebateRound] = []
        self.all_arguments: List[Argument] = []
        self.final_synthesis: Optional[DebateSynthesis] = None
    
    async def _emit_event(self, event_type: str, data: Dict):
        """Event gönder."""
        if self.event_callback:
            event = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
            await self.event_callback(event)
    
    async def run_debate(
        self,
        topic: str,
        context: str,
        focus_areas: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Tartışmayı yürüt.
        
        Args:
            topic: Tartışma konusu
            context: Bağlam bilgisi
            focus_areas: Odak alanları (turlar için)
        
        Yields:
            Tartışma eventleri
        """
        yield {
            "type": "debate_start",
            "topic": topic,
            "max_rounds": self.max_rounds,
            "message": f"🎭 Çok ajanlı tartışma başlıyor: {topic}"
        }
        
        focus_areas = focus_areas or [None] * self.max_rounds
        
        for round_num in range(1, self.max_rounds + 1):
            focus = focus_areas[round_num - 1] if round_num <= len(focus_areas) else None
            
            yield {
                "type": "debate_round_start",
                "round": round_num,
                "focus": focus,
                "message": f"🔔 Tur {round_num}/{self.max_rounds}" + (f" - Odak: {focus}" if focus else "")
            }
            
            round_arguments: List[Argument] = []
            
            # Pro Agent
            yield {
                "type": "agent_speaking",
                "agent": "pro",
                "message": "💚 Pro ajan görüşünü sunuyor..."
            }
            
            pro_arg = await self.pro_agent.generate_argument(
                topic=topic,
                context=context,
                previous_arguments=self.all_arguments,
                focus_area=focus
            )
            round_arguments.append(pro_arg)
            self.all_arguments.append(pro_arg)
            
            yield {
                "type": "argument_made",
                "agent": "pro",
                "argument": pro_arg.to_dict(),
                "message": f"💚 Pro: {pro_arg.claim}"
            }
            
            # Con Agent
            yield {
                "type": "agent_speaking",
                "agent": "con",
                "message": "❤️ Con ajan karşı görüş sunuyor..."
            }
            
            con_arg = await self.con_agent.generate_argument(
                topic=topic,
                context=context,
                previous_arguments=self.all_arguments,
                focus_area=focus
            )
            round_arguments.append(con_arg)
            self.all_arguments.append(con_arg)
            
            yield {
                "type": "argument_made",
                "agent": "con",
                "argument": con_arg.to_dict(),
                "message": f"❤️ Con: {con_arg.claim}"
            }
            
            # Devil's Advocate (sadece bazı turlarda)
            if round_num <= 2:
                yield {
                    "type": "agent_speaking",
                    "agent": "devils_advocate",
                    "message": "😈 Şeytan'ın Avukatı meydan okuyor..."
                }
                
                devils_arg = await self.devils_advocate.generate_argument(
                    topic=topic,
                    context=context,
                    previous_arguments=self.all_arguments,
                    focus_area=focus
                )
                round_arguments.append(devils_arg)
                self.all_arguments.append(devils_arg)
                
                yield {
                    "type": "argument_made",
                    "agent": "devils_advocate",
                    "argument": devils_arg.to_dict(),
                    "message": f"😈 Devil's Advocate: {devils_arg.claim}"
                }
            
            # Round kaydı
            debate_round = DebateRound(
                round_number=round_num,
                topic_focus=focus or topic,
                arguments=round_arguments
            )
            self.rounds.append(debate_round)
            
            yield {
                "type": "debate_round_end",
                "round": round_num,
                "argument_count": len(round_arguments),
                "total_arguments": len(self.all_arguments)
            }
        
        # Final Synthesis
        yield {
            "type": "consensus_building",
            "message": "🤝 Konsensüs oluşturuluyor..."
        }
        
        self.final_synthesis = await self.consensus_builder.build_consensus(
            topic=topic,
            arguments=self.all_arguments,
            context=context
        )
        
        yield {
            "type": "debate_complete",
            "synthesis": {
                "main_conclusion": self.final_synthesis.main_conclusion,
                "pro_points": self.final_synthesis.pro_points,
                "con_points": self.final_synthesis.con_points,
                "balanced_view": self.final_synthesis.balanced_view,
                "recommendations": self.final_synthesis.recommendations,
                "confidence": self.final_synthesis.confidence_score
            },
            "total_arguments": len(self.all_arguments),
            "rounds": len(self.rounds),
            "message": "✅ Tartışma tamamlandı, sentez hazır"
        }
    
    def get_debate_summary(self) -> Dict[str, Any]:
        """Tartışma özeti."""
        return {
            "rounds": len(self.rounds),
            "total_arguments": len(self.all_arguments),
            "pro_arguments": len([a for a in self.all_arguments if a.role == DebateRole.PRO]),
            "con_arguments": len([a for a in self.all_arguments if a.role == DebateRole.CON]),
            "devils_advocate_arguments": len([a for a in self.all_arguments if a.role == DebateRole.DEVILS_ADVOCATE]),
            "synthesis": {
                "conclusion": self.final_synthesis.main_conclusion if self.final_synthesis else None,
                "confidence": self.final_synthesis.confidence_score if self.final_synthesis else 0
            } if self.final_synthesis else None
        }
    
    def to_markdown(self) -> str:
        """Tartışmayı Markdown formatına dönüştür."""
        md_parts = ["## 🎭 Çok Ajanlı Tartışma Özeti\n"]
        
        for round in self.rounds:
            md_parts.append(f"\n### Tur {round.round_number}: {round.topic_focus}\n")
            
            for arg in round.arguments:
                emoji = "💚" if arg.role == DebateRole.PRO else "❤️" if arg.role == DebateRole.CON else "😈"
                md_parts.append(f"\n**{emoji} {arg.role.value.title()}:** {arg.claim}\n")
                
                if arg.evidence:
                    md_parts.append("- Kanıtlar:\n")
                    for ev in arg.evidence[:3]:
                        md_parts.append(f"  - {ev}\n")
        
        if self.final_synthesis:
            md_parts.append("\n### 🤝 Sentez ve Sonuç\n")
            md_parts.append(f"\n**Ana Sonuç:** {self.final_synthesis.main_conclusion}\n")
            md_parts.append(f"\n**Dengeli Değerlendirme:** {self.final_synthesis.balanced_view}\n")
            
            if self.final_synthesis.recommendations:
                md_parts.append("\n**Öneriler:**\n")
                for rec in self.final_synthesis.recommendations:
                    md_parts.append(f"- {rec}\n")
        
        return "".join(md_parts)
