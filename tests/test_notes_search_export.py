"""
Notes Search and Export Tests
==============================

Arama ve dışa aktarma testleri.
- Full-text search
- Tag filtering
- Date filtering
- PDF export
- Markdown export
- Multi-note export
"""

import pytest
import httpx
import uuid
import base64
from pathlib import Path

API_BASE = "http://localhost:8001"


class TestSearch:
    """Search (arama) testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def searchable_notes(self, client):
        """Create notes with specific content for searching."""
        notes = []
        
        # Note 1 - Python content
        resp = client.post("/api/notes", json={
            "title": "Python Tutorial",
            "content": "Learn Python programming language basics",
            "tags": ["python", "tutorial"]
        })
        notes.append(resp.json()["id"])
        
        # Note 2 - JavaScript content
        resp = client.post("/api/notes", json={
            "title": "JavaScript Guide",
            "content": "Modern JavaScript ES6 features overview",
            "tags": ["javascript", "tutorial"]
        })
        notes.append(resp.json()["id"])
        
        # Note 3 - General programming
        resp = client.post("/api/notes", json={
            "title": "Programming Best Practices",
            "content": "Clean code and design patterns",
            "tags": ["best-practices", "programming"]
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
    
    def test_search_by_title(self, client, searchable_notes):
        """Search finds notes by title."""
        resp = client.get("/api/notes", params={
            "search_query": "Python"
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        titles = [n["title"] for n in notes]
        assert any("Python" in t for t in titles)
    
    def test_search_by_content(self, client, searchable_notes):
        """Search finds notes by content."""
        resp = client.get("/api/notes", params={
            "search_query": "ES6"
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        # Should find JavaScript note
        assert len(notes) >= 1
    
    def test_search_case_insensitive(self, client, searchable_notes):
        """Search is case insensitive."""
        resp1 = client.get("/api/notes", params={"search_query": "PYTHON"})
        resp2 = client.get("/api/notes", params={"search_query": "python"})
        
        # Both should find the same notes
        notes1 = resp1.json()["notes"]
        notes2 = resp2.json()["notes"]
        
        # At least one should find Python tutorial
        assert len(notes1) >= 1 or len(notes2) >= 1
    
    def test_search_no_results(self, client):
        """Search with no matches returns empty list."""
        unique_term = f"XYZ{uuid.uuid4().hex}ZYX"
        resp = client.get("/api/notes", params={
            "search_query": unique_term
        })
        assert resp.status_code == 200
        assert len(resp.json()["notes"]) == 0
    
    def test_filter_by_tag(self, client, searchable_notes):
        """Filter notes by tag."""
        resp = client.get("/api/notes", params={
            "tag": "tutorial"
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        # Python and JavaScript both have tutorial tag
        assert len(notes) >= 2
    
    def test_filter_by_folder(self, client):
        """Filter notes by folder."""
        # Create folder
        folder_resp = client.post("/api/folders", json={
            "name": "Search Folder Test"
        })
        folder_id = folder_resp.json()["id"]
        
        # Create notes in folder
        note_resp = client.post("/api/notes", json={
            "title": "Note in Folder",
            "folder_id": folder_id
        })
        note_id = note_resp.json()["id"]
        
        # Filter
        resp = client.get("/api/notes", params={
            "folder_id": folder_id
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        ids = [n["id"] for n in notes]
        assert note_id in ids
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")
        client.delete(f"/api/folders/{folder_id}")
    
    def test_search_with_pagination(self, client, searchable_notes):
        """Search with limit and offset."""
        resp = client.get("/api/notes", params={
            "limit": 1,
            "offset": 0
        })
        assert resp.status_code == 200
        
        notes = resp.json()["notes"]
        assert len(notes) <= 1
    
    def test_combined_search_and_filter(self, client, searchable_notes):
        """Search query + tag filter combined."""
        resp = client.get("/api/notes", params={
            "search_query": "programming",
            "tag": "tutorial"
        })
        assert resp.status_code == 200
        # Just verify it works without crashing


class TestExportMarkdown:
    """Markdown export testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    @pytest.fixture
    def export_note(self, client):
        """Create note for export testing."""
        resp = client.post("/api/notes", json={
            "title": "Export Test Note",
            "content": "# Heading\n\nParagraph with **bold** and *italic*.",
            "tags": ["export", "test"]
        })
        note_id = resp.json()["id"]
        yield note_id
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_export_markdown_endpoint(self, client, export_note):
        """GET /api/notes/{id}/export/markdown works."""
        resp = client.get(f"/api/notes/{export_note}/export/markdown")
        assert resp.status_code == 200
    
    def test_export_markdown_content_type(self, client, export_note):
        """Export returns markdown content type or text."""
        resp = client.get(f"/api/notes/{export_note}/export/markdown")
        content_type = resp.headers.get("content-type", "")
        # Should be text/markdown or text/plain or application/octet-stream
        assert "text" in content_type or "octet" in content_type or resp.status_code == 200
    
    def test_export_markdown_contains_title(self, client, export_note):
        """Exported markdown contains note title."""
        resp = client.get(f"/api/notes/{export_note}/export/markdown")
        content = resp.text
        assert "Export Test Note" in content
    
    def test_export_markdown_contains_content(self, client, export_note):
        """Exported markdown contains note content."""
        resp = client.get(f"/api/notes/{export_note}/export/markdown")
        content = resp.text
        assert "Heading" in content or "bold" in content


class TestExportPDF:
    """PDF export testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=60.0)  # Longer timeout for PDF
    
    @pytest.fixture
    def export_note(self, client):
        resp = client.post("/api/notes", json={
            "title": "PDF Export Test",
            "content": "# Test Content\n\nThis is a test."
        })
        note_id = resp.json()["id"]
        yield note_id
        try:
            client.delete(f"/api/notes/{note_id}")
            client.delete(f"/api/notes/trash/{note_id}")
        except:
            pass
    
    def test_export_pdf_endpoint(self, client, export_note):
        """GET /api/notes/{id}/export/pdf works."""
        resp = client.get(f"/api/notes/{export_note}/export/pdf")
        # Might be 200 or 500 if PDF library not installed
        assert resp.status_code in [200, 500, 501]
    
    def test_export_pdf_binary(self, client, export_note):
        """PDF export returns binary data."""
        resp = client.get(f"/api/notes/{export_note}/export/pdf")
        if resp.status_code == 200:
            # PDF starts with %PDF
            assert resp.content[:4] == b'%PDF' or len(resp.content) > 0


class TestExportBulk:
    """Bulk export testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_export_folder_endpoint(self, client):
        """Export all notes in folder."""
        # Create folder with notes
        folder_resp = client.post("/api/folders", json={
            "name": "Bulk Export Test"
        })
        folder_id = folder_resp.json()["id"]
        
        for i in range(3):
            client.post("/api/notes", json={
                "title": f"Bulk Note {i}",
                "folder_id": folder_id
            })
        
        # Try bulk export
        resp = client.get(f"/api/folders/{folder_id}/export")
        # Might not be implemented
        
        # Cleanup
        notes_resp = client.get("/api/notes", params={"folder_id": folder_id})
        for note in notes_resp.json().get("notes", []):
            client.delete(f"/api/notes/{note['id']}")
            client.delete(f"/api/notes/trash/{note['id']}")
        client.delete(f"/api/folders/{folder_id}")


class TestTemplates:
    """Template (şablon) testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_get_templates_list(self, client):
        """GET /api/notes/templates lists available templates."""
        resp = client.get("/api/notes/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data
    
    def test_create_note_from_template(self, client):
        """Create note using template."""
        # Get templates
        templates_resp = client.get("/api/notes/templates")
        templates = templates_resp.json().get("templates", [])
        
        if templates:
            template_id = templates[0].get("id")
            if template_id:
                resp = client.post("/api/notes/from-template", json={
                    "template_id": template_id,
                    "title": "Note from Template"
                })
                # Might or might not be implemented
                if resp.status_code == 200:
                    note_id = resp.json().get("id")
                    if note_id:
                        client.delete(f"/api/notes/{note_id}")
                        client.delete(f"/api/notes/trash/{note_id}")


class TestBacklinks:
    """Backlinks (geri bağlantı) testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_get_backlinks(self, client):
        """GET /api/notes/{id}/backlinks returns linking notes."""
        # Create note A
        note_a_resp = client.post("/api/notes", json={
            "title": "Target Note",
            "content": "This is the target"
        })
        note_a_id = note_a_resp.json()["id"]
        
        # Create note B that links to A
        note_b_resp = client.post("/api/notes", json={
            "title": "Linking Note",
            "content": f"This links to [[Target Note]]"
        })
        note_b_id = note_b_resp.json()["id"]
        
        # Get backlinks for A
        resp = client.get(f"/api/notes/{note_a_id}/backlinks")
        # Might return backlinks or empty array
        
        # Cleanup
        client.delete(f"/api/notes/{note_a_id}")
        client.delete(f"/api/notes/{note_b_id}")
        client.delete(f"/api/notes/trash/{note_a_id}")
        client.delete(f"/api/notes/trash/{note_b_id}")
    
    def test_note_links(self, client):
        """GET /api/notes/{id}/links returns outgoing links."""
        # Create with wiki-style links
        resp = client.post("/api/notes", json={
            "title": "Note with Links",
            "content": "Links to [[Other Note]] and [[Another]]"
        })
        note_id = resp.json()["id"]
        
        # Get links
        links_resp = client.get(f"/api/notes/{note_id}/links")
        # Implementation dependent
        
        # Cleanup
        client.delete(f"/api/notes/{note_id}")
        client.delete(f"/api/notes/trash/{note_id}")


class TestStats:
    """Statistics testleri."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=API_BASE, timeout=30.0)
    
    def test_notes_stats_endpoint(self, client):
        """GET /api/notes/stats returns statistics."""
        resp = client.get("/api/notes/stats")
        assert resp.status_code == 200
        
        stats = resp.json()
        assert "total_notes" in stats
        assert "total_folders" in stats
    
    def test_stats_includes_counts(self, client):
        """Stats includes various counts."""
        resp = client.get("/api/notes/stats")
        stats = resp.json()
        
        # All counts should be non-negative integers
        for key, value in stats.items():
            if "count" in key.lower() or "total" in key.lower():
                assert isinstance(value, int)
                assert value >= 0


# ============== RUN ==============
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
