#!/usr/bin/env python3
"""
🖥️ MCP CLI Runner - Claude Desktop & Stdio Integration
=======================================================

Bu modül MCP sunucusunu Claude Desktop ve diğer stdio-based
MCP clientlar için çalıştırır.

Kullanım:
    python -m core.mcp_cli
    
Claude Desktop config.json:
{
    "mcpServers": {
        "agenticmanagingsystem": {
            "command": "python",
            "args": ["-m", "core.mcp_cli"],
            "cwd": "/path/to/AgenticManagingSystem"
        }
    }
}
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp_server import MCPServer, MCPStdioTransport
from core.mcp_providers import (
    DocumentResourceProvider, SessionResourceProvider, NotesResourceProvider,
    CoreToolProvider, RAGToolProvider, WebSearchToolProvider,
    SystemPromptProvider
)

# Configure logging to stderr (stdio uses stdin/stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MCP - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class MCPStdioRunner:
    """
    MCP Stdio Runner
    
    Runs MCP server over stdin/stdout for Claude Desktop integration.
    """
    
    def __init__(self):
        self.server: Optional[MCPServer] = None
        self.transport: Optional[MCPStdioTransport] = None
        self.running = False
    
    def setup_server(self) -> MCPServer:
        """Initialize MCP server with all providers"""
        server = MCPServer(
            name="AgenticManagingSystem",
            version="1.0.0"
        )
        
        # Resource Providers
        try:
            server.add_resource_provider(DocumentResourceProvider())
            logger.info("📁 Document provider registered")
        except Exception as e:
            logger.warning(f"Document provider failed: {e}")
        
        try:
            server.add_resource_provider(SessionResourceProvider())
            logger.info("💬 Session provider registered")
        except Exception as e:
            logger.warning(f"Session provider failed: {e}")
        
        try:
            server.add_resource_provider(NotesResourceProvider())
            logger.info("📝 Notes provider registered")
        except Exception as e:
            logger.warning(f"Notes provider failed: {e}")
        
        # Tool Providers
        try:
            server.add_tool_provider(CoreToolProvider())
            logger.info("🔧 Core tools registered")
        except Exception as e:
            logger.warning(f"Core tools failed: {e}")
        
        try:
            server.add_tool_provider(RAGToolProvider())
            logger.info("🔍 RAG tools registered")
        except Exception as e:
            logger.warning(f"RAG tools failed: {e}")
        
        try:
            server.add_tool_provider(WebSearchToolProvider())
            logger.info("🌐 Web search tools registered")
        except Exception as e:
            logger.warning(f"Web search tools failed: {e}")
        
        # Prompt Providers
        try:
            server.add_prompt_provider(SystemPromptProvider())
            logger.info("💡 Prompt templates registered")
        except Exception as e:
            logger.warning(f"Prompt provider failed: {e}")
        
        return server
    
    async def run(self):
        """Run the MCP server over stdio"""
        logger.info("🚀 Starting MCP Stdio Server")
        
        # Setup server
        self.server = self.setup_server()
        self.transport = MCPStdioTransport()
        self.running = True
        
        logger.info("📡 MCP Server ready for connections")
        
        try:
            while self.running:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    # EOF - client disconnected
                    logger.info("📴 Client disconnected (EOF)")
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {e}"
                        }
                    }
                    self._write_response(error_response)
                    continue
                
                # Handle request
                try:
                    response = await self.server.handle_request(request)
                    self._write_response(response)
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {e}"
                        }
                    }
                    self._write_response(error_response)
                    
        except KeyboardInterrupt:
            logger.info("🛑 Server interrupted")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            logger.info("👋 MCP Server shutdown complete")
    
    def _write_response(self, response: dict):
        """Write JSON-RPC response to stdout"""
        json_str = json.dumps(response)
        sys.stdout.write(json_str + "\n")
        sys.stdout.flush()
    
    def send_notification(self, method: str, params: dict = None):
        """Send a notification to the client"""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        self._write_response(notification)


async def main():
    """Main entry point"""
    runner = MCPStdioRunner()
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
