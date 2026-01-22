"""
Full Meta Learning - Advanced Spaced Repetition Module (v3.0)
Gelişmiş aralıklı tekrar sistemi

Features:
- Context-Aware Spacing: Bağlam duyarlı aralık hesaplama
- Emotional Tagging: Duygusal etiketleme ve hafıza bağlantısı
- Related Recall: İlişkili hatırlama tetikleyicisi
- Sleep-Optimized Scheduling: Uyku döngüsüne göre zamanlama
- Adaptive Difficulty: Dinamik zorluk ayarlama
"""

import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import random


# ============ ENUMS ============

class RetentionState(str, Enum):
    """Hafıza tutma durumları"""
    NEW = "new"                      # Yeni öğrenilen
    LEARNING = "learning"            # Öğrenme aşamasında
    YOUNG = "young"                  # Genç hafıza (<21 gün)
    MATURE = "mature"                # Olgun hafıza (>21 gün)
    RELEARNING = "relearning"        # Yeniden öğrenme


class RecallQuality(str, Enum):
    """Hatırlama kalitesi"""
    FORGOT = "forgot"                # Tamamen unutmuş (0)
    DIFFICULT = "difficult"          # Zor hatırladı (1-2)
    MODERATE = "moderate"            # Orta düzey (3)
    EASY = "easy"                    # Kolay hatırladı (4)
    PERFECT = "perfect"              # Mükemmel hatırladı (5)


class EmotionalTag(str, Enum):
    """Duygusal etiketler"""
    CURIOUS = "curious"              # Merak
    EXCITED = "excited"              # Heyecan
    FRUSTRATED = "frustrated"        # Hayal kırıklığı
    CONFIDENT = "confident"          # Güvenli
    CONFUSED = "confused"            # Karışık
    PROUD = "proud"                  # Gururlu
    ANXIOUS = "anxious"              # Endişeli
    NEUTRAL = "neutral"              # Nötr


class ContextType(str, Enum):
    """Bağlam türleri"""
    LOCATION = "location"            # Fiziksel konum
    TIME = "time"                    # Zaman
    MOOD = "mood"                    # Ruh hali
    ACTIVITY = "activity"            # Aktivite
    SOCIAL = "social"                # Sosyal ortam
    DEVICE = "device"                # Kullanılan cihaz


class SleepPhase(str, Enum):
    """Uyku fazları"""
    PRE_SLEEP = "pre_sleep"          # Uyku öncesi (son 1 saat)
    EARLY_MORNING = "early_morning"  # Erken sabah (uyandıktan sonra)
    MIDDAY = "midday"                # Öğle
    AFTERNOON = "afternoon"          # Öğleden sonra
    EVENING = "evening"              # Akşam


# ============ DATA CLASSES ============

@dataclass
class SpacedRepCard:
    """Gelişmiş flashcard"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str = ""
    user_id: str = ""
    
    # İçerik
    front: str = ""
    back: str = ""
    extra_info: str = ""
    
    # SM-2+ Parametreleri
    easiness_factor: float = 2.5     # E-Factor (1.3-2.5+)
    interval: int = 1                 # Gün cinsinden aralık
    repetitions: int = 0              # Başarılı tekrar sayısı
    
    # Gelişmiş metrikler
    stability: float = 1.0            # Hafıza stabilitesi
    difficulty: float = 0.3           # Zorluk (0-1)
    retrievability: float = 1.0       # Hatırlanabilirlik (0-1)
    
    # Durum
    state: RetentionState = RetentionState.NEW
    last_review: Optional[datetime] = None
    next_review: datetime = field(default_factory=datetime.now)
    
    # Duygusal bağlam
    emotional_tags: List[EmotionalTag] = field(default_factory=list)
    emotion_intensity: float = 0.5    # 0-1
    
    # Bağlam
    learning_contexts: List[Dict[str, Any]] = field(default_factory=list)
    
    # İlişkiler
    related_cards: List[str] = field(default_factory=list)
    prerequisite_cards: List[str] = field(default_factory=list)
    
    # İstatistikler
    total_reviews: int = 0
    correct_reviews: int = 0
    lapses: int = 0                   # Unutma sayısı
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReviewSession:
    """Tekrar oturumu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    
    # Kartlar
    cards_reviewed: List[str] = field(default_factory=list)
    cards_correct: int = 0
    cards_incorrect: int = 0
    
    # Bağlam
    context: Dict[str, Any] = field(default_factory=dict)
    mood_at_start: EmotionalTag = EmotionalTag.NEUTRAL
    mood_at_end: EmotionalTag = EmotionalTag.NEUTRAL
    
    # Performans
    avg_response_time_ms: int = 0
    focus_score: float = 0.0


@dataclass
class ContextSnapshot:
    """Bağlam anlık görüntüsü"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Bağlam verileri
    location: str = ""                # "home", "work", "commute", etc.
    time_of_day: str = ""             # "morning", "afternoon", etc.
    device: str = ""                  # "mobile", "desktop", "tablet"
    activity: str = ""                # "studying", "reviewing", "break"
    
    # Durum
    energy_level: float = 0.5         # 0-1
    stress_level: float = 0.3         # 0-1
    
    # Performans korelasyonu
    retention_rate: float = 0.0


@dataclass
class RelatedRecallCluster:
    """İlişkili hatırlama kümesi"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Merkez kart
    anchor_card_id: str = ""
    
    # İlişkili kartlar
    related_cards: List[Dict[str, Any]] = field(default_factory=list)
    
    # İlişki türleri
    relationship_types: List[str] = field(default_factory=list)
    
    # Tetikleme
    trigger_words: List[str] = field(default_factory=list)
    visual_cues: List[str] = field(default_factory=list)


# ============ CORE ALGORITHM ============

class FSRS:
    """Free Spaced Repetition Scheduler - FSRS Algoritması
    
    SM-2'nin modern alternatifi, makine öğrenmesi tabanlı.
    Daha doğru hafıza modelleme.
    """
    
    # FSRS Parametreleri (varsayılan değerler)
    W = [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61]
    
    def __init__(self):
        self.request_retention = 0.9  # Hedef retention oranı
        self.maximum_interval = 36500  # Max 100 yıl
        self.easy_bonus = 1.3
        self.hard_interval = 1.2
    
    def init_ds(self, rating: int) -> Tuple[float, float]:
        """İlk difficulty ve stability hesapla"""
        difficulty = max(1, min(10, self.W[4] - self.W[5] * (rating - 3)))
        stability = self.W[rating - 1] if rating > 0 else self.W[0]
        return difficulty, stability
    
    def next_ds(self, d: float, s: float, r: float, 
                rating: int) -> Tuple[float, float]:
        """Sonraki difficulty ve stability hesapla
        
        Args:
            d: Current difficulty
            s: Current stability
            r: Retrievability at time of review
            rating: 1=Again, 2=Hard, 3=Good, 4=Easy
        """
        if rating == 1:  # Forget
            new_d = min(10, d + 2)
            new_s = self.W[11] * math.pow(d, -self.W[12]) * \
                    (math.pow(s + 1, self.W[13]) - 1) * \
                    math.exp((1 - r) * self.W[14])
        else:
            # Success
            new_d = d - self.W[6] * (rating - 3)
            new_d = max(1, min(10, new_d))
            
            hard_penalty = self.W[15] if rating == 2 else 1
            easy_bonus = self.W[16] if rating == 4 else 1
            
            new_s = s * (1 + math.exp(self.W[8]) * 
                        (11 - d) * 
                        math.pow(s, -self.W[9]) * 
                        (math.exp((1 - r) * self.W[10]) - 1) *
                        hard_penalty * easy_bonus)
        
        return new_d, new_s
    
    def next_interval(self, stability: float) -> int:
        """Sonraki aralığı hesapla"""
        interval = stability / self.W[0] * \
                   (math.pow(self.request_retention, 1 / self.W[1]) - 1)
        return min(self.maximum_interval, max(1, round(interval)))
    
    def retrievability(self, stability: float, 
                       days_elapsed: float) -> float:
        """Mevcut retrievability hesapla"""
        return math.pow(1 + days_elapsed / (9 * stability), -1)


# ============ ENGINES ============

class ContextAwareSpacingEngine:
    """Bağlam duyarlı aralık engine'i"""
    
    def __init__(self):
        self.context_history: Dict[str, List[ContextSnapshot]] = {}
        self.context_correlations: Dict[str, Dict[str, float]] = {}
        self.fsrs = FSRS()
    
    def record_context(self, user_id: str, 
                      context: Dict[str, Any],
                      retention_rate: float) -> ContextSnapshot:
        """Bağlam kaydet"""
        snapshot = ContextSnapshot(
            location=context.get("location", ""),
            time_of_day=context.get("time_of_day", ""),
            device=context.get("device", ""),
            activity=context.get("activity", ""),
            energy_level=context.get("energy", 0.5),
            stress_level=context.get("stress", 0.3),
            retention_rate=retention_rate
        )
        
        if user_id not in self.context_history:
            self.context_history[user_id] = []
        self.context_history[user_id].append(snapshot)
        
        # Korelasyonları güncelle
        self._update_correlations(user_id)
        
        return snapshot
    
    def _update_correlations(self, user_id: str) -> None:
        """Bağlam-performans korelasyonlarını güncelle"""
        history = self.context_history.get(user_id, [])
        if len(history) < 10:
            return
        
        correlations = defaultdict(lambda: defaultdict(list))
        
        for snapshot in history:
            correlations["location"][snapshot.location].append(snapshot.retention_rate)
            correlations["time"][snapshot.time_of_day].append(snapshot.retention_rate)
            correlations["device"][snapshot.device].append(snapshot.retention_rate)
        
        # Ortalama hesapla
        if user_id not in self.context_correlations:
            self.context_correlations[user_id] = {}
        
        for context_type, values in correlations.items():
            self.context_correlations[user_id][context_type] = {
                k: sum(v) / len(v) for k, v in values.items() if v
            }
    
    def get_optimal_context(self, user_id: str) -> Dict[str, Any]:
        """En optimal bağlamı öner"""
        correlations = self.context_correlations.get(user_id, {})
        
        optimal = {}
        for context_type, values in correlations.items():
            if values:
                best = max(values.items(), key=lambda x: x[1])
                optimal[context_type] = {
                    "value": best[0],
                    "avg_retention": best[1]
                }
        
        return optimal
    
    def adjust_interval_for_context(self, base_interval: int,
                                   current_context: Dict[str, Any],
                                   user_id: str) -> int:
        """Bağlama göre aralığı ayarla"""
        correlations = self.context_correlations.get(user_id, {})
        if not correlations:
            return base_interval
        
        multiplier = 1.0
        
        # Her bağlam faktörü için ayarlama
        for context_type, values in correlations.items():
            current_value = current_context.get(context_type, "")
            if current_value in values:
                avg_retention = values[current_value]
                # Yüksek retention = daha uzun aralık
                if avg_retention > 0.8:
                    multiplier *= 1.2
                elif avg_retention < 0.6:
                    multiplier *= 0.8
        
        return max(1, round(base_interval * multiplier))


class EmotionalTaggingEngine:
    """Duygusal etiketleme engine'i"""
    
    # Duygu-hafıza korelasyonları (araştırma bazlı)
    EMOTION_MEMORY_BOOST = {
        EmotionalTag.EXCITED: 1.3,      # Heyecan = güçlü hafıza
        EmotionalTag.CURIOUS: 1.25,     # Merak = iyi odaklanma
        EmotionalTag.PROUD: 1.2,        # Gurur = pozitif pekiştirme
        EmotionalTag.CONFIDENT: 1.15,   # Güven = rahat öğrenme
        EmotionalTag.NEUTRAL: 1.0,      # Nötr = baz
        EmotionalTag.ANXIOUS: 0.9,      # Endişe = dikkat dağınıklığı
        EmotionalTag.CONFUSED: 0.85,    # Karışıklık = zayıf işleme
        EmotionalTag.FRUSTRATED: 0.8    # Hayal kırıklığı = negatif
    }
    
    def __init__(self):
        self.emotion_history: Dict[str, List[Tuple[EmotionalTag, float, float]]] = {}
    
    def tag_emotion(self, card_id: str, 
                   emotion: EmotionalTag,
                   intensity: float = 0.5) -> Dict[str, Any]:
        """Duygu etiketi ekle"""
        if card_id not in self.emotion_history:
            self.emotion_history[card_id] = []
        
        self.emotion_history[card_id].append((emotion, intensity, datetime.now().timestamp()))
        
        boost = self.EMOTION_MEMORY_BOOST.get(emotion, 1.0)
        intensity_factor = 0.5 + (intensity * 0.5)  # 0.5-1.0
        
        return {
            "emotion": emotion.value,
            "intensity": intensity,
            "memory_boost": boost * intensity_factor,
            "recommendation": self._get_recommendation(emotion)
        }
    
    def _get_recommendation(self, emotion: EmotionalTag) -> str:
        """Duyguya göre öneri"""
        recommendations = {
            EmotionalTag.EXCITED: "Harika! Bu enerjiyi kullanarak daha fazla öğrenin.",
            EmotionalTag.CURIOUS: "Merakınız öğrenmeyi güçlendiriyor. Derinleşin!",
            EmotionalTag.PROUD: "Başarınızı kutlayın. Kendini ödüllendir.",
            EmotionalTag.CONFIDENT: "Güveniniz yüksek. Zor konulara geçebilirsiniz.",
            EmotionalTag.NEUTRAL: "Dengeli bir durumdasınız. Devam edin.",
            EmotionalTag.ANXIOUS: "Bir nefes alın. Küçük adımlarla ilerleyin.",
            EmotionalTag.CONFUSED: "Karışıklık normal. Temel kavramlara dönün.",
            EmotionalTag.FRUSTRATED: "Mola verin. Farklı bir yaklaşım deneyin."
        }
        return recommendations.get(emotion, "")
    
    def get_emotional_pattern(self, card_id: str) -> Dict[str, Any]:
        """Duygusal pattern analizi"""
        history = self.emotion_history.get(card_id, [])
        if not history:
            return {"pattern": "unknown", "dominant_emotion": None}
        
        emotion_counts = defaultdict(int)
        intensity_sums = defaultdict(float)
        
        for emotion, intensity, _ in history:
            emotion_counts[emotion] += 1
            intensity_sums[emotion] += intensity
        
        dominant = max(emotion_counts.items(), key=lambda x: x[1])
        avg_intensity = intensity_sums[dominant[0]] / emotion_counts[dominant[0]]
        
        return {
            "dominant_emotion": dominant[0].value,
            "frequency": dominant[1],
            "avg_intensity": avg_intensity,
            "emotion_distribution": {e.value: c for e, c in emotion_counts.items()}
        }
    
    def calculate_emotional_interval_modifier(self, 
                                             card_id: str) -> float:
        """Duygusal aralık çarpanı hesapla"""
        history = self.emotion_history.get(card_id, [])
        if not history:
            return 1.0
        
        # Son 5 kayıt
        recent = history[-5:]
        
        total_boost = 0
        for emotion, intensity, _ in recent:
            boost = self.EMOTION_MEMORY_BOOST.get(emotion, 1.0)
            total_boost += boost * (0.5 + intensity * 0.5)
        
        return total_boost / len(recent)


class RelatedRecallEngine:
    """İlişkili hatırlama engine'i"""
    
    def __init__(self):
        self.clusters: Dict[str, RelatedRecallCluster] = {}
        self.card_relationships: Dict[str, List[Dict]] = {}
    
    def create_relationship(self, card_a: str, card_b: str,
                           relationship_type: str,
                           strength: float = 0.5) -> None:
        """İlişki oluştur"""
        if card_a not in self.card_relationships:
            self.card_relationships[card_a] = []
        if card_b not in self.card_relationships:
            self.card_relationships[card_b] = []
        
        # Bidirectional relationship
        self.card_relationships[card_a].append({
            "related_to": card_b,
            "type": relationship_type,
            "strength": strength
        })
        self.card_relationships[card_b].append({
            "related_to": card_a,
            "type": relationship_type,
            "strength": strength
        })
    
    def get_related_cards(self, card_id: str, 
                         min_strength: float = 0.3) -> List[Dict]:
        """İlişkili kartları al"""
        relationships = self.card_relationships.get(card_id, [])
        return [r for r in relationships if r["strength"] >= min_strength]
    
    def create_cluster(self, anchor_card_id: str,
                      trigger_words: List[str]) -> RelatedRecallCluster:
        """Hatırlama kümesi oluştur"""
        relationships = self.get_related_cards(anchor_card_id)
        
        cluster = RelatedRecallCluster(
            anchor_card_id=anchor_card_id,
            related_cards=[
                {"id": r["related_to"], "type": r["type"], "strength": r["strength"]}
                for r in relationships
            ],
            relationship_types=list(set(r["type"] for r in relationships)),
            trigger_words=trigger_words
        )
        
        self.clusters[cluster.id] = cluster
        return cluster
    
    def trigger_related_recall(self, card_id: str) -> List[Dict]:
        """İlişkili hatırlamayı tetikle"""
        related = self.get_related_cards(card_id, min_strength=0.5)
        
        # Strength'e göre sırala
        related.sort(key=lambda x: x["strength"], reverse=True)
        
        recall_prompts = []
        for rel in related[:3]:  # En güçlü 3 ilişki
            recall_prompts.append({
                "card_id": rel["related_to"],
                "relationship": rel["type"],
                "prompt": f"Bu kavramı hatırla: {rel['type']} ilişkili",
                "strength": rel["strength"]
            })
        
        return recall_prompts
    
    def strengthen_relationship(self, card_a: str, card_b: str,
                               boost: float = 0.1) -> None:
        """İlişkiyi güçlendir"""
        for rel in self.card_relationships.get(card_a, []):
            if rel["related_to"] == card_b:
                rel["strength"] = min(1.0, rel["strength"] + boost)
        
        for rel in self.card_relationships.get(card_b, []):
            if rel["related_to"] == card_a:
                rel["strength"] = min(1.0, rel["strength"] + boost)


class SleepOptimizedScheduler:
    """Uyku optimize zamanlayıcı"""
    
    # Uyku döngüsüne göre optimal tekrar zamanları
    OPTIMAL_PHASES = {
        SleepPhase.PRE_SLEEP: {
            "retention_boost": 1.2,
            "description": "Uyku öncesi yeni öğrenme için ideal",
            "card_types": ["new", "learning"]
        },
        SleepPhase.EARLY_MORNING: {
            "retention_boost": 1.15,
            "description": "Sabah tekrar için en iyi zaman",
            "card_types": ["review", "mature"]
        },
        SleepPhase.MIDDAY: {
            "retention_boost": 0.9,
            "description": "Öğle düşüşü - hafif tekrar",
            "card_types": ["easy", "refresh"]
        },
        SleepPhase.AFTERNOON: {
            "retention_boost": 1.0,
            "description": "Normal verimlilik",
            "card_types": ["all"]
        },
        SleepPhase.EVENING: {
            "retention_boost": 1.1,
            "description": "Gün sonu konsolidasyonu",
            "card_types": ["review", "difficult"]
        }
    }
    
    def __init__(self):
        self.user_sleep_patterns: Dict[str, Dict] = {}
    
    def set_sleep_schedule(self, user_id: str,
                          sleep_time: str,  # "23:00"
                          wake_time: str) -> None:  # "07:00"
        """Uyku programı ayarla"""
        self.user_sleep_patterns[user_id] = {
            "sleep_time": sleep_time,
            "wake_time": wake_time
        }
    
    def get_current_phase(self, user_id: str) -> SleepPhase:
        """Mevcut uyku fazını belirle"""
        now = datetime.now()
        hour = now.hour
        
        pattern = self.user_sleep_patterns.get(user_id, {
            "sleep_time": "23:00",
            "wake_time": "07:00"
        })
        
        sleep_hour = int(pattern["sleep_time"].split(":")[0])
        wake_hour = int(pattern["wake_time"].split(":")[0])
        
        # Pre-sleep: uyku saatinden 1 saat önce
        if sleep_hour - 1 <= hour < sleep_hour:
            return SleepPhase.PRE_SLEEP
        
        # Early morning: uyanıştan 2 saat sonrasına kadar
        if wake_hour <= hour < wake_hour + 2:
            return SleepPhase.EARLY_MORNING
        
        if 11 <= hour < 14:
            return SleepPhase.MIDDAY
        
        if 14 <= hour < 18:
            return SleepPhase.AFTERNOON
        
        return SleepPhase.EVENING
    
    def get_optimal_review_time(self, user_id: str,
                               card_type: str) -> Dict[str, Any]:
        """Optimal tekrar zamanını öner"""
        pattern = self.user_sleep_patterns.get(user_id)
        if not pattern:
            return {"suggestion": "Uyku programı ayarlanmamış"}
        
        best_phases = []
        for phase, info in self.OPTIMAL_PHASES.items():
            if card_type in info["card_types"] or "all" in info["card_types"]:
                best_phases.append({
                    "phase": phase.value,
                    "boost": info["retention_boost"],
                    "description": info["description"]
                })
        
        # En yüksek boost'a göre sırala
        best_phases.sort(key=lambda x: x["boost"], reverse=True)
        
        return {
            "recommended_phases": best_phases,
            "current_phase": self.get_current_phase(user_id).value
        }
    
    def schedule_with_sleep(self, base_next_review: datetime,
                           user_id: str) -> datetime:
        """Uyku döngüsüne göre zamanla"""
        pattern = self.user_sleep_patterns.get(user_id)
        if not pattern:
            return base_next_review
        
        wake_hour = int(pattern["wake_time"].split(":")[0])
        
        # Eğer tekrar zamanı uyku saatlerine denk geliyorsa, sabaha kaydır
        if 0 <= base_next_review.hour < wake_hour:
            return base_next_review.replace(hour=wake_hour + 1, minute=0)
        
        return base_next_review


class AdvancedSpacedRepetitionEngine:
    """Gelişmiş aralıklı tekrar ana engine'i"""
    
    def __init__(self):
        self.cards: Dict[str, SpacedRepCard] = {}
        self.fsrs = FSRS()
        self.context_engine = ContextAwareSpacingEngine()
        self.emotion_engine = EmotionalTaggingEngine()
        self.recall_engine = RelatedRecallEngine()
        self.sleep_scheduler = SleepOptimizedScheduler()
    
    def create_card(self, user_id: str, front: str, back: str,
                   content_id: str = "",
                   difficulty: float = 0.3) -> SpacedRepCard:
        """Yeni kart oluştur"""
        card = SpacedRepCard(
            user_id=user_id,
            content_id=content_id,
            front=front,
            back=back,
            difficulty=difficulty
        )
        
        self.cards[card.id] = card
        return card
    
    def review_card(self, card_id: str, 
                   quality: RecallQuality,
                   context: Dict[str, Any] = None,
                   emotion: EmotionalTag = None) -> Dict[str, Any]:
        """Kartı tekrar et"""
        card = self.cards.get(card_id)
        if not card:
            return {"error": "Card not found"}
        
        # Quality'yi rating'e çevir (1-4)
        rating_map = {
            RecallQuality.FORGOT: 1,
            RecallQuality.DIFFICULT: 2,
            RecallQuality.MODERATE: 3,
            RecallQuality.EASY: 4,
            RecallQuality.PERFECT: 4
        }
        rating = rating_map.get(quality, 3)
        
        # Mevcut retrievability hesapla
        if card.last_review:
            days_elapsed = (datetime.now() - card.last_review).total_seconds() / 86400
            retrievability = self.fsrs.retrievability(card.stability, days_elapsed)
        else:
            retrievability = 1.0
        
        # FSRS ile yeni difficulty ve stability
        if card.repetitions == 0:
            new_difficulty, new_stability = self.fsrs.init_ds(rating)
        else:
            new_difficulty, new_stability = self.fsrs.next_ds(
                card.difficulty, card.stability, retrievability, rating
            )
        
        # Interval hesapla
        base_interval = self.fsrs.next_interval(new_stability)
        
        # Bağlam ayarlaması
        if context:
            adjusted_interval = self.context_engine.adjust_interval_for_context(
                base_interval, context, card.user_id
            )
        else:
            adjusted_interval = base_interval
        
        # Duygusal ayarlama
        if emotion:
            self.emotion_engine.tag_emotion(card_id, emotion)
            emotion_modifier = self.emotion_engine.calculate_emotional_interval_modifier(card_id)
            adjusted_interval = round(adjusted_interval * emotion_modifier)
        
        # Kartı güncelle
        card.difficulty = new_difficulty
        card.stability = new_stability
        card.interval = max(1, adjusted_interval)
        card.last_review = datetime.now()
        
        # Uyku optimize zamanlama
        base_next = datetime.now() + timedelta(days=card.interval)
        card.next_review = self.sleep_scheduler.schedule_with_sleep(
            base_next, card.user_id
        )
        
        # İstatistikler
        card.total_reviews += 1
        if rating >= 3:
            card.correct_reviews += 1
            card.repetitions += 1
        else:
            card.lapses += 1
            card.repetitions = 0
        
        # State güncelle
        if card.repetitions == 0:
            card.state = RetentionState.RELEARNING
        elif card.interval < 21:
            card.state = RetentionState.YOUNG
        else:
            card.state = RetentionState.MATURE
        
        # İlişkili kartları tetikle
        related_prompts = self.recall_engine.trigger_related_recall(card_id)
        
        return {
            "card_id": card_id,
            "new_interval": card.interval,
            "next_review": card.next_review.isoformat(),
            "difficulty": card.difficulty,
            "stability": card.stability,
            "state": card.state.value,
            "related_recall": related_prompts
        }
    
    def get_due_cards(self, user_id: str, limit: int = 20) -> List[SpacedRepCard]:
        """Tekrar edilecek kartları al"""
        now = datetime.now()
        
        user_cards = [c for c in self.cards.values() if c.user_id == user_id]
        due_cards = [c for c in user_cards if c.next_review <= now]
        
        # Urgency'ye göre sırala (retrievability düşük = acil)
        for card in due_cards:
            if card.last_review:
                days = (now - card.last_review).total_seconds() / 86400
                card.retrievability = self.fsrs.retrievability(card.stability, days)
            else:
                card.retrievability = 0
        
        due_cards.sort(key=lambda x: x.retrievability)
        
        return due_cards[:limit]
    
    def get_forecast(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Gelecek tahminleri"""
        user_cards = [c for c in self.cards.values() if c.user_id == user_id]
        
        forecast = []
        now = datetime.now()
        
        for day in range(days + 1):
            target_date = now + timedelta(days=day)
            
            due_count = sum(
                1 for c in user_cards 
                if c.next_review.date() == target_date.date()
            )
            
            # Tahmini workload (dakika)
            estimated_minutes = due_count * 2  # Ortalama 2 dk/kart
            
            forecast.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "due_count": due_count,
                "estimated_minutes": estimated_minutes,
                "load": "light" if due_count < 10 else "medium" if due_count < 30 else "heavy"
            })
        
        return {
            "forecast": forecast,
            "total_cards": len(user_cards),
            "avg_daily_due": sum(f["due_count"] for f in forecast) / len(forecast)
        }


# ============ SINGLETON INSTANCES ============

context_aware_spacing_engine = ContextAwareSpacingEngine()
emotional_tagging_engine = EmotionalTaggingEngine()
related_recall_engine = RelatedRecallEngine()
sleep_optimized_scheduler = SleepOptimizedScheduler()
advanced_spaced_repetition_engine = AdvancedSpacedRepetitionEngine()
