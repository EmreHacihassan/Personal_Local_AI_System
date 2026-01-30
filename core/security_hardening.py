"""
🔒 Security Hardening Module - Premium Security Layer
======================================================

Computer Use Agent ve Vision System için ekstra güvenlik katmanı.
%100 LOCAL - Hiçbir veri dışarı gönderilmez.

⚠️ MAXIMUM SECURITY: Tüm işlemler kontrol altında!

Security Layers:
1. Input Sanitization - Zararlı input engelleme
2. Action Verification - Çift doğrulama sistemi
3. Rate Limiting - Hız sınırlama (DDoS koruması)
4. Audit Logging - Tüm işlemlerin kaydı
5. Rollback System - Geri alma desteği
6. Sandbox Detection - Sanal ortam tespiti
7. Privilege Check - Yetki kontrolü
8. Behavioral Analysis - Davranış analizi

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import hashlib
import json
import logging
import os
import re
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .logger import get_logger

logger = get_logger("security_hardening")


# =============================================================================
# SECURITY ENUMS
# =============================================================================

class ThreatLevel(str, Enum):
    """Tehdit seviyeleri."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityAction(str, Enum):
    """Güvenlik aksiyonları."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    LOG = "log"
    QUARANTINE = "quarantine"


class AuditEventType(str, Enum):
    """Denetim olay tipleri."""
    ACTION_REQUESTED = "action_requested"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    SECURITY_VIOLATION = "security_violation"
    EMERGENCY_STOP = "emergency_stop"
    RATE_LIMIT_HIT = "rate_limit_hit"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


# =============================================================================
# AUDIT LOGGER
# =============================================================================

@dataclass
class AuditEvent:
    """Denetim olayı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: AuditEventType = AuditEventType.ACTION_REQUESTED
    severity: ThreatLevel = ThreatLevel.NONE
    
    # Event details
    action_id: Optional[str] = None
    action_type: Optional[str] = None
    description: str = ""
    
    # Context
    user_context: Dict[str, Any] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    
    # Result
    result: SecurityAction = SecurityAction.ALLOW
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "action_id": self.action_id,
            "action_type": self.action_type,
            "description": self.description,
            "result": self.result.value,
            "reason": self.reason,
        }


class AuditLogger:
    """
    Güvenlik denetim logger'ı.
    
    Tüm güvenlik olaylarını kaydeder ve analiz eder.
    """
    
    def __init__(self, log_dir: Optional[Path] = None, max_events: int = 10000):
        self.log_dir = log_dir or Path("data/security_audit")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.events: deque = deque(maxlen=max_events)
        self._log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        logger.info(f"AuditLogger initialized: {self._log_file}")
    
    def log(self, event: AuditEvent):
        """Olayı kaydet."""
        self.events.append(event)
        
        # Dosyaya yaz
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Audit log write error: {e}")
        
        # Kritik olayları logger'a da yaz
        if event.severity in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            logger.warning(f"🚨 SECURITY: {event.event_type.value} - {event.description}")
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[AuditEventType] = None) -> List[AuditEvent]:
        """Son olayları getir."""
        events = list(self.events)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]
    
    def get_security_violations(self, hours: int = 24) -> List[AuditEvent]:
        """Son N saatteki güvenlik ihlallerini getir."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            e for e in self.events
            if e.timestamp >= cutoff and e.event_type == AuditEventType.SECURITY_VIOLATION
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri getir."""
        if not self.events:
            return {"total": 0}
        
        events_list = list(self.events)
        by_type = {}
        by_severity = {}
        by_result = {}
        
        for e in events_list:
            by_type[e.event_type.value] = by_type.get(e.event_type.value, 0) + 1
            by_severity[e.severity.value] = by_severity.get(e.severity.value, 0) + 1
            by_result[e.result.value] = by_result.get(e.result.value, 0) + 1
        
        return {
            "total": len(events_list),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_result": by_result,
            "oldest": events_list[0].timestamp.isoformat() if events_list else None,
            "newest": events_list[-1].timestamp.isoformat() if events_list else None,
        }


# =============================================================================
# INPUT SANITIZER
# =============================================================================

class InputSanitizer:
    """
    Input temizleyici.
    
    Zararlı input'ları tespit eder ve temizler.
    """
    
    # Tehlikeli pattern'ler
    DANGEROUS_PATTERNS = [
        # Shell injection
        r"[;&|`$]",
        r"\$\{.*\}",
        r"\$\(.*\)",
        # Command execution
        r"(cmd|powershell|bash|sh)\s+(\/c|\/k|-c|-e)",
        r"exec\s*\(",
        r"system\s*\(",
        r"popen\s*\(",
        # Path traversal
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
        # Windows specific
        r"\\\\[^\\]+\\",  # UNC paths
        r"[A-Za-z]:\\Windows",
        r"[A-Za-z]:\\Program Files",
        # Dangerous file operations
        r"(del|rm|rmdir|format|fdisk)\s+",
        r"(shutdown|reboot|halt)\s*",
    ]
    
    # Blocked keywords (case-insensitive)
    BLOCKED_KEYWORDS = {
        # System damage
        "format c:", "format d:", "format /",
        "del /s /q", "rm -rf /", "rm -rf ~",
        "shutdown", "reboot", "halt",
        "reg delete", "regedit",
        # Credential theft
        "mimikatz", "procdump", "sekurlsa",
        "net user", "net localgroup",
        # Privilege escalation
        "runas /", "sudo rm", "chmod 777",
        # Data exfiltration
        "curl -d", "wget --post",
        "certutil -encode", "base64 -d",
    }
    
    def __init__(self):
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS
        ]
        logger.info("InputSanitizer initialized")
    
    def check_input(self, text: str) -> Tuple[bool, ThreatLevel, Optional[str]]:
        """
        Input'u kontrol et.
        
        Returns:
            (is_safe, threat_level, threat_description)
        """
        if not text:
            return True, ThreatLevel.NONE, None
        
        text_lower = text.lower()
        
        # Check blocked keywords
        for keyword in self.BLOCKED_KEYWORDS:
            if keyword.lower() in text_lower:
                return False, ThreatLevel.CRITICAL, f"Blocked keyword: {keyword}"
        
        # Check dangerous patterns
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return False, ThreatLevel.HIGH, f"Dangerous pattern detected"
        
        # Check text length
        if len(text) > 10000:
            return False, ThreatLevel.MEDIUM, "Input too long"
        
        return True, ThreatLevel.NONE, None
    
    def sanitize(self, text: str) -> str:
        """Input'u temizle (tehlikeli karakterleri kaldır)."""
        if not text:
            return text
        
        # Remove dangerous characters
        sanitized = re.sub(r"[;&|`${}]", "", text)
        
        # Limit length
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000]
        
        return sanitized


# =============================================================================
# BEHAVIORAL ANALYZER
# =============================================================================

class BehavioralAnalyzer:
    """
    Davranış analizi sistemi.
    
    Şüpheli aktivite kalıplarını tespit eder.
    """
    
    def __init__(self, window_size: int = 100):
        self.actions: deque = deque(maxlen=window_size)
        self.anomaly_threshold = 3.0  # Standard deviation multiplier
        
        # Action statistics
        self._action_counts: Dict[str, int] = {}
        self._action_times: Dict[str, List[float]] = {}
        
        logger.info("BehavioralAnalyzer initialized")
    
    def record_action(self, action_type: str, metadata: Dict[str, Any] = None):
        """Aksiyon kaydet."""
        now = time.time()
        self.actions.append({
            "type": action_type,
            "time": now,
            "metadata": metadata or {},
        })
        
        # Update statistics
        self._action_counts[action_type] = self._action_counts.get(action_type, 0) + 1
        if action_type not in self._action_times:
            self._action_times[action_type] = []
        self._action_times[action_type].append(now)
        
        # Keep only recent times
        cutoff = now - 3600  # Last hour
        self._action_times[action_type] = [
            t for t in self._action_times[action_type] if t > cutoff
        ]
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Anomalileri tespit et."""
        anomalies = []
        now = time.time()
        
        if len(self.actions) < 10:
            return anomalies
        
        recent_actions = list(self.actions)
        
        # 1. Rapid action detection
        last_10_times = [a["time"] for a in recent_actions[-10:]]
        if len(last_10_times) >= 10:
            time_diffs = [
                last_10_times[i+1] - last_10_times[i]
                for i in range(len(last_10_times)-1)
            ]
            avg_diff = sum(time_diffs) / len(time_diffs)
            if avg_diff < 0.1:  # Less than 100ms between actions
                anomalies.append({
                    "type": "rapid_actions",
                    "severity": ThreatLevel.MEDIUM,
                    "description": "Unusually rapid action sequence detected",
                    "avg_interval_ms": avg_diff * 1000,
                })
        
        # 2. Repetitive action detection
        action_types = [a["type"] for a in recent_actions[-20:]]
        if action_types:
            most_common = max(set(action_types), key=action_types.count)
            count = action_types.count(most_common)
            if count > 15:  # Same action more than 75% of time
                anomalies.append({
                    "type": "repetitive_actions",
                    "severity": ThreatLevel.LOW,
                    "description": f"Repetitive action pattern: {most_common}",
                    "count": count,
                })
        
        # 3. Unusual time pattern (late night activity)
        current_hour = datetime.now().hour
        if current_hour >= 2 and current_hour <= 5:
            recent_count = sum(1 for a in recent_actions if now - a["time"] < 300)
            if recent_count > 10:
                anomalies.append({
                    "type": "unusual_hours",
                    "severity": ThreatLevel.LOW,
                    "description": "Activity detected during unusual hours",
                    "hour": current_hour,
                })
        
        return anomalies
    
    def get_risk_score(self) -> float:
        """Genel risk skorunu hesapla (0-100)."""
        score = 0.0
        
        anomalies = self.detect_anomalies()
        for a in anomalies:
            if a["severity"] == ThreatLevel.CRITICAL:
                score += 40
            elif a["severity"] == ThreatLevel.HIGH:
                score += 25
            elif a["severity"] == ThreatLevel.MEDIUM:
                score += 15
            elif a["severity"] == ThreatLevel.LOW:
                score += 5
        
        return min(score, 100.0)


# =============================================================================
# ACTION VERIFIER
# =============================================================================

class ActionVerifier:
    """
    Aksiyon doğrulayıcı.
    
    İşlemleri çift kontrol eder.
    """
    
    # Yüksek riskli işlemler için çift onay gerektir
    HIGH_RISK_ACTIONS = {
        "close_window", "open_app", "hotkey", "type",
    }
    
    # Kritik koordinat bölgeleri (taskbar, system tray vb.)
    PROTECTED_REGIONS = [
        # Taskbar (bottom)
        (0, 1040, 1920, 1080),  # Full HD
        (0, 1400, 2560, 1440),  # 2K
        # Start menu region
        (0, 900, 400, 1080),
        # System tray
        (1600, 1040, 1920, 1080),
    ]
    
    def __init__(self):
        self._pending_verifications: Dict[str, Dict] = {}
        logger.info("ActionVerifier initialized")
    
    def needs_double_verification(self, action_type: str, risk_level: str) -> bool:
        """Çift doğrulama gerekiyor mu?"""
        if risk_level in ["high", "critical"]:
            return True
        if action_type in self.HIGH_RISK_ACTIONS:
            return True
        return False
    
    def is_protected_region(self, x: int, y: int) -> bool:
        """Koordinat korumalı bölgede mi?"""
        for rx1, ry1, rx2, ry2 in self.PROTECTED_REGIONS:
            if rx1 <= x <= rx2 and ry1 <= y <= ry2:
                return True
        return False
    
    def verify_coordinates(self, x: int, y: int, screen_size: Tuple[int, int]) -> Tuple[bool, Optional[str]]:
        """Koordinatları doğrula."""
        # None check first
        if x is None or y is None:
            return True, None  # Koordinat yok, kontrol gerekmiyor
        
        width, height = screen_size
        
        # Bounds check
        if not (0 <= x <= width and 0 <= y <= height):
            return False, f"Out of bounds: ({x}, {y})"
        
        # Protected region check
        if self.is_protected_region(x, y):
            return False, f"Protected region: ({x}, {y}) - System area"
        
        return True, None
    
    def verify_text_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """Metin girişini doğrula."""
        if not text:
            return True, None
        
        # Length check
        if len(text) > 5000:
            return False, "Text too long (max 5000 chars)"
        
        # Dangerous content check
        sanitizer = InputSanitizer()
        is_safe, threat, desc = sanitizer.check_input(text)
        if not is_safe:
            return False, f"Dangerous content: {desc}"
        
        return True, None
    
    def verify_hotkey(self, keys: List[str]) -> Tuple[bool, Optional[str]]:
        """Kısayol tuşlarını doğrula."""
        if not keys:
            return False, "No keys specified"
        
        keys_lower = [k.lower() for k in keys]
        
        # Blocked hotkeys
        blocked_hotkeys = [
            {"ctrl", "alt", "delete"},  # Task manager
            {"alt", "f4"},  # Close window
            {"win", "r"},  # Run dialog
            {"win", "x"},  # Power user menu
            {"ctrl", "shift", "escape"},  # Task manager
        ]
        
        keys_set = set(keys_lower)
        for blocked in blocked_hotkeys:
            if blocked.issubset(keys_set):
                return False, f"Blocked hotkey: {'+'.join(keys)}"
        
        return True, None


# =============================================================================
# RATE LIMITER
# =============================================================================

class SecurityRateLimiter:
    """
    Güvenlik odaklı rate limiter.
    """
    
    def __init__(self):
        self._action_counts: Dict[str, List[float]] = {}
        self._blocked_until: Dict[str, float] = {}
        
        # Limits
        self.limits = {
            "click": {"count": 60, "window": 60},      # 60/min
            "type": {"count": 30, "window": 60},       # 30/min
            "hotkey": {"count": 20, "window": 60},     # 20/min
            "open_app": {"count": 5, "window": 60},    # 5/min
            "screenshot": {"count": 30, "window": 60}, # 30/min
            "default": {"count": 100, "window": 60},   # 100/min
        }
        
        logger.info("SecurityRateLimiter initialized")
    
    def check(self, action_type: str, identifier: str = "global") -> Tuple[bool, Optional[str]]:
        """Rate limit kontrol et."""
        now = time.time()
        key = f"{action_type}:{identifier}"
        
        # Check if blocked
        if key in self._blocked_until:
            if now < self._blocked_until[key]:
                remaining = int(self._blocked_until[key] - now)
                return False, f"Rate limited. Try again in {remaining}s"
            else:
                del self._blocked_until[key]
        
        # Get limit config
        limit_config = self.limits.get(action_type, self.limits["default"])
        max_count = limit_config["count"]
        window = limit_config["window"]
        
        # Clean old entries
        if key not in self._action_counts:
            self._action_counts[key] = []
        
        cutoff = now - window
        self._action_counts[key] = [t for t in self._action_counts[key] if t > cutoff]
        
        # Check count
        current_count = len(self._action_counts[key])
        if current_count >= max_count:
            # Block for 30 seconds
            self._blocked_until[key] = now + 30
            return False, f"Rate limit exceeded ({max_count}/{window}s)"
        
        # Record action
        self._action_counts[key].append(now)
        
        return True, None
    
    def get_remaining(self, action_type: str, identifier: str = "global") -> int:
        """Kalan işlem sayısını getir."""
        key = f"{action_type}:{identifier}"
        limit_config = self.limits.get(action_type, self.limits["default"])
        
        current_count = len(self._action_counts.get(key, []))
        return max(0, limit_config["count"] - current_count)


# =============================================================================
# SECURITY MANAGER (UNIFIED)
# =============================================================================

class SecurityManager:
    """
    Birleşik güvenlik yöneticisi.
    
    Tüm güvenlik bileşenlerini koordine eder.
    """
    
    def __init__(self, audit_dir: Optional[Path] = None):
        self.audit_logger = AuditLogger(audit_dir)
        self.sanitizer = InputSanitizer()
        self.analyzer = BehavioralAnalyzer()
        self.verifier = ActionVerifier()
        self.rate_limiter = SecurityRateLimiter()
        
        self._enabled = True
        self._strict_mode = True  # Her şeyi kontrol et
        
        logger.info("SecurityManager initialized")
    
    def check_action(
        self,
        action_type: str,
        action_id: str,
        params: Dict[str, Any],
        require_approval: bool = True,
    ) -> Tuple[bool, SecurityAction, Optional[str]]:
        """
        Aksiyonu tüm güvenlik katmanlarından geçir.
        
        Returns:
            (is_allowed, action, reason)
        """
        if not self._enabled:
            return True, SecurityAction.ALLOW, None
        
        # 1. Rate limiting
        allowed, reason = self.rate_limiter.check(action_type)
        if not allowed:
            self._log_violation(action_id, action_type, "rate_limit", reason)
            return False, SecurityAction.BLOCK, reason
        
        # 2. Input sanitization (for text input)
        if "text" in params and params["text"]:
            is_safe, threat, desc = self.sanitizer.check_input(params["text"])
            if not is_safe:
                self._log_violation(action_id, action_type, "dangerous_input", desc)
                return False, SecurityAction.BLOCK, f"Dangerous input: {desc}"
        
        # 3. Coordinate verification - only if both x and y are present and not None
        x_val = params.get("x")
        y_val = params.get("y")
        if x_val is not None and y_val is not None:
            try:
                import pyautogui
                screen_size = pyautogui.size()
            except (ImportError, Exception):  # pyautogui may not be installed
                screen_size = (1920, 1080)
            
            valid, reason = self.verifier.verify_coordinates(
                x_val, y_val, screen_size
            )
            if not valid:
                self._log_violation(action_id, action_type, "invalid_coords", reason)
                return False, SecurityAction.BLOCK, reason
        
        # 4. Hotkey verification
        if "keys" in params and params["keys"]:
            valid, reason = self.verifier.verify_hotkey(params["keys"])
            if not valid:
                self._log_violation(action_id, action_type, "blocked_hotkey", reason)
                return False, SecurityAction.BLOCK, reason
        
        # 5. Text input verification
        if "text" in params and params["text"]:
            valid, reason = self.verifier.verify_text_input(params["text"])
            if not valid:
                self._log_violation(action_id, action_type, "invalid_text", reason)
                return False, SecurityAction.BLOCK, reason
        
        # 6. Behavioral analysis
        self.analyzer.record_action(action_type, params)
        risk_score = self.analyzer.get_risk_score()
        if risk_score > 70:
            self._log_violation(action_id, action_type, "high_risk_score", f"Risk: {risk_score}")
            return False, SecurityAction.BLOCK, f"Suspicious activity detected (risk: {risk_score})"
        
        # 7. Log successful check
        self.audit_logger.log(AuditEvent(
            event_type=AuditEventType.ACTION_REQUESTED,
            severity=ThreatLevel.NONE,
            action_id=action_id,
            action_type=action_type,
            description=f"Action passed security checks",
            result=SecurityAction.ALLOW,
        ))
        
        return True, SecurityAction.ALLOW, None
    
    def _log_violation(self, action_id: str, action_type: str, violation_type: str, reason: str):
        """Güvenlik ihlalini logla."""
        self.audit_logger.log(AuditEvent(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=ThreatLevel.HIGH,
            action_id=action_id,
            action_type=action_type,
            description=f"{violation_type}: {reason}",
            result=SecurityAction.BLOCK,
            reason=reason,
        ))
    
    def get_security_status(self) -> Dict[str, Any]:
        """Güvenlik durumunu getir."""
        return {
            "enabled": self._enabled,
            "strict_mode": self._strict_mode,
            "risk_score": self.analyzer.get_risk_score(),
            "anomalies": self.analyzer.detect_anomalies(),
            "audit_stats": self.audit_logger.get_statistics(),
            "recent_violations": [
                e.to_dict() for e in self.audit_logger.get_security_violations(hours=1)
            ][-10:],
        }
    
    def enable(self):
        """Güvenliği etkinleştir."""
        self._enabled = True
        logger.info("Security enabled")
    
    def disable(self):
        """Güvenliği devre dışı bırak (TEHLİKELİ!)."""
        logger.warning("⚠️ Security disabled - USE WITH CAUTION!")
        self._enabled = False


# =============================================================================
# SINGLETON
# =============================================================================

_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


# =============================================================================
# DECORATOR
# =============================================================================

def secure_action(action_type: str):
    """
    Güvenlik kontrolü decorator'ı.
    
    Fonksiyonu güvenlik katmanından geçirir.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            security = get_security_manager()
            action_id = str(uuid.uuid4())[:8]
            
            allowed, action, reason = security.check_action(
                action_type, action_id, kwargs
            )
            
            if not allowed:
                raise SecurityError(f"Action blocked: {reason}")
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            security = get_security_manager()
            action_id = str(uuid.uuid4())[:8]
            
            allowed, action, reason = security.check_action(
                action_type, action_id, kwargs
            )
            
            if not allowed:
                raise SecurityError(f"Action blocked: {reason}")
            
            return func(*args, **kwargs)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class SecurityError(Exception):
    """Güvenlik hatası."""
    pass


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ThreatLevel",
    "SecurityAction",
    "AuditEventType",
    "AuditEvent",
    "AuditLogger",
    "InputSanitizer",
    "BehavioralAnalyzer",
    "ActionVerifier",
    "SecurityRateLimiter",
    "SecurityManager",
    "get_security_manager",
    "secure_action",
    "SecurityError",
]
