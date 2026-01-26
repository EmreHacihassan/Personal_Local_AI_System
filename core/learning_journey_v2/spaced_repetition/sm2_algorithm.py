"""
🧠 SM-2 Spaced Repetition Algorithm

SuperMemo 2 algoritmasının geliştirilmiş implementasyonu.
Öğrenme yolculuğunda konu hakimiyetini takip eder ve
optimal tekrar zamanlamalarını hesaplar.

Özellikler:
- Klasik SM-2 formülü
- Ease factor dinamik ayarlama
- Minimum/maximum interval limitleri
- Topic-aware scheduling
- Weakness integration
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math


class ReviewQuality(Enum):
    """Geri bildirim kalitesi (0-5 arası)"""
    COMPLETE_BLACKOUT = 0  # Hiç hatırlanmadı
    INCORRECT = 1          # Yanlış cevap
    INCORRECT_EASY = 2     # Yanlış ama kolay hatırlandı
    CORRECT_DIFFICULT = 3  # Doğru ama zor hatırlandı
    CORRECT_HESITANT = 4   # Doğru ama tereddütlü
    PERFECT = 5            # Mükemmel hatırlandı


@dataclass
class ReviewItem:
    """Tekrar edilecek öğe"""
    item_id: str
    topic_id: str
    package_id: str
    stage_id: str
    item_type: str  # concept, question, skill
    
    # SM-2 parametreleri
    ease_factor: float = 2.5  # Kolaylık faktörü (1.3 - 3.0)
    interval: int = 0         # Gün cinsinden interval
    repetition: int = 0       # Tekrar sayısı
    
    # Zamanlar
    next_review: Optional[datetime] = None
    last_review: Optional[datetime] = None
    
    # İstatistikler
    total_reviews: int = 0
    correct_reviews: int = 0
    average_quality: float = 0.0
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    difficulty_score: float = 0.5  # 0.0-1.0 arası zorluk


@dataclass
class ReviewSession:
    """Tekrar oturumu"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    items_reviewed: List[str] = field(default_factory=list)
    items_correct: int = 0
    items_incorrect: int = 0
    
    average_quality: float = 0.0
    xp_earned: int = 0


class SM2Algorithm:
    """
    SuperMemo 2 Algoritması
    
    Formül:
    EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    
    Interval hesaplama:
    - n=1: 1 gün
    - n=2: 6 gün
    - n>2: interval * EF
    """
    
    # Sabitler
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 3.0
    DEFAULT_EASE_FACTOR = 2.5
    
    MIN_INTERVAL = 1
    MAX_INTERVAL = 365
    
    GRADUATION_THRESHOLD = 3  # Bu kadar ardışık başarıdan sonra "learned"
    
    def __init__(self):
        self._review_history: Dict[str, List[Tuple[datetime, int]]] = {}
    
    def calculate_next_review(
        self,
        item: ReviewItem,
        quality: int  # 0-5 arası
    ) -> ReviewItem:
        """
        SM-2 algoritması ile sonraki tekrar zamanını hesapla
        
        Args:
            item: ReviewItem instance
            quality: 0-5 arası kalite puanı
        
        Returns:
            Updated ReviewItem
        """
        # Quality değeri kontrolü
        quality = max(0, min(5, quality))
        
        # Ease factor güncelle
        new_ef = self._calculate_ease_factor(item.ease_factor, quality)
        
        # Interval hesapla
        if quality < 3:
            # Başarısız - en başa dön
            new_interval = 1
            new_repetition = 0
        else:
            # Başarılı
            new_repetition = item.repetition + 1
            
            if new_repetition == 1:
                new_interval = 1
            elif new_repetition == 2:
                new_interval = 6
            else:
                new_interval = int(item.interval * new_ef)
            
            # Interval limitleri
            new_interval = max(self.MIN_INTERVAL, min(self.MAX_INTERVAL, new_interval))
        
        # Zorluk skoru güncelle
        difficulty_delta = (5 - quality) * 0.05
        new_difficulty = max(0.0, min(1.0, item.difficulty_score + difficulty_delta))
        
        # İstatistikleri güncelle
        total_quality = item.average_quality * item.total_reviews + quality
        new_total_reviews = item.total_reviews + 1
        new_average_quality = total_quality / new_total_reviews
        
        # Yeni review zamanı
        now = datetime.now()
        next_review = now + timedelta(days=new_interval)
        
        # Item güncelle
        item.ease_factor = new_ef
        item.interval = new_interval
        item.repetition = new_repetition
        item.next_review = next_review
        item.last_review = now
        item.total_reviews = new_total_reviews
        item.correct_reviews = item.correct_reviews + (1 if quality >= 3 else 0)
        item.average_quality = new_average_quality
        item.difficulty_score = new_difficulty
        
        return item
    
    def _calculate_ease_factor(
        self, 
        current_ef: float, 
        quality: int
    ) -> float:
        """
        Ease factor hesapla
        
        Formül: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        """
        delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        new_ef = current_ef + delta
        
        # Limitleri uygula
        return max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, new_ef))
    
    def get_due_items(
        self,
        items: List[ReviewItem],
        max_items: int = 20,
        include_new: bool = True
    ) -> List[ReviewItem]:
        """
        Bugün tekrar edilecek öğeleri getir
        
        Sıralama:
        1. Gecikmiş öğeler (urgency score'a göre)
        2. Bugün vadesi gelen öğeler
        3. Yeni öğeler (include_new=True ise)
        """
        now = datetime.now()
        
        due_items = []
        new_items = []
        
        for item in items:
            if item.next_review is None:
                if include_new:
                    new_items.append((item, 0))
            elif item.next_review <= now:
                # Gecikme gün sayısı = urgency
                overdue_days = (now - item.next_review).days
                urgency = min(overdue_days, 30)  # Max 30 gün gecikme
                due_items.append((item, urgency))
        
        # Urgency'ye göre sırala (yüksekten düşüğe)
        due_items.sort(key=lambda x: (-x[1], x[0].difficulty_score))
        
        # Yeni öğeleri difficulty'ye göre sırala
        new_items.sort(key=lambda x: x[0].difficulty_score)
        
        # Birleştir
        result = [item for item, _ in due_items[:max_items]]
        
        remaining_slots = max_items - len(result)
        if remaining_slots > 0 and new_items:
            result.extend([item for item, _ in new_items[:remaining_slots]])
        
        return result[:max_items]
    
    def calculate_retention_rate(
        self,
        item: ReviewItem
    ) -> float:
        """
        Tahmini retention (hatırlama) oranı
        
        Ebbinghaus forgetting curve kullanır:
        R = e^(-t/S)
        
        S = item.ease_factor * item.interval (stability)
        """
        if item.last_review is None:
            return 1.0 if item.next_review is None else 0.5
        
        now = datetime.now()
        days_since_review = (now - item.last_review).days
        
        # Stability hesapla
        stability = item.ease_factor * max(item.interval, 1)
        
        # Forgetting curve
        retention = math.exp(-days_since_review / stability)
        
        return max(0.0, min(1.0, retention))
    
    def get_mastery_level(
        self,
        item: ReviewItem
    ) -> Tuple[str, float]:
        """
        Hakimiyet seviyesi hesapla
        
        Returns:
            (level_name, progress_percentage)
        """
        # Faktörler
        retention = self.calculate_retention_rate(item)
        review_success = item.correct_reviews / max(item.total_reviews, 1)
        ease_normalized = (item.ease_factor - self.MIN_EASE_FACTOR) / (
            self.MAX_EASE_FACTOR - self.MIN_EASE_FACTOR
        )
        
        # Ağırlıklı skor
        mastery_score = (
            retention * 0.4 +
            review_success * 0.4 +
            ease_normalized * 0.2
        )
        
        # Seviye belirleme
        if mastery_score >= 0.9:
            return "mastered", mastery_score
        elif mastery_score >= 0.75:
            return "proficient", mastery_score
        elif mastery_score >= 0.5:
            return "developing", mastery_score
        elif mastery_score >= 0.25:
            return "learning", mastery_score
        else:
            return "novice", mastery_score
    
    def get_study_stats(
        self,
        items: List[ReviewItem]
    ) -> Dict[str, Any]:
        """Genel çalışma istatistikleri"""
        if not items:
            return {
                "total_items": 0,
                "mastered_count": 0,
                "due_today": 0,
                "overdue_count": 0,
                "average_retention": 0.0,
                "average_ease": 0.0
            }
        
        now = datetime.now()
        
        mastered = sum(1 for item in items if self.get_mastery_level(item)[0] == "mastered")
        due_today = sum(1 for item in items 
                       if item.next_review and item.next_review.date() == now.date())
        overdue = sum(1 for item in items 
                     if item.next_review and item.next_review < now)
        
        avg_retention = sum(self.calculate_retention_rate(item) for item in items) / len(items)
        avg_ease = sum(item.ease_factor for item in items) / len(items)
        
        return {
            "total_items": len(items),
            "mastered_count": mastered,
            "mastery_percentage": mastered / len(items) * 100,
            "due_today": due_today,
            "overdue_count": overdue,
            "average_retention": avg_retention,
            "average_ease": avg_ease,
            "levels": {
                "mastered": mastered,
                "proficient": sum(1 for item in items if self.get_mastery_level(item)[0] == "proficient"),
                "developing": sum(1 for item in items if self.get_mastery_level(item)[0] == "developing"),
                "learning": sum(1 for item in items if self.get_mastery_level(item)[0] == "learning"),
                "novice": sum(1 for item in items if self.get_mastery_level(item)[0] == "novice"),
            }
        }
    
    def optimize_review_schedule(
        self,
        items: List[ReviewItem],
        daily_minutes: int = 30,
        avg_item_minutes: int = 3
    ) -> List[List[ReviewItem]]:
        """
        Günlük tekrar programı optimize et
        
        Returns:
            Her gün için öğe listesi
        """
        daily_capacity = daily_minutes // avg_item_minutes
        
        # Öğeleri sonraki tekrar tarihine göre sırala
        sorted_items = sorted(
            [item for item in items if item.next_review],
            key=lambda x: x.next_review
        )
        
        # Günlük grupla
        schedule: Dict[datetime.date, List[ReviewItem]] = {}
        
        for item in sorted_items:
            day = item.next_review.date()
            if day not in schedule:
                schedule[day] = []
            schedule[day].append(item)
        
        # Yoğun günleri dağıt
        result = []
        for day in sorted(schedule.keys()):
            day_items = schedule[day]
            
            if len(day_items) <= daily_capacity:
                result.append(day_items)
            else:
                # Fazla öğeleri sonraki günlere taşı
                result.append(day_items[:daily_capacity])
                overflow = day_items[daily_capacity:]
                
                # Overflow'u dağıt
                next_day = day + timedelta(days=1)
                if next_day not in schedule:
                    schedule[next_day] = []
                schedule[next_day].extend(overflow)
        
        return result


# Singleton instance
sm2 = SM2Algorithm()
