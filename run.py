"""
Enterprise AI Assistant - Run Script
Endüstri Standartlarında Kurumsal AI Çözümü

Uygulamayı başlatmak için ana script.
"""

import subprocess
import sys
import os
import time
import webbrowser
import socket
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Default ports
DEFAULT_API_PORT = 8001
DEFAULT_FRONTEND_PORT = 8501


def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    """Boş port bul. Meşgulse bir sonrakini dene."""
    port = start_port
    for _ in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            print(f"   ⚠️ Port {port} meşgul, {port + 1} deneniyor...")
            port += 1
    raise RuntimeError(f"Boş port bulunamadı ({start_port}-{start_port + max_attempts})")


def kill_process_on_port(port: int) -> bool:
    """Belirtilen porttaki işlemi sonlandır."""
    try:
        if sys.platform == 'win32':
            # Windows için
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    pid = parts[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
                    return True
        else:
            # Linux/Mac için
            subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True)
            return True
    except Exception:
        pass
    return False


def check_ollama():
    """Ollama'nın çalışıp çalışmadığını kontrol et."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_models():
    """Gerekli modellerin yüklü olup olmadığını kontrol et."""
    try:
        import ollama
        client = ollama.Client()
        result = client.list()
        
        # Handle both old (dict) and new (object) API formats
        if hasattr(result, 'models'):
            # New API: result.models is a list of Model objects
            model_names = [m.model for m in result.models]
        elif isinstance(result, dict):
            # Old API: result is a dict with 'models' key
            model_list = result.get("models", [])
            model_names = []
            for m in model_list:
                if isinstance(m, dict):
                    model_names.append(m.get("name", m.get("model", "")))
                else:
                    model_names.append(str(m))
        else:
            model_names = []
        
        required = ["qwen", "nomic-embed-text"]  # qwen3-vl veya qwen2.5 olabilir
        missing = []
        
        for req in required:
            if not any(req in m.lower() for m in model_names):
                missing.append(req)
        
        return missing
    except Exception as e:
        print(f"Model kontrolü hatası: {e}")
        return []  # Hata olursa model indirmeye zorlamayalım


def pull_models(models):
    """Eksik modelleri indir."""
    import ollama
    client = ollama.Client()
    
    for model in models:
        print(f"\n📥 {model} indiriliyor...")
        try:
            client.pull(model)
            print(f"✅ {model} indirildi")
        except Exception as e:
            print(f"❌ {model} indirilemedi: {e}")


def run_api(port: int):
    """API sunucusunu başlat."""
    env = os.environ.copy()
    env['API_PORT'] = str(port)
    
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", str(port)],
        cwd=str(PROJECT_ROOT),
        env=env,
    )


def run_frontend(port: int, api_port: int):
    """Streamlit frontend'i başlat."""
    frontend_path = PROJECT_ROOT / "frontend" / "app.py"
    
    env = os.environ.copy()
    env['API_BASE_URL'] = f'http://localhost:{api_port}'
    env['STREAMLIT_SERVER_PORT'] = str(port)
    
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(frontend_path), 
         "--server.port", str(port),
         "--server.headless", "true"],
        cwd=str(PROJECT_ROOT),
        env=env,
    )


def main():
    """Ana çalıştırma fonksiyonu."""
    print("=" * 60)
    print("🤖 Enterprise AI Assistant")
    print("   Endüstri Standartlarında Kurumsal AI Çözümü")
    print("=" * 60)
    
    # Step 1: Check Ollama
    print("\n📡 Ollama kontrol ediliyor...")
    if not check_ollama():
        print("❌ Ollama çalışmıyor!")
        print("   Lütfen önce Ollama'yı başlatın: https://ollama.ai")
        print("   Windows'ta: Ollama uygulamasını çalıştırın")
        return
    print("✅ Ollama aktif")
    
    # Step 2: Check models
    print("\n🔍 Modeller kontrol ediliyor...")
    missing_models = check_models()
    
    if missing_models:
        print(f"⚠️ Eksik modeller: {', '.join(missing_models)}")
        response = input("İndirmek ister misiniz? (e/h): ")
        if response.lower() == 'e':
            pull_models(missing_models)
        else:
            print("⚠️ Modeller olmadan sistem düzgün çalışmayabilir")
    else:
        print("✅ Tüm modeller mevcut")
    
    # Step 3: Create directories
    print("\n📁 Klasörler kontrol ediliyor...")
    from core.config import settings
    settings.ensure_directories()
    print("✅ Klasörler hazır")
    
    # Step 4: Find free ports
    print("\n🔌 Portlar kontrol ediliyor...")
    
    api_port = find_free_port(DEFAULT_API_PORT)
    print(f"   ✅ API port: {api_port}")
    
    frontend_port = find_free_port(DEFAULT_FRONTEND_PORT)
    print(f"   ✅ Frontend port: {frontend_port}")
    
    # Step 5: Start services
    print("\n🚀 Servisler başlatılıyor...")
    
    try:
        # Start API
        print(f"   📡 API başlatılıyor (port {api_port})...")
        api_process = run_api(api_port)
        time.sleep(3)
        
        # Start Frontend
        print(f"   🌐 Frontend başlatılıyor (port {frontend_port})...")
        frontend_process = run_frontend(frontend_port, api_port)
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("✅ Enterprise AI Assistant başarıyla başlatıldı!")
        print("=" * 60)
        print("\n📍 Erişim Adresleri:")
        print(f"   🌐 Frontend: http://localhost:{frontend_port}")
        print(f"   📡 API:      http://localhost:{api_port}")
        print(f"   📚 API Docs: http://localhost:{api_port}/docs")
        print("\n⌨️  Durdurmak için Ctrl+C")
        print("=" * 60)
        
        # Open browser
        time.sleep(2)
        webbrowser.open(f"http://localhost:{frontend_port}")
        
        # Wait for processes
        api_process.wait()
        frontend_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Servisler durduruluyor...")
        api_process.terminate()
        frontend_process.terminate()
        print("✅ Güle güle!")
    except Exception as e:
        print(f"\n❌ Hata: {e}")


if __name__ == "__main__":
    main()
