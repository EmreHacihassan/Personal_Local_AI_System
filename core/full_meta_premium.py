"""
Full Meta Learning - Premium Features Module
Premium öğrenme notları ve gelişmiş özellikler

Features:
- AI Tutor Avatar: Kişiselleştirilmiş AI eğitmen
- Reverse Engineering Mode: Sonuçtan başlayarak öğrenme
- Mastery Certification: Ustalık sertifikasyonu
- Premium Learning Notes: Gelişmiş öğrenme notları oluşturma
- Collaborative Learning: İşbirlikçi öğrenme
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field


# ============ ENUMS ============

class TutorPersonality(str, Enum):
    """AI Tutor kişilik tipleri"""
    SOCRATIC = "socratic"            # Soru sorarak öğretir
    MENTOR = "mentor"                # Destekleyici mentor
    COACH = "coach"                  # Motive edici koç
    PROFESSOR = "professor"          # Detaylı akademik
    FRIEND = "friend"                # Arkadaş gibi
    CHALLENGER = "challenger"        # Meydan okuyan


class NoteType(str, Enum):
    """Not türleri"""
    SUMMARY = "summary"              # Özet
    CORNELL = "cornell"              # Cornell metodu
    MIND_MAP = "mind_map"            # Zihin haritası
    FLASHCARD = "flashcard"          # Flashcard
    OUTLINE = "outline"              # Taslak
    FEYNMAN = "feynman"              # Feynman notu
    VISUAL = "visual"                # Görsel not


class CertificationLevel(str, Enum):
    """Sertifika seviyeleri"""
    BEGINNER = "beginner"            # Başlangıç
    INTERMEDIATE = "intermediate"    # Orta
    ADVANCED = "advanced"            # İleri
    EXPERT = "expert"                # Uzman
    MASTER = "master"                # Usta


class NoteSection(str, Enum):
    """Not bölümleri"""
    KEY_CONCEPTS = "key_concepts"
    DEFINITIONS = "definitions"
    EXAMPLES = "examples"
    CONNECTIONS = "connections"
    QUESTIONS = "questions"
    SUMMARY = "summary"
    ACTION_ITEMS = "action_items"


# ============ DATA CLASSES ============

@dataclass
class AITutorAvatar:
    """AI Tutor Avatar"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Kişilik
    name: str = "Atlas"
    personality: TutorPersonality = TutorPersonality.MENTOR
    
    # Görünüm
    avatar_style: str = "default"    # default, anime, realistic, robot
    avatar_color: str = "#4CAF50"
    
    # Öğretim stili
    explanation_depth: str = "medium"  # brief, medium, detailed
    example_frequency: str = "high"    # low, medium, high
    quiz_frequency: str = "medium"
    encouragement_level: str = "high"  # low, medium, high
    
    # Adaptasyon
    adapted_to_user: bool = False
    learning_style_preference: str = ""
    pace_preference: str = "medium"
    
    # İstatistikler
    sessions_count: int = 0
    total_teaching_minutes: int = 0
    favorite_topics: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TutorSession:
    """Tutor oturumu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tutor_id: str = ""
    user_id: str = ""
    
    topic: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Konuşma
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Öğretim
    concepts_covered: List[str] = field(default_factory=list)
    questions_asked: int = 0
    correct_answers: int = 0
    
    # Değerlendirme
    session_rating: float = 0.0
    user_feedback: str = ""


@dataclass
class ReverseEngineeringSession:
    """Reverse Engineering öğrenme oturumu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Hedef
    target_result: str = ""          # Sonuç/Ürün/Çözüm
    domain: str = ""                 # Alan (programming, science, etc.)
    
    # Dekompozisyon
    components: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Tuple[str, str]] = field(default_factory=list)
    
    # Öğrenme yolu (geriye doğru)
    learning_path: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    
    # İlerleme
    understood_components: List[str] = field(default_factory=list)
    
    started_at: datetime = field(default_factory=datetime.now)


@dataclass
class MasteryCertification:
    """Ustalık sertifikası"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Sertifika bilgileri
    topic: str = ""
    level: CertificationLevel = CertificationLevel.BEGINNER
    title: str = ""
    
    # Başarı kriterleri
    requirements: List[Dict[str, Any]] = field(default_factory=list)
    met_requirements: List[str] = field(default_factory=list)
    
    # Değerlendirme
    final_score: float = 0.0
    assessment_date: Optional[datetime] = None
    
    # Sertifika
    issued: bool = False
    issued_at: Optional[datetime] = None
    certificate_code: str = ""
    
    # Meta
    valid_until: Optional[datetime] = None
    skills_demonstrated: List[str] = field(default_factory=list)


@dataclass
class LearningNote:
    """Öğrenme notu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Not bilgileri
    title: str = ""
    note_type: NoteType = NoteType.SUMMARY
    topic: str = ""
    
    # İçerik bölümleri
    sections: Dict[NoteSection, str] = field(default_factory=dict)
    
    # Rich content
    key_points: List[str] = field(default_factory=list)
    definitions: Dict[str, str] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    diagrams: List[Dict[str, Any]] = field(default_factory=list)
    
    # Cornell method spesifik
    cues: List[str] = field(default_factory=list)       # Sol sütun
    notes: str = ""                                      # Sağ sütun
    summary: str = ""                                    # Alt özet
    
    # Bağlantılar
    related_notes: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    review_count: int = 0
    
    # Kalite
    completeness_score: float = 0.0
    quality_score: float = 0.0


@dataclass
class NoteTemplate:
    """Not şablonu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    note_type: NoteType = NoteType.SUMMARY
    
    # Şablon yapısı
    sections: List[Dict[str, Any]] = field(default_factory=list)
    prompts: Dict[str, str] = field(default_factory=dict)
    
    # Örnek
    example_note: str = ""


# ============ ENGINES ============

class AITutorEngine:
    """AI Tutor Avatar Engine'i"""
    
    # Kişilik bazlı yanıt şablonları
    PERSONALITY_RESPONSES = {
        TutorPersonality.SOCRATIC: {
            "greeting": "Merhaba! Bugün ne keşfetmek istiyorsun? Birlikte sorular sorarak öğrenelim.",
            "correct": "İlginç bir cevap! Peki bunu nasıl biliyorsun? Daha derine inelim.",
            "incorrect": "Hmm, bu cevabı bir düşünelim. Sence başka ne olabilir?",
            "teaching": "Bu konuyu anlamak için sana birkaç soru sormam gerekiyor..."
        },
        TutorPersonality.MENTOR: {
            "greeting": "Hoş geldin! Bugün sana rehberlik etmekten mutluluk duyacağım.",
            "correct": "Harika! Doğru yoldasın. Şimdi bir sonraki adıma geçelim.",
            "incorrect": "Sorun değil, hatalar öğrenmenin parçası. Birlikte düzeltelim.",
            "teaching": "Seninle bu konuyu adım adım keşfedelim..."
        },
        TutorPersonality.COACH: {
            "greeting": "Hazır mısın? Bugün harika şeyler başaracaksın!",
            "correct": "MUHTEŞEM! Tam da beklediğim gibi! Devam et şampiyon!",
            "incorrect": "Hey, bu sadece bir deneme! Kalk ve tekrar dene!",
            "teaching": "Şimdi sana güçlü bir teknik öğreteceğim..."
        },
        TutorPersonality.PROFESSOR: {
            "greeting": "Hoş geldiniz. Bugünkü konumuz oldukça ilginç.",
            "correct": "Doğru. Akademik açıdan tam isabet.",
            "incorrect": "Bu cevap yanlış. Teoriyi tekrar gözden geçirelim.",
            "teaching": "Bu konunun teorik altyapısına bakalım..."
        },
        TutorPersonality.FRIEND: {
            "greeting": "Hey! Bugün ne öğrenmek istiyorsun?",
            "correct": "Aynen! Tam tutturdum derdim ben de!",
            "incorrect": "Yok ya, bu değil ama yaklaştın! Tekrar dene.",
            "teaching": "Bak şimdi, bunu nasıl düşün..."
        },
        TutorPersonality.CHALLENGER: {
            "greeting": "Gel bakalım, ne kadar biliyorsun görelim!",
            "correct": "Hmm, bunu biliyordun. Daha zor bir soru sorayım!",
            "incorrect": "Haha! Yakaladım! Bu kadar kolay değil, tekrar düşün!",
            "teaching": "İşte gerçek meydan okuma başlıyor..."
        }
    }
    
    def __init__(self):
        self.avatars: Dict[str, AITutorAvatar] = {}
        self.sessions: Dict[str, TutorSession] = {}
    
    def create_avatar(self, user_id: str,
                     name: str = "Atlas",
                     personality: TutorPersonality = TutorPersonality.MENTOR) -> AITutorAvatar:
        """Avatar oluştur"""
        avatar = AITutorAvatar(
            user_id=user_id,
            name=name,
            personality=personality
        )
        
        self.avatars[avatar.id] = avatar
        return avatar
    
    def start_session(self, avatar_id: str, topic: str) -> TutorSession:
        """Oturum başlat"""
        avatar = self.avatars.get(avatar_id)
        if not avatar:
            return None
        
        session = TutorSession(
            tutor_id=avatar_id,
            user_id=avatar.user_id,
            topic=topic
        )
        
        # Karşılama mesajı
        greeting = self.PERSONALITY_RESPONSES[avatar.personality]["greeting"]
        session.messages.append({
            "role": "tutor",
            "content": f"{avatar.name}: {greeting}",
            "timestamp": datetime.now().isoformat()
        })
        
        avatar.sessions_count += 1
        self.sessions[session.id] = session
        
        return session
    
    def send_message(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """Kullanıcı mesajı gönder ve yanıt al"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        avatar = self.avatars.get(session.tutor_id)
        if not avatar:
            return {"error": "Avatar not found"}
        
        # Kullanıcı mesajını kaydet
        session.messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Yanıt oluştur (gerçek uygulamada LLM kullanılır)
        response = self._generate_response(avatar, session, user_message)
        
        session.messages.append({
            "role": "tutor",
            "content": f"{avatar.name}: {response['text']}",
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "response": response['text'],
            "tutor_name": avatar.name,
            "action": response.get("action"),
            "question": response.get("question")
        }
    
    def _generate_response(self, avatar: AITutorAvatar, 
                          session: TutorSession,
                          message: str) -> Dict[str, Any]:
        """Yanıt oluştur"""
        personality_responses = self.PERSONALITY_RESPONSES[avatar.personality]
        
        # Basit anahtar kelime analizi (gerçekte LLM kullanılır)
        message_lower = message.lower()
        
        if "anlamadım" in message_lower or "karıştı" in message_lower:
            return {
                "text": "Anlamadığın kısım hangisi? Daha detaylı açıklayayım.",
                "action": "clarify"
            }
        
        if "?" in message:
            return {
                "text": f"İyi soru! {personality_responses['teaching']}",
                "action": "teach"
            }
        
        if "doğru mu" in message_lower or "öyle mi" in message_lower:
            return {
                "text": personality_responses["correct"],
                "action": "confirm"
            }
        
        # Varsayılan öğretim yanıtı
        return {
            "text": personality_responses["teaching"] + f" {session.topic} hakkında konuşalım.",
            "action": "teach",
            "question": "Bu konuda ne biliyorsun?"
        }
    
    def end_session(self, session_id: str, 
                   rating: float = 0.0,
                   feedback: str = "") -> Dict[str, Any]:
        """Oturumu bitir"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session.ended_at = datetime.now()
        session.session_rating = rating
        session.user_feedback = feedback
        
        avatar = self.avatars.get(session.tutor_id)
        if avatar:
            duration = (session.ended_at - session.started_at).seconds // 60
            avatar.total_teaching_minutes += duration
            
            if session.topic not in avatar.favorite_topics:
                avatar.favorite_topics.append(session.topic)
        
        return {
            "session_id": session_id,
            "duration_minutes": (session.ended_at - session.started_at).seconds // 60,
            "messages_count": len(session.messages),
            "concepts_covered": session.concepts_covered
        }


class ReverseEngineeringEngine:
    """Reverse Engineering öğrenme engine'i"""
    
    def __init__(self):
        self.sessions: Dict[str, ReverseEngineeringSession] = {}
    
    def start_session(self, user_id: str,
                     target_result: str,
                     domain: str = "general") -> ReverseEngineeringSession:
        """RE oturumu başlat"""
        session = ReverseEngineeringSession(
            user_id=user_id,
            target_result=target_result,
            domain=domain
        )
        
        # Otomatik dekompozisyon (gerçekte AI/LLM kullanılır)
        session.components = self._decompose(target_result, domain)
        session.learning_path = self._create_reverse_path(session.components)
        
        self.sessions[session.id] = session
        return session
    
    def _decompose(self, target: str, domain: str) -> List[Dict[str, Any]]:
        """Hedegi bileşenlere ayır"""
        # Örnek dekompozisyon (gerçekte domain-specific analiz yapılır)
        if domain == "programming":
            return [
                {"id": "1", "name": "Son Çıktı", "level": 0, "description": target},
                {"id": "2", "name": "Algoritma", "level": 1, "description": "Çözüm algoritması"},
                {"id": "3", "name": "Veri Yapıları", "level": 2, "description": "Kullanılan veri yapıları"},
                {"id": "4", "name": "Temel Kavramlar", "level": 3, "description": "Programlama temelleri"}
            ]
        elif domain == "science":
            return [
                {"id": "1", "name": "Sonuç", "level": 0, "description": target},
                {"id": "2", "name": "Kanıt", "level": 1, "description": "Destekleyen kanıtlar"},
                {"id": "3", "name": "Teori", "level": 2, "description": "Altta yatan teori"},
                {"id": "4", "name": "Temel İlkeler", "level": 3, "description": "Bilimsel ilkeler"}
            ]
        else:
            return [
                {"id": "1", "name": "Hedef", "level": 0, "description": target},
                {"id": "2", "name": "Ara Adımlar", "level": 1, "description": "Ara adımlar"},
                {"id": "3", "name": "Ön Koşullar", "level": 2, "description": "Gerekli bilgiler"}
            ]
    
    def _create_reverse_path(self, 
                            components: List[Dict]) -> List[Dict[str, Any]]:
        """Geriye doğru öğrenme yolu oluştur"""
        # Bileşenleri tersine sırala (sondan başa)
        path = []
        for i, comp in enumerate(components):
            path.append({
                "step": i + 1,
                "component_id": comp["id"],
                "title": comp["name"],
                "description": comp["description"],
                "learning_goals": [f"{comp['name']} kavramını anla"],
                "completed": False
            })
        
        return path
    
    def get_current_step(self, session_id: str) -> Dict[str, Any]:
        """Mevcut adımı al"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if session.current_step >= len(session.learning_path):
            return {"completed": True, "message": "Tüm adımlar tamamlandı!"}
        
        step = session.learning_path[session.current_step]
        
        return {
            "step": step,
            "progress": session.current_step / len(session.learning_path) * 100,
            "remaining_steps": len(session.learning_path) - session.current_step
        }
    
    def complete_step(self, session_id: str) -> Dict[str, Any]:
        """Adımı tamamla"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if session.current_step < len(session.learning_path):
            step = session.learning_path[session.current_step]
            step["completed"] = True
            session.understood_components.append(step["component_id"])
            session.current_step += 1
        
        return self.get_current_step(session_id)


class MasteryCertificationEngine:
    """Ustalık sertifikasyon engine'i"""
    
    # Seviye gereksinimleri
    LEVEL_REQUIREMENTS = {
        CertificationLevel.BEGINNER: {
            "min_score": 60,
            "min_topics": 3,
            "min_practice": 5,
            "title_suffix": "Başlangıç"
        },
        CertificationLevel.INTERMEDIATE: {
            "min_score": 70,
            "min_topics": 5,
            "min_practice": 15,
            "title_suffix": "Orta Seviye"
        },
        CertificationLevel.ADVANCED: {
            "min_score": 80,
            "min_topics": 8,
            "min_practice": 30,
            "title_suffix": "İleri Seviye"
        },
        CertificationLevel.EXPERT: {
            "min_score": 90,
            "min_topics": 12,
            "min_practice": 50,
            "title_suffix": "Uzman"
        },
        CertificationLevel.MASTER: {
            "min_score": 95,
            "min_topics": 15,
            "min_practice": 100,
            "title_suffix": "Usta"
        }
    }
    
    def __init__(self):
        self.certifications: Dict[str, List[MasteryCertification]] = {}
    
    def create_certification_path(self, user_id: str,
                                  topic: str,
                                  target_level: CertificationLevel) -> MasteryCertification:
        """Sertifika yolu oluştur"""
        requirements = self.LEVEL_REQUIREMENTS[target_level]
        
        cert = MasteryCertification(
            user_id=user_id,
            topic=topic,
            level=target_level,
            title=f"{topic} {requirements['title_suffix']} Sertifikası"
        )
        
        # Gereksinimler
        cert.requirements = [
            {"id": "score", "description": f"Minimum %{requirements['min_score']} başarı", "met": False},
            {"id": "topics", "description": f"En az {requirements['min_topics']} alt konu tamamla", "met": False},
            {"id": "practice", "description": f"En az {requirements['min_practice']} pratik yap", "met": False},
            {"id": "assessment", "description": "Final değerlendirmesini geç", "met": False}
        ]
        
        if user_id not in self.certifications:
            self.certifications[user_id] = []
        self.certifications[user_id].append(cert)
        
        return cert
    
    def update_progress(self, cert_id: str,
                       current_score: float,
                       topics_completed: int,
                       practice_count: int) -> Dict[str, Any]:
        """İlerlemeyi güncelle"""
        cert = None
        for user_certs in self.certifications.values():
            for c in user_certs:
                if c.id == cert_id:
                    cert = c
                    break
        
        if not cert:
            return {"error": "Certification not found"}
        
        requirements = self.LEVEL_REQUIREMENTS[cert.level]
        
        # Gereksinimleri kontrol et
        for req in cert.requirements:
            if req["id"] == "score":
                req["met"] = current_score >= requirements["min_score"]
            elif req["id"] == "topics":
                req["met"] = topics_completed >= requirements["min_topics"]
            elif req["id"] == "practice":
                req["met"] = practice_count >= requirements["min_practice"]
        
        cert.met_requirements = [r["id"] for r in cert.requirements if r["met"]]
        
        progress = len(cert.met_requirements) / len(cert.requirements) * 100
        
        return {
            "cert_id": cert_id,
            "progress": progress,
            "requirements": cert.requirements,
            "ready_for_assessment": len(cert.met_requirements) >= 3  # Assessment hariç hepsi
        }
    
    def conduct_assessment(self, cert_id: str,
                          assessment_score: float) -> Dict[str, Any]:
        """Final değerlendirmesi yap"""
        cert = None
        for user_certs in self.certifications.values():
            for c in user_certs:
                if c.id == cert_id:
                    cert = c
                    break
        
        if not cert:
            return {"error": "Certification not found"}
        
        requirements = self.LEVEL_REQUIREMENTS[cert.level]
        
        cert.final_score = assessment_score
        cert.assessment_date = datetime.now()
        
        # Assessment gereksinimini güncelle
        for req in cert.requirements:
            if req["id"] == "assessment":
                req["met"] = assessment_score >= requirements["min_score"]
        
        cert.met_requirements = [r["id"] for r in cert.requirements if r["met"]]
        
        # Tüm gereksinimler karşılandı mı?
        if all(r["met"] for r in cert.requirements):
            cert.issued = True
            cert.issued_at = datetime.now()
            cert.certificate_code = f"CERT-{cert.topic[:3].upper()}-{cert.level.value[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
            cert.valid_until = datetime.now() + timedelta(days=365)  # 1 yıl geçerli
            
            return {
                "passed": True,
                "certificate_code": cert.certificate_code,
                "title": cert.title,
                "score": assessment_score,
                "message": "🎉 Tebrikler! Sertifikanı kazandın!"
            }
        else:
            unmet = [r["description"] for r in cert.requirements if not r["met"]]
            return {
                "passed": False,
                "score": assessment_score,
                "unmet_requirements": unmet,
                "message": "Henüz tüm gereksinimler karşılanmadı."
            }
    
    def get_certificate(self, cert_id: str) -> Dict[str, Any]:
        """Sertifika detaylarını al"""
        for user_certs in self.certifications.values():
            for cert in user_certs:
                if cert.id == cert_id and cert.issued:
                    return {
                        "id": cert.id,
                        "title": cert.title,
                        "topic": cert.topic,
                        "level": cert.level.value,
                        "code": cert.certificate_code,
                        "issued_at": cert.issued_at.isoformat(),
                        "valid_until": cert.valid_until.isoformat() if cert.valid_until else None,
                        "score": cert.final_score,
                        "skills": cert.skills_demonstrated
                    }
        
        return {"error": "Certificate not found or not issued"}


class LearningNotesEngine:
    """Gelişmiş öğrenme notları engine'i"""
    
    # Not şablonları
    TEMPLATES = {
        NoteType.CORNELL: {
            "sections": [NoteSection.KEY_CONCEPTS, NoteSection.DEFINITIONS, 
                        NoteSection.QUESTIONS, NoteSection.SUMMARY],
            "prompts": {
                NoteSection.KEY_CONCEPTS: "Ana kavramları listele...",
                NoteSection.DEFINITIONS: "Önemli terimleri tanımla...",
                NoteSection.QUESTIONS: "Bu konuyla ilgili sorular...",
                NoteSection.SUMMARY: "2-3 cümleyle özetle..."
            }
        },
        NoteType.FEYNMAN: {
            "sections": [NoteSection.KEY_CONCEPTS, NoteSection.EXAMPLES,
                        NoteSection.CONNECTIONS, NoteSection.SUMMARY],
            "prompts": {
                NoteSection.KEY_CONCEPTS: "5 yaşındaki birine nasıl anlatırsın?",
                NoteSection.EXAMPLES: "Günlük hayattan örnekler...",
                NoteSection.CONNECTIONS: "Başka hangi konularla bağlantılı?",
                NoteSection.SUMMARY: "En basit haliyle..."
            }
        },
        NoteType.OUTLINE: {
            "sections": [NoteSection.KEY_CONCEPTS, NoteSection.DEFINITIONS,
                        NoteSection.EXAMPLES, NoteSection.ACTION_ITEMS],
            "prompts": {
                NoteSection.KEY_CONCEPTS: "I. Ana Başlık\n   A. Alt başlık\n      1. Detay",
                NoteSection.DEFINITIONS: "Terimler ve açıklamalar...",
                NoteSection.EXAMPLES: "Örnekler...",
                NoteSection.ACTION_ITEMS: "Yapılacaklar..."
            }
        }
    }
    
    def __init__(self):
        self.notes: Dict[str, List[LearningNote]] = {}
    
    def create_note(self, user_id: str,
                   title: str,
                   topic: str,
                   note_type: NoteType = NoteType.SUMMARY) -> LearningNote:
        """Not oluştur"""
        note = LearningNote(
            user_id=user_id,
            title=title,
            topic=topic,
            note_type=note_type
        )
        
        # Şablon uygula
        if note_type in self.TEMPLATES:
            template = self.TEMPLATES[note_type]
            for section in template["sections"]:
                note.sections[section] = ""
        
        if user_id not in self.notes:
            self.notes[user_id] = []
        self.notes[user_id].append(note)
        
        return note
    
    def update_section(self, note_id: str, user_id: str,
                      section: NoteSection, content: str) -> Dict[str, Any]:
        """Bölüm güncelle"""
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n.id == note_id), None)
        
        if not note:
            return {"error": "Note not found"}
        
        note.sections[section] = content
        note.last_modified = datetime.now()
        
        # Kalite skoru güncelle
        self._update_quality_score(note)
        
        return {
            "note_id": note_id,
            "section": section.value,
            "completeness": note.completeness_score,
            "quality": note.quality_score
        }
    
    def add_key_point(self, note_id: str, user_id: str,
                     point: str) -> bool:
        """Anahtar nokta ekle"""
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n.id == note_id), None)
        
        if not note:
            return False
        
        note.key_points.append(point)
        note.last_modified = datetime.now()
        return True
    
    def add_definition(self, note_id: str, user_id: str,
                      term: str, definition: str) -> bool:
        """Tanım ekle"""
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n.id == note_id), None)
        
        if not note:
            return False
        
        note.definitions[term] = definition
        note.last_modified = datetime.now()
        return True
    
    def add_example(self, note_id: str, user_id: str,
                   example: Dict[str, Any]) -> bool:
        """Örnek ekle"""
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n.id == note_id), None)
        
        if not note:
            return False
        
        note.examples.append({
            "id": str(uuid.uuid4()),
            "title": example.get("title", "Örnek"),
            "content": example.get("content", ""),
            "type": example.get("type", "text")
        })
        note.last_modified = datetime.now()
        return True
    
    def _update_quality_score(self, note: LearningNote) -> None:
        """Kalite skorunu güncelle"""
        # Tamlık skoru
        total_sections = len(note.sections)
        filled_sections = sum(1 for s in note.sections.values() if s.strip())
        note.completeness_score = (filled_sections / total_sections * 100) if total_sections > 0 else 0
        
        # Kalite skoru (içerik zenginliği)
        quality_factors = [
            len(note.key_points) * 5,          # Her key point 5 puan
            len(note.definitions) * 10,         # Her tanım 10 puan
            len(note.examples) * 15,            # Her örnek 15 puan
            len(note.diagrams) * 20             # Her diagram 20 puan
        ]
        note.quality_score = min(100, sum(quality_factors))
    
    def generate_flashcards_from_note(self, note_id: str, 
                                     user_id: str) -> List[Dict[str, Any]]:
        """Nottan flashcard oluştur"""
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n.id == note_id), None)
        
        if not note:
            return []
        
        flashcards = []
        
        # Tanımlardan flashcard
        for term, definition in note.definitions.items():
            flashcards.append({
                "front": f"{term} nedir?",
                "back": definition,
                "source": "definition"
            })
        
        # Key point'lerden flashcard
        for i, point in enumerate(note.key_points):
            flashcards.append({
                "front": f"{note.topic} hakkında önemli nokta #{i+1}:",
                "back": point,
                "source": "key_point"
            })
        
        return flashcards
    
    def get_note_prompts(self, note_type: NoteType) -> Dict[str, str]:
        """Not yazma ipuçları al"""
        template = self.TEMPLATES.get(note_type)
        if template:
            return {s.value: p for s, p in template["prompts"].items()}
        return {}
    
    def export_note(self, note_id: str, user_id: str,
                   format: str = "markdown") -> Optional[str]:
        """Notu export et"""
        user_notes = self.notes.get(user_id, [])
        note = next((n for n in user_notes if n.id == note_id), None)
        
        if not note:
            return None
        
        if format == "markdown":
            return self._to_markdown(note)
        elif format == "html":
            return self._to_html(note)
        else:
            return None
    
    def _to_markdown(self, note: LearningNote) -> str:
        """Markdown'a çevir"""
        md = [f"# {note.title}", "", f"**Konu:** {note.topic}", f"**Tür:** {note.note_type.value}", ""]
        
        # Key Points
        if note.key_points:
            md.append("## 📌 Anahtar Noktalar")
            for point in note.key_points:
                md.append(f"- {point}")
            md.append("")
        
        # Definitions
        if note.definitions:
            md.append("## 📖 Tanımlar")
            for term, definition in note.definitions.items():
                md.append(f"**{term}:** {definition}")
            md.append("")
        
        # Sections
        for section, content in note.sections.items():
            if content:
                md.append(f"## {section.value.replace('_', ' ').title()}")
                md.append(content)
                md.append("")
        
        # Examples
        if note.examples:
            md.append("## 💡 Örnekler")
            for ex in note.examples:
                md.append(f"### {ex['title']}")
                md.append(ex['content'])
                md.append("")
        
        md.append("---")
        md.append(f"*Son güncelleme: {note.last_modified.strftime('%Y-%m-%d %H:%M')}*")
        
        return "\n".join(md)
    
    def _to_html(self, note: LearningNote) -> str:
        """HTML'e çevir"""
        html = [
            "<!DOCTYPE html>",
            "<html><head><style>",
            "body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }",
            "h1 { color: #333; } h2 { color: #666; } .key-point { background: #e8f5e9; padding: 10px; margin: 5px 0; }",
            "</style></head><body>",
            f"<h1>{note.title}</h1>",
            f"<p><strong>Konu:</strong> {note.topic}</p>"
        ]
        
        if note.key_points:
            html.append("<h2>📌 Anahtar Noktalar</h2>")
            for point in note.key_points:
                html.append(f'<div class="key-point">{point}</div>')
        
        if note.definitions:
            html.append("<h2>📖 Tanımlar</h2><dl>")
            for term, definition in note.definitions.items():
                html.append(f"<dt><strong>{term}</strong></dt><dd>{definition}</dd>")
            html.append("</dl>")
        
        html.append("</body></html>")
        return "\n".join(html)


# ============ SINGLETON INSTANCES ============

ai_tutor_engine = AITutorEngine()
reverse_engineering_engine = ReverseEngineeringEngine()
mastery_certification_engine = MasteryCertificationEngine()
learning_notes_engine = LearningNotesEngine()
