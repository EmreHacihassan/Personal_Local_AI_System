"""
Notes Manager - Not ve Klasör Yönetim Sistemi
Masaüstü dosya yöneticisi tarzında not ve klasör yönetimi.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from core.logger import get_logger

logger = get_logger("notes_manager")


class NoteColor(str, Enum):
    """Not renkleri."""
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PINK = "pink"
    PURPLE = "purple"
    ORANGE = "orange"
    RED = "red"
    GRAY = "gray"


@dataclass
class Folder:
    """Klasör veri modeli."""
    id: str
    name: str
    parent_id: Optional[str]  # None = root klasör
    color: str
    icon: str
    created_at: str
    updated_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Folder":
        return cls(**data)


@dataclass
class Note:
    """Not veri modeli."""
    id: str
    title: str
    content: str
    folder_id: Optional[str]  # None = root'ta
    color: str
    pinned: bool
    created_at: str
    updated_at: str
    tags: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Note":
        return cls(**data)


class NotesManager:
    """
    Not ve Klasör yönetim sınıfı.
    Masaüstü dosya yöneticisi tarzında organizasyon.
    """
    
    def __init__(self, data_dir: str = "data/notes"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / "notes.json"
        self.folders_file = self.data_dir / "folders.json"
        self._init_files()
    
    def _init_files(self):
        """Dosyaları başlat."""
        if not self.notes_file.exists():
            self._save_notes([])
        
        if not self.folders_file.exists():
            self._save_folders([])
    
    # ============ FILE OPERATIONS ============
    
    def _load_notes(self) -> List[Dict]:
        try:
            with open(self.notes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def _save_notes(self, notes: List[Dict]):
        with open(self.notes_file, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
    
    def _load_folders(self) -> List[Dict]:
        try:
            with open(self.folders_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def _save_folders(self, folders: List[Dict]):
        with open(self.folders_file, "w", encoding="utf-8") as f:
            json.dump(folders, f, ensure_ascii=False, indent=2)
    
    # ============ KLASÖR İŞLEMLERİ ============
    
    def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
        color: str = "blue",
        icon: str = "📁",
    ) -> Folder:
        """Yeni klasör oluştur."""
        now = datetime.now().isoformat()
        
        folder = Folder(
            id=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            color=color,
            icon=icon,
            created_at=now,
            updated_at=now,
        )
        
        folders = self._load_folders()
        folders.append(folder.to_dict())
        self._save_folders(folders)
        
        logger.info(f"Klasör oluşturuldu: {folder.id} - {name}")
        return folder
    
    def get_folder(self, folder_id: str) -> Optional[Folder]:
        """Klasör getir."""
        folders = self._load_folders()
        for f in folders:
            if f["id"] == folder_id:
                return Folder.from_dict(f)
        return None
    
    def update_folder(
        self,
        folder_id: str,
        name: str = None,
        color: str = None,
        icon: str = None,
        parent_id: str = None,
    ) -> Optional[Folder]:
        """Klasörü güncelle."""
        folders = self._load_folders()
        
        for i, f in enumerate(folders):
            if f["id"] == folder_id:
                if name is not None:
                    f["name"] = name
                if color is not None:
                    f["color"] = color
                if icon is not None:
                    f["icon"] = icon
                if parent_id is not None:
                    # Kendi içine taşımayı engelle
                    if parent_id != folder_id:
                        f["parent_id"] = parent_id
                
                f["updated_at"] = datetime.now().isoformat()
                folders[i] = f
                self._save_folders(folders)
                return Folder.from_dict(f)
        
        return None
    
    def delete_folder(self, folder_id: str, recursive: bool = True) -> bool:
        """Klasörü sil. recursive=True ise içindeki her şeyi de siler."""
        folders = self._load_folders()
        notes = self._load_notes()
        
        # Klasörü bul
        folder = None
        for f in folders:
            if f["id"] == folder_id:
                folder = f
                break
        
        if not folder:
            return False
        
        if recursive:
            # Alt klasörleri bul ve sil
            def get_child_folder_ids(parent_id):
                child_ids = []
                for f in folders:
                    if f["parent_id"] == parent_id:
                        child_ids.append(f["id"])
                        child_ids.extend(get_child_folder_ids(f["id"]))
                return child_ids
            
            child_ids = get_child_folder_ids(folder_id)
            all_folder_ids = [folder_id] + child_ids
            
            # Tüm klasörleri sil
            folders = [f for f in folders if f["id"] not in all_folder_ids]
            
            # Bu klasörlerdeki notları sil
            notes = [n for n in notes if n.get("folder_id") not in all_folder_ids]
        else:
            # Sadece boş klasörü sil
            has_children = any(f["parent_id"] == folder_id for f in folders)
            has_notes = any(n.get("folder_id") == folder_id for n in notes)
            
            if has_children or has_notes:
                return False
            
            folders = [f for f in folders if f["id"] != folder_id]
        
        self._save_folders(folders)
        self._save_notes(notes)
        logger.info(f"Klasör silindi: {folder_id}")
        return True
    
    def list_folders(self, parent_id: Optional[str] = None) -> List[Folder]:
        """Belirli bir klasördeki alt klasörleri listele. parent_id=None root klasörleri listeler."""
        folders = self._load_folders()
        result = [Folder.from_dict(f) for f in folders if f.get("parent_id") == parent_id]
        result.sort(key=lambda x: x.name.lower())
        return result
    
    def get_folder_path(self, folder_id: Optional[str]) -> List[Folder]:
        """Klasörün breadcrumb path'ini döndür (root'tan itibaren)."""
        if folder_id is None:
            return []
        
        path = []
        current_id = folder_id
        
        while current_id:
            folder = self.get_folder(current_id)
            if folder:
                path.insert(0, folder)
                current_id = folder.parent_id
            else:
                break
        
        return path
    
    def get_all_folders(self) -> List[Folder]:
        """Tüm klasörleri getir."""
        folders = self._load_folders()
        return [Folder.from_dict(f) for f in folders]
    
    # ============ NOT İŞLEMLERİ ============
    
    def create_note(
        self,
        title: str,
        content: str = "",
        folder_id: Optional[str] = None,
        color: str = "yellow",
        tags: List[str] = None,
        pinned: bool = False,
    ) -> Note:
        """Yeni not oluştur."""
        now = datetime.now().isoformat()
        
        note = Note(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            folder_id=folder_id,
            color=color,
            pinned=pinned,
            created_at=now,
            updated_at=now,
            tags=tags or [],
        )
        
        notes = self._load_notes()
        notes.insert(0, note.to_dict())
        self._save_notes(notes)
        
        logger.info(f"Not oluşturuldu: {note.id}")
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        """Not getir."""
        notes = self._load_notes()
        for n in notes:
            if n["id"] == note_id:
                return Note.from_dict(n)
        return None
    
    def update_note(
        self,
        note_id: str,
        title: str = None,
        content: str = None,
        folder_id: str = None,
        color: str = None,
        tags: List[str] = None,
        pinned: bool = None,
    ) -> Optional[Note]:
        """Notu güncelle."""
        notes = self._load_notes()
        
        for i, n in enumerate(notes):
            if n["id"] == note_id:
                if title is not None:
                    n["title"] = title
                if content is not None:
                    n["content"] = content
                if folder_id is not None:
                    n["folder_id"] = folder_id if folder_id != "" else None
                if color is not None:
                    n["color"] = color
                if tags is not None:
                    n["tags"] = tags
                if pinned is not None:
                    n["pinned"] = pinned
                
                n["updated_at"] = datetime.now().isoformat()
                notes[i] = n
                self._save_notes(notes)
                return Note.from_dict(n)
        
        return None
    
    def delete_note(self, note_id: str) -> bool:
        """Notu sil."""
        notes = self._load_notes()
        original_len = len(notes)
        notes = [n for n in notes if n["id"] != note_id]
        
        if len(notes) < original_len:
            self._save_notes(notes)
            logger.info(f"Not silindi: {note_id}")
            return True
        return False
    
    def toggle_pin(self, note_id: str) -> Optional[Note]:
        """Notu sabitle/kaldır."""
        note = self.get_note(note_id)
        if note:
            return self.update_note(note_id, pinned=not note.pinned)
        return None
    
    def move_note(self, note_id: str, new_folder_id: Optional[str]) -> Optional[Note]:
        """Notu başka klasöre taşı."""
        return self.update_note(note_id, folder_id=new_folder_id if new_folder_id else "")
    
    def list_notes(
        self,
        folder_id: Optional[str] = None,
        include_subfolders: bool = False,
        search_query: str = None,
        pinned_only: bool = False,
    ) -> List[Note]:
        """Notları listele."""
        notes = self._load_notes()
        
        # Folder filter
        if not include_subfolders:
            notes = [n for n in notes if n.get("folder_id") == folder_id]
        else:
            # Alt klasörlerdeki notları da dahil et
            if folder_id:
                all_folder_ids = [folder_id]
                folders = self._load_folders()
                
                def get_child_ids(parent_id):
                    ids = []
                    for f in folders:
                        if f["parent_id"] == parent_id:
                            ids.append(f["id"])
                            ids.extend(get_child_ids(f["id"]))
                    return ids
                
                all_folder_ids.extend(get_child_ids(folder_id))
                notes = [n for n in notes if n.get("folder_id") in all_folder_ids]
        
        # Search filter
        if search_query:
            query_lower = search_query.lower()
            notes = [
                n for n in notes
                if query_lower in n["title"].lower() or query_lower in n["content"].lower()
            ]
        
        # Pinned filter
        if pinned_only:
            notes = [n for n in notes if n.get("pinned", False)]
        
        # Sort: pinned first, then by update time
        notes.sort(key=lambda x: (not x.get("pinned", False), x.get("updated_at", "")), reverse=True)
        notes.sort(key=lambda x: not x.get("pinned", False))
        
        return [Note.from_dict(n) for n in notes]
    
    def search_notes(self, query: str) -> List[Note]:
        """Tüm notlarda ara."""
        notes = self._load_notes()
        query_lower = query.lower()
        
        results = [
            n for n in notes
            if query_lower in n["title"].lower() or query_lower in n["content"].lower()
        ]
        
        return [Note.from_dict(n) for n in results[:10]]
    
    def get_notes_count(self, folder_id: Optional[str] = None) -> int:
        """Klasördeki not sayısı."""
        notes = self._load_notes()
        if folder_id is None:
            return len([n for n in notes if n.get("folder_id") is None])
        return len([n for n in notes if n.get("folder_id") == folder_id])
    
    def get_all_notes(self) -> List[Note]:
        """Tüm notları getir."""
        notes = self._load_notes()
        return [Note.from_dict(n) for n in notes]
    
    # ============ STATS & UTILS ============
    
    def get_stats(self) -> Dict:
        """İstatistikler."""
        notes = self._load_notes()
        folders = self._load_folders()
        
        return {
            "total_notes": len(notes),
            "total_folders": len(folders),
            "pinned_notes": len([n for n in notes if n.get("pinned")]),
            "root_notes": len([n for n in notes if n.get("folder_id") is None]),
            "root_folders": len([f for f in folders if f.get("parent_id") is None]),
        }
    
    def export_all(self, format: str = "json") -> str:
        """Tüm notları dışa aktar."""
        notes = self._load_notes()
        folders = self._load_folders()
        
        if format == "json":
            return json.dumps({"notes": notes, "folders": folders}, ensure_ascii=False, indent=2)
        elif format == "markdown":
            md = "# Notlarım\n\n"
            for note in notes:
                md += f"## {note['title']}\n\n"
                md += f"{note['content']}\n\n"
                md += "---\n\n"
            return md
        
        return ""



from core.config import settings

# Singleton instance
# Use external data directory from settings
notes_manager = NotesManager(data_dir=str(settings.DATA_DIR / "notes"))
