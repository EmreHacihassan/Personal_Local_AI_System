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
    is_favorite: bool = False  # Favori mesaj


@dataclass
class Session:
    """Chat session'ı."""
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_pinned: bool = False  # Sabitleme
    tags: List[str] = field(default_factory=list)  # Etiketler
    category: str = ""  # Kategori
    
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
            "is_pinned": self.is_pinned,
            "tags": self.tags,
            "category": self.category,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Dict'ten Session oluştur."""
        messages = []
        for m in data.get("messages", []):
            msg = Message(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", ""),
                sources=m.get("sources", []),
                metadata=m.get("metadata", {}),
                is_favorite=m.get("is_favorite", False),
            )
            messages.append(msg)
        
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=messages,
            metadata=data.get("metadata", {}),
            is_pinned=data.get("is_pinned", False),
            tags=data.get("tags", []),
            category=data.get("category", ""),
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
        self._list_cache: Optional[List[Dict[str, Any]]] = None
        self._list_cache_time: float = 0
        self._list_cache_ttl: float = 5.0  # 5 saniye cache
    
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
        import time
        
        # Cache kontrolü
        current_time = time.time()
        if self._list_cache is not None and (current_time - self._list_cache_time) < self._list_cache_ttl:
            return self._list_cache[:limit]
        
        sessions = []
        pinned_sessions = []
        
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
                    
                    session_info = {
                        "id": data["id"],
                        "title": data["title"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(messages),
                        "preview": preview,
                        "is_pinned": data.get("is_pinned", False),
                        "tags": data.get("tags", []),
                        "category": data.get("category", ""),
                    }
                    
                    # Sabitlenmiş olanları ayrı listele
                    if data.get("is_pinned", False):
                        pinned_sessions.append(session_info)
                    else:
                        sessions.append(session_info)
                        
            except Exception:
                continue
        
        # Sabitlenmiş olanlar önce, sonra normal olanlar
        result = pinned_sessions + sessions
        
        # Cache'i güncelle
        self._list_cache = result
        self._list_cache_time = current_time
        
        return result[:limit]
    
    def invalidate_list_cache(self):
        """Liste cache'ini geçersiz kıl."""
        self._list_cache = None
        self._list_cache_time = 0
    
    def cleanup_old_sessions(self, days: int = 7, keep_pinned: bool = True) -> Dict[str, Any]:
        """
        Eski session'ları temizle.
        
        Args:
            days: Kaç günden eski session'lar silinsin
            keep_pinned: Sabitlenmiş session'ları koru (default: True)
            
        Returns:
            Temizleme raporu
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        kept_count = 0
        deleted_ids = []
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Skip pinned sessions
                if keep_pinned and data.get("is_pinned", False):
                    kept_count += 1
                    continue
                
                # Check last update date
                updated_at = data.get("updated_at", data.get("created_at", ""))
                if updated_at:
                    try:
                        session_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        # Make naive for comparison
                        if session_date.tzinfo:
                            session_date = session_date.replace(tzinfo=None)
                        
                        if session_date < cutoff_date:
                            # Delete old session
                            session_id = data.get("id", "")
                            if session_id in self._cache:
                                del self._cache[session_id]
                            file_path.unlink()
                            deleted_count += 1
                            deleted_ids.append(session_id)
                    except Exception:
                        pass
                        
            except Exception:
                continue
        
        # Invalidate cache
        self.invalidate_list_cache()
        
        return {
            "deleted_count": deleted_count,
            "kept_pinned": kept_count,
            "cutoff_days": days,
            "deleted_ids": deleted_ids[:10],  # First 10 for reference
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Session'ı sil."""
        # Cache'den kaldır
        if session_id in self._cache:
            del self._cache[session_id]
        
        # Liste cache'ini geçersiz kıl
        self.invalidate_list_cache()
        
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
        
        # Liste cache'ini geçersiz kıl
        self.invalidate_list_cache()
            
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
        self.invalidate_list_cache()
        return count
    
    def auto_title_session(self, session_id: str, first_message: str) -> Optional[Session]:
        """İlk mesaja göre otomatik başlık oluştur."""
        # İlk 50 karakteri al ve başlık yap
        title = first_message[:50].strip()
        if len(first_message) > 50:
            title += "..."
        
        return self.update_session_title(session_id, title)
    
    # ============ SABİTLEME & ETİKETLEME ============
    
    def toggle_pin(self, session_id: str) -> bool:
        """Session'ı sabitle/sabitlemesini kaldır."""
        session = self.get_session(session_id)
        if session:
            session.is_pinned = not session.is_pinned
            session.updated_at = datetime.now().isoformat()
            self._save_session(session)
            return session.is_pinned
        return False
    
    def add_tag(self, session_id: str, tag: str) -> bool:
        """Session'a etiket ekle."""
        session = self.get_session(session_id)
        if session:
            tag = tag.strip().lower()
            if tag and tag not in session.tags:
                session.tags.append(tag)
                session.updated_at = datetime.now().isoformat()
                self._save_session(session)
                return True
        return False
    
    def remove_tag(self, session_id: str, tag: str) -> bool:
        """Session'dan etiket kaldır."""
        session = self.get_session(session_id)
        if session and tag in session.tags:
            session.tags.remove(tag)
            session.updated_at = datetime.now().isoformat()
            self._save_session(session)
            return True
        return False
    
    def set_category(self, session_id: str, category: str) -> bool:
        """Session'a kategori ata."""
        session = self.get_session(session_id)
        if session:
            session.category = category
            session.updated_at = datetime.now().isoformat()
            self._save_session(session)
            return True
        return False
    
    def get_all_tags(self) -> List[str]:
        """Tüm kullanılan etiketleri getir."""
        tags = set()
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for tag in data.get("tags", []):
                        tags.add(tag)
            except Exception:
                continue
        return sorted(list(tags))
    
    def get_all_categories(self) -> List[str]:
        """Tüm kategorileri getir."""
        categories = set()
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cat = data.get("category", "")
                    if cat:
                        categories.add(cat)
            except Exception:
                continue
        return sorted(list(categories))
    
    def list_sessions_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Etikete göre session'ları listele."""
        all_sessions = self.list_sessions(limit=100)
        return [s for s in all_sessions if tag in s.get("tags", [])]
    
    def list_sessions_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Kategoriye göre session'ları listele."""
        all_sessions = self.list_sessions(limit=100)
        return [s for s in all_sessions if s.get("category", "") == category]
    
    # ============ FAVORİ MESAJLAR ============
    
    def toggle_message_favorite(self, session_id: str, message_index: int) -> bool:
        """Mesajı favorilere ekle/çıkar."""
        session = self.get_session(session_id)
        if session and 0 <= message_index < len(session.messages):
            session.messages[message_index].is_favorite = not session.messages[message_index].is_favorite
            session.updated_at = datetime.now().isoformat()
            self._save_session(session)
            return session.messages[message_index].is_favorite
        return False
    
    def get_all_favorites(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Tüm favori mesajları getir."""
        favorites = []
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                session_id = data["id"]
                session_title = data["title"]
                
                for idx, msg in enumerate(data.get("messages", [])):
                    if msg.get("is_favorite", False):
                        favorites.append({
                            "session_id": session_id,
                            "session_title": session_title,
                            "message_index": idx,
                            "role": msg.get("role"),
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp"),
                        })
                        
                        if len(favorites) >= limit:
                            return favorites
                            
            except Exception:
                continue
        
        # Tarihe göre sırala
        favorites.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return favorites
    
    # ============ MESAJ ŞABLONLARI ============
    
    def get_templates_path(self) -> Path:
        """Şablon dosyası yolunu getir."""
        return self.storage_dir.parent / "templates.json"
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Tüm şablonları getir."""
        path = self.get_templates_path()
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def save_template(self, name: str, content: str, category: str = "") -> bool:
        """Yeni şablon kaydet."""
        templates = self.get_templates()
        
        # Aynı isimde varsa güncelle
        for t in templates:
            if t["name"] == name:
                t["content"] = content
                t["category"] = category
                t["updated_at"] = datetime.now().isoformat()
                break
        else:
            templates.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "content": content,
                "category": category,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "use_count": 0,
            })
        
        try:
            with open(self.get_templates_path(), "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Şablon sil."""
        templates = self.get_templates()
        templates = [t for t in templates if t.get("id") != template_id]
        
        try:
            with open(self.get_templates_path(), "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def increment_template_use(self, template_id: str) -> None:
        """Şablon kullanım sayısını artır."""
        templates = self.get_templates()
        for t in templates:
            if t.get("id") == template_id:
                t["use_count"] = t.get("use_count", 0) + 1
                break
        
        try:
            with open(self.get_templates_path(), "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    # ============ İSTATİSTİKLER ============
    
    def get_statistics(self) -> Dict[str, Any]:
        """Detaylı kullanım istatistiklerini getir."""
        from collections import Counter
        
        stats = {
            "total_sessions": 0,
            "total_messages": 0,
            "total_user_messages": 0,
            "total_assistant_messages": 0,
            "total_favorites": 0,
            "total_pinned": 0,
            "sessions_by_date": Counter(),
            "messages_by_hour": Counter(),
            "top_categories": Counter(),
            "top_tags": Counter(),
            "avg_messages_per_session": 0,
            "word_cloud_data": [],
        }
        
        all_user_text = []
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                messages = data.get("messages", [])
                if not messages:
                    continue
                
                stats["total_sessions"] += 1
                stats["total_messages"] += len(messages)
                
                if data.get("is_pinned"):
                    stats["total_pinned"] += 1
                
                # Kategori ve etiketler
                cat = data.get("category", "")
                if cat:
                    stats["top_categories"][cat] += 1
                
                for tag in data.get("tags", []):
                    stats["top_tags"][tag] += 1
                
                # Tarih bazlı istatistik
                created = data.get("created_at", "")[:10]
                if created:
                    stats["sessions_by_date"][created] += 1
                
                for msg in messages:
                    role = msg.get("role", "")
                    if role == "user":
                        stats["total_user_messages"] += 1
                        all_user_text.append(msg.get("content", ""))
                    elif role == "assistant":
                        stats["total_assistant_messages"] += 1
                    
                    if msg.get("is_favorite"):
                        stats["total_favorites"] += 1
                    
                    # Saat bazlı istatistik
                    timestamp = msg.get("timestamp", "")
                    if len(timestamp) >= 13:
                        hour = timestamp[11:13]
                        stats["messages_by_hour"][hour] += 1
                        
            except Exception:
                continue
        
        # Ortalama hesapla
        if stats["total_sessions"] > 0:
            stats["avg_messages_per_session"] = round(
                stats["total_messages"] / stats["total_sessions"], 1
            )
        
        # Word cloud verisi
        stats["word_cloud_data"] = self.get_all_topics(limit=30)
        
        # Counter'ları dict'e çevir
        stats["sessions_by_date"] = dict(sorted(
            stats["sessions_by_date"].items(),
            reverse=True
        )[:30])
        stats["messages_by_hour"] = dict(sorted(stats["messages_by_hour"].items()))
        stats["top_categories"] = dict(stats["top_categories"].most_common(10))
        stats["top_tags"] = dict(stats["top_tags"].most_common(10))
        
        return stats
    
    # ============ GELİŞMİŞ ARAMA ============
    
    def advanced_search(
        self,
        query: str = "",
        date_from: str = "",
        date_to: str = "",
        tags: List[str] = None,
        category: str = "",
        pinned_only: bool = False,
        favorites_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Gelişmiş arama."""
        results = []
        query_lower = query.lower() if query else ""
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                messages = data.get("messages", [])
                if not messages:
                    continue
                
                # Filtreler
                session_date = data.get("created_at", "")[:10]
                
                if date_from and session_date < date_from:
                    continue
                if date_to and session_date > date_to:
                    continue
                
                if pinned_only and not data.get("is_pinned"):
                    continue
                
                if category and data.get("category", "") != category:
                    continue
                
                if tags:
                    session_tags = data.get("tags", [])
                    if not any(t in session_tags for t in tags):
                        continue
                
                # Metin araması
                matched = not query_lower  # Sorgu yoksa eşleş
                match_snippet = ""
                
                for msg in messages:
                    content = msg.get("content", "")
                    
                    if favorites_only and not msg.get("is_favorite"):
                        continue
                    
                    if query_lower and query_lower in content.lower():
                        matched = True
                        idx = content.lower().find(query_lower)
                        start = max(0, idx - 30)
                        end = min(len(content), idx + 70)
                        match_snippet = content[start:end]
                        if start > 0:
                            match_snippet = "..." + match_snippet
                        if end < len(content):
                            match_snippet = match_snippet + "..."
                        break
                
                if matched:
                    preview = ""
                    for msg in messages:
                        if msg.get("role") == "user":
                            preview = msg.get("content", "")[:80]
                            break
                    
                    results.append({
                        "id": data["id"],
                        "title": data["title"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(messages),
                        "preview": preview,
                        "match_snippet": match_snippet,
                        "is_pinned": data.get("is_pinned", False),
                        "tags": data.get("tags", []),
                        "category": data.get("category", ""),
                    })
                    
                    if len(results) >= limit:
                        break
                        
            except Exception:
                continue
        
        # Sabitlenmiş olanları önce göster
        results.sort(key=lambda x: (not x.get("is_pinned"), x.get("updated_at", "")), reverse=True)
        
        return results
    
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
