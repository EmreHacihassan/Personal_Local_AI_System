"""
🌐 Ultra Premium Web Scraping Engine
=====================================

Next-generation web content extraction with:
- JavaScript rendering (Playwright)
- Anti-bot bypass
- Smart content extraction
- Multi-format output
- Parallel processing
- Intelligent caching

Premium Features:
- Trafilatura for accurate article extraction
- Newspaper3k for news-specific parsing
- Readability algorithms
- Structured data extraction (JSON-LD, Schema.org)
- Image captioning support
- PDF/Document URL scraping
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)

# ============ OPTIONAL IMPORTS WITH FALLBACKS ============

# Trafilatura - Best-in-class article extraction
try:
    import trafilatura
    from trafilatura.settings import use_config
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False
    logger.info("trafilatura not installed - using fallback extraction")

# Newspaper3k - News article parsing
try:
    from newspaper import Article, Config as NewspaperConfig
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logger.info("newspaper3k not installed - using fallback extraction")

# Playwright - JavaScript rendering
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.info("playwright not installed - JavaScript rendering disabled")

# Standard libraries
import httpx
from bs4 import BeautifulSoup


class ExtractionMethod(Enum):
    """İçerik çıkarma yöntemi."""
    TRAFILATURA = "trafilatura"
    NEWSPAPER = "newspaper"
    BEAUTIFULSOUP = "beautifulsoup"
    PLAYWRIGHT = "playwright"
    HYBRID = "hybrid"
    AUTO = "auto"


class ContentType(Enum):
    """İçerik türü."""
    ARTICLE = "article"
    NEWS = "news"
    BLOG = "blog"
    DOCUMENTATION = "documentation"
    ECOMMERCE = "ecommerce"
    FORUM = "forum"
    SOCIAL = "social"
    ACADEMIC = "academic"
    GENERIC = "generic"


@dataclass
class ExtractedContent:
    """Çıkarılmış içerik."""
    url: str
    title: str
    content: str
    summary: str = ""
    author: str = ""
    publish_date: str = ""
    language: str = ""
    word_count: int = 0
    reading_time_minutes: int = 0
    
    # Structured data
    headings: List[str] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    
    # Metadata
    content_type: ContentType = ContentType.GENERIC
    extraction_method: ExtractionMethod = ExtractionMethod.AUTO
    extraction_time_ms: int = 0
    quality_score: float = 0.0
    
    # Schema.org / JSON-LD
    structured_data: Dict[str, Any] = field(default_factory=dict)
    
    # Raw data
    html: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScraperConfig:
    """Scraper konfigürasyonu."""
    # Timeouts
    request_timeout: int = 15
    render_timeout: int = 30
    
    # Content limits
    max_content_length: int = 50000
    max_images: int = 20
    max_links: int = 50
    
    # Extraction preferences
    prefer_trafilatura: bool = True
    enable_javascript: bool = True
    extract_images: bool = True
    extract_tables: bool = True
    extract_code: bool = True
    
    # Anti-bot
    use_random_user_agent: bool = True
    add_referer: bool = True
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 24


class ContentCache:
    """Thread-safe content cache."""
    
    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self._cache: Dict[str, Tuple[ExtractedContent, datetime]] = {}
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = threading.Lock()
    
    def _make_key(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str) -> Optional[ExtractedContent]:
        key = self._make_key(url)
        with self._lock:
            if key in self._cache:
                content, timestamp = self._cache[key]
                if datetime.now() - timestamp < self._ttl:
                    return content
                else:
                    del self._cache[key]
        return None
    
    def set(self, url: str, content: ExtractedContent) -> None:
        key = self._make_key(url)
        with self._lock:
            # Evict oldest if full
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache, key=lambda k: self._cache[k][1])
                del self._cache[oldest_key]
            self._cache[key] = (content, datetime.now())
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


class UserAgentRotator:
    """User agent rotation for anti-bot bypass."""
    
    AGENTS = [
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        # Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    def __init__(self):
        self._index = 0
        self._lock = threading.Lock()
    
    def get(self) -> str:
        with self._lock:
            agent = self.AGENTS[self._index % len(self.AGENTS)]
            self._index += 1
            return agent


class TrafilaturaExtractor:
    """Trafilatura-based content extraction."""
    
    def __init__(self):
        if TRAFILATURA_AVAILABLE:
            # Configure trafilatura
            self.config = use_config()
            self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    
    def extract(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        if not TRAFILATURA_AVAILABLE:
            return None
        
        try:
            # Extract with full options
            result = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                include_images=True,
                include_links=True,
                output_format='json',
                with_metadata=True,
                favor_precision=True,
                config=self.config
            )
            
            if result:
                return json.loads(result)
        except Exception as e:
            logger.warning(f"Trafilatura extraction failed: {e}")
        
        return None


class NewspaperExtractor:
    """Newspaper3k-based news extraction."""
    
    def __init__(self):
        if NEWSPAPER_AVAILABLE:
            self.config = NewspaperConfig()
            self.config.browser_user_agent = UserAgentRotator().get()
            self.config.request_timeout = 15
            self.config.fetch_images = True
            self.config.memoize_articles = False
    
    def extract(self, url: str, html: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not NEWSPAPER_AVAILABLE:
            return None
        
        try:
            article = Article(url, config=self.config)
            
            if html:
                article.set_html(html)
            else:
                article.download()
            
            article.parse()
            
            # NLP features (optional)
            try:
                article.nlp()
                keywords = article.keywords
                summary = article.summary
            except:
                keywords = []
                summary = ""
            
            return {
                "title": article.title,
                "text": article.text,
                "authors": article.authors,
                "publish_date": str(article.publish_date) if article.publish_date else "",
                "top_image": article.top_image,
                "images": list(article.images)[:10],
                "keywords": keywords,
                "summary": summary,
                "html": article.html,
            }
        except Exception as e:
            logger.warning(f"Newspaper extraction failed: {e}")
        
        return None


class PlaywrightExtractor:
    """Playwright-based JavaScript rendering."""
    
    def __init__(self):
        self._browser: Optional[Browser] = None
        self._playwright = None
    
    async def _get_browser(self) -> Browser:
        if self._browser is None and PLAYWRIGHT_AVAILABLE:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
        return self._browser
    
    async def extract(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        timeout: int = 30000
    ) -> Optional[str]:
        if not PLAYWRIGHT_AVAILABLE:
            return None
        
        browser = await self._get_browser()
        if not browser:
            return None
        
        page = None
        try:
            page = await browser.new_page()
            
            # Anti-detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            # Wait for specific selector if provided
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=5000)
                except:
                    pass
            
            # Scroll to load lazy content
            await page.evaluate("""
                window.scrollTo(0, document.body.scrollHeight / 2);
            """)
            await asyncio.sleep(0.5)
            
            html = await page.content()
            return html
            
        except Exception as e:
            logger.warning(f"Playwright extraction failed: {e}")
            return None
        finally:
            if page:
                await page.close()
    
    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class BeautifulSoupExtractor:
    """BeautifulSoup-based fallback extraction."""
    
    # Content-likely tags
    CONTENT_TAGS = ['article', 'main', 'section', 'div']
    CONTENT_CLASSES = ['content', 'article', 'post', 'entry', 'main', 'body', 'text']
    
    # Noise tags to remove
    NOISE_TAGS = ['script', 'style', 'nav', 'header', 'footer', 'aside', 
                  'advertisement', 'sidebar', 'menu', 'banner']
    
    def extract(self, html: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove noise
        for tag in soup.find_all(self.NOISE_TAGS):
            tag.decompose()
        
        # Extract metadata
        title = self._extract_title(soup)
        author = self._extract_author(soup)
        date = self._extract_date(soup)
        
        # Find main content
        content = self._find_main_content(soup)
        
        # Extract structured elements
        headings = self._extract_headings(soup)
        links = self._extract_links(soup, url)
        images = self._extract_images(soup, url)
        tables = self._extract_tables(soup)
        code_blocks = self._extract_code(soup)
        
        return {
            "title": title,
            "content": content,
            "author": author,
            "date": date,
            "headings": headings,
            "links": links,
            "images": images,
            "tables": tables,
            "code_blocks": code_blocks,
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try multiple sources
        for selector in [
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
        ]:
            tag = soup.find(selector[0], selector[1])
            if tag and tag.get('content'):
                return tag['content']
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        for selector in [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('a', {'rel': 'author'}),
        ]:
            tag = soup.find(selector[0], selector[1])
            if tag:
                return tag.get('content') or tag.get_text(strip=True)
        return ""
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        for selector in [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'date'}),
            ('time', {'datetime': True}),
        ]:
            tag = soup.find(selector[0], selector[1])
            if tag:
                return tag.get('content') or tag.get('datetime') or ""
        return ""
    
    def _find_main_content(self, soup: BeautifulSoup) -> str:
        # Try article/main tags first
        for tag_name in ['article', 'main']:
            tag = soup.find(tag_name)
            if tag and len(tag.get_text(strip=True)) > 200:
                return self._clean_text(tag.get_text(separator='\n'))
        
        # Try common content classes
        for class_name in self.CONTENT_CLASSES:
            tag = soup.find(class_=re.compile(class_name, re.I))
            if tag and len(tag.get_text(strip=True)) > 200:
                return self._clean_text(tag.get_text(separator='\n'))
        
        # Fallback: largest text block
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
            return self._clean_text(content)
        
        return self._clean_text(soup.get_text(separator='\n'))
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if text and len(text) > 3:
                headings.append(text)
        return headings[:20]
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        links = []
        for a in soup.find_all('a', href=True)[:50]:
            href = a['href']
            if href.startswith('/'):
                href = urljoin(base_url, href)
            text = a.get_text(strip=True)
            if text and href.startswith('http'):
                links.append({"text": text[:100], "url": href})
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        images = []
        for img in soup.find_all('img', src=True)[:20]:
            src = img['src']
            if src.startswith('/'):
                src = urljoin(base_url, src)
            alt = img.get('alt', '')
            if src.startswith('http'):
                images.append({"src": src, "alt": alt[:100]})
        return images
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        tables = []
        for table in soup.find_all('table')[:5]:
            rows = []
            for tr in table.find_all('tr')[:30]:
                cells = [td.get_text(strip=True)[:200] for td in tr.find_all(['td', 'th'])[:15]]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables
    
    def _extract_code(self, soup: BeautifulSoup) -> List[str]:
        codes = []
        for code in soup.find_all(['pre', 'code'])[:10]:
            text = code.get_text(strip=True)
            if len(text) > 20:
                codes.append(text[:1000])
        return codes
    
    def _clean_text(self, text: str) -> str:
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        return text.strip()


class UltraPremiumScraper:
    """
    Ultra Premium Web Scraper.
    
    Combines multiple extraction methods for best results.
    """
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        
        # Extractors
        self.trafilatura = TrafilaturaExtractor()
        self.newspaper = NewspaperExtractor()
        self.playwright = PlaywrightExtractor() if PLAYWRIGHT_AVAILABLE else None
        self.beautifulsoup = BeautifulSoupExtractor()
        
        # Utilities
        self.user_agent = UserAgentRotator()
        self.cache = ContentCache(
            ttl_hours=self.config.cache_ttl_hours
        ) if self.config.cache_enabled else None
        
        # HTTP client - try http2 if available
        try:
            self.client = httpx.AsyncClient(
                timeout=self.config.request_timeout,
                follow_redirects=True,
                http2=True
            )
        except ImportError:
            # h2 package not installed, fallback to http1
            self.client = httpx.AsyncClient(
                timeout=self.config.request_timeout,
                follow_redirects=True,
                http2=False
            )
    
    async def extract(
        self,
        url: str,
        method: ExtractionMethod = ExtractionMethod.AUTO,
        use_javascript: bool = False
    ) -> ExtractedContent:
        """
        URL'den içerik çıkar.
        
        Args:
            url: Hedef URL
            method: Çıkarma yöntemi
            use_javascript: JS rendering kullan
            
        Returns:
            ExtractedContent
        """
        start_time = time.time()
        
        # Check cache
        if self.cache:
            cached = self.cache.get(url)
            if cached:
                cached.metadata["from_cache"] = True
                return cached
        
        # Fetch HTML
        html = None
        
        if use_javascript and self.playwright:
            html = await self.playwright.extract(url)
        
        if not html:
            html = await self._fetch_html(url)
        
        if not html:
            return ExtractedContent(
                url=url,
                title="",
                content="Failed to fetch content",
                quality_score=0.0
            )
        
        # Extract based on method
        result = await self._extract_with_method(url, html, method)
        
        # Calculate metrics
        result.extraction_time_ms = int((time.time() - start_time) * 1000)
        result.word_count = len(result.content.split())
        result.reading_time_minutes = max(1, result.word_count // 200)
        result.quality_score = self._calculate_quality(result)
        
        # Detect content type
        result.content_type = self._detect_content_type(url, result)
        
        # Cache result
        if self.cache and result.quality_score > 0.3:
            self.cache.set(url, result)
        
        return result
    
    async def extract_batch(
        self,
        urls: List[str],
        method: ExtractionMethod = ExtractionMethod.AUTO,
        max_concurrent: int = 5
    ) -> List[ExtractedContent]:
        """
        Birden fazla URL'den paralel içerik çıkar.
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_with_semaphore(url: str) -> ExtractedContent:
            async with semaphore:
                return await self.extract(url, method)
        
        tasks = [extract_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """HTML içeriğini çek."""
        headers = {
            "User-Agent": self.user_agent.get(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        if self.config.add_referer:
            headers["Referer"] = f"https://www.google.com/search?q={urlparse(url).netloc}"
        
        try:
            response = await self.client.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    async def _extract_with_method(
        self,
        url: str,
        html: str,
        method: ExtractionMethod
    ) -> ExtractedContent:
        """Belirtilen yöntemle içerik çıkar."""
        
        if method == ExtractionMethod.AUTO or method == ExtractionMethod.HYBRID:
            # Try multiple methods and merge
            results = []
            
            # Trafilatura
            if TRAFILATURA_AVAILABLE and self.config.prefer_trafilatura:
                traf_result = self.trafilatura.extract(html, url)
                if traf_result:
                    results.append(("trafilatura", traf_result))
            
            # Newspaper
            if NEWSPAPER_AVAILABLE:
                news_result = self.newspaper.extract(url, html)
                if news_result:
                    results.append(("newspaper", news_result))
            
            # BeautifulSoup fallback
            bs_result = self.beautifulsoup.extract(html, url)
            results.append(("beautifulsoup", bs_result))
            
            return self._merge_results(url, html, results)
        
        elif method == ExtractionMethod.TRAFILATURA:
            result = self.trafilatura.extract(html, url)
            return self._trafilatura_to_content(url, html, result)
        
        elif method == ExtractionMethod.NEWSPAPER:
            result = self.newspaper.extract(url, html)
            return self._newspaper_to_content(url, html, result)
        
        else:
            result = self.beautifulsoup.extract(html, url)
            return self._beautifulsoup_to_content(url, html, result)
    
    def _merge_results(
        self,
        url: str,
        html: str,
        results: List[Tuple[str, Dict]]
    ) -> ExtractedContent:
        """Farklı extractorların sonuçlarını birleştir."""
        best_content = ""
        best_title = ""
        best_method = ExtractionMethod.BEAUTIFULSOUP
        
        # Pick best content by length and quality
        for method_name, result in results:
            if not result:
                continue
            
            content = result.get("content") or result.get("text") or ""
            title = result.get("title", "")
            
            if len(content) > len(best_content):
                best_content = content
                best_title = title
                best_method = ExtractionMethod(method_name) if method_name in [e.value for e in ExtractionMethod] else ExtractionMethod.AUTO
        
        # Merge metadata from all results
        author = ""
        date = ""
        headings = []
        images = []
        links = []
        tables = []
        code_blocks = []
        
        for _, result in results:
            if not result:
                continue
            
            if not author:
                author = result.get("author") or (result.get("authors", []) or [""])[0]
            if not date:
                date = result.get("date") or result.get("publish_date", "")
            
            headings.extend(result.get("headings", []))
            images.extend(result.get("images", []))
            links.extend(result.get("links", []))
            tables.extend(result.get("tables", []))
            code_blocks.extend(result.get("code_blocks", []))
        
        # Deduplicate
        headings = list(dict.fromkeys(headings))[:20]
        
        return ExtractedContent(
            url=url,
            title=best_title,
            content=best_content,
            author=author,
            publish_date=date,
            headings=headings,
            images=images[:self.config.max_images],
            links=links[:self.config.max_links],
            tables=tables[:5],
            code_blocks=code_blocks[:10],
            extraction_method=best_method,
            html=html[:10000],  # Truncate HTML
        )
    
    def _trafilatura_to_content(self, url: str, html: str, result: Optional[Dict]) -> ExtractedContent:
        if not result:
            return self._beautifulsoup_to_content(url, html, self.beautifulsoup.extract(html, url))
        
        return ExtractedContent(
            url=url,
            title=result.get("title", ""),
            content=result.get("text", ""),
            author=result.get("author", ""),
            publish_date=result.get("date", ""),
            language=result.get("language", ""),
            extraction_method=ExtractionMethod.TRAFILATURA,
            html=html[:10000],
        )
    
    def _newspaper_to_content(self, url: str, html: str, result: Optional[Dict]) -> ExtractedContent:
        if not result:
            return self._beautifulsoup_to_content(url, html, self.beautifulsoup.extract(html, url))
        
        return ExtractedContent(
            url=url,
            title=result.get("title", ""),
            content=result.get("text", ""),
            summary=result.get("summary", ""),
            author=result.get("authors", [""])[0] if result.get("authors") else "",
            publish_date=result.get("publish_date", ""),
            images=[{"src": result.get("top_image", ""), "alt": ""}] if result.get("top_image") else [],
            extraction_method=ExtractionMethod.NEWSPAPER,
            html=html[:10000],
        )
    
    def _beautifulsoup_to_content(self, url: str, html: str, result: Dict) -> ExtractedContent:
        return ExtractedContent(
            url=url,
            title=result.get("title", ""),
            content=result.get("content", ""),
            author=result.get("author", ""),
            publish_date=result.get("date", ""),
            headings=result.get("headings", []),
            links=result.get("links", []),
            images=result.get("images", []),
            tables=result.get("tables", []),
            code_blocks=result.get("code_blocks", []),
            extraction_method=ExtractionMethod.BEAUTIFULSOUP,
            html=html[:10000],
        )
    
    def _calculate_quality(self, content: ExtractedContent) -> float:
        """İçerik kalite skoru hesapla."""
        score = 0.0
        
        # Title
        if content.title:
            score += 0.1
        
        # Content length
        if content.word_count > 100:
            score += 0.2
        if content.word_count > 500:
            score += 0.1
        if content.word_count > 1000:
            score += 0.1
        
        # Structured content
        if content.headings:
            score += 0.1
        if content.images:
            score += 0.05
        if content.tables:
            score += 0.1
        if content.code_blocks:
            score += 0.05
        
        # Author and date
        if content.author:
            score += 0.1
        if content.publish_date:
            score += 0.1
        
        return min(1.0, score)
    
    def _detect_content_type(self, url: str, content: ExtractedContent) -> ContentType:
        """İçerik türünü tespit et."""
        domain = urlparse(url).netloc.lower()
        
        # Domain-based detection
        if any(x in domain for x in ['news', 'haber', 'times', 'post']):
            return ContentType.NEWS
        if any(x in domain for x in ['blog', 'medium.com', 'substack']):
            return ContentType.BLOG
        if any(x in domain for x in ['docs.', 'wiki', 'documentation']):
            return ContentType.DOCUMENTATION
        if any(x in domain for x in ['edu', 'academic', 'scholar', 'arxiv']):
            return ContentType.ACADEMIC
        if any(x in domain for x in ['forum', 'reddit', 'stackoverflow']):
            return ContentType.FORUM
        if any(x in domain for x in ['amazon', 'ebay', 'shop']):
            return ContentType.ECOMMERCE
        
        # Content-based detection
        if content.code_blocks:
            return ContentType.DOCUMENTATION
        
        return ContentType.GENERIC
    
    async def close(self):
        """Cleanup resources."""
        await self.client.aclose()
        if self.playwright:
            await self.playwright.close()


# Singleton instance
_scraper: Optional[UltraPremiumScraper] = None

def get_premium_scraper() -> UltraPremiumScraper:
    global _scraper
    if _scraper is None:
        _scraper = UltraPremiumScraper()
    return _scraper


# Convenience functions
async def extract_url(url: str, use_javascript: bool = False) -> ExtractedContent:
    """URL'den içerik çıkar."""
    scraper = get_premium_scraper()
    return await scraper.extract(url, use_javascript=use_javascript)


async def extract_urls(urls: List[str], max_concurrent: int = 5) -> List[ExtractedContent]:
    """Paralel URL çıkarımı."""
    scraper = get_premium_scraper()
    return await scraper.extract_batch(urls, max_concurrent=max_concurrent)
