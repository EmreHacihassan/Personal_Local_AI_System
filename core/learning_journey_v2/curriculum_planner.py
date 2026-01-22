"""
🧠 Curriculum Planner Agent
Multi-Agent Orchestration ile Müfredat Planlama

Bu agent:
1. Kullanıcının hedefini analiz eder
2. Konuları stage'lere ayırır
3. Her stage için paketler oluşturur
4. Sınav ve egzersiz planı yapar
5. Zaman çizelgesi oluşturur
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from .models import (
    LearningGoal, CurriculumPlan, Stage, Package, PackageType,
    Exam, ExamType, Exercise, ExerciseType, ContentBlock, ContentType,
    DifficultyLevel, StageStatus, PackageStatus, ExamQuestion
)


# ==================== CURRICULUM TEMPLATES ====================

MATH_AYT_CURRICULUM = {
    "Temel Matematik": {
        "topics": ["Sayılar ve İşlemler", "Bölünebilme", "EBOB-EKOK", "Rasyonel Sayılar", "Üslü Sayılar", "Köklü Sayılar"],
        "difficulty": "beginner",
        "estimated_hours": 20,
        "order": 1
    },
    "Cebir": {
        "topics": ["Cebirsel İfadeler", "Özdeşlikler", "Çarpanlara Ayırma", "1. Derece Denklemler", "2. Derece Denklemler", "Eşitsizlikler", "Mutlak Değer"],
        "difficulty": "beginner",
        "estimated_hours": 25,
        "order": 2
    },
    "Fonksiyonlar": {
        "topics": ["Fonksiyon Kavramı", "Fonksiyon Türleri", "Bileşke Fonksiyon", "Ters Fonksiyon", "Polinom", "İkinci Derece Fonksiyonlar"],
        "difficulty": "intermediate",
        "estimated_hours": 30,
        "order": 3
    },
    "Üstel ve Logaritmik Fonksiyonlar": {
        "topics": ["Üstel Fonksiyonlar", "Logaritma Tanımı", "Logaritma Özellikleri", "Logaritmik Denklemler"],
        "difficulty": "intermediate",
        "estimated_hours": 20,
        "order": 4
    },
    "Trigonometri": {
        "topics": ["Trigonometrik Oranlar", "Trigonometrik Denklemler", "Ters Trigonometrik Fonksiyonlar", "Toplam-Fark Formülleri"],
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "order": 5
    },
    "Diziler": {
        "topics": ["Dizi Kavramı", "Aritmetik Dizi", "Geometrik Dizi", "Dizi Uygulamaları"],
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "order": 6
    },
    "Limit ve Süreklilik": {
        "topics": ["Limit Kavramı", "Limit Hesaplama", "Belirsizlik Durumları", "Süreklilik"],
        "difficulty": "advanced",
        "estimated_hours": 20,
        "order": 7
    },
    "Türev": {
        "topics": ["Türev Tanımı", "Türev Kuralları", "Bileşke Türev", "Örtük Türev", "Türev Uygulamaları", "Maksimum-Minimum"],
        "difficulty": "advanced",
        "estimated_hours": 35,
        "order": 8
    },
    "İntegral": {
        "topics": ["Belirsiz İntegral", "Temel İntegral Formülleri", "Değişken Dönüşümü", "Kısmi İntegral", "Belirli İntegral", "Alan Hesabı"],
        "difficulty": "advanced",
        "estimated_hours": 35,
        "order": 9
    },
    "Analitik Geometri": {
        "topics": ["Noktanın Analitiği", "Doğrunun Analitiği", "Çemberin Analitiği", "Konikler"],
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "order": 10
    },
    "Geometri": {
        "topics": ["Üçgenler", "Dörtgenler", "Çember", "Çokgenler", "Katı Cisimler"],
        "difficulty": "intermediate",
        "estimated_hours": 40,
        "order": 11
    },
    "Olasılık ve İstatistik": {
        "topics": ["Permütasyon", "Kombinasyon", "Binom Açılımı", "Olasılık", "İstatistik", "Veri Analizi"],
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "order": 12
    }
}

THEME_COLORS = [
    {"name": "Candy", "primary": "#FF6B9D", "secondary": "#C44569", "accent": "#FFD93D"},
    {"name": "Forest", "primary": "#2D5016", "secondary": "#4A7C23", "accent": "#8BC34A"},
    {"name": "Ocean", "primary": "#0077B6", "secondary": "#00B4D8", "accent": "#90E0EF"},
    {"name": "Space", "primary": "#4A00E0", "secondary": "#8E2DE2", "accent": "#00D9FF"},
    {"name": "Desert", "primary": "#D4A574", "secondary": "#C19A6B", "accent": "#FFB347"},
    {"name": "Arctic", "primary": "#A8D8EA", "secondary": "#87CEEB", "accent": "#00CED1"},
    {"name": "Volcano", "primary": "#FF4500", "secondary": "#DC143C", "accent": "#FFD700"},
    {"name": "Crystal", "primary": "#9B59B6", "secondary": "#8E44AD", "accent": "#E74C3C"},
    {"name": "Jungle", "primary": "#228B22", "secondary": "#32CD32", "accent": "#ADFF2F"},
    {"name": "Sunset", "primary": "#FF6347", "secondary": "#FF7F50", "accent": "#FFD700"},
    {"name": "Galaxy", "primary": "#191970", "secondary": "#4B0082", "accent": "#DA70D6"},
    {"name": "Coral", "primary": "#FF7F50", "secondary": "#FA8072", "accent": "#FFA07A"}
]


# ==================== AGENT THOUGHTS ====================

@dataclass
class AgentThought:
    """Agent düşünce süreci kaydı"""
    step: int
    agent_name: str
    action: str
    reasoning: str
    output: Any
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "agent_name": self.agent_name,
            "action": self.action,
            "reasoning": self.reasoning,
            "output": self.output if not hasattr(self.output, 'to_dict') else self.output.to_dict(),
            "timestamp": self.timestamp
        }


# ==================== CURRICULUM PLANNER AGENT ====================

class CurriculumPlannerAgent:
    """
    Müfredat Planlama Agent'ı
    
    Research 2.0'daki gibi düşünce süreci ile:
    1. Hedef Analizi
    2. Konu Haritalama
    3. Stage Planlama
    4. Paket Oluşturma
    5. Sınav Stratejisi
    6. Zaman Optimizasyonu
    """
    
    def __init__(self, llm_service=None, rag_service=None):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.thoughts: List[AgentThought] = []
        self.step_counter = 0
    
    def _add_thought(self, agent: str, action: str, reasoning: str, output: Any) -> AgentThought:
        """Düşünce adımı ekle"""
        self.step_counter += 1
        thought = AgentThought(
            step=self.step_counter,
            agent_name=agent,
            action=action,
            reasoning=reasoning,
            output=output
        )
        self.thoughts.append(thought)
        return thought
    
    async def plan_curriculum(self, goal: LearningGoal) -> Tuple[CurriculumPlan, List[AgentThought]]:
        """
        Tam müfredat planı oluştur
        
        Returns:
            (CurriculumPlan, List[AgentThought]) - Plan ve düşünce süreci
        """
        self.thoughts = []
        self.step_counter = 0
        
        # 1. Hedef Analizi
        goal_analysis = await self._analyze_goal(goal)
        
        # 2. Müfredat Seçimi
        curriculum = await self._select_curriculum(goal, goal_analysis)
        
        # 3. Konu Haritalama
        topic_map = await self._map_topics(goal, curriculum)
        
        # 4. Stage Planlama
        stages = await self._plan_stages(goal, topic_map, curriculum)
        
        # 5. Paket Oluşturma
        stages_with_packages = await self._create_packages(goal, stages, curriculum)
        
        # 6. Sınav Stratejisi
        stages_with_exams = await self._plan_exams(goal, stages_with_packages)
        
        # 7. Zaman Optimizasyonu
        optimized_plan = await self._optimize_timeline(goal, stages_with_exams)
        
        # 8. Final Plan Oluşturma
        final_plan = await self._finalize_plan(goal, optimized_plan)
        
        return final_plan, self.thoughts
    
    async def _analyze_goal(self, goal: LearningGoal) -> Dict[str, Any]:
        """Hedef analizi yap"""
        
        # Zorluk seviyesi belirleme
        difficulty_score = 0
        if "AYT" in goal.title or "YKS" in goal.title:
            difficulty_score = 70
        elif "TYT" in goal.title:
            difficulty_score = 50
        elif "temel" in goal.title.lower():
            difficulty_score = 30
        else:
            difficulty_score = 50
        
        # Öğrenme stili analizi
        learning_profile = {
            "visual_preference": 0.7 if ContentType.VIDEO in goal.content_preferences else 0.3,
            "reading_preference": 0.7 if ContentType.TEXT in goal.content_preferences else 0.5,
            "practical_preference": 0.8 if ExamType.PRACTICAL in goal.exam_preferences else 0.5,
            "self_paced": goal.daily_hours >= 2
        }
        
        analysis = {
            "difficulty_score": difficulty_score,
            "estimated_complexity": "high" if difficulty_score > 60 else "medium" if difficulty_score > 40 else "low",
            "learning_profile": learning_profile,
            "time_available_hours": goal.daily_hours * 7 * 12,  # 12 haftalık varsayım
            "focus_weight": {topic: 1.5 for topic in goal.focus_areas},
            "weak_area_weight": {topic: 2.0 for topic in goal.weak_areas}
        }
        
        self._add_thought(
            agent="Goal Analyzer",
            action="analyze_learning_goal",
            reasoning=f"Kullanıcının '{goal.title}' hedefi analiz edildi. "
                     f"Zorluk seviyesi: {analysis['estimated_complexity']}, "
                     f"Tahmini toplam çalışma süresi: {analysis['time_available_hours']} saat",
            output=analysis
        )
        
        return analysis
    
    async def _select_curriculum(self, goal: LearningGoal, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Uygun müfredatı seç"""
        
        # Şimdilik matematik müfredatı
        if "matematik" in goal.subject.lower():
            curriculum = MATH_AYT_CURRICULUM
        else:
            curriculum = MATH_AYT_CURRICULUM  # Default
        
        # Kullanıcının dahil etmek istediği/istemediği konuları filtrele
        filtered_curriculum = {}
        for topic_name, topic_data in curriculum.items():
            if goal.topics_to_exclude and topic_name in goal.topics_to_exclude:
                continue
            if goal.topics_to_include and topic_name not in goal.topics_to_include:
                if goal.topics_to_include:  # Eğer liste boş değilse
                    continue
            filtered_curriculum[topic_name] = topic_data
        
        self._add_thought(
            agent="Curriculum Selector",
            action="select_curriculum",
            reasoning=f"'{goal.subject}' için müfredat seçildi. "
                     f"{len(filtered_curriculum)} ana konu kategorisi belirlendi.",
            output={
                "curriculum_type": f"{goal.subject} AYT",
                "total_topics": len(filtered_curriculum),
                "topics": list(filtered_curriculum.keys())
            }
        )
        
        return filtered_curriculum
    
    async def _map_topics(self, goal: LearningGoal, curriculum: Dict[str, Any]) -> Dict[str, Any]:
        """Konuları haritalandır"""
        
        topic_map = {
            "stages": [],
            "total_topics": 0,
            "total_subtopics": 0,
            "estimated_hours": 0
        }
        
        # Her ana konuyu bir stage olarak planla
        sorted_topics = sorted(curriculum.items(), key=lambda x: x[1].get("order", 0))
        
        for topic_name, topic_data in sorted_topics:
            stage_info = {
                "name": topic_name,
                "subtopics": topic_data["topics"],
                "difficulty": topic_data["difficulty"],
                "estimated_hours": topic_data["estimated_hours"]
            }
            topic_map["stages"].append(stage_info)
            topic_map["total_topics"] += 1
            topic_map["total_subtopics"] += len(topic_data["topics"])
            topic_map["estimated_hours"] += topic_data["estimated_hours"]
        
        self._add_thought(
            agent="Topic Mapper",
            action="map_topics_to_stages",
            reasoning=f"Müfredat haritalandırıldı: {topic_map['total_topics']} stage, "
                     f"{topic_map['total_subtopics']} alt konu, "
                     f"toplam {topic_map['estimated_hours']} saat",
            output=topic_map
        )
        
        return topic_map
    
    async def _plan_stages(self, goal: LearningGoal, topic_map: Dict[str, Any], curriculum: Dict[str, Any]) -> List[Stage]:
        """Stage'leri planla"""
        
        stages = []
        theme_index = 0
        
        for idx, stage_info in enumerate(topic_map["stages"]):
            theme = THEME_COLORS[theme_index % len(THEME_COLORS)]
            theme_index += 1
            
            # Pozisyon hesapla (Candy Crush zigzag)
            row = idx // 3
            col = idx % 3
            if row % 2 == 1:
                col = 2 - col
            
            x = 20 + (col * 30)
            y = 85 - (row * 15)
            
            stage = Stage(
                journey_id=goal.id,
                number=idx + 1,
                title=stage_info["name"],
                description=f"{stage_info['name']} konularını kapsayan öğrenme aşaması",
                main_topic=stage_info["name"],
                covered_topics=stage_info["subtopics"],
                status=StageStatus.AVAILABLE if idx == 0 else StageStatus.LOCKED,
                estimated_duration_days=max(3, stage_info["estimated_hours"] // goal.daily_hours),
                position={"x": x, "y": y},
                theme=theme["name"].lower(),
                color_scheme={
                    "primary": theme["primary"],
                    "secondary": theme["secondary"],
                    "accent": theme["accent"]
                },
                unlock_requirements=[stages[-1].id] if stages else []
            )
            
            stages.append(stage)
        
        self._add_thought(
            agent="Stage Planner",
            action="create_stage_structure",
            reasoning=f"{len(stages)} stage oluşturuldu. Her stage farklı bir tema ile tasarlandı. "
                     f"İlk stage açık, diğerleri sırayla açılacak.",
            output={
                "total_stages": len(stages),
                "stage_names": [s.title for s in stages]
            }
        )
        
        return stages
    
    async def _create_packages(self, goal: LearningGoal, stages: List[Stage], curriculum: Dict[str, Any]) -> List[Stage]:
        """Her stage için paketler oluştur"""
        
        for stage in stages:
            packages = []
            subtopics = stage.covered_topics
            package_number = 1
            
            # 1. Giriş Paketi
            intro_package = Package(
                stage_id=stage.id,
                number=package_number,
                title=f"{stage.title} - Giriş",
                description=f"{stage.title} konusuna giriş ve ön bilgiler",
                type=PackageType.INTRO,
                curriculum_section=stage.main_topic,
                topics=[stage.main_topic],
                learning_objectives=[
                    f"{stage.title} konusunun temel kavramlarını öğrenmek",
                    "Önceki konularla bağlantı kurmak",
                    "Öğrenme hedeflerini anlamak"
                ],
                estimated_duration_minutes=30,
                difficulty=DifficultyLevel.BEGINNER,
                xp_reward=50,
                status=PackageStatus.AVAILABLE if stage.status == StageStatus.AVAILABLE else PackageStatus.LOCKED,
                theme_color=stage.color_scheme.get("primary", "#6366F1"),
                icon="🎯"
            )
            packages.append(intro_package)
            stage.intro_package_id = intro_package.id
            package_number += 1
            
            # 2. Her alt konu için öğrenme paketi
            for subtopic in subtopics:
                learning_package = Package(
                    stage_id=stage.id,
                    number=package_number,
                    title=subtopic,
                    description=f"{subtopic} konusunun detaylı öğrenimi",
                    type=PackageType.LEARNING,
                    curriculum_section=f"{stage.main_topic} > {subtopic}",
                    topics=[subtopic],
                    subtopics=[],
                    learning_objectives=[
                        f"{subtopic} kavramını anlamak",
                        f"{subtopic} ile ilgili problem çözmek",
                        f"{subtopic} konusunu uygulamak"
                    ],
                    estimated_duration_minutes=45,
                    difficulty=self._get_difficulty(curriculum.get(stage.main_topic, {}).get("difficulty", "intermediate")),
                    xp_reward=100,
                    status=PackageStatus.LOCKED,
                    unlock_requirements=[packages[-1].id] if packages else [],
                    theme_color=stage.color_scheme.get("secondary", "#8B5CF6"),
                    icon="📚"
                )
                packages.append(learning_package)
                package_number += 1
                
                # Her 2-3 konudan sonra pratik paketi
                if package_number % 3 == 0:
                    practice_package = Package(
                        stage_id=stage.id,
                        number=package_number,
                        title=f"Pratik: {', '.join(subtopics[max(0, package_number-4):package_number-1])}",
                        description="Öğrenilen konuların pekiştirilmesi",
                        type=PackageType.PRACTICE,
                        curriculum_section=stage.main_topic,
                        topics=subtopics[max(0, package_number-4):package_number-1],
                        learning_objectives=["Öğrenilen konuları pratik etmek"],
                        estimated_duration_minutes=30,
                        difficulty=self._get_difficulty(curriculum.get(stage.main_topic, {}).get("difficulty", "intermediate")),
                        xp_reward=75,
                        status=PackageStatus.LOCKED,
                        unlock_requirements=[packages[-1].id],
                        theme_color=stage.color_scheme.get("accent", "#F59E0B"),
                        icon="✏️"
                    )
                    packages.append(practice_package)
                    package_number += 1
            
            # 3. Tekrar Paketi
            review_package = Package(
                stage_id=stage.id,
                number=package_number,
                title=f"{stage.title} - Tekrar",
                description=f"{stage.title} konularının tekrarı ve özeti",
                type=PackageType.REVIEW,
                curriculum_section=stage.main_topic,
                topics=[stage.main_topic],
                subtopics=subtopics,
                learning_objectives=["Tüm konuları gözden geçirmek"],
                estimated_duration_minutes=40,
                difficulty=self._get_difficulty(curriculum.get(stage.main_topic, {}).get("difficulty", "intermediate")),
                xp_reward=75,
                status=PackageStatus.LOCKED,
                unlock_requirements=[packages[-1].id],
                theme_color=stage.color_scheme.get("primary", "#6366F1"),
                icon="🔄"
            )
            packages.append(review_package)
            package_number += 1
            
            # 4. Kapanış Paketi (Final Sınavları)
            closure_package = Package(
                stage_id=stage.id,
                number=package_number,
                title=f"{stage.title} - Final",
                description=f"{stage.title} kapanış sınavları ve değerlendirme",
                type=PackageType.CLOSURE,
                curriculum_section=stage.main_topic,
                topics=[stage.main_topic],
                subtopics=subtopics,
                learning_objectives=[
                    "Stage'i başarıyla tamamlamak",
                    "Tüm konularda yeterlilik göstermek"
                ],
                required_exam_score=75.0,
                estimated_duration_minutes=60,
                difficulty=DifficultyLevel.ADVANCED,
                xp_reward=200,
                status=PackageStatus.LOCKED,
                unlock_requirements=[packages[-1].id],
                theme_color="#10B981",
                icon="🏆"
            )
            packages.append(closure_package)
            stage.closure_package_id = closure_package.id
            
            stage.packages = packages
            stage.xp_total = sum(p.xp_reward for p in packages)
        
        total_packages = sum(len(s.packages) for s in stages)
        self._add_thought(
            agent="Package Creator",
            action="create_packages_for_stages",
            reasoning=f"Toplam {total_packages} paket oluşturuldu. "
                     f"Her stage: Giriş → Öğrenme → Pratik → Tekrar → Kapanış yapısında.",
            output={
                "total_packages": total_packages,
                "packages_per_stage": [len(s.packages) for s in stages]
            }
        )
        
        return stages
    
    async def _plan_exams(self, goal: LearningGoal, stages: List[Stage]) -> List[Stage]:
        """Sınav stratejisi oluştur"""
        
        exam_types_to_use = [
            ExamType.MULTIPLE_CHOICE,
            ExamType.FEYNMAN,
            ExamType.PROBLEM_SOLVING,
            ExamType.SHORT_ANSWER
        ]
        
        if goal.exam_preferences:
            exam_types_to_use = goal.exam_preferences + exam_types_to_use
        
        for stage in stages:
            for package in stage.packages:
                exams = []
                exercises = []
                
                if package.type == PackageType.LEARNING:
                    # Konu sonu mini test
                    mini_quiz = Exam(
                        title=f"{package.title} - Mini Test",
                        description="Konuyu anladığını test et",
                        type=ExamType.MULTIPLE_CHOICE,
                        questions=self._generate_sample_questions(package.topics[0] if package.topics else "", 5, ExamType.MULTIPLE_CHOICE),
                        time_limit_minutes=10,
                        passing_score=60.0,
                        max_attempts=5,
                        weight_in_package=0.3
                    )
                    exams.append(mini_quiz)
                    
                    # Pratik egzersiz
                    practice = Exercise(
                        type=ExerciseType.DRILL,
                        title=f"{package.title} - Alıştırma",
                        instructions="Verilen soruları çöz",
                        duration_minutes=15,
                        xp_reward=30
                    )
                    exercises.append(practice)
                
                elif package.type == PackageType.PRACTICE:
                    # Karma egzersizler
                    for ex_type in [ExerciseType.RETRIEVAL, ExerciseType.ELABORATION, ExerciseType.SPACED_REPETITION]:
                        ex = Exercise(
                            type=ex_type,
                            title=f"{package.title} - {ex_type.value.replace('_', ' ').title()}",
                            instructions=f"{ex_type.value} tekniği ile pratik",
                            duration_minutes=10,
                            xp_reward=25
                        )
                        exercises.append(ex)
                
                elif package.type == PackageType.CLOSURE:
                    # 1. Çoktan seçmeli sınav
                    mc_exam = Exam(
                        title=f"{stage.title} - Final Test",
                        description="Kapsamlı çoktan seçmeli test",
                        type=ExamType.MULTIPLE_CHOICE,
                        questions=self._generate_sample_questions(stage.main_topic, 20, ExamType.MULTIPLE_CHOICE),
                        time_limit_minutes=30,
                        passing_score=70.0,
                        max_attempts=3,
                        weight_in_package=0.4
                    )
                    exams.append(mc_exam)
                    
                    # 2. Feynman Tekniği Sınavı
                    feynman_exam = Exam(
                        title=f"{stage.title} - Feynman Sınavı",
                        description="Konuyu kendi cümlelerinle anlat",
                        type=ExamType.FEYNMAN,
                        questions=[],
                        passing_score=70.0,
                        max_attempts=2,
                        weight_in_package=0.3,
                        feynman_config={
                            "topic": stage.main_topic,
                            "subtopics": stage.covered_topics,
                            "min_explanation_words": 100,
                            "required_concepts": stage.covered_topics[:3],
                            "audience_level": "beginner",
                            "evaluation_criteria": [
                                "Kavram doğruluğu",
                                "Basit dil kullanımı",
                                "Örnek kullanımı",
                                "Mantıksal akış",
                                "Eksik bilgi tespiti"
                            ]
                        }
                    )
                    exams.append(feynman_exam)
                    
                    # 3. Problem Çözme Sınavı
                    problem_exam = Exam(
                        title=f"{stage.title} - Problem Çözme",
                        description="Gerçek problemleri çöz",
                        type=ExamType.PROBLEM_SOLVING,
                        questions=self._generate_sample_questions(stage.main_topic, 5, ExamType.PROBLEM_SOLVING),
                        time_limit_minutes=45,
                        passing_score=65.0,
                        max_attempts=3,
                        weight_in_package=0.3
                    )
                    exams.append(problem_exam)
                
                package.exams = exams
                package.exercises = exercises
        
        total_exams = sum(len(p.exams) for s in stages for p in s.packages)
        total_exercises = sum(len(p.exercises) for s in stages for p in s.packages)
        
        self._add_thought(
            agent="Exam Strategist",
            action="plan_exams_and_exercises",
            reasoning=f"Toplam {total_exams} sınav ve {total_exercises} egzersiz planlandı. "
                     f"Her kapanış paketinde: Çoktan seçmeli + Feynman + Problem çözme sınavları var.",
            output={
                "total_exams": total_exams,
                "total_exercises": total_exercises,
                "exam_types_used": list(set(e.type.value for s in stages for p in s.packages for e in p.exams))
            }
        )
        
        return stages
    
    async def _optimize_timeline(self, goal: LearningGoal, stages: List[Stage]) -> List[Stage]:
        """Zaman çizelgesini optimize et"""
        
        total_hours = sum(s.estimated_duration_days * goal.daily_hours for s in stages)
        
        if goal.deadline:
            try:
                deadline = datetime.fromisoformat(goal.deadline)
                days_until_deadline = (deadline - datetime.now()).days
                
                if days_until_deadline > 0:
                    # Zaman baskısına göre ayarla
                    available_hours = days_until_deadline * goal.daily_hours
                    
                    if available_hours < total_hours:
                        # Yoğunlaştır
                        ratio = available_hours / total_hours
                        for stage in stages:
                            stage.estimated_duration_days = max(2, int(stage.estimated_duration_days * ratio))
            except:
                pass
        
        # Tahmini bitiş hesapla
        current_day = 0
        for stage in stages:
            stage.estimated_duration_days = max(3, stage.estimated_duration_days)
            current_day += stage.estimated_duration_days
        
        self._add_thought(
            agent="Timeline Optimizer",
            action="optimize_study_timeline",
            reasoning=f"Toplam {current_day} günlük çalışma planı oluşturuldu. "
                     f"Günlük {goal.daily_hours} saat çalışma varsayımıyla.",
            output={
                "total_days": current_day,
                "total_hours": current_day * goal.daily_hours,
                "daily_hours": goal.daily_hours,
                "deadline": goal.deadline
            }
        )
        
        return stages
    
    async def _finalize_plan(self, goal: LearningGoal, stages: List[Stage]) -> CurriculumPlan:
        """Final planı oluştur"""
        
        total_packages = sum(len(s.packages) for s in stages)
        total_exams = sum(len(p.exams) for s in stages for p in s.packages)
        total_exercises = sum(len(p.exercises) for s in stages for p in s.packages)
        total_xp = sum(s.xp_total for s in stages)
        total_hours = sum(
            sum(p.estimated_duration_minutes for p in s.packages) / 60 
            for s in stages
        )
        total_days = sum(s.estimated_duration_days for s in stages)
        
        plan = CurriculumPlan(
            goal=goal,
            title=f"{goal.title} - Öğrenme Yolculuğu",
            description=f"{goal.subject} için kapsamlı öğrenme planı. {goal.target_outcome}",
            stages=stages,
            current_stage_id=stages[0].id if stages else None,
            total_packages=total_packages,
            total_exams=total_exams,
            total_exercises=total_exercises,
            estimated_total_hours=total_hours,
            estimated_completion_days=total_days,
            total_xp_possible=total_xp,
            planning_metadata={
                "algorithm": "curriculum_planner_v2",
                "agents_used": ["Goal Analyzer", "Curriculum Selector", "Topic Mapper", 
                               "Stage Planner", "Package Creator", "Exam Strategist", "Timeline Optimizer"],
                "total_thinking_steps": len(self.thoughts)
            },
            agent_reasoning=[t.to_dict() for t in self.thoughts]
        )
        
        self._add_thought(
            agent="Plan Finalizer",
            action="create_final_curriculum_plan",
            reasoning=f"Müfredat planı tamamlandı! "
                     f"{len(stages)} stage, {total_packages} paket, {total_exams} sınav. "
                     f"Tahmini süre: {total_days} gün, {total_hours:.1f} saat. "
                     f"Toplam XP: {total_xp}",
            output={
                "plan_id": plan.id,
                "stages": len(stages),
                "packages": total_packages,
                "exams": total_exams,
                "exercises": total_exercises,
                "total_hours": round(total_hours, 1),
                "total_days": total_days,
                "total_xp": total_xp
            }
        )
        
        return plan
    
    def _get_difficulty(self, difficulty_str: str) -> DifficultyLevel:
        """String'den DifficultyLevel'a çevir"""
        mapping = {
            "beginner": DifficultyLevel.BEGINNER,
            "elementary": DifficultyLevel.ELEMENTARY,
            "intermediate": DifficultyLevel.INTERMEDIATE,
            "upper_intermediate": DifficultyLevel.UPPER_INTERMEDIATE,
            "advanced": DifficultyLevel.ADVANCED,
            "expert": DifficultyLevel.EXPERT,
            "master": DifficultyLevel.MASTER
        }
        return mapping.get(difficulty_str.lower(), DifficultyLevel.INTERMEDIATE)
    
    def _generate_sample_questions(self, topic: str, count: int, exam_type: ExamType) -> List[ExamQuestion]:
        """Örnek sorular oluştur (gerçek uygulamada LLM kullanılacak)"""
        questions = []
        for i in range(count):
            if exam_type == ExamType.MULTIPLE_CHOICE:
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} ile ilgili soru {i+1}",
                    options=["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4"],
                    correct_answer="A",
                    explanation=f"Doğru cevap A çünkü...",
                    points=10,
                    topic=topic
                )
            elif exam_type == ExamType.PROBLEM_SOLVING:
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} konusunda problem {i+1}: Verilen koşulları kullanarak çözünüz.",
                    explanation="Adım adım çözüm...",
                    points=20,
                    topic=topic,
                    rubric={
                        "problem_understanding": 5,
                        "solution_approach": 5,
                        "calculations": 5,
                        "final_answer": 5
                    }
                )
            else:
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} ile ilgili soru {i+1}",
                    points=10,
                    topic=topic
                )
            questions.append(q)
        return questions


# ==================== SINGLETON ====================

_planner_instance: Optional[CurriculumPlannerAgent] = None

def get_curriculum_planner() -> CurriculumPlannerAgent:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = CurriculumPlannerAgent()
    return _planner_instance
