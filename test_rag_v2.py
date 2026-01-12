"""
RAG Debug Script V2 - Geliştirilmiş RAG sistemini test et
Enterprise-grade diagnostic tool
"""

import sys
import os

# Proje root'unu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.vector_store import vector_store
from core.config import settings
from pathlib import Path


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def analyze_vector_store():
    """Vector store içeriğini analiz et"""
    print_section("VECTOR STORE ANALİZİ")
    
    # Toplam chunk sayısı
    total_count = vector_store.count()
    print(f"\n📊 Toplam chunk sayısı: {total_count}")
    
    if total_count == 0:
        print("❌ VECTöR STORE BOŞ! Döküman yüklenmemiş.")
        return
    
    # Tüm dökümanları al
    all_data = vector_store.collection.get(include=['documents', 'metadatas'])
    
    # Kaynakları grupla
    sources = {}
    for i, meta in enumerate(all_data['metadatas']):
        if meta:
            # original_filename veya filename kullan
            filename = meta.get('original_filename') or meta.get('filename', 'unknown')
            # UUID prefix'i kaldır
            if '_' in filename and len(filename.split('_')[0]) == 36:
                filename = filename.split('_', 1)[1]
            
            if filename not in sources:
                sources[filename] = {'count': 0, 'pages': set(), 'sample': None}
            sources[filename]['count'] += 1
            
            page = meta.get('page') or meta.get('page_number')
            if page:
                sources[filename]['pages'].add(page)
            
            if sources[filename]['sample'] is None and all_data['documents']:
                sources[filename]['sample'] = all_data['documents'][i][:200]
    
    # Özet yazdır
    print(f"\n📁 Benzersiz kaynak sayısı: {len(sources)}")
    print("\n📄 KAYNAKLAR VE CHUNK SAYILARI:")
    print("-" * 50)
    
    for filename, info in sorted(sources.items(), key=lambda x: -x[1]['count']):
        pages = sorted(info['pages']) if info['pages'] else []
        page_str = f"Sayfalar: {min(pages) if pages else '?'}-{max(pages) if pages else '?'}" if pages else "Sayfa yok"
        print(f"  • {filename}")
        print(f"    Chunks: {info['count']} | {page_str}")
        if info['sample']:
            sample = info['sample'].replace('\n', ' ')[:100]
            print(f"    Örnek: {sample}...")
        print()


def test_search(query: str, top_k: int = 5):
    """Arama testi yap"""
    print_section(f'ARAMA TESTİ: "{query}"')
    
    try:
        results = vector_store.search_with_scores(
            query=query,
            n_results=top_k,
            score_threshold=0.0
        )
        
        if not results:
            print("❌ Sonuç bulunamadı!")
            return
        
        print(f"\n✅ {len(results)} sonuç bulundu:\n")
        
        for i, r in enumerate(results, 1):
            meta = r.get('metadata', {})
            filename = meta.get('original_filename') or meta.get('filename', 'Bilinmeyen')
            # UUID prefix'i kaldır
            if '_' in filename and len(filename.split('_')[0]) == 36:
                filename = filename.split('_', 1)[1]
            
            page = meta.get('page') or meta.get('page_number', '-')
            score = r.get('score', 0)
            content = r.get('document', '')[:200].replace('\n', ' ')
            
            print(f"  {i}. [{score:.4f}] {filename} (s.{page})")
            print(f"     {content}...")
            print()
            
    except Exception as e:
        print(f"❌ Arama hatası: {e}")
        import traceback
        traceback.print_exc()


def test_improved_search():
    """Geliştirilmiş hybrid search'ü test et"""
    print_section("GELİŞTİRİLMİŞ RAG TESTİ")
    
    try:
        # api/main.py'deki search_knowledge_base fonksiyonunu import et
        from api.main import search_knowledge_base, get_uploaded_document_list
        
        # Yüklenen döküman listesi
        docs = get_uploaded_document_list()
        print(f"\n📁 Yüklenen döküman sayısı: {len(docs)}")
        for doc in docs[:10]:
            print(f"  • {doc['name']} ({doc['type']}, {doc['size_kb']:.1f} KB)")
        
        # Test aramaları
        test_queries = [
            "PowerPoint slayt",
            "Excel formül",
            "MIS105",
            "fonksiyon",
        ]
        
        for query in test_queries:
            print(f"\n🔍 Arama: '{query}'")
            knowledge, refs, source_map = search_knowledge_base(query, top_k=3)
            
            if knowledge:
                print(f"   ✅ {len(source_map)} kaynak bulundu")
                for name, info in source_map.items():
                    print(f"      [{info['letter']}] {info['filename']}")
            else:
                print("   ❌ Sonuç yok")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()


def check_uploads_folder():
    """Uploads klasörünü kontrol et"""
    print_section("UPLOADS KLASÖRÜ KONTROLÜ")
    
    upload_dir = settings.DATA_DIR / "uploads"
    
    if not upload_dir.exists():
        print(f"❌ Upload klasörü yok: {upload_dir}")
        return
    
    files = list(upload_dir.iterdir())
    print(f"\n📁 Upload klasörü: {upload_dir}")
    print(f"📄 Toplam dosya: {len(files)}")
    
    # Dosya türlerini say
    types = {}
    for f in files:
        ext = f.suffix.lower()
        types[ext] = types.get(ext, 0) + 1
    
    print("\n📊 Dosya türleri:")
    for ext, count in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  • {ext or 'uzantısız'}: {count}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("    RAG DEBUG & DIAGNOSTIC TOOL V2")
    print("="*60)
    
    check_uploads_folder()
    analyze_vector_store()
    test_search("MIS105 PowerPoint")
    test_search("Excel formül")
    test_improved_search()
    
    print("\n" + "="*60)
    print("    DEBUG TAMAMLANDI")
    print("="*60 + "\n")
