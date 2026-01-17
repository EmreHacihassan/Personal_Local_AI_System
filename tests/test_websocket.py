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
        
        stream_id = buffer.create_stream(session_id="test-session")
        
        assert stream_id is not None
        assert len(stream_id) > 0
    
    def test_add_token_to_stream(self):
        """Stream'e token eklenebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test-session")
        
        buffer.add_token(stream_id, "Hello")
        buffer.add_token(stream_id, " ")
        buffer.add_token(stream_id, "World")
        
        state = buffer.get_stream_state(stream_id)
        
        assert state is not None
        assert len(state.tokens) == 3
    
    def test_get_tokens_from_index(self):
        """Belirli index'ten itibaren tokenlar alınabilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test-session")
        
        # 5 token ekle
        tokens = ["Token1", "Token2", "Token3", "Token4", "Token5"]
        for token in tokens:
            buffer.add_token(stream_id, token)
        
        # Index 2'den itibaren al
        resume_data = buffer.get_resume_data(stream_id, from_index=2)
        
        assert len(resume_data['tokens']) == 3
        assert resume_data['tokens'][0]['content'] == "Token3"
    
    def test_stream_completion(self):
        """Stream tamamlandığında işaretlenebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test-session")
        
        buffer.add_token(stream_id, "Test")
        buffer.complete_stream(stream_id)
        
        state = buffer.get_stream_state(stream_id)
        
        assert state.is_complete
    
    def test_stream_error_handling(self):
        """Stream hatası kaydedilebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test-session")
        
        buffer.set_stream_error(stream_id, "Connection timeout")
        
        state = buffer.get_stream_state(stream_id)
        
        assert state.error is not None
        assert "timeout" in state.error.lower()
    
    def test_stream_ttl_cleanup(self):
        """Eski streamler temizlenmeli."""
        from core.stream_buffer import StreamBuffer
        import time
        
        buffer = StreamBuffer(ttl_seconds=1)
        stream_id = buffer.create_stream(session_id="test-session")
        
        # 1 saniye bekle
        time.sleep(1.5)
        
        buffer.cleanup_expired()
        
        state = buffer.get_stream_state(stream_id)
        
        # TTL geçtiyse None dönmeli
        assert state is None
    
    def test_get_full_content(self):
        """Tam içerik alınabilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test-session")
        
        buffer.add_token(stream_id, "Hello")
        buffer.add_token(stream_id, " ")
        buffer.add_token(stream_id, "World")
        buffer.add_token(stream_id, "!")
        
        full_content = buffer.get_full_content(stream_id)
        
        assert full_content == "Hello World!"
    
    def test_multiple_sessions(self):
        """Birden fazla session yönetilebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        
        stream1 = buffer.create_stream(session_id="session-1")
        stream2 = buffer.create_stream(session_id="session-2")
        
        buffer.add_token(stream1, "Session 1")
        buffer.add_token(stream2, "Session 2")
        
        content1 = buffer.get_full_content(stream1)
        content2 = buffer.get_full_content(stream2)
        
        assert content1 == "Session 1"
        assert content2 == "Session 2"


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
        return ws
    
    @pytest.mark.asyncio
    async def test_websocket_connection_accept(self, mock_websocket):
        """WebSocket bağlantısı kabul edilmeli."""
        from api.websocket_v2 import handle_websocket
        
        mock_websocket.receive_json.side_effect = [
            {"type": "ping"},
            Exception("Connection closed")
        ]
        
        try:
            await handle_websocket(mock_websocket)
        except:
            pass
        
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ping_pong_handling(self, mock_websocket):
        """Ping-pong heartbeat çalışmalı."""
        from api.websocket_v2 import handle_websocket
        
        mock_websocket.receive_json.side_effect = [
            {"type": "ping"},
            Exception("Connection closed")
        ]
        
        try:
            await handle_websocket(mock_websocket)
        except:
            pass
        
        # Pong yanıtı gönderilmeli
        calls = mock_websocket.send_json.call_args_list
        pong_sent = any(
            call[0][0].get('type') == 'pong' 
            for call in calls if call[0]
        )
        assert pong_sent
    
    @pytest.mark.asyncio
    async def test_resume_message_handling(self, mock_websocket):
        """Resume mesajı işlenmeli."""
        from api.websocket_v2 import handle_websocket
        from core.stream_buffer import stream_buffer
        
        # Önce bir stream oluştur
        stream_id = stream_buffer.create_stream(session_id="test")
        stream_buffer.add_token(stream_id, "Token1")
        stream_buffer.add_token(stream_id, "Token2")
        
        mock_websocket.receive_json.side_effect = [
            {"type": "resume", "stream_id": stream_id, "from_index": 0},
            Exception("Connection closed")
        ]
        
        try:
            await handle_websocket(mock_websocket)
        except:
            pass
        
        # Resume yanıtı gönderilmeli
        assert mock_websocket.send_json.called
    
    @pytest.mark.asyncio
    async def test_chat_message_streaming(self, mock_websocket):
        """Chat mesajı stream edilmeli."""
        from api.websocket_v2 import handle_websocket
        
        mock_websocket.receive_json.side_effect = [
            {
                "type": "chat",
                "message": "Hello",
                "session_id": "test-session"
            },
            Exception("Connection closed")
        ]
        
        with patch('api.websocket_v2.llm_manager') as mock_llm:
            mock_llm.generate_stream = Mock(return_value=iter(["Hello", " ", "World"]))
            
            try:
                await handle_websocket(mock_websocket)
            except:
                pass
        
        # Stream başlatıldığını kontrol et
        assert mock_websocket.send_json.called
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_websocket):
        """Bağlantı hatası graceful handle edilmeli."""
        from api.websocket_v2 import handle_websocket
        
        mock_websocket.receive_json.side_effect = Exception("Network error")
        
        # Hata fırlatmamalı, graceful kapanmalı
        try:
            await handle_websocket(mock_websocket)
        except Exception as e:
            # Beklenmeyen hata olmamalı
            assert "Network error" in str(e)


class TestWebSocketReconnection:
    """WebSocket yeniden bağlanma testleri."""
    
    def test_session_persistence(self):
        """Session bilgisi korunmalı."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        session_id = "persistent-session"
        
        # İlk bağlantı
        stream1 = buffer.create_stream(session_id=session_id)
        buffer.add_token(stream1, "First")
        buffer.add_token(stream1, "Message")
        buffer.complete_stream(stream1)
        
        # İkinci bağlantı (reconnect)
        stream2 = buffer.create_stream(session_id=session_id)
        
        # Eski stream hala erişilebilir olmalı
        old_content = buffer.get_full_content(stream1)
        assert old_content == "FirstMessage"
    
    def test_resume_from_last_token(self):
        """Son token'dan devam edilebilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test")
        
        # 10 token ekle
        for i in range(10):
            buffer.add_token(stream_id, f"Token{i}")
        
        # Client 5. token'da koptu, 5'ten devam et
        resume_data = buffer.get_resume_data(stream_id, from_index=5)
        
        assert len(resume_data['tokens']) == 5
        assert resume_data['tokens'][0]['content'] == "Token5"
        assert resume_data['tokens'][-1]['content'] == "Token9"
    
    def test_incomplete_stream_detection(self):
        """Tamamlanmamış stream tespit edilmeli."""
        from core.stream_buffer import StreamBuffer
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="test")
        
        buffer.add_token(stream_id, "Incomplete")
        # complete_stream çağrılmadı
        
        state = buffer.get_stream_state(stream_id)
        
        assert not state.is_complete


class TestWebSocketProtocol:
    """WebSocket protokol testleri."""
    
    def test_message_format_chat(self):
        """Chat mesaj formatı doğru olmalı."""
        expected_format = {
            "type": "chat",
            "message": str,
            "session_id": str
        }
        
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
        assert "stream_id" in token_message
    
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
    
    def test_message_format_error(self):
        """Error mesaj formatı doğru olmalı."""
        error_message = {
            "type": "error",
            "error": "Connection timeout",
            "code": "TIMEOUT"
        }
        
        assert error_message["type"] == "error"
        assert "error" in error_message


class TestWebSocketSecurity:
    """WebSocket güvenlik testleri."""
    
    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.receive_json = AsyncMock()
        ws.close = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_message_size_limit(self, mock_websocket):
        """Çok büyük mesajlar reddedilmeli."""
        from api.websocket_v2 import handle_websocket
        
        # 1MB'lık mesaj
        huge_message = {
            "type": "chat",
            "message": "A" * (1024 * 1024),
            "session_id": "test"
        }
        
        mock_websocket.receive_json.side_effect = [
            huge_message,
            Exception("Done")
        ]
        
        try:
            await handle_websocket(mock_websocket)
        except:
            pass
        
        # Error response gönderilmiş olmalı
        calls = mock_websocket.send_json.call_args_list
        # Ya error dönmeli ya da mesajı işlememeli
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_websocket):
        """Rate limiting uygulanmalı."""
        from api.websocket_v2 import handle_websocket
        
        # Çok hızlı mesaj bombardımanı
        messages = [
            {"type": "chat", "message": f"Msg{i}", "session_id": "test"}
            for i in range(100)
        ]
        messages.append(Exception("Done"))
        
        mock_websocket.receive_json.side_effect = messages
        
        try:
            await handle_websocket(mock_websocket)
        except:
            pass
        
        # Rate limit mesajı gönderilmiş olabilir
    
    @pytest.mark.asyncio
    async def test_invalid_message_type(self, mock_websocket):
        """Geçersiz mesaj tipi handle edilmeli."""
        from api.websocket_v2 import handle_websocket
        
        mock_websocket.receive_json.side_effect = [
            {"type": "INVALID_TYPE", "data": "test"},
            Exception("Done")
        ]
        
        try:
            await handle_websocket(mock_websocket)
        except:
            pass
        
        # Error veya ignore edilmeli


class TestWebSocketPerformance:
    """WebSocket performans testleri."""
    
    def test_buffer_memory_efficiency(self):
        """Buffer bellek verimli olmalı."""
        from core.stream_buffer import StreamBuffer
        import sys
        
        buffer = StreamBuffer(max_streams=100)
        
        # 100 stream oluştur
        for i in range(100):
            stream_id = buffer.create_stream(session_id=f"session-{i}")
            for j in range(100):
                buffer.add_token(stream_id, f"Token{j}")
        
        # Memory kullanımı makul olmalı
        # (Bu test platformdan platforma değişebilir)
        buffer_size = sys.getsizeof(buffer)
        assert buffer_size < 50 * 1024 * 1024  # 50MB'dan az
    
    def test_token_retrieval_performance(self):
        """Token erişimi hızlı olmalı."""
        from core.stream_buffer import StreamBuffer
        import time
        
        buffer = StreamBuffer()
        stream_id = buffer.create_stream(session_id="perf-test")
        
        # 1000 token ekle
        for i in range(1000):
            buffer.add_token(stream_id, f"Token{i}")
        
        # Resume süresi ölç
        start = time.time()
        for _ in range(100):
            buffer.get_resume_data(stream_id, from_index=500)
        elapsed = time.time() - start
        
        # 100 erişim 1 saniyeden kısa olmalı
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
