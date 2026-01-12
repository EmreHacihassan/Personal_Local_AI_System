"""
Upload Cleanup & Reindex Script
- Duplicate dosyaları temizle (en yenisini tut)
- Eksik dosyaları yeniden index'le
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from core.vector_store import vector_store
from core.config import settings
from rag.document_loader import document_loader
from rag.chunker import document_chunker
import os


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def cleanup_duplicate_uploads():
    """Duplicate dosyaları temizle - en yenisini tut"""
    print_section("DUPLICATE DOSYALARI TEMİZLE")
    
    upload_dir = settings.DATA_DIR / "uploads"
    if not upload_dir.exists():
        print("Upload klasörü yok")
        return
    
    # Dosyaları orijinal isme göre grupla
    files_by_name = {}
    for f in upload_dir.iterdir():
        if f.is_file():
            parts = f.name.split("_", 1)
            if len(parts) > 1:
                original_name = parts[1]
                if original_name not in files_by_name:
                    files_by_name[original_name] = []
                files_by_name[original_name].append(f)
    
    # Her dosya için sadece en yenisini tut
    deleted_count = 0
    for original_name, files in files_by_name.items():
        if len(files) > 1:
            # En yeni dosyayı bul
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            newest = files[0]
            
            print(f"\n📄 {original_name}: {len(files)} kopya var")
            print(f"   En yeni tutuldu: {newest.name}")
            
            # Eskileri sil
            for old_file in files[1:]:
                print(f"   ❌ Silindi: {old_file.name}")
                old_file.unlink()
                deleted_count += 1
    
    print(f"\n✅ Toplam {deleted_count} duplicate dosya silindi")
    return files_by_name


def get_indexed_files():
    """Vector store'da hangi dosyalar var?"""
    all_data = vector_store.collection.get(include=['metadatas'])
    
    indexed = set()
    for meta in all_data['metadatas']:
        if meta:
            filename = meta.get('original_filename') or meta.get('filename', '')
            # UUID prefix'i kaldır
            if '_' in filename and len(filename.split('_')[0]) == 36:
                filename = filename.split('_', 1)[1]
            if filename:
                indexed.add(filename)
    
    return indexed


def reindex_missing_files():
    """Eksik dosyaları yeniden index'le"""
    print_section("EKSİK DOSYALARI YENDEN INDEX'LE")
    
    upload_dir = settings.DATA_DIR / "uploads"
    if not upload_dir.exists():
        print("Upload klasörü yok")
        return
    
    # Mevcut indexed dosyaları al
    indexed_files = get_indexed_files()
    print(f"\n📊 Vector store'da {len(indexed_files)} dosya var")
    
    # Upload klasöründeki dosyaları kontrol et
    missing_files = []
    for f in upload_dir.iterdir():
        if f.is_file():
            parts = f.name.split("_", 1)
            if len(parts) > 1:
                original_name = parts[1]
                if original_name not in indexed_files:
                    missing_files.append(f)
    
    print(f"🔍 Index'lenmemiş dosya sayısı: {len(missing_files)}")
    
    if not missing_files:
        print("✅ Tüm dosyalar zaten index'lenmiş")
        return
    
    # Eksik dosyaları index'le
    for file_path in missing_files:
        parts = file_path.name.split("_", 1)
        document_id = parts[0]
        original_name = parts[1] if len(parts) > 1 else file_path.name
        
        print(f"\n📄 Index'leniyor: {original_name}")
        
        try:
            # Dökümanı yükle
            documents = document_loader.load_file(str(file_path))
            
            if not documents:
                print(f"   ⚠️ Boş döküman, atlanıyor")
                continue
            
            # Chunk'la
            chunks = document_chunker.chunk_documents(documents)
            
            if not chunks:
                from rag.chunker import Chunk
                chunks = [Chunk(content=doc.content, metadata=doc.metadata) for doc in documents]
            
            # Vector store'a ekle
            chunk_texts = [c.content for c in chunks]
            chunk_metadatas = [
                {**c.metadata, "document_id": document_id, "original_filename": original_name}
                for c in chunks
            ]
            
            vector_store.add_documents(
                documents=chunk_texts,
                metadatas=chunk_metadatas,
            )
            
            print(f"   ✅ {len(chunks)} chunk eklendi")
            
        except Exception as e:
            print(f"   ❌ Hata: {e}")
    
    # Sonuç
    new_count = vector_store.count()
    print(f"\n✅ Yeniden index'leme tamamlandı")
    print(f"   Yeni toplam chunk: {new_count}")


def show_final_status():
    """Son durumu göster"""
    print_section("SON DURUM")
    
    upload_dir = settings.DATA_DIR / "uploads"
    
    # Upload klasörü
    upload_files = list(upload_dir.iterdir()) if upload_dir.exists() else []
    print(f"\n📁 Upload klasöründe {len(upload_files)} dosya")
    
    # Vector store
    chunk_count = vector_store.count()
    indexed_files = get_indexed_files()
    print(f"📊 Vector store'da {chunk_count} chunk, {len(indexed_files)} benzersiz kaynak")
    
    print("\n📄 Index'lenmiş dosyalar:")
    for filename in sorted(indexed_files):
        print(f"   • {filename}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("    UPLOAD CLEANUP & REINDEX TOOL")
    print("="*60)
    
    cleanup_duplicate_uploads()
    reindex_missing_files()
    show_final_status()
    
    print("\n" + "="*60)
    print("    İŞLEM TAMAMLANDI")
    print("="*60 + "\n")
