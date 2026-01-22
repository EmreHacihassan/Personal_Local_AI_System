"""
Enterprise Knowledge Graph Engine
=================================
Advanced graph-based knowledge representation with LLM-powered entity extraction,
semantic relationship inference, and interactive visualization.

Premium Features:
- LLM-Powered Entity Extraction (not just regex)
- Semantic Relationship Inference
- Graph Traversal & Query Engine
- D3.js/Cytoscape Compatible Export
- Auto-Linking Documents
- Knowledge Gap Detection
- Graph-Enhanced RAG
- Community Detection
- Path Finding & Recommendations
- Temporal Knowledge Tracking

100% Local Processing
"""

import asyncio
import hashlib
import json
import logging
import math
import pickle
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import threading

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    from networkx.algorithms import community
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed. Install with: pip install networkx")


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class EntityType(str, Enum):
    """Types of entities in the knowledge graph"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"
    TECHNOLOGY = "technology"
    PRODUCT = "product"
    EVENT = "event"
    DATE = "date"
    DOCUMENT = "document"
    TOPIC = "topic"
    SKILL = "skill"
    PROJECT = "project"
    CUSTOM = "custom"


class RelationType(str, Enum):
    """Types of relationships between entities"""
    # General
    RELATES_TO = "relates_to"
    IS_A = "is_a"
    PART_OF = "part_of"
    HAS = "has"
    
    # Person relationships
    WORKS_AT = "works_at"
    KNOWS = "knows"
    CREATED_BY = "created_by"
    MANAGED_BY = "managed_by"
    COLLABORATES_WITH = "collaborates_with"
    
    # Location relationships
    LOCATED_IN = "located_in"
    NEAR = "near"
    
    # Temporal relationships
    BEFORE = "before"
    AFTER = "after"
    DURING = "during"
    
    # Semantic relationships
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"
    DEPENDS_ON = "depends_on"
    ENABLES = "enables"
    CAUSES = "causes"
    
    # Document relationships
    MENTIONS = "mentions"
    REFERENCES = "references"
    ABOUT = "about"
    
    # Custom
    CUSTOM = "custom"


class ImportanceLevel(str, Enum):
    """Entity/relationship importance"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Entity:
    """An entity in the knowledge graph"""
    id: str
    name: str
    type: EntityType
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    confidence: float = 0.8
    
    # Source tracking
    sources: List[str] = field(default_factory=list)  # Document IDs
    mentions_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    # Embedding for semantic operations
    embedding: Optional[List[float]] = None
    
    # Graph metrics (computed)
    centrality: float = 0.0
    community_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value if isinstance(self.type, EntityType) else self.type,
            "description": self.description,
            "properties": self.properties,
            "aliases": self.aliases,
            "importance": self.importance.value if isinstance(self.importance, ImportanceLevel) else self.importance,
            "confidence": self.confidence,
            "sources": self.sources,
            "mentions_count": self.mentions_count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "centrality": self.centrality,
            "community_id": self.community_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        entity = cls(
            id=data["id"],
            name=data["name"],
            type=EntityType(data.get("type", "concept"))
        )
        entity.description = data.get("description", "")
        entity.properties = data.get("properties", {})
        entity.aliases = data.get("aliases", [])
        entity.importance = ImportanceLevel(data.get("importance", "medium"))
        entity.confidence = data.get("confidence", 0.8)
        entity.sources = data.get("sources", [])
        entity.mentions_count = data.get("mentions_count", 1)
        if data.get("first_seen"):
            entity.first_seen = datetime.fromisoformat(data["first_seen"])
        if data.get("last_seen"):
            entity.last_seen = datetime.fromisoformat(data["last_seen"])
        entity.centrality = data.get("centrality", 0.0)
        entity.community_id = data.get("community_id")
        return entity


@dataclass
class Relationship:
    """A relationship between two entities"""
    id: str
    source_id: str
    target_id: str
    type: RelationType
    label: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    confidence: float = 0.8
    bidirectional: bool = False
    
    # Source tracking
    sources: List[str] = field(default_factory=list)
    mentions_count: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    # Temporal validity
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value if isinstance(self.type, RelationType) else self.type,
            "label": self.label,
            "properties": self.properties,
            "weight": self.weight,
            "confidence": self.confidence,
            "bidirectional": self.bidirectional,
            "sources": self.sources,
            "mentions_count": self.mentions_count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        rel = cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=RelationType(data.get("type", "relates_to"))
        )
        rel.label = data.get("label", "")
        rel.properties = data.get("properties", {})
        rel.weight = data.get("weight", 1.0)
        rel.confidence = data.get("confidence", 0.8)
        rel.bidirectional = data.get("bidirectional", False)
        rel.sources = data.get("sources", [])
        rel.mentions_count = data.get("mentions_count", 1)
        return rel


@dataclass
class GraphPath:
    """A path through the knowledge graph"""
    nodes: List[str]  # Entity IDs
    edges: List[str]  # Relationship IDs
    total_weight: float = 0.0
    confidence: float = 1.0
    explanation: str = ""


@dataclass
class GraphQuery:
    """Query for the knowledge graph"""
    query_text: str
    entity_types: Optional[List[EntityType]] = None
    relationship_types: Optional[List[RelationType]] = None
    max_hops: int = 3
    min_confidence: float = 0.5
    include_paths: bool = True
    limit: int = 20


@dataclass
class GraphQueryResult:
    """Result from a graph query"""
    entities: List[Entity]
    relationships: List[Relationship]
    paths: List[GraphPath]
    subgraph: Optional[Dict[str, Any]] = None  # For visualization
    context: str = ""
    relevance_score: float = 0.0
    query_time_ms: float = 0.0


@dataclass
class KnowledgeGap:
    """Detected gap in knowledge"""
    entity_id: str
    entity_name: str
    gap_type: str  # missing_description, low_confidence, few_connections, missing_type
    description: str
    severity: str  # high, medium, low
    suggestions: List[str]


@dataclass
class ExtractionResult:
    """Result from entity/relationship extraction"""
    entities: List[Entity]
    relationships: List[Relationship]
    document_id: str
    extraction_time_ms: float
    confidence: float


# =============================================================================
# LLM-POWERED ENTITY EXTRACTOR
# =============================================================================

class LLMEntityExtractor:
    """
    Uses LLM to extract entities and relationships from text.
    Much more powerful than regex-based extraction.
    """
    
    def __init__(self):
        self._llm = None
        self._embedding = None
    
    def _get_llm(self):
        if self._llm is None:
            try:
                from core.llm_manager import llm_manager
                self._llm = llm_manager
            except:
                pass
        return self._llm
    
    def _get_embedding(self):
        if self._embedding is None:
            try:
                from core.embedding import embedding_manager
                self._embedding = embedding_manager
            except:
                pass
        return self._embedding
    
    async def extract_entities(
        self,
        text: str,
        document_id: str = "",
        existing_entities: Optional[List[Entity]] = None
    ) -> ExtractionResult:
        """Extract entities from text using LLM"""
        import time
        start_time = time.time()
        
        entities = []
        relationships = []
        
        llm = self._get_llm()
        if not llm:
            # Fallback to regex-based extraction
            return self._regex_extract(text, document_id)
        
        # Prepare context with existing entities if available
        existing_context = ""
        if existing_entities:
            existing_names = [e.name for e in existing_entities[:20]]
            existing_context = f"\nBilinen varlıklar: {', '.join(existing_names)}"
        
        extraction_prompt = f"""Aşağıdaki metinden varlıkları (entities) ve ilişkileri (relationships) çıkar.

Metin:
{text[:3000]}
{existing_context}

JSON formatında yanıt ver:
{{
  "entities": [
    {{
      "name": "varlık adı",
      "type": "person/organization/location/concept/technology/product/event/date/topic/skill/project",
      "description": "kısa açıklama",
      "aliases": ["alternatif isimler"],
      "properties": {{"key": "value"}}
    }}
  ],
  "relationships": [
    {{
      "source": "kaynak varlık adı",
      "target": "hedef varlık adı",
      "type": "relates_to/is_a/part_of/works_at/knows/created_by/similar_to/depends_on/mentions",
      "label": "ilişki açıklaması"
    }}
  ]
}}

Sadece JSON yanıtla, başka bir şey yazma."""

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm.generate(extraction_prompt, max_tokens=2000)
            )
            
            # Parse JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                # Create entities
                for ent_data in data.get("entities", []):
                    entity = Entity(
                        id=str(uuid.uuid4()),
                        name=ent_data.get("name", ""),
                        type=self._parse_entity_type(ent_data.get("type", "concept")),
                        description=ent_data.get("description", ""),
                        aliases=ent_data.get("aliases", []),
                        properties=ent_data.get("properties", {}),
                        sources=[document_id] if document_id else [],
                        confidence=0.85
                    )
                    
                    # Get embedding
                    embedding_manager = self._get_embedding()
                    if embedding_manager:
                        try:
                            entity.embedding = embedding_manager.embed(
                                f"{entity.name} {entity.description}"
                            )
                        except:
                            pass
                    
                    entities.append(entity)
                
                # Create relationships
                entity_name_map = {e.name.lower(): e.id for e in entities}
                
                for rel_data in data.get("relationships", []):
                    source_name = rel_data.get("source", "").lower()
                    target_name = rel_data.get("target", "").lower()
                    
                    source_id = entity_name_map.get(source_name)
                    target_id = entity_name_map.get(target_name)
                    
                    if source_id and target_id:
                        relationship = Relationship(
                            id=str(uuid.uuid4()),
                            source_id=source_id,
                            target_id=target_id,
                            type=self._parse_relation_type(rel_data.get("type", "relates_to")),
                            label=rel_data.get("label", ""),
                            sources=[document_id] if document_id else [],
                            confidence=0.8
                        )
                        relationships.append(relationship)
        
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._regex_extract(text, document_id)
        
        extraction_time = (time.time() - start_time) * 1000
        
        return ExtractionResult(
            entities=entities,
            relationships=relationships,
            document_id=document_id,
            extraction_time_ms=extraction_time,
            confidence=0.85 if entities else 0.0
        )
    
    def _parse_entity_type(self, type_str: str) -> EntityType:
        """Parse entity type from string"""
        type_map = {
            "person": EntityType.PERSON,
            "kişi": EntityType.PERSON,
            "organization": EntityType.ORGANIZATION,
            "kuruluş": EntityType.ORGANIZATION,
            "şirket": EntityType.ORGANIZATION,
            "location": EntityType.LOCATION,
            "konum": EntityType.LOCATION,
            "yer": EntityType.LOCATION,
            "concept": EntityType.CONCEPT,
            "kavram": EntityType.CONCEPT,
            "technology": EntityType.TECHNOLOGY,
            "teknoloji": EntityType.TECHNOLOGY,
            "product": EntityType.PRODUCT,
            "ürün": EntityType.PRODUCT,
            "event": EntityType.EVENT,
            "olay": EntityType.EVENT,
            "date": EntityType.DATE,
            "tarih": EntityType.DATE,
            "topic": EntityType.TOPIC,
            "konu": EntityType.TOPIC,
            "skill": EntityType.SKILL,
            "beceri": EntityType.SKILL,
            "project": EntityType.PROJECT,
            "proje": EntityType.PROJECT
        }
        return type_map.get(type_str.lower(), EntityType.CONCEPT)
    
    def _parse_relation_type(self, type_str: str) -> RelationType:
        """Parse relationship type from string"""
        type_map = {
            "relates_to": RelationType.RELATES_TO,
            "is_a": RelationType.IS_A,
            "part_of": RelationType.PART_OF,
            "has": RelationType.HAS,
            "works_at": RelationType.WORKS_AT,
            "knows": RelationType.KNOWS,
            "created_by": RelationType.CREATED_BY,
            "managed_by": RelationType.MANAGED_BY,
            "located_in": RelationType.LOCATED_IN,
            "similar_to": RelationType.SIMILAR_TO,
            "depends_on": RelationType.DEPENDS_ON,
            "enables": RelationType.ENABLES,
            "causes": RelationType.CAUSES,
            "mentions": RelationType.MENTIONS,
            "references": RelationType.REFERENCES,
            "about": RelationType.ABOUT
        }
        return type_map.get(type_str.lower(), RelationType.RELATES_TO)
    
    def _regex_extract(self, text: str, document_id: str) -> ExtractionResult:
        """Fallback regex-based extraction"""
        import time
        start_time = time.time()
        
        entities = []
        
        # Basic patterns
        patterns = {
            EntityType.PERSON: [
                r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\b',
            ],
            EntityType.ORGANIZATION: [
                r'\b([A-Z][A-Za-z]+\s+(?:Inc\.|Corp\.|Ltd\.|LLC|A\.Ş\.|Şti\.))\b',
                r'\b([A-Z][A-Z]{2,})\b',
            ],
            EntityType.TECHNOLOGY: [
                r'\b(Python|JavaScript|TypeScript|React|Node\.js|Docker|Kubernetes|AWS|Azure|GCP|PostgreSQL|MongoDB|Redis)\b',
            ],
            EntityType.DATE: [
                r'\b(\d{1,2}[./]\d{1,2}[./]\d{2,4})\b',
                r'\b(\d{4}-\d{2}-\d{2})\b',
            ]
        }
        
        seen_names = set()
        
        for entity_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match.strip()
                    if len(name) > 2 and name.lower() not in seen_names:
                        seen_names.add(name.lower())
                        entities.append(Entity(
                            id=str(uuid.uuid4()),
                            name=name,
                            type=entity_type,
                            sources=[document_id] if document_id else [],
                            confidence=0.6
                        ))
        
        extraction_time = (time.time() - start_time) * 1000
        
        return ExtractionResult(
            entities=entities,
            relationships=[],
            document_id=document_id,
            extraction_time_ms=extraction_time,
            confidence=0.6 if entities else 0.0
        )
    
    async def infer_relationships(
        self,
        entity1: Entity,
        entity2: Entity,
        context: str = ""
    ) -> Optional[Relationship]:
        """Use LLM to infer relationship between two entities"""
        llm = self._get_llm()
        if not llm:
            return None
        
        prompt = f"""Bu iki varlık arasındaki ilişkiyi belirle:

Varlık 1: {entity1.name} ({entity1.type.value})
Açıklama 1: {entity1.description}

Varlık 2: {entity2.name} ({entity2.type.value})
Açıklama 2: {entity2.description}

{f'Bağlam: {context}' if context else ''}

İlişki türü seçenekleri: relates_to, is_a, part_of, works_at, knows, created_by, similar_to, depends_on, enables, causes, mentions

JSON yanıtla:
{{"relationship_type": "...", "label": "ilişki açıklaması", "confidence": 0.0-1.0, "bidirectional": true/false}}

Eğer ilişki yoksa null döndür."""

        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm.generate(prompt, max_tokens=200)
            )
            
            if "null" in response.lower():
                return None
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                return Relationship(
                    id=str(uuid.uuid4()),
                    source_id=entity1.id,
                    target_id=entity2.id,
                    type=self._parse_relation_type(data.get("relationship_type", "relates_to")),
                    label=data.get("label", ""),
                    confidence=data.get("confidence", 0.7),
                    bidirectional=data.get("bidirectional", False)
                )
        
        except Exception as e:
            logger.error(f"Relationship inference failed: {e}")
        
        return None


# =============================================================================
# ENTERPRISE KNOWLEDGE GRAPH
# =============================================================================

class EnterpriseKnowledgeGraph:
    """
    Enterprise-grade Knowledge Graph with LLM-powered extraction,
    semantic operations, and graph analytics.
    """
    
    def __init__(self, storage_dir: str = "data/knowledge_graph"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        if HAS_NETWORKX:
            self.graph = nx.DiGraph()
        else:
            self.graph = None
        
        self.extractor = LLMEntityExtractor()
        
        # Indexes for fast lookup
        self._name_index: Dict[str, str] = {}  # name -> entity_id
        self._type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self._source_index: Dict[str, Set[str]] = defaultdict(set)  # source -> entity_ids
        
        # Stats
        self.stats = {
            "total_entities": 0,
            "total_relationships": 0,
            "extractions_count": 0,
            "queries_count": 0
        }
        
        self._load()
        
        logger.info(f"EnterpriseKnowledgeGraph initialized with {len(self.entities)} entities")
    
    def _load(self):
        """Load graph from disk"""
        entities_path = self.storage_dir / "entities.json"
        relationships_path = self.storage_dir / "relationships.json"
        
        if entities_path.exists():
            try:
                with open(entities_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for ent_data in data:
                        entity = Entity.from_dict(ent_data)
                        self.entities[entity.id] = entity
                        self._index_entity(entity)
            except Exception as e:
                logger.error(f"Error loading entities: {e}")
        
        if relationships_path.exists():
            try:
                with open(relationships_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for rel_data in data:
                        relationship = Relationship.from_dict(rel_data)
                        self.relationships[relationship.id] = relationship
            except Exception as e:
                logger.error(f"Error loading relationships: {e}")
        
        self._rebuild_graph()
        self.stats["total_entities"] = len(self.entities)
        self.stats["total_relationships"] = len(self.relationships)
    
    def _save(self):
        """Save graph to disk"""
        entities_path = self.storage_dir / "entities.json"
        relationships_path = self.storage_dir / "relationships.json"
        
        with open(entities_path, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in self.entities.values()], f, ensure_ascii=False, indent=2)
        
        with open(relationships_path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in self.relationships.values()], f, ensure_ascii=False, indent=2)
    
    def _index_entity(self, entity: Entity):
        """Add entity to indexes"""
        self._name_index[entity.name.lower()] = entity.id
        for alias in entity.aliases:
            self._name_index[alias.lower()] = entity.id
        self._type_index[entity.type].add(entity.id)
        for source in entity.sources:
            self._source_index[source].add(entity.id)
    
    def _rebuild_graph(self):
        """Rebuild NetworkX graph from entities and relationships"""
        if not HAS_NETWORKX:
            return
        
        self.graph = nx.DiGraph()
        
        # Add nodes
        for entity in self.entities.values():
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.type.value,
                importance=entity.importance.value
            )
        
        # Add edges
        for rel in self.relationships.values():
            if rel.source_id in self.entities and rel.target_id in self.entities:
                self.graph.add_edge(
                    rel.source_id,
                    rel.target_id,
                    id=rel.id,
                    type=rel.type.value,
                    weight=rel.weight
                )
                
                if rel.bidirectional:
                    self.graph.add_edge(
                        rel.target_id,
                        rel.source_id,
                        id=f"{rel.id}_reverse",
                        type=rel.type.value,
                        weight=rel.weight
                    )
        
        # Compute metrics
        self._compute_graph_metrics()
    
    def _compute_graph_metrics(self):
        """Compute graph-level metrics for entities"""
        if not HAS_NETWORKX or not self.graph.nodes():
            return
        
        try:
            # Centrality
            centrality = nx.degree_centrality(self.graph)
            for entity_id, cent_value in centrality.items():
                if entity_id in self.entities:
                    self.entities[entity_id].centrality = cent_value
            
            # Community detection (for undirected version)
            undirected = self.graph.to_undirected()
            if undirected.number_of_edges() > 0:
                try:
                    communities = community.greedy_modularity_communities(undirected)
                    for i, comm in enumerate(communities):
                        for entity_id in comm:
                            if entity_id in self.entities:
                                self.entities[entity_id].community_id = i
                except:
                    pass
        
        except Exception as e:
            logger.warning(f"Error computing graph metrics: {e}")
    
    # =========================================================================
    # ENTITY MANAGEMENT
    # =========================================================================
    
    def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: str = "",
        properties: Dict[str, Any] = None,
        aliases: List[str] = None,
        source: str = ""
    ) -> Entity:
        """Add a new entity or update existing"""
        # Check if entity already exists
        existing_id = self._name_index.get(name.lower())
        if existing_id and existing_id in self.entities:
            # Update existing
            entity = self.entities[existing_id]
            entity.mentions_count += 1
            entity.last_seen = datetime.now()
            if source and source not in entity.sources:
                entity.sources.append(source)
            if description and not entity.description:
                entity.description = description
            if properties:
                entity.properties.update(properties)
            if aliases:
                for alias in aliases:
                    if alias not in entity.aliases:
                        entity.aliases.append(alias)
                        self._name_index[alias.lower()] = entity.id
            
            self._save()
            return entity
        
        # Create new entity
        entity = Entity(
            id=str(uuid.uuid4()),
            name=name,
            type=entity_type,
            description=description,
            properties=properties or {},
            aliases=aliases or [],
            sources=[source] if source else []
        )
        
        self.entities[entity.id] = entity
        self._index_entity(entity)
        
        # Add to graph
        if HAS_NETWORKX:
            self.graph.add_node(
                entity.id,
                name=entity.name,
                type=entity_type.value,
                importance=entity.importance.value
            )
        
        self.stats["total_entities"] = len(self.entities)
        self._save()
        
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID"""
        return self.entities.get(entity_id)
    
    def find_entity(self, name: str) -> Optional[Entity]:
        """Find an entity by name or alias"""
        entity_id = self._name_index.get(name.lower())
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> Optional[Entity]:
        """Update an entity"""
        entity = self.entities.get(entity_id)
        if not entity:
            return None
        
        for key, value in updates.items():
            if key == "type" and isinstance(value, str):
                value = EntityType(value)
            if key == "importance" and isinstance(value, str):
                value = ImportanceLevel(value)
            if hasattr(entity, key):
                setattr(entity, key, value)
        
        self._save()
        return entity
    
    def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and its relationships"""
        if entity_id not in self.entities:
            return False
        
        entity = self.entities[entity_id]
        
        # Remove from indexes
        if entity.name.lower() in self._name_index:
            del self._name_index[entity.name.lower()]
        for alias in entity.aliases:
            if alias.lower() in self._name_index:
                del self._name_index[alias.lower()]
        self._type_index[entity.type].discard(entity_id)
        
        # Remove relationships
        to_remove = [
            rel_id for rel_id, rel in self.relationships.items()
            if rel.source_id == entity_id or rel.target_id == entity_id
        ]
        for rel_id in to_remove:
            del self.relationships[rel_id]
        
        # Remove from graph
        if HAS_NETWORKX and entity_id in self.graph:
            self.graph.remove_node(entity_id)
        
        del self.entities[entity_id]
        self.stats["total_entities"] = len(self.entities)
        self._save()
        
        return True
    
    def list_entities(
        self,
        entity_type: Optional[EntityType] = None,
        source: Optional[str] = None,
        min_mentions: int = 1,
        limit: int = 100
    ) -> List[Entity]:
        """List entities with optional filtering"""
        entities = list(self.entities.values())
        
        if entity_type:
            entity_ids = self._type_index.get(entity_type, set())
            entities = [e for e in entities if e.id in entity_ids]
        
        if source:
            source_ids = self._source_index.get(source, set())
            entities = [e for e in entities if e.id in source_ids]
        
        entities = [e for e in entities if e.mentions_count >= min_mentions]
        
        # Sort by centrality/importance
        entities.sort(key=lambda e: (e.centrality, e.mentions_count), reverse=True)
        
        return entities[:limit]
    
    # =========================================================================
    # RELATIONSHIP MANAGEMENT
    # =========================================================================
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        label: str = "",
        weight: float = 1.0,
        bidirectional: bool = False,
        source: str = ""
    ) -> Optional[Relationship]:
        """Add a relationship between entities"""
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        # Check if relationship already exists
        for rel in self.relationships.values():
            if rel.source_id == source_id and rel.target_id == target_id and rel.type == relation_type:
                rel.mentions_count += 1
                rel.last_seen = datetime.now()
                rel.weight = min(rel.weight + 0.1, 5.0)  # Increase weight
                if source and source not in rel.sources:
                    rel.sources.append(source)
                self._save()
                return rel
        
        # Create new relationship
        relationship = Relationship(
            id=str(uuid.uuid4()),
            source_id=source_id,
            target_id=target_id,
            type=relation_type,
            label=label,
            weight=weight,
            bidirectional=bidirectional,
            sources=[source] if source else []
        )
        
        self.relationships[relationship.id] = relationship
        
        # Add to graph
        if HAS_NETWORKX:
            self.graph.add_edge(
                source_id,
                target_id,
                id=relationship.id,
                type=relation_type.value,
                weight=weight
            )
            if bidirectional:
                self.graph.add_edge(
                    target_id,
                    source_id,
                    id=f"{relationship.id}_reverse",
                    type=relation_type.value,
                    weight=weight
                )
        
        self.stats["total_relationships"] = len(self.relationships)
        self._save()
        
        return relationship
    
    def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",  # outgoing, incoming, both
        relation_type: Optional[RelationType] = None
    ) -> List[Relationship]:
        """Get relationships for an entity"""
        relationships = []
        
        for rel in self.relationships.values():
            if direction in ["outgoing", "both"] and rel.source_id == entity_id:
                if not relation_type or rel.type == relation_type:
                    relationships.append(rel)
            
            if direction in ["incoming", "both"] and rel.target_id == entity_id:
                if not relation_type or rel.type == relation_type:
                    relationships.append(rel)
        
        return relationships
    
    def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship"""
        if relationship_id not in self.relationships:
            return False
        
        rel = self.relationships[relationship_id]
        
        # Remove from graph
        if HAS_NETWORKX:
            if self.graph.has_edge(rel.source_id, rel.target_id):
                self.graph.remove_edge(rel.source_id, rel.target_id)
        
        del self.relationships[relationship_id]
        self.stats["total_relationships"] = len(self.relationships)
        self._save()
        
        return True
    
    # =========================================================================
    # EXTRACTION
    # =========================================================================
    
    async def extract_from_text(
        self,
        text: str,
        document_id: str = "",
        auto_link: bool = True
    ) -> ExtractionResult:
        """Extract entities and relationships from text"""
        # Get existing entities for context
        existing = list(self.entities.values())[:50]
        
        # Extract using LLM
        result = await self.extractor.extract_entities(text, document_id, existing)
        
        # Add extracted entities to graph
        added_entities = []
        for entity in result.entities:
            # Check for existing entity with same name
            existing_id = self._name_index.get(entity.name.lower())
            if existing_id:
                # Update existing
                existing_entity = self.entities[existing_id]
                existing_entity.mentions_count += 1
                existing_entity.last_seen = datetime.now()
                if document_id and document_id not in existing_entity.sources:
                    existing_entity.sources.append(document_id)
                added_entities.append(existing_entity)
            else:
                # Add new
                self.entities[entity.id] = entity
                self._index_entity(entity)
                added_entities.append(entity)
                
                if HAS_NETWORKX:
                    self.graph.add_node(
                        entity.id,
                        name=entity.name,
                        type=entity.type.value
                    )
        
        # Add extracted relationships
        for rel in result.relationships:
            # Map names to IDs
            source_id = self._name_index.get(rel.source_id.lower()) if rel.source_id else None
            target_id = self._name_index.get(rel.target_id.lower()) if rel.target_id else None
            
            if source_id and target_id:
                self.add_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=rel.type,
                    label=rel.label,
                    source=document_id
                )
        
        # Auto-link: find semantic relationships between new and existing entities
        if auto_link and len(added_entities) > 0:
            await self._auto_link_entities(added_entities)
        
        self.stats["extractions_count"] += 1
        self._save()
        
        result.entities = added_entities
        return result
    
    async def _auto_link_entities(self, new_entities: List[Entity]):
        """Automatically find and create relationships between entities"""
        # Get entities with embeddings
        entities_with_embeddings = [
            e for e in self.entities.values()
            if e.embedding and e.id not in [ne.id for ne in new_entities]
        ]
        
        if not entities_with_embeddings:
            return
        
        for new_entity in new_entities:
            if not new_entity.embedding:
                continue
            
            # Find similar entities
            similarities = []
            for existing in entities_with_embeddings:
                sim = self._cosine_similarity(new_entity.embedding, existing.embedding)
                if sim > 0.7:  # High similarity threshold
                    similarities.append((existing, sim))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Create relationships for top similar entities
            for existing, sim in similarities[:3]:
                # Check if relationship already exists
                existing_rel = any(
                    (r.source_id == new_entity.id and r.target_id == existing.id) or
                    (r.source_id == existing.id and r.target_id == new_entity.id)
                    for r in self.relationships.values()
                )
                
                if not existing_rel:
                    self.add_relationship(
                        source_id=new_entity.id,
                        target_id=existing.id,
                        relation_type=RelationType.SIMILAR_TO,
                        label=f"Semantik benzerlik: {sim:.2f}",
                        weight=sim,
                        bidirectional=True
                    )
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    
    # =========================================================================
    # QUERYING
    # =========================================================================
    
    async def query(self, query: GraphQuery) -> GraphQueryResult:
        """Query the knowledge graph"""
        import time
        start_time = time.time()
        
        self.stats["queries_count"] += 1
        
        entities = []
        relationships = []
        paths = []
        
        # Find relevant entities
        query_lower = query.query_text.lower()
        
        for entity in self.entities.values():
            relevance = 0.0
            
            # Name matching
            if query_lower in entity.name.lower():
                relevance += 0.5
            
            # Description matching
            if entity.description and query_lower in entity.description.lower():
                relevance += 0.3
            
            # Alias matching
            for alias in entity.aliases:
                if query_lower in alias.lower():
                    relevance += 0.2
                    break
            
            # Type filter
            if query.entity_types and entity.type not in query.entity_types:
                continue
            
            # Confidence filter
            if entity.confidence < query.min_confidence:
                continue
            
            if relevance > 0:
                entities.append(entity)
        
        # Sort by relevance and limit
        entities = entities[:query.limit]
        
        # Get relationships for found entities
        entity_ids = {e.id for e in entities}
        
        for rel in self.relationships.values():
            if rel.source_id in entity_ids or rel.target_id in entity_ids:
                if query.relationship_types and rel.type not in query.relationship_types:
                    continue
                if rel.confidence >= query.min_confidence:
                    relationships.append(rel)
        
        # Find paths if requested
        if query.include_paths and len(entities) >= 2 and HAS_NETWORKX:
            paths = self._find_paths(entities[:5], query.max_hops)
        
        # Generate context for RAG
        context = self._generate_context(entities, relationships)
        
        # Build subgraph for visualization
        subgraph = self._build_subgraph(entities, relationships)
        
        query_time = (time.time() - start_time) * 1000
        
        return GraphQueryResult(
            entities=entities,
            relationships=relationships,
            paths=paths,
            subgraph=subgraph,
            context=context,
            relevance_score=len(entities) / max(1, query.limit),
            query_time_ms=query_time
        )
    
    def _find_paths(self, entities: List[Entity], max_hops: int) -> List[GraphPath]:
        """Find paths between entities"""
        if not HAS_NETWORKX or len(entities) < 2:
            return []
        
        paths = []
        
        for i, source in enumerate(entities):
            for target in entities[i+1:]:
                try:
                    # Find shortest paths
                    for path in nx.all_shortest_paths(
                        self.graph.to_undirected(),
                        source.id,
                        target.id
                    ):
                        if len(path) <= max_hops + 1:
                            # Get edges for this path
                            edge_ids = []
                            for j in range(len(path) - 1):
                                for rel in self.relationships.values():
                                    if ((rel.source_id == path[j] and rel.target_id == path[j+1]) or
                                        (rel.source_id == path[j+1] and rel.target_id == path[j])):
                                        edge_ids.append(rel.id)
                                        break
                            
                            paths.append(GraphPath(
                                nodes=path,
                                edges=edge_ids,
                                total_weight=len(path) - 1,
                                confidence=0.8
                            ))
                            break  # Only first path between each pair
                except nx.NetworkXNoPath:
                    continue
        
        return paths[:10]  # Limit paths
    
    def _generate_context(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> str:
        """Generate context string for RAG"""
        context_parts = []
        
        # Entity descriptions
        for entity in entities[:10]:
            desc = f"- {entity.name}"
            if entity.type != EntityType.CONCEPT:
                desc += f" ({entity.type.value})"
            if entity.description:
                desc += f": {entity.description}"
            context_parts.append(desc)
        
        # Relationship descriptions
        if relationships:
            context_parts.append("\nİlişkiler:")
            for rel in relationships[:10]:
                source = self.entities.get(rel.source_id)
                target = self.entities.get(rel.target_id)
                if source and target:
                    context_parts.append(
                        f"- {source.name} → {rel.type.value} → {target.name}"
                    )
        
        return "\n".join(context_parts)
    
    def _build_subgraph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """Build subgraph data for visualization (D3.js/Cytoscape compatible)"""
        nodes = []
        links = []
        
        entity_ids = {e.id for e in entities}
        
        for entity in entities:
            nodes.append({
                "id": entity.id,
                "label": entity.name,
                "type": entity.type.value,
                "importance": entity.importance.value,
                "centrality": entity.centrality,
                "community": entity.community_id
            })
        
        for rel in relationships:
            if rel.source_id in entity_ids and rel.target_id in entity_ids:
                links.append({
                    "id": rel.id,
                    "source": rel.source_id,
                    "target": rel.target_id,
                    "type": rel.type.value,
                    "label": rel.label or rel.type.value,
                    "weight": rel.weight
                })
        
        return {"nodes": nodes, "links": links}
    
    # =========================================================================
    # GRAPH-ENHANCED RAG
    # =========================================================================
    
    async def enhance_rag_query(self, query: str) -> Dict[str, Any]:
        """
        Enhance a RAG query with knowledge graph context.
        Returns additional context and entities to improve retrieval.
        """
        # Find relevant entities
        graph_result = await self.query(GraphQuery(
            query_text=query,
            max_hops=2,
            limit=10
        ))
        
        # Expand with related entities
        expanded_entities = set()
        for entity in graph_result.entities:
            expanded_entities.add(entity.name)
            for alias in entity.aliases:
                expanded_entities.add(alias)
            
            # Get related entities
            for rel in self.get_relationships(entity.id):
                if rel.source_id != entity.id:
                    related = self.entities.get(rel.source_id)
                else:
                    related = self.entities.get(rel.target_id)
                if related:
                    expanded_entities.add(related.name)
        
        return {
            "original_query": query,
            "expanded_terms": list(expanded_entities),
            "context": graph_result.context,
            "entities": [e.to_dict() for e in graph_result.entities],
            "subgraph": graph_result.subgraph
        }
    
    # =========================================================================
    # KNOWLEDGE GAP DETECTION
    # =========================================================================
    
    def detect_knowledge_gaps(self) -> List[KnowledgeGap]:
        """Detect gaps in the knowledge graph"""
        gaps = []
        
        for entity in self.entities.values():
            # Low confidence entities
            if entity.confidence < 0.6:
                gaps.append(KnowledgeGap(
                    entity_id=entity.id,
                    entity_name=entity.name,
                    gap_type="low_confidence",
                    description=f"Varlık düşük güvenilirlikte ({entity.confidence:.2f})",
                    severity="medium",
                    suggestions=["Bu varlığı doğrulayın veya daha fazla bağlam ekleyin"]
                ))
            
            # Missing description
            if not entity.description and entity.type != EntityType.DATE:
                gaps.append(KnowledgeGap(
                    entity_id=entity.id,
                    entity_name=entity.name,
                    gap_type="missing_description",
                    description="Varlık açıklaması eksik",
                    severity="low",
                    suggestions=["Bu varlık için bir açıklama ekleyin"]
                ))
            
            # Isolated entities (no connections)
            rels = self.get_relationships(entity.id)
            if len(rels) == 0 and len(self.entities) > 1:
                gaps.append(KnowledgeGap(
                    entity_id=entity.id,
                    entity_name=entity.name,
                    gap_type="no_connections",
                    description="Varlık hiçbir şeye bağlı değil",
                    severity="high",
                    suggestions=[
                        "Bu varlığı diğer varlıklarla ilişkilendirin",
                        "Otomatik bağlantı için yeni metin ekleyin"
                    ]
                ))
        
        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda g: severity_order.get(g.severity, 99))
        
        return gaps
    
    # =========================================================================
    # ANALYTICS
    # =========================================================================
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        stats = {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": {},
            "relationship_types": {},
            "avg_connections_per_entity": 0,
            "most_connected_entities": [],
            "communities_count": 0,
            "density": 0,
            "avg_path_length": 0
        }
        
        # Entity type distribution
        for entity_type, ids in self._type_index.items():
            stats["entity_types"][entity_type.value] = len(ids)
        
        # Relationship type distribution
        rel_types = defaultdict(int)
        for rel in self.relationships.values():
            rel_types[rel.type.value] += 1
        stats["relationship_types"] = dict(rel_types)
        
        # Average connections
        if self.entities:
            total_connections = sum(
                len(self.get_relationships(e.id))
                for e in self.entities.values()
            )
            stats["avg_connections_per_entity"] = total_connections / len(self.entities)
        
        # Most connected entities
        sorted_entities = sorted(
            self.entities.values(),
            key=lambda e: e.centrality,
            reverse=True
        )
        stats["most_connected_entities"] = [
            {"name": e.name, "type": e.type.value, "centrality": e.centrality}
            for e in sorted_entities[:10]
        ]
        
        # Graph metrics from NetworkX
        if HAS_NETWORKX and self.graph.number_of_nodes() > 0:
            stats["density"] = nx.density(self.graph)
            
            # Communities
            communities = set(e.community_id for e in self.entities.values() if e.community_id is not None)
            stats["communities_count"] = len(communities)
            
            # Average path length (sample-based for performance)
            try:
                if nx.is_connected(self.graph.to_undirected()):
                    stats["avg_path_length"] = nx.average_shortest_path_length(self.graph.to_undirected())
            except:
                pass
        
        return stats
    
    # =========================================================================
    # EXPORT/IMPORT
    # =========================================================================
    
    def export_graph(self, format: str = "json") -> Union[Dict[str, Any], str]:
        """Export the graph in various formats"""
        if format == "json":
            return {
                "entities": [e.to_dict() for e in self.entities.values()],
                "relationships": [r.to_dict() for r in self.relationships.values()],
                "stats": self.get_graph_stats(),
                "exported_at": datetime.now().isoformat()
            }
        
        elif format == "cytoscape":
            # Cytoscape.js compatible format
            elements = []
            
            for entity in self.entities.values():
                elements.append({
                    "group": "nodes",
                    "data": {
                        "id": entity.id,
                        "label": entity.name,
                        "type": entity.type.value,
                        **entity.properties
                    }
                })
            
            for rel in self.relationships.values():
                elements.append({
                    "group": "edges",
                    "data": {
                        "id": rel.id,
                        "source": rel.source_id,
                        "target": rel.target_id,
                        "label": rel.label or rel.type.value,
                        "type": rel.type.value
                    }
                })
            
            return {"elements": elements}
        
        elif format == "d3":
            # D3.js force-directed compatible format
            return self._build_subgraph(
                list(self.entities.values()),
                list(self.relationships.values())
            )
        
        elif format == "graphml" and HAS_NETWORKX:
            # GraphML format
            import io
            output = io.BytesIO()
            nx.write_graphml(self.graph, output)
            return output.getvalue().decode('utf-8')
        
        else:
            return self.export_graph("json")
    
    def import_graph(self, data: Dict[str, Any]) -> int:
        """Import entities and relationships from export data"""
        imported_count = 0
        
        for ent_data in data.get("entities", []):
            entity = Entity.from_dict(ent_data)
            if entity.id not in self.entities:
                self.entities[entity.id] = entity
                self._index_entity(entity)
                imported_count += 1
        
        for rel_data in data.get("relationships", []):
            rel = Relationship.from_dict(rel_data)
            if rel.id not in self.relationships:
                if rel.source_id in self.entities and rel.target_id in self.entities:
                    self.relationships[rel.id] = rel
                    imported_count += 1
        
        self._rebuild_graph()
        self._save()
        
        return imported_count
    
    def clear(self):
        """Clear all data from the graph"""
        self.entities.clear()
        self.relationships.clear()
        self._name_index.clear()
        self._type_index.clear()
        self._source_index.clear()
        
        if HAS_NETWORKX:
            self.graph = nx.DiGraph()
        
        self.stats = {
            "total_entities": 0,
            "total_relationships": 0,
            "extractions_count": 0,
            "queries_count": 0
        }
        
        self._save()


# =============================================================================
# SINGLETON
# =============================================================================

enterprise_knowledge_graph = EnterpriseKnowledgeGraph()
