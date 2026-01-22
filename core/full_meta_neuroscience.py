"""
Full Meta Learning - Neuroscience Module
Nörobilim tabanlı öğrenme teknikleri

Features:
- Theta Wave Sync: Beyin dalgası simülasyonu döngüleri
- Memory Palace AI: Sanal bellek sarayı sistemi
- Chunking Intelligence: Miller's Law (7±2) optimizasyonu
- Dual Coding: Metin + görsel çift kodlama
- Interleaving Mode: Karışık öğrenme modu
"""

import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel


# ============ ENUMS ============

class BrainWaveState(str, Enum):
    """Beyin dalgası durumları"""
    THETA = "theta"       # 4-8 Hz - Derin öğrenme, hafıza kodlama
    ALPHA = "alpha"       # 8-12 Hz - Rahat uyanıklık, dinlenme
    BETA = "beta"         # 12-30 Hz - Aktif düşünme, konsantrasyon
    GAMMA = "gamma"       # 30-100 Hz - Yüksek bilişsel işlem
    DELTA = "delta"       # 0.5-4 Hz - Derin uyku, hafıza konsolidasyonu


class LearningStyle(str, Enum):
    """Öğrenme stilleri"""
    VISUAL = "visual"           # Görsel öğrenen
    AUDITORY = "auditory"       # İşitsel öğrenen
    KINESTHETIC = "kinesthetic" # Yaparak öğrenen
    READING = "reading"         # Okuyarak öğrenen
    MIXED = "mixed"             # Karışık


class ChunkingStrategy(str, Enum):
    """Parçalama stratejileri"""
    HIERARCHICAL = "hierarchical"   # Hiyerarşik
    ASSOCIATIVE = "associative"     # İlişkisel
    SEQUENTIAL = "sequential"       # Sıralı
    CONCEPTUAL = "conceptual"       # Kavramsal


# ============ DATA CLASSES ============

@dataclass
class ThetaSession:
    """Theta Wave öğrenme oturumu"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=datetime.now)
    current_state: BrainWaveState = BrainWaveState.THETA
    cycle_count: int = 0
    total_theta_minutes: int = 0
    total_alpha_minutes: int = 0
    focus_score: float = 0.0  # 0-100
    retention_boost: float = 1.0  # Multiplier
    
    # Cycle: 25min Theta (deep learning) + 5min Alpha (rest)
    THETA_DURATION: int = 25
    ALPHA_DURATION: int = 5
    
    def get_current_phase(self) -> Dict[str, Any]:
        """Mevcut fazı hesapla"""
        elapsed = (datetime.now() - self.started_at).seconds // 60
        cycle_duration = self.THETA_DURATION + self.ALPHA_DURATION
        current_cycle = elapsed // cycle_duration
        phase_elapsed = elapsed % cycle_duration
        
        if phase_elapsed < self.THETA_DURATION:
            return {
                "state": BrainWaveState.THETA,
                "remaining_minutes": self.THETA_DURATION - phase_elapsed,
                "message": "🧠 Derin öğrenme modunda - Tam konsantrasyon",
                "tips": [
                    "Dikkat dağıtıcıları kapat",
                    "Yeni kavramları öğren",
                    "Aktif not al",
                    "Sorular sor"
                ]
            }
        else:
            return {
                "state": BrainWaveState.ALPHA,
                "remaining_minutes": cycle_duration - phase_elapsed,
                "message": "😌 Dinlenme modu - Beyin konsolidasyonu",
                "tips": [
                    "Gözlerini kapat",
                    "Derin nefes al",
                    "Öğrendiklerini düşün",
                    "Hareket et"
                ]
            }


@dataclass 
class MemoryPalace:
    """Bellek Sarayı - Spatial memory technique"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    workspace_id: str = ""
    
    # Saray yapısı
    rooms: List[Dict[str, Any]] = field(default_factory=list)
    # Her oda içindeki objeler (kavramlar)
    objects: List[Dict[str, Any]] = field(default_factory=list)
    
    # Görsel bağlantılar
    visual_associations: List[Dict[str, Any]] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    last_visited: Optional[datetime] = None
    visit_count: int = 0
    
    def add_room(self, name: str, description: str, position: int) -> Dict:
        """Saraya yeni oda ekle"""
        room = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "position": position,
            "objects": [],
            "image_prompt": f"A {name} in a grand memory palace, detailed interior, warm lighting"
        }
        self.rooms.append(room)
        return room
    
    def place_concept(self, room_id: str, concept: str, visual_hook: str, 
                      emotional_tag: str = None) -> Dict:
        """Bir kavramı odaya yerleştir"""
        obj = {
            "id": str(uuid.uuid4()),
            "room_id": room_id,
            "concept": concept,
            "visual_hook": visual_hook,  # "Dev bir elma ağacı üzerinde formül yazılı"
            "emotional_tag": emotional_tag,
            "strength": 1.0,
            "placed_at": datetime.now().isoformat(),
            "recall_count": 0
        }
        self.objects.append(obj)
        return obj
    
    def create_association(self, object1_id: str, object2_id: str, 
                          association_type: str, description: str) -> Dict:
        """İki obje arasında bağlantı kur"""
        assoc = {
            "id": str(uuid.uuid4()),
            "object1_id": object1_id,
            "object2_id": object2_id,
            "type": association_type,
            "description": description,
            "strength": 1.0
        }
        self.visual_associations.append(assoc)
        return assoc
    
    def take_tour(self) -> List[Dict]:
        """Sarayda tur at - sıralı geri çağırma"""
        self.visit_count += 1
        self.last_visited = datetime.now()
        
        tour = []
        for room in sorted(self.rooms, key=lambda x: x.get("position", 0)):
            room_objects = [o for o in self.objects if o["room_id"] == room["id"]]
            tour.append({
                "room": room,
                "objects": room_objects,
                "narrative": self._generate_narrative(room, room_objects)
            })
        return tour
    
    def _generate_narrative(self, room: Dict, objects: List[Dict]) -> str:
        """Oda için anlatı oluştur"""
        if not objects:
            return f"{room['name']} odasına giriyorsun. Henüz boş."
        
        narratives = [f"{room['name']} odasına giriyorsun."]
        for obj in objects:
            narratives.append(f"Görüyorsun: {obj['visual_hook']} - Bu sana {obj['concept']} kavramını hatırlatıyor.")
        return " ".join(narratives)


@dataclass
class ChunkingResult:
    """Chunking sonucu"""
    original_concepts: List[str]
    chunks: List[Dict[str, Any]]
    strategy: ChunkingStrategy
    optimal_chunk_size: int
    cognitive_load_score: float  # 0-100, düşük = iyi


@dataclass
class DualCodedContent:
    """Çift kodlanmış içerik"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    concept: str = ""
    
    # Verbal/Text encoding
    text_explanation: str = ""
    keywords: List[str] = field(default_factory=list)
    
    # Visual encoding
    diagram_description: str = ""
    visual_elements: List[Dict[str, Any]] = field(default_factory=list)
    color_coding: Dict[str, str] = field(default_factory=dict)
    
    # Mnemonic
    mnemonic_hook: str = ""
    
    # Effectiveness
    encoding_strength: float = 1.0


@dataclass
class InterleavingSchedule:
    """Interleaving (karışık öğrenme) planı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topics: List[str] = field(default_factory=list)
    schedule: List[Dict[str, Any]] = field(default_factory=list)  # Karışık sıralama
    
    # Blocked vs Interleaved comparison
    blocked_order: List[str] = field(default_factory=list)  # AAABBBCCC
    interleaved_order: List[str] = field(default_factory=list)  # ABCABCABC
    
    current_position: int = 0
    retention_boost: float = 1.4  # Interleaving typically 40% better


# ============ ENGINES ============

class ThetaWaveEngine:
    """Theta Wave Sync Engine - Beyin dalgası tabanlı öğrenme döngüleri"""
    
    def __init__(self):
        self.active_sessions: Dict[str, ThetaSession] = {}
        
    def start_session(self, user_id: str) -> ThetaSession:
        """Yeni theta oturumu başlat"""
        session = ThetaSession()
        self.active_sessions[user_id] = session
        return session
    
    def get_session_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Oturum durumunu al"""
        session = self.active_sessions.get(user_id)
        if not session:
            return None
        
        phase = session.get_current_phase()
        elapsed = (datetime.now() - session.started_at).seconds // 60
        
        return {
            "session_id": session.id,
            "elapsed_minutes": elapsed,
            "current_state": phase["state"].value,
            "remaining_minutes": phase["remaining_minutes"],
            "message": phase["message"],
            "tips": phase["tips"],
            "cycle_count": elapsed // 30,
            "focus_score": self._calculate_focus_score(session),
            "retention_boost": self._calculate_retention_boost(session)
        }
    
    def _calculate_focus_score(self, session: ThetaSession) -> float:
        """Focus skorunu hesapla"""
        # Daha uzun süre = daha yüksek focus (diminishing returns)
        elapsed = (datetime.now() - session.started_at).seconds // 60
        base_score = min(100, 50 + (elapsed * 2))
        
        # Cycle bonusu
        cycles = elapsed // 30
        cycle_bonus = min(20, cycles * 5)
        
        return min(100, base_score + cycle_bonus)
    
    def _calculate_retention_boost(self, session: ThetaSession) -> float:
        """Retention boost çarpanını hesapla"""
        elapsed = (datetime.now() - session.started_at).seconds // 60
        cycles = elapsed // 30
        
        # Her döngü %5 bonus
        return 1.0 + (cycles * 0.05)
    
    def end_session(self, user_id: str) -> Dict[str, Any]:
        """Oturumu sonlandır"""
        session = self.active_sessions.pop(user_id, None)
        if not session:
            return {"error": "No active session"}
        
        elapsed = (datetime.now() - session.started_at).seconds // 60
        
        return {
            "total_minutes": elapsed,
            "cycles_completed": elapsed // 30,
            "theta_minutes": (elapsed // 30) * 25 + min(25, elapsed % 30),
            "final_focus_score": self._calculate_focus_score(session),
            "retention_boost": self._calculate_retention_boost(session),
            "recommendation": self._get_recommendation(elapsed)
        }
    
    def _get_recommendation(self, elapsed: int) -> str:
        """Süreye göre öneri"""
        if elapsed < 25:
            return "Kısa oturum. En az 1 tam döngü (30 dk) önerilir."
        elif elapsed < 60:
            return "İyi oturum! 2-3 döngü optimal öğrenme için ideal."
        elif elapsed < 120:
            return "Harika oturum! Mükemmel konsantrasyon."
        else:
            return "Uzun oturum. Daha uzun mola önerilir."


class MemoryPalaceEngine:
    """Memory Palace Engine - Bellek sarayı yönetimi"""
    
    def __init__(self):
        self.palaces: Dict[str, MemoryPalace] = {}
    
    def create_palace(self, workspace_id: str, name: str, 
                     description: str, template: str = "mansion") -> MemoryPalace:
        """Yeni bellek sarayı oluştur"""
        palace = MemoryPalace(
            name=name,
            description=description,
            workspace_id=workspace_id
        )
        
        # Template'e göre varsayılan odalar
        templates = {
            "mansion": [
                ("Giriş Holü", "Büyük kapıdan girilen görkemli giriş", 0),
                ("Kütüphane", "Duvarları kitaplarla kaplı sessiz oda", 1),
                ("Salon", "Şömineli rahat oturma odası", 2),
                ("Mutfak", "Lezzetli kokularla dolu mutfak", 3),
                ("Bahçe", "Çiçeklerle dolu huzurlu bahçe", 4),
                ("Çatı Katı", "Yıldızların görüldüğü çatı terası", 5),
            ],
            "school": [
                ("Ana Koridor", "Lokerlarla dolu ana koridor", 0),
                ("Sınıf 1", "Tahtalı klasik sınıf", 1),
                ("Laboratuvar", "Deney malzemeleriyle dolu lab", 2),
                ("Kütüphane", "Sessiz çalışma alanı", 3),
                ("Spor Salonu", "Geniş spor alanı", 4),
                ("Kafeterya", "Yemek kokuları", 5),
            ],
            "castle": [
                ("Kale Kapısı", "Zincirli köprülü giriş", 0),
                ("Şövalye Salonu", "Zırhlı şövalyeler", 1),
                ("Taht Odası", "Altın tahtın olduğu salon", 2),
                ("Kule", "Spiral merdivenli kule", 3),
                ("Zindan", "Karanlık yeraltı", 4),
                ("Hazine Odası", "Altın ve mücevherler", 5),
            ]
        }
        
        rooms = templates.get(template, templates["mansion"])
        for name, desc, pos in rooms:
            palace.add_room(name, desc, pos)
        
        self.palaces[palace.id] = palace
        return palace
    
    def get_palace(self, palace_id: str) -> Optional[MemoryPalace]:
        """Sarayı getir"""
        return self.palaces.get(palace_id)
    
    def generate_visual_hook(self, concept: str) -> str:
        """Kavram için görsel kanca üret (LLM ile)"""
        # TODO: LLM integration
        hooks = [
            f"Dev boyutlu parlayan {concept} heykeli",
            f"Duvara {concept} yazan ateşten harfler",
            f"{concept} şeklinde kristal bir küre",
            f"Dans eden {concept} sembolleri",
            f"Gökkuşağı renklerinde {concept} pankartı"
        ]
        return random.choice(hooks)


class ChunkingEngine:
    """Chunking Intelligence Engine - Miller's Law optimizasyonu"""
    
    # Miller's Law: 7 ± 2 items
    OPTIMAL_MIN = 5
    OPTIMAL_MAX = 9
    OPTIMAL_TARGET = 7
    
    def chunk_concepts(self, concepts: List[str], 
                       strategy: ChunkingStrategy = ChunkingStrategy.CONCEPTUAL) -> ChunkingResult:
        """Kavramları optimal parçalara böl"""
        
        if len(concepts) <= self.OPTIMAL_MAX:
            # Zaten optimal boyutta
            return ChunkingResult(
                original_concepts=concepts,
                chunks=[{
                    "id": str(uuid.uuid4()),
                    "concepts": concepts,
                    "size": len(concepts),
                    "label": "Ana Grup"
                }],
                strategy=strategy,
                optimal_chunk_size=len(concepts),
                cognitive_load_score=len(concepts) / self.OPTIMAL_MAX * 50
            )
        
        # Parçalama
        chunks = []
        chunk_size = self.OPTIMAL_TARGET
        
        for i in range(0, len(concepts), chunk_size):
            chunk_concepts = concepts[i:i + chunk_size]
            chunks.append({
                "id": str(uuid.uuid4()),
                "concepts": chunk_concepts,
                "size": len(chunk_concepts),
                "label": f"Grup {len(chunks) + 1}",
                "super_concept": self._create_super_concept(chunk_concepts)
            })
        
        # Cognitive load hesapla
        total_chunks = len(chunks)
        avg_size = len(concepts) / total_chunks
        cognitive_load = (total_chunks / 5) * 30 + (avg_size / self.OPTIMAL_MAX) * 20
        
        return ChunkingResult(
            original_concepts=concepts,
            chunks=chunks,
            strategy=strategy,
            optimal_chunk_size=chunk_size,
            cognitive_load_score=min(100, cognitive_load)
        )
    
    def _create_super_concept(self, concepts: List[str]) -> str:
        """Chunk için üst kavram oluştur"""
        # TODO: LLM ile daha akıllı üst kavram
        if len(concepts) <= 3:
            return " & ".join(concepts)
        return f"{concepts[0]} ve {len(concepts)-1} ilişkili kavram"
    
    def suggest_grouping(self, concepts: List[str]) -> List[Dict[str, Any]]:
        """Kavramlar için gruplandırma öner"""
        # Basit benzerlik bazlı gruplandırma
        # TODO: LLM/embedding bazlı semantic grouping
        suggestions = []
        
        # Ortak prefix/suffix ara
        prefixes = {}
        for concept in concepts:
            words = concept.split()
            if words:
                prefix = words[0].lower()
                prefixes.setdefault(prefix, []).append(concept)
        
        for prefix, group in prefixes.items():
            if len(group) >= 2:
                suggestions.append({
                    "type": "prefix_group",
                    "key": prefix,
                    "concepts": group,
                    "reason": f"'{prefix}' ile başlayan kavramlar"
                })
        
        return suggestions


class DualCodingEngine:
    """Dual Coding Engine - Çift kodlama sistemi"""
    
    def create_dual_coded(self, concept: str, explanation: str) -> DualCodedContent:
        """Kavram için çift kodlama oluştur"""
        content = DualCodedContent(
            concept=concept,
            text_explanation=explanation,
            keywords=self._extract_keywords(explanation)
        )
        
        # Görsel kodlama
        content.diagram_description = self._generate_diagram_description(concept, explanation)
        content.visual_elements = self._generate_visual_elements(concept)
        content.color_coding = self._generate_color_coding(concept)
        content.mnemonic_hook = self._generate_mnemonic(concept)
        
        return content
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Anahtar kelimeleri çıkar"""
        # Basit implementasyon
        words = text.split()
        # Uzun kelimeleri al (genellikle önemli kavramlar)
        keywords = [w for w in words if len(w) > 6][:10]
        return keywords
    
    def _generate_diagram_description(self, concept: str, explanation: str) -> str:
        """Diyagram açıklaması üret"""
        # TODO: LLM ile zenginleştir
        return f"Merkez: {concept}. Dallar: Ana kavramların ilişkilerini gösteren zihin haritası."
    
    def _generate_visual_elements(self, concept: str) -> List[Dict[str, Any]]:
        """Görsel elementler üret"""
        return [
            {"type": "icon", "name": "lightbulb", "meaning": "Ana fikir"},
            {"type": "shape", "name": "circle", "meaning": concept},
            {"type": "arrow", "direction": "outward", "meaning": "İlişkiler"},
            {"type": "color_block", "color": "#4CAF50", "meaning": "Önemli nokta"}
        ]
    
    def _generate_color_coding(self, concept: str) -> Dict[str, str]:
        """Renk kodlaması üret"""
        return {
            "primary_concept": "#2196F3",
            "related_concepts": "#4CAF50", 
            "examples": "#FF9800",
            "warnings": "#F44336",
            "tips": "#9C27B0"
        }
    
    def _generate_mnemonic(self, concept: str) -> str:
        """Mnemonik (hafıza kancası) üret"""
        # Akronim veya hikaye
        words = concept.split()
        if len(words) >= 2:
            acronym = "".join(w[0].upper() for w in words[:5])
            return f"Akronim: {acronym}"
        return f"Görsel: {concept}'i bir resim olarak hayal et"


class InterleavingEngine:
    """Interleaving Engine - Karışık öğrenme modu"""
    
    def create_schedule(self, topics: List[str], items_per_topic: int = 3) -> InterleavingSchedule:
        """Interleaved öğrenme planı oluştur"""
        schedule = InterleavingSchedule(topics=topics)
        
        # Blocked order: AAABBBCCC
        for topic in topics:
            schedule.blocked_order.extend([topic] * items_per_topic)
        
        # Interleaved order: ABCABCABC
        for i in range(items_per_topic):
            for topic in topics:
                schedule.interleaved_order.append(topic)
        
        # Ana schedule (interleaved)
        for i, topic in enumerate(schedule.interleaved_order):
            schedule.schedule.append({
                "position": i,
                "topic": topic,
                "item_number": i // len(topics) + 1,
                "context_switch": i > 0 and schedule.interleaved_order[i-1] != topic
            })
        
        return schedule
    
    def get_next_item(self, schedule: InterleavingSchedule) -> Optional[Dict[str, Any]]:
        """Sıradaki öğeyi al"""
        if schedule.current_position >= len(schedule.schedule):
            return None
        
        item = schedule.schedule[schedule.current_position]
        schedule.current_position += 1
        
        return {
            **item,
            "progress": schedule.current_position / len(schedule.schedule) * 100,
            "tip": "Konu değişimi beyninin bağlantı kurmasını sağlar!" if item.get("context_switch") else None
        }
    
    def compare_effectiveness(self) -> Dict[str, Any]:
        """Blocked vs Interleaved karşılaştırması"""
        return {
            "blocked": {
                "description": "AAABBBCCC - Tek konuya odaklanma",
                "short_term_performance": "Daha yüksek (%85)",
                "long_term_retention": "Düşük (%50)",
                "transfer_ability": "Düşük"
            },
            "interleaved": {
                "description": "ABCABCABC - Konular arası geçiş",
                "short_term_performance": "Orta (%70)",
                "long_term_retention": "Yüksek (%75)",
                "transfer_ability": "Yüksek",
                "retention_boost": "+40%"
            },
            "recommendation": "Uzun vadeli öğrenme için INTERLEAVED tercih edilmeli"
        }


# ============ SINGLETON INSTANCES ============

theta_engine = ThetaWaveEngine()
memory_palace_engine = MemoryPalaceEngine()
chunking_engine = ChunkingEngine()
dual_coding_engine = DualCodingEngine()
interleaving_engine = InterleavingEngine()
