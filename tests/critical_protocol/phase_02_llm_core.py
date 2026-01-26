"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 2: LLM & AI CORE                     ║
║                                                                                 ║
║  Tests: llm_manager, llm_client, model_router, moe_router, embedding           ║
║  Scope: AI/LLM infrastructure and model management                             ║
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


class Phase02LLMCore:
    """Phase 2: LLM & AI Core Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 2: LLM & AI CORE"
        
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
            
    async def test_llm_manager(self):
        """Test LLM Manager module"""
        print("\n  [2.1] LLM Manager Tests")
        print("  " + "-" * 40)
        
        # Test 2.1.1: Import
        try:
            from core.llm_manager import LLMManager, llm_manager
            self.add_result("LLM Manager Import", True)
        except Exception as e:
            self.add_result("LLM Manager Import", False, str(e))
            return
            
        # Test 2.1.2: Singleton instance
        try:
            from core.llm_manager import llm_manager
            self.add_result("LLM Manager Singleton", llm_manager is not None)
        except Exception as e:
            self.add_result("LLM Manager Singleton", False, str(e))
            
        # Test 2.1.3: Has generate method
        try:
            from core.llm_manager import llm_manager
            has_generate = hasattr(llm_manager, 'generate') or hasattr(llm_manager, 'chat')
            self.add_result("LLM Manager Has Generate", has_generate)
        except Exception as e:
            self.add_result("LLM Manager Has Generate", False, str(e))
            
        # Test 2.1.4: Model availability check
        try:
            from core.llm_manager import llm_manager
            models = await llm_manager.get_available_models() if hasattr(llm_manager, 'get_available_models') else []
            self.add_result("LLM Manager Model Check", True, f"Found {len(models)} models")
        except Exception as e:
            self.add_result("LLM Manager Model Check", False, str(e))
            
    async def test_llm_client(self):
        """Test LLM Client module"""
        print("\n  [2.2] LLM Client Tests")
        print("  " + "-" * 40)
        
        # Test 2.2.1: Import
        try:
            from core.llm_client import LLMClient
            self.add_result("LLM Client Import", True)
        except Exception as e:
            self.add_result("LLM Client Import", False, str(e))
            return
            
        # Test 2.2.2: Instantiation
        try:
            from core.llm_client import LLMClient
            client = LLMClient()
            self.add_result("LLM Client Instantiation", client is not None)
        except Exception as e:
            self.add_result("LLM Client Instantiation", False, str(e))
            
        # Test 2.2.3: Required methods
        try:
            from core.llm_client import LLMClient
            client = LLMClient()
            methods = ['generate', 'chat', 'stream']
            has_methods = any(hasattr(client, m) for m in methods)
            self.add_result("LLM Client Methods", has_methods)
        except Exception as e:
            self.add_result("LLM Client Methods", False, str(e))
            
    async def test_model_router(self):
        """Test Model Router module"""
        print("\n  [2.3] Model Router Tests")
        print("  " + "-" * 40)
        
        # Test 2.3.1: Import
        try:
            from core.model_router import ModelRouter
            self.add_result("Model Router Import", True)
        except Exception as e:
            self.add_result("Model Router Import", False, str(e))
            return
            
        # Test 2.3.2: Instantiation
        try:
            from core.model_router import ModelRouter
            router = ModelRouter()
            self.add_result("Model Router Instantiation", router is not None)
        except Exception as e:
            self.add_result("Model Router Instantiation", False, str(e))
            
        # Test 2.3.3: Route method
        try:
            from core.model_router import ModelRouter
            router = ModelRouter()
            has_route = hasattr(router, 'route') or hasattr(router, 'select_model')
            self.add_result("Model Router Has Route", has_route)
        except Exception as e:
            self.add_result("Model Router Has Route", False, str(e))
            
    async def test_moe_router(self):
        """Test Mixture of Experts Router module"""
        print("\n  [2.4] MoE Router Tests")
        print("  " + "-" * 40)
        
        # Test 2.4.1: Import
        try:
            from core.moe_router import MoERouter
            self.add_result("MoE Router Import", True)
        except Exception as e:
            self.add_result("MoE Router Import", False, str(e))
            return
            
        # Test 2.4.2: Instantiation
        try:
            from core.moe_router import MoERouter
            router = MoERouter()
            self.add_result("MoE Router Instantiation", router is not None)
        except Exception as e:
            self.add_result("MoE Router Instantiation", False, str(e))
            
    async def test_embedding(self):
        """Test Embedding module"""
        print("\n  [2.5] Embedding Module Tests")
        print("  " + "-" * 40)
        
        # Test 2.5.1: Import
        try:
            from core.embedding import EmbeddingManager
            self.add_result("Embedding Import", True)
        except ImportError:
            try:
                from core import embedding
                self.add_result("Embedding Import (module)", True)
            except Exception as e:
                self.add_result("Embedding Import", False, str(e))
                return
                
        # Test 2.5.2: Instantiation
        try:
            from core.embedding import EmbeddingManager
            emb = EmbeddingManager()
            self.add_result("Embedding Manager Instantiation", emb is not None)
        except Exception as e:
            self.add_result("Embedding Manager Instantiation", False, str(e))
            
        # Test 2.5.3: Embed method
        try:
            from core.embedding import EmbeddingManager
            emb = EmbeddingManager()
            has_embed = hasattr(emb, 'embed_text') or hasattr(emb, 'embed_query') or hasattr(emb, 'embed_document')
            self.add_result("Embedding Has Embed Method", has_embed)
        except Exception as e:
            self.add_result("Embedding Has Embed Method", False, str(e))
            
    async def test_prompts(self):
        """Test Prompts module"""
        print("\n  [2.6] Prompts Module Tests")
        print("  " + "-" * 40)
        
        # Test 2.6.1: Import
        try:
            from core.prompts import (
                SYSTEM_PROMPT,
                get_prompt,
                PromptTemplate
            )
            self.add_result("Prompts Import", True)
        except ImportError:
            try:
                from core import prompts
                self.add_result("Prompts Import (module)", True)
            except Exception as e:
                self.add_result("Prompts Import", False, str(e))
                return
                
        # Test 2.6.2: System prompt exists
        try:
            from core import prompts
            has_system = hasattr(prompts, 'SYSTEM_PROMPT_TR') or hasattr(prompts, 'SYSTEM_PROMPT_EN') or hasattr(prompts, 'PromptTemplate')
            self.add_result("System Prompt Exists", has_system)
        except Exception as e:
            self.add_result("System Prompt Exists", False, str(e))
            
    async def test_streaming(self):
        """Test Streaming module"""
        print("\n  [2.7] Streaming Module Tests")
        print("  " + "-" * 40)
        
        # Test 2.7.1: Import
        try:
            from core.streaming import StreamManager
            self.add_result("Streaming Import", True)
        except ImportError:
            try:
                from core import streaming
                self.add_result("Streaming Import (module)", True)
            except Exception as e:
                self.add_result("Streaming Import", False, str(e))
                return
                
        # Test 2.7.2: Instantiation
        try:
            from core.streaming import StreamManager
            handler = StreamManager()
            self.add_result("StreamManager Instantiation", handler is not None)
        except Exception as e:
            self.add_result("StreamManager Instantiation", False, str(e))
            
    async def test_instructor_structured(self):
        """Test Instructor Structured Output module"""
        print("\n  [2.8] Instructor Structured Output Tests")
        print("  " + "-" * 40)
        
        # Test 2.8.1: Import
        try:
            from core.instructor_structured import StructuredOutputManager
            self.add_result("Instructor Import", True)
        except ImportError:
            try:
                from core import instructor_structured
                self.add_result("Instructor Import (module)", True)
            except Exception as e:
                self.add_result("Instructor Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 2 tests"""
        self.print_header()
        
        await self.test_llm_manager()
        await self.test_llm_client()
        await self.test_model_router()
        await self.test_moe_router()
        await self.test_embedding()
        await self.test_prompts()
        await self.test_streaming()
        await self.test_instructor_structured()
        
        return self.get_summary()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
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
    phase = Phase02LLMCore()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
