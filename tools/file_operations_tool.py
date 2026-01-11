"""
File Operations Tool
====================

Dosya okuma/yazma/listeleme aracı (güvenli).
"""

import asyncio
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .base_tool import BaseTool


class FileOperationsTool(BaseTool):
    """
    Güvenli dosya işlemleri aracı
    
    Özellikler:
    - Dosya okuma
    - Dosya yazma
    - Dizin listeleme
    - Dosya bilgisi
    - Sandbox koruması
    """
    
    name = "file_operations"
    description = "Dosya okuma, yazma ve listeleme işlemleri yapar."
    
    # Yasaklı uzantılar
    FORBIDDEN_EXTENSIONS: Set[str] = {
        ".exe", ".dll", ".so", ".dylib",
        ".bat", ".cmd", ".ps1", ".sh",
        ".env", ".pem", ".key", ".crt",
    }
    
    # Maksimum dosya boyutları
    MAX_READ_SIZE = 1024 * 1024  # 1MB
    MAX_WRITE_SIZE = 512 * 1024  # 512KB
    
    def __init__(
        self,
        base_directory: Optional[str] = None,
        allowed_extensions: Optional[Set[str]] = None,
        read_only: bool = False
    ):
        super().__init__()
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.allowed_extensions = allowed_extensions
        self.read_only = read_only
    
    def _validate_path(self, path: str) -> Path:
        """
        Dosya yolunu doğrula ve güvenli hale getir
        
        - Sandbox dışına çıkmayı engelle
        - Yasaklı uzantıları kontrol et
        """
        # Mutlak yol oluştur
        full_path = (self.base_directory / path).resolve()
        
        # Sandbox kontrolü
        try:
            full_path.relative_to(self.base_directory.resolve())
        except ValueError:
            raise PermissionError(f"Erişim engellendi: {path} (sandbox dışı)")
        
        # Uzantı kontrolü
        ext = full_path.suffix.lower()
        if ext in self.FORBIDDEN_EXTENSIONS:
            raise PermissionError(f"Yasaklı dosya türü: {ext}")
        
        if self.allowed_extensions and ext not in self.allowed_extensions:
            raise PermissionError(f"İzin verilmeyen dosya türü: {ext}")
        
        return full_path
    
    async def _read_file(self, path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """Dosya oku"""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"Dosya bulunamadı: {path}"
                }
            
            if not file_path.is_file():
                return {
                    "success": False,
                    "error": f"Bu bir dosya değil: {path}"
                }
            
            # Boyut kontrolü
            size = file_path.stat().st_size
            if size > self.MAX_READ_SIZE:
                return {
                    "success": False,
                    "error": f"Dosya çok büyük: {size} bytes (max: {self.MAX_READ_SIZE})"
                }
            
            # Dosyayı oku
            content = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: file_path.read_text(encoding=encoding)
            )
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.base_directory)),
                "content": content,
                "size": size,
                "encoding": encoding
            }
        
        except PermissionError as e:
            return {"success": False, "error": str(e)}
        except UnicodeDecodeError:
            return {
                "success": False,
                "error": f"Dosya okunamadı (encoding hatası): {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Dosya yaz"""
        if self.read_only:
            return {
                "success": False,
                "error": "Yazma işlemi devre dışı (read-only mod)"
            }
        
        try:
            file_path = self._validate_path(path)
            
            # Boyut kontrolü
            content_size = len(content.encode(encoding))
            if content_size > self.MAX_WRITE_SIZE:
                return {
                    "success": False,
                    "error": f"İçerik çok büyük: {content_size} bytes (max: {self.MAX_WRITE_SIZE})"
                }
            
            # Var olan dosya kontrolü
            if file_path.exists() and not overwrite:
                return {
                    "success": False,
                    "error": f"Dosya zaten var: {path}. Üzerine yazmak için overwrite=True kullanın."
                }
            
            # Dizini oluştur
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Dosyayı yaz
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: file_path.write_text(content, encoding=encoding)
            )
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.base_directory)),
                "size": content_size,
                "encoding": encoding,
                "created": not file_path.exists(),
                "overwritten": file_path.exists()
            }
        
        except PermissionError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_directory(
        self,
        path: str = ".",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dizin içeriğini listele"""
        try:
            dir_path = self._validate_path(path)
            
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Dizin bulunamadı: {path}"
                }
            
            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"Bu bir dizin değil: {path}"
                }
            
            items = []
            
            if recursive:
                iterator = dir_path.rglob(pattern or "*")
            else:
                iterator = dir_path.glob(pattern or "*")
            
            for item in iterator:
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "path": str(item.relative_to(self.base_directory)),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception:
                    continue
            
            return {
                "success": True,
                "path": str(dir_path.relative_to(self.base_directory)),
                "items": sorted(items, key=lambda x: (x["type"] != "directory", x["name"])),
                "total_items": len(items)
            }
        
        except PermissionError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _file_info(self, path: str) -> Dict[str, Any]:
        """Dosya bilgilerini al"""
        try:
            file_path = self._validate_path(path)
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"Dosya bulunamadı: {path}"
                }
            
            stat = file_path.stat()
            
            return {
                "success": True,
                "path": str(file_path.relative_to(self.base_directory)),
                "name": file_path.name,
                "extension": file_path.suffix,
                "type": "directory" if file_path.is_dir() else "file",
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_hidden": file_path.name.startswith("."),
                "parent": str(file_path.parent.relative_to(self.base_directory))
            }
        
        except PermissionError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _run(
        self,
        operation: str,
        path: str = ".",
        content: Optional[str] = None,
        encoding: str = "utf-8",
        overwrite: bool = False,
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dosya işlemi yap
        
        Args:
            operation: İşlem tipi (read, write, list, info)
            path: Dosya/dizin yolu
            content: Yazılacak içerik (write için)
            encoding: Karakter kodlaması
            overwrite: Üzerine yazma izni
            recursive: Özyinelemeli listeleme
            pattern: Dosya deseni (glob)
            
        Returns:
            İşlem sonucu
        """
        operations = {
            "read": lambda: self._read_file(path, encoding),
            "write": lambda: self._write_file(path, content or "", encoding, overwrite),
            "list": lambda: self._list_directory(path, recursive, pattern),
            "info": lambda: self._file_info(path)
        }
        
        if operation not in operations:
            return {
                "success": False,
                "error": f"Geçersiz işlem: {operation}. Geçerli: {list(operations.keys())}"
            }
        
        return await operations[operation]()
    
    def execute(self, **kwargs) -> "ToolResult":
        """Sync execute metodu."""
        import asyncio
        from .base_tool import ToolResult
        
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._run(**kwargs))
            return ToolResult(success=result.get("success", False), data=result)
        finally:
            loop.close()
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["read", "write", "list", "info"],
                        "description": "İşlem tipi"
                    },
                    "path": {
                        "type": "string",
                        "description": "Dosya veya dizin yolu"
                    },
                    "content": {
                        "type": "string",
                        "description": "Yazılacak içerik (write için)"
                    },
                    "encoding": {
                        "type": "string",
                        "default": "utf-8",
                        "description": "Karakter kodlaması"
                    },
                    "overwrite": {
                        "type": "boolean",
                        "default": False,
                        "description": "Var olan dosyanın üzerine yaz"
                    },
                    "recursive": {
                        "type": "boolean",
                        "default": False,
                        "description": "Özyinelemeli listeleme"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Dosya deseni (örn: *.txt)"
                    }
                },
                "required": ["operation"]
            }
        }


# Tool instance - lazy initialization
file_operations_tool = None

def get_file_operations_tool():
    global file_operations_tool
    if file_operations_tool is None:
        file_operations_tool = FileOperationsTool()
    return file_operations_tool
