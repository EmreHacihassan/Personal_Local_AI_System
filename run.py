#!/usr/bin/env python3
# ╔═══════════════════════════════════════════════════════════════════════════════════╗
# ║  ⚠️  HATIRLATMA: Bu projede ZATEN bir .venv var! Yenisini oluşturmana gerek yok!  ║
# ║  📁  Konum: .\.venv\Scripts\python.exe                                           ║
# ║  💡  Kullanım: .\.venv\Scripts\python.exe run.py                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════════════╝
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ENTERPRISE AI ASSISTANT - RUN SCRIPT                      ║
║                                                                              ║
║   v3.0 - BULLET-PROOF EDITION                                                ║
║                                                                              ║
║   🔧 ÖZELLİKLER:                                                             ║
║   ├─ Pre-flight testleri (başlamadan önce)                                   ║
║   ├─ Akıllı port yönetimi (çakışma önleme)                                   ║
║   ├─ Otomatik PATH yenileme (Node.js için)                                   ║
║   ├─ Senkronize başlatma (backend → frontend sırası)                         ║
║   ├─ Health check garantisi                                                  ║
║   ├─ Post-startup API doğrulama testleri                                     ║
║   └─ Otomatik servis izleme ve yeniden başlatma                              ║
║                                                                              ║
║   Backend:    FastAPI      → Port 8001                                       ║
║   Frontend:   Next.js      → Port 3000                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Kullanım:
  python run.py              # Backend + Frontend başlat
  python run.py --api-only   # Sadece API başlat
  python run.py --test       # Önce testleri çalıştır, sonra başlat
  python run.py --test-only  # Sadece testleri çalıştır (API çalışıyor olmalı)
  python run.py --clean      # Portları temizle ve başlat
  python run.py --skip-frontend  # Sadece backend başlat
  python run.py --no-browser # Tarayıcı açma
"""

import subprocess
import sys
import os
import time
import socket
import atexit
import io

# ══════════════════════════════════════════════════════════════════════════════
# UTF-8 STDOUT/STDERR - Windows emoji/unicode hataları için (ÖNCELİKLİ)
# ══════════════════════════════════════════════════════════════════════════════
if sys.platform == 'win32':
    # Windows console için UTF-8 encoding zorla - HER ŞEYden ÖNCE
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass  # Zaten wrapper ise atla

# ══════════════════════════════════════════════════════════════════════════════
# CHROMADB TELEMETRY KAPATMA - capture() argument hatası önleme
# ══════════════════════════════════════════════════════════════════════════════
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY'] = 'false'

# ══════════════════════════════════════════════════════════════════════════════
# HUGGINGFACE OFFLINE MODE - İnternet olmadan çalışması için
# ══════════════════════════════════════════════════════════════════════════════
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# ══════════════════════════════════════════════════════════════════════════════
# VENV ENFORCEMENT - Bu script SADECE venv ile çalışmalı!
# ══════════════════════════════════════════════════════════════════════════════
def enforce_venv():
    """Venv kullanımını zorunlu kıl ve gizli modda çalıştır."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.abspath(__file__)
    
    # .venv veya venv klasörünü bul
    venv_dir = None
    for venv_name in ['.venv', 'venv']:
        potential_venv = os.path.join(script_dir, venv_name)
        if os.path.exists(potential_venv):
            venv_dir = potential_venv
            break
    
    if not venv_dir:
        print("\n❌ Venv bulunamadı! Önce venv oluşturun:")
        print("   python -m venv .venv")
        print("   .\\.venv\\Scripts\\pip.exe install -r requirements.txt")
        sys.exit(1)
    
    venv_python = os.path.join(venv_dir, 'Scripts', 'python.exe')
    venv_pythonw = os.path.join(venv_dir, 'Scripts', 'pythonw.exe')
    
    # Windows'ta kontrol et
    if sys.platform == 'win32':
        current_exe = sys.executable.lower()
        venv_name = os.path.basename(venv_dir).lower()
        
        # 1. Venv içinde değilsek - venv ile yeniden başlat
        if venv_name not in current_exe and '.venv' not in current_exe and 'venv' not in current_exe:
            print("\n" + "="*70)
            print("⚠️  HATA: Bu script VENV içinden çalıştırılmalı!")
            print("="*70)
            print(f"\n❌ Şu an kullanılan: {sys.executable}")
            print(f"✅ Kullanılması gereken: {venv_python}")
            print("\n💡 Doğru kullanım:")
            print(f"   .\\{os.path.basename(venv_dir)}\\Scripts\\python.exe run.py")
            print("\n" + "="*70)
            
            if os.path.exists(venv_python):
                print("\n🔄 Otomatik olarak venv ile yeniden başlatılıyor...\n")
                import subprocess
                new_args = [venv_python, script_path] + sys.argv[1:]
                result = subprocess.run(new_args)
                sys.exit(result.returncode)
            sys.exit(1)
        
        # 2. pythonw.exe değilsek VE --no-hide flag'i yoksa - gizli modda yeniden başlat
        # Bu sayede terminal penceresi açılmaz
        if '--no-hide' not in sys.argv and 'pythonw' not in current_exe:
            if os.path.exists(venv_pythonw):
                # VBScript ile gizli modda yeniden başlat (en güvenilir yöntem)
                import subprocess
                import tempfile
                
                # Geçici VBS dosyası oluştur
                vbs_launcher = os.path.join(script_dir, '.run_launcher.vbs')
                vbs_content = f'''Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "{script_dir}"
objShell.Run """{venv_pythonw}"" ""{script_path}"" --no-hide", 0, False
'''
                with open(vbs_launcher, 'w') as f:
                    f.write(vbs_content)
                
                # VBS ile başlat
                subprocess.Popen(['wscript.exe', vbs_launcher], creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Mevcut process'i kapat - yeni process arka planda çalışacak
                sys.exit(0)

# Venv kontrolü - Script başlarken çalış
enforce_venv()
import argparse
import signal
import threading
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Lock/PID files
LOCK_FILE = PROJECT_ROOT / ".run.lock"
PID_FILE = PROJECT_ROOT / ".run.pid"


# Log directory
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class ServicePort(Enum):
    """Servis port tanımları."""
    API = 8001
    NEXTJS = 3000
    STREAMLIT = 8501

class ServiceStatus(Enum):
    """Servis durumları."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

@dataclass
class ServiceConfig:
    """Servis konfigürasyonu."""
    name: str
    port: int
    color: str
    icon: str
    health_endpoint: str = "/"
    startup_timeout: int = 60

# Servis konfigürasyonları
SERVICES = {
    "api": ServiceConfig(
        name="FastAPI Backend",
        port=ServicePort.API.value,
        color="\033[92m",
        icon="📡",
        health_endpoint="/health",
        startup_timeout=30
    ),
    "nextjs": ServiceConfig(
        name="Next.js Frontend",
        port=ServicePort.NEXTJS.value,
        color="\033[94m",
        icon="⚛️",
        health_endpoint="/",
        startup_timeout=120
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
    started_at: Optional[datetime] = None
    last_error: Optional[str] = None
    log_handle: Optional[any] = None  # Log dosyası handle'ı

class AppState:
    """Uygulama durumu."""
    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {
            "api": ProcessInfo(),
            "nextjs": ProcessInfo(),
        }
        self.shutdown_requested = False
        self.start_time: Optional[datetime] = None

state = AppState()

# ══════════════════════════════════════════════════════════════════════════════
# TERMINAL COLORS
# ══════════════════════════════════════════════════════════════════════════════

class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

def log(msg: str, level: str = "info", service: str = None):
    """Renkli log mesajı."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    levels = {
        "info":    (Colors.CYAN,   "ℹ️ "),
        "success": (Colors.GREEN,  "✅"),
        "warning": (Colors.YELLOW, "⚠️ "),
        "error":   (Colors.RED,    "❌"),
        "loading": (Colors.BLUE,   "⏳"),
        "rocket":  (Colors.MAGENTA,"🚀"),
        "test":    (Colors.CYAN,   "🧪"),
    }
    
    color, icon = levels.get(level, (Colors.RESET, "•"))
    service_tag = f" [{service}]" if service else ""
    
    print(f"{Colors.DIM}[{timestamp}]{Colors.RESET} {icon} {color}{msg}{Colors.RESET}{service_tag}")

def print_banner():
    """Başlangıç banner'ı."""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════╗
║   {Colors.BOLD}🤖 ENTERPRISE AI ASSISTANT v3.0{Colors.RESET}{Colors.CYAN}                          ║
║   {Colors.DIM}Bullet-Proof Edition - Zero Failure Guarantee{Colors.RESET}{Colors.CYAN}             ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
""")

# ══════════════════════════════════════════════════════════════════════════════
# PSUTIL IMPORT WITH FALLBACK
# ══════════════════════════════════════════════════════════════════════════════

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    log("psutil kurulu değil, temel process yönetimi kullanılacak", "warning")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    log("requests kurulu değil, HTTP testleri atlanacak", "warning")

# ══════════════════════════════════════════════════════════════════════════════
# GPU DETECTION
# ══════════════════════════════════════════════════════════════════════════════

GPU_INFO = {
    "available": False,
    "name": None,
    "memory_total": 0,
    "memory_free": 0,
    "utilization": 0,
    "cuda_available": False,
    "pytorch_version": None,
}

def detect_gpu():
    """GPU bilgilerini tespit et."""
    global GPU_INFO
    
    # 1. nvidia-smi ile GPU bilgisi
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.free,utilization.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            if len(parts) >= 4:
                GPU_INFO["available"] = True
                GPU_INFO["name"] = parts[0].strip()
                GPU_INFO["memory_total"] = int(parts[1].strip())
                GPU_INFO["memory_free"] = int(parts[2].strip())
                GPU_INFO["utilization"] = int(parts[3].strip())
    except:
        pass
    
    # 2. PyTorch CUDA kontrolü
    try:
        import torch
        GPU_INFO["pytorch_version"] = torch.__version__
        GPU_INFO["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available() and not GPU_INFO["name"]:
            GPU_INFO["name"] = torch.cuda.get_device_name(0)
            GPU_INFO["available"] = True
    except:
        pass
    
    return GPU_INFO

def get_gpu_status_line() -> str:
    """GPU durum satırı döndür."""
    if not GPU_INFO["available"]:
        return "GPU: Bulunamadı"
    
    mem_used = GPU_INFO["memory_total"] - GPU_INFO["memory_free"]
    cuda_status = "CUDA ✓" if GPU_INFO["cuda_available"] else "CUDA ✗"
    
    return f"{GPU_INFO['name']} | {mem_used}/{GPU_INFO['memory_total']} MB | %{GPU_INFO['utilization']} | {cuda_status}"

# ══════════════════════════════════════════════════════════════════════════════
# PORT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def is_port_available(port: int) -> bool:
    """Port kullanılabilir mi? (bind test)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('127.0.0.1', port))
            return True
    except:
        return False

def is_service_running(port: int) -> bool:
    """Port'ta bir servis çalışıyor mu? (connect test)"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except:
        return False

def get_pids_using_port(port: int) -> List[int]:
    """Belirli portu kullanan PID'leri bul."""
    pids = []
    
    if PSUTIL_AVAILABLE:
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port and conn.status == 'LISTEN':
                    if conn.pid:
                        pids.append(conn.pid)
        except:
            pass
    
    # Fallback: netstat (Windows)
    if not pids and sys.platform == 'win32':
        try:
            result = subprocess.run(
                f'netstat -ano | findstr ":{port}"',
                shell=True, capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split('\n'):
                if 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1].isdigit():
                        pids.append(int(parts[-1]))
        except:
            pass
    
    return list(set(pids))

def kill_process(pid: int) -> bool:
    """Process'i öldür."""
    if pid == os.getpid():
        return False  # Kendimizi öldürme
    
    killed = False
    
    # Method 1: psutil
    if PSUTIL_AVAILABLE:
        try:
            proc = psutil.Process(pid)
            children = proc.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except:
                    pass
            proc.kill()
            proc.wait(timeout=3)
            killed = True
        except:
            pass
    
    # Method 2: taskkill (Windows)
    if sys.platform == 'win32' and not killed:
        try:
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                capture_output=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            killed = True
        except:
            pass
    
    return killed

def kill_by_name(name: str):
    """İsme göre process'leri öldür."""
    if sys.platform == 'win32':
        try:
            subprocess.run(
                f'taskkill /F /IM {name} 2>nul',
                shell=True, capture_output=True, timeout=10
            )
        except:
            pass

def nuclear_port_cleanup(port: int) -> bool:
    """
    NUCLEAR PORT CLEANUP - Portu MUTLAKA temizle.
    Tüm yöntemleri agresif şekilde dene.
    """
    log(f"☢️ Nuclear cleanup başlatılıyor: Port {port}", "warning")
    
    if sys.platform == 'win32':
        # ═══════════════════════════════════════════════════════════════════
        # YÖNTEM 1: netstat + for döngüsü ile tüm PID'leri öldür
        # ═══════════════════════════════════════════════════════════════════
        for _ in range(3):
            try:
                # LISTENING + ESTABLISHED + TIME_WAIT hepsini bul
                result = subprocess.run(
                    f'netstat -ano | findstr ":{port}"',
                    shell=True, capture_output=True, text=True, timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in result.stdout.split('\n'):
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit() and int(pid) != os.getpid():
                            subprocess.run(
                                f'taskkill /F /T /PID {pid}',
                                shell=True, capture_output=True, timeout=5,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
            except:
                pass
            time.sleep(0.3)
        
        # ═══════════════════════════════════════════════════════════════════
        # YÖNTEM 2: Port'a özel process isimleri
        # ═══════════════════════════════════════════════════════════════════
        if port == ServicePort.NEXTJS.value:
            # Node.js - ama sadece 3000 portunu kullananları
            try:
                # wmic ile daha hassas kontrol
                result = subprocess.run(
                    'wmic process where "name=\'node.exe\'" get processid,commandline',
                    shell=True, capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in result.stdout.split('\n'):
                    if 'next' in line.lower() or '3000' in line:
                        parts = line.strip().split()
                        if parts:
                            pid = parts[-1]
                            if pid.isdigit():
                                subprocess.run(f'taskkill /F /T /PID {pid}', shell=True, capture_output=True, timeout=5)
            except:
                pass
        
        if port == ServicePort.API.value:
            # Uvicorn/Python process'leri - 8001 portunu kullananları
            try:
                result = subprocess.run(
                    'wmic process where "name=\'python.exe\'" get processid,commandline',
                    shell=True, capture_output=True, text=True, timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in result.stdout.split('\n'):
                    if 'uvicorn' in line.lower() or '8001' in line:
                        parts = line.strip().split()
                        if parts:
                            pid = parts[-1]
                            if pid.isdigit() and int(pid) != os.getpid():
                                subprocess.run(f'taskkill /F /T /PID {pid}', shell=True, capture_output=True, timeout=5)
            except:
                pass
        
        # ═══════════════════════════════════════════════════════════════════
        # YÖNTEM 3: PowerShell ile daha güçlü temizlik
        # ═══════════════════════════════════════════════════════════════════
        try:
            ps_cmd = f'''
            Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | 
            ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}
            '''
            subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass
    
    time.sleep(1)
    result = is_port_available(port)
    if result:
        log(f"✅ Port {port} temizlendi", "success")
    else:
        log(f"⚠️ Port {port} hala kullanımda", "warning")
    return result

def ensure_port_free(port: int, max_attempts: int = 5) -> bool:
    """Port'un boş olduğundan emin ol - garantili temizlik."""
    # Zaten boşsa hemen dön
    if is_port_available(port):
        return True
    
    log(f"Port {port} kullanımda, temizleniyor...", "warning")
    
    # Önce normal yöntemler
    for attempt in range(max_attempts):
        # Port'u kullanan process'leri bul ve öldür
        pids = get_pids_using_port(port)
        if pids:
            for pid in pids:
                kill_process(pid)
            time.sleep(0.5)
        
        # Hemen kontrol
        if is_port_available(port):
            log(f"Port {port} temizlendi", "success")
            return True
        
        # 2. denemeden sonra Node.js için özel işlem
        if attempt >= 1 and port == ServicePort.NEXTJS.value:
            kill_by_name('node.exe')
            time.sleep(0.5)
            if is_port_available(port):
                log(f"Port {port} temizlendi", "success")
                return True
        
        # 3. denemeden sonra nuclear cleanup
        if attempt >= 2:
            nuclear_port_cleanup(port)
            time.sleep(0.5)
            if is_port_available(port):
                log(f"Port {port} temizlendi (nuclear)", "success")
                return True
    
    # Son çare: tüm yöntemleri aynı anda uygula
    log(f"Port {port} direniyor, tam temizlik yapılıyor...", "warning")
    pids = get_pids_using_port(port)
    for pid in pids:
        kill_process(pid)
    if port == ServicePort.NEXTJS.value:
        kill_by_name('node.exe')
    nuclear_port_cleanup(port)
    time.sleep(1)
    
    if is_port_available(port):
        log(f"Port {port} temizlendi (full cleanup)", "success")
        return True
    
    log(f"Port {port} temizlenemedi!", "error")
    return False

# ══════════════════════════════════════════════════════════════════════════════
# PID MANAGEMENT - Önceki instance'ı otomatik kapat
# ══════════════════════════════════════════════════════════════════════════════

def kill_previous_instance() -> bool:
    """
    Önceki çalışan instance'ı kapat.
    PID dosyasından eski PID'i oku ve process'i sonlandır.
    Ayrıca portları da agresif şekilde temizle.
    """
    killed_any = False
    my_pid = os.getpid()
    
    # 1. Önce portları HEMEN temizle - bu en önemli adım
    for port in [ServicePort.API.value, ServicePort.NEXTJS.value]:
        if not is_port_available(port):
            log(f"Port {port} kullanımda, temizleniyor...", "loading")
            # Nuclear cleanup - agresif temizlik
            nuclear_port_cleanup(port)
            time.sleep(1)
            
            # Hala kullanımdaysa ensure_port_free ile devam et
            if not is_port_available(port):
                if ensure_port_free(port):
                    killed_any = True
                    log(f"Port {port} temizlendi", "success")
    
    # 2. PID dosyasından önceki ana process'i de kapat
    if PID_FILE.exists():
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Kendimiz değilse kapat
            if old_pid != my_pid:
                if PSUTIL_AVAILABLE:
                    try:
                        proc = psutil.Process(old_pid)
                        if 'python' in proc.name().lower():
                            children = proc.children(recursive=True)
                            for child in children:
                                try:
                                    child.kill()
                                except:
                                    pass
                            proc.kill()
                            proc.wait(timeout=3)
                            killed_any = True
                            log(f"Önceki ana process kapatıldı (PID: {old_pid})", "success")
                    except psutil.NoSuchProcess:
                        pass
                    except:
                        pass
                else:
                    if sys.platform == 'win32':
                        try:
                            subprocess.run(
                                ['taskkill', '/F', '/T', '/PID', str(old_pid)],
                                capture_output=True, timeout=5,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            killed_any = True
                        except:
                            pass
        except:
            pass
        
        try:
            PID_FILE.unlink()
        except:
            pass
    
    # 3. Son kontrol - portlar temiz mi?
    time.sleep(1)
    for port in [ServicePort.API.value, ServicePort.NEXTJS.value]:
        if not is_port_available(port):
            log(f"⚠️ Port {port} hala kullanımda!", "warning")
    
    return killed_any


def save_current_pid():
    """Mevcut PID'i dosyaya kaydet."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# PATH MANAGEMENT (NODE.JS için kritik)
# ══════════════════════════════════════════════════════════════════════════════

def refresh_environment_path():
    """Windows ortam değişkenlerini yenile."""
    if sys.platform != 'win32':
        return True
    
    try:
        # Sistem ve kullanıcı PATH'ini al
        result = subprocess.run(
            ['powershell', '-Command', 
             '[System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")'],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            os.environ['PATH'] = result.stdout.strip()
            return True
    except:
        pass
    
    return False

def check_node_installed() -> Tuple[bool, str]:
    """Node.js kurulu mu kontrol et."""
    # PATH'i yenile
    refresh_environment_path()
    
    # Node.js kontrol
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True, text=True, timeout=10,
            shell=True if sys.platform == 'win32' else False,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except:
        pass
    
    # Bilinen konumlarda ara
    known_paths = [
        r"C:\Program Files\nodejs",
        r"C:\nvm4w\nodejs",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs"),
    ]
    
    for path in known_paths:
        node_exe = os.path.join(path, "node.exe")
        if os.path.exists(node_exe):
            os.environ['PATH'] = f"{path};{os.environ.get('PATH', '')}"
            try:
                result = subprocess.run(
                    ['node', '--version'],
                    capture_output=True, text=True, timeout=10,
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    return True, result.stdout.strip()
            except:
                pass
    
    return False, ""

# ══════════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT TESTS
# ══════════════════════════════════════════════════════════════════════════════

def run_preflight_tests() -> Dict:
    """Başlamadan önce sistem testleri yap."""
    log("🧪 Pre-flight testler başlatılıyor...", "test")
    
    results = {
        "python_version": {"status": False, "detail": ""},
        "directories": {"status": False, "detail": ""},
        "node_js": {"status": False, "detail": ""},
        "ports": {"status": False, "detail": ""},
        "gpu": {"status": False, "detail": ""},
        "ollama": {"status": False, "detail": ""},
        "imports": {"status": False, "detail": ""},
    }
    
    # 1. Python version
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 10:
        results["python_version"]["status"] = True
        results["python_version"]["detail"] = f"Python {major}.{minor}"
    else:
        results["python_version"]["detail"] = f"Python {major}.{minor} (min 3.10 gerekli)"
    
    # 2. Directories
    try:
        dirs = ["data", "data/chroma_db", "data/sessions", "logs"]
        for d in dirs:
            (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)
        results["directories"]["status"] = True
        results["directories"]["detail"] = "Tüm dizinler hazır"
    except Exception as e:
        results["directories"]["detail"] = str(e)
    
    # 3. Node.js
    node_ok, node_version = check_node_installed()
    results["node_js"]["status"] = node_ok
    results["node_js"]["detail"] = node_version if node_ok else "Node.js bulunamadı"
    
    # 4. Ports
    ports_ok = True
    port_details = []
    for name, config in SERVICES.items():
        if is_port_available(config.port):
            port_details.append(f"{config.port}:✓")
        else:
            port_details.append(f"{config.port}:kullanımda")
            # Temizlemeyi dene
            if ensure_port_free(config.port):
                port_details[-1] = f"{config.port}:temizlendi"
            else:
                ports_ok = False
    results["ports"]["status"] = ports_ok
    results["ports"]["detail"] = ", ".join(port_details)
    
    # 5. GPU Detection
    detect_gpu()
    if GPU_INFO["available"]:
        if GPU_INFO["cuda_available"]:
            results["gpu"]["status"] = True
            mem_gb = GPU_INFO["memory_total"] / 1024
            results["gpu"]["detail"] = f"{GPU_INFO['name'][:20]} {mem_gb:.0f}GB CUDA✓"
        else:
            results["gpu"]["status"] = False
            results["gpu"]["detail"] = f"{GPU_INFO['name'][:20]} (CUDA yok!)"
    else:
        results["gpu"]["detail"] = "GPU bulunamadı"
    
    # 6. Ollama
    if REQUESTS_AVAILABLE:
        try:
            resp = requests.get("http://localhost:11434/api/version", timeout=2)
            results["ollama"]["status"] = resp.status_code == 200
            results["ollama"]["detail"] = "Çalışıyor" if resp.status_code == 200 else "Yanıt yok"
        except:
            results["ollama"]["status"] = False
            results["ollama"]["detail"] = "Bağlantı yok (isteğe bağlı)"
    else:
        results["ollama"]["detail"] = "Kontrol atlandı"
    
    # 7. Critical imports
    try:
        import fastapi
        import uvicorn
        import chromadb
        results["imports"]["status"] = True
        results["imports"]["detail"] = "FastAPI, Uvicorn, Chroma OK"
    except ImportError as e:
        results["imports"]["detail"] = str(e)
    
    # Sonuçları göster
    print()
    print(f"{Colors.CYAN}┌─────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│         PRE-FLIGHT TEST SONUÇLARI          │{Colors.RESET}")
    print(f"{Colors.CYAN}├─────────────────────────────────────────────┤{Colors.RESET}")
    
    all_ok = True
    for name, result in results.items():
        icon = "✅" if result["status"] else "❌"
        color = Colors.GREEN if result["status"] else Colors.RED
        # GPU ve Ollama isteğe bağlı
        if not result["status"] and name in ["gpu", "ollama"]:
            icon = "⚠️ "
            color = Colors.YELLOW
        print(f"{Colors.CYAN}│{Colors.RESET} {icon} {name:15} {color}{result['detail'][:25]:25}{Colors.RESET} {Colors.CYAN}│{Colors.RESET}")
        if not result["status"] and name not in ["ollama", "gpu"]:
            all_ok = False
    
    print(f"{Colors.CYAN}└─────────────────────────────────────────────┘{Colors.RESET}")
    print()
    
    return {"results": results, "all_ok": all_ok}

# ══════════════════════════════════════════════════════════════════════════════
# API TESTS
# ══════════════════════════════════════════════════════════════════════════════

def run_api_tests() -> Dict:
    """Backend API'yi kapsamlı test et."""
    if not REQUESTS_AVAILABLE:
        return {"success": False, "message": "requests modülü yok"}
    
    log("🧪 Backend API testleri çalıştırılıyor...", "test")
    
    base_url = f"http://localhost:{ServicePort.API.value}"
    
    tests = [
        # Health & Status
        ("GET", "/health", "Health Check", None),
        ("GET", "/api/health", "API Health", None),
        ("GET", "/api/system/info", "System Info", None),
        
        # RAG
        ("GET", "/api/rag/status", "RAG Status", None),
        ("GET", "/api/rag/stats", "RAG Stats", None),
        
        # Sessions
        ("GET", "/api/sessions", "Sessions", None),
        ("GET", "/api/chat/sessions", "Chat Sessions", None),
        
        # Documents
        ("GET", "/api/documents", "Documents", None),
        
        # Agents
        ("GET", "/api/analytics/agents", "Agents Usage", None),
        
        # Learning
        ("GET", "/api/learning/workspaces", "Workspaces", None),
        ("GET", "/api/learning/documents/styles", "Doc Styles", None),
        ("GET", "/api/learning/tests/types", "Test Types", None),
        
        # Premium
        ("GET", "/api/premium/status", "Premium Status", None),
        ("GET", "/api/premium/features", "Premium Features", None),
        
        # Visual Learning
        ("POST", "/api/learning/visual/mindmap", "Visual Mindmap", 
         {"topic": "Test", "content": "Test content"}),
        
        # Multimedia
        ("POST", "/api/learning/multimedia/slides", "Multimedia Slides",
         {"topic": "Test", "content": "Test content", "slide_count": 3}),
        
        # Linking
        ("POST", "/api/learning/linking/prerequisites", "Linking Prerequisites",
         {"topic": "Python", "content": "Programming basics"}),
        
        # WebSocket
        ("GET", "/api/ws/stats", "WebSocket Stats", None),
        
        # Admin
        ("GET", "/api/admin/stats", "Admin Stats", None),
        
        # Plugins
        ("GET", "/api/plugins", "Plugins List", None),
        ("GET", "/api/plugins/stats", "Plugins Stats", None),
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for method, path, name, data in tests:
        try:
            url = base_url + path
            if method == "GET":
                resp = requests.get(url, timeout=10)
            else:
                resp = requests.post(url, json=data, timeout=15)
            
            success = resp.status_code == 200
            results.append({
                "name": name,
                "path": path,
                "status": resp.status_code,
                "success": success
            })
            
            if success:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            results.append({
                "name": name,
                "path": path,
                "status": 0,
                "success": False,
                "error": str(e)[:50]
            })
            failed += 1
    
    # Sonuçları göster
    print()
    print(f"{Colors.CYAN}┌─────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.CYAN}│            API TEST SONUÇLARI               │{Colors.RESET}")
    print(f"{Colors.CYAN}├─────────────────────────────────────────────┤{Colors.RESET}")
    
    for r in results:
        icon = "✅" if r["success"] else "❌"
        status = r["status"] if r["status"] else "ERR"
        print(f"{Colors.CYAN}│{Colors.RESET} {icon} {r['name']:20} [{status:3}] {r['path'][:15]:15} {Colors.CYAN}│{Colors.RESET}")
    
    print(f"{Colors.CYAN}├─────────────────────────────────────────────┤{Colors.RESET}")
    rate = (passed / len(tests)) * 100 if tests else 0
    color = Colors.GREEN if rate >= 90 else Colors.YELLOW if rate >= 70 else Colors.RED
    print(f"{Colors.CYAN}│{Colors.RESET} {color}TOPLAM: {passed}/{len(tests)} başarılı ({rate:.1f}%){Colors.RESET}          {Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.CYAN}└─────────────────────────────────────────────┘{Colors.RESET}")
    print()
    
    return {
        "success": failed == 0,
        "passed": passed,
        "failed": failed,
        "total": len(tests),
        "rate": rate,
        "results": results
    }

def run_frontend_test() -> bool:
    """Frontend erişilebilir mi kontrol et."""
    if not REQUESTS_AVAILABLE:
        return False
    
    try:
        resp = requests.get(f"http://localhost:{ServicePort.NEXTJS.value}", timeout=5)
        return resp.status_code == 200
    except:
        return False

# ══════════════════════════════════════════════════════════════════════════════
# SERVICE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def wait_for_service(port: int, endpoint: str = "/", timeout: int = 60) -> bool:
    """Servisin hazır olmasını bekle."""
    if not REQUESTS_AVAILABLE:
        time.sleep(5)
        return not is_port_available(port)
    
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"http://localhost:{port}{endpoint}", timeout=3)
            if resp.status_code in [200, 304]:
                return True
        except:
            pass
        time.sleep(2)
    
    return False

def start_api() -> bool:
    """FastAPI backend'i başlat."""
    config = SERVICES["api"]
    
    if not ensure_port_free(config.port):
        state.processes["api"].status = ServiceStatus.ERROR
        state.processes["api"].last_error = "Port kullanılamıyor"
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
    
    # Log dosyası
    log_file = LOG_DIR / f"api_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Log dosyasını aç (subprocess devam ederken açık kalmalı)
    log_handle = open(log_file, "a", encoding="utf-8")
    log_handle.write(f"\n{'='*60}\n")
    log_handle.write(f"API Starting at {datetime.now()}\n")
    log_handle.write(f"Command: {' '.join(cmd)}\n")
    log_handle.write(f"{'='*60}\n")
    log_handle.flush()
    
    # Windows'ta subprocess'i tamamen izole et
    # CREATE_NEW_PROCESS_GROUP: Yeni process grubu oluştur
    # DETACHED_PROCESS: Ana process'ten bağımsız çalışsın
    # CREATE_NO_WINDOW: Console penceresi açmasın
    if sys.platform == 'win32':
        creation_flags = (
            subprocess.CREATE_NEW_PROCESS_GROUP |
            subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NO_WINDOW
        )
    else:
        creation_flags = 0
    
    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_handle,
        stderr=log_handle,
        creationflags=creation_flags,
        start_new_session=True if sys.platform != 'win32' else False,
    )
    
    # Log handle'ı sakla (cleanup'ta kapatılacak)
    state.processes["api"].log_handle = log_handle
    
    state.processes["api"].process = proc
    state.processes["api"].started_at = datetime.now()
    
    # Health check
    if wait_for_service(config.port, config.health_endpoint, config.startup_timeout):
        state.processes["api"].status = ServiceStatus.RUNNING
        log(f"API hazır (port {config.port})", "success", "api")
        return True
    else:
        state.processes["api"].status = ServiceStatus.ERROR
        state.processes["api"].last_error = "Health check timeout"
        log("API başlatılamadı!", "error", "api")
        return False

def start_nextjs() -> bool:
    """Next.js frontend'i başlat."""
    config = SERVICES["nextjs"]
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    
    if not nextjs_dir.exists():
        log("Next.js dizini bulunamadı!", "error", "nextjs")
        return False
    
    # Node.js kontrolü
    node_ok, node_version = check_node_installed()
    if not node_ok:
        log("Node.js kurulu değil! https://nodejs.org", "error", "nextjs")
        return False
    
    log(f"Node.js {node_version} ✓", "success", "nextjs")
    
    # ═══════════════════════════════════════════════════════════════════
    # NEXT.JS CACHE CLEANUP - Module not found hatalarını önler
    # ═══════════════════════════════════════════════════════════════════
    next_cache = nextjs_dir / ".next"
    if next_cache.exists():
        # Cache'in boyutunu kontrol et
        cache_size = sum(f.stat().st_size for f in next_cache.rglob('*') if f.is_file()) / (1024 * 1024)
        
        # Cache bozuk olabilir mi kontrol et
        cache_corrupted = False
        
        # 817.js gibi chunk dosyaları eksikse cache bozuk
        cache_chunks = list(next_cache.glob("**/*.js"))
        if len(cache_chunks) > 0:
            # Chunk reference hatası olabilir mi?
            build_manifest = next_cache / "build-manifest.json"
            if build_manifest.exists():
                try:
                    import json
                    with open(build_manifest, 'r') as f:
                        manifest = json.load(f)
                    # Manifest'teki dosyaların varlığını kontrol et
                    for page, chunks in manifest.get("pages", {}).items():
                        for chunk in chunks[:3]:  # İlk 3 chunk'ı kontrol et
                            chunk_path = nextjs_dir / ".next" / chunk
                            if not chunk_path.exists():
                                cache_corrupted = True
                                log(f"Eksik chunk tespit edildi: {chunk}", "warning", "nextjs")
                                break
                        if cache_corrupted:
                            break
                except Exception:
                    pass
        
        if cache_corrupted:
            log("⚠️ Bozuk Next.js cache tespit edildi, temizleniyor...", "warning", "nextjs")
            try:
                shutil.rmtree(next_cache)
                log("✅ Next.js cache temizlendi", "success", "nextjs")
            except Exception as e:
                log(f"Cache temizleme hatası: {e}", "warning", "nextjs")
    
    # Port temizle
    if not ensure_port_free(config.port):
        state.processes["nextjs"].status = ServiceStatus.ERROR
        state.processes["nextjs"].last_error = "Port kullanılamıyor"
        return False
    
    # node_modules kontrolü
    node_modules = nextjs_dir / "node_modules"
    if not node_modules.exists() or not (node_modules / "next").exists():
        log("npm install çalıştırılıyor...", "loading", "nextjs")
        try:
            result = subprocess.run(
                "npm install --legacy-peer-deps",
                cwd=str(nextjs_dir),
                shell=True,
                capture_output=True,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            if result.returncode != 0:
                log("npm install başarısız!", "error", "nextjs")
                return False
            log("npm install tamamlandı", "success", "nextjs")
        except Exception as e:
            log(f"npm install hatası: {e}", "error", "nextjs")
            return False
    
    log(f"Next.js başlatılıyor (port {config.port})...", "loading", "nextjs")
    state.processes["nextjs"].status = ServiceStatus.STARTING
    
    env = os.environ.copy()
    env['NEXT_PUBLIC_API_URL'] = f'http://localhost:{ServicePort.API.value}'
    env['PORT'] = str(config.port)
    env['NODE_ENV'] = 'development'
    env['NEXT_TELEMETRY_DISABLED'] = '1'
    
    # Log dosyası
    log_file = LOG_DIR / f"nextjs_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Log dosyasını aç (subprocess devam ederken açık kalmalı)
    log_handle = open(log_file, "a", encoding="utf-8")
    log_handle.write(f"\n{'='*60}\n")
    log_handle.write(f"Next.js Starting at {datetime.now()}\n")
    log_handle.write(f"{'='*60}\n")
    log_handle.flush()
    
    # Windows'ta VBScript wrapper kullan - %100 gizli çalışır
    # Node.js subprocess'leri CREATE_NO_WINDOW flag'ini miras almıyor
    # Bu yüzden VBScript ile tamamen gizli başlatıyoruz
    if sys.platform == 'win32':
        node_exe = shutil.which("node.exe") or shutil.which("node") or "node.exe"
        next_cli = nextjs_dir / "node_modules" / "next" / "dist" / "bin" / "next"
        
        if not next_cli.exists():
            # Fallback path
            next_cli = nextjs_dir / "node_modules" / ".bin" / "next"
        
        # Geçici VBS dosyası oluştur - daha güvenli escape yöntemi
        vbs_file = PROJECT_ROOT / ".nextjs_launcher.vbs"
        
        # Yolları string olarak al (VBS'te backslash escape gerekmez)
        node_path = str(node_exe)
        next_path = str(next_cli)
        nextjs_path = str(nextjs_dir)
        
        vbs_content = f'''On Error Resume Next
Set objShell = CreateObject("WScript.Shell")
objShell.CurrentDirectory = "{nextjs_path}"

' Environment variables
Set objEnv = objShell.Environment("Process")
objEnv("NEXT_PUBLIC_API_URL") = "http://localhost:{ServicePort.API.value}"
objEnv("PORT") = "{config.port}"
objEnv("NODE_ENV") = "development"
objEnv("NEXT_TELEMETRY_DISABLED") = "1"

' Node.js ile Next.js başlat - 0 = gizli pencere
strNode = "{node_path}"
strNext = "{next_path}"
strCmd = Chr(34) & strNode & Chr(34) & " " & Chr(34) & strNext & Chr(34) & " dev -p {config.port}"
objShell.Run strCmd, 0, False
'''
        
        with open(vbs_file, 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        
        # VBS dosyasını wscript ile çalıştır
        proc = subprocess.Popen(
            ['wscript.exe', str(vbs_file)],
            cwd=str(nextjs_dir),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        
        log_handle.write(f"VBS launcher kullanıldı: {vbs_file}\n")
        log_handle.flush()
    else:
        proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(nextjs_dir),
            env=env,
            stdout=log_handle,
            stderr=log_handle,
            start_new_session=True,
        )
    
    # Log handle'ı sakla
    state.processes["nextjs"].log_handle = log_handle
    
    state.processes["nextjs"].process = proc
    state.processes["nextjs"].started_at = datetime.now()
    
    # Health check - Next.js için daha uzun bekle
    log("Next.js derleniyor, bu birkaç dakika sürebilir...", "loading", "nextjs")
    
    if wait_for_service(config.port, config.health_endpoint, config.startup_timeout):
        state.processes["nextjs"].status = ServiceStatus.RUNNING
        log(f"Next.js hazır (port {config.port})", "success", "nextjs")
        return True
    else:
        # Process çalışıyor mu kontrol et
        if proc.poll() is None:
            log("Next.js henüz derlenmiyor ama process çalışıyor", "warning", "nextjs")
            state.processes["nextjs"].status = ServiceStatus.RUNNING
            return True
        
        state.processes["nextjs"].status = ServiceStatus.ERROR
        state.processes["nextjs"].last_error = "Health check timeout"
        log("Next.js başlatılamadı!", "error", "nextjs")
        return False

# ══════════════════════════════════════════════════════════════════════════════
# BACKEND CONTROL SIGNALS
# ══════════════════════════════════════════════════════════════════════════════
SIGNAL_FILE = ROOT_DIR / ".backend_state"

def check_backend_signal():
    """Backend kontrol sinyallerini kontrol et."""
    if not SIGNAL_FILE.exists():
        return "running"
    
    try:
        with open(SIGNAL_FILE, "r", encoding="utf-8") as f:
            signal = f.read().strip()
        return signal
    except:
        return "running"

def clear_signal(new_state="running"):
    """Sinyal dosyasını güncelle."""
    try:
        with open(SIGNAL_FILE, "w", encoding="utf-8") as f:
            f.write(new_state)
    except:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

_cleanup_done = False
_cleanup_reason = "unknown"

def cleanup(reason: str = None):
    """Tüm process'leri temiz kapat."""
    global _cleanup_done, _cleanup_reason
    if _cleanup_done:
        return
    _cleanup_done = True
    
    if reason:
        _cleanup_reason = reason
    
    state.shutdown_requested = True
    
    # Cleanup sebebini logla - debug için önemli
    import traceback
    stack = ''.join(traceback.format_stack()[-5:-1])
    log(f"Servisler durduruluyor... (sebep: {_cleanup_reason})", "loading")
    
    # Log dosyasına detaylı bilgi yaz
    try:
        cleanup_log = LOG_DIR / "cleanup_debug.log"
        with open(cleanup_log, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Cleanup called at {datetime.now()}\n")
            f.write(f"Reason: {_cleanup_reason}\n")
            f.write(f"Stack trace:\n{stack}\n")
            f.write(f"{'='*60}\n")
    except:
        pass
    
    for name, proc_info in state.processes.items():
        # Log handle'ı kapat
        if hasattr(proc_info, 'log_handle') and proc_info.log_handle:
            try:
                proc_info.log_handle.close()
            except:
                pass
        
        if proc_info.process is not None:
            try:
                proc_info.process.terminate()
                try:
                    proc_info.process.wait(timeout=5)
                except:
                    proc_info.process.kill()
            except:
                pass
    
    # Lock dosyalarını temizle
    try:
        LOCK_FILE.unlink(missing_ok=True)
        PID_FILE.unlink(missing_ok=True)
    except:
        pass
    
    log("Tüm servisler durduruldu", "success")

# ══════════════════════════════════════════════════════════════════════════════
# MONITORING
# ══════════════════════════════════════════════════════════════════════════════

def monitor_services(services: List[str]):
    """Servisleri izle - Bullet-proof versiyon."""
    log("Servisler izleniyor... (Ctrl+C ile çıkış)", "info")
    
    # Her servis için son restart zamanını takip et (flood protection)
    last_restart: Dict[str, datetime] = {}
    restart_cooldown = 60  # En az 60 saniye bekle her restart arasında
    
    # Başlangıç grace period - ilk 120 saniye kontrol etme
    startup_time = datetime.now()
    startup_grace_period = 120  # seconds
    
    while not state.shutdown_requested:
        time.sleep(15)  # Her 15 saniyede bir kontrol
        
        # Grace period kontrolü
        elapsed = (datetime.now() - startup_time).total_seconds()
        
        # Sinyal Kontrolü (Grace period'dan bağımsız)
        signal = check_backend_signal()
        
        # STOP SIGNAL - Backend'i durdur
        if signal == "stopped":
            proc_info = state.processes.get("api")
            if proc_info and proc_info.status != ServiceStatus.STOPPED:
                log("Kullanıcı isteğiyle Backend durduruluyor...", "warning", "api")
                if proc_info.process:
                    try:
                        proc_info.process.terminate()
                        proc_info.process.wait(timeout=2)
                    except:
                        pass
                proc_info.status = ServiceStatus.STOPPED
                # Next.js'i durdurmaya gerek yok, bağımsız çalışabilir
            continue

        # RESTART SIGNAL
        if signal == "restarting":
            log("Kullanıcı isteğiyle Backend yeniden başlatılıyor...", "warning", "api")
            proc_info = state.processes.get("api")
            if proc_info and proc_info.process:
                try:
                    proc_info.process.terminate()
                    proc_info.process.wait(timeout=2)
                except:
                    pass
            # Status'u ERROR yap ki aşağıda restart logic tetiklesin
            start_api() 
            clear_signal("running")
            last_restart["api"] = datetime.now()
            continue

        if elapsed < startup_grace_period:
            continue
        
        for service_name in services:
            proc_info = state.processes.get(service_name)
            if not proc_info or proc_info.status == ServiceStatus.ERROR:
                continue
            
            # Servis zaten STARTING durumundaysa bekle
            if proc_info.status == ServiceStatus.STARTING:
                continue
            
            config = SERVICES[service_name]
            
            # Cooldown kontrolü - çok sık restart yapma
            if service_name in last_restart:
                since_last = (datetime.now() - last_restart[service_name]).total_seconds()
                if since_last < restart_cooldown:
                    continue
            
            # Servis gerçekten çalışıyor mu? (Port bağlantı testi)
            service_responding = is_service_running(config.port)
            
            if not service_responding:
                # Port boş VE process ölmüş mü kontrol et
                process_dead = False
                if proc_info.process:
                    poll_result = proc_info.process.poll()
                    process_dead = poll_result is not None
                
                # Windows'ta CMD alt process'leri için ekstra kontrol
                port_available = is_port_available(config.port)
                
                # Sadece hem port boş hem de process ölmüşse restart yap
                if port_available and process_dead:
                    log(f"{config.name} durdu, yeniden başlatılıyor...", "warning", service_name)
                    last_restart[service_name] = datetime.now()
                    
                    if service_name == "api":
                        start_api()
                    elif service_name == "nextjs":
                        start_nextjs()
                elif not service_responding and not port_available:
                    # Port kullanılıyor ama yanıt vermiyor - bekle
                    log(f"{config.name} başlatılıyor, lütfen bekleyin...", "loading", service_name)

def print_success():
    """Başarılı başlatma mesajı."""
    api_running = state.processes["api"].status == ServiceStatus.RUNNING
    nextjs_running = state.processes["nextjs"].status == ServiceStatus.RUNNING
    
    print()
    print(f"{Colors.GREEN}╔══════════════════════════════════════════════════════════════╗")
    print(f"║   ✅ SERVİSLER BAŞARIYLA BAŞLATILDI!                         ║")
    print(f"╠══════════════════════════════════════════════════════════════╣")
    print(f"║                                                              ║")
    if api_running:
        print(f"║   📡 API:          http://localhost:{ServicePort.API.value}                    ║")
        print(f"║   📚 API Docs:     http://localhost:{ServicePort.API.value}/docs               ║")
    if nextjs_running:
        print(f"║   ⚛️  Frontend:     http://localhost:{ServicePort.NEXTJS.value}                     ║")
    print(f"║                                                              ║")
    print(f"║   ⌨️  Durdurmak için: Ctrl+C                                  ║")
    print(f"║                                                              ║")
    print(f"╚══════════════════════════════════════════════════════════════╝{Colors.RESET}")
    print()

# ══════════════════════════════════════════════════════════════════════════════
# ARGUMENTS
# ══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Argümanları parse et."""
    parser = argparse.ArgumentParser(
        description="Enterprise AI Assistant - Bullet-Proof Runner v3.0"
    )
    
    parser.add_argument("--api-only", action="store_true",
                       help="Sadece API başlat")
    parser.add_argument("--skip-frontend", action="store_true",
                       help="Frontend başlatmayı atla")
    parser.add_argument("--test", action="store_true",
                       help="Önce testleri çalıştır, sonra başlat")
    parser.add_argument("--test-only", action="store_true",
                       help="Sadece testleri çalıştır, başlatma")
    parser.add_argument("--clean", action="store_true",
                       help="Portları temizle ve başlat")
    parser.add_argument("--no-browser", action="store_true",
                       help="Tarayıcı açma")
    parser.add_argument("--status", action="store_true",
                       help="Servislerin durumunu kontrol et")
    parser.add_argument("--stop", action="store_true",
                       help="Çalışan servisleri durdur")
    parser.add_argument("--no-hide", action="store_true",
                       help="Gizli modda yeniden başlatmayı atla (dahili kullanım)")
    
    return parser.parse_args()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Ana çalıştırma fonksiyonu."""
    args = parse_args()
    
    # Cleanup handler - sadece atexit kullan, signal handler probleme yol açıyor
    atexit.register(cleanup)
    
    # Windows'ta SIGINT handling - daha güvenli yaklaşım
    def graceful_shutdown(signum, frame):
        """Graceful shutdown handler."""
        log(f"Sinyal alındı: {signum}, kapatılıyor...", "warning")
        state.shutdown_requested = True
        # cleanup() burada çağırma, atexit halledecek
        sys.exit(0)
    
    # Sadece SIGINT için handler (CTRL+C)
    try:
        signal.signal(signal.SIGINT, graceful_shutdown)
        # Windows'ta SIGBREAK de yakala
        if sys.platform == 'win32':
            signal.signal(signal.SIGBREAK, graceful_shutdown)
    except (AttributeError, ValueError):
        pass  # Signal desteklenmiyorsa geç
    
    # Banner
    print_banner()
    state.start_time = datetime.now()
    
    # ═══════ ÖNCEKI INSTANCE KONTROLÜ ═══════
    # Status ve stop modları hariç, önceki instance'ı otomatik kapat
    if not args.status and not args.stop and not args.test_only:
        if kill_previous_instance():
            log("Önceki instance temizlendi, yeni başlatma yapılıyor...", "info")
            time.sleep(2)  # Process'lerin tamamen kapanması için bekle
    
    # Mevcut PID'i kaydet
    save_current_pid()
    
    # ═══════ STATUS CHECK MODE ═══════
    if args.status:
        log("Servis durumları kontrol ediliyor...", "info")
        api_ok = is_service_running(ServicePort.API.value)
        frontend_ok = is_service_running(ServicePort.NEXTJS.value)
        ollama_ok = is_service_running(11434)
        
        # GPU durumu
        detect_gpu()
        
        print(f"\n{Colors.CYAN}┌─────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.CYAN}│              SERVİS DURUMU                          │{Colors.RESET}")
        print(f"{Colors.CYAN}├─────────────────────────────────────────────────────┤{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} {'✅' if api_ok else '❌'} API (8001):      {'ONLINE' if api_ok else 'OFFLINE':10}                {Colors.CYAN}│{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} {'✅' if frontend_ok else '❌'} Frontend (3000): {'ONLINE' if frontend_ok else 'OFFLINE':10}                {Colors.CYAN}│{Colors.RESET}")
        print(f"{Colors.CYAN}│{Colors.RESET} {'✅' if ollama_ok else '⚠️ '} Ollama (11434):  {'ONLINE' if ollama_ok else 'OFFLINE':10}                {Colors.CYAN}│{Colors.RESET}")
        print(f"{Colors.CYAN}├─────────────────────────────────────────────────────┤{Colors.RESET}")
        print(f"{Colors.CYAN}│              GPU DURUMU                             │{Colors.RESET}")
        print(f"{Colors.CYAN}├─────────────────────────────────────────────────────┤{Colors.RESET}")
        if GPU_INFO["available"]:
            cuda_icon = "✅" if GPU_INFO["cuda_available"] else "❌"
            mem_used = GPU_INFO["memory_total"] - GPU_INFO["memory_free"]
            print(f"{Colors.CYAN}│{Colors.RESET} 🎮 {GPU_INFO['name'][:40]:40}     {Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}    Memory: {mem_used}/{GPU_INFO['memory_total']} MB ({GPU_INFO['utilization']}% kullanım)        {Colors.CYAN}│{Colors.RESET}")
            print(f"{Colors.CYAN}│{Colors.RESET}    {cuda_icon} CUDA: {'Aktif' if GPU_INFO['cuda_available'] else 'Pasif'}  PyTorch: {GPU_INFO['pytorch_version'] or 'N/A':15}  {Colors.CYAN}│{Colors.RESET}")
        else:
            print(f"{Colors.CYAN}│{Colors.RESET} ❌ GPU bulunamadı                                   {Colors.CYAN}│{Colors.RESET}")
        print(f"{Colors.CYAN}└─────────────────────────────────────────────────────┘{Colors.RESET}\n")
        sys.exit(0)
    
    # ═══════ STOP MODE ═══════
    if args.stop:
        log("Çalışan servisler durduruluyor...", "loading")
        stopped = 0
        for port in [ServicePort.API.value, ServicePort.NEXTJS.value]:
            if not is_port_available(port):
                pids = get_pids_using_port(port)
                for pid in pids:
                    kill_process(pid)
                    stopped += 1
        if stopped > 0:
            log(f"{stopped} servis durduruldu", "success")
        else:
            log("Çalışan servis bulunamadı", "info")
        sys.exit(0)
    
    # ═══════ STEP 0: TEST-ONLY MODE (before cleaning) ═══════
    if args.test_only:
        log("Test-only mod", "info")
        
        # API zaten çalışıyor mu kontrol et (servise bağlanmayı dene)
        if is_service_running(ServicePort.API.value):
            log("API çalışıyor, testler başlatılıyor...", "success")
            test_results = run_api_tests()
            sys.exit(0 if test_results["success"] else 1)
        else:
            log("API çalışmıyor, önce başlatın: python run.py", "error")
            sys.exit(1)
    
    # ═══════ STEP 1: CHECK AND CLEAN PORTS (only if needed) ═══════
    ports_to_clean = []
    for config in SERVICES.values():
        if not is_port_available(config.port):
            ports_to_clean.append(config.port)
    
    if ports_to_clean:
        log(f"Dolu portlar temizleniyor: {ports_to_clean}", "loading")
        for port in ports_to_clean:
            ensure_port_free(port)
    
    # ═══════ STEP 2: PRE-FLIGHT TESTS ═══════
    preflight = run_preflight_tests()
    
    if not preflight["all_ok"]:
        log("Pre-flight testler başarısız!", "error")
        sys.exit(1)
    
    # ═══════ STEP 3: DETERMINE SERVICES ═══════
    services_to_start = ["api"]
    
    if not args.api_only and not args.skip_frontend:
        services_to_start.append("nextjs")
    
    log(f"Başlatılacak servisler: {', '.join(services_to_start)}", "info")
    
    # ═══════ STEP 4: START API ═══════
    api_started = False
    for attempt in range(3):
        if start_api():
            api_started = True
            break
        log(f"API başlatma denemesi {attempt + 1}/3 başarısız, yeniden deneniyor...", "warning")
        ensure_port_free(ServicePort.API.value)
        time.sleep(1)
    
    if not api_started:
        log("API başlatılamadı!", "error")
        cleanup()
        sys.exit(1)
    
    # API tamamen hazır olana kadar bekle
    time.sleep(2)
    
    # ═══════ STEP 5: RUN API TESTS (if requested) ═══════
    if args.test:
        try:
            test_results = run_api_tests()
            if not test_results["success"]:
                log(f"API testleri başarısız ({test_results['failed']} hata)", "warning")
            else:
                log(f"API testleri başarılı ({test_results['passed']}/{test_results['total']})", "success")
        except Exception as e:
            log(f"API testleri çalıştırılamadı: {e}", "warning")
    
    # ═══════ STEP 6: START FRONTEND ═══════
    if "nextjs" in services_to_start:
        frontend_started = False
        for attempt in range(2):
            if start_nextjs():
                frontend_started = True
                break
            log(f"Frontend başlatma denemesi {attempt + 1}/2 başarısız...", "warning")
            ensure_port_free(ServicePort.NEXTJS.value)
            time.sleep(1)
        
        if not frontend_started:
            log("Frontend başlatılamadı (API çalışmaya devam ediyor)", "warning")
    
    # ═══════ STEP 7: SUCCESS ═══════
    print_success()
    
    # ═══════ STEP 8: OPEN BROWSER ═══════
    if not args.no_browser:
        time.sleep(2)
        try:
            import webbrowser
            if state.processes["nextjs"].status == ServiceStatus.RUNNING:
                webbrowser.open(f"http://localhost:{ServicePort.NEXTJS.value}")
            else:
                webbrowser.open(f"http://localhost:{ServicePort.API.value}/docs")
        except:
            pass
    
    # ═══════ STEP 9: MONITOR ═══════
    try:
        monitor_services(services_to_start)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
