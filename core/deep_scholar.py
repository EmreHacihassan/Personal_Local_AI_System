"""
DeepScholar v2.0 - Fraktal Araştırma ve Sentez Mimarisi
=======================================================

Kurumsal seviye akademik döküman oluşturucu.

Özellikler:
- Fraktal Genişleme (Fractal Expansion) - Dinamik derinlik yönetimi
- Global/Local State yönetimi - Tutarlılık için hafıza mimarisi
- Information Gain algoritması - Akıllı araştırma derinliği
- Cross-Pollination sentez motoru - Kaynak sentezleme
- Self-Correction döngüsü - Halüsinasyon kontrolü
- User Proxy simülatörü - İç kalite kontrolü
- Paralel araştırma + Sıralı yazım
- Akademik kaynakça (APA/IEEE/Chicago)
- PDF export
- Çoklu dil desteği
- Canlı ilerleme takibi (WebSocket)

Maksimum: 60 sayfa
"""

import asyncio
import json
import time
import hashlib
import re
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import traceback

from core.config import settings
from core.llm_manager import llm_manager

# Premium modüller (opsiyonel)
try:
    from core.deep_scholar_premium.advanced import (
        DynamicPageManager,
        MultiAgentDebate,
        RealTimeStreamingManager,
        OriginalityChecker,
        MultilingualResearchEngine,
        ResearchAnalyticsEngine,
        LiteratureReviewEngine,
        PRISMAGenerator
    )
    PREMIUM_ADVANCED_AVAILABLE = True
except ImportError:
    PREMIUM_ADVANCED_AVAILABLE = False


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class DocumentLanguage(str, Enum):
    """Desteklenen döküman dilleri."""
    TURKISH = "tr"
    ENGLISH = "en"
    GERMAN = "de"


class CitationStyle(str, Enum):
    """Kaynakça stilleri."""
    APA = "apa"
    IEEE = "ieee"
    CHICAGO = "chicago"
    HARVARD = "harvard"


class ResearchDepth(str, Enum):
    """Araştırma derinliği."""
    SHALLOW = "shallow"      # 1-5 sayfa: Yüzeysel özet
    MODERATE = "moderate"    # 6-15 sayfa: Orta detay
    DEEP = "deep"           # 16-30 sayfa: Derin araştırma
    EXHAUSTIVE = "exhaustive"  # 31-60 sayfa: Kapsamlı analiz


class AgentRole(str, Enum):
    """Ajan rolleri."""
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    RESEARCHER = "researcher"
    WRITER = "writer"
    FACT_CHECKER = "fact_checker"
    USER_PROXY = "user_proxy"
    SYNTHESIZER = "synthesizer"


class EventType(str, Enum):
    """WebSocket event tipleri."""
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    AGENT_MESSAGE = "agent_message"
    RESEARCH_FOUND = "research_found"
    SECTION_START = "section_start"
    SECTION_COMPLETE = "section_complete"
    CONFLICT_DETECTED = "conflict_detected"
    FACT_CHECK = "fact_check"
    USER_PROXY_FEEDBACK = "user_proxy_feedback"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETE = "complete"
    # Yeni event tipleri
    PAUSED = "paused"
    RESUMED = "resumed"
    VISUAL_GENERATED = "visual_generated"
    CHECKPOINT_SAVED = "checkpoint_saved"


class VisualType(str, Enum):
    """Görsel tipleri."""
    MERMAID_FLOWCHART = "mermaid_flowchart"
    MERMAID_SEQUENCE = "mermaid_sequence"
    MERMAID_MINDMAP = "mermaid_mindmap"
    MERMAID_TIMELINE = "mermaid_timeline"
    MERMAID_PIE = "mermaid_pie"
    MERMAID_GANTT = "mermaid_gantt"
    ASCII_TABLE = "ascii_table"
    ASCII_CHART = "ascii_chart"
    LATEX_FORMULA = "latex_formula"
    CODE_BLOCK = "code_block"
    COMPARISON_TABLE = "comparison_table"
    STATISTICS_BOX = "statistics_box"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Citation:
    """Akademik atıf."""
    id: str
    source_type: str  # web, pdf, article, book
    title: str
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    pages: Optional[str] = None
    access_date: Optional[str] = None
    
    # Döküman içi kullanım
    used_in_pages: List[int] = field(default_factory=list)
    used_in_sections: List[str] = field(default_factory=list)
    inline_citations: List[Dict] = field(default_factory=list)  # {page, line, text}
    
    def to_apa(self) -> str:
        """APA formatında kaynakça."""
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        year_str = f"({self.year})" if self.year else "(n.d.)"
        
        if self.url:
            return f"{authors_str} {year_str}. {self.title}. Retrieved from {self.url}"
        elif self.journal:
            return f"{authors_str} {year_str}. {self.title}. {self.journal}, {self.pages or ''}."
        else:
            return f"{authors_str} {year_str}. {self.title}. {self.publisher or ''}."
    
    def to_ieee(self) -> str:
        """IEEE formatında kaynakça."""
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        
        if self.journal:
            return f'{authors_str}, "{self.title}," {self.journal}, {self.year or "n.d."}.'
        elif self.url:
            return f'{authors_str}, "{self.title}," [Online]. Available: {self.url}'
        else:
            return f'{authors_str}, "{self.title}," {self.publisher or ""}, {self.year or "n.d."}.'
    
    def to_chicago(self) -> str:
        """Chicago formatında kaynakça."""
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        
        if self.journal:
            return f'{authors_str}. "{self.title}." {self.journal} ({self.year or "n.d."}): {self.pages or ""}.'
        else:
            return f'{authors_str}. {self.title}. {self.publisher or ""}, {self.year or "n.d."}.'


@dataclass
class ResearchItem:
    """Araştırma sonucu."""
    id: str
    content: str
    source_title: str
    source_url: Optional[str] = None
    source_type: str = "web"  # web, pdf, academic, local
    relevance_score: float = 0.0
    reliability_score: float = 0.5
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    claims: List[str] = field(default_factory=list)  # Çıkarılan iddialar
    evidence: List[str] = field(default_factory=list)  # Kanıtlar


@dataclass
class SectionOutline:
    """Bölüm taslağı."""
    id: str
    title: str
    level: int  # 1 = ana bölüm, 2 = alt bölüm, 3 = alt-alt
    page_start: int
    page_end: int
    word_target: int
    subtopics: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    research_queries: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Bağımlı olduğu bölümler
    parent_id: Optional[str] = None


@dataclass
class GlobalState:
    """
    Global State (Uzun Süreli Hafıza)
    Tüm ajanlar tarafından okunabilir, sadece Orchestrator tarafından değiştirilebilir.
    """
    # Master plan
    master_outline: List[SectionOutline] = field(default_factory=list)
    thesis_statement: str = ""
    
    # Tutarlılık için
    global_glossary: Dict[str, str] = field(default_factory=dict)  # Terim -> Açıklama
    style_guide: Dict[str, str] = field(default_factory=dict)
    
    # Kaynaklar
    all_citations: Dict[str, Citation] = field(default_factory=dict)  # id -> Citation
    citation_counter: int = 0
    
    # Üst bilgi
    document_title: str = ""
    document_topic: str = ""
    target_pages: int = 10
    language: DocumentLanguage = DocumentLanguage.TURKISH
    citation_style: CitationStyle = CitationStyle.APA
    
    # Yazım tamamlanan bölümler
    completed_sections: Dict[str, str] = field(default_factory=dict)  # section_id -> content
    section_summaries: Dict[str, str] = field(default_factory=dict)  # section_id -> summary


@dataclass
class LocalState:
    """
    Local State (Kısa Süreli Hafıza)
    Sadece aktif bölümü ilgilendirir, bölüm bitince temizlenir.
    """
    current_section: Optional[SectionOutline] = None
    current_sources: List[ResearchItem] = field(default_factory=list)
    previous_section_summary: str = ""
    current_content: str = ""
    current_word_count: int = 0
    
    # Sentez için
    extracted_claims: List[Dict] = field(default_factory=list)
    detected_conflicts: List[Dict] = field(default_factory=list)
    
    def clear(self):
        """Bölüm tamamlandığında temizle."""
        self.current_section = None
        self.current_sources = []
        self.current_content = ""
        self.current_word_count = 0
        self.extracted_claims = []
        self.detected_conflicts = []


@dataclass
class AgentMessage:
    """Ajanlar arası mesaj."""
    from_agent: AgentRole
    to_agent: AgentRole
    message_type: str
    content: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DeepScholarConfig:
    """DeepScholar yapılandırması."""
    title: str
    topic: str
    page_count: int = 10
    language: DocumentLanguage = DocumentLanguage.TURKISH
    citation_style: CitationStyle = CitationStyle.APA
    style: str = "academic"  # academic, casual, detailed, summary, exam_prep
    
    # Araştırma ayarları
    web_search: str = "auto"  # off, auto, on
    academic_search: bool = True
    max_sources_per_section: int = 10
    
    # Kalite ayarları
    enable_fact_checking: bool = True
    enable_user_proxy: bool = True
    enable_conflict_detection: bool = True
    
    # Kullanıcı talimatları
    custom_instructions: str = ""
    user_persona: str = ""  # User Proxy için persona
    
    # Gelişmiş
    parallel_research: bool = True
    max_research_depth: int = 3  # Fraktal derinlik
    
    # Görsel üretim ayarları (Premium)
    enable_visuals: bool = True  # Görsel üretimi aktif
    visual_types: List[str] = field(default_factory=lambda: [
        "mermaid_flowchart", "mermaid_mindmap", "ascii_table", 
        "latex_formula", "comparison_table", "statistics_box"
    ])
    visuals_per_section: int = 2  # Bölüm başına maksimum görsel sayısı
    enable_code_examples: bool = True  # Kod örnekleri ekle
    enable_formulas: bool = True  # Matematiksel formüller ekle
    
    # 🚀 Premium V2 Özellikler
    enable_dynamic_pages: bool = True  # Dinamik sayfa artırma (max +15)
    max_page_expansion: int = 15  # Maksimum ek sayfa sayısı
    enable_debate_mode: bool = False  # Çok ajanlı tartışma modu
    debate_perspectives: List[str] = field(default_factory=lambda: ["pro", "con", "devils_advocate"])
    enable_originality_check: bool = True  # Orijinallik kontrolü
    enable_multilingual: bool = False  # Çok dilli araştırma
    research_languages: List[str] = field(default_factory=lambda: ["en", "tr"])
    enable_analytics: bool = True  # Araştırma analitiği
    enable_literature_review: bool = False  # Sistematik literatür tarama (PRISMA)
    enable_realtime_streaming: bool = True  # Gerçek zamanlı streaming


@dataclass
class GenerationCheckpoint:
    """Üretim checkpoint'i - Pause/Resume için."""
    document_id: str
    config: Dict[str, Any]
    progress: int
    current_phase: str
    completed_sections: List[Dict[str, Any]]
    pending_sections: List[Dict[str, Any]]
    all_research: Dict[str, List[Dict[str, Any]]]
    global_state: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """JSON'a dönüştür."""
        return {
            "document_id": self.document_id,
            "config": self.config,
            "progress": self.progress,
            "current_phase": self.current_phase,
            "completed_sections": self.completed_sections,
            "pending_sections": self.pending_sections,
            "all_research": self.all_research,
            "global_state": self.global_state,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenerationCheckpoint':
        """JSON'dan oluştur."""
        return cls(
            document_id=data["document_id"],
            config=data["config"],
            progress=data["progress"],
            current_phase=data["current_phase"],
            completed_sections=data["completed_sections"],
            pending_sections=data["pending_sections"],
            all_research=data["all_research"],
            global_state=data["global_state"],
            created_at=data.get("created_at", datetime.now().isoformat())
        )


# ============================================================================
# ACADEMIC SEARCH ENGINE
# ============================================================================

class AcademicSearchEngine:
    """
    Ücretsiz akademik arama motoru.
    
    Desteklenen kaynaklar:
    - Semantic Scholar API (ücretsiz)
    - arXiv API (ücretsiz)
    - CrossRef API (ücretsiz)
    - CORE API (ücretsiz)
    - OpenAlex API (ücretsiz)
    """
    
    def __init__(self):
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        self.arxiv_base = "http://export.arxiv.org/api/query"
        self.crossref_base = "https://api.crossref.org/works"
        self.openalex_base = "https://api.openalex.org"
        
    async def search_semantic_scholar(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[ResearchItem]:
        """Semantic Scholar'da arama."""
        import aiohttp
        
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.semantic_scholar_base}/paper/search"
                params = {
                    "query": query,
                    "limit": limit,
                    "fields": "title,abstract,authors,year,url,citationCount,journal"
                }
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        for paper in data.get("data", []):
                            authors = [a.get("name", "") for a in paper.get("authors", [])]
                            results.append(ResearchItem(
                                id=f"ss_{paper.get('paperId', '')}",
                                content=paper.get("abstract", "") or "",
                                source_title=paper.get("title", ""),
                                source_url=paper.get("url"),
                                source_type="academic",
                                authors=authors,
                                year=paper.get("year"),
                                abstract=paper.get("abstract"),
                                relevance_score=min(paper.get("citationCount", 0) / 100, 1.0),
                                reliability_score=0.9  # Akademik kaynak
                            ))
        except Exception as e:
            print(f"[Semantic Scholar Error] {e}")
        
        return results
    
    async def search_arxiv(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[ResearchItem]:
        """arXiv'de arama."""
        import aiohttp
        import xml.etree.ElementTree as ET
        
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": limit,
                    "sortBy": "relevance"
                }
                
                async with session.get(self.arxiv_base, params=params, timeout=30) as response:
                    if response.status == 200:
                        text = await response.text()
                        root = ET.fromstring(text)
                        
                        ns = {"atom": "http://www.w3.org/2005/Atom"}
                        
                        for entry in root.findall("atom:entry", ns):
                            title = entry.find("atom:title", ns)
                            summary = entry.find("atom:summary", ns)
                            published = entry.find("atom:published", ns)
                            link = entry.find("atom:id", ns)
                            
                            authors = []
                            for author in entry.findall("atom:author", ns):
                                name = author.find("atom:name", ns)
                                if name is not None:
                                    authors.append(name.text)
                            
                            year = None
                            if published is not None and published.text:
                                year = int(published.text[:4])
                            
                            results.append(ResearchItem(
                                id=f"arxiv_{hashlib.md5((link.text or '').encode()).hexdigest()[:8]}",
                                content=summary.text if summary is not None else "",
                                source_title=title.text if title is not None else "",
                                source_url=link.text if link is not None else None,
                                source_type="academic",
                                authors=authors,
                                year=year,
                                abstract=summary.text if summary is not None else None,
                                relevance_score=0.85,
                                reliability_score=0.9
                            ))
        except Exception as e:
            print(f"[arXiv Error] {e}")
        
        return results
    
    async def search_crossref(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[ResearchItem]:
        """CrossRef'te arama."""
        import aiohttp
        
        results = []
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "query": query,
                    "rows": limit,
                    "select": "title,abstract,author,published-print,URL,DOI,container-title"
                }
                
                async with session.get(self.crossref_base, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        for item in data.get("message", {}).get("items", []):
                            authors = []
                            for author in item.get("author", []):
                                name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                                if name:
                                    authors.append(name)
                            
                            year = None
                            published = item.get("published-print", {}).get("date-parts", [[]])
                            if published and published[0]:
                                year = published[0][0]
                            
                            title = item.get("title", [""])[0] if item.get("title") else ""
                            
                            results.append(ResearchItem(
                                id=f"cr_{item.get('DOI', hashlib.md5(title.encode()).hexdigest()[:8])}",
                                content=item.get("abstract", "") or "",
                                source_title=title,
                                source_url=item.get("URL"),
                                source_type="academic",
                                authors=authors,
                                year=year,
                                abstract=item.get("abstract"),
                                relevance_score=0.8,
                                reliability_score=0.85
                            ))
        except Exception as e:
            print(f"[CrossRef Error] {e}")
        
        return results
    
    async def search_all(
        self, 
        query: str, 
        limit_per_source: int = 5
    ) -> List[ResearchItem]:
        """Tüm kaynaklarda paralel arama."""
        tasks = [
            self.search_semantic_scholar(query, limit_per_source),
            self.search_arxiv(query, limit_per_source),
            self.search_crossref(query, limit_per_source),
        ]
        
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        for results in results_lists:
            if isinstance(results, list):
                all_results.extend(results)
        
        # Sırala ve deduplicate
        seen_titles = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.relevance_score, reverse=True):
            title_lower = r.source_title.lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_results.append(r)
        
        return unique_results


# ============================================================================
# WEB SEARCH ENGINE
# ============================================================================

class WebSearchEngine:
    """Web arama motoru wrapper."""
    
    async def search(
        self, 
        query: str, 
        num_results: int = 5
    ) -> List[ResearchItem]:
        """Web'de arama."""
        results = []
        
        try:
            from tools.web_search_engine import PremiumWebSearchEngine
            
            engine = PremiumWebSearchEngine()
            web_result = engine.search(query, num_results=num_results)
            
            if hasattr(web_result, 'results'):
                for wr in web_result.results:
                    content = getattr(wr, 'full_content', None) or getattr(wr, 'snippet', '') or ''
                    
                    results.append(ResearchItem(
                        id=f"web_{hashlib.md5(getattr(wr, 'url', '').encode()).hexdigest()[:8]}",
                        content=content[:2000],
                        source_title=getattr(wr, 'title', '') or 'Web Page',
                        source_url=getattr(wr, 'url', None),
                        source_type="web",
                        relevance_score=getattr(wr, 'relevance_score', 0.7),
                        reliability_score=getattr(wr, 'reliability_score', 0.5)
                    ))
        except Exception as e:
            print(f"[Web Search Error] {e}")
        
        return results


# ============================================================================
# DEEP SCHOLAR AGENTS
# ============================================================================

class BaseAgent:
    """Temel ajan sınıfı."""
    
    def __init__(self, role: AgentRole, global_state: GlobalState):
        self.role = role
        self.global_state = global_state
        self._executor = ThreadPoolExecutor(max_workers=2)
    
    async def _llm_generate(self, prompt: str, temperature: float = 0.7, timeout: int = 600) -> str:
        """LLM çağrısı (async wrapper with timeout).
        
        Args:
            prompt: LLM'e gönderilecek prompt
            temperature: Yaratıcılık seviyesi
            timeout: Maksimum bekleme süresi (saniye), varsayılan 10 dakika (kalite için yeterli düşünme süresi)
        """
        loop = asyncio.get_event_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    lambda: llm_manager.generate(prompt, temperature=temperature)
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"LLM çağrısı {timeout} saniye içinde yanıt vermedi")
    
    def _parse_json(self, text: str) -> Any:
        """JSON parse with fallback."""
        try:
            # JSON bloğunu bul
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Direkt JSON dene
            json_match = re.search(r'[\[\{][\s\S]*[\]\}]', text)
            if json_match:
                return json.loads(json_match.group(0))
            
            return json.loads(text)
        except:
            return None


class PlannerAgent(BaseAgent):
    """
    Planlama Ajanı
    
    Görevler:
    - Döküman iskeletini oluştur
    - Sayfa dağılımını hesapla
    - Araştırma sorgularını belirle
    - Fraktal genişleme kararları
    """
    
    def __init__(self, global_state: GlobalState):
        super().__init__(AgentRole.PLANNER, global_state)
    
    async def create_master_outline(
        self, 
        config: DeepScholarConfig
    ) -> List[SectionOutline]:
        """Ana içerik planını oluştur."""
        
        # Derinlik hesapla
        if config.page_count <= 5:
            depth = ResearchDepth.SHALLOW
            section_count = 4  # Giriş, 2 bölüm, Sonuç
        elif config.page_count <= 15:
            depth = ResearchDepth.MODERATE
            section_count = 6
        elif config.page_count <= 30:
            depth = ResearchDepth.DEEP
            section_count = 10
        else:
            depth = ResearchDepth.EXHAUSTIVE
            section_count = 15
        
        words_per_page = 400
        total_words = config.page_count * words_per_page
        
        lang_prompts = {
            DocumentLanguage.TURKISH: "Türkçe",
            DocumentLanguage.ENGLISH: "English",
            DocumentLanguage.GERMAN: "Deutsch"
        }
        
        prompt = f"""Sen akademik bir döküman planlayıcısısın. Aşağıdaki konu için {config.page_count} sayfalık kapsamlı bir döküman planı oluştur.

KONU: {config.topic}
BAŞLIK: {config.title}
DİL: {lang_prompts.get(config.language, 'Türkçe')}
ARAŞTIRMA DERİNLİĞİ: {depth.value}
TOPLAM KELİME HEDEFİ: ~{total_words} kelime
TAHMİNİ BÖLÜM SAYISI: {section_count}
YAZI STİLİ: {config.style}

{f'KULLANICI TALİMATLARI: {config.custom_instructions}' if config.custom_instructions else ''}

Her bölüm için şunları planla:
1. Bölüm başlığı ve seviyesi (1=ana, 2=alt, 3=alt-alt)
2. Sayfa aralığı
3. Kelime hedefi
4. Alt konular
5. Araştırılması gereken anahtar noktalar
6. Web/Akademik arama sorguları
7. Bağımlı olduğu önceki bölümler

JSON formatında döndür:
```json
[
  {{
    "id": "sec_1",
    "title": "Giriş",
    "level": 1,
    "page_start": 1,
    "page_end": 2,
    "word_target": 800,
    "subtopics": ["Konunun önemi", "Araştırma sorusu"],
    "key_points": ["Ana argüman", "Kapsam"],
    "research_queries": ["konu genel bakış", "konu tarihçesi"],
    "dependencies": []
  }},
  ...
]
```

Önemli kurallar:
- Giriş ve Sonuç bölümleri mutlaka olmalı
- Sayfa dağılımı dengeli olmalı
- Toplam {config.page_count} sayfayı geçmemeli
- Her bölüm mantıksal bir akış izlemeli
- Araştırma sorguları spesifik ve aranabilir olmalı"""

        response = await self._llm_generate(prompt)
        
        outline_data = self._parse_json(response)
        
        # Validate outline_data is a list of dicts
        if not outline_data or not isinstance(outline_data, list):
            return self._default_outline(config)
        
        sections = []
        for i, sec in enumerate(outline_data):
            # Skip non-dict elements (e.g., if LLM returns list of strings)
            if not isinstance(sec, dict):
                continue
            sections.append(SectionOutline(
                id=sec.get("id", f"sec_{i+1}"),
                title=sec.get("title", f"Bölüm {i+1}"),
                level=sec.get("level", 1),
                page_start=sec.get("page_start", i+1),
                page_end=sec.get("page_end", i+2),
                word_target=sec.get("word_target", 400),
                subtopics=sec.get("subtopics", []),
                key_points=sec.get("key_points", []),
                research_queries=sec.get("research_queries", [config.topic]),
                dependencies=sec.get("dependencies", []),
                parent_id=sec.get("parent_id")
            ))
        
        # If no valid sections found, use default
        if not sections:
            return self._default_outline(config)
        
        return sections
    
    def _default_outline(self, config: DeepScholarConfig) -> List[SectionOutline]:
        """Varsayılan plan."""
        words_per_page = 400
        total_words = config.page_count * words_per_page
        
        return [
            SectionOutline(
                id="sec_1",
                title="Giriş" if config.language == DocumentLanguage.TURKISH else "Introduction",
                level=1,
                page_start=1,
                page_end=max(1, config.page_count // 6),
                word_target=total_words // 6,
                subtopics=[config.topic],
                key_points=["Konunun önemi", "Araştırma sorusu"],
                research_queries=[f"{config.topic} genel bakış", f"{config.topic} tarihçe"]
            ),
            SectionOutline(
                id="sec_2",
                title="Ana İçerik" if config.language == DocumentLanguage.TURKISH else "Main Content",
                level=1,
                page_start=max(1, config.page_count // 6) + 1,
                page_end=config.page_count - max(1, config.page_count // 6),
                word_target=int(total_words * 0.7),
                subtopics=[config.topic],
                key_points=["Temel kavramlar", "Detaylı analiz"],
                research_queries=[config.topic, f"{config.topic} detaylar"]
            ),
            SectionOutline(
                id="sec_3",
                title="Sonuç" if config.language == DocumentLanguage.TURKISH else "Conclusion",
                level=1,
                page_start=config.page_count - max(1, config.page_count // 6) + 1,
                page_end=config.page_count,
                word_target=total_words // 6,
                subtopics=["Özet"],
                key_points=["Ana bulgular", "Gelecek çalışmalar"],
                research_queries=[]
            )
        ]
    
    async def expand_section(
        self, 
        section: SectionOutline, 
        current_research: List[ResearchItem],
        target_depth: int
    ) -> List[SectionOutline]:
        """
        Fraktal Genişleme - Bölümü alt bölümlere ayır.
        
        Information Gain algoritması: Eğer toplanan veri yeterince zenginse,
        bölümü daha küçük parçalara böl.
        """
        if target_depth <= 0:
            return [section]
        
        # Bilgi kazancını hesapla
        info_density = len(current_research) * sum(r.relevance_score for r in current_research)
        
        # Yeterli bilgi yoksa genişleme yapma
        if info_density < 2.0:
            return [section]
        
        prompt = f"""Bu bölümü alt bölümlere ayır:

BÖLÜM: {section.title}
ALT KONULAR: {', '.join(section.subtopics)}
KELİME HEDEFİ: {section.word_target}

MEVCUT ARAŞTIRMA KONULARI:
{chr(10).join([f"- {r.source_title}: {r.content[:200]}..." for r in current_research[:5]])}

Bu bölümü 2-4 alt bölüme ayır. JSON formatında döndür:
```json
[
  {{"title": "Alt Bölüm 1", "key_points": ["..."], "word_target": 200}},
  ...
]
```"""

        response = await self._llm_generate(prompt)
        subsections_data = self._parse_json(response)
        
        if not subsections_data or len(subsections_data) < 2:
            return [section]
        
        # Alt bölümleri oluştur
        subsections = []
        word_per_sub = section.word_target // len(subsections_data)
        page_per_sub = max(1, (section.page_end - section.page_start + 1) // len(subsections_data))
        
        for i, sub in enumerate(subsections_data):
            subsections.append(SectionOutline(
                id=f"{section.id}_{i+1}",
                title=sub.get("title", f"Alt Bölüm {i+1}"),
                level=section.level + 1,
                page_start=section.page_start + i * page_per_sub,
                page_end=section.page_start + (i + 1) * page_per_sub - 1,
                word_target=word_per_sub,
                subtopics=sub.get("subtopics", []),
                key_points=sub.get("key_points", []),
                research_queries=sub.get("research_queries", [sub.get("title", "")]),
                parent_id=section.id
            ))
        
        return subsections


class ResearcherAgent(BaseAgent):
    """
    Araştırmacı Ajan
    
    Görevler:
    - Web araması
    - Akademik kaynak araması
    - RAG ile yerel kaynak araması
    - Claim extraction (İddia çıkarma)
    - Conflict detection (Çelişki tespiti)
    """
    
    def __init__(self, global_state: GlobalState):
        super().__init__(AgentRole.RESEARCHER, global_state)
        self.academic_engine = AcademicSearchEngine()
        self.web_engine = WebSearchEngine()
    
    async def research_section(
        self,
        section: SectionOutline,
        config: DeepScholarConfig,
        local_state: LocalState
    ) -> List[ResearchItem]:
        """Bölüm için araştırma yap."""
        all_results = []
        
        # Araştırma sorguları
        queries = section.research_queries or [section.title]
        queries.extend(section.key_points[:3])
        queries = list(set(queries))[:8]  # Max 8 sorgu
        
        tasks = []
        
        # Web araması
        if config.web_search in ["on", "auto"]:
            for query in queries[:3]:
                tasks.append(self.web_engine.search(query, 3))
        
        # Akademik arama
        if config.academic_search:
            for query in queries[:3]:
                tasks.append(self.academic_engine.search_all(query, 3))
        
        # Paralel arama
        if config.parallel_research:
            results_lists = await asyncio.gather(*tasks, return_exceptions=True)
            for results in results_lists:
                if isinstance(results, list):
                    all_results.extend(results)
        else:
            for task in tasks:
                try:
                    results = await task
                    all_results.extend(results)
                except:
                    pass
        
        # RAG araması
        try:
            from core.vector_store import vector_store
            for query in queries[:5]:
                rag_results = vector_store.search_with_scores(
                    query=query,
                    n_results=5,
                    score_threshold=0.3
                )
                for r in rag_results:
                    all_results.append(ResearchItem(
                        id=f"rag_{hashlib.md5(r.get('document', '')[:100].encode()).hexdigest()[:8]}",
                        content=r.get("document", ""),
                        source_title=r.get("metadata", {}).get("original_filename", "Local Document"),
                        source_type="local",
                        relevance_score=r.get("score", 0.5),
                        reliability_score=0.8
                    ))
        except Exception as e:
            print(f"[RAG Search Error] {e}")
        
        # Deduplicate ve sırala
        seen = set()
        unique_results = []
        for r in sorted(all_results, key=lambda x: x.relevance_score * x.reliability_score, reverse=True):
            content_hash = hashlib.md5(r.content[:200].encode()).hexdigest()
            if content_hash not in seen:
                seen.add(content_hash)
                unique_results.append(r)
        
        return unique_results[:config.max_sources_per_section]
    
    async def extract_claims(
        self, 
        research_items: List[ResearchItem]
    ) -> List[Dict]:
        """
        Kaynaklardan iddialar ve kanıtlar çıkar.
        Cross-Pollination için temel.
        """
        if not research_items:
            return []
        
        sources_text = "\n\n".join([
            f"[KAYNAK {i+1}] ({r.source_title}):\n{r.content[:500]}"
            for i, r in enumerate(research_items[:8])
        ])
        
        prompt = f"""Bu kaynaklardan ana iddiaları (claims) ve kanıtları (evidence) çıkar:

{sources_text}

Her iddia için:
1. İddia metni
2. Hangi kaynaktan geldiği
3. Destekleyen kanıt
4. Güven skoru (0-1)

JSON formatında döndür:
```json
[
  {{
    "claim": "İddia metni",
    "source_index": 1,
    "evidence": "Destekleyen kanıt",
    "confidence": 0.85
  }}
]
```"""

        response = await self._llm_generate(prompt)
        claims = self._parse_json(response)
        
        return claims if claims else []
    
    async def detect_conflicts(
        self, 
        claims: List[Dict]
    ) -> List[Dict]:
        """
        Çelişen iddiaları tespit et.
        Cross-Pollination sentez için kritik.
        """
        if len(claims) < 2:
            return []
        
        claims_text = "\n".join([
            f"{i+1}. {c.get('claim', '')} (Kaynak {c.get('source_index', '?')})"
            for i, c in enumerate(claims)
        ])
        
        prompt = f"""Bu iddiaları analiz et ve çelişenleri bul:

{claims_text}

Çelişen iddia çiftlerini bul ve açıkla. JSON formatında döndür:
```json
[
  {{
    "claim_1_index": 1,
    "claim_2_index": 3,
    "conflict_type": "factual|methodological|interpretive",
    "description": "Çelişkinin açıklaması",
    "possible_resolution": "Muhtemel açıklama"
  }}
]
```

Eğer çelişki yoksa boş liste döndür: []"""

        response = await self._llm_generate(prompt)
        conflicts = self._parse_json(response)
        
        return conflicts if conflicts else []


# ============================================================================
# VISUAL GENERATOR - PREMIUM FEATURE
# ============================================================================

class VisualGenerator:
    """
    Görsel Üretici - Premium Özellik
    
    Döküman içine eklenebilecek görsel öğeler:
    - Mermaid diyagramları (flowchart, sequence, mindmap, timeline, pie, gantt)
    - ASCII tablolar ve grafikler
    - LaTeX formüller
    - Karşılaştırma tabloları
    - İstatistik kutuları
    - Kod blokları
    """
    
    def __init__(self):
        self.supported_types = list(VisualType)
    
    async def _llm_generate(self, prompt: str, temperature: float = 0.7) -> str:
        """LLM ile içerik üret."""
        try:
            result = await llm_manager.generate_with_model(
                prompt=prompt,
                temperature=temperature,
                max_tokens=2000
            )
            return result.get("response", "")
        except Exception as e:
            return ""
    
    async def generate_visuals_for_section(
        self,
        section_title: str,
        section_content: str,
        topic: str,
        config: DeepScholarConfig
    ) -> List[Dict[str, Any]]:
        """Bölüm için uygun görseller üret."""
        visuals = []
        
        if not config.enable_visuals:
            return visuals
        
        # Hangi görsel tiplerinin uygun olduğunu belirle
        suitable_types = await self._analyze_content_for_visuals(
            section_title, section_content, topic, config
        )
        
        for visual_type in suitable_types[:config.visuals_per_section]:
            visual = await self._generate_visual(
                visual_type, section_title, section_content, topic, config
            )
            if visual:
                visuals.append(visual)
        
        return visuals
    
    async def _analyze_content_for_visuals(
        self,
        section_title: str,
        section_content: str,
        topic: str,
        config: DeepScholarConfig
    ) -> List[VisualType]:
        """İçeriğe uygun görsel tiplerini belirle."""
        content_preview = section_content[:1500]
        
        prompt = f"""Bu bölüm içeriğini analiz et ve en uygun görsel tiplerini seç.

BÖLÜM: {section_title}
KONU: {topic}
İÇERİK:
{content_preview}

Mevcut görsel tipleri:
1. mermaid_flowchart - Süreç, akış, karar ağacı için
2. mermaid_mindmap - Kavram haritası, ilişkiler için
3. mermaid_timeline - Tarihsel olaylar, kronoloji için
4. mermaid_pie - Dağılım, oran gösterimi için
5. ascii_table - Karşılaştırma, veri tablosu için
6. latex_formula - Matematiksel formüller için
7. comparison_table - A vs B karşılaştırması için
8. statistics_box - İstatistik, sayısal veri vurgusu için
9. code_block - Kod örneği için

İçeriğe EN UYGUN 2-3 görsel tipini JSON array olarak döndür.
Örnek: ["mermaid_flowchart", "statistics_box"]

Sadece konuyla ilgili ve faydalı olacak görselleri seç."""

        response = await self._llm_generate(prompt, temperature=0.3)
        
        try:
            # JSON parse
            import re
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                types_list = json.loads(json_match.group())
                return [VisualType(t) for t in types_list if t in [v.value for v in VisualType]]
        except:
            pass
        
        # Varsayılan: flowchart ve statistics_box
        return [VisualType.MERMAID_FLOWCHART, VisualType.STATISTICS_BOX]
    
    async def _generate_visual(
        self,
        visual_type: VisualType,
        section_title: str,
        section_content: str,
        topic: str,
        config: DeepScholarConfig
    ) -> Optional[Dict[str, Any]]:
        """Belirli tipte görsel üret."""
        
        generators = {
            VisualType.MERMAID_FLOWCHART: self._generate_mermaid_flowchart,
            VisualType.MERMAID_MINDMAP: self._generate_mermaid_mindmap,
            VisualType.MERMAID_TIMELINE: self._generate_mermaid_timeline,
            VisualType.MERMAID_PIE: self._generate_mermaid_pie,
            VisualType.MERMAID_SEQUENCE: self._generate_mermaid_sequence,
            VisualType.ASCII_TABLE: self._generate_ascii_table,
            VisualType.COMPARISON_TABLE: self._generate_comparison_table,
            VisualType.STATISTICS_BOX: self._generate_statistics_box,
            VisualType.LATEX_FORMULA: self._generate_latex_formula,
            VisualType.CODE_BLOCK: self._generate_code_block,
        }
        
        generator = generators.get(visual_type)
        if generator:
            return await generator(section_title, section_content, topic, config)
        
        return None
    
    async def _generate_mermaid_flowchart(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Mermaid flowchart üret."""
        prompt = f"""Bu içerik için bir Mermaid flowchart diyagramı oluştur.

BÖLÜM: {section_title}
İÇERİK ÖZETİ: {content[:800]}

Mermaid flowchart formatında döndür. Örnek:
```mermaid
flowchart TD
    A[Başlangıç] --> B{{Karar}}
    B -->|Evet| C[Sonuç 1]
    B -->|Hayır| D[Sonuç 2]
```

Sadece Mermaid kodu döndür, açıklama ekleme. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        
        # Mermaid kodunu temizle
        code = self._clean_mermaid_code(code)
        
        return {
            "type": VisualType.MERMAID_FLOWCHART.value,
            "title": f"📊 {section_title} - Akış Şeması",
            "code": code,
            "render_type": "mermaid"
        }
    
    async def _generate_mermaid_mindmap(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Mermaid mindmap üret."""
        prompt = f"""Bu içerik için bir Mermaid mindmap diyagramı oluştur.

BÖLÜM: {section_title}
KONU: {topic}
İÇERİK: {content[:800]}

Mermaid mindmap formatında döndür. Örnek:
```mermaid
mindmap
  root((Ana Konu))
    Alt Konu 1
      Detay A
      Detay B
    Alt Konu 2
      Detay C
```

Sadece Mermaid kodu döndür. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        code = self._clean_mermaid_code(code)
        
        return {
            "type": VisualType.MERMAID_MINDMAP.value,
            "title": f"🧠 {section_title} - Kavram Haritası",
            "code": code,
            "render_type": "mermaid"
        }
    
    async def _generate_mermaid_timeline(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Mermaid timeline üret."""
        prompt = f"""Bu içerik için bir Mermaid timeline diyagramı oluştur.

BÖLÜM: {section_title}
İÇERİK: {content[:800]}

Mermaid timeline formatında döndür. Örnek:
```mermaid
timeline
    title Tarihsel Gelişim
    1990 : Olay 1
    2000 : Olay 2
    2010 : Olay 3
```

Sadece Mermaid kodu döndür. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        code = self._clean_mermaid_code(code)
        
        return {
            "type": VisualType.MERMAID_TIMELINE.value,
            "title": f"📅 {section_title} - Zaman Çizelgesi",
            "code": code,
            "render_type": "mermaid"
        }
    
    async def _generate_mermaid_pie(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Mermaid pie chart üret."""
        prompt = f"""Bu içerik için bir Mermaid pasta grafiği oluştur.

BÖLÜM: {section_title}
İÇERİK: {content[:800]}

İçerikten uygun bir dağılım çıkar ve Mermaid pie formatında döndür. Örnek:
```mermaid
pie showData
    title Dağılım
    "Kategori A" : 40
    "Kategori B" : 35
    "Kategori C" : 25
```

Sadece Mermaid kodu döndür. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        code = self._clean_mermaid_code(code)
        
        return {
            "type": VisualType.MERMAID_PIE.value,
            "title": f"🥧 {section_title} - Dağılım",
            "code": code,
            "render_type": "mermaid"
        }
    
    async def _generate_mermaid_sequence(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Mermaid sequence diagram üret."""
        prompt = f"""Bu içerik için bir Mermaid sequence diyagramı oluştur.

BÖLÜM: {section_title}
İÇERİK: {content[:800]}

Mermaid sequence formatında döndür. Örnek:
```mermaid
sequenceDiagram
    participant A as Kullanıcı
    participant B as Sistem
    A->>B: İstek
    B-->>A: Yanıt
```

Sadece Mermaid kodu döndür. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        code = self._clean_mermaid_code(code)
        
        return {
            "type": VisualType.MERMAID_SEQUENCE.value,
            "title": f"🔄 {section_title} - Sıralı Diyagram",
            "code": code,
            "render_type": "mermaid"
        }
    
    async def _generate_ascii_table(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """ASCII tablo üret."""
        prompt = f"""Bu içerik için bir Markdown tablosu oluştur.

BÖLÜM: {section_title}
İÇERİK: {content[:800]}

İçerikten anlamlı veriler çıkar ve Markdown tablo formatında döndür. Örnek:
| Özellik | Değer | Açıklama |
|---------|-------|----------|
| A | 100 | Detay A |
| B | 200 | Detay B |

Sadece tablo kodunu döndür. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        
        return {
            "type": VisualType.ASCII_TABLE.value,
            "title": f"📋 {section_title} - Veri Tablosu",
            "code": code.strip(),
            "render_type": "markdown"
        }
    
    async def _generate_comparison_table(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Karşılaştırma tablosu üret."""
        prompt = f"""Bu içerik için bir karşılaştırma tablosu oluştur.

BÖLÜM: {section_title}
İÇERİK: {content[:800]}

İki veya daha fazla kavramı/yaklaşımı karşılaştır. Markdown tablo formatında döndür:
| Özellik | Kavram A | Kavram B |
|---------|----------|----------|
| Avantaj | ✅ X | ❌ Y |
| Dezavantaj | ⚠️ Z | ✅ W |

Sadece tablo kodunu döndür. Emoji kullan. Türkçe metin kullan."""

        code = await self._llm_generate(prompt, temperature=0.5)
        
        return {
            "type": VisualType.COMPARISON_TABLE.value,
            "title": f"⚖️ {section_title} - Karşılaştırma",
            "code": code.strip(),
            "render_type": "markdown"
        }
    
    async def _generate_statistics_box(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """İstatistik kutusu üret."""
        prompt = f"""Bu içerikten önemli istatistikleri ve sayısal verileri çıkar.

BÖLÜM: {section_title}
İÇERİK: {content[:800]}

JSON formatında döndür:
{{
  "stats": [
    {{"label": "Toplam Kullanıcı", "value": "1.5M", "icon": "👥", "trend": "up"}},
    {{"label": "Büyüme Oranı", "value": "%25", "icon": "📈", "trend": "up"}},
    {{"label": "Pazar Payı", "value": "%40", "icon": "🎯", "trend": "stable"}}
  ],
  "highlight": "Ana bulgu veya önemli sonuç"
}}

İçerikten gerçekçi ve tutarlı veriler çıkar. Veri yoksa makul tahminler yap."""

        response = await self._llm_generate(prompt, temperature=0.5)
        
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {"stats": [], "highlight": ""}
        except:
            data = {"stats": [], "highlight": ""}
        
        return {
            "type": VisualType.STATISTICS_BOX.value,
            "title": f"📊 {section_title} - İstatistikler",
            "data": data,
            "render_type": "statistics"
        }
    
    async def _generate_latex_formula(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """LaTeX formül üret."""
        if not config.enable_formulas:
            return None
        
        prompt = f"""Bu içerik için uygun matematiksel formüller üret.

BÖLÜM: {section_title}
KONU: {topic}
İÇERİK: {content[:600]}

LaTeX formatında formüller döndür. Örnek:
$$E = mc^2$$
$$\\sum_{{i=1}}^{{n}} x_i = x_1 + x_2 + ... + x_n$$

İçerikle ilgili 1-3 formül üret. Sadece LaTeX kodunu döndür."""

        code = await self._llm_generate(prompt, temperature=0.5)
        
        return {
            "type": VisualType.LATEX_FORMULA.value,
            "title": f"🔢 {section_title} - Formüller",
            "code": code.strip(),
            "render_type": "latex"
        }
    
    async def _generate_code_block(
        self, section_title: str, content: str, topic: str, config: DeepScholarConfig
    ) -> Dict[str, Any]:
        """Kod bloğu üret."""
        if not config.enable_code_examples:
            return None
        
        prompt = f"""Bu içerik için örnek bir kod bloğu oluştur.

BÖLÜM: {section_title}
KONU: {topic}
İÇERİK: {content[:600]}

Konuyla ilgili pratik ve eğitici bir kod örneği yaz.
Python, JavaScript veya uygun başka bir dilde olabilir.

Markdown code block formatında döndür:
```python
# Kod örneği
```"""

        code = await self._llm_generate(prompt, temperature=0.5)
        
        return {
            "type": VisualType.CODE_BLOCK.value,
            "title": f"💻 {section_title} - Kod Örneği",
            "code": code.strip(),
            "render_type": "code"
        }
    
    def _clean_mermaid_code(self, code: str) -> str:
        """Mermaid kodunu temizle."""
        # Markdown code block'larını kaldır
        code = re.sub(r'```mermaid\s*', '', code)
        code = re.sub(r'```\s*$', '', code)
        code = re.sub(r'```', '', code)
        return code.strip()


class WriterAgent(BaseAgent):
    """
    Yazar Ajan
    
    Görevler:
    - Bölüm içeriği yazma
    - Kaynak entegrasyonu
    - Stil tutarlılığı
    - Geçiş paragrafları
    """
    
    def __init__(self, global_state: GlobalState):
        super().__init__(AgentRole.WRITER, global_state)
    
    async def write_section(
        self,
        section: SectionOutline,
        research: List[ResearchItem],
        local_state: LocalState,
        config: DeepScholarConfig
    ) -> Tuple[str, List[Citation]]:
        """Bölüm içeriği yaz."""
        
        lang_prompts = {
            DocumentLanguage.TURKISH: "Türkçe",
            DocumentLanguage.ENGLISH: "English",
            DocumentLanguage.GERMAN: "Deutsch"
        }
        
        style_prompts = {
            "academic": "akademik, formal ve detaylı",
            "casual": "samimi, anlaşılır ve akıcı",
            "detailed": "kapsamlı, her detayı açıklayan",
            "summary": "özet, ana noktaları vurgulayan",
            "exam_prep": "sınava yönelik, önemli noktaları vurgulayan"
        }
        
        # Kaynak metni oluştur
        sources_text = ""
        source_map = {}
        for i, r in enumerate(research[:10], 1):
            sources_text += f"\n[KAYNAK {i}] ({r.source_title}"
            if r.year:
                sources_text += f", {r.year}"
            sources_text += f"):\n{r.content[:600]}\n"
            source_map[i] = r
        
        # Önceki bölüm özeti
        prev_summary = ""
        if local_state.previous_section_summary:
            prev_summary = f"\nÖNCEKİ BÖLÜM ÖZETİ:\n{local_state.previous_section_summary}\n"
        
        # Tez statement
        thesis = ""
        if self.global_state.thesis_statement:
            thesis = f"\nANA TEZ: {self.global_state.thesis_statement}\n"
        
        # Terimler sözlüğü
        glossary = ""
        if self.global_state.global_glossary:
            glossary = "\nKULLANILACAK TERİMLER:\n" + "\n".join([
                f"- {term}: {defn}" 
                for term, defn in list(self.global_state.global_glossary.items())[:10]
            ]) + "\n"
        
        prompt = f"""Bu bölüm için akademik içerik yaz.

DÖKÜMAN: {self.global_state.document_title}
BÖLÜM: {section.title}
BÖLÜM SEVİYESİ: {'#' * section.level} (Markdown başlık)
ALT KONULAR: {', '.join(section.subtopics)}
ANAHTAR NOKTALAR: {', '.join(section.key_points)}

DİL: {lang_prompts.get(config.language, 'Türkçe')}
YAZI STİLİ: {style_prompts.get(config.style, 'akademik')}
KELİME HEDEFİ: ~{section.word_target} kelime
{thesis}
{prev_summary}
{glossary}

KAYNAKLAR:
{sources_text}

YAZIM KURALLARI:
1. {'#' * section.level} ile başlık kullan
2. Kaynaklara metin içinde [KAYNAK X] şeklinde atıf yap
3. Akademik ve tutarlı bir dil kullan
4. Paragraflar arası geçişler yumuşak olsun
5. Önemli kavramları **kalın** yap
6. Gerekirse madde işaretleri kullan
7. Kelime hedefine yaklaş

{f'ÖZEL TALİMATLAR: {config.custom_instructions}' if config.custom_instructions else ''}

Şimdi bu bölümün içeriğini yaz:"""

        content = await self._llm_generate(prompt)
        
        # Citation'ları çıkar
        citations = []
        citation_pattern = r'\[KAYNAK (\d+)\]'
        
        for match in re.finditer(citation_pattern, content):
            src_idx = int(match.group(1))
            if src_idx in source_map:
                r = source_map[src_idx]
                
                # Citation oluştur
                citation = Citation(
                    id=f"cite_{self.global_state.citation_counter + 1}",
                    source_type=r.source_type,
                    title=r.source_title,
                    authors=r.authors,
                    year=r.year,
                    url=r.source_url,
                    used_in_sections=[section.id]
                )
                
                citations.append(citation)
                self.global_state.citation_counter += 1
                
                # Global state'e ekle
                if citation.id not in self.global_state.all_citations:
                    self.global_state.all_citations[citation.id] = citation
        
        # [KAYNAK X] -> [X] formatına çevir
        clean_content = content
        for i in range(1, 20):
            clean_content = clean_content.replace(f"[KAYNAK {i}]", f"[{i}]")
        
        return clean_content, citations


class FactCheckerAgent(BaseAgent):
    """
    Gerçek Kontrolü Ajanı
    
    Görevler:
    - Halüsinasyon tespiti
    - Referans doğrulama
    - Sayısal doğruluk kontrolü
    """
    
    def __init__(self, global_state: GlobalState):
        super().__init__(AgentRole.FACT_CHECKER, global_state)
    
    async def verify_content(
        self,
        content: str,
        research: List[ResearchItem]
    ) -> Dict:
        """İçeriği doğrula."""
        
        sources_text = "\n".join([
            f"[KAYNAK {i+1}]: {r.content[:300]}"
            for i, r in enumerate(research[:8])
        ])
        
        prompt = f"""Bu içeriği kaynaklarla karşılaştır ve doğrula:

İÇERİK:
{content[:2000]}

KAYNAKLAR:
{sources_text}

Her faktüel iddia için:
1. İddiayı bul
2. Kaynakta doğrulama var mı?
3. Güven skoru (0-1)

JSON formatında döndür:
```json
{{
  "verified_claims": [
    {{"claim": "...", "verified": true, "source_index": 1, "confidence": 0.9}}
  ],
  "unverified_claims": [
    {{"claim": "...", "issue": "Kaynaklarda bulunamadı"}}
  ],
  "overall_score": 0.85,
  "recommendations": ["..."]
}}
```"""

        response = await self._llm_generate(prompt)
        result = self._parse_json(response)
        
        return result if result else {
            "verified_claims": [],
            "unverified_claims": [],
            "overall_score": 0.7,
            "recommendations": []
        }


class UserProxyAgent(BaseAgent):
    """
    Kullanıcı Simülasyonu Ajanı
    
    Görevler:
    - Kullanıcı perspektifinden içerik değerlendirme
    - Anlaşılırlık kontrolü
    - Stil uygunluğu
    """
    
    def __init__(self, global_state: GlobalState, persona: str = ""):
        super().__init__(AgentRole.USER_PROXY, global_state)
        self.persona = persona
    
    async def review_content(
        self,
        content: str,
        config: DeepScholarConfig
    ) -> Dict:
        """İçeriği kullanıcı perspektifinden değerlendir."""
        
        persona_text = self.persona or config.user_persona or "genel okuyucu"
        
        prompt = f"""Sen bir okuyucu olarak bu içeriği değerlendir.

OKUYUCU PROFİLİ: {persona_text}
DİL: {config.language.value}

İÇERİK:
{content[:2000]}

Değerlendirme kriterleri:
1. Anlaşılırlık (1-10)
2. Bilgi yoğunluğu (1-10)
3. Akış ve tutarlılık (1-10)
4. Teknik terim kullanımı uygun mu?
5. Eksik veya karmaşık kısımlar var mı?

JSON formatında döndür:
```json
{{
  "clarity_score": 8,
  "density_score": 7,
  "flow_score": 8,
  "technical_terms_ok": true,
  "issues": [
    {{"location": "2. paragraf", "issue": "Terim açıklanmamış", "suggestion": "..."}}
  ],
  "overall_feedback": "Genel değerlendirme..."
}}
```"""

        response = await self._llm_generate(prompt)
        result = self._parse_json(response)
        
        return result if result else {
            "clarity_score": 7,
            "density_score": 7,
            "flow_score": 7,
            "technical_terms_ok": True,
            "issues": [],
            "overall_feedback": "İçerik genel olarak iyi."
        }


class SynthesizerAgent(BaseAgent):
    """
    Sentez Ajanı
    
    Görevler:
    - Kaynakları sentezleme
    - Çelişkileri çözme
    - Bütünleştirici paragraflar
    """
    
    def __init__(self, global_state: GlobalState):
        super().__init__(AgentRole.SYNTHESIZER, global_state)
    
    async def synthesize_claims(
        self,
        claims: List[Dict],
        conflicts: List[Dict]
    ) -> str:
        """Çelişen iddiaları sentezle."""
        
        if not conflicts:
            return ""
        
        claims_text = "\n".join([
            f"{i+1}. {c.get('claim', '')} (Güven: {c.get('confidence', 0.5)})"
            for i, c in enumerate(claims)
        ])
        
        conflicts_text = "\n".join([
            f"- Çelişki: İddia {c['claim_1_index']} vs İddia {c['claim_2_index']}: {c.get('description', '')}"
            for c in conflicts
        ])
        
        prompt = f"""Bu çelişkileri analiz et ve sentezle:

İDDİALAR:
{claims_text}

ÇELİŞKİLER:
{conflicts_text}

Her çelişki için:
1. Neden farklılık var?
2. Hangi kaynak daha güvenilir?
3. Sentez cümlesi oluştur

Akademik bir dille, çelişkileri açıklayan ve sentezleyen bir paragraf yaz."""

        response = await self._llm_generate(prompt)
        return response


# ============================================================================
# DEEP SCHOLAR ORCHESTRATOR
# ============================================================================

class DeepScholarOrchestrator:
    """
    DeepScholar Ana Orkestratör
    
    Tüm ajanları koordine eder ve döküman üretim sürecini yönetir.
    Pause/Resume ve Görsel Üretim destekler.
    """
    
    # Checkpoint'leri saklayan class-level dict
    _checkpoints: Dict[str, 'GenerationCheckpoint'] = {}
    _paused_states: Dict[str, bool] = {}
    
    def __init__(self):
        self.global_state = GlobalState()
        self.local_state = LocalState()
        
        # Ajanlar
        self.planner: Optional[PlannerAgent] = None
        self.researcher: Optional[ResearcherAgent] = None
        self.writer: Optional[WriterAgent] = None
        self.fact_checker: Optional[FactCheckerAgent] = None
        self.user_proxy: Optional[UserProxyAgent] = None
        self.synthesizer: Optional[SynthesizerAgent] = None
        
        # Görsel üretici
        self.visual_generator = VisualGenerator()
        
        # 🚀 Premium V2 Modüller
        self.dynamic_page_manager: Optional['DynamicPageManager'] = None
        self.multi_agent_debate: Optional['MultiAgentDebate'] = None
        self.realtime_streaming: Optional['RealTimeStreamingManager'] = None
        self.originality_checker: Optional['OriginalityChecker'] = None
        self.multilingual_engine: Optional['MultilingualResearchEngine'] = None
        self.analytics_engine: Optional['ResearchAnalyticsEngine'] = None
        self.literature_review: Optional['LiteratureReviewEngine'] = None
        
        # Event callback
        self._event_callback: Optional[Callable] = None
        
        # Pause/Resume state
        self._is_paused = False
        self._document_id: Optional[str] = None
    
    def set_event_callback(self, callback: Callable):
        """Event callback ayarla (WebSocket için)."""
        self._event_callback = callback
    
    def set_document_id(self, doc_id: str):
        """Döküman ID'sini ayarla (pause/resume için)."""
        self._document_id = doc_id
    
    @classmethod
    def pause_generation(cls, document_id: str) -> bool:
        """Üretimi duraklat."""
        cls._paused_states[document_id] = True
        return True
    
    @classmethod
    def resume_generation(cls, document_id: str) -> bool:
        """Üretimi devam ettir."""
        cls._paused_states[document_id] = False
        return True
    
    @classmethod
    def is_paused(cls, document_id: str) -> bool:
        """Duraklatılmış mı kontrol et."""
        return cls._paused_states.get(document_id, False)
    
    @classmethod
    def get_checkpoint(cls, document_id: str) -> Optional['GenerationCheckpoint']:
        """Checkpoint'i getir."""
        return cls._checkpoints.get(document_id)
    
    @classmethod
    def save_checkpoint(cls, checkpoint: 'GenerationCheckpoint'):
        """Checkpoint'i kaydet."""
        cls._checkpoints[checkpoint.document_id] = checkpoint
    
    @classmethod
    def delete_checkpoint(cls, document_id: str):
        """Checkpoint'i sil."""
        cls._checkpoints.pop(document_id, None)
        cls._paused_states.pop(document_id, None)
    
    async def _check_pause(self) -> bool:
        """Duraklatma kontrolü."""
        if self._document_id and self.is_paused(self._document_id):
            return True
        return False
    
    async def _emit_event(
        self, 
        event_type: EventType, 
        data: Dict[str, Any]
    ):
        """Event yayınla."""
        event = {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        
        if self._event_callback:
            await self._event_callback(event)
    
    async def generate_document(
        self,
        config: DeepScholarConfig
    ) -> AsyncGenerator[Dict, None]:
        """
        Döküman üretimi (ana akış).
        
        Yields:
            Progress events
        """
        try:
            # Global state'i başlat
            self.global_state = GlobalState(
                document_title=config.title,
                document_topic=config.topic,
                target_pages=config.page_count,
                language=config.language,
                citation_style=config.citation_style
            )
            
            # 🚀 Premium V2 Modüllerini Başlat
            if PREMIUM_ADVANCED_AVAILABLE:
                if config.enable_dynamic_pages:
                    self.dynamic_page_manager = DynamicPageManager(
                        base_page_count=config.page_count,
                        max_expansion=config.max_page_expansion
                    )
                
                if config.enable_realtime_streaming:
                    # target_sections = outline length (will be set after planning)
                    self.realtime_streaming = RealTimeStreamingManager(
                        target_pages=config.page_count,
                        target_sections=10  # Default, will be updated after outline
                    )
                
                if config.enable_originality_check:
                    self.originality_checker = OriginalityChecker()
                
                if config.enable_analytics:
                    self.analytics_engine = ResearchAnalyticsEngine()
            
            # Ajanları oluştur
            self.planner = PlannerAgent(self.global_state)
            self.researcher = ResearcherAgent(self.global_state)
            self.writer = WriterAgent(self.global_state)
            self.fact_checker = FactCheckerAgent(self.global_state)
            self.user_proxy = UserProxyAgent(self.global_state, config.user_persona)
            self.synthesizer = SynthesizerAgent(self.global_state)
            
            # ============ PHASE 1: PLANNING ============
            yield {
                "type": EventType.PHASE_START.value,
                "phase": "planning",
                "message": "📋 Döküman planlanıyor...",
                "progress": 5
            }
            
            yield {
                "type": EventType.AGENT_MESSAGE.value,
                "agent": AgentRole.PLANNER.value,
                "message": f"🧠 {config.page_count} sayfalık döküman için master outline oluşturuluyor..."
            }
            
            outline = await self.planner.create_master_outline(config)
            self.global_state.master_outline = outline
            
            yield {
                "type": EventType.PHASE_END.value,
                "phase": "planning",
                "message": f"✅ {len(outline)} bölümlük plan hazırlandı",
                "progress": 10,
                "data": {
                    "outline": [
                        {"id": s.id, "title": s.title, "level": s.level, "pages": f"{s.page_start}-{s.page_end}"}
                        for s in outline
                    ]
                }
            }
            
            # ============ PHASE 2: RESEARCH ============
            yield {
                "type": EventType.PHASE_START.value,
                "phase": "research",
                "message": "🔍 Araştırma yapılıyor...",
                "progress": 15
            }
            
            all_research: Dict[str, List[ResearchItem]] = {}
            total_sources = 0
            
            for i, section in enumerate(outline):
                yield {
                    "type": EventType.AGENT_MESSAGE.value,
                    "agent": AgentRole.RESEARCHER.value,
                    "message": f"🔎 Bölüm {i+1}/{len(outline)} araştırılıyor: {section.title}"
                }
                
                self.local_state.current_section = section
                research = await self.researcher.research_section(section, config, self.local_state)
                all_research[section.id] = research
                total_sources += len(research)
                
                yield {
                    "type": EventType.RESEARCH_FOUND.value,
                    "section": section.title,
                    "sources_count": len(research),
                    "sources": [
                        {"title": r.source_title, "type": r.source_type, "score": r.relevance_score}
                        for r in research[:5]
                    ]
                }
                
                # Fraktal genişleme kontrolü
                if config.max_research_depth > 1 and len(research) > 5:
                    claims = await self.researcher.extract_claims(research)
                    self.local_state.extracted_claims = claims
                    
                    if config.enable_conflict_detection:
                        conflicts = await self.researcher.detect_conflicts(claims)
                        self.local_state.detected_conflicts = conflicts
                        
                        if conflicts:
                            yield {
                                "type": EventType.CONFLICT_DETECTED.value,
                                "section": section.title,
                                "conflicts": conflicts
                            }
            
            yield {
                "type": EventType.PHASE_END.value,
                "phase": "research",
                "message": f"📚 Toplam {total_sources} kaynak bulundu",
                "progress": 30
            }
            
            # 🚀 Research Analytics (Premium V2)
            if PREMIUM_ADVANCED_AVAILABLE and config.enable_analytics and self.analytics_engine:
                yield {
                    "type": EventType.AGENT_THINKING.value,
                    "agent": "ResearchAnalytics",
                    "thought": "📊 Araştırma kalitesi analiz ediliyor..."
                }
                
                # Tüm kaynakları düz listeye çevir
                flat_sources = []
                for section_id, research_items in all_research.items():
                    for item in research_items:
                        flat_sources.append({
                            "id": item.id,
                            "title": item.source_title,
                            "type": item.source_type,
                            "content": item.content[:500] if item.content else "",
                            "keywords": [],
                            "year": 2024
                        })
                
                analytics_report = await self.analytics_engine.analyze_sources(
                    flat_sources, config.topic
                )
                
                yield {
                    "type": "research_analytics",
                    "quality_score": analytics_report.quality_score,
                    "diversity_score": round(analytics_report.source_metrics.diversity_score, 2),
                    "recency_score": round(analytics_report.source_metrics.recency_score, 2),
                    "topic_clusters": [c.name for c in analytics_report.topic_clusters[:5]],
                    "gaps": analytics_report.gaps_identified[:3],
                    "recommendations": analytics_report.recommendations[:3],
                    "message": f"📊 Araştırma kalitesi: {analytics_report.quality_score}/100"
                }
            
            # ============ PHASE 3: WRITING ============
            yield {
                "type": EventType.PHASE_START.value,
                "phase": "writing",
                "message": "✍️ İçerik yazılıyor...",
                "progress": 35
            }
            
            all_content = []
            all_citations = []
            
            for i, section in enumerate(outline):
                progress = 35 + int((i / len(outline)) * 45)
                
                yield {
                    "type": EventType.SECTION_START.value,
                    "section_index": i,
                    "section_title": section.title,
                    "progress": progress
                }
                
                yield {
                    "type": EventType.AGENT_MESSAGE.value,
                    "agent": AgentRole.WRITER.value,
                    "message": f"✏️ Yazılıyor: {section.title} ({section.word_target} kelime hedef)"
                }
                
                # Pause kontrolü
                if await self._check_pause():
                    # Checkpoint kaydet
                    checkpoint = GenerationCheckpoint(
                        document_id=self._document_id or "",
                        config={
                            "title": config.title,
                            "topic": config.topic,
                            "page_count": config.page_count,
                            "language": config.language.value,
                            "citation_style": config.citation_style.value,
                            "style": config.style
                        },
                        progress=progress,
                        current_phase="writing",
                        completed_sections=[
                            {"id": c["section_id"], "title": c["title"], "content": c["content"]}
                            for c in all_content
                        ],
                        pending_sections=[
                            {"id": s.id, "title": s.title}
                            for s in outline[i:]
                        ],
                        all_research={
                            k: [{"id": r.id, "content": r.content, "source_title": r.source_title}
                                for r in v]
                            for k, v in all_research.items()
                        },
                        global_state={
                            "completed_sections": dict(self.global_state.completed_sections),
                            "section_summaries": dict(self.global_state.section_summaries)
                        }
                    )
                    self.save_checkpoint(checkpoint)
                    
                    yield {
                        "type": EventType.PAUSED.value,
                        "message": "⏸️ Üretim duraklatıldı. Kaldığınız yerden devam edebilirsiniz.",
                        "progress": progress,
                        "checkpoint_id": self._document_id,
                        "completed_sections": len(all_content),
                        "pending_sections": len(outline) - i
                    }
                    
                    # Pause döngüsü - resume bekle
                    while await self._check_pause():
                        await asyncio.sleep(1)
                    
                    yield {
                        "type": EventType.RESUMED.value,
                        "message": "▶️ Üretim devam ediyor...",
                        "progress": progress
                    }
                
                # Local state güncelle
                self.local_state.current_section = section
                self.local_state.current_sources = all_research.get(section.id, [])
                
                if i > 0:
                    prev_section = outline[i-1]
                    self.local_state.previous_section_summary = self.global_state.section_summaries.get(
                        prev_section.id, ""
                    )
                
                # Yazım
                content, citations = await self.writer.write_section(
                    section, 
                    self.local_state.current_sources,
                    self.local_state,
                    config
                )
                
                # Görsel üretimi (Premium)
                visuals = []
                if config.enable_visuals:
                    yield {
                        "type": EventType.AGENT_MESSAGE.value,
                        "agent": AgentRole.SYNTHESIZER.value,
                        "message": f"🎨 Görseller üretiliyor: {section.title}"
                    }
                    
                    visuals = await self.visual_generator.generate_visuals_for_section(
                        section.title,
                        content,
                        config.topic,
                        config
                    )
                    
                    for visual in visuals:
                        yield {
                            "type": EventType.VISUAL_GENERATED.value,
                            "section": section.title,
                            "visual_type": visual.get("type"),
                            "visual_title": visual.get("title"),
                            "visual": visual
                        }
                    
                    # Görselleri içeriğe ekle
                    if visuals:
                        content = self._integrate_visuals(content, visuals)
                
                all_content.append({
                    "section_id": section.id,
                    "title": section.title,
                    "level": section.level,
                    "content": content,
                    "word_count": len(content.split()),
                    "visuals": visuals
                })
                all_citations.extend(citations)
                
                # Global state güncelle
                self.global_state.completed_sections[section.id] = content
                
                # Özet oluştur (sonraki bölüm için)
                summary_prompt = f"Bu içeriği 2-3 cümleyle özetle:\n{content[:1000]}"
                summary = await self.writer._llm_generate(summary_prompt, temperature=0.3)
                self.global_state.section_summaries[section.id] = summary[:300]
                
                # Fact check (opsiyonel)
                if config.enable_fact_checking:
                    yield {
                        "type": EventType.AGENT_MESSAGE.value,
                        "agent": AgentRole.FACT_CHECKER.value,
                        "message": f"🔍 Doğrulama: {section.title}"
                    }
                    
                    verification = await self.fact_checker.verify_content(
                        content, 
                        self.local_state.current_sources
                    )
                    
                    yield {
                        "type": EventType.FACT_CHECK.value,
                        "section": section.title,
                        "score": verification.get("overall_score", 0.7),
                        "verified_count": len(verification.get("verified_claims", [])),
                        "unverified_count": len(verification.get("unverified_claims", []))
                    }
                
                # User proxy review (opsiyonel)
                if config.enable_user_proxy:
                    yield {
                        "type": EventType.AGENT_MESSAGE.value,
                        "agent": AgentRole.USER_PROXY.value,
                        "message": f"👤 Okuyucu değerlendirmesi: {section.title}"
                    }
                    
                    review = await self.user_proxy.review_content(content, config)
                    
                    yield {
                        "type": EventType.USER_PROXY_FEEDBACK.value,
                        "section": section.title,
                        "clarity": review.get("clarity_score", 7),
                        "issues": review.get("issues", [])
                    }
                
                # 🚀 Originality Check (Premium V2)
                if PREMIUM_ADVANCED_AVAILABLE and config.enable_originality_check and self.originality_checker:
                    yield {
                        "type": EventType.AGENT_THINKING.value,
                        "agent": "OriginalityChecker",
                        "thought": f"📝 Orijinallik kontrolü yapılıyor: {section.title}"
                    }
                    
                    # Kaynak metinleri al
                    source_texts = [
                        r.content for r in self.local_state.current_sources
                        if r.content
                    ]
                    
                    originality_report = await self.originality_checker.check_originality(
                        content, source_texts
                    )
                    
                    yield {
                        "type": "originality_check",
                        "section": section.title,
                        "originality_score": originality_report.originality_score,
                        "similarity_index": originality_report.similarity_index,
                        "unique_phrases_ratio": originality_report.unique_phrases_ratio,
                        "citation_count": len(originality_report.cited_passages),
                        "message": f"📊 Orijinallik: {originality_report.originality_score:.0%}"
                    }
                
                yield {
                    "type": EventType.SECTION_COMPLETE.value,
                    "section_index": i,
                    "section_title": section.title,
                    "section_level": section.level,
                    "visuals": visuals,
                    "word_count": len(content.split()),
                    "content": content,  # Full content for live preview
                    "content_preview": content[:500] + "..." if len(content) > 500 else content,
                    "progress": progress + 5
                }
                
                # Local state temizle
                self.local_state.clear()
            
            yield {
                "type": EventType.PHASE_END.value,
                "phase": "writing",
                "message": "✅ İçerik yazımı tamamlandı",
                "progress": 85
            }
            
            # ============ PHASE 4: BIBLIOGRAPHY ============
            yield {
                "type": EventType.PHASE_START.value,
                "phase": "bibliography",
                "message": "📖 Kaynakça oluşturuluyor...",
                "progress": 88
            }
            
            bibliography = self._create_bibliography(config)
            
            yield {
                "type": EventType.PHASE_END.value,
                "phase": "bibliography",
                "message": f"📚 {len(self.global_state.all_citations)} kaynak listelendi",
                "progress": 92
            }
            
            # ============ PHASE 5: FINALIZE ============
            yield {
                "type": EventType.PHASE_START.value,
                "phase": "finalize",
                "message": "🔧 Döküman birleştiriliyor...",
                "progress": 94
            }
            
            # Final döküman
            final_content = self._combine_content(all_content, bibliography, config)
            
            yield {
                "type": EventType.COMPLETE.value,
                "message": "🎉 Döküman başarıyla oluşturuldu!",
                "progress": 100,
                "document": {
                    "title": config.title,
                    "content": final_content,
                    "word_count": len(final_content.split()),
                    "page_count": config.page_count,
                    "citations_count": len(self.global_state.all_citations),
                    "sections": [
                        {"id": s.id, "title": s.title}
                        for s in outline
                    ]
                }
            }
            
        except Exception as e:
            yield {
                "type": EventType.ERROR.value,
                "message": f"❌ Hata: {str(e)}",
                "error": str(e),
                "trace": traceback.format_exc()
            }
    
    def _create_bibliography(self, config: DeepScholarConfig) -> str:
        """Akademik kaynakça oluştur."""
        
        if not self.global_state.all_citations:
            return ""
        
        lang_headers = {
            DocumentLanguage.TURKISH: "KAYNAKÇA",
            DocumentLanguage.ENGLISH: "REFERENCES",
            DocumentLanguage.GERMAN: "LITERATURVERZEICHNIS"
        }
        
        bibliography = f"\n\n---\n\n# 📚 {lang_headers.get(config.language, 'KAYNAKÇA')}\n\n"
        
        # Kaynak tipine göre grupla
        web_sources = []
        academic_sources = []
        local_sources = []
        
        for citation in self.global_state.all_citations.values():
            if citation.source_type == "academic":
                academic_sources.append(citation)
            elif citation.source_type == "web":
                web_sources.append(citation)
            else:
                local_sources.append(citation)
        
        # Akademik kaynaklar
        if academic_sources:
            bibliography += "## Akademik Kaynaklar\n\n"
            for i, c in enumerate(academic_sources, 1):
                if config.citation_style == CitationStyle.APA:
                    bibliography += f"[{i}] {c.to_apa()}\n\n"
                elif config.citation_style == CitationStyle.IEEE:
                    bibliography += f"[{i}] {c.to_ieee()}\n\n"
                else:
                    bibliography += f"[{i}] {c.to_chicago()}\n\n"
        
        # Web kaynakları
        if web_sources:
            bibliography += "## Web Kaynakları\n\n"
            for i, c in enumerate(web_sources, len(academic_sources) + 1):
                date = c.access_date or datetime.now().strftime("%Y-%m-%d")
                bibliography += f"[{i}] {c.title}. Erişim: {c.url} ({date})\n\n"
        
        # Yerel kaynaklar
        if local_sources:
            bibliography += "## Yerel Dökümanlar\n\n"
            for i, c in enumerate(local_sources, len(academic_sources) + len(web_sources) + 1):
                bibliography += f"[{i}] {c.title}\n\n"
        
        return bibliography
    
    def _combine_content(
        self, 
        sections: List[Dict], 
        bibliography: str,
        config: DeepScholarConfig
    ) -> str:
        """Tüm içeriği birleştir."""
        
        # Başlık sayfası
        lang_headers = {
            DocumentLanguage.TURKISH: {"title": "ARAŞTIRMA DÖKÜMANI", "topic": "Konu", "date": "Tarih", "pages": "Sayfa"},
            DocumentLanguage.ENGLISH: {"title": "RESEARCH DOCUMENT", "topic": "Topic", "date": "Date", "pages": "Pages"},
            DocumentLanguage.GERMAN: {"title": "FORSCHUNGSDOKUMENT", "topic": "Thema", "date": "Datum", "pages": "Seiten"}
        }
        
        headers = lang_headers.get(config.language, lang_headers[DocumentLanguage.TURKISH])
        
        content = f"""# {config.title}

**{headers['topic']}:** {config.topic}
**{headers['date']}:** {datetime.now().strftime('%Y-%m-%d')}
**{headers['pages']}:** {config.page_count}

---

"""
        
        # İçindekiler
        content += "## 📑 İÇİNDEKİLER\n\n"
        for section in sections:
            indent = "  " * (section.get("level", 1) - 1)
            content += f"{indent}- [{section['title']}](#{section['section_id']})\n"
        content += "\n---\n\n"
        
        # Bölümler
        for section in sections:
            content += section['content'] + "\n\n---\n\n"
        
        # Kaynakça
        content += bibliography
        
        return content
    
    def _integrate_visuals(self, content: str, visuals: List[Dict[str, Any]]) -> str:
        """Görselleri içeriğe entegre et."""
        if not visuals:
            return content
        
        visual_section = "\n\n---\n\n### 📊 Görseller ve Diyagramlar\n\n"
        
        for visual in visuals:
            visual_type = visual.get("type", "")
            title = visual.get("title", "Görsel")
            render_type = visual.get("render_type", "")
            
            visual_section += f"#### {title}\n\n"
            
            if render_type == "mermaid":
                code = visual.get("code", "")
                visual_section += f"```mermaid\n{code}\n```\n\n"
            
            elif render_type == "markdown":
                code = visual.get("code", "")
                visual_section += f"{code}\n\n"
            
            elif render_type == "latex":
                code = visual.get("code", "")
                visual_section += f"{code}\n\n"
            
            elif render_type == "code":
                code = visual.get("code", "")
                visual_section += f"{code}\n\n"
            
            elif render_type == "statistics":
                data = visual.get("data", {})
                stats = data.get("stats", [])
                highlight = data.get("highlight", "")
                
                if stats:
                    visual_section += "| Metrik | Değer | Trend |\n|--------|-------|-------|\n"
                    for stat in stats:
                        icon = stat.get("icon", "📊")
                        label = stat.get("label", "")
                        value = stat.get("value", "")
                        trend = stat.get("trend", "")
                        trend_icon = "📈" if trend == "up" else "📉" if trend == "down" else "➡️"
                        visual_section += f"| {icon} {label} | **{value}** | {trend_icon} |\n"
                    visual_section += "\n"
                
                if highlight:
                    visual_section += f"> 💡 **Önemli:** {highlight}\n\n"
            
            visual_section += "\n"
        
        # İçeriğin sonuna ekle
        return content + visual_section


# ============================================================================
# PDF EXPORT
# ============================================================================

class PDFExporter:
    """PDF export işlemleri."""
    
    @staticmethod
    async def export_to_pdf(
        content: str,
        title: str,
        output_path: str
    ) -> bool:
        """Markdown içeriği PDF'e çevir."""
        try:
            # WeasyPrint veya pdfkit kullan
            import markdown
            
            # Markdown -> HTML
            html_content = markdown.markdown(
                content,
                extensions=['tables', 'fenced_code', 'toc']
            )
            
            # HTML şablonu
            html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        blockquote {{ border-left: 3px solid #3498db; margin-left: 0; padding-left: 20px; color: #555; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f4f4f4; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
            
            # PDF oluştur (pdfkit kullan)
            try:
                import pdfkit
                pdfkit.from_string(html_template, output_path)
                return True
            except ImportError:
                # Alternatif: HTML olarak kaydet
                html_path = output_path.replace('.pdf', '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_template)
                print(f"PDF export için pdfkit gerekli. HTML olarak kaydedildi: {html_path}")
                return False
                
        except Exception as e:
            print(f"[PDF Export Error] {e}")
            return False


# ============================================================================
# SINGLETON
# ============================================================================

deep_scholar = DeepScholarOrchestrator()
