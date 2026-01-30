"""
Kapsamlı Proje Analiz Scripti
=============================
Tüm projeyi kategorize eder ve her kategori için detaylı analiz yapar.
"""

import importlib
import sys
import os
import traceback
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent

# Kategoriler ve modüller
CATEGORIES = {
    "🔌 Backend API": {
        "modules": [
            "api.main",
            "api.websocket_v2",
            "api.agent_endpoints",
            "api.learning_endpoints", 
            "api.learning_journey_endpoints",
            "api.deep_scholar_endpoints",
            "api.premium_endpoints",
            "api.voice_endpoints",
            "api.mcp_endpoints",
            "api.workflow_endpoints",
            "api.security_endpoints",
            "api.knowledge_graph_endpoints",
        ],
        "description": "FastAPI endpoint'leri ve WebSocket"
    },
    "⚙️ Core Modüller": {
        "modules": [
            "core.config",
            "core.llm_manager",
            "core.model_router",
            "core.session_manager",
            "core.vector_store",
            "core.embedding",
            "core.stream_buffer",
            "core.health",
            "core.screen_capture",
            "core.voice_ai",
            "core.code_interpreter",
            "core.knowledge_graph",
            "core.workflow_engine",
        ],
        "description": "Temel sistem modülleri"
    },
    "🤖 Agent Sistemi": {
        "modules": [
            "agents.orchestrator",
            "agents.base_agent",
            "agents.research_agent",
            "agents.writer_agent",
            "agents.analyzer_agent",
            "agents.planning_agent",
            "agents.react_agent",
        ],
        "description": "Multi-agent orkestrasyon"
    },
    "📚 RAG Sistemi": {
        "modules": [
            "rag.unified_orchestrator",
            "rag.reranker",
            "rag.retriever",
            "rag.chunker",
            "rag.hybrid_search",
            "rag.query_expansion",
            "rag.agentic_rag",
        ],
        "description": "Retrieval Augmented Generation"
    },
}


def test_module_import(module_name: str) -> Tuple[bool, str, dict]:
    """Bir modülü import et ve sonucu döndür."""
    try:
        mod = importlib.import_module(module_name)
        
        # Modül bilgilerini topla
        info = {
            "classes": [],
            "functions": [],
            "has_docstring": bool(mod.__doc__),
        }
        
        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if isinstance(obj, type):
                info["classes"].append(name)
            elif callable(obj):
                info["functions"].append(name)
        
        return True, "OK", info
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:80]}", {}


def analyze_python_file(file_path: Path) -> dict:
    """Python dosyasını statik analiz et."""
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        analysis = {
            "total_lines": len(lines),
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "imports": [],
            "classes": [],
            "functions": [],
            "todos": [],
            "fixmes": [],
        }
        
        in_docstring = False
        docstring_char = None
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Blank line
            if not stripped:
                analysis["blank_lines"] += 1
                continue
            
            # Comment
            if stripped.startswith("#"):
                analysis["comment_lines"] += 1
                if "TODO" in stripped.upper():
                    analysis["todos"].append(f"Line {i}: {stripped[:60]}")
                if "FIXME" in stripped.upper():
                    analysis["fixmes"].append(f"Line {i}: {stripped[:60]}")
                continue
            
            # Docstring handling (basic)
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
            
            # Code line
            analysis["code_lines"] += 1
            
            # Import
            if stripped.startswith("import ") or stripped.startswith("from "):
                analysis["imports"].append(stripped[:60])
            
            # Class definition
            if stripped.startswith("class "):
                class_name = stripped.split("(")[0].replace("class ", "").strip(":")
                analysis["classes"].append(class_name)
            
            # Function definition
            if stripped.startswith("def ") or stripped.startswith("async def "):
                func_name = stripped.replace("async ", "").replace("def ", "").split("(")[0]
                analysis["functions"].append(func_name)
        
        return analysis
    except Exception as e:
        return {"error": str(e)}


def run_comprehensive_analysis():
    """Kapsamlı analiz çalıştır."""
    results = {
        "summary": {
            "total_modules": 0,
            "successful_imports": 0,
            "failed_imports": 0,
            "categories": {},
        },
        "categories": {},
        "errors": [],
        "warnings": [],
    }
    
    print("=" * 70)
    print("🔍 KAPSAMLI PROJE ANALİZİ")
    print("=" * 70)
    print()
    
    for category_name, category_info in CATEGORIES.items():
        print(f"\n{category_name}")
        print("-" * 50)
        print(f"📝 {category_info['description']}")
        print()
        
        category_results = {
            "description": category_info["description"],
            "modules": {},
            "stats": {
                "total": len(category_info["modules"]),
                "success": 0,
                "failed": 0,
            }
        }
        
        for module_name in category_info["modules"]:
            success, message, info = test_module_import(module_name)
            results["summary"]["total_modules"] += 1
            
            short_name = module_name.split(".")[-1]
            
            if success:
                category_results["stats"]["success"] += 1
                results["summary"]["successful_imports"] += 1
                
                info_str = ""
                if info.get("classes"):
                    info_str += f" [{len(info['classes'])} class]"
                if info.get("functions"):
                    info_str += f" [{len(info['functions'])} func]"
                
                print(f"  ✓ {short_name}{info_str}")
                category_results["modules"][module_name] = {
                    "status": "OK",
                    "info": info
                }
            else:
                category_results["stats"]["failed"] += 1
                results["summary"]["failed_imports"] += 1
                print(f"  ✗ {short_name}: {message[:50]}")
                category_results["modules"][module_name] = {
                    "status": "FAILED",
                    "error": message
                }
                results["errors"].append({
                    "category": category_name,
                    "module": module_name,
                    "error": message
                })
        
        # Kategori özeti
        stats = category_results["stats"]
        print()
        print(f"  📊 {stats['success']}/{stats['total']} başarılı")
        
        results["categories"][category_name] = category_results
        results["summary"]["categories"][category_name] = {
            "success": stats["success"],
            "total": stats["total"],
            "rate": f"{(stats['success']/stats['total']*100):.0f}%" if stats["total"] > 0 else "N/A"
        }
    
    # Genel özet
    print()
    print("=" * 70)
    print("📊 GENEL ÖZET")
    print("=" * 70)
    
    summary = results["summary"]
    print(f"\nToplam Modül: {summary['total_modules']}")
    print(f"Başarılı: {summary['successful_imports']}")
    print(f"Hatalı: {summary['failed_imports']}")
    print(f"Başarı Oranı: {(summary['successful_imports']/summary['total_modules']*100):.1f}%")
    
    print("\nKategori Bazlı:")
    for cat, stats in summary["categories"].items():
        status_icon = "✓" if stats["success"] == stats["total"] else "⚠️"
        print(f"  {status_icon} {cat}: {stats['rate']} ({stats['success']}/{stats['total']})")
    
    if results["errors"]:
        print()
        print("=" * 70)
        print("❌ HATA DETAYLARI")
        print("=" * 70)
        for err in results["errors"]:
            print(f"\n  {err['module']}:")
            print(f"    {err['error']}")
    
    # Sonuçları kaydet
    output_file = PROJECT_ROOT / "analysis_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Detaylı sonuçlar: {output_file}")
    
    return results


if __name__ == "__main__":
    run_comprehensive_analysis()
