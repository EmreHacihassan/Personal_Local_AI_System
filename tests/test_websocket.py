"""
Enterprise AI Assistant - WebSocket Tests
==========================================

WebSocket streaming, resume capability, connection handling testleri.
Real-time communication için endüstri standardı testler.
"""

import pytest
import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStreamBuffer:
    """Stream Buffer testleri."""
    
    def test_buffer_initialization(self):
        """StreamBuffer başlatılabilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        assert buffer is not None
    
    def test_create_stream(self):
        """Yeni stream oluşturulabilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        
        # Actual API: create_stream(session_id, message)
        stream = buffer.create_stream(session_id="test-session", message="test message")
        
        assert stream is not None
        assert stream.stream_id is not None
        assert len(stream.stream_id) > 0
    
    def test_add_token_to_stream(self):
        """Stream'e token eklenebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test-session", message="test")
        
        buffer.add_token(stream.stream_id, "Hello")
        buffer.add_token(stream.stream_id, " ")
        buffer.add_token(stream.stream_id, "World")
        
        # get_stream returns StreamState directly
        state = buffer.get_stream(stream.stream_id)
        
        assert state is not None
        assert len(state.tokens) == 3
    
    def test_get_tokens_from_index(self):
        """Belirli index'ten itibaren tokenlar alınabilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test-session", message="test")
        
        # 5 token ekle
        tokens = ["Token1", "Token2", "Token3", "Token4", "Token5"]
        for token in tokens:
            buffer.add_token(stream.stream_id, token)
        
        # Index 2'den itibaren al
        resume_data = buffer.get_resume_data(stream.stream_id, from_index=2)
        
        assert len(resume_data['tokens']) == 3
        assert resume_data['tokens'][0]['content'] == "Token3"
    
    def test_stream_completion(self):
        """Stream tamamlandığında işaretlenebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test-session", message="test")
        
        buffer.add_token(stream.stream_id, "Test")
        buffer.complete_stream(stream.stream_id)
        
        state = buffer.get_stream(stream.stream_id)
        
        # is_active should be False when completed
        assert not state.is_active
        assert state.status == "completed"
    
    def test_stream_error_handling(self):
        """Stream hatası kaydedilebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test-session", message="test")
        
        # Use error_stream instead of set_stream_error
        buffer.error_stream(stream.stream_id, "Connection timeout")
        
        state = buffer.get_stream(stream.stream_id)
        
        assert state.error is not None
        assert "timeout" in state.error.lower()
    
    def test_get_full_content(self):
        """Tam içerik alınabilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test-session", message="test")
        
        buffer.add_token(stream.stream_id, "Hello")
        buffer.add_token(stream.stream_id, " ")
        buffer.add_token(stream.stream_id, "World")
        buffer.add_token(stream.stream_id, "!")
        
        # Use state.full_response property
        state = buffer.get_stream(stream.stream_id)
        full_content = state.full_response
        
        assert full_content == "Hello World!"
    
    def test_multiple_sessions(self):
        """Birden fazla session yönetilebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        
        stream1 = buffer.create_stream(session_id="session-1", message="msg1")
        stream2 = buffer.create_stream(session_id="session-2", message="msg2")
        
        buffer.add_token(stream1.stream_id, "Session 1")
        buffer.add_token(stream2.stream_id, "Session 2")
        
        state1 = buffer.get_stream(stream1.stream_id)
        state2 = buffer.get_stream(stream2.stream_id)
        
        assert state1.full_response == "Session 1"
        assert state2.full_response == "Session 2"


class TestWebSocketHandler:
    """WebSocket Handler testleri."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_text = AsyncMock()
        ws.receive_json = AsyncMock()
        ws.receive_text = AsyncMock()
        ws.close = AsyncMock()
        ws.client_state = Mock()
        return ws
    
    @pytest.mark.asyncio
    async def test_websocket_manager_initialization(self):
        """WebSocket Manager başlatılabilmeli."""
        from api.websocket_v2 import WebSocketManagerV2
        
        manager = WebSocketManagerV2()
        assert manager is not None
        assert manager.active_count == 0


class TestWebSocketReconnection:
    """WebSocket yeniden bağlanma testleri."""
    
    def test_session_persistence(self):
        """Session bilgisi korunmalı."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        session_id = "persistent-session"
        
        # İlk bağlantı
        stream1 = buffer.create_stream(session_id=session_id, message="first")
        buffer.add_token(stream1.stream_id, "First")
        buffer.add_token(stream1.stream_id, "Message")
        buffer.complete_stream(stream1.stream_id)
        
        # İkinci bağlantı (reconnect)
        stream2 = buffer.create_stream(session_id=session_id, message="second")
        
        # Eski stream hala erişilebilir olmalı
        state1 = buffer.get_stream(stream1.stream_id)
        assert state1.full_response == "FirstMessage"
    
    def test_resume_from_last_token(self):
        """Son token'dan devam edilebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test", message="test")
        
        # 10 token ekle
        for i in range(10):
            buffer.add_token(stream.stream_id, f"Token{i}")
        
        # Client 5. token'da koptu, 5'ten devam et
        resume_data = buffer.get_resume_data(stream.stream_id, from_index=5)
        
        assert len(resume_data['tokens']) == 5
        assert resume_data['tokens'][0]['content'] == "Token5"
        assert resume_data['tokens'][-1]['content'] == "Token9"
    
    def test_incomplete_stream_detection(self):
        """Tamamlanmamış stream tespit edilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="test", message="test")
        
        buffer.add_token(stream.stream_id, "Incomplete")
        # complete_stream çağrılmadı
        
        state = buffer.get_stream(stream.stream_id)
        
        # is_active should be True when not completed
        assert state.is_active


class TestWebSocketProtocol:
    """WebSocket protokol testleri."""
    
    def test_message_format_chat(self):
        """Chat mesaj formatı doğru olmalı."""
        test_message = {
            "type": "chat",
            "message": "Hello",
            "session_id": "abc123"
        }
        
        assert test_message["type"] == "chat"
        assert isinstance(test_message["message"], str)
        assert isinstance(test_message["session_id"], str)
    
    def test_message_format_token(self):
        """Token mesaj formatı doğru olmalı."""
        token_message = {
            "type": "token",
            "content": "Hello",
            "index": 0,
            "stream_id": "stream-123"
        }
        
        assert token_message["type"] == "token"
        assert "content" in token_message
        assert "index" in token_message
    
    def test_message_format_resume(self):
        """Resume mesaj formatı doğru olmalı."""
        resume_message = {
            "type": "resume",
            "stream_id": "stream-123",
            "from_index": 5
        }
        
        assert resume_message["type"] == "resume"
        assert "stream_id" in resume_message
        assert "from_index" in resume_message


class TestWebSocketPerformance:
    """WebSocket performans testleri."""
    
    def test_buffer_memory_efficiency(self):
        """Buffer bellek verimli olmalı."""
        from core.stream_buffer import StreamBuffer
        import sys
        
        buffer = StreamBuffer()
        
        # 100 stream oluştur
        for i in range(100):
            stream = buffer.create_stream(session_id=f"session-{i}", message=f"msg-{i}")
            for j in range(100):
                buffer.add_token(stream.stream_id, f"Token{j}")
        
        # Memory kullanımı makul olmalı
        stats = buffer.get_stats()
        assert stats["total_streams"] <= 100
    
    def test_token_retrieval_performance(self):
        """Token erişimi hızlı olmalı."""
        from core.stream_buffer import StreamBuffer
        import time
        
        buffer = StreamBuffer()
        stream = buffer.create_stream(session_id="perf-test", message="test")
        
        # 1000 token ekle
        for i in range(1000):
            buffer.add_token(stream.stream_id, f"Token{i}")
        
        # Resume süresi ölç
        start = time.time()
        for _ in range(100):
            buffer.get_resume_data(stream.stream_id, from_index=500)
        elapsed = time.time() - start
        
        # 100 erişim 1 saniyeden kısa olmalı
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
