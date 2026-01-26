"""
PresentationGenerator - Sunum Slaytları Oluşturma
================================================

Akademik sunumlar için slayt oluşturma.
HTML reveal.js ve Markdown formatları desteklenir.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class PresentationFormat(str, Enum):
    """Sunum formatları."""
    REVEAL_JS = "reveal_js"
    MARP = "marp"          # Markdown Presentation
    BEAMER = "beamer"      # LaTeX Beamer
    HTML = "html"


class SlideLayout(str, Enum):
    """Slayt düzenleri."""
    TITLE = "title"
    CONTENT = "content"
    TWO_COLUMN = "two_column"
    IMAGE = "image"
    QUOTE = "quote"
    CODE = "code"
    COMPARISON = "comparison"
    BULLET_POINTS = "bullet_points"


@dataclass
class PresentationStyle:
    """Sunum stil ayarları."""
    theme: str = "white"  # reveal.js themes: white, black, league, beige, sky, night, serif, simple
    
    # Renkler
    primary_color: str = "#2c3e50"
    accent_color: str = "#3498db"
    background_color: str = "#ffffff"
    
    # Yazı tipleri
    title_font: str = "Georgia, serif"
    body_font: str = "system-ui, sans-serif"
    code_font: str = "Consolas, monospace"
    
    # Boyutlar
    width: int = 1920
    height: int = 1080
    
    # Geçiş efektleri
    transition: str = "slide"  # none, fade, slide, convex, concave, zoom


@dataclass
class Slide:
    """Slayt."""
    layout: SlideLayout = SlideLayout.CONTENT
    title: Optional[str] = None
    content: Optional[str] = None
    bullets: List[str] = field(default_factory=list)
    image: Optional[str] = None
    image_caption: Optional[str] = None
    code: Optional[str] = None
    code_language: str = "python"
    left_content: Optional[str] = None
    right_content: Optional[str] = None
    notes: Optional[str] = None
    background: Optional[str] = None


@dataclass
class Presentation:
    """Sunum."""
    title: str
    subtitle: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    date: Optional[str] = None
    institution: Optional[str] = None
    slides: List[Slide] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PresentationGenerator:
    """
    Sunum Slaytları Oluşturma Modülü
    
    Akademik içerikten profesyonel sunumlar oluşturur.
    """
    
    def __init__(
        self,
        format: PresentationFormat = PresentationFormat.REVEAL_JS,
        style: Optional[PresentationStyle] = None
    ):
        self.format = format
        self.style = style or PresentationStyle()
    
    def generate(
        self,
        presentation: Presentation,
        output_path: Optional[str] = None
    ) -> str:
        """
        Sunum oluştur.
        
        Args:
            presentation: Sunum
            output_path: Çıktı dosya yolu
            
        Returns:
            Sunum içeriği
        """
        if self.format == PresentationFormat.REVEAL_JS:
            content = self._generate_reveal_js(presentation)
        elif self.format == PresentationFormat.MARP:
            content = self._generate_marp(presentation)
        elif self.format == PresentationFormat.BEAMER:
            content = self._generate_beamer(presentation)
        else:
            content = self._generate_html(presentation)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return content
    
    def from_document_sections(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        authors: Optional[List[str]] = None,
        max_bullets_per_slide: int = 5
    ) -> Presentation:
        """
        Doküman bölümlerinden sunum oluştur.
        
        Args:
            title: Sunum başlığı
            sections: Bölümler
            authors: Yazarlar
            max_bullets_per_slide: Slayt başına maksimum madde
            
        Returns:
            Sunum
        """
        slides = []
        
        for section in sections:
            sec_title = section.get('title', '')
            content = section.get('content', '')
            
            # Bölüm başlığı slaytı
            slides.append(Slide(
                layout=SlideLayout.TITLE,
                title=sec_title
            ))
            
            # İçerik slaytları
            paragraphs = content.split('\n\n')
            current_bullets = []
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                # Madde işaretli mi?
                if para.startswith('- ') or para.startswith('* '):
                    items = [line.lstrip('- *').strip() for line in para.split('\n') if line.strip()]
                    current_bullets.extend(items)
                else:
                    # Özet cümle olarak ekle
                    current_bullets.append(self._summarize(para))
                
                # Slayt doldu mu?
                if len(current_bullets) >= max_bullets_per_slide:
                    slides.append(Slide(
                        layout=SlideLayout.BULLET_POINTS,
                        title=sec_title,
                        bullets=current_bullets[:max_bullets_per_slide]
                    ))
                    current_bullets = current_bullets[max_bullets_per_slide:]
            
            # Kalan maddeler
            if current_bullets:
                slides.append(Slide(
                    layout=SlideLayout.BULLET_POINTS,
                    title=sec_title,
                    bullets=current_bullets
                ))
        
        return Presentation(
            title=title,
            authors=authors or [],
            slides=slides
        )
    
    def _generate_reveal_js(self, presentation: Presentation) -> str:
        """Reveal.js formatında sunum oluştur."""
        style = self.style
        
        slides_html = []
        
        # Title slide
        title_slide = f'''
<section>
    <h1>{self._escape(presentation.title)}</h1>
    {f'<h3>{self._escape(presentation.subtitle)}</h3>' if presentation.subtitle else ''}
    {f'<p>{", ".join(self._escape(a) for a in presentation.authors)}</p>' if presentation.authors else ''}
    {f'<p><em>{self._escape(presentation.institution)}</em></p>' if presentation.institution else ''}
    {f'<p><small>{self._escape(presentation.date)}</small></p>' if presentation.date else ''}
</section>'''
        slides_html.append(title_slide)
        
        # Content slides
        for slide in presentation.slides:
            slides_html.append(self._render_reveal_slide(slide))
        
        slides_content = '\n'.join(slides_html)
        
        return f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape(presentation.title)}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/{style.theme}.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/plugin/highlight/monokai.css">
    <style>
        .reveal h1, .reveal h2, .reveal h3 {{
            font-family: {style.title_font};
            color: {style.primary_color};
        }}
        .reveal {{
            font-family: {style.body_font};
        }}
        .reveal pre code {{
            font-family: {style.code_font};
        }}
        .two-column {{
            display: flex;
            gap: 40px;
        }}
        .two-column > div {{
            flex: 1;
        }}
        .slide-quote {{
            font-size: 1.5em;
            font-style: italic;
            border-left: 5px solid {style.accent_color};
            padding-left: 30px;
        }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
            {slides_content}
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/plugin/highlight/highlight.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/plugin/notes/notes.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            transition: '{style.transition}',
            plugins: [RevealHighlight, RevealNotes]
        }});
    </script>
</body>
</html>'''
    
    def _render_reveal_slide(self, slide: Slide) -> str:
        """Reveal.js slaytı render et."""
        bg_attr = f' data-background-color="{slide.background}"' if slide.background else ''
        
        if slide.layout == SlideLayout.TITLE:
            return f'''
<section{bg_attr}>
    <h2>{self._escape(slide.title or '')}</h2>
    {f'<p>{self._escape(slide.content)}</p>' if slide.content else ''}
</section>'''
        
        elif slide.layout == SlideLayout.BULLET_POINTS:
            bullets = '\n'.join(f'<li class="fragment">{self._escape(b)}</li>' for b in slide.bullets)
            return f'''
<section{bg_attr}>
    <h3>{self._escape(slide.title or '')}</h3>
    <ul>
        {bullets}
    </ul>
    {f'<aside class="notes">{self._escape(slide.notes)}</aside>' if slide.notes else ''}
</section>'''
        
        elif slide.layout == SlideLayout.TWO_COLUMN:
            return f'''
<section{bg_attr}>
    <h3>{self._escape(slide.title or '')}</h3>
    <div class="two-column">
        <div>{slide.left_content or ''}</div>
        <div>{slide.right_content or ''}</div>
    </div>
</section>'''
        
        elif slide.layout == SlideLayout.IMAGE:
            return f'''
<section{bg_attr}>
    <h3>{self._escape(slide.title or '')}</h3>
    <img src="{self._escape(slide.image or '')}" alt="{self._escape(slide.image_caption or '')}">
    {f'<p><small>{self._escape(slide.image_caption)}</small></p>' if slide.image_caption else ''}
</section>'''
        
        elif slide.layout == SlideLayout.CODE:
            return f'''
<section{bg_attr}>
    <h3>{self._escape(slide.title or '')}</h3>
    <pre><code data-trim data-noescape class="language-{slide.code_language}">
{self._escape(slide.code or '')}
    </code></pre>
</section>'''
        
        elif slide.layout == SlideLayout.QUOTE:
            return f'''
<section{bg_attr}>
    <blockquote class="slide-quote">
        {self._escape(slide.content or '')}
    </blockquote>
</section>'''
        
        else:  # CONTENT
            return f'''
<section{bg_attr}>
    <h3>{self._escape(slide.title or '')}</h3>
    <p>{self._escape(slide.content or '')}</p>
</section>'''
    
    def _generate_marp(self, presentation: Presentation) -> str:
        """Marp (Markdown) formatında sunum oluştur."""
        lines = [
            '---',
            'marp: true',
            f'theme: {self.style.theme}',
            'paginate: true',
            '---',
            '',
            f'# {presentation.title}',
        ]
        
        if presentation.subtitle:
            lines.append(f'\n## {presentation.subtitle}')
        
        if presentation.authors:
            lines.append(f'\n**{", ".join(presentation.authors)}**')
        
        if presentation.institution:
            lines.append(f'\n*{presentation.institution}*')
        
        if presentation.date:
            lines.append(f'\n{presentation.date}')
        
        for slide in presentation.slides:
            lines.append('\n---\n')
            
            if slide.title:
                if slide.layout == SlideLayout.TITLE:
                    lines.append(f'# {slide.title}')
                else:
                    lines.append(f'## {slide.title}')
            
            if slide.content:
                lines.append(f'\n{slide.content}')
            
            if slide.bullets:
                lines.append('')
                for bullet in slide.bullets:
                    lines.append(f'- {bullet}')
            
            if slide.code:
                lines.append(f'\n```{slide.code_language}')
                lines.append(slide.code)
                lines.append('```')
            
            if slide.image:
                lines.append(f'\n![{slide.image_caption or ""}]({slide.image})')
        
        return '\n'.join(lines)
    
    def _generate_beamer(self, presentation: Presentation) -> str:
        """LaTeX Beamer formatında sunum oluştur."""
        lines = [
            r'\documentclass{beamer}',
            r'\usetheme{Madrid}',
            r'\usepackage[utf8]{inputenc}',
            r'\usepackage[turkish]{babel}',
            '',
            f'\\title{{{self._escape_latex(presentation.title)}}}',
        ]
        
        if presentation.subtitle:
            lines.append(f'\\subtitle{{{self._escape_latex(presentation.subtitle)}}}')
        
        if presentation.authors:
            lines.append(f'\\author{{{", ".join(self._escape_latex(a) for a in presentation.authors)}}}')
        
        if presentation.institution:
            lines.append(f'\\institute{{{self._escape_latex(presentation.institution)}}}')
        
        if presentation.date:
            lines.append(f'\\date{{{self._escape_latex(presentation.date)}}}')
        else:
            lines.append(r'\date{\today}')
        
        lines.extend([
            '',
            r'\begin{document}',
            '',
            r'\begin{frame}',
            r'\titlepage',
            r'\end{frame}',
        ])
        
        for slide in presentation.slides:
            lines.append('')
            lines.append(r'\begin{frame}')
            
            if slide.title:
                lines.append(f'\\frametitle{{{self._escape_latex(slide.title)}}}')
            
            if slide.content:
                lines.append(self._escape_latex(slide.content))
            
            if slide.bullets:
                lines.append(r'\begin{itemize}')
                for bullet in slide.bullets:
                    lines.append(f'\\item {self._escape_latex(bullet)}')
                lines.append(r'\end{itemize}')
            
            if slide.code:
                lines.append(r'\begin{verbatim}')
                lines.append(slide.code)
                lines.append(r'\end{verbatim}')
            
            lines.append(r'\end{frame}')
        
        lines.extend([
            '',
            r'\end{document}'
        ])
        
        return '\n'.join(lines)
    
    def _generate_html(self, presentation: Presentation) -> str:
        """Basit HTML sunum."""
        # Reveal.js ile aynı, ama CDN'siz
        return self._generate_reveal_js(presentation)
    
    def _summarize(self, text: str, max_length: int = 100) -> str:
        """Metni özetle."""
        if len(text) <= max_length:
            return text
        
        # İlk cümleyi al
        sentences = re.split(r'[.!?]', text)
        if sentences and len(sentences[0]) <= max_length:
            return sentences[0].strip() + '.'
        
        # Kısalt
        return text[:max_length-3].rsplit(' ', 1)[0] + '...'
    
    def _escape(self, text: str) -> str:
        """HTML escape."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))
    
    def _escape_latex(self, text: str) -> str:
        """LaTeX escape."""
        if not text:
            return ""
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text
