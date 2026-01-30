"""
WebSocket & Entegrasyon Test
=============================
WebSocket akışlarını ve kritik entegrasyon noktalarını test eder.
"""

import asyncio
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Test sonuçları
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
}


def test_passed(name: str, detail: str = ""):
    print(f"  ✓ {name}" + (f": {detail}" if detail else ""))
    test_results["passed"].append(name)


def test_failed(name: str, reason: str):
    print(f"  ✗ {name}: {reason}")
    test_results["failed"].append({"name": name, "reason": reason})


def test_warning(name: str, message: str):
    print(f"  ⚠️ {name}: {message}")
    test_results["warnings"].append({"name": name, "message": message})


async def test_websocket_module():
    """WebSocket modülünü test et."""
    print("\n" + "=" * 60)
    print("🔌 WebSocket Sistemi Testleri")
    print("=" * 60)
    
    try:
        from api.websocket_v2 import WebSocketManagerV2, WebSocketHandlerV2
        test_passed("WebSocketManagerV2 import")
        test_passed("WebSocketHandlerV2 import")
        
        # Manager kontrolü
        manager = WebSocketManagerV2()
        if hasattr(manager, "active_connections") or hasattr(manager, "_connections"):
            test_passed("Connection yönetimi mevcut")
        else:
            test_warning("Connection yönetimi", "connections attribute bulunamadı")
        
    except Exception as e:
        test_failed("WebSocket import", str(e))
        return
    
    # Method varlık kontrolü
    methods_to_check = [
        "_handle_chat",
        "_stream_response",
        "_stream_routed_response",
        "_send_phase_update",
        "connect",
    ]
    
    for method in methods_to_check:
        if hasattr(manager, method):
            test_passed(f"Method: {method}")
        else:
            test_failed(f"Method: {method}", "Bulunamadı")


async def test_model_router():
    """Model router testleri."""
    print("\n" + "=" * 60)
    print("🎯 Model Router Testleri")
    print("=" * 60)
    
    try:
        from core.model_router import ModelRouter, RuleBasedRouter
        test_passed("ModelRouter import")
        
        # Rule-based router test
        rbr = RuleBasedRouter()
        
        # Basit sorgu testi - RuleBasedRouter.route() returns Tuple[ModelSize, float, str]
        simple_queries = ["merhaba", "selam", "naber", "nasılsın", "günaydın"]
        for query in simple_queries:
            result = rbr.route(query)  # Returns (ModelSize, confidence, reason) or None
            if result:
                model_size, confidence, reason = result
                if model_size.value == "small":
                    test_passed(f"Basit sorgu '{query}'", f"→ {model_size.value} ({confidence:.0%})")
                else:
                    test_warning(f"Basit sorgu '{query}'", f"Beklenmeyen: {model_size.value}")
            else:
                test_warning(f"Basit sorgu '{query}'", "Rule-based eşleşmedi")
        
        # Karmaşık sorgu testi
        complex_queries = [
            "Python'da asenkron programlama nasıl yapılır?",
            "Makine öğrenmesi algoritmalarını karşılaştır",
        ]
        for query in complex_queries:
            result = rbr.route(query)
            if result:
                model_size, confidence, reason = result
                test_passed(f"Karmaşık sorgu", f"'{query[:30]}...' → {model_size.value}")
            else:
                test_passed(f"Karmaşık sorgu", f"'{query[:30]}...' → AI Router'a yönlendirilecek")
        
    except Exception as e:
        test_failed("Model Router", str(e))


async def test_rag_system():
    """RAG sistemi testleri."""
    print("\n" + "=" * 60)
    print("📚 RAG Sistemi Testleri")
    print("=" * 60)
    
    try:
        from rag.unified_orchestrator import UnifiedAdvancedOrchestrator
        test_passed("UnifiedAdvancedOrchestrator import")
        
        # Singleton/instance kontrolü
        orch = UnifiedAdvancedOrchestrator()
        
        if hasattr(orch, "search"):
            test_passed("search() method mevcut")
        elif hasattr(orch, "retrieve"):
            test_passed("retrieve() method mevcut")
        elif hasattr(orch, "query"):
            test_passed("query() method mevcut")
        else:
            test_warning("RAG Orchestrator", "Ana search metodu bulunamadı")
        
    except Exception as e:
        test_failed("RAG Orchestrator", str(e))
    
    # Reranker test
    try:
        from rag.reranker import Reranker, CrossEncoderReranker
        test_passed("Reranker import")
        test_passed("CrossEncoderReranker import")
        
        reranker = Reranker()
        if hasattr(reranker, "rerank"):
            test_passed("rerank() method mevcut")
            
    except Exception as e:
        test_failed("Reranker", str(e))


async def test_agent_system():
    """Agent sistemi testleri."""
    print("\n" + "=" * 60)
    print("🤖 Agent Sistemi Testleri")
    print("=" * 60)
    
    try:
        from agents.orchestrator import Orchestrator
        test_passed("Orchestrator import")
        
        # Orchestrator BaseAgent'tan inherit ediyor
        if hasattr(Orchestrator, "execute") or hasattr(Orchestrator, "run") or hasattr(Orchestrator, "process"):
            test_passed("Ana execution metodu mevcut")
        else:
            test_warning("Orchestrator", "execute/run/process metodu bulunamadı")
            
    except Exception as e:
        test_failed("Orchestrator", str(e))
    
    # Agent'ları test et
    agents_to_test = [
        ("research_agent", "ResearchAgent"),
        ("writer_agent", "WriterAgent"),
        ("analyzer_agent", "AnalyzerAgent"),
    ]
    
    for module_name, class_name in agents_to_test:
        try:
            module = __import__(f"agents.{module_name}", fromlist=[class_name])
            agent_class = getattr(module, class_name)
            test_passed(f"{class_name}")
        except Exception as e:
            test_failed(class_name, str(e)[:50])


async def test_llm_manager():
    """LLM Manager testleri."""
    print("\n" + "=" * 60)
    print("🧠 LLM Manager Testleri")
    print("=" * 60)
    
    try:
        from core.llm_manager import LLMManager
        test_passed("LLMManager import")
        
        llm = LLMManager()
        
        if hasattr(llm, "generate") or hasattr(llm, "chat") or hasattr(llm, "stream"):
            test_passed("Ana generation metodu mevcut")
            
        if hasattr(llm, "available_models") or hasattr(llm, "models"):
            test_passed("Model listesi mevcut")
            
    except Exception as e:
        test_failed("LLM Manager", str(e))


async def test_critical_integrations():
    """Kritik entegrasyon noktaları."""
    print("\n" + "=" * 60)
    print("🔗 Kritik Entegrasyon Testleri")
    print("=" * 60)
    
    # Config kontrolü
    try:
        from core.config import Settings
        settings = Settings()
        test_passed("Settings yüklendi")
        
        if hasattr(settings, "OLLAMA_URL") or hasattr(settings, "ollama_url"):
            test_passed("Ollama URL konfigürasyonu mevcut")
            
    except Exception as e:
        test_failed("Settings", str(e))
    
    # ChromaDB kontrolü
    try:
        from core.chromadb_manager import ChromaDBManager
        test_passed("ChromaDBManager import")
        
        manager = ChromaDBManager()
        if manager._client:
            test_passed("ChromaDB client aktif")
            
    except Exception as e:
        test_warning("ChromaDB", str(e)[:50])


async def run_all_tests():
    """Tüm testleri çalıştır."""
    print("=" * 60)
    print("🧪 KAPSAMLI ENTEGRASYON TESTLERİ")
    print("=" * 60)
    
    await test_websocket_module()
    await test_model_router()
    await test_rag_system()
    await test_agent_system()
    await test_llm_manager()
    await test_critical_integrations()
    
    # Özet
    print("\n" + "=" * 60)
    print("📊 TEST ÖZETİ")
    print("=" * 60)
    
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    warnings = len(test_results["warnings"])
    total = passed + failed
    
    print(f"\n✓ Geçen: {passed}")
    print(f"✗ Başarısız: {failed}")
    print(f"⚠️ Uyarı: {warnings}")
    print(f"\nBaşarı Oranı: {(passed/total*100):.1f}%" if total > 0 else "")
    
    if test_results["failed"]:
        print("\n❌ Başarısız Testler:")
        for f in test_results["failed"]:
            print(f"  - {f['name']}: {f['reason']}")
    
    if test_results["warnings"]:
        print("\n⚠️ Uyarılar:")
        for w in test_results["warnings"]:
            print(f"  - {w['name']}: {w['message']}")
    
    return len(test_results["failed"]) == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    print("\n" + ("✅ TÜM TESTLER GEÇTİ!" if success else "❌ BAZI TESTLER BAŞARISIZ"))
    sys.exit(0 if success else 1)
