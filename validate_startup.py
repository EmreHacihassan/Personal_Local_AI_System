#!/usr/bin/env python
"""
Enterprise AI Assistant - Startup Validation Script
====================================================

Bu script sistemi çalıştırmadan ÖNCE tüm gereksinimleri kontrol eder.
Herhangi bir import yapmadan, minimum bağımlılıkla çalışır.

KULLANIM:
    python validate_startup.py          # Tam doğrulama
    python validate_startup.py --quick  # Hızlı doğrulama
    python validate_startup.py --fix    # Otomatik düzeltme dene
    python validate_startup.py --json   # JSON çıktı

KONTROLLER:
1. Python sürümü
2. Virtual environment
3. Kritik paketler
4. Veri dizinleri
5. Dosya izinleri
6. Port kullanılabilirliği
7. Disk alanı
8. ChromaDB veritabanı
9. Ollama servisi
10. Environment variables
"""

import sys
import os
import json
import argparse
import subprocess
import socket
import shutil
from pathlib import Path
from datetime import datetime


# =============================================================================
# CONSTANTS
# =============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()

# Minimum gereksinimler
MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 13)

# Kritik paketler (pip freeze çıktısından kontrol edilir)
CRITICAL_PACKAGES = [
    "fastapi",
    "uvicorn",
    "chromadb",
    "ollama",
    "pydantic",
    "httpx",
    "python-multipart",
]

# Veri dizinleri
DATA_DIRS = [
    "data",
    "data/cache",
    "data/chroma_db",
    "data/chroma_backups",
    "data/sessions",
    "data/uploads",
    "logs",
]

# Port kontrolleri
REQUIRED_PORTS = {
    8001: "FastAPI Backend",
    3000: "Next.js Frontend",
    8501: "Streamlit Dashboard",
    11434: "Ollama LLM",
}

# Minimum disk alanı (bytes)
MIN_DISK_SPACE = 1024 * 1024 * 1024  # 1 GB


# =============================================================================
# OUTPUT HELPERS
# =============================================================================

class Colors:
    """ANSI renk kodları."""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def supports_color():
    """Terminal renk desteği var mı?"""
    if os.name == 'nt':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            return False
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

USE_COLORS = supports_color()

def color(text: str, code: str) -> str:
    """Renkli metin."""
    if USE_COLORS:
        return f"{code}{text}{Colors.RESET}"
    return text

def ok(msg: str) -> str:
    return color(f"✅ {msg}", Colors.GREEN)

def warn(msg: str) -> str:
    return color(f"⚠️ {msg}", Colors.YELLOW)

def err(msg: str) -> str:
    return color(f"❌ {msg}", Colors.RED)

def info(msg: str) -> str:
    return color(f"ℹ️ {msg}", Colors.BLUE)

def header(msg: str) -> str:
    return color(f"\n{'='*60}\n{msg}\n{'='*60}", Colors.BOLD)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

class ValidationResult:
    """Doğrulama sonucu."""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.details = []
        self.fixable = False
        self.fix_command = None
    
    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "fixable": self.fixable,
            "fix_command": self.fix_command,
        }


def check_python_version() -> ValidationResult:
    """Python sürümü kontrolü."""
    result = ValidationResult("Python Version")
    
    version = sys.version_info[:2]
    version_str = f"{version[0]}.{version[1]}"
    
    if version < MIN_PYTHON:
        result.message = f"Python {version_str} çok eski. Minimum: {MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
        result.fixable = False
    elif version > MAX_PYTHON:
        result.message = f"Python {version_str} desteklenmiyor. Maksimum: {MAX_PYTHON[0]}.{MAX_PYTHON[1]}"
        result.details.append("Python 3.14+ henüz ChromaDB tarafından desteklenmiyor")
        result.fixable = False
    else:
        result.passed = True
        result.message = f"Python {version_str} ✓"
    
    result.details.append(f"Executable: {sys.executable}")
    
    return result


def check_virtual_env() -> ValidationResult:
    """Virtual environment kontrolü."""
    result = ValidationResult("Virtual Environment")
    
    in_venv = (
        sys.prefix != sys.base_prefix or
        os.environ.get("VIRTUAL_ENV") is not None
    )
    
    if in_venv:
        result.passed = True
        result.message = "Virtual environment aktif ✓"
        result.details.append(f"Prefix: {sys.prefix}")
    else:
        result.message = "Virtual environment bulunamadı"
        result.details.append("Sistem Python'u kullanılıyor")
        result.fixable = True
        result.fix_command = "python -m venv .venv && .venv\\Scripts\\activate"
    
    return result


def check_critical_packages() -> ValidationResult:
    """Kritik paket kontrolü."""
    result = ValidationResult("Critical Packages")
    
    try:
        # pip list kullan
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if proc.returncode == 0:
            packages = {
                pkg["name"].lower(): pkg["version"]
                for pkg in json.loads(proc.stdout)
            }
            
            missing = []
            installed = []
            
            for pkg in CRITICAL_PACKAGES:
                pkg_lower = pkg.lower()
                if pkg_lower in packages:
                    installed.append(f"{pkg}: {packages[pkg_lower]}")
                else:
                    missing.append(pkg)
            
            if missing:
                result.message = f"{len(missing)} kritik paket eksik"
                result.details = [f"Eksik: {', '.join(missing)}"]
                result.fixable = True
                result.fix_command = f"pip install {' '.join(missing)}"
            else:
                result.passed = True
                result.message = f"Tüm kritik paketler yüklü ({len(installed)})"
                result.details = installed
        else:
            result.message = "pip list çalıştırılamadı"
            result.details.append(proc.stderr)
    
    except Exception as e:
        result.message = f"Paket kontrolü başarısız: {e}"
    
    return result


def check_data_directories() -> ValidationResult:
    """Veri dizinleri kontrolü."""
    result = ValidationResult("Data Directories")
    
    missing = []
    created = []
    exists = []
    
    for dir_path in DATA_DIRS:
        full_path = SCRIPT_DIR / dir_path
        
        if full_path.exists():
            exists.append(dir_path)
        else:
            missing.append(dir_path)
    
    if missing:
        result.message = f"{len(missing)} dizin eksik"
        result.details = [f"Eksik: {', '.join(missing)}"]
        result.fixable = True
    else:
        result.passed = True
        result.message = f"Tüm dizinler mevcut ({len(exists)})"
    
    return result


def check_file_permissions() -> ValidationResult:
    """Dosya izinleri kontrolü."""
    result = ValidationResult("File Permissions")
    
    issues = []
    
    # Data dizininde yazma izni
    data_dir = SCRIPT_DIR / "data"
    if data_dir.exists():
        test_file = data_dir / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            issues.append(f"data/ dizininde yazma izni yok")
    
    # ChromaDB dosyası
    chroma_db = SCRIPT_DIR / "data" / "chroma_db" / "chroma.sqlite3"
    if chroma_db.exists():
        try:
            # Okuma testi
            with open(chroma_db, "rb") as f:
                f.read(16)
            
            # Yazma testi (dosya boyutunu değiştirmeden)
            os.access(chroma_db, os.W_OK)
        except PermissionError:
            issues.append("ChromaDB dosyasında yazma izni yok")
    
    if issues:
        result.message = f"{len(issues)} izin sorunu"
        result.details = issues
    else:
        result.passed = True
        result.message = "Dosya izinleri OK ✓"
    
    return result


def check_port_availability() -> ValidationResult:
    """Port kullanılabilirliği kontrolü."""
    result = ValidationResult("Port Availability")
    
    blocked = []
    available = []
    
    for port, service in REQUIRED_PORTS.items():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.bind(("127.0.0.1", port))
            sock.close()
            available.append(f"{port} ({service})")
        except OSError:
            # Port kullanımda - bu OK olabilir (servis zaten çalışıyor)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect(("127.0.0.1", port))
                sock.close()
                # Bağlantı başarılı = servis çalışıyor
                available.append(f"{port} ({service}) - aktif")
            except:
                blocked.append(f"{port} ({service})")
    
    if blocked:
        result.message = f"{len(blocked)} port kullanılamıyor"
        result.details = [f"Bloke: {', '.join(blocked)}"]
    else:
        result.passed = True
        result.message = f"Tüm portlar erişilebilir"
        result.details = available
    
    return result


def check_disk_space() -> ValidationResult:
    """Disk alanı kontrolü."""
    result = ValidationResult("Disk Space")
    
    try:
        total, used, free = shutil.disk_usage(SCRIPT_DIR)
        
        free_gb = free / (1024 ** 3)
        total_gb = total / (1024 ** 3)
        used_percent = (used / total) * 100
        
        result.details.append(f"Toplam: {total_gb:.1f} GB")
        result.details.append(f"Kullanılan: {used_percent:.1f}%")
        result.details.append(f"Boş: {free_gb:.1f} GB")
        
        if free < MIN_DISK_SPACE:
            result.message = f"Yetersiz disk alanı: {free_gb:.1f} GB"
        else:
            result.passed = True
            result.message = f"Yeterli disk alanı: {free_gb:.1f} GB boş"
    
    except Exception as e:
        result.message = f"Disk kontrolü başarısız: {e}"
    
    return result


def check_chromadb_integrity() -> ValidationResult:
    """ChromaDB veritabanı bütünlüğü kontrolü."""
    result = ValidationResult("ChromaDB Integrity")
    
    db_path = SCRIPT_DIR / "data" / "chroma_db" / "chroma.sqlite3"
    
    if not db_path.exists():
        result.passed = True
        result.message = "ChromaDB henüz oluşturulmamış (OK)"
        return result
    
    try:
        import sqlite3
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Integrity check
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result == "ok":
            # Tablo sayısı
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            )
            table_count = cursor.fetchone()[0]
            
            result.passed = True
            result.message = f"ChromaDB bütünlüğü OK ({table_count} tablo)"
            
            # Dosya boyutu
            size_mb = db_path.stat().st_size / (1024 * 1024)
            result.details.append(f"Boyut: {size_mb:.1f} MB")
        else:
            result.message = f"ChromaDB bozuk: {integrity_result}"
            result.fixable = True
            result.fix_command = "ChromaDB backup'tan geri yüklenebilir"
        
        conn.close()
    
    except ImportError:
        result.message = "sqlite3 modülü bulunamadı"
    except Exception as e:
        result.message = f"ChromaDB kontrolü başarısız: {e}"
        result.fixable = True
    
    return result


def check_ollama_service() -> ValidationResult:
    """Ollama servisi kontrolü."""
    result = ValidationResult("Ollama Service")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock_result = sock.connect_ex(("127.0.0.1", 11434))
        sock.close()
        
        if sock_result == 0:
            # Ollama çalışıyor, model listesi al
            try:
                import urllib.request
                
                req = urllib.request.Request(
                    "http://127.0.0.1:11434/api/tags",
                    headers={"Content-Type": "application/json"},
                )
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read())
                    models = [m["name"] for m in data.get("models", [])]
                    
                    if models:
                        result.passed = True
                        result.message = f"Ollama çalışıyor ({len(models)} model)"
                        result.details = models[:5]  # İlk 5 model
                    else:
                        result.message = "Ollama çalışıyor ama model yüklü değil"
                        result.fixable = True
                        result.fix_command = "ollama pull qwen3:8b"
            
            except Exception as e:
                result.passed = True  # Port açık = servis çalışıyor
                result.message = "Ollama çalışıyor"
                result.details.append(f"API kontrolü başarısız: {e}")
        else:
            result.message = "Ollama servisi çalışmıyor"
            result.fixable = True
            result.fix_command = "ollama serve"
    
    except Exception as e:
        result.message = f"Ollama kontrolü başarısız: {e}"
    
    return result


def check_environment_variables() -> ValidationResult:
    """Environment variable kontrolü."""
    result = ValidationResult("Environment Variables")
    
    # İsteğe bağlı env vars
    optional_vars = [
        "OLLAMA_HOST",
        "CHROMADB_HOST",
        "LOG_LEVEL",
    ]
    
    found = []
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            # Değeri gizle
            display = value[:10] + "..." if len(value) > 10 else value
            found.append(f"{var}={display}")
    
    result.passed = True  # Env vars opsiyonel
    
    if found:
        result.message = f"{len(found)} environment variable ayarlı"
        result.details = found
    else:
        result.message = "Varsayılan yapılandırma kullanılacak"
    
    return result


def check_nodejs_npm() -> ValidationResult:
    """Node.js ve npm kontrolü."""
    result = ValidationResult("Node.js & npm")
    
    try:
        # Node.js kontrolü
        node_result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True,
        )
        
        if node_result.returncode != 0:
            result.message = "Node.js kurulu değil"
            result.fixable = True
            result.fix_command = "https://nodejs.org adresinden indirin"
            return result
        
        node_version = node_result.stdout.strip()
        
        # npm kontrolü
        npm_result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True,
        )
        
        if npm_result.returncode != 0:
            result.message = f"Node.js {node_version} var ama npm bulunamadı"
            result.fixable = True
            result.fix_command = "Node.js'i yeniden kurun"
            return result
        
        npm_version = npm_result.stdout.strip()
        
        # Node version kontrolü
        try:
            major = int(node_version.lstrip('v').split('.')[0])
            if major < 16:
                result.message = f"Node.js {node_version} çok eski (min v16)"
                result.fixable = True
                result.fix_command = "Node.js LTS indirin: https://nodejs.org"
                return result
        except:
            pass
        
        result.passed = True
        result.message = f"Node.js {node_version}, npm {npm_version} ✓"
        
    except FileNotFoundError:
        result.message = "Node.js kurulu değil"
        result.fixable = True
        result.fix_command = "https://nodejs.org adresinden indirin"
    except Exception as e:
        result.message = f"Node.js kontrolü başarısız: {e}"
    
    return result


def check_nextjs_dependencies() -> ValidationResult:
    """Next.js bağımlılıkları kontrolü."""
    result = ValidationResult("Next.js Dependencies")
    
    nextjs_dir = SCRIPT_DIR / "frontend-next"
    node_modules = nextjs_dir / "node_modules"
    
    if not nextjs_dir.exists():
        result.passed = True
        result.message = "Next.js yapılandırılmamış (atlandı)"
        return result
    
    if not node_modules.exists():
        result.message = "node_modules eksik"
        result.fixable = True
        result.fix_command = "cd frontend-next && npm install"
        return result
    
    # Kritik paketler
    critical = ["next", "react", "react-dom", "socket.io-client"]
    missing = [pkg for pkg in critical if not (node_modules / pkg).exists()]
    
    if missing:
        result.message = f"Eksik paketler: {', '.join(missing)}"
        result.fixable = True
        result.fix_command = f"cd frontend-next && npm install {' '.join(missing)}"
        return result
    
    result.passed = True
    result.message = "Tüm Next.js bağımlılıkları mevcut ✓"
    result.details = [f"{len(critical)} kritik paket"]
    
    return result


# =============================================================================
# FIX FUNCTIONS
# =============================================================================

def fix_data_directories():
    """Eksik dizinleri oluştur."""
    created = []
    
    for dir_path in DATA_DIRS:
        full_path = SCRIPT_DIR / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
    
    return created


def fix_packages():
    """Eksik paketleri yükle."""
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=SCRIPT_DIR,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


# =============================================================================
# MAIN
# =============================================================================

def run_all_validations(quick: bool = False) -> list:
    """Tüm doğrulamaları çalıştır."""
    
    validations = [
        check_python_version,
        check_virtual_env,
        check_critical_packages,
        check_data_directories,
        check_file_permissions,
        check_disk_space,
    ]
    
    if not quick:
        validations.extend([
            check_port_availability,
            check_chromadb_integrity,
            check_ollama_service,
            check_nodejs_npm,
            check_nextjs_dependencies,
            check_environment_variables,
        ])
    
    results = []
    
    for validator in validations:
        try:
            result = validator()
            results.append(result)
        except Exception as e:
            result = ValidationResult(validator.__name__)
            result.message = f"Beklenmeyen hata: {e}"
            results.append(result)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise AI Assistant - Startup Validation"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Hızlı doğrulama (ağ kontrolleri atlanır)"
    )
    parser.add_argument(
        "--fix", "-f",
        action="store_true",
        help="Düzeltilebilir sorunları otomatik düzelt"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="JSON formatında çıktı"
    )
    
    args = parser.parse_args()
    
    if not args.json:
        print(header("🔍 Enterprise AI Assistant - Startup Validation"))
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📂 {SCRIPT_DIR}\n")
    
    # Doğrulamaları çalıştır
    results = run_all_validations(quick=args.quick)
    
    # Sonuçları göster
    passed = 0
    failed = 0
    fixable = []
    
    for result in results:
        if result.passed:
            passed += 1
            if not args.json:
                print(ok(f"{result.name}: {result.message}"))
        else:
            failed += 1
            if not args.json:
                print(err(f"{result.name}: {result.message}"))
            
            if result.fixable:
                fixable.append(result)
        
        # Detaylar
        if not args.json and result.details:
            for detail in result.details[:3]:
                print(f"   └─ {detail}")
    
    # Özet
    if args.json:
        output = {
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "failed": failed,
            "results": [r.to_dict() for r in results],
        }
        print(json.dumps(output, indent=2))
    else:
        print(header("📊 Özet"))
        print(f"  ✅ Başarılı: {passed}")
        print(f"  ❌ Başarısız: {failed}")
        print(f"  🔧 Düzeltilebilir: {len(fixable)}")
        
        # Otomatik düzeltme
        if args.fix and fixable:
            print(header("🔧 Otomatik Düzeltme"))
            
            for result in fixable:
                print(info(f"Düzeltiliyor: {result.name}..."))
                
                if result.name == "Data Directories":
                    created = fix_data_directories()
                    if created:
                        print(ok(f"Dizinler oluşturuldu: {', '.join(created)}"))
                
                elif result.name == "Critical Packages":
                    if fix_packages():
                        print(ok("Paketler yüklendi"))
                    else:
                        print(err("Paket yüklemesi başarısız"))
                
                elif result.fix_command:
                    print(info(f"Manuel düzeltme: {result.fix_command}"))
        
        # Final
        if failed == 0:
            print(header("🎉 Sistem çalıştırmaya hazır!"))
            print("  Çalıştırmak için: python run.py")
            return 0
        else:
            print(header("⚠️ Sorunlar çözülmeden sistem başlatılmamalı"))
            if not args.fix and fixable:
                print("  Otomatik düzeltme için: python validate_startup.py --fix")
            return 1


if __name__ == "__main__":
    sys.exit(main())
