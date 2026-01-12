"""
HIZLI BATCH REINDEX SCRIPTI
- API üzerinden dosyaları yeniden yükler
- BytesIO ile dosya gönderir (dosya lock sorunu önlenir)
"""

import requests
import time
import io
from pathlib import Path

UPLOAD_DIR = Path(r"c:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem\data\uploads")
API_URL = "http://localhost:8001"

print("\n" + "🚀"*20)
print("     BATCH REINDEX")
print("🚀"*20)

# Dosyaları listele
files = list(UPLOAD_DIR.iterdir())
print(f"\n📁 Toplam dosya: {len(files)}")

# Her dosyayı API üzerinden yükle
success_count = 0
fail_count = 0
skipped_count = 0

# Büyük dosyaları atla (15MB üstü) - embedding çok uzun sürer
MAX_SIZE_MB = 15

for i, file_path in enumerate(files, 1):
    if not file_path.is_file():
        continue
    
    # Orijinal dosya adını al
    parts = file_path.name.split("_", 1)
    original_name = parts[1] if len(parts) > 1 else file_path.name
    size_mb = file_path.stat().st_size / (1024*1024)
    
    print(f"\n[{i}/{len(files)}] {original_name} ({size_mb:.2f} MB)")
    
    # Büyük dosyaları atla
    if size_mb > MAX_SIZE_MB:
        print(f"   ⏭️ Atlandı (>{MAX_SIZE_MB}MB)")
        skipped_count += 1
        continue
    
    try:
        # Dosyayı oku ve BytesIO ile gönder (dosya lock sorununu önler)
        with open(file_path, 'rb') as f:
            content = f.read()
        
        files_data = {'file': (original_name, io.BytesIO(content), 'application/octet-stream')}
        response = requests.post(
            f"{API_URL}/api/documents/upload",
            files=files_data,
            timeout=180  # 3 dakika timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data.get('chunks_created', '?')} chunk")
            success_count += 1
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
            fail_count += 1
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️ Timeout - atlanıyor")
        fail_count += 1
    except Exception as e:
        print(f"   ❌ Hata: {str(e)[:80]}")
        fail_count += 1
    
    # API'ye nefes aldır
    time.sleep(1)

# Özet
print("\n" + "="*50)
print(f"✅ Başarılı: {success_count}")
print(f"❌ Başarısız: {fail_count}")
print(f"⏭️ Atlanan (büyük): {skipped_count}")

# Vector store durumunu kontrol et
try:
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        data = response.json()
        chunks = data.get('components', {}).get('document_count', 0)
        print(f"\n📊 Toplam chunk: {chunks}")
except:
    pass

print("\n" + "✅"*20)
print("     TAMAMLANDI")
print("✅"*20 + "\n")
