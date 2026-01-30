"""
Knowledge Graph - Entity extraction and relationship mapping
Enhances RAG with semantic relationships
100% Local using NetworkX
"""

import asyncio
import hashlib
import json
import logging
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pickle

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed. Install with: pip install networkx")


@dataclass
class Entity:
    """A knowledge graph entity"""
    id: str
    name: str
    type: str  # person, organization, concept, location, event, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    mentions: List[str] = field(default_factory=list)  # Source document IDs
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Relationship:
    """A relationship between entities"""
    id: str
    source_id: str
    target_id: str
    type: str  # relates_to, works_at, located_in, part_of, etc.
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    mentions: List[str] = field(default_factory=list)


@dataclass
class GraphQuery:
    """Query result from knowledge graph"""
    entities: List[Entity]
    relationships: List[Relationship]
    paths: List[List[str]]
    context: str
    score: float


class KnowledgeGraph:
    """
    Knowledge Graph for enhanced RAG
    Uses NetworkX for graph operations
    """
    
    def __init__(self, storage_path: str = "data/knowledge_graph"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        if HAS_NETWORKX:
            self.graph = nx.DiGraph()
        else:
            self.graph = None
        
        self._load()
        
        # Entity type patterns for extraction
        self.entity_patterns = {
            "person": [
                r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # John Smith
                r'\b(Dr\.|Mr\.|Mrs\.|Ms\.) ([A-Z][a-z]+ [A-Z][a-z]+)\b',
            ],
            "organization": [
                r'\b([A-Z][A-Za-z]+ (?:Inc\.|Corp\.|Ltd\.|LLC|Company|Organization))\b',
                r'\b([A-Z][A-Z]+)\b',  # Acronyms like IBM, NASA
            ],
            "location": [
                r'\b([A-Z][a-z]+(?:, [A-Z][a-z]+)?)\b',
            ],
            "date": [
                r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
                r'\b(\d{4}-\d{2}-\d{2})\b',
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2},? \d{4}\b',
            ],
            "concept": [
                r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',  # Capitalized phrases
            ]
        }
        
        # Relationship patterns
        self.relationship_patterns = [
            (r'(\w+) works at (\w+)', "works_at"),
            (r'(\w+) is CEO of (\w+)', "leads"),
            (r'(\w+) founded (\w+)', "founded"),
            (r'(\w+) is part of (\w+)', "part_of"),
            (r'(\w+) is located in (\w+)', "located_in"),
            (r'(\w+) acquired (\w+)', "acquired"),
            (r'(\w+) partnered with (\w+)', "partners_with"),
            (r'(\w+) reports to (\w+)', "reports_to"),
            (r'(\w+) created (\w+)', "created"),
            (r'(\w+) uses (\w+)', "uses"),
        ]
    
    def _load(self):
        """Load graph from disk"""
        entities_file = self.storage_path / "entities.json"
        relationships_file = self.storage_path / "relationships.json"
        graph_file = self.storage_path / "graph.pkl"
        
        if entities_file.exists():
            try:
                data = json.loads(entities_file.read_text(encoding='utf-8'))
                self.entities = {
                    e["id"]: Entity(**e) for e in data
                }
            except Exception as e:
                logger.error(f"Failed to load entities: {e}")
        
        if relationships_file.exists():
            try:
                data = json.loads(relationships_file.read_text(encoding='utf-8'))
                self.relationships = {
                    r["id"]: Relationship(**r) for r in data
                }
            except Exception as e:
                logger.error(f"Failed to load relationships: {e}")
        
        # Rebuild graph
        if HAS_NETWORKX and self.entities:
            self._rebuild_graph()
    
    def _save(self):
        """Save graph to disk"""
        entities_file = self.storage_path / "entities.json"
        relationships_file = self.storage_path / "relationships.json"
        
        entities_file.write_text(
            json.dumps([
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "properties": e.properties,
                    "mentions": e.mentions,
                    "created_at": e.created_at
                }
                for e in self.entities.values()
            ], indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        relationships_file.write_text(
            json.dumps([
                {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type,
                    "properties": r.properties,
                    "weight": r.weight,
                    "mentions": r.mentions
                }
                for r in self.relationships.values()
            ], indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def _rebuild_graph(self):
        """Rebuild NetworkX graph from entities and relationships"""
        if not HAS_NETWORKX:
            return
        
        self.graph = nx.DiGraph()
        
        for entity in self.entities.values():
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type,
                **entity.properties
            )
        
        for rel in self.relationships.values():
            self.graph.add_edge(
                rel.source_id,
                rel.target_id,
                id=rel.id,
                type=rel.type,
                weight=rel.weight,
                **rel.properties
            )
    
    def _generate_entity_id(self, name: str, entity_type: str) -> str:
        """Generate consistent ID for entity"""
        key = f"{entity_type}:{name.lower().strip()}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    # CRUD Operations
    
    def add_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[Dict] = None,
        source_doc: Optional[str] = None
    ) -> Entity:
        """Add or update an entity"""
        entity_id = self._generate_entity_id(name, entity_type)
        
        if entity_id in self.entities:
            # Update existing
            entity = self.entities[entity_id]
            if properties:
                entity.properties.update(properties)
            if source_doc and source_doc not in entity.mentions:
                entity.mentions.append(source_doc)
        else:
            # Create new
            entity = Entity(
                id=entity_id,
                name=name,
                type=entity_type,
                properties=properties or {},
                mentions=[source_doc] if source_doc else []
            )
            self.entities[entity_id] = entity
            
            if HAS_NETWORKX:
                self.graph.add_node(
                    entity_id,
                    name=name,
                    type=entity_type,
                    **(properties or {})
                )
        
        self._save()
        return entity
    
    def add_relationship(
        self,
        source_name: str,
        source_type: str,
        target_name: str,
        target_type: str,
        relationship_type: str,
        properties: Optional[Dict] = None,
        source_doc: Optional[str] = None
    ) -> Relationship:
        """Add or update a relationship"""
        # Ensure entities exist
        source_entity = self.add_entity(source_name, source_type, source_doc=source_doc)
        target_entity = self.add_entity(target_name, target_type, source_doc=source_doc)
        
        # Create relationship ID
        rel_id = hashlib.md5(
            f"{source_entity.id}:{relationship_type}:{target_entity.id}".encode()
        ).hexdigest()[:12]
        
        if rel_id in self.relationships:
            # Update existing
            rel = self.relationships[rel_id]
            rel.weight += 0.5  # Increase weight on re-mention
            if properties:
                rel.properties.update(properties)
            if source_doc and source_doc not in rel.mentions:
                rel.mentions.append(source_doc)
        else:
            # Create new
            rel = Relationship(
                id=rel_id,
                source_id=source_entity.id,
                target_id=target_entity.id,
                type=relationship_type,
                properties=properties or {},
                mentions=[source_doc] if source_doc else []
            )
            self.relationships[rel_id] = rel
            
            if HAS_NETWORKX:
                self.graph.add_edge(
                    source_entity.id,
                    target_entity.id,
                    id=rel_id,
                    type=relationship_type,
                    weight=rel.weight,
                    **(properties or {})
                )
        
        self._save()
        return rel
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def find_entity(self, name: str) -> Optional[Entity]:
        """Find entity by name"""
        name_lower = name.lower().strip()
        for entity in self.entities.values():
            if entity.name.lower() == name_lower:
                return entity
        return None
    
    def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Entity]:
        """Search entities by name"""
        query_lower = query.lower()
        results = []
        
        for entity in self.entities.values():
            if entity_type and entity.type != entity_type:
                continue
            
            if query_lower in entity.name.lower():
                results.append(entity)
        
        return results[:limit]
    
    def get_entity_relationships(
        self,
        entity_id: str,
        direction: str = "both"  # "in", "out", "both"
    ) -> List[Relationship]:
        """Get relationships for an entity"""
        results = []
        
        for rel in self.relationships.values():
            if direction in ("out", "both") and rel.source_id == entity_id:
                results.append(rel)
            elif direction in ("in", "both") and rel.target_id == entity_id:
                results.append(rel)
        
        return results
    
    def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1
    ) -> List[Entity]:
        """Get neighboring entities up to depth"""
        if not HAS_NETWORKX:
            # Fallback without NetworkX
            neighbors = set()
            for rel in self.get_entity_relationships(entity_id):
                if rel.source_id == entity_id:
                    neighbors.add(rel.target_id)
                else:
                    neighbors.add(rel.source_id)
            return [self.entities[eid] for eid in neighbors if eid in self.entities]
        
        # Use NetworkX BFS
        visited = set()
        to_visit = [(entity_id, 0)]
        
        while to_visit:
            current_id, current_depth = to_visit.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            if current_id in self.graph:
                for neighbor in self.graph.neighbors(current_id):
                    if neighbor not in visited:
                        to_visit.append((neighbor, current_depth + 1))
                for neighbor in self.graph.predecessors(current_id):
                    if neighbor not in visited:
                        to_visit.append((neighbor, current_depth + 1))
        
        visited.discard(entity_id)  # Remove self
        return [self.entities[eid] for eid in visited if eid in self.entities]
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between entities"""
        if not HAS_NETWORKX:
            return None
        
        try:
            path = nx.shortest_path(
                self.graph.to_undirected(),
                source_id,
                target_id
            )
            return path if len(path) <= max_depth else None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    # Extraction from text
    
    async def extract_entities_from_text(
        self,
        text: str,
        source_doc: Optional[str] = None,
        use_llm: bool = True
    ) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        if use_llm:
            # Use LLM for better extraction
            entities = await self._extract_entities_llm(text, source_doc)
        else:
            # Use regex patterns
            entities = self._extract_entities_regex(text, source_doc)
        
        return entities
    
    def _extract_entities_regex(
        self,
        text: str,
        source_doc: Optional[str] = None
    ) -> List[Entity]:
        """Extract entities using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match if isinstance(match, str) else " ".join(match)
                    if len(name) > 2:  # Skip very short matches
                        entity = self.add_entity(name, entity_type, source_doc=source_doc)
                        entities.append(entity)
        
        return entities
    
    async def _extract_entities_llm(
        self,
        text: str,
        source_doc: Optional[str] = None
    ) -> List[Entity]:
        """Extract entities using LLM"""
        try:
            from core.llm_client import get_llm_client
            
            llm = await get_llm_client()
            
            prompt = f"""Extract all named entities from the following text. 
For each entity, provide:
- name: The entity name
- type: One of (person, organization, location, concept, event, product, technology)

Return as JSON array:
[{{"name": "...", "type": "..."}}]

Text:
{text[:2000]}

Entities (JSON only):"""
            
            response = await llm.chat(prompt)
            
            # Parse JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities_data = json.loads(json_match.group())
                
                entities = []
                for ed in entities_data:
                    if "name" in ed and "type" in ed:
                        entity = self.add_entity(
                            ed["name"],
                            ed["type"],
                            source_doc=source_doc
                        )
                        entities.append(entity)
                
                return entities
        
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
        
        # Fallback to regex
        return self._extract_entities_regex(text, source_doc)
    
    async def extract_relationships_from_text(
        self,
        text: str,
        source_doc: Optional[str] = None
    ) -> List[Relationship]:
        """Extract relationships from text using LLM"""
        try:
            from core.llm_client import get_llm_client
            
            llm = await get_llm_client()
            
            prompt = f"""Extract relationships between entities from the following text.
For each relationship, provide:
- source: Source entity name
- source_type: Entity type
- target: Target entity name  
- target_type: Entity type
- relationship: Type of relationship (works_at, founded, part_of, located_in, created, uses, etc.)

Return as JSON array:
[{{"source": "...", "source_type": "...", "target": "...", "target_type": "...", "relationship": "..."}}]

Text:
{text[:2000]}

Relationships (JSON only):"""
            
            response = await llm.chat(prompt)
            
            # Parse JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                rels_data = json.loads(json_match.group())
                
                relationships = []
                for rd in rels_data:
                    try:
                        rel = self.add_relationship(
                            rd["source"],
                            rd.get("source_type", "concept"),
                            rd["target"],
                            rd.get("target_type", "concept"),
                            rd["relationship"],
                            source_doc=source_doc
                        )
                        relationships.append(rel)
                    except (KeyError, ValueError, TypeError) as e:
                        logger.debug(f"Skipping invalid relationship: {e}")
                        continue
                
                return relationships
        
        except Exception as e:
            logger.error(f"LLM relationship extraction failed: {e}")
        
        return []
    
    # Graph queries
    
    def query(
        self,
        query_text: str,
        top_k: int = 10
    ) -> GraphQuery:
        """Query the knowledge graph"""
        # Find relevant entities
        query_words = query_text.lower().split()
        
        entity_scores: Dict[str, float] = defaultdict(float)
        
        for entity in self.entities.values():
            name_lower = entity.name.lower()
            for word in query_words:
                if word in name_lower:
                    entity_scores[entity.id] += 1.0
        
        # Get top entities
        top_entity_ids = sorted(
            entity_scores.keys(),
            key=lambda x: entity_scores[x],
            reverse=True
        )[:top_k]
        
        top_entities = [self.entities[eid] for eid in top_entity_ids]
        
        # Get relationships between top entities
        relevant_rels = []
        entity_id_set = set(top_entity_ids)
        
        for rel in self.relationships.values():
            if rel.source_id in entity_id_set or rel.target_id in entity_id_set:
                relevant_rels.append(rel)
        
        # Find paths between top 2 entities
        paths = []
        if len(top_entity_ids) >= 2 and HAS_NETWORKX:
            path = self.find_path(top_entity_ids[0], top_entity_ids[1])
            if path:
                paths.append(path)
        
        # Generate context
        context = self._generate_context(top_entities, relevant_rels)
        
        return GraphQuery(
            entities=top_entities,
            relationships=relevant_rels,
            paths=paths,
            context=context,
            score=max(entity_scores.values()) if entity_scores else 0.0
        )
    
    def _generate_context(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> str:
        """Generate natural language context from graph data"""
        lines = []
        
        # Entity descriptions
        for entity in entities[:5]:
            lines.append(f"- {entity.name} ({entity.type})")
        
        # Relationship descriptions
        for rel in relationships[:10]:
            source = self.entities.get(rel.source_id)
            target = self.entities.get(rel.target_id)
            if source and target:
                lines.append(f"- {source.name} {rel.type.replace('_', ' ')} {target.name}")
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict:
        """Get graph statistics"""
        stats = {
            "entity_count": len(self.entities),
            "relationship_count": len(self.relationships),
            "entity_types": defaultdict(int),
            "relationship_types": defaultdict(int)
        }
        
        for entity in self.entities.values():
            stats["entity_types"][entity.type] += 1
        
        for rel in self.relationships.values():
            stats["relationship_types"][rel.type] += 1
        
        stats["entity_types"] = dict(stats["entity_types"])
        stats["relationship_types"] = dict(stats["relationship_types"])
        
        if HAS_NETWORKX and self.graph:
            stats["graph_density"] = nx.density(self.graph)
            stats["connected_components"] = nx.number_weakly_connected_components(self.graph)
        
        return stats
    
    def export_to_json(self) -> Dict:
        """Export graph to JSON format"""
        return {
            "entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "properties": e.properties
                }
                for e in self.entities.values()
            ],
            "relationships": [
                {
                    "id": r.id,
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.type,
                    "weight": r.weight
                }
                for r in self.relationships.values()
            ]
        }
    
    def clear(self):
        """Clear all data"""
        self.entities.clear()
        self.relationships.clear()
        if HAS_NETWORKX:
            self.graph = nx.DiGraph()
        self._save()


# Global instance
knowledge_graph = KnowledgeGraph()


def get_knowledge_graph() -> KnowledgeGraph:
    """Get knowledge graph instance"""
    return knowledge_graph
