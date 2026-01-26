"""
LaTeXExporter - Akademik LaTeX Dışa Aktarma
==========================================

Akademik standartlara uygun LaTeX çıktısı.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class DocumentClass(str, Enum):
    """LaTeX doküman sınıfları."""
    ARTICLE = "article"
    REPORT = "report"
    BOOK = "book"
    IEEEtran = "IEEEtran"
    ACM = "acmart"


@dataclass
class LaTeXStyle:
    """LaTeX stil ayarları."""
    document_class: DocumentClass = DocumentClass.ARTICLE
    font_size: int = 11
    paper: str = "a4paper"
    
    # Paketler
    use_hyperref: bool = True
    use_graphicx: bool = True
    use_amsmath: bool = True
    use_natbib: bool = True
    use_listings: bool = True
    
    # Dil
    language: str = "turkish"
    
    # Bibliografi
    bibliography_style: str = "plain"


@dataclass
class LaTeXDocument:
    """LaTeX dokümanı."""
    title: str
    authors: List[Dict[str, str]] = field(default_factory=list)  # name, affiliation, email
    abstract: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    appendices: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LaTeXExporter:
    """
    Akademik LaTeX Dışa Aktarma Modülü
    
    Derlenebilir LaTeX kaynak kodu üretir.
    """
    
    def __init__(self, style: Optional[LaTeXStyle] = None):
        self.style = style or LaTeXStyle()
        
        # Özel karakter escape map
        self.escape_map = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}'
        }
    
    def export(
        self,
        document: LaTeXDocument,
        output_path: Optional[str] = None
    ) -> str:
        """
        LaTeX olarak dışa aktar.
        
        Args:
            document: LaTeX dokümanı
            output_path: Çıktı dosya yolu
            
        Returns:
            LaTeX kaynak kodu
        """
        latex = self._build_document(document)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(latex)
        
        return latex
    
    def _build_document(self, document: LaTeXDocument) -> str:
        """Tam LaTeX dokümanı oluştur."""
        parts = []
        
        # Preamble
        parts.append(self._create_preamble())
        
        # Title, authors
        parts.append(self._create_title_section(document))
        
        # Document begin
        parts.append(r'\begin{document}')
        parts.append(r'\maketitle')
        
        # Abstract
        if document.abstract:
            parts.append(self._create_abstract(document.abstract, document.keywords))
        
        # Sections
        for section in document.sections:
            parts.append(self._render_section(section))
        
        # References
        if document.references:
            parts.append(self._create_bibliography(document.references))
        
        # Appendices
        if document.appendices:
            parts.append(r'\appendix')
            for appendix in document.appendices:
                parts.append(self._render_section(appendix))
        
        # Document end
        parts.append(r'\end{document}')
        
        return '\n\n'.join(parts)
    
    def _create_preamble(self) -> str:
        """Preamble oluştur."""
        style = self.style
        
        lines = [
            f'\\documentclass[{style.font_size}pt,{style.paper}]{{{style.document_class.value}}}'
        ]
        
        # Encoding
        lines.append(r'\usepackage[utf8]{inputenc}')
        lines.append(r'\usepackage[T1]{fontenc}')
        
        # Dil
        if style.language:
            lines.append(f'\\usepackage[{style.language}]{{babel}}')
        
        # Paketler
        if style.use_graphicx:
            lines.append(r'\usepackage{graphicx}')
        
        if style.use_amsmath:
            lines.append(r'\usepackage{amsmath}')
            lines.append(r'\usepackage{amssymb}')
        
        if style.use_hyperref:
            lines.append(r'\usepackage{hyperref}')
            lines.append(r'\hypersetup{colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue}')
        
        if style.use_natbib:
            lines.append(r'\usepackage{natbib}')
        
        if style.use_listings:
            lines.append(r'\usepackage{listings}')
            lines.append(r'\lstset{basicstyle=\ttfamily\small,breaklines=true}')
        
        # Ekstra paketler
        lines.extend([
            r'\usepackage{booktabs}',
            r'\usepackage{array}',
            r'\usepackage{float}',
            r'\usepackage{caption}',
            r'\usepackage{subcaption}'
        ])
        
        return '\n'.join(lines)
    
    def _create_title_section(self, document: LaTeXDocument) -> str:
        """Başlık bölümü oluştur."""
        lines = []
        
        # LaTeX escape sequences
        latex_newline = r' \\ '
        latex_and = r' \and '
        
        # Title
        title_escaped = self._escape(document.title)
        lines.append(r'\title{' + title_escaped + '}')
        
        # Authors
        if document.authors:
            author_strs = []
            for author in document.authors:
                name = self._escape(author.get('name', ''))
                affiliation = author.get('affiliation', '')
                email = author.get('email', '')
                
                author_str = name
                if affiliation:
                    author_str += latex_newline + self._escape(affiliation)
                if email:
                    author_str += latex_newline + r'\texttt{' + self._escape(email) + '}'
                
                author_strs.append(author_str)
            
            lines.append(r'\author{' + latex_and.join(author_strs) + '}')
        
        # Date
        date = document.metadata.get('date', r'\today')
        lines.append(r'\date{' + date + '}')
        
        return '\n'.join(lines)
    
    def _create_abstract(self, abstract: str, keywords: List[str]) -> str:
        """Özet oluştur."""
        parts = [
            r'\begin{abstract}',
            self._escape(abstract),
            r'\end{abstract}'
        ]
        
        if keywords:
            kw_str = ', '.join(self._escape(k) for k in keywords)
            parts.append(f'\\textbf{{Anahtar Kelimeler:}} {kw_str}')
        
        return '\n'.join(parts)
    
    def _render_section(self, section: Dict[str, Any], level: int = 0) -> str:
        """Bölüm render et."""
        parts = []
        
        title = section.get('title', '')
        content = section.get('content', '')
        subsections = section.get('subsections', [])
        
        # Heading command
        section_cmds = ['section', 'subsection', 'subsubsection', 'paragraph', 'subparagraph']
        cmd = section_cmds[min(level, len(section_cmds) - 1)]
        
        if title:
            parts.append('\\' + cmd + '{' + self._escape(title) + '}')
        
        # Content
        if content:
            parts.append(self._process_content(content))
        
        # Figures
        for fig in section.get('figures', []):
            parts.append(self._render_figure(fig))
        
        # Tables
        for table in section.get('tables', []):
            parts.append(self._render_table(table))
        
        # Subsections
        for subsec in subsections:
            parts.append(self._render_section(subsec, level + 1))
        
        return '\n\n'.join(parts)
    
    def _process_content(self, content: str) -> str:
        """İçeriği işle."""
        # Paragrafları ayır
        paragraphs = content.split('\n\n')
        processed = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Kod bloğu
            if para.startswith('```'):
                code = para.strip('`').strip()
                lang = ''
                if '\n' in code:
                    first_line, code = code.split('\n', 1)
                    if not first_line.startswith(' '):
                        lang = first_line
                        code = code.strip()
                processed.append(r'\begin{lstlisting}[language=' + lang + ']\n' + code + r'\end{lstlisting}')
            
            # Liste
            elif para.startswith('- ') or para.startswith('* '):
                items = [line.lstrip('- *').strip() for line in para.split('\n') if line.strip()]
                item_strs = [r'\item ' + self._escape(item) for item in items]
                processed.append(r'\begin{itemize}' + '\n' + '\n'.join(item_strs) + '\n' + r'\end{itemize}')
            
            # Numaralı liste
            elif para[0].isdigit() and para[1:3] in ['. ', ') ']:
                items = []
                for line in para.split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        # İlk sayı ve noktayı/parantezi kaldır
                        line = re.sub(r'^\d+[\.\)]\s*', '', line)
                        items.append(line)
                item_strs = [r'\item ' + self._escape(item) for item in items]
                processed.append(r'\begin{enumerate}' + '\n' + '\n'.join(item_strs) + '\n' + r'\end{enumerate}')
            
            # Normal paragraf
            else:
                processed.append(self._escape(para))
        
        return '\n\n'.join(processed)
    
    def _render_figure(self, figure: Dict[str, Any]) -> str:
        """Şekil render et."""
        path = figure.get('path', 'figure')
        caption = figure.get('caption', '')
        label = figure.get('label', '')
        width = figure.get('width', '0.8\\textwidth')
        
        lines = [
            r'\begin{figure}[htbp]',
            r'\centering',
            r'\includegraphics[width=' + width + ']{' + path + '}',
        ]
        
        if caption:
            lines.append(r'\caption{' + self._escape(caption) + '}')
        
        if label:
            lines.append(r'\label{fig:' + label + '}')
        
        lines.append(r'\end{figure}')
        
        return '\n'.join(lines)
    
    def _render_table(self, table: Dict[str, Any]) -> str:
        """Tablo render et."""
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        caption = table.get('caption', '')
        label = table.get('label', '')
        
        if not headers and not rows:
            return ''
        
        n_cols = len(headers) if headers else len(rows[0]) if rows else 0
        col_spec = 'l' * n_cols
        
        lines = [
            r'\begin{table}[htbp]',
            r'\centering',
        ]
        
        if caption:
            lines.append(r'\caption{' + self._escape(caption) + '}')
        
        if label:
            lines.append(r'\label{tab:' + label + '}')
        
        lines.append(r'\begin{tabular}{' + col_spec + '}')
        lines.append(r'\toprule')
        
        if headers:
            header_row = ' & '.join(r'\textbf{' + self._escape(h) + '}' for h in headers)
            lines.append(header_row + r' \\')
            lines.append(r'\midrule')
        
        for row in rows:
            row_str = ' & '.join(self._escape(str(cell)) for cell in row)
            lines.append(row_str + r' \\')
        
        lines.append(r'\bottomrule')
        lines.append(r'\end{tabular}')
        lines.append(r'\end{table}')
        
        return '\n'.join(lines)
    
    def _create_bibliography(self, references: List[Dict[str, Any]]) -> str:
        """Kaynakça oluştur."""
        lines = [
            r'\begin{thebibliography}{99}'
        ]
        
        for i, ref in enumerate(references):
            key = ref.get('key', f'ref{i+1}')
            text = ref.get('text', ref.get('citation', ''))
            
            if isinstance(text, dict):
                # Structured reference
                authors = text.get('authors', '')
                title = text.get('title', '')
                year = text.get('year', '')
                journal = text.get('journal', '')
                
                citation = f'{authors}. {title}. \\textit{{{journal}}}, {year}.'
            else:
                citation = self._escape(str(text))
            
            lines.append(f'\\bibitem{{{key}}} {citation}')
        
        lines.append(r'\end{thebibliography}')
        
        return '\n'.join(lines)
    
    def _escape(self, text: str) -> str:
        """LaTeX özel karakterlerini escape et."""
        if not text:
            return ""
        
        result = text
        
        # Özel karakterleri escape et (sıralama önemli)
        result = result.replace('\\', r'\textbackslash{}')
        
        for char, escaped in self.escape_map.items():
            if char != '\\':  # Backslash zaten işlendi
                result = result.replace(char, escaped)
        
        return result
    
    def generate_bibtex(self, references: List[Dict[str, Any]]) -> str:
        """BibTeX dosyası oluştur."""
        entries = []
        
        for ref in references:
            entry_type = ref.get('type', 'article')
            key = ref.get('key', 'ref')
            
            fields = []
            for field_name in ['author', 'title', 'journal', 'year', 'volume', 'pages', 'doi', 'url', 'publisher']:
                if field_name in ref:
                    value = ref[field_name]
                    fields.append(f'  {field_name} = {{{value}}}')
            
            entry = f'@{entry_type}{{{key},\n' + ',\n'.join(fields) + '\n}'
            entries.append(entry)
        
        return '\n\n'.join(entries)
