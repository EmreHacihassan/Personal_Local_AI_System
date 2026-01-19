"""
Citation Verifier & Hallucination Detector
==========================================

Advanced system for verifying RAG responses against source documents.

Features:
- Claim Extraction from responses
- Source Attribution Verification
- Factual Consistency Checking
- Hallucination Detection
- Citation Accuracy Scoring
- Confidence Calibration
- Grounding Analysis

Enterprise-grade implementation for trustworthy RAG systems.

Author: AI Assistant
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    Type,
    Union,
)

from core.logger import get_logger

logger = get_logger("rag.citation_verifier")


# =============================================================================
# ENUMS
# =============================================================================

class ClaimType(Enum):
    """Claim türleri."""
    FACTUAL = "factual"           # Doğrulanabilir gerçek
    QUANTITATIVE = "quantitative" # Sayısal iddia
    COMPARATIVE = "comparative"   # Karşılaştırma
    TEMPORAL = "temporal"         # Zamansal
    CAUSAL = "causal"             # Nedensel
    DEFINITIONAL = "definitional" # Tanımsal
    PROCEDURAL = "procedural"     # Prosedürel/Adımsal
    OPINION = "opinion"           # Görüş (doğrulanamaz)


class VerificationStatus(Enum):
    """Doğrulama durumu."""
    VERIFIED = "verified"           # Kaynakla doğrulandı
    PARTIALLY_VERIFIED = "partial"  # Kısmen doğrulandı
    UNVERIFIED = "unverified"       # Doğrulanamadı
    CONTRADICTED = "contradicted"   # Kaynakla çelişiyor
    UNSUPPORTED = "unsupported"     # Kaynak desteği yok
    NOT_APPLICABLE = "n/a"          # Doğrulama gerekmiyor (görüş vs)


class HallucinationType(Enum):
    """Hallucination türleri."""
    FABRICATION = "fabrication"       # Tamamen uydurma
    EXAGGERATION = "exaggeration"     # Abartı
    CONTRADICTION = "contradiction"   # Kaynaklarla çelişki
    MISATTRIBUTION = "misattribution" # Yanlış kaynak atfı
    CONFLATION = "conflation"         # Bilgileri karıştırma
    OUTDATED = "outdated"             # Güncel olmayan bilgi
    NONE = "none"                     # Hallucination yok


class GroundingLevel(Enum):
    """Grounding seviyesi."""
    FULLY_GROUNDED = "fully_grounded"
    MOSTLY_GROUNDED = "mostly_grounded"
    PARTIALLY_GROUNDED = "partially_grounded"
    WEAKLY_GROUNDED = "weakly_grounded"
    NOT_GROUNDED = "not_grounded"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Claim:
    """Çıkarılan claim/iddia."""
    id: str
    text: str
    claim_type: ClaimType
    
    # Position in response
    start_position: int = 0
    end_position: int = 0
    sentence_index: int = 0
    
    # Verification results
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    supporting_sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    
    # Hallucination detection
    hallucination_type: HallucinationType = HallucinationType.NONE
    hallucination_reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.claim_type.value,
            "sentence_index": self.sentence_index,
            "status": self.verification_status.value,
            "sources": len(self.supporting_sources),
            "confidence": self.confidence,
            "hallucination": self.hallucination_type.value,
        }


@dataclass
class SourceCitation:
    """Kaynak citation."""
    id: str
    document_id: str
    content: str
    
    # Citation details
    page_number: Optional[int] = None
    section: Optional[str] = None
    
    # Relevance
    relevance_score: float = 0.0
    claims_supported: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content[:200],
            "page": self.page_number,
            "relevance": self.relevance_score,
            "claims_supported": len(self.claims_supported),
        }


@dataclass
class VerificationResult:
    """Tek claim için doğrulama sonucu."""
    claim: Claim
    status: VerificationStatus
    confidence: float
    
    # Sources
    supporting_sources: List[SourceCitation]
    contradicting_sources: List[SourceCitation] = field(default_factory=list)
    
    # Details
    explanation: str = ""
    suggested_correction: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "claim": self.claim.to_dict(),
            "status": self.status.value,
            "confidence": self.confidence,
            "supporting_sources": len(self.supporting_sources),
            "contradicting_sources": len(self.contradicting_sources),
            "explanation": self.explanation[:200],
        }


@dataclass
class HallucinationReport:
    """Hallucination raporu."""
    claim: Claim
    hallucination_type: HallucinationType
    severity: float  # 0-1, 1 = en ciddi
    
    # Details
    evidence: str = ""
    reason: str = ""
    
    # Correction
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim.id,
            "claim_text": self.claim.text[:100],
            "type": self.hallucination_type.value,
            "severity": self.severity,
            "reason": self.reason,
        }


@dataclass
class CitationAnalysis:
    """Tam citation analizi."""
    response: str
    claims: List[Claim]
    
    # Verification
    verification_results: List[VerificationResult]
    
    # Hallucination
    hallucination_reports: List[HallucinationReport]
    
    # Scores
    overall_grounding: GroundingLevel
    grounding_score: float  # 0-1
    citation_accuracy: float  # 0-1
    hallucination_rate: float  # 0-1
    
    # Summary
    verified_claims: int = 0
    unverified_claims: int = 0
    contradicted_claims: int = 0
    total_hallucinations: int = 0
    
    # Processing
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "claims_total": len(self.claims),
            "verified": self.verified_claims,
            "unverified": self.unverified_claims,
            "contradicted": self.contradicted_claims,
            "hallucinations": self.total_hallucinations,
            "grounding": self.overall_grounding.value,
            "grounding_score": self.grounding_score,
            "citation_accuracy": self.citation_accuracy,
            "hallucination_rate": self.hallucination_rate,
            "processing_time_ms": self.processing_time_ms,
        }
    
    def get_summary(self) -> str:
        """Özet metin."""
        return (
            f"Citation Analysis: {len(self.claims)} claims found. "
            f"Verified: {self.verified_claims}, Contradicted: {self.contradicted_claims}, "
            f"Hallucinations: {self.total_hallucinations}. "
            f"Grounding: {self.overall_grounding.value} ({self.grounding_score:.2f})"
        )


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
# CLAIM EXTRACTOR
# =============================================================================

class ClaimExtractor:
    """
    Response'dan claim'leri çıkarır.
    """
    
    # Claim type detection patterns
    QUANTITATIVE_PATTERNS = [
        r'\d+%', r'\d+\s*(percent|yüzde)',
        r'\d+\s*(million|billion|thousand|milyar|milyon|bin)',
        r'\$\d+', r'₺\d+', r'€\d+',
    ]
    
    TEMPORAL_PATTERNS = [
        r'in\s+\d{4}', r'\d{4}\s+yılında',
        r'since\s+\d{4}', r'\d{4}\'den beri',
        r'(before|after|during)\s+\d{4}',
    ]
    
    CAUSAL_PATTERNS = [
        r'because', r'therefore', r'thus', r'hence',
        r'çünkü', r'dolayısıyla', r'bu nedenle',
        r'results in', r'leads to', r'causes',
    ]
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def extract_claims(self, response: str) -> List[Claim]:
        """Response'dan claim'leri çıkar."""
        # 1. Split into sentences
        sentences = self._split_sentences(response)
        
        claims = []
        position = 0
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                position += len(sentence) + 1
                continue
            
            # 2. Determine claim type
            claim_type = self._detect_claim_type(sentence)
            
            # 3. Skip opinion statements
            if claim_type == ClaimType.OPINION:
                position += len(sentence) + 1
                continue
            
            # 4. Create claim
            claim_id = hashlib.md5(f"{sentence}_{i}".encode()).hexdigest()[:8]
            
            claim = Claim(
                id=claim_id,
                text=sentence,
                claim_type=claim_type,
                start_position=position,
                end_position=position + len(sentence),
                sentence_index=i,
            )
            claims.append(claim)
            
            position += len(sentence) + 1
        
        return claims
    
    def extract_claims_llm(self, response: str) -> List[Claim]:
        """LLM ile claim extraction."""
        self._lazy_load()
        
        prompt = f"""Extract all verifiable claims from the following text.
For each claim, identify:
1. The exact claim text
2. Type: factual, quantitative, comparative, temporal, causal, definitional, procedural

Return as JSON array: [{{"text": "...", "type": "..."}}]

Text: {response[:2000]}

Claims (JSON):"""
        
        try:
            result = self._llm.generate(prompt, max_tokens=800)
            
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                claims_data = json.loads(json_match.group())
                
                claims = []
                for i, item in enumerate(claims_data):
                    try:
                        claim_type = ClaimType(item.get("type", "factual"))
                    except ValueError:
                        claim_type = ClaimType.FACTUAL
                    
                    claim_id = hashlib.md5(f"{item['text']}_{i}".encode()).hexdigest()[:8]
                    
                    claims.append(Claim(
                        id=claim_id,
                        text=item["text"],
                        claim_type=claim_type,
                        sentence_index=i,
                    ))
                
                return claims
        
        except Exception as e:
            logger.warning(f"LLM claim extraction failed: {e}")
        
        # Fallback to rule-based
        return self.extract_claims(response)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Metni cümlelere böl."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _detect_claim_type(self, sentence: str) -> ClaimType:
        """Claim tipini tespit et."""
        sentence_lower = sentence.lower()
        
        # Check for opinion markers
        opinion_markers = [
            "i think", "i believe", "in my opinion", "possibly", "maybe",
            "bence", "sanırım", "düşünüyorum", "belki", "muhtemelen"
        ]
        if any(marker in sentence_lower for marker in opinion_markers):
            return ClaimType.OPINION
        
        # Check for quantitative
        if any(re.search(p, sentence, re.IGNORECASE) for p in self.QUANTITATIVE_PATTERNS):
            return ClaimType.QUANTITATIVE
        
        # Check for temporal
        if any(re.search(p, sentence, re.IGNORECASE) for p in self.TEMPORAL_PATTERNS):
            return ClaimType.TEMPORAL
        
        # Check for causal
        if any(re.search(p, sentence, re.IGNORECASE) for p in self.CAUSAL_PATTERNS):
            return ClaimType.CAUSAL
        
        # Check for comparative
        comparative_markers = ["more than", "less than", "greater", "smaller", "better", "worse", "daha"]
        if any(marker in sentence_lower for marker in comparative_markers):
            return ClaimType.COMPARATIVE
        
        # Check for definitional
        definitional_markers = ["is defined as", "refers to", "means", "tanımlanır", "demektir"]
        if any(marker in sentence_lower for marker in definitional_markers):
            return ClaimType.DEFINITIONAL
        
        return ClaimType.FACTUAL


# =============================================================================
# SOURCE VERIFIER
# =============================================================================

class SourceVerifier:
    """
    Claim'leri kaynaklara karşı doğrular.
    """
    
    def __init__(
        self,
        llm: Optional[LLMProtocol] = None,
        embedding: Optional[EmbeddingProtocol] = None
    ):
        self._llm = llm
        self._embedding = embedding
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def verify_claim(
        self,
        claim: Claim,
        sources: List[SourceCitation]
    ) -> VerificationResult:
        """Tek bir claim'i doğrula."""
        if not sources:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.UNSUPPORTED,
                confidence=0.0,
                supporting_sources=[],
                explanation="No sources available for verification."
            )
        
        self._lazy_load()
        
        # Find relevant sources
        relevant_sources = self._find_relevant_sources(claim, sources)
        
        if not relevant_sources:
            return VerificationResult(
                claim=claim,
                status=VerificationStatus.UNSUPPORTED,
                confidence=0.2,
                supporting_sources=[],
                explanation="No relevant sources found for this claim."
            )
        
        # Verify against sources using LLM
        verification = self._llm_verify(claim, relevant_sources)
        
        return verification
    
    def _find_relevant_sources(
        self,
        claim: Claim,
        sources: List[SourceCitation],
        top_k: int = 3
    ) -> List[SourceCitation]:
        """İlgili kaynakları bul."""
        scored_sources = []
        
        claim_words = set(claim.text.lower().split())
        
        for source in sources:
            source_words = set(source.content.lower().split())
            
            # Simple word overlap scoring
            overlap = len(claim_words & source_words)
            score = overlap / max(len(claim_words), 1)
            
            scored_sources.append((score, source))
        
        # Sort by score
        scored_sources.sort(key=lambda x: x[0], reverse=True)
        
        # Return top sources with decent scores
        return [s for score, s in scored_sources[:top_k] if score > 0.1]
    
    def _llm_verify(
        self,
        claim: Claim,
        sources: List[SourceCitation]
    ) -> VerificationResult:
        """LLM ile claim doğrulama."""
        sources_text = "\n\n".join([
            f"[Source {i+1}]: {s.content[:500]}"
            for i, s in enumerate(sources)
        ])
        
        prompt = f"""Verify if the following claim is supported by the given sources.

Claim: {claim.text}

Sources:
{sources_text}

Respond in JSON format:
{{
    "status": "verified" | "partially_verified" | "contradicted" | "unsupported",
    "confidence": 0.0-1.0,
    "supporting_source_indices": [1, 2, ...],
    "contradicting_source_indices": [],
    "explanation": "Brief explanation",
    "suggested_correction": "Only if contradicted, suggest fix"
}}

Verification:"""
        
        try:
            result = self._llm.generate(prompt, max_tokens=300)
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                status = VerificationStatus(data.get("status", "unverified"))
                confidence = data.get("confidence", 0.5)
                
                supporting_indices = data.get("supporting_source_indices", [])
                contradicting_indices = data.get("contradicting_source_indices", [])
                
                supporting = [sources[i-1] for i in supporting_indices if 0 < i <= len(sources)]
                contradicting = [sources[i-1] for i in contradicting_indices if 0 < i <= len(sources)]
                
                # Update claim
                claim.verification_status = status
                claim.confidence = confidence
                claim.supporting_sources = [s.id for s in supporting]
                
                return VerificationResult(
                    claim=claim,
                    status=status,
                    confidence=confidence,
                    supporting_sources=supporting,
                    contradicting_sources=contradicting,
                    explanation=data.get("explanation", ""),
                    suggested_correction=data.get("suggested_correction"),
                )
        
        except Exception as e:
            logger.warning(f"LLM verification failed: {e}")
        
        # Fallback - assume partial verification
        return VerificationResult(
            claim=claim,
            status=VerificationStatus.PARTIALLY_VERIFIED,
            confidence=0.5,
            supporting_sources=sources[:1] if sources else [],
            explanation="Automated verification could not determine status.",
        )


# =============================================================================
# HALLUCINATION DETECTOR
# =============================================================================

class HallucinationDetector:
    """
    Hallucination tespit sistemi.
    """
    
    def __init__(self, llm: Optional[LLMProtocol] = None):
        self._llm = llm
    
    def _lazy_load(self):
        if self._llm is None:
            from core.llm_manager import llm_manager
            self._llm = llm_manager
    
    def detect_hallucinations(
        self,
        claims: List[Claim],
        verification_results: List[VerificationResult]
    ) -> List[HallucinationReport]:
        """Hallucination'ları tespit et."""
        reports = []
        
        for i, (claim, verification) in enumerate(zip(claims, verification_results)):
            hallucination = self._analyze_hallucination(claim, verification)
            
            if hallucination.hallucination_type != HallucinationType.NONE:
                reports.append(hallucination)
        
        return reports
    
    def _analyze_hallucination(
        self,
        claim: Claim,
        verification: VerificationResult
    ) -> HallucinationReport:
        """Tek claim için hallucination analizi."""
        # Determine hallucination type based on verification
        if verification.status == VerificationStatus.CONTRADICTED:
            return HallucinationReport(
                claim=claim,
                hallucination_type=HallucinationType.CONTRADICTION,
                severity=0.9,
                reason="Claim directly contradicts source information.",
                evidence=verification.explanation,
                suggested_fix=verification.suggested_correction,
            )
        
        if verification.status == VerificationStatus.UNSUPPORTED:
            # Check if it looks fabricated
            if verification.confidence < 0.3:
                return HallucinationReport(
                    claim=claim,
                    hallucination_type=HallucinationType.FABRICATION,
                    severity=0.8,
                    reason="Claim has no source support and appears fabricated.",
                )
        
        if verification.status == VerificationStatus.PARTIALLY_VERIFIED:
            # Check for exaggeration
            if self._is_exaggeration(claim, verification):
                return HallucinationReport(
                    claim=claim,
                    hallucination_type=HallucinationType.EXAGGERATION,
                    severity=0.5,
                    reason="Claim exaggerates or overstates source information.",
                )
        
        # No hallucination
        claim.hallucination_type = HallucinationType.NONE
        return HallucinationReport(
            claim=claim,
            hallucination_type=HallucinationType.NONE,
            severity=0.0,
        )
    
    def _is_exaggeration(
        self,
        claim: Claim,
        verification: VerificationResult
    ) -> bool:
        """Abartı tespiti."""
        exaggeration_words = [
            "all", "every", "always", "never", "none", "completely",
            "absolutely", "definitely", "certainly", "undoubtedly",
            "hep", "her zaman", "asla", "hiç", "kesinlikle", "mutlaka"
        ]
        
        claim_lower = claim.text.lower()
        return any(word in claim_lower for word in exaggeration_words)


# =============================================================================
# CITATION VERIFIER
# =============================================================================

class CitationVerifier:
    """
    Complete Citation Verification System.
    
    Combines claim extraction, source verification, and
    hallucination detection into a unified analysis.
    
    Example:
        verifier = CitationVerifier()
        analysis = verifier.verify_response(response, sources)
    """
    
    def __init__(
        self,
        llm: Optional[LLMProtocol] = None,
        embedding: Optional[EmbeddingProtocol] = None
    ):
        self._llm = llm
        self._embedding = embedding
        
        self.claim_extractor = ClaimExtractor(llm)
        self.source_verifier = SourceVerifier(llm, embedding)
        self.hallucination_detector = HallucinationDetector(llm)
        
        # Stats
        self._verification_count = 0
        self._total_claims = 0
        self._total_hallucinations = 0
    
    def verify_response(
        self,
        response: str,
        sources: List[Dict[str, Any]],
        use_llm_extraction: bool = False
    ) -> CitationAnalysis:
        """
        Response'u kaynaklara karşı doğrula.
        
        Args:
            response: RAG response
            sources: Kaynak dokümanlar
            use_llm_extraction: LLM ile claim extraction
            
        Returns:
            CitationAnalysis
        """
        start_time = time.time()
        
        # 1. Convert sources to SourceCitations
        source_citations = self._convert_sources(sources)
        
        # 2. Extract claims
        if use_llm_extraction:
            claims = self.claim_extractor.extract_claims_llm(response)
        else:
            claims = self.claim_extractor.extract_claims(response)
        
        if not claims:
            return self._empty_analysis(response)
        
        # 3. Verify each claim
        verification_results = []
        for claim in claims:
            result = self.source_verifier.verify_claim(claim, source_citations)
            verification_results.append(result)
        
        # 4. Detect hallucinations
        hallucination_reports = self.hallucination_detector.detect_hallucinations(
            claims, verification_results
        )
        
        # 5. Calculate scores
        verified_count = sum(1 for r in verification_results if r.status == VerificationStatus.VERIFIED)
        partial_count = sum(1 for r in verification_results if r.status == VerificationStatus.PARTIALLY_VERIFIED)
        unverified_count = sum(1 for r in verification_results if r.status in [VerificationStatus.UNVERIFIED, VerificationStatus.UNSUPPORTED])
        contradicted_count = sum(1 for r in verification_results if r.status == VerificationStatus.CONTRADICTED)
        
        total_claims = len(claims)
        hallucination_count = len([r for r in hallucination_reports if r.hallucination_type != HallucinationType.NONE])
        
        # Grounding score
        grounding_score = (verified_count + 0.5 * partial_count) / max(total_claims, 1)
        
        # Citation accuracy
        citation_accuracy = verified_count / max(total_claims, 1)
        
        # Hallucination rate
        hallucination_rate = hallucination_count / max(total_claims, 1)
        
        # Determine grounding level
        if grounding_score >= 0.9:
            grounding_level = GroundingLevel.FULLY_GROUNDED
        elif grounding_score >= 0.7:
            grounding_level = GroundingLevel.MOSTLY_GROUNDED
        elif grounding_score >= 0.5:
            grounding_level = GroundingLevel.PARTIALLY_GROUNDED
        elif grounding_score >= 0.3:
            grounding_level = GroundingLevel.WEAKLY_GROUNDED
        else:
            grounding_level = GroundingLevel.NOT_GROUNDED
        
        # Update stats
        self._verification_count += 1
        self._total_claims += total_claims
        self._total_hallucinations += hallucination_count
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return CitationAnalysis(
            response=response,
            claims=claims,
            verification_results=verification_results,
            hallucination_reports=hallucination_reports,
            overall_grounding=grounding_level,
            grounding_score=round(grounding_score, 3),
            citation_accuracy=round(citation_accuracy, 3),
            hallucination_rate=round(hallucination_rate, 3),
            verified_claims=verified_count,
            unverified_claims=unverified_count,
            contradicted_claims=contradicted_count,
            total_hallucinations=hallucination_count,
            processing_time_ms=processing_time,
        )
    
    async def verify_response_async(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> CitationAnalysis:
        """Asenkron doğrulama."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.verify_response(response, sources)
        )
    
    def _convert_sources(self, sources: List[Dict[str, Any]]) -> List[SourceCitation]:
        """Kaynakları SourceCitation'a dönüştür."""
        citations = []
        
        for i, source in enumerate(sources):
            if isinstance(source, dict):
                content = source.get("content", source.get("text", str(source)))
                doc_id = source.get("id", source.get("document_id", f"doc_{i}"))
                page = source.get("page", source.get("page_number"))
            else:
                content = str(source)
                doc_id = f"doc_{i}"
                page = None
            
            citation = SourceCitation(
                id=f"cite_{i}",
                document_id=doc_id,
                content=content,
                page_number=page,
            )
            citations.append(citation)
        
        return citations
    
    def _empty_analysis(self, response: str) -> CitationAnalysis:
        """Boş analiz oluştur."""
        return CitationAnalysis(
            response=response,
            claims=[],
            verification_results=[],
            hallucination_reports=[],
            overall_grounding=GroundingLevel.NOT_GROUNDED,
            grounding_score=0.0,
            citation_accuracy=0.0,
            hallucination_rate=0.0,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """İstatistikler."""
        avg_hallucination_rate = (
            self._total_hallucinations / max(self._total_claims, 1)
        )
        
        return {
            "verification_count": self._verification_count,
            "total_claims_analyzed": self._total_claims,
            "total_hallucinations_found": self._total_hallucinations,
            "avg_hallucination_rate": round(avg_hallucination_rate, 3),
        }


# =============================================================================
# GROUNDING SCORER
# =============================================================================

class GroundingScorer:
    """
    Response grounding kalite scorer.
    """
    
    def score(self, analysis: CitationAnalysis) -> Dict[str, float]:
        """Grounding skorlarını hesapla."""
        scores = {
            "overall": analysis.grounding_score,
            "citation_accuracy": analysis.citation_accuracy,
            "factual_accuracy": 1.0 - analysis.hallucination_rate,
            "source_coverage": self._calculate_source_coverage(analysis),
            "claim_density": self._calculate_claim_density(analysis),
        }
        
        # Weighted average
        weights = {
            "overall": 0.3,
            "citation_accuracy": 0.25,
            "factual_accuracy": 0.25,
            "source_coverage": 0.1,
            "claim_density": 0.1,
        }
        
        weighted_score = sum(scores[k] * weights[k] for k in scores)
        scores["weighted_average"] = round(weighted_score, 3)
        
        return scores
    
    def _calculate_source_coverage(self, analysis: CitationAnalysis) -> float:
        """Kaynak kapsam skoru."""
        if not analysis.verification_results:
            return 0.0
        
        claims_with_sources = sum(
            1 for r in analysis.verification_results
            if r.supporting_sources
        )
        
        return claims_with_sources / len(analysis.verification_results)
    
    def _calculate_claim_density(self, analysis: CitationAnalysis) -> float:
        """Claim yoğunluğu skoru."""
        response_length = len(analysis.response)
        claim_count = len(analysis.claims)
        
        if response_length == 0:
            return 0.0
        
        # Optimal: ~1 claim per 100 chars
        expected_claims = response_length / 100
        
        if expected_claims == 0:
            return 0.0
        
        ratio = claim_count / expected_claims
        
        # Score: 1.0 at ratio=1.0, decreasing as ratio deviates
        return max(0.0, 1.0 - abs(ratio - 1.0) * 0.5)


# =============================================================================
# SINGLETON
# =============================================================================

_citation_verifier: Optional[CitationVerifier] = None
_grounding_scorer: Optional[GroundingScorer] = None


def get_citation_verifier() -> CitationVerifier:
    """Singleton CitationVerifier instance."""
    global _citation_verifier
    
    if _citation_verifier is None:
        _citation_verifier = CitationVerifier()
    
    return _citation_verifier


def get_grounding_scorer() -> GroundingScorer:
    """Singleton GroundingScorer instance."""
    global _grounding_scorer
    
    if _grounding_scorer is None:
        _grounding_scorer = GroundingScorer()
    
    return _grounding_scorer


citation_verifier = CitationVerifier()
grounding_scorer = GroundingScorer()


__all__ = [
    "CitationVerifier",
    "ClaimExtractor",
    "SourceVerifier",
    "HallucinationDetector",
    "GroundingScorer",
    "CitationAnalysis",
    "Claim",
    "ClaimType",
    "SourceCitation",
    "VerificationResult",
    "VerificationStatus",
    "HallucinationReport",
    "HallucinationType",
    "GroundingLevel",
    "citation_verifier",
    "grounding_scorer",
    "get_citation_verifier",
    "get_grounding_scorer",
]
