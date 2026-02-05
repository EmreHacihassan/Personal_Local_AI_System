"""
🔍 Advanced Hallucination Detector
===================================

LLM yanıtlarında halüsinasyon tespiti ve düzeltme.

Features:
- Fact verification against sources
- Entity consistency checking  
- Temporal validation
- Confidence scoring
- Auto-correction suggestions
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum

logger = logging.getLogger(__name__)


class HallucinationType(Enum):
    """Halüsinasyon türleri."""
    FACTUAL = "factual"  # Yanlış bilgi
    ENTITY = "entity"  # Yanlış entity
    TEMPORAL = "temporal"  # Yanlış tarih/zaman
    NUMERIC = "numeric"  # Yanlış sayı
    ATTRIBUTION = "attribution"  # Yanlış kaynak atıfı
    CONFLATION = "conflation"  # Karışık/birleştirilmiş bilgi
    FABRICATION = "fabrication"  # Tamamen uydurma


class SeverityLevel(Enum):
    """Halüsinasyon ciddiyeti."""
    LOW = "low"  # Küçük detay hatası
    MEDIUM = "medium"  # Önemli ama düzeltilebilir
    HIGH = "high"  # Ciddi yanlış bilgi
    CRITICAL = "critical"  # Tamamen yanlış


@dataclass
class DetectedHallucination:
    """Tespit edilen halüsinasyon."""
    type: HallucinationType
    severity: SeverityLevel
    span: Tuple[int, int]  # (başlangıç, bitiş) pozisyonu
    text: str  # Sorunlu metin
    reason: str  # Neden halüsinasyon
    suggestion: Optional[str] = None  # Düzeltme önerisi
    confidence: float = 0.0  # Tespit güveni
    source_contradicts: Optional[str] = None  # Çelişen kaynak


@dataclass
class HallucinationReport:
    """Halüsinasyon analiz raporu."""
    total_hallucinations: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    hallucinations: List[DetectedHallucination]
    overall_score: float  # 0-1 (1 = temiz)
    flagged_sections: List[str]
    recommendations: List[str]


class FactChecker:
    """
    Fact-based verification.
    
    Kaynaklarla karşılaştırarak doğruluk kontrolü yapar.
    """
    
    def __init__(self):
        # Sayı desenleri
        self.number_patterns = [
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b',  # 1,000.50
            r'\b\d+(?:\.\d+)?%\b',  # 50.5%
            r'\b\d+(?:\.\d+)?\s*(?:million|billion|trilyon|milyar|milyon)\b',
        ]
        
        # Tarih desenleri
        self.date_patterns = [
            r'\b\d{4}\b',  # Yıl
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # Tarih
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',
            r'\b(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık)\s+\d{4}\b',
        ]
    
    def extract_facts(self, text: str) -> Dict[str, List[str]]:
        """Metinden fact'leri çıkar."""
        facts = {
            "numbers": [],
            "dates": [],
            "entities": [],
            "claims": []
        }
        
        # Sayıları çıkar
        for pattern in self.number_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            facts["numbers"].extend(matches)
        
        # Tarihleri çıkar
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            facts["dates"].extend(matches)
        
        return facts
    
    def compare_facts(
        self,
        response_facts: Dict[str, List[str]],
        source_facts: Dict[str, List[str]]
    ) -> List[Tuple[str, str, str]]:
        """
        Fact'leri karşılaştır.
        
        Returns:
            List of (category, response_fact, issue)
        """
        issues = []
        
        # Sayıları kontrol et
        for num in response_facts.get("numbers", []):
            if num not in source_facts.get("numbers", []):
                # Yakın değer var mı kontrol et
                is_close = self._check_close_number(
                    num, source_facts.get("numbers", [])
                )
                if not is_close:
                    issues.append(("number", num, "not_in_source"))
        
        # Tarihleri kontrol et
        for date in response_facts.get("dates", []):
            if date not in source_facts.get("dates", []):
                issues.append(("date", date, "not_in_source"))
        
        return issues
    
    def _check_close_number(
        self,
        num_str: str,
        source_nums: List[str],
        tolerance: float = 0.1
    ) -> bool:
        """Yakın sayı kontrolü."""
        try:
            num = float(num_str.replace(",", "").replace("%", ""))
            for src in source_nums:
                try:
                    src_num = float(src.replace(",", "").replace("%", ""))
                    if abs(num - src_num) / max(abs(src_num), 1) < tolerance:
                        return True
                except:
                    continue
        except:
            pass
        return False


class EntityConsistencyChecker:
    """
    Entity tutarlılık kontrolü.
    
    Named entities'in doğruluğunu kontrol eder.
    """
    
    def __init__(self):
        # Basit NER patterns
        self.name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        self.org_indicators = ["Inc.", "Corp.", "Ltd.", "LLC", "A.Ş.", "Ltd.Şti."]
    
    def extract_entities(self, text: str) -> Dict[str, Set[str]]:
        """Entity'leri çıkar."""
        entities = {
            "names": set(),
            "organizations": set()
        }
        
        # İsim benzeri pattern'ları bul
        matches = re.findall(self.name_pattern, text)
        for match in matches:
            # Organization indicator var mı?
            if any(ind in match for ind in self.org_indicators):
                entities["organizations"].add(match)
            elif len(match.split()) >= 2:  # En az 2 kelime = isim
                entities["names"].add(match)
        
        return entities
    
    def check_consistency(
        self,
        response_entities: Dict[str, Set[str]],
        source_entities: Dict[str, Set[str]]
    ) -> List[Tuple[str, str, str]]:
        """Entity tutarlılığını kontrol et."""
        issues = []
        
        # Response'daki entity'ler source'ta var mı?
        for name in response_entities.get("names", set()):
            if not self._fuzzy_match(name, source_entities.get("names", set())):
                issues.append(("name", name, "not_in_source"))
        
        for org in response_entities.get("organizations", set()):
            if not self._fuzzy_match(org, source_entities.get("organizations", set())):
                issues.append(("organization", org, "not_in_source"))
        
        return issues
    
    def _fuzzy_match(self, text: str, candidates: Set[str]) -> bool:
        """Fuzzy matching için basit kontrol."""
        text_lower = text.lower()
        for cand in candidates:
            cand_lower = cand.lower()
            # Exact or partial match
            if text_lower in cand_lower or cand_lower in text_lower:
                return True
        return False


class UncertaintyDetector:
    """
    Belirsizlik ifadelerini tespit eder.
    
    "Probably", "might be", "yaklaşık" gibi ifadeler.
    """
    
    def __init__(self):
        self.uncertainty_phrases = [
            # English
            "probably", "might", "may", "could be", "possibly",
            "approximately", "around", "about", "roughly",
            "i think", "i believe", "it seems", "apparently",
            "as far as i know", "to my knowledge",
            
            # Turkish
            "muhtemelen", "belki", "galiba", "herhalde",
            "yaklaşık", "civarında", "kadar", "sanırım",
            "düşünüyorum", "galiba", "gibi görünüyor",
            "bildiğim kadarıyla"
        ]
        
        self.confidence_phrases = [
            # High confidence
            ("definitely", 0.9), ("certainly", 0.9),
            ("kesinlikle", 0.9), ("mutlaka", 0.9),
            
            # Low confidence
            ("probably", 0.6), ("might", 0.5),
            ("muhtemelen", 0.6), ("belki", 0.4)
        ]
    
    def detect_uncertainty(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Belirsizlik ifadelerini tespit et.
        
        Returns:
            List of (phrase, start, end)
        """
        found = []
        text_lower = text.lower()
        
        for phrase in self.uncertainty_phrases:
            idx = text_lower.find(phrase)
            while idx != -1:
                found.append((phrase, idx, idx + len(phrase)))
                idx = text_lower.find(phrase, idx + 1)
        
        return found
    
    def get_confidence_score(self, text: str) -> float:
        """Metnin güven skorunu hesapla."""
        text_lower = text.lower()
        
        high_conf = sum(
            1 for phrase, _ in self.confidence_phrases
            if phrase in text_lower and _ > 0.7
        )
        low_conf = sum(
            1 for phrase, _ in self.confidence_phrases
            if phrase in text_lower and _ < 0.6
        )
        
        if low_conf > high_conf:
            return 0.5
        elif high_conf > low_conf:
            return 0.9
        return 0.7


class HallucinationDetector:
    """
    Ana halüsinasyon tespit sınıfı.
    
    Tüm checkers'ı koordine eder.
    """
    
    def __init__(self):
        self.fact_checker = FactChecker()
        self.entity_checker = EntityConsistencyChecker()
        self.uncertainty_detector = UncertaintyDetector()
        
        # Fabrication indicators
        self.fabrication_indicators = [
            "studies show", "research indicates", "according to experts",
            "araştırmalar gösteriyor", "uzmanlara göre", "bilimsel olarak",
        ]
    
    def detect(
        self,
        response: str,
        sources: List[str],
        query: Optional[str] = None
    ) -> HallucinationReport:
        """
        Response'daki halüsinasyonları tespit et.
        
        Args:
            response: LLM yanıtı
            sources: RAG kaynakları
            query: Original sorgu (opsiyonel)
            
        Returns:
            HallucinationReport
        """
        hallucinations = []
        combined_sources = " ".join(sources)
        
        # 1. Fact checking
        response_facts = self.fact_checker.extract_facts(response)
        source_facts = self.fact_checker.extract_facts(combined_sources)
        fact_issues = self.fact_checker.compare_facts(response_facts, source_facts)
        
        for category, fact, issue in fact_issues:
            h_type = HallucinationType.NUMERIC if category == "number" else HallucinationType.TEMPORAL
            hallucinations.append(DetectedHallucination(
                type=h_type,
                severity=SeverityLevel.MEDIUM,
                span=self._find_span(response, fact),
                text=fact,
                reason=f"{category} not found in sources",
                suggestion=f"Verify {fact} against source documents",
                confidence=0.7
            ))
        
        # 2. Entity consistency
        response_entities = self.entity_checker.extract_entities(response)
        source_entities = self.entity_checker.extract_entities(combined_sources)
        entity_issues = self.entity_checker.check_consistency(
            response_entities, source_entities
        )
        
        for category, entity, issue in entity_issues:
            hallucinations.append(DetectedHallucination(
                type=HallucinationType.ENTITY,
                severity=SeverityLevel.MEDIUM,
                span=self._find_span(response, entity),
                text=entity,
                reason=f"{category} '{entity}' not found in sources",
                suggestion=f"Verify if '{entity}' is correct",
                confidence=0.6
            ))
        
        # 3. Fabrication check
        fabrication = self._check_fabrication(response, combined_sources)
        hallucinations.extend(fabrication)
        
        # 4. Attribution check
        attribution = self._check_attribution(response, combined_sources)
        hallucinations.extend(attribution)
        
        # 5. Calculate overall score
        overall_score = self._calculate_overall_score(hallucinations, response)
        
        # 6. Generate report
        by_type = {}
        by_severity = {}
        for h in hallucinations:
            by_type[h.type.value] = by_type.get(h.type.value, 0) + 1
            by_severity[h.severity.value] = by_severity.get(h.severity.value, 0) + 1
        
        recommendations = self._generate_recommendations(hallucinations)
        flagged = [h.text for h in hallucinations if h.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]]
        
        return HallucinationReport(
            total_hallucinations=len(hallucinations),
            by_type=by_type,
            by_severity=by_severity,
            hallucinations=hallucinations,
            overall_score=overall_score,
            flagged_sections=flagged,
            recommendations=recommendations
        )
    
    def _find_span(self, text: str, substring: str) -> Tuple[int, int]:
        """Substring'in pozisyonunu bul."""
        idx = text.find(substring)
        if idx == -1:
            return (0, 0)
        return (idx, idx + len(substring))
    
    def _check_fabrication(
        self,
        response: str,
        sources: str
    ) -> List[DetectedHallucination]:
        """Fabrication kontrolü."""
        hallucinations = []
        response_lower = response.lower()
        
        for indicator in self.fabrication_indicators:
            if indicator in response_lower:
                # Bu ifadeyi destekleyen kaynak var mı?
                if indicator not in sources.lower():
                    hallucinations.append(DetectedHallucination(
                        type=HallucinationType.FABRICATION,
                        severity=SeverityLevel.HIGH,
                        span=self._find_span(response.lower(), indicator),
                        text=indicator,
                        reason="Unsupported claim indicator",
                        suggestion="Remove or verify claim with actual sources",
                        confidence=0.6
                    ))
        
        return hallucinations
    
    def _check_attribution(
        self,
        response: str,
        sources: str
    ) -> List[DetectedHallucination]:
        """Attribution kontrolü (kaynak atıfı)."""
        hallucinations = []
        
        # "According to X" pattern
        patterns = [
            r"according to ([^,]+)",
            r"([^,]+) states that",
            r"([^,]+)'ya göre",
            r"([^,]+) belirtiyor"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                if match.lower() not in sources.lower():
                    hallucinations.append(DetectedHallucination(
                        type=HallucinationType.ATTRIBUTION,
                        severity=SeverityLevel.MEDIUM,
                        span=self._find_span(response, match),
                        text=match,
                        reason=f"Source '{match}' not found in documents",
                        suggestion="Verify source attribution",
                        confidence=0.5
                    ))
        
        return hallucinations
    
    def _calculate_overall_score(
        self,
        hallucinations: List[DetectedHallucination],
        response: str
    ) -> float:
        """Overall güvenilirlik skorunu hesapla."""
        if not hallucinations:
            return 1.0
        
        penalty = 0.0
        for h in hallucinations:
            if h.severity == SeverityLevel.CRITICAL:
                penalty += 0.3
            elif h.severity == SeverityLevel.HIGH:
                penalty += 0.2
            elif h.severity == SeverityLevel.MEDIUM:
                penalty += 0.1
            else:
                penalty += 0.05
        
        return max(0.0, 1.0 - penalty)
    
    def _generate_recommendations(
        self,
        hallucinations: List[DetectedHallucination]
    ) -> List[str]:
        """Düzeltme önerileri oluştur."""
        recs = []
        
        critical = [h for h in hallucinations if h.severity == SeverityLevel.CRITICAL]
        if critical:
            recs.append("CRITICAL: Review and rewrite sections with critical hallucinations")
        
        numeric = [h for h in hallucinations if h.type == HallucinationType.NUMERIC]
        if numeric:
            recs.append("Verify all numerical values against source documents")
        
        entity = [h for h in hallucinations if h.type == HallucinationType.ENTITY]
        if entity:
            recs.append("Double-check entity names and references")
        
        fabrication = [h for h in hallucinations if h.type == HallucinationType.FABRICATION]
        if fabrication:
            recs.append("Remove unsupported claims or add proper citations")
        
        if not hallucinations:
            recs.append("Response appears well-grounded in source material")
        
        return recs
    
    def quick_check(
        self,
        response: str,
        sources: List[str]
    ) -> Tuple[float, List[str]]:
        """
        Hızlı halüsinasyon kontrolü.
        
        Returns:
            (score, warnings)
        """
        report = self.detect(response, sources)
        warnings = [h.text for h in report.hallucinations[:5]]
        return report.overall_score, warnings


# Singleton instance
hallucination_detector = HallucinationDetector()
