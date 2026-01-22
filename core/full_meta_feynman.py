"""
Full Meta Learning - Feynman 2.0 Module
Feynman Tekniği gelişmiş versiyonu

Features:
- Rubber Duck AI: İnteraktif açıklama partneri
- Analogy Generator: Otomatik analoji üretici
- Concept Map Builder: Kavram haritası oluşturucu
- Gap Detector: Bilgi boşluğu tespit sistemi
- Teaching Mode: Öğretme modu simülasyonu
"""

import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict


# ============ ENUMS ============

class ExplanationLevel(str, Enum):
    """Açıklama seviyeleri"""
    CHILD = "child"                  # 5 yaşındaki çocuğa
    BEGINNER = "beginner"            # Başlangıç seviyesi
    INTERMEDIATE = "intermediate"    # Orta seviye
    ADVANCED = "advanced"            # İleri seviye
    EXPERT = "expert"                # Uzman


class GapSeverity(str, Enum):
    """Boşluk şiddeti"""
    MINOR = "minor"                  # Küçük eksik
    MODERATE = "moderate"            # Orta eksik
    MAJOR = "major"                  # Büyük eksik
    CRITICAL = "critical"            # Kritik eksik


class AnalogyDomain(str, Enum):
    """Analoji alanları"""
    EVERYDAY = "everyday"            # Günlük yaşam
    NATURE = "nature"                # Doğa
    SPORTS = "sports"                # Spor
    COOKING = "cooking"              # Yemek
    BUILDING = "building"            # İnşaat/Mimari
    GAMES = "games"                  # Oyunlar
    MUSIC = "music"                  # Müzik
    JOURNEY = "journey"              # Yolculuk


class ConceptRelationType(str, Enum):
    """Kavram ilişki türleri"""
    IS_A = "is_a"                    # "X bir Y'dir"
    HAS_A = "has_a"                  # "X'in Y'si var"
    PART_OF = "part_of"              # "X, Y'nin parçasıdır"
    CAUSES = "causes"                # "X, Y'ye neden olur"
    REQUIRES = "requires"            # "X, Y'yi gerektirir"
    SIMILAR_TO = "similar_to"        # "X, Y'ye benzer"
    OPPOSITE_OF = "opposite_of"      # "X, Y'nin zıttıdır"
    LEADS_TO = "leads_to"            # "X, Y'ye yol açar"


class TeachingPhase(str, Enum):
    """Öğretme fazları"""
    INTRODUCTION = "introduction"    # Giriş
    EXPLANATION = "explanation"      # Açıklama
    EXAMPLE = "example"              # Örnek
    QUESTION = "question"            # Soru
    FEEDBACK = "feedback"            # Geri bildirim
    SUMMARY = "summary"              # Özet


# ============ DATA CLASSES ============

@dataclass
class RubberDuckSession:
    """Rubber Duck (Lastik Ördek) oturumu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Konu
    topic: str = ""
    explanation_level: ExplanationLevel = ExplanationLevel.BEGINNER
    
    # Konuşma geçmişi
    conversation: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tespit edilen sorunlar
    detected_gaps: List[str] = field(default_factory=list)
    unclear_points: List[str] = field(default_factory=list)
    
    # Metrikler
    clarity_score: float = 0.0        # Açıklık skoru (0-100)
    completeness_score: float = 0.0   # Tamlık skoru (0-100)
    simplicity_score: float = 0.0     # Sadelik skoru (0-100)
    
    # Zaman
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Sonuç
    final_summary: str = ""
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class RubberDuckMessage:
    """Rubber Duck mesajı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    role: str = "user"  # user veya duck
    content: str = ""
    
    # Duck yanıtı için
    question_type: str = ""  # clarification, probe, challenge
    detected_issue: str = ""
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Analogy:
    """Analoji"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Kaynak ve hedef
    source_concept: str = ""          # Bilinen kavram
    target_concept: str = ""          # Öğrenilecek kavram
    
    domain: AnalogyDomain = AnalogyDomain.EVERYDAY
    
    # Analoji içeriği
    analogy_text: str = ""
    mapping: List[Dict[str, str]] = field(default_factory=list)  # Eşleştirmeler
    
    # Sınırlamalar
    limitations: List[str] = field(default_factory=list)  # Analoginin sınırları
    
    # Değerlendirme
    effectiveness_score: float = 0.0
    times_used: int = 0


@dataclass
class ConceptNode:
    """Kavram haritası node'u"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    label: str = ""
    description: str = ""
    
    # Görsel
    x: float = 0.0
    y: float = 0.0
    color: str = "#4CAF50"
    size: str = "medium"  # small, medium, large
    
    # İlişkiler
    connections: List[Dict[str, Any]] = field(default_factory=list)
    
    # Meta
    importance: float = 0.5  # 0-1
    mastery_level: float = 0.0  # 0-100


@dataclass
class ConceptMap:
    """Kavram haritası"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    title: str = ""
    topic: str = ""
    
    # Nodes ve edges
    nodes: Dict[str, ConceptNode] = field(default_factory=dict)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    
    # Merkez kavram
    central_concept: str = ""
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeGap:
    """Bilgi boşluğu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    topic: str = ""
    concept: str = ""
    
    # Detay
    description: str = ""
    severity: GapSeverity = GapSeverity.MINOR
    
    # Kanıt
    evidence: List[str] = field(default_factory=list)  # Tespit nedenleri
    related_concepts: List[str] = field(default_factory=list)
    
    # Çözüm
    suggested_resources: List[str] = field(default_factory=list)
    prerequisite_concepts: List[str] = field(default_factory=list)
    
    # Durum
    addressed: bool = False
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class TeachingSession:
    """Öğretme modu oturumu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    topic: str = ""
    target_audience: ExplanationLevel = ExplanationLevel.BEGINNER
    
    # Fazlar ve içerik
    phases: List[Dict[str, Any]] = field(default_factory=list)
    current_phase: TeachingPhase = TeachingPhase.INTRODUCTION
    
    # Sanal öğrenci soruları
    student_questions: List[str] = field(default_factory=list)
    user_answers: List[str] = field(default_factory=list)
    
    # Değerlendirme
    teaching_score: float = 0.0
    clarity_feedback: List[str] = field(default_factory=list)
    
    completed: bool = False


# ============ ENGINES ============

class RubberDuckEngine:
    """Rubber Duck AI Engine'i - İnteraktif açıklama partneri"""
    
    # Soru şablonları
    CLARIFICATION_QUESTIONS = [
        "Bu kavramı biraz daha açar mısın?",
        "'{term}' derken tam olarak neyi kastediyorsun?",
        "Bu nasıl çalışıyor?",
        "Bir örnek verebilir misin?",
        "Bu neden önemli?"
    ]
    
    PROBING_QUESTIONS = [
        "Peki bu {related} ile nasıl ilişkili?",
        "Ya {scenario} durumunda ne olur?",
        "Bunun tersini düşünürsek?",
        "Alternatif bir yaklaşım olabilir mi?",
        "Bu kuralın istisnası var mı?"
    ]
    
    CHALLENGE_QUESTIONS = [
        "Emin misin? Bence {alternative} olabilir.",
        "Ama {contradiction} durumunda bu çalışmaz mı?",
        "Bu çok karmaşık görünüyor, daha basit açıklayabilir misin?",
        "Neden {alternative} değil de bu?",
        "Bunu kanıtlayan bir örnek var mı?"
    ]
    
    # Jargon ve karmaşık terimler (basitleştirilmeli)
    COMPLEXITY_INDICATORS = [
        r'\b(algoritma|paradigma|abstraksiyon|polimorfizm)\b',
        r'\b(implementasyon|instantiate|encapsulation)\b',
        r'\b(recursive|iterative|concurrent)\b',
        r'[A-Z]{2,}',  # Kısaltmalar
    ]
    
    def __init__(self):
        self.sessions: Dict[str, RubberDuckSession] = {}
    
    def start_session(self, user_id: str, topic: str,
                     level: ExplanationLevel = ExplanationLevel.BEGINNER) -> RubberDuckSession:
        """Yeni oturum başlat"""
        session = RubberDuckSession(
            user_id=user_id,
            topic=topic,
            explanation_level=level
        )
        
        # İlk duck mesajı
        intro_message = RubberDuckMessage(
            role="duck",
            content=f"🦆 Merhaba! Ben Rubber Duck, senin öğrenme partnerinim. "
                   f"'{topic}' konusunu bana açıklayacaksın. "
                   f"Sanki ben {self._level_description(level)} gibi açıkla. Hazırsan başla!"
        )
        session.conversation.append(vars(intro_message))
        
        self.sessions[session.id] = session
        return session
    
    def _level_description(self, level: ExplanationLevel) -> str:
        """Seviye açıklaması"""
        descriptions = {
            ExplanationLevel.CHILD: "5 yaşında bir çocuğum",
            ExplanationLevel.BEGINNER: "bu konuyu hiç bilmiyorum",
            ExplanationLevel.INTERMEDIATE: "temel bilgileri biliyorum",
            ExplanationLevel.ADVANCED: "ileri seviye bir öğrenciyim",
            ExplanationLevel.EXPERT: "alan uzmanıyım"
        }
        return descriptions.get(level, "bu konuyu bilmiyorum")
    
    def process_explanation(self, session_id: str, 
                           explanation: str) -> Dict[str, Any]:
        """Açıklamayı işle ve yanıt üret"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Kullanıcı mesajını ekle
        user_msg = RubberDuckMessage(role="user", content=explanation)
        session.conversation.append(vars(user_msg))
        
        # Analiz yap
        analysis = self._analyze_explanation(explanation, session.explanation_level)
        
        # Duck yanıtı oluştur
        duck_response = self._generate_duck_response(analysis, session)
        
        # Skorları güncelle
        session.clarity_score = analysis["clarity"]
        session.completeness_score = analysis["completeness"]
        session.simplicity_score = analysis["simplicity"]
        
        # Eksikleri kaydet
        session.detected_gaps.extend(analysis.get("gaps", []))
        session.unclear_points.extend(analysis.get("unclear", []))
        
        # Duck mesajını ekle
        duck_msg = RubberDuckMessage(
            role="duck",
            content=duck_response["response"],
            question_type=duck_response["type"],
            detected_issue=duck_response.get("issue", "")
        )
        session.conversation.append(vars(duck_msg))
        
        return {
            "response": duck_response["response"],
            "question_type": duck_response["type"],
            "scores": {
                "clarity": session.clarity_score,
                "completeness": session.completeness_score,
                "simplicity": session.simplicity_score
            },
            "detected_issues": analysis.get("issues", [])
        }
    
    def _analyze_explanation(self, text: str, 
                            level: ExplanationLevel) -> Dict[str, Any]:
        """Açıklamayı analiz et"""
        analysis = {
            "clarity": 0.0,
            "completeness": 0.0,
            "simplicity": 0.0,
            "gaps": [],
            "unclear": [],
            "issues": []
        }
        
        # Uzunluk kontrolü
        word_count = len(text.split())
        if word_count < 10:
            analysis["issues"].append("Açıklama çok kısa")
            analysis["completeness"] = 30
        elif word_count > 500:
            analysis["issues"].append("Açıklama çok uzun, odaklan")
            analysis["completeness"] = 70
        else:
            analysis["completeness"] = min(100, 50 + word_count * 0.5)
        
        # Jargon kontrolü
        jargon_count = 0
        for pattern in self.COMPLEXITY_INDICATORS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            jargon_count += len(matches)
        
        if level in [ExplanationLevel.CHILD, ExplanationLevel.BEGINNER]:
            if jargon_count > 0:
                analysis["issues"].append(f"{jargon_count} teknik terim var, basitleştir")
                analysis["simplicity"] = max(0, 100 - jargon_count * 15)
            else:
                analysis["simplicity"] = 90
        else:
            analysis["simplicity"] = 80
        
        # Örnek kontrolü
        has_example = any(word in text.lower() for word in 
                         ["örneğin", "mesela", "gibi", "örnek"])
        if not has_example:
            analysis["issues"].append("Örnek yok")
            analysis["clarity"] = 60
        else:
            analysis["clarity"] = 85
        
        # "Şey", "falan" gibi belirsiz ifadeler
        vague_words = len(re.findall(r'\b(şey|falan|filan|bir nevi|gibi bir şey)\b', 
                                      text, re.IGNORECASE))
        if vague_words > 0:
            analysis["unclear"].append("Belirsiz ifadeler kullanılmış")
            analysis["clarity"] -= vague_words * 10
        
        return analysis
    
    def _generate_duck_response(self, analysis: Dict, 
                               session: RubberDuckSession) -> Dict[str, Any]:
        """Duck yanıtı üret"""
        import random
        
        issues = analysis.get("issues", [])
        
        # En ciddi soruna göre yanıt seç
        if analysis["simplicity"] < 50:
            question = random.choice([
                "🦆 Hmm, bu biraz karmaşık geldi. Daha basit anlatabilir misin?",
                "🦆 Teknik terimler kafamı karıştırdı. Günlük dille açıklar mısın?",
                "🦆 Sanki ders kitabı okuyorum. Arkadaşına anlatır gibi anlat!"
            ])
            return {"response": question, "type": "simplification", "issue": "complexity"}
        
        if analysis["completeness"] < 50:
            question = random.choice([
                "🦆 Peki sonra ne oluyor? Devam et!",
                "🦆 Anlattın ama eksik bir şeyler var gibi. Biraz daha detay?",
                "🦆 Bu kadar mı? Daha fazlası olmalı!"
            ])
            return {"response": question, "type": "elaboration", "issue": "incomplete"}
        
        if analysis["clarity"] < 70:
            question = random.choice([
                "🦆 Örnek verebilir misin? Somutlaştır biraz.",
                "🦆 Anladım gibi ama... Bir örnek verirsen daha iyi anlarım.",
                "🦆 Görsel düşünmemi ister misin? Bunu nasıl hayal edebilirim?"
            ])
            return {"response": question, "type": "example_request", "issue": "no_example"}
        
        # Her şey iyi - ileri soru sor
        probing = random.choice([
            "🦆 Harika açıklama! Peki bu neden önemli?",
            "🦆 Anladım! Bunun tersi nasıl olurdu?",
            "🦆 Güzel! Bunu günlük hayatta nasıl kullanırım?",
            "🦆 Süper! Bununla ilgili başka ne biliyorsun?"
        ])
        return {"response": probing, "type": "probing", "issue": ""}
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """Oturumu bitir ve özet oluştur"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session.ended_at = datetime.now()
        
        # Genel skor hesapla
        overall_score = (
            session.clarity_score * 0.4 +
            session.completeness_score * 0.3 +
            session.simplicity_score * 0.3
        )
        
        # İyileştirme önerileri
        suggestions = []
        if session.clarity_score < 70:
            suggestions.append("Daha fazla somut örnek kullan")
        if session.simplicity_score < 70:
            suggestions.append("Teknik terimleri günlük dile çevir")
        if session.completeness_score < 70:
            suggestions.append("Konuyu daha kapsamlı açıkla")
        if session.detected_gaps:
            suggestions.append(f"Şu konuları gözden geçir: {', '.join(session.detected_gaps[:3])}")
        
        session.improvement_suggestions = suggestions
        session.final_summary = f"'{session.topic}' konusunu açıklama puanın: {overall_score:.0f}/100"
        
        return {
            "session_id": session_id,
            "topic": session.topic,
            "overall_score": overall_score,
            "scores": {
                "clarity": session.clarity_score,
                "completeness": session.completeness_score,
                "simplicity": session.simplicity_score
            },
            "improvements": suggestions,
            "detected_gaps": session.detected_gaps,
            "conversation_length": len(session.conversation)
        }


class AnalogyGeneratorEngine:
    """Analoji üretim engine'i"""
    
    # Domain-spesifik analoji şablonları
    ANALOGY_TEMPLATES = {
        AnalogyDomain.EVERYDAY: [
            "{target} tıpkı {source} gibidir. {mapping}",
            "{target}'i anlamak için {source}'i düşün. {mapping}",
            "Nasıl ki {source}, {target} de öyle. {mapping}"
        ],
        AnalogyDomain.COOKING: [
            "{target}, yemek yapmak gibidir. {mapping}",
            "{target}'i bir tarif gibi düşün. {mapping}",
            "Tıpkı bir şefin {source} yapması gibi, {target} de öyle çalışır. {mapping}"
        ],
        AnalogyDomain.BUILDING: [
            "{target}, bir bina inşa etmek gibidir. {mapping}",
            "{target}'i mimari açıdan düşün. {mapping}",
            "Nasıl bir {source} temel gerektirir, {target} de öyle. {mapping}"
        ],
        AnalogyDomain.JOURNEY: [
            "{target}, bir yolculuk gibidir. {mapping}",
            "{target}'i bir haritada navigasyon gibi düşün. {mapping}",
            "Tıpkı bir gezginin {source} yapması gibi. {mapping}"
        ],
        AnalogyDomain.GAMES: [
            "{target}, oyun oynamak gibidir. {mapping}",
            "{target}'i satranç/puzzle gibi düşün. {mapping}",
            "Tıpkı bir oyunda {source} gibi, {target} da öyle çalışır. {mapping}"
        ]
    }
    
    # Yaygın kavram-analoji eşleştirmeleri
    CONCEPT_ANALOGIES = {
        "recursion": {
            "domain": AnalogyDomain.EVERYDAY,
            "source": "aynalar karşı karşıya",
            "mapping": "Fonksiyon kendini çağırır, tıpkı iki aynanın sonsuz yansıma yapması gibi"
        },
        "variable": {
            "domain": AnalogyDomain.EVERYDAY,
            "source": "etiketli kutu",
            "mapping": "Değişken bir kutu, içine değer koyarsın ve etiketle isimlendirirsin"
        },
        "function": {
            "domain": AnalogyDomain.COOKING,
            "source": "tarif",
            "mapping": "Fonksiyon bir tarif, malzeme verirsin (input), yemek çıkar (output)"
        },
        "array": {
            "domain": AnalogyDomain.EVERYDAY,
            "source": "tren vagonları",
            "mapping": "Array sıralı vagonlar gibi, her vagonda bir yolcu (değer), numara ile erişirsin"
        },
        "database": {
            "domain": AnalogyDomain.EVERYDAY,
            "source": "kütüphane",
            "mapping": "Veritabanı organize bir kütüphane, kitaplar (veriler) raflarla (tablolar) düzenlenir"
        },
        "api": {
            "domain": AnalogyDomain.COOKING,
            "source": "restoran menüsü",
            "mapping": "API menü gibi, ne isteyebileceğini listeler, mutfağa (sunucu) iletir, yemek (veri) gelir"
        },
        "class": {
            "domain": AnalogyDomain.BUILDING,
            "source": "mimari plan",
            "mapping": "Sınıf bir plan, instance (nesne) ise o plandan yapılan gerçek bina"
        },
        "inheritance": {
            "domain": AnalogyDomain.EVERYDAY,
            "source": "aile soy ağacı",
            "mapping": "Kalıtım aile gibi, çocuk ebeveynin özelliklerini alır ama kendi özellikleri de olur"
        }
    }
    
    def __init__(self):
        self.analogies: Dict[str, Analogy] = {}
        self.user_ratings: Dict[str, List[float]] = {}
    
    def generate_analogy(self, concept: str,
                        preferred_domain: AnalogyDomain = None) -> Analogy:
        """Kavram için analoji üret"""
        
        # Hazır analoji var mı?
        concept_lower = concept.lower()
        if concept_lower in self.CONCEPT_ANALOGIES:
            preset = self.CONCEPT_ANALOGIES[concept_lower]
            domain = preferred_domain or preset["domain"]
            
            analogy = Analogy(
                source_concept=preset["source"],
                target_concept=concept,
                domain=domain,
                analogy_text=preset["mapping"],
                mapping=[{"from": preset["source"], "to": concept}]
            )
        else:
            # Genel analoji oluştur
            domain = preferred_domain or AnalogyDomain.EVERYDAY
            templates = self.ANALOGY_TEMPLATES.get(domain, self.ANALOGY_TEMPLATES[AnalogyDomain.EVERYDAY])
            
            import random
            template = random.choice(templates)
            
            # Basit source üret (gerçek uygulamada LLM kullanılır)
            generic_sources = {
                AnalogyDomain.EVERYDAY: "günlük bir aktivite",
                AnalogyDomain.COOKING: "yemek yapmak",
                AnalogyDomain.BUILDING: "ev inşa etmek",
                AnalogyDomain.JOURNEY: "seyahat etmek",
                AnalogyDomain.GAMES: "oyun oynamak"
            }
            
            source = generic_sources.get(domain, "bir aktivite")
            
            analogy = Analogy(
                source_concept=source,
                target_concept=concept,
                domain=domain,
                analogy_text=template.format(
                    target=concept,
                    source=source,
                    mapping=f"{concept}, {source} ile benzer mantıkla çalışır."
                )
            )
        
        # Sınırlamalar ekle
        analogy.limitations = [
            "Her analoji mükemmel değildir, bazı detaylar farklı olabilir.",
            "Analoginin sınırlarını aşan durumlar için orijinal kavramı incele."
        ]
        
        self.analogies[analogy.id] = analogy
        return analogy
    
    def rate_analogy(self, analogy_id: str, rating: float) -> None:
        """Analojiyi değerlendir"""
        analogy = self.analogies.get(analogy_id)
        if not analogy:
            return
        
        if analogy_id not in self.user_ratings:
            self.user_ratings[analogy_id] = []
        
        self.user_ratings[analogy_id].append(rating)
        analogy.effectiveness_score = sum(self.user_ratings[analogy_id]) / len(self.user_ratings[analogy_id])
        analogy.times_used += 1
    
    def get_best_analogies(self, concept: str, limit: int = 3) -> List[Analogy]:
        """En iyi analojileri al"""
        concept_lower = concept.lower()
        
        matching = [a for a in self.analogies.values() 
                   if concept_lower in a.target_concept.lower()]
        
        # Effectiveness'a göre sırala
        matching.sort(key=lambda x: x.effectiveness_score, reverse=True)
        
        return matching[:limit]


class ConceptMapBuilderEngine:
    """Kavram haritası oluşturma engine'i"""
    
    def __init__(self):
        self.maps: Dict[str, ConceptMap] = {}
    
    def create_map(self, title: str, topic: str,
                   central_concept: str) -> ConceptMap:
        """Yeni kavram haritası oluştur"""
        concept_map = ConceptMap(
            title=title,
            topic=topic,
            central_concept=central_concept
        )
        
        # Merkez node ekle
        center_node = ConceptNode(
            label=central_concept,
            x=400,
            y=300,
            color="#FF5722",
            size="large",
            importance=1.0
        )
        concept_map.nodes[center_node.id] = center_node
        
        self.maps[concept_map.id] = concept_map
        return concept_map
    
    def add_concept(self, map_id: str, label: str,
                   connected_to: str,
                   relation_type: ConceptRelationType,
                   description: str = "") -> Optional[ConceptNode]:
        """Kavram ekle"""
        concept_map = self.maps.get(map_id)
        if not concept_map:
            return None
        
        # Bağlanacak node'u bul
        target_node = None
        for node in concept_map.nodes.values():
            if node.label.lower() == connected_to.lower() or node.id == connected_to:
                target_node = node
                break
        
        if not target_node:
            return None
        
        # Pozisyon hesapla (basit radial layout)
        import math
        existing_connections = len([e for e in concept_map.edges 
                                   if e["from"] == target_node.id])
        angle = existing_connections * (2 * math.pi / 6)
        radius = 150
        
        x = target_node.x + radius * math.cos(angle)
        y = target_node.y + radius * math.sin(angle)
        
        # Yeni node
        new_node = ConceptNode(
            label=label,
            description=description,
            x=x,
            y=y,
            color=self._get_color_for_relation(relation_type),
            size="medium"
        )
        
        concept_map.nodes[new_node.id] = new_node
        
        # Edge ekle
        concept_map.edges.append({
            "from": target_node.id,
            "to": new_node.id,
            "relation": relation_type.value,
            "label": relation_type.value.replace("_", " ")
        })
        
        concept_map.last_modified = datetime.now()
        
        return new_node
    
    def _get_color_for_relation(self, relation: ConceptRelationType) -> str:
        """İlişki türüne göre renk"""
        colors = {
            ConceptRelationType.IS_A: "#4CAF50",
            ConceptRelationType.HAS_A: "#2196F3",
            ConceptRelationType.PART_OF: "#9C27B0",
            ConceptRelationType.CAUSES: "#FF9800",
            ConceptRelationType.REQUIRES: "#F44336",
            ConceptRelationType.SIMILAR_TO: "#00BCD4",
            ConceptRelationType.OPPOSITE_OF: "#E91E63",
            ConceptRelationType.LEADS_TO: "#795548"
        }
        return colors.get(relation, "#607D8B")
    
    def get_map_data(self, map_id: str) -> Optional[Dict[str, Any]]:
        """Harita verisini al (görselleştirme için)"""
        concept_map = self.maps.get(map_id)
        if not concept_map:
            return None
        
        return {
            "id": concept_map.id,
            "title": concept_map.title,
            "topic": concept_map.topic,
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "description": n.description,
                    "x": n.x,
                    "y": n.y,
                    "color": n.color,
                    "size": n.size,
                    "mastery": n.mastery_level
                }
                for n in concept_map.nodes.values()
            ],
            "edges": concept_map.edges,
            "central": concept_map.central_concept
        }
    
    def suggest_connections(self, map_id: str, 
                           new_concept: str) -> List[Dict[str, Any]]:
        """Yeni kavram için bağlantı öner"""
        concept_map = self.maps.get(map_id)
        if not concept_map:
            return []
        
        suggestions = []
        for node in concept_map.nodes.values():
            # Basit benzerlik kontrolü (gerçekte NLP/LLM kullanılır)
            suggestions.append({
                "target_node": node.label,
                "suggested_relations": [
                    ConceptRelationType.SIMILAR_TO.value,
                    ConceptRelationType.PART_OF.value,
                    ConceptRelationType.LEADS_TO.value
                ],
                "confidence": 0.5  # Placeholder
            })
        
        return suggestions[:5]


class GapDetectorEngine:
    """Bilgi boşluğu tespit engine'i"""
    
    # Boşluk göstergeleri
    GAP_INDICATORS = {
        "vague_language": [
            r'\b(bir şey|falan|filan|galiba|sanırım|belki)\b',
            r'\b(gibi bir şey|bir nevi|tarzında)\b'
        ],
        "uncertainty": [
            r'\b(emin değilim|bilmiyorum|hatırlamıyorum)\b',
            r'\b(karışık|kafam karıştı|anlamadım)\b'
        ],
        "incomplete": [
            r'\b(sonra|devamı|detay)\b.*\?',
            r'\.\.\.$',
            r'\b(vs|vb|etc)\b'
        ]
    }
    
    def __init__(self):
        self.gaps: Dict[str, List[KnowledgeGap]] = {}  # user_id -> gaps
    
    def analyze_explanation(self, user_id: str, topic: str,
                           explanation: str) -> List[KnowledgeGap]:
        """Açıklamayı analiz et ve boşlukları tespit et"""
        detected_gaps = []
        
        # Belirsiz dil kontrolü
        for pattern in self.GAP_INDICATORS["vague_language"]:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            if matches:
                gap = KnowledgeGap(
                    topic=topic,
                    concept="Belirsiz kavramlar",
                    description=f"Belirsiz ifadeler kullanılmış: {', '.join(matches[:3])}",
                    severity=GapSeverity.MINOR,
                    evidence=matches
                )
                detected_gaps.append(gap)
        
        # Belirsizlik kontrolü
        for pattern in self.GAP_INDICATORS["uncertainty"]:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            if matches:
                gap = KnowledgeGap(
                    topic=topic,
                    concept="Emin olunmayan konular",
                    description="Belirsizlik ifadeleri tespit edildi",
                    severity=GapSeverity.MODERATE,
                    evidence=matches
                )
                detected_gaps.append(gap)
        
        # Eksik açıklama kontrolü
        for pattern in self.GAP_INDICATORS["incomplete"]:
            matches = re.findall(pattern, explanation, re.IGNORECASE)
            if matches:
                gap = KnowledgeGap(
                    topic=topic,
                    concept="Tamamlanmamış açıklama",
                    description="Açıklama eksik veya devamı var",
                    severity=GapSeverity.MODERATE,
                    evidence=matches
                )
                detected_gaps.append(gap)
        
        # Kaydet
        if user_id not in self.gaps:
            self.gaps[user_id] = []
        self.gaps[user_id].extend(detected_gaps)
        
        return detected_gaps
    
    def analyze_quiz_results(self, user_id: str, topic: str,
                            results: List[Dict[str, Any]]) -> List[KnowledgeGap]:
        """Quiz sonuçlarından boşluk tespit et"""
        detected_gaps = []
        
        # Yanlış cevapları grupla
        wrong_topics = defaultdict(list)
        for result in results:
            if not result.get("correct"):
                wrong_topics[result.get("subtopic", topic)].append(result)
        
        # Her topic için boşluk oluştur
        for subtopic, wrongs in wrong_topics.items():
            if len(wrongs) >= 2:
                severity = GapSeverity.MAJOR if len(wrongs) >= 4 else GapSeverity.MODERATE
            else:
                severity = GapSeverity.MINOR
            
            gap = KnowledgeGap(
                topic=topic,
                concept=subtopic,
                description=f"{len(wrongs)} yanlış cevap tespit edildi",
                severity=severity,
                evidence=[f"Soru: {w.get('question', 'N/A')}" for w in wrongs[:3]]
            )
            detected_gaps.append(gap)
        
        if user_id not in self.gaps:
            self.gaps[user_id] = []
        self.gaps[user_id].extend(detected_gaps)
        
        return detected_gaps
    
    def get_gap_summary(self, user_id: str) -> Dict[str, Any]:
        """Boşluk özeti"""
        user_gaps = self.gaps.get(user_id, [])
        
        if not user_gaps:
            return {"has_gaps": False, "message": "Tespit edilen boşluk yok!"}
        
        severity_counts = defaultdict(int)
        topic_gaps = defaultdict(list)
        
        for gap in user_gaps:
            if not gap.addressed:
                severity_counts[gap.severity.value] += 1
                topic_gaps[gap.topic].append(gap.concept)
        
        # Öncelikli boşluklar (kritik ve major)
        priority_gaps = [g for g in user_gaps 
                        if g.severity in [GapSeverity.CRITICAL, GapSeverity.MAJOR]
                        and not g.addressed]
        
        return {
            "has_gaps": True,
            "total_gaps": len([g for g in user_gaps if not g.addressed]),
            "severity_distribution": dict(severity_counts),
            "topics_with_gaps": dict(topic_gaps),
            "priority_gaps": [
                {
                    "topic": g.topic,
                    "concept": g.concept,
                    "severity": g.severity.value,
                    "description": g.description
                }
                for g in priority_gaps[:5]
            ]
        }
    
    def mark_gap_addressed(self, gap_id: str) -> bool:
        """Boşluğu giderildi olarak işaretle"""
        for user_gaps in self.gaps.values():
            for gap in user_gaps:
                if gap.id == gap_id:
                    gap.addressed = True
                    return True
        return False


class TeachingModeEngine:
    """Öğretme modu engine'i - Sanal öğrenci simülasyonu"""
    
    # Sanal öğrenci soruları
    STUDENT_QUESTIONS = {
        ExplanationLevel.CHILD: [
            "Neden?",
            "Bu ne işe yarıyor?",
            "Bunu gösterebilir misin?",
            "Anlamadım, tekrar söyler misin?"
        ],
        ExplanationLevel.BEGINNER: [
            "Bu ne demek?",
            "Örnek verebilir misin?",
            "Bunu nerede kullanırım?",
            "Zor geldi, basitleştirebilir misin?"
        ],
        ExplanationLevel.INTERMEDIATE: [
            "Peki bunun X ile ilişkisi ne?",
            "Alternatifi var mı?",
            "Avantajları ve dezavantajları neler?",
            "Gerçek dünyada nasıl uygulanır?"
        ],
        ExplanationLevel.ADVANCED: [
            "Edge case'lerde ne olur?",
            "Performans etkileri neler?",
            "Best practice'ler neler?",
            "Trade-off'ları neler?"
        ]
    }
    
    def __init__(self):
        self.sessions: Dict[str, TeachingSession] = {}
        self.rubber_duck = RubberDuckEngine()
        self.gap_detector = GapDetectorEngine()
    
    def start_teaching_session(self, user_id: str, topic: str,
                               audience: ExplanationLevel = ExplanationLevel.BEGINNER) -> TeachingSession:
        """Öğretme oturumu başlat"""
        session = TeachingSession(
            user_id=user_id,
            topic=topic,
            target_audience=audience
        )
        
        # Fazları hazırla
        session.phases = [
            {"phase": TeachingPhase.INTRODUCTION.value, "prompt": f"'{topic}' konusunu tanıt."},
            {"phase": TeachingPhase.EXPLANATION.value, "prompt": "Ana kavramları açıkla."},
            {"phase": TeachingPhase.EXAMPLE.value, "prompt": "Somut örnekler ver."},
            {"phase": TeachingPhase.QUESTION.value, "prompt": "Öğrenci sorularını yanıtla."},
            {"phase": TeachingPhase.SUMMARY.value, "prompt": "Özet yap."}
        ]
        
        self.sessions[session.id] = session
        return session
    
    def submit_teaching(self, session_id: str, 
                       content: str) -> Dict[str, Any]:
        """Öğretme içeriği gönder"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # Mevcut faz
        current_phase_idx = [
            i for i, p in enumerate(session.phases) 
            if p["phase"] == session.current_phase.value
        ]
        current_phase_idx = current_phase_idx[0] if current_phase_idx else 0
        
        # İçeriği değerlendir
        gaps = self.gap_detector.analyze_explanation(
            session.user_id, session.topic, content
        )
        
        # Sanal öğrenci sorusu oluştur
        import random
        questions = self.STUDENT_QUESTIONS.get(
            session.target_audience, 
            self.STUDENT_QUESTIONS[ExplanationLevel.BEGINNER]
        )
        student_question = random.choice(questions)
        session.student_questions.append(student_question)
        
        # Fazı güncelle
        session.phases[current_phase_idx]["content"] = content
        session.phases[current_phase_idx]["gaps"] = [g.description for g in gaps]
        
        # Sonraki faza geç
        if current_phase_idx < len(session.phases) - 1:
            next_phase = TeachingPhase(session.phases[current_phase_idx + 1]["phase"])
            session.current_phase = next_phase
        else:
            session.completed = True
        
        return {
            "student_question": f"🙋 Öğrenci: {student_question}",
            "feedback": self._generate_feedback(content, gaps),
            "current_phase": session.current_phase.value,
            "completed": session.completed,
            "detected_gaps": [g.description for g in gaps],
            "progress": (current_phase_idx + 1) / len(session.phases) * 100
        }
    
    def _generate_feedback(self, content: str, 
                          gaps: List[KnowledgeGap]) -> str:
        """Geri bildirim oluştur"""
        if not gaps:
            return "👏 Harika açıklama! Devam et."
        
        feedback_parts = ["📝 Geri bildirim:"]
        for gap in gaps[:2]:
            if gap.severity in [GapSeverity.MAJOR, GapSeverity.CRITICAL]:
                feedback_parts.append(f"⚠️ {gap.description}")
            else:
                feedback_parts.append(f"💡 {gap.description}")
        
        return " ".join(feedback_parts)
    
    def finish_teaching(self, session_id: str) -> Dict[str, Any]:
        """Öğretme oturumunu bitir"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session.completed = True
        
        # Skor hesapla
        total_gaps = sum(len(p.get("gaps", [])) for p in session.phases)
        covered_phases = sum(1 for p in session.phases if p.get("content"))
        
        completeness = covered_phases / len(session.phases) * 100
        clarity = max(0, 100 - total_gaps * 10)
        
        session.teaching_score = (completeness * 0.6 + clarity * 0.4)
        
        return {
            "session_id": session_id,
            "topic": session.topic,
            "teaching_score": session.teaching_score,
            "phases_completed": covered_phases,
            "total_phases": len(session.phases),
            "student_questions_answered": len(session.user_answers),
            "clarity_score": clarity,
            "feedback": self._final_feedback(session)
        }
    
    def _final_feedback(self, session: TeachingSession) -> List[str]:
        """Final geri bildirim"""
        feedback = []
        
        if session.teaching_score >= 80:
            feedback.append("🌟 Mükemmel öğretme becerisi!")
        elif session.teaching_score >= 60:
            feedback.append("👍 İyi iş, biraz daha pratikle ustalaşırsın.")
        else:
            feedback.append("📚 Konuyu tekrar gözden geçirmeni öneririm.")
        
        # Faz bazlı feedback
        for phase in session.phases:
            if not phase.get("content"):
                feedback.append(f"⚠️ {phase['phase']} aşamasını tamamlamadın.")
            elif phase.get("gaps"):
                feedback.append(f"💡 {phase['phase']}: {phase['gaps'][0]}")
        
        return feedback


# ============ SINGLETON INSTANCES ============

rubber_duck_engine = RubberDuckEngine()
analogy_generator_engine = AnalogyGeneratorEngine()
concept_map_builder_engine = ConceptMapBuilderEngine()
gap_detector_engine = GapDetectorEngine()
teaching_mode_engine = TeachingModeEngine()
