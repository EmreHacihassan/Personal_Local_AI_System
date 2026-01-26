"""
Research Modülleri - Premium Araştırma Araçları
================================================

Bu modül gelişmiş araştırma yetenekleri sağlar:
- AdvancedSearchEngine: Çoklu kaynak arama (PubMed, Google Scholar, etc.)
- SourceQualityAnalyzer: Kaynak kalite değerlendirmesi
- SourceVerifier: DOI/ISBN doğrulama ve erişim kontrolü
"""

from .advanced_search import AdvancedSearchEngine
from .source_quality import SourceQualityAnalyzer
from .source_verifier import SourceVerifier

__all__ = [
    "AdvancedSearchEngine",
    "SourceQualityAnalyzer",
    "SourceVerifier"
]
