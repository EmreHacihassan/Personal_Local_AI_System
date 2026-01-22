"""
Full Meta Learning - Adaptive Intelligence Module
Adaptif öğrenme zekası ve kişiselleştirme

Features:
- Struggle Detection: Zorlanma algılama ve otomatik yardım
- Learning Style AI: Öğrenme stili analizi ve uyarlama
- Optimal Time Predictor: En verimli çalışma zamanı tahmini
- Forgetting Prediction: Unutma tahmini ve proaktif tekrar
- Confusion Clustering: Karışıklık paterni analizi
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

class StruggleLevel(str, Enum):
    """Zorlanma seviyeleri"""
    NONE = "none"                # Zorlanmıyor
    MILD = "mild"                # Hafif zorlanma
    MODERATE = "moderate"        # Orta zorlanma
    SEVERE = "severe"            # Ciddi zorlanma
    BLOCKED = "blocked"          # Tamamen takılmış


class LearningStyleType(str, Enum):
    """VARK öğrenme stilleri + ek stiller"""
    VISUAL = "visual"            # Görsel öğrenen
    AUDITORY = "auditory"        # İşitsel öğrenen
    READING = "reading"          # Okuma/yazma odaklı
    KINESTHETIC = "kinesthetic"  # Yaparak öğrenen
    MIXED = "mixed"              # Karma


class ConfusionPattern(str, Enum):
    """Karışıklık pattern türleri"""
    SIMILAR_CONCEPTS = "similar_concepts"    # Benzer kavramlar karışıyor
    SEQUENCE_ERROR = "sequence_error"        # Sıralama hatası
    PARTIAL_UNDERSTANDING = "partial"        # Kısmi anlama
    TERMINOLOGY_CONFUSION = "terminology"    # Terim karışıklığı
    APPLICATION_GAP = "application_gap"      # Uygulama boşluğu


class TimeOfDay(str, Enum):
    """Gün içi zaman dilimleri"""
    EARLY_MORNING = "early_morning"    # 05:00-08:00
    MORNING = "morning"                 # 08:00-12:00
    AFTERNOON = "afternoon"             # 12:00-17:00
    EVENING = "evening"                 # 17:00-21:00
    NIGHT = "night"                     # 21:00-01:00
    LATE_NIGHT = "late_night"           # 01:00-05:00


class AdaptationAction(str, Enum):
    """Uyarlama aksiyonları"""
    SIMPLIFY = "simplify"              # Basitleştir
    ADD_EXAMPLE = "add_example"        # Örnek ekle
    CHANGE_FORMAT = "change_format"    # Format değiştir
    SLOW_DOWN = "slow_down"            # Yavaşla
    ADD_VISUAL = "add_visual"          # Görsel ekle
    PREREQUISITE = "prerequisite"      # Ön koşula geri dön
    BREAK_DOWN = "break_down"          # Parçala
    PRACTICE = "practice"              # Pratik yaptır


# ============ DATA CLASSES ============

@dataclass
class StruggleIndicator:
    """Zorlanma göstergesi"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str = ""
    user_id: str = ""
    
    # Metrikler
    time_spent_seconds: int = 0
    expected_time_seconds: int = 0
    revisit_count: int = 0
    error_count: int = 0
    hint_requests: int = 0
    
    # Davranış sinyalleri
    scroll_back_count: int = 0        # Geri kaydırma
    pause_count: int = 0              # Duraksama
    highlight_count: int = 0          # Vurgulama
    copy_paste_count: int = 0         # Kopyala-yapıştır
    
    # Sonuç
    struggle_level: StruggleLevel = StruggleLevel.NONE
    confidence_score: float = 0.0
    
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class LearningStyleProfile:
    """Öğrenme stili profili"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # VARK skorları (0-100)
    visual_score: float = 25.0
    auditory_score: float = 25.0
    reading_score: float = 25.0
    kinesthetic_score: float = 25.0
    
    # Ana stil
    primary_style: LearningStyleType = LearningStyleType.MIXED
    secondary_style: Optional[LearningStyleType] = None
    
    # Tercihler
    preferred_content_length: str = "medium"  # short, medium, long
    preferred_complexity: str = "medium"      # simple, medium, complex
    prefers_examples: bool = True
    prefers_visuals: bool = True
    prefers_practice: bool = True
    
    # Öğrenme hızı
    learning_speed: str = "average"  # slow, average, fast
    optimal_session_minutes: int = 25
    
    # Güncelleme
    data_points: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_dominant_style(self) -> LearningStyleType:
        """Baskın stili bul"""
        scores = {
            LearningStyleType.VISUAL: self.visual_score,
            LearningStyleType.AUDITORY: self.auditory_score,
            LearningStyleType.READING: self.reading_score,
            LearningStyleType.KINESTHETIC: self.kinesthetic_score
        }
        
        max_score = max(scores.values())
        dominant_styles = [k for k, v in scores.items() if v == max_score]
        
        if len(dominant_styles) > 1:
            return LearningStyleType.MIXED
        return dominant_styles[0]
    
    def get_content_recommendations(self) -> Dict[str, Any]:
        """İçerik önerileri"""
        recommendations = {
            "formats": [],
            "features": [],
            "avoid": []
        }
        
        if self.visual_score > 50:
            recommendations["formats"].extend(["infographics", "diagrams", "videos"])
            recommendations["features"].append("color_coding")
        
        if self.auditory_score > 50:
            recommendations["formats"].extend(["podcasts", "explanations", "discussions"])
            recommendations["features"].append("text_to_speech")
        
        if self.reading_score > 50:
            recommendations["formats"].extend(["articles", "books", "notes"])
            recommendations["features"].append("highlighting")
        
        if self.kinesthetic_score > 50:
            recommendations["formats"].extend(["exercises", "projects", "simulations"])
            recommendations["features"].append("interactive")
        
        return recommendations


@dataclass
class TimePerformanceData:
    """Zaman bazlı performans verisi"""
    user_id: str = ""
    time_of_day: TimeOfDay = TimeOfDay.MORNING
    
    # Metrikler
    sessions_count: int = 0
    total_minutes: int = 0
    avg_focus_score: float = 0.0
    avg_retention_score: float = 0.0
    avg_completion_rate: float = 0.0
    
    # Detay
    best_topics: List[str] = field(default_factory=list)
    worst_topics: List[str] = field(default_factory=list)


@dataclass
class OptimalTimeProfile:
    """Optimal zaman profili"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Zaman dilimi performansları
    time_performances: Dict[TimeOfDay, TimePerformanceData] = field(default_factory=dict)
    
    # Öneriler
    peak_times: List[TimeOfDay] = field(default_factory=list)
    avoid_times: List[TimeOfDay] = field(default_factory=list)
    
    # Günlük önerilen süre
    recommended_daily_minutes: int = 60
    optimal_session_length: int = 25
    recommended_breaks: int = 5
    
    # Haftalık pattern
    best_days: List[str] = field(default_factory=list)  # "monday", "tuesday", etc.
    
    last_analyzed: datetime = field(default_factory=datetime.now)


@dataclass
class ForgettingPrediction:
    """Unutma tahmini"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str = ""
    user_id: str = ""
    
    # Öğrenme geçmişi
    initial_learning_date: datetime = field(default_factory=datetime.now)
    last_review_date: datetime = field(default_factory=datetime.now)
    review_count: int = 0
    
    # Ebbinghaus parametreleri
    stability: float = 1.0           # Hafıza stabilitesi
    difficulty: float = 0.5          # İçerik zorluğu
    retention_rate: float = 1.0      # Şu anki tutma oranı
    
    # Tahminler
    predicted_retention: float = 1.0
    predicted_forget_date: datetime = field(default_factory=datetime.now)
    optimal_review_date: datetime = field(default_factory=datetime.now)
    
    # Urgency
    urgency_score: float = 0.0  # 0-100, yüksek = acil tekrar gerekli
    
    def calculate_retention(self, days_since_review: float) -> float:
        """Ebbinghaus unutma eğrisi ile retention hesapla"""
        # R = e^(-t/S) formülü
        # S = stability (gün cinsinden)
        retention = math.exp(-days_since_review / max(0.1, self.stability))
        return min(1.0, max(0.0, retention))
    
    def update_predictions(self) -> None:
        """Tahminleri güncelle"""
        now = datetime.now()
        days_since = (now - self.last_review_date).total_seconds() / 86400
        
        self.predicted_retention = self.calculate_retention(days_since)
        
        # Unutma tarihi (%50 retention threshold)
        days_to_50 = -self.stability * math.log(0.5)
        self.predicted_forget_date = self.last_review_date + timedelta(days=days_to_50)
        
        # Optimal tekrar tarihi (%70 retention threshold)
        days_to_70 = -self.stability * math.log(0.7)
        self.optimal_review_date = self.last_review_date + timedelta(days=days_to_70)
        
        # Urgency hesapla
        if self.predicted_retention < 0.5:
            self.urgency_score = 100
        elif self.predicted_retention < 0.7:
            self.urgency_score = 70 + (0.7 - self.predicted_retention) * 100
        elif self.predicted_retention < 0.85:
            self.urgency_score = 30 + (0.85 - self.predicted_retention) * 200
        else:
            self.urgency_score = max(0, (1.0 - self.predicted_retention) * 200)


@dataclass
class ConfusionCluster:
    """Karışıklık kümesi"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Karışan kavramlar
    confused_concepts: List[str] = field(default_factory=list)
    confusion_pattern: ConfusionPattern = ConfusionPattern.SIMILAR_CONCEPTS
    
    # Kanıtlar
    error_instances: List[Dict[str, Any]] = field(default_factory=list)
    confusion_score: float = 0.0  # 0-100
    
    # Çözüm
    suggested_remediation: List[str] = field(default_factory=list)
    comparison_created: bool = False
    
    first_detected: datetime = field(default_factory=datetime.now)
    last_occurred: datetime = field(default_factory=datetime.now)


# ============ ENGINES ============

class StruggleDetectionEngine:
    """Zorlanma algılama engine'i"""
    
    # Eşik değerleri
    THRESHOLDS = {
        "time_multiplier": {
            StruggleLevel.MILD: 1.5,
            StruggleLevel.MODERATE: 2.0,
            StruggleLevel.SEVERE: 3.0,
            StruggleLevel.BLOCKED: 5.0
        },
        "revisit_count": {
            StruggleLevel.MILD: 2,
            StruggleLevel.MODERATE: 4,
            StruggleLevel.SEVERE: 6,
            StruggleLevel.BLOCKED: 10
        },
        "error_count": {
            StruggleLevel.MILD: 1,
            StruggleLevel.MODERATE: 3,
            StruggleLevel.SEVERE: 5,
            StruggleLevel.BLOCKED: 8
        }
    }
    
    def __init__(self):
        self.indicators: Dict[str, List[StruggleIndicator]] = {}  # user_id -> indicators
        self.interventions: Dict[str, List[AdaptationAction]] = {}
    
    def detect_struggle(self, user_id: str, content_id: str,
                       metrics: Dict[str, Any]) -> StruggleIndicator:
        """Zorlanma tespit et"""
        indicator = StruggleIndicator(
            content_id=content_id,
            user_id=user_id,
            time_spent_seconds=metrics.get("time_spent", 0),
            expected_time_seconds=metrics.get("expected_time", 60),
            revisit_count=metrics.get("revisits", 0),
            error_count=metrics.get("errors", 0),
            hint_requests=metrics.get("hints", 0),
            scroll_back_count=metrics.get("scroll_backs", 0),
            pause_count=metrics.get("pauses", 0)
        )
        
        # Struggle level hesapla
        level_scores = {
            StruggleLevel.NONE: 0,
            StruggleLevel.MILD: 0,
            StruggleLevel.MODERATE: 0,
            StruggleLevel.SEVERE: 0,
            StruggleLevel.BLOCKED: 0
        }
        
        # Zaman bazlı analiz
        if indicator.expected_time_seconds > 0:
            time_ratio = indicator.time_spent_seconds / indicator.expected_time_seconds
            for level, threshold in self.THRESHOLDS["time_multiplier"].items():
                if time_ratio >= threshold:
                    level_scores[level] += 1
        
        # Revisit analizi
        for level, threshold in self.THRESHOLDS["revisit_count"].items():
            if indicator.revisit_count >= threshold:
                level_scores[level] += 1
        
        # Hata analizi
        for level, threshold in self.THRESHOLDS["error_count"].items():
            if indicator.error_count >= threshold:
                level_scores[level] += 1
        
        # Ek sinyaller
        behavior_score = (
            indicator.scroll_back_count * 0.5 +
            indicator.pause_count * 0.3 +
            indicator.hint_requests * 0.8
        )
        
        if behavior_score > 5:
            level_scores[StruggleLevel.MODERATE] += 1
        if behavior_score > 10:
            level_scores[StruggleLevel.SEVERE] += 1
        
        # En yüksek skoru bul
        max_level = StruggleLevel.NONE
        max_score = 0
        for level, score in level_scores.items():
            if score > max_score:
                max_score = score
                max_level = level
        
        indicator.struggle_level = max_level
        indicator.confidence_score = min(1.0, max_score / 3.0)
        
        # Kaydet
        if user_id not in self.indicators:
            self.indicators[user_id] = []
        self.indicators[user_id].append(indicator)
        
        return indicator
    
    def get_intervention(self, indicator: StruggleIndicator) -> List[AdaptationAction]:
        """Müdahale önerileri"""
        actions = []
        
        if indicator.struggle_level == StruggleLevel.NONE:
            return []
        
        if indicator.struggle_level == StruggleLevel.MILD:
            actions = [AdaptationAction.ADD_EXAMPLE, AdaptationAction.SLOW_DOWN]
        
        elif indicator.struggle_level == StruggleLevel.MODERATE:
            actions = [
                AdaptationAction.SIMPLIFY,
                AdaptationAction.ADD_VISUAL,
                AdaptationAction.BREAK_DOWN
            ]
        
        elif indicator.struggle_level == StruggleLevel.SEVERE:
            actions = [
                AdaptationAction.PREREQUISITE,
                AdaptationAction.CHANGE_FORMAT,
                AdaptationAction.PRACTICE
            ]
        
        elif indicator.struggle_level == StruggleLevel.BLOCKED:
            actions = [
                AdaptationAction.PREREQUISITE,
                AdaptationAction.SIMPLIFY,
                AdaptationAction.BREAK_DOWN,
                AdaptationAction.CHANGE_FORMAT
            ]
        
        return actions
    
    def get_struggle_summary(self, user_id: str) -> Dict[str, Any]:
        """Zorlanma özeti"""
        indicators = self.indicators.get(user_id, [])
        
        if not indicators:
            return {"total_struggles": 0, "level_distribution": {}}
        
        level_counts = defaultdict(int)
        for ind in indicators:
            level_counts[ind.struggle_level.value] += 1
        
        # En çok zorlanılan içerikler
        content_struggles = defaultdict(int)
        for ind in indicators:
            if ind.struggle_level != StruggleLevel.NONE:
                content_struggles[ind.content_id] += 1
        
        top_struggles = sorted(content_struggles.items(), 
                              key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_struggles": len([i for i in indicators 
                                   if i.struggle_level != StruggleLevel.NONE]),
            "level_distribution": dict(level_counts),
            "top_struggling_content": [c[0] for c in top_struggles],
            "recent_struggles": [
                {
                    "content_id": i.content_id,
                    "level": i.struggle_level.value,
                    "detected_at": i.detected_at.isoformat()
                }
                for i in indicators[-5:]
            ]
        }


class LearningStyleEngine:
    """Öğrenme stili analiz engine'i"""
    
    def __init__(self):
        self.profiles: Dict[str, LearningStyleProfile] = {}
        self.interaction_history: Dict[str, List[Dict]] = {}
    
    def analyze_interaction(self, user_id: str, 
                           interaction: Dict[str, Any]) -> None:
        """Etkileşimi analiz et ve profili güncelle"""
        
        if user_id not in self.profiles:
            self.profiles[user_id] = LearningStyleProfile(user_id=user_id)
        
        profile = self.profiles[user_id]
        
        # Etkileşim türüne göre stil skorlarını güncelle
        content_type = interaction.get("content_type", "")
        engagement_score = interaction.get("engagement", 0.5)
        performance = interaction.get("performance", 0.5)
        time_spent = interaction.get("time_spent", 0)
        
        # Ağırlık hesapla (başarılı etkileşimler daha önemli)
        weight = engagement_score * performance
        
        # Stil güncellemeleri
        if content_type in ["image", "video", "diagram", "infographic"]:
            profile.visual_score = self._update_score(
                profile.visual_score, weight * 10, profile.data_points
            )
        
        if content_type in ["audio", "podcast", "lecture"]:
            profile.auditory_score = self._update_score(
                profile.auditory_score, weight * 10, profile.data_points
            )
        
        if content_type in ["text", "article", "documentation"]:
            profile.reading_score = self._update_score(
                profile.reading_score, weight * 10, profile.data_points
            )
        
        if content_type in ["exercise", "project", "simulation", "code"]:
            profile.kinesthetic_score = self._update_score(
                profile.kinesthetic_score, weight * 10, profile.data_points
            )
        
        profile.data_points += 1
        profile.primary_style = profile.get_dominant_style()
        profile.last_updated = datetime.now()
        
        # Öğrenme hızı analizi
        expected_time = interaction.get("expected_time", time_spent)
        if expected_time > 0:
            speed_ratio = expected_time / max(1, time_spent)
            if speed_ratio > 1.3:
                profile.learning_speed = "fast"
            elif speed_ratio < 0.7:
                profile.learning_speed = "slow"
            else:
                profile.learning_speed = "average"
    
    def _update_score(self, current: float, delta: float, data_points: int) -> float:
        """Skor güncelle (exponential moving average)"""
        alpha = 2 / (data_points + 10)  # Smoothing factor
        new_score = current * (1 - alpha) + (current + delta) * alpha
        return min(100, max(0, new_score))
    
    def get_profile(self, user_id: str) -> Optional[LearningStyleProfile]:
        """Profili al"""
        return self.profiles.get(user_id)
    
    def get_content_adaptation(self, user_id: str, 
                               content: Dict[str, Any]) -> Dict[str, Any]:
        """İçerik adaptasyonu öner"""
        profile = self.profiles.get(user_id)
        if not profile:
            return {"adaptations": [], "format": "default"}
        
        adaptations = []
        
        # Görsel tercih
        if profile.visual_score > 60:
            adaptations.append({
                "type": "add_visuals",
                "reason": "Görsel öğrenme stiliniz güçlü",
                "suggestion": "Diyagram ve infografik ekle"
            })
        
        # İşitsel tercih
        if profile.auditory_score > 60:
            adaptations.append({
                "type": "add_audio",
                "reason": "İşitsel öğrenme stiliniz güçlü",
                "suggestion": "Sesli anlatım ekle"
            })
        
        # Pratik tercih
        if profile.kinesthetic_score > 60:
            adaptations.append({
                "type": "add_practice",
                "reason": "Yaparak öğrenme stiliniz güçlü",
                "suggestion": "İnteraktif alıştırma ekle"
            })
        
        # Hız adaptasyonu
        pace = "normal"
        if profile.learning_speed == "fast":
            pace = "condensed"
        elif profile.learning_speed == "slow":
            pace = "detailed"
        
        return {
            "adaptations": adaptations,
            "pace": pace,
            "session_length": profile.optimal_session_minutes,
            "preferences": profile.get_content_recommendations()
        }


class OptimalTimeEngine:
    """Optimal zaman tahmini engine'i"""
    
    def __init__(self):
        self.profiles: Dict[str, OptimalTimeProfile] = {}
        self.sessions: Dict[str, List[Dict]] = {}
    
    def record_session(self, user_id: str, session_data: Dict[str, Any]) -> None:
        """Oturum kaydet"""
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        
        session = {
            "timestamp": datetime.now(),
            "duration_minutes": session_data.get("duration", 0),
            "focus_score": session_data.get("focus", 0.5),
            "retention_score": session_data.get("retention", 0.5),
            "completion_rate": session_data.get("completion", 0.5),
            "topics": session_data.get("topics", [])
        }
        
        self.sessions[user_id].append(session)
        
        # Profili güncelle
        self._update_profile(user_id)
    
    def _get_time_of_day(self, dt: datetime) -> TimeOfDay:
        """Zaman dilimini belirle"""
        hour = dt.hour
        if 5 <= hour < 8:
            return TimeOfDay.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 21:
            return TimeOfDay.EVENING
        elif 21 <= hour or hour < 1:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.LATE_NIGHT
    
    def _update_profile(self, user_id: str) -> None:
        """Profili güncelle"""
        sessions = self.sessions.get(user_id, [])
        if not sessions:
            return
        
        if user_id not in self.profiles:
            self.profiles[user_id] = OptimalTimeProfile(user_id=user_id)
        
        profile = self.profiles[user_id]
        
        # Zaman dilimlerine göre grupla
        time_groups = defaultdict(list)
        for s in sessions:
            tod = self._get_time_of_day(s["timestamp"])
            time_groups[tod].append(s)
        
        # Her zaman dilimi için performans hesapla
        for tod, group in time_groups.items():
            if not group:
                continue
            
            perf = TimePerformanceData(
                user_id=user_id,
                time_of_day=tod,
                sessions_count=len(group),
                total_minutes=sum(s["duration_minutes"] for s in group),
                avg_focus_score=statistics.mean(s["focus_score"] for s in group),
                avg_retention_score=statistics.mean(s["retention_score"] for s in group),
                avg_completion_rate=statistics.mean(s["completion_rate"] for s in group)
            )
            
            profile.time_performances[tod] = perf
        
        # Peak ve avoid times belirle
        if profile.time_performances:
            sorted_times = sorted(
                profile.time_performances.items(),
                key=lambda x: (x[1].avg_focus_score + x[1].avg_retention_score) / 2,
                reverse=True
            )
            
            profile.peak_times = [t[0] for t in sorted_times[:2]]
            profile.avoid_times = [t[0] for t in sorted_times[-2:] 
                                  if t[1].sessions_count > 2]
        
        profile.last_analyzed = datetime.now()
    
    def get_optimal_times(self, user_id: str) -> Dict[str, Any]:
        """Optimal zamanları al"""
        profile = self.profiles.get(user_id)
        
        if not profile or not profile.time_performances:
            return {
                "has_data": False,
                "message": "Daha fazla veri gerekli",
                "default_recommendation": {
                    "peak_times": [TimeOfDay.MORNING.value, TimeOfDay.EVENING.value],
                    "session_length": 25
                }
            }
        
        return {
            "has_data": True,
            "peak_times": [t.value for t in profile.peak_times],
            "avoid_times": [t.value for t in profile.avoid_times],
            "time_performance": {
                tod.value: {
                    "focus": perf.avg_focus_score,
                    "retention": perf.avg_retention_score,
                    "sessions": perf.sessions_count
                }
                for tod, perf in profile.time_performances.items()
            },
            "recommendations": {
                "session_length": profile.optimal_session_length,
                "daily_goal": profile.recommended_daily_minutes,
                "break_frequency": profile.recommended_breaks
            }
        }
    
    def get_study_schedule(self, user_id: str, 
                          available_hours: List[int]) -> List[Dict[str, Any]]:
        """Çalışma planı öner"""
        profile = self.profiles.get(user_id)
        
        schedule = []
        for hour in available_hours:
            # Mock datetime for time classification
            mock_dt = datetime.now().replace(hour=hour, minute=0)
            tod = self._get_time_of_day(mock_dt)
            
            perf = profile.time_performances.get(tod) if profile else None
            
            quality = "average"
            if perf:
                combined = (perf.avg_focus_score + perf.avg_retention_score) / 2
                if combined > 0.7:
                    quality = "excellent"
                elif combined > 0.5:
                    quality = "good"
                elif combined < 0.3:
                    quality = "poor"
            
            schedule.append({
                "hour": hour,
                "time_of_day": tod.value,
                "quality": quality,
                "recommended": quality in ["excellent", "good"]
            })
        
        return schedule


class ForgettingPredictionEngine:
    """Unutma tahmini engine'i"""
    
    def __init__(self):
        self.predictions: Dict[str, Dict[str, ForgettingPrediction]] = {}
    
    def create_prediction(self, user_id: str, content_id: str,
                         initial_performance: float = 0.8,
                         difficulty: float = 0.5) -> ForgettingPrediction:
        """Yeni tahmin oluştur"""
        
        # Stability başlangıç değeri (performansa bağlı)
        base_stability = 1.0 + (initial_performance * 2)  # 1-3 gün
        difficulty_factor = 1.0 - (difficulty * 0.5)  # 0.5-1.0
        stability = base_stability * difficulty_factor
        
        prediction = ForgettingPrediction(
            content_id=content_id,
            user_id=user_id,
            stability=stability,
            difficulty=difficulty
        )
        
        prediction.update_predictions()
        
        if user_id not in self.predictions:
            self.predictions[user_id] = {}
        self.predictions[user_id][content_id] = prediction
        
        return prediction
    
    def record_review(self, user_id: str, content_id: str,
                     performance: float) -> Optional[ForgettingPrediction]:
        """Tekrar kaydet ve tahmini güncelle"""
        if user_id not in self.predictions:
            return None
        
        prediction = self.predictions[user_id].get(content_id)
        if not prediction:
            return self.create_prediction(user_id, content_id, performance)
        
        # Stability güncelle (SM-2 benzeri)
        if performance >= 0.8:
            prediction.stability *= 2.5  # Çok iyi hatırlama
        elif performance >= 0.6:
            prediction.stability *= 1.5  # İyi hatırlama
        elif performance >= 0.4:
            prediction.stability *= 1.0  # Orta - değişmez
        else:
            prediction.stability = max(0.5, prediction.stability * 0.5)  # Kötü
        
        prediction.last_review_date = datetime.now()
        prediction.review_count += 1
        prediction.update_predictions()
        
        return prediction
    
    def get_urgent_reviews(self, user_id: str, 
                          limit: int = 10) -> List[ForgettingPrediction]:
        """Acil tekrar gereken içerikleri al"""
        user_predictions = self.predictions.get(user_id, {})
        
        # Güncel tahminler
        for pred in user_predictions.values():
            pred.update_predictions()
        
        # Urgency'ye göre sırala
        sorted_preds = sorted(
            user_predictions.values(),
            key=lambda x: x.urgency_score,
            reverse=True
        )
        
        return sorted_preds[:limit]
    
    def get_retention_forecast(self, user_id: str, 
                               days_ahead: int = 7) -> Dict[str, Any]:
        """Retention tahmini"""
        user_predictions = self.predictions.get(user_id, {})
        
        forecast = []
        for day in range(days_ahead + 1):
            date = datetime.now() + timedelta(days=day)
            
            at_risk = 0
            safe = 0
            
            for pred in user_predictions.values():
                days_since = (date - pred.last_review_date).total_seconds() / 86400
                retention = pred.calculate_retention(days_since)
                
                if retention < 0.5:
                    at_risk += 1
                else:
                    safe += 1
            
            forecast.append({
                "date": date.strftime("%Y-%m-%d"),
                "at_risk_count": at_risk,
                "safe_count": safe,
                "risk_percentage": at_risk / max(1, at_risk + safe) * 100
            })
        
        return {
            "forecast": forecast,
            "total_items": len(user_predictions),
            "current_at_risk": forecast[0]["at_risk_count"] if forecast else 0
        }


class ConfusionClusteringEngine:
    """Karışıklık kümeleme engine'i"""
    
    def __init__(self):
        self.clusters: Dict[str, List[ConfusionCluster]] = {}
        self.error_history: Dict[str, List[Dict]] = {}
    
    def record_error(self, user_id: str, error_data: Dict[str, Any]) -> None:
        """Hata kaydet"""
        if user_id not in self.error_history:
            self.error_history[user_id] = []
        
        self.error_history[user_id].append({
            "timestamp": datetime.now(),
            "expected": error_data.get("expected", ""),
            "actual": error_data.get("actual", ""),
            "concept_a": error_data.get("concept_a", ""),
            "concept_b": error_data.get("concept_b", ""),
            "context": error_data.get("context", "")
        })
        
        # Cluster analizi
        self._analyze_clusters(user_id)
    
    def _analyze_clusters(self, user_id: str) -> None:
        """Cluster analizi yap"""
        errors = self.error_history.get(user_id, [])
        if len(errors) < 3:
            return
        
        # Kavram çiftlerini say
        concept_pairs = defaultdict(int)
        for error in errors:
            a, b = error.get("concept_a", ""), error.get("concept_b", "")
            if a and b:
                pair = tuple(sorted([a, b]))
                concept_pairs[pair] += 1
        
        # 2+ tekrar eden çiftleri cluster yap
        if user_id not in self.clusters:
            self.clusters[user_id] = []
        
        for pair, count in concept_pairs.items():
            if count >= 2:
                # Mevcut cluster var mı?
                existing = next(
                    (c for c in self.clusters[user_id] 
                     if set(c.confused_concepts) == set(pair)),
                    None
                )
                
                if existing:
                    existing.confusion_score = min(100, existing.confusion_score + 10)
                    existing.last_occurred = datetime.now()
                else:
                    cluster = ConfusionCluster(
                        user_id=user_id,
                        confused_concepts=list(pair),
                        confusion_pattern=self._detect_pattern(pair, errors),
                        confusion_score=count * 15
                    )
                    
                    cluster.suggested_remediation = self._get_remediation(cluster)
                    self.clusters[user_id].append(cluster)
    
    def _detect_pattern(self, pair: Tuple[str, str], 
                       errors: List[Dict]) -> ConfusionPattern:
        """Karışıklık paterni tespit et"""
        # Basit analiz - gerçek uygulamada NLP kullanılabilir
        a, b = pair
        
        if len(a) > 3 and len(b) > 3 and a[:3] == b[:3]:
            return ConfusionPattern.TERMINOLOGY_CONFUSION
        
        return ConfusionPattern.SIMILAR_CONCEPTS
    
    def _get_remediation(self, cluster: ConfusionCluster) -> List[str]:
        """Düzeltme önerileri"""
        remediation = []
        
        concepts = cluster.confused_concepts
        
        remediation.append(f"'{concepts[0]}' ve '{concepts[1]}' kavramlarını karşılaştır")
        remediation.append("Her iki kavram için ayrı ayrı örnekler çalış")
        remediation.append("Kavramlar arası farkları listele")
        
        if cluster.confusion_pattern == ConfusionPattern.TERMINOLOGY_CONFUSION:
            remediation.append("Terimlerin etimolojisini öğren")
        
        return remediation
    
    def get_confusion_map(self, user_id: str) -> Dict[str, Any]:
        """Karışıklık haritası"""
        clusters = self.clusters.get(user_id, [])
        
        if not clusters:
            return {"has_confusions": False, "clusters": []}
        
        return {
            "has_confusions": True,
            "total_clusters": len(clusters),
            "clusters": [
                {
                    "concepts": c.confused_concepts,
                    "pattern": c.confusion_pattern.value,
                    "score": c.confusion_score,
                    "remediation": c.suggested_remediation
                }
                for c in sorted(clusters, key=lambda x: x.confusion_score, reverse=True)
            ]
        }


# ============ SINGLETON INSTANCES ============

struggle_detection_engine = StruggleDetectionEngine()
learning_style_engine = LearningStyleEngine()
optimal_time_engine = OptimalTimeEngine()
forgetting_prediction_engine = ForgettingPredictionEngine()
confusion_clustering_engine = ConfusionClusteringEngine()
