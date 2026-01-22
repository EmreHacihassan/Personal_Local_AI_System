"""
🎓 Exam System with Feynman Technique
AI-Powered Sınav ve Değerlendirme Sistemi

Bu modül şunları içerir:
1. Feynman Tekniği Sınavları - Kullanıcı anlatır, AI değerlendirir
2. Çoktan Seçmeli Testler
3. Problem Çözme Sınavları
4. Oral Presentation değerlendirmesi
5. Concept Mapping
6. Peer Review
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from .models import (
    Exam, ExamType, ExamQuestion, Package, Stage,
    DifficultyLevel
)


# ==================== EVALUATION RESULTS ====================

@dataclass
class EvaluationCriteria:
    """Değerlendirme kriteri"""
    name: str
    max_score: float
    weight: float = 1.0
    description: str = ""

@dataclass
class CriteriaScore:
    """Kriter puanı"""
    criteria_name: str
    score: float
    max_score: float
    feedback: str

@dataclass
class ExamResult:
    """Sınav sonucu"""
    exam_id: str
    user_id: str
    exam_type: ExamType
    total_score: float
    max_possible_score: float
    percentage: float
    passed: bool
    attempt_number: int
    criteria_scores: List[CriteriaScore] = field(default_factory=list)
    detailed_feedback: str = ""
    suggestions: List[str] = field(default_factory=list)
    time_taken_seconds: int = 0
    submitted_at: str = field(default_factory=lambda: datetime.now().isoformat())
    ai_evaluator_model: str = ""
    
    @property
    def grade(self) -> str:
        if self.percentage >= 90:
            return "A+"
        elif self.percentage >= 85:
            return "A"
        elif self.percentage >= 80:
            return "B+"
        elif self.percentage >= 75:
            return "B"
        elif self.percentage >= 70:
            return "C+"
        elif self.percentage >= 65:
            return "C"
        elif self.percentage >= 60:
            return "D"
        else:
            return "F"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_id": self.exam_id,
            "user_id": self.user_id,
            "exam_type": self.exam_type.value,
            "total_score": self.total_score,
            "max_possible_score": self.max_possible_score,
            "percentage": round(self.percentage, 1),
            "grade": self.grade,
            "passed": self.passed,
            "attempt_number": self.attempt_number,
            "criteria_scores": [
                {
                    "name": c.criteria_name,
                    "score": c.score,
                    "max_score": c.max_score,
                    "feedback": c.feedback
                } for c in self.criteria_scores
            ],
            "detailed_feedback": self.detailed_feedback,
            "suggestions": self.suggestions,
            "time_taken_seconds": self.time_taken_seconds,
            "submitted_at": self.submitted_at
        }


# ==================== FEYNMAN EXAM EVALUATOR ====================

class FeynmanExamEvaluator:
    """
    Feynman Tekniği Sınav Değerlendiricisi
    
    Richard Feynman'ın öğrenme tekniği:
    1. Konuyu seç
    2. Bir çocuğa anlatır gibi basit bir dille açıkla
    3. Eksik kaldığın yerleri tespit et
    4. Geri dön, öğren, basitleştir
    
    Bu sınav türünde:
    - Kullanıcı konuyu kendi cümleleriyle anlatır
    - AI, anlatımı değerlendirir
    - Eksik/yanlış kavramları tespit eder
    - Geri bildirim verir
    """
    
    EVALUATION_CRITERIA = [
        EvaluationCriteria(
            name="concept_accuracy",
            max_score=30,
            weight=1.5,
            description="Kavramların doğruluğu ve eksiksizliği"
        ),
        EvaluationCriteria(
            name="simplicity",
            max_score=20,
            weight=1.0,
            description="Basit ve anlaşılır dil kullanımı"
        ),
        EvaluationCriteria(
            name="examples",
            max_score=15,
            weight=1.0,
            description="Uygun örnekler kullanımı"
        ),
        EvaluationCriteria(
            name="logical_flow",
            max_score=15,
            weight=1.0,
            description="Mantıksal akış ve tutarlılık"
        ),
        EvaluationCriteria(
            name="completeness",
            max_score=20,
            weight=1.2,
            description="Konunun eksiksiz işlenmesi"
        )
    ]
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def evaluate(
        self, 
        exam: Exam, 
        user_explanation: str,
        user_id: str,
        attempt_number: int = 1,
        audio_transcript: Optional[str] = None
    ) -> ExamResult:
        """
        Feynman sınavını değerlendir
        
        Args:
            exam: Feynman sınavı
            user_explanation: Kullanıcının yazılı açıklaması
            user_id: Kullanıcı ID
            attempt_number: Deneme numarası
            audio_transcript: Sesli anlatım transkripsiyonu (opsiyonel)
        
        Returns:
            ExamResult
        """
        
        config = exam.feynman_config or {}
        topic = config.get("topic", "Konu")
        subtopics = config.get("subtopics", [])
        required_concepts = config.get("required_concepts", [])
        min_words = config.get("min_explanation_words", 100)
        
        # Metin birleştir
        full_text = user_explanation
        if audio_transcript:
            full_text = f"{user_explanation}\n\nSesli Anlatım:\n{audio_transcript}"
        
        # Kelime sayısı kontrolü
        word_count = len(full_text.split())
        word_penalty = 0
        if word_count < min_words:
            word_penalty = (min_words - word_count) / min_words * 20
        
        # AI ile değerlendirme
        if self.llm_service:
            evaluation = await self._evaluate_with_llm(
                topic=topic,
                subtopics=subtopics,
                required_concepts=required_concepts,
                user_text=full_text
            )
        else:
            # Mock değerlendirme (LLM olmadan)
            evaluation = self._mock_evaluation(
                topic=topic,
                subtopics=subtopics,
                required_concepts=required_concepts,
                user_text=full_text
            )
        
        # Kriterlere göre puanlama
        criteria_scores = []
        total_score = 0
        max_score = 0
        
        for criteria in self.EVALUATION_CRITERIA:
            score = evaluation.get(criteria.name, {}).get("score", 0)
            feedback = evaluation.get(criteria.name, {}).get("feedback", "")
            
            # Kelime cezası uygula
            if criteria.name == "completeness":
                score = max(0, score - word_penalty)
            
            weighted_score = score * criteria.weight
            weighted_max = criteria.max_score * criteria.weight
            
            criteria_scores.append(CriteriaScore(
                criteria_name=criteria.name,
                score=round(weighted_score, 1),
                max_score=weighted_max,
                feedback=feedback
            ))
            
            total_score += weighted_score
            max_score += weighted_max
        
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Öneriler oluştur
        suggestions = evaluation.get("suggestions", [])
        if not suggestions:
            suggestions = self._generate_suggestions(evaluation, topic, subtopics)
        
        # Detaylı geri bildirim
        detailed_feedback = evaluation.get("overall_feedback", "")
        if not detailed_feedback:
            detailed_feedback = self._generate_detailed_feedback(
                evaluation, topic, percentage
            )
        
        return ExamResult(
            exam_id=exam.id,
            user_id=user_id,
            exam_type=ExamType.FEYNMAN,
            total_score=round(total_score, 1),
            max_possible_score=round(max_score, 1),
            percentage=round(percentage, 1),
            passed=percentage >= exam.passing_score,
            attempt_number=attempt_number,
            criteria_scores=criteria_scores,
            detailed_feedback=detailed_feedback,
            suggestions=suggestions,
            ai_evaluator_model="gpt-4o" if self.llm_service else "mock"
        )
    
    async def _evaluate_with_llm(
        self,
        topic: str,
        subtopics: List[str],
        required_concepts: List[str],
        user_text: str
    ) -> Dict[str, Any]:
        """LLM ile değerlendirme"""
        
        prompt = f"""Sen bir Feynman Tekniği değerlendirmecisisin. Öğrencinin aşağıdaki konu hakkındaki açıklamasını değerlendir.

**Konu:** {topic}
**Alt Konular:** {', '.join(subtopics)}
**Gerekli Kavramlar:** {', '.join(required_concepts)}

**Öğrencinin Açıklaması:**
{user_text}

**Değerlendirme Kriterleri:**
1. concept_accuracy (0-30): Kavramların doğruluğu
2. simplicity (0-20): Basit dil kullanımı
3. examples (0-15): Örnek kullanımı
4. logical_flow (0-15): Mantıksal akış
5. completeness (0-20): Konunun eksiksizliği

Yanıtını şu JSON formatında ver:
{{
    "concept_accuracy": {{"score": X, "feedback": "..."}},
    "simplicity": {{"score": X, "feedback": "..."}},
    "examples": {{"score": X, "feedback": "..."}},
    "logical_flow": {{"score": X, "feedback": "..."}},
    "completeness": {{"score": X, "feedback": "..."}},
    "missing_concepts": ["..."],
    "incorrect_concepts": ["..."],
    "suggestions": ["..."],
    "overall_feedback": "..."
}}"""

        try:
            response = await self.llm_service.generate(prompt, json_mode=True)
            return json.loads(response)
        except:
            return self._mock_evaluation(topic, subtopics, required_concepts, user_text)
    
    def _mock_evaluation(
        self,
        topic: str,
        subtopics: List[str],
        required_concepts: List[str],
        user_text: str
    ) -> Dict[str, Any]:
        """Mock değerlendirme (test için)"""
        
        word_count = len(user_text.split())
        base_score = min(80, word_count / 5)  # Her 5 kelime için 1 puan
        
        # Konu kelimelerinin geçip geçmediğini kontrol et
        topic_mentions = sum(1 for t in subtopics if t.lower() in user_text.lower())
        topic_bonus = topic_mentions * 2
        
        return {
            "concept_accuracy": {
                "score": min(30, base_score * 0.3 + topic_bonus),
                "feedback": f"Konuyu genel olarak doğru anlatmışsın. {topic_mentions}/{len(subtopics)} alt konuya değindin."
            },
            "simplicity": {
                "score": min(20, base_score * 0.2),
                "feedback": "Dil kullanımın anlaşılır."
            },
            "examples": {
                "score": min(15, base_score * 0.15),
                "feedback": "Örnekler eklemen anlatımı güçlendirir."
            },
            "logical_flow": {
                "score": min(15, base_score * 0.15),
                "feedback": "Anlatımın mantıksal bir akış izliyor."
            },
            "completeness": {
                "score": min(20, base_score * 0.2),
                "feedback": f"Kelime sayısı: {word_count}. Daha fazla detay ekleyebilirsin."
            },
            "missing_concepts": [s for s in subtopics if s.lower() not in user_text.lower()],
            "incorrect_concepts": [],
            "suggestions": [
                "Daha fazla örnek ekle",
                "Kavramları basit kelimelerle açıkla",
                "Konu arasındaki bağlantıları göster"
            ],
            "overall_feedback": f"{topic} konusunu kendi cümlelerinle anlatmaya çalışmışsın. Devam et!"
        }
    
    def _generate_suggestions(
        self, 
        evaluation: Dict[str, Any],
        topic: str,
        subtopics: List[str]
    ) -> List[str]:
        """Öneriler oluştur"""
        suggestions = []
        
        missing = evaluation.get("missing_concepts", [])
        if missing:
            suggestions.append(f"Şu konulara değinmeyi unuttun: {', '.join(missing[:3])}")
        
        incorrect = evaluation.get("incorrect_concepts", [])
        if incorrect:
            suggestions.append(f"Şu kavramları gözden geçir: {', '.join(incorrect[:3])}")
        
        if evaluation.get("examples", {}).get("score", 0) < 10:
            suggestions.append("Günlük hayattan örnekler ekleyerek konuyu somutlaştır")
        
        if evaluation.get("simplicity", {}).get("score", 0) < 15:
            suggestions.append("Teknik terimleri daha basit kelimelerle açıkla")
        
        if not suggestions:
            suggestions.append("Harika iş! Şimdi farklı bir kitleye anlatmayı dene")
        
        return suggestions
    
    def _generate_detailed_feedback(
        self,
        evaluation: Dict[str, Any],
        topic: str,
        percentage: float
    ) -> str:
        """Detaylı geri bildirim oluştur"""
        
        if percentage >= 90:
            intro = f"Mükemmel! {topic} konusunu çok iyi anlatmışsın. 🌟"
        elif percentage >= 75:
            intro = f"Güzel iş! {topic} konusunu iyi kavramışsın. 👏"
        elif percentage >= 60:
            intro = f"İyi başlangıç! {topic} konusunda gelişim gösteriyorsun. 💪"
        else:
            intro = f"{topic} konusunu tekrar gözden geçirmeni öneririm. 📚"
        
        strengths = []
        weaknesses = []
        
        for key in ["concept_accuracy", "simplicity", "examples", "logical_flow", "completeness"]:
            criteria = evaluation.get(key, {})
            score = criteria.get("score", 0)
            max_scores = {"concept_accuracy": 30, "simplicity": 20, "examples": 15, "logical_flow": 15, "completeness": 20}
            
            ratio = score / max_scores.get(key, 1)
            
            if ratio >= 0.8:
                strengths.append(key.replace("_", " ").title())
            elif ratio < 0.5:
                weaknesses.append(key.replace("_", " ").title())
        
        feedback = intro + "\n\n"
        
        if strengths:
            feedback += f"**Güçlü Yönlerin:** {', '.join(strengths)}\n"
        
        if weaknesses:
            feedback += f"**Geliştirilebilir Yönlerin:** {', '.join(weaknesses)}\n"
        
        missing = evaluation.get("missing_concepts", [])
        if missing:
            feedback += f"\n**Eksik Kalan Konular:** {', '.join(missing[:5])}"
        
        return feedback


# ==================== MULTIPLE CHOICE EVALUATOR ====================

class MultipleChoiceEvaluator:
    """Çoktan seçmeli sınav değerlendiricisi"""
    
    def evaluate(
        self,
        exam: Exam,
        answers: Dict[str, str],  # question_id -> selected_answer
        user_id: str,
        attempt_number: int = 1,
        time_taken_seconds: int = 0
    ) -> ExamResult:
        """Çoktan seçmeli sınavı değerlendir"""
        
        correct_count = 0
        total_points = 0
        earned_points = 0
        criteria_scores = []
        
        for question in exam.questions:
            total_points += question.points
            user_answer = answers.get(question.id, "")
            
            is_correct = user_answer.upper() == question.correct_answer.upper()
            if is_correct:
                correct_count += 1
                earned_points += question.points
            
            criteria_scores.append(CriteriaScore(
                criteria_name=f"soru_{question.id[:8]}",
                score=question.points if is_correct else 0,
                max_score=question.points,
                feedback=question.explanation if not is_correct else "Doğru!"
            ))
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        return ExamResult(
            exam_id=exam.id,
            user_id=user_id,
            exam_type=ExamType.MULTIPLE_CHOICE,
            total_score=earned_points,
            max_possible_score=total_points,
            percentage=percentage,
            passed=percentage >= exam.passing_score,
            attempt_number=attempt_number,
            criteria_scores=criteria_scores,
            detailed_feedback=f"{correct_count}/{len(exam.questions)} soru doğru.",
            time_taken_seconds=time_taken_seconds
        )


# ==================== PROBLEM SOLVING EVALUATOR ====================

class ProblemSolvingEvaluator:
    """Problem çözme sınavı değerlendiricisi"""
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def evaluate(
        self,
        exam: Exam,
        solutions: Dict[str, str],  # question_id -> solution_text
        user_id: str,
        attempt_number: int = 1,
        time_taken_seconds: int = 0
    ) -> ExamResult:
        """Problem çözme sınavını değerlendir"""
        
        total_points = 0
        earned_points = 0
        criteria_scores = []
        
        for question in exam.questions:
            total_points += question.points
            solution = solutions.get(question.id, "")
            
            if self.llm_service:
                score, feedback = await self._evaluate_solution_with_llm(
                    question, solution
                )
            else:
                score, feedback = self._mock_evaluate_solution(question, solution)
            
            earned_points += score
            criteria_scores.append(CriteriaScore(
                criteria_name=f"problem_{question.id[:8]}",
                score=score,
                max_score=question.points,
                feedback=feedback
            ))
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        return ExamResult(
            exam_id=exam.id,
            user_id=user_id,
            exam_type=ExamType.PROBLEM_SOLVING,
            total_score=earned_points,
            max_possible_score=total_points,
            percentage=percentage,
            passed=percentage >= exam.passing_score,
            attempt_number=attempt_number,
            criteria_scores=criteria_scores,
            detailed_feedback=f"Toplam {earned_points}/{total_points} puan aldın.",
            time_taken_seconds=time_taken_seconds
        )
    
    async def _evaluate_solution_with_llm(
        self, 
        question: ExamQuestion, 
        solution: str
    ) -> Tuple[float, str]:
        """LLM ile çözüm değerlendir"""
        
        prompt = f"""Aşağıdaki matematik probleminin çözümünü değerlendir.

**Problem:**
{question.question}

**Öğrenci Çözümü:**
{solution}

**Rubrik:**
{json.dumps(question.rubric, ensure_ascii=False) if question.rubric else "Genel değerlendirme"}

**Maksimum Puan:** {question.points}

Yanıtını şu formatta ver:
{{
    "score": X,
    "feedback": "Değerlendirme ve açıklama..."
}}"""

        try:
            response = await self.llm_service.generate(prompt, json_mode=True)
            data = json.loads(response)
            return data.get("score", 0), data.get("feedback", "")
        except:
            return self._mock_evaluate_solution(question, solution)
    
    def _mock_evaluate_solution(
        self, 
        question: ExamQuestion, 
        solution: str
    ) -> Tuple[float, str]:
        """Mock çözüm değerlendirmesi"""
        
        # Basit heuristik: kelime sayısına göre puan
        word_count = len(solution.split())
        
        if word_count < 10:
            score = question.points * 0.2
            feedback = "Çözümün çok kısa. Adımları detaylı göster."
        elif word_count < 30:
            score = question.points * 0.5
            feedback = "İyi başlangıç ama daha fazla açıklama gerekiyor."
        elif word_count < 50:
            score = question.points * 0.75
            feedback = "Güzel çözüm! Birkaç detay eksik kalmış."
        else:
            score = question.points * 0.9
            feedback = "Kapsamlı ve detaylı bir çözüm. Harika!"
        
        return round(score, 1), feedback


# ==================== TEACH BACK EVALUATOR ====================

class TeachBackEvaluator:
    """
    Teach-Back (Öğreterek Öğrenme) Değerlendiricisi
    
    Kullanıcı konuyu başka birine öğretiyormuş gibi anlatır.
    AI, bir öğrenci gibi sorular sorabilir.
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def evaluate(
        self,
        exam: Exam,
        teaching_content: str,
        user_id: str,
        attempt_number: int = 1,
        qa_history: Optional[List[Dict[str, str]]] = None
    ) -> ExamResult:
        """Teach-back sınavını değerlendir"""
        
        # Feynman benzeri değerlendirme + etkileşim puanı
        base_evaluator = FeynmanExamEvaluator(self.llm_service)
        result = await base_evaluator.evaluate(
            exam, teaching_content, user_id, attempt_number
        )
        
        # Soru-cevap etkileşimi varsa ekstra puan
        if qa_history and len(qa_history) > 0:
            interaction_bonus = min(10, len(qa_history) * 2)
            result.total_score += interaction_bonus
            result.percentage = (result.total_score / result.max_possible_score * 100)
            result.suggestions.append(
                f"Harika! {len(qa_history)} soruya cevap verdin."
            )
        
        result.exam_type = ExamType.TEACH_BACK
        return result


# ==================== CONCEPT MAP EVALUATOR ====================

class ConceptMapEvaluator:
    """
    Kavram Haritası Değerlendiricisi
    
    Kullanıcı kavramlar arası ilişkileri görselleştirir.
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
    
    async def evaluate(
        self,
        exam: Exam,
        concept_map: Dict[str, Any],  # nodes ve edges içeren yapı
        user_id: str,
        attempt_number: int = 1
    ) -> ExamResult:
        """Kavram haritasını değerlendir"""
        
        nodes = concept_map.get("nodes", [])
        edges = concept_map.get("edges", [])
        
        # Puanlama kriterleri
        node_count = len(nodes)
        edge_count = len(edges)
        
        # Düğüm sayısı puanı
        node_score = min(30, node_count * 3)
        
        # Bağlantı sayısı puanı
        edge_score = min(30, edge_count * 2)
        
        # Bağlantı/düğüm oranı (iyi bir haritada her düğümün en az 1-2 bağlantısı olmalı)
        ratio = edge_count / max(1, node_count)
        ratio_score = min(20, ratio * 10)
        
        # Etiketli bağlantı puanı
        labeled_edges = sum(1 for e in edges if e.get("label"))
        label_score = min(20, (labeled_edges / max(1, edge_count)) * 20)
        
        total_score = node_score + edge_score + ratio_score + label_score
        max_score = 100
        percentage = total_score
        
        criteria_scores = [
            CriteriaScore("node_coverage", node_score, 30, f"{node_count} kavram eklendi"),
            CriteriaScore("connections", edge_score, 30, f"{edge_count} bağlantı oluşturuldu"),
            CriteriaScore("interconnection", ratio_score, 20, f"Bağlantı oranı: {ratio:.1f}"),
            CriteriaScore("labeled_relations", label_score, 20, f"{labeled_edges} etiketli bağlantı")
        ]
        
        return ExamResult(
            exam_id=exam.id,
            user_id=user_id,
            exam_type=ExamType.CONCEPT_MAP,
            total_score=total_score,
            max_possible_score=max_score,
            percentage=percentage,
            passed=percentage >= exam.passing_score,
            attempt_number=attempt_number,
            criteria_scores=criteria_scores,
            detailed_feedback=f"Kavram haritanda {node_count} kavram ve {edge_count} bağlantı var.",
            suggestions=[
                "Daha fazla kavram ekle" if node_count < 8 else "Kavram sayısı yeterli",
                "Kavramlar arası daha fazla bağlantı kur" if ratio < 1.5 else "Bağlantılar iyi",
                "Bağlantılara açıklayıcı etiketler ekle" if labeled_edges < edge_count * 0.5 else "Etiketler iyi"
            ]
        )


# ==================== EXAM SYSTEM ORCHESTRATOR ====================

class ExamSystem:
    """
    Sınav Sistemi Orkestratörü
    
    Tüm sınav türlerini yönetir.
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.feynman_evaluator = FeynmanExamEvaluator(llm_service)
        self.mc_evaluator = MultipleChoiceEvaluator()
        self.problem_evaluator = ProblemSolvingEvaluator(llm_service)
        self.teach_back_evaluator = TeachBackEvaluator(llm_service)
        self.concept_map_evaluator = ConceptMapEvaluator(llm_service)
    
    async def evaluate_exam(
        self,
        exam: Exam,
        submission: Dict[str, Any],
        user_id: str,
        attempt_number: int = 1
    ) -> ExamResult:
        """Sınavı türüne göre değerlendir"""
        
        if exam.type == ExamType.FEYNMAN:
            return await self.feynman_evaluator.evaluate(
                exam=exam,
                user_explanation=submission.get("explanation", ""),
                user_id=user_id,
                attempt_number=attempt_number,
                audio_transcript=submission.get("audio_transcript")
            )
        
        elif exam.type == ExamType.MULTIPLE_CHOICE:
            return self.mc_evaluator.evaluate(
                exam=exam,
                answers=submission.get("answers", {}),
                user_id=user_id,
                attempt_number=attempt_number,
                time_taken_seconds=submission.get("time_taken_seconds", 0)
            )
        
        elif exam.type == ExamType.PROBLEM_SOLVING:
            return await self.problem_evaluator.evaluate(
                exam=exam,
                solutions=submission.get("solutions", {}),
                user_id=user_id,
                attempt_number=attempt_number,
                time_taken_seconds=submission.get("time_taken_seconds", 0)
            )
        
        elif exam.type == ExamType.TEACH_BACK:
            return await self.teach_back_evaluator.evaluate(
                exam=exam,
                teaching_content=submission.get("teaching_content", ""),
                user_id=user_id,
                attempt_number=attempt_number,
                qa_history=submission.get("qa_history")
            )
        
        elif exam.type == ExamType.CONCEPT_MAP:
            return await self.concept_map_evaluator.evaluate(
                exam=exam,
                concept_map=submission.get("concept_map", {}),
                user_id=user_id,
                attempt_number=attempt_number
            )
        
        else:
            # Diğer türler için basit değerlendirme
            return ExamResult(
                exam_id=exam.id,
                user_id=user_id,
                exam_type=exam.type,
                total_score=0,
                max_possible_score=100,
                percentage=0,
                passed=False,
                attempt_number=attempt_number,
                detailed_feedback="Bu sınav türü henüz desteklenmiyor."
            )
    
    async def generate_questions(
        self,
        topic: str,
        subtopics: List[str],
        exam_type: ExamType,
        count: int = 10,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    ) -> List[ExamQuestion]:
        """AI ile soru üret"""
        
        if not self.llm_service:
            return self._generate_mock_questions(topic, exam_type, count)
        
        # LLM ile soru üretimi
        prompt = f"""Aşağıdaki konu için {count} adet {exam_type.value} türünde soru oluştur.

**Konu:** {topic}
**Alt Konular:** {', '.join(subtopics)}
**Zorluk:** {difficulty.value}

Her soru için şu formatı kullan:
{{
    "questions": [
        {{
            "question": "Soru metni",
            "options": ["A", "B", "C", "D"] (çoktan seçmeli için),
            "correct_answer": "A",
            "explanation": "Açıklama",
            "points": 10,
            "topic": "Alt konu"
        }}
    ]
}}"""

        try:
            response = await self.llm_service.generate(prompt, json_mode=True)
            data = json.loads(response)
            
            questions = []
            for q_data in data.get("questions", []):
                questions.append(ExamQuestion(
                    type=exam_type,
                    question=q_data.get("question", ""),
                    options=q_data.get("options"),
                    correct_answer=q_data.get("correct_answer"),
                    explanation=q_data.get("explanation"),
                    points=q_data.get("points", 10),
                    topic=q_data.get("topic", topic)
                ))
            return questions
        except:
            return self._generate_mock_questions(topic, exam_type, count)
    
    def _generate_mock_questions(
        self, 
        topic: str, 
        exam_type: ExamType, 
        count: int
    ) -> List[ExamQuestion]:
        """Mock soru üretimi"""
        
        questions = []
        for i in range(count):
            if exam_type == ExamType.MULTIPLE_CHOICE:
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} ile ilgili örnek soru {i+1}?",
                    options=["A) Seçenek 1", "B) Seçenek 2", "C) Seçenek 3", "D) Seçenek 4"],
                    correct_answer="A",
                    explanation="Bu sorunun açıklaması...",
                    points=10,
                    topic=topic
                )
            else:
                q = ExamQuestion(
                    type=exam_type,
                    question=f"{topic} konusunda problem {i+1}",
                    points=20,
                    topic=topic
                )
            questions.append(q)
        return questions


# ==================== SINGLETON ====================

_exam_system: Optional[ExamSystem] = None

def get_exam_system() -> ExamSystem:
    global _exam_system
    if _exam_system is None:
        _exam_system = ExamSystem()
    return _exam_system
