"""
Enterprise AI Assistant - Guardrails Module
Güvenlik ve içerik kontrolü

Input/Output validation, content filtering, safety checks.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class GuardLevel(str, Enum):
    """Güvenlik seviyesi."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


class ViolationType(str, Enum):
    """İhlal türleri."""
    PROFANITY = "profanity"
    PII = "pii"  # Personal Identifiable Information
    INJECTION = "injection"
    HARMFUL = "harmful"
    OFF_TOPIC = "off_topic"
    TOO_LONG = "too_long"
    SPAM = "spam"
    HALLUCINATION = "hallucination"


@dataclass
class GuardResult:
    """Güvenlik kontrolü sonucu."""
    is_safe: bool
    violations: List[Dict[str, Any]] = field(default_factory=list)
    filtered_content: Optional[str] = None
    confidence: float = 1.0
    checked_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "is_safe": self.is_safe,
            "violations": self.violations,
            "filtered_content": self.filtered_content,
            "confidence": self.confidence,
            "checked_at": self.checked_at.isoformat(),
        }


class InputGuard:
    """
    Giriş güvenliği kontrolü.
    
    Prompt injection, PII, kötü amaçlı içerik tespiti.
    """
    
    # Prompt injection patterns
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)?\s*instructions",
        r"disregard\s+(all\s+)?(previous|above)?",
        r"forget\s+(everything|all|previous)",
        r"you\s+are\s+now\s+a",
        r"act\s+as\s+if\s+you",
        r"pretend\s+(you|to)\s+(are|be)",
        r"system\s*:\s*",
        r"\[system\]",
        r"<\|im_start\|>",
        r"<\|system\|>",
        r"###\s*instruction",
    ]
    
    # PII patterns (Turkish & English)
    PII_PATTERNS = {
        "tc_kimlik": r"\b[1-9]\d{10}\b",  # TC Kimlik No
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone_tr": r"\b0[5][0-9]{9}\b",  # Türk cep telefonu
        "phone_intl": r"\+\d{1,3}\s?\d{6,14}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "iban_tr": r"\bTR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b",
    }
    
    # Profanity patterns (basic - expand as needed)
    PROFANITY_PATTERNS = [
        # Add domain-specific blocked terms
    ]
    
    def __init__(self, level: GuardLevel = GuardLevel.MEDIUM):
        """Input guard başlat."""
        self.level = level
        self._compiled_injection = [
            re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS
        ]
        self._compiled_pii = {
            k: re.compile(v, re.IGNORECASE) 
            for k, v in self.PII_PATTERNS.items()
        }
    
    def check(self, text: str) -> GuardResult:
        """
        Girişi kontrol et.
        
        Args:
            text: Kontrol edilecek metin
            
        Returns:
            Güvenlik sonucu
        """
        violations = []
        
        # Length check
        if len(text) > 10000:
            violations.append({
                "type": ViolationType.TOO_LONG.value,
                "message": "Metin çok uzun",
                "severity": "medium",
            })
        
        # Injection check
        injection_result = self._check_injection(text)
        if injection_result:
            violations.append(injection_result)
        
        # PII check (medium+ level)
        if self.level in [GuardLevel.MEDIUM, GuardLevel.HIGH, GuardLevel.STRICT]:
            pii_results = self._check_pii(text)
            violations.extend(pii_results)
        
        # Spam check
        spam_result = self._check_spam(text)
        if spam_result:
            violations.append(spam_result)
        
        is_safe = len(violations) == 0
        
        # Filter content if needed
        filtered = text
        if not is_safe and self.level in [GuardLevel.HIGH, GuardLevel.STRICT]:
            filtered = self._filter_content(text, violations)
        
        return GuardResult(
            is_safe=is_safe,
            violations=violations,
            filtered_content=filtered if filtered != text else None,
        )
    
    def _check_injection(self, text: str) -> Optional[Dict]:
        """Prompt injection kontrolü."""
        for pattern in self._compiled_injection:
            if pattern.search(text):
                return {
                    "type": ViolationType.INJECTION.value,
                    "message": "Potansiyel prompt injection tespit edildi",
                    "severity": "high",
                }
        return None
    
    def _check_pii(self, text: str) -> List[Dict]:
        """PII kontrolü."""
        violations = []
        
        for pii_type, pattern in self._compiled_pii.items():
            matches = pattern.findall(text)
            if matches:
                violations.append({
                    "type": ViolationType.PII.value,
                    "subtype": pii_type,
                    "message": f"{pii_type} tespit edildi",
                    "count": len(matches),
                    "severity": "high",
                })
        
        return violations
    
    def _check_spam(self, text: str) -> Optional[Dict]:
        """Spam kontrolü."""
        # Check for excessive repetition
        words = text.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                return {
                    "type": ViolationType.SPAM.value,
                    "message": "Aşırı tekrar tespit edildi",
                    "severity": "medium",
                }
        
        # Check for excessive caps
        if len(text) > 20:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.7:
                return {
                    "type": ViolationType.SPAM.value,
                    "message": "Aşırı büyük harf kullanımı",
                    "severity": "low",
                }
        
        return None
    
    def _filter_content(self, text: str, violations: List[Dict]) -> str:
        """İçeriği filtrele."""
        filtered = text
        
        for v in violations:
            if v["type"] == ViolationType.PII.value:
                # Mask PII
                pii_type = v.get("subtype")
                if pii_type and pii_type in self._compiled_pii:
                    pattern = self._compiled_pii[pii_type]
                    filtered = pattern.sub("[MASKED]", filtered)
        
        return filtered


class OutputGuard:
    """
    Çıkış güvenliği kontrolü.
    
    Hallucination detection, content safety, format validation.
    """
    
    def __init__(self, level: GuardLevel = GuardLevel.MEDIUM):
        """Output guard başlat."""
        self.level = level
    
    def check(
        self,
        output: str,
        context: str = None,
        expected_format: str = None,
    ) -> GuardResult:
        """
        Çıkışı kontrol et.
        
        Args:
            output: LLM çıktısı
            context: Bağlam (RAG kaynakları)
            expected_format: Beklenen format
            
        Returns:
            Güvenlik sonucu
        """
        violations = []
        
        # Length check
        if len(output) < 10:
            violations.append({
                "type": "too_short",
                "message": "Yanıt çok kısa",
                "severity": "low",
            })
        
        # Hallucination check (if context provided)
        if context and self.level in [GuardLevel.HIGH, GuardLevel.STRICT]:
            hallucination = self._check_hallucination(output, context)
            if hallucination:
                violations.append(hallucination)
        
        # Format check
        if expected_format:
            format_result = self._check_format(output, expected_format)
            if format_result:
                violations.append(format_result)
        
        # Refusal check
        refusal = self._check_refusal(output)
        if refusal:
            violations.append(refusal)
        
        is_safe = len([v for v in violations if v.get("severity") == "high"]) == 0
        
        return GuardResult(
            is_safe=is_safe,
            violations=violations,
        )
    
    def _check_hallucination(self, output: str, context: str) -> Optional[Dict]:
        """
        Basit hallucination kontrolü.
        
        Çıktıdaki bilgilerin bağlamda olup olmadığını kontrol eder.
        """
        # Extract key claims from output (simplified)
        # In production, use NER/claim extraction
        
        # Check if output contains info not in context
        output_words = set(output.lower().split())
        context_words = set(context.lower().split())
        
        # Find potential hallucinations (words in output but not in context)
        new_words = output_words - context_words
        
        # Filter common words
        common_words = {"bir", "ve", "bu", "için", "ile", "de", "da", "the", "a", "an", "is", "are"}
        new_words = new_words - common_words
        
        # If too many new words, might be hallucination
        if len(new_words) > len(output_words) * 0.5:
            return {
                "type": ViolationType.HALLUCINATION.value,
                "message": "Potansiyel hallucination - çıktı bağlamda olmayan bilgiler içeriyor",
                "severity": "medium",
                "confidence": 0.6,
            }
        
        return None
    
    def _check_format(self, output: str, expected: str) -> Optional[Dict]:
        """Format kontrolü."""
        if expected == "json":
            try:
                import json
                json.loads(output)
            except:
                return {
                    "type": "format_error",
                    "message": "Geçersiz JSON formatı",
                    "severity": "medium",
                }
        
        elif expected == "list":
            if not any(c in output for c in ["-", "•", "1.", "*"]):
                return {
                    "type": "format_error",
                    "message": "Liste formatı bekleniyor",
                    "severity": "low",
                }
        
        return None
    
    def _check_refusal(self, output: str) -> Optional[Dict]:
        """Model refusal kontrolü."""
        refusal_phrases = [
            "yapamam",
            "yardımcı olamam",
            "i cannot",
            "i can't help",
            "as an ai",
            "bir yapay zeka olarak",
        ]
        
        output_lower = output.lower()
        for phrase in refusal_phrases:
            if phrase in output_lower:
                return {
                    "type": "refusal",
                    "message": "Model isteği reddetti",
                    "severity": "low",
                }
        
        return None


class Guardrails:
    """Ana güvenlik sistemi."""
    
    def __init__(self, level: GuardLevel = GuardLevel.MEDIUM):
        """Guardrails başlat."""
        self.level = level
        self.input_guard = InputGuard(level)
        self.output_guard = OutputGuard(level)
        self._custom_validators: List[Callable] = []
    
    def add_validator(self, validator: Callable[[str], Optional[Dict]]):
        """Özel validator ekle."""
        self._custom_validators.append(validator)
    
    def check_input(self, text: str) -> GuardResult:
        """Girişi kontrol et."""
        result = self.input_guard.check(text)
        
        # Run custom validators
        for validator in self._custom_validators:
            custom_result = validator(text)
            if custom_result:
                result.violations.append(custom_result)
                result.is_safe = False
        
        return result
    
    def check_output(
        self,
        output: str,
        context: str = None,
        expected_format: str = None,
    ) -> GuardResult:
        """Çıkışı kontrol et."""
        return self.output_guard.check(output, context, expected_format)
    
    def safe_generate(
        self,
        llm_func: Callable,
        prompt: str,
        context: str = None,
        **kwargs,
    ) -> Tuple[str, GuardResult, GuardResult]:
        """
        Güvenli LLM çağrısı.
        
        Args:
            llm_func: LLM generate fonksiyonu
            prompt: Prompt
            context: RAG bağlamı
            **kwargs: LLM parametreleri
            
        Returns:
            (output, input_result, output_result)
        """
        # Check input
        input_result = self.check_input(prompt)
        
        if not input_result.is_safe and self.level == GuardLevel.STRICT:
            return (
                "Güvenlik ihlali: Giriş reddedildi.",
                input_result,
                GuardResult(is_safe=False),
            )
        
        # Use filtered content if available
        safe_prompt = input_result.filtered_content or prompt
        
        # Generate
        output = llm_func(safe_prompt, **kwargs)
        
        # Check output
        output_result = self.check_output(output, context)
        
        return output, input_result, output_result


# Singleton instance
guardrails = Guardrails(GuardLevel.MEDIUM)
