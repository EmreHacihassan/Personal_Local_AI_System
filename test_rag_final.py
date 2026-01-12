"""RAG Test Script"""
import sys
sys.path.insert(0, '.')

from api.main import search_knowledge_base

print('='*50)
print('RAG TEST')
print('='*50)

tests = [
    'PowerPoint slayt',
    'MIS105',
    'Excel formül',
    'AVERAGE fonksiyonu',
    'İlyada',
]

for query in tests:
    print(f'\n🔍 Sorgu: "{query}"')
    knowledge, refs, source_map = search_knowledge_base(query, top_k=3)
    
    if source_map:
        print(f'   ✅ {len(source_map)} kaynak bulundu:')
        for name, info in source_map.items():
            print(f'      [{info["letter"]}] {info["filename"]}')
    else:
        print('   ❌ Sonuç yok')

print('\n' + '='*50)
print('TEST TAMAMLANDI')
print('='*50)
