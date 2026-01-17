"""
Hızlı dosya indexleme scripti - API gerektirmez
"""
import sys
sys.path.insert(0, '.')

from pathlib import Path
from rag.document_loader import document_loader, Document
from rag.chunker import document_chunker
from core.vector_store import vector_store

def index_all_files():
    uploads_dir = Path('data/uploads')
    
    if not uploads_dir.exists():
        print("❌ uploads klasörü bulunamadı")
        return
    
    files = [f for f in uploads_dir.iterdir() if f.is_file()]
    print(f"📁 Toplam dosya: {len(files)}")
    print(f"📊 Mevcut ChromaDB count: {vector_store.count()}")
    print()
    
    total_chunks = 0
    success = 0
    failed = 0
    
    for i, file_path in enumerate(files, 1):
        # Original filename'i çıkar (UUID prefix'i kaldır)
        parts = file_path.name.split("_", 1)
        original_name = parts[1] if len(parts) > 1 else file_path.name
        
        print(f"[{i}/{len(files)}] {original_name}")
        
        try:
            # Dosyayı yükle
            documents = document_loader.load_file(str(file_path))
            
            if not documents:
                print(f"   ⚠️ Boş döküman")
                continue
            
            # Chunk'lara ayır
            chunks = document_chunker.chunk_documents(documents)
            
            if not chunks:
                print(f"   ⚠️ Chunk oluşturulamadı")
                continue
            
            # Vector store'a ekle
            chunk_texts = [c.content for c in chunks]
            chunk_metadatas = [
                {**c.metadata, "original_filename": original_name}
                for c in chunks
            ]
            
            vector_store.add_documents(
                documents=chunk_texts,
                metadatas=chunk_metadatas,
            )
            
            total_chunks += len(chunks)
            success += 1
            print(f"   ✅ {len(chunks)} chunk eklendi")
            
        except Exception as e:
            failed += 1
            print(f"   ❌ Hata: {str(e)[:80]}")
    
    print()
    print("=" * 50)
    print(f"✅ Başarılı: {success}")
    print(f"❌ Başarısız: {failed}")
    print(f"📊 Toplam chunk: {total_chunks}")
    print(f"📊 ChromaDB toplam: {vector_store.count()}")

if __name__ == "__main__":
    index_all_files()
