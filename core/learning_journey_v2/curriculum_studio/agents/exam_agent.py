"""
📋 Exam Agent - Sınav Oluşturucu

Sorumluluklar:
- Soru üretimi (Bloom taksonomisine göre)
- Feynman sınavları tasarımı
- Çoktan seçmeli testler
- Problem çözme sınavları
- Spaced repetition soruları
- Zayıf alan vurgulu sorular
"""

import asyncio
import random
from typing import Dict, Any, AsyncGenerator, List

from .base_agent import BaseCurriculumAgent, AgentThought, ThinkingPhase


class ExamAgent(BaseCurriculumAgent):
    """
    Sınav Oluşturucu Agent
    
    Bloom taksonomisine dayalı, çeşitli sınav türleri oluşturan agent.
    Spaced repetition ve weakness detection ile entegre çalışır.
    """
    
    # Soru türleri
    QUESTION_TYPES = {
        "multiple_choice": {
            "name": "Çoktan Seçmeli",
            "bloom_levels": ["remember", "understand", "apply"],
            "difficulty_range": (1, 7),
            "time_per_question": 90  # saniye
        },
        "true_false": {
            "name": "Doğru/Yanlış",
            "bloom_levels": ["remember", "understand"],
            "difficulty_range": (1, 4),
            "time_per_question": 45
        },
        "fill_blank": {
            "name": "Boşluk Doldurma",
            "bloom_levels": ["remember", "understand", "apply"],
            "difficulty_range": (2, 6),
            "time_per_question": 60
        },
        "short_answer": {
            "name": "Kısa Cevap",
            "bloom_levels": ["understand", "apply", "analyze"],
            "difficulty_range": (3, 8),
            "time_per_question": 120
        },
        "problem_solving": {
            "name": "Problem Çözme",
            "bloom_levels": ["apply", "analyze", "evaluate"],
            "difficulty_range": (4, 10),
            "time_per_question": 300
        },
        "feynman": {
            "name": "Feynman Tekniği",
            "bloom_levels": ["understand", "analyze", "evaluate", "create"],
            "difficulty_range": (5, 10),
            "time_per_question": 600
        },
        "concept_map": {
            "name": "Kavram Haritası",
            "bloom_levels": ["understand", "analyze", "create"],
            "difficulty_range": (4, 9),
            "time_per_question": 480
        }
    }
    
    # Bloom seviyelerine göre soru ağırlıkları
    BLOOM_WEIGHTS = {
        "beginner": {"remember": 0.4, "understand": 0.4, "apply": 0.2},
        "intermediate": {"understand": 0.3, "apply": 0.4, "analyze": 0.3},
        "advanced": {"apply": 0.2, "analyze": 0.4, "evaluate": 0.3, "create": 0.1}
    }
    
    def __init__(self):
        super().__init__(
            name="Sınav Uzmanı",
            role="Değerlendirme Uzmanı",
            specialty="Soru üretimi, Bloom taksonomisi, ölçme-değerlendirme",
            model_preference="openai/gpt-4o-mini",
            thinking_style="precise and pedagogically rigorous"
        )
        self.icon = "📋"
    
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Sınav planlaması yap
        
        Steps:
        1. Sınav Stratejisi
        2. Soru Türü Dağılımı
        3. Bloom Seviyesi Eşleştirme
        4. Spaced Repetition Soruları
        5. Zayıf Alan Vurgulu Sorular
        """
        goal = context.get("goal")
        pedagogy_result = context.get("pedagogy_result", {})
        
        # Intro
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="baslangic",
            phase=ThinkingPhase.ANALYZING,
            thinking="📋 Sınav sistemi tasarlanıyor...",
            reasoning="Bloom taksonomisi ve öğrenme hedeflerine uygun sınavlar oluşturacağım.",
            is_streaming=True
        )
        
        await asyncio.sleep(0.5)
        
        # ===== STEP 1: Sınav Stratejisi =====
        async for thought in self.think(
            prompt=self._build_exam_strategy_prompt(goal),
            step="sinav_stratejisi",
            context=context
        ):
            yield thought
        
        # ===== STEP 2: Soru Türü Dağılımı =====
        async for thought in self._plan_question_distribution(goal, context):
            yield thought
        
        # ===== STEP 3: Bloom Eşleştirme =====
        async for thought in self._map_bloom_levels(goal, context):
            yield thought
        
        # ===== STEP 4: Spaced Repetition Soruları =====
        async for thought in self._plan_spaced_repetition_questions(goal, context):
            yield thought
        
        # ===== STEP 5: Stage Closure Planı =====
        async for thought in self._plan_stage_closure_exams(goal, context):
            yield thought
        
        # Final
        exam_plan = self._compile_exam_plan(context)
        context["exam_plan"] = exam_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ozet",
            phase=ThinkingPhase.CONCLUDING,
            thinking="✅ Sınav planı tamamlandı",
            conclusion=f"Toplam {exam_plan.get('total_questions', 0)} soru planlandı.",
            evidence=[
                f"Çoktan seçmeli: {exam_plan.get('mc_count', 0)}",
                f"Problem çözme: {exam_plan.get('problem_count', 0)}",
                f"Feynman: {exam_plan.get('feynman_count', 0)}"
            ],
            confidence=0.9,
            is_complete=True
        )
    
    def _build_exam_strategy_prompt(self, goal) -> str:
        """Sınav stratejisi promptu"""
        subject = goal.subject if hasattr(goal, 'subject') else "Genel"
        
        return f"""Sınav stratejisi oluştur:

Konu: {subject}
Hedef: {goal.target_outcome if hasattr(goal, 'target_outcome') else 'Genel öğrenme'}
Zorluk Tercihi: {goal.difficulty_preference if hasattr(goal, 'difficulty_preference') else 'intermediate'}

Belirle:
1. Ana sınav türleri (test, problem çözme, Feynman)
2. Her paket için sınav sayısı
3. Geçme puanı stratejisi
4. Yeniden deneme politikası
5. Feedback detay seviyesi

JSON formatında döndür."""
    
    async def _plan_question_distribution(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Soru türü dağılımı"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="soru_dagilimi",
            phase=ThinkingPhase.REASONING,
            thinking="📊 Soru türü dağılımı hesaplanıyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.2)
        
        # Konu bazlı soru dağılımı
        subject = goal.subject.lower() if hasattr(goal, 'subject') else "genel"
        
        if "matematik" in subject or "fizik" in subject:
            distribution = {
                "multiple_choice": 0.35,
                "problem_solving": 0.40,
                "short_answer": 0.15,
                "feynman": 0.10
            }
        elif "ingilizce" in subject or "dil" in subject:
            distribution = {
                "multiple_choice": 0.30,
                "fill_blank": 0.25,
                "short_answer": 0.25,
                "feynman": 0.20
            }
        else:
            distribution = {
                "multiple_choice": 0.40,
                "short_answer": 0.25,
                "problem_solving": 0.20,
                "feynman": 0.15
            }
        
        context["question_distribution"] = distribution
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="soru_dagilimi",
            phase=ThinkingPhase.CONCLUDING,
            thinking="📊 Soru dağılımı belirlendi",
            evidence=[f"{k}: %{int(v*100)}" for k, v in distribution.items()],
            confidence=0.88,
            is_complete=True
        )
    
    async def _map_bloom_levels(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Bloom seviyesi eşleştirme"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="bloom_eslestirme",
            phase=ThinkingPhase.ANALYZING,
            thinking="🎯 Bloom taksonomisi eşleştirmesi yapılıyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.0)
        
        difficulty = goal.difficulty_preference if hasattr(goal, 'difficulty_preference') else "intermediate"
        
        if hasattr(difficulty, 'value'):
            difficulty = difficulty.value
        
        # Difficulty'yi kategorize et
        if difficulty in ["beginner", "elementary"]:
            level = "beginner"
        elif difficulty in ["advanced", "expert", "master"]:
            level = "advanced"
        else:
            level = "intermediate"
        
        bloom_weights = self.BLOOM_WEIGHTS.get(level, self.BLOOM_WEIGHTS["intermediate"])
        context["bloom_weights"] = bloom_weights
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="bloom_eslestirme",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🎯 Bloom seviyeleri eşleştirildi",
            reasoning=f"Seviye: {level}",
            evidence=[f"{k}: %{int(v*100)}" for k, v in bloom_weights.items()],
            confidence=0.9,
            is_complete=True
        )
    
    async def _plan_spaced_repetition_questions(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Spaced repetition soruları planla"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="spaced_repetition",
            phase=ThinkingPhase.ANALYZING,
            thinking="🔄 Aralıklı tekrar soruları planlanıyor...",
            reasoning="Önceki paketlerden tekrar soruları eklenecek.",
            is_streaming=True
        )
        
        await asyncio.sleep(1.5)
        
        # Spaced repetition planı
        spaced_plan = {
            "enabled": True,
            "strategy": "progressive",  # Her pakette öncekilerden artan oranda soru
            "ratios": {
                "package_2": {"from_package_1": 0.10},  # %10 önceki paketten
                "package_3": {"from_package_1": 0.05, "from_package_2": 0.10},
                "package_4": {"from_package_1": 0.05, "from_package_2": 0.05, "from_package_3": 0.10},
                "stage_closure": {"from_all": 0.30}  # %30 tüm paketlerden
            },
            "priority": "weak_areas_first",  # Zayıf alanlar öncelikli
            "question_selection": "adaptive"  # Performansa göre adaptif
        }
        
        context["spaced_repetition_plan"] = spaced_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="spaced_repetition",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🔄 Aralıklı tekrar planı hazır",
            conclusion="Progressive spaced repetition stratejisi uygulanacak.",
            evidence=[
                "Her pakette öncekilerden %5-10 soru",
                "Zayıf alanlar öncelikli",
                "Stage closure'da %30 tekrar"
            ],
            confidence=0.92,
            is_complete=True
        )
    
    async def _plan_stage_closure_exams(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Stage bitirme sınavları planla"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="stage_closure",
            phase=ThinkingPhase.REASONING,
            thinking="🎓 Stage bitirme sınavları tasarlanıyor...",
            reasoning="Dinamik, zayıf alan vurgulu kapanış sınavları oluşturulacak.",
            is_streaming=True
        )
        
        await asyncio.sleep(1.3)
        
        # Stage closure planı
        closure_plan = {
            "generation_timing": "after_packages_complete",  # Paketler bittikten sonra üret
            "dynamic_question_selection": True,
            "weakness_emphasis": {
                "enabled": True,
                "weak_threshold": 0.60,  # %60 altı zayıf
                "extra_questions_ratio": 0.40  # Zayıf alanlardan %40 ekstra soru
            },
            "question_count": {
                "base": 20,
                "from_packages": 10,  # Paketlerden
                "weakness_focused": 10  # Zayıf alan odaklı
            },
            "exam_types": ["multiple_choice", "problem_solving", "feynman"],
            "passing_score": 75,
            "time_limit_minutes": 45
        }
        
        context["stage_closure_plan"] = closure_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="stage_closure",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🎓 Stage bitirme planı hazır",
            conclusion="Dinamik, adaptif kapanış sınavları üretilecek.",
            evidence=[
                f"Toplam {closure_plan['question_count']['base'] + closure_plan['question_count']['from_packages']} soru",
                "Zayıf alanlardan %40 ekstra",
                f"Geçme puanı: %{closure_plan['passing_score']}"
            ],
            confidence=0.93,
            is_complete=True
        )
    
    def _compile_exam_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tüm sınav planını derle"""
        distribution = context.get("question_distribution", {})
        spaced = context.get("spaced_repetition_plan", {})
        closure = context.get("stage_closure_plan", {})
        
        # Tahmini soru sayıları
        base_questions_per_package = 15
        packages_estimate = 20  # Tahmini toplam paket sayısı
        
        total = base_questions_per_package * packages_estimate
        
        return {
            "total_questions": total,
            "mc_count": int(total * distribution.get("multiple_choice", 0.4)),
            "problem_count": int(total * distribution.get("problem_solving", 0.2)),
            "feynman_count": int(total * distribution.get("feynman", 0.1)),
            "short_answer_count": int(total * distribution.get("short_answer", 0.2)),
            "distribution": distribution,
            "spaced_repetition": spaced,
            "stage_closure": closure,
            "bloom_weights": context.get("bloom_weights", {}),
            "passing_scores": {
                "package": 70,
                "stage_closure": 75,
                "final": 80
            }
        }
    
    def generate_question_template(
        self, 
        topic: str, 
        question_type: str, 
        bloom_level: str
    ) -> Dict[str, Any]:
        """Soru şablonu oluştur"""
        templates = {
            "remember": {
                "stems": [
                    f"{topic} nedir?",
                    f"{topic}'ın tanımını yapınız.",
                    f"{topic}'ın temel özellikleri nelerdir?"
                ]
            },
            "understand": {
                "stems": [
                    f"{topic}'ı kendi cümlelerinizle açıklayınız.",
                    f"{topic}'ın önemini belirtiniz.",
                    f"{topic} ile ilgili bir örnek veriniz."
                ]
            },
            "apply": {
                "stems": [
                    f"{topic}'ı kullanarak şu problemi çözünüz:",
                    f"{topic}'ı yeni bir duruma uygulayınız:",
                    f"{topic} ile ilgili hesaplama yapınız:"
                ]
            },
            "analyze": {
                "stems": [
                    f"{topic}'ın bileşenlerini analiz ediniz.",
                    f"{topic} ile X arasındaki farkları karşılaştırınız.",
                    f"{topic}'ın nedenlerini açıklayınız."
                ]
            },
            "evaluate": {
                "stems": [
                    f"{topic} yaklaşımını değerlendiriniz.",
                    f"{topic}'ın etkinliğini tartışınız.",
                    f"{topic}'ın avantaj ve dezavantajlarını belirtiniz."
                ]
            },
            "create": {
                "stems": [
                    f"{topic} kullanarak yeni bir çözüm öneriniz.",
                    f"{topic}'ı birleştirerek özgün bir yaklaşım geliştirin.",
                    f"{topic} ile ilgili bir proje tasarlayınız."
                ]
            }
        }
        
        level_templates = templates.get(bloom_level, templates["understand"])
        
        return {
            "topic": topic,
            "question_type": question_type,
            "bloom_level": bloom_level,
            "stem_template": random.choice(level_templates["stems"]),
            "difficulty": self._estimate_difficulty(bloom_level),
            "time_limit_seconds": self.QUESTION_TYPES.get(question_type, {}).get("time_per_question", 90)
        }
    
    def _estimate_difficulty(self, bloom_level: str) -> int:
        """Bloom seviyesine göre zorluk tahmini"""
        difficulty_map = {
            "remember": 2,
            "understand": 3,
            "apply": 5,
            "analyze": 7,
            "evaluate": 8,
            "create": 9
        }
        return difficulty_map.get(bloom_level, 5)
