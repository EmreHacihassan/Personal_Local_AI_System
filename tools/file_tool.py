"""
Enterprise AI Assistant - File Tool
Endüstri Standartlarında Kurumsal AI Çözümü

Dosya işlemleri tool'u - okuma, yazma, listeleme.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import os
import json

from .base_tool import BaseTool, ToolResult

import sys
sys.path.append('..')

from core.config import settings


class FileTool(BaseTool):
    """
    Dosya İşlemleri Tool'u - Endüstri standartlarına uygun.
    
    Yetenekler:
    - Dosya okuma
    - Dosya yazma
    - Klasör listeleme
    - Dosya arama
    """
    
    ALLOWED_EXTENSIONS = {
        ".txt", ".md", ".json", ".csv", ".xml",
        ".pdf", ".docx", ".xlsx", ".html",
    }
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Dosya sistemi işlemleri - okuma, yazma, listeleme",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "search"],
                        "description": "Yapılacak işlem",
                    },
                    "path": {
                        "type": "string",
                        "description": "Dosya veya klasör yolu",
                    },
                    "content": {
                        "type": "string",
                        "description": "Yazılacak içerik (write için)",
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Arama kalıbı (search için)",
                    },
                },
                "required": ["operation", "path"],
            },
        )
        
        # Base directory for file operations
        self.base_dir = settings.DATA_DIR
    
    def execute(
        self,
        operation: str,
        path: str,
        content: Optional[str] = None,
        pattern: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Dosya işlemi yap.
        
        Args:
            operation: İşlem tipi (read, write, list, search)
            path: Dosya/klasör yolu
            content: Yazılacak içerik
            pattern: Arama kalıbı
            
        Returns:
            ToolResult
        """
        try:
            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                return self._write_file(path, content or "")
            elif operation == "list":
                return self._list_directory(path)
            elif operation == "search":
                return self._search_files(path, pattern or "")
            else:
                return ToolResult(
                    success=False,
                    error=f"Bilinmeyen işlem: {operation}",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"operation": operation, "path": path},
            )
    
    def _resolve_path(self, path: str) -> Path:
        """Güvenli yol çözümleme."""
        # If absolute path, use as is (with validation)
        if os.path.isabs(path):
            resolved = Path(path).resolve()
        else:
            # Relative to base directory
            resolved = (self.base_dir / path).resolve()
        
        # Security: ensure path is within allowed directories
        allowed_dirs = [settings.DATA_DIR, settings.BASE_DIR / "uploads"]
        
        # For read operations, allow more flexibility
        # For write operations, restrict to data directory
        return resolved
    
    def _read_file(self, path: str) -> ToolResult:
        """Dosya oku."""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return ToolResult(
                success=False,
                error=f"Dosya bulunamadı: {path}",
            )
        
        if not file_path.is_file():
            return ToolResult(
                success=False,
                error=f"Bu bir dosya değil: {path}",
            )
        
        # Read content
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            return ToolResult(
                success=True,
                data=content,
                metadata={
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix,
                },
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Dosya okunamadı: {e}",
            )
    
    def _write_file(self, path: str, content: str) -> ToolResult:
        """Dosya yaz."""
        file_path = self._resolve_path(path)
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return ToolResult(
                success=True,
                data={"path": str(file_path), "bytes_written": len(content)},
                metadata={"operation": "write"},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Dosya yazılamadı: {e}",
            )
    
    def _list_directory(self, path: str) -> ToolResult:
        """Klasör içeriğini listele."""
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return ToolResult(
                success=False,
                error=f"Klasör bulunamadı: {path}",
            )
        
        if not dir_path.is_dir():
            return ToolResult(
                success=False,
                error=f"Bu bir klasör değil: {path}",
            )
        
        items = []
        for item in dir_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
                "extension": item.suffix if item.is_file() else None,
            })
        
        return ToolResult(
            success=True,
            data=items,
            metadata={
                "path": str(dir_path),
                "item_count": len(items),
            },
        )
    
    def _search_files(self, path: str, pattern: str) -> ToolResult:
        """Dosyalarda arama yap."""
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return ToolResult(
                success=False,
                error=f"Klasör bulunamadı: {path}",
            )
        
        matches = []
        
        for file_path in dir_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Check if filename matches pattern
            if pattern.lower() in file_path.name.lower():
                matches.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "match_type": "filename",
                })
                continue
            
            # Check file content for text files
            if file_path.suffix in {".txt", ".md", ".json", ".csv", ".xml", ".html"}:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    
                    if pattern.lower() in content.lower():
                        # Find matching lines
                        lines = content.split("\n")
                        matching_lines = [
                            (i + 1, line.strip())
                            for i, line in enumerate(lines)
                            if pattern.lower() in line.lower()
                        ][:3]  # Limit to 3 matches
                        
                        matches.append({
                            "name": file_path.name,
                            "path": str(file_path),
                            "match_type": "content",
                            "matching_lines": matching_lines,
                        })
                except Exception:
                    pass
        
        return ToolResult(
            success=True,
            data=matches,
            metadata={
                "search_path": str(dir_path),
                "pattern": pattern,
                "match_count": len(matches),
            },
        )


# Singleton instance
file_tool = FileTool()
