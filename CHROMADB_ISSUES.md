<!-- 
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  HATIRLATMA: Bu projede ZATEN bir venv var! Yenisini oluşturmana gerek yok!  ║
║  📁  Konum: .\venv\Scripts\pip.exe                                               ║
║  💡  Kurulum: .\venv\Scripts\pip.exe install chromadb==0.4.24                    ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
-->

# ChromaDB Sorunları ve Çözümleri

## 🔴 Karşılaştığımız Kritik Sorunlar

### 1. HNSW Index Corruption (Rust Panic)

**Hata Mesajı:**
```
pyo3_runtime.PanicException: range start index 10 out of range for slice of length 9
```

**Neden Oluşuyor:**
- ChromaDB, vektörleri HNSW (Hierarchical Navigable Small World) algoritmasıyla indexliyor
- Bu index **Rust** ile yazılmış `hnswlib-rs` kütüphanesini kullanıyor
- Index dosyası disk'e binary format'ta kaydediliyor

**Tetikleyiciler:**
| Durum | Açıklama |
|-------|----------|
| Ani Kapanma | CTRL+C, crash, güç kesintisi sırasında index yarım kalıyor |
| Concurrent Write | Birden fazla process aynı anda yazınca index bozuluyor |
| Disk I/O Hatası | SSD/HDD yazma hatası index'i corrupt ediyor |
| Version Mismatch | Farklı ChromaDB versiyonları farklı index formatı kullanıyor |

**Çözüm:**
```powershell
# ChromaDB klasörünü tamamen sil
Remove-Item "data\chroma_db" -Recurse -Force
New-Item "data\chroma_db" -ItemType Directory
```

---

### 2. NumPy 2.0 Uyumsuzluğu

**Hata Mesajı:**
```
AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.
```

**Neden:**
- NumPy 2.0 (Haziran 2024) birçok deprecated type'ı kaldırdı
- ChromaDB 0.4.x dahili olarak `np.float_`, `np.int_` kullanıyor
- Bu type'lar NumPy 2.0'da mevcut değil

**Çözüm:**
```bash
pip install "numpy<2.0"
# veya
pip install numpy==1.26.4
```

**requirements.txt'e ekle:**
```
numpy<2.0  # CRITICAL: ChromaDB incompatible with NumPy 2.0+
```

---

### 3. ChromaDB Version Compatibility Matrix

| ChromaDB | NumPy | Python | SQLite | Durum |
|----------|-------|--------|--------|-------|
| **0.4.24** | **1.26.x** | **3.11** | 3.35+ | ✅ **ÖNERİLEN** |
| 0.4.22 | 1.26.x | 3.11 | 3.35+ | ✅ Stabil |
| 0.5.0+ | 1.26.x | 3.11+ | 3.35+ | ⚠️ API Breaking Changes |
| 0.4.x | 2.0.x | Any | Any | ❌ **KIRIK** |
| 0.3.x | Any | 3.9-3.11 | Any | ⚠️ Eski, güncellenmiyor |

---

### 4. `_type` Key Error (0.5.x)

**Hata Mesajı:**
```
KeyError: '_type'
```

**Neden:**
- ChromaDB 0.5.x collection metadata formatını değiştirdi
- 0.4.x'te oluşturulan collection'lar 0.5.x ile uyumsuz

**Çözüm:**
```bash
# Downgrade yap
pip install chromadb==0.4.24

# VEYA database'i sıfırla
rm -rf data/chroma_db
```

---

## 🟢 Önerilen Konfigürasyon

### requirements.txt
```
chromadb>=0.4.22,<0.5.0
numpy<2.0
sentence-transformers>=2.2.2
```

### Python Sürümü
```
Python 3.11.9 (ZORUNLU)
```

### Kurulum
```powershell
# 1. Python 3.11.9 kur
# 2. Virtual environment oluştur
python -m venv venv
.\venv\Scripts\activate

# 3. Paketleri kur
pip install -r requirements.txt

# 4. NumPy kontrolü
python -c "import numpy; print(numpy.__version__)"
# Çıktı: 1.26.4 olmalı

# 5. ChromaDB kontrolü
python -c "import chromadb; print(chromadb.__version__)"
# Çıktı: 0.4.24 olmalı
```

---

## 🔧 Koruyucu Önlemler (Projede Mevcut)

### 1. Graceful Shutdown
```python
# core/chromadb_manager.py
import atexit
atexit.register(self.shutdown)
```

### 2. Otomatik Backup
```python
# Her başlangıçta backup alınıyor
def _create_backup(self, prefix="backup"):
    ...
```

### 3. Connection Retry
```python
# 3 deneme ile bağlantı
for attempt in range(3):
    try:
        self._connect()
        break
    except Exception:
        time.sleep(1)
```

### 4. Duplicate Check
```python
# Content-based hash ile duplicate kontrolü
def add_documents(self, ..., skip_duplicates=True):
    ...
```

---

## 📊 Alternatif Vector Database'ler

Eğer ChromaDB sorunları devam ederse:

| Database | Avantaj | Dezavantaj |
|----------|---------|------------|
| **Qdrant** | Rust-native, stabil | Docker gerekli |
| **Milvus** | Enterprise-grade | Ağır kurulum |
| **Weaviate** | GraphQL API | Cloud-focused |
| **FAISS** | Facebook, çok hızlı | Persistence zor |
| **LanceDB** | Yeni, SQLite-like | Henüz olgunlaşmamış |

---

## 🆘 Acil Kurtarma Prosedürü

```powershell
# 1. Tüm Python process'lerini kapat
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. ChromaDB'yi sıfırla
Remove-Item "data\chroma_db" -Recurse -Force
New-Item "data\chroma_db" -ItemType Directory

# 3. NumPy'yi düzelt
.\venv\Scripts\pip.exe install "numpy<2.0" --force-reinstall

# 4. ChromaDB'yi düzelt
.\venv\Scripts\pip.exe install chromadb==0.4.24 --force-reinstall

# 5. Test et
.\venv\Scripts\python.exe -c "import chromadb; c = chromadb.Client(); print('OK')"
```

---

## 📝 Notlar

- **Bu dosyayı LLM'lere veya tanıdıklarınıza gösterin** - sorunun tam açıklaması burada
- ChromaDB aktif geliştirme altında, her minor version breaking change içerebilir
- Production için **0.4.24 + NumPy 1.26.4 + Python 3.11.9** kombinasyonu test edilmiş ve stabil

---

*Son Güncelleme: 2026-01-20*
