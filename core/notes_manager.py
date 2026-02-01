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
class NoteVersion:
    """Not versiyon modeli - her kayıtta önceki durum saklanır."""
    version_id: str
    note_id: str
    title: str
    content: str
    created_at: str  # Versiyonun oluşturulma zamanı
    diff_summary: str  # AI ile oluşturulmuş değişiklik özeti
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "NoteVersion":
        return cls(**data)


@dataclass
class TrashNote:
    """Çöp kutusundaki not modeli."""
    id: str
    original_note: Dict  # Orijinal not verisi
    deleted_at: str
    deleted_from_folder: Optional[str]  # Hangi klasörden silindiği
    versions: List[Dict]  # Silinen notun versiyonları
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TrashNote":
        return cls(**data)


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
    locked: bool = False  # Kilitli klasör silinemez
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Folder":
        # Eski klasörler için varsayılan değerler ekle
        data.setdefault('locked', False)
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
    locked: bool = False  # Kilitli not silinemez
    encrypted: bool = False  # Şifreli not - AI okuyamaz
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Note":
        # Eski notlar için varsayılan değerler ekle
        data.setdefault('locked', False)
        data.setdefault('encrypted', False)
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
        self.versions_file = self.data_dir / "versions.json"
        self.trash_file = self.data_dir / "trash.json"
        self.max_versions = 10  # Her not için maksimum 10 versiyon saklanır
        self._init_files()
    
    def _init_files(self):
        """Dosyaları başlat."""
        if not self.notes_file.exists():
            self._save_notes([])
        
        if not self.folders_file.exists():
            self._save_folders([])
        
        if not self.versions_file.exists():
            self._save_versions([])
        
        if not self.trash_file.exists():
            self._save_trash([])
    
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
    
    def _load_versions(self) -> List[Dict]:
        try:
            with open(self.versions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def _save_versions(self, versions: List[Dict]):
        with open(self.versions_file, "w", encoding="utf-8") as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)
    
    def _load_trash(self) -> List[Dict]:
        try:
            with open(self.trash_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    
    def _save_trash(self, trash: List[Dict]):
        with open(self.trash_file, "w", encoding="utf-8") as f:
            json.dump(trash, f, ensure_ascii=False, indent=2)
    
    # ============ VERSİYON İŞLEMLERİ ============
    
    def _create_version(self, note: Dict, diff_summary: str = "") -> NoteVersion:
        """Notun mevcut durumunu versiyon olarak kaydet."""
        version = NoteVersion(
            version_id=str(uuid.uuid4()),
            note_id=note["id"],
            title=note["title"],
            content=note["content"],
            created_at=datetime.now().isoformat(),
            diff_summary=diff_summary,
        )
        
        versions = self._load_versions()
        
        # Bu nota ait versiyonları bul
        note_versions = [v for v in versions if v["note_id"] == note["id"]]
        other_versions = [v for v in versions if v["note_id"] != note["id"]]
        
        # Yeni versiyonu ekle
        note_versions.append(version.to_dict())
        
        # Maksimum versiyon sayısını aş, en eskisini sil
        if len(note_versions) > self.max_versions:
            # En eskiye göre sırala ve ilk n tanesini al
            note_versions.sort(key=lambda x: x["created_at"])
            note_versions = note_versions[-self.max_versions:]
        
        # Tüm versiyonları birleştir ve kaydet
        all_versions = other_versions + note_versions
        self._save_versions(all_versions)
        
        logger.info(f"Versiyon oluşturuldu: {version.version_id} (not: {note['id']})")
        return version
    
    def get_note_versions(self, note_id: str) -> List[NoteVersion]:
        """Notun tüm versiyonlarını getir (en yeniden eskiye)."""
        versions = self._load_versions()
        note_versions = [v for v in versions if v["note_id"] == note_id]
        note_versions.sort(key=lambda x: x["created_at"], reverse=True)
        return [NoteVersion.from_dict(v) for v in note_versions]
    
    def get_version(self, version_id: str) -> Optional[NoteVersion]:
        """Tek bir versiyonu getir."""
        versions = self._load_versions()
        for v in versions:
            if v["version_id"] == version_id:
                return NoteVersion.from_dict(v)
        return None
    
    def restore_version(self, note_id: str, version_id: str) -> Optional[Note]:
        """Notu belirli bir versiyona geri döndür."""
        version = self.get_version(version_id)
        if not version or version.note_id != note_id:
            return None
        
        # Mevcut durumu önce versiyon olarak kaydet
        current_note = self.get_note(note_id)
        if current_note:
            self._create_version(current_note.to_dict(), diff_summary="Versiyon geri yükleme öncesi otomatik kayıt")
        
        # Versiyondaki içeriği geri yükle
        return self.update_note(
            note_id,
            title=version.title,
            content=version.content,
            _skip_version=True  # Versiyon oluştururken sonsuz döngüyü önle
        )
    
    def get_version_diff(self, note_id: str, version_id_1: str, version_id_2: str) -> Dict:
        """İki versiyon arasındaki farkları getir."""
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)
        
        if not v1 or not v2:
            return {"error": "Versiyon bulunamadı"}
        
        # Basit diff - satır bazlı karşılaştırma
        lines1 = v1.content.split('\n')
        lines2 = v2.content.split('\n')
        
        diff = {
            "version_1": {
                "id": v1.version_id,
                "title": v1.title,
                "created_at": v1.created_at,
            },
            "version_2": {
                "id": v2.version_id,
                "title": v2.title,
                "created_at": v2.created_at,
            },
            "title_changed": v1.title != v2.title,
            "content_diff": {
                "lines_added": len(lines2) - len(lines1) if len(lines2) > len(lines1) else 0,
                "lines_removed": len(lines1) - len(lines2) if len(lines1) > len(lines2) else 0,
                "old_content": v1.content,
                "new_content": v2.content,
            }
        }
        
        return diff
    
    def delete_version(self, version_id: str) -> bool:
        """Belirli bir versiyonu sil."""
        versions = self._load_versions()
        original_len = len(versions)
        versions = [v for v in versions if v["version_id"] != version_id]
        
        if len(versions) < original_len:
            self._save_versions(versions)
            logger.info(f"Versiyon silindi: {version_id}")
            return True
        return False
    
    def clear_note_versions(self, note_id: str) -> int:
        """Notun tüm versiyonlarını sil."""
        versions = self._load_versions()
        original_len = len(versions)
        versions = [v for v in versions if v["note_id"] != note_id]
        deleted_count = original_len - len(versions)
        
        if deleted_count > 0:
            self._save_versions(versions)
            logger.info(f"Not versiyonları silindi: {note_id} ({deleted_count} adet)")
        
        return deleted_count
    
    # ============ ÇÖP KUTUSU İŞLEMLERİ ============
    
    def _move_to_trash(self, note: Dict) -> TrashNote:
        """Notu çöp kutusuna taşı."""
        # Notun versiyonlarını al
        versions = self._load_versions()
        note_versions = [v for v in versions if v["note_id"] == note["id"]]
        
        trash_note = TrashNote(
            id=str(uuid.uuid4()),
            original_note=note,
            deleted_at=datetime.now().isoformat(),
            deleted_from_folder=note.get("folder_id"),
            versions=note_versions,
        )
        
        trash = self._load_trash()
        trash.insert(0, trash_note.to_dict())
        self._save_trash(trash)
        
        # Versiyonları ana listeden sil
        versions = [v for v in versions if v["note_id"] != note["id"]]
        self._save_versions(versions)
        
        logger.info(f"Not çöp kutusuna taşındı: {note['id']}")
        return trash_note
    
    def get_trash(self) -> List[TrashNote]:
        """Çöp kutusundaki notları getir (en yeni silinen önce)."""
        trash = self._load_trash()
        return [TrashNote.from_dict(t) for t in trash]
    
    def get_trash_note(self, trash_id: str) -> Optional[TrashNote]:
        """Çöp kutusundan tek bir not getir."""
        trash = self._load_trash()
        for t in trash:
            if t["id"] == trash_id:
                return TrashNote.from_dict(t)
        return None
    
    def restore_from_trash(self, trash_id: str) -> Optional[Note]:
        """Çöp kutusundan notu geri yükle."""
        trash = self._load_trash()
        trash_note = None
        trash_index = -1
        
        for i, t in enumerate(trash):
            if t["id"] == trash_id:
                trash_note = t
                trash_index = i
                break
        
        if not trash_note:
            return None
        
        # Orijinal notu geri yükle
        original_note = trash_note["original_note"]
        original_note["updated_at"] = datetime.now().isoformat()
        
        notes = self._load_notes()
        notes.insert(0, original_note)
        self._save_notes(notes)
        
        # Versiyonları geri yükle
        if trash_note.get("versions"):
            versions = self._load_versions()
            versions.extend(trash_note["versions"])
            self._save_versions(versions)
        
        # Çöp kutusundan kaldır
        trash.pop(trash_index)
        self._save_trash(trash)
        
        logger.info(f"Not çöp kutusundan geri yüklendi: {original_note['id']}")
        return Note.from_dict(original_note)
    
    def permanent_delete(self, trash_id: str) -> bool:
        """Çöp kutusundan kalıcı olarak sil."""
        trash = self._load_trash()
        original_len = len(trash)
        trash = [t for t in trash if t["id"] != trash_id]
        
        if len(trash) < original_len:
            self._save_trash(trash)
            logger.info(f"Not kalıcı olarak silindi: {trash_id}")
            return True
        return False
    
    def empty_trash(self) -> int:
        """Çöp kutusunu tamamen boşalt."""
        trash = self._load_trash()
        count = len(trash)
        self._save_trash([])
        logger.info(f"Çöp kutusu boşaltıldı: {count} not silindi")
        return count
    
    def get_trash_count(self) -> int:
        """Çöp kutusundaki not sayısı."""
        trash = self._load_trash()
        return len(trash)
    
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
        locked: bool = None,
        encrypted: bool = None,
        _skip_version: bool = False,  # Dahili kullanım için
    ) -> Optional[Note]:
        """Notu güncelle. Her güncellemede önceki durum versiyon olarak saklanır."""
        notes = self._load_notes()
        
        for i, n in enumerate(notes):
            if n["id"] == note_id:
                # Değişiklik var mı kontrol et
                has_content_change = (
                    (title is not None and n["title"] != title) or
                    (content is not None and n["content"] != content)
                )
                
                # İçerik değişikliği varsa versiyon oluştur
                if has_content_change and not _skip_version:
                    diff_summary = self._generate_diff_summary(n, title, content)
                    self._create_version(n, diff_summary=diff_summary)
                
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
                if locked is not None:
                    n["locked"] = locked
                if encrypted is not None:
                    n["encrypted"] = encrypted
                
                n["updated_at"] = datetime.now().isoformat()
                notes[i] = n
                self._save_notes(notes)
                return Note.from_dict(n)
        
        return None
    
    def _generate_diff_summary(self, old_note: Dict, new_title: str = None, new_content: str = None) -> str:
        """Değişiklik özeti oluştur (basit versiyon)."""
        changes = []
        
        if new_title and old_note["title"] != new_title:
            changes.append(f"Başlık değişti: '{old_note['title'][:30]}' → '{new_title[:30]}'")
        
        if new_content and old_note["content"] != new_content:
            old_lines = len(old_note["content"].split('\n'))
            new_lines = len(new_content.split('\n'))
            old_chars = len(old_note["content"])
            new_chars = len(new_content)
            
            if new_chars > old_chars:
                changes.append(f"+{new_chars - old_chars} karakter eklendi")
            elif new_chars < old_chars:
                changes.append(f"-{old_chars - new_chars} karakter silindi")
            
            if new_lines != old_lines:
                diff = new_lines - old_lines
                changes.append(f"{'+' if diff > 0 else ''}{diff} satır")
        
        return " | ".join(changes) if changes else "Küçük değişiklikler"
    
    def delete_note(self, note_id: str) -> bool:
        """Notu çöp kutusuna taşı (kalıcı silmek için permanent_delete kullan)."""
        notes = self._load_notes()
        note_to_delete = None
        note_index = -1
        
        for i, n in enumerate(notes):
            if n["id"] == note_id:
                note_to_delete = n
                note_index = i
                break
        
        if note_to_delete:
            # Çöp kutusuna taşı
            self._move_to_trash(note_to_delete)
            
            # Ana listeden kaldır
            notes.pop(note_index)
            self._save_notes(notes)
            
            logger.info(f"Not silindi (çöp kutusuna taşındı): {note_id}")
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
        versions = self._load_versions()
        trash = self._load_trash()
        
        return {
            "total_notes": len(notes),
            "total_folders": len(folders),
            "pinned_notes": len([n for n in notes if n.get("pinned")]),
            "root_notes": len([n for n in notes if n.get("folder_id") is None]),
            "root_folders": len([f for f in folders if f.get("parent_id") is None]),
            "total_versions": len(versions),
            "trash_count": len(trash),
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
