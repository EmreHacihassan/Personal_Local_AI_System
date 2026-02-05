"""
Enterprise AI Assistant - Intelligent Model Router
====================================================

Human-in-the-Loop Model Routing with Feedback Learning System.

Bu modül, kullanıcı sorgularını analiz ederek en uygun modele yönlendirir:
- Küçük Model (4B): Basit sorgular, hızlı yanıtlar
- Büyük Model (8B): Kapsamlı sorgular, detaylı yanıtlar

ENTERPRISE FEATURES:
- AI-Powered Routing (4B model karar verir)
- Rule-Based Fast Path (bilinen pattern'lar için)
- Human Feedback Learning (kullanıcı tercihlerinden öğrenme)
- Semantic Similarity Learning (embedding tabanlı)
- Confidence Scoring (belirsiz durumlar için)
- A/B Comparison (model karşılaştırma)
- Real-time Metrics & Analytics

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    Model Router                              │
    ├─────────────────────────────────────────────────────────────┤
    │  1. Rule-Based Check (< 1ms)                                │
    │     └─> Exact/Pattern match → Instant decision              │
    │  2. AI Router (4B Model)                                    │
    │     └─> Semantic analysis → Classification                  │
    │  3. Feedback Learning                                       │
    │     └─> User corrections → Pattern extraction → DB store    │
    │  4. Similarity Search                                       │
    │     └─> Embedding comparison → Nearest neighbor decision    │
    └─────────────────────────────────────────────────────────────┘

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import threading
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

import ollama

from .config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class ModelSize(str, Enum):
    """Model boyut sınıflandırması."""
    SMALL = "small"   # 4B - Hızlı, basit sorgular
    LARGE = "large"   # 8B - Kapsamlı, detaylı sorgular


class RoutingDecision(str, Enum):
    """Routing kararı kaynağı."""
    RULE_BASED = "rule_based"       # Pattern/keyword match
    AI_ROUTER = "ai_router"         # 4B model kararı
    LEARNED = "learned"             # Feedback'ten öğrenilmiş
    SIMILARITY = "similarity"       # Embedding benzerliği
    DEFAULT = "default"             # Fallback


class FeedbackType(str, Enum):
    """Kullanıcı feedback tipi."""
    CORRECT = "correct"             # Doğru model kullanıldı
    DOWNGRADE = "downgrade"         # Büyük kullanıldı ama küçük yeterliydi
    UPGRADE = "upgrade"             # Küçük kullanıldı ama büyük lazımdı


class FeedbackStatus(str, Enum):
    """Feedback onay durumu."""
    PENDING = "pending"             # Henüz onaylanmadı
    CONFIRMED = "confirmed"         # Karşılaştırma sonrası onaylandı
    CANCELLED = "cancelled"         # Karşılaştırma sonrası iptal edildi


# Model configuration - dynamically loaded from settings
MODEL_CONFIG = {
    ModelSize.SMALL: {
        "name": settings.ROUTING_SMALL_MODEL,
        "display_name": settings.ROUTING_SMALL_MODEL_DISPLAY,
        "icon": settings.ROUTING_SMALL_MODEL_ICON,
        "description": "Hızlı yanıtlar, basit sorgular",
        "avg_tokens_per_second": settings.ROUTING_SMALL_MODEL_TOKENS_PER_SEC,
    },
    ModelSize.LARGE: {
        "name": settings.ROUTING_LARGE_MODEL,
        "display_name": settings.ROUTING_LARGE_MODEL_DISPLAY,
        "icon": settings.ROUTING_LARGE_MODEL_ICON,
        "description": "Kapsamlı yanıtlar, karmaşık sorgular",
        "avg_tokens_per_second": settings.ROUTING_LARGE_MODEL_TOKENS_PER_SEC,
    },
}

# Default model for uncertain cases
DEFAULT_MODEL = ModelSize.LARGE

# Confidence thresholds - from settings
CONFIDENCE_HIGH = settings.ROUTING_CONFIDENCE_HIGH      # Auto-route without indicator
CONFIDENCE_MEDIUM = settings.ROUTING_CONFIDENCE_MEDIUM  # Route with "uncertain" indicator
CONFIDENCE_LOW = settings.ROUTING_CONFIDENCE_LOW        # Use default model

# Learning thresholds - from settings
MIN_FEEDBACKS_TO_LEARN = settings.ROUTING_MIN_FEEDBACKS_TO_LEARN  # Minimum feedback count
SIMILARITY_THRESHOLD = settings.ROUTING_SIMILARITY_THRESHOLD       # Minimum similarity


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RoutingResult:
    """Model routing kararı sonucu."""
    model_size: ModelSize
    model_name: str
    confidence: float
    decision_source: RoutingDecision
    reasoning: str
    query_hash: str
    response_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    attempt_number: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_size": self.model_size.value,
            "model_name": self.model_name,
            "model_icon": MODEL_CONFIG[self.model_size]["icon"],
            "model_display_name": MODEL_CONFIG[self.model_size]["display_name"],
            "confidence": round(self.confidence, 2),
            "decision_source": self.decision_source.value,
            "reasoning": self.reasoning,
            "response_id": self.response_id,
            "attempt_number": self.attempt_number,
        }


@dataclass
class Feedback:
    """Kullanıcı feedback'i."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    response_id: str = ""
    query: str = ""
    query_hash: str = ""
    original_model: ModelSize = ModelSize.LARGE
    feedback_type: FeedbackType = FeedbackType.CORRECT
    suggested_model: Optional[ModelSize] = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    comparison_response_id: Optional[str] = None
    final_decision: Optional[ModelSize] = None
    created_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "response_id": self.response_id,
            "query": self.query[:100] + "..." if len(self.query) > 100 else self.query,
            "original_model": self.original_model.value,
            "feedback_type": self.feedback_type.value,
            "suggested_model": self.suggested_model.value if self.suggested_model else None,
            "status": self.status.value,
            "final_decision": self.final_decision.value if self.final_decision else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class LearnedPattern:
    """Feedback'lerden öğrenilmiş pattern."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_type: str = "keyword"  # keyword, regex, semantic
    pattern_value: str = ""
    target_model: ModelSize = ModelSize.SMALL
    confidence: float = 0.5
    sample_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "pattern_value": self.pattern_value[:50],
            "target_model": self.target_model.value,
            "confidence": round(self.confidence, 2),
            "sample_count": self.sample_count,
        }


@dataclass
class RouterMetrics:
    """Router performans metrikleri."""
    total_requests: int = 0
    rule_based_routes: int = 0
    ai_routes: int = 0
    learned_routes: int = 0
    similarity_routes: int = 0
    default_routes: int = 0
    total_feedbacks: int = 0
    confirmed_feedbacks: int = 0
    cancelled_feedbacks: int = 0
    avg_routing_time_ms: float = 0.0
    accuracy_score: float = 0.0  # Confirmed / (Confirmed + Cancelled)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# RULE-BASED ROUTER
# =============================================================================

class RuleBasedRouter:
    """
    Kural tabanlı hızlı router.
    
    Bilinen pattern'lar için anında karar verir (< 1ms).
    """
    
    # Kesinlikle SMALL model için pattern'lar
    SMALL_PATTERNS = {
        "greetings": [
            r"^(selam|merhaba|hey|hi|hello|günaydın|iyi\s*(akşamlar|günler))[\s!?.]*$",
            r"^(naber|nasılsın|ne\s*haber|nasıl\s*gidiyor)[\s?]*$",
            r"^(teşekkür|sağol|eyvallah|tamam|ok|anladım)[\s!.]*$",
        ],
        "simple_facts": [
            r"^.{0,30}\s*(kaç|ne\s*kadar|hangisi|nedir|ne\s*demek)[\s?]*$",
            r"^(bugün|yarın|dün)\s+(günlerden|ayın\s*kaçı|hangi\s*gün)",
            r"^saat\s*kaç",
            r"^\d+\s*[\+\-\*\/]\s*\d+",  # Basit matematik
        ],
        "yes_no": [
            r"^.{0,50}\s*(mı|mi|mu|mü|var\s*mı|olur\s*mu)[\s?]*$",
        ],
        "short_queries": [
            r"^.{0,20}$",  # 20 karakterden kısa sorgular
        ],
    }
    
    # Kesinlikle LARGE model için pattern'lar
    LARGE_PATTERNS = {
        "education": [
            r"(öğret|anlat|açıkla).*(detaylı|kapsamlı|derinlemesine|baştan\s*sona|sıfırdan)",
            r"(öğret|anlat|açıkla)\s+.{20,}",  # Uzun öğretme istekleri
        ],
        "reports": [
            r"(rapor|analiz|araştır).*(oluştur|hazırla|yaz|yap)",
            r"(karşılaştır|compare).*(detaylı|kapsamlı)",
        ],
        "development": [
            r"(proje|uygulama|sistem|mimari).*(nasıl\s*yapılır|tasarla|geliştir)",
            r"(refactor|optimize|debug|review).*(kod|code|fonksiyon|class)",
        ],
        "complex_queries": [
            r".{100,}",  # 100+ karakterlik sorgular
            r"(step\s*by\s*step|adım\s*adım|aşama\s*aşama)",
        ],
    }
    
    # Keyword-based classification
    SMALL_KEYWORDS = {
        "selam", "merhaba", "naber", "nasılsın", "teşekkür", "sağol",
        "evet", "hayır", "tamam", "ok", "anladım", "kaç", "nedir",
        "ne demek", "hangisi", "var mı", "açılımı",
    }
    
    LARGE_KEYWORDS = {
        "öğret", "anlat", "açıkla", "detaylı", "kapsamlı", "rapor",
        "analiz", "karşılaştır", "araştır", "tasarla", "geliştir",
        "refactor", "optimize", "debug", "tutorial", "rehber",
        "strateji", "planlama", "mimari", "architecture",
    }
    
    def __init__(self):
        # Compile regex patterns for performance
        self._small_compiled = {}
        self._large_compiled = {}
        
        for category, patterns in self.SMALL_PATTERNS.items():
            self._small_compiled[category] = [
                re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns
            ]
        
        for category, patterns in self.LARGE_PATTERNS.items():
            self._large_compiled[category] = [
                re.compile(p, re.IGNORECASE | re.UNICODE) for p in patterns
            ]
    
    def route(self, query: str) -> Optional[Tuple[ModelSize, float, str]]:
        """
        Kural tabanlı routing.
        
        Returns:
            (ModelSize, confidence, reasoning) veya None (belirsiz)
        """
        query_lower = query.lower().strip()
        query_length = len(query)
        
        # 1. Check SMALL patterns
        for category, patterns in self._small_compiled.items():
            for pattern in patterns:
                if pattern.search(query_lower):
                    return (
                        ModelSize.SMALL,
                        0.95,
                        f"Rule match: {category}"
                    )
        
        # 2. Check LARGE patterns
        for category, patterns in self._large_compiled.items():
            for pattern in patterns:
                if pattern.search(query_lower):
                    return (
                        ModelSize.LARGE,
                        0.95,
                        f"Rule match: {category}"
                    )
        
        # 3. Keyword analysis
        words = set(query_lower.split())
        
        small_score = len(words & self.SMALL_KEYWORDS)
        large_score = len(words & self.LARGE_KEYWORDS)
        
        if small_score > large_score and small_score >= 1:
            return (
                ModelSize.SMALL,
                min(0.7 + small_score * 0.1, 0.9),
                f"Keyword match: {small_score} small keywords"
            )
        
        if large_score > small_score and large_score >= 1:
            return (
                ModelSize.LARGE,
                min(0.7 + large_score * 0.1, 0.9),
                f"Keyword match: {large_score} large keywords"
            )
        
        # 4. Length-based heuristic
        if query_length < 15:
            return (ModelSize.SMALL, 0.7, "Very short query")
        
        if query_length > 80:
            return (ModelSize.LARGE, 0.7, "Long query")
        
        # Belirsiz - AI router'a bırak
        return None


# =============================================================================
# AI-POWERED ROUTER
# =============================================================================

class AIRouter:
    """
    AI tabanlı router - 4B model ile karar verir.
    
    Belirsiz sorgular için semantic analiz yapar.
    """
    
    ROUTER_SYSTEM_PROMPT = """Sen bir sorgu sınıflandırıcısısın. Kullanıcı sorgularını analiz ederek hangi model boyutunun kullanılması gerektiğine karar veriyorsun.

SMALL model (4B) şunlar için:
- Selamlaşma, günlük konuşma
- Tek cümlelik faktüel sorular
- Evet/Hayır soruları
- Basit tanımlar
- Kısa hesaplamalar
- Basit kod snippet'leri

LARGE model (8B) şunlar için:
- Öğretici/eğitici içerik
- Detaylı açıklamalar
- Rapor oluşturma
- Karşılaştırma ve analiz
- Proje geliştirme
- Kod review/refactoring
- Strateji ve planlama

SADECE şu formatta yanıt ver (başka hiçbir şey yazma):
MODEL: SMALL veya LARGE
CONFIDENCE: 0.0 ile 1.0 arası sayı
REASON: Tek cümlelik açıklama"""

    ROUTER_PROMPT_TEMPLATE = """Sorgu: {query}

Bu sorgu için hangi model kullanılmalı?"""
    
    def __init__(self, model_name: str = "qwen3:4b"):
        self.model_name = model_name
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self._available = None
    
    def is_available(self) -> bool:
        """Router modeli mevcut mu?"""
        if self._available is not None:
            return self._available
        
        try:
            result = self.client.list()
            if hasattr(result, 'models'):
                models = [m.model for m in result.models]
            elif isinstance(result, dict):
                models = [m["name"] for m in result.get("models", [])]
            else:
                models = []
            
            self._available = any(
                self.model_name in m or m.startswith(self.model_name.split(":")[0])
                for m in models
            )
            return self._available
        except Exception:
            self._available = False
            return False
    
    def route(self, query: str) -> Tuple[ModelSize, float, str]:
        """
        AI tabanlı routing kararı.
        
        Returns:
            (ModelSize, confidence, reasoning)
        """
        if not self.is_available():
            logger.warning(f"AI Router model not available: {self.model_name}")
            return (DEFAULT_MODEL, 0.5, "AI router unavailable, using default")
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": self.ROUTER_PROMPT_TEMPLATE.format(query=query)},
                ],
                options={
                    "temperature": 0.1,  # Düşük temperature = tutarlı kararlar
                    "num_predict": 100,  # Kısa yanıt yeterli
                },
            )
            
            # Parse response
            content = response.get("message", {}).get("content", "")
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"AI Router error: {e}")
            return (DEFAULT_MODEL, 0.5, f"AI router error: {str(e)[:50]}")
    
    async def route_async(self, query: str) -> Tuple[ModelSize, float, str]:
        """Async routing."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.route(query))
    
    def _parse_response(self, content: str) -> Tuple[ModelSize, float, str]:
        """AI yanıtını parse et."""
        lines = content.strip().split("\n")
        
        model_size = DEFAULT_MODEL
        confidence = 0.7
        reason = "AI classification"
        
        for line in lines:
            line = line.strip()
            
            if line.upper().startswith("MODEL:"):
                value = line.split(":", 1)[1].strip().upper()
                if "SMALL" in value:
                    model_size = ModelSize.SMALL
                elif "LARGE" in value:
                    model_size = ModelSize.LARGE
            
            elif line.upper().startswith("CONFIDENCE:"):
                try:
                    value = line.split(":", 1)[1].strip()
                    # Extract number from string
                    match = re.search(r"[\d.]+", value)
                    if match:
                        confidence = float(match.group())
                        confidence = max(0.0, min(1.0, confidence))
                except (ValueError, IndexError):
                    pass
            
            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()
        
        return (model_size, confidence, reason)


# =============================================================================
# FEEDBACK STORAGE
# =============================================================================

class FeedbackStorage:
    """
    SQLite-backed feedback storage.
    
    Kullanıcı feedback'lerini ve öğrenilmiş pattern'ları saklar.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(settings.DATA_DIR / "model_routing.db")
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Thread-safe connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self):
        """Veritabanı tablolarını oluştur."""
        conn = self._get_conn()
        
        # Responses table - her yanıtın kaydı
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                model_size TEXT NOT NULL,
                model_name TEXT NOT NULL,
                decision_source TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT,
                attempt_number INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Index for faster lookups
                UNIQUE(query_hash, attempt_number)
            )
        """)
        
        # Feedbacks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedbacks (
                id TEXT PRIMARY KEY,
                response_id TEXT NOT NULL,
                query TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                original_model TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                suggested_model TEXT,
                status TEXT DEFAULT 'pending',
                comparison_response_id TEXT,
                final_decision TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES responses(id)
            )
        """)
        
        # Learned patterns table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                target_model TEXT NOT NULL,
                confidence REAL DEFAULT 0.5,
                sample_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                UNIQUE(pattern_type, pattern_value)
            )
        """)
        
        # Query embeddings for similarity search (optional)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_embeddings (
                query_hash TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                embedding BLOB,
                target_model TEXT NOT NULL,
                feedback_count INTEGER DEFAULT 1,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Metrics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS routing_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_responses_query_hash ON responses(query_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedbacks_response_id ON feedbacks(response_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedbacks_status ON feedbacks(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_patterns_target ON learned_patterns(target_model)")
        
        conn.commit()
    
    # --- Response Methods ---
    
    def save_response(self, result: RoutingResult, query: str) -> None:
        """Routing sonucunu kaydet."""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO responses 
            (id, query, query_hash, model_size, model_name, decision_source, 
             confidence, reasoning, attempt_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result.response_id,
            query,
            result.query_hash,
            result.model_size.value,
            result.model_name,
            result.decision_source.value,
            result.confidence,
            result.reasoning,
            result.attempt_number,
        ))
        conn.commit()
    
    def get_response(self, response_id: str) -> Optional[Dict]:
        """Response bilgisini al."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM responses WHERE id = ?", (response_id,)
        ).fetchone()
        return dict(row) if row else None
    
    def get_responses_by_query_hash(self, query_hash: str) -> List[Dict]:
        """Aynı sorgunun tüm response'larını al."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM responses WHERE query_hash = ? ORDER BY attempt_number",
            (query_hash,)
        ).fetchall()
        return [dict(row) for row in rows]
    
    # --- Feedback Methods ---
    
    def save_feedback(self, feedback: Feedback) -> None:
        """Feedback kaydet."""
        conn = self._get_conn()
        conn.execute("""
            INSERT OR REPLACE INTO feedbacks 
            (id, response_id, query, query_hash, original_model, feedback_type,
             suggested_model, status, comparison_response_id, final_decision,
             created_at, confirmed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback.id,
            feedback.response_id,
            feedback.query,
            feedback.query_hash,
            feedback.original_model.value,
            feedback.feedback_type.value,
            feedback.suggested_model.value if feedback.suggested_model else None,
            feedback.status.value,
            feedback.comparison_response_id,
            feedback.final_decision.value if feedback.final_decision else None,
            feedback.created_at.isoformat(),
            feedback.confirmed_at.isoformat() if feedback.confirmed_at else None,
        ))
        conn.commit()
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Feedback al."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM feedbacks WHERE id = ?", (feedback_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return Feedback(
            id=row["id"],
            response_id=row["response_id"],
            query=row["query"],
            query_hash=row["query_hash"],
            original_model=ModelSize(row["original_model"]),
            feedback_type=FeedbackType(row["feedback_type"]),
            suggested_model=ModelSize(row["suggested_model"]) if row["suggested_model"] else None,
            status=FeedbackStatus(row["status"]),
            comparison_response_id=row["comparison_response_id"],
            final_decision=ModelSize(row["final_decision"]) if row["final_decision"] else None,
        )
    
    def get_feedback_by_response(self, response_id: str) -> Optional[Feedback]:
        """Response'a ait feedback'i al."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM feedbacks WHERE response_id = ? ORDER BY created_at DESC LIMIT 1",
            (response_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return self.get_feedback(row["id"])
    
    def update_feedback_status(
        self, 
        feedback_id: str, 
        status: FeedbackStatus,
        final_decision: Optional[ModelSize] = None,
        comparison_response_id: Optional[str] = None,
    ) -> None:
        """Feedback durumunu güncelle."""
        conn = self._get_conn()
        
        updates = ["status = ?", "confirmed_at = ?"]
        values = [status.value, datetime.now().isoformat()]
        
        if final_decision:
            updates.append("final_decision = ?")
            values.append(final_decision.value)
        
        if comparison_response_id:
            updates.append("comparison_response_id = ?")
            values.append(comparison_response_id)
        
        values.append(feedback_id)
        
        conn.execute(
            f"UPDATE feedbacks SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()
    
    def get_confirmed_feedbacks(
        self, 
        limit: int = 100,
        target_model: Optional[ModelSize] = None
    ) -> List[Feedback]:
        """Onaylanmış feedback'leri al."""
        conn = self._get_conn()
        
        query = "SELECT * FROM feedbacks WHERE status = 'confirmed'"
        params = []
        
        if target_model:
            query += " AND final_decision = ?"
            params.append(target_model.value)
        
        query += " ORDER BY confirmed_at DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
        return [self.get_feedback(row["id"]) for row in rows]
    
    # --- Pattern Learning Methods ---
    
    def save_pattern(self, pattern: LearnedPattern) -> None:
        """Öğrenilmiş pattern kaydet."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO learned_patterns 
            (id, pattern_type, pattern_value, target_model, confidence, sample_count, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pattern_type, pattern_value) DO UPDATE SET
                target_model = excluded.target_model,
                confidence = excluded.confidence,
                sample_count = excluded.sample_count,
                last_updated = excluded.last_updated
        """, (
            pattern.id,
            pattern.pattern_type,
            pattern.pattern_value,
            pattern.target_model.value,
            pattern.confidence,
            pattern.sample_count,
            pattern.last_updated.isoformat(),
        ))
        conn.commit()
    
    def get_patterns_for_model(self, target_model: ModelSize) -> List[LearnedPattern]:
        """Belirli model için öğrenilmiş pattern'ları al."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM learned_patterns WHERE target_model = ? AND confidence >= 0.6",
            (target_model.value,)
        ).fetchall()
        
        return [
            LearnedPattern(
                id=row["id"],
                pattern_type=row["pattern_type"],
                pattern_value=row["pattern_value"],
                target_model=ModelSize(row["target_model"]),
                confidence=row["confidence"],
                sample_count=row["sample_count"],
            )
            for row in rows
        ]
    
    def get_all_patterns(self) -> List[LearnedPattern]:
        """Tüm pattern'ları al."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM learned_patterns ORDER BY confidence DESC"
        ).fetchall()
        
        return [
            LearnedPattern(
                id=row["id"],
                pattern_type=row["pattern_type"],
                pattern_value=row["pattern_value"],
                target_model=ModelSize(row["target_model"]),
                confidence=row["confidence"],
                sample_count=row["sample_count"],
            )
            for row in rows
        ]
    
    # --- Query Embedding Methods ---
    
    def save_query_embedding(
        self, 
        query_hash: str, 
        query: str, 
        embedding: bytes,
        target_model: ModelSize
    ) -> None:
        """Sorgu embedding'ini kaydet."""
        conn = self._get_conn()
        conn.execute("""
            INSERT INTO query_embeddings (query_hash, query, embedding, target_model, feedback_count)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(query_hash) DO UPDATE SET
                feedback_count = feedback_count + 1,
                target_model = excluded.target_model,
                last_updated = CURRENT_TIMESTAMP
        """, (query_hash, query, embedding, target_model.value))
        conn.commit()
    
    def get_all_embeddings(self) -> List[Dict]:
        """Tüm embedding'leri al (similarity search için)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT query_hash, query, embedding, target_model FROM query_embeddings"
        ).fetchall()
        return [dict(row) for row in rows]
    
    # --- Metrics Methods ---
    
    def get_metrics(self) -> Dict[str, Any]:
        """Router metriklerini al."""
        conn = self._get_conn()
        
        # Total responses
        total = conn.execute("SELECT COUNT(*) FROM responses").fetchone()[0]
        
        # By decision source
        sources = conn.execute("""
            SELECT decision_source, COUNT(*) as count 
            FROM responses GROUP BY decision_source
        """).fetchall()
        
        # Feedback stats
        feedback_stats = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM feedbacks GROUP BY status
        """).fetchall()
        
        # Pattern count
        pattern_count = conn.execute("SELECT COUNT(*) FROM learned_patterns").fetchone()[0]
        
        return {
            "total_requests": total,
            "by_source": {row["decision_source"]: row["count"] for row in sources},
            "feedback_stats": {row["status"]: row["count"] for row in feedback_stats},
            "learned_patterns": pattern_count,
        }


# =============================================================================
# PATTERN LEARNER
# =============================================================================

class PatternLearner:
    """
    Feedback'lerden pattern öğrenen sistem.
    
    Confirmed feedback'leri analiz ederek yeni routing kuralları oluşturur.
    """
    
    def __init__(self, storage: FeedbackStorage):
        self.storage = storage
    
    def learn_from_feedback(self, feedback: Feedback) -> List[LearnedPattern]:
        """Tek bir feedback'ten pattern öğren."""
        if feedback.status != FeedbackStatus.CONFIRMED:
            return []
        
        if not feedback.final_decision:
            return []
        
        patterns = []
        query = feedback.query.lower().strip()
        target_model = feedback.final_decision
        
        # 1. Keyword extraction
        keywords = self._extract_keywords(query)
        for keyword in keywords:
            pattern = LearnedPattern(
                pattern_type="keyword",
                pattern_value=keyword,
                target_model=target_model,
                confidence=0.7,
                sample_count=1,
            )
            patterns.append(pattern)
        
        # 2. Length-based pattern
        if len(query) < 30:
            patterns.append(LearnedPattern(
                pattern_type="length",
                pattern_value="short",
                target_model=target_model,
                confidence=0.6,
                sample_count=1,
            ))
        elif len(query) > 100:
            patterns.append(LearnedPattern(
                pattern_type="length",
                pattern_value="long",
                target_model=target_model,
                confidence=0.6,
                sample_count=1,
            ))
        
        # 3. Question type pattern
        if query.endswith("?") or any(q in query for q in ["mı", "mi", "mu", "mü"]):
            patterns.append(LearnedPattern(
                pattern_type="question",
                pattern_value="yes_no" if len(query) < 50 else "complex",
                target_model=target_model,
                confidence=0.65,
                sample_count=1,
            ))
        
        # Save patterns
        for pattern in patterns:
            existing = self._get_existing_pattern(pattern.pattern_type, pattern.pattern_value)
            if existing:
                # Update existing pattern
                if existing.target_model == target_model:
                    existing.confidence = min(0.95, existing.confidence + 0.05)
                    existing.sample_count += 1
                else:
                    # Conflict - reduce confidence
                    existing.confidence = max(0.3, existing.confidence - 0.1)
                existing.last_updated = datetime.now()
                self.storage.save_pattern(existing)
            else:
                self.storage.save_pattern(pattern)
        
        return patterns
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Sorgudan önemli keyword'leri çıkar."""
        # Stopwords
        stopwords = {
            "bir", "bu", "şu", "o", "ve", "ile", "için", "de", "da", "mi", "mı",
            "mu", "mü", "ne", "nasıl", "neden", "niçin", "the", "a", "an", "is",
            "are", "was", "were", "be", "been", "being", "have", "has", "had",
        }
        
        words = re.findall(r'\b\w{3,}\b', query.lower())
        keywords = [w for w in words if w not in stopwords]
        
        # Return top 3 most significant
        return keywords[:3]
    
    def _get_existing_pattern(
        self, 
        pattern_type: str, 
        pattern_value: str
    ) -> Optional[LearnedPattern]:
        """Mevcut pattern'ı bul."""
        patterns = self.storage.get_all_patterns()
        for p in patterns:
            if p.pattern_type == pattern_type and p.pattern_value == pattern_value:
                return p
        return None
    
    def batch_learn(self) -> int:
        """Tüm confirmed feedback'lerden toplu öğren."""
        feedbacks = self.storage.get_confirmed_feedbacks(limit=500)
        learned_count = 0
        
        for feedback in feedbacks:
            patterns = self.learn_from_feedback(feedback)
            learned_count += len(patterns)
        
        return learned_count


# =============================================================================
# MAIN MODEL ROUTER
# =============================================================================

class ModelRouter:
    """
    Ana model router sınıfı.
    
    Tüm routing stratejilerini koordine eder:
    1. Rule-based (hızlı path)
    2. Learned patterns (feedback'ten öğrenilmiş)
    3. AI router (4B model)
    4. Default fallback
    """
    
    def __init__(
        self,
        enable_ai_router: bool = True,
        enable_learning: bool = True,
        db_path: Optional[str] = None,
    ):
        self.rule_router = RuleBasedRouter()
        self.ai_router = AIRouter() if enable_ai_router else None
        self.storage = FeedbackStorage(db_path)
        self.learner = PatternLearner(self.storage) if enable_learning else None
        
        self._enable_learning = enable_learning
        self._metrics = RouterMetrics()
        
        # Load learned patterns
        self._learned_patterns: Dict[str, List[LearnedPattern]] = {
            ModelSize.SMALL.value: [],
            ModelSize.LARGE.value: [],
        }
        self._load_learned_patterns()
        
        logger.info(f"ModelRouter initialized. AI Router: {enable_ai_router}, Learning: {enable_learning}")
    
    def _load_learned_patterns(self):
        """Öğrenilmiş pattern'ları yükle."""
        for model_size in [ModelSize.SMALL, ModelSize.LARGE]:
            patterns = self.storage.get_patterns_for_model(model_size)
            self._learned_patterns[model_size.value] = patterns
            logger.info(f"Loaded {len(patterns)} patterns for {model_size.value}")
    
    @staticmethod
    def hash_query(query: str) -> str:
        """Sorgu hash'i oluştur."""
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def route(self, query: str) -> RoutingResult:
        """
        Ana routing metodu.
        
        Args:
            query: Kullanıcı sorgusu
            
        Returns:
            RoutingResult with model decision
        """
        start_time = time.time()
        query_hash = self.hash_query(query)
        self._metrics.total_requests += 1
        
        # 1. Rule-based check (fastest)
        rule_result = self.rule_router.route(query)
        if rule_result and rule_result[1] >= CONFIDENCE_HIGH:
            model_size, confidence, reasoning = rule_result
            self._metrics.rule_based_routes += 1
            
            result = RoutingResult(
                model_size=model_size,
                model_name=MODEL_CONFIG[model_size]["name"],
                confidence=confidence,
                decision_source=RoutingDecision.RULE_BASED,
                reasoning=reasoning,
                query_hash=query_hash,
            )
            self.storage.save_response(result, query)
            self._update_routing_time(start_time)
            return result
        
        # 2. Check learned patterns
        learned_result = self._check_learned_patterns(query)
        if learned_result and learned_result[1] >= CONFIDENCE_MEDIUM:
            model_size, confidence, reasoning = learned_result
            self._metrics.learned_routes += 1
            
            result = RoutingResult(
                model_size=model_size,
                model_name=MODEL_CONFIG[model_size]["name"],
                confidence=confidence,
                decision_source=RoutingDecision.LEARNED,
                reasoning=reasoning,
                query_hash=query_hash,
            )
            self.storage.save_response(result, query)
            self._update_routing_time(start_time)
            return result
        
        # 3. AI Router (if available)
        if self.ai_router:
            model_size, confidence, reasoning = self.ai_router.route(query)
            self._metrics.ai_routes += 1
            
            result = RoutingResult(
                model_size=model_size,
                model_name=MODEL_CONFIG[model_size]["name"],
                confidence=confidence,
                decision_source=RoutingDecision.AI_ROUTER,
                reasoning=reasoning,
                query_hash=query_hash,
            )
            self.storage.save_response(result, query)
            self._update_routing_time(start_time)
            return result
        
        # 4. Default fallback
        self._metrics.default_routes += 1
        
        # Use rule-based result if available, else default
        if rule_result:
            model_size, confidence, reasoning = rule_result
        else:
            model_size = DEFAULT_MODEL
            confidence = 0.5
            reasoning = "Default model (no matching rules)"
        
        result = RoutingResult(
            model_size=model_size,
            model_name=MODEL_CONFIG[model_size]["name"],
            confidence=confidence,
            decision_source=RoutingDecision.DEFAULT,
            reasoning=reasoning,
            query_hash=query_hash,
        )
        self.storage.save_response(result, query)
        self._update_routing_time(start_time)
        return result
    
    async def route_async(self, query: str) -> RoutingResult:
        """Async routing."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.route(query))
    
    def _check_learned_patterns(self, query: str) -> Optional[Tuple[ModelSize, float, str]]:
        """Öğrenilmiş pattern'lara karşı kontrol."""
        query_lower = query.lower()
        
        best_match = None
        best_confidence = 0.0
        
        for model_size in [ModelSize.SMALL, ModelSize.LARGE]:
            patterns = self._learned_patterns.get(model_size.value, [])
            
            for pattern in patterns:
                if pattern.pattern_type == "keyword":
                    if pattern.pattern_value in query_lower:
                        if pattern.confidence > best_confidence:
                            best_match = (model_size, pattern.confidence, f"Learned keyword: {pattern.pattern_value}")
                            best_confidence = pattern.confidence
        
        return best_match
    
    def _update_routing_time(self, start_time: float):
        """Routing süresini güncelle."""
        elapsed = (time.time() - start_time) * 1000
        n = self._metrics.total_requests
        self._metrics.avg_routing_time_ms = (
            (self._metrics.avg_routing_time_ms * (n - 1) + elapsed) / n
        )
    
    # --- Feedback Methods ---
    
    def submit_feedback(
        self,
        response_id: str,
        feedback_type: FeedbackType,
        suggested_model: Optional[ModelSize] = None,
    ) -> Feedback:
        """
        Kullanıcı feedback'i kaydet.
        
        Args:
            response_id: Yanıt ID'si
            feedback_type: Feedback tipi
            suggested_model: Önerilen model (downgrade/upgrade için)
            
        Returns:
            Created Feedback object
        """
        response = self.storage.get_response(response_id)
        if not response:
            raise ValueError(f"Response not found: {response_id}")
        
        feedback = Feedback(
            response_id=response_id,
            query=response["query"],
            query_hash=response["query_hash"],
            original_model=ModelSize(response["model_size"]),
            feedback_type=feedback_type,
            suggested_model=suggested_model,
            status=FeedbackStatus.PENDING if feedback_type != FeedbackType.CORRECT else FeedbackStatus.CONFIRMED,
        )
        
        # If correct, mark as confirmed immediately
        if feedback_type == FeedbackType.CORRECT:
            feedback.final_decision = feedback.original_model
            feedback.confirmed_at = datetime.now()
        
        self.storage.save_feedback(feedback)
        self._metrics.total_feedbacks += 1
        
        # Learn from correct feedback immediately
        if feedback_type == FeedbackType.CORRECT and self.learner:
            self.learner.learn_from_feedback(feedback)
            self._load_learned_patterns()
        
        return feedback
    
    def request_comparison(
        self,
        feedback_id: str,
    ) -> Tuple[str, RoutingResult]:
        """
        Karşılaştırma için diğer modelle routing iste.
        
        Args:
            feedback_id: Feedback ID'si
            
        Returns:
            (query, RoutingResult for comparison model)
        """
        feedback = self.storage.get_feedback(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback not found: {feedback_id}")
        
        if feedback.status != FeedbackStatus.PENDING:
            raise ValueError(f"Feedback already processed: {feedback.status}")
        
        # Determine comparison model
        if feedback.feedback_type == FeedbackType.DOWNGRADE:
            comparison_model = ModelSize.SMALL
        elif feedback.feedback_type == FeedbackType.UPGRADE:
            comparison_model = ModelSize.LARGE
        else:
            raise ValueError(f"Invalid feedback type for comparison: {feedback.feedback_type}")
        
        # Create comparison routing result
        comparison_result = RoutingResult(
            model_size=comparison_model,
            model_name=MODEL_CONFIG[comparison_model]["name"],
            confidence=1.0,
            decision_source=RoutingDecision.DEFAULT,
            reasoning="Comparison request by user",
            query_hash=feedback.query_hash,
            attempt_number=2,  # Second attempt
        )
        
        self.storage.save_response(comparison_result, feedback.query)
        
        # Update feedback with comparison response ID
        self.storage.update_feedback_status(
            feedback_id,
            FeedbackStatus.PENDING,
            comparison_response_id=comparison_result.response_id,
        )
        
        return (feedback.query, comparison_result)
    
    def confirm_feedback(
        self,
        feedback_id: str,
        confirmed: bool,
    ) -> Feedback:
        """
        Karşılaştırma sonrası feedback'i onayla veya iptal et.
        
        Args:
            feedback_id: Feedback ID'si
            confirmed: True = Feedback doğruydu, False = İlk model doğruydu
            
        Returns:
            Updated Feedback
        """
        feedback = self.storage.get_feedback(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback not found: {feedback_id}")
        
        if confirmed:
            # Feedback was correct
            final_decision = feedback.suggested_model
            status = FeedbackStatus.CONFIRMED
            self._metrics.confirmed_feedbacks += 1
        else:
            # Original model was correct
            final_decision = feedback.original_model
            status = FeedbackStatus.CANCELLED
            self._metrics.cancelled_feedbacks += 1
        
        self.storage.update_feedback_status(
            feedback_id,
            status,
            final_decision=final_decision,
        )
        
        # Learn from confirmed feedback
        if confirmed and self.learner:
            feedback.status = status
            feedback.final_decision = final_decision
            self.learner.learn_from_feedback(feedback)
            self._load_learned_patterns()
        
        # Update accuracy
        total = self._metrics.confirmed_feedbacks + self._metrics.cancelled_feedbacks
        if total > 0:
            self._metrics.accuracy_score = self._metrics.confirmed_feedbacks / total
        
        return self.storage.get_feedback(feedback_id)
    
    # --- Stats & Config ---
    
    def get_stats(self) -> Dict[str, Any]:
        """Router istatistiklerini al."""
        db_metrics = self.storage.get_metrics()
        
        return {
            "runtime_metrics": self._metrics.to_dict(),
            "database_metrics": db_metrics,
            "models": {
                k.value: v for k, v in MODEL_CONFIG.items()
            },
            "learned_patterns": {
                ModelSize.SMALL.value: len(self._learned_patterns.get(ModelSize.SMALL.value, [])),
                ModelSize.LARGE.value: len(self._learned_patterns.get(ModelSize.LARGE.value, [])),
            },
            "ai_router_available": self.ai_router.is_available() if self.ai_router else False,
        }
    
    def get_model_config(self, model_size: ModelSize) -> Dict[str, Any]:
        """Model konfigürasyonunu al."""
        return MODEL_CONFIG.get(model_size, MODEL_CONFIG[DEFAULT_MODEL])
    
    def refresh_patterns(self):
        """Pattern cache'ini yenile."""
        self._load_learned_patterns()


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Lazy initialization
_model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Global ModelRouter instance'ını al."""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter(
            enable_ai_router=True,
            enable_learning=True,
        )
    return _model_router


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "ModelSize",
    "RoutingDecision", 
    "FeedbackType",
    "FeedbackStatus",
    
    # Data classes
    "RoutingResult",
    "Feedback",
    "LearnedPattern",
    "RouterMetrics",
    
    # Config
    "MODEL_CONFIG",
    "DEFAULT_MODEL",
    
    # Classes
    "RuleBasedRouter",
    "AIRouter",
    "FeedbackStorage",
    "PatternLearner",
    "ModelRouter",
    
    # Functions
    "get_model_router",
]
