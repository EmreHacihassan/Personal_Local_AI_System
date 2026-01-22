"""
AI Memory & Personalization Engine
===================================
Long-term user memory, preference learning, and personalized AI experience
100% Local Processing - Complete Privacy

Features:
- User Profile Management (preferences, skills, interests)
- Conversation Memory (semantic storage of past interactions)
- Writing Style Learning (adapts to user's communication style)
- Context Persistence (remembers across sessions)
- Preference Evolution (learns and updates over time)
- Smart Recall (retrieves relevant memories contextually)
- Privacy-First Design (all data stays local)

Enterprise-grade implementation with full personalization capabilities.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class MemoryType(str, Enum):
    """Types of memories stored"""
    CONVERSATION = "conversation"       # Chat history
    PREFERENCE = "preference"           # User preferences
    FACT = "fact"                       # Facts about user
    SKILL = "skill"                     # User skills/expertise
    PROJECT = "project"                 # Project context
    RELATIONSHIP = "relationship"       # Entity relationships
    CORRECTION = "correction"           # User corrections to AI
    FEEDBACK = "feedback"               # Explicit user feedback
    PATTERN = "pattern"                 # Detected usage patterns


class ImportanceLevel(str, Enum):
    """Memory importance for retrieval prioritization"""
    CRITICAL = "critical"       # Always remember (e.g., name, profession)
    HIGH = "high"               # Very important facts
    MEDIUM = "medium"           # Contextually important
    LOW = "low"                 # Nice to have
    TEMPORARY = "temporary"     # Short-term only


class CommunicationStyle(str, Enum):
    """User's preferred communication style"""
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    SIMPLE = "simple"
    DETAILED = "detailed"
    CONCISE = "concise"


class ExpertiseLevel(str, Enum):
    """User expertise level in various domains"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class Memory:
    """A single memory unit"""
    id: str
    type: MemoryType
    content: str
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    source: str = ""  # Where this memory came from
    confidence: float = 0.8
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, MemoryType) else self.type,
            "content": self.content,
            "importance": self.importance.value if isinstance(self.importance, ImportanceLevel) else self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count,
            "context": self.context,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=MemoryType(data.get("type", "fact")),
            content=data.get("content", ""),
            importance=ImportanceLevel(data.get("importance", "medium")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else datetime.now(),
            access_count=data.get("access_count", 0),
            context=data.get("context", {}),
            tags=data.get("tags", []),
            source=data.get("source", ""),
            confidence=data.get("confidence", 0.8),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None
        )


@dataclass
class UserProfile:
    """Complete user profile with preferences and learned information"""
    id: str
    name: Optional[str] = None
    profession: Optional[str] = None
    expertise_areas: Dict[str, ExpertiseLevel] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    
    # Communication preferences
    preferred_language: str = "tr"
    communication_style: CommunicationStyle = CommunicationStyle.CASUAL
    response_length_preference: str = "balanced"  # short, balanced, detailed
    technical_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    
    # Writing style patterns learned from user
    writing_patterns: Dict[str, Any] = field(default_factory=dict)
    vocabulary_preferences: List[str] = field(default_factory=list)
    avoided_terms: List[str] = field(default_factory=list)
    
    # Context
    current_projects: List[Dict[str, Any]] = field(default_factory=list)
    frequently_used_tools: List[str] = field(default_factory=list)
    timezone: str = "Europe/Istanbul"
    
    # Statistics
    total_interactions: int = 0
    first_interaction: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    favorite_topics: Dict[str, int] = field(default_factory=dict)
    
    # Custom preferences
    custom_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "profession": self.profession,
            "expertise_areas": {k: v.value for k, v in self.expertise_areas.items()},
            "interests": self.interests,
            "preferred_language": self.preferred_language,
            "communication_style": self.communication_style.value,
            "response_length_preference": self.response_length_preference,
            "technical_level": self.technical_level.value,
            "writing_patterns": self.writing_patterns,
            "vocabulary_preferences": self.vocabulary_preferences,
            "avoided_terms": self.avoided_terms,
            "current_projects": self.current_projects,
            "frequently_used_tools": self.frequently_used_tools,
            "timezone": self.timezone,
            "total_interactions": self.total_interactions,
            "first_interaction": self.first_interaction.isoformat() if self.first_interaction else None,
            "last_interaction": self.last_interaction.isoformat() if self.last_interaction else None,
            "favorite_topics": self.favorite_topics,
            "custom_preferences": self.custom_preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        profile = cls(id=data.get("id", "default"))
        profile.name = data.get("name")
        profile.profession = data.get("profession")
        profile.expertise_areas = {
            k: ExpertiseLevel(v) for k, v in data.get("expertise_areas", {}).items()
        }
        profile.interests = data.get("interests", [])
        profile.preferred_language = data.get("preferred_language", "tr")
        if data.get("communication_style"):
            profile.communication_style = CommunicationStyle(data["communication_style"])
        profile.response_length_preference = data.get("response_length_preference", "balanced")
        if data.get("technical_level"):
            profile.technical_level = ExpertiseLevel(data["technical_level"])
        profile.writing_patterns = data.get("writing_patterns", {})
        profile.vocabulary_preferences = data.get("vocabulary_preferences", [])
        profile.avoided_terms = data.get("avoided_terms", [])
        profile.current_projects = data.get("current_projects", [])
        profile.frequently_used_tools = data.get("frequently_used_tools", [])
        profile.timezone = data.get("timezone", "Europe/Istanbul")
        profile.total_interactions = data.get("total_interactions", 0)
        if data.get("first_interaction"):
            profile.first_interaction = datetime.fromisoformat(data["first_interaction"])
        if data.get("last_interaction"):
            profile.last_interaction = datetime.fromisoformat(data["last_interaction"])
        profile.favorite_topics = data.get("favorite_topics", {})
        profile.custom_preferences = data.get("custom_preferences", {})
        return profile


@dataclass
class ConversationContext:
    """Context from a conversation for memory extraction"""
    conversation_id: str
    messages: List[Dict[str, str]]
    topic: Optional[str] = None
    entities_mentioned: List[str] = field(default_factory=list)
    key_points: List[str] = field(default_factory=list)
    user_corrections: List[Dict[str, str]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemorySearchResult:
    """Result from memory search"""
    memory: Memory
    relevance_score: float
    match_reason: str


# =============================================================================
# MEMORY ENGINE
# =============================================================================

class MemoryEngine:
    """
    AI Memory & Personalization Engine
    
    Provides long-term memory and personalization for AI interactions.
    All data is stored locally with complete privacy.
    """
    
    def __init__(self, storage_dir: str = "data/memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.storage_dir / "memory.db"
        self.profiles_path = self.storage_dir / "profiles"
        self.profiles_path.mkdir(exist_ok=True)
        
        self._init_database()
        
        # In-memory caches
        self.profiles: Dict[str, UserProfile] = {}
        self.memory_cache: Dict[str, Memory] = {}
        self._load_profiles()
        
        # LLM for memory extraction (lazy loaded)
        self._llm = None
        self._embedding = None
        
        # Patterns for information extraction
        self._fact_patterns = self._compile_fact_patterns()
        
        logger.info(f"MemoryEngine initialized with storage at {self.storage_dir}")
    
    def _init_database(self):
        """Initialize SQLite database for memory storage"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                context TEXT,
                tags TEXT,
                source TEXT,
                confidence REAL DEFAULT 0.8,
                expires_at TEXT,
                embedding BLOB
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON memories(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON memories(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)")
        
        # Conversation summaries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summaries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_topics TEXT,
                extracted_facts TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # User interactions log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _compile_fact_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for fact extraction"""
        return {
            "name": [
                re.compile(r"(?:benim adım|adım|ben)\s+([A-ZÇĞİÖŞÜa-zçğıöşü]+)", re.IGNORECASE),
                re.compile(r"(?:my name is|i'm|i am)\s+([A-Za-z]+)", re.IGNORECASE),
            ],
            "profession": [
                re.compile(r"(?:ben bir|ben)\s+([A-ZÇĞİÖŞÜa-zçğıöşü\s]+(?:mühendis|developer|geliştirici|yazılımcı|tasarımcı|analist|yönetici|öğrenci|öğretmen|doktor|avukat|mimar))", re.IGNORECASE),
                re.compile(r"(?:i'm a|i am a|i work as a?)\s+([A-Za-z\s]+(?:engineer|developer|designer|analyst|manager|student|teacher|doctor|lawyer|architect))", re.IGNORECASE),
            ],
            "expertise": [
                re.compile(r"(?:uzmanım|biliyorum|çalışıyorum)\s+([A-ZÇĞİÖŞÜa-zçğıöşü\s,]+)", re.IGNORECASE),
                re.compile(r"(?:expert in|specialize in|work with)\s+([A-Za-z\s,]+)", re.IGNORECASE),
            ],
            "preference": [
                re.compile(r"(?:tercih ederim|severim|istiyorum)\s+([^.!?]+)", re.IGNORECASE),
                re.compile(r"(?:i prefer|i like|i want)\s+([^.!?]+)", re.IGNORECASE),
            ],
            "project": [
                re.compile(r"(?:proje|çalışıyorum|yapıyorum)\s+([^.!?]+(?:proje|app|uygulama|sistem))", re.IGNORECASE),
                re.compile(r"(?:working on|building|developing)\s+([^.!?]+(?:project|app|application|system))", re.IGNORECASE),
            ],
            "dislike": [
                re.compile(r"(?:sevmiyorum|istemiyorum|hoşlanmıyorum)\s+([^.!?]+)", re.IGNORECASE),
                re.compile(r"(?:don't like|hate|avoid)\s+([^.!?]+)", re.IGNORECASE),
            ]
        }
    
    def _load_profiles(self):
        """Load all user profiles from disk"""
        for profile_file in self.profiles_path.glob("*.json"):
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    profile = UserProfile.from_dict(data)
                    self.profiles[profile.id] = profile
            except Exception as e:
                logger.error(f"Error loading profile {profile_file}: {e}")
        
        # Ensure default profile exists
        if "default" not in self.profiles:
            self.profiles["default"] = UserProfile(id="default")
            self._save_profile("default")
    
    def _save_profile(self, user_id: str):
        """Save a user profile to disk"""
        if user_id not in self.profiles:
            return
        
        profile_path = self.profiles_path / f"{user_id}.json"
        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(self.profiles[user_id].to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving profile {user_id}: {e}")
    
    def _get_llm(self):
        """Lazy load LLM manager"""
        if self._llm is None:
            try:
                from core.llm_manager import llm_manager
                self._llm = llm_manager
            except Exception as e:
                logger.warning(f"Could not load LLM manager: {e}")
        return self._llm
    
    def _get_embedding(self):
        """Lazy load embedding manager"""
        if self._embedding is None:
            try:
                from core.embedding import embedding_manager
                self._embedding = embedding_manager
            except Exception as e:
                logger.warning(f"Could not load embedding manager: {e}")
        return self._embedding
    
    # =========================================================================
    # PROFILE MANAGEMENT
    # =========================================================================
    
    def get_profile(self, user_id: str = "default") -> UserProfile:
        """Get user profile, creating if doesn't exist"""
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(id=user_id)
            self._save_profile(user_id)
        return self.profiles[user_id]
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update user profile with new information"""
        profile = self.get_profile(user_id)
        
        for key, value in updates.items():
            if hasattr(profile, key):
                if key == "communication_style" and isinstance(value, str):
                    value = CommunicationStyle(value)
                elif key == "technical_level" and isinstance(value, str):
                    value = ExpertiseLevel(value)
                setattr(profile, key, value)
        
        profile.last_interaction = datetime.now()
        self._save_profile(user_id)
        
        logger.info(f"Updated profile for user {user_id}: {list(updates.keys())}")
        return profile
    
    def add_expertise(self, user_id: str, domain: str, level: ExpertiseLevel):
        """Add or update user expertise in a domain"""
        profile = self.get_profile(user_id)
        profile.expertise_areas[domain] = level
        self._save_profile(user_id)
        
        # Also create a memory for this
        self.add_memory(
            user_id=user_id,
            content=f"Kullanıcı {domain} alanında {level.value} seviyesinde",
            memory_type=MemoryType.SKILL,
            importance=ImportanceLevel.HIGH,
            tags=["expertise", domain]
        )
    
    def add_interest(self, user_id: str, interest: str):
        """Add a user interest"""
        profile = self.get_profile(user_id)
        if interest not in profile.interests:
            profile.interests.append(interest)
            self._save_profile(user_id)
            
            self.add_memory(
                user_id=user_id,
                content=f"Kullanıcı {interest} ile ilgileniyor",
                memory_type=MemoryType.PREFERENCE,
                importance=ImportanceLevel.MEDIUM,
                tags=["interest", interest]
            )
    
    def add_project(self, user_id: str, project: Dict[str, Any]):
        """Add a current project to user profile"""
        profile = self.get_profile(user_id)
        
        # Check if project already exists
        existing = next((p for p in profile.current_projects if p.get("name") == project.get("name")), None)
        if existing:
            existing.update(project)
        else:
            project["added_at"] = datetime.now().isoformat()
            profile.current_projects.append(project)
        
        self._save_profile(user_id)
        
        # Create memory
        self.add_memory(
            user_id=user_id,
            content=f"Kullanıcı {project.get('name', 'bir proje')} üzerinde çalışıyor: {project.get('description', '')}",
            memory_type=MemoryType.PROJECT,
            importance=ImportanceLevel.HIGH,
            context=project,
            tags=["project", project.get("name", "unnamed")]
        )
    
    def increment_topic_count(self, user_id: str, topic: str):
        """Track favorite topics"""
        profile = self.get_profile(user_id)
        profile.favorite_topics[topic] = profile.favorite_topics.get(topic, 0) + 1
        profile.total_interactions += 1
        profile.last_interaction = datetime.now()
        if not profile.first_interaction:
            profile.first_interaction = datetime.now()
        self._save_profile(user_id)
    
    # =========================================================================
    # MEMORY MANAGEMENT
    # =========================================================================
    
    def add_memory(
        self,
        user_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.FACT,
        importance: ImportanceLevel = ImportanceLevel.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        source: str = "",
        confidence: float = 0.8,
        expires_at: Optional[datetime] = None
    ) -> Memory:
        """Add a new memory"""
        memory_id = str(uuid.uuid4())
        
        memory = Memory(
            id=memory_id,
            type=memory_type,
            content=content,
            importance=importance,
            context=context or {},
            tags=tags or [],
            source=source,
            confidence=confidence,
            expires_at=expires_at
        )
        
        # Get embedding for semantic search
        embedding_manager = self._get_embedding()
        if embedding_manager:
            try:
                embedding = embedding_manager.embed(content)
                memory.embedding = embedding
            except Exception as e:
                logger.warning(f"Could not generate embedding: {e}")
        
        # Store in database
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO memories (id, user_id, type, content, importance, created_at, 
                                  last_accessed, access_count, context, tags, source, 
                                  confidence, expires_at, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.id,
            user_id,
            memory.type.value,
            memory.content,
            memory.importance.value,
            memory.created_at.isoformat(),
            memory.last_accessed.isoformat(),
            memory.access_count,
            json.dumps(memory.context),
            json.dumps(memory.tags),
            memory.source,
            memory.confidence,
            memory.expires_at.isoformat() if memory.expires_at else None,
            json.dumps(memory.embedding) if memory.embedding else None
        ))
        
        conn.commit()
        conn.close()
        
        # Cache
        self.memory_cache[memory_id] = memory
        
        logger.info(f"Added memory for user {user_id}: {content[:50]}...")
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get a specific memory by ID"""
        # Check cache first
        if memory_id in self.memory_cache:
            return self.memory_cache[memory_id]
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_memory(row)
        return None
    
    def _row_to_memory(self, row) -> Memory:
        """Convert database row to Memory object"""
        return Memory(
            id=row[0],
            type=MemoryType(row[2]),
            content=row[3],
            importance=ImportanceLevel(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            last_accessed=datetime.fromisoformat(row[6]),
            access_count=row[7],
            context=json.loads(row[8]) if row[8] else {},
            tags=json.loads(row[9]) if row[9] else [],
            source=row[10],
            confidence=row[11],
            expires_at=datetime.fromisoformat(row[12]) if row[12] else None,
            embedding=json.loads(row[13]) if row[13] else None
        )
    
    def search_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        min_importance: ImportanceLevel = ImportanceLevel.LOW,
        limit: int = 10,
        include_expired: bool = False
    ) -> List[MemorySearchResult]:
        """Search memories with semantic similarity"""
        results = []
        
        # Get query embedding
        embedding_manager = self._get_embedding()
        query_embedding = None
        if embedding_manager:
            try:
                query_embedding = embedding_manager.embed(query)
            except Exception as e:
                logger.warning(f"Could not generate query embedding: {e}")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Build query
        sql = "SELECT * FROM memories WHERE user_id = ?"
        params = [user_id]
        
        if memory_types:
            placeholders = ",".join(["?" for _ in memory_types])
            sql += f" AND type IN ({placeholders})"
            params.extend([mt.value for mt in memory_types])
        
        importance_order = ["temporary", "low", "medium", "high", "critical"]
        min_idx = importance_order.index(min_importance.value)
        allowed_importance = importance_order[min_idx:]
        placeholders = ",".join(["?" for _ in allowed_importance])
        sql += f" AND importance IN ({placeholders})"
        params.extend(allowed_importance)
        
        if not include_expired:
            sql += " AND (expires_at IS NULL OR expires_at > ?)"
            params.append(datetime.now().isoformat())
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Score and rank results
        for row in rows:
            memory = self._row_to_memory(row)
            score = 0.0
            match_reason = []
            
            # Text matching score
            query_lower = query.lower()
            content_lower = memory.content.lower()
            
            if query_lower in content_lower:
                score += 0.5
                match_reason.append("exact match")
            
            # Word overlap
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)
            if overlap > 0:
                score += 0.3 * (overlap / len(query_words))
                match_reason.append(f"{overlap} word overlap")
            
            # Tag matching
            for tag in memory.tags:
                if tag.lower() in query_lower:
                    score += 0.2
                    match_reason.append(f"tag: {tag}")
            
            # Semantic similarity (if embeddings available)
            if query_embedding and memory.embedding:
                try:
                    similarity = self._cosine_similarity(query_embedding, memory.embedding)
                    score += similarity * 0.5
                    if similarity > 0.7:
                        match_reason.append(f"semantic: {similarity:.2f}")
                except:
                    pass
            
            # Importance boost
            importance_boost = {
                ImportanceLevel.CRITICAL: 0.3,
                ImportanceLevel.HIGH: 0.2,
                ImportanceLevel.MEDIUM: 0.1,
                ImportanceLevel.LOW: 0.05,
                ImportanceLevel.TEMPORARY: 0
            }
            score += importance_boost.get(memory.importance, 0)
            
            # Recency boost
            age_days = (datetime.now() - memory.created_at).days
            recency_boost = max(0, 0.1 * (1 - age_days / 365))
            score += recency_boost
            
            if score > 0.1:
                results.append(MemorySearchResult(
                    memory=memory,
                    relevance_score=score,
                    match_reason=", ".join(match_reason) if match_reason else "weak match"
                ))
        
        # Sort by score and limit
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    
    def get_all_memories(
        self,
        user_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[Memory]:
        """Get all memories for a user"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute(
                "SELECT * FROM memories WHERE user_id = ? AND type = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, memory_type.value, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM memories WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_memory(row) for row in rows]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if memory_id in self.memory_cache:
            del self.memory_cache[memory_id]
        
        return deleted
    
    def update_memory_access(self, memory_id: str):
        """Update memory access time and count"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE memories 
            SET last_accessed = ?, access_count = access_count + 1 
            WHERE id = ?
        """, (datetime.now().isoformat(), memory_id))
        conn.commit()
        conn.close()
    
    # =========================================================================
    # CONVERSATION ANALYSIS & MEMORY EXTRACTION
    # =========================================================================
    
    async def process_conversation(
        self,
        user_id: str,
        conversation: ConversationContext
    ) -> Dict[str, Any]:
        """
        Process a conversation to extract and store memories.
        This is the main entry point for learning from conversations.
        """
        extracted = {
            "facts": [],
            "preferences": [],
            "corrections": [],
            "profile_updates": {}
        }
        
        profile = self.get_profile(user_id)
        
        for message in conversation.messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                
                # Extract facts using patterns
                facts = self._extract_facts_from_text(content)
                for fact_type, fact_value in facts:
                    extracted["facts"].append({"type": fact_type, "value": fact_value})
                    
                    # Update profile based on fact type
                    if fact_type == "name" and not profile.name:
                        extracted["profile_updates"]["name"] = fact_value
                    elif fact_type == "profession":
                        extracted["profile_updates"]["profession"] = fact_value
                    
                    # Store as memory
                    self.add_memory(
                        user_id=user_id,
                        content=f"{fact_type}: {fact_value}",
                        memory_type=MemoryType.FACT,
                        importance=ImportanceLevel.HIGH if fact_type in ["name", "profession"] else ImportanceLevel.MEDIUM,
                        tags=[fact_type],
                        source=f"conversation:{conversation.conversation_id}"
                    )
                
                # Detect writing style
                style_analysis = self._analyze_writing_style(content)
                if style_analysis:
                    if "writing_patterns" not in extracted["profile_updates"]:
                        extracted["profile_updates"]["writing_patterns"] = profile.writing_patterns.copy()
                    extracted["profile_updates"]["writing_patterns"].update(style_analysis)
                
                # Detect corrections to AI
                if any(phrase in content.lower() for phrase in ["hayır", "yanlış", "değil", "no", "wrong", "not"]):
                    extracted["corrections"].append({
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.add_memory(
                        user_id=user_id,
                        content=f"Kullanıcı düzeltmesi: {content}",
                        memory_type=MemoryType.CORRECTION,
                        importance=ImportanceLevel.HIGH,
                        source=f"conversation:{conversation.conversation_id}"
                    )
        
        # Apply profile updates
        if extracted["profile_updates"]:
            self.update_profile(user_id, extracted["profile_updates"])
        
        # Store conversation summary if it was meaningful
        if len(conversation.messages) >= 4:
            summary = await self._summarize_conversation(conversation)
            if summary:
                self._store_conversation_summary(user_id, conversation.conversation_id, summary)
        
        # Update topic counts
        if conversation.topic:
            self.increment_topic_count(user_id, conversation.topic)
        
        return extracted
    
    def _extract_facts_from_text(self, text: str) -> List[Tuple[str, str]]:
        """Extract facts from text using patterns"""
        facts = []
        
        for fact_type, patterns in self._fact_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = " ".join(match)
                    match = match.strip()
                    if len(match) > 2:
                        facts.append((fact_type, match))
        
        return facts
    
    def _analyze_writing_style(self, text: str) -> Dict[str, Any]:
        """Analyze writing style patterns"""
        style = {}
        
        words = text.split()
        if len(words) < 5:
            return style
        
        # Average word length
        avg_word_len = sum(len(w) for w in words) / len(words)
        style["avg_word_length"] = avg_word_len
        
        # Sentence count and average length
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            style["avg_sentence_length"] = len(words) / len(sentences)
        
        # Formality indicators
        formal_words = ["lütfen", "rica ederim", "merhaba", "teşekkür", "please", "thank you", "kindly"]
        informal_words = ["ya", "yani", "hani", "abi", "hey", "cool", "ok"]
        
        formal_count = sum(1 for w in text.lower().split() if w in formal_words)
        informal_count = sum(1 for w in text.lower().split() if w in informal_words)
        
        if formal_count > informal_count:
            style["detected_formality"] = "formal"
        elif informal_count > formal_count:
            style["detected_formality"] = "informal"
        
        # Technical language detection
        tech_indicators = ["api", "code", "function", "class", "server", "database", "algorithm"]
        tech_count = sum(1 for word in text.lower().split() if word in tech_indicators)
        if tech_count >= 2:
            style["uses_technical_language"] = True
        
        return style
    
    async def _summarize_conversation(self, conversation: ConversationContext) -> Optional[str]:
        """Use LLM to summarize a conversation"""
        llm = self._get_llm()
        if not llm:
            return None
        
        try:
            messages_text = "\n".join([
                f"{m.get('role', 'unknown')}: {m.get('content', '')}" 
                for m in conversation.messages[-10:]  # Last 10 messages
            ])
            
            prompt = f"""Aşağıdaki konuşmayı özetle ve kullanıcı hakkında öğrenilen önemli bilgileri çıkar.
Sadece gerçekleri ve önemli bilgileri listele.

Konuşma:
{messages_text}

Özet (Türkçe, 2-3 cümle):"""
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: llm.generate(prompt, max_tokens=200)
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return None
    
    def _store_conversation_summary(self, user_id: str, conversation_id: str, summary: str):
        """Store conversation summary"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversation_summaries (id, user_id, conversation_id, summary, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            user_id,
            conversation_id,
            summary,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # PERSONALIZATION
    # =========================================================================
    
    def get_personalization_context(self, user_id: str) -> str:
        """
        Generate a personalization context string for the AI.
        This should be added to the system prompt.
        """
        profile = self.get_profile(user_id)
        
        context_parts = []
        
        if profile.name:
            context_parts.append(f"Kullanıcının adı: {profile.name}")
        
        if profile.profession:
            context_parts.append(f"Mesleği: {profile.profession}")
        
        if profile.expertise_areas:
            areas = [f"{k} ({v.value})" for k, v in profile.expertise_areas.items()]
            context_parts.append(f"Uzmanlık alanları: {', '.join(areas)}")
        
        if profile.interests:
            context_parts.append(f"İlgi alanları: {', '.join(profile.interests[:5])}")
        
        if profile.current_projects:
            projects = [p.get("name", "unnamed") for p in profile.current_projects[:3]]
            context_parts.append(f"Aktif projeler: {', '.join(projects)}")
        
        style_notes = []
        if profile.communication_style == CommunicationStyle.FORMAL:
            style_notes.append("resmi dil kullan")
        elif profile.communication_style == CommunicationStyle.CASUAL:
            style_notes.append("samimi ve rahat bir dil kullan")
        elif profile.communication_style == CommunicationStyle.TECHNICAL:
            style_notes.append("teknik terimler kullanabilirsin")
        
        if profile.response_length_preference == "short":
            style_notes.append("kısa ve öz yanıtlar ver")
        elif profile.response_length_preference == "detailed":
            style_notes.append("detaylı açıklamalar yap")
        
        if style_notes:
            context_parts.append(f"İletişim tercihleri: {', '.join(style_notes)}")
        
        # Get recent relevant memories
        recent_facts = self.get_all_memories(user_id, MemoryType.FACT, limit=5)
        if recent_facts:
            facts_text = "; ".join([m.content for m in recent_facts[:5]])
            context_parts.append(f"Bilinen bilgiler: {facts_text}")
        
        if context_parts:
            return "=== KULLANICI PROFİLİ ===\n" + "\n".join(context_parts) + "\n=== ===\n"
        
        return ""
    
    def get_relevant_memories_for_query(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> str:
        """Get memories relevant to a specific query, formatted for context"""
        results = self.search_memories(user_id, query, limit=limit)
        
        if not results:
            return ""
        
        memory_texts = []
        for result in results:
            memory_texts.append(f"- {result.memory.content} (güven: {result.relevance_score:.2f})")
        
        return "=== İLGİLİ HAFIZA ===\n" + "\n".join(memory_texts) + "\n=== ===\n"
    
    # =========================================================================
    # ANALYTICS & INSIGHTS
    # =========================================================================
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's memories"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Total memories
        cursor.execute("SELECT COUNT(*) FROM memories WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM memories WHERE user_id = ? 
            GROUP BY type
        """, (user_id,))
        by_type = dict(cursor.fetchall())
        
        # By importance
        cursor.execute("""
            SELECT importance, COUNT(*) as count 
            FROM memories WHERE user_id = ? 
            GROUP BY importance
        """, (user_id,))
        by_importance = dict(cursor.fetchall())
        
        # Most accessed
        cursor.execute("""
            SELECT content, access_count 
            FROM memories WHERE user_id = ? 
            ORDER BY access_count DESC LIMIT 5
        """, (user_id,))
        most_accessed = [{"content": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        profile = self.get_profile(user_id)
        
        return {
            "total_memories": total,
            "by_type": by_type,
            "by_importance": by_importance,
            "most_accessed": most_accessed,
            "total_interactions": profile.total_interactions,
            "favorite_topics": dict(sorted(
                profile.favorite_topics.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "profile_completeness": self._calculate_profile_completeness(profile)
        }
    
    def _calculate_profile_completeness(self, profile: UserProfile) -> float:
        """Calculate how complete a user profile is"""
        fields = [
            profile.name is not None,
            profile.profession is not None,
            len(profile.expertise_areas) > 0,
            len(profile.interests) > 0,
            len(profile.current_projects) > 0,
            profile.total_interactions >= 10
        ]
        return sum(fields) / len(fields)
    
    # =========================================================================
    # DATA MANAGEMENT
    # =========================================================================
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for backup or portability"""
        profile = self.get_profile(user_id)
        memories = self.get_all_memories(user_id, limit=10000)
        
        return {
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "profile": profile.to_dict(),
            "memories": [m.to_dict() for m in memories],
            "stats": self.get_memory_stats(user_id)
        }
    
    def import_user_data(self, data: Dict[str, Any]) -> bool:
        """Import user data from backup"""
        try:
            user_id = data.get("user_id", "default")
            
            # Import profile
            if "profile" in data:
                profile = UserProfile.from_dict(data["profile"])
                self.profiles[user_id] = profile
                self._save_profile(user_id)
            
            # Import memories
            for memory_data in data.get("memories", []):
                memory = Memory.from_dict(memory_data)
                self.add_memory(
                    user_id=user_id,
                    content=memory.content,
                    memory_type=memory.type,
                    importance=memory.importance,
                    context=memory.context,
                    tags=memory.tags,
                    source=memory.source,
                    confidence=memory.confidence
                )
            
            return True
        except Exception as e:
            logger.error(f"Error importing user data: {e}")
            return False
    
    def clear_user_data(self, user_id: str) -> bool:
        """Clear all data for a user (privacy feature)"""
        try:
            # Delete memories
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM conversation_summaries WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM interaction_log WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            # Delete profile
            if user_id in self.profiles:
                del self.profiles[user_id]
            
            profile_path = self.profiles_path / f"{user_id}.json"
            if profile_path.exists():
                profile_path.unlink()
            
            logger.info(f"Cleared all data for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing user data: {e}")
            return False


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

memory_engine = MemoryEngine()
