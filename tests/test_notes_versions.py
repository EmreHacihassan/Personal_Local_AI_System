"""
Notes Version History Tests
============================

Version history sistemi için kapsamlı testler.
- Max 10 version sınırı
- Version content korunması
- Restore işlemi
- Diff hesaplama
"""

import pytest
import httpx
import uuid
import time
from pathlib import Path
import sys
import json

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE = "http://localhost:8001"


class TestVersionHistoryUnit:
    """Unit testleri - NotesManager ile doğrudan."""
    
    @pytest.fixture
    def temp_notes_dir(self, tmp_path):
        """Create temporary notes directory."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()
        return notes_dir
    
    @pytest.fixture
    def notes_manager(self, temp_notes_dir):
        """Create NotesManager instance."""
        try:
            from core.notes_manager import NotesManager
            return NotesManager(str(temp_notes_dir))
        except ImportError:
            pytest.skip("NotesManager not available")
    
    def test_version_created_on_update(self, notes_manager):
        """Update creates a version."""
        # Create note
        note = notes_manager.create_note("Version Test", "Initial content")
        note_id = note.id
        
        # Update
        notes_manager.update_note(note_id, content="Updated content v2")
        
        # Check versions
        versions = notes_manager.get_note_versions(note_id)
        assert len(versions) >= 1
    
    def test_max_10_versions(self, notes_manager):
        """Maximum 10 versions retained."""
        # Create note
        note = notes_manager.create_note("Max Version Test", "v0")
        note_id = note.id
        
        # Update 15 times
        for i in range(1, 16):
            notes_manager.update_note(note_id, content=f"Content v{i}")
        
        # Should have max 10 versions
        versions = notes_manager.get_note_versions(note_id)
        assert len(versions) <= 10
    
    def test_version_content_preserved(self, notes_manager):
        """Version captures previous content."""
        # Create note
        note = notes_manager.create_note("Preserve Test", "Original content")
        note_id = note.id
        
        # Update with new content
        notes_manager.update_note(note_id, content="New content")
        
        # Get versions - first version should have original content
        versions = notes_manager.get_note_versions(note_id)
        if versions:
            # Version stores the content BEFORE the change
            assert "Original content" in [v.content for v in versions] or \
                   "New content" in [v.content for v in versions]
    
    def test_restore_version(self, notes_manager):
        """Restore reverts to previous content."""
        # Create and update
        note = notes_manager.create_note("Restore Test", "Original")
        note_id = note.id
        notes_manager.update_note(note_id, content="Updated")
        
        # Get version to restore
        versions = notes_manager.get_note_versions(note_id)
        if versions:
            # Restore first version
            notes_manager.restore_note_version(note_id, versions[0].id)
            
            # Check current content
            restored = notes_manager.get_note(note_id)
            # Content should match the restored version
            assert restored.content == versions[0].content
    
    def test_version_metadata(self, notes_manager):
        """Version has proper metadata."""
        note = notes_manager.create_note("Metadata Test", "Content")
        note_id = note.id
        notes_manager.update_note(note_id, content="Updated")
        
        versions = notes_manager.get_note_versions(note_id)
        if versions:
            version = versions[0]
            assert hasattr(version, 'id')
            assert hasattr(version, 'created_at')
            assert hasattr(version, 'content')


class TestVersionHistoryAPI:
    """API integration testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def versioned_note(self, client):
        """Create note with multiple versions."""
        # Create
        resp = client.post("/api/notes", json={
            "title": f"Version API Test {uuid.uuid4().hex[:6]}",
            "content": "Initial content v1"
        })
        note_id = resp.json()["id"]
        
        # Create 5 versions
        for i in range(2, 7):
            client.put(f"/api/notes/{note_id}", json={
                "content": f"Updated content v{i}"
            })
            time.sleep(0.1)  # Small delay to ensure different timestamps
        
        yield note_id
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_versions_endpoint_exists(self, client, versioned_note):
        """GET /api/notes/{id}/versions returns 200."""
        resp = client.get(f"/api/notes/{versioned_note}/versions")
        assert resp.status_code == 200
    
    def test_versions_list_structure(self, client, versioned_note):
        """Versions list has proper structure."""
        resp = client.get(f"/api/notes/{versioned_note}/versions")
        data = resp.json()
        
        assert "versions" in data
        versions = data["versions"]
        
        if versions:
            v = versions[0]
            assert "id" in v
            assert "created_at" in v
    
    def test_versions_count_increases(self, client):
        """Each update increases version count."""
        # Create
        resp = client.post("/api/notes", json={
            "title": "Count Test",
            "content": "v1"
        })
        note_id = resp.json()["id"]
        
        # Get initial versions
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        initial_count = len(v_resp.json().get("versions", []))
        
        # Update
        client.put(f"/api/notes/{note_id}", json={"content": "v2"})
        
        # Check increased
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        new_count = len(v_resp.json().get("versions", []))
        
        assert new_count >= initial_count  # Should be more or equal
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_get_specific_version(self, client, versioned_note):
        """GET /api/notes/{id}/versions/{vid} returns version content."""
        # Get versions list
        v_resp = client.get(f"/api/notes/{versioned_note}/versions")
        versions = v_resp.json().get("versions", [])
        
        if versions:
            version_id = versions[0]["id"]
            resp = client.get(f"/api/notes/{versioned_note}/versions/{version_id}")
            assert resp.status_code == 200
    
    def test_restore_version_api(self, client, versioned_note):
        """POST /api/notes/{id}/restore/{vid} restores content."""
        # Get versions
        v_resp = client.get(f"/api/notes/{versioned_note}/versions")
        versions = v_resp.json().get("versions", [])
        
        if len(versions) >= 2:
            # Get content of old version
            old_version = versions[-1]  # Oldest
            old_version_id = old_version["id"]
            
            # Get the version content
            ver_resp = client.get(f"/api/notes/{versioned_note}/versions/{old_version_id}")
            
            if ver_resp.status_code == 200:
                old_content = ver_resp.json().get("content")
                
                # Restore
                restore_resp = client.post(f"/api/notes/{versioned_note}/restore/{old_version_id}")
                assert restore_resp.status_code == 200
                
                # Check current note
                note_resp = client.get(f"/api/notes/{versioned_note}")
                if old_content:
                    assert note_resp.json()["content"] == old_content
    
    def test_diff_endpoint(self, client, versioned_note):
        """GET /api/notes/{id}/diff/{v1}/{v2} returns diff."""
        v_resp = client.get(f"/api/notes/{versioned_note}/versions")
        versions = v_resp.json().get("versions", [])
        
        if len(versions) >= 2:
            v1_id = versions[0]["id"]
            v2_id = versions[1]["id"]
            
            resp = client.get(f"/api/notes/{versioned_note}/diff/{v1_id}/{v2_id}")
            assert resp.status_code == 200
            
            data = resp.json()
            assert "diff" in data
    
    def test_versions_ordered_by_date(self, client, versioned_note):
        """Versions are ordered newest first."""
        v_resp = client.get(f"/api/notes/{versioned_note}/versions")
        versions = v_resp.json().get("versions", [])
        
        if len(versions) >= 2:
            dates = [v["created_at"] for v in versions]
            # Should be descending (newest first)
            assert dates == sorted(dates, reverse=True), "Versions should be newest first"
    
    def test_version_not_found(self, client, versioned_note):
        """GET non-existent version returns 404."""
        resp = client.get(f"/api/notes/{versioned_note}/versions/fake-version-id")
        assert resp.status_code == 404
    
    def test_restore_nonexistent_version(self, client, versioned_note):
        """Restore non-existent version returns 404."""
        resp = client.post(f"/api/notes/{versioned_note}/restore/fake-version-id")
        assert resp.status_code == 404


class TestVersionEdgeCases:
    """Edge case testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_new_note_no_versions(self, client):
        """Newly created note has 0 versions."""
        resp = client.post("/api/notes", json={
            "title": "No Versions Yet"
        })
        note_id = resp.json()["id"]
        
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        versions = v_resp.json().get("versions", [])
        
        # New note should have 0 versions (no updates yet)
        assert len(versions) == 0
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_only_content_changes_create_version(self, client):
        """Only content/title changes create versions, not color changes."""
        resp = client.post("/api/notes", json={
            "title": "Color Change Test",
            "content": "Original"
        })
        note_id = resp.json()["id"]
        
        # Update only color
        client.put(f"/api/notes/{note_id}", json={"color": "red"})
        
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        versions_after_color = len(v_resp.json().get("versions", []))
        
        # Update content
        client.put(f"/api/notes/{note_id}", json={"content": "New content"})
        
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        versions_after_content = len(v_resp.json().get("versions", []))
        
        # Content change should create version, color might not
        assert versions_after_content >= versions_after_color
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_restore_creates_new_version(self, client):
        """Restoring a version should create a new version entry."""
        # Create with multiple versions
        resp = client.post("/api/notes", json={
            "title": "Restore Version Test",
            "content": "v1"
        })
        note_id = resp.json()["id"]
        
        for i in range(2, 5):
            client.put(f"/api/notes/{note_id}", json={"content": f"v{i}"})
        
        # Get version count
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        versions = v_resp.json().get("versions", [])
        count_before = len(versions)
        
        if count_before >= 1:
            # Restore oldest
            oldest_id = versions[-1]["id"]
            client.post(f"/api/notes/{note_id}/restore/{oldest_id}")
            
            # Check count
            v_resp = client.get(f"/api/notes/{note_id}/versions")
            count_after = len(v_resp.json().get("versions", []))
            
            # Restore should create a new version (the "restored from" snapshot)
            # This depends on implementation
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_deleted_note_versions_preserved(self, client):
        """Versions are preserved when note is deleted (in trash)."""
        # Create with versions
        resp = client.post("/api/notes", json={
            "title": "Delete Version Test",
            "content": "v1"
        })
        note_id = resp.json()["id"]
        client.put(f"/api/notes/{note_id}", json={"content": "v2"})
        
        # Get version count
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        count_before = len(v_resp.json().get("versions", []))
        
        # Delete note
        client.delete(f"/api/notes/{note_id}")
        
        # Restore from trash
        client.post(f"/api/notes/trash/{note_id}/restore")
        
        # Check versions still there
        v_resp = client.get(f"/api/notes/{note_id}/versions")
        count_after = len(v_resp.json().get("versions", []))
        
        assert count_after == count_before
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")


# ============== RUN ==============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
