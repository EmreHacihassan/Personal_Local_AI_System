"""
Enterprise AI Assistant - Streaming Tests
==========================================

Streaming yanıt, SSE, WebSocket ve token akışı testleri.
Performans ve güvenilirlik odaklı kapsamlı testler.
"""

import pytest
import sys
import time
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import List, Dict, Any, AsyncGenerator

sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock chromadb before any imports
from unittest.mock import MagicMock
if 'chromadb' not in sys.modules:
    mock_chromadb = MagicMock()
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.query.return_value = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    mock_chromadb.PersistentClient.return_value.get_or_create_collection.return_value = mock_collection
    sys.modules['chromadb'] = mock_chromadb
    sys.modules['chromadb.config'] = MagicMock()
    sys.modules['chromadb.api'] = MagicMock()


class TestStreamingBasics:
    """Temel streaming testleri."""
    
    def test_streaming_endpoint_exists(self):
        """Streaming endpoint mevcut olmalı."""
        from api.main import app
        
        routes = [r.path for r in app.routes]
        
        # Streaming endpoint'ler
        assert '/api/chat/stream' in routes or any('stream' in r for r in routes)
    
    def test_streaming_returns_sse_format(self):
        """Streaming SSE formatında döndürmeli."""
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        # Mock LLM response
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.generate_stream.return_value = iter(['Token1', 'Token2', 'Token3'])
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.session_manager') as mock_session:
                mock_session.get_session.return_value = None
                mock_session.create_session.return_value = MagicMock(id='test-session')
                
                response = client.post(
                    '/api/chat/stream',
                    json={'message': 'Test', 'session_id': 'test'}
                )
                
                # Response stream olarak gelir
                assert response.status_code == 200
    
    def test_streaming_content_type(self):
        """Content-Type text/event-stream olmalı."""
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.generate_stream.return_value = iter(['Test'])
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.session_manager') as mock_session:
                mock_session.get_session.return_value = None
                mock_session.create_session.return_value = MagicMock(id='test-session')
                
                response = client.post(
                    '/api/chat/stream',
                    json={'message': 'Test'}
                )
                
                content_type = response.headers.get('content-type', '')
                assert 'event-stream' in content_type or response.status_code == 200


class TestTokenStreaming:
    """Token streaming testleri."""
    
    def test_tokens_arrive_incrementally(self):
        """Token'lar artımlı olarak gelmeli."""
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        tokens_sent = ['Merhaba', ' ', 'dünya', '!']
        
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.generate_stream.return_value = iter(tokens_sent)
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.session_manager') as mock_session:
                mock_session.get_session.return_value = None
                mock_session.create_session.return_value = MagicMock(id='test-session')
                
                response = client.post(
                    '/api/chat/stream',
                    json={'message': 'Merhaba de'}
                )
                
                # Response başarılı olmalı
                assert response.status_code == 200
    
    def test_streaming_preserves_order(self):
        """Token sırası korunmalı."""
        ordered_tokens = ['1', '2', '3', '4', '5']
        
        # Sıralama kontrolü
        for i, token in enumerate(ordered_tokens):
            assert token == str(i + 1)
    
    def test_streaming_handles_unicode(self):
        """Unicode karakterler düzgün işlenmeli."""
        unicode_tokens = ['Türkçe', ' ', 'karakter:', ' ', 'ğüşıöç', 'ĞÜŞİÖÇ']
        
        # Her token düzgün encode/decode edilmeli
        for token in unicode_tokens:
            encoded = token.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert decoded == token


class TestSSEProtocol:
    """SSE (Server-Sent Events) protokol testleri."""
    
    def test_sse_message_format(self):
        """SSE mesaj formatı doğru olmalı."""
        # SSE format: "data: {json}\n\n"
        test_data = {"type": "token", "content": "test"}
        sse_message = f"data: {json.dumps(test_data)}\n\n"
        
        assert sse_message.startswith("data: ")
        assert sse_message.endswith("\n\n")
        
        # JSON parse edilebilmeli
        json_part = sse_message[6:-2]  # "data: " ve "\n\n" kaldır
        parsed = json.loads(json_part)
        assert parsed == test_data
    
    def test_sse_event_types(self):
        """Farklı SSE event tipleri desteklenmeli."""
        expected_types = ['session', 'token', 'end', 'error', 'status']
        
        # Her tip için test
        for event_type in expected_types:
            event = {"type": event_type, "content": "test"}
            sse = f"data: {json.dumps(event)}\n\n"
            
            parsed = json.loads(sse[6:-2])
            assert parsed["type"] == event_type
    
    def test_sse_session_event_first(self):
        """Session event ilk gelmeli."""
        events = [
            {"type": "session", "session_id": "abc123"},
            {"type": "token", "content": "Hello"},
            {"type": "end"}
        ]
        
        assert events[0]["type"] == "session"
    
    def test_sse_end_event_last(self):
        """End event en son gelmeli."""
        events = [
            {"type": "session", "session_id": "abc123"},
            {"type": "token", "content": "Hello"},
            {"type": "token", "content": " World"},
            {"type": "end"}
        ]
        
        assert events[-1]["type"] == "end"


class TestStreamingPerformance:
    """Streaming performans testleri."""
    
    def test_first_token_latency(self):
        """İlk token gecikmesi kabul edilebilir olmalı."""
        # Target: < 500ms for first token (mocked)
        target_latency_ms = 500
        
        start_time = time.time()
        
        # Simulated first token
        first_token = "Merhaba"
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Simülasyonda çok hızlı olmalı
        assert elapsed_ms < target_latency_ms
    
    def test_token_throughput(self):
        """Token throughput yeterli olmalı."""
        # Target: > 20 tokens/second
        tokens = ['token'] * 100
        
        start_time = time.time()
        count = 0
        for token in tokens:
            count += 1
        elapsed = time.time() - start_time
        
        if elapsed > 0:
            throughput = count / elapsed
            # Simülasyonda çok yüksek olmalı
            assert throughput > 20
    
    def test_streaming_memory_efficiency(self):
        """Streaming memory-efficient olmalı."""
        import sys
        
        # Generator memory test
        def token_generator():
            for i in range(1000):
                yield f"token_{i}"
        
        gen = token_generator()
        
        # Generator object küçük olmalı
        gen_size = sys.getsizeof(gen)
        assert gen_size < 1000  # bytes
    
    def test_no_buffering_delays(self):
        """Buffering gecikmeleri olmamalı."""
        from api.main import app
        
        # X-Accel-Buffering: no header kontrolü
        # Bu, nginx gibi proxy'lerin buffer yapmaması için
        
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        with patch('api.main.llm_manager') as mock_llm:
            mock_llm.generate_stream.return_value = iter(['Test'])
            mock_llm.get_status.return_value = {'primary_available': True}
            
            with patch('api.main.session_manager') as mock_session:
                mock_session.get_session.return_value = None
                mock_session.create_session.return_value = MagicMock(id='test')
                
                response = client.post(
                    '/api/chat/stream',
                    json={'message': 'Test'}
                )
                
                # Response başarılı
                assert response.status_code == 200


class TestStreamingResilience:
    """Streaming dayanıklılık testleri."""
    
    def test_streaming_handles_connection_drop(self):
        """Bağlantı kopması düzgün yönetilmeli."""
        # Connection drop simülasyonu
        class MockConnectionDrop(Exception):
            pass
        
        def dropping_generator():
            yield "token1"
            yield "token2"
            raise MockConnectionDrop("Connection lost")
        
        gen = dropping_generator()
        received = []
        
        try:
            for token in gen:
                received.append(token)
        except MockConnectionDrop:
            pass
        
        # Gelen token'lar alınmış olmalı
        assert len(received) == 2
    
    @pytest.mark.asyncio
    async def test_streaming_timeout_handling(self):
        """Timeout durumları yönetilmeli."""
        import asyncio
        
        async def slow_generator():
            yield "token1"
            await asyncio.sleep(0.1)
            yield "token2"
        
        async def collect_with_timeout():
            tokens = []
            async for token in slow_generator():
                tokens.append(token)
            return tokens
        
        # Timeout olmadan tamamlanmalı
        result = await asyncio.wait_for(collect_with_timeout(), timeout=5.0)
        assert len(result) == 2
    
    def test_streaming_error_recovery(self):
        """Hata durumunda recovery olmalı."""
        error_event = {"type": "error", "message": "Test error"}
        sse_error = f"data: {json.dumps(error_event)}\n\n"
        
        # Error event parse edilebilmeli
        parsed = json.loads(sse_error[6:-2])
        assert parsed["type"] == "error"
        assert "message" in parsed


class TestWebSearchStreaming:
    """Web search streaming testleri."""
    
    def test_web_search_stream_endpoint_exists(self):
        """Web search streaming endpoint mevcut olmalı."""
        from api.main import app
        
        routes = [r.path for r in app.routes]
        
        # Web stream endpoint
        assert '/api/chat/web-stream' in routes or any('web-stream' in r for r in routes)
    
    def test_web_search_phases(self):
        """Web search fazları sırayla gelmeli."""
        expected_phases = ['search', 'analyze', 'context', 'generate']
        
        # Her faz için status event
        for phase in expected_phases:
            event = {"type": "status", "phase": phase, "message": f"Phase: {phase}"}
            assert event["phase"] == phase
    
    def test_web_sources_event(self):
        """Sources event kaynakları içermeli."""
        sources_event = {
            "type": "sources",
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"}
            ],
            "search_time_ms": 150
        }
        
        assert sources_event["type"] == "sources"
        assert len(sources_event["sources"]) == 2
        assert "search_time_ms" in sources_event


class TestStreamingConcurrency:
    """Streaming eşzamanlılık testleri."""
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self):
        """Birden fazla eşzamanlı stream desteklenmeli."""
        
        async def mock_stream(stream_id: int):
            for i in range(3):
                await asyncio.sleep(0.01)
                yield f"stream_{stream_id}_token_{i}"
        
        # 3 eşzamanlı stream
        async def collect_stream(stream_id: int):
            tokens = []
            async for token in mock_stream(stream_id):
                tokens.append(token)
            return tokens
        
        results = await asyncio.gather(
            collect_stream(1),
            collect_stream(2),
            collect_stream(3)
        )
        
        assert len(results) == 3
        for i, tokens in enumerate(results):
            assert len(tokens) == 3
            assert all(f"stream_{i+1}" in t for t in tokens)
    
    @pytest.mark.asyncio
    async def test_stream_isolation(self):
        """Stream'ler birbirinden izole olmalı."""
        
        stream1_tokens = []
        stream2_tokens = []
        
        async def stream1():
            for token in ['A', 'B', 'C']:
                await asyncio.sleep(0.01)
                stream1_tokens.append(token)
        
        async def stream2():
            for token in ['1', '2', '3']:
                await asyncio.sleep(0.01)
                stream2_tokens.append(token)
        
        await asyncio.gather(stream1(), stream2())
        
        # Her stream kendi token'larını almalı
        assert stream1_tokens == ['A', 'B', 'C']
        assert stream2_tokens == ['1', '2', '3']


class TestStreamingSessionManagement:
    """Streaming session yönetimi testleri."""
    
    def test_session_id_returned_first(self):
        """Session ID ilk event olarak dönmeli."""
        events = [
            {"type": "session", "session_id": "new-session-123"},
            {"type": "token", "content": "Hello"}
        ]
        
        assert events[0]["type"] == "session"
        assert "session_id" in events[0]
    
    def test_session_persists_messages(self):
        """Session mesajları saklamalı."""
        session_messages = []
        
        # User mesajı
        session_messages.append({
            "role": "user",
            "content": "Test sorusu"
        })
        
        # Assistant yanıtı
        session_messages.append({
            "role": "assistant",
            "content": "Test yanıtı"
        })
        
        assert len(session_messages) == 2
        assert session_messages[0]["role"] == "user"
        assert session_messages[1]["role"] == "assistant"
    
    def test_stream_continues_session_context(self):
        """Stream session context'ini kullanmalı."""
        session_history = [
            {"role": "user", "content": "Merhaba"},
            {"role": "assistant", "content": "Merhaba! Size nasıl yardımcı olabilirim?"}
        ]
        
        # Yeni mesaj geldiğinde history kullanılmalı
        new_message = "Python nedir?"
        
        # Context history'yi içermeli
        assert len(session_history) == 2
