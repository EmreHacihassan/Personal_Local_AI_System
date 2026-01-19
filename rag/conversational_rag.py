"""
Conversational RAG System
=========================

Chat-aware RAG with conversation memory, context tracking,
and intelligent query reformulation.

Features:
- Conversation Memory Management
- Query Reformulation (Anaphora Resolution)
- Topic Tracking & Detection
- Context Window Optimization
- Multi-Turn Understanding
- Follow-up Question Handling
- Conversation Summarization
- Session Persistence

Enterprise-grade implementation for chat applications.

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any,
    Callable,
    Deque,
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

from core.logger import get_logger

logger = get_logger("rag.conversational_rag")


# =============================================================================
# ENUMS
# =============================================================================

class MessageRole(Enum):
    """Mesaj rolü."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    CONTEXT = "context"


class ConversationState(Enum):
    """Konuşma durumu."""
    ACTIVE = "active"
    IDLE = "idle"
    SUMMARIZING = "summarizing"
    CLOSED = "closed"


class QueryType(Enum):
    """Sorgu tipi."""
    NEW_TOPIC = "new_topic"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    REFINEMENT = "refinement"
    REFERENCE = "reference"
    COMPARISON = "comparison"


class TopicState(Enum):
    """Topic durumu."""
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Message:
    """Konuşma mesajı."""
    id: str
    role: MessageRole
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Metadata
    token_count: int = 0
    query_type: Optional[QueryType] = None
    entities: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    
    # RAG context
    retrieved_docs: List[str] = field(default_factory=list)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
            "query_type": self.query_type.value if self.query_type else None,
            "entities": self.entities,
            "topics": self.topics,
            "confidence": self.confidence,
        }
    
    @classmethod
    def user(cls, content: str) -> "Message":
        """Kullanıcı mesajı oluştur."""
        return cls(
            id=str(uuid.uuid4())[:8],
            role=MessageRole.USER,
            content=content,
        )
    
    @classmethod
    def assistant(cls, content: str, confidence: float = 1.0) -> "Message":
        """Asistan mesajı oluştur."""
        return cls(
            id=str(uuid.uuid4())[:8],
            role=MessageRole.ASSISTANT,
            content=content,
            confidence=confidence,
        )


@dataclass
class Topic:
    """Konuşma konusu."""
    id: str
    name: str
    keywords: List[str]
    state: TopicState = TopicState.ACTIVE
    
    # Tracking
    message_count: int = 0
    first_mentioned: str = field(default_factory=lambda: datetime.now().isoformat())
    last_mentioned: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Context
    summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "keywords": self.keywords,
            "state": self.state.value,
            "message_count": self.message_count,
            "summary": self.summary[:200],
        }


@dataclass
class ConversationContext:
    """Konuşma bağlamı."""
    active_topics: List[Topic]
    recent_entities: List[str]
    key_facts: List[str]
    
    # Context window
    context_summary: str = ""
    window_messages: List[Message] = field(default_factory=list)
    
    # Statistics
    total_messages: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "active_topics": [t.to_dict() for t in self.active_topics],
            "recent_entities": self.recent_entities[:10],
            "key_facts": self.key_facts[:5],
            "context_summary": self.context_summary[:300],
            "total_messages": self.total_messages,
        }


@dataclass
class ReformulatedQuery:
    """Reformüle edilmiş sorgu."""
    original_query: str
    reformulated_query: str
    query_type: QueryType
    
    # Resolution
    resolved_references: Dict[str, str] = field(default_factory=dict)
    added_context: List[str] = field(default_factory=list)
    
    # Confidence
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "original": self.original_query,
            "reformulated": self.reformulated_query,
            "type": self.query_type.value,
            "resolved_references": self.resolved_references,
            "confidence": self.confidence,
        }


@dataclass
class ConversationSession:
    """Konuşma oturumu."""
    session_id: str
    user_id: Optional[str] = None
    
    # State
    state: ConversationState = ConversationState.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Messages
    messages: List[Message] = field(default_factory=list)
    
    # Topics & Context
    topics: List[Topic] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    
    # Summary
    conversation_summary: str = ""
    
    # Settings
    max_history_messages: int = 50
    context_window_size: int = 10
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "state": self.state.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "message_count": len(self.messages),
            "topic_count": len(self.topics),
            "summary": self.conversation_summary[:200],
        }


@dataclass
class ConversationalResult:
    """Konuşma RAG sonucu."""
    session_id: str
    query: str
    reformulated_query: str
    response: str
    confidence: float
    
    # Context used
    conversation_context: ConversationContext
    retrieved_documents: List[Any]
    
    # Query analysis
    query_type: QueryType
    resolved_references: Dict[str, str]
    
    # Metrics
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "query": self.query,
            "reformulated_query": self.reformulated_query,
            "response": self.response,
            "confidence": self.confidence,
            "query_type": self.query_type.value,
            "resolved_references": self.resolved_references,
            "processing_time_ms": self.processing_time_ms,
        }


# =============================================================================
# PROTOCOLS
# =============================================================================

class LLMProtocol(Protocol):
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> Any:
        ...


# =============================================================================
# QUERY REFORMULATOR
# =============================================================================

class QueryReformulator:
    """
    Query reformulation for conversational context.
    
    Handles:
    - Anaphora resolution (it, this, that, they)
    - Ellipsis resolution (missing subjects/objects)
    - Topic continuation
    - Reference resolution
    """
    
    # Common pronouns and references
    PRONOUNS = {"it", "this", "that", "they", "them", "these", "those", "he", "she", "its"}
    ELLIPSIS_MARKERS = {"also", "too", "same", "again", "more", "another", "other"}
    FOLLOW_UP_MARKERS = {"what about", "how about", "and", "but", "also", "then", "so"}
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def reformulate(
        self,
        query: str,
        conversation_history: List[Message],
        context: ConversationContext
    ) -> ReformulatedQuery:
        """Sorguyu konuşma bağlamına göre reformüle et."""
        # 1. Detect query type
        query_type = self._detect_query_type(query, conversation_history)
        
        # 2. Check if reformulation needed
        if query_type == QueryType.NEW_TOPIC:
            return ReformulatedQuery(
                original_query=query,
                reformulated_query=query,
                query_type=query_type,
                confidence=1.0,
            )
        
        # 3. Rule-based resolution first
        resolved_query, resolutions = self._rule_based_resolution(
            query, conversation_history, context
        )
        
        # 4. LLM-based resolution if needed
        if self._needs_llm_resolution(resolved_query, resolutions):
            self._lazy_load()
            resolved_query = self._llm_resolution(
                query, conversation_history, context
            )
        
        return ReformulatedQuery(
            original_query=query,
            reformulated_query=resolved_query,
            query_type=query_type,
            resolved_references=resolutions,
            confidence=0.9 if resolutions else 1.0,
        )
    
    def _detect_query_type(
        self,
        query: str,
        history: List[Message]
    ) -> QueryType:
        """Sorgu tipini tespit et."""
        query_lower = query.lower().strip()
        
        # Check for reference patterns
        has_pronouns = any(p in query_lower.split() for p in self.PRONOUNS)
        has_follow_up = any(query_lower.startswith(m) for m in self.FOLLOW_UP_MARKERS)
        has_ellipsis = any(m in query_lower for m in self.ELLIPSIS_MARKERS)
        
        # Very short query suggests follow-up
        is_short = len(query_lower.split()) <= 3
        
        # Question about previous answer
        if any(p in query_lower for p in ["why", "how come", "explain"]) and has_pronouns:
            return QueryType.CLARIFICATION
        
        # Comparison query
        if any(p in query_lower for p in ["compare", "difference", "vs", "versus", "better"]):
            return QueryType.COMPARISON
        
        # Reference to previous content
        if has_pronouns or (is_short and history):
            return QueryType.REFERENCE
        
        # Follow-up
        if has_follow_up or has_ellipsis:
            return QueryType.FOLLOW_UP
        
        # Refinement
        if any(p in query_lower for p in ["more", "less", "instead", "rather"]):
            return QueryType.REFINEMENT
        
        return QueryType.NEW_TOPIC
    
    def _rule_based_resolution(
        self,
        query: str,
        history: List[Message],
        context: ConversationContext
    ) -> Tuple[str, Dict[str, str]]:
        """Kural tabanlı referans çözümleme."""
        resolutions = {}
        resolved_query = query
        
        if not history:
            return query, resolutions
        
        # Get recent context
        recent_messages = history[-6:]  # Last 3 exchanges
        last_user_query = None
        last_assistant_response = None
        
        for msg in reversed(recent_messages):
            if msg.role == MessageRole.USER and last_user_query is None:
                if msg.content != query:
                    last_user_query = msg.content
            elif msg.role == MessageRole.ASSISTANT and last_assistant_response is None:
                last_assistant_response = msg.content
        
        # Extract entities from recent context
        recent_entities = context.recent_entities[:5] if context.recent_entities else []
        active_topics = [t.name for t in context.active_topics[:3]] if context.active_topics else []
        
        # Resolve "it", "this", "that"
        for pronoun in ["it", "this", "that"]:
            if pronoun in query.lower().split():
                # Try to find the most likely referent
                referent = None
                
                if recent_entities:
                    referent = recent_entities[0]
                elif active_topics:
                    referent = active_topics[0]
                elif last_user_query:
                    # Extract main noun from last query
                    words = last_user_query.split()
                    nouns = [w for w in words if len(w) > 3 and w[0].isupper()]
                    if nouns:
                        referent = nouns[0]
                
                if referent:
                    # Simple replacement
                    pattern = r'\b' + pronoun + r'\b'
                    resolved_query = re.sub(pattern, referent, resolved_query, flags=re.IGNORECASE)
                    resolutions[pronoun] = referent
        
        # Resolve "they", "them"
        for pronoun in ["they", "them"]:
            if pronoun in query.lower().split():
                if len(recent_entities) > 1:
                    referent = " and ".join(recent_entities[:2])
                    pattern = r'\b' + pronoun + r'\b'
                    resolved_query = re.sub(pattern, referent, resolved_query, flags=re.IGNORECASE)
                    resolutions[pronoun] = referent
        
        return resolved_query, resolutions
    
    def _needs_llm_resolution(
        self,
        query: str,
        resolutions: Dict[str, str]
    ) -> bool:
        """LLM çözümlemesi gerekiyor mu?"""
        # If we couldn't resolve pronouns
        query_lower = query.lower()
        has_unresolved = any(p in query_lower.split() for p in self.PRONOUNS if p not in resolutions)
        
        # Very short ambiguous query
        is_ambiguous = len(query.split()) <= 2 and not resolutions
        
        return has_unresolved or is_ambiguous
    
    def _llm_resolution(
        self,
        query: str,
        history: List[Message],
        context: ConversationContext
    ) -> str:
        """LLM ile sorgu çözümleme."""
        # Build conversation context
        history_text = []
        for msg in history[-6:]:
            role = "User" if msg.role == MessageRole.USER else "Assistant"
            history_text.append(f"{role}: {msg.content[:200]}")
        
        history_str = "\n".join(history_text)
        
        topics_str = ", ".join(t.name for t in context.active_topics[:3]) if context.active_topics else "None"
        entities_str = ", ".join(context.recent_entities[:5]) if context.recent_entities else "None"
        
        prompt = f"""Reformulate the following query to be standalone, resolving any references.

Conversation History:
{history_str}

Active Topics: {topics_str}
Recent Entities: {entities_str}

Current Query: {query}

Reformulated Query (standalone, no pronouns):"""
        
        try:
            result = self._llm.generate(prompt, max_tokens=100)
            
            # Clean up result
            result = result.strip().strip('"').strip("'")
            
            # Basic validation
            if len(result) > 5 and len(result) < 500:
                return result
        
        except Exception as e:
            logger.warning(f"LLM resolution failed: {e}")
        
        return query


# =============================================================================
# TOPIC TRACKER
# =============================================================================

class TopicTracker:
    """
    Conversation topic tracking.
    
    Detects, tracks, and manages conversation topics.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
        self._topics: Dict[str, Topic] = {}
        
        # Topic detection patterns
        self._topic_patterns = [
            r"(?:about|regarding|concerning)\s+(\w+(?:\s+\w+)?)",
            r"(?:tell me about|explain|describe)\s+(\w+(?:\s+\w+)?)",
            r"(?:what is|who is|where is)\s+(\w+(?:\s+\w+)?)",
        ]
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def detect_topics(
        self,
        message: Message,
        existing_topics: List[Topic]
    ) -> List[Topic]:
        """Mesajdan topic'leri tespit et."""
        content = message.content.lower()
        detected_topics = []
        
        # Rule-based detection
        for pattern in self._topic_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                topic_name = match.strip().title()
                topic = self._get_or_create_topic(topic_name)
                detected_topics.append(topic)
        
        # Check existing topics
        for topic in existing_topics:
            for keyword in topic.keywords:
                if keyword.lower() in content:
                    topic.last_mentioned = datetime.now().isoformat()
                    topic.message_count += 1
                    if topic not in detected_topics:
                        detected_topics.append(topic)
        
        # Update message with topics
        message.topics = [t.name for t in detected_topics]
        
        return detected_topics
    
    def _get_or_create_topic(self, name: str) -> Topic:
        """Topic getir veya oluştur."""
        topic_id = hashlib.md5(name.lower().encode()).hexdigest()[:8]
        
        if topic_id in self._topics:
            topic = self._topics[topic_id]
            topic.last_mentioned = datetime.now().isoformat()
            topic.message_count += 1
            return topic
        
        topic = Topic(
            id=topic_id,
            name=name,
            keywords=[name.lower()],
        )
        self._topics[topic_id] = topic
        
        return topic
    
    def get_active_topics(self, limit: int = 5) -> List[Topic]:
        """Aktif topic'leri getir."""
        active = [t for t in self._topics.values() if t.state == TopicState.ACTIVE]
        
        # Sort by recency
        active.sort(key=lambda t: t.last_mentioned, reverse=True)
        
        return active[:limit]
    
    def summarize_topic(self, topic: Topic, messages: List[Message]) -> str:
        """Topic için özet oluştur."""
        self._lazy_load()
        
        # Get messages related to topic
        topic_messages = []
        for msg in messages:
            if topic.name.lower() in msg.content.lower() or any(
                kw in msg.content.lower() for kw in topic.keywords
            ):
                topic_messages.append(msg)
        
        if not topic_messages:
            return ""
        
        messages_text = "\n".join([
            f"{msg.role.value}: {msg.content[:200]}"
            for msg in topic_messages[-6:]
        ])
        
        prompt = f"""Summarize the discussion about "{topic.name}" in 2-3 sentences.

Messages:
{messages_text}

Summary:"""
        
        try:
            summary = self._llm.generate(prompt, max_tokens=100)
            topic.summary = summary.strip()
            return topic.summary
        
        except Exception as e:
            logger.warning(f"Topic summarization failed: {e}")
            return ""


# =============================================================================
# CONVERSATION MEMORY
# =============================================================================

class ConversationMemory:
    """
    Conversation memory manager.
    
    Manages message history, context windows, and memory optimization.
    """
    
    def __init__(
        self,
        max_messages: int = 100,
        context_window: int = 10,
        summarize_threshold: int = 20
    ):
        self.max_messages = max_messages
        self.context_window = context_window
        self.summarize_threshold = summarize_threshold
        
        self._sessions: Dict[str, ConversationSession] = {}
        self._entity_tracker: Dict[str, List[str]] = {}  # session_id -> entities
    
    def get_or_create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> ConversationSession:
        """Session getir veya oluştur."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession(
                session_id=session_id,
                user_id=user_id,
            )
            self._entity_tracker[session_id] = []
        
        return self._sessions[session_id]
    
    def add_message(
        self,
        session_id: str,
        message: Message
    ) -> ConversationSession:
        """Mesaj ekle."""
        session = self.get_or_create_session(session_id)
        
        # Add message
        session.messages.append(message)
        session.last_activity = datetime.now().isoformat()
        
        # Extract and track entities
        entities = self._extract_entities(message.content)
        message.entities = entities
        self._entity_tracker[session_id].extend(entities)
        
        # Keep only unique recent entities
        self._entity_tracker[session_id] = list(dict.fromkeys(
            self._entity_tracker[session_id][-50:]
        ))
        
        # Trim history if needed
        if len(session.messages) > self.max_messages:
            self._trim_history(session)
        
        return session
    
    def get_context_window(
        self,
        session_id: str,
        window_size: Optional[int] = None
    ) -> List[Message]:
        """Context window mesajları."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        size = window_size or self.context_window
        return session.messages[-size:]
    
    def get_conversation_context(
        self,
        session_id: str,
        topic_tracker: TopicTracker
    ) -> ConversationContext:
        """Konuşma bağlamı oluştur."""
        session = self._sessions.get(session_id)
        if not session:
            return ConversationContext(
                active_topics=[],
                recent_entities=[],
                key_facts=[],
            )
        
        active_topics = topic_tracker.get_active_topics()
        recent_entities = self._entity_tracker.get(session_id, [])[-10:]
        
        # Count messages by role
        user_count = sum(1 for m in session.messages if m.role == MessageRole.USER)
        assistant_count = sum(1 for m in session.messages if m.role == MessageRole.ASSISTANT)
        
        return ConversationContext(
            active_topics=active_topics,
            recent_entities=recent_entities,
            key_facts=[],  # Could be populated with extracted facts
            context_summary=session.conversation_summary,
            window_messages=session.messages[-self.context_window:],
            total_messages=len(session.messages),
            user_message_count=user_count,
            assistant_message_count=assistant_count,
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """Basit entity extraction."""
        entities = []
        
        # Capitalized words (simple NER)
        words = text.split()
        for i, word in enumerate(words):
            if word and word[0].isupper() and len(word) > 2:
                # Skip sentence starters
                if i > 0:
                    clean_word = word.strip(".,!?:;\"'()")
                    if clean_word:
                        entities.append(clean_word)
        
        return list(set(entities))[:10]
    
    def _trim_history(self, session: ConversationSession):
        """Geçmişi kısalt."""
        # Keep first few messages for context
        keep_start = 2
        
        # Keep recent messages
        keep_end = self.context_window
        
        if len(session.messages) <= keep_start + keep_end:
            return
        
        # Messages to summarize
        to_summarize = session.messages[keep_start:-keep_end]
        
        # Create summary (simple version)
        summary_parts = []
        for msg in to_summarize:
            if msg.role == MessageRole.USER:
                summary_parts.append(f"User asked about: {msg.content[:50]}")
        
        session.conversation_summary = "\n".join(summary_parts[-10:])
        
        # Trim messages
        session.messages = session.messages[:keep_start] + session.messages[-keep_end:]
    
    def close_session(self, session_id: str):
        """Session'ı kapat."""
        if session_id in self._sessions:
            self._sessions[session_id].state = ConversationState.CLOSED
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Session getir."""
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[ConversationSession]:
        """Tüm session'ları getir."""
        return list(self._sessions.values())


# =============================================================================
# CONVERSATIONAL RAG
# =============================================================================

class ConversationalRAG:
    """
    Conversational RAG System.
    
    Chat-aware retrieval-augmented generation with:
    - Conversation memory
    - Query reformulation
    - Topic tracking
    - Context optimization
    
    Example:
        conv_rag = ConversationalRAG()
        result = conv_rag.query("session_123", "Tell me more about it")
    """
    
    def __init__(
        self,
        retriever: Optional[RetrieverProtocol] = None,
        llm: Optional[LLMProtocol] = None,
        memory: Optional[ConversationMemory] = None,
    ):
        self._retriever = retriever
        self._llm = llm
        
        self.memory = memory or ConversationMemory()
        self.reformulator = QueryReformulator(llm)
        self.topic_tracker = TopicTracker(llm)
        
        # Stats
        self._query_count = 0
        self._sessions_created = 0
    
    def _lazy_load(self):
        if self._retriever is None:
            from rag.pipeline import rag_pipeline
            self._retriever = rag_pipeline
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def query(
        self,
        session_id: str,
        query: str,
        user_id: Optional[str] = None,
        top_k: int = 5,
        use_reformulation: bool = True,
    ) -> ConversationalResult:
        """
        Konuşma tabanlı RAG sorgusu.
        
        Args:
            session_id: Oturum ID
            query: Kullanıcı sorgusu
            user_id: Kullanıcı ID (opsiyonel)
            top_k: Retrieval sonuç sayısı
            use_reformulation: Sorgu reformülasyonu kullan
            
        Returns:
            ConversationalResult
        """
        self._lazy_load()
        
        start_time = time.time()
        
        # 1. Get/create session
        session = self.memory.get_or_create_session(session_id, user_id)
        if session.state == ConversationState.CLOSED:
            # Reopen closed session
            session.state = ConversationState.ACTIVE
        
        # 2. Create user message
        user_message = Message.user(query)
        
        # 3. Get conversation context
        context = self.memory.get_conversation_context(session_id, self.topic_tracker)
        
        # 4. Detect topics
        self.topic_tracker.detect_topics(user_message, context.active_topics)
        
        # 5. Reformulate query
        reformulated = ReformulatedQuery(
            original_query=query,
            reformulated_query=query,
            query_type=QueryType.NEW_TOPIC,
        )
        
        if use_reformulation and session.messages:
            reformulated = self.reformulator.reformulate(
                query, session.messages, context
            )
        
        # 6. Retrieve documents
        retrieved_docs = []
        try:
            rag_context = self._retriever.retrieve(
                query=reformulated.reformulated_query,
                top_k=top_k
            )
            retrieved_docs = rag_context.chunks if hasattr(rag_context, 'chunks') else []
        except Exception as e:
            logger.warning(f"Retrieval failed: {e}")
        
        # 7. Generate response
        response, confidence = self._generate_response(
            query=reformulated.reformulated_query,
            original_query=query,
            context=context,
            retrieved_docs=retrieved_docs,
        )
        
        # 8. Create assistant message
        assistant_message = Message.assistant(response, confidence)
        assistant_message.retrieved_docs = [str(d) for d in retrieved_docs[:3]]
        
        # 9. Add messages to memory
        self.memory.add_message(session_id, user_message)
        self.memory.add_message(session_id, assistant_message)
        
        # 10. Update context
        updated_context = self.memory.get_conversation_context(session_id, self.topic_tracker)
        
        processing_time = int((time.time() - start_time) * 1000)
        self._query_count += 1
        
        return ConversationalResult(
            session_id=session_id,
            query=query,
            reformulated_query=reformulated.reformulated_query,
            response=response,
            confidence=confidence,
            conversation_context=updated_context,
            retrieved_documents=retrieved_docs,
            query_type=reformulated.query_type,
            resolved_references=reformulated.resolved_references,
            processing_time_ms=processing_time,
        )
    
    async def query_async(
        self,
        session_id: str,
        query: str,
        **kwargs
    ) -> ConversationalResult:
        """Asenkron sorgu."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(session_id, query, **kwargs)
        )
    
    def _generate_response(
        self,
        query: str,
        original_query: str,
        context: ConversationContext,
        retrieved_docs: List[Any],
    ) -> Tuple[str, float]:
        """Response üret."""
        # Build prompt with conversation context
        prompt_parts = []
        
        # System instruction
        prompt_parts.append("You are a helpful assistant engaged in a conversation.")
        
        # Conversation summary if available
        if context.context_summary:
            prompt_parts.append(f"\nConversation Summary:\n{context.context_summary}")
        
        # Recent conversation
        if context.window_messages:
            prompt_parts.append("\nRecent Conversation:")
            for msg in context.window_messages[-4:]:
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                prompt_parts.append(f"{role}: {msg.content[:300]}")
        
        # Retrieved context
        if retrieved_docs:
            prompt_parts.append("\n\n=== Relevant Information ===")
            for i, doc in enumerate(retrieved_docs[:3], 1):
                content = doc.content if hasattr(doc, 'content') else str(doc)
                prompt_parts.append(f"[{i}]: {content[:400]}")
        
        # Current query
        prompt_parts.append(f"\nCurrent User Query: {original_query}")
        
        if query != original_query:
            prompt_parts.append(f"(Interpreted as: {query})")
        
        prompt_parts.append("\nAssistant Response:")
        
        full_prompt = "\n".join(prompt_parts)
        
        try:
            response = self._llm.generate(full_prompt, max_tokens=600)
            
            # Calculate confidence
            confidence = 0.7
            if retrieved_docs:
                confidence += 0.15
            if context.window_messages:
                confidence += 0.1
            
            return response.strip(), min(confidence, 1.0)
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"Error generating response: {str(e)}", 0.0
    
    def get_session_history(
        self,
        session_id: str
    ) -> List[Dict]:
        """Session geçmişini getir."""
        session = self.memory.get_session(session_id)
        if not session:
            return []
        
        return [msg.to_dict() for msg in session.messages]
    
    def clear_session(self, session_id: str):
        """Session'ı temizle."""
        session = self.memory.get_session(session_id)
        if session:
            session.messages = []
            session.conversation_summary = ""
    
    def close_session(self, session_id: str):
        """Session'ı kapat."""
        self.memory.close_session(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler."""
        sessions = self.memory.get_all_sessions()
        active_sessions = sum(1 for s in sessions if s.state == ConversationState.ACTIVE)
        
        return {
            "query_count": self._query_count,
            "total_sessions": len(sessions),
            "active_sessions": active_sessions,
            "topics_tracked": len(self.topic_tracker._topics),
        }


# =============================================================================
# SINGLETON
# =============================================================================

_conversational_rag: Optional[ConversationalRAG] = None
_conversation_memory: Optional[ConversationMemory] = None


def get_conversational_rag() -> ConversationalRAG:
    """Singleton ConversationalRAG instance."""
    global _conversational_rag, _conversation_memory
    
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    
    if _conversational_rag is None:
        _conversational_rag = ConversationalRAG(memory=_conversation_memory)
    
    return _conversational_rag


def get_conversation_memory() -> ConversationMemory:
    """Singleton ConversationMemory instance."""
    global _conversation_memory
    
    if _conversation_memory is None:
        _conversation_memory = ConversationMemory()
    
    return _conversation_memory


conversational_rag = ConversationalRAG()
conversation_memory = ConversationMemory()


__all__ = [
    "ConversationalRAG",
    "ConversationMemory",
    "ConversationSession",
    "ConversationContext",
    "ConversationalResult",
    "Message",
    "MessageRole",
    "ConversationState",
    "QueryType",
    "Topic",
    "TopicState",
    "TopicTracker",
    "QueryReformulator",
    "ReformulatedQuery",
    "conversational_rag",
    "conversation_memory",
    "get_conversational_rag",
    "get_conversation_memory",
]
