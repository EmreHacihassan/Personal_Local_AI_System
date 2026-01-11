"""
Conversation Chain Manager
==========================

Endüstri standartlarında konuşma zinciri yönetimi.
LangChain ConversationChain pattern'ine uyumlu.

Features:
- Conversation history management
- Context window optimization
- Message compression
- Conversation branching
- Multi-turn reasoning
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib

from .logger import get_logger

logger = get_logger("conversation")


class MessageRole(Enum):
    """Mesaj rolleri"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass
class Message:
    """Konuşma mesajı"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: Optional[int] = None
    message_id: Optional[str] = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = hashlib.md5(
                f"{self.role.value}{self.content}{self.timestamp.isoformat()}".encode()
            ).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "token_count": self.token_count,
            "message_id": self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            token_count=data.get("token_count"),
            message_id=data.get("message_id")
        )
    
    def to_llm_format(self) -> Dict[str, str]:
        """LLM API formatına dönüştür"""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class ConversationTurn:
    """Bir konuşma turu (user + assistant)"""
    user_message: Message
    assistant_message: Optional[Message] = None
    turn_id: int = 0
    context_used: Optional[List[str]] = None  # RAG context
    tools_used: Optional[List[str]] = None
    
    @property
    def is_complete(self) -> bool:
        return self.assistant_message is not None


class MessageCompressor(ABC):
    """Mesaj sıkıştırma stratejisi"""
    
    @abstractmethod
    def compress(self, messages: List[Message], max_tokens: int) -> List[Message]:
        pass


class TruncateCompressor(MessageCompressor):
    """Son N mesajı tut"""
    
    def compress(self, messages: List[Message], max_tokens: int) -> List[Message]:
        # Basit yaklaşım: token sayısına göre kırp
        result = []
        total_tokens = 0
        
        # Son mesajlardan başla
        for msg in reversed(messages):
            estimated_tokens = msg.token_count or len(msg.content) // 4
            
            if total_tokens + estimated_tokens <= max_tokens:
                result.insert(0, msg)
                total_tokens += estimated_tokens
            else:
                break
        
        return result


class SummaryCompressor(MessageCompressor):
    """Eski mesajları özetle"""
    
    def __init__(self, summarizer: Optional[Callable[[str], str]] = None):
        self.summarizer = summarizer
    
    def compress(self, messages: List[Message], max_tokens: int) -> List[Message]:
        if len(messages) <= 4:
            return messages
        
        # Son 4 mesajı koru
        recent = messages[-4:]
        old = messages[:-4]
        
        # Eski mesajları özetle
        if self.summarizer and old:
            old_text = "\n".join([f"{m.role.value}: {m.content}" for m in old])
            summary = self.summarizer(old_text)
            
            summary_msg = Message(
                role=MessageRole.SYSTEM,
                content=f"[Previous conversation summary: {summary}]",
                metadata={"is_summary": True, "original_count": len(old)}
            )
            
            return [summary_msg] + recent
        
        return recent


class Conversation:
    """
    Konuşma yönetimi
    
    Features:
    - Message history
    - Token counting
    - Context window management
    - Branching support
    """
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        compressor: Optional[MessageCompressor] = None
    ):
        self.conversation_id = conversation_id or hashlib.md5(
            datetime.now().isoformat().encode()
        ).hexdigest()[:16]
        
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.compressor = compressor or TruncateCompressor()
        
        self._messages: List[Message] = []
        self._turns: List[ConversationTurn] = []
        self._branches: Dict[str, List[Message]] = {}
        self._current_branch = "main"
        
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
        
        # System prompt ekle
        if system_prompt:
            self.add_message(MessageRole.SYSTEM, system_prompt)
    
    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict] = None,
        token_count: Optional[int] = None
    ) -> Message:
        """Mesaj ekle"""
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            token_count=token_count or len(content) // 4
        )
        
        self._messages.append(msg)
        self.updated_at = datetime.now()
        
        # Turn tracking
        if role == MessageRole.USER:
            self._turns.append(ConversationTurn(
                user_message=msg,
                turn_id=len(self._turns)
            ))
        elif role == MessageRole.ASSISTANT and self._turns:
            self._turns[-1].assistant_message = msg
        
        logger.debug(f"Message added: {role.value} ({len(content)} chars)")
        
        return msg
    
    def add_user_message(self, content: str, **kwargs) -> Message:
        """User mesajı ekle (kısayol)"""
        return self.add_message(MessageRole.USER, content, **kwargs)
    
    def add_assistant_message(self, content: str, **kwargs) -> Message:
        """Assistant mesajı ekle (kısayol)"""
        return self.add_message(MessageRole.ASSISTANT, content, **kwargs)
    
    def get_messages(
        self,
        include_system: bool = True,
        compress: bool = True
    ) -> List[Message]:
        """Mesajları al"""
        messages = self._messages.copy()
        
        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]
        
        if compress:
            messages = self.compressor.compress(messages, self.max_tokens)
        
        return messages
    
    def get_llm_messages(self, compress: bool = True) -> List[Dict[str, str]]:
        """LLM API formatında mesajları al"""
        return [m.to_llm_format() for m in self.get_messages(compress=compress)]
    
    def get_last_user_message(self) -> Optional[Message]:
        """Son user mesajını al"""
        for msg in reversed(self._messages):
            if msg.role == MessageRole.USER:
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Son assistant mesajını al"""
        for msg in reversed(self._messages):
            if msg.role == MessageRole.ASSISTANT:
                return msg
        return None
    
    @property
    def turn_count(self) -> int:
        """Tur sayısı"""
        return len(self._turns)
    
    @property
    def message_count(self) -> int:
        """Mesaj sayısı"""
        return len(self._messages)
    
    @property
    def total_tokens(self) -> int:
        """Toplam token sayısı (tahmini)"""
        return sum(m.token_count or len(m.content) // 4 for m in self._messages)
    
    def create_branch(self, branch_name: str, from_message_id: Optional[str] = None) -> str:
        """Konuşma dalı oluştur"""
        if from_message_id:
            # Belirli mesaja kadar kopyala
            branch_messages = []
            for msg in self._messages:
                branch_messages.append(msg)
                if msg.message_id == from_message_id:
                    break
        else:
            branch_messages = self._messages.copy()
        
        self._branches[branch_name] = branch_messages
        
        logger.info(f"Branch created: {branch_name} ({len(branch_messages)} messages)")
        
        return branch_name
    
    def switch_branch(self, branch_name: str) -> bool:
        """Dal değiştir"""
        if branch_name == "main":
            return True
        
        if branch_name not in self._branches:
            return False
        
        # Mevcut dalı kaydet
        if self._current_branch == "main":
            self._branches["main"] = self._messages.copy()
        
        # Yeni dala geç
        self._messages = self._branches[branch_name].copy()
        self._current_branch = branch_name
        
        logger.info(f"Switched to branch: {branch_name}")
        
        return True
    
    def clear(self, keep_system: bool = True):
        """Konuşmayı temizle"""
        if keep_system:
            self._messages = [m for m in self._messages if m.role == MessageRole.SYSTEM]
        else:
            self._messages.clear()
        
        self._turns.clear()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Serialization"""
        return {
            "conversation_id": self.conversation_id,
            "system_prompt": self.system_prompt,
            "messages": [m.to_dict() for m in self._messages],
            "turns": len(self._turns),
            "current_branch": self._current_branch,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conversation":
        """Deserialization"""
        conv = cls(
            conversation_id=data["conversation_id"],
            system_prompt=data.get("system_prompt")
        )
        
        conv._messages = [Message.from_dict(m) for m in data["messages"]]
        conv.created_at = datetime.fromisoformat(data["created_at"])
        conv.updated_at = datetime.fromisoformat(data["updated_at"])
        conv.metadata = data.get("metadata", {})
        
        return conv


class ConversationStore:
    """
    Konuşma depolama
    
    SQLite tabanlı persistent storage.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/conversations.db")
        self._init_db()
    
    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_updated 
            ON conversations(updated_at DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save(self, conversation: Conversation):
        """Konuşmayı kaydet"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversations (id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (
            conversation.conversation_id,
            json.dumps(conversation.to_dict()),
            conversation.created_at.isoformat(),
            conversation.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Conversation saved: {conversation.conversation_id}")
    
    def load(self, conversation_id: str) -> Optional[Conversation]:
        """Konuşmayı yükle"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT data FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Conversation.from_dict(json.loads(row[0]))
        
        return None
    
    def list_conversations(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Konuşmaları listele"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, created_at, updated_at FROM conversations
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        results = [
            {"id": row[0], "created_at": row[1], "updated_at": row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return results
    
    def delete(self, conversation_id: str) -> bool:
        """Konuşmayı sil"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted


class ConversationChain:
    """
    LangChain-style Conversation Chain
    
    Konuşma akışını yönetir ve LLM ile entegre çalışır.
    """
    
    def __init__(
        self,
        llm_callable: Optional[Callable[[List[Dict]], str]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        store: Optional[ConversationStore] = None,
        auto_save: bool = True
    ):
        self.llm = llm_callable
        self.conversation = Conversation(
            system_prompt=system_prompt,
            max_tokens=max_tokens
        )
        self.store = store or ConversationStore()
        self.auto_save = auto_save
        
        self._preprocessors: List[Callable[[str], str]] = []
        self._postprocessors: List[Callable[[str], str]] = []
    
    def add_preprocessor(self, fn: Callable[[str], str]):
        """Input preprocessor ekle"""
        self._preprocessors.append(fn)
    
    def add_postprocessor(self, fn: Callable[[str], str]):
        """Output postprocessor ekle"""
        self._postprocessors.append(fn)
    
    def _preprocess(self, text: str) -> str:
        for fn in self._preprocessors:
            text = fn(text)
        return text
    
    def _postprocess(self, text: str) -> str:
        for fn in self._postprocessors:
            text = fn(text)
        return text
    
    async def arun(self, user_input: str, **kwargs) -> str:
        """
        Async conversation run
        
        1. User input'u preprocess et
        2. Mesajları hazırla
        3. LLM'i çağır
        4. Response'u postprocess et
        5. Kaydet
        """
        # Preprocess
        processed_input = self._preprocess(user_input)
        
        # Add user message
        self.conversation.add_user_message(processed_input)
        
        # Get messages for LLM
        messages = self.conversation.get_llm_messages()
        
        # Call LLM
        if self.llm:
            import asyncio
            if asyncio.iscoroutinefunction(self.llm):
                response = await self.llm(messages, **kwargs)
            else:
                response = self.llm(messages, **kwargs)
        else:
            response = "[No LLM configured]"
        
        # Postprocess
        processed_response = self._postprocess(response)
        
        # Add assistant message
        self.conversation.add_assistant_message(processed_response)
        
        # Auto save
        if self.auto_save:
            self.store.save(self.conversation)
        
        return processed_response
    
    def run(self, user_input: str, **kwargs) -> str:
        """Sync conversation run"""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.arun(user_input, **kwargs)
        )
    
    def predict(self, input: str, **kwargs) -> str:
        """LangChain uyumlu predict metodu"""
        return self.run(input, **kwargs)
    
    @property
    def memory(self) -> Conversation:
        """LangChain uyumlu memory accessor"""
        return self.conversation
    
    def load_conversation(self, conversation_id: str) -> bool:
        """Mevcut konuşmayı yükle"""
        loaded = self.store.load(conversation_id)
        if loaded:
            self.conversation = loaded
            return True
        return False
    
    def new_conversation(self, system_prompt: Optional[str] = None):
        """Yeni konuşma başlat"""
        self.conversation = Conversation(
            system_prompt=system_prompt or self.conversation.system_prompt,
            max_tokens=self.conversation.max_tokens
        )


# Global instances
conversation_store = ConversationStore()


__all__ = [
    "Conversation",
    "ConversationChain",
    "ConversationStore",
    "ConversationTurn",
    "Message",
    "MessageRole",
    "MessageCompressor",
    "TruncateCompressor",
    "SummaryCompressor",
    "conversation_store"
]
