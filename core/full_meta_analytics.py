"""
Full Meta Learning - Analytics Module
Gelişmiş öğrenme analitiği ve raporlama

Features:
- Learning Velocity Graph: Öğrenme hızı grafiği
- Strength Map: Konu bazlı güç haritası
- Time Investment ROI: Zaman yatırımı getirisi
- Optimal Study Plan: Optimal çalışma planı
- Burnout Detector: Tükenmişlik algılama
- Predicted Exam Score: Tahmini sınav puanı
"""

import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


# ============ ENUMS ============

class MetricType(str, Enum):
    """Metrik türleri"""
    VELOCITY = "velocity"            # Öğrenme hızı
    RETENTION = "retention"          # Hatırlama oranı
    ACCURACY = "accuracy"            # Doğruluk
    CONSISTENCY = "consistency"      # Tutarlılık
    EFFICIENCY = "efficiency"        # Verimlilik
    ENGAGEMENT = "engagement"        # Katılım


class StrengthLevel(str, Enum):
    """Güç seviyeleri"""
    WEAK = "weak"                    # 0-40
    DEVELOPING = "developing"        # 40-60
    MODERATE = "moderate"            # 60-75
    STRONG = "strong"                # 75-90
    MASTERED = "mastered"            # 90-100


class BurnoutRisk(str, Enum):
    """Tükenmişlik risk seviyeleri"""
    LOW = "low"                      # Düşük risk
    MODERATE = "moderate"            # Orta risk
    HIGH = "high"                    # Yüksek risk
    CRITICAL = "critical"            # Kritik risk


class StudySessionType(str, Enum):
    """Çalışma oturumu türleri"""
    LEARNING = "learning"            # Yeni öğrenme
    REVIEW = "review"                # Tekrar
    PRACTICE = "practice"            # Pratik
    ASSESSMENT = "assessment"        # Değerlendirme
    MIXED = "mixed"                  # Karışık


class TrendDirection(str, Enum):
    """Trend yönü"""
    IMPROVING = "improving"          # İyileşme
    STABLE = "stable"                # Stabil
    DECLINING = "declining"          # Düşüş


# ============ DATA CLASSES ============

@dataclass
class LearningDataPoint:
    """Öğrenme veri noktası"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Metrikler
    items_learned: int = 0
    items_reviewed: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    
    # Zaman
    duration_minutes: int = 0
    active_time_minutes: int = 0     # Gerçek aktif süre
    
    # Kalite
    retention_rate: float = 0.0
    accuracy_rate: float = 0.0
    
    # Bağlam
    session_type: StudySessionType = StudySessionType.MIXED
    topics: List[str] = field(default_factory=list)


@dataclass
class LearningVelocity:
    """Öğrenme hızı"""
    user_id: str = ""
    
    # Hız metrikleri
    items_per_hour: float = 0.0
    concepts_per_day: float = 0.0
    retention_per_review: float = 0.0
    
    # Trend
    velocity_trend: TrendDirection = TrendDirection.STABLE
    velocity_change_percent: float = 0.0
    
    # Karşılaştırma
    percentile_rank: int = 50        # Diğer kullanıcılara göre
    
    # Zaman serisi
    daily_velocities: List[float] = field(default_factory=list)
    weekly_average: float = 0.0
    monthly_average: float = 0.0


@dataclass
class TopicStrength:
    """Konu gücü"""
    topic: str = ""
    
    # Güç metrikleri
    strength_score: float = 0.0      # 0-100
    level: StrengthLevel = StrengthLevel.DEVELOPING
    
    # Detay
    total_items: int = 0
    mastered_items: int = 0
    struggling_items: int = 0
    
    # Trend
    trend: TrendDirection = TrendDirection.STABLE
    last_studied: Optional[datetime] = None
    
    # Alt konular
    subtopics: Dict[str, float] = field(default_factory=dict)


@dataclass
class TimeInvestmentROI:
    """Zaman yatırımı ROI"""
    period: str = ""                 # "day", "week", "month"
    
    # Yatırım
    total_time_minutes: int = 0
    active_learning_minutes: int = 0
    review_minutes: int = 0
    
    # Getiri
    new_concepts_learned: int = 0
    retention_gained: float = 0.0    # Toplam retention artışı
    mastery_gained: float = 0.0      # Mastery artışı
    
    # ROI hesaplama
    learning_efficiency: float = 0.0  # concepts per hour
    retention_per_minute: float = 0.0
    
    # Karşılaştırma
    roi_score: float = 0.0           # 0-100
    optimal_allocation: Dict[str, float] = field(default_factory=dict)


@dataclass
class StudyPlanSlot:
    """Çalışma planı slotu"""
    date: datetime = field(default_factory=datetime.now)
    time_slot: str = ""              # "09:00-10:00"
    
    # İçerik
    topics: List[str] = field(default_factory=list)
    session_type: StudySessionType = StudySessionType.LEARNING
    
    # Hedefler
    target_items: int = 0
    target_duration_minutes: int = 25
    
    # Öncelik
    priority: str = "medium"         # low, medium, high, critical
    
    # Durum
    completed: bool = False
    actual_duration: int = 0


@dataclass
class OptimalStudyPlan:
    """Optimal çalışma planı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Plan detayları
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    slots: List[StudyPlanSlot] = field(default_factory=list)
    
    # Hedefler
    target_topics: List[str] = field(default_factory=list)
    target_mastery: float = 80.0
    
    # Öneriler
    daily_goal_minutes: int = 60
    optimal_times: List[str] = field(default_factory=list)
    break_frequency: int = 25         # Pomodoro
    
    # Meta
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class BurnoutIndicator:
    """Tükenmişlik göstergesi"""
    user_id: str = ""
    assessed_at: datetime = field(default_factory=datetime.now)
    
    # Risk faktörleri (0-100)
    overwork_score: float = 0.0      # Aşırı çalışma
    fatigue_score: float = 0.0       # Yorgunluk
    declining_performance: float = 0.0
    irregular_schedule: float = 0.0
    
    # Genel risk
    overall_risk: BurnoutRisk = BurnoutRisk.LOW
    risk_score: float = 0.0          # 0-100
    
    # Uyarılar
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ExamScorePrediction:
    """Sınav puanı tahmini"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Giriş
    topics: List[str] = field(default_factory=list)
    exam_type: str = "general"       # general, midterm, final, certification
    
    # Tahmin
    predicted_score: float = 0.0     # 0-100
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    confidence_level: float = 0.0    # 0-1
    
    # Detay
    topic_predictions: Dict[str, float] = field(default_factory=dict)
    strong_topics: List[str] = field(default_factory=list)
    weak_topics: List[str] = field(default_factory=list)
    
    # Öneriler
    study_priorities: List[str] = field(default_factory=list)
    estimated_improvement: Dict[str, float] = field(default_factory=dict)
    
    predicted_at: datetime = field(default_factory=datetime.now)


# ============ ENGINES ============

class LearningVelocityEngine:
    """Öğrenme hızı analiz engine'i"""
    
    def __init__(self):
        self.data_points: Dict[str, List[LearningDataPoint]] = {}
        self.velocities: Dict[str, LearningVelocity] = {}
    
    def record_session(self, user_id: str, 
                      data: Dict[str, Any]) -> LearningDataPoint:
        """Oturum kaydet"""
        point = LearningDataPoint(
            items_learned=data.get("items_learned", 0),
            items_reviewed=data.get("items_reviewed", 0),
            correct_count=data.get("correct", 0),
            incorrect_count=data.get("incorrect", 0),
            duration_minutes=data.get("duration", 0),
            active_time_minutes=data.get("active_time", data.get("duration", 0)),
            session_type=StudySessionType(data.get("type", "mixed")),
            topics=data.get("topics", [])
        )
        
        # Oranları hesapla
        total = point.correct_count + point.incorrect_count
        if total > 0:
            point.accuracy_rate = point.correct_count / total
        
        if user_id not in self.data_points:
            self.data_points[user_id] = []
        self.data_points[user_id].append(point)
        
        # Velocity güncelle
        self._update_velocity(user_id)
        
        return point
    
    def _update_velocity(self, user_id: str) -> None:
        """Velocity güncelle"""
        points = self.data_points.get(user_id, [])
        if not points:
            return
        
        # Son 7 gün
        week_ago = datetime.now() - timedelta(days=7)
        recent_points = [p for p in points if p.timestamp > week_ago]
        
        if not recent_points:
            return
        
        # Toplam metrikler
        total_items = sum(p.items_learned + p.items_reviewed for p in recent_points)
        total_hours = sum(p.duration_minutes for p in recent_points) / 60
        
        velocity = LearningVelocity(user_id=user_id)
        
        if total_hours > 0:
            velocity.items_per_hour = total_items / total_hours
        
        # Günlük velocity
        daily_counts = defaultdict(int)
        for p in recent_points:
            date_key = p.timestamp.strftime("%Y-%m-%d")
            daily_counts[date_key] += p.items_learned
        
        velocity.daily_velocities = list(daily_counts.values())
        
        if velocity.daily_velocities:
            velocity.weekly_average = statistics.mean(velocity.daily_velocities)
        
        # Trend hesapla
        if len(velocity.daily_velocities) >= 3:
            first_half = velocity.daily_velocities[:len(velocity.daily_velocities)//2]
            second_half = velocity.daily_velocities[len(velocity.daily_velocities)//2:]
            
            first_avg = statistics.mean(first_half) if first_half else 0
            second_avg = statistics.mean(second_half) if second_half else 0
            
            if first_avg > 0:
                change = (second_avg - first_avg) / first_avg * 100
                velocity.velocity_change_percent = change
                
                if change > 10:
                    velocity.velocity_trend = TrendDirection.IMPROVING
                elif change < -10:
                    velocity.velocity_trend = TrendDirection.DECLINING
                else:
                    velocity.velocity_trend = TrendDirection.STABLE
        
        self.velocities[user_id] = velocity
    
    def get_velocity_graph_data(self, user_id: str, 
                                days: int = 30) -> Dict[str, Any]:
        """Velocity grafik verisi"""
        points = self.data_points.get(user_id, [])
        cutoff = datetime.now() - timedelta(days=days)
        
        recent_points = [p for p in points if p.timestamp > cutoff]
        
        # Günlük grupla
        daily_data = defaultdict(lambda: {"items": 0, "minutes": 0, "correct": 0, "total": 0})
        
        for p in recent_points:
            date_key = p.timestamp.strftime("%Y-%m-%d")
            daily_data[date_key]["items"] += p.items_learned + p.items_reviewed
            daily_data[date_key]["minutes"] += p.duration_minutes
            daily_data[date_key]["correct"] += p.correct_count
            daily_data[date_key]["total"] += p.correct_count + p.incorrect_count
        
        graph_data = []
        for date_str in sorted(daily_data.keys()):
            data = daily_data[date_str]
            hours = data["minutes"] / 60 if data["minutes"] > 0 else 1
            accuracy = data["correct"] / data["total"] if data["total"] > 0 else 0
            
            graph_data.append({
                "date": date_str,
                "items": data["items"],
                "velocity": data["items"] / hours,
                "minutes": data["minutes"],
                "accuracy": accuracy * 100
            })
        
        velocity = self.velocities.get(user_id)
        
        return {
            "data": graph_data,
            "summary": {
                "trend": velocity.velocity_trend.value if velocity else "stable",
                "change": velocity.velocity_change_percent if velocity else 0,
                "weekly_avg": velocity.weekly_average if velocity else 0
            }
        }


class StrengthMapEngine:
    """Konu güç haritası engine'i"""
    
    def __init__(self):
        self.strengths: Dict[str, Dict[str, TopicStrength]] = {}
    
    def update_strength(self, user_id: str, topic: str,
                       performance: float,
                       items_count: int = 1) -> TopicStrength:
        """Güç güncelle"""
        if user_id not in self.strengths:
            self.strengths[user_id] = {}
        
        if topic not in self.strengths[user_id]:
            self.strengths[user_id][topic] = TopicStrength(topic=topic)
        
        strength = self.strengths[user_id][topic]
        
        # Exponential moving average ile güncelle
        alpha = 0.3  # Smoothing factor
        strength.strength_score = (1 - alpha) * strength.strength_score + alpha * (performance * 100)
        strength.total_items += items_count
        
        if performance >= 0.9:
            strength.mastered_items += items_count
        elif performance < 0.5:
            strength.struggling_items += items_count
        
        # Level belirle
        score = strength.strength_score
        if score >= 90:
            strength.level = StrengthLevel.MASTERED
        elif score >= 75:
            strength.level = StrengthLevel.STRONG
        elif score >= 60:
            strength.level = StrengthLevel.MODERATE
        elif score >= 40:
            strength.level = StrengthLevel.DEVELOPING
        else:
            strength.level = StrengthLevel.WEAK
        
        strength.last_studied = datetime.now()
        
        return strength
    
    def get_strength_map(self, user_id: str) -> Dict[str, Any]:
        """Güç haritası al"""
        user_strengths = self.strengths.get(user_id, {})
        
        if not user_strengths:
            return {"has_data": False, "topics": []}
        
        topics = []
        for topic, strength in user_strengths.items():
            topics.append({
                "topic": topic,
                "score": strength.strength_score,
                "level": strength.level.value,
                "total_items": strength.total_items,
                "mastered": strength.mastered_items,
                "struggling": strength.struggling_items,
                "last_studied": strength.last_studied.isoformat() if strength.last_studied else None,
                "color": self._get_color_for_level(strength.level)
            })
        
        # Skora göre sırala
        topics.sort(key=lambda x: x["score"], reverse=True)
        
        # Özet istatistikler
        scores = [t["score"] for t in topics]
        
        return {
            "has_data": True,
            "topics": topics,
            "summary": {
                "total_topics": len(topics),
                "average_score": statistics.mean(scores) if scores else 0,
                "strongest": topics[0]["topic"] if topics else None,
                "weakest": topics[-1]["topic"] if topics else None,
                "level_distribution": self._get_level_distribution(user_strengths)
            }
        }
    
    def _get_color_for_level(self, level: StrengthLevel) -> str:
        """Seviyeye göre renk"""
        colors = {
            StrengthLevel.WEAK: "#F44336",
            StrengthLevel.DEVELOPING: "#FF9800",
            StrengthLevel.MODERATE: "#FFC107",
            StrengthLevel.STRONG: "#8BC34A",
            StrengthLevel.MASTERED: "#4CAF50"
        }
        return colors.get(level, "#9E9E9E")
    
    def _get_level_distribution(self, 
                               strengths: Dict[str, TopicStrength]) -> Dict[str, int]:
        """Seviye dağılımı"""
        distribution = defaultdict(int)
        for strength in strengths.values():
            distribution[strength.level.value] += 1
        return dict(distribution)


class TimeROIEngine:
    """Zaman yatırımı ROI engine'i"""
    
    def __init__(self):
        self.roi_records: Dict[str, List[TimeInvestmentROI]] = {}
    
    def calculate_roi(self, user_id: str,
                     learning_data: List[LearningDataPoint],
                     period: str = "week") -> TimeInvestmentROI:
        """ROI hesapla"""
        # Dönem filtresi
        if period == "day":
            cutoff = datetime.now() - timedelta(days=1)
        elif period == "week":
            cutoff = datetime.now() - timedelta(weeks=1)
        else:
            cutoff = datetime.now() - timedelta(days=30)
        
        filtered_data = [d for d in learning_data if d.timestamp > cutoff]
        
        if not filtered_data:
            return TimeInvestmentROI(period=period)
        
        roi = TimeInvestmentROI(period=period)
        
        # Zaman metrikleri
        roi.total_time_minutes = sum(d.duration_minutes for d in filtered_data)
        roi.active_learning_minutes = sum(
            d.active_time_minutes for d in filtered_data 
            if d.session_type == StudySessionType.LEARNING
        )
        roi.review_minutes = sum(
            d.active_time_minutes for d in filtered_data 
            if d.session_type == StudySessionType.REVIEW
        )
        
        # Getiri metrikleri
        roi.new_concepts_learned = sum(d.items_learned for d in filtered_data)
        roi.retention_gained = sum(d.retention_rate for d in filtered_data) / len(filtered_data)
        
        # Verimlilik
        total_hours = roi.total_time_minutes / 60
        if total_hours > 0:
            roi.learning_efficiency = roi.new_concepts_learned / total_hours
        
        if roi.total_time_minutes > 0:
            roi.retention_per_minute = roi.retention_gained / roi.total_time_minutes
        
        # ROI skoru (0-100)
        # Basit formül: efficiency * retention_quality
        roi.roi_score = min(100, roi.learning_efficiency * roi.retention_gained * 10)
        
        # Optimal dağılım önerisi
        roi.optimal_allocation = {
            "learning": 0.4,    # %40 yeni öğrenme
            "review": 0.35,     # %35 tekrar
            "practice": 0.25    # %25 pratik
        }
        
        # Kaydet
        if user_id not in self.roi_records:
            self.roi_records[user_id] = []
        self.roi_records[user_id].append(roi)
        
        return roi
    
    def get_roi_analysis(self, user_id: str) -> Dict[str, Any]:
        """ROI analizi"""
        records = self.roi_records.get(user_id, [])
        
        if not records:
            return {"has_data": False}
        
        latest = records[-1]
        
        # Trend (son 4 kayıt)
        recent = records[-4:] if len(records) >= 4 else records
        roi_trend = [r.roi_score for r in recent]
        
        trend_direction = TrendDirection.STABLE
        if len(roi_trend) >= 2:
            if roi_trend[-1] > roi_trend[0] * 1.1:
                trend_direction = TrendDirection.IMPROVING
            elif roi_trend[-1] < roi_trend[0] * 0.9:
                trend_direction = TrendDirection.DECLINING
        
        return {
            "has_data": True,
            "current_roi": {
                "score": latest.roi_score,
                "efficiency": latest.learning_efficiency,
                "time_invested": latest.total_time_minutes,
                "concepts_learned": latest.new_concepts_learned
            },
            "trend": trend_direction.value,
            "optimal_allocation": latest.optimal_allocation,
            "recommendations": self._get_roi_recommendations(latest)
        }
    
    def _get_roi_recommendations(self, roi: TimeInvestmentROI) -> List[str]:
        """ROI önerileri"""
        recommendations = []
        
        if roi.roi_score < 50:
            recommendations.append("Öğrenme verimliliğini artırmak için odaklanma sürelerini kısalt")
        
        if roi.review_minutes < roi.active_learning_minutes * 0.5:
            recommendations.append("Daha fazla tekrar yap - retention artırmak için")
        
        if roi.learning_efficiency < 5:
            recommendations.append("Öğrenme hızın düşük, aktif öğrenme tekniklerini dene")
        
        if not recommendations:
            recommendations.append("Harika gidiyorsun! Bu tempoyu koru.")
        
        return recommendations


class StudyPlanEngine:
    """Optimal çalışma planı engine'i"""
    
    def __init__(self):
        self.plans: Dict[str, OptimalStudyPlan] = {}
    
    def generate_plan(self, user_id: str,
                     topics: List[str],
                     available_hours: Dict[str, List[str]],  # {"Monday": ["09:00", "14:00"], ...}
                     target_mastery: float = 80.0,
                     duration_days: int = 7) -> OptimalStudyPlan:
        """Plan oluştur"""
        plan = OptimalStudyPlan(
            user_id=user_id,
            end_date=datetime.now() + timedelta(days=duration_days),
            target_topics=topics,
            target_mastery=target_mastery
        )
        
        slots = []
        current_date = datetime.now()
        
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for day_offset in range(duration_days):
            plan_date = current_date + timedelta(days=day_offset)
            weekday = weekdays[plan_date.weekday()]
            
            day_hours = available_hours.get(weekday, [])
            
            for hour in day_hours:
                # Her slot için topic seç (round-robin)
                topic_idx = len(slots) % len(topics)
                topic = topics[topic_idx]
                
                # Session type belirle
                if len(slots) % 3 == 0:
                    session_type = StudySessionType.LEARNING
                elif len(slots) % 3 == 1:
                    session_type = StudySessionType.REVIEW
                else:
                    session_type = StudySessionType.PRACTICE
                
                slot = StudyPlanSlot(
                    date=plan_date.replace(hour=int(hour.split(":")[0]), minute=0),
                    time_slot=f"{hour}-{int(hour.split(':')[0])+1}:00",
                    topics=[topic],
                    session_type=session_type,
                    target_items=10,
                    target_duration_minutes=25,
                    priority="medium"
                )
                slots.append(slot)
        
        plan.slots = slots
        plan.daily_goal_minutes = 60
        plan.optimal_times = ["09:00", "14:00", "19:00"]
        
        self.plans[plan.id] = plan
        return plan
    
    def get_today_plan(self, user_id: str) -> Dict[str, Any]:
        """Bugünkü planı al"""
        user_plans = [p for p in self.plans.values() if p.user_id == user_id]
        if not user_plans:
            return {"has_plan": False}
        
        latest_plan = user_plans[-1]
        today = datetime.now().date()
        
        today_slots = [s for s in latest_plan.slots if s.date.date() == today]
        
        completed = sum(1 for s in today_slots if s.completed)
        
        return {
            "has_plan": True,
            "slots": [
                {
                    "time": s.time_slot,
                    "topics": s.topics,
                    "type": s.session_type.value,
                    "duration": s.target_duration_minutes,
                    "completed": s.completed,
                    "priority": s.priority
                }
                for s in today_slots
            ],
            "progress": completed / len(today_slots) * 100 if today_slots else 0,
            "remaining_slots": len(today_slots) - completed
        }


class BurnoutDetectorEngine:
    """Tükenmişlik algılama engine'i"""
    
    # Risk faktörleri eşikleri
    THRESHOLDS = {
        "daily_hours_warning": 4,        # 4+ saat/gün uyarı
        "daily_hours_critical": 6,       # 6+ saat/gün kritik
        "consecutive_days_warning": 7,   # 7 gün üst üste
        "performance_drop_warning": 15,  # %15 performans düşüşü
        "irregular_schedule_threshold": 0.5  # %50'den az düzenli
    }
    
    def __init__(self):
        self.indicators: Dict[str, List[BurnoutIndicator]] = {}
    
    def assess_burnout_risk(self, user_id: str,
                           recent_sessions: List[LearningDataPoint]) -> BurnoutIndicator:
        """Tükenmişlik riski değerlendir"""
        indicator = BurnoutIndicator(user_id=user_id)
        
        if not recent_sessions:
            indicator.overall_risk = BurnoutRisk.LOW
            return indicator
        
        # Son 14 günü analiz et
        two_weeks_ago = datetime.now() - timedelta(days=14)
        recent = [s for s in recent_sessions if s.timestamp > two_weeks_ago]
        
        # 1. Aşırı çalışma skoru
        daily_minutes = defaultdict(int)
        for s in recent:
            date_key = s.timestamp.strftime("%Y-%m-%d")
            daily_minutes[date_key] += s.duration_minutes
        
        high_workload_days = sum(1 for m in daily_minutes.values() 
                                if m > self.THRESHOLDS["daily_hours_warning"] * 60)
        indicator.overwork_score = min(100, high_workload_days * 15)
        
        if any(m > self.THRESHOLDS["daily_hours_critical"] * 60 for m in daily_minutes.values()):
            indicator.warnings.append("⚠️ Bazı günlerde 6+ saat çalışma tespit edildi")
        
        # 2. Yorgunluk skoru (artan session süreleri = düşen verimlilik)
        if len(recent) >= 5:
            durations = [s.duration_minutes for s in recent[-5:]]
            avg_duration = statistics.mean(durations)
            if avg_duration > 60:  # 1 saatten uzun sessionlar
                indicator.fatigue_score = min(100, (avg_duration - 30) * 2)
        
        # 3. Performans düşüşü
        if len(recent) >= 10:
            early_accuracy = statistics.mean(s.accuracy_rate for s in recent[:5])
            late_accuracy = statistics.mean(s.accuracy_rate for s in recent[-5:])
            
            if early_accuracy > 0:
                drop = (early_accuracy - late_accuracy) / early_accuracy * 100
                if drop > 0:
                    indicator.declining_performance = min(100, drop * 5)
                    if drop > self.THRESHOLDS["performance_drop_warning"]:
                        indicator.warnings.append(f"📉 Performansta %{drop:.0f} düşüş")
        
        # 4. Düzensiz program
        study_hours = [s.timestamp.hour for s in recent]
        if study_hours:
            hour_variance = statistics.variance(study_hours) if len(study_hours) > 1 else 0
            indicator.irregular_schedule = min(100, hour_variance * 2)
        
        # Genel risk hesapla
        risk_score = (
            indicator.overwork_score * 0.35 +
            indicator.fatigue_score * 0.25 +
            indicator.declining_performance * 0.25 +
            indicator.irregular_schedule * 0.15
        )
        indicator.risk_score = risk_score
        
        # Risk seviyesi belirle
        if risk_score >= 70:
            indicator.overall_risk = BurnoutRisk.CRITICAL
            indicator.recommendations.append("🛑 Acil mola ver! En az 2-3 gün dinlen.")
        elif risk_score >= 50:
            indicator.overall_risk = BurnoutRisk.HIGH
            indicator.recommendations.append("⚠️ Çalışma sürenin azalt ve düzenli molalar ver.")
        elif risk_score >= 30:
            indicator.overall_risk = BurnoutRisk.MODERATE
            indicator.recommendations.append("💡 Dikkatli ol, çalışma-dinlenme dengesini koru.")
        else:
            indicator.overall_risk = BurnoutRisk.LOW
            indicator.recommendations.append("✅ Dengeli gidiyorsun, böyle devam et!")
        
        # Kaydet
        if user_id not in self.indicators:
            self.indicators[user_id] = []
        self.indicators[user_id].append(indicator)
        
        return indicator
    
    def get_burnout_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Tükenmişlik dashboard"""
        indicators = self.indicators.get(user_id, [])
        
        if not indicators:
            return {"has_data": False, "risk": "unknown"}
        
        latest = indicators[-1]
        
        # Trend (son 4 değerlendirme)
        recent_scores = [i.risk_score for i in indicators[-4:]]
        trend = TrendDirection.STABLE
        if len(recent_scores) >= 2:
            if recent_scores[-1] > recent_scores[0] * 1.2:
                trend = TrendDirection.DECLINING  # Risk artıyor
            elif recent_scores[-1] < recent_scores[0] * 0.8:
                trend = TrendDirection.IMPROVING
        
        return {
            "has_data": True,
            "current_risk": latest.overall_risk.value,
            "risk_score": latest.risk_score,
            "factors": {
                "overwork": latest.overwork_score,
                "fatigue": latest.fatigue_score,
                "performance_drop": latest.declining_performance,
                "schedule_irregularity": latest.irregular_schedule
            },
            "trend": trend.value,
            "warnings": latest.warnings,
            "recommendations": latest.recommendations
        }


class ExamPredictionEngine:
    """Sınav puanı tahmin engine'i"""
    
    def __init__(self):
        self.predictions: Dict[str, List[ExamScorePrediction]] = {}
        self.strength_engine = StrengthMapEngine()
    
    def predict_score(self, user_id: str,
                     topics: List[str],
                     topic_strengths: Dict[str, float],
                     exam_type: str = "general") -> ExamScorePrediction:
        """Sınav puanı tahmin et"""
        prediction = ExamScorePrediction(
            topics=topics,
            exam_type=exam_type
        )
        
        if not topic_strengths:
            prediction.predicted_score = 50  # Varsayılan
            prediction.confidence_level = 0.2
            return prediction
        
        # Topic ağırlıkları (eşit ağırlık varsayımı)
        weights = {t: 1.0 / len(topics) for t in topics}
        
        # Ağırlıklı ortalama
        total_score = 0
        for topic in topics:
            strength = topic_strengths.get(topic, 50)
            prediction.topic_predictions[topic] = strength
            total_score += strength * weights[topic]
        
        prediction.predicted_score = total_score
        
        # Güven aralığı (standart sapma bazlı)
        scores = list(topic_strengths.values())
        if len(scores) > 1:
            std_dev = statistics.stdev(scores)
            prediction.confidence_interval = (
                max(0, total_score - std_dev),
                min(100, total_score + std_dev)
            )
        else:
            prediction.confidence_interval = (total_score - 10, total_score + 10)
        
        # Confidence level (veri miktarına bağlı)
        prediction.confidence_level = min(0.9, 0.3 + len(topic_strengths) * 0.1)
        
        # Güçlü ve zayıf konular
        sorted_topics = sorted(topic_strengths.items(), key=lambda x: x[1], reverse=True)
        prediction.strong_topics = [t[0] for t in sorted_topics[:3] if t[1] >= 70]
        prediction.weak_topics = [t[0] for t in sorted_topics[-3:] if t[1] < 60]
        
        # Çalışma öncelikleri (en zayıf konular)
        prediction.study_priorities = prediction.weak_topics[:3]
        
        # Tahmini iyileştirme
        for weak_topic in prediction.weak_topics:
            current = topic_strengths.get(weak_topic, 50)
            potential_gain = (80 - current) * 0.5  # %50'sini kazanabilir
            prediction.estimated_improvement[weak_topic] = potential_gain
        
        # Kaydet
        if user_id not in self.predictions:
            self.predictions[user_id] = []
        self.predictions[user_id].append(prediction)
        
        return prediction
    
    def get_prediction_analysis(self, user_id: str) -> Dict[str, Any]:
        """Tahmin analizi"""
        predictions = self.predictions.get(user_id, [])
        
        if not predictions:
            return {"has_predictions": False}
        
        latest = predictions[-1]
        
        return {
            "has_predictions": True,
            "current_prediction": {
                "score": latest.predicted_score,
                "confidence_interval": list(latest.confidence_interval),
                "confidence_level": latest.confidence_level
            },
            "topic_breakdown": latest.topic_predictions,
            "strong_topics": latest.strong_topics,
            "weak_topics": latest.weak_topics,
            "study_priorities": latest.study_priorities,
            "potential_improvement": latest.estimated_improvement,
            "recommendation": self._get_score_recommendation(latest.predicted_score)
        }
    
    def _get_score_recommendation(self, score: float) -> str:
        """Puana göre öneri"""
        if score >= 90:
            return "🌟 Mükemmel hazırlık! Sınava güvenle girebilirsin."
        elif score >= 80:
            return "👍 İyi durumdasın, son tekrarlarla daha da güçlendir."
        elif score >= 70:
            return "📚 Orta seviye, zayıf konulara odaklan."
        elif score >= 60:
            return "⚠️ Risk bölgesi, yoğun çalışma gerekli."
        else:
            return "🚨 Acil aksiyon al, temel konuları baştan gözden geçir."


# ============ SINGLETON INSTANCES ============

learning_velocity_engine = LearningVelocityEngine()
strength_map_engine = StrengthMapEngine()
time_roi_engine = TimeROIEngine()
study_plan_engine = StudyPlanEngine()
burnout_detector_engine = BurnoutDetectorEngine()
exam_prediction_engine = ExamPredictionEngine()
