"""
Enterprise AI Assistant - Export/Import Module
Veri dışa/içe aktarma

Endüstri standardı data portability.
"""

import json
import zipfile
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, BinaryIO
from dataclasses import asdict
import shutil

from core.config import settings
from core.session_manager import session_manager, Session


class ExportManager:
    """Dışa aktarma yöneticisi."""
    
    def __init__(self, export_dir: Optional[Path] = None):
        """Export manager başlat."""
        self.export_dir = export_dir or settings.DATA_DIR / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_sessions_json(
        self,
        session_ids: List[str] = None,
        output_path: Path = None
    ) -> Path:
        """
        Session'ları JSON olarak dışa aktar.
        
        Args:
            session_ids: Aktarılacak session ID'leri (None = tümü)
            output_path: Çıktı dosyası yolu
            
        Returns:
            Oluşturulan dosya yolu
        """
        if session_ids:
            sessions = [session_manager.get_session(sid) for sid in session_ids]
            sessions = [s for s in sessions if s]
        else:
            session_list = session_manager.list_sessions(limit=1000)
            sessions = [session_manager.get_session(s["id"]) for s in session_list]
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "version": "1.0",
            "session_count": len(sessions),
            "sessions": [s.to_dict() for s in sessions if s],
        }
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"sessions_export_{timestamp}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_sessions_csv(
        self,
        session_ids: List[str] = None,
        output_path: Path = None
    ) -> Path:
        """
        Session mesajlarını CSV olarak dışa aktar.
        
        Args:
            session_ids: Aktarılacak session ID'leri
            output_path: Çıktı dosyası yolu
            
        Returns:
            Oluşturulan dosya yolu
        """
        if session_ids:
            sessions = [session_manager.get_session(sid) for sid in session_ids]
            sessions = [s for s in sessions if s]
        else:
            session_list = session_manager.list_sessions(limit=1000)
            sessions = [session_manager.get_session(s["id"]) for s in session_list]
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"messages_export_{timestamp}.csv"
        
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "session_id", "session_title", "message_role",
                "message_content", "timestamp", "sources"
            ])
            
            for session in sessions:
                if session:
                    for msg in session.messages:
                        writer.writerow([
                            session.id,
                            session.title,
                            msg.role,
                            msg.content,
                            msg.timestamp,
                            ";".join(msg.sources) if msg.sources else "",
                        ])
        
        return output_path
    
    def export_full_backup(self, output_path: Path = None) -> Path:
        """
        Tam sistem yedeği al.
        
        Args:
            output_path: Çıktı ZIP dosyası
            
        Returns:
            Oluşturulan dosya yolu
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_path is None:
            output_path = self.export_dir / f"full_backup_{timestamp}.zip"
        
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Sessions
            sessions_dir = settings.DATA_DIR / "sessions"
            if sessions_dir.exists():
                for file in sessions_dir.glob("*.json"):
                    zf.write(file, f"sessions/{file.name}")
            
            # Uploads metadata (not actual files for size)
            uploads_dir = settings.DATA_DIR / "uploads"
            if uploads_dir.exists():
                upload_list = []
                for file in uploads_dir.iterdir():
                    if file.is_file():
                        upload_list.append({
                            "name": file.name,
                            "size": file.stat().st_size,
                            "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                        })
                zf.writestr(
                    "uploads/manifest.json",
                    json.dumps(upload_list, ensure_ascii=False, indent=2)
                )
            
            # Config (without sensitive data)
            config_export = {
                "CHUNK_SIZE": settings.CHUNK_SIZE,
                "CHUNK_OVERLAP": settings.CHUNK_OVERLAP,
                "TOP_K_RESULTS": settings.TOP_K_RESULTS,
                "OLLAMA_PRIMARY_MODEL": settings.OLLAMA_PRIMARY_MODEL,
            }
            zf.writestr(
                "config.json",
                json.dumps(config_export, ensure_ascii=False, indent=2)
            )
            
            # Backup metadata
            metadata = {
                "backup_date": datetime.now().isoformat(),
                "version": "1.0",
                "type": "full_backup",
            }
            zf.writestr(
                "metadata.json",
                json.dumps(metadata, ensure_ascii=False, indent=2)
            )
        
        return output_path
    
    def export_analytics(
        self,
        days: int = 30,
        output_path: Path = None
    ) -> Path:
        """
        Analytics verilerini dışa aktar.
        
        Args:
            days: Kaç günlük veri
            output_path: Çıktı dosyası
            
        Returns:
            Dosya yolu
        """
        from core.analytics import analytics
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.export_dir / f"analytics_export_{timestamp}.json"
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "period_days": days,
            "stats": analytics.get_stats(days),
            "hourly_activity": analytics.get_hourly_activity(days),
            "agent_usage": analytics.get_agent_usage(days),
            "events": analytics.export_events(since=None, limit=10000),
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_path


class ImportManager:
    """İçe aktarma yöneticisi."""
    
    def import_sessions_json(self, file_path: Path) -> Dict[str, Any]:
        """
        JSON'dan session'ları içe aktar.
        
        Args:
            file_path: JSON dosyası yolu
            
        Returns:
            İçe aktarma sonucu
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        imported = 0
        skipped = 0
        errors = []
        
        for session_data in data.get("sessions", []):
            try:
                session_id = session_data.get("id")
                
                # Check if session already exists
                existing = session_manager.get_session(session_id)
                if existing:
                    skipped += 1
                    continue
                
                # Create session
                session = Session.from_dict(session_data)
                session_manager._cache[session.id] = session
                session_manager._save_session(session)
                imported += 1
                
            except Exception as e:
                errors.append(f"Session import error: {str(e)}")
        
        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
            "total": len(data.get("sessions", [])),
        }
    
    def import_from_backup(self, zip_path: Path) -> Dict[str, Any]:
        """
        Yedekten geri yükle.
        
        Args:
            zip_path: ZIP dosyası yolu
            
        Returns:
            Geri yükleme sonucu
        """
        result = {
            "sessions_imported": 0,
            "errors": [],
        }
        
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Extract sessions
            for name in zf.namelist():
                if name.startswith("sessions/") and name.endswith(".json"):
                    try:
                        content = zf.read(name).decode("utf-8")
                        session_data = json.loads(content)
                        
                        session = Session.from_dict(session_data)
                        session_manager._cache[session.id] = session
                        session_manager._save_session(session)
                        result["sessions_imported"] += 1
                        
                    except Exception as e:
                        result["errors"].append(f"Error importing {name}: {str(e)}")
        
        return result


# Singleton instances
export_manager = ExportManager()
import_manager = ImportManager()
