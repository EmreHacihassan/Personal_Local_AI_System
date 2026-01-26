"""
DeepScholar Premium v3.0 - Enterprise Academic Document Generation
===================================================================

Premium özellikler:
- Gelişmiş çoklu ajan mimarisi (6 özelleştirilmiş ajan)
- Kapsamlı araştırma (Semantic Scholar, CrossRef, OpenAlex, ArXiv)
- QualityAssuranceAgent ile kalite garantisi
- Tarafsızlık analizi (PERSPEKTİF ÇEŞİTLİLİĞİNİ KORUR)
- Profesyonel export (PDF, DOCX, LaTeX, HTML, Presentation)
- İleri düzey görselleştirme (Diagrams, Charts)
- Plagiarism ve readability analizi

ÖNEMLİ TASARIM PRENSİBİ:
Bu sistem FARKLI BAKIŞ AÇILARINI DEĞERLİ görür ve KORUR.
Kalite kontrolü perspektif çeşitliliğini zenginlik olarak değerlendirir,
farklı fikirleri "törpülemez" veya homojenleştirmez.

Modüller:
- agents: Özelleştirilmiş premium ajanlar (6 ajan)
- research: Gelişmiş araştırma motorları
- quality: Kalite kontrol araçları
- visuals: İleri düzey görselleştirme
- export: Çoklu format export

Author: DeepScholar Team
Version: 3.0 Premium
"""

# Agents
from .agents import (
    QualityAssuranceAgent,
    CriticAgent,
    EditorAgent,
    CitationAgent,
    StatisticsAgent,
    TranslatorAgent
)

# Research
from .research import (
    AdvancedSearchEngine,
    SourceQualityAnalyzer,
    SourceVerifier
)

# Quality
from .quality import (
    PlagiarismDetector,
    ReadabilityAnalyzer,
    ConsistencyChecker,
    BiasAnalyzer,
    QualityScorer
)

# Visuals
from .visuals import (
    DiagramGenerator,
    SVGChartGenerator,
    DataVisualizationEngine
)

# Export
from .export import (
    PremiumPDFExporter,
    DOCXExporter,
    LaTeXExporter,
    HTMLExporter,
    PresentationGenerator
)

# Orchestrator
from .orchestrator import (
    DeepScholarPremiumOrchestrator,
    PremiumConfig,
    DocumentRequest,
    PremiumDocument,
    PremiumTier,
    DocumentType
)

__version__ = "3.0.0"
__all__ = [
    # Agents
    "QualityAssuranceAgent",
    "CriticAgent", 
    "EditorAgent",
    "CitationAgent",
    "StatisticsAgent",
    "TranslatorAgent",
    
    # Research
    "AdvancedSearchEngine",
    "SourceQualityAnalyzer",
    "SourceVerifier",
    
    # Quality
    "PlagiarismDetector",
    "ReadabilityAnalyzer",
    "ConsistencyChecker",
    "BiasAnalyzer",
    "QualityScorer",
    
    # Visuals
    "DiagramGenerator",
    "SVGChartGenerator",
    "DataVisualizationEngine",
    
    # Export
    "PremiumPDFExporter",
    "DOCXExporter",
    "LaTeXExporter",
    "HTMLExporter",
    "PresentationGenerator",
    
    # Orchestrator
    "DeepScholarPremiumOrchestrator",
    "PremiumConfig",
    "DocumentRequest",
    "PremiumDocument",
    "PremiumTier",
    "DocumentType"
]
