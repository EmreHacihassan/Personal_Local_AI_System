"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║         PREMIUM TEST FRAMEWORK - ADAPTIVE INTROSPECTION SYSTEM                ║
║                                                                                 ║
║  Features:                                                                      ║
║  - Dynamic module introspection                                                 ║
║  - Automatic fallback mechanisms                                                ║
║  - Self-healing test suggestions                                                ║
║  - Runtime class/method discovery                                               ║
║  - Defensive error handling                                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import os
import inspect
import importlib
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable, Type, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class TestResult:
    """Enhanced test result with detailed information"""
    name: str
    status: TestStatus
    error: Optional[str] = None
    details: Optional[str] = None
    duration_ms: float = 0.0
    suggestions: List[str] = field(default_factory=list)
    discovered_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASSED


@dataclass
class ModuleInfo:
    """Information about a discovered module"""
    name: str
    path: str
    classes: List[str]
    functions: List[str]
    constants: List[str]
    can_import: bool
    error: Optional[str] = None


class AdaptiveIntrospector:
    """
    Premium introspection system that dynamically discovers
    module contents without hardcoded assumptions
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.module_cache: Dict[str, ModuleInfo] = {}
        self._import_errors: Dict[str, str] = {}
        
    def discover_module(self, module_path: str) -> ModuleInfo:
        """Dynamically discover module contents"""
        if module_path in self.module_cache:
            return self.module_cache[module_path]
            
        info = ModuleInfo(
            name=module_path,
            path="",
            classes=[],
            functions=[],
            constants=[],
            can_import=False
        )
        
        try:
            module = importlib.import_module(module_path)
            info.can_import = True
            info.path = getattr(module, '__file__', '')
            
            for name, obj in inspect.getmembers(module):
                if name.startswith('_'):
                    continue
                    
                if inspect.isclass(obj):
                    # Check if class is defined in this module
                    if hasattr(obj, '__module__') and obj.__module__ == module_path:
                        info.classes.append(name)
                elif inspect.isfunction(obj):
                    if hasattr(obj, '__module__') and obj.__module__ == module_path:
                        info.functions.append(name)
                elif not callable(obj):
                    info.constants.append(name)
                    
        except Exception as e:
            info.error = str(e)
            self._import_errors[module_path] = str(e)
            
        self.module_cache[module_path] = info
        return info
        
    def discover_class_interface(self, module_path: str, class_name: str) -> Dict[str, Any]:
        """Discover a class's interface (methods, attributes, init params)"""
        result = {
            "exists": False,
            "methods": [],
            "properties": [],
            "init_params": [],
            "init_defaults": {},
            "class_attrs": [],
            "error": None
        }
        
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name, None)
            
            if cls is None:
                result["error"] = f"Class '{class_name}' not found in {module_path}"
                # Try to find similar classes
                similar = [n for n in dir(module) if class_name.lower() in n.lower()]
                if similar:
                    result["suggestions"] = similar
                return result
                
            result["exists"] = True
            
            # Get methods and properties
            for name, obj in inspect.getmembers(cls):
                if name.startswith('_') and not name.startswith('__'):
                    continue
                if name.startswith('__') and name.endswith('__'):
                    continue
                    
                if inspect.ismethod(obj) or inspect.isfunction(obj):
                    result["methods"].append(name)
                elif isinstance(obj, property):
                    result["properties"].append(name)
                    
            # Get __init__ signature
            try:
                sig = inspect.signature(cls.__init__)
                for param_name, param in sig.parameters.items():
                    if param_name == 'self':
                        continue
                    result["init_params"].append(param_name)
                    if param.default != inspect.Parameter.empty:
                        result["init_defaults"][param_name] = repr(param.default)
            except (ValueError, TypeError):
                pass
                
        except Exception as e:
            result["error"] = str(e)
            
        return result
        
    def find_similar_names(self, module_path: str, target: str, 
                          search_type: str = "all") -> List[str]:
        """Find similar names in a module (fuzzy matching)"""
        info = self.discover_module(module_path)
        all_names = []
        
        if search_type in ("all", "classes"):
            all_names.extend(info.classes)
        if search_type in ("all", "functions"):
            all_names.extend(info.functions)
        if search_type in ("all", "constants"):
            all_names.extend(info.constants)
            
        target_lower = target.lower()
        matches = []
        
        for name in all_names:
            # Exact match
            if name.lower() == target_lower:
                matches.insert(0, name)
            # Contains match
            elif target_lower in name.lower() or name.lower() in target_lower:
                matches.append(name)
            # Partial word match
            elif any(w in name.lower() for w in target_lower.split('_')):
                matches.append(name)
                
        return matches[:5]
        
    def get_instantiation_hint(self, module_path: str, class_name: str) -> Dict[str, Any]:
        """Get hints for instantiating a class correctly"""
        interface = self.discover_class_interface(module_path, class_name)
        
        hint = {
            "can_instantiate": False,
            "required_params": [],
            "optional_params": {},
            "example_code": "",
            "error": interface.get("error")
        }
        
        if not interface["exists"]:
            return hint
            
        required = [p for p in interface["init_params"] 
                   if p not in interface["init_defaults"]]
        optional = interface["init_defaults"]
        
        hint["can_instantiate"] = len(required) == 0
        hint["required_params"] = required
        hint["optional_params"] = optional
        
        # Generate example code
        if required:
            params = ", ".join(f"{p}=..." for p in required)
            hint["example_code"] = f"{class_name}({params})"
        else:
            hint["example_code"] = f"{class_name}()"
            
        return hint


class SelfHealingTestRunner:
    """
    Premium test runner with self-healing capabilities
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.introspector = AdaptiveIntrospector(self.project_root)
        
    def safe_import(self, module_path: str, 
                   *names: str,
                   fallback_names: Dict[str, List[str]] = None) -> Tuple[bool, Any, str]:
        """
        Safely import from a module with fallback support
        
        Returns: (success, imported_object_or_module, error_message)
        """
        fallback_names = fallback_names or {}
        
        try:
            module = importlib.import_module(module_path)
            
            if not names:
                return True, module, ""
                
            result = {}
            for name in names:
                # First try exact name
                obj = getattr(module, name, None)
                
                if obj is None and name in fallback_names:
                    # Try fallback names
                    for fallback in fallback_names[name]:
                        obj = getattr(module, fallback, None)
                        if obj is not None:
                            break
                            
                if obj is None:
                    # Try to find similar
                    similar = self.introspector.find_similar_names(module_path, name)
                    if similar:
                        return False, None, f"'{name}' not found. Did you mean: {similar}?"
                    return False, None, f"'{name}' not found in {module_path}"
                    
                result[name] = obj
                
            return True, result if len(result) > 1 else list(result.values())[0], ""
            
        except ImportError as e:
            return False, None, str(e)
            
    def safe_instantiate(self, cls: Type, 
                        *args,
                        required_params: Dict[str, Any] = None,
                        **kwargs) -> Tuple[bool, Any, str]:
        """
        Safely instantiate a class with automatic parameter detection
        """
        required_params = required_params or {}
        
        try:
            # Merge required_params into kwargs
            for key, value in required_params.items():
                if key not in kwargs:
                    kwargs[key] = value
                    
            instance = cls(*args, **kwargs)
            return True, instance, ""
            
        except TypeError as e:
            error_msg = str(e)
            
            # Analyze what's missing
            if "required positional argument" in error_msg:
                # Extract missing argument name
                import re
                match = re.search(r"'(\w+)'", error_msg)
                if match:
                    missing_arg = match.group(1)
                    hint = self.introspector.get_instantiation_hint(
                        cls.__module__, cls.__name__
                    )
                    return False, None, (
                        f"Missing required parameter: '{missing_arg}'. "
                        f"Example: {hint['example_code']}"
                    )
                    
            return False, None, error_msg
            
        except Exception as e:
            return False, None, str(e)
            
    def check_interface(self, obj: Any, 
                       required_methods: List[str] = None,
                       required_attrs: List[str] = None,
                       any_of_methods: List[str] = None) -> Tuple[bool, List[str], str]:
        """
        Check if an object has the required interface
        
        Returns: (success, found_items, message)
        """
        required_methods = required_methods or []
        required_attrs = required_attrs or []
        any_of_methods = any_of_methods or []
        
        found = []
        missing = []
        
        # Check required methods
        for method in required_methods:
            if hasattr(obj, method) and callable(getattr(obj, method)):
                found.append(method)
            else:
                missing.append(method)
                
        # Check required attributes
        for attr in required_attrs:
            if hasattr(obj, attr):
                found.append(attr)
            else:
                missing.append(attr)
                
        # Check any_of_methods (at least one required)
        if any_of_methods:
            found_any = [m for m in any_of_methods if hasattr(obj, m)]
            if found_any:
                found.extend(found_any)
            else:
                missing.append(f"any of: {any_of_methods}")
                
        if missing:
            # Get actual methods for suggestion
            actual_methods = [m for m in dir(obj) if not m.startswith('_') and callable(getattr(obj, m, None))]
            return False, found, f"Missing: {missing}. Available: {actual_methods[:10]}"
            
        return True, found, ""


class PremiumTestPhase(ABC):
    """
    Premium base class for test phases with adaptive introspection
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name: str = "UNNAMED PHASE"
        self.runner = SelfHealingTestRunner()
        self.introspector = self.runner.introspector
        self.start_time: datetime = None
        
    def print_header(self):
        """Print phase header"""
        self.start_time = datetime.now()
        print("\n" + "═" * 70)
        print(f"  {self.phase_name}")
        print(f"  Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70)
        
    def add_result(self, 
                  name: str, 
                  passed: bool, 
                  error: str = None,
                  details: str = None,
                  suggestions: List[str] = None,
                  discovered: Dict[str, Any] = None):
        """Add a test result with enhanced information"""
        status = TestStatus.PASSED if passed else TestStatus.FAILED
        
        result = TestResult(
            name=name,
            status=status,
            error=error,
            details=details,
            suggestions=suggestions or [],
            discovered_info=discovered or {}
        )
        
        self.results.append(result)
        
        status_str = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status_str}: {name}")
        
        if error and not passed:
            print(f"         └─ Error: {error[:80]}...")
            if suggestions:
                print(f"         └─ Suggestion: {suggestions[0]}")
                
    def add_warning(self, name: str, message: str):
        """Add a warning result"""
        result = TestResult(
            name=name,
            status=TestStatus.WARNING,
            details=message
        )
        self.results.append(result)
        print(f"  ⚠ WARN: {name}")
        print(f"         └─ {message[:80]}")
        
    def add_skip(self, name: str, reason: str):
        """Add a skipped test"""
        result = TestResult(
            name=name,
            status=TestStatus.SKIPPED,
            details=reason
        )
        self.results.append(result)
        print(f"  ○ SKIP: {name}")
        print(f"         └─ Reason: {reason[:80]}")
        
    async def test_import_with_discovery(self,
                                         module_path: str,
                                         test_name: str,
                                         expected_classes: List[str] = None,
                                         expected_functions: List[str] = None,
                                         fallbacks: Dict[str, List[str]] = None) -> Optional[Any]:
        """
        Test module import with automatic discovery and fallbacks
        
        Returns the module if successful, None otherwise
        """
        expected_classes = expected_classes or []
        expected_functions = expected_functions or []
        fallbacks = fallbacks or {}
        
        # Discover module first
        info = self.introspector.discover_module(module_path)
        
        if not info.can_import:
            self.add_result(
                test_name, 
                False, 
                info.error,
                suggestions=[f"Check if {module_path} exists and has no syntax errors"]
            )
            return None
            
        # Report discovery
        discovered = {
            "classes": info.classes[:5],
            "functions": info.functions[:5],
            "constants_count": len(info.constants)
        }
        
        self.add_result(
            test_name,
            True,
            discovered=discovered
        )
        
        # Now verify expected items exist
        module = importlib.import_module(module_path)
        
        for cls_name in expected_classes:
            actual_name = cls_name
            
            # Check for fallbacks
            if not hasattr(module, cls_name):
                if cls_name in fallbacks:
                    for fb in fallbacks[cls_name]:
                        if hasattr(module, fb):
                            actual_name = fb
                            break
                            
                if not hasattr(module, actual_name):
                    similar = self.introspector.find_similar_names(module_path, cls_name, "classes")
                    self.add_result(
                        f"{cls_name} Class",
                        False,
                        f"Class not found",
                        suggestions=[f"Did you mean: {similar}?"] if similar else []
                    )
                    continue
                    
            self.add_result(f"{actual_name} Class", True)
            
        for func_name in expected_functions:
            if hasattr(module, func_name):
                self.add_result(f"{func_name} Function", True)
            else:
                similar = self.introspector.find_similar_names(module_path, func_name, "functions")
                self.add_result(
                    f"{func_name} Function",
                    False,
                    f"Function not found",
                    suggestions=[f"Did you mean: {similar}?"] if similar else []
                )
                
        return module
        
    async def test_class_instantiation(self,
                                       module_path: str,
                                       class_name: str,
                                       test_name: str,
                                       init_params: Dict[str, Any] = None,
                                       auto_discover_params: bool = True) -> Optional[Any]:
        """
        Test class instantiation with automatic parameter detection
        
        Returns the instance if successful, None otherwise
        """
        init_params = init_params or {}
        
        # Get instantiation hint
        hint = self.introspector.get_instantiation_hint(module_path, class_name)
        
        if hint["error"]:
            self.add_result(
                test_name,
                False,
                hint["error"],
                suggestions=hint.get("suggestions", [])
            )
            return None
            
        # Import the class
        success, cls, error = self.runner.safe_import(module_path, class_name)
        if not success:
            self.add_result(test_name, False, error)
            return None
            
        # If auto_discover_params, use defaults for missing required params
        if auto_discover_params and hint["required_params"]:
            for param in hint["required_params"]:
                if param not in init_params:
                    # Try to create sensible defaults
                    init_params[param] = self._generate_default_value(param)
                    
        # Try to instantiate
        success, instance, error = self.runner.safe_instantiate(cls, **init_params)
        
        if success:
            self.add_result(
                test_name,
                True,
                discovered={
                    "methods": hint.get("methods", [])[:5],
                    "required_params": hint["required_params"],
                    "optional_params": list(hint["optional_params"].keys())[:5]
                }
            )
            return instance
        else:
            self.add_result(
                test_name,
                False,
                error,
                suggestions=[f"Try: {hint['example_code']}"]
            )
            return None
            
    def _generate_default_value(self, param_name: str) -> Any:
        """Generate sensible default values based on parameter name"""
        import tempfile
        from pathlib import Path
        
        name_lower = param_name.lower()
        
        # Path-related
        if 'path' in name_lower or 'file' in name_lower or 'dir' in name_lower:
            return Path(tempfile.gettempdir()) / f"test_{param_name}.tmp"
            
        # Database-related
        if 'db' in name_lower or 'database' in name_lower:
            return Path(tempfile.gettempdir()) / "test_db.sqlite"
            
        # URL-related
        if 'url' in name_lower:
            return "http://localhost:8001"
            
        # Storage-related
        if 'storage' in name_lower or 'store' in name_lower:
            # Try to find and instantiate a storage class
            return None
            
        # String-like
        if 'name' in name_lower or 'id' in name_lower:
            return f"test_{param_name}"
            
        # Number-like
        if 'size' in name_lower or 'count' in name_lower or 'limit' in name_lower:
            return 100
            
        # Boolean-like
        if 'enable' in name_lower or 'disable' in name_lower or 'is_' in name_lower:
            return True
            
        return None
        
    async def test_interface_compliance(self,
                                        instance: Any,
                                        test_name: str,
                                        required_methods: List[str] = None,
                                        any_of_methods: List[str] = None,
                                        required_attrs: List[str] = None):
        """
        Test if an instance complies with expected interface
        """
        success, found, message = self.runner.check_interface(
            instance,
            required_methods=required_methods,
            any_of_methods=any_of_methods,
            required_attrs=required_attrs
        )
        
        self.add_result(
            test_name,
            success,
            message if not success else None,
            discovered={"found": found}
        )
        
    @abstractmethod
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests - must be implemented by subclasses"""
        pass
        
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        warned = sum(1 for r in self.results if r.status == TestStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        print("\n" + "═" * 70)
        print(f"  {self.phase_name} - SUMMARY")
        print("═" * 70)
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({100*passed/total:.1f}%)" if total > 0 else "  No tests run")
        print(f"  Failed: {failed}")
        if warned > 0:
            print(f"  Warnings: {warned}")
        if skipped > 0:
            print(f"  Skipped: {skipped}")
        print(f"  Duration: {duration:.2f}s")
        
        if failed > 0:
            print(f"\n  Failed Tests:")
            for r in self.results:
                if r.status == TestStatus.FAILED:
                    print(f"    ✗ {r.name}: {r.error[:60] if r.error else 'Unknown'}")
                    if r.suggestions:
                        print(f"      └─ Suggestion: {r.suggestions[0]}")
                        
        print("═" * 70 + "\n")
        
        return {
            "phase": self.phase_name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warned,
            "skipped": skipped,
            "success_rate": round(100 * passed / total, 1) if total > 0 else 0,
            "duration_seconds": round(duration, 2),
            "results": [
                {
                    "name": r.name, 
                    "passed": r.passed, 
                    "status": r.status.value,
                    "error": r.error,
                    "suggestions": r.suggestions,
                    "discovered": r.discovered_info
                }
                for r in self.results
            ]
        }


class TestDiscovery:
    """
    Premium test discovery system
    """
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.core_dir = project_root / "core"
        
    def discover_all_modules(self) -> Dict[str, ModuleInfo]:
        """Discover all modules in core directory"""
        introspector = AdaptiveIntrospector(self.project_root)
        modules = {}
        
        for py_file in self.core_dir.glob("*.py"):
            if py_file.name.startswith('_'):
                continue
                
            module_name = f"core.{py_file.stem}"
            info = introspector.discover_module(module_name)
            modules[module_name] = info
            
        return modules
        
    def generate_test_suggestions(self, module_path: str) -> List[str]:
        """Generate test suggestions for a module"""
        introspector = AdaptiveIntrospector(self.project_root)
        info = introspector.discover_module(module_path)
        
        suggestions = []
        
        for cls in info.classes:
            suggestions.append(f"Test {cls} instantiation")
            
            interface = introspector.discover_class_interface(module_path, cls)
            for method in interface.get("methods", [])[:3]:
                suggestions.append(f"Test {cls}.{method}() functionality")
                
        for func in info.functions[:5]:
            suggestions.append(f"Test {func}() function")
            
        return suggestions


# Helper decorator for robust async tests
def robust_test(timeout: float = 30.0):
    """Decorator for robust async tests with timeout and error handling"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                return {"error": f"Test timed out after {timeout}s"}
            except Exception as e:
                return {"error": str(e), "traceback": traceback.format_exc()}
        return wrapper
    return decorator
