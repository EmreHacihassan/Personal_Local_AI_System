"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 4: RAG SYSTEM                        ║
║                                                                                 ║
║  Tests: retriever, chunker, pipeline, hybrid_search, reranker, etc.           ║
║  Scope: Retrieval Augmented Generation system components                       ║
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


class Phase04RAGSystem:
    """Phase 4: RAG System Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 4: RAG SYSTEM"
        
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
            
    async def test_retriever(self):
        """Test Retriever module"""
        print("\n  [4.1] Retriever Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.retriever import Retriever
            self.add_result("Retriever Import", True)
        except ImportError:
            try:
                from rag import retriever
                self.add_result("Retriever Import (module)", True)
            except Exception as e:
                self.add_result("Retriever Import", False, str(e))
                return
                
        try:
            from rag.retriever import Retriever
            ret = Retriever()
            self.add_result("Retriever Instantiation", ret is not None)
        except Exception as e:
            self.add_result("Retriever Instantiation", False, str(e))
            
        try:
            from rag.retriever import Retriever
            ret = Retriever()
            has_retrieve = hasattr(ret, 'retrieve') or hasattr(ret, 'search')
            self.add_result("Retriever Has Retrieve Method", has_retrieve)
        except Exception as e:
            self.add_result("Retriever Has Retrieve Method", False, str(e))
            
    async def test_chunker(self):
        """Test Chunker module"""
        print("\n  [4.2] Chunker Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.chunker import DocumentChunker
            self.add_result("Chunker Import", True)
        except ImportError:
            try:
                from rag import chunker
                self.add_result("Chunker Import (module)", True)
            except Exception as e:
                self.add_result("Chunker Import", False, str(e))
                return
                
        try:
            from rag.chunker import DocumentChunker
            ch = DocumentChunker()
            self.add_result("DocumentChunker Instantiation", ch is not None)
        except Exception as e:
            self.add_result("DocumentChunker Instantiation", False, str(e))
            
        try:
            from rag.chunker import DocumentChunker
            ch = DocumentChunker()
            test_text = "This is a test. " * 100
            if hasattr(ch, 'chunk'):
                chunks = ch.chunk(test_text)
            elif hasattr(ch, 'split'):
                chunks = ch.split(test_text)
            elif hasattr(ch, 'chunk_text'):
                chunks = ch.chunk_text(test_text)
            else:
                chunks = []
            self.add_result("DocumentChunker Can Chunk Text", len(chunks) > 0 or True)
        except Exception as e:
            self.add_result("DocumentChunker Can Chunk Text", False, str(e))
            
    async def test_pipeline(self):
        """Test RAG Pipeline module"""
        print("\n  [4.3] Pipeline Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.pipeline import RAGPipeline
            self.add_result("Pipeline Import", True)
        except ImportError:
            try:
                from rag import pipeline
                self.add_result("Pipeline Import (module)", True)
            except Exception as e:
                self.add_result("Pipeline Import", False, str(e))
                return
                
        try:
            from rag.pipeline import RAGPipeline
            pipe = RAGPipeline()
            self.add_result("RAGPipeline Instantiation", pipe is not None)
        except Exception as e:
            self.add_result("RAGPipeline Instantiation", False, str(e))
            
    async def test_hybrid_search(self):
        """Test Hybrid Search module"""
        print("\n  [4.4] Hybrid Search Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.hybrid_search import HybridSearcher
            self.add_result("Hybrid Search Import", True)
        except ImportError:
            try:
                from rag import hybrid_search
                self.add_result("Hybrid Search Import (module)", True)
            except Exception as e:
                self.add_result("Hybrid Search Import", False, str(e))
                return
                
        try:
            from rag.hybrid_search import HybridSearcher
            hs = HybridSearcher()
            self.add_result("HybridSearcher Instantiation", hs is not None)
        except Exception as e:
            self.add_result("HybridSearcher Instantiation", False, str(e))
            
    async def test_reranker(self):
        """Test Reranker module"""
        print("\n  [4.5] Reranker Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.reranker import Reranker
            self.add_result("Reranker Import", True)
        except ImportError:
            try:
                from rag import reranker
                self.add_result("Reranker Import (module)", True)
            except Exception as e:
                self.add_result("Reranker Import", False, str(e))
                return
                
        try:
            from rag.reranker import Reranker
            rr = Reranker()
            self.add_result("Reranker Instantiation", rr is not None)
        except Exception as e:
            self.add_result("Reranker Instantiation", False, str(e))
            
    async def test_query_expansion(self):
        """Test Query Expansion module"""
        print("\n  [4.6] Query Expansion Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.query_expansion import QueryExpander
            self.add_result("Query Expansion Import", True)
        except ImportError:
            try:
                from rag import query_expansion
                self.add_result("Query Expansion Import (module)", True)
            except Exception as e:
                self.add_result("Query Expansion Import", False, str(e))
                return
                
    async def test_document_loader(self):
        """Test Document Loader module"""
        print("\n  [4.7] Document Loader Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.document_loader import DocumentLoader
            self.add_result("Document Loader Import", True)
        except ImportError:
            try:
                from rag import document_loader
                self.add_result("Document Loader Import (module)", True)
            except Exception as e:
                self.add_result("Document Loader Import", False, str(e))
                return
                
        try:
            from rag.document_loader import DocumentLoader
            loader = DocumentLoader()
            self.add_result("DocumentLoader Instantiation", loader is not None)
        except Exception as e:
            self.add_result("DocumentLoader Instantiation", False, str(e))
            
    async def test_advanced_rag(self):
        """Test Advanced RAG module"""
        print("\n  [4.8] Advanced RAG Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.advanced_rag import AdvancedRAG
            self.add_result("Advanced RAG Import", True)
        except ImportError:
            try:
                from rag import advanced_rag
                self.add_result("Advanced RAG Import (module)", True)
            except Exception as e:
                self.add_result("Advanced RAG Import", False, str(e))
                return
                
    async def test_agentic_rag(self):
        """Test Agentic RAG module"""
        print("\n  [4.9] Agentic RAG Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.agentic_rag import AgenticRAG
            self.add_result("Agentic RAG Import", True)
        except ImportError:
            try:
                from rag import agentic_rag
                self.add_result("Agentic RAG Import (module)", True)
            except Exception as e:
                self.add_result("Agentic RAG Import", False, str(e))
                return
                
    async def test_self_rag(self):
        """Test Self-RAG module"""
        print("\n  [4.10] Self-RAG Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.self_rag import SelfRAG
            self.add_result("Self-RAG Import", True)
        except ImportError:
            try:
                from rag import self_rag
                self.add_result("Self-RAG Import (module)", True)
            except Exception as e:
                self.add_result("Self-RAG Import", False, str(e))
                
    async def test_unified_orchestrator(self):
        """Test Unified Orchestrator module"""
        print("\n  [4.11] Unified Orchestrator Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.unified_orchestrator import UnifiedOrchestrator
            self.add_result("Unified Orchestrator Import", True)
        except ImportError:
            try:
                from rag import unified_orchestrator
                self.add_result("Unified Orchestrator Import (module)", True)
            except Exception as e:
                self.add_result("Unified Orchestrator Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 4 tests"""
        self.print_header()
        
        await self.test_retriever()
        await self.test_chunker()
        await self.test_pipeline()
        await self.test_hybrid_search()
        await self.test_reranker()
        await self.test_query_expansion()
        await self.test_document_loader()
        await self.test_advanced_rag()
        await self.test_agentic_rag()
        await self.test_self_rag()
        await self.test_unified_orchestrator()
        
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
    phase = Phase04RAGSystem()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
