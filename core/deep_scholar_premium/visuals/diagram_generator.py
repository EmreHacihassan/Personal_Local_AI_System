"""
DiagramGenerator - Gelişmiş Diyagram Oluşturma Modülü
=====================================================

Desteklenen Formatlar:
1. PlantUML - UML diyagramları
2. Mermaid - Akış ve sekans diyagramları
3. D2 - Modern diyagram dili
4. Graphviz DOT - Graf diyagramları

Diyagram Türleri:
- Akış şeması (Flowchart)
- Sınıf diyagramı (Class diagram)
- Sekans diyagramı (Sequence diagram)
- Durum diyagramı (State diagram)
- Zihin haritası (Mind map)
- Gantt şeması
- ER diyagramı
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.llm_manager import llm_manager


class DiagramType(str, Enum):
    """Diyagram türleri."""
    FLOWCHART = "flowchart"
    SEQUENCE = "sequence"
    CLASS = "class"
    STATE = "state"
    MINDMAP = "mindmap"
    GANTT = "gantt"
    ER = "er"
    ARCHITECTURE = "architecture"
    PROCESS = "process"


class DiagramFormat(str, Enum):
    """Diyagram formatları."""
    PLANTUML = "plantuml"
    MERMAID = "mermaid"
    D2 = "d2"
    GRAPHVIZ = "graphviz"


@dataclass
class Diagram:
    """Diyagram."""
    type: DiagramType
    format: DiagramFormat
    code: str
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Render edilmiş hali
    rendered_svg: Optional[str] = None
    rendered_png_base64: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Markdown'a çevir."""
        if self.format == DiagramFormat.MERMAID:
            return f"""```mermaid
{self.code}
```"""
        elif self.format == DiagramFormat.PLANTUML:
            return f"""```plantuml
{self.code}
```"""
        elif self.format == DiagramFormat.D2:
            return f"""```d2
{self.code}
```"""
        else:
            return f"""```dot
{self.code}
```"""


@dataclass
class DiagramRequest:
    """Diyagram isteği."""
    description: str
    type: DiagramType
    preferred_format: DiagramFormat = DiagramFormat.MERMAID
    elements: List[str] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)


class DiagramGenerator:
    """
    Gelişmiş Diyagram Oluşturma Modülü
    
    Metinden otomatik diyagram oluşturur veya
    yapılandırılmış veriden diyagram üretir.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.default_format = DiagramFormat.MERMAID
    
    async def generate_from_text(
        self,
        content: str,
        diagram_type: DiagramType = DiagramType.FLOWCHART,
        preferred_format: DiagramFormat = DiagramFormat.MERMAID
    ) -> Diagram:
        """
        Metinden diyagram oluştur.
        
        Args:
            content: Kaynak metin
            diagram_type: Diyagram türü
            preferred_format: Tercih edilen format
            
        Returns:
            Oluşturulan diyagram
        """
        prompt = self._build_generation_prompt(content, diagram_type, preferred_format)
        
        response = await self._llm_call(prompt)
        
        # Kod bloğunu çıkar
        code = self._extract_diagram_code(response, preferred_format)
        
        return Diagram(
            type=diagram_type,
            format=preferred_format,
            code=code,
            title=f"{diagram_type.value.title()} Diyagramı"
        )
    
    async def generate_process_flow(
        self,
        steps: List[str],
        decisions: Optional[List[Dict[str, Any]]] = None,
        format: DiagramFormat = DiagramFormat.MERMAID
    ) -> Diagram:
        """
        Süreç akış diyagramı oluştur.
        
        Args:
            steps: Süreç adımları
            decisions: Karar noktaları
            format: Diyagram formatı
            
        Returns:
            Akış diyagramı
        """
        if format == DiagramFormat.MERMAID:
            code = self._generate_mermaid_flowchart(steps, decisions)
        elif format == DiagramFormat.PLANTUML:
            code = self._generate_plantuml_flowchart(steps, decisions)
        else:
            code = self._generate_mermaid_flowchart(steps, decisions)
        
        return Diagram(
            type=DiagramType.FLOWCHART,
            format=format,
            code=code,
            title="Süreç Akış Diyagramı"
        )
    
    async def generate_sequence_diagram(
        self,
        actors: List[str],
        interactions: List[Dict[str, str]],
        format: DiagramFormat = DiagramFormat.MERMAID
    ) -> Diagram:
        """
        Sekans diyagramı oluştur.
        
        Args:
            actors: Aktörler
            interactions: Etkileşimler
            format: Diyagram formatı
            
        Returns:
            Sekans diyagramı
        """
        if format == DiagramFormat.MERMAID:
            code = self._generate_mermaid_sequence(actors, interactions)
        elif format == DiagramFormat.PLANTUML:
            code = self._generate_plantuml_sequence(actors, interactions)
        else:
            code = self._generate_mermaid_sequence(actors, interactions)
        
        return Diagram(
            type=DiagramType.SEQUENCE,
            format=format,
            code=code,
            title="Sekans Diyagramı"
        )
    
    async def generate_mindmap(
        self,
        central_topic: str,
        branches: Dict[str, List[str]],
        format: DiagramFormat = DiagramFormat.MERMAID
    ) -> Diagram:
        """
        Zihin haritası oluştur.
        
        Args:
            central_topic: Merkezi konu
            branches: Dallar ve alt konular
            format: Diyagram formatı
            
        Returns:
            Zihin haritası
        """
        if format == DiagramFormat.MERMAID:
            code = self._generate_mermaid_mindmap(central_topic, branches)
        else:
            code = self._generate_mermaid_mindmap(central_topic, branches)
        
        return Diagram(
            type=DiagramType.MINDMAP,
            format=format,
            code=code,
            title="Zihin Haritası"
        )
    
    async def generate_class_diagram(
        self,
        classes: List[Dict[str, Any]],
        relationships: List[Dict[str, str]],
        format: DiagramFormat = DiagramFormat.MERMAID
    ) -> Diagram:
        """
        Sınıf diyagramı oluştur.
        
        Args:
            classes: Sınıf tanımları
            relationships: İlişkiler
            format: Diyagram formatı
            
        Returns:
            Sınıf diyagramı
        """
        if format == DiagramFormat.MERMAID:
            code = self._generate_mermaid_class(classes, relationships)
        elif format == DiagramFormat.PLANTUML:
            code = self._generate_plantuml_class(classes, relationships)
        else:
            code = self._generate_mermaid_class(classes, relationships)
        
        return Diagram(
            type=DiagramType.CLASS,
            format=format,
            code=code,
            title="Sınıf Diyagramı"
        )
    
    async def generate_architecture_diagram(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, str]],
        format: DiagramFormat = DiagramFormat.D2
    ) -> Diagram:
        """
        Mimari diyagramı oluştur.
        
        Args:
            components: Sistem bileşenleri
            connections: Bağlantılar
            format: Diyagram formatı
            
        Returns:
            Mimari diyagramı
        """
        if format == DiagramFormat.D2:
            code = self._generate_d2_architecture(components, connections)
        elif format == DiagramFormat.MERMAID:
            code = self._generate_mermaid_architecture(components, connections)
        else:
            code = self._generate_d2_architecture(components, connections)
        
        return Diagram(
            type=DiagramType.ARCHITECTURE,
            format=format,
            code=code,
            title="Sistem Mimarisi"
        )
    
    def _build_generation_prompt(
        self,
        content: str,
        diagram_type: DiagramType,
        format: DiagramFormat
    ) -> str:
        """LLM promptu oluştur."""
        format_examples = {
            DiagramFormat.MERMAID: """```mermaid
flowchart TD
    A[Başla] --> B{Karar}
    B -->|Evet| C[İşlem]
    B -->|Hayır| D[Son]
```""",
            DiagramFormat.PLANTUML: """```plantuml
@startuml
start
:Başla;
if (Karar?) then (evet)
  :İşlem;
else (hayır)
  :Son;
endif
@enduml
```""",
            DiagramFormat.D2: """```d2
start: Başla
decision: Karar {shape: diamond}
process: İşlem
end: Son

start -> decision
decision -> process: Evet
decision -> end: Hayır
```"""
        }
        
        return f"""Aşağıdaki metni analiz et ve {diagram_type.value} türünde {format.value} formatında bir diyagram oluştur.

## Metin:
{content[:3000]}

## Format Örneği:
{format_examples.get(format, format_examples[DiagramFormat.MERMAID])}

## Kurallar:
1. Sadece diyagram kodunu döndür
2. Açıklama ekleme
3. Türkçe etiketler kullan
4. Mantıklı ve anlaşılır bir akış oluştur

## Diyagram Kodu:"""
    
    def _generate_mermaid_flowchart(
        self,
        steps: List[str],
        decisions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Mermaid akış şeması oluştur."""
        lines = ["flowchart TD"]
        
        for i, step in enumerate(steps):
            node_id = f"S{i}"
            if i == 0:
                lines.append(f"    {node_id}([{step}])")
            elif i == len(steps) - 1:
                lines.append(f"    {node_id}([{step}])")
            else:
                lines.append(f"    {node_id}[{step}]")
        
        # Bağlantılar
        for i in range(len(steps) - 1):
            lines.append(f"    S{i} --> S{i+1}")
        
        return "\n".join(lines)
    
    def _generate_plantuml_flowchart(
        self,
        steps: List[str],
        decisions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """PlantUML akış şeması oluştur."""
        lines = ["@startuml", "start"]
        
        for step in steps:
            lines.append(f":{step};")
        
        lines.extend(["stop", "@enduml"])
        
        return "\n".join(lines)
    
    def _generate_mermaid_sequence(
        self,
        actors: List[str],
        interactions: List[Dict[str, str]]
    ) -> str:
        """Mermaid sekans diyagramı oluştur."""
        lines = ["sequenceDiagram"]
        
        # Aktörleri tanımla
        for actor in actors:
            lines.append(f"    participant {actor}")
        
        # Etkileşimleri ekle
        for interaction in interactions:
            from_actor = interaction.get("from", actors[0])
            to_actor = interaction.get("to", actors[1] if len(actors) > 1 else actors[0])
            message = interaction.get("message", "")
            arrow = interaction.get("arrow", "->>")
            
            lines.append(f"    {from_actor}{arrow}{to_actor}: {message}")
        
        return "\n".join(lines)
    
    def _generate_plantuml_sequence(
        self,
        actors: List[str],
        interactions: List[Dict[str, str]]
    ) -> str:
        """PlantUML sekans diyagramı oluştur."""
        lines = ["@startuml"]
        
        # Aktörler
        for actor in actors:
            lines.append(f'participant "{actor}" as {actor.replace(" ", "_")}')
        
        # Etkileşimler
        for interaction in interactions:
            from_actor = interaction.get("from", "").replace(" ", "_")
            to_actor = interaction.get("to", "").replace(" ", "_")
            message = interaction.get("message", "")
            
            lines.append(f"{from_actor} -> {to_actor}: {message}")
        
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    def _generate_mermaid_mindmap(
        self,
        central_topic: str,
        branches: Dict[str, List[str]]
    ) -> str:
        """Mermaid zihin haritası oluştur."""
        lines = ["mindmap", f"  root(({central_topic}))"]
        
        for branch, items in branches.items():
            lines.append(f"    {branch}")
            for item in items:
                lines.append(f"      {item}")
        
        return "\n".join(lines)
    
    def _generate_mermaid_class(
        self,
        classes: List[Dict[str, Any]],
        relationships: List[Dict[str, str]]
    ) -> str:
        """Mermaid sınıf diyagramı oluştur."""
        lines = ["classDiagram"]
        
        # Sınıfları tanımla
        for cls in classes:
            name = cls.get("name", "Class")
            attributes = cls.get("attributes", [])
            methods = cls.get("methods", [])
            
            lines.append(f"    class {name} {{")
            for attr in attributes:
                lines.append(f"        {attr}")
            for method in methods:
                lines.append(f"        {method}()")
            lines.append("    }")
        
        # İlişkiler
        for rel in relationships:
            from_cls = rel.get("from", "")
            to_cls = rel.get("to", "")
            rel_type = rel.get("type", "-->")
            
            lines.append(f"    {from_cls} {rel_type} {to_cls}")
        
        return "\n".join(lines)
    
    def _generate_plantuml_class(
        self,
        classes: List[Dict[str, Any]],
        relationships: List[Dict[str, str]]
    ) -> str:
        """PlantUML sınıf diyagramı oluştur."""
        lines = ["@startuml"]
        
        for cls in classes:
            name = cls.get("name", "Class")
            attributes = cls.get("attributes", [])
            methods = cls.get("methods", [])
            
            lines.append(f"class {name} {{")
            for attr in attributes:
                lines.append(f"    {attr}")
            for method in methods:
                lines.append(f"    {method}()")
            lines.append("}")
        
        for rel in relationships:
            lines.append(f"{rel.get('from', '')} --> {rel.get('to', '')}")
        
        lines.append("@enduml")
        
        return "\n".join(lines)
    
    def _generate_d2_architecture(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, str]]
    ) -> str:
        """D2 mimari diyagramı oluştur."""
        lines = []
        
        # Bileşenler
        for comp in components:
            name = comp.get("name", "Component")
            label = comp.get("label", name)
            shape = comp.get("shape", "rectangle")
            
            safe_name = name.replace(" ", "_").lower()
            lines.append(f"{safe_name}: {label} {{shape: {shape}}}")
        
        # Bağlantılar
        for conn in connections:
            from_comp = conn.get("from", "").replace(" ", "_").lower()
            to_comp = conn.get("to", "").replace(" ", "_").lower()
            label = conn.get("label", "")
            
            if label:
                lines.append(f"{from_comp} -> {to_comp}: {label}")
            else:
                lines.append(f"{from_comp} -> {to_comp}")
        
        return "\n".join(lines)
    
    def _generate_mermaid_architecture(
        self,
        components: List[Dict[str, Any]],
        connections: List[Dict[str, str]]
    ) -> str:
        """Mermaid mimari diyagramı oluştur."""
        lines = ["flowchart TB"]
        
        # Bileşenler
        for comp in components:
            name = comp.get("name", "").replace(" ", "_")
            label = comp.get("label", comp.get("name", ""))
            comp_type = comp.get("type", "service")
            
            if comp_type == "database":
                lines.append(f"    {name}[({label})]")
            elif comp_type == "user":
                lines.append(f"    {name}(({label}))")
            else:
                lines.append(f"    {name}[{label}]")
        
        # Bağlantılar
        for conn in connections:
            from_comp = conn.get("from", "").replace(" ", "_")
            to_comp = conn.get("to", "").replace(" ", "_")
            label = conn.get("label", "")
            
            if label:
                lines.append(f"    {from_comp} -->|{label}| {to_comp}")
            else:
                lines.append(f"    {from_comp} --> {to_comp}")
        
        return "\n".join(lines)
    
    def _extract_diagram_code(
        self,
        response: str,
        format: DiagramFormat
    ) -> str:
        """LLM yanıtından diyagram kodunu çıkar."""
        # Kod bloğu ara
        patterns = [
            rf'```{format.value}\n(.*?)```',
            rf'```mermaid\n(.*?)```',
            rf'```plantuml\n(.*?)```',
            rf'```d2\n(.*?)```',
            rf'```dot\n(.*?)```',
            r'```\n(.*?)```'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Kod bloğu yoksa tüm yanıtı döndür
        return response.strip()
    
    async def _llm_call(self, prompt: str, timeout: int = 180) -> str:
        """LLM çağrısı."""
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    llm_manager.chat,
                    messages=messages,
                    model_type="default"
                ),
                timeout=timeout
            )
            return response.get("content", "") if isinstance(response, dict) else str(response)
        except Exception as e:
            return f"Error: {str(e)}"
