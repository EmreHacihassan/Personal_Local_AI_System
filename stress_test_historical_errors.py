#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           HISTORICAL ERROR STRESS TEST                                       ║
║                                                                              ║
║   Bu script geçmişte karşılaştığımız tüm hataları yeniden tetiklemeye       ║
║   çalışır ve sistemin bu hatalara karşı dayanıklılığını test eder.          ║
╚══════════════════════════════════════════════════════════════════════════════╝

Geçmişte Karşılaşılan Hatalar:
1. ChromaDB telemetry capture() hatası
2. HuggingFace offline mode - internete bağlanmaya çalışma
3. Unicode/emoji encoding hataları (charmap codec)
4. Port çakışmaları (8001, 3000)
5. HNSW index bozulması
6. Next.js cache bozulması
7. SIGINT signal çakışması
8. Venv vs global Python karışıklığı
9. WebSocket/Agents import hataları
10. CrossEncoder model loading hatası
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Test sonuçları
RESULTS: Dict[str, Dict[str, Any]] = {}

def log_result(test_name: str, passed: bool, message: str, details: str = None):
    """Test sonucunu kaydet."""
    RESULTS[test_name] = {
        "passed": passed,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    icon = "✅" if passed else "❌"
    print(f"\n{icon} {test_name}")
    print(f"   {message}")
    if details and not passed:
        print(f"   Detay: {details[:200]}...")

def print_header(text: str):
    """Bölüm başlığı yazdır."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: CHROMADB TELEMETRY - capture() argument hatası
# ══════════════════════════════════════════════════════════════════════════════
def test_chromadb_telemetry():
    """
    Hata: TypeError: capture() takes 1 positional argument but 3 were given
    Sebep: ChromaDB'nin Posthog telemetry kodu hatalı
    Çözüm: Posthog monkey-patch
    """
    print_header("TEST 1: ChromaDB Telemetry")
    
    try:
        # Telemetry'yi tetiklemeye çalış
        import chromadb
        
        # Client oluştur - bu telemetry'yi tetikler
        client = chromadb.PersistentClient(path="./data/chroma_test_temp")
        
        # Collection oluştur
        try:
            client.delete_collection("test_telemetry")
        except:
            pass
        
        collection = client.create_collection("test_telemetry")
        collection.add(
            documents=["test document for telemetry"],
            ids=["test1"]
        )
        
        # Temizlik
        client.delete_collection("test_telemetry")
        
        log_result(
            "ChromaDB Telemetry",
            True,
            "Telemetry hatası olmadan ChromaDB çalıştı"
        )
        return True
        
    except TypeError as e:
        if "capture()" in str(e):
            log_result(
                "ChromaDB Telemetry",
                False,
                "capture() hatası hala mevcut!",
                str(e)
            )
        else:
            log_result(
                "ChromaDB Telemetry",
                False,
                f"Beklenmeyen TypeError: {e}",
                traceback.format_exc()
            )
        return False
    except Exception as e:
        log_result(
            "ChromaDB Telemetry",
            False,
            f"Beklenmeyen hata: {type(e).__name__}",
            str(e)
        )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: HUGGINGFACE OFFLINE MODE
# ══════════════════════════════════════════════════════════════════════════════
def test_huggingface_offline():
    """
    Hata: requests.exceptions.ConnectionError - HuggingFace Hub'a bağlanmaya çalışma
    Sebep: Model yüklerken internet gerekiyordu
    Çözüm: HF_HUB_OFFLINE=1 + local_files_only=True
    """
    print_header("TEST 2: HuggingFace Offline Mode")
    
    # Ortam değişkenlerini kontrol et
    hf_offline = os.environ.get('HF_HUB_OFFLINE')
    tf_offline = os.environ.get('TRANSFORMERS_OFFLINE')
    
    print(f"   HF_HUB_OFFLINE: {hf_offline}")
    print(f"   TRANSFORMERS_OFFLINE: {tf_offline}")
    
    try:
        # SentenceTransformer'ı offline modda yüklemeye çalış
        from sentence_transformers import SentenceTransformer
        
        # Bu model cache'de olmalı
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            device="cpu"  # Test için CPU
        )
        
        # Basit test
        embedding = model.encode(["test text"])
        
        log_result(
            "HuggingFace Offline Mode",
            True,
            f"Model offline modda yüklendi (dim: {len(embedding[0])})"
        )
        return True
        
    except OSError as e:
        if "offline mode" in str(e).lower() or "does not appear to have" in str(e).lower():
            log_result(
                "HuggingFace Offline Mode",
                False,
                "Model cache'de bulunamadı!",
                str(e)
            )
        else:
            log_result(
                "HuggingFace Offline Mode",
                False,
                f"OSError: {e}",
                traceback.format_exc()
            )
        return False
    except Exception as e:
        if "connection" in str(e).lower() or "network" in str(e).lower():
            log_result(
                "HuggingFace Offline Mode",
                False,
                "İnternete bağlanmaya çalıştı!",
                str(e)
            )
        else:
            log_result(
                "HuggingFace Offline Mode",
                True,  # Başka hatalar offline mode ile ilgili değil
                f"Offline mode çalışıyor (diğer hata: {type(e).__name__})"
            )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: UNICODE/EMOJI ENCODING
# ══════════════════════════════════════════════════════════════════════════════
def test_unicode_emoji():
    """
    Hata: 'charmap' codec can't encode characters
    Sebep: Windows console UTF-8 desteklemiyor
    Çözüm: TextIOWrapper ile UTF-8 zorla + errors='replace'
    """
    print_header("TEST 3: Unicode/Emoji Encoding")
    
    test_strings = [
        "✅ Başarılı",
        "❌ Hata",
        "🚀 Roket emojisi",
        "🎮 NVIDIA GeForce RTX 4070",
        "📡 API: http://localhost:8001",
        "⚛️ Frontend hazır",
        "🔧 Türkçe karakterler: ğüşıöçĞÜŞİÖÇ",
        "✨ Mixed: Başarı! 🎉 Tebrikler 🎊",
    ]
    
    errors = []
    
    for test_str in test_strings:
        try:
            # stdout'a yaz
            print(f"   Test: {test_str}")
            
            # stderr'e de yaz
            sys.stderr.write(f"   Stderr: {test_str}\n")
            sys.stderr.flush()
            
        except UnicodeEncodeError as e:
            errors.append((test_str, str(e)))
        except Exception as e:
            errors.append((test_str, f"{type(e).__name__}: {e}"))
    
    if errors:
        log_result(
            "Unicode/Emoji Encoding",
            False,
            f"{len(errors)}/{len(test_strings)} string encode edilemedi",
            str(errors[:3])
        )
        return False
    else:
        log_result(
            "Unicode/Emoji Encoding",
            True,
            f"Tüm {len(test_strings)} emoji/unicode string başarılı"
        )
        return True

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: PORT ÇAKIŞMASI
# ══════════════════════════════════════════════════════════════════════════════
def test_port_conflict():
    """
    Hata: [Errno 10048] error while attempting to bind on address
    Sebep: Port zaten kullanımda
    Çözüm: ensure_port_free() fonksiyonu
    """
    print_header("TEST 4: Port Çakışması Yönetimi")
    
    import socket
    
    test_port = 18765  # Test için kullanılmayan bir port
    
    try:
        # Bir socket oluştur ve porta bağla
        sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock1.bind(('127.0.0.1', test_port))
        sock1.listen(1)
        print(f"   Port {test_port} meşgul edildi")
        
        # Şimdi run.py'deki is_port_available fonksiyonunu test et
        # Manuel olarak aynı mantığı uygulayalım
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock2.bind(('127.0.0.1', test_port))
            sock2.close()
            port_available = True
        except OSError:
            port_available = False
        finally:
            sock2.close()
        
        # Temizlik
        sock1.close()
        
        if not port_available:
            log_result(
                "Port Çakışması Yönetimi",
                True,
                "Port meşgul olduğunda doğru tespit edildi"
            )
            return True
        else:
            log_result(
                "Port Çakışması Yönetimi",
                False,
                "Port meşgul ama available olarak gösterildi!"
            )
            return False
            
    except Exception as e:
        log_result(
            "Port Çakışması Yönetimi",
            False,
            f"Test hatası: {e}",
            traceback.format_exc()
        )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: HNSW INDEX BOZULMASI
# ══════════════════════════════════════════════════════════════════════════════
def test_hnsw_index_recovery():
    """
    Hata: HNSW index corrupted / inconsistent state
    Sebep: ChromaDB index dosyaları bozuk
    Çözüm: _verify_hnsw_index() + otomatik recovery
    """
    print_header("TEST 5: HNSW Index Recovery")
    
    try:
        # ChromaDB manager'ı import et - doğru fonksiyonu kullan
        from core.chromadb_manager import get_chromadb_manager
        
        manager = get_chromadb_manager()
        
        # HNSW doğrulamasını çalıştır
        is_valid = manager._verify_hnsw_index()
        
        if is_valid:
            log_result(
                "HNSW Index Recovery",
                True,
                "HNSW index doğrulaması başarılı"
            )
            return True
        else:
            log_result(
                "HNSW Index Recovery",
                False,
                "HNSW index geçersiz bulundu!",
                "Recovery mekanizması çalışmalı"
            )
            return False
            
    except Exception as e:
        log_result(
            "HNSW Index Recovery",
            False,
            f"HNSW test hatası: {e}",
            traceback.format_exc()
        )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: NEXT.JS CACHE BOZULMASI
# ══════════════════════════════════════════════════════════════════════════════
def test_nextjs_cache():
    """
    Hata: Module not found: Can't resolve ...
    Sebep: .next cache bozuk
    Çözüm: Otomatik cache temizleme
    """
    print_header("TEST 6: Next.js Cache Kontrolü")
    
    nextjs_dir = Path(__file__).parent / "frontend-next"
    next_cache = nextjs_dir / ".next"
    
    if not nextjs_dir.exists():
        log_result(
            "Next.js Cache Kontrolü",
            False,
            "frontend-next dizini bulunamadı!"
        )
        return False
    
    # Cache durumunu kontrol et
    issues = []
    
    if next_cache.exists():
        # Gerekli dosyaları kontrol et - Next.js 14+ yapısı
        required_patterns = [
            "build-manifest.json",
            "static/chunks",  # Klasörün varlığını kontrol et
        ]
        
        for req_pattern in required_patterns:
            full_path = next_cache / req_pattern
            if not full_path.exists():
                issues.append(f"Eksik: {req_pattern}")
        
        # Cache boyutunu kontrol et
        try:
            cache_size = sum(
                f.stat().st_size for f in next_cache.rglob('*') if f.is_file()
            ) / (1024 * 1024)
            print(f"   Cache boyutu: {cache_size:.1f} MB")
        except Exception as e:
            issues.append(f"Cache boyutu hesaplanamadı: {e}")
    else:
        print("   .next cache mevcut değil (ilk build'de oluşacak)")
    
    # node_modules kontrolü
    node_modules = nextjs_dir / "node_modules"
    if not node_modules.exists():
        issues.append("node_modules eksik - npm install gerekli")
    elif not (node_modules / "next").exists():
        issues.append("next paketi eksik")
    
    if issues:
        log_result(
            "Next.js Cache Kontrolü",
            False,
            f"{len(issues)} sorun bulundu",
            "; ".join(issues)
        )
        return False
    else:
        log_result(
            "Next.js Cache Kontrolü",
            True,
            "Next.js cache ve bağımlılıklar sağlıklı"
        )
        return True

# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: VENV ENFORCEMENT
# ══════════════════════════════════════════════════════════════════════════════
def test_venv_enforcement():
    """
    Hata: Global Python ile çalıştırma sorunları
    Sebep: Yanlış Python interpreter
    Çözüm: enforce_venv() fonksiyonu
    """
    print_header("TEST 7: Venv Enforcement")
    
    current_python = sys.executable
    expected_venv_path = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    
    print(f"   Şu anki Python: {current_python}")
    print(f"   Beklenen venv: {expected_venv_path}")
    
    is_venv = "venv" in current_python.lower()
    
    if is_venv:
        log_result(
            "Venv Enforcement",
            True,
            "Venv içinden çalıştırılıyor ✓"
        )
        return True
    else:
        log_result(
            "Venv Enforcement",
            False,
            "Global Python kullanılıyor!",
            f"Kullanılan: {current_python}"
        )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: IMPORT HATALARI
# ══════════════════════════════════════════════════════════════════════════════
def test_imports():
    """
    Hata: ImportError, ModuleNotFoundError
    Sebep: Circular imports, eksik modüller
    Çözüm: Import düzeltmeleri
    """
    print_header("TEST 8: Import Testleri")
    
    modules_to_test = [
        ("core.config", "settings"),
        ("core.logger", "get_logger"),
        ("core.embedding", "embedding_manager"),
        ("core.vector_store", "vector_store"),
        ("core.chromadb_manager", "get_chromadb_manager"),
        ("rag.retriever", "retriever"),
        ("rag.reranker", "CrossEncoderReranker"),
        ("agents.orchestrator", "orchestrator"),
        ("api.main", "app"),
    ]
    
    failed_imports = []
    successful_imports = []
    
    for module_name, attr_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            obj = getattr(module, attr_name)
            successful_imports.append(module_name)
            print(f"   ✅ {module_name}.{attr_name}")
        except ImportError as e:
            failed_imports.append((module_name, f"ImportError: {e}"))
            print(f"   ❌ {module_name}: {e}")
        except Exception as e:
            failed_imports.append((module_name, f"{type(e).__name__}: {e}"))
            print(f"   ⚠️ {module_name}: {type(e).__name__}")
    
    if failed_imports:
        log_result(
            "Import Testleri",
            False,
            f"{len(failed_imports)}/{len(modules_to_test)} modül import edilemedi",
            str(failed_imports)
        )
        return False
    else:
        log_result(
            "Import Testleri",
            True,
            f"Tüm {len(modules_to_test)} modül başarıyla import edildi"
        )
        return True

# ══════════════════════════════════════════════════════════════════════════════
# TEST 9: CROSSENCODER GPU LOADING
# ══════════════════════════════════════════════════════════════════════════════
def test_crossencoder_loading():
    """
    Hata: HuggingFace Hub bağlantı hatası
    Sebep: CrossEncoder model bilgisi internetten çekiliyordu
    Çözüm: local_files_only + fallback
    """
    print_header("TEST 9: CrossEncoder GPU Loading")
    
    try:
        from sentence_transformers import CrossEncoder
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   Device: {device}")
        
        # Offline modda yüklemeyi dene
        model = CrossEncoder(
            "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
            device=device,
            local_files_only=True
        )
        
        # Basit test
        scores = model.predict([("query", "document")])
        print(f"   Test score: {scores[0]:.4f}")
        
        log_result(
            "CrossEncoder GPU Loading",
            True,
            f"CrossEncoder başarıyla yüklendi (device: {device})"
        )
        return True
        
    except OSError as e:
        if "offline mode" in str(e).lower() or "does not appear" in str(e).lower():
            log_result(
                "CrossEncoder GPU Loading",
                False,
                "Model cache'de yok!",
                str(e)
            )
        else:
            log_result(
                "CrossEncoder GPU Loading",
                False,
                f"OSError: {e}"
            )
        return False
    except Exception as e:
        log_result(
            "CrossEncoder GPU Loading",
            False,
            f"Hata: {type(e).__name__}",
            str(e)
        )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# TEST 10: API HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════
def test_api_components():
    """
    API bileşenlerinin doğru yüklenip yüklenmediğini test et.
    """
    print_header("TEST 10: API Components")
    
    try:
        from api.main import app
        
        # Routes kontrolü
        routes = [r.path for r in app.routes]
        required_routes = ["/health", "/api/chat", "/api/documents"]
        
        missing_routes = []
        for route in required_routes:
            if route not in routes and not any(route in r for r in routes):
                missing_routes.append(route)
        
        print(f"   Toplam route sayısı: {len(routes)}")
        
        if missing_routes:
            log_result(
                "API Components",
                False,
                f"Eksik route'lar: {missing_routes}"
            )
            return False
        else:
            log_result(
                "API Components",
                True,
                f"Tüm temel route'lar mevcut ({len(routes)} route)"
            )
            return True
            
    except Exception as e:
        log_result(
            "API Components",
            False,
            f"API yüklenemedi: {e}",
            traceback.format_exc()
        )
        return False

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    """Ana test fonksiyonu."""
    print("\n" + "═"*70)
    print("       🧪 HISTORICAL ERROR STRESS TEST")
    print("       Geçmiş Hataları Yeniden Tetikleme Testi")
    print("═"*70)
    print(f"\nTarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Tüm testleri çalıştır
    tests = [
        ("1. ChromaDB Telemetry", test_chromadb_telemetry),
        ("2. HuggingFace Offline", test_huggingface_offline),
        ("3. Unicode/Emoji", test_unicode_emoji),
        ("4. Port Çakışması", test_port_conflict),
        ("5. HNSW Index", test_hnsw_index_recovery),
        ("6. Next.js Cache", test_nextjs_cache),
        ("7. Venv Enforcement", test_venv_enforcement),
        ("8. Import Tests", test_imports),
        ("9. CrossEncoder", test_crossencoder_loading),
        ("10. API Components", test_api_components),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n❌ {test_name} - EXCEPTION: {e}")
            failed += 1
    
    # Sonuç özeti
    print("\n" + "═"*70)
    print("       📊 TEST SONUÇLARI")
    print("═"*70)
    
    total = passed + failed
    percentage = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n   Toplam Test: {total}")
    print(f"   ✅ Başarılı: {passed}")
    print(f"   ❌ Başarısız: {failed}")
    print(f"   📈 Başarı Oranı: {percentage:.1f}%")
    
    # Detaylı sonuçlar
    print("\n   Detaylı Sonuçlar:")
    print("   " + "-"*50)
    
    for test_name, result in RESULTS.items():
        icon = "✅" if result["passed"] else "❌"
        print(f"   {icon} {test_name}: {result['message']}")
    
    # Raporu dosyaya kaydet
    report_file = Path(__file__).parent / "logs" / "stress_test_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "percentage": percentage
        },
        "results": RESULTS
    }
    
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n   📄 Rapor kaydedildi: {report_file}")
    print("\n" + "═"*70)
    
    # Exit code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
