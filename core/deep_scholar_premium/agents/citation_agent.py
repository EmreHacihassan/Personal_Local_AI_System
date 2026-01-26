"""
CitationAgent - Premium Atıf Yönetim Ajanı
==========================================

Görevler:
1. Akıllı inline atıf yerleştirme
2. Kaynak doğrulama ve metadata zenginleştirme
3. Çoklu atıf stili desteği (APA, IEEE, Chicago, Harvard, MLA)
4. Atıf tutarlılık kontrolü
5. Kaynakça otomatik oluşturma
6. DOI/ISBN çözümleme
7. Atıf grafiği analizi
"""

import asyncio
import json
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.llm_manager import llm_manager


class CitationStyle(str, Enum):
    """Atıf stilleri."""
    APA = "apa"           # APA 7th Edition
    IEEE = "ieee"         # IEEE
    CHICAGO = "chicago"   # Chicago
    HARVARD = "harvard"   # Harvard
    MLA = "mla"           # MLA 9th Edition
    VANCOUVER = "vancouver"  # Vancouver


class SourceType(str, Enum):
    """Kaynak türleri."""
    JOURNAL_ARTICLE = "journal_article"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    CONFERENCE_PAPER = "conference_paper"
    THESIS = "thesis"
    WEBSITE = "website"
    REPORT = "report"
    PATENT = "patent"
    PREPRINT = "preprint"
    NEWS_ARTICLE = "news_article"


@dataclass
class Citation:
    """Atıf bilgisi."""
    id: str
    source_type: SourceType
    title: str
    authors: List[str]
    year: Optional[int]
    
    # Opsiyonel alanlar
    journal: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    access_date: Optional[str] = None
    
    # Kullanım bilgisi
    inline_references: List[Dict[str, Any]] = field(default_factory=list)
    relevance_score: float = 0.0
    verified: bool = False
    
    def to_apa(self) -> str:
        """APA 7th formatında."""
        authors_str = self._format_authors_apa()
        year_str = f"({self.year})" if self.year else "(n.d.)"
        
        if self.source_type == SourceType.JOURNAL_ARTICLE:
            return f"{authors_str} {year_str}. {self.title}. *{self.journal or 'Unknown'}*, {self.volume or ''}({self.issue or ''}), {self.pages or ''}. {f'https://doi.org/{self.doi}' if self.doi else ''}"
        elif self.source_type == SourceType.BOOK:
            return f"{authors_str} {year_str}. *{self.title}*. {self.publisher or ''}."
        elif self.source_type == SourceType.WEBSITE:
            return f"{authors_str} {year_str}. {self.title}. Retrieved {self.access_date or 'n.d.'} from {self.url or ''}"
        else:
            return f"{authors_str} {year_str}. {self.title}."
    
    def to_ieee(self) -> str:
        """IEEE formatında."""
        authors_str = self._format_authors_ieee()
        
        if self.source_type == SourceType.JOURNAL_ARTICLE:
            return f'{authors_str}, "{self.title}," *{self.journal or "Unknown"}*, vol. {self.volume or ""}, no. {self.issue or ""}, pp. {self.pages or ""}, {self.year or "n.d."}.'
        elif self.source_type == SourceType.BOOK:
            return f'{authors_str}, *{self.title}*. {self.publisher or ""}, {self.year or "n.d."}.'
        else:
            return f'{authors_str}, "{self.title}," {self.year or "n.d."}.'
    
    def to_chicago(self) -> str:
        """Chicago formatında."""
        authors_str = self._format_authors_chicago()
        
        if self.source_type == SourceType.JOURNAL_ARTICLE:
            return f'{authors_str}. "{self.title}." *{self.journal or "Unknown"}* {self.volume or ""}{"." + self.issue if self.issue else ""} ({self.year or "n.d."}): {self.pages or ""}.'
        elif self.source_type == SourceType.BOOK:
            return f'{authors_str}. *{self.title}*. {self.publisher or ""}, {self.year or "n.d."}.'
        else:
            return f'{authors_str}. "{self.title}." {self.year or "n.d."}.'
    
    def to_harvard(self) -> str:
        """Harvard formatında."""
        authors_str = self._format_authors_harvard()
        year_str = f"({self.year})" if self.year else "(n.d.)"
        
        if self.source_type == SourceType.JOURNAL_ARTICLE:
            return f"{authors_str} {year_str} '{self.title}', *{self.journal or 'Unknown'}*, vol. {self.volume or ''}, no. {self.issue or ''}, pp. {self.pages or ''}."
        elif self.source_type == SourceType.BOOK:
            return f"{authors_str} {year_str} *{self.title}*, {self.publisher or ''}."
        else:
            return f"{authors_str} {year_str} '{self.title}'."
    
    def _format_authors_apa(self) -> str:
        """APA yazar formatı."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) == 1:
            return self.authors[0]
        elif len(self.authors) == 2:
            return f"{self.authors[0]} & {self.authors[1]}"
        elif len(self.authors) <= 20:
            return ", ".join(self.authors[:-1]) + f", & {self.authors[-1]}"
        else:
            return ", ".join(self.authors[:19]) + ", ... " + self.authors[-1]
    
    def _format_authors_ieee(self) -> str:
        """IEEE yazar formatı."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) <= 3:
            return " and ".join(self.authors)
        else:
            return self.authors[0] + " et al."
    
    def _format_authors_chicago(self) -> str:
        """Chicago yazar formatı."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) == 1:
            return self.authors[0]
        elif len(self.authors) <= 3:
            return ", ".join(self.authors[:-1]) + ", and " + self.authors[-1]
        else:
            return self.authors[0] + " et al."
    
    def _format_authors_harvard(self) -> str:
        """Harvard yazar formatı."""
        if not self.authors:
            return "Unknown"
        if len(self.authors) == 1:
            return self.authors[0]
        elif len(self.authors) == 2:
            return f"{self.authors[0]} and {self.authors[1]}"
        else:
            return self.authors[0] + " et al."
    
    def get_inline_citation(self, style: CitationStyle, citation_number: int = 1) -> str:
        """Inline atıf formatı."""
        if style == CitationStyle.APA:
            if len(self.authors) == 1:
                return f"({self.authors[0].split()[-1]}, {self.year or 'n.d.'})"
            elif len(self.authors) == 2:
                return f"({self.authors[0].split()[-1]} & {self.authors[1].split()[-1]}, {self.year or 'n.d.'})"
            else:
                return f"({self.authors[0].split()[-1]} et al., {self.year or 'n.d.'})"
        elif style == CitationStyle.IEEE:
            return f"[{citation_number}]"
        elif style == CitationStyle.CHICAGO:
            return f"({self.authors[0].split()[-1] if self.authors else 'Unknown'} {self.year or 'n.d.'})"
        elif style == CitationStyle.HARVARD:
            if len(self.authors) == 1:
                return f"({self.authors[0].split()[-1]}, {self.year or 'n.d.'})"
            else:
                return f"({self.authors[0].split()[-1]} et al., {self.year or 'n.d.'})"
        else:
            return f"[{citation_number}]"


@dataclass
class CitationPlacement:
    """Atıf yerleştirme önerisi."""
    sentence: str
    suggested_position: int  # Karakterin pozisyonu
    citation_id: str
    confidence: float
    reason: str


@dataclass
class Bibliography:
    """Kaynakça."""
    citations: List[Citation]
    style: CitationStyle
    formatted_entries: List[str]
    
    def to_markdown(self) -> str:
        """Markdown formatında kaynakça."""
        lines = ["# Kaynakça", ""]
        for i, entry in enumerate(self.formatted_entries, 1):
            lines.append(f"{i}. {entry}")
        return "\n".join(lines)
    
    def to_html(self) -> str:
        """HTML formatında kaynakça."""
        lines = ["<div class='bibliography'>", "<h2>Kaynakça</h2>", "<ol>"]
        for entry in self.formatted_entries:
            lines.append(f"<li>{entry}</li>")
        lines.extend(["</ol>", "</div>"])
        return "\n".join(lines)


class CitationAgent:
    """
    Premium Atıf Yönetim Ajanı
    
    Akıllı atıf yerleştirme ve kaynakça yönetimi.
    """
    
    def __init__(self, global_state: Optional[Any] = None):
        self.global_state = global_state
        self.citations: Dict[str, Citation] = {}
        self.default_style = CitationStyle.APA
    
    async def analyze_content_for_citations(
        self,
        content: str,
        sources: List[Dict[str, Any]]
    ) -> List[CitationPlacement]:
        """
        İçeriği analiz edip atıf yerleştirme önerileri sun.
        
        Args:
            content: Doküman içeriği
            sources: Mevcut kaynaklar
            
        Returns:
            Atıf yerleştirme önerileri
        """
        prompt = f"""Aşağıdaki içerikte hangi cümlelere atıf eklenmesi gerektiğini belirle.

## İçerik:
{content[:3000]}

## Mevcut Kaynaklar:
{json.dumps([{'id': s.get('id', ''), 'title': s.get('title', '')} for s in sources[:10]], ensure_ascii=False)}

## Atıf Gerektiren Durumlar:
1. İstatistiksel veriler
2. Başkalarının fikirleri
3. Tanımlar ve kavramlar
4. Araştırma bulguları
5. Özel iddialar

## Yanıt Formatı (JSON Array):
[
    {{
        "sentence": "<atıf gerektiren cümle>",
        "suggested_source_id": "<uygun kaynak id>",
        "confidence": <0.0-1.0>,
        "reason": "<neden atıf gerekli>"
    }}
]"""

        response = await self._llm_call(prompt)
        
        placements = []
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
                for item in data:
                    placements.append(CitationPlacement(
                        sentence=item.get("sentence", ""),
                        suggested_position=content.find(item.get("sentence", "")[:50]),
                        citation_id=item.get("suggested_source_id", ""),
                        confidence=float(item.get("confidence", 0.5)),
                        reason=item.get("reason", "")
                    ))
        except:
            pass
        
        return placements
    
    async def insert_citations(
        self,
        content: str,
        placements: List[CitationPlacement],
        style: CitationStyle = CitationStyle.APA
    ) -> str:
        """
        Atıfları içeriğe yerleştir.
        
        Args:
            content: Orijinal içerik
            placements: Yerleştirme önerileri
            style: Atıf stili
            
        Returns:
            Atıflı içerik
        """
        cited_content = content
        
        # Pozisyona göre ters sırala (sondan başa)
        sorted_placements = sorted(placements, key=lambda x: x.suggested_position, reverse=True)
        
        for i, placement in enumerate(sorted_placements, 1):
            if placement.citation_id in self.citations:
                citation = self.citations[placement.citation_id]
                inline_cite = citation.get_inline_citation(style, i)
                
                # Cümle sonuna atıf ekle
                sentence_end = content.find(placement.sentence) + len(placement.sentence)
                if sentence_end > 0 and sentence_end <= len(cited_content):
                    # Nokta öncesine ekle
                    if cited_content[sentence_end-1] == '.':
                        cited_content = cited_content[:sentence_end-1] + f" {inline_cite}." + cited_content[sentence_end:]
                    else:
                        cited_content = cited_content[:sentence_end] + f" {inline_cite}" + cited_content[sentence_end:]
        
        return cited_content
    
    async def generate_bibliography(
        self,
        style: CitationStyle = CitationStyle.APA
    ) -> Bibliography:
        """
        Kaynakça oluştur.
        
        Args:
            style: Kaynakça stili
            
        Returns:
            Formatlanmış kaynakça
        """
        formatted_entries = []
        
        # Sıralama: yazara göre alfabetik (APA, Chicago, Harvard) veya numaraya göre (IEEE)
        sorted_citations = sorted(
            self.citations.values(),
            key=lambda x: (x.authors[0] if x.authors else "ZZZ", x.year or 9999)
        )
        
        for citation in sorted_citations:
            if style == CitationStyle.APA:
                formatted_entries.append(citation.to_apa())
            elif style == CitationStyle.IEEE:
                formatted_entries.append(citation.to_ieee())
            elif style == CitationStyle.CHICAGO:
                formatted_entries.append(citation.to_chicago())
            elif style == CitationStyle.HARVARD:
                formatted_entries.append(citation.to_harvard())
            else:
                formatted_entries.append(citation.to_apa())
        
        return Bibliography(
            citations=list(sorted_citations),
            style=style,
            formatted_entries=formatted_entries
        )
    
    async def verify_citation(
        self,
        citation: Citation
    ) -> Dict[str, Any]:
        """
        Atıfı doğrula (DOI/ISBN kontrolü).
        
        Args:
            citation: Doğrulanacak atıf
            
        Returns:
            Doğrulama sonucu
        """
        result = {
            "verified": False,
            "method": None,
            "metadata": {},
            "issues": []
        }
        
        # DOI kontrolü
        if citation.doi:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = f"https://api.crossref.org/works/{citation.doi}"
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            result["verified"] = True
                            result["method"] = "DOI"
                            result["metadata"] = {
                                "title": data.get("message", {}).get("title", [None])[0],
                                "authors": [a.get("given", "") + " " + a.get("family", "") 
                                          for a in data.get("message", {}).get("author", [])]
                            }
            except:
                result["issues"].append("DOI doğrulanamadı")
        
        # Temel kontroller
        if not citation.authors:
            result["issues"].append("Yazar bilgisi eksik")
        if not citation.year:
            result["issues"].append("Yıl bilgisi eksik")
        if not citation.title:
            result["issues"].append("Başlık eksik")
        
        if not result["issues"]:
            result["verified"] = True
            result["method"] = "Basic validation"
        
        return result
    
    async def check_citation_consistency(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Atıf tutarlılığını kontrol et.
        
        Args:
            content: Doküman içeriği
            
        Returns:
            Tutarlılık raporu
        """
        # Inline atıfları bul
        apa_pattern = r'\([A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+(?:&|ve)\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)?(?:\s+et\s+al\.)?,?\s*\d{4}[a-z]?\)'
        ieee_pattern = r'\[\d+(?:,\s*\d+)*\]'
        
        apa_matches = re.findall(apa_pattern, content)
        ieee_matches = re.findall(ieee_pattern, content)
        
        mixed_styles = len(apa_matches) > 0 and len(ieee_matches) > 0
        
        # Eksik kaynakça kontulü
        cited_in_text = set()
        for match in apa_matches:
            # Yazar adını çıkar
            author = re.search(r'\(([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)', match)
            if author:
                cited_in_text.add(author.group(1))
        
        return {
            "total_inline_citations": len(apa_matches) + len(ieee_matches),
            "apa_citations": len(apa_matches),
            "ieee_citations": len(ieee_matches),
            "mixed_styles": mixed_styles,
            "style_recommendation": "APA" if len(apa_matches) >= len(ieee_matches) else "IEEE",
            "issues": ["Karışık atıf stilleri tespit edildi"] if mixed_styles else [],
            "cited_authors": list(cited_in_text)
        }
    
    def add_citation(self, citation: Citation) -> str:
        """Atıf ekle."""
        citation_id = hashlib.md5(
            f"{citation.title}{citation.year}".encode()
        ).hexdigest()[:12]
        citation.id = citation_id
        self.citations[citation_id] = citation
        return citation_id
    
    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Atıf getir."""
        return self.citations.get(citation_id)
    
    async def _llm_call(self, prompt: str, timeout: int = 300) -> str:
        """LLM çağrısı yap."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_manager.chat,
                    messages=messages,
                    model_type="default"
                ),
                timeout=timeout
            )
            return response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
