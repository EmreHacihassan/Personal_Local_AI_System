"""
DynamicPageManager - Dinamik Sayfa Artırma Sistemi
===================================================

AI'ın içerik zenginliğine göre sayfa sayısını otomatik artırmasını sağlar.
Kullanıcının belirlediği sayfa sayısı + maksimum 15 sayfa esneklik.

Özellikler:
- Information density analizi
- Topic complexity scoring
- AI-driven page expansion (max +15)
- Quality-aware expansion
- User consent integration
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("dynamic_page_manager")


class ExpansionReason(str, Enum):
    """Sayfa artırma nedenleri."""
    HIGH_COMPLEXITY = "high_complexity"
    RICH_SOURCES = "rich_sources"
    DEEP_SUBTOPICS = "deep_subtopics"
    USER_INTEREST = "user_interest"
    QUALITY_ENHANCEMENT = "quality_enhancement"
    CROSS_REFERENCES = "cross_references"


@dataclass
class ExpansionRequest:
    """Sayfa artırma isteği."""
    section_id: str
    section_title: str
    current_pages: int
    requested_additional: int
    reason: ExpansionReason
    confidence: float
    justification: str
    estimated_quality_gain: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ExpansionDecision:
    """Sayfa artırma kararı."""
    approved: bool
    additional_pages: int
    reason: str
    new_total_pages: int


@dataclass
class PageAllocation:
    """Sayfa dağılımı."""
    section_id: str
    section_title: str
    base_pages: float
    bonus_pages: float
    total_pages: float
    importance_score: float


class DynamicPageManager:
    """
    Dinamik Sayfa Yönetim Sistemi
    
    AI, içerik zenginliğine göre sayfa sayısını otomatik artırabilir.
    Maksimum artış: +15 sayfa (kullanıcının belirlediği limit)
    """
    
    MAX_EXPANSION = 15  # Maksimum ek sayfa
    
    def __init__(
        self,
        base_page_count: int,
        max_expansion: int = MAX_EXPANSION,
        auto_expand: bool = True
    ):
        self.base_page_count = base_page_count
        self.max_expansion = min(max_expansion, self.MAX_EXPANSION)
        self.auto_expand = auto_expand
        
        self.current_page_count = base_page_count
        self.expansion_requests: List[ExpansionRequest] = []
        self.approved_expansions: List[ExpansionDecision] = []
        self.section_allocations: Dict[str, PageAllocation] = {}
        
        # Metrics
        self.total_expanded = 0
        self.expansion_history: List[Dict] = []
    
    @property
    def remaining_expansion(self) -> int:
        """Kalan genişleme kapasitesi."""
        return self.max_expansion - self.total_expanded
    
    @property
    def current_total(self) -> int:
        """Mevcut toplam sayfa sayısı."""
        return self.base_page_count + self.total_expanded
    
    async def analyze_section_complexity(
        self,
        section_title: str,
        section_content: str,
        research_sources: List[Dict],
        subtopics: List[str]
    ) -> Dict[str, Any]:
        """
        Bölüm karmaşıklığını analiz et.
        
        Returns:
            Karmaşıklık metrikleri ve genişleme önerisi
        """
        metrics = {
            "source_richness": 0.0,
            "topic_depth": 0.0,
            "cross_reference_potential": 0.0,
            "technical_density": 0.0,
            "overall_complexity": 0.0
        }
        
        # Source richness (kaynak zenginliği)
        source_count = len(research_sources)
        if source_count >= 15:
            metrics["source_richness"] = 1.0
        elif source_count >= 10:
            metrics["source_richness"] = 0.8
        elif source_count >= 5:
            metrics["source_richness"] = 0.5
        else:
            metrics["source_richness"] = 0.3
        
        # Topic depth (alt konu derinliği)
        subtopic_count = len(subtopics)
        if subtopic_count >= 8:
            metrics["topic_depth"] = 1.0
        elif subtopic_count >= 5:
            metrics["topic_depth"] = 0.7
        elif subtopic_count >= 3:
            metrics["topic_depth"] = 0.5
        else:
            metrics["topic_depth"] = 0.3
        
        # Technical density (teknik yoğunluk)
        technical_keywords = [
            "algoritma", "formül", "denklem", "teorem", "hipotez",
            "algorithm", "formula", "equation", "theorem", "hypothesis",
            "methodology", "framework", "architecture", "protocol"
        ]
        
        content_lower = section_content.lower()
        tech_count = sum(1 for kw in technical_keywords if kw in content_lower)
        metrics["technical_density"] = min(1.0, tech_count / 10)
        
        # Cross-reference potential
        if source_count > 5 and subtopic_count > 3:
            metrics["cross_reference_potential"] = 0.8
        else:
            metrics["cross_reference_potential"] = 0.4
        
        # Overall complexity
        metrics["overall_complexity"] = (
            metrics["source_richness"] * 0.3 +
            metrics["topic_depth"] * 0.3 +
            metrics["technical_density"] * 0.2 +
            metrics["cross_reference_potential"] * 0.2
        )
        
        # Genişleme önerisi
        expansion_suggested = 0
        if metrics["overall_complexity"] >= 0.8:
            expansion_suggested = 3
        elif metrics["overall_complexity"] >= 0.6:
            expansion_suggested = 2
        elif metrics["overall_complexity"] >= 0.4:
            expansion_suggested = 1
        
        metrics["expansion_suggested"] = min(expansion_suggested, self.remaining_expansion)
        
        return metrics
    
    async def request_expansion(
        self,
        section_id: str,
        section_title: str,
        reason: ExpansionReason,
        requested_pages: int,
        justification: str,
        confidence: float = 0.7
    ) -> ExpansionDecision:
        """
        Sayfa artırma isteği oluştur ve değerlendir.
        
        Args:
            section_id: Bölüm ID
            section_title: Bölüm başlığı
            reason: Artırma nedeni
            requested_pages: İstenen ek sayfa
            justification: Gerekçe
            confidence: Güven skoru (0-1)
        
        Returns:
            ExpansionDecision - Onay/red kararı
        """
        # Kapasite kontrolü
        if self.remaining_expansion <= 0:
            return ExpansionDecision(
                approved=False,
                additional_pages=0,
                reason="Maksimum genişleme kapasitesine ulaşıldı",
                new_total_pages=self.current_total
            )
        
        # İsteği kaydet
        request = ExpansionRequest(
            section_id=section_id,
            section_title=section_title,
            current_pages=self.current_page_count,
            requested_additional=requested_pages,
            reason=reason,
            confidence=confidence,
            justification=justification,
            estimated_quality_gain=confidence * 0.2  # Tahmini kalite artışı
        )
        self.expansion_requests.append(request)
        
        # Auto-expand aktifse ve yeterli güven varsa onayla
        if self.auto_expand and confidence >= 0.6:
            approved_pages = min(requested_pages, self.remaining_expansion)
            
            if approved_pages > 0:
                self.total_expanded += approved_pages
                self.current_page_count += approved_pages
                
                decision = ExpansionDecision(
                    approved=True,
                    additional_pages=approved_pages,
                    reason=f"Otomatik onay: {reason.value}",
                    new_total_pages=self.current_total
                )
                
                self.approved_expansions.append(decision)
                self.expansion_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "section": section_title,
                    "pages_added": approved_pages,
                    "reason": reason.value,
                    "new_total": self.current_total
                })
                
                logger.info(f"📄 Sayfa artırma onaylandı: +{approved_pages} sayfa ({section_title})")
                return decision
        
        return ExpansionDecision(
            approved=False,
            additional_pages=0,
            reason="Otomatik genişleme kapalı veya güven düşük",
            new_total_pages=self.current_total
        )
    
    async def ai_evaluate_expansion_need(
        self,
        topic: str,
        outline: List[Dict],
        research_summary: str
    ) -> Tuple[bool, int, str]:
        """
        AI ile genişleme ihtiyacını değerlendir.
        
        Returns:
            (should_expand, suggested_pages, reasoning)
        """
        prompt = f"""Bir akademik döküman için sayfa sayısı değerlendirmesi yap.

Konu: {topic}
Mevcut Plan: {len(outline)} bölüm
Hedef Sayfa: {self.base_page_count}
Maksimum Ek Sayfa: {self.remaining_expansion}

Araştırma Özeti:
{research_summary[:1500]}

Bölümler:
{', '.join([s.get('title', '') for s in outline[:10]])}

Değerlendir:
1. İçerik bu sayfa sayısına sığar mı?
2. Kaliteyi artırmak için ek sayfa gerekli mi?
3. Hangi bölümler genişlemeye ihtiyaç duyar?

JSON formatında yanıt ver:
{{
    "should_expand": true/false,
    "suggested_additional_pages": 0-{self.remaining_expansion},
    "reasoning": "...",
    "priority_sections": ["bölüm1", "bölüm2"]
}}
"""
        
        try:
            response = await llm_manager.generate_async(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            import json
            import re
            
            # JSON çıkar
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return (
                    result.get("should_expand", False),
                    min(result.get("suggested_additional_pages", 0), self.remaining_expansion),
                    result.get("reasoning", "")
                )
        except Exception as e:
            logger.error(f"AI expansion evaluation error: {e}")
        
        return (False, 0, "Değerlendirme yapılamadı")
    
    def allocate_pages_to_sections(
        self,
        sections: List[Dict],
        importance_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, PageAllocation]:
        """
        Sayfa sayısını bölümlere dağıt.
        
        Args:
            sections: Bölüm listesi
            importance_scores: Bölüm önem skorları
        
        Returns:
            Bölüm bazlı sayfa dağılımı
        """
        total_pages = self.current_total
        section_count = len(sections)
        
        if section_count == 0:
            return {}
        
        # Varsayılan eşit dağılım
        base_per_section = total_pages / section_count
        
        # Önem skorlarına göre ağırlıklandır
        if importance_scores:
            total_importance = sum(importance_scores.values())
            
            for section in sections:
                section_id = section.get("id", "")
                section_title = section.get("title", "")
                importance = importance_scores.get(section_id, 1.0)
                
                # Ağırlıklı sayfa hesapla
                weighted_pages = (importance / total_importance) * total_pages
                
                self.section_allocations[section_id] = PageAllocation(
                    section_id=section_id,
                    section_title=section_title,
                    base_pages=base_per_section,
                    bonus_pages=weighted_pages - base_per_section,
                    total_pages=weighted_pages,
                    importance_score=importance
                )
        else:
            for section in sections:
                section_id = section.get("id", "")
                section_title = section.get("title", "")
                
                self.section_allocations[section_id] = PageAllocation(
                    section_id=section_id,
                    section_title=section_title,
                    base_pages=base_per_section,
                    bonus_pages=0,
                    total_pages=base_per_section,
                    importance_score=1.0
                )
        
        return self.section_allocations
    
    def get_expansion_report(self) -> Dict[str, Any]:
        """Genişleme raporu oluştur."""
        return {
            "base_page_count": self.base_page_count,
            "max_expansion_allowed": self.max_expansion,
            "total_expanded": self.total_expanded,
            "remaining_capacity": self.remaining_expansion,
            "current_total": self.current_total,
            "expansion_history": self.expansion_history,
            "request_count": len(self.expansion_requests),
            "approved_count": len(self.approved_expansions),
            "section_allocations": {
                k: {
                    "title": v.section_title,
                    "pages": v.total_pages,
                    "importance": v.importance_score
                }
                for k, v in self.section_allocations.items()
            }
        }
    
    def to_event(self, event_type: str = "page_expansion") -> Dict[str, Any]:
        """WebSocket event formatına dönüştür."""
        return {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "base_pages": self.base_page_count,
            "current_pages": self.current_total,
            "expanded_by": self.total_expanded,
            "remaining_capacity": self.remaining_expansion,
            "message": f"📄 Sayfa sayısı: {self.base_page_count} + {self.total_expanded} = {self.current_total}"
        }
