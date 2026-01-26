"""
👨‍🏫 Pedagogy Agent - Eğitim Bilimi Uzmanı

Sorumluluklar:
- Öğrenme hedefi analizi
- Bloom taksonomisi uygulaması
- Pedagojik sıralama
- Öğrenme stili adaptasyonu
- Ön koşul belirleme
"""

import asyncio
from typing import Dict, Any, AsyncGenerator, List

from .base_agent import BaseCurriculumAgent, AgentThought, ThinkingPhase


class PedagogyAgent(BaseCurriculumAgent):
    """
    Pedagoji Uzmanı Agent
    
    Eğitim bilimi ve öğrenme teorileri uzmanı.
    Bloom taksonomisi, öğrenme stilleri ve pedagojik sıralama konularında uzman.
    """
    
    # Bloom Taksonomisi Seviyeleri
    BLOOM_LEVELS = [
        ("remember", "Hatırlama", "Temel bilgileri hatırlama"),
        ("understand", "Anlama", "Kavramları açıklayabilme"),
        ("apply", "Uygulama", "Bilgiyi yeni durumlarda kullanma"),
        ("analyze", "Analiz", "Parçalara ayırma, ilişkileri görme"),
        ("evaluate", "Değerlendirme", "Yargılama, eleştirme"),
        ("create", "Yaratma", "Yeni ürünler oluşturma")
    ]
    
    # Öğrenme Stilleri
    LEARNING_STYLES = {
        "visual": {
            "name": "Görsel",
            "preferences": ["diagram", "infographic", "video", "mindmap"],
            "strategies": ["Görsel materyaller kullan", "Renk kodlaması yap", "Akış şemaları oluştur"]
        },
        "auditory": {
            "name": "İşitsel",
            "preferences": ["video", "podcast", "discussion"],
            "strategies": ["Sesli anlatım ekle", "Tartışma soruları koy", "Özetleri seslendir"]
        },
        "kinesthetic": {
            "name": "Kinestetik",
            "preferences": ["interactive", "simulation", "practice"],
            "strategies": ["Hands-on aktiviteler", "Simülasyonlar", "Pratik egzersizler"]
        },
        "reading": {
            "name": "Okuma/Yazma",
            "preferences": ["text", "notes", "summary"],
            "strategies": ["Detaylı notlar", "Özet çıkarma", "Yazılı sorular"]
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Pedagoji Uzmanı",
            role="Eğitim Bilimi Uzmanı",
            specialty="Bloom taksonomisi, öğrenme stilleri, pedagojik tasarım",
            model_preference="openai/gpt-4o",
            thinking_style="methodical and evidence-based"
        )
        self.icon = "👨‍🏫"
    
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Pedagojik analiz yap
        
        Steps:
        1. Hedef Analizi
        2. Bloom Seviyesi Belirleme
        3. Ön Koşul Analizi
        4. Pedagojik Sıralama
        5. Öğrenme Stili Adaptasyonu
        """
        goal = context.get("goal")
        
        # Intro thought
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="baslangic",
            phase=ThinkingPhase.ANALYZING,
            thinking="🎯 Pedagojik analiz başlıyor...",
            reasoning="Öğrenme hedefini, seviyeyi ve stili değerlendireceğim.",
            is_streaming=True
        )
        
        await asyncio.sleep(0.5)
        
        # ===== STEP 1: Hedef Analizi =====
        async for thought in self.think(
            prompt=self._build_goal_analysis_prompt(goal),
            step="hedef_analizi",
            context={"goal": goal.to_dict() if hasattr(goal, 'to_dict') else goal}
        ):
            yield thought
        
        # ===== STEP 2: Bloom Seviyesi =====
        async for thought in self.think(
            prompt=self._build_bloom_analysis_prompt(goal),
            step="bloom_seviyesi",
            context=context
        ):
            yield thought
        
        # ===== STEP 3: Ön Koşullar =====
        async for thought in self.think(
            prompt=self._build_prerequisites_prompt(goal),
            step="on_kosullar",
            context=context
        ):
            yield thought
        
        # ===== STEP 4: Pedagojik Sıralama =====
        async for thought in self.think(
            prompt=self._build_sequencing_prompt(goal),
            step="pedagojik_siralama",
            context=context
        ):
            yield thought
        
        # ===== STEP 5: Öğrenme Stili =====
        async for thought in self.think(
            prompt=self._build_learning_style_prompt(goal),
            step="ogrenme_stili",
            context=context
        ):
            yield thought
        
        # Final summary
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ozet",
            phase=ThinkingPhase.CONCLUDING,
            thinking="✅ Pedagojik analiz tamamlandı",
            reasoning="Tüm pedagojik gereksinimler belirlendi.",
            conclusion=self._generate_summary(goal),
            confidence=0.9,
            is_complete=True
        )
    
    def _build_goal_analysis_prompt(self, goal) -> str:
        """Hedef analizi promptu"""
        if hasattr(goal, 'title'):
            return f"""Öğrenme hedefini analiz et:

Hedef: {goal.title}
Konu: {goal.subject}
Amaç: {goal.target_outcome}
Açıklama: {goal.description}

Analiz et:
1. Bu hedef SMART kriterlerine uygun mu?
2. Öğrencinin mevcut seviyesi ne olmalı?
3. Hedefin ulaşılabilirliği (timeline: {goal.deadline})
4. Motivasyon faktörleri: {goal.motivation}

JSON formatında yanıt ver."""
        return "Genel öğrenme hedefi analizi yap."
    
    def _build_bloom_analysis_prompt(self, goal) -> str:
        """Bloom taksonomisi promptu"""
        if hasattr(goal, 'subject'):
            return f"""Bloom Taksonomisi analizi yap:

Konu: {goal.subject}
Hedef: {goal.target_outcome}

Her alt konu için hedef Bloom seviyesini belirle:
1. Hatırlama - Temel tanımlar
2. Anlama - Kavramları açıklama
3. Uygulama - Problem çözme
4. Analiz - Karşılaştırma, ilişkilendirme
5. Değerlendirme - Kritik düşünme
6. Yaratma - Yeni ürünler oluşturma

JSON formatında konu-seviye eşleştirmesi döndür."""
        return "Bloom taksonomisi seviyelerini belirle."
    
    def _build_prerequisites_prompt(self, goal) -> str:
        """Ön koşul analizi promptu"""
        if hasattr(goal, 'prior_knowledge'):
            return f"""Ön koşul analizi yap:

Konu: {goal.subject}
Mevcut Bilgi: {goal.prior_knowledge}
Zayıf Alanlar: {goal.weak_areas}

Belirle:
1. Bu konuyu öğrenmek için hangi ön bilgiler gerekli?
2. Öğrencinin eksik olabileceği ön koşullar
3. Tavsiye edilen başlangıç noktası
4. Varsa atlayılabilecek konular

JSON formatında döndür."""
        return "Ön koşulları belirle."
    
    def _build_sequencing_prompt(self, goal) -> str:
        """Pedagojik sıralama promptu"""
        if hasattr(goal, 'topics_to_include'):
            topics = goal.topics_to_include or []
            return f"""Pedagojik sıralama yap:

Konu: {goal.subject}
Alt Konular: {', '.join(topics) if topics else 'Belirtilmemiş'}
Hariç Tutulanlar: {goal.topics_to_exclude}

Konuları pedagojik olarak doğru sıraya koy:
- Basittten karmaşığa
- Somuttan soyuta
- Bilinen-bilinmeyene

Her konu için:
- Önerilen sıra
- Tahmini süre
- Bağlantılı konular

JSON formatında döndür."""
        return "Konuları pedagojik olarak sırala."
    
    def _build_learning_style_prompt(self, goal) -> str:
        """Öğrenme stili promptu"""
        if hasattr(goal, 'learning_style'):
            return f"""Öğrenme stili adaptasyonu:

Tercih Edilen Stil: {goal.learning_style or 'Belirtilmemiş'}
Günlük Çalışma: {goal.daily_hours} saat
İçerik Tercihleri: {goal.content_preferences}

Bu profile göre öner:
1. En uygun içerik türleri
2. Paket süreleri
3. Pratik/teori oranı
4. Değerlendirme yöntemleri

JSON formatında döndür."""
        return "Öğrenme stiline göre adapte et."
    
    def _generate_summary(self, goal) -> str:
        """Özet oluştur"""
        if hasattr(goal, 'subject'):
            return f"""Pedagojik Analiz Özeti:
• Konu: {goal.subject}
• Hedef Bloom Seviyesi: Uygulama-Analiz
• Önerilen Yaklaşım: Spiral öğrenme
• Tahmini Süre: {goal.daily_hours * 30} saat"""
        return "Pedagojik analiz tamamlandı."
    
    def analyze_topic_difficulty(self, topic: str, subject: str) -> Dict[str, Any]:
        """Konu zorluğunu analiz et"""
        # Heuristik zorluk tahmini
        difficulty_keywords = {
            "advanced": ["ileri", "karmaşık", "entegral", "diferansiyel", "analiz"],
            "intermediate": ["orta", "uygulama", "problem", "fonksiyon"],
            "beginner": ["temel", "giriş", "tanım", "kavram"]
        }
        
        topic_lower = topic.lower()
        
        for level, keywords in difficulty_keywords.items():
            if any(kw in topic_lower for kw in keywords):
                return {
                    "topic": topic,
                    "difficulty": level,
                    "bloom_level": "apply" if level == "intermediate" else ("analyze" if level == "advanced" else "understand"),
                    "estimated_hours": 4 if level == "advanced" else (2 if level == "intermediate" else 1)
                }
        
        return {
            "topic": topic,
            "difficulty": "intermediate",
            "bloom_level": "apply",
            "estimated_hours": 2
        }
    
    def recommend_content_types(self, learning_style: str) -> List[str]:
        """Öğrenme stiline göre içerik türleri öner"""
        style = self.LEARNING_STYLES.get(learning_style, self.LEARNING_STYLES["visual"])
        return style["preferences"]
