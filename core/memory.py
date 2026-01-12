"""
Enterprise AI Assistant - Long-Term Memory Module
Uzun süreli hafıza yönetimi

LangChain uyumlu conversation memory ve knowledge persistence.

ENTERPRISE FEATURES:
- LLM-based intelligent summarization
- Importance-based memory retention
- Semantic memory search
- User preference learning
- Knowledge graph (triple store)
- Memory decay with access patterns
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib

from core.config import settings


@dataclass
class MemoryItem:
    """Hafıza öğesi."""
    id: str
    content: str
    memory_type: str  # fact, preference, context, interaction
    importance: float  # 0.0 - 1.0
    source: str
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    decay_rate: float = 0.1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "MemoryItem":
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=data["memory_type"],
            importance=data["importance"],
            source=data["source"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
            decay_rate=data.get("decay_rate", 0.1),
            metadata=data.get("metadata", {}),
        )


class ConversationBufferMemory:
    """Konuşma tampon hafızası - son N mesajı tutar."""
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._buffer: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """Mesaj ekle."""
        self._buffer.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Trim if needed
        if len(self._buffer) > self.max_messages:
            self._buffer = self._buffer[-self.max_messages:]
    
    def get_messages(self, limit: int = None) -> List[Dict[str, str]]:
        """Mesajları al."""
        if limit:
            return self._buffer[-limit:]
        return self._buffer.copy()
    
    def clear(self):
        """Tamponu temizle."""
        self._buffer.clear()
    
    def get_context_string(self) -> str:
        """Mesajları string olarak al."""
        lines = []
        for msg in self._buffer:
            role = "Kullanıcı" if msg["role"] == "user" else "Asistan"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)


class ConversationSummaryMemory:
    """
    Özet tabanlı hafıza - uzun konuşmaları akıllıca özetler.
    
    ENTERPRISE FEATURES:
    - LLM-based intelligent summarization
    - Incremental summary updates
    - Key information extraction
    - Context preservation
    """
    
    def __init__(
        self,
        summarize_threshold: int = 10,
        llm_summarize_fn: Optional[Callable[[str], str]] = None,
    ):
        self.summarize_threshold = summarize_threshold
        self._messages: List[Dict[str, str]] = []
        self._summaries: List[str] = []
        self._current_summary: str = ""
        self._llm_fn = llm_summarize_fn  # LLM özet fonksiyonu
        self._key_facts: List[str] = []  # Çıkarılan önemli bilgiler
    
    def set_llm_function(self, llm_fn: Callable[[str], str]) -> None:
        """LLM özet fonksiyonunu ayarla."""
        self._llm_fn = llm_fn
    
    def add_message(self, role: str, content: str):
        """Mesaj ekle ve gerekirse özetle."""
        self._messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Summarize if threshold reached
        if len(self._messages) >= self.summarize_threshold:
            self._create_summary()
    
    def _create_summary(self):
        """
        Mevcut mesajları akıllıca özetle.
        
        LLM varsa kullan, yoksa basit özet oluştur.
        """
        if not self._messages:
            return
        
        # Mesajları formatlı string'e çevir
        conversation_text = ""
        for msg in self._messages:
            role_name = "Kullanıcı" if msg["role"] == "user" else "Asistan"
            conversation_text += f"{role_name}: {msg['content']}\n\n"
        
        if self._llm_fn:
            # LLM-based intelligent summarization
            try:
                summary_prompt = f"""Aşağıdaki konuşmayı özetle. Önemli noktaları, kararları ve kullanıcının isteklerini vurgula.

KONUŞMA:
{conversation_text}

ÖNEMLİ: 
1. Özet en fazla 200 kelime olmalı
2. Anahtar bilgileri bullet point olarak listele
3. Kullanıcının tercihlerini ve öğrenilmesi gereken bilgileri belirt

ÖZET:"""
                
                new_summary = self._llm_fn(summary_prompt)
                
                # Önemli bilgileri çıkar
                facts_prompt = f"""Bu konuşmadan öğrenilmesi gereken önemli bilgileri çıkar.
Her satıra bir bilgi yaz. Sadece gerçek/somut bilgileri çıkar.

{conversation_text}

ÖNEMLİ BİLGİLER (her satıra bir):"""
                
                try:
                    facts = self._llm_fn(facts_prompt)
                    for line in facts.strip().split('\n'):
                        line = line.strip().lstrip('•-1234567890. ')
                        if line and len(line) > 10:
                            self._key_facts.append(line)
                except:
                    pass
                
            except Exception as e:
                print(f"⚠️ LLM summarization failed, using fallback: {e}")
                new_summary = self._fallback_summary()
        else:
            new_summary = self._fallback_summary()
        
        self._summaries.append(new_summary)
        
        # Birleşik özet oluştur (son 3 özet)
        self._current_summary = "\n\n---\n\n".join(self._summaries[-3:])
        
        # Keep only recent messages
        self._messages = self._messages[-3:]
    
    def _fallback_summary(self) -> str:
        """LLM olmadan basit özet oluştur."""
        summary_parts = []
        for msg in self._messages:
            content = msg['content']
            if msg["role"] == "user":
                # Kullanıcı sorularını koru
                if len(content) > 150:
                    content = content[:150] + "..."
                summary_parts.append(f"• Kullanıcı: {content}")
            else:
                # Asistan yanıtlarından ilk cümleyi al
                first_sentence = content.split('.')[0] if '.' in content else content[:100]
                summary_parts.append(f"• Asistan: {first_sentence}...")
        
        return "\n".join(summary_parts[-10:])  # Son 10 madde
    
    def get_context(self) -> Dict[str, Any]:
        """Özet ve son mesajları al."""
        return {
            "summary": self._current_summary,
            "recent_messages": self._messages,
            "key_facts": self._key_facts[-10:],  # Son 10 önemli bilgi
            "total_summaries": len(self._summaries),
        }
    
    def get_key_facts(self) -> List[str]:
        """Çıkarılan önemli bilgileri al."""
        return self._key_facts.copy()
    
    def force_summarize(self) -> str:
        """Zorla özet oluştur."""
        if self._messages:
            self._create_summary()
        return self._current_summary


class LongTermMemory:
    """
    Uzun süreli hafıza sistemi.
    
    Öğrenilen bilgileri, kullanıcı tercihlerini ve önemli
    bağlamsal bilgileri kalıcı olarak saklar.
    """
    
    def __init__(self, db_path: Path = None):
        """Long-term memory başlat."""
        self.db_path = db_path or settings.DATA_DIR / "memory.db"
        self._init_db()
    
    def _init_db(self):
        """Veritabanını başlat."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    source TEXT,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    decay_rate REAL DEFAULT 0.1,
                    metadata TEXT,
                    embedding TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_type 
                ON memories(memory_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance 
                ON memories(importance DESC)
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, key)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learned_facts (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    object TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    def store(
        self,
        content: str,
        memory_type: str = "context",
        importance: float = 0.5,
        source: str = "conversation",
        metadata: Dict = None,
    ) -> str:
        """
        Hafızaya bilgi kaydet.
        
        Args:
            content: İçerik
            memory_type: fact, preference, context, interaction
            importance: Önem derecesi (0-1)
            source: Kaynak
            metadata: Ek veriler
            
        Returns:
            Memory ID
        """
        memory_id = hashlib.md5(
            f"{content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memories 
                (id, content, memory_type, importance, source, 
                 created_at, last_accessed, access_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                memory_id, content, memory_type, importance,
                source, now, now, json.dumps(metadata or {})
            ))
            conn.commit()
        
        return memory_id
    
    def recall(
        self,
        query: str = None,
        memory_type: str = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryItem]:
        """
        Hafızadan bilgi çağır.
        
        Args:
            query: Arama sorgusu (basit metin eşleşmesi)
            memory_type: Filtre türü
            limit: Maksimum sonuç
            min_importance: Minimum önem
            
        Returns:
            Hafıza öğeleri listesi
        """
        conditions = ["importance >= ?"]
        params = [min_importance]
        
        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type)
        
        if query:
            conditions.append("content LIKE ?")
            params.append(f"%{query}%")
        
        where_clause = " AND ".join(conditions)
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT * FROM memories
                WHERE {where_clause}
                ORDER BY importance DESC, last_accessed DESC
                LIMIT ?
            """, params)
            
            results = []
            for row in cursor.fetchall():
                # Update access
                conn.execute("""
                    UPDATE memories 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE id = ?
                """, (datetime.now().isoformat(), row["id"]))
                
                results.append(MemoryItem(
                    id=row["id"],
                    content=row["content"],
                    memory_type=row["memory_type"],
                    importance=row["importance"],
                    source=row["source"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_accessed=datetime.fromisoformat(row["last_accessed"]),
                    access_count=row["access_count"],
                    decay_rate=row["decay_rate"],
                    metadata=json.loads(row["metadata"] or "{}"),
                ))
            
            conn.commit()
        
        return results
    
    def store_preference(self, user_id: str, key: str, value: Any):
        """Kullanıcı tercihi kaydet."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (user_id, key, value, updated_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, key, json.dumps(value), datetime.now().isoformat()))
            conn.commit()
    
    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Kullanıcı tercihi al."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT value FROM user_preferences
                WHERE user_id = ? AND key = ?
            """, (user_id, key))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return default
    
    def store_fact(
        self,
        subject: str,
        predicate: str,
        obj: str,
        confidence: float = 1.0,
        source: str = None,
    ) -> str:
        """
        Öğrenilen bilgiyi triple olarak kaydet.
        
        Args:
            subject: Özne
            predicate: Yüklem
            obj: Nesne
            confidence: Güven skoru
            source: Kaynak
        """
        fact_id = hashlib.md5(
            f"{subject}{predicate}{obj}".encode()
        ).hexdigest()[:16]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learned_facts
                (id, subject, predicate, object, confidence, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                fact_id, subject, predicate, obj,
                confidence, source, datetime.now().isoformat()
            ))
            conn.commit()
        
        return fact_id
    
    def query_facts(
        self,
        subject: str = None,
        predicate: str = None,
        obj: str = None,
    ) -> List[Dict[str, Any]]:
        """Öğrenilen bilgileri sorgula."""
        conditions = []
        params = []
        
        if subject:
            conditions.append("subject LIKE ?")
            params.append(f"%{subject}%")
        if predicate:
            conditions.append("predicate LIKE ?")
            params.append(f"%{predicate}%")
        if obj:
            conditions.append("object LIKE ?")
            params.append(f"%{obj}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(f"""
                SELECT * FROM learned_facts
                WHERE {where_clause}
                ORDER BY confidence DESC
            """, params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def decay_memories(self, days_threshold: int = 30):
        """
        Eski ve az kullanılan hafızaların önemini azalt.
        
        Memory decay - kullanılmayan bilgiler zamanla silinir.
        """
        threshold_date = (
            datetime.now() - timedelta(days=days_threshold)
        ).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Decay importance
            conn.execute("""
                UPDATE memories
                SET importance = importance * (1 - decay_rate)
                WHERE last_accessed < ?
                AND importance > 0.1
            """, (threshold_date,))
            
            # Delete very low importance memories
            conn.execute("""
                DELETE FROM memories
                WHERE importance < 0.05
                AND memory_type != 'fact'
            """)
            
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Hafıza istatistikleri."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    memory_type,
                    COUNT(*) as count,
                    AVG(importance) as avg_importance,
                    AVG(access_count) as avg_access
                FROM memories
                GROUP BY memory_type
            """)
            
            type_stats = {}
            for row in cursor.fetchall():
                type_stats[row[0]] = {
                    "count": row[1],
                    "avg_importance": round(row[2], 3),
                    "avg_access": round(row[3], 1),
                }
            
            cursor = conn.execute("SELECT COUNT(*) FROM learned_facts")
            facts_count = cursor.fetchone()[0]
            
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM user_preferences"
            )
            users_count = cursor.fetchone()[0]
            
            return {
                "memory_types": type_stats,
                "total_facts": facts_count,
                "users_with_preferences": users_count,
            }


class MemoryManager:
    """
    Tüm hafıza sistemlerini yöneten ana sınıf.
    
    ENTERPRISE FEATURES:
    - Short-term buffer memory
    - LLM-based summary memory
    - Persistent long-term memory
    - Context aggregation
    - Automatic learning from conversations
    """
    
    def __init__(self, llm_fn: Optional[Callable[[str], str]] = None):
        """Memory manager başlat."""
        self.short_term: Dict[str, ConversationBufferMemory] = {}
        self.summary: Dict[str, ConversationSummaryMemory] = {}
        self.long_term = LongTermMemory()
        self._llm_fn = llm_fn
    
    def set_llm_function(self, llm_fn: Callable[[str], str]) -> None:
        """
        LLM fonksiyonunu ayarla.
        
        Bu fonksiyon summary memory tarafından kullanılır.
        """
        self._llm_fn = llm_fn
        # Mevcut summary memory'lere de uygula
        for summary_mem in self.summary.values():
            summary_mem.set_llm_function(llm_fn)
    
    def get_session_memory(
        self,
        session_id: str,
    ) -> Tuple[ConversationBufferMemory, ConversationSummaryMemory]:
        """Session için hafıza al veya oluştur."""
        if session_id not in self.short_term:
            self.short_term[session_id] = ConversationBufferMemory()
            summary_mem = ConversationSummaryMemory()
            if self._llm_fn:
                summary_mem.set_llm_function(self._llm_fn)
            self.summary[session_id] = summary_mem
        
        return self.short_term[session_id], self.summary[session_id]
    
    def add_interaction(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        auto_learn: bool = True,
    ):
        """
        Etkileşim ekle.
        
        Args:
            session_id: Session ID
            user_message: Kullanıcı mesajı
            assistant_response: Asistan yanıtı
            auto_learn: Otomatik öğrenme yapılsın mı
        """
        short_term, summary = self.get_session_memory(session_id)
        
        short_term.add_message("user", user_message)
        short_term.add_message("assistant", assistant_response)
        
        summary.add_message("user", user_message)
        summary.add_message("assistant", assistant_response)
        
        # Otomatik öğrenme
        if auto_learn:
            self._auto_learn(user_message, assistant_response)
    
    def _auto_learn(self, user_message: str, assistant_response: str):
        """
        Konuşmadan otomatik öğren.
        
        Önemli bilgileri long-term memory'ye kaydet.
        """
        # Önemlilik tespiti (basit heuristik)
        importance_keywords = [
            "hatırla", "kaydet", "not et", "unutma", "önemli",
            "her zaman", "asla", "tercih", "seviyorum", "istemiyorum",
            "remember", "save", "note", "important", "always", "never"
        ]
        
        combined = f"{user_message} {assistant_response}".lower()
        importance = 0.3  # Base importance
        
        for keyword in importance_keywords:
            if keyword in combined:
                importance += 0.1
        
        importance = min(importance, 0.9)
        
        # Yeterli önemse kaydet
        if importance > 0.5:
            # Kısa özet oluştur
            content = f"Kullanıcı: {user_message[:200]}"
            if len(assistant_response) > 100:
                content += f"\nÖzet: {assistant_response[:200]}..."
            
            self.long_term.store(
                content=content,
                memory_type="interaction",
                importance=importance,
                source="auto_learn",
            )
    
    def get_context_for_query(
        self,
        session_id: str,
        query: str,
    ) -> Dict[str, Any]:
        """Sorgu için bağlam oluştur."""
        short_term, summary = self.get_session_memory(session_id)
        
        # Get relevant long-term memories
        relevant_memories = self.long_term.recall(
            query=query,
            limit=5,
            min_importance=0.3,
        )
        
        # Get relevant facts
        query_words = query.split()
        relevant_facts = []
        if query_words:
            relevant_facts = self.long_term.query_facts(subject=query_words[0])[:5]
        
        # Summary'den key facts
        summary_context = summary.get_context()
        
        return {
            "recent_messages": short_term.get_messages(limit=10),
            "conversation_summary": summary_context.get("summary", ""),
            "key_facts": summary_context.get("key_facts", []),
            "relevant_memories": [m.to_dict() for m in relevant_memories],
            "relevant_facts": relevant_facts,
        }
    
    def learn_from_conversation(
        self,
        content: str,
        importance: float = 0.5,
        source: str = "conversation",
    ):
        """Konuşmadan öğren."""
        self.long_term.store(
            content=content,
            memory_type="context",
            importance=importance,
            source=source,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Memory manager istatistikleri."""
        return {
            "active_sessions": len(self.short_term),
            "long_term_stats": self.long_term.get_stats(),
            "llm_enabled": self._llm_fn is not None,
        }


# Singleton instance
memory_manager = MemoryManager()
