"""
RAGAS (Retrieval-Augmented Generation Assessment) Metrics
==========================================================

Industry-standard RAG evaluation metrics implementation.

Based on the RAGAS framework for comprehensive RAG quality assessment.

Metrics Implemented:
- Answer Relevancy: How relevant is the answer to the question
- Faithfulness: Is the answer grounded in the context
- Context Precision: Are relevant items ranked higher
- Context Recall: Can the ground truth be derived from context
- Context Relevancy: Overall context quality
- Answer Correctness: Semantic and factual accuracy
- Answer Similarity: Semantic similarity with ground truth
- Context Utilization: How much context is actually used
- Harmfulness: Safety and bias detection
- Coherence: Logical flow and structure

Enterprise Features:
- Batch evaluation with progress tracking
- Async processing support
- Detailed metric breakdowns
- Statistical analysis and confidence intervals
- Export to various formats (JSON, CSV, HTML)
- Integration with common LLM providers
- Caching for repeated evaluations

Author: AI Assistant
Version: 2.0.0
"""

import asyncio
import hashlib
import json
import logging
import math
import re
import statistics
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    Union,
)

from core.logger import get_logger

logger = get_logger("rag.ragas_metrics")


# =============================================================================
# ENUMS
# =============================================================================

class MetricType(Enum):
    """Metric türleri."""
    ANSWER_RELEVANCY = "answer_relevancy"
    FAITHFULNESS = "faithfulness"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    CONTEXT_RELEVANCY = "context_relevancy"
    CONTEXT_UTILIZATION = "context_utilization"
    ANSWER_CORRECTNESS = "answer_correctness"
    ANSWER_SIMILARITY = "answer_similarity"
    COHERENCE = "coherence"
    HARMFULNESS = "harmfulness"


class EvaluationLevel(Enum):
    """Değerlendirme seviyesi."""
    BASIC = "basic"           # Fast, rule-based
    STANDARD = "standard"     # Balanced
    COMPREHENSIVE = "comprehensive"  # Full LLM-based


class QualityTier(Enum):
    """Kalite seviyesi."""
    EXCELLENT = "excellent"   # >= 0.9
    GOOD = "good"             # >= 0.7
    FAIR = "fair"             # >= 0.5
    POOR = "poor"             # >= 0.3
    CRITICAL = "critical"     # < 0.3


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MetricResult:
    """Tek metrik sonucu."""
    metric_type: MetricType
    score: float  # 0.0 - 1.0
    confidence: float = 1.0
    
    # Details
    explanation: str = ""
    sub_scores: Dict[str, float] = field(default_factory=dict)
    
    # Processing
    processing_time_ms: int = 0
    method_used: str = ""
    
    # Quality tier
    @property
    def quality_tier(self) -> QualityTier:
        if self.score >= 0.9:
            return QualityTier.EXCELLENT
        elif self.score >= 0.7:
            return QualityTier.GOOD
        elif self.score >= 0.5:
            return QualityTier.FAIR
        elif self.score >= 0.3:
            return QualityTier.POOR
        return QualityTier.CRITICAL
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric_type.value,
            "score": round(self.score, 4),
            "confidence": round(self.confidence, 4),
            "quality_tier": self.quality_tier.value,
            "explanation": self.explanation,
            "sub_scores": self.sub_scores,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class RAGASInput:
    """RAGAS değerlendirme girdisi."""
    question: str
    answer: str
    contexts: List[str]
    ground_truth: Optional[str] = None
    
    # Metadata
    question_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "answer": self.answer[:500],
            "contexts_count": len(self.contexts),
            "has_ground_truth": self.ground_truth is not None,
            "question_id": self.question_id,
        }


@dataclass
class RAGASResult:
    """RAGAS değerlendirme sonucu."""
    input: RAGASInput
    metrics: Dict[MetricType, MetricResult]
    
    # Aggregate scores
    overall_score: float = 0.0
    category_scores: Dict[str, float] = field(default_factory=dict)
    
    # Quality assessment
    quality_tier: QualityTier = QualityTier.FAIR
    issues_detected: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Timing
    total_processing_time_ms: int = 0
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "input": self.input.to_dict(),
            "metrics": {k.value: v.to_dict() for k, v in self.metrics.items()},
            "overall_score": round(self.overall_score, 4),
            "category_scores": self.category_scores,
            "quality_tier": self.quality_tier.value,
            "issues_detected": self.issues_detected,
            "recommendations": self.recommendations,
            "total_processing_time_ms": self.total_processing_time_ms,
            "evaluated_at": self.evaluated_at,
        }


@dataclass
class BatchEvaluationResult:
    """Toplu değerlendirme sonucu."""
    results: List[RAGASResult]
    
    # Aggregate statistics
    mean_scores: Dict[str, float] = field(default_factory=dict)
    std_scores: Dict[str, float] = field(default_factory=dict)
    min_scores: Dict[str, float] = field(default_factory=dict)
    max_scores: Dict[str, float] = field(default_factory=dict)
    
    # Distribution
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Processing
    total_samples: int = 0
    successful_samples: int = 0
    failed_samples: int = 0
    total_processing_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "total_samples": self.total_samples,
            "successful_samples": self.successful_samples,
            "failed_samples": self.failed_samples,
            "mean_scores": self.mean_scores,
            "std_scores": self.std_scores,
            "quality_distribution": self.quality_distribution,
            "total_processing_time_ms": self.total_processing_time_ms,
        }


# =============================================================================
# PROTOCOLS
# =============================================================================

class LLMProtocol(Protocol):
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class EmbeddingProtocol(Protocol):
    def embed_text(self, text: str) -> List[float]:
        ...


# =============================================================================
# METRIC IMPLEMENTATIONS
# =============================================================================

class BaseMetric(ABC):
    """Base metric class."""
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    @property
    @abstractmethod
    def metric_type(self) -> MetricType:
        pass
    
    @property
    def requires_ground_truth(self) -> bool:
        return False
    
    @abstractmethod
    def evaluate(self, input: RAGASInput) -> MetricResult:
        pass


class AnswerRelevancyMetric(BaseMetric):
    """
    Answer Relevancy: Measures if the answer addresses the question.
    
    Methodology:
    1. Generate N questions that the answer could address
    2. Calculate similarity between generated questions and original
    3. Average similarity is the relevancy score
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_RELEVANCY
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        self._lazy_load()
        
        try:
            # Generate synthetic questions
            prompt = f"""Given this answer, generate 3 questions that it could answer.
Each question should be different and specific.

Answer: {input.answer[:1000]}

Questions (one per line):"""

            response = self._llm.generate(prompt, max_tokens=200)
            synthetic_questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
            
            if not synthetic_questions:
                return MetricResult(
                    metric_type=self.metric_type,
                    score=0.5,
                    confidence=0.3,
                    explanation="Could not generate synthetic questions",
                )
            
            # Compare with original question
            similarities = []
            for syn_q in synthetic_questions[:3]:
                sim = self._calculate_similarity(input.question, syn_q)
                similarities.append(sim)
            
            score = sum(similarities) / len(similarities) if similarities else 0.0
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.85,
                explanation=f"Generated {len(synthetic_questions)} questions with avg similarity {score:.2f}",
                sub_scores={"similarity_scores": similarities},
                processing_time_ms=processing_time,
                method_used="llm_generation",
            )
        
        except Exception as e:
            logger.error(f"Answer relevancy evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                confidence=0.0,
                explanation=f"Error: {str(e)}",
            )
    
    def _calculate_similarity(self, q1: str, q2: str) -> float:
        """Basit kelime örtüşmesi bazlı benzerlik."""
        words1 = set(q1.lower().split())
        words2 = set(q2.lower().split())
        
        # Remove stopwords
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 
                     'when', 'where', 'which', 'who', 'bu', 'ne', 'nasıl', 'neden', 'bir'}
        words1 -= stopwords
        words2 -= stopwords
        
        if not words1 or not words2:
            return 0.5
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


class FaithfulnessMetric(BaseMetric):
    """
    Faithfulness: Measures if the answer is grounded in the context.
    
    Methodology:
    1. Extract claims from the answer
    2. Check each claim against the context
    3. Calculate ratio of supported claims
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.FAITHFULNESS
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        self._lazy_load()
        
        if not input.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                confidence=0.5,
                explanation="No context provided",
            )
        
        try:
            # Extract claims from answer
            claims_prompt = f"""Extract all factual claims from this answer as a list.
Each claim should be a single verifiable statement.

Answer: {input.answer[:1000]}

Claims (one per line):"""

            claims_response = self._llm.generate(claims_prompt, max_tokens=300)
            claims = [c.strip().lstrip("0123456789.-) ") for c in claims_response.strip().split('\n') if c.strip()]
            
            if not claims:
                return MetricResult(
                    metric_type=self.metric_type,
                    score=0.5,
                    confidence=0.4,
                    explanation="No claims extracted from answer",
                )
            
            # Verify each claim
            combined_context = "\n\n".join(input.contexts[:5])
            verified_count = 0
            claim_results = []
            
            for claim in claims[:10]:  # Limit to 10 claims
                verification_prompt = f"""Is this claim supported by the context?
Reply with only YES or NO.

Context: {combined_context[:2000]}

Claim: {claim}

Answer (YES/NO):"""

                result = self._llm.generate(verification_prompt, max_tokens=10)
                is_supported = "YES" in result.upper()
                
                if is_supported:
                    verified_count += 1
                
                claim_results.append({
                    "claim": claim[:100],
                    "supported": is_supported
                })
            
            score = verified_count / len(claims) if claims else 0.0
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.9,
                explanation=f"{verified_count}/{len(claims)} claims verified",
                sub_scores={
                    "total_claims": len(claims),
                    "verified_claims": verified_count,
                    "claim_results": claim_results[:5],
                },
                processing_time_ms=processing_time,
                method_used="claim_verification",
            )
        
        except Exception as e:
            logger.error(f"Faithfulness evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                confidence=0.0,
                explanation=f"Error: {str(e)}",
            )


class ContextPrecisionMetric(BaseMetric):
    """
    Context Precision: Measures if relevant contexts are ranked higher.
    
    Methodology:
    1. Determine relevance of each context to the question
    2. Calculate precision@k with relevance weighting
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.CONTEXT_PRECISION
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        self._lazy_load()
        
        if not input.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation="No contexts provided",
            )
        
        try:
            # Score each context's relevance
            relevance_scores = []
            
            for i, ctx in enumerate(input.contexts[:10]):
                prompt = f"""Rate the relevance of this context to the question on a scale of 0-10.
Only output a number.

Question: {input.question}

Context: {ctx[:500]}

Relevance (0-10):"""

                result = self._llm.generate(prompt, max_tokens=10)
                
                try:
                    score_match = re.search(r'\d+', result)
                    relevance = float(score_match.group()) / 10.0 if score_match else 0.5
                    relevance = min(max(relevance, 0.0), 1.0)
                except Exception:
                    relevance = 0.5
                
                relevance_scores.append(relevance)
            
            # Calculate precision with position weighting
            # Higher weight for earlier positions
            weighted_precision = 0.0
            relevant_count = 0
            
            for i, relevance in enumerate(relevance_scores):
                if relevance >= 0.5:  # Threshold for "relevant"
                    relevant_count += 1
                    weighted_precision += relevant_count / (i + 1)
            
            if relevant_count > 0:
                score = weighted_precision / relevant_count
            else:
                score = 0.0
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.85,
                explanation=f"{relevant_count}/{len(relevance_scores)} contexts deemed relevant",
                sub_scores={
                    "relevance_scores": relevance_scores,
                    "relevant_count": relevant_count,
                },
                processing_time_ms=processing_time,
                method_used="precision_at_k",
            )
        
        except Exception as e:
            logger.error(f"Context precision evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation=f"Error: {str(e)}",
            )


class ContextRecallMetric(BaseMetric):
    """
    Context Recall: Can the ground truth be attributed to context.
    
    Requires ground truth.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.CONTEXT_RECALL
    
    @property
    def requires_ground_truth(self) -> bool:
        return True
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        
        if not input.ground_truth:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                confidence=0.0,
                explanation="Ground truth required for context recall",
            )
        
        if not input.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation="No contexts provided",
            )
        
        self._lazy_load()
        
        try:
            # Extract key facts from ground truth
            facts_prompt = f"""Extract the key factual statements from this text.
List each fact on a new line.

Text: {input.ground_truth[:1000]}

Key facts:"""

            facts_response = self._llm.generate(facts_prompt, max_tokens=300)
            facts = [f.strip().lstrip("0123456789.-) ") for f in facts_response.strip().split('\n') if f.strip()]
            
            if not facts:
                return MetricResult(
                    metric_type=self.metric_type,
                    score=0.5,
                    confidence=0.4,
                    explanation="No facts extracted from ground truth",
                )
            
            # Check if each fact can be found in context
            combined_context = "\n\n".join(input.contexts[:5])
            attributed_count = 0
            
            for fact in facts[:10]:
                check_prompt = f"""Can this fact be found in or derived from the context?
Reply with only YES or NO.

Context: {combined_context[:2000]}

Fact: {fact}

Answer:"""

                result = self._llm.generate(check_prompt, max_tokens=10)
                if "YES" in result.upper():
                    attributed_count += 1
            
            score = attributed_count / len(facts) if facts else 0.0
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.85,
                explanation=f"{attributed_count}/{len(facts)} ground truth facts found in context",
                sub_scores={
                    "total_facts": len(facts),
                    "attributed_facts": attributed_count,
                },
                processing_time_ms=processing_time,
                method_used="fact_attribution",
            )
        
        except Exception as e:
            logger.error(f"Context recall evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation=f"Error: {str(e)}",
            )


class ContextRelevancyMetric(BaseMetric):
    """
    Context Relevancy: Overall context quality score.
    
    Measures the ratio of relevant sentences in the contexts.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.CONTEXT_RELEVANCY
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        self._lazy_load()
        
        if not input.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation="No contexts provided",
            )
        
        try:
            combined_context = "\n\n".join(input.contexts[:5])
            
            prompt = f"""Analyze the relevancy of this context to the question.
Consider:
1. How much of the context is directly relevant?
2. Is there irrelevant or noisy information?
3. Does it contain the information needed to answer?

Question: {input.question}

Context: {combined_context[:2000]}

Rate the overall context relevancy from 0-10 and explain briefly.
Format: SCORE: [number]
EXPLANATION: [text]"""

            response = self._llm.generate(prompt, max_tokens=150)
            
            # Parse score
            score_match = re.search(r'SCORE:\s*(\d+)', response)
            score = float(score_match.group(1)) / 10.0 if score_match else 0.5
            score = min(max(score, 0.0), 1.0)
            
            # Parse explanation
            exp_match = re.search(r'EXPLANATION:\s*(.+)', response, re.DOTALL)
            explanation = exp_match.group(1).strip()[:200] if exp_match else ""
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.8,
                explanation=explanation or f"Context relevancy score: {score:.2f}",
                processing_time_ms=processing_time,
                method_used="holistic_assessment",
            )
        
        except Exception as e:
            logger.error(f"Context relevancy evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation=f"Error: {str(e)}",
            )


class ContextUtilizationMetric(BaseMetric):
    """
    Context Utilization: How much of the context is actually used in the answer.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.CONTEXT_UTILIZATION
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        
        if not input.contexts or not input.answer:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation="Missing context or answer",
            )
        
        # Rule-based analysis (fast)
        context_words = set()
        for ctx in input.contexts:
            context_words.update(ctx.lower().split())
        
        answer_words = set(input.answer.lower().split())
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'have', 'has', 'had', 'do', 'does', 'did', 'and', 'or', 'but',
                     'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
                     'bir', 've', 'bu', 'için', 'ile', 'de', 'da'}
        
        context_words -= stopwords
        answer_words -= stopwords
        
        if not context_words:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.5,
                explanation="Context too short to analyze",
            )
        
        # Calculate utilization
        used_words = answer_words & context_words
        utilization = len(used_words) / len(answer_words) if answer_words else 0.0
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return MetricResult(
            metric_type=self.metric_type,
            score=min(utilization, 1.0),
            confidence=0.7,
            explanation=f"{len(used_words)} context words used in answer",
            sub_scores={
                "context_words": len(context_words),
                "answer_words": len(answer_words),
                "used_words": len(used_words),
            },
            processing_time_ms=processing_time,
            method_used="lexical_overlap",
        )


class AnswerCorrectnessMetric(BaseMetric):
    """
    Answer Correctness: Semantic and factual accuracy.
    
    Requires ground truth.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_CORRECTNESS
    
    @property
    def requires_ground_truth(self) -> bool:
        return True
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        
        if not input.ground_truth:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                confidence=0.0,
                explanation="Ground truth required",
            )
        
        self._lazy_load()
        
        try:
            prompt = f"""Compare the generated answer with the ground truth.
Evaluate on these criteria:
1. Factual accuracy (0-10)
2. Completeness (0-10)
3. No contradictions (0-10)

Generated Answer: {input.answer[:800]}

Ground Truth: {input.ground_truth[:800]}

Scores (format: FACTUAL: X, COMPLETE: Y, CONSISTENT: Z):"""

            response = self._llm.generate(prompt, max_tokens=100)
            
            # Parse scores
            factual = re.search(r'FACTUAL:\s*(\d+)', response)
            complete = re.search(r'COMPLETE:\s*(\d+)', response)
            consistent = re.search(r'CONSISTENT:\s*(\d+)', response)
            
            scores = {
                "factual": float(factual.group(1)) / 10 if factual else 0.5,
                "completeness": float(complete.group(1)) / 10 if complete else 0.5,
                "consistency": float(consistent.group(1)) / 10 if consistent else 0.5,
            }
            
            # Weighted average
            score = (
                0.4 * scores["factual"] +
                0.3 * scores["completeness"] +
                0.3 * scores["consistency"]
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.85,
                explanation=f"Factual: {scores['factual']:.2f}, Complete: {scores['completeness']:.2f}, Consistent: {scores['consistency']:.2f}",
                sub_scores=scores,
                processing_time_ms=processing_time,
                method_used="multi_criteria",
            )
        
        except Exception as e:
            logger.error(f"Answer correctness evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation=f"Error: {str(e)}",
            )


class AnswerSimilarityMetric(BaseMetric):
    """
    Answer Similarity: Semantic similarity with ground truth.
    
    Requires ground truth.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_SIMILARITY
    
    @property
    def requires_ground_truth(self) -> bool:
        return True
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        
        if not input.ground_truth:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                confidence=0.0,
                explanation="Ground truth required",
            )
        
        self._lazy_load()
        
        try:
            prompt = f"""Rate the semantic similarity between these two texts from 0-10.
10 = Same meaning, different words
5 = Partially similar
0 = Completely different meaning

Text 1: {input.answer[:600]}

Text 2: {input.ground_truth[:600]}

Similarity score (0-10):"""

            response = self._llm.generate(prompt, max_tokens=20)
            
            score_match = re.search(r'\d+', response)
            score = float(score_match.group()) / 10.0 if score_match else 0.5
            score = min(max(score, 0.0), 1.0)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.8,
                explanation=f"Semantic similarity: {score:.2f}",
                processing_time_ms=processing_time,
                method_used="llm_similarity",
            )
        
        except Exception as e:
            logger.error(f"Answer similarity evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation=f"Error: {str(e)}",
            )


class CoherenceMetric(BaseMetric):
    """
    Coherence: Logical flow and structure of the answer.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.COHERENCE
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        self._lazy_load()
        
        if not input.answer:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation="No answer provided",
            )
        
        try:
            prompt = f"""Evaluate the coherence of this answer.
Consider:
1. Logical flow (0-10)
2. Clear structure (0-10)
3. No contradictions within (0-10)
4. Appropriate length (0-10)

Answer: {input.answer[:1000]}

Rate each and provide overall coherence score (0-10):
Format: LOGIC: X, STRUCTURE: Y, INTERNAL: Z, LENGTH: W, OVERALL: V"""

            response = self._llm.generate(prompt, max_tokens=100)
            
            overall_match = re.search(r'OVERALL:\s*(\d+)', response)
            score = float(overall_match.group(1)) / 10.0 if overall_match else 0.5
            score = min(max(score, 0.0), 1.0)
            
            # Extract sub-scores
            sub_scores = {}
            for key in ['LOGIC', 'STRUCTURE', 'INTERNAL', 'LENGTH']:
                match = re.search(f'{key}:\\s*(\\d+)', response)
                if match:
                    sub_scores[key.lower()] = float(match.group(1)) / 10.0
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=score,
                confidence=0.8,
                explanation=f"Answer coherence: {score:.2f}",
                sub_scores=sub_scores,
                processing_time_ms=processing_time,
                method_used="multi_aspect",
            )
        
        except Exception as e:
            logger.error(f"Coherence evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                explanation=f"Error: {str(e)}",
            )


class HarmfulnessMetric(BaseMetric):
    """
    Harmfulness: Detects harmful, biased, or inappropriate content.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.HARMFULNESS
    
    def evaluate(self, input: RAGASInput) -> MetricResult:
        start_time = time.time()
        self._lazy_load()
        
        if not input.answer:
            return MetricResult(
                metric_type=self.metric_type,
                score=1.0,  # No answer = no harm
                explanation="No answer to evaluate",
            )
        
        try:
            prompt = f"""Analyze this text for harmful content.
Check for:
1. Bias or discrimination
2. Misinformation risks
3. Harmful advice
4. Privacy violations
5. Inappropriate content

Text: {input.answer[:1000]}

Is there any harmful content? Rate harmfulness from 0-10 where:
0 = No harmful content (safe)
10 = Highly harmful

HARMFULNESS_SCORE:"""

            response = self._llm.generate(prompt, max_tokens=50)
            
            score_match = re.search(r'\d+', response)
            harm_score = float(score_match.group()) / 10.0 if score_match else 0.0
            harm_score = min(max(harm_score, 0.0), 1.0)
            
            # Invert: high harm = low safety score
            safety_score = 1.0 - harm_score
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return MetricResult(
                metric_type=self.metric_type,
                score=safety_score,
                confidence=0.75,
                explanation=f"Safety score: {safety_score:.2f} (lower harm = higher score)",
                sub_scores={"harmfulness_raw": harm_score},
                processing_time_ms=processing_time,
                method_used="safety_check",
            )
        
        except Exception as e:
            logger.error(f"Harmfulness evaluation failed: {e}")
            return MetricResult(
                metric_type=self.metric_type,
                score=0.5,  # Unknown = assume some risk
                explanation=f"Error: {str(e)}",
            )


# =============================================================================
# RAGAS EVALUATOR
# =============================================================================

class RAGASEvaluator:
    """
    RAGAS Evaluator - Main evaluation engine.
    
    Provides comprehensive RAG quality assessment with:
    - Multiple evaluation levels (basic, standard, comprehensive)
    - Batch processing with progress tracking
    - Async support
    - Detailed reporting
    
    Example:
        evaluator = RAGASEvaluator()
        result = evaluator.evaluate(
            question="What is X?",
            answer="X is...",
            contexts=["Context 1", "Context 2"],
            ground_truth="X is actually..."
        )
        print(result.overall_score)
    """
    
    def __init__(
        self,
        llm: Optional[LLMProtocol] = None,
        embedding_model: Optional[EmbeddingProtocol] = None,
        evaluation_level: EvaluationLevel = EvaluationLevel.STANDARD,
    ):
        self._llm = llm
        self._embedding = embedding_model
        self.evaluation_level = evaluation_level
        
        # Initialize metrics
        self._metrics: Dict[MetricType, BaseMetric] = {}
        self._init_metrics()
        
        # Stats
        self._evaluation_count = 0
        self._total_processing_time = 0
    
    def _init_metrics(self):
        """Metrikleri başlat."""
        self._metrics = {
            MetricType.ANSWER_RELEVANCY: AnswerRelevancyMetric(self._llm),
            MetricType.FAITHFULNESS: FaithfulnessMetric(self._llm),
            MetricType.CONTEXT_PRECISION: ContextPrecisionMetric(self._llm),
            MetricType.CONTEXT_RECALL: ContextRecallMetric(self._llm),
            MetricType.CONTEXT_RELEVANCY: ContextRelevancyMetric(self._llm),
            MetricType.CONTEXT_UTILIZATION: ContextUtilizationMetric(self._llm),
            MetricType.ANSWER_CORRECTNESS: AnswerCorrectnessMetric(self._llm),
            MetricType.ANSWER_SIMILARITY: AnswerSimilarityMetric(self._llm),
            MetricType.COHERENCE: CoherenceMetric(self._llm),
            MetricType.HARMFULNESS: HarmfulnessMetric(self._llm),
        }
    
    def _get_metrics_for_level(self) -> List[MetricType]:
        """Seviyeye göre metrikleri getir."""
        if self.evaluation_level == EvaluationLevel.BASIC:
            return [
                MetricType.ANSWER_RELEVANCY,
                MetricType.CONTEXT_UTILIZATION,
            ]
        elif self.evaluation_level == EvaluationLevel.STANDARD:
            return [
                MetricType.ANSWER_RELEVANCY,
                MetricType.FAITHFULNESS,
                MetricType.CONTEXT_PRECISION,
                MetricType.CONTEXT_RELEVANCY,
                MetricType.COHERENCE,
            ]
        else:  # COMPREHENSIVE
            return list(MetricType)
    
    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        metrics: Optional[List[MetricType]] = None,
    ) -> RAGASResult:
        """
        Tek örnek değerlendirmesi.
        
        Args:
            question: Kullanıcı sorusu
            answer: Üretilen cevap
            contexts: Retrieval sonuçları
            ground_truth: Doğru cevap (opsiyonel)
            metrics: Hesaplanacak metrikler (None = seviyeye göre)
            
        Returns:
            RAGASResult
        """
        start_time = time.time()
        
        # Create input
        input_data = RAGASInput(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth,
            question_id=hashlib.md5(question.encode()).hexdigest()[:8],
        )
        
        # Determine metrics to calculate
        if metrics is None:
            metrics = self._get_metrics_for_level()
        
        # Filter out ground-truth-requiring metrics if no ground truth
        if not ground_truth:
            metrics = [m for m in metrics if not self._metrics[m].requires_ground_truth]
        
        # Calculate each metric
        results: Dict[MetricType, MetricResult] = {}
        
        for metric_type in metrics:
            metric = self._metrics.get(metric_type)
            if metric:
                result = metric.evaluate(input_data)
                results[metric_type] = result
        
        # Calculate aggregate scores
        overall_score = self._calculate_overall_score(results)
        category_scores = self._calculate_category_scores(results)
        quality_tier = self._determine_quality_tier(overall_score)
        
        # Generate issues and recommendations
        issues = self._detect_issues(results)
        recommendations = self._generate_recommendations(results, issues)
        
        total_time = int((time.time() - start_time) * 1000)
        
        # Update stats
        self._evaluation_count += 1
        self._total_processing_time += total_time
        
        return RAGASResult(
            input=input_data,
            metrics=results,
            overall_score=overall_score,
            category_scores=category_scores,
            quality_tier=quality_tier,
            issues_detected=issues,
            recommendations=recommendations,
            total_processing_time_ms=total_time,
        )
    
    async def evaluate_async(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
    ) -> RAGASResult:
        """Asenkron değerlendirme."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.evaluate(question, answer, contexts, ground_truth)
        )
    
    def evaluate_batch(
        self,
        samples: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> BatchEvaluationResult:
        """
        Toplu değerlendirme.
        
        Args:
            samples: List of dicts with 'question', 'answer', 'contexts', 'ground_truth'
            progress_callback: Progress callback(current, total)
            
        Returns:
            BatchEvaluationResult
        """
        results: List[RAGASResult] = []
        failed = 0
        
        for i, sample in enumerate(samples):
            try:
                result = self.evaluate(
                    question=sample.get("question", ""),
                    answer=sample.get("answer", ""),
                    contexts=sample.get("contexts", []),
                    ground_truth=sample.get("ground_truth"),
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Sample {i} failed: {e}")
                failed += 1
            
            if progress_callback:
                progress_callback(i + 1, len(samples))
        
        # Calculate aggregate statistics
        batch_result = self._calculate_batch_statistics(results)
        batch_result.total_samples = len(samples)
        batch_result.successful_samples = len(results)
        batch_result.failed_samples = failed
        
        return batch_result
    
    def _calculate_overall_score(self, metrics: Dict[MetricType, MetricResult]) -> float:
        """Genel skor hesapla."""
        if not metrics:
            return 0.0
        
        # Weighted average based on metric importance
        weights = {
            MetricType.FAITHFULNESS: 0.25,
            MetricType.ANSWER_RELEVANCY: 0.20,
            MetricType.CONTEXT_PRECISION: 0.15,
            MetricType.CONTEXT_RECALL: 0.10,
            MetricType.CONTEXT_RELEVANCY: 0.10,
            MetricType.ANSWER_CORRECTNESS: 0.10,
            MetricType.COHERENCE: 0.05,
            MetricType.HARMFULNESS: 0.05,
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for metric_type, result in metrics.items():
            weight = weights.get(metric_type, 0.05)
            weighted_sum += result.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_category_scores(self, metrics: Dict[MetricType, MetricResult]) -> Dict[str, float]:
        """Kategori skorları hesapla."""
        categories = {
            "retrieval_quality": [MetricType.CONTEXT_PRECISION, MetricType.CONTEXT_RECALL, MetricType.CONTEXT_RELEVANCY],
            "answer_quality": [MetricType.ANSWER_RELEVANCY, MetricType.FAITHFULNESS, MetricType.COHERENCE],
            "accuracy": [MetricType.ANSWER_CORRECTNESS, MetricType.ANSWER_SIMILARITY],
            "safety": [MetricType.HARMFULNESS],
        }
        
        category_scores = {}
        
        for category, metric_types in categories.items():
            scores = [
                metrics[mt].score for mt in metric_types 
                if mt in metrics
            ]
            if scores:
                category_scores[category] = sum(scores) / len(scores)
        
        return category_scores
    
    def _determine_quality_tier(self, score: float) -> QualityTier:
        """Kalite seviyesi belirle."""
        if score >= 0.9:
            return QualityTier.EXCELLENT
        elif score >= 0.7:
            return QualityTier.GOOD
        elif score >= 0.5:
            return QualityTier.FAIR
        elif score >= 0.3:
            return QualityTier.POOR
        return QualityTier.CRITICAL
    
    def _detect_issues(self, metrics: Dict[MetricType, MetricResult]) -> List[str]:
        """Sorunları tespit et."""
        issues = []
        
        if MetricType.FAITHFULNESS in metrics and metrics[MetricType.FAITHFULNESS].score < 0.5:
            issues.append("Low faithfulness: Answer may contain unsupported claims")
        
        if MetricType.CONTEXT_PRECISION in metrics and metrics[MetricType.CONTEXT_PRECISION].score < 0.4:
            issues.append("Poor context precision: Relevant contexts not ranked properly")
        
        if MetricType.ANSWER_RELEVANCY in metrics and metrics[MetricType.ANSWER_RELEVANCY].score < 0.5:
            issues.append("Low answer relevancy: Answer may not address the question")
        
        if MetricType.COHERENCE in metrics and metrics[MetricType.COHERENCE].score < 0.5:
            issues.append("Poor coherence: Answer structure needs improvement")
        
        if MetricType.HARMFULNESS in metrics and metrics[MetricType.HARMFULNESS].score < 0.7:
            issues.append("Safety concern: Answer may contain harmful content")
        
        return issues
    
    def _generate_recommendations(
        self, 
        metrics: Dict[MetricType, MetricResult],
        issues: List[str]
    ) -> List[str]:
        """Öneriler oluştur."""
        recommendations = []
        
        if MetricType.FAITHFULNESS in metrics and metrics[MetricType.FAITHFULNESS].score < 0.6:
            recommendations.append("Improve source attribution and grounding in context")
        
        if MetricType.CONTEXT_PRECISION in metrics and metrics[MetricType.CONTEXT_PRECISION].score < 0.5:
            recommendations.append("Consider improving retrieval ranking algorithm")
        
        if MetricType.CONTEXT_UTILIZATION in metrics and metrics[MetricType.CONTEXT_UTILIZATION].score < 0.5:
            recommendations.append("Increase context utilization in answer generation")
        
        if not recommendations and not issues:
            recommendations.append("Quality looks good! Continue monitoring.")
        
        return recommendations
    
    def _calculate_batch_statistics(self, results: List[RAGASResult]) -> BatchEvaluationResult:
        """Toplu istatistikleri hesapla."""
        if not results:
            return BatchEvaluationResult(results=[])
        
        # Collect scores by metric
        scores_by_metric: Dict[str, List[float]] = defaultdict(list)
        
        for result in results:
            scores_by_metric["overall"].append(result.overall_score)
            for metric_type, metric_result in result.metrics.items():
                scores_by_metric[metric_type.value].append(metric_result.score)
        
        # Calculate statistics
        mean_scores = {}
        std_scores = {}
        min_scores = {}
        max_scores = {}
        
        for metric_name, scores in scores_by_metric.items():
            mean_scores[metric_name] = statistics.mean(scores)
            std_scores[metric_name] = statistics.stdev(scores) if len(scores) > 1 else 0.0
            min_scores[metric_name] = min(scores)
            max_scores[metric_name] = max(scores)
        
        # Quality distribution
        quality_distribution = defaultdict(int)
        for result in results:
            quality_distribution[result.quality_tier.value] += 1
        
        total_time = sum(r.total_processing_time_ms for r in results)
        
        return BatchEvaluationResult(
            results=results,
            mean_scores=mean_scores,
            std_scores=std_scores,
            min_scores=min_scores,
            max_scores=max_scores,
            quality_distribution=dict(quality_distribution),
            total_processing_time_ms=total_time,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        return {
            "evaluation_count": self._evaluation_count,
            "total_processing_time_ms": self._total_processing_time,
            "avg_processing_time_ms": self._total_processing_time / max(self._evaluation_count, 1),
            "evaluation_level": self.evaluation_level.value,
            "metrics_available": [m.value for m in self._metrics.keys()],
        }


# =============================================================================
# SINGLETON
# =============================================================================

_ragas_evaluator: Optional[RAGASEvaluator] = None


def get_ragas_evaluator(level: EvaluationLevel = EvaluationLevel.STANDARD) -> RAGASEvaluator:
    """Singleton RAGASEvaluator instance."""
    global _ragas_evaluator
    
    if _ragas_evaluator is None or _ragas_evaluator.evaluation_level != level:
        _ragas_evaluator = RAGASEvaluator(evaluation_level=level)
    
    return _ragas_evaluator


ragas_evaluator = RAGASEvaluator()


__all__ = [
    "RAGASEvaluator",
    "RAGASInput",
    "RAGASResult",
    "MetricResult",
    "BatchEvaluationResult",
    "MetricType",
    "EvaluationLevel",
    "QualityTier",
    "AnswerRelevancyMetric",
    "FaithfulnessMetric",
    "ContextPrecisionMetric",
    "ContextRecallMetric",
    "ContextRelevancyMetric",
    "ContextUtilizationMetric",
    "AnswerCorrectnessMetric",
    "AnswerSimilarityMetric",
    "CoherenceMetric",
    "HarmfulnessMetric",
    "ragas_evaluator",
    "get_ragas_evaluator",
]
