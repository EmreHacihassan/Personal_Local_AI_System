"""
✅ Response Validator & Quality System
======================================

Premium yanıt doğrulama ve kalite kontrol sistemi:
- Multi-criteria validation
- Hallucination detection
- Format checking
- Self-reflection loop
- Confidence scoring

Author: Enterprise AI Team
Version: 1.0.0
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class ValidationStatus(str, Enum):
    """Doğrulama durumu."""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class QualityDimension(str, Enum):
    """Kalite boyutları."""
    RELEVANCE = "relevance"           # Soruyla alakalılık
    COMPLETENESS = "completeness"     # Yanıtın tamlığı
    ACCURACY = "accuracy"             # Bilgi doğruluğu
    FORMATTING = "formatting"         # Markdown/format kalitesi
    CITATIONS = "citations"           # Kaynak kullanımı
    COHERENCE = "coherence"           # Tutarlılık
    HELPFULNESS = "helpfulness"       # Yardımcı olma


@dataclass
class ValidationCheck:
    """Tek bir doğrulama kontrolü."""
    dimension: QualityDimension
    status: ValidationStatus
    score: float  # 0-1
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Doğrulama sonucu."""
    overall_status: ValidationStatus
    overall_score: float
    checks: List[ValidationCheck]
    suggestions: List[str]
    needs_improvement: bool
    improvement_priority: List[QualityDimension]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConfidenceResult:
    """Güven skoru sonucu."""
    overall: float
    breakdown: Dict[str, float]
    recommendation: str
    factors: List[str]


# ============================================================================
# RESPONSE VALIDATOR
# ============================================================================

class ResponseValidator:
    """
    Enterprise-grade yanıt doğrulayıcı.
    
    Features:
    - Multi-criteria validation
    - Hallucination detection
    - Format quality check
    - Source verification
    - Confidence scoring
    """
    
    # Kalite boyutu ağırlıkları
    DIMENSION_WEIGHTS = {
        QualityDimension.RELEVANCE: 0.25,
        QualityDimension.COMPLETENESS: 0.20,
        QualityDimension.ACCURACY: 0.20,
        QualityDimension.FORMATTING: 0.15,
        QualityDimension.CITATIONS: 0.10,
        QualityDimension.COHERENCE: 0.10,
    }
    
    # Minimum kabul edilebilir skorlar
    MIN_THRESHOLDS = {
        QualityDimension.RELEVANCE: 0.5,
        QualityDimension.COMPLETENESS: 0.4,
        QualityDimension.ACCURACY: 0.5,
        QualityDimension.FORMATTING: 0.3,
        QualityDimension.CITATIONS: 0.2,
        QualityDimension.COHERENCE: 0.4,
    }
    
    def __init__(self):
        self.hallucination_patterns = self._load_hallucination_patterns()
        self.quality_patterns = self._load_quality_patterns()
    
    def _load_hallucination_patterns(self) -> Dict[str, List[str]]:
        """Halüsinasyon pattern'lerini yükle."""
        return {
            "made_up_facts": [
                r"araştırmalar gösteriyor ki",
                r"studies show that",
                r"research indicates",
                r"bir çalışmaya göre",
                r"according to a study",
            ],
            "false_certainty": [
                r"kesinlikle",
                r"absolutely",
                r"definitely",
                r"without doubt",
                r"100%",
                r"her zaman",
                r"always",
                r"never",
                r"asla",
            ],
            "vague_sources": [
                r"uzmanlar",
                r"experts say",
                r"some people believe",
                r"bazıları",
                r"it is said",
                r"deniliyor ki",
            ],
        }
    
    def _load_quality_patterns(self) -> Dict[str, Any]:
        """Kalite değerlendirme pattern'lerini yükle."""
        return {
            "markdown_headers": r'^#{1,6}\s+.+$',
            "code_blocks": r'```[\w]*\n[\s\S]*?\n```',
            "inline_code": r'`[^`]+`',
            "lists": r'^[-*+]\s+.+$|^\d+\.\s+.+$',
            "links": r'\[.+?\]\(.+?\)',
            "emphasis": r'\*\*.+?\*\*|\*.+?\*|__.+?__|_.+?_',
            "citations": r'\[(?:Kaynak|Source|Ref)?\s*\d+\]|\[\w+\.\d+\]',
            "math": r'\$\$.+?\$\$|\$.+?\$',
        }
    
    def validate(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Yanıtı kapsamlı doğrula.
        
        Args:
            query: Kullanıcı sorusu
            response: LLM yanıtı
            context: Ek bağlam (RAG sonuçları, vb.)
            
        Returns:
            ValidationResult
        """
        context = context or {}
        checks = []
        
        # Her boyut için kontrol
        checks.append(self._check_relevance(query, response))
        checks.append(self._check_completeness(query, response))
        checks.append(self._check_accuracy(response, context))
        checks.append(self._check_formatting(response))
        checks.append(self._check_citations(response, context))
        checks.append(self._check_coherence(response))
        
        # Toplam skor hesapla
        total_score = self._calculate_total_score(checks)
        
        # Genel durum belirle
        failed_critical = any(
            c.status == ValidationStatus.FAILED and 
            self.DIMENSION_WEIGHTS.get(c.dimension, 0) >= 0.2
            for c in checks
        )
        
        if failed_critical or total_score < 0.4:
            overall_status = ValidationStatus.FAILED
        elif total_score < 0.7 or any(c.status == ValidationStatus.WARNING for c in checks):
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED
        
        # Öneriler oluştur
        suggestions = self._generate_suggestions(checks)
        
        # İyileştirme öncelikleri
        improvement_priority = [
            c.dimension for c in sorted(checks, key=lambda x: x.score)
            if c.score < 0.7
        ]
        
        return ValidationResult(
            overall_status=overall_status,
            overall_score=total_score,
            checks=checks,
            suggestions=suggestions,
            needs_improvement=overall_status != ValidationStatus.PASSED,
            improvement_priority=improvement_priority,
        )
    
    def _check_relevance(self, query: str, response: str) -> ValidationCheck:
        """Yanıtın soruyla alakalılığını kontrol et."""
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Keyword overlap
        common_words = query_words & response_words
        # Stopwords'ü çıkar
        stopwords = {"bir", "bu", "ve", "için", "de", "da", "mi", "mı", "ne", "the", "a", "an", "is", "are"}
        meaningful_overlap = common_words - stopwords
        
        if len(query_words - stopwords) > 0:
            overlap_ratio = len(meaningful_overlap) / len(query_words - stopwords)
        else:
            overlap_ratio = 0.5
        
        # Soru tipine göre ayarla
        is_question = any(q in query.lower() for q in ["?", "nedir", "nasıl", "neden", "what", "how", "why"])
        
        score = min(1.0, 0.3 + overlap_ratio * 0.7)
        
        # Yanıt çok kısa mı?
        if len(response.split()) < 10 and is_question:
            score *= 0.7
        
        # Yanıt çok uzun mu (off-topic olabilir)?
        if len(response.split()) > 1000 and len(query.split()) < 20:
            score *= 0.9
        
        status = (
            ValidationStatus.PASSED if score >= 0.7 else
            ValidationStatus.WARNING if score >= 0.5 else
            ValidationStatus.FAILED
        )
        
        return ValidationCheck(
            dimension=QualityDimension.RELEVANCE,
            status=status,
            score=score,
            message=f"Alakalılık skoru: {score:.2f}",
            details={"overlap_ratio": overlap_ratio, "common_keywords": list(meaningful_overlap)[:5]}
        )
    
    def _check_completeness(self, query: str, response: str) -> ValidationCheck:
        """Yanıtın tamlığını kontrol et."""
        query_lower = query.lower()
        response_lower = response.lower()
        
        score = 0.5
        issues = []
        
        # Soru işaretleri sayısı (birden fazla soru mu?)
        question_count = query.count("?") + sum(1 for q in ["nedir", "nasıl", "neden"] if q in query_lower)
        
        # Yanıt uzunluğu
        word_count = len(response.split())
        
        if word_count >= 50:
            score += 0.2
        if word_count >= 100:
            score += 0.1
        if word_count >= 200:
            score += 0.1
        
        # Çoklu soru kontrolü
        if question_count > 1:
            # Her soru için bir cevap var mı?
            answer_indicators = len(re.findall(r'^\d+\.|^-|^•|#{1,3}\s', response, re.MULTILINE))
            if answer_indicators >= question_count - 1:
                score += 0.1
            else:
                score -= 0.1
                issues.append("Tüm sorular yanıtlanmamış olabilir")
        
        # Sonuç/özet var mı?
        has_conclusion = any(kw in response_lower for kw in 
            ["sonuç", "özet", "özetle", "conclusion", "summary", "in summary"])
        if has_conclusion:
            score += 0.05
        
        score = max(0.2, min(1.0, score))
        
        status = (
            ValidationStatus.PASSED if score >= 0.7 else
            ValidationStatus.WARNING if score >= 0.5 else
            ValidationStatus.FAILED
        )
        
        return ValidationCheck(
            dimension=QualityDimension.COMPLETENESS,
            status=status,
            score=score,
            message=f"Tamlık skoru: {score:.2f}",
            details={"word_count": word_count, "issues": issues}
        )
    
    def _check_accuracy(self, response: str, context: Dict[str, Any]) -> ValidationCheck:
        """Bilgi doğruluğunu kontrol et (halüsinasyon tespiti)."""
        score = 0.7  # Başlangıç
        issues = []
        
        response_lower = response.lower()
        
        # Halüsinasyon pattern kontrolü
        for pattern_type, patterns in self.hallucination_patterns.items():
            for pattern in patterns:
                if re.search(pattern, response_lower):
                    if pattern_type == "made_up_facts":
                        # Eğer kaynak belirtilmemişse risk
                        if not re.search(r'\[.*?\]', response):
                            score -= 0.1
                            issues.append(f"Kaynaksız iddia: '{pattern}'")
                    elif pattern_type == "false_certainty":
                        score -= 0.05
                        issues.append(f"Aşırı kesinlik ifadesi")
                    elif pattern_type == "vague_sources":
                        score -= 0.05
                        issues.append(f"Belirsiz kaynak referansı")
        
        # RAG context varsa, yanıtın context'le uyumunu kontrol et
        if context.get("rag_results"):
            rag_content = " ".join(
                r.get("document", r.get("content", "")) 
                for r in context["rag_results"]
            ).lower()
            
            # Yanıttaki önemli ifadeler context'te var mı?
            response_sentences = response.split(".")
            verified_count = 0
            for sent in response_sentences[:5]:  # İlk 5 cümle
                sent_words = set(sent.lower().split())
                if len(sent_words & set(rag_content.split())) > 3:
                    verified_count += 1
            
            if len(response_sentences) > 0:
                verification_ratio = verified_count / min(5, len(response_sentences))
                score = score * 0.7 + verification_ratio * 0.3
        
        score = max(0.2, min(1.0, score))
        
        status = (
            ValidationStatus.PASSED if score >= 0.7 else
            ValidationStatus.WARNING if score >= 0.5 else
            ValidationStatus.FAILED
        )
        
        return ValidationCheck(
            dimension=QualityDimension.ACCURACY,
            status=status,
            score=score,
            message=f"Doğruluk skoru: {score:.2f}",
            details={"issues": issues[:3]}
        )
    
    def _check_formatting(self, response: str) -> ValidationCheck:
        """Markdown formatlamasını kontrol et."""
        score = 0.5
        features = []
        
        # Başlıklar
        headers = re.findall(self.quality_patterns["markdown_headers"], response, re.MULTILINE)
        if headers:
            score += 0.1
            features.append(f"{len(headers)} başlık")
        
        # Kod blokları
        code_blocks = re.findall(self.quality_patterns["code_blocks"], response)
        if code_blocks:
            score += 0.1
            features.append(f"{len(code_blocks)} kod bloğu")
        
        # Listeler
        lists = re.findall(self.quality_patterns["lists"], response, re.MULTILINE)
        if lists:
            score += 0.1
            features.append(f"{len(lists)} liste öğesi")
        
        # Vurgular
        emphasis = re.findall(self.quality_patterns["emphasis"], response)
        if emphasis:
            score += 0.05
            features.append("vurgular")
        
        # Matematiksel ifadeler
        math = re.findall(self.quality_patterns["math"], response)
        if math:
            score += 0.1
            features.append(f"{len(math)} formül")
        
        # Inline code
        inline_code = re.findall(self.quality_patterns["inline_code"], response)
        if inline_code:
            score += 0.05
            features.append("inline kod")
        
        score = max(0.3, min(1.0, score))
        
        status = (
            ValidationStatus.PASSED if score >= 0.7 else
            ValidationStatus.WARNING if score >= 0.5 else
            ValidationStatus.FAILED
        )
        
        return ValidationCheck(
            dimension=QualityDimension.FORMATTING,
            status=status,
            score=score,
            message=f"Format skoru: {score:.2f}",
            details={"features": features}
        )
    
    def _check_citations(self, response: str, context: Dict[str, Any]) -> ValidationCheck:
        """Kaynak kullanımını kontrol et."""
        citations = re.findall(self.quality_patterns["citations"], response)
        
        has_sources = bool(context.get("rag_results") or context.get("web_results"))
        
        if not has_sources:
            # Kaynak yoksa, citation beklenmez
            return ValidationCheck(
                dimension=QualityDimension.CITATIONS,
                status=ValidationStatus.PASSED,
                score=0.8,
                message="Kaynak beklenmedi (context yok)",
                details={"citations_found": len(citations)}
            )
        
        # Kaynak varsa, citation kullanılmalı
        if citations:
            score = min(1.0, 0.5 + len(citations) * 0.1)
            status = ValidationStatus.PASSED
            message = f"{len(citations)} kaynak referansı bulundu"
        else:
            score = 0.3
            status = ValidationStatus.WARNING
            message = "Kaynak referansı eksik"
        
        return ValidationCheck(
            dimension=QualityDimension.CITATIONS,
            status=status,
            score=score,
            message=message,
            details={"citations_found": len(citations), "citations_expected": has_sources}
        )
    
    def _check_coherence(self, response: str) -> ValidationCheck:
        """Yanıtın tutarlılığını kontrol et."""
        score = 0.7
        issues = []
        
        # Paragraf yapısı
        paragraphs = [p.strip() for p in response.split("\n\n") if p.strip()]
        
        if len(paragraphs) < 2 and len(response.split()) > 100:
            score -= 0.1
            issues.append("Paragraf bölümlemesi eksik")
        
        # Çelişkili ifadeler (basit kontrol)
        contradiction_pairs = [
            ("her zaman", "asla"),
            ("kesinlikle", "belki"),
            ("evet", "hayır"),
            ("always", "never"),
            ("definitely", "maybe"),
        ]
        
        response_lower = response.lower()
        for word1, word2 in contradiction_pairs:
            if word1 in response_lower and word2 in response_lower:
                # Aynı cümlede mi kontrol et
                for sentence in response.split("."):
                    if word1 in sentence.lower() and word2 in sentence.lower():
                        score -= 0.1
                        issues.append(f"Olası çelişki: {word1} vs {word2}")
                        break
        
        # Yarım kalan cümleler
        if response.rstrip()[-1:] not in ".!?\"')":
            score -= 0.15
            issues.append("Yanıt yarım kalmış olabilir")
        
        score = max(0.3, min(1.0, score))
        
        status = (
            ValidationStatus.PASSED if score >= 0.7 else
            ValidationStatus.WARNING if score >= 0.5 else
            ValidationStatus.FAILED
        )
        
        return ValidationCheck(
            dimension=QualityDimension.COHERENCE,
            status=status,
            score=score,
            message=f"Tutarlılık skoru: {score:.2f}",
            details={"issues": issues, "paragraph_count": len(paragraphs)}
        )
    
    def _calculate_total_score(self, checks: List[ValidationCheck]) -> float:
        """Toplam skoru hesapla."""
        total = 0.0
        weight_sum = 0.0
        
        for check in checks:
            weight = self.DIMENSION_WEIGHTS.get(check.dimension, 0.1)
            total += check.score * weight
            weight_sum += weight
        
        return total / weight_sum if weight_sum > 0 else 0.5
    
    def _generate_suggestions(self, checks: List[ValidationCheck]) -> List[str]:
        """İyileştirme önerileri oluştur."""
        suggestions = []
        
        for check in checks:
            if check.status != ValidationStatus.PASSED:
                if check.dimension == QualityDimension.RELEVANCE:
                    suggestions.append("Yanıtı soruyla daha alakalı hale getir")
                elif check.dimension == QualityDimension.COMPLETENESS:
                    suggestions.append("Yanıtı daha kapsamlı yap, tüm soruları yanıtla")
                elif check.dimension == QualityDimension.ACCURACY:
                    suggestions.append("Kaynak belirt, kesinlik ifadelerini yumuşat")
                elif check.dimension == QualityDimension.FORMATTING:
                    suggestions.append("Markdown formatlaması ekle (başlık, liste, kod bloğu)")
                elif check.dimension == QualityDimension.CITATIONS:
                    suggestions.append("Kullandığın bilgilerin kaynaklarını belirt")
                elif check.dimension == QualityDimension.COHERENCE:
                    suggestions.append("Yanıtı paragrafla, tutarlılığı kontrol et")
        
        return suggestions[:3]  # En fazla 3 öneri


# ============================================================================
# CONFIDENCE SCORER
# ============================================================================

class ConfidenceScorer:
    """
    Yanıt güvenilirlik skorlayıcı.
    
    Faktörler:
    - Source quality (kaynak kalitesi)
    - Source coverage (kaynak kapsamı)
    - Internal consistency (iç tutarlılık)
    - Claim verifiability (iddiaların doğrulanabilirliği)
    - Uncertainty language (belirsizlik ifadeleri)
    """
    
    FACTORS = {
        "source_quality": 0.30,
        "source_coverage": 0.25,
        "internal_consistency": 0.20,
        "claim_verifiability": 0.15,
        "uncertainty_language": 0.10,
    }
    
    def score(self, response: str, context: Dict[str, Any]) -> ConfidenceResult:
        """
        Yanıt güvenilirliğini skorla.
        
        Args:
            response: LLM yanıtı
            context: Bağlam bilgileri
            
        Returns:
            ConfidenceResult
        """
        breakdown = {}
        factors = []
        
        # 1. Source quality
        breakdown["source_quality"] = self._score_source_quality(context)
        if breakdown["source_quality"] >= 0.7:
            factors.append("Yüksek kaliteli kaynaklar kullanıldı")
        
        # 2. Source coverage
        breakdown["source_coverage"] = self._score_source_coverage(response, context)
        if breakdown["source_coverage"] >= 0.7:
            factors.append("Yanıt kaynaklar tarafından destekleniyor")
        
        # 3. Internal consistency
        breakdown["internal_consistency"] = self._score_consistency(response)
        if breakdown["internal_consistency"] >= 0.7:
            factors.append("Yanıt tutarlı")
        
        # 4. Claim verifiability
        breakdown["claim_verifiability"] = self._score_verifiability(response)
        if breakdown["claim_verifiability"] >= 0.7:
            factors.append("İddialar doğrulanabilir")
        
        # 5. Uncertainty language
        breakdown["uncertainty_language"] = self._score_uncertainty(response)
        if breakdown["uncertainty_language"] >= 0.7:
            factors.append("Uygun belirsizlik ifadeleri")
        
        # Calculate overall
        overall = sum(
            breakdown[factor] * weight
            for factor, weight in self.FACTORS.items()
        )
        
        # Recommendation
        if overall >= 0.8:
            recommendation = "Yüksek güvenilirlik - yanıt güvenilir"
        elif overall >= 0.6:
            recommendation = "Orta güvenilirlik - doğrulama önerilir"
        elif overall >= 0.4:
            recommendation = "Düşük güvenilirlik - dikkatli kullanın"
        else:
            recommendation = "Çok düşük güvenilirlik - yeniden oluşturun"
        
        return ConfidenceResult(
            overall=round(overall, 2),
            breakdown={k: round(v, 2) for k, v in breakdown.items()},
            recommendation=recommendation,
            factors=factors,
        )
    
    def _score_source_quality(self, context: Dict[str, Any]) -> float:
        """Kaynak kalitesini skorla."""
        if not context.get("rag_results") and not context.get("web_results"):
            return 0.5  # Kaynak yok, orta skor
        
        score = 0.6
        
        # RAG sonuçları
        rag_results = context.get("rag_results", [])
        if rag_results:
            avg_relevance = sum(
                r.get("relevance_score", r.get("score", 0.5))
                for r in rag_results
            ) / len(rag_results)
            score = max(score, avg_relevance)
        
        # Web sonuçları
        web_results = context.get("web_results", [])
        if web_results:
            # Web kaynaklarının güvenilirliği
            trusted_domains = [".edu", ".gov", "wikipedia", "arxiv"]
            trusted_count = sum(
                1 for r in web_results
                if any(td in r.get("url", "").lower() for td in trusted_domains)
            )
            if trusted_count > 0:
                score += 0.1 * min(trusted_count, 3)
        
        return min(1.0, score)
    
    def _score_source_coverage(self, response: str, context: Dict[str, Any]) -> float:
        """Kaynak kapsamını skorla."""
        if not context.get("rag_results"):
            return 0.5
        
        # Kaynaklardan gelen içerik
        source_content = " ".join(
            r.get("document", r.get("content", ""))
            for r in context.get("rag_results", [])
        ).lower()
        
        if not source_content:
            return 0.5
        
        # Yanıttaki önemli kelimelerin kaynakta bulunma oranı
        response_words = set(response.lower().split())
        # Stopwords çıkar
        stopwords = {"bir", "bu", "ve", "için", "de", "da", "the", "a", "an", "is", "are", "ve", "ile"}
        meaningful_words = response_words - stopwords
        
        covered = sum(1 for w in meaningful_words if w in source_content)
        
        if meaningful_words:
            coverage = covered / len(meaningful_words)
            return min(1.0, 0.3 + coverage * 0.7)
        
        return 0.5
    
    def _score_consistency(self, response: str) -> float:
        """İç tutarlılığı skorla."""
        score = 0.8
        
        response_lower = response.lower()
        
        # Çelişkili ifadeler
        contradiction_pairs = [
            ("her zaman", "asla"),
            ("kesinlikle", "belki"),
            ("always", "never"),
        ]
        
        for word1, word2 in contradiction_pairs:
            if word1 in response_lower and word2 in response_lower:
                score -= 0.15
        
        # Yarım cümle kontrolü
        if response.rstrip()[-1:] not in ".!?\"')":
            score -= 0.1
        
        return max(0.3, score)
    
    def _score_verifiability(self, response: str) -> float:
        """İddiaların doğrulanabilirliğini skorla."""
        score = 0.6
        
        # Citation sayısı
        citations = len(re.findall(r'\[.*?\]|\[\d+\]', response))
        score += citations * 0.05
        
        # Spesifik sayılar ve tarihler
        has_specifics = bool(re.search(r'\d{4}|\d+%|\d+\.\d+', response))
        if has_specifics:
            score += 0.1
        
        return min(1.0, score)
    
    def _score_uncertainty(self, response: str) -> float:
        """Belirsizlik ifadelerinin uygunluğunu skorla."""
        response_lower = response.lower()
        
        # Aşırı kesinlik kötü
        certainty_words = ["kesinlikle", "absolutely", "definitely", "100%", "always", "never"]
        certainty_count = sum(1 for w in certainty_words if w in response_lower)
        
        # Uygun belirsizlik iyi
        uncertainty_words = ["belki", "muhtemelen", "olabilir", "genellikle", "çoğunlukla", 
                           "maybe", "probably", "possibly", "generally", "usually"]
        uncertainty_count = sum(1 for w in uncertainty_words if w in response_lower)
        
        score = 0.7
        score -= certainty_count * 0.1
        score += uncertainty_count * 0.05
        
        return max(0.2, min(1.0, score))


# ============================================================================
# SELF-REFLECTION AGENT
# ============================================================================

class SelfReflectionAgent:
    """
    Yanıtları değerlendiren ve iyileştiren agent.
    
    Features:
    - Otomatik iyileştirme önerileri
    - Düşük skorlu yanıtlar için prompt oluşturma
    - Iteratif iyileştirme döngüsü
    """
    
    REFLECTION_PROMPT = """
Aşağıdaki soruya verdiğin yanıtı değerlendir:

**SORU:** {query}

**YANITIM:**
{response}

**DEĞERLENDİRME SONUÇLARI:**
{validation_summary}

**KONTROL LİSTESİ:**
1. ✅/❌ Soru tam ve doğru yanıtlandı mı?
2. ✅/❌ Bilgiler doğru ve doğrulanabilir mi?
3. ✅/❌ Kaynaklara referans verildi mi?
4. ✅/❌ Format uygun mu (başlık, liste, kod)?
5. ✅/❌ Yanıt tutarlı ve mantıklı mı?

**GÖREV:**
Eğer yukarıdaki kontrollerden herhangi biri ❌ ise, yanıtı iyileştir.
Yoksa, yanıtı olduğu gibi bırak.

**İYİLEŞTİRİLMİŞ YANIT:**
"""
    
    def __init__(self):
        self.validator = ResponseValidator()
    
    def should_reflect(self, validation_result: ValidationResult) -> bool:
        """
        Reflection gerekli mi?
        
        Args:
            validation_result: Doğrulama sonucu
            
        Returns:
            Reflection gerekli mi
        """
        return (
            validation_result.overall_status != ValidationStatus.PASSED or
            validation_result.overall_score < 0.75
        )
    
    def create_reflection_prompt(
        self,
        query: str,
        response: str,
        validation_result: ValidationResult,
    ) -> str:
        """
        Reflection prompt'u oluştur.
        
        Args:
            query: Orijinal soru
            response: Mevcut yanıt
            validation_result: Doğrulama sonucu
            
        Returns:
            Reflection prompt
        """
        # Validation özeti
        summary_lines = []
        for check in validation_result.checks:
            status_emoji = "✅" if check.status == ValidationStatus.PASSED else "⚠️" if check.status == ValidationStatus.WARNING else "❌"
            summary_lines.append(f"- {status_emoji} {check.dimension.value}: {check.score:.2f} - {check.message}")
        
        validation_summary = "\n".join(summary_lines)
        
        # Öneriler
        if validation_result.suggestions:
            validation_summary += "\n\n**ÖNERİLER:**\n" + "\n".join(f"- {s}" for s in validation_result.suggestions)
        
        return self.REFLECTION_PROMPT.format(
            query=query,
            response=response,
            validation_summary=validation_summary,
        )
    
    def reflect_and_improve(
        self,
        query: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
        max_iterations: int = 1,
    ) -> Tuple[str, List[ValidationResult]]:
        """
        Yanıtı değerlendir ve gerekirse iyileştir.
        
        Args:
            query: Orijinal soru
            response: Mevcut yanıt
            context: Bağlam
            max_iterations: Maksimum iyileştirme turu
            
        Returns:
            (improved_response, validation_history)
        """
        validation_history = []
        current_response = response
        
        for i in range(max_iterations + 1):
            # Doğrula
            result = self.validator.validate(query, current_response, context)
            validation_history.append(result)
            
            # Yeterince iyi mi veya son iterasyon mu?
            if not self.should_reflect(result) or i == max_iterations:
                break
            
            # İyileştirme prompt'u oluştur (LLM çağrısı dışarıda yapılmalı)
            # Bu metod sadece prompt döndürür, çağıran kod LLM'i çağırmalı
            logger.info(f"Reflection iteration {i+1}: score={result.overall_score:.2f}")
        
        return current_response, validation_history
    
    def get_improvement_priorities(self, validation_result: ValidationResult) -> List[str]:
        """
        İyileştirme önceliklerini al.
        
        Args:
            validation_result: Doğrulama sonucu
            
        Returns:
            Öncelik sırasına göre iyileştirme alanları
        """
        # Skora göre sırala (düşük skorlular önce)
        sorted_checks = sorted(
            validation_result.checks,
            key=lambda c: c.score
        )
        
        priorities = []
        for check in sorted_checks:
            if check.score < 0.7:
                priorities.append(f"{check.dimension.value}: {check.message}")
        
        return priorities[:3]


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

response_validator = ResponseValidator()
confidence_scorer = ConfidenceScorer()
self_reflection_agent = SelfReflectionAgent()


__all__ = [
    "ResponseValidator",
    "ConfidenceScorer",
    "SelfReflectionAgent",
    "ValidationResult",
    "ValidationCheck",
    "ValidationStatus",
    "QualityDimension",
    "ConfidenceResult",
    "response_validator",
    "confidence_scorer",
    "self_reflection_agent",
]
