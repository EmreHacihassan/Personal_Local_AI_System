"""
Full Meta Learning Engine
Nöro-Adaptif Mastery Sistemi - Bilimsel Temelli Öğrenme Motoru

Bilimsel Prensipler:
- Spaced Repetition (Ebbinghaus)
- Retrieval Practice (Roediger)
- Dual Coding (Paivio)
- Elaborative Interrogation (Dunlosky)
- Deliberate Practice (Ericsson)
- Metacognition (Flavell)
- Desirable Difficulties (Bjork)
"""

import json
import uuid
import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class PackageStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"


class LayerType(str, Enum):
    WARMUP = "warmup"
    PRIME = "prime"
    ACQUIRE = "acquire"
    INTERROGATE = "interrogate"
    PRACTICE = "practice"
    CONNECT = "connect"
    CHALLENGE = "challenge"
    ERROR_LAB = "error_lab"
    FEYNMAN = "feynman"
    TRANSFER = "transfer"
    META_REFLECTION = "meta_reflection"
    CONSOLIDATE = "consolidate"


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"
    CODE = "code"
    ORDERING = "ordering"
    MATCHING = "matching"
    FILL_BLANK = "fill_blank"
    TRUE_FALSE = "true_false"
    DIAGRAM = "diagram"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


# Memory strength decay constants (Ebbinghaus curve parameters)
INITIAL_MEMORY_STRENGTH = 1.0
DECAY_RATE = 0.5  # How fast memory decays
MIN_MEMORY_THRESHOLD = 0.4  # Below this, topic needs refresh
OPTIMAL_REVIEW_THRESHOLD = 0.6  # Ideal time to review


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Concept:
    """Bir öğrenme kavramı"""
    id: str
    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    estimated_minutes: int = 30
    content: Dict[str, Any] = field(default_factory=dict)  # Multi-format content


@dataclass
class Question:
    """Bir soru/egzersiz"""
    id: str
    concept_id: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: Any = None
    explanation: str = ""
    hints: List[str] = field(default_factory=list)
    points: int = 10
    time_limit_seconds: Optional[int] = None


@dataclass
class Layer:
    """Paket içindeki bir katman (12 katmandan biri)"""
    id: str
    layer_type: LayerType
    title: str
    description: str
    estimated_minutes: int
    content: Dict[str, Any] = field(default_factory=dict)
    questions: List[Question] = field(default_factory=list)
    completed: bool = False
    score: Optional[float] = None
    completed_at: Optional[str] = None


@dataclass
class Package:
    """Bir öğrenme paketi (Aşama içindeki birim)"""
    id: str
    stage_id: str
    name: str
    description: str
    order: int
    concepts: List[Concept] = field(default_factory=list)
    layers: List[Layer] = field(default_factory=list)
    status: PackageStatus = PackageStatus.LOCKED
    estimated_hours: float = 4.0
    actual_hours: float = 0.0
    current_layer_index: int = 0
    overall_score: float = 0.0
    xp_earned: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    refresh_topics: List[str] = field(default_factory=list)  # Unutulmaya başlayan konular


@dataclass
class Stage:
    """Bir öğrenme aşaması (Roadmap içindeki büyük birim)"""
    id: str
    workspace_id: str
    name: str
    description: str
    order: int
    packages: List[Package] = field(default_factory=list)
    status: PackageStatus = PackageStatus.LOCKED
    mastery_exam_passed: bool = False
    mastery_score: float = 0.0
    prerequisites_met: bool = False


@dataclass
class Workspace:
    """Bir öğrenme çalışma alanı (Ana Roadmap)"""
    id: str
    user_id: str
    name: str
    description: str
    target_goal: str
    source_materials: List[Dict[str, str]] = field(default_factory=list)  # PDF, URL, etc.
    stages: List[Stage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    estimated_total_hours: float = 0.0
    actual_total_hours: float = 0.0
    overall_progress: float = 0.0
    streak_days: int = 0
    last_activity: Optional[str] = None
    total_xp: int = 0
    level: int = 1


@dataclass
class MemoryRecord:
    """Bir kavram için bellek kaydı (Spaced Repetition)"""
    concept_id: str
    user_id: str
    workspace_id: str
    memory_strength: float = INITIAL_MEMORY_STRENGTH
    last_reviewed: str = field(default_factory=lambda: datetime.now().isoformat())
    review_count: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    next_review: Optional[str] = None
    ease_factor: float = 2.5  # SM-2 algorithm ease factor
    interval_days: float = 1.0


@dataclass
class LearnerProfile:
    """Öğrenci profili"""
    user_id: str
    preferred_formats: List[str] = field(default_factory=lambda: ["visual", "practical"])
    optimal_session_minutes: int = 45
    optimal_time_of_day: str = "morning"
    attention_span_minutes: int = 25
    learning_speed: float = 1.0  # 1.0 = average, >1 = fast, <1 = slow
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    total_study_hours: float = 0.0
    achievements: List[str] = field(default_factory=list)


@dataclass
class FeynmanSubmission:
    """Feynman tekniği için kullanıcı anlatımı"""
    id: str
    user_id: str
    package_id: str
    target_audience: str  # "child", "student", "expert"
    format: str  # "audio", "text", "video"
    content: str  # transcript or text
    submitted_at: str
    ai_analysis: Optional[Dict[str, Any]] = None
    score: float = 0.0
    passed: bool = False
    missing_concepts: List[str] = field(default_factory=list)
    feedback: str = ""


@dataclass
class DailySession:
    """Günlük öğrenme oturumu planı"""
    id: str
    user_id: str
    workspace_id: str
    date: str
    planned_minutes: int
    refresh_items: List[Dict[str, Any]] = field(default_factory=list)
    new_content: List[Dict[str, Any]] = field(default_factory=list)
    challenges: List[Dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    actual_minutes: int = 0
    xp_earned: int = 0


# ============================================================================
# MEMORY ENGINE (Spaced Repetition)
# ============================================================================

class MemoryEngine:
    """Ebbinghaus unutma eğrisi + SM-2 algoritması tabanlı bellek motoru"""
    
    def __init__(self, data_dir: str = "data/full_meta"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_records: Dict[str, MemoryRecord] = {}
        self._load_records()
    
    def _load_records(self):
        """Bellek kayıtlarını yükle"""
        records_file = self.data_dir / "memory_records.json"
        if records_file.exists():
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, record in data.items():
                        self.memory_records[key] = MemoryRecord(**record)
            except Exception as e:
                logger.error(f"Memory records load error: {e}")
    
    def _save_records(self):
        """Bellek kayıtlarını kaydet"""
        records_file = self.data_dir / "memory_records.json"
        data = {k: asdict(v) for k, v in self.memory_records.items()}
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_record_key(self, user_id: str, concept_id: str) -> str:
        return f"{user_id}:{concept_id}"
    
    def calculate_memory_strength(self, record: MemoryRecord) -> float:
        """Ebbinghaus unutma eğrisi ile mevcut bellek gücünü hesapla"""
        last_reviewed = datetime.fromisoformat(record.last_reviewed)
        hours_since_review = (datetime.now() - last_reviewed).total_seconds() / 3600
        
        # Ebbinghaus forgetting curve: R = e^(-t/S)
        # S = stability (ease_factor ve review_count'a bağlı)
        stability = record.ease_factor * (1 + record.review_count * 0.1)
        memory_strength = math.exp(-hours_since_review / (stability * 24))
        
        return max(0.0, min(1.0, memory_strength))
    
    def update_after_review(self, user_id: str, concept_id: str, 
                           quality: int, workspace_id: str = "") -> MemoryRecord:
        """
        SM-2 algoritması ile gözden geçirme sonrası güncelle
        quality: 0-5 (0=complete blackout, 5=perfect response)
        """
        key = self.get_record_key(user_id, concept_id)
        
        if key not in self.memory_records:
            self.memory_records[key] = MemoryRecord(
                concept_id=concept_id,
                user_id=user_id,
                workspace_id=workspace_id
            )
        
        record = self.memory_records[key]
        record.review_count += 1
        
        if quality >= 3:
            record.correct_count += 1
        else:
            record.incorrect_count += 1
        
        # SM-2 ease factor update
        record.ease_factor = max(1.3, 
            record.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        )
        
        # Calculate next interval
        if quality < 3:
            record.interval_days = 1
        else:
            if record.review_count == 1:
                record.interval_days = 1
            elif record.review_count == 2:
                record.interval_days = 6
            else:
                record.interval_days = record.interval_days * record.ease_factor
        
        record.last_reviewed = datetime.now().isoformat()
        record.memory_strength = 1.0  # Just reviewed
        record.next_review = (datetime.now() + timedelta(days=record.interval_days)).isoformat()
        
        self._save_records()
        return record
    
    def get_concepts_needing_review(self, user_id: str, 
                                    workspace_id: Optional[str] = None) -> List[MemoryRecord]:
        """Tekrar edilmesi gereken kavramları getir"""
        needs_review = []
        
        for key, record in self.memory_records.items():
            if not key.startswith(user_id):
                continue
            if workspace_id and record.workspace_id != workspace_id:
                continue
            
            current_strength = self.calculate_memory_strength(record)
            record.memory_strength = current_strength
            
            if current_strength < OPTIMAL_REVIEW_THRESHOLD:
                needs_review.append(record)
        
        # En düşük bellek gücüne göre sırala
        needs_review.sort(key=lambda x: x.memory_strength)
        return needs_review
    
    def get_forgetting_risk(self, user_id: str, concept_id: str) -> Dict[str, Any]:
        """Unutma riski analizi"""
        key = self.get_record_key(user_id, concept_id)
        
        if key not in self.memory_records:
            return {"risk": "unknown", "strength": 0, "days_until_critical": None}
        
        record = self.memory_records[key]
        current_strength = self.calculate_memory_strength(record)
        
        # Kritik seviyeye düşene kadar gün hesapla
        if current_strength > MIN_MEMORY_THRESHOLD:
            stability = record.ease_factor * (1 + record.review_count * 0.1)
            days_until_critical = -stability * math.log(MIN_MEMORY_THRESHOLD) - \
                                  (datetime.now() - datetime.fromisoformat(record.last_reviewed)).days
            days_until_critical = max(0, days_until_critical)
        else:
            days_until_critical = 0
        
        if current_strength >= 0.8:
            risk = "low"
        elif current_strength >= OPTIMAL_REVIEW_THRESHOLD:
            risk = "moderate"
        elif current_strength >= MIN_MEMORY_THRESHOLD:
            risk = "high"
        else:
            risk = "critical"
        
        return {
            "risk": risk,
            "strength": current_strength,
            "days_until_critical": round(days_until_critical, 1),
            "review_count": record.review_count,
            "next_review": record.next_review
        }


# ============================================================================
# LAYER GENERATORS (12 Katman İçerik Üreticileri)
# ============================================================================

class LayerGenerator:
    """Her katman için içerik üreteci"""
    
    @staticmethod
    def generate_warmup_layer(package: Package, previous_concepts: List[Concept]) -> Layer:
        """1. Katman: Warm-Up - Hafıza Aktivasyonu"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.WARMUP,
            title="🔥 Warm-Up: Hafıza Aktivasyonu",
            description="Önceki öğrenmeleri hatırla ve beynini aktive et",
            estimated_minutes=10,
            content={
                "recall_prompt": "Önceki pakette öğrendiğin 3 kavramı yaz:",
                "previous_concepts": [c.name for c in previous_concepts[-3:]],
                "brain_activation": {
                    "question": f"{package.name} hakkında ne biliyorsun? Tahmin et.",
                    "purpose": "Merak uyandırma ve ön bilgi aktivasyonu"
                }
            },
            questions=[
                Question(
                    id=str(uuid.uuid4()),
                    concept_id="warmup",
                    question_type=QuestionType.FREE_TEXT,
                    difficulty=DifficultyLevel.EASY,
                    question_text="Önceki paketten öğrendiğin en önemli kavram neydi?",
                    points=5
                )
            ]
        )
    
    @staticmethod
    def generate_prime_layer(package: Package) -> Layer:
        """2. Katman: Prime - Merak Uyandırma"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.PRIME,
            title="💡 Prime: Merak Uyandırma",
            description="Bu pakette neler öğreneceksin ve neden önemli",
            estimated_minutes=5,
            content={
                "learning_objectives": [c.name for c in package.concepts],
                "curiosity_question": f"{package.name} konusunda en merak ettiğin şey ne?",
                "real_world_relevance": f"Bu bilgi şu alanlarda kullanılıyor...",
                "mind_map_preview": {
                    "center": package.name,
                    "branches": [c.name for c in package.concepts[:4]]
                }
            }
        )
    
    @staticmethod
    def generate_acquire_layer(package: Package) -> Layer:
        """3. Katman: Acquire - Ana İçerik (Çoklu Format)"""
        multi_format_content = {}
        for concept in package.concepts:
            multi_format_content[concept.id] = {
                "verbal": concept.description,
                "visual": f"[Görsel/Animasyon: {concept.name}]",
                "analogy": f"{concept.name} şuna benzer: ...",
                "mathematical": concept.content.get("formula", ""),
                "interactive": f"[İnteraktif: {concept.name} simülasyonu]"
            }
        
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.ACQUIRE,
            title="📚 Acquire: Ana İçerik",
            description="Kavramları birden fazla formatta öğren",
            estimated_minutes=30,
            content={
                "concepts": multi_format_content,
                "format_order": ["analogy", "visual", "verbal", "mathematical", "interactive"]
            }
        )
    
    @staticmethod
    def generate_interrogate_layer(package: Package) -> Layer:
        """4. Katman: Interrogate - Neden/Nasıl Sorgulaması"""
        why_questions = []
        how_questions = []
        what_if_questions = []
        
        for concept in package.concepts:
            why_questions.append(f"Neden {concept.name} gerekli?")
            how_questions.append(f"{concept.name} nasıl çalışır?")
            what_if_questions.append(f"{concept.name} olmasaydı ne olurdu?")
        
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.INTERROGATE,
            title="🔍 Interrogate: Derinleştirme",
            description="Neden ve nasıl sorularıyla derinleş",
            estimated_minutes=10,
            content={
                "why_questions": why_questions,
                "how_questions": how_questions,
                "what_if_questions": what_if_questions
            },
            questions=[
                Question(
                    id=str(uuid.uuid4()),
                    concept_id=package.concepts[0].id if package.concepts else "",
                    question_type=QuestionType.FREE_TEXT,
                    difficulty=DifficultyLevel.MEDIUM,
                    question_text=why_questions[0] if why_questions else "Bu kavram neden önemli?",
                    points=15
                )
            ]
        )
    
    @staticmethod
    def generate_practice_layer(package: Package) -> Layer:
        """5. Katman: Practice - Kademeli Problem Çözme"""
        questions = []
        difficulty_levels = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, 
                           DifficultyLevel.HARD, DifficultyLevel.EXPERT]
        
        for i, level in enumerate(difficulty_levels):
            questions.append(
                Question(
                    id=str(uuid.uuid4()),
                    concept_id=package.concepts[0].id if package.concepts else "",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    difficulty=level,
                    question_text=f"[Level {i+1}] {package.name} uygulaması",
                    options=["A", "B", "C", "D"],
                    correct_answer="A",
                    hints=[
                        "İpucu 1: Stratejik yaklaşım",
                        "İpucu 2: İlk adım",
                        "İpucu 3: Detaylı yönlendirme"
                    ],
                    points=10 * (i + 1)
                )
            )
        
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.PRACTICE,
            title="💪 Practice: Kademeli Problem Çözme",
            description="Kolaydan zora problemler çöz",
            estimated_minutes=45,
            content={
                "hint_system": True,
                "hint_penalty": 5,  # XP penalty per hint
                "show_solution_after": 3  # attempts
            },
            questions=questions
        )
    
    @staticmethod
    def generate_connect_layer(package: Package) -> Layer:
        """6. Katman: Connect - Bağlantılar & Analojiler"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.CONNECT,
            title="🔗 Connect: Bağlantılar & Analojiler",
            description="Öğrendiklerini mevcut bilgilerine bağla",
            estimated_minutes=10,
            content={
                "concept_map": {
                    "central": package.name,
                    "connections": [
                        {"from": package.name, "to": c.name, "relation": "includes"}
                        for c in package.concepts
                    ]
                },
                "analogy_exercise": {
                    "prompt": f"{package.name} şuna benzer: _____ çünkü: _____",
                    "example_analogies": []
                },
                "real_world_connections": []
            }
        )
    
    @staticmethod
    def generate_challenge_layer(package: Package) -> Layer:
        """7. Katman: Challenge - Zorlu Problem / Edge Cases"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.CHALLENGE,
            title="⚔️ Challenge: Boss Battle",
            description="Sınırlarını zorla, edge case'leri keşfet",
            estimated_minutes=15,
            content={
                "boss_problem": {
                    "title": f"{package.name} Boss Challenge",
                    "description": "Bu paketteki en zorlu problem",
                    "reward_xp": 100
                },
                "edge_cases": [
                    "Sınır durumu 1: ...",
                    "Sınır durumu 2: ...",
                    "Sınır durumu 3: ..."
                ]
            },
            questions=[
                Question(
                    id=str(uuid.uuid4()),
                    concept_id="boss",
                    question_type=QuestionType.FREE_TEXT,
                    difficulty=DifficultyLevel.EXPERT,
                    question_text=f"{package.name} için en zorlu senaryo",
                    points=100,
                    time_limit_seconds=600
                )
            ]
        )
    
    @staticmethod
    def generate_error_lab_layer(package: Package) -> Layer:
        """8. Katman: Error Lab - Yaygın Hatalar"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.ERROR_LAB,
            title="⚠️ Error Lab: Yaygın Hatalar",
            description="Hataları tanı, tuzaklardan kaçın",
            estimated_minutes=10,
            content={
                "common_misconceptions": [
                    {"wrong": "Yanlış anlama 1", "correct": "Doğrusu"},
                    {"wrong": "Yanlış anlama 2", "correct": "Doğrusu"}
                ],
                "error_finding_exercise": {
                    "buggy_solution": "Hatalı çözüm burada...",
                    "find_the_bug": True
                }
            },
            questions=[
                Question(
                    id=str(uuid.uuid4()),
                    concept_id="error",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    difficulty=DifficultyLevel.MEDIUM,
                    question_text="Bu çözümdeki hata nedir?",
                    options=["Hata A", "Hata B", "Hata C", "Hata yok"],
                    correct_answer="Hata B",
                    points=20
                )
            ]
        )
    
    @staticmethod
    def generate_feynman_layer(package: Package) -> Layer:
        """9. Katman: Feynman - Anlat & Öğret"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.FEYNMAN,
            title="🎤 Feynman: Anlat & Öğret",
            description="Öğrendiklerini kendi kelimelerinle açıkla",
            estimated_minutes=20,
            content={
                "target_audiences": [
                    {"id": "child", "label": "5 Yaş Çocuğu", "bonus_xp": 50},
                    {"id": "student", "label": "Lise Öğrencisi", "bonus_xp": 30},
                    {"id": "expert", "label": "Uzman", "bonus_xp": 20}
                ],
                "formats": ["audio", "text", "diagram"],
                "checklist": [
                    f"{package.name} ne işe yarar?",
                    "Nasıl çalışır?",
                    "Neden önemli?",
                    "Sınırlamaları neler?",
                    "Bir analoji kullan"
                ],
                "passing_score": 85
            }
        )
    
    @staticmethod
    def generate_transfer_layer(package: Package) -> Layer:
        """10. Katman: Transfer - Farklı Bağlamda Uygulama"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.TRANSFER,
            title="🌍 Transfer: Farklı Bağlamda Uygula",
            description="Öğrendiklerini yeni durumlara transfer et",
            estimated_minutes=15,
            content={
                "transfer_scenarios": [
                    {"domain": "Finans", "problem": f"{package.name} finansta nasıl uygulanır?"},
                    {"domain": "Sağlık", "problem": f"{package.name} sağlıkta nasıl uygulanır?"},
                    {"domain": "Günlük Hayat", "problem": f"{package.name} günlük hayatta nerede?"}
                ],
                "creative_application": {
                    "prompt": f"Kendi {package.name} uygulama senaryonu yaz"
                }
            }
        )
    
    @staticmethod
    def generate_meta_reflection_layer(package: Package) -> Layer:
        """11. Katman: Meta-Reflection - Öğrenme Analizi"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.META_REFLECTION,
            title="🪞 Meta-Reflection: Öz Değerlendirme",
            description="Öğrenme sürecini analiz et",
            estimated_minutes=5,
            content={
                "self_assessment": [
                    {"question": "Bu pakette en iyi anladığım konu:", "type": "text"},
                    {"question": "Hala belirsiz olan:", "type": "text"},
                    {"question": "Benim için en etkili öğrenme yöntemi:", "type": "choice",
                     "options": ["Görsel", "Pratik", "Analoji", "Anlatma"]}
                ],
                "difficulty_map": {
                    "concepts": [c.name for c in package.concepts],
                    "scale": "1-5"
                },
                "strategy_note": "Bir dahaki sefere neyi farklı yapardın?"
            }
        )
    
    @staticmethod
    def generate_consolidate_layer(package: Package, next_package: Optional[Package]) -> Layer:
        """12. Katman: Consolidate - Özet & Bağlantı"""
        return Layer(
            id=str(uuid.uuid4()),
            layer_type=LayerType.CONSOLIDATE,
            title="📦 Consolidate: Özet & İleri Bağlantı",
            description="Öğrenilenleri paketle ve sonrakine hazırlan",
            estimated_minutes=5,
            content={
                "summary": {
                    "key_takeaways": [c.name for c in package.concepts],
                    "formulas": [],
                    "important_points": []
                },
                "next_preview": {
                    "title": next_package.name if next_package else "Aşama Sonu",
                    "connection": f"Bu paket, sonraki paketle şöyle bağlantılı..."
                },
                "spaced_repetition_schedule": {
                    "review_1": "24 saat sonra",
                    "review_2": "3 gün sonra",
                    "review_3": "1 hafta sonra",
                    "review_4": "2 hafta sonra"
                },
                "celebration": True
            }
        )
    
    @classmethod
    def generate_all_layers(cls, package: Package, 
                           previous_concepts: List[Concept],
                           next_package: Optional[Package] = None) -> List[Layer]:
        """Bir paket için tüm 12 katmanı oluştur"""
        return [
            cls.generate_warmup_layer(package, previous_concepts),
            cls.generate_prime_layer(package),
            cls.generate_acquire_layer(package),
            cls.generate_interrogate_layer(package),
            cls.generate_practice_layer(package),
            cls.generate_connect_layer(package),
            cls.generate_challenge_layer(package),
            cls.generate_error_lab_layer(package),
            cls.generate_feynman_layer(package),
            cls.generate_transfer_layer(package),
            cls.generate_meta_reflection_layer(package),
            cls.generate_consolidate_layer(package, next_package)
        ]


# ============================================================================
# ROADMAP GENERATOR
# ============================================================================

class RoadmapGenerator:
    """Kaynaklardan roadmap oluşturucu"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def analyze_source(self, source: Dict[str, str]) -> Dict[str, Any]:
        """Kaynağı analiz et ve konu çıkar"""
        # TODO: RAG ile kaynak analizi
        return {
            "topics": [],
            "difficulty": "medium",
            "estimated_hours": 10,
            "prerequisites": []
        }
    
    async def generate_roadmap(self, 
                              user_id: str,
                              name: str,
                              description: str,
                              target_goal: str,
                              sources: List[Dict[str, str]]) -> Workspace:
        """Kaynaklardan komple roadmap oluştur"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            target_goal=target_goal,
            source_materials=sources
        )
        
        # TODO: LLM ile kaynak analizi ve otomatik stage/package oluşturma
        # Şimdilik basit bir yapı oluştur
        
        return workspace
    
    def create_manual_stage(self, 
                           workspace_id: str,
                           name: str,
                           description: str,
                           order: int) -> Stage:
        """Manuel aşama oluştur"""
        return Stage(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=name,
            description=description,
            order=order
        )
    
    def create_manual_package(self,
                             stage_id: str,
                             name: str,
                             description: str,
                             order: int,
                             concepts: List[Dict[str, Any]]) -> Package:
        """Manuel paket oluştur"""
        concept_objects = [
            Concept(
                id=str(uuid.uuid4()),
                name=c["name"],
                description=c.get("description", ""),
                keywords=c.get("keywords", []),
                difficulty=DifficultyLevel(c.get("difficulty", "medium")),
                estimated_minutes=c.get("estimated_minutes", 30)
            )
            for c in concepts
        ]
        
        package = Package(
            id=str(uuid.uuid4()),
            stage_id=stage_id,
            name=name,
            description=description,
            order=order,
            concepts=concept_objects
        )
        
        # 12 katmanı oluştur
        package.layers = LayerGenerator.generate_all_layers(package, [], None)
        
        return package


# ============================================================================
# SESSION PLANNER
# ============================================================================

class SessionPlanner:
    """Günlük öğrenme oturumu planlayıcı"""
    
    def __init__(self, memory_engine: MemoryEngine):
        self.memory_engine = memory_engine
    
    def plan_daily_session(self,
                          user_id: str,
                          workspace: Workspace,
                          available_minutes: int = 45,
                          learner_profile: Optional[LearnerProfile] = None) -> DailySession:
        """Günlük oturum planla"""
        session = DailySession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            workspace_id=workspace.id,
            date=datetime.now().strftime("%Y-%m-%d"),
            planned_minutes=available_minutes
        )
        
        # 1. Tekrar edilmesi gereken konuları bul
        needs_review = self.memory_engine.get_concepts_needing_review(user_id, workspace.id)
        
        refresh_time = min(15, available_minutes // 3)  # Max 15 dk veya 1/3
        remaining_time = available_minutes - refresh_time
        
        for record in needs_review[:3]:  # Max 3 refresh item
            session.refresh_items.append({
                "concept_id": record.concept_id,
                "memory_strength": record.memory_strength,
                "estimated_minutes": 5
            })
        
        # 2. Yeni içerik
        current_package = self._get_current_package(workspace)
        if current_package:
            current_layer = current_package.layers[current_package.current_layer_index] \
                if current_package.current_layer_index < len(current_package.layers) else None
            
            if current_layer:
                session.new_content.append({
                    "package_id": current_package.id,
                    "package_name": current_package.name,
                    "layer_type": current_layer.layer_type.value,
                    "layer_title": current_layer.title,
                    "estimated_minutes": current_layer.estimated_minutes
                })
        
        # 3. Challenge (opsiyonel)
        if remaining_time > 30:
            session.challenges.append({
                "type": "boss_problem",
                "estimated_minutes": 10,
                "bonus_xp": 50
            })
        
        return session
    
    def _get_current_package(self, workspace: Workspace) -> Optional[Package]:
        """Mevcut aktif paketi bul"""
        for stage in workspace.stages:
            for package in stage.packages:
                if package.status == PackageStatus.IN_PROGRESS:
                    return package
                if package.status == PackageStatus.AVAILABLE:
                    return package
        return None


# ============================================================================
# PROGRESS TRACKER
# ============================================================================

class ProgressTracker:
    """İlerleme takip ve XP sistemi"""
    
    # XP rewards
    XP_LAYER_COMPLETE = 25
    XP_PACKAGE_COMPLETE = 100
    XP_STAGE_COMPLETE = 500
    XP_FEYNMAN_PASS = 75
    XP_CHALLENGE_COMPLETE = 50
    XP_STREAK_BONUS = 10  # Per day
    
    def __init__(self, data_dir: str = "data/full_meta"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_level(self, total_xp: int) -> int:
        """XP'den level hesapla"""
        # Level formula: level = floor(sqrt(xp / 100))
        return max(1, int(math.sqrt(total_xp / 100)))
    
    def xp_for_next_level(self, current_level: int) -> int:
        """Sonraki level için gereken XP"""
        return ((current_level + 1) ** 2) * 100
    
    def award_xp(self, workspace: Workspace, amount: int, reason: str) -> Dict[str, Any]:
        """XP ver ve level up kontrolü yap"""
        old_level = workspace.level
        workspace.total_xp += amount
        new_level = self.calculate_level(workspace.total_xp)
        workspace.level = new_level
        
        level_up = new_level > old_level
        
        return {
            "xp_earned": amount,
            "reason": reason,
            "total_xp": workspace.total_xp,
            "level": new_level,
            "level_up": level_up,
            "xp_to_next": self.xp_for_next_level(new_level) - workspace.total_xp
        }
    
    def complete_layer(self, package: Package, layer_index: int, 
                      score: float) -> Dict[str, Any]:
        """Katman tamamlama"""
        if layer_index >= len(package.layers):
            return {"error": "Invalid layer index"}
        
        layer = package.layers[layer_index]
        layer.completed = True
        layer.score = score
        layer.completed_at = datetime.now().isoformat()
        
        package.current_layer_index = layer_index + 1
        
        # XP hesapla (score'a göre bonus)
        base_xp = self.XP_LAYER_COMPLETE
        bonus_xp = int(base_xp * (score / 100) * 0.5)
        
        return {
            "layer_completed": layer.layer_type.value,
            "score": score,
            "xp_earned": base_xp + bonus_xp,
            "next_layer_index": package.current_layer_index,
            "package_progress": package.current_layer_index / len(package.layers) * 100
        }
    
    def complete_package(self, package: Package) -> Dict[str, Any]:
        """Paket tamamlama"""
        package.status = PackageStatus.COMPLETED
        package.completed_at = datetime.now().isoformat()
        
        # Ortalama skor hesapla
        scores = [l.score for l in package.layers if l.score is not None]
        package.overall_score = sum(scores) / len(scores) if scores else 0
        
        return {
            "package_completed": package.name,
            "overall_score": package.overall_score,
            "xp_earned": self.XP_PACKAGE_COMPLETE,
            "time_spent_hours": package.actual_hours
        }
    
    def update_streak(self, workspace: Workspace) -> Dict[str, Any]:
        """Streak güncelle"""
        today = datetime.now().date()
        
        if workspace.last_activity:
            last_date = datetime.fromisoformat(workspace.last_activity).date()
            days_diff = (today - last_date).days
            
            if days_diff == 1:
                workspace.streak_days += 1
            elif days_diff > 1:
                workspace.streak_days = 1  # Reset
            # days_diff == 0: aynı gün, streak değişmez
        else:
            workspace.streak_days = 1
        
        workspace.last_activity = datetime.now().isoformat()
        
        # Streak milestone ödülleri
        milestone_xp = 0
        milestone = None
        if workspace.streak_days in [7, 30, 100, 365]:
            milestone = workspace.streak_days
            milestone_xp = workspace.streak_days * 10
        
        return {
            "streak_days": workspace.streak_days,
            "streak_bonus_xp": self.XP_STREAK_BONUS * workspace.streak_days,
            "milestone": milestone,
            "milestone_xp": milestone_xp
        }


# ============================================================================
# FEYNMAN EVALUATOR
# ============================================================================

class FeynmanEvaluator:
    """Feynman tekniği değerlendirici"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def evaluate_submission(self, 
                                 submission: FeynmanSubmission,
                                 package: Package) -> Dict[str, Any]:
        """Kullanıcı anlatımını değerlendir"""
        # TODO: LLM ile detaylı analiz
        
        # Şimdilik basit bir değerlendirme
        required_concepts = [c.name.lower() for c in package.concepts]
        content_lower = submission.content.lower()
        
        covered = []
        missing = []
        
        for concept in required_concepts:
            if concept in content_lower:
                covered.append(concept)
            else:
                missing.append(concept)
        
        coverage_score = len(covered) / len(required_concepts) * 100 if required_concepts else 0
        
        # Hedef kitleye göre bonus/penaltı
        audience_multiplier = {
            "child": 1.2,  # Zor, bonus
            "student": 1.0,
            "expert": 0.9  # Kolay, az bonus
        }.get(submission.target_audience, 1.0)
        
        final_score = min(100, coverage_score * audience_multiplier)
        passed = final_score >= 85
        
        analysis = {
            "score": round(final_score, 1),
            "passed": passed,
            "covered_concepts": covered,
            "missing_concepts": missing,
            "strengths": ["İyi analoji kullanımı"] if coverage_score > 70 else [],
            "improvements": [f"'{m}' konusunu dahil et" for m in missing[:3]],
            "feedback": "Harika bir açıklama!" if passed else "Eksik konuları tamamla ve tekrar dene."
        }
        
        submission.ai_analysis = analysis
        submission.score = final_score
        submission.passed = passed
        submission.missing_concepts = missing
        submission.feedback = analysis["feedback"]
        
        return analysis


# ============================================================================
# MAIN LEARNING ENGINE
# ============================================================================

class FullMetaEngine:
    """Ana öğrenme motoru - Tüm bileşenleri koordine eder"""
    
    def __init__(self, data_dir: str = "data/full_meta", llm_client=None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_engine = MemoryEngine(str(self.data_dir))
        self.roadmap_generator = RoadmapGenerator(llm_client)
        self.progress_tracker = ProgressTracker(str(self.data_dir))
        self.feynman_evaluator = FeynmanEvaluator(llm_client)
        self.session_planner = SessionPlanner(self.memory_engine)
        
        self.workspaces: Dict[str, Workspace] = {}
        self.learner_profiles: Dict[str, LearnerProfile] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Verileri yükle"""
        workspaces_file = self.data_dir / "workspaces.json"
        if workspaces_file.exists():
            try:
                with open(workspaces_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # TODO: Deserialize properly
            except Exception as e:
                logger.error(f"Load workspaces error: {e}")
    
    def _save_data(self):
        """Verileri kaydet"""
        workspaces_file = self.data_dir / "workspaces.json"
        # TODO: Serialize properly
    
    # Workspace Operations
    async def create_workspace(self,
                              user_id: str,
                              name: str,
                              description: str,
                              target_goal: str,
                              sources: List[Dict[str, str]] = None) -> Workspace:
        """Yeni workspace oluştur"""
        workspace = await self.roadmap_generator.generate_roadmap(
            user_id, name, description, target_goal, sources or []
        )
        self.workspaces[workspace.id] = workspace
        self._save_data()
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Workspace getir"""
        return self.workspaces.get(workspace_id)
    
    def get_user_workspaces(self, user_id: str) -> List[Workspace]:
        """Kullanıcının workspace'lerini getir"""
        return [w for w in self.workspaces.values() if w.user_id == user_id]
    
    # Stage Operations
    def add_stage(self, workspace_id: str, name: str, 
                 description: str) -> Optional[Stage]:
        """Workspace'e aşama ekle"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        order = len(workspace.stages)
        stage = self.roadmap_generator.create_manual_stage(
            workspace_id, name, description, order
        )
        workspace.stages.append(stage)
        
        if order == 0:
            stage.status = PackageStatus.AVAILABLE
        
        self._save_data()
        return stage
    
    # Package Operations
    def add_package(self, stage_id: str, name: str, description: str,
                   concepts: List[Dict[str, Any]]) -> Optional[Package]:
        """Aşamaya paket ekle"""
        for workspace in self.workspaces.values():
            for stage in workspace.stages:
                if stage.id == stage_id:
                    order = len(stage.packages)
                    package = self.roadmap_generator.create_manual_package(
                        stage_id, name, description, order, concepts
                    )
                    stage.packages.append(package)
                    
                    if order == 0 and stage.status == PackageStatus.AVAILABLE:
                        package.status = PackageStatus.AVAILABLE
                    
                    self._save_data()
                    return package
        return None
    
    def start_package(self, package_id: str) -> Optional[Package]:
        """Paketi başlat"""
        for workspace in self.workspaces.values():
            for stage in workspace.stages:
                for package in stage.packages:
                    if package.id == package_id:
                        package.status = PackageStatus.IN_PROGRESS
                        package.started_at = datetime.now().isoformat()
                        self._save_data()
                        return package
        return None
    
    def get_current_layer(self, package_id: str) -> Optional[Tuple[Package, Layer]]:
        """Mevcut katmanı getir"""
        for workspace in self.workspaces.values():
            for stage in workspace.stages:
                for package in stage.packages:
                    if package.id == package_id:
                        if package.current_layer_index < len(package.layers):
                            return (package, package.layers[package.current_layer_index])
                        return (package, None)
        return None
    
    # Learning Operations
    def complete_layer(self, package_id: str, score: float) -> Dict[str, Any]:
        """Katman tamamla"""
        result = self.get_current_layer(package_id)
        if not result:
            return {"error": "Package not found"}
        
        package, layer = result
        if not layer:
            return {"error": "No more layers"}
        
        layer_result = self.progress_tracker.complete_layer(
            package, package.current_layer_index - 1, score
        )
        
        # Tüm katmanlar tamamlandı mı?
        if package.current_layer_index >= len(package.layers):
            package_result = self.progress_tracker.complete_package(package)
            layer_result["package_completed"] = True
            layer_result["package_result"] = package_result
        
        self._save_data()
        return layer_result
    
    def submit_feynman(self, user_id: str, package_id: str,
                      target_audience: str, format: str,
                      content: str) -> FeynmanSubmission:
        """Feynman anlatımı gönder"""
        submission = FeynmanSubmission(
            id=str(uuid.uuid4()),
            user_id=user_id,
            package_id=package_id,
            target_audience=target_audience,
            format=format,
            content=content,
            submitted_at=datetime.now().isoformat()
        )
        
        # TODO: Async evaluate
        return submission
    
    async def evaluate_feynman(self, submission: FeynmanSubmission,
                              package_id: str) -> Dict[str, Any]:
        """Feynman anlatımını değerlendir"""
        result = self.get_current_layer(package_id)
        if not result:
            return {"error": "Package not found"}
        
        package, _ = result
        return await self.feynman_evaluator.evaluate_submission(submission, package)
    
    # Session Operations
    def plan_session(self, user_id: str, workspace_id: str,
                    available_minutes: int = 45) -> DailySession:
        """Günlük oturum planla"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        profile = self.learner_profiles.get(user_id)
        return self.session_planner.plan_daily_session(
            user_id, workspace, available_minutes, profile
        )
    
    # Memory Operations
    def record_review(self, user_id: str, concept_id: str,
                     quality: int, workspace_id: str = "") -> MemoryRecord:
        """Tekrar kaydet"""
        return self.memory_engine.update_after_review(
            user_id, concept_id, quality, workspace_id
        )
    
    def get_review_needed(self, user_id: str, 
                         workspace_id: str = None) -> List[Dict[str, Any]]:
        """Tekrar gereken konuları getir"""
        records = self.memory_engine.get_concepts_needing_review(user_id, workspace_id)
        return [
            {
                "concept_id": r.concept_id,
                "memory_strength": round(r.memory_strength, 2),
                "days_since_review": (datetime.now() - datetime.fromisoformat(r.last_reviewed)).days,
                "review_count": r.review_count
            }
            for r in records
        ]
    
    # Stats & Progress
    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Workspace istatistiklerini getir"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return {}
        
        total_packages = sum(len(s.packages) for s in workspace.stages)
        completed_packages = sum(
            1 for s in workspace.stages 
            for p in s.packages 
            if p.status == PackageStatus.COMPLETED
        )
        
        total_layers = sum(
            len(p.layers) for s in workspace.stages for p in s.packages
        )
        completed_layers = sum(
            sum(1 for l in p.layers if l.completed)
            for s in workspace.stages for p in s.packages
        )
        
        return {
            "workspace_id": workspace_id,
            "name": workspace.name,
            "total_stages": len(workspace.stages),
            "total_packages": total_packages,
            "completed_packages": completed_packages,
            "total_layers": total_layers,
            "completed_layers": completed_layers,
            "overall_progress": round(completed_layers / total_layers * 100, 1) if total_layers else 0,
            "total_xp": workspace.total_xp,
            "level": workspace.level,
            "streak_days": workspace.streak_days,
            "estimated_hours_remaining": workspace.estimated_total_hours - workspace.actual_total_hours
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_engine_instance: Optional[FullMetaEngine] = None

def get_full_meta_engine() -> FullMetaEngine:
    """Singleton engine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = FullMetaEngine()
    return _engine_instance
