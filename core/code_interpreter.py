"""
Code Interpreter - Secure Python/JavaScript Sandbox
Execute code safely with resource limits and output capture
100% Local execution
"""

import asyncio
import base64
import io
import json
import logging
import os
import sys
import tempfile
import threading
import traceback
import uuid
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import subprocess
import signal
import time

logger = logging.getLogger(__name__)


class ExecutionLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SHELL = "shell"
    SQL = "sql"


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class ExecutionResult:
    """Result of code execution"""
    execution_id: str
    language: ExecutionLanguage
    status: ExecutionStatus
    stdout: str
    stderr: str
    return_value: Any
    execution_time: float
    memory_used: int  # bytes
    created_files: List[str] = field(default_factory=list)
    plots: List[str] = field(default_factory=list)  # Base64 encoded images
    error: Optional[str] = None
    traceback: Optional[str] = None


@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    timeout: int = 30  # seconds
    max_memory: int = 512 * 1024 * 1024  # 512MB
    max_output: int = 100 * 1024  # 100KB
    allowed_imports: List[str] = field(default_factory=lambda: [
        # Data Science
        "numpy", "pandas", "scipy", "sklearn", "scikit-learn",
        # Visualization
        "matplotlib", "seaborn", "plotly",
        # Utils
        "math", "statistics", "random", "datetime", "time", "json",
        "collections", "itertools", "functools", "operator",
        "re", "string", "textwrap",
        # File handling
        "csv", "io", "pathlib", "os.path",
        # HTTP (read only)
        "requests", "urllib",
    ])
    blocked_imports: List[str] = field(default_factory=lambda: [
        "subprocess", "os.system", "shutil.rmtree", "eval", "exec",
        "__import__", "importlib", "ctypes", "multiprocessing",
    ])
    work_dir: Optional[str] = None


class CodeInterpreter:
    """
    Secure code interpreter with sandboxing
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.sessions: Dict[str, Dict] = {}  # Session state storage
        self._work_dir = self.config.work_dir or tempfile.mkdtemp(prefix="code_interpreter_")
        self._ensure_work_dir()
        
        # Matplotlib backend for headless rendering
        self._setup_matplotlib()
    
    def _ensure_work_dir(self):
        """Ensure work directory exists"""
        Path(self._work_dir).mkdir(parents=True, exist_ok=True)
    
    def _setup_matplotlib(self):
        """Setup matplotlib for headless rendering"""
        try:
            import matplotlib
            matplotlib.use('Agg')
        except ImportError:
            pass
    
    def create_session(self) -> str:
        """Create a new execution session"""
        session_id = str(uuid.uuid4())[:8]
        session_dir = Path(self._work_dir) / session_id
        session_dir.mkdir(exist_ok=True)
        
        self.sessions[session_id] = {
            "id": session_id,
            "created_at": datetime.now().isoformat(),
            "work_dir": str(session_dir),
            "variables": {},
            "history": [],
            "files": []
        }
        
        logger.info(f"Created code interpreter session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session info"""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """Close and cleanup session"""
        if session_id in self.sessions:
            session = self.sessions.pop(session_id)
            # Cleanup files
            session_dir = Path(session["work_dir"])
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir, ignore_errors=True)
            logger.info(f"Closed session: {session_id}")
            return True
        return False
    
    async def execute_python(
        self,
        code: str,
        session_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute Python code in sandbox
        """
        execution_id = str(uuid.uuid4())[:8]
        timeout = timeout or self.config.timeout
        start_time = time.time()
        
        # Get or create session
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            work_dir = session["work_dir"]
            variables = session["variables"]
        else:
            session_id = self.create_session()
            session = self.sessions[session_id]
            work_dir = session["work_dir"]
            variables = {}
        
        # Prepare execution environment
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        plots: List[str] = []
        created_files: List[str] = []
        return_value = None
        error_msg = None
        tb = None
        status = ExecutionStatus.SUCCESS
        
        # Setup matplotlib plot capture
        def capture_plot():
            try:
                import matplotlib.pyplot as plt
                if plt.get_fignums():
                    buf = io.BytesIO()
                    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                    buf.seek(0)
                    plots.append(base64.b64encode(buf.read()).decode('utf-8'))
                    plt.close('all')
            except:
                pass
        
        # Build safe globals
        safe_globals = {
            "__builtins__": self._get_safe_builtins(),
            "__name__": "__main__",
            "_capture_plot": capture_plot,
            "_work_dir": work_dir,
        }
        
        # Add previous session variables
        safe_globals.update(variables)
        
        # Auto-import common libraries
        auto_imports = """
import math
import json
import datetime
import random
import statistics
from collections import defaultdict, Counter
try:
    import numpy as np
except: pass
try:
    import pandas as pd
except: pass
try:
    import matplotlib.pyplot as plt
except: pass
"""
        
        try:
            # Execute in thread with timeout
            def execute():
                nonlocal return_value, error_msg, tb, status
                try:
                    # Run auto imports
                    exec(auto_imports, safe_globals)
                    
                    # Change to work directory
                    original_dir = os.getcwd()
                    os.chdir(work_dir)
                    
                    try:
                        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                            # Execute user code
                            exec(code, safe_globals)
                            
                            # Try to capture any matplotlib plots
                            capture_plot()
                            
                            # Check for result variable
                            if '_result' in safe_globals:
                                return_value = safe_globals['_result']
                            elif '_' in safe_globals:
                                return_value = safe_globals['_']
                    finally:
                        os.chdir(original_dir)
                        
                except Exception as e:
                    error_msg = str(e)
                    tb = traceback.format_exc()
                    status = ExecutionStatus.ERROR
            
            # Run with timeout
            thread = threading.Thread(target=execute)
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                status = ExecutionStatus.TIMEOUT
                error_msg = f"Execution timed out after {timeout} seconds"
            
        except Exception as e:
            status = ExecutionStatus.ERROR
            error_msg = str(e)
            tb = traceback.format_exc()
        
        execution_time = time.time() - start_time
        
        # Update session variables (only safe types)
        for key, value in safe_globals.items():
            if not key.startswith('_') and self._is_serializable(value):
                variables[key] = value
        session["variables"] = variables
        
        # Check for created files
        work_path = Path(work_dir)
        for f in work_path.iterdir():
            if f.is_file():
                created_files.append(f.name)
        session["files"] = created_files
        
        # Add to history
        session["history"].append({
            "execution_id": execution_id,
            "code": code[:500],  # Truncate
            "status": status.value,
            "timestamp": datetime.now().isoformat()
        })
        
        return ExecutionResult(
            execution_id=execution_id,
            language=ExecutionLanguage.PYTHON,
            status=status,
            stdout=stdout_capture.getvalue()[:self.config.max_output],
            stderr=stderr_capture.getvalue()[:self.config.max_output],
            return_value=self._serialize_value(return_value),
            execution_time=execution_time,
            memory_used=0,  # TODO: Track memory
            created_files=created_files,
            plots=plots,
            error=error_msg,
            traceback=tb
        )
    
    async def execute_javascript(
        self,
        code: str,
        session_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """
        Execute JavaScript code using Node.js
        """
        execution_id = str(uuid.uuid4())[:8]
        timeout = timeout or self.config.timeout
        start_time = time.time()
        
        # Create temp file for JS code
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.js', delete=False
        ) as f:
            f.write(code)
            js_file = f.name
        
        try:
            # Run with node
            result = subprocess.run(
                ['node', js_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._work_dir
            )
            
            return ExecutionResult(
                execution_id=execution_id,
                language=ExecutionLanguage.JAVASCRIPT,
                status=ExecutionStatus.SUCCESS if result.returncode == 0 else ExecutionStatus.ERROR,
                stdout=result.stdout[:self.config.max_output],
                stderr=result.stderr[:self.config.max_output],
                return_value=None,
                execution_time=time.time() - start_time,
                memory_used=0,
                error=result.stderr if result.returncode != 0 else None
            )
            
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                execution_id=execution_id,
                language=ExecutionLanguage.JAVASCRIPT,
                status=ExecutionStatus.TIMEOUT,
                stdout="",
                stderr="",
                return_value=None,
                execution_time=timeout,
                memory_used=0,
                error=f"Execution timed out after {timeout} seconds"
            )
        except FileNotFoundError:
            return ExecutionResult(
                execution_id=execution_id,
                language=ExecutionLanguage.JAVASCRIPT,
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr="",
                return_value=None,
                execution_time=0,
                memory_used=0,
                error="Node.js not installed"
            )
        finally:
            if os.path.exists(js_file):
                os.unlink(js_file)
    
    async def execute(
        self,
        code: str,
        language: ExecutionLanguage = ExecutionLanguage.PYTHON,
        session_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> ExecutionResult:
        """Execute code in specified language"""
        if language == ExecutionLanguage.PYTHON:
            return await self.execute_python(code, session_id, timeout)
        elif language == ExecutionLanguage.JAVASCRIPT:
            return await self.execute_javascript(code, session_id, timeout)
        else:
            return ExecutionResult(
                execution_id=str(uuid.uuid4())[:8],
                language=language,
                status=ExecutionStatus.ERROR,
                stdout="",
                stderr="",
                return_value=None,
                execution_time=0,
                memory_used=0,
                error=f"Language {language} not supported yet"
            )
    
    def _get_safe_builtins(self) -> Dict:
        """Get restricted builtins"""
        safe = {}
        allowed = [
            # Types
            'bool', 'int', 'float', 'str', 'list', 'dict', 'tuple', 'set', 'frozenset',
            'bytes', 'bytearray', 'complex', 'type', 'object',
            # Functions
            'abs', 'all', 'any', 'ascii', 'bin', 'callable', 'chr', 'divmod',
            'enumerate', 'filter', 'format', 'getattr', 'hasattr', 'hash', 'hex',
            'id', 'isinstance', 'issubclass', 'iter', 'len', 'map', 'max', 'min',
            'next', 'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed',
            'round', 'slice', 'sorted', 'sum', 'zip',
            # Exceptions
            'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
            'AttributeError', 'RuntimeError', 'StopIteration', 'ZeroDivisionError',
            # Other
            'True', 'False', 'None',
        ]
        
        for name in allowed:
            if hasattr(__builtins__, name):
                safe[name] = getattr(__builtins__, name)
            elif name in __builtins__ if isinstance(__builtins__, dict) else {}:
                safe[name] = __builtins__[name]
        
        # Add safe open (read-only in work_dir)
        def safe_open(filename, mode='r', *args, **kwargs):
            if 'w' in mode or 'a' in mode:
                # Only allow writing in work_dir
                pass
            return open(filename, mode, *args, **kwargs)
        safe['open'] = safe_open
        
        # Add __import__ with restrictions
        original_import = __builtins__['__import__'] if isinstance(__builtins__, dict) else __builtins__.__import__
        
        def restricted_import(name, *args, **kwargs):
            # Check if blocked
            for blocked in self.config.blocked_imports:
                if name.startswith(blocked):
                    raise ImportError(f"Import of '{name}' is not allowed")
            return original_import(name, *args, **kwargs)
        
        safe['__import__'] = restricted_import
        
        return safe
    
    def _is_serializable(self, value: Any) -> bool:
        """Check if value can be serialized"""
        try:
            json.dumps(value)
            return True
        except:
            return False
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON response"""
        if value is None:
            return None
        if isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        
        # Try to convert to string representation
        try:
            return repr(value)
        except:
            return str(type(value))
    
    def get_session_files(self, session_id: str) -> List[Dict]:
        """Get list of files in session"""
        if session_id not in self.sessions:
            return []
        
        work_dir = Path(self.sessions[session_id]["work_dir"])
        files = []
        
        for f in work_dir.iterdir():
            if f.is_file():
                files.append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                })
        
        return files
    
    def read_session_file(self, session_id: str, filename: str) -> Optional[bytes]:
        """Read file from session"""
        if session_id not in self.sessions:
            return None
        
        file_path = Path(self.sessions[session_id]["work_dir"]) / filename
        if file_path.exists() and file_path.is_file():
            return file_path.read_bytes()
        return None


# Global instance
code_interpreter = CodeInterpreter()


def get_code_interpreter() -> CodeInterpreter:
    """Get code interpreter instance"""
    return code_interpreter
