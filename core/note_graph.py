"""
🧠 Note Graph - Not İlişki Grafiği
Obsidian tarzı not ilişkilerini görselleştirmek için graf yapısı.
"""

import json
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from core.logger import get_logger
from core.notes_manager import NotesManager, Note, notes_manager

logger = get_logger("note_graph")


@dataclass
class GraphNode:
    """Graf düğümü - her not bir düğüm."""
    id: str
    label: str
    title: str  # Full title
    color: str
    size: int = 20  # Bağlantı sayısına göre büyür
    folder_id: Optional[str] = None
    pinned: bool = False
    tags: List[str] = field(default_factory=list)
    x: Optional[float] = None  # Pozisyon (opsiyonel)
    y: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "data": {
                "label": self.label[:30] + "..." if len(self.label) > 30 else self.label,
                "title": self.title,
                "color": self.color,
                "folder_id": self.folder_id,
                "pinned": self.pinned,
                "tags": self.tags
            },
            "position": {"x": self.x or 0, "y": self.y or 0},
            "style": {
                "width": self.size * 2,
                "height": self.size * 2
            }
        }


@dataclass
class GraphEdge:
    """Graf kenarı - notlar arası bağlantı."""
    id: str
    source: str  # Kaynak not ID
    target: str  # Hedef not ID
    label: str = ""
    type: str = "default"  # default, wiki_link, similarity, tag_based
    strength: float = 1.0  # 0-1 arası
    animated: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "label": self.label,
            "type": self.type,
            "animated": self.animated,
            "style": {
                "strokeWidth": max(1, int(self.strength * 3)),
                "opacity": 0.5 + (self.strength * 0.5)
            },
            "data": {
                "strength": self.strength
            }
        }


class NoteGraph:
    """
    🧠 Not Grafiği Yönetici Sınıfı
    
    Notlar arası ilişkileri yönetir ve görselleştirme için veri sağlar.
    
    İlişki Türleri:
    - wiki_link: [[Not Adı]] şeklinde manuel bağlantılar
    - similarity: Semantik benzerlik (içerik bazlı)
    - tag_based: Ortak etiketler
    - folder: Aynı klasörde olma
    """
    
    LINK_PATTERN = r'\[\[([^\]]+)\]\]'
    
    def __init__(self, notes_manager: NotesManager = None, data_dir: str = "data/notes"):
        self._notes_manager = notes_manager
        self.data_dir = Path(data_dir)
        self.graph_file = self.data_dir / "graph.json"
        self.links_file = self.data_dir / "links.json"
        
        # Cache
        self._links_cache: Dict[str, List[str]] = {}  # note_id -> [linked_note_ids]
        self._backlinks_cache: Dict[str, List[str]] = {}  # note_id -> [notes that link to this]

    @property
    def notes_manager(self) -> NotesManager:
        """Lazy load notes_manager from singleton if not provided."""
        if self._notes_manager is None:
            from core.notes_manager import notes_manager as nm
            self._notes_manager = nm
        return self._notes_manager
    
    # ==================== WIKI LINK YÖNETİMİ ====================
    
    def extract_links(self, content: str) -> List[str]:
        """
        İçerikten [[wiki-style]] linkleri çıkar.
        
        Args:
            content: Not içeriği
        
        Returns:
            ["Bağlantılı Not 1", "Bağlantılı Not 2"]
        """
        if not content:
            return []
        
        matches = re.findall(self.LINK_PATTERN, content)
        return list(set(matches))
    
    def find_note_by_title(self, title: str) -> Optional[Note]:
        """Başlığa göre not bul."""
        all_notes = self.notes_manager.get_all_notes()
        title_lower = title.lower().strip()
        
        for note in all_notes:
            if note.title.lower().strip() == title_lower:
                return note
        
        return None
    
    def get_note_links(self, note_id: str) -> List[Dict[str, Any]]:
        """
        Bir notun tüm bağlantılarını getir.
        
        Returns:
            [{"note_id": "...", "title": "...", "type": "wiki_link"}]
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return []
        
        links = []
        
        # Wiki-style linkler
        wiki_titles = self.extract_links(note.content)
        for title in wiki_titles:
            linked_note = self.find_note_by_title(title)
            if linked_note:
                links.append({
                    "note_id": linked_note.id,
                    "title": linked_note.title,
                    "type": "wiki_link"
                })
            else:
                # Not bulunamadı - yaratılabilir
                links.append({
                    "note_id": None,
                    "title": title,
                    "type": "unresolved"
                })
        
        return links
    
    def get_backlinks(self, note_id: str) -> List[Dict[str, Any]]:
        """
        Bir nota bağlanan tüm notları getir (backlinks).
        
        Returns:
            [{"note_id": "...", "title": "...", "excerpt": "..."}]
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return []
        
        all_notes = self.notes_manager.get_all_notes()
        backlinks = []
        
        for other_note in all_notes:
            if other_note.id == note_id:
                continue
            
            # Bu not, hedef nota bağlanıyor mu?
            linked_titles = self.extract_links(other_note.content)
            if note.title.lower() in [t.lower() for t in linked_titles]:
                # Bağlantının bulunduğu bölümü çıkar
                excerpt = self._find_link_context(other_note.content, note.title)
                backlinks.append({
                    "note_id": other_note.id,
                    "title": other_note.title,
                    "excerpt": excerpt
                })
        
        return backlinks
    
    def _find_link_context(self, content: str, link_title: str, context_chars: int = 100) -> str:
        """Linkin bulunduğu bağlamı çıkar."""
        pattern = rf'\[\[{re.escape(link_title)}\]\]'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            start = max(0, match.start() - context_chars)
            end = min(len(content), match.end() + context_chars)
            excerpt = content[start:end]
            
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(content):
                excerpt = excerpt + "..."
            
            return excerpt
        
        return ""
    
    # ==================== GRAF OLUŞTURMA ====================
    
    def build_graph(
        self,
        include_orphans: bool = True,
        include_similarity: bool = True,
        similarity_threshold: float = 0.2,
        include_tags: bool = True,
        folder_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tüm notlar için graf verisi oluştur.
        
        Args:
            include_orphans: Bağlantısız notları dahil et
            include_similarity: Semantik benzerlik kenarları ekle
            similarity_threshold: Benzerlik eşiği
            include_tags: Tag bazlı bağlantıları ekle
            folder_filter: Belirli bir klasöre filtrele
        
        Returns:
            {
                "nodes": [GraphNode.to_dict(), ...],
                "edges": [GraphEdge.to_dict(), ...],
                "stats": {...}
            }
        """
        all_notes = self.notes_manager.get_all_notes()
        
        # Klasör filtresi
        if folder_filter:
            all_notes = [n for n in all_notes if n.folder_id == folder_filter]
        
        if not all_notes:
            return {"nodes": [], "edges": [], "stats": {}}
        
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        connected_ids: Set[str] = set()
        edge_id = 0
        
        # Her not için düğüm oluştur
        note_map = {n.id: n for n in all_notes}
        title_to_id = {n.title.lower(): n.id for n in all_notes}
        
        # Wiki linkleri için kenarlar
        for note in all_notes:
            linked_titles = self.extract_links(note.content)
            
            for title in linked_titles:
                target_id = title_to_id.get(title.lower())
                if target_id and target_id != note.id:
                    edges.append(GraphEdge(
                        id=f"e{edge_id}",
                        source=note.id,
                        target=target_id,
                        label="",
                        type="wiki_link",
                        strength=1.0,
                        animated=False
                    ))
                    edge_id += 1
                    connected_ids.add(note.id)
                    connected_ids.add(target_id)
        
        # Tag bazlı bağlantılar
        if include_tags:
            tag_notes: Dict[str, List[str]] = defaultdict(list)
            for note in all_notes:
                for tag in note.tags:
                    tag_notes[tag].append(note.id)
            
            for tag, note_ids in tag_notes.items():
                if len(note_ids) >= 2:
                    # Aynı etiketli notları bağla
                    for i in range(len(note_ids)):
                        for j in range(i + 1, len(note_ids)):
                            edges.append(GraphEdge(
                                id=f"e{edge_id}",
                                source=note_ids[i],
                                target=note_ids[j],
                                label=tag,
                                type="tag_based",
                                strength=0.6,
                                animated=False
                            ))
                            edge_id += 1
                            connected_ids.add(note_ids[i])
                            connected_ids.add(note_ids[j])
        
        # Benzerlik bazlı bağlantılar
        if include_similarity:
            for i, note1 in enumerate(all_notes):
                for note2 in all_notes[i + 1:]:
                    similarity = self._calculate_similarity(note1, note2)
                    if similarity >= similarity_threshold:
                        # Mevcut kenar var mı kontrol et
                        existing = any(
                            (e.source == note1.id and e.target == note2.id) or
                            (e.source == note2.id and e.target == note1.id)
                            for e in edges
                        )
                        if not existing:
                            edges.append(GraphEdge(
                                id=f"e{edge_id}",
                                source=note1.id,
                                target=note2.id,
                                type="similarity",
                                strength=similarity,
                                animated=True
                            ))
                            edge_id += 1
                            connected_ids.add(note1.id)
                            connected_ids.add(note2.id)
        
        # Düğümleri oluştur
        connection_counts = defaultdict(int)
        for edge in edges:
            connection_counts[edge.source] += 1
            connection_counts[edge.target] += 1
        
        # Her not için düğüm oluştur
        for note in all_notes:
            try:
                is_connected = note.id in connected_ids
                if not include_orphans and not is_connected:
                    continue
                
                # Boyut: Bağlantı sayısına göre
                conn_count = connection_counts[note.id]
                size = 15 + min(conn_count * 5, 30)
                
                # Pozisyon: Spiral layout
                idx = len(nodes)
                import math
                angle = idx * 0.5
                radius = 100 + idx * 20
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                
                # Ensure tags is a list
                tags = note.tags if isinstance(note.tags, list) else []
                
                nodes.append(GraphNode(
                    id=note.id,
                    label=note.title,
                    title=note.title,
                    color=note.color,
                    size=size,
                    folder_id=note.folder_id,
                    pinned=note.pinned,
                    tags=tags,
                    x=x,
                    y=y
                ))
            except Exception as e:
                logger.error(f"Error processing note {note.id} for graph: {e}")
                continue
        
        # İstatistikler
        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "connected_nodes": len(connected_ids),
            "orphan_nodes": len(nodes) - len(connected_ids),
            "wiki_links": len([e for e in edges if e.type == "wiki_link"]),
            "tag_links": len([e for e in edges if e.type == "tag_based"]),
            "similarity_links": len([e for e in edges if e.type == "similarity"])
        }
        
        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "stats": stats
        }
    
    def _calculate_similarity(self, note1: Note, note2: Note) -> float:
        """İki not arasındaki basit benzerliği hesapla."""
        text1 = f"{note1.title} {note1.content}".lower()
        text2 = f"{note2.title} {note2.content}".lower()
        
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    # ==================== GRAF ANALİZİ ====================
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Graf istatistiklerini döndür."""
        graph = self.build_graph()
        return graph["stats"]
    
    def get_central_notes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """En çok bağlantısı olan notları döndür."""
        graph = self.build_graph()
        
        # Bağlantı sayılarını hesapla
        connection_counts = defaultdict(int)
        for edge in graph["edges"]:
            connection_counts[edge["source"]] += 1
            connection_counts[edge["target"]] += 1
        
        # Sırala
        sorted_notes = sorted(
            connection_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        result = []
        for note_id, count in sorted_notes:
            note = self.notes_manager.get_note(note_id)
            if note:
                result.append({
                    "note": note.to_dict(),
                    "connection_count": count
                })
        
        return result
    
    def get_orphan_notes(self) -> List[Note]:
        """Hiçbir bağlantısı olmayan notları döndür."""
        graph = self.build_graph(include_orphans=True, include_similarity=False)
        
        connected_ids = set()
        for edge in graph["edges"]:
            connected_ids.add(edge["source"])
            connected_ids.add(edge["target"])
        
        all_notes = self.notes_manager.get_all_notes()
        orphans = [n for n in all_notes if n.id not in connected_ids]
        
        return orphans
    
    def suggest_connections(self, note_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Bir not için önerilen bağlantıları döndür.
        
        Returns:
            [{"note": Note, "reason": "Ortak etiket: python", "strength": 0.8}]
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return []
        
        all_notes = self.notes_manager.get_all_notes()
        suggestions = []
        
        # Mevcut bağlantıları al
        existing_links = set()
        for link in self.get_note_links(note_id):
            if link["note_id"]:
                existing_links.add(link["note_id"])
        
        for other_note in all_notes:
            if other_note.id == note_id or other_note.id in existing_links:
                continue
            
            # Benzerlik kontrolü
            similarity = self._calculate_similarity(note, other_note)
            
            # Ortak etiketler
            common_tags = set(note.tags) & set(other_note.tags)
            tag_bonus = len(common_tags) * 0.2
            
            total_score = similarity + tag_bonus
            
            if total_score > 0.15:
                reason = []
                if similarity > 0.1:
                    reason.append(f"İçerik benzerliği: %{int(similarity * 100)}")
                if common_tags:
                    reason.append(f"Ortak etiketler: {', '.join(common_tags)}")
                
                suggestions.append({
                    "note": other_note.to_dict(),
                    "reason": " | ".join(reason),
                    "strength": round(min(total_score, 1.0), 2)
                })
        
        # Sırala ve limitle
        suggestions.sort(key=lambda x: x["strength"], reverse=True)
        return suggestions[:limit]

    # ==================== PREMIUM FEATURES ====================
    
    def find_path(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """
        BFS ile iki not arasındaki en kısa yolu bul.
        
        Returns:
            {
                "path": ["id1", "id2", "id3"],
                "length": 2,
                "found": True
            }
        """
        from collections import deque
        
        # Graf oluştur
        graph_data = self.build_graph(include_orphans=True, include_similarity=True)
        
        # Adjacency list oluştur
        adjacency = defaultdict(set)
        for edge in graph_data["edges"]:
            adjacency[edge["source"]].add(edge["target"])
            adjacency[edge["target"]].add(edge["source"])
        
        # BFS
        if source_id == target_id:
            return {"path": [source_id], "length": 0, "found": True}
        
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in adjacency[current]:
                if neighbor == target_id:
                    final_path = path + [neighbor]
                    return {
                        "path": final_path,
                        "length": len(final_path) - 1,
                        "found": True
                    }
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return {"path": [], "length": -1, "found": False}
    
    def get_connection_counts(self) -> Dict[str, int]:
        """
        Her node için bağlantı sayısını hesapla (Heat Map için).
        
        Returns:
            {"note_id": connection_count, ...}
        """
        graph_data = self.build_graph(include_orphans=True, include_similarity=True)
        
        counts = defaultdict(int)
        for edge in graph_data["edges"]:
            counts[edge["source"]] += 1
            counts[edge["target"]] += 1
        
        return dict(counts)
    
    def get_node_details(self, note_id: str) -> Dict[str, Any]:
        """
        Not detaylarını sidebar için getir.
        
        Returns:
            {
                "id": "...",
                "title": "...",
                "content": "...",
                "preview": "...",
                "tags": [...],
                "color": "...",
                "connections": 5,
                "created_at": "...",
                "updated_at": "..."
            }
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return None
        
        # Bağlantı sayısı
        connection_counts = self.get_connection_counts()
        connections = connection_counts.get(note_id, 0)
        
        # İçerik önizlemesi
        content = note.content or ""
        preview = content[:500] + "..." if len(content) > 500 else content
        
        return {
            "id": note.id,
            "title": note.title,
            "content": content,
            "preview": preview,
            "tags": note.tags,
            "color": note.color,
            "connections": connections,
            "created_at": note.created_at.isoformat() if note.created_at else None,
            "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            "folder_id": note.folder_id,
            "pinned": note.pinned
        }
    
    def cluster_notes_by_similarity(self) -> Dict[str, Any]:
        """
        Notları benzerlik bazlı kümele.
        
        Returns:
            {
                "clusters": [
                    {"id": "cluster_0", "name": "Cluster 1", "color": "#...", "notes": ["id1", "id2"]},
                    ...
                ],
                "unclustered": ["id3", "id4"]
            }
        """
        all_notes = self.notes_manager.get_all_notes()
        if not all_notes:
            return {"clusters": [], "unclustered": []}
        
        # Simple clustering based on tags and title similarity
        tag_groups = defaultdict(list)
        unclustered = []
        
        for note in all_notes:
            if note.tags:
                # En popüler taga göre grupla
                primary_tag = note.tags[0]
                tag_groups[primary_tag].append(note.id)
            else:
                unclustered.append(note.id)
        
        # Cluster renkleri
        cluster_colors = [
            "#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", 
            "#ef4444", "#ec4899", "#06b6d4", "#84cc16"
        ]
        
        clusters = []
        for i, (tag, note_ids) in enumerate(tag_groups.items()):
            if len(note_ids) >= 1:  # En az 1 not olan gruplar
                clusters.append({
                    "id": f"cluster_{i}",
                    "name": tag.title(),
                    "color": cluster_colors[i % len(cluster_colors)],
                    "notes": note_ids
                })
        
        return {
            "clusters": clusters,
            "unclustered": unclustered
        }
    
    async def generate_ai_summary(self, note_id: str) -> str:
        """
        AI ile not özeti oluştur.
        
        Returns:
            Özet metni
        """
        note = self.notes_manager.get_note(note_id)
        if not note:
            return "Not bulunamadı."
        
        content = note.content or note.title
        if len(content) < 50:
            return content
        
        try:
            from core.llm_manager import llm_manager
            
            prompt = f"""Aşağıdaki notu 2-3 cümleyle özetle. Türkçe yaz.

Not Başlığı: {note.title}
Not İçeriği: {content[:2000]}

Özet:"""
            
            response = await llm_manager.generate(
                prompt=prompt,
                max_tokens=150,
                temperature=0.3
            )
            
            return response.strip() if response else "Özet oluşturulamadı."
        except Exception as e:
            logger.error(f"AI summary error: {e}")
            # Fallback: ilk 200 karakter
            return content[:200] + "..." if len(content) > 200 else content

# ==================== COLOR MAPPING ====================

NOTE_COLOR_MAP = {
    "yellow": "#fef3c7",
    "green": "#d1fae5",
    "blue": "#dbeafe",
    "pink": "#fce7f3",
    "purple": "#ede9fe",
    "orange": "#ffedd5",
    "red": "#fee2e2",
    "gray": "#f3f4f6",
    "default": "#ffffff"
}


# ==================== SINGLETON ====================

_note_graph: Optional[NoteGraph] = None

def get_note_graph(notes_manager=None) -> NoteGraph:
    """NoteGraph singleton instance'ı döndür."""
    global _note_graph
    if _note_graph is None:
        if notes_manager is None:
            from core.notes_manager import notes_manager as nm
            notes_manager = nm
        _note_graph = NoteGraph(notes_manager=notes_manager)
    return _note_graph
