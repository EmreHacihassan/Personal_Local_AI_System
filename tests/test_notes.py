"""
Enterprise AI Assistant - Notes Management Tests
=================================================

Not ve klasör yönetimi için kapsamlı testler.
CRUD operations, search, export, organization testleri.
"""

import pytest
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestNotesManagerBasics:
    """NotesManager temel testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    def test_init_creates_data_dir(self, temp_dir):
        """NotesManager data dizini oluşturmalı."""
        from core.notes_manager import NotesManager
        
        new_dir = Path(temp_dir) / "test_notes"
        manager = NotesManager(data_dir=str(new_dir))
        
        assert new_dir.exists()
        assert (new_dir / "notes.json").exists()
        assert (new_dir / "folders.json").exists()
    
    def test_init_empty_notes(self, notes_manager):
        """Başlangıçta notlar boş olmalı."""
        notes = notes_manager.get_all_notes()
        assert notes == []
    
    def test_init_empty_folders(self, notes_manager):
        """Başlangıçta klasörler boş olmalı."""
        folders = notes_manager.get_all_folders()
        assert folders == []


class TestNoteOperations:
    """Not işlemleri testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    def test_create_note(self, notes_manager):
        """Not oluşturulabilmeli."""
        note = notes_manager.create_note(
            title="Test Notu",
            content="Bu bir test notudur."
        )
        
        assert note is not None
        assert note.id is not None
        assert note.title == "Test Notu"
        assert note.content == "Bu bir test notudur."
        assert note.folder_id is None
        assert note.pinned is False
    
    def test_create_note_with_color(self, notes_manager):
        """Not renk ile oluşturulabilmeli."""
        note = notes_manager.create_note(
            title="Renkli Not",
            content="İçerik",
            color="blue"
        )
        
        assert note.color == "blue"
    
    def test_create_note_with_tags(self, notes_manager):
        """Not etiketlerle oluşturulabilmeli."""
        note = notes_manager.create_note(
            title="Etiketli Not",
            content="İçerik",
            tags=["python", "test", "dev"]
        )
        
        assert note.tags == ["python", "test", "dev"]
    
    def test_create_pinned_note(self, notes_manager):
        """Sabitlenmiş not oluşturulabilmeli."""
        note = notes_manager.create_note(
            title="Sabit Not",
            content="Önemli içerik",
            pinned=True
        )
        
        assert note.pinned is True
    
    def test_get_note(self, notes_manager):
        """Not getirilebilmeli."""
        created = notes_manager.create_note(
            title="Test",
            content="İçerik"
        )
        
        retrieved = notes_manager.get_note(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"
    
    def test_get_nonexistent_note(self, notes_manager):
        """Olmayan not None dönmeli."""
        result = notes_manager.get_note("nonexistent-id")
        
        assert result is None
    
    def test_update_note_title(self, notes_manager):
        """Not başlığı güncellenebilmeli."""
        note = notes_manager.create_note(
            title="Eski Başlık",
            content="İçerik"
        )
        
        updated = notes_manager.update_note(note.id, title="Yeni Başlık")
        
        assert updated is not None
        assert updated.title == "Yeni Başlık"
        assert updated.content == "İçerik"  # değişmemiş olmalı
    
    def test_update_note_content(self, notes_manager):
        """Not içeriği güncellenebilmeli."""
        note = notes_manager.create_note(
            title="Başlık",
            content="Eski içerik"
        )
        
        updated = notes_manager.update_note(note.id, content="Yeni içerik")
        
        assert updated is not None
        assert updated.content == "Yeni içerik"
    
    def test_update_note_color(self, notes_manager):
        """Not rengi güncellenebilmeli."""
        note = notes_manager.create_note(
            title="Not",
            content="İçerik",
            color="yellow"
        )
        
        updated = notes_manager.update_note(note.id, color="green")
        
        assert updated.color == "green"
    
    def test_update_note_tags(self, notes_manager):
        """Not etiketleri güncellenebilmeli."""
        note = notes_manager.create_note(
            title="Not",
            content="İçerik",
            tags=["eski"]
        )
        
        updated = notes_manager.update_note(note.id, tags=["yeni", "etiket"])
        
        assert updated.tags == ["yeni", "etiket"]
    
    def test_delete_note(self, notes_manager):
        """Not silinebilmeli."""
        note = notes_manager.create_note(
            title="Silinecek",
            content="İçerik"
        )
        
        result = notes_manager.delete_note(note.id)
        
        assert result is True
        assert notes_manager.get_note(note.id) is None
    
    def test_delete_nonexistent_note(self, notes_manager):
        """Olmayan not silme False dönmeli."""
        result = notes_manager.delete_note("nonexistent-id")
        
        assert result is False
    
    def test_toggle_pin(self, notes_manager):
        """Not sabitleme toggle çalışmalı."""
        note = notes_manager.create_note(
            title="Not",
            content="İçerik",
            pinned=False
        )
        
        toggled = notes_manager.toggle_pin(note.id)
        assert toggled.pinned is True
        
        toggled_again = notes_manager.toggle_pin(note.id)
        assert toggled_again.pinned is False
    
    def test_move_note(self, notes_manager):
        """Not taşınabilmeli."""
        folder = notes_manager.create_folder(name="Hedef Klasör")
        note = notes_manager.create_note(
            title="Taşınacak",
            content="İçerik"
        )
        
        moved = notes_manager.move_note(note.id, folder.id)
        
        assert moved is not None
        assert moved.folder_id == folder.id


class TestFolderOperations:
    """Klasör işlemleri testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    def test_create_folder(self, notes_manager):
        """Klasör oluşturulabilmeli."""
        folder = notes_manager.create_folder(name="Test Klasör")
        
        assert folder is not None
        assert folder.id is not None
        assert folder.name == "Test Klasör"
        assert folder.parent_id is None
    
    def test_create_folder_with_color(self, notes_manager):
        """Klasör renk ile oluşturulabilmeli."""
        folder = notes_manager.create_folder(
            name="Renkli Klasör",
            color="red"
        )
        
        assert folder.color == "red"
    
    def test_create_folder_with_icon(self, notes_manager):
        """Klasör ikon ile oluşturulabilmeli."""
        folder = notes_manager.create_folder(
            name="İkonlu Klasör",
            icon="🎯"
        )
        
        assert folder.icon == "🎯"
    
    def test_create_nested_folder(self, notes_manager):
        """İç içe klasör oluşturulabilmeli."""
        parent = notes_manager.create_folder(name="Ana Klasör")
        child = notes_manager.create_folder(
            name="Alt Klasör",
            parent_id=parent.id
        )
        
        assert child.parent_id == parent.id
    
    def test_get_folder(self, notes_manager):
        """Klasör getirilebilmeli."""
        created = notes_manager.create_folder(name="Test")
        
        retrieved = notes_manager.get_folder(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test"
    
    def test_get_nonexistent_folder(self, notes_manager):
        """Olmayan klasör None dönmeli."""
        result = notes_manager.get_folder("nonexistent-id")
        
        assert result is None
    
    def test_update_folder_name(self, notes_manager):
        """Klasör adı güncellenebilmeli."""
        folder = notes_manager.create_folder(name="Eski Ad")
        
        updated = notes_manager.update_folder(folder.id, name="Yeni Ad")
        
        assert updated is not None
        assert updated.name == "Yeni Ad"
    
    def test_update_folder_color(self, notes_manager):
        """Klasör rengi güncellenebilmeli."""
        folder = notes_manager.create_folder(name="Klasör", color="blue")
        
        updated = notes_manager.update_folder(folder.id, color="green")
        
        assert updated.color == "green"
    
    def test_delete_empty_folder(self, notes_manager):
        """Boş klasör silinebilmeli."""
        folder = notes_manager.create_folder(name="Silinecek")
        
        result = notes_manager.delete_folder(folder.id)
        
        assert result is True
        assert notes_manager.get_folder(folder.id) is None
    
    def test_delete_folder_with_notes_recursive(self, notes_manager):
        """Klasör recursive silme notları da silmeli."""
        folder = notes_manager.create_folder(name="Klasör")
        note = notes_manager.create_note(
            title="İçindeki Not",
            content="İçerik",
            folder_id=folder.id
        )
        
        result = notes_manager.delete_folder(folder.id, recursive=True)
        
        assert result is True
        assert notes_manager.get_note(note.id) is None
    
    def test_delete_folder_with_subfolders_recursive(self, notes_manager):
        """Klasör recursive silme alt klasörleri de silmeli."""
        parent = notes_manager.create_folder(name="Ana")
        child = notes_manager.create_folder(name="Alt", parent_id=parent.id)
        
        result = notes_manager.delete_folder(parent.id, recursive=True)
        
        assert result is True
        assert notes_manager.get_folder(parent.id) is None
        assert notes_manager.get_folder(child.id) is None
    
    def test_list_root_folders(self, notes_manager):
        """Root klasörler listelenebilmeli."""
        notes_manager.create_folder(name="Klasör 1")
        notes_manager.create_folder(name="Klasör 2")
        
        folders = notes_manager.list_folders(parent_id=None)
        
        assert len(folders) == 2
    
    def test_list_subfolders(self, notes_manager):
        """Alt klasörler listelenebilmeli."""
        parent = notes_manager.create_folder(name="Ana")
        notes_manager.create_folder(name="Alt 1", parent_id=parent.id)
        notes_manager.create_folder(name="Alt 2", parent_id=parent.id)
        
        subfolders = notes_manager.list_folders(parent_id=parent.id)
        
        assert len(subfolders) == 2
    
    def test_get_folder_path(self, notes_manager):
        """Klasör path alınabilmeli."""
        level1 = notes_manager.create_folder(name="Seviye 1")
        level2 = notes_manager.create_folder(name="Seviye 2", parent_id=level1.id)
        level3 = notes_manager.create_folder(name="Seviye 3", parent_id=level2.id)
        
        path = notes_manager.get_folder_path(level3.id)
        
        assert len(path) == 3
        assert path[0].name == "Seviye 1"
        assert path[1].name == "Seviye 2"
        assert path[2].name == "Seviye 3"


class TestNotesSearch:
    """Not arama testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    @pytest.fixture
    def populated_notes(self, notes_manager):
        """Test notları oluştur."""
        notes_manager.create_note(title="Python Temelleri", content="Python dilinin temelleri")
        notes_manager.create_note(title="JavaScript Notları", content="JS ile web geliştirme")
        notes_manager.create_note(title="Veritabanı", content="PostgreSQL ve MongoDB")
        notes_manager.create_note(title="AI ve ML", content="Machine learning konseptleri")
        return notes_manager
    
    def test_search_by_title(self, populated_notes):
        """Başlıkta arama çalışmalı."""
        results = populated_notes.search_notes("Python")
        
        assert len(results) == 1
        assert results[0].title == "Python Temelleri"
    
    def test_search_by_content(self, populated_notes):
        """İçerikte arama çalışmalı."""
        results = populated_notes.search_notes("web geliştirme")
        
        assert len(results) == 1
        assert results[0].title == "JavaScript Notları"
    
    def test_search_case_insensitive(self, populated_notes):
        """Arama büyük-küçük harf duyarsız olmalı."""
        results = populated_notes.search_notes("PYTHON")
        
        assert len(results) == 1
    
    def test_search_no_results(self, populated_notes):
        """Sonuç yoksa boş liste dönmeli."""
        results = populated_notes.search_notes("olmayan_kelime")
        
        assert results == []
    
    def test_search_limit_results(self, notes_manager):
        """Arama sonuçları limitlenmeli."""
        # 15 not oluştur
        for i in range(15):
            notes_manager.create_note(title=f"Test Not {i}", content="ortak içerik")
        
        results = notes_manager.search_notes("ortak")
        
        # Max 10 sonuç
        assert len(results) <= 10


class TestNotesListing:
    """Not listeleme testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    def test_list_notes_in_folder(self, notes_manager):
        """Klasördeki notlar listelenebilmeli."""
        folder = notes_manager.create_folder(name="Test Klasör")
        
        notes_manager.create_note(title="Not 1", content="", folder_id=folder.id)
        notes_manager.create_note(title="Not 2", content="", folder_id=folder.id)
        notes_manager.create_note(title="Root Not", content="")  # root'ta
        
        notes = notes_manager.list_notes(folder_id=folder.id)
        
        assert len(notes) == 2
    
    def test_list_root_notes(self, notes_manager):
        """Root notlar listelenebilmeli."""
        folder = notes_manager.create_folder(name="Klasör")
        
        notes_manager.create_note(title="Root 1", content="")
        notes_manager.create_note(title="Root 2", content="")
        notes_manager.create_note(title="Klasörde", content="", folder_id=folder.id)
        
        notes = notes_manager.list_notes(folder_id=None)
        
        assert len(notes) == 2
    
    def test_list_pinned_first(self, notes_manager):
        """Sabitlenmiş notlar önce gelmeli."""
        notes_manager.create_note(title="Normal Not", content="")
        notes_manager.create_note(title="Sabit Not", content="", pinned=True)
        notes_manager.create_note(title="Başka Normal", content="")
        
        notes = notes_manager.list_notes()
        
        assert notes[0].pinned is True
        assert notes[0].title == "Sabit Not"
    
    def test_list_pinned_only(self, notes_manager):
        """Sadece sabitlenmiş notlar listelenebilmeli."""
        notes_manager.create_note(title="Normal", content="")
        notes_manager.create_note(title="Sabit 1", content="", pinned=True)
        notes_manager.create_note(title="Sabit 2", content="", pinned=True)
        
        notes = notes_manager.list_notes(pinned_only=True)
        
        assert len(notes) == 2
        assert all(n.pinned for n in notes)
    
    def test_list_with_search(self, notes_manager):
        """Arama ile listeleme çalışmalı."""
        notes_manager.create_note(title="Python Öğreniyorum", content="")
        notes_manager.create_note(title="JavaScript", content="")
        notes_manager.create_note(title="Python Framework", content="")
        
        notes = notes_manager.list_notes(search_query="Python")
        
        assert len(notes) == 2


class TestNotesStats:
    """İstatistik testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    def test_get_stats_empty(self, notes_manager):
        """Boş stats doğru olmalı."""
        stats = notes_manager.get_stats()
        
        assert stats["total_notes"] == 0
        assert stats["total_folders"] == 0
        assert stats["pinned_notes"] == 0
    
    def test_get_stats_with_data(self, notes_manager):
        """Stats doğru sayılmalı."""
        folder = notes_manager.create_folder(name="Klasör")
        notes_manager.create_note(title="Not 1", content="")
        notes_manager.create_note(title="Not 2", content="", pinned=True)
        notes_manager.create_note(title="Not 3", content="", folder_id=folder.id)
        
        stats = notes_manager.get_stats()
        
        assert stats["total_notes"] == 3
        assert stats["total_folders"] == 1
        assert stats["pinned_notes"] == 1
        assert stats["root_notes"] == 2
    
    def test_get_notes_count_in_folder(self, notes_manager):
        """Klasördeki not sayısı doğru olmalı."""
        folder = notes_manager.create_folder(name="Klasör")
        notes_manager.create_note(title="Not 1", content="", folder_id=folder.id)
        notes_manager.create_note(title="Not 2", content="", folder_id=folder.id)
        
        count = notes_manager.get_notes_count(folder_id=folder.id)
        
        assert count == 2


class TestNotesExport:
    """Export testleri."""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici dizin oluştur."""
        dir_path = tempfile.mkdtemp()
        yield dir_path
        shutil.rmtree(dir_path, ignore_errors=True)
    
    @pytest.fixture
    def notes_manager(self, temp_dir):
        """Test için NotesManager."""
        from core.notes_manager import NotesManager
        return NotesManager(data_dir=temp_dir)
    
    def test_export_json(self, notes_manager):
        """JSON export çalışmalı."""
        notes_manager.create_folder(name="Klasör")
        notes_manager.create_note(title="Not", content="İçerik")
        
        export = notes_manager.export_all(format="json")
        
        assert export is not None
        data = json.loads(export)
        assert "notes" in data
        assert "folders" in data
        assert len(data["notes"]) == 1
        assert len(data["folders"]) == 1
    
    def test_export_markdown(self, notes_manager):
        """Markdown export çalışmalı."""
        notes_manager.create_note(title="Test Başlık", content="Test içerik")
        
        export = notes_manager.export_all(format="markdown")
        
        assert "# Notlarım" in export
        assert "## Test Başlık" in export
        assert "Test içerik" in export


class TestNoteDataclasses:
    """Note ve Folder dataclass testleri."""
    
    def test_note_to_dict(self):
        """Note.to_dict çalışmalı."""
        from core.notes_manager import Note
        
        note = Note(
            id="test-id",
            title="Test",
            content="İçerik",
            folder_id=None,
            color="yellow",
            pinned=False,
            created_at="2024-01-01",
            updated_at="2024-01-01",
            tags=["tag1"]
        )
        
        d = note.to_dict()
        
        assert d["id"] == "test-id"
        assert d["title"] == "Test"
        assert d["tags"] == ["tag1"]
    
    def test_note_from_dict(self):
        """Note.from_dict çalışmalı."""
        from core.notes_manager import Note
        
        data = {
            "id": "test-id",
            "title": "Test",
            "content": "İçerik",
            "folder_id": None,
            "color": "yellow",
            "pinned": True,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "tags": []
        }
        
        note = Note.from_dict(data)
        
        assert note.id == "test-id"
        assert note.pinned is True
    
    def test_folder_to_dict(self):
        """Folder.to_dict çalışmalı."""
        from core.notes_manager import Folder
        
        folder = Folder(
            id="folder-id",
            name="Test Klasör",
            parent_id=None,
            color="blue",
            icon="📁",
            created_at="2024-01-01",
            updated_at="2024-01-01"
        )
        
        d = folder.to_dict()
        
        assert d["id"] == "folder-id"
        assert d["name"] == "Test Klasör"
    
    def test_folder_from_dict(self):
        """Folder.from_dict çalışmalı."""
        from core.notes_manager import Folder
        
        data = {
            "id": "folder-id",
            "name": "Test",
            "parent_id": "parent-id",
            "color": "red",
            "icon": "🎯",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01"
        }
        
        folder = Folder.from_dict(data)
        
        assert folder.id == "folder-id"
        assert folder.parent_id == "parent-id"


class TestNoteColor:
    """NoteColor enum testleri."""
    
    def test_all_colors_defined(self):
        """Tüm renkler tanımlı olmalı."""
        from core.notes_manager import NoteColor
        
        expected_colors = ["YELLOW", "GREEN", "BLUE", "PINK", "PURPLE", "ORANGE", "RED", "GRAY"]
        
        for color in expected_colors:
            assert hasattr(NoteColor, color)
    
    def test_color_values(self):
        """Renk değerleri lowercase olmalı."""
        from core.notes_manager import NoteColor
        
        assert NoteColor.YELLOW.value == "yellow"
        assert NoteColor.BLUE.value == "blue"


class TestSingletonInstance:
    """Singleton instance testi."""
    
    def test_notes_manager_singleton(self):
        """notes_manager singleton olmalı."""
        from core.notes_manager import notes_manager
        
        assert notes_manager is not None
        
        # Aynı instance
        from core.notes_manager import notes_manager as nm2
        assert notes_manager is nm2
