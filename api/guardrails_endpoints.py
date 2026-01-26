"""
🛡️ Premium Guardrails API Endpoints
====================================

Enterprise-grade safety and compliance endpoints.

Features:
- Advanced PII detection and redaction
- Jailbreak/prompt injection detection
- Toxicity filtering
- Rate limiting with user context
- Hallucination prevention
- NeMo-style declarative rails
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/guardrails", tags=["Guardrails"])


# ============================================================================
# MODELS
# ============================================================================

class GuardrailCheckRequest(BaseModel):
    """Guardrail check request"""
    text: str = Field(..., description="Text to check")
    check_type: str = Field("input", description="input or output")
    user_id: Optional[str] = Field(None, description="User ID for rate limiting")
    session_id: Optional[str] = Field(None, description="Session ID")
    context: Optional[str] = Field(None, description="Context for hallucination check")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AdvancedCheckRequest(BaseModel):
    """Advanced guardrail check with all features"""
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    checks: List[str] = Field(
        default=["input_validation", "pii", "jailbreak", "toxicity", "rate_limit"],
        description="Which checks to run"
    )
    redact_pii: bool = Field(True, description="Whether to redact detected PII")
    context: Optional[str] = Field(None, description="Context for output validation")


class PIIRedactRequest(BaseModel):
    """PII redaction request"""
    text: str
    pii_types: Optional[List[str]] = Field(
        default=["email", "phone", "ssn", "credit_card"],
        description="PII types to detect"
    )


class JailbreakCheckRequest(BaseModel):
    """Jailbreak detection request"""
    text: str
    sensitivity: str = Field("medium", description="low, medium, high")


class RateLimitCheckRequest(BaseModel):
    """Rate limit check request"""
    user_id: str
    action: str = Field("request", description="Action type to rate limit")


class TopicRestrictionRequest(BaseModel):
    """Add topic restriction"""
    topic: str
    keywords: List[str]
    action: str = Field("block", description="allow, warn, modify, block")
    message: Optional[str] = None


class CustomRailRequest(BaseModel):
    """Add custom NeMo-style rail"""
    name: str
    description: str
    condition: str  # Python expression
    action: str = Field("block", description="allow, warn, modify, block")
    response: Optional[str] = None


class SafeGenerateRequest(BaseModel):
    """Safe LLM generation request"""
    prompt: str
    user_id: Optional[str] = None
    context: Optional[str] = None


# ============================================================================
# GUARDRAIL INSTANCES
# ============================================================================

_orchestrator = None
_nemo_rails = None


def get_orchestrator():
    """Get or create guardrail orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        try:
            from core.advanced_guardrails import create_default_guardrails
            _orchestrator = create_default_guardrails()
            logger.info("🛡️ Advanced guardrails initialized")
        except Exception as e:
            logger.warning(f"Failed to load advanced guardrails: {e}")
            # Fallback to basic guardrails
            from core.guardrails import Guardrails, GuardLevel
            _orchestrator = Guardrails(GuardLevel.MEDIUM)
    return _orchestrator


def get_nemo_rails():
    """Get or create NeMo-style rails"""
    global _nemo_rails
    if _nemo_rails is None:
        try:
            from core.advanced_guardrails import NeMoStyleGuardrails
            _nemo_rails = NeMoStyleGuardrails()
            logger.info("📋 NeMo-style rails initialized")
        except Exception as e:
            logger.warning(f"Failed to load NeMo rails: {e}")
    return _nemo_rails


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/status")
async def get_guardrails_status():
    """Get guardrails system status"""
    orchestrator = get_orchestrator()
    nemo = get_nemo_rails()
    
    return {
        "status": "active",
        "orchestrator_type": type(orchestrator).__name__,
        "nemo_rails_available": nemo is not None,
        "input_guardrails": len(getattr(orchestrator, 'input_guardrails', [])),
        "output_guardrails": len(getattr(orchestrator, 'output_guardrails', [])),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/check")
async def check_guardrails(request: GuardrailCheckRequest):
    """
    Basic guardrail check.
    
    Returns:
        - allowed: Whether the content is allowed
        - results: Detailed results from each guardrail
        - modified_text: Redacted/modified text if applicable
    """
    try:
        orchestrator = get_orchestrator()
        
        if hasattr(orchestrator, 'check_input'):
            # Advanced guardrails
            if request.check_type == "input":
                allowed, results, modified = await orchestrator.check_input(
                    text=request.text,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    metadata=request.metadata
                )
            else:
                allowed, results, modified = await orchestrator.check_output(
                    input_text="",
                    output_text=request.text,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    metadata=request.metadata
                )
            
            return {
                "allowed": allowed,
                "results": [
                    {
                        "guardrail_type": r.guardrail_type.value if hasattr(r, 'guardrail_type') else str(r),
                        "triggered": r.triggered,
                        "action": r.action.value if hasattr(r.action, 'value') else str(r.action),
                        "risk_level": r.risk_level.value if hasattr(r, 'risk_level') and hasattr(r.risk_level, 'value') else "unknown",
                        "message": r.message,
                        "details": r.details
                    }
                    for r in results if hasattr(r, 'triggered')
                ],
                "modified_text": modified if modified != request.text else None,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Basic guardrails fallback
            result = orchestrator.check_input(request.text)
            return {
                "allowed": result.is_safe,
                "results": [{"type": v.get("type"), "message": v.get("message")} for v in result.violations],
                "modified_text": result.filtered_content,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Guardrails check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check/advanced")
async def advanced_check(request: AdvancedCheckRequest):
    """
    Advanced guardrail check with granular control.
    
    Allows selecting which checks to run:
    - input_validation
    - pii
    - jailbreak
    - toxicity
    - rate_limit
    - hallucination (requires context)
    """
    try:
        results = []
        modified_text = request.text
        allowed = True
        
        # Get individual guardrails
        from core.advanced_guardrails import (
            InputValidationGuardrail,
            PIIDetectionGuardrail,
            JailbreakDetectionGuardrail,
            ToxicityFilterGuardrail,
            RateLimitGuardrail,
            HallucinationCheckGuardrail,
            GuardrailContext
        )
        
        context = GuardrailContext(
            user_id=request.user_id,
            session_id=request.session_id,
            input_text=request.text,
            output_text=request.context
        )
        
        # Run selected checks
        if "input_validation" in request.checks:
            guard = InputValidationGuardrail()
            result = await guard.check(context)
            results.append({"check": "input_validation", "result": result.model_dump()})
            if result.triggered and result.action.value == "block":
                allowed = False
        
        if "pii" in request.checks:
            guard = PIIDetectionGuardrail(redact=request.redact_pii)
            result = await guard.check(context)
            results.append({"check": "pii", "result": result.model_dump()})
            if result.modified_content:
                modified_text = result.modified_content
        
        if "jailbreak" in request.checks:
            guard = JailbreakDetectionGuardrail()
            result = await guard.check(context)
            results.append({"check": "jailbreak", "result": result.model_dump()})
            if result.triggered:
                allowed = False
        
        if "toxicity" in request.checks:
            guard = ToxicityFilterGuardrail()
            result = await guard.check(context)
            results.append({"check": "toxicity", "result": result.model_dump()})
            if result.triggered and result.action.value == "block":
                allowed = False
        
        if "rate_limit" in request.checks and request.user_id:
            guard = RateLimitGuardrail()
            result = await guard.check(context)
            results.append({"check": "rate_limit", "result": result.model_dump()})
            if result.triggered:
                allowed = False
        
        if "hallucination" in request.checks and request.context:
            guard = HallucinationCheckGuardrail()
            context.output_text = request.text
            result = await guard.check(context)
            results.append({"check": "hallucination", "result": result.model_dump()})
        
        return {
            "allowed": allowed,
            "checks_run": request.checks,
            "results": results,
            "modified_text": modified_text if modified_text != request.text else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError as e:
        logger.warning(f"Advanced guardrails not available: {e}")
        raise HTTPException(status_code=503, detail="Advanced guardrails not available")
    except Exception as e:
        logger.error(f"Advanced check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pii/redact")
async def redact_pii(request: PIIRedactRequest):
    """
    Detect and redact PII from text.
    
    Detectable PII types:
    - email
    - phone
    - ssn
    - credit_card
    - ip_address
    """
    try:
        from core.advanced_guardrails import PIIDetectionGuardrail, PIIType, GuardrailContext
        
        # Map string types to PIIType enum
        pii_types = []
        for t in request.pii_types:
            try:
                pii_types.append(PIIType(t))
            except ValueError:
                pass
        
        guard = PIIDetectionGuardrail(redact=True, pii_types=pii_types)
        context = GuardrailContext(input_text=request.text)
        result = await guard.check(context)
        
        return {
            "original_text": request.text,
            "redacted_text": result.modified_content or request.text,
            "pii_found": result.triggered,
            "matches_count": len(result.details.get("matches", [])),
            "matches": result.details.get("matches", []),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"PII redaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jailbreak/detect")
async def detect_jailbreak(request: JailbreakCheckRequest):
    """
    Detect jailbreak/prompt injection attempts.
    
    Detects patterns like:
    - "ignore previous instructions"
    - "you are now DAN"
    - "bypass rules"
    - "[system]" injections
    """
    try:
        from core.advanced_guardrails import JailbreakDetectionGuardrail, GuardrailContext
        
        guard = JailbreakDetectionGuardrail()
        context = GuardrailContext(input_text=request.text)
        result = await guard.check(context)
        
        return {
            "is_jailbreak": result.triggered,
            "risk_level": result.risk_level.value if hasattr(result.risk_level, 'value') else str(result.risk_level),
            "patterns_detected": result.details.get("patterns_matched", []),
            "action": result.action.value if hasattr(result.action, 'value') else str(result.action),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Jailbreak detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/topic/add")
async def add_topic_restriction(request: TopicRestrictionRequest):
    """
    Add a topic restriction rule.
    
    Topics matching keywords will be handled according to the action.
    """
    try:
        from core.advanced_guardrails import TopicRestriction, GuardrailAction
        
        orchestrator = get_orchestrator()
        
        # Find or create topic restriction guardrail
        for guard in getattr(orchestrator, 'input_guardrails', []):
            if hasattr(guard, 'add_restriction'):
                restriction = TopicRestriction(
                    topic=request.topic,
                    keywords=request.keywords,
                    action=GuardrailAction(request.action),
                    message=request.message or f"Topic '{request.topic}' is restricted"
                )
                guard.add_restriction(restriction)
                
                return {
                    "success": True,
                    "topic": request.topic,
                    "keywords_count": len(request.keywords),
                    "action": request.action,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "success": False,
            "message": "Topic restriction guardrail not found"
        }
        
    except Exception as e:
        logger.error(f"Add topic restriction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rail/add")
async def add_custom_rail(request: CustomRailRequest):
    """
    Add a custom NeMo-style rail.
    
    Rails are evaluated as Python expressions against the context.
    """
    try:
        from core.advanced_guardrails import Rail, GuardrailAction
        
        nemo = get_nemo_rails()
        if nemo is None:
            raise HTTPException(status_code=503, detail="NeMo rails not available")
        
        rail = Rail(
            name=request.name,
            description=request.description,
            condition=request.condition,
            action=GuardrailAction(request.action),
            response=request.response
        )
        nemo.add_rail(rail)
        
        return {
            "success": True,
            "rail_name": request.name,
            "total_rails": len(nemo.rails),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Add custom rail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/safe")
async def safe_generate(request: SafeGenerateRequest):
    """
    Generate LLM response with guardrail protection.
    
    Input is checked, then generation happens, then output is checked.
    """
    try:
        from core.advanced_guardrails import safe_generate as sg
        
        orchestrator = get_orchestrator()
        
        # Mock LLM function - in production, connect to actual LLM
        async def mock_llm(prompt: str) -> str:
            from core.llm_client import generate_response
            return await generate_response(prompt)
        
        # Use safe_generate wrapper
        response, results = await sg(
            generate_fn=lambda p: "This is a safe response.",  # Placeholder
            input_text=request.prompt,
            guardrails=orchestrator if hasattr(orchestrator, 'check_input') else None,
            user_id=request.user_id
        )
        
        return {
            "response": response,
            "guardrail_results": [
                {
                    "type": r.guardrail_type.value if hasattr(r, 'guardrail_type') else "unknown",
                    "triggered": r.triggered,
                    "action": r.action.value if hasattr(r.action, 'value') else str(r.action)
                }
                for r in results
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Safe generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_guardrails_stats():
    """Get guardrails usage statistics"""
    try:
        orchestrator = get_orchestrator()
        
        stats = {
            "total_checks": 0,
            "blocked_count": 0,
            "pii_detections": 0,
            "jailbreak_attempts": 0,
            "rate_limit_hits": 0
        }
        
        # If orchestrator tracks stats, get them
        if hasattr(orchestrator, 'get_stats'):
            stats.update(orchestrator.get_stats())
        
        return {
            "stats": stats,
            "guardrails_active": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
