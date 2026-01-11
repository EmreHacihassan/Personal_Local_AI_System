"""
🛡️ Advanced Guardrails System
==============================

Enterprise-grade safety and compliance guardrails.

Features:
- Input validation and sanitization
- Output filtering and moderation
- PII detection and redaction
- Topic/content restrictions
- Rate limiting
- Jailbreak detection
- Hallucination prevention
- NeMo Guardrails integration pattern
"""

import asyncio
import hashlib
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union, Pattern
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============ TYPES ============

class GuardrailType(str, Enum):
    """Types of guardrails"""
    INPUT_VALIDATION = "input_validation"
    OUTPUT_FILTER = "output_filter"
    PII_DETECTION = "pii_detection"
    TOPIC_RESTRICTION = "topic_restriction"
    TOXICITY_FILTER = "toxicity_filter"
    JAILBREAK_DETECTION = "jailbreak_detection"
    RATE_LIMIT = "rate_limit"
    HALLUCINATION_CHECK = "hallucination_check"
    CUSTOM = "custom"


class RiskLevel(str, Enum):
    """Risk levels for content"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GuardrailAction(str, Enum):
    """Actions to take when guardrail triggers"""
    ALLOW = "allow"
    WARN = "warn"
    MODIFY = "modify"
    BLOCK = "block"
    ESCALATE = "escalate"


class PIIType(str, Enum):
    """Types of PII"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    MEDICAL = "medical"


# ============ DATA MODELS ============

class GuardrailResult(BaseModel):
    """Result of a guardrail check"""
    guardrail_type: GuardrailType
    triggered: bool
    action: GuardrailAction
    risk_level: RiskLevel = RiskLevel.NONE
    message: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    modified_content: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class GuardrailContext(BaseModel):
    """Context for guardrail evaluation"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    input_text: str
    output_text: Optional[str] = None
    conversation_history: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PIIMatch(BaseModel):
    """A detected PII match"""
    pii_type: PIIType
    value: str
    start: int
    end: int
    confidence: float = 1.0


class TopicRestriction(BaseModel):
    """Topic restriction rule"""
    topic: str
    keywords: List[str]
    action: GuardrailAction = GuardrailAction.BLOCK
    message: str = "Topic restricted"


# ============ GUARDRAIL IMPLEMENTATIONS ============

class Guardrail(ABC):
    """Base class for guardrails"""
    
    @property
    @abstractmethod
    def guardrail_type(self) -> GuardrailType:
        pass
    
    @abstractmethod
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        pass


class InputValidationGuardrail(Guardrail):
    """
    Validates and sanitizes input text.
    """
    
    def __init__(
        self,
        max_length: int = 10000,
        min_length: int = 1,
        allowed_languages: Optional[List[str]] = None,
        block_patterns: Optional[List[str]] = None
    ):
        self.max_length = max_length
        self.min_length = min_length
        self.allowed_languages = allowed_languages
        self.block_patterns = [re.compile(p, re.IGNORECASE) for p in (block_patterns or [])]
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.INPUT_VALIDATION
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        text = context.input_text
        issues = []
        
        # Length check
        if len(text) > self.max_length:
            issues.append(f"Input too long ({len(text)} > {self.max_length})")
        
        if len(text) < self.min_length:
            issues.append(f"Input too short ({len(text)} < {self.min_length})")
        
        # Pattern blocking
        for pattern in self.block_patterns:
            if pattern.search(text):
                issues.append(f"Blocked pattern detected: {pattern.pattern}")
        
        # Empty/whitespace check
        if not text.strip():
            issues.append("Input is empty or whitespace only")
        
        if issues:
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.BLOCK,
                risk_level=RiskLevel.MEDIUM,
                message="; ".join(issues),
                details={"issues": issues}
            )
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW
        )


class PIIDetectionGuardrail(Guardrail):
    """
    Detects and optionally redacts PII.
    """
    
    def __init__(
        self,
        redact: bool = True,
        pii_types: Optional[List[PIIType]] = None
    ):
        self.redact = redact
        self.pii_types = pii_types or list(PIIType)
        
        # PII patterns
        self.patterns: Dict[PIIType, Pattern] = {
            PIIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            PIIType.PHONE: re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
            ),
            PIIType.SSN: re.compile(
                r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
            ),
            PIIType.CREDIT_CARD: re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),
            PIIType.IP_ADDRESS: re.compile(
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
            ),
        }
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.PII_DETECTION
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        text = context.input_text
        matches: List[PIIMatch] = []
        
        for pii_type in self.pii_types:
            if pii_type in self.patterns:
                pattern = self.patterns[pii_type]
                for match in pattern.finditer(text):
                    matches.append(PIIMatch(
                        pii_type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end()
                    ))
        
        if matches:
            # Optionally redact
            modified = text
            if self.redact:
                # Sort by position (reverse) to maintain indices
                for m in sorted(matches, key=lambda x: x.start, reverse=True):
                    placeholder = f"[{m.pii_type.value.upper()}_REDACTED]"
                    modified = modified[:m.start] + placeholder + modified[m.end:]
            
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.MODIFY if self.redact else GuardrailAction.WARN,
                risk_level=RiskLevel.HIGH,
                message=f"Detected {len(matches)} PII item(s)",
                details={
                    "matches": [m.model_dump() for m in matches],
                    "count": len(matches)
                },
                modified_content=modified if self.redact else None
            )
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW
        )


class ToxicityFilterGuardrail(Guardrail):
    """
    Filters toxic/harmful content.
    """
    
    def __init__(
        self,
        toxic_keywords: Optional[List[str]] = None,
        use_ml_model: bool = False
    ):
        self.use_ml_model = use_ml_model
        
        # Basic toxic keywords (extend in production)
        self.toxic_keywords = set(toxic_keywords or [
            "hate", "kill", "attack", "violence", "racist",
            "sexist", "discriminate", "abuse", "threat", "harass"
        ])
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.TOXICITY_FILTER
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        text = context.input_text.lower()
        found_toxic = []
        
        # Keyword-based detection
        for keyword in self.toxic_keywords:
            if keyword in text:
                found_toxic.append(keyword)
        
        if found_toxic:
            risk = RiskLevel.HIGH if len(found_toxic) > 2 else RiskLevel.MEDIUM
            
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.BLOCK,
                risk_level=risk,
                message=f"Potentially toxic content detected",
                details={"keywords": found_toxic}
            )
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW
        )


class TopicRestrictionGuardrail(Guardrail):
    """
    Restricts certain topics.
    """
    
    def __init__(self, restrictions: Optional[List[TopicRestriction]] = None):
        self.restrictions = restrictions or []
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.TOPIC_RESTRICTION
    
    def add_restriction(self, restriction: TopicRestriction):
        """Add a topic restriction"""
        self.restrictions.append(restriction)
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        text = context.input_text.lower()
        
        for restriction in self.restrictions:
            for keyword in restriction.keywords:
                if keyword.lower() in text:
                    return GuardrailResult(
                        guardrail_type=self.guardrail_type,
                        triggered=True,
                        action=restriction.action,
                        risk_level=RiskLevel.MEDIUM,
                        message=restriction.message,
                        details={
                            "topic": restriction.topic,
                            "matched_keyword": keyword
                        }
                    )
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW
        )


class JailbreakDetectionGuardrail(Guardrail):
    """
    Detects jailbreak/prompt injection attempts.
    """
    
    def __init__(self):
        # Common jailbreak patterns
        self.patterns = [
            r"ignore (all |previous |above )?instructions",
            r"forget (all |your |previous )?instructions",
            r"disregard (all |your |previous )?instructions",
            r"you are now (?:DAN|evil|unrestricted)",
            r"pretend you (?:are|can|have)",
            r"act as (?:if|though)",
            r"bypass (?:your |the )?(?:rules|restrictions|filters)",
            r"from now on",
            r"new persona",
            r"jailbreak",
            r"developer mode",
            r"\[system\]|\[admin\]|\[root\]",
            r"sudo",
            r"override",
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.JAILBREAK_DETECTION
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        text = context.input_text
        detected = []
        
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                detected.append(pattern.pattern)
        
        if detected:
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.BLOCK,
                risk_level=RiskLevel.CRITICAL,
                message="Potential jailbreak/prompt injection detected",
                details={"patterns_matched": detected}
            )
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW
        )


class RateLimitGuardrail(Guardrail):
    """
    Rate limiting guardrail.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        
        # In-memory rate tracking (use Redis in production)
        self.minute_counts: Dict[str, List[datetime]] = {}
        self.hour_counts: Dict[str, List[datetime]] = {}
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.RATE_LIMIT
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        user_id = context.user_id or "anonymous"
        now = datetime.now()
        
        # Clean old entries
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Minute check
        if user_id not in self.minute_counts:
            self.minute_counts[user_id] = []
        self.minute_counts[user_id] = [
            t for t in self.minute_counts[user_id] if t > minute_ago
        ]
        
        # Hour check
        if user_id not in self.hour_counts:
            self.hour_counts[user_id] = []
        self.hour_counts[user_id] = [
            t for t in self.hour_counts[user_id] if t > hour_ago
        ]
        
        # Check limits
        minute_count = len(self.minute_counts[user_id])
        hour_count = len(self.hour_counts[user_id])
        
        if minute_count >= self.rpm:
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.BLOCK,
                risk_level=RiskLevel.MEDIUM,
                message=f"Rate limit exceeded: {minute_count}/{self.rpm} requests/minute",
                details={"minute_count": minute_count, "limit": self.rpm}
            )
        
        if hour_count >= self.rph:
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.BLOCK,
                risk_level=RiskLevel.MEDIUM,
                message=f"Rate limit exceeded: {hour_count}/{self.rph} requests/hour",
                details={"hour_count": hour_count, "limit": self.rph}
            )
        
        # Record this request
        self.minute_counts[user_id].append(now)
        self.hour_counts[user_id].append(now)
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW,
            details={
                "minute_count": minute_count + 1,
                "hour_count": hour_count + 1
            }
        )


class HallucinationCheckGuardrail(Guardrail):
    """
    Checks for potential hallucinations in output.
    Requires context/sources to verify against.
    """
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
    
    @property
    def guardrail_type(self) -> GuardrailType:
        return GuardrailType.HALLUCINATION_CHECK
    
    async def check(self, context: GuardrailContext) -> GuardrailResult:
        if not context.output_text:
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=False,
                action=GuardrailAction.ALLOW,
                message="No output to check"
            )
        
        # Check for common hallucination indicators
        indicators = []
        output = context.output_text.lower()
        
        # Uncertain language that might indicate fabrication
        uncertainty_phrases = [
            "i believe", "i think", "probably", "might be",
            "as far as i know", "to my knowledge"
        ]
        
        # Claims without support
        unsupported_claims = [
            "studies show", "research indicates", "according to",
            "experts say", "it is known that"
        ]
        
        for phrase in uncertainty_phrases:
            if phrase in output:
                indicators.append(f"Uncertainty phrase: '{phrase}'")
        
        for phrase in unsupported_claims:
            if phrase in output:
                indicators.append(f"Potential unsupported claim: '{phrase}'")
        
        # Check for fabricated statistics
        if re.search(r'\b\d+(\.\d+)?%\b', output):
            indicators.append("Contains percentage - verify accuracy")
        
        if re.search(r'in \d{4}', output):
            indicators.append("Contains year reference - verify accuracy")
        
        if indicators:
            return GuardrailResult(
                guardrail_type=self.guardrail_type,
                triggered=True,
                action=GuardrailAction.WARN,
                risk_level=RiskLevel.LOW,
                message="Potential hallucination indicators detected",
                details={"indicators": indicators}
            )
        
        return GuardrailResult(
            guardrail_type=self.guardrail_type,
            triggered=False,
            action=GuardrailAction.ALLOW
        )


# ============ GUARDRAIL ORCHESTRATOR ============

class GuardrailOrchestrator:
    """
    Orchestrates multiple guardrails.
    """
    
    def __init__(self):
        self.input_guardrails: List[Guardrail] = []
        self.output_guardrails: List[Guardrail] = []
        self.all_guardrails: List[Guardrail] = []
    
    def add_input_guardrail(self, guardrail: Guardrail):
        """Add a guardrail for input checking"""
        self.input_guardrails.append(guardrail)
        self.all_guardrails.append(guardrail)
    
    def add_output_guardrail(self, guardrail: Guardrail):
        """Add a guardrail for output checking"""
        self.output_guardrails.append(guardrail)
        self.all_guardrails.append(guardrail)
    
    async def check_input(
        self,
        text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, List[GuardrailResult], str]:
        """
        Check input against all input guardrails.
        
        Returns:
            (allowed, results, modified_text)
        """
        context = GuardrailContext(
            user_id=user_id,
            session_id=session_id,
            input_text=text,
            metadata=metadata or {}
        )
        
        results = []
        modified_text = text
        allowed = True
        
        for guardrail in self.input_guardrails:
            result = await guardrail.check(context)
            results.append(result)
            
            if result.triggered:
                if result.action == GuardrailAction.BLOCK:
                    allowed = False
                elif result.action == GuardrailAction.MODIFY and result.modified_content:
                    modified_text = result.modified_content
                    context.input_text = modified_text
        
        return allowed, results, modified_text
    
    async def check_output(
        self,
        input_text: str,
        output_text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, List[GuardrailResult], str]:
        """
        Check output against all output guardrails.
        
        Returns:
            (allowed, results, modified_text)
        """
        context = GuardrailContext(
            user_id=user_id,
            session_id=session_id,
            input_text=input_text,
            output_text=output_text,
            metadata=metadata or {}
        )
        
        results = []
        modified_text = output_text
        allowed = True
        
        for guardrail in self.output_guardrails:
            result = await guardrail.check(context)
            results.append(result)
            
            if result.triggered:
                if result.action == GuardrailAction.BLOCK:
                    allowed = False
                elif result.action == GuardrailAction.MODIFY and result.modified_content:
                    modified_text = result.modified_content
        
        return allowed, results, modified_text


# ============ NEMO-STYLE RAILS ============

class Rail(BaseModel):
    """A NeMo-style rail definition"""
    name: str
    description: str
    condition: str  # Python expression
    action: GuardrailAction
    response: Optional[str] = None


class NeMoStyleGuardrails:
    """
    NeMo Guardrails-style declarative guardrails.
    
    Define rails as conditions and actions.
    """
    
    def __init__(self):
        self.rails: List[Rail] = []
        self.flow_rules: Dict[str, List[str]] = {}
    
    def add_rail(self, rail: Rail):
        """Add a rail"""
        self.rails.append(rail)
    
    def define_flow(self, name: str, allowed_actions: List[str]):
        """Define an allowed flow"""
        self.flow_rules[name] = allowed_actions
    
    async def check(
        self,
        context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check context against rails.
        
        Returns:
            (allowed, action_taken, response_message)
        """
        for rail in self.rails:
            try:
                # Evaluate condition
                if eval(rail.condition, {"context": context}):
                    if rail.action == GuardrailAction.BLOCK:
                        return False, rail.name, rail.response
                    elif rail.action == GuardrailAction.WARN:
                        logger.warning(f"Rail triggered: {rail.name}")
            except Exception as e:
                logger.error(f"Rail condition error ({rail.name}): {e}")
        
        return True, None, None


# ============ CONVENIENCE FUNCTIONS ============

def create_default_guardrails() -> GuardrailOrchestrator:
    """
    Create orchestrator with default guardrails.
    """
    orchestrator = GuardrailOrchestrator()
    
    # Input guardrails
    orchestrator.add_input_guardrail(InputValidationGuardrail())
    orchestrator.add_input_guardrail(PIIDetectionGuardrail(redact=True))
    orchestrator.add_input_guardrail(ToxicityFilterGuardrail())
    orchestrator.add_input_guardrail(JailbreakDetectionGuardrail())
    orchestrator.add_input_guardrail(RateLimitGuardrail())
    
    # Output guardrails
    orchestrator.add_output_guardrail(PIIDetectionGuardrail(redact=True))
    orchestrator.add_output_guardrail(ToxicityFilterGuardrail())
    orchestrator.add_output_guardrail(HallucinationCheckGuardrail())
    
    return orchestrator


async def safe_generate(
    generate_fn: Callable[[str], str],
    input_text: str,
    guardrails: Optional[GuardrailOrchestrator] = None,
    user_id: Optional[str] = None
) -> Tuple[str, List[GuardrailResult]]:
    """
    Safely generate response with guardrails.
    
    Args:
        generate_fn: The LLM generation function
        input_text: User input
        guardrails: Guardrail orchestrator (creates default if None)
        user_id: User identifier for rate limiting
        
    Returns:
        (response, all_guardrail_results)
    """
    if guardrails is None:
        guardrails = create_default_guardrails()
    
    all_results = []
    
    # Check input
    allowed, input_results, safe_input = await guardrails.check_input(
        input_text, user_id=user_id
    )
    all_results.extend(input_results)
    
    if not allowed:
        blocked_result = next(
            (r for r in input_results if r.action == GuardrailAction.BLOCK),
            None
        )
        message = blocked_result.message if blocked_result else "Input blocked"
        return f"I cannot process that request. {message}", all_results
    
    # Generate response
    try:
        response = generate_fn(safe_input)
    except Exception as e:
        return f"Error generating response: {str(e)}", all_results
    
    # Check output
    allowed, output_results, safe_output = await guardrails.check_output(
        safe_input, response, user_id=user_id
    )
    all_results.extend(output_results)
    
    if not allowed:
        return "I cannot provide that response.", all_results
    
    return safe_output, all_results


# ============ EXPORTS ============

__all__ = [
    # Types
    "GuardrailType",
    "RiskLevel",
    "GuardrailAction",
    "PIIType",
    # Models
    "GuardrailResult",
    "GuardrailContext",
    "PIIMatch",
    "TopicRestriction",
    "Rail",
    # Guardrails
    "Guardrail",
    "InputValidationGuardrail",
    "PIIDetectionGuardrail",
    "ToxicityFilterGuardrail",
    "TopicRestrictionGuardrail",
    "JailbreakDetectionGuardrail",
    "RateLimitGuardrail",
    "HallucinationCheckGuardrail",
    # Orchestrator
    "GuardrailOrchestrator",
    "NeMoStyleGuardrails",
    # Factory
    "create_default_guardrails",
    "safe_generate",
]
