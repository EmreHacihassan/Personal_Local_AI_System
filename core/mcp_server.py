"""
🌐 MCP Server - Model Context Protocol Implementation
=====================================================

Anthropic MCP standardına tam uyumlu server implementasyonu.
Claude Desktop, Cursor, VS Code ve diğer MCP client'lar ile uyumlu.

MCP Protocol Spec: https://modelcontextprotocol.io/

Features:
- Full MCP 2024.1 Protocol Support
- JSON-RPC 2.0 Transport
- Resources (dökümanlar, RAG chunks, sessions)
- Tools (web_search, calculate, file_ops, rag_query)
- Prompts (system templates)
- Sampling (LLM generation)
- Roots (file system access)
- Notifications
- Progress tracking
- Cancellation support
"""

import asyncio
import json
import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any, Callable, Coroutine, Dict, List, Optional, 
    TypeVar, Union, AsyncIterator, Literal
)
import sys

# ============ MCP PROTOCOL TYPES ============

class MCPVersion:
    """MCP Protocol Versions"""
    V2024_1 = "2024-11-05"
    CURRENT = V2024_1


class MCPMethod(str, Enum):
    """MCP JSON-RPC Methods"""
    # Lifecycle
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"
    SHUTDOWN = "shutdown"
    
    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"
    
    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    
    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    
    # Sampling
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"
    
    # Roots
    ROOTS_LIST = "roots/list"
    
    # Completion
    COMPLETION_COMPLETE = "completion/complete"
    
    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"
    
    # Notifications
    NOTIFY_PROGRESS = "notifications/progress"
    NOTIFY_MESSAGE = "notifications/message"
    NOTIFY_RESOURCES_UPDATED = "notifications/resources/updated"
    NOTIFY_RESOURCES_LIST_CHANGED = "notifications/resources/list_changed"
    NOTIFY_TOOLS_LIST_CHANGED = "notifications/tools/list_changed"
    NOTIFY_PROMPTS_LIST_CHANGED = "notifications/prompts/list_changed"
    NOTIFY_CANCELLED = "notifications/cancelled"


class MCPError(Exception):
    """MCP Error with code"""
    
    # Standard JSON-RPC errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific errors
    RESOURCE_NOT_FOUND = -32001
    TOOL_NOT_FOUND = -32002
    PROMPT_NOT_FOUND = -32003
    CANCELLED = -32004
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
    
    def to_dict(self) -> Dict:
        error = {"code": self.code, "message": self.message}
        if self.data:
            error["data"] = self.data
        return error


# ============ MCP DATA STRUCTURES ============

@dataclass
class MCPCapabilities:
    """Server capabilities"""
    experimental: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    prompts: Dict[str, Any] = field(default_factory=lambda: {"listChanged": True})
    resources: Dict[str, Any] = field(default_factory=lambda: {"subscribe": True, "listChanged": True})
    tools: Dict[str, Any] = field(default_factory=lambda: {"listChanged": True})
    sampling: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerInfo:
    """Server information"""
    name: str
    version: str
    
    def to_dict(self) -> Dict:
        return {"name": self.name, "version": self.version}


@dataclass
class MCPResource:
    """MCP Resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        result = {"uri": self.uri, "name": self.name}
        if self.description:
            result["description"] = self.description
        if self.mimeType:
            result["mimeType"] = self.mimeType
        if self.annotations:
            result["annotations"] = self.annotations
        return result


@dataclass
class MCPResourceContent:
    """Resource content"""
    uri: str
    mimeType: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[str] = None  # base64 encoded
    
    def to_dict(self) -> Dict:
        result = {"uri": self.uri}
        if self.mimeType:
            result["mimeType"] = self.mimeType
        if self.text is not None:
            result["text"] = self.text
        if self.blob is not None:
            result["blob"] = self.blob
        return result


@dataclass
class MCPToolInput:
    """Tool input schema (JSON Schema)"""
    type: str = "object"
    properties: Dict[str, Any] = field(default_factory=dict)
    required: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "properties": self.properties,
            "required": self.required
        }


@dataclass
class MCPTool:
    """MCP Tool definition"""
    name: str
    description: Optional[str] = None
    inputSchema: MCPToolInput = field(default_factory=MCPToolInput)
    
    def to_dict(self) -> Dict:
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        result["inputSchema"] = self.inputSchema.to_dict()
        return result


@dataclass
class MCPToolResult:
    """Tool execution result"""
    content: List[Dict[str, Any]]  # Array of content items
    isError: bool = False
    
    def to_dict(self) -> Dict:
        return {"content": self.content, "isError": self.isError}


@dataclass
class MCPPromptArgument:
    """Prompt argument definition"""
    name: str
    description: Optional[str] = None
    required: bool = False
    
    def to_dict(self) -> Dict:
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.required:
            result["required"] = self.required
        return result


@dataclass
class MCPPrompt:
    """MCP Prompt definition"""
    name: str
    description: Optional[str] = None
    arguments: List[MCPPromptArgument] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.arguments:
            result["arguments"] = [a.to_dict() for a in self.arguments]
        return result


@dataclass
class MCPPromptMessage:
    """Prompt message"""
    role: Literal["user", "assistant"]
    content: Dict[str, Any]  # {type: "text", text: "..."} or {type: "image", ...}
    
    def to_dict(self) -> Dict:
        return {"role": self.role, "content": self.content}


@dataclass
class MCPRoot:
    """File system root"""
    uri: str
    name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {"uri": self.uri}
        if self.name:
            result["name"] = self.name
        return result


@dataclass
class MCPSamplingMessage:
    """Sampling request message"""
    role: Literal["user", "assistant"]
    content: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {"role": self.role, "content": self.content}


# ============ MCP SERVER IMPLEMENTATION ============

class MCPResourceProvider(ABC):
    """Abstract resource provider"""
    
    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> MCPResourceContent:
        pass


class MCPToolProvider(ABC):
    """Abstract tool provider"""
    
    @abstractmethod
    def get_tools(self) -> List[MCPTool]:
        pass
    
    @abstractmethod
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        pass


class MCPPromptProvider(ABC):
    """Abstract prompt provider"""
    
    @abstractmethod
    def get_prompts(self) -> List[MCPPrompt]:
        pass
    
    @abstractmethod
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> List[MCPPromptMessage]:
        pass


class MCPServer:
    """
    Full MCP Server Implementation
    
    Handles JSON-RPC 2.0 messages and implements the MCP protocol.
    """
    
    def __init__(
        self,
        name: str = "enterprise-ai-assistant",
        version: str = "1.0.0"
    ):
        self.server_info = MCPServerInfo(name=name, version=version)
        self.capabilities = MCPCapabilities()
        self.protocol_version = MCPVersion.CURRENT
        
        # Providers
        self._resource_providers: List[MCPResourceProvider] = []
        self._tool_providers: List[MCPToolProvider] = []
        self._prompt_providers: List[MCPPromptProvider] = []
        
        # State
        self._initialized = False
        self._client_info: Optional[Dict] = None
        self._subscriptions: Dict[str, List[str]] = {}  # uri -> client_ids
        
        # Request handlers
        self._handlers: Dict[str, Callable] = {
            MCPMethod.INITIALIZE.value: self._handle_initialize,
            MCPMethod.SHUTDOWN.value: self._handle_shutdown,
            MCPMethod.RESOURCES_LIST.value: self._handle_resources_list,
            MCPMethod.RESOURCES_READ.value: self._handle_resources_read,
            MCPMethod.RESOURCES_SUBSCRIBE.value: self._handle_resources_subscribe,
            MCPMethod.RESOURCES_UNSUBSCRIBE.value: self._handle_resources_unsubscribe,
            MCPMethod.TOOLS_LIST.value: self._handle_tools_list,
            MCPMethod.TOOLS_CALL.value: self._handle_tools_call,
            MCPMethod.PROMPTS_LIST.value: self._handle_prompts_list,
            MCPMethod.PROMPTS_GET.value: self._handle_prompts_get,
            MCPMethod.ROOTS_LIST.value: self._handle_roots_list,
            MCPMethod.COMPLETION_COMPLETE.value: self._handle_completion,
            MCPMethod.LOGGING_SET_LEVEL.value: self._handle_logging_set_level,
        }
        
        # Pending requests for cancellation
        self._pending_requests: Dict[str, asyncio.Task] = {}
    
    # ============ REGISTRATION ============
    
    def register_resource_provider(self, provider: MCPResourceProvider):
        """Register a resource provider"""
        self._resource_providers.append(provider)
    
    def register_tool_provider(self, provider: MCPToolProvider):
        """Register a tool provider"""
        self._tool_providers.append(provider)
    
    def register_prompt_provider(self, provider: MCPPromptProvider):
        """Register a prompt provider"""
        self._prompt_providers.append(provider)
    
    # ============ MESSAGE HANDLING ============
    
    async def handle_message(self, message: str) -> Optional[str]:
        """
        Handle incoming JSON-RPC message
        
        Args:
            message: JSON-RPC message string
            
        Returns:
            Response JSON string or None for notifications
        """
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            return self._error_response(
                None, 
                MCPError(MCPError.PARSE_ERROR, f"Parse error: {e}")
            )
        
        # Handle batch requests
        if isinstance(data, list):
            responses = []
            for item in data:
                response = await self._handle_single_message(item)
                if response:
                    responses.append(json.loads(response))
            return json.dumps(responses) if responses else None
        
        return await self._handle_single_message(data)
    
    async def _handle_single_message(self, data: Dict) -> Optional[str]:
        """Handle single JSON-RPC message"""
        # Validate JSON-RPC
        if data.get("jsonrpc") != "2.0":
            return self._error_response(
                data.get("id"),
                MCPError(MCPError.INVALID_REQUEST, "Invalid JSON-RPC version")
            )
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        # Notifications (no id)
        if request_id is None:
            await self._handle_notification(method, params)
            return None
        
        # Requests
        handler = self._handlers.get(method)
        if not handler:
            return self._error_response(
                request_id,
                MCPError(MCPError.METHOD_NOT_FOUND, f"Method not found: {method}")
            )
        
        try:
            # Create cancellable task
            task = asyncio.create_task(handler(params))
            self._pending_requests[str(request_id)] = task
            
            result = await task
            
            del self._pending_requests[str(request_id)]
            
            return self._success_response(request_id, result)
            
        except MCPError as e:
            return self._error_response(request_id, e)
        except asyncio.CancelledError:
            return self._error_response(
                request_id,
                MCPError(MCPError.CANCELLED, "Request cancelled")
            )
        except Exception as e:
            return self._error_response(
                request_id,
                MCPError(MCPError.INTERNAL_ERROR, str(e))
            )
    
    async def _handle_notification(self, method: str, params: Dict):
        """Handle notification messages"""
        if method == MCPMethod.INITIALIZED.value:
            self._initialized = True
        elif method == MCPMethod.NOTIFY_CANCELLED.value:
            request_id = params.get("requestId")
            if request_id and str(request_id) in self._pending_requests:
                self._pending_requests[str(request_id)].cancel()
    
    def _success_response(self, request_id: Any, result: Any) -> str:
        """Create success response"""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })
    
    def _error_response(self, request_id: Any, error: MCPError) -> str:
        """Create error response"""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error.to_dict()
        })
    
    # ============ REQUEST HANDLERS ============
    
    async def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request"""
        self._client_info = params.get("clientInfo")
        
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": asdict(self.capabilities),
            "serverInfo": self.server_info.to_dict()
        }
    
    async def _handle_shutdown(self, params: Dict) -> Dict:
        """Handle shutdown request"""
        self._initialized = False
        return {}
    
    async def _handle_resources_list(self, params: Dict) -> Dict:
        """Handle resources/list request"""
        cursor = params.get("cursor")
        
        all_resources = []
        for provider in self._resource_providers:
            resources = await provider.list_resources()
            all_resources.extend([r.to_dict() for r in resources])
        
        # Simple pagination (could be improved)
        page_size = 100
        start = 0 if not cursor else int(cursor)
        end = start + page_size
        
        page = all_resources[start:end]
        next_cursor = str(end) if end < len(all_resources) else None
        
        result = {"resources": page}
        if next_cursor:
            result["nextCursor"] = next_cursor
        
        return result
    
    async def _handle_resources_read(self, params: Dict) -> Dict:
        """Handle resources/read request"""
        uri = params.get("uri")
        if not uri:
            raise MCPError(MCPError.INVALID_PARAMS, "uri is required")
        
        for provider in self._resource_providers:
            try:
                content = await provider.read_resource(uri)
                return {"contents": [content.to_dict()]}
            except Exception:
                continue
        
        raise MCPError(MCPError.RESOURCE_NOT_FOUND, f"Resource not found: {uri}")
    
    async def _handle_resources_subscribe(self, params: Dict) -> Dict:
        """Handle resources/subscribe request"""
        uri = params.get("uri")
        if not uri:
            raise MCPError(MCPError.INVALID_PARAMS, "uri is required")
        
        if uri not in self._subscriptions:
            self._subscriptions[uri] = []
        
        # Add subscription (simplified - would need client tracking in real impl)
        self._subscriptions[uri].append("default")
        
        return {}
    
    async def _handle_resources_unsubscribe(self, params: Dict) -> Dict:
        """Handle resources/unsubscribe request"""
        uri = params.get("uri")
        if uri in self._subscriptions:
            self._subscriptions[uri] = []
        return {}
    
    async def _handle_tools_list(self, params: Dict) -> Dict:
        """Handle tools/list request"""
        cursor = params.get("cursor")
        
        all_tools = []
        for provider in self._tool_providers:
            tools = provider.get_tools()
            all_tools.extend([t.to_dict() for t in tools])
        
        return {"tools": all_tools}
    
    async def _handle_tools_call(self, params: Dict) -> Dict:
        """Handle tools/call request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise MCPError(MCPError.INVALID_PARAMS, "name is required")
        
        for provider in self._tool_providers:
            tools = provider.get_tools()
            if any(t.name == name for t in tools):
                result = await provider.execute_tool(name, arguments)
                return result.to_dict()
        
        raise MCPError(MCPError.TOOL_NOT_FOUND, f"Tool not found: {name}")
    
    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """Handle prompts/list request"""
        cursor = params.get("cursor")
        
        all_prompts = []
        for provider in self._prompt_providers:
            prompts = provider.get_prompts()
            all_prompts.extend([p.to_dict() for p in prompts])
        
        return {"prompts": all_prompts}
    
    async def _handle_prompts_get(self, params: Dict) -> Dict:
        """Handle prompts/get request"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise MCPError(MCPError.INVALID_PARAMS, "name is required")
        
        for provider in self._prompt_providers:
            prompts = provider.get_prompts()
            if any(p.name == name for p in prompts):
                messages = await provider.get_prompt(name, arguments)
                return {
                    "description": next((p.description for p in prompts if p.name == name), None),
                    "messages": [m.to_dict() for m in messages]
                }
        
        raise MCPError(MCPError.PROMPT_NOT_FOUND, f"Prompt not found: {name}")
    
    async def _handle_roots_list(self, params: Dict) -> Dict:
        """Handle roots/list request"""
        # Return project root
        project_root = Path(__file__).parent.parent
        return {
            "roots": [
                MCPRoot(
                    uri=f"file://{project_root}",
                    name="Enterprise AI Assistant"
                ).to_dict()
            ]
        }
    
    async def _handle_completion(self, params: Dict) -> Dict:
        """Handle completion/complete request"""
        ref = params.get("ref", {})
        argument = params.get("argument", {})
        
        # Basic completion logic
        completions = []
        
        ref_type = ref.get("type")
        if ref_type == "ref/resource":
            # Complete resource URIs
            for provider in self._resource_providers:
                resources = await provider.list_resources()
                for r in resources:
                    if argument.get("value", "") in r.uri:
                        completions.append({"values": [r.uri]})
        
        elif ref_type == "ref/prompt":
            # Complete prompt names
            for provider in self._prompt_providers:
                prompts = provider.get_prompts()
                for p in prompts:
                    if argument.get("value", "") in p.name:
                        completions.append({"values": [p.name]})
        
        return {"completion": {"values": completions[:10]}}
    
    async def _handle_logging_set_level(self, params: Dict) -> Dict:
        """Handle logging/setLevel request"""
        level = params.get("level", "info")
        # Update logging level
        import logging
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR
        }
        logging.getLogger().setLevel(level_map.get(level, logging.INFO))
        return {}
    
    # ============ NOTIFICATIONS ============
    
    def create_notification(self, method: str, params: Dict = None) -> str:
        """Create a notification message"""
        return json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        })
    
    def notify_progress(
        self, 
        progress_token: str, 
        progress: float, 
        total: Optional[float] = None
    ) -> str:
        """Create progress notification"""
        params = {"progressToken": progress_token, "progress": progress}
        if total is not None:
            params["total"] = total
        return self.create_notification(MCPMethod.NOTIFY_PROGRESS.value, params)
    
    def notify_resource_updated(self, uri: str) -> str:
        """Notify that a resource was updated"""
        return self.create_notification(
            MCPMethod.NOTIFY_RESOURCES_UPDATED.value,
            {"uri": uri}
        )
    
    def notify_resources_list_changed(self) -> str:
        """Notify that the resources list changed"""
        return self.create_notification(MCPMethod.NOTIFY_RESOURCES_LIST_CHANGED.value)
    
    def notify_tools_list_changed(self) -> str:
        """Notify that the tools list changed"""
        return self.create_notification(MCPMethod.NOTIFY_TOOLS_LIST_CHANGED.value)


# ============ TRANSPORT IMPLEMENTATIONS ============

class MCPStdioTransport:
    """
    STDIO Transport for MCP
    
    Used for local MCP server (Claude Desktop, etc.)
    """
    
    def __init__(self, server: MCPServer):
        self.server = server
    
    async def run(self):
        """Run the STDIO transport"""
        import sys
        
        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Handle message
                response = await self.server.handle_message(line)
                
                if response:
                    # Write response to stdout
                    sys.stdout.write(response + "\n")
                    sys.stdout.flush()
                    
            except Exception as e:
                error = MCPError(MCPError.INTERNAL_ERROR, str(e))
                sys.stdout.write(json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": error.to_dict()
                }) + "\n")
                sys.stdout.flush()


class MCPWebSocketTransport:
    """
    WebSocket Transport for MCP
    
    Used for remote MCP server access.
    """
    
    def __init__(self, server: MCPServer):
        self.server = server
        self._connections: Dict[str, Any] = {}
    
    async def handle_connection(self, websocket, path: str = "/"):
        """Handle WebSocket connection"""
        connection_id = str(uuid.uuid4())
        self._connections[connection_id] = websocket
        
        try:
            async for message in websocket:
                response = await self.server.handle_message(message)
                if response:
                    await websocket.send(response)
        finally:
            del self._connections[connection_id]
    
    async def broadcast_notification(self, notification: str):
        """Broadcast notification to all connections"""
        for ws in self._connections.values():
            try:
                await ws.send(notification)
            except Exception:
                pass


class MCPHTTPTransport:
    """
    HTTP Transport for MCP (SSE for notifications)
    
    RESTful access to MCP server.
    """
    
    def __init__(self, server: MCPServer):
        self.server = server
    
    async def handle_request(self, body: str) -> str:
        """Handle HTTP POST request"""
        return await self.server.handle_message(body) or "{}"


# ============ EXPORTS ============

__all__ = [
    # Types
    "MCPVersion",
    "MCPMethod",
    "MCPError",
    "MCPCapabilities",
    "MCPServerInfo",
    "MCPResource",
    "MCPResourceContent",
    "MCPTool",
    "MCPToolInput",
    "MCPToolResult",
    "MCPPrompt",
    "MCPPromptArgument",
    "MCPPromptMessage",
    "MCPRoot",
    "MCPSamplingMessage",
    # Providers
    "MCPResourceProvider",
    "MCPToolProvider",
    "MCPPromptProvider",
    # Server
    "MCPServer",
    # Transports
    "MCPStdioTransport",
    "MCPWebSocketTransport",
    "MCPHTTPTransport",
]
