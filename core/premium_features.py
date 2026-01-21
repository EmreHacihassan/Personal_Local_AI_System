"""
Enterprise AI Assistant - Premium Features
==========================================

4 Premium Özellik:
1. 🏷️ Smart Auto-Tagging & Categorization
2. 📊 Real-time Analytics Dashboard
3. 🔄 Semantic Reranking (Cross-Encoder)
4. 🕸️ Knowledge Graph

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import hashlib
import json
import math
import re
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from threading import Lock
import statistics
from pathlib import Path

from .config import settings
from .logger import get_logger

logger = get_logger("premium_features")


# =============================================================================
# 1. SMART AUTO-TAGGING & CATEGORIZATION
# =============================================================================

@dataclass
class TaggingConfig:
    """Auto-tagging yapılandırması."""
    enabled: bool = True
    max_tags: int = 10
    min_confidence: float = 0.3
    use_keywords: bool = True
    use_entities: bool = True
    use_topics: bool = True
    custom_categories: List[str] = field(default_factory=list)


class SmartAutoTagger:
    """
    AI-powered otomatik etiketleme sistemi.
    
    Özellikler:
    - Keyword extraction
    - Named entity recognition (basit)
    - Topic classification
    - Custom category matching
    - Confidence scoring
    """
    
    # Predefined categories with keywords
    CATEGORIES = {
        "technology": [
            "api", "code", "software", "programming", "developer", "algorithm",
            "database", "server", "cloud", "docker", "kubernetes", "python",
            "javascript", "react", "node", "ai", "machine learning", "neural",
            "network", "security", "encryption", "authentication", "frontend",
            "backend", "devops", "git", "version control", "debug", "testing"
        ],
        "business": [
            "revenue", "profit", "loss", "investment", "market", "customer",
            "sales", "marketing", "strategy", "growth", "startup", "enterprise",
            "b2b", "b2c", "roi", "kpi", "metrics", "analytics", "report",
            "budget", "finance", "accounting", "tax", "invoice", "payment"
        ],
        "science": [
            "research", "study", "experiment", "hypothesis", "theory", "data",
            "analysis", "statistics", "methodology", "peer review", "journal",
            "publication", "citation", "laboratory", "scientist", "discovery"
        ],
        "education": [
            "learning", "teaching", "course", "curriculum", "student", "teacher",
            "university", "school", "training", "workshop", "tutorial", "lesson",
            "exam", "test", "grade", "certificate", "degree", "diploma"
        ],
        "health": [
            "medical", "health", "disease", "treatment", "diagnosis", "symptom",
            "medicine", "drug", "therapy", "patient", "doctor", "hospital",
            "clinic", "surgery", "vaccine", "nutrition", "fitness", "wellness"
        ],
        "legal": [
            "law", "legal", "contract", "agreement", "compliance", "regulation",
            "policy", "terms", "conditions", "privacy", "gdpr", "license",
            "copyright", "trademark", "patent", "litigation", "court", "attorney"
        ],
        "documentation": [
            "readme", "documentation", "guide", "manual", "tutorial", "howto",
            "instructions", "reference", "api docs", "changelog", "release notes",
            "installation", "configuration", "setup", "troubleshooting"
        ],
        "project": [
            "project", "task", "milestone", "deadline", "sprint", "agile",
            "scrum", "kanban", "backlog", "roadmap", "timeline", "planning",
            "meeting", "standup", "retrospective", "review"
        ]
    }
    
    # Entity patterns (simplified NER)
    ENTITY_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
        "version": r'\bv?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?\b',
        "date": r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "file_path": r'[A-Za-z]:\\[^\s]+|/[^\s]+\.[a-zA-Z]+',
        "code_block": r'```[\s\S]*?```',
        "function": r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)',
        "class_name": r'\bclass\s+([A-Z][a-zA-Z0-9_]*)',
        "import": r'\b(?:import|from)\s+[a-zA-Z_][a-zA-Z0-9_.]*'
    }
    
    # Stop words for keyword extraction
    STOP_WORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "this", "that", "these", "those", "i", "you", "he", "she", "it",
        "we", "they", "what", "which", "who", "when", "where", "why", "how",
        "all", "each", "every", "both", "few", "more", "most", "other",
        "some", "such", "no", "not", "only", "same", "so", "than", "too",
        "very", "just", "also", "now", "here", "there", "then", "once",
        "bir", "ve", "veya", "için", "ile", "gibi", "bu", "şu", "o", "da",
        "de", "ki", "ama", "fakat", "ancak", "çünkü", "eğer", "nasıl", "ne",
        "neden", "nerede", "kim", "hangi", "kadar", "daha", "çok", "az"
    }
    
    def __init__(self, config: Optional[TaggingConfig] = None):
        self.config = config or TaggingConfig()
        self._cache: Dict[str, Dict] = {}
        self._cache_lock = Lock()
        logger.info("SmartAutoTagger initialized")
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        TF-IDF benzeri keyword extraction.
        
        Returns:
            List of (keyword, score) tuples
        """
        # Tokenize
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ][a-zA-ZğüşıöçĞÜŞİÖÇ0-9_-]*\b', text.lower())
        
        # Filter stop words and short words
        words = [w for w in words if w not in self.STOP_WORDS and len(w) > 2]
        
        if not words:
            return []
        
        # Count frequencies
        word_freq = Counter(words)
        total_words = len(words)
        
        # Calculate TF-IDF-like scores
        scores = []
        for word, freq in word_freq.items():
            tf = freq / total_words
            # IDF approximation based on word length and character diversity
            idf = math.log(1 + len(set(word)) / len(word)) + 0.5
            score = tf * idf * len(word) / 10  # Longer words slightly preferred
            scores.append((word, min(score * 10, 1.0)))  # Normalize to 0-1
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_n]
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Basit Named Entity Recognition.
        
        Returns:
            Dict of entity_type -> list of entities
        """
        entities = {}
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Deduplicate
                unique_matches = list(set(matches))[:5]  # Max 5 per type
                entities[entity_type] = unique_matches
        
        return entities
    
    def classify_topics(self, text: str) -> List[Tuple[str, float]]:
        """
        Topic classification based on keyword matching.
        
        Returns:
            List of (topic, confidence) tuples
        """
        text_lower = text.lower()
        topic_scores = []
        
        for topic, keywords in self.CATEGORIES.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                # Score based on match ratio
                confidence = min(matches / 5, 1.0)  # Max 1.0 with 5+ matches
                topic_scores.append((topic, confidence))
        
        # Sort by confidence
        topic_scores.sort(key=lambda x: x[1], reverse=True)
        
        return topic_scores[:3]  # Top 3 topics
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Basit dil tespiti.
        
        Returns:
            (language_code, confidence)
        """
        # Turkish indicators
        turkish_chars = set("ğüşıöçĞÜŞİÖÇ")
        turkish_words = {"ve", "bir", "için", "ile", "bu", "da", "de", "ki", "ama", "gibi"}
        
        text_lower = text.lower()
        words = set(re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', text_lower))
        
        # Check Turkish characters
        has_turkish_chars = any(c in text for c in turkish_chars)
        turkish_word_count = len(words & turkish_words)
        
        if has_turkish_chars or turkish_word_count >= 2:
            confidence = 0.7 + (0.3 if has_turkish_chars else 0) + min(turkish_word_count * 0.05, 0.2)
            return ("tr", min(confidence, 1.0))
        
        return ("en", 0.8)  # Default to English
    
    def generate_tags(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Ana tagging fonksiyonu.
        
        Returns:
            {
                "tags": ["tag1", "tag2", ...],
                "categories": [("category", confidence), ...],
                "entities": {"type": ["entity", ...]},
                "keywords": [("keyword", score), ...],
                "language": ("code", confidence),
                "confidence": overall_confidence
            }
        """
        # Check cache
        content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        with self._cache_lock:
            if content_hash in self._cache:
                return self._cache[content_hash]
        
        result = {
            "tags": [],
            "categories": [],
            "entities": {},
            "keywords": [],
            "language": ("unknown", 0.0),
            "confidence": 0.0,
            "generated_at": datetime.now().isoformat()
        }
        
        try:
            # 1. Extract keywords
            if self.config.use_keywords:
                keywords = self.extract_keywords(content, top_n=15)
                result["keywords"] = keywords
                result["tags"].extend([kw for kw, score in keywords[:5] if score >= self.config.min_confidence])
            
            # 2. Extract entities
            if self.config.use_entities:
                entities = self.extract_entities(content)
                result["entities"] = entities
                # Add entity types as tags
                for entity_type in entities.keys():
                    result["tags"].append(f"has_{entity_type}")
            
            # 3. Classify topics
            if self.config.use_topics:
                topics = self.classify_topics(content)
                result["categories"] = topics
                result["tags"].extend([topic for topic, conf in topics if conf >= self.config.min_confidence])
            
            # 4. Detect language
            language = self.detect_language(content)
            result["language"] = language
            result["tags"].append(f"lang_{language[0]}")
            
            # 5. Add metadata-based tags
            if metadata:
                if "source" in metadata:
                    source = metadata["source"]
                    if source.endswith(".md"):
                        result["tags"].append("markdown")
                    elif source.endswith(".py"):
                        result["tags"].append("python")
                    elif source.endswith((".js", ".ts")):
                        result["tags"].append("javascript")
                    elif source.endswith(".json"):
                        result["tags"].append("json")
            
            # 6. Deduplicate and limit tags
            result["tags"] = list(dict.fromkeys(result["tags"]))[:self.config.max_tags]
            
            # 7. Calculate overall confidence
            confidences = []
            if result["categories"]:
                confidences.append(max(c for _, c in result["categories"]))
            if result["keywords"]:
                confidences.append(max(s for _, s in result["keywords"][:3]))
            confidences.append(result["language"][1])
            
            result["confidence"] = statistics.mean(confidences) if confidences else 0.5
            
            # Cache result
            with self._cache_lock:
                self._cache[content_hash] = result
                # Limit cache size
                if len(self._cache) > 1000:
                    # Remove oldest entries
                    oldest_keys = list(self._cache.keys())[:100]
                    for key in oldest_keys:
                        del self._cache[key]
            
        except Exception as e:
            logger.error(f"Tagging error: {e}")
            result["error"] = str(e)
        
        return result
    
    def suggest_similar_tags(self, tags: List[str]) -> List[str]:
        """Mevcut tag'lere benzer tag önerileri."""
        suggestions = []
        
        tag_mappings = {
            "python": ["programming", "backend", "scripting"],
            "javascript": ["frontend", "web", "nodejs"],
            "api": ["rest", "endpoint", "integration"],
            "database": ["sql", "nosql", "storage"],
            "technology": ["software", "development", "engineering"],
            "documentation": ["guide", "tutorial", "reference"]
        }
        
        for tag in tags:
            if tag in tag_mappings:
                suggestions.extend(tag_mappings[tag])
        
        return list(set(suggestions) - set(tags))[:5]


# =============================================================================
# 2. REAL-TIME ANALYTICS DASHBOARD
# =============================================================================

@dataclass
class AnalyticsEvent:
    """Tek bir analytics event."""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class RealTimeAnalytics:
    """
    Real-time analytics ve dashboard metrikleri.
    
    Özellikler:
    - Live event tracking
    - Time-series metrics
    - Aggregations (count, avg, sum)
    - Anomaly detection
    - Performance monitoring
    """
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self._events: List[AnalyticsEvent] = []
        self._metrics: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._lock = Lock()
        self._start_time = datetime.now()
        
        # Performance tracking
        self._response_times: List[float] = []
        self._error_counts: Dict[str, int] = defaultdict(int)
        
        logger.info("RealTimeAnalytics initialized")
    
    def track_event(
        self,
        event_type: str,
        data: Optional[Dict] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Event kaydet."""
        event = AnalyticsEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            data=data or {},
            user_id=user_id,
            session_id=session_id
        )
        
        with self._lock:
            self._events.append(event)
            self._counters[event_type] += 1
            self._cleanup_old_events()
    
    def record_metric(self, name: str, value: float):
        """Sayısal metrik kaydet."""
        with self._lock:
            self._metrics[name].append((datetime.now(), value))
            # Keep last 1000 values per metric
            if len(self._metrics[name]) > 1000:
                self._metrics[name] = self._metrics[name][-1000:]
    
    def set_gauge(self, name: str, value: float):
        """Gauge değeri set et (anlık değer)."""
        with self._lock:
            self._gauges[name] = value
    
    def increment_counter(self, name: str, amount: int = 1):
        """Counter artır."""
        with self._lock:
            self._counters[name] += amount
    
    def record_response_time(self, duration_ms: float):
        """Response time kaydet."""
        with self._lock:
            self._response_times.append(duration_ms)
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-1000:]
    
    def record_error(self, error_type: str):
        """Error kaydet."""
        with self._lock:
            self._error_counts[error_type] += 1
            self._counters["total_errors"] += 1
    
    def _cleanup_old_events(self):
        """Eski event'leri temizle."""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        self._events = [e for e in self._events if e.timestamp > cutoff]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Dashboard için tüm metrikleri döndür.
        
        Returns:
            Comprehensive dashboard data
        """
        with self._lock:
            now = datetime.now()
            uptime = (now - self._start_time).total_seconds()
            
            # Calculate response time stats
            rt_stats = {}
            if self._response_times:
                rt_stats = {
                    "avg": statistics.mean(self._response_times),
                    "min": min(self._response_times),
                    "max": max(self._response_times),
                    "p50": statistics.median(self._response_times),
                    "p95": self._percentile(self._response_times, 95),
                    "p99": self._percentile(self._response_times, 99),
                    "count": len(self._response_times)
                }
            
            # Events per type (last hour)
            one_hour_ago = now - timedelta(hours=1)
            recent_events = [e for e in self._events if e.timestamp > one_hour_ago]
            events_by_type = defaultdict(int)
            for event in recent_events:
                events_by_type[event.event_type] += 1
            
            # Time series for charts (last 60 minutes, per-minute buckets)
            time_series = self._get_time_series(minutes=60)
            
            return {
                "timestamp": now.isoformat(),
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                
                # Counters
                "counters": dict(self._counters),
                
                # Gauges
                "gauges": dict(self._gauges),
                
                # Response times
                "response_times": rt_stats,
                
                # Error summary
                "errors": {
                    "total": self._counters.get("total_errors", 0),
                    "by_type": dict(self._error_counts),
                    "error_rate": self._calculate_error_rate()
                },
                
                # Recent events
                "recent_events": {
                    "last_hour_count": len(recent_events),
                    "by_type": dict(events_by_type)
                },
                
                # Time series
                "time_series": time_series,
                
                # Health score
                "health": self._calculate_health_score()
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _get_time_series(self, minutes: int = 60) -> Dict[str, List]:
        """Get time series data for charts."""
        now = datetime.now()
        buckets = defaultdict(lambda: defaultdict(int))
        
        for event in self._events:
            age_minutes = (now - event.timestamp).total_seconds() / 60
            if age_minutes <= minutes:
                bucket = int(age_minutes)
                buckets[bucket][event.event_type] += 1
        
        # Convert to chart format
        labels = [f"-{i}m" for i in range(minutes, -1, -5)]
        datasets = defaultdict(list)
        
        for i in range(0, minutes + 1, 5):
            for event_type in set(e.event_type for e in self._events):
                count = sum(buckets[j].get(event_type, 0) for j in range(i, min(i + 5, minutes + 1)))
                datasets[event_type].append(count)
        
        return {"labels": labels, "datasets": dict(datasets)}
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate."""
        total_requests = self._counters.get("total_requests", 0)
        total_errors = self._counters.get("total_errors", 0)
        
        if total_requests == 0:
            return 0.0
        
        return round(total_errors / total_requests * 100, 2)
    
    def _calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall health score."""
        score = 100.0
        issues = []
        
        # Check error rate
        error_rate = self._calculate_error_rate()
        if error_rate > 10:
            score -= 30
            issues.append(f"High error rate: {error_rate}%")
        elif error_rate > 5:
            score -= 15
            issues.append(f"Elevated error rate: {error_rate}%")
        
        # Check response times
        if self._response_times:
            avg_rt = statistics.mean(self._response_times)
            if avg_rt > 5000:  # > 5 seconds
                score -= 20
                issues.append(f"Slow response times: {avg_rt:.0f}ms avg")
            elif avg_rt > 2000:  # > 2 seconds
                score -= 10
                issues.append(f"Moderate response times: {avg_rt:.0f}ms avg")
        
        status = "healthy" if score >= 80 else "degraded" if score >= 50 else "unhealthy"
        
        return {
            "score": max(0, score),
            "status": status,
            "issues": issues
        }
    
    def get_live_metrics(self) -> Dict[str, Any]:
        """WebSocket için anlık metrikler."""
        with self._lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "recent_response_time": self._response_times[-1] if self._response_times else None,
                "health_status": self._calculate_health_score()["status"]
            }


# =============================================================================
# 3. SEMANTIC RERANKING
# =============================================================================

@dataclass
class RerankerConfig:
    """Reranker yapılandırması."""
    enabled: bool = True
    top_k_rerank: int = 20  # İlk kaç sonucu rerank et
    final_k: int = 5  # Son kaç sonuç döndür
    min_score: float = 0.1  # Minimum rerank score
    boost_recency: bool = True  # Yeni dökümanları boost et
    boost_factor: float = 0.1  # Recency boost factor


class SemanticReranker:
    """
    Cross-encoder benzeri semantic reranking.
    
    Özellikler:
    - Query-document relevance scoring
    - Keyword matching boost
    - Recency boost
    - Diversity optimization
    - Score normalization
    """
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        self.config = config or RerankerConfig()
        self._query_cache: Dict[str, List] = {}
        logger.info("SemanticReranker initialized")
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        original_scores: Optional[List[float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Dökümanları yeniden sırala.
        
        Args:
            query: Search query
            documents: List of documents with 'content' and optional 'metadata'
            original_scores: Original similarity scores
            
        Returns:
            Reranked documents with scores
        """
        if not documents:
            return []
        
        if not self.config.enabled:
            return documents[:self.config.final_k]
        
        # Limit to top_k_rerank for efficiency
        docs_to_rerank = documents[:self.config.top_k_rerank]
        
        # Calculate rerank scores
        scored_docs = []
        query_lower = query.lower()
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        
        for i, doc in enumerate(docs_to_rerank):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            # Base score from original ranking
            original_score = original_scores[i] if original_scores and i < len(original_scores) else 0.5
            
            # Calculate rerank score
            rerank_score = self._calculate_relevance_score(
                query_lower, query_words, content, metadata
            )
            
            # Combine scores (weighted average)
            final_score = 0.4 * original_score + 0.6 * rerank_score
            
            # Apply recency boost
            if self.config.boost_recency:
                final_score = self._apply_recency_boost(final_score, metadata)
            
            scored_docs.append({
                **doc,
                "rerank_score": round(final_score, 4),
                "original_score": round(original_score, 4),
                "relevance_score": round(rerank_score, 4)
            })
        
        # Sort by final score
        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        # Apply diversity (optional - avoid very similar results)
        diverse_docs = self._apply_diversity(scored_docs)
        
        # Filter by min score and return top results
        return [
            doc for doc in diverse_docs[:self.config.final_k]
            if doc["rerank_score"] >= self.config.min_score
        ]
    
    def _calculate_relevance_score(
        self,
        query_lower: str,
        query_words: Set[str],
        content: str,
        metadata: Dict
    ) -> float:
        """Calculate query-document relevance score."""
        content_lower = content.lower()
        content_words = set(re.findall(r'\b\w+\b', content_lower))
        
        scores = []
        
        # 1. Exact phrase match (highest weight)
        if query_lower in content_lower:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        # 2. Word overlap (Jaccard similarity)
        if query_words and content_words:
            intersection = len(query_words & content_words)
            union = len(query_words | content_words)
            jaccard = intersection / union if union > 0 else 0
            scores.append(jaccard)
        else:
            scores.append(0.0)
        
        # 3. Query word coverage
        if query_words:
            words_found = sum(1 for w in query_words if w in content_lower)
            coverage = words_found / len(query_words)
            scores.append(coverage)
        else:
            scores.append(0.0)
        
        # 4. Position score (earlier mention = higher score)
        positions = []
        for word in query_words:
            pos = content_lower.find(word)
            if pos != -1:
                positions.append(pos)
        
        if positions:
            avg_position = sum(positions) / len(positions)
            # Normalize: closer to 0 = better
            position_score = max(0, 1 - (avg_position / max(len(content), 1)))
            scores.append(position_score)
        else:
            scores.append(0.0)
        
        # 5. Title/source match
        source = metadata.get("source", "").lower()
        if any(word in source for word in query_words):
            scores.append(0.8)
        else:
            scores.append(0.0)
        
        # Weighted average
        weights = [0.3, 0.2, 0.25, 0.15, 0.1]
        weighted_score = sum(s * w for s, w in zip(scores, weights))
        
        return min(weighted_score, 1.0)
    
    def _apply_recency_boost(self, score: float, metadata: Dict) -> float:
        """Apply recency boost based on document timestamp."""
        timestamp = metadata.get("timestamp") or metadata.get("indexed_at")
        
        if not timestamp:
            return score
        
        try:
            if isinstance(timestamp, str):
                doc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                doc_time = timestamp
            
            # Calculate age in days
            age_days = (datetime.now() - doc_time.replace(tzinfo=None)).days
            
            # Boost newer documents (decay over 30 days)
            if age_days < 30:
                boost = self.config.boost_factor * (1 - age_days / 30)
                return min(score + boost, 1.0)
        except:
            pass
        
        return score
    
    def _apply_diversity(self, docs: List[Dict]) -> List[Dict]:
        """Apply diversity to avoid very similar results."""
        if len(docs) <= 2:
            return docs
        
        diverse_docs = [docs[0]]  # Always keep the best result
        
        for doc in docs[1:]:
            # Check if too similar to already selected docs
            is_diverse = True
            doc_content = doc.get("content", "")[:200].lower()
            
            for selected in diverse_docs:
                selected_content = selected.get("content", "")[:200].lower()
                
                # Simple similarity check
                common_words = len(
                    set(doc_content.split()) & set(selected_content.split())
                )
                total_words = len(set(doc_content.split()) | set(selected_content.split()))
                
                if total_words > 0 and common_words / total_words > 0.8:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse_docs.append(doc)
        
        return diverse_docs


# =============================================================================
# 4. KNOWLEDGE GRAPH
# =============================================================================

@dataclass
class GraphNode:
    """Knowledge graph node."""
    id: str
    label: str
    type: str  # document, concept, entity, tag
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class GraphEdge:
    """Knowledge graph edge."""
    source: str
    target: str
    relation: str  # references, similar_to, contains, tagged_with
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """
    Dökümanlar arası ilişki grafiği.
    
    Özellikler:
    - Document-to-document relationships
    - Concept extraction and linking
    - Entity relationships
    - Tag relationships
    - Graph traversal (BFS, shortest path)
    - Community detection
    - Graph visualization export
    """
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._lock = Lock()
        logger.info("KnowledgeGraph initialized")
    
    def add_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        properties: Optional[Dict] = None,
        weight: float = 1.0
    ) -> GraphNode:
        """Node ekle."""
        node = GraphNode(
            id=node_id,
            label=label,
            type=node_type,
            properties=properties or {},
            weight=weight
        )
        
        with self._lock:
            self.nodes[node_id] = node
        
        return node
    
    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        weight: float = 1.0,
        properties: Optional[Dict] = None
    ) -> Optional[GraphEdge]:
        """Edge ekle."""
        if source not in self.nodes or target not in self.nodes:
            logger.warning(f"Cannot add edge: missing node {source} or {target}")
            return None
        
        edge = GraphEdge(
            source=source,
            target=target,
            relation=relation,
            weight=weight,
            properties=properties or {}
        )
        
        with self._lock:
            self.edges.append(edge)
            self._adjacency[source].append(target)
            self._adjacency[target].append(source)  # Bidirectional
        
        return edge
    
    def build_from_documents(
        self,
        documents: List[Dict[str, Any]],
        similarity_threshold: float = 0.7
    ):
        """
        Dökümanlardan knowledge graph oluştur.
        
        Args:
            documents: List of documents with content, metadata, tags
            similarity_threshold: Minimum similarity for edges
        """
        logger.info(f"Building knowledge graph from {len(documents)} documents")
        
        # 1. Add document nodes
        for doc in documents:
            doc_id = doc.get("id") or hashlib.md5(doc.get("content", "").encode()).hexdigest()[:12]
            
            self.add_node(
                node_id=f"doc_{doc_id}",
                label=doc.get("metadata", {}).get("source", doc_id)[:50],
                node_type="document",
                properties={
                    "content_preview": doc.get("content", "")[:200],
                    "source": doc.get("metadata", {}).get("source", "unknown"),
                    "created_at": doc.get("metadata", {}).get("indexed_at")
                }
            )
            
            # 2. Add tag nodes and edges
            tags = doc.get("tags", []) or doc.get("metadata", {}).get("tags", [])
            for tag in tags:
                tag_id = f"tag_{tag}"
                if tag_id not in self.nodes:
                    self.add_node(
                        node_id=tag_id,
                        label=tag,
                        node_type="tag"
                    )
                
                self.add_edge(
                    source=f"doc_{doc_id}",
                    target=tag_id,
                    relation="tagged_with"
                )
            
            # 3. Extract concepts (simple keyword extraction)
            content = doc.get("content", "")
            concepts = self._extract_concepts(content)
            
            for concept, count in concepts[:5]:  # Top 5 concepts
                concept_id = f"concept_{concept}"
                if concept_id not in self.nodes:
                    self.add_node(
                        node_id=concept_id,
                        label=concept,
                        node_type="concept",
                        weight=count
                    )
                
                self.add_edge(
                    source=f"doc_{doc_id}",
                    target=concept_id,
                    relation="contains",
                    weight=count / 10
                )
        
        # 4. Find document similarities and add edges
        doc_nodes = [n for n in self.nodes.values() if n.type == "document"]
        
        for i, node1 in enumerate(doc_nodes):
            for node2 in doc_nodes[i+1:]:
                # Check shared tags/concepts
                neighbors1 = set(self._adjacency[node1.id])
                neighbors2 = set(self._adjacency[node2.id])
                
                shared = neighbors1 & neighbors2
                if len(shared) >= 2:  # At least 2 shared connections
                    similarity = len(shared) / max(len(neighbors1 | neighbors2), 1)
                    
                    if similarity >= similarity_threshold:
                        self.add_edge(
                            source=node1.id,
                            target=node2.id,
                            relation="similar_to",
                            weight=similarity,
                            properties={"shared_concepts": list(shared)[:5]}
                        )
        
        logger.info(f"Knowledge graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
    
    def _extract_concepts(self, text: str) -> List[Tuple[str, int]]:
        """Extract key concepts from text."""
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}\b', text.lower())
        
        # Filter common words
        stop_words = SmartAutoTagger.STOP_WORDS
        words = [w for w in words if w not in stop_words]
        
        # Count and return top concepts
        counter = Counter(words)
        return counter.most_common(10)
    
    def get_related_documents(
        self,
        doc_id: str,
        max_depth: int = 2,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        İlişkili dökümanları bul (BFS traversal).
        
        Args:
            doc_id: Starting document ID
            max_depth: Maximum traversal depth
            max_results: Maximum results to return
        """
        if doc_id not in self.nodes:
            return []
        
        visited = {doc_id}
        queue = [(doc_id, 0)]  # (node_id, depth)
        related = []
        
        while queue and len(related) < max_results:
            current_id, depth = queue.pop(0)
            
            if depth > max_depth:
                continue
            
            # Get neighbors
            for neighbor_id in self._adjacency[current_id]:
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    
                    neighbor = self.nodes.get(neighbor_id)
                    if neighbor and neighbor.type == "document":
                        # Find the edge
                        edge = next(
                            (e for e in self.edges 
                             if (e.source == current_id and e.target == neighbor_id) or
                                (e.target == current_id and e.source == neighbor_id)),
                            None
                        )
                        
                        related.append({
                            "id": neighbor_id,
                            "label": neighbor.label,
                            "depth": depth + 1,
                            "relation": edge.relation if edge else "connected",
                            "weight": edge.weight if edge else 0.5,
                            "properties": neighbor.properties
                        })
                    
                    queue.append((neighbor_id, depth + 1))
        
        # Sort by weight (relevance)
        related.sort(key=lambda x: (-x["weight"], x["depth"]))
        
        return related[:max_results]
    
    def find_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """İki node arasındaki en kısa yolu bul."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            for neighbor_id in self._adjacency[current_id]:
                if neighbor_id == target_id:
                    return path + [neighbor_id]
                
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None  # No path found
    
    def get_communities(self) -> List[List[str]]:
        """
        Basit community detection (connected components).
        """
        visited = set()
        communities = []
        
        for node_id in self.nodes:
            if node_id not in visited:
                community = []
                queue = [node_id]
                
                while queue:
                    current = queue.pop(0)
                    if current not in visited:
                        visited.add(current)
                        community.append(current)
                        queue.extend(
                            n for n in self._adjacency[current] 
                            if n not in visited
                        )
                
                communities.append(community)
        
        # Sort by size
        communities.sort(key=len, reverse=True)
        return communities
    
    def get_central_nodes(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        En merkezi node'ları bul (degree centrality).
        """
        centrality = []
        
        for node_id, node in self.nodes.items():
            degree = len(self._adjacency[node_id])
            centrality.append({
                "id": node_id,
                "label": node.label,
                "type": node.type,
                "degree": degree,
                "weight": node.weight
            })
        
        centrality.sort(key=lambda x: x["degree"], reverse=True)
        return centrality[:top_n]
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """
        D3.js / vis.js için export.
        
        Returns:
            {
                "nodes": [...],
                "edges": [...],
                "stats": {...}
            }
        """
        nodes_export = []
        for node in self.nodes.values():
            nodes_export.append({
                "id": node.id,
                "label": node.label,
                "type": node.type,
                "weight": node.weight,
                "group": node.type,  # For coloring
                **node.properties
            })
        
        edges_export = []
        for edge in self.edges:
            edges_export.append({
                "source": edge.source,
                "target": edge.target,
                "relation": edge.relation,
                "weight": edge.weight,
                **edge.properties
            })
        
        # Calculate stats
        communities = self.get_communities()
        
        return {
            "nodes": nodes_export,
            "edges": edges_export,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "node_types": dict(Counter(n.type for n in self.nodes.values())),
                "edge_types": dict(Counter(e.relation for e in self.edges)),
                "communities": len(communities),
                "largest_community_size": len(communities[0]) if communities else 0
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Graph istatistikleri."""
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": dict(Counter(n.type for n in self.nodes.values())),
            "edge_types": dict(Counter(e.relation for e in self.edges)),
            "avg_degree": sum(len(adj) for adj in self._adjacency.values()) / max(len(self.nodes), 1),
            "density": 2 * len(self.edges) / max(len(self.nodes) * (len(self.nodes) - 1), 1)
        }


# =============================================================================
# PREMIUM FEATURES MANAGER
# =============================================================================

class PremiumFeaturesManager:
    """
    Tüm premium özellikleri yöneten ana class.
    
    10 Premium Özellik:
    1. 🏷️ Smart Auto-Tagging
    2. 📊 Real-time Analytics
    3. 🔄 Semantic Reranking
    4. 🕸️ Knowledge Graph
    5. 🧠 AI Summarization
    6. 🔍 Fuzzy Search
    7. 📈 Trend Analysis
    8. 🎯 Query Suggestions
    9. 📝 Document Comparison & Diff
    10. 🎨 Content Enhancement
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Original 4 features
        self.auto_tagger = SmartAutoTagger()
        self.analytics = RealTimeAnalytics()
        self.reranker = SemanticReranker()
        self.knowledge_graph = KnowledgeGraph()
        
        # V2 features (lazy loading)
        self._summarizer = None
        self._fuzzy_search = None
        self._trend_analyzer = None
        self._query_suggester = None
        
        # V3 features (lazy loading)
        self._document_comparator = None
        self._content_enhancer = None
        
        self._initialized = True
        logger.info("PremiumFeaturesManager initialized with all 10 features")
    
    # Lazy loading properties for V2 features
    @property
    def summarizer(self):
        if self._summarizer is None:
            from .premium_features_v2 import AISummarizer
            self._summarizer = AISummarizer()
        return self._summarizer
    
    @property
    def fuzzy_search(self):
        if self._fuzzy_search is None:
            from .premium_features_v2 import FuzzySearchEngine
            self._fuzzy_search = FuzzySearchEngine()
        return self._fuzzy_search
    
    @property
    def trend_analyzer(self):
        if self._trend_analyzer is None:
            from .premium_features_v2 import TrendAnalyzer
            self._trend_analyzer = TrendAnalyzer()
        return self._trend_analyzer
    
    @property
    def query_suggester(self):
        if self._query_suggester is None:
            from .premium_features_v2 import SmartQuerySuggester
            self._query_suggester = SmartQuerySuggester()
        return self._query_suggester
    
    # Lazy loading properties for V3 features
    @property
    def document_comparator(self):
        if self._document_comparator is None:
            from .premium_features_v3 import DocumentComparator
            self._document_comparator = DocumentComparator()
        return self._document_comparator
    
    @property
    def content_enhancer(self):
        if self._content_enhancer is None:
            from .premium_features_v3 import ContentEnhancer
            self._content_enhancer = ContentEnhancer()
        return self._content_enhancer
    
    # Original methods
    def tag_document(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Auto-tag a document."""
        return self.auto_tagger.generate_tags(content, metadata)
    
    def track_event(self, event_type: str, data: Optional[Dict] = None):
        """Track an analytics event."""
        self.analytics.track_event(event_type, data)
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data."""
        return self.analytics.get_dashboard_data()
    
    def rerank_results(
        self,
        query: str,
        documents: List[Dict],
        original_scores: Optional[List[float]] = None
    ) -> List[Dict]:
        """Rerank search results."""
        return self.reranker.rerank(query, documents, original_scores)
    
    def build_knowledge_graph(self, documents: List[Dict]):
        """Build knowledge graph from documents."""
        self.knowledge_graph.build_from_documents(documents)
    
    def get_related_documents(self, doc_id: str) -> List[Dict]:
        """Get related documents from knowledge graph."""
        return self.knowledge_graph.get_related_documents(doc_id)
    
    def export_graph(self) -> Dict[str, Any]:
        """Export knowledge graph for visualization."""
        return self.knowledge_graph.export_for_visualization()
    
    # New feature methods
    def summarize(self, text: str, format: str = "paragraph") -> Dict[str, Any]:
        """Summarize text."""
        return self.summarizer.summarize(text, format=format)
    
    def summarize_multiple(self, texts: List[str]) -> Dict[str, Any]:
        """Summarize multiple documents."""
        return self.summarizer.summarize_multiple(texts)
    
    def fuzzy_find(self, query: str, candidates: List[str]) -> List[Tuple[str, float]]:
        """Fuzzy search in candidates."""
        return self.fuzzy_search.find_similar(query, candidates)
    
    def correct_spelling(self, text: str) -> Dict[str, Any]:
        """Correct spelling in text."""
        return self.fuzzy_search.correct_text(text)
    
    def did_you_mean(self, query: str) -> Optional[str]:
        """Get 'did you mean' suggestion."""
        return self.fuzzy_search.did_you_mean(query)
    
    def record_trend_metric(self, name: str, value: float):
        """Record metric for trend analysis."""
        self.trend_analyzer.record_metric(name, value)
    
    def get_trend_insights(self) -> Dict[str, Any]:
        """Get trend insights."""
        return self.trend_analyzer.get_insights()
    
    def analyze_trend(self, metric_name: str) -> Dict[str, Any]:
        """Analyze specific metric trend."""
        return self.trend_analyzer.analyze_metric(metric_name)
    
    def suggest_queries(self, partial_query: str) -> Dict[str, Any]:
        """Get query suggestions."""
        return self.query_suggester.suggest(partial_query)
    
    def record_query(self, query: str, success: bool = True):
        """Record query for suggestions."""
        self.query_suggester.record_query(query, success)
    
    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        """Get popular queries."""
        return self.query_suggester.get_popular_queries(limit)
    
    # V3 feature methods - Document Comparison
    def compare_documents(
        self, 
        text1: str, 
        text2: str, 
        diff_type: str = "lines"
    ) -> Dict[str, Any]:
        """Compare two documents."""
        if diff_type == "lines":
            return self.document_comparator.line_diff(text1, text2)
        elif diff_type == "words":
            return self.document_comparator.word_diff(text1, text2)
        elif diff_type == "semantic":
            return self.document_comparator.semantic_diff(text1, text2)
        else:
            return self.document_comparator.line_diff(text1, text2)
    
    def get_similarity_score(self, text1: str, text2: str) -> Dict[str, Any]:
        """Get similarity score between two texts."""
        return self.document_comparator.similarity_score(text1, text2)
    
    def get_side_by_side_diff(
        self, 
        text1: str, 
        text2: str,
        label1: str = "Original",
        label2: str = "Modified"
    ) -> Dict[str, Any]:
        """Get side-by-side diff visualization."""
        return self.document_comparator.side_by_side(text1, text2, label1, label2)
    
    def compare_versions(self, versions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple versions of a document."""
        return self.document_comparator.version_diff(versions)
    
    # V3 feature methods - Content Enhancement
    def enhance_content(self, text: str) -> Dict[str, Any]:
        """Enhance content with all features."""
        return self.content_enhancer.enhance_content(text)
    
    def fix_markdown(self, text: str) -> Dict[str, Any]:
        """Fix markdown formatting."""
        return self.content_enhancer.fix_markdown(text)
    
    def detect_code_language(self, code: str) -> Dict[str, Any]:
        """Detect code language."""
        return self.content_enhancer.detect_code_language(code)
    
    def extract_tables(self, text: str) -> Dict[str, Any]:
        """Extract tables from text."""
        return self.content_enhancer.extract_tables(text)
    
    def extract_links(self, text: str) -> Dict[str, Any]:
        """Extract and enrich links."""
        return self.content_enhancer.extract_links(text)
    
    def extract_images(self, text: str) -> Dict[str, Any]:
        """Extract image URLs."""
        return self.content_enhancer.extract_images(text)
    
    def auto_format(self, text: str) -> Dict[str, Any]:
        """Auto-format content."""
        return self.content_enhancer.auto_format(text)


# Singleton instance
def get_premium_features() -> PremiumFeaturesManager:
    """Premium features manager singleton."""
    return PremiumFeaturesManager()
