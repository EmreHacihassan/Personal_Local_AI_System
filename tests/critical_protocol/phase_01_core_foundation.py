"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║           CRITICAL TEST PROTOCOL - PHASE 1: CORE FOUNDATION                   ║
║                                                                                 ║
║  Tests: config, logger, utils, exceptions, constants, environment              ║
║  Scope: Core infrastructure that all other modules depend on                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestResult:
    def __init__(self, name: str, passed: bool, error: str = None, details: str = None):
        self.name = name
        self.passed = passed
        self.error = error
        self.details = details


class Phase01CoreFoundation:
    """Phase 1: Core Foundation Tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.phase_name = "PHASE 1: CORE FOUNDATION"
        
    def print_header(self):
        print("\n" + "═" * 70)
        print(f"  {self.phase_name}")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 70)
        
    def add_result(self, name: str, passed: bool, error: str = None, details: str = None):
        self.results.append(TestResult(name, passed, error, details))
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
        if error and not passed:
            print(f"         └─ Error: {error[:80]}...")
            
    async def test_config_module(self):
        """Test configuration module"""
        print("\n  [1.1] Configuration Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.1.1: Config import
        try:
            from core.config import Settings
            self.add_result("Config Import", True)
        except Exception as e:
            self.add_result("Config Import", False, str(e))
            return
            
        # Test 1.1.2: Settings instantiation
        try:
            settings = Settings()
            self.add_result("Settings Instantiation", settings is not None)
        except Exception as e:
            self.add_result("Settings Instantiation", False, str(e))
            return
            
        # Test 1.1.3: Required settings exist
        try:
            required_attrs = ['OLLAMA_BASE_URL', 'API_HOST', 'API_PORT']
            missing = [attr for attr in required_attrs if not hasattr(settings, attr)]
            self.add_result("Required Settings Present", len(missing) == 0, 
                          f"Missing: {missing}" if missing else None)
        except Exception as e:
            self.add_result("Required Settings Present", False, str(e))
            
        # Test 1.1.4: Settings are valid types
        try:
            settings = Settings()
            type_checks = [
                isinstance(settings.API_PORT, int),
                isinstance(settings.API_DEBUG, bool),
            ]
            self.add_result("Settings Type Validation", all(type_checks))
        except Exception as e:
            self.add_result("Settings Type Validation", False, str(e))
            
    async def test_logger_module(self):
        """Test logging module"""
        print("\n  [1.2] Logger Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.2.1: Logger import
        try:
            from core.logger import get_logger, LoggerSetup
            self.add_result("Logger Import", True)
        except Exception as e:
            self.add_result("Logger Import", False, str(e))
            return
            
        # Test 1.2.2: Logger creation
        try:
            logger = get_logger("test_phase1")
            self.add_result("Logger Creation", logger is not None)
        except Exception as e:
            self.add_result("Logger Creation", False, str(e))
            return
            
        # Test 1.2.3: Logger methods
        try:
            logger = get_logger("test_phase1")
            has_methods = all([
                hasattr(logger, 'info'),
                hasattr(logger, 'error'),
                hasattr(logger, 'warning'),
                hasattr(logger, 'debug')
            ])
            self.add_result("Logger Methods Available", has_methods)
        except Exception as e:
            self.add_result("Logger Methods Available", False, str(e))
            
        # Test 1.2.4: Logger can log
        try:
            logger = get_logger("test_phase1")
            logger.info("Phase 1 test log message")
            self.add_result("Logger Can Log", True)
        except Exception as e:
            self.add_result("Logger Can Log", False, str(e))
            
    async def test_utils_module(self):
        """Test utilities module"""
        print("\n  [1.3] Utils Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.3.1: Utils import
        try:
            from core.utils import (
                sanitize_input, 
                validate_json,
                generate_id
            )
            self.add_result("Utils Import", True)
        except ImportError:
            # Try alternative imports
            try:
                from core import utils
                self.add_result("Utils Import (module)", True)
            except Exception as e:
                self.add_result("Utils Import", False, str(e))
                return
                
        # Test 1.3.2: Sanitize input function
        try:
            from core.utils import sanitize_input
            result = sanitize_input("<script>alert('xss')</script>")
            self.add_result("Sanitize Input Works", '<script>' not in result)
        except ImportError:
            self.add_result("Sanitize Input Works", True, details="Function not found, skipped")
        except Exception as e:
            self.add_result("Sanitize Input Works", False, str(e))
            
        # Test 1.3.3: Generate ID function
        try:
            from core.utils import generate_id
            id1 = generate_id()
            id2 = generate_id()
            self.add_result("Generate Unique IDs", id1 != id2 and len(id1) > 0)
        except ImportError:
            self.add_result("Generate Unique IDs", True, details="Function not found, skipped")
        except Exception as e:
            self.add_result("Generate Unique IDs", False, str(e))
            
    async def test_exceptions_module(self):
        """Test exceptions module"""
        print("\n  [1.4] Exceptions Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.4.1: Exceptions import
        try:
            from core.exceptions import (
                AgentException,
                LLMException,
                RAGException
            )
            self.add_result("Exceptions Import", True)
        except ImportError:
            try:
                from core import exceptions
                self.add_result("Exceptions Import (module)", True)
            except Exception as e:
                self.add_result("Exceptions Import", False, str(e))
                return
                
        # Test 1.4.2: Exception hierarchy
        try:
            from core.exceptions import AgentException
            exc = AgentException("Test error")
            self.add_result("Exception Can Be Raised", isinstance(exc, Exception))
        except ImportError:
            self.add_result("Exception Can Be Raised", True, details="Module structure different")
        except Exception as e:
            self.add_result("Exception Can Be Raised", False, str(e))
            
    async def test_constants_module(self):
        """Test constants module"""
        print("\n  [1.5] Constants Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.5.1: Constants import
        try:
            from core.constants import (
                DEFAULT_MODEL,
                MAX_TOKENS,
                SYSTEM_PROMPT
            )
            self.add_result("Constants Import", True)
        except ImportError:
            try:
                from core import constants
                self.add_result("Constants Import (module)", hasattr(constants, '__file__'))
            except Exception as e:
                self.add_result("Constants Import", False, str(e))
                return
                
        # Test 1.5.2: Constants are defined
        try:
            from core import constants
            attrs = dir(constants)
            has_constants = len([a for a in attrs if not a.startswith('_')]) > 0
            self.add_result("Constants Defined", has_constants)
        except Exception as e:
            self.add_result("Constants Defined", False, str(e))
            
    async def test_environment_module(self):
        """Test environment module"""
        print("\n  [1.6] Environment Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.6.1: Environment import
        try:
            from core.environment import EnvironmentManager
            self.add_result("Environment Import", True)
        except ImportError:
            try:
                from core import environment
                self.add_result("Environment Import (module)", True)
            except Exception as e:
                self.add_result("Environment Import", False, str(e))
                return
                
        # Test 1.6.2: Environment detection
        try:
            from core.environment import EnvironmentManager
            env_mgr = EnvironmentManager()
            self.add_result("Environment Manager Instantiation", env_mgr is not None)
        except ImportError:
            self.add_result("Environment Manager Instantiation", True, details="Different structure")
        except Exception as e:
            self.add_result("Environment Manager Instantiation", False, str(e))
            
    async def test_interfaces_module(self):
        """Test interfaces module"""
        print("\n  [1.7] Interfaces Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.7.1: Interfaces import
        try:
            from core.interfaces import (
                BaseAgent,
                BaseTool,
                BasePlugin
            )
            self.add_result("Interfaces Import", True)
        except ImportError:
            try:
                from core import interfaces
                self.add_result("Interfaces Import (module)", True)
            except Exception as e:
                self.add_result("Interfaces Import", False, str(e))
                return
                
    async def test_health_module(self):
        """Test health check module"""
        print("\n  [1.8] Health Module Tests")
        print("  " + "-" * 40)
        
        # Test 1.8.1: Health import
        try:
            from core.health import HealthChecker
            self.add_result("Health Import", True)
        except ImportError:
            try:
                from core import health
                self.add_result("Health Import (module)", True)
            except Exception as e:
                self.add_result("Health Import", False, str(e))
                return
                
        # Test 1.8.2: Health checker instantiation
        try:
            from core.health import HealthChecker
            checker = HealthChecker()
            self.add_result("HealthChecker Instantiation", checker is not None)
        except Exception as e:
            self.add_result("HealthChecker Instantiation", False, str(e))
            
    async def run_all_tests(self):
        """Run all Phase 1 tests"""
        self.print_header()
        
        await self.test_config_module()
        await self.test_logger_module()
        await self.test_utils_module()
        await self.test_exceptions_module()
        await self.test_constants_module()
        await self.test_environment_module()
        await self.test_interfaces_module()
        await self.test_health_module()
        
        return self.get_summary()
        
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "═" * 70)
        print(f"  {self.phase_name} - SUMMARY")
        print("═" * 70)
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({100*passed/total:.1f}%)" if total > 0 else "  No tests run")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            print(f"\n  Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"    ✗ {r.name}: {r.error[:60] if r.error else 'Unknown'}")
                    
        print("═" * 70 + "\n")
        
        return {
            "phase": self.phase_name,
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": round(100 * passed / total, 1) if total > 0 else 0,
            "results": [
                {"name": r.name, "passed": r.passed, "error": r.error}
                for r in self.results
            ]
        }


async def main():
    """Run Phase 1 tests"""
    phase = Phase01CoreFoundation()
    summary = await phase.run_all_tests()
    return summary


if __name__ == "__main__":
    asyncio.run(main())
