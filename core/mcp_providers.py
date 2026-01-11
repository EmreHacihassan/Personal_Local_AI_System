"""
🛠️ MCP Providers - Resource, Tool, Prompt Providers
====================================================

Enterprise AI Assistant için MCP provider implementasyonları.
Tüm sistem kaynaklarını, araçları ve promptları MCP üzerinden expose eder.
"""

import asyncio
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib

from .mcp_server import (
    MCPResourceProvider, MCPToolProvider, MCPPromptProvider,
    MCPResource, MCPResourceContent, MCPTool, MCPToolInput, MCPToolResult,
    MCPPrompt, MCPPromptArgument, MCPPromptMessage
)
from .config import settings


# ============ RESOURCE PROVIDERS ============

class DocumentResourceProvider(MCPResourceProvider):
    """
    Document Resource Provider
    
    Exposes uploaded documents and RAG chunks as MCP resources.
    """
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.uploads_dir = settings.DATA_DIR / "uploads"
    
    async def list_resources(self) -> List[MCPResource]:
        """List all document resources"""
        resources = []
        
        # 1. Uploaded files
        if self.uploads_dir.exists():
            for file_path in self.uploads_dir.glob("**/*"):
                if file_path.is_file():
                    mime_type = self._get_mime_type(file_path)
                    resources.append(MCPResource(
                        uri=f"document://uploads/{file_path.relative_to(self.uploads_dir)}",
                        name=file_path.name,
                        description=f"Uploaded document: {file_path.name}",
                        mimeType=mime_type,
                        annotations={
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                    ))
        
        # 2. Vector store sources (if available)
        if self.vector_store:
            try:
                sources = self.vector_store.get_unique_sources()
                for source in sources:
                    resources.append(MCPResource(
                        uri=f"document://indexed/{source}",
                        name=source,
                        description=f"Indexed document chunks from: {source}",
                        mimeType="application/x-chunks"
                    ))
            except Exception:
                pass
        
        return resources
    
    async def read_resource(self, uri: str) -> MCPResourceContent:
        """Read document resource content"""
        if uri.startswith("document://uploads/"):
            # Read uploaded file
            relative_path = uri.replace("document://uploads/", "")
            file_path = self.uploads_dir / relative_path
            
            if not file_path.exists():
                raise FileNotFoundError(f"Document not found: {uri}")
            
            mime_type = self._get_mime_type(file_path)
            
            # Text files
            if mime_type.startswith("text/") or mime_type in ["application/json", "application/xml"]:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                return MCPResourceContent(uri=uri, mimeType=mime_type, text=content)
            
            # Binary files (PDF, images, etc.)
            content = base64.b64encode(file_path.read_bytes()).decode("utf-8")
            return MCPResourceContent(uri=uri, mimeType=mime_type, blob=content)
        
        elif uri.startswith("document://indexed/"):
            # Read indexed chunks
            source = uri.replace("document://indexed/", "")
            
            if self.vector_store:
                # Get all chunks for this source
                all_data = self.vector_store.collection.get(
                    where={"source": source},
                    include=["documents", "metadatas"]
                )
                
                chunks_text = []
                for i, doc in enumerate(all_data.get("documents", [])):
                    meta = all_data.get("metadatas", [])[i] if all_data.get("metadatas") else {}
                    page = meta.get("page_number", "?")
                    chunks_text.append(f"[Chunk {i+1}, Page {page}]\n{doc}\n")
                
                return MCPResourceContent(
                    uri=uri,
                    mimeType="text/plain",
                    text="\n---\n".join(chunks_text)
                )
        
        raise FileNotFoundError(f"Resource not found: {uri}")
    
    def _get_mime_type(self, path: Path) -> str:
        """Get MIME type from file extension"""
        mime_map = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".html": "text/html",
            ".xml": "application/xml",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
        }
        return mime_map.get(path.suffix.lower(), "application/octet-stream")


class SessionResourceProvider(MCPResourceProvider):
    """
    Session Resource Provider
    
    Exposes chat sessions and conversation history.
    """
    
    def __init__(self, session_manager=None):
        self.session_manager = session_manager
        self.sessions_dir = settings.DATA_DIR / "sessions"
    
    async def list_resources(self) -> List[MCPResource]:
        """List all session resources"""
        resources = []
        
        if self.sessions_dir.exists():
            for file_path in self.sessions_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    session_id = file_path.stem
                    title = data.get("title", "Untitled Session")
                    msg_count = len(data.get("messages", []))
                    created = data.get("created_at", "")[:10]
                    
                    resources.append(MCPResource(
                        uri=f"session://{session_id}",
                        name=f"{title} ({created})",
                        description=f"Chat session with {msg_count} messages",
                        mimeType="application/json",
                        annotations={
                            "message_count": msg_count,
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at")
                        }
                    ))
                except Exception:
                    continue
        
        return resources
    
    async def read_resource(self, uri: str) -> MCPResourceContent:
        """Read session content"""
        if not uri.startswith("session://"):
            raise FileNotFoundError(f"Invalid session URI: {uri}")
        
        session_id = uri.replace("session://", "")
        file_path = self.sessions_dir / f"{session_id}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")
        
        content = file_path.read_text(encoding="utf-8")
        return MCPResourceContent(uri=uri, mimeType="application/json", text=content)


class NotesResourceProvider(MCPResourceProvider):
    """
    Notes Resource Provider
    
    Exposes user notes as MCP resources.
    """
    
    def __init__(self):
        self.notes_dir = settings.DATA_DIR / "notes"
    
    async def list_resources(self) -> List[MCPResource]:
        """List all notes"""
        resources = []
        notes_file = self.notes_dir / "notes.json"
        
        if notes_file.exists():
            try:
                with open(notes_file, "r", encoding="utf-8") as f:
                    notes_data = json.load(f)
                
                for note_id, note in notes_data.items():
                    resources.append(MCPResource(
                        uri=f"note://{note_id}",
                        name=note.get("title", "Untitled"),
                        description=note.get("content", "")[:100] + "...",
                        mimeType="text/markdown",
                        annotations={
                            "color": note.get("color"),
                            "tags": note.get("tags", []),
                            "pinned": note.get("pinned", False),
                            "created_at": note.get("created_at"),
                            "updated_at": note.get("updated_at")
                        }
                    ))
            except Exception:
                pass
        
        return resources
    
    async def read_resource(self, uri: str) -> MCPResourceContent:
        """Read note content"""
        if not uri.startswith("note://"):
            raise FileNotFoundError(f"Invalid note URI: {uri}")
        
        note_id = uri.replace("note://", "")
        notes_file = self.notes_dir / "notes.json"
        
        if notes_file.exists():
            with open(notes_file, "r", encoding="utf-8") as f:
                notes_data = json.load(f)
            
            if note_id in notes_data:
                note = notes_data[note_id]
                content = f"# {note.get('title', 'Untitled')}\n\n{note.get('content', '')}"
                return MCPResourceContent(uri=uri, mimeType="text/markdown", text=content)
        
        raise FileNotFoundError(f"Note not found: {note_id}")


# ============ TOOL PROVIDERS ============

class CoreToolProvider(MCPToolProvider):
    """
    Core Tool Provider
    
    Provides essential tools: calculator, time, file info, etc.
    """
    
    def get_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="calculator",
                description="Evaluate mathematical expressions. Supports basic arithmetic, powers, roots, and common math functions.",
                inputSchema=MCPToolInput(
                    properties={
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3', 'sqrt(16)', '2**10')"
                        }
                    },
                    required=["expression"]
                )
            ),
            MCPTool(
                name="get_current_time",
                description="Get the current date and time",
                inputSchema=MCPToolInput(
                    properties={
                        "timezone": {
                            "type": "string",
                            "description": "Timezone (default: local)",
                            "default": "local"
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format: 'iso', 'human', 'date', 'time'",
                            "default": "iso"
                        }
                    }
                )
            ),
            MCPTool(
                name="get_file_info",
                description="Get information about a file (size, modified date, etc.)",
                inputSchema=MCPToolInput(
                    properties={
                        "path": {
                            "type": "string",
                            "description": "File path to inspect"
                        }
                    },
                    required=["path"]
                )
            ),
            MCPTool(
                name="list_directory",
                description="List contents of a directory",
                inputSchema=MCPToolInput(
                    properties={
                        "path": {
                            "type": "string",
                            "description": "Directory path to list"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to filter (e.g., '*.py')",
                            "default": "*"
                        }
                    },
                    required=["path"]
                )
            ),
            MCPTool(
                name="read_file",
                description="Read text content from a file",
                inputSchema=MCPToolInput(
                    properties={
                        "path": {
                            "type": "string",
                            "description": "File path to read"
                        },
                        "encoding": {
                            "type": "string",
                            "description": "Text encoding",
                            "default": "utf-8"
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": "Maximum characters to read",
                            "default": 10000
                        }
                    },
                    required=["path"]
                )
            ),
            MCPTool(
                name="write_file",
                description="Write text content to a file",
                inputSchema=MCPToolInput(
                    properties={
                        "path": {
                            "type": "string",
                            "description": "File path to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write"
                        },
                        "mode": {
                            "type": "string",
                            "description": "Write mode: 'overwrite' or 'append'",
                            "default": "overwrite"
                        }
                    },
                    required=["path", "content"]
                )
            ),
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute a core tool"""
        try:
            if name == "calculator":
                return await self._calculator(arguments)
            elif name == "get_current_time":
                return await self._get_current_time(arguments)
            elif name == "get_file_info":
                return await self._get_file_info(arguments)
            elif name == "list_directory":
                return await self._list_directory(arguments)
            elif name == "read_file":
                return await self._read_file(arguments)
            elif name == "write_file":
                return await self._write_file(arguments)
            else:
                return MCPToolResult(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    isError=True
                )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _calculator(self, args: Dict) -> MCPToolResult:
        """Calculator implementation"""
        import math
        expression = args.get("expression", "")
        
        # Safe evaluation with math functions
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "pow": pow, "sqrt": math.sqrt, "log": math.log,
            "log10": math.log10, "sin": math.sin, "cos": math.cos,
            "tan": math.tan, "pi": math.pi, "e": math.e,
            "ceil": math.ceil, "floor": math.floor
        }
        
        # Clean expression
        expr_clean = expression.replace("^", "**")
        
        try:
            result = eval(expr_clean, {"__builtins__": {}}, allowed_names)
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Result: {result}\nExpression: {expression}"
                }]
            )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Calculation error: {e}"}],
                isError=True
            )
    
    async def _get_current_time(self, args: Dict) -> MCPToolResult:
        """Get current time"""
        from datetime import datetime
        
        now = datetime.now()
        fmt = args.get("format", "iso")
        
        if fmt == "iso":
            time_str = now.isoformat()
        elif fmt == "human":
            time_str = now.strftime("%d %B %Y, %H:%M:%S")
        elif fmt == "date":
            time_str = now.strftime("%Y-%m-%d")
        elif fmt == "time":
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.isoformat()
        
        return MCPToolResult(
            content=[{
                "type": "text",
                "text": f"Current time: {time_str}"
            }]
        )
    
    async def _get_file_info(self, args: Dict) -> MCPToolResult:
        """Get file information"""
        from pathlib import Path
        from datetime import datetime
        
        path = Path(args.get("path", ""))
        
        if not path.exists():
            return MCPToolResult(
                content=[{"type": "text", "text": f"File not found: {path}"}],
                isError=True
            )
        
        stat = path.stat()
        info = {
            "name": path.name,
            "path": str(path.absolute()),
            "size_bytes": stat.st_size,
            "size_human": self._format_size(stat.st_size),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "extension": path.suffix,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
        
        return MCPToolResult(
            content=[{"type": "text", "text": json.dumps(info, indent=2)}]
        )
    
    async def _list_directory(self, args: Dict) -> MCPToolResult:
        """List directory contents"""
        from pathlib import Path
        
        path = Path(args.get("path", "."))
        pattern = args.get("pattern", "*")
        
        if not path.exists():
            return MCPToolResult(
                content=[{"type": "text", "text": f"Directory not found: {path}"}],
                isError=True
            )
        
        items = []
        for item in path.glob(pattern):
            item_type = "📁" if item.is_dir() else "📄"
            size = self._format_size(item.stat().st_size) if item.is_file() else ""
            items.append(f"{item_type} {item.name} {size}")
        
        return MCPToolResult(
            content=[{
                "type": "text",
                "text": f"Contents of {path}:\n\n" + "\n".join(items[:100])
            }]
        )
    
    async def _read_file(self, args: Dict) -> MCPToolResult:
        """Read file content"""
        from pathlib import Path
        
        path = Path(args.get("path", ""))
        encoding = args.get("encoding", "utf-8")
        max_chars = args.get("max_chars", 10000)
        
        if not path.exists():
            return MCPToolResult(
                content=[{"type": "text", "text": f"File not found: {path}"}],
                isError=True
            )
        
        try:
            content = path.read_text(encoding=encoding, errors="ignore")
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n... [Truncated, {len(content) - max_chars} more chars]"
            
            return MCPToolResult(
                content=[{"type": "text", "text": content}]
            )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Read error: {e}"}],
                isError=True
            )
    
    async def _write_file(self, args: Dict) -> MCPToolResult:
        """Write file content"""
        from pathlib import Path
        
        path = Path(args.get("path", ""))
        content = args.get("content", "")
        mode = args.get("mode", "overwrite")
        
        # Safety check - only allow writing in data directory
        data_dir = settings.DATA_DIR
        if not str(path.absolute()).startswith(str(data_dir)):
            return MCPToolResult(
                content=[{"type": "text", "text": "Security: Can only write to data directory"}],
                isError=True
            )
        
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if mode == "append":
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.write_text(content, encoding="utf-8")
            
            return MCPToolResult(
                content=[{"type": "text", "text": f"Successfully wrote {len(content)} chars to {path}"}]
            )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Write error: {e}"}],
                isError=True
            )
    
    def _format_size(self, size: int) -> str:
        """Format file size"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class RAGToolProvider(MCPToolProvider):
    """
    RAG Tool Provider
    
    Provides RAG-related tools: search, query, document management.
    """
    
    def __init__(self, vector_store=None, retriever=None):
        self.vector_store = vector_store
        self.retriever = retriever
    
    def get_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="rag_search",
                description="Search the knowledge base using semantic search. Returns relevant document chunks.",
                inputSchema=MCPToolInput(
                    properties={
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return",
                            "default": 5
                        },
                        "source_filter": {
                            "type": "string",
                            "description": "Filter by source document name (optional)"
                        },
                        "score_threshold": {
                            "type": "number",
                            "description": "Minimum relevance score (0-1)",
                            "default": 0.3
                        }
                    },
                    required=["query"]
                )
            ),
            MCPTool(
                name="rag_get_sources",
                description="List all indexed document sources in the knowledge base",
                inputSchema=MCPToolInput(properties={})
            ),
            MCPTool(
                name="rag_get_stats",
                description="Get statistics about the knowledge base",
                inputSchema=MCPToolInput(properties={})
            ),
            MCPTool(
                name="rag_query_with_context",
                description="Get formatted context for a query (ready for LLM)",
                inputSchema=MCPToolInput(
                    properties={
                        "query": {
                            "type": "string",
                            "description": "Query to get context for"
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum context tokens",
                            "default": 4000
                        }
                    },
                    required=["query"]
                )
            ),
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute a RAG tool"""
        try:
            if name == "rag_search":
                return await self._search(arguments)
            elif name == "rag_get_sources":
                return await self._get_sources(arguments)
            elif name == "rag_get_stats":
                return await self._get_stats(arguments)
            elif name == "rag_query_with_context":
                return await self._query_with_context(arguments)
            else:
                return MCPToolResult(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    isError=True
                )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"RAG Error: {str(e)}"}],
                isError=True
            )
    
    async def _search(self, args: Dict) -> MCPToolResult:
        """Search knowledge base"""
        if not self.vector_store:
            return MCPToolResult(
                content=[{"type": "text", "text": "Vector store not initialized"}],
                isError=True
            )
        
        query = args.get("query", "")
        top_k = args.get("top_k", 5)
        score_threshold = args.get("score_threshold", 0.3)
        source_filter = args.get("source_filter")
        
        # Build filter
        where_filter = None
        if source_filter:
            where_filter = {"source": source_filter}
        
        results = self.vector_store.search_with_scores(
            query=query,
            n_results=top_k,
            score_threshold=score_threshold,
            where=where_filter
        )
        
        if not results:
            return MCPToolResult(
                content=[{"type": "text", "text": f"No results found for: {query}"}]
            )
        
        # Format results
        output_parts = [f"Found {len(results)} results for: {query}\n"]
        
        for i, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source", "Unknown")
            page = result.get("metadata", {}).get("page_number", "?")
            score = result.get("score", 0)
            content = result.get("document", "")[:500]
            
            output_parts.append(f"\n[{i}] Source: {source} (Page {page})")
            output_parts.append(f"    Score: {score:.3f}")
            output_parts.append(f"    Content: {content}...")
        
        return MCPToolResult(
            content=[{"type": "text", "text": "\n".join(output_parts)}]
        )
    
    async def _get_sources(self, args: Dict) -> MCPToolResult:
        """Get all sources"""
        if not self.vector_store:
            return MCPToolResult(
                content=[{"type": "text", "text": "Vector store not initialized"}],
                isError=True
            )
        
        sources = self.vector_store.get_unique_sources()
        
        output = "Indexed Sources:\n\n"
        for i, source in enumerate(sources, 1):
            output += f"{i}. {source}\n"
        
        if not sources:
            output = "No documents indexed yet."
        
        return MCPToolResult(content=[{"type": "text", "text": output}])
    
    async def _get_stats(self, args: Dict) -> MCPToolResult:
        """Get knowledge base stats"""
        if not self.vector_store:
            return MCPToolResult(
                content=[{"type": "text", "text": "Vector store not initialized"}],
                isError=True
            )
        
        stats = self.vector_store.get_document_stats()
        
        return MCPToolResult(
            content=[{"type": "text", "text": json.dumps(stats, indent=2)}]
        )
    
    async def _query_with_context(self, args: Dict) -> MCPToolResult:
        """Get formatted context for LLM"""
        if not self.retriever:
            return MCPToolResult(
                content=[{"type": "text", "text": "Retriever not initialized"}],
                isError=True
            )
        
        query = args.get("query", "")
        max_tokens = args.get("max_tokens", 4000)
        
        # Rough char estimate (4 chars ≈ 1 token)
        max_chars = max_tokens * 4
        
        context = self.retriever.retrieve_with_context(
            query=query,
            max_context_length=max_chars
        )
        
        if not context:
            return MCPToolResult(
                content=[{"type": "text", "text": f"No context found for: {query}"}]
            )
        
        return MCPToolResult(content=[{"type": "text", "text": context}])


class WebSearchToolProvider(MCPToolProvider):
    """
    Web Search Tool Provider
    
    Provides web search capabilities.
    """
    
    def __init__(self, search_engine=None):
        self.search_engine = search_engine
    
    def get_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="web_search",
                description="Search the web for information. Returns search results with titles, URLs, and snippets.",
                inputSchema=MCPToolInput(
                    properties={
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results",
                            "default": 5
                        },
                        "include_content": {
                            "type": "boolean",
                            "description": "Extract full page content",
                            "default": False
                        }
                    },
                    required=["query"]
                )
            ),
            MCPTool(
                name="fetch_webpage",
                description="Fetch and extract content from a specific webpage",
                inputSchema=MCPToolInput(
                    properties={
                        "url": {
                            "type": "string",
                            "description": "URL to fetch"
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": "Maximum characters to extract",
                            "default": 10000
                        }
                    },
                    required=["url"]
                )
            ),
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute web search tool"""
        try:
            if name == "web_search":
                return await self._web_search(arguments)
            elif name == "fetch_webpage":
                return await self._fetch_webpage(arguments)
            else:
                return MCPToolResult(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    isError=True
                )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Web Error: {str(e)}"}],
                isError=True
            )
    
    async def _web_search(self, args: Dict) -> MCPToolResult:
        """Perform web search"""
        if not self.search_engine:
            # Fallback to basic search
            return MCPToolResult(
                content=[{"type": "text", "text": "Web search engine not configured"}],
                isError=True
            )
        
        query = args.get("query", "")
        num_results = args.get("num_results", 5)
        include_content = args.get("include_content", False)
        
        response = self.search_engine.search(
            query=query,
            num_results=num_results,
            extract_content=include_content
        )
        
        if not response.success:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Search failed: {response.error_message}"}],
                isError=True
            )
        
        # Format results
        output_parts = [f"Web search results for: {query}\n"]
        
        if response.instant_answer:
            ia = response.instant_answer
            output_parts.append(f"\n📌 Quick Answer: {ia.get('title', '')}")
            output_parts.append(f"{ia.get('abstract', '')[:300]}\n")
        
        for i, result in enumerate(response.results, 1):
            output_parts.append(f"\n[{i}] {result.title}")
            output_parts.append(f"    URL: {result.url}")
            output_parts.append(f"    {result.snippet[:200]}...")
            
            if include_content and result.full_content:
                output_parts.append(f"\n    Content: {result.full_content[:500]}...")
        
        return MCPToolResult(
            content=[{"type": "text", "text": "\n".join(output_parts)}]
        )
    
    async def _fetch_webpage(self, args: Dict) -> MCPToolResult:
        """Fetch webpage content"""
        import httpx
        from bs4 import BeautifulSoup
        
        url = args.get("url", "")
        max_chars = args.get("max_chars", 10000)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=15, follow_redirects=True)
                response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            
            # Get text
            text = soup.get_text(separator="\n", strip=True)
            
            # Truncate
            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... [Truncated]"
            
            # Get title
            title = soup.find("title")
            title_text = title.get_text() if title else url
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"# {title_text}\n\nURL: {url}\n\n{text}"
                }]
            )
            
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Fetch error: {e}"}],
                isError=True
            )


# ============ PROMPT PROVIDERS ============

class SystemPromptProvider(MCPPromptProvider):
    """
    System Prompt Provider
    
    Provides reusable prompt templates for different tasks.
    """
    
    def __init__(self):
        self._prompts = {
            "rag_qa": {
                "description": "Answer questions based on provided context from knowledge base",
                "arguments": [
                    MCPPromptArgument("query", "User's question", required=True),
                    MCPPromptArgument("context", "Retrieved context from RAG", required=True),
                    MCPPromptArgument("language", "Response language (tr/en)", required=False),
                ],
                "template": self._rag_qa_template
            },
            "summarize": {
                "description": "Summarize a document or text",
                "arguments": [
                    MCPPromptArgument("text", "Text to summarize", required=True),
                    MCPPromptArgument("style", "Summary style: bullet/paragraph/tldr", required=False),
                    MCPPromptArgument("max_length", "Maximum summary length", required=False),
                ],
                "template": self._summarize_template
            },
            "analyze": {
                "description": "Analyze and extract insights from data or text",
                "arguments": [
                    MCPPromptArgument("content", "Content to analyze", required=True),
                    MCPPromptArgument("focus", "What to focus on in analysis", required=False),
                ],
                "template": self._analyze_template
            },
            "code_review": {
                "description": "Review code and provide feedback",
                "arguments": [
                    MCPPromptArgument("code", "Code to review", required=True),
                    MCPPromptArgument("language", "Programming language", required=False),
                    MCPPromptArgument("focus", "Review focus: security/performance/style", required=False),
                ],
                "template": self._code_review_template
            },
            "creative_write": {
                "description": "Generate creative content",
                "arguments": [
                    MCPPromptArgument("topic", "Topic or theme", required=True),
                    MCPPromptArgument("style", "Writing style", required=False),
                    MCPPromptArgument("format", "Output format: article/story/poem", required=False),
                ],
                "template": self._creative_write_template
            },
            "translate": {
                "description": "Translate text between languages",
                "arguments": [
                    MCPPromptArgument("text", "Text to translate", required=True),
                    MCPPromptArgument("source_lang", "Source language", required=False),
                    MCPPromptArgument("target_lang", "Target language", required=True),
                ],
                "template": self._translate_template
            },
        }
    
    def get_prompts(self) -> List[MCPPrompt]:
        return [
            MCPPrompt(
                name=name,
                description=data["description"],
                arguments=data["arguments"]
            )
            for name, data in self._prompts.items()
        ]
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> List[MCPPromptMessage]:
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        template_fn = self._prompts[name]["template"]
        return template_fn(arguments)
    
    def _rag_qa_template(self, args: Dict) -> List[MCPPromptMessage]:
        query = args.get("query", "")
        context = args.get("context", "")
        language = args.get("language", "tr")
        
        lang_instruction = "Türkçe yanıt ver." if language == "tr" else "Respond in English."
        
        system_content = f"""Sen yardımcı bir asistansın. Kullanıcının sorularını SADECE verilen bağlam (context) bilgisine dayanarak yanıtla.

Kurallar:
1. Yanıtını YALNIZCA verilen bağlamdaki bilgilere dayandır
2. Bağlamda olmayan bilgileri UYDURMA
3. Emin olmadığın konularda "Bu bilgi verilen kaynaklarda bulunmuyor" de
4. Kaynakları referans göster (örn: [Kaynak 1], [Kaynak 2])
5. {lang_instruction}

BAĞLAM:
{context}
"""
        
        return [
            MCPPromptMessage(
                role="user",
                content={"type": "text", "text": f"{system_content}\n\nSORU: {query}"}
            )
        ]
    
    def _summarize_template(self, args: Dict) -> List[MCPPromptMessage]:
        text = args.get("text", "")
        style = args.get("style", "paragraph")
        max_length = args.get("max_length", "")
        
        style_instruction = {
            "bullet": "Madde işaretleri kullanarak özetle",
            "paragraph": "Akıcı bir paragraf halinde özetle",
            "tldr": "Tek cümlelik TL;DR formatında özetle"
        }.get(style, "Özetle")
        
        length_instruction = f"Maksimum {max_length} karakter kullan." if max_length else ""
        
        return [
            MCPPromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"{style_instruction}. {length_instruction}\n\nMETİN:\n{text}"
                }
            )
        ]
    
    def _analyze_template(self, args: Dict) -> List[MCPPromptMessage]:
        content = args.get("content", "")
        focus = args.get("focus", "genel")
        
        return [
            MCPPromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""Aşağıdaki içeriği analiz et ve önemli içgörüler çıkar.

Odak alanı: {focus}

Analizinde şunları içer:
1. Ana temalar ve kalıplar
2. Önemli noktalar
3. Potansiyel sorunlar veya fırsatlar
4. Öneriler

İÇERİK:
{content}"""
                }
            )
        ]
    
    def _code_review_template(self, args: Dict) -> List[MCPPromptMessage]:
        code = args.get("code", "")
        language = args.get("language", "")
        focus = args.get("focus", "genel")
        
        lang_hint = f"Programlama dili: {language}" if language else ""
        
        return [
            MCPPromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""Aşağıdaki kodu incele ve detaylı geri bildirim ver.
{lang_hint}
İnceleme odağı: {focus}

Değerlendir:
1. Kod kalitesi ve okunabilirlik
2. Potansiyel hatalar ve edge case'ler
3. Performans iyileştirmeleri
4. Güvenlik endişeleri
5. Best practice önerileri

KOD:
```
{code}
```"""
                }
            )
        ]
    
    def _creative_write_template(self, args: Dict) -> List[MCPPromptMessage]:
        topic = args.get("topic", "")
        style = args.get("style", "profesyonel")
        fmt = args.get("format", "article")
        
        format_instruction = {
            "article": "Blog yazısı formatında yaz",
            "story": "Kısa hikaye formatında yaz",
            "poem": "Şiir formatında yaz"
        }.get(fmt, "Makale formatında yaz")
        
        return [
            MCPPromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""{format_instruction}.

Konu: {topic}
Stil: {style}

Yaratıcı, ilgi çekici ve akıcı bir içerik üret."""
                }
            )
        ]
    
    def _translate_template(self, args: Dict) -> List[MCPPromptMessage]:
        text = args.get("text", "")
        source = args.get("source_lang", "otomatik algıla")
        target = args.get("target_lang", "en")
        
        return [
            MCPPromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""Aşağıdaki metni çevir.

Kaynak dil: {source}
Hedef dil: {target}

Çeviride:
- Anlam bütünlüğünü koru
- Doğal ve akıcı bir dil kullan
- Kültürel nüansları dikkate al

METİN:
{text}"""
                }
            )
        ]


# ============ EXPORTS ============

__all__ = [
    # Resource Providers
    "DocumentResourceProvider",
    "SessionResourceProvider",
    "NotesResourceProvider",
    # Tool Providers
    "CoreToolProvider",
    "RAGToolProvider",
    "WebSearchToolProvider",
    # Prompt Providers
    "SystemPromptProvider",
]
