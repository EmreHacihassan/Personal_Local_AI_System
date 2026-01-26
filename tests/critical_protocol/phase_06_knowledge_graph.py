"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 6: KNOWLEDGE GRAPH                   ║
║                                                                                 ║
║  Tests: knowledge_graph, enterprise_knowledge_graph, graph_rag                 ║
║  Scope: Knowledge graph construction and graph-based retrieval                 ║
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


class Phase06KnowledgeGraph:
    """Phase 6: Knowledge Graph Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 6: KNOWLEDGE GRAPH"
        
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
            
    async def test_knowledge_graph(self):
        """Test Knowledge Graph module"""
        print("\n  [6.1] Knowledge Graph Tests")
        print("  " + "-" * 40)
        
        try:
            from core.knowledge_graph import KnowledgeGraph
            self.add_result("Knowledge Graph Import", True)
        except ImportError:
            try:
                from core import knowledge_graph
                self.add_result("Knowledge Graph Import (module)", True)
            except Exception as e:
                self.add_result("Knowledge Graph Import", False, str(e))
                return
                
        try:
            from core.knowledge_graph import KnowledgeGraph
            kg = KnowledgeGraph()
            self.add_result("KnowledgeGraph Instantiation", kg is not None)
        except Exception as e:
            self.add_result("KnowledgeGraph Instantiation", False, str(e))
            
        try:
            from core.knowledge_graph import KnowledgeGraph
            kg = KnowledgeGraph()
            methods = ['add_node', 'add_edge', 'query', 'get_neighbors']
            has_methods = any(hasattr(kg, m) for m in methods)
            self.add_result("KnowledgeGraph Graph Methods", has_methods)
        except Exception as e:
            self.add_result("KnowledgeGraph Graph Methods", False, str(e))
            
    async def test_enterprise_knowledge_graph(self):
        """Test Enterprise Knowledge Graph module"""
        print("\n  [6.2] Enterprise Knowledge Graph Tests")
        print("  " + "-" * 40)
        
        try:
            from core.enterprise_knowledge_graph import EnterpriseKnowledgeGraph
            self.add_result("Enterprise KG Import", True)
        except ImportError:
            try:
                from core import enterprise_knowledge_graph
                self.add_result("Enterprise KG Import (module)", True)
            except Exception as e:
                self.add_result("Enterprise KG Import", False, str(e))
                return
                
        try:
            from core.enterprise_knowledge_graph import EnterpriseKnowledgeGraph
            ekg = EnterpriseKnowledgeGraph()
            self.add_result("EnterpriseKG Instantiation", ekg is not None)
        except Exception as e:
            self.add_result("EnterpriseKG Instantiation", False, str(e))
            
    async def test_graph_rag(self):
        """Test Graph RAG module"""
        print("\n  [6.3] Graph RAG Tests")
        print("  " + "-" * 40)
        
        try:
            from core.graph_rag import GraphRAGPipeline
            self.add_result("Graph RAG Import", True)
        except ImportError:
            try:
                from core import graph_rag
                self.add_result("Graph RAG Import (module)", True)
            except Exception as e:
                self.add_result("Graph RAG Import", False, str(e))
                return
                
        try:
            from core.graph_rag import GraphRAGPipeline, InMemoryGraphStore
            graph_store = InMemoryGraphStore()
            gr = GraphRAGPipeline(graph_store=graph_store)
            self.add_result("GraphRAGPipeline Instantiation", gr is not None)
        except Exception as e:
            self.add_result("GraphRAGPipeline Instantiation", False, str(e))
            
    async def test_rag_knowledge_graph(self):
        """Test RAG Knowledge Graph module"""
        print("\n  [6.4] RAG Knowledge Graph Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.knowledge_graph import RAGKnowledgeGraph
            self.add_result("RAG Knowledge Graph Import", True)
        except ImportError:
            try:
                from rag import knowledge_graph
                self.add_result("RAG Knowledge Graph Import (module)", True)
            except Exception as e:
                self.add_result("RAG Knowledge Graph Import", False, str(e))
                return
                
    async def test_graph_rag_advanced(self):
        """Test Graph RAG Advanced module"""
        print("\n  [6.5] Graph RAG Advanced Tests")
        print("  " + "-" * 40)
        
        try:
            from rag.graph_rag_advanced import GraphRAGAdvanced
            self.add_result("Graph RAG Advanced Import", True)
        except ImportError:
            try:
                from rag import graph_rag_advanced
                self.add_result("Graph RAG Advanced Import (module)", True)
            except Exception as e:
                self.add_result("Graph RAG Advanced Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 6 tests"""
        self.print_header()
        
        await self.test_knowledge_graph()
        await self.test_enterprise_knowledge_graph()
        await self.test_graph_rag()
        await self.test_rag_knowledge_graph()
        await self.test_graph_rag_advanced()
        
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
    phase = Phase06KnowledgeGraph()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
