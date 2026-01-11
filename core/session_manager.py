"""
Enterprise AI Assistant - Session Manager
Konuşma oturumu yönetimi

Endüstri standardı session management.
Kalıcı geçmiş saklama ve arama desteği.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
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
    
    def get_user_messages(self) -> List[str]:
        """Sadece kullanıcı mesajlarını al."""
        return [m.content for m in self.messages if m.role == "user"]
    
    def get_assistant_messages(self) -> List[str]:
        """Sadece asistan mesajlarını al."""
        return [m.content for m in self.messages if m.role == "assistant"]
    
    def get_summary(self) -> str:
        """Konuşmanın kısa özetini al."""
        if not self.messages:
            return "Boş konuşma"
        
        user_msgs = self.get_user_messages()
        if not user_msgs:
            return "Boş konuşma"
        
        # İlk ve son kullanıcı mesajından özet oluştur
        first = user_msgs[0][:100] + "..." if len(user_msgs[0]) > 100 else user_msgs[0]
        
        return f"Başlangıç: {first}"
    
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
        """Tüm session'ları listele (özet bilgi). 0 mesajlı session'ları dahil etmez."""
        sessions = []
        
        for file_path in sorted(
            self.storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    messages = data.get("messages", [])
                    
                    # 0 mesajlı session'ları atla
                    if not messages:
                        continue
                    
                    # İlk mesajdan önizleme oluştur
                    preview = ""
                    for msg in messages:
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            preview = content[:80] + "..." if len(content) > 80 else content
                            break
                    
                    sessions.append({
                        "id": data["id"],
                        "title": data["title"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(messages),
                        "preview": preview,
                    })
                    
                    # Limit kontrolü
                    if len(sessions) >= limit:
                        break
                        
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
        """Session'ı dosyaya kaydet. Sadece mesaj varsa kaydeder."""
        # 0 mesajlı session'ları kaydetme
        if not session.messages:
            return
            
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
    
    # ============ YENİ: GEÇMİŞ ARAMA ÖZELLİKLERİ ============
    
    def search_all_sessions(
        self,
        query: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Tüm konuşmalarda arama yap.
        
        Args:
            query: Arama sorgusu
            limit: Maksimum sonuç sayısı
            
        Returns:
            Eşleşen mesajlar listesi
        """
        results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                session_id = data["id"]
                session_title = data["title"]
                messages = data.get("messages", [])
                
                for idx, msg in enumerate(messages):
                    content = msg.get("content", "")
                    content_lower = content.lower()
                    
                    # Tüm kelimeler içerikte var mı kontrol et
                    if all(word in content_lower for word in query_words):
                        # Eşleşen bölümü bul
                        match_start = content_lower.find(query_words[0])
                        snippet_start = max(0, match_start - 50)
                        snippet_end = min(len(content), match_start + 150)
                        snippet = content[snippet_start:snippet_end]
                        
                        if snippet_start > 0:
                            snippet = "..." + snippet
                        if snippet_end < len(content):
                            snippet = snippet + "..."
                        
                        results.append({
                            "session_id": session_id,
                            "session_title": session_title,
                            "message_index": idx,
                            "role": msg.get("role"),
                            "content": content,
                            "snippet": snippet,
                            "timestamp": msg.get("timestamp"),
                            "created_at": data.get("created_at"),
                        })
                        
                        if len(results) >= limit:
                            return results
                            
            except Exception:
                continue
        
        # Tarihe göre sırala (en yeni önce)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return results[:limit]
    
    def get_context_for_query(
        self,
        query: str,
        current_session_id: Optional[str] = None,
        max_results: int = 5
    ) -> str:
        """
        Sorgu için geçmiş konuşmalardan bağlam oluştur.
        
        "Daha önce X hakkında ne demiştim?" tarzı sorgular için.
        
        Args:
            query: Kullanıcı sorgusu
            current_session_id: Mevcut oturum (hariç tutulacak)
            max_results: Maksimum sonuç sayısı
            
        Returns:
            Bağlam metni
        """
        # "Daha önce", "geçmişte", "önceki konuşmada" gibi ifadeleri temizle
        clean_query = query.lower()
        remove_phrases = [
            "daha önce", "daha once", "önceden", "onceden",
            "geçmişte", "gecmiste", "önceki konuşmada", "onceki konusmada",
            "sana söylemiştim", "sana demistim", "hakkında ne demiştim",
            "hakkinda ne demistim", "anlat", "hatırla", "hatirla",
            "konuşmuştuk", "konusmustuk", "bahsetmiştim", "bahsetmistim"
        ]
        
        for phrase in remove_phrases:
            clean_query = clean_query.replace(phrase, "")
        
        clean_query = clean_query.strip()
        
        if not clean_query:
            return ""
        
        # Geçmişte ara
        results = self.search_all_sessions(clean_query, limit=max_results * 2)
        
        # Mevcut oturumu hariç tut
        if current_session_id:
            results = [r for r in results if r["session_id"] != current_session_id]
        
        results = results[:max_results]
        
        if not results:
            return ""
        
        # Bağlam oluştur
        context_parts = ["## Geçmiş Konuşmalardan Bulunan Bilgiler:\n"]
        
        for i, result in enumerate(results, 1):
            role_label = "Sen" if result["role"] == "user" else "Ben (AI)"
            date_str = result.get("timestamp", "")[:10] if result.get("timestamp") else "Bilinmeyen tarih"
            
            context_parts.append(f"""
### Konuşma {i} ({date_str})
**{role_label}:** {result['content'][:500]}{'...' if len(result['content']) > 500 else ''}
""")
        
        return "\n".join(context_parts)
    
    def get_session_full_text(self, session_id: str) -> str:
        """
        Bir session'ın tüm konuşmasını metin olarak al.
        
        Args:
            session_id: Session ID
            
        Returns:
            Konuşma metni
        """
        session = self.get_session(session_id)
        if not session:
            return ""
        
        lines = [f"# {session.title}\n", f"Tarih: {session.created_at[:10]}\n", "---\n"]
        
        for msg in session.messages:
            role_label = "👤 Kullanıcı" if msg.role == "user" else "🤖 AI Asistan"
            timestamp = msg.timestamp[:19].replace("T", " ") if msg.timestamp else ""
            
            lines.append(f"\n**{role_label}** ({timestamp}):\n")
            lines.append(f"{msg.content}\n")
            
            if msg.sources:
                lines.append(f"\n📚 Kaynaklar: {', '.join(msg.sources)}\n")
        
        return "\n".join(lines)
    
    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """
        Session'ı dışa aktar.
        
        Args:
            session_id: Session ID
            format: Çıktı formatı (json, txt, md)
            
        Returns:
            Dışa aktarılan içerik
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        if format == "json":
            return json.dumps(session.to_dict(), ensure_ascii=False, indent=2)
        
        elif format in ["txt", "md"]:
            return self.get_session_full_text(session_id)
        
        return None
    
    def get_all_topics(self, limit: int = 20) -> List[Tuple[str, int]]:
        """
        Tüm konuşmalardan ana konuları çıkar.
        
        Returns:
            (konu, sayı) tuple listesi
        """
        from collections import Counter
        
        # Türkçe stop words
        stop_words = {
            "bir", "bu", "şu", "ve", "veya", "ile", "için", "de", "da",
            "den", "dan", "ne", "nasıl", "neden", "hangi", "kim", "var",
            "yok", "değil", "mi", "mı", "mu", "mü", "ben", "sen", "biz",
            "siz", "o", "onu", "ona", "onun", "bana", "sana", "beni",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "of", "to", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
        }
        
        word_counts = Counter()
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for msg in data.get("messages", []):
                    if msg.get("role") == "user":
                        content = msg.get("content", "").lower()
                        # Sadece alfanumerik kelimeleri al
                        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b', content)
                        
                        for word in words:
                            if word not in stop_words:
                                word_counts[word] += 1
                                
            except Exception:
                continue
        
        return word_counts.most_common(limit)


# Singleton instance
session_manager = SessionManager()
