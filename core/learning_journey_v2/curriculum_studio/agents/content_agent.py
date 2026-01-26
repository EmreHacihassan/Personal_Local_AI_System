"""
📝 Content Agent - İçerik Tasarımcısı

Sorumluluklar:
- İçerik yapısı tasarımı
- Multimedya planlaması
- Paket içerik dağılımı
- AI Video entegrasyonu planı
- İnteraktif içerik tasarımı
"""

import asyncio
from typing import Dict, Any, AsyncGenerator, List

from .base_agent import BaseCurriculumAgent, AgentThought, ThinkingPhase


class ContentAgent(BaseCurriculumAgent):
    """
    İçerik Tasarımcısı Agent
    
    Zengin, multimedya içerik planlaması yapan agent.
    Metin, video, görsel, interaktif içerik dengesi kurar.
    """
    
    # İçerik türleri ve özellikleri
    CONTENT_TYPES = {
        "text": {
            "name": "Yazılı Anlatım",
            "icon": "📖",
            "engagement": 0.6,
            "retention": 0.3,
            "production_effort": "low"
        },
        "video": {
            "name": "Video Anlatım",
            "icon": "🎬",
            "engagement": 0.9,
            "retention": 0.6,
            "production_effort": "high"
        },
        "infographic": {
            "name": "İnfografik",
            "icon": "📊",
            "engagement": 0.8,
            "retention": 0.5,
            "production_effort": "medium"
        },
        "interactive": {
            "name": "İnteraktif",
            "icon": "🎮",
            "engagement": 0.95,
            "retention": 0.7,
            "production_effort": "high"
        },
        "flashcard": {
            "name": "Flashcard",
            "icon": "🃏",
            "engagement": 0.7,
            "retention": 0.8,
            "production_effort": "low"
        },
        "mindmap": {
            "name": "Zihin Haritası",
            "icon": "🧠",
            "engagement": 0.75,
            "retention": 0.6,
            "production_effort": "medium"
        },
        "example": {
            "name": "Çözümlü Örnek",
            "icon": "✏️",
            "engagement": 0.85,
            "retention": 0.65,
            "production_effort": "medium"
        },
        "summary": {
            "name": "Özet",
            "icon": "📋",
            "engagement": 0.5,
            "retention": 0.7,
            "production_effort": "low"
        }
    }
    
    # Paket türlerine göre ideal içerik dağılımı
    PACKAGE_CONTENT_MIX = {
        "intro": {
            "text": 0.4,
            "video": 0.3,
            "infographic": 0.2,
            "mindmap": 0.1
        },
        "learning": {
            "text": 0.3,
            "video": 0.25,
            "example": 0.25,
            "infographic": 0.1,
            "interactive": 0.1
        },
        "practice": {
            "example": 0.4,
            "interactive": 0.3,
            "flashcard": 0.2,
            "summary": 0.1
        },
        "review": {
            "flashcard": 0.3,
            "summary": 0.3,
            "mindmap": 0.2,
            "example": 0.2
        },
        "closure": {
            "summary": 0.3,
            "mindmap": 0.2,
            "example": 0.3,
            "text": 0.2
        }
    }
    
    def __init__(self):
        super().__init__(
            name="İçerik Tasarımcısı",
            role="Multimedya İçerik Uzmanı",
            specialty="İçerik tasarımı, multimedya planlama, engagement optimizasyonu",
            model_preference="ollama/qwen3:8b",
            thinking_style="creative and user-centric"
        )
        self.icon = "📝"
    
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        İçerik planlaması yap
        
        Steps:
        1. İçerik Stratejisi
        2. Paket İçerik Dağılımı
        3. Multimedya Planı
        4. AI Video Planı
        5. İnteraktif İçerik Tasarımı
        """
        goal = context.get("goal")
        pedagogy_result = context.get("pedagogy_result", {})
        
        # Intro
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="baslangic",
            phase=ThinkingPhase.ANALYZING,
            thinking="📝 İçerik tasarımı başlıyor...",
            reasoning="Öğrenme stiline ve konuya uygun içerik planı oluşturacağım.",
            is_streaming=True
        )
        
        await asyncio.sleep(0.5)
        
        # ===== STEP 1: İçerik Stratejisi =====
        async for thought in self.think(
            prompt=self._build_strategy_prompt(goal, pedagogy_result),
            step="icerik_stratejisi",
            context=context
        ):
            yield thought
        
        # ===== STEP 2: Paket İçerik Dağılımı =====
        async for thought in self._plan_package_content(goal, context):
            yield thought
        
        # ===== STEP 3: Multimedya Planı =====
        async for thought in self._plan_multimedia(goal, context):
            yield thought
        
        # ===== STEP 4: AI Video Planı =====
        async for thought in self._plan_ai_videos(goal, context):
            yield thought
        
        # ===== STEP 5: İnteraktif İçerik =====
        async for thought in self._plan_interactive_content(goal, context):
            yield thought
        
        # Final
        content_plan = self._compile_content_plan(context)
        context["content_plan"] = content_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ozet",
            phase=ThinkingPhase.CONCLUDING,
            thinking="✅ İçerik planı tamamlandı",
            conclusion=f"Toplam {content_plan.get('total_blocks', 0)} içerik bloğu planlandı.",
            evidence=[
                f"Metin: {content_plan.get('text_count', 0)}",
                f"Video: {content_plan.get('video_count', 0)}",
                f"İnteraktif: {content_plan.get('interactive_count', 0)}"
            ],
            confidence=0.88,
            is_complete=True
        )
    
    def _build_strategy_prompt(self, goal, pedagogy_result) -> str:
        """İçerik stratejisi promptu"""
        learning_style = goal.learning_style if hasattr(goal, 'learning_style') else "visual"
        
        return f"""İçerik stratejisi oluştur:

Konu: {goal.subject if hasattr(goal, 'subject') else 'Genel'}
Öğrenme Stili: {learning_style}
Günlük Çalışma: {goal.daily_hours if hasattr(goal, 'daily_hours') else 2} saat

Belirle:
1. Ana içerik türü (text, video, interactive)
2. Destekleyici içerik türleri
3. Her paket için tahmini içerik sayısı
4. Engagement stratejisi
5. Retention (hatırlama) optimizasyonu

JSON formatında döndür."""
    
    async def _plan_package_content(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Paket içerik dağılımı"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="paket_dagilimi",
            phase=ThinkingPhase.REASONING,
            thinking="📦 Paket içerik dağılımı planlanıyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.5)
        
        # Her paket türü için içerik planı
        package_plans = {}
        for pkg_type, content_mix in self.PACKAGE_CONTENT_MIX.items():
            package_plans[pkg_type] = {
                "content_mix": content_mix,
                "recommended_blocks": self._calculate_block_count(pkg_type, goal),
                "estimated_duration_minutes": self._estimate_duration(pkg_type, goal)
            }
        
        context["package_content_plans"] = package_plans
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="paket_dagilimi",
            phase=ThinkingPhase.CONCLUDING,
            thinking="📦 Paket içerik dağılımı tamamlandı",
            reasoning="Her paket türü için optimal içerik karışımı belirlendi.",
            evidence=[f"{k}: {v['recommended_blocks']} blok" for k, v in list(package_plans.items())[:3]],
            confidence=0.85,
            is_complete=True
        )
    
    def _calculate_block_count(self, pkg_type: str, goal) -> int:
        """Paket için içerik bloğu sayısı hesapla"""
        base_counts = {
            "intro": 5,
            "learning": 8,
            "practice": 6,
            "review": 4,
            "closure": 6
        }
        return base_counts.get(pkg_type, 5)
    
    def _estimate_duration(self, pkg_type: str, goal) -> int:
        """Paket tahmini süre (dakika)"""
        durations = {
            "intro": 15,
            "learning": 45,
            "practice": 30,
            "review": 20,
            "closure": 40
        }
        return durations.get(pkg_type, 30)
    
    async def _plan_multimedia(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Multimedya planı"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="multimedia_plani",
            phase=ThinkingPhase.ANALYZING,
            thinking="🎨 Multimedya içerik planlanıyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.2)
        
        # Multimedya planı
        multimedia_plan = {
            "diagrams": [],
            "infographics": [],
            "animations": [],
            "images": []
        }
        
        subject = goal.subject if hasattr(goal, 'subject') else "Genel"
        
        # Konu bazlı multimedya önerileri
        if "matematik" in subject.lower():
            multimedia_plan["diagrams"].extend([
                "Fonksiyon grafikleri",
                "Geometrik şekiller",
                "Koordinat sistemi gösterimleri"
            ])
            multimedia_plan["animations"].extend([
                "Limit animasyonu",
                "Türev geometrik yorumu"
            ])
        elif "fizik" in subject.lower():
            multimedia_plan["diagrams"].extend([
                "Kuvvet diyagramları",
                "Hareket grafikleri"
            ])
            multimedia_plan["animations"].extend([
                "Dalga hareketi simülasyonu",
                "Çarpışma animasyonu"
            ])
        
        context["multimedia_plan"] = multimedia_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="multimedia_plani",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🎨 Multimedya planı hazır",
            evidence=[
                f"Diyagramlar: {len(multimedia_plan['diagrams'])}",
                f"Animasyonlar: {len(multimedia_plan['animations'])}"
            ],
            confidence=0.82,
            is_complete=True
        )
    
    async def _plan_ai_videos(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """AI Video planı"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ai_video_plani",
            phase=ThinkingPhase.ANALYZING,
            thinking="🎬 AI Video içerikler planlanıyor...",
            reasoning="HeyGen, D-ID veya Synthesia ile üretilebilecek videolar belirleniyor.",
            is_streaming=True
        )
        
        await asyncio.sleep(1.5)
        
        # AI Video planı
        ai_video_plan = {
            "videos": [],
            "platform_recommendation": "HeyGen",
            "avatar_style": "professional_teacher",
            "language": "tr"
        }
        
        subject = goal.subject if hasattr(goal, 'subject') else "Genel"
        topics = goal.topics_to_include if hasattr(goal, 'topics_to_include') and goal.topics_to_include else [subject]
        
        for topic in topics[:5]:
            ai_video_plan["videos"].append({
                "title": f"{topic} - Konu Anlatımı",
                "duration_seconds": 180,  # 3 dakika
                "script_outline": [
                    f"{topic} nedir?",
                    "Temel kavramlar",
                    "Örnek uygulama",
                    "Özet"
                ],
                "visual_elements": ["slides", "diagrams", "examples"],
                "priority": "high" if topic in (goal.focus_areas if hasattr(goal, 'focus_areas') else []) else "medium"
            })
        
        context["ai_video_plan"] = ai_video_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ai_video_plani",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🎬 AI Video planı hazır",
            conclusion=f"{len(ai_video_plan['videos'])} AI video planlandı",
            evidence=[v["title"] for v in ai_video_plan["videos"][:3]],
            confidence=0.85,
            is_complete=True
        )
    
    async def _plan_interactive_content(
        self, 
        goal, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """İnteraktif içerik planı"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="interaktif_icerik",
            phase=ThinkingPhase.REASONING,
            thinking="🎮 İnteraktif içerikler tasarlanıyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.0)
        
        interactive_plan = {
            "simulations": [],
            "quizzes": [],
            "drag_drop": [],
            "fill_blanks": []
        }
        
        subject = goal.subject if hasattr(goal, 'subject') else "Genel"
        
        # Simülasyon önerileri
        if "matematik" in subject.lower():
            interactive_plan["simulations"].extend([
                {"name": "Grafik Çizici", "type": "graph_plotter"},
                {"name": "Türev Hesaplayıcı", "type": "calculator"}
            ])
        elif "fizik" in subject.lower():
            interactive_plan["simulations"].extend([
                {"name": "Hareket Simülatörü", "type": "physics_sim"},
                {"name": "Elektrik Devresi", "type": "circuit_builder"}
            ])
        
        # Genel interaktif öğeler
        interactive_plan["quizzes"].append({"name": "Hızlı Kontrol", "questions": 5})
        interactive_plan["drag_drop"].append({"name": "Kavram Eşleştirme", "items": 8})
        
        context["interactive_plan"] = interactive_plan
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="interaktif_icerik",
            phase=ThinkingPhase.CONCLUDING,
            thinking="🎮 İnteraktif içerik planı hazır",
            evidence=[
                f"Simülasyonlar: {len(interactive_plan['simulations'])}",
                f"Quizler: {len(interactive_plan['quizzes'])}"
            ],
            confidence=0.8,
            is_complete=True
        )
    
    def _compile_content_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tüm içerik planını derle"""
        package_plans = context.get("package_content_plans", {})
        ai_videos = context.get("ai_video_plan", {}).get("videos", [])
        interactive = context.get("interactive_plan", {})
        multimedia = context.get("multimedia_plan", {})
        
        total_blocks = sum(p.get("recommended_blocks", 0) for p in package_plans.values())
        
        return {
            "total_blocks": total_blocks,
            "text_count": int(total_blocks * 0.35),
            "video_count": len(ai_videos) + int(total_blocks * 0.1),
            "interactive_count": len(interactive.get("simulations", [])) + len(interactive.get("quizzes", [])),
            "multimedia_count": len(multimedia.get("diagrams", [])) + len(multimedia.get("infographics", [])),
            "package_plans": package_plans,
            "ai_videos": ai_videos,
            "interactive": interactive,
            "multimedia": multimedia
        }
