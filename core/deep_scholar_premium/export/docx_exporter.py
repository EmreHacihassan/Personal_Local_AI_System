"""
DOCXExporter - Microsoft Word Dışa Aktarma
==========================================

python-docx kullanarak Word formatında doküman oluşturma.
Harici bağımlılık gerektirmeden XML tabanlı DOCX oluşturma.
"""

import io
import zipfile
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree as ET


@dataclass
class DOCXStyle:
    """DOCX stil ayarları."""
    font_name: str = "Calibri"
    title_size: int = 32  # Half-points (16pt)
    heading1_size: int = 28
    heading2_size: int = 24
    body_size: int = 22  # 11pt
    
    line_spacing: int = 276  # 1.15 line spacing (240 = 1.0)
    
    # Renkler (RGB hex)
    primary_color: str = "000000"
    accent_color: str = "1F4E79"


@dataclass
class DOCXDocument:
    """Word dokümanı."""
    title: str
    sections: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]] = None


class DOCXExporter:
    """
    Microsoft Word Dışa Aktarma Modülü
    
    OOXML (Office Open XML) formatında DOCX oluşturur.
    python-docx kütüphanesi olmadan çalışır.
    """
    
    # XML namespaces
    NAMESPACES = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
        'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcterms': 'http://purl.org/dc/terms/'
    }
    
    def __init__(self, style: Optional[DOCXStyle] = None):
        self.style = style or DOCXStyle()
    
    def export(
        self,
        document: DOCXDocument,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        DOCX olarak dışa aktar.
        
        Args:
            document: Word dokümanı
            output_path: Çıktı dosya yolu
            
        Returns:
            DOCX bytes
        """
        # ZIP dosyası olarak DOCX oluştur
        buffer = io.BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # [Content_Types].xml
            zf.writestr('[Content_Types].xml', self._create_content_types())
            
            # _rels/.rels
            zf.writestr('_rels/.rels', self._create_rels())
            
            # word/_rels/document.xml.rels
            zf.writestr('word/_rels/document.xml.rels', self._create_document_rels())
            
            # word/document.xml
            zf.writestr('word/document.xml', self._create_document(document))
            
            # word/styles.xml
            zf.writestr('word/styles.xml', self._create_styles())
            
            # docProps/core.xml
            zf.writestr('docProps/core.xml', self._create_core_properties(document))
            
            # docProps/app.xml
            zf.writestr('docProps/app.xml', self._create_app_properties())
        
        docx_bytes = buffer.getvalue()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(docx_bytes)
        
        return docx_bytes
    
    def _create_content_types(self) -> str:
        """[Content_Types].xml oluştur."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
    <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
    <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''
    
    def _create_rels(self) -> str:
        """_rels/.rels oluştur."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
    <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    
    def _create_document_rels(self) -> str:
        """word/_rels/document.xml.rels oluştur."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''
    
    def _create_document(self, document: DOCXDocument) -> str:
        """word/document.xml oluştur."""
        w = self.NAMESPACES['w']
        
        # Paragrafları oluştur
        paragraphs = []
        
        # Başlık
        paragraphs.append(self._create_title_paragraph(document.title))
        
        # Bölümler
        for section in document.sections:
            if section.get('type') == 'heading':
                level = section.get('level', 1)
                paragraphs.append(self._create_heading_paragraph(
                    section.get('content', ''),
                    level
                ))
            else:
                paragraphs.append(self._create_body_paragraph(
                    section.get('content', '')
                ))
        
        paragraphs_xml = '\n'.join(paragraphs)
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
            xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
    <w:body>
        {paragraphs_xml}
        <w:sectPr>
            <w:pgSz w:w="11906" w:h="16838"/>
            <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
        </w:sectPr>
    </w:body>
</w:document>'''
    
    def _create_title_paragraph(self, text: str) -> str:
        """Başlık paragrafı."""
        style = self.style
        return f'''<w:p>
    <w:pPr>
        <w:pStyle w:val="Title"/>
        <w:jc w:val="center"/>
    </w:pPr>
    <w:r>
        <w:rPr>
            <w:rFonts w:ascii="{style.font_name}" w:hAnsi="{style.font_name}"/>
            <w:b/>
            <w:sz w:val="{style.title_size}"/>
            <w:color w:val="{style.accent_color}"/>
        </w:rPr>
        <w:t>{self._escape_xml(text)}</w:t>
    </w:r>
</w:p>'''
    
    def _create_heading_paragraph(self, text: str, level: int) -> str:
        """Başlık paragrafı."""
        style = self.style
        size = style.heading1_size if level == 1 else style.heading2_size
        
        return f'''<w:p>
    <w:pPr>
        <w:pStyle w:val="Heading{level}"/>
        <w:spacing w:before="240" w:after="120"/>
    </w:pPr>
    <w:r>
        <w:rPr>
            <w:rFonts w:ascii="{style.font_name}" w:hAnsi="{style.font_name}"/>
            <w:b/>
            <w:sz w:val="{size}"/>
            <w:color w:val="{style.accent_color}"/>
        </w:rPr>
        <w:t>{self._escape_xml(text)}</w:t>
    </w:r>
</w:p>'''
    
    def _create_body_paragraph(self, text: str) -> str:
        """Gövde paragrafı."""
        style = self.style
        
        # Satır sonlarını işle
        runs = []
        for line in text.split('\n'):
            runs.append(f'''<w:r>
        <w:rPr>
            <w:rFonts w:ascii="{style.font_name}" w:hAnsi="{style.font_name}"/>
            <w:sz w:val="{style.body_size}"/>
        </w:rPr>
        <w:t xml:space="preserve">{self._escape_xml(line)}</w:t>
    </w:r>
    <w:r><w:br/></w:r>''')
        
        return f'''<w:p>
    <w:pPr>
        <w:spacing w:after="200" w:line="{style.line_spacing}" w:lineRule="auto"/>
        <w:jc w:val="both"/>
    </w:pPr>
    {''.join(runs)}
</w:p>'''
    
    def _create_styles(self) -> str:
        """word/styles.xml oluştur."""
        style = self.style
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:docDefaults>
        <w:rPrDefault>
            <w:rPr>
                <w:rFonts w:ascii="{style.font_name}" w:hAnsi="{style.font_name}"/>
                <w:sz w:val="{style.body_size}"/>
            </w:rPr>
        </w:rPrDefault>
    </w:docDefaults>
    
    <w:style w:type="paragraph" w:styleId="Normal">
        <w:name w:val="Normal"/>
        <w:pPr>
            <w:spacing w:after="200" w:line="{style.line_spacing}" w:lineRule="auto"/>
        </w:pPr>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="Title">
        <w:name w:val="Title"/>
        <w:basedOn w:val="Normal"/>
        <w:pPr>
            <w:jc w:val="center"/>
            <w:spacing w:after="480"/>
        </w:pPr>
        <w:rPr>
            <w:b/>
            <w:sz w:val="{style.title_size}"/>
            <w:color w:val="{style.accent_color}"/>
        </w:rPr>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="Heading1">
        <w:name w:val="Heading 1"/>
        <w:basedOn w:val="Normal"/>
        <w:pPr>
            <w:spacing w:before="240" w:after="120"/>
        </w:pPr>
        <w:rPr>
            <w:b/>
            <w:sz w:val="{style.heading1_size}"/>
            <w:color w:val="{style.accent_color}"/>
        </w:rPr>
    </w:style>
    
    <w:style w:type="paragraph" w:styleId="Heading2">
        <w:name w:val="Heading 2"/>
        <w:basedOn w:val="Normal"/>
        <w:pPr>
            <w:spacing w:before="200" w:after="100"/>
        </w:pPr>
        <w:rPr>
            <w:b/>
            <w:sz w:val="{style.heading2_size}"/>
        </w:rPr>
    </w:style>
</w:styles>'''
    
    def _create_core_properties(self, document: DOCXDocument) -> str:
        """docProps/core.xml oluştur."""
        metadata = document.metadata or {}
        now = datetime.now().isoformat()
        
        title = self._escape_xml(document.title)
        creator = self._escape_xml(metadata.get('author', 'DeepScholar Premium'))
        
        return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <dc:title>{title}</dc:title>
    <dc:creator>{creator}</dc:creator>
    <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
    <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''
    
    def _create_app_properties(self) -> str:
        """docProps/app.xml oluştur."""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
    <Application>DeepScholar Premium</Application>
    <AppVersion>2.0</AppVersion>
</Properties>'''
    
    def _escape_xml(self, text: str) -> str:
        """XML karakterlerini escape et."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&apos;'))
