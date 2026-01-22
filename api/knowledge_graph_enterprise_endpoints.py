"""
Enterprise Knowledge Graph API Endpoints
Premium graph-based knowledge management with LLM-powered extraction

Features:
- LLM-powered entity extraction
- Relationship inference
- Graph queries
- Visualization data
- Knowledge gap detection
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
import json

router = APIRouter(prefix="/api/knowledge-graph", tags=["Enterprise Knowledge Graph"])


# =============================================================================
# MODELS
# =============================================================================

class EntityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: str = Field(..., description="Type: person, organization, concept, location, event, etc.")
    properties: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str] = None
    source_document: Optional[str] = None


class EntityUpdate(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class RelationshipCreate(BaseModel):
    source_entity: str = Field(..., description="Source entity ID")
    target_entity: str = Field(..., description="Target entity ID")
    relationship_type: str = Field(..., description="Type: relates_to, works_at, part_of, etc.")
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: float = Field(default=1.0, ge=0, le=1)
    bidirectional: bool = False


class TextExtractionRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text to extract entities from")
    extract_relationships: bool = True
    entity_types: Optional[List[str]] = None
    min_confidence: float = Field(default=0.5, ge=0, le=1)


class DocumentIndexRequest(BaseModel):
    document_id: str = Field(..., description="Document ID to index")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extract_entities: bool = True
    extract_relationships: bool = True


class GraphQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    max_hops: int = Field(default=2, ge=1, le=5)
    include_paths: bool = True
    entity_limit: int = Field(default=50, ge=1, le=200)


class PathQueryRequest(BaseModel):
    source_entity: str = Field(..., description="Source entity ID")
    target_entity: str = Field(..., description="Target entity ID")
    max_length: int = Field(default=4, ge=1, le=10)
    relationship_types: Optional[List[str]] = None


class SubgraphRequest(BaseModel):
    center_entity: str = Field(..., description="Center entity ID")
    radius: int = Field(default=2, ge=1, le=5)
    include_properties: bool = True
    max_nodes: int = Field(default=100, ge=1, le=500)


class MergeRequest(BaseModel):
    entity_ids: List[str] = Field(..., min_items=2, description="Entity IDs to merge")
    target_name: str = Field(..., description="Name for merged entity")
    merge_strategy: str = Field(default="combine", description="combine, keep_first, keep_most_connected")


class KnowledgeGapRequest(BaseModel):
    domain: Optional[str] = None
    entity_types: Optional[List[str]] = None
    min_connections: int = Field(default=3, ge=1)


# =============================================================================
# ENTITY ENDPOINTS
# =============================================================================

@router.post("/entities", summary="Create entity")
async def create_entity(entity: EntityCreate):
    """Create a new knowledge graph entity"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.create_entity(
            name=entity.name,
            entity_type=entity.entity_type,
            properties=entity.properties,
            description=entity.description,
            source_document=entity.source_document
        )
        
        return {
            "success": True,
            "entity": result,
            "message": "Entity created"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities", summary="List entities")
async def list_entities(
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    min_connections: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List entities with optional filters"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        entities = knowledge_graph.list_entities(
            entity_type=entity_type,
            search=search,
            min_connections=min_connections,
            limit=limit,
            offset=offset
        )
        
        return {
            "success": True,
            "count": len(entities),
            "entities": entities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}", summary="Get entity")
async def get_entity(entity_id: str, include_relationships: bool = True):
    """Get entity by ID with optional relationships"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        entity = knowledge_graph.get_entity(entity_id, include_relationships)
        
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "entity": entity
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/entities/{entity_id}", summary="Update entity")
async def update_entity(entity_id: str, updates: EntityUpdate):
    """Update entity properties"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.update_entity(
            entity_id=entity_id,
            updates=updates.dict(exclude_none=True)
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "entity": result,
            "message": "Entity updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}", summary="Delete entity")
async def delete_entity(entity_id: str, cascade_relationships: bool = True):
    """Delete entity and optionally its relationships"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        success = await knowledge_graph.delete_entity(entity_id, cascade_relationships)
        
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "message": "Entity deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/merge", summary="Merge entities")
async def merge_entities(request: MergeRequest):
    """Merge multiple entities into one"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.merge_entities(
            entity_ids=request.entity_ids,
            target_name=request.target_name,
            merge_strategy=request.merge_strategy
        )
        
        return {
            "success": True,
            "merged_entity": result,
            "message": f"Merged {len(request.entity_ids)} entities"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/similar", summary="Find similar entities")
async def find_similar_entities(entity_id: str, limit: int = Query(10, ge=1, le=50)):
    """Find entities similar to the given entity"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        similar = await knowledge_graph.find_similar_entities(entity_id, limit)
        
        return {
            "success": True,
            "count": len(similar),
            "similar_entities": similar
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# RELATIONSHIP ENDPOINTS
# =============================================================================

@router.post("/relationships", summary="Create relationship")
async def create_relationship(relationship: RelationshipCreate):
    """Create a relationship between entities"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.create_relationship(
            source_id=relationship.source_entity,
            target_id=relationship.target_entity,
            relationship_type=relationship.relationship_type,
            properties=relationship.properties,
            weight=relationship.weight,
            bidirectional=relationship.bidirectional
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Source or target entity not found")
        
        return {
            "success": True,
            "relationship": result,
            "message": "Relationship created"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationships", summary="List relationships")
async def list_relationships(
    relationship_type: Optional[str] = None,
    source_entity: Optional[str] = None,
    target_entity: Optional[str] = None,
    min_weight: float = Query(0, ge=0, le=1),
    limit: int = Query(100, ge=1, le=500)
):
    """List relationships with filters"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        relationships = knowledge_graph.list_relationships(
            relationship_type=relationship_type,
            source_entity=source_entity,
            target_entity=target_entity,
            min_weight=min_weight,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(relationships),
            "relationships": relationships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/relationships/{relationship_id}", summary="Delete relationship")
async def delete_relationship(relationship_id: str):
    """Delete a relationship"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        success = await knowledge_graph.delete_relationship(relationship_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Relationship not found")
        
        return {
            "success": True,
            "message": "Relationship deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relationship-types", summary="Get relationship types")
async def get_relationship_types():
    """Get all relationship types in the graph"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        types = knowledge_graph.get_relationship_types()
        
        return {
            "success": True,
            "types": types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXTRACTION ENDPOINTS
# =============================================================================

@router.post("/extract/text", summary="Extract from text")
async def extract_from_text(request: TextExtractionRequest, background_tasks: BackgroundTasks):
    """Extract entities and relationships from text using LLM"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.extract_from_text(
            text=request.text,
            extract_relationships=request.extract_relationships,
            entity_types=request.entity_types,
            min_confidence=request.min_confidence
        )
        
        return {
            "success": True,
            "entities_found": len(result["entities"]),
            "relationships_found": len(result.get("relationships", [])),
            "extraction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/document", summary="Index document")
async def index_document(request: DocumentIndexRequest, background_tasks: BackgroundTasks):
    """Index a document and extract knowledge"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        # For large documents, process in background
        if len(request.content) > 10000:
            background_tasks.add_task(
                knowledge_graph.index_document,
                request.document_id,
                request.content,
                request.metadata,
                request.extract_entities,
                request.extract_relationships
            )
            
            return {
                "success": True,
                "status": "processing",
                "message": "Document being processed in background"
            }
        
        result = await knowledge_graph.index_document(
            document_id=request.document_id,
            content=request.content,
            metadata=request.metadata,
            extract_entities=request.extract_entities,
            extract_relationships=request.extract_relationships
        )
        
        return {
            "success": True,
            "document_id": request.document_id,
            "entities_extracted": result["entities_count"],
            "relationships_extracted": result["relationships_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/infer-relationships", summary="Infer relationships")
async def infer_relationships(
    entity_ids: Optional[List[str]] = None,
    min_confidence: float = Query(0.7, ge=0, le=1),
    max_inferences: int = Query(50, ge=1, le=200)
):
    """Use LLM to infer potential relationships between entities"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.infer_relationships(
            entity_ids=entity_ids,
            min_confidence=min_confidence,
            max_inferences=max_inferences
        )
        
        return {
            "success": True,
            "inferred_count": len(result),
            "inferred_relationships": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# QUERY ENDPOINTS
# =============================================================================

@router.post("/query", summary="Natural language query")
async def query_graph(request: GraphQueryRequest):
    """Query the knowledge graph using natural language"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.natural_language_query(
            query=request.query,
            max_hops=request.max_hops,
            include_paths=request.include_paths,
            entity_limit=request.entity_limit
        )
        
        return {
            "success": True,
            "query": request.query,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/path", summary="Find paths between entities")
async def find_paths(request: PathQueryRequest):
    """Find paths between two entities"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        paths = await knowledge_graph.find_paths(
            source_id=request.source_entity,
            target_id=request.target_entity,
            max_length=request.max_length,
            relationship_types=request.relationship_types
        )
        
        return {
            "success": True,
            "source": request.source_entity,
            "target": request.target_entity,
            "paths_found": len(paths),
            "paths": paths
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/subgraph", summary="Get subgraph")
async def get_subgraph(request: SubgraphRequest):
    """Get a subgraph around a central entity"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        subgraph = await knowledge_graph.get_subgraph(
            center_entity=request.center_entity,
            radius=request.radius,
            include_properties=request.include_properties,
            max_nodes=request.max_nodes
        )
        
        return {
            "success": True,
            "center": request.center_entity,
            "nodes": len(subgraph["nodes"]),
            "edges": len(subgraph["edges"]),
            "subgraph": subgraph
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/neighbors/{entity_id}", summary="Get entity neighbors")
async def get_neighbors(
    entity_id: str,
    relationship_type: Optional[str] = None,
    direction: str = Query("both", pattern="^(in|out|both)$"),
    limit: int = Query(50, ge=1, le=200)
):
    """Get neighboring entities"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        neighbors = knowledge_graph.get_neighbors(
            entity_id=entity_id,
            relationship_type=relationship_type,
            direction=direction,
            limit=limit
        )
        
        return {
            "success": True,
            "entity_id": entity_id,
            "count": len(neighbors),
            "neighbors": neighbors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VISUALIZATION
# =============================================================================

@router.get("/visualize", summary="Get visualization data")
async def get_visualization_data(
    entity_types: Optional[str] = None,
    relationship_types: Optional[str] = None,
    max_nodes: int = Query(200, ge=10, le=1000),
    layout: str = Query("force", pattern="^(force|hierarchical|circular|grid)$")
):
    """Get graph data formatted for visualization (D3.js/Cytoscape compatible)"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        entity_type_list = entity_types.split(",") if entity_types else None
        relationship_type_list = relationship_types.split(",") if relationship_types else None
        
        viz_data = knowledge_graph.get_visualization_data(
            entity_types=entity_type_list,
            relationship_types=relationship_type_list,
            max_nodes=max_nodes,
            layout=layout
        )
        
        return {
            "success": True,
            "format": "cytoscape",
            "layout": layout,
            "data": viz_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualize/entity/{entity_id}", summary="Get entity-centered visualization")
async def get_entity_visualization(
    entity_id: str,
    depth: int = Query(2, ge=1, le=4),
    max_nodes: int = Query(100, ge=10, le=500)
):
    """Get visualization data centered on an entity"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        viz_data = await knowledge_graph.get_entity_visualization(
            entity_id=entity_id,
            depth=depth,
            max_nodes=max_nodes
        )
        
        if not viz_data:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "center_entity": entity_id,
            "data": viz_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ANALYSIS
# =============================================================================

@router.post("/analyze/gaps", summary="Find knowledge gaps")
async def find_knowledge_gaps(request: KnowledgeGapRequest):
    """Identify gaps in the knowledge graph"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        gaps = await knowledge_graph.find_knowledge_gaps(
            domain=request.domain,
            entity_types=request.entity_types,
            min_connections=request.min_connections
        )
        
        return {
            "success": True,
            "gaps_found": len(gaps),
            "gaps": gaps
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/clusters", summary="Detect clusters")
async def detect_clusters(min_cluster_size: int = Query(3, ge=2)):
    """Detect entity clusters in the graph"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        clusters = knowledge_graph.detect_clusters(min_cluster_size)
        
        return {
            "success": True,
            "clusters_found": len(clusters),
            "clusters": clusters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/central-entities", summary="Find central entities")
async def find_central_entities(
    metric: str = Query("degree", pattern="^(degree|betweenness|pagerank)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """Find most central/important entities"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        central = knowledge_graph.find_central_entities(metric, limit)
        
        return {
            "success": True,
            "metric": metric,
            "entities": central
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/orphans", summary="Find orphan entities")
async def find_orphans():
    """Find entities with no relationships"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        orphans = knowledge_graph.find_orphan_entities()
        
        return {
            "success": True,
            "count": len(orphans),
            "orphans": orphans
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# STATISTICS
# =============================================================================

@router.get("/stats", summary="Get graph statistics")
async def get_stats():
    """Get overall knowledge graph statistics"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        stats = knowledge_graph.get_statistics()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity-types", summary="Get entity types")
async def get_entity_types():
    """Get all entity types with counts"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        types = knowledge_graph.get_entity_types_with_counts()
        
        return {
            "success": True,
            "types": types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# IMPORT/EXPORT
# =============================================================================

@router.get("/export", summary="Export knowledge graph")
async def export_graph(format: str = Query("json", pattern="^(json|cypher|graphml)$")):
    """Export the entire knowledge graph"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        export_data = await knowledge_graph.export_graph(format)
        
        return {
            "success": True,
            "format": format,
            "data": export_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", summary="Import knowledge graph")
async def import_graph(
    data: Dict[str, Any],
    merge: bool = Query(True, description="Merge with existing data"),
    background_tasks: BackgroundTasks = None
):
    """Import knowledge graph data"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        result = await knowledge_graph.import_graph(data, merge)
        
        return {
            "success": True,
            "entities_imported": result["entities"],
            "relationships_imported": result["relationships"],
            "message": "Graph imported"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH
# =============================================================================

@router.get("/health", summary="Health check")
async def health_check():
    """Check knowledge graph health"""
    try:
        from core.enterprise_knowledge_graph import knowledge_graph
        
        health = knowledge_graph.health_check()
        
        return {
            "success": True,
            "status": "healthy" if health["is_healthy"] else "degraded",
            "details": health
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
