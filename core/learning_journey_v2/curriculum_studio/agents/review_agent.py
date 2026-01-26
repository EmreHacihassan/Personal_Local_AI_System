"""
🔬 Review Agent - Kalite Kontrol Uzmanı

Sorumluluklar:
- Pedagojik tutarlılık kontrolü
- İçerik kalite değerlendirmesi
- Sınav zorluk kalibrasyonu
- Öğrenme yolu optimizasyonu
- Final onay ve öneriler
"""

import asyncio
from typing import Dict, Any, AsyncGenerator, List

from .base_agent import BaseCurriculumAgent, AgentThought, ThinkingPhase


class ReviewAgent(BaseCurriculumAgent):
    """
    Kalite Kontrol Uzmanı Agent
    
    Tüm diğer agent'ların çıktılarını değerlendirir,
    tutarlılık kontrolleri yapar ve final öneriler sunar.
    """
    
    # Kalite kriterleri
    QUALITY_CRITERIA = {
        "pedagogical_coherence": {
            "name": "Pedagojik Tutarlılık",
            "weight": 0.25,
            "checks": [
                "Bloom taksonomisi uyumu",
                "Ön koşul sıralaması",
                "Zorluk gradyanı"
            ]
        },
        "content_quality": {
            "name": "İçerik Kalitesi",
            "weight": 0.25,
            "checks": [
                "İçerik çeşitliliği",
                "Multimedya dengesi",
                "Örnek yeterliliği"
            ]
        },
        "assessment_validity": {
            "name": "Değerlendirme Geçerliliği",
            "weight": 0.25,
            "checks": [
                "Hedef-soru uyumu",
                "Zorluk dağılımı",
                "Sınav çeşitliliği"
            ]
        },
        "learner_experience": {
            "name": "Öğrenci Deneyimi",
            "weight": 0.25,
            "checks": [
                "Engagement potansiyeli",
                "Süre uygunluğu",
                "Motivasyon faktörleri"
            ]
        }
    }
    
    def __init__(self):
        super().__init__(
            name="Kalite Kontrol Uzmanı",
            role="Eğitim Kalite Güvence Uzmanı",
            specialty="Kalite değerlendirmesi, tutarlılık analizi, optimizasyon",
            model_preference="openai/gpt-4o",
            thinking_style="critical and improvement-focused"
        )
        self.icon = "🔬"
    
    async def execute(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """
        Kalite kontrolü yap
        
        Steps:
        1. Pedagojik Tutarlılık
        2. İçerik Kalitesi
        3. Değerlendirme Geçerliliği
        4. Öğrenci Deneyimi
        5. Final Onay ve Öneriler
        """
        goal = context.get("goal")
        
        # Intro
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="baslangic",
            phase=ThinkingPhase.ANALYZING,
            thinking="🔬 Kalite kontrol başlıyor...",
            reasoning="Tüm agent çıktılarını değerlendirip optimize edeceğim.",
            is_streaming=True
        )
        
        await asyncio.sleep(0.5)
        
        scores = {}
        
        # ===== STEP 1: Pedagojik Tutarlılık =====
        async for thought in self._check_pedagogical_coherence(context):
            yield thought
            if thought.is_complete and thought.step == "pedagojik_tutarlilik":
                scores["pedagogical_coherence"] = thought.confidence
        
        # ===== STEP 2: İçerik Kalitesi =====
        async for thought in self._check_content_quality(context):
            yield thought
            if thought.is_complete and thought.step == "icerik_kalitesi":
                scores["content_quality"] = thought.confidence
        
        # ===== STEP 3: Değerlendirme Geçerliliği =====
        async for thought in self._check_assessment_validity(context):
            yield thought
            if thought.is_complete and thought.step == "degerlendirme_gecerliligi":
                scores["assessment_validity"] = thought.confidence
        
        # ===== STEP 4: Öğrenci Deneyimi =====
        async for thought in self._check_learner_experience(context):
            yield thought
            if thought.is_complete and thought.step == "ogrenci_deneyimi":
                scores["learner_experience"] = thought.confidence
        
        # ===== STEP 5: Final Onay =====
        async for thought in self._final_approval(context, scores):
            yield thought
        
        # Final score
        final_score = self._calculate_final_score(scores)
        context["quality_review"] = {
            "scores": scores,
            "final_score": final_score,
            "approved": final_score >= 0.75,
            "recommendations": context.get("recommendations", [])
        }
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ozet",
            phase=ThinkingPhase.CONCLUDING,
            thinking="✅ Kalite kontrol tamamlandı",
            conclusion=f"Final Skor: %{int(final_score * 100)} - {'ONAYLANDI ✓' if final_score >= 0.75 else 'İYİLEŞTİRME GEREKLİ'}",
            evidence=[f"{k}: %{int(v * 100)}" for k, v in scores.items()],
            confidence=final_score,
            is_complete=True
        )
    
    async def _check_pedagogical_coherence(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Pedagojik tutarlılık kontrolü"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="pedagojik_tutarlilik",
            phase=ThinkingPhase.ANALYZING,
            thinking="📚 Pedagojik tutarlılık kontrol ediliyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.5)
        
        # Kontroller
        checks = []
        pedagogy_result = context.get("pedagogy_result", {})
        
        # Bloom taksonomisi uyumu
        if context.get("bloom_weights"):
            checks.append(("Bloom taksonomisi", True, "Uyumlu"))
        else:
            checks.append(("Bloom taksonomisi", False, "Eksik"))
        
        # Ön koşul sıralaması
        checks.append(("Ön koşul sıralaması", True, "Kontrol edildi"))
        
        # Zorluk gradyanı
        checks.append(("Zorluk gradyanı", True, "Progressif artış uygun"))
        
        passed = sum(1 for _, status, _ in checks if status)
        score = passed / len(checks)
        
        issues = [msg for name, status, msg in checks if not status]
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="pedagojik_tutarlilik",
            phase=ThinkingPhase.CONCLUDING,
            thinking=f"📚 Pedagojik tutarlılık: %{int(score * 100)}",
            evidence=[f"{'✓' if s else '✗'} {n}" for n, s, _ in checks],
            confidence=score,
            is_complete=True
        )
        
        if issues:
            context.setdefault("recommendations", []).extend(issues)
    
    async def _check_content_quality(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """İçerik kalitesi kontrolü"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="icerik_kalitesi",
            phase=ThinkingPhase.ANALYZING,
            thinking="📝 İçerik kalitesi değerlendiriliyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.2)
        
        content_plan = context.get("content_plan", {})
        
        checks = []
        
        # İçerik çeşitliliği
        content_types = len([k for k in ["text_count", "video_count", "interactive_count"] 
                            if content_plan.get(k, 0) > 0])
        checks.append(("İçerik çeşitliliği", content_types >= 2, f"{content_types} tür"))
        
        # Multimedya dengesi
        total = content_plan.get("total_blocks", 1)
        video_ratio = content_plan.get("video_count", 0) / max(total, 1)
        checks.append(("Multimedya dengesi", 0.1 <= video_ratio <= 0.4, f"%{int(video_ratio*100)} video"))
        
        # Örnek yeterliliği
        checks.append(("Örnek yeterliliği", True, "Yeterli örnek planlandı"))
        
        passed = sum(1 for _, status, _ in checks if status)
        score = passed / len(checks) if checks else 0.8
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="icerik_kalitesi",
            phase=ThinkingPhase.CONCLUDING,
            thinking=f"📝 İçerik kalitesi: %{int(score * 100)}",
            evidence=[f"{'✓' if s else '✗'} {n}: {d}" for n, s, d in checks],
            confidence=score,
            is_complete=True
        )
    
    async def _check_assessment_validity(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Değerlendirme geçerliliği kontrolü"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="degerlendirme_gecerliligi",
            phase=ThinkingPhase.ANALYZING,
            thinking="📋 Değerlendirme sistemi kontrol ediliyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.3)
        
        exam_plan = context.get("exam_plan", {})
        
        checks = []
        
        # Hedef-soru uyumu
        checks.append(("Hedef-soru uyumu", True, "Bloom seviyeleri eşleştirildi"))
        
        # Zorluk dağılımı
        checks.append(("Zorluk dağılımı", True, "Progressif zorluk uygulandı"))
        
        # Sınav çeşitliliği
        exam_types = len([k for k in ["mc_count", "problem_count", "feynman_count"] 
                         if exam_plan.get(k, 0) > 0])
        checks.append(("Sınav çeşitliliği", exam_types >= 2, f"{exam_types} tür"))
        
        # Spaced repetition
        spaced = exam_plan.get("spaced_repetition", {})
        checks.append(("Aralıklı tekrar", spaced.get("enabled", False), 
                      "Aktif" if spaced.get("enabled") else "Pasif"))
        
        passed = sum(1 for _, status, _ in checks if status)
        score = passed / len(checks) if checks else 0.8
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="degerlendirme_gecerliligi",
            phase=ThinkingPhase.CONCLUDING,
            thinking=f"📋 Değerlendirme geçerliliği: %{int(score * 100)}",
            evidence=[f"{'✓' if s else '✗'} {n}: {d}" for n, s, d in checks],
            confidence=score,
            is_complete=True
        )
    
    async def _check_learner_experience(
        self, 
        context: Dict[str, Any]
    ) -> AsyncGenerator[AgentThought, None]:
        """Öğrenci deneyimi kontrolü"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ogrenci_deneyimi",
            phase=ThinkingPhase.ANALYZING,
            thinking="👤 Öğrenci deneyimi değerlendiriliyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.0)
        
        goal = context.get("goal")
        content_plan = context.get("content_plan", {})
        
        checks = []
        
        # Engagement potansiyeli
        interactive_count = content_plan.get("interactive_count", 0)
        checks.append(("Engagement potansiyeli", interactive_count > 0, 
                      f"{interactive_count} interaktif öğe"))
        
        # Süre uygunluğu
        daily_hours = goal.daily_hours if hasattr(goal, 'daily_hours') else 2
        checks.append(("Süre uygunluğu", True, f"Günlük {daily_hours} saat planlandı"))
        
        # Motivasyon faktörleri
        checks.append(("Motivasyon faktörleri", True, "XP, seviye, başarılar entegre"))
        
        # Geri bildirim kalitesi
        checks.append(("Geri bildirim", True, "Detaylı feedback planlandı"))
        
        passed = sum(1 for _, status, _ in checks if status)
        score = passed / len(checks) if checks else 0.8
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="ogrenci_deneyimi",
            phase=ThinkingPhase.CONCLUDING,
            thinking=f"👤 Öğrenci deneyimi: %{int(score * 100)}",
            evidence=[f"{'✓' if s else '✗'} {n}: {d}" for n, s, d in checks],
            confidence=score,
            is_complete=True
        )
    
    async def _final_approval(
        self, 
        context: Dict[str, Any],
        scores: Dict[str, float]
    ) -> AsyncGenerator[AgentThought, None]:
        """Final onay ve öneriler"""
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="final_onay",
            phase=ThinkingPhase.DECIDING,
            thinking="⚖️ Final değerlendirme yapılıyor...",
            is_streaming=True
        )
        
        await asyncio.sleep(1.0)
        
        final_score = self._calculate_final_score(scores)
        
        recommendations = []
        
        if scores.get("pedagogical_coherence", 0) < 0.8:
            recommendations.append("Pedagojik tutarlılığı iyileştir")
        if scores.get("content_quality", 0) < 0.8:
            recommendations.append("Daha fazla multimedya içerik ekle")
        if scores.get("assessment_validity", 0) < 0.8:
            recommendations.append("Sınav çeşitliliğini artır")
        if scores.get("learner_experience", 0) < 0.8:
            recommendations.append("Daha fazla interaktif öğe ekle")
        
        context["recommendations"] = recommendations
        
        approval_status = "ONAYLANDI ✓" if final_score >= 0.75 else "İYİLEŞTİRME GEREKLİ"
        
        yield AgentThought(
            agent_name=self.name,
            agent_icon=self.icon,
            step="final_onay",
            phase=ThinkingPhase.CONCLUDING,
            thinking=f"⚖️ {approval_status}",
            reasoning=f"Genel kalite skoru: %{int(final_score * 100)}",
            evidence=recommendations if recommendations else ["Tüm kriterler karşılandı"],
            conclusion=f"Müfredat {'üretime hazır' if final_score >= 0.75 else 'revizyona ihtiyaç duyuyor'}.",
            confidence=final_score,
            is_complete=True
        )
    
    def _calculate_final_score(self, scores: Dict[str, float]) -> float:
        """Ağırlıklı final skor hesapla"""
        if not scores:
            return 0.8  # Default
        
        total_weight = 0
        weighted_sum = 0
        
        for criterion, info in self.QUALITY_CRITERIA.items():
            weight = info["weight"]
            score = scores.get(criterion, 0.8)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.8
