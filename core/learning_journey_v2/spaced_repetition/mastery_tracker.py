"""
📊 Mastery Tracker

Konu bazlı hakimiyet takip sistemi.
SM-2 algoritması ile entegre çalışarak
öğrenci ilerlemesini detaylı takip eder.

Özellikler:
- Topic-level mastery tracking
- Package ve Stage level aggregation
- XP ve Level sistemi
- Achievement entegrasyonu
- Progress visualization data
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json

from .sm2_algorithm import SM2Algorithm, ReviewItem, sm2


class MasteryLevel(Enum):
    """Hakimiyet seviyeleri"""
    NOVICE = "novice"           # 0-25%
    LEARNING = "learning"       # 25-50%
    DEVELOPING = "developing"   # 50-75%
    PROFICIENT = "proficient"   # 75-90%
    MASTERED = "mastered"       # 90-100%
    
    @classmethod
    def from_score(cls, score: float) -> "MasteryLevel":
        if score >= 0.9:
            return cls.MASTERED
        elif score >= 0.75:
            return cls.PROFICIENT
        elif score >= 0.5:
            return cls.DEVELOPING
        elif score >= 0.25:
            return cls.LEARNING
        else:
            return cls.NOVICE


@dataclass
class TopicMastery:
    """Konu hakimiyet verisi"""
    topic_id: str
    topic_name: str
    package_id: str
    stage_id: str
    
    # Hakimiyet metrikleri
    mastery_score: float = 0.0       # 0.0-1.0
    mastery_level: MasteryLevel = MasteryLevel.NOVICE
    confidence: float = 0.0          # 0.0-1.0 (ne kadar emin olduğumuz)
    
    # Performans verileri
    total_attempts: int = 0
    correct_attempts: int = 0
    last_score: float = 0.0
    best_score: float = 0.0
    average_score: float = 0.0
    
    # Zaman verileri
    first_attempt: Optional[datetime] = None
    last_attempt: Optional[datetime] = None
    total_study_minutes: int = 0
    
    # SM-2 bağlantısı
    review_items: List[str] = field(default_factory=list)  # ReviewItem IDs
    
    # XP
    xp_earned: int = 0
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class PackageMastery:
    """Paket hakimiyet verisi"""
    package_id: str
    package_name: str
    stage_id: str
    
    # Aggregated scores
    mastery_score: float = 0.0
    mastery_level: MasteryLevel = MasteryLevel.NOVICE
    
    # Topic breakdown
    topic_masteries: Dict[str, float] = field(default_factory=dict)
    topics_mastered: int = 0
    total_topics: int = 0
    
    # Exam sonuçları
    exam_score: Optional[float] = None
    exam_passed: bool = False
    exam_attempts: int = 0
    
    # XP
    xp_earned: int = 0
    
    # Unlocked
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None


@dataclass
class StageMastery:
    """Aşama hakimiyet verisi"""
    stage_id: str
    stage_name: str
    stage_number: int
    
    # Aggregated scores
    mastery_score: float = 0.0
    mastery_level: MasteryLevel = MasteryLevel.NOVICE
    
    # Package breakdown
    package_masteries: Dict[str, float] = field(default_factory=dict)
    packages_completed: int = 0
    total_packages: int = 0
    
    # Stage closure
    closure_exam_score: Optional[float] = None
    closure_passed: bool = False
    closure_attempts: int = 0
    
    # XP
    xp_earned: int = 0
    
    # Unlocked
    is_unlocked: bool = False
    unlocked_at: Optional[datetime] = None


class MasteryTracker:
    """
    Konu Hakimiyet Takip Sistemi
    
    Topic, Package ve Stage seviyelerinde
    hakimiyet skorlarını takip eder.
    """
    
    # XP Değerleri
    XP_CORRECT_ANSWER = 10
    XP_PERFECT_SCORE = 50
    XP_PACKAGE_COMPLETE = 100
    XP_STAGE_COMPLETE = 250
    XP_MASTERY_ACHIEVED = 200
    
    # Unlocking thresholds
    PACKAGE_UNLOCK_SCORE = 0.7   # %70 önceki paketten
    STAGE_UNLOCK_SCORE = 0.75   # %75 önceki aşamadan
    
    def __init__(self, sm2_algorithm: SM2Algorithm = None):
        self.sm2 = sm2_algorithm or sm2
        
        # Storage
        self.topic_masteries: Dict[str, TopicMastery] = {}
        self.package_masteries: Dict[str, PackageMastery] = {}
        self.stage_masteries: Dict[str, StageMastery] = {}
        self.review_items: Dict[str, ReviewItem] = {}
        
        # User progress
        self.total_xp: int = 0
        self.current_level: int = 1
        self.achievements: List[str] = []
    
    def record_topic_attempt(
        self,
        topic_id: str,
        score: float,
        duration_minutes: int = 5,
        question_results: List[Dict] = None
    ) -> Tuple[TopicMastery, int]:
        """
        Konu denemesi kaydet
        
        Args:
            topic_id: Konu ID
            score: 0.0-1.0 arası skor
            duration_minutes: Çalışma süresi
            question_results: Soru bazlı sonuçlar
        
        Returns:
            (updated TopicMastery, xp_earned)
        """
        # Topic mastery al veya oluştur
        if topic_id not in self.topic_masteries:
            self.topic_masteries[topic_id] = TopicMastery(
                topic_id=topic_id,
                topic_name=topic_id,  # Gerçek isim sonra güncellenir
                package_id="",
                stage_id=""
            )
        
        topic = self.topic_masteries[topic_id]
        now = datetime.now()
        
        # İstatistikleri güncelle
        topic.total_attempts += 1
        topic.correct_attempts += 1 if score >= 0.7 else 0
        topic.last_score = score
        topic.best_score = max(topic.best_score, score)
        
        # Ortalama hesapla
        total_score = topic.average_score * (topic.total_attempts - 1) + score
        topic.average_score = total_score / topic.total_attempts
        
        # Zaman güncelle
        if topic.first_attempt is None:
            topic.first_attempt = now
        topic.last_attempt = now
        topic.total_study_minutes += duration_minutes
        
        # Mastery score hesapla
        topic.mastery_score = self._calculate_mastery_score(topic)
        topic.mastery_level = MasteryLevel.from_score(topic.mastery_score)
        
        # Confidence hesapla
        topic.confidence = min(1.0, topic.total_attempts / 5)
        
        # XP hesapla
        xp = self._calculate_xp(score, topic)
        topic.xp_earned += xp
        self.total_xp += xp
        
        # Level güncelle
        self._update_level()
        
        topic.updated_at = now
        
        # SM-2 review items güncelle
        if question_results:
            self._update_review_items(topic_id, question_results)
        
        return topic, xp
    
    def record_package_exam(
        self,
        package_id: str,
        score: float,
        questions: List[Dict] = None
    ) -> Tuple[PackageMastery, int, bool]:
        """
        Paket sınavı kaydet
        
        Returns:
            (PackageMastery, xp_earned, next_unlocked)
        """
        if package_id not in self.package_masteries:
            self.package_masteries[package_id] = PackageMastery(
                package_id=package_id,
                package_name=package_id,
                stage_id=""
            )
        
        package = self.package_masteries[package_id]
        
        package.exam_attempts += 1
        package.exam_score = score
        package.exam_passed = score >= 0.7
        
        # XP
        xp = 0
        if package.exam_passed:
            xp = self.XP_PACKAGE_COMPLETE
            if score >= 0.95:
                xp += self.XP_PERFECT_SCORE
        
        package.xp_earned += xp
        self.total_xp += xp
        self._update_level()
        
        # Aggregated mastery güncelle
        self._update_package_mastery(package_id)
        
        # Sonraki paketi aç
        next_unlocked = package.exam_passed and score >= self.PACKAGE_UNLOCK_SCORE
        
        return package, xp, next_unlocked
    
    def record_stage_closure(
        self,
        stage_id: str,
        score: float,
        weakness_results: Dict[str, float] = None
    ) -> Tuple[StageMastery, int, bool]:
        """
        Aşama kapanış sınavı kaydet
        
        Returns:
            (StageMastery, xp_earned, next_stage_unlocked)
        """
        if stage_id not in self.stage_masteries:
            self.stage_masteries[stage_id] = StageMastery(
                stage_id=stage_id,
                stage_name=stage_id,
                stage_number=1
            )
        
        stage = self.stage_masteries[stage_id]
        
        stage.closure_attempts += 1
        stage.closure_exam_score = score
        stage.closure_passed = score >= 0.75
        
        # XP
        xp = 0
        if stage.closure_passed:
            xp = self.XP_STAGE_COMPLETE
            if score >= 0.95:
                xp += self.XP_PERFECT_SCORE * 2
        
        stage.xp_earned += xp
        self.total_xp += xp
        self._update_level()
        
        # Aggregated mastery güncelle
        self._update_stage_mastery(stage_id)
        
        # Sonraki aşamayı aç
        next_unlocked = stage.closure_passed and score >= self.STAGE_UNLOCK_SCORE
        
        return stage, xp, next_unlocked
    
    def _calculate_mastery_score(self, topic: TopicMastery) -> float:
        """Topic için mastery score hesapla"""
        if topic.total_attempts == 0:
            return 0.0
        
        # Faktörler
        accuracy = topic.correct_attempts / topic.total_attempts
        avg_score = topic.average_score
        recency = self._calculate_recency_factor(topic.last_attempt)
        repetition = min(1.0, topic.total_attempts / 10)  # 10 deneme = tam tekrar
        
        # Review item'lardan retention al
        retention = self._get_average_retention(topic.review_items)
        
        # Ağırlıklı skor
        mastery = (
            accuracy * 0.25 +
            avg_score * 0.25 +
            recency * 0.15 +
            repetition * 0.15 +
            retention * 0.20
        )
        
        return min(1.0, max(0.0, mastery))
    
    def _calculate_recency_factor(
        self, 
        last_attempt: Optional[datetime]
    ) -> float:
        """Yakınlık faktörü (son 7 gün = 1.0, 30+ gün = 0.3)"""
        if last_attempt is None:
            return 0.0
        
        days_ago = (datetime.now() - last_attempt).days
        
        if days_ago <= 7:
            return 1.0
        elif days_ago <= 14:
            return 0.8
        elif days_ago <= 30:
            return 0.5
        else:
            return 0.3
    
    def _get_average_retention(self, review_item_ids: List[str]) -> float:
        """Review item'lardan ortalama retention al"""
        if not review_item_ids:
            return 0.5  # Default
        
        retentions = []
        for item_id in review_item_ids:
            if item_id in self.review_items:
                ret = self.sm2.calculate_retention_rate(self.review_items[item_id])
                retentions.append(ret)
        
        return sum(retentions) / len(retentions) if retentions else 0.5
    
    def _calculate_xp(self, score: float, topic: TopicMastery) -> int:
        """XP hesapla"""
        base_xp = int(score * self.XP_CORRECT_ANSWER)
        
        # Perfect bonus
        if score >= 0.95:
            base_xp += self.XP_PERFECT_SCORE
        
        # First time mastery bonus
        old_level = MasteryLevel.from_score(
            topic.mastery_score - 0.1  # Önceki tahmini
        )
        new_level = MasteryLevel.from_score(topic.mastery_score)
        
        if new_level == MasteryLevel.MASTERED and old_level != MasteryLevel.MASTERED:
            base_xp += self.XP_MASTERY_ACHIEVED
        
        return base_xp
    
    def _update_level(self):
        """Seviye güncelle"""
        # Her 1000 XP = 1 level
        self.current_level = 1 + (self.total_xp // 1000)
    
    def _update_review_items(
        self, 
        topic_id: str, 
        question_results: List[Dict]
    ):
        """SM-2 review items güncelle"""
        topic = self.topic_masteries.get(topic_id)
        if not topic:
            return
        
        for result in question_results:
            item_id = result.get("question_id", f"{topic_id}_{len(topic.review_items)}")
            quality = self._score_to_quality(result.get("score", 0))
            
            if item_id in self.review_items:
                # Mevcut item güncelle
                item = self.review_items[item_id]
                self.sm2.calculate_next_review(item, quality)
            else:
                # Yeni item oluştur
                item = ReviewItem(
                    item_id=item_id,
                    topic_id=topic_id,
                    package_id=topic.package_id,
                    stage_id=topic.stage_id,
                    item_type="question"
                )
                self.sm2.calculate_next_review(item, quality)
                self.review_items[item_id] = item
                topic.review_items.append(item_id)
    
    def _score_to_quality(self, score: float) -> int:
        """Score'u SM-2 quality'ye çevir (0-5)"""
        if score >= 0.9:
            return 5
        elif score >= 0.7:
            return 4
        elif score >= 0.5:
            return 3
        elif score >= 0.3:
            return 2
        elif score > 0:
            return 1
        else:
            return 0
    
    def _update_package_mastery(self, package_id: str):
        """Package mastery skorunu güncelle"""
        package = self.package_masteries.get(package_id)
        if not package:
            return
        
        # Package'a ait topic'leri bul
        topic_scores = []
        for topic_id, topic in self.topic_masteries.items():
            if topic.package_id == package_id:
                topic_scores.append(topic.mastery_score)
                package.topic_masteries[topic_id] = topic.mastery_score
        
        if topic_scores:
            package.mastery_score = sum(topic_scores) / len(topic_scores)
            package.mastery_level = MasteryLevel.from_score(package.mastery_score)
            package.total_topics = len(topic_scores)
            package.topics_mastered = sum(1 for s in topic_scores if s >= 0.9)
    
    def _update_stage_mastery(self, stage_id: str):
        """Stage mastery skorunu güncelle"""
        stage = self.stage_masteries.get(stage_id)
        if not stage:
            return
        
        # Stage'e ait package'ları bul
        package_scores = []
        for package_id, package in self.package_masteries.items():
            if package.stage_id == stage_id:
                package_scores.append(package.mastery_score)
                stage.package_masteries[package_id] = package.mastery_score
        
        if package_scores:
            stage.mastery_score = sum(package_scores) / len(package_scores)
            stage.mastery_level = MasteryLevel.from_score(stage.mastery_score)
            stage.total_packages = len(package_scores)
            stage.packages_completed = sum(1 for s in package_scores if s >= 0.7)
    
    def get_due_reviews(
        self, 
        user_id: str = "",
        max_items: int = 20
    ) -> List[ReviewItem]:
        """Bugün tekrar edilecek öğeleri getir"""
        all_items = list(self.review_items.values())
        return self.sm2.get_due_items(all_items, max_items)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Genel ilerleme özeti"""
        total_topics = len(self.topic_masteries)
        mastered_topics = sum(
            1 for t in self.topic_masteries.values()
            if t.mastery_level == MasteryLevel.MASTERED
        )
        
        total_packages = len(self.package_masteries)
        completed_packages = sum(
            1 for p in self.package_masteries.values()
            if p.exam_passed
        )
        
        total_stages = len(self.stage_masteries)
        completed_stages = sum(
            1 for s in self.stage_masteries.values()
            if s.closure_passed
        )
        
        # SM-2 stats
        sm2_stats = self.sm2.get_study_stats(list(self.review_items.values()))
        
        return {
            "user": {
                "total_xp": self.total_xp,
                "level": self.current_level,
                "next_level_xp": (self.current_level * 1000) - self.total_xp
            },
            "topics": {
                "total": total_topics,
                "mastered": mastered_topics,
                "percentage": (mastered_topics / max(total_topics, 1)) * 100
            },
            "packages": {
                "total": total_packages,
                "completed": completed_packages,
                "percentage": (completed_packages / max(total_packages, 1)) * 100
            },
            "stages": {
                "total": total_stages,
                "completed": completed_stages,
                "percentage": (completed_stages / max(total_stages, 1)) * 100
            },
            "spaced_repetition": sm2_stats,
            "achievements": self.achievements
        }
    
    def get_weakness_areas(self, threshold: float = 0.6) -> List[Dict]:
        """Zayıf alanları bul"""
        weak_topics = []
        
        for topic_id, topic in self.topic_masteries.items():
            if topic.mastery_score < threshold:
                weak_topics.append({
                    "topic_id": topic_id,
                    "topic_name": topic.topic_name,
                    "mastery_score": topic.mastery_score,
                    "attempts": topic.total_attempts,
                    "last_attempt": topic.last_attempt.isoformat() if topic.last_attempt else None,
                    "suggested_review": True
                })
        
        # En zayıftan güçlüye sırala
        weak_topics.sort(key=lambda x: x["mastery_score"])
        
        return weak_topics


# Singleton instance
mastery_tracker = MasteryTracker()
