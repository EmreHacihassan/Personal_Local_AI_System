"""
🖥️🤖 Computer Use Agent - Premium Desktop Automation
======================================================

AI kontrollü masaüstü otomasyon sistemi.
%100 LOCAL çalışır - hiçbir veri dışarı gönderilmez.

⚠️ GÜVENLİK: Her işlemde kullanıcı onayı istenir!

Features:
- 🖱️ Mouse kontrolü (tıklama, sürükleme, scroll)
- ⌨️ Klavye kontrolü (yazma, kısayollar)
- 👁️ Ekran analizi (LLaVA ile görüntü tanıma)
- 🎯 UI element tespiti
- 🔒 Çok katmanlı güvenlik
- ✅ Her işlemde onay sistemi
- 🚫 Tehlikeli işlem engelleme
- 📝 Tam action logging
- ⏹️ Emergency stop (Escape tuşu)

Author: Enterprise AI Assistant
Version: 1.0.0
"""

import asyncio
import base64
import hashlib
import io
import json
import logging
import os
import re
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Optional, 
    Tuple, Union, Set, AsyncGenerator
)
from concurrent.futures import ThreadPoolExecutor

# Image processing
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Screen capture
try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

# Desktop automation
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to abort
    pyautogui.PAUSE = 0.1  # Small pause between actions
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

# Keyboard listener for emergency stop
try:
    from pynput import keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

from .config import settings
from .logger import get_logger
from .realtime_vision import (
    RealtimeVisionSystem,
    VisionConfig,
    VisionMode,
    get_realtime_vision,
    ScreenAnalysis,
    FrameData,
)

# Import security hardening
try:
    from .security_hardening import (
        SecurityManager,
        get_security_manager,
        SecurityAction,
        ThreatLevel,
        AuditEventType,
    )
    HAS_SECURITY = True
except ImportError:
    HAS_SECURITY = False

logger = get_logger("computer_use_agent")


# =============================================================================
# CONFIGURATION
# =============================================================================

class ActionType(str, Enum):
    """Eylem tipleri."""
    # Mouse actions
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    DRAG = "drag"
    SCROLL = "scroll"
    MOVE = "move"
    
    # Keyboard actions
    TYPE = "type"
    HOTKEY = "hotkey"
    PRESS = "press"
    
    # Window actions
    FOCUS_WINDOW = "focus_window"
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"
    CLOSE_WINDOW = "close_window"
    
    # System actions
    OPEN_APP = "open_app"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    
    # Meta actions
    SEQUENCE = "sequence"
    CONDITIONAL = "conditional"


class RiskLevel(str, Enum):
    """Risk seviyeleri."""
    SAFE = "safe"           # Güvenli (scroll, move)
    LOW = "low"             # Düşük risk (click, type)
    MEDIUM = "medium"       # Orta risk (hotkey, open_app)
    HIGH = "high"           # Yüksek risk (close, delete)
    CRITICAL = "critical"   # Kritik (sistem komutları)


class ApprovalStatus(str, Enum):
    """Onay durumları."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AgentMode(str, Enum):
    """Agent çalışma modları."""
    PREVIEW = "preview"       # Sadece göster, uygulama
    CONFIRM_ALL = "confirm_all"  # Her işlemde onay
    CONFIRM_RISKY = "confirm_risky"  # Sadece riskli işlemlerde onay
    AUTONOMOUS = "autonomous"  # Onaysız (tehlikeli!)


@dataclass
class ComputerUseConfig:
    """Computer Use konfigürasyonu."""
    # Agent mode
    mode: AgentMode = AgentMode.CONFIRM_ALL
    
    # Safety settings
    emergency_stop_key: str = "escape"
    max_actions_per_minute: int = 30
    action_timeout: float = 30.0
    approval_timeout: float = 60.0
    
    # Whitelist/Blacklist
    allowed_apps: List[str] = field(default_factory=lambda: [
        "notepad", "explorer", "chrome", "firefox", "edge",
        "code", "word", "excel", "calc", "mspaint"
    ])
    blocked_commands: List[str] = field(default_factory=lambda: [
        "format", "del /", "rm -rf", "shutdown", "reboot",
        "reg delete", "taskkill /im", "net user"
    ])
    blocked_paths: List[str] = field(default_factory=lambda: [
        "C:\\Windows\\System32",
        "C:\\Program Files",
    ])
    
    # Mouse settings
    mouse_speed: float = 0.5  # 0.1 (fast) - 1.0 (slow)
    click_delay: float = 0.1
    
    # Vision settings
    vision_model: str = "llava"
    
    # Logging
    log_all_actions: bool = True
    screenshot_on_action: bool = True
    
    def is_app_allowed(self, app_name: str) -> bool:
        """Uygulama izinli mi?"""
        app_lower = app_name.lower()
        return any(allowed.lower() in app_lower for allowed in self.allowed_apps)
    
    def is_command_blocked(self, command: str) -> bool:
        """Komut engelli mi?"""
        cmd_lower = command.lower()
        return any(blocked.lower() in cmd_lower for blocked in self.blocked_commands)
    
    def is_path_blocked(self, path: str) -> bool:
        """Yol engelli mi?"""
        path_lower = path.lower()
        return any(blocked.lower() in path_lower for blocked in self.blocked_paths)


@dataclass
class Action:
    """Tek bir eylem."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: ActionType = ActionType.CLICK
    
    # Parameters
    x: Optional[int] = None
    y: Optional[int] = None
    text: Optional[str] = None
    keys: Optional[List[str]] = None
    app_name: Optional[str] = None
    duration: Optional[float] = None
    
    # Drag specific
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    
    # Scroll specific
    scroll_amount: int = 0
    
    # Description
    description: str = ""
    reasoning: str = ""
    
    # Risk assessment
    risk_level: RiskLevel = RiskLevel.LOW
    
    # Status
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    executed: bool = False
    success: bool = False
    error: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "x": self.x,
            "y": self.y,
            "text": self.text,
            "keys": self.keys,
            "app_name": self.app_name,
            "description": self.description,
            "reasoning": self.reasoning,
            "risk_level": self.risk_level.value,
            "approval_status": self.approval_status.value,
            "executed": self.executed,
            "success": self.success,
            "error": self.error,
        }
    
    def get_human_readable(self) -> str:
        """İnsan okunabilir açıklama."""
        if self.action_type == ActionType.CLICK:
            return f"🖱️ Tıkla: ({self.x}, {self.y}) - {self.description}"
        elif self.action_type == ActionType.DOUBLE_CLICK:
            return f"🖱️🖱️ Çift tıkla: ({self.x}, {self.y}) - {self.description}"
        elif self.action_type == ActionType.RIGHT_CLICK:
            return f"🖱️ Sağ tıkla: ({self.x}, {self.y}) - {self.description}"
        elif self.action_type == ActionType.TYPE:
            # Mask sensitive text
            display_text = self.text[:20] + "..." if len(self.text or "") > 20 else self.text
            return f"⌨️ Yaz: '{display_text}'"
        elif self.action_type == ActionType.HOTKEY:
            return f"⌨️ Kısayol: {'+'.join(self.keys or [])}"
        elif self.action_type == ActionType.PRESS:
            return f"⌨️ Tuş: {self.keys[0] if self.keys else ''}"
        elif self.action_type == ActionType.SCROLL:
            direction = "yukarı" if self.scroll_amount > 0 else "aşağı"
            return f"🖱️ Scroll {direction}: {abs(self.scroll_amount)}"
        elif self.action_type == ActionType.OPEN_APP:
            return f"📂 Aç: {self.app_name}"
        elif self.action_type == ActionType.WAIT:
            return f"⏳ Bekle: {self.duration}s"
        elif self.action_type == ActionType.DRAG:
            return f"🖱️ Sürükle: ({self.x}, {self.y}) → ({self.end_x}, {self.end_y})"
        else:
            return f"{self.action_type.value}: {self.description}"


@dataclass
class ActionPlan:
    """Eylem planı."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task: str = ""
    actions: List[Action] = field(default_factory=list)
    
    # Status
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    current_step: int = 0
    total_steps: int = 0
    
    success: bool = False
    cancelled: bool = False
    error: Optional[str] = None
    
    # Screenshots
    before_screenshot: Optional[str] = None
    after_screenshot: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "actions": [a.to_dict() for a in self.actions],
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "success": self.success,
            "cancelled": self.cancelled,
            "error": self.error,
        }


@dataclass
class ApprovalRequest:
    """Onay isteği."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    action: Action = None
    plan_id: str = ""
    
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(seconds=60))
    
    status: ApprovalStatus = ApprovalStatus.PENDING
    responded_at: Optional[datetime] = None
    response_reason: Optional[str] = None
    
    # Preview
    screenshot_base64: Optional[str] = None
    highlighted_region: Optional[Tuple[int, int, int, int]] = None
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action.to_dict() if self.action else None,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired(),
            "screenshot": self.screenshot_base64 is not None,
            "highlighted_region": self.highlighted_region,
        }


# =============================================================================
# SAFETY GUARD
# =============================================================================

class SafetyGuard:
    """
    Güvenlik koruma sistemi.
    
    Tüm işlemleri kontrol eder ve tehlikeli olanları engeller.
    """
    
    def __init__(self, config: ComputerUseConfig):
        self.config = config
        self._action_history: deque = deque(maxlen=100)
        self._action_count_per_minute: int = 0
        self._last_minute_reset: datetime = datetime.now()
        self._emergency_stop: bool = False
        self._stop_listener = None
        
        # Start emergency stop listener
        self._start_emergency_listener()
        
        logger.info("SafetyGuard initialized")
    
    def _start_emergency_listener(self):
        """Emergency stop dinleyicisi başlat."""
        if not HAS_PYNPUT:
            logger.warning("pynput not available, emergency stop disabled")
            return
        
        def on_press(key):
            try:
                if key == keyboard.Key.escape:
                    self._emergency_stop = True
                    logger.warning("🛑 EMERGENCY STOP TRIGGERED!")
            except Exception:
                pass
        
        self._stop_listener = keyboard.Listener(on_press=on_press)
        self._stop_listener.start()
    
    def check_emergency_stop(self) -> bool:
        """Emergency stop kontrol et."""
        return self._emergency_stop
    
    def reset_emergency_stop(self):
        """Emergency stop'u sıfırla."""
        self._emergency_stop = False
    
    def assess_risk(self, action: Action) -> RiskLevel:
        """İşlemin risk seviyesini değerlendir."""
        action_type = action.action_type
        
        # Safe actions
        if action_type in [ActionType.MOVE, ActionType.SCREENSHOT, ActionType.WAIT]:
            return RiskLevel.SAFE
        
        # Low risk
        if action_type in [ActionType.SCROLL]:
            return RiskLevel.LOW
        
        # Medium risk
        if action_type in [ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.TYPE]:
            # Check for dangerous text
            if action.text and self.config.is_command_blocked(action.text):
                return RiskLevel.CRITICAL
            return RiskLevel.LOW
        
        # High risk  
        if action_type in [ActionType.HOTKEY]:
            # Check for dangerous shortcuts
            keys = action.keys or []
            keys_lower = [k.lower() for k in keys]
            
            # Alt+F4, Ctrl+Alt+Del etc.
            if "alt" in keys_lower and "f4" in keys_lower:
                return RiskLevel.HIGH
            if set(["ctrl", "alt", "delete"]).issubset(set(keys_lower)):
                return RiskLevel.CRITICAL
            
            return RiskLevel.MEDIUM
        
        # Very high risk
        if action_type in [ActionType.CLOSE_WINDOW, ActionType.OPEN_APP]:
            # Check app whitelist
            if action.app_name and not self.config.is_app_allowed(action.app_name):
                return RiskLevel.HIGH
            return RiskLevel.MEDIUM
        
        return RiskLevel.MEDIUM
    
    def validate_action(self, action: Action) -> Tuple[bool, Optional[str]]:
        """
        İşlemi doğrula.
        
        Returns:
            (is_valid, error_message)
        """
        # Emergency stop check
        if self._emergency_stop:
            return False, "🛑 Emergency stop aktif! İşlem engellendi."
        
        # Rate limiting
        now = datetime.now()
        if (now - self._last_minute_reset).seconds >= 60:
            self._action_count_per_minute = 0
            self._last_minute_reset = now
        
        if self._action_count_per_minute >= self.config.max_actions_per_minute:
            return False, f"⚠️ Rate limit aşıldı! Dakikada max {self.config.max_actions_per_minute} işlem."
        
        # ===== SECURITY HARDENING LAYER =====
        if HAS_SECURITY:
            security = get_security_manager()
            params = {
                "x": action.x,
                "y": action.y,
                "text": action.text,
                "keys": action.keys,
                "app_name": action.app_name,
            }
            
            allowed, sec_action, reason = security.check_action(
                action.action_type.value,
                action.id,
                params,
            )
            
            if not allowed:
                return False, f"🔒 Güvenlik: {reason}"
        # ===== END SECURITY HARDENING =====
        
        # Risk assessment
        risk = self.assess_risk(action)
        action.risk_level = risk
        
        if risk == RiskLevel.CRITICAL:
            return False, "🚫 KRİTİK: Bu işlem çok tehlikeli ve engellendi!"
        
        # Blocked command check
        if action.text and self.config.is_command_blocked(action.text):
            return False, f"🚫 Engellenen komut tespit edildi: {action.text[:50]}"
        
        # Blocked path check
        if action.text and self.config.is_path_blocked(action.text):
            return False, f"🚫 Engellenen yol tespit edildi!"
        
        # App whitelist check
        if action.action_type == ActionType.OPEN_APP:
            if action.app_name and not self.config.is_app_allowed(action.app_name):
                return False, f"🚫 Uygulama izin listesinde değil: {action.app_name}"
        
        # Coordinates validation
        if action.x is not None and action.y is not None:
            screen_width, screen_height = pyautogui.size() if HAS_PYAUTOGUI else (1920, 1080)
            if not (0 <= action.x <= screen_width and 0 <= action.y <= screen_height):
                return False, f"🚫 Geçersiz koordinatlar: ({action.x}, {action.y})"
        
        return True, None
    
    def requires_approval(self, action: Action) -> bool:
        """Bu işlem onay gerektiriyor mu?"""
        mode = self.config.mode
        
        if mode == AgentMode.AUTONOMOUS:
            return False
        
        if mode == AgentMode.CONFIRM_ALL:
            return True
        
        if mode == AgentMode.CONFIRM_RISKY:
            return action.risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        
        if mode == AgentMode.PREVIEW:
            return True  # Preview modunda hiçbir şey yapılmaz ama gösterilir
        
        return True
    
    def log_action(self, action: Action):
        """İşlemi logla."""
        self._action_history.append({
            "action": action.to_dict(),
            "timestamp": datetime.now().isoformat(),
        })
        self._action_count_per_minute += 1
        
        if self.config.log_all_actions:
            logger.info(f"Action: {action.get_human_readable()}")
    
    def get_action_history(self, limit: int = 50) -> List[Dict]:
        """İşlem geçmişi."""
        return list(self._action_history)[-limit:]
    
    def shutdown(self):
        """Kapat."""
        if self._stop_listener:
            self._stop_listener.stop()


# =============================================================================
# ACTION EXECUTOR
# =============================================================================

class ActionExecutor:
    """
    İşlem yürütücü.
    
    PyAutoGUI ile masaüstü işlemlerini gerçekleştirir.
    """
    
    def __init__(self, config: ComputerUseConfig):
        self.config = config
        self._executor = ThreadPoolExecutor(max_workers=1)
        
        if not HAS_PYAUTOGUI:
            logger.error("pyautogui not installed! Action execution disabled.")
        
        logger.info("ActionExecutor initialized")
    
    async def execute(self, action: Action) -> Tuple[bool, Optional[str]]:
        """
        İşlemi yürüt.
        
        Returns:
            (success, error_message)
        """
        if not HAS_PYAUTOGUI:
            return False, "pyautogui yüklü değil!"
        
        action.executed_at = datetime.now()
        start_time = time.time()
        
        try:
            # Run in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._execute_sync,
                action
            )
            
            action.duration_ms = (time.time() - start_time) * 1000
            action.executed = True
            action.success = result[0]
            action.error = result[1]
            
            return result
            
        except Exception as e:
            action.duration_ms = (time.time() - start_time) * 1000
            action.executed = True
            action.success = False
            action.error = str(e)
            
            logger.error(f"Action execution failed: {e}")
            return False, str(e)
    
    def _execute_sync(self, action: Action) -> Tuple[bool, Optional[str]]:
        """Senkron işlem yürütme."""
        try:
            action_type = action.action_type
            
            if action_type == ActionType.CLICK:
                if action.x is not None and action.y is not None:
                    pyautogui.click(action.x, action.y, duration=self.config.mouse_speed)
                else:
                    pyautogui.click()
                    
            elif action_type == ActionType.DOUBLE_CLICK:
                if action.x is not None and action.y is not None:
                    pyautogui.doubleClick(action.x, action.y, duration=self.config.mouse_speed)
                else:
                    pyautogui.doubleClick()
                    
            elif action_type == ActionType.RIGHT_CLICK:
                if action.x is not None and action.y is not None:
                    pyautogui.rightClick(action.x, action.y, duration=self.config.mouse_speed)
                else:
                    pyautogui.rightClick()
                    
            elif action_type == ActionType.MOVE:
                if action.x is not None and action.y is not None:
                    pyautogui.moveTo(action.x, action.y, duration=self.config.mouse_speed)
                    
            elif action_type == ActionType.DRAG:
                if all([action.x, action.y, action.end_x, action.end_y]):
                    pyautogui.moveTo(action.x, action.y, duration=self.config.mouse_speed / 2)
                    pyautogui.drag(
                        action.end_x - action.x,
                        action.end_y - action.y,
                        duration=self.config.mouse_speed
                    )
                    
            elif action_type == ActionType.SCROLL:
                pyautogui.scroll(action.scroll_amount)
                
            elif action_type == ActionType.TYPE:
                if action.text:
                    # Use write for ASCII, typewrite for special chars
                    pyautogui.write(action.text, interval=0.02)
                    
            elif action_type == ActionType.HOTKEY:
                if action.keys:
                    pyautogui.hotkey(*action.keys)
                    
            elif action_type == ActionType.PRESS:
                if action.keys:
                    pyautogui.press(action.keys[0])
                    
            elif action_type == ActionType.WAIT:
                time.sleep(action.duration or 1.0)
                
            elif action_type == ActionType.OPEN_APP:
                if action.app_name:
                    # Windows Run dialog
                    pyautogui.hotkey("win", "r")
                    time.sleep(0.5)
                    pyautogui.write(action.app_name)
                    pyautogui.press("enter")
                    time.sleep(1.0)
            
            elif action_type == ActionType.SCREENSHOT:
                # Already handled by vision system
                pass
            
            else:
                return False, f"Desteklenmeyen işlem tipi: {action_type}"
            
            return True, None
            
        except pyautogui.FailSafeException:
            return False, "🛑 FailSafe tetiklendi! Mouse köşeye taşındı."
        except Exception as e:
            return False, str(e)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """Mevcut mouse pozisyonu."""
        if HAS_PYAUTOGUI:
            return pyautogui.position()
        return (0, 0)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Ekran boyutu."""
        if HAS_PYAUTOGUI:
            return pyautogui.size()
        return (1920, 1080)


# =============================================================================
# ACTION PLANNER
# =============================================================================

class ActionPlanner:
    """
    İşlem planlayıcı.
    
    Kullanıcı isteğini analiz eder ve eylem planı oluşturur.
    """
    
    PLANNING_PROMPT = """You are a desktop automation assistant. Analyze the user's request and create a step-by-step action plan.

CURRENT SCREEN STATE:
{screen_description}

USER REQUEST:
{task}

AVAILABLE ACTIONS (use EXACTLY these action names):
- click: Click at coordinates {{"action": "click", "x": 100, "y": 200, "description": "..."}}
- double_click: Double click {{"action": "double_click", "x": 100, "y": 200, "description": "..."}}
- right_click: Right click {{"action": "right_click", "x": 100, "y": 200, "description": "..."}}
- type: Type text {{"action": "type", "text": "hello", "description": "..."}}
- hotkey: Keyboard shortcut {{"action": "hotkey", "keys": ["ctrl", "t"], "description": "..."}}
- press: Press single key {{"action": "press", "key": "enter", "description": "..."}}
- scroll: Scroll {{"action": "scroll", "amount": 3, "description": "..."}}
- wait: Wait seconds {{"action": "wait", "seconds": 1, "description": "..."}}
- open_app: Open application {{"action": "open_app", "name": "chrome", "description": "..."}}

COMMON TASKS:
- Open Chrome new tab: hotkey ctrl+t or click on + icon
- Google search: type in search bar, press enter
- Open Wikipedia: type URL or search Google

RULES:
1. Use ONLY English action names: click, type, hotkey, press, scroll, wait, open_app
2. Estimate coordinates carefully (screen is typically 1920x1080)
3. Keep descriptions brief
4. Return ONLY a valid JSON array, nothing else

RESPONSE (JSON array only):
[
  {{"action": "hotkey", "keys": ["ctrl", "t"], "description": "Open new tab"}},
  {{"action": "type", "text": "search term", "description": "Type search"}},
  {{"action": "press", "key": "enter", "description": "Press Enter"}}
]"""

    COORDINATE_PROMPT = """Bu ekran görüntüsünde şu elementi bul: "{element}"

Element'in tahmini koordinatlarını ver:
- x: yatay pozisyon (0-1920)
- y: dikey pozisyon (0-1080)

Sadece JSON formatında yanıt ver:
{{"x": 123, "y": 456, "confidence": 0.8, "description": "..."}}"""

    def __init__(self, config: ComputerUseConfig, vision: RealtimeVisionSystem):
        self.config = config
        self.vision = vision
        
        logger.info("ActionPlanner initialized")
    
    async def create_plan(self, task: str) -> ActionPlan:
        """
        Görev için eylem planı oluştur.
        
        Args:
            task: Kullanıcı görevi
            
        Returns:
            ActionPlan
        """
        plan = ActionPlan(task=task)
        
        try:
            # 1. Get current screen state
            screen_analysis = await self.vision.capture_and_analyze(
                mode=VisionMode.UI_ANALYSIS
            )
            
            if not screen_analysis.success:
                plan.error = "Ekran analizi başarısız"
                return plan
            
            # 2. Generate action plan
            prompt = self.PLANNING_PROMPT.format(
                screen_description=screen_analysis.ai_response,
                task=task
            )
            
            # Use vision for planning (LLM call)
            planning_result = await self.vision.capture_and_analyze(
                mode=VisionMode.CUSTOM,
                custom_prompt=prompt
            )
            
            if not planning_result.success:
                plan.error = "Plan oluşturma başarısız"
                return plan
            
            # 3. Parse actions
            actions = self._parse_actions(planning_result.ai_response)
            plan.actions = actions
            plan.total_steps = len(actions)
            
            # 4. Take before screenshot
            frame = self.vision._stream_manager.capture_single()
            if frame:
                plan.before_screenshot = frame.image_base64
            
            return plan
            
        except Exception as e:
            logger.error(f"Plan creation failed: {e}")
            plan.error = str(e)
            return plan
    
    def _parse_actions(self, response: str) -> List[Action]:
        """LLM yanıtından işlemleri parse et."""
        actions = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if not json_match:
                logger.warning("No JSON array found in response")
                return actions
            
            json_str = json_match.group()
            action_dicts = json.loads(json_str)
            
            for i, ad in enumerate(action_dicts):
                action = self._dict_to_action(ad, i)
                if action:
                    actions.append(action)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Action parsing error: {e}")
        
        return actions
    
    def _dict_to_action(self, d: Dict, index: int) -> Optional[Action]:
        """Dict'i Action objesine dönüştür."""
        try:
            action_str = d.get("action", "").lower().strip()
            
            action = Action(
                description=d.get("description", f"Adım {index + 1}"),
                reasoning=d.get("reasoning", ""),
            )
            
            # Extended action type mapping (including Turkish and common variations)
            click_types = ["click", "tıkla", "tikla", "tiklamak", "tıklama", "single_click", "left_click"]
            double_click_types = ["double_click", "doubleclick", "çift_tıkla", "cift_tikla", "çift tıkla"]
            right_click_types = ["right_click", "rightclick", "sağ_tıkla", "sag_tikla", "sağ tıkla"]
            type_types = ["type", "yaz", "yazmak", "yazma", "write", "input", "text"]
            hotkey_types = ["hotkey", "kısayol", "kisayol", "shortcut", "keyboard_shortcut"]
            press_types = ["press", "bas", "basmak", "key_press", "keypress", "tuş", "tus"]
            scroll_types = ["scroll", "kaydır", "kaydir", "kaydirma"]
            wait_types = ["wait", "bekle", "beklemek", "sleep", "delay"]
            open_app_types = ["open_app", "open", "aç", "ac", "açmak", "launch", "run", "start"]
            drag_types = ["drag", "sürükle", "surukle", "drag_drop"]
            
            if action_str in click_types:
                action.action_type = ActionType.CLICK
                action.x = d.get("x")
                action.y = d.get("y")
                
            elif action_str in double_click_types:
                action.action_type = ActionType.DOUBLE_CLICK
                action.x = d.get("x")
                action.y = d.get("y")
                
            elif action_str in right_click_types:
                action.action_type = ActionType.RIGHT_CLICK
                action.x = d.get("x")
                action.y = d.get("y")
                
            elif action_str in type_types:
                action.action_type = ActionType.TYPE
                action.text = d.get("text", "")
                
            elif action_str in hotkey_types:
                action.action_type = ActionType.HOTKEY
                keys = d.get("keys", [])
                if isinstance(keys, str):
                    keys = [keys]
                action.keys = keys
                
            elif action_str in press_types:
                action.action_type = ActionType.PRESS
                key = d.get("key", "")
                action.keys = [key] if key else []
                
            elif action_str in scroll_types:
                action.action_type = ActionType.SCROLL
                action.scroll_amount = d.get("amount", 3)
                
            elif action_str in wait_types:
                action.action_type = ActionType.WAIT
                action.duration = d.get("seconds", 1.0)
                
            elif action_str in open_app_types:
                action.action_type = ActionType.OPEN_APP
                action.app_name = d.get("name", d.get("app", d.get("text", "")))
                
            elif action_str in drag_types:
                action.action_type = ActionType.DRAG
                action.x = d.get("x")
                action.y = d.get("y")
                action.end_x = d.get("end_x")
                action.end_y = d.get("end_y")
                
            else:
                logger.warning(f"Unknown action type: {action_str}")
                return None
            
            return action
            
        except Exception as e:
            logger.error(f"Action conversion error: {e}")
            return None
    
    async def find_element_coordinates(
        self, 
        element_description: str
    ) -> Optional[Tuple[int, int]]:
        """UI elementinin koordinatlarını bul."""
        prompt = self.COORDINATE_PROMPT.format(element=element_description)
        
        result = await self.vision.capture_and_analyze(
            mode=VisionMode.CUSTOM,
            custom_prompt=prompt
        )
        
        if not result.success:
            return None
        
        try:
            json_match = re.search(r'\{.*\}', result.ai_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                x = data.get("x")
                y = data.get("y")
                if x is not None and y is not None:
                    return (int(x), int(y))
        except Exception as e:
            logger.error(f"Coordinate extraction failed: {e}")
        
        return None


# =============================================================================
# APPROVAL MANAGER
# =============================================================================

class ApprovalManager:
    """
    Onay yönetim sistemi.
    
    İşlemler için kullanıcı onayı toplar.
    """
    
    def __init__(self, config: ComputerUseConfig):
        self.config = config
        self._pending_approvals: Dict[str, ApprovalRequest] = {}
        self._approval_events: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()
        
        logger.info("ApprovalManager initialized")
    
    async def request_approval(
        self,
        action: Action,
        plan_id: str,
        screenshot_base64: Optional[str] = None,
    ) -> ApprovalRequest:
        """
        Onay iste.
        
        Args:
            action: Onaylanacak işlem
            plan_id: Plan ID
            screenshot_base64: Ekran görüntüsü
            
        Returns:
            ApprovalRequest
        """
        async with self._lock:
            request = ApprovalRequest(
                action=action,
                plan_id=plan_id,
                screenshot_base64=screenshot_base64,
                expires_at=datetime.now() + timedelta(seconds=self.config.approval_timeout),
            )
            
            # Highlight region if coordinates available
            if action.x is not None and action.y is not None:
                request.highlighted_region = (
                    max(0, action.x - 20),
                    max(0, action.y - 20),
                    40, 40
                )
            
            self._pending_approvals[request.id] = request
            self._approval_events[request.id] = asyncio.Event()
            
            logger.info(f"Approval requested: {request.id} - {action.get_human_readable()}")
            
            return request
    
    async def wait_for_approval(
        self,
        request_id: str,
        timeout: Optional[float] = None
    ) -> ApprovalStatus:
        """
        Onay bekle.
        
        Args:
            request_id: İstek ID
            timeout: Timeout (saniye)
            
        Returns:
            ApprovalStatus
        """
        timeout = timeout or self.config.approval_timeout
        
        event = self._approval_events.get(request_id)
        if not event:
            return ApprovalStatus.CANCELLED
        
        request = self._pending_approvals.get(request_id)
        if not request:
            return ApprovalStatus.CANCELLED
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return request.status
        except asyncio.TimeoutError:
            request.status = ApprovalStatus.TIMEOUT
            return ApprovalStatus.TIMEOUT
    
    async def approve(self, request_id: str, reason: Optional[str] = None) -> bool:
        """İşlemi onayla."""
        async with self._lock:
            request = self._pending_approvals.get(request_id)
            if not request:
                return False
            
            if request.is_expired():
                request.status = ApprovalStatus.TIMEOUT
                return False
            
            request.status = ApprovalStatus.APPROVED
            request.responded_at = datetime.now()
            request.response_reason = reason
            
            if request.action:
                request.action.approval_status = ApprovalStatus.APPROVED
            
            event = self._approval_events.get(request_id)
            if event:
                event.set()
            
            logger.info(f"Approved: {request_id}")
            return True
    
    async def reject(self, request_id: str, reason: Optional[str] = None) -> bool:
        """İşlemi reddet."""
        async with self._lock:
            request = self._pending_approvals.get(request_id)
            if not request:
                return False
            
            request.status = ApprovalStatus.REJECTED
            request.responded_at = datetime.now()
            request.response_reason = reason or "Kullanıcı tarafından reddedildi"
            
            if request.action:
                request.action.approval_status = ApprovalStatus.REJECTED
            
            event = self._approval_events.get(request_id)
            if event:
                event.set()
            
            logger.info(f"Rejected: {request_id}")
            return True
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Bekleyen onaylar."""
        return [
            r for r in self._pending_approvals.values()
            if r.status == ApprovalStatus.PENDING and not r.is_expired()
        ]
    
    def get_approval(self, request_id: str) -> Optional[ApprovalRequest]:
        """Onay isteği al."""
        return self._pending_approvals.get(request_id)
    
    def cleanup_expired(self):
        """Süresi dolmuş istekleri temizle."""
        expired = [
            rid for rid, req in self._pending_approvals.items()
            if req.is_expired()
        ]
        for rid in expired:
            del self._pending_approvals[rid]
            if rid in self._approval_events:
                del self._approval_events[rid]


# =============================================================================
# COMPUTER USE AGENT
# =============================================================================

class ComputerUseAgent:
    """
    Ana Computer Use Agent.
    
    Ekranı analiz eder, işlem planlar ve kullanıcı onayıyla uygular.
    
    Kullanım:
        agent = ComputerUseAgent()
        
        # Görev oluştur
        plan = await agent.create_task("Notepad'i aç ve 'Merhaba' yaz")
        
        # Planı çalıştır (her adımda onay istenir)
        async for status in agent.execute_plan(plan.id):
            print(status)
    """
    
    def __init__(self, config: Optional[ComputerUseConfig] = None):
        self.config = config or ComputerUseConfig()
        
        # Components
        self.vision = get_realtime_vision()
        self.safety = SafetyGuard(self.config)
        self.executor = ActionExecutor(self.config)
        self.planner = ActionPlanner(self.config, self.vision)
        self.approvals = ApprovalManager(self.config)
        
        # State
        self._plans: Dict[str, ActionPlan] = {}
        self._active_plan: Optional[str] = None
        self._running = False
        
        logger.info(f"ComputerUseAgent initialized in {self.config.mode.value} mode")
    
    # =========================================================================
    # TASK MANAGEMENT
    # =========================================================================
    
    async def create_task(self, task: str) -> ActionPlan:
        """
        Yeni görev oluştur.
        
        Args:
            task: Görev açıklaması
            
        Returns:
            ActionPlan
        """
        logger.info(f"Creating task: {task}")
        
        # Create plan
        plan = await self.planner.create_plan(task)
        
        # Validate all actions
        for action in plan.actions:
            is_valid, error = self.safety.validate_action(action)
            if not is_valid:
                action.error = error
                action.approval_status = ApprovalStatus.REJECTED
                logger.warning(f"Action blocked: {error}")
        
        # Store plan
        self._plans[plan.id] = plan
        
        return plan
    
    async def execute_plan(
        self,
        plan_id: str,
        skip_approval: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Planı çalıştır.
        
        Her adımda status yielder:
        - {"type": "started", "plan": {...}}
        - {"type": "approval_needed", "request": {...}}
        - {"type": "step_completed", "action": {...}}
        - {"type": "completed", "success": True}
        - {"type": "error", "message": "..."}
        
        Args:
            plan_id: Plan ID
            skip_approval: Onay atla (sadece AUTONOMOUS modda)
            
        Yields:
            Status updates
        """
        plan = self._plans.get(plan_id)
        if not plan:
            yield {"type": "error", "message": "Plan bulunamadı"}
            return
        
        if self._running:
            yield {"type": "error", "message": "Başka bir plan zaten çalışıyor"}
            return
        
        self._running = True
        self._active_plan = plan_id
        plan.started_at = datetime.now()
        
        yield {"type": "started", "plan": plan.to_dict()}
        
        try:
            for i, action in enumerate(plan.actions):
                plan.current_step = i + 1
                
                # Check emergency stop
                if self.safety.check_emergency_stop():
                    plan.cancelled = True
                    yield {"type": "emergency_stop", "message": "🛑 Emergency stop!"}
                    break
                
                # Skip already rejected actions
                if action.approval_status == ApprovalStatus.REJECTED:
                    yield {
                        "type": "step_skipped",
                        "action": action.to_dict(),
                        "reason": action.error or "Reddedildi"
                    }
                    continue
                
                # Preview mode - don't execute
                if self.config.mode == AgentMode.PREVIEW:
                    yield {
                        "type": "preview",
                        "action": action.to_dict(),
                        "message": f"[PREVIEW] {action.get_human_readable()}"
                    }
                    continue
                
                # Request approval if needed
                if not skip_approval and self.safety.requires_approval(action):
                    # Get current screenshot
                    frame = self.vision._stream_manager.capture_single()
                    screenshot = frame.image_base64 if frame else None
                    
                    # Create approval request
                    approval_req = await self.approvals.request_approval(
                        action=action,
                        plan_id=plan_id,
                        screenshot_base64=screenshot,
                    )
                    
                    yield {
                        "type": "approval_needed",
                        "request": approval_req.to_dict(),
                        "action": action.to_dict(),
                        "message": f"⚠️ Onay gerekiyor: {action.get_human_readable()}"
                    }
                    
                    # Wait for approval
                    status = await self.approvals.wait_for_approval(approval_req.id)
                    
                    if status != ApprovalStatus.APPROVED:
                        yield {
                            "type": "step_rejected",
                            "action": action.to_dict(),
                            "status": status.value,
                            "message": f"❌ İşlem onaylanmadı: {status.value}"
                        }
                        continue
                
                # Execute action
                yield {
                    "type": "step_executing",
                    "action": action.to_dict(),
                    "message": f"▶️ Çalıştırılıyor: {action.get_human_readable()}"
                }
                
                success, error = await self.executor.execute(action)
                
                # Log action
                self.safety.log_action(action)
                
                if success:
                    yield {
                        "type": "step_completed",
                        "action": action.to_dict(),
                        "message": f"✅ Tamamlandı: {action.get_human_readable()}"
                    }
                else:
                    yield {
                        "type": "step_failed",
                        "action": action.to_dict(),
                        "error": error,
                        "message": f"❌ Başarısız: {error}"
                    }
                    
                    # Ask if should continue
                    # For now, continue to next step
                
                # Small delay between actions
                await asyncio.sleep(0.3)
            
            # Take after screenshot
            frame = self.vision._stream_manager.capture_single()
            if frame:
                plan.after_screenshot = frame.image_base64
            
            plan.completed_at = datetime.now()
            plan.success = not plan.cancelled
            
            yield {
                "type": "completed",
                "success": plan.success,
                "plan": plan.to_dict(),
                "message": "🎉 Plan tamamlandı!" if plan.success else "⚠️ Plan iptal edildi"
            }
            
        except Exception as e:
            plan.error = str(e)
            logger.error(f"Plan execution error: {e}")
            yield {"type": "error", "message": str(e)}
            
        finally:
            self._running = False
            self._active_plan = None
    
    async def cancel_plan(self, plan_id: str) -> bool:
        """Planı iptal et."""
        if self._active_plan == plan_id:
            self.safety._emergency_stop = True
            return True
        
        plan = self._plans.get(plan_id)
        if plan:
            plan.cancelled = True
            return True
        
        return False
    
    # =========================================================================
    # QUICK ACTIONS
    # =========================================================================
    
    async def quick_click(self, x: int, y: int) -> Dict[str, Any]:
        """Hızlı tıklama."""
        action = Action(
            action_type=ActionType.CLICK,
            x=x, y=y,
            description=f"Tıkla: ({x}, {y})"
        )
        
        is_valid, error = self.safety.validate_action(action)
        if not is_valid:
            return {"success": False, "error": error}
        
        if self.config.mode != AgentMode.AUTONOMOUS:
            return {
                "success": False,
                "error": "Quick actions require AUTONOMOUS mode",
                "action": action.to_dict(),
            }
        
        success, error = await self.executor.execute(action)
        self.safety.log_action(action)
        
        return {"success": success, "error": error, "action": action.to_dict()}
    
    async def quick_type(self, text: str) -> Dict[str, Any]:
        """Hızlı yazma."""
        action = Action(
            action_type=ActionType.TYPE,
            text=text,
            description=f"Yaz: {text[:20]}..."
        )
        
        is_valid, error = self.safety.validate_action(action)
        if not is_valid:
            return {"success": False, "error": error}
        
        if self.config.mode != AgentMode.AUTONOMOUS:
            return {
                "success": False,
                "error": "Quick actions require AUTONOMOUS mode",
                "action": action.to_dict(),
            }
        
        success, error = await self.executor.execute(action)
        self.safety.log_action(action)
        
        return {"success": success, "error": error, "action": action.to_dict()}
    
    async def quick_hotkey(self, *keys: str) -> Dict[str, Any]:
        """Hızlı kısayol."""
        action = Action(
            action_type=ActionType.HOTKEY,
            keys=list(keys),
            description=f"Kısayol: {'+'.join(keys)}"
        )
        
        is_valid, error = self.safety.validate_action(action)
        if not is_valid:
            return {"success": False, "error": error}
        
        if self.config.mode != AgentMode.AUTONOMOUS:
            return {
                "success": False,
                "error": "Quick actions require AUTONOMOUS mode",
                "action": action.to_dict(),
            }
        
        success, error = await self.executor.execute(action)
        self.safety.log_action(action)
        
        return {"success": success, "error": error, "action": action.to_dict()}
    
    # =========================================================================
    # STATUS & INFO
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Agent durumu."""
        return {
            "mode": self.config.mode.value,
            "running": self._running,
            "active_plan": self._active_plan,
            "emergency_stop": self.safety.check_emergency_stop(),
            "pending_approvals": len(self.approvals.get_pending_approvals()),
            "total_plans": len(self._plans),
            "mouse_position": self.executor.get_mouse_position(),
            "screen_size": self.executor.get_screen_size(),
            "dependencies": {
                "pyautogui": HAS_PYAUTOGUI,
                "pynput": HAS_PYNPUT,
                "PIL": HAS_PIL,
                "mss": HAS_MSS,
            }
        }
    
    def get_plan(self, plan_id: str) -> Optional[ActionPlan]:
        """Plan al."""
        return self._plans.get(plan_id)
    
    def list_plans(self, limit: int = 10) -> List[Dict]:
        """Planları listele."""
        plans = sorted(
            self._plans.values(),
            key=lambda p: p.created_at,
            reverse=True
        )
        return [p.to_dict() for p in plans[:limit]]
    
    def get_action_history(self, limit: int = 50) -> List[Dict]:
        """İşlem geçmişi."""
        return self.safety.get_action_history(limit)
    
    def reset_emergency_stop(self):
        """Emergency stop sıfırla."""
        self.safety.reset_emergency_stop()
    
    def shutdown(self):
        """Kapat."""
        self.safety.shutdown()


# =============================================================================
# SINGLETON & FACTORY
# =============================================================================

_computer_use_agent: Optional[ComputerUseAgent] = None


def get_computer_use_agent(config: Optional[ComputerUseConfig] = None) -> ComputerUseAgent:
    """Singleton instance al."""
    global _computer_use_agent
    
    if _computer_use_agent is None:
        _computer_use_agent = ComputerUseAgent(config)
    
    return _computer_use_agent


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Config
    "ComputerUseConfig",
    "ActionType",
    "RiskLevel",
    "ApprovalStatus",
    "AgentMode",
    # Data classes
    "Action",
    "ActionPlan",
    "ApprovalRequest",
    # Components
    "SafetyGuard",
    "ActionExecutor",
    "ActionPlanner",
    "ApprovalManager",
    # Main agent
    "ComputerUseAgent",
    # Factory
    "get_computer_use_agent",
]
