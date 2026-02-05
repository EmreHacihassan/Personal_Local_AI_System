"""
🔄 CRAG - Corrective RAG System
==============================

Self-correcting RAG implementation:
- Relevance grading
- Query transformation  
- Web search fallback
- Hallucination detection
- Iterative refinement

Based on: "Corrective Retrieval-Augmented Generation" paper
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class RelevanceGrade(str, Enum):
    """Document relevance grades"""
    HIGHLY_RELEVANT = "highly_relevant"  # Perfect match
    RELEVANT = "relevant"  # Good match
    PARTIALLY_RELEVANT = "partially_relevant"  # Some useful info
    NOT_RELEVANT = "not_relevant"  # No useful info
    AMBIGUOUS = "ambiguous"  # Unclear


class CorrectionAction(str, Enum):
    """Correction actions for low relevance"""
    NONE = "none"  # No correction needed
    REFORMULATE = "reformulate"  # Rewrite query
    DECOMPOSE = "decompose"  # Break into sub-queries
    EXPAND = "expand"  # Add related terms
    WEB_SEARCH = "web_search"  # Fall back to web
    USE_GENERAL_KNOWLEDGE = "use_general_knowledge"  # Fall back to LLM general knowledge
    GIVE_UP = "give_up"  # Cannot answer (for personal data queries only)


class HallucinationRisk(str, Enum):
    """Hallucination risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============ DATA MODELS ============

@dataclass
class GradedDocument:
    """Document with relevance grade"""
    content: str
    source: str
    page: Optional[int] = None
    grade: RelevanceGrade = RelevanceGrade.AMBIGUOUS
    relevance_score: float = 0.0
    key_matches: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CRAGResult:
    """Result from CRAG pipeline"""
    query: str
    final_query: str
    answer: str
    graded_documents: List[GradedDocument]
    used_documents: List[GradedDocument]
    corrections_applied: List[CorrectionAction]
    iterations: int
    hallucination_risk: HallucinationRisk
    confidence: float
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class QueryAnalysis(BaseModel):
    """Query analysis result"""
    original_query: str
    query_type: str = Field(description="factual, analytical, comparative, etc.")
    key_concepts: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    temporal_context: Optional[str] = None
    required_knowledge: List[str] = Field(default_factory=list)
    ambiguity_level: float = Field(0.0, ge=0.0, le=1.0)


class ReformulatedQuery(BaseModel):
    """Reformulated query with variants"""
    original: str
    reformulated: str
    variants: List[str] = Field(default_factory=list, description="Alternative phrasings")
    expansion_terms: List[str] = Field(default_factory=list)
    reasoning: str = ""


# ============ CRAG COMPONENTS ============

class RelevanceGrader:
    """
    Grade document relevance to query.
    
    Uses multiple signals:
    - Semantic similarity
    - Keyword overlap
    - Entity matching
    - LLM-based grading (optional)
    """
    
    def __init__(
        self,
        llm_grader: Optional[Callable] = None,
        relevance_threshold: float = 0.5,
        use_llm: bool = True
    ):
        self.llm_grader = llm_grader
        self.relevance_threshold = relevance_threshold
        self.use_llm = use_llm
    
    async def grade_documents(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        query_analysis: Optional[QueryAnalysis] = None
    ) -> List[GradedDocument]:
        """Grade a list of documents"""
        graded = []
        
        for doc in documents:
            graded_doc = await self.grade_document(query, doc, query_analysis)
            graded.append(graded_doc)
        
        # Sort by relevance
        graded.sort(key=lambda d: d.relevance_score, reverse=True)
        
        return graded
    
    async def grade_document(
        self,
        query: str,
        document: Dict[str, Any],
        query_analysis: Optional[QueryAnalysis] = None
    ) -> GradedDocument:
        """Grade a single document"""
        content = document.get("content", document.get("document", ""))
        source = document.get("source", document.get("metadata", {}).get("source", "unknown"))
        page = document.get("page_number", document.get("metadata", {}).get("page_number"))
        
        # Basic scoring
        score, matches = self._calculate_keyword_score(query, content, query_analysis)
        
        # LLM grading if enabled and available
        if self.use_llm and self.llm_grader:
            llm_score = await self._llm_grade(query, content)
            score = (score + llm_score) / 2
        
        # Determine grade
        grade = self._score_to_grade(score)
        
        return GradedDocument(
            content=content,
            source=source,
            page=page,
            grade=grade,
            relevance_score=score,
            key_matches=matches,
            metadata=document.get("metadata", {})
        )
    
    def _calculate_keyword_score(
        self,
        query: str,
        content: str,
        analysis: Optional[QueryAnalysis]
    ) -> Tuple[float, List[str]]:
        """Calculate keyword-based relevance score"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Extract query terms
        query_terms = set(re.findall(r'\b\w{3,}\b', query_lower))
        
        # Add analysis concepts if available
        if analysis:
            query_terms.update(c.lower() for c in analysis.key_concepts)
            query_terms.update(e.lower() for e in analysis.entities)
        
        # Find matches
        matches = []
        match_count = 0
        
        for term in query_terms:
            if term in content_lower:
                matches.append(term)
                match_count += content_lower.count(term)
        
        # Calculate score
        if not query_terms:
            return 0.0, []
        
        coverage = len(matches) / len(query_terms)
        density = min(1.0, match_count / (len(content.split()) / 10))
        
        score = (coverage * 0.7) + (density * 0.3)
        
        return score, matches
    
    async def _llm_grade(self, query: str, content: str) -> float:
        """Use LLM to grade relevance"""
        if not self.llm_grader:
            return 0.5
        
        try:
            result = await self.llm_grader(
                query=query,
                content=content[:2000]  # Truncate for efficiency
            )
            return float(result)
        except Exception as e:
            logger.warning(f"LLM grading failed: {e}")
            return 0.5
    
    def _score_to_grade(self, score: float) -> RelevanceGrade:
        """Convert score to grade"""
        if score >= 0.8:
            return RelevanceGrade.HIGHLY_RELEVANT
        elif score >= 0.6:
            return RelevanceGrade.RELEVANT
        elif score >= 0.4:
            return RelevanceGrade.PARTIALLY_RELEVANT
        elif score >= 0.2:
            return RelevanceGrade.AMBIGUOUS
        else:
            return RelevanceGrade.NOT_RELEVANT


class QueryTransformer:
    """
    Transform queries for better retrieval.
    
    Strategies:
    - Reformulation: Rewrite for clarity
    - Decomposition: Break into sub-queries
    - Expansion: Add related terms
    - HyDE: Hypothetical document generation
    """
    
    def __init__(self, llm_transformer: Optional[Callable] = None):
        self.llm_transformer = llm_transformer
    
    async def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze query to understand intent and components"""
        # Basic analysis
        words = query.lower().split()
        
        # Detect query type
        if any(w in words for w in ["what", "who", "when", "where", "which"]):
            query_type = "factual"
        elif any(w in words for w in ["how", "why", "explain"]):
            query_type = "analytical"
        elif any(w in words for w in ["compare", "difference", "versus", "vs"]):
            query_type = "comparative"
        elif any(w in words for w in ["should", "best", "recommend"]):
            query_type = "advisory"
        else:
            query_type = "general"
        
        # Extract key concepts (simple heuristic)
        stop_words = {"what", "is", "the", "a", "an", "how", "do", "does", "can", "will", "should"}
        concepts = [w for w in words if w not in stop_words and len(w) > 2]
        
        return QueryAnalysis(
            original_query=query,
            query_type=query_type,
            key_concepts=concepts[:5],
            ambiguity_level=0.5 if len(concepts) < 2 else 0.2
        )
    
    async def reformulate(
        self,
        query: str,
        analysis: QueryAnalysis,
        feedback: Optional[str] = None
    ) -> ReformulatedQuery:
        """Reformulate query for better retrieval"""
        if self.llm_transformer:
            try:
                return await self._llm_reformulate(query, analysis, feedback)
            except Exception as e:
                logger.warning(f"LLM reformulation failed: {e}")
        
        # Fallback: Simple reformulation
        reformulated = query
        variants = []
        expansions = []
        
        # Add question variations
        if analysis.query_type == "factual":
            variants.append(f"definition of {' '.join(analysis.key_concepts)}")
            variants.append(f"{' '.join(analysis.key_concepts)} explained")
        
        # Add concept expansions
        expansions = analysis.key_concepts.copy()
        
        return ReformulatedQuery(
            original=query,
            reformulated=reformulated,
            variants=variants[:3],
            expansion_terms=expansions,
            reasoning="Basic reformulation applied"
        )
    
    async def decompose(self, query: str, analysis: QueryAnalysis) -> List[str]:
        """Decompose complex query into sub-queries"""
        sub_queries = [query]  # Always include original
        
        # Simple decomposition based on conjunctions
        if " and " in query.lower():
            parts = query.lower().split(" and ")
            sub_queries.extend(parts)
        
        if " or " in query.lower():
            parts = query.lower().split(" or ")
            sub_queries.extend(parts)
        
        # Question decomposition
        if analysis.query_type == "comparative":
            concepts = analysis.key_concepts
            if len(concepts) >= 2:
                sub_queries.append(f"What is {concepts[0]}?")
                sub_queries.append(f"What is {concepts[1]}?")
        
        return list(set(sub_queries))[:5]  # Limit to 5
    
    async def expand(self, query: str, analysis: QueryAnalysis) -> str:
        """Expand query with related terms"""
        expansions = analysis.key_concepts
        if expansions:
            expanded = f"{query} ({', '.join(expansions)})"
            return expanded
        return query
    
    async def _llm_reformulate(
        self,
        query: str,
        analysis: QueryAnalysis,
        feedback: Optional[str]
    ) -> ReformulatedQuery:
        """Use LLM to reformulate"""
        result = await self.llm_transformer(
            query=query,
            query_type=analysis.query_type,
            concepts=analysis.key_concepts,
            feedback=feedback
        )
        return ReformulatedQuery(**result)


class HallucinationDetector:
    """
    Detect potential hallucinations in generated answers.
    
    Checks:
    - Claim verification against sources
    - Factual consistency
    - Citation accuracy
    - Confidence signals
    """
    
    def __init__(self, llm_checker: Optional[Callable] = None):
        self.llm_checker = llm_checker
    
    async def check_answer(
        self,
        answer: str,
        sources: List[GradedDocument],
        query: str
    ) -> Tuple[HallucinationRisk, List[str]]:
        """
        Check answer for potential hallucinations.
        
        Returns:
            Tuple of (risk level, list of concerns)
        """
        concerns = []
        risk_score = 0.0
        
        # Check 1: Answer length vs source content
        total_source_len = sum(len(s.content) for s in sources)
        if len(answer) > total_source_len * 0.5 and len(answer) > 500:
            concerns.append("Answer significantly longer than source material")
            risk_score += 0.2
        
        # Check 2: Claims without source support
        unsupported = self._find_unsupported_claims(answer, sources)
        if unsupported:
            concerns.extend(unsupported[:3])
            risk_score += 0.1 * len(unsupported)
        
        # Check 3: Numeric claims
        numbers_in_answer = re.findall(r'\b\d+(?:\.\d+)?(?:%|percent)?\b', answer)
        if numbers_in_answer:
            verified = self._verify_numbers(numbers_in_answer, sources)
            if verified < 0.5:
                concerns.append(f"Unverified numeric claims: {numbers_in_answer[:3]}")
                risk_score += 0.3
        
        # Check 4: Hedging language (indicates uncertainty)
        hedge_words = ["might", "possibly", "perhaps", "seems", "appears", "likely"]
        hedge_count = sum(1 for w in hedge_words if w in answer.lower())
        if hedge_count > 3:
            concerns.append("High uncertainty language detected")
            risk_score += 0.1
        
        # Check 5: Source coverage
        if sources:
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources)
            if avg_relevance < 0.4:
                concerns.append("Low source relevance - answer may be extrapolated")
                risk_score += 0.3
        else:
            concerns.append("No sources provided - high hallucination risk")
            risk_score += 0.5
        
        # LLM-based checking if available
        if self.llm_checker:
            try:
                llm_concerns = await self.llm_checker(
                    answer=answer,
                    sources=[s.content for s in sources],
                    query=query
                )
                concerns.extend(llm_concerns)
                risk_score += 0.1 * len(llm_concerns)
            except Exception as e:
                logger.warning(f"LLM hallucination check failed: {e}")
        
        # Determine risk level
        risk = self._score_to_risk(min(1.0, risk_score))
        
        return risk, concerns
    
    def _find_unsupported_claims(
        self,
        answer: str,
        sources: List[GradedDocument]
    ) -> List[str]:
        """Find claims in answer not supported by sources"""
        unsupported = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]', answer)
        source_text = " ".join(s.content.lower() for s in sources)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Extract key terms from sentence
            terms = re.findall(r'\b\w{4,}\b', sentence.lower())
            
            # Check if key terms appear in sources
            matched = sum(1 for t in terms if t in source_text)
            coverage = matched / len(terms) if terms else 0
            
            if coverage < 0.3:
                unsupported.append(f"Potentially unsupported: '{sentence[:50]}...'")
        
        return unsupported
    
    def _verify_numbers(
        self,
        numbers: List[str],
        sources: List[GradedDocument]
    ) -> float:
        """Verify numeric claims against sources"""
        if not numbers:
            return 1.0
        
        source_text = " ".join(s.content for s in sources)
        verified = sum(1 for n in numbers if n in source_text)
        
        return verified / len(numbers)
    
    def _score_to_risk(self, score: float) -> HallucinationRisk:
        """Convert score to risk level"""
        if score >= 0.7:
            return HallucinationRisk.CRITICAL
        elif score >= 0.5:
            return HallucinationRisk.HIGH
        elif score >= 0.3:
            return HallucinationRisk.MEDIUM
        else:
            return HallucinationRisk.LOW


# ============ CRAG PIPELINE ============

class CRAGPipeline:
    """
    Full Corrective RAG Pipeline.
    
    Implements self-correcting retrieval-augmented generation:
    1. Query analysis and transformation
    2. Document retrieval
    3. Relevance grading
    4. Correction loop if needed
    5. Answer generation
    6. Hallucination check
    7. Final refinement
    """
    
    def __init__(
        self,
        retriever: Callable,
        generator: Callable,
        grader: Optional[RelevanceGrader] = None,
        transformer: Optional[QueryTransformer] = None,
        hallucination_detector: Optional[HallucinationDetector] = None,
        web_searcher: Optional[Callable] = None,
        max_iterations: int = 3,
        min_relevant_docs: int = 2,
        relevance_threshold: float = 0.5
    ):
        self.retriever = retriever
        self.generator = generator
        self.grader = grader or RelevanceGrader()
        self.transformer = transformer or QueryTransformer()
        self.hallucination_detector = hallucination_detector or HallucinationDetector()
        self.web_searcher = web_searcher
        self.max_iterations = max_iterations
        self.min_relevant_docs = min_relevant_docs
        self.relevance_threshold = relevance_threshold
    
    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CRAGResult:
        """
        Run the full CRAG pipeline.
        
        Args:
            query: User query
            context: Optional context (conversation history, etc.)
            
        Returns:
            CRAGResult with answer and metadata
        """
        context = context or {}
        corrections_applied = []
        iteration = 0
        all_graded_docs: List[GradedDocument] = []
        
        # Step 1: Analyze query
        analysis = await self.transformer.analyze_query(query)
        current_query = query
        
        logger.info(f"CRAG: Starting with query type '{analysis.query_type}'")
        
        # Step 2: Iterative retrieval and correction
        while iteration < self.max_iterations:
            iteration += 1
            
            logger.info(f"CRAG: Iteration {iteration}, query: {current_query[:50]}...")
            
            # Retrieve documents
            docs = await self.retriever(current_query)
            
            # Grade documents
            graded = await self.grader.grade_documents(current_query, docs, analysis)
            all_graded_docs.extend(graded)
            
            # Filter relevant docs
            relevant_docs = [
                d for d in graded 
                if d.relevance_score >= self.relevance_threshold
            ]
            
            logger.info(f"CRAG: Found {len(relevant_docs)}/{len(graded)} relevant documents")
            
            # Check if we have enough relevant documents
            if len(relevant_docs) >= self.min_relevant_docs:
                break
            
            # Determine correction action
            action = self._determine_correction(
                relevant_count=len(relevant_docs),
                iteration=iteration,
                analysis=analysis
            )
            
            corrections_applied.append(action)
            
            if action == CorrectionAction.NONE:
                break
            elif action == CorrectionAction.GIVE_UP:
                logger.warning("CRAG: Giving up - cannot find relevant documents for personal data query")
                break
            elif action == CorrectionAction.USE_GENERAL_KNOWLEDGE:
                logger.info("CRAG: Falling back to general knowledge - no relevant documents for general query")
                # Continue to generation step with empty context - LLM will use general knowledge
                break
            elif action == CorrectionAction.WEB_SEARCH:
                if self.web_searcher:
                    web_docs = await self.web_searcher(query)
                    all_graded_docs.extend(
                        await self.grader.grade_documents(query, web_docs, analysis)
                    )
                break
            elif action == CorrectionAction.REFORMULATE:
                reformulated = await self.transformer.reformulate(
                    current_query, analysis,
                    feedback="Previous retrieval found low relevance documents"
                )
                current_query = reformulated.reformulated
            elif action == CorrectionAction.DECOMPOSE:
                sub_queries = await self.transformer.decompose(current_query, analysis)
                # Retrieve for each sub-query
                for sq in sub_queries[1:]:  # Skip original
                    sub_docs = await self.retriever(sq)
                    all_graded_docs.extend(
                        await self.grader.grade_documents(sq, sub_docs, analysis)
                    )
            elif action == CorrectionAction.EXPAND:
                current_query = await self.transformer.expand(current_query, analysis)
        
        # Step 3: Select best documents for generation
        unique_docs = self._deduplicate_docs(all_graded_docs)
        used_docs = sorted(unique_docs, key=lambda d: d.relevance_score, reverse=True)
        used_docs = [d for d in used_docs if d.relevance_score >= 0.3][:30]  # Top 30
        
        # Step 4: Generate answer
        context_text = "\n\n".join(
            f"[Source: {d.source}, Page: {d.page or '?'}]\n{d.content}"
            for d in used_docs
        )
        
        answer = await self.generator(
            query=query,
            context=context_text
        )
        
        # Step 5: Check for hallucinations
        risk, concerns = await self.hallucination_detector.check_answer(
            answer, used_docs, query
        )
        
        # Step 6: Build citations
        citations = self._build_citations(answer, used_docs)
        
        # Step 7: Calculate confidence
        confidence = self._calculate_confidence(
            relevant_docs=used_docs,
            hallucination_risk=risk,
            iterations=iteration
        )
        
        return CRAGResult(
            query=query,
            final_query=current_query,
            answer=answer,
            graded_documents=all_graded_docs,
            used_documents=used_docs,
            corrections_applied=corrections_applied,
            iterations=iteration,
            hallucination_risk=risk,
            confidence=confidence,
            citations=citations,
            metadata={
                "query_analysis": analysis.model_dump(),
                "hallucination_concerns": concerns,
                "total_docs_retrieved": len(all_graded_docs)
            }
        )
    
    def _determine_correction(
        self,
        relevant_count: int,
        iteration: int,
        analysis: QueryAnalysis
    ) -> CorrectionAction:
        """Determine what correction action to take"""
        if relevant_count >= self.min_relevant_docs:
            return CorrectionAction.NONE
        
        # Check if query is likely about personal data (requires KB)
        personal_data_indicators = [
            "dosya", "belge", "kayıt", "not", "yüklediğim", "eklediğim",
            "my files", "my documents", "my notes", "uploaded", "added",
            "benim", "kendi", "bendeki", "arşiv"
        ]
        is_personal_query = any(
            indicator in analysis.original_query.lower() 
            for indicator in personal_data_indicators
        )
        
        if iteration >= self.max_iterations:
            # For personal data queries, give up if no documents found
            # For general queries, use LLM's built-in knowledge
            if is_personal_query:
                return CorrectionAction.GIVE_UP
            else:
                return CorrectionAction.USE_GENERAL_KNOWLEDGE
        
        # Choose correction based on iteration and query type
        if iteration == 1:
            return CorrectionAction.REFORMULATE
        elif iteration == 2:
            if analysis.query_type == "comparative":
                return CorrectionAction.DECOMPOSE
            else:
                return CorrectionAction.EXPAND
        else:
            if self.web_searcher:
                return CorrectionAction.WEB_SEARCH
            # Final fallback: general knowledge for non-personal queries
            if is_personal_query:
                return CorrectionAction.GIVE_UP
            else:
                return CorrectionAction.USE_GENERAL_KNOWLEDGE
    
    def _deduplicate_docs(self, docs: List[GradedDocument]) -> List[GradedDocument]:
        """Remove duplicate documents"""
        seen = set()
        unique = []
        
        for doc in docs:
            # Use content hash for dedup
            content_hash = hash(doc.content[:500])
            if content_hash not in seen:
                seen.add(content_hash)
                unique.append(doc)
        
        return unique
    
    def _build_citations(
        self,
        answer: str,
        docs: List[GradedDocument]
    ) -> List[Dict[str, Any]]:
        """Build citations for the answer"""
        citations = []
        
        for i, doc in enumerate(docs):
            citations.append({
                "id": i + 1,
                "source": doc.source,
                "page": doc.page,
                "relevance_score": doc.relevance_score,
                "excerpt": doc.content[:200] + "..."
            })
        
        return citations
    
    def _calculate_confidence(
        self,
        relevant_docs: List[GradedDocument],
        hallucination_risk: HallucinationRisk,
        iterations: int
    ) -> float:
        """Calculate overall confidence score"""
        # Base score from document relevance
        if relevant_docs:
            avg_relevance = sum(d.relevance_score for d in relevant_docs) / len(relevant_docs)
        else:
            avg_relevance = 0.0
        
        # Penalty for hallucination risk
        risk_penalty = {
            HallucinationRisk.LOW: 0.0,
            HallucinationRisk.MEDIUM: 0.15,
            HallucinationRisk.HIGH: 0.35,
            HallucinationRisk.CRITICAL: 0.6
        }[hallucination_risk]
        
        # Penalty for multiple iterations
        iteration_penalty = (iterations - 1) * 0.05
        
        confidence = avg_relevance - risk_penalty - iteration_penalty
        return max(0.0, min(1.0, confidence))


# ============ EXPORTS ============

__all__ = [
    # Types
    "RelevanceGrade",
    "CorrectionAction",
    "HallucinationRisk",
    # Data models
    "GradedDocument",
    "CRAGResult",
    "QueryAnalysis",
    "ReformulatedQuery",
    # Components
    "RelevanceGrader",
    "QueryTransformer",
    "HallucinationDetector",
    # Pipeline
    "CRAGPipeline",
]
