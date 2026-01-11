"""
🤖 Multi-Agent Debate System
============================

Multi-agent debate ve consensus sistemi.
Birden fazla LLM agent'ın tartışarak daha iyi yanıtlar üretmesi.

Features:
- Debate-style reasoning
- Devil's advocate
- Consensus building
- Confidence calibration
- Judge agent for evaluation
"""

import asyncio
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class AgentRole(str, Enum):
    """Agent roles in debate"""
    PROPONENT = "proponent"  # Supports a position
    OPPONENT = "opponent"  # Challenges the position
    CRITIC = "critic"  # Points out flaws
    SYNTHESIZER = "synthesizer"  # Combines views
    JUDGE = "judge"  # Evaluates arguments
    DEVIL_ADVOCATE = "devil_advocate"  # Extreme opposition
    EXPERT = "expert"  # Domain specialist
    SKEPTIC = "skeptic"  # Questions everything


class DebatePhase(str, Enum):
    """Phases of debate"""
    OPENING = "opening"
    ARGUMENTS = "arguments"
    REBUTTAL = "rebuttal"
    SYNTHESIS = "synthesis"
    JUDGMENT = "judgment"
    CONSENSUS = "consensus"


class VoteType(str, Enum):
    """Types of voting"""
    MAJORITY = "majority"
    UNANIMOUS = "unanimous"
    WEIGHTED = "weighted"
    JUDGE_DECIDES = "judge_decides"


# ============ DATA MODELS ============

class Argument(BaseModel):
    """A single argument in debate"""
    agent_id: str
    role: AgentRole
    content: str
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    references: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    in_response_to: Optional[str] = None  # Previous argument ID
    
    def to_debate_format(self) -> str:
        """Format for debate context"""
        role_emoji = {
            AgentRole.PROPONENT: "✅",
            AgentRole.OPPONENT: "❌",
            AgentRole.CRITIC: "🔍",
            AgentRole.SYNTHESIZER: "🔄",
            AgentRole.JUDGE: "⚖️",
            AgentRole.DEVIL_ADVOCATE: "😈",
            AgentRole.EXPERT: "🎓",
            AgentRole.SKEPTIC: "🤔"
        }
        
        emoji = role_emoji.get(self.role, "💬")
        return f"{emoji} [{self.role.value.upper()}] (Confidence: {self.confidence:.0%})\n{self.content}"


class Vote(BaseModel):
    """An agent's vote"""
    agent_id: str
    position: str  # The position being voted on
    support: bool
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    reasoning: str = ""


class DebateResult(BaseModel):
    """Result of a debate"""
    question: str
    final_answer: str
    consensus_level: float = Field(0.0, ge=0.0, le=1.0)
    arguments: List[Argument] = Field(default_factory=list)
    votes: List[Vote] = Field(default_factory=list)
    phases_completed: List[DebatePhase] = Field(default_factory=list)
    total_rounds: int = 0
    winning_position: Optional[str] = None
    dissenting_views: List[str] = Field(default_factory=list)
    confidence_calibration: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentPersona(BaseModel):
    """Persona for a debate agent"""
    agent_id: str
    role: AgentRole
    name: str
    expertise: List[str] = Field(default_factory=list)
    personality_traits: List[str] = Field(default_factory=list)
    bias: Optional[str] = None  # Intentional bias for diversity
    system_prompt: str = ""


# ============ DEBATE AGENTS ============

class DebateAgent:
    """
    A single agent in the debate system.
    """
    
    def __init__(
        self,
        persona: AgentPersona,
        llm: Callable[[str], str],
        temperature: float = 0.7
    ):
        self.persona = persona
        self.llm = llm
        self.temperature = temperature
        self.argument_history: List[Argument] = []
    
    async def generate_argument(
        self,
        question: str,
        context: str,
        previous_arguments: List[Argument],
        phase: DebatePhase
    ) -> Argument:
        """Generate an argument based on role and context"""
        # Build prompt based on role
        role_instructions = self._get_role_instructions(phase)
        
        # Format previous arguments
        prev_args_text = "\n\n".join(
            a.to_debate_format() for a in previous_arguments[-5:]
        )
        
        prompt = f"""{self.persona.system_prompt}

{role_instructions}

QUESTION: {question}

CONTEXT:
{context}

PREVIOUS ARGUMENTS:
{prev_args_text if prev_args_text else "None yet."}

Based on your role as {self.persona.role.value}, provide your argument.
Include:
1. Your main point
2. Supporting evidence or reasoning
3. Your confidence level (0-100%)

YOUR ARGUMENT:"""
        
        # Generate response
        response = self.llm(prompt)
        
        # Parse confidence from response
        confidence = self._extract_confidence(response)
        
        argument = Argument(
            agent_id=self.persona.agent_id,
            role=self.persona.role,
            content=response,
            confidence=confidence,
            in_response_to=previous_arguments[-1].agent_id if previous_arguments else None
        )
        
        self.argument_history.append(argument)
        return argument
    
    async def vote(
        self,
        question: str,
        positions: List[str],
        all_arguments: List[Argument]
    ) -> Vote:
        """Vote on the best position"""
        args_summary = "\n".join(
            f"- {a.role.value}: {a.content[:200]}..." for a in all_arguments
        )
        
        positions_text = "\n".join(f"{i+1}. {p}" for i, p in enumerate(positions))
        
        prompt = f"""Based on the debate about: {question}

ARGUMENTS PRESENTED:
{args_summary}

POSITIONS TO VOTE ON:
{positions_text}

As a {self.persona.role.value}, which position do you support?
Respond with:
1. Position number (1-{len(positions)})
2. Your confidence (0-100%)
3. Brief reasoning

YOUR VOTE:"""
        
        response = self.llm(prompt)
        
        # Parse vote (simple heuristic)
        supported_position = positions[0]  # Default
        for i, pos in enumerate(positions):
            if str(i+1) in response[:50]:
                supported_position = pos
                break
        
        confidence = self._extract_confidence(response)
        
        return Vote(
            agent_id=self.persona.agent_id,
            position=supported_position,
            support=True,
            confidence=confidence,
            reasoning=response
        )
    
    def _get_role_instructions(self, phase: DebatePhase) -> str:
        """Get instructions based on role and phase"""
        instructions = {
            AgentRole.PROPONENT: {
                DebatePhase.OPENING: "Present the strongest case FOR the proposition.",
                DebatePhase.ARGUMENTS: "Strengthen your position with evidence.",
                DebatePhase.REBUTTAL: "Address criticisms and reinforce your points.",
            },
            AgentRole.OPPONENT: {
                DebatePhase.OPENING: "Present the strongest case AGAINST the proposition.",
                DebatePhase.ARGUMENTS: "Challenge the proponent's claims.",
                DebatePhase.REBUTTAL: "Point out flaws in opposing arguments.",
            },
            AgentRole.CRITIC: {
                DebatePhase.OPENING: "Identify potential weaknesses in all positions.",
                DebatePhase.ARGUMENTS: "Question assumptions and logic.",
                DebatePhase.REBUTTAL: "Highlight unaddressed concerns.",
            },
            AgentRole.SYNTHESIZER: {
                DebatePhase.OPENING: "Look for common ground between positions.",
                DebatePhase.ARGUMENTS: "Identify areas of agreement.",
                DebatePhase.SYNTHESIS: "Combine the strongest elements of each view.",
            },
            AgentRole.DEVIL_ADVOCATE: {
                DebatePhase.OPENING: "Take the most extreme opposing view possible.",
                DebatePhase.ARGUMENTS: "Push back hard on any consensus.",
                DebatePhase.REBUTTAL: "Find edge cases and counterexamples.",
            },
            AgentRole.SKEPTIC: {
                DebatePhase.OPENING: "Question whether we can know the answer at all.",
                DebatePhase.ARGUMENTS: "Demand strong evidence for all claims.",
                DebatePhase.REBUTTAL: "Point out uncertainties and unknowns.",
            },
        }
        
        role_instructions = instructions.get(self.persona.role, {})
        return role_instructions.get(
            phase, 
            f"Participate as a {self.persona.role.value} in the {phase.value} phase."
        )
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from text"""
        import re
        
        patterns = [
            r'confidence[:\s]+(\d+)%',
            r'(\d+)%\s*confidence',
            r'(\d+)%',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return min(100, max(0, int(match.group(1)))) / 100
        
        return 0.5  # Default confidence


class JudgeAgent:
    """
    Judge agent that evaluates debate and determines winner.
    """
    
    def __init__(self, llm: Callable[[str], str]):
        self.llm = llm
    
    async def evaluate_debate(
        self,
        question: str,
        arguments: List[Argument],
        positions: List[str]
    ) -> Tuple[str, float, str]:
        """
        Evaluate the debate and determine the winning position.
        
        Returns:
            Tuple of (winning_position, confidence, reasoning)
        """
        args_by_role = {}
        for arg in arguments:
            if arg.role not in args_by_role:
                args_by_role[arg.role] = []
            args_by_role[arg.role].append(arg)
        
        debate_summary = []
        for role, args in args_by_role.items():
            summary = f"**{role.value.upper()}**:\n"
            for a in args:
                summary += f"- {a.content[:300]}... (confidence: {a.confidence:.0%})\n"
            debate_summary.append(summary)
        
        prompt = f"""You are an impartial judge evaluating a debate.

QUESTION: {question}

POSITIONS:
{chr(10).join(f'{i+1}. {p}' for i, p in enumerate(positions))}

DEBATE SUMMARY:
{chr(10).join(debate_summary)}

As a fair judge, evaluate:
1. Which position is best supported by evidence and reasoning?
2. What is your confidence in this judgment?
3. What are the key factors in your decision?

Provide your judgment:
- Winning position number (1-{len(positions)})
- Confidence (0-100%)
- Reasoning (2-3 sentences)

JUDGMENT:"""
        
        response = self.llm(prompt)
        
        # Parse judgment
        winning = positions[0]
        for i, pos in enumerate(positions):
            if str(i+1) in response[:100]:
                winning = pos
                break
        
        # Extract confidence
        import re
        confidence = 0.5
        match = re.search(r'(\d+)%', response)
        if match:
            confidence = int(match.group(1)) / 100
        
        return winning, confidence, response


# ============ DEBATE ORCHESTRATOR ============

class DebateOrchestrator:
    """
    Orchestrates multi-agent debates.
    
    Manages:
    - Agent assignment
    - Turn-taking
    - Phase transitions
    - Consensus building
    - Final judgment
    """
    
    def __init__(
        self,
        llm_factory: Callable[[], Callable[[str], str]],
        num_agents: int = 4,
        max_rounds: int = 3,
        vote_type: VoteType = VoteType.WEIGHTED
    ):
        self.llm_factory = llm_factory
        self.num_agents = num_agents
        self.max_rounds = max_rounds
        self.vote_type = vote_type
        
        self.agents: List[DebateAgent] = []
        self.judge: Optional[JudgeAgent] = None
    
    def _create_agents(self, question: str) -> List[DebateAgent]:
        """Create debate agents with diverse roles"""
        roles = [
            AgentRole.PROPONENT,
            AgentRole.OPPONENT,
            AgentRole.CRITIC,
            AgentRole.SYNTHESIZER,
        ]
        
        if self.num_agents > 4:
            roles.extend([
                AgentRole.DEVIL_ADVOCATE,
                AgentRole.SKEPTIC,
                AgentRole.EXPERT,
            ][:self.num_agents - 4])
        
        agents = []
        for i, role in enumerate(roles[:self.num_agents]):
            persona = AgentPersona(
                agent_id=f"agent_{i}_{role.value}",
                role=role,
                name=f"{role.value.title()} Agent",
                system_prompt=f"You are a {role.value} in a structured debate. Your goal is to contribute meaningfully from your perspective."
            )
            
            agent = DebateAgent(
                persona=persona,
                llm=self.llm_factory()
            )
            agents.append(agent)
        
        return agents
    
    async def debate(
        self,
        question: str,
        context: str = "",
        initial_positions: Optional[List[str]] = None
    ) -> DebateResult:
        """
        Run a full debate on a question.
        
        Args:
            question: The question to debate
            context: Background context/information
            initial_positions: Optional starting positions
            
        Returns:
            DebateResult with final answer and metadata
        """
        logger.info(f"Starting debate: {question[:50]}...")
        
        # Create agents
        self.agents = self._create_agents(question)
        self.judge = JudgeAgent(self.llm_factory())
        
        # Generate initial positions if not provided
        if not initial_positions:
            initial_positions = await self._generate_positions(question, context)
        
        all_arguments: List[Argument] = []
        phases_completed: List[DebatePhase] = []
        
        # Phase 1: Opening statements
        logger.info("Phase: Opening statements")
        opening_args = await self._run_phase(
            DebatePhase.OPENING, question, context, []
        )
        all_arguments.extend(opening_args)
        phases_completed.append(DebatePhase.OPENING)
        
        # Phase 2-3: Arguments and Rebuttals
        for round_num in range(self.max_rounds):
            logger.info(f"Phase: Arguments (Round {round_num + 1})")
            
            args = await self._run_phase(
                DebatePhase.ARGUMENTS, question, context, all_arguments
            )
            all_arguments.extend(args)
            
            if round_num < self.max_rounds - 1:
                rebuttal_args = await self._run_phase(
                    DebatePhase.REBUTTAL, question, context, all_arguments
                )
                all_arguments.extend(rebuttal_args)
        
        phases_completed.extend([DebatePhase.ARGUMENTS, DebatePhase.REBUTTAL])
        
        # Phase 4: Synthesis
        logger.info("Phase: Synthesis")
        synthesis_agents = [a for a in self.agents if a.persona.role == AgentRole.SYNTHESIZER]
        if synthesis_agents:
            synthesis_args = await self._run_phase(
                DebatePhase.SYNTHESIS, question, context, all_arguments,
                agents=synthesis_agents
            )
            all_arguments.extend(synthesis_args)
        phases_completed.append(DebatePhase.SYNTHESIS)
        
        # Phase 5: Voting
        logger.info("Phase: Voting")
        votes = await self._collect_votes(question, initial_positions, all_arguments)
        
        # Phase 6: Judgment
        logger.info("Phase: Judgment")
        winning_position, judge_confidence, judgment_reasoning = await self.judge.evaluate_debate(
            question, all_arguments, initial_positions
        )
        phases_completed.append(DebatePhase.JUDGMENT)
        
        # Calculate consensus
        consensus = self._calculate_consensus(votes, winning_position)
        
        # Generate final answer
        final_answer = await self._generate_final_answer(
            question, winning_position, all_arguments, consensus
        )
        
        # Identify dissenting views
        dissenting = self._get_dissenting_views(votes, winning_position)
        
        return DebateResult(
            question=question,
            final_answer=final_answer,
            consensus_level=consensus,
            arguments=all_arguments,
            votes=votes,
            phases_completed=phases_completed,
            total_rounds=self.max_rounds,
            winning_position=winning_position,
            dissenting_views=dissenting,
            confidence_calibration=judge_confidence,
            metadata={
                "judgment_reasoning": judgment_reasoning,
                "num_agents": len(self.agents),
                "vote_type": self.vote_type.value
            }
        )
    
    async def _generate_positions(self, question: str, context: str) -> List[str]:
        """Generate initial positions to debate"""
        llm = self.llm_factory()
        
        prompt = f"""Given this question: {question}

Context: {context}

Generate 2-3 distinct positions that could be debated:
1. 
2.
3.

POSITIONS:"""
        
        response = llm(prompt)
        
        # Parse positions
        import re
        positions = re.findall(r'\d+\.\s*(.+)', response)
        
        if len(positions) < 2:
            positions = [
                f"Yes, {question.lower().replace('?', '')}",
                f"No, {question.lower().replace('?', '')} is not the case"
            ]
        
        return positions[:3]
    
    async def _run_phase(
        self,
        phase: DebatePhase,
        question: str,
        context: str,
        previous_arguments: List[Argument],
        agents: Optional[List[DebateAgent]] = None
    ) -> List[Argument]:
        """Run a debate phase with agents"""
        agents = agents or self.agents
        arguments = []
        
        # Agents take turns
        for agent in agents:
            arg = await agent.generate_argument(
                question, context, previous_arguments + arguments, phase
            )
            arguments.append(arg)
        
        return arguments
    
    async def _collect_votes(
        self,
        question: str,
        positions: List[str],
        all_arguments: List[Argument]
    ) -> List[Vote]:
        """Collect votes from all agents"""
        votes = []
        
        for agent in self.agents:
            vote = await agent.vote(question, positions, all_arguments)
            votes.append(vote)
        
        return votes
    
    def _calculate_consensus(self, votes: List[Vote], winning_position: str) -> float:
        """Calculate consensus level"""
        if not votes:
            return 0.0
        
        if self.vote_type == VoteType.WEIGHTED:
            # Weighted by confidence
            total_weight = sum(v.confidence for v in votes)
            supporting_weight = sum(
                v.confidence for v in votes 
                if v.position == winning_position
            )
            return supporting_weight / total_weight if total_weight > 0 else 0.0
        
        elif self.vote_type == VoteType.MAJORITY:
            supporting = sum(1 for v in votes if v.position == winning_position)
            return supporting / len(votes)
        
        elif self.vote_type == VoteType.UNANIMOUS:
            all_agree = all(v.position == winning_position for v in votes)
            return 1.0 if all_agree else 0.0
        
        return 0.5
    
    async def _generate_final_answer(
        self,
        question: str,
        winning_position: str,
        all_arguments: List[Argument],
        consensus: float
    ) -> str:
        """Generate final synthesized answer"""
        llm = self.llm_factory()
        
        # Get best arguments for winning position
        supporting_args = [
            a for a in all_arguments 
            if a.role in [AgentRole.PROPONENT, AgentRole.SYNTHESIZER]
        ]
        
        args_text = "\n".join(a.content[:200] for a in supporting_args[-3:])
        
        prompt = f"""Based on a multi-agent debate about:
Question: {question}

Winning Position: {winning_position}
Consensus Level: {consensus:.0%}

Key Arguments:
{args_text}

Provide a final, well-reasoned answer that:
1. Clearly states the conclusion
2. Acknowledges any uncertainties
3. Notes the level of agreement

FINAL ANSWER:"""
        
        return llm(prompt)
    
    def _get_dissenting_views(self, votes: List[Vote], winning: str) -> List[str]:
        """Get dissenting views from the debate"""
        dissenting = []
        
        for vote in votes:
            if vote.position != winning and vote.confidence > 0.5:
                dissenting.append(
                    f"{vote.position} (confidence: {vote.confidence:.0%})"
                )
        
        return dissenting


# ============ SIMPLE DEBATE FUNCTION ============

async def multi_agent_debate(
    question: str,
    llm: Callable[[str], str],
    context: str = "",
    num_agents: int = 4,
    max_rounds: int = 2
) -> DebateResult:
    """
    Simple function to run a multi-agent debate.
    
    Args:
        question: Question to debate
        llm: LLM function
        context: Background context
        num_agents: Number of debate agents
        max_rounds: Maximum debate rounds
        
    Returns:
        DebateResult
    """
    orchestrator = DebateOrchestrator(
        llm_factory=lambda: llm,
        num_agents=num_agents,
        max_rounds=max_rounds
    )
    
    return await orchestrator.debate(question, context)


# ============ EXPORTS ============

__all__ = [
    # Types
    "AgentRole",
    "DebatePhase",
    "VoteType",
    # Models
    "Argument",
    "Vote",
    "DebateResult",
    "AgentPersona",
    # Agents
    "DebateAgent",
    "JudgeAgent",
    # Orchestrator
    "DebateOrchestrator",
    # Functions
    "multi_agent_debate",
]
