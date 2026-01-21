#!/usr/bin/env python3
"""
ChromaDB Comprehensive Analysis & Repair Tool
=============================================

Bu script ChromaDB'nin tüm durumunu analiz eder ve sorunları çözer.

Özellikler:
- SQLite integrity check
- HNSW index validation
- Data consistency verification
- Version compatibility check
- Backup management
- Automatic repair
"""

import os
import sys
import json
import shutil
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
BACKUP_DIR = DATA_DIR / "chroma_backups"

# =============================================================================
# UTILITIES
# =============================================================================

def print_header(title: str):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title: str):
    print()
    print(f"── {title} ──")

def print_status(name: str, status: bool, detail: str = ""):
    icon = "✅" if status else "❌"
    print(f"  {icon} {name}: {detail}")

def print_warning(msg: str):
    print(f"  ⚠️  {msg}")

def print_info(msg: str):
    print(f"  ℹ️  {msg}")

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_dir_size(path: Path) -> int:
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
    except:
        pass
    return total

# =============================================================================
# CHROMADB VERSION CHECK
# =============================================================================

def check_chromadb_version() -> Dict[str, Any]:
    """ChromaDB sürüm uyumluluğunu kontrol et."""
    result = {
        "installed_version": None,
        "is_compatible": False,
        "notes": []
    }
    
    try:
        import chromadb
        version = chromadb.__version__
        result["installed_version"] = version
        
        major, minor, patch = map(int, version.split(".")[:3])
        
        # Version compatibility matrix
        if major == 0 and minor < 4:
            result["notes"].append("Very old version - upgrade recommended")
        elif major == 0 and minor >= 4 and minor < 5:
            result["notes"].append("Stable v0.4.x - good compatibility")
            result["is_compatible"] = True
        elif major == 1 and minor == 0:
            result["notes"].append("v1.0.x - new format, may need migration")
            result["is_compatible"] = True
        elif major == 1 and minor >= 1:
            result["notes"].append("v1.1+ uses Rust bindings - incompatible with old data")
            result["is_compatible"] = True
            result["notes"].append("⚠️ Data format changed from v0.x/v1.0")
        else:
            result["is_compatible"] = True
            
    except ImportError:
        result["notes"].append("ChromaDB not installed!")
    except Exception as e:
        result["notes"].append(f"Version check error: {e}")
    
    return result

# =============================================================================
# FILE SYSTEM ANALYSIS
# =============================================================================

def analyze_filesystem() -> Dict[str, Any]:
    """Dosya sistemini analiz et."""
    result = {
        "chroma_exists": CHROMA_DIR.exists(),
        "files": [],
        "total_size": 0,
        "sqlite_files": [],
        "parquet_files": [],
        "lock_files": [],
        "other_files": [],
    }
    
    if not CHROMA_DIR.exists():
        return result
    
    for f in CHROMA_DIR.rglob("*"):
        if f.is_file():
            file_info = {
                "name": f.name,
                "path": str(f.relative_to(CHROMA_DIR)),
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            result["files"].append(file_info)
            result["total_size"] += f.stat().st_size
            
            if f.suffix == ".sqlite3":
                result["sqlite_files"].append(file_info)
            elif f.suffix == ".parquet":
                result["parquet_files"].append(file_info)
            elif f.suffix == ".lock" or f.name.startswith("."):
                result["lock_files"].append(file_info)
            else:
                result["other_files"].append(file_info)
    
    return result

# =============================================================================
# SQLITE ANALYSIS
# =============================================================================

def analyze_sqlite(db_path: Path) -> Dict[str, Any]:
    """SQLite veritabanını analiz et."""
    result = {
        "exists": db_path.exists(),
        "integrity_ok": False,
        "tables": [],
        "journal_mode": None,
        "page_size": None,
        "page_count": None,
        "errors": []
    }
    
    if not db_path.exists():
        return result
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30)
        cursor = conn.cursor()
        
        # Integrity check
        cursor.execute("PRAGMA quick_check")
        integrity = cursor.fetchone()[0]
        result["integrity_ok"] = (integrity == "ok")
        if integrity != "ok":
            result["errors"].append(f"Integrity check: {integrity}")
        
        # Journal mode
        cursor.execute("PRAGMA journal_mode")
        result["journal_mode"] = cursor.fetchone()[0]
        
        # Page info
        cursor.execute("PRAGMA page_size")
        result["page_size"] = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_count")
        result["page_count"] = cursor.fetchone()[0]
        
        # Tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        result["tables"] = [row[0] for row in cursor.fetchall()]
        
        # Table row counts
        result["table_counts"] = {}
        for table in result["tables"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
                result["table_counts"][table] = cursor.fetchone()[0]
            except:
                result["table_counts"][table] = "error"
        
        conn.close()
        
    except sqlite3.DatabaseError as e:
        result["errors"].append(f"SQLite error: {e}")
    except Exception as e:
        result["errors"].append(f"Error: {e}")
    
    return result

# =============================================================================
# CHROMADB CONNECTION TEST
# =============================================================================

def test_chromadb_connection() -> Dict[str, Any]:
    """ChromaDB bağlantısını test et."""
    result = {
        "can_connect": False,
        "collections": [],
        "document_counts": {},
        "errors": []
    }
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False,
            )
        )
        
        result["can_connect"] = True
        
        # List collections
        collections = client.list_collections()
        for coll in collections:
            result["collections"].append(coll.name)
            try:
                result["document_counts"][coll.name] = coll.count()
            except Exception as e:
                result["document_counts"][coll.name] = f"error: {e}"
        
    except Exception as e:
        result["errors"].append(str(e))
        
        # Categorize error
        error_str = str(e).lower()
        if "range" in error_str and "index" in error_str:
            result["error_type"] = "HNSW_INDEX_CORRUPTION"
            result["error_description"] = "HNSW index dosyası bozuk - Rust binding hatası"
        elif "database is locked" in error_str:
            result["error_type"] = "DATABASE_LOCKED"
            result["error_description"] = "Başka bir process veritabanını kilitliyor"
        elif "no such table" in error_str:
            result["error_type"] = "SCHEMA_MISMATCH"
            result["error_description"] = "Tablo yapısı uyuşmuyor - sürüm farkı olabilir"
        else:
            result["error_type"] = "UNKNOWN"
            result["error_description"] = str(e)
    
    return result

# =============================================================================
# BACKUP ANALYSIS
# =============================================================================

def analyze_backups() -> Dict[str, Any]:
    """Backup'ları analiz et."""
    result = {
        "backup_dir_exists": BACKUP_DIR.exists(),
        "backups": [],
        "total_backup_size": 0
    }
    
    if not BACKUP_DIR.exists():
        return result
    
    for backup in sorted(BACKUP_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if backup.is_dir():
            size = get_dir_size(backup)
            result["backups"].append({
                "name": backup.name,
                "size": size,
                "size_formatted": format_size(size),
                "modified": datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
            })
            result["total_backup_size"] += size
    
    # Check old backup locations
    old_locations = [
        DATA_DIR / "chroma_db_backup",
        DATA_DIR / "chroma_db_backup_old",
    ]
    
    for loc in old_locations:
        if loc.exists():
            size = get_dir_size(loc)
            result["backups"].append({
                "name": f"[OLD] {loc.name}",
                "size": size,
                "size_formatted": format_size(size),
                "modified": datetime.fromtimestamp(loc.stat().st_mtime).isoformat(),
                "location": str(loc)
            })
    
    # Look for corrupt backups
    for item in DATA_DIR.iterdir():
        if item.is_dir() and "corrupt" in item.name.lower():
            size = get_dir_size(item)
            result["backups"].append({
                "name": f"[CORRUPT] {item.name}",
                "size": size,
                "size_formatted": format_size(size),
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                "location": str(item)
            })
    
    return result

# =============================================================================
# REPAIR FUNCTIONS
# =============================================================================

def repair_sqlite(db_path: Path) -> bool:
    """SQLite veritabanını onar."""
    if not db_path.exists():
        return True
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=60)
        cursor = conn.cursor()
        
        # Enable WAL mode for better durability
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Vacuum to rebuild
        cursor.execute("VACUUM")
        
        # Reindex
        cursor.execute("REINDEX")
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print_warning(f"SQLite repair failed: {e}")
        return False

def create_fresh_chromadb() -> bool:
    """Temiz ChromaDB oluştur."""
    try:
        # Backup existing if present
        if CHROMA_DIR.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = DATA_DIR / f"chroma_db_before_fresh_{timestamp}"
            shutil.move(str(CHROMA_DIR), str(backup_path))
            print_info(f"Old data backed up to: {backup_path.name}")
        
        # Create fresh directory
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize fresh ChromaDB
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False,
            )
        )
        
        # Create default collection
        client.get_or_create_collection(
            name="enterprise_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
        print_status("Fresh ChromaDB", True, "Created successfully")
        return True
        
    except Exception as e:
        print_warning(f"Fresh creation failed: {e}")
        return False

def restore_from_backup(backup_name: str) -> bool:
    """Backup'tan restore et."""
    backup_path = BACKUP_DIR / backup_name
    
    if not backup_path.exists():
        # Check old locations
        for loc in [DATA_DIR / backup_name, DATA_DIR / "chroma_db_backup", DATA_DIR / "chroma_db_backup_old"]:
            if loc.exists():
                backup_path = loc
                break
    
    if not backup_path.exists():
        print_warning(f"Backup not found: {backup_name}")
        return False
    
    try:
        # Backup current corrupt DB
        if CHROMA_DIR.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupt_path = DATA_DIR / f"chroma_corrupt_{timestamp}"
            shutil.move(str(CHROMA_DIR), str(corrupt_path))
            print_info(f"Corrupt DB moved to: {corrupt_path.name}")
        
        # Restore from backup
        shutil.copytree(backup_path, CHROMA_DIR)
        
        # Remove metadata file if present
        meta_file = CHROMA_DIR / "_backup_meta.json"
        if meta_file.exists():
            meta_file.unlink()
        
        print_status("Restore", True, f"Restored from {backup_path.name}")
        return True
        
    except Exception as e:
        print_warning(f"Restore failed: {e}")
        return False

# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def run_full_analysis() -> Dict[str, Any]:
    """Tam analiz yap."""
    print_header("🔍 CHROMADB KAPSAMLI ANALİZ")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "issues": [],
        "recommendations": []
    }
    
    # 1. Version Check
    print_section("ChromaDB Sürüm Kontrolü")
    version_info = check_chromadb_version()
    results["version"] = version_info
    
    if version_info["installed_version"]:
        print_status("Installed Version", True, version_info["installed_version"])
        for note in version_info["notes"]:
            print_info(note)
    else:
        print_status("ChromaDB", False, "Not installed!")
        results["issues"].append("ChromaDB not installed")
    
    # 2. Filesystem Analysis
    print_section("Dosya Sistemi Analizi")
    fs_info = analyze_filesystem()
    results["filesystem"] = fs_info
    
    if fs_info["chroma_exists"]:
        print_status("ChromaDB Directory", True, str(CHROMA_DIR))
        print_info(f"Total Size: {format_size(fs_info['total_size'])}")
        print_info(f"SQLite files: {len(fs_info['sqlite_files'])}")
        print_info(f"Parquet files: {len(fs_info['parquet_files'])}")
        print_info(f"Lock files: {len(fs_info['lock_files'])}")
        
        if fs_info['lock_files']:
            print_warning("Lock files found - may cause issues")
            for lf in fs_info['lock_files']:
                print_info(f"  - {lf['path']}")
    else:
        print_status("ChromaDB Directory", False, "Does not exist")
        results["recommendations"].append("Initialize ChromaDB with fresh database")
    
    # 3. SQLite Analysis
    print_section("SQLite Veritabanı Analizi")
    sqlite_path = CHROMA_DIR / "chroma.sqlite3"
    sqlite_info = analyze_sqlite(sqlite_path)
    results["sqlite"] = sqlite_info
    
    if sqlite_info["exists"]:
        print_status("SQLite File", True, str(sqlite_path.name))
        print_status("Integrity Check", sqlite_info["integrity_ok"], 
                     "OK" if sqlite_info["integrity_ok"] else "FAILED")
        print_info(f"Journal Mode: {sqlite_info['journal_mode']}")
        print_info(f"Tables: {', '.join(sqlite_info['tables'])}")
        
        if sqlite_info.get("table_counts"):
            for table, count in sqlite_info["table_counts"].items():
                print_info(f"  - {table}: {count} rows")
        
        if not sqlite_info["integrity_ok"]:
            results["issues"].append("SQLite integrity check failed")
            results["recommendations"].append("Run SQLite repair (VACUUM)")
    else:
        print_info("SQLite file not found (may be using different format)")
    
    # 4. Connection Test
    print_section("ChromaDB Bağlantı Testi")
    conn_info = test_chromadb_connection()
    results["connection"] = conn_info
    
    if conn_info["can_connect"]:
        print_status("Connection", True, "Successful")
        print_info(f"Collections: {len(conn_info['collections'])}")
        for coll in conn_info["collections"]:
            count = conn_info["document_counts"].get(coll, "?")
            print_info(f"  - {coll}: {count} documents")
    else:
        print_status("Connection", False, "FAILED")
        if conn_info.get("error_type"):
            print_warning(f"Error Type: {conn_info['error_type']}")
            print_warning(f"Description: {conn_info['error_description']}")
        
        results["issues"].append(f"Connection failed: {conn_info.get('error_type', 'unknown')}")
        
        # Recommendations based on error type
        error_type = conn_info.get("error_type", "")
        if error_type == "HNSW_INDEX_CORRUPTION":
            results["recommendations"].append("HNSW index bozuk - Backup'tan restore veya fresh start gerekli")
            results["recommendations"].append("ChromaDB sürümü (1.1+) eski veri formatıyla uyumsuz olabilir")
        elif error_type == "DATABASE_LOCKED":
            results["recommendations"].append("Diğer process'leri kapatın ve lock dosyalarını silin")
        elif error_type == "SCHEMA_MISMATCH":
            results["recommendations"].append("ChromaDB sürümü değişmiş - data migration gerekli")
    
    # 5. Backup Analysis
    print_section("Backup Analizi")
    backup_info = analyze_backups()
    results["backups"] = backup_info
    
    if backup_info["backups"]:
        print_info(f"Total Backups: {len(backup_info['backups'])}")
        print_info(f"Total Backup Size: {format_size(backup_info['total_backup_size'])}")
        for backup in backup_info["backups"][:5]:
            print_info(f"  - {backup['name']}: {backup['size_formatted']}")
    else:
        print_warning("No backups found!")
        results["recommendations"].append("Set up automatic backups")
    
    # 6. Final Assessment
    print_section("Sonuç Değerlendirmesi")
    
    if conn_info["can_connect"] and sqlite_info.get("integrity_ok", True):
        results["status"] = "healthy"
        print_status("Overall Status", True, "SAĞLIKLI")
        print_info("ChromaDB düzgün çalışıyor.")
    elif conn_info["can_connect"]:
        results["status"] = "degraded"
        print_status("Overall Status", False, "SORUNLU")
        print_warning("Bağlantı var ama bazı sorunlar mevcut.")
    else:
        results["status"] = "critical"
        print_status("Overall Status", False, "KRİTİK")
        print_warning("ChromaDB'ye bağlanılamıyor!")
    
    if results["recommendations"]:
        print()
        print("📋 ÖNERİLER:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"   {i}. {rec}")
    
    return results

def run_repair() -> bool:
    """Onarım işlemi yap."""
    print_header("🔧 CHROMADB ONARIM")
    
    # First, analyze
    analysis = run_full_analysis()
    
    if analysis["status"] == "healthy":
        print()
        print("✅ ChromaDB zaten sağlıklı, onarıma gerek yok.")
        return True
    
    print_section("Onarım Seçenekleri")
    print("1. SQLite Repair (VACUUM) - Küçük sorunları düzeltir")
    print("2. Backup'tan Restore - En son backup'ı geri yükler")
    print("3. Fresh Start - Tüm veriyi sil, temiz başla")
    print("0. İptal")
    print()
    
    choice = input("Seçiminiz (0-3): ").strip()
    
    if choice == "1":
        print_section("SQLite Repair")
        sqlite_path = CHROMA_DIR / "chroma.sqlite3"
        if repair_sqlite(sqlite_path):
            print_status("SQLite Repair", True, "Completed")
            # Test connection
            test = test_chromadb_connection()
            if test["can_connect"]:
                print_status("Connection Test", True, "Working!")
                return True
            else:
                print_status("Connection Test", False, "Still failing")
                print_info("Daha güçlü bir onarım gerekebilir.")
        return False
        
    elif choice == "2":
        print_section("Backup Restore")
        backup_info = analyze_backups()
        
        if not backup_info["backups"]:
            print_warning("Backup bulunamadı!")
            return False
        
        print("Mevcut backup'lar:")
        for i, backup in enumerate(backup_info["backups"], 1):
            print(f"  {i}. {backup['name']} ({backup['size_formatted']})")
        
        backup_choice = input("Backup seçin (numara): ").strip()
        try:
            idx = int(backup_choice) - 1
            backup_name = backup_info["backups"][idx]["name"]
            
            # Handle [OLD] and [CORRUPT] prefixes
            if backup_name.startswith("[OLD] "):
                backup_name = backup_name[6:]
            elif backup_name.startswith("[CORRUPT] "):
                print_warning("Corrupt backup seçtiniz, bu önerilmez!")
                backup_name = backup_name[10:]
            
            if restore_from_backup(backup_name):
                # Test connection
                test = test_chromadb_connection()
                if test["can_connect"]:
                    print_status("Connection Test", True, "Restored and working!")
                    return True
                else:
                    print_status("Connection Test", False, "Restore failed")
        except (ValueError, IndexError):
            print_warning("Geçersiz seçim")
        return False
        
    elif choice == "3":
        print_section("Fresh Start")
        confirm = input("⚠️  TÜM VERİ SİLİNECEK! Emin misiniz? (evet/hayır): ").strip().lower()
        
        if confirm == "evet":
            if create_fresh_chromadb():
                # Test connection
                test = test_chromadb_connection()
                if test["can_connect"]:
                    print_status("Fresh Start", True, "Success!")
                    return True
        else:
            print_info("İptal edildi.")
        return False
    
    else:
        print_info("İptal edildi.")
        return False

# =============================================================================
# CLI
# =============================================================================

def main():
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         ChromaDB Analysis & Repair Tool v1.0                       ║")
    print("║         Enterprise AI Assistant                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        if cmd == "analyze":
            results = run_full_analysis()
            
            # Save results
            report_path = BASE_DIR / "chromadb_analysis_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print()
            print(f"📄 Report saved to: {report_path}")
            
        elif cmd == "repair":
            run_repair()
            
        elif cmd == "fresh":
            confirm = input("⚠️  TÜM VERİ SİLİNECEK! Emin misiniz? (evet/hayır): ").strip().lower()
            if confirm == "evet":
                create_fresh_chromadb()
            
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python chromadb_analysis.py [analyze|repair|fresh]")
    else:
        # Interactive mode
        print("Komutlar:")
        print("  1. Analiz Yap")
        print("  2. Onarım")
        print("  3. Temiz Başlat (Fresh)")
        print("  0. Çıkış")
        print()
        
        choice = input("Seçiminiz: ").strip()
        
        if choice == "1":
            results = run_full_analysis()
            report_path = BASE_DIR / "chromadb_analysis_report.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print()
            print(f"📄 Report saved to: {report_path}")
        elif choice == "2":
            run_repair()
        elif choice == "3":
            confirm = input("⚠️  TÜM VERİ SİLİNECEK! Emin misiniz? (evet/hayır): ").strip().lower()
            if confirm == "evet":
                create_fresh_chromadb()
        else:
            print("Çıkış...")

if __name__ == "__main__":
    main()
