#!/usr/bin/env python3
"""Deep analysis of old ChromaDB format"""

import sqlite3
from pathlib import Path

db_path = Path(r'c:\Users\LENOVO\Desktop\Aktif Projeler\AgenticManagingSystem\data\chroma_db_backup_20260118_131827\chroma.sqlite3')

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 70)
print("CHROMADB DEEP ANALYSIS")
print("=" * 70)

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    print(f"\n📋 Table: {table}")
    
    # Get columns
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [(col[1], col[2]) for col in cursor.fetchall()]
    print(f"   Columns: {columns}")
    
    # Count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"   Rows: {count}")
    
    # Sample data if not empty
    if count > 0 and count < 100:
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            # Truncate long values
            row_str = str(row)[:200]
            print(f"   Sample: {row_str}")

conn.close()
