"""
📊 RAGAS Evaluation Pipeline
=============================

RAG Evaluation framework for automated quality assessment.

Features:
- Faithfulness scoring
- Answer relevancy
- Context precision
- Context recall
- Answer correctness
- Semantic similarity
- Custom metrics
- Batch evaluation
- A/B testing support
"""

import asyncio
import hashlib
import json
import logging
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class MetricType(str, Enum):
    """Types of evaluation metrics"""
    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCY = "answer_relevancy"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    ANSWER_CORRECTNESS = "answer_correctness"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    LATENCY = "latency"
    COST = "cost"
    CUSTOM = "custom"


class EvaluationStatus(str, Enum):
    """Status of evaluation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============ DATA MODELS ============

class EvaluationSample(BaseModel):
    """A single evaluation sample"""
    id: str
    question: str
    answer: str
    contexts: List[str] = Field(default_factory=list)
    ground_truth: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricResult(BaseModel):
    """Result of a single metric evaluation"""
    metric_type: MetricType
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    reasoning: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    """Complete evaluation result for a sample"""
    sample_id: str
    metrics: Dict[MetricType, MetricResult] = Field(default_factory=dict)
    overall_score: float = Field(0.0, ge=0.0, le=1.0)
    status: EvaluationStatus = EvaluationStatus.COMPLETED
    error: Optional[str] = None
    evaluation_time_ms: float = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchEvaluationResult(BaseModel):
    """Results from batch evaluation"""
    batch_id: str
    total_samples: int
    successful_samples: int
    failed_samples: int
    metric_averages: Dict[MetricType, float] = Field(default_factory=dict)
    metric_std_devs: Dict[MetricType, float] = Field(default_factory=dict)
    overall_average: float = 0.0
    results: List[EvaluationResult] = Field(default_factory=list)
    evaluation_time_ms: float = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============ METRIC IMPLEMENTATIONS ============

class EvaluationMetric(ABC):
    """Base class for evaluation metrics"""
    
    @property
    @abstractmethod
    def metric_type(self) -> MetricType:
        pass
    
    @abstractmethod
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        pass


class FaithfulnessMetric(EvaluationMetric):
    """
    Measures if the answer is faithful to the provided contexts.
    
    Checks that claims in the answer can be traced back to the contexts.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.FAITHFULNESS
    
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        if not sample.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                reasoning="No context provided"
            )
        
        # Extract claims from answer
        claims = self._extract_claims(sample.answer)
        
        if not claims:
            return MetricResult(
                metric_type=self.metric_type,
                score=1.0,
                reasoning="No specific claims found in answer"
            )
        
        # Check each claim against contexts
        supported_claims = 0
        combined_context = " ".join(sample.contexts).lower()
        
        for claim in claims:
            claim_words = set(claim.lower().split())
            # Simple overlap check (production should use LLM)
            if len(claim_words) > 0:
                overlap = sum(1 for w in claim_words if w in combined_context)
                overlap_ratio = overlap / len(claim_words)
                if overlap_ratio > 0.5:
                    supported_claims += 1
        
        score = supported_claims / len(claims)
        
        return MetricResult(
            metric_type=self.metric_type,
            score=score,
            reasoning=f"{supported_claims}/{len(claims)} claims supported by context",
            details={
                "total_claims": len(claims),
                "supported_claims": supported_claims,
                "claims": claims
            }
        )
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        # Simple sentence-based extraction
        sentences = re.split(r'[.!?]', text)
        claims = [s.strip() for s in sentences if len(s.strip()) > 10]
        return claims[:10]  # Limit claims


class AnswerRelevancyMetric(EvaluationMetric):
    """
    Measures if the answer is relevant to the question.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_RELEVANCY
    
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        question_words = set(sample.question.lower().split())
        answer_words = set(sample.answer.lower().split())
        
        # Remove common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when", "where", "who"}
        question_words -= stop_words
        answer_words -= stop_words
        
        if not question_words:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.5,
                reasoning="Question has no significant words"
            )
        
        # Check for key question concepts in answer
        overlap = question_words & answer_words
        keyword_coverage = len(overlap) / len(question_words)
        
        # Check if answer addresses question type
        question_type_score = self._check_question_type(sample.question, sample.answer)
        
        # Combined score
        score = keyword_coverage * 0.4 + question_type_score * 0.6
        score = min(1.0, max(0.0, score))
        
        return MetricResult(
            metric_type=self.metric_type,
            score=score,
            reasoning=f"Keyword coverage: {keyword_coverage:.0%}, Question type match: {question_type_score:.0%}",
            details={
                "keyword_coverage": keyword_coverage,
                "question_type_score": question_type_score,
                "overlapping_words": list(overlap)
            }
        )
    
    def _check_question_type(self, question: str, answer: str) -> float:
        """Check if answer matches question type"""
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Question type detection
        if question_lower.startswith(("what is", "what are")):
            # Definition questions - answer should have defining language
            if any(w in answer_lower for w in ["is", "are", "refers to", "means"]):
                return 1.0
        
        elif question_lower.startswith(("how to", "how do")):
            # How-to questions - answer should have steps/instructions
            if any(w in answer_lower for w in ["first", "then", "step", "1.", "1)"]):
                return 1.0
        
        elif question_lower.startswith("why"):
            # Why questions - answer should have causal language
            if any(w in answer_lower for w in ["because", "since", "due to", "reason"]):
                return 1.0
        
        elif question_lower.startswith(("can", "could", "is it", "are there")):
            # Yes/no questions
            if any(w in answer_lower for w in ["yes", "no", "can", "cannot"]):
                return 1.0
        
        # Default moderate score
        return 0.6


class ContextPrecisionMetric(EvaluationMetric):
    """
    Measures if retrieved contexts are relevant to the question.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.CONTEXT_PRECISION
    
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        if not sample.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                reasoning="No contexts provided"
            )
        
        question_words = set(sample.question.lower().split())
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "what", "how", "why", "when", "where", "who"}
        question_words -= stop_words
        
        relevant_contexts = 0
        context_scores = []
        
        for context in sample.contexts:
            context_words = set(context.lower().split())
            overlap = question_words & context_words
            
            if question_words:
                context_score = len(overlap) / len(question_words)
            else:
                context_score = 0.5
            
            context_scores.append(context_score)
            if context_score > 0.3:
                relevant_contexts += 1
        
        # Precision = relevant / total
        precision = relevant_contexts / len(sample.contexts) if sample.contexts else 0
        
        # Weight by position (earlier contexts matter more)
        weighted_scores = []
        for i, score in enumerate(context_scores):
            weight = 1.0 / (i + 1)  # Higher weight for earlier contexts
            weighted_scores.append(score * weight)
        
        weighted_precision = sum(weighted_scores) / sum(1.0 / (i + 1) for i in range(len(context_scores)))
        
        final_score = (precision + weighted_precision) / 2
        
        return MetricResult(
            metric_type=self.metric_type,
            score=final_score,
            reasoning=f"{relevant_contexts}/{len(sample.contexts)} contexts are relevant",
            details={
                "relevant_contexts": relevant_contexts,
                "total_contexts": len(sample.contexts),
                "context_scores": context_scores,
                "weighted_precision": weighted_precision
            }
        )


class ContextRecallMetric(EvaluationMetric):
    """
    Measures if contexts contain all information needed to answer.
    Requires ground_truth for proper evaluation.
    """
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.CONTEXT_RECALL
    
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        if not sample.ground_truth:
            # Without ground truth, use answer as proxy
            target = sample.answer
            return MetricResult(
                metric_type=self.metric_type,
                score=0.5,
                reasoning="No ground truth provided, using answer as proxy",
                confidence=0.5
            )
        else:
            target = sample.ground_truth
        
        if not sample.contexts:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.0,
                reasoning="No contexts provided"
            )
        
        # Extract key information from ground truth
        target_words = set(target.lower().split())
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "it", "this", "that"}
        target_words -= stop_words
        
        # Check coverage in contexts
        combined_context = " ".join(sample.contexts).lower()
        context_words = set(combined_context.split())
        
        covered_words = target_words & context_words
        recall = len(covered_words) / len(target_words) if target_words else 0
        
        return MetricResult(
            metric_type=self.metric_type,
            score=recall,
            reasoning=f"{len(covered_words)}/{len(target_words)} key terms found in contexts",
            details={
                "covered_terms": len(covered_words),
                "total_terms": len(target_words),
                "missing_terms": list(target_words - covered_words)[:10]
            }
        )


class AnswerCorrectnessMetric(EvaluationMetric):
    """
    Measures if the answer is correct compared to ground truth.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.ANSWER_CORRECTNESS
    
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        if not sample.ground_truth:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.5,
                reasoning="No ground truth available",
                confidence=0.0
            )
        
        # Compute similarity between answer and ground truth
        answer_words = set(sample.answer.lower().split())
        truth_words = set(sample.ground_truth.lower().split())
        
        # Jaccard similarity
        intersection = len(answer_words & truth_words)
        union = len(answer_words | truth_words)
        jaccard = intersection / union if union > 0 else 0
        
        # F1-based similarity
        if len(truth_words) > 0 and len(answer_words) > 0:
            precision = intersection / len(answer_words)
            recall = intersection / len(truth_words)
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        else:
            f1 = 0
        
        # Combined score
        score = jaccard * 0.3 + f1 * 0.7
        
        return MetricResult(
            metric_type=self.metric_type,
            score=score,
            reasoning=f"Jaccard: {jaccard:.2f}, F1: {f1:.2f}",
            details={
                "jaccard_similarity": jaccard,
                "f1_score": f1,
                "common_words": intersection,
                "answer_length": len(answer_words),
                "truth_length": len(truth_words)
            }
        )


class SemanticSimilarityMetric(EvaluationMetric):
    """
    Measures semantic similarity between answer and ground truth.
    Uses embeddings for more accurate similarity.
    """
    
    def __init__(self, embedding_model: Optional[Any] = None):
        self.embedding_model = embedding_model
    
    @property
    def metric_type(self) -> MetricType:
        return MetricType.SEMANTIC_SIMILARITY
    
    async def evaluate(self, sample: EvaluationSample) -> MetricResult:
        if not sample.ground_truth:
            return MetricResult(
                metric_type=self.metric_type,
                score=0.5,
                reasoning="No ground truth available",
                confidence=0.0
            )
        
        # If we have embedding model, use it
        if self.embedding_model:
            try:
                answer_emb = await self._get_embedding(sample.answer)
                truth_emb = await self._get_embedding(sample.ground_truth)
                similarity = self._cosine_similarity(answer_emb, truth_emb)
                
                return MetricResult(
                    metric_type=self.metric_type,
                    score=similarity,
                    reasoning=f"Cosine similarity: {similarity:.3f}",
                    details={"method": "embedding"}
                )
            except Exception as e:
                logger.warning(f"Embedding similarity failed: {e}")
        
        # Fallback to word overlap
        answer_words = set(sample.answer.lower().split())
        truth_words = set(sample.ground_truth.lower().split())
        
        intersection = len(answer_words & truth_words)
        union = len(answer_words | truth_words)
        similarity = intersection / union if union > 0 else 0
        
        return MetricResult(
            metric_type=self.metric_type,
            score=similarity,
            reasoning=f"Word overlap similarity: {similarity:.3f}",
            details={"method": "word_overlap"}
        )
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        return await self.embedding_model.embed(text)
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Compute cosine similarity"""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        return dot / (norm1 * norm2) if norm1 * norm2 > 0 else 0


# ============ EVALUATION ENGINE ============

class RAGASEvaluator:
    """
    Main RAGAS evaluation engine.
    
    Evaluates RAG system outputs using multiple metrics.
    """
    
    def __init__(
        self,
        metrics: Optional[List[EvaluationMetric]] = None,
        llm_client: Optional[Any] = None,
        embedding_model: Optional[Any] = None
    ):
        self.llm_client = llm_client
        self.embedding_model = embedding_model
        
        # Initialize default metrics
        if metrics:
            self.metrics = {m.metric_type: m for m in metrics}
        else:
            self.metrics = self._init_default_metrics()
    
    def _init_default_metrics(self) -> Dict[MetricType, EvaluationMetric]:
        """Initialize default metrics"""
        return {
            MetricType.FAITHFULNESS: FaithfulnessMetric(self.llm_client),
            MetricType.ANSWER_RELEVANCY: AnswerRelevancyMetric(self.llm_client),
            MetricType.CONTEXT_PRECISION: ContextPrecisionMetric(),
            MetricType.CONTEXT_RECALL: ContextRecallMetric(),
            MetricType.ANSWER_CORRECTNESS: AnswerCorrectnessMetric(self.llm_client),
            MetricType.SEMANTIC_SIMILARITY: SemanticSimilarityMetric(self.embedding_model),
        }
    
    async def evaluate_sample(
        self,
        sample: EvaluationSample,
        metrics: Optional[List[MetricType]] = None
    ) -> EvaluationResult:
        """
        Evaluate a single sample.
        
        Args:
            sample: The sample to evaluate
            metrics: Specific metrics to run (default: all)
            
        Returns:
            EvaluationResult
        """
        import time
        start_time = time.time()
        
        metric_results = {}
        metrics_to_run = metrics or list(self.metrics.keys())
        
        # Run metrics
        tasks = []
        for metric_type in metrics_to_run:
            if metric_type in self.metrics:
                tasks.append(self._run_metric(metric_type, sample))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, MetricResult):
                metric_results[result.metric_type] = result
            elif isinstance(result, Exception):
                logger.error(f"Metric evaluation failed: {result}")
        
        # Calculate overall score
        if metric_results:
            overall = sum(r.score for r in metric_results.values()) / len(metric_results)
        else:
            overall = 0.0
        
        elapsed = (time.time() - start_time) * 1000
        
        return EvaluationResult(
            sample_id=sample.id,
            metrics=metric_results,
            overall_score=overall,
            status=EvaluationStatus.COMPLETED,
            evaluation_time_ms=elapsed
        )
    
    async def _run_metric(
        self,
        metric_type: MetricType,
        sample: EvaluationSample
    ) -> MetricResult:
        """Run a single metric"""
        metric = self.metrics[metric_type]
        return await metric.evaluate(sample)
    
    async def evaluate_batch(
        self,
        samples: List[EvaluationSample],
        metrics: Optional[List[MetricType]] = None,
        max_concurrency: int = 5
    ) -> BatchEvaluationResult:
        """
        Evaluate a batch of samples.
        
        Args:
            samples: List of samples to evaluate
            metrics: Specific metrics to run
            max_concurrency: Maximum concurrent evaluations
            
        Returns:
            BatchEvaluationResult
        """
        import time
        start_time = time.time()
        
        batch_id = hashlib.md5(
            str(datetime.now().timestamp()).encode()
        ).hexdigest()[:12]
        
        # Run evaluations with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def eval_with_semaphore(sample):
            async with semaphore:
                return await self.evaluate_sample(sample, metrics)
        
        tasks = [eval_with_semaphore(s) for s in samples]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_count = 0
        
        for result in results:
            if isinstance(result, EvaluationResult):
                successful_results.append(result)
            else:
                failed_count += 1
        
        # Calculate statistics
        metric_averages = {}
        metric_std_devs = {}
        
        for metric_type in (metrics or self.metrics.keys()):
            scores = [
                r.metrics[metric_type].score 
                for r in successful_results 
                if metric_type in r.metrics
            ]
            
            if scores:
                avg = sum(scores) / len(scores)
                metric_averages[metric_type] = avg
                
                if len(scores) > 1:
                    variance = sum((s - avg) ** 2 for s in scores) / len(scores)
                    metric_std_devs[metric_type] = math.sqrt(variance)
                else:
                    metric_std_devs[metric_type] = 0.0
        
        # Overall average
        if metric_averages:
            overall_avg = sum(metric_averages.values()) / len(metric_averages)
        else:
            overall_avg = 0.0
        
        elapsed = (time.time() - start_time) * 1000
        
        return BatchEvaluationResult(
            batch_id=batch_id,
            total_samples=len(samples),
            successful_samples=len(successful_results),
            failed_samples=failed_count,
            metric_averages=metric_averages,
            metric_std_devs=metric_std_devs,
            overall_average=overall_avg,
            results=successful_results,
            evaluation_time_ms=elapsed
        )
    
    def add_metric(self, metric: EvaluationMetric):
        """Add a custom metric"""
        self.metrics[metric.metric_type] = metric
    
    def remove_metric(self, metric_type: MetricType):
        """Remove a metric"""
        if metric_type in self.metrics:
            del self.metrics[metric_type]
    
    # ============ CONVENIENCE METHODS FOR API ============
    
    async def evaluate_faithfulness(
        self,
        question: str,
        answer: str,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """
        Sadece Faithfulness metriğini değerlendir.
        
        Args:
            question: Kullanıcı sorusu
            answer: RAG yanıtı
            contexts: Kullanılan bağlamlar
            
        Returns:
            {"score": float, "reasoning": str, "details": dict}
        """
        sample = EvaluationSample(
            id="single_eval",
            question=question,
            answer=answer,
            contexts=contexts
        )
        
        try:
            if MetricType.FAITHFULNESS in self.metrics:
                result = await self.metrics[MetricType.FAITHFULNESS].evaluate(sample)
                return {
                    "score": result.score,
                    "reasoning": result.reasoning,
                    "details": result.details
                }
        except Exception as e:
            logger.error(f"Faithfulness evaluation error: {e}")
        
        # Fallback: basit kelime eşleşme skoru
        return self._simple_faithfulness(answer, contexts)
    
    def _simple_faithfulness(self, answer: str, contexts: List[str]) -> Dict[str, Any]:
        """Basit faithfulness hesaplama (LLM olmadan)"""
        answer_words = set(answer.lower().split())
        context_words = set()
        for ctx in contexts:
            context_words.update(ctx.lower().split())
        
        if not answer_words:
            return {"score": 0.0, "reasoning": "Boş yanıt", "details": {}}
        
        overlap = len(answer_words & context_words)
        score = min(overlap / len(answer_words), 1.0)
        
        return {
            "score": round(score, 4),
            "reasoning": f"Yanıttaki {len(answer_words)} kelimeden {overlap} tanesi bağlamlarda bulundu",
            "details": {"method": "word_overlap", "overlap_count": overlap}
        }
    
    async def evaluate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Sadece Answer Relevancy metriğini değerlendir.
        
        Args:
            question: Kullanıcı sorusu
            answer: RAG yanıtı
            
        Returns:
            {"score": float, "reasoning": str, "details": dict}
        """
        sample = EvaluationSample(
            id="single_eval",
            question=question,
            answer=answer,
            contexts=[]
        )
        
        try:
            if MetricType.ANSWER_RELEVANCY in self.metrics:
                result = await self.metrics[MetricType.ANSWER_RELEVANCY].evaluate(sample)
                return {
                    "score": result.score,
                    "reasoning": result.reasoning,
                    "details": result.details
                }
        except Exception as e:
            logger.error(f"Answer relevancy evaluation error: {e}")
        
        # Fallback: basit benzerlik skoru
        return self._simple_relevancy(question, answer)
    
    def _simple_relevancy(self, question: str, answer: str) -> Dict[str, Any]:
        """Basit relevancy hesaplama (LLM olmadan)"""
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        
        # Soru kelimelerinin yanıtta bulunma oranı
        if not q_words:
            return {"score": 0.5, "reasoning": "Boş soru", "details": {}}
        
        # Stop words çıkar
        stop_words = {'ne', 'nasıl', 'neden', 'kim', 'nerede', 'hangi', 'mi', 'mı', 'mu', 'mü',
                      'what', 'how', 'why', 'who', 'where', 'which', 'is', 'are', 'the', 'a', 'an'}
        q_meaningful = q_words - stop_words
        
        if not q_meaningful:
            q_meaningful = q_words
        
        overlap = len(q_meaningful & a_words)
        score = min(overlap / len(q_meaningful), 1.0)
        
        # Uzun yanıtlar için bonus
        if len(answer.split()) > 20:
            score = min(score + 0.1, 1.0)
        
        return {
            "score": round(score, 4),
            "reasoning": f"Soru kelimelerinin {overlap}/{len(q_meaningful)} tanesi yanıtta bulundu",
            "details": {"method": "keyword_overlap", "overlap_count": overlap}
        }
    
    async def evaluate_context_precision(
        self,
        question: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sadece Context Precision metriğini değerlendir.
        
        Args:
            question: Kullanıcı sorusu
            contexts: Kullanılan bağlamlar
            ground_truth: Doğru yanıt (opsiyonel)
            
        Returns:
            {"score": float, "reasoning": str, "details": dict}
        """
        sample = EvaluationSample(
            id="single_eval",
            question=question,
            answer="",  # Precision için answer gerekli değil
            contexts=contexts,
            ground_truth=ground_truth
        )
        
        try:
            if MetricType.CONTEXT_PRECISION in self.metrics:
                result = await self.metrics[MetricType.CONTEXT_PRECISION].evaluate(sample)
                return {
                    "score": result.score,
                    "reasoning": result.reasoning,
                    "details": result.details
                }
        except Exception as e:
            logger.error(f"Context precision evaluation error: {e}")
        
        # Fallback: basit precision skoru
        return self._simple_context_precision(question, contexts, ground_truth)
    
    def _simple_context_precision(
        self,
        question: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, Any]:
        """Basit context precision hesaplama"""
        if not contexts:
            return {"score": 0.0, "reasoning": "Bağlam yok", "details": {}}
        
        q_words = set(question.lower().split())
        stop_words = {'ne', 'nasıl', 'neden', 'kim', 'nerede', 'hangi', 'mi', 'mı', 'mu', 'mü',
                      'what', 'how', 'why', 'who', 'where', 'which', 'is', 'are', 'the', 'a', 'an'}
        q_meaningful = q_words - stop_words
        
        if not q_meaningful:
            q_meaningful = q_words
        
        # Her bağlam için skor hesapla
        context_scores = []
        for ctx in contexts:
            ctx_words = set(ctx.lower().split())
            overlap = len(q_meaningful & ctx_words)
            ctx_score = overlap / len(q_meaningful) if q_meaningful else 0
            context_scores.append(min(ctx_score, 1.0))
        
        # Ground truth varsa, ground truth kelimelerini de kontrol et
        if ground_truth:
            gt_words = set(ground_truth.lower().split())
            for i, ctx in enumerate(contexts):
                ctx_words = set(ctx.lower().split())
                gt_overlap = len(gt_words & ctx_words) / len(gt_words) if gt_words else 0
                context_scores[i] = (context_scores[i] + gt_overlap) / 2
        
        # Precision: ilk bağlamların daha önemli olduğu ağırlıklı ortalama
        weights = [1 / (i + 1) for i in range(len(context_scores))]
        weighted_sum = sum(s * w for s, w in zip(context_scores, weights))
        total_weight = sum(weights)
        
        precision = weighted_sum / total_weight if total_weight > 0 else 0
        
        return {
            "score": round(precision, 4),
            "reasoning": f"{len(contexts)} bağlam değerlendirildi, ağırlıklı precision hesaplandı",
            "details": {
                "method": "weighted_precision",
                "context_scores": [round(s, 4) for s in context_scores],
                "weights": [round(w, 4) for w in weights]
            }
        }


# ============ A/B TESTING ============

class ABTestResult(BaseModel):
    """Result of A/B test comparison"""
    test_id: str
    variant_a_name: str
    variant_b_name: str
    variant_a_results: BatchEvaluationResult
    variant_b_results: BatchEvaluationResult
    metric_comparisons: Dict[MetricType, Dict[str, float]] = Field(default_factory=dict)
    winner: Optional[str] = None
    confidence: float = 0.0
    summary: str = ""


class ABTestRunner:
    """
    Run A/B tests between RAG variants.
    """
    
    def __init__(self, evaluator: RAGASEvaluator):
        self.evaluator = evaluator
    
    async def run_test(
        self,
        variant_a_name: str,
        variant_a_samples: List[EvaluationSample],
        variant_b_name: str,
        variant_b_samples: List[EvaluationSample],
        metrics: Optional[List[MetricType]] = None
    ) -> ABTestResult:
        """
        Run A/B test between two variants.
        
        Samples should be generated from the same questions
        but with different RAG configurations.
        """
        test_id = hashlib.md5(
            f"{variant_a_name}_{variant_b_name}_{datetime.now().timestamp()}".encode()
        ).hexdigest()[:12]
        
        # Evaluate both variants
        results_a = await self.evaluator.evaluate_batch(variant_a_samples, metrics)
        results_b = await self.evaluator.evaluate_batch(variant_b_samples, metrics)
        
        # Compare metrics
        comparisons = {}
        for metric_type in results_a.metric_averages:
            if metric_type in results_b.metric_averages:
                avg_a = results_a.metric_averages[metric_type]
                avg_b = results_b.metric_averages[metric_type]
                diff = avg_b - avg_a
                relative_diff = diff / avg_a if avg_a > 0 else 0
                
                comparisons[metric_type] = {
                    "variant_a": avg_a,
                    "variant_b": avg_b,
                    "absolute_diff": diff,
                    "relative_diff": relative_diff
                }
        
        # Determine winner
        wins_a = sum(1 for c in comparisons.values() if c["absolute_diff"] < 0)
        wins_b = sum(1 for c in comparisons.values() if c["absolute_diff"] > 0)
        
        if wins_a > wins_b:
            winner = variant_a_name
            confidence = wins_a / len(comparisons) if comparisons else 0
        elif wins_b > wins_a:
            winner = variant_b_name
            confidence = wins_b / len(comparisons) if comparisons else 0
        else:
            winner = None
            confidence = 0.5
        
        # Generate summary
        if winner:
            summary = f"{winner} performs better on {max(wins_a, wins_b)}/{len(comparisons)} metrics"
        else:
            summary = "No clear winner - variants perform similarly"
        
        return ABTestResult(
            test_id=test_id,
            variant_a_name=variant_a_name,
            variant_b_name=variant_b_name,
            variant_a_results=results_a,
            variant_b_results=results_b,
            metric_comparisons=comparisons,
            winner=winner,
            confidence=confidence,
            summary=summary
        )


# ============ REPORT GENERATOR ============

class EvaluationReporter:
    """
    Generate evaluation reports.
    """
    
    def generate_markdown_report(
        self,
        result: Union[EvaluationResult, BatchEvaluationResult]
    ) -> str:
        """Generate markdown report"""
        lines = []
        
        if isinstance(result, BatchEvaluationResult):
            lines.append("# RAG Evaluation Report")
            lines.append(f"\n**Batch ID:** {result.batch_id}")
            lines.append(f"**Total Samples:** {result.total_samples}")
            lines.append(f"**Successful:** {result.successful_samples}")
            lines.append(f"**Failed:** {result.failed_samples}")
            lines.append(f"\n## Overall Score: {result.overall_average:.2%}")
            
            lines.append("\n## Metric Summary")
            lines.append("| Metric | Average | Std Dev |")
            lines.append("|--------|---------|---------|")
            
            for metric_type, avg in result.metric_averages.items():
                std = result.metric_std_devs.get(metric_type, 0)
                lines.append(f"| {metric_type.value} | {avg:.2%} | {std:.2%} |")
        
        else:
            lines.append("# Sample Evaluation Report")
            lines.append(f"\n**Sample ID:** {result.sample_id}")
            lines.append(f"**Overall Score:** {result.overall_score:.2%}")
            
            lines.append("\n## Metrics")
            for metric_type, metric_result in result.metrics.items():
                lines.append(f"\n### {metric_type.value}")
                lines.append(f"- **Score:** {metric_result.score:.2%}")
                lines.append(f"- **Reasoning:** {metric_result.reasoning}")
        
        return "\n".join(lines)
    
    def generate_json_report(
        self,
        result: Union[EvaluationResult, BatchEvaluationResult]
    ) -> str:
        """Generate JSON report"""
        return result.model_dump_json(indent=2)


# ============ CONVENIENCE FUNCTIONS ============

def create_evaluator(
    llm_client: Optional[Any] = None,
    embedding_model: Optional[Any] = None
) -> RAGASEvaluator:
    """Create a RAGAS evaluator with default metrics"""
    return RAGASEvaluator(
        llm_client=llm_client,
        embedding_model=embedding_model
    )


async def quick_evaluate(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> EvaluationResult:
    """
    Quick evaluation of a single Q&A.
    
    Example:
        result = await quick_evaluate(
            question="What is Python?",
            answer="Python is a programming language.",
            contexts=["Python is a high-level programming language."],
            ground_truth="Python is a versatile programming language."
        )
    """
    evaluator = create_evaluator()
    
    sample = EvaluationSample(
        id=hashlib.md5(question.encode()).hexdigest()[:12],
        question=question,
        answer=answer,
        contexts=contexts,
        ground_truth=ground_truth
    )
    
    return await evaluator.evaluate_sample(sample)


# ============ EXPORTS ============

__all__ = [
    # Types
    "MetricType",
    "EvaluationStatus",
    # Models
    "EvaluationSample",
    "MetricResult",
    "EvaluationResult",
    "BatchEvaluationResult",
    "ABTestResult",
    # Metrics
    "EvaluationMetric",
    "FaithfulnessMetric",
    "AnswerRelevancyMetric",
    "ContextPrecisionMetric",
    "ContextRecallMetric",
    "AnswerCorrectnessMetric",
    "SemanticSimilarityMetric",
    # Engine
    "RAGASEvaluator",
    "ABTestRunner",
    "EvaluationReporter",
    # Factory
    "create_evaluator",
    "quick_evaluate",
]
