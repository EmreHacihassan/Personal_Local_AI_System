"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 9: API ENDPOINTS                     ║
║                                                                                 ║
║  Tests: All API endpoint modules in api/ directory                            ║
║  Scope: REST API endpoints and FastAPI routes                                  ║
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


class Phase09APIEndpoints:
    """Phase 9: API Endpoints Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 9: API ENDPOINTS"
        
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
            
    async def test_main_api(self):
        """Test Main API module"""
        print("\n  [9.1] Main API Tests")
        print("  " + "-" * 40)
        
        try:
            from api.main import app
            self.add_result("Main API Import", True)
        except Exception as e:
            self.add_result("Main API Import", False, str(e))
            return
            
        try:
            from api.main import app
            from fastapi import FastAPI
            self.add_result("FastAPI App Instance", isinstance(app, FastAPI))
        except Exception as e:
            self.add_result("FastAPI App Instance", False, str(e))
            
    async def test_agent_endpoints(self):
        """Test Agent Endpoints"""
        print("\n  [9.2] Agent Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import agent_endpoints
            self.add_result("Agent Endpoints Import", True)
        except Exception as e:
            self.add_result("Agent Endpoints Import", False, str(e))
            
    async def test_deep_scholar_endpoints(self):
        """Test DeepScholar Endpoints"""
        print("\n  [9.3] DeepScholar Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import deep_scholar_endpoints
            self.add_result("DeepScholar Endpoints Import", True)
        except Exception as e:
            self.add_result("DeepScholar Endpoints Import", False, str(e))
            
    async def test_learning_endpoints(self):
        """Test Learning Endpoints"""
        print("\n  [9.4] Learning Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import learning_endpoints
            self.add_result("Learning Endpoints Import", True)
        except Exception as e:
            self.add_result("Learning Endpoints Import", False, str(e))
            
        try:
            from api import learning_journey_endpoints
            self.add_result("Learning Journey Endpoints Import", True)
        except Exception as e:
            self.add_result("Learning Journey Endpoints Import", False, str(e))
            
        try:
            from api import learning_journey_v2_endpoints
            self.add_result("Learning Journey V2 Endpoints Import", True)
        except Exception as e:
            self.add_result("Learning Journey V2 Endpoints Import", False, str(e))
            
    async def test_memory_endpoints(self):
        """Test Memory Endpoints"""
        print("\n  [9.5] Memory Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import memory_endpoints
            self.add_result("Memory Endpoints Import", True)
        except Exception as e:
            self.add_result("Memory Endpoints Import", False, str(e))
            
        try:
            from api import memory_premium_endpoints
            self.add_result("Memory Premium Endpoints Import", True)
        except Exception as e:
            self.add_result("Memory Premium Endpoints Import", False, str(e))
            
    async def test_premium_endpoints(self):
        """Test Premium Endpoints"""
        print("\n  [9.6] Premium Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import premium_endpoints
            self.add_result("Premium Endpoints Import", True)
        except Exception as e:
            self.add_result("Premium Endpoints Import", False, str(e))
            
        try:
            from api import full_meta_premium_endpoints
            self.add_result("Full Meta Premium Endpoints Import", True)
        except Exception as e:
            self.add_result("Full Meta Premium Endpoints Import", False, str(e))
            
    async def test_knowledge_graph_endpoints(self):
        """Test Knowledge Graph Endpoints"""
        print("\n  [9.7] Knowledge Graph Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import knowledge_graph_endpoints
            self.add_result("KG Endpoints Import", True)
        except Exception as e:
            self.add_result("KG Endpoints Import", False, str(e))
            
        try:
            from api import knowledge_graph_enterprise_endpoints
            self.add_result("Enterprise KG Endpoints Import", True)
        except Exception as e:
            self.add_result("Enterprise KG Endpoints Import", False, str(e))
            
    async def test_workflow_endpoints(self):
        """Test Workflow Endpoints"""
        print("\n  [9.8] Workflow Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import workflow_endpoints
            self.add_result("Workflow Endpoints Import", True)
        except Exception as e:
            self.add_result("Workflow Endpoints Import", False, str(e))
            
        try:
            from api import workflow_orchestrator_endpoints
            self.add_result("Workflow Orchestrator Endpoints Import", True)
        except Exception as e:
            self.add_result("Workflow Orchestrator Endpoints Import", False, str(e))
            
    async def test_security_endpoints(self):
        """Test Security Endpoints"""
        print("\n  [9.9] Security Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import security_endpoints
            self.add_result("Security Endpoints Import", True)
        except Exception as e:
            self.add_result("Security Endpoints Import", False, str(e))
            
        try:
            from api import guardrails_endpoints
            self.add_result("Guardrails Endpoints Import", True)
        except Exception as e:
            self.add_result("Guardrails Endpoints Import", False, str(e))
            
    async def test_multimodal_endpoints(self):
        """Test Multimodal Endpoints"""
        print("\n  [9.10] Multimodal Endpoints Tests")
        print("  " + "-" * 40)
        
        try:
            from api import multimodal_endpoints
            self.add_result("Multimodal Endpoints Import", True)
        except Exception as e:
            self.add_result("Multimodal Endpoints Import", False, str(e))
            
        try:
            from api import vision_endpoints
            self.add_result("Vision Endpoints Import", True)
        except Exception as e:
            self.add_result("Vision Endpoints Import", False, str(e))
            
        try:
            from api import voice_endpoints
            self.add_result("Voice Endpoints Import", True)
        except Exception as e:
            self.add_result("Voice Endpoints Import", False, str(e))
            
    async def test_other_endpoints(self):
        """Test Other Endpoints"""
        print("\n  [9.11] Other Endpoints Tests")
        print("  " + "-" * 40)
        
        endpoints = [
            "mcp_endpoints",
            "analytics_endpoints",
            "code_endpoints",
            "routing_endpoints",
            "resilience_endpoints",
            "autonomous_endpoints",
            "computer_use_endpoints",
            "screen_recording_endpoints",
            "agent_marketplace_endpoints",
            "full_meta_endpoints",
            "full_meta_quality_endpoints",
        ]
        
        for ep in endpoints:
            try:
                mod = __import__(f"api.{ep}", fromlist=[ep])
                self.add_result(f"{ep} Import", True)
            except Exception as e:
                self.add_result(f"{ep} Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 9 tests"""
        self.print_header()
        
        await self.test_main_api()
        await self.test_agent_endpoints()
        await self.test_deep_scholar_endpoints()
        await self.test_learning_endpoints()
        await self.test_memory_endpoints()
        await self.test_premium_endpoints()
        await self.test_knowledge_graph_endpoints()
        await self.test_workflow_endpoints()
        await self.test_security_endpoints()
        await self.test_multimodal_endpoints()
        await self.test_other_endpoints()
        
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
    phase = Phase09APIEndpoints()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
