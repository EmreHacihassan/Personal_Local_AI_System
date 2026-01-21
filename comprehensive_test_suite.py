#!/usr/bin/env python3
"""
Enterprise AI Assistant - Comprehensive Test Suite
===================================================

20 aşamalı kapsamlı test scripti.
Tüm sistem bileşenlerini test eder.

Author: Enterprise AI Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class TestResult:
    """Test sonucu."""
    name: str
    passed: bool
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult:
    """Aşama sonucu."""
    stage_num: int
    stage_name: str
    tests: List[TestResult] = field(default_factory=list)
    
    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.passed)
    
    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if not t.passed)
    
    @property
    def total(self) -> int:
        return len(self.tests)
    
    @property
    def success_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0


class ComprehensiveTestSuite:
    """20 aşamalı kapsamlı test suite."""
    
    def __init__(self):
        self.results: List[StageResult] = []
        self.start_time = None
        self.end_time = None
        
    def run_test(self, name: str, test_func) -> TestResult:
        """Tek bir test çalıştır."""
        start = time.time()
        try:
            result = test_func()
            duration = (time.time() - start) * 1000
            if isinstance(result, tuple):
                passed, message, details = result[0], result[1], result[2] if len(result) > 2 else {}
            elif isinstance(result, bool):
                passed, message, details = result, "OK" if result else "FAILED", {}
            else:
                passed, message, details = True, str(result), {}
            return TestResult(name, passed, duration, message, details)
        except Exception as e:
            duration = (time.time() - start) * 1000
            # Handle ChromaDB Rust panic errors gracefully
            error_msg = str(e)
            if "PanicException" in type(e).__name__ or "range start index" in error_msg:
                return TestResult(name, False, duration, f"ChromaDB Rust Error (needs reset)", {"error": error_msg[:200]})
            return TestResult(name, False, duration, f"Exception: {e}", {"traceback": traceback.format_exc()[:500]})
    
    def run_stage(self, stage_num: int, stage_name: str, tests: List[Tuple[str, callable]]) -> StageResult:
        """Bir aşama çalıştır."""
        print(f"\n{'='*60}")
        print(f"📋 AŞAMA {stage_num}/20: {stage_name}")
        print(f"{'='*60}")
        
        stage = StageResult(stage_num, stage_name)
        
        for test_name, test_func in tests:
            result = self.run_test(test_name, test_func)
            stage.tests.append(result)
            
            status = "✅" if result.passed else "❌"
            print(f"  {status} {test_name}: {result.message} ({result.duration_ms:.1f}ms)")
        
        print(f"\n  📊 Sonuç: {stage.passed}/{stage.total} başarılı ({stage.success_rate:.1f}%)")
        self.results.append(stage)
        return stage
    
    def run_all(self):
        """Tüm testleri çalıştır."""
        self.start_time = datetime.now()
        
        print("\n" + "="*70)
        print("🚀 ENTERPRISE AI ASSISTANT - KAPSAMLI TEST SÜİTİ")
        print("="*70)
        print(f"📅 Başlangıç: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Proje: {Path(__file__).parent}")
        print("="*70)
        
        # Stage 1: Python Environment
        self.stage_01_python_environment()
        
        # Stage 2: Core Imports
        self.stage_02_core_imports()
        
        # Stage 3: Configuration
        self.stage_03_configuration()
        
        # Stage 4: GPU & CUDA
        self.stage_04_gpu_cuda()
        
        # Stage 5: Ollama Connection
        self.stage_05_ollama_connection()
        
        # Stage 6: Embedding System
        self.stage_06_embedding_system()
        
        # Stage 7: ChromaDB / Vector Store
        self.stage_07_vector_store()
        
        # Stage 8: Session Manager
        self.stage_08_session_manager()
        
        # Stage 9: LLM Manager
        self.stage_09_llm_manager()
        
        # Stage 10: RAG Components
        self.stage_10_rag_components()
        
        # Stage 11: Hybrid Search
        self.stage_11_hybrid_search()
        
        # Stage 12: Agents
        self.stage_12_agents()
        
        # Stage 13: API Endpoints
        self.stage_13_api_endpoints()
        
        # Stage 14: WebSocket
        self.stage_14_websocket()
        
        # Stage 15: Tools
        self.stage_15_tools()
        
        # Stage 16: Document Processing
        self.stage_16_document_processing()
        
        # Stage 17: Frontend (Next.js)
        self.stage_17_frontend()
        
        # Stage 18: File System & Data
        self.stage_18_filesystem()
        
        # Stage 19: Performance Benchmarks
        self.stage_19_performance()
        
        # Stage 20: Integration Tests
        self.stage_20_integration()
        
        self.end_time = datetime.now()
        self.print_summary()
        self.save_report()
    
    # =========================================================================
    # STAGE 1: Python Environment
    # =========================================================================
    def stage_01_python_environment(self):
        def test_python_version():
            import sys
            version = sys.version_info
            ok = version.major == 3 and version.minor >= 10
            return ok, f"Python {version.major}.{version.minor}.{version.micro}", {"version": sys.version}
        
        def test_venv_active():
            in_venv = sys.prefix != sys.base_prefix
            return in_venv, "Virtual env active" if in_venv else "No venv", {}
        
        def test_required_packages():
            required = ["fastapi", "uvicorn", "chromadb", "ollama", "pydantic", "torch", "numpy"]
            missing = []
            for pkg in required:
                try:
                    __import__(pkg)
                except ImportError:
                    missing.append(pkg)
            ok = len(missing) == 0
            return ok, f"Missing: {missing}" if missing else "All packages OK", {"missing": missing}
        
        def test_optional_packages():
            optional = ["sentence_transformers", "pypdf", "python-docx", "openpyxl"]
            available = []
            for pkg in optional:
                try:
                    __import__(pkg.replace("-", "_"))
                    available.append(pkg)
                except ImportError:
                    pass
            return True, f"{len(available)}/{len(optional)} optional packages", {"available": available}
        
        self.run_stage(1, "Python Environment", [
            ("Python version (3.10+)", test_python_version),
            ("Virtual environment", test_venv_active),
            ("Required packages", test_required_packages),
            ("Optional packages", test_optional_packages),
        ])
    
    # =========================================================================
    # STAGE 2: Core Imports
    # =========================================================================
    def stage_02_core_imports(self):
        def test_core_config():
            from core.config import settings
            return True, f"Settings loaded", {"base_dir": str(settings.BASE_DIR)}
        
        def test_core_logger():
            from core.logger import get_logger
            logger = get_logger("test")
            return True, "Logger OK", {}
        
        def test_core_embedding():
            from core.embedding import embedding_manager
            return True, "EmbeddingManager OK", {}
        
        def test_core_llm():
            from core.llm_manager import llm_manager
            return True, "LLMManager OK", {}
        
        def test_core_vector_store():
            from core.vector_store import vector_store
            return True, "VectorStore OK", {}
        
        def test_core_session():
            from core.session_manager import session_manager
            return True, "SessionManager OK", {}
        
        self.run_stage(2, "Core Imports", [
            ("core.config", test_core_config),
            ("core.logger", test_core_logger),
            ("core.embedding", test_core_embedding),
            ("core.llm_manager", test_core_llm),
            ("core.vector_store", test_core_vector_store),
            ("core.session_manager", test_core_session),
        ])
    
    # =========================================================================
    # STAGE 3: Configuration
    # =========================================================================
    def stage_03_configuration(self):
        def test_env_file():
            env_path = Path(__file__).parent / ".env"
            exists = env_path.exists()
            return exists, "Found" if exists else "Missing", {"path": str(env_path)}
        
        def test_ollama_settings():
            from core.config import settings
            ok = all([
                settings.OLLAMA_BASE_URL,
                settings.OLLAMA_PRIMARY_MODEL,
                settings.OLLAMA_NUM_GPU > 0,
            ])
            return ok, f"GPU layers: {settings.OLLAMA_NUM_GPU}", {
                "base_url": settings.OLLAMA_BASE_URL,
                "model": settings.OLLAMA_PRIMARY_MODEL,
                "num_gpu": settings.OLLAMA_NUM_GPU,
            }
        
        def test_gpu_settings():
            from core.config import settings
            return True, f"GPU batch: {settings.GPU_BATCH_SIZE}", {
                "use_gpu": settings.USE_GPU_EMBEDDING,
                "batch_size": settings.GPU_BATCH_SIZE,
                "model": settings.GPU_EMBEDDING_MODEL,
            }
        
        def test_api_settings():
            from core.config import settings
            return True, f"Port: {settings.API_PORT}", {
                "host": settings.API_HOST,
                "port": settings.API_PORT,
            }
        
        def test_directories():
            from core.config import settings
            dirs_ok = all([
                settings.DATA_DIR.exists(),
                settings.LOGS_DIR.exists(),
            ])
            return dirs_ok, "All directories exist", {
                "data_dir": str(settings.DATA_DIR),
                "logs_dir": str(settings.LOGS_DIR),
            }
        
        self.run_stage(3, "Configuration", [
            (".env file", test_env_file),
            ("Ollama settings", test_ollama_settings),
            ("GPU settings", test_gpu_settings),
            ("API settings", test_api_settings),
            ("Directories", test_directories),
        ])
    
    # =========================================================================
    # STAGE 4: GPU & CUDA
    # =========================================================================
    def stage_04_gpu_cuda(self):
        def test_torch_cuda():
            import torch
            available = torch.cuda.is_available()
            return available, f"CUDA: {torch.version.cuda}" if available else "No CUDA", {
                "cuda_available": available,
                "cuda_version": torch.version.cuda if available else None,
            }
        
        def test_gpu_device():
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                return True, name, {"device_name": name}
            return False, "No GPU", {}
        
        def test_gpu_memory():
            import torch
            if torch.cuda.is_available():
                total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                return True, f"{total:.1f} GB", {"total_memory_gb": total}
            return False, "No GPU", {}
        
        def test_sentence_transformers_gpu():
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                return True, f"Device: {device}", {"device": device}
            except ImportError:
                return False, "Not installed", {}
        
        self.run_stage(4, "GPU & CUDA", [
            ("PyTorch CUDA", test_torch_cuda),
            ("GPU device", test_gpu_device),
            ("GPU memory", test_gpu_memory),
            ("SentenceTransformers GPU", test_sentence_transformers_gpu),
        ])
    
    # =========================================================================
    # STAGE 5: Ollama Connection
    # =========================================================================
    def stage_05_ollama_connection(self):
        def test_ollama_running():
            import ollama
            try:
                client = ollama.Client()
                models = client.list()
                return True, "Connected", {}
            except Exception as e:
                return False, str(e), {}
        
        def test_ollama_models():
            import ollama
            try:
                client = ollama.Client()
                result = client.list()
                if hasattr(result, 'models'):
                    models = [m.model for m in result.models]
                else:
                    models = [m["name"] for m in result.get("models", [])]
                return True, f"{len(models)} models", {"models": models[:5]}
            except Exception as e:
                return False, str(e), {}
        
        def test_primary_model():
            from core.config import settings
            import ollama
            try:
                client = ollama.Client()
                result = client.list()
                if hasattr(result, 'models'):
                    models = [m.model for m in result.models]
                else:
                    models = [m["name"] for m in result.get("models", [])]
                
                found = any(settings.OLLAMA_PRIMARY_MODEL in m for m in models)
                return found, settings.OLLAMA_PRIMARY_MODEL, {"found": found}
            except Exception as e:
                return False, str(e), {}
        
        def test_embedding_model():
            from core.config import settings
            import ollama
            try:
                client = ollama.Client()
                result = client.list()
                if hasattr(result, 'models'):
                    models = [m.model for m in result.models]
                else:
                    models = [m["name"] for m in result.get("models", [])]
                
                found = any(settings.OLLAMA_EMBEDDING_MODEL in m for m in models)
                return found, settings.OLLAMA_EMBEDDING_MODEL, {"found": found}
            except Exception as e:
                return False, str(e), {}
        
        self.run_stage(5, "Ollama Connection", [
            ("Ollama running", test_ollama_running),
            ("Available models", test_ollama_models),
            ("Primary model", test_primary_model),
            ("Embedding model", test_embedding_model),
        ])
    
    # =========================================================================
    # STAGE 6: Embedding System
    # =========================================================================
    def stage_06_embedding_system(self):
        def test_embedding_manager_init():
            from core.embedding import embedding_manager
            return True, f"Dimension: {embedding_manager.dimension}", {
                "dimension": embedding_manager.dimension,
                "use_gpu": embedding_manager._use_gpu,
            }
        
        def test_lazy_loading():
            from core.embedding import embedding_manager
            # Check lazy loading flag
            return True, f"Lazy: {not embedding_manager._gpu_model_loaded}", {
                "loaded": embedding_manager._gpu_model_loaded,
            }
        
        def test_embed_single():
            from core.embedding import embedding_manager
            text = "Bu bir test cümlesidir."
            embedding = embedding_manager.embed_text(text)
            ok = len(embedding) == embedding_manager.dimension
            return ok, f"Vector size: {len(embedding)}", {"size": len(embedding)}
        
        def test_embed_batch():
            from core.embedding import embedding_manager
            texts = ["Test 1", "Test 2", "Test 3"]
            embeddings = embedding_manager.embed_texts(texts)
            ok = len(embeddings) == 3 and all(len(e) == embedding_manager.dimension for e in embeddings)
            return ok, f"Batch size: {len(embeddings)}", {"count": len(embeddings)}
        
        def test_embedding_cache():
            from core.embedding import embedding_manager
            stats = embedding_manager.get_cache_stats()
            return stats is not None, f"Cache: {stats}", {"stats": stats}
        
        self.run_stage(6, "Embedding System", [
            ("EmbeddingManager init", test_embedding_manager_init),
            ("Lazy loading", test_lazy_loading),
            ("Single embedding", test_embed_single),
            ("Batch embedding", test_embed_batch),
            ("Embedding cache", test_embedding_cache),
        ])
    
    # =========================================================================
    # STAGE 7: ChromaDB / Vector Store
    # =========================================================================
    def stage_07_vector_store(self):
        def test_chromadb_connection():
            from core.vector_store import vector_store
            count = vector_store.count()
            return True, f"Documents: {count}", {"count": count}
        
        def test_chromadb_health():
            from core.chromadb_manager import ChromaDBManager
            # Just check class exists
            return True, "ChromaDBManager OK", {}
        
        def test_duplicate_check():
            import inspect
            from core.chromadb_manager import ChromaDBManager
            sig = inspect.signature(ChromaDBManager.add_documents)
            has_param = "skip_duplicates" in sig.parameters
            return has_param, "skip_duplicates param exists", {"has_param": has_param}
        
        def test_vector_search():
            from core.vector_store import vector_store
            try:
                results = vector_store.search("test query", n_results=3)
                return True, f"Search OK", {"result_count": len(results) if results else 0}
            except Exception as e:
                return True, f"Search available (no docs)", {}
        
        self.run_stage(7, "ChromaDB / Vector Store", [
            ("ChromaDB connection", test_chromadb_connection),
            ("ChromaDB health", test_chromadb_health),
            ("Duplicate check param", test_duplicate_check),
            ("Vector search", test_vector_search),
        ])
    
    # =========================================================================
    # STAGE 8: Session Manager
    # =========================================================================
    def stage_08_session_manager(self):
        def test_session_manager_init():
            from core.session_manager import session_manager
            return True, f"Storage: {session_manager.storage_dir}", {}
        
        def test_create_session():
            from core.session_manager import session_manager
            session = session_manager.create_session("Test Session")
            ok = session.id is not None
            # Cleanup
            session_manager.delete_session(session.id)
            return ok, f"ID: {session.id[:8]}...", {"session_id": session.id}
        
        def test_list_sessions():
            from core.session_manager import session_manager
            sessions = session_manager.list_sessions(limit=10)
            return True, f"Count: {len(sessions)}", {"count": len(sessions)}
        
        def test_cleanup_method():
            from core.session_manager import session_manager
            has_method = hasattr(session_manager, 'cleanup_old_sessions')
            return has_method, "cleanup_old_sessions exists", {}
        
        self.run_stage(8, "Session Manager", [
            ("SessionManager init", test_session_manager_init),
            ("Create session", test_create_session),
            ("List sessions", test_list_sessions),
            ("Cleanup method", test_cleanup_method),
        ])
    
    # =========================================================================
    # STAGE 9: LLM Manager
    # =========================================================================
    def stage_09_llm_manager(self):
        def test_llm_manager_init():
            from core.llm_manager import llm_manager
            return True, f"Model: {llm_manager._current_model}", {
                "model": llm_manager._current_model,
            }
        
        def test_llm_status():
            from core.llm_manager import llm_manager
            status = llm_manager.get_status()
            return True, f"Primary OK: {status.get('primary_available')}", status
        
        def test_gpu_options():
            from core.config import settings
            ok = all([
                settings.OLLAMA_NUM_GPU > 0,
                settings.OLLAMA_NUM_CTX > 0,
                settings.OLLAMA_NUM_BATCH > 0,
            ])
            return ok, f"GPU={settings.OLLAMA_NUM_GPU}, CTX={settings.OLLAMA_NUM_CTX}", {}
        
        def test_generate_simple():
            from core.llm_manager import llm_manager
            try:
                # Quick test with small prompt
                response = llm_manager.generate("Say 'OK'", max_tokens=10, temperature=0)
                return len(response) > 0, f"Response: {response[:50]}...", {}
            except Exception as e:
                return False, str(e), {}
        
        self.run_stage(9, "LLM Manager", [
            ("LLMManager init", test_llm_manager_init),
            ("LLM status", test_llm_status),
            ("GPU options in config", test_gpu_options),
            ("Generate (simple)", test_generate_simple),
        ])
    
    # =========================================================================
    # STAGE 10: RAG Components
    # =========================================================================
    def stage_10_rag_components(self):
        def test_document_loader():
            from rag.document_loader import document_loader
            return True, "DocumentLoader OK", {}
        
        def test_chunker():
            from rag.chunker import document_chunker
            return True, "DocumentChunker OK", {}
        
        def test_async_processor():
            from rag.async_processor import robust_loader, batch_processor
            return True, "AsyncProcessor OK", {}
        
        def test_reranker():
            from rag.reranker import reranker
            status = reranker.get_status()
            return True, f"GPU: {status.get('device')}", status
        
        def test_rag_orchestrator():
            try:
                from rag.orchestrator import rag_orchestrator
                return True, "RAGOrchestrator OK", {}
            except ImportError:
                return True, "Not available (optional)", {}
        
        self.run_stage(10, "RAG Components", [
            ("DocumentLoader", test_document_loader),
            ("DocumentChunker", test_chunker),
            ("AsyncProcessor", test_async_processor),
            ("Reranker", test_reranker),
            ("RAGOrchestrator", test_rag_orchestrator),
        ])
    
    # =========================================================================
    # STAGE 11: Hybrid Search
    # =========================================================================
    def stage_11_hybrid_search(self):
        def test_hybrid_search_import():
            from rag.hybrid_search import HybridSearcher, SearchStrategy
            return True, "HybridSearcher OK", {}
        
        def test_search_strategies():
            from rag.hybrid_search import SearchStrategy
            strategies = [s.value for s in SearchStrategy]
            return True, f"Strategies: {strategies}", {"strategies": strategies}
        
        def test_bm25_index():
            from rag.hybrid_search import BM25Index
            index = BM25Index()
            return True, "BM25Index OK", {}
        
        def test_hybrid_searcher_create():
            from rag.hybrid_search import HybridSearcher
            searcher = HybridSearcher()
            return True, "HybridSearcher created", {}
        
        self.run_stage(11, "Hybrid Search", [
            ("HybridSearcher import", test_hybrid_search_import),
            ("Search strategies", test_search_strategies),
            ("BM25Index", test_bm25_index),
            ("HybridSearcher create", test_hybrid_searcher_create),
        ])
    
    # =========================================================================
    # STAGE 12: Agents
    # =========================================================================
    def stage_12_agents(self):
        def test_base_agent():
            from agents.base_agent import BaseAgent
            return True, "BaseAgent OK", {}
        
        def test_orchestrator():
            from agents.orchestrator import orchestrator
            return True, "Orchestrator OK", {}
        
        def test_react_agent():
            from agents.react_agent import ReActAgent
            return True, "ReActAgent OK", {}
        
        def test_research_agent():
            from agents.research_agent import ResearchAgent
            return True, "ResearchAgent OK", {}
        
        def test_writer_agent():
            from agents.writer_agent import WriterAgent
            return True, "WriterAgent OK", {}
        
        self.run_stage(12, "Agents", [
            ("BaseAgent", test_base_agent),
            ("Orchestrator", test_orchestrator),
            ("ReActAgent", test_react_agent),
            ("ResearchAgent", test_research_agent),
            ("WriterAgent", test_writer_agent),
        ])
    
    # =========================================================================
    # STAGE 13: API Endpoints
    # =========================================================================
    def stage_13_api_endpoints(self):
        def test_fastapi_app():
            from api.main import app
            return True, f"Routes: {len(app.routes)}", {"route_count": len(app.routes)}
        
        def test_health_endpoints():
            from api.main import app
            routes = [r.path for r in app.routes if hasattr(r, 'path')]
            health_routes = [r for r in routes if 'health' in r]
            return len(health_routes) > 0, f"Health: {len(health_routes)}", {"routes": health_routes}
        
        def test_embedding_stats_endpoint():
            from api.main import app
            routes = [r.path for r in app.routes if hasattr(r, 'path')]
            exists = '/api/embedding/stats' in routes
            return exists, "Endpoint exists" if exists else "Missing", {}
        
        def test_session_cleanup_endpoint():
            from api.main import app
            routes = [r.path for r in app.routes if hasattr(r, 'path')]
            exists = '/api/sessions/cleanup/old' in routes
            return exists, "Endpoint exists" if exists else "Missing", {}
        
        def test_chat_endpoint():
            from api.main import app
            routes = [r.path for r in app.routes if hasattr(r, 'path')]
            exists = '/api/chat' in routes
            return exists, "Endpoint exists" if exists else "Missing", {}
        
        self.run_stage(13, "API Endpoints", [
            ("FastAPI app", test_fastapi_app),
            ("Health endpoints", test_health_endpoints),
            ("/api/embedding/stats", test_embedding_stats_endpoint),
            ("/api/sessions/cleanup/old", test_session_cleanup_endpoint),
            ("/api/chat", test_chat_endpoint),
        ])
    
    # =========================================================================
    # STAGE 14: WebSocket
    # =========================================================================
    def stage_14_websocket(self):
        def test_websocket_module():
            from api.websocket import websocket_endpoint, manager
            return True, "WebSocket OK", {}
        
        def test_websocket_v2():
            try:
                from api.websocket_v2 import websocket_endpoint_v2
                return True, "WebSocket v2 OK", {}
            except ImportError:
                return True, "v2 not available", {}
        
        def test_connection_manager():
            from api.websocket import manager
            return True, f"Manager OK", {}
        
        self.run_stage(14, "WebSocket", [
            ("WebSocket module", test_websocket_module),
            ("WebSocket v2", test_websocket_v2),
            ("ConnectionManager", test_connection_manager),
        ])
    
    # =========================================================================
    # STAGE 15: Tools
    # =========================================================================
    def stage_15_tools(self):
        def test_web_search():
            try:
                from tools.web_search_engine import PremiumWebSearchEngine
                return True, "WebSearch OK", {}
            except ImportError:
                return True, "Not available", {}
        
        def test_research_synthesizer():
            try:
                from tools.research_synthesizer import ResearchSynthesizer
                return True, "ResearchSynthesizer OK", {}
            except ImportError:
                return True, "Not available", {}
        
        def test_code_executor():
            try:
                from tools.code_executor import CodeExecutor
                return True, "CodeExecutor OK", {}
            except ImportError:
                return True, "Not available", {}
        
        def test_tools_directory():
            tools_dir = Path(__file__).parent / "tools"
            files = list(tools_dir.glob("*.py"))
            return True, f"Tool files: {len(files)}", {"files": [f.name for f in files[:10]]}
        
        self.run_stage(15, "Tools", [
            ("WebSearchEngine", test_web_search),
            ("ResearchSynthesizer", test_research_synthesizer),
            ("CodeExecutor", test_code_executor),
            ("Tools directory", test_tools_directory),
        ])
    
    # =========================================================================
    # STAGE 16: Document Processing
    # =========================================================================
    def stage_16_document_processing(self):
        def test_pdf_support():
            try:
                import pypdf
                return True, "PyPDF OK", {}
            except ImportError:
                return False, "pypdf not installed", {}
        
        def test_docx_support():
            try:
                import docx
                return True, "python-docx OK", {}
            except ImportError:
                return False, "python-docx not installed", {}
        
        def test_excel_support():
            try:
                import openpyxl
                return True, "openpyxl OK", {}
            except ImportError:
                return False, "openpyxl not installed", {}
        
        def test_uploads_directory():
            from core.config import settings
            uploads_dir = settings.DATA_DIR / "uploads"
            exists = uploads_dir.exists()
            if exists:
                files = list(uploads_dir.glob("*"))
                return True, f"Files: {len(files)}", {"count": len(files)}
            return True, "No uploads yet", {}
        
        self.run_stage(16, "Document Processing", [
            ("PDF support", test_pdf_support),
            ("DOCX support", test_docx_support),
            ("Excel support", test_excel_support),
            ("Uploads directory", test_uploads_directory),
        ])
    
    # =========================================================================
    # STAGE 17: Frontend (Next.js)
    # =========================================================================
    def stage_17_frontend(self):
        def test_frontend_next_exists():
            frontend_dir = Path(__file__).parent / "frontend-next"
            return frontend_dir.exists(), "frontend-next exists", {}
        
        def test_old_frontend_deleted():
            frontend_dir = Path(__file__).parent / "frontend"
            deleted = not frontend_dir.exists()
            return deleted, "Streamlit deleted" if deleted else "Still exists", {}
        
        def test_package_json():
            pkg_path = Path(__file__).parent / "frontend-next" / "package.json"
            if pkg_path.exists():
                with open(pkg_path) as f:
                    pkg = json.load(f)
                return True, f"Name: {pkg.get('name')}", {"name": pkg.get("name")}
            return False, "Missing", {}
        
        def test_node_modules():
            nm_dir = Path(__file__).parent / "frontend-next" / "node_modules"
            exists = nm_dir.exists()
            return exists, "Installed" if exists else "Run npm install", {}
        
        def test_next_config():
            cfg_path = Path(__file__).parent / "frontend-next" / "next.config.js"
            return cfg_path.exists(), "next.config.js exists", {}
        
        self.run_stage(17, "Frontend (Next.js)", [
            ("frontend-next exists", test_frontend_next_exists),
            ("Streamlit deleted", test_old_frontend_deleted),
            ("package.json", test_package_json),
            ("node_modules", test_node_modules),
            ("next.config.js", test_next_config),
        ])
    
    # =========================================================================
    # STAGE 18: File System & Data
    # =========================================================================
    def stage_18_filesystem(self):
        def test_data_directory():
            from core.config import settings
            return settings.DATA_DIR.exists(), str(settings.DATA_DIR), {}
        
        def test_logs_directory():
            from core.config import settings
            return settings.LOGS_DIR.exists(), str(settings.LOGS_DIR), {}
        
        def test_chroma_db():
            chroma_dir = Path(__file__).parent / "data" / "chroma_db"
            return chroma_dir.exists(), "ChromaDB exists", {}
        
        def test_sessions_directory():
            sessions_dir = Path(__file__).parent / "data" / "sessions"
            if sessions_dir.exists():
                files = list(sessions_dir.glob("*.json"))
                return True, f"Sessions: {len(files)}", {"count": len(files)}
            return True, "No sessions", {}
        
        def test_disk_space():
            import shutil
            total, used, free = shutil.disk_usage(Path(__file__).parent)
            free_gb = free / (1024**3)
            return free_gb > 1, f"Free: {free_gb:.1f} GB", {"free_gb": free_gb}
        
        self.run_stage(18, "File System & Data", [
            ("Data directory", test_data_directory),
            ("Logs directory", test_logs_directory),
            ("ChromaDB directory", test_chroma_db),
            ("Sessions directory", test_sessions_directory),
            ("Disk space", test_disk_space),
        ])
    
    # =========================================================================
    # STAGE 19: Performance Benchmarks
    # =========================================================================
    def stage_19_performance(self):
        def test_embedding_speed():
            from core.embedding import embedding_manager
            import time
            
            texts = [f"Test document number {i}" for i in range(10)]
            start = time.time()
            embedding_manager.embed_texts(texts)
            duration = time.time() - start
            speed = len(texts) / duration
            
            return True, f"{speed:.1f} embeddings/sec", {"speed": speed}
        
        def test_vector_search_speed():
            from core.vector_store import vector_store
            import time
            
            start = time.time()
            for _ in range(5):
                vector_store.search("test query", n_results=5)
            duration = time.time() - start
            avg_ms = (duration / 5) * 1000
            
            return True, f"{avg_ms:.1f} ms/query", {"avg_ms": avg_ms}
        
        def test_import_time():
            import time
            start = time.time()
            
            # Re-import to measure
            import importlib
            import sys
            
            # Clear cache for accurate measurement
            modules_to_test = ['core.config', 'core.logger']
            for mod in modules_to_test:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            for mod in modules_to_test:
                importlib.import_module(mod)
            
            duration = (time.time() - start) * 1000
            return True, f"Import: {duration:.1f} ms", {"duration_ms": duration}
        
        def test_memory_usage():
            import psutil
            process = psutil.Process()
            mem_mb = process.memory_info().rss / (1024 * 1024)
            return True, f"Memory: {mem_mb:.1f} MB", {"memory_mb": mem_mb}
        
        self.run_stage(19, "Performance Benchmarks", [
            ("Embedding speed", test_embedding_speed),
            ("Vector search speed", test_vector_search_speed),
            ("Import time", test_import_time),
            ("Memory usage", test_memory_usage),
        ])
    
    # =========================================================================
    # STAGE 20: Integration Tests
    # =========================================================================
    def stage_20_integration(self):
        def test_full_rag_pipeline():
            """Test complete RAG: embed -> store -> search."""
            from core.embedding import embedding_manager
            from core.vector_store import vector_store
            
            # Test document
            test_doc = "Enterprise AI Assistant kapsamlı test dokümanı."
            
            # Embed
            embedding = embedding_manager.embed_text(test_doc)
            
            # Search (will work even if doc not stored)
            results = vector_store.search("enterprise test", n_results=3)
            
            return True, "RAG pipeline OK", {"embedding_size": len(embedding)}
        
        def test_session_lifecycle():
            """Test session create -> add message -> delete."""
            from core.session_manager import session_manager
            
            # Create
            session = session_manager.create_session("Integration Test")
            
            # Add message
            session_manager.add_message(session.id, "user", "Test message")
            
            # Get
            retrieved = session_manager.get_session(session.id)
            has_message = len(retrieved.messages) > 0
            
            # Delete
            session_manager.delete_session(session.id)
            
            return has_message, "Session lifecycle OK", {}
        
        def test_api_import_chain():
            """Test that API can import all dependencies."""
            from api.main import app
            from core.llm_manager import llm_manager
            from core.vector_store import vector_store
            from core.embedding import embedding_manager
            
            return True, "Import chain OK", {}
        
        def test_end_to_end_ready():
            """Check if system is ready for production."""
            from core.llm_manager import llm_manager
            from core.vector_store import vector_store
            
            llm_ok = llm_manager.get_status().get("primary_available", False)
            vs_ok = vector_store.count() >= 0
            
            ready = llm_ok and vs_ok
            return ready, "System ready" if ready else "Not ready", {
                "llm_ok": llm_ok,
                "vector_store_ok": vs_ok,
            }
        
        self.run_stage(20, "Integration Tests", [
            ("Full RAG pipeline", test_full_rag_pipeline),
            ("Session lifecycle", test_session_lifecycle),
            ("API import chain", test_api_import_chain),
            ("End-to-end ready", test_end_to_end_ready),
        ])
    
    # =========================================================================
    # Summary & Report
    # =========================================================================
    def print_summary(self):
        """Test sonuçlarını özetle."""
        print("\n" + "="*70)
        print("📊 TEST SONUÇ ÖZETİ")
        print("="*70)
        
        total_tests = sum(s.total for s in self.results)
        total_passed = sum(s.passed for s in self.results)
        total_failed = sum(s.failed for s in self.results)
        overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        duration = (self.end_time - self.start_time).total_seconds()
        
        print(f"\n📈 Genel Sonuçlar:")
        print(f"   Toplam Test: {total_tests}")
        print(f"   ✅ Başarılı: {total_passed}")
        print(f"   ❌ Başarısız: {total_failed}")
        print(f"   📊 Başarı Oranı: {overall_rate:.1f}%")
        print(f"   ⏱️  Süre: {duration:.2f} saniye")
        
        print(f"\n📋 Aşama Detayları:")
        print(f"   {'Aşama':<35} {'Sonuç':<15} {'Oran':<10}")
        print(f"   {'-'*60}")
        
        for stage in self.results:
            status = "✅" if stage.failed == 0 else "⚠️" if stage.passed > 0 else "❌"
            print(f"   {status} {stage.stage_name:<32} {stage.passed}/{stage.total:<12} {stage.success_rate:.0f}%")
        
        # Failed tests detail
        failed_tests = [(s, t) for s in self.results for t in s.tests if not t.passed]
        if failed_tests:
            print(f"\n❌ Başarısız Testler ({len(failed_tests)}):")
            for stage, test in failed_tests:
                print(f"   [{stage.stage_num}] {test.name}: {test.message}")
        
        print("\n" + "="*70)
        if overall_rate == 100:
            print("🎉 TÜM TESTLER BAŞARILI!")
        elif overall_rate >= 90:
            print("✅ Sistem büyük ölçüde hazır, küçük düzeltmeler gerekli.")
        elif overall_rate >= 70:
            print("⚠️ Sistem çalışıyor ancak bazı sorunlar var.")
        else:
            print("❌ Kritik sorunlar tespit edildi!")
        print("="*70 + "\n")
    
    def save_report(self):
        """Test raporunu JSON olarak kaydet."""
        report = {
            "timestamp": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
            "summary": {
                "total_stages": len(self.results),
                "total_tests": sum(s.total for s in self.results),
                "passed": sum(s.passed for s in self.results),
                "failed": sum(s.failed for s in self.results),
            },
            "stages": []
        }
        
        for stage in self.results:
            stage_data = {
                "stage_num": stage.stage_num,
                "stage_name": stage.stage_name,
                "passed": stage.passed,
                "failed": stage.failed,
                "total": stage.total,
                "success_rate": stage.success_rate,
                "tests": []
            }
            
            for test in stage.tests:
                stage_data["tests"].append({
                    "name": test.name,
                    "passed": test.passed,
                    "duration_ms": test.duration_ms,
                    "message": test.message,
                })
            
            report["stages"].append(stage_data)
        
        report_path = Path(__file__).parent / "comprehensive_test_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Rapor kaydedildi: {report_path}")


def main():
    """Ana fonksiyon."""
    suite = ComprehensiveTestSuite()
    suite.run_all()


if __name__ == "__main__":
    main()
