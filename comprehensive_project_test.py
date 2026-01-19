#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                   ENTERPRISE AI ASSISTANT - COMPREHENSIVE TEST SUITE         ║
║                           Version 2.0 - Industry Standard                     ║
║══════════════════════════════════════════════════════════════════════════════║
║  Bu test scripti projenin HER PARÇASINI test eder:                            ║
║  • Core Modules (50+ modül)                                                   ║
║  • API Endpoints (tüm route'lar)                                              ║
║  • Agents (orchestrator, planning, research, writer, vb.)                     ║
║  • RAG System (retrieval, chunking, embedding, reranking)                     ║
║  • Voice/Vision (TTS, STT, LLaVA)                                             ║
║  • Screen Capture (mss, local analysis)                                       ║
║  • Frontend Comparison (Streamlit vs Next.js)                                 ║
║  • Electron Desktop App                                                       ║
║  • Database Systems (SQLite, ChromaDB)                                        ║
║  • Performance & Load Tests                                                   ║
║  • Security Checks                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import asyncio
import threading
import subprocess
import importlib
import traceback
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings("ignore")

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

class TestStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    SKIPPED = "⏭️ SKIPPED"
    WARNING = "⚠️ WARNING"
    ERROR = "💥 ERROR"

class TestCategory(Enum):
    CORE = "Core Modules"
    API = "API Endpoints"
    AGENTS = "AI Agents"
    RAG = "RAG System"
    VOICE = "Voice/Multimodal"
    SCREEN = "Screen Capture"
    FRONTEND = "Frontend"
    ELECTRON = "Electron App"
    DATABASE = "Databases"
    TOOLS = "Tools"
    PLUGINS = "Plugins"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
    INTEGRATION = "Integration"

@dataclass
class TestResult:
    name: str
    category: TestCategory
    status: TestStatus
    message: str = ""
    duration_ms: float = 0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CategoryReport:
    category: TestCategory
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    warnings: int = 0
    results: List[TestResult] = field(default_factory=list)

class TestReport:
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.categories: Dict[TestCategory, CategoryReport] = {}
        self.all_results: List[TestResult] = []
        
    def add_result(self, result: TestResult):
        self.all_results.append(result)
        
        if result.category not in self.categories:
            self.categories[result.category] = CategoryReport(category=result.category)
        
        cat_report = self.categories[result.category]
        cat_report.total += 1
        cat_report.results.append(result)
        
        if result.status == TestStatus.PASSED:
            cat_report.passed += 1
        elif result.status == TestStatus.FAILED:
            cat_report.failed += 1
        elif result.status == TestStatus.SKIPPED:
            cat_report.skipped += 1
        elif result.status == TestStatus.WARNING:
            cat_report.warnings += 1
    
    def finalize(self):
        self.end_time = datetime.now()
    
    @property
    def total_tests(self) -> int:
        return len(self.all_results)
    
    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.all_results if r.status == TestStatus.PASSED)
    
    @property
    def failed_tests(self) -> int:
        return sum(1 for r in self.all_results if r.status == TestStatus.FAILED)
    
    @property
    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

# Global report instance
report = TestReport()

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def log_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─'*60}{Colors.RESET}")

def log_test(name: str, status: TestStatus, message: str = "", duration_ms: float = 0):
    status_colors = {
        TestStatus.PASSED: Colors.GREEN,
        TestStatus.FAILED: Colors.RED,
        TestStatus.SKIPPED: Colors.YELLOW,
        TestStatus.WARNING: Colors.YELLOW,
        TestStatus.ERROR: Colors.RED,
    }
    color = status_colors.get(status, Colors.WHITE)
    duration_str = f" ({duration_ms:.1f}ms)" if duration_ms > 0 else ""
    msg_str = f" - {message}" if message else ""
    print(f"  {color}{status.value}{Colors.RESET} {name}{duration_str}{msg_str}")

# ============================================================================
# TEST UTILITIES
# ============================================================================

def run_test(name: str, category: TestCategory, test_func, *args, **kwargs) -> TestResult:
    """Run a single test and record result."""
    start = time.time()
    try:
        result = test_func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        
        if isinstance(result, tuple):
            status, message, details = result if len(result) == 3 else (*result, {})
        elif isinstance(result, bool):
            status = TestStatus.PASSED if result else TestStatus.FAILED
            message = ""
            details = {}
        else:
            status = TestStatus.PASSED
            message = str(result) if result else ""
            details = {}
        
        test_result = TestResult(
            name=name,
            category=category,
            status=status,
            message=message,
            duration_ms=duration,
            details=details
        )
        
    except Exception as e:
        duration = (time.time() - start) * 1000
        test_result = TestResult(
            name=name,
            category=category,
            status=TestStatus.ERROR,
            message=str(e)[:100],
            duration_ms=duration,
            details={"traceback": traceback.format_exc()}
        )
    
    report.add_result(test_result)
    log_test(name, test_result.status, test_result.message, test_result.duration_ms)
    return test_result

def check_import(module_name: str) -> Tuple[TestStatus, str, Dict]:
    """Check if a module can be imported."""
    try:
        module = importlib.import_module(module_name)
        # Check for main classes/functions
        attrs = [a for a in dir(module) if not a.startswith('_')]
        return TestStatus.PASSED, f"{len(attrs)} exports", {"exports": attrs[:10]}
    except ImportError as e:
        return TestStatus.FAILED, f"Import error: {e}", {}
    except Exception as e:
        return TestStatus.ERROR, str(e)[:50], {}

def check_file_exists(file_path: Path) -> Tuple[TestStatus, str, Dict]:
    """Check if a file exists."""
    if file_path.exists():
        size = file_path.stat().st_size
        return TestStatus.PASSED, f"{size} bytes", {"size": size}
    return TestStatus.FAILED, "File not found", {}

def check_directory_structure(dir_path: Path, expected_files: List[str]) -> Tuple[TestStatus, str, Dict]:
    """Check if directory has expected files."""
    if not dir_path.exists():
        return TestStatus.FAILED, "Directory not found", {}
    
    existing = [f for f in expected_files if (dir_path / f).exists()]
    missing = [f for f in expected_files if not (dir_path / f).exists()]
    
    if not missing:
        return TestStatus.PASSED, f"All {len(expected_files)} files present", {"files": existing}
    elif len(existing) > len(missing):
        return TestStatus.WARNING, f"Missing: {', '.join(missing[:3])}", {"missing": missing}
    else:
        return TestStatus.FAILED, f"Missing {len(missing)} files", {"missing": missing}

# ============================================================================
# CATEGORY 1: CORE MODULES TESTS
# ============================================================================

def test_core_modules():
    """Test all core modules for import and basic functionality."""
    log_section("📦 CORE MODULES TESTS")
    
    core_modules = [
        "core.config",
        "core.llm_manager",
        "core.vector_store",
        "core.chromadb_manager",
        "core.chromadb_resilient",
        "core.embedding",
        "core.circuit_breaker",
        "core.error_recovery",
        "core.exceptions",
        "core.health",
        "core.logger",
        "core.session_manager",
        "core.notes_manager",
        "core.analytics",
        "core.cache",
        "core.rate_limiter",
        "core.conversation",
        "core.document_processor",
        "core.export",
        "core.memory",
        "core.memgpt_memory",
        "core.performance",
        "core.streaming",
        "core.stream_buffer",
        "core.task_queue",
        "core.tracing",
        "core.utils",
        "core.workflow",
        "core.router",
        "core.orchestrator",
        "core.prompts",
        "core.constants",
        "core.interfaces",
        "core.environment",
        "core.plugins",
        "core.guardrails",
        "core.advanced_guardrails",
        "core.moe_router",
        "core.graph_rag",
        "core.crag_system",
        "core.multi_agent_debate",
        "core.instructor_structured",
        "core.langfuse_observability",
        "core.langgraph_orchestration",
        "core.ragas_evaluation",
        "core.learning_workspace",
        "core.study_document_generator",
        "core.system_knowledge",
        "core.screen_capture",
        "core.voice_multimodal",
        "core.mcp_server",
        "core.mcp_providers",
        "core.mcp_cli",
        "core.startup_health",
        "core.test_generator",
    ]
    
    for module in core_modules:
        run_test(f"Import {module}", TestCategory.CORE, check_import, module)

# ============================================================================
# CATEGORY 2: API ENDPOINTS TESTS
# ============================================================================

def test_api_modules():
    """Test API modules and routers."""
    log_section("🌐 API MODULES TESTS")
    
    # API modules
    api_modules = [
        "api.main",
        "api.websocket",
        "api.websocket_v2",
        "api.learning_endpoints",
        "api.mcp_endpoints",
        "api.routers.health",
        "api.routers.documents",
        "api.routers.notes",
        "api.routers.rag",
        "api.routers.admin",
        "api.routers.plugins",
        "api.routers.advanced_rag",
        "api.routers.voice_router",
        "api.routers.screen_router",
    ]
    
    for module in api_modules:
        run_test(f"Import {module}", TestCategory.API, check_import, module)
    
    # Test API app creation
    def test_fastapi_app():
        try:
            from api.main import app
            routes = [r.path for r in app.routes]
            return TestStatus.PASSED, f"{len(routes)} routes", {"routes": routes[:10]}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("FastAPI App Creation", TestCategory.API, test_fastapi_app)

def test_api_endpoints_live():
    """Test live API endpoints (requires running server)."""
    log_section("🔌 LIVE API ENDPOINT TESTS")
    
    import requests
    
    base_url = "http://localhost:8001"
    
    endpoints = [
        ("GET", "/", "Root"),
        ("GET", "/health", "Health Check"),
        ("GET", "/health/live", "Liveness Probe"),
        ("GET", "/health/ready", "Readiness Probe"),
        ("GET", "/status", "Status"),
        ("GET", "/status/circuits", "Circuit Breakers"),
        ("GET", "/api/rag/sync-status", "RAG Sync Status"),
        ("GET", "/api/documents", "Documents List"),
        ("GET", "/api/notes", "Notes List"),
        ("GET", "/api/voice/status", "Voice Status"),
        ("GET", "/api/screen/status", "Screen Status"),
        ("GET", "/api/screen/monitors", "Screen Monitors"),
        ("GET", "/api/admin/stats", "Admin Stats"),
        ("GET", "/api/plugins", "Plugins List"),
        ("GET", "/api/web-search/stats", "Web Search Stats"),
        ("GET", "/docs", "OpenAPI Docs"),
    ]
    
    def test_endpoint(method: str, path: str):
        try:
            url = f"{base_url}{path}"
            if method == "GET":
                r = requests.get(url, timeout=10)
            elif method == "POST":
                r = requests.post(url, json={}, timeout=10)
            else:
                return TestStatus.SKIPPED, "Unknown method", {}
            
            if r.status_code == 200:
                return TestStatus.PASSED, f"HTTP {r.status_code}", {"response_size": len(r.content)}
            elif r.status_code < 500:
                return TestStatus.WARNING, f"HTTP {r.status_code}", {}
            else:
                return TestStatus.FAILED, f"HTTP {r.status_code}", {}
        except requests.exceptions.ConnectionError:
            return TestStatus.SKIPPED, "Server not running", {}
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    for method, path, name in endpoints:
        run_test(f"{name} ({method} {path})", TestCategory.API, test_endpoint, method, path)

# ============================================================================
# CATEGORY 3: AI AGENTS TESTS
# ============================================================================

def test_agents():
    """Test AI agent modules."""
    log_section("🤖 AI AGENTS TESTS")
    
    agent_modules = [
        "agents.base_agent",
        "agents.orchestrator",
        "agents.assistant_agent",
        "agents.analyzer_agent",
        "agents.planning_agent",
        "agents.research_agent",
        "agents.writer_agent",
        "agents.enhanced_agent",
        "agents.react_agent",
        "agents.self_reflection",
    ]
    
    for module in agent_modules:
        run_test(f"Import {module}", TestCategory.AGENTS, check_import, module)
    
    # Test orchestrator
    def test_orchestrator():
        try:
            from agents.orchestrator import orchestrator
            status = orchestrator.get_agents_status()
            return TestStatus.PASSED, f"{len(status)} agents", {"agents": list(status.keys())}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Orchestrator Status", TestCategory.AGENTS, test_orchestrator)

# ============================================================================
# CATEGORY 4: RAG SYSTEM TESTS
# ============================================================================

def test_rag_system():
    """Test RAG system components."""
    log_section("📚 RAG SYSTEM TESTS")
    
    rag_modules = [
        "rag.document_loader",
        "rag.chunker",
        "rag.retriever",
        "rag.reranker",
        "rag.pipeline",
        "rag.orchestrator",
        "rag.unified_orchestrator",
        "rag.advanced_rag",
        "rag.agentic_rag",
        "rag.self_rag",
        "rag.conversational_rag",
        "rag.multimodal_rag",
        "rag.hybrid_search",
        "rag.query_expansion",
        "rag.citation_verifier",
        "rag.knowledge_graph",
        "rag.graph_rag_advanced",
        "rag.evaluation",
        "rag.ragas_metrics",
        "rag.async_processor",
    ]
    
    for module in rag_modules:
        run_test(f"Import {module}", TestCategory.RAG, check_import, module)
    
    # Test vector store
    def test_vector_store():
        try:
            from core.vector_store import vector_store
            count = vector_store.count()
            stats = vector_store.get_stats()
            return TestStatus.PASSED, f"{count} documents", {"stats": stats}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Vector Store Connection", TestCategory.RAG, test_vector_store)
    
    # Test ChromaDB manager
    def test_chromadb_manager():
        try:
            from core.chromadb_manager import get_chromadb_manager
            manager = get_chromadb_manager()
            health = manager.check_health()  # Fixed: was get_health
            return TestStatus.PASSED, f"Healthy: {health.is_healthy}", {"health": health.__dict__}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("ChromaDB Manager", TestCategory.RAG, test_chromadb_manager)

# ============================================================================
# CATEGORY 5: VOICE/MULTIMODAL TESTS
# ============================================================================

def test_voice_multimodal():
    """Test voice and multimodal capabilities."""
    log_section("🎤 VOICE/MULTIMODAL TESTS")
    
    # Test voice module import
    run_test("Import core.voice_multimodal", TestCategory.VOICE, check_import, "core.voice_multimodal")
    
    # Test TTS availability
    def test_tts():
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            return TestStatus.PASSED, f"{len(voices)} voices", {"voices": len(voices)}
        except Exception as e:
            return TestStatus.WARNING, f"TTS not available: {e}", {}
    
    run_test("TTS (pyttsx3) Engine", TestCategory.VOICE, test_tts)
    
    # Test STT availability
    def test_stt():
        try:
            from faster_whisper import WhisperModel
            return TestStatus.PASSED, "faster-whisper available", {}
        except ImportError:
            return TestStatus.WARNING, "faster-whisper not installed", {}
        except Exception as e:
            return TestStatus.WARNING, str(e)[:50], {}
    
    run_test("STT (faster-whisper) Module", TestCategory.VOICE, test_stt)
    
    # Test Ollama connection
    def test_ollama():
        try:
            import ollama
            models = ollama.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            return TestStatus.PASSED, f"{len(model_names)} models", {"models": model_names[:5]}
        except Exception as e:
            return TestStatus.WARNING, f"Ollama not available: {str(e)[:30]}", {}
    
    run_test("Ollama Connection", TestCategory.VOICE, test_ollama)
    
    # Test LLaVA availability
    def test_llava():
        try:
            import ollama
            models = ollama.list()
            model_names = [m.get("model", "").split(":")[0] for m in models.get("models", [])]
            # Also check 'name' field as fallback
            if not any(model_names):
                model_names = [m.get("name", "").split(":")[0] for m in models.get("models", [])]
            has_llava = "llava" in model_names or any("llava" in n.lower() for n in model_names)
            if has_llava:
                return TestStatus.PASSED, "LLaVA model ready (100% LOCAL)", {}
            else:
                return TestStatus.WARNING, "LLaVA not installed", {"available": model_names}
        except Exception as e:
            return TestStatus.SKIPPED, str(e)[:50], {}
    
    run_test("LLaVA Vision Model", TestCategory.VOICE, test_llava)

# ============================================================================
# CATEGORY 6: SCREEN CAPTURE TESTS
# ============================================================================

def test_screen_capture():
    """Test screen capture system."""
    log_section("🖥️ SCREEN CAPTURE TESTS")
    
    # Test mss import
    def test_mss():
        try:
            import mss
            with mss.mss() as sct:
                monitors = sct.monitors
                return TestStatus.PASSED, f"{len(monitors)} monitors", {"monitors": len(monitors)}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("MSS Screen Capture Library", TestCategory.SCREEN, test_mss)
    
    # Test Pillow
    def test_pillow():
        try:
            from PIL import Image
            return TestStatus.PASSED, "Pillow available", {}
        except ImportError:
            return TestStatus.FAILED, "Pillow not installed", {}
    
    run_test("Pillow Image Processing", TestCategory.SCREEN, test_pillow)
    
    # Test screen capture module
    run_test("Import core.screen_capture", TestCategory.SCREEN, check_import, "core.screen_capture")
    
    # Test screen capture system
    def test_screen_system():
        try:
            from core.screen_capture import get_screen_capture_system
            system = get_screen_capture_system()
            status = system.get_status()
            return TestStatus.PASSED, f"Monitors: {len(status.get('monitors', []))}", {"status": status}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Screen Capture System", TestCategory.SCREEN, test_screen_system)

# ============================================================================
# CATEGORY 7: FRONTEND COMPARISON TESTS
# ============================================================================

def test_frontend_comparison():
    """Compare old (Streamlit) and new (Next.js) frontends."""
    log_section("🎨 FRONTEND COMPARISON TESTS")
    
    frontend_old = PROJECT_ROOT / "frontend"
    frontend_new = PROJECT_ROOT / "frontend-next"
    
    # Check old frontend structure
    old_files = ["app.py"]
    run_test("Old Frontend (Streamlit) Structure", TestCategory.FRONTEND, 
             check_directory_structure, frontend_old, old_files)
    
    # Check new frontend structure
    new_files = ["package.json", "next.config.js", "tsconfig.json", "tailwind.config.js"]
    run_test("New Frontend (Next.js) Structure", TestCategory.FRONTEND,
             check_directory_structure, frontend_new, new_files)
    
    # Analyze old frontend features
    def analyze_old_frontend():
        try:
            app_py = frontend_old / "app.py"
            if not app_py.exists():
                return TestStatus.FAILED, "app.py not found", {}
            
            content = app_py.read_text(encoding='utf-8')
            features = {
                "themes": "THEMES" in content,
                "multi_language": "TRANSLATIONS" in content,
                "web_search": "web_search" in content,
                "notes": "notes_manager" in content,
                "documents": "upload_document" in content,
                "streaming": "stream_chat" in content,
                "vision": "vision" in content.lower(),
                "favorites": "favorite" in content.lower(),
                "templates": "template" in content.lower(),
                "keyboard_shortcuts": "keyboard" in content.lower(),
                "session_management": "session_manager" in content,
                "websocket": "WebSocket" in content,
                "response_modes": "response_mode" in content,
                "complexity_levels": "complexity" in content.lower(),
                "dashboard": "dashboard" in content.lower(),
            }
            
            enabled = sum(1 for v in features.values() if v)
            return TestStatus.PASSED, f"{enabled}/{len(features)} features", {"features": features}
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    run_test("Old Frontend Features Analysis", TestCategory.FRONTEND, analyze_old_frontend)
    
    # Analyze new frontend features
    def analyze_new_frontend():
        try:
            pages_dir = frontend_new / "src" / "components" / "pages"
            if not pages_dir.exists():
                return TestStatus.FAILED, "Pages directory not found", {}
            
            pages = list(pages_dir.glob("*.tsx"))
            page_names = [p.stem for p in pages]
            
            # Check ChatPage features
            chat_page = pages_dir / "ChatPage.tsx"
            if chat_page.exists():
                content = chat_page.read_text(encoding='utf-8')
                features = {
                    "streaming": "stream" in content.lower(),
                    "web_search": "webSearch" in content or "web_search" in content,
                    "response_modes": "responseMode" in content or "response_mode" in content,
                    "complexity": "complexity" in content.lower(),
                    "favorites": "favorite" in content.lower(),
                    "templates": "template" in content.lower(),
                    "image_upload": "image" in content.lower() or "ImageIcon" in content,
                    "code_highlighting": "SyntaxHighlighter" in content,
                    "markdown": "ReactMarkdown" in content,
                    "animations": "motion" in content.lower() or "framer" in content.lower(),
                    "timestamps": "timestamp" in content.lower(),
                    "stop_generation": "stop" in content.lower(),
                }
                enabled = sum(1 for v in features.values() if v)
            else:
                features = {}
                enabled = 0
            
            return TestStatus.PASSED, f"{len(pages)} pages, {enabled} features", {
                "pages": page_names,
                "features": features
            }
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    run_test("New Frontend Features Analysis", TestCategory.FRONTEND, analyze_new_frontend)
    
    # Compare features
    def compare_frontends():
        try:
            old_app = frontend_old / "app.py"
            new_chat = frontend_new / "src" / "components" / "pages" / "ChatPage.tsx"
            new_hooks = frontend_new / "src" / "hooks"
            
            old_features = set()
            new_features = set()
            
            feature_keywords = [
                "web_search", "notes", "documents", "streaming", "vision",
                "favorite", "template", "keyboard", "session", "websocket",
                "theme", "language", "dashboard", "analytics", "export",
                "voice", "tts", "stt"
            ]
            
            if old_app.exists():
                old_content = old_app.read_text(encoding='utf-8').lower()
                for kw in feature_keywords:
                    if kw in old_content:
                        old_features.add(kw)
            
            if new_chat.exists():
                new_content = new_chat.read_text(encoding='utf-8').lower()
                for kw in feature_keywords:
                    if kw in new_content:
                        new_features.add(kw)
            
            # Also check hooks folder for WebSocket
            if new_hooks.exists():
                for hook_file in new_hooks.glob("*.ts"):
                    content = hook_file.read_text(encoding='utf-8').lower()
                    for kw in feature_keywords:
                        if kw in content:
                            new_features.add(kw)
            
            # Also check other pages
            new_pages = frontend_new / "src" / "components" / "pages"
            if new_pages.exists():
                for page in new_pages.glob("*.tsx"):
                    content = page.read_text(encoding='utf-8').lower()
                    for kw in feature_keywords:
                        if kw in content:
                            new_features.add(kw)
            
            only_in_old = old_features - new_features
            only_in_new = new_features - old_features
            common = old_features & new_features
            
            details = {
                "old_features": list(old_features),
                "new_features": list(new_features),
                "only_in_old": list(only_in_old),
                "only_in_new": list(only_in_new),
                "common": list(common)
            }
            
            if only_in_old:
                return TestStatus.WARNING, f"Missing in new: {', '.join(only_in_old)}", details
            else:
                return TestStatus.PASSED, f"All features present ({len(common)})", details
            
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    run_test("Frontend Feature Comparison", TestCategory.FRONTEND, compare_frontends)
    
    # Check API integration
    def check_api_file():
        api_file = frontend_new / "src" / "lib" / "api.ts"
        if not api_file.exists():
            return TestStatus.FAILED, "api.ts not found", {}
        
        content = api_file.read_text(encoding='utf-8')
        endpoints = content.count("'/api/")
        functions = content.count("export ")
        
        return TestStatus.PASSED, f"{endpoints} endpoints, {functions} exports", {}
    
    run_test("New Frontend API Integration", TestCategory.FRONTEND, check_api_file)

# ============================================================================
# CATEGORY 8: ELECTRON APP TESTS
# ============================================================================

def test_electron_app():
    """Test Electron desktop application."""
    log_section("🖥️ ELECTRON DESKTOP APP TESTS")
    
    electron_dir = PROJECT_ROOT / "electron-app"
    
    # Check directory structure
    run_test("Electron App Directory", TestCategory.ELECTRON,
             check_file_exists, electron_dir)
    
    # Check package.json
    def check_package_json():
        pkg_file = electron_dir / "package.json" if electron_dir.exists() else None
        if not pkg_file or not pkg_file.exists():
            # Check for package-lock at least
            lock_file = electron_dir / "package-lock.json"
            if lock_file.exists():
                return TestStatus.WARNING, "Only lock file found", {}
            return TestStatus.FAILED, "package.json not found", {}
        
        try:
            data = json.loads(pkg_file.read_text(encoding='utf-8'))
            return TestStatus.PASSED, f"Name: {data.get('name', 'unknown')}", {"package": data}
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    run_test("Electron package.json", TestCategory.ELECTRON, check_package_json)
    
    # Check build output
    def check_build():
        build_dir = electron_dir / "build"
        dist_dir = electron_dir / "dist"
        
        if dist_dir.exists():
            files = list(dist_dir.glob("*"))
            return TestStatus.PASSED, f"{len(files)} files in dist", {}
        elif build_dir.exists():
            files = list(build_dir.glob("*"))
            return TestStatus.PASSED, f"{len(files)} files in build", {}
        else:
            return TestStatus.WARNING, "No build output found", {}
    
    run_test("Electron Build Output", TestCategory.ELECTRON, check_build)
    
    # Check spec file
    spec_file = PROJECT_ROOT / "Enterprise AI Assistant.spec"
    run_test("PyInstaller Spec File", TestCategory.ELECTRON, check_file_exists, spec_file)

# ============================================================================
# CATEGORY 9: DATABASE TESTS
# ============================================================================

def test_databases():
    """Test database systems."""
    log_section("🗄️ DATABASE TESTS")
    
    data_dir = PROJECT_ROOT / "data"
    
    # Check data directory
    run_test("Data Directory", TestCategory.DATABASE, check_file_exists, data_dir)
    
    # Test SQLite databases
    sqlite_dbs = [
        "analytics.db",
        "conversations.db",
        "memory.db",
        "traces.db",
        "task_queue.db",
        "knowledge_graph.db",
    ]
    
    for db_name in sqlite_dbs:
        def test_sqlite_db(db_path):
            if not db_path.exists():
                return TestStatus.WARNING, "Database not created yet", {}
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                return TestStatus.PASSED, f"{len(tables)} tables", {"tables": tables}
            except Exception as e:
                return TestStatus.FAILED, str(e)[:50], {}
        
        run_test(f"SQLite: {db_name}", TestCategory.DATABASE, test_sqlite_db, data_dir / db_name)
    
    # Test ChromaDB
    def test_chromadb():
        chroma_dir = data_dir / "chroma_db"
        if not chroma_dir.exists():
            return TestStatus.WARNING, "ChromaDB directory not found", {}
        
        files = list(chroma_dir.glob("*"))
        return TestStatus.PASSED, f"{len(files)} files/dirs", {}
    
    run_test("ChromaDB Directory", TestCategory.DATABASE, test_chromadb)
    
    # Test backups
    def test_backups():
        backup_dir = data_dir / "chroma_backups"
        if not backup_dir.exists():
            backup_dir = data_dir / "backups"
        
        if not backup_dir.exists():
            return TestStatus.WARNING, "No backup directory", {}
        
        backups = list(backup_dir.glob("*"))
        return TestStatus.PASSED, f"{len(backups)} backups", {}
    
    run_test("Database Backups", TestCategory.DATABASE, test_backups)

# ============================================================================
# CATEGORY 10: TOOLS TESTS
# ============================================================================

def test_tools():
    """Test tool modules."""
    log_section("🔧 TOOLS TESTS")
    
    tool_modules = [
        "tools.base_tool",
        "tools.tool_manager",
        "tools.calculator_tool",
        "tools.code_executor_tool",
        "tools.file_tool",
        "tools.file_operations_tool",
        "tools.web_tool",
        "tools.web_search_tool",
        "tools.web_search_engine",
        "tools.rag_tool",
        "tools.research_synthesizer",
        "tools.mcp_integration",
        "tools.offline_smoke",
    ]
    
    for module in tool_modules:
        run_test(f"Import {module}", TestCategory.TOOLS, check_import, module)

# ============================================================================
# CATEGORY 11: PLUGINS TESTS
# ============================================================================

def test_plugins():
    """Test plugin modules."""
    log_section("🔌 PLUGINS TESTS")
    
    plugin_modules = [
        "plugins.base",
        "plugins.code_analysis_plugin",
        "plugins.text_processing_plugin",
        "plugins.web_search_plugin",
    ]
    
    for module in plugin_modules:
        run_test(f"Import {module}", TestCategory.PLUGINS, check_import, module)

# ============================================================================
# CATEGORY 12: PERFORMANCE TESTS
# ============================================================================

def test_performance():
    """Test performance metrics."""
    log_section("⚡ PERFORMANCE TESTS")
    
    # Test import time
    def test_import_time():
        import time
        modules = ["core.config", "core.llm_manager", "api.main"]
        times = {}
        
        for mod in modules:
            # Clear cache
            if mod in sys.modules:
                del sys.modules[mod]
            
            start = time.time()
            try:
                importlib.import_module(mod)
                times[mod] = (time.time() - start) * 1000
            except:
                times[mod] = -1
        
        avg_time = sum(t for t in times.values() if t > 0) / len([t for t in times.values() if t > 0])
        
        if avg_time < 500:
            return TestStatus.PASSED, f"Avg: {avg_time:.1f}ms", {"times": times}
        elif avg_time < 2000:
            return TestStatus.WARNING, f"Slow: {avg_time:.1f}ms", {"times": times}
        else:
            return TestStatus.FAILED, f"Very slow: {avg_time:.1f}ms", {"times": times}
    
    run_test("Module Import Speed", TestCategory.PERFORMANCE, test_import_time)
    
    # Test memory usage
    def test_memory():
        try:
            import psutil
            process = psutil.Process()
            mem = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Note: 200-400MB is normal for a full AI assistant with:
            # - Ollama client loaded
            # - ChromaDB connection
            # - Multiple agents initialized
            # - RAG pipeline ready
            if mem < 300:
                return TestStatus.PASSED, f"{mem:.1f} MB", {}
            elif mem < 600:
                return TestStatus.PASSED, f"{mem:.1f} MB (normal for AI app)", {}
            else:
                return TestStatus.WARNING, f"{mem:.1f} MB (high)", {}
        except ImportError:
            return TestStatus.SKIPPED, "psutil not installed", {}
    
    run_test("Memory Usage", TestCategory.PERFORMANCE, test_memory)
    
    # Test disk space
    def test_disk():
        try:
            total, used, free = shutil.disk_usage(PROJECT_ROOT)
            free_gb = free / (1024**3)
            
            if free_gb > 10:
                return TestStatus.PASSED, f"{free_gb:.1f} GB free", {}
            elif free_gb > 1:
                return TestStatus.WARNING, f"{free_gb:.1f} GB free (low)", {}
            else:
                return TestStatus.FAILED, f"{free_gb:.2f} GB free (critical)", {}
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    run_test("Disk Space", TestCategory.PERFORMANCE, test_disk)

# ============================================================================
# CATEGORY 13: SECURITY TESTS
# ============================================================================

def test_security():
    """Test security configurations."""
    log_section("🔒 SECURITY TESTS")
    
    # Check .env file
    def test_env_file():
        env_file = PROJECT_ROOT / ".env"
        env_example = PROJECT_ROOT / ".env.example"
        
        if not env_file.exists():
            return TestStatus.WARNING, ".env not found", {}
        
        content = env_file.read_text(encoding='utf-8')
        
        # Check for sensitive data patterns
        sensitive_patterns = ["sk-", "api_key=", "password=", "secret="]
        found = [p for p in sensitive_patterns if p.lower() in content.lower()]
        
        if found:
            return TestStatus.WARNING, f"Possible secrets: {len(found)}", {}
        
        return TestStatus.PASSED, "No obvious secrets", {}
    
    run_test("Environment File Security", TestCategory.SECURITY, test_env_file)
    
    # Check .gitignore
    def test_gitignore():
        gitignore = PROJECT_ROOT / ".gitignore"
        if not gitignore.exists():
            return TestStatus.FAILED, ".gitignore not found", {}
        
        content = gitignore.read_text(encoding='utf-8')
        # *.py[cod] covers *.pyc, *.pyo, *.pyd
        required = [".env", "venv", "__pycache__", "node_modules"]
        # Check for pyc pattern (either *.pyc or *.py[cod])
        has_pyc = "*.pyc" in content or "*.py[cod]" in content
        missing = [r for r in required if r not in content]
        
        if not missing and has_pyc:
            return TestStatus.PASSED, "All required patterns", {}
        elif not missing:
            return TestStatus.WARNING, "Missing pyc pattern", {}
        else:
            return TestStatus.WARNING, f"Missing: {', '.join(missing)}", {}
    
    run_test("Gitignore Configuration", TestCategory.SECURITY, test_gitignore)
    
    # Check CORS settings
    def test_cors():
        try:
            from core.config import settings
            origins = settings.allowed_origins_list
            
            if "*" in origins:
                return TestStatus.WARNING, "Wildcard CORS enabled", {"origins": origins}
            else:
                return TestStatus.PASSED, f"{len(origins)} origins", {"origins": origins}
        except Exception as e:
            return TestStatus.ERROR, str(e)[:50], {}
    
    run_test("CORS Configuration", TestCategory.SECURITY, test_cors)

# ============================================================================
# CATEGORY 14: INTEGRATION TESTS
# ============================================================================

def test_integration():
    """Test integrated functionality."""
    log_section("🔗 INTEGRATION TESTS")
    
    # Test config loading
    def test_config():
        try:
            from core.config import settings
            attrs = [a for a in dir(settings) if not a.startswith('_')]
            return TestStatus.PASSED, f"{len(attrs)} settings", {"settings": attrs[:10]}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Configuration Loading", TestCategory.INTEGRATION, test_config)
    
    # Test LLM manager
    def test_llm():
        try:
            from core.llm_manager import llm_manager
            status = llm_manager.get_status()
            available = status.get("primary_available", False)
            
            if available:
                return TestStatus.PASSED, "LLM available", {"status": status}
            else:
                return TestStatus.WARNING, "LLM not available", {"status": status}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("LLM Manager", TestCategory.INTEGRATION, test_llm)
    
    # Test session manager
    def test_sessions():
        try:
            from core.session_manager import session_manager
            sessions = session_manager.list_sessions(limit=5)
            return TestStatus.PASSED, f"{len(sessions)} sessions", {}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Session Manager", TestCategory.INTEGRATION, test_sessions)
    
    # Test notes manager
    def test_notes():
        try:
            from core.notes_manager import notes_manager
            notes = notes_manager.list_notes()
            return TestStatus.PASSED, f"{len(notes)} notes", {}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Notes Manager", TestCategory.INTEGRATION, test_notes)
    
    # Test analytics
    def test_analytics():
        try:
            from core.analytics import analytics
            return TestStatus.PASSED, "Analytics ready", {}
        except Exception as e:
            return TestStatus.FAILED, str(e)[:50], {}
    
    run_test("Analytics System", TestCategory.INTEGRATION, test_analytics)

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report():
    """Generate comprehensive test report."""
    report.finalize()
    
    print("\n")
    log_header("📊 COMPREHENSIVE TEST REPORT")
    
    # Summary
    print(f"\n{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
    print(f"{'─'*60}")
    print(f"  Total Tests:  {report.total_tests}")
    print(f"  {Colors.GREEN}Passed:{Colors.RESET}      {report.passed_tests}")
    print(f"  {Colors.RED}Failed:{Colors.RESET}      {report.failed_tests}")
    print(f"  {Colors.YELLOW}Warnings:{Colors.RESET}    {sum(1 for r in report.all_results if r.status == TestStatus.WARNING)}")
    print(f"  {Colors.YELLOW}Skipped:{Colors.RESET}     {sum(1 for r in report.all_results if r.status == TestStatus.SKIPPED)}")
    print(f"  Duration:    {report.duration:.2f}s")
    print(f"  Success Rate: {(report.passed_tests/report.total_tests*100):.1f}%")
    
    # Category breakdown
    print(f"\n{Colors.BOLD}CATEGORY BREAKDOWN{Colors.RESET}")
    print(f"{'─'*60}")
    
    for cat in TestCategory:
        if cat in report.categories:
            cr = report.categories[cat]
            status_icon = "✅" if cr.failed == 0 else "⚠️" if cr.failed < cr.total // 2 else "❌"
            print(f"  {status_icon} {cat.value:25} {cr.passed}/{cr.total} passed")
    
    # Failed tests detail
    failed = [r for r in report.all_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
    if failed:
        print(f"\n{Colors.BOLD}{Colors.RED}FAILED TESTS DETAIL{Colors.RESET}")
        print(f"{'─'*60}")
        for r in failed[:20]:  # Show max 20
            print(f"  {Colors.RED}✗{Colors.RESET} [{r.category.value}] {r.name}")
            print(f"    {r.message}")
    
    # Warnings
    warnings = [r for r in report.all_results if r.status == TestStatus.WARNING]
    if warnings:
        print(f"\n{Colors.BOLD}{Colors.YELLOW}WARNINGS{Colors.RESET}")
        print(f"{'─'*60}")
        for r in warnings[:15]:  # Show max 15
            print(f"  {Colors.YELLOW}⚠{Colors.RESET} [{r.category.value}] {r.name}: {r.message}")
    
    # Frontend comparison special report
    frontend_results = [r for r in report.all_results if r.category == TestCategory.FRONTEND]
    comparison = next((r for r in frontend_results if "Comparison" in r.name), None)
    if comparison and comparison.details:
        print(f"\n{Colors.BOLD}FRONTEND COMPARISON REPORT{Colors.RESET}")
        print(f"{'─'*60}")
        details = comparison.details
        if details.get("only_in_old"):
            print(f"  {Colors.RED}Features in OLD but NOT in NEW:{Colors.RESET}")
            for f in details["only_in_old"]:
                print(f"    • {f}")
        if details.get("only_in_new"):
            print(f"  {Colors.GREEN}Features in NEW but NOT in OLD:{Colors.RESET}")
            for f in details["only_in_new"]:
                print(f"    • {f}")
        if details.get("common"):
            print(f"  {Colors.BLUE}Common features:{Colors.RESET} {len(details['common'])}")
    
    # Save report to file
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "duration_seconds": report.duration,
        "total_tests": report.total_tests,
        "passed": report.passed_tests,
        "failed": report.failed_tests,
        "success_rate": report.passed_tests / report.total_tests * 100 if report.total_tests > 0 else 0,
        "categories": {
            cat.value: {
                "total": cr.total,
                "passed": cr.passed,
                "failed": cr.failed,
                "warnings": cr.warnings,
            }
            for cat, cr in report.categories.items()
        },
        "failed_tests": [
            {"name": r.name, "category": r.category.value, "message": r.message}
            for r in failed
        ],
        "warnings": [
            {"name": r.name, "category": r.category.value, "message": r.message}
            for r in warnings
        ],
    }
    
    report_file = PROJECT_ROOT / "test_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.CYAN}Report saved to: {report_file}{Colors.RESET}")
    
    # Final verdict
    print(f"\n{'='*60}")
    if report.failed_tests == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.RESET}")
    elif report.failed_tests < report.total_tests * 0.1:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ MOSTLY PASSED - {report.failed_tests} issues to fix{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ NEEDS ATTENTION - {report.failed_tests} failures{Colors.RESET}")
    print(f"{'='*60}\n")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main test execution."""
    log_header("🚀 ENTERPRISE AI ASSISTANT - COMPREHENSIVE TEST SUITE")
    print(f"  Project: AgenticManagingSystem")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Root: {PROJECT_ROOT}")
    
    # Run all test categories
    test_core_modules()
    test_api_modules()
    test_agents()
    test_rag_system()
    test_voice_multimodal()
    test_screen_capture()
    test_frontend_comparison()
    test_electron_app()
    test_databases()
    test_tools()
    test_plugins()
    test_performance()
    test_security()
    test_integration()
    
    # Live API tests (optional)
    print("\n")
    run_live = input("Run live API tests? (requires running server) [y/N]: ").strip().lower()
    if run_live == 'y':
        test_api_endpoints_live()
    
    # Generate report
    generate_report()
    
    return 0 if report.failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
