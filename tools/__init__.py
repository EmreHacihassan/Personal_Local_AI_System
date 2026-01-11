"""
Tools Package
=============

Agent araçları modülü.

Bileşenler:
- BaseTool: Tüm araçlar için temel sınıf
- ToolManager: Araç yönetimi
- Calculator: Matematiksel hesaplamalar
- WebSearch: Web araması
- CodeExecutor: Python kod çalıştırıcı
- FileOperations: Dosya işlemleri
- MCP Integration: Model Context Protocol
"""

# Base
from .base_tool import BaseTool, FunctionTool, ToolResult

# Legacy Tools
from .rag_tool import RAGTool
from .file_tool import FileTool
from .web_tool import WebSearchTool

# New Enterprise Tools
from .calculator_tool import CalculatorTool, calculator_tool
from .code_executor_tool import (
    CodeExecutorTool,
    code_executor_tool,
    SafetyAnalyzer,
    SandboxNamespace,
    ExecutionResult,
)
from .file_operations_tool import FileOperationsTool, file_operations_tool
from .web_search_tool import WebSearchTool as EnterpriseWebSearchTool, web_search_tool

# Tool Manager
from .tool_manager import (
    ToolManager,
    ToolRegistry,
    ToolCategory,
    ToolMetadata,
    ToolExecution,
    tool_manager,
    tool_registry,
    register_default_tools,
)

# MCP Integration
from .mcp_integration import MCPHub, mcp_hub, LocalMCPServer, RemoteMCPServer, MCPToolCall

__all__ = [
    # Base
    "BaseTool",
    "FunctionTool",
    "ToolResult",
    
    # Legacy Tools
    "RAGTool",
    "FileTool",
    "WebSearchTool",
    
    # Calculator
    "CalculatorTool",
    "calculator_tool",
    
    # Code Executor
    "CodeExecutorTool",
    "code_executor_tool",
    "SafetyAnalyzer",
    "SandboxNamespace",
    "ExecutionResult",
    
    # File Operations
    "FileOperationsTool",
    "file_operations_tool",
    
    # Enterprise Web Search
    "EnterpriseWebSearchTool",
    "web_search_tool",
    
    # Manager
    "ToolManager",
    "ToolRegistry",
    "ToolCategory",
    "ToolMetadata",
    "ToolExecution",
    "tool_manager",
    "tool_registry",
    "register_default_tools",
    
    # MCP
    "MCPHub",
    "mcp_hub",
    "LocalMCPServer",
    "RemoteMCPServer",
    "MCPToolCall",
]
