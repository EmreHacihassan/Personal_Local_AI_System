"""
🧠 Enterprise AI Assistant - System Self-Knowledge
==================================================

Bu modül, AI asistanın kendi teknik mimarisi, özellikleri ve 
yetenekleri hakkında bilgi sahibi olmasını sağlar.

Kullanım:
    from core.system_knowledge import SYSTEM_KNOWLEDGE, get_capability_info
    
    # Tüm bilgiyi al
    info = SYSTEM_KNOWLEDGE
    
    # Belirli bir özellik hakkında bilgi al
    mcp_info = get_capability_info("mcp")
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================================
# SYSTEM VERSION & METADATA
# ============================================================================

SYSTEM_VERSION = "2.2.0"
SYSTEM_NAME = "Enterprise AI Assistant"
SYSTEM_CODENAME = "AgenticManagingSystem"
BUILD_DATE = "2026-01-12"
ARCHITECTURE_VERSION = "v2.2 Enterprise Performance & Quality Overhaul"


# ============================================================================
# COMPLETE SYSTEM KNOWLEDGE BASE
# ============================================================================

SYSTEM_KNOWLEDGE: Dict[str, Any] = {
    
    # ========== GENEL BİLGİLER ==========
    "identity": {
        "name": "Enterprise AI Assistant",
        "version": SYSTEM_VERSION,
        "codename": SYSTEM_CODENAME,
        "description": "Endüstri standartlarında, tam yerel çalışan kurumsal AI asistan sistemi",
        "architecture": "Multi-Agent RAG-Enhanced LLM System",
        "deployment": "Local-first (Ollama + ChromaDB)",
        "languages": ["Türkçe", "English"],
        "creator": "Custom Enterprise Solution",
        "last_update": BUILD_DATE,
    },
    
    # ========== TEMEL MİMARİ ==========
    "architecture": {
        "description": """
Enterprise AI Assistant, modüler ve ölçeklenebilir bir mimari üzerine kurulmuştur.
Sistem, birden fazla katmandan oluşur ve her katman belirli sorumlulukları yerine getirir.
        """,
        "layers": {
            "frontend": {
                "name": "Streamlit Web UI",
                "technology": "Streamlit 1.x",
                "port": 8501,
                "features": [
                    "Modern responsive tasarım",
                    "Real-time streaming chat",
                    "Döküman yükleme ve yönetimi",
                    "Session geçmişi",
                    "Not alma sistemi",
                    "Tema desteği (Klasik, Gece, Okyanus, Orman, vb.)",
                    "Klavye kısayolları",
                ],
            },
            "api": {
                "name": "FastAPI Backend",
                "technology": "FastAPI + Uvicorn",
                "port": 8000,
                "features": [
                    "RESTful API endpoints",
                    "WebSocket real-time streaming",
                    "OpenAPI/Swagger dokümantasyonu",
                    "CORS middleware",
                    "Rate limiting",
                    "Health checks",
                ],
            },
            "core": {
                "name": "Core Processing Engine",
                "description": "Ana işleme motoru - LLM, embedding, vektör veritabanı yönetimi",
                "modules": [
                    "LLM Manager",
                    "Embedding Manager", 
                    "Vector Store",
                    "Session Manager",
                    "Cache System",
                    "Guardrails",
                ],
            },
            "agents": {
                "name": "Multi-Agent System",
                "description": "Uzmanlaşmış AI agent'lar",
                "agent_types": [
                    "Orchestrator",
                    "Research Agent",
                    "Writer Agent",
                    "Analyzer Agent",
                    "Assistant Agent",
                    "ReAct Agent",
                ],
            },
            "rag": {
                "name": "RAG Pipeline",
                "description": "Retrieval-Augmented Generation sistemi",
                "components": [
                    "Document Loader",
                    "Chunker",
                    "Retriever",
                    "Reranker",
                    "Query Expansion",
                    "Hybrid Search",
                ],
            },
            "tools": {
                "name": "Tool System",
                "description": "Agent'ların kullandığı araçlar",
                "available_tools": [
                    "Web Search",
                    "Calculator",
                    "Code Executor",
                    "File Operations",
                    "RAG Query",
                ],
            },
        },
        "data_flow": """
1. Kullanıcı → Frontend (Streamlit) → API (FastAPI)
2. API → Orchestrator → Uygun Agent seçimi
3. Agent → Tool kullanımı (gerekirse)
4. Agent → RAG sorgusu (bilgi gerekirse)
5. Agent → LLM çağrısı (yanıt üretimi)
6. LLM yanıtı → Guardrails (güvenlik kontrolü)
7. Yanıt → API → Frontend → Kullanıcı
        """,
    },
    
    # ========== MCP (Model Context Protocol) ==========
    "mcp": {
        "name": "Model Context Protocol",
        "version": "2024-11-05 (v2024.1)",
        "description": """
MCP (Model Context Protocol), Anthropic tarafından geliştirilen standart bir protokoldür.
AI asistanların dış kaynaklara, araçlara ve servislere bağlanmasını sağlar.
Bu sistemde MCP, endüstri standardı bir arayüz olarak implement edilmiştir.
        """,
        "implementation_file": "core/mcp_server.py",
        "provider_file": "core/mcp_providers.py",
        
        "features": {
            "resources": {
                "description": "Dökümanlar, RAG chunks ve session'ları MCP kaynağı olarak expose eder",
                "capabilities": [
                    "document://uploads/* - Yüklenen dökümanlar",
                    "document://indexed/* - İndekslenmiş RAG chunks",
                    "session://* - Chat session'ları",
                    "note://* - Kullanıcı notları",
                ],
            },
            "tools": {
                "description": "AI'ın kullanabileceği araçları MCP tool olarak sunar",
                "available": [
                    "web_search - Web araması yapar",
                    "calculate - Matematiksel hesaplamalar",
                    "rag_query - Döküman tabanında arama",
                    "file_read - Dosya okuma",
                    "file_write - Dosya yazma",
                    "code_execute - Python kodu çalıştırma (sandbox)",
                ],
            },
            "prompts": {
                "description": "Sistem promptlarını MCP üzerinden yönetir",
                "templates": [
                    "chat_assistant - Genel sohbet promptu",
                    "research_mode - Araştırma modu promptu",
                    "code_helper - Kod yardımı promptu",
                    "document_qa - Döküman soru-cevap promptu",
                ],
            },
            "sampling": {
                "description": "LLM generation'ı MCP üzerinden yapabilme",
                "model": "Ollama üzerinden konfigüre edilen model",
            },
        },
        
        "protocol_compliance": {
            "json_rpc": "2.0",
            "transport": "stdio, HTTP, WebSocket",
            "methods": [
                "initialize / initialized",
                "resources/list, resources/read",
                "tools/list, tools/call",
                "prompts/list, prompts/get",
                "sampling/createMessage",
                "notifications/progress",
            ],
        },
        
        "use_cases": [
            "Claude Desktop ile entegrasyon",
            "Cursor IDE ile entegrasyon", 
            "VS Code Copilot ile entegrasyon",
            "Diğer MCP-uyumlu client'lar",
        ],
        
        "benefits": [
            "Standart protokol - farklı AI sistemleriyle uyumluluk",
            "Güvenli kaynak erişimi",
            "Tool kullanımı için tek arayüz",
            "Kolay genişletilebilirlik",
        ],
    },
    
    # ========== LLM MANAGER ==========
    "llm_manager": {
        "name": "LLM Manager",
        "file": "core/llm_manager.py",
        "description": """
Ollama tabanlı yerel LLM yönetim sistemi. Model seçimi, failover ve streaming desteği sağlar.
        """,
        "features": {
            "model_management": {
                "primary_model": "qwen2.5:7b (varsayılan)",
                "backup_model": "llama3.2:3b (failover)",
                "supported_models": [
                    "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",
                    "llama3.2:3b", "llama3.1:8b", "llama3.1:70b",
                    "mistral:7b", "mixtral:8x7b",
                    "phi3:14b", "gemma2:9b",
                    "deepseek-coder:6.7b",
                ],
            },
            "token_management": {
                "token_counting": "Model bazlı yaklaşık token hesaplama",
                "context_window": "Model'e göre dinamik (8K - 128K token)",
                "auto_truncation": "Context aşımında otomatik kırpma",
            },
            "reliability": {
                "retry_strategy": "Exponential backoff (3 deneme)",
                "failover": "Primary model başarısız olursa backup'a geç",
                "timeout": "Konfigüre edilebilir timeout",
            },
            "streaming": {
                "token_streaming": "Gerçek zamanlı token akışı",
                "chunk_streaming": "Chunk bazlı streaming",
                "progress_tracking": "İlerleme takibi",
            },
            "caching": {
                "response_cache": "SQLite-backed LLM yanıt cache",
                "semantic_matching": "Benzer sorgular için cache hit",
                "ttl": "Konfigüre edilebilir cache süresi",
            },
        },
    },
    
    # ========== EMBEDDING SYSTEM ==========
    "embedding": {
        "name": "Embedding Manager",
        "file": "core/embedding.py",
        "description": """
Ollama tabanlı embedding üretim sistemi. Döküman ve sorgu vektörizasyonu.
        """,
        "model": "nomic-embed-text (varsayılan)",
        "dimension": 768,
        "features": {
            "batch_processing": "Tek API çağrısında çoklu embedding",
            "caching": "Thread-safe LRU cache (2000 giriş)",
            "parallel_processing": "Büyük döküman setleri için paralel işleme",
            "normalization": "L2 normalization",
            "retry": "Otomatik retry on failure",
        },
        "performance": {
            "cache_size": 2000,
            "batch_size": 50,
            "parallel_workers": 4,
        },
    },
    
    # ========== VECTOR STORE ==========
    "vector_store": {
        "name": "Vector Store",
        "file": "core/vector_store.py",
        "database": "ChromaDB",
        "description": """
ChromaDB tabanlı vektör veritabanı. Semantic search ve döküman yönetimi.
        """,
        "features": {
            "semantic_search": "Cosine similarity tabanlı arama",
            "metadata_filtering": "Metadata bazlı filtreleme",
            "batch_operations": "Toplu ekleme/silme",
            "persistence": "Disk'e kalıcı kayıt",
            "page_retrieval": "Sayfa bazlı sonuç getirme",
        },
        "storage": {
            "location": "data/chroma_db/",
            "collection": "documents",
            "index_type": "HNSW (Hierarchical Navigable Small World)",
        },
    },
    
    # ========== RAG PIPELINE ==========
    "rag": {
        "name": "RAG Pipeline",
        "description": """
Retrieval-Augmented Generation - Döküman tabanlı bilgi getirme ve yanıt üretme.
        """,
        "components": {
            "document_loader": {
                "file": "rag/document_loader.py",
                "supported_formats": [
                    ".pdf", ".docx", ".doc",
                    ".txt", ".md", ".json",
                    ".csv", ".xlsx", ".xls",
                    ".html", ".xml",
                    ".py", ".js", ".ts", ".java", ".cpp",
                ],
                "features": ["OCR desteği", "Metadata çıkarma", "Encoding detection"],
            },
            "chunker": {
                "file": "rag/chunker.py",
                "strategies": [
                    "Fixed size chunking",
                    "Semantic chunking", 
                    "Sentence-based chunking",
                    "Paragraph-based chunking",
                    "Recursive character splitting",
                ],
                "default_chunk_size": 512,
                "default_overlap": 50,
            },
            "retriever": {
                "file": "rag/retriever.py",
                "methods": [
                    "Dense retrieval (embedding similarity)",
                    "Sparse retrieval (BM25)",
                    "Hybrid retrieval (Dense + Sparse)",
                ],
                "default_top_k": 5,
            },
            "reranker": {
                "file": "rag/reranker.py",
                "strategies": [
                    "BM25 reranking",
                    "Cross-encoder reranking",
                    "RRF (Reciprocal Rank Fusion)",
                    "Custom scoring",
                ],
            },
            "query_expansion": {
                "file": "rag/query_expansion.py",
                "techniques": [
                    "Synonym expansion",
                    "HyDE (Hypothetical Document Embeddings)",
                    "Multi-query generation",
                    "Step-back prompting",
                ],
            },
            "hybrid_search": {
                "file": "rag/hybrid_search.py",
                "description": "Dense + Sparse retrieval kombinasyonu",
                "fusion_method": "RRF (Reciprocal Rank Fusion)",
            },
        },
        "advanced_features": {
            "crag": {
                "name": "Corrective RAG",
                "file": "core/crag_system.py",
                "description": "Self-correcting RAG with relevance grading and hallucination detection",
                "features": [
                    "Relevance grading (highly_relevant, relevant, partially_relevant, not_relevant)",
                    "Query reformulation on low relevance",
                    "Web search fallback",
                    "Hallucination detection",
                    "Iterative refinement",
                ],
            },
            "graph_rag": {
                "name": "Graph RAG",
                "file": "core/graph_rag.py",
                "description": "Knowledge Graph destekli RAG",
                "features": [
                    "Entity extraction",
                    "Relationship detection",
                    "Subgraph expansion",
                    "Cypher query generation",
                ],
            },
        },
    },
    
    # ========== MULTI-AGENT SYSTEM ==========
    "agents": {
        "name": "Multi-Agent System",
        "description": """
Uzmanlaşmış AI agent'ların koordineli çalışması. Her agent belirli görevlerde uzmanlaşmıştır.
        """,
        "orchestrator": {
            "file": "agents/orchestrator.py",
            "role": "Merkez yönetici - görev analizi ve agent routing",
            "capabilities": [
                "Görev analizi ve sınıflandırma",
                "Uygun agent seçimi",
                "Çoklu agent koordinasyonu",
                "Sonuç birleştirme",
            ],
        },
        "agent_types": {
            "research_agent": {
                "file": "agents/research_agent.py",
                "specialty": "Bilgi arama, kaynak bulma, araştırma",
                "tools": ["web_search", "rag_query"],
            },
            "writer_agent": {
                "file": "agents/writer_agent.py",
                "specialty": "İçerik yazma, email, rapor, makale",
                "capabilities": ["Ton ayarlama", "Format seçimi", "Uzunluk kontrolü"],
            },
            "analyzer_agent": {
                "file": "agents/analyzer_agent.py",
                "specialty": "Veri analizi, karşılaştırma, özet çıkarma",
                "capabilities": ["Sayısal analiz", "Trend tespiti", "Rapor oluşturma"],
            },
            "assistant_agent": {
                "file": "agents/assistant_agent.py",
                "specialty": "Genel sorular, günlük yardım, sohbet",
                "capabilities": ["Doğal diyalog", "Bağlam takibi", "Kişiselleştirme"],
            },
            "react_agent": {
                "file": "agents/react_agent.py",
                "specialty": "ReAct (Reasoning + Acting) pattern",
                "description": "Thought → Action → Observation döngüsü",
                "capabilities": [
                    "Chain-of-Thought reasoning",
                    "Tool kullanımı",
                    "Şeffaf düşünce süreci",
                    "Iteratif problem çözme",
                ],
            },
        },
        "advanced_features": {
            "self_reflection": {
                "file": "agents/self_reflection.py",
                "description": "Agent çıktılarının kalite değerlendirmesi",
                "capabilities": [
                    "Self-critique (öz eleştiri)",
                    "Hallucination detection",
                    "Fact verification",
                    "Quality scoring",
                    "Iterative refinement",
                ],
            },
            "multi_agent_debate": {
                "file": "core/multi_agent_debate.py",
                "description": "Birden fazla agent'ın tartışarak daha iyi yanıt üretmesi",
                "roles": [
                    "Proponent - Pozisyonu savunan",
                    "Opponent - Karşı çıkan",
                    "Critic - Eleştiren",
                    "Synthesizer - Birleştiren",
                    "Judge - Değerlendiren",
                ],
            },
            "langgraph_orchestration": {
                "file": "core/langgraph_orchestration.py",
                "description": "State machine tabanlı agent akış yönetimi",
                "features": [
                    "State graph tanımlaması",
                    "Conditional routing",
                    "Parallel execution",
                    "Human-in-the-loop",
                    "Checkpoint/resume",
                ],
            },
        },
    },
    
    # ========== TOOL SYSTEM ==========
    "tools": {
        "name": "Tool System",
        "description": """
Agent'ların dış dünya ile etkileşim kurmasını sağlayan araç sistemi.
        """,
        "base_file": "tools/base_tool.py",
        "manager_file": "tools/tool_manager.py",
        "available_tools": {
            "web_search": {
                "file": "tools/web_search_tool.py",
                "description": "DuckDuckGo tabanlı web araması",
                "features": [
                    "Instant answers",
                    "Web search",
                    "News search",
                    "Region ve dil filtresi",
                ],
            },
            "calculator": {
                "file": "tools/calculator_tool.py",
                "description": "Matematiksel hesaplamalar",
                "capabilities": [
                    "Aritmetik işlemler",
                    "Trigonometri",
                    "İstatistik",
                    "Birim dönüşümleri",
                ],
            },
            "code_executor": {
                "file": "tools/code_executor_tool.py",
                "description": "Python kodu çalıştırma (sandbox)",
                "security": [
                    "AST analizi ile güvenlik kontrolü",
                    "Yasaklı modül/fonksiyon listesi",
                    "Timeout limiti",
                    "Bellek limiti",
                ],
            },
            "file_operations": {
                "file": "tools/file_operations_tool.py",
                "description": "Dosya okuma/yazma işlemleri",
                "operations": ["read", "write", "list", "search"],
            },
            "rag_tool": {
                "file": "tools/rag_tool.py",
                "description": "Döküman tabanında arama",
            },
        },
        "mcp_integration": {
            "file": "tools/mcp_integration.py",
            "description": "MCP üzerinden tool kullanımı",
            "components": ["MCPHub", "LocalMCPServer", "RemoteMCPServer"],
        },
    },
    
    # ========== SECURITY & GUARDRAILS ==========
    "security": {
        "name": "Security & Guardrails",
        "description": """
Input/Output güvenlik kontrolü, içerik filtreleme ve güvenlik önlemleri.
        """,
        "components": {
            "input_guard": {
                "file": "core/guardrails.py",
                "protections": [
                    "Prompt injection detection",
                    "PII (Personal Identifiable Information) detection",
                    "Profanity filter",
                    "Content length limits",
                ],
                "patterns_detected": [
                    "TC Kimlik numarası",
                    "Email adresleri",
                    "Telefon numaraları",
                    "Kredi kartı numaraları",
                    "IBAN numaraları",
                ],
            },
            "output_guard": {
                "file": "core/guardrails.py",
                "protections": [
                    "Harmful content filtering",
                    "Hallucination warnings",
                    "Source verification",
                ],
            },
            "advanced_guardrails": {
                "file": "core/advanced_guardrails.py",
                "features": [
                    "Multi-layer filtering",
                    "Context-aware filtering",
                    "Custom rule engine",
                ],
            },
        },
        "levels": ["LOW", "MEDIUM", "HIGH", "STRICT"],
    },
    
    # ========== CACHING SYSTEM ==========
    "caching": {
        "name": "Two-Tier Caching System",
        "file": "core/cache.py",
        "description": """
L1 (In-memory) + L2 (SQLite) iki katmanlı cache sistemi.
        """,
        "tiers": {
            "l1_cache": {
                "type": "In-memory LRU",
                "max_size": 500,
                "max_memory": "100 MB",
                "features": ["Thread-safe", "LRU eviction", "Fast access"],
            },
            "l2_cache": {
                "type": "SQLite persistent",
                "features": ["Disk persistence", "TTL support", "Connection pooling"],
            },
        },
        "cache_targets": [
            "LLM responses",
            "Embeddings",
            "Search results",
            "API responses",
        ],
    },
    
    # ========== STREAMING ==========
    "streaming": {
        "name": "Streaming Manager",
        "file": "core/streaming.py",
        "description": """
Real-time token streaming ve event handling.
        """,
        "features": [
            "Token-by-token streaming",
            "Server-Sent Events (SSE)",
            "WebSocket streaming",
            "Progress callbacks",
            "Multi-client broadcasting",
            "Stream buffering",
        ],
        "event_types": [
            "START", "TOKEN", "CHUNK", "PROGRESS",
            "TOOL_CALL", "TOOL_RESULT", "METADATA",
            "ERROR", "END", "HEARTBEAT",
        ],
    },
    
    # ========== OBSERVABILITY ==========
    "observability": {
        "name": "Observability & Tracing",
        "description": """
Distributed tracing, metrics collection ve monitoring.
        """,
        "components": {
            "tracing": {
                "file": "core/tracing.py",
                "features": [
                    "OpenTelemetry compatible spans",
                    "Distributed trace context",
                    "Performance monitoring",
                    "Error tracking",
                ],
            },
            "analytics": {
                "file": "core/analytics.py",
                "features": [
                    "Usage analytics",
                    "Event tracking",
                    "Session analytics",
                    "Performance metrics",
                ],
            },
            "logging": {
                "file": "core/logger.py",
                "features": [
                    "Rotating file logs",
                    "Console output",
                    "Error-specific logs",
                    "Structured logging",
                ],
            },
        },
    },
    
    # ========== RELIABILITY ==========
    "reliability": {
        "name": "Reliability Patterns",
        "description": """
Sistem dayanıklılığı için enterprise patternler.
        """,
        "patterns": {
            "circuit_breaker": {
                "file": "core/circuit_breaker.py",
                "states": ["CLOSED", "OPEN", "HALF_OPEN"],
                "description": "Cascade failure önleme",
            },
            "rate_limiter": {
                "file": "core/rate_limiter.py",
                "limits": {
                    "per_minute": 60,
                    "per_hour": 1000,
                    "per_day": 10000,
                    "burst": 10,
                },
            },
            "retry": {
                "strategy": "Exponential backoff",
                "max_attempts": 3,
            },
            "error_recovery": {
                "file": "core/error_recovery.py",
                "strategies": ["Retry", "Fallback", "Graceful degradation"],
            },
        },
    },
    
    # ========== MEMORY SYSTEMS ==========
    "memory": {
        "name": "Memory Systems",
        "file": "core/memory.py",
        "description": """
Uzun süreli hafıza ve bilgi saklama sistemleri.
        """,
        "types": {
            "conversation_buffer": {
                "description": "Son N mesajı bellekte tutar",
                "max_messages": 20,
            },
            "summary_memory": {
                "description": "Konuşmaları özetleyerek saklar",
                "features": ["LLM-based summarization", "Compression"],
            },
            "entity_memory": {
                "description": "Varlıkları ve ilişkileri saklar",
                "features": ["Entity extraction", "Relationship tracking"],
            },
            "knowledge_memory": {
                "description": "Öğrenilen bilgileri saklar",
                "features": ["Importance scoring", "Decay with time", "Semantic search"],
            },
        },
        "memgpt_style": {
            "file": "core/memgpt_memory.py",
            "description": "MemGPT-inspired memory management",
            "features": [
                "Core memory (always available)",
                "Archival memory (searchable)",
                "Working memory (current context)",
            ],
        },
    },
    
    # ========== SESSION MANAGEMENT ==========
    "sessions": {
        "name": "Session Management",
        "file": "core/session_manager.py",
        "description": """
Konuşma oturumu yönetimi ve geçmiş saklama.
        """,
        "features": [
            "Persistent session storage (JSON)",
            "Session history search",
            "Favorite messages",
            "Session pinning",
            "Tags and categories",
            "Export/Import",
        ],
        "storage_location": "data/sessions/",
    },
    
    # ========== NOTES SYSTEM ==========
    "notes": {
        "name": "Notes Manager",
        "file": "core/notes_manager.py",
        "description": """
Masaüstü dosya yöneticisi tarzında not ve klasör yönetimi.
        """,
        "features": [
            "Folders and subfolders",
            "Rich text notes",
            "Color coding",
            "Pinning",
            "Tags",
            "Search",
        ],
        "storage_location": "data/notes/",
    },
    
    # ========== DEPLOYMENT ==========
    "deployment": {
        "name": "Deployment Options",
        "description": """
Sistemin farklı ortamlarda çalıştırılması.
        """,
        "options": {
            "local": {
                "startup_script": "run.py",
                "windows_scripts": ["startup.bat", "startup.ps1", "startup.vbs"],
                "requirements": "requirements.txt",
            },
            "docker": {
                "files": ["Dockerfile", "Dockerfile.frontend", "docker-compose.yml"],
                "services": ["backend", "frontend", "ollama"],
            },
        },
        "requirements": {
            "python": ">=3.10",
            "ollama": "Running locally on port 11434",
            "memory": "Minimum 8GB RAM (16GB recommended)",
            "storage": "~2GB for models + data",
        },
    },
    
    # ========== PERFORMANCE FEATURES ==========
    "performance": {
        "name": "Performance Optimizations",
        "version": "v2.2",
        "features": [
            "Lazy loading - Modüller sadece kullanıldığında yüklenir",
            "Two-tier caching - L1 memory + L2 SQLite",
            "Connection pooling - HTTP ve database bağlantıları",
            "Batch processing - Embedding ve API çağrıları",
            "Async operations - Non-blocking I/O",
            "Stream processing - Memory-efficient data handling",
        ],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_capability_info(capability: str) -> Optional[Dict[str, Any]]:
    """
    Belirli bir yetenek hakkında bilgi al.
    
    Args:
        capability: Yetenek adı (ör: "mcp", "rag", "agents")
        
    Returns:
        Yetenek bilgisi dictionary'si veya None
    """
    return SYSTEM_KNOWLEDGE.get(capability)


def get_all_capabilities() -> List[str]:
    """Tüm yeteneklerin listesini döndür."""
    return list(SYSTEM_KNOWLEDGE.keys())


def get_feature_summary() -> str:
    """Özellik özetini metin olarak döndür."""
    summary = f"""
# {SYSTEM_NAME} - Sistem Özeti
Version: {SYSTEM_VERSION}

## Temel Özellikler:
- 🤖 Multi-Agent System: Orchestrator, Research, Writer, Analyzer, Assistant, ReAct agents
- 📚 RAG Pipeline: Document loader, chunker, retriever, reranker, hybrid search
- 🧠 LLM Manager: Ollama tabanlı, failover, streaming, caching
- 🔍 Advanced RAG: CRAG (Corrective RAG), Graph RAG
- 🛠️ Tool System: Web search, calculator, code executor, file operations
- 🔌 MCP Support: Model Context Protocol for AI interoperability
- 🛡️ Security: Guardrails, prompt injection protection, PII detection
- ⚡ Performance: Lazy loading, two-tier caching, async operations
- 📊 Observability: Tracing, analytics, logging
- 🔄 Reliability: Circuit breaker, rate limiter, retry patterns
- 💾 Memory: Conversation, summary, entity, knowledge memory
- 🌐 Web UI: Streamlit frontend with themes

## Mimari:
- Frontend: Streamlit (Port 8501)
- Backend: FastAPI (Port 8000)
- LLM: Ollama (Port 11434)
- Vector DB: ChromaDB (Persistent)
- Cache: SQLite + In-Memory LRU
"""
    return summary


def get_architecture_description() -> str:
    """Detaylı mimari açıklamasını döndür."""
    return SYSTEM_KNOWLEDGE["architecture"]["description"]


def format_for_system_prompt() -> str:
    """
    Sistem bilgisini system prompt'a eklenebilecek formatta döndür.
    Bu, AI'ın kendi hakkında bilgi sahibi olmasını sağlar.
    """
    return f"""
## Senin Hakkında (Sistem Bilgisi)

Sen "{SYSTEM_NAME}" adlı kurumsal AI asistansın. Version {SYSTEM_VERSION}.

### Temel Yeteneklerin:
1. **Multi-Agent System**: Araştırma, yazma, analiz ve genel asistanlık için uzmanlaşmış agent'lar
2. **RAG (Retrieval-Augmented Generation)**: Yüklenen dökümanlardan bilgi çekme ve yanıtlarını zenginleştirme
3. **Web Search**: DuckDuckGo üzerinden güncel bilgi arama
4. **MCP (Model Context Protocol)**: Dış sistemlerle standart protokol üzerinden entegrasyon
5. **Tool Usage**: Hesaplama, kod çalıştırma, dosya işlemleri

### Teknik Altyapın:
- LLM: Ollama üzerinde çalışan yerel model (varsayılan: qwen2.5:7b)
- Vector DB: ChromaDB (semantic search için)
- Embedding: nomic-embed-text (768 dimension)
- API: FastAPI backend
- Frontend: Streamlit web UI

### MCP Hakkında:
MCP (Model Context Protocol), Anthropic'in geliştirdiği standart bir AI interoperabilite protokolüdür.
Sende MCP tam implement edilmiştir:
- Resources: Dökümanlar, session'lar, notlar MCP kaynağı olarak sunulur
- Tools: Web search, calculate, rag_query gibi araçlar MCP tool olarak kullanılabilir
- Prompts: Sistem promptları MCP üzerinden yönetilebilir

### Güvenlik:
- Prompt injection koruması
- PII (Kişisel Bilgi) tespiti ve maskeleme
- Content filtering
- Rate limiting

### Performans:
- Lazy loading ile hızlı başlangıç
- İki katmanlı cache sistemi (memory + disk)
- Streaming yanıtlar
- Async işlemler

Bu bilgileri kullanarak kendi mimarini ve yeteneklerini açıklayabilirsin.
"""


# ============================================================================
# SYSTEM PROMPT INTEGRATION
# ============================================================================

SELF_KNOWLEDGE_PROMPT = format_for_system_prompt()


# ============================================================================
# CAPABILITY QUERY INTERFACE
# ============================================================================

class SystemKnowledgeQuery:
    """
    AI'ın kendi hakkında soru sormasını sağlayan interface.
    """
    
    @staticmethod
    def what_is(topic: str) -> str:
        """Belirli bir konu hakkında bilgi ver."""
        info = get_capability_info(topic.lower().replace(" ", "_"))
        if info:
            if isinstance(info, dict):
                name = info.get("name", topic)
                desc = info.get("description", "Bilgi mevcut değil.")
                return f"**{name}**: {desc}"
            return str(info)
        return f"'{topic}' hakkında bilgi bulunamadı."
    
    @staticmethod
    def how_does_work(component: str) -> str:
        """Bir bileşenin nasıl çalıştığını açıkla."""
        info = get_capability_info(component.lower().replace(" ", "_"))
        if info and isinstance(info, dict):
            features = info.get("features", {})
            if features:
                if isinstance(features, dict):
                    return "\n".join([f"- {k}: {v}" for k, v in features.items()])
                elif isinstance(features, list):
                    return "\n".join([f"- {f}" for f in features])
        return f"'{component}' çalışma detayları bulunamadı."
    
    @staticmethod  
    def list_capabilities() -> str:
        """Tüm yetenekleri listele."""
        caps = get_all_capabilities()
        return "Mevcut yetenekler:\n" + "\n".join([f"- {c}" for c in caps])


# Convenience instance
system_knowledge = SystemKnowledgeQuery()
