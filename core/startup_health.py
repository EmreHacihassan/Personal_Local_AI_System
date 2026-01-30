"""
Enterprise AI Assistant - Startup Health System
================================================

Kapsamlı startup sağlık kontrol sistemi.

FEATURES:
- Pre-flight checks (Python version, dependencies)
- Service dependency validation
- ChromaDB health with auto-recovery
- Ollama connectivity check
- Port availability check
- Graceful startup with proper ordering
- Detailed error reporting

Bu modül tüm startup hatalarını önler.
"""

import os
import sys
import time
import socket
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import importlib
import json

from .config import settings
from .logger import get_logger

logger = get_logger("startup_health")


class CheckStatus(str, Enum):
    """Check durumları."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class HealthCheckResult:
    """Tek bir health check sonucu."""
    name: str
    status: CheckStatus
    message: str
    duration_ms: int = 0
    details: Optional[Dict[str, Any]] = None
    fix_suggestion: Optional[str] = None
    is_critical: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "details": self.details,
            "fix_suggestion": self.fix_suggestion,
            "is_critical": self.is_critical,
        }


@dataclass
class StartupReport:
    """Startup raporu."""
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    skipped_checks: int = 0
    is_ready: bool = False
    results: List[HealthCheckResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_duration_ms": int((self.completed_at - self.started_at).total_seconds() * 1000) if self.completed_at else 0,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "warning_checks": self.warning_checks,
            "skipped_checks": self.skipped_checks,
            "is_ready": self.is_ready,
            "results": [r.to_dict() for r in self.results],
        }
    
    def add_result(self, result: HealthCheckResult):
        """Sonuç ekle."""
        self.results.append(result)
        self.total_checks += 1
        
        if result.status == CheckStatus.PASSED:
            self.passed_checks += 1
        elif result.status == CheckStatus.FAILED:
            self.failed_checks += 1
        elif result.status == CheckStatus.WARNING:
            self.warning_checks += 1
        elif result.status == CheckStatus.SKIPPED:
            self.skipped_checks += 1
    
    def print_summary(self):
        """Özet yazdır."""
        print("\n" + "=" * 60)
        print("🏥 STARTUP HEALTH CHECK REPORT")
        print("=" * 60)
        
        for result in self.results:
            icon = {
                CheckStatus.PASSED: "✅",
                CheckStatus.FAILED: "❌",
                CheckStatus.WARNING: "⚠️",
                CheckStatus.SKIPPED: "⏭️",
            }.get(result.status, "❓")
            
            critical_tag = " [CRITICAL]" if result.is_critical else ""
            print(f"{icon} {result.name}{critical_tag}")
            print(f"   {result.message}")
            if result.fix_suggestion:
                print(f"   💡 Fix: {result.fix_suggestion}")
        
        print("-" * 60)
        print(f"Total: {self.total_checks} | ✅ {self.passed_checks} | ❌ {self.failed_checks} | ⚠️ {self.warning_checks}")
        
        if self.is_ready:
            print("\n🚀 System is READY to start!")
        else:
            print("\n⛔ System is NOT READY - fix critical issues first")
        
        print("=" * 60 + "\n")


class StartupHealthChecker:
    """
    Kapsamlı startup sağlık kontrolcüsü.
    
    Checks:
    1. Python version
    2. Virtual environment
    3. Critical dependencies
    4. Data directories
    5. ChromaDB health
    6. Ollama connectivity
    7. Port availability
    8. Disk space
    
    Usage:
        checker = StartupHealthChecker()
        report = checker.run_all_checks()
        if report.is_ready:
            start_services()
    """
    
    # Required Python version
    MIN_PYTHON_VERSION = (3, 10)
    MAX_PYTHON_VERSION = (3, 13)
    
    # Critical packages
    CRITICAL_PACKAGES = [
        "fastapi",
        "uvicorn",
        "chromadb",
        "ollama",
        "pydantic",
        "httpx",
        "numpy",
    ]
    
    # Ports to check
    SERVICE_PORTS = {
        "api": 8001,
        "streamlit": 8501,
        "nextjs": 3000,
        "ollama": 11434,
    }
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent.parent
        self.report = StartupReport(started_at=datetime.now())
    
    def run_check(
        self,
        name: str,
        check_fn: Callable[[], Tuple[bool, str, Optional[Dict]]],
        is_critical: bool = False,
        fix_suggestion: Optional[str] = None,
    ) -> HealthCheckResult:
        """
        Tek bir check çalıştır.
        
        Args:
            name: Check adı
            check_fn: Check fonksiyonu -> (success, message, details)
            is_critical: Kritik mi (fail ederse startup durdurulur)
            fix_suggestion: Düzeltme önerisi
        """
        start = time.time()
        
        try:
            success, message, details = check_fn()
            status = CheckStatus.PASSED if success else CheckStatus.FAILED
            
        except Exception as e:
            status = CheckStatus.FAILED
            message = f"Check error: {str(e)}"
            details = {"exception": type(e).__name__}
        
        duration_ms = int((time.time() - start) * 1000)
        
        result = HealthCheckResult(
            name=name,
            status=status,
            message=message,
            duration_ms=duration_ms,
            details=details,
            fix_suggestion=fix_suggestion if status == CheckStatus.FAILED else None,
            is_critical=is_critical,
        )
        
        self.report.add_result(result)
        return result
    
    # ==========================================================================
    # CHECK IMPLEMENTATIONS
    # ==========================================================================
    
    def check_python_version(self) -> Tuple[bool, str, Optional[Dict]]:
        """Python versiyonu kontrolü."""
        current = sys.version_info[:3]
        major, minor, patch = current
        
        details = {
            "current_version": f"{major}.{minor}.{patch}",
            "min_version": f"{self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]}",
            "max_version": f"{self.MAX_PYTHON_VERSION[0]}.{self.MAX_PYTHON_VERSION[1]}",
            "executable": sys.executable,
        }
        
        if (major, minor) < self.MIN_PYTHON_VERSION:
            return False, f"Python {major}.{minor} too old (min: {self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]})", details
        
        if (major, minor) > self.MAX_PYTHON_VERSION:
            return False, f"Python {major}.{minor} too new (max: {self.MAX_PYTHON_VERSION[0]}.{self.MAX_PYTHON_VERSION[1]})", details
        
        return True, f"Python {major}.{minor}.{patch} OK", details
    
    def check_virtual_env(self) -> Tuple[bool, str, Optional[Dict]]:
        """Virtual environment kontrolü."""
        in_venv = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )
        
        venv_path = Path(sys.prefix)
        
        details = {
            "in_venv": in_venv,
            "venv_path": str(venv_path),
            "executable": sys.executable,
        }
        
        if not in_venv:
            return False, "Not running in virtual environment", details
        
        # Venv'in proje dizininde olup olmadığını kontrol et
        try:
            venv_path.relative_to(self.project_dir)
            return True, f"Running in project venv", details
        except ValueError:
            return True, f"Running in external venv: {venv_path}", details
    
    def check_critical_packages(self) -> Tuple[bool, str, Optional[Dict]]:
        """Kritik paketlerin yüklü olup olmadığını kontrol et."""
        missing = []
        installed = []
        
        for package in self.CRITICAL_PACKAGES:
            try:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                installed.append({"name": package, "version": version})
            except ImportError:
                missing.append(package)
        
        details = {
            "installed": installed,
            "missing": missing,
        }
        
        if missing:
            return False, f"Missing packages: {', '.join(missing)}", details
        
        return True, f"All {len(installed)} critical packages installed", details
    
    def check_data_directories(self) -> Tuple[bool, str, Optional[Dict]]:
        """Data dizinlerinin varlığını ve yazılabilirliğini kontrol et."""
        required_dirs = [
            settings.DATA_DIR,
            settings.DATA_DIR / "chroma_db",
            settings.DATA_DIR / "sessions",
            settings.DATA_DIR / "uploads",
            settings.DATA_DIR / "cache",
            settings.DATA_DIR / "logs",
        ]
        
        created = []
        existing = []
        errors = []
        
        for dir_path in required_dirs:
            try:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created.append(str(dir_path))
                else:
                    existing.append(str(dir_path))
                
                # Write test
                test_file = dir_path / ".write_test"
                test_file.write_text("test")
                test_file.unlink()
                
            except Exception as e:
                errors.append({"path": str(dir_path), "error": str(e)})
        
        details = {
            "created": created,
            "existing": existing,
            "errors": errors,
        }
        
        if errors:
            return False, f"Directory errors: {len(errors)}", details
        
        msg = f"Directories OK ({len(existing)} existing, {len(created)} created)"
        return True, msg, details
    
    def check_chromadb_health(self) -> Tuple[bool, str, Optional[Dict]]:
        """ChromaDB sağlık kontrolü."""
        try:
            from .chromadb_resilient import resilient_chromadb
            
            # ensure_healthy tüm recovery'yi dener
            is_healthy = resilient_chromadb.ensure_healthy()
            
            if is_healthy:
                status = resilient_chromadb.get_status()
                return True, "ChromaDB healthy", status
            else:
                return False, "ChromaDB recovery failed", None
                
        except ImportError:
            # Fallback to basic check
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            chroma_path = settings.DATA_DIR / "chroma_db"
            
            try:
                client = chromadb.PersistentClient(
                    path=str(chroma_path),
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                collections = client.list_collections()
                return True, f"ChromaDB OK ({len(collections)} collections)", {"collection_count": len(collections)}
            except Exception as e:
                return False, f"ChromaDB error: {e}", None
        
        except Exception as e:
            return False, f"ChromaDB check failed: {e}", None
    
    def check_ollama_connectivity(self) -> Tuple[bool, str, Optional[Dict]]:
        """Ollama bağlantı kontrolü."""
        import httpx
        
        ollama_url = settings.OLLAMA_BASE_URL
        
        try:
            response = httpx.get(f"{ollama_url}/api/tags", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", m.get("model", "unknown")) for m in models]
                
                details = {
                    "url": ollama_url,
                    "model_count": len(models),
                    "models": model_names[:10],  # First 10
                }
                
                # Primary model kontrolü
                primary_model = settings.OLLAMA_PRIMARY_MODEL
                has_primary = any(primary_model in m for m in model_names)
                
                if has_primary:
                    return True, f"Ollama OK ({len(models)} models, primary: {primary_model})", details
                else:
                    details["warning"] = f"Primary model '{primary_model}' not found"
                    return True, f"Ollama OK but primary model missing", details
            else:
                return False, f"Ollama returned {response.status_code}", {"url": ollama_url}
                
        except httpx.ConnectError:
            return False, "Ollama not running", {"url": ollama_url}
        except Exception as e:
            return False, f"Ollama check error: {e}", {"url": ollama_url}
    
    def check_port_availability(self) -> Tuple[bool, str, Optional[Dict]]:
        """Port kullanılabilirlik kontrolü."""
        port_status = {}
        conflicts = []
        
        for service, port in self.SERVICE_PORTS.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            
            try:
                result = sock.connect_ex(('localhost', port))
                is_in_use = result == 0
                port_status[service] = {
                    "port": port,
                    "in_use": is_in_use,
                    "available": not is_in_use,
                }
                
                if is_in_use and service != "ollama":  # Ollama açık olmalı
                    conflicts.append(f"{service}:{port}")
                    
            except Exception:
                port_status[service] = {"port": port, "error": True}
            finally:
                sock.close()
        
        details = {"ports": port_status}
        
        if conflicts:
            return False, f"Port conflicts: {', '.join(conflicts)}", details
        
        return True, "Ports available", details
    
    def check_disk_space(self) -> Tuple[bool, str, Optional[Dict]]:
        """Disk alanı kontrolü."""
        import shutil
        
        path = self.project_dir
        
        try:
            total, used, free = shutil.disk_usage(path)
            
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            used_percent = (used / total) * 100
            
            details = {
                "path": str(path),
                "total_gb": round(total_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 2),
            }
            
            # En az 1GB boş alan gerekli
            if free_gb < 1.0:
                return False, f"Low disk space: {free_gb:.2f}GB free", details
            elif free_gb < 5.0:
                details["warning"] = "Consider freeing up disk space"
                return True, f"Disk OK ({free_gb:.2f}GB free, warning)", details
            else:
                return True, f"Disk OK ({free_gb:.2f}GB free)", details
                
        except Exception as e:
            return False, f"Disk check error: {e}", None
    
    def check_environment_variables(self) -> Tuple[bool, str, Optional[Dict]]:
        """Ortam değişkenleri kontrolü."""
        env_vars = {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }
        
        details = {"variables": env_vars}
        
        return True, f"Environment: {env_vars['ENVIRONMENT']}", details
    
    def check_nodejs_npm(self) -> Tuple[bool, str, Optional[Dict]]:
        """Node.js ve npm kontrolü - SELF-HEALING VERSION."""
        details = {}
        
        def _refresh_path():
            """Windows PATH'ini yenile."""
            if sys.platform != 'win32':
                return
            try:
                machine_path = subprocess.run(
                    ['powershell', '-Command', '[System.Environment]::GetEnvironmentVariable("Path","Machine")'],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).stdout.strip()
                
                user_path = subprocess.run(
                    ['powershell', '-Command', '[System.Environment]::GetEnvironmentVariable("Path","User")'],
                    capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ).stdout.strip()
                
                os.environ['PATH'] = f"{machine_path};{user_path}"
            except (subprocess.SubprocessError, OSError, Exception):
                pass  # Path refresh failed, continue with current PATH
        
        def _check_node():
            """Node.js'i kontrol et."""
            try:
                node_result = subprocess.run(
                    ["node", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True if sys.platform == 'win32' else False,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                )
                
                if node_result.returncode != 0:
                    return None, None
                
                node_version = node_result.stdout.strip()
                
                npm_result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=True if sys.platform == 'win32' else False,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                )
                
                npm_version = npm_result.stdout.strip() if npm_result.returncode == 0 else None
                return node_version, npm_version
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                return None, None
        
        def _auto_install_nodejs():
            """Node.js'i otomatik kur."""
            if sys.platform != 'win32':
                return False
            try:
                logger.info("🔧 Node.js otomatik kurulum deneniyor...")
                result = subprocess.run(
                    ['winget', 'install', 'OpenJS.NodeJS.LTS', 
                     '--accept-source-agreements', '--accept-package-agreements', '--silent'],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0 or 'Successfully installed' in result.stdout:
                    logger.info("✅ Node.js başarıyla kuruldu!")
                    time.sleep(3)
                    _refresh_path()
                    return True
                return False
            except (subprocess.SubprocessError, FileNotFoundError, OSError):
                return False
        
        def _find_nodejs_in_known_paths():
            """Bilinen konumlarda Node.js ara."""
            known_paths = [
                r"C:\Program Files\nodejs",
                r"C:\Program Files (x86)\nodejs",
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs"),
            ]
            
            for path in known_paths:
                node_exe = os.path.join(path, "node.exe")
                if os.path.exists(node_exe):
                    os.environ['PATH'] = f"{path};{os.environ.get('PATH', '')}"
                    return path
            return None
        
        try:
            # İlk deneme
            node_version, npm_version = _check_node()
            
            if not node_version:
                # PATH yenile ve tekrar dene
                _refresh_path()
                node_version, npm_version = _check_node()
            
            if not node_version:
                # Bilinen konumlarda ara
                found_path = _find_nodejs_in_known_paths()
                if found_path:
                    node_version, npm_version = _check_node()
                    if node_version:
                        details["found_at"] = found_path
            
            if not node_version:
                # Otomatik kurulum dene
                details["auto_install_attempted"] = True
                if _auto_install_nodejs():
                    node_version, npm_version = _check_node()
                    if node_version:
                        details["auto_installed"] = True
            
            if not node_version:
                return False, "Node.js not installed", details
            
            details["node_version"] = node_version
            
            # Version kontrolü
            try:
                major = int(node_version.lstrip('v').split('.')[0])
                if major < 16:
                    return False, f"Node.js {node_version} too old (need v16+)", details
                elif major < 18:
                    details["warning"] = "Node.js v18+ recommended"
            except (ValueError, IndexError, AttributeError):
                pass  # Version parsing failed, skip version check
            
            if not npm_version:
                return False, "npm not found", details
            
            details["npm_version"] = npm_version
            
            return True, f"Node.js {node_version}, npm {npm_version}", details
            
        except subprocess.TimeoutExpired:
            return False, "Node.js check timeout", None
        except FileNotFoundError:
            return False, "Node.js not installed", None
        except Exception as e:
            return False, f"Node.js check error: {e}", None
    
    def check_nextjs_deps(self) -> Tuple[bool, str, Optional[Dict]]:
        """Next.js bağımlılıkları kontrolü."""
        nextjs_dir = self.project_dir / "frontend-next"
        node_modules = nextjs_dir / "node_modules"
        
        if not nextjs_dir.exists():
            return True, "Next.js not configured (skipped)", {"skipped": True}
        
        details = {"path": str(nextjs_dir)}
        
        # node_modules var mı?
        if not node_modules.exists():
            return False, "node_modules missing, run npm install", details
        
        # Kritik paketler var mı?
        critical = ["next", "react", "react-dom", "socket.io-client"]
        missing = [pkg for pkg in critical if not (node_modules / pkg).exists()]
        
        if missing:
            details["missing"] = missing
            return False, f"Missing packages: {', '.join(missing)}", details
        
        # .next build var mı? (opsiyonel)
        next_build = nextjs_dir / ".next"
        details["build_exists"] = next_build.exists()
        
        return True, "Next.js dependencies OK", details
    
    # ==========================================================================
    # MAIN RUNNER
    # ==========================================================================
    
    def run_all_checks(self, verbose: bool = True) -> StartupReport:
        """
        Tüm kontrolleri çalıştır.
        
        Args:
            verbose: Sonuçları yazdır
            
        Returns:
            StartupReport
        """
        logger.info("🏥 Starting health checks...")
        
        # 1. Critical checks (fail -> stop)
        self.run_check(
            "Python Version",
            self.check_python_version,
            is_critical=True,
            fix_suggestion="Use Python 3.10-3.12"
        )
        
        self.run_check(
            "Virtual Environment",
            self.check_virtual_env,
            is_critical=False,
            fix_suggestion="Run: python -m venv .venv && .venv\\Scripts\\activate"
        )
        
        self.run_check(
            "Critical Packages",
            self.check_critical_packages,
            is_critical=True,
            fix_suggestion="Run: pip install -r requirements.txt"
        )
        
        # 2. Infrastructure checks
        self.run_check(
            "Data Directories",
            self.check_data_directories,
            is_critical=True,
            fix_suggestion="Check file permissions"
        )
        
        self.run_check(
            "Disk Space",
            self.check_disk_space,
            is_critical=False,
            fix_suggestion="Free up disk space (need at least 1GB)"
        )
        
        # 3. Service checks
        self.run_check(
            "ChromaDB Health",
            self.check_chromadb_health,
            is_critical=True,
            fix_suggestion="Delete data/chroma_db and restart"
        )
        
        self.run_check(
            "Ollama Connectivity",
            self.check_ollama_connectivity,
            is_critical=False,  # Can start without Ollama
            fix_suggestion="Start Ollama: ollama serve"
        )
        
        self.run_check(
            "Port Availability",
            self.check_port_availability,
            is_critical=False,
            fix_suggestion="Kill processes using required ports"
        )
        
        self.run_check(
            "Node.js & npm",
            self.check_nodejs_npm,
            is_critical=False,  # Next.js kullanılmayabilir
            fix_suggestion="Install Node.js LTS from https://nodejs.org"
        )
        
        self.run_check(
            "Next.js Dependencies",
            self.check_nextjs_deps,
            is_critical=False,
            fix_suggestion="Run: cd frontend-next && npm install"
        )
        
        self.run_check(
            "Environment",
            self.check_environment_variables,
            is_critical=False,
        )
        
        # Finalize
        self.report.completed_at = datetime.now()
        
        # Critical failures varsa ready değil
        critical_failures = [r for r in self.report.results if r.is_critical and r.status == CheckStatus.FAILED]
        self.report.is_ready = len(critical_failures) == 0
        
        if verbose:
            self.report.print_summary()
        
        return self.report
    
    def save_report(self, path: Optional[Path] = None) -> Path:
        """Raporu dosyaya kaydet."""
        if path is None:
            path = settings.DATA_DIR / "logs" / f"startup_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            json.dump(self.report.to_dict(), f, indent=2)
        
        return path


def run_startup_checks(verbose: bool = True) -> bool:
    """
    Convenience function for startup checks.
    
    Returns:
        True if system is ready
    """
    checker = StartupHealthChecker()
    report = checker.run_all_checks(verbose=verbose)
    return report.is_ready


# CLI entrypoint
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Startup Health Checker")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    checker = StartupHealthChecker()
    report = checker.run_all_checks(verbose=not args.quiet and not args.json)
    
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    
    sys.exit(0 if report.is_ready else 1)
