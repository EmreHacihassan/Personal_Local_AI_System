"""
Full Meta Learning - Gamification Module
Oyunlaştırma ve motivasyon sistemi

Features:
- Skill Tree Visualization: RPG tarzı yetenek ağacı
- Boss Battles: Stage/Paket sonu testleri (geçiş için yeterli puan gerekli)
- Daily Quests: Günlük mikro-görevler ve streak sistemi
- Random Events: Sürpriz bonus eventler
"""

import uuid
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field


# ============ ENUMS ============

class NodeType(str, Enum):
    """Skill tree node tipleri"""
    CONCEPT = "concept"          # Temel kavram
    SKILL = "skill"              # Beceri
    MASTERY = "mastery"          # Ustalık
    BOSS = "boss"                # Boss savaşı
    MILESTONE = "milestone"      # Kilometre taşı
    SECRET = "secret"            # Gizli yetenek


class NodeStatus(str, Enum):
    """Node durumları"""
    LOCKED = "locked"            # Kilitli
    AVAILABLE = "available"      # Açılabilir
    IN_PROGRESS = "in_progress"  # Devam ediyor
    COMPLETED = "completed"      # Tamamlandı
    MASTERED = "mastered"        # Ustalaşıldı


class BattleDifficulty(str, Enum):
    """Savaş zorluk seviyeleri"""
    MINI = "mini"                # Mini boss (paket sonu)
    STANDARD = "standard"        # Standart (stage sonu)
    ELITE = "elite"              # Elite (workspace yarısı)
    FINAL = "final"              # Final boss (workspace sonu)


class QuestType(str, Enum):
    """Görev tipleri"""
    LEARN = "learn"              # Yeni öğren
    REVIEW = "review"            # Tekrar et
    PRACTICE = "practice"        # Uygula
    CHALLENGE = "challenge"      # Meydan oku
    SOCIAL = "social"            # Sosyal


class EventType(str, Enum):
    """Random event tipleri"""
    BONUS_XP = "bonus_xp"                # 2x XP
    DOUBLE_RETENTION = "double_retention" # 2x retention
    LUCKY_STREAK = "lucky_streak"        # Streak koruması
    WISDOM_BOOST = "wisdom_boost"        # Ekstra ipucu
    TIME_WARP = "time_warp"              # Hızlandırılmış review
    TREASURE = "treasure"                # Gizli içerik


# ============ DATA CLASSES ============

@dataclass
class SkillTreeNode:
    """Skill tree node"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    node_type: NodeType = NodeType.CONCEPT
    status: NodeStatus = NodeStatus.LOCKED
    
    # Pozisyon (görselleştirme için)
    x: float = 0.0
    y: float = 0.0
    tier: int = 1  # 1-5 tier system
    
    # Bağlantılar
    prerequisites: List[str] = field(default_factory=list)  # Node ID'leri
    unlocks: List[str] = field(default_factory=list)
    
    # İlerleme
    progress: float = 0.0  # 0-100
    xp_reward: int = 100
    xp_required: int = 0
    
    # İçerik
    package_id: Optional[str] = None
    content_ids: List[str] = field(default_factory=list)
    
    # Meta
    icon: str = "⭐"
    color: str = "#4CAF50"
    completed_at: Optional[datetime] = None


@dataclass
class SkillTree:
    """Tam skill tree"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = ""
    name: str = ""
    
    nodes: Dict[str, SkillTreeNode] = field(default_factory=dict)
    connections: List[Tuple[str, str]] = field(default_factory=list)  # (from_id, to_id)
    
    # Stats
    total_nodes: int = 0
    completed_nodes: int = 0
    current_tier: int = 1
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_node(self, node: SkillTreeNode) -> None:
        """Node ekle"""
        self.nodes[node.id] = node
        self.total_nodes = len(self.nodes)
    
    def connect(self, from_id: str, to_id: str) -> None:
        """İki node'u bağla"""
        self.connections.append((from_id, to_id))
        if from_id in self.nodes:
            self.nodes[from_id].unlocks.append(to_id)
        if to_id in self.nodes:
            self.nodes[to_id].prerequisites.append(from_id)
    
    def update_availability(self) -> List[str]:
        """Kullanılabilir node'ları güncelle"""
        newly_available = []
        
        for node_id, node in self.nodes.items():
            if node.status == NodeStatus.LOCKED:
                # Tüm prerequisites tamamlandı mı?
                prereqs_done = all(
                    self.nodes.get(p, SkillTreeNode()).status in 
                    [NodeStatus.COMPLETED, NodeStatus.MASTERED]
                    for p in node.prerequisites
                )
                if prereqs_done or not node.prerequisites:
                    node.status = NodeStatus.AVAILABLE
                    newly_available.append(node_id)
        
        return newly_available
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Görselleştirme verisi"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "status": n.status.value,
                    "x": n.x,
                    "y": n.y,
                    "tier": n.tier,
                    "icon": n.icon,
                    "color": n.color,
                    "progress": n.progress
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {"from": f, "to": t}
                for f, t in self.connections
            ],
            "stats": {
                "total": self.total_nodes,
                "completed": self.completed_nodes,
                "progress": self.completed_nodes / max(1, self.total_nodes) * 100
            }
        }


@dataclass
class BossBattle:
    """Boss Battle - Test sınavı"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    difficulty: BattleDifficulty = BattleDifficulty.MINI
    
    # İlişkili içerik
    package_id: Optional[str] = None
    stage_id: Optional[str] = None
    workspace_id: str = ""
    
    # Sorular
    questions: List[Dict[str, Any]] = field(default_factory=list)
    total_questions: int = 0
    
    # Geçiş kriterleri
    passing_score: float = 70.0  # Minimum %70
    time_limit_minutes: int = 30
    max_attempts: int = 3
    
    # Durum
    attempts: int = 0
    best_score: float = 0.0
    passed: bool = False
    
    # Ödüller
    xp_reward: int = 500
    bonus_xp_perfect: int = 200  # %100 için bonus
    unlock_content: List[str] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class BattleAttempt:
    """Bir savaş denemesi"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    battle_id: str = ""
    
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    
    answers: List[Dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    passed: bool = False
    
    # Analiz
    correct_count: int = 0
    wrong_count: int = 0
    weak_topics: List[str] = field(default_factory=list)  # Zayıf konular
    
    time_spent_seconds: int = 0


@dataclass
class DailyQuest:
    """Günlük görev"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    quest_type: QuestType = QuestType.LEARN
    
    title: str = ""
    description: str = ""
    
    # Hedef
    target_count: int = 1
    current_count: int = 0
    
    # Ödüller
    xp_reward: int = 50
    streak_bonus: int = 10  # Her streak günü için bonus
    
    # Durum
    completed: bool = False
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=1))
    
    # İlişkili içerik
    related_packages: List[str] = field(default_factory=list)


@dataclass
class DailyQuestSet:
    """Günlük görev seti (3 görev)"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    date: datetime = field(default_factory=datetime.now)
    
    quests: List[DailyQuest] = field(default_factory=list)
    
    all_completed: bool = False
    completion_bonus: int = 100  # Hepsini tamamlama bonusu
    
    # Streak
    streak_day: int = 0
    streak_protected: bool = False  # Random event koruması


@dataclass
class RandomEvent:
    """Random event"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.BONUS_XP
    
    title: str = ""
    description: str = ""
    icon: str = "🎁"
    
    # Etki
    multiplier: float = 2.0
    duration_minutes: int = 30
    
    # Durum
    active: bool = True
    activated_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=30))
    
    # Nadir mi?
    rarity: str = "common"  # common, rare, epic, legendary


# ============ ENGINES ============

class SkillTreeEngine:
    """Skill Tree yönetim engine'i"""
    
    def __init__(self):
        self.trees: Dict[str, SkillTree] = {}
    
    def create_tree_from_workspace(self, workspace_id: str, stages: List[Dict], 
                                   packages: List[Dict]) -> SkillTree:
        """Workspace'den skill tree oluştur"""
        tree = SkillTree(
            workspace_id=workspace_id,
            name=f"Skill Tree - {workspace_id[:8]}"
        )
        
        tier = 1
        prev_boss_id = None
        y_offset = 0
        
        for stage_idx, stage in enumerate(stages):
            stage_packages = [p for p in packages if p.get("stage_id") == stage.get("id")]
            
            for pkg_idx, pkg in enumerate(stage_packages):
                # Paket node'u
                node = SkillTreeNode(
                    name=pkg.get("title", f"Paket {pkg_idx + 1}"),
                    description=pkg.get("description", ""),
                    node_type=NodeType.CONCEPT,
                    tier=tier,
                    x=pkg_idx * 150,
                    y=y_offset,
                    package_id=pkg.get("id"),
                    xp_reward=100 * tier,
                    icon=self._get_icon_for_tier(tier),
                    color=self._get_color_for_tier(tier)
                )
                
                if prev_boss_id:
                    node.prerequisites.append(prev_boss_id)
                
                tree.add_node(node)
                
                if prev_boss_id:
                    tree.connect(prev_boss_id, node.id)
            
            # Stage sonu boss
            boss_node = SkillTreeNode(
                name=f"🏆 {stage.get('title', 'Stage')} Boss",
                description="Stage sonu değerlendirme",
                node_type=NodeType.BOSS,
                tier=tier,
                x=len(stage_packages) * 150 + 100,
                y=y_offset,
                xp_reward=500 * tier,
                icon="⚔️",
                color="#FF5722"
            )
            
            # Tüm stage paketlerini prerequisite yap
            for pkg in stage_packages:
                pkg_node = next((n for n in tree.nodes.values() 
                               if n.package_id == pkg.get("id")), None)
                if pkg_node:
                    boss_node.prerequisites.append(pkg_node.id)
                    tree.connect(pkg_node.id, boss_node.id)
            
            tree.add_node(boss_node)
            prev_boss_id = boss_node.id
            
            tier = min(5, tier + 1)
            y_offset += 200
        
        tree.update_availability()
        self.trees[tree.id] = tree
        return tree
    
    def _get_icon_for_tier(self, tier: int) -> str:
        """Tier'a göre ikon"""
        icons = {1: "📚", 2: "🎯", 3: "⚡", 4: "🔮", 5: "👑"}
        return icons.get(tier, "⭐")
    
    def _get_color_for_tier(self, tier: int) -> str:
        """Tier'a göre renk"""
        colors = {
            1: "#4CAF50",  # Green
            2: "#2196F3",  # Blue
            3: "#9C27B0",  # Purple
            4: "#FF9800",  # Orange
            5: "#F44336"   # Red
        }
        return colors.get(tier, "#4CAF50")
    
    def complete_node(self, tree_id: str, node_id: str) -> Dict[str, Any]:
        """Node'u tamamla"""
        tree = self.trees.get(tree_id)
        if not tree or node_id not in tree.nodes:
            return {"error": "Node not found"}
        
        node = tree.nodes[node_id]
        node.status = NodeStatus.COMPLETED
        node.progress = 100.0
        node.completed_at = datetime.now()
        tree.completed_nodes += 1
        
        # Yeni açılan node'ları bul
        newly_available = tree.update_availability()
        
        return {
            "node_id": node_id,
            "xp_earned": node.xp_reward,
            "newly_available": newly_available,
            "tree_progress": tree.completed_nodes / tree.total_nodes * 100
        }


class BossBattleEngine:
    """Boss Battle yönetim engine'i"""
    
    def __init__(self):
        self.battles: Dict[str, BossBattle] = {}
        self.attempts: Dict[str, List[BattleAttempt]] = {}
    
    def create_battle(self, difficulty: BattleDifficulty, 
                      content_items: List[Dict],
                      package_id: str = None,
                      stage_id: str = None) -> BossBattle:
        """Boss battle oluştur"""
        
        # Zorluk ayarları
        settings = {
            BattleDifficulty.MINI: {
                "questions": 5,
                "passing": 60.0,
                "time": 10,
                "xp": 200
            },
            BattleDifficulty.STANDARD: {
                "questions": 10,
                "passing": 70.0,
                "time": 20,
                "xp": 500
            },
            BattleDifficulty.ELITE: {
                "questions": 15,
                "passing": 75.0,
                "time": 30,
                "xp": 1000
            },
            BattleDifficulty.FINAL: {
                "questions": 20,
                "passing": 80.0,
                "time": 45,
                "xp": 2000
            }
        }
        
        config = settings.get(difficulty, settings[BattleDifficulty.MINI])
        
        battle = BossBattle(
            name=f"{difficulty.value.title()} Boss Battle",
            difficulty=difficulty,
            package_id=package_id,
            stage_id=stage_id,
            total_questions=config["questions"],
            passing_score=config["passing"],
            time_limit_minutes=config["time"],
            xp_reward=config["xp"]
        )
        
        # Soruları oluştur
        battle.questions = self._generate_questions(content_items, config["questions"])
        
        self.battles[battle.id] = battle
        return battle
    
    def _generate_questions(self, content_items: List[Dict], count: int) -> List[Dict]:
        """Sorular oluştur"""
        questions = []
        
        # Her content item'dan soru türet
        for i, item in enumerate(content_items[:count]):
            q_type = random.choice(["multiple_choice", "true_false", "fill_blank"])
            
            if q_type == "multiple_choice":
                questions.append({
                    "id": str(uuid.uuid4()),
                    "type": "multiple_choice",
                    "question": f"{item.get('title', 'Kavram')} hakkında hangisi doğrudur?",
                    "options": [
                        {"id": "a", "text": "Doğru cevap (placeholder)", "correct": True},
                        {"id": "b", "text": "Yanlış seçenek 1", "correct": False},
                        {"id": "c", "text": "Yanlış seçenek 2", "correct": False},
                        {"id": "d", "text": "Yanlış seçenek 3", "correct": False}
                    ],
                    "points": 10,
                    "topic": item.get('title', 'Genel')
                })
            elif q_type == "true_false":
                questions.append({
                    "id": str(uuid.uuid4()),
                    "type": "true_false",
                    "question": f"{item.get('title', 'Bu kavram')} ile ilgili ifade doğru mudur?",
                    "correct_answer": True,
                    "points": 5,
                    "topic": item.get('title', 'Genel')
                })
            else:
                questions.append({
                    "id": str(uuid.uuid4()),
                    "type": "fill_blank",
                    "question": f"_____ kavramı {item.get('title', 'bu konuyla')} ilişkilidir.",
                    "correct_answer": item.get('title', 'cevap'),
                    "points": 15,
                    "topic": item.get('title', 'Genel')
                })
        
        random.shuffle(questions)
        return questions
    
    def start_attempt(self, battle_id: str) -> Optional[BattleAttempt]:
        """Savaş denemesi başlat"""
        battle = self.battles.get(battle_id)
        if not battle:
            return None
        
        if battle.attempts >= battle.max_attempts:
            return None  # Max deneme aşıldı
        
        attempt = BattleAttempt(battle_id=battle_id)
        
        if battle_id not in self.attempts:
            self.attempts[battle_id] = []
        self.attempts[battle_id].append(attempt)
        
        battle.attempts += 1
        
        return attempt
    
    def submit_answer(self, attempt_id: str, question_id: str, 
                      answer: Any) -> Dict[str, Any]:
        """Cevap gönder"""
        # Attempt'i bul
        for battle_attempts in self.attempts.values():
            for attempt in battle_attempts:
                if attempt.id == attempt_id:
                    # Soruyu bul
                    battle = self.battles.get(attempt.battle_id)
                    if not battle:
                        return {"error": "Battle not found"}
                    
                    question = next((q for q in battle.questions 
                                   if q["id"] == question_id), None)
                    if not question:
                        return {"error": "Question not found"}
                    
                    # Cevabı değerlendir
                    is_correct = self._check_answer(question, answer)
                    
                    attempt.answers.append({
                        "question_id": question_id,
                        "answer": answer,
                        "correct": is_correct,
                        "topic": question.get("topic", "Genel")
                    })
                    
                    if is_correct:
                        attempt.correct_count += 1
                    else:
                        attempt.wrong_count += 1
                        attempt.weak_topics.append(question.get("topic", "Genel"))
                    
                    return {
                        "correct": is_correct,
                        "progress": len(attempt.answers) / len(battle.questions) * 100
                    }
        
        return {"error": "Attempt not found"}
    
    def _check_answer(self, question: Dict, answer: Any) -> bool:
        """Cevabı kontrol et"""
        q_type = question.get("type")
        
        if q_type == "multiple_choice":
            correct_option = next((o for o in question.get("options", []) 
                                  if o.get("correct")), None)
            return correct_option and correct_option.get("id") == answer
        elif q_type == "true_false":
            return question.get("correct_answer") == answer
        elif q_type == "fill_blank":
            return str(answer).lower().strip() == str(question.get("correct_answer", "")).lower().strip()
        
        return False
    
    def finish_attempt(self, attempt_id: str) -> Dict[str, Any]:
        """Denemeyi bitir"""
        for battle_id, battle_attempts in self.attempts.items():
            for attempt in battle_attempts:
                if attempt.id == attempt_id:
                    battle = self.battles.get(battle_id)
                    if not battle:
                        return {"error": "Battle not found"}
                    
                    attempt.finished_at = datetime.now()
                    attempt.time_spent_seconds = int(
                        (attempt.finished_at - attempt.started_at).total_seconds()
                    )
                    
                    # Skor hesapla
                    total_questions = len(battle.questions)
                    attempt.score = (attempt.correct_count / total_questions) * 100
                    attempt.passed = attempt.score >= battle.passing_score
                    
                    # Battle'ı güncelle
                    if attempt.score > battle.best_score:
                        battle.best_score = attempt.score
                    
                    if attempt.passed and not battle.passed:
                        battle.passed = True
                        battle.completed_at = datetime.now()
                    
                    # XP hesapla
                    xp = 0
                    if attempt.passed:
                        xp = battle.xp_reward
                        if attempt.score == 100:
                            xp += battle.bonus_xp_perfect
                    
                    # Unique weak topics
                    unique_weak = list(set(attempt.weak_topics))
                    
                    return {
                        "score": attempt.score,
                        "passed": attempt.passed,
                        "passing_score": battle.passing_score,
                        "correct": attempt.correct_count,
                        "wrong": attempt.wrong_count,
                        "time_spent": attempt.time_spent_seconds,
                        "xp_earned": xp,
                        "weak_topics": unique_weak,
                        "can_retry": battle.attempts < battle.max_attempts,
                        "attempts_remaining": battle.max_attempts - battle.attempts,
                        "message": "🎉 Tebrikler! Geçtiniz!" if attempt.passed else 
                                   f"❌ Geçemediniz. Minimum %{battle.passing_score} gerekli."
                    }
        
        return {"error": "Attempt not found"}


class DailyQuestEngine:
    """Daily Quest yönetim engine'i"""
    
    def __init__(self):
        self.quest_sets: Dict[str, DailyQuestSet] = {}  # user_id -> quest set
        self.streaks: Dict[str, int] = {}  # user_id -> streak count
    
    def generate_daily_quests(self, user_id: str, 
                              available_packages: List[str]) -> DailyQuestSet:
        """Günlük görev seti oluştur"""
        
        # Bugün için zaten var mı?
        today = datetime.now().date()
        existing = self.quest_sets.get(user_id)
        if existing and existing.date.date() == today:
            return existing
        
        # Streak hesapla
        streak = self.streaks.get(user_id, 0)
        if existing and existing.all_completed:
            streak += 1
        elif existing and not existing.all_completed:
            streak = 0  # Streak kırıldı
        self.streaks[user_id] = streak
        
        # 3 görev oluştur
        quests = [
            DailyQuest(
                quest_type=QuestType.LEARN,
                title="📚 Yeni Öğren",
                description="Bugün 1 yeni paket tamamla",
                target_count=1,
                xp_reward=50 + (streak * 5),
                related_packages=available_packages[:3]
            ),
            DailyQuest(
                quest_type=QuestType.REVIEW,
                title="🔄 Tekrar Et",
                description="3 flashcard'ı tekrar et",
                target_count=3,
                xp_reward=30 + (streak * 3)
            ),
            DailyQuest(
                quest_type=QuestType.PRACTICE,
                title="✍️ Uygula",
                description="1 Feynman açıklaması yap",
                target_count=1,
                xp_reward=40 + (streak * 4)
            )
        ]
        
        quest_set = DailyQuestSet(
            quests=quests,
            streak_day=streak
        )
        
        self.quest_sets[user_id] = quest_set
        return quest_set
    
    def update_quest_progress(self, user_id: str, quest_type: QuestType, 
                              increment: int = 1) -> Dict[str, Any]:
        """Görev ilerlemesini güncelle"""
        quest_set = self.quest_sets.get(user_id)
        if not quest_set:
            return {"error": "No quest set found"}
        
        for quest in quest_set.quests:
            if quest.quest_type == quest_type and not quest.completed:
                quest.current_count = min(quest.target_count, 
                                         quest.current_count + increment)
                
                if quest.current_count >= quest.target_count:
                    quest.completed = True
                    
                    # Tümü tamamlandı mı?
                    if all(q.completed for q in quest_set.quests):
                        quest_set.all_completed = True
                        return {
                            "quest_completed": True,
                            "all_completed": True,
                            "xp_earned": quest.xp_reward + quest_set.completion_bonus,
                            "streak": quest_set.streak_day + 1,
                            "message": "🎉 Tüm günlük görevler tamamlandı! Bonus XP kazandın!"
                        }
                    
                    return {
                        "quest_completed": True,
                        "all_completed": False,
                        "xp_earned": quest.xp_reward,
                        "progress": f"{sum(1 for q in quest_set.quests if q.completed)}/3"
                    }
                
                return {
                    "quest_completed": False,
                    "progress": f"{quest.current_count}/{quest.target_count}"
                }
        
        return {"message": "No matching quest found"}


class RandomEventEngine:
    """Random Event yönetim engine'i"""
    
    # Event havuzu
    EVENT_POOL = [
        {
            "type": EventType.BONUS_XP,
            "title": "⚡ Double XP!",
            "description": "Sonraki 30 dakika 2x XP kazan!",
            "icon": "⚡",
            "multiplier": 2.0,
            "duration": 30,
            "rarity": "common",
            "weight": 30
        },
        {
            "type": EventType.DOUBLE_RETENTION,
            "title": "🧠 Super Memory!",
            "description": "Sonraki 30 dakika öğrendiklerin 2x daha iyi kalıcı!",
            "icon": "🧠",
            "multiplier": 2.0,
            "duration": 30,
            "rarity": "rare",
            "weight": 20
        },
        {
            "type": EventType.LUCKY_STREAK,
            "title": "🍀 Lucky Streak!",
            "description": "Bugün streak'in korunuyor!",
            "icon": "🍀",
            "multiplier": 1.0,
            "duration": 1440,  # 24 saat
            "rarity": "rare",
            "weight": 15
        },
        {
            "type": EventType.WISDOM_BOOST,
            "title": "💡 Wisdom Boost!",
            "description": "Ekstra ipuçları ve açıklamalar!",
            "icon": "💡",
            "multiplier": 1.5,
            "duration": 60,
            "rarity": "common",
            "weight": 25
        },
        {
            "type": EventType.TIME_WARP,
            "title": "⏰ Time Warp!",
            "description": "Review süreleri yarıya indi!",
            "icon": "⏰",
            "multiplier": 0.5,
            "duration": 45,
            "rarity": "epic",
            "weight": 8
        },
        {
            "type": EventType.TREASURE,
            "title": "💎 Hidden Treasure!",
            "description": "Gizli bonus içerik açıldı!",
            "icon": "💎",
            "multiplier": 1.0,
            "duration": 60,
            "rarity": "legendary",
            "weight": 2
        }
    ]
    
    def __init__(self):
        self.active_events: Dict[str, List[RandomEvent]] = {}  # user_id -> events
    
    def try_trigger_event(self, user_id: str, trigger_chance: float = 0.1) -> Optional[RandomEvent]:
        """Random event tetiklemeye çalış"""
        if random.random() > trigger_chance:
            return None
        
        # Ağırlıklı seçim
        total_weight = sum(e["weight"] for e in self.EVENT_POOL)
        r = random.uniform(0, total_weight)
        
        cumulative = 0
        selected = None
        for event_template in self.EVENT_POOL:
            cumulative += event_template["weight"]
            if r <= cumulative:
                selected = event_template
                break
        
        if not selected:
            return None
        
        # Event oluştur
        event = RandomEvent(
            event_type=selected["type"],
            title=selected["title"],
            description=selected["description"],
            icon=selected["icon"],
            multiplier=selected["multiplier"],
            duration_minutes=selected["duration"],
            rarity=selected["rarity"],
            expires_at=datetime.now() + timedelta(minutes=selected["duration"])
        )
        
        if user_id not in self.active_events:
            self.active_events[user_id] = []
        self.active_events[user_id].append(event)
        
        return event
    
    def get_active_events(self, user_id: str) -> List[RandomEvent]:
        """Aktif eventleri al"""
        events = self.active_events.get(user_id, [])
        
        # Süresi dolmuş olanları temizle
        now = datetime.now()
        active = [e for e in events if e.expires_at > now]
        self.active_events[user_id] = active
        
        return active
    
    def get_multipliers(self, user_id: str) -> Dict[str, float]:
        """Aktif çarpanları al"""
        events = self.get_active_events(user_id)
        
        multipliers = {
            "xp": 1.0,
            "retention": 1.0,
            "review_time": 1.0
        }
        
        for event in events:
            if event.event_type == EventType.BONUS_XP:
                multipliers["xp"] *= event.multiplier
            elif event.event_type == EventType.DOUBLE_RETENTION:
                multipliers["retention"] *= event.multiplier
            elif event.event_type == EventType.TIME_WARP:
                multipliers["review_time"] *= event.multiplier
        
        return multipliers


# ============ SINGLETON INSTANCES ============

skill_tree_engine = SkillTreeEngine()
boss_battle_engine = BossBattleEngine()
daily_quest_engine = DailyQuestEngine()
random_event_engine = RandomEventEngine()
