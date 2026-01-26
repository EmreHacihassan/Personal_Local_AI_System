"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 7: AGENT SYSTEM                      ║
║                                                                                 ║
║  Tests: base_agent, react_agent, orchestrator, planning_agent, etc.           ║
║  Scope: Agent architecture and multi-agent systems                             ║
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


class Phase07AgentSystem:
    """Phase 7: Agent System Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 7: AGENT SYSTEM"
        
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
            
    async def test_base_agent(self):
        """Test Base Agent module"""
        print("\n  [7.1] Base Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.base_agent import BaseAgent
            self.add_result("Base Agent Import", True)
        except ImportError:
            try:
                from agents import base_agent
                self.add_result("Base Agent Import (module)", True)
            except Exception as e:
                self.add_result("Base Agent Import", False, str(e))
                return
                
    async def test_react_agent(self):
        """Test ReAct Agent module"""
        print("\n  [7.2] ReAct Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.react_agent import ReActAgent
            self.add_result("ReAct Agent Import", True)
        except ImportError:
            try:
                from agents import react_agent
                self.add_result("ReAct Agent Import (module)", True)
            except Exception as e:
                self.add_result("ReAct Agent Import", False, str(e))
                return
                
        try:
            from agents.react_agent import ReActAgent
            agent = ReActAgent()
            self.add_result("ReActAgent Instantiation", agent is not None)
        except Exception as e:
            self.add_result("ReActAgent Instantiation", False, str(e))
            
    async def test_orchestrator(self):
        """Test Orchestrator module"""
        print("\n  [7.3] Orchestrator Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.orchestrator import Orchestrator
            self.add_result("Orchestrator Import", True)
        except ImportError:
            try:
                from agents import orchestrator
                self.add_result("Orchestrator Import (module)", True)
            except Exception as e:
                self.add_result("Orchestrator Import", False, str(e))
                return
                
        try:
            from agents.orchestrator import Orchestrator
            orch = Orchestrator()
            self.add_result("Orchestrator Instantiation", orch is not None)
        except Exception as e:
            self.add_result("Orchestrator Instantiation", False, str(e))
            
    async def test_planning_agent(self):
        """Test Planning Agent module"""
        print("\n  [7.4] Planning Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.planning_agent import PlanningAgent
            self.add_result("Planning Agent Import", True)
        except ImportError:
            try:
                from agents import planning_agent
                self.add_result("Planning Agent Import (module)", True)
            except Exception as e:
                self.add_result("Planning Agent Import", False, str(e))
                return
                
        try:
            from agents.planning_agent import PlanningAgent
            agent = PlanningAgent()
            self.add_result("PlanningAgent Instantiation", agent is not None)
        except Exception as e:
            self.add_result("PlanningAgent Instantiation", False, str(e))
            
    async def test_research_agent(self):
        """Test Research Agent module"""
        print("\n  [7.5] Research Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.research_agent import ResearchAgent
            self.add_result("Research Agent Import", True)
        except ImportError:
            try:
                from agents import research_agent
                self.add_result("Research Agent Import (module)", True)
            except Exception as e:
                self.add_result("Research Agent Import", False, str(e))
                return
                
        try:
            from agents.research_agent import ResearchAgent
            agent = ResearchAgent()
            self.add_result("ResearchAgent Instantiation", agent is not None)
        except Exception as e:
            self.add_result("ResearchAgent Instantiation", False, str(e))
            
    async def test_writer_agent(self):
        """Test Writer Agent module"""
        print("\n  [7.6] Writer Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.writer_agent import WriterAgent
            self.add_result("Writer Agent Import", True)
        except ImportError:
            try:
                from agents import writer_agent
                self.add_result("Writer Agent Import (module)", True)
            except Exception as e:
                self.add_result("Writer Agent Import", False, str(e))
                return
                
        try:
            from agents.writer_agent import WriterAgent
            agent = WriterAgent()
            self.add_result("WriterAgent Instantiation", agent is not None)
        except Exception as e:
            self.add_result("WriterAgent Instantiation", False, str(e))
            
    async def test_analyzer_agent(self):
        """Test Analyzer Agent module"""
        print("\n  [7.7] Analyzer Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.analyzer_agent import AnalyzerAgent
            self.add_result("Analyzer Agent Import", True)
        except ImportError:
            try:
                from agents import analyzer_agent
                self.add_result("Analyzer Agent Import (module)", True)
            except Exception as e:
                self.add_result("Analyzer Agent Import", False, str(e))
                return
                
    async def test_assistant_agent(self):
        """Test Assistant Agent module"""
        print("\n  [7.8] Assistant Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.assistant_agent import AssistantAgent
            self.add_result("Assistant Agent Import", True)
        except ImportError:
            try:
                from agents import assistant_agent
                self.add_result("Assistant Agent Import (module)", True)
            except Exception as e:
                self.add_result("Assistant Agent Import", False, str(e))
                return
                
    async def test_enhanced_agent(self):
        """Test Enhanced Agent module"""
        print("\n  [7.9] Enhanced Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.enhanced_agent import EnhancedAgent
            self.add_result("Enhanced Agent Import", True)
        except ImportError:
            try:
                from agents import enhanced_agent
                self.add_result("Enhanced Agent Import (module)", True)
            except Exception as e:
                self.add_result("Enhanced Agent Import", False, str(e))
                return
                
    async def test_self_reflection(self):
        """Test Self Reflection module"""
        print("\n  [7.10] Self Reflection Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.self_reflection import SelfReflectionAgent
            self.add_result("Self Reflection Import", True)
        except ImportError:
            try:
                from agents import self_reflection
                self.add_result("Self Reflection Import (module)", True)
            except Exception as e:
                self.add_result("Self Reflection Import", False, str(e))
                
    async def test_autonomous_agent(self):
        """Test Autonomous Agent module"""
        print("\n  [7.11] Autonomous Agent Tests")
        print("  " + "-" * 40)
        
        try:
            from agents.autonomous_agent import AutonomousAgent
            self.add_result("Autonomous Agent Import", True)
        except ImportError:
            try:
                from core.autonomous_agent import AutonomousAgent
                self.add_result("Autonomous Agent Import (core)", True)
            except Exception as e:
                self.add_result("Autonomous Agent Import", False, str(e))
                
    async def test_core_orchestrator(self):
        """Test Core Orchestrator module"""
        print("\n  [7.12] Core Orchestrator Tests")
        print("  " + "-" * 40)
        
        try:
            from core.orchestrator import CoreOrchestrator
            self.add_result("Core Orchestrator Import", True)
        except ImportError:
            try:
                from core import orchestrator
                self.add_result("Core Orchestrator Import (module)", True)
            except Exception as e:
                self.add_result("Core Orchestrator Import", False, str(e))
                
    async def run_all_tests(self):
        """Run all Phase 7 tests"""
        self.print_header()
        
        await self.test_base_agent()
        await self.test_react_agent()
        await self.test_orchestrator()
        await self.test_planning_agent()
        await self.test_research_agent()
        await self.test_writer_agent()
        await self.test_analyzer_agent()
        await self.test_assistant_agent()
        await self.test_enhanced_agent()
        await self.test_self_reflection()
        await self.test_autonomous_agent()
        await self.test_core_orchestrator()
        
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
    phase = Phase07AgentSystem()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
