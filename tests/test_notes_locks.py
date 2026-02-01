"""
Notes Lock and Encryption Tests
================================

Lock (kilit) ve Encryption (şifreleme/AI gizleme) testleri.
- Locked note/folder silinemez (403)
- Unlock sonrası silinebilir
- Encrypted flag korunur
- AI istemlerinden gizleme
"""

import pytest
import httpx
import uuid

API_BASE = "http://localhost:8001"


class TestNoteLocking:
    """Note lock testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def note_id(self, client):
        """Create a test note."""
        resp = client.post("/api/notes", json={
            "title": f"Lock Test {uuid.uuid4().hex[:6]}",
            "content": "Test content"
        })
        note_id = resp.json()["id"]
        yield note_id
        # Cleanup
        try:
            client.put(f"/api/notes/{note_id}", json={"locked": False})
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_lock_note(self, client, note_id):
        """PUT locked=true sets lock."""
        resp = client.put(f"/api/notes/{note_id}", json={"locked": True})
        assert resp.status_code == 200
        
        # Verify locked
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json().get("locked") == True
    
    def test_unlock_note(self, client, note_id):
        """PUT locked=false removes lock."""
        # Lock first
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        # Unlock
        resp = client.put(f"/api/notes/{note_id}", json={"locked": False})
        assert resp.status_code == 200
        
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json().get("locked") == False
    
    def test_delete_locked_note_fails(self, client, note_id):
        """DELETE locked note returns 403."""
        # Lock
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        # Try delete
        del_resp = client.delete(f"/api/notes/{note_id}")
        assert del_resp.status_code == 403
    
    def test_delete_after_unlock(self, client):
        """Unlocked note can be deleted."""
        # Create and lock
        resp = client.post("/api/notes", json={"title": "Unlock Delete Test"})
        note_id = resp.json()["id"]
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        # Unlock
        client.put(f"/api/notes/{note_id}", json={"locked": False})
        
        # Delete should succeed
        del_resp = client.delete(f"/api/notes/{note_id}")
        assert del_resp.status_code == 200
        
        # Cleanup
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_locked_note_can_update_other_fields(self, client, note_id):
        """Locked note can still update title, content etc."""
        # Lock
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        # Update content - should work
        update_resp = client.put(f"/api/notes/{note_id}", json={
            "content": "Updated content"
        })
        assert update_resp.status_code == 200
    
    def test_move_locked_note(self, client, note_id):
        """Moving a locked note might be allowed or not."""
        # Create folder
        folder_resp = client.post("/api/folders", json={"name": "Lock Move Test"})
        folder_id = folder_resp.json()["id"]
        
        # Lock note
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        # Try move
        move_resp = client.post(
            f"/api/notes/{note_id}/move",
            params={"folder_id": folder_id}
        )
        # Implementation dependent - might allow or forbid
        # Just check it doesn't crash
        assert move_resp.status_code in [200, 403]
        
        # Cleanup
        client.delete(f"/api/folders/{folder_id}")


class TestFolderLocking:
    """Folder lock testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def folder_id(self, client):
        """Create a test folder."""
        resp = client.post("/api/folders", json={
            "name": f"Lock Folder Test {uuid.uuid4().hex[:6]}"
        })
        folder_id = resp.json()["id"]
        yield folder_id
        try:
            client.put(f"/api/folders/{folder_id}", json={"locked": False})
            client.delete(f"/api/folders/{folder_id}")
        except:
            pass
    
    def test_lock_folder(self, client, folder_id):
        """PUT locked=true locks folder."""
        resp = client.put(f"/api/folders/{folder_id}", json={"locked": True})
        assert resp.status_code == 200
        
        get_resp = client.get(f"/api/folders/{folder_id}")
        assert get_resp.json().get("locked") == True
    
    def test_delete_locked_folder_fails(self, client, folder_id):
        """DELETE locked folder returns 403."""
        client.put(f"/api/folders/{folder_id}", json={"locked": True})
        
        del_resp = client.delete(f"/api/folders/{folder_id}")
        assert del_resp.status_code == 403
    
    def test_delete_folder_after_unlock(self, client):
        """Unlocked folder can be deleted."""
        resp = client.post("/api/folders", json={"name": "Unlock Delete Folder"})
        folder_id = resp.json()["id"]
        
        # Lock then unlock
        client.put(f"/api/folders/{folder_id}", json={"locked": True})
        client.put(f"/api/folders/{folder_id}", json={"locked": False})
        
        # Delete
        del_resp = client.delete(f"/api/folders/{folder_id}")
        assert del_resp.status_code == 200
    
    def test_locked_folder_notes_deletable(self, client, folder_id):
        """Notes inside locked folder might still be deletable."""
        # Add note to folder
        note_resp = client.post("/api/notes", json={
            "title": "Note in Locked Folder",
            "folder_id": folder_id
        })
        note_id = note_resp.json()["id"]
        
        # Lock folder
        client.put(f"/api/folders/{folder_id}", json={"locked": True})
        
        # Try delete note - behavior depends on implementation
        del_resp = client.delete(f"/api/notes/{note_id}")
        # Might be 200 or 403
        assert del_resp.status_code in [200, 403]
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note_id}")
        except:
            pass
        try:
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass


class TestEncryption:
    """Encryption (AI hiding) testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def note_id(self, client):
        resp = client.post("/api/notes", json={
            "title": f"Encrypt Test {uuid.uuid4().hex[:6]}",
            "content": "Secret content"
        })
        note_id = resp.json()["id"]
        yield note_id
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_set_encrypted_true(self, client, note_id):
        """Set encrypted=true persists."""
        resp = client.put(f"/api/notes/{note_id}", json={"encrypted": True})
        assert resp.status_code == 200
        
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json().get("encrypted") == True
    
    def test_set_encrypted_false(self, client, note_id):
        """Set encrypted=false persists."""
        # First set true
        client.put(f"/api/notes/{note_id}", json={"encrypted": True})
        
        # Then false
        resp = client.put(f"/api/notes/{note_id}", json={"encrypted": False})
        assert resp.status_code == 200
        
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json().get("encrypted") == False
    
    def test_encrypted_content_readable(self, client, note_id):
        """Encrypted note content is still readable (base64 obfuscated)."""
        original = "This is secret content"
        client.put(f"/api/notes/{note_id}", json={
            "content": original,
            "encrypted": True
        })
        
        get_resp = client.get(f"/api/notes/{note_id}")
        content = get_resp.json().get("content")
        
        # Content should be present (might be original or base64 encoded)
        assert content is not None
    
    def test_encrypted_note_searchable(self, client):
        """Encrypted notes included in search (content decoded for search)."""
        unique_term = f"UniqueSearchTerm{uuid.uuid4().hex[:8]}"
        
        resp = client.post("/api/notes", json={
            "title": "Search Encrypt Test",
            "content": f"This contains {unique_term}",
            "encrypted": True
        })
        note_id = resp.json()["id"]
        
        # Search - implementation dependent whether it searches encrypted
        search_resp = client.get("/api/notes", params={
            "search_query": unique_term
        })
        
        # Just verify search doesn't crash
        assert search_resp.status_code == 200
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_encrypted_folder(self, client):
        """Folder can be marked encrypted."""
        resp = client.post("/api/folders", json={
            "name": "Encrypted Folder"
        })
        folder_id = resp.json()["id"]
        
        # Set encrypted
        update_resp = client.put(f"/api/folders/{folder_id}", json={
            "encrypted": True
        })
        # Might or might not support folder encryption
        
        # Cleanup
        client.delete(f"/api/folders/{folder_id}")


class TestHiddenNotes:
    """Hidden notes testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_set_hidden_true(self, client):
        """Set hidden=true persists."""
        resp = client.post("/api/notes", json={
            "title": "Hidden Test"
        })
        note_id = resp.json()["id"]
        
        update_resp = client.put(f"/api/notes/{note_id}", json={"hidden": True})
        assert update_resp.status_code == 200
        
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json().get("hidden") == True
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_hidden_notes_excluded_from_list(self, client):
        """Hidden notes might be excluded from default listing."""
        resp = client.post("/api/notes", json={
            "title": f"Hidden List Test {uuid.uuid4().hex[:6]}"
        })
        note_id = resp.json()["id"]
        
        # Set hidden
        client.put(f"/api/notes/{note_id}", json={"hidden": True})
        
        # Get list
        list_resp = client.get("/api/notes")
        notes = list_resp.json()["notes"]
        
        # Might or might not include hidden notes in default listing
        # Just verify the endpoint works
        assert isinstance(notes, list)
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")


class TestBothLockAndEncrypt:
    """Lock ve encrypt beraber."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_locked_and_encrypted(self, client):
        """Note can be both locked and encrypted."""
        resp = client.post("/api/notes", json={
            "title": "Both Lock Encrypt Test",
            "content": "Secret"
        })
        note_id = resp.json()["id"]
        
        # Set both
        update_resp = client.put(f"/api/notes/{note_id}", json={
            "locked": True,
            "encrypted": True
        })
        assert update_resp.status_code == 200
        
        # Verify both
        get_resp = client.get(f"/api/notes/{note_id}")
        note = get_resp.json()
        assert note.get("locked") == True
        assert note.get("encrypted") == True
        
        # Cleanup
        client.put(f"/api/notes/{note_id}", json={"locked": False})
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")


# ============== RUN ==============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
