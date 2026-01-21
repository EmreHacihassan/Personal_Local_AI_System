#!/usr/bin/env python3
"""
🔍 Kapsamlı Sistem Analizi ve Test Script'i
==========================================
Bu script tüm projeyi analiz eder, eksik/hatalı bileşenleri tespit eder.

Analiz Kapsamı:
1. Backend API Endpoints
2. Frontend Integration
3. RAG System
4. Learning Module
5. Agents
6. WebSocket
7. MCP Endpoints
8. Database/ChromaDB
9. Configuration
10. Dependencies
"""

import asyncio
import aiohttp
import json
import os
import sys
import importlib
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import subprocess

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {text}{Colors.END}")
    print(f"{Colors.BLUE}{'-'*50}{Colors.END}")

def print_success(text: str):
    print(f"  {Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    print(f"  {Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    print(f"  {Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    print(f"  {Colors.WHITE}ℹ️  {text}{Colors.END}")

# Analysis Results
class AnalysisResult:
    def __init__(self):
        self.total_checks = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.issues: List[Dict[str, Any]] = []
        self.recommendations: List[str] = []
    
    def add_pass(self, component: str, detail: str):
        self.total_checks += 1
        self.passed += 1
        print_success(f"[{component}] {detail}")
    
    def add_fail(self, component: str, detail: str, fix: str = None):
        self.total_checks += 1
        self.failed += 1
        print_error(f"[{component}] {detail}")
        self.issues.append({
            "component": component,
            "issue": detail,
            "fix": fix,
            "severity": "error"
        })
        if fix:
            self.recommendations.append(f"{component}: {fix}")
    
    def add_warning(self, component: str, detail: str, suggestion: str = None):
        self.total_checks += 1
        self.warnings += 1
        print_warning(f"[{component}] {detail}")
        self.issues.append({
            "component": component,
            "issue": detail,
            "fix": suggestion,
            "severity": "warning"
        })
        if suggestion:
            self.recommendations.append(f"{component}: {suggestion}")
    
    def summary(self) -> Dict:
        return {
            "total_checks": self.total_checks,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "success_rate": round(self.passed / self.total_checks * 100, 1) if self.total_checks > 0 else 0,
            "issues": self.issues,
            "recommendations": self.recommendations
        }

result = AnalysisResult()

# ==================== 1. CONFIGURATION CHECK ====================
def check_configuration():
    print_section("1. Configuration Check")
    
    base_path = Path(__file__).parent
    
    # Check .env file
    env_file = base_path / ".env"
    env_example = base_path / ".env.example"
    
    if env_file.exists():
        result.add_pass("Config", ".env file exists")
        
        # Check required env vars
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        required_vars = [
            "OLLAMA_HOST",
            "CHROMA_HOST", 
            "API_HOST",
            "API_PORT",
            "FRONTEND_PORT"
        ]
        
        for var in required_vars:
            if var in env_content:
                result.add_pass("Config", f"{var} is configured")
            else:
                result.add_warning("Config", f"{var} not found in .env", f"Add {var} to .env file")
    else:
        result.add_fail("Config", ".env file missing", "Copy .env.example to .env and configure")
    
    # Check requirements.txt
    req_file = base_path / "requirements.txt"
    if req_file.exists():
        result.add_pass("Config", "requirements.txt exists")
        
        # Check for critical packages
        with open(req_file, 'r') as f:
            requirements = f.read().lower()
        
        critical_packages = ["fastapi", "uvicorn", "chromadb", "langchain", "pydantic"]
        for pkg in critical_packages:
            if pkg in requirements:
                result.add_pass("Config", f"Critical package '{pkg}' in requirements")
            else:
                result.add_fail("Config", f"Critical package '{pkg}' missing", f"Add {pkg} to requirements.txt")
    else:
        result.add_fail("Config", "requirements.txt missing", "Create requirements.txt with dependencies")

# ==================== 2. IMPORT CHECK ====================
def check_imports():
    print_section("2. Python Module Import Check")
    
    base_path = Path(__file__).parent
    sys.path.insert(0, str(base_path))
    
    modules_to_check = [
        ("core.config", "Configuration module"),
        ("core.llm_client", "LLM Client"),
        ("core.vector_store", "Vector Store"),
        ("core.learning_workspace", "Learning Workspace Manager"),
        ("core.learning_advanced_features", "Learning Advanced Features"),
        ("core.study_document_generator", "Study Document Generator"),
        ("core.test_generator", "Test Generator"),
        ("api.main", "API Main"),
        ("api.learning_endpoints", "Learning API Endpoints"),
        ("api.mcp_endpoints", "MCP Endpoints"),
        ("agents.orchestrator", "Agent Orchestrator"),
        ("agents.react_agent", "ReAct Agent"),
        ("rag.retriever", "RAG Retriever"),
        ("rag.reranker", "RAG Reranker"),
    ]
    
    for module_name, description in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            result.add_pass("Import", f"{description} ({module_name})")
        except ImportError as e:
            result.add_fail("Import", f"{description} ({module_name}): {str(e)}", f"Fix import in {module_name}")
        except Exception as e:
            result.add_warning("Import", f"{description} ({module_name}): {str(e)}")

# ==================== 3. API ENDPOINT CHECK ====================
async def check_api_endpoints():
    print_section("3. API Endpoint Check")
    
    base_url = "http://localhost:8001"
    
    endpoints = [
        # Health
        ("GET", "/health", None, "Health Check"),
        ("GET", "/api/health", None, "API Health"),
        
        # Learning Workspaces
        ("GET", "/api/learning/workspaces", None, "List Workspaces"),
        ("POST", "/api/learning/workspaces", {"name": "Test Workspace", "topic": "Test"}, "Create Workspace"),
        
        # RAG
        ("GET", "/api/rag/status", None, "RAG Status"),
        ("GET", "/api/rag/stats", None, "RAG Stats"),
        
        # Documents
        ("GET", "/api/documents", None, "List Documents"),
        
        # Chat
        ("GET", "/api/chat/sessions", None, "List Chat Sessions"),
        
        # System
        ("GET", "/api/system/info", None, "System Info"),
        
        # Learning Stats
        ("GET", "/api/learning/tests/types", None, "Test Types"),
        ("GET", "/api/learning/tests/difficulties", None, "Test Difficulties"),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, endpoint, body, description in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                
                if method == "GET":
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        status = resp.status
                        data = await resp.text()
                elif method == "POST":
                    async with session.post(url, json=body, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        status = resp.status
                        data = await resp.text()
                
                if status in [200, 201]:
                    result.add_pass("API", f"{method} {endpoint} - {description}")
                elif status == 404:
                    result.add_fail("API", f"{method} {endpoint} - Not Found", f"Implement endpoint {endpoint}")
                elif status == 422:
                    result.add_warning("API", f"{method} {endpoint} - Validation Error")
                elif status == 500:
                    result.add_fail("API", f"{method} {endpoint} - Server Error", f"Fix server error in {endpoint}")
                else:
                    result.add_warning("API", f"{method} {endpoint} - Status {status}")
                    
            except aiohttp.ClientConnectorError:
                result.add_fail("API", f"{method} {endpoint} - Connection Failed", "Ensure backend is running on port 8001")
                break  # Stop if server not running
            except asyncio.TimeoutError:
                result.add_warning("API", f"{method} {endpoint} - Timeout")
            except Exception as e:
                result.add_fail("API", f"{method} {endpoint} - {str(e)}")

# ==================== 4. LEARNING MODULE CHECK ====================
async def check_learning_module():
    print_section("4. Learning Module Deep Check")
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        # Create a test workspace
        try:
            async with session.post(
                f"{base_url}/api/learning/workspaces",
                json={"name": f"Analysis Test {datetime.now().isoformat()}", "topic": "System Analysis"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    workspace_id = data.get("workspace", {}).get("id")
                    
                    if workspace_id:
                        result.add_pass("Learning", f"Workspace created: {workspace_id[:8]}...")
                        
                        # Test sources
                        async with session.get(
                            f"{base_url}/api/learning/workspaces/{workspace_id}/sources",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp2:
                            if resp2.status == 200:
                                result.add_pass("Learning", "Sources endpoint working")
                            else:
                                result.add_fail("Learning", "Sources endpoint failed")
                        
                        # Test stats
                        async with session.get(
                            f"{base_url}/api/learning/workspaces/{workspace_id}/stats",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp3:
                            if resp3.status == 200:
                                result.add_pass("Learning", "Stats endpoint working")
                            else:
                                result.add_fail("Learning", "Stats endpoint failed")
                        
                        # Test document creation
                        async with session.post(
                            f"{base_url}/api/learning/workspaces/{workspace_id}/documents",
                            json={
                                "title": "Test Doc",
                                "topic": "Testing",
                                "page_count": 1,
                                "style": "summary"
                            },
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp4:
                            if resp4.status in [200, 201]:
                                result.add_pass("Learning", "Document creation working")
                            else:
                                result.add_fail("Learning", f"Document creation failed: {resp4.status}")
                        
                        # Test visual endpoints
                        visual_test = {
                            "topic": "Python Programming",
                            "content": "Python is a high-level programming language known for its simplicity and readability. It supports multiple paradigms including procedural, object-oriented, and functional programming."
                        }
                        
                        async with session.post(
                            f"{base_url}/api/learning/visual/mindmap",
                            json=visual_test,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as resp5:
                            if resp5.status == 200:
                                data5 = await resp5.json()
                                if data5.get("success"):
                                    result.add_pass("Learning", "Visual mindmap generation working")
                                else:
                                    result.add_warning("Learning", "Visual mindmap returned but success=false")
                            else:
                                result.add_fail("Learning", f"Visual mindmap failed: {resp5.status}")
                        
                        # Cleanup - delete test workspace
                        async with session.delete(
                            f"{base_url}/api/learning/workspaces/{workspace_id}",
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as resp_del:
                            if resp_del.status == 200:
                                result.add_pass("Learning", "Workspace cleanup successful")
                    else:
                        result.add_fail("Learning", "Workspace ID not returned")
                else:
                    result.add_fail("Learning", f"Workspace creation failed: {resp.status}")
                    
        except aiohttp.ClientConnectorError:
            result.add_fail("Learning", "Cannot connect to backend")
        except Exception as e:
            result.add_fail("Learning", f"Learning module check failed: {str(e)}")

# ==================== 5. RAG SYSTEM CHECK ====================
async def check_rag_system():
    print_section("5. RAG System Check")
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        # Check RAG status
        try:
            async with session.get(
                f"{base_url}/api/rag/status",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    result.add_pass("RAG", f"RAG status: {data.get('status', 'unknown')}")
                    
                    doc_count = data.get("document_count", 0)
                    if doc_count > 0:
                        result.add_pass("RAG", f"Documents indexed: {doc_count}")
                    else:
                        result.add_warning("RAG", "No documents indexed", "Upload documents to RAG")
                else:
                    result.add_fail("RAG", f"RAG status check failed: {resp.status}")
            
            # Test query
            async with session.post(
                f"{base_url}/api/rag/query",
                json={"query": "test query", "top_k": 5},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp2:
                if resp2.status == 200:
                    result.add_pass("RAG", "RAG query endpoint working")
                elif resp2.status == 404:
                    result.add_fail("RAG", "RAG query endpoint not found", "Implement /api/rag/query")
                else:
                    result.add_warning("RAG", f"RAG query returned: {resp2.status}")
                    
        except aiohttp.ClientConnectorError:
            result.add_fail("RAG", "Cannot connect to backend")
        except Exception as e:
            result.add_fail("RAG", f"RAG check failed: {str(e)}")

# ==================== 6. CHROMADB CHECK ====================
def check_chromadb():
    print_section("6. ChromaDB Check")
    
    try:
        import chromadb
        result.add_pass("ChromaDB", "chromadb package installed")
        
        # Try to connect
        try:
            from core.config import settings
            chroma_host = getattr(settings, 'CHROMA_HOST', 'localhost')
            chroma_port = getattr(settings, 'CHROMA_PORT', 8002)
            
            client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            collections = client.list_collections()
            result.add_pass("ChromaDB", f"Connected, {len(collections)} collections found")
            
            for coll in collections[:5]:  # Show first 5
                count = coll.count()
                result.add_pass("ChromaDB", f"Collection '{coll.name}': {count} documents")
                
        except Exception as e:
            # Try persistent client
            try:
                base_path = Path(__file__).parent
                chroma_path = base_path / "data" / "chroma_db"
                
                if chroma_path.exists():
                    client = chromadb.PersistentClient(path=str(chroma_path))
                    collections = client.list_collections()
                    result.add_pass("ChromaDB", f"Persistent DB found, {len(collections)} collections")
                else:
                    result.add_warning("ChromaDB", "ChromaDB data directory not found")
            except Exception as e2:
                result.add_warning("ChromaDB", f"Cannot connect to ChromaDB: {str(e2)}")
                
    except ImportError:
        result.add_fail("ChromaDB", "chromadb package not installed", "pip install chromadb")

# ==================== 7. OLLAMA CHECK ====================
async def check_ollama():
    print_section("7. Ollama LLM Check")
    
    ollama_url = "http://localhost:11434"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Check if Ollama is running
            async with session.get(
                f"{ollama_url}/api/tags",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = data.get("models", [])
                    
                    result.add_pass("Ollama", f"Ollama running, {len(models)} models available")
                    
                    for model in models[:5]:
                        result.add_pass("Ollama", f"Model: {model.get('name', 'unknown')}")
                    
                    # Check for required models
                    model_names = [m.get("name", "") for m in models]
                    required_models = ["qwen3", "nomic-embed"]
                    
                    for req in required_models:
                        found = any(req in name for name in model_names)
                        if found:
                            result.add_pass("Ollama", f"Required model '{req}' found")
                        else:
                            result.add_warning("Ollama", f"Model '{req}' not found", f"Run: ollama pull {req}")
                else:
                    result.add_fail("Ollama", f"Ollama API returned: {resp.status}")
                    
        except aiohttp.ClientConnectorError:
            result.add_fail("Ollama", "Ollama not running", "Start Ollama: ollama serve")
        except Exception as e:
            result.add_fail("Ollama", f"Ollama check failed: {str(e)}")

# ==================== 8. FRONTEND CHECK ====================
async def check_frontend():
    print_section("8. Frontend Check")
    
    frontend_url = "http://localhost:3000"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                frontend_url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    result.add_pass("Frontend", "Next.js frontend running on port 3000")
                else:
                    result.add_warning("Frontend", f"Frontend returned: {resp.status}")
                    
        except aiohttp.ClientConnectorError:
            result.add_fail("Frontend", "Frontend not running", "Run: cd frontend-next && npm run dev")
        except Exception as e:
            result.add_fail("Frontend", f"Frontend check failed: {str(e)}")
    
    # Check frontend files
    base_path = Path(__file__).parent
    frontend_path = base_path / "frontend-next"
    
    if frontend_path.exists():
        result.add_pass("Frontend", "frontend-next directory exists")
        
        # Check critical files
        critical_files = [
            "package.json",
            "src/components/pages/LearningPage.tsx",
            "src/app/page.tsx"
        ]
        
        for file in critical_files:
            file_path = frontend_path / file
            if file_path.exists():
                result.add_pass("Frontend", f"File exists: {file}")
            else:
                result.add_fail("Frontend", f"Missing file: {file}")
    else:
        result.add_fail("Frontend", "frontend-next directory missing")

# ==================== 9. WEBSOCKET CHECK ====================
async def check_websocket():
    print_section("9. WebSocket Check")
    
    try:
        import websockets
        result.add_pass("WebSocket", "websockets package installed")
        
        # Try to connect
        try:
            async with websockets.connect(
                "ws://localhost:8001/ws/chat",
                close_timeout=5
            ) as ws:
                result.add_pass("WebSocket", "WebSocket connection successful")
                
                # Send test message
                await ws.send(json.dumps({"type": "ping"}))
                
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    result.add_pass("WebSocket", f"WebSocket response received")
                except asyncio.TimeoutError:
                    result.add_warning("WebSocket", "No response to ping (may be expected)")
                    
        except Exception as e:
            result.add_warning("WebSocket", f"WebSocket connection test: {str(e)}")
            
    except ImportError:
        result.add_warning("WebSocket", "websockets package not installed for testing")

# ==================== 10. FILE STRUCTURE CHECK ====================
def check_file_structure():
    print_section("10. File Structure Check")
    
    base_path = Path(__file__).parent
    
    required_dirs = [
        "api",
        "core",
        "agents",
        "rag",
        "tools",
        "frontend-next",
        "data",
        "logs"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            result.add_pass("Structure", f"Directory exists: {dir_name}/")
        else:
            result.add_warning("Structure", f"Directory missing: {dir_name}/", f"Create directory: mkdir {dir_name}")
    
    # Check for __init__.py files
    python_dirs = ["api", "core", "agents", "rag", "tools"]
    for dir_name in python_dirs:
        init_file = base_path / dir_name / "__init__.py"
        if init_file.exists():
            result.add_pass("Structure", f"{dir_name}/__init__.py exists")
        else:
            result.add_warning("Structure", f"{dir_name}/__init__.py missing", "Create empty __init__.py")

# ==================== 11. CORE MODULES DEEP CHECK ====================
def check_core_modules():
    print_section("11. Core Modules Deep Check")
    
    base_path = Path(__file__).parent
    sys.path.insert(0, str(base_path))
    
    # Check LLM Client
    try:
        from core.llm_client import llm_client
        result.add_pass("Core", "LLM Client imported successfully")
        
        # Check if generate method exists
        if hasattr(llm_client, 'generate'):
            result.add_pass("Core", "LLM Client has 'generate' method")
        else:
            result.add_fail("Core", "LLM Client missing 'generate' method")
            
        if hasattr(llm_client, 'generate_stream'):
            result.add_pass("Core", "LLM Client has 'generate_stream' method")
        else:
            result.add_warning("Core", "LLM Client missing 'generate_stream' method")
            
    except Exception as e:
        result.add_fail("Core", f"LLM Client error: {str(e)}")
    
    # Check Vector Store
    try:
        from core.vector_store import vector_store
        result.add_pass("Core", "Vector Store imported successfully")
        
        if hasattr(vector_store, 'search'):
            result.add_pass("Core", "Vector Store has 'search' method")
        else:
            result.add_fail("Core", "Vector Store missing 'search' method")
            
        if hasattr(vector_store, 'add_documents'):
            result.add_pass("Core", "Vector Store has 'add_documents' method")
        else:
            result.add_warning("Core", "Vector Store missing 'add_documents' method")
            
    except Exception as e:
        result.add_fail("Core", f"Vector Store error: {str(e)}")
    
    # Check Learning Advanced Features
    try:
        from core.learning_advanced_features import get_learning_advanced_features
        features = get_learning_advanced_features()
        result.add_pass("Core", "Learning Advanced Features initialized")
        
        expected_methods = [
            'create_mind_map',
            'create_concept_map',
            'create_timeline',
            'create_flowchart',
            'create_infographic',
            'create_video_script',
            'create_slide_deck',
            'create_podcast_script',
            'create_audio_summary',
            'get_prerequisites',
            'get_related_content',
            'get_learning_path',
            'get_next_topics'
        ]
        
        for method in expected_methods:
            if hasattr(features, method):
                result.add_pass("Core", f"Learning Features has '{method}'")
            else:
                result.add_fail("Core", f"Learning Features missing '{method}'")
                
    except Exception as e:
        result.add_fail("Core", f"Learning Advanced Features error: {str(e)}")

# ==================== 12. AGENT SYSTEM CHECK ====================
def check_agents():
    print_section("12. Agent System Check")
    
    base_path = Path(__file__).parent
    sys.path.insert(0, str(base_path))
    
    agents_to_check = [
        ("agents.orchestrator", "Orchestrator", "AgentOrchestrator"),
        ("agents.react_agent", "ReAct Agent", "ReActAgent"),
        ("agents.analyzer_agent", "Analyzer Agent", "AnalyzerAgent"),
        ("agents.research_agent", "Research Agent", "ResearchAgent"),
        ("agents.writer_agent", "Writer Agent", "WriterAgent"),
        ("agents.planning_agent", "Planning Agent", "PlanningAgent"),
    ]
    
    for module_name, description, class_name in agents_to_check:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                result.add_pass("Agents", f"{description} class exists")
            else:
                result.add_warning("Agents", f"{description} class '{class_name}' not found in module")
        except ImportError as e:
            result.add_fail("Agents", f"{description} import failed: {str(e)}")
        except Exception as e:
            result.add_warning("Agents", f"{description} check error: {str(e)}")

# ==================== MAIN ====================
async def main():
    print_header("🔍 KAPSAMLI SİSTEM ANALİZİ")
    print(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    
    # Run all checks
    check_configuration()
    check_imports()
    await check_api_endpoints()
    await check_learning_module()
    await check_rag_system()
    check_chromadb()
    await check_ollama()
    await check_frontend()
    await check_websocket()
    check_file_structure()
    check_core_modules()
    check_agents()
    
    # Summary
    print_header("📊 ANALİZ SONUÇLARI")
    
    summary = result.summary()
    
    print(f"\n{Colors.BOLD}Toplam Kontrol: {summary['total_checks']}{Colors.END}")
    print(f"{Colors.GREEN}✅ Başarılı: {summary['passed']}{Colors.END}")
    print(f"{Colors.RED}❌ Başarısız: {summary['failed']}{Colors.END}")
    print(f"{Colors.YELLOW}⚠️  Uyarı: {summary['warnings']}{Colors.END}")
    print(f"\n{Colors.BOLD}Başarı Oranı: {summary['success_rate']}%{Colors.END}")
    
    if summary['recommendations']:
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}📋 ÖNERİLER:{Colors.END}")
        for i, rec in enumerate(summary['recommendations'][:20], 1):
            print(f"  {i}. {rec}")
    
    # Save report
    report_path = Path(__file__).parent / "system_analysis_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.CYAN}📄 Rapor kaydedildi: {report_path}{Colors.END}")
    
    return summary

if __name__ == "__main__":
    try:
        summary = asyncio.run(main())
        sys.exit(0 if summary['failed'] == 0 else 1)
    except KeyboardInterrupt:
        print("\n\nAnaliz iptal edildi.")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Kritik Hata: {str(e)}{Colors.END}")
        traceback.print_exc()
        sys.exit(1)
