"""
🚀 Multi-Provider Search Engine - Premium Edition
=================================================

Endüstri-seviyesi çoklu arama sağlayıcısı sistemi.
Perplexity AI ve ChatGPT Browse kalitesinde.

ÜCRETSİZ API'ler:
- DuckDuckGo (mevcut, sınırsız)
- Brave Search (2000 sorgu/ay ücretsiz)
- Jina Reader (r.jina.ai ücretsiz)
- Wikipedia API (sınırsız)
- Semantic Scholar (akademik, ücretsiz)

ÜCRETLİ (kullanılmıyor):
- ❌ Tavily API (ücretli)
- ❌ Serper API (ücretli) 
- ❌ Bing Search API (ücretli)
- ❌ Google Custom Search (ücretli)

Özellikler:
- Akıllı provider routing
- Paralel arama
- Result fusion (RRF)
- Quality scoring
- Automatic fallback
- Rate limiting
"""

import asyncio
import hashlib
import json
import logging
import re
import time
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
from abc import ABC, abstractmethod
import threading

import httpx

# Premium Cache integration
try:
    from core.premium_cache import get_search_cache, SearchCache
    _search_cache: Optional[SearchCache] = None
    CACHE_ENABLED = True
except ImportError:
    _search_cache = None
    CACHE_ENABLED = False

# Premium Search Enhancement imports
try:
    from core.semantic_query_expander import get_query_expander, SemanticQueryExpander
    from core.smart_title_generator import get_title_generator, SmartTitleGenerator
    PREMIUM_SEARCH_ENABLED = True
except ImportError:
    PREMIUM_SEARCH_ENABLED = False
    get_query_expander = None
    get_title_generator = None

logger = logging.getLogger(__name__)


# ============ ENUMS ============

class SearchProvider(Enum):
    """Arama sağlayıcıları"""
    DUCKDUCKGO = "duckduckgo"
    BRAVE = "brave"
    JINA = "jina"
    WIKIPEDIA = "wikipedia"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    # Ücretli - kullanılmıyor
    TAVILY = "tavily"  # ❌ ÜCRETLI
    SERPER = "serper"  # ❌ ÜCRETLI


class SearchIntent(Enum):
    """Arama niyeti"""
    GENERAL = "general"
    NEWS = "news"
    ACADEMIC = "academic"
    CODE = "code"
    IMAGES = "images"
    VIDEOS = "videos"
    SHOPPING = "shopping"
    LOCAL = "local"


class ContentQuality(Enum):
    """İçerik kalitesi"""
    PREMIUM = "premium"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SearchResult:
    """Tekil arama sonucu"""
    title: str
    url: str
    snippet: str
    content: str = ""
    provider: SearchProvider = SearchProvider.DUCKDUCKGO
    
    # Quality metrics
    relevance_score: float = 0.5
    quality_score: float = 0.5
    freshness_score: float = 0.5
    
    # Metadata
    domain: str = ""
    published_date: Optional[str] = None
    author: Optional[str] = None
    word_count: int = 0
    language: str = "tr"
    
    # Source classification
    source_type: str = "web"  # academic, news, official, blog, forum
    is_primary_source: bool = False
    citation_count: int = 0
    
    # Extra
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedSearchResponse:
    """Birleşik arama yanıtı"""
    query: str
    results: List[SearchResult]
    
    # Aggregated data
    total_results: int = 0
    search_time_ms: int = 0
    providers_used: List[str] = field(default_factory=list)
    providers_failed: List[str] = field(default_factory=list)
    
    # Enhanced features
    instant_answer: Optional[Dict[str, Any]] = None
    knowledge_panel: Optional[Dict[str, Any]] = None
    related_queries: List[str] = field(default_factory=list)
    
    # AI-ready
    context_for_llm: str = ""
    source_citations: List[Dict[str, str]] = field(default_factory=list)
    
    # Status
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============ SEARCH PROVIDER BASE ============

class BaseSearchProvider(ABC):
    """Arama sağlayıcı temel sınıfı"""
    
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
        self._request_count = 0
        self._last_request = 0.0
        self._rate_limit_delay = 0.1  # Minimum delay between requests
    
    @property
    @abstractmethod
    def provider_name(self) -> SearchProvider:
        pass
    
    @property
    def is_available(self) -> bool:
        """Sağlayıcı kullanılabilir mi?"""
        return True
    
    async def _rate_limit(self):
        """Rate limiting"""
        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request = time.time()
        self._request_count += 1
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Arama yap"""
        pass
    
    async def close(self):
        await self.client.aclose()


# ============ DUCKDUCKGO PROVIDER ============

class DuckDuckGoProvider(BaseSearchProvider):
    """DuckDuckGo arama sağlayıcısı - ÜCRETSİZ"""
    
    INSTANT_ANSWER_API = "https://api.duckduckgo.com/"
    HTML_SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    @property
    def provider_name(self) -> SearchProvider:
        return SearchProvider.DUCKDUCKGO
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        await self._rate_limit()
        results = []
        
        try:
            # HTML Search
            data = {"q": query, "kl": "tr-tr"}
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            
            response = await self.client.post(
                self.HTML_SEARCH_URL,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for result in soup.select('.result')[:num_results]:
                    link_elem = result.select_one('.result__a')
                    snippet_elem = result.select_one('.result__snippet')
                    
                    if link_elem:
                        url = link_elem.get('href', '')
                        title = link_elem.get_text(strip=True)
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if url and title:
                            results.append(SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet,
                                domain=urlparse(url).netloc,
                                provider=self.provider_name,
                                relevance_score=0.7
                            ))
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
        
        return results
    
    async def get_instant_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """Instant Answer API"""
        try:
            params = {"q": query, "format": "json", "no_html": 1}
            response = await self.client.get(self.INSTANT_ANSWER_API, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("Abstract"):
                    return {
                        "type": "instant_answer",
                        "title": data.get("Heading", ""),
                        "answer": data.get("Abstract", ""),
                        "source": data.get("AbstractSource", ""),
                        "url": data.get("AbstractURL", ""),
                        "image": data.get("Image", ""),
                    }
        except Exception:
            pass
        return None


# ============ BRAVE SEARCH PROVIDER ============

class BraveSearchProvider(BaseSearchProvider):
    """
    Brave Search API - ÜCRETSİZ TIER
    
    Free tier: 2000 queries/month
    https://brave.com/search/api/
    
    API key environment variable: BRAVE_SEARCH_API_KEY
    """
    
    API_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0):
        super().__init__(timeout)
        self.api_key = api_key or os.environ.get("BRAVE_SEARCH_API_KEY")
        self._rate_limit_delay = 1.0  # Brave requires slower rate
    
    @property
    def provider_name(self) -> SearchProvider:
        return SearchProvider.BRAVE
    
    @property
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        if not self.api_key:
            return []
        
        await self._rate_limit()
        results = []
        
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key
            }
            params = {
                "q": query,
                "count": min(num_results, 20),
                "search_lang": "tr",
                "country": "TR",
                "safesearch": "moderate",
                "freshness": "pw"  # Past week for fresher results
            }
            
            response = await self.client.get(
                self.API_URL,
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                for item in data.get("web", {}).get("results", []):
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("description", ""),
                        domain=urlparse(item.get("url", "")).netloc,
                        provider=self.provider_name,
                        relevance_score=0.85,  # Brave has high quality
                        published_date=item.get("page_age"),
                        language=item.get("language", "tr"),
                        metadata={
                            "age": item.get("age"),
                            "family_friendly": item.get("family_friendly"),
                        }
                    ))
            elif response.status_code == 429:
                logger.warning("Brave Search rate limit reached")
            elif response.status_code == 401:
                logger.error("Brave Search API key invalid")
                
        except Exception as e:
            logger.warning(f"Brave search error: {e}")
        
        return results


# ============ JINA READER PROVIDER ============

class JinaReaderProvider(BaseSearchProvider):
    """
    Jina Reader - ÜCRETSİZ
    
    r.jina.ai: URL'leri LLM-friendly markdown'a çevirir
    s.jina.ai: Web araması + içerik çıkarma
    
    Tamamen ücretsiz, API key gerektirmez!
    """
    
    READER_URL = "https://r.jina.ai/"
    SEARCH_URL = "https://s.jina.ai/"
    
    @property
    def provider_name(self) -> SearchProvider:
        return SearchProvider.JINA
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Jina Search API - arama + içerik"""
        await self._rate_limit()
        results = []
        
        try:
            # s.jina.ai search endpoint
            headers = {
                "Accept": "application/json",
                "X-Return-Format": "markdown"
            }
            
            url = f"{self.SEARCH_URL}{quote_plus(query)}"
            response = await self.client.get(url, headers=headers, timeout=20.0)
            
            if response.status_code == 200:
                content = response.text
                
                # Parse Jina response (markdown format)
                # Jina returns structured markdown with sources
                sections = content.split("\n\n---\n\n")
                
                for i, section in enumerate(sections[:num_results]):
                    if not section.strip():
                        continue
                    
                    # Extract title and content
                    lines = section.strip().split("\n")
                    title = lines[0].lstrip("#").strip() if lines else ""
                    snippet = "\n".join(lines[1:4]) if len(lines) > 1 else ""
                    
                    # Try to find URL in section
                    url_match = re.search(r'https?://[^\s\)]+', section)
                    url = url_match.group(0) if url_match else ""
                    
                    if title and (url or snippet):
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet[:500],
                            content=section[:2000],
                            domain=urlparse(url).netloc if url else "jina.ai",
                            provider=self.provider_name,
                            relevance_score=0.8,
                            quality_score=0.9,  # Jina provides clean content
                        ))
                        
        except Exception as e:
            logger.warning(f"Jina search error: {e}")
        
        return results
    
    async def read_url(self, url: str) -> Optional[str]:
        """URL'yi LLM-friendly markdown'a çevir"""
        try:
            reader_url = f"{self.READER_URL}{url}"
            headers = {"X-Return-Format": "markdown"}
            
            response = await self.client.get(reader_url, headers=headers, timeout=20.0)
            
            if response.status_code == 200:
                return response.text
        except Exception as e:
            logger.warning(f"Jina reader error: {e}")
        
        return None


# ============ WIKIPEDIA PROVIDER ============

class WikipediaProvider(BaseSearchProvider):
    """Wikipedia API - ÜCRETSİZ"""
    
    API_URL = "https://tr.wikipedia.org/w/api.php"
    
    def __init__(self, language: str = "tr", timeout: float = 10.0):
        super().__init__(timeout)
        self.language = language
        self.api_url = f"https://{language}.wikipedia.org/w/api.php"
    
    @property
    def provider_name(self) -> SearchProvider:
        return SearchProvider.WIKIPEDIA
    
    async def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        await self._rate_limit()
        results = []
        
        try:
            # Search
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": num_results,
                "utf8": 1
            }
            
            response = await self.client.get(self.api_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                
                for item in search_results:
                    page_id = item.get("pageid")
                    title = item.get("title", "")
                    snippet = re.sub(r'<[^>]+>', '', item.get("snippet", ""))
                    
                    # Get page content
                    content = await self._get_page_content(page_id)
                    
                    url = f"https://{self.language}.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        content=content,
                        domain="wikipedia.org",
                        provider=self.provider_name,
                        relevance_score=0.9,
                        quality_score=0.95,
                        source_type="encyclopedia",
                        is_primary_source=True,
                    ))
                    
        except Exception as e:
            logger.warning(f"Wikipedia search error: {e}")
        
        return results
    
    async def _get_page_content(self, page_id: int) -> str:
        """Sayfa içeriğini al"""
        try:
            params = {
                "action": "query",
                "pageids": page_id,
                "prop": "extracts",
                "exintro": 1,
                "explaintext": 1,
                "format": "json"
            }
            
            response = await self.client.get(self.api_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                page = pages.get(str(page_id), {})
                return page.get("extract", "")[:3000]
        except Exception:
            pass
        
        return ""


# ============ SEMANTIC SCHOLAR PROVIDER ============

class SemanticScholarProvider(BaseSearchProvider):
    """
    Semantic Scholar API - ÜCRETSİZ
    
    Akademik makaleler için en iyi kaynak.
    https://api.semanticscholar.org/
    
    Rate limit: 100 requests per 5 minutes (free tier)
    """
    
    API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    def __init__(self, timeout: float = 15.0):
        super().__init__(timeout)
        self._rate_limit_delay = 3.0  # Conservative rate limit
    
    @property
    def provider_name(self) -> SearchProvider:
        return SearchProvider.SEMANTIC_SCHOLAR
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        await self._rate_limit()
        results = []
        
        try:
            params = {
                "query": query,
                "limit": min(num_results, 20),
                "fields": "title,abstract,url,year,citationCount,authors,venue"
            }
            
            response = await self.client.get(self.API_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                for paper in data.get("data", []):
                    authors = ", ".join([a.get("name", "") for a in paper.get("authors", [])[:3]])
                    
                    results.append(SearchResult(
                        title=paper.get("title", ""),
                        url=paper.get("url", f"https://api.semanticscholar.org/{paper.get('paperId', '')}"),
                        snippet=paper.get("abstract", "")[:500] if paper.get("abstract") else "",
                        content=paper.get("abstract", ""),
                        domain="semanticscholar.org",
                        provider=self.provider_name,
                        relevance_score=0.9,
                        quality_score=0.95,
                        source_type="academic",
                        is_primary_source=True,
                        author=authors,
                        citation_count=paper.get("citationCount", 0),
                        published_date=str(paper.get("year", "")),
                        metadata={
                            "venue": paper.get("venue", ""),
                            "paper_id": paper.get("paperId"),
                        }
                    ))
                    
        except Exception as e:
            logger.warning(f"Semantic Scholar search error: {e}")
        
        return results


# ============ RESULT FUSION ============

class ResultFusion:
    """
    Reciprocal Rank Fusion (RRF) ile sonuç birleştirme.
    
    Birden fazla kaynaktan gelen sonuçları akıllıca birleştirir.
    """
    
    def __init__(self, k: int = 60):
        self.k = k  # RRF constant
    
    def fuse(
        self,
        result_lists: List[List[SearchResult]],
        provider_weights: Optional[Dict[SearchProvider, float]] = None
    ) -> List[SearchResult]:
        """
        RRF ile sonuçları birleştir.
        
        Args:
            result_lists: Her provider'dan sonuç listesi
            provider_weights: Provider ağırlıkları
            
        Returns:
            Birleştirilmiş ve sıralanmış sonuçlar
        """
        if not provider_weights:
            provider_weights = {
                SearchProvider.WIKIPEDIA: 1.2,
                SearchProvider.SEMANTIC_SCHOLAR: 1.3,
                SearchProvider.BRAVE: 1.1,
                SearchProvider.JINA: 1.0,
                SearchProvider.DUCKDUCKGO: 0.9,
            }
        
        # URL -> (result, score)
        url_scores: Dict[str, Tuple[SearchResult, float]] = {}
        
        for result_list in result_lists:
            for rank, result in enumerate(result_list, 1):
                url = result.url
                
                # RRF score
                weight = provider_weights.get(result.provider, 1.0)
                rrf_score = weight * (1.0 / (self.k + rank))
                
                if url in url_scores:
                    existing_result, existing_score = url_scores[url]
                    # Merge and update score
                    merged = self._merge_results(existing_result, result)
                    url_scores[url] = (merged, existing_score + rrf_score)
                else:
                    url_scores[url] = (result, rrf_score)
        
        # Sort by score
        sorted_results = sorted(
            url_scores.values(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Update scores and return
        final_results = []
        for result, score in sorted_results:
            result.relevance_score = min(1.0, score * 10)  # Normalize
            final_results.append(result)
        
        return final_results
    
    def _merge_results(self, r1: SearchResult, r2: SearchResult) -> SearchResult:
        """İki sonucu birleştir"""
        # Keep the one with more content
        if len(r2.content) > len(r1.content):
            r1.content = r2.content
        if len(r2.snippet) > len(r1.snippet):
            r1.snippet = r2.snippet
        
        # Merge metadata
        r1.metadata.update(r2.metadata)
        
        # Keep best quality indicators
        r1.quality_score = max(r1.quality_score, r2.quality_score)
        r1.citation_count = max(r1.citation_count, r2.citation_count)
        
        return r1


# ============ INTENT DETECTOR ============

class IntentDetector:
    """Arama niyetini tespit et"""
    
    PATTERNS = {
        SearchIntent.NEWS: [
            r'\b(haber|news|gündem|son dakika|breaking|bugün|dün)\b',
            r'\b(açıklama|duyuru|announcement)\b',
        ],
        SearchIntent.ACADEMIC: [
            r'\b(makale|paper|araştırma|research|study|scientist)\b',
            r'\b(bilimsel|academic|scholar|journal|thesis)\b',
            r'\b(pdf|doi|citation|reference)\b',
        ],
        SearchIntent.CODE: [
            r'\b(kod|code|programming|github|stackoverflow)\b',
            r'\b(python|javascript|java|api|error|bug|fix)\b',
            r'\b(function|class|method|library|framework)\b',
        ],
        SearchIntent.SHOPPING: [
            r'\b(satın al|buy|fiyat|price|ucuz|cheap|indirim)\b',
            r'\b(amazon|trendyol|hepsiburada|shop)\b',
        ],
    }
    
    def detect(self, query: str) -> SearchIntent:
        query_lower = query.lower()
        
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.I):
                    return intent
        
        return SearchIntent.GENERAL


# ============ MAIN ENGINE ============

class MultiProviderSearchEngine:
    """
    Multi-Provider Search Engine
    
    Endüstri standardında çoklu kaynak arama motoru.
    Perplexity AI ve ChatGPT Browse kalitesinde.
    """
    
    def __init__(
        self,
        brave_api_key: Optional[str] = None,
        enable_brave: bool = True,
        enable_jina: bool = True,
        enable_wikipedia: bool = True,
        enable_semantic_scholar: bool = True,
    ):
        # Providers
        self.providers: Dict[SearchProvider, BaseSearchProvider] = {}
        
        # Always include DuckDuckGo (free, no limit)
        self.providers[SearchProvider.DUCKDUCKGO] = DuckDuckGoProvider()
        
        # Brave (free tier: 2000/month)
        if enable_brave:
            brave = BraveSearchProvider(api_key=brave_api_key)
            if brave.is_available:
                self.providers[SearchProvider.BRAVE] = brave
        
        # Jina (free, no limit)
        if enable_jina:
            self.providers[SearchProvider.JINA] = JinaReaderProvider()
        
        # Wikipedia (free, no limit)
        if enable_wikipedia:
            self.providers[SearchProvider.WIKIPEDIA] = WikipediaProvider()
        
        # Semantic Scholar (free, rate limited)
        if enable_semantic_scholar:
            self.providers[SearchProvider.SEMANTIC_SCHOLAR] = SemanticScholarProvider()
        
        # Utilities
        self.fusion = ResultFusion()
        self.intent_detector = IntentDetector()
        
        # Stats
        self.stats = {
            "total_searches": 0,
            "provider_usage": {},
            "avg_search_time_ms": 0,
        }
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        providers: Optional[List[SearchProvider]] = None,
        intent: Optional[SearchIntent] = None,
        parallel: bool = True,
        use_cache: bool = True,
    ) -> UnifiedSearchResponse:
        """
        Çoklu kaynak araması yap.
        
        Args:
            query: Arama sorgusu
            num_results: İstenen sonuç sayısı
            providers: Kullanılacak sağlayıcılar (None = otomatik)
            intent: Arama niyeti (None = otomatik tespit)
            parallel: Paralel arama
            use_cache: Cache kullan (varsayılan: True)
            
        Returns:
            UnifiedSearchResponse
        """
        start_time = time.time()
        self.stats["total_searches"] += 1
        
        # Cache check
        if use_cache and CACHE_ENABLED:
            global _search_cache
            if _search_cache is None:
                _search_cache = get_search_cache()
            
            provider_names = [p.value for p in providers] if providers else None
            cached_response = _search_cache.get_results(query, provider_names)
            if cached_response is not None:
                logger.info(f"Cache hit for query: {query[:50]}...")
                # Update timestamp
                cached_response.timestamp = datetime.now().isoformat()
                return cached_response
        
        # Detect intent
        if intent is None:
            intent = self.intent_detector.detect(query)
        
        # Select providers based on intent
        if providers is None:
            providers = self._select_providers_for_intent(intent)
        
        # Search all providers
        all_results: List[List[SearchResult]] = []
        providers_used = []
        providers_failed = []
        
        if parallel:
            # Parallel search
            tasks = []
            for provider in providers:
                if provider in self.providers:
                    tasks.append(self._search_provider(provider, query, num_results))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for provider, result in zip(providers, results):
                if isinstance(result, Exception):
                    providers_failed.append(provider.value)
                    logger.warning(f"Provider {provider.value} failed: {result}")
                elif result:
                    all_results.append(result)
                    providers_used.append(provider.value)
        else:
            # Sequential search
            for provider in providers:
                if provider in self.providers:
                    try:
                        results = await self._search_provider(provider, query, num_results)
                        if results:
                            all_results.append(results)
                            providers_used.append(provider.value)
                    except Exception as e:
                        providers_failed.append(provider.value)
                        logger.warning(f"Provider {provider.value} failed: {e}")
        
        # Fuse results
        fused_results = self.fusion.fuse(all_results) if all_results else []
        
        # Limit results
        fused_results = fused_results[:num_results]
        
        # Get instant answer from DuckDuckGo
        instant_answer = None
        if SearchProvider.DUCKDUCKGO in self.providers:
            ddg = self.providers[SearchProvider.DUCKDUCKGO]
            if isinstance(ddg, DuckDuckGoProvider):
                instant_answer = await ddg.get_instant_answer(query)
        
        # Generate LLM context
        context = self._generate_llm_context(query, fused_results, instant_answer)
        
        # Generate citations
        citations = self._generate_citations(fused_results)
        
        # Related queries (from results)
        related_queries = self._extract_related_queries(fused_results, query)
        
        # Calculate search time
        search_time_ms = int((time.time() - start_time) * 1000)
        self.stats["avg_search_time_ms"] = (
            self.stats["avg_search_time_ms"] * 0.9 + search_time_ms * 0.1
        )
        
        response = UnifiedSearchResponse(
            query=query,
            results=fused_results,
            total_results=len(fused_results),
            search_time_ms=search_time_ms,
            providers_used=providers_used,
            providers_failed=providers_failed,
            instant_answer=instant_answer,
            related_queries=related_queries,
            context_for_llm=context,
            source_citations=citations,
            success=len(fused_results) > 0,
        )
        
        # Cache results
        if use_cache and CACHE_ENABLED and response.success:
            provider_names = [p.value for p in providers] if providers else None
            _search_cache.set_results(query, response, provider_names, ttl_seconds=1800)
            logger.info(f"Cached results for query: {query[:50]}...")
        
        return response
    
    async def _search_provider(
        self,
        provider: SearchProvider,
        query: str,
        num_results: int
    ) -> List[SearchResult]:
        """Tek provider'da arama"""
        if provider not in self.providers:
            return []
        
        return await self.providers[provider].search(query, num_results)
    
    def _select_providers_for_intent(self, intent: SearchIntent) -> List[SearchProvider]:
        """Intent'e göre provider seç"""
        available = list(self.providers.keys())
        
        if intent == SearchIntent.ACADEMIC:
            # Academic: Semantic Scholar + Wikipedia öncelikli
            priority = [
                SearchProvider.SEMANTIC_SCHOLAR,
                SearchProvider.WIKIPEDIA,
                SearchProvider.JINA,
                SearchProvider.BRAVE,
                SearchProvider.DUCKDUCKGO,
            ]
        elif intent == SearchIntent.NEWS:
            # News: Brave + DuckDuckGo (fresh results)
            priority = [
                SearchProvider.BRAVE,
                SearchProvider.DUCKDUCKGO,
                SearchProvider.JINA,
            ]
        elif intent == SearchIntent.CODE:
            # Code: Jina + DDG (stackoverflow, github)
            priority = [
                SearchProvider.JINA,
                SearchProvider.DUCKDUCKGO,
                SearchProvider.BRAVE,
            ]
        else:
            # General: All providers
            priority = [
                SearchProvider.DUCKDUCKGO,
                SearchProvider.BRAVE,
                SearchProvider.JINA,
                SearchProvider.WIKIPEDIA,
            ]
        
        return [p for p in priority if p in available]
    
    def _generate_llm_context(
        self,
        query: str,
        results: List[SearchResult],
        instant_answer: Optional[Dict]
    ) -> str:
        """LLM için optimize edilmiş bağlam oluştur"""
        parts = []
        
        # Instant answer
        if instant_answer:
            parts.append(f"""
📌 **HIZLI CEVAP:**
{instant_answer.get('title', '')}
{instant_answer.get('answer', '')}
Kaynak: {instant_answer.get('source', '')}
""")
        
        # Results
        parts.append(f"\n🔍 **ARAMA SONUÇLARI** (Sorgu: {query}):\n")
        
        for i, result in enumerate(results[:50], 1):
            source_badge = {
                "academic": "🎓",
                "encyclopedia": "📚",
                "news": "📰",
                "official": "🏛️",
                "blog": "✍️",
            }.get(result.source_type, "🌐")
            
            content = result.content if result.content else result.snippet
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            parts.append(f"""
---
**[{i}] {result.title}** {source_badge}
URL: {result.url}
Güvenilirlik: {'⭐' * int(result.quality_score * 5)}

{content}
""")
        
        return "\n".join(parts)
    
    def _generate_citations(self, results: List[SearchResult]) -> List[Dict[str, str]]:
        """Kaynak atıfları oluştur"""
        citations = []
        
        for i, result in enumerate(results[:10], 1):
            citation = {
                "index": str(i),
                "title": result.title,
                "url": result.url,
                "domain": result.domain,
                "type": result.source_type,
            }
            
            if result.author:
                citation["author"] = result.author
            if result.published_date:
                citation["date"] = result.published_date
            
            citations.append(citation)
        
        return citations
    
    def _extract_related_queries(
        self,
        results: List[SearchResult],
        original_query: str
    ) -> List[str]:
        """İlgili sorgular çıkar"""
        related = set()
        query_words = set(original_query.lower().split())
        
        for result in results[:5]:
            # Extract from titles
            title_words = result.title.lower().split()
            for word in title_words:
                if word not in query_words and len(word) > 4:
                    related.add(f"{original_query} {word}")
        
        return list(related)[:5]
    
    async def read_url(self, url: str) -> Optional[str]:
        """URL içeriğini oku (Jina Reader)"""
        if SearchProvider.JINA in self.providers:
            jina = self.providers[SearchProvider.JINA]
            if isinstance(jina, JinaReaderProvider):
                return await jina.read_url(url)
        return None
    
    async def premium_search(
        self,
        query: str,
        num_results: int = 50,
        providers: Optional[List[SearchProvider]] = None,
        enable_query_expansion: bool = True,
        enable_smart_titles: bool = True,
        max_query_variations: int = 8,
        parallel: bool = True,
    ) -> UnifiedSearchResponse:
        """
        🔥 Premium Search - Semantic Query Expansion + Smart Titles
        
        Tek sorgu yerine 5-10 varyasyon ile arama yapar.
        Generic başlıkları akıllı başlıklara dönüştürür.
        
        Args:
            query: Orijinal sorgu
            num_results: Toplam sonuç sayısı (varsayılan: 50)
            providers: Kullanılacak sağlayıcılar
            enable_query_expansion: Semantic expansion kullansın mı
            enable_smart_titles: Başlık iyileştirme aktif mi
            max_query_variations: Maksimum sorgu varyasyonu
            parallel: Paralel arama
            
        Returns:
            UnifiedSearchResponse with 40-50 unique sources
        """
        start_time = time.time()
        
        # Query expansion
        all_queries = [query]
        if enable_query_expansion and PREMIUM_SEARCH_ENABLED and get_query_expander:
            try:
                expander = get_query_expander()
                expansion_result = await expander.expand_query(query, max_query_variations)
                all_queries = expansion_result.get_all_queries()
                logger.info(f"🔍 Query expanded: '{query}' → {len(all_queries)} variations")
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}")
        
        # Search with all query variations
        all_results: List[SearchResult] = []
        seen_urls: Set[str] = set()
        providers_used_set: Set[str] = set()
        providers_failed_set: Set[str] = set()
        
        # Calculate results per query
        results_per_query = max(10, num_results // len(all_queries))
        
        for q in all_queries:
            try:
                response = await self.search(
                    query=q,
                    num_results=results_per_query,
                    providers=providers,
                    parallel=parallel,
                    use_cache=True
                )
                
                providers_used_set.update(response.providers_used)
                providers_failed_set.update(response.providers_failed)
                
                # Deduplicate by URL
                for result in response.results:
                    url_key = result.url.lower().rstrip('/')
                    if url_key not in seen_urls:
                        seen_urls.add(url_key)
                        all_results.append(result)
                        
                        if len(all_results) >= num_results:
                            break
                            
            except Exception as e:
                logger.warning(f"Search failed for query '{q[:30]}...': {e}")
            
            if len(all_results) >= num_results:
                break
        
        # Smart title improvement
        if enable_smart_titles and PREMIUM_SEARCH_ENABLED and get_title_generator and all_results:
            try:
                title_gen = get_title_generator()
                
                # Batch improve titles
                for result in all_results:
                    title_result = title_gen.generate_title_sync(
                        url=result.url,
                        raw_title=result.title,
                        query=query
                    )
                    if title_result.is_improved:
                        result.title = title_result.smart_title
                
                logger.info(f"📝 Titles improved for {len(all_results)} results")
            except Exception as e:
                logger.warning(f"Title improvement failed: {e}")
        
        # Domain diversity - limit same domain results
        domain_counts: Dict[str, int] = {}
        diverse_results: List[SearchResult] = []
        MAX_SAME_DOMAIN = 5
        
        for result in all_results:
            domain = result.domain
            current_count = domain_counts.get(domain, 0)
            
            if current_count < MAX_SAME_DOMAIN:
                diverse_results.append(result)
                domain_counts[domain] = current_count + 1
        
        # Sort by quality score
        diverse_results.sort(key=lambda r: r.quality_score, reverse=True)
        final_results = diverse_results[:num_results]
        
        # Regenerate context with all results
        context = self._generate_llm_context(query, final_results, None)
        citations = self._generate_citations(final_results)
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return UnifiedSearchResponse(
            query=query,
            results=final_results,
            total_results=len(final_results),
            search_time_ms=search_time_ms,
            providers_used=list(providers_used_set),
            providers_failed=list(providers_failed_set - providers_used_set),
            instant_answer=None,
            related_queries=[q for q in all_queries[1:6] if q != query],
            context_for_llm=context,
            source_citations=citations,
            success=len(final_results) > 0,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler"""
        return {
            **self.stats,
            "available_providers": [p.value for p in self.providers.keys()],
        }
    
    async def close(self):
        """Cleanup"""
        for provider in self.providers.values():
            await provider.close()


# ============ SINGLETON ============

_engine: Optional[MultiProviderSearchEngine] = None

def get_multi_search_engine() -> MultiProviderSearchEngine:
    """Singleton instance"""
    global _engine
    if _engine is None:
        _engine = MultiProviderSearchEngine()
    return _engine


# ============ TEST ============

async def test_search():
    """Test function"""
    engine = get_multi_search_engine()
    
    print("Available providers:", [p.value for p in engine.providers.keys()])
    
    result = await engine.search("Python machine learning", num_results=5)
    
    print(f"\nQuery: {result.query}")
    print(f"Time: {result.search_time_ms}ms")
    print(f"Providers used: {result.providers_used}")
    print(f"Total results: {result.total_results}")
    
    if result.instant_answer:
        print(f"\nInstant Answer: {result.instant_answer.get('title')}")
    
    print("\n--- RESULTS ---")
    for i, r in enumerate(result.results, 1):
        print(f"\n[{i}] {r.title}")
        print(f"    URL: {r.url}")
        print(f"    Provider: {r.provider.value}")
        print(f"    Quality: {r.quality_score:.2f}")
    
    await engine.close()


if __name__ == "__main__":
    asyncio.run(test_search())
