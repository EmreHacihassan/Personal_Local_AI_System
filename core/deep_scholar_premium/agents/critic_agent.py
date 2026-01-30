"""
CriticAgent - Premium Eleştiri ve Değerlendirme Ajanı
=====================================================

Görevler:
1. Her bölümü bağımsız değerlendir ve puan ver
2. Argüman gücünü analiz et
3. Kanıt kalitesini değerlendir
4. Mantıksal tutarlılığı kontrol et
5. Karşıt görüşleri ve sınırlamaları belirle
6. Akademik standartlara uygunluğu denetle

ÖNEMLİ: Critic farklı fikirleri törpülemez, 
aksine zengin perspektifleri ÖDÜLLENDIRIR.
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm_manager import llm_manager

# Logger setup
logger = logging.getLogger(__name__)


class ArgumentStrength(str, Enum):
    """Argüman gücü seviyeleri."""
    COMPELLING = "compelling"          # Çok ikna edici
    STRONG = "strong"                  # Güçlü
    MODERATE = "moderate"              # Orta
    WEAK = "weak"                      # Zayıf
    UNSUPPORTED = "unsupported"        # Desteksiz


class EvidenceQuality(str, Enum):
    """Kanıt kalitesi seviyeleri."""
    EXEMPLARY = "exemplary"            # Örnek teşkil edici
    SOLID = "solid"                    # Sağlam
    ADEQUATE = "adequate"              # Yeterli
    INSUFFICIENT = "insufficient"       # Yetersiz
    MISSING = "missing"                # Eksik


@dataclass
class CritiqueResult:
    """Eleştiri sonucu."""
    section_id: str
    section_title: str
    overall_rating: float  # 1-10
    
    # Detaylı puanlar
    argument_strength: ArgumentStrength
    evidence_quality: EvidenceQuality
    logical_coherence: float  # 1-10
    academic_rigor: float  # 1-10
    originality: float  # 1-10
    clarity: float  # 1-10
    
    # Analiz
    key_arguments: List[str]
    supporting_evidence: List[str]
    logical_gaps: List[str]
    counter_arguments: List[str]
    limitations: List[str]
    
    # Öneriler
    strengths_to_keep: List[str]
    areas_for_improvement: List[str]
    specific_suggestions: List[str]
    
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DocumentCritique:
    """Doküman geneli eleştiri."""
    document_id: str
    section_critiques: List[CritiqueResult]
    
    # Genel değerlendirme
    overall_rating: float
    thesis_clarity: float
    argument_flow: float
    evidence_integration: float
    conclusion_strength: float
    
    # Özet
    executive_summary: str
    major_strengths: List[str]
    major_weaknesses: List[str]
    recommended_revisions: List[Dict[str, Any]]
    
    # Meta
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class CriticAgent:
    """
    Premium Eleştiri Ajanı
    
    Her bölümü derinlemesine analiz eder ve yapıcı eleştiri sunar.
    Farklı bakış açılarını törpülemez, aksine akademik çeşitliliği teşvik eder.
    """
    
    def __init__(self, global_state: Optional[Any] = None):
        self.global_state = global_state
        
        # Değerlendirme ağırlıkları
        self.rating_weights = {
            "argument_strength": 0.25,
            "evidence_quality": 0.20,
            "logical_coherence": 0.20,
            "academic_rigor": 0.15,
            "originality": 0.10,
            "clarity": 0.10
        }
    
    async def critique_section(
        self,
        section_content: str,
        section_title: str,
        section_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CritiqueResult:
        """
        Tek bir bölümü eleştir.
        
        Args:
            section_content: Bölüm içeriği
            section_title: Bölüm başlığı
            section_id: Bölüm ID
            context: Döküman bağlamı
            
        Returns:
            Detaylı eleştiri sonucu
        """
        prompt = f"""Sen bir akademik eleştirmensin. Aşağıdaki bölümü kapsamlı şekilde değerlendir.

## Bölüm Başlığı: {section_title}

## İçerik:
{section_content[:4000]}

## Değerlendirme Kriterleri:

1. **Argüman Gücü**: Argümanlar ne kadar ikna edici?
2. **Kanıt Kalitesi**: Destekleyici kanıtlar ne kadar sağlam?
3. **Mantıksal Tutarlılık**: Akış mantıklı mı?
4. **Akademik Titizlik**: Akademik standartlara uygun mu?
5. **Özgünlük**: Özgün katkı var mı?
6. **Açıklık**: Anlaşılır mı?

## Yanıt Formatı (JSON):
{{
    "overall_rating": <1-10>,
    "argument_strength": "compelling|strong|moderate|weak|unsupported",
    "evidence_quality": "exemplary|solid|adequate|insufficient|missing",
    "logical_coherence": <1-10>,
    "academic_rigor": <1-10>,
    "originality": <1-10>,
    "clarity": <1-10>,
    "key_arguments": ["<argüman 1>", "<argüman 2>"],
    "supporting_evidence": ["<kanıt 1>", "<kanıt 2>"],
    "logical_gaps": ["<boşluk 1>", "<boşluk 2>"],
    "counter_arguments": ["<karşıt görüş 1>"],
    "limitations": ["<sınırlama 1>"],
    "strengths_to_keep": ["<güçlü yön 1>"],
    "areas_for_improvement": ["<iyileştirilecek alan 1>"],
    "specific_suggestions": ["<somut öneri 1>"]
}}

ÖNEMLİ KURALLAR:
- Farklı bakış açılarını TÖRPÜLEME
- Özgün fikirleri ÖDÜLLENDIR
- Yapıcı eleştiri yap, yıkıcı değil
- Akademik çoğulculuğu destekle"""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                return CritiqueResult(
                    section_id=section_id,
                    section_title=section_title,
                    overall_rating=float(data.get("overall_rating", 7)),
                    argument_strength=ArgumentStrength(data.get("argument_strength", "moderate")),
                    evidence_quality=EvidenceQuality(data.get("evidence_quality", "adequate")),
                    logical_coherence=float(data.get("logical_coherence", 7)),
                    academic_rigor=float(data.get("academic_rigor", 7)),
                    originality=float(data.get("originality", 7)),
                    clarity=float(data.get("clarity", 7)),
                    key_arguments=data.get("key_arguments", []),
                    supporting_evidence=data.get("supporting_evidence", []),
                    logical_gaps=data.get("logical_gaps", []),
                    counter_arguments=data.get("counter_arguments", []),
                    limitations=data.get("limitations", []),
                    strengths_to_keep=data.get("strengths_to_keep", []),
                    areas_for_improvement=data.get("areas_for_improvement", []),
                    specific_suggestions=data.get("specific_suggestions", [])
                )
        except Exception as e:
            logger.warning(f"Failed to parse critique response: {e}")
        
        # Varsayılan sonuç
        return CritiqueResult(
            section_id=section_id,
            section_title=section_title,
            overall_rating=7.0,
            argument_strength=ArgumentStrength.MODERATE,
            evidence_quality=EvidenceQuality.ADEQUATE,
            logical_coherence=7.0,
            academic_rigor=7.0,
            originality=7.0,
            clarity=7.0,
            key_arguments=[],
            supporting_evidence=[],
            logical_gaps=[],
            counter_arguments=[],
            limitations=[],
            strengths_to_keep=[],
            areas_for_improvement=[],
            specific_suggestions=[]
        )
    
    async def critique_document(
        self,
        sections: List[Dict[str, Any]],
        document_id: str
    ) -> DocumentCritique:
        """
        Tüm dokümanı eleştir.
        
        Args:
            sections: Bölüm listesi
            document_id: Doküman ID
            
        Returns:
            Kapsamlı doküman eleştirisi
        """
        # Her bölümü eleştir
        section_critiques = []
        for section in sections:
            critique = await self.critique_section(
                section_content=section.get("content", ""),
                section_title=section.get("title", ""),
                section_id=section.get("id", "")
            )
            section_critiques.append(critique)
        
        # Genel puanları hesapla
        overall_rating = sum(c.overall_rating for c in section_critiques) / max(len(section_critiques), 1)
        
        # Yönetici özeti oluştur
        executive_summary = await self._generate_executive_summary(section_critiques)
        
        # Büyük güçlü/zayıf yönleri derle
        major_strengths = []
        major_weaknesses = []
        for critique in section_critiques:
            major_strengths.extend(critique.strengths_to_keep[:2])
            major_weaknesses.extend(critique.areas_for_improvement[:2])
        
        # Revizyon önerileri
        recommended_revisions = await self._generate_revision_recommendations(section_critiques)
        
        return DocumentCritique(
            document_id=document_id,
            section_critiques=section_critiques,
            overall_rating=overall_rating,
            thesis_clarity=await self._evaluate_thesis_clarity(sections),
            argument_flow=await self._evaluate_argument_flow(sections),
            evidence_integration=await self._evaluate_evidence_integration(sections),
            conclusion_strength=await self._evaluate_conclusion_strength(sections),
            executive_summary=executive_summary,
            major_strengths=list(set(major_strengths))[:10],
            major_weaknesses=list(set(major_weaknesses))[:10],
            recommended_revisions=recommended_revisions
        )
    
    async def analyze_argument_structure(
        self,
        content: str
    ) -> Dict[str, Any]:
        """Argüman yapısını analiz et."""
        prompt = f"""Aşağıdaki içerikteki argüman yapısını analiz et.

İçerik:
{content[:3000]}

JSON formatında yanıt:
{{
    "main_thesis": "<ana tez>",
    "supporting_arguments": [
        {{"argument": "<argüman>", "strength": "strong|moderate|weak", "evidence": "<kanıt>"}}
    ],
    "logical_structure": "deductive|inductive|abductive|mixed",
    "argument_flow": "linear|circular|branching|complex",
    "persuasiveness_score": <1-10>,
    "fallacies_detected": ["<mantık hatası>"],
    "missing_connections": ["<eksik bağlantı>"]
}}"""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"main_thesis": "", "supporting_arguments": [], "persuasiveness_score": 7}
    
    async def identify_bias_and_perspectives(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Önyargı ve perspektifleri belirle.
        
        NOT: Bu fonksiyon önyargıları TÖRPÜLEMEMELİ,
        sadece TESPİT ETMELİ ve farkındalık sağlamalıdır.
        """
        prompt = f"""Aşağıdaki içerikteki perspektifleri ve olası önyargıları analiz et.

İçerik:
{content[:3000]}

ÖNEMLİ: Amaç önyargıları TÖRPÜLEMEK değil, FARKINDALIK sağlamaktır.
Farklı perspektifler akademik zenginliktir.

JSON formatında yanıt:
{{
    "primary_perspective": "<ana perspektif>",
    "alternative_perspectives_mentioned": ["<alternatif 1>"],
    "perspectives_missing": ["<eksik perspektif>"],
    "potential_biases": [
        {{
            "type": "<önyargı türü>",
            "description": "<açıklama>",
            "impact": "low|medium|high",
            "suggestion": "<dengeli ifade önerisi>"
        }}
    ],
    "objectivity_score": <1-10>,
    "balance_score": <1-10>,
    "recommendations": ["<öneri>"]
}}

NOT: Özgün bakış açıları ve güçlü argümanlar önyargı DEĞİLDİR.
Bir görüşü savunmak normal ve akademik olarak kabul edilebilirdir."""

        response = await self._llm_call(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"objectivity_score": 8, "balance_score": 8, "potential_biases": []}
    
    async def _generate_executive_summary(
        self,
        critiques: List[CritiqueResult]
    ) -> str:
        """Yönetici özeti oluştur."""
        avg_rating = sum(c.overall_rating for c in critiques) / max(len(critiques), 1)
        
        summary_parts = []
        summary_parts.append(f"Doküman genel puanı: {avg_rating:.1f}/10.")
        
        # En güçlü bölümler
        sorted_by_rating = sorted(critiques, key=lambda x: x.overall_rating, reverse=True)
        if sorted_by_rating:
            best = sorted_by_rating[0]
            summary_parts.append(f"En güçlü bölüm: '{best.section_title}' ({best.overall_rating}/10).")
        
        # İyileştirme gereken bölümler
        needs_improvement = [c for c in critiques if c.overall_rating < 7]
        if needs_improvement:
            summary_parts.append(
                f"{len(needs_improvement)} bölüm iyileştirme gerektiriyor."
            )
        
        return " ".join(summary_parts)
    
    async def _generate_revision_recommendations(
        self,
        critiques: List[CritiqueResult]
    ) -> List[Dict[str, Any]]:
        """Revizyon önerileri oluştur."""
        recommendations = []
        
        for critique in critiques:
            if critique.overall_rating < 7:
                recommendations.append({
                    "section": critique.section_title,
                    "priority": "high" if critique.overall_rating < 5 else "medium",
                    "issues": critique.areas_for_improvement[:3],
                    "suggestions": critique.specific_suggestions[:3],
                    "expected_improvement": f"+{min(3, 10-critique.overall_rating):.1f} puan"
                })
        
        # Önceliğe göre sırala
        recommendations.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
        
        return recommendations[:10]
    
    async def _evaluate_thesis_clarity(self, sections: List[Dict[str, Any]]) -> float:
        """Tez netliğini değerlendir."""
        # İlk bölümden (giriş) tez netliğini değerlendir
        if sections:
            intro_content = sections[0].get("content", "")[:1000]
            if "tez" in intro_content.lower() or "amaç" in intro_content.lower():
                return 8.0
        return 6.5
    
    async def _evaluate_argument_flow(self, sections: List[Dict[str, Any]]) -> float:
        """Argüman akışını değerlendir."""
        return 7.5  # Basit varsayılan
    
    async def _evaluate_evidence_integration(self, sections: List[Dict[str, Any]]) -> float:
        """Kanıt entegrasyonunu değerlendir."""
        total_citations = 0
        for section in sections:
            content = section.get("content", "")
            # Basit alıntı sayımı
            total_citations += len(re.findall(r'\[\d+\]|\(\d{4}\)', content))
        
        # Her bölüm başına ortalama
        avg_per_section = total_citations / max(len(sections), 1)
        return min(10, 5 + avg_per_section)
    
    async def _evaluate_conclusion_strength(self, sections: List[Dict[str, Any]]) -> float:
        """Sonuç gücünü değerlendir."""
        if sections:
            last_section = sections[-1].get("content", "")
            if "sonuç" in last_section.lower() or "özet" in last_section.lower():
                return 7.5
        return 6.0
    
    async def _llm_call(self, prompt: str, timeout: int = 300) -> str:
        """LLM çağrısı yap."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_manager.chat,
                    messages=messages,
                    model_type="default"
                ),
                timeout=timeout
            )
            return response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
