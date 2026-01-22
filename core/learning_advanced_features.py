"""
AI ile Öğren - Gelişmiş İçerik Özellikleri
==========================================

3 Premium Özellik:
14. 🎨 Visual Learning Tools
15. 📹 Multimedia Content Generation  
16. 🔗 Smart Content Linking

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import hashlib
import json
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from threading import Lock
from pathlib import Path
import math

from .logger import get_logger

logger = get_logger("learning_advanced_features")


# =============================================================================
# 14. VISUAL LEARNING TOOLS
# =============================================================================

@dataclass
class MindMapNode:
    """Mind map düğümü."""
    id: str
    label: str
    level: int = 0
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    color: str = "#4A90D9"
    icon: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "level": self.level,
            "parent_id": self.parent_id,
            "children": self.children,
            "color": self.color,
            "icon": self.icon,
            "notes": self.notes
        }


@dataclass
class ConceptRelation:
    """Kavram ilişkisi."""
    source: str
    target: str
    relation_type: str  # "is_a", "part_of", "leads_to", "requires", "related"
    strength: float = 1.0
    label: str = ""


class VisualLearningTools:
    """
    Görsel öğrenme araçları.
    
    Özellikler:
    - Mind-map otomatik oluşturma
    - Kavram haritası (Concept Map)
    - Mermaid diagram üretimi
    - Infografik yapısı
    - Timeline oluşturma
    - Flowchart üretimi
    """
    
    # Renk paleti
    LEVEL_COLORS = [
        "#4A90D9",  # Level 0 - Ana konu (mavi)
        "#7B68EE",  # Level 1 - Alt başlık (mor)
        "#50C878",  # Level 2 - Detay (yeşil)
        "#FFB347",  # Level 3 - Alt detay (turuncu)
        "#FF6B6B",  # Level 4 - Derin detay (kırmızı)
        "#4ECDC4",  # Level 5+ (turkuaz)
    ]
    
    # İlişki türleri
    RELATION_TYPES = {
        "is_a": {"label": "bir türüdür", "arrow": "-->"},
        "part_of": {"label": "parçasıdır", "arrow": "-->"},
        "leads_to": {"label": "yol açar", "arrow": "==>"},
        "requires": {"label": "gerektirir", "arrow": "-.->"},
        "related": {"label": "ilişkili", "arrow": "---"},
        "causes": {"label": "neden olur", "arrow": "==>"},
        "example": {"label": "örneği", "arrow": "-.->"},
        "opposite": {"label": "zıttı", "arrow": "<-->"},
    }
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = Lock()
        logger.info("VisualLearningTools initialized")
    
    def _generate_id(self, text: str) -> str:
        """Unique ID oluştur."""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def _extract_concepts(self, text: str) -> List[Dict[str, Any]]:
        """Metinden kavramları çıkar."""
        concepts = []
        
        # Başlıkları bul (markdown)
        headers = re.findall(r'^(#{1,6})\s+(.+)$', text, re.MULTILINE)
        for hashes, title in headers:
            level = len(hashes) - 1
            concepts.append({
                "text": title.strip(),
                "level": level,
                "type": "header"
            })
        
        # Bold metinleri bul (önemli kavramlar)
        bold_texts = re.findall(r'\*\*([^*]+)\*\*', text)
        for bold in bold_texts:
            if len(bold) < 50:  # Kısa olanlar kavram
                concepts.append({
                    "text": bold.strip(),
                    "level": 2,
                    "type": "concept"
                })
        
        # Liste öğelerini bul
        list_items = re.findall(r'^\s*[-*]\s+(.+)$', text, re.MULTILINE)
        for item in list_items[:20]:  # Max 20 item
            concepts.append({
                "text": item.strip()[:50],
                "level": 3,
                "type": "item"
            })
        
        # Numaralı liste
        numbered = re.findall(r'^\s*\d+\.\s+(.+)$', text, re.MULTILINE)
        for item in numbered[:20]:
            concepts.append({
                "text": item.strip()[:50],
                "level": 3,
                "type": "step"
            })
        
        return concepts
    
    def generate_mind_map(
        self, 
        topic: str, 
        content: str,
        max_depth: int = 4,
        max_children: int = 8
    ) -> Dict[str, Any]:
        """
        İçerikten mind-map oluştur.
        
        Returns:
            {
                "root": MindMapNode,
                "nodes": List[MindMapNode],
                "edges": List[Dict],
                "mermaid": str,
                "html": str
            }
        """
        nodes: Dict[str, MindMapNode] = {}
        edges: List[Dict] = []
        
        # Root node
        root_id = self._generate_id(topic)
        root = MindMapNode(
            id=root_id,
            label=topic,
            level=0,
            color=self.LEVEL_COLORS[0],
            icon="🎯"
        )
        nodes[root_id] = root
        
        # Kavramları çıkar
        concepts = self._extract_concepts(content)
        
        # Parent stack for hierarchy
        parent_stack = [(root_id, 0)]  # (node_id, level)
        
        for concept in concepts:
            text = concept["text"]
            level = min(concept["level"], max_depth)
            
            # Uygun parent'ı bul
            while parent_stack and parent_stack[-1][1] >= level:
                parent_stack.pop()
            
            if not parent_stack:
                parent_stack.append((root_id, 0))
            
            parent_id = parent_stack[-1][0]
            parent_node = nodes[parent_id]
            
            # Max children kontrolü
            if len(parent_node.children) >= max_children:
                continue
            
            # Yeni node oluştur
            node_id = self._generate_id(f"{parent_id}_{text}")
            color = self.LEVEL_COLORS[min(level, len(self.LEVEL_COLORS) - 1)]
            
            node = MindMapNode(
                id=node_id,
                label=text[:40],  # Truncate
                level=level,
                parent_id=parent_id,
                color=color,
                icon=self._get_icon_for_type(concept["type"])
            )
            
            nodes[node_id] = node
            parent_node.children.append(node_id)
            
            edges.append({
                "source": parent_id,
                "target": node_id,
                "type": "child"
            })
            
            parent_stack.append((node_id, level))
        
        # Mermaid diagram
        mermaid = self._generate_mermaid_mindmap(root, nodes)
        
        # HTML visualization
        html = self._generate_mindmap_html(root, nodes)
        
        return {
            "root": root.to_dict(),
            "nodes": [n.to_dict() for n in nodes.values()],
            "node_count": len(nodes),
            "edges": edges,
            "edge_count": len(edges),
            "max_depth": max(n.level for n in nodes.values()),
            "mermaid": mermaid,
            "html": html
        }
    
    def _get_icon_for_type(self, concept_type: str) -> str:
        """Kavram türüne göre ikon."""
        icons = {
            "header": "📌",
            "concept": "💡",
            "item": "•",
            "step": "→",
            "definition": "📖",
            "example": "💫",
        }
        return icons.get(concept_type, "")
    
    def _generate_mermaid_mindmap(
        self, 
        root: MindMapNode, 
        nodes: Dict[str, MindMapNode]
    ) -> str:
        """Mermaid mindmap syntax oluştur."""
        lines = ["mindmap"]
        lines.append(f"  root(({root.label}))")
        
        def add_children(node_id: str, indent: int):
            node = nodes[node_id]
            for child_id in node.children:
                child = nodes[child_id]
                prefix = "  " * (indent + 1)
                
                # Level'a göre şekil
                if child.level == 1:
                    lines.append(f"{prefix}[{child.label}]")
                elif child.level == 2:
                    lines.append(f"{prefix}({child.label})")
                else:
                    lines.append(f"{prefix}{child.label}")
                
                add_children(child_id, indent + 1)
        
        add_children(root.id, 1)
        
        return "\n".join(lines)
    
    def _generate_mindmap_html(
        self, 
        root: MindMapNode, 
        nodes: Dict[str, MindMapNode]
    ) -> str:
        """Mind map için HTML visualization."""
        
        def render_node(node_id: str, depth: int = 0) -> str:
            node = nodes[node_id]
            indent = "  " * depth
            
            children_html = ""
            if node.children:
                children_html = f"""
{indent}  <ul class="mm-children">
{chr(10).join(render_node(c, depth + 2) for c in node.children)}
{indent}  </ul>"""
            
            return f"""{indent}<li class="mm-node mm-level-{node.level}">
{indent}  <div class="mm-content" style="background-color:{node.color}">
{indent}    <span class="mm-icon">{node.icon}</span>
{indent}    <span class="mm-label">{node.label}</span>
{indent}  </div>{children_html}
{indent}</li>"""
        
        return f"""
<div class="mindmap-container">
<style>
.mindmap-container {{ font-family: Arial, sans-serif; }}
.mm-children {{ list-style: none; padding-left: 20px; margin: 5px 0; }}
.mm-node {{ margin: 5px 0; }}
.mm-content {{
    display: inline-block;
    padding: 8px 16px;
    border-radius: 20px;
    color: white;
    font-weight: 500;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}}
.mm-level-0 .mm-content {{ font-size: 18px; padding: 12px 24px; }}
.mm-level-1 .mm-content {{ font-size: 14px; }}
.mm-level-2 .mm-content {{ font-size: 12px; opacity: 0.95; }}
.mm-level-3 .mm-content {{ font-size: 11px; opacity: 0.9; }}
.mm-icon {{ margin-right: 6px; }}
</style>
<ul class="mm-children">
{render_node(root.id, 1)}
</ul>
</div>
"""
    
    def generate_concept_map(
        self, 
        topic: str, 
        content: str,
        include_relations: bool = True
    ) -> Dict[str, Any]:
        """
        Kavram haritası oluştur.
        
        Kavramlar arası ilişkileri gösterir.
        """
        concepts = self._extract_concepts(content)
        
        nodes = []
        edges = []
        
        # Ana konu
        main_id = self._generate_id(topic)
        nodes.append({
            "id": main_id,
            "label": topic,
            "type": "main",
            "level": 0,
            "x": 400,
            "y": 300
        })
        
        # Kavramları düzenle
        angle_step = 2 * math.pi / max(len(concepts), 1)
        radius = 200
        
        for i, concept in enumerate(concepts[:15]):  # Max 15 concept
            node_id = self._generate_id(concept["text"])
            angle = i * angle_step
            
            x = 400 + radius * math.cos(angle)
            y = 300 + radius * math.sin(angle)
            
            nodes.append({
                "id": node_id,
                "label": concept["text"][:30],
                "type": concept["type"],
                "level": concept["level"],
                "x": int(x),
                "y": int(y)
            })
            
            # Ana konuya bağla
            edges.append({
                "source": main_id,
                "target": node_id,
                "relation": "contains",
                "label": ""
            })
        
        # Kavramlar arası ilişkileri bul
        if include_relations:
            for i, n1 in enumerate(nodes[1:], 1):
                for j, n2 in enumerate(nodes[i+1:], i+1):
                    # Basit ilişki tespiti (ortak kelimeler)
                    words1 = set(n1["label"].lower().split())
                    words2 = set(n2["label"].lower().split())
                    common = words1 & words2
                    
                    if common and len(common) > 0:
                        edges.append({
                            "source": n1["id"],
                            "target": n2["id"],
                            "relation": "related",
                            "label": list(common)[0]
                        })
        
        # Mermaid flowchart
        mermaid = self._generate_mermaid_flowchart(nodes, edges, topic)
        
        return {
            "topic": topic,
            "nodes": nodes,
            "node_count": len(nodes),
            "edges": edges,
            "edge_count": len(edges),
            "mermaid": mermaid
        }
    
    def _generate_mermaid_flowchart(
        self, 
        nodes: List[Dict], 
        edges: List[Dict],
        title: str
    ) -> str:
        """Mermaid flowchart syntax."""
        lines = ["flowchart TB"]
        lines.append(f"    subgraph {title}")
        
        # Node tanımları
        for node in nodes:
            node_id = node["id"]
            label = node["label"].replace('"', "'")
            
            if node["type"] == "main":
                lines.append(f'    {node_id}[("{label}")]')
            elif node["type"] == "header":
                lines.append(f'    {node_id}["{label}"]')
            else:
                lines.append(f'    {node_id}("{label}")')
        
        lines.append("    end")
        
        # Edge tanımları
        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            rel = edge.get("relation", "related")
            
            arrow = self.RELATION_TYPES.get(rel, {}).get("arrow", "-->")
            label = edge.get("label", "")
            
            if label:
                lines.append(f'    {src} {arrow}|{label}| {tgt}')
            else:
                lines.append(f'    {src} {arrow} {tgt}')
        
        return "\n".join(lines)
    
    def generate_timeline(
        self, 
        topic: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Zaman çizelgesi oluştur.
        
        Sıralı olaylar, adımlar için.
        """
        # Numaralı adımları bul
        steps = re.findall(r'(?:^|\n)\s*(\d+)[.):]\s*(.+?)(?=\n\s*\d+[.):]\s*|\n\n|$)', content, re.DOTALL)
        
        if not steps:
            # Bullet points'ten
            items = re.findall(r'^\s*[-*]\s+(.+)$', content, re.MULTILINE)
            steps = [(str(i+1), item) for i, item in enumerate(items[:10])]
        
        events = []
        for i, (num, text) in enumerate(steps[:15]):
            events.append({
                "order": i + 1,
                "number": num,
                "title": text.strip()[:60],
                "description": text.strip(),
                "color": self.LEVEL_COLORS[i % len(self.LEVEL_COLORS)]
            })
        
        # Mermaid timeline
        mermaid_lines = ["timeline", f"    title {topic}"]
        for event in events:
            mermaid_lines.append(f"    {event['title'][:30]}")
        
        return {
            "topic": topic,
            "events": events,
            "event_count": len(events),
            "mermaid": "\n".join(mermaid_lines)
        }
    
    def generate_flowchart(
        self, 
        topic: str, 
        content: str,
        direction: str = "TB"  # TB, LR, BT, RL
    ) -> Dict[str, Any]:
        """
        Akış şeması oluştur.
        
        Süreç, algoritma, karar ağaçları için.
        """
        steps = []
        decisions = []
        
        # Adımları bul
        step_matches = re.findall(r'(?:^|\n)\s*(\d+)[.):]\s*(.+?)(?=\n|$)', content)
        for num, text in step_matches[:12]:
            text_clean = text.strip()
            
            # Karar noktası mı?
            is_decision = any(kw in text_clean.lower() for kw in 
                            ['eğer', 'if', 'ise', 'mı?', 'mi?', 'karar', 'seç'])
            
            if is_decision:
                decisions.append({
                    "id": f"d{num}",
                    "text": text_clean[:40],
                    "type": "decision"
                })
            else:
                steps.append({
                    "id": f"s{num}",
                    "text": text_clean[:40],
                    "type": "process"
                })
        
        # Mermaid flowchart
        mermaid_lines = [f"flowchart {direction}"]
        
        all_nodes = steps + decisions
        for i, node in enumerate(all_nodes):
            if node["type"] == "decision":
                mermaid_lines.append(f'    {node["id"]}{{"{node["text"]}"}}')
            else:
                mermaid_lines.append(f'    {node["id"]}["{node["text"]}"]')
            
            # Sıralı bağlantı
            if i > 0:
                prev = all_nodes[i-1]
                if prev["type"] == "decision":
                    mermaid_lines.append(f'    {prev["id"]} -->|Evet| {node["id"]}')
                else:
                    mermaid_lines.append(f'    {prev["id"]} --> {node["id"]}')
        
        return {
            "topic": topic,
            "steps": steps,
            "decisions": decisions,
            "direction": direction,
            "mermaid": "\n".join(mermaid_lines)
        }
    
    def generate_infographic_structure(
        self, 
        topic: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        İnfografik yapısı oluştur.
        
        Bölümler, istatistikler, önemli noktalar.
        """
        sections = []
        
        # Başlıkları bul
        headers = re.findall(r'^(#{1,3})\s+(.+)$', content, re.MULTILINE)
        
        current_section = None
        for hashes, title in headers:
            level = len(hashes)
            
            if level <= 2:
                if current_section:
                    sections.append(current_section)
                
                current_section = {
                    "title": title.strip(),
                    "level": level,
                    "key_points": [],
                    "statistics": [],
                    "icon": self._suggest_icon(title)
                }
            elif current_section:
                current_section["key_points"].append(title.strip())
        
        if current_section:
            sections.append(current_section)
        
        # Sayıları/istatistikleri bul
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(%|adet|tane|kez|yıl|gün)?', content)
        statistics = []
        for num, unit in numbers[:10]:
            if len(num) <= 6:  # Çok büyük sayıları atla
                statistics.append({
                    "value": num,
                    "unit": unit or "",
                    "display": f"{num}{unit}" if unit else num
                })
        
        # Key points (bold text)
        key_points = re.findall(r'\*\*([^*]+)\*\*', content)[:10]
        
        return {
            "topic": topic,
            "sections": sections,
            "section_count": len(sections),
            "statistics": statistics[:8],
            "key_points": key_points,
            "suggested_layout": self._suggest_infographic_layout(len(sections))
        }
    
    def _suggest_icon(self, text: str) -> str:
        """Başlığa uygun ikon öner."""
        text_lower = text.lower()
        
        icon_map = {
            "giriş": "🚀", "introduction": "🚀", "başlangıç": "🚀",
            "sonuç": "🎯", "conclusion": "🎯", "özet": "📋",
            "örnek": "💡", "example": "💡",
            "uyarı": "⚠️", "warning": "⚠️", "dikkat": "⚠️",
            "ipucu": "💡", "tip": "💡",
            "adım": "👣", "step": "👣",
            "soru": "❓", "question": "❓",
            "cevap": "✅", "answer": "✅",
            "kod": "💻", "code": "💻",
            "kaynak": "📚", "source": "📚", "referans": "📚",
            "tarih": "📅", "history": "📅", "zaman": "⏰",
            "grafik": "📊", "chart": "📊", "istatistik": "📈",
            "liste": "📝", "list": "📝",
            "tanım": "📖", "definition": "📖",
        }
        
        for keyword, icon in icon_map.items():
            if keyword in text_lower:
                return icon
        
        return "📌"
    
    def _suggest_infographic_layout(self, section_count: int) -> str:
        """Bölüm sayısına göre layout öner."""
        if section_count <= 3:
            return "horizontal_blocks"
        elif section_count <= 5:
            return "vertical_timeline"
        elif section_count <= 8:
            return "grid_2x4"
        else:
            return "scrolling_sections"


# =============================================================================
# 15. MULTIMEDIA CONTENT GENERATION
# =============================================================================

@dataclass
class SlideContent:
    """Slayt içeriği."""
    slide_number: int
    title: str
    bullet_points: List[str]
    speaker_notes: str = ""
    visual_suggestion: str = ""
    layout: str = "title_content"  # title_only, title_content, two_column, image_focus


class MultimediaContentGenerator:
    """
    Multimedya içerik üretimi.
    
    Özellikler:
    - Video script oluşturma
    - Slide deck üretimi
    - Podcast script
    - Audio summary
    - Presentation outline
    """
    
    # Slide layouts
    SLIDE_LAYOUTS = {
        "title_only": "Sadece başlık - açılış/kapanış için",
        "title_content": "Başlık + bullet points - standart",
        "two_column": "İki sütun - karşılaştırma için",
        "image_focus": "Görsel odaklı - infografik için",
        "quote": "Alıntı slaytı",
        "statistics": "İstatistik vurgulu"
    }
    
    # Video segment types
    VIDEO_SEGMENTS = {
        "intro": "Giriş - konu tanıtımı",
        "hook": "Dikkat çekici açılış",
        "main": "Ana içerik",
        "example": "Örnek/Demo",
        "summary": "Özet",
        "cta": "Call to action",
        "outro": "Kapanış"
    }
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        logger.info("MultimediaContentGenerator initialized")
    
    def generate_video_script(
        self, 
        topic: str, 
        content: str,
        duration_minutes: int = 10,
        style: str = "educational"  # educational, casual, professional
    ) -> Dict[str, Any]:
        """
        Video script oluştur.
        
        Returns:
            {
                "title": str,
                "duration": int,
                "segments": List[Dict],
                "full_script": str,
                "visual_cues": List[Dict]
            }
        """
        # İçeriği bölümlere ayır
        sections = self._extract_sections(content)
        
        # Segment başına süre hesapla
        total_segments = len(sections) + 2  # +2 for intro and outro
        segment_duration = duration_minutes / total_segments
        
        segments = []
        visual_cues = []
        full_script = []
        
        # INTRO
        intro_script = self._generate_intro_script(topic, style)
        segments.append({
            "type": "intro",
            "duration_seconds": int(segment_duration * 60),
            "title": "Giriş",
            "script": intro_script,
            "visual": "Logo + Konu başlığı animasyonu"
        })
        full_script.append(f"[INTRO - {int(segment_duration * 60)}s]\n{intro_script}\n")
        visual_cues.append({
            "timestamp": "0:00",
            "type": "title_card",
            "description": f"'{topic}' başlığı göster"
        })
        
        # MAIN CONTENT
        current_time = segment_duration
        for i, section in enumerate(sections):
            section_script = self._generate_section_script(section, style)
            
            segments.append({
                "type": "main",
                "duration_seconds": int(segment_duration * 60),
                "title": section["title"],
                "script": section_script,
                "visual": f"Bölüm {i+1} görselleri"
            })
            
            timestamp = f"{int(current_time)}:{int((current_time % 1) * 60):02d}"
            full_script.append(f"[BÖLÜM {i+1}: {section['title']} - {timestamp}]\n{section_script}\n")
            
            visual_cues.append({
                "timestamp": timestamp,
                "type": "section_title",
                "description": f"'{section['title']}' geçişi"
            })
            
            # Key points için görsel cue
            if section.get("key_points"):
                for j, point in enumerate(section["key_points"][:3]):
                    point_time = current_time + (segment_duration / 4) * (j + 1)
                    visual_cues.append({
                        "timestamp": f"{int(point_time)}:{int((point_time % 1) * 60):02d}",
                        "type": "bullet_point",
                        "description": point[:50]
                    })
            
            current_time += segment_duration
        
        # OUTRO
        outro_script = self._generate_outro_script(topic, style)
        segments.append({
            "type": "outro",
            "duration_seconds": int(segment_duration * 60),
            "title": "Kapanış",
            "script": outro_script,
            "visual": "CTA + Logo"
        })
        full_script.append(f"[OUTRO]\n{outro_script}\n")
        
        return {
            "title": topic,
            "duration_minutes": duration_minutes,
            "style": style,
            "segment_count": len(segments),
            "segments": segments,
            "full_script": "\n".join(full_script),
            "word_count": sum(len(s["script"].split()) for s in segments),
            "visual_cues": visual_cues
        }
    
    def _extract_sections(self, content: str) -> List[Dict]:
        """İçeriği bölümlere ayır."""
        sections = []
        
        # Markdown başlıklarına göre böl
        parts = re.split(r'^(#{1,3})\s+(.+)$', content, flags=re.MULTILINE)
        
        current_section = None
        for i, part in enumerate(parts):
            if part.startswith('#'):
                if current_section:
                    sections.append(current_section)
                # Sonraki part başlık
                if i + 1 < len(parts):
                    title = parts[i + 1]
                    current_section = {
                        "title": title.strip(),
                        "content": "",
                        "key_points": []
                    }
            elif current_section and not part.strip().startswith('#'):
                current_section["content"] += part
                # Key points çıkar
                points = re.findall(r'[-*]\s+(.+)', part)
                current_section["key_points"].extend(points)
        
        if current_section:
            sections.append(current_section)
        
        # Eğer başlık yoksa paragrafları kullan
        if not sections:
            paragraphs = content.split('\n\n')
            for i, para in enumerate(paragraphs[:5]):
                if para.strip():
                    first_line = para.split('\n')[0][:50]
                    sections.append({
                        "title": f"Bölüm {i+1}",
                        "content": para,
                        "key_points": []
                    })
        
        return sections[:8]  # Max 8 section
    
    def _generate_intro_script(self, topic: str, style: str) -> str:
        """Giriş scripti."""
        if style == "casual":
            return f"""Merhaba arkadaşlar! Bugün çok heyecan verici bir konuya dalacağız: {topic}.

Bu video boyunca size adım adım her şeyi anlatacağım. Hazırsanız başlayalım!"""
        elif style == "professional":
            return f"""Hoş geldiniz. Bu sunumda {topic} konusunu detaylı olarak ele alacağız.

Öğrenecekleriniz iş hayatınızda ve projelerinizde size büyük fayda sağlayacak."""
        else:  # educational
            return f"""Merhaba! Bu videoda {topic} konusunu birlikte öğreneceğiz.

Video sonunda bu konuyu tam olarak anlamış olacaksınız. Hazırsanız başlayalım!"""
    
    def _generate_section_script(self, section: Dict, style: str) -> str:
        """Bölüm scripti."""
        title = section.get("title", "")
        content = section.get("content", "")[:300]
        points = section.get("key_points", [])
        
        script = f"Şimdi {title} konusuna geçelim.\n\n"
        
        if content:
            # İçeriği konuşma diline çevir
            script += content.replace('\n', ' ').strip()[:200] + "...\n\n"
        
        if points:
            script += "Önemli noktalar:\n"
            for point in points[:3]:
                script += f"- {point.strip()[:50]}\n"
        
        return script
    
    def _generate_outro_script(self, topic: str, style: str) -> str:
        """Kapanış scripti."""
        if style == "casual":
            return f"""İşte bu kadar! {topic} hakkında bilmeniz gerekenleri öğrendiniz.

Videoyu beğendiyseniz like atmayı ve abone olmayı unutmayın. Bir sonraki videoda görüşmek üzere!"""
        elif style == "professional":
            return f"""{topic} konusundaki sunumumuz burada sona eriyor.

Sorularınız için iletişime geçebilirsiniz. Katılımınız için teşekkür ederiz."""
        else:
            return f"""Bugün {topic} konusunu birlikte öğrendik.

Sorularınızı yorumlarda belirtebilirsiniz. Öğrenmeye devam edin!"""
    
    def generate_slide_deck(
        self, 
        topic: str, 
        content: str,
        slide_count: int = 10,
        include_notes: bool = True
    ) -> Dict[str, Any]:
        """
        Slide deck oluştur.
        
        PowerPoint/Google Slides için yapı.
        """
        slides = []
        
        # Title slide
        slides.append(SlideContent(
            slide_number=1,
            title=topic,
            bullet_points=[],
            speaker_notes="Kendinizi tanıtın, konu hakkında kısa bir giriş yapın.",
            visual_suggestion="Çarpıcı arka plan görseli veya tema görseli",
            layout="title_only"
        ))
        
        # Agenda slide
        sections = self._extract_sections(content)
        agenda_points = [s["title"] for s in sections[:6]]
        
        slides.append(SlideContent(
            slide_number=2,
            title="İçerik",
            bullet_points=agenda_points,
            speaker_notes="Bugün ele alacağımız konuları kısaca özetleyin.",
            visual_suggestion="Numbered list veya icons",
            layout="title_content"
        ))
        
        # Content slides
        slide_num = 3
        remaining_slides = slide_count - 4  # -4 for title, agenda, summary, closing
        slides_per_section = max(1, remaining_slides // max(len(sections), 1))
        
        for section in sections:
            # Section title slide
            if slides_per_section >= 2:
                slides.append(SlideContent(
                    slide_number=slide_num,
                    title=section["title"],
                    bullet_points=[],
                    speaker_notes=f"{section['title']} bölümüne geçiş",
                    visual_suggestion="Section divider görseli",
                    layout="title_only"
                ))
                slide_num += 1
            
            # Content slide
            points = section.get("key_points", [])[:5]
            if not points:
                # İçerikten cümleler al
                sentences = re.split(r'[.!?]', section.get("content", ""))
                points = [s.strip()[:60] for s in sentences if s.strip()][:4]
            
            slides.append(SlideContent(
                slide_number=slide_num,
                title=section["title"],
                bullet_points=points,
                speaker_notes=section.get("content", "")[:200],
                visual_suggestion="İlgili ikon veya diagram",
                layout="title_content"
            ))
            slide_num += 1
            
            if slide_num > slide_count - 2:
                break
        
        # Summary slide
        summary_points = [s["title"] for s in sections[:4]]
        slides.append(SlideContent(
            slide_number=slide_num,
            title="Özet",
            bullet_points=summary_points,
            speaker_notes="Ana noktaları tekrar edin.",
            visual_suggestion="Checkmark icons",
            layout="title_content"
        ))
        slide_num += 1
        
        # Closing slide
        slides.append(SlideContent(
            slide_number=slide_num,
            title="Teşekkürler!",
            bullet_points=["Sorular?"],
            speaker_notes="Sorulara açılın, iletişim bilgilerini paylaşın.",
            visual_suggestion="Thank you görseli + contact info",
            layout="title_only"
        ))
        
        return {
            "title": topic,
            "slide_count": len(slides),
            "slides": [self._slide_to_dict(s) for s in slides],
            "estimated_duration": f"{len(slides) * 2}-{len(slides) * 3} dakika",
            "markdown_export": self._slides_to_markdown(slides)
        }
    
    def _slide_to_dict(self, slide: SlideContent) -> Dict:
        """Slide'ı dict'e çevir."""
        return {
            "slide_number": slide.slide_number,
            "title": slide.title,
            "bullet_points": slide.bullet_points,
            "speaker_notes": slide.speaker_notes,
            "visual_suggestion": slide.visual_suggestion,
            "layout": slide.layout
        }
    
    def _slides_to_markdown(self, slides: List[SlideContent]) -> str:
        """Slides'ı markdown'a export et."""
        lines = []
        for slide in slides:
            lines.append(f"---\n## Slayt {slide.slide_number}: {slide.title}\n")
            
            for point in slide.bullet_points:
                lines.append(f"- {point}")
            
            if slide.speaker_notes:
                lines.append(f"\n> 🎤 Not: {slide.speaker_notes[:100]}")
            
            if slide.visual_suggestion:
                lines.append(f"\n> 🖼️ Görsel: {slide.visual_suggestion}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_podcast_script(
        self, 
        topic: str, 
        content: str,
        duration_minutes: int = 15,
        host_count: int = 1,  # 1 = monolog, 2 = dialog
        style: str = "conversational"
    ) -> Dict[str, Any]:
        """
        Podcast script oluştur.
        """
        sections = self._extract_sections(content)
        
        script_parts = []
        timestamps = []
        
        if host_count == 1:
            host = "HOST"
            # Monolog format
            
            # Intro (2 dk)
            script_parts.append(f"""[INTRO - 0:00]
{host}: Merhaba ve podcast'imize hoş geldiniz! Ben [isim] ve bugün çok ilginç bir konuyu konuşacağız: {topic}.

Bu bölümde öğrenecekleriniz hayatınızı değiştirebilir. Hazırsanız başlayalım!
""")
            timestamps.append({"time": "0:00", "section": "Giriş"})
            
            # Main content
            current_time = 2
            segment_time = (duration_minutes - 4) / max(len(sections), 1)
            
            for section in sections:
                time_str = f"{current_time}:{0:02d}"
                
                script_parts.append(f"""[{section['title'].upper()} - {time_str}]
{host}: Şimdi {section['title']} konusuna geçelim.

{section.get('content', '')[:300]}

""")
                timestamps.append({"time": time_str, "section": section["title"]})
                
                for point in section.get("key_points", [])[:2]:
                    script_parts.append(f"{host}: Önemli bir nokta: {point}\n\n")
                
                current_time += int(segment_time)
            
            # Outro
            script_parts.append(f"""[OUTRO - {duration_minutes - 2}:00]
{host}: İşte bugünkü bölümümüz burada sona eriyor. {topic} hakkında umarım faydalı bilgiler edinmişsinizdir.

Bir sonraki bölümde görüşmek üzere. Kendinize iyi bakın!
""")
            timestamps.append({"time": f"{duration_minutes - 2}:00", "section": "Kapanış"})
        
        else:
            # Dialog format (2 hosts)
            script_parts.append(f"""[INTRO - 0:00]
HOST A: Merhaba! Podcast'imize hoş geldiniz.
HOST B: Bugün gerçekten heyecanlıyız çünkü {topic} konuşacağız.
HOST A: Evet, bu konu son zamanlarda çok popüler. Hadi başlayalım!
""")
            
            current_time = 2
            segment_time = (duration_minutes - 4) / max(len(sections), 1)
            
            for i, section in enumerate(sections):
                speaker = "HOST A" if i % 2 == 0 else "HOST B"
                other = "HOST B" if i % 2 == 0 else "HOST A"
                
                script_parts.append(f"""[{section['title'].upper()} - {current_time}:00]
{speaker}: {section['title']} hakkında ne düşünüyorsun?
{other}: Çok ilginç bir konu. {section.get('content', '')[:150]}
{speaker}: Kesinlikle katılıyorum.
""")
                timestamps.append({"time": f"{current_time}:00", "section": section["title"]})
                current_time += int(segment_time)
            
            script_parts.append(f"""[OUTRO]
HOST A: Harika bir sohbetti!
HOST B: Evet, bir sonraki bölümde görüşmek üzere!
""")
        
        full_script = "\n".join(script_parts)
        
        return {
            "title": topic,
            "duration_minutes": duration_minutes,
            "host_count": host_count,
            "style": style,
            "full_script": full_script,
            "word_count": len(full_script.split()),
            "timestamps": timestamps,
            "estimated_reading_time": len(full_script.split()) // 150  # ~150 wpm
        }
    
    def generate_audio_summary(
        self, 
        topic: str, 
        content: str,
        duration_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Kısa audio özet scripti.
        
        1 dakikalık TL;DR audio için.
        """
        # Ana noktaları çıkar
        key_points = re.findall(r'[-*]\s+(.+)', content)[:5]
        headers = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)[:3]
        
        words_per_second = 2.5  # Ortalama okuma hızı
        target_words = int(duration_seconds * words_per_second)
        
        script = f"Kısaca {topic}: "
        
        # Headers
        if headers:
            script += f"Bu konu {len(headers)} ana bölümden oluşuyor. "
            for h in headers[:2]:
                script += f"{h}. "
        
        # Key points
        if key_points:
            script += "Önemli noktalar: "
            for point in key_points[:3]:
                script += f"{point[:40]}. "
        
        # Truncate to target
        words = script.split()
        if len(words) > target_words:
            script = " ".join(words[:target_words]) + "..."
        
        return {
            "topic": topic,
            "duration_seconds": duration_seconds,
            "script": script,
            "word_count": len(script.split()),
            "estimated_duration": len(script.split()) / words_per_second
        }


# =============================================================================
# 16. SMART CONTENT LINKING
# =============================================================================

@dataclass
class ContentLink:
    """İçerik bağlantısı."""
    source_id: str
    target_id: str
    source_title: str
    target_title: str
    link_type: str  # "prerequisite", "related", "extends", "example", "opposite"
    strength: float = 1.0
    explanation: str = ""


@dataclass
class LearningPrerequisite:
    """Öğrenme ön koşulu."""
    topic: str
    required_topics: List[str]
    recommended_order: List[str]
    difficulty_level: int  # 1-5


class SmartContentLinker:
    """
    Akıllı içerik bağlama sistemi.
    
    Özellikler:
    - Konular arası otomatik bağlantı
    - Prerequisite (ön koşul) tespiti
    - "Bunu anlamak için önce şunu öğren" önerileri
    - İlişkili içerik önerileri
    - Öğrenme yolu oluşturma
    """
    
    # Konu hiyerarşisi şablonları (domain-specific)
    DOMAIN_HIERARCHIES = {
        "programming": {
            "python": {
                "prerequisites": ["temel programlama", "algoritma"],
                "subtopics": ["syntax", "veri tipleri", "fonksiyonlar", "oop", "modüller"],
                "leads_to": ["django", "flask", "fastapi", "data science", "machine learning"]
            },
            "web development": {
                "prerequisites": ["html", "css", "javascript"],
                "subtopics": ["frontend", "backend", "api", "database"],
                "leads_to": ["react", "vue", "node.js", "full stack"]
            },
            "machine learning": {
                "prerequisites": ["python", "matematik", "istatistik", "lineer cebir"],
                "subtopics": ["supervised", "unsupervised", "neural networks"],
                "leads_to": ["deep learning", "nlp", "computer vision"]
            }
        },
        "mathematics": {
            "calculus": {
                "prerequisites": ["algebra", "trigonometry"],
                "subtopics": ["limits", "derivatives", "integrals"],
                "leads_to": ["differential equations", "multivariable calculus"]
            },
            "statistics": {
                "prerequisites": ["basic math", "probability"],
                "subtopics": ["descriptive", "inferential", "hypothesis testing"],
                "leads_to": ["machine learning", "data analysis"]
            }
        },
        "language": {
            "english": {
                "prerequisites": ["alphabet", "basic vocabulary"],
                "subtopics": ["grammar", "vocabulary", "reading", "writing", "speaking"],
                "levels": ["A1", "A2", "B1", "B2", "C1", "C2"]
            }
        }
    }
    
    # İlişki anahtar kelimeleri
    RELATION_KEYWORDS = {
        "prerequisite": ["önce", "gerekli", "temel", "önkoşul", "required", "basic", "fundamental"],
        "extends": ["ileri", "advanced", "detaylı", "derinlemesine", "extends"],
        "related": ["ilişkili", "benzer", "related", "similar", "ayrıca", "also"],
        "example": ["örnek", "example", "uygulama", "practice", "case study"],
        "opposite": ["zıt", "karşı", "aksine", "versus", "vs", "contrary"]
    }
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._content_graph: Dict[str, List[ContentLink]] = defaultdict(list)
        self._lock = Lock()
        logger.info("SmartContentLinker initialized")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Metinden anahtar kelimeleri çıkar."""
        # Stop words
        stop_words = {
            'bir', 'bu', 've', 'ile', 'için', 'de', 'da', 'ki', 'ne', 'nasıl',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'of', 'to', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'or', 'and', 'if'
        }
        
        words = re.findall(r'\b[a-zA-ZğüşöçıİĞÜŞÖÇ]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        # Frekansa göre sırala
        freq = Counter(keywords)
        return [w for w, _ in freq.most_common(20)]
    
    def _detect_domain(self, text: str) -> Optional[str]:
        """Metnin domain'ini tespit et."""
        text_lower = text.lower()
        
        domain_keywords = {
            "programming": ["code", "kod", "program", "function", "class", "api", "database"],
            "mathematics": ["math", "matematik", "equation", "denklem", "integral", "calculus"],
            "science": ["science", "bilim", "experiment", "hypothesis", "theory"],
            "language": ["grammar", "vocabulary", "language", "dil", "speaking", "writing"],
            "business": ["business", "iş", "marketing", "management", "finance"]
        }
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return None
    
    def find_prerequisites(
        self, 
        topic: str, 
        content: str
    ) -> Dict[str, Any]:
        """
        Bir konunun ön koşullarını tespit et.
        
        Returns:
            {
                "topic": str,
                "prerequisites": List[Dict],
                "recommended_order": List[str],
                "difficulty_level": int
            }
        """
        domain = self._detect_domain(content) or self._detect_domain(topic)
        keywords = self._extract_keywords(topic + " " + content)
        
        prerequisites = []
        recommended_order = []
        
        # Domain hierarchy'den ön koşulları al
        if domain and domain in self.DOMAIN_HIERARCHIES:
            domain_data = self.DOMAIN_HIERARCHIES[domain]
            
            for subject, info in domain_data.items():
                if subject.lower() in topic.lower():
                    prereqs = info.get("prerequisites", [])
                    for prereq in prereqs:
                        prerequisites.append({
                            "topic": prereq,
                            "type": "required",
                            "reason": f"'{topic}' konusunu anlamak için temel gereklilik",
                            "confidence": 0.9
                        })
                    recommended_order = prereqs + [topic]
        
        # İçerikten ön koşul ipuçlarını bul
        prereq_patterns = [
            r'önce\s+(.+?)\s+(?:öğren|bil|anla)',
            r'(?:temel|basic)\s+(.+?)\s+(?:bilgisi|knowledge)',
            r'(?:gerekli|required):\s*(.+?)(?:\.|$)',
            r'(.+?)\s+(?:bilmeden|olmadan)',
        ]
        
        for pattern in prereq_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) < 50:  # Makul uzunluk
                    prerequisites.append({
                        "topic": match.strip(),
                        "type": "inferred",
                        "reason": "İçerikten tespit edildi",
                        "confidence": 0.7
                    })
        
        # Zorluk seviyesini tahmin et
        difficulty_indicators = {
            1: ["temel", "basic", "başlangıç", "intro", "giriş", "101"],
            2: ["orta", "intermediate", "medium"],
            3: ["ileri", "advanced", "detaylı"],
            4: ["uzman", "expert", "master"],
            5: ["araştırma", "research", "cutting-edge"]
        }
        
        difficulty_level = 2  # Default
        content_lower = (topic + " " + content).lower()
        for level, indicators in difficulty_indicators.items():
            if any(ind in content_lower for ind in indicators):
                difficulty_level = level
                break
        
        return {
            "topic": topic,
            "domain": domain,
            "prerequisites": prerequisites,
            "prerequisite_count": len(prerequisites),
            "recommended_order": recommended_order,
            "difficulty_level": difficulty_level,
            "difficulty_label": ["", "Başlangıç", "Orta", "İleri", "Uzman", "Araştırma"][difficulty_level]
        }
    
    def find_related_content(
        self, 
        topic: str, 
        content: str,
        all_topics: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        İlişkili içerikleri bul.
        
        Args:
            topic: Mevcut konu
            content: Mevcut içerik
            all_topics: Diğer konular listesi [{"id": "", "title": "", "content": ""}, ...]
        """
        keywords = self._extract_keywords(topic + " " + content)
        domain = self._detect_domain(content)
        
        related = []
        extensions = []
        examples = []
        
        # Domain'den ilişkili konuları al
        if domain and domain in self.DOMAIN_HIERARCHIES:
            domain_data = self.DOMAIN_HIERARCHIES[domain]
            
            for subject, info in domain_data.items():
                if subject.lower() in topic.lower():
                    # Leads to (extends)
                    for next_topic in info.get("leads_to", []):
                        extensions.append({
                            "topic": next_topic,
                            "relation": "extends",
                            "reason": f"'{topic}' öğrendikten sonra bu konuya geçebilirsiniz",
                            "confidence": 0.85
                        })
                    
                    # Subtopics (related)
                    for subtopic in info.get("subtopics", []):
                        related.append({
                            "topic": subtopic,
                            "relation": "subtopic",
                            "reason": f"'{topic}' altında yer alan konu",
                            "confidence": 0.9
                        })
        
        # Diğer konularla karşılaştır
        if all_topics:
            for other in all_topics:
                other_title = other.get("title", "")
                other_content = other.get("content", "")
                other_keywords = self._extract_keywords(other_title + " " + other_content)
                
                # Ortak keyword sayısı
                common = set(keywords) & set(other_keywords)
                similarity = len(common) / max(len(set(keywords) | set(other_keywords)), 1)
                
                if similarity >= 0.3 and other_title != topic:
                    related.append({
                        "topic": other_title,
                        "id": other.get("id"),
                        "relation": "similar",
                        "similarity": round(similarity, 2),
                        "common_keywords": list(common)[:5],
                        "confidence": similarity
                    })
        
        # İçerikten örnek referansları bul
        example_patterns = [
            r'örneğin\s+(.+?)(?:\.|,|$)',
            r'example:\s*(.+?)(?:\.|$)',
            r'(?:gibi|like)\s+(.+?)(?:\s|$)',
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if 5 < len(match) < 50:
                    examples.append({
                        "topic": match.strip(),
                        "relation": "example",
                        "reason": "İçerikte örnek olarak geçiyor"
                    })
        
        return {
            "topic": topic,
            "domain": domain,
            "related_topics": related,
            "extensions": extensions,
            "examples": examples[:5],
            "total_links": len(related) + len(extensions) + len(examples)
        }
    
    def generate_learning_path(
        self, 
        target_topic: str,
        current_knowledge: List[str] = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Hedefe ulaşmak için öğrenme yolu oluştur.
        
        "Bu konuyu anlamak için önce şunları öğren" listesi.
        """
        current_knowledge = current_knowledge or []
        path = []
        
        # Target topic'in ön koşullarını recursive olarak bul
        def find_path_recursive(topic: str, visited: Set[str], depth: int = 0) -> List[str]:
            if depth > max_steps or topic in visited:
                return []
            
            visited.add(topic)
            
            # Domain'den ön koşulları al
            prerequisites = []
            for domain, subjects in self.DOMAIN_HIERARCHIES.items():
                for subject, info in subjects.items():
                    if subject.lower() in topic.lower():
                        prerequisites = info.get("prerequisites", [])
                        break
            
            result = []
            for prereq in prerequisites:
                if prereq.lower() not in [k.lower() for k in current_knowledge]:
                    # Recursive olarak prereq'un prereq'lerini bul
                    sub_path = find_path_recursive(prereq, visited, depth + 1)
                    result.extend(sub_path)
                    result.append(prereq)
            
            return result
        
        raw_path = find_path_recursive(target_topic, set())
        
        # İçerik karmaşıklığına göre öğrenme süresi tahmini
        def estimate_learning_time(topic: str, is_known: bool = False) -> str:
            """Konu karmaşıklığına göre öğrenme süresi tahmin et."""
            if is_known:
                return "0 saat (biliniyor)"
            
            topic_lower = topic.lower()
            
            # Karmaşıklık göstergeleri
            advanced_keywords = ["ileri", "advanced", "optimizasyon", "derin", "kompleks", 
                                "mimari", "analiz", "sistem", "entegrasyon"]
            intermediate_keywords = ["orta", "intermediate", "uygulama", "pratik", "temel+"]
            beginner_keywords = ["giriş", "temel", "başlangıç", "intro", "101"]
            
            # Süre hesapla
            if any(kw in topic_lower for kw in advanced_keywords):
                base_hours = 4
                difficulty = "İleri"
            elif any(kw in topic_lower for kw in beginner_keywords):
                base_hours = 1
                difficulty = "Başlangıç"
            elif any(kw in topic_lower for kw in intermediate_keywords):
                base_hours = 2
                difficulty = "Orta"
            else:
                # Kelime sayısına göre tahmin
                word_count = len(topic.split())
                if word_count > 4:
                    base_hours = 3
                    difficulty = "Orta-İleri"
                elif word_count > 2:
                    base_hours = 2
                    difficulty = "Orta"
                else:
                    base_hours = 1.5
                    difficulty = "Temel"
            
            return f"{base_hours}-{base_hours + 2} saat ({difficulty})"
        
        # Duplicate'ları kaldır, sırayı koru
        seen = set()
        for step in raw_path:
            if step.lower() not in seen:
                seen.add(step.lower())
                is_known = step.lower() in [k.lower() for k in current_knowledge]
                path.append({
                    "step": len(path) + 1,
                    "topic": step,
                    "is_known": is_known,
                    "estimated_time": estimate_learning_time(step, is_known)
                })
        
        # Hedefi ekle
        path.append({
            "step": len(path) + 1,
            "topic": target_topic,
            "is_target": True,
            "estimated_time": estimate_learning_time(target_topic)
        })
        
        # Toplam süre hesapla
        total_min_hours = 0
        total_max_hours = 0
        for p in path:
            if not p.get("is_known"):
                time_str = p.get("estimated_time", "2-4 saat")
                import re
                match = re.search(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)', time_str)
                if match:
                    total_min_hours += float(match.group(1))
                    total_max_hours += float(match.group(2))
                else:
                    total_min_hours += 2
                    total_max_hours += 4
        
        return {
            "target": target_topic,
            "current_knowledge": current_knowledge,
            "learning_path": path,
            "total_steps": len(path),
            "new_topics_to_learn": len([p for p in path if not p.get("is_known") and not p.get("is_target")]),
            "estimated_total_time": f"{int(total_min_hours)}-{int(total_max_hours)} saat",
            "estimated_days": f"{int(total_min_hours / 4)}-{int(total_max_hours / 2)} gün (günde 2-4 saat çalışma ile)"
        }
    
    def suggest_next_topics(
        self, 
        completed_topics: List[str],
        interests: List[str] = None
    ) -> Dict[str, Any]:
        """
        Tamamlanan konulara göre sonraki adımları öner.
        """
        suggestions = []
        
        for domain, subjects in self.DOMAIN_HIERARCHIES.items():
            for subject, info in subjects.items():
                # Eğer prerequisite'ları tamamlandıysa
                prereqs = info.get("prerequisites", [])
                prereqs_met = all(
                    any(p.lower() in c.lower() for c in completed_topics)
                    for p in prereqs
                )
                
                if prereqs_met:
                    # Subtopics öner
                    for subtopic in info.get("subtopics", []):
                        if not any(subtopic.lower() in c.lower() for c in completed_topics):
                            suggestions.append({
                                "topic": subtopic,
                                "parent": subject,
                                "domain": domain,
                                "type": "subtopic",
                                "reason": f"{subject} altında henüz öğrenmediğiniz konu"
                            })
                    
                    # Leads to öner
                    for next_topic in info.get("leads_to", []):
                        if not any(next_topic.lower() in c.lower() for c in completed_topics):
                            suggestions.append({
                                "topic": next_topic,
                                "from": subject,
                                "domain": domain,
                                "type": "next_level",
                                "reason": f"{subject} bilginizle ilerleyebileceğiniz konu"
                            })
        
        # İlgi alanlarına göre filtrele
        if interests:
            filtered = []
            for s in suggestions:
                if any(i.lower() in s["topic"].lower() or i.lower() in s.get("domain", "").lower() 
                       for i in interests):
                    s["matches_interest"] = True
                    filtered.insert(0, s)  # İlgi alanları önce
                else:
                    filtered.append(s)
            suggestions = filtered
        
        return {
            "completed_topics": completed_topics,
            "interests": interests or [],
            "suggestions": suggestions[:10],
            "suggestion_count": len(suggestions)
        }
    
    def create_content_link(
        self,
        source_id: str,
        source_title: str,
        target_id: str,
        target_title: str,
        link_type: str,
        explanation: str = ""
    ) -> ContentLink:
        """Manuel içerik bağlantısı oluştur."""
        link = ContentLink(
            source_id=source_id,
            target_id=target_id,
            source_title=source_title,
            target_title=target_title,
            link_type=link_type,
            explanation=explanation
        )
        
        with self._lock:
            self._content_graph[source_id].append(link)
        
        return link
    
    def get_content_links(self, content_id: str) -> List[Dict]:
        """Bir içeriğin bağlantılarını getir."""
        links = self._content_graph.get(content_id, [])
        return [
            {
                "target_id": l.target_id,
                "target_title": l.target_title,
                "link_type": l.link_type,
                "explanation": l.explanation
            }
            for l in links
        ]


# =============================================================================
# LEARNING ADVANCED FEATURES MANAGER
# =============================================================================

class LearningAdvancedFeaturesManager:
    """
    Gelişmiş öğrenme özellikleri yöneticisi.
    
    3 Premium Özellik:
    14. 🎨 Visual Learning Tools
    15. 📹 Multimedia Content Generation
    16. 🔗 Smart Content Linking
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.visual_tools = VisualLearningTools()
        self.multimedia_generator = MultimediaContentGenerator()
        self.content_linker = SmartContentLinker()
        
        self._initialized = True
        logger.info("LearningAdvancedFeaturesManager initialized with 3 features")
    
    # Visual Tools shortcuts
    def create_mind_map(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.visual_tools.generate_mind_map(topic, content, **kwargs)
    
    def create_concept_map(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.visual_tools.generate_concept_map(topic, content, **kwargs)
    
    def create_timeline(self, topic: str, content: str) -> Dict[str, Any]:
        return self.visual_tools.generate_timeline(topic, content)
    
    def create_flowchart(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.visual_tools.generate_flowchart(topic, content, **kwargs)
    
    def create_infographic(self, topic: str, content: str) -> Dict[str, Any]:
        return self.visual_tools.generate_infographic_structure(topic, content)
    
    # Multimedia shortcuts
    def create_video_script(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.multimedia_generator.generate_video_script(topic, content, **kwargs)
    
    def create_slide_deck(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.multimedia_generator.generate_slide_deck(topic, content, **kwargs)
    
    def create_podcast_script(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.multimedia_generator.generate_podcast_script(topic, content, **kwargs)
    
    def create_audio_summary(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.multimedia_generator.generate_audio_summary(topic, content, **kwargs)
    
    # Content Linking shortcuts
    def get_prerequisites(self, topic: str, content: str) -> Dict[str, Any]:
        return self.content_linker.find_prerequisites(topic, content)
    
    def get_related_content(self, topic: str, content: str, **kwargs) -> Dict[str, Any]:
        return self.content_linker.find_related_content(topic, content, **kwargs)
    
    def get_learning_path(self, target: str, **kwargs) -> Dict[str, Any]:
        return self.content_linker.generate_learning_path(target, **kwargs)
    
    def get_next_topics(self, completed: List[str], **kwargs) -> Dict[str, Any]:
        return self.content_linker.suggest_next_topics(completed, **kwargs)


# Singleton
def get_learning_advanced_features() -> LearningAdvancedFeaturesManager:
    """Learning advanced features manager singleton."""
    return LearningAdvancedFeaturesManager()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "VisualLearningTools",
    "MultimediaContentGenerator", 
    "SmartContentLinker",
    "LearningAdvancedFeaturesManager",
    "get_learning_advanced_features",
    "MindMapNode",
    "ContentLink",
    "SlideContent",
]
