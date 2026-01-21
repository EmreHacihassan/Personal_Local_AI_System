#!/usr/bin/env python3
"""Check backup with data"""

import sqlite3
from pathlib import Path

backups = [
    Path(r'c:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem\data\chroma_db_backup_20260118_131827\chroma.sqlite3'),
    Path(r'c:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem\data\chroma_db_backup\chroma.sqlite3'),
]

for db_path in backups:
    if not db_path.exists():
        print(f"Not found: {db_path.parent.name}")
        continue
    
    print(f"\n{'='*60}")
    print(f"Backup: {db_path.parent.name}")
    print(f"Size: {db_path.stat().st_size / 1024:.2f} KB")
    print('='*60)
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check for data
        data_tables = ['embeddings', 'embedding_metadata', 'collections', 'segments', 'embedding_fulltext_search']
        
        for table in data_tables:
            if table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f'  ✅ {table}: {count} rows')
                    else:
                        print(f'  ⚪ {table}: empty')
                except Exception as e:
                    print(f'  ❌ {table}: {e}')
        
        # Check for actual document content
        if 'embeddings' in tables:
            try:
                cursor.execute('SELECT COUNT(*) FROM embeddings WHERE document IS NOT NULL')
                doc_count = cursor.fetchone()[0]
                print(f'\n  📄 Documents with content: {doc_count}')
            except:
                pass
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*60)
print("Summary: Looking for backups with actual document data...")
