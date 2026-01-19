"""
Self-RAG System
===============

Self-Reflective Retrieval-Augmented Generation.

Kendi çıktısını değerlendiren, iteratif olarak iyileştiren RAG sistemi.

Features:
- Self-Evaluation with multiple dimensions
- Confidence Scoring
- Adaptive Re-retrieval
- Iterative Refinement Loop
- Hallucination Detection
- Quality Gating
- Critique Generation

Based on: "Self-RAG: Learning to Retrieve, Generate, and Critique"

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Tuple

from core.logger import get_logger

logger = get_logger("rag.self_rag")


# =============================================================================
# ENUMS
# =============================================================================

class RetrievalDecision(Enum):
    """Retrieval kararı."""
    RETRIEVE = "retrieve"         # Retrieval gerekli
    NO_RETRIEVE = "no_retrieve"   # Bilgi yeterli
    REFINE = "refine"             # Mevcut bilgiyi rafine et


class SupportLevel(Enum):
    """Kaynak desteği seviyesi."""
    FULLY_SUPPORTED = "fully_supported"       # Tamamen destekleniyor
    PARTIALLY_SUPPORTED = "partially_supported"  # Kısmen destekleniyor
    NO_SUPPORT = "no_support"                 # Desteklenmiyor
    CONTRADICTS = "contradicts"               # Çelişiyor


class RelevanceLevel(Enum):
    """Relevance seviyesi."""
    HIGHLY_RELEVANT = "highly_relevant"
    RELEVANT = "relevant"
    PARTIALLY_RELEVANT = "partially_relevant"
    IRRELEVANT = "irrelevant"


class UsefulnessLevel(Enum):
    """Usefulness seviyesi."""
    VERY_USEFUL = "very_useful"
    USEFUL = "useful"
    SOMEWHAT_USEFUL = "somewhat_useful"
    NOT_USEFUL = "not_useful"


class QualityDimension(Enum):
    """Kalite boyutları."""
    RELEVANCE = "relevance"
    FAITHFULNESS = "faithfulness"
    COHERENCE = "coherence"
    COMPLETENESS = "completeness"
    FLUENCY = "fluency"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class RetrievedPassage:
    """Getirilen pasaj."""
    id: str
    content: str
    score: float
    source: str = ""
    page_number: Optional[int] = None
    
    # Self-RAG evaluations
    relevance: Optional[RelevanceLevel] = None
    support_level: Optional[SupportLevel] = None
    usefulness: Optional[UsefulnessLevel] = None
    
    # Scores
    relevance_score: float = 0.0
    support_score: float = 0.0
    usefulness_score: float = 0.0
    
    def combined_score(self) -> float:
        """Birleşik skor."""
        return (
            0.4 * self.relevance_score +
            0.35 * self.support_score +
            0.25 * self.usefulness_score
        )
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content[:200] + "...",
            "score": self.score,
            "source": self.source,
            "relevance": self.relevance.value if self.relevance else None,
            "support_level": self.support_level.value if self.support_level else None,
            "usefulness": self.usefulness.value if self.usefulness else None,
            "combined_score": self.combined_score(),
        }


@dataclass
class GeneratedSegment:
    """Üretilen metin segmenti."""
    content: str
    supporting_passages: List[str]
    confidence: float
    
    # Evaluation
    is_supported: bool = True
    support_level: Optional[SupportLevel] = None
    needs_citation: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "supporting_passages": self.supporting_passages[:3],
            "confidence": self.confidence,
            "is_supported": self.is_supported,
            "support_level": self.support_level.value if self.support_level else None,
        }


@dataclass
class CritiqueResult:
    """Critique sonucu."""
    dimension: QualityDimension
    score: float  # 0-1
    explanation: str
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "explanation": self.explanation,
            "suggestions": self.suggestions,
        }


@dataclass
class ReflectionResult:
    """Reflection sonucu."""
    overall_quality: float
    critiques: List[CritiqueResult]
    needs_refinement: bool
    refinement_suggestions: List[str]
    confidence_adjustment: float
    
    # Detailed scores
    relevance_score: float = 0.0
    faithfulness_score: float = 0.0
    coherence_score: float = 0.0
    completeness_score: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "overall_quality": self.overall_quality,
            "critiques": [c.to_dict() for c in self.critiques],
            "needs_refinement": self.needs_refinement,
            "refinement_suggestions": self.refinement_suggestions,
            "confidence_adjustment": self.confidence_adjustment,
            "scores": {
                "relevance": self.relevance_score,
                "faithfulness": self.faithfulness_score,
                "coherence": self.coherence_score,
                "completeness": self.completeness_score,
            },
        }


@dataclass
class SelfRAGResponse:
    """Self-RAG yanıt objesi."""
    query: str
    response: str
    passages: List[RetrievedPassage]
    segments: List[GeneratedSegment]
    reflection: ReflectionResult
    
    # Confidence & Quality
    initial_confidence: float
    final_confidence: float
    quality_score: float
    
    # Iteration tracking
    iterations: int
    retrieval_decisions: List[str]
    refinements_made: int
    
    # Timing
    total_time_ms: int
    
    # Flags
    is_grounded: bool = True
    has_hallucinations: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "response": self.response,
            "passages_count": len(self.passages),
            "segments_count": len(self.segments),
            "reflection": self.reflection.to_dict(),
            "initial_confidence": self.initial_confidence,
            "final_confidence": self.final_confidence,
            "quality_score": self.quality_score,
            "iterations": self.iterations,
            "refinements_made": self.refinements_made,
            "total_time_ms": self.total_time_ms,
            "is_grounded": self.is_grounded,
            "has_hallucinations": self.has_hallucinations,
        }


# =============================================================================
# PROTOCOLS
# =============================================================================

class LLMProtocol(Protocol):
    def generate(self, prompt: str, **kwargs) -> str:
        ...


class RetrieverProtocol(Protocol):
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> Any:
        ...


# =============================================================================
# SELF-RAG COMPONENTS
# =============================================================================

class RetrievalPredictor:
    """
    Retrieval gereksinimi tahmin edici.
    
    Sorgunun retrieval gerektirip gerektirmediğini belirler.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def predict(self, query: str, context: str = "") -> RetrievalDecision:
        """Retrieval kararı ver."""
        self._lazy_load()
        
        # Heuristic checks first
        if not context:
            return RetrievalDecision.RETRIEVE
        
        # Keywords that suggest retrieval need
        retrieval_keywords = [
            "güncel", "son", "yeni", "recent", "latest",
            "kaynak", "belge", "source", "document",
            "detay", "detail", "açıkla", "explain"
        ]
        
        query_lower = query.lower()
        needs_retrieval = any(kw in query_lower for kw in retrieval_keywords)
        
        if needs_retrieval and not context:
            return RetrievalDecision.RETRIEVE
        
        # LLM-based decision for complex cases
        try:
            prompt = f"""Decide if retrieval is needed to answer this query.

Query: {query}
Available Context: {context[:500] if context else "None"}

Options:
1. RETRIEVE - Need to fetch new information
2. NO_RETRIEVE - Existing context is sufficient
3. REFINE - Need to refine existing information

Decision (one word):"""

            response = self._llm.generate(prompt, max_tokens=20).strip().upper()
            
            if "RETRIEVE" in response and "NO" not in response:
                return RetrievalDecision.RETRIEVE
            elif "NO_RETRIEVE" in response or "NO" in response:
                return RetrievalDecision.NO_RETRIEVE
            else:
                return RetrievalDecision.REFINE
                
        except Exception:
            return RetrievalDecision.RETRIEVE


class PassageEvaluator:
    """
    Passage değerlendirici.
    
    Getirilen pasajların kalitesini değerlendirir.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def evaluate_relevance(
        self,
        query: str,
        passage: RetrievedPassage
    ) -> Tuple[RelevanceLevel, float]:
        """Relevance değerlendir."""
        self._lazy_load()
        
        try:
            prompt = f"""Rate the relevance of this passage to the query.

Query: {query}
Passage: {passage.content[:500]}

Rating (1-5, where 5 is highly relevant):"""

            response = self._llm.generate(prompt, max_tokens=10)
            score = float(response.strip()[0]) / 5.0
            
            if score >= 0.8:
                level = RelevanceLevel.HIGHLY_RELEVANT
            elif score >= 0.6:
                level = RelevanceLevel.RELEVANT
            elif score >= 0.4:
                level = RelevanceLevel.PARTIALLY_RELEVANT
            else:
                level = RelevanceLevel.IRRELEVANT
            
            return level, score
            
        except Exception:
            return RelevanceLevel.RELEVANT, 0.6
    
    def evaluate_support(
        self,
        claim: str,
        passage: RetrievedPassage
    ) -> Tuple[SupportLevel, float]:
        """Kaynak desteğini değerlendir."""
        self._lazy_load()
        
        try:
            prompt = f"""Does the passage support this claim?

Claim: {claim}
Passage: {passage.content[:500]}

Answer (FULLY_SUPPORTED / PARTIALLY_SUPPORTED / NO_SUPPORT / CONTRADICTS):"""

            response = self._llm.generate(prompt, max_tokens=20).strip().upper()
            
            if "FULLY" in response:
                return SupportLevel.FULLY_SUPPORTED, 1.0
            elif "PARTIALLY" in response:
                return SupportLevel.PARTIALLY_SUPPORTED, 0.6
            elif "CONTRADICT" in response:
                return SupportLevel.CONTRADICTS, 0.0
            else:
                return SupportLevel.NO_SUPPORT, 0.2
                
        except Exception:
            return SupportLevel.PARTIALLY_SUPPORTED, 0.5
    
    def evaluate_usefulness(
        self,
        query: str,
        passage: RetrievedPassage,
        existing_passages: List[RetrievedPassage]
    ) -> Tuple[UsefulnessLevel, float]:
        """Usefulness değerlendir."""
        # Check for redundancy
        existing_content = " ".join(p.content[:200] for p in existing_passages)
        
        # Simple overlap check
        passage_words = set(passage.content.lower().split())
        existing_words = set(existing_content.lower().split())
        
        overlap = len(passage_words & existing_words) / max(len(passage_words), 1)
        
        if overlap > 0.7:
            return UsefulnessLevel.NOT_USEFUL, 0.2
        elif overlap > 0.5:
            return UsefulnessLevel.SOMEWHAT_USEFUL, 0.4
        elif passage.score > 0.7:
            return UsefulnessLevel.VERY_USEFUL, 0.9
        else:
            return UsefulnessLevel.USEFUL, 0.6
    
    def evaluate_passage(
        self,
        query: str,
        passage: RetrievedPassage,
        existing_passages: List[RetrievedPassage] = None
    ) -> RetrievedPassage:
        """Pasajı kapsamlı değerlendir."""
        existing_passages = existing_passages or []
        
        # Evaluate dimensions
        rel_level, rel_score = self.evaluate_relevance(query, passage)
        use_level, use_score = self.evaluate_usefulness(query, passage, existing_passages)
        
        passage.relevance = rel_level
        passage.relevance_score = rel_score
        passage.usefulness = use_level
        passage.usefulness_score = use_score
        
        return passage


class ResponseGenerator:
    """
    Response generator with segment tracking.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def generate(
        self,
        query: str,
        passages: List[RetrievedPassage],
        previous_response: str = ""
    ) -> Tuple[str, List[GeneratedSegment]]:
        """Response üret ve segment'lere ayır."""
        self._lazy_load()
        
        # Build context
        context_parts = []
        for i, p in enumerate(passages[:5], 1):
            context_parts.append(f"[{i}] {p.content[:600]}")
        
        context = "\n\n".join(context_parts)
        
        # Generate
        if previous_response:
            prompt = f"""Improve this response based on the sources:

Previous Response: {previous_response}

Sources:
{context}

Question: {query}

Improved Response (cite sources with [1], [2], etc.):"""
        else:
            prompt = f"""Answer the question based on these sources.
Cite each source used with [1], [2], etc.

Sources:
{context}

Question: {query}

Answer:"""
        
        response = self._llm.generate(prompt, max_tokens=800)
        
        # Parse into segments
        segments = self._parse_segments(response, passages)
        
        return response, segments
    
    def _parse_segments(
        self,
        response: str,
        passages: List[RetrievedPassage]
    ) -> List[GeneratedSegment]:
        """Response'u segment'lere ayır."""
        import re
        
        segments = []
        
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', response)
        
        for sentence in sentences:
            if not sentence.strip():
                continue
            
            # Find citations
            citations = re.findall(r'\[(\d+)\]', sentence)
            supporting = []
            
            for cite in citations:
                idx = int(cite) - 1
                if 0 <= idx < len(passages):
                    supporting.append(passages[idx].id)
            
            # Calculate confidence based on citation presence
            confidence = 0.8 if supporting else 0.5
            
            segments.append(GeneratedSegment(
                content=sentence,
                supporting_passages=supporting,
                confidence=confidence,
                needs_citation=len(supporting) == 0 and len(sentence) > 50,
            ))
        
        return segments


class SelfCritic:
    """
    Self-Critic - Response kalitesini değerlendirir.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def critique(
        self,
        query: str,
        response: str,
        passages: List[RetrievedPassage]
    ) -> ReflectionResult:
        """Response'u kritik et."""
        self._lazy_load()
        
        critiques = []
        
        # 1. Relevance critique
        rel_critique = self._critique_dimension(
            query, response, QualityDimension.RELEVANCE,
            "Does the response directly answer the question?"
        )
        critiques.append(rel_critique)
        
        # 2. Faithfulness critique
        faith_critique = self._critique_faithfulness(query, response, passages)
        critiques.append(faith_critique)
        
        # 3. Coherence critique
        coh_critique = self._critique_dimension(
            query, response, QualityDimension.COHERENCE,
            "Is the response logically coherent and well-structured?"
        )
        critiques.append(coh_critique)
        
        # 4. Completeness critique
        comp_critique = self._critique_dimension(
            query, response, QualityDimension.COMPLETENESS,
            "Does the response cover all aspects of the question?"
        )
        critiques.append(comp_critique)
        
        # Calculate overall quality
        scores = [c.score for c in critiques]
        overall_quality = sum(scores) / len(scores)
        
        # Determine if refinement needed
        needs_refinement = overall_quality < 0.6 or any(c.score < 0.4 for c in critiques)
        
        # Generate suggestions
        suggestions = []
        for c in critiques:
            if c.score < 0.6:
                suggestions.extend(c.suggestions)
        
        # Confidence adjustment
        confidence_adjustment = overall_quality - 0.5
        
        return ReflectionResult(
            overall_quality=overall_quality,
            critiques=critiques,
            needs_refinement=needs_refinement,
            refinement_suggestions=suggestions[:5],
            confidence_adjustment=confidence_adjustment,
            relevance_score=rel_critique.score,
            faithfulness_score=faith_critique.score,
            coherence_score=coh_critique.score,
            completeness_score=comp_critique.score,
        )
    
    def _critique_dimension(
        self,
        query: str,
        response: str,
        dimension: QualityDimension,
        question: str
    ) -> CritiqueResult:
        """Tek bir boyutu kritik et."""
        try:
            prompt = f"""Evaluate this response on {dimension.value}.

Question: {query}
Response: {response[:500]}

{question}

Score (1-5) and brief explanation:"""

            result = self._llm.generate(prompt, max_tokens=100)
            
            # Parse score
            import re
            score_match = re.search(r'(\d)', result)
            score = float(score_match.group(1)) / 5.0 if score_match else 0.5
            
            # Parse explanation
            explanation = result.split('\n')[0] if result else "No explanation"
            
            suggestions = []
            if score < 0.6:
                suggestions.append(f"Improve {dimension.value}")
            
            return CritiqueResult(
                dimension=dimension,
                score=score,
                explanation=explanation,
                suggestions=suggestions,
            )
            
        except Exception as e:
            return CritiqueResult(
                dimension=dimension,
                score=0.5,
                explanation=f"Evaluation failed: {str(e)}",
            )
    
    def _critique_faithfulness(
        self,
        query: str,
        response: str,
        passages: List[RetrievedPassage]
    ) -> CritiqueResult:
        """Faithfulness (kaynak uyumu) kritik et."""
        if not passages:
            return CritiqueResult(
                dimension=QualityDimension.FAITHFULNESS,
                score=0.3,
                explanation="No sources available for verification",
                suggestions=["Add source citations"],
            )
        
        # Check if response content aligns with passages
        passage_content = " ".join(p.content for p in passages[:5])
        
        try:
            prompt = f"""Is this response faithful to the sources?

Sources: {passage_content[:1000]}

Response: {response[:500]}

Score (1-5) where 5 means fully faithful:"""

            result = self._llm.generate(prompt, max_tokens=50)
            
            import re
            score_match = re.search(r'(\d)', result)
            score = float(score_match.group(1)) / 5.0 if score_match else 0.5
            
            suggestions = []
            if score < 0.6:
                suggestions.append("Ensure all claims are supported by sources")
                suggestions.append("Remove or qualify unsupported statements")
            
            return CritiqueResult(
                dimension=QualityDimension.FAITHFULNESS,
                score=score,
                explanation=f"Faithfulness score: {score:.2f}",
                suggestions=suggestions,
            )
            
        except Exception:
            return CritiqueResult(
                dimension=QualityDimension.FAITHFULNESS,
                score=0.5,
                explanation="Faithfulness evaluation failed",
            )


class ResponseRefiner:
    """
    Response refiner - İyileştirme yapar.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def refine(
        self,
        query: str,
        response: str,
        reflection: ReflectionResult,
        passages: List[RetrievedPassage]
    ) -> str:
        """Response'u iyileştir."""
        self._lazy_load()
        
        # Build refinement prompt
        issues = []
        for critique in reflection.critiques:
            if critique.score < 0.6:
                issues.append(f"- {critique.dimension.value}: {critique.explanation}")
        
        suggestions = "\n".join(f"- {s}" for s in reflection.refinement_suggestions[:3])
        
        context = "\n".join(p.content[:300] for p in passages[:3])
        
        prompt = f"""Improve this response based on the critique.

Original Question: {query}

Original Response: {response}

Issues Found:
{chr(10).join(issues)}

Suggestions:
{suggestions}

Available Sources:
{context}

Improved Response:"""

        refined = self._llm.generate(prompt, max_tokens=800)
        
        return refined


# =============================================================================
# SELF-RAG MAIN CLASS
# =============================================================================

class SelfRAG:
    """
    Self-RAG - Self-Reflective RAG sistemi.
    
    Kendi çıktısını değerlendiren ve iteratif olarak iyileştiren
    gelişmiş RAG sistemi.
    
    Example:
        self_rag = SelfRAG()
        result = self_rag.query("What are the benefits of X?")
        print(result.response)
        print(result.reflection.overall_quality)
    """
    
    def __init__(
        self,
        retriever: Optional[RetrieverProtocol] = None,
        llm: Optional[LLMProtocol] = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.7,
        confidence_threshold: float = 0.6,
    ):
        """
        Self-RAG başlat.
        
        Args:
            retriever: Retriever instance
            llm: LLM instance
            max_iterations: Maksimum iterasyon sayısı
            quality_threshold: Minimum kalite eşiği
            confidence_threshold: Minimum güven eşiği
        """
        self._retriever = retriever
        self._llm = llm
        
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.confidence_threshold = confidence_threshold
        
        # Components
        self.retrieval_predictor = RetrievalPredictor(llm)
        self.passage_evaluator = PassageEvaluator(llm)
        self.generator = ResponseGenerator(llm)
        self.critic = SelfCritic(llm)
        self.refiner = ResponseRefiner(llm)
        
        # Stats
        self._query_count = 0
        self._avg_quality = 0.0
        self._refinement_count = 0
    
    def _lazy_load(self):
        if self._retriever is None:
            from rag.pipeline import rag_pipeline
            self._retriever = rag_pipeline
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        enable_reflection: bool = True,
        enable_refinement: bool = True,
    ) -> SelfRAGResponse:
        """
        Self-RAG sorgusu.
        
        Args:
            query: Kullanıcı sorgusu
            top_k: Döndürülecek pasaj sayısı
            enable_reflection: Self-reflection aktif mi
            enable_refinement: Auto-refinement aktif mi
            
        Returns:
            SelfRAGResponse
        """
        self._lazy_load()
        
        start_time = time.time()
        logger.info(f"Self-RAG query: {query[:50]}...")
        
        iterations = 0
        refinements_made = 0
        retrieval_decisions = []
        passages: List[RetrievedPassage] = []
        
        # 1. Initial retrieval decision
        decision = self.retrieval_predictor.predict(query)
        retrieval_decisions.append(decision.value)
        
        # 2. Retrieve if needed
        if decision != RetrievalDecision.NO_RETRIEVE:
            passages = self._retrieve_and_evaluate(query, top_k)
        
        # 3. Generate initial response
        response, segments = self.generator.generate(query, passages)
        initial_confidence = self._calculate_confidence(passages, segments)
        
        # 4. Self-reflection loop
        current_response = response
        reflection = None
        
        while iterations < self.max_iterations:
            iterations += 1
            
            # Reflect on current response
            if enable_reflection:
                reflection = self.critic.critique(query, current_response, passages)
                
                # Check if quality is good enough
                if reflection.overall_quality >= self.quality_threshold:
                    logger.info(f"Quality threshold met at iteration {iterations}")
                    break
                
                # Refine if needed and enabled
                if enable_refinement and reflection.needs_refinement:
                    # Decide if more retrieval needed
                    if reflection.faithfulness_score < 0.5:
                        # Re-retrieve with refined query
                        new_passages = self._retrieve_and_evaluate(query, top_k)
                        passages.extend(new_passages)
                        passages = self._deduplicate_passages(passages)[:top_k * 2]
                        retrieval_decisions.append(RetrievalDecision.REFINE.value)
                    
                    # Refine response
                    current_response = self.refiner.refine(
                        query, current_response, reflection, passages
                    )
                    refinements_made += 1
                    
                    # Re-segment
                    _, segments = self.generator.generate(query, passages, current_response)
                else:
                    break
            else:
                break
        
        # 5. Final reflection
        if reflection is None:
            reflection = self.critic.critique(query, current_response, passages)
        
        # 6. Calculate final metrics
        final_confidence = self._calculate_confidence(passages, segments)
        final_confidence += reflection.confidence_adjustment * 0.2
        final_confidence = max(0.0, min(1.0, final_confidence))
        
        quality_score = reflection.overall_quality
        
        # Check for hallucinations
        has_hallucinations = reflection.faithfulness_score < 0.4
        is_grounded = reflection.faithfulness_score >= 0.6
        
        total_time = int((time.time() - start_time) * 1000)
        
        # Update stats
        self._update_stats(quality_score, refinements_made)
        
        result = SelfRAGResponse(
            query=query,
            response=current_response,
            passages=passages,
            segments=segments,
            reflection=reflection,
            initial_confidence=initial_confidence,
            final_confidence=final_confidence,
            quality_score=quality_score,
            iterations=iterations,
            retrieval_decisions=retrieval_decisions,
            refinements_made=refinements_made,
            total_time_ms=total_time,
            is_grounded=is_grounded,
            has_hallucinations=has_hallucinations,
        )
        
        logger.info(
            f"Self-RAG completed: quality={quality_score:.2f}, "
            f"confidence={final_confidence:.2f}, iterations={iterations}"
        )
        
        return result
    
    async def query_async(
        self,
        query: str,
        top_k: int = 5,
        enable_reflection: bool = True,
        enable_refinement: bool = True,
    ) -> SelfRAGResponse:
        """Asenkron Self-RAG sorgusu."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query(query, top_k, enable_reflection, enable_refinement)
        )
    
    def _retrieve_and_evaluate(
        self,
        query: str,
        top_k: int
    ) -> List[RetrievedPassage]:
        """Retrieve ve evaluate."""
        # Retrieve
        context = self._retriever.retrieve(query=query, top_k=top_k)
        
        # Convert to RetrievedPassage
        passages = []
        for chunk in context.chunks:
            passage = RetrievedPassage(
                id=chunk.id,
                content=chunk.content,
                score=chunk.score,
                source=chunk.source,
                page_number=chunk.page_number,
            )
            
            # Evaluate
            passage = self.passage_evaluator.evaluate_passage(query, passage, passages)
            passages.append(passage)
        
        # Sort by combined score
        passages.sort(key=lambda p: p.combined_score(), reverse=True)
        
        return passages
    
    def _deduplicate_passages(
        self,
        passages: List[RetrievedPassage]
    ) -> List[RetrievedPassage]:
        """Duplicate pasajları kaldır."""
        seen = set()
        unique = []
        
        for p in passages:
            content_hash = hashlib.md5(p.content[:100].encode()).hexdigest()
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(p)
        
        return unique
    
    def _calculate_confidence(
        self,
        passages: List[RetrievedPassage],
        segments: List[GeneratedSegment]
    ) -> float:
        """Confidence hesapla."""
        if not passages:
            return 0.3
        
        # Passage quality
        passage_scores = [p.combined_score() for p in passages[:5]]
        avg_passage_score = sum(passage_scores) / len(passage_scores) if passage_scores else 0.0
        
        # Segment support
        if segments:
            supported_count = sum(1 for s in segments if s.supporting_passages)
            support_ratio = supported_count / len(segments)
        else:
            support_ratio = 0.5
        
        # Combined confidence
        confidence = 0.5 * avg_passage_score + 0.5 * support_ratio
        
        return round(confidence, 3)
    
    def _update_stats(self, quality: float, refinements: int):
        """İstatistikleri güncelle."""
        self._query_count += 1
        n = self._query_count
        self._avg_quality = (self._avg_quality * (n - 1) + quality) / n
        self._refinement_count += refinements
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        return {
            "query_count": self._query_count,
            "avg_quality": round(self._avg_quality, 3),
            "total_refinements": self._refinement_count,
            "avg_refinements_per_query": self._refinement_count / max(self._query_count, 1),
        }


# =============================================================================
# SINGLETON
# =============================================================================

_self_rag: Optional[SelfRAG] = None


def get_self_rag() -> SelfRAG:
    """Singleton SelfRAG instance."""
    global _self_rag
    
    if _self_rag is None:
        _self_rag = SelfRAG()
    
    return _self_rag


self_rag = SelfRAG()


__all__ = [
    "SelfRAG",
    "SelfRAGResponse",
    "RetrievedPassage",
    "GeneratedSegment",
    "ReflectionResult",
    "CritiqueResult",
    "RetrievalDecision",
    "SupportLevel",
    "RelevanceLevel",
    "UsefulnessLevel",
    "QualityDimension",
    "self_rag",
    "get_self_rag",
]
