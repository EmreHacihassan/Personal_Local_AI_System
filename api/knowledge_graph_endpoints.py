"""
Knowledge Graph API Endpoints
Entity extraction and relationship mapping for enhanced RAG
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-graph", tags=["Knowledge Graph"])

# Lazy import
_kg = None

def get_kg():
    global _kg
    if _kg is None:
        from core.knowledge_graph import get_knowledge_graph
        _kg = get_knowledge_graph()
    return _kg


class EntityCreate(BaseModel):
    name: str
    type: str
    properties: Optional[Dict[str, Any]] = None
    source_doc: Optional[str] = None


class RelationshipCreate(BaseModel):
    source_name: str
    source_type: str
    target_name: str
    target_type: str
    relationship_type: str
    properties: Optional[Dict[str, Any]] = None
    source_doc: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str
    source_doc: Optional[str] = None
    use_llm: bool = True


class QueryRequest(BaseModel):
    query: str
    top_k: int = 10


class EntityResponse(BaseModel):
    id: str
    name: str
    type: str
    properties: Dict[str, Any]
    mention_count: int


class RelationshipResponse(BaseModel):
    id: str
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    type: str
    weight: float


@router.get("/status")
async def get_status():
    """Get knowledge graph status"""
    try:
        kg = get_kg()
        stats = kg.get_statistics()
        return {
            "status": "active",
            **stats
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/entities", response_model=EntityResponse)
async def create_entity(request: EntityCreate):
    """Create or update an entity"""
    kg = get_kg()
    entity = kg.add_entity(
        name=request.name,
        entity_type=request.type,
        properties=request.properties,
        source_doc=request.source_doc
    )
    
    return EntityResponse(
        id=entity.id,
        name=entity.name,
        type=entity.type,
        properties=entity.properties,
        mention_count=len(entity.mentions)
    )


@router.get("/entities")
async def list_entities(
    entity_type: Optional[str] = None,
    limit: int = 50
):
    """List all entities"""
    kg = get_kg()
    
    entities = []
    for entity in list(kg.entities.values())[:limit]:
        if entity_type and entity.type != entity_type:
            continue
        entities.append({
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "mention_count": len(entity.mentions)
        })
    
    return {"entities": entities, "total": len(kg.entities)}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity details"""
    kg = get_kg()
    entity = kg.get_entity(entity_id)
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Get relationships
    relationships = kg.get_entity_relationships(entity_id)
    neighbors = kg.get_neighbors(entity_id, depth=1)
    
    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.type,
        "properties": entity.properties,
        "mentions": entity.mentions,
        "created_at": entity.created_at,
        "relationships": [
            {
                "id": r.id,
                "type": r.type,
                "direction": "outgoing" if r.source_id == entity_id else "incoming",
                "other_entity": r.target_id if r.source_id == entity_id else r.source_id
            }
            for r in relationships
        ],
        "neighbors": [
            {"id": n.id, "name": n.name, "type": n.type}
            for n in neighbors[:10]
        ]
    }


@router.get("/entities/search/{query}")
async def search_entities(query: str, entity_type: Optional[str] = None, limit: int = 10):
    """Search entities by name"""
    kg = get_kg()
    entities = kg.search_entities(query, entity_type, limit)
    
    return {"entities": [
        {
            "id": e.id,
            "name": e.name,
            "type": e.type
        }
        for e in entities
    ]}


@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(request: RelationshipCreate):
    """Create a relationship between entities"""
    kg = get_kg()
    rel = kg.add_relationship(
        source_name=request.source_name,
        source_type=request.source_type,
        target_name=request.target_name,
        target_type=request.target_type,
        relationship_type=request.relationship_type,
        properties=request.properties,
        source_doc=request.source_doc
    )
    
    source_entity = kg.get_entity(rel.source_id)
    target_entity = kg.get_entity(rel.target_id)
    
    return RelationshipResponse(
        id=rel.id,
        source_id=rel.source_id,
        source_name=source_entity.name if source_entity else "",
        target_id=rel.target_id,
        target_name=target_entity.name if target_entity else "",
        type=rel.type,
        weight=rel.weight
    )


@router.get("/relationships")
async def list_relationships(
    relationship_type: Optional[str] = None,
    limit: int = 50
):
    """List all relationships"""
    kg = get_kg()
    
    relationships = []
    for rel in list(kg.relationships.values())[:limit]:
        if relationship_type and rel.type != relationship_type:
            continue
        
        source = kg.get_entity(rel.source_id)
        target = kg.get_entity(rel.target_id)
        
        relationships.append({
            "id": rel.id,
            "source": {"id": rel.source_id, "name": source.name if source else ""},
            "target": {"id": rel.target_id, "name": target.name if target else ""},
            "type": rel.type,
            "weight": rel.weight
        })
    
    return {"relationships": relationships, "total": len(kg.relationships)}


@router.post("/extract")
async def extract_from_text(request: ExtractRequest):
    """Extract entities and relationships from text"""
    kg = get_kg()
    
    # Extract entities
    entities = await kg.extract_entities_from_text(
        request.text,
        source_doc=request.source_doc,
        use_llm=request.use_llm
    )
    
    # Extract relationships
    relationships = await kg.extract_relationships_from_text(
        request.text,
        source_doc=request.source_doc
    )
    
    return {
        "entities_extracted": len(entities),
        "relationships_extracted": len(relationships),
        "entities": [
            {"id": e.id, "name": e.name, "type": e.type}
            for e in entities
        ],
        "relationships": [
            {"source": r.source_id, "target": r.target_id, "type": r.type}
            for r in relationships
        ]
    }


@router.post("/query")
async def query_graph(request: QueryRequest):
    """Query the knowledge graph"""
    kg = get_kg()
    
    result = kg.query(request.query, top_k=request.top_k)
    
    return {
        "entities": [
            {"id": e.id, "name": e.name, "type": e.type}
            for e in result.entities
        ],
        "relationships": [
            {
                "source": r.source_id,
                "target": r.target_id,
                "type": r.type
            }
            for r in result.relationships
        ],
        "paths": result.paths,
        "context": result.context,
        "score": result.score
    }


@router.get("/path/{source_id}/{target_id}")
async def find_path(source_id: str, target_id: str, max_depth: int = 5):
    """Find shortest path between entities"""
    kg = get_kg()
    
    path = kg.find_path(source_id, target_id, max_depth)
    
    if not path:
        raise HTTPException(status_code=404, detail="No path found")
    
    path_entities = [kg.get_entity(eid) for eid in path]
    
    return {
        "path": path,
        "entities": [
            {"id": e.id, "name": e.name, "type": e.type}
            for e in path_entities if e
        ],
        "length": len(path)
    }


@router.get("/export")
async def export_graph():
    """Export entire graph as JSON"""
    kg = get_kg()
    return kg.export_to_json()


@router.get("/statistics")
async def get_statistics():
    """Get graph statistics"""
    kg = get_kg()
    return kg.get_statistics()


@router.delete("/clear")
async def clear_graph():
    """Clear all graph data"""
    kg = get_kg()
    kg.clear()
    return {"status": "cleared"}


# Visualization endpoint
@router.get("/visualization")
async def get_visualization_data():
    """Get data for graph visualization (D3.js format)"""
    kg = get_kg()
    
    nodes = [
        {
            "id": e.id,
            "label": e.name,
            "group": e.type
        }
        for e in kg.entities.values()
    ]
    
    links = [
        {
            "source": r.source_id,
            "target": r.target_id,
            "type": r.type,
            "value": r.weight
        }
        for r in kg.relationships.values()
    ]
    
    return {
        "nodes": nodes,
        "links": links
    }
