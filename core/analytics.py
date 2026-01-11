"""
Enterprise AI Assistant - Analytics Module
Kullanım analitikleri ve istatistikler

Endüstri standardı analytics implementasyonu.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import sqlite3

from core.config import settings


@dataclass
class AnalyticsEvent:
    """Analitik event."""
    event_type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class AnalyticsManager:
    """Analitik yönetim sınıfı."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Analytics manager başlat."""
        self.db_path = db_path or settings.DATA_DIR / "analytics.db"
        self._init_db()
    
    def _init_db(self) -> None:
        """Veritabanını başlat."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON events(timestamp)
            """)
            conn.commit()
    
    def track(
        self,
        event_type: str,
        data: Dict[str, Any] = None,
        user_id: str = None,
        session_id: str = None
    ) -> None:
        """
        Event kaydet.
        
        Args:
            event_type: Event tipi (chat, search, upload, etc.)
            data: Event verisi
            user_id: Kullanıcı ID
            session_id: Session ID
        """
        event = AnalyticsEvent(
            event_type=event_type,
            data=data or {},
            user_id=user_id,
            session_id=session_id,
        )
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO events (event_type, timestamp, user_id, session_id, data)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.event_type,
                    event.timestamp,
                    event.user_id,
                    event.session_id,
                    json.dumps(event.data, ensure_ascii=False),
                )
            )
            conn.commit()
    
    def track_chat(
        self,
        query: str,
        response_length: int,
        duration_ms: float,
        agent: str = None,
        session_id: str = None
    ) -> None:
        """Chat event'i kaydet."""
        self.track(
            event_type="chat",
            data={
                "query_length": len(query),
                "response_length": response_length,
                "duration_ms": duration_ms,
                "agent": agent,
            },
            session_id=session_id,
        )
    
    def track_search(
        self,
        query: str,
        results_count: int,
        duration_ms: float
    ) -> None:
        """Search event'i kaydet."""
        self.track(
            event_type="search",
            data={
                "query": query[:100],
                "results_count": results_count,
                "duration_ms": duration_ms,
            },
        )
    
    def track_document_upload(
        self,
        filename: str,
        file_size: int,
        chunks_created: int
    ) -> None:
        """Döküman yükleme event'i kaydet."""
        self.track(
            event_type="document_upload",
            data={
                "filename": filename,
                "file_size": file_size,
                "chunks_created": chunks_created,
            },
        )
    
    def track_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict = None
    ) -> None:
        """Hata event'i kaydet."""
        self.track(
            event_type="error",
            data={
                "error_type": error_type,
                "error_message": error_message[:500],
                "context": context or {},
            },
        )
    
    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        İstatistikleri al.
        
        Args:
            days: Kaç günlük veri
            
        Returns:
            İstatistik dict'i
        """
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            # Total events by type
            cursor = conn.execute(
                """
                SELECT event_type, COUNT(*) as count
                FROM events
                WHERE timestamp >= ?
                GROUP BY event_type
                """,
                (since,)
            )
            events_by_type = dict(cursor.fetchall())
            
            # Daily counts
            cursor = conn.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM events
                WHERE timestamp >= ?
                GROUP BY DATE(timestamp)
                ORDER BY date
                """,
                (since,)
            )
            daily_counts = dict(cursor.fetchall())
            
            # Average response time for chats
            cursor = conn.execute(
                """
                SELECT AVG(json_extract(data, '$.duration_ms')) as avg_duration
                FROM events
                WHERE event_type = 'chat' AND timestamp >= ?
                """,
                (since,)
            )
            avg_chat_duration = cursor.fetchone()[0] or 0
            
            # Popular queries (from search)
            cursor = conn.execute(
                """
                SELECT json_extract(data, '$.query') as query, COUNT(*) as count
                FROM events
                WHERE event_type = 'search' AND timestamp >= ?
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
                """,
                (since,)
            )
            popular_queries = cursor.fetchall()
            
            # Error count
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM events
                WHERE event_type = 'error' AND timestamp >= ?
                """,
                (since,)
            )
            error_count = cursor.fetchone()[0]
        
        return {
            "period_days": days,
            "events_by_type": events_by_type,
            "daily_counts": daily_counts,
            "total_chats": events_by_type.get("chat", 0),
            "total_searches": events_by_type.get("search", 0),
            "total_uploads": events_by_type.get("document_upload", 0),
            "avg_chat_duration_ms": round(avg_chat_duration, 2),
            "popular_queries": [{"query": q, "count": c} for q, c in popular_queries],
            "error_count": error_count,
        }
    
    def get_hourly_activity(self, days: int = 1) -> Dict[int, int]:
        """Saatlik aktivite dağılımı."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as count
                FROM events
                WHERE timestamp >= ?
                GROUP BY hour
                ORDER BY hour
                """,
                (since,)
            )
            return dict(cursor.fetchall())
    
    def get_agent_usage(self, days: int = 7) -> Dict[str, int]:
        """Agent kullanım istatistikleri."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                SELECT json_extract(data, '$.agent') as agent, COUNT(*) as count
                FROM events
                WHERE event_type = 'chat' AND timestamp >= ?
                AND json_extract(data, '$.agent') IS NOT NULL
                GROUP BY agent
                ORDER BY count DESC
                """,
                (since,)
            )
            return dict(cursor.fetchall())
    
    def export_events(
        self,
        event_type: str = None,
        since: str = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Event'leri dışa aktar."""
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
analytics = AnalyticsManager()
