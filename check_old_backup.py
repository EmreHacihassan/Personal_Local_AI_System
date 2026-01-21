#!/usr/bin/env python3
"""Check old backup data"""

import sqlite3
from pathlib import Path

old_db = Path(r'c:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem\data\chroma_db_backup_old\chroma.sqlite3')

if old_db.exists():
    print(f"Checking: {old_db}")
    print(f"Size: {old_db.stat().st_size / 1024:.2f} KB")
    print()
    
    conn = sqlite3.connect(str(old_db))
    cursor = conn.cursor()
    
    # Integrity check
    cursor.execute('PRAGMA quick_check')
    integrity = cursor.fetchone()[0]
    print(f'Integrity: {integrity}')
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'Total Tables: {len(tables)}')
    print()
    
    # Check important tables
    important_tables = ['embeddings', 'embedding_metadata', 'collections', 'segments']
    for table in important_tables:
        if table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                print(f'  {table}: {count} rows')
            except Exception as e:
                print(f'  {table}: Error - {e}')
    
    conn.close()
    print()
    print("Analysis complete.")
else:
    print("Old backup not found!")
