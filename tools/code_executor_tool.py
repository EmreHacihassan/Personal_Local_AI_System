"""
Code Executor Tool
==================

Python kodunu güvenli sandbox ortamında çalıştıran araç.
"""

import ast
import asyncio
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import copy

from .base_tool import BaseTool


@dataclass
class ExecutionResult:
    """Kod çalıştırma sonucu"""
    success: bool
    output: str
    error: Optional[str]
    return_value: Any
    execution_time: float
    variables: Dict[str, Any]


class SafetyAnalyzer:
    """
    Kod güvenlik analizörü
    
    Tehlikeli operasyonları tespit eder:
    - Dosya sistemi erişimi
    - Ağ erişimi
    - Sistem komutları
    - Modül importları
    """
    
    # Yasak modüller
    FORBIDDEN_MODULES: Set[str] = {
        "os", "sys", "subprocess", "shutil", "pathlib",
        "socket", "urllib", "requests", "httpx", "aiohttp",
        "pickle", "shelve", "marshal",
        "ctypes", "multiprocessing", "threading",
        "importlib", "__import__", "exec", "eval", "compile",
        "open", "input", "breakpoint",
    }
    
    # Yasak fonksiyonlar
    FORBIDDEN_FUNCTIONS: Set[str] = {
        "exec", "eval", "compile", "open", "input",
        "__import__", "breakpoint", "exit", "quit",
        "globals", "locals", "vars", "dir",
        "getattr", "setattr", "delattr", "hasattr",
    }
    
    # Yasak attribute'lar
    FORBIDDEN_ATTRIBUTES: Set[str] = {
        "__class__", "__bases__", "__subclasses__",
        "__mro__", "__code__", "__globals__",
        "__builtins__", "__dict__", "__module__",
    }
    
    def __init__(self, allow_imports: bool = False):
        self.allow_imports = allow_imports
        self.violations: List[str] = []
    
    def analyze(self, code: str) -> bool:
        """
        Kodu analiz et ve güvenli olup olmadığını kontrol et
        
        Returns:
            True eğer kod güvenliyse
        """
        self.violations = []
        
        try:
            tree = ast.parse(code)
            self._visit(tree)
            return len(self.violations) == 0
        except SyntaxError as e:
            self.violations.append(f"Sözdizimi hatası: {e}")
            return False
    
    def _visit(self, node: ast.AST):
        """AST node'unu ziyaret et"""
        # Import kontrolü
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if not self.allow_imports:
                self.violations.append("Import ifadeleri devre dışı")
            else:
                module_name = ""
                if isinstance(node, ast.Import):
                    module_name = node.names[0].name.split(".")[0]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    module_name = node.module.split(".")[0]
                
                if module_name in self.FORBIDDEN_MODULES:
                    self.violations.append(f"Yasaklı modül: {module_name}")
        
        # Fonksiyon çağrısı kontrolü
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.FORBIDDEN_FUNCTIONS:
                    self.violations.append(f"Yasaklı fonksiyon: {func_name}")
        
        # Attribute erişimi kontrolü
        elif isinstance(node, ast.Attribute):
            if node.attr in self.FORBIDDEN_ATTRIBUTES:
                self.violations.append(f"Yasaklı attribute: {node.attr}")
        
        # Child node'ları ziyaret et
        for child in ast.iter_child_nodes(node):
            self._visit(child)


class SandboxNamespace:
    """
    Güvenli sandbox namespace
    
    Sadece güvenli built-in fonksiyonlara izin verir.
    """
    
    # İzin verilen built-in fonksiyonlar
    SAFE_BUILTINS = {
        # Tipler
        "bool", "int", "float", "str", "bytes", "bytearray",
        "list", "tuple", "dict", "set", "frozenset",
        "complex", "range", "slice", "type",
        
        # Fonksiyonlar
        "abs", "all", "any", "ascii", "bin", "callable",
        "chr", "divmod", "enumerate", "filter", "format",
        "hash", "hex", "id", "isinstance", "issubclass",
        "iter", "len", "map", "max", "min", "next",
        "oct", "ord", "pow", "print", "repr", "reversed",
        "round", "sorted", "sum", "zip",
        
        # Exceptions
        "Exception", "ValueError", "TypeError", "KeyError",
        "IndexError", "AttributeError", "RuntimeError",
        "StopIteration", "ZeroDivisionError",
        
        # Constants
        "True", "False", "None",
    }
    
    @classmethod
    def create(cls, extra_globals: Optional[Dict] = None) -> Dict[str, Any]:
        """Güvenli namespace oluştur"""
        import builtins
        
        safe_builtins = {
            name: getattr(builtins, name)
            for name in cls.SAFE_BUILTINS
            if hasattr(builtins, name)
        }
        
        namespace = {
            "__builtins__": safe_builtins,
            "__name__": "__sandbox__",
            "__doc__": None,
        }
        
        # Matematiksel fonksiyonlar ekle
        import math
        namespace["math"] = math
        
        # Ek global'ler
        if extra_globals:
            namespace.update(extra_globals)
        
        return namespace


class CodeExecutorTool(BaseTool):
    """
    Python kod çalıştırıcı aracı
    
    Özellikler:
    - Güvenlik analizi
    - Sandbox ortamı
    - Zaman aşımı koruması
    - Çıktı yakalama
    """
    
    name = "code_executor"
    description = "Python kodunu güvenli bir ortamda çalıştırır ve sonucu döndürür."
    
    def __init__(
        self,
        timeout: float = 5.0,
        max_output_length: int = 10000,
        allow_imports: bool = False
    ):
        super().__init__()
        self.timeout = timeout
        self.max_output_length = max_output_length
        self.allow_imports = allow_imports
        self.analyzer = SafetyAnalyzer(allow_imports=allow_imports)
    
    def _execute_code(
        self,
        code: str,
        namespace: Dict[str, Any]
    ) -> ExecutionResult:
        """Kodu çalıştır ve sonucu döndür"""
        import time
        
        start_time = time.time()
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        return_value = None
        error = None
        
        try:
            # stdout ve stderr'i yakala
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Kodu derle
                compiled = compile(code, "<sandbox>", "exec")
                
                # Çalıştır
                exec(compiled, namespace)
                
                # Son ifadeyi değerlendir
                tree = ast.parse(code)
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    last_expr = ast.Expression(body=tree.body[-1].value)
                    compiled_expr = compile(last_expr, "<sandbox>", "eval")
                    return_value = eval(compiled_expr, namespace)
        
        except Exception as e:
            error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        
        execution_time = time.time() - start_time
        
        # Çıktıyı al
        output = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()
        
        if stderr:
            output += f"\n[STDERR]:\n{stderr}"
        
        # Çıktıyı kısalt
        if len(output) > self.max_output_length:
            output = output[:self.max_output_length] + "\n... (çıktı kesildi)"
        
        # Değişkenleri topla (sadece güvenli olanları)
        variables = {}
        for name, value in namespace.items():
            if not name.startswith("_") and name not in ["math", "__builtins__"]:
                try:
                    # Basit tipleri kopyala
                    if isinstance(value, (int, float, str, bool, list, dict, tuple, set)):
                        variables[name] = copy.deepcopy(value)
                except Exception:
                    pass
        
        return ExecutionResult(
            success=error is None,
            output=output,
            error=error,
            return_value=return_value,
            execution_time=execution_time,
            variables=variables
        )
    
    async def _run(
        self,
        code: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Python kodunu çalıştır
        
        Args:
            code: Çalıştırılacak Python kodu
            timeout: Maksimum çalışma süresi (saniye)
            
        Returns:
            Çalıştırma sonucu
        """
        timeout = timeout or self.timeout
        
        # Güvenlik analizi
        if not self.analyzer.analyze(code):
            return {
                "success": False,
                "error": "Güvenlik ihlali tespit edildi",
                "violations": self.analyzer.violations,
                "code": code
            }
        
        # Sandbox namespace oluştur
        namespace = SandboxNamespace.create()
        
        try:
            # Timeout ile çalıştır
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    self._execute_code,
                    code,
                    namespace
                ),
                timeout=timeout
            )
            
            return {
                "success": result.success,
                "output": result.output,
                "error": result.error,
                "return_value": repr(result.return_value) if result.return_value is not None else None,
                "execution_time": round(result.execution_time, 4),
                "variables": {k: repr(v) for k, v in result.variables.items()},
                "code": code
            }
        
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Zaman aşımı: Kod {timeout} saniyede tamamlanmadı",
                "code": code
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Beklenmeyen hata: {str(e)}",
                "code": code
            }
    
    def execute(self, **kwargs) -> "ToolResult":
        """Sync execute metodu."""
        import asyncio
        from .base_tool import ToolResult
        
        code = kwargs.get("code", "")
        timeout = kwargs.get("timeout")
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(self._run(code, timeout))
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
                    "code": {
                        "type": "string",
                        "description": "Çalıştırılacak Python kodu"
                    },
                    "timeout": {
                        "type": "number",
                        "minimum": 0.1,
                        "maximum": 30,
                        "description": "Maksimum çalışma süresi (saniye)"
                    }
                },
                "required": ["code"]
            }
        }


# Tool instance - lazy initialization
code_executor_tool = None

def get_code_executor_tool():
    global code_executor_tool
    if code_executor_tool is None:
        code_executor_tool = CodeExecutorTool()
    return code_executor_tool
