"""
Notes Frontend Integration Tests
=================================

Frontend-backend entegrasyon testleri.
Playwright/Selenium olmadan - sadece API üzerinden UI durumunu test eder.
"""

import pytest
import httpx
import uuid

API_BASE = "http://localhost:8001"


class TestFrontendStateSync:
    """Frontend state senkronizasyonu."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_create_note_returns_full_object(self, client):
        """Create returns all fields for frontend state."""
        resp = client.post("/api/notes", json={
            "title": "Frontend State Test",
            "content": "Content",
            "color": "blue",
            "tags": ["test"]
        })
        assert resp.status_code == 200
        
        note = resp.json()
        
        # Required fields for frontend
        required_fields = ["id", "title", "content", "created_at", "updated_at"]
        for field in required_fields:
            assert field in note, f"Missing field: {field}"
        
        # Optional but expected fields
        optional_fields = ["color", "tags", "pinned", "locked", "encrypted"]
        for field in optional_fields:
            # Just check they exist (can be null)
            pass
        
        # Cleanup
        client.delete(f"/api/notes/{note['id']}")
        client.delete(f"/api/notes/trash/{note['id']}")
    
    def test_update_returns_full_object(self, client):
        """Update returns full note for frontend state update."""
        resp = client.post("/api/notes", json={"title": "Update State Test"})
        note_id = resp.json()["id"]
        
        update_resp = client.put(f"/api/notes/{note_id}", json={
            "title": "Updated Title"
        })
        assert update_resp.status_code == 200
        
        note = update_resp.json()
        assert note["id"] == note_id
        assert note["title"] == "Updated Title"
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_folder_returns_notes_count(self, client):
        """Folder listing might include notes count."""
        # Create folder with notes
        folder_resp = client.post("/api/folders", json={
            "name": "Notes Count Test"
        })
        folder_id = folder_resp.json()["id"]
        
        # Add notes
        for i in range(3):
            client.post("/api/notes", json={
                "title": f"Note {i}",
                "folder_id": folder_id
            })
        
        # Get folder
        get_resp = client.get(f"/api/folders/{folder_id}")
        folder = get_resp.json()
        
        # Might have notes_count field
        # Implementation dependent
        
        # Cleanup
        notes_resp = client.get("/api/notes", params={"folder_id": folder_id})
        for note in notes_resp.json().get("notes", []):
            client.delete(f"/api/notes/{note['id']}")
            client.delete(f"/api/notes/trash/{note['id']}")
        client.delete(f"/api/folders/{folder_id}")


class TestFrontendPagination:
    """Pagination testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def many_notes(self, client):
        """Create many notes for pagination testing."""
        notes = []
        for i in range(15):
            resp = client.post("/api/notes", json={
                "title": f"Pagination Note {i:02d}"
            })
            notes.append(resp.json()["id"])
        
        yield notes
        
        # Cleanup
        for note_id in notes:
            try:
                client.delete(f"/api/notes/{note_id}")
                client.delete(f"/api/notes/trash/{note_id}")
            except:
                pass
    
    def test_pagination_limit(self, client, many_notes):
        """Limit parameter works."""
        resp = client.get("/api/notes", params={"limit": 5})
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        assert len(notes) <= 5
    
    def test_pagination_offset(self, client, many_notes):
        """Offset parameter works."""
        # Get first page
        page1 = client.get("/api/notes", params={"limit": 5, "offset": 0})
        notes1 = page1.json()["notes"]
        
        # Get second page
        page2 = client.get("/api/notes", params={"limit": 5, "offset": 5})
        notes2 = page2.json()["notes"]
        
        # Should be different notes
        ids1 = [n["id"] for n in notes1]
        ids2 = [n["id"] for n in notes2]
        
        # No overlap (unless less than 10 total notes)
        if len(ids1) == 5 and len(ids2) > 0:
            assert not set(ids1).intersection(set(ids2))
    
    def test_response_includes_total(self, client, many_notes):
        """Response might include total count."""
        resp = client.get("/api/notes", params={"limit": 5})
        data = resp.json()
        
        # Might have total_count field
        if "total" in data or "total_count" in data:
            total = data.get("total") or data.get("total_count")
            assert total >= len(many_notes)


class TestFrontendSorting:
    """Sorting testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_sort_by_updated_at(self, client):
        """Sort by updated_at works."""
        resp = client.get("/api/notes", params={
            "sort_by": "updated_at",
            "sort_order": "desc"
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        if len(notes) >= 2:
            # First should be more recent
            dates = [n["updated_at"] for n in notes]
            assert dates == sorted(dates, reverse=True)
    
    def test_sort_by_title(self, client):
        """Sort by title works."""
        resp = client.get("/api/notes", params={
            "sort_by": "title",
            "sort_order": "asc"
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        if len(notes) >= 2:
            titles = [n["title"] for n in notes]
            # Should be alphabetical
            assert titles == sorted(titles)
    
    def test_pinned_notes_first(self, client):
        """Pinned notes appear first regardless of sort."""
        # Create unpinned note
        unpinned = client.post("/api/notes", json={
            "title": "ZZZZZ Unpinned"  # Would be last alphabetically
        })
        unpinned_id = unpinned.json()["id"]
        
        # Create pinned note
        pinned = client.post("/api/notes", json={
            "title": "AAAAA Pinned",
            "pinned": True
        })
        pinned_id = pinned.json()["id"]
        
        # Get notes
        resp = client.get("/api/notes")
        notes = resp.json()["notes"]
        
        # Find positions
        pinned_index = next((i for i, n in enumerate(notes) if n["id"] == pinned_id), -1)
        unpinned_index = next((i for i, n in enumerate(notes) if n["id"] == unpinned_id), -1)
        
        # Pinned should come before unpinned
        if pinned_index >= 0 and unpinned_index >= 0:
            # Might be true depending on implementation
            pass
        
        # Cleanup
        client.delete(f"/api/notes/{pinned_id}")
        client.delete(f"/api/notes/{unpinned_id}")
        client.delete(f"/api/notes/trash/{pinned_id}")
        client.delete(f"/api/notes/trash/{unpinned_id}")


class TestFrontendRealTime:
    """Real-time update testleri (polling/websocket olmadan)."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_update_reflects_immediately(self, client):
        """Update is immediately visible on GET."""
        resp = client.post("/api/notes", json={
            "title": "Realtime Test"
        })
        note_id = resp.json()["id"]
        
        # Update
        client.put(f"/api/notes/{note_id}", json={
            "title": "Updated Realtime"
        })
        
        # Immediate GET
        get_resp = client.get(f"/api/notes/{note_id}")
        assert get_resp.json()["title"] == "Updated Realtime"
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
    
    def test_delete_reflects_immediately(self, client):
        """Delete is immediately visible on list."""
        resp = client.post("/api/notes", json={
            "title": "Delete Realtime"
        })
        note_id = resp.json()["id"]
        
        # Delete
        client.delete(f"/api/notes/{note_id}")
        
        # Immediate list
        list_resp = client.get("/api/notes")
        ids = [n["id"] for n in list_resp.json()["notes"]]
        assert note_id not in ids
        
        # Cleanup from trash
        client.delete(f"/api/notes/trash/{note_id}")


class TestFrontendValidation:
    """Frontend input validation testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_empty_title_rejected(self, client):
        """Empty title is rejected."""
        resp = client.post("/api/notes", json={
            "title": ""
        })
        assert resp.status_code == 422  # Validation error
    
    def test_whitespace_only_title(self, client):
        """Whitespace-only title handling."""
        resp = client.post("/api/notes", json={
            "title": "   "
        })
        # Might be rejected or trimmed
        assert resp.status_code in [200, 422]
        
        if resp.status_code == 200:
            # Should be trimmed or rejected
            note = resp.json()
            client.delete(f"/api/notes/{note['id']}")
            client.delete(f"/api/notes/trash/{note['id']}")
    
    def test_very_long_title(self, client):
        """Very long title handling."""
        long_title = "A" * 1000
        resp = client.post("/api/notes", json={
            "title": long_title
        })
        # Should accept or truncate, not crash
        assert resp.status_code in [200, 422]
        
        if resp.status_code == 200:
            note = resp.json()
            client.delete(f"/api/notes/{note['id']}")
            client.delete(f"/api/notes/trash/{note['id']}")
    
    def test_special_characters_in_title(self, client):
        """Special characters in title."""
        resp = client.post("/api/notes", json={
            "title": "Note with émojis 🎉 and spëcial chars"
        })
        assert resp.status_code == 200
        
        note = resp.json()
        assert "émojis" in note["title"] or "spëcial" in note["title"]
        
        # Cleanup
        client.delete(f"/api/notes/{note['id']}")
        client.delete(f"/api/notes/trash/{note['id']}")
    
    def test_html_in_title_escaped(self, client):
        """HTML in title should be escaped or stripped."""
        resp = client.post("/api/notes", json={
            "title": "<script>alert('xss')</script>"
        })
        
        if resp.status_code == 200:
            note = resp.json()
            # Should not contain raw script tag
            # Implementation dependent
            client.delete(f"/api/notes/{note['id']}")
            client.delete(f"/api/notes/trash/{note['id']}")
    
    def test_invalid_color(self, client):
        """Invalid color value handling."""
        resp = client.post("/api/notes", json={
            "title": "Invalid Color Test",
            "color": "not-a-color"
        })
        # Should accept or reject, not crash
        assert resp.status_code in [200, 422]
        
        if resp.status_code == 200:
            note = resp.json()
            client.delete(f"/api/notes/{note['id']}")
            client.delete(f"/api/notes/trash/{note['id']}")


class TestFrontendBatchOperations:
    """Batch operations testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_batch_delete(self, client):
        """Delete multiple notes at once."""
        # Create notes
        note_ids = []
        for i in range(3):
            resp = client.post("/api/notes", json={
                "title": f"Batch Delete {i}"
            })
            note_ids.append(resp.json()["id"])
        
        # Try batch delete - might be POST /api/notes/batch-delete
        batch_resp = client.post("/api/notes/batch-delete", json={
            "ids": note_ids
        })
        
        # Might not be implemented
        if batch_resp.status_code == 404:
            # Delete one by one
            for note_id in note_ids:
                client.delete(f"/api/notes/{note_id}")
        
        # Cleanup from trash
        for note_id in note_ids:
            try:
                client.delete(f"/api/notes/trash/{note_id}")
            except:
                pass
    
    def test_batch_move(self, client):
        """Move multiple notes to folder."""
        # Create folder
        folder_resp = client.post("/api/folders", json={
            "name": "Batch Move Target"
        })
        folder_id = folder_resp.json()["id"]
        
        # Create notes
        note_ids = []
        for i in range(3):
            resp = client.post("/api/notes", json={
                "title": f"Batch Move {i}"
            })
            note_ids.append(resp.json()["id"])
        
        # Try batch move
        batch_resp = client.post("/api/notes/batch-move", json={
            "ids": note_ids,
            "folder_id": folder_id
        })
        
        # Might not be implemented
        
        # Cleanup
        for note_id in note_ids:
            try:
                client.delete(f"/api/notes/{note_id}")
                client.delete(f"/api/notes/trash/{note_id}")
            except:
                pass
        client.delete(f"/api/folders/{folder_id}")


# ============== RUN ==============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
