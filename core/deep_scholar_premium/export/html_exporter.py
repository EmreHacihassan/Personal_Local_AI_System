"""
HTMLExporter - Web-Ready HTML Dışa Aktarma
==========================================

Modern, responsive HTML çıktısı.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class HTMLTemplate(str, Enum):
    """HTML şablonları."""
    MINIMAL = "minimal"
    ACADEMIC = "academic"
    MODERN = "modern"
    DARK = "dark"


@dataclass
class HTMLStyle:
    """HTML stil ayarları."""
    template: HTMLTemplate = HTMLTemplate.MODERN
    
    # Renk teması
    primary_color: str = "#2c3e50"
    accent_color: str = "#3498db"
    background_color: str = "#ffffff"
    text_color: str = "#333333"
    
    # Typography
    font_family: str = "system-ui, -apple-system, sans-serif"
    heading_font: str = "Georgia, serif"
    code_font: str = "Consolas, monospace"
    font_size: str = "16px"
    line_height: str = "1.6"
    
    # Layout
    max_width: str = "800px"
    
    # Features
    syntax_highlight: bool = True
    table_of_contents: bool = True
    responsive: bool = True


@dataclass
class HTMLDocument:
    """HTML dokümanı."""
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    sections: List[Dict[str, Any]] = field(default_factory=list)
    styles: Optional[str] = None
    scripts: Optional[str] = None


class HTMLExporter:
    """
    Web-Ready HTML Dışa Aktarma Modülü
    
    SEO-friendly, accessibility-compliant HTML üretir.
    """
    
    def __init__(self, style: Optional[HTMLStyle] = None):
        self.style = style or HTMLStyle()
    
    def export(
        self,
        document: HTMLDocument,
        output_path: Optional[str] = None,
        standalone: bool = True
    ) -> str:
        """
        HTML olarak dışa aktar.
        
        Args:
            document: HTML dokümanı
            output_path: Çıktı dosya yolu
            standalone: Tam HTML mi yoksa sadece body mi
            
        Returns:
            HTML içeriği
        """
        if standalone:
            html = self._build_full_html(document)
        else:
            html = self._build_content_html(document)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html
    
    def _build_full_html(self, document: HTMLDocument) -> str:
        """Tam HTML dokümanı oluştur."""
        metadata = document.metadata or {}
        style = self.style
        
        css = self._generate_css()
        
        # Meta tags
        meta_tags = [
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<meta name="description" content="{self._escape(metadata.get("description", document.title))}">',
            f'<meta name="author" content="{self._escape(metadata.get("author", ""))}">',
        ]
        
        if metadata.get('keywords'):
            meta_tags.append(f'<meta name="keywords" content="{self._escape(", ".join(metadata["keywords"]))}">')
        
        # OpenGraph tags
        og_tags = [
            f'<meta property="og:title" content="{self._escape(document.title)}">',
            f'<meta property="og:type" content="article">',
        ]
        
        if metadata.get('description'):
            og_tags.append(f'<meta property="og:description" content="{self._escape(metadata["description"])}">')
        
        content_html = self._build_content_html(document)
        
        return f'''<!DOCTYPE html>
<html lang="{metadata.get('language', 'tr')}">
<head>
    {chr(10).join(meta_tags)}
    {chr(10).join(og_tags)}
    <title>{self._escape(document.title)}</title>
    <style>
{css}
    </style>
    {document.styles or ''}
</head>
<body>
    <article class="document">
        {content_html}
    </article>
    {document.scripts or ''}
</body>
</html>'''
    
    def _build_content_html(self, document: HTMLDocument) -> str:
        """İçerik HTML'i oluştur."""
        parts = []
        
        # Header
        parts.append(self._build_header(document))
        
        # Table of contents
        if self.style.table_of_contents and document.sections:
            parts.append(self._build_toc(document.sections))
        
        # Main content
        if document.content:
            parts.append(f'<div class="content">{self._process_content(document.content)}</div>')
        
        # Sections
        for section in document.sections:
            parts.append(self._render_section(section))
        
        return '\n'.join(parts)
    
    def _build_header(self, document: HTMLDocument) -> str:
        """Header oluştur."""
        metadata = document.metadata or {}
        
        parts = ['<header class="document-header">']
        parts.append(f'<h1 class="title">{self._escape(document.title)}</h1>')
        
        if metadata.get('authors'):
            authors = metadata['authors']
            if isinstance(authors, list):
                parts.append(f'<div class="authors">{", ".join(self._escape(a) for a in authors)}</div>')
            else:
                parts.append(f'<div class="authors">{self._escape(authors)}</div>')
        
        if metadata.get('date'):
            parts.append(f'<div class="date">{self._escape(metadata["date"])}</div>')
        
        if metadata.get('abstract'):
            parts.append(f'<div class="abstract"><strong>Özet:</strong> {self._escape(metadata["abstract"])}</div>')
        
        if metadata.get('keywords'):
            kw = ', '.join(metadata['keywords'])
            parts.append(f'<div class="keywords"><strong>Anahtar Kelimeler:</strong> {self._escape(kw)}</div>')
        
        parts.append('</header>')
        
        return '\n'.join(parts)
    
    def _build_toc(self, sections: List[Dict[str, Any]]) -> str:
        """İçindekiler oluştur."""
        parts = [
            '<nav class="table-of-contents">',
            '<h2>İçindekiler</h2>',
            '<ul>'
        ]
        
        def render_toc_items(secs: List[Dict[str, Any]], level: int = 0) -> List[str]:
            items = []
            for sec in secs:
                title = sec.get('title', '')
                slug = self._slugify(title)
                items.append(f'<li><a href="#{slug}">{self._escape(title)}</a>')
                
                subsections = sec.get('subsections', [])
                if subsections:
                    items.append('<ul>')
                    items.extend(render_toc_items(subsections, level + 1))
                    items.append('</ul>')
                
                items.append('</li>')
            return items
        
        parts.extend(render_toc_items(sections))
        parts.extend(['</ul>', '</nav>'])
        
        return '\n'.join(parts)
    
    def _render_section(self, section: Dict[str, Any], level: int = 2) -> str:
        """Bölüm render et."""
        title = section.get('title', '')
        content = section.get('content', '')
        subsections = section.get('subsections', [])
        
        slug = self._slugify(title)
        heading_tag = f'h{min(level, 6)}'
        
        parts = [f'<section id="{slug}">']
        
        if title:
            parts.append(f'<{heading_tag}>{self._escape(title)}</{heading_tag}>')
        
        if content:
            parts.append(f'<div class="section-content">{self._process_content(content)}</div>')
        
        # Figures
        for fig in section.get('figures', []):
            parts.append(self._render_figure(fig))
        
        # Tables
        for table in section.get('tables', []):
            parts.append(self._render_table(table))
        
        # Subsections
        for subsec in subsections:
            parts.append(self._render_section(subsec, level + 1))
        
        parts.append('</section>')
        
        return '\n'.join(parts)
    
    def _process_content(self, content: str) -> str:
        """İçeriği HTML'e dönüştür."""
        lines = content.split('\n')
        result = []
        in_list = False
        in_code_block = False
        code_buffer = []
        code_lang = ''
        
        for line in lines:
            # Code block
            if line.startswith('```'):
                if in_code_block:
                    # End code block
                    code = '\n'.join(code_buffer)
                    result.append(f'<pre><code class="language-{code_lang}">{self._escape(code)}</code></pre>')
                    code_buffer = []
                    in_code_block = False
                else:
                    # Start code block
                    code_lang = line[3:].strip()
                    in_code_block = True
                continue
            
            if in_code_block:
                code_buffer.append(line)
                continue
            
            line = line.strip()
            if not line:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append('')
                continue
            
            # Headings
            if line.startswith('#'):
                level = len(line.split(' ')[0])
                text = line[level:].strip()
                result.append(f'<h{level}>{self._escape(text)}</h{level}>')
                continue
            
            # Lists
            if line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                text = line[2:].strip()
                result.append(f'<li>{self._process_inline(text)}</li>')
                continue
            
            # Paragraph
            if in_list:
                result.append('</ul>')
                in_list = False
            
            result.append(f'<p>{self._process_inline(line)}</p>')
        
        if in_list:
            result.append('</ul>')
        
        return '\n'.join(result)
    
    def _process_inline(self, text: str) -> str:
        """Inline formatting."""
        # Bold
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        # Code
        text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
        # Links
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
        
        return text
    
    def _render_figure(self, figure: Dict[str, Any]) -> str:
        """Şekil render et."""
        src = figure.get('src', figure.get('path', ''))
        alt = figure.get('alt', figure.get('caption', ''))
        caption = figure.get('caption', '')
        
        parts = ['<figure>']
        
        if figure.get('svg'):
            parts.append(figure['svg'])
        else:
            parts.append(f'<img src="{self._escape(src)}" alt="{self._escape(alt)}" loading="lazy">')
        
        if caption:
            parts.append(f'<figcaption>{self._escape(caption)}</figcaption>')
        
        parts.append('</figure>')
        
        return '\n'.join(parts)
    
    def _render_table(self, table: Dict[str, Any]) -> str:
        """Tablo render et."""
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        caption = table.get('caption', '')
        
        parts = ['<table>']
        
        if caption:
            parts.append(f'<caption>{self._escape(caption)}</caption>')
        
        if headers:
            parts.append('<thead><tr>')
            for h in headers:
                parts.append(f'<th>{self._escape(str(h))}</th>')
            parts.append('</tr></thead>')
        
        if rows:
            parts.append('<tbody>')
            for row in rows:
                parts.append('<tr>')
                for cell in row:
                    parts.append(f'<td>{self._escape(str(cell))}</td>')
                parts.append('</tr>')
            parts.append('</tbody>')
        
        parts.append('</table>')
        
        return '\n'.join(parts)
    
    def _generate_css(self) -> str:
        """CSS oluştur."""
        s = self.style
        
        return f'''
        :root {{
            --primary-color: {s.primary_color};
            --accent-color: {s.accent_color};
            --background-color: {s.background_color};
            --text-color: {s.text_color};
        }}
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: {s.font_family};
            font-size: {s.font_size};
            line-height: {s.line_height};
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }}
        
        .document {{
            max-width: {s.max_width};
            margin: 0 auto;
            padding: 40px;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        
        .document-header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 2px solid var(--accent-color);
        }}
        
        .title {{
            font-family: {s.heading_font};
            font-size: 2.5em;
            color: var(--primary-color);
            margin-bottom: 10px;
        }}
        
        .authors {{
            font-size: 1.1em;
            color: #666;
        }}
        
        .date {{
            font-size: 0.9em;
            color: #888;
            margin-top: 10px;
        }}
        
        .abstract {{
            background: #f8f9fa;
            padding: 20px;
            border-left: 4px solid var(--accent-color);
            margin: 20px 0;
            text-align: left;
        }}
        
        .keywords {{
            font-size: 0.9em;
            color: #666;
            margin-top: 15px;
            text-align: left;
        }}
        
        .table-of-contents {{
            background: #f8f9fa;
            padding: 20px 30px;
            margin: 30px 0;
            border-radius: 5px;
        }}
        
        .table-of-contents h2 {{
            margin-top: 0;
            font-size: 1.2em;
        }}
        
        .table-of-contents ul {{
            list-style: none;
            padding-left: 20px;
        }}
        
        .table-of-contents a {{
            color: var(--accent-color);
            text-decoration: none;
        }}
        
        .table-of-contents a:hover {{
            text-decoration: underline;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            font-family: {s.heading_font};
            color: var(--primary-color);
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        
        h2 {{
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        
        p {{
            text-align: justify;
            margin-bottom: 1em;
        }}
        
        a {{
            color: var(--accent-color);
        }}
        
        code {{
            font-family: {s.code_font};
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: inherit;
        }}
        
        figure {{
            margin: 30px 0;
            text-align: center;
        }}
        
        figure img {{
            max-width: 100%;
            height: auto;
        }}
        
        figcaption {{
            font-size: 0.9em;
            color: #666;
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
            padding: 12px;
            text-align: left;
        }}
        
        th {{
            background: var(--primary-color);
            color: white;
        }}
        
        tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        caption {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            .document {{
                padding: 20px;
            }}
            
            .title {{
                font-size: 1.8em;
            }}
            
            table {{
                font-size: 0.9em;
            }}
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .document {{
                box-shadow: none;
                max-width: none;
            }}
            
            .table-of-contents {{
                page-break-after: always;
            }}
        }}
        '''
    
    def _escape(self, text: str) -> str:
        """HTML escape."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def _slugify(self, text: str) -> str:
        """URL-friendly slug oluştur."""
        slug = text.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug.strip('-')
        return slug or 'section'
