# Sistem Stabilite Kılavuzu

Bu belge, AgenticManagingSystem projesindeki stabilite iyileştirmelerini ve sorun giderme yöntemlerini açıklar.

## 🚀 Hızlı Başlangıç

```bash
# Projeyi başlat (otomatik port temizleme dahil)
python run.py

# Sadece API (frontend olmadan)
python run.py --api-only

# Tarayıcı açmadan
python run.py --no-browser
```

> **Not:** run.py zaten portları otomatik olarak kontrol eder ve dolu olan portları temizler. `--clean` flag'i sadece çok nadir durumlarda (zombie process'ler vs.) gerekebilir.

## 📊 Servis Durumları

| Servis | Port | Kontrol Endpoint |
|--------|------|------------------|
| API Backend | 8001 | http://localhost:8001/health |
| Next.js Frontend | 3000 | http://localhost:3000 |
| Ollama | 11434 | http://localhost:11434/api/tags |
| ChromaDB | Embedded | API üzerinden |

## 🔧 Son Yapılan İyileştirmeler

### 1. run.py Monitor İyileştirmeleri

**Sorun:** Next.js sürekli yeniden başlatılıyordu (restart loop)

**Çözüm:**
- 120 saniyelik başlangıç grace period eklendi
- Restart cooldown (60 saniye) eklendi - çok sık restart yapılmıyor
- Process.poll() + port availability çift kontrol
- Windows CMD alt process'leri için ekstra kontrol

### 2. Servis Kontrol API'leri

Yeni endpoint'ler eklendi:

```bash
# Tüm servislerin durumu
GET /api/services/status

# Ollama başlat
POST /api/services/ollama/start

# ChromaDB yeniden bağlan
POST /api/services/chromadb/start

# ChromaDB sıfırla (DİKKAT: tüm verileri siler!)
POST /api/services/chromadb/reset

# Backend bilgisi
POST /api/services/backend/restart

# Next.js durumu
POST /api/services/nextjs/start
```

### 3. Frontend Servis Başlatma Butonları

Sidebar'daki System panelinde:
- **API Offline** → Info butonu (restart talimatları)
- **Ollama Offline** → Play butonu (otomatik başlatma dener)
- **ChromaDB Offline** → Reconnect butonu (bağlantı yenileme)

## 🐛 Sık Karşılaşılan Sorunlar

### Next.js Başlatma Sorunu

**Belirti:** "Next.js durdu, yeniden başlatılıyor..." mesajı sürekli görünüyor

**Çözüm:**
1. Tüm servisleri durdurun (Ctrl+C)
2. Normal başlatma yeterli olmalı: `python run.py`
3. Eğer hala sorun varsa zorla port temizliği:
   ```powershell
   taskkill /F /IM node.exe
   python run.py
   ```

### Ollama Bağlantı Sorunu

**Belirti:** "LLM yanıt vermiyor" hatası

**Çözümler:**
1. Sidebar'daki Play butonuna tıklayın
2. Veya terminal'de: `ollama serve`
3. Model yükleyin: `ollama pull llama3.2:3b`

### ChromaDB Bozulması

**Belirti:** "HNSW Index corruption" veya NumPy hataları

**Çözümler:**
1. Sidebar'dan Reconnect butonunu deneyin
2. Veya veritabanını sıfırlayın:
   - `/api/services/chromadb/reset` endpoint'ini çağırın
   - Ya da `data/chroma_db` klasörünü silin

⚠️ **Uyarı:** ChromaDB sıfırlamak tüm vektör verilerini siler!

## 📋 Gereksinimler

### Python Sürümü
- **Zorunlu:** Python 3.11.x
- **Test edildi:** Python 3.11.9

### Kritik Bağımlılıklar

```plaintext
chromadb>=0.4.22,<0.5.0  # 0.5.x ile uyumsuzluk var
numpy<2.0                 # NumPy 2.0 ile ChromaDB çakışıyor
```

### Node.js
- **Minimum:** Node.js 18+
- **Önerilen:** Node.js 20+

## 🧪 Test Komutları

```bash
# Tüm API endpoint'lerini test et
python comprehensive_test_suite.py

# Sadece API testleri
python test_all_endpoints.py

# Belirli testler
pytest tests/test_basic.py -v
```

## 📁 Önemli Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `run.py` | Ana başlatıcı script |
| `api/main.py` | FastAPI backend |
| `frontend-next/` | Next.js frontend |
| `requirements.txt` | Python bağımlılıkları |
| `CHROMADB_ISSUES.md` | ChromaDB sorunları detayı |

## 🔄 Otomatik Yeniden Başlatma

run.py aşağıdaki durumlarda servisleri yeniden başlatır:

1. Port boşalırsa (servis çökmüşse)
2. Process öldüyse (poll() is not None)

**Korumalar:**
- 120 saniye startup grace period
- 60 saniye restart cooldown
- Çift kontrol (port + process)

## 📞 Destek

Sorunlar için:
1. `logs/` klasöründeki log dosyalarını inceleyin
2. `/health` endpoint'ini kontrol edin
3. Sidebar'daki System panelini genişletin

---
*Son güncelleme: 2025*
