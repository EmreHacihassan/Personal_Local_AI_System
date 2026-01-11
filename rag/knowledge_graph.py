"""
Enterprise AI Assistant - Knowledge Graph Module
Graf tabanlı bilgi yönetimi

Entity extraction, relation mapping, graph queries.
"""

import sqlite3
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from core.config import settings


@dataclass
class Entity:
    """Graf varlığı."""
    id: str
    name: str
    entity_type: str  # PERSON, ORG, LOCATION, CONCEPT, DOCUMENT, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
        }


@dataclass 
class Relation:
    """Graf ilişkisi."""
    id: str
    source_id: str
    target_id: str
    relation_type: str  # WORKS_AT, LOCATED_IN, MENTIONS, RELATED_TO, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type,
            "properties": self.properties,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
        }


class EntityExtractor:
    """
    LLM tabanlı entity çıkarıcı.
    
    Metinden varlıkları ve ilişkileri çıkarır.
    """
    
    def __init__(self, llm_manager=None):
        """Extractor başlat."""
        self._llm = llm_manager
    
    def _lazy_load(self):
        """Lazy loading."""
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Metinden varlıkları çıkar.
        
        Args:
            text: Kaynak metin
            
        Returns:
            Varlık listesi
        """
        self._lazy_load()
        
        prompt = f"""Aşağıdaki metinden önemli varlıkları (entity) çıkar.
Her varlık için JSON formatında döndür.

Varlık türleri: PERSON, ORGANIZATION, LOCATION, DATE, CONCEPT, DOCUMENT, PRODUCT, EVENT

Metin:
{text[:2000]}

JSON formatında çıktı (liste olarak):
[{{"name": "...", "type": "...", "description": "..."}}]

Varlıklar:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=500)
            
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                return entities
        except Exception:
            pass
        
        return []
    
    def extract_relations(
        self,
        text: str,
        entities: List[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Varlıklar arası ilişkileri çıkar.
        
        Args:
            text: Kaynak metin
            entities: Bulunan varlıklar
            
        Returns:
            İlişki listesi
        """
        self._lazy_load()
        
        entity_names = [e["name"] for e in entities[:10]]
        
        prompt = f"""Aşağıdaki metinde, verilen varlıklar arasındaki ilişkileri bul.

Varlıklar: {', '.join(entity_names)}

Metin:
{text[:1500]}

İlişki türleri: WORKS_AT, LOCATED_IN, PART_OF, RELATED_TO, CREATED_BY, MENTIONS

JSON formatında çıktı:
[{{"source": "...", "target": "...", "relation": "...", "description": "..."}}]

İlişkiler:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=400)
            
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                relations = json.loads(json_match.group())
                return relations
        except Exception:
            pass
        
        return []


class KnowledgeGraph:
    """
    Knowledge Graph veritabanı.
    
    Graf yapısında bilgi saklama ve sorgulama.
    """
    
    def __init__(self, db_path: Path = None):
        """Knowledge graph başlat."""
        self.db_path = db_path or settings.DATA_DIR / "knowledge_graph.db"
        self.extractor = EntityExtractor()
        self._init_db()
    
    def _init_db(self):
        """Veritabanını başlat."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    properties TEXT,
                    embedding TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_name 
                ON entities(name)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_type 
                ON entities(entity_type)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    properties TEXT,
                    weight REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relation_source 
                ON relations(source_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relation_target 
                ON relations(target_id)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_relation_type 
                ON relations(relation_type)
            """)
            
            conn.commit()
    
    def add_entity(self, entity: Entity) -> str:
        """Varlık ekle."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO entities 
                (id, name, entity_type, properties, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                entity.id,
                entity.name,
                entity.entity_type,
                json.dumps(entity.properties),
                entity.created_at.isoformat(),
            ))
            conn.commit()
        
        return entity.id
    
    def add_relation(self, relation: Relation) -> str:
        """İlişki ekle."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO relations
                (id, source_id, target_id, relation_type, properties, weight, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                relation.id,
                relation.source_id,
                relation.target_id,
                relation.relation_type,
                json.dumps(relation.properties),
                relation.weight,
                relation.created_at.isoformat(),
            ))
            conn.commit()
        
        return relation.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Varlık al."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM entities WHERE id = ?",
                (entity_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Entity(
                    id=row["id"],
                    name=row["name"],
                    entity_type=row["entity_type"],
                    properties=json.loads(row["properties"] or "{}"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
        return None
    
    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """İsme göre varlık bul."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM entities WHERE name LIKE ?",
                (f"%{name}%",)
            )
            row = cursor.fetchone()
            
            if row:
                return Entity(
                    id=row["id"],
                    name=row["name"],
                    entity_type=row["entity_type"],
                    properties=json.loads(row["properties"] or "{}"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
        return None
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: str = None,
        direction: str = "both",
    ) -> List[Tuple[Entity, Relation]]:
        """
        Varlığın komşularını al.
        
        Args:
            entity_id: Varlık ID
            relation_type: Filtre için ilişki türü
            direction: "outgoing", "incoming", "both"
            
        Returns:
            (Komşu varlık, ilişki) listesi
        """
        neighbors = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if direction in ["outgoing", "both"]:
                query = """
                    SELECT e.*, r.id as rel_id, r.relation_type, r.properties as rel_props, r.weight
                    FROM entities e
                    JOIN relations r ON e.id = r.target_id
                    WHERE r.source_id = ?
                """
                params = [entity_id]
                
                if relation_type:
                    query += " AND r.relation_type = ?"
                    params.append(relation_type)
                
                for row in conn.execute(query, params):
                    entity = Entity(
                        id=row["id"],
                        name=row["name"],
                        entity_type=row["entity_type"],
                        properties=json.loads(row["properties"] or "{}"),
                    )
                    relation = Relation(
                        id=row["rel_id"],
                        source_id=entity_id,
                        target_id=row["id"],
                        relation_type=row["relation_type"],
                        properties=json.loads(row["rel_props"] or "{}"),
                        weight=row["weight"],
                    )
                    neighbors.append((entity, relation))
            
            if direction in ["incoming", "both"]:
                query = """
                    SELECT e.*, r.id as rel_id, r.relation_type, r.properties as rel_props, r.weight
                    FROM entities e
                    JOIN relations r ON e.id = r.source_id
                    WHERE r.target_id = ?
                """
                params = [entity_id]
                
                if relation_type:
                    query += " AND r.relation_type = ?"
                    params.append(relation_type)
                
                for row in conn.execute(query, params):
                    entity = Entity(
                        id=row["id"],
                        name=row["name"],
                        entity_type=row["entity_type"],
                        properties=json.loads(row["properties"] or "{}"),
                    )
                    relation = Relation(
                        id=row["rel_id"],
                        source_id=row["id"],
                        target_id=entity_id,
                        relation_type=row["relation_type"],
                        properties=json.loads(row["rel_props"] or "{}"),
                        weight=row["weight"],
                    )
                    neighbors.append((entity, relation))
        
        return neighbors
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 4,
    ) -> List[List[str]]:
        """
        İki varlık arasındaki yolları bul (BFS).
        
        Args:
            start_id: Başlangıç varlığı
            end_id: Hedef varlık
            max_depth: Maksimum derinlik
            
        Returns:
            Yol listesi (her yol entity ID listesi)
        """
        if start_id == end_id:
            return [[start_id]]
        
        paths = []
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue and len(paths) < 5:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            neighbors = self.get_neighbors(current)
            
            for neighbor_entity, _ in neighbors:
                neighbor_id = neighbor_entity.id
                
                if neighbor_id == end_id:
                    paths.append(path + [end_id])
                elif neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return paths
    
    def extract_and_add(self, text: str, source: str = None) -> Dict[str, int]:
        """
        Metinden varlık ve ilişkileri çıkar ve ekle.
        
        Args:
            text: Kaynak metin
            source: Kaynak döküman
            
        Returns:
            Eklenen varlık ve ilişki sayıları
        """
        import hashlib
        
        # Extract entities
        raw_entities = self.extractor.extract_entities(text)
        
        entity_map = {}  # name -> id
        added_entities = 0
        
        for e in raw_entities:
            entity_id = hashlib.md5(
                f"{e['name']}{e['type']}".encode()
            ).hexdigest()[:16]
            
            entity = Entity(
                id=entity_id,
                name=e["name"],
                entity_type=e["type"],
                properties={
                    "description": e.get("description", ""),
                    "source": source,
                },
            )
            
            self.add_entity(entity)
            entity_map[e["name"]] = entity_id
            added_entities += 1
        
        # Extract relations
        raw_relations = self.extractor.extract_relations(text, raw_entities)
        
        added_relations = 0
        
        for r in raw_relations:
            source_id = entity_map.get(r["source"])
            target_id = entity_map.get(r["target"])
            
            if source_id and target_id:
                relation_id = hashlib.md5(
                    f"{source_id}{target_id}{r['relation']}".encode()
                ).hexdigest()[:16]
                
                relation = Relation(
                    id=relation_id,
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=r["relation"],
                    properties={"description": r.get("description", "")},
                )
                
                self.add_relation(relation)
                added_relations += 1
        
        return {
            "entities_added": added_entities,
            "relations_added": added_relations,
        }
    
    def query_subgraph(
        self,
        query: str,
        max_entities: int = 20,
    ) -> Dict[str, Any]:
        """
        Sorguyla ilgili alt grafı getir.
        
        Args:
            query: Arama sorgusu
            max_entities: Maksimum varlık sayısı
            
        Returns:
            Alt graf (nodes ve edges)
        """
        nodes = []
        edges = []
        seen_ids = set()
        
        # Search entities
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Find matching entities
            cursor = conn.execute("""
                SELECT * FROM entities 
                WHERE name LIKE ? OR properties LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", max_entities))
            
            for row in cursor:
                entity_id = row["id"]
                if entity_id not in seen_ids:
                    seen_ids.add(entity_id)
                    nodes.append({
                        "id": entity_id,
                        "name": row["name"],
                        "type": row["entity_type"],
                    })
            
            # Get relations between found entities
            if seen_ids:
                placeholders = ",".join(["?"] * len(seen_ids))
                cursor = conn.execute(f"""
                    SELECT * FROM relations
                    WHERE source_id IN ({placeholders})
                    OR target_id IN ({placeholders})
                """, list(seen_ids) + list(seen_ids))
                
                for row in cursor:
                    edges.append({
                        "source": row["source_id"],
                        "target": row["target_id"],
                        "type": row["relation_type"],
                        "weight": row["weight"],
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "query": query,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Graf istatistikleri."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM entities")
            entity_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM relations")
            relation_count = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT entity_type, COUNT(*) as count 
                FROM entities 
                GROUP BY entity_type
            """)
            entity_types = {row[0]: row[1] for row in cursor}
            
            cursor = conn.execute("""
                SELECT relation_type, COUNT(*) as count 
                FROM relations 
                GROUP BY relation_type
            """)
            relation_types = {row[0]: row[1] for row in cursor}
            
            return {
                "total_entities": entity_count,
                "total_relations": relation_count,
                "entity_types": entity_types,
                "relation_types": relation_types,
            }


# Singleton instance
knowledge_graph = KnowledgeGraph()
