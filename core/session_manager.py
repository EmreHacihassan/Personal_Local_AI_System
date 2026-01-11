"""
Enterprise AI Assistant - Session Manager
Konuşma oturumu yönetimi

Endüstri standardı session management.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
import uuid

from core.config import settings


@dataclass
class Message:
    """Chat mesajı."""
    role: str  # "user" veya "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """Chat session'ı."""
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, sources: List[str] = None, metadata: Dict = None) -> Message:
        """Session'a mesaj ekle."""
        message = Message(
            role=role,
            content=content,
            sources=sources or [],
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()
        return message
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Son N mesajı al."""
        return [asdict(m) for m in self.messages[-limit:]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Session'ı dict'e çevir."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [asdict(m) for m in self.messages],
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Dict'ten Session oluştur."""
        messages = [
            Message(**m) for m in data.get("messages", [])
        ]
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=messages,
            metadata=data.get("metadata", {}),
        )


class SessionManager:
    """Session yönetim sınıfı."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        SessionManager başlat.
        
        Args:
            storage_dir: Session dosyalarının saklanacağı klasör
        """
        self.storage_dir = storage_dir or settings.DATA_DIR / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Session] = {}
    
    def create_session(self, title: Optional[str] = None) -> Session:
        """Yeni session oluştur."""
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        session = Session(
            id=session_id,
            title=title or f"Konuşma - {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            created_at=now,
            updated_at=now,
        )
        
        self._cache[session_id] = session
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Session'ı ID ile getir."""
        # Önce cache'e bak
        if session_id in self._cache:
            return self._cache[session_id]
        
        # Dosyadan yükle
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                session = Session.from_dict(data)
                self._cache[session_id] = session
                return session
        
        return None
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Session getir veya oluştur."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        return self.create_session()
    
    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Tüm session'ları listele (özet bilgi)."""
        sessions = []
        
        for file_path in sorted(
            self.storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data["id"],
                        "title": data["title"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(data.get("messages", [])),
                    })
            except Exception:
                continue
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Session'ı sil."""
        # Cache'den kaldır
        if session_id in self._cache:
            del self._cache[session_id]
        
        # Dosyayı sil
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def update_session_title(self, session_id: str, title: str) -> Optional[Session]:
        """Session başlığını güncelle."""
        session = self.get_session(session_id)
        if session:
            session.title = title
            session.updated_at = datetime.now().isoformat()
            self._save_session(session)
            return session
        return None
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: List[str] = None,
        metadata: Dict = None
    ) -> Optional[Message]:
        """Session'a mesaj ekle."""
        session = self.get_session(session_id)
        if session:
            message = session.add_message(role, content, sources, metadata)
            self._save_session(session)
            return message
        return None
    
    def _save_session(self, session: Session) -> None:
        """Session'ı dosyaya kaydet."""
        file_path = self.storage_dir / f"{session.id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)
    
    def clear_all_sessions(self) -> int:
        """Tüm session'ları temizle."""
        count = 0
        for file_path in self.storage_dir.glob("*.json"):
            file_path.unlink()
            count += 1
        
        self._cache.clear()
        return count
    
    def auto_title_session(self, session_id: str, first_message: str) -> Optional[Session]:
        """İlk mesaja göre otomatik başlık oluştur."""
        # İlk 50 karakteri al ve başlık yap
        title = first_message[:50].strip()
        if len(first_message) > 50:
            title += "..."
        
        return self.update_session_title(session_id, title)


# Singleton instance
session_manager = SessionManager()
