"""
QualityScorer - Kapsamlı Kalite Puanlama Modülü
===============================================

Tüm kalite boyutlarını bir araya getirir:
1. Okunabilirlik
2. Tutarlılık
3. İntihal kontrolü
4. Perspektif çeşitliliği
5. Akademik standartlar
"""

import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from .plagiarism_detector import PlagiarismDetector, PlagiarismReport
from .readability_analyzer import ReadabilityAnalyzer, ReadabilityReport, AudienceType
from .consistency_checker import ConsistencyChecker, ConsistencyReport
from .bias_analyzer import BiasAnalyzer, BiasReport


class QualityGrade(str, Enum):
    """Kalite notu."""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class DimensionScore:
    """Boyut puanı."""
    name: str
    score: float  # 0-100
    weight: float
    weighted_score: float
    grade: str
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityScore:
    """Kapsamlı kalite puanı."""
    overall_score: float
    grade: QualityGrade
    
    # Boyut puanları
    dimensions: List[DimensionScore]
    
    # Alt raporlar
    readability_report: Optional[ReadabilityReport] = None
    consistency_report: Optional[ConsistencyReport] = None
    plagiarism_report: Optional[PlagiarismReport] = None
    bias_report: Optional[BiasReport] = None
    
    # Özet
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade.value,
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 1),
                    "grade": d.grade
                }
                for d in self.dimensions
            ],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations
        }
    
    def to_markdown(self) -> str:
        lines = [
            "# 📊 Kapsamlı Kalite Değerlendirmesi",
            "",
            f"## Genel Puan: {round(self.overall_score)}/100 ({self.grade.value})",
            "",
            "---",
            "",
            "## Boyut Puanları",
            ""
        ]
        
        # Boyut tablosu
        lines.append("| Boyut | Puan | Not | Özet |")
        lines.append("|-------|------|-----|------|")
        for d in self.dimensions:
            lines.append(f"| {d.name} | {round(d.score)} | {d.grade} | {d.summary[:50]}... |")
        
        lines.append("")
        
        # Güçlü yönler
        if self.strengths:
            lines.extend(["## ✅ Güçlü Yönler", ""])
            for s in self.strengths:
                lines.append(f"- {s}")
            lines.append("")
        
        # Zayıf yönler
        if self.weaknesses:
            lines.extend(["## ⚠️ İyileştirme Alanları", ""])
            for w in self.weaknesses:
                lines.append(f"- {w}")
            lines.append("")
        
        # Öneriler
        if self.recommendations:
            lines.extend(["## 💡 Öneriler", ""])
            for r in self.recommendations:
                lines.append(f"- {r}")
        
        return "\n".join(lines)


class QualityScorer:
    """
    Kapsamlı Kalite Puanlama Modülü
    
    Tüm kalite boyutlarını değerlendirir ve tek bir puan üretir.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Alt modüller
        self.readability_analyzer = ReadabilityAnalyzer(config)
        self.consistency_checker = ConsistencyChecker(config)
        self.plagiarism_detector = PlagiarismDetector(config)
        self.bias_analyzer = BiasAnalyzer(config)
        
        # Boyut ağırlıkları (toplam = 1.0)
        self.dimension_weights = {
            "readability": 0.20,
            "consistency": 0.20,
            "originality": 0.25,
            "balance": 0.15,
            "structure": 0.10,
            "academic": 0.10
        }
    
    async def evaluate_document(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        target_audience: AudienceType = AudienceType.ACADEMIC
    ) -> QualityScore:
        """
        Dokümanı kapsamlı değerlendir.
        
        Args:
            content: Doküman içeriği
            sources: Kullanılan kaynaklar
            target_audience: Hedef kitle
            
        Returns:
            Kapsamlı kalite puanı
        """
        dimensions: List[DimensionScore] = []
        
        # Paralel analiz
        tasks = [
            self._evaluate_readability(content, target_audience),
            self._evaluate_consistency(content),
            self._evaluate_originality(content, sources),
            self._evaluate_balance(content, sources),
            self._evaluate_structure(content),
            self._evaluate_academic_standards(content)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Sonuçları topla
        readability_score, readability_report = results[0] if not isinstance(results[0], Exception) else (70, None)
        consistency_score, consistency_report = results[1] if not isinstance(results[1], Exception) else (70, None)
        originality_score, plagiarism_report = results[2] if not isinstance(results[2], Exception) else (80, None)
        balance_score, bias_report = results[3] if not isinstance(results[3], Exception) else (75, None)
        structure_score, _ = results[4] if not isinstance(results[4], Exception) else (70, None)
        academic_score, _ = results[5] if not isinstance(results[5], Exception) else (70, None)
        
        # Boyut skorları
        dimensions = [
            DimensionScore(
                name="Okunabilirlik",
                score=readability_score,
                weight=self.dimension_weights["readability"],
                weighted_score=readability_score * self.dimension_weights["readability"],
                grade=self._score_to_grade(readability_score),
                summary="Metin okunabilirliği ve akıcılığı",
                details={"report": readability_report}
            ),
            DimensionScore(
                name="Tutarlılık",
                score=consistency_score,
                weight=self.dimension_weights["consistency"],
                weighted_score=consistency_score * self.dimension_weights["consistency"],
                grade=self._score_to_grade(consistency_score),
                summary="Terminoloji ve stil tutarlılığı",
                details={"report": consistency_report}
            ),
            DimensionScore(
                name="Özgünlük",
                score=originality_score,
                weight=self.dimension_weights["originality"],
                weighted_score=originality_score * self.dimension_weights["originality"],
                grade=self._score_to_grade(originality_score),
                summary="İçerik orijinalliği ve intihal kontrolü",
                details={"report": plagiarism_report}
            ),
            DimensionScore(
                name="Perspektif Dengesi",
                score=balance_score,
                weight=self.dimension_weights["balance"],
                weighted_score=balance_score * self.dimension_weights["balance"],
                grade=self._score_to_grade(balance_score),
                summary="Bakış açısı çeşitliliği ve denge",
                details={"report": bias_report}
            ),
            DimensionScore(
                name="Yapı",
                score=structure_score,
                weight=self.dimension_weights["structure"],
                weighted_score=structure_score * self.dimension_weights["structure"],
                grade=self._score_to_grade(structure_score),
                summary="Bölüm organizasyonu ve akış"
            ),
            DimensionScore(
                name="Akademik Standartlar",
                score=academic_score,
                weight=self.dimension_weights["academic"],
                weighted_score=academic_score * self.dimension_weights["academic"],
                grade=self._score_to_grade(academic_score),
                summary="Akademik yazım kurallarına uyum"
            )
        ]
        
        # Genel puan
        overall_score = sum(d.weighted_score for d in dimensions)
        grade = self._score_to_quality_grade(overall_score)
        
        # Güçlü ve zayıf yönler
        strengths, weaknesses = self._identify_strengths_weaknesses(dimensions)
        
        # Öneriler
        recommendations = self._generate_recommendations(dimensions)
        
        return QualityScore(
            overall_score=overall_score,
            grade=grade,
            dimensions=dimensions,
            readability_report=readability_report,
            consistency_report=consistency_report,
            plagiarism_report=plagiarism_report,
            bias_report=bias_report,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    async def _evaluate_readability(
        self,
        content: str,
        target_audience: AudienceType
    ) -> tuple:
        """Okunabilirlik değerlendir."""
        report = self.readability_analyzer.analyze(content, target_audience)
        score = report.metrics.flesch_reading_ease
        
        # Akademik içerik için ayarlama
        if target_audience == AudienceType.ACADEMIC:
            # Akademik metinler için 30-60 arası idealdir
            if 30 <= score <= 60:
                adjusted_score = 85 + (score - 30) / 3
            elif score < 30:
                adjusted_score = 70 + score  # Çok zor
            else:
                adjusted_score = 80 - (score - 60) / 2  # Çok kolay
            score = min(100, max(0, adjusted_score))
        
        return score, report
    
    async def _evaluate_consistency(
        self,
        content: str
    ) -> tuple:
        """Tutarlılık değerlendir."""
        report = await self.consistency_checker.check_document(content)
        return report.overall_score, report
    
    async def _evaluate_originality(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]]
    ) -> tuple:
        """Özgünlük değerlendir."""
        report = await self.plagiarism_detector.check_document(content, sources)
        
        # Benzerlik düşükse puan yüksek
        score = (1 - report.overall_similarity) * 100
        
        return score, report
    
    async def _evaluate_balance(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]]
    ) -> tuple:
        """Perspektif dengesi değerlendir."""
        report = await self.bias_analyzer.analyze_document(content, sources)
        return report.overall_score, report
    
    async def _evaluate_structure(
        self,
        content: str
    ) -> tuple:
        """Yapı değerlendir."""
        score = 70.0
        
        # Bölüm başlıkları kontrolü
        headers = len([line for line in content.split('\n') if line.startswith('#')])
        if headers >= 5:
            score += 15
        elif headers >= 3:
            score += 10
        
        # Paragraf uzunluğu kontrolü
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        avg_para_length = sum(len(p.split()) for p in paragraphs) / max(len(paragraphs), 1)
        if 50 <= avg_para_length <= 200:
            score += 10
        
        # Liste kullanımı
        if '- ' in content or '1. ' in content:
            score += 5
        
        return min(100, score), None
    
    async def _evaluate_academic_standards(
        self,
        content: str
    ) -> tuple:
        """Akademik standartlar değerlendir."""
        score = 70.0
        
        # Referans kullanımı
        ref_patterns = [
            r'\([^)]+\d{4}\)',  # APA
            r'\[\d+\]'          # IEEE
        ]
        has_refs = any(len([m for m in __import__('re').findall(p, content)]) > 0 for p in ref_patterns)
        if has_refs:
            score += 15
        
        # Akademik kelime dağarcığı
        academic_words = [
            "analiz", "değerlendirme", "metodoloji", "bulgular",
            "sonuç", "tartışma", "literatür", "hipotez"
        ]
        word_count = sum(1 for w in academic_words if w in content.lower())
        score += min(word_count * 2, 10)
        
        # Kaynak bölümü
        if "kaynakça" in content.lower() or "referans" in content.lower():
            score += 5
        
        return min(100, score), None
    
    def _score_to_grade(self, score: float) -> str:
        """Puanı nota çevir."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _score_to_quality_grade(self, score: float) -> QualityGrade:
        """Puanı kalite notuna çevir."""
        if score >= 95:
            return QualityGrade.A_PLUS
        elif score >= 90:
            return QualityGrade.A
        elif score >= 85:
            return QualityGrade.B_PLUS
        elif score >= 80:
            return QualityGrade.B
        elif score >= 75:
            return QualityGrade.C_PLUS
        elif score >= 70:
            return QualityGrade.C
        elif score >= 60:
            return QualityGrade.D
        else:
            return QualityGrade.F
    
    def _identify_strengths_weaknesses(
        self,
        dimensions: List[DimensionScore]
    ) -> tuple:
        """Güçlü ve zayıf yönleri belirle."""
        strengths = []
        weaknesses = []
        
        for d in dimensions:
            if d.score >= 85:
                strengths.append(f"Yüksek {d.name.lower()} kalitesi ({d.grade})")
            elif d.score < 70:
                weaknesses.append(f"{d.name} iyileştirme gerektirir ({d.grade})")
        
        return strengths, weaknesses
    
    def _generate_recommendations(
        self,
        dimensions: List[DimensionScore]
    ) -> List[str]:
        """Öneriler oluştur."""
        recommendations = []
        
        # En düşük puanlı boyutlar için öneri
        sorted_dims = sorted(dimensions, key=lambda d: d.score)
        
        for d in sorted_dims[:2]:
            if d.score < 80:
                if d.name == "Okunabilirlik":
                    recommendations.append("Cümle uzunluklarını gözden geçirin ve karmaşık ifadeleri sadeleştirin")
                elif d.name == "Tutarlılık":
                    recommendations.append("Terim kullanımını standartlaştırın ve stil kılavuzu oluşturun")
                elif d.name == "Özgünlük":
                    recommendations.append("Alıntıları uygun şekilde kaynak gösterin veya yeniden ifade edin")
                elif d.name == "Perspektif Dengesi":
                    recommendations.append("Farklı bakış açılarını içerikten çıkarmadan, alternatif görüşler ekleyin")
                elif d.name == "Yapı":
                    recommendations.append("Bölüm başlıkları ekleyin ve içeriği daha iyi organize edin")
                elif d.name == "Akademik Standartlar":
                    recommendations.append("Referans kullanımını artırın ve akademik terminolojiye dikkat edin")
        
        return recommendations
