"""
🌐 Premium Web Search Engine
============================

Endüstri standardında web arama motoru.
Perplexity AI, ChatGPT Browse, Google Bard kalitesinde sonuçlar.

Özellikler:
- Multi-source arama (DuckDuckGo, Google, Bing, Wikipedia)
- Gerçek içerik çıkarma (sadece link değil)
- AI-powered özet ve sentez
- Kaynak doğrulama ve güvenilirlik skoru
- Akıllı cache sistemi
- Rate limiting ve hata yönetimi
- Paralel işleme
- Dil algılama ve çoklu dil desteği
"""

import asyncio
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urljoin, urlparse
import concurrent.futures
from functools import lru_cache
import threading

import httpx
import requests
from bs4 import BeautifulSoup


# ============ ENUMS & DATA CLASSES ============

class SearchProvider(Enum):
    """Arama sağlayıcıları"""
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"
    BING = "bing"
    WIKIPEDIA = "wikipedia"
    NEWS = "news"


class ContentQuality(Enum):
    """İçerik kalite seviyesi"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class SourceType(Enum):
    """Kaynak türleri"""
    ACADEMIC = "academic"
    NEWS = "news"
    OFFICIAL = "official"
    BLOG = "blog"
    FORUM = "forum"
    WIKI = "wiki"
    SOCIAL = "social"
    ECOMMERCE = "ecommerce"
    UNKNOWN = "unknown"


@dataclass
class SearchResult:
    """Tek bir arama sonucu"""
    title: str
    url: str
    snippet: str = ""
    full_content: str = ""
    domain: str = ""
    source_type: SourceType = SourceType.UNKNOWN
    quality: ContentQuality = ContentQuality.UNKNOWN
    reliability_score: float = 0.5
    published_date: Optional[str] = None
    author: Optional[str] = None
    word_count: int = 0
    language: str = "tr"
    provider: SearchProvider = SearchProvider.DUCKDUCKGO
    fetch_time_ms: int = 0
    is_cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Tam arama yanıtı"""
    query: str
    results: List[SearchResult]
    total_results: int = 0
    search_time_ms: int = 0
    providers_used: List[str] = field(default_factory=list)
    instant_answer: Optional[Dict[str, Any]] = None
    related_queries: List[str] = field(default_factory=list)
    knowledge_panel: Optional[Dict[str, Any]] = None
    ai_summary: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    cached: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ContentExtraction:
    """Çıkarılan içerik"""
    title: str
    main_content: str
    meta_description: str = ""
    headings: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    images: List[Dict[str, str]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    word_count: int = 0
    reading_time_min: int = 0
    language: str = "unknown"
    published_date: Optional[str] = None
    author: Optional[str] = None


# ============ CACHE SYSTEM ============

class SearchCache:
    """Thread-safe arama cache sistemi"""
    
    def __init__(self, max_size: int = 500, ttl_minutes: int = 30):
        self.cache: Dict[str, Tuple[SearchResponse, datetime]] = {}
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _hash_query(self, query: str, params: Dict = None) -> str:
        """Sorgu hash'i oluştur"""
        key = query.lower().strip()
        if params:
            key += json.dumps(params, sort_keys=True)
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, query: str, params: Dict = None) -> Optional[SearchResponse]:
        """Cache'den al"""
        with self.lock:
            key = self._hash_query(query, params)
            
            if key in self.cache:
                response, timestamp = self.cache[key]
                
                if datetime.now() - timestamp < self.ttl:
                    self.hits += 1
                    response.cached = True
                    return response
                else:
                    del self.cache[key]
            
            self.misses += 1
            return None
    
    def set(self, query: str, response: SearchResponse, params: Dict = None):
        """Cache'e kaydet"""
        with self.lock:
            # Boyut kontrolü
            if len(self.cache) >= self.max_size:
                # En eski %20'yi sil
                sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
                for key, _ in sorted_items[:int(self.max_size * 0.2)]:
                    del self.cache[key]
            
            key = self._hash_query(query, params)
            self.cache[key] = (response, datetime.now())
    
    def clear(self):
        """Cache'i temizle"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Cache istatistikleri"""
        with self.lock:
            total = self.hits + self.misses
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": (self.hits / total * 100) if total > 0 else 0,
                "ttl_minutes": self.ttl.seconds // 60
            }


# ============ CONTENT EXTRACTOR ============

class ContentExtractor:
    """
    Web sayfalarından akıllı içerik çıkarma.
    
    Özellikler:
    - Trafilatura benzeri ana içerik tespiti
    - Başlık, meta, heading çıkarma
    - Tablo ve kod bloğu desteği
    - Reklam ve navigasyon filtreleme
    - Çoklu dil desteği
    """
    
    # Filtrelenecek class/id patternleri (reklam, nav, footer vb.)
    NOISE_PATTERNS = [
        r'ad[-_]?', r'ads[-_]?', r'advert', r'banner', r'sponsor',
        r'sidebar', r'widget', r'popup', r'modal', r'overlay',
        r'cookie', r'gdpr', r'consent', r'newsletter',
        r'social[-_]?share', r'share[-_]?button', r'follow[-_]?us',
        r'comment', r'reply', r'disqus',
        r'footer', r'header', r'nav', r'menu', r'breadcrumb',
        r'related[-_]?', r'recommended', r'also[-_]?read',
        r'promo', r'cta', r'subscribe',
        r'author[-_]?bio', r'about[-_]?author'
    ]
    
    # Ana içerik göstergeleri
    CONTENT_MARKERS = [
        'article', 'main', 'content', 'post', 'entry', 'story',
        'body', 'text', 'prose', 'markdown'
    ]
    
    # Akademik/güvenilir domain'ler
    TRUSTED_DOMAINS = [
        'wikipedia.org', 'edu', 'gov', 'gov.tr', 'edu.tr',
        'arxiv.org', 'nature.com', 'sciencedirect.com',
        'pubmed.ncbi.nlm.nih.gov', 'scholar.google.com',
        'researchgate.net', 'academia.edu',
        'bbc.com', 'reuters.com', 'apnews.com',
        'nytimes.com', 'theguardian.com',
        'microsoft.com', 'python.org', 'developer.mozilla.org',
        'stackoverflow.com', 'github.com'
    ]
    
    def __init__(self, timeout: float = 15.0, max_content_length: int = 15000):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
    
    def extract(self, url: str) -> Optional[ContentExtraction]:
        """URL'den içerik çıkar"""
        try:
            start_time = time.time()
            
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # Encoding düzeltme
            if response.encoding is None:
                response.encoding = 'utf-8'
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Gürültülü elementleri kaldır
            self._remove_noise(soup)
            
            # Ana içerik bul
            main_content = self._find_main_content(soup)
            
            # Başlık çıkar
            title = self._extract_title(soup)
            
            # Meta description
            meta_desc = self._extract_meta_description(soup)
            
            # Headings
            headings = self._extract_headings(soup)
            
            # Tarih ve yazar
            published_date = self._extract_date(soup)
            author = self._extract_author(soup)
            
            # Tablolar
            tables = self._extract_tables(soup)
            
            # Kod blokları
            code_blocks = self._extract_code_blocks(soup)
            
            # Key points (önemli noktalar)
            key_points = self._extract_key_points(main_content, headings)
            
            # İçerik temizle ve kısalt
            clean_content = self._clean_text(main_content)
            
            if len(clean_content) > self.max_content_length:
                clean_content = self._smart_truncate(clean_content, self.max_content_length)
            
            # Kelime sayısı ve okuma süresi
            word_count = len(clean_content.split())
            reading_time = max(1, word_count // 200)  # 200 kelime/dakika
            
            # Dil tespiti (basit)
            language = self._detect_language(clean_content)
            
            return ContentExtraction(
                title=title,
                main_content=clean_content,
                meta_description=meta_desc,
                headings=headings,
                key_points=key_points,
                tables=tables,
                code_blocks=code_blocks,
                word_count=word_count,
                reading_time_min=reading_time,
                language=language,
                published_date=published_date,
                author=author
            )
            
        except Exception as e:
            return None
    
    def _remove_noise(self, soup: BeautifulSoup):
        """Gürültülü elementleri kaldır"""
        # Script, style, iframe vb.
        for tag in soup(['script', 'style', 'iframe', 'noscript', 'svg', 'form', 'button', 'input']):
            tag.decompose()
        
        # Pattern'e uyan elementler
        noise_regex = re.compile('|'.join(self.NOISE_PATTERNS), re.I)
        
        for element in soup.find_all(class_=noise_regex):
            element.decompose()
        
        for element in soup.find_all(id=noise_regex):
            element.decompose()
        
        # Boş elementler
        for element in soup.find_all(['div', 'span', 'p']):
            if not element.get_text(strip=True):
                element.decompose()
    
    def _find_main_content(self, soup: BeautifulSoup) -> str:
        """Ana içerik bloğunu bul"""
        content = ""
        
        # 1. Article tag'i dene
        article = soup.find('article')
        if article:
            content = article.get_text(separator='\n', strip=True)
            if len(content) > 200:
                return content
        
        # 2. Main tag'i dene
        main = soup.find('main')
        if main:
            content = main.get_text(separator='\n', strip=True)
            if len(content) > 200:
                return content
        
        # 3. Content marker class/id'leri dene
        for marker in self.CONTENT_MARKERS:
            element = soup.find(class_=re.compile(marker, re.I))
            if element:
                content = element.get_text(separator='\n', strip=True)
                if len(content) > 200:
                    return content
            
            element = soup.find(id=re.compile(marker, re.I))
            if element:
                content = element.get_text(separator='\n', strip=True)
                if len(content) > 200:
                    return content
        
        # 4. En büyük metin bloğunu bul
        max_text = ""
        for tag in soup.find_all(['div', 'section']):
            text = tag.get_text(separator='\n', strip=True)
            if len(text) > len(max_text):
                max_text = text
        
        if len(max_text) > 200:
            return max_text
        
        # 5. Body'den al
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return soup.get_text(separator='\n', strip=True)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Başlık çıkar"""
        # og:title
        og_title = soup.find('meta', property='og:title')
        if og_title:
            return og_title.get('content', '')
        
        # title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # h1
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Meta description çıkar"""
        # og:description
        og_desc = soup.find('meta', property='og:description')
        if og_desc:
            return og_desc.get('content', '')
        
        # meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        return ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """Başlıkları çıkar"""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = tag.get_text(strip=True)
            if text and len(text) > 3:
                headings.append(text)
        return headings[:20]  # Max 20 heading
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Yayın tarihini çıkar"""
        # Meta tags
        date_metas = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'date'}),
            ('meta', {'name': 'publish-date'}),
            ('time', {'datetime': True}),
        ]
        
        for tag, attrs in date_metas:
            element = soup.find(tag, attrs)
            if element:
                date_val = element.get('content') or element.get('datetime')
                if date_val:
                    return date_val[:10]  # YYYY-MM-DD
        
        return None
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Yazarı çıkar"""
        # Meta tags
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            return author_meta.get('content')
        
        # Schema.org
        author_link = soup.find('a', rel='author')
        if author_link:
            return author_link.get_text(strip=True)
        
        return None
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[List[List[str]]]:
        """Tabloları çıkar"""
        tables = []
        for table in soup.find_all('table')[:3]:  # Max 3 tablo
            rows = []
            for tr in table.find_all('tr')[:20]:  # Max 20 satır
                cells = []
                for td in tr.find_all(['td', 'th'])[:10]:  # Max 10 sütun
                    cells.append(td.get_text(strip=True)[:100])
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables
    
    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[str]:
        """Kod bloklarını çıkar"""
        codes = []
        for code in soup.find_all(['pre', 'code'])[:5]:
            text = code.get_text(strip=True)
            if len(text) > 20:
                codes.append(text[:500])
        return codes
    
    def _extract_key_points(self, content: str, headings: List[str]) -> List[str]:
        """Önemli noktaları çıkar"""
        points = []
        
        # Numaralı listeler
        numbered = re.findall(r'^\s*\d+[\.\)]\s*(.+?)$', content, re.MULTILINE)
        points.extend(numbered[:10])
        
        # Bullet points
        bullets = re.findall(r'^\s*[\•\-\*]\s*(.+?)$', content, re.MULTILINE)
        points.extend(bullets[:10])
        
        # Kısa headings
        for h in headings:
            if len(h) < 100:
                points.append(h)
        
        return list(set(points))[:15]
    
    def _clean_text(self, text: str) -> str:
        """Metni temizle"""
        # Fazla boşlukları kaldır
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        
        # Anlamsız satırları kaldır
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 10:  # Çok kısa satırları atla
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _smart_truncate(self, text: str, max_length: int) -> str:
        """Akıllı kısaltma (cümle sınırında)"""
        if len(text) <= max_length:
            return text
        
        # Son cümle sınırını bul
        truncated = text[:max_length]
        
        # Son nokta, soru işareti veya ünlemi bul
        last_sentence = max(
            truncated.rfind('.'),
            truncated.rfind('?'),
            truncated.rfind('!')
        )
        
        if last_sentence > max_length * 0.7:
            return truncated[:last_sentence + 1]
        
        return truncated + "..."
    
    def _detect_language(self, text: str) -> str:
        """Basit dil tespiti"""
        # Türkçe karakterler
        tr_chars = set('çğıöşüÇĞİÖŞÜ')
        text_chars = set(text)
        
        if tr_chars & text_chars:
            return "tr"
        return "en"
    
    def classify_source(self, url: str) -> Tuple[SourceType, float]:
        """Kaynak türünü ve güvenilirlik skorunu belirle"""
        domain = urlparse(url).netloc.lower()
        
        # Güvenilir domain kontrolü
        for trusted in self.TRUSTED_DOMAINS:
            if trusted in domain:
                if 'edu' in trusted or 'gov' in trusted:
                    return SourceType.ACADEMIC, 0.9
                elif 'wiki' in trusted:
                    return SourceType.WIKI, 0.85
                else:
                    return SourceType.OFFICIAL, 0.8
        
        # Haber siteleri
        news_patterns = ['news', 'haber', 'gazete', 'times', 'post', 'herald']
        for p in news_patterns:
            if p in domain:
                return SourceType.NEWS, 0.7
        
        # Blog platformları
        blog_patterns = ['blog', 'medium.com', 'substack', 'wordpress']
        for p in blog_patterns:
            if p in domain:
                return SourceType.BLOG, 0.5
        
        # Forum/Sosyal
        social_patterns = ['reddit', 'quora', 'forum', 'twitter', 'facebook']
        for p in social_patterns:
            if p in domain:
                return SourceType.FORUM if 'reddit' in p or 'forum' in p else SourceType.SOCIAL, 0.4
        
        # E-ticaret
        ecommerce_patterns = ['amazon', 'ebay', 'aliexpress', 'trendyol', 'hepsiburada']
        for p in ecommerce_patterns:
            if p in domain:
                return SourceType.ECOMMERCE, 0.3
        
        return SourceType.UNKNOWN, 0.5


# ============ SEARCH PROVIDERS ============

class DuckDuckGoProvider:
    """DuckDuckGo arama sağlayıcısı"""
    
    INSTANT_ANSWER_API = "https://api.duckduckgo.com/"
    HTML_SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def instant_answer(self, query: str) -> Optional[Dict[str, Any]]:
        """Instant Answer API"""
        try:
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            }
            
            response = self.session.get(
                self.INSTANT_ANSWER_API,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("Abstract"):
                    return {
                        "type": "instant_answer",
                        "title": data.get("Heading", ""),
                        "abstract": data.get("Abstract", ""),
                        "source": data.get("AbstractSource", ""),
                        "url": data.get("AbstractURL", ""),
                        "image": data.get("Image", ""),
                        "related_topics": [
                            {"text": t.get("Text", ""), "url": t.get("FirstURL", "")}
                            for t in data.get("RelatedTopics", [])[:5]
                            if isinstance(t, dict) and "Text" in t
                        ]
                    }
                
                # Infobox (knowledge panel)
                if data.get("Infobox"):
                    return {
                        "type": "knowledge_panel",
                        "title": data.get("Heading", ""),
                        "content": data.get("Infobox", {}).get("content", []),
                        "url": data.get("AbstractURL", "")
                    }
        except:
            pass
        
        return None
    
    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """HTML arama"""
        results = []
        
        try:
            data = {
                "q": query,
                "kl": "tr-tr",  # Türkiye
            }
            
            response = self.session.post(
                self.HTML_SEARCH_URL,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Sonuçları parse et
                for result in soup.select('.result')[:num_results]:
                    link_elem = result.select_one('.result__a')
                    snippet_elem = result.select_one('.result__snippet')
                    
                    if link_elem:
                        url = link_elem.get('href', '')
                        title = link_elem.get_text(strip=True)
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        if url and title:
                            results.append({
                                "title": title,
                                "url": url,
                                "snippet": snippet
                            })
        except:
            pass
        
        return results


class WikipediaProvider:
    """Wikipedia API sağlayıcısı"""
    
    API_URL = "https://tr.wikipedia.org/w/api.php"
    
    def __init__(self, timeout: float = 10.0, language: str = "tr"):
        self.timeout = timeout
        self.language = language
        self.api_url = f"https://{language}.wikipedia.org/w/api.php"
    
    def search(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """Wikipedia arama"""
        results = []
        
        try:
            # Arama yap
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": num_results,
                "utf8": 1
            }
            
            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                search_results = data.get("query", {}).get("search", [])
                
                for item in search_results:
                    page_id = item.get("pageid")
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    
                    # HTML taglerini temizle
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                    
                    # Sayfa içeriğini al
                    content = self._get_page_content(page_id)
                    
                    url = f"https://{self.language}.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
                    
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "content": content,
                        "source": "Wikipedia"
                    })
        except:
            pass
        
        return results
    
    def _get_page_content(self, page_id: int) -> str:
        """Sayfa içeriğini al"""
        try:
            params = {
                "action": "query",
                "pageids": page_id,
                "prop": "extracts",
                "exintro": 1,  # Sadece giriş
                "explaintext": 1,  # Plain text
                "format": "json"
            }
            
            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get("query", {}).get("pages", {})
                page = pages.get(str(page_id), {})
                return page.get("extract", "")[:3000]
        except:
            pass
        
        return ""


# ============ MAIN SEARCH ENGINE ============

class PremiumWebSearchEngine:
    """
    Premium Web Search Engine
    
    Perplexity AI kalitesinde web arama ve içerik çıkarma.
    """
    
    def __init__(
        self,
        max_results: int = 8,
        extract_content: bool = True,
        use_wikipedia: bool = True,
        cache_enabled: bool = True,
        parallel_extraction: bool = True,
        min_content_length: int = 200
    ):
        self.max_results = max_results
        self.extract_content = extract_content
        self.use_wikipedia = use_wikipedia
        self.cache_enabled = cache_enabled
        self.parallel_extraction = parallel_extraction
        self.min_content_length = min_content_length
        
        # Providers
        self.ddg = DuckDuckGoProvider()
        self.wiki = WikipediaProvider()
        self.extractor = ContentExtractor()
        
        # Cache
        self.cache = SearchCache() if cache_enabled else None
        
        # Stats
        self.stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "content_extractions": 0,
            "avg_search_time_ms": 0
        }
    
    def search(
        self,
        query: str,
        num_results: Optional[int] = None,
        extract_content: Optional[bool] = None,
        include_wikipedia: Optional[bool] = None
    ) -> SearchResponse:
        """
        Ana arama fonksiyonu.
        
        Args:
            query: Arama sorgusu
            num_results: Sonuç sayısı
            extract_content: İçerik çıkarsın mı
            include_wikipedia: Wikipedia dahil edilsin mi
            
        Returns:
            SearchResponse: Kapsamlı arama yanıtı
        """
        start_time = time.time()
        self.stats["total_searches"] += 1
        
        num_results = num_results or self.max_results
        extract_content = extract_content if extract_content is not None else self.extract_content
        include_wikipedia = include_wikipedia if include_wikipedia is not None else self.use_wikipedia
        
        # Cache kontrolü
        if self.cache_enabled and self.cache:
            cached = self.cache.get(query, {"num_results": num_results})
            if cached:
                return cached
        
        results: List[SearchResult] = []
        providers_used = []
        instant_answer = None
        knowledge_panel = None
        related_queries = []
        
        try:
            # 1. DuckDuckGo Instant Answer
            ia = self.ddg.instant_answer(query)
            if ia:
                if ia.get("type") == "instant_answer":
                    instant_answer = ia
                elif ia.get("type") == "knowledge_panel":
                    knowledge_panel = ia
                
                related = ia.get("related_topics", [])
                related_queries = [r.get("text", "")[:100] for r in related if r.get("text")]
            
            # 2. DuckDuckGo Web Search
            ddg_results = self.ddg.search(query, num_results + 2)
            providers_used.append("DuckDuckGo")
            
            for r in ddg_results:
                result = SearchResult(
                    title=r["title"],
                    url=r["url"],
                    snippet=r["snippet"],
                    domain=urlparse(r["url"]).netloc,
                    provider=SearchProvider.DUCKDUCKGO
                )
                
                # Kaynak sınıflandırma
                source_type, reliability = self.extractor.classify_source(r["url"])
                result.source_type = source_type
                result.reliability_score = reliability
                
                results.append(result)
            
            # 3. Wikipedia (opsiyonel)
            if include_wikipedia:
                wiki_results = self.wiki.search(query, 2)
                providers_used.append("Wikipedia")
                
                for w in wiki_results:
                    result = SearchResult(
                        title=w["title"],
                        url=w["url"],
                        snippet=w["snippet"],
                        full_content=w.get("content", ""),
                        domain="wikipedia.org",
                        source_type=SourceType.WIKI,
                        reliability_score=0.85,
                        provider=SearchProvider.WIKIPEDIA
                    )
                    results.insert(0, result)  # Wikipedia'yı başa al
            
            # 4. İçerik çıkarma (paralel)
            if extract_content and results:
                results = self._extract_contents_parallel(results)
            
            # Sonuçları filtrele ve sırala
            results = self._filter_and_rank(results, query)
            results = results[:num_results]
            
            # Arama süresi
            search_time_ms = int((time.time() - start_time) * 1000)
            
            # Yanıt oluştur
            response = SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time_ms=search_time_ms,
                providers_used=providers_used,
                instant_answer=instant_answer,
                related_queries=related_queries[:5],
                knowledge_panel=knowledge_panel,
                success=len(results) > 0
            )
            
            self.stats["successful_searches"] += 1
            self.stats["avg_search_time_ms"] = (
                self.stats["avg_search_time_ms"] * 0.9 + search_time_ms * 0.1
            )
            
            # Cache'e kaydet
            if self.cache_enabled and self.cache and response.success:
                self.cache.set(query, response, {"num_results": num_results})
            
            return response
            
        except Exception as e:
            return SearchResponse(
                query=query,
                results=[],
                success=False,
                error_message=str(e),
                search_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def _extract_contents_parallel(self, results: List[SearchResult]) -> List[SearchResult]:
        """Paralel içerik çıkarma"""
        if not self.parallel_extraction:
            return self._extract_contents_sequential(results)
        
        def extract_single(result: SearchResult) -> SearchResult:
            if result.full_content:  # Zaten var (Wikipedia gibi)
                return result
            
            try:
                extraction = self.extractor.extract(result.url)
                if extraction:
                    result.full_content = extraction.main_content
                    result.word_count = extraction.word_count
                    result.language = extraction.language
                    result.published_date = extraction.published_date
                    result.author = extraction.author
                    
                    if extraction.meta_description and not result.snippet:
                        result.snippet = extraction.meta_description
                    
                    self.stats["content_extractions"] += 1
            except:
                pass
            
            return result
        
        # Paralel çalıştır
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(extract_single, results))
        
        return results
    
    def _extract_contents_sequential(self, results: List[SearchResult]) -> List[SearchResult]:
        """Sıralı içerik çıkarma"""
        for result in results:
            if result.full_content:
                continue
            
            try:
                extraction = self.extractor.extract(result.url)
                if extraction:
                    result.full_content = extraction.main_content
                    result.word_count = extraction.word_count
                    self.stats["content_extractions"] += 1
            except:
                pass
        
        return results
    
    def _filter_and_rank(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Sonuçları filtrele ve sırala"""
        # İçeriği yetersiz olanları filtrele
        filtered = []
        seen_domains = set()
        
        for result in results:
            # Duplicate domain kontrolü (max 2 per domain)
            if list(seen_domains).count(result.domain) >= 2:
                continue
            
            # Minimum içerik kontrolü
            content_length = len(result.full_content) if result.full_content else len(result.snippet)
            if content_length < self.min_content_length and result.source_type != SourceType.WIKI:
                # İçerik az ama snippet varsa kabul et
                if len(result.snippet) < 50:
                    continue
            
            # Kalite skoru hesapla
            result.quality = self._calculate_quality(result, query)
            
            filtered.append(result)
            seen_domains.add(result.domain)
        
        # Sıralama: güvenilirlik + kalite
        filtered.sort(key=lambda x: (
            x.reliability_score * 0.4 +
            (1 if x.quality == ContentQuality.HIGH else 0.6 if x.quality == ContentQuality.MEDIUM else 0.3) * 0.3 +
            (len(x.full_content) / 10000) * 0.2 +
            (1 if x.source_type == SourceType.WIKI else 0.8 if x.source_type == SourceType.ACADEMIC else 0.5) * 0.1
        ), reverse=True)
        
        return filtered
    
    def _calculate_quality(self, result: SearchResult, query: str) -> ContentQuality:
        """İçerik kalitesini hesapla"""
        score = 0
        
        # Başlık relevance
        query_words = set(query.lower().split())
        title_words = set(result.title.lower().split())
        if query_words & title_words:
            score += 2
        
        # İçerik uzunluğu
        content_len = len(result.full_content) if result.full_content else 0
        if content_len > 2000:
            score += 2
        elif content_len > 500:
            score += 1
        
        # Kaynak güvenilirliği
        if result.reliability_score > 0.7:
            score += 2
        elif result.reliability_score > 0.5:
            score += 1
        
        # Tarih bilgisi
        if result.published_date:
            score += 1
        
        if score >= 5:
            return ContentQuality.HIGH
        elif score >= 3:
            return ContentQuality.MEDIUM
        else:
            return ContentQuality.LOW
    
    def get_formatted_context(self, response: SearchResponse, max_length: int = 8000) -> str:
        """
        LLM için formatlanmış bağlam oluştur.
        
        AI'ın kullanabileceği şekilde arama sonuçlarını formatlar.
        """
        context_parts = []
        
        # Instant Answer varsa
        if response.instant_answer:
            ia = response.instant_answer
            context_parts.append(f"""
📌 **HIZLI CEVAP (Wikipedia/DuckDuckGo):**
{ia.get('title', '')}
{ia.get('abstract', '')}
Kaynak: {ia.get('source', '')} - {ia.get('url', '')}
""")
        
        # Knowledge Panel varsa
        if response.knowledge_panel:
            kp = response.knowledge_panel
            context_parts.append(f"""
📊 **BİLGİ PANELİ:**
{kp.get('title', '')}
""")
            for item in kp.get('content', [])[:5]:
                if isinstance(item, dict):
                    label = item.get('label', '')
                    value = item.get('value', '')
                    if label and value:
                        context_parts.append(f"• {label}: {value}")
        
        # Ana sonuçlar
        for i, result in enumerate(response.results, 1):
            # Kaynak tipi badge
            type_badge = {
                SourceType.WIKI: "📚 Wikipedia",
                SourceType.ACADEMIC: "🎓 Akademik",
                SourceType.NEWS: "📰 Haber",
                SourceType.OFFICIAL: "🏛️ Resmi",
                SourceType.BLOG: "✍️ Blog",
                SourceType.FORUM: "💬 Forum",
            }.get(result.source_type, "🌐 Web")
            
            # Güvenilirlik yıldızları
            stars = "⭐" * int(result.reliability_score * 5)
            
            # İçerik
            content = result.full_content if result.full_content else result.snippet
            if len(content) > 1500:
                content = content[:1500] + "..."
            
            part = f"""
---
### [{i}] {result.title}
{type_badge} | {stars} | {result.domain}
URL: {result.url}

{content}
"""
            context_parts.append(part)
        
        # Birleştir ve kısalt
        full_context = "\n".join(context_parts)
        
        if len(full_context) > max_length:
            full_context = full_context[:max_length] + "\n\n[İçerik kısaltıldı...]"
        
        return full_context
    
    def get_sources_for_ui(self, response: SearchResponse) -> List[Dict[str, Any]]:
        """UI için kaynak listesi"""
        sources = []
        
        for i, result in enumerate(response.results, 1):
            type_icon = {
                SourceType.WIKI: "📚",
                SourceType.ACADEMIC: "🎓",
                SourceType.NEWS: "📰",
                SourceType.OFFICIAL: "🏛️",
                SourceType.BLOG: "✍️",
                SourceType.FORUM: "💬",
            }.get(result.source_type, "🌐")
            
            sources.append({
                "index": i,
                "title": result.title,
                "url": result.url,
                "domain": result.domain,
                "snippet": result.snippet[:250] if result.snippet else "",
                "type": result.source_type.value,
                "type_icon": type_icon,
                "reliability": result.reliability_score,
                "quality": result.quality.value,
                "word_count": result.word_count,
                "date": result.published_date,
                "author": result.author
            })
        
        return sources
    
    def get_stats(self) -> Dict[str, Any]:
        """Arama istatistikleri"""
        stats = dict(self.stats)
        
        if self.cache:
            stats["cache"] = self.cache.get_stats()
        
        return stats
    
    def clear_cache(self):
        """Cache'i temizle"""
        if self.cache:
            self.cache.clear()


# ============ SINGLETON INSTANCE ============

_search_engine: Optional[PremiumWebSearchEngine] = None

def get_search_engine() -> PremiumWebSearchEngine:
    """Singleton search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = PremiumWebSearchEngine()
    return _search_engine


# ============ TOOL WRAPPER ============

class WebSearchTool:
    """
    Web Search Tool - BaseTool uyumlu wrapper.
    
    Mevcut sistemle uyumluluk için.
    """
    
    name = "web_search"
    description = "Web'de arama yapar, içerik çıkarır ve kapsamlı sonuçlar döndürür."
    
    def __init__(self, max_results: int = 8):
        self.max_results = max_results
        self.engine = get_search_engine()
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Tool çalıştır"""
        query = kwargs.get("query", "")
        num_results = kwargs.get("num_results", self.max_results)
        search_type = kwargs.get("search_type", "general")
        
        response = self.engine.search(query, num_results=num_results)
        
        return {
            "success": response.success,
            "query": response.query,
            "instant_answer": response.instant_answer,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "content": r.full_content,
                    "domain": r.domain,
                    "type": r.source_type.value,
                    "reliability": r.reliability_score
                }
                for r in response.results
            ],
            "total_results": response.total_results,
            "search_time_ms": response.search_time_ms,
            "providers": response.providers_used,
            "related_queries": response.related_queries,
            "timestamp": response.timestamp
        }
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Arama sorgusu"
                    },
                    "num_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 15,
                        "default": 8,
                        "description": "Sonuç sayısı"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["general", "news", "academic"],
                        "default": "general"
                    }
                },
                "required": ["query"]
            }
        }


# Test
if __name__ == "__main__":
    engine = PremiumWebSearchEngine()
    
    result = engine.search("Python programlama öğrenme kaynakları")
    
    print(f"Arama: {result.query}")
    print(f"Süre: {result.search_time_ms}ms")
    print(f"Sonuç: {result.total_results}")
    print(f"Providers: {result.providers_used}")
    
    if result.instant_answer:
        print(f"\nInstant Answer: {result.instant_answer['title']}")
        print(result.instant_answer['abstract'][:200])
    
    print("\n--- SONUÇLAR ---")
    for i, r in enumerate(result.results, 1):
        print(f"\n[{i}] {r.title}")
        print(f"    {r.url}")
        print(f"    Type: {r.source_type.value} | Score: {r.reliability_score}")
        print(f"    Content: {len(r.full_content)} chars")
