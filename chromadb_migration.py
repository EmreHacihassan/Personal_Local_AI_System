#!/usr/bin/env python3
"""
ChromaDB Data Migration Tool
============================

Eski ChromaDB backup'larından veriyi yeni formata taşır.

Bu script:
1. Eski SQLite'dan dökümanları okur
2. Yeni ChromaDB'ye ekler
3. Embedding'leri korur (mümkünse)
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Source backup with data
SOURCE_BACKUP = DATA_DIR / "chroma_db_backup_20260118_131827"
SOURCE_DB = SOURCE_BACKUP / "chroma.sqlite3"

# =============================================================================
# DATA EXTRACTION
# =============================================================================

def extract_data_from_old_backup(db_path: Path) -> Dict[str, Any]:
    """Eski backup'tan veriyi çıkar (ChromaDB v0.4-1.0 format)."""
    
    import struct
    
    result = {
        "documents": [],
        "embeddings": [],
        "metadatas": [],
        "ids": [],
        "stats": {
            "total_embeddings": 0,
            "total_with_docs": 0,
            "total_metadata": 0,
        }
    }
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return result
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found tables: {len(tables)}")
        
        # =====================================================================
        # STRATEGY: Use embedding_fulltext_search_content for documents
        #           Use embeddings_queue for vectors
        #           Use embedding_metadata for metadata
        # =====================================================================
        
        # 1. Get documents from fulltext search content table
        doc_map = {}  # id -> document
        if 'embedding_fulltext_search_content' in tables:
            cursor.execute("SELECT id, c0 FROM embedding_fulltext_search_content")
            for row in cursor.fetchall():
                doc_id = row[0]
                content = row[1]
                if content:
                    doc_map[doc_id] = content
            print(f"📄 Found {len(doc_map)} documents in fulltext search")
        
        # 2. Get embeddings from queue (these have the actual vectors)
        embedding_map = {}  # id -> (embedding, doc_id_str)
        if 'embeddings_queue' in tables:
            cursor.execute("SELECT seq_id, id, vector, metadata FROM embeddings_queue")
            for row in cursor.fetchall():
                seq_id = row[0]
                uuid_id = row[1]
                vector_blob = row[2]
                metadata_str = row[3]
                
                # Parse vector (float32 binary)
                if vector_blob:
                    try:
                        num_floats = len(vector_blob) // 4
                        embedding = list(struct.unpack(f'{num_floats}f', vector_blob))
                    except:
                        embedding = None
                else:
                    embedding = None
                
                # Parse metadata
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except:
                    metadata = {}
                
                embedding_map[seq_id] = {
                    "id": uuid_id,
                    "embedding": embedding,
                    "metadata": metadata
                }
            print(f"🔢 Found {len(embedding_map)} embeddings in queue")
        
        # 3. Get additional metadata from embedding_metadata
        metadata_by_seq = {}  # seq_id -> {key: value}
        if 'embedding_metadata' in tables:
            cursor.execute("""
                SELECT id, key, string_value, int_value, float_value
                FROM embedding_metadata
            """)
            for row in cursor.fetchall():
                seq_id = row[0]
                key = row[1]
                value = row[2] or row[3] or row[4]
                
                if seq_id not in metadata_by_seq:
                    metadata_by_seq[seq_id] = {}
                
                if key and value is not None:
                    metadata_by_seq[seq_id][key] = value
            
            result["stats"]["total_metadata"] = len(metadata_by_seq)
            print(f"📝 Found metadata for {len(metadata_by_seq)} items")
        
        # 4. Combine everything
        # Match by sequential id (1, 2, 3...) which corresponds in all tables
        for seq_id in sorted(doc_map.keys()):
            document = doc_map.get(seq_id, "")
            emb_data = embedding_map.get(seq_id, {})
            
            embedding = emb_data.get("embedding")
            uuid_id = emb_data.get("id", f"doc_{seq_id}")
            base_metadata = emb_data.get("metadata", {})
            
            # Merge additional metadata
            extra_metadata = metadata_by_seq.get(seq_id, {})
            full_metadata = {**base_metadata, **extra_metadata}
            
            # Add migration marker
            full_metadata["_migrated_from"] = "chroma_db_backup_20260118_131827"
            full_metadata["_original_seq_id"] = seq_id
            
            result["ids"].append(uuid_id)
            result["documents"].append(document)
            result["embeddings"].append(embedding)
            result["metadatas"].append(full_metadata)
            
            if document:
                result["stats"]["total_with_docs"] += 1
        
        result["stats"]["total_embeddings"] = len(result["ids"])
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error extracting data: {e}")
        import traceback
        traceback.print_exc()
    
    return result

# =============================================================================
# DATA IMPORT
# =============================================================================

def import_to_new_chromadb(data: Dict[str, Any]) -> bool:
    """Veriyi yeni ChromaDB'ye aktar."""
    
    if not data["documents"]:
        print("⚠️ No documents to import")
        return False
    
    try:
        # Import the embedding manager for re-embedding if needed
        from core.embedding import embedding_manager
        from core.vector_store import vector_store
        
        # Ensure initialized
        vector_store._ensure_initialized()
        
        print(f"\n📥 Importing {len(data['documents'])} documents...")
        
        # Reserved keys that ChromaDB doesn't allow
        RESERVED_KEYS = {'chroma:document', 'chroma:embedding', 'chroma:id'}
        
        # Filter out empty documents and clean metadata
        valid_docs = []
        valid_metadatas = []
        valid_ids = []
        valid_embeddings = []
        
        for i, doc in enumerate(data["documents"]):
            if doc and len(doc.strip()) > 10:  # At least some content
                valid_docs.append(doc)
                
                # Clean metadata - remove reserved keys
                raw_metadata = data["metadatas"][i] if data["metadatas"] else {}
                cleaned_metadata = {}
                for key, value in raw_metadata.items():
                    if key not in RESERVED_KEYS and not key.startswith('chroma:'):
                        # Ensure value is a supported type
                        if isinstance(value, (str, int, float, bool)):
                            cleaned_metadata[key] = value
                        elif value is None:
                            pass  # Skip None values
                        else:
                            # Convert to string
                            cleaned_metadata[key] = str(value)
                
                valid_metadatas.append(cleaned_metadata)
                valid_ids.append(data["ids"][i] if data["ids"] else f"migrated_{i}")
                valid_embeddings.append(data["embeddings"][i] if data["embeddings"] else None)
        
        print(f"📊 Valid documents: {len(valid_docs)}")
        
        if not valid_docs:
            print("⚠️ No valid documents after filtering")
            return False
        
        # Check if we have embeddings
        has_embeddings = any(e is not None for e in valid_embeddings)
        
        if has_embeddings:
            print("✅ Using existing embeddings")
            # Use existing embeddings where available
            embeddings_to_use = []
            docs_to_reembed = []
            docs_to_reembed_idx = []
            
            for i, emb in enumerate(valid_embeddings):
                if emb is not None and len(emb) > 0:
                    embeddings_to_use.append(emb)
                else:
                    docs_to_reembed.append(valid_docs[i])
                    docs_to_reembed_idx.append(i)
            
            # Re-embed documents without embeddings
            if docs_to_reembed:
                print(f"🔄 Re-embedding {len(docs_to_reembed)} documents...")
                new_embeddings = embedding_manager.embed_texts(docs_to_reembed)
                
                for j, idx in enumerate(docs_to_reembed_idx):
                    embeddings_to_use.insert(idx, new_embeddings[j])
        else:
            print("🔄 Re-embedding all documents...")
            embeddings_to_use = embedding_manager.embed_texts(valid_docs)
        
        # Add to ChromaDB
        vector_store._manager.add_documents(
            documents=valid_docs,
            embeddings=embeddings_to_use,
            metadatas=valid_metadatas,
            ids=valid_ids,
        )
        
        # Verify
        count = vector_store.count()
        print(f"\n✅ Import complete! Total documents: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

# =============================================================================
# MAIN
# =============================================================================

def main():
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         ChromaDB Data Migration Tool v1.0                          ║")
    print("║         Eski backup'tan veri kurtarma                              ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # 1. Check source backup
    print("=" * 60)
    print("1️⃣  KAYNAK BACKUP KONTROLÜ")
    print("=" * 60)
    
    if not SOURCE_DB.exists():
        print(f"❌ Source backup not found: {SOURCE_DB}")
        return
    
    print(f"✅ Source: {SOURCE_BACKUP.name}")
    print(f"   Size: {SOURCE_DB.stat().st_size / 1024:.2f} KB")
    
    # 2. Extract data
    print()
    print("=" * 60)
    print("2️⃣  VERİ ÇIKARMA")
    print("=" * 60)
    
    data = extract_data_from_old_backup(SOURCE_DB)
    
    print(f"\n📊 Extracted:")
    print(f"   - Total embeddings: {data['stats']['total_embeddings']}")
    print(f"   - With documents: {data['stats']['total_with_docs']}")
    print(f"   - Metadata entries: {data['stats']['total_metadata']}")
    
    if data['documents']:
        # Show sample
        print(f"\n📄 Sample document (first 200 chars):")
        sample = data['documents'][0][:200] if data['documents'][0] else "(empty)"
        print(f"   {sample}...")
    
    # 3. Confirm migration
    print()
    print("=" * 60)
    print("3️⃣  ONAY")
    print("=" * 60)
    
    if not data['documents']:
        print("❌ No documents to migrate!")
        return
    
    print(f"📦 {len(data['documents'])} döküman taşınacak.")
    confirm = input("Devam edilsin mi? (evet/hayır): ").strip().lower()
    
    if confirm != "evet":
        print("İptal edildi.")
        return
    
    # 4. Import
    print()
    print("=" * 60)
    print("4️⃣  IMPORT")
    print("=" * 60)
    
    success = import_to_new_chromadb(data)
    
    if success:
        print()
        print("🎉 Migration tamamlandı!")
    else:
        print()
        print("❌ Migration başarısız.")

if __name__ == "__main__":
    main()
