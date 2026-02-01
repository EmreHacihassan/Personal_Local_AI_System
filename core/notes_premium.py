"""
Premium Notes Features - Enterprise AI Assistant
=================================================

"WOW" dedirtecek premium özellikler:
- Smart Insights (AI analiz)
- Writing Streaks & Gamification  
- Focus Mode / Pomodoro Timer
- Daily Digest & Analytics
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import re

logger = logging.getLogger(__name__)


# ==================== ENUMS & CONSTANTS ====================

class Badge(Enum):
    """Gamification rozetleri."""
    FIRST_NOTE = "first_note"           # İlk not
    PROLIFIC_WRITER = "prolific_writer" # 50+ not    
    STREAK_7 = "streak_7"               # 7 gün streak
    STREAK_30 = "streak_30"             # 30 gün streak
    ORGANIZATION_MASTER = "org_master"  # 10+ klasör
    LINKER = "linker"                   # 20+ link
    NIGHT_OWL = "night_owl"             # Gece yazarı
    EARLY_BIRD = "early_bird"           # Sabah yazarı
    MARKDOWN_PRO = "markdown_pro"       # Markdown kullanımı
    FOCUSED = "focused"                 # 10+ pomodoro


BADGE_INFO = {
    Badge.FIRST_NOTE: {"title": "🎉 İlk Not", "description": "İlk notunu oluşturdun!", "points": 10},
    Badge.PROLIFIC_WRITER: {"title": "✍️ Üretken Yazar", "description": "50+ not yazdın!", "points": 100},
    Badge.STREAK_7: {"title": "🔥 Haftalık Seri", "description": "7 gün üst üste not aldın!", "points": 50},
    Badge.STREAK_30: {"title": "💎 Aylık Seri", "description": "30 gün üst üste not aldın!", "points": 200},
    Badge.ORGANIZATION_MASTER: {"title": "📂 Organizasyon Ustası", "description": "10+ klasör oluşturdun!", "points": 75},
    Badge.LINKER: {"title": "🔗 Bağlantı Uzmanı", "description": "20+ not bağlantısı oluşturdun!", "points": 50},
    Badge.NIGHT_OWL: {"title": "🦉 Gece Kuşu", "description": "Gece geç saatlerde yazıyorsun!", "points": 25},
    Badge.EARLY_BIRD: {"title": "🐦 Erken Kuş", "description": "Sabah erken yazıyorsun!", "points": 25},
    Badge.MARKDOWN_PRO: {"title": "📝 Markdown Pro", "description": "Markdown formatını ustaca kullanıyorsun!", "points": 40},
    Badge.FOCUSED: {"title": "🎯 Odaklanma Ustası", "description": "10+ pomodoro tamamladın!", "points": 100},
}


# ==================== DATA CLASSES ====================

@dataclass
class WritingStreak:
    """Yazma serisi verisi."""
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: Optional[str] = None
    total_writing_days: int = 0
    streak_history: List[Dict] = field(default_factory=list)


@dataclass
class FocusSession:
    """Pomodoro odaklanma oturumu."""
    session_id: str = ""
    start_time: str = ""
    end_time: Optional[str] = None
    duration_minutes: int = 25
    break_minutes: int = 5
    completed: bool = False
    note_id: Optional[str] = None
    words_written: int = 0


@dataclass
class UserStats:
    """Kullanıcı istatistikleri."""
    total_notes: int = 0
    total_words: int = 0
    total_folders: int = 0
    total_links: int = 0
    total_pomodoros: int = 0
    total_focus_minutes: int = 0
    badges_earned: List[str] = field(default_factory=list)
    points: int = 0
    level: int = 1
    streak: WritingStreak = field(default_factory=WritingStreak)


@dataclass  
class NoteInsights:
    """Not analiz sonuçları."""
    note_id: str
    word_count: int = 0
    character_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    reading_time_minutes: float = 0.0
    readability_score: float = 0.0  # Flesch-Kincaid benzeri
    sentiment: str = "neutral"  # positive, negative, neutral
    topics: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    has_links: bool = False
    has_images: bool = False
    has_code: bool = False
    has_latex: bool = False
    markdown_elements: Dict[str, int] = field(default_factory=dict)


# ==================== PREMIUM MANAGER ====================

class NotesPremiumManager:
    """Premium özellikler yöneticisi."""
    
    def __init__(self):
        from core.config import settings
        self.data_dir = Path(settings.DATA_DIR) / "premium"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats_file = self.data_dir / "user_stats.json"
        self.focus_file = self.data_dir / "focus_sessions.json"
        self.insights_cache = self.data_dir / "insights_cache.json"
        
        self._load_stats()
        logger.info("NotesPremiumManager initialized")
    
    def _load_stats(self) -> UserStats:
        """Kullanıcı istatistiklerini yükle."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    streak_data = data.pop("streak", {})
                    self._stats = UserStats(
                        **{k: v for k, v in data.items() if k != "streak"},
                        streak=WritingStreak(**streak_data)
                    )
            else:
                self._stats = UserStats()
        except Exception as e:
            logger.error(f"Stats load error: {e}")
            self._stats = UserStats()
        return self._stats
    
    def _save_stats(self):
        """İstatistikleri kaydet."""
        try:
            data = asdict(self._stats)
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Stats save error: {e}")
    
    # ==================== SMART INSIGHTS ====================
    
    def analyze_note(self, content: str, note_id: str = "") -> NoteInsights:
        """
        Not içeriğini analiz et - kelime sayısı, okunabilirlik, sentiment vb.
        """
        if not content:
            return NoteInsights(note_id=note_id)
        
        # Temel metrikler
        words = content.split()
        word_count = len(words)
        char_count = len(content)
        sentences = re.split(r'[.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])
        paragraphs = content.split('\n\n')
        paragraph_count = len([p for p in paragraphs if p.strip()])
        
        # Okunma süresi (ortalama 200 kelime/dakika)
        reading_time = word_count / 200.0
        
        # Okunabilirlik skoru (basitleştirilmiş Flesch-Kincaid)
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        avg_chars_per_word = char_count / max(word_count, 1)
        readability = max(0, min(100, 
            206.835 - (1.015 * avg_words_per_sentence) - (84.6 * (avg_chars_per_word / 5))
        ))
        
        # Sentiment analizi (basit keyword tabanlı)
        positive_words = ["harika", "mükemmel", "güzel", "iyi", "başarı", "mutlu", "sevgi",
                         "great", "excellent", "good", "success", "happy", "love", "amazing"]
        negative_words = ["kötü", "zor", "problem", "hata", "başarısız", "üzgün", "korku",
                         "bad", "difficult", "problem", "error", "failed", "sad", "fear"]
        
        content_lower = content.lower()
        pos_count = sum(1 for w in positive_words if w in content_lower)
        neg_count = sum(1 for w in negative_words if w in content_lower)
        
        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Markdown elementleri
        markdown_elements = {
            "headers": len(re.findall(r'^#+\s', content, re.MULTILINE)),
            "bold": len(re.findall(r'\*\*[^*]+\*\*', content)),
            "italic": len(re.findall(r'\*[^*]+\*', content)),
            "links": len(re.findall(r'\[\[.+?\]\]|\[.+?\]\(.+?\)', content)),
            "code_blocks": len(re.findall(r'```[\s\S]*?```', content)),
            "inline_code": len(re.findall(r'`[^`]+`', content)),
            "lists": len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE)),
            "checkboxes": len(re.findall(r'\[[ x]\]', content)),
            "images": len(re.findall(r'!\[.*?\]\(.*?\)', content)),
            "latex": len(re.findall(r'\$\$.+?\$\$|\$.+?\$', content)),
        }
        
        # Öneriler oluştur
        suggestions = []
        if word_count < 50:
            suggestions.append("💡 Notunuzu daha detaylı hale getirebilirsiniz")
        if readability < 40:
            suggestions.append("📖 Daha kısa cümleler kullanmayı deneyin")
        if markdown_elements["headers"] == 0 and word_count > 100:
            suggestions.append("📑 Başlıklar ekleyerek notunuzu organize edin")
        if markdown_elements["links"] == 0:
            suggestions.append("🔗 Diğer notlarınızla bağlantılar oluşturun")
        if markdown_elements["lists"] == 0 and word_count > 150:
            suggestions.append("📋 Listeler kullanarak bilgiyi yapılandırın")
        
        return NoteInsights(
            note_id=note_id,
            word_count=word_count,
            character_count=char_count,
            sentence_count=sentence_count,
            paragraph_count=paragraph_count,
            reading_time_minutes=round(reading_time, 1),
            readability_score=round(readability, 1),
            sentiment=sentiment,
            suggestions=suggestions,
            has_links=markdown_elements["links"] > 0,
            has_images=markdown_elements["images"] > 0,
            has_code=markdown_elements["code_blocks"] > 0 or markdown_elements["inline_code"] > 0,
            has_latex=markdown_elements["latex"] > 0,
            markdown_elements=markdown_elements,
        )
    
    # ==================== WRITING STREAKS ====================
    
    def record_activity(self, activity_type: str = "note_edit") -> WritingStreak:
        """Aktivite kaydet ve streak güncelle."""
        today = datetime.now().strftime("%Y-%m-%d")
        streak = self._stats.streak
        
        if streak.last_activity_date:
            last_date = datetime.strptime(streak.last_activity_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            diff = (today_date - last_date).days
            
            if diff == 0:
                # Aynı gün, streak değişmez
                pass
            elif diff == 1:
                # Ardışık gün, streak artar
                streak.current_streak += 1
                streak.total_writing_days += 1
            else:
                # Streak kırıldı
                if streak.current_streak > 0:
                    streak.streak_history.append({
                        "ended": streak.last_activity_date,
                        "length": streak.current_streak
                    })
                streak.current_streak = 1
                streak.total_writing_days += 1
        else:
            # İlk aktivite
            streak.current_streak = 1
            streak.total_writing_days = 1
        
        streak.last_activity_date = today
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        
        self._stats.streak = streak
        self._save_stats()
        
        # Rozet kontrolü
        self._check_streak_badges()
        
        return streak
    
    def get_streak_info(self) -> Dict[str, Any]:
        """Streak bilgisini döndür."""
        streak = self._stats.streak
        
        # Streak hala aktif mi kontrol et
        if streak.last_activity_date:
            last_date = datetime.strptime(streak.last_activity_date, "%Y-%m-%d")
            diff = (datetime.now() - last_date).days
            if diff > 1:
                # Streak kırılmış
                streak.current_streak = 0
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "last_activity": streak.last_activity_date,
            "total_writing_days": streak.total_writing_days,
            "streak_status": self._get_streak_status(streak.current_streak),
            "next_milestone": self._get_next_streak_milestone(streak.current_streak),
        }
    
    def _get_streak_status(self, streak: int) -> Dict:
        """Streak durumu emojisi ve mesajı."""
        if streak >= 30:
            return {"emoji": "💎", "message": "Efsane! Bir aydır yazıyorsun!", "level": "legendary"}
        elif streak >= 14:
            return {"emoji": "🔥", "message": "Harika! 2 haftayı geçtin!", "level": "epic"}
        elif streak >= 7:
            return {"emoji": "⚡", "message": "Süper! Bir haftayı doldurdun!", "level": "great"}
        elif streak >= 3:
            return {"emoji": "✨", "message": "İyi gidiyorsun! Devam et!", "level": "good"}
        elif streak >= 1:
            return {"emoji": "🌱", "message": "Başlangıç yaptın!", "level": "start"}
        else:
            return {"emoji": "💤", "message": "Bugün yazmaya başla!", "level": "none"}
    
    def _get_next_streak_milestone(self, current: int) -> Dict:
        """Sonraki streak hedefi."""
        milestones = [3, 7, 14, 30, 60, 100, 365]
        for m in milestones:
            if current < m:
                return {"target": m, "remaining": m - current}
        return {"target": 365, "remaining": 0, "message": "Tüm hedefleri tamamladın!"}
    
    # ==================== GAMIFICATION ====================
    
    def get_user_stats(self) -> Dict[str, Any]:
        """Kullanıcı istatistiklerini döndür."""
        from core.notes_manager import notes_manager
        
        # Güncel istatistikleri hesapla
        notes = notes_manager._load_notes()
        folders = notes_manager._load_folders()
        
        total_words = 0
        total_links = 0
        for note in notes:
            content = note.get("content", "")
            total_words += len(content.split())
            total_links += len(re.findall(r'\[\[.+?\]\]', content))
        
        self._stats.total_notes = len(notes)
        self._stats.total_words = total_words
        self._stats.total_folders = len(folders)
        self._stats.total_links = total_links
        
        # Level hesapla
        self._stats.level = 1 + (self._stats.points // 100)
        
        # Rozetleri kontrol et
        self._check_all_badges()
        self._save_stats()
        
        return {
            "total_notes": self._stats.total_notes,
            "total_words": self._stats.total_words,
            "total_folders": self._stats.total_folders,
            "total_links": self._stats.total_links,
            "total_pomodoros": self._stats.total_pomodoros,
            "total_focus_minutes": self._stats.total_focus_minutes,
            "points": self._stats.points,
            "level": self._stats.level,
            "level_progress": (self._stats.points % 100),
            "badges": [
                {
                    "id": badge,
                    **BADGE_INFO.get(Badge(badge), {})
                }
                for badge in self._stats.badges_earned
            ],
            "streak": self.get_streak_info(),
        }
    
    def _check_all_badges(self):
        """Tüm rozetleri kontrol et."""
        self._check_note_badges()
        self._check_streak_badges()
        self._check_organization_badges()
    
    def _check_note_badges(self):
        """Not rozetlerini kontrol et."""
        if self._stats.total_notes >= 1:
            self._award_badge(Badge.FIRST_NOTE)
        if self._stats.total_notes >= 50:
            self._award_badge(Badge.PROLIFIC_WRITER)
        if self._stats.total_links >= 20:
            self._award_badge(Badge.LINKER)
    
    def _check_streak_badges(self):
        """Streak rozetlerini kontrol et."""
        if self._stats.streak.longest_streak >= 7:
            self._award_badge(Badge.STREAK_7)
        if self._stats.streak.longest_streak >= 30:
            self._award_badge(Badge.STREAK_30)
    
    def _check_organization_badges(self):
        """Organizasyon rozetlerini kontrol et."""
        if self._stats.total_folders >= 10:
            self._award_badge(Badge.ORGANIZATION_MASTER)
    
    def _award_badge(self, badge: Badge):
        """Rozet ver."""
        if badge.value not in self._stats.badges_earned:
            self._stats.badges_earned.append(badge.value)
            self._stats.points += BADGE_INFO[badge]["points"]
            logger.info(f"Badge earned: {badge.value}")
    
    # ==================== FOCUS MODE / POMODORO ====================
    
    def start_focus_session(
        self, 
        duration_minutes: int = 25,
        break_minutes: int = 5,
        note_id: Optional[str] = None
    ) -> FocusSession:
        """Pomodoro odaklanma oturumu başlat."""
        import uuid
        session = FocusSession(
            session_id=str(uuid.uuid4()),
            start_time=datetime.now().isoformat(),
            duration_minutes=duration_minutes,
            break_minutes=break_minutes,
            note_id=note_id,
        )
        
        # Aktif oturumu kaydet
        self._save_active_session(session)
        
        return session
    
    def complete_focus_session(self, session_id: str, words_written: int = 0) -> Dict:
        """Oturumu tamamla."""
        session = self._get_active_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session.end_time = datetime.now().isoformat()
        session.completed = True
        session.words_written = words_written
        
        # İstatistikleri güncelle
        self._stats.total_pomodoros += 1
        self._stats.total_focus_minutes += session.duration_minutes
        
        # Rozet kontrolü
        if self._stats.total_pomodoros >= 10:
            self._award_badge(Badge.FOCUSED)
        
        self._save_stats()
        self._save_session_history(session)
        self._clear_active_session()
        
        return {
            "completed": True,
            "session": asdict(session),
            "total_pomodoros": self._stats.total_pomodoros,
            "total_focus_minutes": self._stats.total_focus_minutes,
        }
    
    def get_active_session(self) -> Optional[Dict]:
        """Aktif oturumu döndür."""
        try:
            active_file = self.data_dir / "active_session.json"
            if active_file.exists():
                with open(active_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _save_active_session(self, session: FocusSession):
        """Aktif oturumu kaydet."""
        try:
            active_file = self.data_dir / "active_session.json"
            with open(active_file, "w", encoding="utf-8") as f:
                json.dump(asdict(session), f)
        except Exception as e:
            logger.error(f"Save active session error: {e}")
    
    def _get_active_session(self, session_id: str) -> Optional[FocusSession]:
        """Aktif oturumu getir."""
        data = self.get_active_session()
        if data and data.get("session_id") == session_id:
            return FocusSession(**data)
        return None
    
    def _clear_active_session(self):
        """Aktif oturumu temizle."""
        try:
            active_file = self.data_dir / "active_session.json"
            if active_file.exists():
                active_file.unlink()
        except Exception:
            pass
    
    def _save_session_history(self, session: FocusSession):
        """Oturum geçmişine kaydet."""
        try:
            history = []
            if self.focus_file.exists():
                with open(self.focus_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            
            history.append(asdict(session))
            
            # Son 100 oturumu tut
            history = history[-100:]
            
            with open(self.focus_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Save session history error: {e}")
    
    # ==================== DAILY DIGEST ====================
    
    def get_daily_digest(self) -> Dict[str, Any]:
        """Günlük özet ve öneriler."""
        from core.notes_manager import notes_manager
        
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        notes = notes_manager._load_notes()
        
        # Bugün oluşturulan/düzenlenen notlar
        today_notes = []
        week_notes = []
        
        for note in notes:
            created = note.get("created_at", "")[:10]
            updated = note.get("updated_at", "")[:10]
            
            if created == today_str or updated == today_str:
                today_notes.append(note)
            
            if created >= week_ago or updated >= week_ago:
                week_notes.append(note)
        
        # İstatistikler
        stats = self.get_user_stats()
        streak_info = self.get_streak_info()
        
        # Motivasyon mesajı
        motivation = self._get_motivation_message(streak_info["current_streak"])
        
        # Öneri notları (en az ziyaret edilenler)
        suggestions = self._get_note_suggestions(notes)
        
        return {
            "date": today_str,
            "greeting": self._get_greeting(),
            "motivation": motivation,
            "today_stats": {
                "notes_created": len([n for n in today_notes if n.get("created_at", "")[:10] == today_str]),
                "notes_edited": len([n for n in today_notes if n.get("updated_at", "")[:10] == today_str]),
                "words_today": sum(len(n.get("content", "").split()) for n in today_notes),
            },
            "week_stats": {
                "total_notes": len(week_notes),
                "total_words": sum(len(n.get("content", "").split()) for n in week_notes),
                "most_active_day": self._get_most_active_day(week_notes),
            },
            "streak": streak_info,
            "level_info": {
                "level": stats["level"],
                "points": stats["points"],
                "progress": stats["level_progress"],
            },
            "suggestions": suggestions,
            "achievements": {
                "badges_count": len(stats["badges"]),
                "total_pomodoros": stats["total_pomodoros"],
                "focus_hours": round(stats["total_focus_minutes"] / 60, 1),
            }
        }
    
    def _get_greeting(self) -> str:
        """Günün zamanına göre selamlama."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "🌅 Günaydın!"
        elif 12 <= hour < 17:
            return "☀️ İyi günler!"
        elif 17 <= hour < 21:
            return "🌆 İyi akşamlar!"
        else:
            return "🌙 İyi geceler!"
    
    def _get_motivation_message(self, streak: int) -> str:
        """Motivasyon mesajı."""
        messages = [
            "Harika gidiyorsun! Her not, bir adım ileri.",
            "Düşüncelerini yazmak, zihnini özgürleştirir.",
            "Bugün hangi fikirleri yakalayacaksın?",
            "Tutarlılık başarının anahtarı.",
            "Not almak, öğrenmenin en güçlü yoludur.",
        ]
        
        if streak >= 7:
            return f"🔥 {streak} günlük serin devam ediyor! Muhteşemsin!"
        elif streak >= 3:
            return f"⚡ {streak} gündür yazıyorsun! Harika iş!"
        else:
            import random
            return random.choice(messages)
    
    def _get_note_suggestions(self, notes: List[Dict]) -> List[Dict]:
        """Öneri notları."""
        suggestions = []
        
        # Taslak notlar (kısa içerik)
        drafts = [n for n in notes if len(n.get("content", "").split()) < 20]
        if drafts:
            suggestions.append({
                "type": "incomplete",
                "title": "📝 Tamamlanmayı Bekleyen Notlar",
                "notes": [{"id": n["id"], "title": n["title"]} for n in drafts[:3]],
                "message": f"{len(drafts)} taslak notunuz var",
            })
        
        # Bağlantısız notlar
        orphans = [n for n in notes if "[[" not in n.get("content", "")]
        if len(orphans) > 5:
            suggestions.append({
                "type": "unlinked",
                "title": "🔗 Bağlantı Eklenebilecek Notlar",
                "notes": [{"id": n["id"], "title": n["title"]} for n in orphans[:3]],
                "message": f"{len(orphans)} not henüz bağlı değil",
            })
        
        return suggestions
    
    def _get_most_active_day(self, notes: List[Dict]) -> str:
        """En aktif günü bul."""
        from collections import Counter
        days = []
        for note in notes:
            date_str = note.get("created_at", note.get("updated_at", ""))[:10]
            if date_str:
                try:
                    day = datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
                    days.append(day)
                except Exception:
                    pass
        
        if days:
            most_common = Counter(days).most_common(1)
            if most_common:
                return most_common[0][0]
        return "N/A"


# Singleton instance
_premium_manager: Optional[NotesPremiumManager] = None


def get_premium_manager() -> NotesPremiumManager:
    """Premium manager singleton."""
    global _premium_manager
    if _premium_manager is None:
        _premium_manager = NotesPremiumManager()
    return _premium_manager
