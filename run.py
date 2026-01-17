"""
Enterprise AI Assistant - Run Script
Endüstri Standartlarında Kurumsal AI Çözümü

Tek komutla tüm sistemi başlat - SIFIR SORUN GARANTİSİ.
Port temizleme, auto-restart ve health check dahil.

Kullanım:
  python run.py              # Varsayılan: Streamlit frontend
  python run.py --next       # Next.js frontend kullan
  python run.py --all        # Tüm frontend'leri başlat
  python run.py --api-only   # Sadece API başlat
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

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# SABIT PORTLAR - değiştirme
API_PORT = 8001
STREAMLIT_PORT = 8501
NEXTJS_PORT = 3000

# Global process references for cleanup
_processes = {
    "api": None,
    "streamlit": None,
    "nextjs": None,
}
_shutdown_requested = False


def cleanup_on_exit():
    """Çıkışta tüm process'leri temizle."""
    global _processes, _shutdown_requested
    _shutdown_requested = True
    
    for name, proc in _processes.items():
        if proc is not None:
            try:
                print(f"   🛑 {name} durduruluyor...")
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass


def kill_port(port: int) -> bool:
    """Belirtilen porttaki TÜM process'leri öldür."""
    try:
        if sys.platform == 'win32':
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'tcp'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            pids_killed = set()
            for line in result.stdout.split('\n'):
                if f':{port}' in line and ('LISTENING' in line or 'ESTABLISHED' in line or 'TIME_WAIT' in line):
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit() and pid != '0' and pid not in pids_killed:
                            try:
                                subprocess.run(
                                    ['taskkill', '/F', '/PID', pid],
                                    capture_output=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                pids_killed.add(pid)
                            except:
                                pass
            
            return len(pids_killed) > 0
        else:
            subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True)
            return True
    except:
        pass
    return False


def is_port_available(port: int) -> bool:
    """Port kullanılabilir mi kontrol et."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.bind(('127.0.0.1', port))
            return True
    except:
        return False


def ensure_port_available(port: int) -> bool:
    """Port'un kullanılabilir olmasını GARANTILE."""
    if is_port_available(port):
        return True
    
    print(f"   ⚠️ Port {port} meşgul, temizleniyor...")
    
    for attempt in range(3):
        kill_port(port)
        time.sleep(0.5)
        
        if is_port_available(port):
            print(f"   ✅ Port {port} temizlendi")
            return True
        
        time.sleep(1)
    
    return False


def check_ollama() -> bool:
    """Ollama'nın çalışıp çalışmadığını kontrol et."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=3)
        return response.status_code == 200
    except:
        return False


def start_ollama() -> bool:
    """Ollama'yı başlat."""
    if check_ollama():
        return True
    
    print("   Ollama başlatılıyor...")
    
    try:
        if sys.platform == 'win32':
            ollama_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Ollama\ollama.exe"),
                r"C:\Program Files\Ollama\ollama.exe",
            ]
            
            for ollama_path in ollama_paths:
                if os.path.exists(ollama_path):
                    subprocess.Popen(
                        [ollama_path, "serve"],
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
                return True
        
    except Exception as e:
        print(f"   ⚠️ Ollama başlatma hatası: {e}")
    
    return check_ollama()


def wait_for_api(port: int, max_retries: int = 30) -> bool:
    """API'nin GERÇEKTEN hazır olmasını bekle."""
    import requests
    
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=3)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    return True
        except:
            pass
        
        if i > 0 and i % 5 == 0:
            print(f"   ⏳ API bekleniyor... ({i}/{max_retries})")
        
        time.sleep(1)
    
    return False


def run_api(port: int):
    """API sunucusunu başlat - ROBUST."""
    global _processes
    
    env = os.environ.copy()
    env['API_PORT'] = str(port)
    env['PYTHONUNBUFFERED'] = '1'
    
    if sys.platform == 'win32':
        _processes["api"] = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app",
             "--host", "0.0.0.0",
             "--port", str(port),
             "--log-level", "warning"],
            cwd=str(PROJECT_ROOT),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        _processes["api"] = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api.main:app",
             "--host", "0.0.0.0",
             "--port", str(port),
             "--log-level", "warning"],
            cwd=str(PROJECT_ROOT),
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    
    return _processes["api"]


def run_streamlit(port: int, api_port: int):
    """Streamlit frontend'i başlat - ROBUST."""
    global _processes
    
    frontend_path = PROJECT_ROOT / "frontend" / "app.py"
    
    if not frontend_path.exists():
        print(f"   ⚠️ Streamlit frontend bulunamadı: {frontend_path}")
        return None
    
    env = os.environ.copy()
    env['API_BASE_URL'] = f'http://localhost:{api_port}'
    env['STREAMLIT_SERVER_PORT'] = str(port)
    env['PYTHONUNBUFFERED'] = '1'
    
    if sys.platform == 'win32':
        _processes["streamlit"] = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(frontend_path),
             "--server.port", str(port),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            cwd=str(PROJECT_ROOT),
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        _processes["streamlit"] = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(frontend_path),
             "--server.port", str(port),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            cwd=str(PROJECT_ROOT),
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    
    return _processes["streamlit"]


def check_node_installed() -> bool:
    """Node.js kurulu mu kontrol et."""
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


def check_npm_installed() -> bool:
    """npm kurulu mu kontrol et."""
    try:
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            shell=True if sys.platform == 'win32' else False
        )
        return result.returncode == 0
    except:
        return False


def install_nextjs_deps() -> bool:
    """Next.js bağımlılıklarını yükle."""
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    node_modules = nextjs_dir / "node_modules"
    
    if node_modules.exists() and (node_modules / "next").exists():
        return True
    
    print("   📦 Next.js bağımlılıkları yükleniyor (ilk seferde gerekli)...")
    
    try:
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(nextjs_dir),
            capture_output=True,
            text=True,
            timeout=300,
            shell=True if sys.platform == 'win32' else False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ npm install hatası: {e}")
        return False


def run_nextjs(port: int, api_port: int, dev_mode: bool = False):
    """Next.js frontend'i başlat."""
    global _processes
    
    nextjs_dir = PROJECT_ROOT / "frontend-next"
    
    if not nextjs_dir.exists():
        print(f"   ⚠️ Next.js frontend bulunamadı: {nextjs_dir}")
        return None
    
    # Node.js kontrol et
    if not check_node_installed():
        print("   ❌ Node.js kurulu değil! https://nodejs.org adresinden indirin.")
        return None
    
    # Bağımlılıkları yükle
    if not install_nextjs_deps():
        print("   ❌ Next.js bağımlılıkları yüklenemedi!")
        return None
    
    env = os.environ.copy()
    env['NEXT_PUBLIC_API_URL'] = f'http://localhost:{api_port}'
    env['PORT'] = str(port)
    
    # Production build kontrol
    next_build = nextjs_dir / ".next"
    
    if dev_mode or not next_build.exists():
        # Development mode
        cmd = ["npm", "run", "dev"]
        mode_text = "development"
    else:
        # Production mode
        cmd = ["npm", "run", "start"]
        mode_text = "production"
    
    print(f"   🔧 Next.js {mode_text} mode başlatılıyor...")
    
    if sys.platform == 'win32':
        _processes["nextjs"] = subprocess.Popen(
            cmd,
            cwd=str(nextjs_dir),
            env=env,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    else:
        _processes["nextjs"] = subprocess.Popen(
            cmd,
            cwd=str(nextjs_dir),
            env=env,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    
    return _processes["nextjs"]


def wait_for_service(url: str, name: str, max_retries: int = 30) -> bool:
    """Servisin hazır olmasını bekle."""
    import requests
    
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=3)
            if response.status_code in [200, 304]:
                return True
        except:
            pass
        
        if i > 0 and i % 5 == 0:
            print(f"   ⏳ {name} bekleniyor... ({i}/{max_retries})")
        
        time.sleep(1)
    
    return False


def parse_args():
    """Komut satırı argümanlarını parse et."""
    parser = argparse.ArgumentParser(
        description="Enterprise AI Assistant - Tek komutla tüm sistemi başlat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python run.py              # Varsayılan: Streamlit frontend
  python run.py --next       # Next.js frontend kullan
  python run.py --all        # Tüm frontend'leri başlat
  python run.py --api-only   # Sadece API başlat
  python run.py --dev        # Development mode (hot reload)
        """
    )
    
    parser.add_argument(
        "--next", "-n",
        action="store_true",
        help="Next.js frontend kullan (port 3000)"
    )
    parser.add_argument(
        "--streamlit", "-s",
        action="store_true",
        help="Streamlit frontend kullan (port 8501) [varsayılan]"
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Tüm frontend'leri başlat (Streamlit + Next.js)"
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Sadece API sunucusunu başlat"
    )
    parser.add_argument(
        "--dev", "-d",
        action="store_true",
        help="Development mode (hot reload aktif)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Tarayıcıyı otomatik açma"
    )
    parser.add_argument(
        "--skip-ollama",
        action="store_true",
        help="Ollama kontrolünü atla"
    )
    
    return parser.parse_args()


def main():
    """Ana çalıştırma fonksiyonu - SORUNSUZ."""
    global _processes, _shutdown_requested
    
    # Argümanları parse et
    args = parse_args()
    
    # Cleanup handler kaydet
    atexit.register(cleanup_on_exit)
    
    # Signal handler
    def signal_handler(sig, frame):
        global _shutdown_requested
        _shutdown_requested = True
        print("\n\n🛑 Kapatılıyor...")
        cleanup_on_exit()
        print("✅ Güle güle!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🤖 Enterprise AI Assistant")
    print("   Endüstri Standartlarında Kurumsal AI Çözümü")
    print("=" * 60)
    
    # Hangi frontend'leri başlatacağımızı belirle
    use_streamlit = args.streamlit or args.all or (not args.next and not args.api_only)
    use_nextjs = args.next or args.all
    api_only = args.api_only
    
    # ===== STEP 1: OLLAMA =====
    if not args.skip_ollama:
        print("\n📡 Ollama kontrol ediliyor...")
        if not start_ollama():
            print("⚠️ Ollama başlatılamadı!")
            print("   → Ollama uygulamasını manuel başlatın veya --skip-ollama kullanın")
            try:
                user_input = input("\n   Devam etmek için Enter'a basın (Ollama olmadan) veya 'q' ile çıkın: ")
                if user_input.lower() == 'q':
                    return
            except:
                pass
        else:
            print("✅ Ollama aktif")
    else:
        print("\n⏭️ Ollama kontrolü atlandı")
    
    # ===== STEP 2: DIRECTORIES =====
    print("\n📁 Klasörler hazırlanıyor...")
    try:
        from core.config import settings
        settings.ensure_directories()
        print("✅ Klasörler hazır")
    except Exception as e:
        print(f"⚠️ Klasör hatası (devam ediliyor): {e}")
    
    # ===== STEP 3: PORTS =====
    print("\n🔌 Portlar hazırlanıyor...")
    
    if not ensure_port_available(API_PORT):
        print(f"❌ API portu ({API_PORT}) temizlenemedi!")
        return
    print(f"   ✅ API port: {API_PORT}")
    
    if use_streamlit:
        if not ensure_port_available(STREAMLIT_PORT):
            print(f"❌ Streamlit portu ({STREAMLIT_PORT}) temizlenemedi!")
            return
        print(f"   ✅ Streamlit port: {STREAMLIT_PORT}")
    
    if use_nextjs:
        if not ensure_port_available(NEXTJS_PORT):
            print(f"❌ Next.js portu ({NEXTJS_PORT}) temizlenemedi!")
            return
        print(f"   ✅ Next.js port: {NEXTJS_PORT}")
    
    # ===== STEP 4: START SERVICES =====
    print("\n🚀 Servisler başlatılıyor...")
    
    try:
        # Start API
        print(f"   📡 API başlatılıyor...")
        run_api(API_PORT)
        
        # API'nin hazır olmasını bekle
        print(f"   ⏳ API hazır olması bekleniyor...")
        if not wait_for_service(f"http://localhost:{API_PORT}/health", "API", max_retries=30):
            print("   ⚠️ API health check zaman aşımı, yine de devam ediliyor...")
        else:
            print(f"   ✅ API hazır!")
        
        # Sadece API modunda frontend başlatma
        if api_only:
            print("\n" + "=" * 60)
            print("✅ API BAŞLATILDI (Frontend yok)")
            print("=" * 60)
            print(f"\n📍 API: http://localhost:{API_PORT}")
            print(f"📚 Docs: http://localhost:{API_PORT}/docs")
            print("\n⌨️  Durdurmak için Ctrl+C")
            print("=" * 60)
            
            if not args.no_browser:
                try:
                    webbrowser.open(f"http://localhost:{API_PORT}/docs")
                except:
                    pass
        else:
            # Start Streamlit
            if use_streamlit:
                print(f"   🎨 Streamlit başlatılıyor...")
                run_streamlit(STREAMLIT_PORT, API_PORT)
                time.sleep(2)
            
            # Start Next.js
            if use_nextjs:
                print(f"   ⚛️ Next.js başlatılıyor...")
                run_nextjs(NEXTJS_PORT, API_PORT, dev_mode=args.dev)
                time.sleep(3)
            
            # Success message
            print("\n" + "=" * 60)
            print("✅ Enterprise AI Assistant BAŞLATILDI!")
            print("=" * 60)
            print("\n📍 Erişim Adresleri:")
            
            primary_url = None
            
            if use_streamlit:
                print(f"   🎨 Streamlit: http://localhost:{STREAMLIT_PORT}")
                primary_url = f"http://localhost:{STREAMLIT_PORT}"
            
            if use_nextjs:
                print(f"   ⚛️ Next.js:   http://localhost:{NEXTJS_PORT}")
                if not primary_url:
                    primary_url = f"http://localhost:{NEXTJS_PORT}"
            
            print(f"   📡 API:       http://localhost:{API_PORT}")
            print(f"   📚 API Docs:  http://localhost:{API_PORT}/docs")
            print("\n⌨️  Durdurmak için Ctrl+C")
            print("=" * 60)
            
            # Tarayıcı aç
            if not args.no_browser and primary_url:
                time.sleep(1)
                try:
                    webbrowser.open(primary_url)
                except:
                    pass
        
        # Process'leri izle ve gerekirse yeniden başlat
        while not _shutdown_requested:
            # API durdu mu?
            if _processes["api"] and _processes["api"].poll() is not None:
                print("\n⚠️ API durdu, yeniden başlatılıyor...")
                time.sleep(2)
                ensure_port_available(API_PORT)
                run_api(API_PORT)
                wait_for_service(f"http://localhost:{API_PORT}/health", "API", max_retries=15)
            
            # Streamlit durdu mu?
            if use_streamlit and _processes["streamlit"] and _processes["streamlit"].poll() is not None:
                print("\n⚠️ Streamlit durdu, yeniden başlatılıyor...")
                time.sleep(2)
                ensure_port_available(STREAMLIT_PORT)
                run_streamlit(STREAMLIT_PORT, API_PORT)
            
            # Next.js durdu mu?
            if use_nextjs and _processes["nextjs"] and _processes["nextjs"].poll() is not None:
                print("\n⚠️ Next.js durdu, yeniden başlatılıyor...")
                time.sleep(2)
                ensure_port_available(NEXTJS_PORT)
                run_nextjs(NEXTJS_PORT, API_PORT, dev_mode=args.dev)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cleanup_on_exit()


if __name__ == "__main__":
    main()
