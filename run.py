"""
Enterprise AI Assistant - Run Script
Endüstri Standartlarında Kurumsal AI Çözümü

Tek komutla tüm sistemi başlat - SIFIR SORUN GARANTİSİ.
Port temizleme, auto-restart ve health check dahil.
"""

import subprocess
import sys
import os
import time
import webbrowser
import socket
import atexit
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# SABIT PORTLAR - değiştirme
API_PORT = 8001
FRONTEND_PORT = 8501

# Global process references for cleanup
_api_process = None
_frontend_process = None


def cleanup_on_exit():
    """Çıkışta tüm process'leri temizle."""
    global _api_process, _frontend_process
    
    if _api_process:
        try:
            _api_process.terminate()
            _api_process.wait(timeout=3)
        except:
            try:
                _api_process.kill()
            except:
                pass
    
    if _frontend_process:
        try:
            _frontend_process.terminate()
            _frontend_process.wait(timeout=3)
        except:
            try:
                _frontend_process.kill()
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
    global _api_process
    
    env = os.environ.copy()
    env['API_PORT'] = str(port)
    env['PYTHONUNBUFFERED'] = '1'
    
    if sys.platform == 'win32':
        _api_process = subprocess.Popen(
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
        _api_process = subprocess.Popen(
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
    
    return _api_process


def run_frontend(port: int, api_port: int):
    """Streamlit frontend'i başlat - ROBUST."""
    global _frontend_process
    
    frontend_path = PROJECT_ROOT / "frontend" / "app.py"
    
    env = os.environ.copy()
    env['API_BASE_URL'] = f'http://localhost:{api_port}'
    env['STREAMLIT_SERVER_PORT'] = str(port)
    env['PYTHONUNBUFFERED'] = '1'
    
    if sys.platform == 'win32':
        _frontend_process = subprocess.Popen(
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
        _frontend_process = subprocess.Popen(
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
    
    return _frontend_process


def main():
    """Ana çalıştırma fonksiyonu - SORUNSUZ."""
    global _api_process, _frontend_process
    
    # Cleanup handler kaydet
    atexit.register(cleanup_on_exit)
    
    print("=" * 60)
    print("🤖 Enterprise AI Assistant")
    print("   Endüstri Standartlarında Kurumsal AI Çözümü")
    print("=" * 60)
    
    # ===== STEP 1: OLLAMA =====
    print("\n📡 Ollama kontrol ediliyor...")
    if not start_ollama():
        print("❌ Ollama başlatılamadı!")
        print("   → Ollama uygulamasını manuel başlatın")
        input("\n   Ollama'yı başlattıktan sonra Enter'a basın...")
        if not check_ollama():
            print("❌ Ollama hala çalışmıyor. Çıkılıyor.")
            return
    print("✅ Ollama aktif")
    
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
    
    if not ensure_port_available(FRONTEND_PORT):
        print(f"❌ Frontend portu ({FRONTEND_PORT}) temizlenemedi!")
        return
    print(f"   ✅ Frontend port: {FRONTEND_PORT}")
    
    # ===== STEP 4: START SERVICES =====
    print("\n🚀 Servisler başlatılıyor...")
    
    try:
        # Start API
        print(f"   📡 API başlatılıyor...")
        api_proc = run_api(API_PORT)
        
        # API'nin hazır olmasını bekle
        print(f"   ⏳ API hazır olması bekleniyor...")
        if not wait_for_api(API_PORT, max_retries=30):
            print("   ⚠️ API health check zaman aşımı, yine de devam ediliyor...")
        else:
            print(f"   ✅ API hazır!")
        
        # Start Frontend
        print(f"   🌐 Frontend başlatılıyor...")
        frontend_proc = run_frontend(FRONTEND_PORT, API_PORT)
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("✅ Enterprise AI Assistant BAŞLATILDI!")
        print("=" * 60)
        print("\n📍 Erişim Adresleri:")
        print(f"   🌐 Frontend: http://localhost:{FRONTEND_PORT}")
        print(f"   📡 API:      http://localhost:{API_PORT}")
        print(f"   📚 API Docs: http://localhost:{API_PORT}/docs")
        print("\n⌨️  Durdurmak için Ctrl+C")
        print("=" * 60)
        
        # Tarayıcı aç
        time.sleep(1)
        try:
            webbrowser.open(f"http://localhost:{FRONTEND_PORT}")
        except:
            pass
        
        # Process'leri izle ve gerekirse yeniden başlat
        while True:
            # API durdu mu?
            if api_proc.poll() is not None:
                print("\n⚠️ API durdu, yeniden başlatılıyor...")
                time.sleep(2)
                ensure_port_available(API_PORT)
                api_proc = run_api(API_PORT)
                wait_for_api(API_PORT, max_retries=15)
            
            # Frontend durdu mu?
            if frontend_proc.poll() is not None:
                print("\n⚠️ Frontend durdu, yeniden başlatılıyor...")
                time.sleep(2)
                ensure_port_available(FRONTEND_PORT)
                frontend_proc = run_frontend(FRONTEND_PORT, API_PORT)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Kapatılıyor...")
        cleanup_on_exit()
        print("✅ Güle güle!")
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        cleanup_on_exit()


if __name__ == "__main__":
    main()
