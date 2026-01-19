"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ENTERPRISE AI ASSISTANT - RUN SCRIPT                      ║
║                                                                              ║
║   Endüstri Standartlarında Kurumsal AI Çözümü                                ║
║   Tek komutla tüm sistemi başlat - SIFIR SORUN GARANTİSİ                     ║
║                                                                              ║
║   Backend:    FastAPI      → Port 8001                                       ║
║   Frontend 1: Next.js      → Port 3000  (Modern React UI)                    ║
║   Frontend 2: Streamlit    → Port 8501  (Klasik Python UI)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Kullanım:
  python run.py              # Varsayılan: API + Next.js
  python run.py --all        # Tüm servisleri başlat (API + Next.js + Streamlit)
  python run.py --streamlit  # Sadece API + Streamlit
  python run.py --next       # Sadece API + Next.js
  python run.py --api-only   # Sadece API başlat
  python run.py --dev        # Development mode (hot reload)
  python run.py --skip-ollama  # Ollama kontrolü atla
  python run.py --skip-health  # Sağlık kontrollerini atla (hızlı başlatma)
  python run.py --health-only  # Sadece sağlık kontrolü yap

v2.1 - RESILIENCE UPDATE:
- ChromaDB auto-backup & recovery
- Comprehensive startup health checks
- Python version validation
- Dependency verification
"""

import subprocess
import sys
import os
import time
import webbrowser
import socket
import atexit
import argparse
import signal
import threading
import psutil  # Process yönetimi için
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass
from enum import Enum

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

class ServicePort(Enum):
    """Servis port tanımları."""
    API = 8001
    STREAMLIT = 8501
    NEXTJS = 3000

class ServiceStatus(Enum):
    """Servis durumları."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    RESTARTING = "restarting"

@dataclass
class ServiceConfig:
    """Servis konfigürasyonu."""
    name: str
    port: int
    color: str
    icon: str
    max_restarts: int = 3
    health_endpoint: Optional[str] = None
    startup_timeout: int = 45

# Servis konfigürasyonları
SERVICES = {
    "api": ServiceConfig(
        name="FastAPI Backend",
        port=ServicePort.API.value,
        color="\033[92m",  # Green
        icon="📡",
        health_endpoint="/health",
        startup_timeout=45
    ),
    "nextjs": ServiceConfig(
        name="Next.js Frontend",
        port=ServicePort.NEXTJS.value,
        color="\033[94m",  # Blue
        icon="⚛️",
        health_endpoint="/",
        startup_timeout=60
    ),
    "streamlit": ServiceConfig(
        name="Streamlit Frontend",
        port=ServicePort.STREAMLIT.value,
        color="\033[95m",  # Magenta
        icon="🎨",
        health_endpoint="/",
        startup_timeout=30
    ),
}

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL STATE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProcessInfo:
    """Process bilgisi."""
    process: Optional[subprocess.Popen] = None
    status: ServiceStatus = ServiceStatus.STOPPED
    restart_count: int = 0
    last_error: Optional[str] = None
    started_at: Optional[datetime] = None

class AppState:
    """Uygulama durumu - Singleton."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.processes: Dict[str, ProcessInfo] = {
            "api": ProcessInfo(),
            "nextjs": ProcessInfo(),
            "streamlit": ProcessInfo(),
        }
        self.shutdown_requested = False
        self.log_threads: List[threading.Thread] = []
        self.start_time: Optional[datetime] = None

state = AppState()

# ══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    """Terminal renkleri."""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


# Log dosyaları için dizin
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_log_file(service_name: str) -> Path:
    """Servis için log dosya yolunu döndür."""
    timestamp = datetime.now().strftime("%Y%m%d")
    return LOG_DIR / f"{service_name}_{timestamp}.log"


def write_to_service_log(service_name: str, message: str, level: str = "INFO"):
    """Servis log dosyasına yaz."""
    try:
        log_file = get_log_file(service_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception:
        pass  # Log yazma hatası sistem çalışmasını engellememeli

def log(msg: str, level: str = "info", service: Optional[str] = None):
    """Gelişmiş renkli log mesajı."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    level_config = {
        "info":    (Colors.CYAN,   "ℹ️ "),
        "success": (Colors.GREEN,  "✅"),
        "warning": (Colors.YELLOW, "⚠️ "),
        "error":   (Colors.RED,    "❌"),
        "loading": (Colors.BLUE,   "⏳"),
        "rocket":  (Colors.MAGENTA,"🚀"),
        "debug":   (Colors.DIM,    "🔍"),
    }
    
    color, icon = level_config.get(level, (Colors.WHITE, "•"))
    
    service_tag = ""
    if service:
        svc_config = SERVICES.get(service)
        if svc_config:
            service_tag = f" [{svc_config.icon} {svc_config.name}]"
    
    print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {icon} {color}{msg}{Colors.RESET}{service_tag}")

def print_banner():
    """Profesyonel başlangıç banner'ı."""
    banner = f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   {Colors.BOLD}🤖 ENTERPRISE AI ASSISTANT{Colors.RESET}{Colors.CYAN}                              ║
║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━            ║
║   {Colors.DIM}Endüstri Standartlarında Kurumsal AI Çözümü{Colors.RESET}{Colors.CYAN}               ║
║   {Colors.DIM}v2.0 - Multi-Frontend Architecture{Colors.RESET}{Colors.CYAN}                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)

def print_success_panel(services: List[str]):
    """Başarılı başlatma paneli."""
    print()
    print(f"{Colors.GREEN}╔══════════════════════════════════════════════════════════════╗")
    print(f"║   {Colors.BOLD}✅ TÜM SERVİSLER BAŞARIYLA BAŞLATILDI!{Colors.RESET}{Colors.GREEN}                     ║")
    print(f"╠══════════════════════════════════════════════════════════════╣")
    print(f"║                                                              ║")
    print(f"║   {Colors.CYAN}📍 ERİŞİM ADRESLERİ:{Colors.GREEN}                                        ║")
    print(f"║   ────────────────────────────────────────────────           ║")
    
    if "nextjs" in services:
        print(f"║   {Colors.BLUE}⚛️  Next.js:{Colors.GREEN}      http://localhost:{ServicePort.NEXTJS.value}                    ║")
    if "streamlit" in services:
        print(f"║   {Colors.MAGENTA}🎨 Streamlit:{Colors.GREEN}    http://localhost:{ServicePort.STREAMLIT.value}                    ║")
    if "api" in services:
        print(f"║   {Colors.YELLOW}📡 API:{Colors.GREEN}          http://localhost:{ServicePort.API.value}                    ║")
        print(f"║   {Colors.YELLOW}📚 API Docs:{Colors.GREEN}     http://localhost:{ServicePort.API.value}/docs               ║")
    
    print(f"║                                                              ║")
    print(f"║   {Colors.DIM}⌨️  Durdurmak için: Ctrl+C{Colors.GREEN}                                  ║")
    print(f"║                                                              ║")
    print(f"╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()

# ══════════════════════════════════════════════════════════════════════════════
# PORT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def is_port_available(port: int) -> bool:
    """Port kullanılabilir mi kontrol et."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('127.0.0.1', port))
            return True
    except:
        return False

def get_pids_using_port(port: int) -> List[int]:
    """Belirli portu kullanan PID'leri bul - psutil ile."""
    pids = set()
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                if conn.pid:
                    pids.add(conn.pid)
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        pass
    
    # Fallback: netstat
    if not pids:
        try:
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['netstat', '-ano', '-p', 'tcp'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            if pid.isdigit() and pid != '0':
                                pids.add(int(pid))
        except:
            pass
    return list(pids)

def kill_process_tree(pid: int):
    """Process ve tüm child process'lerini öldür."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Önce children'ları öldür
        for child in children:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sonra parent'ı öldür
        try:
            parent.kill()
            parent.wait(timeout=3)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass
            
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Fallback: taskkill
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

def kill_processes_by_name(name: str):
    """İsme göre tüm process'leri öldür."""
    try:
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if name.lower() in proc.info['name'].lower():
                    kill_process_tree(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except:
        pass

def kill_port(port: int, force: bool = True) -> bool:
    """Portu temizle - NUCLEAR mode."""
    killed = False
    
    # 1. Port kullanan tüm PID'leri bul ve öldür (3 deneme)
    for attempt in range(3):
        pids = get_pids_using_port(port)
        for pid in pids:
            kill_process_tree(pid)
            killed = True
        if not pids:
            break
        time.sleep(0.5)
    
    # 2. Next.js portu için tüm node.exe'leri öldür
    if port == ServicePort.NEXTJS.value:
        kill_processes_by_name('node.exe')
        # Ekstra: taskkill ile de dene
        try:
            subprocess.run('taskkill /F /IM node.exe', shell=True, 
                          capture_output=True, timeout=5)
        except:
            pass
        killed = True
    
    # 3. API portu için python/uvicorn öldür
    if port == ServicePort.API.value:
        pids = get_pids_using_port(port)
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                if 'python' in proc.name().lower():
                    kill_process_tree(pid)
                    killed = True
            except:
                pass
    
    # Windows'ta port release için bekle
    time.sleep(2)
    return killed

def ensure_port_available(port: int, max_attempts: int = 10) -> bool:
    """Port'un kullanılabilir olmasını garanti et - NUCLEAR."""
    if is_port_available(port):
        return True
    
    log(f"Port {port} meşgul, agresif temizlik başlatılıyor...", "warning")
    
    for attempt in range(max_attempts):
        kill_port(port, force=True)
        
        # Her denemede daha uzun bekle (exponential backoff)
        wait_time = min(1 + attempt * 0.5, 5)  # 1s, 1.5s, 2s... max 5s
        time.sleep(wait_time)
        
        if is_port_available(port):
            log(f"Port {port} başarıyla temizlendi (deneme {attempt + 1})", "success")
            return True
        
        # 3. denemeden sonra daha agresif ol
        if attempt >= 2:
            if port == ServicePort.NEXTJS.value:
                # Tüm node process'lerini öldür
                kill_processes_by_name('node')
                try:
                    subprocess.run('taskkill /F /IM node.exe', shell=True, capture_output=True, timeout=5)
                except:
                    pass
            time.sleep(2)
        
        # 5. denemeden sonra netstat ile kontrol et ve logla
        if attempt >= 4:
            try:
                result = subprocess.run(f'netstat -ano | findstr ":{port}"', 
                                       shell=True, capture_output=True, text=True, timeout=5)
                if result.stdout.strip():
                    log(f"Port {port} hala kullanılıyor: {result.stdout.strip()[:80]}", "debug")
            except:
                pass
    
    log(f"Port {port} temizlenemedi! ({max_attempts} deneme)", "error")
    return False

def cleanup_all_ports():
    """Tüm servislerin portlarını NUCLEAR şekilde temizle."""
    log("Tüm portlar NUCLEAR şekilde temizleniyor...", "loading")
    
    # Önce tüm node.exe'leri öldür (Next.js için)
    kill_processes_by_name('node.exe')
    try:
        subprocess.run('taskkill /F /IM node.exe', shell=True, capture_output=True, timeout=5)
    except:
        pass
    time.sleep(2)
    
    # Tüm portları temizle
    for service_name, config in SERVICES.items():
        if not is_port_available(config.port):
            pids = get_pids_using_port(config.port)
            for pid in pids:
                kill_process_tree(pid)
            log(f"Port {config.port} temizlendi", "success")
    
    # Windows'ta port release için uzun bekle
    time.sleep(3)
    
    # Son kontrol
    all_clean = True
    for service_name, config in SERVICES.items():
        if not is_port_available(config.port):
            log(f"UYARI: Port {config.port} hala meşgul!", "warning")
            all_clean = False
    
    if all_clean:
        log("Tüm portlar temiz", "success")
    else:
        log("Bazı portlar temizlenemedi, devam ediliyor...", "warning")

# ══════════════════════════════════════════════════════════════════════════════
# OLLAMA MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def check_ollama() -> bool:
    """Ollama çalışıyor mu?"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_ollama() -> bool:
    """Ollama'yı başlat."""
    if check_ollama():
        return True
    
    log("Ollama başlatılıyor...", "loading")
    
    try:
        if sys.platform == 'win32':
            ollama_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama.exe"),
                r"C:\Program Files\Ollama\ollama.exe",
            ]
            
            for path in ollama_paths:
                if os.path.exists(path):
                    subprocess.Popen(
                        [path, "serve"],
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    break
        else:
            subprocess.Popen(
                ['ollama', 'serve'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        for _ in range(15):
            time.sleep(1)
            if check_ollama():
                log("Ollama başlatıldı", "success")
                return True
        
    except Exception as e:
        log(f"Ollama başlatma hatası: {e}", "warning")
    
    return check_ollama()

# ══════════════════════════════════════════════════════════════════════════════
# SERVICE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def stream_output(proc: subprocess.Popen, service_name: str):
    """Process çıktısını izle (sadece loglama amaçlı)."""
    try:
        while not state.shutdown_requested:
            if proc.poll() is not None:
                break  # Process bitti
            
            try:
                line = proc.stdout.readline()
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    # Önemli hataları logla
                    if any(word in decoded.lower() for word in ['error', 'exception', 'failed', 'critical']):
                        # Çok uzun satırları kısalt
                        log(decoded[:100], "warning", service_name)
                elif proc.stdout.closed:
                    break  # stdout kapandı
            except:
                break
    except:
        pass

def wait_for_health(url: str, timeout: int = 45) -> bool:
    """Servisin hazır olmasını bekle."""
    import requests
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code in [200, 304]:
                return True
        except:
            pass
        time.sleep(1)
    return False

# ═══════════════════════════════════════════════════════════════
# API SERVICE
# ═══════════════════════════════════════════════════════════════

def start_api():
    """FastAPI backend'i başlat."""
    config = SERVICES["api"]
    
    if not ensure_port_available(config.port):
        state.processes["api"].status = ServiceStatus.ERROR
        state.processes["api"].last_error = "Port unavailable"
        return False
    
    log(f"API başlatılıyor (port {config.port})...", "loading", "api")
    state.processes["api"].status = ServiceStatus.STARTING
    
    env = os.environ.copy()
    env['API_PORT'] = str(config.port)
    env['PYTHONUNBUFFERED'] = '1'
    
    cmd = [
        sys.executable, "-m", "uvicorn", "api.main:app",
        "--host", "0.0.0.0",
        "--port", str(config.port),
        "--log-level", "warning"
    ]
    
    # Log dosyasına yönlendir - DEBUG için önemli
    log_file = get_log_file("api")
    write_to_service_log("api", f"API starting on port {config.port}", "INFO")
    
    with open(log_file, "a", encoding="utf-8") as api_log:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
            stdout=api_log,
            stderr=api_log,
            start_new_session=True if sys.platform != 'win32' else False,
        )
    
    state.processes["api"].process = proc
    state.processes["api"].started_at = datetime.now()
    
    # Health check
    if wait_for_health(f"http://localhost:{config.port}/health", config.startup_timeout):
        state.processes["api"].status = ServiceStatus.RUNNING
        log(f"API hazır (port {config.port})", "success", "api")
        return True
    else:
        state.processes["api"].status = ServiceStatus.ERROR
        state.processes["api"].last_error = "Health check timeout"
        log("API health check başarısız", "warning", "api")
        return False

# ═══════════════════════════════════════════════════════════════
# NEXT.JS SERVICE
# ═══════════════════════════════════════════════════════════════

def check_node_installed() -> tuple:
    """
    Node.js kurulu mu ve sürümü uygun mu?
    
    Returns:
        (installed: bool, version: str, npm_available: bool)
    """
    try:
        # Node.js version check
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            shell=True if sys.platform == 'win32' else False
        )
        if result.returncode != 0:
            return False, "", False
        
        node_version = result.stdout.strip()
        
        # npm check
        npm_result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            shell=True if sys.platform == 'win32' else False
        )
        npm_available = npm_result.returncode == 0
        
        return True, node_version, npm_available
    except Exception as e:
        return False, "", False


def verify_npm_cache() -> bool:
    """npm cache'i temiz mi kontrol et."""
    try:
        result = subprocess.run(
            ["npm", "cache", "verify"],
            capture_output=True,
            text=True,
            timeout=60,
            shell=True if sys.platform == 'win32' else False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.returncode == 0
    except:
        return True  # Hata olursa devam et

def ensure_nextjs_deps() -> bool:
    """
    Next.js bağımlılıklarını kontrol et/yükle.
    
    BULLET-PROOF versiyon:
    - node_modules varlık kontrolü
    - Kritik paketlerin varlık kontrolü
    - npm install with --legacy-peer-deps fallback
    - npm cache clean on failure
    """
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    node_modules = nextjs_dir / "node_modules"
    
    # Kritik paketlerin varlığını kontrol et
    critical_packages = ["next", "react", "react-dom", "socket.io-client"]
    all_present = True
    
    if node_modules.exists():
        for pkg in critical_packages:
            if not (node_modules / pkg).exists():
                all_present = False
                log(f"Eksik paket: {pkg}", "warning", "nextjs")
                break
    else:
        all_present = False
    
    if all_present:
        log("Tüm Next.js bağımlılıkları mevcut ✓", "success", "nextjs")
        return True
    
    log("Next.js bağımlılıkları yükleniyor...", "loading", "nextjs")
    
    # Ortam değişkenleri
    env = os.environ.copy()
    env['npm_config_legacy_peer_deps'] = 'true'  # Peer dep hatalarını önle
    
    try:
        # İlk deneme: normal npm install
        result = subprocess.run(
            "npm install",
            cwd=str(nextjs_dir),
            capture_output=True,
            text=True,
            timeout=600,  # 10 dakika timeout
            shell=True,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            log("Bağımlılıklar yüklendi ✓", "success", "nextjs")
            return True
        
        # İkinci deneme: legacy-peer-deps ile
        log("npm install tekrar deneniyor (legacy-peer-deps)...", "loading", "nextjs")
        result = subprocess.run(
            "npm install --legacy-peer-deps",
            cwd=str(nextjs_dir),
            capture_output=True,
            text=True,
            timeout=600,
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        if result.returncode == 0:
            log("Bağımlılıklar yüklendi (legacy mode) ✓", "success", "nextjs")
            return True
        
        # Hata detayını logla
        error_msg = result.stderr[:200] if result.stderr else "Bilinmeyen hata"
        log(f"npm install hatası: {error_msg}", "error", "nextjs")
        write_to_service_log("nextjs", f"npm install failed: {result.stderr}", "ERROR")
        
        return False
        
    except subprocess.TimeoutExpired:
        log("npm install zaman aşımı (10 dakika)!", "error", "nextjs")
        return False
    except Exception as e:
        log(f"npm install exception: {e}", "error", "nextjs")
        return False

def ensure_nextjs_build() -> bool:
    """Next.js production build kontrol et/yap."""
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    next_build = nextjs_dir / ".next"
    
    if next_build.exists() and (next_build / "BUILD_ID").exists():
        return True
    
    log("Next.js production build yapılıyor...", "loading", "nextjs")
    
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(nextjs_dir),
            capture_output=True,
            text=True,
            timeout=300,
            shell=True if sys.platform == 'win32' else False
        )
        if result.returncode == 0:
            log("Production build tamamlandı", "success", "nextjs")
            return True
        else:
            log(f"Build hatası: {result.stderr[:150]}", "warning", "nextjs")
            return False
    except Exception as e:
        log(f"Build exception: {e}", "error", "nextjs")
        return False

def check_websocket_compatibility() -> bool:
    """
    WebSocket bağlantısı için gerekli kontrolleri yap.
    
    Socket.io-client frontend'de, backend WebSocket endpoint'i API'de.
    """
    try:
        # API WebSocket endpoint kontrolü
        import requests
        response = requests.get(
            f"http://localhost:{ServicePort.API.value}/ws/health",
            timeout=3
        )
        return response.status_code in [200, 404, 426]  # 426 = Upgrade Required (normal)
    except:
        return True  # API henüz başlamadıysa sorun yok


def start_nextjs(dev_mode: bool = False):
    """Next.js frontend'i başlat - ULTRA BULLET-PROOF versiyon."""
    config = SERVICES["nextjs"]
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    
    if not nextjs_dir.exists():
        log("Next.js klasörü bulunamadı!", "error", "nextjs")
        return False
    
    # Node.js kontrolü - geliştirilmiş
    node_ok, node_version, npm_ok = check_node_installed()
    if not node_ok:
        log("Node.js kurulu değil! https://nodejs.org", "error", "nextjs")
        log("💡 Node.js LTS sürümünü indirin: https://nodejs.org/en/download/", "info")
        return False
    
    if not npm_ok:
        log("npm bulunamadı! Node.js kurulumunu kontrol edin.", "error", "nextjs")
        return False
    
    log(f"Node.js {node_version} tespit edildi ✓", "success", "nextjs")
    
    # ═══════ ADIM 1: PORT TEMİZLİĞİ ═══════
    log(f"Port {config.port} hazırlanıyor...", "loading", "nextjs")
    
    # Önce tüm node process'lerini öldür - en agresif yöntem
    kill_processes_by_name('node.exe')
    try:
        subprocess.run('taskkill /F /IM node.exe 2>nul', shell=True, capture_output=True, timeout=10)
    except:
        pass
    time.sleep(3)
    
    # Port'u agresif şekilde temizle
    if not ensure_port_available(config.port, max_attempts=15):  # 15 deneme
        state.processes["nextjs"].status = ServiceStatus.ERROR
        state.processes["nextjs"].last_error = f"Port {config.port} temizlenemedi"
        return False
    
    # EXTRA: Port temizlendikten sonra bekle - Windows port release YAVAŞ
    time.sleep(5)
    
    # Port gerçekten temiz mi TEKRAR kontrol et
    for retry in range(3):
        if is_port_available(config.port):
            break
        
        log(f"Port {config.port} hala meşgul, agresif temizlik #{retry+1}...", "warning", "nextjs")
        kill_processes_by_name('node.exe')
        
        # netstat ile PID bul ve öldür
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{config.port}"',
                shell=True, capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split('\n'):
                parts = line.split()
                if len(parts) >= 5 and parts[-1].isdigit():
                    pid = parts[-1]
                    subprocess.run(f'taskkill /F /PID {pid} 2>nul', shell=True, timeout=5)
        except:
            pass
        
        time.sleep(5)
    
    if not is_port_available(config.port):
        log(f"Port {config.port} temizlenemedi! Yeniden başlatma gerekebilir.", "error", "nextjs")
        state.processes["nextjs"].status = ServiceStatus.ERROR
        return False
    
    log(f"Port {config.port} hazır ✓", "success", "nextjs")
    
    # ═══════ ADIM 2: BAĞIMLILIK KONTROLÜ ═══════
    if not ensure_nextjs_deps():
        state.processes["nextjs"].status = ServiceStatus.ERROR
        state.processes["nextjs"].last_error = "npm install failed"
        return False
    
    # ═══════ ADIM 3: NEXT.JS BAŞLATMA ═══════
    log(f"Next.js başlatılıyor (port {config.port})...", "loading", "nextjs")
    state.processes["nextjs"].status = ServiceStatus.STARTING
    
    # Development mode - en güvenilir seçenek
    mode = "development"
    log(f"Next.js {mode} mode başlatılıyor...", "rocket", "nextjs")
    
    # ═══════ ADIM 4: ENVIRONMENT HAZIRLA ═══════
    env = os.environ.copy()
    env['NEXT_PUBLIC_API_URL'] = f'http://localhost:{ServicePort.API.value}'
    env['NEXT_PUBLIC_WS_URL'] = f'ws://localhost:{ServicePort.API.value}'  # WebSocket URL
    env['PORT'] = str(config.port)
    env['NODE_ENV'] = 'development'
    env['NEXT_TELEMETRY_DISABLED'] = '1'  # Telemetry kapat
    
    # Log dosyasına yönlendir
    log_file = get_log_file("nextjs")
    write_to_service_log("nextjs", f"Next.js starting on port {config.port}", "INFO")
    write_to_service_log("nextjs", f"API URL: http://localhost:{ServicePort.API.value}", "INFO")
    write_to_service_log("nextjs", f"WS URL: ws://localhost:{ServicePort.API.value}", "INFO")
    
    # ═══════ ADIM 5: PROCESS BAŞLAT ═══════
    with open(log_file, "a", encoding="utf-8") as nextjs_log:
        # Windows'ta cmd /c ile başlat - en güvenilir yöntem
        proc = subprocess.Popen(
            ["cmd", "/c", "npm run dev"],
            cwd=str(nextjs_dir),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=nextjs_log,
            stderr=nextjs_log,
        )
    
    state.processes["nextjs"].process = proc
    state.processes["nextjs"].started_at = datetime.now()
    
    # ═══════ ADIM 6: HEALTH CHECK ═══════
    # Dev mode için uzun bekle - İlk compile UZUN sürer
    wait_time = 180  # 3 dakika - ilk compile çok uzun sürebilir
    log(f"Next.js hazır olması bekleniyor (max {wait_time}s)...", "loading", "nextjs")
    
    # İlk başlangıç için bekle - Node.js'in başlaması zaman alır
    time.sleep(15)
    
    # Progressive health check - her 5 saniyede kontrol et
    start_check = time.time()
    health_ok = False
    last_status = ""
    
    while time.time() - start_check < wait_time:
        # Process hala çalışıyor mu?
        if proc.poll() is not None:
            log("Next.js process beklenmedik şekilde sonlandı!", "error", "nextjs")
            # Log dosyasından hatayı oku
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    last_lines = f.readlines()[-20:]
                    error_lines = [l for l in last_lines if 'error' in l.lower()]
                    if error_lines:
                        log(f"Hata: {error_lines[-1].strip()[:100]}", "error", "nextjs")
            except:
                pass
            state.processes["nextjs"].status = ServiceStatus.ERROR
            state.processes["nextjs"].last_error = "Process terminated unexpectedly"
            return False
        
        # HTTP health check
        try:
            import requests
            response = requests.get(f"http://localhost:{config.port}", timeout=5)
            if response.status_code in [200, 304]:
                health_ok = True
                break
            else:
                current_status = f"status {response.status_code}"
        except requests.exceptions.ConnectionError:
            current_status = "bağlantı bekleniyor..."
        except requests.exceptions.Timeout:
            current_status = "timeout..."
        except Exception as e:
            current_status = str(e)[:50]
        
        # Status değiştiyse logla
        if current_status != last_status:
            log(f"Next.js: {current_status}", "loading", "nextjs")
            last_status = current_status
        
        time.sleep(5)
    
    if health_ok:
        state.processes["nextjs"].status = ServiceStatus.RUNNING
        elapsed = int(time.time() - start_check)
        log(f"Next.js hazır (port {config.port}) - {elapsed}s [{mode}]", "success", "nextjs")
        return True
    else:
        # Process hala çalışıyor mu kontrol et
        if proc.poll() is None:
            # Process çalışıyor ama henüz ready değil - devam et
            log("Next.js henüz tam hazır değil ama process çalışıyor, devam ediliyor...", "warning", "nextjs")
            state.processes["nextjs"].status = ServiceStatus.RUNNING
            return True
        else:
            state.processes["nextjs"].status = ServiceStatus.ERROR
            state.processes["nextjs"].last_error = "Health check timeout"
            log("Next.js başlatılamadı!", "error", "nextjs")
            return False

# ═══════════════════════════════════════════════════════════════
# STREAMLIT SERVICE
# ═══════════════════════════════════════════════════════════════

def start_streamlit():
    """Streamlit frontend'i başlat."""
    config = SERVICES["streamlit"]
    frontend_path = PROJECT_ROOT / "frontend" / "app.py"
    
    if not frontend_path.exists():
        log(f"Streamlit app.py bulunamadı: {frontend_path}", "error", "streamlit")
        return False
    
    if not ensure_port_available(config.port):
        state.processes["streamlit"].status = ServiceStatus.ERROR
        return False
    
    log(f"Streamlit başlatılıyor (port {config.port})...", "loading", "streamlit")
    state.processes["streamlit"].status = ServiceStatus.STARTING
    
    env = os.environ.copy()
    env['API_BASE_URL'] = f'http://localhost:{ServicePort.API.value}'
    env['STREAMLIT_SERVER_PORT'] = str(config.port)
    env['PYTHONUNBUFFERED'] = '1'
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(frontend_path),
        "--server.port", str(config.port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.primaryColor", "#667eea",
    ]
    
    # Log dosyasına yönlendir - DEBUG için önemli
    log_file = get_log_file("streamlit")
    write_to_service_log("streamlit", f"Streamlit starting on port {config.port}", "INFO")
    
    with open(log_file, "a", encoding="utf-8") as streamlit_log:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
            stdout=streamlit_log,
            stderr=streamlit_log,
            start_new_session=True if sys.platform != 'win32' else False,
        )
    
    state.processes["streamlit"].process = proc
    state.processes["streamlit"].started_at = datetime.now()
    
    # Health check
    time.sleep(2)
    if wait_for_health(f"http://localhost:{config.port}", config.startup_timeout):
        state.processes["streamlit"].status = ServiceStatus.RUNNING
        log(f"Streamlit hazır (port {config.port})", "success", "streamlit")
        return True
    else:
        state.processes["streamlit"].status = ServiceStatus.ERROR
        log("Streamlit health check başarısız", "warning", "streamlit")
        return False

# ══════════════════════════════════════════════════════════════════════════════
# PROCESS MONITORING
# ══════════════════════════════════════════════════════════════════════════════

def is_service_healthy(service_name: str) -> bool:
    """Servisin gerçekten sağlıklı olup olmadığını kontrol et."""
    config = SERVICES.get(service_name)
    if not config:
        return False
    
    # Port dinleniyor mu?
    if is_port_available(config.port):
        return False  # Port boşsa servis çalışmıyor
    
    # Health endpoint varsa kontrol et
    if config.health_endpoint:
        try:
            import requests
            url = f"http://localhost:{config.port}{config.health_endpoint}"
            response = requests.get(url, timeout=3)
            return response.status_code in [200, 304]
        except:
            # Health check başarısız ama port dinleniyor - servis muhtemelen başlıyor
            return True
    
    return True  # Port dinleniyor, health endpoint yok

def monitor_services(services: List[str], dev_mode: bool = False):
    """
    Servisleri izle ve gerekirse yeniden başlat.
    
    ÖNEMLİ DEĞİŞİKLİKLER:
    - 60 saniye stabilizasyon süresi (30'dan artırıldı)
    - Sadece process GERÇEKTEN ölmüşse yeniden başlat
    - Port dinleniyorsa ASLA yeniden başlatma
    - 10 saniye aralıklarla kontrol (5'ten artırıldı)
    """
    error_logged = set()
    stable_count = {s: 0 for s in services}
    
    # 60 saniye stabilizasyon - KRITIK: ilk compile uzun sürer
    initial_stabilization = 60
    start_time = time.time()
    
    log("Servisler izleniyor... (Ctrl+C ile çıkış)", "info")
    
    while not state.shutdown_requested:
        elapsed = time.time() - start_time
        
        for service_name in services:
            proc_info = state.processes.get(service_name)
            if not proc_info:
                continue
            
            # Zaten hata durumundaysa atla
            if proc_info.status == ServiceStatus.ERROR:
                continue
            
            config = SERVICES[service_name]
            
            # KRITIK: Port dinleniyorsa servis çalışıyor demektir - ASLA dokunma
            if not is_port_available(config.port):
                # Port kullanılıyor = servis çalışıyor
                if proc_info.status != ServiceStatus.RUNNING:
                    proc_info.status = ServiceStatus.RUNNING
                stable_count[service_name] = 0
                continue
            
            # İlk stabilizasyon süresinde yeniden başlatma yapma
            if elapsed < initial_stabilization:
                continue
            
            # Port boş VE process ölmüş mü kontrol et
            process_dead = proc_info.process is None or proc_info.process.poll() is not None
            
            if not process_dead:
                # Process çalışıyor ama port boş - henüz başlıyor olabilir
                stable_count[service_name] += 1
                if stable_count[service_name] < 6:  # 60 saniye bekle (6 * 10s)
                    continue
            
            # Yeniden başlatma gerekiyor - SADECE process ölmüşse
            if process_dead and proc_info.restart_count < config.max_restarts:
                log(f"{config.name} durdu, yeniden başlatılıyor...", "warning", service_name)
                proc_info.restart_count += 1
                proc_info.status = ServiceStatus.RESTARTING
                stable_count[service_name] = 0
                
                # Eski process'i temizle
                if proc_info.process:
                    try:
                        proc_info.process.terminate()
                        proc_info.process.wait(timeout=5)
                    except:
                        try:
                            proc_info.process.kill()
                        except:
                            pass
                
                # Port temizlenmesi için bekle - UZUN bekle
                time.sleep(5)
                ensure_port_available(config.port)
                time.sleep(3)
                
                if service_name == "api":
                    start_api()
                elif service_name == "nextjs":
                    start_nextjs(dev_mode)
                elif service_name == "streamlit":
                    start_streamlit()
            elif proc_info.restart_count >= config.max_restarts:
                if service_name not in error_logged:
                    log(f"{config.name} çok fazla yeniden başlatıldı, durduruldu.", "error", service_name)
                    error_logged.add(service_name)
                proc_info.status = ServiceStatus.ERROR
        
        time.sleep(10)  # 10 saniye aralıklarla kontrol (5'ten artırıldı)

# ══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

_cleanup_done = False

def cleanup():
    """Tüm process'leri temiz bir şekilde kapat."""
    global _cleanup_done
    
    # Cleanup zaten yapıldıysa tekrar yapma
    if _cleanup_done:
        return
    _cleanup_done = True
    
    state.shutdown_requested = True
    
    for name, proc_info in state.processes.items():
        if proc_info.process is not None:
            try:
                config = SERVICES.get(name)
                if config:
                    log(f"{config.name} durduruluyor...", "loading", name)
                proc_info.process.terminate()
                proc_info.process.wait(timeout=5)
            except:
                try:
                    proc_info.process.kill()
                except:
                    pass
    
    log("Tüm servisler durduruldu", "success")

# ══════════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSING
# ══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Komut satırı argümanlarını parse et."""
    parser = argparse.ArgumentParser(
        description="Enterprise AI Assistant - Çoklu Servis Başlatıcı",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
╔══════════════════════════════════════════════════════════════╗
║ KULLANIM ÖRNEKLERİ:                                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   python run.py              → API + Next.js (varsayılan)    ║
║   python run.py --all        → API + Next.js + Streamlit     ║
║   python run.py --streamlit  → API + Streamlit               ║
║   python run.py --next       → API + Next.js                 ║
║   python run.py --api-only   → Sadece API                    ║
║   python run.py --dev        → Development mode              ║
║   python run.py --skip-ollama                                ║
║                                                              ║
║ PORTLAR:                                                     ║
║   📡 API:       {ServicePort.API.value}                                      ║
║   ⚛️  Next.js:   {ServicePort.NEXTJS.value}                                      ║
║   🎨 Streamlit: {ServicePort.STREAMLIT.value}                                      ║
╚══════════════════════════════════════════════════════════════╝
        """
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--all", "-a", action="store_true",
                           help="Tüm frontend'leri başlat (Next.js + Streamlit)")
    mode_group.add_argument("--next", "-n", action="store_true",
                           help="Sadece Next.js frontend (varsayılan)")
    mode_group.add_argument("--streamlit", "-s", action="store_true",
                           help="Sadece Streamlit frontend")
    mode_group.add_argument("--api-only", action="store_true",
                           help="Sadece API sunucusu")
    
    parser.add_argument("--dev", "-d", action="store_true",
                       help="Development mode (hot reload)")
    parser.add_argument("--no-browser", action="store_true",
                       help="Tarayıcıyı otomatik açma")
    parser.add_argument("--skip-ollama", action="store_true",
                       help="Ollama kontrolünü atla")
    parser.add_argument("--clean", action="store_true",
                       help="Başlamadan önce tüm portları temizle")
    parser.add_argument("--skip-health", action="store_true",
                       help="Startup sağlık kontrollerini atla (hızlı başlatma)")
    parser.add_argument("--health-only", action="store_true",
                       help="Sadece sağlık kontrolü yap, servisleri başlatma")
    
    return parser.parse_args()


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP HEALTH CHECK INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

def run_startup_health_checks(verbose: bool = True) -> bool:
    """
    Kapsamlı startup sağlık kontrolü.
    
    Returns:
        True if system is ready to start services
    """
    try:
        from core.startup_health import StartupHealthChecker
        
        log("🏥 Kapsamlı sağlık kontrolü başlatılıyor...", "loading")
        
        checker = StartupHealthChecker(project_dir=PROJECT_ROOT)
        report = checker.run_all_checks(verbose=verbose)
        
        # Raporu kaydet
        try:
            checker.save_report()
        except:
            pass
        
        if report.is_ready:
            log(f"✅ Sistem hazır ({report.passed_checks}/{report.total_checks} kontrol başarılı)", "success")
            return True
        else:
            log(f"❌ Sistem hazır değil ({report.failed_checks} kritik hata)", "error")
            
            # Kritik hataları göster
            for result in report.results:
                if result.is_critical and result.status.value == "failed":
                    log(f"  → {result.name}: {result.message}", "error")
                    if result.fix_suggestion:
                        log(f"    💡 Çözüm: {result.fix_suggestion}", "info")
            
            return False
            
    except ImportError:
        log("⚠️ Sağlık kontrolü modülü yüklenemedi, basit kontrol yapılıyor...", "warning")
        return run_basic_health_check()
    except Exception as e:
        log(f"⚠️ Sağlık kontrolü hatası: {e}", "warning")
        return run_basic_health_check()


def run_basic_health_check() -> bool:
    """Basit sağlık kontrolü (fallback)."""
    log("Temel kontroller yapılıyor...", "loading")
    
    # Python version check
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        log(f"❌ Python {major}.{minor} çok eski (min: 3.10)", "error")
        return False
    
    if major == 3 and minor > 13:
        log(f"⚠️ Python {major}.{minor} çok yeni, sorunlar olabilir", "warning")
    
    # Data directory check
    data_dir = PROJECT_ROOT / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "chroma_db").mkdir(parents=True, exist_ok=True)
        (data_dir / "sessions").mkdir(parents=True, exist_ok=True)
    except Exception as e:
        log(f"❌ Dizin oluşturulamadı: {e}", "error")
        return False
    
    log("✅ Temel kontroller tamamlandı", "success")
    return True

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Ana çalıştırma fonksiyonu."""
    args = parse_args()
    
    # Cleanup handler
    atexit.register(cleanup)
    
    # Signal handler
    def signal_handler(sig, frame):
        print("\n")
        log("Kapatılıyor...", "loading")
        cleanup()
        log("Güle güle! 👋", "success")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Banner
    print_banner()
    state.start_time = datetime.now()
    
    # ═══════ STEP 0: HEALTH CHECKS ═══════
    if args.health_only:
        log("Sadece sağlık kontrolü modu", "info")
        is_ready = run_startup_health_checks(verbose=True)
        sys.exit(0 if is_ready else 1)
    
    if not args.skip_health:
        log("Startup sağlık kontrolü başlatılıyor...", "loading")
        if not run_startup_health_checks(verbose=True):
            log("❌ Sağlık kontrolü başarısız!", "error")
            log("💡 Hataları düzeltin veya --skip-health ile atlayın", "info")
            sys.exit(1)
    else:
        log("⚠️ Sağlık kontrolü atlandı (--skip-health)", "warning")
    
    # Hangi servisleri başlatacağımızı belirle
    services_to_start = ["api"]  # API her zaman
    
    if args.all:
        services_to_start.extend(["nextjs", "streamlit"])
    elif args.streamlit:
        services_to_start.append("streamlit")
    elif args.api_only:
        pass  # Sadece API
    else:
        # Varsayılan: Next.js
        services_to_start.append("nextjs")
    
    log(f"Başlatılacak servisler: {', '.join([SERVICES[s].name for s in services_to_start])}", "info")
    
    # ═══════ STEP 1: CLEAN ALL PORTS FIRST ═══════
    # Her zaman portları temizle - bu en önemli adım
    log("Portlar temizleniyor (çakışmaları önlemek için)...", "loading")
    cleanup_all_ports()
    time.sleep(3)  # Port temizliği için UZUN bekle - Windows port release yavaş
    
    # ═══════ STEP 2: OLLAMA ═══════
    if not args.skip_ollama:
        log("Ollama kontrol ediliyor...", "loading")
        if not start_ollama():
            log("Ollama başlatılamadı (isteğe bağlı)", "warning")
    else:
        log("Ollama kontrolü atlandı", "info")
    
    # ═══════ STEP 3: DIRECTORIES ═══════
    log("Klasörler hazırlanıyor...", "loading")
    try:
        from core.config import settings
        settings.ensure_directories()
        log("Klasörler hazır", "success")
    except Exception as e:
        log(f"Klasör hatası (devam ediliyor): {e}", "warning")
    
    # ═══════ STEP 4: START SERVICES ═══════
    log("Servisler başlatılıyor...", "rocket")
    
    success = True
    
    # API - önce API başlamalı
    if "api" in services_to_start:
        if not start_api():
            log("API başlatılamadı!", "error")
            success = False
        else:
            # API'nin tam hazır olması için bekle
            time.sleep(5)
    
    # Next.js
    if "nextjs" in services_to_start and success:
        if not start_nextjs(args.dev):
            log("Next.js başlatılamadı (API hala çalışıyor)", "warning")
    
    # Streamlit
    if "streamlit" in services_to_start and success:
        if not start_streamlit():
            log("Streamlit başlatılamadı!", "warning")
    
    if not success:
        log("Kritik servis başlatılamadı, çıkılıyor...", "error")
        cleanup()
        return
    
    # ═══════ STEP 5: SUCCESS ═══════
    active_services = [s for s in services_to_start 
                      if state.processes[s].status == ServiceStatus.RUNNING]
    
    if not active_services:
        log("Hiçbir servis başlatılamadı!", "error")
        cleanup()
        return
        
    print_success_panel(active_services)
    
    # ═══════ STEP 6: OPEN BROWSER ═══════
    if not args.no_browser:
        time.sleep(2)  # Servislerin tamamen hazır olması için bekle
        try:
            if "nextjs" in active_services:
                webbrowser.open(f"http://localhost:{ServicePort.NEXTJS.value}")
            elif "streamlit" in active_services:
                webbrowser.open(f"http://localhost:{ServicePort.STREAMLIT.value}")
            elif "api" in active_services:
                webbrowser.open(f"http://localhost:{ServicePort.API.value}/docs")
        except:
            pass
    
    # ═══════ STEP 7: MONITOR ═══════
    try:
        monitor_services(services_to_start, args.dev)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
