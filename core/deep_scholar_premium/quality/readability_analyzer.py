"""
ReadabilityAnalyzer - Okunabilirlik Analiz Modülü
=================================================

Metrikler:
1. Flesch Reading Ease
2. Flesch-Kincaid Grade Level
3. SMOG Index
4. Coleman-Liau Index
5. Automated Readability Index (ARI)
6. Gunning Fog Index
7. Türkçe okunabilirlik metrikleri
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ReadabilityLevel(str, Enum):
    """Okunabilirlik seviyesi."""
    VERY_EASY = "very_easy"       # İlkokul
    EASY = "easy"                 # Ortaokul
    FAIRLY_EASY = "fairly_easy"  # Lise başlangıç
    STANDARD = "standard"        # Lise
    FAIRLY_DIFFICULT = "fairly_difficult"  # Üniversite
    DIFFICULT = "difficult"      # Yüksek lisans
    VERY_DIFFICULT = "very_difficult"  # Akademik/Teknik


class AudienceType(str, Enum):
    """Hedef kitle."""
    GENERAL = "general"
    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    STUDENT = "student"
    EXPERT = "expert"


@dataclass
class ReadabilityMetrics:
    """Okunabilirlik metrikleri."""
    # Temel metrikler
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    smog_index: float
    coleman_liau_index: float
    ari: float  # Automated Readability Index
    gunning_fog: float
    
    # Türkçe metrikleri
    atesman_score: Optional[float] = None  # Türkçe Flesch
    
    # Ortalamalar
    average_grade_level: float = 0.0
    overall_level: ReadabilityLevel = ReadabilityLevel.STANDARD


@dataclass
class TextStatistics:
    """Metin istatistikleri."""
    total_characters: int
    total_words: int
    total_sentences: int
    total_paragraphs: int
    total_syllables: int
    
    avg_word_length: float
    avg_sentence_length: float
    avg_syllables_per_word: float
    avg_words_per_paragraph: float
    
    complex_word_count: int  # 3+ hece
    complex_word_percentage: float
    
    # Kelime çeşitliliği
    unique_words: int
    type_token_ratio: float


@dataclass
class ReadabilityReport:
    """Okunabilirlik raporu."""
    metrics: ReadabilityMetrics
    statistics: TextStatistics
    level: ReadabilityLevel
    target_audience: AudienceType
    
    # Analiz
    strengths: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    # Bölüm bazlı analiz
    section_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "flesch_reading_ease": round(self.metrics.flesch_reading_ease, 1),
            "flesch_kincaid_grade": round(self.metrics.flesch_kincaid_grade, 1),
            "smog_index": round(self.metrics.smog_index, 1),
            "level": self.level.value,
            "target_audience": self.target_audience.value,
            "avg_sentence_length": round(self.statistics.avg_sentence_length, 1),
            "avg_word_length": round(self.statistics.avg_word_length, 1),
            "strengths": self.strengths,
            "issues": self.issues,
            "suggestions": self.suggestions
        }
    
    def to_markdown(self) -> str:
        lines = [
            "# 📖 Okunabilirlik Raporu",
            "",
            f"**Genel Seviye:** {self.level.value.replace('_', ' ').title()}",
            f"**Hedef Kitle:** {self.target_audience.value.replace('_', ' ').title()}",
            "",
            "## Metrikler",
            f"- Flesch Reading Ease: {round(self.metrics.flesch_reading_ease, 1)}/100",
            f"- Flesch-Kincaid Grade: {round(self.metrics.flesch_kincaid_grade, 1)}",
            f"- SMOG Index: {round(self.metrics.smog_index, 1)}",
            f"- Gunning Fog: {round(self.metrics.gunning_fog, 1)}",
            "",
            "## İstatistikler",
            f"- Toplam Kelime: {self.statistics.total_words}",
            f"- Toplam Cümle: {self.statistics.total_sentences}",
            f"- Ortalama Cümle Uzunluğu: {round(self.statistics.avg_sentence_length, 1)} kelime",
            f"- Karmaşık Kelime Oranı: %{round(self.statistics.complex_word_percentage, 1)}",
            ""
        ]
        
        if self.strengths:
            lines.extend(["## ✅ Güçlü Yönler", ""])
            for s in self.strengths:
                lines.append(f"- {s}")
            lines.append("")
        
        if self.issues:
            lines.extend(["## ⚠️ İyileştirme Alanları", ""])
            for i in self.issues:
                lines.append(f"- {i}")
            lines.append("")
        
        if self.suggestions:
            lines.extend(["## 💡 Öneriler", ""])
            for s in self.suggestions:
                lines.append(f"- {s}")
        
        return "\n".join(lines)


class ReadabilityAnalyzer:
    """
    Okunabilirlik Analiz Modülü
    
    Çoklu metrik ile metin okunabilirliğini değerlendirir.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.target_audience = AudienceType.ACADEMIC
        
        # Türkçe hece kuralları
        self.turkish_vowels = set("aeıioöuüAEIİOÖUÜ")
    
    def analyze(
        self,
        content: str,
        target_audience: AudienceType = AudienceType.ACADEMIC
    ) -> ReadabilityReport:
        """
        Metni analiz et.
        
        Args:
            content: Analiz edilecek içerik
            target_audience: Hedef kitle
            
        Returns:
            Okunabilirlik raporu
        """
        self.target_audience = target_audience
        
        # İstatistikler
        stats = self._calculate_statistics(content)
        
        # Metrikler
        metrics = self._calculate_metrics(stats)
        
        # Seviye belirleme
        level = self._determine_level(metrics)
        
        # Analiz
        strengths, issues, suggestions = self._analyze_results(
            metrics, stats, target_audience
        )
        
        return ReadabilityReport(
            metrics=metrics,
            statistics=stats,
            level=level,
            target_audience=target_audience,
            strengths=strengths,
            issues=issues,
            suggestions=suggestions
        )
    
    def analyze_by_sections(
        self,
        sections: List[Dict[str, str]]
    ) -> Dict[str, ReadabilityReport]:
        """Bölüm bazlı analiz."""
        results = {}
        
        for section in sections:
            title = section.get("title", "Untitled")
            content = section.get("content", "")
            
            if content.strip():
                results[title] = self.analyze(content)
        
        return results
    
    def _calculate_statistics(self, content: str) -> TextStatistics:
        """Metin istatistiklerini hesapla."""
        # Temizle
        content = content.strip()
        
        # Paragraflar
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Cümleler
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Kelimeler
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Heceler
        total_syllables = sum(self._count_syllables(w) for w in words)
        
        # Karmaşık kelimeler (3+ hece)
        complex_words = [w for w in words if self._count_syllables(w) >= 3]
        
        # Benzersiz kelimeler
        unique_words = set(words)
        
        total_words = len(words)
        total_sentences = len(sentences)
        
        return TextStatistics(
            total_characters=len(content),
            total_words=total_words,
            total_sentences=total_sentences,
            total_paragraphs=len(paragraphs),
            total_syllables=total_syllables,
            avg_word_length=sum(len(w) for w in words) / max(total_words, 1),
            avg_sentence_length=total_words / max(total_sentences, 1),
            avg_syllables_per_word=total_syllables / max(total_words, 1),
            avg_words_per_paragraph=total_words / max(len(paragraphs), 1),
            complex_word_count=len(complex_words),
            complex_word_percentage=(len(complex_words) / max(total_words, 1)) * 100,
            unique_words=len(unique_words),
            type_token_ratio=len(unique_words) / max(total_words, 1)
        )
    
    def _calculate_metrics(self, stats: TextStatistics) -> ReadabilityMetrics:
        """Okunabilirlik metriklerini hesapla."""
        words = stats.total_words
        sentences = max(stats.total_sentences, 1)
        syllables = stats.total_syllables
        complex_words = stats.complex_word_count
        characters = stats.total_characters
        
        # Flesch Reading Ease
        # 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        flesch = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / max(words, 1))
        flesch = max(0, min(100, flesch))
        
        # Flesch-Kincaid Grade Level
        # 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        fk_grade = 0.39 * (words / sentences) + 11.8 * (syllables / max(words, 1)) - 15.59
        fk_grade = max(0, fk_grade)
        
        # SMOG Index
        # 1.0430 * sqrt(polysyllables * 30/sentences) + 3.1291
        smog = 1.0430 * ((complex_words * (30 / sentences)) ** 0.5) + 3.1291
        smog = max(0, smog)
        
        # Coleman-Liau Index
        # 0.0588 * L - 0.296 * S - 15.8
        # L = avg letters per 100 words, S = avg sentences per 100 words
        L = (characters / max(words, 1)) * 100
        S = (sentences / max(words, 1)) * 100
        coleman = 0.0588 * L - 0.296 * S - 15.8
        coleman = max(0, coleman)
        
        # Automated Readability Index
        # 4.71 * (characters/words) + 0.5 * (words/sentences) - 21.43
        ari = 4.71 * (characters / max(words, 1)) + 0.5 * (words / sentences) - 21.43
        ari = max(0, ari)
        
        # Gunning Fog Index
        # 0.4 * ((words/sentences) + 100 * (complex_words/words))
        fog = 0.4 * ((words / sentences) + 100 * (complex_words / max(words, 1)))
        fog = max(0, fog)
        
        # Ateşman Türkçe formülü (Flesch adaptasyonu)
        # 198.825 - 40.175 * (syllables/words) - 2.610 * (words/sentences)
        atesman = 198.825 - 40.175 * (syllables / max(words, 1)) - 2.610 * (words / sentences)
        atesman = max(0, min(100, atesman))
        
        # Ortalama sınıf seviyesi
        avg_grade = (fk_grade + smog + coleman + ari + fog) / 5
        
        # Seviye belirleme
        level = self._determine_level_from_score(flesch)
        
        return ReadabilityMetrics(
            flesch_reading_ease=flesch,
            flesch_kincaid_grade=fk_grade,
            smog_index=smog,
            coleman_liau_index=coleman,
            ari=ari,
            gunning_fog=fog,
            atesman_score=atesman,
            average_grade_level=avg_grade,
            overall_level=level
        )
    
    def _count_syllables(self, word: str) -> int:
        """Hece sayısını hesapla (Türkçe ve İngilizce)."""
        word = word.lower()
        
        # Türkçe: sesli harf sayısı ≈ hece sayısı
        vowels = sum(1 for c in word if c in "aeıioöuü")
        
        if vowels == 0:
            return 1
        
        return vowels
    
    def _determine_level(self, metrics: ReadabilityMetrics) -> ReadabilityLevel:
        """Genel seviye belirle."""
        return metrics.overall_level
    
    def _determine_level_from_score(self, flesch: float) -> ReadabilityLevel:
        """Flesch skorundan seviye belirle."""
        if flesch >= 90:
            return ReadabilityLevel.VERY_EASY
        elif flesch >= 80:
            return ReadabilityLevel.EASY
        elif flesch >= 70:
            return ReadabilityLevel.FAIRLY_EASY
        elif flesch >= 60:
            return ReadabilityLevel.STANDARD
        elif flesch >= 50:
            return ReadabilityLevel.FAIRLY_DIFFICULT
        elif flesch >= 30:
            return ReadabilityLevel.DIFFICULT
        else:
            return ReadabilityLevel.VERY_DIFFICULT
    
    def _analyze_results(
        self,
        metrics: ReadabilityMetrics,
        stats: TextStatistics,
        target: AudienceType
    ) -> Tuple[List[str], List[str], List[str]]:
        """Sonuçları analiz et."""
        strengths = []
        issues = []
        suggestions = []
        
        # Hedef kitleye göre ideal aralıklar
        ideal_ranges = {
            AudienceType.GENERAL: {"flesch": (60, 80), "grade": (6, 10)},
            AudienceType.ACADEMIC: {"flesch": (30, 60), "grade": (12, 16)},
            AudienceType.PROFESSIONAL: {"flesch": (40, 60), "grade": (10, 14)},
            AudienceType.STUDENT: {"flesch": (50, 70), "grade": (8, 12)},
            AudienceType.EXPERT: {"flesch": (20, 50), "grade": (14, 18)}
        }
        
        ideal = ideal_ranges.get(target, ideal_ranges[AudienceType.ACADEMIC])
        
        # Flesch kontrolü
        if ideal["flesch"][0] <= metrics.flesch_reading_ease <= ideal["flesch"][1]:
            strengths.append(f"Okunabilirlik hedef kitle için uygun (Flesch: {round(metrics.flesch_reading_ease)})")
        elif metrics.flesch_reading_ease < ideal["flesch"][0]:
            issues.append("Metin hedef kitle için çok karmaşık olabilir")
            suggestions.append("Cümleleri kısaltın ve daha basit kelimeler kullanın")
        else:
            issues.append("Metin hedef kitle için çok basit olabilir")
            suggestions.append("Akademik terimler ve daha detaylı açıklamalar ekleyin")
        
        # Cümle uzunluğu
        if stats.avg_sentence_length > 25:
            issues.append(f"Cümleler çok uzun (ortalama {round(stats.avg_sentence_length)} kelime)")
            suggestions.append("Uzun cümleleri bölerek daha net ifade edin")
        elif stats.avg_sentence_length < 10 and target == AudienceType.ACADEMIC:
            issues.append("Cümleler akademik yazı için kısa")
            suggestions.append("Daha bağlayıcı ve detaylı cümleler kurun")
        else:
            strengths.append("Cümle uzunluğu dengeli")
        
        # Karmaşık kelime oranı
        if stats.complex_word_percentage > 30:
            issues.append(f"Karmaşık kelime oranı yüksek (%{round(stats.complex_word_percentage)})")
            suggestions.append("Bazı teknik terimleri açıklayın veya sadeleştirin")
        elif stats.complex_word_percentage > 15:
            if target in [AudienceType.ACADEMIC, AudienceType.EXPERT]:
                strengths.append("Akademik terminoloji kullanımı uygun")
            else:
                issues.append("Bazı bölümler genel okuyucu için karmaşık")
        
        # Kelime çeşitliliği
        if stats.type_token_ratio > 0.7:
            strengths.append("Zengin kelime dağarcığı")
        elif stats.type_token_ratio < 0.4:
            issues.append("Kelime tekrarı fazla")
            suggestions.append("Eş anlamlı kelimeler kullanarak çeşitliliği artırın")
        
        return strengths, issues, suggestions
    
    def get_grade_level_description(self, grade: float) -> str:
        """Sınıf seviyesi açıklaması."""
        if grade <= 5:
            return "İlkokul seviyesi"
        elif grade <= 8:
            return "Ortaokul seviyesi"
        elif grade <= 12:
            return "Lise seviyesi"
        elif grade <= 16:
            return "Üniversite seviyesi"
        else:
            return "Yüksek lisans/akademik seviye"
