"""
🔬 Deep Research 3.0 - Premium Research Engine
===============================================

Endüstri-seviyesi derinlemesine araştırma motoru.
Perplexity Pro, ChatGPT Deep Research kalitesinde.

Özellikler:
- Iterative Research Loop: 3-5 iterasyonlu derinlemesine araştırma
- Evidence Grading: Kanıt kalitesi değerlendirme
- Multi-Source Synthesis: Çoklu kaynak sentezi
- Fact Verification: Gerçek doğrulama
- Confidence Scoring: Güven skoru
- Progress Streaming: Gerçek zamanlı ilerleme
- Auto-Refinement: Otomatik iyileştirme
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator
import hashlib

logger = logging.getLogger(__name__)


# ============ ENUMS ============

class ResearchPhase(Enum):
    """Araştırma fazları"""
    PLANNING = "planning"
    SEARCHING = "searching"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    VERIFYING = "verifying"
    SYNTHESIZING = "synthesizing"
    REFINING = "refining"
    COMPLETE = "complete"


class EvidenceGrade(Enum):
    """Kanıt kalite seviyeleri"""
    A = "A"  # Çok güçlü (peer-reviewed, resmi kaynak)
    B = "B"  # Güçlü (güvenilir kaynak, tutarlı)
    C = "C"  # Orta (blog, forum ama destekli)
    D = "D"  # Zayıf (tek kaynak, doğrulanmamış)
    F = "F"  # Çok zayıf (çelişkili, güvenilmez)


class SourceReliability(Enum):
    """Kaynak güvenilirliği"""
    ACADEMIC = "academic"      # 0.95
    OFFICIAL = "official"      # 0.9
    NEWS = "news"              # 0.8
    DOCUMENTATION = "documentation"  # 0.85
    WIKI = "wiki"              # 0.8
    BLOG = "blog"              # 0.6
    FORUM = "forum"            # 0.5
    SOCIAL = "social"          # 0.4
    UNKNOWN = "unknown"        # 0.3


# ============ DATA CLASSES ============

@dataclass
class ResearchQuery:
    """Araştırma sorgusu"""
    original_query: str
    refined_queries: List[str] = field(default_factory=list)
    sub_questions: List[str] = field(default_factory=list)
    key_concepts: List[str] = field(default_factory=list)
    search_strategy: str = "comprehensive"


@dataclass
class Evidence:
    """Tek bir kanıt parçası"""
    content: str
    source_url: str
    source_title: str
    source_type: SourceReliability
    
    # Grading
    grade: EvidenceGrade = EvidenceGrade.C
    confidence: float = 0.5
    
    # Verification
    verified: bool = False
    supporting_sources: int = 0
    contradicting_sources: int = 0
    
    # Extraction info
    extraction_method: str = "content"
    relevance_score: float = 0.5
    
    # Metadata
    author: str = ""
    date: str = ""
    quote: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content[:500],
            "source_url": self.source_url,
            "source_title": self.source_title,
            "source_type": self.source_type.value,
            "grade": self.grade.value,
            "confidence": self.confidence,
            "verified": self.verified,
            "supporting_sources": self.supporting_sources,
        }


@dataclass
class Finding:
    """Araştırma bulgusu"""
    claim: str
    evidence: List[Evidence]
    confidence: float = 0.5
    grade: EvidenceGrade = EvidenceGrade.C
    
    # Analysis
    consensus: str = "unknown"  # "strong", "moderate", "weak", "disputed"
    nuance: str = ""
    caveats: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence_count": len(self.evidence),
            "confidence": self.confidence,
            "grade": self.grade.value,
            "consensus": self.consensus,
            "caveats": self.caveats,
        }


@dataclass
class ResearchProgress:
    """Araştırma ilerleme durumu"""
    phase: ResearchPhase
    iteration: int
    total_iterations: int
    message: str
    
    # Metrics
    sources_found: int = 0
    evidence_collected: int = 0
    findings_count: int = 0
    confidence: float = 0.0
    
    # Timing
    elapsed_seconds: float = 0.0
    estimated_remaining: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "iteration": self.iteration,
            "total_iterations": self.total_iterations,
            "message": self.message,
            "sources_found": self.sources_found,
            "evidence_collected": self.evidence_collected,
            "findings_count": self.findings_count,
            "confidence": self.confidence,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "estimated_remaining": round(self.estimated_remaining, 1),
            "progress_percent": int((self.iteration / max(1, self.total_iterations)) * 100),
        }


@dataclass
class ResearchReport:
    """Nihai araştırma raporu"""
    query: str
    executive_summary: str
    findings: List[Finding]
    
    # Quality metrics
    overall_confidence: float = 0.5
    overall_grade: EvidenceGrade = EvidenceGrade.C
    
    # Sources
    total_sources: int = 0
    sources_used: List[Dict[str, str]] = field(default_factory=list)
    
    # Analysis
    key_insights: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    further_research: List[str] = field(default_factory=list)
    
    # Metadata
    iterations: int = 0
    total_time_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "executive_summary": self.executive_summary,
            "findings": [f.to_dict() for f in self.findings],
            "overall_confidence": self.overall_confidence,
            "overall_grade": self.overall_grade.value,
            "total_sources": self.total_sources,
            "key_insights": self.key_insights,
            "limitations": self.limitations,
            "further_research": self.further_research,
            "iterations": self.iterations,
            "total_time_seconds": round(self.total_time_seconds, 1),
            "timestamp": self.timestamp,
        }


# ============ EVIDENCE GRADER ============

class EvidenceGrader:
    """
    Kanıt kalitesi değerlendirici.
    
    Evidence-based medicine scoring sisteminden esinlenilmiştir.
    """
    
    # Source reliability scores
    SOURCE_SCORES = {
        SourceReliability.ACADEMIC: 0.95,
        SourceReliability.OFFICIAL: 0.90,
        SourceReliability.DOCUMENTATION: 0.85,
        SourceReliability.WIKI: 0.80,
        SourceReliability.NEWS: 0.75,
        SourceReliability.BLOG: 0.55,
        SourceReliability.FORUM: 0.45,
        SourceReliability.SOCIAL: 0.35,
        SourceReliability.UNKNOWN: 0.30,
    }
    
    def grade_evidence(self, evidence: Evidence) -> EvidenceGrade:
        """Tek bir kanıtı değerlendir"""
        score = self._calculate_score(evidence)
        
        if score >= 0.85:
            return EvidenceGrade.A
        elif score >= 0.70:
            return EvidenceGrade.B
        elif score >= 0.55:
            return EvidenceGrade.C
        elif score >= 0.35:
            return EvidenceGrade.D
        else:
            return EvidenceGrade.F
    
    def _calculate_score(self, evidence: Evidence) -> float:
        """Kanıt skoru hesapla"""
        score = 0.0
        
        # 1. Source reliability (40%)
        source_score = self.SOURCE_SCORES.get(evidence.source_type, 0.3)
        score += source_score * 0.40
        
        # 2. Verification status (25%)
        if evidence.verified:
            score += 0.25
        elif evidence.supporting_sources > 0:
            support_ratio = evidence.supporting_sources / max(1, evidence.supporting_sources + evidence.contradicting_sources)
            score += support_ratio * 0.25
        
        # 3. Content quality (20%)
        content_score = self._assess_content_quality(evidence.content)
        score += content_score * 0.20
        
        # 4. Recency if date available (10%)
        if evidence.date:
            recency_score = self._assess_recency(evidence.date)
            score += recency_score * 0.10
        else:
            score += 0.05  # Neutral
        
        # 5. Relevance (5%)
        score += evidence.relevance_score * 0.05
        
        return min(1.0, score)
    
    def _assess_content_quality(self, content: str) -> float:
        """İçerik kalitesini değerlendir"""
        score = 0.5
        
        # Length check
        word_count = len(content.split())
        if word_count > 100:
            score += 0.1
        if word_count > 300:
            score += 0.1
        
        # Has specific data (numbers, dates)
        if re.search(r'\d+', content):
            score += 0.1
        
        # Has citations or references
        if any(w in content.lower() for w in ['according to', 'study', 'research', 'göre', 'araştırma']):
            score += 0.1
        
        return min(1.0, score)
    
    def _assess_recency(self, date_str: str) -> float:
        """Güncellik değerlendir"""
        try:
            # Simple year extraction
            year_match = re.search(r'20\d{2}', date_str)
            if year_match:
                year = int(year_match.group())
                current_year = datetime.now().year
                age = current_year - year
                
                if age <= 1:
                    return 1.0
                elif age <= 3:
                    return 0.8
                elif age <= 5:
                    return 0.6
                else:
                    return 0.4
        except Exception:
            pass
        return 0.5
    
    def grade_findings(self, finding: Finding) -> Tuple[EvidenceGrade, float]:
        """Bulguyu değerlendir"""
        if not finding.evidence:
            return EvidenceGrade.F, 0.0
        
        # Average evidence grades
        grades = [e.grade for e in finding.evidence]
        grade_scores = {
            EvidenceGrade.A: 1.0,
            EvidenceGrade.B: 0.8,
            EvidenceGrade.C: 0.6,
            EvidenceGrade.D: 0.4,
            EvidenceGrade.F: 0.2,
        }
        
        avg_score = sum(grade_scores.get(g, 0.5) for g in grades) / len(grades)
        
        # Bonus for multiple supporting sources
        if len(finding.evidence) >= 3:
            avg_score += 0.05
        if len(finding.evidence) >= 5:
            avg_score += 0.05
        
        # Penalty for contradicting sources
        total_contradicting = sum(e.contradicting_sources for e in finding.evidence)
        if total_contradicting > 0:
            avg_score -= 0.1
        
        avg_score = max(0.0, min(1.0, avg_score))
        
        # Determine final grade
        if avg_score >= 0.85:
            return EvidenceGrade.A, avg_score
        elif avg_score >= 0.70:
            return EvidenceGrade.B, avg_score
        elif avg_score >= 0.55:
            return EvidenceGrade.C, avg_score
        elif avg_score >= 0.35:
            return EvidenceGrade.D, avg_score
        else:
            return EvidenceGrade.F, avg_score


# ============ RESEARCH PLANNER ============

class ResearchPlanner:
    """
    Araştırma planlayıcı.
    
    Sorguyu analiz eder ve araştırma stratejisi oluşturur.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def plan(self, query: str) -> ResearchQuery:
        """Araştırma planı oluştur"""
        # Analyze query
        key_concepts = self._extract_concepts(query)
        sub_questions = await self._generate_sub_questions(query)
        refined_queries = self._generate_search_queries(query, key_concepts)
        
        return ResearchQuery(
            original_query=query,
            refined_queries=refined_queries,
            sub_questions=sub_questions,
            key_concepts=key_concepts,
            search_strategy=self._determine_strategy(query),
        )
    
    def _extract_concepts(self, query: str) -> List[str]:
        """Anahtar kavramları çıkar"""
        # Simple keyword extraction
        stop_words = {"bir", "ve", "veya", "ile", "için", "bu", "şu", "ne", "nasıl", "neden", 
                      "the", "a", "an", "is", "are", "what", "how", "why"}
        
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]{3,}\b', query.lower())
        concepts = [w for w in words if w not in stop_words]
        
        # Deduplicate while preserving order
        seen = set()
        unique_concepts = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique_concepts.append(c)
        
        return unique_concepts[:10]
    
    async def _generate_sub_questions(self, query: str) -> List[str]:
        """Alt sorular oluştur"""
        prompt = f"""Break down this research question into 3-5 specific sub-questions 
that need to be answered for comprehensive understanding.

Main Question: {query}

Sub-questions (one per line):"""
        
        try:
            response = await self._call_llm(prompt)
            questions = [q.strip() for q in response.split('\n') if q.strip() and '?' in q]
            return questions[:5]
        except Exception:
            # Fallback
            return [
                f"{query} nedir?",
                f"{query} nasıl çalışır?",
                f"{query} örnekleri nelerdir?",
            ]
    
    def _generate_search_queries(self, query: str, concepts: List[str]) -> List[str]:
        """Arama sorguları oluştur"""
        queries = [query]
        
        # Add concept-focused queries
        for concept in concepts[:3]:
            queries.append(f"{concept} guide")
            queries.append(f"{concept} explained")
        
        # Add Turkish variants
        if any(c in query for c in 'ğüşıöçĞÜŞİÖÇ'):
            queries.append(f"{query} nedir")
            queries.append(f"{query} nasıl")
        
        return queries[:8]
    
    def _determine_strategy(self, query: str) -> str:
        """Araştırma stratejisi belirle"""
        query_lower = query.lower()
        
        if any(w in query_lower for w in ['bilimsel', 'araştırma', 'study', 'research', 'evidence']):
            return "academic"
        elif any(w in query_lower for w in ['haber', 'güncel', 'news', 'recent', 'latest']):
            return "news"
        elif any(w in query_lower for w in ['nasıl yapılır', 'how to', 'guide', 'tutorial']):
            return "practical"
        else:
            return "comprehensive"
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=300)
            except Exception:
                pass
        
        # Fallback to Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 200, "temperature": 0.5}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception:
            pass
        
        return ""


# ============ DEEP RESEARCH ENGINE ============

class DeepResearchEngine:
    """
    Deep Research 3.0 Engine.
    
    Iterative, evidence-graded, multi-source research.
    """
    
    def __init__(
        self,
        search_engine=None,
        llm_client=None,
        max_iterations: int = 4,
        min_confidence: float = 0.7,
    ):
        self.search_engine = search_engine
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.min_confidence = min_confidence
        
        # Components
        self.planner = ResearchPlanner(llm_client)
        self.grader = EvidenceGrader()
        
        # State
        self._current_progress: Optional[ResearchProgress] = None
    
    async def research(
        self,
        query: str,
        depth: str = "comprehensive",  # quick, standard, comprehensive, exhaustive
    ) -> AsyncIterator[ResearchProgress | ResearchReport]:
        """
        Derinlemesine araştırma yap.
        
        Yields:
            ResearchProgress objects during research
            ResearchReport at the end
        """
        start_time = time.time()
        
        # Adjust iterations based on depth
        iterations = {
            "quick": 1,
            "standard": 2,
            "comprehensive": 3,
            "exhaustive": 5,
        }.get(depth, 3)
        
        iterations = min(iterations, self.max_iterations)
        
        # Initialize
        all_evidence: List[Evidence] = []
        all_sources: List[Dict] = []
        findings: List[Finding] = []
        
        # Phase 1: Planning
        yield self._progress(ResearchPhase.PLANNING, 0, iterations, "Araştırma planlanıyor...")
        
        research_plan = await self.planner.plan(query)
        
        # Iterative research loop
        for iteration in range(1, iterations + 1):
            # Phase 2: Searching
            yield self._progress(
                ResearchPhase.SEARCHING, iteration, iterations,
                f"İterasyon {iteration}/{iterations}: Kaynaklar aranıyor...",
                sources_found=len(all_sources)
            )
            
            # Determine queries for this iteration
            if iteration == 1:
                search_queries = [query] + research_plan.refined_queries[:3]
            else:
                # Refine based on gaps
                search_queries = self._generate_refinement_queries(findings, research_plan)
            
            # Search
            new_results = await self._search_all(search_queries)
            all_sources.extend(new_results)
            
            # Phase 3: Extracting
            yield self._progress(
                ResearchPhase.EXTRACTING, iteration, iterations,
                f"Kanıtlar çıkarılıyor...",
                sources_found=len(all_sources),
                evidence_collected=len(all_evidence)
            )
            
            # Extract evidence
            new_evidence = await self._extract_evidence(new_results, query)
            all_evidence.extend(new_evidence)
            
            # Phase 4: Analyzing
            yield self._progress(
                ResearchPhase.ANALYZING, iteration, iterations,
                f"Kanıtlar analiz ediliyor...",
                sources_found=len(all_sources),
                evidence_collected=len(all_evidence)
            )
            
            # Analyze and grade evidence
            for evidence in new_evidence:
                evidence.grade = self.grader.grade_evidence(evidence)
            
            # Phase 5: Verifying
            if iteration >= 2:
                yield self._progress(
                    ResearchPhase.VERIFYING, iteration, iterations,
                    f"Bulgular doğrulanıyor...",
                    evidence_collected=len(all_evidence)
                )
                
                # Cross-verify evidence
                all_evidence = self._verify_evidence(all_evidence)
            
            # Generate findings
            iteration_findings = await self._generate_findings(all_evidence, query)
            
            # Merge with existing findings
            findings = self._merge_findings(findings, iteration_findings)
            
            # Calculate current confidence
            current_confidence = self._calculate_confidence(findings)
            
            yield self._progress(
                ResearchPhase.ANALYZING, iteration, iterations,
                f"İterasyon {iteration} tamamlandı. Güven: {current_confidence:.0%}",
                sources_found=len(all_sources),
                evidence_collected=len(all_evidence),
                findings_count=len(findings),
                confidence=current_confidence
            )
            
            # Check if we've reached sufficient confidence
            if current_confidence >= self.min_confidence and iteration >= 2:
                break
        
        # Phase 6: Synthesizing
        yield self._progress(
            ResearchPhase.SYNTHESIZING, iterations, iterations,
            "Rapor sentezleniyor...",
            sources_found=len(all_sources),
            evidence_collected=len(all_evidence),
            findings_count=len(findings)
        )
        
        # Generate executive summary
        summary = await self._generate_summary(query, findings)
        
        # Generate insights and limitations
        insights = await self._generate_insights(findings)
        limitations = self._identify_limitations(all_evidence, findings)
        further_research = await self._suggest_further_research(query, findings)
        
        # Calculate overall grade and confidence
        overall_grade, overall_confidence = self._calculate_overall_grade(findings)
        
        # Build report
        report = ResearchReport(
            query=query,
            executive_summary=summary,
            findings=findings,
            overall_confidence=overall_confidence,
            overall_grade=overall_grade,
            total_sources=len(all_sources),
            sources_used=self._format_sources(all_sources),
            key_insights=insights,
            limitations=limitations,
            further_research=further_research,
            iterations=iterations,
            total_time_seconds=time.time() - start_time,
        )
        
        # Complete
        yield self._progress(
            ResearchPhase.COMPLETE, iterations, iterations,
            "Araştırma tamamlandı!",
            sources_found=len(all_sources),
            evidence_collected=len(all_evidence),
            findings_count=len(findings),
            confidence=overall_confidence,
            elapsed_seconds=time.time() - start_time
        )
        
        yield report
    
    def _progress(
        self,
        phase: ResearchPhase,
        iteration: int,
        total: int,
        message: str,
        **kwargs
    ) -> ResearchProgress:
        """Progress nesnesi oluştur"""
        return ResearchProgress(
            phase=phase,
            iteration=iteration,
            total_iterations=total,
            message=message,
            **kwargs
        )
    
    async def _search_all(self, queries: List[str]) -> List[Dict]:
        """Tüm sorguları ara"""
        all_results = []
        
        for query in queries:
            try:
                if self.search_engine:
                    results = await self.search_engine.search(query, num_results=15)
                    all_results.extend([r.__dict__ if hasattr(r, '__dict__') else r for r in results.results])
                else:
                    # Fallback to web search tool
                    results = await self._fallback_search(query)
                    all_results.extend(results)
            except Exception as e:
                logger.warning(f"Search failed for '{query}': {e}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)
        
        return unique_results
    
    async def _fallback_search(self, query: str) -> List[Dict]:
        """Fallback arama"""
        try:
            from tools.web_search_engine import get_search_engine
            engine = get_search_engine()
            response = engine.search(query, num_results=15)
            
            results = []
            for r in response.results:
                results.append({
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "content": r.full_content,
                    "domain": r.domain,
                    "source_type": r.source_type.value if hasattr(r.source_type, 'value') else str(r.source_type),
                    "reliability_score": r.reliability_score,
                })
            return results
        except Exception as e:
            logger.warning(f"Fallback search failed: {e}")
            return []
    
    async def _extract_evidence(
        self,
        results: List[Dict],
        query: str
    ) -> List[Evidence]:
        """Kanıtları çıkar"""
        evidence_list = []
        
        for result in results:
            content = result.get("content") or result.get("snippet", "")
            if not content:
                continue
            
            # Determine source type
            source_type = self._classify_source(result)
            
            evidence = Evidence(
                content=content[:2000],
                source_url=result.get("url", ""),
                source_title=result.get("title", ""),
                source_type=source_type,
                relevance_score=result.get("reliability_score", 0.5),
                author=result.get("author", ""),
                date=result.get("date", result.get("published_date", "")),
            )
            
            evidence_list.append(evidence)
        
        return evidence_list
    
    def _classify_source(self, result: Dict) -> SourceReliability:
        """Kaynak türünü sınıflandır"""
        source_type = result.get("source_type", "unknown")
        url = result.get("url", "").lower()
        domain = result.get("domain", "").lower()
        
        if source_type == "academic" or any(x in domain for x in ["arxiv", "scholar", "edu", "academic"]):
            return SourceReliability.ACADEMIC
        elif source_type == "wiki" or "wikipedia" in domain:
            return SourceReliability.WIKI
        elif any(x in domain for x in ["gov", "resmi"]):
            return SourceReliability.OFFICIAL
        elif source_type == "news" or any(x in domain for x in ["news", "haber"]):
            return SourceReliability.NEWS
        elif any(x in domain for x in ["docs.", "documentation"]):
            return SourceReliability.DOCUMENTATION
        elif source_type == "blog" or any(x in domain for x in ["blog", "medium"]):
            return SourceReliability.BLOG
        elif source_type == "forum" or any(x in domain for x in ["reddit", "forum", "stackoverflow"]):
            return SourceReliability.FORUM
        else:
            return SourceReliability.UNKNOWN
    
    def _verify_evidence(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """Kanıtları çapraz doğrula"""
        # Group by claim similarity
        for i, e1 in enumerate(evidence_list):
            supporting = 0
            contradicting = 0
            
            for j, e2 in enumerate(evidence_list):
                if i == j:
                    continue
                
                # Simple similarity check
                overlap = self._content_similarity(e1.content, e2.content)
                
                if overlap > 0.3:
                    supporting += 1
                elif overlap < 0.1 and self._check_contradiction(e1.content, e2.content):
                    contradicting += 1
            
            e1.supporting_sources = supporting
            e1.contradicting_sources = contradicting
            e1.verified = supporting >= 2 and contradicting == 0
        
        return evidence_list
    
    def _content_similarity(self, text1: str, text2: str) -> float:
        """Basit içerik benzerliği"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / max(1, union)
    
    def _check_contradiction(self, text1: str, text2: str) -> bool:
        """Çelişki kontrolü"""
        # Very simple check for negation patterns
        negation_words = ["değil", "hayır", "yanlış", "not", "no", "false", "incorrect"]
        
        t1_has_neg = any(w in text1.lower() for w in negation_words)
        t2_has_neg = any(w in text2.lower() for w in negation_words)
        
        # If only one has negation about similar topic, might be contradiction
        return t1_has_neg != t2_has_neg
    
    async def _generate_findings(
        self,
        evidence: List[Evidence],
        query: str
    ) -> List[Finding]:
        """Bulgular oluştur"""
        if not evidence:
            return []
        
        # Group evidence by topic/claim
        findings = []
        
        # Use LLM to extract claims
        claims = await self._extract_claims(evidence, query)
        
        for claim in claims:
            # Find supporting evidence
            supporting = [e for e in evidence if self._evidence_supports_claim(e, claim)]
            
            if not supporting:
                continue
            
            # Grade the finding
            finding = Finding(
                claim=claim,
                evidence=supporting,
            )
            
            finding.grade, finding.confidence = self.grader.grade_findings(finding)
            finding.consensus = self._assess_consensus(supporting)
            
            findings.append(finding)
        
        return findings
    
    async def _extract_claims(self, evidence: List[Evidence], query: str) -> List[str]:
        """Ana iddiaları çıkar"""
        # Build evidence text
        evidence_text = "\n".join([f"- {e.content[:200]}" for e in evidence[:10]])
        
        prompt = f"""Based on this evidence about "{query}", identify 3-5 main claims or facts.
Write each claim as a clear, standalone statement.

Evidence:
{evidence_text}

Main Claims (one per line):"""
        
        try:
            response = await self._call_llm(prompt)
            claims = [c.strip() for c in response.split('\n') if c.strip() and len(c.strip()) > 20]
            return claims[:5]
        except Exception:
            # Fallback: Return first sentences from evidence
            claims = []
            for e in evidence[:3]:
                first_sentence = e.content.split('.')[0].strip()
                if len(first_sentence) > 20:
                    claims.append(first_sentence)
            return claims
    
    def _evidence_supports_claim(self, evidence: Evidence, claim: str) -> bool:
        """Kanıt iddiayı destekliyor mu?"""
        # Simple keyword overlap
        claim_words = set(claim.lower().split())
        evidence_words = set(evidence.content.lower().split())
        
        overlap = len(claim_words & evidence_words)
        return overlap >= len(claim_words) * 0.3
    
    def _assess_consensus(self, evidence: List[Evidence]) -> str:
        """Konsensüs değerlendir"""
        if not evidence:
            return "unknown"
        
        supporting = sum(1 for e in evidence if e.supporting_sources > 0)
        contradicting = sum(1 for e in evidence if e.contradicting_sources > 0)
        
        if supporting >= 3 and contradicting == 0:
            return "strong"
        elif supporting >= 2:
            return "moderate"
        elif contradicting > 0:
            return "disputed"
        else:
            return "weak"
    
    def _merge_findings(
        self,
        existing: List[Finding],
        new: List[Finding]
    ) -> List[Finding]:
        """Bulguları birleştir"""
        merged = list(existing)
        
        for new_finding in new:
            # Check if similar finding exists
            merged_existing = False
            for existing_finding in merged:
                similarity = self._content_similarity(new_finding.claim, existing_finding.claim)
                if similarity > 0.5:
                    # Merge evidence
                    existing_finding.evidence.extend(new_finding.evidence)
                    # Re-grade
                    existing_finding.grade, existing_finding.confidence = self.grader.grade_findings(existing_finding)
                    merged_existing = True
                    break
            
            if not merged_existing:
                merged.append(new_finding)
        
        return merged
    
    def _generate_refinement_queries(
        self,
        findings: List[Finding],
        plan: ResearchQuery
    ) -> List[str]:
        """Boşlukları doldurmak için yeni sorgular"""
        queries = []
        
        # Low confidence findings need more research
        for finding in findings:
            if finding.confidence < 0.6:
                # Extract key terms from claim
                words = [w for w in finding.claim.split() if len(w) > 4][:3]
                if words:
                    queries.append(" ".join(words) + " research evidence")
        
        # Add sub-questions not yet addressed
        for sq in plan.sub_questions:
            addressed = any(self._content_similarity(sq, f.claim) > 0.3 for f in findings)
            if not addressed:
                queries.append(sq)
        
        return queries[:5]
    
    def _calculate_confidence(self, findings: List[Finding]) -> float:
        """Genel güven hesapla"""
        if not findings:
            return 0.0
        
        confidences = [f.confidence for f in findings]
        return sum(confidences) / len(confidences)
    
    def _calculate_overall_grade(self, findings: List[Finding]) -> Tuple[EvidenceGrade, float]:
        """Genel derece hesapla"""
        if not findings:
            return EvidenceGrade.F, 0.0
        
        grade_scores = {
            EvidenceGrade.A: 1.0,
            EvidenceGrade.B: 0.8,
            EvidenceGrade.C: 0.6,
            EvidenceGrade.D: 0.4,
            EvidenceGrade.F: 0.2,
        }
        
        scores = [grade_scores.get(f.grade, 0.5) for f in findings]
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.85:
            return EvidenceGrade.A, avg_score
        elif avg_score >= 0.70:
            return EvidenceGrade.B, avg_score
        elif avg_score >= 0.55:
            return EvidenceGrade.C, avg_score
        elif avg_score >= 0.35:
            return EvidenceGrade.D, avg_score
        else:
            return EvidenceGrade.F, avg_score
    
    async def _generate_summary(self, query: str, findings: List[Finding]) -> str:
        """Yönetici özeti oluştur"""
        findings_text = "\n".join([f"- {f.claim} (Güven: {f.confidence:.0%})" for f in findings[:5]])
        
        prompt = f"""Write an executive summary for this research on "{query}".
Be concise but comprehensive. Include confidence levels.

Key Findings:
{findings_text}

Executive Summary:"""
        
        try:
            return await self._call_llm(prompt)
        except Exception:
            # Fallback
            if findings:
                return f"Bu araştırma '{query}' konusunda {len(findings)} ana bulgu ortaya koymuştur. " + \
                       f"En güvenilir bulgu: {findings[0].claim}"
            return f"'{query}' konusunda araştırma tamamlandı."
    
    async def _generate_insights(self, findings: List[Finding]) -> List[str]:
        """Önemli içgörüler"""
        if not findings:
            return []
        
        insights = []
        
        # High confidence findings are insights
        for f in findings:
            if f.confidence >= 0.7:
                insights.append(f"✓ {f.claim}")
        
        return insights[:5]
    
    def _identify_limitations(
        self,
        evidence: List[Evidence],
        findings: List[Finding]
    ) -> List[str]:
        """Sınırlamaları belirle"""
        limitations = []
        
        # Check for low evidence count
        if len(evidence) < 5:
            limitations.append("Sınırlı kaynak sayısı")
        
        # Check for low consensus
        disputed = [f for f in findings if f.consensus == "disputed"]
        if disputed:
            limitations.append(f"{len(disputed)} bulgu tartışmalı")
        
        # Check for source diversity
        source_types = set(e.source_type for e in evidence)
        if len(source_types) < 3:
            limitations.append("Kaynak çeşitliliği sınırlı")
        
        # Check for academic sources
        academic = [e for e in evidence if e.source_type == SourceReliability.ACADEMIC]
        if not academic:
            limitations.append("Akademik kaynak bulunmuyor")
        
        return limitations
    
    async def _suggest_further_research(
        self,
        query: str,
        findings: List[Finding]
    ) -> List[str]:
        """İleri araştırma önerileri"""
        suggestions = []
        
        # Low confidence findings need more research
        for f in findings:
            if f.confidence < 0.6:
                suggestions.append(f"'{f.claim}' konusu daha detaylı araştırılabilir")
        
        # General suggestion
        suggestions.append(f"'{query}' konusunda akademik kaynaklar incelenebilir")
        
        return suggestions[:3]
    
    def _format_sources(self, sources: List[Dict]) -> List[Dict[str, str]]:
        """Kaynakları formatla"""
        formatted = []
        seen_urls = set()
        
        for s in sources:
            url = s.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            formatted.append({
                "title": s.get("title", ""),
                "url": url,
                "domain": s.get("domain", ""),
            })
        
        return formatted[:20]
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=500)
            except Exception:
                pass
        
        # Fallback to Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 400, "temperature": 0.5}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "")
        except Exception:
            pass
        
        return ""


# ============ SINGLETON ============

_engine: Optional[DeepResearchEngine] = None

def get_deep_research_engine() -> DeepResearchEngine:
    global _engine
    if _engine is None:
        _engine = DeepResearchEngine()
    return _engine


# ============ TEST ============

async def test_research():
    """Test deep research"""
    print("Testing Deep Research 3.0...")
    
    engine = get_deep_research_engine()
    
    query = "Python asyncio vs threading performans karşılaştırması"
    
    async for result in engine.research(query, depth="quick"):
        if isinstance(result, ResearchProgress):
            print(f"[{result.phase.value}] {result.message}")
        elif isinstance(result, ResearchReport):
            print(f"\n=== REPORT ===")
            print(f"Query: {result.query}")
            print(f"Grade: {result.overall_grade.value}")
            print(f"Confidence: {result.overall_confidence:.0%}")
            print(f"\nSummary: {result.executive_summary[:500]}")
            print(f"\nFindings: {len(result.findings)}")
            print(f"Sources: {result.total_sources}")
            print(f"Time: {result.total_time_seconds:.1f}s")


if __name__ == "__main__":
    asyncio.run(test_research())
