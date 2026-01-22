"""
AI Memory & Personalization API Endpoints
Premium memory system with user preferences and learning

Features:
- User profile management
- Preference learning
- Conversation memory
- Writing style adaptation
- Context personalization
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/memory", tags=["AI Memory & Personalization"])


# =============================================================================
# MODELS
# =============================================================================

class UserProfileCreate(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    name: Optional[str] = None
    profession: Optional[str] = None
    expertise_level: Optional[str] = "intermediate"
    interests: List[str] = Field(default_factory=list)
    preferred_language: str = "auto"
    timezone: Optional[str] = None


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    profession: Optional[str] = None
    expertise_level: Optional[str] = None
    interests: Optional[List[str]] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class PreferenceUpdate(BaseModel):
    category: str = Field(..., description="Preference category (response_style, communication, topics)")
    preferences: Dict[str, Any] = Field(..., description="Preference key-value pairs")


class MemoryEntry(BaseModel):
    content: str = Field(..., description="Memory content to store")
    memory_type: str = Field(default="fact", description="Type: fact, preference, context, episode")
    importance: float = Field(default=0.5, ge=0, le=1, description="Importance score 0-1")
    tags: List[str] = Field(default_factory=list)
    expires_at: Optional[str] = None


class ConversationContext(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="Conversation messages")
    extract_preferences: bool = Field(default=True)
    update_memory: bool = Field(default=True)


class WritingStyleSample(BaseModel):
    text: str = Field(..., description="Sample text to analyze")
    context: Optional[str] = None


class PersonalizedPromptRequest(BaseModel):
    base_prompt: str = Field(..., description="Base prompt to personalize")
    include_preferences: bool = True
    include_context: bool = True
    include_memory: bool = True


# =============================================================================
# ENDPOINTS
# =============================================================================

# User Profile Management
@router.post("/profiles", summary="Create user profile")
async def create_profile(profile: UserProfileCreate):
    """Create a new user profile for personalization"""
    try:
        from core.user_memory import user_memory_engine
        
        result = await user_memory_engine.create_user_profile(
            user_id=profile.user_id,
            name=profile.name,
            profession=profile.profession,
            expertise_level=profile.expertise_level,
            interests=profile.interests,
            preferred_language=profile.preferred_language,
            timezone=profile.timezone
        )
        
        return {
            "success": True,
            "profile": result.to_dict(),
            "message": "Profile created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{user_id}", summary="Get user profile")
async def get_profile(user_id: str):
    """Get user profile by ID"""
    try:
        from core.user_memory import user_memory_engine
        
        profile = user_memory_engine.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "profile": profile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/profiles/{user_id}", summary="Update user profile")
async def update_profile(user_id: str, updates: UserProfileUpdate):
    """Update user profile"""
    try:
        from core.user_memory import user_memory_engine
        
        result = await user_memory_engine.update_user_profile(
            user_id=user_id,
            updates=updates.dict(exclude_none=True)
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "profile": result.to_dict(),
            "message": "Profile updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{user_id}", summary="Delete user profile")
async def delete_profile(user_id: str, delete_all_data: bool = Query(False)):
    """Delete user profile and optionally all associated data"""
    try:
        from core.user_memory import user_memory_engine
        
        success = await user_memory_engine.delete_user_profile(
            user_id=user_id,
            delete_all_data=delete_all_data
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "message": "Profile deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Preferences
@router.post("/profiles/{user_id}/preferences", summary="Update preferences")
async def update_preferences(user_id: str, update: PreferenceUpdate):
    """Update user preferences for a specific category"""
    try:
        from core.user_memory import user_memory_engine
        
        result = await user_memory_engine.update_preferences(
            user_id=user_id,
            category=update.category,
            preferences=update.preferences
        )
        
        return {
            "success": True,
            "preferences": result,
            "message": f"{update.category} preferences updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{user_id}/preferences", summary="Get all preferences")
async def get_preferences(user_id: str, category: Optional[str] = None):
    """Get user preferences, optionally filtered by category"""
    try:
        from core.user_memory import user_memory_engine
        
        preferences = user_memory_engine.get_preferences(user_id, category)
        
        return {
            "success": True,
            "user_id": user_id,
            "category": category,
            "preferences": preferences
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Memory Management
@router.post("/profiles/{user_id}/memories", summary="Add memory")
async def add_memory(user_id: str, entry: MemoryEntry):
    """Add a memory entry for the user"""
    try:
        from core.user_memory import user_memory_engine
        
        memory_id = await user_memory_engine.add_memory(
            user_id=user_id,
            content=entry.content,
            memory_type=entry.memory_type,
            importance=entry.importance,
            tags=entry.tags,
            expires_at=entry.expires_at
        )
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory added"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{user_id}/memories", summary="Get memories")
async def get_memories(
    user_id: str,
    memory_type: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get user memories with optional filters"""
    try:
        from core.user_memory import user_memory_engine
        
        tag_list = tags.split(",") if tags else None
        
        memories = user_memory_engine.get_memories(
            user_id=user_id,
            memory_type=memory_type,
            tags=tag_list,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "count": len(memories),
            "memories": memories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{user_id}/memories/search", summary="Search memories")
async def search_memories(
    user_id: str,
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Semantic search through user memories"""
    try:
        from core.user_memory import user_memory_engine
        
        results = await user_memory_engine.search_memories(
            user_id=user_id,
            query=query,
            limit=limit
        )
        
        return {
            "success": True,
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{user_id}/memories/{memory_id}", summary="Delete memory")
async def delete_memory(user_id: str, memory_id: str):
    """Delete a specific memory"""
    try:
        from core.user_memory import user_memory_engine
        
        success = await user_memory_engine.delete_memory(user_id, memory_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {
            "success": True,
            "message": "Memory deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Learning & Adaptation
@router.post("/profiles/{user_id}/learn/conversation", summary="Learn from conversation")
async def learn_from_conversation(user_id: str, context: ConversationContext, background_tasks: BackgroundTasks):
    """Extract preferences and patterns from a conversation"""
    try:
        from core.user_memory import user_memory_engine
        
        # Process in background for long conversations
        if len(context.messages) > 10:
            background_tasks.add_task(
                user_memory_engine.learn_from_conversation,
                user_id,
                context.messages,
                context.extract_preferences,
                context.update_memory
            )
            return {
                "success": True,
                "status": "processing",
                "message": "Learning from conversation in background"
            }
        
        result = await user_memory_engine.learn_from_conversation(
            user_id=user_id,
            messages=context.messages,
            extract_preferences=context.extract_preferences,
            update_memory=context.update_memory
        )
        
        return {
            "success": True,
            "learned": result,
            "message": "Conversation analyzed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{user_id}/learn/writing-style", summary="Learn writing style")
async def learn_writing_style(user_id: str, sample: WritingStyleSample):
    """Analyze and learn user's writing style"""
    try:
        from core.user_memory import user_memory_engine
        
        result = await user_memory_engine.analyze_writing_style(
            user_id=user_id,
            text=sample.text,
            context=sample.context
        )
        
        return {
            "success": True,
            "analysis": result,
            "message": "Writing style analyzed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{user_id}/writing-style", summary="Get writing style profile")
async def get_writing_style(user_id: str):
    """Get user's learned writing style profile"""
    try:
        from core.user_memory import user_memory_engine
        
        style = user_memory_engine.get_writing_style(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "writing_style": style
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Personalization
@router.post("/profiles/{user_id}/personalize-prompt", summary="Personalize prompt")
async def personalize_prompt(user_id: str, request: PersonalizedPromptRequest):
    """Generate a personalized prompt based on user profile and preferences"""
    try:
        from core.user_memory import user_memory_engine
        
        result = await user_memory_engine.personalize_prompt(
            user_id=user_id,
            base_prompt=request.base_prompt,
            include_preferences=request.include_preferences,
            include_context=request.include_context,
            include_memory=request.include_memory
        )
        
        return {
            "success": True,
            "original_prompt": request.base_prompt,
            "personalized_prompt": result["prompt"],
            "context_added": result.get("context_added", []),
            "preferences_applied": result.get("preferences_applied", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{user_id}/context", summary="Get personalization context")
async def get_personalization_context(user_id: str):
    """Get full personalization context for a user"""
    try:
        from core.user_memory import user_memory_engine
        
        context = user_memory_engine.get_personalization_context(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "context": context
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Statistics & Insights
@router.get("/profiles/{user_id}/stats", summary="Get memory statistics")
async def get_memory_stats(user_id: str):
    """Get memory and usage statistics for a user"""
    try:
        from core.user_memory import user_memory_engine
        
        stats = user_memory_engine.get_user_stats(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{user_id}/consolidate", summary="Consolidate memories")
async def consolidate_memories(user_id: str, background_tasks: BackgroundTasks):
    """Consolidate and optimize user memories (merge duplicates, decay old memories)"""
    try:
        from core.user_memory import user_memory_engine
        
        background_tasks.add_task(
            user_memory_engine.consolidate_memories,
            user_id
        )
        
        return {
            "success": True,
            "status": "processing",
            "message": "Memory consolidation started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# System-wide endpoints
@router.get("/stats", summary="Get system memory statistics")
async def get_system_stats():
    """Get overall memory system statistics"""
    try:
        from core.user_memory import user_memory_engine
        
        stats = user_memory_engine.get_system_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Memory system health check")
async def health_check():
    """Check memory system health"""
    try:
        from core.user_memory import user_memory_engine
        
        health = user_memory_engine.health_check()
        
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
