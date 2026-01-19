"""
Advanced Graph RAG System
=========================

Knowledge Graph enhanced Retrieval-Augmented Generation.

Features:
- Entity Extraction & Linking
- Relationship Detection
- Multi-hop Graph Traversal
- Community Detection
- Path-based Reasoning
- Graph-Vector Hybrid Search
- Subgraph Summarization
- Knowledge Graph Construction

Enterprise-grade implementation with Neo4j/NetworkX support.

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    Union,
)

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

from core.logger import get_logger

logger = get_logger("rag.graph_rag")


# =============================================================================
# ENUMS
# =============================================================================

class EntityType(Enum):
    """Entity türleri."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    CONCEPT = "concept"
    PRODUCT = "product"
    EVENT = "event"
    DOCUMENT = "document"
    CHUNK = "chunk"
    TOPIC = "topic"
    UNKNOWN = "unknown"


class RelationType(Enum):
    """İlişki türleri."""
    # Semantic relations
    IS_A = "is_a"
    PART_OF = "part_of"
    HAS_PROPERTY = "has_property"
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"
    
    # Document relations
    MENTIONS = "mentions"
    CONTAINS = "contains"
    REFERENCES = "references"
    FOLLOWS = "follows"
    PRECEDES = "precedes"
    
    # Entity relations
    WORKS_FOR = "works_for"
    LOCATED_IN = "located_in"
    CREATED_BY = "created_by"
    OWNS = "owns"
    PARTICIPATES_IN = "participates_in"
    
    # Temporal relations
    HAPPENED_BEFORE = "happened_before"
    HAPPENED_AFTER = "happened_after"
    CONCURRENT_WITH = "concurrent_with"


class TraversalStrategy(Enum):
    """Graph traversal stratejileri."""
    BFS = "bfs"                     # Breadth-first
    DFS = "dfs"                     # Depth-first
    WEIGHTED = "weighted"           # Edge weight based
    PAGERANK = "pagerank"           # PageRank based
    COMMUNITY = "community"         # Community-aware


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Entity:
    """Graf entity'si."""
    id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Graph metadata
    degree: int = 0
    centrality: float = 0.0
    community_id: Optional[str] = None
    
    # Source tracking
    source_documents: List[str] = field(default_factory=list)
    mention_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.entity_type.value,
            "properties": self.properties,
            "degree": self.degree,
            "centrality": self.centrality,
            "community_id": self.community_id,
            "mention_count": self.mention_count,
        }
    
    @classmethod
    def from_text(cls, text: str, entity_type: EntityType = EntityType.UNKNOWN) -> "Entity":
        """Metinden entity oluştur."""
        entity_id = hashlib.md5(f"{text}_{entity_type.value}".encode()).hexdigest()[:12]
        return cls(
            id=entity_id,
            name=text,
            entity_type=entity_type,
        )


@dataclass
class Relationship:
    """Graf ilişkisi."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # Provenance
    source_document: Optional[str] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "weight": self.weight,
            "confidence": self.confidence,
        }


@dataclass
class GraphPath:
    """Graf yolu."""
    nodes: List[Entity]
    edges: List[Relationship]
    total_weight: float = 0.0
    
    def to_text(self) -> str:
        """Yolu metne dönüştür."""
        if not self.nodes:
            return ""
        
        parts = []
        for i, node in enumerate(self.nodes):
            parts.append(node.name)
            if i < len(self.edges):
                parts.append(f" --[{self.edges[i].relation_type.value}]--> ")
        
        return "".join(parts)
    
    def __len__(self) -> int:
        return len(self.nodes)


@dataclass
class GraphContext:
    """Graph-based context."""
    entities: List[Entity]
    relationships: List[Relationship]
    paths: List[GraphPath]
    subgraph_text: str
    
    # Metadata
    community_summaries: Dict[str, str] = field(default_factory=dict)
    central_entities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "paths": [p.to_text() for p in self.paths],
            "subgraph_text": self.subgraph_text[:500],
            "community_summaries": self.community_summaries,
            "central_entities": self.central_entities,
        }


@dataclass
class GraphRAGResult:
    """Graph RAG sonucu."""
    query: str
    response: str
    confidence: float
    
    # Graph context
    graph_context: GraphContext
    entities_found: List[Entity]
    reasoning_path: List[GraphPath]
    
    # Vector context (hybrid)
    vector_context: List[Any]
    
    # Metrics
    graph_hops: int = 0
    entities_traversed: int = 0
    total_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "response": self.response,
            "confidence": self.confidence,
            "graph_context": self.graph_context.to_dict(),
            "entities_found": [e.to_dict() for e in self.entities_found],
            "reasoning_path": [p.to_text() for p in self.reasoning_path],
            "graph_hops": self.graph_hops,
            "entities_traversed": self.entities_traversed,
            "total_time_ms": self.total_time_ms,
        }


# =============================================================================
# PROTOCOLS
# =============================================================================

class LLMProtocol(Protocol):
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class EmbeddingProtocol(Protocol):
    def embed_text(self, text: str) -> List[float]:
        ...


class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> Any:
        ...


# =============================================================================
# KNOWLEDGE GRAPH
# =============================================================================

class KnowledgeGraph:
    """
    In-memory Knowledge Graph.
    
    NetworkX-based graph implementation with:
    - Entity & Relationship management
    - Multi-hop traversal
    - Community detection
    - Centrality analysis
    - Subgraph extraction
    """
    
    def __init__(self):
        if not HAS_NETWORKX:
            logger.warning("NetworkX not installed. Using fallback implementation.")
            self._graph = None
            self._entities: Dict[str, Entity] = {}
            self._relationships: Dict[str, Relationship] = {}
            self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        else:
            self._graph = nx.DiGraph()
        
        self._entity_index: Dict[str, Entity] = {}
        self._name_to_id: Dict[str, str] = {}
        self._type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self._document_entities: Dict[str, Set[str]] = defaultdict(set)
    
    # =========================================================================
    # ENTITY MANAGEMENT
    # =========================================================================
    
    def add_entity(self, entity: Entity) -> str:
        """Entity ekle."""
        self._entity_index[entity.id] = entity
        self._name_to_id[entity.name.lower()] = entity.id
        self._type_index[entity.entity_type].add(entity.id)
        
        if HAS_NETWORKX and self._graph is not None:
            self._graph.add_node(
                entity.id,
                name=entity.name,
                type=entity.entity_type.value,
                properties=entity.properties,
            )
        else:
            self._entities[entity.id] = entity
        
        return entity.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Entity getir."""
        return self._entity_index.get(entity_id)
    
    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """İsme göre entity bul."""
        entity_id = self._name_to_id.get(name.lower())
        if entity_id:
            return self._entity_index.get(entity_id)
        return None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Türe göre entity'leri getir."""
        entity_ids = self._type_index.get(entity_type, set())
        return [self._entity_index[eid] for eid in entity_ids if eid in self._entity_index]
    
    # =========================================================================
    # RELATIONSHIP MANAGEMENT
    # =========================================================================
    
    def add_relationship(self, relationship: Relationship) -> str:
        """İlişki ekle."""
        if HAS_NETWORKX and self._graph is not None:
            self._graph.add_edge(
                relationship.source_id,
                relationship.target_id,
                id=relationship.id,
                type=relationship.relation_type.value,
                weight=relationship.weight,
                confidence=relationship.confidence,
            )
        else:
            self._relationships[relationship.id] = relationship
            self._adjacency[relationship.source_id].add(relationship.target_id)
        
        # Update entity degrees
        source_entity = self._entity_index.get(relationship.source_id)
        target_entity = self._entity_index.get(relationship.target_id)
        
        if source_entity:
            source_entity.degree += 1
        if target_entity:
            target_entity.degree += 1
        
        return relationship.id
    
    def get_relationships(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> List[Relationship]:
        """Entity'nin ilişkilerini getir."""
        relationships = []
        
        if HAS_NETWORKX and self._graph is not None:
            if direction in ["out", "both"]:
                for _, target, data in self._graph.out_edges(entity_id, data=True):
                    relationships.append(Relationship(
                        id=data.get("id", ""),
                        source_id=entity_id,
                        target_id=target,
                        relation_type=RelationType(data.get("type", "related_to")),
                        weight=data.get("weight", 1.0),
                        confidence=data.get("confidence", 1.0),
                    ))
            
            if direction in ["in", "both"]:
                for source, _, data in self._graph.in_edges(entity_id, data=True):
                    relationships.append(Relationship(
                        id=data.get("id", ""),
                        source_id=source,
                        target_id=entity_id,
                        relation_type=RelationType(data.get("type", "related_to")),
                        weight=data.get("weight", 1.0),
                        confidence=data.get("confidence", 1.0),
                    ))
        else:
            for rel in self._relationships.values():
                if direction in ["out", "both"] and rel.source_id == entity_id:
                    relationships.append(rel)
                if direction in ["in", "both"] and rel.target_id == entity_id:
                    relationships.append(rel)
        
        return relationships
    
    # =========================================================================
    # GRAPH TRAVERSAL
    # =========================================================================
    
    def get_neighbors(
        self,
        entity_id: str,
        max_depth: int = 1,
        relation_types: List[RelationType] = None
    ) -> List[Entity]:
        """Komşu entity'leri getir."""
        if max_depth < 1:
            return []
        
        visited = set()
        neighbors = []
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, depth = queue.pop(0)
            
            if current_id in visited:
                continue
            visited.add(current_id)
            
            if current_id != entity_id:
                entity = self._entity_index.get(current_id)
                if entity:
                    neighbors.append(entity)
            
            if depth < max_depth:
                relationships = self.get_relationships(current_id, "both")
                
                for rel in relationships:
                    if relation_types and rel.relation_type not in relation_types:
                        continue
                    
                    next_id = rel.target_id if rel.source_id == current_id else rel.source_id
                    if next_id not in visited:
                        queue.append((next_id, depth + 1))
        
        return neighbors
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[GraphPath]:
        """İki entity arasında yol bul."""
        if HAS_NETWORKX and self._graph is not None:
            try:
                path_ids = nx.shortest_path(self._graph, source_id, target_id)
                
                nodes = [self._entity_index[nid] for nid in path_ids if nid in self._entity_index]
                edges = []
                
                for i in range(len(path_ids) - 1):
                    edge_data = self._graph.get_edge_data(path_ids[i], path_ids[i+1])
                    if edge_data:
                        edges.append(Relationship(
                            id=edge_data.get("id", ""),
                            source_id=path_ids[i],
                            target_id=path_ids[i+1],
                            relation_type=RelationType(edge_data.get("type", "related_to")),
                            weight=edge_data.get("weight", 1.0),
                        ))
                
                return GraphPath(nodes=nodes, edges=edges)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return None
        else:
            # Simple BFS fallback
            visited = set()
            queue = [(source_id, [source_id], [])]
            
            while queue:
                current_id, path, edges = queue.pop(0)
                
                if current_id == target_id:
                    nodes = [self._entity_index[nid] for nid in path if nid in self._entity_index]
                    return GraphPath(nodes=nodes, edges=edges)
                
                if len(path) > max_depth:
                    continue
                
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                for next_id in self._adjacency.get(current_id, []):
                    if next_id not in visited:
                        # Find edge
                        edge = None
                        for rel in self._relationships.values():
                            if rel.source_id == current_id and rel.target_id == next_id:
                                edge = rel
                                break
                        
                        new_edges = edges + [edge] if edge else edges
                        queue.append((next_id, path + [next_id], new_edges))
            
            return None
    
    def find_paths_through_entity(
        self,
        query_entities: List[str],
        max_paths: int = 5,
        max_depth: int = 3
    ) -> List[GraphPath]:
        """Sorgudaki entity'ler arasındaki yolları bul."""
        paths = []
        
        if len(query_entities) < 2:
            return paths
        
        for i in range(len(query_entities)):
            for j in range(i + 1, len(query_entities)):
                path = self.find_path(query_entities[i], query_entities[j], max_depth)
                if path:
                    paths.append(path)
                    if len(paths) >= max_paths:
                        return paths
        
        return paths
    
    # =========================================================================
    # GRAPH ANALYSIS
    # =========================================================================
    
    def calculate_centrality(self) -> Dict[str, float]:
        """PageRank centrality hesapla."""
        if HAS_NETWORKX and self._graph is not None and len(self._graph) > 0:
            try:
                centrality = nx.pagerank(self._graph, alpha=0.85)
                
                for entity_id, score in centrality.items():
                    if entity_id in self._entity_index:
                        self._entity_index[entity_id].centrality = score
                
                return centrality
            except Exception:
                pass
        
        return {}
    
    def detect_communities(self) -> Dict[str, str]:
        """Topluluk tespiti."""
        if HAS_NETWORKX and self._graph is not None:
            try:
                # Convert to undirected for community detection
                undirected = self._graph.to_undirected()
                
                # Simple connected components as communities
                components = nx.connected_components(undirected)
                
                community_map = {}
                for i, component in enumerate(components):
                    community_id = f"community_{i}"
                    for node_id in component:
                        community_map[node_id] = community_id
                        if node_id in self._entity_index:
                            self._entity_index[node_id].community_id = community_id
                
                return community_map
            except Exception:
                pass
        
        return {}
    
    def get_subgraph(
        self,
        entity_ids: List[str],
        max_depth: int = 1
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Belirli entity'ler etrafında subgraph çıkar."""
        all_entity_ids = set(entity_ids)
        
        # Expand with neighbors
        for entity_id in entity_ids:
            neighbors = self.get_neighbors(entity_id, max_depth)
            for neighbor in neighbors:
                all_entity_ids.add(neighbor.id)
        
        # Get entities
        entities = [self._entity_index[eid] for eid in all_entity_ids if eid in self._entity_index]
        
        # Get relationships between these entities
        relationships = []
        seen_rels = set()
        
        for entity_id in all_entity_ids:
            for rel in self.get_relationships(entity_id, "out"):
                if rel.target_id in all_entity_ids and rel.id not in seen_rels:
                    relationships.append(rel)
                    seen_rels.add(rel.id)
        
        return entities, relationships
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Graf istatistikleri."""
        if HAS_NETWORKX and self._graph is not None:
            return {
                "entity_count": self._graph.number_of_nodes(),
                "relationship_count": self._graph.number_of_edges(),
                "entity_types": {t.value: len(ids) for t, ids in self._type_index.items()},
                "avg_degree": sum(d for _, d in self._graph.degree()) / max(self._graph.number_of_nodes(), 1),
            }
        else:
            return {
                "entity_count": len(self._entity_index),
                "relationship_count": len(self._relationships) if hasattr(self, '_relationships') else 0,
                "entity_types": {t.value: len(ids) for t, ids in self._type_index.items()},
            }
    
    def clear(self):
        """Grafi temizle."""
        if HAS_NETWORKX and self._graph is not None:
            self._graph.clear()
        
        self._entity_index.clear()
        self._name_to_id.clear()
        self._type_index.clear()
        self._document_entities.clear()
        
        if hasattr(self, '_entities'):
            self._entities.clear()
        if hasattr(self, '_relationships'):
            self._relationships.clear()
        if hasattr(self, '_adjacency'):
            self._adjacency.clear()


# =============================================================================
# ENTITY EXTRACTOR
# =============================================================================

class EntityExtractor:
    """
    LLM-based entity extraction.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def extract_entities(
        self,
        text: str,
        entity_types: List[EntityType] = None
    ) -> List[Entity]:
        """Metinden entity'leri çıkar."""
        self._lazy_load()
        
        if entity_types is None:
            entity_types = list(EntityType)
        
        type_list = ", ".join(t.value for t in entity_types)
        
        prompt = f"""Extract named entities from the following text.
Return as JSON array with format: [{{"name": "...", "type": "..."}}]
Valid types: {type_list}

Text: {text[:1500]}

Entities (JSON):"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=500)
            
            # Parse JSON
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                entities_data = json.loads(json_match.group())
                
                entities = []
                for item in entities_data:
                    try:
                        entity_type = EntityType(item.get("type", "unknown"))
                    except ValueError:
                        entity_type = EntityType.UNKNOWN
                    
                    entity = Entity.from_text(item["name"], entity_type)
                    entities.append(entity)
                
                return entities
        
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
        # Fallback: simple extraction
        return self._simple_extract(text)
    
    def _simple_extract(self, text: str) -> List[Entity]:
        """Basit entity extraction."""
        entities = []
        
        # Capitalized words (proper nouns)
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2 and i > 0:
                clean_word = word.strip(".,!?:;\"'")
                if clean_word:
                    entity = Entity.from_text(clean_word, EntityType.UNKNOWN)
                    entities.append(entity)
        
        return entities[:20]  # Limit


class RelationshipExtractor:
    """
    LLM-based relationship extraction.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def extract_relationships(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relationship]:
        """Entity'ler arası ilişkileri çıkar."""
        if len(entities) < 2:
            return []
        
        self._lazy_load()
        
        entity_names = [e.name for e in entities[:10]]
        entity_str = ", ".join(entity_names)
        
        relation_types = ", ".join(r.value for r in RelationType)
        
        prompt = f"""Find relationships between these entities in the text.
Return as JSON array: [{{"source": "...", "target": "...", "relation": "..."}}]
Valid relations: {relation_types}

Entities: {entity_str}

Text: {text[:1000]}

Relationships (JSON):"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=400)
            
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                rels_data = json.loads(json_match.group())
                
                # Build entity name -> id map
                name_to_entity = {e.name.lower(): e for e in entities}
                
                relationships = []
                for item in rels_data:
                    source_name = item.get("source", "").lower()
                    target_name = item.get("target", "").lower()
                    
                    source_entity = name_to_entity.get(source_name)
                    target_entity = name_to_entity.get(target_name)
                    
                    if source_entity and target_entity:
                        try:
                            rel_type = RelationType(item.get("relation", "related_to"))
                        except ValueError:
                            rel_type = RelationType.RELATED_TO
                        
                        rel_id = hashlib.md5(
                            f"{source_entity.id}_{target_entity.id}_{rel_type.value}".encode()
                        ).hexdigest()[:12]
                        
                        relationships.append(Relationship(
                            id=rel_id,
                            source_id=source_entity.id,
                            target_id=target_entity.id,
                            relation_type=rel_type,
                        ))
                
                return relationships
        
        except Exception as e:
            logger.warning(f"Relationship extraction failed: {e}")
        
        return []


# =============================================================================
# GRAPH RAG
# =============================================================================

class GraphRAG:
    """
    Graph RAG - Knowledge Graph enhanced RAG.
    
    Vector retrieval ile graph traversal'ı birleştiren
    gelişmiş RAG sistemi.
    
    Example:
        graph_rag = GraphRAG()
        result = graph_rag.query("How is X related to Y?")
    """
    
    def __init__(
        self,
        retriever: Optional[RetrieverProtocol] = None,
        llm: Optional[LLMProtocol] = None,
        embedding_model: Optional[EmbeddingProtocol] = None,
        graph: Optional[KnowledgeGraph] = None,
    ):
        """
        Graph RAG başlat.
        
        Args:
            retriever: Vector retriever
            llm: LLM instance
            embedding_model: Embedding model
            graph: Knowledge graph (varsayılan olarak yeni oluşturulur)
        """
        self._retriever = retriever
        self._llm = llm
        self._embedding = embedding_model
        
        self.graph = graph or KnowledgeGraph()
        self.entity_extractor = EntityExtractor(llm)
        self.relationship_extractor = RelationshipExtractor(llm)
        
        # Config
        self.max_graph_hops = 3
        self.max_entities_per_query = 10
        self.vector_weight = 0.6
        self.graph_weight = 0.4
        
        # Stats
        self._query_count = 0
        self._avg_hops = 0.0
    
    def _lazy_load(self):
        if self._retriever is None:
            from rag.pipeline import rag_pipeline
            self._retriever = rag_pipeline
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def index_document(
        self,
        document_id: str,
        content: str,
        metadata: Dict[str, Any] = None
    ):
        """Dokümanı grafa indexle."""
        # 1. Extract entities
        entities = self.entity_extractor.extract_entities(content)
        
        # 2. Add entities to graph
        entity_ids = []
        for entity in entities:
            entity.source_documents.append(document_id)
            entity.mention_count += 1
            
            # Check if entity already exists
            existing = self.graph.find_entity_by_name(entity.name)
            if existing:
                existing.mention_count += 1
                existing.source_documents.append(document_id)
                entity_ids.append(existing.id)
            else:
                self.graph.add_entity(entity)
                entity_ids.append(entity.id)
        
        # 3. Extract and add relationships
        relationships = self.relationship_extractor.extract_relationships(content, entities)
        
        for rel in relationships:
            rel.source_document = document_id
            self.graph.add_relationship(rel)
        
        # 4. Add document as entity
        doc_entity = Entity(
            id=f"doc_{document_id}",
            name=metadata.get("title", document_id) if metadata else document_id,
            entity_type=EntityType.DOCUMENT,
            properties=metadata or {},
        )
        self.graph.add_entity(doc_entity)
        
        # 5. Link document to entities
        for entity_id in entity_ids:
            rel = Relationship(
                id=f"doc_rel_{document_id}_{entity_id}",
                source_id=doc_entity.id,
                target_id=entity_id,
                relation_type=RelationType.MENTIONS,
            )
            self.graph.add_relationship(rel)
        
        logger.info(f"Indexed document {document_id}: {len(entities)} entities, {len(relationships)} relationships")
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        graph_depth: int = 2,
        use_vector: bool = True,
        use_graph: bool = True,
    ) -> GraphRAGResult:
        """
        Graph RAG sorgusu.
        
        Args:
            query: Kullanıcı sorgusu
            top_k: Döndürülecek sonuç sayısı
            graph_depth: Graph traversal derinliği
            use_vector: Vector search kullan
            use_graph: Graph traversal kullan
            
        Returns:
            GraphRAGResult
        """
        self._lazy_load()
        
        start_time = time.time()
        logger.info(f"Graph RAG query: {query[:50]}...")
        
        # 1. Extract entities from query
        query_entities = self.entity_extractor.extract_entities(query)
        query_entity_ids = []
        
        for qe in query_entities:
            # Find in graph
            existing = self.graph.find_entity_by_name(qe.name)
            if existing:
                query_entity_ids.append(existing.id)
        
        # 2. Vector retrieval
        vector_context = []
        if use_vector:
            try:
                context = self._retriever.retrieve(query=query, top_k=top_k)
                vector_context = context.chunks
            except Exception as e:
                logger.warning(f"Vector retrieval failed: {e}")
        
        # 3. Graph traversal
        graph_entities = []
        graph_relationships = []
        reasoning_paths = []
        
        if use_graph and query_entity_ids:
            # Get subgraph around query entities
            graph_entities, graph_relationships = self.graph.get_subgraph(
                query_entity_ids, 
                max_depth=graph_depth
            )
            
            # Find reasoning paths
            if len(query_entity_ids) >= 2:
                reasoning_paths = self.graph.find_paths_through_entity(
                    query_entity_ids,
                    max_paths=5,
                    max_depth=graph_depth
                )
        
        # 4. Build graph context
        subgraph_text = self._build_subgraph_text(graph_entities, graph_relationships, reasoning_paths)
        
        graph_context = GraphContext(
            entities=graph_entities,
            relationships=graph_relationships,
            paths=reasoning_paths,
            subgraph_text=subgraph_text,
            central_entities=[e.name for e in sorted(graph_entities, key=lambda x: x.centrality, reverse=True)[:5]],
        )
        
        # 5. Generate response
        response, confidence = self._generate_response(
            query, vector_context, graph_context
        )
        
        # 6. Calculate metrics
        graph_hops = max(len(p) for p in reasoning_paths) if reasoning_paths else 0
        entities_traversed = len(graph_entities)
        total_time = int((time.time() - start_time) * 1000)
        
        # Update stats
        self._update_stats(graph_hops)
        
        result = GraphRAGResult(
            query=query,
            response=response,
            confidence=confidence,
            graph_context=graph_context,
            entities_found=[self.graph.get_entity(eid) for eid in query_entity_ids if self.graph.get_entity(eid)],
            reasoning_path=reasoning_paths,
            vector_context=vector_context,
            graph_hops=graph_hops,
            entities_traversed=entities_traversed,
            total_time_ms=total_time,
        )
        
        logger.info(f"Graph RAG completed: {entities_traversed} entities, {graph_hops} hops, {total_time}ms")
        
        return result
    
    async def query_async(
        self,
        query: str,
        top_k: int = 5,
        graph_depth: int = 2,
    ) -> GraphRAGResult:
        """Asenkron Graph RAG sorgusu."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(query, top_k, graph_depth)
        )
    
    def _build_subgraph_text(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        paths: List[GraphPath]
    ) -> str:
        """Subgraph'ı metne dönüştür."""
        parts = []
        
        # Entity descriptions
        if entities:
            parts.append("=== Entities ===")
            for e in entities[:10]:
                parts.append(f"- {e.name} ({e.entity_type.value})")
        
        # Relationships
        if relationships:
            parts.append("\n=== Relationships ===")
            for r in relationships[:10]:
                source = self.graph.get_entity(r.source_id)
                target = self.graph.get_entity(r.target_id)
                if source and target:
                    parts.append(f"- {source.name} --[{r.relation_type.value}]--> {target.name}")
        
        # Paths
        if paths:
            parts.append("\n=== Reasoning Paths ===")
            for p in paths[:3]:
                parts.append(f"- {p.to_text()}")
        
        return "\n".join(parts)
    
    def _generate_response(
        self,
        query: str,
        vector_context: List[Any],
        graph_context: GraphContext
    ) -> Tuple[str, float]:
        """Response üret."""
        # Build combined context
        context_parts = []
        
        # Vector context
        if vector_context:
            context_parts.append("=== Document Sources ===")
            for i, chunk in enumerate(vector_context[:5], 1):
                context_parts.append(f"[Doc {i}]: {chunk.content[:400]}")
        
        # Graph context
        if graph_context.subgraph_text:
            context_parts.append("\n=== Knowledge Graph Context ===")
            context_parts.append(graph_context.subgraph_text)
        
        context = "\n\n".join(context_parts)
        
        if not context.strip():
            return "İlgili bilgi bulunamadı.", 0.3
        
        prompt = f"""Answer the question using both document sources and knowledge graph context.
Reference specific entities and relationships when relevant.

{context}

Question: {query}

Answer:"""
        
        try:
            response = self._llm.generate(prompt, max_tokens=800)
            
            # Calculate confidence based on context richness
            has_vector = len(vector_context) > 0
            has_graph = len(graph_context.entities) > 0
            has_paths = len(graph_context.paths) > 0
            
            confidence = 0.5
            if has_vector:
                confidence += 0.2
            if has_graph:
                confidence += 0.15
            if has_paths:
                confidence += 0.15
            
            return response, min(confidence, 1.0)
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"Error generating response: {str(e)}", 0.0
    
    def _update_stats(self, hops: int):
        """İstatistikleri güncelle."""
        self._query_count += 1
        n = self._query_count
        self._avg_hops = (self._avg_hops * (n - 1) + hops) / n
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        graph_stats = self.graph.get_stats()
        return {
            "query_count": self._query_count,
            "avg_hops": round(self._avg_hops, 2),
            "graph": graph_stats,
        }
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Graph istatistikleri."""
        return self.graph.get_stats()


# =============================================================================
# SINGLETON
# =============================================================================

_graph_rag: Optional[GraphRAG] = None
_knowledge_graph: Optional[KnowledgeGraph] = None


def get_graph_rag() -> GraphRAG:
    """Singleton GraphRAG instance."""
    global _graph_rag, _knowledge_graph
    
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    
    if _graph_rag is None:
        _graph_rag = GraphRAG(graph=_knowledge_graph)
    
    return _graph_rag


def get_knowledge_graph() -> KnowledgeGraph:
    """Singleton KnowledgeGraph instance."""
    global _knowledge_graph
    
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    
    return _knowledge_graph


graph_rag = GraphRAG()
knowledge_graph = KnowledgeGraph()


__all__ = [
    "GraphRAG",
    "KnowledgeGraph",
    "Entity",
    "EntityType",
    "Relationship",
    "RelationType",
    "GraphPath",
    "GraphContext",
    "GraphRAGResult",
    "TraversalStrategy",
    "EntityExtractor",
    "RelationshipExtractor",
    "graph_rag",
    "knowledge_graph",
    "get_graph_rag",
    "get_knowledge_graph",
]
