"""
🕸️ Graph RAG - Neo4j Knowledge Graph Integration
================================================

Knowledge Graph destekli RAG sistemi.

Features:
- Neo4j graph database integration
- Entity extraction and linking
- Relationship detection
- Graph-based retrieval
- Subgraph expansion
- Knowledge graph completion
- Cypher query generation
"""

import asyncio
import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class EntityType(str, Enum):
    """Types of entities in the knowledge graph"""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    CONCEPT = "concept"
    DOCUMENT = "document"
    CHUNK = "chunk"
    TOPIC = "topic"
    DATE = "date"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    UNKNOWN = "unknown"


class RelationType(str, Enum):
    """Types of relationships"""
    MENTIONS = "mentions"
    RELATED_TO = "related_to"
    PART_OF = "part_of"
    LOCATED_IN = "located_in"
    WORKS_FOR = "works_for"
    CREATED_BY = "created_by"
    CONTAINS = "contains"
    CAUSED_BY = "caused_by"
    FOLLOWS = "follows"
    SIMILAR_TO = "similar_to"
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"


# ============ DATA MODELS ============

class Entity(BaseModel):
    """A node in the knowledge graph"""
    id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = Field(default_factory=dict)
    embeddings: Optional[List[float]] = None
    source_chunks: List[str] = Field(default_factory=list)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
    """An edge in the knowledge graph"""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(1.0, ge=0.0)
    source_chunk: Optional[str] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class Triplet(BaseModel):
    """A subject-predicate-object triplet"""
    subject: str
    predicate: str
    object: str
    subject_type: EntityType = EntityType.UNKNOWN
    object_type: EntityType = EntityType.UNKNOWN
    confidence: float = 1.0


class Subgraph(BaseModel):
    """A subgraph containing relevant entities and relationships"""
    entities: List[Entity]
    relationships: List[Relationship]
    center_entity: Optional[str] = None
    depth: int = 1
    context: str = ""


class GraphRAGResult(BaseModel):
    """Result from Graph RAG retrieval"""
    query: str
    subgraph: Subgraph
    text_chunks: List[str]
    graph_context: str
    combined_context: str
    entities_found: List[str]
    relationships_found: int
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============ ENTITY EXTRACTOR ============

class EntityExtractor:
    """
    Extract entities from text using rule-based and LLM approaches.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        
        # Rule-based patterns
        self.patterns = {
            EntityType.PERSON: [
                r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple name pattern
                r'\b(Mr\.|Mrs\.|Ms\.|Dr\.) [A-Z][a-z]+\b',
            ],
            EntityType.ORGANIZATION: [
                r'\b[A-Z][A-Za-z]* (Inc\.|Corp\.|Ltd\.|LLC)\b',
                r'\b(Google|Microsoft|Apple|Amazon|Meta|OpenAI)\b',
            ],
            EntityType.LOCATION: [
                r'\b(New York|London|Paris|Tokyo|Berlin)\b',
                r'\b[A-Z][a-z]+ (City|State|Country)\b',
            ],
            EntityType.DATE: [
                r'\b\d{4}-\d{2}-\d{2}\b',
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}\b',
            ],
            EntityType.TECHNOLOGY: [
                r'\b(Python|JavaScript|React|Node\.js|TensorFlow|PyTorch|LangChain|Neo4j)\b',
                r'\b(API|REST|GraphQL|SQL|NoSQL)\b',
            ],
        }
    
    def extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        seen = set()
        
        # Rule-based extraction
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match if isinstance(match, str) else match[0]
                    if name.lower() not in seen:
                        seen.add(name.lower())
                        entity_id = hashlib.md5(name.encode()).hexdigest()[:12]
                        entities.append(Entity(
                            id=entity_id,
                            name=name,
                            entity_type=entity_type,
                            confidence=0.7
                        ))
        
        return entities
    
    async def extract_entities_llm(self, text: str) -> List[Entity]:
        """Extract entities using LLM (more accurate)"""
        if not self.llm_client:
            return self.extract_entities(text)
        
        prompt = f"""Extract all named entities from the following text.
For each entity, provide:
- name: The entity name
- type: One of [person, organization, location, event, concept, date, technology, product]
- confidence: How confident you are (0-1)

Text: {text[:2000]}

Respond in JSON format:
{{"entities": [{{"name": "...", "type": "...", "confidence": 0.9}}]}}
"""
        
        try:
            response = await self.llm_client.generate(prompt)
            data = json.loads(response)
            
            entities = []
            for e in data.get("entities", []):
                entity_type = EntityType(e.get("type", "unknown"))
                entity_id = hashlib.md5(e["name"].encode()).hexdigest()[:12]
                entities.append(Entity(
                    id=entity_id,
                    name=e["name"],
                    entity_type=entity_type,
                    confidence=e.get("confidence", 0.8)
                ))
            
            return entities
            
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")
            return self.extract_entities(text)


# ============ RELATIONSHIP EXTRACTOR ============

class RelationshipExtractor:
    """
    Extract relationships between entities.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        
        # Relationship patterns (subject pattern, relation, object pattern)
        self.patterns = [
            (r"(\w+) works for (\w+)", RelationType.WORKS_FOR),
            (r"(\w+) is part of (\w+)", RelationType.PART_OF),
            (r"(\w+) is located in (\w+)", RelationType.LOCATED_IN),
            (r"(\w+) created (\w+)", RelationType.CREATED_BY),
            (r"(\w+) depends on (\w+)", RelationType.DEPENDS_ON),
            (r"(\w+) references (\w+)", RelationType.REFERENCES),
        ]
    
    def extract_relationships(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relationship]:
        """Extract relationships from text given entities"""
        relationships = []
        entity_names = {e.name.lower(): e for e in entities}
        
        # Simple co-occurrence based relationships
        sentences = text.split(".")
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            found_entities = []
            
            for name, entity in entity_names.items():
                if name in sentence_lower:
                    found_entities.append(entity)
            
            # Create RELATED_TO for co-occurring entities
            for i, e1 in enumerate(found_entities):
                for e2 in found_entities[i+1:]:
                    rel_id = f"{e1.id}_{e2.id}"
                    relationships.append(Relationship(
                        id=rel_id,
                        source_id=e1.id,
                        target_id=e2.id,
                        relation_type=RelationType.RELATED_TO,
                        confidence=0.6
                    ))
        
        return relationships
    
    def extract_triplets(self, text: str) -> List[Triplet]:
        """Extract subject-predicate-object triplets"""
        triplets = []
        
        # Simple pattern-based extraction
        patterns = [
            r"(\w+(?:\s+\w+)?)\s+(is|are|was|were|has|have)\s+(\w+(?:\s+\w+)?)",
            r"(\w+(?:\s+\w+)?)\s+(works for|belongs to|created)\s+(\w+(?:\s+\w+)?)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 3:
                    triplets.append(Triplet(
                        subject=match[0],
                        predicate=match[1],
                        object=match[2],
                        confidence=0.6
                    ))
        
        return triplets


# ============ GRAPH STORE ============

class GraphStore(ABC):
    """Abstract base class for graph storage"""
    
    @abstractmethod
    async def add_entity(self, entity: Entity) -> bool:
        pass
    
    @abstractmethod
    async def add_relationship(self, relationship: Relationship) -> bool:
        pass
    
    @abstractmethod
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        pass
    
    @abstractmethod
    async def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1,
        relation_types: Optional[List[RelationType]] = None
    ) -> Subgraph:
        pass
    
    @abstractmethod
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[EntityType] = None,
        limit: int = 10
    ) -> List[Entity]:
        pass


class InMemoryGraphStore(GraphStore):
    """
    In-memory graph store for development/testing.
    Production should use Neo4j.
    """
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.adjacency: Dict[str, List[str]] = {}  # entity_id -> [relationship_ids]
    
    async def add_entity(self, entity: Entity) -> bool:
        self.entities[entity.id] = entity
        if entity.id not in self.adjacency:
            self.adjacency[entity.id] = []
        return True
    
    async def add_relationship(self, relationship: Relationship) -> bool:
        self.relationships[relationship.id] = relationship
        
        # Update adjacency
        if relationship.source_id not in self.adjacency:
            self.adjacency[relationship.source_id] = []
        self.adjacency[relationship.source_id].append(relationship.id)
        
        if relationship.target_id not in self.adjacency:
            self.adjacency[relationship.target_id] = []
        self.adjacency[relationship.target_id].append(relationship.id)
        
        return True
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)
    
    async def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1,
        relation_types: Optional[List[RelationType]] = None
    ) -> Subgraph:
        """Get subgraph around an entity"""
        visited_entities: Set[str] = set()
        visited_relationships: Set[str] = set()
        
        entities: List[Entity] = []
        relationships: List[Relationship] = []
        
        # BFS traversal
        queue = [(entity_id, 0)]
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            if current_id in visited_entities or current_depth > depth:
                continue
            
            visited_entities.add(current_id)
            
            if current_id in self.entities:
                entities.append(self.entities[current_id])
            
            # Get relationships
            for rel_id in self.adjacency.get(current_id, []):
                if rel_id in visited_relationships:
                    continue
                
                rel = self.relationships[rel_id]
                
                # Filter by relation type
                if relation_types and rel.relation_type not in relation_types:
                    continue
                
                visited_relationships.add(rel_id)
                relationships.append(rel)
                
                # Add neighbors to queue
                neighbor_id = rel.target_id if rel.source_id == current_id else rel.source_id
                if neighbor_id not in visited_entities:
                    queue.append((neighbor_id, current_depth + 1))
        
        return Subgraph(
            entities=entities,
            relationships=relationships,
            center_entity=entity_id,
            depth=depth
        )
    
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[EntityType] = None,
        limit: int = 10
    ) -> List[Entity]:
        """Search entities by name"""
        query_lower = query.lower()
        results = []
        
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            
            if query_lower in entity.name.lower():
                results.append(entity)
                
                if len(results) >= limit:
                    break
        
        return results


class Neo4jGraphStore(GraphStore):
    """
    Neo4j graph database integration.
    
    Requires: neo4j Python driver
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j"
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver = None
    
    async def _get_driver(self):
        """Get or create Neo4j driver"""
        if self._driver is None:
            try:
                from neo4j import AsyncGraphDatabase
                self._driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password)
                )
            except ImportError:
                logger.error("neo4j package not installed")
                raise RuntimeError("neo4j package required for Neo4jGraphStore")
        return self._driver
    
    async def close(self):
        """Close Neo4j connection"""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    async def add_entity(self, entity: Entity) -> bool:
        """Add entity to Neo4j"""
        driver = await self._get_driver()
        
        query = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.entity_type = $entity_type,
            e.confidence = $confidence,
            e.properties = $properties
        RETURN e
        """
        
        async with driver.session(database=self.database) as session:
            await session.run(
                query,
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type.value,
                confidence=entity.confidence,
                properties=json.dumps(entity.properties)
            )
        
        return True
    
    async def add_relationship(self, relationship: Relationship) -> bool:
        """Add relationship to Neo4j"""
        driver = await self._get_driver()
        
        # Dynamic relationship type
        rel_type = relationship.relation_type.value.upper()
        
        query = f"""
        MATCH (source:Entity {{id: $source_id}})
        MATCH (target:Entity {{id: $target_id}})
        MERGE (source)-[r:{rel_type} {{id: $id}}]->(target)
        SET r.weight = $weight,
            r.confidence = $confidence
        RETURN r
        """
        
        async with driver.session(database=self.database) as session:
            await session.run(
                query,
                id=relationship.id,
                source_id=relationship.source_id,
                target_id=relationship.target_id,
                weight=relationship.weight,
                confidence=relationship.confidence
            )
        
        return True
    
    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity from Neo4j"""
        driver = await self._get_driver()
        
        query = """
        MATCH (e:Entity {id: $id})
        RETURN e
        """
        
        async with driver.session(database=self.database) as session:
            result = await session.run(query, id=entity_id)
            record = await result.single()
            
            if record:
                node = record["e"]
                return Entity(
                    id=node["id"],
                    name=node["name"],
                    entity_type=EntityType(node["entity_type"]),
                    confidence=node["confidence"],
                    properties=json.loads(node.get("properties", "{}"))
                )
        
        return None
    
    async def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1,
        relation_types: Optional[List[RelationType]] = None
    ) -> Subgraph:
        """Get subgraph from Neo4j"""
        driver = await self._get_driver()
        
        # Build relationship type filter
        rel_filter = ""
        if relation_types:
            types = "|".join(r.value.upper() for r in relation_types)
            rel_filter = f":{types}"
        
        query = f"""
        MATCH path = (center:Entity {{id: $id}})-[r{rel_filter}*1..{depth}]-(neighbor:Entity)
        RETURN center, neighbor, relationships(path) as rels
        """
        
        entities = []
        relationships = []
        seen_entities = set()
        seen_rels = set()
        
        async with driver.session(database=self.database) as session:
            result = await session.run(query, id=entity_id)
            
            async for record in result:
                # Process center
                center = record["center"]
                if center["id"] not in seen_entities:
                    seen_entities.add(center["id"])
                    entities.append(Entity(
                        id=center["id"],
                        name=center["name"],
                        entity_type=EntityType(center["entity_type"]),
                        confidence=center["confidence"]
                    ))
                
                # Process neighbor
                neighbor = record["neighbor"]
                if neighbor["id"] not in seen_entities:
                    seen_entities.add(neighbor["id"])
                    entities.append(Entity(
                        id=neighbor["id"],
                        name=neighbor["name"],
                        entity_type=EntityType(neighbor["entity_type"]),
                        confidence=neighbor["confidence"]
                    ))
                
                # Process relationships
                for rel in record["rels"]:
                    if rel["id"] not in seen_rels:
                        seen_rels.add(rel["id"])
                        relationships.append(Relationship(
                            id=rel["id"],
                            source_id=rel.start_node["id"],
                            target_id=rel.end_node["id"],
                            relation_type=RelationType(rel.type.lower()),
                            weight=rel.get("weight", 1.0),
                            confidence=rel.get("confidence", 1.0)
                        ))
        
        return Subgraph(
            entities=entities,
            relationships=relationships,
            center_entity=entity_id,
            depth=depth
        )
    
    async def search_entities(
        self,
        query: str,
        entity_type: Optional[EntityType] = None,
        limit: int = 10
    ) -> List[Entity]:
        """Search entities in Neo4j"""
        driver = await self._get_driver()
        
        type_filter = ""
        if entity_type:
            type_filter = f"AND e.entity_type = '{entity_type.value}'"
        
        cypher_query = f"""
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($query)
        {type_filter}
        RETURN e
        LIMIT $limit
        """
        
        entities = []
        
        async with driver.session(database=self.database) as session:
            result = await session.run(cypher_query, query=query, limit=limit)
            
            async for record in result:
                node = record["e"]
                entities.append(Entity(
                    id=node["id"],
                    name=node["name"],
                    entity_type=EntityType(node["entity_type"]),
                    confidence=node["confidence"]
                ))
        
        return entities


# ============ GRAPH RAG PIPELINE ============

class GraphRAGPipeline:
    """
    Graph-enhanced RAG pipeline.
    
    Combines:
    1. Traditional vector retrieval
    2. Graph-based context expansion
    3. Subgraph serialization for context
    """
    
    def __init__(
        self,
        graph_store: GraphStore,
        vector_store: Optional[Any] = None,
        entity_extractor: Optional[EntityExtractor] = None,
        relationship_extractor: Optional[RelationshipExtractor] = None,
        llm_client: Optional[Any] = None
    ):
        self.graph_store = graph_store
        self.vector_store = vector_store
        self.entity_extractor = entity_extractor or EntityExtractor(llm_client)
        self.relationship_extractor = relationship_extractor or RelationshipExtractor(llm_client)
        self.llm_client = llm_client
    
    async def index_document(
        self,
        document_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Index a document into the knowledge graph.
        
        Returns count of entities and relationships created.
        """
        metadata = metadata or {}
        
        # Extract entities
        entities = self.entity_extractor.extract_entities(text)
        
        # Extract relationships
        relationships = self.relationship_extractor.extract_relationships(text, entities)
        
        # Create document entity
        doc_entity = Entity(
            id=hashlib.md5(document_id.encode()).hexdigest()[:12],
            name=document_id,
            entity_type=EntityType.DOCUMENT,
            properties=metadata
        )
        await self.graph_store.add_entity(doc_entity)
        
        # Add entities and connect to document
        for entity in entities:
            entity.source_chunks.append(document_id)
            await self.graph_store.add_entity(entity)
            
            # Connect entity to document
            rel = Relationship(
                id=f"{doc_entity.id}_{entity.id}",
                source_id=doc_entity.id,
                target_id=entity.id,
                relation_type=RelationType.MENTIONS
            )
            await self.graph_store.add_relationship(rel)
        
        # Add relationships
        for rel in relationships:
            await self.graph_store.add_relationship(rel)
        
        return {
            "entities": len(entities),
            "relationships": len(relationships)
        }
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        graph_depth: int = 2
    ) -> GraphRAGResult:
        """
        Retrieve relevant context using graph + vector.
        """
        # 1. Extract entities from query
        query_entities = self.entity_extractor.extract_entities(query)
        
        # 2. Search for matching entities in graph
        found_entities = []
        for entity in query_entities:
            matches = await self.graph_store.search_entities(
                entity.name,
                entity_type=entity.entity_type,
                limit=3
            )
            found_entities.extend(matches)
        
        # Also search for query terms directly
        words = query.split()
        for word in words:
            if len(word) > 3:
                matches = await self.graph_store.search_entities(word, limit=2)
                found_entities.extend(matches)
        
        # 3. Expand graph around found entities
        all_entities = []
        all_relationships = []
        seen_entity_ids = set()
        seen_rel_ids = set()
        
        for entity in found_entities:
            subgraph = await self.graph_store.get_neighbors(
                entity.id,
                depth=graph_depth
            )
            
            for e in subgraph.entities:
                if e.id not in seen_entity_ids:
                    seen_entity_ids.add(e.id)
                    all_entities.append(e)
            
            for r in subgraph.relationships:
                if r.id not in seen_rel_ids:
                    seen_rel_ids.add(r.id)
                    all_relationships.append(r)
        
        # 4. Build subgraph
        subgraph = Subgraph(
            entities=all_entities,
            relationships=all_relationships,
            depth=graph_depth
        )
        
        # 5. Serialize graph to text context
        graph_context = self._serialize_subgraph(subgraph)
        
        # 6. Vector retrieval (if available)
        text_chunks = []
        if self.vector_store:
            try:
                results = self.vector_store.similarity_search(query, k=top_k)
                text_chunks = [r.page_content for r in results]
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # 7. Combine contexts
        combined_context = self._combine_contexts(graph_context, text_chunks)
        
        return GraphRAGResult(
            query=query,
            subgraph=subgraph,
            text_chunks=text_chunks,
            graph_context=graph_context,
            combined_context=combined_context,
            entities_found=[e.name for e in found_entities],
            relationships_found=len(all_relationships),
            confidence=min(1.0, len(found_entities) / 5 * 0.5 + len(text_chunks) / top_k * 0.5)
        )
    
    def _serialize_subgraph(self, subgraph: Subgraph) -> str:
        """Convert subgraph to text for LLM context"""
        if not subgraph.entities:
            return ""
        
        lines = ["=== Knowledge Graph Context ===\n"]
        
        # Entities
        lines.append("Entities:")
        for entity in subgraph.entities[:20]:  # Limit for context window
            lines.append(f"  - {entity.name} ({entity.entity_type.value})")
        
        # Relationships
        if subgraph.relationships:
            lines.append("\nRelationships:")
            
            # Build entity lookup
            entity_lookup = {e.id: e.name for e in subgraph.entities}
            
            for rel in subgraph.relationships[:30]:
                source_name = entity_lookup.get(rel.source_id, rel.source_id)
                target_name = entity_lookup.get(rel.target_id, rel.target_id)
                lines.append(f"  - {source_name} --[{rel.relation_type.value}]--> {target_name}")
        
        return "\n".join(lines)
    
    def _combine_contexts(
        self,
        graph_context: str,
        text_chunks: List[str]
    ) -> str:
        """Combine graph and text contexts"""
        parts = []
        
        if graph_context:
            parts.append(graph_context)
        
        if text_chunks:
            parts.append("\n=== Document Context ===\n")
            for i, chunk in enumerate(text_chunks, 1):
                parts.append(f"[{i}] {chunk}\n")
        
        return "\n".join(parts)


# ============ CYPHER GENERATOR ============

class CypherGenerator:
    """
    Generate Cypher queries from natural language.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        
        # Common Cypher patterns
        self.templates = {
            "find_entity": "MATCH (e:Entity) WHERE e.name CONTAINS $query RETURN e",
            "find_neighbors": "MATCH (e:Entity {id: $id})-[r]-(neighbor) RETURN e, r, neighbor",
            "find_path": "MATCH path = shortestPath((a:Entity {name: $start})-[*]-(b:Entity {name: $end})) RETURN path",
            "count_relations": "MATCH (e:Entity {id: $id})-[r]->() RETURN type(r), count(r)",
        }
    
    def generate_cypher(self, query: str) -> str:
        """
        Generate Cypher query from natural language.
        
        Uses templates for common patterns, LLM for complex queries.
        """
        query_lower = query.lower()
        
        # Template matching
        if "find" in query_lower and "named" in query_lower:
            return self.templates["find_entity"]
        
        if "connected" in query_lower or "related" in query_lower:
            return self.templates["find_neighbors"]
        
        if "path" in query_lower or "between" in query_lower:
            return self.templates["find_path"]
        
        if "count" in query_lower or "how many" in query_lower:
            return self.templates["count_relations"]
        
        # Default to entity search
        return self.templates["find_entity"]


# ============ CONVENIENCE FUNCTIONS ============

def create_graph_rag(
    use_neo4j: bool = False,
    neo4j_uri: str = "bolt://localhost:7687",
    neo4j_user: str = "neo4j",
    neo4j_password: str = "password",
    llm_client: Optional[Any] = None
) -> GraphRAGPipeline:
    """
    Create a Graph RAG pipeline.
    
    Args:
        use_neo4j: Whether to use Neo4j (requires running instance)
        neo4j_uri: Neo4j connection URI
        neo4j_user: Neo4j username
        neo4j_password: Neo4j password
        llm_client: Optional LLM client for entity extraction
        
    Returns:
        GraphRAGPipeline instance
    """
    if use_neo4j:
        graph_store = Neo4jGraphStore(
            uri=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
    else:
        graph_store = InMemoryGraphStore()
    
    return GraphRAGPipeline(
        graph_store=graph_store,
        entity_extractor=EntityExtractor(llm_client),
        relationship_extractor=RelationshipExtractor(llm_client),
        llm_client=llm_client
    )


# ============ EXPORTS ============

__all__ = [
    # Types
    "EntityType",
    "RelationType",
    # Models
    "Entity",
    "Relationship",
    "Triplet",
    "Subgraph",
    "GraphRAGResult",
    # Extractors
    "EntityExtractor",
    "RelationshipExtractor",
    # Stores
    "GraphStore",
    "InMemoryGraphStore",
    "Neo4jGraphStore",
    # Pipeline
    "GraphRAGPipeline",
    "CypherGenerator",
    # Factory
    "create_graph_rag",
]
