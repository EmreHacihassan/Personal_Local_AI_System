# 🏗️ Learning Journey V2 - Premium Mimari Tasarımı

## 🎯 Hedef Vizyon

**Deep Scholar 2.0 tarzı Multi-Agent Multi-Model Öğrenme Sistemi**

```
Kullanıcı: "Matematik öğrenmek istiyorum"
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI CURRICULUM STUDIO                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 🧠 Curriculum Orchestrator                                │  │
│  │    "5 uzman agent'ım var, şimdi analiz başlıyor..."      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│     ┌────────────┬───────────┼───────────┬────────────┐        │
│     ▼            ▼           ▼           ▼            ▼        │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐        │
│  │Peda- │   │Rese- │   │Cont- │   │Exam  │   │Revi- │        │
│  │gogy  │   │arch  │   │ent   │   │      │   │ew    │        │
│  │Agent │   │Agent │   │Agent │   │Agent │   │Agent │        │
│  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘        │
│     │            │           │           │            │        │
│     └────────────┴───────────┴───────────┴────────────┘        │
│                              │                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 🤖 Multi-Model Layer                                      │  │
│  │    Ollama (qwen3) │ OpenAI (gpt-4o) │ Claude │ Gemini    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
Kişiselleştirilmiş Müfredat (30-120 saniye düşünme)
```

---

## 📁 Yeni Dosya Yapısı

```
core/learning_journey_v2/
├── __init__.py
├── models.py                    # Mevcut (güncelleme)
├── 
├── # 🆕 MULTI-AGENT CURRICULUM STUDIO
├── curriculum_studio/
│   ├── __init__.py
│   ├── orchestrator.py          # Ana orkestratör
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Temel agent sınıfı
│   │   ├── pedagogy_agent.py    # Eğitim bilimi uzmanı
│   │   ├── research_agent.py    # RAG + Web araştırmacı
│   │   ├── content_agent.py     # İçerik tasarımcısı
│   │   ├── exam_agent.py        # Sınav oluşturucu
│   │   └── review_agent.py      # Kalite kontrol
│   └── models/
│       ├── __init__.py
│       └── multi_model_layer.py # LLM abstraction
│
├── # 🆕 SPACED REPETITION ENGINE
├── spaced_repetition/
│   ├── __init__.py
│   ├── sm2_algorithm.py         # SM-2 algoritması
│   ├── leitner_box.py           # Leitner kutu sistemi
│   ├── mastery_tracker.py       # Konu ustalık takibi
│   └── review_scheduler.py      # Tekrar zamanlayıcı
│
├── # 🆕 WEAKNESS DETECTION
├── weakness_detection/
│   ├── __init__.py
│   ├── performance_analyzer.py  # Test performans analizi
│   ├── weakness_detector.py     # Zayıf alan tespiti
│   └── adaptive_content.py      # Adaptif içerik seçimi
│
├── # 🆕 DYNAMIC STAGE CLOSURE
├── dynamic_closure/
│   ├── __init__.py
│   ├── closure_generator.py     # Dinamik kapanış üretici
│   └── weakness_emphasis.py     # Zayıf alan vurgusu
│
├── # Mevcut (güncelleme)
├── curriculum_planner.py        # Legacy - yeni sisteme wrapper
├── content_generator.py         # Güncelleme
├── exam_system.py               # Güncelleme
├── orchestrator.py              # Güncelleme
└── certificate_system.py        # Mevcut
```

---

## 🧠 Multi-Agent Curriculum Studio

### 1. Base Agent

```python
# core/learning_journey_v2/curriculum_studio/agents/base_agent.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
import asyncio

@dataclass
class AgentThought:
    """Visible reasoning - görünür düşünce"""
    agent_name: str
    step: str
    thinking: str          # "Şimdi konuları analiz ediyorum..."
    reasoning: str         # Detaylı mantık zinciri
    conclusion: str        # Sonuç
    confidence: float      # 0.0 - 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: int = 0

@dataclass
class AgentOutput:
    """Agent çıktısı"""
    agent_name: str
    result: Dict[str, Any]
    thoughts: List[AgentThought]
    success: bool
    error: Optional[str] = None

class BaseCurriculumAgent(ABC):
    """
    Curriculum Studio Base Agent
    
    Her agent:
    - Bağımsız düşünebilir
    - Düşünce sürecini stream edebilir
    - Diğer agentlarla iletişim kurabilir
    """
    
    def __init__(
        self,
        name: str,
        role: str,
        model_preference: str = "ollama/qwen3",
        fallback_models: List[str] = None
    ):
        self.name = name
        self.role = role
        self.model_preference = model_preference
        self.fallback_models = fallback_models or ["openai/gpt-4o", "ollama/llama3"]
        self.thoughts: List[AgentThought] = []
        
    async def think(
        self, 
        prompt: str, 
        step: str
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Düşünme süreci - stream olarak düşünceleri yayınla
        """
        start_time = datetime.now()
        
        # Düşünme başladı
        yield AgentThought(
            agent_name=self.name,
            step=step,
            thinking=f"🤔 {step} üzerinde düşünüyorum...",
            reasoning="",
            conclusion="",
            confidence=0.0
        )
        
        # LLM çağrısı
        try:
            response = await self._call_llm(prompt)
            
            thought = AgentThought(
                agent_name=self.name,
                step=step,
                thinking=f"✅ {step} tamamlandı",
                reasoning=response.get("reasoning", ""),
                conclusion=response.get("conclusion", ""),
                confidence=response.get("confidence", 0.8),
                duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
            )
            self.thoughts.append(thought)
            yield thought
            
        except Exception as e:
            yield AgentThought(
                agent_name=self.name,
                step=step,
                thinking=f"⚠️ {step} sırasında hata: {str(e)}",
                reasoning="Fallback model deneniyor...",
                conclusion="",
                confidence=0.0
            )
            
    @abstractmethod
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Agent'ın ana görevi"""
        pass
    
    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """LLM çağrısı - multi-model fallback ile"""
        # Multi-model layer kullanılacak
        pass
```

### 2. Pedagogy Agent (Eğitim Bilimi Uzmanı)

```python
# core/learning_journey_v2/curriculum_studio/agents/pedagogy_agent.py

class PedagogyAgent(BaseCurriculumAgent):
    """
    Pedagoji Uzmanı Agent
    
    Sorumluluklar:
    - Öğrenme hedefi analizi
    - Pedagojik sıralama
    - Bloom taksonomisi uygulaması
    - Öğrenme stili adaptasyonu
    """
    
    def __init__(self):
        super().__init__(
            name="Pedagoji Uzmanı",
            role="Eğitim bilimi ve öğrenme teorileri uzmanı",
            model_preference="openai/gpt-4o"  # Pedagoji için güçlü model
        )
        
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Pedagojik analiz yap
        """
        goal = context.get("goal")
        
        # Adım 1: Hedef Analizi
        async for thought in self.think(
            prompt=f"""
            Öğrenme hedefi: {goal.title}
            Konu: {goal.subject}
            Hedef: {goal.target_outcome}
            
            Bu hedefe ulaşmak için:
            1. Hangi ön bilgiler gerekli?
            2. Bloom taksonomisine göre öğrenme seviyesi ne olmalı?
            3. Önerilen öğrenme yolu nasıl olmalı?
            
            JSON formatında analiz et.
            """,
            step="hedef_analizi"
        ):
            yield thought
        
        # Adım 2: Pedagojik Sıralama
        async for thought in self.think(
            prompt=f"""
            Konu: {goal.subject}
            
            Bu konunun alt başlıklarını pedagojik olarak doğru sıraya koy.
            Ön koşullar → Temel kavramlar → İleri konular → Uygulama
            
            JSON formatında sıralı liste döndür.
            """,
            step="pedagojik_siralama"
        ):
            yield thought
        
        # Adım 3: Öğrenme Stili Adaptasyonu
        async for thought in self.think(
            prompt=f"""
            Öğrenci profili:
            - Öğrenme stili: {goal.learning_style or 'Belirtilmemiş'}
            - Günlük çalışma: {goal.daily_hours} saat
            - Tercih edilen içerik: {goal.content_preferences}
            
            Bu profile göre:
            1. Hangi içerik türleri ağırlıklı olmalı?
            2. Paket süreleri ne kadar olmalı?
            3. Pratik/teori oranı ne olmalı?
            """,
            step="ogrenme_stili_adaptasyonu"
        ):
            yield thought
```

### 3. Research Agent

```python
# core/learning_journey_v2/curriculum_studio/agents/research_agent.py

class ResearchAgent(BaseCurriculumAgent):
    """
    Araştırma Agent
    
    Sorumluluklar:
    - RAG ile bilgi çekme
    - Web araştırması
    - Güncel içerik bulma
    - Kaynak doğrulama
    """
    
    def __init__(self, rag_service=None, web_search_service=None):
        super().__init__(
            name="Araştırma Uzmanı",
            role="Bilgi toplama ve doğrulama uzmanı",
            model_preference="ollama/qwen3"  # Hızlı model
        )
        self.rag = rag_service
        self.web_search = web_search_service
        
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Konu araştırması yap
        """
        topics = context.get("topics", [])
        
        # RAG Araştırması
        async for thought in self.think(
            prompt=f"RAG'dan '{', '.join(topics)}' konularını araştır",
            step="rag_arastirmasi"
        ):
            yield thought
        
        # Web Araştırması
        async for thought in self.think(
            prompt=f"Web'den güncel '{', '.join(topics)}' kaynakları bul",
            step="web_arastirmasi"
        ):
            yield thought
```

### 4. Curriculum Studio Orchestrator

```python
# core/learning_journey_v2/curriculum_studio/orchestrator.py

class CurriculumStudioOrchestrator:
    """
    Multi-Agent Curriculum Orchestrator
    
    5 uzman agent'ı koordine eder:
    1. Pedagogy Agent - Eğitim bilimi
    2. Research Agent - Araştırma
    3. Content Agent - İçerik tasarımı
    4. Exam Agent - Sınav oluşturma
    5. Review Agent - Kalite kontrol
    """
    
    def __init__(self):
        self.agents = {
            "pedagogy": PedagogyAgent(),
            "research": ResearchAgent(),
            "content": ContentDesignAgent(),
            "exam": ExamCreationAgent(),
            "review": ReviewAgent()
        }
        
    async def create_curriculum(
        self,
        goal: LearningGoal
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Multi-agent curriculum oluşturma
        
        Yields:
            AgentThought - Her agent'ın düşüncesi real-time
        """
        context = {"goal": goal}
        
        # Orchestrator başlangıç mesajı
        yield AgentThought(
            agent_name="Curriculum Studio",
            step="baslatma",
            thinking="🎬 5 uzman agent müfredatını hazırlıyor...",
            reasoning="Pedagoji, Araştırma, İçerik, Sınav ve Kalite Kontrol uzmanları devreye giriyor.",
            conclusion="",
            confidence=1.0
        )
        
        # ===== FAZ 1: Paralel Analiz =====
        yield AgentThought(
            agent_name="Curriculum Studio",
            step="faz_1",
            thinking="📊 Faz 1: Paralel Analiz Başlıyor...",
            reasoning="Pedagoji ve Araştırma agent'ları eş zamanlı çalışacak",
            conclusion="",
            confidence=1.0
        )
        
        # Pedagogy ve Research paralel çalışsın
        pedagogy_task = asyncio.create_task(
            self._run_agent("pedagogy", context)
        )
        research_task = asyncio.create_task(
            self._run_agent("research", context)
        )
        
        # Her iki agent'tan gelen düşünceleri stream et
        async for thought in self._merge_streams([pedagogy_task, research_task]):
            yield thought
        
        # Sonuçları context'e ekle
        context["pedagogy_result"] = await pedagogy_task
        context["research_result"] = await research_task
        
        # ===== FAZ 2: İçerik ve Sınav Tasarımı =====
        yield AgentThought(
            agent_name="Curriculum Studio",
            step="faz_2",
            thinking="📝 Faz 2: İçerik ve Sınav Tasarımı...",
            reasoning="Pedagoji analizine göre içerik ve sınavlar tasarlanıyor",
            conclusion="",
            confidence=1.0
        )
        
        # Content ve Exam paralel
        async for thought in self.agents["content"].execute(context):
            yield thought
            
        async for thought in self.agents["exam"].execute(context):
            yield thought
        
        # ===== FAZ 3: Kalite Kontrol =====
        yield AgentThought(
            agent_name="Curriculum Studio",
            step="faz_3",
            thinking="🔍 Faz 3: Kalite Kontrol...",
            reasoning="Tüm çıktılar gözden geçiriliyor",
            conclusion="",
            confidence=1.0
        )
        
        async for thought in self.agents["review"].execute(context):
            yield thought
        
        # Final
        yield AgentThought(
            agent_name="Curriculum Studio",
            step="tamamlandi",
            thinking="✅ Müfredat hazırlandı!",
            reasoning="5 uzman agent başarıyla tamamladı",
            conclusion="Kişiselleştirilmiş müfredat hazır",
            confidence=1.0
        )
```

---

## 🔄 Spaced Repetition Engine

### SM-2 Algoritması

```python
# core/learning_journey_v2/spaced_repetition/sm2_algorithm.py

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

@dataclass
class ReviewCard:
    """Tekrar kartı"""
    card_id: str
    topic: str
    question_id: str
    
    # SM-2 parametreleri
    easiness_factor: float = 2.5  # E-Factor (1.3 - 2.5)
    interval: int = 1             # Gün cinsinden interval
    repetition: int = 0           # Tekrar sayısı
    
    # Zamanlama
    next_review: Optional[datetime] = None
    last_review: Optional[datetime] = None
    
    # Mastery
    mastery_level: float = 0.0    # 0-100

class SM2Algorithm:
    """
    SuperMemo 2 Algoritması
    
    Aralıklı tekrar için altın standart algoritma.
    """
    
    @staticmethod
    def calculate_next_review(
        card: ReviewCard,
        quality: int  # 0-5 arası (0=tam yanlış, 5=mükemmel)
    ) -> ReviewCard:
        """
        Kaliteye göre sonraki tekrar zamanını hesapla
        
        Args:
            card: Mevcut kart durumu
            quality: 0-5 arası performans değeri
                0: Tamamen yanlış
                1: Yanlış ama tanıdık
                2: Yanlış ama hatırladı
                3: Doğru ama zor
                4: Doğru
                5: Mükemmel
        
        Returns:
            Güncellenmiş kart
        """
        # E-Factor güncelleme
        new_ef = card.easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ef = max(1.3, new_ef)  # Minimum 1.3
        
        # Interval hesaplama
        if quality < 3:
            # Başarısız - sıfırla
            new_interval = 1
            new_repetition = 0
        else:
            # Başarılı
            if card.repetition == 0:
                new_interval = 1
            elif card.repetition == 1:
                new_interval = 6
            else:
                new_interval = round(card.interval * new_ef)
            new_repetition = card.repetition + 1
        
        # Mastery güncelleme
        mastery_delta = (quality - 2.5) * 10  # -25 to +25
        new_mastery = max(0, min(100, card.mastery_level + mastery_delta))
        
        # Sonraki tekrar zamanı
        next_review = datetime.now() + timedelta(days=new_interval)
        
        return ReviewCard(
            card_id=card.card_id,
            topic=card.topic,
            question_id=card.question_id,
            easiness_factor=new_ef,
            interval=new_interval,
            repetition=new_repetition,
            next_review=next_review,
            last_review=datetime.now(),
            mastery_level=new_mastery
        )
```

### Mastery Tracker

```python
# core/learning_journey_v2/spaced_repetition/mastery_tracker.py

class MasteryTracker:
    """
    Konu Ustalık Takip Sistemi
    
    Her konu için:
    - Mastery seviyesi (0-100%)
    - Tekrar kartları
    - Zayıf alan tespiti
    """
    
    def __init__(self):
        self.topic_mastery: Dict[str, float] = {}
        self.cards: Dict[str, List[ReviewCard]] = {}
        
    def record_performance(
        self,
        topic: str,
        question_id: str,
        is_correct: bool,
        confidence: float = 0.5
    ) -> float:
        """
        Performans kaydet ve mastery güncelle
        """
        # SM-2 quality hesapla
        if is_correct:
            quality = 3 + int(confidence * 2)  # 3-5
        else:
            quality = int(confidence * 2)  # 0-2
        
        # Kart bul veya oluştur
        card = self._get_or_create_card(topic, question_id)
        
        # SM-2 uygula
        updated_card = SM2Algorithm.calculate_next_review(card, quality)
        self._save_card(updated_card)
        
        # Topic mastery güncelle
        self._update_topic_mastery(topic)
        
        return self.topic_mastery.get(topic, 0)
    
    def get_weak_topics(self, threshold: float = 50.0) -> List[str]:
        """Zayıf konuları getir"""
        return [
            topic for topic, mastery in self.topic_mastery.items()
            if mastery < threshold
        ]
    
    def get_due_reviews(self) -> List[ReviewCard]:
        """Tekrar zamanı gelen kartları getir"""
        now = datetime.now()
        due_cards = []
        
        for topic_cards in self.cards.values():
            for card in topic_cards:
                if card.next_review and card.next_review <= now:
                    due_cards.append(card)
        
        return sorted(due_cards, key=lambda c: c.next_review)
```

---

## 🎯 Weakness Detection System

```python
# core/learning_journey_v2/weakness_detection/weakness_detector.py

class WeaknessDetector:
    """
    Zayıf Alan Tespit Sistemi
    
    Test sonuçlarından:
    - Zayıf konuları tespit et
    - Hata paternlerini analiz et
    - Kişiselleştirilmiş öneriler sun
    """
    
    def __init__(self, mastery_tracker: MasteryTracker):
        self.mastery_tracker = mastery_tracker
        
    def analyze_exam_result(
        self,
        exam_result: ExamResult
    ) -> Dict[str, Any]:
        """
        Sınav sonucunu analiz et
        """
        weakness_map = {}
        
        for criteria in exam_result.criteria_scores:
            topic = criteria.criteria_name
            ratio = criteria.score / criteria.max_score
            
            if ratio < 0.6:  # %60 altı = zayıf
                weakness_map[topic] = {
                    "score": criteria.score,
                    "max_score": criteria.max_score,
                    "ratio": ratio,
                    "feedback": criteria.feedback,
                    "severity": "critical" if ratio < 0.3 else "moderate"
                }
        
        return weakness_map
    
    def generate_stage_closure_emphasis(
        self,
        stage_id: str,
        all_results: List[ExamResult]
    ) -> Dict[str, Any]:
        """
        Stage bitirme paketi için zayıf alan vurgusunu hesapla
        """
        topic_performance = {}
        
        # Tüm sonuçları topla
        for result in all_results:
            for criteria in result.criteria_scores:
                topic = criteria.criteria_name
                if topic not in topic_performance:
                    topic_performance[topic] = []
                topic_performance[topic].append(criteria.score / criteria.max_score)
        
        # Ortalama hesapla
        topic_averages = {
            topic: sum(scores) / len(scores)
            for topic, scores in topic_performance.items()
        }
        
        # Zayıftan güçlüye sırala
        sorted_topics = sorted(topic_averages.items(), key=lambda x: x[1])
        
        # Stage closure için soru dağılımı
        question_distribution = {}
        remaining_questions = 30  # Toplam soru sayısı
        
        for topic, avg in sorted_topics:
            if avg < 0.5:
                # Çok zayıf: %40 soru
                questions = int(remaining_questions * 0.4)
            elif avg < 0.7:
                # Orta zayıf: %25 soru
                questions = int(remaining_questions * 0.25)
            else:
                # İyi: %10 soru
                questions = int(remaining_questions * 0.1)
            
            question_distribution[topic] = questions
            remaining_questions -= questions
        
        return {
            "topic_averages": topic_averages,
            "weak_topics": [t for t, a in sorted_topics if a < 0.6],
            "question_distribution": question_distribution,
            "emphasis_message": self._generate_emphasis_message(sorted_topics)
        }
    
    def _generate_emphasis_message(self, sorted_topics: List[Tuple[str, float]]) -> str:
        """Kişiselleştirilmiş vurgu mesajı"""
        weak_count = sum(1 for _, avg in sorted_topics if avg < 0.6)
        
        if weak_count == 0:
            return "Harika gidiyorsun! 🌟 Tüm konularda iyi bir seviyedesin."
        elif weak_count <= 2:
            topics = [t for t, a in sorted_topics if a < 0.6]
            return f"📚 {', '.join(topics)} konularına biraz daha odaklanmalısın."
        else:
            return f"⚠️ {weak_count} konuda gelişim gerekiyor. Endişelenme, bu test tam da bunun için!"
```

---

## 🔐 Puan Bazlı Kilitleme

```python
# core/learning_journey_v2/models.py güncelleme

@dataclass
class Package:
    # ... mevcut alanlar ...
    
    # Yeni alanlar
    is_locked: bool = True
    lock_reason: Optional[str] = None
    required_score: float = 70.0
    attempt_count: int = 0
    max_attempts: int = 5
    last_attempt_score: Optional[float] = None
    
    def can_proceed(self) -> Tuple[bool, str]:
        """
        Bir sonraki pakete geçilebilir mi?
        """
        if self.status != PackageStatus.PASSED:
            return False, "Paketi tamamlamadın"
        
        if self.last_attempt_score is None:
            return False, "Henüz test çözmedin"
        
        if self.last_attempt_score < self.required_score:
            return False, f"Minimum %{self.required_score} puan gerekli. Aldığın: %{self.last_attempt_score:.1f}"
        
        return True, "Geçebilirsin!"
    
    def record_attempt(self, score: float) -> Dict[str, Any]:
        """
        Test denemesi kaydet
        """
        self.attempt_count += 1
        self.last_attempt_score = score
        
        if score >= self.required_score:
            self.status = PackageStatus.PASSED
            return {
                "passed": True,
                "message": "Tebrikler! 🎉 Bir sonraki pakete geçebilirsin.",
                "unlock_next": True
            }
        else:
            remaining = self.max_attempts - self.attempt_count
            if remaining <= 0:
                return {
                    "passed": False,
                    "message": "Maksimum deneme hakkını kullandın. Yardım almak ister misin?",
                    "unlock_next": False,
                    "offer_help": True
                }
            return {
                "passed": False,
                "message": f"Puan yetersiz. {remaining} deneme hakkın kaldı.",
                "unlock_next": False,
                "remaining_attempts": remaining
            }
```

---

## 🖥️ Frontend Güncellemeleri

### 1. Real-time Agent Streaming

```tsx
// frontend-next/src/components/learning/AgentThinkingStream.tsx

interface AgentThought {
  agent_name: string;
  step: string;
  thinking: string;
  reasoning: string;
  conclusion: string;
  confidence: number;
}

const AgentThinkingStream: React.FC<{
  thoughts: AgentThought[];
  isStreaming: boolean;
}> = ({ thoughts, isStreaming }) => {
  return (
    <div className="space-y-4">
      {/* Agent Avatarları */}
      <div className="flex gap-4 justify-center">
        {AGENTS.map(agent => (
          <AgentAvatar 
            key={agent.name}
            agent={agent}
            isActive={thoughts.some(t => t.agent_name === agent.name)}
          />
        ))}
      </div>
      
      {/* Düşünce Akışı */}
      <div className="space-y-3 max-h-96 overflow-auto">
        <AnimatePresence>
          {thoughts.map((thought, idx) => (
            <motion.div
              key={`${thought.agent_name}-${thought.step}-${idx}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 rounded-xl bg-gray-800/50 border border-gray-700"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-medium text-purple-400">
                  {thought.agent_name}
                </span>
                <span className="text-xs text-gray-500">
                  {thought.step}
                </span>
              </div>
              
              <p className="text-white">{thought.thinking}</p>
              
              {thought.reasoning && (
                <p className="text-sm text-gray-400 mt-2 italic">
                  💭 {thought.reasoning}
                </p>
              )}
              
              {thought.conclusion && (
                <p className="text-sm text-green-400 mt-2">
                  ✅ {thought.conclusion}
                </p>
              )}
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isStreaming && (
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 1 }}
            className="text-center text-purple-400"
          >
            Agent'lar düşünüyor...
          </motion.div>
        )}
      </div>
    </div>
  );
};
```

### 2. Mastery Progress Bar

```tsx
// frontend-next/src/components/learning/MasteryProgress.tsx

const MasteryProgress: React.FC<{
  topics: Array<{
    name: string;
    mastery: number;
    isWeak: boolean;
  }>;
}> = ({ topics }) => {
  return (
    <div className="space-y-3">
      {topics.map(topic => (
        <div key={topic.name} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className={topic.isWeak ? "text-red-400" : "text-white"}>
              {topic.isWeak && "⚠️ "}{topic.name}
            </span>
            <span className="text-gray-400">%{topic.mastery.toFixed(0)}</span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${topic.mastery}%` }}
              className={`h-full rounded-full ${
                topic.mastery >= 80 ? "bg-green-500" :
                topic.mastery >= 50 ? "bg-yellow-500" :
                "bg-red-500"
              }`}
            />
          </div>
        </div>
      ))}
    </div>
  );
};
```

---

## 📅 Uygulama Zaman Çizelgesi

### Hafta 1: Core Infrastructure
- [ ] `curriculum_studio/` klasör yapısı
- [ ] `BaseCurriculumAgent` implementasyonu
- [ ] `PedagogyAgent` implementasyonu
- [ ] Multi-model layer

### Hafta 2: Agent'lar + Spaced Repetition
- [ ] Diğer 4 agent
- [ ] `CurriculumStudioOrchestrator`
- [ ] SM-2 algoritması
- [ ] `MasteryTracker`

### Hafta 3: Weakness + Dynamic Closure
- [ ] `WeaknessDetector`
- [ ] Dynamic stage closure generator
- [ ] Puan bazlı kilitleme enforcement

### Hafta 4: Frontend
- [ ] `AgentThinkingStream` component
- [ ] `MasteryProgress` component
- [ ] WebSocket streaming entegrasyonu
- [ ] Test ve polish

---

*Bu tasarım belgesi, Learning Journey V2'nin premium versiyonunu tanımlar.*
