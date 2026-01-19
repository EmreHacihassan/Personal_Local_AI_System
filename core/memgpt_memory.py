"""
🧠 MemGPT-Style Tiered Memory System
====================================

Hierarchical memory system inspired by MemGPT:
- Core memory (always in context, editable)
- Working memory (active conversation)
- Archival memory (long-term, searchable)
- Recall memory (episodic, time-based)

Features:
- Automatic memory management
- Memory consolidation
- Context window optimization
- Memory editing capabilities
- Persistence across sessions
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class MemoryType(str, Enum):
    """Memory tier types"""
    CORE = "core"  # Always in context
    WORKING = "working"  # Current conversation
    ARCHIVAL = "archival"  # Long-term storage
    RECALL = "recall"  # Episodic memories


class MemoryPriority(str, Enum):
    """Memory importance levels"""
    CRITICAL = "critical"  # Never forget
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TEMPORARY = "temporary"  # Can be discarded


# ============ MEMORY MODELS ============

class MemoryBlock(BaseModel):
    """A single memory block"""
    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority = MemoryPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    token_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def touch(self):
        """Update access time and count"""
        self.accessed_at = datetime.now()
        self.access_count += 1


class CoreMemory(BaseModel):
    """
    Core memory - always present in context.
    Contains persona and user information.
    """
    persona: str = Field(
        default="You are a helpful AI assistant.",
        description="AI persona/system prompt"
    )
    human: str = Field(
        default="The user is interacting with you.",
        description="Information about the user"
    )
    system_facts: List[str] = Field(
        default_factory=list,
        description="Important system facts"
    )
    user_facts: List[str] = Field(
        default_factory=list,
        description="Known facts about user"
    )
    custom_sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom memory sections"
    )
    
    def to_prompt(self) -> str:
        """Convert core memory to prompt format"""
        sections = []
        
        sections.append(f"<persona>\n{self.persona}\n</persona>")
        sections.append(f"<human>\n{self.human}\n</human>")
        
        if self.system_facts:
            facts = "\n".join(f"- {f}" for f in self.system_facts)
            sections.append(f"<system_facts>\n{facts}\n</system_facts>")
        
        if self.user_facts:
            facts = "\n".join(f"- {f}" for f in self.user_facts)
            sections.append(f"<user_facts>\n{facts}\n</user_facts>")
        
        for name, content in self.custom_sections.items():
            sections.append(f"<{name}>\n{content}\n</{name}>")
        
        return "\n\n".join(sections)
    
    def update_section(self, section: str, content: str):
        """Update a memory section"""
        if section == "persona":
            self.persona = content
        elif section == "human":
            self.human = content
        else:
            self.custom_sections[section] = content


class ConversationMessage(BaseModel):
    """A message in working memory"""
    role: str  # user, assistant, system, function
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: int = 0


class ArchivalEntry(BaseModel):
    """An entry in archival memory"""
    id: str
    content: str
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    source: str = "conversation"  # conversation, user, system
    importance: float = 0.5
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecallEntry(BaseModel):
    """An episodic memory entry"""
    id: str
    event_type: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.now)
    participants: List[str] = Field(default_factory=list)
    emotions: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    importance: float = 0.5


# ============ MEMORY STORAGE ============

class MemoryStorage(ABC):
    """Abstract memory storage backend"""
    
    @abstractmethod
    async def save_memory(self, memory: MemoryBlock):
        pass
    
    @abstractmethod
    async def load_memory(self, memory_id: str) -> Optional[MemoryBlock]:
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryBlock]:
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str):
        pass


class SQLiteMemoryStorage(MemoryStorage):
    """SQLite-based memory storage"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                accessed_at TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                token_count INTEGER DEFAULT 0,
                metadata TEXT,
                embedding BLOB
            );
            
            CREATE TABLE IF NOT EXISTS core_memory (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                persona TEXT,
                human TEXT,
                system_facts TEXT,
                user_facts TEXT,
                custom_sections TEXT,
                updated_at TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS archival_memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                summary TEXT,
                created_at TIMESTAMP,
                source TEXT,
                importance REAL DEFAULT 0.5,
                embedding BLOB,
                tags TEXT,
                metadata TEXT
            );
            
            CREATE TABLE IF NOT EXISTS recall_memory (
                id TEXT PRIMARY KEY,
                event_type TEXT,
                description TEXT,
                timestamp TIMESTAMP,
                participants TEXT,
                emotions TEXT,
                context TEXT,
                importance REAL DEFAULT 0.5
            );
            
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memories_priority ON memories(priority);
            CREATE INDEX IF NOT EXISTS idx_archival_importance ON archival_memory(importance);
            CREATE INDEX IF NOT EXISTS idx_recall_timestamp ON recall_memory(timestamp);
        """)
        
        conn.commit()
        conn.close()
    
    def _get_conn(self):
        return sqlite3.connect(str(self.db_path))
    
    async def save_memory(self, memory: MemoryBlock):
        """Save a memory block"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        embedding_blob = None
        if memory.embedding:
            embedding_blob = json.dumps(memory.embedding).encode()
        
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, content, memory_type, priority, created_at, updated_at, accessed_at, 
             access_count, token_count, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.id, memory.content, memory.memory_type.value, memory.priority.value,
            memory.created_at.isoformat(), memory.updated_at.isoformat(),
            memory.accessed_at.isoformat(), memory.access_count, memory.token_count,
            json.dumps(memory.metadata), embedding_blob
        ))
        
        conn.commit()
        conn.close()
    
    async def load_memory(self, memory_id: str) -> Optional[MemoryBlock]:
        """Load a memory block"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        embedding = None
        if row[10]:
            embedding = json.loads(row[10].decode())
        
        return MemoryBlock(
            id=row[0],
            content=row[1],
            memory_type=MemoryType(row[2]),
            priority=MemoryPriority(row[3]),
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
            accessed_at=datetime.fromisoformat(row[6]),
            access_count=row[7],
            token_count=row[8],
            metadata=json.loads(row[9]) if row[9] else {},
            embedding=embedding
        )
    
    async def search_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryBlock]:
        """Search memories by content"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if memory_type:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE memory_type = ? AND content LIKE ?
                ORDER BY accessed_at DESC
                LIMIT ?
            """, (memory_type.value, f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM memories 
                WHERE content LIKE ?
                ORDER BY accessed_at DESC
                LIMIT ?
            """, (f"%{query}%", limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        memories = []
        for row in rows:
            embedding = None
            if row[10]:
                embedding = json.loads(row[10].decode())
            
            memories.append(MemoryBlock(
                id=row[0],
                content=row[1],
                memory_type=MemoryType(row[2]),
                priority=MemoryPriority(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
                accessed_at=datetime.fromisoformat(row[6]),
                access_count=row[7],
                token_count=row[8],
                metadata=json.loads(row[9]) if row[9] else {},
                embedding=embedding
            ))
        
        return memories
    
    async def delete_memory(self, memory_id: str):
        """Delete a memory"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()


# ============ TIERED MEMORY MANAGER ============

class TieredMemoryManager:
    """
    MemGPT-style tiered memory manager.
    
    Manages four memory tiers:
    1. Core Memory: Always in context (persona, user info)
    2. Working Memory: Current conversation messages
    3. Archival Memory: Long-term searchable storage
    4. Recall Memory: Episodic memories of events
    """
    
    def __init__(
        self,
        storage: MemoryStorage,
        max_working_messages: int = 20,
        max_context_tokens: int = 4000,
        embedding_fn: Optional[Callable[[str], List[float]]] = None
    ):
        self.storage = storage
        self.max_working_messages = max_working_messages
        self.max_context_tokens = max_context_tokens
        self.embedding_fn = embedding_fn
        
        # In-memory caches
        self.core_memory = CoreMemory()
        self.working_memory: List[ConversationMessage] = []
        self._archival_cache: Dict[str, ArchivalEntry] = {}
        self._recall_cache: Dict[str, RecallEntry] = {}
    
    # ============ CORE MEMORY ============
    
    async def load_core_memory(self, user_id: str = "default"):
        """Load core memory from storage"""
        # In production, load from database
        pass
    
    async def save_core_memory(self, user_id: str = "default"):
        """Save core memory to storage"""
        # In production, save to database
        pass
    
    def update_core_memory(self, section: str, content: str):
        """Update a section of core memory"""
        self.core_memory.update_section(section, content)
        logger.info(f"Core memory updated: {section}")
    
    def add_user_fact(self, fact: str):
        """Add a fact about the user"""
        if fact not in self.core_memory.user_facts:
            self.core_memory.user_facts.append(fact)
            logger.info(f"User fact added: {fact}")
    
    def add_system_fact(self, fact: str):
        """Add a system fact"""
        if fact not in self.core_memory.system_facts:
            self.core_memory.system_facts.append(fact)
    
    # ============ WORKING MEMORY ============
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add a message to working memory"""
        msg = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
            token_count=len(content) // 4  # Rough estimate
        )
        self.working_memory.append(msg)
        
        # Trim if needed
        self._trim_working_memory()
    
    def get_conversation_context(self) -> str:
        """Get working memory as conversation string"""
        lines = []
        for msg in self.working_memory:
            lines.append(f"{msg.role.upper()}: {msg.content}")
        return "\n\n".join(lines)
    
    def _trim_working_memory(self):
        """Trim working memory to fit constraints"""
        # By message count
        while len(self.working_memory) > self.max_working_messages:
            # Archive oldest non-system message before removing
            oldest = self.working_memory.pop(0)
            if oldest.role != "system":
                asyncio.create_task(self._archive_message(oldest))
        
        # By token count
        total_tokens = sum(m.token_count for m in self.working_memory)
        while total_tokens > self.max_context_tokens and len(self.working_memory) > 2:
            oldest = self.working_memory.pop(0)
            total_tokens -= oldest.token_count
            if oldest.role != "system":
                asyncio.create_task(self._archive_message(oldest))
    
    async def _archive_message(self, message: ConversationMessage):
        """Archive a message to archival memory"""
        entry_id = hashlib.md5(
            f"{message.content}{message.timestamp}".encode()
        ).hexdigest()[:12]
        
        entry = ArchivalEntry(
            id=entry_id,
            content=f"[{message.role}] {message.content}",
            source="conversation",
            importance=0.3
        )
        
        await self.add_to_archival(entry)
    
    # ============ ARCHIVAL MEMORY ============
    
    async def add_to_archival(
        self,
        entry: ArchivalEntry,
        generate_embedding: bool = True
    ):
        """Add entry to archival memory"""
        if generate_embedding and self.embedding_fn:
            try:
                entry.embedding = self.embedding_fn(entry.content)
            except Exception as e:
                logger.warning(f"Embedding generation failed: {e}")
        
        self._archival_cache[entry.id] = entry
        
        # Save as memory block
        block = MemoryBlock(
            id=entry.id,
            content=entry.content,
            memory_type=MemoryType.ARCHIVAL,
            priority=self._importance_to_priority(entry.importance),
            metadata={
                "summary": entry.summary,
                "source": entry.source,
                "tags": entry.tags,
                **entry.metadata
            },
            embedding=entry.embedding
        )
        await self.storage.save_memory(block)
    
    async def search_archival(
        self,
        query: str,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[ArchivalEntry]:
        """Search archival memory"""
        memories = await self.storage.search_memories(
            query=query,
            memory_type=MemoryType.ARCHIVAL,
            limit=limit * 2  # Get more for filtering
        )
        
        results = []
        for mem in memories:
            importance = mem.metadata.get("importance", 0.5)
            if importance >= min_importance:
                entry = ArchivalEntry(
                    id=mem.id,
                    content=mem.content,
                    summary=mem.metadata.get("summary"),
                    created_at=mem.created_at,
                    source=mem.metadata.get("source", "unknown"),
                    importance=importance,
                    tags=mem.metadata.get("tags", []),
                    metadata=mem.metadata
                )
                results.append(entry)
        
        return results[:limit]
    
    # ============ RECALL MEMORY ============
    
    async def add_recall(self, entry: RecallEntry):
        """Add entry to recall memory"""
        self._recall_cache[entry.id] = entry
        
        block = MemoryBlock(
            id=entry.id,
            content=entry.description,
            memory_type=MemoryType.RECALL,
            priority=self._importance_to_priority(entry.importance),
            metadata={
                "event_type": entry.event_type,
                "participants": entry.participants,
                "emotions": entry.emotions,
                "context": entry.context
            }
        )
        await self.storage.save_memory(block)
    
    async def recall_by_time(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 10
    ) -> List[RecallEntry]:
        """Recall memories by time range"""
        # In production, query database with time filters
        results = []
        for entry in self._recall_cache.values():
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            results.append(entry)
        
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]
    
    async def recall_by_type(
        self,
        event_type: str,
        limit: int = 10
    ) -> List[RecallEntry]:
        """Recall memories by event type"""
        results = [
            e for e in self._recall_cache.values()
            if e.event_type == event_type
        ]
        results.sort(key=lambda e: e.importance, reverse=True)
        return results[:limit]
    
    # ============ CONTEXT BUILDING ============
    
    def build_context(
        self,
        include_archival_search: Optional[str] = None,
        archival_limit: int = 3
    ) -> str:
        """
        Build complete context from all memory tiers.
        
        Returns prompt-ready context string.
        """
        sections = []
        
        # 1. Core memory (always included)
        sections.append("=== CORE MEMORY ===")
        sections.append(self.core_memory.to_prompt())
        
        # 2. Archival memory (if search query provided)
        if include_archival_search:
            archival_results = asyncio.run(
                self.search_archival(include_archival_search, limit=archival_limit)
            )
            if archival_results:
                sections.append("\n=== RELEVANT MEMORIES ===")
                for entry in archival_results:
                    sections.append(f"[{entry.created_at.strftime('%Y-%m-%d')}] {entry.content}")
        
        # 3. Working memory (conversation)
        sections.append("\n=== CONVERSATION ===")
        sections.append(self.get_conversation_context())
        
        return "\n".join(sections)
    
    # ============ MEMORY CONSOLIDATION ============
    
    async def consolidate_memories(
        self,
        summarizer: Optional[Callable[[str], str]] = None
    ):
        """
        Consolidate and compress memories.
        
        - Summarize old working memory
        - Merge similar archival entries
        - Decay importance of old memories
        """
        logger.info("Starting memory consolidation...")
        consolidated_count = 0
        decayed_count = 0
        
        # 1. Decay importance of archival memories
        for entry_id, entry in self._archival_cache.items():
            age_days = (datetime.now() - entry.created_at).days
            if age_days > 30:
                old_importance = entry.importance
                entry.importance *= 0.95  # Gradual decay
                decayed_count += 1
                logger.debug(f"Decayed memory {entry_id}: {old_importance:.2f} -> {entry.importance:.2f}")
        
        # 2. Find and merge similar entries
        if len(self._archival_cache) > 10:
            entries = list(self._archival_cache.values())
            merged_ids = set()
            
            for i, entry1 in enumerate(entries):
                if entry1.id in merged_ids:
                    continue
                
                similar_entries = []
                for j, entry2 in enumerate(entries[i+1:], i+1):
                    if entry2.id in merged_ids:
                        continue
                    
                    # Calculate similarity using simple word overlap
                    similarity = self._calculate_text_similarity(
                        entry1.content, entry2.content
                    )
                    
                    if similarity > 0.7:  # High similarity threshold
                        similar_entries.append(entry2)
                        merged_ids.add(entry2.id)
                
                # Merge similar entries into one
                if similar_entries and summarizer:
                    all_contents = [entry1.content] + [e.content for e in similar_entries]
                    combined = "\n---\n".join(all_contents)
                    
                    try:
                        # Summarize combined content
                        summary = summarizer(combined)
                        
                        # Update entry1 with merged content
                        entry1.content = summary
                        entry1.importance = max(entry1.importance, *[e.importance for e in similar_entries])
                        entry1.tags = list(set(entry1.tags + [tag for e in similar_entries for tag in e.tags]))
                        
                        # Remove merged entries from cache
                        for e in similar_entries:
                            if e.id in self._archival_cache:
                                del self._archival_cache[e.id]
                                await self.storage.delete_memory(e.id)
                        
                        consolidated_count += len(similar_entries)
                        logger.info(f"Merged {len(similar_entries) + 1} similar memories into one")
                    except Exception as e:
                        logger.warning(f"Summarization failed: {e}")
        
        # 3. Remove very low importance memories (cleanup)
        to_remove = []
        for entry_id, entry in self._archival_cache.items():
            if entry.importance < 0.1:  # Very low importance
                to_remove.append(entry_id)
        
        for entry_id in to_remove:
            del self._archival_cache[entry_id]
            await self.storage.delete_memory(entry_id)
            logger.debug(f"Removed low-importance memory: {entry_id}")
        
        logger.info(f"Memory consolidation complete: {consolidated_count} merged, {decayed_count} decayed, {len(to_remove)} removed")
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using word overlap (Jaccard similarity).
        For production, use embedding-based similarity.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    # ============ UTILITIES ============
    
    def _importance_to_priority(self, importance: float) -> MemoryPriority:
        """Convert importance score to priority"""
        if importance >= 0.9:
            return MemoryPriority.CRITICAL
        elif importance >= 0.7:
            return MemoryPriority.HIGH
        elif importance >= 0.4:
            return MemoryPriority.MEDIUM
        elif importance >= 0.2:
            return MemoryPriority.LOW
        else:
            return MemoryPriority.TEMPORARY
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "core_memory": {
                "persona_length": len(self.core_memory.persona),
                "human_length": len(self.core_memory.human),
                "system_facts": len(self.core_memory.system_facts),
                "user_facts": len(self.core_memory.user_facts),
                "custom_sections": len(self.core_memory.custom_sections)
            },
            "working_memory": {
                "message_count": len(self.working_memory),
                "total_tokens": sum(m.token_count for m in self.working_memory)
            },
            "archival_memory": {
                "cached_entries": len(self._archival_cache)
            },
            "recall_memory": {
                "cached_entries": len(self._recall_cache)
            }
        }


# ============ MEMORY-ENABLED AGENT ============

class MemoryEnabledAgent:
    """
    Agent with full MemGPT-style memory capabilities.
    
    Can:
    - Read and update core memory
    - Search archival memory
    - Recall episodic events
    - Manage context window
    """
    
    def __init__(
        self,
        memory_manager: TieredMemoryManager,
        llm: Callable[[str], str],
        max_context_tokens: int = 4000
    ):
        self.memory = memory_manager
        self.llm = llm
        self.max_context_tokens = max_context_tokens
    
    async def process_message(
        self,
        user_message: str,
        extract_facts: bool = True
    ) -> str:
        """Process a user message with full memory context"""
        # 1. Add message to working memory
        self.memory.add_message("user", user_message)
        
        # 2. Build context with archival search
        context = self.memory.build_context(
            include_archival_search=user_message[:100]
        )
        
        # 3. Generate response
        prompt = f"{context}\n\nUSER: {user_message}\n\nASSISTANT:"
        response = self.llm(prompt)
        
        # 4. Add response to working memory
        self.memory.add_message("assistant", response)
        
        # 5. Extract and store facts if enabled
        if extract_facts:
            await self._extract_facts(user_message, response)
        
        return response
    
    async def _extract_facts(self, user_message: str, response: str):
        """Extract facts to store in memory"""
        # Simple heuristic extraction
        # In production, use LLM for extraction
        
        # Look for user preferences
        preference_patterns = [
            r"i (?:like|love|prefer|enjoy) (.+)",
            r"my (?:name|favorite|hobby) is (.+)",
            r"i am (?:from|interested in|working on) (.+)"
        ]
        
        import re
        for pattern in preference_patterns:
            matches = re.findall(pattern, user_message.lower())
            for match in matches:
                self.memory.add_user_fact(f"User {match}")
    
    async def memory_command(self, command: str, args: Dict[str, Any]) -> str:
        """
        Execute memory commands (for function calling).
        
        Commands:
        - core_memory_append: Add to core memory section
        - core_memory_replace: Replace core memory section
        - archival_memory_insert: Add to archival memory
        - archival_memory_search: Search archival memory
        - recall_memory_search: Search recall memory
        """
        if command == "core_memory_append":
            section = args.get("section", "human")
            content = args.get("content", "")
            current = getattr(self.memory.core_memory, section, "")
            self.memory.update_core_memory(section, f"{current}\n{content}")
            return f"Appended to {section}"
        
        elif command == "core_memory_replace":
            section = args.get("section", "human")
            content = args.get("content", "")
            self.memory.update_core_memory(section, content)
            return f"Replaced {section}"
        
        elif command == "archival_memory_insert":
            content = args.get("content", "")
            entry_id = hashlib.md5(content.encode()).hexdigest()[:12]
            entry = ArchivalEntry(
                id=entry_id,
                content=content,
                source="agent_command",
                importance=args.get("importance", 0.5)
            )
            await self.memory.add_to_archival(entry)
            return f"Inserted to archival memory: {entry_id}"
        
        elif command == "archival_memory_search":
            query = args.get("query", "")
            results = await self.memory.search_archival(query)
            return json.dumps([
                {"id": r.id, "content": r.content[:200]}
                for r in results
            ], indent=2)
        
        elif command == "recall_memory_search":
            event_type = args.get("event_type")
            if event_type:
                results = await self.memory.recall_by_type(event_type)
            else:
                results = await self.memory.recall_by_time()
            return json.dumps([
                {"id": r.id, "event_type": r.event_type, "description": r.description}
                for r in results
            ], indent=2)
        
        return "Unknown command"


# ============ FACTORY ============

def create_memory_manager(
    data_dir: Path,
    max_working_messages: int = 20,
    max_context_tokens: int = 4000
) -> TieredMemoryManager:
    """Create a configured memory manager"""
    db_path = data_dir / "memory" / "memory.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    storage = SQLiteMemoryStorage(db_path)
    
    return TieredMemoryManager(
        storage=storage,
        max_working_messages=max_working_messages,
        max_context_tokens=max_context_tokens
    )


# ============ EXPORTS ============

__all__ = [
    # Types
    "MemoryType",
    "MemoryPriority",
    # Models
    "MemoryBlock",
    "CoreMemory",
    "ConversationMessage",
    "ArchivalEntry",
    "RecallEntry",
    # Storage
    "MemoryStorage",
    "SQLiteMemoryStorage",
    # Manager
    "TieredMemoryManager",
    "MemoryEnabledAgent",
    # Factory
    "create_memory_manager",
]
