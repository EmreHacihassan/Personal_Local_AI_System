# 📚 Enterprise AI Assistant - Tam Özellik Dökümantasyonu

> **Versiyon:** 3.0  
> **Son Güncelleme:** 23 Ocak 2026  
> **Toplam Özellik Sayısı:** 77+  
> **Toplam API Endpoint:** 100+  

---

## 📋 İçindekiler

1. [Genel Bakış](#1-genel-bakış)
2. [Sohbet ve Konuşma Özellikleri](#2-sohbet-ve-konuşma-özellikleri)
3. [RAG ve Doküman Sistemi](#3-rag-ve-doküman-sistemi)
4. [Ajan Sistemi](#4-ajan-sistemi)
5. [Öğrenme Yolculuğu V1](#5-öğrenme-yolculuğu-v1)
6. [Öğrenme Yolculuğu V2 (Full Meta)](#6-öğrenme-yolculuğu-v2-full-meta)
7. [Premium Özellikler](#7-premium-özellikler)
8. [Görüntü ve Bilgisayar Kullanımı](#8-görüntü-ve-bilgisayar-kullanımı)
9. [Analitik ve Dashboard](#9-analitik-ve-dashboard)
10. [Ayarlar ve Yapılandırma](#10-ayarlar-ve-yapılandırma)
11. [Entegrasyon Özellikleri](#11-entegrasyon-özellikleri)
12. [Güvenlik Özellikleri](#12-güvenlik-özellikleri)
13. [Frontend Bileşenleri](#13-frontend-bileşenleri)
14. [Teknik Altyapı](#14-teknik-altyapı)

---

## 1. Genel Bakış

### Teknoloji Yığını

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **Backend** | FastAPI (Python 3.11) | Async API sunucusu |
| **Frontend** | Next.js 14 (TypeScript/React) | Modern web arayüzü |
| **Vektör DB** | ChromaDB | Embedding storage |
| **LLM** | Ollama (Multi-model) | Lokal AI modelleri |
| **Arama** | Hybrid Search (BM25 + Dense + RRF) | Gelişmiş arama |
| **GPU** | CUDA (NVIDIA RTX) | Hızlandırılmış işlem |

### Özet İstatistikler

```
┌─────────────────────────────────────────┐
│  Toplam Özellik Kategorisi:  11         │
│  Toplam Özellik:             77+        │
│  API Endpoint:               100+       │
│  WebSocket Endpoint:         8          │
│  Core Modül:                 83+        │
│  Ajan Tipi:                  12         │
│  RAG Stratejisi:             6          │
│  Premium Özellik:            12         │
└─────────────────────────────────────────┘
```

---

## 2. Sohbet ve Konuşma Özellikleri

### 2.1 Chat API
**Dosya:** `api/main.py`  
**Endpoint:** `/api/chat`, `/api/chat/stream`

| Özellik | Açıklama |
|---------|----------|
| Çoklu Oturum | Birden fazla sohbet oturumu yönetimi |
| SSE Streaming | Gerçek zamanlı akış yanıtları |
| Kaynak Referansı | Wikipedia tarzı [1][2] kaynak gösterimi |
| Bağlam Yönetimi | Önceki mesajları hatırlama |

```python
# Örnek kullanım
POST /api/chat
{
  "message": "Python nedir?",
  "session_id": "abc123",
  "use_rag": true
}
```

### 2.2 Model Routing (Akıllı Model Seçimi)
**Dosya:** `api/routing_endpoints.py`  
**Endpoint:** `/routing/route`, `/routing/feedback`, `/routing/compare`, `/routing/confirm`

| Özellik | Açıklama |
|---------|----------|
| Human-in-the-Loop | Kullanıcı onaylı model seçimi |
| AI Router | Karmaşıklık analizi ile otomatik seçim |
| Pattern Learning | Geri bildirimle öğrenen sistem |
| Model Karşılaştırma | A/B test ile model performans karşılaştırması |

**Desteklenen Modeller:**
- `gemma3:4b` - Hızlı, basit sorular
- `qwen2.5:7b` - Genel amaçlı
- `qwen2.5:14b` - Karmaşık görevler
- `deepseek-r1:8b` - Akıl yürütme
- `llama3.2-vision:11b` - Görsel analiz

### 2.3 Sesli Konuşma (Voice AI)
**Dosya:** `api/voice_endpoints.py`  
**Endpoint:** `/api/voice/transcribe`, `/api/voice/synthesize`, `/ws/voice`

| Özellik | Açıklama |
|---------|----------|
| STT (Whisper) | Konuşmayı metne çevirme |
| TTS (Edge TTS) | Metni sese çevirme |
| WebSocket Voice | Gerçek zamanlı sesli sohbet |
| Çoklu Dil | Türkçe, İngilizce ve diğer diller |

**Desteklenen Sesler:**
- `tr-TR-AhmetNeural` (Erkek, Türkçe)
- `tr-TR-EmelNeural` (Kadın, Türkçe)
- `en-US-JennyNeural` (Kadın, İngilizce)

### 2.4 AI Bellek ve Kişiselleştirme
**Dosya:** `api/memory_endpoints.py`  
**Endpoint:** `/api/memory/profiles/{user_id}`, `/api/memory/memories`, `/api/memory/learn/*`

| Özellik | Açıklama |
|---------|----------|
| Kullanıcı Profili | Tercihler, ilgi alanları, stil |
| Konuşma Belleği | Önceki konuşmalardan öğrenme |
| Yazım Stili Adaptasyonu | Kullanıcıya uygun ton |
| Kişiselleştirilmiş Promptlar | Otomatik özelleştirme |

### 2.5 Web Arama Entegrasyonu
**Dosya:** `api/main.py`  
**Endpoint:** `/api/web-search`

| Özellik | Açıklama |
|---------|----------|
| DuckDuckGo Arama | Privacy-focused arama |
| Sonuç Özetleme | AI ile sonuç özetleme |
| Premium Arama | Genişletilmiş sonuçlar |

### 2.6 LLM Manager
**Dosya:** `core/llm_manager.py`

| Özellik | Açıklama |
|---------|----------|
| Primary/Backup Failover | Model çökerse yedek model |
| Streaming | Token token yanıt |
| Önbellek (2 saat TTL) | Tekrarlayan sorulara hızlı yanıt |
| Token Sayımı | Bağlam penceresi yönetimi |
| Retry (Exponential Backoff) | Hata durumunda yeniden deneme |
| VLM Desteği | Görsel + metin sorguları |

### 2.7 Oturum Yönetimi
**Dosya:** `core/session_manager.py`

| Özellik | Açıklama |
|---------|----------|
| Kalıcı Oturumlar | SQLite tabanlı saklama |
| Geçmiş Yönetimi | Sohbet geçmişi |
| Bağlam Threading | Konu takibi |

### 2.8 Circuit Breaker
**Dosya:** `core/circuit_breaker.py`

| Özellik | Açıklama |
|---------|----------|
| Otomatik Failover | Hata eşiği aşılınca devre kesme |
| Rate Limiting | İstek sınırlama |
| Hata Eşiği Koruması | Sistem koruması |

---

## 3. RAG ve Doküman Sistemi

### 3.1 Advanced RAG System
**Dosya:** `rag/advanced_rag.py`

**6 RAG Stratejisi:**

| Strateji | Açıklama | Kullanım Durumu |
|----------|----------|-----------------|
| **Naive** | Basit embedding araması | Hızlı sorgular |
| **HyDE** | Hipotetik doküman oluşturma | Belirsiz sorular |
| **Multi-Query** | Sorguyu genişletme | Kapsamlı arama |
| **Fusion (RRF)** | Sonuçları birleştirme | En iyi doğruluk |
| **Rerank** | Cross-encoder ile yeniden sıralama | Yüksek precision |
| **Contextual Compression** | Bağlam sıkıştırma | Token tasarrufu |

### 3.2 Hybrid Search
**Dosya:** `rag/hybrid_search.py`

| Özellik | Açıklama |
|---------|----------|
| Dense Search | Embedding tabanlı semantik arama |
| Sparse Search | BM25 anahtar kelime araması |
| Reciprocal Rank Fusion | Sonuç birleştirme algoritması |
| Namespace Desteği | Koleksiyon izolasyonu |

```
Hybrid Score = α × Dense_Score + (1-α) × Sparse_Score
```

### 3.3 Query Expansion
**Dosya:** `api/premium_endpoints.py`  
**Endpoint:** `/api/premium/query/expand`

| Özellik | Açıklama |
|---------|----------|
| Eş Anlamlı Genişleme | Synonym ekleme |
| Anahtar Kelime Çıkarma | TF-IDF bazlı |
| Multi-Query | Birden fazla sorgu oluşturma |
| HyDE | Hipotetik doküman üretme |

### 3.4 Semantic Reranking
**Dosya:** `core/premium_features.py`

| Özellik | Açıklama |
|---------|----------|
| Cross-Encoder | Derin anlam karşılaştırması |
| Keyword Boost | Anahtar kelime eşleşmesi artışı |
| Recency Boost | Yeni dokümanlara öncelik |
| Diversity Optimization | Çeşitli sonuçlar |

### 3.5 Multi-Modal RAG
**Dosya:** `api/multimodal_endpoints.py`  
**Endpoint:** `/api/multimodal/index`, `/api/multimodal/search`, `/api/multimodal/qa`

| Dosya Türü | Desteklenen Formatlar |
|------------|----------------------|
| **Doküman** | PDF, DOCX, TXT, MD |
| **Görsel** | PNG, JPG, WebP |
| **Ses** | MP3, WAV, M4A |
| **Video** | MP4, AVI, MKV |

### 3.6 Doküman Yönetimi
**Dosya:** `api/routers/documents.py`  
**Endpoint:** `/api/documents/*`

| Özellik | Açıklama |
|---------|----------|
| Yükleme | Dosya yükleme ve indeksleme |
| Metadata | Etiket, kategori, açıklama |
| Silme | Güvenli silme |
| Güncelleme | Doküman güncelleme |

### 3.7 RAG Evaluation
**Dosya:** `api/premium_endpoints.py`  
**Endpoint:** `/api/premium/rag/evaluate`

| Metrik | Açıklama |
|--------|----------|
| Faithfulness | Yanıtın kaynaklara sadakati |
| Relevance | Soruyla ilgililik |
| Context Precision | Bağlam doğruluğu |

### 3.8 Smart Auto-Tagging
**Dosya:** `core/premium_features.py`

| Özellik | Açıklama |
|---------|----------|
| TF-IDF | Anahtar kelime çıkarma |
| NER | Email, URL, kod pattern tanıma |
| Topic Classification | Konu sınıflandırma |
| Language Detection | Dil algılama |

### 3.9 Chunking Strategies
**Dosya:** `rag/chunking.py`

| Strateji | Açıklama |
|----------|----------|
| Semantic Chunking | Anlam bazlı bölme |
| Sliding Window | Kayar pencere |
| Recursive Splitting | Hiyerarşik bölme |

### 3.10 Embedding Management
**Dosya:** `core/embedding.py`

| Özellik | Açıklama |
|---------|----------|
| Multi-Model | Farklı embedding modelleri |
| Caching | Önbellek |
| Batch Processing | Toplu işlem |

**Desteklenen Modeller:**
- `nomic-embed-text`
- `mxbai-embed-large`
- `bge-m3`

### 3.11 Vector Store Operations
**Dosya:** `core/vector_store.py`

| Özellik | Açıklama |
|---------|----------|
| ChromaDB CRUD | Oluşturma, okuma, güncelleme, silme |
| Collection Management | Koleksiyon yönetimi |
| Similarity Search | Benzerlik araması |

### 3.12 Document Comparison
**Dosya:** `core/premium_features_v3.py`

| Özellik | Açıklama |
|---------|----------|
| Line Diff | Satır bazlı fark |
| Word Diff | Kelime bazlı fark |
| Semantic Diff | Anlam bazlı fark |
| Side-by-Side View | Yan yana görünüm |

---

## 4. Ajan Sistemi

### 4.1 Autonomous Agent
**Dosya:** `agents/autonomous_agent.py`  
**Endpoint:** `/api/agent/tasks`, `/ws/agent/{task_id}`

| Özellik | Açıklama |
|---------|----------|
| Görev Ayrıştırma | Multi-step decomposition |
| Araç Seçimi | Otomatik tool selection |
| Kendini Düzeltme | Self-correction |
| Checkpoint | İlerleme kaydetme |
| Human-in-the-Loop | Kullanıcı müdahalesi |

**Görev Durumları:**
```
pending → running → [completed | failed | cancelled]
                  ↓
              waiting_for_input
```

### 4.2 Orchestrator Agent
**Dosya:** `agents/orchestrator.py`

| Özellik | Açıklama |
|---------|----------|
| Görev Analizi | Görev karmaşıklık analizi |
| Ajan Yönlendirme | Doğru ajana yönlendirme |
| Multi-Agent | Çoklu ajan koordinasyonu |
| Sonuç Birleştirme | Sonuçları merge etme |

### 4.3 Agent Marketplace
**Dosya:** `api/agent_marketplace_endpoints.py`  
**Endpoint:** `/api/agents`, `/api/agents/templates`, `/api/agents/teams`

| Özellik | Açıklama |
|---------|----------|
| Özel Ajan Oluşturucu | Custom agent builder |
| Davranış Konfigürasyonu | Kişilik, yaratıcılık, özerklik |
| Şablonlar | Hazır ajan şablonları |
| Import/Export | Ajan paylaşımı |
| Puanlama | Ajan değerlendirmesi |

**Ajan Kişilik Ayarları:**
```json
{
  "personality": "helpful, precise, creative",
  "creativity": 0.7,
  "autonomy_level": "moderate",
  "risk_tolerance": "low"
}
```

### 4.4 Multi-Agent Teams
**Dosya:** `api/agent_marketplace_endpoints.py`  
**Endpoint:** `/api/agents/teams/{id}/execute`

| Strateji | Açıklama |
|----------|----------|
| **Sequential** | Sıralı çalışma |
| **Parallel** | Paralel çalışma |
| **Hierarchical** | Hiyerarşik çalışma |
| **Consensus** | Uzlaşma tabanlı |
| **Debate** | Tartışma tabanlı |

### 4.5 Research Agent
**Dosya:** `agents/research_agent.py`

| Özellik | Açıklama |
|---------|----------|
| Bilgi Arama | RAG ve web araması |
| Kaynak Toplama | Çoklu kaynak birleştirme |
| Doğrulama | Fact verification |

### 4.6 Writer Agent
**Dosya:** `agents/writer_agent.py`

| Özellik | Açıklama |
|---------|----------|
| İçerik Oluşturma | Blog, makale, rapor |
| E-posta Yazma | Profesyonel e-postalar |
| Rapor Yazma | Yapılandırılmış raporlar |

### 4.7 Analyzer Agent
**Dosya:** `agents/analyzer_agent.py`

| Özellik | Açıklama |
|---------|----------|
| Veri Analizi | İstatistiksel analiz |
| Karşılaştırma | A/B karşılaştırma |
| Özetleme | Metin özetleme |

### 4.8 Tool Manager
**Dosya:** `tools/tool_manager.py`

| Özellik | Açıklama |
|---------|----------|
| Tool Registry | Araç kayıt sistemi |
| Rate Limiting | İstek sınırlama |
| Execution Tracking | Kullanım takibi |
| OpenAI Format | Function calling uyumu |

### 4.9 Mevcut Araçlar

| Araç | Dosya | Açıklama |
|------|-------|----------|
| **Calculator** | `tools/calculator_tool.py` | Matematik hesaplamaları |
| **Web Search** | `tools/web_search_tool.py` | İnternet araması |
| **Code Executor** | `tools/code_executor_tool.py` | Python/JS çalıştırma |
| **File Operations** | `tools/file_operations_tool.py` | Dosya işlemleri |

### 4.10 MCP Integration
**Dosya:** `tools/mcp_integration.py`

| Özellik | Açıklama |
|---------|----------|
| Model Context Protocol | Standart tool protokolü |
| JSON-RPC 2.0 | Haberleşme protokolü |

---

## 5. Öğrenme Yolculuğu V1

### 5.1 Stage Map System
**Dosya:** `api/learning_journey_endpoints.py`  
**Endpoint:** `/api/learning/packages`, `/api/learning/stages`, `/api/learning/content`

| Özellik | Açıklama |
|---------|----------|
| Candy Crush Tarzı | Görsel ilerleme haritası |
| Paket/Stage/İçerik | 3 seviyeli hiyerarşi |
| Kilit Açma | İlerleme ile kilit açma |

**Hiyerarşi:**
```
Stage (Aşama)
  └── Package (Paket)
        └── Content (İçerik)
              ├── Konu Anlatımı
              ├── Örnekler
              └── Sorular
```

### 5.2 XP & Stars System
**Dosya:** `api/learning_journey_endpoints.py`  
**Endpoint:** `/api/learning/xp`, `/api/learning/user/{id}/stats`

| Özellik | Açıklama |
|---------|----------|
| Experience Points | Deneyim puanları |
| Yıldız Toplama | Her paket için yıldız |
| Level Progression | Seviye atlama |

**XP Kazanma:**
- İçerik tamamlama: +50 XP
- Paket bitirme: +200 XP
- Stage bitirme: +500 XP
- Mükemmel puan: +100 XP bonus

### 5.3 Streak Tracking
**Dosya:** `api/learning_journey_endpoints.py`

| Özellik | Açıklama |
|---------|----------|
| Günlük Streak | Ardışık gün sayısı |
| Motivasyon | Streak kaybetmeme teşviki |
| Freeze | Streak dondurma hakkı |

### 5.4 Math Curriculum (AYT)
**Dosya:** `api/learning_journey_endpoints.py`

| Konu | Alt Konular |
|------|-------------|
| **Temel Matematik** | Sayılar, İşlemler |
| **Cebir** | Denklemler, Eşitsizlikler |
| **Fonksiyonlar** | Polinom, Üstel, Logaritma |
| **Trigonometri** | Açılar, Formüller |
| **Analitik Geometri** | Doğru, Çember, Konik |
| **Türev** | Limit, Türev Kuralları |
| **İntegral** | Belirsiz, Belirli İntegral |

### 5.5 Content Management
**Dosya:** `api/learning_journey_endpoints.py`  
**Endpoint:** `/api/learning/packages/{id}/content`

| Özellik | Açıklama |
|---------|----------|
| İçerik Oluşturma | Yeni içerik ekleme |
| Düzenleme | Mevcut içerik güncelleme |
| Sıralama | İçerik sırası değiştirme |

---

## 6. Öğrenme Yolculuğu V2 (Full Meta)

### 6.1 Journey Creation Wizard
**Dosya:** `frontend-next/src/components/learning/JourneyCreationWizard.tsx`

**5 Adımlı Wizard:**

| Adım | İçerik |
|------|--------|
| 1. Konu Seçimi | Matematik, Fizik, Programlama vb. |
| 2. Hedef Belirleme | Ana hedef, motivasyon |
| 3. Ön Bilgi | Seviye, zayıf alanlar |
| 4. Zaman Planı | Günlük saat, hedef tarih |
| 5. Tercihler | İçerik ve sınav türleri |

### 6.2 AI Thinking View
**Dosya:** `frontend-next/src/components/learning/AIThinkingView.tsx`

| Adım | Açıklama |
|------|----------|
| Goal Analyzer | Hedef analizi |
| Curriculum Selector | Müfredat seçimi |
| Topic Mapper | Konu haritalama |
| Stage Planner | Aşama planlama |
| Package Designer | Paket tasarımı |
| Exam Generator | Sınav oluşturma |
| Exercise Creator | Egzersiz oluşturma |
| Content Structurer | İçerik yapılandırma |

### 6.3 Curriculum Planning
**Dosya:** `api/learning_journey_v2_endpoints.py`  
**Endpoint:** `/journey/v2/create`

| Özellik | Açıklama |
|---------|----------|
| AI Müfredat | Otomatik müfredat oluşturma |
| Kişiselleştirme | Zayıf alanlara odaklanma |
| Zaman Tahmini | Tamamlama süresi hesabı |

**Çıktı Örneği:**
```json
{
  "total_stages": 7,
  "total_packages": 130,
  "total_exams": 98,
  "total_exercises": 158,
  "estimated_total_hours": 88.5,
  "total_xp_possible": 12500
}
```

### 6.4 Package Types

| Tür | Emoji | Açıklama |
|-----|-------|----------|
| **Intro** | 🎯 | Stage giriş paketi |
| **Learning** | 📚 | Konu anlatımı |
| **Practice** | ✏️ | Pratik egzersizler |
| **Review** | 🔄 | Tekrar paketi |
| **Exam** | 📝 | Sınav paketi |
| **Closure** | 🏆 | Stage kapanış paketi |

### 6.5 Advanced Exam System
**Dosya:** `core/learning_journey_v2/exam_system.py`

**15 Sınav Türü:**

| Kategori | Türler |
|----------|--------|
| **Klasik** | multiple_choice, true_false, fill_blank, matching |
| **Açık Uçlu** | short_answer, essay, open_ended |
| **Öğretme Bazlı** | feynman, teach_back, oral_presentation |
| **Görsel** | concept_map, diagram_label, flowchart |
| **Problem Çözme** | problem_solving, case_study, debugging |

### 6.6 Feynman Technique Exam
**Dosya:** `frontend-next/src/components/learning/ExamView.tsx`

| Adım | Açıklama |
|------|----------|
| 1. Konu Verme | AI bir konu seçer |
| 2. Açıklama | Kullanıcı konuyu anlatır |
| 3. AI Değerlendirme | 5 kriter üzerinden puanlama |
| 4. Geri Bildirim | Detaylı öneri |

**Değerlendirme Kriterleri:**
- **Accuracy (Doğruluk):** %20 - Bilgi doğruluğu
- **Depth (Derinlik):** %20 - Konu hakimiyeti
- **Clarity (Açıklık):** %20 - Anlaşılırlık
- **Examples (Örnekler):** %20 - Örnek kullanımı
- **Completeness (Bütünlük):** %20 - Konuyu kapsama

### 6.7 Exercise Types
**Dosya:** `core/learning_journey_v2/models.py`

**10 Egzersiz Türü:**

| Tür | Açıklama |
|-----|----------|
| **spaced_repetition** | Aralıklı tekrar |
| **active_recall** | Aktif hatırlama |
| **deliberate_practice** | Bilinçli pratik |
| **interleaving** | Karışık çalışma |
| **elaboration** | Detaylandırma |
| **dual_coding** | Görsel + metin |
| **concrete_examples** | Somut örnekler |
| **retrieval_practice** | Geri çağırma pratiği |
| **generation_effect** | Üretme etkisi |
| **testing_effect** | Test etkisi |

### 6.8 Certificate System
**Dosya:** `core/learning_journey_v2/certificate_system.py`  
**Frontend:** `frontend-next/src/components/learning/CertificateView.tsx`

| Özellik | Açıklama |
|---------|----------|
| Benzersiz Kod | Doğrulama kodu |
| Görsel Sertifika | Bronze, Silver, Gold, Platinum |
| Paylaşım | LinkedIn, Twitter |
| İndirme | PDF formatı |

**Seviyeler:**
- 🥉 **Bronze:** İlk tamamlama
- 🥈 **Silver:** Ortalama %80+
- 🥇 **Gold:** Ortalama %90+
- 💎 **Platinum:** Mükemmel tamamlama

### 6.9 Stage Map V2
**Dosya:** `frontend-next/src/components/learning/StageMapV2.tsx`

| Özellik | Açıklama |
|---------|----------|
| Genişletilebilir Aşamalar | Tıkla-genişlet |
| Çoklu Paket | Her stage'de birden fazla paket |
| Progress Bar | İlerleme çubuğu |
| XP Gösterimi | Kazanılan/Toplam XP |

### 6.10 Full Meta (12 Katmanlı Öğrenme)
**Dosya:** `api/full_meta_endpoints.py`

**12 Öğrenme Katmanı:**

| # | Katman | Açıklama | Süre |
|---|--------|----------|------|
| 1 | **warmup** | Isınma, ön hazırlık | 5 dk |
| 2 | **prime** | Motivasyon, hedef | 3 dk |
| 3 | **acquire** | Yeni bilgi edinme | 15 dk |
| 4 | **interrogate** | Sorgulama, neden/nasıl | 10 dk |
| 5 | **practice** | Temel uygulama | 15 dk |
| 6 | **connect** | Bağlantı kurma | 10 dk |
| 7 | **challenge** | Zorlayıcı problemler | 15 dk |
| 8 | **error_lab** | Hata analizi | 10 dk |
| 9 | **feynman** | Basitçe anlatma | 15 dk |
| 10 | **transfer** | Farklı alana uygulama | 10 dk |
| 11 | **meta_reflection** | Öğrenme sürecini değerlendirme | 5 dk |
| 12 | **consolidate** | Pekiştirme, özet | 10 dk |

---

## 7. Premium Özellikler

### 7.1 Background Task Queue
**Dosya:** `api/premium_endpoints.py`  
**Endpoint:** `/api/premium/tasks`, `/api/premium/tasks/{id}`

| Özellik | Açıklama |
|---------|----------|
| Öncelik Kuyruğu | Low, Normal, High, Critical |
| Durum Takibi | pending, running, completed, failed |
| İptal | Görev iptal etme |
| Progress | İlerleme yüzdesi |

### 7.2 Guardrails (Koruma)
**Dosya:** `api/premium_endpoints.py`  
**Endpoint:** `/api/premium/guardrails/check-input`, `/api/premium/guardrails/check-output`

| Kontrol | Açıklama |
|---------|----------|
| Input Safety | Zararlı giriş kontrolü |
| Output Safety | Çıktı filtreleme |
| Content Filter | İçerik filtreleme |
| PII Detection | Kişisel veri algılama |

### 7.3 Knowledge Graph
**Dosya:** `core/premium_features.py`  
**Endpoint:** `/api/knowledge-graph/*`

| Özellik | Açıklama |
|---------|----------|
| Entity Management | Varlık CRUD |
| Relationship Management | İlişki CRUD |
| Graph Traversal | BFS, DFS, Shortest Path |
| Community Detection | Topluluk algılama |
| D3.js Export | Görselleştirme verisi |

**Entity Türleri:**
- Person, Organization, Concept, Event, Location, Document

### 7.4 Real-Time Analytics
**Dosya:** `core/premium_features.py`

| Özellik | Açıklama |
|---------|----------|
| Event Tracking | Olay kayıt |
| Time-Series | Zaman serisi verileri |
| Anomaly Detection | Anormallik algılama |
| Health Scoring | Sağlık puanı (0-100) |
| Percentiles | p50, p90, p99 yanıt süreleri |

### 7.5 Deep Scholar
**Dosya:** `api/deep_scholar_endpoints.py`  
**Endpoint:** `/api/deep-scholar/documents`, `/api/deep-scholar/queue`

**6 Ajan Mimarisi:**

| Ajan | Görev |
|------|-------|
| **Researcher** | Kaynak toplama |
| **Analyzer** | Kaynak analizi |
| **Outliner** | Yapı oluşturma |
| **Writer** | İçerik yazma |
| **Critic** | Eleştiri ve düzeltme |
| **Editor** | Son düzenleme |

| Özellik | Açıklama |
|---------|----------|
| Priority Queue | Öncelikli kuyruk |
| Checkpoint/Recovery | İlerleme kaydetme |
| PDF/Markdown Export | Çıktı formatları |
| Academic Sources | Semantic Scholar, arXiv, CrossRef |

### 7.6 Workflow Builder
**Dosya:** `api/workflow_endpoints.py`  
**Endpoint:** `/api/workflows`, `/api/workflows/{id}/execute`, `/ws/workflows/{id}`

**Node Türleri:**

| Node | Açıklama |
|------|----------|
| **start** | Başlangıç noktası |
| **end** | Bitiş noktası |
| **llm_chat** | LLM sorgulama |
| **rag_query** | RAG sorgulama |
| **template** | Şablon işleme |
| **conditional** | Koşullu dallanma |
| **transform** | Veri dönüşümü |
| **api_call** | Harici API çağrısı |

### 7.7 Code Interpreter
**Dosya:** `api/code_endpoints.py`  
**Endpoint:** `/api/code/execute`, `/api/code/sessions`

| Özellik | Açıklama |
|---------|----------|
| Sandboxed Execution | İzole çalıştırma |
| Python/JavaScript | Desteklenen diller |
| Session Management | Oturum yönetimi |
| Plot Generation | Grafik oluşturma (base64) |
| File Upload/Download | Dosya işlemleri |

### 7.8 Trend Analysis
**Dosya:** `core/premium_features_v2.py`

| Özellik | Açıklama |
|---------|----------|
| Metric Recording | Metrik kayıt |
| Trend Insights | Trend analizi |
| Forecasting | Tahminleme |

### 7.9 Query Suggestions
**Dosya:** `core/premium_features_v2.py`

| Özellik | Açıklama |
|---------|----------|
| Autocomplete | Otomatik tamamlama |
| Popular Queries | Popüler sorgular |
| Personalized | Kişiselleştirilmiş öneriler |

### 7.10 Content Enhancement
**Dosya:** `core/premium_features_v3.py`

| Özellik | Açıklama |
|---------|----------|
| Markdown Fixing | MD düzeltme |
| Code Language Detection | Dil algılama |
| Table Extraction | Tablo çıkarma |
| Link Enrichment | Link zenginleştirme |
| Auto-Formatting | Otomatik biçimlendirme |

### 7.11 Fuzzy Search
**Dosya:** `core/premium_features_v2.py`

| Özellik | Açıklama |
|---------|----------|
| Typo Tolerance | Yazım hatası toleransı |
| Spelling Correction | Yazım düzeltme |
| "Did you mean" | Öneri sistemi |

### 7.12 AI Summarization
**Dosya:** `core/premium_features_v2.py`

| Özellik | Açıklama |
|---------|----------|
| Multi-Document | Çoklu doküman özeti |
| Extractive | Cümle seçme |
| Abstractive | Yeniden yazma |

---

## 8. Görüntü ve Bilgisayar Kullanımı

### 8.1 Vision AI
**Dosya:** `api/vision_endpoints.py`  
**Endpoint:** `/api/vision/capture`, `/api/vision/analyze`, `/ws/vision`

**Analiz Modları:**

| Mod | Açıklama |
|-----|----------|
| **describe** | Genel açıklama |
| **ui** | UI element analizi |
| **text_extract** | Metin çıkarma (OCR) |
| **code_review** | Kod inceleme |
| **error_detect** | Hata algılama |

### 8.2 Computer Use (Masaüstü Otomasyonu)
**Dosya:** `api/computer_use_endpoints.py`  
**Endpoint:** `/api/computer-use/execute`, `/api/computer-use/modes`, `/ws/computer-use`

**Eylem Türleri:**

| Eylem | Açıklama |
|-------|----------|
| **click** | Mouse tıklama |
| **type** | Metin yazma |
| **hotkey** | Klavye kısayolu |
| **scroll** | Kaydırma |
| **move** | Mouse hareket |
| **drag** | Sürükle-bırak |

**Onay Modları:**

| Mod | Açıklama |
|-----|----------|
| **preview** | Sadece önizleme |
| **confirm_all** | Her eylem için onay |
| **confirm_risky** | Riskli eylemler için onay |
| **autonomous** | Tam otonom |

**Güvenlik:**
- Emergency Stop: `Ctrl+Shift+Esc`
- Rate Limiting: Max 60 action/minute
- Sandbox Mode: Test ortamı

### 8.3 Screen Sharing
**Dosya:** `api/vision_endpoints.py`  
**Endpoint:** `/ws/vision/stream`

| Ayar | Değer |
|------|-------|
| Quality | 10-100% |
| FPS | 1-30 |
| Format | JPEG, PNG |

### 8.4 VLM Integration
**Dosya:** `core/llm_manager.py`

| Özellik | Açıklama |
|---------|----------|
| Vision-Language Model | Görsel + metin sorgulama |
| Image Support | Base64, URL |
| Model | llama3.2-vision:11b |

---

## 9. Analitik ve Dashboard

### 9.1 User Analytics
**Dosya:** `api/analytics_endpoints.py`  
**Endpoint:** `/api/analytics/events`, `/api/analytics/sessions`

| Özellik | Açıklama |
|---------|----------|
| Event Logging | Olay kayıt |
| Session Tracking | Oturum takibi |
| User Behavior | Kullanıcı davranışı |

### 9.2 Productivity Insights
**Dosya:** `api/analytics_endpoints.py`  
**Endpoint:** `/api/analytics/productivity`, `/api/analytics/insights`

| Metrik | Açıklama |
|--------|----------|
| Active Time | Aktif kullanım süresi |
| Tasks Completed | Tamamlanan görevler |
| Efficiency Score | Verimlilik puanı |
| AI Insights | AI tavsiyeler |

### 9.3 Usage Trends
**Dosya:** `api/analytics_endpoints.py`  
**Endpoint:** `/api/analytics/trends`

| Analiz | Açıklama |
|--------|----------|
| Feature Usage | Özellik kullanımı |
| Time Patterns | Zaman kalıpları |
| Growth Metrics | Büyüme metrikleri |

### 9.4 Dashboard Aggregation
**Dosya:** `api/analytics_endpoints.py`  
**Endpoint:** `/api/analytics/dashboard`

| Widget | Açıklama |
|--------|----------|
| KPI Summary | Temel metrikler |
| Charts | Grafikler |
| Recent Activity | Son aktiviteler |
| Health Status | Sistem durumu |

### 9.5 System Health Dashboard
**Dosya:** `core/premium_features.py`

| Metrik | Açıklama |
|--------|----------|
| Uptime | Çalışma süresi |
| Error Rate | Hata oranı |
| Response Times | Yanıt süreleri |
| Health Score | Sağlık puanı (0-100) |

---

## 10. Ayarlar ve Yapılandırma

### 10.1 Health Endpoints
**Dosya:** `api/main.py`  
**Endpoint:** `/health`, `/health/live`, `/health/ready`

| Endpoint | Açıklama |
|----------|----------|
| `/health` | Genel sağlık kontrolü |
| `/health/live` | Kubernetes liveness |
| `/health/ready` | Kubernetes readiness |

### 10.2 Service Control
**Dosya:** `api/main.py`  
**Endpoint:** `/services/*`

| Servis | Endpoint |
|--------|----------|
| Ollama | `/services/ollama/start`, `/services/ollama/status` |
| ChromaDB | `/services/chromadb/status` |
| Next.js | `/services/nextjs/start`, `/services/nextjs/status` |

### 10.3 Configuration Management
**Dosya:** `core/config.py`

| Ayar | Açıklama |
|------|----------|
| Model Selection | Varsayılan model |
| GPU Settings | CUDA ayarları |
| Cache Settings | Önbellek ayarları |
| Rate Limits | İstek limitleri |

### 10.4 Plugin System
**Dosya:** `api/routers/plugins.py`  
**Endpoint:** `/api/plugins/*`

| Özellik | Açıklama |
|---------|----------|
| Discovery | Plugin keşfi |
| Enable/Disable | Aktif/Pasif |
| Configuration | Plugin ayarları |
| Hot Reload | Canlı yenileme |

---

## 11. Entegrasyon Özellikleri

### 11.1 MCP Server
**Dosya:** `api/mcp_endpoints.py`  
**Endpoint:** `/api/mcp/rpc`, `/api/mcp/resources`, `/api/mcp/tools`, `/ws/mcp`

| Özellik | Açıklama |
|---------|----------|
| JSON-RPC 2.0 | Haberleşme protokolü |
| Resource Provider | Kaynak sağlayıcı |
| Tool Provider | Araç sağlayıcı |
| Prompt Provider | Prompt sağlayıcı |
| Claude Desktop Config | Otomatik config oluşturma |

**Claude Desktop Entegrasyonu:**
```json
{
  "mcpServers": {
    "enterprise-ai": {
      "command": "python",
      "args": ["-m", "api.mcp_server"]
    }
  }
}
```

### 11.2 WebSocket Infrastructure

| Endpoint | Kullanım |
|----------|----------|
| `/ws/chat` | Streaming chat |
| `/ws/agent/{task_id}` | Agent task updates |
| `/ws/learning/journey/{id}` | Learning progress |
| `/ws/vision` | Vision streaming |
| `/ws/vision/stream` | Screen sharing |
| `/ws/workflows/{id}` | Workflow execution |
| `/ws/computer-use` | Desktop automation |
| `/ws/mcp` | MCP protocol |

### 11.3 SSE Streaming
**Dosya:** `api/main.py`

| Özellik | Açıklama |
|---------|----------|
| Chat Streaming | Token-by-token yanıt |
| Event Types | token, source, done, error |
| Retry Logic | Otomatik yeniden bağlanma |

### 11.4 Docker Support

| Dosya | Açıklama |
|-------|----------|
| `Dockerfile` | Backend container |
| `Dockerfile.frontend` | Frontend container |
| `docker-compose.yml` | Orchestration |

```bash
# Başlatma
docker-compose up -d

# Servislere erişim
# Backend: http://localhost:8001
# Frontend: http://localhost:3000
```

### 11.5 Browser Extension
**Dosya:** `browser-extension/`

| Özellik | Açıklama |
|---------|----------|
| Chrome Extension | Web entegrasyonu |
| Context Menu | Sağ tık menüsü |
| Text Selection | Seçili metin işleme |

---

## 12. Güvenlik Özellikleri

### 12.1 Code Security Scanner
**Dosya:** `api/security_endpoints.py`  
**Endpoint:** `/api/security/scan`, `/api/security/analyze`

| Kontrol | Açıklama |
|---------|----------|
| Vulnerability Scan | Zafiyet tarama |
| Static Analysis | Statik analiz |
| Secret Detection | Gizli bilgi algılama |
| OWASP/CWE | Standart kategoriler |

**Algılanan Zafiyetler:**
- SQL Injection
- XSS
- Path Traversal
- Command Injection
- Hardcoded Secrets

### 12.2 AI Code Review
**Dosya:** `api/security_endpoints.py`  
**Endpoint:** `/api/security/review`

| Özellik | Açıklama |
|---------|----------|
| AI-Powered Review | AI kod inceleme |
| Best Practices | İyi pratik önerileri |
| Severity Levels | Critical, High, Medium, Low |

### 12.3 Dependency Check
**Dosya:** `api/security_endpoints.py`  
**Endpoint:** `/api/security/dependencies`

| Özellik | Açıklama |
|---------|----------|
| Known Vulnerabilities | Bilinen zafiyetler |
| Version Check | Güncel versiyon kontrolü |
| CVE Database | CVE veritabanı sorgusu |

### 12.4 Rate Limiting
**Dosya:** `api/main.py`

| Endpoint | Limit |
|----------|-------|
| `/api/chat` | 60/dakika |
| `/api/chat/stream` | 30/dakika |
| `/api/agent/tasks` | 20/dakika |
| Varsayılan | 100/dakika |

---

## 13. Frontend Bileşenleri

### 13.1 Ana Sayfalar

| Sayfa | Dosya | Açıklama |
|-------|-------|----------|
| **ChatPage** | `ChatPage.tsx` | Ana sohbet arayüzü |
| **DashboardPage** | `DashboardPage.tsx` | Genel görünüm |
| **DocumentsPage** | `DocumentsPage.tsx` | Doküman yönetimi |
| **FavoritesPage** | `FavoritesPage.tsx` | Favoriler |
| **HistoryPage** | `HistoryPage.tsx` | Sohbet geçmişi |
| **LearningPage** | `LearningPage.tsx` | Öğrenme merkezi |
| **NotesPage** | `NotesPage.tsx` | Notlar |
| **SearchPage** | `SearchPage.tsx` | Arama |
| **SettingsPage** | `SettingsPage.tsx` | Ayarlar |
| **TemplatesPage** | `TemplatesPage.tsx` | Şablonlar |

### 13.2 Premium Paneller

| Panel | Dosya | Açıklama |
|-------|-------|----------|
| **AgentMarketplacePanel** | `AgentMarketplacePanel.tsx` | Ajan mağazası |
| **AIMemoryPanel** | `AIMemoryPanel.tsx` | AI bellek yönetimi |
| **AnalyticsDashboard** | `AnalyticsDashboard.tsx` | Analitik |
| **AutonomousAgentPanel** | `AutonomousAgentPanel.tsx` | Otonom ajan |
| **CodeInterpreterPanel** | `CodeInterpreterPanel.tsx` | Kod çalıştırma |
| **FullMetaPanel** | `FullMetaPanel.tsx` | Full Meta öğrenme |
| **KnowledgeGraphPanel** | `KnowledgeGraphPanel.tsx` | Bilgi grafiği |
| **SecurityScannerPanel** | `SecurityScannerPanel.tsx` | Güvenlik tarama |
| **VoiceAIPanel** | `VoiceAIPanel.tsx` | Sesli asistan |
| **WorkflowOrchestratorPanel** | `WorkflowOrchestratorPanel.tsx` | Workflow builder |

### 13.3 Öğrenme Bileşenleri

| Bileşen | Dosya | Açıklama |
|---------|-------|----------|
| **AIThinkingView** | `AIThinkingView.tsx` | AI düşünme görselleştirme |
| **CertificateView** | `CertificateView.tsx` | Sertifika görünümü |
| **DeepScholarCreator** | `DeepScholarCreator.tsx` | Akademik doküman |
| **ExamView** | `ExamView.tsx` | Sınav arayüzü |
| **JourneyCreationWizard** | `JourneyCreationWizard.tsx` | Yolculuk oluşturma |
| **PackageView** | `PackageView.tsx` | Paket görünümü |
| **StageMapV2** | `StageMapV2.tsx` | Aşama haritası |

### 13.4 UI Bileşenleri

| Bileşen | Dosya | Açıklama |
|---------|-------|----------|
| **ComputerUsePanel** | `ComputerUsePanel.tsx` | Masaüstü kontrolü |
| **VisionPanel** | `VisionPanel.tsx` | Görüntü analizi |
| **ErrorBoundary** | `ErrorBoundary.tsx` | Hata yakalama |
| **FloatingWidget** | `FloatingWidget.tsx` | Yüzen widget |
| **WidgetWrapper** | `WidgetWrapper.tsx` | Widget kapsayıcı |
| **KeyboardShortcutsModal** | `KeyboardShortcutsModal.tsx` | Klavye kısayolları |
| **Sidebar** | `Sidebar.tsx` | Yan menü |
| **ModelBadge** | `ModelBadge.tsx` | Model göstergesi |
| **Toaster** | `Toaster.tsx` | Bildirimler |

### 13.5 Klavye Kısayolları

| Kısayol | Eylem |
|---------|-------|
| `Ctrl + ?` | Kısayolları göster |
| `Ctrl + K` | Hızlı arama |
| `Ctrl + N` | Yeni sohbet |
| `Ctrl + ,` | Ayarlar |
| `Ctrl + Shift + T` | Tema değiştir |
| `Ctrl + 1` | Sohbet sayfası |
| `Ctrl + 2` | Geçmiş |
| `Ctrl + 3` | Notlar |
| `Ctrl + 4` | Dokümanlar |
| `Ctrl + 5` | Öğrenme |

---

## 14. Teknik Altyapı

### 14.1 Proje Yapısı

```
AgenticManagingSystem/
├── api/                    # FastAPI endpoints
│   ├── main.py            # Ana uygulama
│   ├── routers/           # API router'ları
│   └── *_endpoints.py     # Özellik endpoint'leri
├── agents/                 # Ajan modülleri
│   ├── orchestrator.py    # Ajan koordinasyonu
│   └── *_agent.py         # Ajan implementasyonları
├── core/                   # Temel modüller
│   ├── llm_manager.py     # LLM yönetimi
│   ├── vector_store.py    # Vektör deposu
│   └── premium_*.py       # Premium özellikler
├── rag/                    # RAG sistemi
│   ├── advanced_rag.py    # Gelişmiş RAG
│   └── hybrid_search.py   # Hybrid arama
├── tools/                  # Araçlar
│   ├── tool_manager.py    # Araç yönetimi
│   └── *_tool.py          # Araç implementasyonları
├── frontend-next/          # Next.js frontend
│   └── src/
│       ├── app/           # Sayfalar
│       ├── components/    # Bileşenler
│       └── store/         # State yönetimi
├── plugins/                # Plugin sistemi
├── tests/                  # Test dosyaları
├── data/                   # Veri dosyaları
├── logs/                   # Log dosyaları
├── blobs/                  # Binary dosyalar
├── Dockerfile              # Backend container
├── Dockerfile.frontend     # Frontend container
├── docker-compose.yml      # Orchestration
├── requirements.txt        # Python bağımlılıkları
└── run.py                  # Başlatma scripti
```

### 14.2 API Yapısı

```
/api
├── /chat                   # Sohbet
├── /routing                # Model yönlendirme
├── /voice                  # Sesli asistan
├── /memory                 # AI bellek
├── /documents              # Dokümanlar
├── /rag                    # RAG sistemi
├── /premium                # Premium özellikler
├── /agent                  # Ajan sistemi
├── /agents                 # Agent marketplace
├── /learning               # Öğrenme V1
├── /journey/v2             # Öğrenme V2
├── /full-meta              # Full Meta
├── /deep-scholar           # Akademik yazım
├── /workflows              # Workflow builder
├── /code                   # Kod çalıştırma
├── /vision                 # Görüntü analizi
├── /computer-use           # Masaüstü kontrolü
├── /analytics              # Analitik
├── /security               # Güvenlik
├── /mcp                    # MCP protokolü
├── /plugins                # Plugin sistemi
├── /knowledge-graph        # Bilgi grafiği
├── /multimodal             # Multi-modal RAG
└── /services               # Servis kontrolü
```

### 14.3 Veritabanı Yapısı

**ChromaDB Collections:**
- `documents` - Ana doküman koleksiyonu
- `conversations` - Sohbet geçmişi
- `user_memories` - Kullanıcı bellekleri
- `learning_content` - Öğrenme içerikleri
- `knowledge_graph` - Bilgi grafiği

**SQLite Tabloları:**
- `sessions` - Sohbet oturumları
- `tasks` - Arka plan görevleri
- `analytics_events` - Analitik olaylar
- `learning_progress` - Öğrenme ilerlemesi
- `certificates` - Sertifikalar

### 14.4 Ortam Değişkenleri

```env
# LLM Ayarları
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=qwen2.5:7b
BACKUP_MODEL=gemma3:4b
VISION_MODEL=llama3.2-vision:11b

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# API
API_HOST=0.0.0.0
API_PORT=8001

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001

# Güvenlik
API_KEY=your-api-key
RATE_LIMIT_PER_MINUTE=100

# Cache
CACHE_TTL_HOURS=2
MAX_CACHE_SIZE=1000
```

### 14.5 Başlatma

```bash
# Geliştirme
python run.py

# Sadece Backend
python run.py --skip-frontend

# Sadece API
python run.py --api-only

# Test ile başlat
python run.py --test

# Docker
docker-compose up -d
```

---

## 📊 Özet Tablo

| Kategori | Özellik Sayısı | Ana Teknolojiler |
|----------|----------------|------------------|
| **Sohbet & Konuşma** | 8 | LLM, Voice AI, Memory |
| **RAG & Doküman** | 12 | HyDE, Hybrid Search, Rerank |
| **Ajan Sistemi** | 10 | Orchestrator, Multi-Agent Teams |
| **Öğrenme V1** | 5 | XP/Stars, Streaks, Stage Map |
| **Öğrenme V2** | 7 | Feynman, Certificates, Full Meta |
| **Premium** | 12 | Knowledge Graph, Workflow, Deep Scholar |
| **Vision & Computer Use** | 4 | VLM, Desktop Automation |
| **Analitik** | 5 | Productivity, Health Dashboard |
| **Ayarlar** | 4 | Health Probes, Plugins |
| **Entegrasyon** | 5 | MCP, WebSocket, Docker |
| **Güvenlik** | 4 | Security Scanner, Rate Limiting |
| **TOPLAM** | **77+** | |

---

> **Not:** Bu dökümantasyon, Enterprise AI Assistant projesinin tüm özelliklerini kapsar. Her özellik aktif olarak geliştirilmekte ve iyileştirilmektedir.

---

*Son güncelleme: 23 Ocak 2026*
