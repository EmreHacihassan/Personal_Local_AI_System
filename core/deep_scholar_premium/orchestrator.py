"""
DeepScholar Premium Orchestrator
================================

Tüm premium bileşenleri entegre eden ana orkestratör.

ÖNEMLİ TASARIM PRENSİPLERİ:
1. FARKLI BAKIŞ AÇILARI DEĞERLİDİR - Farklı perspektifler zenginliktir
2. Kalite kontrolü perspektif çeşitliliğini KORUR, törpülemez
3. Bias analizi tarafsızlığı sağlar ama fikirleri homojenleştirmez
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Premium agents
from .agents.quality_agent import QualityAssuranceAgent
from .agents.critic_agent import CriticAgent
from .agents.editor_agent import EditorAgent
from .agents.citation_agent import CitationAgent
from .agents.statistics_agent import StatisticsAgent
from .agents.translator_agent import TranslatorAgent

# Research modules
from .research.advanced_search import AdvancedSearchEngine
from .research.source_quality import SourceQualityAnalyzer
from .research.source_verifier import SourceVerifier

# Quality modules
from .quality.plagiarism_detector import PlagiarismDetector
from .quality.readability_analyzer import ReadabilityAnalyzer
from .quality.consistency_checker import ConsistencyChecker
from .quality.bias_analyzer import BiasAnalyzer
from .quality.quality_scorer import QualityScorer

# Visuals modules
from .visuals.diagram_generator import DiagramGenerator
from .visuals.svg_charts import SVGChartGenerator
from .visuals.data_visualization import DataVisualizationEngine

# Export modules
from .export.pdf_exporter import PremiumPDFExporter
from .export.docx_exporter import DOCXExporter
from .export.latex_exporter import LaTeXExporter
from .export.html_exporter import HTMLExporter
from .export.presentation_generator import PresentationGenerator


logger = logging.getLogger(__name__)


class PremiumTier(str, Enum):
    """Premium tier seviyeleri."""
    BASIC = "basic"          # Temel özellikler
    STANDARD = "standard"    # Standart premium
    PROFESSIONAL = "professional"  # Profesyonel
    ENTERPRISE = "enterprise"  # Kurumsal


class DocumentType(str, Enum):
    """Doküman türleri."""
    RESEARCH_PAPER = "research_paper"
    THESIS = "thesis"
    REPORT = "report"
    ARTICLE = "article"
    REVIEW = "review"
    CASE_STUDY = "case_study"


@dataclass
class PremiumConfig:
    """Premium konfigürasyonu."""
    tier: PremiumTier = PremiumTier.STANDARD
    
    # LLM ayarları
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen3:4b"
    llm_timeout: int = 600
    
    # Kalite ayarları
    min_quality_score: float = 0.7
    enable_plagiarism_check: bool = True
    enable_bias_analysis: bool = True
    preserve_diverse_perspectives: bool = True  # FARKLI BAKIŞ AÇILARI!
    
    # Araştırma ayarları
    max_sources: int = 50
    verify_sources: bool = True
    academic_sources_only: bool = False
    
    # Görselleştirme
    enable_diagrams: bool = True
    diagram_format: str = "mermaid"
    enable_charts: bool = True
    
    # Çıktı formatları
    output_formats: List[str] = field(default_factory=lambda: ["html", "pdf"])
    
    # Dil
    language: str = "tr"
    enable_translation: bool = False


@dataclass
class DocumentRequest:
    """Doküman oluşturma isteği."""
    topic: str
    document_type: DocumentType = DocumentType.RESEARCH_PAPER
    config: Optional[PremiumConfig] = None
    outline: Optional[List[Dict[str, Any]]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    requirements: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PremiumDocument:
    """Premium doküman."""
    title: str
    content: str
    sections: List[Dict[str, Any]]
    
    # Kalite metrikleri
    quality_score: float = 0.0
    quality_report: Optional[Dict[str, Any]] = None
    
    # Kaynaklar
    sources: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    
    # Görseller
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Çıktılar
    exports: Dict[str, str] = field(default_factory=dict)
    
    # Meta
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_time: float = 0.0


class DeepScholarPremiumOrchestrator:
    """
    DeepScholar Premium Orkestratör
    
    Tüm premium bileşenleri koordine eder.
    
    ÖNEMLİ: Bu sistem farklı bakış açılarını KORUR.
    Kalite kontrolü perspektif çeşitliliğini zenginlik olarak görür.
    """
    
    def __init__(self, config: Optional[PremiumConfig] = None):
        self.config = config or PremiumConfig()
        
        # Bileşenleri başlat
        self._init_agents()
        self._init_research()
        self._init_quality()
        self._init_visuals()
        self._init_export()
        
        logger.info(f"DeepScholar Premium başlatıldı (Tier: {self.config.tier.value})")
    
    def _init_agents(self):
        """Ajanları başlat."""
        base_url = self.config.llm_base_url
        model = self.config.llm_model
        timeout = self.config.llm_timeout
        
        self.quality_agent = QualityAssuranceAgent(
            ollama_base_url=base_url,
            model=model,
            timeout=timeout
        )
        
        self.critic_agent = CriticAgent(
            ollama_base_url=base_url,
            model=model,
            timeout=timeout
        )
        
        self.editor_agent = EditorAgent(
            ollama_base_url=base_url,
            model=model,
            timeout=timeout
        )
        
        self.citation_agent = CitationAgent(
            ollama_base_url=base_url,
            model=model,
            timeout=timeout
        )
        
        self.statistics_agent = StatisticsAgent(
            ollama_base_url=base_url,
            model=model,
            timeout=timeout
        )
        
        self.translator_agent = TranslatorAgent(
            ollama_base_url=base_url,
            model=model,
            timeout=timeout
        )
    
    def _init_research(self):
        """Araştırma modüllerini başlat."""
        self.search_engine = AdvancedSearchEngine()
        self.source_analyzer = SourceQualityAnalyzer()
        self.source_verifier = SourceVerifier()
    
    def _init_quality(self):
        """Kalite modüllerini başlat."""
        self.plagiarism_detector = PlagiarismDetector()
        self.readability_analyzer = ReadabilityAnalyzer()
        self.consistency_checker = ConsistencyChecker()
        
        # Bias analyzer - perspektif çeşitliliğini KORUR
        self.bias_analyzer = BiasAnalyzer(
            ollama_base_url=self.config.llm_base_url,
            model=self.config.llm_model
        )
        
        self.quality_scorer = QualityScorer()
    
    def _init_visuals(self):
        """Görselleştirme modüllerini başlat."""
        self.diagram_generator = DiagramGenerator()
        self.chart_generator = SVGChartGenerator()
        self.visualization_engine = DataVisualizationEngine(
            chart_generator=self.chart_generator,
            diagram_generator=self.diagram_generator
        )
    
    def _init_export(self):
        """Export modüllerini başlat."""
        self.pdf_exporter = PremiumPDFExporter()
        self.docx_exporter = DOCXExporter()
        self.latex_exporter = LaTeXExporter()
        self.html_exporter = HTMLExporter()
        self.presentation_generator = PresentationGenerator()
    
    async def generate_document(
        self,
        request: DocumentRequest
    ) -> PremiumDocument:
        """
        Premium doküman oluştur.
        
        Args:
            request: Doküman isteği
            
        Returns:
            Premium doküman
        """
        start_time = datetime.now()
        config = request.config or self.config
        
        logger.info(f"Premium doküman oluşturma başladı: {request.topic}")
        
        # 1. Kaynak araştırması
        sources = await self._research_phase(request)
        
        # 2. İçerik oluşturma (Base DeepScholar ile)
        content, sections = await self._content_generation_phase(request, sources)
        
        # 3. Kalite kontrolü
        quality_report = await self._quality_phase(content, sections, config)
        
        # 4. Düzenleme
        content, sections = await self._editing_phase(content, sections, quality_report)
        
        # 5. Görselleştirme
        diagrams, charts = await self._visualization_phase(sections, config)
        
        # 6. Kaynak formatlaması
        citations = await self._citation_phase(sources)
        
        # 7. Dışa aktarma
        exports = await self._export_phase(
            request.topic,
            content,
            sections,
            citations,
            config
        )
        
        # Sonuç
        generation_time = (datetime.now() - start_time).total_seconds()
        
        document = PremiumDocument(
            title=request.topic,
            content=content,
            sections=sections,
            quality_score=quality_report.get('overall_score', 0.0),
            quality_report=quality_report,
            sources=sources,
            citations=citations,
            diagrams=diagrams,
            charts=charts,
            exports=exports,
            metadata=request.metadata or {},
            generation_time=generation_time
        )
        
        logger.info(f"Premium doküman tamamlandı: {request.topic} ({generation_time:.1f}s)")
        
        return document
    
    async def _research_phase(
        self,
        request: DocumentRequest
    ) -> List[Dict[str, Any]]:
        """Araştırma fazı."""
        if request.sources:
            sources = request.sources
        else:
            # Otomatik kaynak araştırması
            search_result = await self.search_engine.search(
                query=request.topic,
                max_results=self.config.max_sources
            )
            sources = search_result.get('results', [])
        
        # Kaynak kalite analizi
        analyzed_sources = []
        for source in sources:
            quality = await self.source_analyzer.analyze_source(source)
            source['quality_score'] = quality.get('overall_score', 0.5)
            analyzed_sources.append(source)
        
        # Kaliteye göre sırala
        analyzed_sources.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # Doğrulama
        if self.config.verify_sources:
            for source in analyzed_sources[:20]:  # İlk 20 kaynak
                verification = await self.source_verifier.verify_source(source)
                source['verified'] = verification.get('verified', False)
        
        return analyzed_sources
    
    async def _content_generation_phase(
        self,
        request: DocumentRequest,
        sources: List[Dict[str, Any]]
    ) -> tuple:
        """İçerik oluşturma fazı."""
        # Bu faz base DeepScholar tarafından yapılır
        # Burada sadece placeholder
        
        sections = []
        content = ""
        
        # Outline varsa kullan
        if request.outline:
            for item in request.outline:
                sections.append({
                    'title': item.get('title', ''),
                    'level': item.get('level', 1),
                    'content': item.get('content', ''),
                    'subsections': item.get('subsections', [])
                })
        
        return content, sections
    
    async def _quality_phase(
        self,
        content: str,
        sections: List[Dict[str, Any]],
        config: PremiumConfig
    ) -> Dict[str, Any]:
        """
        Kalite kontrol fazı.
        
        ÖNEMLİ: Bu faz farklı bakış açılarını KORUR.
        Perspektif çeşitliliği kalite düşüşü değil, zenginliktir.
        """
        full_text = self._sections_to_text(sections)
        
        quality_report = {
            'overall_score': 0.0,
            'dimensions': {},
            'issues': [],
            'recommendations': []
        }
        
        # Okunabilirlik
        readability = await self.readability_analyzer.analyze(full_text)
        quality_report['dimensions']['readability'] = readability
        
        # Tutarlılık
        consistency = await self.consistency_checker.check(full_text, sections)
        quality_report['dimensions']['consistency'] = consistency
        
        # İntihal kontrolü
        if config.enable_plagiarism_check:
            plagiarism = await self.plagiarism_detector.detect(full_text)
            quality_report['dimensions']['originality'] = {
                'score': 1.0 - plagiarism.get('similarity_score', 0),
                'details': plagiarism
            }
        
        # Bias analizi - PERSPEKTİF ÇEŞİTLİLİĞİNİ KORUR
        if config.enable_bias_analysis:
            bias_result = await self.bias_analyzer.analyze(full_text)
            quality_report['dimensions']['perspective_diversity'] = bias_result
            
            # Perspektif çeşitliliği YÜKSEKSE bonus puan
            if bias_result.get('perspective_diversity_score', 0) > 0.7:
                quality_report['recommendations'].append({
                    'type': 'positive',
                    'message': 'Belgede zengin perspektif çeşitliliği tespit edildi. Bu kaliteyi artırıcı bir özelliktir.'
                })
        
        # Genel skor hesapla
        scores = []
        for dim_name, dim_data in quality_report['dimensions'].items():
            if isinstance(dim_data, dict) and 'score' in dim_data:
                scores.append(dim_data['score'])
        
        if scores:
            quality_report['overall_score'] = sum(scores) / len(scores)
        
        return quality_report
    
    async def _editing_phase(
        self,
        content: str,
        sections: List[Dict[str, Any]],
        quality_report: Dict[str, Any]
    ) -> tuple:
        """
        Düzenleme fazı.
        
        ÖNEMLİ: Düzenleme farklı bakış açılarını KORUR.
        Sadece dil bilgisi, stil ve akış düzenlenir.
        """
        # Kalite sorunlarına göre düzenleme
        for section in sections:
            if section.get('content'):
                # Editor agent ile düzenle
                edit_result = await self.editor_agent.edit(
                    text=section['content'],
                    preserve_perspectives=True  # PERSPEKTİFLERİ KORU
                )
                
                if edit_result.get('edited_text'):
                    section['content'] = edit_result['edited_text']
        
        # İçeriği yeniden birleştir
        content = self._sections_to_text(sections)
        
        return content, sections
    
    async def _visualization_phase(
        self,
        sections: List[Dict[str, Any]],
        config: PremiumConfig
    ) -> tuple:
        """Görselleştirme fazı."""
        diagrams = []
        charts = []
        
        if not config.enable_diagrams and not config.enable_charts:
            return diagrams, charts
        
        for section in sections:
            content = section.get('content', '')
            
            # Diagram önerileri
            if config.enable_diagrams:
                diagram_suggestions = await self.diagram_generator.suggest_diagrams(
                    content=content,
                    topic=section.get('title', '')
                )
                
                for suggestion in diagram_suggestions[:2]:  # Max 2 diagram per section
                    diagram = await self.diagram_generator.generate(
                        diagram_type=suggestion.get('type'),
                        content=suggestion.get('content'),
                        format=config.diagram_format
                    )
                    if diagram:
                        diagrams.append({
                            'section': section.get('title', ''),
                            'diagram': diagram
                        })
        
        return diagrams, charts
    
    async def _citation_phase(
        self,
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """Kaynak formatlaması fazı."""
        citations = []
        
        for source in sources[:30]:  # Max 30 kaynak
            citation = await self.citation_agent.format_citation(
                source=source,
                style='apa'  # Varsayılan APA
            )
            if citation:
                citations.append(citation)
        
        return citations
    
    async def _export_phase(
        self,
        title: str,
        content: str,
        sections: List[Dict[str, Any]],
        citations: List[str],
        config: PremiumConfig
    ) -> Dict[str, str]:
        """Dışa aktarma fazı."""
        exports = {}
        
        # HTML
        if 'html' in config.output_formats:
            from .export.html_exporter import HTMLDocument
            html_doc = HTMLDocument(
                title=title,
                content=content,
                sections=sections,
                metadata={'citations': citations}
            )
            exports['html'] = self.html_exporter.export(html_doc)
        
        # LaTeX
        if 'latex' in config.output_formats:
            from .export.latex_exporter import LaTeXDocument
            latex_doc = LaTeXDocument(
                title=title,
                sections=sections,
                references=[{'text': c} for c in citations]
            )
            exports['latex'] = self.latex_exporter.export(latex_doc)
        
        return exports
    
    def _sections_to_text(self, sections: List[Dict[str, Any]]) -> str:
        """Bölümleri düz metne dönüştür."""
        parts = []
        
        def process_section(sec: Dict[str, Any], level: int = 1):
            title = sec.get('title', '')
            content = sec.get('content', '')
            
            if title:
                parts.append(f"\n{'#' * level} {title}\n")
            if content:
                parts.append(content)
            
            for subsec in sec.get('subsections', []):
                process_section(subsec, level + 1)
        
        for section in sections:
            process_section(section)
        
        return '\n'.join(parts)
    
    # === Yardımcı metodlar ===
    
    async def analyze_quality(self, text: str) -> Dict[str, Any]:
        """Metin kalitesini analiz et."""
        return await self._quality_phase(text, [], self.config)
    
    async def check_plagiarism(self, text: str) -> Dict[str, Any]:
        """İntihal kontrolü."""
        return await self.plagiarism_detector.detect(text)
    
    async def analyze_bias(self, text: str) -> Dict[str, Any]:
        """
        Bias analizi.
        
        Not: Bu analiz perspektif çeşitliliğini DEĞER olarak görür.
        """
        return await self.bias_analyzer.analyze(text)
    
    async def generate_presentation(
        self,
        document: PremiumDocument
    ) -> str:
        """Sunuma dönüştür."""
        from .export.presentation_generator import Presentation
        
        presentation = self.presentation_generator.from_document_sections(
            title=document.title,
            sections=document.sections,
            authors=document.metadata.get('authors', [])
        )
        
        return self.presentation_generator.generate(presentation)
    
    async def translate_document(
        self,
        document: PremiumDocument,
        target_language: str
    ) -> PremiumDocument:
        """Dokümanı çevir."""
        translated_sections = []
        
        for section in document.sections:
            translated = await self.translator_agent.translate(
                text=section.get('content', ''),
                source_lang='auto',
                target_lang=target_language
            )
            
            translated_section = section.copy()
            translated_section['content'] = translated.get('translated_text', section.get('content', ''))
            translated_sections.append(translated_section)
        
        translated_doc = PremiumDocument(
            title=document.title,
            content=self._sections_to_text(translated_sections),
            sections=translated_sections,
            quality_score=document.quality_score,
            sources=document.sources,
            metadata={**document.metadata, 'translated_to': target_language}
        )
        
        return translated_doc
