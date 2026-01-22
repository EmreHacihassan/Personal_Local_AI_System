"""
Full Meta Learning - Quality Enhancements (2026 Student Optimization)
Kalite iyileştirmeleri - 2026 öğrenci deneyimi için kritik optimizasyonlar

Bu modül mevcut özelliklerin VERİMLİLİĞİNİ kritik derecede artırır.

2026 Öğrenci Profili Analizi:
- Dikkat süresi: 8-12 dakika (2020'de 20 dk idi)
- Çoklu cihaz kullanımı
- Anında geri bildirim beklentisi
- Mikro-öğrenme tercihi
- Sosyal medya kaynaklı dikkat dağınıklığı
- Flow state'e girmekte zorluk
- Bilgi kirliliği ile mücadele

Bilimsel Temeller:
- Flow Theory (Csikszentmihalyi, 1990)
- Cognitive Load Theory (Sweller, 2011)
- Attention Restoration Theory (Kaplan, 1995)
- Pomodoro 2.0 with AI adaptation
- Desirable Difficulties (Bjork, 2011)
- Testing Effect (Roediger, 2006)
"""

import uuid
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
import statistics
import random


# ============================================================================
# ENHANCEMENT 1: ATTENTION FLOW MANAGER
# Dikkat akışı yönetimi - Flow state'e girme ve koruma
# ============================================================================

class AttentionState(str, Enum):
    """Dikkat durumları (Flow Theory based)"""
    SCATTERED = "scattered"          # Dağınık - odaklanma yok
    FOCUSING = "focusing"            # Odaklanmaya çalışıyor
    FOCUSED = "focused"              # Odaklanmış
    FLOW = "flow"                    # Flow state - optimal performans
    HYPERFOCUS = "hyperfocus"        # Aşırı odaklanma (risk)
    FATIGUED = "fatigued"            # Yorgun - mola gerekli


class DistractionType(str, Enum):
    """Dikkat dağıtıcı türleri"""
    NOTIFICATION = "notification"    # Bildirim
    TASK_SWITCH = "task_switch"      # Görev değiştirme
    MIND_WANDERING = "mind_wandering" # Zihin gezinmesi
    EXTERNAL = "external"            # Dış faktör
    INTERNAL = "internal"            # İç faktör (endişe vs)


class FlowBlocker(str, Enum):
    """Flow engelleyiciler"""
    TOO_EASY = "too_easy"            # Çok kolay - sıkılma
    TOO_HARD = "too_hard"            # Çok zor - hayal kırıklığı
    UNCLEAR_GOAL = "unclear_goal"    # Belirsiz hedef
    NO_FEEDBACK = "no_feedback"      # Geri bildirim eksikliği
    INTERRUPTION = "interruption"    # Kesinti


@dataclass
class AttentionSession:
    """Dikkat oturumu - her öğrenme seansını takip eder"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    
    # Dikkat metrikleri
    current_state: AttentionState = AttentionState.SCATTERED
    flow_score: float = 0.0          # 0-100 arası flow skoru
    focus_duration_seconds: int = 0   # Kesintisiz odaklanma süresi
    total_distractions: int = 0
    
    # Flow döngüsü
    time_to_flow_seconds: int = 0    # Flow'a girme süresi
    flow_periods: List[Dict] = field(default_factory=list)  # Flow dönemleri
    current_streak_minutes: int = 0   # Mevcut kesintisiz çalışma
    
    # Adaptif parametreler
    optimal_session_length: int = 25  # Dakika - kişiye özel
    break_needed_at: Optional[datetime] = None
    next_micro_break: Optional[datetime] = None
    
    # Tahminler
    predicted_fatigue_time: Optional[datetime] = None
    distraction_risk_score: float = 0.0


@dataclass 
class AttentionProfile:
    """Kullanıcının dikkat profili - uzun vadeli öğrenme"""
    user_id: str = ""
    
    # Uzun vadeli metrikler
    avg_focus_duration: float = 15.0  # Ortalama odaklanma süresi (dk)
    avg_time_to_flow: float = 8.0     # Flow'a ortalama giriş süresi (dk)
    peak_performance_hours: List[int] = field(default_factory=lambda: [9, 10, 15, 16])
    distraction_prone_hours: List[int] = field(default_factory=lambda: [13, 14, 22, 23])
    
    # Öğrenilmiş tercihler
    preferred_session_length: int = 25
    preferred_break_length: int = 5
    max_sessions_before_long_break: int = 4
    
    # Dikkat dağıtıcılar analizi
    top_distractors: Dict[DistractionType, int] = field(default_factory=dict)
    flow_blockers: Dict[FlowBlocker, int] = field(default_factory=dict)
    
    # Flow geçmişi
    total_flow_minutes: int = 0
    best_flow_streak: int = 0        # En uzun flow süresi (dk)
    flow_trigger_patterns: List[str] = field(default_factory=list)


class AttentionFlowManager:
    """
    Dikkat Akışı Yöneticisi
    
    2026 öğrencisi için kritik:
    - Dikkat süresini dinamik olarak ölçer
    - Flow state'e girmeyi kolaylaştırır
    - Dikkat dağılmadan ÖNCE uyarır
    - Kişiselleştirilmiş oturum süreleri önerir
    """
    
    def __init__(self):
        self.sessions: Dict[str, AttentionSession] = {}
        self.profiles: Dict[str, AttentionProfile] = {}
        
        # Flow state parametreleri (bilimsel)
        self.MIN_FLOW_DURATION = 180  # 3 dk - minimum flow süresi
        self.FLOW_ENTRY_THRESHOLD = 70  # Flow'a giriş eşiği
        self.FATIGUE_THRESHOLD = 45  # Dakika - yorgunluk eşiği
        
    def start_session(self, user_id: str, content_difficulty: float = 0.5) -> AttentionSession:
        """Yeni dikkat oturumu başlat"""
        profile = self._get_or_create_profile(user_id)
        
        session = AttentionSession(
            user_id=user_id,
            optimal_session_length=profile.preferred_session_length,
        )
        
        # İlk micro-break zamanını ayarla (10-15 dk sonra)
        session.next_micro_break = datetime.now() + timedelta(
            minutes=min(15, profile.avg_focus_duration)
        )
        
        # Zorluğa göre tahminleri ayarla
        skill_match = 1.0 - abs(content_difficulty - 0.5) * 2  # 0-1 arası
        session.distraction_risk_score = (1.0 - skill_match) * 50
        
        self.sessions[session.id] = session
        return session
    
    def record_attention_signal(
        self, 
        session_id: str, 
        signal_type: str,
        signal_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Dikkat sinyali kaydet ve analiz et.
        
        Sinyaller:
        - "active": Aktif çalışma (scrolling, typing, clicking)
        - "idle": Pasif (hareketsizlik)
        - "distraction": Dikkat dağılması (tab switch, notification)
        - "return": Dönüş (dikkat yeniden kazanıldı)
        - "progress": İlerleme (soru cevaplama, içerik tamamlama)
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        now = datetime.now()
        result = {"state": session.current_state.value, "action": None}
        
        if signal_type == "active":
            session.focus_duration_seconds += 5
            session = self._update_flow_score(session, +2)
            
        elif signal_type == "idle":
            # 30 saniyeden fazla idle = dikkat kaybı riski
            idle_seconds = signal_data.get("duration", 0) if signal_data else 0
            if idle_seconds > 30:
                session = self._update_flow_score(session, -5)
                result["warning"] = "attention_drift_detected"
                
        elif signal_type == "distraction":
            session.total_distractions += 1
            session = self._update_flow_score(session, -15)
            
            # Flow state kaybedildi mi?
            if session.current_state == AttentionState.FLOW:
                session.current_state = AttentionState.FOCUSED
                result["alert"] = "flow_state_broken"
                
        elif signal_type == "progress":
            # İlerleme = pozitif reinforcement
            session = self._update_flow_score(session, +5)
            session.current_streak_minutes += 1
            
        elif signal_type == "return":
            # Dikkat geri kazanıldı
            session.current_state = AttentionState.FOCUSING
            session = self._update_flow_score(session, +3)
        
        # State güncellemesi
        session.current_state = self._calculate_attention_state(session)
        
        # Öneriler
        result["recommendations"] = self._generate_attention_recommendations(session)
        result["flow_score"] = session.flow_score
        result["state"] = session.current_state.value
        
        self.sessions[session_id] = session
        return result
    
    def _update_flow_score(self, session: AttentionSession, delta: float) -> AttentionSession:
        """Flow skorunu güncelle"""
        session.flow_score = max(0, min(100, session.flow_score + delta))
        return session
    
    def _calculate_attention_state(self, session: AttentionSession) -> AttentionState:
        """Mevcut dikkat durumunu hesapla"""
        score = session.flow_score
        
        if score < 20:
            return AttentionState.SCATTERED
        elif score < 40:
            return AttentionState.FOCUSING
        elif score < 70:
            return AttentionState.FOCUSED
        elif score < 95:
            return AttentionState.FLOW
        else:
            return AttentionState.HYPERFOCUS
    
    def _generate_attention_recommendations(self, session: AttentionSession) -> List[Dict]:
        """Dikkat için öneriler üret"""
        recommendations = []
        now = datetime.now()
        
        # Micro-break önerisi
        if session.next_micro_break and now >= session.next_micro_break:
            recommendations.append({
                "type": "micro_break",
                "priority": "high",
                "message": "30 saniyelik bir nefes molası zamanı 🧘",
                "action": "pause",
                "duration_seconds": 30
            })
        
        # Flow state yaklaşıyorsa teşvik
        if session.current_state == AttentionState.FOCUSING and session.flow_score > 55:
            recommendations.append({
                "type": "flow_approaching",
                "priority": "medium", 
                "message": "Harika gidiyorsun! Flow state'e yaklaşıyorsun 🎯",
                "action": "continue"
            })
        
        # Dikkat dağılma riski
        if session.distraction_risk_score > 60:
            recommendations.append({
                "type": "distraction_warning",
                "priority": "high",
                "message": "Dikkat dağılma riski yüksek. Bildirimleri kapat 📵",
                "action": "enable_focus_mode"
            })
        
        # Uzun süre flow'da = hyperfocus riski
        if session.current_state == AttentionState.FLOW:
            flow_duration = session.focus_duration_seconds / 60
            if flow_duration > 45:
                recommendations.append({
                    "type": "hyperfocus_warning",
                    "priority": "medium",
                    "message": "45+ dakika flow'dasın! Kısa bir mola faydalı olabilir 💧",
                    "action": "suggest_break"
                })
        
        return recommendations
    
    def get_optimal_session_config(self, user_id: str, content_type: str = "learning") -> Dict:
        """Kullanıcı için optimal oturum konfigürasyonu"""
        profile = self._get_or_create_profile(user_id)
        now = datetime.now()
        current_hour = now.hour
        
        # Saat bazlı ayarlama
        is_peak = current_hour in profile.peak_performance_hours
        is_prone = current_hour in profile.distraction_prone_hours
        
        base_length = profile.preferred_session_length
        
        if is_peak:
            session_length = min(45, int(base_length * 1.5))  # Peak'te %50 daha uzun
        elif is_prone:
            session_length = max(15, int(base_length * 0.6))  # Dikkat dağınıkken %40 kısa
        else:
            session_length = base_length
        
        return {
            "session_length_minutes": session_length,
            "break_length_minutes": 5 if session_length <= 25 else 10,
            "micro_breaks_enabled": True,
            "micro_break_interval_minutes": min(12, session_length // 2),
            "distraction_shield": is_prone,  # Bildirimleri engelle
            "is_peak_hour": is_peak,
            "flow_music_enabled": content_type == "learning",
            "focus_timer_style": "visual" if is_prone else "minimal"
        }
    
    def _get_or_create_profile(self, user_id: str) -> AttentionProfile:
        """Profil al veya oluştur"""
        if user_id not in self.profiles:
            self.profiles[user_id] = AttentionProfile(user_id=user_id)
        return self.profiles[user_id]


# ============================================================================
# ENHANCEMENT 2: MICRO-LEARNING OPTIMIZER
# Mikro-öğrenme optimizasyonu - Kısa dikkat süreleri için
# ============================================================================

class MicroContentType(str, Enum):
    """Mikro içerik türleri"""
    FLASH_CONCEPT = "flash_concept"      # 30 sn - tek kavram
    QUICK_QUIZ = "quick_quiz"            # 1 dk - hızlı quiz
    MINI_LESSON = "mini_lesson"          # 3 dk - mini ders
    SPACED_REMINDER = "spaced_reminder"  # 15 sn - hatırlatma
    MICRO_PRACTICE = "micro_practice"    # 2 dk - hızlı pratik


@dataclass
class MicroLearningUnit:
    """Mikro öğrenme birimi"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_type: MicroContentType = MicroContentType.FLASH_CONCEPT
    
    # İçerik
    title: str = ""
    content: str = ""
    visual_aid: Optional[str] = None  # Emoji veya icon
    
    # Zamanlama
    duration_seconds: int = 30
    optimal_time_of_day: List[int] = field(default_factory=list)
    
    # Bağlam
    topic: str = ""
    difficulty: float = 0.5
    prerequisite_units: List[str] = field(default_factory=list)
    
    # Etkileşim
    interaction_type: str = "read"  # read, swipe, tap, type
    completion_action: str = "next"  # next, quiz, apply


@dataclass
class LearningMoment:
    """Öğrenme anı - gün içinde yakalanabilir mikro fırsatlar"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    detected_at: datetime = field(default_factory=datetime.now)
    moment_type: str = ""  # waiting, commute, break, etc.
    available_seconds: int = 60
    
    # Bağlam
    location_type: str = ""  # home, transit, work, etc.
    device: str = ""  # phone, tablet, desktop
    
    # Öneri
    suggested_units: List[str] = field(default_factory=list)
    accepted: bool = False


class MicroLearningOptimizer:
    """
    Mikro Öğrenme Optimizatörü
    
    2026 öğrencisi için kritik:
    - İçeriği 30sn-3dk parçalara böler
    - "Dead time"ları öğrenme fırsatına çevirir
    - Swipe/tap bazlı hızlı etkileşim
    - Bilgi kirliliğini önler (sadece önemli bilgi)
    """
    
    def __init__(self):
        self.units: Dict[str, MicroLearningUnit] = {}
        self.user_moments: Dict[str, List[LearningMoment]] = defaultdict(list)
        
    def chunk_content_to_micro(
        self, 
        content: str, 
        topic: str,
        target_duration: int = 30
    ) -> List[MicroLearningUnit]:
        """İçeriği mikro parçalara böl"""
        units = []
        
        # Basit chunking - cümle bazlı
        sentences = content.replace('\n', ' ').split('. ')
        
        current_chunk = []
        current_duration = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Her cümle ~5 saniye okuma süresi
            sentence_duration = max(5, len(sentence) // 20)
            
            if current_duration + sentence_duration <= target_duration:
                current_chunk.append(sentence)
                current_duration += sentence_duration
            else:
                # Chunk tamamlandı
                if current_chunk:
                    units.append(self._create_micro_unit(
                        ". ".join(current_chunk) + ".",
                        topic,
                        current_duration
                    ))
                current_chunk = [sentence]
                current_duration = sentence_duration
        
        # Son chunk
        if current_chunk:
            units.append(self._create_micro_unit(
                ". ".join(current_chunk) + ".",
                topic,
                current_duration
            ))
        
        return units
    
    def _create_micro_unit(
        self, 
        content: str, 
        topic: str, 
        duration: int
    ) -> MicroLearningUnit:
        """Mikro birim oluştur"""
        # İçerik tipini belirle
        if duration <= 30:
            content_type = MicroContentType.FLASH_CONCEPT
        elif duration <= 60:
            content_type = MicroContentType.QUICK_QUIZ
        elif duration <= 120:
            content_type = MicroContentType.MICRO_PRACTICE
        else:
            content_type = MicroContentType.MINI_LESSON
        
        # Görsel yardımcı seç
        visual_aids = {
            "python": "🐍",
            "javascript": "⚡",
            "data": "📊",
            "ai": "🤖",
            "math": "📐",
            "default": "💡"
        }
        visual = visual_aids.get(topic.lower().split()[0], visual_aids["default"])
        
        unit = MicroLearningUnit(
            content_type=content_type,
            title=content[:50] + "..." if len(content) > 50 else content,
            content=content,
            visual_aid=visual,
            duration_seconds=duration,
            topic=topic,
            interaction_type="swipe" if duration <= 30 else "read"
        )
        
        self.units[unit.id] = unit
        return unit
    
    def detect_learning_moment(
        self, 
        user_id: str,
        context: Dict[str, Any]
    ) -> Optional[LearningMoment]:
        """Öğrenme anı tespit et"""
        available_seconds = context.get("available_seconds", 60)
        
        # Çok kısa süreler için öğrenme önerme
        if available_seconds < 15:
            return None
        
        moment = LearningMoment(
            user_id=user_id,
            moment_type=context.get("moment_type", "break"),
            available_seconds=available_seconds,
            location_type=context.get("location", "unknown"),
            device=context.get("device", "phone")
        )
        
        # Süreye uygun üniteler bul
        suitable_units = [
            u for u in self.units.values()
            if u.duration_seconds <= available_seconds
        ]
        
        # En uygun 3 tanesini öner
        suitable_units.sort(key=lambda x: abs(x.duration_seconds - available_seconds * 0.8))
        moment.suggested_units = [u.id for u in suitable_units[:3]]
        
        self.user_moments[user_id].append(moment)
        return moment
    
    def get_micro_feed(self, user_id: str, count: int = 5) -> List[Dict]:
        """
        TikTok/Instagram tarzı mikro içerik akışı
        Swipe ile geçilebilir hızlı öğrenme içerikleri
        """
        # Kullanıcının bekleyen ünitelerini al
        all_units = list(self.units.values())
        
        # Shuffle ve seç
        random.shuffle(all_units)
        selected = all_units[:count]
        
        feed = []
        for unit in selected:
            feed.append({
                "id": unit.id,
                "type": unit.content_type.value,
                "visual": unit.visual_aid,
                "title": unit.title,
                "content": unit.content,
                "duration": unit.duration_seconds,
                "interaction": unit.interaction_type,
                "topic": unit.topic,
                "swipeable": True
            })
        
        return feed


# ============================================================================
# ENHANCEMENT 3: REAL-TIME FEEDBACK LOOP
# Gerçek zamanlı geri bildirim döngüsü
# ============================================================================

class FeedbackIntensity(str, Enum):
    """Geri bildirim yoğunluğu"""
    SUBTLE = "subtle"          # Hafif (renk değişimi)
    MODERATE = "moderate"      # Orta (animasyon + ses)
    INTENSE = "intense"        # Yoğun (tam ekran + haptic)


class FeedbackTiming(str, Enum):
    """Geri bildirim zamanlaması"""
    IMMEDIATE = "immediate"    # Anında (<100ms)
    QUICK = "quick"            # Hızlı (<500ms)  
    DELAYED = "delayed"        # Gecikmeli (1-3s) - düşünme süresi


@dataclass
class FeedbackEvent:
    """Geri bildirim olayı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""       # correct, incorrect, progress, milestone, etc.
    intensity: FeedbackIntensity = FeedbackIntensity.MODERATE
    timing: FeedbackTiming = FeedbackTiming.IMMEDIATE
    
    # Görsel
    animation: str = ""        # confetti, shake, pulse, glow, etc.
    color: str = ""            # success, error, warning, info
    icon: str = ""             # emoji veya icon adı
    
    # Metin
    message: str = ""
    sub_message: str = ""
    
    # Ses/Haptic
    sound: Optional[str] = None
    haptic: Optional[str] = None  # light, medium, heavy
    
    # İstatistik
    stat_update: Optional[Dict] = None  # XP, streak, level vb.


class RealTimeFeedbackEngine:
    """
    Gerçek Zamanlı Geri Bildirim Motoru
    
    2026 öğrencisi için kritik:
    - Anında görsel geri bildirim
    - Dopamin odaklı mikro ödüller
    - Progress görselleştirme
    - "Streak" ve momentum koruması
    """
    
    # Geri bildirim şablonları
    FEEDBACK_TEMPLATES = {
        "correct_easy": {
            "animation": "pulse",
            "color": "success",
            "icon": "✓",
            "messages": ["Doğru!", "Harika!", "Güzel!"],
            "intensity": FeedbackIntensity.SUBTLE
        },
        "correct_medium": {
            "animation": "glow",
            "color": "success", 
            "icon": "🎯",
            "messages": ["Mükemmel!", "Tam isabet!", "Süpersin!"],
            "intensity": FeedbackIntensity.MODERATE
        },
        "correct_hard": {
            "animation": "confetti",
            "color": "success",
            "icon": "🏆",
            "messages": ["İNANILMAZ!", "USTALIĞA BİR ADIM DAHA!", "ZOR OLANI BAŞARDIN!"],
            "intensity": FeedbackIntensity.INTENSE
        },
        "incorrect_gentle": {
            "animation": "shake_gentle",
            "color": "warning",
            "icon": "💭",
            "messages": ["Neredeyse!", "Bir daha düşün", "Çok yaklaştın"],
            "intensity": FeedbackIntensity.SUBTLE
        },
        "incorrect_learning": {
            "animation": "pulse",
            "color": "info",
            "icon": "📚",
            "messages": ["Bu normal, öğreniyorsun!", "Hatalardan öğrenilir", "Devam et!"],
            "intensity": FeedbackIntensity.MODERATE
        },
        "streak_milestone": {
            "animation": "explosion",
            "color": "special",
            "icon": "🔥",
            "messages": ["{streak} günlük seri!", "Muhteşem tutarlılık!", "Durdurulamıyorsun!"],
            "intensity": FeedbackIntensity.INTENSE
        },
        "level_up": {
            "animation": "level_up",
            "color": "gold",
            "icon": "⬆️",
            "messages": ["SEVİYE ATLADIN!", "Level {level}!", "YENİ GÜÇLER AÇILDI!"],
            "intensity": FeedbackIntensity.INTENSE
        },
        "flow_entered": {
            "animation": "aura",
            "color": "purple",
            "icon": "🌊",
            "messages": ["Flow moduna girdin!", "Odaklanma dorukta!", "Bu hissi koru!"],
            "intensity": FeedbackIntensity.MODERATE
        },
        "micro_progress": {
            "animation": "progress_tick",
            "color": "success",
            "icon": "+",
            "messages": ["+{xp} XP", "İlerleme!", "Bir adım daha!"],
            "intensity": FeedbackIntensity.SUBTLE
        }
    }
    
    def __init__(self):
        self.user_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_correct": 0,
            "total_incorrect": 0,
            "current_streak": 0,
            "best_streak": 0,
            "xp": 0,
            "level": 1,
            "last_feedback": None
        })
    
    def generate_feedback(
        self,
        user_id: str,
        event_type: str,
        context: Dict[str, Any] = None
    ) -> FeedbackEvent:
        """Geri bildirim oluştur"""
        context = context or {}
        stats = self.user_stats[user_id]
        
        # Template seç
        template_key = self._select_template(event_type, context, stats)
        template = self.FEEDBACK_TEMPLATES.get(template_key, self.FEEDBACK_TEMPLATES["micro_progress"])
        
        # Mesaj seç
        message = random.choice(template["messages"])
        
        # Placeholder'ları doldur
        message = message.format(
            xp=context.get("xp", 10),
            streak=stats["current_streak"],
            level=stats["level"]
        )
        
        # Stats güncelle
        stat_update = self._update_stats(user_id, event_type, context)
        
        feedback = FeedbackEvent(
            event_type=event_type,
            intensity=template["intensity"],
            timing=FeedbackTiming.IMMEDIATE,
            animation=template["animation"],
            color=template["color"],
            icon=template["icon"],
            message=message,
            stat_update=stat_update
        )
        
        # Ses ve haptic ekle
        if template["intensity"] == FeedbackIntensity.INTENSE:
            feedback.sound = "success_fanfare" if "correct" in event_type else "level_up"
            feedback.haptic = "heavy"
        elif template["intensity"] == FeedbackIntensity.MODERATE:
            feedback.sound = "pop"
            feedback.haptic = "medium"
        
        stats["last_feedback"] = datetime.now()
        return feedback
    
    def _select_template(
        self, 
        event_type: str, 
        context: Dict,
        stats: Dict
    ) -> str:
        """Duruma göre template seç"""
        difficulty = context.get("difficulty", "medium")
        
        if event_type == "correct":
            if difficulty == "hard":
                return "correct_hard"
            elif difficulty == "easy":
                return "correct_easy"
            return "correct_medium"
            
        elif event_type == "incorrect":
            # Üst üste hata sayısı
            consecutive_errors = context.get("consecutive_errors", 0)
            if consecutive_errors < 2:
                return "incorrect_gentle"
            return "incorrect_learning"
            
        elif event_type == "streak":
            return "streak_milestone"
            
        elif event_type == "level_up":
            return "level_up"
            
        elif event_type == "flow":
            return "flow_entered"
            
        return "micro_progress"
    
    def _update_stats(
        self, 
        user_id: str, 
        event_type: str,
        context: Dict
    ) -> Dict:
        """İstatistikleri güncelle"""
        stats = self.user_stats[user_id]
        updates = {}
        
        if event_type == "correct":
            stats["total_correct"] += 1
            stats["current_streak"] += 1
            xp_gain = context.get("xp", 10)
            stats["xp"] += xp_gain
            updates["xp_gained"] = xp_gain
            updates["streak"] = stats["current_streak"]
            
            if stats["current_streak"] > stats["best_streak"]:
                stats["best_streak"] = stats["current_streak"]
                updates["new_best_streak"] = True
            
            # Level kontrolü
            new_level = self._calculate_level(stats["xp"])
            if new_level > stats["level"]:
                stats["level"] = new_level
                updates["level_up"] = new_level
                
        elif event_type == "incorrect":
            stats["total_incorrect"] += 1
            stats["current_streak"] = 0
            updates["streak_reset"] = True
        
        return updates
    
    def _calculate_level(self, xp: int) -> int:
        """XP'den level hesapla"""
        return int(math.sqrt(xp / 100)) + 1
    
    def get_progress_animation(self, user_id: str, target: str = "daily") -> Dict:
        """
        İlerleme animasyonu verisi
        Gamification progress bar/ring için
        """
        stats = self.user_stats[user_id]
        
        # Günlük hedef (örnek: 50 XP)
        daily_target = 50
        daily_progress = min(100, (stats["xp"] % 100) / daily_target * 100)
        
        # Level progress
        current_level_xp = (stats["level"] - 1) ** 2 * 100
        next_level_xp = stats["level"] ** 2 * 100
        level_progress = (stats["xp"] - current_level_xp) / (next_level_xp - current_level_xp) * 100
        
        return {
            "daily_progress": daily_progress,
            "level_progress": level_progress,
            "xp": stats["xp"],
            "level": stats["level"],
            "streak": stats["current_streak"],
            "animation_type": "circular_fill" if daily_progress < 100 else "celebration",
            "color_gradient": ["#4F46E5", "#7C3AED"] if level_progress < 50 else ["#7C3AED", "#EC4899"]
        }


# ============================================================================
# ENHANCEMENT 4: COGNITIVE LOAD BALANCER
# Bilişsel yük dengeleyici
# ============================================================================

class CognitiveLoadLevel(str, Enum):
    """Bilişsel yük seviyeleri (Sweller's CLT)"""
    MINIMAL = "minimal"        # Çok az - sıkılma riski
    OPTIMAL = "optimal"        # İdeal - öğrenme zone'u
    HIGH = "high"              # Yüksek - zorlanma
    OVERLOAD = "overload"      # Aşırı yük - öğrenme durur


@dataclass
class CognitiveLoadState:
    """Bilişsel yük durumu"""
    user_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Yük bileşenleri (Sweller'ın 3 tipi)
    intrinsic_load: float = 0.0      # İçsel yük (içerik zorluğu)
    extraneous_load: float = 0.0     # Gereksiz yük (kötü sunum)
    germane_load: float = 0.0        # Üretken yük (şema oluşturma)
    
    # Toplam yük
    total_load: float = 0.0
    load_level: CognitiveLoadLevel = CognitiveLoadLevel.OPTIMAL
    
    # Kapasite
    available_capacity: float = 100.0  # Kalan kapasite
    fatigue_factor: float = 1.0        # Yorgunluk çarpanı
    
    # Öneriler
    recommendations: List[str] = field(default_factory=list)


class CognitiveLoadBalancer:
    """
    Bilişsel Yük Dengeleyici
    
    2026 öğrencisi için kritik:
    - İçerik sunumunu dinamik olarak ayarlar
    - "Cognitive overload" önler
    - Optimal öğrenme bölgesinde tutar
    - Gereksiz bilgi yükünü azaltır
    """
    
    # İçerik kompleksitesi faktörleri
    COMPLEXITY_FACTORS = {
        "new_concepts": 15,      # Yeni kavram başına yük
        "interactions": 5,       # Etkileşim sayısı
        "text_density": 0.1,     # Kelime başına
        "visual_elements": 3,    # Görsel başına
        "code_lines": 2,         # Kod satırı başına
        "formulas": 20,          # Formül başına
        "links": 2,              # Bağlantı başına
    }
    
    # Optimal yük aralıkları
    OPTIMAL_RANGE = (40, 70)
    HIGH_THRESHOLD = 85
    OVERLOAD_THRESHOLD = 95
    
    def __init__(self):
        self.user_states: Dict[str, CognitiveLoadState] = {}
        self.user_history: Dict[str, List[CognitiveLoadState]] = defaultdict(list)
    
    def analyze_content_load(self, content: Dict[str, Any]) -> Dict[str, float]:
        """İçeriğin bilişsel yükünü analiz et"""
        loads = {}
        
        # İçsel yük hesapla
        intrinsic = 0
        intrinsic += content.get("new_concepts", 0) * self.COMPLEXITY_FACTORS["new_concepts"]
        intrinsic += content.get("formula_count", 0) * self.COMPLEXITY_FACTORS["formulas"]
        intrinsic += len(content.get("code", "").split('\n')) * self.COMPLEXITY_FACTORS["code_lines"]
        loads["intrinsic"] = min(100, intrinsic)
        
        # Gereksiz yük (sunum kalitesine göre)
        extraneous = 0
        if content.get("cluttered_layout", False):
            extraneous += 20
        if content.get("poor_formatting", False):
            extraneous += 15
        if content.get("irrelevant_info", 0) > 0:
            extraneous += content["irrelevant_info"] * 10
        loads["extraneous"] = min(50, extraneous)
        
        # Üretken yük
        germane = 0
        if content.get("examples", 0) > 0:
            germane += min(20, content["examples"] * 5)
        if content.get("analogies", 0) > 0:
            germane += min(15, content["analogies"] * 5)
        if content.get("practice_problems", 0) > 0:
            germane += min(15, content["practice_problems"] * 3)
        loads["germane"] = germane
        
        loads["total"] = loads["intrinsic"] + loads["extraneous"] + loads["germane"]
        
        # Zone belirleme
        total = loads["total"]
        if total < self.OPTIMAL_RANGE[0]:
            loads["zone"] = "underload"
        elif total <= self.OPTIMAL_RANGE[1]:
            loads["zone"] = "optimal"
        elif total <= self.HIGH_THRESHOLD:
            loads["zone"] = "high"
        else:
            loads["zone"] = "overload"
        
        return loads
    
    def get_user_cognitive_state(
        self, 
        user_id: str,
        session_duration_minutes: int = 0,
        items_completed: int = 0
    ) -> CognitiveLoadState:
        """Kullanıcının mevcut bilişsel durumunu al"""
        
        # Yorgunluk faktörü (oturum süresine göre)
        fatigue = 1.0 + (session_duration_minutes / 60) * 0.3  # Her saat %30 yorgunluk
        fatigue = min(fatigue, 2.0)  # Max 2x
        
        # Mevcut kapasite
        base_capacity = 100
        available = max(20, base_capacity / fatigue)
        
        state = CognitiveLoadState(
            user_id=user_id,
            fatigue_factor=fatigue,
            available_capacity=available
        )
        
        self.user_states[user_id] = state
        return state
    
    def adjust_content_for_load(
        self,
        content: Dict[str, Any],
        user_state: CognitiveLoadState
    ) -> Dict[str, Any]:
        """İçeriği kullanıcının kapasitesine göre ayarla"""
        
        content_load = self.analyze_content_load(content)
        adjusted = content.copy()
        
        total_load = content_load["total"]
        available = user_state.available_capacity
        
        # Yük kapasiteyi aşıyorsa ayarla
        if total_load > available:
            reduction_needed = (total_load - available) / total_load
            
            # İçerik basitleştirme stratejileri
            adjustments = []
            
            if reduction_needed > 0.3:
                # Büyük azaltma gerekli
                adjusted["split_content"] = True
                adjusted["show_summary_first"] = True
                adjusted["hide_advanced_details"] = True
                adjustments.append("İçerik parçalandı")
                
            if reduction_needed > 0.15:
                # Orta azaltma
                adjusted["simplify_language"] = True
                adjusted["add_visual_aid"] = True
                adjustments.append("Görsel yardım eklendi")
                
            # Gereksiz yükü azalt
            adjusted["clean_layout"] = True
            adjusted["remove_distractions"] = True
            
            adjusted["_adjustments"] = adjustments
            adjusted["_load_reduction"] = reduction_needed
        
        # Yük çok düşükse zorluk artır
        elif total_load < self.OPTIMAL_RANGE[0] and user_state.fatigue_factor < 1.3:
            adjusted["add_challenge"] = True
            adjusted["include_bonus_question"] = True
            adjusted["_load_increase"] = True
        
        return adjusted
    
    def get_pacing_recommendation(self, user_id: str) -> Dict[str, Any]:
        """Tempo önerisi - ne kadar hızlı/yavaş ilerlemeli"""
        state = self.user_states.get(user_id)
        if not state:
            return {"pace": "normal", "adjustment": 1.0}
        
        load_level = state.total_load / state.available_capacity
        
        if load_level > 0.9:
            return {
                "pace": "slow",
                "adjustment": 0.6,
                "message": "Biraz yavaşla, içeriği sindirmeye zaman ver",
                "suggest_break": True
            }
        elif load_level > 0.7:
            return {
                "pace": "moderate", 
                "adjustment": 0.85,
                "message": "İyi gidiyorsun, tempoyu koru"
            }
        elif load_level < 0.4:
            return {
                "pace": "fast",
                "adjustment": 1.3,
                "message": "Hazır görünüyorsun, hızlanabilirsin!"
            }
        
        return {"pace": "normal", "adjustment": 1.0}


# ============================================================================
# ENHANCEMENT 5: LEARNING MOMENTUM ENGINE  
# Öğrenme momentumu - sürdürülebilir ilerleme
# ============================================================================

class MomentumState(str, Enum):
    """Momentum durumları"""
    COLD = "cold"              # Soğuk başlangıç
    WARMING = "warming"        # Isınıyor
    ROLLING = "rolling"        # Akışta
    PEAK = "peak"              # Zirve momentum
    COOLING = "cooling"        # Soğuyor


@dataclass
class LearningMomentum:
    """Öğrenme momentumu durumu"""
    user_id: str = ""
    
    # Momentum metrikleri
    momentum_score: float = 0.0      # 0-100
    state: MomentumState = MomentumState.COLD
    
    # Streak bilgileri
    daily_streak: int = 0
    weekly_streak: int = 0
    session_streak: int = 0          # Oturum içi streak
    
    # Aktivite
    sessions_today: int = 0
    items_today: int = 0
    xp_today: int = 0
    
    # Trend
    trend_direction: str = "stable"  # improving, stable, declining
    velocity: float = 0.0            # Öğrenme hızı
    
    # Tehdit analizi
    risk_factors: List[str] = field(default_factory=list)
    boost_opportunities: List[str] = field(default_factory=list)


class LearningMomentumEngine:
    """
    Öğrenme Momentum Motoru
    
    2026 öğrencisi için kritik:
    - Tutarlılığı ödüllendirir
    - "Streak break" önler
    - Momentum kaybını erkenden algılar
    - Geri dönüş kolaylaştırır
    """
    
    def __init__(self):
        self.user_momentum: Dict[str, LearningMomentum] = {}
        self.activity_log: Dict[str, List[Dict]] = defaultdict(list)
        
    def record_activity(
        self,
        user_id: str,
        activity_type: str,
        value: int = 1
    ) -> LearningMomentum:
        """Aktivite kaydet ve momentum güncelle"""
        now = datetime.now()
        
        # Aktivite logla
        self.activity_log[user_id].append({
            "type": activity_type,
            "value": value,
            "timestamp": now
        })
        
        momentum = self._get_or_create_momentum(user_id)
        
        # Momentum güncelle
        if activity_type == "session_complete":
            momentum.sessions_today += 1
            momentum.momentum_score = min(100, momentum.momentum_score + 5)
        elif activity_type == "item_complete":
            momentum.items_today += value
            momentum.session_streak += 1
            momentum.momentum_score = min(100, momentum.momentum_score + 2)
        elif activity_type == "xp_earned":
            momentum.xp_today += value
            momentum.momentum_score = min(100, momentum.momentum_score + 1)
        elif activity_type == "daily_login":
            momentum.daily_streak += 1
            momentum.momentum_score = min(100, momentum.momentum_score + 10)
        
        # State güncelle
        momentum.state = self._calculate_state(momentum)
        
        # Risk ve fırsat analizi
        momentum.risk_factors = self._analyze_risks(momentum)
        momentum.boost_opportunities = self._find_boosts(momentum)
        
        self.user_momentum[user_id] = momentum
        return momentum
    
    def _get_or_create_momentum(self, user_id: str) -> LearningMomentum:
        """Momentum al veya oluştur"""
        if user_id not in self.user_momentum:
            self.user_momentum[user_id] = LearningMomentum(user_id=user_id)
        return self.user_momentum[user_id]
    
    def _calculate_state(self, momentum: LearningMomentum) -> MomentumState:
        """Momentum durumunu hesapla"""
        score = momentum.momentum_score
        
        if score < 20:
            return MomentumState.COLD
        elif score < 40:
            return MomentumState.WARMING
        elif score < 70:
            return MomentumState.ROLLING
        elif score < 90:
            return MomentumState.PEAK
        else:
            return MomentumState.PEAK
    
    def _analyze_risks(self, momentum: LearningMomentum) -> List[str]:
        """Risk faktörlerini analiz et"""
        risks = []
        
        if momentum.daily_streak > 5 and momentum.sessions_today == 0:
            risks.append("streak_at_risk")
        
        if momentum.momentum_score < 30 and momentum.state == MomentumState.COOLING:
            risks.append("momentum_declining")
        
        # Son 3 günün aktivitesine bak
        recent_activity = [
            a for a in self.activity_log.get(momentum.user_id, [])
            if a["timestamp"] > datetime.now() - timedelta(days=3)
        ]
        if len(recent_activity) < 5:
            risks.append("low_recent_activity")
        
        return risks
    
    def _find_boosts(self, momentum: LearningMomentum) -> List[str]:
        """Boost fırsatlarını bul"""
        boosts = []
        
        # Streak milestones yaklaşıyor
        if momentum.daily_streak in [6, 13, 20, 27]:
            boosts.append(f"milestone_approaching_{momentum.daily_streak + 1}")
        
        # XP hedefine yakın
        daily_xp_goal = 50
        if momentum.xp_today >= daily_xp_goal * 0.8 and momentum.xp_today < daily_xp_goal:
            boosts.append("daily_goal_close")
        
        # Momentum zirveye yakın
        if 80 <= momentum.momentum_score < 90:
            boosts.append("peak_momentum_close")
        
        return boosts
    
    def get_comeback_path(self, user_id: str) -> Dict[str, Any]:
        """
        Momentum kaybeden kullanıcı için geri dönüş yolu
        'Gentle re-onboarding'
        """
        momentum = self._get_or_create_momentum(user_id)
        
        if momentum.state == MomentumState.COLD:
            return {
                "path_type": "fresh_start",
                "message": "Tekrar hoş geldin! Küçük adımlarla başlayalım.",
                "suggested_session_minutes": 10,
                "content_type": "review",  # Yeni değil, tekrar
                "difficulty": "easy",
                "goal": "1 micro-lesson tamamla",
                "xp_bonus": 2.0,  # 2x XP bonus
                "no_pressure": True
            }
        elif momentum.state == MomentumState.WARMING:
            return {
                "path_type": "rebuilding",
                "message": "İyi gidiyorsun! Bir adım daha atalım.",
                "suggested_session_minutes": 15,
                "content_type": "mixed",
                "difficulty": "easy-medium",
                "goal": "3 item tamamla",
                "xp_bonus": 1.5
            }
        
        return {
            "path_type": "normal",
            "message": "Hazırsın! Devam edelim.",
            "suggested_session_minutes": 25,
            "xp_bonus": 1.0
        }
    
    def get_momentum_boost_notification(self, user_id: str) -> Optional[Dict]:
        """Momentum boost için proaktif bildirim"""
        momentum = self._get_or_create_momentum(user_id)
        
        if "streak_at_risk" in momentum.risk_factors:
            return {
                "type": "streak_save",
                "urgency": "high",
                "title": f"🔥 {momentum.daily_streak} günlük serin tehlikede!",
                "message": "2 dakikalık hızlı bir quiz ile streak'ini koru",
                "action": "quick_session",
                "action_duration": 120
            }
        
        if "daily_goal_close" in momentum.boost_opportunities:
            remaining = 50 - momentum.xp_today
            return {
                "type": "goal_push",
                "urgency": "medium",
                "title": f"🎯 Günlük hedefe {remaining} XP kaldı!",
                "message": "1 hızlı ders ile hedefini tamamla",
                "action": "micro_lesson"
            }
        
        if "peak_momentum_close" in momentum.boost_opportunities:
            return {
                "type": "peak_push",
                "urgency": "low",
                "title": "⚡ Zirve momentuma çok yakınsın!",
                "message": "Birkaç soru daha ve zirvedesin",
                "action": "continue"
            }
        
        return None


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

attention_flow_manager = AttentionFlowManager()
micro_learning_optimizer = MicroLearningOptimizer()
realtime_feedback_engine = RealTimeFeedbackEngine()
cognitive_load_balancer = CognitiveLoadBalancer()
learning_momentum_engine = LearningMomentumEngine()
