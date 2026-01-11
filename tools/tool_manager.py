"""
Tool Manager
============

Araç kayıt, keşif ve çalıştırma yönetimi.
"""

import asyncio
import inspect
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union
import json

from .base_tool import BaseTool, ToolResult


class ToolCategory(Enum):
    """Araç kategorileri"""
    COMPUTATION = "computation"
    SEARCH = "search"
    FILE = "file"
    CODE = "code"
    WEB = "web"
    DATA = "data"
    COMMUNICATION = "communication"
    UTILITY = "utility"


@dataclass
class ToolMetadata:
    """Araç meta verileri"""
    name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    author: str = "system"
    enabled: bool = True
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # calls per minute
    tags: List[str] = field(default_factory=list)


@dataclass
class ToolExecution:
    """Araç çalıştırma kaydı"""
    tool_name: str
    timestamp: datetime
    duration: float
    success: bool
    input_args: Dict[str, Any]
    output: Any
    error: Optional[str] = None


class ToolRegistry:
    """
    Araç kayıt sistemi
    
    Singleton pattern ile tek instance.
    """
    
    _instance: Optional["ToolRegistry"] = None
    
    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._tools: Dict[str, BaseTool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._execution_history: List[ToolExecution] = []
        self._rate_limits: Dict[str, List[datetime]] = {}
        self._initialized = True
    
    def register(
        self,
        tool: BaseTool,
        category: ToolCategory = ToolCategory.UTILITY,
        metadata: Optional[ToolMetadata] = None
    ) -> None:
        """
        Aracı kaydet
        
        Args:
            tool: Araç instance'ı
            category: Araç kategorisi
            metadata: Opsiyonel meta veriler
        """
        if metadata is None:
            metadata = ToolMetadata(
                name=tool.name,
                description=tool.description,
                category=category
            )
        
        self._tools[tool.name] = tool
        self._metadata[tool.name] = metadata
    
    def unregister(self, name: str) -> bool:
        """Aracı kayıttan çıkar"""
        if name in self._tools:
            del self._tools[name]
            del self._metadata[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseTool]:
        """İsme göre araç al"""
        return self._tools.get(name)
    
    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Araç meta verilerini al"""
        return self._metadata.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """Araçları listele"""
        tools = []
        for name, meta in self._metadata.items():
            if category and meta.category != category:
                continue
            if enabled_only and not meta.enabled:
                continue
            tools.append(name)
        return sorted(tools)
    
    def get_all_schemas(self) -> List[Dict]:
        """Tüm araç şemalarını al"""
        schemas = []
        for name, tool in self._tools.items():
            meta = self._metadata.get(name)
            if meta and meta.enabled:
                schemas.append(tool.get_schema())
        return schemas
    
    def _check_rate_limit(self, name: str) -> bool:
        """Rate limit kontrolü"""
        meta = self._metadata.get(name)
        if not meta or not meta.rate_limit:
            return True
        
        now = datetime.now()
        minute_ago = now.replace(second=0, microsecond=0)
        
        # Eski kayıtları temizle
        if name in self._rate_limits:
            self._rate_limits[name] = [
                t for t in self._rate_limits[name]
                if t >= minute_ago
            ]
        else:
            self._rate_limits[name] = []
        
        # Limit kontrolü
        if len(self._rate_limits[name]) >= meta.rate_limit:
            return False
        
        self._rate_limits[name].append(now)
        return True
    
    async def execute(
        self,
        name: str,
        **kwargs
    ) -> ToolResult:
        """
        Aracı çalıştır
        
        Args:
            name: Araç adı
            **kwargs: Araç parametreleri
            
        Returns:
            ToolResult
        """
        import time
        
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Araç bulunamadı: {name}"
            )
        
        meta = self._metadata.get(name)
        if meta and not meta.enabled:
            return ToolResult(
                success=False,
                error=f"Araç devre dışı: {name}"
            )
        
        # Rate limit kontrolü
        if not self._check_rate_limit(name):
            return ToolResult(
                success=False,
                error=f"Rate limit aşıldı: {name}"
            )
        
        # Çalıştır
        start_time = time.time()
        result = await tool.run(**kwargs)
        duration = time.time() - start_time
        
        # Geçmişe kaydet
        execution = ToolExecution(
            tool_name=name,
            timestamp=datetime.now(),
            duration=duration,
            success=result.success,
            input_args=kwargs,
            output=result.data if result.success else None,
            error=result.error
        )
        self._execution_history.append(execution)
        
        # Geçmişi sınırla
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-500:]
        
        return result
    
    def get_history(
        self,
        tool_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ToolExecution]:
        """Çalıştırma geçmişini al"""
        history = self._execution_history
        
        if tool_name:
            history = [e for e in history if e.tool_name == tool_name]
        
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri al"""
        stats = {
            "total_tools": len(self._tools),
            "enabled_tools": sum(1 for m in self._metadata.values() if m.enabled),
            "total_executions": len(self._execution_history),
            "successful_executions": sum(1 for e in self._execution_history if e.success),
            "by_category": {},
            "by_tool": {}
        }
        
        # Kategori bazında
        for meta in self._metadata.values():
            cat = meta.category.value
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        
        # Araç bazında
        for execution in self._execution_history:
            name = execution.tool_name
            if name not in stats["by_tool"]:
                stats["by_tool"][name] = {
                    "total": 0,
                    "success": 0,
                    "avg_duration": 0
                }
            stats["by_tool"][name]["total"] += 1
            if execution.success:
                stats["by_tool"][name]["success"] += 1
            
            # Ortalama süre güncelle
            total = stats["by_tool"][name]["total"]
            avg = stats["by_tool"][name]["avg_duration"]
            stats["by_tool"][name]["avg_duration"] = (
                avg * (total - 1) + execution.duration
            ) / total
        
        return stats


class ToolManager:
    """
    Araç yönetim arayüzü
    
    LLM için araç kullanım desteği sağlar.
    """
    
    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or ToolRegistry()
    
    def register_tool(
        self,
        tool: BaseTool,
        category: ToolCategory = ToolCategory.UTILITY
    ) -> None:
        """Araç kaydet"""
        self.registry.register(tool, category)
    
    def register_function(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: ToolCategory = ToolCategory.UTILITY
    ) -> None:
        """Fonksiyonu araç olarak kaydet"""
        from .base_tool import FunctionTool
        
        tool = FunctionTool(
            func=func,
            name=name or func.__name__,
            description=description or func.__doc__ or ""
        )
        self.register_tool(tool, category)
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Araç al"""
        return self.registry.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[Dict[str, str]]:
        """Araç listesi"""
        tools = []
        for name in self.registry.list_tools(category):
            meta = self.registry.get_metadata(name)
            tools.append({
                "name": name,
                "description": meta.description if meta else "",
                "category": meta.category.value if meta else "utility"
            })
        return tools
    
    def get_schemas_for_llm(self) -> List[Dict]:
        """
        LLM için araç şemalarını al
        
        OpenAI function calling formatında döner.
        """
        return self.registry.get_all_schemas()
    
    async def execute_tool(
        self,
        name: str,
        arguments: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aracı çalıştır
        
        Args:
            name: Araç adı
            arguments: JSON string veya dict olarak argümanlar
            
        Returns:
            Sonuç dictionary
        """
        # JSON string'i parse et
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Geçersiz JSON: {e}"
                }
        
        result = await self.registry.execute(name, **arguments)
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }
    
    async def execute_tool_call(
        self,
        tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        OpenAI tool call formatında çalıştır
        
        Args:
            tool_call: {
                "id": "...",
                "type": "function",
                "function": {
                    "name": "...",
                    "arguments": "..."
                }
            }
            
        Returns:
            Tool mesajı formatında sonuç
        """
        func = tool_call.get("function", {})
        name = func.get("name", "")
        arguments = func.get("arguments", "{}")
        
        result = await self.execute_tool(name, arguments)
        
        return {
            "tool_call_id": tool_call.get("id", ""),
            "role": "tool",
            "content": json.dumps(result, ensure_ascii=False)
        }
    
    def enable_tool(self, name: str) -> bool:
        """Aracı etkinleştir"""
        meta = self.registry.get_metadata(name)
        if meta:
            meta.enabled = True
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """Aracı devre dışı bırak"""
        meta = self.registry.get_metadata(name)
        if meta:
            meta.enabled = False
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri al"""
        return self.registry.get_stats()


# Singleton instances
tool_registry = ToolRegistry()
tool_manager = ToolManager(tool_registry)


def register_default_tools():
    """Varsayılan araçları kaydet"""
    from .calculator_tool import calculator_tool
    from .web_search_tool import web_search_tool
    from .code_executor_tool import code_executor_tool
    from .file_operations_tool import file_operations_tool
    
    tool_manager.register_tool(calculator_tool, ToolCategory.COMPUTATION)
    tool_manager.register_tool(web_search_tool, ToolCategory.WEB)
    tool_manager.register_tool(code_executor_tool, ToolCategory.CODE)
    tool_manager.register_tool(file_operations_tool, ToolCategory.FILE)


# Varsayılan araçları otomatik kaydet
try:
    register_default_tools()
except ImportError:
    pass  # Araçlar henüz yüklenmemiş olabilir
