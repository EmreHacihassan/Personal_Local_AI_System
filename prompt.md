# 🤖 ENTERPRISE AI ASSISTANT - KAPSAMLI PROJE DOKÜMANTASYONU

> **Versiyon:** 1.0.0  
> **Başlangıç Tarihi:** 10 Ocak 2026  
> **Proje Kodu:** EAA-2026  
> **Durum:** Geliştirme Aşamasında  
> **Standart:** ENDÜSTRİ STANDARTLARINDA KURUMSAL YAZILIM

---

## 🏆 ENDÜSTRİ STANDARTLARI UYUMLULUK BELGESİ

Bu proje, aşağıdaki endüstri standartlarına ve en iyi uygulamalara tam uyumlu olarak tasarlanmış ve geliştirilmektedir:

### Yazılım Mühendisliği Standartları
- **ISO/IEC 25010** - Yazılım kalite modeli ve değerlendirme
- **ISO/IEC 12207** - Yazılım yaşam döngüsü süreçleri
- **IEEE 830** - Yazılım gereksinim spesifikasyonları
- **SOLID Prensipleri** - Nesne yönelimli tasarım ilkeleri
- **Clean Architecture** - Katmanlı ve bağımsız mimari yapı
- **12-Factor App** - Modern uygulama geliştirme metodolojisi

### Veri Güvenliği ve Gizlilik Standartları
- **KVKK** - Kişisel Verilerin Korunması Kanunu tam uyumlu
- **GDPR** - Avrupa Birliği Genel Veri Koruma Yönetmeliği uyumlu
- **ISO 27001** - Bilgi güvenliği yönetim sistemi prensipleri
- **SOC 2 Type II** - Güvenlik, erişilebilirlik ve gizlilik kontrolleri
- **Zero Trust Architecture** - Sıfır güven güvenlik modeli

### AI/ML Endüstri Standartları
- **MLOps Best Practices** - Makine öğrenmesi operasyonları
- **Responsible AI Guidelines** - Sorumlu yapay zeka ilkeleri
- **Model Cards** - Model dokümantasyon standardı
- **AI Ethics Framework** - Yapay zeka etik çerçevesi

### Kurumsal Yazılım Standartları
- **Enterprise Integration Patterns** - Kurumsal entegrasyon kalıpları
- **RESTful API Design Guidelines** - API tasarım standartları
- **OpenAPI 3.0** - API spesifikasyon standardı
- **Semantic Versioning 2.0** - Sürüm numaralandırma standardı

---

## 📋 İÇİNDEKİLER

1. Proje Özeti
2. Problem Tanımı
3. Çözüm Vizyonu
4. Hedef Kitle
5. Teknik Mimari
6. Agent Sistemi
7. RAG Sistemi
8. MCP Entegrasyonu
9. Tool Sistemi
10. API Tasarımı
11. Frontend Tasarımı
12. Veritabanı Şeması
13. Güvenlik
14. Deployment
15. Kullanım Senaryoları
16. Proje Yapısı
17. Geliştirme Yol Haritası
18. Test Stratejisi
19. Performans Hedefleri
20. Maliyet Analizi

---

## 1. PROJE ÖZETİ

### 1.1 Proje Adı
**Enterprise AI Assistant (EAA)** - Kurumsal Yapay Zeka Asistanı

### 1.2 Tek Cümlelik Tanım
Şirketlerin tüm kurumsal bilgi yönetimi, döküman işleme ve iş akışı otomasyonunu tek bir AI platformunda birleştiren, **tamamen local çalışan**, veri güvenliği odaklı, multi-agent tabanlı akıllı asistan sistemi.

### 1.3 Temel Değer Önerisi

**🔐 %100 LOCAL** → Veri şirketten ASLA çıkmaz  
**🧠 MULTI-AGENT** → Uzmanlaşmış AI ekibi  
**📄 UNIVERSAL RAG** → Her format desteklenir  
**🔧 MCP TOOLS** → Genişletilebilir tool sistemi  
**💰 SIFIR CLOUD** → Aylık API maliyeti YOK  
**🚀 HIZLI KURULUM** → 30 dakikada çalışır durumda

### 1.4 Proje Motivasyonu
- Şirketlerin %78'i kurumsal bilgiye erişimde zorluk yaşıyor
- Cloud AI çözümleri veri güvenliği endişesi yaratıyor
- Mevcut çözümler pahalı ve karmaşık
- Local LLM'ler artık production-ready kalitede

### 1.5 Başarı Kriterleri

| Metrik | Hedef |
|--------|-------|
| Yanıt süresi | < 3 saniye |
| Doğruluk oranı | > %90 |
| Kullanıcı memnuniyeti | > %85 |
| Uptime | %99.5 |
| Döküman işleme | < 5 sn/sayfa |

---

## 2. PROBLEM TANIMI

### 2.1 Kurumsal Bilgi Yönetimi Sorunları

#### 2.1.1 Bilgi Dağınıklığı
Tipik bir şirkette bilgi birçok farklı sistemde dağılmış durumdadır:
- Email sistemleri (Outlook, Gmail)
- Mesajlaşma platformları (Slack, Teams, Discord)
- Dosya depolama servisleri (Drive, Dropbox, SharePoint)
- Not alma uygulamaları (Notion, OneNote, Obsidian)
- Tablolar (Excel, Google Sheets)
- Dökümanlar (Word, PDF, PowerPoint)
- CRM sistemleri (Salesforce, HubSpot)
- Proje yönetimi araçları (Jira, Asana, Trello)
- Legacy sistemler (ERP, özel yazılımlar)

**SONUÇ:** Çalışanlar haftada ortalama 9.3 saat bilgi aramakla geçiriyor!

#### 2.1.2 Kurumsal Hafıza Kaybı
- Deneyimli çalışan ayrıldığında bilgi kayboluyor
- "Bu nasıl yapılıyordu?" sorusu sürekli tekrarlanıyor
- Aynı hatalar tekrar ediliyor
- Best practice'ler kaybolıyor

#### 2.1.3 Verimsiz Onboarding
- Yeni çalışan 3-6 ay "öğrenme" modunda
- Sürekli aynı sorular soruluyor
- Mentor zamanı verimsiz kullanılıyor
- Dökümanlar güncel değil veya bulunamıyor

#### 2.1.4 Döküman İşleme Yükü
- Manuel özet çıkarma
- Sözleşme analizi saatler sürüyor
- Rapor hazırlama zaman alıyor
- Veri girişi tekrarlı ve hatalı

### 2.2 Mevcut Çözümlerin Eksiklikleri

#### 2.2.1 Cloud AI Çözümleri (ChatGPT, Claude, Gemini)
**Sorunlar:**
- Veri güvenliği riski (veriler cloud'a gidiyor)
- KVKK/GDPR uyumluluk sorunları
- Aylık yüksek API maliyetleri ($100-10,000+)
- İnternet bağımlılığı
- Şirkete özel bilgi yok (genel model)
- Rate limiting ve downtime

#### 2.2.2 Enterprise Arama Çözümleri
**Sorunlar:**
- Sadece keyword-based arama
- Semantic anlama yok
- Soru-cevap yapamıyor
- İçerik üretemiyor
- Pahalı lisans maliyetleri
- Karmaşık kurulum

#### 2.2.3 Geleneksel Chatbot'lar
**Sorunlar:**
- Rule-based, esnek değil
- Doğal dil anlama zayıf
- Karmaşık sorularda başarısız
- Sürekli bakım gerektiriyor
- Kullanıcı deneyimi kötü

### 2.3 Problem Özeti Matrisi

| Problem | Etki | Mevcut Çözüm | Bizim Çözümümüz |
|---------|------|--------------|-----------------|
| Bilgi dağınıklığı | Yüksek | Manuel arama | Unified RAG |
| Hafıza kaybı | Kritik | Dökümentasyon | AI Knowledge Base |
| Yavaş onboarding | Orta | Mentor sistemi | AI Asistan |
| Döküman işleme | Yüksek | Manuel işlem | Auto-analysis |
| Veri güvenliği | Kritik | Cloud trust | %100 Local |
| Yüksek maliyet | Orta | Budget limit | Sıfır API cost |

---

## 3. ÇÖZÜM VİZYONU

### 3.1 Ürün Vizyonu
"Her şirketin kendi **dijital beyni** - tüm kurumsal bilgiyi anlayan, analiz eden ve üzerine değer katan, güvenli ve uygun maliyetli AI asistan."

### 3.2 Çözüm Yaklaşımı

Sistem, katmanlı bir mimari ile tasarlanmıştır:

**Sunum Katmanı:** Web UI (Streamlit), REST API (FastAPI), Bot Entegrasyonları (Slack/Teams)

**Uygulama Katmanı:** Agent Orchestrator sistemi içinde Research Agent, Writer Agent, Analyzer Agent ve Assistant Agent'lar çalışır. Tool Manager üzerinden RAG Tool, File Tool, Web Search, Calendar Tool ve Custom Tool'lar yönetilir. MCP Server Layer ile Filesystem, Database, Memory ve Custom Server'lar entegre edilir.

**Veri Katmanı:** ChromaDB (Vectors, Embeddings, Indexes), SQLite (Metadata, Sessions, Analytics), File Store (Documents, Uploads, Cache)

**LLM Katmanı:** Ollama üzerinden Llama 3.2 (Primary Chat LLM), Mistral (Backup Model), nomic-embed-text (Embedding Model) çalıştırılır. Port: 11434

### 3.3 Temel Özellikler

#### 3.3.1 Akıllı Bilgi Erişimi
Kullanıcı doğal dille soru sorar, sistem soruyu anlar (semantic understanding), ilgili dökümanları bulur (RAG retrieval), bağlama göre yanıt üretir (LLM generation) ve kaynakları gösterir (transparency).

Örnek sorgu: "Şirketimizin uzaktan çalışma politikası nedir?"

Sistem yanıtı kaynak dökümanlarla birlikte sunar: HR_Politikalar_2025.pdf sayfa 12, Çalışan_El_Kitabı.docx bölüm 3.2 gibi referanslarla destekler.

#### 3.3.2 Multi-Agent İş Akışı
Karmaşık görevler birden fazla agent ile çözülür.

Örnek görev: "Q3 satış raporunu analiz et, önemli noktaları çıkar ve müdüre özet email hazırla"

İş akışı:
1. Research Agent → Q3 raporunu bulur
2. Analyzer Agent → Raporu analiz eder, key metrics çıkarır
3. Writer Agent → Profesyonel email taslağı hazırlar

#### 3.3.3 Universal Döküman Desteği
Desteklenen formatlar:
- PDF (text, OCR, tables)
- Word (.docx, .doc)
- Excel (.xlsx, .xls, .csv)
- PowerPoint (.pptx, .ppt)
- Text (.txt, .md, .rst)
- Web (.html, .xml)
- Email (.eml, .msg)
- JSON/YAML yapılandırma
- Görseller (OCR ile - opsiyonel)

#### 3.3.4 Proaktif Asistan
Sistem sadece soru cevaplamaz, proaktif öneriler de sunar:
- **Daily Digest:** Önemli güncellemelerin özeti
- **Deadline Alerts:** Yaklaşan deadline hatırlatmaları
- **Knowledge Gaps:** Eksik döküman tespiti
- **Duplicate Detection:** Tekrar eden bilgi uyarısı
- **Trend Analysis:** Sık sorulan konular raporu

### 3.4 Diferansiyasyon Faktörleri

| Özellik | Rakipler | Bizim Çözümümüz |
|---------|----------|-----------------|
| Veri lokasyonu | Cloud | %100 Local |
| API maliyeti | $100-10K/ay | $0 |
| Kurulum süresi | Haftalar | 30 dakika |
| Özelleştirme | Sınırlı | Tam kontrol |
| Güncelleme | Vendor bağımlı | Bağımsız |
| Offline çalışma | Hayır | Evet |
| Multi-agent | Basit | Gelişmiş |
| MCP desteği | Yok | Var |

---

## 4. HEDEF KİTLE

### 4.1 Birincil Hedef: KOBİ'ler (10-500 çalışan)

#### 4.1.1 Neden KOBİ'ler?
- IT departmanı küçük/yok  Basit çözüm arıyorlar
- Bütçe sınırlı  Cloud AI'a para veremiyorlar
- Veri hassasiyeti  Müşteri verilerini cloud'a yükleyemiyorlar
- Hızlı karar  Enterprise satış döngüsü yok
- Büyüme odaklı  Verimlilik araçlarına açıklar

#### 4.1.2 Hedef Sektörler
**Öncelikli Sektörler:**
- Hukuk büroları (sözleşme analizi)
- Muhasebe firmaları (döküman işleme)
- Sağlık kuruluşları (hasta verileri - KVKK)
- Üretim şirketleri (teknik dökümanlar)
- E-ticaret (müşteri hizmetleri)
- Eğitim kurumları (bilgi yönetimi)

### 4.2 İkincil Hedef: Departmanlar

#### 4.2.1 HR Departmanları
Kullanım alanları: Çalışan politikası sorguları, onboarding asistanı, CV tarama ve analiz, performans raporu analizi, eğitim içeriği oluşturma

#### 4.2.2 Legal/Hukuk Departmanları
Kullanım alanları: Sözleşme analizi ve karşılaştırma, mevzuat takibi, due diligence desteği, risk analizi, döküman hazırlama

#### 4.2.3 Satış Ekipleri
Kullanım alanları: Müşteri bilgisi sorgulama, teklif hazırlama desteği, rakip analizi, satış raporu özeti, email taslakları

### 4.3 Kullanıcı Personaları

#### Persona 1: Ayşe - HR Müdürü
**Profil:** 35 yaşında, 80 çalışanlı teknoloji firmasında çalışıyor, orta düzey teknik bilgiye sahip. Günlük zorluğu aynı soruları tekrar tekrar cevaplamak.

**İhtiyaçlar:** "İzin politikamız ne?" sorularına otomatik cevap, yeni çalışan için döküman paketi hazırlama, CV'leri hızlıca tarama, çalışan el kitabını güncel tutma.

**Başarı Kriteri:** Haftada 10+ saat tasarruf

#### Persona 2: Mehmet - Avukat
**Profil:** 42 yaşında, 15 kişilik hukuk bürosunda çalışıyor, düşük teknik bilgiye sahip. Günlük zorluğu sözleşmelerde kritik maddeleri kaçırma korkusu.

**İhtiyaçlar:** Sözleşmeleri hızlıca analiz etme, geçmiş davalarda emsal arama, mevzuat değişikliklerini takip, müvekkil verilerini güvende tutma (cloud'a yükleyemez!).

**Başarı Kriteri:** Sözleşme inceleme süresini %70 azaltma

#### Persona 3: Zeynep - Operasyon Yöneticisi
**Profil:** 38 yaşında, 200 çalışanlı üretim firmasında çalışıyor, orta düzey teknik bilgiye sahip. Günlük zorluğu teknik dökümanları bulmak ve anlamak.

**İhtiyaçlar:** Makine kılavuzlarında hızlı arama, prosedür dökümanlarına kolay erişim, arıza çözüm önerilerini bulma, yeni personele bilgi aktarımı.

**Başarı Kriteri:** Problem çözme süresini %50 kısaltma

---

## 5. TEKNİK MİMARİ

### 5.1 Sistem Bileşenleri

Sistem dört ana katmandan oluşur:

**1. Presentation Layer (Sunum Katmanı)**
- Web UI: Streamlit üzerinde çalışır, Port 8501
- REST API: FastAPI ile geliştirilir, Port 8000
- Bot Entegrasyonları: Slack/Teams webhook'ları

**2. Application Layer (Uygulama Katmanı)**
- Agent Orchestrator: Research, Writer, Analyzer, Assistant agent'ları yönetir
- Tool Manager: RAG, File, Web Search, Calendar ve Custom tool'ları koordine eder
- MCP Server Layer: Filesystem, Database, Memory ve Custom server'lar

**3. Data Layer (Veri Katmanı)**
- ChromaDB: Vector'ler, embedding'ler ve index'ler
- SQLite: Metadata, session'lar ve analytics
- File Store: Dökümanlar, upload'lar ve cache

**4. LLM Layer (Dil Modeli Katmanı)**
- Ollama runtime, Port 11434
- Primary: Llama 3.2 8B/70B
- Backup: Mistral 7B/8x7B
- Embedding: nomic-embed-text

### 5.2 Teknoloji Stack

#### 5.2.1 Backend
- **Runtime:** Python 3.11+, asyncio, uvloop
- **Frameworks:** FastAPI 0.109+, Pydantic 2.5+
- **LLM Provider:** Ollama
- **Models:** llama3.2:8b (primary), mistral:7b (backup), nomic-embed-text (embeddings)
- **Agent Framework:** CrewAI (primary), LangGraph (alternative)
- **RAG:** LangChain, ChromaDB, RecursiveCharacterTextSplitter
- **MCP:** anthropic-mcp-sdk, filesystem/sqlite/memory servers

#### 5.2.2 Frontend
- **Primary UI:** Streamlit 1.30+, Custom CSS, streamlit-chat, streamlit-option-menu
- **Alternative:** Gradio (lighter option)
- **Future:** React + TypeScript, TailwindCSS

#### 5.2.3 Data Storage
- **Vector Database:** ChromaDB, local disk persistence, cosine similarity
- **Relational:** SQLite, SQLAlchemy (optional)
- **File Storage:** Local filesystem, date/type organized
- **Cache:** Local cache, LRU strategy

### 5.3 Data Flow

Veri akışı altı adımda gerçekleşir:

1. **Input Parsing:** Kullanıcı girdisi doğrulanır, temizlenir ve sınıflandırılır
2. **Task Planning:** Görev analiz edilir, parçalara ayrılır ve uygun agent'a yönlendirilir
3. **Tool Execution:** RAG tool ile embedding ve vector search yapılır, diğer tool'lar (file ops, web search, calendar) çalıştırılır
4. **Context Build:** Sonuçlar birleştirilir, context formatlanır, metadata eklenir
5. **LLM Generation:** System prompt, context ve user query ile yanıt üretilir
6. **Post-Process:** Output formatlanır, kaynaklar eklenir, analytics loglanır

### 5.4 Sistem Gereksinimleri

#### 5.4.1 Minimum Gereksinimler
- CPU: 4 cores
- RAM: 16 GB
- Storage: 50 GB SSD
- GPU: Not required (CPU inference)
- OS: Windows 10/11, Ubuntu 20.04+, macOS 12+

#### 5.4.2 Önerilen Gereksinimler
- CPU: 8+ cores
- RAM: 32 GB
- Storage: 100 GB NVMe SSD
- GPU: NVIDIA RTX 3060+ (8GB+ VRAM) - Optional
- OS: Ubuntu 22.04 LTS

#### 5.4.3 Enterprise Gereksinimler
- CPU: 16+ cores (AMD EPYC / Intel Xeon)
- RAM: 64 GB+
- Storage: 500 GB+ NVMe SSD
- GPU: NVIDIA RTX 4090 / A100 (for faster inference)
- OS: Ubuntu 22.04 LTS Server

---

## 6. AGENT SİSTEMİ

### 6.1 Agent Mimarisi

Sistem hiyerarşik bir multi-agent yapısına sahiptir:

**Orchestrator (Merkez Yönetici)**
- Task analysis: Gelen görevleri analiz eder
- Agent routing: Uygun agent'a yönlendirir
- Flow control: İş akışını kontrol eder
- Result merge: Sonuçları birleştirir

**Research Agent (Araştırma Uzmanı)**
- Role: Bilgi arama ve toplama
- Tools: RAG Search, Web Search, DB Query
- Capabilities: Semantic search, multi-source aggregation

**Writer Agent (İçerik Yazarı)**
- Role: İçerik üretimi ve yazım
- Tools: File Write, Format Tool, Template
- Capabilities: Email draft, report write, doc generate, translate

**Analyzer Agent (Veri Analisti)**
- Role: Veri analizi ve insight
- Tools: RAG Search, Data Tool, Math Tool
- Capabilities: Summarize, compare, extract, trend detect

**Assistant Agent (Genel Asistan)**
- Role: Kullanıcı ile etkileşim
- Capabilities: Q&A, task routing, clarification, help

### 6.2 Agent Tanımları

#### 6.2.1 Research Agent
**İsim:** Research Agent  
**Rol:** Araştırma Uzmanı  
**Hedef:** Şirket bilgi tabanında kapsamlı ve doğru araştırma yapmak

**Arka Plan:** Şirketin tüm dökümanlarına, veri tabanlarına ve bilgi kaynaklarına hakim bir araştırma uzmanıdır. Yıllardır bu şirkette çalışıyor ve her türlü bilginin nerede olduğunu bilir. Araştırma yaparken önce en güncel kaynaklara bakar, birden fazla kaynağı çapraz kontrol eder, bulamadığı bilgiyi açıkça belirtir ve kaynakları her zaman gösterir.

**Araçlar:** rag_search (Vector DB arama), web_search (İnternet araması - opsiyonel), db_query (SQL sorguları), file_search (Dosya sistemi arama)

**Kısıtlamalar:** Sadece doğrulanmış bilgi ver, kaynak göstermeden bilgi verme, tahmin yapmak yerine "bilmiyorum" de, gizli/hassas verilere dikkat et

#### 6.2.2 Writer Agent
**İsim:** Writer Agent  
**Rol:** İçerik Yazarı  
**Hedef:** Profesyonel, etkili ve amaca uygun içerikler üretmek

**Arka Plan:** Deneyimli bir kurumsal içerik yazarıdır. Her türlü iş yazışmasında, rapor hazırlamada ve döküman oluşturmada uzmandır. Yazarken hedef kitleye uygun ton kullanır, net ve anlaşılır olur, profesyonel standartlara uyar, gramer ve imla hatası yapmaz.

**Araçlar:** file_write (Dosya yazma), format_tool (Markdown/HTML formatlama), template_tool (Template kullanımı), translate_tool (Çeviri - opsiyonel)

**Çıktı Tipleri:** email_draft, report, summary, proposal, documentation, presentation

**Ton Seçenekleri:** formal (resmi), friendly (samimi), technical (teknik), persuasive (ikna edici)

#### 6.2.3 Analyzer Agent
**İsim:** Analyzer Agent  
**Rol:** Veri Analisti  
**Hedef:** Dökümanları ve verileri analiz ederek değerli içgörüler çıkarmak

**Arka Plan:** Analitik düşünen, detaycı bir veri analistidir. Karmaşık dökümanlardan önemli bilgileri çıkarır, trendleri tespit eder ve anlamlı özetler hazırlar. Analiz yaparken önce genel resme bakar, kritik noktaları belirler, sayısal verileri yorumlar ve önerilerde bulunur.

**Araçlar:** rag_search (Bilgi arama), data_analysis (Veri analizi), math_tool (Hesaplama), chart_tool (Grafik oluşturma - opsiyonel)

**Analiz Tipleri:** summarization (özetleme), comparison (karşılaştırma), extraction (bilgi çıkarma), trend_analysis (trend analizi), risk_assessment (risk değerlendirme), gap_analysis (eksik analizi)

#### 6.2.4 Assistant Agent
**İsim:** Assistant Agent  
**Rol:** Genel Asistan  
**Hedef:** Kullanıcılara her konuda yardımcı olmak ve doğru yönlendirmek

**Arka Plan:** Yardımsever, sabırlı ve bilgili bir asistan. Kullanıcının ihtiyaçlarını anlar, sorularını yanıtlar ve gerektiğinde diğer uzmanlara yönlendirir. Her zaman nazik ve profesyonel olur, soruyu tam anlamaya çalışır, belirsiz durumlarda ek soru sorar ve en uygun çözümü sunar.

**Araçlar:** rag_search (Temel arama), task_router (Diğer agent'lara yönlendirme)

**Yetenekler:** general_qa (Genel soru-cevap), task_routing (Görev yönlendirme), clarification (Netleştirme), help_guide (Yardım rehberi), small_talk (Basit sohbet)

### 6.3 Agent Collaboration Patterns

#### Pattern 1: Sequential (Sıralı)
Görev: "Satış raporunu analiz et ve özet email hazırla"

Akış: Research Agent  Analyzer Agent  Writer Agent

Adımlar: Dökümanları bul  Analiz et ve özetle  Email taslağı yaz

#### Pattern 2: Parallel (Paralel)
Görev: "Tüm departman raporlarını özetle"

Akış: Research Agent paralel olarak HR, Sales ve Ops analiz agent'larına dağıtır, sonuçlar Writer Agent'ta birleştirilir.

#### Pattern 3: Hierarchical (Hiyerarşik)
Görev: Karmaşık multi-step işlem

Akış: Orchestrator (Master)  Research/Analyzer/Writer (Sub-agents)  Final Output

### 6.4 Agent Communication Protocol

Agent'lar arası iletişim standart bir mesaj formatı ile gerçekleşir:

**Mesaj Bileşenleri:**
- message_id: Benzersiz tanımlayıcı (UUID)
- timestamp: Zaman damgası (ISO8601)
- sender: Gönderen agent bilgisi (name, role)
- recipient: Alıcı bilgisi (agent_name veya 'orchestrator' veya 'user')
- message_type: Mesaj tipi (request, response, status, error)
- content: İçerik (task, context, data, sources)
- metadata: Ek bilgiler (priority, requires_response, timeout)

---

## 7. RAG SİSTEMİ

### 7.1 RAG Pipeline

RAG sistemi üç ana pipeline'dan oluşur:

**1. Indexing Pipeline (İndeksleme)**
Document Input  Parse/Extract  Chunk/Split  Embed Vectors  Store (ChromaDB)

**2. Retrieval Pipeline (Getirme)**
User Query  Embed Query  Search Vector  Rerank/Filter  Context Builder

**3. Generation Pipeline (Üretim)**
Context + Query  Prompt Build  LLM Generate  Output Format

### 7.2 Document Processing

#### 7.2.1 Desteklenen Formatlar

**PDF İşleme:**
- Loader: PyPDFLoader
- Özellikler: text, tables, images_ocr
- Fallback: pdfplumber

**Microsoft Office:**
- DOCX: python-docx ile text, tables, styles
- XLSX: openpyxl ile sheets, tables, formulas
- PPTX: python-pptx ile slides, notes, text

**Text Formatları:**
- TXT: TextLoader
- MD: MarkdownLoader
- CSV: CSVLoader
- JSON: JSONLoader

**Web Formatları:**
- HTML: BSHTMLLoader
- XML: XMLLoader

**Email:**
- EML: UnstructuredEmailLoader

#### 7.2.2 Chunking Stratejisi

**Default Chunking:**
- Method: RecursiveCharacterTextSplitter
- Chunk size: 1000 karakter
- Overlap: 200 karakter
- Separators: paragraf, satır, cümle, kelime, karakter

**Code Chunking:**
- Method: CodeSplitter
- Chunk size: 1500 karakter
- Diller: Python, JavaScript, SQL

**Markdown Chunking:**
- Method: MarkdownHeaderTextSplitter
- Header'lara göre bölme: H1, H2, H3

**Semantic Chunking:**
- Method: SemanticChunker
- Breakpoint threshold: 0.5

#### 7.2.3 Metadata Extraction

Her döküman chunk'ı için çıkarılan metadata:
- source: Dosya adı/yolu
- file_type: Dosya uzantısı
- created_at: Oluşturulma tarihi
- modified_at: Son değişiklik tarihi
- author: Yazar (varsa)
- title: Başlık (varsa)
- page_number: Sayfa numarası (varsa)
- section: Bölüm (varsa)
- chunk_index: Chunk sırası
- total_chunks: Toplam chunk sayısı
- word_count: Kelime sayısı
- language: Dil
- department: Departman (manual tag)
- category: Kategori (manual tag)
- access_level: Erişim seviyesi (public, internal, confidential)

### 7.3 Vector Store Configuration

**Engine:** ChromaDB  
**Persistence:** ./data/chroma_db  

**Collection Settings:**
- Name: enterprise_knowledge
- HNSW space: cosine
- Construction EF: 100
- Search EF: 50

**Embedding Config:**
- Model: nomic-embed-text
- Dimension: 768
- Normalize: True

**Index Settings:**
- Batch size: 100
- Show progress: True

### 7.4 Retrieval Strategies

#### 7.4.1 Basic Semantic Search
Query embedding oluşturulur ve vector database'de cosine similarity ile en yakın sonuçlar getirilir.

#### 7.4.2 Hybrid Search (Semantic + Keyword)
Semantic sonuçlar ve BM25 (keyword) sonuçları Reciprocal Rank Fusion ile birleştirilir. Alpha parametresi semantic ağırlığını belirler (0-1 arası).

#### 7.4.3 Multi-Query Retrieval
LLM ile sorgunun farklı varyasyonları üretilir, her varyasyon için ayrı arama yapılır, sonuçlar deduplicate edilir ve ilgililik skoruna göre sıralanır.

#### 7.4.4 Contextual Compression
Daha fazla döküman getirilir, LLM ile her dökümanın sadece sorguyla ilgili kısımları çıkarılır, boş olmayan sonuçlar döndürülür.

---

## 8. MCP ENTEGRASYONU

### 8.1 MCP Nedir?
Model Context Protocol (MCP), Anthropic tarafından geliştirilen, AI modellerinin harici araçlar ve veri kaynaklarıyla standart bir şekilde etkileşim kurmasını sağlayan açık protokoldür.

### 8.2 MCP Server'lar

**Filesystem Server:** Dosya sistemi işlemleri (okuma, yazma, listeleme, arama)

**Database Server:** SQLite veritabanı işlemleri (sorgu, insert, update, delete)

**Memory Server:** Kısa süreli bellek yönetimi (session state, conversation history)

**Custom Servers:** Şirkete özel entegrasyonlar (CRM, ERP, özel API'ler)

### 8.3 MCP Avantajları
- Standart protokol ile tool ekleme kolaylığı
- Güvenli ve kontrollü erişim
- Genişletilebilir mimari
- Community tarafından geliştirilen server'lar

---

## 9. TOOL SİSTEMİ

### 9.1 Core Tools

**RAG Search Tool:** Vector database'de semantic arama yapar

**File Operations Tool:** Dosya okuma, yazma, listeleme, silme işlemleri

**Web Search Tool:** İnternet araması (DuckDuckGo, Serper API)

**Calculator Tool:** Matematiksel hesaplamalar

**Date/Time Tool:** Tarih ve saat işlemleri

### 9.2 Domain-Specific Tools

**Document Analyzer:** PDF, Word, Excel analizi

**Email Composer:** Profesyonel email taslakları

**Report Generator:** Otomatik rapor oluşturma

**Contract Reviewer:** Sözleşme analizi ve risk tespiti

### 9.3 Custom Tool Framework

Yeni tool ekleme için standart interface:
- Tool adı ve açıklaması
- Input parametreleri (Pydantic schema)
- Output formatı
- Execute metodu

---

## 10. API TASARIMI

### 10.1 RESTful Endpoints

**Chat Endpoints:**
- POST /api/chat - Yeni mesaj gönder
- GET /api/chat/history - Chat geçmişi
- DELETE /api/chat/session - Session temizle

**Document Endpoints:**
- POST /api/documents/upload - Döküman yükle
- GET /api/documents - Döküman listesi
- DELETE /api/documents/{id} - Döküman sil
- POST /api/documents/search - Döküman ara

**Agent Endpoints:**
- POST /api/agent/task - Görev ata
- GET /api/agent/status/{task_id} - Görev durumu

**Admin Endpoints:**
- GET /api/admin/stats - Sistem istatistikleri
- POST /api/admin/reindex - Yeniden indeksle

### 10.2 WebSocket Endpoints

**Real-time Chat:**
- WS /ws/chat - Streaming yanıtlar için

### 10.3 API Authentication

- API Key authentication
- Rate limiting (requests per minute)
- IP whitelisting (opsiyonel)

---

## 11. FRONTEND TASARIMI

### 11.1 Ana Sayfalar

**Chat Page:** Ana sohbet arayüzü, mesaj geçmişi, streaming yanıtlar

**Documents Page:** Döküman yönetimi, yükleme, listeleme, arama

**Search Page:** Gelişmiş arama, filtreler, sonuç görüntüleme

**Analytics Page:** Kullanım istatistikleri, popüler sorular, performans metrikleri

**Settings Page:** Sistem ayarları, model seçimi, kullanıcı tercihleri

### 11.2 UI Bileşenleri

**Chat Interface:** Mesaj baloncukları, typing indicator, source citations

**File Uploader:** Drag & drop, progress bar, format validation

**Search Results:** Highlight, pagination, relevance score

**Analytics Dashboard:** Charts, metrics, trends

---

## 12. VERİTABANI ŞEMASI

### 12.1 SQLite Tabloları

**documents:** id, filename, filepath, file_type, upload_date, chunk_count, metadata

**chat_sessions:** id, created_at, updated_at, user_id, title

**chat_messages:** id, session_id, role, content, timestamp, sources

**analytics:** id, event_type, event_data, timestamp

**settings:** key, value, updated_at

### 12.2 ChromaDB Collections

**enterprise_knowledge:** Ana bilgi tabanı collection'ı
- Documents: Döküman chunk'ları
- Embeddings: Vector representation'lar
- Metadatas: Chunk metadata'ları

---

## 13. GÜVENLİK

### 13.1 Veri Güvenliği

**Local-First Approach:**
- Tüm veriler local'de kalır
- Cloud'a veri gönderimi YOK
- Offline çalışabilme

**Encryption:**
- At-rest encryption (opsiyonel)
- Secure file storage

**Access Control:**
- Document-level permissions
- User authentication

### 13.2 Model Güvenliği

**Prompt Injection Prevention:**
- Input sanitization
- Output filtering
- Guardrails

**Data Leakage Prevention:**
- PII detection
- Sensitive data masking

---

## 14. DEPLOYMENT

### 14.1 Local Deployment

**Gereksinimler:**
- Python 3.11+
- Ollama
- 16GB+ RAM

**Kurulum Adımları:**
1. Repository clone
2. Virtual environment oluştur
3. Dependencies yükle
4. Ollama model'leri indir
5. Uygulamayı başlat

### 14.2 Docker Deployment

**Docker Compose:**
- Backend container
- Frontend container
- Ollama container
- Volume mounts for persistence

### 14.3 Enterprise Deployment

**Kubernetes:**
- Helm charts
- Horizontal scaling
- Load balancing

---

## 15. KULLANIM SENARYOLARI

### 15.1 HR Senaryoları

**Senaryo 1:** Çalışan izin politikası sorgusu
**Senaryo 2:** Yeni çalışan onboarding paketi
**Senaryo 3:** CV tarama ve özet

### 15.2 Legal Senaryoları

**Senaryo 1:** Sözleşme analizi
**Senaryo 2:** Emsal arama
**Senaryo 3:** Risk değerlendirme

### 15.3 Sales Senaryoları

**Senaryo 1:** Müşteri bilgisi sorgulama
**Senaryo 2:** Teklif taslağı hazırlama
**Senaryo 3:** Satış raporu özeti

---

## 16. PROJE YAPISI

enterprise-ai-assistant/
- README.md
- requirements.txt
- docker-compose.yml
- .env.example
- agents/ (orchestrator.py, research_agent.py, writer_agent.py, analyzer_agent.py, assistant_agent.py)
- tools/ (rag_tool.py, file_tool.py, web_tool.py, calendar_tool.py)
- core/ (llm_manager.py, embedding.py, vector_store.py, config.py)
- rag/ (document_loader.py, chunker.py, retriever.py, reranker.py)
- api/ (main.py, routes/, websocket.py)
- frontend/ (app.py, pages/, components/)
- data/ (chroma_db/, uploads/, sessions/, cache/)
- tests/ (test_agents.py, test_rag.py, test_api.py)

---

## 17. GELİŞTİRME YOL HARİTASI

### Phase 1: MVP (Hafta 1-2)
- Core RAG sistemi
- Temel chat arayüzü
- Döküman yükleme

### Phase 2: Multi-Agent (Hafta 3-4)
- Agent orchestrator
- Research, Writer, Analyzer agents
- Tool integration

### Phase 3: MCP & Extensions (Hafta 5-6)
- MCP server entegrasyonu
- Custom tool framework
- Advanced retrieval strategies

### Phase 4: Polish & Deploy (Hafta 7-8)
- UI/UX improvements
- Performance optimization
- Documentation
- Docker deployment

---

## 18. TEST STRATEJİSİ

### 18.1 Unit Tests
- Agent logic tests
- Tool function tests
- RAG component tests

### 18.2 Integration Tests
- API endpoint tests
- Agent collaboration tests
- End-to-end flow tests

### 18.3 Performance Tests
- Response time benchmarks
- Throughput tests
- Memory usage profiling

---

## 19. PERFORMANS HEDEFLERİ

| Metrik | Hedef | Ölçüm Yöntemi |
|--------|-------|---------------|
| İlk yanıt süresi | < 1 saniye | Time to first token |
| Toplam yanıt süresi | < 5 saniye | End-to-end latency |
| Döküman indexleme | < 2 sn/sayfa | Pages per second |
| Concurrent users | 10+ | Simultaneous requests |
| Memory usage | < 8 GB | Peak RAM |

---

## 20. MALİYET ANALİZİ

### 20.1 Geliştirme Maliyetleri

| Bileşen | Maliyet |
|---------|---------|
| Ollama | $0 (Açık kaynak) |
| LLM Models | $0 (Llama, Mistral ücretsiz) |
| ChromaDB | $0 (Açık kaynak) |
| Python libs | $0 |
| Streamlit | $0 |
| FastAPI | $0 |
| **TOPLAM** | **$0** |

### 20.2 Operasyonel Maliyetler

| Bileşen | Aylık Maliyet |
|---------|---------------|
| Cloud API | $0 |
| Lisans | $0 |
| Hosting | $0 (local) |
| **TOPLAM** | **$0** |

### 20.3 Donanım Gereksinimleri

Mevcut kurumsal bilgisayarlar genellikle minimum gereksinimleri karşılar. Opsiyonel GPU ile performans artışı sağlanabilir.

---

##  SONUÇ

Enterprise AI Assistant, endüstri standartlarında tasarlanmış, güvenli, ölçeklenebilir ve maliyet-etkin bir kurumsal AI çözümüdür. Tamamen local çalışması, multi-agent mimarisi ve genişletilebilir tool sistemi ile şirketlerin dijital dönüşüm ihtiyaçlarını karşılamaya hazırdır.

**Bu proje ENDÜSTRİ STANDARTLARINDA bir yazılım olarak geliştirilmektedir.**

---

> **Son Güncelleme:** 10 Ocak 2026  
> **Doküman Versiyonu:** 1.0.0  
> **Durum:** Aktif Geliştirme
