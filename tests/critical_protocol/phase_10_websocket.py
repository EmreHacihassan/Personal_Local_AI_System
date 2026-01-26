"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 10: WEBSOCKET                        ║
║                                                                                 ║
║  Tests: websocket.py, websocket_v2.py, real-time communication                ║
║  Scope: WebSocket connections and real-time messaging                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestResult:
    def __init__(self, name: str, passed: bool, error: str = None):
        self.name = name
        self.passed = passed
        self.error = error


class Phase10WebSocket:
    """Phase 10: WebSocket Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 10: WEBSOCKET"
        
    def print_header(self):
        print("\n" + "═" * 70)
        print(f"  {self.phase_name}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70)
        
    def add_result(self, name: str, passed: bool, error: str = None):
        self.results.append(TestResult(name, passed, error))
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if error and not passed:
            print(f"         └─ Error: {error[:80]}...")
            
    async def test_websocket_v1(self):
        """Test WebSocket V1 module"""
        print("\n  [10.1] WebSocket V1 Tests")
        print("  " + "-" * 40)
        
        try:
            from api.websocket import ConnectionManager
            self.add_result("WebSocket V1 Import", True)
        except ImportError:
            try:
                from api import websocket
                self.add_result("WebSocket V1 Import (module)", True)
            except Exception as e:
                self.add_result("WebSocket V1 Import", False, str(e))
                return
                
        try:
            from api.websocket import ConnectionManager
            ws = ConnectionManager()
            self.add_result("ConnectionManager Instantiation", ws is not None)
        except Exception as e:
            self.add_result("ConnectionManager Instantiation", False, str(e))
            
        try:
            from api.websocket import ConnectionManager
            ws = ConnectionManager()
            methods = ['connect', 'disconnect', 'send_message', 'broadcast']
            has_methods = any(hasattr(ws, m) for m in methods)
            self.add_result("WebSocket Methods Available", has_methods)
        except Exception as e:
            self.add_result("WebSocket Methods Available", False, str(e))
            
    async def test_websocket_v2(self):
        """Test WebSocket V2 module"""
        print("\n  [10.2] WebSocket V2 Tests")
        print("  " + "-" * 40)
        
        try:
            from api.websocket_v2 import WebSocketManagerV2
            self.add_result("WebSocket V2 Import", True)
        except ImportError:
            try:
                from api import websocket_v2
                self.add_result("WebSocket V2 Import (module)", True)
            except Exception as e:
                self.add_result("WebSocket V2 Import", False, str(e))
                return
                
        try:
            from api.websocket_v2 import WebSocketManagerV2
            ws = WebSocketManagerV2()
            self.add_result("WebSocketManagerV2 Instantiation", ws is not None)
        except Exception as e:
            self.add_result("WebSocketManagerV2 Instantiation", False, str(e))
            
    async def test_stream_buffer(self):
        """Test Stream Buffer module"""
        print("\n  [10.3] Stream Buffer Tests")
        print("  " + "-" * 40)
        
        try:
            from core.stream_buffer import StreamBuffer
            self.add_result("Stream Buffer Import", True)
        except ImportError:
            try:
                from core import stream_buffer
                self.add_result("Stream Buffer Import (module)", True)
            except Exception as e:
                self.add_result("Stream Buffer Import", False, str(e))
                return
                
        try:
            from core.stream_buffer import StreamBuffer
            buf = StreamBuffer()
            self.add_result("StreamBuffer Instantiation", buf is not None)
        except Exception as e:
            self.add_result("StreamBuffer Instantiation", False, str(e))
            
    async def test_streaming_handler(self):
        """Test Streaming Handler module"""
        print("\n  [10.4] Streaming Handler Tests")
        print("  " + "-" * 40)
        
        try:
            from core.streaming import StreamManager
            self.add_result("Streaming Handler Import", True)
        except ImportError:
            try:
                from core import streaming
                self.add_result("Streaming Handler Import (module)", True)
            except Exception as e:
                self.add_result("Streaming Handler Import", False, str(e))
                return
                
        try:
            from core.streaming import StreamManager
            handler = StreamManager()
            self.add_result("StreamManager Instantiation", handler is not None)
        except Exception as e:
            self.add_result("StreamManager Instantiation", False, str(e))
            
    async def run_all_tests(self):
        """Run all Phase 10 tests"""
        self.print_header()
        
        await self.test_websocket_v1()
        await self.test_websocket_v2()
        await self.test_stream_buffer()
        await self.test_streaming_handler()
        
        return self.get_summary()
        
    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "═" * 70)
        print(f"  {self.phase_name} - SUMMARY")
        print("═" * 70)
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({100*passed/total:.1f}%)" if total > 0 else "  No tests run")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            print(f"\n  Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"    ✗ {r.name}: {r.error[:60] if r.error else 'Unknown'}")
                    
        print("═" * 70 + "\n")
        
        return {
            "phase": self.phase_name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(100 * passed / total, 1) if total > 0 else 0
        }


async def main():
    phase = Phase10WebSocket()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
