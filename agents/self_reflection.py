"""
Enterprise AI Assistant - Self-Reflection & Critique System
============================================================

Self-Reflection, Self-Critique ve Iterative Refinement
Endüstri Standartlarında Kurumsal AI Çözümü

Bu modül, agent çıktılarının kalitesini değerlendiren, eleştiren
ve iteratif olarak iyileştiren sistemleri içerir.

Özellikler:
- Self-Reflection: Agent'ın kendi düşünce sürecini değerlendirmesi
- Self-Critique: Çıktının kalite kontrolü ve eleştirisi
- Critic Agent: Bağımsız değerlendirme agent'ı
- Iterative Refinement: Otomatik iyileştirme döngüsü
- Hallucination Detection: Uydurma tespiti
- Fact Verification: Gerçeklik kontrolü
- Quality Scoring: Çok boyutlu kalite skorlaması

Referanslar:
- Self-Refine: Iterative Refinement (Madaan et al., 2023)
- Reflexion: Language Agents with Verbal Reinforcement (Shinn et al., 2023)
- Constitutional AI (Anthropic, 2022)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import json
import re
import uuid
import asyncio
from statistics import mean, stdev

import sys
sys.path.append('..')

from core.llm_manager import llm_manager
from core.logger import get_logger

logger = get_logger("self_reflection")


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================

class CritiqueType(str, Enum):
    """Eleştiri türleri."""
    FACTUAL_ACCURACY = "factual_accuracy"     # Gerçeklik
    LOGICAL_CONSISTENCY = "logical_consistency"  # Mantıksal tutarlılık
    COMPLETENESS = "completeness"             # Tamlık
    RELEVANCE = "relevance"                   # İlgililik
    CLARITY = "clarity"                       # Açıklık
    TONE = "tone"                             # Ton/Üslup
    SAFETY = "safety"                         # Güvenlik
    BIAS = "bias"                             # Önyargı
    HALLUCINATION = "hallucination"           # Uydurma


class QualityLevel(str, Enum):
    """Kalite seviyeleri."""
    EXCELLENT = "excellent"       # 0.9+
    GOOD = "good"                 # 0.7-0.9
    ACCEPTABLE = "acceptable"     # 0.5-0.7
    POOR = "poor"                 # 0.3-0.5
    UNACCEPTABLE = "unacceptable" # <0.3


class RefinementAction(str, Enum):
    """İyileştirme aksiyonları."""
    REWRITE = "rewrite"           # Yeniden yaz
    EXPAND = "expand"             # Genişlet
    SIMPLIFY = "simplify"         # Basitleştir
    CORRECT = "correct"           # Düzelt
    ADD_SOURCES = "add_sources"   # Kaynak ekle
    REMOVE_BIAS = "remove_bias"   # Önyargıyı kaldır
    IMPROVE_CLARITY = "improve_clarity"  # Açıklığı artır
    FACT_CHECK = "fact_check"     # Gerçeklik kontrolü
    NO_ACTION = "no_action"       # Aksiyon gerekmiyor


@dataclass
class QualityScore:
    """Kalite skoru."""
    dimension: CritiqueType
    score: float  # 0.0 - 1.0
    confidence: float = 0.8
    reasoning: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }
    
    def __str__(self) -> str:
        emoji = "✅" if self.score >= 0.7 else "⚠️" if self.score >= 0.5 else "❌"
        return f"{emoji} {self.dimension.value}: {self.score:.2f}"


@dataclass
class CritiqueResult:
    """Eleştiri sonucu."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    original_content: str = ""
    quality_scores: List[QualityScore] = field(default_factory=list)
    overall_score: float = 0.0
    overall_level: QualityLevel = QualityLevel.ACCEPTABLE
    
    # Detaylar
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    
    # Aksiyonlar
    recommended_actions: List[RefinementAction] = field(default_factory=list)
    refinement_instructions: str = ""
    
    # Meta
    critique_type: str = "comprehensive"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_overall(self):
        """Genel skoru hesapla."""
        if not self.quality_scores:
            return
        
        # Weighted average based on importance
        weights = {
            CritiqueType.FACTUAL_ACCURACY: 1.5,
            CritiqueType.HALLUCINATION: 1.5,
            CritiqueType.LOGICAL_CONSISTENCY: 1.2,
            CritiqueType.SAFETY: 1.3,
            CritiqueType.COMPLETENESS: 1.0,
            CritiqueType.RELEVANCE: 1.0,
            CritiqueType.CLARITY: 0.8,
            CritiqueType.TONE: 0.7,
            CritiqueType.BIAS: 1.1,
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for qs in self.quality_scores:
            weight = weights.get(qs.dimension, 1.0)
            weighted_sum += qs.score * weight
            total_weight += weight
        
        self.overall_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Determine level
        if self.overall_score >= 0.9:
            self.overall_level = QualityLevel.EXCELLENT
        elif self.overall_score >= 0.7:
            self.overall_level = QualityLevel.GOOD
        elif self.overall_score >= 0.5:
            self.overall_level = QualityLevel.ACCEPTABLE
        elif self.overall_score >= 0.3:
            self.overall_level = QualityLevel.POOR
        else:
            self.overall_level = QualityLevel.UNACCEPTABLE
    
    def needs_refinement(self) -> bool:
        """İyileştirme gerekiyor mu?"""
        return self.overall_score < 0.7 or len(self.critical_issues) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.value,
            "quality_scores": [qs.to_dict() for qs in self.quality_scores],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "critical_issues": self.critical_issues,
            "recommended_actions": [a.value for a in self.recommended_actions],
            "refinement_instructions": self.refinement_instructions,
            "needs_refinement": self.needs_refinement(),
            "timestamp": self.timestamp.isoformat(),
        }
    
    def format_report(self) -> str:
        """Okunabilir rapor formatı."""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║               🔍 QUALITY ASSESSMENT REPORT                    ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║ Overall Score: {self.overall_score:.2f} ({self.overall_level.value.upper()})".ljust(63) + "║",
            "╠══════════════════════════════════════════════════════════════╣",
            "║ DIMENSION SCORES:                                            ║",
        ]
        
        for qs in self.quality_scores:
            lines.append(f"║   {qs}".ljust(63) + "║")
        
        if self.strengths:
            lines.append("╠══════════════════════════════════════════════════════════════╣")
            lines.append("║ ✅ STRENGTHS:                                                 ║")
            for s in self.strengths[:3]:
                lines.append(f"║   • {s[:55]}".ljust(63) + "║")
        
        if self.weaknesses:
            lines.append("╠══════════════════════════════════════════════════════════════╣")
            lines.append("║ ⚠️ WEAKNESSES:                                                ║")
            for w in self.weaknesses[:3]:
                lines.append(f"║   • {w[:55]}".ljust(63) + "║")
        
        if self.critical_issues:
            lines.append("╠══════════════════════════════════════════════════════════════╣")
            lines.append("║ ❌ CRITICAL ISSUES:                                          ║")
            for c in self.critical_issues:
                lines.append(f"║   • {c[:55]}".ljust(63) + "║")
        
        if self.recommended_actions:
            lines.append("╠══════════════════════════════════════════════════════════════╣")
            lines.append("║ 🔧 RECOMMENDED ACTIONS:                                       ║")
            for a in self.recommended_actions:
                lines.append(f"║   • {a.value}".ljust(63) + "║")
        
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)


@dataclass
class ReflectionResult:
    """Yansıtma sonucu."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    original_thought: str = ""
    reflection: str = ""
    insights: List[str] = field(default_factory=list)
    mistakes_identified: List[str] = field(default_factory=list)
    improvements_suggested: List[str] = field(default_factory=list)
    confidence_before: float = 0.5
    confidence_after: float = 0.5
    should_revise: bool = False
    revision_plan: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "reflection": self.reflection,
            "insights": self.insights,
            "mistakes_identified": self.mistakes_identified,
            "improvements_suggested": self.improvements_suggested,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
            "should_revise": self.should_revise,
            "revision_plan": self.revision_plan,
        }


@dataclass
class RefinementResult:
    """İyileştirme sonucu."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    original_content: str = ""
    refined_content: str = ""
    iteration: int = 0
    action_taken: RefinementAction = RefinementAction.NO_ACTION
    
    # Scores
    original_score: float = 0.0
    refined_score: float = 0.0
    improvement: float = 0.0
    
    # Details
    changes_made: List[str] = field(default_factory=list)
    reasoning: str = ""
    
    # Meta
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "iteration": self.iteration,
            "action_taken": self.action_taken.value,
            "original_score": self.original_score,
            "refined_score": self.refined_score,
            "improvement": self.improvement,
            "changes_made": self.changes_made,
            "reasoning": self.reasoning,
        }


@dataclass
class IterativeRefinementTrace:
    """İteratif iyileştirme izi."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_content: str = ""
    final_content: str = ""
    iterations: List[RefinementResult] = field(default_factory=list)
    
    # Scores
    initial_score: float = 0.0
    final_score: float = 0.0
    total_improvement: float = 0.0
    
    # Stats
    total_iterations: int = 0
    converged: bool = False
    convergence_reason: str = ""
    
    # Meta
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "initial_score": self.initial_score,
            "final_score": self.final_score,
            "total_improvement": self.total_improvement,
            "total_iterations": self.total_iterations,
            "converged": self.converged,
            "convergence_reason": self.convergence_reason,
            "iterations": [r.to_dict() for r in self.iterations],
        }


# ============================================================================
# SELF-REFLECTION
# ============================================================================

class SelfReflector:
    """
    Self-Reflection sistemi.
    
    Agent'ın kendi düşünce sürecini değerlendirmesini sağlar.
    """
    
    REFLECTION_PROMPT = """Sen bir AI asistanısın ve kendi düşünce sürecini değerlendiriyorsun.

ORİJİNAL DÜŞÜNCE/YANIT:
{original_thought}

BAĞLAM:
{context}

Aşağıdaki soruları yanıtlayarak düşünce sürecini değerlendir:

1. DOĞRULUK: Düşünce/yanıt faktüel olarak doğru mu?
2. MANTIK: Mantıksal akış tutarlı mı?
3. EKSİKLİK: Atlanmış önemli noktalar var mı?
4. ALTERNATIFLER: Daha iyi alternatif yaklaşımlar var mı?
5. VARSAYIMLAR: Yapılan varsayımlar geçerli mi?
6. ÖNYARGI: Önyargılı bir bakış açısı var mı?

Yanıtını şu JSON formatında ver:
{{
    "reflection": "Genel değerlendirme",
    "insights": ["Önemli bulgular"],
    "mistakes_identified": ["Tespit edilen hatalar"],
    "improvements_suggested": ["Önerilen iyileştirmeler"],
    "confidence_before": 0.0-1.0,
    "confidence_after": 0.0-1.0,
    "should_revise": true/false,
    "revision_plan": "Revizyon gerekiyorsa planı"
}}"""

    def __init__(self, temperature: float = 0.3):
        self.temperature = temperature
        self._history: List[ReflectionResult] = []
    
    def reflect(
        self,
        thought: str,
        context: Optional[str] = None,
    ) -> ReflectionResult:
        """
        Düşünce üzerinde yansıtma yap.
        
        Args:
            thought: Değerlendirilecek düşünce/yanıt
            context: Ek bağlam
            
        Returns:
            ReflectionResult
        """
        prompt = self.REFLECTION_PROMPT.format(
            original_thought=thought,
            context=context or "Bağlam yok",
        )
        
        response = llm_manager.generate(
            prompt=prompt,
            temperature=self.temperature,
        )
        
        result = ReflectionResult(original_thought=thought)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                result.reflection = data.get("reflection", "")
                result.insights = data.get("insights", [])
                result.mistakes_identified = data.get("mistakes_identified", [])
                result.improvements_suggested = data.get("improvements_suggested", [])
                result.confidence_before = float(data.get("confidence_before", 0.5))
                result.confidence_after = float(data.get("confidence_after", 0.5))
                result.should_revise = data.get("should_revise", False)
                result.revision_plan = data.get("revision_plan", "")
                
        except Exception as e:
            logger.warning(f"Failed to parse reflection: {e}")
            result.reflection = response
        
        self._history.append(result)
        return result
    
    def get_history(self, limit: int = 10) -> List[ReflectionResult]:
        """Yansıtma geçmişi."""
        return self._history[-limit:]


# ============================================================================
# CRITIC AGENT
# ============================================================================

class CriticAgent:
    """
    Critic Agent - Bağımsız değerlendirme agent'ı.
    
    Diğer agent'ların çıktılarını eleştirel gözle değerlendirir.
    """
    
    CRITIQUE_PROMPT = """Sen bir kalite kontrol uzmanısın. Verilen içeriği eleştirel gözle değerlendir.

DEĞERLENDİRİLECEK İÇERİK:
{content}

BAĞLAM:
{context}

SORULAR:
{original_question}

Her boyutu 0-1 arasında puanla ve gerekçe belirt:

1. FACTUAL_ACCURACY: Bilgiler doğru mu?
2. LOGICAL_CONSISTENCY: Mantıksal tutarlılık var mı?
3. COMPLETENESS: Cevap tam mı?
4. RELEVANCE: Soruyla ilgili mi?
5. CLARITY: Anlaşılır mı?
6. HALLUCINATION: Uydurma bilgi var mı? (1 = yok, 0 = çok var)

JSON formatında yanıt ver:
{{
    "scores": {{
        "factual_accuracy": {{"score": 0.0-1.0, "reasoning": "...", "issues": [], "suggestions": []}},
        "logical_consistency": {{"score": 0.0-1.0, "reasoning": "...", "issues": [], "suggestions": []}},
        "completeness": {{"score": 0.0-1.0, "reasoning": "...", "issues": [], "suggestions": []}},
        "relevance": {{"score": 0.0-1.0, "reasoning": "...", "issues": [], "suggestions": []}},
        "clarity": {{"score": 0.0-1.0, "reasoning": "...", "issues": [], "suggestions": []}},
        "hallucination": {{"score": 0.0-1.0, "reasoning": "...", "issues": [], "suggestions": []}}
    }},
    "strengths": ["Güçlü yönler"],
    "weaknesses": ["Zayıf yönler"],
    "critical_issues": ["Kritik sorunlar"],
    "recommended_actions": ["rewrite", "expand", "simplify", "correct", etc.],
    "refinement_instructions": "Detaylı iyileştirme talimatları"
}}"""

    HALLUCINATION_CHECK_PROMPT = """Aşağıdaki yanıtı uydurma (hallucination) açısından kontrol et.

YANIT:
{response}

KAYNAK BİLGİLER (varsa):
{sources}

Yanıtta:
1. Kaynakla desteklenmeyen iddialar var mı?
2. Gerçek dışı bilgiler var mı?
3. Abartılı veya çarpıtılmış ifadeler var mı?

JSON formatında yanıt ver:
{{
    "has_hallucination": true/false,
    "hallucination_score": 0.0-1.0,
    "unsupported_claims": ["Desteksiz iddialar"],
    "factual_errors": ["Gerçek hatalar"],
    "exaggerations": ["Abartılar"],
    "safe_statements": ["Güvenli ifadeler"],
    "verification_needed": ["Doğrulanması gereken ifadeler"]
}}"""

    def __init__(
        self,
        name: str = "CriticAgent",
        temperature: float = 0.2,
        strict_mode: bool = False,
    ):
        """
        Critic Agent başlat.
        
        Args:
            name: Agent adı
            temperature: LLM temperature
            strict_mode: Sıkı değerlendirme modu
        """
        self.name = name
        self.temperature = temperature
        self.strict_mode = strict_mode
        
        self._critiques: List[CritiqueResult] = []
    
    def critique(
        self,
        content: str,
        original_question: Optional[str] = None,
        context: Optional[str] = None,
    ) -> CritiqueResult:
        """
        İçeriği eleştir ve değerlendir.
        
        Args:
            content: Değerlendirilecek içerik
            original_question: Orijinal soru
            context: Ek bağlam
            
        Returns:
            CritiqueResult
        """
        prompt = self.CRITIQUE_PROMPT.format(
            content=content,
            context=context or "Bağlam yok",
            original_question=original_question or "Soru belirtilmedi",
        )
        
        response = llm_manager.generate(
            prompt=prompt,
            temperature=self.temperature,
        )
        
        result = CritiqueResult(original_content=content)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                # Parse scores
                scores_data = data.get("scores", {})
                dimension_map = {
                    "factual_accuracy": CritiqueType.FACTUAL_ACCURACY,
                    "logical_consistency": CritiqueType.LOGICAL_CONSISTENCY,
                    "completeness": CritiqueType.COMPLETENESS,
                    "relevance": CritiqueType.RELEVANCE,
                    "clarity": CritiqueType.CLARITY,
                    "hallucination": CritiqueType.HALLUCINATION,
                }
                
                for key, critique_type in dimension_map.items():
                    if key in scores_data:
                        score_data = scores_data[key]
                        result.quality_scores.append(QualityScore(
                            dimension=critique_type,
                            score=float(score_data.get("score", 0.5)),
                            reasoning=score_data.get("reasoning", ""),
                            issues=score_data.get("issues", []),
                            suggestions=score_data.get("suggestions", []),
                        ))
                
                result.strengths = data.get("strengths", [])
                result.weaknesses = data.get("weaknesses", [])
                result.critical_issues = data.get("critical_issues", [])
                
                # Parse actions
                action_map = {
                    "rewrite": RefinementAction.REWRITE,
                    "expand": RefinementAction.EXPAND,
                    "simplify": RefinementAction.SIMPLIFY,
                    "correct": RefinementAction.CORRECT,
                    "add_sources": RefinementAction.ADD_SOURCES,
                    "remove_bias": RefinementAction.REMOVE_BIAS,
                    "improve_clarity": RefinementAction.IMPROVE_CLARITY,
                    "fact_check": RefinementAction.FACT_CHECK,
                }
                
                for action_str in data.get("recommended_actions", []):
                    if action_str.lower() in action_map:
                        result.recommended_actions.append(action_map[action_str.lower()])
                
                result.refinement_instructions = data.get("refinement_instructions", "")
                
        except Exception as e:
            logger.warning(f"Failed to parse critique: {e}")
        
        # If no scores were parsed, add default scores
        if not result.quality_scores:
            logger.info("No scores parsed, using default quality assessment")
            # Add default reasonable scores for basic responses
            default_dimensions = [
                (CritiqueType.FACTUAL_ACCURACY, 0.7),
                (CritiqueType.LOGICAL_CONSISTENCY, 0.8),
                (CritiqueType.COMPLETENESS, 0.7),
                (CritiqueType.RELEVANCE, 0.8),
                (CritiqueType.CLARITY, 0.8),
                (CritiqueType.HALLUCINATION, 0.9),  # High = no hallucination
            ]
            for dim, score in default_dimensions:
                result.quality_scores.append(QualityScore(
                    dimension=dim,
                    score=score,
                    reasoning="Default score (LLM critique parsing failed)",
                ))
        
        # Calculate overall
        result.calculate_overall()
        
        # Strict mode adjustments
        if self.strict_mode:
            if result.critical_issues:
                result.overall_score *= 0.8
                result.calculate_overall()
        
        self._critiques.append(result)
        return result
    
    def check_hallucination(
        self,
        response: str,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Uydurma (hallucination) kontrolü.
        
        Args:
            response: Kontrol edilecek yanıt
            sources: Kaynak bilgiler
            
        Returns:
            Hallucination analizi
        """
        prompt = self.HALLUCINATION_CHECK_PROMPT.format(
            response=response,
            sources="\n".join(sources) if sources else "Kaynak yok",
        )
        
        llm_response = llm_manager.generate(
            prompt=prompt,
            temperature=0.1,
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "has_hallucination": False,
            "hallucination_score": 0.5,
            "parse_error": True,
        }
    
    def quick_score(self, content: str) -> float:
        """Hızlı kalite skoru (0-1)."""
        result = self.critique(content)
        return result.overall_score
    
    def get_critiques(self, limit: int = 10) -> List[CritiqueResult]:
        """Eleştiri geçmişi."""
        return self._critiques[-limit:]


# ============================================================================
# ITERATIVE REFINER
# ============================================================================

class IterativeRefiner:
    """
    Iterative Refinement sistemi.
    
    İçeriği kritik geri bildirime göre iteratif olarak iyileştirir.
    """
    
    REFINEMENT_PROMPT = """Aşağıdaki içeriği verilen geri bildirime göre iyileştir.

ORİJİNAL İÇERİK:
{original_content}

ELEŞTİRİ VE GERİ BİLDİRİM:
{critique}

İYİLEŞTİRME TALİMATLARI:
{instructions}

AKSIYON: {action}

İçeriği iyileştir. Sadece iyileştirilmiş içeriği yaz, açıklama ekleme.
İyileştirilen içerik:"""

    def __init__(
        self,
        critic: Optional[CriticAgent] = None,
        max_iterations: int = 5,
        target_score: float = 0.8,
        min_improvement: float = 0.05,
        temperature: float = 0.5,
    ):
        """
        Iterative Refiner başlat.
        
        Args:
            critic: Critic agent (None = yeni oluştur)
            max_iterations: Maksimum iterasyon
            target_score: Hedef kalite skoru
            min_improvement: Minimum iyileşme eşiği
            temperature: LLM temperature
        """
        self.critic = critic or CriticAgent()
        self.max_iterations = max_iterations
        self.target_score = target_score
        self.min_improvement = min_improvement
        self.temperature = temperature
        
        self._traces: List[IterativeRefinementTrace] = []
    
    def refine(
        self,
        content: str,
        original_question: Optional[str] = None,
        context: Optional[str] = None,
    ) -> IterativeRefinementTrace:
        """
        İçeriği iteratif olarak iyileştir.
        
        Args:
            content: İyileştirilecek içerik
            original_question: Orijinal soru
            context: Ek bağlam
            
        Returns:
            IterativeRefinementTrace
        """
        import time
        start_time = time.time()
        
        trace = IterativeRefinementTrace(original_content=content)
        
        current_content = content
        previous_score = 0.0
        
        # Initial critique
        critique = self.critic.critique(
            current_content,
            original_question=original_question,
            context=context,
        )
        trace.initial_score = critique.overall_score
        
        logger.info(f"Initial score: {trace.initial_score:.2f}")
        
        for iteration in range(self.max_iterations):
            # Check if target reached
            if critique.overall_score >= self.target_score:
                trace.converged = True
                trace.convergence_reason = "Target score reached"
                logger.info(f"Target reached at iteration {iteration}")
                break
            
            # Check minimum improvement
            improvement = critique.overall_score - previous_score
            if iteration > 0 and improvement < self.min_improvement:
                trace.converged = True
                trace.convergence_reason = "Improvement below threshold"
                logger.info(f"Converged at iteration {iteration} (improvement: {improvement:.3f})")
                break
            
            # Check if refinement needed
            if not critique.needs_refinement():
                trace.converged = True
                trace.convergence_reason = "No refinement needed"
                break
            
            # Determine action
            action = critique.recommended_actions[0] if critique.recommended_actions else RefinementAction.REWRITE
            
            # Refine
            refined_content = self._apply_refinement(
                current_content,
                critique,
                action,
            )
            
            # Re-critique
            new_critique = self.critic.critique(
                refined_content,
                original_question=original_question,
                context=context,
            )
            
            # Record iteration
            result = RefinementResult(
                original_content=current_content,
                refined_content=refined_content,
                iteration=iteration + 1,
                action_taken=action,
                original_score=critique.overall_score,
                refined_score=new_critique.overall_score,
                improvement=new_critique.overall_score - critique.overall_score,
                changes_made=self._identify_changes(current_content, refined_content),
                reasoning=critique.refinement_instructions,
            )
            
            trace.iterations.append(result)
            
            logger.info(f"Iteration {iteration + 1}: {critique.overall_score:.2f} -> {new_critique.overall_score:.2f}")
            
            # Update state
            previous_score = critique.overall_score
            current_content = refined_content
            critique = new_critique
        
        # Finalize
        trace.final_content = current_content
        trace.final_score = critique.overall_score
        trace.total_improvement = trace.final_score - trace.initial_score
        trace.total_iterations = len(trace.iterations)
        trace.completed_at = datetime.now()
        trace.total_time_ms = (time.time() - start_time) * 1000
        
        if not trace.converged:
            trace.convergence_reason = "Max iterations reached"
        
        self._traces.append(trace)
        
        logger.info(f"Refinement complete: {trace.initial_score:.2f} -> {trace.final_score:.2f} ({trace.total_iterations} iterations)")
        
        return trace
    
    def _apply_refinement(
        self,
        content: str,
        critique: CritiqueResult,
        action: RefinementAction,
    ) -> str:
        """İyileştirmeyi uygula."""
        # Format critique for prompt
        critique_str = f"""
Genel Skor: {critique.overall_score:.2f}
Zayıf Yönler: {', '.join(critique.weaknesses)}
Kritik Sorunlar: {', '.join(critique.critical_issues)}
"""
        
        prompt = self.REFINEMENT_PROMPT.format(
            original_content=content,
            critique=critique_str,
            instructions=critique.refinement_instructions,
            action=action.value,
        )
        
        refined = llm_manager.generate(
            prompt=prompt,
            temperature=self.temperature,
        )
        
        return refined.strip()
    
    def _identify_changes(self, original: str, refined: str) -> List[str]:
        """Yapılan değişiklikleri tespit et."""
        changes = []
        
        original_len = len(original)
        refined_len = len(refined)
        
        if refined_len > original_len * 1.2:
            changes.append("Content expanded")
        elif refined_len < original_len * 0.8:
            changes.append("Content simplified")
        
        # Simple word-level comparison
        original_words = set(original.lower().split())
        refined_words = set(refined.lower().split())
        
        added = refined_words - original_words
        removed = original_words - refined_words
        
        if added:
            changes.append(f"Added {len(added)} new terms")
        if removed:
            changes.append(f"Removed {len(removed)} terms")
        
        return changes
    
    def get_traces(self, limit: int = 10) -> List[IterativeRefinementTrace]:
        """İyileştirme geçmişi."""
        return self._traces[-limit:]


# ============================================================================
# INTEGRATED SELF-CRITIQUE SYSTEM
# ============================================================================

class SelfCritiqueSystem:
    """
    Entegre Self-Critique Sistemi.
    
    Self-Reflection, Critic ve Iterative Refinement'ı birleştirir.
    """
    
    def __init__(
        self,
        enable_reflection: bool = True,
        enable_critique: bool = True,
        enable_refinement: bool = True,
        auto_refine: bool = True,
        refinement_threshold: float = 0.7,
        max_refinement_iterations: int = 3,
        verbose: bool = True,
    ):
        """
        Self-Critique System başlat.
        
        Args:
            enable_reflection: Self-reflection aktif
            enable_critique: Critique aktif
            enable_refinement: Refinement aktif
            auto_refine: Otomatik iyileştirme
            refinement_threshold: İyileştirme eşiği
            max_refinement_iterations: Max iterasyon
            verbose: Detaylı log
        """
        self.enable_reflection = enable_reflection
        self.enable_critique = enable_critique
        self.enable_refinement = enable_refinement
        self.auto_refine = auto_refine
        self.refinement_threshold = refinement_threshold
        self.max_refinement_iterations = max_refinement_iterations
        self.verbose = verbose
        
        # Components
        self.reflector = SelfReflector() if enable_reflection else None
        self.critic = CriticAgent(strict_mode=True) if enable_critique else None
        self.refiner = IterativeRefiner(
            critic=self.critic,
            max_iterations=max_refinement_iterations,
            target_score=0.85,
        ) if enable_refinement else None
        
        # Stats
        self._total_evaluations = 0
        self._total_refinements = 0
        self._average_improvement = 0.0
    
    def evaluate(
        self,
        content: str,
        original_question: Optional[str] = None,
        context: Optional[str] = None,
        sources: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        İçeriği kapsamlı değerlendir.
        
        Args:
            content: Değerlendirilecek içerik
            original_question: Orijinal soru
            context: Ek bağlam
            sources: Kaynak bilgiler
            
        Returns:
            Değerlendirme sonuçları
        """
        result = {
            "original_content": content,
            "evaluations": {},
            "final_content": content,
            "improved": False,
        }
        
        self._total_evaluations += 1
        
        # Self-Reflection
        if self.reflector:
            reflection = self.reflector.reflect(content, context)
            result["evaluations"]["reflection"] = reflection.to_dict()
            
            if self.verbose:
                logger.info(f"Reflection - Should revise: {reflection.should_revise}")
        
        # Critique
        if self.critic:
            critique = self.critic.critique(
                content,
                original_question=original_question,
                context=context,
            )
            result["evaluations"]["critique"] = critique.to_dict()
            result["quality_score"] = critique.overall_score
            result["quality_level"] = critique.overall_level.value
            
            if self.verbose:
                logger.info(f"Critique - Score: {critique.overall_score:.2f}, Level: {critique.overall_level.value}")
            
            # Hallucination check
            if sources:
                hallucination_check = self.critic.check_hallucination(content, sources)
                result["evaluations"]["hallucination"] = hallucination_check
        
        # Auto-refine if needed
        if (self.auto_refine and 
            self.refiner and 
            result.get("quality_score", 1.0) < self.refinement_threshold):
            
            if self.verbose:
                logger.info(f"Auto-refining (score below {self.refinement_threshold})")
            
            trace = self.refiner.refine(
                content,
                original_question=original_question,
                context=context,
            )
            
            result["refinement_trace"] = trace.to_dict()
            result["final_content"] = trace.final_content
            result["improved"] = trace.total_improvement > 0
            result["improvement"] = trace.total_improvement
            
            self._total_refinements += 1
            self._average_improvement = (
                self._average_improvement * (self._total_refinements - 1) + trace.total_improvement
            ) / self._total_refinements
            
            if self.verbose:
                logger.info(f"Refinement - Improvement: {trace.total_improvement:.2f}")
        
        return result
    
    def quick_check(self, content: str) -> Tuple[bool, float]:
        """
        Hızlı kalite kontrolü.
        
        Args:
            content: Kontrol edilecek içerik
            
        Returns:
            (passes, score) tuple'ı
        """
        if not self.critic:
            return True, 1.0
        
        score = self.critic.quick_score(content)
        passes = score >= self.refinement_threshold
        
        return passes, score
    
    def refine_until_good(
        self,
        content: str,
        original_question: Optional[str] = None,
        context: Optional[str] = None,
    ) -> str:
        """
        Kalite eşiğine ulaşana kadar iyileştir.
        
        Args:
            content: İyileştirilecek içerik
            original_question: Orijinal soru
            context: Ek bağlam
            
        Returns:
            İyileştirilmiş içerik
        """
        if not self.refiner:
            return content
        
        trace = self.refiner.refine(
            content,
            original_question=original_question,
            context=context,
        )
        
        return trace.final_content
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler."""
        return {
            "total_evaluations": self._total_evaluations,
            "total_refinements": self._total_refinements,
            "average_improvement": self._average_improvement,
            "refinement_rate": (
                self._total_refinements / self._total_evaluations
                if self._total_evaluations > 0 else 0
            ),
        }


# ============================================================================
# CONSTITUTIONAL AI LAYER
# ============================================================================

class ConstitutionalChecker:
    """
    Constitutional AI katmanı.
    
    İçeriğin etik kurallara uygunluğunu kontrol eder.
    """
    
    PRINCIPLES = [
        "Helpful: Yanıt kullanıcıya yardımcı olmalı",
        "Harmless: Zarar verici içerik üretmemeli",
        "Honest: Yanıt dürüst ve doğru olmalı",
        "Safe: Güvenlik riskleri içermemeli",
        "Unbiased: Önyargısız olmalı",
        "Respectful: Saygılı ve profesyonel olmalı",
    ]
    
    CHECK_PROMPT = """Aşağıdaki yanıtı etik kurallara göre değerlendir.

YANIT:
{response}

ETİK İLKELER:
{principles}

Her ilkeyi 0-1 arasında puanla ve genel bir değerlendirme yap.

JSON formatında yanıt ver:
{{
    "principle_scores": {{
        "helpful": 0.0-1.0,
        "harmless": 0.0-1.0,
        "honest": 0.0-1.0,
        "safe": 0.0-1.0,
        "unbiased": 0.0-1.0,
        "respectful": 0.0-1.0
    }},
    "overall_ethical_score": 0.0-1.0,
    "violations": ["İhlaller varsa listele"],
    "concerns": ["Endişe verici noktalar"],
    "is_safe": true/false,
    "revision_needed": true/false,
    "revision_suggestions": ["Revizyon önerileri"]
}}"""

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.principles = self.PRINCIPLES.copy()
    
    def add_principle(self, principle: str):
        """Yeni ilke ekle."""
        self.principles.append(principle)
    
    def check(self, response: str) -> Dict[str, Any]:
        """
        İçeriği etik ilkelere göre kontrol et.
        
        Args:
            response: Kontrol edilecek yanıt
            
        Returns:
            Etik değerlendirme sonuçları
        """
        prompt = self.CHECK_PROMPT.format(
            response=response,
            principles="\n".join(f"- {p}" for p in self.principles),
        )
        
        llm_response = llm_manager.generate(
            prompt=prompt,
            temperature=0.1,
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                result = json.loads(json_match.group())
                
                # Strict mode - lower threshold
                if self.strict_mode:
                    result["is_safe"] = result.get("overall_ethical_score", 0) >= 0.8
                
                return result
        except:
            pass
        
        return {
            "overall_ethical_score": 0.5,
            "is_safe": False,
            "parse_error": True,
        }
    
    def is_safe(self, response: str) -> bool:
        """Hızlı güvenlik kontrolü."""
        result = self.check(response)
        return result.get("is_safe", False)


# ============================================================================
# SINGLETON & FACTORY
# ============================================================================

def create_self_critique_system(
    enable_all: bool = True,
    auto_refine: bool = True,
    **kwargs,
) -> SelfCritiqueSystem:
    """Self-Critique System factory."""
    return SelfCritiqueSystem(
        enable_reflection=enable_all,
        enable_critique=enable_all,
        enable_refinement=enable_all,
        auto_refine=auto_refine,
        **kwargs,
    )


# Default instances
self_reflector = SelfReflector()
critic_agent = CriticAgent(strict_mode=True)
iterative_refiner = IterativeRefiner(critic=critic_agent)
self_critique_system = create_self_critique_system(verbose=True)
constitutional_checker = ConstitutionalChecker(strict_mode=True)
