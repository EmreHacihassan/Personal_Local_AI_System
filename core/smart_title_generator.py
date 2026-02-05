"""
📝 Smart Title Generator - Premium Search Enhancement

HTML title'larını anlamlı, özetlenmiş başlıklara dönüştürür.
Generic başlıkları query-relevant başlıklara çevirir.

Author: Enterprise AI Team
Date: 2025-02
"""

import asyncio
import logging
import re
import hashlib
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class TitleResult:
    """Başlık üretim sonucu"""
    original_title: str
    smart_title: str
    is_improved: bool
    quality_score: float  # 0-1
    method: str  # "llm", "rule", "original"
    keywords_matched: List[str]


class SmartTitleGenerator:
    """
    Akıllı Başlık Üretici
    
    Raw HTML title'ları query-relevant, anlamlı başlıklara dönüştürür.
    """
    
    # Generic title patterns that need improvement
    GENERIC_PATTERNS = [
        r"^home\s*[-|:–]",
        r"^welcome\s*(to)?\s*[-|:–]",
        r"^page\s+\d+",
        r"^untitled",
        r"^index\s*(of)?",
        r"^site\s*[-|:–]",
        r"^main\s*[-|:–]",
        r"^\w+\s*[-|:–]\s*\w+$",  # Just "Site - Page" pattern
        r"^document\s*\d*$",
        r"^\d+\s*[-|:–]",
        r"^loading",
        r"^please wait",
    ]
    
    # Title cleanup patterns
    CLEANUP_PATTERNS = [
        (r"\s*[-|:–]\s*(home|anasayfa|homepage|main page)\s*$", ""),
        (r"\s*[-|:–]\s*(official site|official website)\s*$", ""),
        (r"^\s*(the|a|an)\s+", ""),
        (r"\s*\|\s*page\s+\d+\s*$", ""),
        (r"\s*[-|:–]\s*$", ""),
        (r"^\s*[-|:–]\s*", ""),
        (r"\s+", " "),
    ]
    
    # Domain to category mapping
    DOMAIN_CATEGORIES = {
        "wikipedia.org": "📚 Wiki",
        "arxiv.org": "🎓 Academic",
        "github.com": "💻 Code",
        "stackoverflow.com": "❓ Q&A",
        "medium.com": "✍️ Blog",
        "dev.to": "💻 Dev",
        "youtube.com": "🎬 Video",
        "docs.python.org": "📖 Docs",
        "docs.microsoft.com": "📖 Docs",
        "developer.mozilla.org": "📖 MDN",
    }
    
    LLM_TITLE_PROMPT = """Aşağıdaki web sayfası için kısa ve açıklayıcı bir başlık oluştur.

URL: {url}
Mevcut Başlık: {title}
İçerik Özeti: {content_snippet}
Arama Sorgusu: {query}

KURALLAR:
- Maksimum 60 karakter
- Sayfa içeriğini yansıtmalı
- Arama sorgusuyla ilişkili olmalı
- Türkçe sorgu ise Türkçe, İngilizce ise İngilizce

Sadece yeni başlığı yaz, başka bir şey yazma:"""

    def __init__(self, llm_client=None, cache_enabled: bool = True):
        """
        Args:
            llm_client: LLM client (optional)
            cache_enabled: Title cache kullanılsın mı
        """
        self.llm_client = llm_client
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, TitleResult] = {}
        self._stats = {
            "total_generated": 0,
            "llm_improved": 0,
            "rule_improved": 0,
            "cache_hits": 0,
        }
    
    def _get_cache_key(self, url: str, title: str) -> str:
        """Cache key oluştur"""
        combined = f"{url}:{title}".lower()
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _is_generic_title(self, title: str, url: str) -> bool:
        """Başlık generic mi kontrol et"""
        title_lower = title.lower().strip()
        
        # Check against generic patterns
        for pattern in self.GENERIC_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True
        
        # Check if title is just the domain name
        try:
            domain = urlparse(url).netloc.replace("www.", "")
            if title_lower in domain.lower() or domain.lower() in title_lower:
                return len(title) < 30  # Short domain-only titles are generic
        except:
            pass
        
        # Check if title is too short
        if len(title) < 10:
            return True
        
        # Check if title is too long (auto-generated)
        if len(title) > 150:
            return True
        
        return False
    
    def _clean_title(self, title: str) -> str:
        """Başlığı temizle"""
        cleaned = title.strip()
        
        for pattern, replacement in self.CLEANUP_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[!?]+$', '', cleaned)
        cleaned = re.sub(r'^[!?]+', '', cleaned)
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _truncate_title(self, title: str, max_length: int = 60) -> str:
        """Başlığı kısalt"""
        if len(title) <= max_length:
            return title
        
        # Try to cut at word boundary
        truncated = title[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.7:
            truncated = truncated[:last_space]
        
        return truncated.rstrip('.,;:-') + "..."
    
    def _extract_title_from_url(self, url: str) -> Optional[str]:
        """URL'den başlık çıkarmaya çalış"""
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return None
            
            # Get last path segment
            segments = path.split('/')
            last_segment = segments[-1] if segments else ""
            
            # Remove file extension
            if '.' in last_segment:
                last_segment = last_segment.rsplit('.', 1)[0]
            
            # Convert URL slug to title
            title = last_segment.replace('-', ' ').replace('_', ' ')
            title = title.title()
            
            if len(title) > 5:
                return title
        except:
            pass
        
        return None
    
    def _get_domain_category(self, url: str) -> Optional[str]:
        """Domain'den kategori al"""
        try:
            domain = urlparse(url).netloc.lower()
            
            for d, category in self.DOMAIN_CATEGORIES.items():
                if d in domain:
                    return category
        except:
            pass
        
        return None
    
    def _calculate_title_quality(
        self,
        title: str,
        query: str,
        url: str
    ) -> Tuple[float, List[str]]:
        """Başlık kalitesini hesapla"""
        score = 0.5  # Base score
        matched_keywords = []
        
        title_lower = title.lower()
        query_lower = query.lower()
        
        # Extract query keywords
        query_words = set(re.findall(r'\w+', query_lower))
        title_words = set(re.findall(r'\w+', title_lower))
        
        # Check keyword overlap
        common_words = query_words & title_words
        if common_words:
            overlap_ratio = len(common_words) / len(query_words)
            score += overlap_ratio * 0.3
            matched_keywords = list(common_words)
        
        # Length bonus (optimal: 30-60 chars)
        if 30 <= len(title) <= 60:
            score += 0.1
        elif len(title) < 15 or len(title) > 100:
            score -= 0.1
        
        # Category bonus
        category = self._get_domain_category(url)
        if category:
            score += 0.05
        
        # Generic penalty
        if self._is_generic_title(title, url):
            score -= 0.2
        
        return min(1.0, max(0.0, score)), matched_keywords
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """LLM'i çağır"""
        if not self.llm_client:
            try:
                from core.llm_manager import llm_manager
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: llm_manager.generate(prompt, model="qwen3:4b")
                )
                return response
            except Exception as e:
                logger.warning(f"LLM call failed: {e}")
                return None
        
        try:
            if hasattr(self.llm_client, 'generate'):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.llm_client.generate(prompt)
                )
                return response
        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
        
        return None
    
    def generate_title_sync(
        self,
        url: str,
        raw_title: str,
        query: str = "",
        content_snippet: str = ""
    ) -> TitleResult:
        """Senkron başlık üretimi (rule-based only)"""
        self._stats["total_generated"] += 1
        
        # Check cache
        cache_key = self._get_cache_key(url, raw_title)
        if self.cache_enabled and cache_key in self._cache:
            self._stats["cache_hits"] += 1
            return self._cache[cache_key]
        
        # Clean the title
        cleaned = self._clean_title(raw_title)
        
        # Check if needs improvement
        is_generic = self._is_generic_title(cleaned, url)
        
        smart_title = cleaned
        method = "original"
        
        if is_generic:
            # Try URL-based title
            url_title = self._extract_title_from_url(url)
            if url_title and len(url_title) > 10:
                smart_title = url_title
                method = "rule"
                self._stats["rule_improved"] += 1
            
            # Add domain category prefix
            category = self._get_domain_category(url)
            if category and category not in smart_title:
                smart_title = f"{category} {smart_title}"
        
        # Truncate if needed
        smart_title = self._truncate_title(smart_title)
        
        # Calculate quality
        quality_score, keywords = self._calculate_title_quality(smart_title, query, url)
        
        result = TitleResult(
            original_title=raw_title,
            smart_title=smart_title,
            is_improved=(method != "original"),
            quality_score=quality_score,
            method=method,
            keywords_matched=keywords
        )
        
        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = result
        
        return result
    
    async def generate_title(
        self,
        url: str,
        raw_title: str,
        query: str = "",
        content_snippet: str = "",
        use_llm: bool = True
    ) -> TitleResult:
        """
        Akıllı başlık üret.
        
        Args:
            url: Sayfa URL'i
            raw_title: Ham HTML title
            query: Arama sorgusu (optional)
            content_snippet: İçerik önizlemesi (optional)
            use_llm: LLM kullanılsın mı
            
        Returns:
            TitleResult with smart title
        """
        self._stats["total_generated"] += 1
        
        # Check cache
        cache_key = self._get_cache_key(url, raw_title)
        if self.cache_enabled and cache_key in self._cache:
            self._stats["cache_hits"] += 1
            return self._cache[cache_key]
        
        # Clean the title first
        cleaned = self._clean_title(raw_title)
        
        # Check if needs improvement
        is_generic = self._is_generic_title(cleaned, url)
        
        smart_title = cleaned
        method = "original"
        
        if is_generic and use_llm and (query or content_snippet):
            # Try LLM improvement
            prompt = self.LLM_TITLE_PROMPT.format(
                url=url,
                title=raw_title,
                content_snippet=content_snippet[:300] if content_snippet else "N/A",
                query=query or "N/A"
            )
            
            llm_title = await self._call_llm(prompt)
            
            if llm_title:
                llm_title = llm_title.strip().strip('"\'')
                if 10 < len(llm_title) < 100:
                    smart_title = self._truncate_title(llm_title)
                    method = "llm"
                    self._stats["llm_improved"] += 1
        
        if is_generic and method == "original":
            # Fallback to rule-based
            url_title = self._extract_title_from_url(url)
            if url_title and len(url_title) > 10:
                smart_title = url_title
                method = "rule"
                self._stats["rule_improved"] += 1
            
            # Add domain category
            category = self._get_domain_category(url)
            if category and category not in smart_title:
                smart_title = f"{category} {smart_title}"
        
        # Truncate if needed
        smart_title = self._truncate_title(smart_title)
        
        # Calculate quality
        quality_score, keywords = self._calculate_title_quality(smart_title, query, url)
        
        result = TitleResult(
            original_title=raw_title,
            smart_title=smart_title,
            is_improved=(method != "original"),
            quality_score=quality_score,
            method=method,
            keywords_matched=keywords
        )
        
        # Cache result
        if self.cache_enabled:
            self._cache[cache_key] = result
        
        return result
    
    async def batch_generate(
        self,
        items: List[Dict],
        query: str = ""
    ) -> List[TitleResult]:
        """
        Birden fazla başlık üret.
        
        Args:
            items: List of {"url": ..., "title": ..., "snippet": ...}
            query: Arama sorgusu
            
        Returns:
            List of TitleResult
        """
        tasks = []
        for item in items:
            tasks.append(self.generate_title(
                url=item.get("url", ""),
                raw_title=item.get("title", ""),
                query=query,
                content_snippet=item.get("snippet", ""),
                use_llm=True
            ))
        
        return await asyncio.gather(*tasks)
    
    def get_stats(self) -> Dict[str, int]:
        """İstatistikleri döndür"""
        return self._stats.copy()
    
    def clear_cache(self):
        """Cache'i temizle"""
        self._cache.clear()


# Singleton instance
_generator_instance: Optional[SmartTitleGenerator] = None


def get_title_generator() -> SmartTitleGenerator:
    """Singleton title generator instance'ı al"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = SmartTitleGenerator()
    return _generator_instance


# === UTILITY FUNCTIONS ===

def improve_title(url: str, title: str, query: str = "") -> str:
    """
    Basit utility function - başlığı iyileştir.
    
    Usage:
        better_title = improve_title("https://example.com/ml-guide", "Home", "machine learning")
    """
    generator = get_title_generator()
    result = generator.generate_title_sync(url, title, query)
    return result.smart_title


async def improve_titles_batch(
    sources: List[Dict],
    query: str = ""
) -> List[Dict]:
    """
    Kaynak listesindeki başlıkları iyileştir.
    
    Usage:
        sources = [{"url": "...", "title": "...", "snippet": "..."}]
        improved = await improve_titles_batch(sources, "python tutorial")
    """
    generator = get_title_generator()
    results = await generator.batch_generate(sources, query)
    
    improved_sources = []
    for source, result in zip(sources, results):
        improved = source.copy()
        improved["title"] = result.smart_title
        improved["title_quality"] = result.quality_score
        improved["title_improved"] = result.is_improved
        improved_sources.append(improved)
    
    return improved_sources


# === TEST ===

if __name__ == "__main__":
    async def test():
        generator = SmartTitleGenerator()
        
        test_cases = [
            {
                "url": "https://example.com/python-machine-learning-tutorial",
                "title": "Home - Example",
                "query": "Python ML tutorial",
            },
            {
                "url": "https://wikipedia.org/wiki/Artificial_intelligence",
                "title": "Artificial intelligence - Wikipedia",
                "query": "yapay zeka nedir",
            },
            {
                "url": "https://github.com/tensorflow/tensorflow",
                "title": "GitHub - tensorflow/tensorflow: An Open Source Machine Learning Framework",
                "query": "tensorflow",
            },
            {
                "url": "https://medium.com/some-long-article-about-react",
                "title": "🚀 10 Amazing React Tips You Need to Know in 2024!!!",
                "query": "react tips",
            },
        ]
        
        for case in test_cases:
            print(f"\n{'='*60}")
            print(f"URL: {case['url']}")
            print(f"Original: {case['title']}")
            print(f"Query: {case['query']}")
            
            result = await generator.generate_title(
                url=case["url"],
                raw_title=case["title"],
                query=case["query"]
            )
            
            print(f"\nSmart Title: {result.smart_title}")
            print(f"Quality: {result.quality_score:.2f}")
            print(f"Method: {result.method}")
            print(f"Improved: {result.is_improved}")
            print(f"Keywords: {result.keywords_matched}")
        
        print(f"\n{'='*60}")
        print(f"Stats: {generator.get_stats()}")
    
    asyncio.run(test())
