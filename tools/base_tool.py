"""
Enterprise AI Assistant - Base Tool
Endüstri Standartlarında Kurumsal AI Çözümü

Tüm tool'ların temel sınıfı - ortak interface ve yapı.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import inspect


@dataclass
class ToolResult:
    """Tool çalıştırma sonucu."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class BaseTool(ABC):
    """
    Temel Tool sınıfı - Endüstri standartlarına uygun.
    
    Tüm tool'lar bu sınıftan türer.
    """
    
    name: str = "base_tool"
    description: str = "Base tool"
    
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        if name:
            self.name = name
        if description:
            self.description = description
        self.parameters = parameters or {}
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Tool'u çalıştır (sync).
        
        Returns:
            ToolResult
        """
        pass
    
    async def _run(self, **kwargs) -> Any:
        """
        Async çalıştırma metodu - override edilebilir.
        
        Returns:
            Sonuç verisi
        """
        # Default: sync execute'u çağır
        result = self.execute(**kwargs)
        return result.data if result.success else result.error
    
    async def run(self, **kwargs) -> ToolResult:
        """
        Tool'u async olarak çalıştır.
        
        Returns:
            ToolResult
        """
        try:
            result = await self._run(**kwargs)
            
            if isinstance(result, ToolResult):
                return result
            elif isinstance(result, dict) and "success" in result:
                return ToolResult(
                    success=result.get("success", True),
                    data=result.get("data", result),
                    error=result.get("error"),
                    metadata=result.get("metadata", {})
                )
            else:
                return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def validate_params(self, **kwargs) -> bool:
        """Parametreleri doğrula."""
        required = self.parameters.get("required", [])
        for param in required:
            if param not in kwargs:
                return False
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Tool şemasını döndür (OpenAI function calling formatı)."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class FunctionTool(BaseTool):
    """
    Fonksiyonu tool olarak sarmalayan sınıf.
    
    Herhangi bir fonksiyonu tool'a dönüştürür.
    """
    
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.func = func
        
        # İsim ve açıklama
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Function: {func.__name__}"
        
        super().__init__(
            name=tool_name,
            description=tool_description,
            parameters=parameters or self._infer_parameters()
        )
    
    def _infer_parameters(self) -> Dict[str, Any]:
        """Fonksiyon imzasından parametreleri çıkar."""
        sig = inspect.signature(self.func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            
            param_info = {"type": "string"}  # Default tip
            
            # Type annotation varsa
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_info["type"] = "integer"
                elif param.annotation == float:
                    param_info["type"] = "number"
                elif param.annotation == bool:
                    param_info["type"] = "boolean"
                elif param.annotation == list:
                    param_info["type"] = "array"
                elif param.annotation == dict:
                    param_info["type"] = "object"
            
            properties[param_name] = param_info
            
            # Default değeri yoksa required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def execute(self, **kwargs) -> ToolResult:
        """Fonksiyonu çalıştır."""
        try:
            result = self.func(**kwargs)
            return ToolResult(success=True, data=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    async def _run(self, **kwargs) -> Any:
        """Async çalıştırma."""
        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(**kwargs)
            else:
                return self.func(**kwargs)
        except Exception as e:
            return {"success": False, "error": str(e)}
