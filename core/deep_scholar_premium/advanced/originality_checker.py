"""
OriginalityChecker - Orijinallik ve Benzerlik Kontrolü
=======================================================

İçeriğin orijinalliğini kontrol eder, benzerlik indeksi hesaplar.

Özellikler:
- Similarity index hesaplama
- Alıntı vs paraphrase ayrımı
- Self-plagiarism detection
- N-gram analizi
- Semantic similarity
- Originality report PDF
"""

import asyncio
import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from enum import Enum
from collections import Counter
import math

from core.logger import get_logger
from core.llm_manager import llm_manager

logger = get_logger("originality_checker")


class SimilarityType(str, Enum):
    """Benzerlik türü."""
    EXACT_MATCH = "exact_match"
    NEAR_MATCH = "near_match"
    PARAPHRASE = "paraphrase"
    COMMON_KNOWLEDGE = "common_knowledge"
    CITATION = "citation"
    ORIGINAL = "original"


class OriginalityLevel(str, Enum):
    """Orijinallik seviyesi."""
    EXCELLENT = "excellent"      # %90+
    GOOD = "good"                # %75-90
    ACCEPTABLE = "acceptable"    # %60-75
    NEEDS_REVIEW = "needs_review"  # %40-60
    PROBLEMATIC = "problematic"  # <%40


@dataclass
class SimilarityMatch:
    """Benzerlik eşleşmesi."""
    match_id: str
    source_text: str
    matched_text: str
    similarity_score: float
    similarity_type: SimilarityType
    source_info: Optional[str] = None
    position_start: int = 0
    position_end: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "match_id": self.match_id,
            "source_text": self.source_text[:200] + "..." if len(self.source_text) > 200 else self.source_text,
            "matched_text": self.matched_text[:200] + "..." if len(self.matched_text) > 200 else self.matched_text,
            "similarity_score": round(self.similarity_score, 2),
            "similarity_type": self.similarity_type.value,
            "source_info": self.source_info,
            "position": f"{self.position_start}-{self.position_end}"
        }


@dataclass
class OriginalityReport:
    """Orijinallik raporu."""
    document_id: str
    document_title: str
    
    # Scores
    overall_originality: float
    originality_level: OriginalityLevel
    
    # Breakdowns
    exact_match_percentage: float
    paraphrase_percentage: float
    citation_percentage: float
    original_percentage: float
    
    # Matches
    similarity_matches: List[SimilarityMatch]
    
    # Statistics
    total_words: int
    unique_phrases: int
    flagged_sections: List[str]
    
    # Recommendations
    recommendations: List[str]
    
    # Metadata
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_duration_seconds: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "document_id": self.document_id,
            "document_title": self.document_title,
            "overall_originality": round(self.overall_originality, 1),
            "originality_level": self.originality_level.value,
            "breakdown": {
                "exact_match": round(self.exact_match_percentage, 1),
                "paraphrase": round(self.paraphrase_percentage, 1),
                "citation": round(self.citation_percentage, 1),
                "original": round(self.original_percentage, 1)
            },
            "total_words": self.total_words,
            "unique_phrases": self.unique_phrases,
            "flagged_sections": self.flagged_sections,
            "match_count": len(self.similarity_matches),
            "top_matches": [m.to_dict() for m in self.similarity_matches[:10]],
            "recommendations": self.recommendations,
            "timestamp": self.analysis_timestamp,
            "duration_seconds": round(self.analysis_duration_seconds, 2)
        }
    
    def get_summary(self) -> str:
        """Özet metin oluştur."""
        level_emoji = {
            OriginalityLevel.EXCELLENT: "🌟",
            OriginalityLevel.GOOD: "✅",
            OriginalityLevel.ACCEPTABLE: "⚠️",
            OriginalityLevel.NEEDS_REVIEW: "🔶",
            OriginalityLevel.PROBLEMATIC: "🔴"
        }
        
        emoji = level_emoji.get(self.originality_level, "📊")
        
        return f"""{emoji} Orijinallik Skoru: %{self.overall_originality:.1f}
📝 Toplam Kelime: {self.total_words}
🔍 Tespit Edilen Eşleşme: {len(self.similarity_matches)}
📚 Atıf Oranı: %{self.citation_percentage:.1f}
✨ Orijinal İçerik: %{self.original_percentage:.1f}"""


class NGramAnalyzer:
    """N-gram bazlı metin analizi."""
    
    def __init__(self, n: int = 5):
        self.n = n
    
    def extract_ngrams(self, text: str) -> Set[str]:
        """Metinden n-gram'ları çıkar."""
        # Temizle
        words = re.findall(r'\b\w+\b', text.lower())
        
        if len(words) < self.n:
            return set()
        
        ngrams = set()
        for i in range(len(words) - self.n + 1):
            ngram = " ".join(words[i:i + self.n])
            ngrams.add(ngram)
        
        return ngrams
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """İki metin arasındaki n-gram benzerliğini hesapla."""
        ngrams1 = self.extract_ngrams(text1)
        ngrams2 = self.extract_ngrams(text2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = ngrams1.intersection(ngrams2)
        union = ngrams1.union(ngrams2)
        
        # Jaccard similarity
        return len(intersection) / len(union) if union else 0.0
    
    def find_matching_phrases(
        self,
        target: str,
        source: str,
        min_length: int = 5
    ) -> List[Tuple[str, int, int]]:
        """Eşleşen ifadeleri bul."""
        target_words = re.findall(r'\b\w+\b', target.lower())
        source_lower = source.lower()
        
        matches = []
        
        for length in range(min_length, min(len(target_words), 20)):
            for i in range(len(target_words) - length + 1):
                phrase = " ".join(target_words[i:i + length])
                
                if phrase in source_lower:
                    # Orijinal pozisyonu bul
                    original_phrase = " ".join(
                        re.findall(r'\b\w+\b', target)[i:i + length]
                    )
                    start = target.lower().find(phrase)
                    end = start + len(phrase)
                    
                    matches.append((original_phrase, start, end))
        
        # Örtüşen eşleşmeleri birleştir
        merged = self._merge_overlapping(matches)
        
        return merged
    
    def _merge_overlapping(
        self,
        matches: List[Tuple[str, int, int]]
    ) -> List[Tuple[str, int, int]]:
        """Örtüşen eşleşmeleri birleştir."""
        if not matches:
            return []
        
        # Başlangıç pozisyonuna göre sırala
        sorted_matches = sorted(matches, key=lambda x: (x[1], -x[2]))
        
        merged = [sorted_matches[0]]
        
        for phrase, start, end in sorted_matches[1:]:
            last_phrase, last_start, last_end = merged[-1]
            
            if start <= last_end:
                # Örtüşme var, birleştir
                if end > last_end:
                    merged[-1] = (
                        phrase if len(phrase) > len(last_phrase) else last_phrase,
                        last_start,
                        end
                    )
            else:
                merged.append((phrase, start, end))
        
        return merged


class OriginalityChecker:
    """
    Orijinallik Kontrol Sistemi
    
    İçeriğin orijinalliğini çok boyutlu olarak analiz eder.
    """
    
    def __init__(
        self,
        ngram_size: int = 5,
        threshold_exact: float = 0.95,
        threshold_similar: float = 0.75
    ):
        self.ngram_analyzer = NGramAnalyzer(n=ngram_size)
        self.threshold_exact = threshold_exact
        self.threshold_similar = threshold_similar
        
        # Cache for previous documents (self-plagiarism)
        self.document_history: Dict[str, str] = {}
        
        # Known citation patterns
        self.citation_patterns = [
            r'\([^)]+,\s*\d{4}\)',  # (Author, 2024)
            r'\[\d+\]',             # [1]
            r'According to [^,]+',   # According to X
            r'"[^"]{20,}"',          # Long quotes
        ]
    
    async def check_originality(
        self,
        document_id: str,
        document_title: str,
        content: str,
        sources: Optional[List[Dict]] = None,
        check_self_plagiarism: bool = True
    ) -> OriginalityReport:
        """
        Orijinallik kontrolü yap.
        
        Args:
            document_id: Döküman ID
            document_title: Döküman başlığı
            content: Kontrol edilecek içerik
            sources: Karşılaştırılacak kaynaklar
            check_self_plagiarism: Önceki dökümanlarla karşılaştır
        
        Returns:
            OriginalityReport
        """
        start_time = datetime.now()
        sources = sources or []
        
        total_words = len(content.split())
        matches: List[SimilarityMatch] = []
        
        # 1. Citation analizi
        citation_text = self._extract_citations(content)
        citation_words = len(citation_text.split()) if citation_text else 0
        citation_percentage = (citation_words / total_words * 100) if total_words > 0 else 0
        
        # 2. Kaynak karşılaştırma
        exact_match_words = 0
        paraphrase_words = 0
        
        for source in sources:
            source_text = source.get("content", source.get("text", ""))
            source_info = source.get("title", source.get("url", "Unknown"))
            
            if not source_text:
                continue
            
            # N-gram benzerliği
            similarity = self.ngram_analyzer.calculate_similarity(content, source_text)
            
            if similarity >= self.threshold_exact:
                # Exact match bul
                matching_phrases = self.ngram_analyzer.find_matching_phrases(
                    content, source_text
                )
                
                for phrase, start, end in matching_phrases:
                    match_words = len(phrase.split())
                    exact_match_words += match_words
                    
                    matches.append(SimilarityMatch(
                        match_id=hashlib.md5(phrase.encode()).hexdigest()[:8],
                        source_text=source_text[max(0, source_text.lower().find(phrase.lower())-50):
                                               source_text.lower().find(phrase.lower())+len(phrase)+50],
                        matched_text=phrase,
                        similarity_score=similarity,
                        similarity_type=SimilarityType.EXACT_MATCH,
                        source_info=source_info,
                        position_start=start,
                        position_end=end
                    ))
            
            elif similarity >= self.threshold_similar:
                # Paraphrase olabilir
                paraphrase_words += int(total_words * similarity * 0.3)
                
                matches.append(SimilarityMatch(
                    match_id=hashlib.md5(source_info.encode()).hexdigest()[:8],
                    source_text=source_text[:300],
                    matched_text=content[:300],
                    similarity_score=similarity,
                    similarity_type=SimilarityType.PARAPHRASE,
                    source_info=source_info
                ))
        
        # 3. Self-plagiarism kontrolü
        if check_self_plagiarism:
            for prev_id, prev_content in self.document_history.items():
                if prev_id == document_id:
                    continue
                
                similarity = self.ngram_analyzer.calculate_similarity(content, prev_content)
                
                if similarity > 0.3:
                    matches.append(SimilarityMatch(
                        match_id=f"self_{prev_id[:8]}",
                        source_text=prev_content[:200],
                        matched_text=content[:200],
                        similarity_score=similarity,
                        similarity_type=SimilarityType.PARAPHRASE,
                        source_info=f"Önceki döküman: {prev_id}"
                    ))
        
        # 4. Yüzdeleri hesapla
        exact_match_percentage = (exact_match_words / total_words * 100) if total_words > 0 else 0
        paraphrase_percentage = (paraphrase_words / total_words * 100) if total_words > 0 else 0
        
        original_percentage = max(0, 100 - exact_match_percentage - paraphrase_percentage - citation_percentage)
        
        # 5. Overall originality
        overall_originality = original_percentage + (citation_percentage * 0.8)  # Atıflar kısmen orijinal sayılır
        
        # 6. Level belirle
        if overall_originality >= 90:
            level = OriginalityLevel.EXCELLENT
        elif overall_originality >= 75:
            level = OriginalityLevel.GOOD
        elif overall_originality >= 60:
            level = OriginalityLevel.ACCEPTABLE
        elif overall_originality >= 40:
            level = OriginalityLevel.NEEDS_REVIEW
        else:
            level = OriginalityLevel.PROBLEMATIC
        
        # 7. Flagged sections
        flagged_sections = []
        high_similarity_matches = [m for m in matches if m.similarity_score > 0.7]
        for m in high_similarity_matches[:5]:
            flagged_sections.append(m.matched_text[:100])
        
        # 8. Recommendations
        recommendations = self._generate_recommendations(
            overall_originality, exact_match_percentage, 
            paraphrase_percentage, len(matches)
        )
        
        # 9. Unique phrases
        unique_phrases = len(self.ngram_analyzer.extract_ngrams(content))
        
        # Cache for future self-plagiarism checks
        self.document_history[document_id] = content
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return OriginalityReport(
            document_id=document_id,
            document_title=document_title,
            overall_originality=overall_originality,
            originality_level=level,
            exact_match_percentage=exact_match_percentage,
            paraphrase_percentage=paraphrase_percentage,
            citation_percentage=citation_percentage,
            original_percentage=original_percentage,
            similarity_matches=matches,
            total_words=total_words,
            unique_phrases=unique_phrases,
            flagged_sections=flagged_sections,
            recommendations=recommendations,
            analysis_duration_seconds=duration
        )
    
    def _extract_citations(self, content: str) -> str:
        """Atıf metinlerini çıkar."""
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return " ".join(citations)
    
    def _generate_recommendations(
        self,
        originality: float,
        exact_match: float,
        paraphrase: float,
        match_count: int
    ) -> List[str]:
        """Öneriler oluştur."""
        recommendations = []
        
        if exact_match > 20:
            recommendations.append(
                "⚠️ Yüksek oranda birebir eşleşme tespit edildi. "
                "Alıntıları tırnak içine alın veya paraphrase yapın."
            )
        
        if paraphrase > 30:
            recommendations.append(
                "🔄 Paraphrase oranı yüksek. "
                "İçeriği daha orijinal şekilde ifade edin."
            )
        
        if match_count > 10:
            recommendations.append(
                "📚 Çok sayıda kaynak eşleşmesi var. "
                "Kaynak çeşitliliğini artırın."
            )
        
        if originality < 60:
            recommendations.append(
                "✏️ Orijinallik düşük. "
                "Kendi yorumlarınızı ve analizlerinizi ekleyin."
            )
        
        if originality >= 85:
            recommendations.append(
                "✅ Orijinallik yüksek. İçerik kaliteli görünüyor."
            )
        
        return recommendations
    
    async def generate_pdf_report(
        self,
        report: OriginalityReport,
        output_path: str
    ) -> str:
        """PDF rapor oluştur."""
        # PDF generation logic would go here
        # For now, return a markdown version
        
        markdown_report = f"""# Orijinallik Raporu

## Döküman Bilgileri
- **Başlık:** {report.document_title}
- **ID:** {report.document_id}
- **Analiz Tarihi:** {report.analysis_timestamp}

## Özet
{report.get_summary()}

## Detaylı Analiz

### Orijinallik Dağılımı
| Kategori | Yüzde |
|----------|-------|
| Orijinal İçerik | %{report.original_percentage:.1f} |
| Atıf/Alıntı | %{report.citation_percentage:.1f} |
| Paraphrase | %{report.paraphrase_percentage:.1f} |
| Birebir Eşleşme | %{report.exact_match_percentage:.1f} |

### İstatistikler
- Toplam Kelime: {report.total_words}
- Benzersiz İfade: {report.unique_phrases}
- Tespit Edilen Eşleşme: {len(report.similarity_matches)}

### Öneriler
"""
        
        for rec in report.recommendations:
            markdown_report += f"- {rec}\n"
        
        if report.flagged_sections:
            markdown_report += "\n### Dikkat Gerektiren Bölümler\n"
            for section in report.flagged_sections:
                markdown_report += f'> "{section}..."\n\n'
        
        return markdown_report
    
    def to_event(self, report: OriginalityReport) -> Dict[str, Any]:
        """WebSocket event formatına dönüştür."""
        return {
            "type": "originality_check",
            "timestamp": datetime.now().isoformat(),
            "summary": report.get_summary(),
            "overall_score": report.overall_originality,
            "level": report.originality_level.value,
            "match_count": len(report.similarity_matches),
            "recommendations": report.recommendations
        }
