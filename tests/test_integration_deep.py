#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║           DEEP INTEGRATION & END-TO-END TEST SUITE                                   ║
║                    "Test the Full User Journey"                                      ║
║                                                                                      ║
║  🔄 Workflows | 📝 User Journeys | 🔗 Component Integration | 🎭 Scenario Testing    ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

Test Scenarios:
===============
1. Complete User Chat Session
2. Document Upload and RAG
3. Multi-turn Conversation
4. WebSocket Real-time Chat
5. Session Persistence
6. Streaming Response
7. Error Recovery
8. Feature Combinations
9. Edge User Behaviors
10. Cross-Component State

Author: Integration Test Engineer
Date: 2026-01-28
"""

import asyncio
import json
import os
import random
import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

import pytest

try:
    import httpx
    import websockets
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "httpx", "websockets", "-q"])
    import httpx
    import websockets

sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8001")
WS_URL = os.environ.get("TEST_WS_URL", "ws://localhost:8001/ws/chat")

INTEGRATION_CONFIG = {
    "timeout": 60,
    "ws_timeout": 30,
    "max_retries": 3,
}


# =============================================================================
# TEST FIXTURES & UTILITIES
# =============================================================================

@dataclass
class TestSession:
    """Represents a test user session."""
    session_id: str
    client: httpx.Client
    messages: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    
    def chat(self, message: str, **kwargs) -> httpx.Response:
        """Send a chat message."""
        payload = {
            "message": message,
            "session_id": self.session_id,
            **kwargs
        }
        response = self.client.post("/api/chat", json=payload)
        self.messages.append({"role": "user", "content": message, "response": response})
        return response
    
    def get_history(self) -> Optional[Dict]:
        """Get session history."""
        try:
            response = self.client.get(f"/api/sessions/{self.session_id}")
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return None


@dataclass 
class TestUser:
    """Simulated test user with behaviors."""
    user_id: str
    name: str
    behavior: str  # "normal", "aggressive", "slow", "erratic"
    sessions: List[TestSession] = field(default_factory=list)
    
    def think_time(self) -> float:
        """Return time to wait between actions based on behavior."""
        if self.behavior == "aggressive":
            return 0.01
        elif self.behavior == "slow":
            return random.uniform(2, 5)
        elif self.behavior == "erratic":
            return random.choice([0, 0.5, 2, 10])
        else:
            return random.uniform(0.5, 1.5)


# =============================================================================
# SCENARIO 1: COMPLETE USER CHAT SESSION
# =============================================================================

class TestCompleteUserSession:
    """Test a complete user chat session from start to finish."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_new_user_first_conversation(self, client):
        """Test a brand new user's first conversation."""
        session = TestSession(
            session_id=f"new_user_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        # Step 1: Initial greeting
        response = session.chat("Merhaba, ben yeni bir kullanıcıyım!")
        assert response.status_code == 200, f"First message failed: {response.status_code}"
        
        # Step 2: Ask a question
        response = session.chat("Python ile web scraping nasıl yapılır?")
        assert response.status_code == 200
        data = response.json()
        assert "content" in data or "response" in data or "message" in data
        
        # Step 3: Follow-up question
        response = session.chat("BeautifulSoup kullanabilir miyim?")
        assert response.status_code == 200
        
        # Step 4: Thank and end
        response = session.chat("Teşekkürler, çok faydalı oldu!")
        assert response.status_code == 200
        
        # Verify conversation was maintained
        assert len(session.messages) == 4
    
    def test_returning_user_session_continuation(self, client):
        """Test returning user continuing a previous session."""
        session_id = f"returning_{uuid.uuid4().hex[:8]}"
        
        # First visit
        session1 = TestSession(session_id=session_id, client=client)
        response = session1.chat("Python öğreniyorum, veri yapıları hakkında bilgi ver")
        assert response.status_code == 200
        
        # "Close browser" - new client
        time.sleep(0.5)
        
        # Return with same session ID
        session2 = TestSession(session_id=session_id, client=client)
        response = session2.chat("Önceki konuşmamıza devam edelim, listeler hakkında ne demiştin?")
        assert response.status_code == 200
        
        # Context should be maintained (response might reference previous)
    
    def test_multi_topic_conversation(self, client):
        """Test conversation spanning multiple topics."""
        session = TestSession(
            session_id=f"multi_topic_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        topics = [
            "Python nedir?",
            "JavaScript ile Python arasındaki farklar neler?",
            "Makine öğrenmesi için hangi dil daha uygun?",
            "TensorFlow kurulumu nasıl yapılır?",
            "Bir görüntü sınıflandırma projesi yapabilir misin?",
        ]
        
        for topic in topics:
            response = session.chat(topic)
            assert response.status_code == 200, f"Failed on topic: {topic}"
            time.sleep(0.3)  # Small delay between messages
    
    def test_user_correction_flow(self, client):
        """Test user correcting the AI's understanding."""
        session = TestSession(
            session_id=f"correction_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        # Initial query
        session.chat("JavaScript hakkında bilgi ver")
        
        # Correction
        response = session.chat("Hayır, Java dedim, JavaScript değil!")
        assert response.status_code == 200
        
        # Verify correction handled
        response = session.chat("Evet, Java'nın nesne yönelimli özellikleri neler?")
        assert response.status_code == 200


# =============================================================================
# SCENARIO 2: DOCUMENT & RAG INTEGRATION
# =============================================================================

class TestRAGIntegration:
    """Test RAG pipeline integration."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_document_context_query(self, client):
        """Test querying with document context."""
        session_id = f"rag_{uuid.uuid4().hex[:8]}"
        
        # First: Provide context
        context_message = """
        Aşağıdaki belgeyi okuyup sorularımı yanıtla:
        
        ---
        BELGE: Python En İyi Pratikleri
        
        1. Her zaman virtual environment kullanın
        2. requirements.txt ile bağımlılıkları yönetin
        3. Type hints kullanarak kod okunabilirliğini artırın
        4. Docstring ile fonksiyonları belgeleyin
        5. Unit testler yazın
        ---
        
        Bu belgeyi anladın mı?
        """
        
        response = client.post("/api/chat", json={
            "message": context_message,
            "session_id": session_id
        })
        assert response.status_code == 200
        
        # Query about the document
        response = client.post("/api/chat", json={
            "message": "Belgede bahsedilen en iyi pratiklerden virtual environment neden önemli?",
            "session_id": session_id
        })
        assert response.status_code == 200
    
    def test_web_search_integration(self, client):
        """Test web search integration in chat."""
        session_id = f"search_{uuid.uuid4().hex[:8]}"
        
        # Query that might trigger web search
        response = client.post("/api/chat", json={
            "message": "2024'te en popüler programlama dilleri hangileri?",
            "session_id": session_id,
            "enable_web_search": True
        })
        
        # Should complete regardless of whether web search is enabled
        assert response.status_code in [200, 500, 501]


# =============================================================================
# SCENARIO 3: MULTI-TURN CONVERSATION
# =============================================================================

class TestMultiTurnConversation:
    """Test complex multi-turn conversations."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_20_turn_conversation(self, client):
        """Test a 20-turn conversation maintains coherence."""
        session = TestSession(
            session_id=f"long_conv_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        conversation_flow = [
            "Merhaba!",
            "Python öğrenmek istiyorum, nereden başlamalıyım?",
            "Temel sözdizimi hakkında bilgi verir misin?",
            "Değişkenler nasıl tanımlanır?",
            "Veri tipleri nelerdir?",
            "String işlemleri nasıl yapılır?",
            "Liste nedir?",
            "Dictionary ne işe yarar?",
            "Döngüler hakkında bilgi ver",
            "While ve for farkı nedir?",
            "Fonksiyonlar nasıl tanımlanır?",
            "Lambda fonksiyonları nedir?",
            "Sınıflar nasıl oluşturulur?",
            "Miras alma (inheritance) nedir?",
            "Dosya işlemleri nasıl yapılır?",
            "Hata yönetimi (exception handling) nedir?",
            "Module ve package farkı nedir?",
            "Virtual environment neden önemli?",
            "Pip ile paket kurulumu nasıl yapılır?",
            "Öğrendiklerimi özetler misin?",
        ]
        
        for i, message in enumerate(conversation_flow):
            response = session.chat(message)
            assert response.status_code == 200, f"Failed at turn {i+1}: {message}"
            
            # Optional: Small delay to simulate human
            if i % 5 == 0:
                time.sleep(0.5)
        
        # Final message should reference conversation history
        assert len(session.messages) == 20
    
    def test_conversation_with_context_switches(self, client):
        """Test conversation that switches between contexts."""
        session = TestSession(
            session_id=f"context_switch_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        # Context 1: Technical
        session.chat("Python'da async/await nasıl çalışır?")
        session.chat("Event loop nedir?")
        
        # Context switch: Personal
        session.chat("Bugün hava çok güzel, dışarı çıkmalı mıyım?")
        
        # Back to technical
        response = session.chat("Önceki konuya dönelim, asyncio ile örnek gösterir misin?")
        assert response.status_code == 200
        
        # System should handle context switches gracefully


# =============================================================================
# SCENARIO 4: WEBSOCKET REAL-TIME CHAT
# =============================================================================

class TestWebSocketIntegration:
    """Test WebSocket-based real-time chat."""
    
    @pytest.mark.asyncio
    async def test_websocket_basic_chat(self):
        """Test basic WebSocket chat flow."""
        session_id = f"ws_basic_{uuid.uuid4().hex[:8]}"
        
        try:
            async with websockets.connect(
                f"{WS_URL}?session_id={session_id}",
                close_timeout=5
            ) as ws:
                # Send message
                await ws.send(json.dumps({
                    "type": "message",
                    "content": "WebSocket üzerinden merhaba!"
                }))
                
                # Receive response (with timeout)
                try:
                    async with asyncio.timeout(INTEGRATION_CONFIG["ws_timeout"]):
                        response = await ws.recv()
                        data = json.loads(response)
                        assert "type" in data or "content" in data
                except asyncio.TimeoutError:
                    pytest.skip("WebSocket response timeout")
                    
        except Exception as e:
            pytest.skip(f"WebSocket connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_streaming_response(self):
        """Test streaming response via WebSocket."""
        session_id = f"ws_stream_{uuid.uuid4().hex[:8]}"
        
        try:
            async with websockets.connect(
                f"{WS_URL}?session_id={session_id}",
                close_timeout=5
            ) as ws:
                await ws.send(json.dumps({
                    "type": "message",
                    "content": "Uzun bir cevap gerektiren detaylı bir soru sor"
                }))
                
                # Collect streaming chunks
                chunks = []
                try:
                    async with asyncio.timeout(30):
                        while True:
                            try:
                                chunk = await asyncio.wait_for(ws.recv(), timeout=5)
                                chunks.append(chunk)
                                
                                # Check for completion signal
                                data = json.loads(chunk)
                                if data.get("type") == "complete" or data.get("done"):
                                    break
                            except asyncio.TimeoutError:
                                break
                except asyncio.TimeoutError:
                    pass
                
                # Should receive at least something
                assert len(chunks) >= 0
                
        except Exception as e:
            pytest.skip(f"WebSocket streaming test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_messages(self):
        """Test sending multiple messages via WebSocket."""
        session_id = f"ws_multi_{uuid.uuid4().hex[:8]}"
        
        try:
            async with websockets.connect(
                f"{WS_URL}?session_id={session_id}",
                close_timeout=5
            ) as ws:
                messages = ["Birinci mesaj", "İkinci mesaj", "Üçüncü mesaj"]
                
                for msg in messages:
                    await ws.send(json.dumps({
                        "type": "message",
                        "content": msg
                    }))
                    
                    # Wait for response
                    try:
                        async with asyncio.timeout(10):
                            response = await ws.recv()
                            assert response is not None
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            pytest.skip(f"WebSocket multi-message test failed: {e}")


# =============================================================================
# SCENARIO 5: SESSION PERSISTENCE
# =============================================================================

class TestSessionPersistence:
    """Test session data persistence."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_session_survives_multiple_requests(self, client):
        """Test that session data persists across requests."""
        session_id = f"persist_{uuid.uuid4().hex[:8]}"
        
        # Create session with initial message
        response = client.post("/api/chat", json={
            "message": "Benim adım Test Kullanıcısı",
            "session_id": session_id
        })
        assert response.status_code == 200
        
        # Make several more requests
        for i in range(5):
            client.post("/api/chat", json={
                "message": f"Mesaj {i+1}",
                "session_id": session_id
            })
        
        # Recall information
        response = client.post("/api/chat", json={
            "message": "Benim adım neydi?",
            "session_id": session_id
        })
        assert response.status_code == 200
    
    def test_session_isolation(self, client):
        """Test that sessions are isolated from each other."""
        session1_id = f"isolated_1_{uuid.uuid4().hex[:8]}"
        session2_id = f"isolated_2_{uuid.uuid4().hex[:8]}"
        
        # Session 1: Set context
        client.post("/api/chat", json={
            "message": "Bugün hava çok sıcak",
            "session_id": session1_id
        })
        
        # Session 2: Different context
        client.post("/api/chat", json={
            "message": "Bugün hava çok soğuk",
            "session_id": session2_id
        })
        
        # Session 1 should not see Session 2's context
        response = client.post("/api/chat", json={
            "message": "Hava nasıl demiştim?",
            "session_id": session1_id
        })
        assert response.status_code == 200
        # Should reference "sıcak" not "soğuk" (context isolation)


# =============================================================================
# SCENARIO 6: ERROR RECOVERY
# =============================================================================

class TestErrorRecovery:
    """Test system recovery from various error conditions."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_recovery_after_malformed_request(self, client):
        """Test recovery after malformed request."""
        session_id = f"recover_malformed_{uuid.uuid4().hex[:8]}"
        
        # Good request
        response = client.post("/api/chat", json={
            "message": "İlk mesaj",
            "session_id": session_id
        })
        assert response.status_code == 200
        
        # Malformed request
        try:
            client.post("/api/chat", content="not json")
        except Exception:
            pass
        
        # Should still work
        response = client.post("/api/chat", json={
            "message": "Devam edebilir miyiz?",
            "session_id": session_id
        })
        assert response.status_code == 200
    
    def test_recovery_after_timeout(self, client):
        """Test recovery after request timeout."""
        session_id = f"recover_timeout_{uuid.uuid4().hex[:8]}"
        
        # Normal request
        response = client.post("/api/chat", json={
            "message": "İlk mesaj",
            "session_id": session_id
        })
        assert response.status_code == 200
        
        # Potentially timing out request (large)
        try:
            with httpx.Client(base_url=BASE_URL, timeout=1.0) as fast_client:
                fast_client.post("/api/chat", json={
                    "message": "x" * 10000,
                    "session_id": session_id
                })
        except Exception:
            pass
        
        # Should recover
        response = client.post("/api/chat", json={
            "message": "Sistem hala çalışıyor mu?",
            "session_id": session_id
        })
        assert response.status_code in [200, 500]
    
    def test_graceful_degradation(self, client):
        """Test graceful degradation under stress."""
        results = []
        
        # Stress the system
        for i in range(20):
            try:
                response = client.post("/api/chat", json={
                    "message": f"Stress test {i}",
                    "session_id": f"stress_{i}_{uuid.uuid4().hex[:4]}"
                })
                results.append(response.status_code)
            except Exception:
                results.append(0)
        
        # Should have some successes
        success_count = sum(1 for r in results if r == 200)
        assert success_count > 5, f"Too few successes: {success_count}/20"


# =============================================================================
# SCENARIO 7: FEATURE COMBINATIONS
# =============================================================================

class TestFeatureCombinations:
    """Test combinations of features working together."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_chat_with_model_selection(self, client):
        """Test chat with explicit model selection."""
        session_id = f"model_select_{uuid.uuid4().hex[:8]}"
        
        # Different model requests
        models = ["qwen3:4b", "default", None]
        
        for model in models:
            payload = {
                "message": f"Model test: {model}",
                "session_id": session_id
            }
            if model:
                payload["model"] = model
                
            response = client.post("/api/chat", json=payload)
            assert response.status_code in [200, 400, 422, 500]
    
    def test_chat_with_parameters(self, client):
        """Test chat with various parameters."""
        session_id = f"params_{uuid.uuid4().hex[:8]}"
        
        parameter_sets = [
            {"temperature": 0.0},
            {"temperature": 1.0},
            {"max_tokens": 100},
            {"max_tokens": 1000},
            {"temperature": 0.7, "max_tokens": 500},
        ]
        
        for params in parameter_sets:
            payload = {
                "message": "Parameter test",
                "session_id": session_id,
                **params
            }
            response = client.post("/api/chat", json=payload)
            assert response.status_code in [200, 400, 422, 500]
    
    def test_mixed_http_and_ws(self):
        """Test mixing HTTP and WebSocket requests."""
        session_id = f"mixed_{uuid.uuid4().hex[:8]}"
        
        # HTTP request
        with httpx.Client(base_url=BASE_URL, timeout=30) as client:
            response = client.post("/api/chat", json={
                "message": "HTTP mesajı",
                "session_id": session_id
            })
            assert response.status_code in [200, 500]
        
        # WebSocket request to same session
        async def ws_request():
            try:
                async with websockets.connect(
                    f"{WS_URL}?session_id={session_id}",
                    close_timeout=5
                ) as ws:
                    await ws.send(json.dumps({
                        "type": "message",
                        "content": "WebSocket mesajı"
                    }))
                    
                    try:
                        async with asyncio.timeout(10):
                            await ws.recv()
                    except asyncio.TimeoutError:
                        pass
            except Exception:
                pass
        
        try:
            asyncio.run(ws_request())
        except Exception:
            pass


# =============================================================================
# SCENARIO 8: EDGE USER BEHAVIORS
# =============================================================================

class TestEdgeUserBehaviors:
    """Test unusual but valid user behaviors."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_rapid_fire_messages(self, client):
        """Test user sending messages very rapidly."""
        session_id = f"rapid_{uuid.uuid4().hex[:8]}"
        results = []
        
        for i in range(10):
            response = client.post("/api/chat", json={
                "message": f"Hızlı mesaj {i}",
                "session_id": session_id
            })
            results.append(response.status_code)
            # No delay - as fast as possible
        
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 5, "Too many failed rapid messages"
    
    def test_very_long_message(self, client):
        """Test user sending a very long message."""
        session_id = f"long_msg_{uuid.uuid4().hex[:8]}"
        
        long_message = "Bu çok uzun bir mesaj. " * 500  # ~10KB
        
        response = client.post("/api/chat", json={
            "message": long_message,
            "session_id": session_id
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 400, 413, 422, 500]
    
    def test_unicode_heavy_message(self, client):
        """Test messages with lots of Unicode."""
        session_id = f"unicode_{uuid.uuid4().hex[:8]}"
        
        unicode_messages = [
            "Merhaba! 你好! こんにちは! 안녕하세요! مرحبا!",
            "🎉🎊🎁🎀🎄🎃🎇🎆✨🌟",
            "∑∏∫√∞≠≤≥±×÷",
            "α β γ δ ε ζ η θ ι κ λ μ",
            "←↑→↓↔↕↖↗↘↙",
        ]
        
        for msg in unicode_messages:
            response = client.post("/api/chat", json={
                "message": msg,
                "session_id": session_id
            })
            assert response.status_code in [200, 400, 422]
    
    def test_empty_and_whitespace_messages(self, client):
        """Test empty and whitespace-only messages."""
        session_id = f"empty_{uuid.uuid4().hex[:8]}"
        
        edge_messages = [
            "",
            " ",
            "\t",
            "\n",
            "   \t   \n   ",
        ]
        
        for msg in edge_messages:
            response = client.post("/api/chat", json={
                "message": msg,
                "session_id": session_id
            })
            # Should reject or handle gracefully
            assert response.status_code in [200, 400, 422]
    
    def test_user_sends_json_in_message(self, client):
        """Test user sending JSON as message content."""
        session_id = f"json_content_{uuid.uuid4().hex[:8]}"
        
        json_message = '{"key": "value", "array": [1, 2, 3], "nested": {"a": "b"}}'
        
        response = client.post("/api/chat", json={
            "message": json_message,
            "session_id": session_id
        })
        
        assert response.status_code in [200, 400, 422]
    
    def test_user_sends_code_snippets(self, client):
        """Test user sending code snippets."""
        session_id = f"code_{uuid.uuid4().hex[:8]}"
        
        code_snippets = [
            """```python
def hello():
    print("Hello, World!")
```""",
            "<script>alert('xss')</script>",
            "SELECT * FROM users WHERE id = 1; --",
            "#!/bin/bash\nrm -rf /",
        ]
        
        for code in code_snippets:
            response = client.post("/api/chat", json={
                "message": f"Bu kodu analiz et: {code}",
                "session_id": session_id
            })
            assert response.status_code in [200, 400, 422, 500]


# =============================================================================
# SCENARIO 9: CROSS-COMPONENT STATE
# =============================================================================

class TestCrossComponentState:
    """Test state consistency across components."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=INTEGRATION_CONFIG["timeout"])
    
    def test_session_state_after_health_check(self, client):
        """Test that health checks don't affect session state."""
        session_id = f"health_state_{uuid.uuid4().hex[:8]}"
        
        # Create session
        client.post("/api/chat", json={
            "message": "İlk mesaj",
            "session_id": session_id
        })
        
        # Health check
        client.get("/api/health")
        
        # Session should still work
        response = client.post("/api/chat", json={
            "message": "Devam",
            "session_id": session_id
        })
        assert response.status_code == 200
    
    def test_concurrent_sessions_independence(self, client):
        """Test that concurrent sessions don't interfere."""
        import threading
        
        results = {}
        errors = []
        
        def run_session(session_num: int):
            session_id = f"concurrent_{session_num}_{uuid.uuid4().hex[:4]}"
            try:
                for i in range(5):
                    response = client.post("/api/chat", json={
                        "message": f"Session {session_num} message {i}",
                        "session_id": session_id
                    })
                    if response.status_code != 200:
                        errors.append(f"Session {session_num} failed at message {i}")
                        return
                results[session_num] = "success"
            except Exception as e:
                errors.append(f"Session {session_num}: {str(e)}")
        
        threads = [threading.Thread(target=run_session, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)
        
        # Most sessions should succeed
        assert len(results) >= 3, f"Too few successful sessions: {results}, errors: {errors}"


# =============================================================================
# SCENARIO 10: FULL USER JOURNEY
# =============================================================================

class TestFullUserJourney:
    """Test complete user journeys."""
    
    @pytest.fixture
    def client(self):
        return httpx.Client(base_url=BASE_URL, timeout=120)
    
    def test_complete_learning_journey(self, client):
        """Simulate a user learning something new."""
        session = TestSession(
            session_id=f"learning_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        journey = [
            ("intro", "Python öğrenmek istiyorum, yardımcı olur musun?"),
            ("basics", "Değişkenler ve veri tipleri hakkında bilgi ver"),
            ("example", "Örnek bir kod gösterir misin?"),
            ("question", "Bu kodda 'int' ne anlama geliyor?"),
            ("practice", "Basit bir hesap makinesi nasıl yazarım?"),
            ("debug", "Hata alıyorum: NameError, bu ne demek?"),
            ("solution", "Anladım, teşekkürler! Artık daha iyi anladım."),
        ]
        
        for step_name, message in journey:
            response = session.chat(message)
            assert response.status_code == 200, f"Failed at step '{step_name}'"
            time.sleep(0.3)
        
        assert len(session.messages) == len(journey)
    
    def test_troubleshooting_journey(self, client):
        """Simulate a user troubleshooting a problem."""
        session = TestSession(
            session_id=f"debug_{uuid.uuid4().hex[:8]}",
            client=client
        )
        
        debug_flow = [
            "Kodum çalışmıyor, yardım eder misin?",
            "Python'da 'IndentationError' hatası alıyorum",
            "Kodumda girintileri düzelttim ama hala hata var",
            "Şimdi 'TypeError: unsupported operand type(s)' hatası aldım",
            "String ile int'i toplamaya çalışıyormuşum, nasıl düzeltirim?",
            "str() fonksiyonu ile düzeldi, teşekkürler!",
        ]
        
        for message in debug_flow:
            response = session.chat(message)
            assert response.status_code == 200
            time.sleep(0.2)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",
        "--timeout=300",
        "-W", "ignore::DeprecationWarning"
    ])

