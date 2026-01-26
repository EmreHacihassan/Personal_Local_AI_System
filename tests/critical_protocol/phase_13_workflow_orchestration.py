"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 13: WORKFLOW & ORCHESTRATION         ║
║                                                                                 ║
║  Tests: workflow_engine, langgraph, core_orchestrator, task workflows         ║
║  Scope: All workflow and orchestration systems                                 ║
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


class Phase13Workflow:
    """Phase 13: Workflow & Orchestration Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 13: WORKFLOW & ORCHESTRATION"
        
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
            
    async def test_workflow_engine(self):
        """Test Workflow Engine"""
        print("\n  [13.1] Workflow Engine Tests")
        print("  " + "-" * 40)
        
        try:
            from core.workflow_engine import WorkflowEngine
            self.add_result("Workflow Engine Import", True)
        except ImportError:
            try:
                from core import workflow_engine
                self.add_result("Workflow Engine Import (module)", True)
            except Exception as e:
                self.add_result("Workflow Engine Import", False, str(e))
                return
                
        try:
            from core.workflow_engine import WorkflowEngine
            we = WorkflowEngine()
            self.add_result("WorkflowEngine Instantiation", we is not None)
        except Exception as e:
            self.add_result("WorkflowEngine Instantiation", False, str(e))
            
        try:
            from core.workflow_engine import WorkflowEngine
            we = WorkflowEngine()
            methods = ['execute', 'add_step', 'run', 'create_workflow', 'get_status']
            has_methods = any(hasattr(we, m) for m in methods)
            self.add_result("Workflow Engine Methods", has_methods)
        except Exception as e:
            self.add_result("Workflow Engine Methods", False, str(e))
            
    async def test_langgraph_orchestration(self):
        """Test LangGraph Orchestration"""
        print("\n  [13.2] LangGraph Orchestration Tests")
        print("  " + "-" * 40)
        
        try:
            from core.langgraph_orchestration import StateGraph, AgentState
            self.add_result("LangGraph Orchestration Import", True)
        except ImportError:
            try:
                from core import langgraph_orchestration
                self.add_result("LangGraph Orchestration Import (module)", True)
            except Exception as e:
                self.add_result("LangGraph Orchestration Import", False, str(e))
                return
                
        try:
            from core.langgraph_orchestration import StateGraph, AgentState
            lgo = StateGraph(AgentState)
            self.add_result("StateGraph Instantiation", lgo is not None)
        except Exception as e:
            self.add_result("StateGraph Instantiation", False, str(e))
            
    async def test_orchestrator(self):
        """Test Core Orchestrator"""
        print("\n  [13.3] Orchestrator Tests")
        print("  " + "-" * 40)
        
        try:
            from core.orchestrator import EnterpriseAIOrchestrator
            self.add_result("Core Orchestrator Import", True)
        except ImportError:
            try:
                from core import orchestrator
                self.add_result("Core Orchestrator Import (module)", True)
            except Exception as e:
                self.add_result("Core Orchestrator Import", False, str(e))
                return
                
        try:
            from core.orchestrator import EnterpriseAIOrchestrator
            co = EnterpriseAIOrchestrator()
            self.add_result("EnterpriseAIOrchestrator Instantiation", co is not None)
        except Exception as e:
            self.add_result("EnterpriseAIOrchestrator Instantiation", False, str(e))
            
    async def test_agents_orchestrator(self):
        """Test Agents Orchestrator"""
        print("\n  [13.4] Agents Orchestrator Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.orchestrator import Orchestrator
            self.add_result("Agent Orchestrator Import", True)
        except ImportError:
            try:
                from agents import orchestrator
                self.add_result("Agent Orchestrator Import (module)", True)
            except Exception as e:
                self.add_result("Agent Orchestrator Import", False, str(e))
                return
                
        try:
            from agents.orchestrator import Orchestrator
            ao = Orchestrator()
            self.add_result("Orchestrator Instantiation", ao is not None)
        except Exception as e:
            self.add_result("Orchestrator Instantiation", False, str(e))
            
    async def test_task_queue(self):
        """Test Task Queue"""
        print("\n  [13.5] Task Queue Tests")
        print("  " + "-" * 40)
        
        try:
            from core.task_queue import TaskQueue
            self.add_result("Task Queue Import", True)
        except ImportError:
            try:
                from core import task_queue
                self.add_result("Task Queue Import (module)", True)
            except Exception as e:
                self.add_result("Task Queue Import", False, str(e))
                return
                
        try:
            from core.task_queue import TaskQueue
            tq = TaskQueue()
            self.add_result("TaskQueue Instantiation", tq is not None)
        except Exception as e:
            self.add_result("TaskQueue Instantiation", False, str(e))
            
    async def test_workflow_orchestrator(self):
        """Test Workflow Orchestrator"""
        print("\n  [13.6] Workflow Orchestrator Tests")
        print("  " + "-" * 40)
        
        try:
            from core.workflow_orchestrator import WorkflowOrchestrator
            self.add_result("Workflow Orchestrator Import", True)
        except ImportError:
            try:
                from core import workflow_orchestrator
                self.add_result("Workflow Orchestrator Import (module)", True)
            except Exception as e:
                self.add_result("Workflow Orchestrator Import", False, str(e))
                return
                
        try:
            from core.workflow_orchestrator import WorkflowOrchestrator
            wo = WorkflowOrchestrator()
            self.add_result("WorkflowOrchestrator Instantiation", wo is not None)
        except Exception as e:
            self.add_result("WorkflowOrchestrator Instantiation", False, str(e))
            
    async def test_workflow_api(self):
        """Test Workflow API Endpoints"""
        print("\n  [13.7] Workflow API Tests")
        print("  " + "-" * 40)
        
        try:
            from api.workflow_endpoints import router as workflow_router
            self.add_result("Workflow Endpoints Import", True)
        except ImportError:
            try:
                from api import workflow_endpoints
                self.add_result("Workflow Endpoints Import (module)", True)
            except Exception as e:
                self.add_result("Workflow Endpoints Import", False, str(e))
                return
                
    async def test_advanced_workflow_engine(self):
        """Test Advanced Workflow Engine"""
        print("\n  [13.8] Advanced Workflow Engine Tests")
        print("  " + "-" * 40)
        
        try:
            from core.advanced_workflow_engine import AdvancedWorkflowEngine
            self.add_result("Advanced Workflow Engine Import", True)
        except ImportError:
            try:
                from core import advanced_workflow_engine
                self.add_result("Advanced Workflow Engine Import (module)", True)
            except Exception as e:
                self.add_result("Advanced Workflow Engine Import", False, str(e))
                return
                
        try:
            from core.advanced_workflow_engine import AdvancedWorkflowEngine
            awe = AdvancedWorkflowEngine()
            self.add_result("AdvancedWorkflowEngine Instantiation", awe is not None)
        except Exception as e:
            self.add_result("AdvancedWorkflowEngine Instantiation", False, str(e))
            
    async def run_all_tests(self):
        """Run all Phase 13 tests"""
        self.print_header()
        
        await self.test_workflow_engine()
        await self.test_langgraph_orchestration()
        await self.test_orchestrator()
        await self.test_agents_orchestrator()
        await self.test_task_queue()
        await self.test_workflow_orchestrator()
        await self.test_workflow_api()
        await self.test_advanced_workflow_engine()
        
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
    phase = Phase13Workflow()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
