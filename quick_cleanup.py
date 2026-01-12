"""
HIZLI TEMİZLİK SCRIPTI
- Duplicate uploads'ları sil (sadece dosya sistemi)
- Vector store duplicate'lerini sil
- REINDEX YOK - hızlı çalışır
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from core.vector_store import vector_store
from core.config import settings


def cleanup_duplicate_uploads():
    """Upload klasöründeki duplicate dosyaları sil"""
    print("\n" + "="*50)
    print("UPLOAD DUPLICATE TEMİZLİĞİ")
    print("="*50)
    
    upload_dir = settings.DATA_DIR / "uploads"
    if not upload_dir.exists():
        print("Upload klasörü yok")
        return 0
    
    # Dosyaları orijinal isme göre grupla
    files_by_name = {}
    for f in upload_dir.iterdir():
        if f.is_file():
            parts = f.name.split("_", 1)
            if len(parts) > 1:
                original_name = parts[1]
            else:
                original_name = f.name
            
            if original_name not in files_by_name:
                files_by_name[original_name] = []
            files_by_name[original_name].append(f)
    
    deleted_count = 0
    for original_name, files in files_by_name.items():
        if len(files) > 1:
            # En yeni dosyayı tut
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            print(f"\n📄 {original_name}: {len(files)} kopya")
            
            for old_file in files[1:]:
                old_file.unlink()
                deleted_count += 1
                print(f"   ❌ Silindi")
    
    remaining = len(list(upload_dir.iterdir()))
    print(f"\n✅ {deleted_count} duplicate silindi, {remaining} dosya kaldı")
    return deleted_count


def cleanup_vector_duplicates():
    """Vector store'daki duplicate chunk'ları sil"""
    print("\n" + "="*50)
    print("VECTOR STORE DUPLICATE TEMİZLİĞİ")
    print("="*50)
    
    total_before = vector_store.count()
    print(f"Önceki toplam: {total_before}")
    
    all_data = vector_store.collection.get(include=['documents', 'metadatas'])
    
    seen_hashes = {}
    duplicates = []
    
    for i, doc in enumerate(all_data['documents']):
        if not doc:
            continue
        content_hash = hash(doc[:200].strip().lower())
        if content_hash in seen_hashes:
            duplicates.append(all_data['ids'][i])
        else:
            seen_hashes[content_hash] = all_data['ids'][i]
    
    if duplicates:
        # Batch sil
        for i in range(0, len(duplicates), 100):
            batch = duplicates[i:i+100]
            vector_store.collection.delete(ids=batch)
        print(f"❌ {len(duplicates)} duplicate silindi")
    
    total_after = vector_store.count()
    print(f"✅ Son toplam: {total_after}")
    return len(duplicates)


def show_status():
    """Mevcut durumu göster"""
    print("\n" + "="*50)
    print("MEVCUT DURUM")
    print("="*50)
    
    upload_dir = settings.DATA_DIR / "uploads"
    
    # Upload dosyaları
    if upload_dir.exists():
        files = list(upload_dir.iterdir())
        unique_names = set()
        for f in files:
            parts = f.name.split("_", 1)
            name = parts[1] if len(parts) > 1 else f.name
            unique_names.add(name)
        print(f"\n📁 Upload: {len(files)} dosya, {len(unique_names)} benzersiz")
    
    # Vector store
    count = vector_store.count()
    all_data = vector_store.collection.get(include=['metadatas'])
    sources = set()
    for meta in all_data['metadatas']:
        if meta:
            fn = meta.get('original_filename') or meta.get('filename', '')
            if '_' in fn and len(fn.split('_')[0]) == 36:
                fn = fn.split('_', 1)[1]
            if fn:
                sources.add(fn)
    
    print(f"📊 Vector Store: {count} chunk, {len(sources)} kaynak")
    print("\n📄 Kaynaklar:")
    for s in sorted(sources):
        print(f"   • {s}")


if __name__ == "__main__":
    print("\n" + "🚀"*20)
    print("     HIZLI TEMİZLİK")
    print("🚀"*20)
    
    cleanup_duplicate_uploads()
    cleanup_vector_duplicates()
    show_status()
    
    print("\n" + "✅"*20)
    print("     TAMAMLANDI")
    print("✅"*20 + "\n")
