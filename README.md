<!-- 
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  ⚠️  HATIRLATMA: Bu projede ZATEN bir venv var! Yenisini oluşturmana gerek yok!  ║
║  📁  Konum: .\venv\Scripts\python.exe                                           ║
║  💡  Çalıştırma: .\venv\Scripts\python.exe run.py                                ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
-->

# 🚀 Enterprise AI Assistant
## Endüstri Standartlarında Kurumsal Agentic AI Çözümü

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/status-production-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/LangGraph-compatible-purple.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/MCP-integrated-yellow.svg" alt="MCP">
</p>

## 🎯 Proje Hakkında

Enterprise AI Assistant, şirketlerin kurumsal bilgi yönetimi ihtiyaçlarını karşılamak için tasarlanmış, **tamamen local çalışan**, **sıfır maliyetli**, **endüstri standartlarında** bir Agentic AI çözümüdür.

### ✨ Temel Özellikler

- 🔒 **%100 Local** - Veriler şirketten asla çıkmaz
- 🤖 **Multi-Agent Sistem** - Uzmanlaşmış AI ekibi
- 📚 **Universal RAG** - Her format desteklenir (PDF, DOCX, XLSX, TXT, MD, HTML, JSON)
- 🛠️ **MCP Entegrasyonu** - Model Context Protocol ile genişletilebilir araçlar
- 💰 **Sıfır Maliyet** - API ücreti yok
- ⚡ **Hızlı Kurulum** - 30 dakikada çalışır durumda

### 🆕 v2.0.0 Enterprise Özellikler

#### 🧠 Advanced RAG Pipeline
- **HyDE** (Hypothetical Document Embeddings) - LLM ile varsayımsal döküman oluşturma
- **Multi-Query Retrieval** - Çoklu sorgu perspektifleri
- **Reciprocal Rank Fusion (RRF)** - Sonuç birleştirme algoritması
- **Cross-Encoder Reranking** - Semantic reranking
- **Contextual Compression** - Bağlam sıkıştırma

#### 🔗 Knowledge Graph (GraphRAG)
- **Entity Extraction** - LLM tabanlı varlık çıkarma
- **Relation Mapping** - İlişki haritalama
- **Graph Queries** - Graf sorgulama
- **Path Finding** - Varlıklar arası yol bulma

#### 🔄 LangGraph-Style Workflows
- **State Machine** - Durum makinesi tabanlı akış
- **Conditional Routing** - Koşullu yönlendirme
- **Parallel Execution** - Paralel görev yürütme
- **Human-in-the-Loop** - İnsan onayı noktaları

#### 🛡️ Guardrails & Safety
- **Input Guards** - Injection, PII, spam koruması
- **Output Guards** - Hallüsinasyon tespiti, format validasyonu
- **Multi-Level Security** - LOW, MEDIUM, HIGH, STRICT seviyeleri

#### 📊 RAG Evaluation Metrics
- **Context Relevance** - Bağlam alaka düzeyi
- **Faithfulness** - Kaynak sadakati
- **Answer Relevance** - Yanıt kalitesi
- **Lexical Overlap** - Sözcüksel örtüşme

#### 🧠 Long-Term Memory
- **Conversation Buffer** - Son N mesaj belleği
- **Summary Memory** - Uzun konuşma özetleme
- **Persistent Memory** - SQLite destekli kalıcı bellek
- **Memory Decay** - Kullanılmayan bilgi unutma

#### 🔌 MCP Integration
- **Local MCP Servers** - Yerel araç sunucuları
- **Remote MCP Servers** - Uzak araç entegrasyonu
- **MCPHub** - Çoklu sunucu yönetimi
- **Built-in Tools** - Calculator, Time, File Info

#### 🤖 Autonomous Agent System (YENİ!)
- **Multi-step Task Planning** - Karmaşık görevleri otomatik planlama
- **Tool Selection & Execution** - Akıllı araç seçimi ve çalıştırma
- **Self-Correction Mechanism** - Hata durumunda otomatik düzeltme
- **Human-in-the-Loop Support** - Gerektiğinde insan müdahalesi
- **Progress Streaming** - Gerçek zamanlı ilerleme takibi
- **WebSocket Integration** - Anlık durum güncellemeleri

#### 📊 v1.1.0 Özellikler
- **Analytics Dashboard** - Kullanım istatistikleri ve trend analizi
- **Akıllı Cache** - LLM yanıtları için TTL destekli cache sistemi
- **Prompt Templates** - Önceden tanımlı profesyonel prompt şablonları
- **Web Search** - DuckDuckGo ile internet araması
- **Export/Import** - Session ve analytics dışa/içe aktarma
- **Rate Limiting** - API istekleri için limit koruması
- **Health Monitoring** - Detaylı sistem sağlık kontrolü
- **Advanced Document Processing** - Gelişmiş döküman işleme

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.11+
- [Ollama](https://ollama.ai) (local LLM runtime)
- 16GB+ RAM

### Kurulum

```bash
# 1. Repoyu klonla
git clone <repo-url>
cd AgenticManagingSystem

# 2. Virtual environment oluştur
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Bağımlılıkları yükle
pip install -r requirements.txt

# 4. .env dosyasını oluştur
copy .env.example .env

# 5. Ollama modellerini indir
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 6. Uygulamayı başlat
python run.py
```

## 📁 Proje Yapısı

```
enterprise-ai-assistant/
├── agents/                # Multi-agent sistemi
│   ├── orchestrator.py        # Merkez yönetici
│   ├── research_agent.py      # Araştırma ajanı
│   ├── writer_agent.py        # Yazı ajanı
│   ├── analyzer_agent.py      # Analiz ajanı
│   └── assistant_agent.py     # Genel asistan
├── api/                   # FastAPI backend
│   ├── main.py                # API endpoint'leri
│   └── websocket.py           # Real-time streaming
├── core/                  # Çekirdek modüller
│   ├── config.py              # Konfigürasyon
│   ├── llm_manager.py         # LLM yönetimi
│   ├── embedding.py           # Embedding işlemleri
│   ├── vector_store.py        # ChromaDB vektör DB
│   ├── session_manager.py     # Session yönetimi
│   ├── logger.py              # Logging sistemi
│   ├── utils.py               # Yardımcı fonksiyonlar
│   ├── analytics.py           # 📊 Kullanım istatistikleri
│   ├── cache.py               # 💾 LLM cache sistemi
│   ├── prompts.py             # 📝 Prompt şablonları
│   ├── export.py              # 📤 Export/Import
│   ├── rate_limiter.py        # ⏱️ Rate limiting
│   ├── health.py              # ❤️ Sağlık kontrolü
│   ├── document_processor.py  # 📄 Gelişmiş döküman işleme
│   ├── memory.py              # 🧠 Long-term memory
│   ├── workflow.py            # 🔄 LangGraph-style workflows
│   └── guardrails.py          # 🛡️ Safety guards
├── frontend/              # Streamlit UI
│   └── app.py                 # Ana arayüz
├── rag/                   # RAG pipeline
│   ├── document_loader.py     # Döküman yükleme
│   ├── chunker.py             # Metin parçalama
│   ├── retriever.py           # Semantic retrieval
│   ├── advanced_rag.py        # 🚀 HyDE, Multi-Query, RRF
│   ├── knowledge_graph.py     # 🔗 GraphRAG
│   └── evaluation.py          # 📊 RAG evaluation
├── tools/                 # Agent araçları
│   ├── rag_tool.py            # RAG araçları
│   ├── file_tool.py           # Dosya işlemleri
│   ├── web_tool.py            # 🌐 Web arama
│   └── mcp_integration.py     # 🔌 MCP entegrasyonu
├── data/                  # Veri klasörleri
│   ├── chroma_db/             # Vektör veritabanı
│   ├── uploads/               # Yüklenen dosyalar
│   └── exports/               # Export dosyaları
├── logs/                  # Log dosyaları
├── requirements.txt       # Python bağımlılıkları
├── run.py                 # Ana başlatma scripti
└── README.md              # Bu dosya
```

## 🔧 Kullanım

### Web Arayüzü

1. `python run.py` ile başlatın
2. Tarayıcıda `http://localhost:8501` adresine gidin
3. Sohbet edin, döküman yükleyin, arama yapın!

### API

```bash
# Sağlık kontrolü
curl http://localhost:8000/health

# Detaylı sağlık raporu
curl http://localhost:8000/api/health/detailed

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "İzin politikamız nedir?"}'

# Döküman yükle
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@document.pdf"

# Arama
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "çalışan hakları", "top_k": 5}'

# Analytics istatistikleri
curl http://localhost:8000/api/analytics/stats?days=7

# Session export (JSON)
curl http://localhost:8000/api/export/sessions -o sessions.json

# Tam yedek
curl http://localhost:8000/api/export/backup -o backup.zip
```

### API Endpoint'leri

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/health` | GET | Temel sağlık kontrolü |
| `/api/health/detailed` | GET | Detaylı sistem raporu |
| `/api/chat` | POST | AI ile sohbet |
| `/api/search` | POST | Semantic arama |
| `/api/documents/upload` | POST | Döküman yükleme |
| `/api/documents` | GET | Döküman listesi |
| `/api/analytics/stats` | GET | Kullanım istatistikleri |
| `/api/analytics/activity` | GET | Saatlik aktivite |
| `/api/ratelimit/status` | GET | Rate limit durumu |
| `/api/export/sessions` | GET | Session export |
| `/api/export/backup` | GET | Tam yedek |
| `/ws/chat/{client_id}` | WS | Real-time streaming |

### 🤖 Autonomous Agent API

| Endpoint | Method | Açıklama |
|----------|--------|----------|
| `/api/agent/tasks` | POST | Yeni görev oluştur |
| `/api/agent/tasks` | GET | Tüm görevleri listele |
| `/api/agent/tasks/{id}` | GET | Görev detayı |
| `/api/agent/tasks/{id}/start` | POST | Görevi başlat |
| `/api/agent/tasks/{id}/cancel` | POST | Görevi iptal et |
| `/api/agent/tasks/{id}/respond` | POST | İnsan müdahalesine yanıt |
| `/api/agent/tasks/{id}/stream` | POST | Streaming execution (SSE) |
| `/api/agent/quick` | POST | Hızlı görev (oluştur + çalıştır) |
| `/api/agent/tools` | GET | Mevcut araçları listele |
| `/api/agent/stats` | GET | Agent istatistikleri |
| `/ws/agent/{task_id}` | WS | Task WebSocket streaming |

### API Dökümantasyonu

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤖 Agent Sistemi

| Agent | Rol | Yetenekler |
|-------|-----|------------|
| **Orchestrator** | Merkez Yönetici | Görev analizi, yönlendirme |
| **Research Agent** | Araştırmacı | Bilgi arama, kaynak toplama |
| **Writer Agent** | Yazar | Email, rapor, döküman üretimi |
| **Analyzer Agent** | Analist | Veri analizi, özet, karşılaştırma |
| **Assistant Agent** | Asistan | Genel soru-cevap, yardım |

## 📊 Teknoloji Stack

### Core
| Teknoloji | Kullanım |
|-----------|----------|
| **Ollama** | Local LLM runtime |
| **Qwen 2.5:8B** | Ana LLM modeli |
| **nomic-embed-text** | Embedding modeli |
| **ChromaDB** | Vektör veritabanı |
| **SQLite** | Kalıcı veri depolama |

### Backend
| Teknoloji | Kullanım |
|-----------|----------|
| **FastAPI** | REST API |
| **WebSocket** | Real-time streaming |
| **Pydantic** | Veri validasyonu |
| **asyncio** | Asenkron işlemler |

### Frontend
| Teknoloji | Kullanım |
|-----------|----------|
| **Streamlit** | Web arayüzü |
| **Plotly** | Grafikler |

### AI/ML Patterns
| Pattern | Uygulama |
|---------|----------|
| **LangGraph** | Workflow engine |
| **MCP** | Tool integration |
| **GraphRAG** | Knowledge graph |
| **HyDE** | Advanced retrieval |
| **RRF** | Result fusion |

## 🎯 Kullanım Senaryoları

- 📋 HR: Politika soruları, onboarding, CV tarama
- ⚖️ Legal: Sözleşme analizi, emsal arama
- 💼 Sales: Müşteri bilgisi, teklif hazırlama
- 📊 Operations: Teknik dökümanlar, prosedürler

## 📈 Performans

| Metrik | Hedef |
|--------|-------|
| İlk yanıt süresi | < 1 sn |
| Toplam yanıt süresi | < 5 sn |
| Döküman indexleme | < 2 sn/sayfa |
| Cache hit ratio | > 30% |

## 🔐 Güvenlik

- ✅ Tüm veriler local'de kalır
- ✅ Cloud'a veri gönderimi yok
- ✅ Offline çalışabilir
- ✅ KVKK/GDPR uyumlu
- ✅ Rate limiting koruması
- ✅ Input sanitization

## 📄 Lisans

MIT License

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır!

---

**Enterprise AI Assistant** - Endüstri Standartlarında Kurumsal AI Çözümü 🚀
