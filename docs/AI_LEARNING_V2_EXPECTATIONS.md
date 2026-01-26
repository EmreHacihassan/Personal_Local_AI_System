# 🎓 AI ile Öğren V2 - Kapsamlı Beklentiler Dokümanı

> **Versiyon:** 2.0  
> **Son Güncelleme:** 23 Ocak 2026  
> **Durum:** Premium Test Protokolü Referansı

---

## 📋 İçindekiler

1. [Genel Vizyon](#1-genel-vizyon)
2. [Kullanıcı Deneyimi Beklentileri](#2-kullanıcı-deneyimi-beklentileri)
3. [Backend Beklentileri](#3-backend-beklentileri)
4. [Frontend Beklentileri](#4-frontend-beklentileri)
5. [Sınav Sistemi Beklentileri](#5-sınav-sistemi-beklentileri)
6. [Sertifika Sistemi Beklentileri](#6-sertifika-sistemi-beklentileri)
7. [Performans Beklentileri](#7-performans-beklentileri)
8. [Entegrasyon Beklentileri](#8-entegrasyon-beklentileri)

---

## 1. Genel Vizyon

### 1.1 Temel Hedef
**"AI ile Öğren" bölümü, Candy Crush tarzı görsel bir ilerleme haritasında, bilimsel öğrenme teknikleriyle desteklenen kapsamlı bir eğitim sistemi sunmalıdır.**

### 1.2 Ana Bileşenler

| Bileşen | Açıklama | Öncelik |
|---------|----------|---------|
| **Journey Creation Wizard** | 5 adımlı yolculuk oluşturma sihirbazı | 🔴 Kritik |
| **AI Thinking View** | AI düşünce sürecini gösteren animasyonlu görünüm | 🔴 Kritik |
| **Stage Map V2** | Candy Crush tarzı genişletilebilir aşama haritası | 🔴 Kritik |
| **Package View** | İçerik görüntüleme ve tüketme | 🔴 Kritik |
| **Exam System** | 15 farklı sınav türü (Feynman dahil) | 🔴 Kritik |
| **Certificate System** | Sertifika oluşturma ve doğrulama | 🟡 Önemli |

### 1.3 Tasarım Prensipleri

```
┌─────────────────────────────────────────────────────────────┐
│  1. Gamification     - XP, Stars, Streaks, Achievements    │
│  2. Scientific       - Feynman, Spaced Repetition, Recall  │
│  3. Personalization  - Weak areas, preferences, pace       │
│  4. Visual Progress  - Maps, charts, badges                │
│  5. AI-Powered       - Content generation, evaluation      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Kullanıcı Deneyimi Beklentileri

### 2.1 Journey Creation (Yolculuk Oluşturma)

#### Beklenen Akış:
```
[Konu Seçimi] → [Hedef Belirleme] → [Ön Bilgi] → [Zaman Planı] → [Tercihler]
       ↓                ↓               ↓             ↓              ↓
   Matematik        AYT 35+net     Zayıf alanlar   2 saat/gün    Video+Feynman
```

#### Detaylı Beklentiler:

| Adım | Beklenti | Doğrulama |
|------|----------|-----------|
| 1. Konu Seçimi | 8+ konu kartı görüntülenmeli | `SUBJECTS` array |
| 2. Hedef | Başlık, hedef, motivasyon alanları | Form validation |
| 3. Ön Bilgi | Seviye seçimi, zayıf alan çoklu seçim | Multi-select UI |
| 4. Zaman | Slider (0.5-8 saat), tarih seçici | Input controls |
| 5. Tercihler | İçerik türleri, sınav türleri seçimi | Checkbox groups |

#### Beklenmeyen Durumlar:
- ❌ Boş konu ile devam edilememeli
- ❌ Geçersiz tarih kabul edilmemeli
- ❌ 0 saat/gün seçilememeli

### 2.2 AI Thinking Animation

#### Beklenen Agent'lar:
1. **Goal Analyzer** - Hedef analizi
2. **Curriculum Selector** - Müfredat seçimi  
3. **Topic Mapper** - Konu haritalama
4. **Stage Planner** - Aşama planlama
5. **Package Designer** - Paket tasarımı
6. **Exam Generator** - Sınav oluşturma
7. **Exercise Creator** - Egzersiz oluşturma
8. **Content Structurer** - İçerik yapılandırma

#### UI Beklentileri:
- Her agent için animasyonlu kart
- Gerçek zamanlı düşünce akışı
- Progress indicator
- Tamamlanma bildirimi

### 2.3 Stage Map V2

#### Görsel Beklentiler:
```
┌──────────────────────────────────────────────────────┐
│  Stage 1: Temel Kavramlar                     ✅     │
│  ├── 📚 Intro Package        [100%] ⭐⭐⭐           │
│  ├── 📖 Learning Package     [100%] ⭐⭐⭐           │
│  ├── ✏️ Practice Package     [75%]  ⭐⭐             │
│  └── 📝 Exam Package         [Locked] 🔒            │
├──────────────────────────────────────────────────────┤
│  Stage 2: İleri Kavramlar                    🔓      │
│  ► Tıkla ve genişlet                                │
└──────────────────────────────────────────────────────┘
```

#### Etkileşim Beklentileri:
- Tıkla-genişlet stage kartları
- Paket kartlarına tıklayınca detay görünümü
- Kilitli paketler için görsel feedback
- Smooth animasyonlar (framer-motion)

### 2.4 Package View

#### İçerik Türleri:
| Tür | Emoji | Beklenen Görünüm |
|-----|-------|------------------|
| text | 📖 | Markdown render |
| video | 🎬 | Video player embed |
| interactive | 🎮 | Custom component |
| example | 📝 | Code/math rendering |
| summary | 📋 | Kısa özet kartı |

#### Progress Tracking:
- Her content block için completion checkbox
- Package progress bar
- XP kazanım bildirimi

---

## 3. Backend Beklentileri

### 3.1 API Endpoints

| Endpoint | Method | Beklenen Response | Status |
|----------|--------|-------------------|--------|
| `/journey/v2/list` | GET | `{journeys: [...]}` | ✅ |
| `/journey/v2/create` | POST | `{journey_id, events}` | ✅ |
| `/journey/v2/{id}/map` | GET | Stage map with packages | ✅ |
| `/journey/v2/{id}/progress` | GET | User progress data | ⚠️ |
| `/journey/v2/{id}/packages/{pkg}/start` | POST | Package content | ✅ |
| `/journey/v2/{id}/packages/{pkg}/complete` | POST | Completion result | ⚠️ |
| `/journey/v2/{id}/exams/{exam}/submit` | POST | Exam result | ✅ |
| `/journey/v2/{id}/complete` | POST | Certificate | ⚠️ |
| `/certificates/verify/{code}` | GET | Certificate data | ⚠️ |

### 3.2 Data Models

#### LearningGoal:
```python
@dataclass
class LearningGoal:
    id: str
    user_id: str
    title: str                    # "AYT Matematik"
    subject: str                  # "Matematik"
    target_outcome: str           # "35+ net"
    daily_hours: float            # 2.0
    weak_areas: List[str]         # ["Türev", "İntegral"]
    content_preferences: List[ContentType]
    exam_preferences: List[ExamType]
```

#### CurriculumPlan:
```python
@dataclass
class CurriculumPlan:
    id: str
    goal: LearningGoal
    stages: List[Stage]           # 7-12 aşama
    total_packages: int           # 100-150 paket
    total_exams: int              # ~100 sınav
    total_xp_possible: int        # 10000+ XP
```

#### Stage:
```python
@dataclass
class Stage:
    id: str
    number: int
    title: str
    packages: List[Package]       # 8-15 paket per stage
    status: StageStatus
    xp_total: int
```

#### Package:
```python
@dataclass
class Package:
    id: str
    type: PackageType             # intro/learning/practice/exam/closure
    content_blocks: List[ContentBlock]
    exercises: List[Exercise]
    exams: List[Exam]
    status: PackageStatus
```

### 3.3 Orchestrator Beklentileri

| Fonksiyon | Beklenen Davranış |
|-----------|-------------------|
| `create_journey()` | Streaming events ile plan oluştur |
| `start_package()` | İçerik blokları oluştur/getir |
| `submit_exam()` | AI ile değerlendir, sonuç dön |
| `complete_journey()` | Sertifika oluştur |
| `get_stage_map()` | Frontend-uyumlu map dön |

### 3.4 Singleton Pattern

```python
# Beklenen: Global singleton instance
orchestrator = get_learning_orchestrator()  # Her zaman aynı instance
exam_system = get_exam_system()
certificate_generator = get_certificate_generator()
```

---

## 4. Frontend Beklentileri

### 4.1 Component Hiyerarşisi

```
LearningPage
├── JourneyCreationWizard
│   ├── StepIndicator
│   ├── SubjectStep
│   ├── GoalStep
│   ├── BackgroundStep
│   ├── ScheduleStep
│   └── PreferencesStep
├── AIThinkingView
│   ├── AgentCard
│   └── ProgressBar
├── StageMapV2
│   ├── StageCard (expandable)
│   └── PackageCard
├── PackageView
│   ├── ContentBlock
│   └── ProgressTracker
├── ExamView
│   ├── Timer
│   ├── QuestionView
│   ├── FeynmanView
│   └── ResultView
└── CertificateView
    ├── CertificateCard
    └── ShareButtons
```

### 4.2 State Management

```typescript
// Beklenen store yapısı
interface LearningState {
  currentJourney: Journey | null;
  journeyList: Journey[];
  currentPackage: Package | null;
  currentExam: Exam | null;
  isCreating: boolean;
  isLoading: boolean;
  error: string | null;
}
```

### 4.3 API Integration

```typescript
// Beklenen API çağrıları
const api = {
  createJourney: (goal: LearningGoal) => POST('/journey/v2/create', goal),
  getJourneyMap: (id: string) => GET(`/journey/v2/${id}/map`),
  startPackage: (journeyId, pkgId) => POST(`/journey/v2/${journeyId}/packages/${pkgId}/start`),
  submitExam: (journeyId, examId, data) => POST(`/journey/v2/${journeyId}/exams/${examId}/submit`, data),
};
```

### 4.4 Styling Beklentileri

| Element | Dark Mode | Light Mode |
|---------|-----------|------------|
| Background | `bg-gray-900` | `bg-white` |
| Cards | `bg-gray-800` | `bg-gray-50` |
| Text | `text-white` | `text-gray-900` |
| Accent | `purple-500/indigo-600` | Same |
| Progress | Gradient bars | Same |

---

## 5. Sınav Sistemi Beklentileri

### 5.1 Desteklenen Sınav Türleri

| Tür | Kod | Değerlendirme | Priority |
|-----|-----|---------------|----------|
| Çoktan Seçmeli | `multiple_choice` | Otomatik | 🔴 |
| Feynman | `feynman` | AI Değerlendirme | 🔴 |
| Problem Çözme | `problem_solving` | AI Değerlendirme | 🔴 |
| Kavram Haritası | `concept_map` | AI Değerlendirme | 🟡 |
| Öğreterek Öğren | `teach_back` | AI Değerlendirme | 🟡 |
| Doğru/Yanlış | `true_false` | Otomatik | 🟢 |
| Boşluk Doldurma | `fill_blank` | Otomatik/AI | 🟢 |
| Kısa Cevap | `short_answer` | AI Değerlendirme | 🟢 |
| Kompozisyon | `essay` | AI Değerlendirme | 🟢 |

### 5.2 Feynman Tekniği Sınavı

#### Beklenen Akış:
```
1. AI konu verir → "Türev nedir ve neden önemlidir?"
2. Kullanıcı açıklar (metin/ses)
3. AI 5 kritere göre değerlendirir
4. Detaylı geri bildirim verilir
```

#### Değerlendirme Kriterleri:
| Kriter | Ağırlık | Açıklama |
|--------|---------|----------|
| Accuracy | %20 | Bilgi doğruluğu |
| Depth | %20 | Konu derinliği |
| Clarity | %20 | Açıklık ve anlaşılırlık |
| Examples | %20 | Örnek kullanımı |
| Completeness | %20 | Konuyu kapsama |

#### Beklenen Response:
```json
{
  "passed": true,
  "score": 85,
  "feedback": {
    "accuracy": 90,
    "depth": 80,
    "clarity": 85,
    "examples": 90,
    "completeness": 80
  },
  "overall_feedback": "Türev kavramını iyi açıkladınız..."
}
```

### 5.3 ExamResult Model

```python
@dataclass
class ExamResult:
    exam_id: str
    user_id: str
    exam_type: ExamType
    total_score: float
    percentage: float
    passed: bool
    criteria_scores: List[CriteriaScore]
    detailed_feedback: str
    suggestions: List[str]
```

---

## 6. Sertifika Sistemi Beklentileri

### 6.1 Sertifika Seviyeleri

| Seviye | Emoji | Koşul |
|--------|-------|-------|
| Bronze | 🥉 | İlk tamamlama |
| Silver | 🥈 | %80+ ortalama |
| Gold | 🥇 | %90+ ortalama |
| Platinum | 💎 | Mükemmel (%95+) |

### 6.2 Sertifika İçeriği

```
┌─────────────────────────────────────────────────┐
│           🏆 BAŞARI SERTİFİKASI 🏆              │
│                                                 │
│  [Kullanıcı Adı]                               │
│                                                 │
│  [Yolculuk Başlığı] başarıyla tamamlandı       │
│                                                 │
│  Puan: 92%  |  XP: 12,500  |  Süre: 45 gün     │
│                                                 │
│  Doğrulama Kodu: ABC123XYZ                     │
│                                                 │
│  Tarih: 23 Ocak 2026                           │
└─────────────────────────────────────────────────┘
```

### 6.3 Doğrulama Endpoint

```
GET /certificates/verify/{code}
Response: {
  "valid": true,
  "certificate": {...},
  "issued_at": "2026-01-23T12:00:00Z"
}
```

---

## 7. Performans Beklentileri

### 7.1 Response Time Targets

| Endpoint | Target | Max |
|----------|--------|-----|
| `/journey/v2/list` | <100ms | 500ms |
| `/journey/v2/create` | <30s | 60s |
| `/journey/v2/{id}/map` | <200ms | 1s |
| `/journey/v2/.../start` | <2s | 10s |
| `/journey/v2/.../submit` | <5s | 15s |

### 7.2 Memory Management

- Orchestrator singleton pattern
- Journey state in-memory (active_journeys dict)
- Lazy loading for content blocks
- Pagination for large stage maps

### 7.3 Error Handling

| Hata | HTTP Code | Beklenen Mesaj |
|------|-----------|----------------|
| Journey not found | 404 | "Journey bulunamadı" |
| Package not found | 404 | "Paket bulunamadı" |
| Exam not found | 404 | "Sınav bulunamadı" |
| Invalid submission | 422 | Validation error |
| Server error | 500 | "Internal error" |

---

## 8. Entegrasyon Beklentileri

### 8.1 WebSocket Real-time Updates

```javascript
// Beklenen WebSocket mesajları
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  switch(type) {
    case 'journey_started': // Yolculuk başladı
    case 'thinking_step':   // AI düşünce adımı
    case 'package_ready':   // Paket hazır
    case 'exam_graded':     // Sınav değerlendirildi
    case 'xp_earned':       // XP kazanıldı
    case 'journey_complete': // Yolculuk tamamlandı
  }
};
```

### 8.2 Full Meta Integration

12 katmanlı öğrenme sistemi ile entegrasyon:
1. Warmup
2. Prime
3. Acquire
4. Interrogate
5. Practice
6. Connect
7. Challenge
8. Error Lab
9. Feynman
10. Transfer
11. Meta Reflection
12. Consolidate

### 8.3 RAG Integration

- Content generation için RAG kullanımı
- Soru oluşturma için kaynak kullanımı
- Değerlendirme için context awareness

---

## 📊 Beklenti Özeti

| Kategori | Toplam | Kritik | Önemli | Normal |
|----------|--------|--------|--------|--------|
| UX | 25 | 10 | 10 | 5 |
| Backend | 30 | 15 | 10 | 5 |
| Frontend | 20 | 8 | 8 | 4 |
| Sınav | 15 | 8 | 5 | 2 |
| Sertifika | 8 | 3 | 3 | 2 |
| Performans | 10 | 5 | 3 | 2 |
| **TOPLAM** | **108** | **49** | **39** | **20** |

---

> **Sonraki Adım:** Bu beklentiler temelinde Premium Test Protokolü oluşturulacak ve her beklenti test edilecektir.

---

*Son güncelleme: 23 Ocak 2026*
