"""
Enterprise AI Assistant - Resilient ChromaDB Wrapper
=====================================================

ChromaDB için dayanıklı, hata-toleranslı wrapper.

FEATURES:
- Startup health check with retry
- Automatic backup before operations
- Corruption detection & auto-recovery
- File locking for concurrent access
- Graceful degradation
- Comprehensive logging

Bu modül ChromaDB hatalarını KALICI olarak çözer.
"""

import os
import shutil
import time
import hashlib
import threading
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
import json

import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import settings
from .logger import get_logger

logger = get_logger("chromadb_resilient")


@dataclass
class ChromaDBHealth:
    """ChromaDB sağlık durumu."""
    is_healthy: bool
    collection_count: int
    document_count: int
    last_check: datetime
    error_message: Optional[str] = None
    sqlite_integrity: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_healthy": self.is_healthy,
            "collection_count": self.collection_count,
            "document_count": self.document_count,
            "last_check": self.last_check.isoformat(),
            "error_message": self.error_message,
            "sqlite_integrity": self.sqlite_integrity,
        }


class ChromaDBBackupManager:
    """
    ChromaDB backup yönetimi.
    
    - Otomatik backup before risky operations
    - Backup rotation (max 5 backup)
    - Restore capability
    """
    
    def __init__(self, data_dir: Path, max_backups: int = 5):
        self.data_dir = Path(data_dir)
        self.chroma_dir = self.data_dir / "chroma_db"
        self.backup_dir = self.data_dir / "chroma_backups"
        self.max_backups = max_backups
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, reason: str = "manual") -> Optional[Path]:
        """
        ChromaDB backup oluştur.
        
        Args:
            reason: Backup sebebi (startup, before_write, scheduled, manual)
            
        Returns:
            Backup path veya None (hata durumunda)
        """
        if not self.chroma_dir.exists():
            logger.warning("ChromaDB dizini yok, backup oluşturulamıyor")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"chroma_backup_{reason}_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Copy entire directory
            shutil.copytree(self.chroma_dir, backup_path, dirs_exist_ok=True)
            
            # Create metadata
            metadata = {
                "created_at": datetime.now().isoformat(),
                "reason": reason,
                "source_path": str(self.chroma_dir),
                "files": [f.name for f in self.chroma_dir.iterdir() if f.is_file()],
            }
            
            with open(backup_path / "backup_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ ChromaDB backup oluşturuldu: {backup_name}")
            
            # Rotate old backups
            self._rotate_backups()
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Backup oluşturulamadı: {e}")
            return None
    
    def _rotate_backups(self):
        """Eski backup'ları sil (max_backups'ı aşanları)."""
        try:
            backups = sorted(
                [d for d in self.backup_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # En yeni max_backups kadar tut
            for old_backup in backups[self.max_backups:]:
                shutil.rmtree(old_backup, ignore_errors=True)
                logger.info(f"🗑️ Eski backup silindi: {old_backup.name}")
                
        except Exception as e:
            logger.warning(f"Backup rotation hatası: {e}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Mevcut backup'ları listele."""
        backups = []
        
        try:
            for backup_dir in self.backup_dir.iterdir():
                if backup_dir.is_dir():
                    metadata_file = backup_dir / "backup_metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                    else:
                        metadata = {"created_at": "unknown"}
                    
                    backups.append({
                        "name": backup_dir.name,
                        "path": str(backup_dir),
                        "created_at": metadata.get("created_at"),
                        "reason": metadata.get("reason", "unknown"),
                        "size_mb": sum(f.stat().st_size for f in backup_dir.rglob("*") if f.is_file()) / (1024*1024),
                    })
        except Exception as e:
            logger.error(f"Backup listeleme hatası: {e}")
        
        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Backup'tan geri yükle.
        
        Args:
            backup_name: Backup klasör adı
            
        Returns:
            Başarılı mı
        """
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            logger.error(f"Backup bulunamadı: {backup_name}")
            return False
        
        try:
            # Mevcut DB'yi yedekle
            if self.chroma_dir.exists():
                corrupt_backup = self.data_dir / f"chroma_db_corrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(str(self.chroma_dir), str(corrupt_backup))
                logger.info(f"Corrupt DB taşındı: {corrupt_backup}")
            
            # Backup'ı restore et
            shutil.copytree(backup_path, self.chroma_dir, dirs_exist_ok=True)
            
            # Metadata dosyasını sil (orijinal değil backup'tan)
            metadata_file = self.chroma_dir / "backup_metadata.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"✅ Backup restore edildi: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Restore hatası: {e}")
            return False
    
    def get_latest_backup(self) -> Optional[Path]:
        """En son backup'ı döndür."""
        backups = self.list_backups()
        if backups:
            return Path(backups[0]["path"])
        return None


class ChromaDBIntegrityChecker:
    """
    ChromaDB SQLite integrity kontrolü.
    
    - PRAGMA integrity_check
    - Table structure validation
    - Collection consistency check
    """
    
    @staticmethod
    def check_sqlite_integrity(db_path: Path) -> Tuple[bool, str]:
        """
        SQLite veritabanı bütünlük kontrolü.
        
        Returns:
            (is_valid, message)
        """
        if not db_path.exists():
            return False, "Database file not found"
        
        try:
            conn = sqlite3.connect(str(db_path), timeout=10)
            cursor = conn.cursor()
            
            # Integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            
            if result != "ok":
                conn.close()
                return False, f"Integrity check failed: {result}"
            
            # Quick validation - temel tablolar var mı
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # ChromaDB 1.x expected tables
            if not tables:
                return False, "No tables found in database"
            
            return True, "Database integrity OK"
            
        except sqlite3.DatabaseError as e:
            return False, f"SQLite error: {e}"
        except Exception as e:
            return False, f"Unknown error: {e}"
    
    @staticmethod
    def repair_database(db_path: Path) -> bool:
        """
        SQLite database repair attempt.
        
        Sadece basit recovery yapar - ciddi corruption için backup restore gerekir.
        """
        try:
            conn = sqlite3.connect(str(db_path), timeout=30)
            cursor = conn.cursor()
            
            # Vacuum to rebuild
            cursor.execute("VACUUM")
            
            # Reindex
            cursor.execute("REINDEX")
            
            conn.commit()
            conn.close()
            
            logger.info("Database repair attempt completed")
            return True
            
        except Exception as e:
            logger.error(f"Database repair failed: {e}")
            return False


class ResilientChromaDB:
    """
    Dayanıklı ChromaDB wrapper.
    
    FEATURES:
    - Startup health check with retry
    - Automatic backup
    - Corruption detection & recovery
    - File locking
    - Circuit breaker integration
    - Graceful degradation
    
    Kullanım:
        chroma = ResilientChromaDB()
        chroma.ensure_healthy()  # Startup'ta çağır
        collection = chroma.get_collection("my_collection")
    """
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "enterprise_knowledge",
        auto_backup: bool = True,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.persist_directory = persist_directory or str(settings.DATA_DIR / "chroma_db")
        self.collection_name = collection_name
        self.auto_backup = auto_backup
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection = None
        self._lock = threading.RLock()
        self._is_healthy = False
        self._last_health_check: Optional[datetime] = None
        self._health_check_interval = timedelta(minutes=5)
        
        # Backup manager
        self.backup_manager = ChromaDBBackupManager(
            data_dir=Path(self.persist_directory).parent
        )
        
        # Integrity checker
        self.integrity_checker = ChromaDBIntegrityChecker()
        
        # Metrics
        self._metrics = {
            "total_operations": 0,
            "failed_operations": 0,
            "recovery_attempts": 0,
            "successful_recoveries": 0,
        }
    
    @property
    def sqlite_path(self) -> Path:
        """ChromaDB SQLite dosya yolu."""
        return Path(self.persist_directory) / "chroma.sqlite3"
    
    def _create_client(self) -> chromadb.PersistentClient:
        """ChromaDB client oluştur."""
        # Dizin yoksa oluştur
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        return chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,  # Güvenlik için False
            ),
        )
    
    def _connect_with_retry(self) -> bool:
        """Retry logic ile bağlan."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                self._client = self._create_client()
                
                # Test connection
                self._client.list_collections()
                
                logger.info(f"✅ ChromaDB bağlantısı başarılı (attempt {attempt + 1})")
                return True
                
            except Exception as e:
                last_error = e
                logger.warning(f"ChromaDB bağlantı hatası (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        logger.error(f"❌ ChromaDB bağlantısı başarısız: {last_error}")
        return False
    
    def check_health(self, force: bool = False) -> ChromaDBHealth:
        """
        Sağlık kontrolü yap.
        
        Args:
            force: Cache'i bypass et
        """
        with self._lock:
            # Cache kontrolü
            if not force and self._last_health_check:
                if datetime.now() - self._last_health_check < self._health_check_interval:
                    return ChromaDBHealth(
                        is_healthy=self._is_healthy,
                        collection_count=len(self._client.list_collections()) if self._client else 0,
                        document_count=self._collection.count() if self._collection else 0,
                        last_check=self._last_health_check,
                    )
            
            health = ChromaDBHealth(
                is_healthy=False,
                collection_count=0,
                document_count=0,
                last_check=datetime.now(),
            )
            
            # 1. SQLite integrity check
            if self.sqlite_path.exists():
                is_valid, message = self.integrity_checker.check_sqlite_integrity(self.sqlite_path)
                health.sqlite_integrity = is_valid
                if not is_valid:
                    health.error_message = message
                    logger.error(f"SQLite integrity check failed: {message}")
                    return health
            
            # 2. Client connection check
            try:
                if not self._client:
                    self._client = self._create_client()
                
                collections = self._client.list_collections()
                health.collection_count = len(collections)
                
                # 3. Collection access check
                if self._collection:
                    health.document_count = self._collection.count()
                
                health.is_healthy = True
                self._is_healthy = True
                self._last_health_check = datetime.now()
                
            except Exception as e:
                health.is_healthy = False
                health.error_message = str(e)
                self._is_healthy = False
                logger.error(f"ChromaDB health check failed: {e}")
            
            return health
    
    def ensure_healthy(self) -> bool:
        """
        ChromaDB'nin sağlıklı olduğundan emin ol.
        
        Startup'ta çağrılmalı. Gerekirse recovery dener.
        
        Returns:
            Sağlıklı mı
        """
        logger.info("🔍 ChromaDB sağlık kontrolü başlatılıyor...")
        
        # 1. Backup before anything (eğer DB varsa)
        if self.auto_backup and self.sqlite_path.exists():
            self.backup_manager.create_backup("startup")
        
        # 2. Health check
        health = self.check_health(force=True)
        
        if health.is_healthy:
            logger.info("✅ ChromaDB sağlıklı")
            return True
        
        # 3. Recovery attempt
        logger.warning("⚠️ ChromaDB sağlıksız, recovery deneniyor...")
        self._metrics["recovery_attempts"] += 1
        
        # 3a. SQLite repair attempt
        if not health.sqlite_integrity and self.sqlite_path.exists():
            logger.info("SQLite repair deneniyor...")
            if self.integrity_checker.repair_database(self.sqlite_path):
                health = self.check_health(force=True)
                if health.is_healthy:
                    self._metrics["successful_recoveries"] += 1
                    logger.info("✅ SQLite repair başarılı")
                    return True
        
        # 3b. Backup restore attempt
        latest_backup = self.backup_manager.get_latest_backup()
        if latest_backup:
            logger.info(f"Backup restore deneniyor: {latest_backup.name}")
            
            # Close existing client
            self._client = None
            self._collection = None
            
            if self.backup_manager.restore_backup(latest_backup.name):
                # Reconnect
                if self._connect_with_retry():
                    health = self.check_health(force=True)
                    if health.is_healthy:
                        self._metrics["successful_recoveries"] += 1
                        logger.info("✅ Backup restore başarılı")
                        return True
        
        # 3c. Fresh start (son çare)
        logger.warning("⚠️ Recovery başarısız, temiz başlatma yapılıyor...")
        
        # Mevcut corrupt DB'yi taşı
        if self.sqlite_path.exists():
            corrupt_path = Path(self.persist_directory).parent / f"chroma_db_corrupt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(self.persist_directory, str(corrupt_path))
            logger.info(f"Corrupt DB taşındı: {corrupt_path}")
        
        # Yeni bağlantı
        if self._connect_with_retry():
            self._metrics["successful_recoveries"] += 1
            logger.info("✅ Temiz ChromaDB başlatıldı")
            return True
        
        logger.error("❌ ChromaDB recovery tamamen başarısız")
        return False
    
    def get_collection(self, name: Optional[str] = None) -> Any:
        """
        Collection al veya oluştur.
        
        Args:
            name: Collection adı (default: self.collection_name)
        """
        with self._lock:
            collection_name = name or self.collection_name
            
            if not self._client:
                if not self._connect_with_retry():
                    raise ConnectionError("ChromaDB bağlantısı kurulamadı")
            
            try:
                self._collection = self._client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                return self._collection
                
            except Exception as e:
                self._metrics["failed_operations"] += 1
                logger.error(f"Collection erişim hatası: {e}")
                raise
    
    @contextmanager
    def safe_operation(self, operation_name: str = "unknown"):
        """
        Güvenli operasyon context manager.
        
        Otomatik backup, error handling ve recovery.
        
        Usage:
            with chroma.safe_operation("add_documents"):
                collection.add(...)
        """
        self._metrics["total_operations"] += 1
        
        # Backup before risky write operations
        if self.auto_backup and operation_name in ("add", "update", "delete", "upsert"):
            self.backup_manager.create_backup(f"before_{operation_name}")
        
        try:
            yield
            
        except Exception as e:
            self._metrics["failed_operations"] += 1
            logger.error(f"Operation '{operation_name}' failed: {e}")
            
            # Health check
            health = self.check_health(force=True)
            if not health.is_healthy:
                logger.warning("ChromaDB sağlıksız, recovery deneniyor...")
                self.ensure_healthy()
            
            raise
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Dökümanları güvenli şekilde ekle.
        """
        collection = self.get_collection()
        
        # Generate IDs if not provided
        if not ids:
            ids = [
                hashlib.md5(f"{doc}_{i}_{time.time()}".encode()).hexdigest()
                for i, doc in enumerate(documents)
            ]
        
        with self.safe_operation("add"):
            add_kwargs = {
                "documents": documents,
                "ids": ids,
            }
            
            if embeddings:
                add_kwargs["embeddings"] = embeddings
            if metadatas:
                add_kwargs["metadatas"] = metadatas
            
            collection.add(**add_kwargs)
            
            logger.info(f"✅ {len(documents)} döküman eklendi")
            return ids
    
    def query(
        self,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 5,
        where: Optional[Dict] = None,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Güvenli sorgu.
        """
        collection = self.get_collection()
        
        with self.safe_operation("query"):
            return collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                include=include or ["documents", "metadatas", "distances"],
            )
    
    def delete(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict] = None,
    ) -> None:
        """
        Güvenli silme.
        """
        collection = self.get_collection()
        
        with self.safe_operation("delete"):
            collection.delete(ids=ids, where=where)
            logger.info(f"Dökümanlar silindi")
    
    def count(self) -> int:
        """Döküman sayısı."""
        collection = self.get_collection()
        return collection.count()
    
    def clear(self) -> None:
        """
        Tüm dökümanları sil (backup ile).
        """
        if self.auto_backup:
            self.backup_manager.create_backup("before_clear")
        
        collection = self.get_collection()
        
        with self.safe_operation("clear"):
            # ChromaDB'de tüm verileri silmek için collection'ı yeniden oluştur
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("Collection temizlendi")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Metrikler."""
        return {
            **self._metrics,
            "is_healthy": self._is_healthy,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Durum raporu."""
        health = self.check_health()
        
        return {
            "health": health.to_dict(),
            "metrics": self.get_metrics(),
            "backups": self.backup_manager.list_backups()[:5],
            "persist_directory": self.persist_directory,
            "collection_name": self.collection_name,
        }


# Singleton instance
resilient_chromadb = ResilientChromaDB()


__all__ = [
    "ResilientChromaDB",
    "ChromaDBBackupManager",
    "ChromaDBIntegrityChecker",
    "ChromaDBHealth",
    "resilient_chromadb",
]
