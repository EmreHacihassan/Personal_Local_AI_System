"""
🌐 MCP API Endpoints - REST & WebSocket Interface
=================================================

MCP Protocol'ün HTTP ve WebSocket üzerinden erişilebilir hale getirilmesi.
Claude Desktop, VSCode, ve diğer MCP client'ların bağlanabilmesi için.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path

# MCP Server import
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.mcp_server import (
    MCPServer, MCPHTTPTransport, MCPWebSocketTransport,
    MCPResource, MCPTool, MCPToolResult
)
from core.mcp_providers import (
    DocumentResourceProvider, SessionResourceProvider, NotesResourceProvider,
    CoreToolProvider, RAGToolProvider, WebSearchToolProvider,
    SystemPromptProvider
)

logger = logging.getLogger(__name__)

# ============ ROUTER ============

mcp_router = APIRouter(prefix="/mcp", tags=["MCP Protocol"])


# ============ GLOBAL MCP SERVER ============

_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get or create MCP server instance"""
    global _mcp_server
    
    if _mcp_server is None:
        _mcp_server = MCPServer(
            name="AgenticManagingSystem",
            version="1.0.0"
        )
        
        # Register providers
        _mcp_server.add_resource_provider(DocumentResourceProvider())
        _mcp_server.add_resource_provider(SessionResourceProvider())
        _mcp_server.add_resource_provider(NotesResourceProvider())
        
        _mcp_server.add_tool_provider(CoreToolProvider())
        _mcp_server.add_tool_provider(RAGToolProvider())
        _mcp_server.add_tool_provider(WebSearchToolProvider())
        
        _mcp_server.add_prompt_provider(SystemPromptProvider())
        
        logger.info("🔧 MCP Server initialized with all providers")
    
    return _mcp_server


# ============ PYDANTIC MODELS ============

class MCPRequest(BaseModel):
    """JSON-RPC 2.0 Request"""
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class MCPResponse(BaseModel):
    """JSON-RPC 2.0 Response"""
    jsonrpc: str = "2.0"
    id: Optional[int | str] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class ToolCallRequest(BaseModel):
    """Simplified tool call request"""
    tool_name: str
    arguments: Dict[str, Any] = {}


class ResourceReadRequest(BaseModel):
    """Resource read request"""
    uri: str


class PromptGetRequest(BaseModel):
    """Prompt get request"""
    name: str
    arguments: Dict[str, Any] = {}


# ============ HTTP ENDPOINTS ============

@mcp_router.get("/")
async def mcp_info():
    """MCP Server information"""
    server = get_mcp_server()
    
    return {
        "name": server.name,
        "version": server.version,
        "protocol_version": server.protocol_version,
        "capabilities": server.capabilities,
        "status": "running",
        "endpoints": {
            "rpc": "/mcp/rpc",
            "websocket": "/mcp/ws",
            "tools": "/mcp/tools",
            "resources": "/mcp/resources",
            "prompts": "/mcp/prompts"
        }
    }


@mcp_router.post("/rpc")
async def mcp_rpc(request: MCPRequest):
    """
    JSON-RPC 2.0 endpoint
    
    Main MCP protocol endpoint. Supports all MCP methods:
    - initialize
    - tools/list, tools/call
    - resources/list, resources/read, resources/subscribe
    - prompts/list, prompts/get
    - completion/complete
    """
    server = get_mcp_server()
    
    try:
        # Convert request to dict
        request_dict = request.model_dump()
        
        # Handle the request through MCP server
        response = await server.handle_request(request_dict)
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"MCP RPC error: {e}")
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        })


@mcp_router.get("/tools")
async def list_tools():
    """List all available MCP tools"""
    server = get_mcp_server()
    tools = await server.list_tools()
    
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema.model_dump() if t.inputSchema else None
            }
            for t in tools
        ],
        "count": len(tools)
    }


@mcp_router.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call a specific tool"""
    server = get_mcp_server()
    
    result = await server.call_tool(request.tool_name, request.arguments)
    
    return {
        "tool": request.tool_name,
        "result": {
            "content": result.content,
            "isError": result.isError
        },
        "timestamp": datetime.now().isoformat()
    }


@mcp_router.get("/resources")
async def list_resources():
    """List all available MCP resources"""
    server = get_mcp_server()
    resources = await server.list_resources()
    
    return {
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mimeType": r.mimeType,
                "annotations": r.annotations
            }
            for r in resources
        ],
        "count": len(resources)
    }


@mcp_router.post("/resources/read")
async def read_resource(request: ResourceReadRequest):
    """Read a specific resource"""
    server = get_mcp_server()
    
    try:
        content = await server.read_resource(request.uri)
        
        return {
            "uri": request.uri,
            "content": {
                "mimeType": content.mimeType,
                "text": content.text,
                "blob": content.blob
            }
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@mcp_router.get("/prompts")
async def list_prompts():
    """List all available MCP prompts"""
    server = get_mcp_server()
    prompts = await server.list_prompts()
    
    return {
        "prompts": [
            {
                "name": p.name,
                "description": p.description,
                "arguments": [
                    {"name": a.name, "description": a.description, "required": a.required}
                    for a in (p.arguments or [])
                ]
            }
            for p in prompts
        ],
        "count": len(prompts)
    }


@mcp_router.post("/prompts/get")
async def get_prompt(request: PromptGetRequest):
    """Get a specific prompt with arguments filled in"""
    server = get_mcp_server()
    
    try:
        messages = await server.get_prompt(request.name, request.arguments)
        
        return {
            "prompt": request.name,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content
                }
                for m in messages
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============ WEBSOCKET ENDPOINT ============

@mcp_router.websocket("/ws")
async def mcp_websocket(websocket: WebSocket):
    """
    MCP WebSocket endpoint
    
    Full-duplex MCP communication for real-time clients.
    Supports server-initiated notifications (resource updates, etc.)
    """
    server = get_mcp_server()
    transport = MCPWebSocketTransport(websocket)
    
    await websocket.accept()
    logger.info("📡 MCP WebSocket client connected")
    
    try:
        while True:
            # Receive JSON-RPC message
            data = await websocket.receive_text()
            
            try:
                request = json.loads(data)
                
                # Handle through MCP server
                response = await server.handle_request(request)
                
                # Send response
                await websocket.send_text(json.dumps(response))
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }))
                
    except WebSocketDisconnect:
        logger.info("📡 MCP WebSocket client disconnected")
    except Exception as e:
        logger.error(f"MCP WebSocket error: {e}")
        await websocket.close()


# ============ SSE ENDPOINT (Server-Sent Events) ============

@mcp_router.get("/events")
async def mcp_events():
    """
    Server-Sent Events for MCP notifications
    
    Streams resource updates, tool completions, etc.
    """
    async def event_generator():
        server = get_mcp_server()
        
        # Initial connection event
        yield f"event: connected\ndata: {json.dumps({'server': server.name})}\n\n"
        
        # Keep-alive and notifications
        while True:
            await asyncio.sleep(30)  # Heartbeat every 30s
            yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============ CLAUDE DESKTOP CONFIG ============

@mcp_router.get("/claude-config")
async def get_claude_desktop_config():
    """
    Get Claude Desktop MCP configuration
    
    Returns configuration for adding this server to Claude Desktop.
    """
    import socket
    
    hostname = socket.gethostname()
    
    return {
        "description": "Add this configuration to Claude Desktop's config file",
        "config_path": {
            "windows": "%APPDATA%\\Claude\\claude_desktop_config.json",
            "mac": "~/Library/Application Support/Claude/claude_desktop_config.json",
            "linux": "~/.config/Claude/claude_desktop_config.json"
        },
        "mcp_config": {
            "mcpServers": {
                "agenticmanagingsystem": {
                    "command": "python",
                    "args": [
                        "-m",
                        "core.mcp_cli"
                    ],
                    "cwd": str(Path(__file__).parent.parent),
                    "env": {}
                }
            }
        },
        "alternative_http_config": {
            "mcpServers": {
                "agenticmanagingsystem": {
                    "url": f"http://localhost:8001/mcp/rpc",
                    "transport": "http"
                }
            }
        }
    }


# ============ DIAGNOSTICS ============

@mcp_router.get("/diagnostics")
async def mcp_diagnostics():
    """
    MCP server diagnostics
    
    Check server health, registered providers, etc.
    """
    server = get_mcp_server()
    
    tools = await server.list_tools()
    resources = await server.list_resources()
    prompts = await server.list_prompts()
    
    return {
        "server": {
            "name": server.name,
            "version": server.version,
            "protocol_version": server.protocol_version
        },
        "providers": {
            "resource_providers": len(server.resource_providers),
            "tool_providers": len(server.tool_providers),
            "prompt_providers": len(server.prompt_providers)
        },
        "registered": {
            "tools": len(tools),
            "resources": len(resources),
            "prompts": len(prompts)
        },
        "tool_names": [t.name for t in tools],
        "resource_uris": [r.uri for r in resources[:10]],  # First 10
        "prompt_names": [p.name for p in prompts],
        "health": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ============ EXPORTS ============

__all__ = [
    "mcp_router",
    "get_mcp_server"
]
