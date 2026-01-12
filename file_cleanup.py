"""
DOSYA TEMİZLİK SCRIPTI - ChromaDB KULLANMAZ
Sadece duplicate dosyaları siler
"""

from pathlib import Path

UPLOAD_DIR = Path(r"c:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem\data\uploads")

print("\n" + "="*50)
print("  UPLOAD DUPLICATE TEMİZLİĞİ")
print("="*50)

if not UPLOAD_DIR.exists():
    print("Upload klasörü yok!")
    exit(1)

# Dosyaları grupla
files_by_name = {}
for f in UPLOAD_DIR.iterdir():
    if f.is_file():
        parts = f.name.split("_", 1)
        original_name = parts[1] if len(parts) > 1 else f.name
        if original_name not in files_by_name:
            files_by_name[original_name] = []
        files_by_name[original_name].append(f)

print(f"\n📁 Toplam dosya: {sum(len(v) for v in files_by_name.values())}")
print(f"📄 Benzersiz dosya: {len(files_by_name)}")

# Duplicate'leri sil
deleted = 0
for name, files in files_by_name.items():
    if len(files) > 1:
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        print(f"\n{name}: {len(files)} kopya")
        for f in files[1:]:
            f.unlink()
            deleted += 1
            print(f"  ❌ Silindi: {f.name[:40]}...")

print(f"\n✅ {deleted} duplicate silindi")

# Kalan dosyalar
remaining = list(UPLOAD_DIR.iterdir())
print(f"📁 Kalan dosya sayısı: {len(remaining)}")

print("\n📄 Mevcut dosyalar:")
for f in sorted(remaining, key=lambda x: x.name):
    parts = f.name.split("_", 1)
    name = parts[1] if len(parts) > 1 else f.name
    size_mb = f.stat().st_size / (1024*1024)
    print(f"  • {name} ({size_mb:.2f} MB)")

print("\n" + "="*50)
print("  TEMİZLİK TAMAMLANDI")
print("="*50 + "\n")
