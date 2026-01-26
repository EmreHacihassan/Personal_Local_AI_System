"""
PremiumPDFExporter - Profesyonel PDF Dışa Aktarma
================================================

Şablon tabanlı, akademik standartlara uygun PDF oluşturma.
"""

import io
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PDFTemplate(str, Enum):
    """PDF Şablonları."""
    ACADEMIC_PAPER = "academic_paper"
    THESIS = "thesis"
    REPORT = "report"
    ARTICLE = "article"
    BOOK_CHAPTER = "book_chapter"
    CONFERENCE_PAPER = "conference_paper"


class PageSize(str, Enum):
    """Sayfa boyutları."""
    A4 = "A4"
    LETTER = "Letter"
    A5 = "A5"


@dataclass
class DocumentMetadata:
    """Doküman metadata."""
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    date: Optional[str] = None
    institution: Optional[str] = None
    doi: Optional[str] = None
    version: str = "1.0"


@dataclass
class PDFStyle:
    """PDF stil ayarları."""
    # Sayfa
    page_size: PageSize = PageSize.A4
    margin_top: float = 2.5  # cm
    margin_bottom: float = 2.5
    margin_left: float = 2.5
    margin_right: float = 2.5
    
    # Yazı tipleri
    font_family: str = "Times New Roman"
    title_font_size: int = 18
    heading1_font_size: int = 14
    heading2_font_size: int = 12
    body_font_size: int = 11
    caption_font_size: int = 10
    
    # Satır aralığı
    line_spacing: float = 1.5
    paragraph_spacing: float = 12  # pt
    
    # Renk
    primary_color: str = "#000000"
    accent_color: str = "#1a5276"
    
    # Numaralandırma
    number_sections: bool = True
    number_figures: bool = True
    number_tables: bool = True


@dataclass
class Section:
    """Bölüm."""
    title: str
    content: str
    level: int = 1
    subsections: List['Section'] = field(default_factory=list)


@dataclass
class Figure:
    """Şekil."""
    image_path: Optional[str] = None
    svg_code: Optional[str] = None
    caption: str = ""
    number: Optional[int] = None


@dataclass
class Table:
    """Tablo."""
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    caption: str = ""
    number: Optional[int] = None


@dataclass
class PDFDocument:
    """PDF Dokümanı."""
    metadata: DocumentMetadata
    sections: List[Section] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    appendices: List[Section] = field(default_factory=list)


class PremiumPDFExporter:
    """
    Profesyonel PDF Dışa Aktarma Modülü
    
    ReportLab benzeri saf Python PDF oluşturma.
    Harici bağımlılık gerektirmez.
    """
    
    def __init__(
        self,
        template: PDFTemplate = PDFTemplate.ACADEMIC_PAPER,
        style: Optional[PDFStyle] = None
    ):
        self.template = template
        self.style = style or PDFStyle()
        
        # Sayfa boyutları (mm)
        self.page_sizes = {
            PageSize.A4: (210, 297),
            PageSize.LETTER: (216, 279),
            PageSize.A5: (148, 210)
        }
        
        self._figure_count = 0
        self._table_count = 0
        self._section_numbers = []
    
    def export(
        self,
        document: PDFDocument,
        output_path: Optional[str] = None
    ) -> Union[bytes, str]:
        """
        Dokümanı PDF olarak dışa aktar.
        
        Not: Tam PDF oluşturma için reportlab veya weasyprint gerekir.
        Bu implementasyon HTML çıktısı üretir ve PDF'e dönüştürme için
        harici araçlara (wkhtmltopdf, Chrome headless, etc.) bırakılır.
        
        Args:
            document: PDF dokümanı
            output_path: Çıktı dosya yolu
            
        Returns:
            PDF-ready HTML içeriği
        """
        html = self._build_html(document)
        
        if output_path:
            with open(output_path.replace('.pdf', '.html'), 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html
    
    def export_to_markdown(
        self,
        document: PDFDocument,
        output_path: Optional[str] = None
    ) -> str:
        """Markdown olarak dışa aktar."""
        md = self._build_markdown(document)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md)
        
        return md
    
    def _build_html(self, document: PDFDocument) -> str:
        """HTML oluştur."""
        style = self.style
        
        css = self._generate_css()
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="tr">',
            '<head>',
            '<meta charset="UTF-8">',
            f'<title>{document.metadata.title}</title>',
            '<style>',
            css,
            '</style>',
            '</head>',
            '<body>',
            '<div class="document">'
        ]
        
        # Başlık sayfası
        html_parts.append(self._render_title_page(document.metadata))
        
        # Özet
        if document.metadata.abstract:
            html_parts.append(self._render_abstract(document.metadata.abstract))
        
        # İçindekiler
        html_parts.append(self._render_toc(document.sections))
        
        # Bölümler
        for section in document.sections:
            html_parts.append(self._render_section(section, []))
        
        # Referanslar
        if document.references:
            html_parts.append(self._render_references(document.references))
        
        # Ekler
        for appendix in document.appendices:
            html_parts.append(self._render_appendix(appendix))
        
        html_parts.extend([
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def _generate_css(self) -> str:
        """CSS oluştur."""
        style = self.style
        page_width, page_height = self.page_sizes[style.page_size]
        
        return f'''
        @page {{
            size: {style.page_size.value};
            margin: {style.margin_top}cm {style.margin_right}cm {style.margin_bottom}cm {style.margin_left}cm;
        }}
        
        body {{
            font-family: "{style.font_family}", serif;
            font-size: {style.body_font_size}pt;
            line-height: {style.line_spacing};
            color: {style.primary_color};
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .document {{
            background: white;
        }}
        
        .title-page {{
            text-align: center;
            page-break-after: always;
            padding-top: 100px;
        }}
        
        .title {{
            font-size: {style.title_font_size}pt;
            font-weight: bold;
            margin-bottom: 30px;
            color: {style.accent_color};
        }}
        
        .authors {{
            font-size: {style.body_font_size}pt;
            margin-bottom: 20px;
        }}
        
        .institution {{
            font-size: {style.caption_font_size}pt;
            color: #666;
        }}
        
        .abstract {{
            margin: 30px 40px;
            padding: 20px;
            background: #f9f9f9;
            border-left: 3px solid {style.accent_color};
        }}
        
        .abstract-title {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .keywords {{
            margin-top: 15px;
            font-size: {style.caption_font_size}pt;
        }}
        
        .toc {{
            page-break-after: always;
        }}
        
        .toc-title {{
            font-size: {style.heading1_font_size}pt;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        
        .toc-item {{
            margin: 5px 0;
        }}
        
        .toc-level-1 {{ margin-left: 0; }}
        .toc-level-2 {{ margin-left: 20px; }}
        .toc-level-3 {{ margin-left: 40px; }}
        
        h1 {{
            font-size: {style.heading1_font_size}pt;
            color: {style.accent_color};
            border-bottom: 2px solid {style.accent_color};
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        
        h2 {{
            font-size: {style.heading2_font_size}pt;
            margin-top: 25px;
        }}
        
        h3 {{
            font-size: {style.body_font_size + 1}pt;
            margin-top: 20px;
        }}
        
        p {{
            text-align: justify;
            margin-bottom: {style.paragraph_spacing}pt;
        }}
        
        .figure {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .figure-caption {{
            font-size: {style.caption_font_size}pt;
            font-style: italic;
            margin-top: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        
        th {{
            background: {style.accent_color};
            color: white;
        }}
        
        .table-caption {{
            font-size: {style.caption_font_size}pt;
            font-style: italic;
            margin-bottom: 10px;
        }}
        
        .references {{
            margin-top: 40px;
        }}
        
        .reference-item {{
            margin: 10px 0;
            padding-left: 30px;
            text-indent: -30px;
        }}
        
        @media print {{
            body {{
                max-width: none;
                padding: 0;
            }}
            
            .document {{
                page-break-inside: auto;
            }}
            
            h1, h2, h3 {{
                page-break-after: avoid;
            }}
        }}
        '''
    
    def _render_title_page(self, metadata: DocumentMetadata) -> str:
        """Başlık sayfası."""
        parts = ['<div class="title-page">']
        
        parts.append(f'<h1 class="title">{metadata.title}</h1>')
        
        if metadata.authors:
            parts.append('<div class="authors">')
            parts.append('<br>'.join(metadata.authors))
            parts.append('</div>')
        
        if metadata.institution:
            parts.append(f'<div class="institution">{metadata.institution}</div>')
        
        if metadata.date:
            parts.append(f'<div class="date">{metadata.date}</div>')
        elif metadata.date is None:
            parts.append(f'<div class="date">{datetime.now().strftime("%B %Y")}</div>')
        
        if metadata.doi:
            parts.append(f'<div class="doi">DOI: {metadata.doi}</div>')
        
        parts.append('</div>')
        
        return '\n'.join(parts)
    
    def _render_abstract(self, abstract: str) -> str:
        """Özet."""
        return f'''
        <div class="abstract">
            <div class="abstract-title">Özet / Abstract</div>
            <p>{abstract}</p>
        </div>
        '''
    
    def _render_toc(self, sections: List[Section]) -> str:
        """İçindekiler."""
        parts = [
            '<div class="toc">',
            '<div class="toc-title">İçindekiler</div>'
        ]
        
        def render_toc_items(secs: List[Section], level: int = 1, prefix: str = ""):
            items = []
            for i, sec in enumerate(secs):
                num = f"{prefix}{i+1}." if self.style.number_sections else ""
                items.append(f'<div class="toc-item toc-level-{level}">{num} {sec.title}</div>')
                if sec.subsections:
                    items.extend(render_toc_items(sec.subsections, level + 1, f"{prefix}{i+1}."))
            return items
        
        parts.extend(render_toc_items(sections))
        parts.append('</div>')
        
        return '\n'.join(parts)
    
    def _render_section(self, section: Section, numbers: List[int]) -> str:
        """Bölüm."""
        numbers = numbers + [len(numbers) + 1]
        number_str = ".".join(map(str, numbers)) + "." if self.style.number_sections else ""
        
        heading_tag = f"h{min(section.level, 6)}"
        
        parts = [f'<{heading_tag}>{number_str} {section.title}</{heading_tag}>']
        
        # İçerik
        content = self._process_content(section.content)
        parts.append(f'<div class="section-content">{content}</div>')
        
        # Alt bölümler
        for i, subsec in enumerate(section.subsections):
            parts.append(self._render_section(subsec, numbers))
        
        return '\n'.join(parts)
    
    def _process_content(self, content: str) -> str:
        """İçeriği HTML'e dönüştür."""
        # Paragraflar
        paragraphs = content.split('\n\n')
        processed = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # Bold
                para = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', para)
                # Italic
                para = re.sub(r'\*(.*?)\*', r'<em>\1</em>', para)
                # Inline code
                para = re.sub(r'`(.*?)`', r'<code>\1</code>', para)
                
                processed.append(f'<p>{para}</p>')
        
        return '\n'.join(processed)
    
    def _render_references(self, references: List[str]) -> str:
        """Referanslar."""
        parts = [
            '<div class="references">',
            '<h1>Kaynakça / References</h1>'
        ]
        
        for i, ref in enumerate(references, 1):
            parts.append(f'<div class="reference-item">[{i}] {ref}</div>')
        
        parts.append('</div>')
        
        return '\n'.join(parts)
    
    def _render_appendix(self, appendix: Section) -> str:
        """Ek."""
        return f'''
        <div class="appendix">
            <h1>Ek: {appendix.title}</h1>
            <div class="appendix-content">{self._process_content(appendix.content)}</div>
        </div>
        '''
    
    def _build_markdown(self, document: PDFDocument) -> str:
        """Markdown oluştur."""
        parts = []
        
        # Başlık
        parts.append(f'# {document.metadata.title}\n')
        
        if document.metadata.authors:
            parts.append(f'**Yazarlar:** {", ".join(document.metadata.authors)}\n')
        
        if document.metadata.date:
            parts.append(f'**Tarih:** {document.metadata.date}\n')
        
        # Özet
        if document.metadata.abstract:
            parts.append('\n## Özet\n')
            parts.append(document.metadata.abstract + '\n')
        
        # Anahtar kelimeler
        if document.metadata.keywords:
            parts.append(f'\n**Anahtar Kelimeler:** {", ".join(document.metadata.keywords)}\n')
        
        parts.append('\n---\n')
        
        # Bölümler
        def render_section_md(sec: Section, level: int = 2):
            heading = '#' * level
            md = [f'\n{heading} {sec.title}\n']
            md.append(sec.content + '\n')
            
            for subsec in sec.subsections:
                md.append(render_section_md(subsec, level + 1))
            
            return '\n'.join(md)
        
        for section in document.sections:
            parts.append(render_section_md(section))
        
        # Referanslar
        if document.references:
            parts.append('\n## Kaynakça\n')
            for i, ref in enumerate(document.references, 1):
                parts.append(f'{i}. {ref}')
        
        return '\n'.join(parts)
