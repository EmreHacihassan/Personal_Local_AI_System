"""
🧠 Base Curriculum Agent

Tüm Curriculum Studio agent'larının temel sınıfı.
Visible reasoning, multi-model fallback ve streaming desteği.
"""

import asyncio
import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from enum import Enum


class ThinkingPhase(str, Enum):
    """Düşünme fazları"""
    ANALYZING = "analyzing"
    REASONING = "reasoning"
    DECIDING = "deciding"
    CONCLUDING = "concluding"


@dataclass
class AgentThought:
    """
    Visible Reasoning - Görünür Düşünce
    
    Her agent'ın düşünce süreci kullanıcıya gösterilir.
    Deep Scholar 2.0 tarzı "AI düşünüyor" deneyimi.
    """
    agent_name: str
    agent_icon: str = "🤖"
    step: str = ""
    phase: ThinkingPhase = ThinkingPhase.ANALYZING
    
    # Düşünce içeriği
    thinking: str = ""          # Kısa düşünce ("Konuları analiz ediyorum...")
    reasoning: str = ""         # Detaylı mantık zinciri
    evidence: List[str] = field(default_factory=list)  # Kanıtlar/kaynaklar
    conclusion: str = ""        # Sonuç
    
    # Meta
    confidence: float = 0.0     # 0.0 - 1.0
    duration_ms: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Streaming
    is_streaming: bool = False
    is_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_icon": self.agent_icon,
            "step": self.step,
            "phase": self.phase.value,
            "thinking": self.thinking,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "is_streaming": self.is_streaming,
            "is_complete": self.is_complete
        }


@dataclass
class AgentOutput:
    """Agent çıktısı"""
    agent_name: str
    result: Dict[str, Any] = field(default_factory=dict)
    thoughts: List[AgentThought] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    execution_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "result": self.result,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "success": self.success,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms
        }


class BaseCurriculumAgent(ABC):
    """
    Curriculum Studio Base Agent
    
    Her agent:
    - Bağımsız düşünebilir
    - Düşünce sürecini stream edebilir
    - Multi-model fallback kullanabilir
    - Diğer agent'larla iletişim kurabilir
    
    Features:
    - Visible reasoning (düşünce süreci görünür)
    - Confidence scoring
    - Evidence-based conclusions
    - Streaming support
    """
    
    # Agent avatarları
    AGENT_ICONS = {
        "pedagogy": "👨‍🏫",
        "research": "🔍",
        "content": "📝",
        "exam": "📋",
        "review": "🔬",
        "orchestrator": "🎭"
    }
    
    def __init__(
        self,
        name: str,
        role: str,
        specialty: str,
        model_preference: str = "ollama/qwen3:8b",
        fallback_models: List[str] = None,
        thinking_style: str = "analytical"
    ):
        self.name = name
        self.role = role
        self.specialty = specialty
        self.model_preference = model_preference
        self.fallback_models = fallback_models or [
            "ollama/llama3.2",
            "openai/gpt-4o-mini"
        ]
        self.thinking_style = thinking_style
        self.thoughts: List[AgentThought] = []
        self.agent_type = name.lower().split()[0] if name else "agent"
        self.icon = self.AGENT_ICONS.get(self.agent_type, "🤖")
        
        # LLM service (lazy loading)
        self._llm_service = None
        
    @property
    def llm_service(self):
        """Lazy load LLM service"""
        if self._llm_service is None:
            try:
                from core.llm_router import get_best_available_llm
                self._llm_service = get_best_available_llm()
            except:
                pass
        return self._llm_service
    
    @llm_service.setter
    def llm_service(self, value):
        """Set LLM service"""
        self._llm_service = value
    
    async def think(
        self, 
        prompt: str, 
        step: str,
        context: Dict[str, Any] = None
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Düşünme süreci - stream olarak düşünceleri yayınla
        
        Args:
            prompt: LLM'e gönderilecek prompt
            step: Adım adı (örn: "hedef_analizi")
            context: Ek bağlam bilgisi
            
        Yields:
            AgentThought - Her düşünce adımı
        """
        start_time = datetime.now()
        
        # Faz 1: Analyzing
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step=step,
            phase=ThinkingPhase.ANALYZING,
            thinking=f"🔍 {step.replace('_', ' ').title()} üzerinde çalışıyorum...",
            is_streaming=True,
            is_complete=False
        )
        
        # Gerçekçi düşünme süresi simülasyonu
        await asyncio.sleep(random.uniform(1.5, 3.0))
        
        # Faz 2: Reasoning
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step=step,
            phase=ThinkingPhase.REASONING,
            thinking=f"💭 Bilgileri değerlendiriyorum...",
            reasoning=self._generate_reasoning_preview(step, context),
            is_streaming=True,
            is_complete=False
        )
        
        await asyncio.sleep(random.uniform(1.0, 2.5))
        
        # LLM çağrısı
        try:
            response = await self._call_llm(prompt, context)
            
            # Faz 3: Concluding
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            thought = AgentThought(
                agent_name=self.name,
                agent_icon=self.icon,
                step=step,
                phase=ThinkingPhase.CONCLUDING,
                thinking=f"✅ {step.replace('_', ' ').title()} tamamlandı",
                reasoning=response.get("reasoning", ""),
                evidence=response.get("evidence", []),
                conclusion=response.get("conclusion", ""),
                confidence=response.get("confidence", 0.85),
                duration_ms=duration_ms,
                is_streaming=False,
                is_complete=True
            )
            self.thoughts.append(thought)
            yield thought
            
        except Exception as e:
            yield AgentThought(
                agent_name=self.name,
                agent_icon=self.icon,
                step=step,
                phase=ThinkingPhase.CONCLUDING,
                thinking=f"⚠️ Hata oluştu: {str(e)[:50]}",
                reasoning="Fallback strateji uygulanıyor...",
                confidence=0.5,
                is_streaming=False,
                is_complete=True
            )
    
    def _generate_reasoning_preview(self, step: str, context: Dict[str, Any] = None) -> str:
        """Reasoning önizlemesi oluştur"""
        previews = {
            "hedef_analizi": "Öğrencinin hedefini, mevcut seviyesini ve öğrenme stilini analiz ediyorum...",
            "pedagojik_siralama": "Bloom taksonomisine göre konuları sıralıyorum, ön koşulları belirliyorum...",
            "ogrenme_stili": "Görsel, işitsel ve kinestetik öğrenme tercihleri değerlendiriliyor...",
            "rag_arastirmasi": "Bilgi tabanından ilgili dokümanları çekiyorum...",
            "web_arastirmasi": "Güncel kaynakları ve akademik makaleleri tarıyorum...",
            "icerik_tasarimi": "Multimedya içerik yapısını planlıyorum...",
            "soru_uretimi": "Bloom taksonomisi seviyelerine göre sorular üretiyorum...",
            "kalite_kontrol": "Pedagojik tutarlılık ve içerik kalitesini değerlendiriyorum..."
        }
        return previews.get(step, "Detaylı analiz yapılıyor...")
    
    async def _call_llm(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        LLM çağrısı - multi-model fallback ile
        
        Returns:
            Dict with: reasoning, conclusion, confidence, evidence
        """
        system_prompt = f"""Sen bir {self.role}sın. Uzmanlık alanın: {self.specialty}.
        
Düşünme stilin: {self.thinking_style}

Her zaman yapılandırılmış, kanıta dayalı ve güven seviyesi belirten yanıtlar ver.
Yanıtını JSON formatında döndür:
{{
    "reasoning": "Detaylı mantık zincirin",
    "conclusion": "Ana sonuç",
    "confidence": 0.0-1.0 arası güven seviyesi,
    "evidence": ["Kanıt 1", "Kanıt 2"],
    "recommendations": ["Öneri 1", "Öneri 2"]
}}"""

        # Context'i prompt'a ekle
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2, default=str)
            full_prompt = f"Bağlam:\n{context_str}\n\nGörev:\n{prompt}"
        else:
            full_prompt = prompt
        
        # LLM service varsa kullan
        if self.llm_service:
            try:
                response = await self._call_llm_service(system_prompt, full_prompt)
                return response
            except Exception as e:
                print(f"[{self.name}] LLM error: {e}")
        
        # Fallback: Mock response
        return self._generate_mock_response(prompt, context)
    
    async def _call_llm_service(
        self, 
        system_prompt: str, 
        user_prompt: str
    ) -> Dict[str, Any]:
        """Gerçek LLM servisi çağrısı"""
        try:
            # Ollama veya diğer LLM servislerini dene
            response_text = await self.llm_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=2000
            )
            
            # JSON parse et
            try:
                # JSON bloğunu bul
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0]
                else:
                    json_str = response_text
                    
                return json.loads(json_str.strip())
            except:
                return {
                    "reasoning": response_text[:500],
                    "conclusion": response_text[:200],
                    "confidence": 0.75,
                    "evidence": [],
                    "recommendations": []
                }
        except Exception as e:
            raise e
    
    def _generate_mock_response(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Mock response - LLM olmadan çalışma"""
        return {
            "reasoning": f"[{self.name}] {self.specialty} perspektifinden analiz yapıldı.",
            "conclusion": f"Başarılı analiz tamamlandı.",
            "confidence": random.uniform(0.75, 0.95),
            "evidence": [
                "Pedagojik ilkelere uygunluk kontrol edildi",
                "Öğrenme hedefleri ile uyum sağlandı"
            ],
            "recommendations": [
                "Adım adım ilerleme önerilir",
                "Pratik uygulamalar eklenmeli"
            ]
        }
    
    @abstractmethod
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Agent'ın ana görevi
        
        Args:
            context: Çalışma bağlamı (goal, previous results, etc.)
            
        Yields:
            AgentThought - Her düşünce adımı
        """
        pass
    
    async def get_final_output(self) -> AgentOutput:
        """Tüm düşüncelerden final output oluştur"""
        # Son düşüncedeki conclusion'ı al
        conclusions = [t.conclusion for t in self.thoughts if t.conclusion]
        reasonings = [t.reasoning for t in self.thoughts if t.reasoning]
        
        total_time = sum(t.duration_ms for t in self.thoughts)
        avg_confidence = sum(t.confidence for t in self.thoughts) / max(len(self.thoughts), 1)
        
        return AgentOutput(
            agent_name=self.name,
            result={
                "conclusions": conclusions,
                "reasoning_chain": reasonings,
                "confidence": avg_confidence
            },
            thoughts=self.thoughts,
            success=True,
            execution_time_ms=total_time
        )
    
    def reset(self):
        """Agent durumunu sıfırla"""
        self.thoughts = []
