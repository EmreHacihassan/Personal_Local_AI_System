"""
Notes API Endpoint Integration Tests
=====================================

FastAPI endpoint testleri - tüm CRUD, folder, version, trash endpointleri.
Backend çalışırken: pytest tests/test_notes_api.py -v
"""

import pytest
import httpx
import uuid
from datetime import datetime

# API Base URL
API_BASE = "http://localhost:8001"


class TestNotesAPI:
    """Notes CRUD API testleri."""
    
    @pytest.fixture
    def client(self):
        """HTTP client for API calls."""
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def test_note_id(self, client):
        """Create a test note and return its ID, cleanup after test."""
        response = client.post("/api/notes", json={
            "title": f"Test Note {uuid.uuid4().hex[:8]}",
            "content": "Test content for API testing",
            "color": "blue",
            "tags": ["test", "api"]
        })
        assert response.status_code == 200
        note_id = response.json()["id"]
        yield note_id
        # Cleanup - delete note
        try:
            client.delete(f"/api/notes/{note_id}")
            # Also empty from trash
            trash_resp = client.get("/api/notes/trash")
            if trash_resp.status_code == 200:
                for item in trash_resp.json().get("trash", []):
                    if item.get("id") == note_id:
                        client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    @pytest.fixture
    def test_folder_id(self, client):
        """Create a test folder and return its ID, cleanup after test."""
        response = client.post("/api/folders", json={
            "name": f"Test Folder {uuid.uuid4().hex[:8]}",
            "color": "green",
            "icon": "📁"
        })
        assert response.status_code == 200
        folder_id = response.json()["id"]
        yield folder_id
        # Cleanup
        try:
            client.delete(f"/api/folders/{folder_id}")
        except:
            pass
    
    # ============== NOTES CRUD ==============
    
    def test_list_notes(self, client):
        """GET /api/notes - List all notes."""
        response = client.get("/api/notes")
        assert response.status_code == 200
        data = response.json()
        assert "notes" in data
        assert isinstance(data["notes"], list)
    
    def test_create_note_minimal(self, client):
        """POST /api/notes - Create with only title."""
        response = client.post("/api/notes", json={
            "title": f"Minimal Note {uuid.uuid4().hex[:8]}"
        })
        assert response.status_code == 200
        note = response.json()
        assert "id" in note
        assert note["title"].startswith("Minimal Note")
        # Cleanup
        client.delete(f"/api/notes/{note['id']}")
    
    def test_create_note_full(self, client):
        """POST /api/notes - Create with all fields."""
        response = client.post("/api/notes", json={
            "title": "Full Note Test",
            "content": "# Heading\n\nParagraph content",
            "color": "purple",
            "pinned": True,
            "tags": ["important", "test"]
        })
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "Full Note Test"
        assert note["pinned"] == True
        assert "important" in note.get("tags", [])
        # Cleanup
        client.delete(f"/api/notes/{note['id']}")
    
    def test_create_note_invalid_empty_title(self, client):
        """POST /api/notes - Empty title should fail."""
        response = client.post("/api/notes", json={
            "title": ""
        })
        # Should return 422 validation error
        assert response.status_code == 422
    
    def test_get_note(self, client, test_note_id):
        """GET /api/notes/{id} - Get single note."""
        response = client.get(f"/api/notes/{test_note_id}")
        assert response.status_code == 200
        note = response.json()
        assert note["id"] == test_note_id
    
    def test_get_note_not_found(self, client):
        """GET /api/notes/{id} - Non-existent note returns 404."""
        response = client.get("/api/notes/nonexistent-id-12345")
        assert response.status_code == 404
    
    def test_update_note_title(self, client, test_note_id):
        """PUT /api/notes/{id} - Update title."""
        response = client.put(f"/api/notes/{test_note_id}", json={
            "title": "Updated Title"
        })
        assert response.status_code == 200
        note = response.json()
        assert note["title"] == "Updated Title"
    
    def test_update_note_content(self, client, test_note_id):
        """PUT /api/notes/{id} - Update content."""
        new_content = "# New Content\n\nUpdated paragraph"
        response = client.put(f"/api/notes/{test_note_id}", json={
            "content": new_content
        })
        assert response.status_code == 200
        note = response.json()
        assert note["content"] == new_content
    
    def test_update_note_color(self, client, test_note_id):
        """PUT /api/notes/{id} - Update color."""
        response = client.put(f"/api/notes/{test_note_id}", json={
            "color": "red"
        })
        assert response.status_code == 200
        note = response.json()
        assert note["color"] == "red"
    
    def test_update_note_not_found(self, client):
        """PUT /api/notes/{id} - Non-existent note returns 404."""
        response = client.put("/api/notes/nonexistent-id-12345", json={
            "title": "Test"
        })
        assert response.status_code == 404
    
    def test_delete_note(self, client):
        """DELETE /api/notes/{id} - Delete note (moves to trash)."""
        # Create a note first
        create_resp = client.post("/api/notes", json={
            "title": "Note to Delete"
        })
        note_id = create_resp.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/notes/{note_id}")
        assert response.status_code == 200
        
        # Verify it's gone from notes list
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.status_code == 404
        
        # Verify it's in trash (using original_note.id)
        trash_resp = client.get("/api/notes/trash")
        trash_data = trash_resp.json().get("trash", [])
        trash_original_ids = [item.get("original_note", {}).get("id") for item in trash_data]
        assert note_id in trash_original_ids
        
        # Cleanup from trash (can use original note id)
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_delete_note_not_found(self, client):
        """DELETE /api/notes/{id} - Non-existent note returns 404."""
        response = client.delete("/api/notes/nonexistent-id-12345")
        assert response.status_code == 404
    
    def test_pin_toggle(self, client, test_note_id):
        """POST /api/notes/{id}/pin - Toggle pin status."""
        # Get initial state
        note = client.get(f"/api/notes/{test_note_id}").json()
        initial_pinned = note.get("pinned", False)
        
        # Toggle
        response = client.post(f"/api/notes/{test_note_id}/pin")
        assert response.status_code == 200
        assert response.json()["pinned"] != initial_pinned
    
    def test_move_note_to_folder(self, client, test_note_id, test_folder_id):
        """POST /api/notes/{id}/move - Move note to folder."""
        response = client.post(
            f"/api/notes/{test_note_id}/move",
            params={"folder_id": test_folder_id}
        )
        assert response.status_code == 200
        note = response.json()
        assert note.get("folder_id") == test_folder_id
    
    def test_notes_search(self, client, test_note_id):
        """GET /api/notes?search_query= - Search notes."""
        response = client.get("/api/notes", params={
            "search_query": "Test content"
        })
        assert response.status_code == 200
        notes = response.json()["notes"]
        # Should find our test note
        found = any(n["id"] == test_note_id for n in notes)
        assert found
    
    def test_notes_stats(self, client):
        """GET /api/notes/stats - Get statistics."""
        response = client.get("/api/notes/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "total_notes" in stats
        assert "total_folders" in stats


class TestFoldersAPI:
    """Folders API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def test_folder_id(self, client):
        response = client.post("/api/folders", json={
            "name": f"Test Folder {uuid.uuid4().hex[:8]}"
        })
        folder_id = response.json()["id"]
        yield folder_id
        try:
            client.delete(f"/api/folders/{folder_id}")
        except:
            pass
    
    def test_list_folders(self, client):
        """GET /api/folders - List root folders."""
        response = client.get("/api/folders")
        assert response.status_code == 200
        data = response.json()
        assert "folders" in data
    
    def test_list_all_folders(self, client):
        """GET /api/folders/all - List ALL folders."""
        response = client.get("/api/folders/all")
        assert response.status_code == 200
        data = response.json()
        assert "folders" in data
    
    def test_create_folder(self, client):
        """POST /api/folders - Create folder."""
        response = client.post("/api/folders", json={
            "name": "New API Folder",
            "color": "blue",
            "icon": "📂"
        })
        assert response.status_code == 200
        folder = response.json()
        assert folder["name"] == "New API Folder"
        # Cleanup
        client.delete(f"/api/folders/{folder['id']}")
    
    def test_create_nested_folder(self, client, test_folder_id):
        """POST /api/folders - Create nested folder."""
        response = client.post("/api/folders", json={
            "name": "Child Folder",
            "parent_id": test_folder_id
        })
        assert response.status_code == 200
        folder = response.json()
        assert folder.get("parent_id") == test_folder_id
        # Cleanup
        client.delete(f"/api/folders/{folder['id']}")
    
    def test_get_folder(self, client, test_folder_id):
        """GET /api/folders/{id} - Get single folder."""
        response = client.get(f"/api/folders/{test_folder_id}")
        assert response.status_code == 200
        folder = response.json()
        assert folder["id"] == test_folder_id
    
    def test_get_folder_path(self, client, test_folder_id):
        """GET /api/folders/{id}/path - Get breadcrumb path."""
        response = client.get(f"/api/folders/{test_folder_id}/path")
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert isinstance(data["path"], list)
    
    def test_update_folder(self, client, test_folder_id):
        """PUT /api/folders/{id} - Update folder."""
        response = client.put(f"/api/folders/{test_folder_id}", json={
            "name": "Renamed Folder",
            "color": "red"
        })
        assert response.status_code == 200
        folder = response.json()
        assert folder["name"] == "Renamed Folder"
    
    def test_delete_folder(self, client):
        """DELETE /api/folders/{id} - Delete folder."""
        # Create folder
        create_resp = client.post("/api/folders", json={
            "name": "Folder to Delete"
        })
        folder_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/folders/{folder_id}")
        assert response.status_code == 200
        
        # Verify gone
        get_resp = client.get(f"/api/folders/{folder_id}")
        assert get_resp.status_code == 404


class TestVersionHistoryAPI:
    """Version History API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def test_note_with_versions(self, client):
        """Create note and update it multiple times to create versions."""
        # Create
        response = client.post("/api/notes", json={
            "title": "Version Test Note",
            "content": "Initial content v1"
        })
        note_id = response.json()["id"]
        
        # Update multiple times to create versions
        for i in range(2, 5):
            client.put(f"/api/notes/{note_id}", json={
                "content": f"Updated content v{i}"
            })
        
        yield note_id
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_list_versions(self, client, test_note_with_versions):
        """GET /api/notes/{id}/versions - List versions."""
        response = client.get(f"/api/notes/{test_note_with_versions}/versions")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        # Should have at least some versions
        assert len(data["versions"]) >= 1
    
    def test_get_specific_version(self, client, test_note_with_versions):
        """GET /api/notes/{id}/versions/{vid} - Get specific version."""
        # First get versions list
        versions_resp = client.get(f"/api/notes/{test_note_with_versions}/versions")
        versions = versions_resp.json()["versions"]
        
        if versions:
            version_id = versions[0]["version_id"]  # Use version_id, not id
            response = client.get(f"/api/notes/{test_note_with_versions}/versions/{version_id}")
            assert response.status_code == 200
    
    def test_restore_version(self, client, test_note_with_versions):
        """POST /api/notes/{id}/restore/{vid} - Restore version."""
        # Get versions
        versions_resp = client.get(f"/api/notes/{test_note_with_versions}/versions")
        versions = versions_resp.json()["versions"]
        
        if len(versions) >= 2:
            version_id = versions[-1]["version_id"]  # Get oldest version, use version_id
            response = client.post(f"/api/notes/{test_note_with_versions}/restore/{version_id}")
            assert response.status_code == 200
    
    def test_version_diff(self, client, test_note_with_versions):
        """GET /api/notes/{id}/diff/{v1}/{v2} - Get diff."""
        versions_resp = client.get(f"/api/notes/{test_note_with_versions}/versions")
        versions = versions_resp.json()["versions"]
        
        if len(versions) >= 2:
            v1 = versions[0]["version_id"]  # Use version_id
            v2 = versions[1]["version_id"]  # Use version_id
            response = client.get(f"/api/notes/{test_note_with_versions}/diff/{v1}/{v2}")
            assert response.status_code == 200
            data = response.json()
            # API returns content_diff, not diff
            assert "content_diff" in data or "diff" in data


class TestTrashAPI:
    """Trash System API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def trashed_note_id(self, client):
        """Create and delete a note to put it in trash."""
        response = client.post("/api/notes", json={
            "title": "Note for Trash Test",
            "content": "This will be deleted"
        })
        note_id = response.json()["id"]
        
        # Delete to move to trash
        client.delete(f"/api/notes/{note_id}")
        
        yield note_id
        
        # Cleanup from trash
        try:
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_list_trash(self, client, trashed_note_id):
        """GET /api/notes/trash - List trashed notes."""
        response = client.get("/api/notes/trash")
        assert response.status_code == 200
        data = response.json()
        assert "trash" in data
        # Our note should be there (check original_note.id)
        trash_original_ids = [item.get("original_note", {}).get("id") for item in data["trash"]]
        assert trashed_note_id in trash_original_ids
    
    def test_trash_count(self, client, trashed_note_id):
        """GET /api/notes/trash/count - Count trashed notes."""
        response = client.get("/api/notes/trash/count")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert data["count"] >= 1
    
    def test_get_trash_item(self, client, trashed_note_id):
        """GET /api/notes/trash/{id} - Get specific trash item."""
        response = client.get(f"/api/notes/trash/{trashed_note_id}")
        assert response.status_code == 200
    
    def test_restore_from_trash(self, client):
        """POST /api/notes/trash/{id}/restore - Restore note."""
        # Create and delete
        create_resp = client.post("/api/notes", json={
            "title": "Restore Test Note"
        })
        note_id = create_resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        # Restore
        response = client.post(f"/api/notes/trash/{note_id}/restore")
        assert response.status_code == 200
        
        # Verify restored
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.status_code == 200
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_permanent_delete(self, client):
        """DELETE /api/notes/trash/{id} - Permanent delete."""
        # Create and delete
        create_resp = client.post("/api/notes", json={
            "title": "Permanent Delete Test"
        })
        note_id = create_resp.json()["id"]
        client.delete(f"/api/notes/{note_id}")
        
        # Permanent delete (using original note id)
        response = client.delete(f"/api/notes/trash/{note_id}")
        assert response.status_code == 200
        
        # Verify gone from trash (check original_note.id)
        trash_resp = client.get("/api/notes/trash")
        trash_original_ids = [item.get("original_note", {}).get("id") for item in trash_resp.json().get("trash", [])]
        assert note_id not in trash_original_ids


class TestLockAPI:
    """Lock functionality API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def locked_note_id(self, client):
        """Create a locked note."""
        response = client.post("/api/notes", json={
            "title": "Locked Note Test"
        })
        note_id = response.json()["id"]
        
        # Lock it
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        yield note_id
        
        # Unlock and cleanup
        try:
            client.put(f"/api/notes/{note_id}", json={"locked": False})
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    @pytest.fixture
    def locked_folder_id(self, client):
        """Create a locked folder."""
        response = client.post("/api/folders", json={
            "name": "Locked Folder Test"
        })
        folder_id = response.json()["id"]
        
        # Lock it
        client.put(f"/api/folders/{folder_id}", json={"locked": True})
        
        yield folder_id
        
        # Unlock and cleanup
        try:
            client.put(f"/api/folders/{folder_id}", json={"locked": False})
            client.delete(f"/api/folders/{folder_id}")
        except:
            pass
    
    def test_delete_locked_note_fails(self, client, locked_note_id):
        """DELETE locked note should return 403."""
        response = client.delete(f"/api/notes/{locked_note_id}")
        assert response.status_code == 403
    
    def test_delete_locked_folder_fails(self, client, locked_folder_id):
        """DELETE locked folder should return 403."""
        response = client.delete(f"/api/folders/{locked_folder_id}")
        assert response.status_code == 403
    
    def test_unlock_then_delete_note(self, client):
        """Unlock note, then delete should succeed."""
        # Create and lock
        create_resp = client.post("/api/notes", json={"title": "Unlock Test"})
        note_id = create_resp.json()["id"]
        client.put(f"/api/notes/{note_id}", json={"locked": True})
        
        # Try delete - should fail
        del_resp = client.delete(f"/api/notes/{note_id}")
        assert del_resp.status_code == 403
        
        # Unlock
        client.put(f"/api/notes/{note_id}", json={"locked": False})
        
        # Delete - should succeed
        del_resp = client.delete(f"/api/notes/{note_id}")
        assert del_resp.status_code == 200
        
        # Cleanup
        client.delete(f"/api/notes/trash/{note_id}")


class TestEncryptionAPI:
    """Encryption (AI hiding) API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_set_encrypted_flag(self, client):
        """PUT encrypted=true should be saved."""
        # Create note
        create_resp = client.post("/api/notes", json={
            "title": "Encryption Test",
            "content": "Secret content"
        })
        note_id = create_resp.json()["id"]
        
        # Set encrypted
        update_resp = client.put(f"/api/notes/{note_id}", json={
            "encrypted": True
        })
        assert update_resp.status_code == 200
        
        # Verify
        get_resp = client.get(f"/api/notes/{note_id}")
        note = get_resp.json()
        assert note.get("encrypted") == True
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")


class TestGraphAPI:
    """Graph/Mind Map API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_get_graph(self, client):
        """GET /api/notes/graph - Get graph data."""
        response = client.get("/api/notes/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
    
    def test_graph_stats(self, client):
        """GET /api/notes/graph/stats - Get graph stats."""
        response = client.get("/api/notes/graph/stats")
        assert response.status_code == 200
    
    def test_central_notes(self, client):
        """GET /api/notes/graph/central - Most connected notes."""
        response = client.get("/api/notes/graph/central")
        assert response.status_code == 200
    
    def test_orphan_notes(self, client):
        """GET /api/notes/graph/orphans - Notes with no connections."""
        response = client.get("/api/notes/graph/orphans")
        assert response.status_code == 200
    
    def test_graph_clusters(self, client):
        """GET /api/notes/graph/clusters - Note clusters."""
        response = client.get("/api/notes/graph/clusters")
        assert response.status_code == 200


class TestTemplatesAPI:
    """Templates API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_get_templates(self, client):
        """GET /api/notes/templates - Get available templates."""
        response = client.get("/api/notes/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data


class TestGraphLinksAPI:
    """Graph Links ve Backlinks API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def linked_notes(self, client):
        """Create two linked notes."""
        # Create note 1
        resp1 = client.post("/api/notes", json={
            "title": "Link Source Note",
            "content": "This links to [[Link Target Note]]"
        })
        note1_id = resp1.json()["id"]
        
        # Create note 2
        resp2 = client.post("/api/notes", json={
            "title": "Link Target Note", 
            "content": "This is the target"
        })
        note2_id = resp2.json()["id"]
        
        yield (note1_id, note2_id)
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note1_id}")
            client.delete(f"/api/notes/{note2_id}")
            client.delete(f"/api/notes/trash/{note1_id}")
            client.delete(f"/api/notes/trash/{note2_id}")
        except:
            pass
    
    def test_get_note_links(self, client, linked_notes):
        """GET /api/notes/{id}/links - Get outgoing links."""
        note1_id, _ = linked_notes
        response = client.get(f"/api/notes/{note1_id}/links")
        assert response.status_code == 200
    
    def test_get_note_backlinks(self, client, linked_notes):
        """GET /api/notes/{id}/backlinks - Get incoming links."""
        _, note2_id = linked_notes
        response = client.get(f"/api/notes/{note2_id}/backlinks")
        assert response.status_code == 200
    
    def test_graph_path(self, client):
        """GET /api/notes/graph/path - Find path between notes."""
        response = client.get("/api/notes/graph/path", params={
            "source_id": "nonexistent1",
            "target_id": "nonexistent2"
        })
        # Should return 200 even if no path found, or 404/500 for invalid IDs
        assert response.status_code in [200, 404, 500]
    
    def test_graph_connections(self, client, linked_notes):
        """GET /api/notes/graph/connections - Get all connections."""
        response = client.get("/api/notes/graph/connections")
        assert response.status_code == 200


class TestVersionDeleteAPI:
    """Version Delete API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def note_with_versions(self, client):
        """Create a note with multiple versions."""
        # Create
        resp = client.post("/api/notes", json={
            "title": "Version Delete Test",
            "content": "v1"
        })
        note_id = resp.json()["id"]
        
        # Create versions by updating
        client.put(f"/api/notes/{note_id}", json={"content": "v2"})
        client.put(f"/api/notes/{note_id}", json={"content": "v3"})
        
        yield note_id
        
        # Cleanup
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_delete_single_version(self, client, note_with_versions):
        """DELETE /api/notes/{id}/versions/{vid} - Delete specific version."""
        note_id = note_with_versions
        
        # Get versions
        versions_resp = client.get(f"/api/notes/{note_id}/versions")
        versions = versions_resp.json().get("versions", [])
        
        if versions:
            version_id = versions[0]["version_id"]
            response = client.delete(f"/api/notes/{note_id}/versions/{version_id}")
            assert response.status_code == 200
    
    def test_delete_all_versions(self, client, note_with_versions):
        """DELETE /api/notes/{id}/versions - Delete all versions."""
        note_id = note_with_versions
        response = client.delete(f"/api/notes/{note_id}/versions")
        assert response.status_code == 200
        
        # Verify versions are gone
        versions_resp = client.get(f"/api/notes/{note_id}/versions")
        versions = versions_resp.json().get("versions", [])
        assert len(versions) == 0


class TestNoteDetailsAPI:
    """Note Details API testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def test_note_id(self, client):
        resp = client.post("/api/notes", json={
            "title": "Details Test Note",
            "content": "Content for details"
        })
        note_id = resp.json()["id"]
        yield note_id
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_get_note_details(self, client, test_note_id):
        """GET /api/notes/{id}/details - Get detailed note info."""
        response = client.get(f"/api/notes/{test_note_id}/details")
        assert response.status_code == 200
        data = response.json()
        # Should have note data
        assert "id" in data or "title" in data


class TestAIEndpoints:
    """AI Endpoint testleri - Ollama bağımlılığı var."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=60.0)
    
    @pytest.fixture
    def test_note_id(self, client):
        resp = client.post("/api/notes", json={
            "title": "AI Test Note",
            "content": "This is a test note with some content for AI processing."
        })
        note_id = resp.json()["id"]
        yield note_id
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_summarize_note(self, client, test_note_id):
        """POST /api/notes/{id}/summarize - AI summarization."""
        response = client.post(f"/api/notes/{test_note_id}/summarize")
        assert response.status_code in [200, 503]  # 503 if Ollama not available
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_suggest_tags(self, client, test_note_id):
        """POST /api/notes/{id}/suggest-tags - AI tag suggestion."""
        response = client.post(f"/api/notes/{test_note_id}/suggest-tags")
        assert response.status_code in [200, 503]
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_get_related_notes(self, client, test_note_id):
        """GET /api/notes/{id}/related - Find related notes."""
        response = client.get(f"/api/notes/{test_note_id}/related")
        assert response.status_code in [200, 503]
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_enrich_note(self, client, test_note_id):
        """POST /api/notes/{id}/enrich - AI enrichment."""
        response = client.post(f"/api/notes/{test_note_id}/enrich")
        assert response.status_code in [200, 503]
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_generate_flashcards(self, client, test_note_id):
        """POST /api/notes/{id}/flashcards - Generate flashcards."""
        response = client.post(f"/api/notes/{test_note_id}/flashcards")
        assert response.status_code in [200, 503]
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_ask_notes(self, client):
        """POST /api/notes/ask - Ask question about notes."""
        response = client.post("/api/notes/ask", json={
            "question": "What are my notes about?"
        })
        assert response.status_code in [200, 503]
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_get_suggestions(self, client, test_note_id):
        """GET /api/notes/{id}/suggestions - Get AI suggestions."""
        response = client.get(f"/api/notes/{test_note_id}/suggestions")
        assert response.status_code in [200, 503]
    
    @pytest.mark.skipif(True, reason="Requires Ollama/LLM running")
    def test_get_ai_summary(self, client, test_note_id):
        """GET /api/notes/{id}/ai-summary - Get AI summary."""
        response = client.get(f"/api/notes/{test_note_id}/ai-summary")
        assert response.status_code in [200, 503]


# ============== RUN STANDALONE ==============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
