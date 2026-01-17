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

def get_pids_using_port(port: int) -> List[str]:
    """Belirli portu kullanan PID'leri bul."""
    pids = []
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
                            pids.append(pid)
    except:
        pass
    return list(set(pids))

def kill_port(port: int, force: bool = True) -> bool:
    """Portu temizle - Aggressive mode."""
    killed = False
    try:
        if sys.platform == 'win32':
            # Özel işlem: Node.js için tüm node.exe'leri öldür
            if port == ServicePort.NEXTJS.value:
                result = subprocess.run(
                    ['taskkill', '/F', '/IM', 'node.exe'],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    killed = True
                time.sleep(1)
            
            # PID bazlı temizlik - birkaç deneme yap
            for attempt in range(3):
                pids = get_pids_using_port(port)
                if not pids:
                    break
                    
                for pid in pids:
                    try:
                        subprocess.run(
                            ['taskkill', '/F', '/PID', pid],
                            capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        killed = True
                    except:
                        pass
                
                time.sleep(0.5)
            
            return killed
        else:
            subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True)
            return True
    except:
        pass
    return False

def ensure_port_available(port: int, max_attempts: int = 5) -> bool:
    """Port'un kullanılabilir olmasını garanti et."""
    if is_port_available(port):
        return True
    
    log(f"Port {port} meşgul, temizleniyor...", "warning")
    
    for attempt in range(max_attempts):
        kill_port(port)
        time.sleep(0.5)
        
        if is_port_available(port):
            log(f"Port {port} başarıyla temizlendi", "success")
            return True
        
        time.sleep(1)
    
    log(f"Port {port} temizlenemedi!", "error")
    return False

def cleanup_all_ports():
    """Tüm servislerin portlarını temizle."""
    log("Tüm portlar temizleniyor...", "loading")
    
    for service_name, config in SERVICES.items():
        if not is_port_available(config.port):
            kill_port(config.port)
    
    time.sleep(1)
    log("Portlar temizlendi", "success")

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
    
    if sys.platform == 'win32':
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    
    state.processes["api"].process = proc
    state.processes["api"].started_at = datetime.now()
    
    # Log thread
    t = threading.Thread(target=stream_output, args=(proc, "api"), daemon=True)
    t.start()
    state.log_threads.append(t)
    
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

def check_node_installed() -> bool:
    """Node.js kurulu mu?"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return result.returncode == 0
    except:
        return False

def ensure_nextjs_deps() -> bool:
    """Next.js bağımlılıklarını kontrol et/yükle."""
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    node_modules = nextjs_dir / "node_modules"
    
    if node_modules.exists() and (node_modules / "next").exists():
        return True
    
    log("Next.js bağımlılıkları yükleniyor...", "loading", "nextjs")
    
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(nextjs_dir),
            capture_output=True,
            text=True,
            timeout=300,
            shell=True if sys.platform == 'win32' else False
        )
        if result.returncode == 0:
            log("Bağımlılıklar yüklendi", "success", "nextjs")
            return True
        else:
            log(f"npm install hatası: {result.stderr[:100]}", "error", "nextjs")
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

def start_nextjs(dev_mode: bool = False):
    """Next.js frontend'i başlat."""
    config = SERVICES["nextjs"]
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    
    if not nextjs_dir.exists():
        log("Next.js klasörü bulunamadı!", "error", "nextjs")
        return False
    
    if not check_node_installed():
        log("Node.js kurulu değil! https://nodejs.org", "error", "nextjs")
        return False
    
    if not ensure_port_available(config.port):
        state.processes["nextjs"].status = ServiceStatus.ERROR
        return False
    
    if not ensure_nextjs_deps():
        return False
    
    log(f"Next.js başlatılıyor (port {config.port})...", "loading", "nextjs")
    state.processes["nextjs"].status = ServiceStatus.STARTING
    
    # Production veya development mode
    if dev_mode:
        cmd = ["npm", "run", "dev"]
        mode = "development"
    else:
        if not ensure_nextjs_build():
            log("Production build başarısız, dev mode'a geçiliyor...", "warning", "nextjs")
            cmd = ["npm", "run", "dev"]
            mode = "development"
        else:
            cmd = ["npm", "run", "start"]
            mode = "production"
    
    log(f"Next.js {mode} mode başlatılıyor...", "rocket", "nextjs")
    
    env = os.environ.copy()
    env['NEXT_PUBLIC_API_URL'] = f'http://localhost:{ServicePort.API.value}'
    env['PORT'] = str(config.port)
    
    if sys.platform == 'win32':
        proc = subprocess.Popen(
            cmd,
            cwd=str(nextjs_dir),
            env=env,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(nextjs_dir),
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    
    state.processes["nextjs"].process = proc
    state.processes["nextjs"].started_at = datetime.now()
    
    # Log thread
    t = threading.Thread(target=stream_output, args=(proc, "nextjs"), daemon=True)
    t.start()
    state.log_threads.append(t)
    
    # Health check
    time.sleep(3)  # Next.js'in başlaması için biraz bekle
    if wait_for_health(f"http://localhost:{config.port}", config.startup_timeout):
        state.processes["nextjs"].status = ServiceStatus.RUNNING
        log(f"Next.js hazır (port {config.port})", "success", "nextjs")
        return True
    else:
        state.processes["nextjs"].status = ServiceStatus.ERROR
        log("Next.js health check başarısız", "warning", "nextjs")
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
    
    if sys.platform == 'win32':
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    
    state.processes["streamlit"].process = proc
    state.processes["streamlit"].started_at = datetime.now()
    
    # Log thread
    t = threading.Thread(target=stream_output, args=(proc, "streamlit"), daemon=True)
    t.start()
    state.log_threads.append(t)
    
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
    
    ÖNEMLİ: Sadece gerçekten durmuş servisleri yeniden başlat.
    Port dinleniyorsa servis çalışıyor demektir.
    """
    error_logged = set()
    stable_count = {s: 0 for s in services}  # Stabilite sayacı
    
    # İlk 30 saniye servisler stabilize olsun
    initial_stabilization = 30
    start_time = time.time()
    
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
            
            # Servis sağlıklı mı kontrol et (port + health check)
            is_healthy = is_service_healthy(service_name)
            
            if is_healthy:
                # Servis çalışıyor, durumu güncelle
                if proc_info.status != ServiceStatus.RUNNING:
                    proc_info.status = ServiceStatus.RUNNING
                stable_count[service_name] = 0
                continue
            
            # İlk stabilizasyon süresinde yeniden başlatma yapma
            if elapsed < initial_stabilization:
                continue
            
            # Servis gerçekten durmuş - process de mi durmuş?
            process_dead = proc_info.process is None or proc_info.process.poll() is not None
            
            if not process_dead:
                # Process hala çalışıyor ama port dinlenmiyor - biraz bekle
                stable_count[service_name] += 1
                if stable_count[service_name] < 3:  # 3 kontrol bekle (15 saniye)
                    continue
            
            # Yeniden başlatma gerekiyor
            if proc_info.restart_count < config.max_restarts:
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
                
                # Port temizlenmesi için bekle
                time.sleep(3)
                ensure_port_available(config.port)
                time.sleep(1)
                
                if service_name == "api":
                    start_api()
                elif service_name == "nextjs":
                    start_nextjs(dev_mode)
                elif service_name == "streamlit":
                    start_streamlit()
            else:
                if service_name not in error_logged:
                    log(f"{config.name} çok fazla yeniden başlatıldı, durduruldu.", "error", service_name)
                    error_logged.add(service_name)
                proc_info.status = ServiceStatus.ERROR
        
        time.sleep(5)

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
    
    return parser.parse_args()

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
    
    # ═══════ STEP 1: OLLAMA ═══════
    if not args.skip_ollama:
        log("Ollama kontrol ediliyor...", "loading")
        if not start_ollama():
            log("Ollama başlatılamadı (isteğe bağlı)", "warning")
    else:
        log("Ollama kontrolü atlandı", "info")
    
    # ═══════ STEP 2: DIRECTORIES ═══════
    log("Klasörler hazırlanıyor...", "loading")
    try:
        from core.config import settings
        settings.ensure_directories()
        log("Klasörler hazır", "success")
    except Exception as e:
        log(f"Klasör hatası (devam ediliyor): {e}", "warning")
    
    # ═══════ STEP 3: CLEAN PORTS ═══════
    if args.clean:
        cleanup_all_ports()
    
    # ═══════ STEP 4: START SERVICES ═══════
    log("Servisler başlatılıyor...", "rocket")
    
    success = True
    
    # API
    if "api" in services_to_start:
        if not start_api():
            log("API başlatılamadı!", "error")
            success = False
    
    # Next.js
    if "nextjs" in services_to_start and success:
        if not start_nextjs(args.dev):
            log("Next.js başlatılamadı!", "warning")
    
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
    print_success_panel(active_services)
    
    # ═══════ STEP 6: OPEN BROWSER ═══════
    if not args.no_browser:
        time.sleep(1)
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
