"""
🧠 Premium Reasoning Engine - Chain of Thought & Multi-Agent Debate
===================================================================

Endüstri-seviyesi reasoning sistemi.
Claude Extended Thinking, OpenAI o1, DeepSeek R1 kalitesinde.

Özellikler:
- Extended Thinking: Adım adım düşünme
- Chain of Thought: Düşünce zinciri görselleştirme
- Multi-Agent Debate: Çoklu perspektif tartışması
- Self-Consistency: Tutarlılık kontrolü
- Reflection: Öz-değerlendirme
- Decomposition: Problem ayrıştırma
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, AsyncIterator
from datetime import datetime

logger = logging.getLogger(__name__)


# ============ ENUMS ============

class ThinkingPhase(Enum):
    """Düşünme fazları"""
    UNDERSTANDING = "understanding"
    PLANNING = "planning"
    DECOMPOSING = "decomposing"
    ANALYZING = "analyzing"
    SYNTHESIZING = "synthesizing"
    VERIFYING = "verifying"
    REFLECTING = "reflecting"
    CONCLUDING = "concluding"


class AgentRole(Enum):
    """Ajan rolleri"""
    ANALYST = "analyst"      # Ana analizci
    CRITIC = "critic"        # Eleştirmen
    ADVOCATE = "advocate"    # Savunucu
    SKEPTIC = "skeptic"      # Şüpheci
    SYNTHESIZER = "synthesizer"  # Sentezci


class ConfidenceLevel(Enum):
    """Güven seviyeleri"""
    VERY_HIGH = "very_high"   # 90%+
    HIGH = "high"             # 75-90%
    MODERATE = "moderate"     # 50-75%
    LOW = "low"               # 25-50%
    VERY_LOW = "very_low"     # <25%


# ============ DATA CLASSES ============

@dataclass
class ThinkingStep:
    """Tek bir düşünme adımı"""
    phase: ThinkingPhase
    content: str
    
    # Metadata
    duration_ms: int = 0
    confidence: float = 0.7
    
    # Optional
    sub_steps: List['ThinkingStep'] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "content": self.content,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "sub_steps": [s.to_dict() for s in self.sub_steps],
        }


@dataclass
class ChainOfThought:
    """Düşünce zinciri"""
    question: str
    steps: List[ThinkingStep]
    
    # Conclusion
    final_answer: str = ""
    overall_confidence: float = 0.7
    
    # Metadata
    total_time_ms: int = 0
    token_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "overall_confidence": self.overall_confidence,
            "total_time_ms": self.total_time_ms,
        }


@dataclass
class DebateArgument:
    """Tartışma argümanı"""
    agent: AgentRole
    position: str
    content: str
    
    # Evidence
    supporting_points: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    # Response to others
    rebuttals: Dict[str, str] = field(default_factory=dict)
    concessions: List[str] = field(default_factory=list)
    
    # Score
    strength: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent.value,
            "position": self.position,
            "content": self.content,
            "supporting_points": self.supporting_points,
            "weaknesses": self.weaknesses,
            "strength": self.strength,
        }


@dataclass
class DebateResult:
    """Tartışma sonucu"""
    topic: str
    arguments: List[DebateArgument]
    
    # Synthesis
    consensus_points: List[str] = field(default_factory=list)
    disputed_points: List[str] = field(default_factory=list)
    final_synthesis: str = ""
    
    # Winner
    winning_position: str = ""
    confidence: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "arguments": [a.to_dict() for a in self.arguments],
            "consensus_points": self.consensus_points,
            "disputed_points": self.disputed_points,
            "final_synthesis": self.final_synthesis,
            "winning_position": self.winning_position,
            "confidence": self.confidence,
        }


@dataclass
class ReasoningResult:
    """Nihai reasoning sonucu"""
    question: str
    answer: str
    
    # Process
    chain_of_thought: Optional[ChainOfThought] = None
    debate: Optional[DebateResult] = None
    
    # Quality
    confidence: float = 0.7
    confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    
    # Verification
    self_consistent: bool = True
    verification_notes: List[str] = field(default_factory=list)
    
    # Metadata
    reasoning_type: str = "chain_of_thought"
    total_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "chain_of_thought": self.chain_of_thought.to_dict() if self.chain_of_thought else None,
            "debate": self.debate.to_dict() if self.debate else None,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "self_consistent": self.self_consistent,
            "verification_notes": self.verification_notes,
            "reasoning_type": self.reasoning_type,
            "total_time_ms": self.total_time_ms,
        }


# ============ CHAIN OF THOUGHT GENERATOR ============

class ChainOfThoughtGenerator:
    """
    Chain of Thought düşünce zinciri üretici.
    
    OpenAI o1-style extended thinking.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def generate(
        self,
        question: str,
        context: str = "",
        depth: str = "standard"  # quick, standard, deep
    ) -> ChainOfThought:
        """Düşünce zinciri oluştur"""
        start_time = time.time()
        steps: List[ThinkingStep] = []
        
        # Phase 1: Understanding
        understanding = await self._understand(question, context)
        steps.append(ThinkingStep(
            phase=ThinkingPhase.UNDERSTANDING,
            content=understanding,
            confidence=0.9
        ))
        
        # Phase 2: Planning
        plan = await self._plan(question, understanding)
        steps.append(ThinkingStep(
            phase=ThinkingPhase.PLANNING,
            content=plan,
            confidence=0.85
        ))
        
        # Phase 3: Decomposition (for complex questions)
        if depth in ["standard", "deep"] and self._is_complex(question):
            sub_problems = await self._decompose(question)
            decomp_step = ThinkingStep(
                phase=ThinkingPhase.DECOMPOSING,
                content=f"Alt problemlere ayrıştırıldı: {', '.join(sub_problems)}",
                confidence=0.8
            )
            
            # Solve sub-problems
            for sp in sub_problems[:3]:  # Max 3 sub-problems
                sub_solution = await self._analyze_subproblem(sp)
                decomp_step.sub_steps.append(ThinkingStep(
                    phase=ThinkingPhase.ANALYZING,
                    content=sub_solution,
                    confidence=0.7
                ))
            
            steps.append(decomp_step)
        
        # Phase 4: Analysis
        analysis = await self._analyze(question, understanding, plan)
        steps.append(ThinkingStep(
            phase=ThinkingPhase.ANALYZING,
            content=analysis,
            confidence=0.75
        ))
        
        # Phase 5: Synthesis
        synthesis = await self._synthesize(question, steps)
        steps.append(ThinkingStep(
            phase=ThinkingPhase.SYNTHESIZING,
            content=synthesis,
            confidence=0.8
        ))
        
        # Phase 6: Verification (deep only)
        if depth == "deep":
            verification = await self._verify(question, synthesis)
            steps.append(ThinkingStep(
                phase=ThinkingPhase.VERIFYING,
                content=verification,
                confidence=0.85
            ))
        
        # Phase 7: Conclusion
        conclusion = await self._conclude(question, steps)
        steps.append(ThinkingStep(
            phase=ThinkingPhase.CONCLUDING,
            content=conclusion,
            confidence=0.85
        ))
        
        # Calculate overall confidence
        confidences = [s.confidence for s in steps]
        overall_confidence = sum(confidences) / len(confidences)
        
        return ChainOfThought(
            question=question,
            steps=steps,
            final_answer=conclusion,
            overall_confidence=overall_confidence,
            total_time_ms=int((time.time() - start_time) * 1000)
        )
    
    async def _understand(self, question: str, context: str) -> str:
        """Soruyu anla"""
        prompt = f"""Analyze this question to understand what's being asked.
Identify: key concepts, question type, what information is needed.

Question: {question}
{"Context: " + context if context else ""}

Understanding (be concise):"""
        
        return await self._call_llm(prompt)
    
    async def _plan(self, question: str, understanding: str) -> str:
        """Çözüm planla"""
        prompt = f"""Create a brief plan to answer this question.
List 3-5 steps.

Question: {question}
Understanding: {understanding}

Plan:"""
        
        return await self._call_llm(prompt)
    
    def _is_complex(self, question: str) -> bool:
        """Soru karmaşık mı?"""
        complexity_indicators = [
            "karşılaştır", "compare", "analiz", "analyze",
            "neden", "why", "nasıl", "how",
            "fark", "difference", "avantaj", "dezavantaj",
            "ençok", "hangisi", "which"
        ]
        return any(ind in question.lower() for ind in complexity_indicators) or len(question) > 100
    
    async def _decompose(self, question: str) -> List[str]:
        """Alt problemlere ayır"""
        prompt = f"""Break this question into 2-3 simpler sub-questions.
Each sub-question should be answerable independently.

Question: {question}

Sub-questions (one per line):"""
        
        response = await self._call_llm(prompt)
        questions = [q.strip() for q in response.split('\n') if q.strip() and '?' in q]
        return questions[:3]
    
    async def _analyze_subproblem(self, subproblem: str) -> str:
        """Alt problemi analiz et"""
        prompt = f"""Briefly answer this sub-question:
{subproblem}

Answer:"""
        
        return await self._call_llm(prompt, max_tokens=200)
    
    async def _analyze(
        self,
        question: str,
        understanding: str,
        plan: str
    ) -> str:
        """Ana analiz"""
        prompt = f"""Following the plan, analyze to answer the question.
Show your reasoning step by step.

Question: {question}
Understanding: {understanding}
Plan: {plan}

Analysis:"""
        
        return await self._call_llm(prompt, max_tokens=500)
    
    async def _synthesize(
        self,
        question: str,
        steps: List[ThinkingStep]
    ) -> str:
        """Sentezle"""
        steps_text = "\n".join([f"- {s.phase.value}: {s.content[:200]}" for s in steps])
        
        prompt = f"""Synthesize all the analysis into a coherent answer.

Question: {question}

Previous Steps:
{steps_text}

Synthesis:"""
        
        return await self._call_llm(prompt, max_tokens=400)
    
    async def _verify(self, question: str, synthesis: str) -> str:
        """Doğrula"""
        prompt = f"""Verify this answer. Check for:
1. Logical consistency
2. Missing information
3. Potential errors

Question: {question}
Answer: {synthesis}

Verification:"""
        
        return await self._call_llm(prompt, max_tokens=200)
    
    async def _conclude(
        self,
        question: str,
        steps: List[ThinkingStep]
    ) -> str:
        """Sonuçlandır"""
        latest = steps[-1].content if steps else ""
        
        prompt = f"""Based on all the reasoning, provide a clear, direct answer.

Question: {question}
Latest Analysis: {latest[:500]}

Final Answer:"""
        
        return await self._call_llm(prompt, max_tokens=300)
    
    async def _call_llm(self, prompt: str, max_tokens: int = 300) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=max_tokens)
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
                        "options": {"num_predict": max_tokens, "temperature": 0.5}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
        except Exception:
            pass
        
        return "Analysis in progress..."


# ============ MULTI-AGENT DEBATE ============

class MultiAgentDebate:
    """
    Multi-Agent Debate sistemi.
    
    Farklı perspektiflerden analiz.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def debate(
        self,
        topic: str,
        positions: List[str] = None,
        rounds: int = 2
    ) -> DebateResult:
        """Çoklu ajan tartışması"""
        arguments: List[DebateArgument] = []
        
        # Default positions for comparison questions
        if not positions:
            positions = self._generate_positions(topic)
        
        # Round 1: Initial arguments
        for i, position in enumerate(positions[:3]):
            role = [AgentRole.ADVOCATE, AgentRole.CRITIC, AgentRole.SKEPTIC][i % 3]
            arg = await self._generate_argument(topic, position, role)
            arguments.append(arg)
        
        # Round 2: Rebuttals
        if rounds >= 2:
            for i, arg in enumerate(arguments):
                other_args = [a for j, a in enumerate(arguments) if j != i]
                rebuttals = await self._generate_rebuttals(arg, other_args)
                arg.rebuttals = rebuttals
        
        # Round 3: Concessions (if 3 rounds)
        if rounds >= 3:
            for arg in arguments:
                concessions = await self._find_concessions(arg, arguments)
                arg.concessions = concessions
        
        # Synthesis
        synthesis = await self._synthesize_debate(topic, arguments)
        consensus = self._find_consensus(arguments)
        disputed = self._find_disputed(arguments)
        winning = self._determine_winner(arguments)
        
        return DebateResult(
            topic=topic,
            arguments=arguments,
            consensus_points=consensus,
            disputed_points=disputed,
            final_synthesis=synthesis,
            winning_position=winning[0] if winning else "",
            confidence=winning[1] if winning else 0.5
        )
    
    def _generate_positions(self, topic: str) -> List[str]:
        """Pozisyonlar oluştur"""
        # Try to extract comparison targets
        if " vs " in topic.lower() or " karşı " in topic.lower():
            parts = re.split(r'\s+(?:vs|versus|karşı|mı)\s+', topic, flags=re.IGNORECASE)
            if len(parts) >= 2:
                return [f"{parts[0]} daha iyi", f"{parts[1]} daha iyi"]
        
        # Default: pro, con, neutral
        return ["Olumlu bakış", "Olumsuz bakış", "Dengeli bakış"]
    
    async def _generate_argument(
        self,
        topic: str,
        position: str,
        role: AgentRole
    ) -> DebateArgument:
        """Argüman oluştur"""
        role_prompts = {
            AgentRole.ADVOCATE: "You strongly support this position. Make the best case for it.",
            AgentRole.CRITIC: "You are critical. Find problems and weaknesses.",
            AgentRole.SKEPTIC: "You are skeptical. Question assumptions and demand evidence."
        }
        
        prompt = f"""{role_prompts.get(role, '')}

Topic: {topic}
Position: {position}

Provide:
1. Main argument (2-3 sentences)
2. 3 supporting points
3. 2 potential weaknesses

Format:
ARGUMENT: [your main argument]
SUPPORTING:
- [point 1]
- [point 2]
- [point 3]
WEAKNESSES:
- [weakness 1]
- [weakness 2]"""
        
        response = await self._call_llm(prompt, max_tokens=400)
        
        # Parse response
        argument = DebateArgument(
            agent=role,
            position=position,
            content=response
        )
        
        # Extract parts
        if "ARGUMENT:" in response:
            parts = response.split("SUPPORTING:")
            argument.content = parts[0].replace("ARGUMENT:", "").strip()
        
        # Extract supporting points
        supporting_match = re.findall(r'-\s*(.+)', response)
        if supporting_match:
            argument.supporting_points = supporting_match[:3]
            argument.weaknesses = supporting_match[3:5]
        
        # Calculate strength based on content quality
        argument.strength = self._calculate_strength(argument)
        
        return argument
    
    async def _generate_rebuttals(
        self,
        arg: DebateArgument,
        other_args: List[DebateArgument]
    ) -> Dict[str, str]:
        """Karşı argümanlar"""
        rebuttals = {}
        
        for other in other_args:
            prompt = f"""Your position: {arg.position}
Your argument: {arg.content[:200]}

Opponent says: {other.content[:200]}

Write a brief rebuttal (2-3 sentences):"""
            
            rebuttal = await self._call_llm(prompt, max_tokens=150)
            rebuttals[other.position] = rebuttal
        
        return rebuttals
    
    async def _find_concessions(
        self,
        arg: DebateArgument,
        all_args: List[DebateArgument]
    ) -> List[str]:
        """Kabul edilen noktalar"""
        other_points = []
        for a in all_args:
            if a != arg:
                other_points.extend(a.supporting_points)
        
        if not other_points:
            return []
        
        prompt = f"""Your position: {arg.position}

Other side's points:
{chr(10).join(f'- {p}' for p in other_points[:5])}

Which points (if any) do you concede have merit? List 1-2:"""
        
        response = await self._call_llm(prompt, max_tokens=100)
        concessions = [c.strip() for c in response.split('\n') if c.strip() and len(c.strip()) > 10]
        return concessions[:2]
    
    def _calculate_strength(self, arg: DebateArgument) -> float:
        """Argüman gücü"""
        strength = 0.5
        
        # More supporting points
        strength += len(arg.supporting_points) * 0.1
        
        # Content length (up to a point)
        word_count = len(arg.content.split())
        if word_count > 50:
            strength += 0.1
        
        # Has specific examples or data
        if any(c.isdigit() for c in arg.content):
            strength += 0.1
        
        return min(1.0, strength)
    
    def _find_consensus(self, arguments: List[DebateArgument]) -> List[str]:
        """Konsensüs noktaları"""
        all_points = []
        for arg in arguments:
            all_points.extend(arg.supporting_points)
        
        # Find similar points
        consensus = []
        for i, p1 in enumerate(all_points):
            for j, p2 in enumerate(all_points[i+1:], i+1):
                similarity = self._text_similarity(p1, p2)
                if similarity > 0.3:
                    consensus.append(p1)
                    break
        
        return list(set(consensus))[:3]
    
    def _find_disputed(self, arguments: List[DebateArgument]) -> List[str]:
        """Tartışmalı noktalar"""
        disputed = []
        
        for arg in arguments:
            # Check if weaknesses of one are supporting points of another
            for weakness in arg.weaknesses:
                for other in arguments:
                    if other != arg:
                        for support in other.supporting_points:
                            if self._text_similarity(weakness, support) > 0.2:
                                disputed.append(weakness)
        
        return list(set(disputed))[:3]
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Basit metin benzerliği"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / max(1, union)
    
    def _determine_winner(self, arguments: List[DebateArgument]) -> Tuple[str, float]:
        """Kazananı belirle"""
        if not arguments:
            return "", 0.5
        
        # Sort by strength
        sorted_args = sorted(arguments, key=lambda a: a.strength, reverse=True)
        winner = sorted_args[0]
        
        # Calculate confidence based on margin
        if len(sorted_args) > 1:
            margin = winner.strength - sorted_args[1].strength
            confidence = 0.5 + margin
        else:
            confidence = winner.strength
        
        return winner.position, min(0.95, confidence)
    
    async def _synthesize_debate(
        self,
        topic: str,
        arguments: List[DebateArgument]
    ) -> str:
        """Tartışmayı sentezle"""
        args_text = "\n".join([f"- {a.position}: {a.content[:150]}" for a in arguments])
        
        prompt = f"""Synthesize this debate into a balanced conclusion.
Acknowledge valid points from all sides.

Topic: {topic}

Arguments:
{args_text}

Balanced Synthesis:"""
        
        return await self._call_llm(prompt, max_tokens=300)
    
    async def _call_llm(self, prompt: str, max_tokens: int = 300) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=max_tokens)
            except Exception:
                pass
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": max_tokens, "temperature": 0.6}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
        except Exception:
            pass
        
        return "Debate in progress..."


# ============ SELF-CONSISTENCY CHECKER ============

class SelfConsistencyChecker:
    """
    Self-Consistency doğrulayıcı.
    
    Aynı soruya farklı yaklaşımlarla tutarlılık kontrolü.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def check_consistency(
        self,
        question: str,
        answer: str,
        num_samples: int = 3
    ) -> Tuple[bool, float, List[str]]:
        """
        Tutarlılık kontrolü.
        
        Returns:
            (is_consistent, confidence, alternative_answers)
        """
        # Generate alternative answers
        alternatives = []
        for i in range(num_samples):
            alt = await self._generate_alternative(question, i)
            alternatives.append(alt)
        
        # Compare with original
        similarities = []
        for alt in alternatives:
            sim = self._compare_answers(answer, alt)
            similarities.append(sim)
        
        # Calculate consistency
        avg_similarity = sum(similarities) / len(similarities)
        is_consistent = avg_similarity > 0.5
        
        return is_consistent, avg_similarity, alternatives
    
    async def _generate_alternative(self, question: str, variation: int) -> str:
        """Alternatif cevap üret"""
        variation_prompts = [
            "Answer directly and concisely.",
            "Think step by step before answering.",
            "Consider different perspectives and answer.",
        ]
        
        prompt = f"""{variation_prompts[variation % len(variation_prompts)]}

Question: {question}

Answer:"""
        
        return await self._call_llm(prompt)
    
    def _compare_answers(self, answer1: str, answer2: str) -> float:
        """Cevapları karşılaştır"""
        # Extract key facts from both
        words1 = set(answer1.lower().split())
        words2 = set(answer2.lower().split())
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / max(1, union)
    
    async def _call_llm(self, prompt: str) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=200)
            except Exception:
                pass
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 200, "temperature": 0.7}  # Slightly higher temp for variation
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
        except Exception:
            pass
        
        return ""


# ============ REFLECTION ENGINE ============

class ReflectionEngine:
    """
    Öz-değerlendirme motoru.
    
    Cevapları eleştirel olarak değerlendirir.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def reflect(
        self,
        question: str,
        answer: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Cevabı değerlendir"""
        # Evaluate different aspects
        accuracy = await self._check_accuracy(question, answer)
        completeness = await self._check_completeness(question, answer)
        clarity = await self._check_clarity(answer)
        improvements = await self._suggest_improvements(question, answer)
        
        return {
            "accuracy_score": accuracy,
            "completeness_score": completeness,
            "clarity_score": clarity,
            "overall_score": (accuracy + completeness + clarity) / 3,
            "improvements": improvements,
        }
    
    async def _check_accuracy(self, question: str, answer: str) -> float:
        """Doğruluk kontrolü"""
        prompt = f"""Rate the accuracy of this answer on a scale of 1-10.
Only provide the number.

Question: {question}
Answer: {answer}

Accuracy (1-10):"""
        
        response = await self._call_llm(prompt, max_tokens=10)
        try:
            score = int(re.search(r'\d+', response).group())
            return min(10, max(1, score)) / 10
        except Exception:
            return 0.7
    
    async def _check_completeness(self, question: str, answer: str) -> float:
        """Tamlık kontrolü"""
        prompt = f"""Rate how completely this answer addresses the question (1-10).
Only provide the number.

Question: {question}
Answer: {answer}

Completeness (1-10):"""
        
        response = await self._call_llm(prompt, max_tokens=10)
        try:
            score = int(re.search(r'\d+', response).group())
            return min(10, max(1, score)) / 10
        except Exception:
            return 0.7
    
    async def _check_clarity(self, answer: str) -> float:
        """Netlik kontrolü"""
        # Simple heuristics
        clarity = 0.7
        
        # Good length
        word_count = len(answer.split())
        if 50 <= word_count <= 500:
            clarity += 0.1
        
        # Has structure (lists, paragraphs)
        if '\n' in answer or '-' in answer:
            clarity += 0.1
        
        # Not too many complex sentences
        sentences = answer.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
        if avg_sentence_length < 25:
            clarity += 0.1
        
        return min(1.0, clarity)
    
    async def _suggest_improvements(self, question: str, answer: str) -> List[str]:
        """İyileştirme önerileri"""
        prompt = f"""Suggest 2-3 specific improvements for this answer.
Be constructive and brief.

Question: {question}
Answer: {answer}

Improvements:"""
        
        response = await self._call_llm(prompt, max_tokens=200)
        improvements = [i.strip() for i in response.split('\n') if i.strip() and len(i.strip()) > 10]
        return improvements[:3]
    
    async def _call_llm(self, prompt: str, max_tokens: int = 200) -> str:
        """LLM çağrısı"""
        if self.llm_client:
            try:
                return await self.llm_client.generate(prompt, max_tokens=max_tokens)
            except Exception:
                pass
        
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": max_tokens, "temperature": 0.4}
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
        except Exception:
            pass
        
        return ""


# ============ PREMIUM REASONING ENGINE ============

class PremiumReasoningEngine:
    """
    Premium Reasoning Engine.
    
    Tüm reasoning yeteneklerini birleştirir.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
        # Components
        self.cot_generator = ChainOfThoughtGenerator(llm_client)
        self.debate_engine = MultiAgentDebate(llm_client)
        self.consistency_checker = SelfConsistencyChecker(llm_client)
        self.reflection_engine = ReflectionEngine(llm_client)
    
    async def reason(
        self,
        question: str,
        mode: str = "auto",  # auto, cot, debate, comprehensive
        depth: str = "standard",  # quick, standard, deep
        context: str = ""
    ) -> ReasoningResult:
        """
        Premium reasoning.
        
        Args:
            question: Soru
            mode: Reasoning modu
            depth: Derinlik
            context: Ek bağlam
        
        Returns:
            ReasoningResult
        """
        start_time = time.time()
        
        # Auto-detect best mode
        if mode == "auto":
            mode = self._detect_best_mode(question)
        
        # Execute based on mode
        if mode == "cot":
            result = await self._reason_cot(question, depth, context)
        elif mode == "debate":
            result = await self._reason_debate(question)
        else:  # comprehensive
            result = await self._reason_comprehensive(question, depth, context)
        
        result.total_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    def _detect_best_mode(self, question: str) -> str:
        """En iyi modu tespit et"""
        q_lower = question.lower()
        
        # Comparison questions -> debate
        if any(w in q_lower for w in ['karşılaştır', 'compare', 'vs', 'versus', 'mı yoksa', 'hangisi']):
            return "debate"
        
        # Complex analytical -> comprehensive
        if any(w in q_lower for w in ['analiz', 'analyze', 'değerlendir', 'evaluate', 'açıkla', 'explain why']):
            return "comprehensive"
        
        # Default -> chain of thought
        return "cot"
    
    async def _reason_cot(
        self,
        question: str,
        depth: str,
        context: str
    ) -> ReasoningResult:
        """Chain of Thought reasoning"""
        # Generate CoT
        cot = await self.cot_generator.generate(question, context, depth)
        
        # Self-consistency check (if not quick)
        if depth != "quick":
            is_consistent, consistency_score, _ = await self.consistency_checker.check_consistency(
                question, cot.final_answer
            )
        else:
            is_consistent, consistency_score = True, cot.overall_confidence
        
        # Calculate confidence level
        confidence_level = self._get_confidence_level(cot.overall_confidence)
        
        return ReasoningResult(
            question=question,
            answer=cot.final_answer,
            chain_of_thought=cot,
            confidence=cot.overall_confidence,
            confidence_level=confidence_level,
            self_consistent=is_consistent,
            reasoning_type="chain_of_thought"
        )
    
    async def _reason_debate(self, question: str) -> ReasoningResult:
        """Multi-agent debate reasoning"""
        debate = await self.debate_engine.debate(question)
        
        return ReasoningResult(
            question=question,
            answer=debate.final_synthesis,
            debate=debate,
            confidence=debate.confidence,
            confidence_level=self._get_confidence_level(debate.confidence),
            self_consistent=len(debate.consensus_points) > len(debate.disputed_points),
            reasoning_type="multi_agent_debate"
        )
    
    async def _reason_comprehensive(
        self,
        question: str,
        depth: str,
        context: str
    ) -> ReasoningResult:
        """Comprehensive reasoning with all capabilities"""
        # Step 1: Chain of Thought
        cot = await self.cot_generator.generate(question, context, depth)
        
        # Step 2: Multi-Agent Debate (if comparison question)
        debate = None
        if any(w in question.lower() for w in ['karşılaştır', 'compare', 'vs', 'hangisi']):
            debate = await self.debate_engine.debate(question, rounds=1)
        
        # Step 3: Self-Consistency
        is_consistent, consistency_score, alternatives = await self.consistency_checker.check_consistency(
            question, cot.final_answer, num_samples=2
        )
        
        # Step 4: Reflection
        reflection = await self.reflection_engine.reflect(question, cot.final_answer, context)
        
        # Combine insights
        final_answer = cot.final_answer
        
        # If debate provided different perspective, incorporate
        if debate and debate.final_synthesis:
            if debate.confidence > cot.overall_confidence:
                final_answer = f"{final_answer}\n\n**Alternatif Perspektif:**\n{debate.final_synthesis}"
        
        # Overall confidence
        confidence = (cot.overall_confidence + consistency_score + reflection.get("overall_score", 0.7)) / 3
        
        # Verification notes
        verification_notes = []
        if is_consistent:
            verification_notes.append("✓ Self-consistency verified")
        else:
            verification_notes.append("⚠ Some inconsistency detected")
        
        if reflection.get("overall_score", 0) > 0.8:
            verification_notes.append("✓ High quality answer")
        
        for improvement in reflection.get("improvements", [])[:2]:
            verification_notes.append(f"💡 {improvement}")
        
        return ReasoningResult(
            question=question,
            answer=final_answer,
            chain_of_thought=cot,
            debate=debate,
            confidence=confidence,
            confidence_level=self._get_confidence_level(confidence),
            self_consistent=is_consistent,
            verification_notes=verification_notes,
            reasoning_type="comprehensive"
        )
    
    def _get_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Güven seviyesi"""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.75:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MODERATE
        elif confidence >= 0.25:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    async def stream_reasoning(
        self,
        question: str,
        mode: str = "auto",
        depth: str = "standard"
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Streaming reasoning.
        
        Yields progress updates and steps.
        """
        if mode == "auto":
            mode = self._detect_best_mode(question)
        
        yield {"type": "start", "mode": mode, "question": question}
        
        if mode == "cot":
            # Stream CoT steps
            yield {"type": "phase", "phase": "understanding", "message": "Soruyu anlıyorum..."}
            
            cot = await self.cot_generator.generate(question, "", depth)
            
            for step in cot.steps:
                yield {
                    "type": "step",
                    "phase": step.phase.value,
                    "content": step.content,
                    "confidence": step.confidence
                }
            
            yield {
                "type": "answer",
                "answer": cot.final_answer,
                "confidence": cot.overall_confidence
            }
        
        elif mode == "debate":
            yield {"type": "phase", "phase": "debating", "message": "Tartışma başlıyor..."}
            
            debate = await self.debate_engine.debate(question, rounds=2)
            
            for arg in debate.arguments:
                yield {
                    "type": "argument",
                    "agent": arg.agent.value,
                    "position": arg.position,
                    "content": arg.content[:300]
                }
            
            yield {
                "type": "synthesis",
                "consensus": debate.consensus_points,
                "disputed": debate.disputed_points
            }
            
            yield {
                "type": "answer",
                "answer": debate.final_synthesis,
                "confidence": debate.confidence,
                "winning_position": debate.winning_position
            }
        
        yield {"type": "complete"}


# ============ SINGLETON ============

_engine: Optional[PremiumReasoningEngine] = None

def get_reasoning_engine() -> PremiumReasoningEngine:
    global _engine
    if _engine is None:
        _engine = PremiumReasoningEngine()
    return _engine


# ============ TEST ============

async def test_reasoning():
    """Test reasoning engine"""
    print("Testing Premium Reasoning Engine...")
    
    engine = get_reasoning_engine()
    
    # Test 1: Chain of Thought
    print("\n=== Test 1: Chain of Thought ===")
    result = await engine.reason(
        "Python'da async/await nasıl çalışır?",
        mode="cot",
        depth="quick"
    )
    print(f"Answer: {result.answer[:200]}...")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Steps: {len(result.chain_of_thought.steps) if result.chain_of_thought else 0}")
    
    # Test 2: Debate
    print("\n=== Test 2: Multi-Agent Debate ===")
    result = await engine.reason(
        "React vs Vue: Hangisi daha iyi?",
        mode="debate"
    )
    print(f"Synthesis: {result.answer[:200]}...")
    print(f"Winning: {result.debate.winning_position if result.debate else 'N/A'}")
    print(f"Confidence: {result.confidence:.0%}")
    
    print("\n✅ Tests completed!")


if __name__ == "__main__":
    asyncio.run(test_reasoning())
