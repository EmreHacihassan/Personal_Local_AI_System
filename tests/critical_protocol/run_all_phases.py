"""
╔═══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                ║
║   ██████╗██████╗ ██╗████████╗██╗ ██████╗ █████╗ ██╗         ████████╗███████╗███████╗████████╗ ║
║  ██╔════╝██╔══██╗██║╚══██╔══╝██║██╔════╝██╔══██╗██║         ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝ ║
║  ██║     ██████╔╝██║   ██║   ██║██║     ███████║██║            ██║   █████╗  ███████╗   ██║    ║
║  ██║     ██╔══██╗██║   ██║   ██║██║     ██╔══██║██║            ██║   ██╔══╝  ╚════██║   ██║    ║
║  ╚██████╗██║  ██║██║   ██║   ██║╚██████╗██║  ██║███████╗       ██║   ███████╗███████║   ██║    ║
║   ╚═════╝╚═╝  ╚═╝╚═╝   ╚═╝   ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝       ╚═╝   ╚══════╝╚══════╝   ╚═╝    ║
║                                                                                                ║
║                    ██████╗ ██████╗  ██████╗ ████████╗ ██████╗  ██████╗ ██████╗ ██╗             ║
║                    ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██║             ║
║                    ██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║             ║
║                    ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║             ║
║                    ██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╗╚██████╔╝███████╗        ║
║                    ╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝        ║
║                                                                                                ║
║                                    15 PHASE MASTER RUNNER                                      ║
║                                                                                                ║
║  Comprehensive testing of the entire AgenticManagingSystem project                             ║
║  Covers: Core, LLM, Memory, RAG, Vectors, Graphs, Agents, Premium, API, WebSocket,            ║
║          Tools & Plugins, Security, Workflow, Learning, Frontend Integration                   ║
║                                                                                                ║
╚═══════════════════════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import json
from pathlib import Path

# Add project root and test dir to path
project_root = Path(__file__).parent.parent.parent
test_dir = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(test_dir))

# Import all phases
from phase_01_core_foundation import Phase01CoreFoundation
from phase_02_llm_core import Phase02LLMCore
from phase_03_memory_cache import Phase03MemoryCache
from phase_04_rag_system import Phase04RAGSystem
from phase_05_vector_store import Phase05VectorStore
from phase_06_knowledge_graph import Phase06KnowledgeGraph
from phase_07_agent_system import Phase07AgentSystem
from phase_08_premium_features import Phase08PremiumFeatures
from phase_09_api_endpoints import Phase09APIEndpoints
from phase_10_websocket import Phase10WebSocket
from phase_11_tools_plugins import Phase11ToolsPlugins
from phase_12_security_guardrails import Phase12Security
from phase_13_workflow_orchestration import Phase13Workflow
from phase_14_learning_system import Phase14Learning
from phase_15_frontend_integration import Phase15Frontend


class CriticalTestProtocol:
    """Master runner for all 15 phases of the Critical Test Protocol"""
    
    def __init__(self):
        self.phases = [
            ("Phase 01", "Core Foundation", Phase01CoreFoundation),
            ("Phase 02", "LLM & AI Core", Phase02LLMCore),
            ("Phase 03", "Memory & Cache", Phase03MemoryCache),
            ("Phase 04", "RAG System", Phase04RAGSystem),
            ("Phase 05", "Vector Store & Embeddings", Phase05VectorStore),
            ("Phase 06", "Knowledge Graph", Phase06KnowledgeGraph),
            ("Phase 07", "Agent System", Phase07AgentSystem),
            ("Phase 08", "Premium Features", Phase08PremiumFeatures),
            ("Phase 09", "API Endpoints", Phase09APIEndpoints),
            ("Phase 10", "WebSocket", Phase10WebSocket),
            ("Phase 11", "Tools & Plugins", Phase11ToolsPlugins),
            ("Phase 12", "Security & Guardrails", Phase12Security),
            ("Phase 13", "Workflow & Orchestration", Phase13Workflow),
            ("Phase 14", "Learning System", Phase14Learning),
            ("Phase 15", "Frontend Integration", Phase15Frontend),
        ]
        self.results: List[Dict[str, Any]] = []
        
    def print_banner(self):
        print("\n")
        print("╔" + "═" * 88 + "╗")
        print("║" + " " * 88 + "║")
        print("║" + "     ▄████▄  ██▀███   ██▓▄▄▄█████▓ ██▓ ▄████▄   ▄▄▄       ██▓           ".center(88) + "║")
        print("║" + "    ▒██▀ ▀█ ▓██ ▒ ██▒▓██▒▓  ██▒ ▓▒▓██▒▒██▀ ▀█  ▒████▄    ▓██▒           ".center(88) + "║")
        print("║" + "    ▒▓█    ▄▓██ ░▄█ ▒▒██▒▒ ▓██░ ▒░▒██▒▒▓█    ▄ ▒██  ▀█▄  ▒██░           ".center(88) + "║")
        print("║" + "    ▒▓▓▄ ▄██▒██▀▀█▄  ░██░░ ▓██▓ ░ ░██░▒▓▓▄ ▄██▒░██▄▄▄▄██ ▒██░           ".center(88) + "║")
        print("║" + "    ▒ ▓███▀ ░██▓ ▒██▒░██░  ▒██▒ ░ ░██░▒ ▓███▀ ░ ▓█   ▓██▒░██████▒       ".center(88) + "║")
        print("║" + "    ░ ░▒ ▒  ░ ▒▓ ░▒▓░░▓    ▒ ░░   ░▓  ░ ░▒ ▒  ░ ▒▒   ▓▒█░░ ▒░▓  ░       ".center(88) + "║")
        print("║" + " " * 88 + "║")
        print("║" + "                    ████████╗███████╗███████╗████████╗                  ".center(88) + "║")
        print("║" + "                    ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝                  ".center(88) + "║")
        print("║" + "                       ██║   █████╗  ███████╗   ██║                     ".center(88) + "║")
        print("║" + "                       ██║   ██╔══╝  ╚════██║   ██║                     ".center(88) + "║")
        print("║" + "                       ██║   ███████╗███████║   ██║                     ".center(88) + "║")
        print("║" + "                       ╚═╝   ╚══════╝╚══════╝   ╚═╝                     ".center(88) + "║")
        print("║" + " " * 88 + "║")
        print("║" + "             ██████╗ ██████╗  ██████╗ ████████╗ ██████╗  ██████╗ ██████╗ ██╗".center(88) + "║")
        print("║" + "             ██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔═══██╗██╔════╝██╔═══██╗██║".center(88) + "║")
        print("║" + "             ██████╔╝██████╔╝██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║".center(88) + "║")
        print("║" + "             ██╔═══╝ ██╔══██╗██║   ██║   ██║   ██║   ██║██║     ██║   ██║██║".center(88) + "║")
        print("║" + "             ██║     ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╗╚██████╔╝███████╗".center(88) + "║")
        print("║" + "             ╚═╝     ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚═════╝ ╚══════╝".center(88) + "║")
        print("║" + " " * 88 + "║")
        print("║" + "                          15 PHASE COMPREHENSIVE TEST                   ".center(88) + "║")
        print("║" + " " * 88 + "║")
        print("╚" + "═" * 88 + "╝")
        print()
        
    def print_phase_list(self):
        print("\n" + "═" * 70)
        print("  PHASES TO EXECUTE:")
        print("═" * 70)
        for i, (phase_id, phase_name, _) in enumerate(self.phases, 1):
            print(f"  {i:2}. {phase_id}: {phase_name}")
        print("═" * 70 + "\n")
        
    async def run_all_phases(self):
        """Run all 15 phases sequentially"""
        self.print_banner()
        self.print_phase_list()
        
        start_time = datetime.now()
        print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70)
        
        for phase_id, phase_name, PhaseClass in self.phases:
            print(f"\n{'▶' * 5} RUNNING {phase_id}: {phase_name} {'◀' * 5}")
            try:
                phase = PhaseClass()
                result = await phase.run_all_tests()
                self.results.append(result)
            except Exception as e:
                print(f"  ✗ CRITICAL ERROR in {phase_id}: {str(e)}")
                self.results.append({
                    "phase": f"{phase_id}: {phase_name}",
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "error": str(e)
                })
                
        end_time = datetime.now()
        duration = end_time - start_time
        
        return self.generate_final_report(start_time, end_time, duration)
        
    def generate_final_report(self, start_time, end_time, duration):
        """Generate comprehensive final report"""
        
        print("\n")
        print("╔" + "═" * 88 + "╗")
        print("║" + "                        FINAL REPORT - CRITICAL TEST PROTOCOL          ".center(88) + "║")
        print("╚" + "═" * 88 + "╝")
        
        # Calculate totals
        total_tests = sum(r.get('total', 0) for r in self.results)
        total_passed = sum(r.get('passed', 0) for r in self.results)
        total_failed = sum(r.get('failed', 0) for r in self.results)
        
        overall_rate = (100 * total_passed / total_tests) if total_tests > 0 else 0
        
        # Time information
        print(f"\n  ⏱  Test Duration: {duration}")
        print(f"  📅 Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  📅 Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Phase by phase summary
        print("\n" + "═" * 70)
        print("  PHASE SUMMARY")
        print("═" * 70)
        print(f"  {'Phase':<35} {'Tests':<8} {'Pass':<8} {'Fail':<8} {'Rate':<10}")
        print("  " + "-" * 68)
        
        for result in self.results:
            phase = result.get('phase', 'Unknown')[:30]
            tests = result.get('total', 0)
            passed = result.get('passed', 0)
            failed = result.get('failed', 0)
            rate = result.get('success_rate', 0)
            
            status = "✓" if failed == 0 else "✗"
            print(f"  {status} {phase:<33} {tests:<8} {passed:<8} {failed:<8} {rate:.1f}%")
            
        # Overall summary
        print("\n" + "═" * 70)
        print("  OVERALL RESULTS")
        print("═" * 70)
        print(f"  Total Phases: {len(self.results)}")
        print(f"  Total Tests:  {total_tests}")
        print(f"  Total Passed: {total_passed}")
        print(f"  Total Failed: {total_failed}")
        print(f"  Success Rate: {overall_rate:.1f}%")
        
        # Visual bar
        bar_length = 50
        filled = int(bar_length * overall_rate / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"\n  Progress: [{bar}] {overall_rate:.1f}%")
        
        # Verdict
        print("\n" + "═" * 70)
        if overall_rate >= 90:
            print("  ✓ VERDICT: EXCELLENT - System is in great condition")
            verdict = "EXCELLENT"
        elif overall_rate >= 70:
            print("  ◐ VERDICT: GOOD - Minor issues need attention")
            verdict = "GOOD"
        elif overall_rate >= 50:
            print("  ◐ VERDICT: MODERATE - Several issues need fixing")
            verdict = "MODERATE"
        else:
            print("  ✗ VERDICT: CRITICAL - Major issues detected")
            verdict = "CRITICAL"
        print("═" * 70)
        
        # Failed tests detail
        if total_failed > 0:
            print("\n  FAILED TESTS REQUIRING ATTENTION:")
            print("  " + "-" * 60)
            for result in self.results:
                if result.get('failed', 0) > 0:
                    print(f"  • {result.get('phase')}")
                    
        # Save report
        report_path = project_root / "tests" / "critical_protocol" / "test_report.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration.total_seconds(),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": overall_rate,
            "verdict": verdict,
            "phases": self.results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        print(f"\n  📄 Report saved to: {report_path}")
        print("═" * 70 + "\n")
        
        return report_data


async def main():
    protocol = CriticalTestProtocol()
    return await protocol.run_all_phases()


if __name__ == "__main__":
    asyncio.run(main())
