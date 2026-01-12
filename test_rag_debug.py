"""
RAG Debug Script - Veritabanı ve arama sistemini test et
"""
import sys
sys.path.insert(0, '.')

print("=== RAG DEBUG SCRIPT ===\n")

# 1. Vector Store Test
print("1. VECTOR STORE TEST")
print("-" * 40)
from core.vector_store import vector_store

count = vector_store.count()
print(f"Toplam chunk sayısı: {count}")

if count > 0:
    # Tüm metadataları al
    all_data = vector_store.collection.get(include=['metadatas', 'documents'])
    
    # Unique kaynakları bul
    sources = {}
    for i, meta in enumerate(all_data.get('metadatas', [])):
        if meta:
            source = meta.get('original_filename') or meta.get('filename') or meta.get('source', 'unknown')
            if source not in sources:
                sources[source] = []
            sources[source].append({
                'chunk_index': meta.get('chunk_index', i),
                'page': meta.get('page') or meta.get('page_number'),
                'doc_len': len(all_data['documents'][i]) if all_data['documents'] else 0
            })
    
    print(f"\nBenzersiz kaynak sayısı: {len(sources)}")
    print("\nKaynaklar ve chunk detayları:")
    for source, chunks in sorted(sources.items()):
        print(f"\n  📄 {source}")
        print(f"     Chunk sayısı: {len(chunks)}")
        pages = set(c['page'] for c in chunks if c['page'])
        if pages:
            print(f"     Sayfalar: {sorted(pages)}")
        avg_len = sum(c['doc_len'] for c in chunks) / len(chunks) if chunks else 0
        print(f"     Ortalama chunk uzunluğu: {avg_len:.0f} karakter")

    # İlk chunk örneği
    print("\n" + "=" * 50)
    print("İLK CHUNK ÖRNEĞİ:")
    print("=" * 50)
    print(f"Metadata: {all_data['metadatas'][0]}")
    print(f"\nİçerik (ilk 500 char):\n{all_data['documents'][0][:500]}...")

# 2. Arama Testi
print("\n\n2. ARAMA TESTİ")
print("-" * 40)

test_query = "PowerPoint slayt"
print(f"Test sorgusu: '{test_query}'")

results = vector_store.search_with_scores(
    query=test_query,
    n_results=5,
)

print(f"\nBulunan sonuç: {len(results)}")
for i, r in enumerate(results, 1):
    meta = r.get('metadata', {})
    source = meta.get('original_filename') or meta.get('filename') or meta.get('source', 'unknown')
    page = meta.get('page') or meta.get('page_number', 'N/A')
    score = r.get('score', 0)
    content_preview = r.get('document', '')[:150]
    
    print(f"\n--- Sonuç {i} ---")
    print(f"Kaynak: {source}")
    print(f"Sayfa: {page}")
    print(f"Skor: {score:.4f}")
    print(f"İçerik: {content_preview}...")

# 3. Advanced RAG Testi
print("\n\n3. ADVANCED RAG TESTİ")
print("-" * 40)

try:
    from rag.advanced_rag import advanced_rag, RAGStrategy
    
    results = advanced_rag.retrieve(
        query=test_query,
        strategy=RAGStrategy.NAIVE,
        top_k=3,
    )
    
    print(f"Advanced RAG sonuç sayısı: {len(results)}")
    for i, r in enumerate(results, 1):
        print(f"\n--- Advanced RAG Sonuç {i} ---")
        print(f"Kaynak: {r.source}")
        print(f"Skor: {r.score:.4f}")
        print(f"Metadata: {r.metadata}")
        print(f"İçerik: {r.content[:150]}...")
        
except Exception as e:
    print(f"Advanced RAG hatası: {e}")
    import traceback
    traceback.print_exc()

print("\n\n=== DEBUG TAMAMLANDI ===")
