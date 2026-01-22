"""
Full Meta Learning - Multi-Modal Module
Çok modlu öğrenme deneyimi

Features:
- Visual Lessons: Görselli öğretim (infografik, diyagram, video)
- Interactive Diagrams: Etkileşimli diyagramlar
- Mnemonic Generator: Hafıza teknikleri üretici
- Code Playground: Canlı kod çalıştırma ortamı
- Sketch-to-Explain: Çizimle açıklama
"""

import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field


# ============ ENUMS ============

class VisualType(str, Enum):
    """Görsel içerik tipleri"""
    INFOGRAPHIC = "infographic"      # Bilgi grafiği
    FLOWCHART = "flowchart"          # Akış şeması
    MIND_MAP = "mind_map"            # Zihin haritası
    DIAGRAM = "diagram"              # Diyagram
    COMPARISON = "comparison"        # Karşılaştırma tablosu
    TIMELINE = "timeline"            # Zaman çizelgesi
    HIERARCHY = "hierarchy"          # Hiyerarşi
    PROCESS = "process"              # Süreç şeması
    CONCEPT_MAP = "concept_map"      # Kavram haritası


class DiagramElementType(str, Enum):
    """Diyagram element tipleri"""
    NODE = "node"
    EDGE = "edge"
    GROUP = "group"
    LABEL = "label"
    ICON = "icon"
    IMAGE = "image"


class MnemonicType(str, Enum):
    """Hafıza tekniği tipleri"""
    ACRONYM = "acronym"              # Kısaltma (NASA)
    ACROSTIC = "acrostic"            # İlk harfler cümle
    RHYME = "rhyme"                  # Kafiye
    CHUNKING = "chunking"            # Gruplama
    STORY = "story"                  # Hikaye
    PEG_SYSTEM = "peg_system"        # Çivi sistemi
    LOCI = "loci"                    # Loci metodu
    KEYWORD = "keyword"              # Anahtar kelime
    VISUAL = "visual"                # Görsel çağrışım


class CodeLanguage(str, Enum):
    """Desteklenen programlama dilleri"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    SQL = "sql"
    BASH = "bash"


class SketchTool(str, Enum):
    """Çizim araçları"""
    PEN = "pen"
    HIGHLIGHTER = "highlighter"
    ARROW = "arrow"
    SHAPE = "shape"
    TEXT = "text"
    ERASER = "eraser"
    CONNECTOR = "connector"


# ============ DATA CLASSES ============

@dataclass
class VisualContent:
    """Görsel içerik"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    visual_type: VisualType = VisualType.DIAGRAM
    
    title: str = ""
    description: str = ""
    
    # İçerik
    svg_content: str = ""          # SVG formatında görsel
    json_schema: Dict = field(default_factory=dict)  # Yapısal veri
    
    # Stil
    color_scheme: str = "default"
    theme: str = "light"
    
    # İlişki
    source_content_id: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    view_count: int = 0
    effectiveness_score: float = 0.0


@dataclass
class InteractiveDiagram:
    """Etkileşimli diyagram"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    title: str = ""
    diagram_type: VisualType = VisualType.FLOWCHART
    
    # Elementler
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    groups: List[Dict[str, Any]] = field(default_factory=list)
    
    # Etkileşim
    clickable_areas: List[Dict[str, Any]] = field(default_factory=list)
    hover_info: Dict[str, str] = field(default_factory=dict)
    drill_down_links: Dict[str, str] = field(default_factory=dict)
    
    # Animasyon
    animation_sequence: List[str] = field(default_factory=list)
    auto_play: bool = False
    
    # Düzenleme
    is_editable: bool = True
    last_edited: datetime = field(default_factory=datetime.now)


@dataclass
class MnemonicDevice:
    """Hafıza cihazı / tekniği"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mnemonic_type: MnemonicType = MnemonicType.ACRONYM
    
    # İçerik
    target_content: str = ""       # Hatırlanacak içerik
    mnemonic: str = ""             # Hafıza tekniği
    explanation: str = ""          # Açıklama
    
    # Görselleştirme
    visual_cue: str = ""           # Görsel ipucu
    audio_cue: str = ""            # Sesli ipucu
    
    # Etkililik
    times_used: int = 0
    success_rate: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CodePlayground:
    """Kod çalıştırma ortamı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    language: CodeLanguage = CodeLanguage.PYTHON
    
    title: str = ""
    description: str = ""
    
    # Kod
    initial_code: str = ""
    solution_code: str = ""
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    
    # Hints
    hints: List[str] = field(default_factory=list)
    hints_used: int = 0
    
    # Execution
    max_execution_time: int = 10  # saniye
    memory_limit_mb: int = 128
    
    # İlerleme
    attempts: int = 0
    solved: bool = False
    best_solution: str = ""
    
    # İlişki
    related_concept: str = ""
    difficulty: int = 1  # 1-5


@dataclass
class CodeExecutionResult:
    """Kod çalıştırma sonucu"""
    success: bool = False
    output: str = ""
    error: str = ""
    execution_time_ms: int = 0
    memory_used_mb: float = 0
    
    # Test sonuçları
    tests_passed: int = 0
    tests_failed: int = 0
    test_results: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SketchExplanation:
    """Çizimle açıklama"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    title: str = ""
    concept: str = ""
    
    # Canvas
    canvas_width: int = 800
    canvas_height: int = 600
    background_color: str = "#FFFFFF"
    
    # Çizim elementleri
    strokes: List[Dict[str, Any]] = field(default_factory=list)
    shapes: List[Dict[str, Any]] = field(default_factory=list)
    text_annotations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Kayıt
    recording: List[Dict[str, Any]] = field(default_factory=list)  # Çizim replay
    audio_narration: str = ""
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    duration_seconds: int = 0


# ============ ENGINES ============

class VisualContentEngine:
    """Görsel içerik üretim engine'i"""
    
    def __init__(self):
        self.visuals: Dict[str, VisualContent] = {}
    
    def generate_visual(self, content: Dict[str, Any], 
                       visual_type: VisualType) -> VisualContent:
        """İçerikten görsel oluştur"""
        
        title = content.get("title", "Görsel")
        points = content.get("key_points", [])
        relationships = content.get("relationships", [])
        
        visual = VisualContent(
            visual_type=visual_type,
            title=title,
            source_content_id=content.get("id", "")
        )
        
        if visual_type == VisualType.MIND_MAP:
            visual.json_schema = self._create_mind_map(title, points)
        elif visual_type == VisualType.FLOWCHART:
            visual.json_schema = self._create_flowchart(points)
        elif visual_type == VisualType.COMPARISON:
            visual.json_schema = self._create_comparison(content)
        elif visual_type == VisualType.TIMELINE:
            visual.json_schema = self._create_timeline(points)
        elif visual_type == VisualType.HIERARCHY:
            visual.json_schema = self._create_hierarchy(content)
        else:
            visual.json_schema = self._create_generic_diagram(points)
        
        # SVG oluştur
        visual.svg_content = self._schema_to_svg(visual.json_schema, visual_type)
        
        self.visuals[visual.id] = visual
        return visual
    
    def _create_mind_map(self, center: str, branches: List[str]) -> Dict:
        """Mind map şeması"""
        nodes = [{"id": "center", "label": center, "type": "center", "x": 400, "y": 300}]
        edges = []
        
        angle_step = 360 / max(1, len(branches))
        radius = 200
        
        for i, branch in enumerate(branches):
            import math
            angle = math.radians(i * angle_step)
            x = 400 + radius * math.cos(angle)
            y = 300 + radius * math.sin(angle)
            
            node_id = f"branch_{i}"
            nodes.append({
                "id": node_id,
                "label": branch[:50],
                "type": "branch",
                "x": x,
                "y": y
            })
            edges.append({"from": "center", "to": node_id})
        
        return {"nodes": nodes, "edges": edges, "type": "mind_map"}
    
    def _create_flowchart(self, steps: List[str]) -> Dict:
        """Flowchart şeması"""
        nodes = []
        edges = []
        
        y_offset = 50
        for i, step in enumerate(steps):
            node_id = f"step_{i}"
            nodes.append({
                "id": node_id,
                "label": step[:40],
                "type": "process" if i > 0 and i < len(steps) - 1 else "terminal",
                "x": 400,
                "y": y_offset
            })
            
            if i > 0:
                edges.append({"from": f"step_{i-1}", "to": node_id})
            
            y_offset += 100
        
        return {"nodes": nodes, "edges": edges, "type": "flowchart"}
    
    def _create_comparison(self, content: Dict) -> Dict:
        """Karşılaştırma tablosu"""
        items = content.get("items", [])
        criteria = content.get("criteria", ["Özellik 1", "Özellik 2", "Özellik 3"])
        
        return {
            "type": "comparison",
            "headers": [item.get("name", f"Öğe {i}") for i, item in enumerate(items)],
            "criteria": criteria,
            "data": [
                [item.get(c, "-") for item in items]
                for c in criteria
            ]
        }
    
    def _create_timeline(self, events: List[str]) -> Dict:
        """Zaman çizelgesi"""
        points = []
        for i, event in enumerate(events):
            points.append({
                "position": i,
                "label": event[:50],
                "year": f"Adım {i+1}"
            })
        
        return {"type": "timeline", "points": points}
    
    def _create_hierarchy(self, content: Dict) -> Dict:
        """Hiyerarşi şeması"""
        title = content.get("title", "Root")
        children = content.get("children", [])
        
        def build_tree(node, depth=0):
            result = {
                "name": node.get("name", "Node") if isinstance(node, dict) else str(node),
                "depth": depth,
                "children": []
            }
            if isinstance(node, dict) and "children" in node:
                for child in node["children"]:
                    result["children"].append(build_tree(child, depth + 1))
            return result
        
        return {"type": "hierarchy", "root": {"name": title, "children": children}}
    
    def _create_generic_diagram(self, points: List[str]) -> Dict:
        """Genel diyagram"""
        nodes = []
        for i, point in enumerate(points):
            nodes.append({
                "id": f"node_{i}",
                "label": point[:50],
                "x": 100 + (i % 3) * 250,
                "y": 100 + (i // 3) * 150
            })
        
        return {"type": "diagram", "nodes": nodes, "edges": []}
    
    def _schema_to_svg(self, schema: Dict, visual_type: VisualType) -> str:
        """Schema'dan SVG oluştur"""
        # Basit SVG template
        svg_parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">']
        svg_parts.append('<style>.node { fill: #4CAF50; } .edge { stroke: #666; stroke-width: 2; } .label { font-family: Arial; font-size: 12px; }</style>')
        
        # Nodes
        for node in schema.get("nodes", []):
            x = node.get("x", 100)
            y = node.get("y", 100)
            label = node.get("label", "")
            
            svg_parts.append(f'<rect x="{x-50}" y="{y-20}" width="100" height="40" rx="5" class="node" fill="#4CAF50"/>')
            svg_parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" class="label" fill="white">{label[:15]}</text>')
        
        # Edges
        for edge in schema.get("edges", []):
            svg_parts.append(f'<line x1="100" y1="100" x2="200" y2="200" class="edge"/>')
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)


class InteractiveDiagramEngine:
    """Etkileşimli diyagram engine'i"""
    
    def __init__(self):
        self.diagrams: Dict[str, InteractiveDiagram] = {}
    
    def create_diagram(self, title: str, 
                      diagram_type: VisualType = VisualType.FLOWCHART) -> InteractiveDiagram:
        """Yeni diyagram oluştur"""
        diagram = InteractiveDiagram(
            title=title,
            diagram_type=diagram_type
        )
        self.diagrams[diagram.id] = diagram
        return diagram
    
    def add_node(self, diagram_id: str, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Node ekle"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return {"error": "Diagram not found"}
        
        node = {
            "id": str(uuid.uuid4()),
            "type": node_data.get("type", "default"),
            "label": node_data.get("label", "Node"),
            "x": node_data.get("x", 100),
            "y": node_data.get("y", 100),
            "width": node_data.get("width", 120),
            "height": node_data.get("height", 60),
            "color": node_data.get("color", "#4CAF50"),
            "info": node_data.get("info", ""),
            "link": node_data.get("link", "")
        }
        
        diagram.nodes.append(node)
        
        # Hover info ekle
        if node["info"]:
            diagram.hover_info[node["id"]] = node["info"]
        
        # Drill-down link ekle
        if node["link"]:
            diagram.drill_down_links[node["id"]] = node["link"]
        
        return node
    
    def add_edge(self, diagram_id: str, from_id: str, to_id: str,
                 label: str = "", style: str = "solid") -> Dict[str, Any]:
        """Edge ekle"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return {"error": "Diagram not found"}
        
        edge = {
            "id": str(uuid.uuid4()),
            "from": from_id,
            "to": to_id,
            "label": label,
            "style": style,  # solid, dashed, dotted
            "arrow": True
        }
        
        diagram.edges.append(edge)
        return edge
    
    def set_animation_sequence(self, diagram_id: str, 
                               sequence: List[str]) -> bool:
        """Animasyon sırası ayarla"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return False
        
        diagram.animation_sequence = sequence
        return True
    
    def get_interactive_data(self, diagram_id: str) -> Dict[str, Any]:
        """Etkileşimli veri al (frontend için)"""
        diagram = self.diagrams.get(diagram_id)
        if not diagram:
            return {}
        
        return {
            "id": diagram.id,
            "title": diagram.title,
            "type": diagram.diagram_type.value,
            "nodes": diagram.nodes,
            "edges": diagram.edges,
            "groups": diagram.groups,
            "interactions": {
                "hover": diagram.hover_info,
                "click": diagram.drill_down_links,
                "animation": diagram.animation_sequence
            },
            "settings": {
                "editable": diagram.is_editable,
                "autoPlay": diagram.auto_play
            }
        }


class MnemonicGeneratorEngine:
    """Hafıza tekniği üretim engine'i"""
    
    # Peg System sayıları (Türkçe)
    PEG_WORDS = {
        1: "bir-biber",
        2: "iki-iki göz",
        3: "üç-üçgen",
        4: "dört-dörtlü",
        5: "beş-beşik",
        6: "altı-altın",
        7: "yedi-yedi cüceler",
        8: "sekiz-sekizgen",
        9: "dokuz-dokuma",
        10: "on-on parmak"
    }
    
    def __init__(self):
        self.mnemonics: Dict[str, MnemonicDevice] = {}
    
    def generate_acronym(self, items: List[str]) -> MnemonicDevice:
        """Kısaltma oluştur"""
        first_letters = [item[0].upper() for item in items if item]
        acronym = "".join(first_letters)
        
        mnemonic = MnemonicDevice(
            mnemonic_type=MnemonicType.ACRONYM,
            target_content=", ".join(items),
            mnemonic=acronym,
            explanation=f"Her harf bir öğeyi temsil eder: {' - '.join([f'{l}: {i}' for l, i in zip(first_letters, items)])}"
        )
        
        self.mnemonics[mnemonic.id] = mnemonic
        return mnemonic
    
    def generate_acrostic(self, items: List[str]) -> MnemonicDevice:
        """İlk harflerden cümle oluştur"""
        first_letters = [item[0].upper() for item in items if item]
        
        # Basit kelime önerileri (gerçek uygulamada LLM kullanılabilir)
        word_suggestions = {
            'A': 'Ayşe', 'B': 'Büyük', 'C': 'Cesur', 'Ç': 'Çalışkan',
            'D': 'Deniz', 'E': 'Evde', 'F': 'Futbol', 'G': 'Güzel',
            'H': 'Her', 'I': 'Ilık', 'İ': 'İyi', 'J': 'Joker',
            'K': 'Kedi', 'L': 'Limon', 'M': 'Masa', 'N': 'Neden',
            'O': 'Okul', 'Ö': 'Öğrenci', 'P': 'Park', 'R': 'Renk',
            'S': 'Sevgi', 'Ş': 'Şeker', 'T': 'Tatlı', 'U': 'Uzun',
            'Ü': 'Ülke', 'V': 'Var', 'Y': 'Yeşil', 'Z': 'Zaman'
        }
        
        sentence_words = [word_suggestions.get(l, f"{l}...") for l in first_letters]
        sentence = " ".join(sentence_words)
        
        mnemonic = MnemonicDevice(
            mnemonic_type=MnemonicType.ACROSTIC,
            target_content=", ".join(items),
            mnemonic=sentence,
            explanation=f"Cümledeki her kelimenin ilk harfi sırayla: {', '.join(items)}"
        )
        
        self.mnemonics[mnemonic.id] = mnemonic
        return mnemonic
    
    def generate_story(self, items: List[str]) -> MnemonicDevice:
        """Hikaye oluştur"""
        # Basit hikaye şablonu
        story_template = "Bir gün {0} gördüm. Sonra {1} ile karşılaştım. Birlikte {2} hakkında konuştuk."
        
        # İtemleri hikayeye yerleştir
        if len(items) >= 3:
            story = story_template.format(*items[:3])
            for i, item in enumerate(items[3:], 3):
                story += f" Ardından {item} keşfettik."
        else:
            story = f"Hatırla: {' → '.join(items)}"
        
        mnemonic = MnemonicDevice(
            mnemonic_type=MnemonicType.STORY,
            target_content=", ".join(items),
            mnemonic=story,
            explanation="Hikayeyi görselleştirerek kavramları hatırla"
        )
        
        self.mnemonics[mnemonic.id] = mnemonic
        return mnemonic
    
    def generate_peg_system(self, items: List[str]) -> MnemonicDevice:
        """Peg (çivi) sistemi"""
        pegs = []
        for i, item in enumerate(items[:10], 1):
            peg = self.PEG_WORDS.get(i, f"{i}")
            pegs.append(f"{i}. {peg} → {item}")
        
        mnemonic = MnemonicDevice(
            mnemonic_type=MnemonicType.PEG_SYSTEM,
            target_content=", ".join(items),
            mnemonic="\n".join(pegs),
            explanation="Her sayı-kelime çiftini öğrenilecek öğeyle ilişkilendir"
        )
        
        self.mnemonics[mnemonic.id] = mnemonic
        return mnemonic
    
    def generate_visual_association(self, concept: str, 
                                   meaning: str) -> MnemonicDevice:
        """Görsel çağrışım oluştur"""
        # Basit görsel öneri (gerçek uygulamada AI görsel üretimi)
        visual_cue = f"🎨 '{concept}' kelimesini '{meaning}' ile ilişkilendir. " \
                     f"Görselleştir: {concept} şeklinde bir {meaning} hayal et."
        
        mnemonic = MnemonicDevice(
            mnemonic_type=MnemonicType.VISUAL,
            target_content=f"{concept}: {meaning}",
            mnemonic=visual_cue,
            explanation="Görsel bir sahne hayal ederek bağlantı kur",
            visual_cue=visual_cue
        )
        
        self.mnemonics[mnemonic.id] = mnemonic
        return mnemonic
    
    def suggest_best_technique(self, content_type: str, 
                               item_count: int) -> MnemonicType:
        """En iyi tekniği öner"""
        if item_count <= 5:
            return MnemonicType.ACRONYM
        elif item_count <= 10:
            return MnemonicType.PEG_SYSTEM
        elif item_count <= 15:
            return MnemonicType.STORY
        else:
            return MnemonicType.CHUNKING


class CodePlaygroundEngine:
    """Kod çalıştırma ortamı engine'i"""
    
    # Güvenli import whitelist (Python)
    SAFE_IMPORTS = {
        "math", "random", "datetime", "json", "re", 
        "collections", "itertools", "functools", "statistics"
    }
    
    def __init__(self):
        self.playgrounds: Dict[str, CodePlayground] = {}
    
    def create_playground(self, language: CodeLanguage,
                         title: str,
                         initial_code: str = "",
                         description: str = "") -> CodePlayground:
        """Yeni playground oluştur"""
        playground = CodePlayground(
            language=language,
            title=title,
            description=description,
            initial_code=initial_code
        )
        
        self.playgrounds[playground.id] = playground
        return playground
    
    def add_test_case(self, playground_id: str, 
                      input_data: Any, expected_output: Any,
                      description: str = "") -> bool:
        """Test case ekle"""
        playground = self.playgrounds.get(playground_id)
        if not playground:
            return False
        
        playground.test_cases.append({
            "id": str(uuid.uuid4()),
            "input": input_data,
            "expected": expected_output,
            "description": description
        })
        
        return True
    
    def execute_code(self, playground_id: str, 
                     code: str) -> CodeExecutionResult:
        """Kodu çalıştır (sandbox)"""
        playground = self.playgrounds.get(playground_id)
        if not playground:
            return CodeExecutionResult(success=False, error="Playground not found")
        
        playground.attempts += 1
        
        if playground.language == CodeLanguage.PYTHON:
            return self._execute_python(code, playground)
        else:
            return CodeExecutionResult(
                success=False, 
                error=f"Language {playground.language.value} execution not implemented"
            )
    
    def _execute_python(self, code: str, 
                       playground: CodePlayground) -> CodeExecutionResult:
        """Python kodu çalıştır (güvenli sandbox)"""
        import time
        start_time = time.time()
        
        # Tehlikeli import kontrolü
        dangerous_patterns = [
            r'import\s+os', r'import\s+sys', r'import\s+subprocess',
            r'__import__', r'eval\s*\(', r'exec\s*\(',
            r'open\s*\(', r'file\s*\('
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                return CodeExecutionResult(
                    success=False,
                    error=f"Güvenlik: Bu işlem izin verilmiyor"
                )
        
        # Sandbox ortamında çalıştır
        try:
            # Güvenli globals
            safe_globals = {
                "__builtins__": {
                    "print": print, "len": len, "range": range,
                    "str": str, "int": int, "float": float,
                    "list": list, "dict": dict, "set": set,
                    "tuple": tuple, "bool": bool, "type": type,
                    "sum": sum, "min": min, "max": max,
                    "sorted": sorted, "reversed": reversed,
                    "enumerate": enumerate, "zip": zip,
                    "map": map, "filter": filter,
                    "abs": abs, "round": round, "pow": pow,
                    "True": True, "False": False, "None": None
                }
            }
            
            # Safe imports ekle
            import math
            import random as rand_module
            safe_globals["math"] = math
            safe_globals["random"] = rand_module
            
            local_vars = {}
            
            # Stdout yakala
            import io
            import sys
            old_stdout = sys.stdout
            sys.stdout = captured_output = io.StringIO()
            
            try:
                exec(code, safe_globals, local_vars)
                output = captured_output.getvalue()
            finally:
                sys.stdout = old_stdout
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Test cases çalıştır
            test_results = []
            tests_passed = 0
            tests_failed = 0
            
            if playground.test_cases and "solution" in local_vars:
                solution_func = local_vars["solution"]
                
                for test in playground.test_cases:
                    try:
                        result = solution_func(test["input"])
                        passed = result == test["expected"]
                        
                        test_results.append({
                            "input": test["input"],
                            "expected": test["expected"],
                            "actual": result,
                            "passed": passed
                        })
                        
                        if passed:
                            tests_passed += 1
                        else:
                            tests_failed += 1
                    except Exception as e:
                        tests_failed += 1
                        test_results.append({
                            "input": test["input"],
                            "error": str(e),
                            "passed": False
                        })
            
            # Başarılı mı?
            success = tests_failed == 0 if playground.test_cases else True
            
            if success and not playground.solved:
                playground.solved = True
                playground.best_solution = code
            
            return CodeExecutionResult(
                success=success,
                output=output,
                execution_time_ms=execution_time,
                tests_passed=tests_passed,
                tests_failed=tests_failed,
                test_results=test_results
            )
            
        except Exception as e:
            return CodeExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def get_hint(self, playground_id: str) -> Optional[str]:
        """İpucu al"""
        playground = self.playgrounds.get(playground_id)
        if not playground or not playground.hints:
            return None
        
        if playground.hints_used < len(playground.hints):
            hint = playground.hints[playground.hints_used]
            playground.hints_used += 1
            return hint
        
        return "Tüm ipuçları kullanıldı!"


class SketchExplainEngine:
    """Çizimle açıklama engine'i"""
    
    def __init__(self):
        self.sketches: Dict[str, SketchExplanation] = {}
    
    def create_sketch(self, title: str, concept: str) -> SketchExplanation:
        """Yeni sketch oluştur"""
        sketch = SketchExplanation(
            title=title,
            concept=concept
        )
        
        self.sketches[sketch.id] = sketch
        return sketch
    
    def add_stroke(self, sketch_id: str, 
                   points: List[Tuple[float, float]],
                   color: str = "#000000",
                   width: int = 2) -> bool:
        """Çizgi ekle"""
        sketch = self.sketches.get(sketch_id)
        if not sketch:
            return False
        
        stroke = {
            "id": str(uuid.uuid4()),
            "type": "stroke",
            "points": points,
            "color": color,
            "width": width,
            "timestamp": datetime.now().timestamp()
        }
        
        sketch.strokes.append(stroke)
        sketch.recording.append(stroke)
        
        return True
    
    def add_shape(self, sketch_id: str,
                  shape_type: str,  # rect, circle, arrow, line
                  x: float, y: float,
                  width: float = 100, height: float = 50,
                  color: str = "#4CAF50") -> bool:
        """Şekil ekle"""
        sketch = self.sketches.get(sketch_id)
        if not sketch:
            return False
        
        shape = {
            "id": str(uuid.uuid4()),
            "type": shape_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": color,
            "timestamp": datetime.now().timestamp()
        }
        
        sketch.shapes.append(shape)
        sketch.recording.append(shape)
        
        return True
    
    def add_annotation(self, sketch_id: str,
                       text: str,
                       x: float, y: float,
                       font_size: int = 14) -> bool:
        """Metin notu ekle"""
        sketch = self.sketches.get(sketch_id)
        if not sketch:
            return False
        
        annotation = {
            "id": str(uuid.uuid4()),
            "type": "text",
            "text": text,
            "x": x,
            "y": y,
            "fontSize": font_size,
            "timestamp": datetime.now().timestamp()
        }
        
        sketch.text_annotations.append(annotation)
        sketch.recording.append(annotation)
        
        return True
    
    def get_replay_data(self, sketch_id: str) -> Optional[Dict[str, Any]]:
        """Replay verisi al"""
        sketch = self.sketches.get(sketch_id)
        if not sketch:
            return None
        
        # Recording'i timestamp'e göre sırala
        sorted_recording = sorted(
            sketch.recording,
            key=lambda x: x.get("timestamp", 0)
        )
        
        return {
            "id": sketch.id,
            "title": sketch.title,
            "canvas": {
                "width": sketch.canvas_width,
                "height": sketch.canvas_height,
                "background": sketch.background_color
            },
            "recording": sorted_recording,
            "duration": sketch.duration_seconds,
            "audio": sketch.audio_narration
        }
    
    def export_as_image(self, sketch_id: str) -> Optional[str]:
        """SVG olarak export et"""
        sketch = self.sketches.get(sketch_id)
        if not sketch:
            return None
        
        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{sketch.canvas_width}" height="{sketch.canvas_height}" '
            f'style="background:{sketch.background_color}">'
        ]
        
        # Strokes
        for stroke in sketch.strokes:
            points = stroke.get("points", [])
            if len(points) >= 2:
                path_data = f"M {points[0][0]} {points[0][1]}"
                for p in points[1:]:
                    path_data += f" L {p[0]} {p[1]}"
                
                svg_parts.append(
                    f'<path d="{path_data}" stroke="{stroke["color"]}" '
                    f'stroke-width="{stroke["width"]}" fill="none"/>'
                )
        
        # Shapes
        for shape in sketch.shapes:
            shape_type = shape.get("type")
            if shape_type == "rect":
                svg_parts.append(
                    f'<rect x="{shape["x"]}" y="{shape["y"]}" '
                    f'width="{shape["width"]}" height="{shape["height"]}" '
                    f'fill="{shape["color"]}" opacity="0.7"/>'
                )
            elif shape_type == "circle":
                r = min(shape["width"], shape["height"]) / 2
                svg_parts.append(
                    f'<circle cx="{shape["x"] + r}" cy="{shape["y"] + r}" '
                    f'r="{r}" fill="{shape["color"]}" opacity="0.7"/>'
                )
        
        # Text annotations
        for ann in sketch.text_annotations:
            svg_parts.append(
                f'<text x="{ann["x"]}" y="{ann["y"]}" '
                f'font-size="{ann["fontSize"]}">{ann["text"]}</text>'
            )
        
        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)


# ============ SINGLETON INSTANCES ============

visual_content_engine = VisualContentEngine()
interactive_diagram_engine = InteractiveDiagramEngine()
mnemonic_generator_engine = MnemonicGeneratorEngine()
code_playground_engine = CodePlaygroundEngine()
sketch_explain_engine = SketchExplainEngine()
