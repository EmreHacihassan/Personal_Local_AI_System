"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 3: MEMORY & CACHE                    ║
║                                                                                 ║
║  Tests: memory, cache, session_manager, memgpt_memory, conversation            ║
║  Scope: Memory management, caching, and session handling                        ║
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


class Phase03MemoryCache:
    """Phase 3: Memory & Cache Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 3: MEMORY & CACHE"
        
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
            
    async def test_memory_module(self):
        """Test Memory module"""
        print("\n  [3.1] Memory Module Tests")
        print("  " + "-" * 40)
        
        try:
            from core.memory import MemoryManager
            self.add_result("Memory Import", True)
        except ImportError:
            try:
                from core import memory
                self.add_result("Memory Import (module)", True)
            except Exception as e:
                self.add_result("Memory Import", False, str(e))
                return
                
        try:
            from core.memory import MemoryManager
            mem = MemoryManager()
            self.add_result("MemoryManager Instantiation", mem is not None)
        except Exception as e:
            self.add_result("MemoryManager Instantiation", False, str(e))
            
        try:
            from core.memory import MemoryManager
            mem = MemoryManager()
            methods = ['add_message', 'get_messages', 'add_interaction', 'get_context_for_query', 'get_stats']
            has_methods = any(hasattr(mem, m) for m in methods)
            self.add_result("Memory Has CRUD Methods", has_methods)
        except Exception as e:
            self.add_result("Memory Has CRUD Methods", False, str(e))
            
    async def test_cache_module(self):
        """Test Cache module"""
        print("\n  [3.2] Cache Module Tests")
        print("  " + "-" * 40)
        
        try:
            from core.cache import CacheManager
            self.add_result("Cache Import", True)
        except ImportError:
            try:
                from core import cache
                self.add_result("Cache Import (module)", True)
            except Exception as e:
                self.add_result("Cache Import", False, str(e))
                return
                
        try:
            from core.cache import CacheManager
            cache_mgr = CacheManager()
            self.add_result("CacheManager Instantiation", cache_mgr is not None)
        except Exception as e:
            self.add_result("CacheManager Instantiation", False, str(e))
            
        try:
            from core.cache import CacheManager
            cache_mgr = CacheManager()
            has_set = hasattr(cache_mgr, 'set') or hasattr(cache_mgr, 'put')
            has_get = hasattr(cache_mgr, 'get')
            self.add_result("Cache Has Get/Set", has_set and has_get)
        except Exception as e:
            self.add_result("Cache Has Get/Set", False, str(e))
            
    async def test_session_manager(self):
        """Test Session Manager module"""
        print("\n  [3.3] Session Manager Tests")
        print("  " + "-" * 40)
        
        try:
            from core.session_manager import SessionManager
            self.add_result("Session Manager Import", True)
        except ImportError:
            try:
                from core import session_manager
                self.add_result("Session Manager Import (module)", True)
            except Exception as e:
                self.add_result("Session Manager Import", False, str(e))
                return
                
        try:
            from core.session_manager import SessionManager
            sm = SessionManager()
            self.add_result("SessionManager Instantiation", sm is not None)
        except Exception as e:
            self.add_result("SessionManager Instantiation", False, str(e))
            
        try:
            from core.session_manager import SessionManager
            sm = SessionManager()
            methods = ['create_session', 'get_session', 'end_session']
            has_methods = any(hasattr(sm, m) for m in methods)
            self.add_result("Session Manager Methods", has_methods)
        except Exception as e:
            self.add_result("Session Manager Methods", False, str(e))
            
    async def test_memgpt_memory(self):
        """Test MemGPT Memory module"""
        print("\n  [3.4] MemGPT Memory Tests")
        print("  " + "-" * 40)
        
        try:
            from core.memgpt_memory import TieredMemoryManager, SQLiteMemoryStorage
            self.add_result("MemGPT Memory Import", True)
        except ImportError:
            try:
                from core import memgpt_memory
                self.add_result("MemGPT Memory Import (module)", True)
            except Exception as e:
                self.add_result("MemGPT Memory Import", False, str(e))
                return
                
        try:
            import tempfile
            from pathlib import Path
            from core.memgpt_memory import TieredMemoryManager, SQLiteMemoryStorage
            # Use temp db path for testing
            temp_db = Path(tempfile.gettempdir()) / "test_tiered_memory.db"
            storage = SQLiteMemoryStorage(db_path=temp_db)
            mem = TieredMemoryManager(storage=storage)
            self.add_result("TieredMemoryManager Instantiation", mem is not None)
        except Exception as e:
            self.add_result("TieredMemoryManager Instantiation", False, str(e))
            
    async def test_conversation_module(self):
        """Test Conversation module"""
        print("\n  [3.5] Conversation Module Tests")
        print("  " + "-" * 40)
        
        try:
            from core.conversation import Conversation
            self.add_result("Conversation Import", True)
        except ImportError:
            try:
                from core import conversation
                self.add_result("Conversation Import (module)", True)
            except Exception as e:
                self.add_result("Conversation Import", False, str(e))
                return
                
        try:
            from core.conversation import Conversation
            conv = Conversation()
            self.add_result("Conversation Instantiation", conv is not None)
        except Exception as e:
            self.add_result("Conversation Instantiation", False, str(e))
            
        try:
            from core.conversation import Conversation
            conv = Conversation()
            methods = ['add_message', 'get_history', 'clear', 'add_user_message', 'add_assistant_message']
            has_methods = any(hasattr(conv, m) for m in methods)
            self.add_result("Conversation Methods", has_methods)
        except Exception as e:
            self.add_result("Conversation Methods", False, str(e))
            
    async def test_memory_engine(self):
        """Test Memory Engine module"""
        print("\n  [3.6] Memory Engine Tests")
        print("  " + "-" * 40)
        
        try:
            from core.memory_engine import MemoryEngine
            self.add_result("Memory Engine Import", True)
        except ImportError:
            try:
                from core import memory_engine
                self.add_result("Memory Engine Import (module)", True)
            except Exception as e:
                self.add_result("Memory Engine Import", False, str(e))
                return
                
        try:
            from core.memory_engine import MemoryEngine
            engine = MemoryEngine()
            self.add_result("MemoryEngine Instantiation", engine is not None)
        except Exception as e:
            self.add_result("MemoryEngine Instantiation", False, str(e))
            
    async def run_all_tests(self):
        """Run all Phase 3 tests"""
        self.print_header()
        
        await self.test_memory_module()
        await self.test_cache_module()
        await self.test_session_manager()
        await self.test_memgpt_memory()
        await self.test_conversation_module()
        await self.test_memory_engine()
        
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
    phase = Phase03MemoryCache()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
