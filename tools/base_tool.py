"""
Enterprise AI Assistant - Base Tool
Endüstri Standartlarında Kurumsal AI Çözümü

Tüm tool'ların temel sınıfı - ortak interface ve yapı.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


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
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters or {}
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Tool'u çalıştır.
        
        Returns:
            ToolResult
        """
        pass
    
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
