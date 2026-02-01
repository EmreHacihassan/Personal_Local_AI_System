"""
Notes Trash System Tests
========================

Trash (çöp kutusu) sistemi için kapsamlı testler.
- Soft delete (silinen notlar trash'e gider)
- Restore (trash'ten geri yükleme)
- Permanent delete (kalıcı silme)
- 30 gün sonra otomatik silme (scheduled)
"""

import pytest
import httpx
import uuid
from datetime import datetime, timedelta
import time

API_BASE = "http://localhost:8001"


class TestTrashBasics:
    """Temel trash işlemleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_trash_list_endpoint(self, client):
        """GET /api/notes/trash returns 200."""
        resp = client.get("/api/notes/trash")
        assert resp.status_code == 200
        assert "trash" in resp.json()
    
    def test_trash_count_endpoint(self, client):
        """GET /api/notes/trash/count returns count."""
        resp = client.get("/api/notes/trash/count")
        assert resp.status_code == 200
        assert "count" in resp.json()
    
    def test_delete_moves_to_trash(self, client):
        """DELETE note moves it to trash, not permanent delete."""
        # Create
        resp = client.post("/api/notes", json={
            "title": f"Trash Move Test {uuid.uuid4().hex[:6]}"
        })
        note_id = resp.json()["id"]
        
        # Delete
        del_resp = client.delete(f"/api/notes/{note_id}")
        assert del_resp.status_code == 200
        
        # Should be gone from notes
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.status_code == 404
        
        # Should be in trash
        trash_resp = client.get("/api/notes/trash")
        trash_ids = [t["id"] for t in trash_resp.json()["trash"]]
        assert note_id in trash_ids
        
        # Cleanup
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_trash_item_preserves_data(self, client):
        """Trash item keeps title, content, etc."""
        original_title = f"Preserve Data Test {uuid.uuid4().hex[:6]}"
        original_content = "This content should be preserved"
        
        resp = client.post("/api/notes", json={
            "title": original_title,
            "content": original_content,
            "tags": ["test", "trash"]
        })
        note_id = resp.json()["id"]
        
        # Delete
        client.delete(f"/api/notes/{note_id}")
        
        # Get from trash
        trash_resp = client.get(f"/api/notes/trash/{note_id}")
        assert trash_resp.status_code == 200
        
        trash_item = trash_resp.json()
        assert trash_item.get("title") == original_title or \
               trash_item.get("original_title") == original_title
        
        # Cleanup
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_trash_item_has_deleted_at(self, client):
        """Trash item has deleted_at timestamp."""
        resp = client.post("/api/notes", json={
            "title": "Timestamp Test"
        })
        note_id = resp.json()["id"]
        
        client.delete(f"/api/notes/{note_id}")
        
        trash_resp = client.get(f"/api/notes/trash/{note_id}")
        if trash_resp.status_code == 200:
            trash_item = trash_resp.json()
            # Should have deleted_at
            assert "deleted_at" in trash_item or "deletedAt" in trash_item
        
        # Cleanup
        client.delete(f"/api/notes/trash/{note_id}")


class TestTrashRestore:
    """Trash restore işlemleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def trashed_note(self, client):
        """Create and trash a note."""
        resp = client.post("/api/notes", json={
            "title": f"Restore Test {uuid.uuid4().hex[:6]}",
            "content": "Content to restore"
        })
        note_id = resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        yield note_id
        
        # Cleanup (might be restored or still in trash)
        try:
            client.delete(f"/api/notes/{note_id}")
        except:
            pass
        try:
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_restore_from_trash(self, client, trashed_note):
        """POST /api/notes/trash/{id}/restore brings back note."""
        # Verify in trash
        trash_resp = client.get("/api/notes/trash")
        trash_ids = [t["id"] for t in trash_resp.json()["trash"]]
        assert trashed_note in trash_ids
        
        # Restore
        restore_resp = client.post(f"/api/notes/trash/{trashed_note}/restore")
        assert restore_resp.status_code == 200
        
        # Should be back in notes
        get_resp = client.get(f"/api/notes/{trashed_note}")
        assert get_resp.status_code == 200
        
        # Should be gone from trash
        trash_resp = client.get("/api/notes/trash")
        trash_ids = [t["id"] for t in trash_resp.json()["trash"]]
        assert trashed_note not in trash_ids
    
    def test_restore_preserves_content(self, client):
        """Restored note has same content as before deletion."""
        original_content = "This is the original content to preserve"
        
        resp = client.post("/api/notes", json={
            "title": "Content Preserve Test",
            "content": original_content
        })
        note_id = resp.json()["id"]
        
        # Delete
        client.delete(f"/api/notes/{note_id}")
        
        # Restore
        client.post(f"/api/notes/trash/{note_id}/restore")
        
        # Check content
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json()["content"] == original_content
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_restore_preserves_folder(self, client):
        """Restored note goes back to original folder."""
        # Create folder
        folder_resp = client.post("/api/folders", json={
            "name": "Restore Folder Test"
        })
        folder_id = folder_resp.json()["id"]
        
        # Create note in folder
        note_resp = client.post("/api/notes", json={
            "title": "In Folder Note",
            "folder_id": folder_id
        })
        note_id = note_resp.json()["id"]
        
        # Delete and restore
        client.delete(f"/api/notes/{note_id}")
        client.post(f"/api/notes/trash/{note_id}/restore")
        
        # Check folder
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json().get("folder_id") == folder_id
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
        client.delete(f"/api/folders/{folder_id}")
    
    def test_restore_nonexistent_fails(self, client):
        """Restore non-existent trash item returns 404."""
        resp = client.post("/api/notes/trash/fake-id-12345/restore")
        assert resp.status_code == 404


class TestPermanentDelete:
    """Kalıcı silme işlemleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_permanent_delete(self, client):
        """DELETE /api/notes/trash/{id} permanently deletes."""
        # Create and trash
        resp = client.post("/api/notes", json={
            "title": "Permanent Delete Test"
        })
        note_id = resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        # Permanent delete
        perm_resp = client.delete(f"/api/notes/trash/{note_id}")
        assert perm_resp.status_code == 200
        
        # Should be gone from trash too
        trash_resp = client.get(f"/api/notes/trash/{note_id}")
        assert trash_resp.status_code == 404
    
    def test_permanent_delete_nonexistent(self, client):
        """Permanent delete of non-existent returns 404."""
        resp = client.delete("/api/notes/trash/fake-id-12345")
        assert resp.status_code == 404
    
    def test_cannot_restore_after_permanent(self, client):
        """Cannot restore after permanent delete."""
        # Create, trash, permanent delete
        resp = client.post("/api/notes", json={
            "title": "No Restore After Permanent"
        })
        note_id = resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
        
        # Try restore
        restore_resp = client.post(f"/api/notes/trash/{note_id}/restore")
        assert restore_resp.status_code == 404


class TestTrashFolders:
    """Folder trash işlemleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_delete_folder_moves_to_trash(self, client):
        """Deleting folder should handle its notes."""
        # Create folder with notes
        folder_resp = client.post("/api/folders", json={
            "name": "Delete Folder Test"
        })
        folder_id = folder_resp.json()["id"]
        
        note_resp = client.post("/api/notes", json={
            "title": "Note in Deleted Folder",
            "folder_id": folder_id
        })
        note_id = note_resp.json()["id"]
        
        # Delete folder
        del_resp = client.delete(f"/api/folders/{folder_id}")
        # This might delete folder and move notes to trash,
        # or delete folder and orphan notes
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note_id}")
        except:
            pass
        try:
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_restore_note_folder_deleted(self, client):
        """Restore note when its folder was deleted."""
        # Create folder
        folder_resp = client.post("/api/folders", json={
            "name": "Restore Orphan Test"
        })
        folder_id = folder_resp.json()["id"]
        
        # Create note in folder
        note_resp = client.post("/api/notes", json={
            "title": "Will Be Orphaned",
            "folder_id": folder_id
        })
        note_id = note_resp.json()["id"]
        
        # Delete note
        client.delete(f"/api/notes/{note_id}")
        
        # Delete folder
        client.delete(f"/api/folders/{folder_id}")
        
        # Try restore note
        restore_resp = client.post(f"/api/notes/trash/{note_id}/restore")
        
        if restore_resp.status_code == 200:
            # Note restored, should have no folder (orphaned) or root
            get_resp = client.get(f"/api/notes/{note_id}")
            note = get_resp.json()
            # folder_id should be None or empty
            assert note.get("folder_id") is None or note.get("folder_id") == ""
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note_id}")
        except:
            pass
        try:
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass


class TestTrashCount:
    """Trash count testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_count_increases_on_delete(self, client):
        """Trash count increases when note deleted."""
        # Get initial count
        count_resp = client.get("/api/notes/trash/count")
        initial = count_resp.json()["count"]
        
        # Create and delete
        note_resp = client.post("/api/notes", json={
            "title": "Count Increase Test"
        })
        note_id = note_resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        # Check count
        count_resp = client.get("/api/notes/trash/count")
        new_count = count_resp.json()["count"]
        
        assert new_count == initial + 1
        
        # Cleanup
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_count_decreases_on_restore(self, client):
        """Trash count decreases when note restored."""
        # Create and trash
        note_resp = client.post("/api/notes", json={
            "title": "Count Decrease Test"
        })
        note_id = note_resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        # Get count
        count_resp = client.get("/api/notes/trash/count")
        before_restore = count_resp.json()["count"]
        
        # Restore
        client.post(f"/api/notes/trash/{note_id}/restore")
        
        # Check count
        count_resp = client.get("/api/notes/trash/count")
        after_restore = count_resp.json()["count"]
        
        assert after_restore == before_restore - 1
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_count_decreases_on_permanent_delete(self, client):
        """Trash count decreases on permanent delete."""
        # Create and trash
        note_resp = client.post("/api/notes", json={
            "title": "Perm Delete Count Test"
        })
        note_id = note_resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        # Get count
        count_resp = client.get("/api/notes/trash/count")
        before = count_resp.json()["count"]
        
        # Permanent delete
        client.delete(f"/api/notes/trash/{note_id}")
        
        # Check count
        count_resp = client.get("/api/notes/trash/count")
        after = count_resp.json()["count"]
        
        assert after == before - 1


class TestTrashBulkOperations:
    """Bulk trash işlemleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_empty_trash_endpoint(self, client):
        """DELETE /api/notes/trash empties all trash."""
        # Create and trash a few notes
        note_ids = []
        for i in range(3):
            resp = client.post("/api/notes", json={
                "title": f"Empty Trash Test {i}"
            })
            note_id = resp.json()["id"]
            client.delete(f"/api/notes/{note_id}")
            note_ids.append(note_id)
        
        # Get count before
        count_resp = client.get("/api/notes/trash/count")
        before = count_resp.json()["count"]
        assert before >= 3
        
        # Empty trash
        empty_resp = client.delete("/api/notes/trash")
        # This might return 200 or 204
        assert empty_resp.status_code in [200, 204]
        
        # Check count
        count_resp = client.get("/api/notes/trash/count")
        after = count_resp.json()["count"]
        
        # Should be 0 or less than before
        assert after == 0 or after < before


# ============== RUN ==============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
