"""
SourceVerifier - Kaynak Doğrulama Modülü
========================================

Görevler:
1. DOI çözümleme ve doğrulama
2. ISBN doğrulama
3. URL erişilebilirlik kontrolü
4. Kaynak metadata doğrulama
5. Tam metin erişim kontrolü
6. Yazar ORCID doğrulama
"""

import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

try:
    import aiohttp
except ImportError:
    aiohttp = None


class VerificationStatus(str, Enum):
    """Doğrulama durumu."""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    ERROR = "error"


class AccessStatus(str, Enum):
    """Erişim durumu."""
    OPEN_ACCESS = "open_access"
    SUBSCRIPTION_REQUIRED = "subscription_required"
    EMBARGOED = "embargoed"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class DOIInfo:
    """DOI bilgisi."""
    doi: str
    valid: bool
    
    # Metadata
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    publisher: Optional[str] = None
    publication_date: Optional[str] = None
    journal: Optional[str] = None
    
    # Linkler
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    
    # Erişim
    access_status: AccessStatus = AccessStatus.UNKNOWN
    license: Optional[str] = None


@dataclass
class ISBNInfo:
    """ISBN bilgisi."""
    isbn: str
    valid: bool
    isbn10: Optional[str] = None
    isbn13: Optional[str] = None
    
    # Kitap bilgileri
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    
    # Diğer
    cover_url: Optional[str] = None
    page_count: Optional[int] = None


@dataclass
class URLStatus:
    """URL durumu."""
    url: str
    accessible: bool
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    is_pdf: bool = False
    is_html: bool = False
    requires_login: bool = False
    error_message: Optional[str] = None


@dataclass
class VerificationResult:
    """Doğrulama sonucu."""
    status: VerificationStatus
    confidence: float  # 0-1
    
    # Detaylar
    doi_info: Optional[DOIInfo] = None
    isbn_info: Optional[ISBNInfo] = None
    url_status: Optional[URLStatus] = None
    orcid_verified: bool = False
    
    # Metadata eşleşme
    title_match: bool = True
    author_match: bool = True
    year_match: bool = True
    
    # Mesajlar
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "confidence": round(self.confidence, 2),
            "title_match": self.title_match,
            "author_match": self.author_match,
            "year_match": self.year_match,
            "messages": self.messages,
            "warnings": self.warnings
        }


class SourceVerifier:
    """
    Kaynak Doğrulama Modülü
    
    Akademik kaynakların doğruluğunu ve erişilebilirliğini kontrol eder.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # API endpoints
        self.doi_api = "https://api.crossref.org/works"
        self.openlibrary_api = "https://openlibrary.org/api/books"
        self.unpaywall_api = "https://api.unpaywall.org/v2"
    
    async def verify_source(
        self,
        title: str,
        authors: List[str],
        year: Optional[int] = None,
        doi: Optional[str] = None,
        isbn: Optional[str] = None,
        url: Optional[str] = None
    ) -> VerificationResult:
        """
        Kaynağı kapsamlı doğrula.
        
        Args:
            title: Makale/kitap başlığı
            authors: Yazarlar
            year: Yayın yılı
            doi: DOI (varsa)
            isbn: ISBN (varsa)
            url: URL (varsa)
            
        Returns:
            Doğrulama sonucu
        """
        result = VerificationResult(
            status=VerificationStatus.UNVERIFIED,
            confidence=0.0,
            messages=[],
            warnings=[]
        )
        
        confidence_points = 0.0
        max_points = 0.0
        
        # DOI doğrulama
        if doi:
            max_points += 40
            doi_info = await self.verify_doi(doi)
            result.doi_info = doi_info
            
            if doi_info.valid:
                confidence_points += 20
                result.messages.append(f"DOI doğrulandı: {doi}")
                
                # Başlık eşleşmesi
                if doi_info.title:
                    title_match = self._match_title(title, doi_info.title)
                    result.title_match = title_match
                    if title_match:
                        confidence_points += 10
                    else:
                        result.warnings.append("Başlık DOI kaydıyla tam eşleşmiyor")
                
                # Yazar eşleşmesi
                if doi_info.authors and authors:
                    author_match = self._match_authors(authors, doi_info.authors)
                    result.author_match = author_match
                    if author_match:
                        confidence_points += 10
                    else:
                        result.warnings.append("Yazarlar DOI kaydıyla tam eşleşmiyor")
            else:
                result.warnings.append(f"DOI bulunamadı veya geçersiz: {doi}")
        
        # ISBN doğrulama (kitaplar için)
        if isbn:
            max_points += 30
            isbn_info = await self.verify_isbn(isbn)
            result.isbn_info = isbn_info
            
            if isbn_info.valid:
                confidence_points += 15
                result.messages.append(f"ISBN doğrulandı: {isbn}")
                
                if isbn_info.title:
                    title_match = self._match_title(title, isbn_info.title)
                    if title_match:
                        confidence_points += 15
                    else:
                        result.warnings.append("Başlık ISBN kaydıyla tam eşleşmiyor")
            else:
                result.warnings.append(f"ISBN doğrulanamadı: {isbn}")
        
        # URL erişilebilirlik
        if url:
            max_points += 20
            url_status = await self.check_url(url)
            result.url_status = url_status
            
            if url_status.accessible:
                confidence_points += 10
                result.messages.append("URL erişilebilir")
                
                if url_status.is_pdf:
                    confidence_points += 10
                    result.messages.append("PDF mevcut")
            else:
                result.warnings.append(f"URL erişilebilir değil: {url_status.error_message}")
        
        # Baz puan (tanımlayıcı yoksa)
        if max_points == 0:
            max_points = 100
            confidence_points = 30  # Sadece metadata ile düşük güven
            result.warnings.append("DOI, ISBN veya URL bilgisi eksik - kaynak tam doğrulanamadı")
        
        # Sonuç hesapla
        result.confidence = confidence_points / max_points if max_points > 0 else 0
        
        if result.confidence >= 0.8:
            result.status = VerificationStatus.VERIFIED
        elif result.confidence >= 0.5:
            result.status = VerificationStatus.PARTIALLY_VERIFIED
        else:
            result.status = VerificationStatus.UNVERIFIED
        
        return result
    
    async def verify_doi(self, doi: str) -> DOIInfo:
        """
        DOI doğrula.
        
        Args:
            doi: DOI numarası
            
        Returns:
            DOI bilgisi
        """
        # DOI formatını temizle
        cleaned_doi = self._clean_doi(doi)
        
        if not self._validate_doi_format(cleaned_doi):
            return DOIInfo(doi=doi, valid=False)
        
        info = DOIInfo(doi=cleaned_doi, valid=False)
        
        if not aiohttp:
            return info
        
        try:
            async with aiohttp.ClientSession() as session:
                # CrossRef API
                url = f"{self.doi_api}/{cleaned_doi}"
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = data.get("message", {})
                        
                        info.valid = True
                        info.title = message.get("title", [None])[0]
                        info.authors = [
                            f"{a.get('given', '')} {a.get('family', '')}".strip()
                            for a in message.get("author", [])
                        ]
                        info.publisher = message.get("publisher")
                        info.journal = message.get("container-title", [None])[0]
                        info.url = message.get("URL")
                        
                        # Yayın tarihi
                        date_parts = message.get("published-print", {}).get("date-parts", [[]])
                        if date_parts and date_parts[0]:
                            info.publication_date = "-".join(str(x) for x in date_parts[0] if x)
                        
                        # Unpaywall ile open access kontrolü
                        info = await self._check_open_access(info)
        except Exception as e:
            info.valid = False
        
        return info
    
    async def verify_isbn(self, isbn: str) -> ISBNInfo:
        """
        ISBN doğrula.
        
        Args:
            isbn: ISBN numarası
            
        Returns:
            ISBN bilgisi
        """
        # ISBN temizle
        cleaned_isbn = re.sub(r'[^0-9X]', '', isbn.upper())
        
        # Format kontrolü
        if len(cleaned_isbn) == 10:
            valid = self._validate_isbn10(cleaned_isbn)
        elif len(cleaned_isbn) == 13:
            valid = self._validate_isbn13(cleaned_isbn)
        else:
            return ISBNInfo(isbn=isbn, valid=False)
        
        if not valid:
            return ISBNInfo(isbn=isbn, valid=False)
        
        info = ISBNInfo(
            isbn=cleaned_isbn,
            valid=True,
            isbn10=cleaned_isbn if len(cleaned_isbn) == 10 else self._isbn13_to_10(cleaned_isbn),
            isbn13=cleaned_isbn if len(cleaned_isbn) == 13 else self._isbn10_to_13(cleaned_isbn)
        )
        
        if not aiohttp:
            return info
        
        # Open Library'den bilgi al
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://openlibrary.org/isbn/{cleaned_isbn}.json"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        info.title = data.get("title")
                        info.page_count = data.get("number_of_pages")
        except:
            pass
        
        return info
    
    async def check_url(self, url: str) -> URLStatus:
        """
        URL erişilebilirliğini kontrol et.
        
        Args:
            url: Kontrol edilecek URL
            
        Returns:
            URL durumu
        """
        status = URLStatus(url=url, accessible=False)
        
        if not aiohttp:
            status.error_message = "aiohttp kurulu değil"
            return status
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(
                    url,
                    timeout=10,
                    allow_redirects=True
                ) as response:
                    status.status_code = response.status
                    status.accessible = response.status == 200
                    
                    content_type = response.headers.get("Content-Type", "")
                    status.content_type = content_type
                    status.is_pdf = "pdf" in content_type.lower()
                    status.is_html = "html" in content_type.lower()
                    
                    # Login gereksinimi kontrolü
                    if response.status in [401, 403]:
                        status.requires_login = True
                        status.accessible = False
                        status.error_message = "Erişim için giriş gerekli"
        except asyncio.TimeoutError:
            status.error_message = "Zaman aşımı"
        except Exception as e:
            status.error_message = str(e)
        
        return status
    
    async def verify_orcid(self, orcid: str) -> Tuple[bool, Optional[Dict]]:
        """
        ORCID doğrula.
        
        Args:
            orcid: ORCID numarası
            
        Returns:
            (doğrulandı mı, yazar bilgileri)
        """
        # ORCID formatı: 0000-0002-1825-0097
        pattern = r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$'
        if not re.match(pattern, orcid):
            return False, None
        
        if not aiohttp:
            return False, None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://pub.orcid.org/v3.0/{orcid}/record"
                headers = {"Accept": "application/json"}
                
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        person = data.get("person", {})
                        name = person.get("name", {})
                        
                        return True, {
                            "given_name": name.get("given-names", {}).get("value"),
                            "family_name": name.get("family-name", {}).get("value"),
                            "orcid": orcid
                        }
        except:
            pass
        
        return False, None
    
    async def find_full_text(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[str]:
        """
        Tam metin PDF bulma girişimi.
        
        Args:
            doi: DOI
            title: Başlık
            
        Returns:
            PDF URL (varsa)
        """
        if doi and aiohttp:
            # Unpaywall dene
            try:
                email = self.config.get("email", "user@example.com")
                url = f"{self.unpaywall_api}/{doi}?email={email}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            best = data.get("best_oa_location")
                            if best and best.get("url_for_pdf"):
                                return best["url_for_pdf"]
            except:
                pass
            
            # Sci-Hub (link oluştur, indirme değil)
            scihub_url = f"https://sci-hub.se/{doi}"
            return scihub_url
        
        return None
    
    async def _check_open_access(self, doi_info: DOIInfo) -> DOIInfo:
        """Open access durumunu kontrol et."""
        if not aiohttp or not doi_info.doi:
            return doi_info
        
        try:
            email = self.config.get("email", "user@example.com")
            url = f"{self.unpaywall_api}/{doi_info.doi}?email={email}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("is_oa"):
                            doi_info.access_status = AccessStatus.OPEN_ACCESS
                            best = data.get("best_oa_location")
                            if best:
                                doi_info.pdf_url = best.get("url_for_pdf")
                                doi_info.license = best.get("license")
                        else:
                            doi_info.access_status = AccessStatus.SUBSCRIPTION_REQUIRED
        except:
            pass
        
        return doi_info
    
    def _clean_doi(self, doi: str) -> str:
        """DOI temizle."""
        doi = doi.strip()
        
        # URL formatından çıkar
        prefixes = [
            "https://doi.org/",
            "http://doi.org/",
            "https://dx.doi.org/",
            "http://dx.doi.org/",
            "doi:",
            "DOI:"
        ]
        
        for prefix in prefixes:
            if doi.lower().startswith(prefix.lower()):
                doi = doi[len(prefix):]
        
        return doi
    
    def _validate_doi_format(self, doi: str) -> bool:
        """DOI format kontrolü."""
        # Temel DOI formatı: 10.prefix/suffix
        pattern = r'^10\.\d{4,}(?:\.\d+)*\/\S+$'
        return bool(re.match(pattern, doi))
    
    def _validate_isbn10(self, isbn: str) -> bool:
        """ISBN-10 checksum doğrulama."""
        if len(isbn) != 10:
            return False
        
        total = 0
        for i, char in enumerate(isbn):
            if char == 'X':
                total += 10 * (10 - i)
            else:
                total += int(char) * (10 - i)
        
        return total % 11 == 0
    
    def _validate_isbn13(self, isbn: str) -> bool:
        """ISBN-13 checksum doğrulama."""
        if len(isbn) != 13:
            return False
        
        total = 0
        for i, char in enumerate(isbn):
            if char.isdigit():
                weight = 1 if i % 2 == 0 else 3
                total += int(char) * weight
        
        return total % 10 == 0
    
    def _isbn10_to_13(self, isbn10: str) -> Optional[str]:
        """ISBN-10'u ISBN-13'e çevir."""
        if len(isbn10) != 10:
            return None
        
        prefix = "978" + isbn10[:9]
        
        total = 0
        for i, char in enumerate(prefix):
            weight = 1 if i % 2 == 0 else 3
            total += int(char) * weight
        
        check = (10 - (total % 10)) % 10
        return prefix + str(check)
    
    def _isbn13_to_10(self, isbn13: str) -> Optional[str]:
        """ISBN-13'ü ISBN-10'a çevir (978 prefix için)."""
        if not isbn13.startswith("978"):
            return None
        
        core = isbn13[3:12]
        
        total = 0
        for i, char in enumerate(core):
            total += int(char) * (10 - i)
        
        check = (11 - (total % 11)) % 11
        check_char = 'X' if check == 10 else str(check)
        
        return core + check_char
    
    def _match_title(self, title1: str, title2: str) -> bool:
        """Başlıkları karşılaştır."""
        # Normalizasyon
        def normalize(t):
            t = t.lower()
            t = re.sub(r'[^\w\s]', '', t)
            t = ' '.join(t.split())
            return t
        
        n1 = normalize(title1)
        n2 = normalize(title2)
        
        # Tam eşleşme
        if n1 == n2:
            return True
        
        # Kısmen eşleşme (Jaccard)
        words1 = set(n1.split())
        words2 = set(n2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return (intersection / union) >= 0.7
    
    def _match_authors(
        self,
        authors1: List[str],
        authors2: List[str]
    ) -> bool:
        """Yazar listelerini karşılaştır."""
        if not authors1 or not authors2:
            return False
        
        def get_surname(name):
            parts = name.strip().split()
            return parts[-1].lower() if parts else ""
        
        surnames1 = set(get_surname(a) for a in authors1)
        surnames2 = set(get_surname(a) for a in authors2)
        
        # En az ilk yazar eşleşmeli
        first1 = get_surname(authors1[0]) if authors1 else ""
        first2 = get_surname(authors2[0]) if authors2 else ""
        
        if first1 and first2 and first1 == first2:
            return True
        
        # Genel eşleşme
        intersection = len(surnames1 & surnames2)
        return intersection >= min(len(surnames1), len(surnames2)) * 0.5


async def main():
    """Test."""
    verifier = SourceVerifier()
    
    # DOI testi
    doi_info = await verifier.verify_doi("10.1038/nature12373")
    print(f"DOI Valid: {doi_info.valid}")
    print(f"Title: {doi_info.title}")
    
    # ISBN testi
    isbn_info = await verifier.verify_isbn("978-0-13-468599-1")
    print(f"ISBN Valid: {isbn_info.valid}")


if __name__ == "__main__":
    asyncio.run(main())
