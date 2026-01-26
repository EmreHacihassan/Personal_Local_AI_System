"""
PlagiarismDetector - İntihal Tespit Modülü
==========================================

Tespit Yöntemleri:
1. Metin eşleştirme (n-gram)
2. Semantik benzerlik (embedding)
3. Kaynak eşleştirme
4. Parafraz tespiti
5. Self-plagiarism kontrolü
"""

import asyncio
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


class SimilarityLevel(str, Enum):
    """Benzerlik seviyesi."""
    NONE = "none"           # %0-10
    LOW = "low"             # %10-30
    MODERATE = "moderate"   # %30-50
    HIGH = "high"           # %50-70
    VERY_HIGH = "very_high" # %70-90
    EXACT = "exact"         # %90-100


@dataclass
class PlagiarismMatch:
    """İntihal eşleşmesi."""
    text: str
    source_text: str
    source_id: Optional[str]
    source_title: Optional[str]
    similarity: float  # 0-1
    match_type: str    # "exact", "paraphrase", "semantic"
    start_position: int
    end_position: int


@dataclass
class PlagiarismReport:
    """İntihal raporu."""
    overall_similarity: float
    level: SimilarityLevel
    total_matches: int
    matches: List[PlagiarismMatch]
    
    # İstatistikler
    exact_matches: int = 0
    paraphrase_matches: int = 0
    semantic_matches: int = 0
    
    # Özet
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_similarity": round(self.overall_similarity * 100, 1),
            "level": self.level.value,
            "total_matches": self.total_matches,
            "exact_matches": self.exact_matches,
            "paraphrase_matches": self.paraphrase_matches,
            "semantic_matches": self.semantic_matches,
            "summary": self.summary,
            "recommendations": self.recommendations
        }
    
    def to_markdown(self) -> str:
        lines = [
            "# 📋 İntihal Raporu",
            "",
            f"**Genel Benzerlik:** %{round(self.overall_similarity * 100, 1)}",
            f"**Seviye:** {self.level.value.replace('_', ' ').title()}",
            f"**Toplam Eşleşme:** {self.total_matches}",
            "",
            "## Eşleşme Dağılımı",
            f"- Tam eşleşme: {self.exact_matches}",
            f"- Parafraz: {self.paraphrase_matches}",
            f"- Semantik: {self.semantic_matches}",
            ""
        ]
        
        if self.matches:
            lines.extend(["## Tespit Edilen Eşleşmeler", ""])
            for i, match in enumerate(self.matches[:10], 1):
                lines.append(f"### {i}. Eşleşme (%{round(match.similarity * 100)})")
                lines.append(f"> {match.text[:200]}...")
                if match.source_title:
                    lines.append(f"*Kaynak: {match.source_title}*")
                lines.append("")
        
        if self.recommendations:
            lines.extend(["## Öneriler", ""])
            for rec in self.recommendations:
                lines.append(f"- {rec}")
        
        return "\n".join(lines)


class PlagiarismDetector:
    """
    İntihal Tespit Modülü
    
    Çoklu yöntemle intihal tespiti yapar.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.known_sources: Dict[str, str] = {}  # source_id -> content
        self.ngram_index: Dict[str, List[str]] = {}  # ngram -> [source_ids]
        
        # Parametreler
        self.ngram_size = config.get("ngram_size", 5) if config else 5
        self.min_match_length = config.get("min_match_length", 10) if config else 10
        self.similarity_threshold = config.get("similarity_threshold", 0.3) if config else 0.3
    
    async def check_document(
        self,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> PlagiarismReport:
        """
        Dokümanı intihal için kontrol et.
        
        Args:
            content: Kontrol edilecek içerik
            sources: Karşılaştırılacak kaynaklar
            
        Returns:
            İntihal raporu
        """
        matches: List[PlagiarismMatch] = []
        
        # Kaynakları indexe ekle
        if sources:
            for source in sources:
                source_id = source.get("id", hashlib.md5(
                    source.get("content", "")[:100].encode()
                ).hexdigest()[:8])
                source_content = source.get("content", "") or source.get("abstract", "")
                if source_content:
                    self.add_source(source_id, source_content, source.get("title"))
        
        # N-gram tabanlı tam eşleşme kontrolü
        exact_matches = await self._check_exact_matches(content)
        matches.extend(exact_matches)
        
        # Parafraz tespiti
        paraphrase_matches = await self._check_paraphrases(content)
        matches.extend(paraphrase_matches)
        
        # Semantik benzerlik (opsiyonel, embedding gerektirir)
        semantic_matches = await self._check_semantic_similarity(content)
        matches.extend(semantic_matches)
        
        # Duplikasyonları kaldır
        matches = self._deduplicate_matches(matches)
        
        # Genel benzerlik hesapla
        overall_similarity = self._calculate_overall_similarity(content, matches)
        
        # Rapor oluştur
        return self._create_report(overall_similarity, matches)
    
    async def check_section(
        self,
        section_content: str,
        section_title: str
    ) -> PlagiarismReport:
        """Tek bir bölümü kontrol et."""
        return await self.check_document(section_content)
    
    def add_source(
        self,
        source_id: str,
        content: str,
        title: Optional[str] = None
    ):
        """
        Karşılaştırma için kaynak ekle.
        
        Args:
            source_id: Kaynak kimliği
            content: Kaynak içeriği
            title: Kaynak başlığı
        """
        self.known_sources[source_id] = {
            "content": content,
            "title": title
        }
        
        # N-gram indexini güncelle
        ngrams = self._get_ngrams(content)
        for ngram in ngrams:
            ngram_hash = hashlib.md5(ngram.encode()).hexdigest()
            if ngram_hash not in self.ngram_index:
                self.ngram_index[ngram_hash] = []
            if source_id not in self.ngram_index[ngram_hash]:
                self.ngram_index[ngram_hash].append(source_id)
    
    async def _check_exact_matches(
        self,
        content: str
    ) -> List[PlagiarismMatch]:
        """Tam eşleşme kontrolü (n-gram tabanlı)."""
        matches = []
        
        # İçeriği cümlelere böl
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) < self.min_match_length:
                continue
            
            # N-gramları kontrol et
            ngrams = self._get_ngrams(sentence)
            
            for ngram in ngrams:
                ngram_hash = hashlib.md5(ngram.encode()).hexdigest()
                
                if ngram_hash in self.ngram_index:
                    for source_id in self.ngram_index[ngram_hash]:
                        source_info = self.known_sources.get(source_id, {})
                        source_content = source_info.get("content", "")
                        
                        # Daha uzun eşleşme bul
                        match_start, match_end = self._find_longest_match(
                            sentence, source_content
                        )
                        
                        if match_end - match_start >= self.min_match_length * 5:
                            matched_text = sentence[match_start:match_end]
                            
                            matches.append(PlagiarismMatch(
                                text=matched_text,
                                source_text=matched_text,
                                source_id=source_id,
                                source_title=source_info.get("title"),
                                similarity=1.0,
                                match_type="exact",
                                start_position=content.find(sentence),
                                end_position=content.find(sentence) + len(sentence)
                            ))
        
        return matches
    
    async def _check_paraphrases(
        self,
        content: str
    ) -> List[PlagiarismMatch]:
        """Parafraz tespiti."""
        matches = []
        
        # Her kaynak için benzerlik kontrolü
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence.split()) < 5:
                continue
            
            for source_id, source_info in self.known_sources.items():
                source_content = source_info.get("content", "")
                source_sentences = re.split(r'[.!?]+', source_content)
                
                for source_sentence in source_sentences:
                    source_sentence = source_sentence.strip()
                    if len(source_sentence.split()) < 5:
                        continue
                    
                    # Jaccard benzerliği
                    similarity = self._jaccard_similarity(sentence, source_sentence)
                    
                    if 0.5 <= similarity < 0.9:  # Parafraz aralığı
                        matches.append(PlagiarismMatch(
                            text=sentence,
                            source_text=source_sentence,
                            source_id=source_id,
                            source_title=source_info.get("title"),
                            similarity=similarity,
                            match_type="paraphrase",
                            start_position=content.find(sentence),
                            end_position=content.find(sentence) + len(sentence)
                        ))
                        break
        
        return matches
    
    async def _check_semantic_similarity(
        self,
        content: str
    ) -> List[PlagiarismMatch]:
        """Semantik benzerlik kontrolü (basitleştirilmiş)."""
        # Bu özellik için embedding modeli gerekir
        # Şimdilik boş döndür
        return []
    
    def _get_ngrams(self, text: str) -> List[str]:
        """N-gramları çıkar."""
        words = text.lower().split()
        ngrams = []
        
        for i in range(len(words) - self.ngram_size + 1):
            ngram = " ".join(words[i:i + self.ngram_size])
            ngrams.append(ngram)
        
        return ngrams
    
    def _find_longest_match(
        self,
        text1: str,
        text2: str
    ) -> Tuple[int, int]:
        """En uzun eşleşen alt diziyi bul."""
        words1 = text1.lower().split()
        words2 = text2.lower().split()
        
        # Basit LCS (Longest Common Subsequence) yaklaşımı
        max_length = 0
        max_start = 0
        
        for i in range(len(words1)):
            for j in range(len(words2)):
                length = 0
                while (i + length < len(words1) and 
                       j + length < len(words2) and
                       words1[i + length] == words2[j + length]):
                    length += 1
                
                if length > max_length:
                    max_length = length
                    max_start = sum(len(w) + 1 for w in words1[:i])
        
        return max_start, max_start + max_length * 6  # Yaklaşık karakter pozisyonu
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Jaccard benzerliği hesapla."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _deduplicate_matches(
        self,
        matches: List[PlagiarismMatch]
    ) -> List[PlagiarismMatch]:
        """Çakışan eşleşmeleri birleştir."""
        if not matches:
            return []
        
        # Pozisyona göre sırala
        sorted_matches = sorted(matches, key=lambda m: m.start_position)
        
        result = [sorted_matches[0]]
        
        for match in sorted_matches[1:]:
            last = result[-1]
            
            # Çakışma kontrolü
            if match.start_position < last.end_position:
                # En yüksek benzerliği tut
                if match.similarity > last.similarity:
                    result[-1] = match
            else:
                result.append(match)
        
        return result
    
    def _calculate_overall_similarity(
        self,
        content: str,
        matches: List[PlagiarismMatch]
    ) -> float:
        """Genel benzerlik oranını hesapla."""
        if not matches:
            return 0.0
        
        total_length = len(content)
        if total_length == 0:
            return 0.0
        
        matched_chars = sum(m.end_position - m.start_position for m in matches)
        
        return min(matched_chars / total_length, 1.0)
    
    def _create_report(
        self,
        overall_similarity: float,
        matches: List[PlagiarismMatch]
    ) -> PlagiarismReport:
        """Rapor oluştur."""
        # Seviye belirle
        if overall_similarity < 0.1:
            level = SimilarityLevel.NONE
        elif overall_similarity < 0.3:
            level = SimilarityLevel.LOW
        elif overall_similarity < 0.5:
            level = SimilarityLevel.MODERATE
        elif overall_similarity < 0.7:
            level = SimilarityLevel.HIGH
        elif overall_similarity < 0.9:
            level = SimilarityLevel.VERY_HIGH
        else:
            level = SimilarityLevel.EXACT
        
        # Eşleşme türlerini say
        exact_count = sum(1 for m in matches if m.match_type == "exact")
        paraphrase_count = sum(1 for m in matches if m.match_type == "paraphrase")
        semantic_count = sum(1 for m in matches if m.match_type == "semantic")
        
        # Özet
        if level in [SimilarityLevel.NONE, SimilarityLevel.LOW]:
            summary = "İntihal riski düşük. İçerik büyük ölçüde orijinal görünüyor."
        elif level == SimilarityLevel.MODERATE:
            summary = "Orta düzeyde benzerlik tespit edildi. Bazı bölümlerin yeniden yazılması önerilir."
        else:
            summary = "Yüksek benzerlik tespit edildi. Ciddi revizyon gerekli."
        
        # Öneriler
        recommendations = []
        if exact_count > 0:
            recommendations.append("Tam eşleşen bölümleri kendi kelimelerinizle yeniden yazın")
        if paraphrase_count > 0:
            recommendations.append("Parafraz bölümlerini farklı bir perspektiften ele alın")
        if level in [SimilarityLevel.HIGH, SimilarityLevel.VERY_HIGH]:
            recommendations.append("Tüm alıntıları uygun şekilde kaynak göstererek işaretleyin")
        
        return PlagiarismReport(
            overall_similarity=overall_similarity,
            level=level,
            total_matches=len(matches),
            matches=matches,
            exact_matches=exact_count,
            paraphrase_matches=paraphrase_count,
            semantic_matches=semantic_count,
            summary=summary,
            recommendations=recommendations
        )
    
    def clear_sources(self):
        """Kaynak indexini temizle."""
        self.known_sources.clear()
        self.ngram_index.clear()
