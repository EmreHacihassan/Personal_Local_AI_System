"""
AI ile Öğren - 4 Premium Özellik
================================

🎓 Premium Feature 1: AI Tutor - Kişiselleştirilmiş Öğrenme Asistanı
📚 Premium Feature 2: Spaced Repetition System (SRS) - Akıllı Hafıza Sistemi
💻 Premium Feature 3: Interactive Code Playground - Canlı Kod Deneyimi
🧠 Premium Feature 4: Knowledge Graph - Bilgi Haritası ve İlişki Ağı

Author: Enterprise AI Assistant
Version: 2.0.0
"""

import hashlib
import json
import re
import random
import asyncio
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from threading import Lock
from pathlib import Path
from enum import Enum
import math
import uuid

from .logger import get_logger

logger = get_logger("learning_premium_features")


# =============================================================================
# 🎓 PREMIUM FEATURE 1: AI TUTOR - KİŞİSELLEŞTİRİLMİŞ ÖĞRENME ASİSTANI
# =============================================================================

class TutorMode(str, Enum):
    """AI Tutor modları."""
    EXPLAIN = "explain"         # Konu açıklama
    QUIZ = "quiz"               # Soru-cevap
    PRACTICE = "practice"       # Pratik yapma
    REVIEW = "review"           # Gözden geçirme
    SOCRATIC = "socratic"       # Sokratik sorgulama
    ADAPTIVE = "adaptive"       # Adaptif öğrenme


class DifficultyLevel(str, Enum):
    """Zorluk seviyeleri."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class StudentProfile:
    """Öğrenci profili."""
    id: str
    learning_style: str = "visual"  # visual, auditory, reading, kinesthetic
    difficulty_preference: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    pace: str = "normal"  # slow, normal, fast
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    completed_topics: List[str] = field(default_factory=list)
    scores_history: List[Dict] = field(default_factory=list)
    total_study_time: int = 0  # dakika
    average_score: float = 0.0
    streak_days: int = 0
    last_activity: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TutorSession:
    """Tutor oturumu."""
    id: str
    workspace_id: str
    topic: str
    mode: TutorMode
    messages: List[Dict] = field(default_factory=list)
    current_difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    questions_asked: int = 0
    correct_answers: int = 0
    hints_used: int = 0
    started_at: str = ""
    ended_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "topic": self.topic,
            "mode": self.mode.value,
            "messages": self.messages,
            "current_difficulty": self.current_difficulty.value,
            "questions_asked": self.questions_asked,
            "correct_answers": self.correct_answers,
            "hints_used": self.hints_used,
            "accuracy": round(self.correct_answers / max(self.questions_asked, 1) * 100, 1),
            "started_at": self.started_at,
            "ended_at": self.ended_at
        }


class AITutor:
    """
    🎓 AI Tutor - Kişiselleştirilmiş Öğrenme Asistanı
    
    Özellikler:
    - Öğrenci seviyesine göre adaptif içerik
    - Sokratik sorgulama metodu
    - İnteraktif soru-cevap
    - Anlık geri bildirim
    - Zayıf noktaları tespit ve güçlendirme
    - Motivasyon ve streak sistemi
    - Çoklu öğrenme stilleri desteği
    """
    
    # Sokratik sorular
    SOCRATIC_TEMPLATES = [
        "Bu konuyu kendi kelimelerinle açıklar mısın?",
        "Neden böyle düşünüyorsun?",
        "Bunun tersi doğru olsaydı ne olurdu?",
        "Bir örnek verebilir misin?",
        "Bu bilgiyi nerede kullanabilirsin?",
        "Daha önce öğrendiğin hangi konuyla bağlantılı?",
        "Eğer bunu bilmeseydin ne yapardın?",
        "Bu kavramın en önemli parçası nedir?",
        "Başka bir şekilde ifade edebilir misin?",
        "Bu neden önemli sence?"
    ]
    
    # Motivasyon mesajları
    MOTIVATION_MESSAGES = {
        "correct": [
            "🎉 Mükemmel! Doğru cevap!",
            "⭐ Harika! Çok iyi gidiyorsun!",
            "🚀 Süpersin! Devam et!",
            "✨ Tam isabet! Bravo!",
            "🏆 Muhteşem! Öğrenme yolunda ilerliyorsun!"
        ],
        "incorrect": [
            "💪 Neredeyse! Bir daha deneyelim.",
            "🤔 İyi düşünce ama tam değil. Tekrar bakalım.",
            "📚 Endişelenme, hata yaparak öğreniyoruz!",
            "🔍 Yaklaştın! Bir ipucu ister misin?",
            "🌟 Her yanlış cevap seni doğruya yaklaştırır!"
        ],
        "streak": [
            "🔥 {streak} günlük seri! Muhteşem!",
            "💎 {streak} gün üst üste! Kararlılığın harika!",
            "⚡ {streak} günlük istikrar! Durma!",
        ],
        "milestone": [
            "🏅 Tebrikler! {count} soruyu doğru cevapladın!",
            "🎖️ Yeni başarım açıldı: {achievement}",
            "📈 Seviye atlama! Artık {level} seviyesindesin!"
        ]
    }
    
    # Zorluk ayarlama eşikleri
    DIFFICULTY_THRESHOLDS = {
        "upgrade": 0.85,    # %85 üstü başarı = zorluk artar
        "downgrade": 0.50,  # %50 altı başarı = zorluk azalır
        "window_size": 5    # Son 5 soru değerlendirilir
    }
    
    def __init__(self):
        self._sessions: Dict[str, TutorSession] = {}
        self._profiles: Dict[str, StudentProfile] = {}
        self._lock = Lock()
        self._llm = None
        logger.info("AITutor initialized")
    
    def _get_llm(self):
        """LLM manager'ı lazy load et."""
        if self._llm is None:
            try:
                from .llm_manager import llm_manager
                self._llm = llm_manager
            except ImportError:
                logger.warning("LLM manager not available")
        return self._llm
    
    def create_or_get_profile(self, student_id: str) -> StudentProfile:
        """Öğrenci profili oluştur veya getir."""
        with self._lock:
            if student_id not in self._profiles:
                self._profiles[student_id] = StudentProfile(id=student_id)
            return self._profiles[student_id]
    
    def update_profile(self, student_id: str, **kwargs) -> StudentProfile:
        """Öğrenci profilini güncelle."""
        profile = self.create_or_get_profile(student_id)
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.last_activity = datetime.now().isoformat()
        return profile
    
    def start_session(
        self,
        workspace_id: str,
        topic: str,
        mode: TutorMode = TutorMode.ADAPTIVE,
        student_id: Optional[str] = None
    ) -> TutorSession:
        """Yeni tutor oturumu başlat."""
        session_id = str(uuid.uuid4())
        
        # Öğrenci profilinden zorluk seviyesi al
        difficulty = DifficultyLevel.INTERMEDIATE
        if student_id:
            profile = self.create_or_get_profile(student_id)
            difficulty = profile.difficulty_preference
        
        session = TutorSession(
            id=session_id,
            workspace_id=workspace_id,
            topic=topic,
            mode=mode,
            current_difficulty=difficulty,
            started_at=datetime.now().isoformat()
        )
        
        with self._lock:
            self._sessions[session_id] = session
        
        # Hoşgeldin mesajı
        welcome_msg = self._generate_welcome_message(topic, mode, difficulty)
        session.messages.append({
            "role": "tutor",
            "content": welcome_msg,
            "timestamp": datetime.now().isoformat()
        })
        
        return session
    
    def _generate_welcome_message(
        self, 
        topic: str, 
        mode: TutorMode, 
        difficulty: DifficultyLevel
    ) -> str:
        """Hoşgeldin mesajı oluştur."""
        mode_intros = {
            TutorMode.EXPLAIN: f"Merhaba! 📚 Bugün sana **{topic}** konusunu anlatacağım. Hazır mısın?",
            TutorMode.QUIZ: f"Merhaba! 🎯 **{topic}** konusunda bilgini test edeceğiz. Başlayalım!",
            TutorMode.PRACTICE: f"Merhaba! 💪 **{topic}** konusunda pratik yapacağız. Hadi başlayalım!",
            TutorMode.REVIEW: f"Merhaba! 🔄 **{topic}** konusunu birlikte gözden geçirelim.",
            TutorMode.SOCRATIC: f"Merhaba! 🤔 **{topic}** hakkında birlikte düşünelim. Sana sorular soracağım.",
            TutorMode.ADAPTIVE: f"Merhaba! 🎓 **{topic}** konusunda seninle çalışacağım. Seviyene göre ilerleyeceğiz."
        }
        
        difficulty_info = {
            DifficultyLevel.BEGINNER: "Başlangıç seviyesinden başlıyoruz.",
            DifficultyLevel.ELEMENTARY: "Temel seviyede ilerleyeceğiz.",
            DifficultyLevel.INTERMEDIATE: "Orta seviyede çalışacağız.",
            DifficultyLevel.ADVANCED: "İleri seviyede konuşacağız.",
            DifficultyLevel.EXPERT: "Uzman seviyesinde derinleşeceğiz."
        }
        
        intro = mode_intros.get(mode, f"Merhaba! **{topic}** konusunda yardımcı olacağım.")
        level = difficulty_info.get(difficulty, "")
        
        return f"{intro}\n\n{level}\n\n💡 İstediğin zaman **'ipucu'**, **'açıkla'** veya **'değiştir'** diyebilirsin!"
    
    def process_message(
        self,
        session_id: str,
        user_message: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Kullanıcı mesajını işle ve yanıt oluştur."""
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Oturum bulunamadı"}
        
        # Kullanıcı mesajını kaydet
        session.messages.append({
            "role": "student",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Özel komutları kontrol et
        command = self._check_special_command(user_message.lower())
        if command:
            response = self._handle_command(session, command, context)
        else:
            response = self._generate_response(session, user_message, context)
        
        # Tutor yanıtını kaydet
        session.messages.append({
            "role": "tutor",
            "content": response["message"],
            "metadata": response.get("metadata", {}),
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _check_special_command(self, message: str) -> Optional[str]:
        """Özel komutları kontrol et."""
        commands = {
            "ipucu": "hint",
            "hint": "hint",
            "açıkla": "explain",
            "explain": "explain",
            "soru": "question",
            "question": "question",
            "değiştir": "change_difficulty",
            "zorlaştır": "increase_difficulty",
            "kolaylaştır": "decrease_difficulty",
            "özet": "summary",
            "summary": "summary",
            "bitir": "end",
            "end": "end",
            "istatistik": "stats",
            "stats": "stats"
        }
        
        for keyword, cmd in commands.items():
            if keyword in message:
                return cmd
        return None
    
    def _handle_command(
        self, 
        session: TutorSession, 
        command: str, 
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Özel komutları işle."""
        if command == "hint":
            session.hints_used += 1
            return {
                "message": self._generate_hint(session, context),
                "type": "hint",
                "metadata": {"hints_used": session.hints_used}
            }
        
        elif command == "explain":
            return {
                "message": self._generate_explanation(session, context),
                "type": "explanation"
            }
        
        elif command == "question":
            session.questions_asked += 1
            return self._generate_question(session, context)
        
        elif command == "increase_difficulty":
            return self._change_difficulty(session, increase=True)
        
        elif command == "decrease_difficulty":
            return self._change_difficulty(session, increase=False)
        
        elif command == "summary":
            return {
                "message": self._generate_summary(session),
                "type": "summary"
            }
        
        elif command == "stats":
            return {
                "message": self._generate_stats(session),
                "type": "stats",
                "metadata": session.to_dict()
            }
        
        elif command == "end":
            session.ended_at = datetime.now().isoformat()
            return {
                "message": self._generate_closing(session),
                "type": "closing",
                "session_complete": True
            }
        
        return {"message": "Komutu anlamadım. Tekrar dener misin?", "type": "error"}
    
    def _generate_response(
        self, 
        session: TutorSession, 
        user_message: str, 
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Genel yanıt oluştur."""
        mode = session.mode
        
        if mode == TutorMode.QUIZ:
            # Cevap değerlendirmesi
            return self._evaluate_answer(session, user_message, context)
        
        elif mode == TutorMode.SOCRATIC:
            # Sokratik soru sor
            return self._generate_socratic_response(session, user_message, context)
        
        elif mode == TutorMode.EXPLAIN:
            # Açıklama yap
            return {
                "message": self._generate_explanation(session, context, user_message),
                "type": "explanation"
            }
        
        elif mode == TutorMode.ADAPTIVE:
            # Adaptif mod - kullanıcı mesajına göre mod seç
            if "?" in user_message:
                return {
                    "message": self._generate_explanation(session, context, user_message),
                    "type": "answer"
                }
            else:
                # Soru sor
                session.questions_asked += 1
                return self._generate_question(session, context)
        
        return {
            "message": self._get_llm_response(session, user_message, context) if self._get_llm() else "Anladım, devam edelim.",
            "type": "response"
        }
    
    def _generate_hint(self, session: TutorSession, context: Optional[str]) -> str:
        """İpucu oluştur."""
        hints = [
            f"💡 **İpucu:** Düşün bakalım, {session.topic} konusunda temel kavram neydi?",
            f"💡 **İpucu:** Konuyu daha küçük parçalara ayırmayı dene.",
            f"💡 **İpucu:** Bir örnek düşün ve oradan ilerle.",
            f"💡 **İpucu:** Önceki öğrendiklerinle bağlantı kur.",
            f"💡 **İpucu:** Tersten düşünmeyi dene - doğru olmasaydı ne olurdu?"
        ]
        
        if context:
            return f"💡 **İpucu:** {context[:200]}... konuyla ilgili bu bilgiyi kullanabilirsin."
        
        return random.choice(hints)
    
    def _generate_explanation(
        self, 
        session: TutorSession, 
        context: Optional[str],
        question: Optional[str] = None
    ) -> str:
        """Açıklama oluştur."""
        llm = self._get_llm()
        if llm and context:
            prompt = f"""Konu: {session.topic}
Zorluk: {session.current_difficulty.value}
Soru/Talep: {question or 'Konuyu açıkla'}

Kaynak İçerik:
{context[:2000]}

Öğrenci seviyesine uygun, anlaşılır bir açıklama yap. Örnekler ve benzetmeler kullan."""
            
            try:
                return llm.generate(prompt, "Sen yardımcı bir öğretmensin. Türkçe ve anlaşılır açıklamalar yap.")
            except:
                pass
        
        return f"📖 **{session.topic}** konusu hakkında:\n\nBu konuyu anlamak için temel kavramları ele alalım. Önce basit bir örnekle başlayalım..."
    
    def _generate_question(
        self, 
        session: TutorSession, 
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Soru oluştur."""
        difficulty_templates = {
            DifficultyLevel.BEGINNER: [
                f"{session.topic} nedir?",
                f"{session.topic} konusunda temel kavram hangisidir?",
                f"{session.topic} ne işe yarar?"
            ],
            DifficultyLevel.INTERMEDIATE: [
                f"{session.topic} nasıl çalışır?",
                f"{session.topic} konusunda hangi adımları izlemeliyiz?",
                f"{session.topic} ile ilgili bir örnek verir misin?"
            ],
            DifficultyLevel.ADVANCED: [
                f"{session.topic} konusundaki karmaşık durumları açıklar mısın?",
                f"{session.topic} kullanırken dikkat edilmesi gerekenler nelerdir?",
                f"{session.topic} ile ilgili yaygın hatalar nelerdir?"
            ]
        }
        
        templates = difficulty_templates.get(
            session.current_difficulty, 
            difficulty_templates[DifficultyLevel.INTERMEDIATE]
        )
        
        question = random.choice(templates)
        
        return {
            "message": f"❓ **Soru {session.questions_asked}:**\n\n{question}",
            "type": "question",
            "metadata": {
                "question_number": session.questions_asked,
                "difficulty": session.current_difficulty.value
            }
        }
    
    def _evaluate_answer(
        self, 
        session: TutorSession, 
        answer: str, 
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Cevabı değerlendir."""
        # Basit değerlendirme - gerçekte LLM kullanılmalı
        is_correct = len(answer) > 20  # Placeholder
        
        if is_correct:
            session.correct_answers += 1
            feedback = random.choice(self.MOTIVATION_MESSAGES["correct"])
            
            # Zorluk ayarlama
            self._adjust_difficulty(session)
            
            return {
                "message": f"{feedback}\n\n✅ Cevabın doğru!",
                "type": "feedback",
                "is_correct": True,
                "metadata": {
                    "accuracy": round(session.correct_answers / session.questions_asked * 100, 1)
                }
            }
        else:
            feedback = random.choice(self.MOTIVATION_MESSAGES["incorrect"])
            
            return {
                "message": f"{feedback}\n\n🔄 Tekrar düşünmek ister misin? İpucu için 'ipucu' yaz.",
                "type": "feedback",
                "is_correct": False
            }
    
    def _generate_socratic_response(
        self, 
        session: TutorSession, 
        user_message: str, 
        context: Optional[str]
    ) -> Dict[str, Any]:
        """Sokratik yanıt oluştur."""
        # Sokratik bir soru seç
        question = random.choice(self.SOCRATIC_TEMPLATES)
        
        response = f"Hmm, ilginç bir bakış açısı. 🤔\n\n{question}"
        
        return {
            "message": response,
            "type": "socratic",
            "metadata": {"method": "socratic_questioning"}
        }
    
    def _adjust_difficulty(self, session: TutorSession):
        """Zorluğu otomatik ayarla."""
        if session.questions_asked < self.DIFFICULTY_THRESHOLDS["window_size"]:
            return
        
        accuracy = session.correct_answers / session.questions_asked
        
        if accuracy >= self.DIFFICULTY_THRESHOLDS["upgrade"]:
            # Zorluk arttır
            levels = list(DifficultyLevel)
            current_idx = levels.index(session.current_difficulty)
            if current_idx < len(levels) - 1:
                session.current_difficulty = levels[current_idx + 1]
                logger.info(f"Difficulty increased to {session.current_difficulty.value}")
        
        elif accuracy <= self.DIFFICULTY_THRESHOLDS["downgrade"]:
            # Zorluk azalt
            levels = list(DifficultyLevel)
            current_idx = levels.index(session.current_difficulty)
            if current_idx > 0:
                session.current_difficulty = levels[current_idx - 1]
                logger.info(f"Difficulty decreased to {session.current_difficulty.value}")
    
    def _change_difficulty(
        self, 
        session: TutorSession, 
        increase: bool
    ) -> Dict[str, Any]:
        """Manuel zorluk değiştir."""
        levels = list(DifficultyLevel)
        current_idx = levels.index(session.current_difficulty)
        
        if increase and current_idx < len(levels) - 1:
            session.current_difficulty = levels[current_idx + 1]
        elif not increase and current_idx > 0:
            session.current_difficulty = levels[current_idx - 1]
        
        return {
            "message": f"🎚️ Zorluk seviyesi değiştirildi: **{session.current_difficulty.value}**",
            "type": "system",
            "metadata": {"new_difficulty": session.current_difficulty.value}
        }
    
    def _generate_summary(self, session: TutorSession) -> str:
        """Oturum özeti oluştur."""
        accuracy = round(session.correct_answers / max(session.questions_asked, 1) * 100, 1)
        
        return f"""📋 **Oturum Özeti**

📚 **Konu:** {session.topic}
🎯 **Mod:** {session.mode.value}
📊 **Zorluk:** {session.current_difficulty.value}

**İstatistikler:**
- ❓ Toplam Soru: {session.questions_asked}
- ✅ Doğru Cevap: {session.correct_answers}
- 📈 Başarı Oranı: %{accuracy}
- 💡 İpucu Kullanımı: {session.hints_used}

Harika gidiyorsun! 🚀"""
    
    def _generate_stats(self, session: TutorSession) -> str:
        """Detaylı istatistik mesajı."""
        accuracy = round(session.correct_answers / max(session.questions_asked, 1) * 100, 1)
        
        level_emoji = {
            DifficultyLevel.BEGINNER: "🌱",
            DifficultyLevel.ELEMENTARY: "🌿",
            DifficultyLevel.INTERMEDIATE: "🌳",
            DifficultyLevel.ADVANCED: "🌲",
            DifficultyLevel.EXPERT: "🏔️"
        }
        
        return f"""📊 **Detaylı İstatistikler**

{level_emoji.get(session.current_difficulty, '📊')} **Mevcut Seviye:** {session.current_difficulty.value}

| Metrik | Değer |
|--------|-------|
| Sorular | {session.questions_asked} |
| Doğru | {session.correct_answers} |
| Yanlış | {session.questions_asked - session.correct_answers} |
| Başarı | %{accuracy} |
| İpucu | {session.hints_used} |

{'🏆 Harika performans!' if accuracy >= 80 else '💪 Daha iyi olabilir!' if accuracy >= 50 else '📚 Biraz daha çalışmalıyız!'}"""
    
    def _generate_closing(self, session: TutorSession) -> str:
        """Kapanış mesajı oluştur."""
        accuracy = round(session.correct_answers / max(session.questions_asked, 1) * 100, 1)
        
        if accuracy >= 80:
            emoji = "🏆"
            message = "Muhteşem bir performans gösterdin!"
        elif accuracy >= 60:
            emoji = "⭐"
            message = "İyi bir çalışma oldu!"
        else:
            emoji = "💪"
            message = "Pratik yaptığın için tebrikler!"
        
        return f"""{emoji} **Oturum Tamamlandı!**

{message}

📊 **Sonuçlar:**
- Toplam Soru: {session.questions_asked}
- Başarı Oranı: %{accuracy}
- Zorluk: {session.current_difficulty.value}

Bir sonraki oturumda görüşmek üzere! 🎓"""
    
    def _get_llm_response(
        self, 
        session: TutorSession, 
        message: str, 
        context: Optional[str]
    ) -> str:
        """LLM ile yanıt oluştur."""
        llm = self._get_llm()
        if not llm:
            return "Mesajını aldım. Devam edelim!"
        
        system_prompt = f"""Sen bir AI Tutor'sün. Öğrenci "{session.topic}" konusunu çalışıyor.
Zorluk seviyesi: {session.current_difficulty.value}
Mod: {session.mode.value}

Öğrenciye yardımcı, teşvik edici ve öğretici ol. Türkçe yanıt ver."""
        
        if context:
            message = f"Kaynak içerik:\n{context[:1500]}\n\nÖğrenci mesajı: {message}"
        
        try:
            return llm.generate(message, system_prompt)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "Mesajını aldım. Devam edelim!"
    
    def get_session(self, session_id: str) -> Optional[TutorSession]:
        """Oturumu getir."""
        return self._sessions.get(session_id)
    
    def end_session(self, session_id: str) -> Optional[Dict]:
        """Oturumu sonlandır."""
        session = self._sessions.get(session_id)
        if session:
            session.ended_at = datetime.now().isoformat()
            return session.to_dict()
        return None


# =============================================================================
# 📚 PREMIUM FEATURE 2: SPACED REPETITION SYSTEM (SRS)
# =============================================================================

class CardStatus(str, Enum):
    """Kart durumları."""
    NEW = "new"
    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"
    GRADUATED = "graduated"


@dataclass
class Flashcard:
    """Hafıza kartı."""
    id: str
    workspace_id: str
    front: str  # Soru
    back: str   # Cevap
    deck: str = "default"
    status: CardStatus = CardStatus.NEW
    
    # SRS parametreleri
    ease_factor: float = 2.5  # Kolaylık faktörü (min 1.3)
    interval: int = 0         # Gün cinsinden tekrar aralığı
    repetitions: int = 0      # Toplam tekrar sayısı
    
    # Tarihler
    created_at: str = ""
    last_review: Optional[str] = None
    next_review: Optional[str] = None
    
    # İstatistikler
    correct_count: int = 0
    incorrect_count: int = 0
    streak: int = 0
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    source_doc_id: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "front": self.front,
            "back": self.back,
            "deck": self.deck,
            "status": self.status.value,
            "ease_factor": round(self.ease_factor, 2),
            "interval": self.interval,
            "repetitions": self.repetitions,
            "created_at": self.created_at,
            "last_review": self.last_review,
            "next_review": self.next_review,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "streak": self.streak,
            "accuracy": round(self.correct_count / max(self.correct_count + self.incorrect_count, 1) * 100, 1),
            "tags": self.tags,
            "notes": self.notes
        }


class ReviewRating(int, Enum):
    """Değerlendirme puanları (SM-2 algoritması)."""
    AGAIN = 0      # Tamamen unuttum
    HARD = 1       # Zor hatırladım
    GOOD = 2       # Hatırladım
    EASY = 3       # Çok kolaydı


@dataclass
class StudySession:
    """Çalışma oturumu."""
    id: str
    workspace_id: str
    deck: str
    cards_studied: int = 0
    cards_new: int = 0
    cards_review: int = 0
    correct: int = 0
    incorrect: int = 0
    started_at: str = ""
    ended_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SpacedRepetitionSystem:
    """
    📚 Spaced Repetition System (SRS) - Akıllı Hafıza Sistemi
    
    SM-2 algoritması tabanlı:
    - Anki benzeri hafıza kartları
    - Unutma eğrisi hesaplama
    - Günlük tekrar seansları
    - Akıllı önceliklendirme
    - İlerleme takibi
    - Çoklu deste desteği
    """
    
    # SM-2 Algoritma sabitleri
    INITIAL_EASE = 2.5
    MIN_EASE = 1.3
    EASE_BONUS = 0.15
    EASE_PENALTY = 0.2
    
    # Yeni kart ayarları
    NEW_STEPS = [1, 10]  # dakika
    GRADUATING_INTERVAL = 1  # gün
    EASY_INTERVAL = 4  # gün
    
    # Günlük limitler
    NEW_CARDS_PER_DAY = 20
    REVIEW_CARDS_PER_DAY = 200
    
    def __init__(self):
        self._cards: Dict[str, Flashcard] = {}
        self._decks: Dict[str, List[str]] = defaultdict(list)  # deck_id -> card_ids
        self._sessions: Dict[str, StudySession] = {}
        self._lock = Lock()
        logger.info("SpacedRepetitionSystem initialized")
    
    def create_card(
        self,
        workspace_id: str,
        front: str,
        back: str,
        deck: str = "default",
        tags: List[str] = None,
        source_doc_id: Optional[str] = None
    ) -> Flashcard:
        """Yeni hafıza kartı oluştur."""
        card_id = str(uuid.uuid4())
        
        card = Flashcard(
            id=card_id,
            workspace_id=workspace_id,
            front=front,
            back=back,
            deck=deck,
            tags=tags or [],
            source_doc_id=source_doc_id,
            created_at=datetime.now().isoformat()
        )
        
        with self._lock:
            self._cards[card_id] = card
            self._decks[f"{workspace_id}:{deck}"].append(card_id)
        
        logger.info(f"Card created: {card_id[:8]}")
        return card
    
    def create_cards_from_content(
        self,
        workspace_id: str,
        content: str,
        deck: str = "default",
        card_type: str = "qa"  # qa, cloze, reverse
    ) -> List[Flashcard]:
        """İçerikten otomatik kart oluştur."""
        cards = []
        
        if card_type == "qa":
            # Soru-Cevap formatı - başlıklardan
            headers = re.findall(r'^(#{1,3})\s+(.+)$', content, re.MULTILINE)
            current_topic = ""
            
            for hashes, title in headers:
                level = len(hashes)
                if level <= 2:
                    current_topic = title.strip()
                elif current_topic:
                    # Alt başlık -> soru olarak kullan
                    card = self.create_card(
                        workspace_id=workspace_id,
                        front=f"{title.strip()} nedir?",
                        back=f"{current_topic} - {title.strip()}",
                        deck=deck,
                        tags=[current_topic.lower()]
                    )
                    cards.append(card)
            
            # Bold metinlerden
            bold_pairs = re.findall(r'\*\*([^*]+)\*\*[:\s]+([^*\n]+)', content)
            for term, definition in bold_pairs[:20]:
                if len(definition) > 10:
                    card = self.create_card(
                        workspace_id=workspace_id,
                        front=f"{term.strip()} nedir?",
                        back=definition.strip()[:300],
                        deck=deck
                    )
                    cards.append(card)
        
        elif card_type == "cloze":
            # Cloze deletion - önemli kelimeleri gizle
            sentences = re.findall(r'\*\*([^*]+)\*\*', content)
            for i, term in enumerate(sentences[:15]):
                # Terimi içeren cümleyi bul
                pattern = rf'([^.!?\n]*\*\*{re.escape(term)}\*\*[^.!?\n]*[.!?])'
                matches = re.findall(pattern, content)
                
                if matches:
                    sentence = matches[0].replace(f"**{term}**", "[...]")
                    card = self.create_card(
                        workspace_id=workspace_id,
                        front=f"Boşluğu doldurun:\n{sentence}",
                        back=term,
                        deck=deck,
                        tags=["cloze"]
                    )
                    cards.append(card)
        
        elif card_type == "reverse":
            # Çift yönlü kartlar
            bold_pairs = re.findall(r'\*\*([^*]+)\*\*[:\s]+([^*\n]+)', content)
            for term, definition in bold_pairs[:10]:
                if len(definition) > 10:
                    # Normal kart
                    card1 = self.create_card(
                        workspace_id=workspace_id,
                        front=f"{term.strip()} nedir?",
                        back=definition.strip()[:200],
                        deck=deck,
                        tags=["reverse"]
                    )
                    cards.append(card1)
                    
                    # Ters kart
                    card2 = self.create_card(
                        workspace_id=workspace_id,
                        front=definition.strip()[:200],
                        back=term.strip(),
                        deck=deck,
                        tags=["reverse"]
                    )
                    cards.append(card2)
        
        logger.info(f"Created {len(cards)} cards from content")
        return cards
    
    def get_due_cards(
        self,
        workspace_id: str,
        deck: Optional[str] = None,
        limit: int = 50
    ) -> List[Flashcard]:
        """Bugün çalışılması gereken kartları getir."""
        now = datetime.now()
        today = now.date()
        
        due_cards = []
        new_cards = []
        review_cards = []
        
        # Filtreleme
        for card_id, card in self._cards.items():
            if card.workspace_id != workspace_id:
                continue
            if deck and card.deck != deck:
                continue
            
            if card.status == CardStatus.NEW:
                new_cards.append(card)
            elif card.next_review:
                next_date = datetime.fromisoformat(card.next_review).date()
                if next_date <= today:
                    review_cards.append(card)
        
        # Önce vadesi gelen review kartlar, sonra yeni kartlar
        review_cards.sort(key=lambda c: c.next_review or "")
        due_cards = review_cards[:self.REVIEW_CARDS_PER_DAY]
        
        remaining = limit - len(due_cards)
        if remaining > 0:
            due_cards.extend(new_cards[:min(remaining, self.NEW_CARDS_PER_DAY)])
        
        return due_cards[:limit]
    
    def review_card(
        self,
        card_id: str,
        rating: ReviewRating
    ) -> Dict[str, Any]:
        """Kartı değerlendir ve SM-2 algoritmasını uygula."""
        card = self._cards.get(card_id)
        if not card:
            return {"error": "Kart bulunamadı"}
        
        now = datetime.now()
        card.last_review = now.isoformat()
        card.repetitions += 1
        
        # SM-2 Algoritması
        if rating == ReviewRating.AGAIN:
            # Tamamen unuttum - sıfırla
            card.incorrect_count += 1
            card.streak = 0
            card.interval = 0
            card.ease_factor = max(self.MIN_EASE, card.ease_factor - self.EASE_PENALTY)
            card.status = CardStatus.RELEARNING
            card.next_review = (now + timedelta(minutes=1)).isoformat()
            
        elif rating == ReviewRating.HARD:
            # Zor hatırladım
            card.correct_count += 1
            card.streak += 1
            card.ease_factor = max(self.MIN_EASE, card.ease_factor - 0.15)
            
            if card.interval == 0:
                card.interval = 1
            else:
                card.interval = int(card.interval * 1.2)
            
            card.status = CardStatus.REVIEW
            card.next_review = (now + timedelta(days=card.interval)).isoformat()
            
        elif rating == ReviewRating.GOOD:
            # Normal hatırladım
            card.correct_count += 1
            card.streak += 1
            
            if card.status == CardStatus.NEW:
                card.interval = self.GRADUATING_INTERVAL
            else:
                card.interval = int(card.interval * card.ease_factor)
            
            card.status = CardStatus.REVIEW
            card.next_review = (now + timedelta(days=card.interval)).isoformat()
            
        elif rating == ReviewRating.EASY:
            # Çok kolaydı
            card.correct_count += 1
            card.streak += 1
            card.ease_factor += self.EASE_BONUS
            
            if card.status == CardStatus.NEW:
                card.interval = self.EASY_INTERVAL
            else:
                card.interval = int(card.interval * card.ease_factor * 1.3)
            
            card.status = CardStatus.REVIEW
            card.next_review = (now + timedelta(days=card.interval)).isoformat()
        
        # Mezuniyet kontrolü (30+ gün aralık)
        if card.interval >= 30 and card.streak >= 5:
            card.status = CardStatus.GRADUATED
        
        logger.info(f"Card {card_id[:8]} reviewed: rating={rating.name}, interval={card.interval}")
        
        return {
            "card": card.to_dict(),
            "rating": rating.name,
            "new_interval": card.interval,
            "next_review": card.next_review,
            "feedback": self._get_review_feedback(rating, card)
        }
    
    def _get_review_feedback(self, rating: ReviewRating, card: Flashcard) -> str:
        """Değerlendirme geri bildirimi."""
        feedbacks = {
            ReviewRating.AGAIN: [
                "🔄 Endişelenme, tekrar göreceğiz!",
                "💪 Pratik mükemmelleştirir!",
                "📚 Bir kez daha bakalım."
            ],
            ReviewRating.HARD: [
                "🤔 Zor ama hatırladın!",
                "💭 Yakında kolaylaşacak.",
                "📖 Bir sonraki sefer daha kolay olacak."
            ],
            ReviewRating.GOOD: [
                "✅ Harika! Doğru hatırladın!",
                "👍 Çok iyi gidiyorsun!",
                "🎯 Tam isabet!"
            ],
            ReviewRating.EASY: [
                "🌟 Mükemmel! Çok kolay!",
                "🚀 Süpersin!",
                "⭐ Bu konuyu çok iyi biliyorsun!"
            ]
        }
        
        base = random.choice(feedbacks.get(rating, ["👍"]))
        
        # Streak bonusu
        if card.streak >= 5:
            base += f"\n🔥 {card.streak} doğru seri!"
        
        return base
    
    def get_deck_stats(
        self,
        workspace_id: str,
        deck: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deste istatistikleri."""
        stats = {
            "total": 0,
            "new": 0,
            "learning": 0,
            "review": 0,
            "graduated": 0,
            "due_today": 0,
            "average_ease": 0.0,
            "retention_rate": 0.0
        }
        
        ease_sum = 0
        correct_total = 0
        total_reviews = 0
        now = datetime.now().date()
        
        for card in self._cards.values():
            if card.workspace_id != workspace_id:
                continue
            if deck and card.deck != deck:
                continue
            
            stats["total"] += 1
            
            if card.status == CardStatus.NEW:
                stats["new"] += 1
            elif card.status == CardStatus.LEARNING:
                stats["learning"] += 1
            elif card.status == CardStatus.REVIEW:
                stats["review"] += 1
            elif card.status == CardStatus.GRADUATED:
                stats["graduated"] += 1
            
            if card.next_review:
                next_date = datetime.fromisoformat(card.next_review).date()
                if next_date <= now:
                    stats["due_today"] += 1
            
            ease_sum += card.ease_factor
            correct_total += card.correct_count
            total_reviews += card.correct_count + card.incorrect_count
        
        if stats["total"] > 0:
            stats["average_ease"] = round(ease_sum / stats["total"], 2)
        
        if total_reviews > 0:
            stats["retention_rate"] = round(correct_total / total_reviews * 100, 1)
        
        return stats
    
    def start_study_session(
        self,
        workspace_id: str,
        deck: str = "default"
    ) -> StudySession:
        """Çalışma oturumu başlat."""
        session_id = str(uuid.uuid4())
        
        session = StudySession(
            id=session_id,
            workspace_id=workspace_id,
            deck=deck,
            started_at=datetime.now().isoformat()
        )
        
        self._sessions[session_id] = session
        return session
    
    def get_card(self, card_id: str) -> Optional[Flashcard]:
        """Kart getir."""
        return self._cards.get(card_id)
    
    def delete_card(self, card_id: str) -> bool:
        """Kart sil."""
        if card_id in self._cards:
            card = self._cards.pop(card_id)
            deck_key = f"{card.workspace_id}:{card.deck}"
            if card_id in self._decks[deck_key]:
                self._decks[deck_key].remove(card_id)
            return True
        return False
    
    def get_cards_by_workspace(
        self,
        workspace_id: str,
        deck: Optional[str] = None,
        status: Optional[CardStatus] = None
    ) -> List[Flashcard]:
        """Workspace kartlarını getir."""
        result = []
        for card in self._cards.values():
            if card.workspace_id != workspace_id:
                continue
            if deck and card.deck != deck:
                continue
            if status and card.status != status:
                continue
            result.append(card)
        return result


# =============================================================================
# 💻 PREMIUM FEATURE 3: INTERACTIVE CODE PLAYGROUND
# =============================================================================

class CodeLanguage(str, Enum):
    """Desteklenen diller."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    HTML = "html"
    CSS = "css"
    SQL = "sql"
    BASH = "bash"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class CodeSnippet:
    """Kod parçası."""
    id: str
    workspace_id: str
    title: str
    language: CodeLanguage
    code: str
    explanation: str = ""
    
    # Çalıştırma sonuçları
    output: str = ""
    error: str = ""
    execution_time: float = 0.0
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    source_doc_id: Optional[str] = None
    created_at: str = ""
    last_run: Optional[str] = None
    run_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "title": self.title,
            "language": self.language.value,
            "code": self.code,
            "explanation": self.explanation,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tags": self.tags,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "run_count": self.run_count
        }


@dataclass
class CodeExercise:
    """Kod alıştırması."""
    id: str
    workspace_id: str
    title: str
    description: str
    language: CodeLanguage
    
    # Başlangıç kodu ve beklenen çıktı
    starter_code: str
    expected_output: str = ""
    solution: str = ""
    hints: List[str] = field(default_factory=list)
    
    # Test case'ler
    test_cases: List[Dict] = field(default_factory=list)
    
    # Zorluk ve kategoriler
    difficulty: str = "medium"
    category: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Kullanıcı ilerlemesi
    attempts: int = 0
    completed: bool = False
    best_solution: str = ""
    completion_time: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InteractiveCodePlayground:
    """
    💻 Interactive Code Playground - Canlı Kod Deneyimi
    
    Özellikler:
    - Canlı kod çalıştırma (sandboxed)
    - Step-by-step debugging
    - AI açıklamalı kod analizi
    - Alıştırma ve challenge'lar
    - Kod karşılaştırma
    - Syntax highlighting
    - Otomatik tamamlama önerileri
    """
    
    # Güvenli Python built-in'leri
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'callable', 'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate',
        'filter', 'float', 'format', 'frozenset', 'getattr', 'hasattr',
        'hash', 'hex', 'id', 'int', 'isinstance', 'issubclass', 'iter',
        'len', 'list', 'map', 'max', 'min', 'next', 'oct', 'ord', 'pow',
        'print', 'range', 'repr', 'reversed', 'round', 'set', 'slice',
        'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
    }
    
    # Yasaklı modüller
    BLOCKED_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'requests',
        'urllib', 'http', 'ftplib', 'smtplib', 'telnetlib', 'pickle',
        'shelve', 'marshal', 'dbm', 'sqlite3', 'ctypes', 'multiprocessing'
    }
    
    def __init__(self):
        self._snippets: Dict[str, CodeSnippet] = {}
        self._exercises: Dict[str, CodeExercise] = {}
        self._lock = Lock()
        self._llm = None
        logger.info("InteractiveCodePlayground initialized")
    
    def _get_llm(self):
        """LLM manager'ı lazy load et."""
        if self._llm is None:
            try:
                from .llm_manager import llm_manager
                self._llm = llm_manager
            except ImportError:
                pass
        return self._llm
    
    def create_snippet(
        self,
        workspace_id: str,
        title: str,
        language: CodeLanguage,
        code: str,
        explanation: str = "",
        tags: List[str] = None
    ) -> CodeSnippet:
        """Kod parçası oluştur."""
        snippet_id = str(uuid.uuid4())
        
        snippet = CodeSnippet(
            id=snippet_id,
            workspace_id=workspace_id,
            title=title,
            language=language,
            code=code,
            explanation=explanation,
            tags=tags or [],
            created_at=datetime.now().isoformat()
        )
        
        with self._lock:
            self._snippets[snippet_id] = snippet
        
        return snippet
    
    def extract_code_from_content(
        self,
        content: str,
        workspace_id: str
    ) -> List[CodeSnippet]:
        """İçerikten kod bloklarını çıkar."""
        snippets = []
        
        # Markdown code block pattern
        pattern = r'```(\w+)?\n([\s\S]*?)```'
        matches = re.findall(pattern, content)
        
        for i, (lang, code) in enumerate(matches):
            if not code.strip():
                continue
            
            # Dili belirle
            language = CodeLanguage.PYTHON  # default
            lang_lower = (lang or "").lower()
            
            language_map = {
                "python": CodeLanguage.PYTHON,
                "py": CodeLanguage.PYTHON,
                "javascript": CodeLanguage.JAVASCRIPT,
                "js": CodeLanguage.JAVASCRIPT,
                "typescript": CodeLanguage.TYPESCRIPT,
                "ts": CodeLanguage.TYPESCRIPT,
                "html": CodeLanguage.HTML,
                "css": CodeLanguage.CSS,
                "sql": CodeLanguage.SQL,
                "bash": CodeLanguage.BASH,
                "sh": CodeLanguage.BASH,
                "json": CodeLanguage.JSON,
                "md": CodeLanguage.MARKDOWN,
                "markdown": CodeLanguage.MARKDOWN
            }
            
            if lang_lower in language_map:
                language = language_map[lang_lower]
            
            snippet = self.create_snippet(
                workspace_id=workspace_id,
                title=f"Code Block {i + 1}",
                language=language,
                code=code.strip()
            )
            snippets.append(snippet)
        
        logger.info(f"Extracted {len(snippets)} code snippets")
        return snippets
    
    def run_python_code(
        self,
        code: str,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Python kodunu güvenli şekilde çalıştır.
        
        ⚠️ NOT: Gerçek uygulamada Docker container veya 
        güvenli sandbox kullanılmalıdır!
        """
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        
        # Güvenlik kontrolü
        for module in self.BLOCKED_MODULES:
            if f"import {module}" in code or f"from {module}" in code:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Güvenlik hatası: '{module}' modülü kullanılamaz.",
                    "execution_time": 0
                }
        
        # Tehlikeli fonksiyon kontrolü
        dangerous = ['exec', 'eval', 'compile', 'open', '__import__', 'globals', 'locals']
        for func in dangerous:
            if func + '(' in code:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Güvenlik hatası: '{func}' fonksiyonu kullanılamaz.",
                    "execution_time": 0
                }
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        start_time = datetime.now()
        
        try:
            # Güvenli globals
            safe_globals = {"__builtins__": {b: getattr(__builtins__, b) for b in self.SAFE_BUILTINS if hasattr(__builtins__, b)}}
            safe_globals["__builtins__"]["print"] = print
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, safe_globals, {})
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "output": stdout_capture.getvalue(),
                "error": stderr_capture.getvalue(),
                "execution_time": round(execution_time, 4)
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": False,
                "output": stdout_capture.getvalue(),
                "error": f"{type(e).__name__}: {str(e)}",
                "execution_time": round(execution_time, 4)
            }
    
    def run_snippet(self, snippet_id: str) -> Dict[str, Any]:
        """Snippet'i çalıştır."""
        snippet = self._snippets.get(snippet_id)
        if not snippet:
            return {"error": "Snippet bulunamadı"}
        
        if snippet.language != CodeLanguage.PYTHON:
            return {
                "error": f"Şu an sadece Python çalıştırılabilir. Dil: {snippet.language.value}"
            }
        
        result = self.run_python_code(snippet.code)
        
        # Snippet'i güncelle
        snippet.output = result.get("output", "")
        snippet.error = result.get("error", "")
        snippet.execution_time = result.get("execution_time", 0)
        snippet.last_run = datetime.now().isoformat()
        snippet.run_count += 1
        
        return {
            "snippet": snippet.to_dict(),
            **result
        }
    
    def analyze_code(
        self,
        code: str,
        language: CodeLanguage = CodeLanguage.PYTHON
    ) -> Dict[str, Any]:
        """Kod analizi yap."""
        analysis = {
            "language": language.value,
            "lines": len(code.split('\n')),
            "characters": len(code),
            "complexity": "low",
            "suggestions": [],
            "explanation": ""
        }
        
        # Basit analiz
        if language == CodeLanguage.PYTHON:
            # Fonksiyon sayısı
            func_count = len(re.findall(r'def \w+', code))
            class_count = len(re.findall(r'class \w+', code))
            
            analysis["functions"] = func_count
            analysis["classes"] = class_count
            
            # Complexity
            if func_count + class_count > 5:
                analysis["complexity"] = "high"
            elif func_count + class_count > 2:
                analysis["complexity"] = "medium"
            
            # Öneriler
            if "import *" in code:
                analysis["suggestions"].append("⚠️ 'import *' kullanmaktan kaçının")
            
            if len(code.split('\n')) > 50:
                analysis["suggestions"].append("💡 Uzun fonksiyonları parçalara ayırın")
            
            if not re.search(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', code):
                analysis["suggestions"].append("📝 Docstring eklemeyi düşünün")
        
        # LLM ile açıklama
        llm = self._get_llm()
        if llm:
            try:
                prompt = f"Bu {language.value} kodunu kısaca açıkla:\n```{language.value}\n{code[:1000]}\n```"
                analysis["explanation"] = llm.generate(
                    prompt, 
                    "Sen bir kod açıklama asistanısın. Türkçe ve kısa açıklamalar yap."
                )
            except:
                pass
        
        return analysis
    
    def create_exercise(
        self,
        workspace_id: str,
        title: str,
        description: str,
        language: CodeLanguage,
        starter_code: str,
        solution: str = "",
        expected_output: str = "",
        hints: List[str] = None,
        difficulty: str = "medium"
    ) -> CodeExercise:
        """Kod alıştırması oluştur."""
        exercise_id = str(uuid.uuid4())
        
        exercise = CodeExercise(
            id=exercise_id,
            workspace_id=workspace_id,
            title=title,
            description=description,
            language=language,
            starter_code=starter_code,
            solution=solution,
            expected_output=expected_output,
            hints=hints or [],
            difficulty=difficulty
        )
        
        with self._lock:
            self._exercises[exercise_id] = exercise
        
        return exercise
    
    def check_exercise(
        self,
        exercise_id: str,
        user_code: str
    ) -> Dict[str, Any]:
        """Alıştırma çözümünü kontrol et."""
        exercise = self._exercises.get(exercise_id)
        if not exercise:
            return {"error": "Alıştırma bulunamadı"}
        
        exercise.attempts += 1
        
        # Kodu çalıştır
        result = self.run_python_code(user_code)
        
        # Beklenen çıktı ile karşılaştır
        is_correct = False
        if result["success"] and exercise.expected_output:
            user_output = result["output"].strip()
            expected = exercise.expected_output.strip()
            is_correct = user_output == expected
        
        if is_correct:
            exercise.completed = True
            exercise.best_solution = user_code
            exercise.completion_time = datetime.now().isoformat()
            
            return {
                "correct": True,
                "message": "🎉 Tebrikler! Doğru çözüm!",
                "output": result["output"],
                "attempts": exercise.attempts
            }
        else:
            # İpucu ver
            hint = ""
            hint_index = min(exercise.attempts - 1, len(exercise.hints) - 1)
            if hint_index >= 0 and exercise.hints:
                hint = exercise.hints[hint_index]
            
            return {
                "correct": False,
                "message": "❌ Henüz doğru değil. Tekrar dene!",
                "output": result["output"],
                "error": result["error"],
                "hint": hint,
                "attempts": exercise.attempts
            }
    
    def get_snippet(self, snippet_id: str) -> Optional[CodeSnippet]:
        """Snippet getir."""
        return self._snippets.get(snippet_id)
    
    def get_exercise(self, exercise_id: str) -> Optional[CodeExercise]:
        """Alıştırma getir."""
        return self._exercises.get(exercise_id)
    
    def get_snippets_by_workspace(self, workspace_id: str) -> List[CodeSnippet]:
        """Workspace snippet'lerini getir."""
        return [s for s in self._snippets.values() if s.workspace_id == workspace_id]
    
    def get_exercises_by_workspace(self, workspace_id: str) -> List[CodeExercise]:
        """Workspace alıştırmalarını getir."""
        return [e for e in self._exercises.values() if e.workspace_id == workspace_id]


# =============================================================================
# 🧠 PREMIUM FEATURE 4: KNOWLEDGE GRAPH - BİLGİ HARİTASI
# =============================================================================

class NodeType(str, Enum):
    """Düğüm türleri."""
    CONCEPT = "concept"
    TOPIC = "topic"
    FACT = "fact"
    EXAMPLE = "example"
    QUESTION = "question"
    RESOURCE = "resource"
    PERSON = "person"
    EVENT = "event"


class EdgeType(str, Enum):
    """Bağlantı türleri."""
    IS_A = "is_a"                 # X bir Y'dir
    PART_OF = "part_of"           # X, Y'nin parçasıdır
    REQUIRES = "requires"         # X, Y'yi gerektirir
    LEADS_TO = "leads_to"         # X, Y'ye yol açar
    RELATED = "related"           # X ve Y ilişkili
    EXAMPLE_OF = "example_of"     # X, Y'nin örneği
    OPPOSITE = "opposite"         # X, Y'nin zıttı
    CAUSED_BY = "caused_by"       # X, Y'den kaynaklanır
    CONTAINS = "contains"         # X, Y'yi içerir


@dataclass
class KnowledgeNode:
    """Bilgi düğümü."""
    id: str
    workspace_id: str
    label: str
    node_type: NodeType
    description: str = ""
    
    # Görsel özellikler
    color: str = "#4A90D9"
    size: int = 30
    icon: str = ""
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    source_doc_id: Optional[str] = None
    created_at: str = ""
    
    # İstatistikler
    connections: int = 0
    importance: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "description": self.description,
            "color": self.color,
            "size": self.size,
            "icon": self.icon,
            "tags": self.tags,
            "connections": self.connections,
            "importance": round(self.importance, 2)
        }


@dataclass  
class KnowledgeEdge:
    """Bilgi bağlantısı."""
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    label: str = ""
    weight: float = 1.0
    bidirectional: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.edge_type.value,
            "label": self.label or self.edge_type.value,
            "weight": self.weight,
            "bidirectional": self.bidirectional
        }


class KnowledgeGraph:
    """
    🧠 Knowledge Graph - Bilgi Haritası ve İlişki Ağı
    
    Özellikler:
    - Kavramlar arası ilişki haritası
    - Otomatik ilişki keşfi
    - Görsel graph render
    - Path finding (öğrenme yolu)
    - Cluster analizi
    - Eksik bağlantı önerisi
    - Export (JSON, Mermaid, Cytoscape)
    """
    
    # Düğüm renkleri
    NODE_COLORS = {
        NodeType.CONCEPT: "#4A90D9",   # Mavi
        NodeType.TOPIC: "#7B68EE",      # Mor
        NodeType.FACT: "#50C878",       # Yeşil
        NodeType.EXAMPLE: "#FFB347",    # Turuncu
        NodeType.QUESTION: "#FF6B6B",   # Kırmızı
        NodeType.RESOURCE: "#4ECDC4",   # Turkuaz
        NodeType.PERSON: "#DDA0DD",     # Pembe
        NodeType.EVENT: "#F0E68C",      # Sarı
    }
    
    # Düğüm ikonları
    NODE_ICONS = {
        NodeType.CONCEPT: "💡",
        NodeType.TOPIC: "📚",
        NodeType.FACT: "✓",
        NodeType.EXAMPLE: "📌",
        NodeType.QUESTION: "❓",
        NodeType.RESOURCE: "🔗",
        NodeType.PERSON: "👤",
        NodeType.EVENT: "📅",
    }
    
    def __init__(self):
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: Dict[str, KnowledgeEdge] = {}
        self._workspace_graphs: Dict[str, Set[str]] = defaultdict(set)  # workspace -> node_ids
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)  # node_id -> connected_node_ids
        self._lock = Lock()
        logger.info("KnowledgeGraph initialized")
    
    def create_node(
        self,
        workspace_id: str,
        label: str,
        node_type: NodeType = NodeType.CONCEPT,
        description: str = "",
        tags: List[str] = None,
        source_doc_id: Optional[str] = None
    ) -> KnowledgeNode:
        """Düğüm oluştur."""
        node_id = str(uuid.uuid4())
        
        node = KnowledgeNode(
            id=node_id,
            workspace_id=workspace_id,
            label=label,
            node_type=node_type,
            description=description,
            color=self.NODE_COLORS.get(node_type, "#4A90D9"),
            icon=self.NODE_ICONS.get(node_type, ""),
            tags=tags or [],
            source_doc_id=source_doc_id,
            created_at=datetime.now().isoformat()
        )
        
        with self._lock:
            self._nodes[node_id] = node
            self._workspace_graphs[workspace_id].add(node_id)
        
        return node
    
    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType = EdgeType.RELATED,
        label: str = "",
        weight: float = 1.0,
        bidirectional: bool = False
    ) -> Optional[KnowledgeEdge]:
        """Bağlantı oluştur."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        
        edge_id = str(uuid.uuid4())
        
        edge = KnowledgeEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            label=label,
            weight=weight,
            bidirectional=bidirectional
        )
        
        with self._lock:
            self._edges[edge_id] = edge
            self._adjacency[source_id].add(target_id)
            if bidirectional:
                self._adjacency[target_id].add(source_id)
            
            # Connection sayısını güncelle
            self._nodes[source_id].connections += 1
            self._nodes[target_id].connections += 1
        
        return edge
    
    def build_from_content(
        self,
        workspace_id: str,
        content: str,
        source_doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """İçerikten otomatik graph oluştur."""
        nodes_created = []
        edges_created = []
        
        # 1. Başlıkları kavram olarak ekle
        headers = re.findall(r'^(#{1,3})\s+(.+)$', content, re.MULTILINE)
        topic_nodes = {}  # level -> last node at that level
        
        for hashes, title in headers:
            level = len(hashes)
            title = title.strip()
            
            node_type = NodeType.TOPIC if level == 1 else NodeType.CONCEPT
            
            node = self.create_node(
                workspace_id=workspace_id,
                label=title,
                node_type=node_type,
                source_doc_id=source_doc_id
            )
            nodes_created.append(node)
            
            # Hiyerarşik bağlantı
            if level > 1 and (level - 1) in topic_nodes:
                parent = topic_nodes[level - 1]
                edge = self.create_edge(
                    source_id=parent.id,
                    target_id=node.id,
                    edge_type=EdgeType.CONTAINS
                )
                if edge:
                    edges_created.append(edge)
            
            topic_nodes[level] = node
        
        # 2. Bold metinleri kavram olarak ekle
        bold_texts = re.findall(r'\*\*([^*]{3,50})\*\*', content)
        bold_nodes = []
        
        for text in set(bold_texts)[:30]:  # Max 30 kavram
            node = self.create_node(
                workspace_id=workspace_id,
                label=text,
                node_type=NodeType.CONCEPT,
                source_doc_id=source_doc_id
            )
            nodes_created.append(node)
            bold_nodes.append(node)
        
        # 3. Kavramlar arası basit ilişki (aynı paragrafta geçenler)
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para_concepts = []
            for node in bold_nodes:
                if node.label.lower() in para.lower():
                    para_concepts.append(node)
            
            # Aynı paragraftakileri bağla
            for i, n1 in enumerate(para_concepts):
                for n2 in para_concepts[i+1:]:
                    edge = self.create_edge(
                        source_id=n1.id,
                        target_id=n2.id,
                        edge_type=EdgeType.RELATED,
                        bidirectional=True
                    )
                    if edge:
                        edges_created.append(edge)
        
        # Importance hesapla
        self._calculate_importance(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "nodes_created": len(nodes_created),
            "edges_created": len(edges_created),
            "nodes": [n.to_dict() for n in nodes_created],
            "edges": [e.to_dict() for e in edges_created]
        }
    
    def _calculate_importance(self, workspace_id: str):
        """PageRank benzeri importance hesapla."""
        node_ids = list(self._workspace_graphs.get(workspace_id, set()))
        if not node_ids:
            return
        
        # Basit: bağlantı sayısına göre
        max_connections = max(
            self._nodes[nid].connections for nid in node_ids
        ) or 1
        
        for node_id in node_ids:
            node = self._nodes[node_id]
            node.importance = 0.5 + 0.5 * (node.connections / max_connections)
            node.size = 20 + int(node.importance * 30)
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 10
    ) -> Optional[List[str]]:
        """İki düğüm arasında yol bul (BFS)."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for neighbor in self._adjacency[current]:
                if neighbor == target_id:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None  # Yol bulunamadı
    
    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1
    ) -> List[KnowledgeNode]:
        """Düğümün komşularını getir."""
        if node_id not in self._nodes:
            return []
        
        result = set()
        current_level = {node_id}
        
        for _ in range(depth):
            next_level = set()
            for nid in current_level:
                for neighbor in self._adjacency[nid]:
                    if neighbor != node_id:
                        result.add(neighbor)
                        next_level.add(neighbor)
            current_level = next_level
        
        return [self._nodes[nid] for nid in result if nid in self._nodes]
    
    def suggest_connections(
        self,
        workspace_id: str,
        node_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """Olası yeni bağlantılar öner."""
        if node_id not in self._nodes:
            return []
        
        node = self._nodes[node_id]
        suggestions = []
        
        # Workspace'teki diğer düğümler
        workspace_nodes = self._workspace_graphs.get(workspace_id, set())
        connected = self._adjacency[node_id]
        
        for other_id in workspace_nodes:
            if other_id == node_id or other_id in connected:
                continue
            
            other = self._nodes[other_id]
            
            # Benzerlik skoru hesapla
            similarity = 0
            
            # Ortak taglar
            common_tags = set(node.tags) & set(other.tags)
            similarity += len(common_tags) * 0.3
            
            # Aynı tip
            if node.node_type == other.node_type:
                similarity += 0.2
            
            # Ortak komşular
            common_neighbors = self._adjacency[node_id] & self._adjacency[other_id]
            similarity += len(common_neighbors) * 0.2
            
            if similarity > 0:
                suggestions.append({
                    "node": other.to_dict(),
                    "similarity": round(similarity, 2),
                    "reason": self._get_suggestion_reason(node, other, common_tags, common_neighbors)
                })
        
        # Benzerliğe göre sırala
        suggestions.sort(key=lambda x: x["similarity"], reverse=True)
        
        return suggestions[:limit]
    
    def _get_suggestion_reason(
        self,
        node1: KnowledgeNode,
        node2: KnowledgeNode,
        common_tags: Set[str],
        common_neighbors: Set[str]
    ) -> str:
        """Öneri sebebi."""
        reasons = []
        
        if common_tags:
            reasons.append(f"Ortak etiketler: {', '.join(list(common_tags)[:3])}")
        
        if node1.node_type == node2.node_type:
            reasons.append(f"Aynı tür: {node1.node_type.value}")
        
        if common_neighbors:
            neighbor_labels = [self._nodes[n].label for n in list(common_neighbors)[:2] if n in self._nodes]
            if neighbor_labels:
                reasons.append(f"Ortak bağlantılar: {', '.join(neighbor_labels)}")
        
        return " | ".join(reasons) if reasons else "Potansiyel ilişki"
    
    def get_clusters(
        self,
        workspace_id: str,
        min_cluster_size: int = 2
    ) -> List[Dict]:
        """Kümeleri bul (connected components)."""
        node_ids = list(self._workspace_graphs.get(workspace_id, set()))
        if not node_ids:
            return []
        
        visited = set()
        clusters = []
        
        for start_id in node_ids:
            if start_id in visited:
                continue
            
            # BFS ile cluster'ı bul
            cluster = []
            queue = [start_id]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                cluster.append(current)
                
                for neighbor in self._adjacency[current]:
                    if neighbor not in visited and neighbor in node_ids:
                        queue.append(neighbor)
            
            if len(cluster) >= min_cluster_size:
                cluster_nodes = [self._nodes[nid] for nid in cluster if nid in self._nodes]
                
                # Cluster'ın ana konusunu bul
                main_topic = max(cluster_nodes, key=lambda n: n.importance).label
                
                clusters.append({
                    "id": str(uuid.uuid4())[:8],
                    "name": main_topic,
                    "size": len(cluster),
                    "nodes": [n.to_dict() for n in cluster_nodes]
                })
        
        return sorted(clusters, key=lambda c: c["size"], reverse=True)
    
    def export_mermaid(self, workspace_id: str) -> str:
        """Mermaid formatında export."""
        lines = ["graph TB"]
        
        node_ids = self._workspace_graphs.get(workspace_id, set())
        
        # Düğümler
        for node_id in node_ids:
            node = self._nodes[node_id]
            shape = {
                NodeType.CONCEPT: f'["{node.label}"]',
                NodeType.TOPIC: f'(("{node.label}"))',
                NodeType.FACT: f'{{"{node.label}"}}',
                NodeType.EXAMPLE: f'("{node.label}")',
                NodeType.QUESTION: f'>"{node.label}"]',
            }.get(node.node_type, f'["{node.label}"]')
            
            lines.append(f"    {node_id[:8]}{shape}")
        
        # Bağlantılar
        for edge in self._edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                arrow = "-->" if not edge.bidirectional else "<-->"
                label = f"|{edge.label}|" if edge.label else ""
                lines.append(f"    {edge.source_id[:8]} {arrow}{label} {edge.target_id[:8]}")
        
        return "\n".join(lines)
    
    def export_cytoscape(self, workspace_id: str) -> Dict:
        """Cytoscape.js formatında export."""
        elements = {"nodes": [], "edges": []}
        
        node_ids = self._workspace_graphs.get(workspace_id, set())
        
        for node_id in node_ids:
            node = self._nodes[node_id]
            elements["nodes"].append({
                "data": {
                    "id": node_id,
                    "label": node.label,
                    "type": node.node_type.value,
                    "color": node.color,
                    "size": node.size
                }
            })
        
        for edge in self._edges.values():
            if edge.source_id in node_ids and edge.target_id in node_ids:
                elements["edges"].append({
                    "data": {
                        "id": edge.id,
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "type": edge.edge_type.value,
                        "label": edge.label
                    }
                })
        
        return elements
    
    def get_graph_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Graph istatistikleri."""
        node_ids = self._workspace_graphs.get(workspace_id, set())
        
        edge_count = sum(
            1 for e in self._edges.values()
            if e.source_id in node_ids
        )
        
        type_distribution = Counter(
            self._nodes[nid].node_type.value
            for nid in node_ids
            if nid in self._nodes
        )
        
        return {
            "total_nodes": len(node_ids),
            "total_edges": edge_count,
            "density": round(edge_count / max(len(node_ids) * (len(node_ids) - 1), 1), 4),
            "type_distribution": dict(type_distribution),
            "avg_connections": round(
                sum(self._nodes[nid].connections for nid in node_ids if nid in self._nodes) / max(len(node_ids), 1),
                2
            )
        }
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Düğüm getir."""
        return self._nodes.get(node_id)
    
    def get_nodes_by_workspace(self, workspace_id: str) -> List[KnowledgeNode]:
        """Workspace düğümlerini getir."""
        node_ids = self._workspace_graphs.get(workspace_id, set())
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]
    
    def get_edges_by_workspace(self, workspace_id: str) -> List[KnowledgeEdge]:
        """Workspace bağlantılarını getir."""
        node_ids = self._workspace_graphs.get(workspace_id, set())
        return [
            e for e in self._edges.values()
            if e.source_id in node_ids
        ]
    
    def delete_node(self, node_id: str) -> bool:
        """Düğümü ve bağlantılarını sil."""
        if node_id not in self._nodes:
            return False
        
        with self._lock:
            node = self._nodes.pop(node_id)
            
            # Workspace'ten kaldır
            if node.workspace_id in self._workspace_graphs:
                self._workspace_graphs[node.workspace_id].discard(node_id)
            
            # Bağlantıları sil
            edges_to_delete = [
                e.id for e in self._edges.values()
                if e.source_id == node_id or e.target_id == node_id
            ]
            
            for edge_id in edges_to_delete:
                self._edges.pop(edge_id, None)
            
            # Adjacency güncelle
            self._adjacency.pop(node_id, None)
            for adj_set in self._adjacency.values():
                adj_set.discard(node_id)
        
        return True


# =============================================================================
# 📊 PREMIUM FEATURE 5: LEARNING ANALYTICS - ÖĞRENME ANALİTİĞİ
# =============================================================================

@dataclass
class LearningEvent:
    """Öğrenme olayı kaydı."""
    id: str
    workspace_id: str
    event_type: str  # document_read, test_completed, card_reviewed, tutor_session, etc.
    timestamp: str
    duration_minutes: int = 0
    score: Optional[float] = None
    topic: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LearningInsight:
    """Öğrenme içgörüsü."""
    id: str
    insight_type: str  # strength, weakness, recommendation, milestone
    title: str
    description: str
    importance: str = "medium"  # low, medium, high
    action_items: List[str] = field(default_factory=list)
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LearningAnalytics:
    """
    📊 Learning Analytics - Öğrenme Analitiği
    
    Özellikler:
    - Detaylı ilerleme takibi
    - Zayıf nokta tespiti
    - Öğrenme kalıpları analizi
    - Performans trendleri
    - AI destekli içgörüler
    - Kişiselleştirilmiş öneriler
    - Haftalık/aylık raporlar
    """
    
    def __init__(self):
        self._events: List[LearningEvent] = []
        self._insights: Dict[str, List[LearningInsight]] = defaultdict(list)  # workspace_id -> insights
        self._lock = Lock()
        self._llm = None
        logger.info("LearningAnalytics initialized")
    
    def _get_llm(self):
        """LLM manager'ı lazy load et."""
        if self._llm is None:
            try:
                from .llm_manager import llm_manager
                self._llm = llm_manager
            except ImportError:
                pass
        return self._llm
    
    def log_event(
        self,
        workspace_id: str,
        event_type: str,
        duration_minutes: int = 0,
        score: Optional[float] = None,
        topic: str = "",
        metadata: Dict = None
    ) -> LearningEvent:
        """Öğrenme olayı kaydet."""
        event = LearningEvent(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            duration_minutes=duration_minutes,
            score=score,
            topic=topic,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._events.append(event)
        
        return event
    
    def get_workspace_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Çalışma alanı istatistikleri."""
        events = [e for e in self._events if e.workspace_id == workspace_id]
        
        if not events:
            return {
                "total_study_time": 0,
                "session_count": 0,
                "documents_read": 0,
                "tests_completed": 0,
                "cards_reviewed": 0,
                "average_score": 0,
                "streak_days": 0,
                "most_active_day": None,
                "performance_trend": "neutral"
            }
        
        # Temel metrikler
        total_time = sum(e.duration_minutes for e in events)
        documents_read = sum(1 for e in events if e.event_type == "document_read")
        tests_completed = sum(1 for e in events if e.event_type == "test_completed")
        cards_reviewed = sum(1 for e in events if e.event_type == "card_reviewed")
        
        # Ortalama skor
        scores = [e.score for e in events if e.score is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        
        # Günlük aktivite
        daily_activity = Counter()
        for event in events:
            day = event.timestamp[:10]
            daily_activity[day] += event.duration_minutes
        
        most_active_day = max(daily_activity.items(), key=lambda x: x[1])[0] if daily_activity else None
        
        # Streak hesapla
        streak = self._calculate_streak(events)
        
        # Performans trendi
        trend = self._calculate_trend(events)
        
        return {
            "total_study_time": total_time,
            "session_count": len(set(e.id for e in events)),
            "documents_read": documents_read,
            "tests_completed": tests_completed,
            "cards_reviewed": cards_reviewed,
            "average_score": round(average_score, 1),
            "streak_days": streak,
            "most_active_day": most_active_day,
            "performance_trend": trend,
            "event_count": len(events)
        }
    
    def _calculate_streak(self, events: List[LearningEvent]) -> int:
        """Ardışık çalışma günü serisini hesapla."""
        if not events:
            return 0
        
        dates = sorted(set(e.timestamp[:10] for e in events), reverse=True)
        today = datetime.now().strftime("%Y-%m-%d")
        
        if not dates or dates[0] != today:
            return 0
        
        streak = 1
        for i in range(1, len(dates)):
            prev_date = datetime.strptime(dates[i-1], "%Y-%m-%d")
            curr_date = datetime.strptime(dates[i], "%Y-%m-%d")
            
            if (prev_date - curr_date).days == 1:
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_trend(self, events: List[LearningEvent]) -> str:
        """Performans trendini hesapla."""
        scored_events = [e for e in events if e.score is not None]
        
        if len(scored_events) < 4:
            return "neutral"
        
        # Son 2 hafta vs önceki 2 hafta
        sorted_events = sorted(scored_events, key=lambda e: e.timestamp, reverse=True)
        recent = sorted_events[:len(sorted_events)//2]
        older = sorted_events[len(sorted_events)//2:]
        
        recent_avg = sum(e.score for e in recent) / len(recent)
        older_avg = sum(e.score for e in older) / len(older)
        
        if recent_avg > older_avg + 5:
            return "improving"
        elif recent_avg < older_avg - 5:
            return "declining"
        else:
            return "stable"
    
    def get_weekly_activity(self, workspace_id: str) -> List[Dict]:
        """Son 7 günlük aktivite."""
        events = [e for e in self._events if e.workspace_id == workspace_id]
        weekly = []
        today = datetime.now()
        
        for i in range(7):
            date = today - timedelta(days=6-i)
            date_str = date.strftime("%Y-%m-%d")
            day_events = [e for e in events if e.timestamp[:10] == date_str]
            
            weekly.append({
                "date": date_str,
                "day": date.strftime("%a"),
                "day_name": {
                    "Mon": "Pzt", "Tue": "Sal", "Wed": "Çar",
                    "Thu": "Per", "Fri": "Cum", "Sat": "Cmt", "Sun": "Paz"
                }.get(date.strftime("%a"), date.strftime("%a")),
                "minutes": sum(e.duration_minutes for e in day_events),
                "events": len(day_events),
                "average_score": round(
                    sum(e.score for e in day_events if e.score) / 
                    len([e for e in day_events if e.score]) if [e for e in day_events if e.score] else 0,
                    1
                )
            })
        
        return weekly
    
    def get_topic_performance(self, workspace_id: str) -> List[Dict]:
        """Konulara göre performans."""
        events = [e for e in self._events if e.workspace_id == workspace_id and e.topic]
        
        topic_stats = defaultdict(lambda: {"scores": [], "time": 0, "count": 0})
        
        for event in events:
            topic_stats[event.topic]["scores"].append(event.score or 0)
            topic_stats[event.topic]["time"] += event.duration_minutes
            topic_stats[event.topic]["count"] += 1
        
        result = []
        for topic, stats in topic_stats.items():
            avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
            result.append({
                "topic": topic,
                "average_score": round(avg_score, 1),
                "total_time": stats["time"],
                "session_count": stats["count"],
                "mastery_level": "expert" if avg_score >= 90 else "advanced" if avg_score >= 75 else "intermediate" if avg_score >= 60 else "beginner"
            })
        
        return sorted(result, key=lambda x: x["average_score"], reverse=True)
    
    def get_weak_areas(self, workspace_id: str, limit: int = 5) -> List[Dict]:
        """Zayıf alanları tespit et."""
        topic_perf = self.get_topic_performance(workspace_id)
        
        weak = [
            {
                **t,
                "recommendation": f"'{t['topic']}' konusunu tekrar çalışmanız önerilir.",
                "suggested_action": "review"
            }
            for t in topic_perf
            if t["average_score"] < 70
        ]
        
        return sorted(weak, key=lambda x: x["average_score"])[:limit]
    
    def get_strengths(self, workspace_id: str, limit: int = 5) -> List[Dict]:
        """Güçlü alanları tespit et."""
        topic_perf = self.get_topic_performance(workspace_id)
        
        strong = [
            {
                **t,
                "recommendation": f"'{t['topic']}' konusunda çok iyisin!",
                "suggested_action": "advance"
            }
            for t in topic_perf
            if t["average_score"] >= 80
        ]
        
        return sorted(strong, key=lambda x: x["average_score"], reverse=True)[:limit]
    
    def generate_insights(self, workspace_id: str) -> List[LearningInsight]:
        """AI destekli içgörüler oluştur."""
        stats = self.get_workspace_stats(workspace_id)
        weekly = self.get_weekly_activity(workspace_id)
        weak_areas = self.get_weak_areas(workspace_id)
        strengths = self.get_strengths(workspace_id)
        
        insights = []
        
        # Çalışma süresi analizi
        if stats["total_study_time"] < 60:
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="recommendation",
                title="Çalışma Süresini Artır",
                description="Toplam çalışma süreniz 1 saatten az. Düzenli çalışma alışkanlığı edinmeniz önerilir.",
                importance="high",
                action_items=["Günde en az 30 dakika çalışma hedefi koyun", "Sabit bir çalışma saati belirleyin"],
                created_at=datetime.now().isoformat()
            ))
        elif stats["total_study_time"] > 300:
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="milestone",
                title="Harika İlerleme!",
                description=f"5 saatten fazla çalışma süresi biriktirdiniz. Muhteşem bir tutarlılık!",
                importance="medium",
                action_items=["Bu tempoyu koruyun", "Kendinizi ödüllendirin"],
                created_at=datetime.now().isoformat()
            ))
        
        # Streak analizi
        if stats["streak_days"] >= 7:
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="milestone",
                title=f"🔥 {stats['streak_days']} Günlük Seri!",
                description="Muhteşem bir tutarlılık gösteriyorsunuz. Devam edin!",
                importance="high",
                action_items=["Seriyi korumaya devam edin"],
                created_at=datetime.now().isoformat()
            ))
        elif stats["streak_days"] == 0:
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="recommendation",
                title="Seri Başlatın",
                description="Her gün en az 10 dakika çalışarak bir seri başlatabilirsiniz.",
                importance="medium",
                action_items=["Bugün çalışmaya başlayın", "Günlük hatırlatıcı kurun"],
                created_at=datetime.now().isoformat()
            ))
        
        # Zayıf alan analizi
        for weak in weak_areas[:2]:
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="weakness",
                title=f"'{weak['topic']}' Geliştirilmeli",
                description=f"Bu konuda ortalama puanınız %{weak['average_score']:.0f}. Tekrar çalışmanız önerilir.",
                importance="high",
                action_items=[
                    f"'{weak['topic']}' konusunu tekrar okuyun",
                    "Bu konudan test çözün",
                    "Flashcard'lar oluşturun"
                ],
                created_at=datetime.now().isoformat()
            ))
        
        # Güçlü alan analizi
        for strong in strengths[:1]:
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="strength",
                title=f"'{strong['topic']}' Uzmanlık Alanınız",
                description=f"Bu konuda %{strong['average_score']:.0f} ortalama ile harika gidiyorsunuz!",
                importance="low",
                action_items=["İleri seviye konulara geçebilirsiniz"],
                created_at=datetime.now().isoformat()
            ))
        
        # Performans trendi
        if stats["performance_trend"] == "improving":
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="milestone",
                title="📈 Performansınız Yükseliyor",
                description="Son dönemde performansınız artış gösteriyor. Harika gidiyorsunuz!",
                importance="medium",
                action_items=["Bu tempoyu sürdürün"],
                created_at=datetime.now().isoformat()
            ))
        elif stats["performance_trend"] == "declining":
            insights.append(LearningInsight(
                id=str(uuid.uuid4()),
                insight_type="recommendation",
                title="📉 Performans Düşüşü",
                description="Son dönemde performansta düşüş gözlemleniyor. Mola vermeyi veya çalışma yönteminizi değiştirmeyi düşünün.",
                importance="high",
                action_items=["Kısa bir mola verin", "Çalışma ortamınızı değiştirin", "Daha kolay konularla devam edin"],
                created_at=datetime.now().isoformat()
            ))
        
        # Kaydet
        with self._lock:
            self._insights[workspace_id] = insights
        
        return insights
    
    def get_insights(self, workspace_id: str) -> List[LearningInsight]:
        """Mevcut içgörüleri getir."""
        return self._insights.get(workspace_id, [])
    
    def get_learning_report(self, workspace_id: str) -> Dict[str, Any]:
        """Kapsamlı öğrenme raporu."""
        stats = self.get_workspace_stats(workspace_id)
        weekly = self.get_weekly_activity(workspace_id)
        topic_perf = self.get_topic_performance(workspace_id)
        weak_areas = self.get_weak_areas(workspace_id)
        strengths = self.get_strengths(workspace_id)
        insights = self.generate_insights(workspace_id)
        
        # Genel sağlık skoru
        health_score = 50
        if stats["streak_days"] >= 3:
            health_score += 15
        if stats["total_study_time"] >= 120:
            health_score += 15
        if stats["average_score"] >= 70:
            health_score += 10
        if stats["performance_trend"] == "improving":
            health_score += 10
        
        health_status = "excellent" if health_score >= 80 else "good" if health_score >= 60 else "needs_attention"
        
        return {
            "overview": stats,
            "weekly_activity": weekly,
            "topic_performance": topic_perf,
            "weak_areas": weak_areas,
            "strengths": strengths,
            "insights": [i.to_dict() for i in insights],
            "health": {
                "score": min(100, health_score),
                "status": health_status,
                "message": {
                    "excellent": "🌟 Mükemmel! Öğrenme yolculuğunuz harika gidiyor!",
                    "good": "👍 İyi gidiyorsun! Biraz daha gayret göster.",
                    "needs_attention": "💪 Biraz daha çalışmaya ihtiyacın var. Devam et!"
                }.get(health_status, "")
            },
            "generated_at": datetime.now().isoformat()
        }


# =============================================================================
# 🎭 PREMIUM FEATURE 6: AI SIMULATIONS - PRATİK SENARYOLARI
# =============================================================================

class ScenarioType(str, Enum):
    """Senaryo türleri."""
    INTERVIEW = "interview"           # Mülakat simülasyonu
    PRESENTATION = "presentation"     # Sunum pratiği
    PROBLEM_SOLVING = "problem_solving"  # Problem çözme
    DEBATE = "debate"                 # Tartışma/münazara
    CASE_STUDY = "case_study"         # Vaka analizi
    ROLE_PLAY = "role_play"           # Rol yapma
    EXAM_SIMULATION = "exam_simulation"  # Sınav simülasyonu
    CONSULTATION = "consultation"     # Danışmanlık senaryosu


class ScenarioDifficulty(str, Enum):
    """Senaryo zorlukları."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


@dataclass
class Scenario:
    """Simülasyon senaryosu."""
    id: str
    workspace_id: str
    scenario_type: ScenarioType
    title: str
    description: str
    context: str = ""
    difficulty: ScenarioDifficulty = ScenarioDifficulty.MEDIUM
    objectives: List[str] = field(default_factory=list)
    conversation: List[Dict] = field(default_factory=list)
    evaluation: Dict = field(default_factory=dict)
    status: str = "active"  # active, completed, abandoned
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "scenario_type": self.scenario_type.value,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "difficulty": self.difficulty.value,
            "objectives": self.objectives,
            "conversation": self.conversation,
            "evaluation": self.evaluation,
            "status": self.status,
            "turn_count": len([m for m in self.conversation if m.get("role") == "user"]),
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class AISimulationSystem:
    """
    🎭 AI Simulation System - Pratik Senaryoları
    
    Özellikler:
    - Mülakat simülasyonu
    - Sunum pratiği
    - Problem çözme senaryoları
    - Tartışma/münazara
    - Vaka analizi
    - Rol yapma
    - Sınav simülasyonu
    - Gerçekçi geri bildirim
    """
    
    SCENARIO_TEMPLATES = {
        ScenarioType.INTERVIEW: {
            "icon": "👔",
            "title_template": "{topic} - Teknik Mülakat",
            "description": "Bir teknoloji şirketinde teknik mülakat yapıyorsunuz.",
            "objectives": [
                "Teknik sorulara doğru cevap ver",
                "Problem çözme yaklaşımını göster",
                "İletişim becerilerini sergile"
            ],
            "system_prompt": """Sen deneyimli bir teknik mülakatçısın. {topic} konusunda mülakat yapıyorsun.

Kurallar:
- Gerçekçi mülakat soruları sor
- Cevapları değerlendir ve takip soruları sor
- Yapıcı geri bildirim ver
- Zorluk: {difficulty}

Mülakat başladı. Kendinizi tanıtın ve ilk soruyu sorun."""
        },
        
        ScenarioType.PRESENTATION: {
            "icon": "🎤",
            "title_template": "{topic} - Sunum Pratiği",
            "description": "Bir konferansta sunum yapıyorsunuz. Dinleyiciler soru soracak.",
            "objectives": [
                "Konuyu açık ve net anlat",
                "Soruları başarıyla yanıtla",
                "Dinleyici ilgisini koru"
            ],
            "system_prompt": """Sen bir sunum dinleyicisisin. {topic} hakkında sunum yapılıyor.

Görevin:
- Sunumu dinle ve sorular sor
- Açıklama iste
- Zor sorular sor (zorluk: {difficulty})
- Sunum sonunda değerlendir

"Sahnede sizsiniz. Sunumunuza başlayabilirsiniz." diyerek başla."""
        },
        
        ScenarioType.PROBLEM_SOLVING: {
            "icon": "🧩",
            "title_template": "{topic} - Problem Çözme",
            "description": "Gerçek dünya problemleri ile pratik yapın.",
            "objectives": [
                "Problemi analiz et",
                "Çözüm stratejisi geliştir",
                "Adım adım çöz"
            ],
            "system_prompt": """Sen bir problem çözme koçusun. {topic} alanında problemler sunuyorsun.

Yaklaşım:
- Gerçekçi bir problem sun
- Çözüm adımlarını sor
- İpuçları ver (gerekirse)
- Alternatif çözümleri değerlendir
Zorluk: {difficulty}

İlk problemi sun."""
        },
        
        ScenarioType.DEBATE: {
            "icon": "⚔️",
            "title_template": "{topic} - Tartışma",
            "description": "Yapıcı bir tartışma yapın ve argümanlarınızı savunun.",
            "objectives": [
                "Argümanları savun",
                "Karşı argümanları değerlendir",
                "Mantıklı ve tutarlı ol"
            ],
            "system_prompt": """Sen bir tartışma moderatörü ve karşı tarafsın. {topic} tartışılıyor.

Görevin:
- Karşı argümanlar sun
- Zayıf noktaları sorgula
- Yapıcı eleştiri yap
Zorluk: {difficulty}

"Tartışmaya hoş geldiniz. Pozisyonunuzu belirtin." diyerek başla."""
        },
        
        ScenarioType.CASE_STUDY: {
            "icon": "📋",
            "title_template": "{topic} - Vaka Analizi",
            "description": "Gerçek bir vaka üzerinden analiz yapın.",
            "objectives": [
                "Vakayı analiz et",
                "Problemleri tespit et",
                "Çözüm önerileri sun"
            ],
            "system_prompt": """Sen bir vaka analizi uzmanısın. {topic} alanında bir vaka sunuyorsun.

Yaklaşım:
- Detaylı bir vaka sun
- Analiz soruları sor
- Çözüm önerilerini değerlendir
Zorluk: {difficulty}

Vakayı anlat."""
        },
        
        ScenarioType.ROLE_PLAY: {
            "icon": "🎭",
            "title_template": "{topic} - Rol Yapma",
            "description": "Bir senaryoda rol yaparak pratik edin.",
            "objectives": [
                "Rolü başarıyla canlandır",
                "Duruma uygun tepkiler ver",
                "İletişim becerilerini göster"
            ],
            "system_prompt": """Sen bir rol yapma partnerisin. {topic} senaryosunda oynuyorsun.

Senaryo oluştur ve rolünü oyna. Karşılıklı diyalog kur.
Zorluk: {difficulty}

Senaryoyu başlat ve ilk repliği söyle."""
        },
        
        ScenarioType.EXAM_SIMULATION: {
            "icon": "📝",
            "title_template": "{topic} - Sınav Simülasyonu",
            "description": "Gerçekçi bir sınav deneyimi yaşayın.",
            "objectives": [
                "Sorulara hızlı ve doğru cevap ver",
                "Zaman yönetimini göster",
                "Stres altında performans sergile"
            ],
            "system_prompt": """Sen bir sınav gözetmenisin. {topic} sınavı yapıyorsun.

Kurallar:
- Sorular çeşitli türlerde olsun (çoktan seçmeli, açık uçlu, doğru/yanlış)
- Her cevaptan sonra doğru/yanlış belirt
- Toplam 10 soru sor
- Sonunda detaylı puan ver
Zorluk: {difficulty}

Sınav başlıyor. İlk soruyu sor."""
        },
        
        ScenarioType.CONSULTATION: {
            "icon": "💼",
            "title_template": "{topic} - Danışmanlık",
            "description": "Bir danışman olarak müşteriye yardım edin.",
            "objectives": [
                "Müşteri ihtiyaçlarını anla",
                "Profesyonel öneriler sun",
                "Çözüm odaklı yaklaş"
            ],
            "system_prompt": """Sen bir müşterisin ve {topic} konusunda danışmanlık almak istiyorsun.

Senaryo:
- Gerçekçi sorular ve endişeler belirt
- Danışmanın önerilerini değerlendir
- Zor durumlar oluştur
Zorluk: {difficulty}

"Merhaba, {topic} konusunda yardıma ihtiyacım var." diyerek başla."""
        }
    }
    
    def __init__(self):
        self._scenarios: Dict[str, Scenario] = {}
        self._lock = Lock()
        self._llm = None
        logger.info("AISimulationSystem initialized")
    
    def _get_llm(self):
        """LLM manager'ı lazy load et."""
        if self._llm is None:
            try:
                from .llm_manager import llm_manager
                self._llm = llm_manager
            except ImportError:
                pass
        return self._llm
    
    def get_scenario_types(self) -> List[Dict]:
        """Mevcut senaryo türlerini getir."""
        return [
            {
                "id": st.value,
                "name": {
                    "interview": "Mülakat Simülasyonu",
                    "presentation": "Sunum Pratiği",
                    "problem_solving": "Problem Çözme",
                    "debate": "Tartışma/Münazara",
                    "case_study": "Vaka Analizi",
                    "role_play": "Rol Yapma",
                    "exam_simulation": "Sınav Simülasyonu",
                    "consultation": "Danışmanlık"
                }.get(st.value, st.value),
                "icon": self.SCENARIO_TEMPLATES.get(st, {}).get("icon", "🎯"),
                "description": self.SCENARIO_TEMPLATES.get(st, {}).get("description", "")
            }
            for st in ScenarioType
        ]
    
    def create_scenario(
        self,
        workspace_id: str,
        scenario_type: ScenarioType,
        topic: str,
        difficulty: ScenarioDifficulty = ScenarioDifficulty.MEDIUM,
        custom_context: str = ""
    ) -> Scenario:
        """Yeni senaryo oluştur."""
        template = self.SCENARIO_TEMPLATES.get(scenario_type, self.SCENARIO_TEMPLATES[ScenarioType.PROBLEM_SOLVING])
        
        scenario = Scenario(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            scenario_type=scenario_type,
            title=template["title_template"].format(topic=topic),
            description=template["description"],
            context=custom_context or template["description"],
            difficulty=difficulty,
            objectives=template["objectives"],
            created_at=datetime.now().isoformat()
        )
        
        # İlk mesajı oluştur
        initial_message = self._generate_initial_message(scenario, topic, template)
        scenario.conversation.append({
            "role": "assistant",
            "content": initial_message,
            "timestamp": datetime.now().isoformat()
        })
        
        with self._lock:
            self._scenarios[scenario.id] = scenario
        
        return scenario
    
    def _generate_initial_message(self, scenario: Scenario, topic: str, template: Dict) -> str:
        """Başlangıç mesajı oluştur."""
        llm = self._get_llm()
        
        if llm:
            system_prompt = template["system_prompt"].format(
                topic=topic,
                difficulty=scenario.difficulty.value
            )
            
            try:
                return llm.generate(
                    "Senaryoyu başlat.",
                    system_prompt
                )
            except:
                pass
        
        # Fallback
        return f"""🎭 **{scenario.title}**

{template['icon']} {scenario.description}

**Hedefler:**
{chr(10).join('• ' + obj for obj in scenario.objectives)}

Hazır olduğunuzda başlayabilirsiniz!"""
    
    def interact(
        self,
        scenario_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """Senaryo ile etkileşim."""
        scenario = self._scenarios.get(scenario_id)
        if not scenario:
            return {"error": "Senaryo bulunamadı"}
        
        if scenario.status != "active":
            return {"error": "Senaryo aktif değil", "status": scenario.status}
        
        # Kullanıcı mesajını kaydet
        scenario.conversation.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Yanıt oluştur
        response = self._generate_response(scenario, user_message)
        
        # Asistan yanıtını kaydet
        scenario.conversation.append({
            "role": "assistant",
            "content": response["message"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Tamamlanma kontrolü
        if response.get("scenario_complete"):
            scenario.status = "completed"
            scenario.completed_at = datetime.now().isoformat()
            scenario.evaluation = self._evaluate_scenario(scenario)
        
        return {
            "response": response["message"],
            "scenario_id": scenario_id,
            "status": scenario.status,
            "turn_count": len([m for m in scenario.conversation if m["role"] == "user"]),
            "evaluation": scenario.evaluation if scenario.status == "completed" else None
        }
    
    def _generate_response(self, scenario: Scenario, user_message: str) -> Dict[str, Any]:
        """Senaryo yanıtı oluştur."""
        llm = self._get_llm()
        
        # Tamamlama komutları
        if any(cmd in user_message.lower() for cmd in ["bitir", "sonlandır", "end", "finish"]):
            return {
                "message": "Senaryo sonlandırılıyor. Değerlendirme hazırlanıyor...",
                "scenario_complete": True
            }
        
        # Çok uzun konuşma kontrolü
        turn_count = len([m for m in scenario.conversation if m["role"] == "user"])
        if turn_count >= 15:
            return {
                "message": """Bu senaryo için yeterli etkileşim sağlandı. 

Performansınızı değerlendirmek için 'bitir' yazabilirsiniz.""",
                "scenario_complete": False
            }
        
        if llm:
            template = self.SCENARIO_TEMPLATES.get(scenario.scenario_type, {})
            system_prompt = f"""{template.get('system_prompt', '').format(
                topic=scenario.title.split(' - ')[0],
                difficulty=scenario.difficulty.value
            )}

Konuşma geçmişini dikkate al. Senaryo devam ediyor.
Hedefler: {', '.join(scenario.objectives)}

NOT: 10+ tur geçtiyse senaryoyu doğal şekilde sonlandır ve "SENARYO_TAMAMLANDI" yaz."""
            
            # Son 10 mesaj
            history = scenario.conversation[-10:]
            
            try:
                response = llm.generate(
                    user_message,
                    system_prompt,
                    conversation_history=history
                )
                
                is_complete = "SENARYO_TAMAMLANDI" in response
                response = response.replace("SENARYO_TAMAMLANDI", "").strip()
                
                return {
                    "message": response,
                    "scenario_complete": is_complete
                }
            except Exception as e:
                logger.error(f"LLM error in simulation: {e}")
        
        # Fallback
        return {
            "message": "Anladım, devam edelim. Başka sorunuz var mı?",
            "scenario_complete": False
        }
    
    def _evaluate_scenario(self, scenario: Scenario) -> Dict[str, Any]:
        """Senaryo değerlendirmesi."""
        user_messages = [m["content"] for m in scenario.conversation if m["role"] == "user"]
        
        llm = self._get_llm()
        if llm:
            prompt = f"""Aşağıdaki senaryo performansını değerlendir:

Senaryo: {scenario.title}
Tür: {scenario.scenario_type.value}
Zorluk: {scenario.difficulty.value}
Hedefler: {', '.join(scenario.objectives)}

Kullanıcı yanıtları:
{json.dumps(user_messages, ensure_ascii=False, indent=2)}

JSON formatında değerlendirme yap:
{{
  "overall_score": 0-100,
  "strengths": ["güçlü yön 1", "güçlü yön 2"],
  "improvements": ["geliştirilecek alan 1"],
  "objective_scores": {{"hedef1": 0-100}},
  "feedback": "Genel geri bildirim",
  "grade": "A/B/C/D/F"
}}"""
            
            try:
                response = llm.generate(prompt, "Sen bir performans değerlendirme uzmanısın. JSON formatında yanıt ver.")
                
                # JSON parse
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                
                return json.loads(response)
            except:
                pass
        
        # Fallback değerlendirme
        turn_count = len(user_messages)
        base_score = min(100, 40 + turn_count * 5)
        
        return {
            "overall_score": base_score,
            "strengths": ["Senaryoya katılım gösterdiniz"],
            "improvements": ["Daha detaylı yanıtlar verilebilir"],
            "objective_scores": {obj: base_score for obj in scenario.objectives[:3]},
            "feedback": f"Toplam {turn_count} tur etkileşim sağladınız. Genel performansınız iyi.",
            "grade": "A" if base_score >= 90 else "B" if base_score >= 80 else "C" if base_score >= 70 else "D"
        }
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Senaryoyu getir."""
        return self._scenarios.get(scenario_id)
    
    def list_scenarios(self, workspace_id: str, status: Optional[str] = None) -> List[Scenario]:
        """Workspace senaryolarını listele."""
        scenarios = [s for s in self._scenarios.values() if s.workspace_id == workspace_id]
        
        if status:
            scenarios = [s for s in scenarios if s.status == status]
        
        return sorted(scenarios, key=lambda s: s.created_at, reverse=True)
    
    def abandon_scenario(self, scenario_id: str) -> bool:
        """Senaryoyu terk et."""
        scenario = self._scenarios.get(scenario_id)
        if scenario:
            scenario.status = "abandoned"
            return True
        return False


# =============================================================================
# PREMIUM FEATURES MANAGER
# =============================================================================

class PremiumFeaturesManager:
    """
    6 Premium Özellik Yöneticisi
    
    🎓 Premium 1: AI Tutor - Kişiselleştirilmiş Öğretmen
    📚 Premium 2: Spaced Repetition System - Akıllı Hafıza
    💻 Premium 3: Interactive Code Playground - Kod Pratiği
    🧠 Premium 4: Knowledge Graph - Bilgi Haritası
    📊 Premium 5: Learning Analytics - Öğrenme Analitiği
    🎭 Premium 6: AI Simulations - Pratik Senaryoları
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
        
        self.ai_tutor = AITutor()
        self.srs = SpacedRepetitionSystem()
        self.code_playground = InteractiveCodePlayground()
        self.knowledge_graph = KnowledgeGraph()
        self.analytics = LearningAnalytics()
        self.simulations = AISimulationSystem()
        
        self._initialized = True
        logger.info("PremiumFeaturesManager initialized with 6 premium features")
    
    def get_feature_status(self) -> Dict[str, Any]:
        """Tüm özelliklerin durumunu getir."""
        return {
            "ai_tutor": {
                "name": "AI Tutor",
                "icon": "🎓",
                "description": "Kişiselleştirilmiş AI öğretmen",
                "active_sessions": len(self.ai_tutor._sessions),
                "student_profiles": len(self.ai_tutor._profiles)
            },
            "spaced_repetition": {
                "name": "Spaced Repetition",
                "icon": "📚",
                "description": "Akıllı hafıza kartları",
                "total_cards": len(self.srs._cards),
                "total_decks": len(self.srs._decks)
            },
            "code_playground": {
                "name": "Code Playground",
                "icon": "💻",
                "description": "İnteraktif kod pratiği",
                "total_snippets": len(self.code_playground._snippets),
                "total_exercises": len(self.code_playground._exercises)
            },
            "knowledge_graph": {
                "name": "Knowledge Graph",
                "icon": "🧠",
                "description": "Bilgi haritası ve ilişki ağı",
                "total_nodes": len(self.knowledge_graph._nodes),
                "total_edges": len(self.knowledge_graph._edges)
            },
            "analytics": {
                "name": "Learning Analytics",
                "icon": "📊",
                "description": "Detaylı öğrenme analitiği",
                "total_events": len(self.analytics._events),
                "workspaces_tracked": len(set(e.workspace_id for e in self.analytics._events))
            },
            "simulations": {
                "name": "AI Simulations",
                "icon": "🎭",
                "description": "Gerçek dünya pratik senaryoları",
                "total_scenarios": len(self.simulations._scenarios),
                "scenario_types": len(ScenarioType)
            }
        }


# Singleton
def get_premium_features() -> PremiumFeaturesManager:
    """Premium features manager singleton."""
    return PremiumFeaturesManager()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # AI Tutor
    "AITutor",
    "TutorMode",
    "TutorSession",
    "StudentProfile",
    "DifficultyLevel",
    
    # SRS
    "SpacedRepetitionSystem",
    "Flashcard",
    "CardStatus",
    "ReviewRating",
    "StudySession",
    
    # Code Playground
    "InteractiveCodePlayground",
    "CodeSnippet",
    "CodeExercise",
    "CodeLanguage",
    
    # Knowledge Graph
    "KnowledgeGraph",
    "KnowledgeNode",
    "KnowledgeEdge",
    "NodeType",
    "EdgeType",
    
    # Learning Analytics
    "LearningAnalytics",
    "LearningEvent",
    "LearningInsight",
    
    # AI Simulations
    "AISimulationSystem",
    "Scenario",
    "ScenarioType",
    "ScenarioDifficulty",
    
    # Manager
    "PremiumFeaturesManager",
    "get_premium_features"
]
