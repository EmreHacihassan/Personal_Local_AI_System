"""
Vector Store Cleanup Script - Duplicate chunk'ları temizle
"""

import sys
sys.path.insert(0, '.')

from core.vector_store import vector_store

print("="*60)
print("  VECTOR STORE DUPLICATE TEMİZLİĞİ")
print("="*60)

# Mevcut durumu göster
total_before = vector_store.count()
print(f"\n📊 Temizlik öncesi toplam chunk: {total_before}")

# Tüm verileri al
all_data = vector_store.collection.get(include=['documents', 'metadatas'])

# Duplicate'leri tespit et
seen_hashes = {}
duplicates_to_remove = []

for i, doc in enumerate(all_data['documents']):
    if not doc:
        continue
    
    # İlk 200 karakter hash'i al
    content_hash = hash(doc[:200].strip().lower())
    
    if content_hash in seen_hashes:
        # Bu bir duplicate, kaldırılacaklar listesine ekle
        duplicates_to_remove.append(all_data['ids'][i])
    else:
        seen_hashes[content_hash] = all_data['ids'][i]

print(f"\n🔍 Tespit edilen duplicate: {len(duplicates_to_remove)}")

if duplicates_to_remove:
    print(f"\n🗑️ Duplicate'ler siliniyor...")
    
    # Batch halinde sil (ChromaDB'de tek seferde çok fazla silme sorun olabilir)
    batch_size = 100
    for i in range(0, len(duplicates_to_remove), batch_size):
        batch = duplicates_to_remove[i:i+batch_size]
        vector_store.collection.delete(ids=batch)
        print(f"   Silinen: {len(batch)} chunk")
    
    # Yeni durumu göster
    total_after = vector_store.count()
    print(f"\n✅ Temizlik sonrası toplam chunk: {total_after}")
    print(f"   Toplam silinen: {total_before - total_after}")
else:
    print("\n✅ Duplicate bulunamadı, temizlik gerekmiyor.")

print("\n" + "="*60)
print("  TEMİZLİK TAMAMLANDI")
print("="*60 + "\n")
