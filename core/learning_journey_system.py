"""
🎮 Learning Journey System - Candy Crush Style Stage Map
2026 Öğrenci Optimizasyonu için Gamified Öğrenme Yolculuğu

Bu sistem:
- Konuları Stage'lere, Stage'leri Paketlere ayırır
- Her stage için içerik oluşturur (RAG + Web + LLM)
- Candy Crush tarzı görsel harita deneyimi sunar
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import random


# ==================== ENUMS ====================

class StageStatus(str, Enum):
    LOCKED = "locked"           # Kilitli - önceki stage tamamlanmadı
    AVAILABLE = "available"     # Açık - oynanabilir
    IN_PROGRESS = "in_progress" # Devam ediyor
    COMPLETED = "completed"     # Tamamlandı
    MASTERED = "mastered"       # Ustalaşıldı (3 yıldız)


class ContentType(str, Enum):
    LESSON = "lesson"           # Konu anlatımı
    FORMULA = "formula"         # Formül notları
    VIDEO = "video"             # Video içerik
    PRACTICE = "practice"       # Alıştırma
    QUIZ = "quiz"               # Mini sınav
    CHALLENGE = "challenge"     # Bonus challenge


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"       # Temel
    INTERMEDIATE = "intermediate" # Orta
    ADVANCED = "advanced"       # İleri
    EXPERT = "expert"           # Uzman


class PackageTheme(str, Enum):
    FOREST = "forest"           # Orman teması
    OCEAN = "ocean"             # Okyanus teması
    SPACE = "space"             # Uzay teması
    CANDY = "candy"             # Şeker teması
    DESERT = "desert"           # Çöl teması
    ARCTIC = "arctic"           # Kutup teması
    VOLCANO = "volcano"         # Volkan teması
    CRYSTAL = "crystal"         # Kristal teması


# ==================== DATA CLASSES ====================

@dataclass
class StageContent:
    """Stage içindeki tek bir içerik öğesi"""
    id: str
    type: ContentType
    title: str
    description: str
    content: Dict[str, Any]  # Tip'e göre farklı yapı
    duration_minutes: int
    xp_reward: int
    is_completed: bool = False
    completion_date: Optional[str] = None
    source: str = "llm"  # llm, rag, web
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, ContentType) else self.type,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "duration_minutes": self.duration_minutes,
            "xp_reward": self.xp_reward,
            "is_completed": self.is_completed,
            "completion_date": self.completion_date,
            "source": self.source
        }


@dataclass
class Stage:
    """Tek bir stage (seviye)"""
    id: str
    number: int
    title: str
    topic: str
    subtopics: List[str]
    difficulty: DifficultyLevel
    contents: List[StageContent]
    status: StageStatus = StageStatus.LOCKED
    stars: int = 0  # 0-3 arası
    xp_total: int = 0
    xp_earned: int = 0
    attempts: int = 0
    best_score: float = 0.0
    unlock_requirements: List[str] = field(default_factory=list)
    position: Dict[str, float] = field(default_factory=dict)  # x, y koordinatları
    special_reward: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "topic": self.topic,
            "subtopics": self.subtopics,
            "difficulty": self.difficulty.value if isinstance(self.difficulty, DifficultyLevel) else self.difficulty,
            "contents": [c.to_dict() for c in self.contents],
            "status": self.status.value if isinstance(self.status, StageStatus) else self.status,
            "stars": self.stars,
            "xp_total": self.xp_total,
            "xp_earned": self.xp_earned,
            "attempts": self.attempts,
            "best_score": self.best_score,
            "unlock_requirements": self.unlock_requirements,
            "position": self.position,
            "special_reward": self.special_reward
        }


@dataclass
class Package:
    """Stage'lerin gruplandığı paket (bölge)"""
    id: str
    number: int
    name: str
    description: str
    theme: PackageTheme
    subject: str  # Matematik, Fizik, vb.
    stages: List[Stage]
    is_unlocked: bool = False
    completion_percentage: float = 0.0
    total_xp: int = 0
    earned_xp: int = 0
    boss_stage_id: Optional[str] = None  # Her paketin sonunda boss stage
    unlock_date: Optional[str] = None
    background_image: str = ""
    color_scheme: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "number": self.number,
            "name": self.name,
            "description": self.description,
            "theme": self.theme.value if isinstance(self.theme, PackageTheme) else self.theme,
            "subject": self.subject,
            "stages": [s.to_dict() for s in self.stages],
            "is_unlocked": self.is_unlocked,
            "completion_percentage": self.completion_percentage,
            "total_xp": self.total_xp,
            "earned_xp": self.earned_xp,
            "boss_stage_id": self.boss_stage_id,
            "unlock_date": self.unlock_date,
            "background_image": self.background_image,
            "color_scheme": self.color_scheme
        }


@dataclass
class LearningPath:
    """Kullanıcının öğrenme yolculuğu"""
    user_id: str
    subject: str
    goal: str
    packages: List[Package]
    current_package_id: str
    current_stage_id: str
    total_xp: int = 0
    total_stars: int = 0
    streak_days: int = 0
    last_activity: Optional[str] = None
    estimated_completion_days: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "subject": self.subject,
            "goal": self.goal,
            "packages": [p.to_dict() for p in self.packages],
            "current_package_id": self.current_package_id,
            "current_stage_id": self.current_stage_id,
            "total_xp": self.total_xp,
            "total_stars": self.total_stars,
            "streak_days": self.streak_days,
            "last_activity": self.last_activity,
            "estimated_completion_days": self.estimated_completion_days,
            "created_at": self.created_at
        }


# ==================== CURRICULUM TEMPLATES ====================

MATH_CURRICULUM = {
    "Temel Matematik": {
        "topics": ["Sayılar", "Dört İşlem", "Kesirler", "Ondalık Sayılar", "Yüzdeler"],
        "difficulty": DifficultyLevel.BEGINNER,
        "theme": PackageTheme.CANDY,
        "estimated_hours": 15
    },
    "Cebir Temelleri": {
        "topics": ["Değişkenler", "Denklemler", "Eşitsizlikler", "Polinomlar", "Özdeşlikler"],
        "difficulty": DifficultyLevel.BEGINNER,
        "theme": PackageTheme.FOREST,
        "estimated_hours": 20
    },
    "Fonksiyonlar": {
        "topics": ["Fonksiyon Kavramı", "Doğrusal Fonksiyonlar", "İkinci Derece Fonksiyonlar", 
                   "Üstel Fonksiyonlar", "Logaritmik Fonksiyonlar", "Trigonometrik Fonksiyonlar"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "theme": PackageTheme.OCEAN,
        "estimated_hours": 30
    },
    "Geometri": {
        "topics": ["Temel Geometri", "Üçgenler", "Dörtgenler", "Çember", "Katı Cisimler", "Analitik Geometri"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "theme": PackageTheme.CRYSTAL,
        "estimated_hours": 35
    },
    "Türev": {
        "topics": ["Limit", "Süreklilik", "Türev Tanımı", "Türev Kuralları", "Türev Uygulamaları"],
        "difficulty": DifficultyLevel.ADVANCED,
        "theme": PackageTheme.SPACE,
        "estimated_hours": 25
    },
    "İntegral": {
        "topics": ["Belirsiz İntegral", "Belirli İntegral", "İntegral Yöntemleri", "Alan Hesabı", "Hacim Hesabı"],
        "difficulty": DifficultyLevel.ADVANCED,
        "theme": PackageTheme.VOLCANO,
        "estimated_hours": 25
    },
    "Olasılık ve İstatistik": {
        "topics": ["Permütasyon", "Kombinasyon", "Olasılık", "İstatistik", "Dağılımlar"],
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "theme": PackageTheme.ARCTIC,
        "estimated_hours": 20
    }
}

THEME_COLORS = {
    PackageTheme.CANDY: {
        "primary": "#FF6B9D",
        "secondary": "#C44569",
        "background": "#FFF0F5",
        "accent": "#FFD93D"
    },
    PackageTheme.FOREST: {
        "primary": "#2D5016",
        "secondary": "#4A7C23",
        "background": "#E8F5E9",
        "accent": "#8BC34A"
    },
    PackageTheme.OCEAN: {
        "primary": "#0077B6",
        "secondary": "#00B4D8",
        "background": "#E0F7FA",
        "accent": "#90E0EF"
    },
    PackageTheme.SPACE: {
        "primary": "#1A1A2E",
        "secondary": "#4A00E0",
        "background": "#0F0F1A",
        "accent": "#8E2DE2"
    },
    PackageTheme.DESERT: {
        "primary": "#D4A574",
        "secondary": "#C19A6B",
        "background": "#FDF5E6",
        "accent": "#FFB347"
    },
    PackageTheme.ARCTIC: {
        "primary": "#A8D8EA",
        "secondary": "#87CEEB",
        "background": "#F0FFFF",
        "accent": "#00CED1"
    },
    PackageTheme.VOLCANO: {
        "primary": "#FF4500",
        "secondary": "#DC143C",
        "background": "#1A0000",
        "accent": "#FFD700"
    },
    PackageTheme.CRYSTAL: {
        "primary": "#9B59B6",
        "secondary": "#8E44AD",
        "background": "#F5E6FF",
        "accent": "#E74C3C"
    }
}


# ==================== CONTENT GENERATOR ====================

class AIContentGenerator:
    """
    AI destekli içerik oluşturucu.
    RAG, Web arama ve LLM bilgisini kullanır.
    """
    
    def __init__(self, rag_service=None, llm_service=None):
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.content_cache: Dict[str, Any] = {}
    
    async def generate_lesson_content(
        self, 
        topic: str, 
        subtopic: str,
        difficulty: DifficultyLevel,
        target_duration: int = 15
    ) -> StageContent:
        """Konu anlatımı içeriği oluştur"""
        cache_key = f"lesson_{topic}_{subtopic}_{difficulty.value}"
        
        if cache_key in self.content_cache:
            return self.content_cache[cache_key]
        
        # İçerik yapısı
        content = {
            "sections": [
                {
                    "title": f"{subtopic} - Giriş",
                    "type": "introduction",
                    "text": f"{subtopic} konusuna hoş geldiniz. Bu derste temel kavramları öğreneceksiniz.",
                    "examples": []
                },
                {
                    "title": "Temel Kavramlar",
                    "type": "concepts",
                    "text": f"{subtopic} ile ilgili temel kavramlar ve tanımlar.",
                    "key_points": [
                        f"{subtopic} tanımı",
                        "Temel özellikler",
                        "Uygulama alanları"
                    ]
                },
                {
                    "title": "Örnekler",
                    "type": "examples",
                    "problems": [
                        {
                            "question": f"{subtopic} ile ilgili örnek soru 1",
                            "solution": "Adım adım çözüm",
                            "answer": "Cevap"
                        }
                    ]
                },
                {
                    "title": "Özet",
                    "type": "summary",
                    "key_takeaways": [
                        f"{subtopic} temel prensipleri",
                        "Önemli formüller",
                        "Dikkat edilmesi gerekenler"
                    ]
                }
            ],
            "interactive_elements": [
                {"type": "flashcard", "count": 5},
                {"type": "mini_quiz", "questions": 3}
            ],
            "resources": {
                "videos": [],
                "articles": [],
                "practice_sets": []
            }
        }
        
        stage_content = StageContent(
            id=f"lesson_{hashlib.md5(cache_key.encode()).hexdigest()[:8]}",
            type=ContentType.LESSON,
            title=f"{subtopic} Dersi",
            description=f"{topic} kapsamında {subtopic} konusunun detaylı anlatımı",
            content=content,
            duration_minutes=target_duration,
            xp_reward=target_duration * 10,
            source="llm"
        )
        
        self.content_cache[cache_key] = stage_content
        return stage_content
    
    async def generate_formula_content(
        self,
        topic: str,
        subtopic: str
    ) -> StageContent:
        """Formül notları oluştur"""
        content = {
            "formulas": [
                {
                    "name": f"{subtopic} Temel Formülü",
                    "latex": "f(x) = ax^2 + bx + c",
                    "description": "Temel formül açıklaması",
                    "variables": {
                        "a": "Katsayı",
                        "b": "Katsayı",
                        "c": "Sabit terim"
                    },
                    "examples": ["Örnek uygulama"]
                }
            ],
            "cheat_sheet": {
                "quick_reference": [],
                "common_mistakes": [],
                "tips": []
            },
            "related_formulas": []
        }
        
        return StageContent(
            id=f"formula_{hashlib.md5(f'{topic}_{subtopic}'.encode()).hexdigest()[:8]}",
            type=ContentType.FORMULA,
            title=f"{subtopic} Formülleri",
            description=f"{subtopic} için tüm formüller ve notlar",
            content=content,
            duration_minutes=5,
            xp_reward=30,
            source="llm"
        )
    
    async def generate_video_content(
        self,
        topic: str,
        subtopic: str
    ) -> StageContent:
        """Video içerik referansları oluştur"""
        content = {
            "videos": [
                {
                    "title": f"{subtopic} Konu Anlatımı",
                    "source": "youtube",
                    "url": "",  # RAG veya web'den bulunacak
                    "duration": "15:00",
                    "thumbnail": "",
                    "chapters": [
                        {"time": "0:00", "title": "Giriş"},
                        {"time": "2:30", "title": "Temel Kavramlar"},
                        {"time": "8:00", "title": "Örnekler"},
                        {"time": "12:00", "title": "Özet"}
                    ]
                }
            ],
            "supplementary": [],
            "notes": []
        }
        
        return StageContent(
            id=f"video_{hashlib.md5(f'{topic}_{subtopic}'.encode()).hexdigest()[:8]}",
            type=ContentType.VIDEO,
            title=f"{subtopic} Video Dersi",
            description=f"{subtopic} konusunu anlatan video içerikler",
            content=content,
            duration_minutes=15,
            xp_reward=50,
            source="web"
        )
    
    async def generate_practice_content(
        self,
        topic: str,
        subtopic: str,
        difficulty: DifficultyLevel,
        question_count: int = 10
    ) -> StageContent:
        """Alıştırma soruları oluştur"""
        questions = []
        for i in range(question_count):
            questions.append({
                "id": f"q_{i+1}",
                "question": f"{subtopic} ile ilgili soru {i+1}",
                "type": random.choice(["multiple_choice", "fill_blank", "true_false"]),
                "options": ["A", "B", "C", "D"] if i % 2 == 0 else None,
                "correct_answer": "A",
                "explanation": "Çözüm açıklaması",
                "difficulty": difficulty.value,
                "points": 10 + (i * 5)
            })
        
        content = {
            "questions": questions,
            "time_limit": question_count * 2,  # dakika
            "passing_score": 70,
            "hints_available": 3,
            "retry_allowed": True
        }
        
        return StageContent(
            id=f"practice_{hashlib.md5(f'{topic}_{subtopic}'.encode()).hexdigest()[:8]}",
            type=ContentType.PRACTICE,
            title=f"{subtopic} Alıştırmaları",
            description=f"{question_count} soruluk alıştırma seti",
            content=content,
            duration_minutes=question_count * 2,
            xp_reward=question_count * 15,
            source="llm"
        )
    
    async def generate_quiz_content(
        self,
        topic: str,
        subtopic: str,
        difficulty: DifficultyLevel
    ) -> StageContent:
        """Mini sınav oluştur"""
        content = {
            "questions": [
                {
                    "id": f"quiz_q_{i}",
                    "question": f"Sınav sorusu {i}",
                    "type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": random.choice(["A", "B", "C", "D"]),
                    "points": 20
                }
                for i in range(1, 6)
            ],
            "time_limit": 10,
            "passing_score": 60,
            "stars_thresholds": {
                "1_star": 60,
                "2_stars": 80,
                "3_stars": 95
            }
        }
        
        return StageContent(
            id=f"quiz_{hashlib.md5(f'{topic}_{subtopic}'.encode()).hexdigest()[:8]}",
            type=ContentType.QUIZ,
            title=f"{subtopic} Mini Sınavı",
            description="Öğrendiklerini test et!",
            content=content,
            duration_minutes=10,
            xp_reward=100,
            source="llm"
        )


# ==================== STAGE MAP GENERATOR ====================

class StageMapGenerator:
    """
    Candy Crush tarzı stage haritası oluşturucu.
    Konuları stage'lere, stage'leri paketlere organize eder.
    """
    
    def __init__(self, content_generator: AIContentGenerator = None):
        self.content_generator = content_generator or AIContentGenerator()
        self.user_paths: Dict[str, LearningPath] = {}
    
    def _generate_stage_position(self, stage_number: int, total_stages: int) -> Dict[str, float]:
        """Candy Crush tarzı zigzag pozisyon hesapla"""
        # Her 5 stage'de bir yön değişimi
        row = stage_number // 5
        col_in_row = stage_number % 5
        
        # Zigzag pattern
        if row % 2 == 0:
            x = 20 + (col_in_row * 15)  # Soldan sağa
        else:
            x = 80 - (col_in_row * 15)  # Sağdan sola
        
        y = 90 - (row * 18)  # Aşağıdan yukarı
        
        # Küçük random offset
        x += random.uniform(-3, 3)
        y += random.uniform(-2, 2)
        
        return {"x": max(10, min(90, x)), "y": max(10, min(90, y))}
    
    async def generate_stage_for_topic(
        self,
        topic: str,
        subtopic: str,
        stage_number: int,
        difficulty: DifficultyLevel,
        total_stages: int
    ) -> Stage:
        """Bir konu için stage oluştur"""
        
        # İçerikleri oluştur
        contents = []
        
        # 1. Konu anlatımı
        lesson = await self.content_generator.generate_lesson_content(
            topic, subtopic, difficulty
        )
        contents.append(lesson)
        
        # 2. Formül notları
        formula = await self.content_generator.generate_formula_content(topic, subtopic)
        contents.append(formula)
        
        # 3. Video içerik
        video = await self.content_generator.generate_video_content(topic, subtopic)
        contents.append(video)
        
        # 4. Alıştırma
        practice = await self.content_generator.generate_practice_content(
            topic, subtopic, difficulty
        )
        contents.append(practice)
        
        # 5. Mini sınav
        quiz = await self.content_generator.generate_quiz_content(
            topic, subtopic, difficulty
        )
        contents.append(quiz)
        
        # Toplam XP hesapla
        total_xp = sum(c.xp_reward for c in contents)
        
        # Stage oluştur
        stage = Stage(
            id=f"stage_{hashlib.md5(f'{topic}_{subtopic}_{stage_number}'.encode()).hexdigest()[:8]}",
            number=stage_number,
            title=subtopic,
            topic=topic,
            subtopics=[subtopic],
            difficulty=difficulty,
            contents=contents,
            status=StageStatus.LOCKED if stage_number > 1 else StageStatus.AVAILABLE,
            xp_total=total_xp,
            position=self._generate_stage_position(stage_number - 1, total_stages),
            unlock_requirements=[f"stage_{stage_number - 1}"] if stage_number > 1 else [],
            special_reward={"type": "badge", "name": f"{subtopic} Ustası"} if stage_number % 5 == 0 else None
        )
        
        return stage
    
    async def generate_package(
        self,
        package_number: int,
        package_name: str,
        package_info: Dict[str, Any],
        subject: str
    ) -> Package:
        """Bir paket (bölge) oluştur"""
        
        topics = package_info["topics"]
        difficulty = package_info["difficulty"]
        theme = package_info["theme"]
        
        stages = []
        stage_number = 1
        
        for topic in topics:
            stage = await self.generate_stage_for_topic(
                package_name,
                topic,
                stage_number,
                difficulty,
                len(topics)
            )
            stages.append(stage)
            stage_number += 1
        
        # Boss stage ekle (her paketin sonunda)
        boss_stage = Stage(
            id=f"boss_{hashlib.md5(f'{package_name}_boss'.encode()).hexdigest()[:8]}",
            number=stage_number,
            title=f"{package_name} Final Sınavı",
            topic=package_name,
            subtopics=topics,
            difficulty=DifficultyLevel.ADVANCED,
            contents=[],  # Boss içeriği ayrı oluşturulacak
            status=StageStatus.LOCKED,
            xp_total=500,
            position=self._generate_stage_position(stage_number - 1, len(topics) + 1),
            unlock_requirements=[s.id for s in stages],
            special_reward={
                "type": "package_completion",
                "name": f"{package_name} Tamamlandı!",
                "xp_bonus": 1000
            }
        )
        stages.append(boss_stage)
        
        # Paket toplam XP
        total_xp = sum(s.xp_total for s in stages)
        
        package = Package(
            id=f"pkg_{hashlib.md5(package_name.encode()).hexdigest()[:8]}",
            number=package_number,
            name=package_name,
            description=f"{subject} - {package_name} konularını içerir",
            theme=theme,
            subject=subject,
            stages=stages,
            is_unlocked=package_number == 1,  # İlk paket açık
            total_xp=total_xp,
            boss_stage_id=boss_stage.id,
            color_scheme=THEME_COLORS.get(theme, THEME_COLORS[PackageTheme.CANDY])
        )
        
        return package
    
    async def generate_learning_path(
        self,
        user_id: str,
        subject: str,
        goal: str,
        curriculum: Dict[str, Dict[str, Any]] = None
    ) -> LearningPath:
        """Kullanıcı için tam öğrenme yolu oluştur"""
        
        if curriculum is None:
            curriculum = MATH_CURRICULUM
        
        packages = []
        package_number = 1
        
        for package_name, package_info in curriculum.items():
            package = await self.generate_package(
                package_number,
                package_name,
                package_info,
                subject
            )
            packages.append(package)
            package_number += 1
        
        # Tahmini tamamlama süresi
        total_hours = sum(
            curriculum[p]["estimated_hours"] 
            for p in curriculum
        )
        estimated_days = total_hours // 2  # Günde 2 saat çalışma varsayımı
        
        learning_path = LearningPath(
            user_id=user_id,
            subject=subject,
            goal=goal,
            packages=packages,
            current_package_id=packages[0].id if packages else "",
            current_stage_id=packages[0].stages[0].id if packages and packages[0].stages else "",
            estimated_completion_days=estimated_days
        )
        
        self.user_paths[user_id] = learning_path
        return learning_path
    
    def get_user_path(self, user_id: str) -> Optional[LearningPath]:
        """Kullanıcının öğrenme yolunu getir"""
        return self.user_paths.get(user_id)
    
    def update_stage_progress(
        self,
        user_id: str,
        stage_id: str,
        content_id: str,
        score: float,
        completed: bool
    ) -> Dict[str, Any]:
        """Stage ilerleme güncelle"""
        
        path = self.user_paths.get(user_id)
        if not path:
            return {"error": "Learning path not found"}
        
        for package in path.packages:
            for stage in package.stages:
                if stage.id == stage_id:
                    # İçerik tamamlama
                    for content in stage.contents:
                        if content.id == content_id:
                            content.is_completed = completed
                            content.completion_date = datetime.now().isoformat()
                            
                            if completed:
                                stage.xp_earned += content.xp_reward
                                path.total_xp += content.xp_reward
                    
                    # Stage durumu güncelle
                    completed_contents = sum(1 for c in stage.contents if c.is_completed)
                    total_contents = len(stage.contents)
                    
                    if completed_contents == total_contents:
                        stage.status = StageStatus.COMPLETED
                        stage.stars = self._calculate_stars(score)
                        path.total_stars += stage.stars
                        
                        # Sonraki stage'i aç
                        self._unlock_next_stage(path, package, stage)
                    elif completed_contents > 0:
                        stage.status = StageStatus.IN_PROGRESS
                    
                    stage.attempts += 1
                    if score > stage.best_score:
                        stage.best_score = score
                    
                    # Paket ilerleme güncelle
                    completed_stages = sum(1 for s in package.stages if s.status == StageStatus.COMPLETED)
                    package.completion_percentage = (completed_stages / len(package.stages)) * 100
                    package.earned_xp = sum(s.xp_earned for s in package.stages)
                    
                    return {
                        "success": True,
                        "stage_status": stage.status.value,
                        "stars": stage.stars,
                        "xp_earned": stage.xp_earned,
                        "package_progress": package.completion_percentage
                    }
        
        return {"error": "Stage not found"}
    
    def _calculate_stars(self, score: float) -> int:
        """Skora göre yıldız hesapla"""
        if score >= 95:
            return 3
        elif score >= 80:
            return 2
        elif score >= 60:
            return 1
        return 0
    
    def _unlock_next_stage(self, path: LearningPath, package: Package, completed_stage: Stage):
        """Sonraki stage'i aç"""
        stage_index = package.stages.index(completed_stage)
        
        if stage_index + 1 < len(package.stages):
            next_stage = package.stages[stage_index + 1]
            next_stage.status = StageStatus.AVAILABLE
            path.current_stage_id = next_stage.id
        else:
            # Paket tamamlandı, sonraki paketi aç
            package_index = path.packages.index(package)
            if package_index + 1 < len(path.packages):
                next_package = path.packages[package_index + 1]
                next_package.is_unlocked = True
                next_package.unlock_date = datetime.now().isoformat()
                if next_package.stages:
                    next_package.stages[0].status = StageStatus.AVAILABLE
                    path.current_package_id = next_package.id
                    path.current_stage_id = next_package.stages[0].id


# ==================== SINGLETON INSTANCES ====================

_content_generator: Optional[AIContentGenerator] = None
_stage_map_generator: Optional[StageMapGenerator] = None


def get_content_generator() -> AIContentGenerator:
    global _content_generator
    if _content_generator is None:
        _content_generator = AIContentGenerator()
    return _content_generator


def get_stage_map_generator() -> StageMapGenerator:
    global _stage_map_generator
    if _stage_map_generator is None:
        _stage_map_generator = StageMapGenerator(get_content_generator())
    return _stage_map_generator


# ==================== QUICK TEST ====================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        generator = get_stage_map_generator()
        
        path = await generator.generate_learning_path(
            user_id="test_user",
            subject="Matematik",
            goal="AYT Matematik sınavında başarılı olmak"
        )
        
        print(f"Created learning path with {len(path.packages)} packages")
        for pkg in path.packages:
            print(f"  - {pkg.name}: {len(pkg.stages)} stages, {pkg.total_xp} XP")
    
    asyncio.run(test())
