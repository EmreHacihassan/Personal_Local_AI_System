"""
⭐ Source Quality Scorer - Premium Search Enhancement

Kaynakları kalite ve relevance'a göre puanlar.
Domain güvenilirliği, içerik uyumu ve güncellik değerlendirilir.

Author: Enterprise AI Team
Date: 2025-02
"""

import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Kaynak tipi"""
    ACADEMIC = "academic"
    ENCYCLOPEDIA = "encyclopedia"
    OFFICIAL = "official"
    NEWS = "news"
    BLOG = "blog"
    FORUM = "forum"
    CODE = "code"
    VIDEO = "video"
    SOCIAL = "social"
    UNKNOWN = "unknown"


@dataclass
class QualityScore:
    """Kalite puanı detayları"""
    total_score: float  # 0-1
    domain_score: float
    relevance_score: float
    freshness_score: float
    uniqueness_score: float
    source_type: SourceType
    trust_level: str  # "high", "medium", "low"
    details: Dict[str, Any]


class SourceQualityScorer:
    """
    Kaynak Kalite Puanlayıcı
    
    Her kaynağı multiple criteria ile değerlendirir:
    - Domain güvenilirliği
    - İçerik relevance'ı
    - Güncellik
    - Benzersizlik
    """
    
    # Domain trust scores (0-100)
    DOMAIN_TRUST_SCORES = {
        # Academic (90-100) 🎓
        ".edu": 95,
        ".ac.uk": 95,
        ".ac.": 93,
        "arxiv.org": 98,
        "scholar.google": 95,
        "semanticscholar.org": 95,
        "pubmed.ncbi": 98,
        "nature.com": 97,
        "sciencedirect.com": 95,
        "ieee.org": 96,
        "acm.org": 95,
        "springer.com": 94,
        "researchgate.net": 88,
        "jstor.org": 95,
        "plos.org": 93,
        
        # Government & Official (85-95) 🏛️
        ".gov": 92,
        ".gov.uk": 92,
        ".gov.tr": 90,
        "who.int": 95,
        "un.org": 93,
        "europa.eu": 92,
        "nih.gov": 96,
        "cdc.gov": 95,
        
        # Encyclopedia & Reference (85-95) 📚
        "wikipedia.org": 88,
        "britannica.com": 92,
        "merriam-webster.com": 90,
        "dictionary.com": 85,
        "investopedia.com": 85,
        
        # Quality Tech Documentation (80-90) 📖
        "docs.python.org": 92,
        "docs.microsoft.com": 90,
        "developer.mozilla.org": 92,
        "developer.apple.com": 90,
        "cloud.google.com": 88,
        "aws.amazon.com": 88,
        "docs.oracle.com": 88,
        "kubernetes.io": 88,
        "reactjs.org": 88,
        "vuejs.org": 87,
        "angular.io": 87,
        
        # Code Repositories (75-85) 💻
        "github.com": 82,
        "gitlab.com": 80,
        "bitbucket.org": 78,
        "stackoverflow.com": 85,
        "stackexchange.com": 83,
        
        # Quality News (70-85) 📰
        "bbc.com": 85,
        "bbc.co.uk": 85,
        "reuters.com": 88,
        "apnews.com": 87,
        "theguardian.com": 82,
        "nytimes.com": 83,
        "washingtonpost.com": 82,
        "economist.com": 85,
        "ft.com": 84,
        "bloomberg.com": 83,
        "wired.com": 78,
        "arstechnica.com": 80,
        "techcrunch.com": 75,
        "theverge.com": 74,
        
        # Quality Blogs/Tutorials (65-80) ✍️
        "medium.com": 68,
        "dev.to": 72,
        "freecodecamp.org": 78,
        "towardsdatascience.com": 75,
        "hackernoon.com": 70,
        "css-tricks.com": 78,
        "smashingmagazine.com": 78,
        "digitalocean.com": 80,
        "baeldung.com": 78,
        "realpython.com": 82,
        "geeksforgeeks.org": 72,
        "w3schools.com": 70,
        "tutorialspoint.com": 68,
        
        # Video Platforms (60-75) 🎬
        "youtube.com": 65,
        "vimeo.com": 68,
        "coursera.org": 82,
        "udemy.com": 70,
        "edx.org": 85,
        "khanacademy.org": 85,
        
        # Forums (55-70) 💬
        "reddit.com": 62,
        "quora.com": 65,
        "discourse.": 60,
        
        # Social Media (40-55) 📱
        "twitter.com": 50,
        "x.com": 50,
        "linkedin.com": 58,
        "facebook.com": 45,
        
        # Low trust (30-50) ⚠️
        "buzzfeed.com": 45,
        "huffpost.com": 55,
        "pinterest.com": 40,
    }
    
    # Source type mapping
    SOURCE_TYPE_PATTERNS = {
        SourceType.ACADEMIC: [
            "arxiv", "scholar", "pubmed", "nature.com", "science",
            "ieee", "acm.org", "springer", "researchgate", ".edu",
            "journal", "proceedings", "thesis", "dissertation",
        ],
        SourceType.ENCYCLOPEDIA: [
            "wikipedia", "britannica", "encyclopedia", "wiki",
            "dictionary", "glossary", "reference",
        ],
        SourceType.OFFICIAL: [
            ".gov", "official", "docs.", "documentation",
            "developer.", "cloud.google", "aws.amazon",
        ],
        SourceType.NEWS: [
            "news", "bbc", "reuters", "nytimes", "guardian",
            "washingtonpost", "bloomberg", "techcrunch", "verge",
        ],
        SourceType.BLOG: [
            "medium", "dev.to", "blog", "tutorial", "guide",
            "freecodecamp", "towardsdatascience", "hackernoon",
        ],
        SourceType.CODE: [
            "github", "gitlab", "stackoverflow", "stackexchange",
            "bitbucket", "gist", "codepen", "jsfiddle",
        ],
        SourceType.VIDEO: [
            "youtube", "vimeo", "coursera", "udemy", "edx",
            "video", "watch", "channel",
        ],
        SourceType.FORUM: [
            "reddit", "quora", "forum", "discussion", "community",
            "discourse", "slack", "discord",
        ],
        SourceType.SOCIAL: [
            "twitter", "facebook", "linkedin", "instagram",
            "tiktok", "x.com",
        ],
    }
    
    def __init__(self):
        self._cache: Dict[str, QualityScore] = {}
        self._stats = {
            "total_scored": 0,
            "cache_hits": 0,
            "avg_score": 0.0,
        }
    
    def _get_cache_key(self, url: str, query: str) -> str:
        """Cache key oluştur"""
        combined = f"{url.lower()}:{query.lower()}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _get_domain(self, url: str) -> str:
        """URL'den domain çıkar"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace("www.", "")
        except:
            return ""
    
    def _calculate_domain_score(self, url: str) -> Tuple[float, str]:
        """Domain güvenilirlik puanı (0-1)"""
        domain = self._get_domain(url)
        url_lower = url.lower()
        
        # Check exact matches first
        for pattern, score in self.DOMAIN_TRUST_SCORES.items():
            if pattern in domain or pattern in url_lower:
                return score / 100, pattern
        
        # Check TLD patterns
        if ".edu" in domain:
            return 0.90, ".edu"
        if ".gov" in domain:
            return 0.88, ".gov"
        if ".org" in domain:
            return 0.65, ".org"
        if ".ac." in domain:
            return 0.88, ".ac."
        
        # Default score
        return 0.50, "default"
    
    def _detect_source_type(self, url: str, content: str = "") -> SourceType:
        """Kaynak tipini tespit et"""
        url_lower = url.lower()
        content_lower = (content or "").lower()
        combined = url_lower + " " + content_lower
        
        for source_type, patterns in self.SOURCE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern in combined:
                    return source_type
        
        return SourceType.UNKNOWN
    
    def _calculate_relevance_score(
        self,
        content: str,
        title: str,
        query: str
    ) -> float:
        """İçerik relevance puanı (0-1)"""
        if not query:
            return 0.5
        
        # Normalize
        query_lower = query.lower()
        content_lower = (content or "").lower()
        title_lower = (title or "").lower()
        
        # Extract query keywords (remove stopwords)
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "of", "in", "to",
            "for", "with", "on", "at", "by", "from", "as", "ve", "ile",
            "için", "bu", "bir", "de", "da", "mi", "mı", "ne", "nasıl",
            "nedir", "hangi", "neden", "kim", "what", "how", "why",
        }
        
        query_words = set(re.findall(r'\w+', query_lower)) - stopwords
        
        if not query_words:
            return 0.5
        
        # Calculate overlap scores
        title_words = set(re.findall(r'\w+', title_lower))
        content_words = set(re.findall(r'\w+', content_lower[:2000]))  # First 2000 chars
        
        # Title match (high weight)
        title_overlap = len(query_words & title_words) / len(query_words)
        
        # Content match
        content_overlap = len(query_words & content_words) / len(query_words)
        
        # Exact phrase match bonus
        phrase_bonus = 0.0
        if query_lower in title_lower:
            phrase_bonus = 0.2
        elif query_lower in content_lower:
            phrase_bonus = 0.1
        
        # Weighted score
        score = (title_overlap * 0.4) + (content_overlap * 0.4) + phrase_bonus
        
        return min(1.0, score)
    
    def _calculate_freshness_score(
        self,
        date_str: Optional[str] = None
    ) -> float:
        """Güncellik puanı (0-1)"""
        if not date_str:
            return 0.5  # Unknown date - neutral score
        
        try:
            # Try parsing various date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y"]:
                try:
                    pub_date = datetime.strptime(date_str[:10], fmt)
                    break
                except:
                    continue
            else:
                return 0.5
            
            # Calculate age in days
            age_days = (datetime.now() - pub_date).days
            
            # Score based on age
            if age_days < 30:  # Last month
                return 1.0
            elif age_days < 90:  # Last 3 months
                return 0.9
            elif age_days < 180:  # Last 6 months
                return 0.8
            elif age_days < 365:  # Last year
                return 0.7
            elif age_days < 730:  # Last 2 years
                return 0.6
            elif age_days < 1825:  # Last 5 years
                return 0.5
            else:
                return 0.4  # Older
                
        except Exception:
            return 0.5
    
    def _calculate_uniqueness_score(
        self,
        url: str,
        seen_domains: Optional[set] = None
    ) -> float:
        """Benzersizlik puanı (0-1)"""
        if seen_domains is None:
            return 1.0
        
        domain = self._get_domain(url)
        
        if domain not in seen_domains:
            return 1.0  # New domain - full score
        else:
            return 0.7  # Same domain - reduced score
    
    def score_source(
        self,
        url: str,
        title: str = "",
        content: str = "",
        query: str = "",
        date: Optional[str] = None,
        seen_domains: Optional[set] = None,
        use_cache: bool = True,
    ) -> QualityScore:
        """
        Kaynağı puanla.
        
        Args:
            url: Kaynak URL'i
            title: Başlık
            content: İçerik snippet'i
            query: Arama sorgusu
            date: Yayın tarihi (optional)
            seen_domains: Daha önce görülen domain'ler
            use_cache: Cache kullan
            
        Returns:
            QualityScore with all details
        """
        self._stats["total_scored"] += 1
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(url, query)
            if cache_key in self._cache:
                self._stats["cache_hits"] += 1
                return self._cache[cache_key]
        
        # Calculate individual scores
        domain_score, matched_pattern = self._calculate_domain_score(url)
        relevance_score = self._calculate_relevance_score(content, title, query)
        freshness_score = self._calculate_freshness_score(date)
        uniqueness_score = self._calculate_uniqueness_score(url, seen_domains)
        source_type = self._detect_source_type(url, content)
        
        # Weighted total score
        weights = {
            "domain": 0.25,
            "relevance": 0.40,
            "freshness": 0.20,
            "uniqueness": 0.15,
        }
        
        total_score = (
            domain_score * weights["domain"] +
            relevance_score * weights["relevance"] +
            freshness_score * weights["freshness"] +
            uniqueness_score * weights["uniqueness"]
        )
        
        # Determine trust level
        if total_score >= 0.75:
            trust_level = "high"
        elif total_score >= 0.50:
            trust_level = "medium"
        else:
            trust_level = "low"
        
        result = QualityScore(
            total_score=round(total_score, 3),
            domain_score=round(domain_score, 3),
            relevance_score=round(relevance_score, 3),
            freshness_score=round(freshness_score, 3),
            uniqueness_score=round(uniqueness_score, 3),
            source_type=source_type,
            trust_level=trust_level,
            details={
                "url": url,
                "domain": self._get_domain(url),
                "matched_pattern": matched_pattern,
                "weights": weights,
            }
        )
        
        # Update stats
        n = self._stats["total_scored"]
        self._stats["avg_score"] = (
            (self._stats["avg_score"] * (n - 1) + total_score) / n
        )
        
        # Cache result
        if use_cache:
            self._cache[cache_key] = result
        
        return result
    
    def score_sources_batch(
        self,
        sources: List[Dict],
        query: str = ""
    ) -> List[Tuple[Dict, QualityScore]]:
        """
        Birden fazla kaynağı puanla.
        
        Args:
            sources: List of {"url": ..., "title": ..., "content": ...}
            query: Arama sorgusu
            
        Returns:
            List of (source, score) tuples, sorted by score
        """
        seen_domains: set = set()
        scored_sources = []
        
        for source in sources:
            score = self.score_source(
                url=source.get("url", ""),
                title=source.get("title", ""),
                content=source.get("content", source.get("snippet", "")),
                query=query,
                date=source.get("date"),
                seen_domains=seen_domains,
            )
            
            # Add domain to seen set
            domain = self._get_domain(source.get("url", ""))
            seen_domains.add(domain)
            
            scored_sources.append((source, score))
        
        # Sort by total score (descending)
        scored_sources.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return scored_sources
    
    def rank_sources(
        self,
        sources: List[Dict],
        query: str = "",
        top_k: int = 50
    ) -> List[Dict]:
        """
        Kaynakları puanla ve sırala.
        
        Args:
            sources: Kaynak listesi
            query: Arama sorgusu
            top_k: Döndürülecek maksimum kaynak
            
        Returns:
            Puanlanmış ve sıralanmış kaynak listesi
        """
        scored = self.score_sources_batch(sources, query)
        
        ranked = []
        for source, score in scored[:top_k]:
            enhanced = source.copy()
            enhanced["quality_score"] = score.total_score
            enhanced["trust_level"] = score.trust_level
            enhanced["source_type"] = score.source_type.value
            enhanced["score_details"] = {
                "domain": score.domain_score,
                "relevance": score.relevance_score,
                "freshness": score.freshness_score,
                "uniqueness": score.uniqueness_score,
            }
            ranked.append(enhanced)
        
        return ranked
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri döndür"""
        return self._stats.copy()
    
    def clear_cache(self):
        """Cache'i temizle"""
        self._cache.clear()


# Singleton instance
_scorer_instance: Optional[SourceQualityScorer] = None


def get_quality_scorer() -> SourceQualityScorer:
    """Singleton instance al"""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = SourceQualityScorer()
    return _scorer_instance


# === UTILITY FUNCTIONS ===

def score_source(url: str, query: str = "", **kwargs) -> float:
    """
    Basit utility - kaynak puanla.
    
    Returns: 0-1 arası puan
    """
    scorer = get_quality_scorer()
    result = scorer.score_source(url=url, query=query, **kwargs)
    return result.total_score


def rank_search_results(
    results: List[Dict],
    query: str = "",
    top_k: int = 50
) -> List[Dict]:
    """
    Arama sonuçlarını puanla ve sırala.
    
    Usage:
        ranked = rank_search_results(search_results, "python tutorial", 30)
    """
    scorer = get_quality_scorer()
    return scorer.rank_sources(results, query, top_k)


# === TEST ===

if __name__ == "__main__":
    scorer = SourceQualityScorer()
    
    print("=" * 60)
    print("Source Quality Scorer Test")
    print("=" * 60)
    
    test_sources = [
        {
            "url": "https://arxiv.org/abs/2301.00001",
            "title": "Deep Learning Survey 2024",
            "content": "Comprehensive deep learning machine learning neural networks survey",
        },
        {
            "url": "https://en.wikipedia.org/wiki/Machine_learning",
            "title": "Machine learning - Wikipedia",
            "content": "Machine learning is a field of artificial intelligence",
        },
        {
            "url": "https://medium.com/ai-blog/getting-started",
            "title": "Getting Started with AI",
            "content": "Learn about artificial intelligence and machine learning basics",
        },
        {
            "url": "https://stackoverflow.com/questions/12345",
            "title": "How to implement ML in Python?",
            "content": "Python machine learning scikit-learn tensorflow implementation",
        },
        {
            "url": "https://randomsite.com/page",
            "title": "Home Page",
            "content": "Welcome to our website about various topics",
        },
    ]
    
    query = "machine learning deep learning"
    
    print(f"\nQuery: '{query}'")
    print("\n" + "-" * 60)
    
    ranked = scorer.rank_sources(test_sources, query)
    
    for i, source in enumerate(ranked, 1):
        print(f"\n[{i}] {source['title']}")
        print(f"    URL: {source['url']}")
        print(f"    Score: {source['quality_score']:.3f} ({source['trust_level']})")
        print(f"    Type: {source['source_type']}")
        details = source['score_details']
        print(f"    Details: D={details['domain']:.2f} R={details['relevance']:.2f} F={details['freshness']:.2f} U={details['uniqueness']:.2f}")
    
    print(f"\n{'='*60}")
    print(f"Stats: {scorer.get_stats()}")
