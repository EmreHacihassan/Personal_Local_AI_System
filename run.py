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
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


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
        models = client.list()
        model_names = [m["name"] for m in models.get("models", [])]
        
        required = ["qwen2.5", "nomic-embed-text"]
        missing = []
        
        for req in required:
            if not any(req in m for m in model_names):
                missing.append(req)
        
        return missing
    except Exception as e:
        print(f"Model kontrolü hatası: {e}")
        return ["qwen2.5:7b", "nomic-embed-text"]


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


def run_api():
    """API sunucusunu başlat."""
    api_path = PROJECT_ROOT / "api" / "main.py"
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=str(PROJECT_ROOT),
    )


def run_frontend():
    """Streamlit frontend'i başlat."""
    frontend_path = PROJECT_ROOT / "frontend" / "app.py"
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(frontend_path), "--server.port", "8501"],
        cwd=str(PROJECT_ROOT),
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
    
    # Step 4: Start services
    print("\n🚀 Servisler başlatılıyor...")
    
    try:
        # Start API
        print("   📡 API başlatılıyor (port 8000)...")
        api_process = run_api()
        time.sleep(3)
        
        # Start Frontend
        print("   🌐 Frontend başlatılıyor (port 8501)...")
        frontend_process = run_frontend()
        time.sleep(3)
        
        print("\n" + "=" * 60)
        print("✅ Enterprise AI Assistant başarıyla başlatıldı!")
        print("=" * 60)
        print("\n📍 Erişim Adresleri:")
        print("   🌐 Frontend: http://localhost:8501")
        print("   📡 API:      http://localhost:8000")
        print("   📚 API Docs: http://localhost:8000/docs")
        print("\n⌨️  Durdurmak için Ctrl+C")
        print("=" * 60)
        
        # Open browser
        time.sleep(2)
        webbrowser.open("http://localhost:8501")
        
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
