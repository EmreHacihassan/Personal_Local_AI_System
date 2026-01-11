"""
Enterprise AI Assistant - MCP Integration Module
Model Context Protocol entegrasyonu

Harici araçlar ve servislerle iletişim.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import httpx


@dataclass
class MCPToolDefinition:
    """MCP araç tanımı."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    required_params: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "required": self.required_params,
        }


@dataclass
class MCPToolCall:
    """MCP araç çağrısı."""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.call_id,
            "name": self.tool_name,
            "arguments": self.arguments,
        }


@dataclass
class MCPToolResult:
    """MCP araç sonucu."""
    call_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.call_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


class MCPServer(ABC):
    """MCP Server abstract base class."""
    
    @abstractmethod
    def get_tools(self) -> List[MCPToolDefinition]:
        """Sunucunun araçlarını döndür."""
        pass
    
    @abstractmethod
    async def execute_tool(self, call: MCPToolCall) -> MCPToolResult:
        """Aracı çalıştır."""
        pass


class LocalMCPServer(MCPServer):
    """Local MCP Server - Python fonksiyonları için."""
    
    def __init__(self, name: str):
        """Local server başlat."""
        self.name = name
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        required_params: List[str] = None,
    ):
        """Araç kaydet."""
        self._tools[name] = MCPToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            required_params=required_params or [],
        )
        self._handlers[name] = handler
    
    def get_tools(self) -> List[MCPToolDefinition]:
        """Tüm araçları döndür."""
        return list(self._tools.values())
    
    async def execute_tool(self, call: MCPToolCall) -> MCPToolResult:
        """Aracı çalıştır."""
        import time
        import uuid
        
        start_time = time.time()
        call_id = call.call_id or str(uuid.uuid4())[:8]
        
        if call.tool_name not in self._handlers:
            return MCPToolResult(
                call_id=call_id,
                success=False,
                error=f"Tool not found: {call.tool_name}",
            )
        
        try:
            handler = self._handlers[call.tool_name]
            
            if asyncio.iscoroutinefunction(handler):
                result = await handler(**call.arguments)
            else:
                result = handler(**call.arguments)
            
            execution_time = (time.time() - start_time) * 1000
            
            return MCPToolResult(
                call_id=call_id,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return MCPToolResult(
                call_id=call_id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )


class RemoteMCPServer(MCPServer):
    """Remote MCP Server - HTTP/WebSocket üzerinden."""
    
    def __init__(self, name: str, base_url: str, api_key: str = None):
        """Remote server başlat."""
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._tools_cache: Optional[List[MCPToolDefinition]] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """HTTP headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def fetch_tools(self) -> List[MCPToolDefinition]:
        """Uzak sunucudan araçları al."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tools",
                headers=self._get_headers(),
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
            
            tools = []
            for tool_data in data.get("tools", []):
                tools.append(MCPToolDefinition(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("parameters", {}),
                    required_params=tool_data.get("required", []),
                ))
            
            self._tools_cache = tools
            return tools
    
    def get_tools(self) -> List[MCPToolDefinition]:
        """Cache'lenmiş araçları döndür."""
        if self._tools_cache is None:
            # Sync wrapper
            return asyncio.run(self.fetch_tools())
        return self._tools_cache
    
    async def execute_tool(self, call: MCPToolCall) -> MCPToolResult:
        """Uzak aracı çalıştır."""
        import time
        import uuid
        
        start_time = time.time()
        call_id = call.call_id or str(uuid.uuid4())[:8]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/tools/{call.tool_name}/execute",
                    headers=self._get_headers(),
                    json={"arguments": call.arguments},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                
                execution_time = (time.time() - start_time) * 1000
                
                return MCPToolResult(
                    call_id=call_id,
                    success=data.get("success", True),
                    result=data.get("result"),
                    error=data.get("error"),
                    execution_time_ms=execution_time,
                )
        
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return MCPToolResult(
                call_id=call_id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )


class MCPHub:
    """
    MCP Hub - Tüm MCP sunucularını yönetir.
    
    Araçları keşfeder, çağrıları yönlendirir.
    """
    
    def __init__(self):
        """Hub başlat."""
        self._servers: Dict[str, MCPServer] = {}
        self._tool_to_server: Dict[str, str] = {}
    
    def register_server(self, server: MCPServer, server_id: str = None):
        """
        Sunucu kaydet.
        
        Args:
            server: MCP sunucusu
            server_id: Sunucu kimliği
        """
        server_id = server_id or server.name
        self._servers[server_id] = server
        
        # Map tools to server
        for tool in server.get_tools():
            self._tool_to_server[tool.name] = server_id
    
    def get_all_tools(self) -> List[MCPToolDefinition]:
        """Tüm sunuculardan tüm araçları al."""
        all_tools = []
        for server in self._servers.values():
            all_tools.extend(server.get_tools())
        return all_tools
    
    def get_tools_for_llm(self) -> List[Dict]:
        """LLM için araç tanımları (OpenAI format)."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": tool.required_params,
                    },
                },
            }
            for tool in self.get_all_tools()
        ]
    
    async def execute_tool(self, call: MCPToolCall) -> MCPToolResult:
        """Aracı çalıştır (doğru sunucuya yönlendir)."""
        server_id = self._tool_to_server.get(call.tool_name)
        
        if not server_id:
            return MCPToolResult(
                call_id=call.call_id,
                success=False,
                error=f"Tool not found: {call.tool_name}",
            )
        
        server = self._servers[server_id]
        return await server.execute_tool(call)
    
    def execute_tool_sync(self, call: MCPToolCall) -> MCPToolResult:
        """Senkron araç çalıştırma."""
        return asyncio.run(self.execute_tool(call))


# ============ BUILT-IN TOOLS ============

def create_builtin_mcp_server() -> LocalMCPServer:
    """Yerleşik araçlarla MCP sunucusu oluştur."""
    server = LocalMCPServer("builtin")
    
    # Calculator tool
    def calculator(expression: str) -> Dict[str, Any]:
        """Matematiksel ifadeyi hesapla."""
        try:
            # Safe eval for math
            allowed = set("0123456789+-*/.() ")
            if not all(c in allowed for c in expression):
                return {"error": "Invalid expression"}
            result = eval(expression)
            return {"result": result, "expression": expression}
        except Exception as e:
            return {"error": str(e)}
    
    server.register_tool(
        name="calculator",
        description="Matematiksel ifadeleri hesaplar",
        parameters={
            "expression": {"type": "string", "description": "Hesaplanacak ifade (örn: 2+2*3)"},
        },
        handler=calculator,
        required_params=["expression"],
    )
    
    # Current time tool
    def get_current_time(timezone: str = "UTC") -> Dict[str, Any]:
        """Mevcut zamanı döndür."""
        from datetime import datetime
        now = datetime.now()
        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timezone": timezone,
        }
    
    server.register_tool(
        name="get_current_time",
        description="Mevcut tarih ve saati döndürür",
        parameters={
            "timezone": {"type": "string", "description": "Saat dilimi", "default": "UTC"},
        },
        handler=get_current_time,
    )
    
    # File info tool
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Dosya bilgilerini döndür."""
        from pathlib import Path
        
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found"}
        
        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "extension": path.suffix,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
    
    server.register_tool(
        name="get_file_info",
        description="Dosya bilgilerini döndürür",
        parameters={
            "file_path": {"type": "string", "description": "Dosya yolu"},
        },
        handler=get_file_info,
        required_params=["file_path"],
    )
    
    return server


# Singleton instances
mcp_hub = MCPHub()
builtin_server = create_builtin_mcp_server()
mcp_hub.register_server(builtin_server, "builtin")
