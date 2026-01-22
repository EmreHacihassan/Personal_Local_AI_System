"""
Full Meta Learning - Premium Endpoints
Gelişmiş Full Meta Learning modülleri için API endpoints

Bu dosya, yeni eklenen premium modüller için API endpoint'lerini tanımlar.
Mevcut full_meta_endpoints.py ile birlikte çalışır.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/full-meta/premium", tags=["Full Meta Premium"])


# ==================== PYDANTIC MODELS ====================

class ThetaSessionRequest(BaseModel):
    user_id: str
    topic: str
    duration_minutes: int = 25


class MemoryPalaceRequest(BaseModel):
    user_id: str
    name: str
    items: List[str]


class ChunkRequest(BaseModel):
    content: str
    max_items: int = 7


class BossBattleRequest(BaseModel):
    difficulty: str
    content_items: List[Dict[str, Any]]
    package_id: Optional[str] = None


class AnswerRequest(BaseModel):
    attempt_id: str
    question_id: str
    answer: Any


class ReviewCardRequest(BaseModel):
    card_id: str
    quality: str
    context: Optional[Dict[str, Any]] = None
    emotion: Optional[str] = None


class RubberDuckRequest(BaseModel):
    user_id: str
    topic: str
    level: str = "beginner"


class ExplanationRequest(BaseModel):
    session_id: str
    explanation: str


class StudyPlanRequest(BaseModel):
    user_id: str
    topics: List[str]
    available_hours: Dict[str, List[str]]
    duration_days: int = 7


class TutorAvatarRequest(BaseModel):
    user_id: str
    name: str = "Atlas"
    personality: str = "mentor"


class NoteRequest(BaseModel):
    user_id: str
    title: str
    topic: str
    note_type: str = "summary"


# ==================== LAZY IMPORTS ====================

def get_neuroscience_engines():
    """Neuroscience engine'lerini lazy load"""
    from core.full_meta_neuroscience import (
        theta_wave_engine, memory_palace_engine, chunking_engine,
        dual_coding_engine, interleaving_engine
    )
    return {
        "theta": theta_wave_engine,
        "palace": memory_palace_engine,
        "chunk": chunking_engine,
        "dual": dual_coding_engine,
        "interleave": interleaving_engine
    }


def get_gamification_engines():
    """Gamification engine'lerini lazy load"""
    from core.full_meta_gamification import (
        skill_tree_engine, boss_battle_engine, daily_quest_engine,
        random_event_engine, BattleDifficulty, QuestType
    )
    return {
        "skill_tree": skill_tree_engine,
        "boss": boss_battle_engine,
        "quest": daily_quest_engine,
        "event": random_event_engine,
        "BattleDifficulty": BattleDifficulty,
        "QuestType": QuestType
    }


def get_adaptive_engines():
    """Adaptive engine'lerini lazy load"""
    from core.full_meta_adaptive import (
        struggle_detection_engine, learning_style_engine,
        optimal_time_engine, forgetting_prediction_engine,
        confusion_clustering_engine
    )
    return {
        "struggle": struggle_detection_engine,
        "style": learning_style_engine,
        "time": optimal_time_engine,
        "forget": forgetting_prediction_engine,
        "confusion": confusion_clustering_engine
    }


def get_multimodal_engines():
    """Multimodal engine'lerini lazy load"""
    from core.full_meta_multimodal import (
        visual_content_engine, interactive_diagram_engine,
        mnemonic_generator_engine, code_playground_engine,
        sketch_explain_engine, VisualType, MnemonicType, CodeLanguage
    )
    return {
        "visual": visual_content_engine,
        "diagram": interactive_diagram_engine,
        "mnemonic": mnemonic_generator_engine,
        "code": code_playground_engine,
        "sketch": sketch_explain_engine,
        "VisualType": VisualType,
        "MnemonicType": MnemonicType,
        "CodeLanguage": CodeLanguage
    }


def get_spaced_rep_engines():
    """Spaced repetition engine'lerini lazy load"""
    from core.full_meta_spaced_rep import (
        advanced_spaced_repetition_engine, context_aware_spacing_engine,
        emotional_tagging_engine, related_recall_engine,
        sleep_optimized_scheduler, EmotionalTag, RecallQuality
    )
    return {
        "sr": advanced_spaced_repetition_engine,
        "context": context_aware_spacing_engine,
        "emotion": emotional_tagging_engine,
        "recall": related_recall_engine,
        "sleep": sleep_optimized_scheduler,
        "EmotionalTag": EmotionalTag,
        "RecallQuality": RecallQuality
    }


def get_feynman_engines():
    """Feynman engine'lerini lazy load"""
    from core.full_meta_feynman import (
        rubber_duck_engine, analogy_generator_engine,
        concept_map_builder_engine, gap_detector_engine,
        teaching_mode_engine, ExplanationLevel, AnalogyDomain
    )
    return {
        "duck": rubber_duck_engine,
        "analogy": analogy_generator_engine,
        "cmap": concept_map_builder_engine,
        "gap": gap_detector_engine,
        "teach": teaching_mode_engine,
        "ExplanationLevel": ExplanationLevel,
        "AnalogyDomain": AnalogyDomain
    }


def get_analytics_engines():
    """Analytics engine'lerini lazy load"""
    from core.full_meta_analytics import (
        learning_velocity_engine, strength_map_engine,
        time_roi_engine, study_plan_engine,
        burnout_detector_engine, exam_prediction_engine
    )
    return {
        "velocity": learning_velocity_engine,
        "strength": strength_map_engine,
        "roi": time_roi_engine,
        "plan": study_plan_engine,
        "burnout": burnout_detector_engine,
        "exam": exam_prediction_engine
    }


def get_premium_engines():
    """Premium engine'lerini lazy load"""
    from core.full_meta_premium import (
        ai_tutor_engine, reverse_engineering_engine,
        mastery_certification_engine, learning_notes_engine,
        TutorPersonality, NoteType, CertificationLevel
    )
    return {
        "tutor": ai_tutor_engine,
        "reverse": reverse_engineering_engine,
        "cert": mastery_certification_engine,
        "notes": learning_notes_engine,
        "TutorPersonality": TutorPersonality,
        "NoteType": NoteType,
        "CertificationLevel": CertificationLevel
    }


# ==================== NEUROSCIENCE ENDPOINTS ====================

@router.post("/neuroscience/theta-session")
async def start_theta_session(request: ThetaSessionRequest):
    """Theta wave sync oturumu başlat"""
    engines = get_neuroscience_engines()
    session = engines["theta"].start_session(
        request.user_id, 
        request.topic,
        request.duration_minutes
    )
    return {
        "session_id": session.id,
        "state": session.state.value,
        "duration": session.duration_minutes
    }


@router.get("/neuroscience/theta-session/{session_id}/state")
async def get_theta_state(session_id: str):
    """Theta oturum durumunu al"""
    engines = get_neuroscience_engines()
    state = engines["theta"].get_current_state(session_id)
    return state


@router.post("/neuroscience/memory-palace")
async def create_memory_palace(request: MemoryPalaceRequest):
    """Memory palace oluştur"""
    engines = get_neuroscience_engines()
    palace = engines["palace"].create_palace(
        request.user_id,
        request.name,
        request.items
    )
    return {
        "palace_id": palace.id,
        "rooms": len(palace.rooms),
        "items_placed": sum(len(r.items) for r in palace.rooms)
    }


@router.post("/neuroscience/chunk")
async def chunk_content(request: ChunkRequest):
    """İçeriği chunk'la"""
    engines = get_neuroscience_engines()
    result = engines["chunk"].chunk_content(request.content, request.max_items)
    return result


# ==================== GAMIFICATION ENDPOINTS ====================

@router.post("/gamification/skill-tree")
async def create_skill_tree(
    workspace_id: str = Body(...),
    stages: List[Dict] = Body(...),
    packages: List[Dict] = Body(...)
):
    """Skill tree oluştur"""
    engines = get_gamification_engines()
    tree = engines["skill_tree"].create_tree_from_workspace(workspace_id, stages, packages)
    return tree.get_visualization_data()


@router.post("/gamification/boss-battle")
async def create_boss_battle(request: BossBattleRequest):
    """Boss battle oluştur"""
    engines = get_gamification_engines()
    difficulty = engines["BattleDifficulty"](request.difficulty)
    battle = engines["boss"].create_battle(
        difficulty, 
        request.content_items,
        request.package_id
    )
    return {
        "battle_id": battle.id,
        "difficulty": battle.difficulty.value,
        "questions": len(battle.questions),
        "passing_score": battle.passing_score
    }


@router.post("/gamification/boss-battle/{battle_id}/start")
async def start_battle_attempt(battle_id: str):
    """Boss battle denemesi başlat"""
    engines = get_gamification_engines()
    attempt = engines["boss"].start_attempt(battle_id)
    if not attempt:
        raise HTTPException(status_code=400, detail="Cannot start attempt")
    return {"attempt_id": attempt.id}


@router.get("/gamification/daily-quests/{user_id}")
async def get_daily_quests(user_id: str, packages: List[str] = Query(default=[])):
    """Günlük görevleri al"""
    engines = get_gamification_engines()
    quest_set = engines["quest"].generate_daily_quests(user_id, packages)
    return {
        "quests": [vars(q) for q in quest_set.quests],
        "streak": quest_set.streak_day,
        "all_completed": quest_set.all_completed
    }


@router.post("/gamification/random-event/{user_id}")
async def try_trigger_event(user_id: str, chance: float = Query(0.1)):
    """Random event tetiklemeyi dene"""
    engines = get_gamification_engines()
    event = engines["event"].try_trigger_event(user_id, chance)
    if event:
        return {"triggered": True, "event": vars(event)}
    return {"triggered": False}


# ==================== ADAPTIVE ENDPOINTS ====================

@router.post("/adaptive/struggle-detect")
async def detect_struggle(
    user_id: str = Body(...),
    content_id: str = Body(...),
    metrics: Dict[str, Any] = Body(...)
):
    """Zorlanma tespit et"""
    engines = get_adaptive_engines()
    indicator = engines["struggle"].detect_struggle(user_id, content_id, metrics)
    interventions = engines["struggle"].get_intervention(indicator)
    return {
        "level": indicator.struggle_level.value,
        "confidence": indicator.confidence_score,
        "interventions": [i.value for i in interventions]
    }


@router.get("/adaptive/learning-style/{user_id}")
async def get_learning_style(user_id: str):
    """Öğrenme stilini al"""
    engines = get_adaptive_engines()
    profile = engines["style"].get_profile(user_id)
    if not profile:
        return {"has_profile": False}
    return {"has_profile": True, "profile": vars(profile)}


@router.get("/adaptive/optimal-time/{user_id}")
async def get_optimal_times(user_id: str):
    """Optimal zamanları al"""
    engines = get_adaptive_engines()
    return engines["time"].get_optimal_times(user_id)


@router.get("/adaptive/forgetting-forecast/{user_id}")
async def get_forgetting_forecast(user_id: str, days: int = Query(7)):
    """Unutma tahmini al"""
    engines = get_adaptive_engines()
    return engines["forget"].get_retention_forecast(user_id, days)


@router.get("/adaptive/confusion-map/{user_id}")
async def get_confusion_map(user_id: str):
    """Karışıklık haritası al"""
    engines = get_adaptive_engines()
    return engines["confusion"].get_confusion_map(user_id)


# ==================== SPACED REPETITION ENDPOINTS ====================

@router.post("/spaced-rep/card")
async def create_sr_card(
    user_id: str = Body(...),
    front: str = Body(...),
    back: str = Body(...),
    content_id: str = Body("")
):
    """Spaced repetition kartı oluştur"""
    engines = get_spaced_rep_engines()
    card = engines["sr"].create_card(user_id, front, back, content_id)
    return {"card_id": card.id}


@router.post("/spaced-rep/review")
async def review_card(request: ReviewCardRequest):
    """Kartı tekrar et"""
    engines = get_spaced_rep_engines()
    quality = engines["RecallQuality"](request.quality)
    emotion = engines["EmotionalTag"](request.emotion) if request.emotion else None
    
    result = engines["sr"].review_card(
        request.card_id, quality, request.context, emotion
    )
    return result


@router.get("/spaced-rep/due/{user_id}")
async def get_due_cards(user_id: str, limit: int = Query(20)):
    """Tekrar edilecek kartları al"""
    engines = get_spaced_rep_engines()
    cards = engines["sr"].get_due_cards(user_id, limit)
    return {
        "cards": [
            {"id": c.id, "front": c.front, "back": c.back, "retrievability": c.retrievability}
            for c in cards
        ]
    }


@router.get("/spaced-rep/forecast/{user_id}")
async def get_sr_forecast(user_id: str, days: int = Query(7)):
    """SR tahminleri al"""
    engines = get_spaced_rep_engines()
    return engines["sr"].get_forecast(user_id, days)


# ==================== FEYNMAN ENDPOINTS ====================

@router.post("/feynman/rubber-duck")
async def start_rubber_duck_session(request: RubberDuckRequest):
    """Rubber duck oturumu başlat"""
    engines = get_feynman_engines()
    level = engines["ExplanationLevel"](request.level)
    session = engines["duck"].start_session(request.user_id, request.topic, level)
    return {"session_id": session.id, "conversation": session.conversation}


@router.post("/feynman/rubber-duck/explain")
async def send_explanation(request: ExplanationRequest):
    """Açıklama gönder"""
    engines = get_feynman_engines()
    result = engines["duck"].process_explanation(request.session_id, request.explanation)
    return result


@router.post("/feynman/rubber-duck/{session_id}/end")
async def end_rubber_duck_session(session_id: str):
    """Rubber duck oturumunu bitir"""
    engines = get_feynman_engines()
    return engines["duck"].end_session(session_id)


@router.post("/feynman/analogy")
async def generate_analogy(concept: str = Body(...), domain: str = Body("everyday")):
    """Analoji oluştur"""
    engines = get_feynman_engines()
    d = engines["AnalogyDomain"](domain)
    analogy = engines["analogy"].generate_analogy(concept, d)
    return vars(analogy)


@router.post("/feynman/concept-map")
async def create_concept_map(
    title: str = Body(...),
    topic: str = Body(...),
    central_concept: str = Body(...)
):
    """Kavram haritası oluştur"""
    engines = get_feynman_engines()
    cmap = engines["cmap"].create_map(title, topic, central_concept)
    return engines["cmap"].get_map_data(cmap.id)


@router.get("/feynman/gap-summary/{user_id}")
async def get_gap_summary(user_id: str):
    """Bilgi boşluğu özeti"""
    engines = get_feynman_engines()
    return engines["gap"].get_gap_summary(user_id)


# ==================== ANALYTICS ENDPOINTS ====================

@router.get("/analytics/velocity/{user_id}")
async def get_velocity_graph(user_id: str, days: int = Query(30)):
    """Velocity grafiği verisi"""
    engines = get_analytics_engines()
    return engines["velocity"].get_velocity_graph_data(user_id, days)


@router.get("/analytics/strength-map/{user_id}")
async def get_strength_map(user_id: str):
    """Güç haritası"""
    engines = get_analytics_engines()
    return engines["strength"].get_strength_map(user_id)


@router.get("/analytics/roi/{user_id}")
async def get_roi_analysis(user_id: str):
    """ROI analizi"""
    engines = get_analytics_engines()
    return engines["roi"].get_roi_analysis(user_id)


@router.post("/analytics/study-plan")
async def generate_study_plan(request: StudyPlanRequest):
    """Çalışma planı oluştur"""
    engines = get_analytics_engines()
    plan = engines["plan"].generate_plan(
        request.user_id, request.topics, 
        request.available_hours, duration_days=request.duration_days
    )
    return {"plan_id": plan.id, "slots": len(plan.slots), "daily_goal": plan.daily_goal_minutes}


@router.get("/analytics/study-plan/today/{user_id}")
async def get_today_plan(user_id: str):
    """Bugünkü plan"""
    engines = get_analytics_engines()
    return engines["plan"].get_today_plan(user_id)


@router.get("/analytics/burnout/{user_id}")
async def get_burnout_assessment(user_id: str):
    """Tükenmişlik değerlendirmesi"""
    engines = get_analytics_engines()
    velocity_engines = get_analytics_engines()
    points = velocity_engines["velocity"].data_points.get(user_id, [])
    engines["burnout"].assess_burnout_risk(user_id, points)
    return engines["burnout"].get_burnout_dashboard(user_id)


@router.post("/analytics/exam-prediction")
async def predict_exam_score(
    user_id: str = Body(...),
    topics: List[str] = Body(...),
    exam_type: str = Body("general")
):
    """Sınav puanı tahmin et"""
    engines = get_analytics_engines()
    strength_data = engines["strength"].get_strength_map(user_id)
    topic_strengths = {}
    if strength_data.get("has_data"):
        for t in strength_data["topics"]:
            topic_strengths[t["topic"]] = t["score"]
    
    engines["exam"].predict_score(user_id, topics, topic_strengths, exam_type)
    return engines["exam"].get_prediction_analysis(user_id)


# ==================== PREMIUM ENDPOINTS ====================

@router.post("/tutor/avatar")
async def create_tutor_avatar(request: TutorAvatarRequest):
    """AI Tutor avatar oluştur"""
    engines = get_premium_engines()
    personality = engines["TutorPersonality"](request.personality)
    avatar = engines["tutor"].create_avatar(request.user_id, request.name, personality)
    return {"avatar_id": avatar.id, "name": avatar.name}


@router.post("/tutor/session")
async def start_tutor_session(avatar_id: str = Body(...), topic: str = Body(...)):
    """Tutor oturumu başlat"""
    engines = get_premium_engines()
    session = engines["tutor"].start_session(avatar_id, topic)
    if not session:
        raise HTTPException(status_code=404, detail="Avatar not found")
    return {"session_id": session.id, "messages": session.messages}


@router.post("/tutor/message")
async def send_tutor_message(session_id: str = Body(...), message: str = Body(...)):
    """Tutor'a mesaj gönder"""
    engines = get_premium_engines()
    return engines["tutor"].send_message(session_id, message)


@router.post("/reverse-engineering")
async def start_reverse_engineering(
    user_id: str = Body(...),
    target_result: str = Body(...),
    domain: str = Body("general")
):
    """Reverse engineering oturumu başlat"""
    engines = get_premium_engines()
    session = engines["reverse"].start_session(user_id, target_result, domain)
    return {
        "session_id": session.id,
        "components": session.components,
        "learning_path": session.learning_path
    }


@router.post("/certification")
async def create_certification_path(
    user_id: str = Body(...),
    topic: str = Body(...),
    level: str = Body("beginner")
):
    """Sertifika yolu oluştur"""
    engines = get_premium_engines()
    cert_level = engines["CertificationLevel"](level)
    cert = engines["cert"].create_certification_path(user_id, topic, cert_level)
    return {"cert_id": cert.id, "title": cert.title, "requirements": cert.requirements}


@router.post("/certification/{cert_id}/assess")
async def conduct_certification_assessment(cert_id: str, score: float = Body(...)):
    """Sertifika değerlendirmesi yap"""
    engines = get_premium_engines()
    return engines["cert"].conduct_assessment(cert_id, score)


@router.get("/certification/{cert_id}")
async def get_certificate(cert_id: str):
    """Sertifika al"""
    engines = get_premium_engines()
    return engines["cert"].get_certificate(cert_id)


@router.post("/notes")
async def create_learning_note(request: NoteRequest):
    """Öğrenme notu oluştur"""
    engines = get_premium_engines()
    n_type = engines["NoteType"](request.note_type)
    note = engines["notes"].create_note(request.user_id, request.title, request.topic, n_type)
    return {
        "note_id": note.id,
        "sections": {k.value: v for k, v in note.sections.items()},
        "prompts": engines["notes"].get_note_prompts(n_type)
    }


@router.post("/notes/{note_id}/flashcards")
async def generate_flashcards_from_note(note_id: str, user_id: str = Body(...)):
    """Nottan flashcard oluştur"""
    engines = get_premium_engines()
    flashcards = engines["notes"].generate_flashcards_from_note(note_id, user_id)
    return {"flashcards": flashcards}


@router.get("/notes/{note_id}/export")
async def export_note(note_id: str, user_id: str = Query(...), format: str = Query("markdown")):
    """Notu export et"""
    engines = get_premium_engines()
    content = engines["notes"].export_note(note_id, user_id, format)
    if not content:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"content": content, "format": format}


# ==================== DASHBOARD ====================

@router.get("/dashboard/{user_id}")
async def get_premium_dashboard(user_id: str):
    """Premium Full Meta Learning dashboard"""
    analytics = get_analytics_engines()
    gamification = get_gamification_engines()
    spaced_rep = get_spaced_rep_engines()
    feynman = get_feynman_engines()
    
    return {
        "velocity": analytics["velocity"].velocities.get(user_id),
        "strength_map": analytics["strength"].get_strength_map(user_id),
        "burnout": analytics["burnout"].get_burnout_dashboard(user_id),
        "daily_quests": {
            "available": True,
            "streak": gamification["quest"].streaks.get(user_id, 0)
        },
        "active_events": [
            vars(e) for e in gamification["event"].get_active_events(user_id)
        ],
        "due_cards": len(spaced_rep["sr"].get_due_cards(user_id, 100)),
        "gap_summary": feynman["gap"].get_gap_summary(user_id)
    }
