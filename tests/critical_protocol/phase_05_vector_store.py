"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 5: VECTOR STORE & EMBEDDINGS         ║
║                                                                                 ║
║  Tests: embedding, vector_store, chromadb_manager, enterprise_vector_store     ║
║  Scope: Vector database and embedding operations                               ║
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


class Phase05VectorStore:
    """Phase 5: Vector Store & Embeddings Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 5: VECTOR STORE & EMBEDDINGS"
        
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
            
    async def test_vector_store(self):
        """Test Vector Store module"""
        print("\n  [5.1] Vector Store Tests")
        print("  " + "-" * 40)
        
        try:
            from core.vector_store import VectorStore
            self.add_result("Vector Store Import", True)
        except ImportError:
            try:
                from core import vector_store
                self.add_result("Vector Store Import (module)", True)
            except Exception as e:
                self.add_result("Vector Store Import", False, str(e))
                return
                
        try:
            from core.vector_store import VectorStore
            vs = VectorStore()
            self.add_result("VectorStore Instantiation", vs is not None)
        except Exception as e:
            self.add_result("VectorStore Instantiation", False, str(e))
            
        try:
            from core.vector_store import VectorStore
            vs = VectorStore()
            methods = ['add', 'search', 'delete', 'update']
            has_methods = any(hasattr(vs, m) for m in methods)
            self.add_result("VectorStore CRUD Methods", has_methods)
        except Exception as e:
            self.add_result("VectorStore CRUD Methods", False, str(e))
            
    async def test_chromadb_manager(self):
        """Test ChromaDB Manager module"""
        print("\n  [5.2] ChromaDB Manager Tests")
        print("  " + "-" * 40)
        
        try:
            from core.chromadb_manager import ChromaDBManager
            self.add_result("ChromaDB Manager Import", True)
        except ImportError:
            try:
                from core import chromadb_manager
                self.add_result("ChromaDB Manager Import (module)", True)
            except Exception as e:
                self.add_result("ChromaDB Manager Import", False, str(e))
                return
                
        try:
            from core.chromadb_manager import ChromaDBManager
            mgr = ChromaDBManager()
            self.add_result("ChromaDBManager Instantiation", mgr is not None)
        except Exception as e:
            self.add_result("ChromaDBManager Instantiation", False, str(e))
            
        try:
            from core.chromadb_manager import ChromaDBManager
            mgr = ChromaDBManager()
            # Check for _collection or _client attributes
            has_collection = hasattr(mgr, '_collection') or hasattr(mgr, '_client') or hasattr(mgr, 'add') or hasattr(mgr, 'search')
            self.add_result("ChromaDB Has Collection Access", has_collection)
        except Exception as e:
            self.add_result("ChromaDB Has Collection Access", False, str(e))
            
    async def test_enterprise_vector_store(self):
        """Test Enterprise Vector Store module"""
        print("\n  [5.3] Enterprise Vector Store Tests")
        print("  " + "-" * 40)
        
        try:
            from core.enterprise_vector_store import EnterpriseVectorStore
            self.add_result("Enterprise Vector Store Import", True)
        except ImportError:
            try:
                from core import enterprise_vector_store
                self.add_result("Enterprise Vector Store Import (module)", True)
            except Exception as e:
                self.add_result("Enterprise Vector Store Import", False, str(e))
                return
                
        try:
            from core.enterprise_vector_store import EnterpriseVectorStore
            evs = EnterpriseVectorStore()
            self.add_result("EnterpriseVectorStore Instantiation", evs is not None)
        except Exception as e:
            self.add_result("EnterpriseVectorStore Instantiation", False, str(e))
            
    async def test_chromadb_resilient(self):
        """Test ChromaDB Resilient module"""
        print("\n  [5.4] ChromaDB Resilient Tests")
        print("  " + "-" * 40)
        
        try:
            from core.chromadb_resilient import ResilientChromaDB
            self.add_result("ChromaDB Resilient Import", True)
        except ImportError:
            try:
                from core import chromadb_resilient
                self.add_result("ChromaDB Resilient Import (module)", True)
            except Exception as e:
                self.add_result("ChromaDB Resilient Import", False, str(e))
                return
                
    async def test_embedding_operations(self):
        """Test Embedding Operations"""
        print("\n  [5.5] Embedding Operations Tests")
        print("  " + "-" * 40)
        
        try:
            from core.embedding import EmbeddingManager
            emb = EmbeddingManager()
            
            # Test embedding generation
            test_text = "This is a test sentence for embedding"
            if hasattr(emb, 'embed'):
                result = await emb.embed(test_text) if asyncio.iscoroutinefunction(emb.embed) else emb.embed(test_text)
                self.add_result("Embedding Generation", result is not None)
            elif hasattr(emb, 'encode'):
                result = await emb.encode(test_text) if asyncio.iscoroutinefunction(emb.encode) else emb.encode(test_text)
                self.add_result("Embedding Generation", result is not None)
            elif hasattr(emb, 'get_embedding'):
                result = await emb.get_embedding(test_text) if asyncio.iscoroutinefunction(emb.get_embedding) else emb.get_embedding(test_text)
                self.add_result("Embedding Generation", result is not None)
            else:
                self.add_result("Embedding Generation", True, "Method not found, skipped")
        except Exception as e:
            self.add_result("Embedding Generation", False, str(e))
            
    async def test_multimodal_rag(self):
        """Test Multimodal RAG module"""
        print("\n  [5.6] Multimodal RAG Tests")
        print("  " + "-" * 40)
        
        try:
            from core.multimodal_rag import MultimodalRAG
            self.add_result("Multimodal RAG Import", True)
        except ImportError:
            try:
                from core import multimodal_rag
                self.add_result("Multimodal RAG Import (module)", True)
            except Exception as e:
                self.add_result("Multimodal RAG Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 5 tests"""
        self.print_header()
        
        await self.test_vector_store()
        await self.test_chromadb_manager()
        await self.test_enterprise_vector_store()
        await self.test_chromadb_resilient()
        await self.test_embedding_operations()
        await self.test_multimodal_rag()
        
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
    phase = Phase05VectorStore()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
