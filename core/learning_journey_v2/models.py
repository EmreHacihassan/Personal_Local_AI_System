"""
🎓 Learning Journey V2 - Data Models
Kapsamlı veri modelleri: Stage, Package, Exam, Certificate

Her Stage birden fazla Package içerir.
Her Package müfredatın bir bölümünü kapsar.
Sınavlar: Test, Feynman, Pratik Egzersiz, Sunum vb.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid


# ==================== ENUMS ====================

class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    UPPER_INTERMEDIATE = "upper_intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class ContentType(str, Enum):
    """İçerik türleri"""
    TEXT = "text"                      # Yazılı konu anlatımı
    VIDEO = "video"                    # Video içerik
    IMAGE = "image"                    # Görsel/Diagram
    INFOGRAPHIC = "infographic"        # İnfografik
    INTERACTIVE = "interactive"        # İnteraktif içerik
    SIMULATION = "simulation"          # Simülasyon
    MINDMAP = "mindmap"                # Zihin haritası
    FLASHCARD = "flashcard"            # Flashcard
    FORMULA_SHEET = "formula_sheet"    # Formül sayfası
    SUMMARY = "summary"                # Özet
    EXAMPLE = "example"                # Çözümlü örnek
    CASE_STUDY = "case_study"          # Vaka çalışması


class ExamType(str, Enum):
    """Sınav türleri - 2026 Bilimsel Tekniklere Dayalı"""
    MULTIPLE_CHOICE = "multiple_choice"          # Çoktan seçmeli
    TRUE_FALSE = "true_false"                    # Doğru/Yanlış
    FILL_BLANK = "fill_blank"                    # Boşluk doldurma
    SHORT_ANSWER = "short_answer"                # Kısa cevap
    ESSAY = "essay"                              # Kompozisyon
    FEYNMAN = "feynman"                          # Feynman tekniği - anlatarak öğrenme
    TEACH_BACK = "teach_back"                    # Geri öğretme
    CONCEPT_MAP = "concept_map"                  # Kavram haritası oluşturma
    PROBLEM_SOLVING = "problem_solving"          # Problem çözme
    CODE_CHALLENGE = "code_challenge"            # Kod yazma (programlama için)
    ORAL_PRESENTATION = "oral_presentation"      # Sözlü sunum
    PEER_REVIEW = "peer_review"                  # Akran değerlendirmesi
    SELF_ASSESSMENT = "self_assessment"          # Öz değerlendirme
    PRACTICAL = "practical"                      # Pratik uygulama
    SIMULATION_BASED = "simulation_based"        # Simülasyon tabanlı


class ExerciseType(str, Enum):
    """Pratik egzersiz türleri"""
    DRILL = "drill"                    # Tekrar alıştırması
    SPACED_REPETITION = "spaced"       # Aralıklı tekrar
    ELABORATION = "elaboration"        # Detaylandırma
    INTERLEAVING = "interleaving"      # Karma pratik
    RETRIEVAL = "retrieval"            # Hatırlama pratiği
    DUAL_CODING = "dual_coding"        # Çift kodlama
    CONCRETE_EXAMPLES = "concrete"     # Somut örnekler
    GENERATION = "generation"          # Üretim
    REFLECTION = "reflection"          # Yansıtma
    METACOGNITION = "metacognition"    # Üst biliş


class PackageType(str, Enum):
    """Paket türleri"""
    LEARNING = "learning"              # Öğrenme paketi
    PRACTICE = "practice"              # Pratik paketi
    EXAM = "exam"                      # Sınav paketi
    REVIEW = "review"                  # Tekrar paketi
    CLOSURE = "closure"                # Kapanış paketi (stage sonu)
    INTRO = "intro"                    # Giriş paketi (stage başı)


class StageStatus(str, Enum):
    """Stage durumları"""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MASTERED = "mastered"


class PackageStatus(str, Enum):
    """Paket durumları"""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"            # Tamamlandı (eski format uyumluluk)
    PASSED = "passed"                  # Geçti
    FAILED = "failed"                  # Kaldı - tekrar gerekli
    MASTERED = "mastered"              # Mükemmel
    NEEDS_REVIEW = "needs_review"      # Tekrar gerekiyor


# ==================== DATA CLASSES ====================

@dataclass
class LearningGoal:
    """Kullanıcının öğrenme hedefi - detaylı tanımlama"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    
    # Temel bilgiler
    title: str = ""                                # "AYT Matematik Hazırlığı"
    description: str = ""                          # Detaylı açıklama
    subject: str = ""                              # "Matematik"
    category: str = ""                             # "Üniversite Sınavı"
    
    # Hedef detayları
    target_outcome: str = ""                       # "AYT'de 40 net yapmak"
    motivation: str = ""                           # Neden öğrenmek istiyor
    prior_knowledge: str = ""                      # Mevcut bilgi seviyesi
    learning_style: str = ""                       # Öğrenme stili tercihi
    
    # Zaman planlaması
    deadline: Optional[str] = None                 # "2026-06-15"
    daily_hours: float = 2.0                       # Günlük çalışma süresi
    preferred_times: List[str] = field(default_factory=list)  # ["morning", "evening"]
    
    # Kapsam
    topics_to_include: List[str] = field(default_factory=list)
    topics_to_exclude: List[str] = field(default_factory=list)
    focus_areas: List[str] = field(default_factory=list)      # Odaklanılacak alanlar
    weak_areas: List[str] = field(default_factory=list)       # Zayıf alanlar
    
    # Tercihler
    content_preferences: List[ContentType] = field(default_factory=list)
    exam_preferences: List[ExamType] = field(default_factory=list)
    difficulty_preference: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    language: str = "tr"
    
    # Meta
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "category": self.category,
            "target_outcome": self.target_outcome,
            "motivation": self.motivation,
            "prior_knowledge": self.prior_knowledge,
            "learning_style": self.learning_style,
            "deadline": self.deadline,
            "daily_hours": self.daily_hours,
            "preferred_times": self.preferred_times,
            "topics_to_include": self.topics_to_include,
            "topics_to_exclude": self.topics_to_exclude,
            "focus_areas": self.focus_areas,
            "weak_areas": self.weak_areas,
            "content_preferences": [c.value for c in self.content_preferences],
            "exam_preferences": [e.value for e in self.exam_preferences],
            "difficulty_preference": self.difficulty_preference.value,
            "language": self.language,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class ContentBlock:
    """Tek bir içerik bloğu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ContentType = ContentType.TEXT
    title: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    media_url: Optional[str] = None
    duration_minutes: int = 5
    order: int = 0
    is_required: bool = True
    source: str = "ai"  # ai, rag, web, manual
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        # Content'i string olarak da sun (frontend uyumu için)
        content_str = ""
        if isinstance(self.content, dict):
            content_str = self.content.get("markdown", "") or self.content.get("text", "")
        elif isinstance(self.content, str):
            content_str = self.content
        
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ContentType) else self.type,
            "block_type": self.type.value if isinstance(self.type, ContentType) else self.type,
            "title": self.title,
            "content": content_str,
            "content_data": self.content if isinstance(self.content, dict) else {"text": self.content},
            "media_url": self.media_url,
            "duration_minutes": self.duration_minutes,
            "order": self.order,
            "is_required": self.is_required,
            "source": self.source,
            "metadata": self.metadata,
            "completed": False
        }


@dataclass
class ExamQuestion:
    """Sınav sorusu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ExamType = ExamType.MULTIPLE_CHOICE
    question: str = ""
    options: Optional[List[str]] = None           # Çoktan seçmeli için
    correct_answer: Optional[str] = None
    explanation: str = ""
    points: int = 10
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    topic: str = ""
    subtopic: str = ""
    hints: List[str] = field(default_factory=list)
    rubric: Optional[Dict[str, Any]] = None       # Değerlendirme kriterleri
    time_limit_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ExamType) else self.type,
            "question": self.question,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "points": self.points,
            "difficulty": self.difficulty.value if isinstance(self.difficulty, DifficultyLevel) else self.difficulty,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "hints": self.hints,
            "rubric": self.rubric,
            "time_limit_seconds": self.time_limit_seconds
        }


@dataclass
class Exam:
    """Sınav yapısı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    type: ExamType = ExamType.MULTIPLE_CHOICE     # Ana sınav türü
    questions: List[ExamQuestion] = field(default_factory=list)
    
    # Sınav ayarları
    time_limit_minutes: Optional[int] = None
    passing_score: float = 70.0                    # Geçme notu (%)
    max_attempts: int = 3
    shuffle_questions: bool = True
    shuffle_options: bool = True
    show_feedback: bool = True
    
    # Puanlama
    total_points: int = 0
    weight_in_package: float = 1.0                 # Paket içindeki ağırlık
    
    # Deneme sayısı
    attempts: int = 0
    
    # Özel sınav türleri için
    feynman_config: Optional[Dict[str, Any]] = None      # Feynman tekniği ayarları
    presentation_config: Optional[Dict[str, Any]] = None  # Sunum ayarları
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.type.value if isinstance(self.type, ExamType) else self.type,
            "exam_type": self.type.value if isinstance(self.type, ExamType) else self.type,
            "questions": [q.to_dict() for q in self.questions],
            "time_limit_minutes": self.time_limit_minutes or 30,
            "passing_score": self.passing_score,
            "max_attempts": self.max_attempts,
            "attempts": self.attempts,
            "shuffle_questions": self.shuffle_questions,
            "shuffle_options": self.shuffle_options,
            "show_feedback": self.show_feedback,
            "total_points": self.total_points,
            "weight_in_package": self.weight_in_package,
            "feynman_config": self.feynman_config,
            "presentation_config": self.presentation_config
        }


@dataclass
class Exercise:
    """Pratik egzersiz"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ExerciseType = ExerciseType.DRILL
    title: str = ""
    instructions: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    duration_minutes: int = 10
    xp_reward: int = 20
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    is_required: bool = True
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ExerciseType) else self.type,
            "title": self.title,
            "instructions": self.instructions,
            "content": self.content,
            "duration_minutes": self.duration_minutes,
            "xp_reward": self.xp_reward,
            "difficulty": self.difficulty.value if isinstance(self.difficulty, DifficultyLevel) else self.difficulty,
            "is_required": self.is_required,
            "order": self.order
        }


@dataclass
class Package:
    """
    Öğrenme Paketi - Stage'in yapı taşı
    
    Her paket müfredatın belirli bir bölümünü kapsar ve şunları içerir:
    - Konu anlatımları (metin, video, görsel)
    - Pratik egzersizler
    - Sınavlar (çeşitli türlerde)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    stage_id: str = ""
    
    # Temel bilgiler
    number: int = 1
    title: str = ""
    description: str = ""
    type: PackageType = PackageType.LEARNING
    
    # Müfredat bağlantısı
    curriculum_section: str = ""                   # Müfredattaki yeri
    topics: List[str] = field(default_factory=list)
    subtopics: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    
    # İçerikler
    content_blocks: List[ContentBlock] = field(default_factory=list)
    exercises: List[Exercise] = field(default_factory=list)
    exams: List[Exam] = field(default_factory=list)
    
    # İlerleme gereksinimleri
    required_content_completion: float = 100.0     # Zorunlu içerik tamamlama (%)
    required_exercise_completion: float = 80.0     # Zorunlu egzersiz tamamlama (%)
    required_exam_score: float = 70.0              # Geçme notu
    
    # Zaman ve zorluk
    estimated_duration_minutes: int = 60
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    
    # XP ve Puanlama
    xp_reward: int = 100
    bonus_xp_conditions: Dict[str, int] = field(default_factory=dict)
    
    # Durum
    status: PackageStatus = PackageStatus.LOCKED
    unlock_requirements: List[str] = field(default_factory=list)  # Önceki paket ID'leri
    
    # Görsel
    theme_color: str = "#6366F1"
    icon: str = "📚"
    
    # LLM Enhancement
    llm_content_ready: bool = False  # LLM ile içerik zenginleştirildi mi?
    
    # Meta
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "stage_id": self.stage_id,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "type": self.type.value if isinstance(self.type, PackageType) else self.type,
            "curriculum_section": self.curriculum_section,
            "topics": self.topics,
            "subtopics": self.subtopics,
            "learning_objectives": self.learning_objectives,
            "prerequisites": self.prerequisites,
            "content_blocks": [c.to_dict() for c in self.content_blocks],
            "exercises": [e.to_dict() for e in self.exercises],
            "exams": [e.to_dict() for e in self.exams],
            "required_content_completion": self.required_content_completion,
            "required_exercise_completion": self.required_exercise_completion,
            "required_exam_score": self.required_exam_score,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "difficulty": self.difficulty.value if isinstance(self.difficulty, DifficultyLevel) else self.difficulty,
            "xp_reward": self.xp_reward,
            "bonus_xp_conditions": self.bonus_xp_conditions,
            "status": self.status.value if isinstance(self.status, PackageStatus) else self.status,
            "unlock_requirements": self.unlock_requirements,
            "theme_color": self.theme_color,
            "icon": self.icon,
            "llm_content_ready": self.llm_content_ready,
            "created_at": self.created_at
        }


@dataclass
class Stage:
    """
    Öğrenme Aşaması - Birden fazla paketten oluşur
    
    Her stage:
    - Giriş paketi ile başlar
    - Öğrenme paketleri içerir
    - Kapanış paketi ile biter
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    journey_id: str = ""
    
    # Temel bilgiler
    number: int = 1
    title: str = ""
    description: str = ""
    
    # Paketler
    packages: List[Package] = field(default_factory=list)
    intro_package_id: Optional[str] = None         # Giriş paketi
    closure_package_id: Optional[str] = None       # Kapanış paketi
    
    # Kapsam
    main_topic: str = ""
    covered_topics: List[str] = field(default_factory=list)
    learning_outcomes: List[str] = field(default_factory=list)
    
    # İlerleme
    status: StageStatus = StageStatus.LOCKED
    progress_percentage: float = 0.0
    packages_completed: int = 0
    
    # Değerlendirme
    average_score: float = 0.0
    stars: int = 0                                  # 0-3 yıldız
    
    # Zaman
    estimated_duration_days: int = 7
    actual_duration_days: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # XP
    xp_total: int = 0
    xp_earned: int = 0
    
    # Görsel (Candy Crush style)
    position: Dict[str, float] = field(default_factory=dict)  # x, y koordinatları
    theme: str = "default"
    color_scheme: Dict[str, str] = field(default_factory=dict)
    
    # Unlock
    unlock_requirements: List[str] = field(default_factory=list)  # Önceki stage ID'leri
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "journey_id": self.journey_id,
            "number": self.number,
            "title": self.title,
            "description": self.description,
            "packages": [p.to_dict() for p in self.packages],
            "intro_package_id": self.intro_package_id,
            "closure_package_id": self.closure_package_id,
            "main_topic": self.main_topic,
            "covered_topics": self.covered_topics,
            "learning_outcomes": self.learning_outcomes,
            "status": self.status.value if isinstance(self.status, StageStatus) else self.status,
            "progress_percentage": self.progress_percentage,
            "packages_completed": self.packages_completed,
            "average_score": self.average_score,
            "stars": self.stars,
            "estimated_duration_days": self.estimated_duration_days,
            "actual_duration_days": self.actual_duration_days,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "xp_total": self.xp_total,
            "xp_earned": self.xp_earned,
            "position": self.position,
            "theme": self.theme,
            "color_scheme": self.color_scheme,
            "unlock_requirements": self.unlock_requirements
        }


@dataclass
class CurriculumPlan:
    """
    Müfredat Planı - AI tarafından oluşturulan tam öğrenme yolu
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: LearningGoal = field(default_factory=LearningGoal)
    
    # Plan detayları
    title: str = ""
    description: str = ""
    subject: str = ""                              # Frontend için gerekli
    target_outcome: str = ""                       # Frontend için gerekli
    
    # Stages
    stages: List[Stage] = field(default_factory=list)
    current_stage_id: Optional[str] = None
    
    # Özet istatistikler
    total_packages: int = 0
    total_exams: int = 0
    total_exercises: int = 0
    estimated_total_hours: float = 0.0
    estimated_completion_days: int = 0
    
    # İlerleme
    overall_progress: float = 0.0
    stages_completed: int = 0
    total_xp_earned: int = 0
    total_xp_possible: int = 0
    
    # Sertifikasyon
    certificate_id: Optional[str] = None
    certificate_eligible: bool = False
    
    # AI Planning metadata
    planning_metadata: Dict[str, Any] = field(default_factory=dict)
    agent_reasoning: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal.to_dict(),
            "title": self.title,
            "description": self.description,
            "subject": self.subject or self.goal.subject,
            "target_outcome": self.target_outcome or self.goal.target_outcome,
            "stages": [s.to_dict() for s in self.stages],
            "current_stage_id": self.current_stage_id,
            "total_stages": len(self.stages),
            "total_packages": self.total_packages,
            "total_exams": self.total_exams,
            "total_exercises": self.total_exercises,
            "estimated_total_hours": self.estimated_total_hours,
            "estimated_completion_days": self.estimated_completion_days,
            "overall_progress": self.overall_progress,
            "stages_completed": self.stages_completed,
            "total_xp_earned": self.total_xp_earned,
            "total_xp_possible": self.total_xp_possible,
            "certificate_id": self.certificate_id,
            "certificate_eligible": self.certificate_eligible,
            "planning_metadata": self.planning_metadata,
            "agent_reasoning": self.agent_reasoning,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class Certificate:
    """Tamamlama Sertifikası"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    journey_id: str = ""
    
    # Sertifika bilgileri
    title: str = ""
    description: str = ""
    subject: str = ""
    
    # Başarı detayları
    completion_date: str = field(default_factory=lambda: datetime.now().isoformat())
    total_hours_studied: float = 0.0
    total_xp_earned: int = 0
    average_score: float = 0.0
    stages_completed: int = 0
    packages_completed: int = 0
    exams_passed: int = 0
    
    # Beceri seviyeleri
    skills_acquired: Dict[str, str] = field(default_factory=dict)  # skill: level
    
    # Sertifika kimliği
    verification_code: str = field(default_factory=lambda: hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16].upper())
    
    # Görsel
    template: str = "default"
    badge_url: Optional[str] = None
    
    # Paylaşım
    is_public: bool = False
    share_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "journey_id": self.journey_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "completion_date": self.completion_date,
            "total_hours_studied": self.total_hours_studied,
            "total_xp_earned": self.total_xp_earned,
            "average_score": self.average_score,
            "stages_completed": self.stages_completed,
            "packages_completed": self.packages_completed,
            "exams_passed": self.exams_passed,
            "skills_acquired": self.skills_acquired,
            "verification_code": self.verification_code,
            "template": self.template,
            "badge_url": self.badge_url,
            "is_public": self.is_public,
            "share_url": self.share_url
        }


@dataclass
class UserProgress:
    """Kullanıcı ilerleme takibi"""
    user_id: str = ""
    journey_id: str = ""
    
    # Mevcut konum
    current_stage_id: str = ""
    current_package_id: str = ""
    current_content_id: str = ""
    
    # İlerleme - Sayısal
    completed_packages: int = 0                    # Frontend uyumlu
    completed_stages: int = 0                      # Frontend uyumlu
    completed_exams: int = 0                       # Frontend uyumlu
    
    # İlerleme - Liste
    completed_content_ids: List[str] = field(default_factory=list)
    completed_exercise_ids: List[str] = field(default_factory=list)
    completed_exam_ids: List[str] = field(default_factory=list)
    completed_package_ids: List[str] = field(default_factory=list)
    completed_stage_ids: List[str] = field(default_factory=list)
    
    # Sınav sonuçları
    exam_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # exam_id: {score, attempts, ...}
    
    # XP ve seviye - Frontend uyumlu
    xp_earned: int = 0                             # Frontend uyumlu
    total_xp: int = 0
    level: int = 1
    xp_to_next_level: int = 100
    
    # Streak - Frontend uyumlu
    streak_days: int = 0                           # Frontend uyumlu
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: Optional[str] = None
    
    # Zaman
    total_time_spent: int = 0                      # seconds - Frontend uyumlu
    total_time_spent_minutes: int = 0
    session_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # İstatistikler
    average_score: float = 0.0
    total_exams_taken: int = 0
    total_exams_passed: int = 0
    
    # Level hesaplama
    XP_PER_LEVEL = [
        0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200,  # Levels 1-10
        4000, 5000, 6200, 7600, 9200, 11000, 13000, 15500, 18500, 22000,  # Levels 11-20
        26000, 31000, 37000, 44000, 52000  # Levels 21-25
    ]
    
    def calculate_level(self) -> None:
        """XP'ye göre level hesapla"""
        for lvl, required_xp in enumerate(self.XP_PER_LEVEL):
            if self.xp_earned < required_xp:
                self.level = max(1, lvl)
                self.xp_to_next_level = required_xp - self.xp_earned
                return
        self.level = len(self.XP_PER_LEVEL)
        self.xp_to_next_level = 0
    
    def add_xp(self, amount: int) -> Dict[str, Any]:
        """XP ekle ve level-up kontrolü yap"""
        old_level = self.level
        self.xp_earned += amount
        self.total_xp += amount
        self.calculate_level()
        
        leveled_up = self.level > old_level
        return {
            "xp_added": amount,
            "total_xp": self.xp_earned,
            "level": self.level,
            "leveled_up": leveled_up,
            "xp_to_next": self.xp_to_next_level
        }
    
    def update_streak(self) -> None:
        """Streak güncelle"""
        from datetime import datetime, timedelta
        
        today = datetime.now().date().isoformat()
        
        if self.last_activity_date is None:
            self.current_streak = 1
            self.streak_days = 1
        else:
            try:
                last_date = datetime.fromisoformat(self.last_activity_date).date()
                current_date = datetime.now().date()
                
                diff = (current_date - last_date).days
                
                if diff == 0:
                    # Aynı gün, değişiklik yok
                    pass
                elif diff == 1:
                    # Ardışık gün, streak arttır
                    self.current_streak += 1
                    self.streak_days = self.current_streak
                else:
                    # Streak kırıldı
                    self.current_streak = 1
                    self.streak_days = 1
            except:
                self.current_streak = 1
                self.streak_days = 1
        
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.last_activity_date = today
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "journey_id": self.journey_id,
            "current_stage_id": self.current_stage_id,
            "current_package_id": self.current_package_id,
            "current_content_id": self.current_content_id,
            "completed_content_ids": self.completed_content_ids,
            "completed_exercise_ids": self.completed_exercise_ids,
            "completed_exam_ids": self.completed_exam_ids,
            "completed_package_ids": self.completed_package_ids,
            "completed_stage_ids": self.completed_stage_ids,
            "exam_results": self.exam_results,
            "xp_earned": self.xp_earned,
            "total_xp": self.total_xp,
            "level": self.level,
            "xp_to_next_level": self.xp_to_next_level,
            "current_streak": self.current_streak,
            "streak_days": self.streak_days,
            "longest_streak": self.longest_streak,
            "last_activity_date": self.last_activity_date,
            "total_time_spent": self.total_time_spent,
            "total_time_spent_minutes": self.total_time_spent_minutes,
            "session_times": self.session_times,
            "average_score": self.average_score,
            "total_exams_taken": self.total_exams_taken,
            "total_exams_passed": self.total_exams_passed
        }
