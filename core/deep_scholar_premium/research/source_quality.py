"""
SourceQualityAnalyzer - Kaynak Kalite Değerlendirme Modülü
==========================================================

Değerlendirme Kriterleri:
1. Impact Factor
2. H-Index (yazar bazlı)
3. Atıf sayısı ve kalitesi
4. Dergi/Yayınevi prestiji
5. Akademik güvenilirlik
6. Güncellik
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

try:
    import aiohttp
except ImportError:
    aiohttp = None


class QualityTier(str, Enum):
    """Kalite seviyesi."""
    TIER_1 = "tier_1"   # En yüksek kalite (Nature, Science, vb.)
    TIER_2 = "tier_2"   # Yüksek kalite 
    TIER_3 = "tier_3"   # Orta-üst kalite
    TIER_4 = "tier_4"   # Orta kalite
    TIER_5 = "tier_5"   # Düşük kalite
    UNRANKED = "unranked"


class JournalCategory(str, Enum):
    """Dergi kategorisi."""
    Q1 = "Q1"  # Top %25
    Q2 = "Q2"  # %25-50
    Q3 = "Q3"  # %50-75
    Q4 = "Q4"  # Bottom %25
    UNKNOWN = "unknown"


@dataclass
class AuthorMetrics:
    """Yazar metrikleri."""
    name: str
    h_index: Optional[int] = None
    i10_index: Optional[int] = None
    total_citations: int = 0
    total_papers: int = 0
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    
    @property
    def avg_citations_per_paper(self) -> float:
        if self.total_papers == 0:
            return 0.0
        return self.total_citations / self.total_papers


@dataclass
class JournalMetrics:
    """Dergi metrikleri."""
    name: str
    issn: Optional[str] = None
    
    # Metrikler
    impact_factor: Optional[float] = None
    five_year_impact_factor: Optional[float] = None
    cite_score: Optional[float] = None
    sjr: Optional[float] = None  # Scimago Journal Rank
    snip: Optional[float] = None  # Source Normalized Impact per Paper
    
    # Kategori
    category: JournalCategory = JournalCategory.UNKNOWN
    subject_areas: List[str] = field(default_factory=list)
    
    # Diğer
    publisher: Optional[str] = None
    open_access: bool = False


@dataclass
class QualityScore:
    """Kaynak kalite puanı."""
    overall_score: float  # 0-100
    tier: QualityTier
    
    # Alt puanlar
    journal_score: float = 0.0
    author_score: float = 0.0
    citation_score: float = 0.0
    recency_score: float = 0.0
    methodology_score: float = 0.0
    
    # Detaylar
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "tier": self.tier.value,
            "journal_score": round(self.journal_score, 1),
            "author_score": round(self.author_score, 1),
            "citation_score": round(self.citation_score, 1),
            "recency_score": round(self.recency_score, 1),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendation": self.recommendation
        }


class SourceQualityAnalyzer:
    """
    Kaynak Kalite Değerlendirme Modülü
    
    Akademik kaynakların kalitesini çok boyutlu analiz eder.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Bilinen prestijli dergiler
        self.prestigious_journals = {
            # Genel
            "nature": {"impact": 50.0, "tier": QualityTier.TIER_1},
            "science": {"impact": 45.0, "tier": QualityTier.TIER_1},
            "cell": {"impact": 40.0, "tier": QualityTier.TIER_1},
            "proceedings of the national academy of sciences": {"impact": 12.0, "tier": QualityTier.TIER_1},
            "pnas": {"impact": 12.0, "tier": QualityTier.TIER_1},
            
            # Bilgisayar Bilimi
            "nature machine intelligence": {"impact": 25.0, "tier": QualityTier.TIER_1},
            "ieee transactions on pattern analysis and machine intelligence": {"impact": 24.0, "tier": QualityTier.TIER_1},
            "acm computing surveys": {"impact": 16.0, "tier": QualityTier.TIER_1},
            "artificial intelligence": {"impact": 14.0, "tier": QualityTier.TIER_1},
            "journal of machine learning research": {"impact": 6.0, "tier": QualityTier.TIER_2},
            "neural networks": {"impact": 8.0, "tier": QualityTier.TIER_2},
            
            # Tıp
            "the lancet": {"impact": 79.0, "tier": QualityTier.TIER_1},
            "new england journal of medicine": {"impact": 91.0, "tier": QualityTier.TIER_1},
            "jama": {"impact": 56.0, "tier": QualityTier.TIER_1},
            "bmj": {"impact": 39.0, "tier": QualityTier.TIER_1},
        }
        
        # Prestijli yayınevleri
        self.prestigious_publishers = [
            "springer", "elsevier", "wiley", "nature publishing",
            "oxford university press", "cambridge university press",
            "acm", "ieee", "aaai", "mit press"
        ]
        
        # Bilinen konferanslar (CS için)
        self.prestigious_conferences = [
            "neurips", "icml", "iclr", "cvpr", "iccv", "eccv",
            "acl", "emnlp", "naacl", "aaai", "ijcai", "kdd",
            "www", "sigir", "chi"
        ]
    
    async def analyze_source(
        self,
        title: str,
        authors: List[str],
        year: Optional[int],
        venue: Optional[str] = None,
        doi: Optional[str] = None,
        citation_count: int = 0,
        abstract: Optional[str] = None
    ) -> QualityScore:
        """
        Kaynağı kapsamlı analiz et.
        
        Args:
            title: Makale başlığı
            authors: Yazarlar
            year: Yayın yılı
            venue: Dergi/Konferans adı
            doi: DOI numarası
            citation_count: Atıf sayısı
            abstract: Özet
            
        Returns:
            Kalite puanı
        """
        # Alt puanları hesapla
        journal_score = await self._evaluate_venue(venue)
        author_score = await self._evaluate_authors(authors)
        citation_score = self._evaluate_citations(citation_count, year)
        recency_score = self._evaluate_recency(year)
        methodology_score = await self._evaluate_methodology(abstract) if abstract else 50.0
        
        # Ağırlıklı toplam
        weights = {
            "journal": 0.30,
            "author": 0.15,
            "citation": 0.25,
            "recency": 0.15,
            "methodology": 0.15
        }
        
        overall = (
            journal_score * weights["journal"] +
            author_score * weights["author"] +
            citation_score * weights["citation"] +
            recency_score * weights["recency"] +
            methodology_score * weights["methodology"]
        )
        
        # Tier belirle
        tier = self._determine_tier(overall)
        
        # Güçlü ve zayıf yönler
        strengths, weaknesses = self._identify_strengths_weaknesses(
            journal_score, author_score, citation_score, recency_score, methodology_score
        )
        
        # Öneri
        recommendation = self._generate_recommendation(tier, strengths, weaknesses)
        
        return QualityScore(
            overall_score=round(overall, 1),
            tier=tier,
            journal_score=round(journal_score, 1),
            author_score=round(author_score, 1),
            citation_score=round(citation_score, 1),
            recency_score=round(recency_score, 1),
            methodology_score=round(methodology_score, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation
        )
    
    async def analyze_multiple_sources(
        self,
        sources: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], QualityScore]]:
        """
        Birden fazla kaynağı analiz et.
        
        Args:
            sources: Kaynak listesi
            
        Returns:
            Kaynak ve kalite puanı çiftleri
        """
        results = []
        
        for source in sources:
            score = await self.analyze_source(
                title=source.get("title", ""),
                authors=source.get("authors", []),
                year=source.get("year"),
                venue=source.get("venue") or source.get("journal"),
                doi=source.get("doi"),
                citation_count=source.get("citation_count", 0),
                abstract=source.get("abstract")
            )
            results.append((source, score))
        
        # En yüksekten düşüğe sırala
        results.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        return results
    
    async def get_journal_metrics(
        self,
        journal_name: str
    ) -> JournalMetrics:
        """
        Dergi metriklerini getir.
        
        Args:
            journal_name: Dergi adı
            
        Returns:
            Dergi metrikleri
        """
        normalized_name = journal_name.lower().strip()
        
        # Bilinen dergiler
        if normalized_name in self.prestigious_journals:
            info = self.prestigious_journals[normalized_name]
            return JournalMetrics(
                name=journal_name,
                impact_factor=info["impact"],
                category=JournalCategory.Q1 if info["tier"] == QualityTier.TIER_1 else JournalCategory.Q2
            )
        
        # OpenAlex'ten bilgi çek
        if aiohttp:
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.openalex.org/sources?search={journal_name}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("results"):
                                source = data["results"][0]
                                return JournalMetrics(
                                    name=source.get("display_name", journal_name),
                                    issn=source.get("issn_l"),
                                    cite_score=source.get("summary_stats", {}).get("2yr_mean_citedness"),
                                    open_access=source.get("is_oa", False),
                                    publisher=source.get("host_organization_name")
                                )
            except:
                pass
        
        return JournalMetrics(name=journal_name)
    
    async def get_author_metrics(
        self,
        author_name: str
    ) -> AuthorMetrics:
        """
        Yazar metriklerini getir.
        
        Args:
            author_name: Yazar adı
            
        Returns:
            Yazar metrikleri
        """
        metrics = AuthorMetrics(name=author_name)
        
        if aiohttp:
            try:
                # OpenAlex'ten yazar bilgisi
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.openalex.org/authors?search={author_name}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("results"):
                                author = data["results"][0]
                                metrics.h_index = author.get("summary_stats", {}).get("h_index")
                                metrics.total_citations = author.get("cited_by_count", 0)
                                metrics.total_papers = author.get("works_count", 0)
                                metrics.orcid = author.get("orcid")
                                
                                if author.get("last_known_institution"):
                                    metrics.affiliation = author["last_known_institution"].get("display_name")
            except:
                pass
        
        return metrics
    
    async def _evaluate_venue(self, venue: Optional[str]) -> float:
        """Yayın yerini değerlendir."""
        if not venue:
            return 50.0
        
        normalized = venue.lower().strip()
        
        # Prestijli dergi kontrolü
        for journal_name, info in self.prestigious_journals.items():
            if journal_name in normalized:
                if info["tier"] == QualityTier.TIER_1:
                    return 95.0
                elif info["tier"] == QualityTier.TIER_2:
                    return 85.0
        
        # Prestijli konferans kontrolü
        for conf in self.prestigious_conferences:
            if conf in normalized:
                return 85.0
        
        # Prestijli yayınevi kontrolü
        for publisher in self.prestigious_publishers:
            if publisher in normalized:
                return 70.0
        
        # ArXiv/preprint kontrolü
        if "arxiv" in normalized or "preprint" in normalized:
            return 55.0
        
        return 60.0
    
    async def _evaluate_authors(self, authors: List[str]) -> float:
        """Yazarları değerlendir."""
        if not authors:
            return 50.0
        
        # İlk yazarın h-index'ini kontrol et
        if aiohttp:
            try:
                metrics = await self.get_author_metrics(authors[0])
                if metrics.h_index:
                    if metrics.h_index >= 50:
                        return 95.0
                    elif metrics.h_index >= 30:
                        return 85.0
                    elif metrics.h_index >= 15:
                        return 75.0
                    elif metrics.h_index >= 5:
                        return 65.0
                    else:
                        return 55.0
            except:
                pass
        
        return 60.0
    
    def _evaluate_citations(
        self,
        citation_count: int,
        year: Optional[int]
    ) -> float:
        """Atıf sayısını değerlendir."""
        if citation_count == 0:
            return 40.0
        
        # Yıllık atıf ortalaması
        if year:
            years_since_pub = max(1, datetime.now().year - year)
            annual_citations = citation_count / years_since_pub
            
            if annual_citations >= 100:
                return 95.0
            elif annual_citations >= 50:
                return 90.0
            elif annual_citations >= 20:
                return 80.0
            elif annual_citations >= 10:
                return 70.0
            elif annual_citations >= 5:
                return 60.0
            else:
                return 50.0
        else:
            # Sadece toplam atıf
            if citation_count >= 500:
                return 90.0
            elif citation_count >= 100:
                return 80.0
            elif citation_count >= 50:
                return 70.0
            elif citation_count >= 10:
                return 60.0
            else:
                return 50.0
    
    def _evaluate_recency(self, year: Optional[int]) -> float:
        """Güncelliği değerlendir."""
        if not year:
            return 50.0
        
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 1:
            return 95.0
        elif age <= 2:
            return 90.0
        elif age <= 3:
            return 85.0
        elif age <= 5:
            return 75.0
        elif age <= 10:
            return 60.0
        elif age <= 20:
            return 45.0
        else:
            return 30.0
    
    async def _evaluate_methodology(self, abstract: str) -> float:
        """Metodoloji kalitesini özetten değerlendir."""
        score = 50.0
        
        # Metodoloji belirteçleri
        methodology_indicators = [
            ("random", 5), ("control", 5), ("experiment", 5),
            ("participant", 4), ("sample", 4), ("survey", 3),
            ("interview", 3), ("analysis", 3), ("statistical", 4),
            ("significant", 4), ("p-value", 5), ("hypothesis", 4),
            ("regression", 4), ("correlation", 3), ("model", 3)
        ]
        
        abstract_lower = abstract.lower()
        
        for indicator, points in methodology_indicators:
            if indicator in abstract_lower:
                score += points
        
        return min(score, 90.0)
    
    def _determine_tier(self, overall_score: float) -> QualityTier:
        """Genel puana göre tier belirle."""
        if overall_score >= 85:
            return QualityTier.TIER_1
        elif overall_score >= 70:
            return QualityTier.TIER_2
        elif overall_score >= 55:
            return QualityTier.TIER_3
        elif overall_score >= 40:
            return QualityTier.TIER_4
        else:
            return QualityTier.TIER_5
    
    def _identify_strengths_weaknesses(
        self,
        journal_score: float,
        author_score: float,
        citation_score: float,
        recency_score: float,
        methodology_score: float
    ) -> Tuple[List[str], List[str]]:
        """Güçlü ve zayıf yönleri belirle."""
        strengths = []
        weaknesses = []
        
        scores = {
            "Dergi/Konferans kalitesi": journal_score,
            "Yazar prestiji": author_score,
            "Atıf etkisi": citation_score,
            "Güncellik": recency_score,
            "Metodoloji": methodology_score
        }
        
        for name, score in scores.items():
            if score >= 80:
                strengths.append(f"Yüksek {name.lower()}")
            elif score < 50:
                weaknesses.append(f"Düşük {name.lower()}")
        
        return strengths, weaknesses
    
    def _generate_recommendation(
        self,
        tier: QualityTier,
        strengths: List[str],
        weaknesses: List[str]
    ) -> str:
        """Öneri oluştur."""
        if tier == QualityTier.TIER_1:
            return "Mükemmel kalitede kaynak. Ana argümanlar için kullanılabilir."
        elif tier == QualityTier.TIER_2:
            return "Yüksek kalitede kaynak. Güvenle kullanılabilir."
        elif tier == QualityTier.TIER_3:
            return "Orta-üst kalitede kaynak. Destekleyici referans olarak uygundur."
        elif tier == QualityTier.TIER_4:
            return "Orta kalitede kaynak. Dikkatli kullanın, başka kaynaklarla destekleyin."
        else:
            return "Düşük kalitede kaynak. Mümkünse daha güçlü alternatifler tercih edin."


async def main():
    """Test."""
    analyzer = SourceQualityAnalyzer()
    
    # Örnek analiz
    score = await analyzer.analyze_source(
        title="Deep Learning for NLP",
        authors=["Geoffrey Hinton", "Yann LeCun"],
        year=2020,
        venue="Nature Machine Intelligence",
        citation_count=150
    )
    
    print(f"Overall: {score.overall_score}")
    print(f"Tier: {score.tier.value}")
    print(f"Strengths: {score.strengths}")
    print(f"Weaknesses: {score.weaknesses}")
    print(f"Recommendation: {score.recommendation}")


if __name__ == "__main__":
    asyncio.run(main())
