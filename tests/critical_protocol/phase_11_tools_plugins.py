"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 11: TOOLS & PLUGINS                  ║
║                                                                                 ║
║  Tests: tools/, plugins/, custom tools, plugin system                          ║
║  Scope: All tools and plugins in the system                                    ║
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


class Phase11ToolsPlugins:
    """Phase 11: Tools & Plugins Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 11: TOOLS & PLUGINS"
        
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
            
    async def test_tool_manager(self):
        """Test Tool Manager"""
        print("\n  [11.1] Tool Manager Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.tool_manager import ToolManager
            self.add_result("Tool Manager Import", True)
        except ImportError:
            try:
                from tools import tool_manager
                self.add_result("Tool Manager Import (module)", True)
            except Exception as e:
                self.add_result("Tool Manager Import", False, str(e))
                return
                
        try:
            from tools.tool_manager import ToolManager
            tm = ToolManager()
            self.add_result("ToolManager Instantiation", tm is not None)
        except Exception as e:
            self.add_result("ToolManager Instantiation", False, str(e))
            
    async def test_web_search_tool(self):
        """Test Web Search Tool"""
        print("\n  [11.2] Web Search Tool Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.web_search_tool import WebSearchTool
            self.add_result("Web Search Tool Import", True)
        except ImportError:
            try:
                from tools import web_search_tool
                self.add_result("Web Search Tool Import (module)", True)
            except Exception as e:
                self.add_result("Web Search Tool Import", False, str(e))
                return
                
        try:
            from tools.web_search_tool import WebSearchTool
            tool = WebSearchTool()
            self.add_result("WebSearchTool Instantiation", tool is not None)
        except Exception as e:
            self.add_result("WebSearchTool Instantiation", False, str(e))
            
    async def test_code_executor_tool(self):
        """Test Code Executor Tool"""
        print("\n  [11.3] Code Executor Tool Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.code_executor_tool import CodeExecutorTool
            self.add_result("Code Executor Tool Import", True)
        except ImportError:
            try:
                from tools import code_executor_tool
                self.add_result("Code Executor Tool Import (module)", True)
            except Exception as e:
                self.add_result("Code Executor Tool Import", False, str(e))
                return
                
        try:
            from tools.code_executor_tool import CodeExecutorTool
            tool = CodeExecutorTool()
            self.add_result("CodeExecutorTool Instantiation", tool is not None)
        except Exception as e:
            self.add_result("CodeExecutorTool Instantiation", False, str(e))
            
    async def test_file_tool(self):
        """Test File Tool"""
        print("\n  [11.4] File Tool Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.file_tool import FileTool
            self.add_result("File Tool Import", True)
        except ImportError:
            try:
                from tools import file_tool
                self.add_result("File Tool Import (module)", True)
            except Exception as e:
                self.add_result("File Tool Import", False, str(e))
                return
                
        try:
            from tools.file_tool import FileTool
            tool = FileTool()
            self.add_result("FileTool Instantiation", tool is not None)
        except Exception as e:
            self.add_result("FileTool Instantiation", False, str(e))
            
    async def test_calculator_tool(self):
        """Test Calculator Tool"""
        print("\n  [11.5] Calculator Tool Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.calculator_tool import CalculatorTool
            self.add_result("Calculator Tool Import", True)
        except ImportError:
            try:
                from tools import calculator_tool
                self.add_result("Calculator Tool Import (module)", True)
            except Exception as e:
                self.add_result("Calculator Tool Import", False, str(e))
                return
                
        try:
            from tools.calculator_tool import CalculatorTool
            tool = CalculatorTool()
            self.add_result("CalculatorTool Instantiation", tool is not None)
        except Exception as e:
            self.add_result("CalculatorTool Instantiation", False, str(e))
            
    async def test_base_plugin(self):
        """Test Base Plugin"""
        print("\n  [11.6] Base Plugin Tests")
        print("  " + "-" * 40)
        
        try:
            from plugins.base import BasePlugin
            self.add_result("Base Plugin Import", True)
        except ImportError:
            try:
                from plugins import base
                self.add_result("Base Plugin Import (module)", True)
            except Exception as e:
                self.add_result("Base Plugin Import", False, str(e))
                return
                
    async def test_web_search_plugin(self):
        """Test Web Search Plugin"""
        print("\n  [11.7] Web Search Plugin Tests")
        print("  " + "-" * 40)
        
        try:
            from plugins.web_search_plugin import WebSearchPlugin
            self.add_result("Web Search Plugin Import", True)
        except ImportError:
            try:
                from plugins import web_search_plugin
                self.add_result("Web Search Plugin Import (module)", True)
            except Exception as e:
                self.add_result("Web Search Plugin Import", False, str(e))
                return
            
    async def test_mcp_integration(self):
        """Test MCP Integration"""
        print("\n  [11.8] MCP Integration Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.mcp_integration import MCPIntegration
            self.add_result("MCP Integration Import", True)
        except ImportError:
            try:
                from tools import mcp_integration
                self.add_result("MCP Integration Import (module)", True)
            except Exception as e:
                self.add_result("MCP Integration Import", False, str(e))
                return
                
    async def test_base_tool(self):
        """Test Base Tool"""
        print("\n  [11.9] Base Tool Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.base_tool import BaseTool
            self.add_result("Base Tool Import", True)
        except ImportError:
            try:
                from tools import base_tool
                self.add_result("Base Tool Import (module)", True)
            except Exception as e:
                self.add_result("Base Tool Import", False, str(e))
                return
                
    async def test_rag_tool(self):
        """Test RAG Tool"""
        print("\n  [11.10] RAG Tool Tests")
        print("  " + "-" * 40)
        
        try:
            from tools.rag_tool import RAGTool
            self.add_result("RAG Tool Import", True)
        except ImportError:
            try:
                from tools import rag_tool
                self.add_result("RAG Tool Import (module)", True)
            except Exception as e:
                self.add_result("RAG Tool Import", False, str(e))
                return
                
    async def run_all_tests(self):
        """Run all Phase 11 tests"""
        self.print_header()
        
        await self.test_tool_manager()
        await self.test_web_search_tool()
        await self.test_code_executor_tool()
        await self.test_file_tool()
        await self.test_calculator_tool()
        await self.test_base_plugin()
        await self.test_web_search_plugin()
        await self.test_mcp_integration()
        await self.test_base_tool()
        await self.test_rag_tool()
        
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
    phase = Phase11ToolsPlugins()
    return await phase.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
