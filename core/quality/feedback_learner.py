"""
📊 Feedback Learning System
============================

Kullanıcı geri bildirimlerinden öğrenme ve adaptasyon.

Features:
- Feedback collection and analysis
- Pattern recognition
- Preference learning
- Quality improvement suggestions
- A/B testing support
"""

import logging
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Geri bildirim türleri."""
    EXPLICIT_POSITIVE = "positive"  # Thumbs up
    EXPLICIT_NEGATIVE = "negative"  # Thumbs down
    IMPLICIT_ACCEPT = "accept"  # Yanıtı kullandı
    IMPLICIT_REJECT = "reject"  # Yeniden sordu
    CORRECTION = "correction"  # Düzeltme yaptı
    EDIT = "edit"  # Yanıtı düzenledi
    REGENERATE = "regenerate"  # Yeniden oluştur istedi


class FeedbackDimension(Enum):
    """Geri bildirim boyutları."""
    ACCURACY = "accuracy"  # Doğruluk
    RELEVANCE = "relevance"  # İlgililik
    COMPLETENESS = "completeness"  # Bütünlük
    CLARITY = "clarity"  # Netlik
    HELPFULNESS = "helpfulness"  # Yardımcılık
    FORMATTING = "formatting"  # Biçimlendirme
    TONE = "tone"  # Ton/üslup


@dataclass
class Feedback:
    """Tek bir geri bildirim kaydı."""
    id: str
    timestamp: datetime
    query: str
    response: str
    feedback_type: FeedbackType
    dimensions: Dict[str, float] = field(default_factory=dict)
    comment: Optional[str] = None
    correction: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackStats:
    """Geri bildirim istatistikleri."""
    total_count: int
    positive_rate: float
    negative_rate: float
    average_by_dimension: Dict[str, float]
    common_issues: List[Tuple[str, int]]
    improvement_suggestions: List[str]


@dataclass
class LearningInsight:
    """Öğrenme çıkarımı."""
    insight_type: str
    description: str
    confidence: float
    supporting_evidence: int
    actionable_suggestion: str


class FeedbackStore:
    """
    Geri bildirim depolama ve sorgulama.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self.feedbacks: List[Feedback] = []
        self.query_feedback_map: Dict[str, List[str]] = defaultdict(list)
        
        # Load existing if storage path provided
        if self.storage_path and self.storage_path.exists():
            self._load_feedbacks()
    
    def add(self, feedback: Feedback) -> str:
        """Geri bildirim ekle."""
        self.feedbacks.append(feedback)
        
        # Query hash ile indexle
        query_hash = self._hash_query(feedback.query)
        self.query_feedback_map[query_hash].append(feedback.id)
        
        # Persist if storage configured
        if self.storage_path:
            self._save_feedback(feedback)
        
        logger.info(f"Feedback added: {feedback.id} ({feedback.feedback_type.value})")
        return feedback.id
    
    def get_by_query(self, query: str) -> List[Feedback]:
        """Sorguya göre geri bildirimleri al."""
        query_hash = self._hash_query(query)
        feedback_ids = self.query_feedback_map.get(query_hash, [])
        return [f for f in self.feedbacks if f.id in feedback_ids]
    
    def get_recent(self, limit: int = 100) -> List[Feedback]:
        """Son geri bildirimleri al."""
        sorted_feedbacks = sorted(
            self.feedbacks,
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_feedbacks[:limit]
    
    def get_by_type(self, feedback_type: FeedbackType) -> List[Feedback]:
        """Türe göre geri bildirimleri al."""
        return [f for f in self.feedbacks if f.feedback_type == feedback_type]
    
    def _hash_query(self, query: str) -> str:
        """Query için hash oluştur."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _save_feedback(self, feedback: Feedback):
        """Feedback'i dosyaya kaydet."""
        if not self.storage_path:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        filepath = self.storage_path / f"{feedback.id}.json"
        
        data = {
            "id": feedback.id,
            "timestamp": feedback.timestamp.isoformat(),
            "query": feedback.query,
            "response": feedback.response[:500],  # Truncate
            "feedback_type": feedback.feedback_type.value,
            "dimensions": feedback.dimensions,
            "comment": feedback.comment,
            "correction": feedback.correction,
            "user_id": feedback.user_id,
            "session_id": feedback.session_id,
            "metadata": feedback.metadata
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_feedbacks(self):
        """Mevcut feedback'leri yükle."""
        if not self.storage_path:
            return
        
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                feedback = Feedback(
                    id=data["id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    query=data["query"],
                    response=data["response"],
                    feedback_type=FeedbackType(data["feedback_type"]),
                    dimensions=data.get("dimensions", {}),
                    comment=data.get("comment"),
                    correction=data.get("correction"),
                    user_id=data.get("user_id"),
                    session_id=data.get("session_id"),
                    metadata=data.get("metadata", {})
                )
                self.feedbacks.append(feedback)
                
                query_hash = self._hash_query(feedback.query)
                self.query_feedback_map[query_hash].append(feedback.id)
                
            except Exception as e:
                logger.error(f"Error loading feedback {filepath}: {e}")


class FeedbackAnalyzer:
    """
    Geri bildirim analizi ve pattern tespiti.
    """
    
    def __init__(self, store: FeedbackStore):
        self.store = store
    
    def get_stats(
        self,
        since: Optional[datetime] = None
    ) -> FeedbackStats:
        """Genel istatistikleri hesapla."""
        feedbacks = self.store.feedbacks
        
        if since:
            feedbacks = [f for f in feedbacks if f.timestamp >= since]
        
        if not feedbacks:
            return FeedbackStats(
                total_count=0,
                positive_rate=0.0,
                negative_rate=0.0,
                average_by_dimension={},
                common_issues=[],
                improvement_suggestions=[]
            )
        
        total = len(feedbacks)
        positive = sum(
            1 for f in feedbacks
            if f.feedback_type in [FeedbackType.EXPLICIT_POSITIVE, FeedbackType.IMPLICIT_ACCEPT]
        )
        negative = sum(
            1 for f in feedbacks
            if f.feedback_type in [FeedbackType.EXPLICIT_NEGATIVE, FeedbackType.IMPLICIT_REJECT]
        )
        
        # Dimension averages
        dimension_sums = defaultdict(list)
        for f in feedbacks:
            for dim, score in f.dimensions.items():
                dimension_sums[dim].append(score)
        
        dimension_avgs = {
            dim: sum(scores) / len(scores)
            for dim, scores in dimension_sums.items()
        }
        
        # Common issues
        issues = self._extract_common_issues(feedbacks)
        
        # Suggestions
        suggestions = self._generate_suggestions(
            positive / total if total > 0 else 0,
            dimension_avgs,
            issues
        )
        
        return FeedbackStats(
            total_count=total,
            positive_rate=positive / total if total > 0 else 0,
            negative_rate=negative / total if total > 0 else 0,
            average_by_dimension=dimension_avgs,
            common_issues=issues[:5],
            improvement_suggestions=suggestions
        )
    
    def find_patterns(
        self,
        min_occurrences: int = 3
    ) -> List[LearningInsight]:
        """Pattern tespiti yap."""
        insights = []
        
        # 1. Negative feedback patterns
        negative = self.store.get_by_type(FeedbackType.EXPLICIT_NEGATIVE)
        negative.extend(self.store.get_by_type(FeedbackType.IMPLICIT_REJECT))
        
        if len(negative) >= min_occurrences:
            # Query patterns
            query_words = defaultdict(int)
            for f in negative:
                for word in f.query.lower().split():
                    if len(word) > 3:  # Skip short words
                        query_words[word] += 1
            
            common_words = [
                (word, count) for word, count in query_words.items()
                if count >= min_occurrences
            ]
            
            if common_words:
                top_word = max(common_words, key=lambda x: x[1])
                insights.append(LearningInsight(
                    insight_type="negative_pattern",
                    description=f"Queries containing '{top_word[0]}' often receive negative feedback",
                    confidence=min(top_word[1] / len(negative), 1.0),
                    supporting_evidence=top_word[1],
                    actionable_suggestion=f"Improve handling of queries about '{top_word[0]}'"
                ))
        
        # 2. Dimension patterns
        dimension_issues = self._find_dimension_patterns()
        insights.extend(dimension_issues)
        
        # 3. Correction patterns
        corrections = self.store.get_by_type(FeedbackType.CORRECTION)
        if len(corrections) >= min_occurrences:
            insights.append(LearningInsight(
                insight_type="correction_frequency",
                description=f"Users frequently correct responses ({len(corrections)} times)",
                confidence=0.8,
                supporting_evidence=len(corrections),
                actionable_suggestion="Review correction patterns to improve accuracy"
            ))
        
        return insights
    
    def _extract_common_issues(
        self,
        feedbacks: List[Feedback]
    ) -> List[Tuple[str, int]]:
        """Yaygın sorunları çıkar."""
        issues = defaultdict(int)
        
        for f in feedbacks:
            if f.feedback_type in [FeedbackType.EXPLICIT_NEGATIVE, FeedbackType.IMPLICIT_REJECT]:
                if f.comment:
                    # Extract key phrases from comments
                    words = f.comment.lower().split()
                    for i, word in enumerate(words):
                        if word in ["wrong", "incorrect", "yanlış", "hatalı"]:
                            issues["accuracy_issues"] += 1
                        elif word in ["unclear", "confusing", "anlaşılmaz"]:
                            issues["clarity_issues"] += 1
                        elif word in ["incomplete", "eksik", "yetersiz"]:
                            issues["completeness_issues"] += 1
                
                # Dimension-based issues
                for dim, score in f.dimensions.items():
                    if score < 0.5:
                        issues[f"low_{dim}"] += 1
        
        return sorted(issues.items(), key=lambda x: x[1], reverse=True)
    
    def _find_dimension_patterns(self) -> List[LearningInsight]:
        """Dimension pattern analizi."""
        insights = []
        
        dimension_scores = defaultdict(list)
        for f in self.store.feedbacks:
            for dim, score in f.dimensions.items():
                dimension_scores[dim].append(score)
        
        for dim, scores in dimension_scores.items():
            if len(scores) >= 5:
                avg = sum(scores) / len(scores)
                if avg < 0.5:
                    insights.append(LearningInsight(
                        insight_type="low_dimension",
                        description=f"{dim} consistently scores low (avg: {avg:.2f})",
                        confidence=0.7,
                        supporting_evidence=len(scores),
                        actionable_suggestion=f"Focus on improving {dim} in responses"
                    ))
        
        return insights
    
    def _generate_suggestions(
        self,
        positive_rate: float,
        dimension_avgs: Dict[str, float],
        issues: List[Tuple[str, int]]
    ) -> List[str]:
        """Öneriler oluştur."""
        suggestions = []
        
        if positive_rate < 0.5:
            suggestions.append("Critical: Overall satisfaction is low, review response quality")
        
        for dim, avg in dimension_avgs.items():
            if avg < 0.5:
                suggestions.append(f"Improve {dim}: current average is {avg:.2f}")
        
        if issues:
            top_issue = issues[0]
            suggestions.append(f"Address most common issue: {top_issue[0]} ({top_issue[1]} occurrences)")
        
        if not suggestions:
            suggestions.append("Performance is good, continue monitoring feedback")
        
        return suggestions


class FeedbackLearner:
    """
    Ana feedback learning sistemi.
    
    Geri bildirimlerden öğrenir ve sistem parametrelerini optimize eder.
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None
    ):
        self.store = FeedbackStore(storage_path)
        self.analyzer = FeedbackAnalyzer(self.store)
        
        # Learned preferences
        self.preferences: Dict[str, Any] = {
            "preferred_length": "medium",  # short, medium, long
            "preferred_style": "professional",  # casual, professional, technical
            "preferred_detail": "detailed",  # brief, detailed, comprehensive
        }
        
        # Quality adjustments based on feedback
        self.quality_adjustments: Dict[str, float] = {
            "temperature": 0.0,  # Adjustment to temperature
            "max_tokens": 0,  # Adjustment to max tokens
            "context_chunks": 0,  # Adjustment to context count
        }
    
    def record_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        dimensions: Optional[Dict[str, float]] = None,
        comment: Optional[str] = None,
        correction: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Geri bildirim kaydet."""
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(query.encode()).hexdigest()[:8]}"
        
        feedback = Feedback(
            id=feedback_id,
            timestamp=datetime.now(),
            query=query,
            response=response,
            feedback_type=feedback_type,
            dimensions=dimensions or {},
            comment=comment,
            correction=correction,
            user_id=user_id,
            session_id=session_id
        )
        
        self.store.add(feedback)
        
        # Learn from feedback
        self._learn_from_feedback(feedback)
        
        return feedback_id
    
    def get_recommendations(
        self,
        query: str
    ) -> Dict[str, Any]:
        """
        Sorgu için öğrenilmiş önerileri al.
        
        Geçmiş geri bildirimlerden öğrenilen parametreleri döndürür.
        """
        # Similar query feedback
        similar_feedbacks = self.store.get_by_query(query)
        
        recommendations = {
            "preferences": self.preferences.copy(),
            "adjustments": self.quality_adjustments.copy(),
            "warnings": []
        }
        
        if similar_feedbacks:
            negative_count = sum(
                1 for f in similar_feedbacks
                if f.feedback_type in [FeedbackType.EXPLICIT_NEGATIVE, FeedbackType.IMPLICIT_REJECT]
            )
            
            if negative_count > len(similar_feedbacks) / 2:
                recommendations["warnings"].append(
                    "Similar queries received negative feedback - be extra careful"
                )
        
        return recommendations
    
    def get_insights(self) -> Dict[str, Any]:
        """Tüm öğrenme çıkarımlarını al."""
        stats = self.analyzer.get_stats()
        patterns = self.analyzer.find_patterns()
        
        return {
            "stats": {
                "total_feedbacks": stats.total_count,
                "positive_rate": stats.positive_rate,
                "negative_rate": stats.negative_rate,
                "dimension_scores": stats.average_by_dimension
            },
            "patterns": [
                {
                    "type": p.insight_type,
                    "description": p.description,
                    "confidence": p.confidence,
                    "suggestion": p.actionable_suggestion
                }
                for p in patterns
            ],
            "common_issues": stats.common_issues,
            "suggestions": stats.improvement_suggestions,
            "current_preferences": self.preferences,
            "current_adjustments": self.quality_adjustments
        }
    
    def _learn_from_feedback(self, feedback: Feedback):
        """Tek bir feedback'ten öğren."""
        # Positive feedback -> reinforce
        if feedback.feedback_type in [FeedbackType.EXPLICIT_POSITIVE, FeedbackType.IMPLICIT_ACCEPT]:
            # Response length preference
            response_length = len(feedback.response.split())
            if response_length < 50:
                self._adjust_preference("preferred_length", "short", 0.1)
            elif response_length > 200:
                self._adjust_preference("preferred_length", "long", 0.1)
            else:
                self._adjust_preference("preferred_length", "medium", 0.1)
        
        # Negative feedback -> adjust
        elif feedback.feedback_type in [FeedbackType.EXPLICIT_NEGATIVE, FeedbackType.IMPLICIT_REJECT]:
            # Temperature adjustment
            self.quality_adjustments["temperature"] += 0.05
            
            # Dimension-based learning
            for dim, score in feedback.dimensions.items():
                if score < 0.5:
                    if dim == FeedbackDimension.COMPLETENESS.value:
                        self.quality_adjustments["max_tokens"] += 50
                        self.quality_adjustments["context_chunks"] += 1
                    elif dim == FeedbackDimension.ACCURACY.value:
                        self.quality_adjustments["temperature"] -= 0.1
        
        # Correction -> specific learning
        elif feedback.feedback_type == FeedbackType.CORRECTION and feedback.correction:
            # Could implement more sophisticated learning here
            self.quality_adjustments["temperature"] -= 0.05
        
        # Clamp adjustments
        self.quality_adjustments["temperature"] = max(-0.3, min(0.3, self.quality_adjustments["temperature"]))
        self.quality_adjustments["max_tokens"] = max(-200, min(500, self.quality_adjustments["max_tokens"]))
        self.quality_adjustments["context_chunks"] = max(-2, min(5, self.quality_adjustments["context_chunks"]))
    
    def _adjust_preference(self, key: str, value: str, weight: float):
        """Preference'ı ayarla (momentum-based)."""
        # Simple: just set if high weight
        if weight > 0.05:
            self.preferences[key] = value


# Singleton instance
feedback_learner = FeedbackLearner()
