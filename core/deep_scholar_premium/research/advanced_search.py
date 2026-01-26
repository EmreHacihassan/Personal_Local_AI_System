"""
AdvancedSearchEngine - Premium Çoklu Kaynak Arama Motoru
========================================================

Desteklenen Kaynaklar:
1. Semantic Scholar API
2. CrossRef API
3. ArXiv API
4. PubMed (NCBI E-utilities)
5. OpenAlex API
6. CORE API
"""

import asyncio
import json
import re
import hashlib
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from urllib.parse import quote_plus

try:
    import aiohttp
except ImportError:
    aiohttp = None


class SearchSource(str, Enum):
    """Arama kaynakları."""
    SEMANTIC_SCHOLAR = "semantic_scholar"
    CROSSREF = "crossref"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    OPENALEX = "openalex"
    CORE = "core"


class DocumentType(str, Enum):
    """Doküman türleri."""
    JOURNAL_ARTICLE = "journal_article"
    CONFERENCE_PAPER = "conference_paper"
    PREPRINT = "preprint"
    BOOK = "book"
    THESIS = "thesis"
    DATASET = "dataset"
    OTHER = "other"


@dataclass
class Author:
    """Yazar bilgisi."""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    h_index: Optional[int] = None
    
    
@dataclass
class SearchResult:
    """Arama sonucu."""
    id: str
    title: str
    authors: List[Author]
    abstract: Optional[str]
    year: Optional[int]
    source: SearchSource
    
    # Bibliyografik bilgiler
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    venue: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    
    # Metrikler
    citation_count: int = 0
    influence_score: float = 0.0
    
    # Tam metin durumu
    open_access: bool = False
    full_text_available: bool = False
    
    # Anahtar kelimeler
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Sözlüğe dönüştür."""
        return {
            "id": self.id,
            "title": self.title,
            "authors": [a.name for a in self.authors],
            "abstract": self.abstract,
            "year": self.year,
            "source": self.source.value,
            "doi": self.doi,
            "url": self.url,
            "citation_count": self.citation_count,
            "open_access": self.open_access
        }


@dataclass
class SearchQuery:
    """Arama sorgusu."""
    query: str
    filters: Dict[str, Any] = field(default_factory=dict)
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    document_types: List[DocumentType] = field(default_factory=list)
    open_access_only: bool = False
    limit: int = 20
    offset: int = 0


class AdvancedSearchEngine:
    """
    Premium Çoklu Kaynak Arama Motoru
    
    Birden fazla akademik veritabanını arar, 
    sonuçları birleştirir ve sıralar.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.cache: Dict[str, List[SearchResult]] = {}
        
        # API endpoints
        self.endpoints = {
            SearchSource.SEMANTIC_SCHOLAR: "https://api.semanticscholar.org/graph/v1",
            SearchSource.CROSSREF: "https://api.crossref.org/works",
            SearchSource.ARXIV: "http://export.arxiv.org/api/query",
            SearchSource.PUBMED: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            SearchSource.OPENALEX: "https://api.openalex.org/works"
        }
        
        # Rate limiting
        self._last_request_time: Dict[str, float] = {}
        self._rate_limits = {
            SearchSource.SEMANTIC_SCHOLAR: 1.0,  # 1 request per second
            SearchSource.CROSSREF: 0.5,
            SearchSource.ARXIV: 3.0,  # 3 seconds between requests
            SearchSource.PUBMED: 0.35,  # ~3 requests per second
            SearchSource.OPENALEX: 0.1
        }
    
    async def search(
        self,
        query: Union[str, SearchQuery],
        sources: Optional[List[SearchSource]] = None,
        max_results: int = 50
    ) -> List[SearchResult]:
        """
        Çoklu kaynakta arama yap.
        
        Args:
            query: Arama sorgusu
            sources: Aranacak kaynaklar
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Birleştirilmiş ve sıralanmış sonuçlar
        """
        if isinstance(query, str):
            query = SearchQuery(query=query, limit=max_results)
        
        sources = sources or [
            SearchSource.SEMANTIC_SCHOLAR,
            SearchSource.CROSSREF,
            SearchSource.OPENALEX
        ]
        
        # Cache kontrolü
        cache_key = self._get_cache_key(query, sources)
        if cache_key in self.cache:
            return self.cache[cache_key][:max_results]
        
        # Paralel arama
        all_results: List[SearchResult] = []
        
        for source in sources:
            try:
                results = await self._search_source(source, query)
                all_results.extend(results)
            except Exception as e:
                print(f"Search error for {source.value}: {e}")
        
        # Duplikasyonları kaldır ve sırala
        unique_results = self._deduplicate_results(all_results)
        sorted_results = self._rank_results(unique_results, query.query)
        
        # Cache'e kaydet
        self.cache[cache_key] = sorted_results
        
        return sorted_results[:max_results]
    
    async def search_semantic_scholar(
        self,
        query: SearchQuery
    ) -> List[SearchResult]:
        """Semantic Scholar'da ara."""
        if not aiohttp:
            return []
        
        await self._rate_limit(SearchSource.SEMANTIC_SCHOLAR)
        
        params = {
            "query": query.query,
            "limit": min(query.limit, 100),
            "offset": query.offset,
            "fields": "paperId,title,abstract,authors,year,citationCount,"
                     "influentialCitationCount,venue,publicationTypes,openAccessPdf"
        }
        
        if query.year_from:
            params["year"] = f"{query.year_from}-{query.year_to or datetime.now().year}"
        
        results = []
        
        try:
            url = f"{self.endpoints[SearchSource.SEMANTIC_SCHOLAR]}/paper/search"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        for paper in data.get("data", []):
                            result = SearchResult(
                                id=paper.get("paperId", ""),
                                title=paper.get("title", ""),
                                authors=[
                                    Author(name=a.get("name", ""))
                                    for a in paper.get("authors", [])
                                ],
                                abstract=paper.get("abstract"),
                                year=paper.get("year"),
                                source=SearchSource.SEMANTIC_SCHOLAR,
                                venue=paper.get("venue"),
                                citation_count=paper.get("citationCount", 0),
                                influence_score=paper.get("influentialCitationCount", 0) / 100,
                                open_access=bool(paper.get("openAccessPdf")),
                                pdf_url=paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None
                            )
                            results.append(result)
        except Exception as e:
            print(f"Semantic Scholar error: {e}")
        
        return results
    
    async def search_crossref(
        self,
        query: SearchQuery
    ) -> List[SearchResult]:
        """CrossRef'te ara."""
        if not aiohttp:
            return []
        
        await self._rate_limit(SearchSource.CROSSREF)
        
        params = {
            "query": query.query,
            "rows": min(query.limit, 100),
            "offset": query.offset
        }
        
        if query.year_from:
            params["filter"] = f"from-pub-date:{query.year_from}"
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints[SearchSource.CROSSREF],
                    params=params,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get("message", {}).get("items", []):
                            result = SearchResult(
                                id=item.get("DOI", ""),
                                title=item.get("title", [""])[0] if item.get("title") else "",
                                authors=[
                                    Author(
                                        name=f"{a.get('given', '')} {a.get('family', '')}".strip(),
                                        affiliation=a.get("affiliation", [{}])[0].get("name") if a.get("affiliation") else None
                                    )
                                    for a in item.get("author", [])
                                ],
                                abstract=item.get("abstract"),
                                year=item.get("published-print", {}).get("date-parts", [[None]])[0][0] or
                                     item.get("published-online", {}).get("date-parts", [[None]])[0][0],
                                source=SearchSource.CROSSREF,
                                doi=item.get("DOI"),
                                url=item.get("URL"),
                                venue=item.get("container-title", [""])[0] if item.get("container-title") else None,
                                citation_count=item.get("is-referenced-by-count", 0),
                                open_access=item.get("is-referenced-by-count") == "open-access"
                            )
                            results.append(result)
        except Exception as e:
            print(f"CrossRef error: {e}")
        
        return results
    
    async def search_openalex(
        self,
        query: SearchQuery
    ) -> List[SearchResult]:
        """OpenAlex'te ara."""
        if not aiohttp:
            return []
        
        await self._rate_limit(SearchSource.OPENALEX)
        
        params = {
            "search": query.query,
            "per-page": min(query.limit, 200),
            "page": (query.offset // query.limit) + 1
        }
        
        filters = []
        if query.year_from:
            filters.append(f"publication_year:>{query.year_from-1}")
        if query.year_to:
            filters.append(f"publication_year:<{query.year_to+1}")
        if query.open_access_only:
            filters.append("is_oa:true")
        
        if filters:
            params["filter"] = ",".join(filters)
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints[SearchSource.OPENALEX],
                    params=params,
                    headers={"User-Agent": "DeepScholar/1.0"},
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for work in data.get("results", []):
                            result = SearchResult(
                                id=work.get("id", ""),
                                title=work.get("title", ""),
                                authors=[
                                    Author(
                                        name=a.get("author", {}).get("display_name", ""),
                                        affiliation=a.get("institutions", [{}])[0].get("display_name") if a.get("institutions") else None,
                                        orcid=a.get("author", {}).get("orcid")
                                    )
                                    for a in work.get("authorships", [])
                                ],
                                abstract=self._reconstruct_abstract(work.get("abstract_inverted_index")),
                                year=work.get("publication_year"),
                                source=SearchSource.OPENALEX,
                                doi=work.get("doi", "").replace("https://doi.org/", "") if work.get("doi") else None,
                                url=work.get("id"),
                                venue=work.get("primary_location", {}).get("source", {}).get("display_name") if work.get("primary_location") else None,
                                citation_count=work.get("cited_by_count", 0),
                                open_access=work.get("open_access", {}).get("is_oa", False),
                                pdf_url=work.get("open_access", {}).get("oa_url"),
                                keywords=[c.get("display_name", "") for c in work.get("concepts", [])[:5]]
                            )
                            results.append(result)
        except Exception as e:
            print(f"OpenAlex error: {e}")
        
        return results
    
    async def search_arxiv(
        self,
        query: SearchQuery
    ) -> List[SearchResult]:
        """ArXiv'de ara."""
        if not aiohttp:
            return []
        
        await self._rate_limit(SearchSource.ARXIV)
        
        params = {
            "search_query": f"all:{quote_plus(query.query)}",
            "start": query.offset,
            "max_results": min(query.limit, 100),
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.endpoints[SearchSource.ARXIV],
                    params=params,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        # XML parse
                        results = self._parse_arxiv_xml(text)
        except Exception as e:
            print(f"ArXiv error: {e}")
        
        return results
    
    def _parse_arxiv_xml(self, xml_text: str) -> List[SearchResult]:
        """ArXiv XML çıktısını parse et."""
        results = []
        
        # Basit regex ile parse
        entries = re.findall(r'<entry>(.*?)</entry>', xml_text, re.DOTALL)
        
        for entry in entries:
            id_match = re.search(r'<id>(.*?)</id>', entry)
            title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            abstract_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
            
            authors = []
            for author_match in re.finditer(r'<author>.*?<name>(.*?)</name>.*?</author>', entry, re.DOTALL):
                authors.append(Author(name=author_match.group(1).strip()))
            
            year = None
            published_match = re.search(r'<published>(\d{4})', entry)
            if published_match:
                year = int(published_match.group(1))
            
            arxiv_id = ""
            if id_match:
                arxiv_id = id_match.group(1).split("/abs/")[-1] if "/abs/" in id_match.group(1) else id_match.group(1)
            
            result = SearchResult(
                id=arxiv_id,
                title=title_match.group(1).strip().replace("\n", " ") if title_match else "",
                authors=authors,
                abstract=abstract_match.group(1).strip().replace("\n", " ") if abstract_match else None,
                year=year,
                source=SearchSource.ARXIV,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                document_type=DocumentType.PREPRINT,
                open_access=True,
                full_text_available=True
            )
            results.append(result)
        
        return results
    
    async def _search_source(
        self,
        source: SearchSource,
        query: SearchQuery
    ) -> List[SearchResult]:
        """Tek kaynakta ara."""
        if source == SearchSource.SEMANTIC_SCHOLAR:
            return await self.search_semantic_scholar(query)
        elif source == SearchSource.CROSSREF:
            return await self.search_crossref(query)
        elif source == SearchSource.OPENALEX:
            return await self.search_openalex(query)
        elif source == SearchSource.ARXIV:
            return await self.search_arxiv(query)
        else:
            return []
    
    def _deduplicate_results(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Duplikeleri kaldır."""
        seen_dois = set()
        seen_titles = set()
        unique = []
        
        for result in results:
            # DOI ile kontrol
            if result.doi:
                doi_normalized = result.doi.lower().strip()
                if doi_normalized in seen_dois:
                    continue
                seen_dois.add(doi_normalized)
            
            # Başlık ile kontrol
            title_normalized = re.sub(r'[^\w\s]', '', result.title.lower())
            title_normalized = ' '.join(title_normalized.split())
            
            if title_normalized in seen_titles:
                continue
            seen_titles.add(title_normalized)
            
            unique.append(result)
        
        return unique
    
    def _rank_results(
        self,
        results: List[SearchResult],
        query: str
    ) -> List[SearchResult]:
        """Sonuçları sırala."""
        query_words = set(query.lower().split())
        
        def score(result: SearchResult) -> float:
            s = 0.0
            
            # Atıf sayısı (log scale)
            if result.citation_count > 0:
                import math
                s += math.log10(result.citation_count + 1) * 10
            
            # Başlık uyumu
            title_words = set(result.title.lower().split())
            overlap = len(query_words & title_words)
            s += overlap * 5
            
            # Güncellik (son 5 yıl bonus)
            if result.year:
                current_year = datetime.now().year
                years_old = current_year - result.year
                if years_old <= 2:
                    s += 15
                elif years_old <= 5:
                    s += 10
                elif years_old <= 10:
                    s += 5
            
            # Open access bonus
            if result.open_access:
                s += 5
            
            # Abstract varsa bonus
            if result.abstract:
                s += 3
            
            return s
        
        return sorted(results, key=score, reverse=True)
    
    def _reconstruct_abstract(
        self,
        inverted_index: Optional[Dict[str, List[int]]]
    ) -> Optional[str]:
        """OpenAlex inverted index'ten abstract oluştur."""
        if not inverted_index:
            return None
        
        words = []
        for word, positions in inverted_index.items():
            for pos in positions:
                words.append((pos, word))
        
        words.sort(key=lambda x: x[0])
        return " ".join(w[1] for w in words)
    
    async def _rate_limit(self, source: SearchSource):
        """Rate limiting uygula."""
        import time
        
        source_key = source.value
        min_interval = self._rate_limits.get(source, 1.0)
        
        if source_key in self._last_request_time:
            elapsed = time.time() - self._last_request_time[source_key]
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        
        self._last_request_time[source_key] = time.time()
    
    def _get_cache_key(
        self,
        query: SearchQuery,
        sources: List[SearchSource]
    ) -> str:
        """Cache key oluştur."""
        key_data = f"{query.query}:{query.year_from}:{query.year_to}:{','.join(s.value for s in sources)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def clear_cache(self):
        """Cache temizle."""
        self.cache.clear()
