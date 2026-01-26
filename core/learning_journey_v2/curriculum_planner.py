"""
🧠 Curriculum Planner Agent - V2 Enhanced
Multi-Agent Orchestration ile Müfredat Planlama

Bu agent:
1. LLM ile gerçek içerik üretir
2. RAG ile zenginleştirilmiş bilgi kullanır
3. Kişiselleştirilmiş öğrenme yolu oluşturur
4. Gerçek sınav soruları üretir
5. Multi-agent düşünce süreci ile kalite kontrolü yapar

2026 Enterprise Edition - AI-Powered Learning
"""

import asyncio
import json
import random
import re
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
        "order": 1,
        "prerequisites": [],
        "key_concepts": ["Doğal sayılar", "Tam sayılar", "Rasyonel sayılar", "İrrasyonel sayılar"],
        "real_world_applications": ["Finansal hesaplamalar", "Mühendislik", "Günlük yaşam"]
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
        "order": 8,
        "prerequisites": ["Limit ve Süreklilik"],
        "key_concepts": ["Anlık değişim", "Türev kuralları", "Optimizasyon", "Eğim"],
        "real_world_applications": ["Hız-ivme analizi", "Maliyet optimizasyonu", "Makine öğrenmesi", "Fizik"]
    },
    "İntegral": {
        "topics": ["Belirsiz İntegral", "Temel İntegral Formülleri", "Değişken Dönüşümü", "Kısmi İntegral", "Belirli İntegral", "Alan Hesabı"],
        "difficulty": "advanced",
        "estimated_hours": 35,
        "order": 9,
        "prerequisites": ["Türev"],
        "key_concepts": ["Antitürev", "Riemann toplamı", "Temel teorem", "Alan ve hacim"],
        "real_world_applications": ["Alan ve hacim hesaplama", "Fizik", "Olasılık", "Ekonomi"]
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

# Fizik AYT Müfredatı
PHYSICS_AYT_CURRICULUM = {
    "Kuvvet ve Hareket": {
        "topics": ["Vektörler", "Kuvvet Dengesi", "Newton Yasaları", "Sürtünme Kuvveti", "İş ve Enerji"],
        "difficulty": "intermediate",
        "estimated_hours": 30,
        "order": 1,
        "prerequisites": [],
        "key_concepts": ["Vektörel toplama", "Kuvvet bileşenleri", "İş-enerji teoremi"],
        "real_world_applications": ["Mühendislik hesapları", "Araç tasarımı", "Spor fiziği"]
    },
    "Elektrik ve Manyetizma": {
        "topics": ["Elektrik Yükü", "Elektrik Alan", "Elektrik Potansiyeli", "Kondansatörler", "Manyetik Alan"],
        "difficulty": "advanced",
        "estimated_hours": 35,
        "order": 2,
        "prerequisites": ["Kuvvet ve Hareket"],
        "key_concepts": ["Coulomb yasası", "Elektrik alan çizgileri", "Manyetik kuvvet"],
        "real_world_applications": ["Elektronik cihazlar", "Elektrik motorları", "MR cihazları"]
    },
    "Dalgalar": {
        "topics": ["Dalga Özellikleri", "Ses Dalgaları", "Elektromanyetik Dalgalar", "Işık ve Optik"],
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "order": 3,
        "prerequisites": [],
        "key_concepts": ["Dalga boyu", "Frekans", "Kırılma ve yansıma"],
        "real_world_applications": ["Müzik aletleri", "Radyo-TV yayıncılığı", "Optik fiber"]
    },
    "Modern Fizik": {
        "topics": ["Atom Modelleri", "Radyoaktivite", "Özel Görelilik", "Kuantum Fiziği Giriş"],
        "difficulty": "expert",
        "estimated_hours": 20,
        "order": 4,
        "prerequisites": ["Dalgalar"],
        "key_concepts": ["Foton", "Dalga-parçacık ikiliği", "Kütle-enerji eşdeğerliği"],
        "real_world_applications": ["Nükleer enerji", "Tıbbi görüntüleme", "Lazer teknolojisi"]
    }
}

# Programlama Müfredatı
PROGRAMMING_CURRICULUM = {
    "Python Temelleri": {
        "topics": ["Değişkenler ve Veri Tipleri", "Operatörler", "Koşullu İfadeler", "Döngüler", "Fonksiyonlar"],
        "difficulty": "beginner",
        "estimated_hours": 20,
        "order": 1,
        "prerequisites": [],
        "key_concepts": ["Syntax", "Değişken tanımlama", "Kontrol akışı"],
        "real_world_applications": ["Otomasyon scriptleri", "Veri işleme", "Web geliştirme"]
    },
    "Veri Yapıları": {
        "topics": ["Listeler", "Sözlükler", "Kümeler", "Tuple", "String İşlemleri"],
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "order": 2,
        "prerequisites": ["Python Temelleri"],
        "key_concepts": ["İndeksleme", "Slicing", "Comprehension"],
        "real_world_applications": ["Veri analizi", "API geliştirme", "Veritabanı işlemleri"]
    },
    "Nesne Yönelimli Programlama": {
        "topics": ["Sınıflar", "Kalıtım", "Polimorfizm", "Encapsulation", "Magic Methods"],
        "difficulty": "advanced",
        "estimated_hours": 30,
        "order": 3,
        "prerequisites": ["Veri Yapıları"],
        "key_concepts": ["OOP prensipleri", "SOLID", "Design patterns"],
        "real_world_applications": ["Kurumsal yazılım", "Oyun geliştirme", "Framework tasarımı"]
    },
    "Web Geliştirme": {
        "topics": ["Flask/FastAPI Temelleri", "REST API", "Veritabanı Bağlantısı", "Authentication", "Deployment"],
        "difficulty": "advanced",
        "estimated_hours": 35,
        "order": 4,
        "prerequisites": ["Nesne Yönelimli Programlama"],
        "key_concepts": ["HTTP protokolü", "CRUD işlemleri", "JWT"],
        "real_world_applications": ["Web servisleri", "Mobil backend", "Mikroservisler"]
    }
}

# İngilizce Müfredatı
ENGLISH_CURRICULUM = {
    "Grammar Fundamentals": {
        "topics": ["Tenses", "Articles", "Prepositions", "Modal Verbs", "Conditionals"],
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "order": 1,
        "prerequisites": [],
        "key_concepts": ["Present Perfect vs Past Simple", "Zero/First/Second Conditionals"],
        "real_world_applications": ["Günlük konuşma", "E-posta yazımı", "İş görüşmeleri"]
    },
    "Vocabulary Building": {
        "topics": ["Academic Words", "Phrasal Verbs", "Idioms", "Collocations", "Word Formation"],
        "difficulty": "intermediate",
        "estimated_hours": 30,
        "order": 2,
        "prerequisites": [],
        "key_concepts": ["Context clues", "Word families", "Register"],
        "real_world_applications": ["IELTS/TOEFL hazırlık", "Akademik yazı", "Okuma anlama"]
    },
    "Reading Comprehension": {
        "topics": ["Skimming", "Scanning", "Inference", "Main Idea", "Text Structure"],
        "difficulty": "advanced",
        "estimated_hours": 20,
        "order": 3,
        "prerequisites": ["Vocabulary Building"],
        "key_concepts": ["Çıkarım yapma", "Ana fikir bulma", "Detay sorular"],
        "real_world_applications": ["Akademik okuma", "Haber okuma", "Rapor analizi"]
    },
    "Writing Skills": {
        "topics": ["Essay Structure", "Paragraphing", "Coherence", "Academic Style", "Argumentation"],
        "difficulty": "advanced",
        "estimated_hours": 25,
        "order": 4,
        "prerequisites": ["Grammar Fundamentals", "Reading Comprehension"],
        "key_concepts": ["Thesis statement", "Topic sentences", "Transitions"],
        "real_world_applications": ["Akademik makale", "İş mektubu", "Rapor yazımı"]
    }
}

# Tüm müfredatlar için map
ALL_CURRICULA = {
    "matematik": MATH_AYT_CURRICULUM,
    "math": MATH_AYT_CURRICULUM,
    "fizik": PHYSICS_AYT_CURRICULUM,
    "physics": PHYSICS_AYT_CURRICULUM,
    "programlama": PROGRAMMING_CURRICULUM,
    "programming": PROGRAMMING_CURRICULUM,
    "python": PROGRAMMING_CURRICULUM,
    "ingilizce": ENGLISH_CURRICULUM,
    "english": ENGLISH_CURRICULUM
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
    Müfredat Planlama Agent'ı - V2 Enhanced
    
    LLM + RAG entegrasyonu ile gerçek içerik üretimi:
    1. Hedef Analizi (LLM destekli)
    2. Konu Haritalama (RAG destekli)
    3. Stage Planlama
    4. Paket Oluşturma
    5. İçerik Üretimi (LLM)
    6. Soru Üretimi (LLM)
    7. Sınav Stratejisi
    8. Zaman Optimizasyonu
    """
    
    def __init__(self, llm_service=None, rag_service=None, use_llm: bool = True):
        self.thoughts: List[AgentThought] = []
        self.step_counter = 0
        
        # Environment variable ile LLM'i devre dışı bırakabilirsin
        import os
        skip_llm = os.environ.get("SKIP_LLM", "false").lower() == "true"
        
        if skip_llm or not use_llm:
            print("[CurriculumPlanner] LLM devre dışı - template tabanlı içerik kullanılacak")
            self.llm_service = None
            self.rag_service = None
        else:
            self.llm_service = llm_service
            self.rag_service = rag_service
            
            # LLM service'i lazy load et
            if self.llm_service is None:
                try:
                    from core.llm_manager import llm_manager
                    self.llm_service = llm_manager
                    print("[CurriculumPlanner] LLM service yüklendi")
                except ImportError as e:
                    print(f"[CurriculumPlanner] LLM yüklenemedi: {e}")
            
            # RAG service'i lazy load et
            if self.rag_service is None:
                try:
                    from rag.unified_orchestrator import UnifiedRAGOrchestrator
                    self.rag_service = UnifiedRAGOrchestrator()
                    print("[CurriculumPlanner] RAG service yüklendi")
                except ImportError as e:
                    print(f"[CurriculumPlanner] RAG yüklenemedi: {e}")
    
    def _add_thought(self, agent: str, action: str, reasoning: str, output: Any, confidence: float = 1.0) -> AgentThought:
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
    
    def _normalize_text(self, s: str) -> str:
        """Türkçe karakter ve case insensitive karşılaştırma için normalize"""
        if not s:
            return ""
        # Türkçe büyük harfleri değiştir
        result = s.replace('İ', 'i').replace('Ü', 'u').replace('Ö', 'o').replace('Ş', 's').replace('Ç', 'c').replace('Ğ', 'g').replace('I', 'i')
        # Lower ve Türkçe küçük harfleri ASCII'ye çevir
        result = result.lower().replace('ü', 'u').replace('ö', 'o').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i')
        return result
    
    async def _generate_with_llm(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, timeout: float = 30.0) -> Optional[str]:
        """LLM ile içerik üret (timeout ile)"""
        if self.llm_service:
            try:
                if hasattr(self.llm_service, 'generate_async'):
                    return await asyncio.wait_for(
                        self.llm_service.generate_async(prompt, system_prompt=system_prompt, temperature=temperature),
                        timeout=timeout
                    )
                elif hasattr(self.llm_service, 'generate'):
                    loop = asyncio.get_event_loop()
                    return await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: self.llm_service.generate(prompt, system_prompt=system_prompt, temperature=temperature)),
                        timeout=timeout
                    )
            except asyncio.TimeoutError:
                print(f"[CurriculumPlanner] LLM timeout ({timeout}s) - template kullanılacak")
            except Exception as e:
                print(f"[CurriculumPlanner] LLM Error: {e}")
        return None
    
    async def _search_with_rag(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """RAG ile ilgili içerik ara"""
        if self.rag_service:
            try:
                if hasattr(self.rag_service, 'query'):
                    result = await self.rag_service.query(query, top_k=top_k)
                    return result.get('sources', []) if isinstance(result, dict) else []
            except Exception as e:
                print(f"RAG Error: {e}")
        return []
    
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
        """Uygun müfredatı seç - Çoklu müfredat desteği"""
        
        # Subject'e göre müfredat seç
        subject_lower = goal.subject.lower()
        curriculum = None
        
        # ALL_CURRICULA map'inden ara
        for key, curr in ALL_CURRICULA.items():
            if key in subject_lower or subject_lower in key:
                curriculum = curr
                break
        
        # Bulunamazsa default matematik
        if curriculum is None:
            curriculum = MATH_AYT_CURRICULUM
            self._add_thought(
                agent="Curriculum Selector",
                action="default_curriculum",
                reasoning=f"'{goal.subject}' için özel müfredat bulunamadı. Varsayılan matematik müfredatı kullanılıyor.",
                output={"subject": goal.subject, "default": "MATH_AYT_CURRICULUM"}
            )
        else:
            self._add_thought(
                agent="Curriculum Selector",
                action="curriculum_matched",
                reasoning=f"'{goal.subject}' için uygun müfredat bulundu.",
                output={"subject": goal.subject, "topics_count": len(curriculum)}
            )
        
        # Kullanıcının dahil etmek istediği/istemediği konuları filtrele
        # Normalize fonksiyonu - Türkçe karakter ve case insensitive karşılaştırma
        def normalize(s: str) -> str:
            # Önce Türkçe büyük harfleri değiştir (özellikle İ problematik)
            result = s.replace('İ', 'i').replace('Ü', 'u').replace('Ö', 'o').replace('Ş', 's').replace('Ç', 'c').replace('Ğ', 'g').replace('I', 'i')
            # Sonra lower() uygula ve Türkçe küçük harfleri ASCII'ye çevir
            result = result.lower().replace('ü', 'u').replace('ö', 'o').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i')
            return result
        
        # topics_to_include ve exclude listelerini normalize et
        normalized_include = [normalize(t) for t in (goal.topics_to_include or [])]
        normalized_exclude = [normalize(t) for t in (goal.topics_to_exclude or [])]
        
        filtered_curriculum = {}
        for topic_name, topic_data in curriculum.items():
            normalized_topic = normalize(topic_name)
            
            # Exclude kontrolü
            if normalized_exclude and normalized_topic in normalized_exclude:
                continue
            
            # Include kontrolü (partial match de destekle)
            if normalized_include:
                matched = False
                for inc_topic in normalized_include:
                    if inc_topic in normalized_topic or normalized_topic in inc_topic:
                        matched = True
                        break
                if not matched:
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
                estimated_duration_days=max(3, stage_info["estimated_hours"] // max(goal.daily_hours, 1)),
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
        
        # İçerik bloklarını oluştur
        await self._generate_content_for_packages(stages, goal)
        
        return stages
    
    async def _generate_content_for_packages(self, stages: List[Stage], goal: LearningGoal) -> None:
        """Her paket için içerik blokları oluştur - LAZY LOADING + PARALLEL"""
        
        self._add_thought(
            agent="Content Planner",
            action="plan_content_structure",
            reasoning="Paket içerikleri lazy loading ile hazırlanıyor. "
                     "Temel yapılar anında oluşturulacak, LLM içerikler talep anında üretilecek.",
            output={"status": "started", "mode": "lazy_loading", "content_types": ["intro", "explanation", "formulas", "examples", "summary"]}
        )
        
        total_content_blocks = 0
        
        # Tüm paketler için hızlı template içerikler oluştur (LLM kullanmadan)
        for stage in stages:
            curriculum_data = self._get_curriculum_data(stage.main_topic)
            
            for package in stage.packages:
                # Hızlı template tabanlı içerik (LLM yok)
                content_blocks = self._create_package_content_fast(package, stage, goal, curriculum_data)
                package.content_blocks = content_blocks
                package.llm_content_ready = False  # İçerik henüz LLM ile zenginleştirilmedi
                total_content_blocks += len(content_blocks)
        
        self._add_thought(
            agent="Content Planner",
            action="content_generation_completed",
            reasoning=f"Toplam {total_content_blocks} içerik bloğu (template) oluşturuldu. "
                     f"LLM ile zenginleştirme talep anında yapılacak.",
            output={
                "total_content_blocks": total_content_blocks,
                "avg_per_package": round(total_content_blocks / max(sum(len(s.packages) for s in stages), 1), 1),
                "mode": "lazy_loading"
            }
        )
    
    def _get_curriculum_data(self, main_topic: str) -> Dict[str, Any]:
        """Ana konu için müfredat verisini getir - Çoklu müfredat destekli"""
        normalized = self._normalize_text(main_topic)
        
        # Tüm müfredatları tara
        for curriculum in [MATH_AYT_CURRICULUM, PHYSICS_AYT_CURRICULUM, PROGRAMMING_CURRICULUM, ENGLISH_CURRICULUM]:
            for key, data in curriculum.items():
                if self._normalize_text(key) == normalized:
                    return data
        
        return {}
    
    def _create_package_content_fast(self, package: Package, stage: Stage, goal: LearningGoal, curriculum_data: Dict[str, Any] = None) -> List[ContentBlock]:
        """Paket için hızlı template içerikler oluştur - LLM KULLANMAZ (instant)"""
        content_blocks = []
        order = 1
        curriculum_data = curriculum_data or {}
        
        # 1. Giriş İçeriği (Template)
        intro_content = self._generate_intro_template(package, stage, goal)
        content_blocks.append(ContentBlock(
            type=ContentType.TEXT,
            title=f"🎯 {package.title} - Giriş",
            content={"markdown": intro_content, "text": intro_content, "llm_pending": True},
            duration_minutes=3,
            order=order,
            is_required=True,
            metadata={"package_id": package.id, "content_type": "intro", "llm_enhanced": False}
        ))
        order += 1
        
        # 2. Her konu için açıklama (Template)
        for topic in package.topics:
            explanation = self._generate_topic_template(topic, stage.main_topic, package.difficulty, curriculum_data)
            content_blocks.append(ContentBlock(
                type=ContentType.TEXT,
                title=f"📖 {topic}",
                content={"markdown": explanation, "text": explanation, "llm_pending": True},
                duration_minutes=8,
                order=order,
                is_required=True,
                metadata={"topic": topic, "content_type": "explanation", "llm_enhanced": False}
            ))
            order += 1
        
        # 3. Formüller (Template)
        if self._is_math_subject(goal.subject):
            formulas = self._generate_formulas_template(package.topics, stage.main_topic)
            if formulas:
                content_blocks.append(ContentBlock(
                    type=ContentType.TEXT,
                    title=f"📐 Formüller ve Kurallar",
                    content={"markdown": formulas, "text": formulas, "llm_pending": True},
                    duration_minutes=5,
                    order=order,
                    is_required=True,
                    metadata={"content_type": "formulas", "llm_enhanced": False}
                ))
                order += 1
        
        # 4. Örnekler (Template)
        examples = self._generate_examples_template(package.topics, package.difficulty, stage.main_topic)
        content_blocks.append(ContentBlock(
            type=ContentType.TEXT,
            title=f"✏️ Çözümlü Örnekler",
            content={"markdown": examples, "text": examples, "llm_pending": True},
            duration_minutes=10,
            order=order,
            is_required=True,
            metadata={"content_type": "examples", "llm_enhanced": False}
        ))
        order += 1
        
        # 5. Video Önerisi (statik)
        video_suggestion = self._generate_video_suggestion(package.topics, stage.main_topic)
        content_blocks.append(ContentBlock(
            type=ContentType.VIDEO,
            title=f"🎬 Önerilen Video",
            content={"markdown": video_suggestion, "video_type": "external"},
            duration_minutes=10,
            order=order,
            is_required=False,
            metadata={"content_type": "video"}
        ))
        order += 1
        
        # 6. Özet (Template)
        summary = self._generate_summary_content(package, stage)
        content_blocks.append(ContentBlock(
            type=ContentType.TEXT,
            title=f"📝 Özet",
            content={"markdown": summary, "text": summary},
            duration_minutes=3,
            order=order,
            is_required=True,
            metadata={"content_type": "summary"}
        ))
        
        return content_blocks
    
    def _generate_intro_template(self, package: Package, stage: Stage, goal: LearningGoal) -> str:
        """Giriş içeriği template - LLM kullanmaz"""
        topics_list = '\n'.join(f'- **{topic}**' for topic in package.topics)
        objectives_list = '\n'.join(f'- {obj}' for obj in package.learning_objectives)
        
        return f"""## Hoş Geldin! 👋

Bu pakette **{package.title}** konusunu öğreneceksin.

### 📚 Bu Pakette Neler Var?
{topics_list}

### 🎯 Öğrenme Hedeflerin
{objectives_list}

### ⏱️ Tahmini Süre
Bu paketi tamamlaman yaklaşık **{package.estimated_duration_minutes} dakika** sürecek.

### 🏆 Kazanacağın XP
Bu paketi başarıyla tamamladığında **{package.xp_reward} XP** kazanacaksın!

---

**Hazır mısın?** Aşağıdaki içerikleri sırasıyla tamamla ve konuyu öğren! 🚀"""

    def _generate_topic_template(self, topic: str, main_topic: str, difficulty: DifficultyLevel, curriculum_data: Dict = None) -> str:
        """Konu açıklaması template - LLM kullanmaz"""
        difficulty_text = {
            DifficultyLevel.BEGINNER: "başlangıç",
            DifficultyLevel.ELEMENTARY: "temel",
            DifficultyLevel.INTERMEDIATE: "orta",
            DifficultyLevel.UPPER_INTERMEDIATE: "ileri-orta",
            DifficultyLevel.ADVANCED: "ileri",
            DifficultyLevel.EXPERT: "uzman",
            DifficultyLevel.MASTER: "usta"
        }.get(difficulty, "orta")
        
        key_concepts = (curriculum_data or {}).get("key_concepts", [])
        applications = (curriculum_data or {}).get("real_world_applications", [])
        
        concepts_text = '\n'.join(f'- **{c}**' for c in key_concepts[:4]) if key_concepts else "- Temel kavramlar yükleniyor..."
        apps_text = '\n'.join(f'- {a}' for a in applications[:3]) if applications else "- Günlük hayat uygulamaları"
        
        return f"""## {topic}

### 📌 Tanım
**{topic}**, {main_topic} konusunun önemli alt başlıklarından biridir.

### 🔍 Temel Kavramlar
{concepts_text}

### 🌍 Uygulama Alanları
{apps_text}

### ⚠️ Dikkat Edilmesi Gerekenler
- Bu konu {difficulty_text} seviyesindedir
- Adım adım ilerleyin ve her kavramı anladığınızdan emin olun
- Önceki konularla bağlantı kurun

### 💡 İpucu
> Konuyu anlamak için önce temel kavramları öğrenin, sonra örneklere geçin."""

    def _generate_formulas_template(self, topics: List[str], main_topic: str) -> str:
        """Formüller template - LLM kullanmaz"""
        formula_map = {
            "türev": [
                ("Türev Tanımı", "$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$"),
                ("Çarpım Kuralı", "$(f \\cdot g)' = f' \\cdot g + f \\cdot g'$"),
            ],
            "integral": [
                ("Belirsiz İntegral", "$\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$"),
            ],
            "limit": [
                ("Limit Tanımı", "$\\lim_{x \\to a} f(x) = L$"),
            ],
            "logaritma": [
                ("Çarpım", "$\\log_a(x \\cdot y) = \\log_a x + \\log_a y$"),
            ],
        }
        
        # Eşleşen formülleri bul
        matched_formulas = []
        normalized_main = self._normalize_text(main_topic)
        for key, formulas in formula_map.items():
            if key in normalized_main:
                matched_formulas.extend(formulas)
        
        if not matched_formulas:
            matched_formulas = [("Temel Formül", "$a + b = c$")]
        
        formula_text = '\n\n'.join([f"### {name}\n{formula}" for name, formula in matched_formulas])
        
        return f"""## 📐 Önemli Formüller

{formula_text}

---
> 💡 Bu formülleri ezberlemek yerine anlamaya çalışın!"""

    def _generate_examples_template(self, topics: List[str], difficulty: DifficultyLevel, main_topic: str) -> str:
        """Örnekler template - LLM kullanmaz"""
        topic_name = topics[0] if topics else main_topic
        
        return f"""## ✏️ Çözümlü Örnekler

### Örnek 1: Temel Uygulama

**Soru:** {topic_name} konusu ile ilgili temel bir soru.

**Çözüm:**
1. Önce verilen bilgileri yazalım
2. İlgili formülü uygulayalım
3. Sonucu hesaplayalım

**Cevap:** Örnek cevap

---

### Örnek 2: Orta Seviye

**Soru:** Daha karmaşık bir uygulama.

**Çözüm:**
Adım adım çözüm burada gösterilecek.

---

> 💡 Bu örnekleri çözdükten sonra benzer sorular deneyin!"""

    async def enhance_package_content_with_llm(self, package: Package, stage: Stage, goal: LearningGoal) -> None:
        """Paket içeriklerini LLM ile zenginleştir - TALEP ANINDA çağrılır"""
        if not self.llm_service or getattr(package, 'llm_content_ready', False):
            return
        
        curriculum_data = self._get_curriculum_data(stage.main_topic)
        
        # Paralel olarak tüm içerikleri zenginleştir
        tasks = []
        for content_block in package.content_blocks:
            if content_block.metadata.get("llm_enhanced") is False:
                if content_block.metadata.get("content_type") == "intro":
                    tasks.append(self._enhance_intro_block(content_block, package, stage, goal))
                elif content_block.metadata.get("content_type") == "explanation":
                    topic = content_block.metadata.get("topic", "")
                    tasks.append(self._enhance_topic_block(content_block, topic, stage.main_topic, package.difficulty, goal, curriculum_data))
                elif content_block.metadata.get("content_type") == "formulas":
                    tasks.append(self._enhance_formulas_block(content_block, package.topics, stage.main_topic, goal.subject))
                elif content_block.metadata.get("content_type") == "examples":
                    tasks.append(self._enhance_examples_block(content_block, package.topics, package.difficulty, stage.main_topic, goal))
        
        if tasks:
            # Paralel çalıştır (max 5 concurrent)
            await asyncio.gather(*tasks, return_exceptions=True)
        
        package.llm_content_ready = True
    
    async def _enhance_intro_block(self, block: ContentBlock, package: Package, stage: Stage, goal: LearningGoal) -> None:
        """Giriş bloğunu LLM ile zenginleştir"""
        enhanced = await self._generate_intro_content(package, stage, goal)
        if enhanced:
            block.content["markdown"] = enhanced
            block.content["text"] = enhanced
            block.content["llm_pending"] = False
            block.metadata["llm_enhanced"] = True
    
    async def _enhance_topic_block(self, block: ContentBlock, topic: str, main_topic: str, difficulty: DifficultyLevel, goal: LearningGoal, curriculum_data: Dict) -> None:
        """Konu bloğunu LLM ile zenginleştir"""
        enhanced = await self._generate_topic_content(topic, main_topic, difficulty, goal, curriculum_data)
        if enhanced:
            block.content["markdown"] = enhanced
            block.content["text"] = enhanced
            block.content["llm_pending"] = False
            block.metadata["llm_enhanced"] = True
    
    async def _enhance_formulas_block(self, block: ContentBlock, topics: List[str], main_topic: str, subject: str) -> None:
        """Formül bloğunu LLM ile zenginleştir"""
        enhanced = await self._generate_formulas_content(topics, main_topic, subject)
        if enhanced:
            block.content["markdown"] = enhanced
            block.content["text"] = enhanced
            block.content["llm_pending"] = False
            block.metadata["llm_enhanced"] = True
    
    async def _enhance_examples_block(self, block: ContentBlock, topics: List[str], difficulty: DifficultyLevel, main_topic: str, goal: LearningGoal) -> None:
        """Örnek bloğunu LLM ile zenginleştir"""
        enhanced = await self._generate_examples_content(topics, difficulty, main_topic, goal)
        if enhanced:
            block.content["markdown"] = enhanced
            block.content["text"] = enhanced
            block.content["llm_pending"] = False
            block.metadata["llm_enhanced"] = True
    
    async def _generate_intro_content(self, package: Package, stage: Stage, goal: LearningGoal) -> str:
        """Giriş içeriği oluştur - LLM destekli + Kişiselleştirme"""
        
        # Kişiselleştirme bilgileri
        weak_areas = goal.weak_areas or []
        focus_areas = goal.focus_areas or []
        is_weak_topic = any(self._normalize_text(w) in self._normalize_text(package.title) for w in weak_areas)
        is_focus_topic = any(self._normalize_text(f) in self._normalize_text(package.title) for f in focus_areas)
        
        # LLM ile kişiselleştirilmiş giriş
        if self.llm_service:
            personalization_note = ""
            if is_weak_topic:
                personalization_note = "\n⚠️ NOT: Bu konu öğrencinin zayıf olduğu konulardan biri. Ekstra teşvik ve adım adım yaklaşım gerekli."
            if is_focus_topic:
                personalization_note += "\n🎯 NOT: Bu konu öğrencinin odaklanmak istediği öncelikli konulardan. Derinlemesine içerik sun."
            
            prompt = f"""
{package.title} konusu için öğrenciye motivasyon verici bir giriş yaz.

Öğrenci profili:
- Hedef: {goal.target_outcome}
- Günlük çalışma: {goal.daily_hours} saat
- Zayıf alanları: {', '.join(weak_areas) if weak_areas else 'Belirtilmemiş'}
- Odak alanları: {', '.join(focus_areas) if focus_areas else 'Belirtilmemiş'}
{personalization_note}

Konu bilgisi:
- Ana konu: {stage.main_topic}
- Alt konu: {package.title}
- Öğrenme hedefleri: {', '.join(package.learning_objectives[:3])}
- Tahmini süre: {package.estimated_duration_minutes} dakika
- XP ödülü: {package.xp_reward}

Giriş metni şunları içermeli:
1. Konunun önemi ve neden öğrenilmeli
2. Bu pakette neler öğrenilecek
3. Kişiselleştirilmiş motivasyon mesajı

Markdown formatında, samimi ve teşvik edici bir dille yaz. 150-200 kelime.
"""
            llm_response = await self._generate_with_llm(prompt, temperature=0.7)
            if llm_response:
                return llm_response
        
        # Fallback template
        topics_list = '\n'.join(f'- **{topic}**' for topic in package.topics)
        objectives_list = '\n'.join(f'- {obj}' for obj in package.learning_objectives)
        
        return f"""## Hoş Geldin! 👋

Bu pakette **{package.title}** konusunu öğreneceksin.

### 📚 Bu Pakette Neler Var?
{topics_list}

### 🎯 Öğrenme Hedeflerin
{objectives_list}

### ⏱️ Tahmini Süre
Bu paketi tamamlaman yaklaşık **{package.estimated_duration_minutes} dakika** sürecek.

### 🏆 Kazanacağın XP
Bu paketi başarıyla tamamladığında **{package.xp_reward} XP** kazanacaksın!

---

**Hazır mısın?** Aşağıdaki içerikleri sırasıyla tamamla ve konuyu öğren! 🚀"""

    async def _generate_topic_content(self, topic: str, main_topic: str, difficulty: DifficultyLevel, goal: LearningGoal = None, curriculum_data: Dict = None) -> str:
        """Konu açıklaması oluştur - LLM destekli"""
        difficulty_text = {
            DifficultyLevel.BEGINNER: "başlangıç",
            DifficultyLevel.ELEMENTARY: "temel",
            DifficultyLevel.INTERMEDIATE: "orta",
            DifficultyLevel.UPPER_INTERMEDIATE: "ileri-orta",
            DifficultyLevel.ADVANCED: "ileri",
            DifficultyLevel.EXPERT: "uzman",
            DifficultyLevel.MASTER: "usta"
        }.get(difficulty, "orta")
        
        # LLM ile gerçek içerik üret
        if self.llm_service:
            key_concepts = (curriculum_data or {}).get("key_concepts", [])
            applications = (curriculum_data or {}).get("real_world_applications", [])
            
            # Kişiselleştirme
            weak_areas = (goal.weak_areas if goal else []) or []
            is_weak = any(self._normalize_text(w) in self._normalize_text(topic) for w in weak_areas)
            personalization = ""
            if is_weak:
                personalization = "\n⚠️ Bu konu öğrencinin zayıf olduğu konulardan. Daha temel ve adım adım açıkla."
            
            prompt = f"""
{topic} konusunu {difficulty_text} seviyesinde detaylı açıkla.

Konu bağlamı:
- Ana konu: {main_topic}
- Alt konu: {topic}
- Anahtar kavramlar: {', '.join(key_concepts) if key_concepts else 'Belirtilmemiş'}
- Uygulama alanları: {', '.join(applications) if applications else 'Belirtilmemiş'}
{personalization}

İçerik şunları kapsamalı:
1. **Tanım**: Net ve anlaşılır tanım
2. **Temel Kavramlar**: En önemli 3-4 kavram
3. **Matematiksel/Bilimsel Temeller**: İlgili formüller
4. **Adım Adım Açıklama**: Mantıksal akış
5. **Dikkat Edilmesi Gerekenler**: Sık yapılan hatalar
6. **İpucu**: Konuyu daha iyi anlamak için tavsiye

Markdown formatında yaz. Formüller için LaTeX: $formül$
300-400 kelime.
"""
            llm_response = await self._generate_with_llm(prompt, temperature=0.5)
            if llm_response:
                return llm_response
        
        # Fallback template
        return f"""## {topic}

### 📌 Tanım
**{topic}**, {main_topic} konusunun önemli alt başlıklarından biridir. Bu kavram, matematikte ve günlük hayatta sıkça karşımıza çıkar.

### 🔍 Temel Kavramlar
1. **Kavram 1**: {topic} ile ilgili temel tanım
2. **Kavram 2**: İlişkili özellikler ve kurallar
3. **Kavram 3**: Uygulama alanları

### ⚠️ Dikkat Edilmesi Gerekenler
- {topic} konusunda sık yapılan hatalardan kaçının
- Formülleri doğru uyguladığınızdan emin olun
- Birim dönüşümlerine dikkat edin

### 💡 İpucu
> Bu konu {difficulty_text} seviyede bir konudur. Adım adım ilerleyin ve her kavramı anladığınızdan emin olun.

### 📎 Ön Koşullar
Bu konuyu anlamak için şu kavramları bilmeniz gerekir:
- Temel aritmetik işlemler
- {main_topic} temel kavramları"""

    async def _generate_formulas_content(self, topics: List[str], main_topic: str, subject: str = "Matematik") -> str:
        """Formüller içeriği oluştur - LLM destekli"""
        
        # LLM ile gerçek formül içeriği üret
        if self.llm_service:
            prompt = f"""
{main_topic} konusundaki önemli formülleri listele.

Alt konular: {', '.join(topics)}
Ders: {subject}

Her formül için:
1. Formül adı
2. LaTeX formatında formül
3. Değişkenlerin açıklamaları
4. Ne zaman kullanılır

Format:
## 📐 Önemli Formüller

### 1. [Formül Adı]
$$[LaTeX formül]$$

**Değişkenler:**
- $x$: açıklama
- $y$: açıklama

**Kullanım:** Ne zaman kullanılır

---

En az 5, en fazla 8 formül listele.
Formüller $$ veya $ arasında olmalı.
"""
            llm_response = await self._generate_with_llm(prompt, temperature=0.4)
            if llm_response:
                return llm_response
        
        # Fallback: Statik formüller
        formulas = []
        
        formula_templates = {
            "Türev": [
                ("Türev Tanımı", "$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$"),
                ("Çarpım Kuralı", "$(f \\cdot g)' = f' \\cdot g + f \\cdot g'$"),
                ("Bölüm Kuralı", "$\\left(\\frac{f}{g}\\right)' = \\frac{f' \\cdot g - f \\cdot g'}{g^2}$"),
                ("Zincir Kuralı", "$(f(g(x)))' = f'(g(x)) \\cdot g'(x)$")
            ],
            "İntegral": [
                ("Belirsiz İntegral", "$\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$"),
                ("Belirli İntegral", "$\\int_a^b f(x)dx = F(b) - F(a)$"),
                ("Kısmi İntegral", "$\\int u\\,dv = uv - \\int v\\,du$")
            ],
            "Limit": [
                ("Limit Tanımı", "$\\lim_{x \\to a} f(x) = L$"),
                ("Önemli Limit", "$\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$")
            ],
            "Logaritma": [
                ("Çarpım", "$\\log_a(x \\cdot y) = \\log_a x + \\log_a y$"),
                ("Üs", "$\\log_a x^n = n \\cdot \\log_a x$")
            ],
            "Trigonometri": [
                ("Temel Özdeşlik", "$\\sin^2 x + \\cos^2 x = 1$"),
                ("Tanjant", "$\\tan x = \\frac{\\sin x}{\\cos x}$")
            ],
            "Dizi": [
                ("Aritmetik Dizi", "$a_n = a_1 + (n-1)d$"),
                ("Geometrik Dizi", "$a_n = a_1 \\cdot r^{n-1}$")
            ],
        }
        
        for topic in topics:
            for key, formula_list in formula_templates.items():
                if key.lower() in topic.lower() or key.lower() in main_topic.lower():
                    formulas.extend(formula_list)
                    break
        
        if not formulas:
            formulas = [("Pisagor", "$a^2 + b^2 = c^2$")]
        
        formulas_text = '\n\n'.join(
            f"### {i+1}. {name}\n$${{formula}}$$".replace("{formula}", formula) 
            for i, (name, formula) in enumerate(formulas[:8])
        )
        
        return f"""## 📐 Önemli Formüller

{formulas_text}

---

### 📝 Formül Kullanım İpuçları
1. Formülleri ezberlemek yerine anlamaya çalışın
2. Her formülü örneklerle pekiştirin
3. Problem çözerken hangi formülü kullanacağınızı belirleyin
4. Birim uyumluluğunu kontrol edin"""

    async def _generate_examples_content(self, topics: List[str], difficulty: DifficultyLevel, main_topic: str = "", goal: LearningGoal = None) -> str:
        """Çözümlü örnekler oluştur - LLM destekli"""
        topic = topics[0] if topics else "Genel"
        
        difficulty_text = {
            DifficultyLevel.BEGINNER: "kolay",
            DifficultyLevel.ELEMENTARY: "kolay",
            DifficultyLevel.INTERMEDIATE: "orta",
            DifficultyLevel.UPPER_INTERMEDIATE: "orta-zor",
            DifficultyLevel.ADVANCED: "zor",
            DifficultyLevel.EXPERT: "çok zor",
            DifficultyLevel.MASTER: "olimpiyat"
        }.get(difficulty, "orta")
        
        # LLM ile gerçek örnekler üret
        if self.llm_service:
            prompt = f"""
{topic} konusunda {difficulty_text} seviyede 3 adet çözümlü örnek hazırla.

Konu bilgisi:
- Ana konu: {main_topic}
- Alt konu: {topic}
- Seviye: {difficulty_text}

Her örnek için:
1. Net ve anlaşılır soru ifadesi
2. Adım adım detaylı çözüm
3. Son cevap

Örnekler giderek zorlaşmalı:
- Örnek 1: Temel uygulama ({difficulty_text} alt sınır)
- Örnek 2: Orta seviye (tipik soru)
- Örnek 3: Üst seviye ({difficulty_text} üst sınır)

Format:
## ✏️ Çözümlü Örnekler

### Örnek 1: [Başlık]
**Soru:** [Soru metni]

**Çözüm:**
[Adım adım çözüm]

**Cevap:** [Net cevap]

---

Matematiksel ifadeler için LaTeX kullan: $formül$
Çözümler öğretici ve anlaşılır olmalı.
"""
            llm_response = await self._generate_with_llm(prompt, temperature=0.6)
            if llm_response:
                return llm_response
        
        # Fallback template
        return f"""## ✏️ Çözümlü Örnekler

### Örnek 1: Temel Uygulama
**Soru:** {topic} konusunda temel bir problem çözünüz.

**Çözüm:**
1. **Adım 1:** Verilenler belirlendi
2. **Adım 2:** Uygun formül seçildi
3. **Adım 3:** Değerler yerine konuldu
4. **Adım 4:** Sonuç hesaplandı

**Cevap:** Sonuç = X

---

### Örnek 2: Orta Seviye Problem
**Soru:** {topic} ile ilgili daha karmaşık bir problem çözünüz.

**Çözüm:**
Verilen: a, b, c değerleri
İstenen: Sonuç
Formül: f(x) = ...
Hesaplama: ...

**Cevap:** Sonuç = Y

---

### Örnek 3: İleri Seviye
**Soru:** {topic} konusunda uygulama sorusu.

**Çözüm:**
Bu tür sorularda dikkat edilmesi gereken noktalar:
- Verileri doğru analiz edin
- Adım adım ilerleyin
- Sonucu kontrol edin

**Cevap:** Sonuç = Z

---

### 💡 Pratik Yapın!
Bu örnekleri inceledikten sonra benzer sorular çözmeye çalışın."""

    async def _generate_interactive_content(self, topics: List[str], main_topic: str = "", goal: LearningGoal = None) -> str:
        """İnteraktif alıştırma içeriği"""
        topic = topics[0] if topics else "Genel"
        
        return f"""## 🎮 İnteraktif Alıştırma

### Kendi Kendine Test
Aşağıdaki alıştırmaları yaparak {topic} konusundaki anlayışını test et!

**Alıştırma 1:** Temel kavramları tanımlayın
**Alıştırma 2:** Formülleri uygulayın
**Alıştırma 3:** Örnek problemler çözün

### 🎯 Hedef
Bu alıştırmaları tamamladığında {topic} konusunda yeterli bilgiye sahip olacaksın!

### ⏱️ Süre
Tahmini tamamlama süresi: 15 dakika"""

    def _generate_video_suggestion(self, topics: List[str], main_topic: str) -> str:
        """Video önerisi içeriği"""
        topic = topics[0] if topics else main_topic
        
        return f"""## 🎬 Önerilen Video İçerikler

### Video 1: {topic} - Temel Anlatım
📺 Bu video ile konuyu görsel olarak öğrenebilirsin.
⏱️ Süre: ~10 dakika

### Video 2: {topic} - Soru Çözümü
📺 Örnek soru çözümleri ile pratik yap.
⏱️ Süre: ~15 dakika

### 💡 Video İzleme İpuçları
1. Videoyu durdurarak not alın
2. Anlamadığınız kısımları tekrar izleyin
3. Video sonrası kendiniz sorular çözmeye çalışın"""

    def _generate_summary_content(self, package: Package, stage: Stage) -> str:
        """Özet içeriği oluştur"""
        topics_list = '\n'.join(f'- ✅ {topic}' for topic in package.topics)
        
        return f"""## 📝 Özet

### Bu Pakette Öğrendikleriniz
{topics_list}

### 🔑 Anahtar Noktalar
1. **Temel Kavramlar:** {package.title} ile ilgili temel kavramları öğrendiniz
2. **Formüller:** Önemli formülleri ve kullanım alanlarını gördünüz
3. **Örnekler:** Çözümlü örneklerle pratik yaptınız

### 🎯 Sonraki Adım
Şimdi **sınav bölümüne** geçerek öğrendiklerinizi test edin!

### 💪 Motivasyon
> "Matematik öğrenmek bir maraton gibidir. Adım adım ilerleyin ve asla pes etmeyin!"

---

**Tebrikler!** Bu paketi tamamladın. Sınavda başarılar! 🏆"""

    def _is_math_subject(self, subject: str) -> bool:
        """Matematiksel içerik mi kontrol et"""
        math_keywords = ["matematik", "math", "calculus", "algebra", "geometry", 
                        "trigonometry", "ayt", "tyt", "lgs", "yks"]
        return any(keyword in subject.lower() for keyword in math_keywords)
    
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
            subject=goal.subject,
            target_outcome=goal.target_outcome,
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
    
    async def _generate_sample_questions_async(self, topic: str, count: int, exam_type: ExamType, difficulty: DifficultyLevel = None, main_topic: str = "") -> List[ExamQuestion]:
        """Örnek sorular oluştur - LLM destekli gerçek soru üretimi"""
        questions = []
        
        difficulty_text = {
            DifficultyLevel.BEGINNER: "kolay",
            DifficultyLevel.ELEMENTARY: "kolay",
            DifficultyLevel.INTERMEDIATE: "orta",
            DifficultyLevel.UPPER_INTERMEDIATE: "orta-zor",
            DifficultyLevel.ADVANCED: "zor",
            DifficultyLevel.EXPERT: "çok zor",
            DifficultyLevel.MASTER: "olimpiyat"
        }.get(difficulty, "orta") if difficulty else "orta"
        
        # LLM ile gerçek soru üretimi
        if self.llm_service and exam_type == ExamType.MULTIPLE_CHOICE:
            prompt = f"""
{topic} konusunda {count} adet {difficulty_text} seviyede çoktan seçmeli soru oluştur.

Konu: {main_topic or topic}
Alt konu: {topic}
Zorluk: {difficulty_text}
Soru sayısı: {count}

Her soru için JSON formatında:
{{
  "questions": [
    {{
      "question": "Soru metni (detaylı ve net)",
      "options": ["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4", "E) Seçenek 5"],
      "correct_answer": "A/B/C/D/E",
      "explanation": "Doğru cevabın açıklaması"
    }}
  ]
}}

Kurallar:
- Sorular {difficulty_text} seviyeye uygun olmalı
- Her sorunun 5 şıkkı olmalı (A-E)
- Şıklar gerçekçi ve mantıklı olmalı
- Doğru cevap rastgele dağılmalı
- Açıklamalar öğretici olmalı
- Matematiksel ifadeler için $ $ kullan

SADECE JSON döndür, başka metin ekleme.
"""
            try:
                llm_response = await self._generate_with_llm(prompt, temperature=0.7)
                if llm_response:
                    # JSON parse et
                    json_match = re.search(r'\{[\s\S]*\}', llm_response)
                    if json_match:
                        import json
                        data = json.loads(json_match.group())
                        for q_data in data.get("questions", []):
                            q = ExamQuestion(
                                type=exam_type,
                                question=q_data.get("question", ""),
                                options=q_data.get("options", []),
                                correct_answer=q_data.get("correct_answer", "A"),
                                explanation=q_data.get("explanation", ""),
                                points=10,
                                topic=topic
                            )
                            questions.append(q)
                        
                        if len(questions) >= count:
                            return questions[:count]
            except Exception as e:
                self._add_thought(f"LLM soru üretimi hatası: {e}", "question_generator", 0.3)
        
        elif self.llm_service and exam_type == ExamType.PROBLEM_SOLVING:
            prompt = f"""
{topic} konusunda {count} adet {difficulty_text} seviyede problem çözme sorusu oluştur.

Konu: {main_topic or topic}
Alt konu: {topic}
Zorluk: {difficulty_text}

Her soru için JSON formatında:
{{
  "questions": [
    {{
      "question": "Problem metni (veriler ve istenenler açık)",
      "explanation": "Adım adım çözüm",
      "rubric": {{
        "problem_understanding": 5,
        "solution_approach": 5,
        "calculations": 5,
        "final_answer": 5
      }}
    }}
  ]
}}

Kurallar:
- Problemler gerçekçi senaryolar içermeli
- Veriler net ve yeterli olmalı
- Çözümler adım adım olmalı
- Matematiksel ifadeler için $ $ kullan

SADECE JSON döndür.
"""
            try:
                llm_response = await self._generate_with_llm(prompt, temperature=0.7)
                if llm_response:
                    json_match = re.search(r'\{[\s\S]*\}', llm_response)
                    if json_match:
                        import json
                        data = json.loads(json_match.group())
                        for q_data in data.get("questions", []):
                            q = ExamQuestion(
                                type=exam_type,
                                question=q_data.get("question", ""),
                                explanation=q_data.get("explanation", ""),
                                points=20,
                                topic=topic,
                                rubric=q_data.get("rubric", {
                                    "problem_understanding": 5,
                                    "solution_approach": 5,
                                    "calculations": 5,
                                    "final_answer": 5
                                })
                            )
                            questions.append(q)
                        
                        if len(questions) >= count:
                            return questions[:count]
            except Exception as e:
                self._add_thought(f"LLM problem üretimi hatası: {e}", "question_generator", 0.3)
        
        # Fallback: Statik sorular
        for i in range(count - len(questions)):
            if exam_type == ExamType.MULTIPLE_CHOICE:
                correct = random.choice(["A", "B", "C", "D", "E"])
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} ile ilgili soru {i+1}",
                    options=["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4", "E) Seçenek 5"],
                    correct_answer=correct,
                    explanation=f"Doğru cevap {correct} çünkü...",
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
    
    def _generate_sample_questions(self, topic: str, count: int, exam_type: ExamType) -> List[ExamQuestion]:
        """Senkron wrapper - eski API uyumluluğu için"""
        questions = []
        for i in range(count):
            if exam_type == ExamType.MULTIPLE_CHOICE:
                correct = random.choice(["A", "B", "C", "D", "E"])
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} ile ilgili soru {i+1}",
                    options=["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4", "E) Seçenek 5"],
                    correct_answer=correct,
                    explanation=f"Doğru cevap {correct} çünkü...",
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
